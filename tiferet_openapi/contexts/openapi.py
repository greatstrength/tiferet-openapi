'''Tiferet OpenAPI Context'''

# *** imports

# ** core
import importlib
from typing import Any, Callable

# ** infra
from tiferet import TiferetError
from tiferet.assets.exceptions import TiferetAPIError
from tiferet.contexts import (
    AppInterfaceContext,
    FeatureContext,
    ErrorContext,
    LoggingContext,
)
from tiferet.events import DomainEvent

# ** app
from .request import OpenApiRequestContext


# *** contexts

# ** context: open_api_context
class OpenApiContext(AppInterfaceContext):
    '''
    A shared API context for managing OpenAPI interactions within the Tiferet framework.
    '''

    # * attribute: get_route_handler
    get_route_handler: Callable

    # * attribute: get_status_code_handler
    get_status_code_handler: Callable

    # * attribute: get_routers_handler
    get_routers_handler: Callable

    # * init
    def __init__(self,
            interface_id: str,
            features: FeatureContext,
            errors: ErrorContext,
            logging: LoggingContext,
            get_route_evt: DomainEvent,
            get_status_code_evt: DomainEvent,
            get_routers_evt: DomainEvent,
        ):
        '''
        Initialize the OpenAPI context.

        :param interface_id: The interface ID.
        :type interface_id: str
        :param features: The feature context.
        :type features: FeatureContext
        :param errors: The error context.
        :type errors: ErrorContext
        :param logging: The logging context.
        :type logging: LoggingContext
        :param get_route_evt: The domain event for retrieving a route.
        :type get_route_evt: DomainEvent
        :param get_status_code_evt: The domain event for retrieving a status code.
        :type get_status_code_evt: DomainEvent
        :param get_routers_evt: The domain event for retrieving all routers.
        :type get_routers_evt: DomainEvent
        '''

        # Call the parent constructor.
        super().__init__(interface_id, features, errors, logging)

        # Set the domain event handlers.
        self.get_route_handler = get_route_evt.execute
        self.get_status_code_handler = get_status_code_evt.execute
        self.get_routers_handler = get_routers_evt.execute

    # * method: parse_request
    def parse_request(self, headers: dict = {}, data: dict = {}, feature_id: str = None, **kwargs) -> OpenApiRequestContext:
        '''
        Parse the incoming request and return an OpenApiRequestContext instance.

        :param headers: The request headers.
        :type headers: dict
        :param data: The request data.
        :type data: dict
        :param feature_id: The feature ID.
        :type feature_id: str
        :param kwargs: Additional keyword arguments.
        :type kwargs: dict
        :return: An OpenApiRequestContext instance.
        :rtype: OpenApiRequestContext
        '''

        # Return an OpenApiRequestContext instance.
        return OpenApiRequestContext(
            headers=headers,
            data=data,
            feature_id=feature_id,
        )

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
            status_code = self.get_status_code_handler(error_code=error.error_code)
        else:
            status_code = 500

        # Delegate formatting to parent (which raises TiferetAPIError).
        try:
            return super().handle_error(error, **kwargs)
        except TiferetAPIError as api_error:
            api_error.status_code = status_code
            raise

    # * method: handle_response
    def handle_response(self, request: OpenApiRequestContext, **kwargs) -> Any:
        '''
        Handle the response from the request context.

        :param request: The request context.
        :type request: OpenApiRequestContext
        :param kwargs: Additional keyword arguments.
        :type kwargs: dict
        :return: The response and status code.
        :rtype: Any
        '''

        # Handle the response from the request context.
        response = super().handle_response(request, **kwargs)

        # Retrieve the route by the request feature id.
        route = self.get_route_handler(endpoint=request.feature_id)

        # Return the result with the specified status code.
        return response, route.status_code if route else 200

    # * method: _resolve_model_schema
    def _resolve_model_schema(self, model_path: str) -> dict | None:
        '''
        Resolve a dotted import path to a Pydantic model JSON schema.

        :param model_path: Dotted import path (e.g. 'app.domain.request.AddRequest').
        :type model_path: str
        :return: The JSON schema dict, or None if resolution fails.
        :rtype: dict | None
        '''

        try:
            # Split the dotted path into module and class name.
            module_path, class_name = model_path.rsplit('.', 1)

            # Import the module and retrieve the class.
            module = importlib.import_module(module_path)
            model_cls = getattr(module, class_name)

            # Return the JSON schema from the Pydantic model.
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

        # Retrieve all routers via the domain event handler.
        routers = self.get_routers_handler()

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

                    # Include summary if present.
                    if route.summary:
                        operation['summary'] = route.summary

                    # Include description if present.
                    if route.description:
                        operation['description'] = route.description

                    # Include tags if present.
                    if route.tags:
                        operation['tags'] = route.tags

                    # Resolve request model schema for requestBody if present.
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

                    # Resolve response model schema if present.
                    if route.response_model:
                        response_schema = self._resolve_model_schema(route.response_model)
                        if response_schema:
                            operation['responses'][str(route.status_code)]['content'] = {
                                'application/json': {
                                    'schema': response_schema,
                                },
                            }

                    # Add the operation to the path.
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
