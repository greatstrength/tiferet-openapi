'''Tiferet OpenAPI Service Interfaces'''

# *** imports

# ** core
from abc import abstractmethod
from typing import List

# ** infra
from tiferet import Service

# ** app
from ..domain import ApiRoute, ApiRouter


# *** interfaces

# ** interface: open_api_service
class OpenApiService(Service):
    '''
    Abstract service contract for OpenAPI route and router retrieval.
    '''

    # * method: get_routers
    @abstractmethod
    def get_routers(self) -> List[ApiRouter]:
        '''
        Retrieve all configured API routers.

        :return: A list of API routers.
        :rtype: List[ApiRouter]
        '''
        raise NotImplementedError()

    # * method: get_route
    @abstractmethod
    def get_route(self, route_id: str, router_name: str = None) -> ApiRoute:
        '''
        Retrieve a single API route by its identifier.

        :param route_id: The unique identifier of the route.
        :type route_id: str
        :param router_name: Optional router name to scope the lookup.
        :type router_name: str
        :return: The matching API route.
        :rtype: ApiRoute
        '''
        raise NotImplementedError()

    # * method: get_status_code
    @abstractmethod
    def get_status_code(self, error_code: str) -> int:
        '''
        Retrieve the HTTP status code mapped to a given error code.

        :param error_code: The error code to look up.
        :type error_code: str
        :return: The corresponding HTTP status code.
        :rtype: int
        '''
        raise NotImplementedError()