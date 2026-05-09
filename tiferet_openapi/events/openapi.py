'''Tiferet OpenAPI Domain Events'''

# *** imports

# ** core
from typing import List

# ** infra
from tiferet import DomainEvent

# ** app
from ..domain import ApiRoute, ApiRouter
from ..interfaces import OpenApiService


# *** events

# ** event: get_routers
class GetRouters(DomainEvent):
    '''
    Domain event to retrieve all API routers.
    '''

    # * attribute: openapi_service
    openapi_service: OpenApiService

    # * init
    def __init__(self, openapi_service: OpenApiService):
        '''
        Initialize the GetRouters event.

        :param openapi_service: The OpenAPI service.
        :type openapi_service: OpenApiService
        '''

        # Set the OpenAPI service dependency.
        self.openapi_service = openapi_service

    # * method: execute
    def execute(self, **kwargs) -> List[ApiRouter]:
        '''
        Retrieve all configured API routers.

        :param kwargs: Additional keyword arguments.
        :type kwargs: dict
        :return: A list of API routers.
        :rtype: List[ApiRouter]
        '''

        # Retrieve routers from the service.
        return self.openapi_service.get_routers()


# ** event: get_route
class GetRoute(DomainEvent):
    '''
    Domain event to retrieve an API route by endpoint.
    '''

    # * attribute: openapi_service
    openapi_service: OpenApiService

    # * init
    def __init__(self, openapi_service: OpenApiService):
        '''
        Initialize the GetRoute event.

        :param openapi_service: The OpenAPI service.
        :type openapi_service: OpenApiService
        '''

        # Set the OpenAPI service dependency.
        self.openapi_service = openapi_service

    # * method: execute
    @DomainEvent.parameters_required(['endpoint'])
    def execute(self, endpoint: str, **kwargs) -> ApiRoute:
        '''
        Retrieve an API route by its endpoint string.

        :param endpoint: The fully-qualified endpoint (e.g. "calc.add").
        :type endpoint: str
        :param kwargs: Additional keyword arguments.
        :type kwargs: dict
        :return: The matching API route.
        :rtype: ApiRoute
        '''

        # Parse endpoint into router_name and route_id.
        parts = endpoint.split('.', 1)
        if len(parts) == 2:
            router_name, route_id = parts
        else:
            router_name = None
            route_id = parts[0]

        # Retrieve the route from the service.
        route = self.openapi_service.get_route(route_id, router_name)

        # Verify that the route exists.
        self.verify(
            expression=route is not None,
            error_code='OPENAPI_ROUTE_NOT_FOUND',
            endpoint=endpoint,
        )

        # Return the route.
        return route


# ** event: get_status_code
class GetStatusCode(DomainEvent):
    '''
    Domain event to retrieve the HTTP status code for an error code.
    '''

    # * attribute: openapi_service
    openapi_service: OpenApiService

    # * init
    def __init__(self, openapi_service: OpenApiService):
        '''
        Initialize the GetStatusCode event.

        :param openapi_service: The OpenAPI service.
        :type openapi_service: OpenApiService
        '''

        # Set the OpenAPI service dependency.
        self.openapi_service = openapi_service

    # * method: execute
    @DomainEvent.parameters_required(['error_code'])
    def execute(self, error_code: str, **kwargs) -> int:
        '''
        Retrieve the HTTP status code for a given error code.

        :param error_code: The error code to look up.
        :type error_code: str
        :param kwargs: Additional keyword arguments.
        :type kwargs: dict
        :return: The corresponding HTTP status code.
        :rtype: int
        '''

        # Retrieve the status code from the service.
        return self.openapi_service.get_status_code(error_code)