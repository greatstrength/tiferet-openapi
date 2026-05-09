'''Tiferet OpenAPI Context'''

# *** imports

# ** core
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

    # * init
    def __init__(self,
            interface_id: str,
            features: FeatureContext,
            errors: ErrorContext,
            logging: LoggingContext,
            get_route_evt: DomainEvent,
            get_status_code_evt: DomainEvent,
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
        '''

        # Call the parent constructor.
        super().__init__(interface_id, features, errors, logging)

        # Set the domain event handlers.
        self.get_route_handler = get_route_evt.execute
        self.get_status_code_handler = get_status_code_evt.execute

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