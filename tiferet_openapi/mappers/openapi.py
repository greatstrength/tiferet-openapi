'''Tiferet OpenAPI Mapper Objects'''

# *** imports

# ** core
from typing import Any, ClassVar, Dict, List

# ** infra
from pydantic import Field
from tiferet import Aggregate, TransferObject

# ** app
from ..domain import ApiRoute, ApiRouter


# *** mappers

# ** mapper: api_route_aggregate
class ApiRouteAggregate(ApiRoute, Aggregate):
    '''
    Aggregate for the ApiRoute domain object.
    '''
    pass


# ** mapper: api_router_aggregate
class ApiRouterAggregate(ApiRouter, Aggregate):
    '''
    Aggregate for the ApiRouter domain object.
    '''

    # * method: add_route
    def add_route(self,
            endpoint: str,
            path: str,
            methods: List[str],
            status_code: int = 200,
        ) -> ApiRouteAggregate:
        '''
        Add a new route to this router.

        :param endpoint: The route endpoint identifier.
        :type endpoint: str
        :param path: The URL path.
        :type path: str
        :param methods: The HTTP methods.
        :type methods: List[str]
        :param status_code: The default HTTP status code.
        :type status_code: int
        :return: The created route aggregate.
        :rtype: ApiRouteAggregate
        '''

        # Create the route with a fully-qualified endpoint.
        route = ApiRouteAggregate(
            id=endpoint,
            endpoint=f'{self.name}.{endpoint}',
            path=path,
            methods=methods,
            status_code=status_code,
        )

        # Append the route to the routes list.
        routes = list(self.routes)
        routes.append(route)
        self.routes = routes

        # Return the created route.
        return route

    # * method: remove_route
    def remove_route(self, route_id: str) -> None:
        '''
        Remove a route from this router by its ID.

        :param route_id: The route identifier to remove.
        :type route_id: str
        :return: None
        :rtype: None
        '''

        # Filter out the route with the given ID.
        self.routes = [r for r in self.routes if r.id != route_id]


# ** mapper: api_route_yaml_object
class ApiRouteYamlObject(ApiRoute, TransferObject):
    '''
    A YAML data representation of an API route.
    '''

    # * attribute: _ROLES
    _ROLES: ClassVar[Dict[str, Dict[str, Any]]] = {
        'to_model': {},
        'to_data.yaml': {
            'by_alias': True,
            'exclude': {'id', 'endpoint'},
        },
    }

    # * attribute: id
    id: str | None = Field(
        default=None,
        description='The unique identifier of the route.',
    )

    # * attribute: endpoint
    endpoint: str | None = Field(
        default=None,
        description='The fully-qualified endpoint (router_name.route_id).',
    )

    # * method: map
    def map(self, id: str = None, endpoint: str = None, **overrides) -> ApiRouteAggregate:
        '''
        Map the route YAML data to a route aggregate.

        :param id: The route identifier.
        :type id: str
        :param endpoint: The fully-qualified endpoint.
        :type endpoint: str
        :param overrides: Additional keyword arguments.
        :type overrides: dict
        :return: A new route aggregate.
        :rtype: ApiRouteAggregate
        '''

        # Map the route data with id and endpoint overrides.
        return super().map(
            ApiRouteAggregate,
            id=id or self.id,
            endpoint=endpoint or self.endpoint,
            **overrides,
        )

    # * method: from_model
    @classmethod
    def from_model(cls, route: ApiRoute, **overrides) -> 'ApiRouteYamlObject':
        '''
        Create an ApiRouteYamlObject from an ApiRoute model.

        :param route: The route model.
        :type route: ApiRoute
        :param overrides: Additional keyword arguments.
        :type overrides: dict
        :return: A new ApiRouteYamlObject.
        :rtype: ApiRouteYamlObject
        '''

        # Create a new transfer object from the model.
        return super().from_model(route, **overrides)


# ** mapper: api_router_yaml_object
class ApiRouterYamlObject(ApiRouter, TransferObject):
    '''
    A YAML data representation of an API router.
    '''

    # * attribute: _ROLES
    _ROLES: ClassVar[Dict[str, Dict[str, Any]]] = {
        'to_model': {'exclude': {'routes'}},
        'to_data.yaml': {
            'by_alias': True,
            'exclude': {'name'},
        },
    }

    # * attribute: name
    name: str | None = Field(
        default=None,
        description='The name of the router.',
    )

    # * attribute: routes
    routes: Dict[str, ApiRouteYamlObject] = Field(
        default_factory=dict,
        description='Routes in this router, keyed by route ID.',
    )

    # * method: map
    def map(self, **overrides) -> ApiRouterAggregate:
        '''
        Map the router YAML data to a router aggregate.

        :param overrides: Additional keyword arguments.
        :type overrides: dict
        :return: A new router aggregate.
        :rtype: ApiRouterAggregate
        '''

        # Convert dict routes to list with endpoint derivation.
        router_name = overrides.get('name', self.name)
        routes = [
            route_obj.map(
                id=route_id,
                endpoint=f'{router_name}.{route_id}',
            )
            for route_id, route_obj in (self.routes or {}).items()
        ]

        # Map the router data with converted routes.
        return super().map(
            ApiRouterAggregate,
            routes=routes,
            **overrides,
        )

    # * method: from_model
    @classmethod
    def from_model(cls, router: ApiRouter, **overrides) -> 'ApiRouterYamlObject':
        '''
        Create an ApiRouterYamlObject from an ApiRouter model.

        :param router: The router model.
        :type router: ApiRouter
        :param overrides: Additional keyword arguments.
        :type overrides: dict
        :return: A new ApiRouterYamlObject.
        :rtype: ApiRouterYamlObject
        '''

        # Convert list routes to dict keyed by route ID.
        routes = {
            route.id: ApiRouteYamlObject.from_model(route)
            for route in router.routes
        }

        # Create a new transfer object from the model.
        return super().from_model(router, routes=routes, **overrides)