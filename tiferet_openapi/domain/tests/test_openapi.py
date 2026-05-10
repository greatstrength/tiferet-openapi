'''Tiferet OpenAPI Domain Object Tests'''

# *** imports

# ** infra
import pytest

# ** app
from ..openapi import ApiRoute, ApiRouter


# *** fixtures

# ** fixture: sample_route_data
@pytest.fixture
def sample_route_data() -> dict:
    '''
    Sample data for constructing an ApiRoute.

    :return: A dictionary of route data.
    :rtype: dict
    '''

    return dict(
        id='get_users',
        endpoint='users.get_users',
        path='/users',
        methods=['GET'],
        status_code=200,
    )


# ** fixture: sample_route
@pytest.fixture
def sample_route(sample_route_data: dict) -> ApiRoute:
    '''
    A sample ApiRoute instance.

    :param sample_route_data: The sample route data.
    :type sample_route_data: dict
    :return: An ApiRoute instance.
    :rtype: ApiRoute
    '''

    return ApiRoute(**sample_route_data)


# ** fixture: sample_router_data
@pytest.fixture
def sample_router_data(sample_route: ApiRoute) -> dict:
    '''
    Sample data for constructing an ApiRouter.

    :param sample_route: A sample ApiRoute instance.
    :type sample_route: ApiRoute
    :return: A dictionary of router data.
    :rtype: dict
    '''

    return dict(
        name='users',
        prefix='/api/v1',
        routes=[sample_route],
    )


# *** tests

# ** test: api_route_constructor
def test_api_route_constructor(sample_route: ApiRoute, sample_route_data: dict) -> None:
    '''
    Test that ApiRoute can be instantiated with all required fields.

    :param sample_route: The sample ApiRoute instance.
    :type sample_route: ApiRoute
    :param sample_route_data: The sample route data.
    :type sample_route_data: dict
    '''

    # Verify all fields match the provided data.
    assert sample_route.id == sample_route_data['id']
    assert sample_route.endpoint == sample_route_data['endpoint']
    assert sample_route.path == sample_route_data['path']
    assert sample_route.methods == sample_route_data['methods']
    assert sample_route.status_code == sample_route_data['status_code']


# ** test: api_route_status_code_default
def test_api_route_status_code_default() -> None:
    '''
    Test that status_code defaults to 200 when not provided.
    '''

    # Create a route without specifying status_code.
    route = ApiRoute(
        id='create_user',
        endpoint='users.create_user',
        path='/users',
        methods=['POST'],
    )

    # Verify the default status_code.
    assert route.status_code == 200


# ** test: api_router_constructor
def test_api_router_constructor(sample_router_data: dict, sample_route: ApiRoute) -> None:
    '''
    Test that ApiRouter can be instantiated with nested ApiRoute instances.

    :param sample_router_data: The sample router data.
    :type sample_router_data: dict
    :param sample_route: The sample ApiRoute instance.
    :type sample_route: ApiRoute
    '''

    # Create the router.
    router = ApiRouter(**sample_router_data)

    # Verify all fields match the provided data.
    assert router.name == sample_router_data['name']
    assert router.prefix == sample_router_data['prefix']
    assert len(router.routes) == 1
    assert router.routes[0].id == sample_route.id


# ** test: api_router_prefix_default
def test_api_router_prefix_default() -> None:
    '''
    Test that prefix defaults to None when not provided.
    '''

    # Create a router without specifying prefix.
    router = ApiRouter(name='default')

    # Verify the default prefix.
    assert router.prefix is None


# ** test: api_route_swagger_fields
def test_api_route_swagger_fields() -> None:
    '''
    Test that ApiRoute accepts all 5 optional Swagger metadata fields.
    '''

    # Create a route with all Swagger metadata fields.
    route = ApiRoute(
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

    # Verify all Swagger metadata fields.
    assert route.summary == 'Add two numbers'
    assert route.description == 'Adds two numbers and returns the result'
    assert route.tags == ['calculator', 'arithmetic']
    assert route.request_model == 'app.domain.request.AddNumberRequest'
    assert route.response_model == 'app.domain.request.CalculatorResponse'


# ** test: api_route_swagger_fields_defaults
def test_api_route_swagger_fields_defaults() -> None:
    '''
    Test that new Swagger metadata fields default correctly when not provided.
    '''

    # Create a route without Swagger metadata fields.
    route = ApiRoute(
        id='get_users',
        endpoint='users.get_users',
        path='/users',
        methods=['GET'],
    )

    # Verify defaults.
    assert route.summary is None
    assert route.description is None
    assert route.tags == []
    assert route.request_model is None
    assert route.response_model is None


# ** test: api_router_routes_default
def test_api_router_routes_default() -> None:
    '''
    Test that routes defaults to an empty list when not provided.
    '''

    # Create a router without specifying routes.
    router = ApiRouter(name='empty')

    # Verify the default routes.
    assert router.routes == []
