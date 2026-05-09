'''Tiferet OpenAPI YAML Repository'''

# *** imports

# ** core
from typing import List

# ** infra
from tiferet import Yaml

# ** app
from ..interfaces import OpenApiService
from ..domain import ApiRoute, ApiRouter
from ..mappers import (
    ApiRouterAggregate,
    ApiRouterYamlObject,
)


# *** repos

# ** repo: open_api_yaml_repository
class OpenApiYamlRepository(OpenApiService):
    '''
    YAML-backed repository for OpenAPI router and error-to-status-code configurations.
    '''

    # * attribute: openapi_yaml_file
    openapi_yaml_file: str

    # * attribute: encoding
    encoding: str

    # * attribute: root_key
    root_key: str

    # * init
    def __init__(self, openapi_yaml_file: str, root_key: str = 'openapi', encoding: str = 'utf-8') -> None:
        '''
        Initialize the OpenAPI YAML repository.

        :param openapi_yaml_file: The YAML configuration file path.
        :type openapi_yaml_file: str
        :param root_key: The root key in the YAML file (e.g. 'openapi', 'flask', 'fast').
        :type root_key: str
        :param encoding: The file encoding (default is 'utf-8').
        :type encoding: str
        '''

        # Set the repository attributes.
        self.openapi_yaml_file = openapi_yaml_file
        self.encoding = encoding
        self.root_key = root_key

    # * method: get_routers
    def get_routers(self) -> List[ApiRouterAggregate]:
        '''
        Retrieve all configured API routers from the YAML file.

        :return: A list of API router aggregates.
        :rtype: List[ApiRouterAggregate]
        '''

        # Load the routers mapping from the configuration file.
        routers_data = Yaml(
            self.openapi_yaml_file,
            encoding=self.encoding,
        ).load(
            start_node=lambda data: data.get(self.root_key, {}).get('routers', {})
        )

        # Map each entry via ApiRouterYamlObject and return the list.
        return [
            ApiRouterYamlObject.model_validate(
                dict(name=name, **data)
            ).map()
            for name, data in routers_data.items()
        ]

    # * method: get_route
    def get_route(self, route_id: str, router_name: str = None) -> ApiRoute | None:
        '''
        Retrieve a single API route by its identifier.

        :param route_id: The unique identifier of the route.
        :type route_id: str
        :param router_name: Optional router name to scope the lookup.
        :type router_name: str
        :return: The matching API route, or None if not found.
        :rtype: ApiRoute | None
        '''

        # Load all routers.
        routers = self.get_routers()

        # Iterate over routers, filtering by router_name if provided.
        for router in routers:
            if router_name and router.name != router_name:
                continue

            # Search for the route within this router.
            for route in router.routes:
                if route.id == route_id:
                    return route

        # Return None if no matching route was found.
        return None

    # * method: get_status_code
    def get_status_code(self, error_code: str) -> int:
        '''
        Retrieve the HTTP status code mapped to a given error code.

        :param error_code: The error code to look up.
        :type error_code: str
        :return: The corresponding HTTP status code, defaulting to 500.
        :rtype: int
        '''

        # Load the errors mapping from the configuration file.
        errors_data = Yaml(
            self.openapi_yaml_file,
            encoding=self.encoding,
        ).load(
            start_node=lambda data: data.get(self.root_key, {}).get('errors', {})
        )

        # Return the mapped status code, defaulting to 500.
        return errors_data.get(error_code, 500)