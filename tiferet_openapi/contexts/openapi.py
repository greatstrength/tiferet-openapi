'''Tiferet OpenAPI Context'''

# *** imports

# ** core
import importlib
import warnings
from typing import Any, Callable

# ** infra
from tiferet import TiferetError, TiferetAPIError
from tiferet.contexts.app import AppSessionContext
from tiferet.contexts.cache import CacheContext

# ** app
from .request import OpenApiRequestContext

# *** contexts

# ** context: open_api_session_context
class OpenApiSessionContext(AppSessionContext):
    '''
    The shared OpenAPI session hub Flask and FastAPI adapters subclass for
    status-code-aware error handling and response building.
    '''

    # * attribute: get_route (private)
    _get_route: Callable

    # * attribute: get_status_code (private)
    _get_status_code: Callable

    # * attribute: get_routers (private)
    _get_routers: Callable

    # * init
    def __init__(self,
            get_dependency: Callable,
            get_route_handler: Callable = None,
            get_status_code_handler: Callable = None,
            get_routers_handler: Callable = None,
            cache: CacheContext = None,
            build_logger_handler: Callable = None,
            execute_feature_handler: Callable = None,
            create_request_handler: Callable = None,
            raise_error_handler: Callable = None,
            response_handler: Callable = None):
        '''
        Initialize the OpenAPI session context.

        :param get_dependency: The DI resolution handler injected by the blueprint.
        :type get_dependency: Callable
        :param get_route_handler: The injected callable that retrieves a route.
        :type get_route_handler: Callable
        :param get_status_code_handler: The injected callable that retrieves a status code.
        :type get_status_code_handler: Callable
        :param get_routers_handler: The injected callable that retrieves all routers.
        :type get_routers_handler: Callable
        :param cache: The shared bootstrap cache.
        :type cache: CacheContext
        :param build_logger_handler: The logger-construction handler.
        :type build_logger_handler: Callable
        :param execute_feature_handler: The feature-execution handler.
        :type execute_feature_handler: Callable
        :param create_request_handler: The request-construction handler.
        :type create_request_handler: Callable
        :param raise_error_handler: The error-handling handler.
        :type raise_error_handler: Callable
        :param response_handler: The response-building handler.
        :type response_handler: Callable
        '''

        # Initialize the base application session hub.
        super().__init__(
            get_dependency=get_dependency,
            cache=cache,
            build_logger_handler=build_logger_handler,
            execute_feature_handler=execute_feature_handler,
            create_request_handler=create_request_handler,
            raise_error_handler=raise_error_handler,
            response_handler=response_handler,
        )

        # Store the injected OpenAPI handler callables.
        self._get_route = get_route_handler
        self._get_status_code = get_status_code_handler
        self._get_routers = get_routers_handler

    # * method: handle_error
    def handle_error(self, error: Exception, **kwargs) -> Any:
        '''
        Handle the error and raise TiferetAPIError with status_code.

        :param error: The error to handle.
        :type error: Exception
        :param kwargs: Additional keyword arguments.
        :type kwargs: dict
        :return: The error response.
        :rtype: Any
        '''

        # Get the status code via event if it's a TiferetError.
        if isinstance(error, TiferetError):
            status_code = self._get_status_code(error_code=error.error_code)
        else:
            status_code = 500

        # Delegate formatting to parent (which raises TiferetAPIError).
        try:
            return super().handle_error(error, **kwargs)
        except TiferetAPIError as api_error:
            api_error.status_code = status_code
            raise

    # * method: build_response
    def build_response(self, request: OpenApiRequestContext) -> Any:
        '''
        Build the response from the request context.

        :param request: The request context.
        :type request: OpenApiRequestContext
        :return: The response and status code.
        :rtype: Any
        '''

        # Handle the response from the request context.
        response = super().build_response(request)

        # Retrieve the route by the request feature id.
        route = self._get_route(endpoint=request.feature_id)

        # Return the result with the specified status code.
        return response, route.status_code if route else 200

    # * method: _resolve_model_schema
    def _resolve_model_schema(self, model_path: str) -> dict:
        '''
        Resolve a dotted import path to a Pydantic model JSON schema.

        :param model_path: The dotted path to the model class.
        :type model_path: str
        :return: The JSON schema dict.
        :rtype: dict
        :raises TiferetError: When the path is malformed, the module or class cannot be found, or the class has no model_json_schema.
        '''

        try:
            # Split the dotted path into module and class names.
            module_path, class_name = model_path.rsplit('.', 1)

            # Import the module and retrieve the model class.
            module = importlib.import_module(module_path)
            model_cls = getattr(module, class_name)

            # Return the Pydantic JSON schema.
            return model_cls.model_json_schema()

        except Exception as exception:

            # Raise a structured error carrying the failing path and reason.
            TiferetError.raise_error(
                'OPENAPI_MODEL_RESOLUTION_FAILED',
                f'Failed to resolve model schema for path: {model_path}.',
                model_path=model_path,
                reason=str(exception),
            )

    # * method: generate_spec
    def generate_spec(self, title: str = 'API', version: str = '1.0.0', description: str = '') -> dict:
        '''
        Generate an OpenAPI 3.0 specification from the configured routers.

        :param title: The API title.
        :type title: str
        :param version: The API version.
        :type version: str
        :param description: The API description.
        :type description: str
        :return: An OpenAPI 3.0 spec dict.
        :rtype: dict
        :raises TiferetError: When any route's request_model/response_model path fails to resolve; the first such failure aborts the entire spec generation call.
        '''

        # Retrieve all routers via the domain event handler.
        routers = self._get_routers()

        # Build the paths dict from routers and their routes.
        paths = {}
        for router in routers:
            for route in router.routes:
                full_path = f'{router.prefix or ""}{route.path}'
                if full_path not in paths:
                    paths[full_path] = {}
                for method in route.methods:
                    # Build the base operation entry.
                    operation = {
                        'operationId': route.endpoint,
                        'responses': {
                            str(route.status_code): {
                                'description': 'Successful response',
                            },
                        },
                    }

                    # Include the declared summary when present.
                    if route.summary:
                        operation['summary'] = route.summary

                    # Include the declared description when present.
                    if route.description:
                        operation['description'] = route.description

                    # Include the declared tags when present.
                    if route.tags:
                        operation['tags'] = route.tags

                    # Resolution failures propagate as a structured TiferetError rather than being caught here, so a broken model reference fails spec generation loudly instead of silently producing an incomplete spec.
                    if route.request_model:
                        request_schema = self._resolve_model_schema(route.request_model)
                        operation['requestBody'] = {
                            'required': True,
                            'content': {
                                'application/json': {
                                    'schema': request_schema,
                                },
                            },
                        }

                    # Include the resolved response schema when present.
                    if route.response_model:
                        response_schema = self._resolve_model_schema(route.response_model)
                        operation['responses'][str(route.status_code)]['content'] = {
                            'application/json': {
                                'schema': response_schema,
                            },
                        }

                    # Add the operation to its HTTP method entry.
                    paths[full_path][method.lower()] = operation

        # Return the OpenAPI 3.0 spec.
        return {
            'openapi': '3.0.3',
            'info': {
                'title': title,
                'version': version,
                'description': description,
            },
            'paths': paths,
        }

    # * method: get_docs_spec
    def get_docs_spec(self,
            title: str = 'API',
            version: str = '1.0.0',
            description: str = '',
            **kwargs) -> dict:
        '''
        Return the generated OpenAPI specification for adapter rendering.

        :param title: The API title.
        :type title: str
        :param version: The API version.
        :type version: str
        :param description: The API description.
        :type description: str
        :param kwargs: Additional keyword arguments.
        :type kwargs: dict
        :return: The generated OpenAPI 3.0 specification.
        :rtype: dict
        '''

        # Generate and return the framework-agnostic specification data.
        return self.generate_spec(
            title=title,
            version=version,
            description=description,
        )

    # * method: create_docs_handler (obsolete)
    # -- obsolete: Remove at the full v1.0.0 release after the deprecation window.
    def create_docs_handler(self,
            title: str = 'API',
            version: str = '1.0.0',
            description: str = '',
            **kwargs) -> dict:
        '''
        Return the generated OpenAPI specification through a deprecated alias.

        :param title: The API title.
        :type title: str
        :param version: The API version.
        :type version: str
        :param description: The API description.
        :type description: str
        :param kwargs: Additional keyword arguments.
        :type kwargs: dict
        :return: The generated OpenAPI 3.0 specification.
        :rtype: dict
        :raises DeprecationWarning: Always, because this alias will be removed.
        '''

        # Warn callers to use the data-oriented replacement method.
        warnings.warn(
            'create_docs_handler is deprecated; use get_docs_spec instead.',
            DeprecationWarning,
            stacklevel=2,
        )

        # Delegate specification creation to the replacement method.
        return self.get_docs_spec(
            title=title,
            version=version,
            description=description,
            **kwargs,
        )
