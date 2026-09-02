'''Tiferet OpenAPI Context'''

# *** imports

# ** core
import importlib
from typing import Any, Callable

# ** infra
from tiferet import TiferetError, TiferetAPIError
from tiferet.contexts.app import AppSessionContext
from tiferet.contexts.cache import CacheContext
from tiferet.events import DomainEvent

# ** app
from .request import OpenApiRequestContext


# *** contexts

# ** context: open_api_session_context
class OpenApiSessionContext(AppSessionContext):
    '''
    A shared API session context that extends the application session hub
    with OpenAPI-specific status-code-aware error handling and response
    building, so any framework-specific adapter (Flask, FastAPI) can
    subclass it and inherit consistent route- and error-status resolution.
    '''

    # * attribute: get_route_evt (private)
    _get_route_evt: DomainEvent

    # * attribute: get_status_code_evt (private)
    _get_status_code_evt: DomainEvent

    # * attribute: get_routers_evt (private)
    _get_routers_evt: DomainEvent

    # * init
    def __init__(self,
            get_dependency: Callable,
            get_route_evt: DomainEvent = None,
            get_status_code_evt: DomainEvent = None,
            get_routers_evt: DomainEvent = None,
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
        :param get_route_evt: The domain event for retrieving a route.
        :type get_route_evt: DomainEvent
        :param get_status_code_evt: The domain event for retrieving a status code.
        :type get_status_code_evt: DomainEvent
        :param get_routers_evt: The domain event for retrieving all routers.
        :type get_routers_evt: DomainEvent
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

        # Store the OpenAPI event collaborators privately.
        self._get_route_evt = get_route_evt
        self._get_status_code_evt = get_status_code_evt
        self._get_routers_evt = get_routers_evt

    # * method: build_response
    def build_response(self, request: OpenApiRequestContext) -> Any:
        '''
        Build the response and pair it with its HTTP status code.

        Extends the hub's build_response so an unwired response_handler
        still raises through the hub guard, then looks the route up to
        attach the appropriate status code.

        :param request: The completed request context.
        :type request: OpenApiRequestContext
        :return: The response and status code.
        :rtype: Any
        '''

        # Delegate response extraction to the hub template method.
        response = super().build_response(request)

        # Retrieve the route by the request feature id.
        route = self._get_route_evt.execute(endpoint=request.feature_id)

        # Return the result with the specified status code.
        return response, route.status_code if route else 200

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
            status_code = self._get_status_code_evt.execute(error_code=error.error_code)
        else:
            status_code = 500

        # Delegate formatting to the hub (which raises TiferetAPIError).
        try:
            return super().handle_error(error, **kwargs)
        except TiferetAPIError as api_error:
            api_error.status_code = status_code
            raise
    # * method: _resolve_model_schema
    def _resolve_model_schema(self, model_path: str) -> dict | None:
        '''
        Resolve a dotted import path to a Pydantic model JSON schema.

        :param model_path: The dotted path to the model class.
        :type model_path: str
        :return: The JSON schema dict, or None when resolution fails.
        :rtype: dict | None
        '''

        try:
            # Split the dotted path into module and class names.
            module_path, class_name = model_path.rsplit('.', 1)

            # Import the module and retrieve the model class.
            module = importlib.import_module(module_path)
            model_cls = getattr(module, class_name)

            # Return the Pydantic JSON schema.
            return model_cls.model_json_schema()
        except Exception:
            return None

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
        '''

        # Retrieve all routers via the domain event.
        routers = self._get_routers_evt.execute()

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

                    # Include the resolved request schema when present.
                    if route.request_model:
                        request_schema = self._resolve_model_schema(route.request_model)
                        if request_schema:
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
                        if response_schema:
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

    # * method: create_docs_handler
    def create_docs_handler(self, **kwargs):
        '''
        Create a documentation handler for serving the OpenAPI spec.
        Base implementation returns None; override in framework-specific subclasses.

        :param kwargs: Additional keyword arguments.
        :type kwargs: dict
        :return: A framework-specific handler, or None.
        :rtype: Any
        '''

        # Return None by default (no-op for base context).
        return None
