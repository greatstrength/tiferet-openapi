'''Tiferet OpenAPI Mapper Tests'''

# *** imports

# ** infra
import pytest

# ** app
from ..openapi import (
    ApiRouteAggregate,
    ApiRouterAggregate,
    ApiRouteYamlObject,
    ApiRouterYamlObject,
)


# *** constants

# ** constant: route_aggregate_data
ROUTE_AGGREGATE_DATA = dict(
    id='get_users',
    endpoint='users.get_users',
    path='/users',
    methods=['GET'],
    status_code=200,
)

# ** constant: router_aggregate_data
ROUTER_AGGREGATE_DATA = dict(
    name='users',
    prefix='/api/v1',
    routes=[],
)

# ** constant: route_yaml_data
ROUTE_YAML_DATA = dict(
    path='/users',
    methods=['GET'],
    status_code=200,
)

# ** constant: router_yaml_data
ROUTER_YAML_DATA = dict(
    prefix='/api/v1',
    routes={
        'get_users': ROUTE_YAML_DATA,
    },
)


# *** fixtures

# ** fixture: route_aggregate
@pytest.fixture
def route_aggregate() -> ApiRouteAggregate:
    '''
    A sample ApiRouteAggregate instance.

    :return: An ApiRouteAggregate instance.
    :rtype: ApiRouteAggregate
    '''

    return ApiRouteAggregate(**ROUTE_AGGREGATE_DATA)


# ** fixture: router_aggregate
@pytest.fixture
def router_aggregate() -> ApiRouterAggregate:
    '''
    A sample ApiRouterAggregate instance with no routes.

    :return: An ApiRouterAggregate instance.
    :rtype: ApiRouterAggregate
    '''

    return ApiRouterAggregate(**ROUTER_AGGREGATE_DATA)


# *** tests

# ** test: api_route_aggregate_constructor
def test_api_route_aggregate_constructor(route_aggregate: ApiRouteAggregate) -> None:
    '''
    Test that ApiRouteAggregate can be instantiated with all fields.

    :param route_aggregate: The sample route aggregate.
    :type route_aggregate: ApiRouteAggregate
    '''

    # Verify all fields match the provided data.
    assert route_aggregate.id == ROUTE_AGGREGATE_DATA['id']
    assert route_aggregate.endpoint == ROUTE_AGGREGATE_DATA['endpoint']
    assert route_aggregate.path == ROUTE_AGGREGATE_DATA['path']
    assert route_aggregate.methods == ROUTE_AGGREGATE_DATA['methods']
    assert route_aggregate.status_code == ROUTE_AGGREGATE_DATA['status_code']


# ** test: api_router_aggregate_add_route
def test_api_router_aggregate_add_route(router_aggregate: ApiRouterAggregate) -> None:
    '''
    Test that add_route creates a route with the correct fully-qualified endpoint.

    :param router_aggregate: The sample router aggregate.
    :type router_aggregate: ApiRouterAggregate
    '''

    # Add a route to the router.
    route = router_aggregate.add_route(
        endpoint='get_users',
        path='/users',
        methods=['GET'],
    )

    # Verify the route was added with the correct endpoint.
    assert len(router_aggregate.routes) == 1
    assert route.id == 'get_users'
    assert route.endpoint == 'users.get_users'
    assert route.path == '/users'
    assert route.methods == ['GET']
    assert route.status_code == 200


# ** test: api_router_aggregate_remove_route
def test_api_router_aggregate_remove_route(router_aggregate: ApiRouterAggregate) -> None:
    '''
    Test that remove_route removes the route by ID.

    :param router_aggregate: The sample router aggregate.
    :type router_aggregate: ApiRouterAggregate
    '''

    # Add a route, then remove it.
    router_aggregate.add_route(endpoint='get_users', path='/users', methods=['GET'])
    assert len(router_aggregate.routes) == 1

    # Remove the route.
    router_aggregate.remove_route('get_users')

    # Verify the route was removed.
    assert len(router_aggregate.routes) == 0


# ** test: api_route_yaml_object_map
def test_api_route_yaml_object_map() -> None:
    '''
    Test that ApiRouteYamlObject.map() produces a valid ApiRouteAggregate.
    '''

    # Create a route YAML object and map it.
    yaml_obj = ApiRouteYamlObject.model_validate(ROUTE_YAML_DATA)
    aggregate = yaml_obj.map(id='get_users', endpoint='users.get_users')

    # Verify the aggregate has the correct fields.
    assert isinstance(aggregate, ApiRouteAggregate)
    assert aggregate.id == 'get_users'
    assert aggregate.endpoint == 'users.get_users'
    assert aggregate.path == '/users'
    assert aggregate.methods == ['GET']
    assert aggregate.status_code == 200


# ** test: api_router_yaml_object_map
def test_api_router_yaml_object_map() -> None:
    '''
    Test that ApiRouterYamlObject.map() produces a valid ApiRouterAggregate with nested routes.
    '''

    # Create a router YAML object and map it.
    yaml_obj = ApiRouterYamlObject.model_validate(ROUTER_YAML_DATA)
    aggregate = yaml_obj.map(name='users')

    # Verify the aggregate has the correct fields.
    assert isinstance(aggregate, ApiRouterAggregate)
    assert aggregate.name == 'users'
    assert aggregate.prefix == '/api/v1'
    assert len(aggregate.routes) == 1
    assert aggregate.routes[0].id == 'get_users'
    assert aggregate.routes[0].endpoint == 'users.get_users'


# ** test: api_route_from_model_round_trip
def test_api_route_from_model_round_trip(route_aggregate: ApiRouteAggregate) -> None:
    '''
    Test that from_model round-trips correctly for ApiRoute.

    :param route_aggregate: The sample route aggregate.
    :type route_aggregate: ApiRouteAggregate
    '''

    # Convert aggregate to YAML object and back.
    yaml_obj = ApiRouteYamlObject.from_model(route_aggregate)
    result = yaml_obj.map()

    # Verify the round-trip preserves data.
    assert result.id == route_aggregate.id
    assert result.endpoint == route_aggregate.endpoint
    assert result.path == route_aggregate.path
    assert result.methods == route_aggregate.methods
    assert result.status_code == route_aggregate.status_code


# ** test: api_router_from_model_round_trip
def test_api_router_from_model_round_trip() -> None:
    '''
    Test that from_model round-trips correctly for ApiRouter.
    '''

    # Build a router aggregate with a route.
    router = ApiRouterAggregate(**ROUTER_AGGREGATE_DATA)
    router.add_route(endpoint='get_users', path='/users', methods=['GET'])

    # Convert to YAML object and back.
    yaml_obj = ApiRouterYamlObject.from_model(router)
    result = yaml_obj.map(name='users')

    # Verify the round-trip preserves data.
    assert result.name == router.name
    assert result.prefix == router.prefix
    assert len(result.routes) == 1
    assert result.routes[0].id == 'get_users'
    assert result.routes[0].endpoint == 'users.get_users'
    assert result.routes[0].path == '/users'


# ** test: api_route_yaml_object_map_with_swagger_fields
def test_api_route_yaml_object_map_with_swagger_fields() -> None:
    '''
    Test that ApiRouteYamlObject.map() preserves Swagger metadata fields.
    '''

    # Create a route YAML object with Swagger metadata fields.
    yaml_data = dict(
        path='/add',
        methods=['POST'],
        status_code=200,
        summary='Add two numbers',
        description='Adds two numbers and returns the result',
        tags=['calculator', 'arithmetic'],
        request_model='app.domain.request.AddNumberRequest',
        response_model='app.domain.request.CalculatorResponse',
    )
    yaml_obj = ApiRouteYamlObject.model_validate(yaml_data)
    aggregate = yaml_obj.map(id='add', endpoint='calc.add')

    # Verify Swagger metadata fields are preserved.
    assert aggregate.summary == 'Add two numbers'
    assert aggregate.description == 'Adds two numbers and returns the result'
    assert aggregate.tags == ['calculator', 'arithmetic']
    assert aggregate.request_model == 'app.domain.request.AddNumberRequest'
    assert aggregate.response_model == 'app.domain.request.CalculatorResponse'


# ** test: api_route_swagger_fields_round_trip
def test_api_route_swagger_fields_round_trip() -> None:
    '''
    Test that from_model round-trips correctly for ApiRoute with Swagger metadata fields.
    '''

    # Create a route aggregate with Swagger metadata fields.
    aggregate = ApiRouteAggregate(
        id='add',
        endpoint='calc.add',
        path='/add',
        methods=['POST'],
        status_code=200,
        summary='Add two numbers',
        description='Adds two numbers and returns the result',
        tags=['calculator', 'arithmetic'],
        request_model='app.domain.request.AddNumberRequest',
        response_model='app.domain.request.CalculatorResponse',
    )

    # Convert to YAML object and back.
    yaml_obj = ApiRouteYamlObject.from_model(aggregate)
    result = yaml_obj.map()

    # Verify round-trip preserves Swagger metadata.
    assert result.summary == aggregate.summary
    assert result.description == aggregate.description
    assert result.tags == aggregate.tags
    assert result.request_model == aggregate.request_model
    assert result.response_model == aggregate.response_model


# ** test: api_route_yaml_object_map_without_swagger_fields
def test_api_route_yaml_object_map_without_swagger_fields() -> None:
    '''
    Test that ApiRouteYamlObject.map() works without Swagger metadata (backward compat).
    '''

    # Create a route YAML object without Swagger metadata.
    yaml_obj = ApiRouteYamlObject.model_validate(ROUTE_YAML_DATA)
    aggregate = yaml_obj.map(id='get_users', endpoint='users.get_users')

    # Verify defaults for Swagger metadata fields.
    assert aggregate.summary is None
    assert aggregate.description is None
    assert aggregate.tags == []
    assert aggregate.request_model is None
    assert aggregate.response_model is None
