'''Tiferet OpenAPI Mapper Tests'''

# *** imports

# ** app
from tiferet import use_tester
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

# *** testers

# ** tester: test_api_route_aggregate
@use_tester(
    type='aggregate',
    target_cls=ApiRouteAggregate,
    sample_data=ROUTE_AGGREGATE_DATA,
    equality_fields=['id', 'endpoint', 'path', 'methods', 'status_code'],
)
class TestApiRouteAggregate:
    '''
    Bound aggregate tester for ApiRouteAggregate.
    '''

    # * test: api_route_aggregate_constructor
    def test_api_route_aggregate_constructor(self, test_ctx) -> None:
        '''
        Test that ApiRouteAggregate can be instantiated with all fields.

        :param test_ctx: The bound aggregate tester context.
        :type test_ctx: object
        :return: None
        :rtype: None
        '''

        # Construct from sample data and assert field equality.
        test_ctx.assert_new()

# ** tester: test_api_router_aggregate
@use_tester(
    type='aggregate',
    target_cls=ApiRouterAggregate,
    sample_data=ROUTER_AGGREGATE_DATA,
    equality_fields=['name', 'prefix'],
)
class TestApiRouterAggregate:
    '''
    Bound aggregate tester for ApiRouterAggregate.
    '''

    # * test: api_router_aggregate_add_route
    def test_api_router_aggregate_add_route(self, test_ctx) -> None:
        '''
        Test that add_route creates a route with the correct fully-qualified endpoint.

        :param test_ctx: The bound aggregate tester context.
        :type test_ctx: object
        :return: None
        :rtype: None
        '''

        # Add a route to the router.
        router = test_ctx.make_target()
        route = router.add_route(
            endpoint='get_users',
            path='/users',
            methods=['GET'],
        )

        # Verify the route was added with the correct endpoint.
        assert len(router.routes) == 1
        assert route.id == 'get_users'
        assert route.endpoint == 'users.get_users'
        assert route.path == '/users'
        assert route.methods == ['GET']
        assert route.status_code == 200

    # * test: api_router_aggregate_remove_route
    def test_api_router_aggregate_remove_route(self, test_ctx) -> None:
        '''
        Test that remove_route removes the route by ID.

        :param test_ctx: The bound aggregate tester context.
        :type test_ctx: object
        :return: None
        :rtype: None
        '''

        # Add a route, then remove it.
        router = test_ctx.make_target()
        router.add_route(endpoint='get_users', path='/users', methods=['GET'])
        assert len(router.routes) == 1

        # Remove the route.
        router.remove_route('get_users')

        # Verify the route was removed.
        assert len(router.routes) == 0

# ** tester: test_api_route_yaml_object
@use_tester(
    type='transfer_object',
    target_cls=ApiRouteYamlObject,
    aggregate_cls=ApiRouteAggregate,
    sample_data=ROUTE_YAML_DATA,
    aggregate_sample_data=ROUTE_AGGREGATE_DATA,
    map_kwargs={'id': 'get_users', 'endpoint': 'users.get_users'},
    equality_fields=['id', 'endpoint', 'path', 'methods', 'status_code'],
)
class TestApiRouteYamlObject:
    '''
    Bound transfer-object tester for ApiRouteYamlObject.
    '''

    # * test: api_route_yaml_object_map
    def test_api_route_yaml_object_map(self, test_ctx) -> None:
        '''
        Test that ApiRouteYamlObject.map() produces a valid ApiRouteAggregate.

        :param test_ctx: The bound transfer-object tester context.
        :type test_ctx: object
        :return: None
        :rtype: None
        '''

        # Map sample YAML data onto the aggregate.
        test_ctx.assert_map()

    # * test: api_route_from_model_round_trip
    def test_api_route_from_model_round_trip(self, test_ctx) -> None:
        '''
        Test that from_model round-trips correctly for ApiRoute.

        :param test_ctx: The bound transfer-object tester context.
        :type test_ctx: object
        :return: None
        :rtype: None
        '''

        # Round-trip the aggregate through the YAML object.
        test_ctx.assert_round_trip()

    # * test: api_route_yaml_object_map_with_swagger_fields
    def test_api_route_yaml_object_map_with_swagger_fields(self) -> None:
        '''
        Test that ApiRouteYamlObject.map() preserves Swagger metadata fields.

        :return: None
        :rtype: None
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

    # * test: api_route_swagger_fields_round_trip
    def test_api_route_swagger_fields_round_trip(self) -> None:
        '''
        Test that from_model round-trips correctly for ApiRoute with Swagger metadata fields.

        :return: None
        :rtype: None
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

    # * test: api_route_yaml_object_map_without_swagger_fields
    def test_api_route_yaml_object_map_without_swagger_fields(self) -> None:
        '''
        Test that ApiRouteYamlObject.map() works without Swagger metadata (backward compat).

        :return: None
        :rtype: None
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

    # * test: api_route_yaml_object_to_data_yaml_excludes_only_id_and_endpoint
    def test_api_route_yaml_object_to_data_yaml_excludes_only_id_and_endpoint(self) -> None:
        '''
        Test that the to_data.yaml role excludes only id and endpoint.

        :return: None
        :rtype: None
        '''

        # Verify the exclude set no longer drops tags.
        assert ApiRouteYamlObject._ROLES['to_data.yaml']['exclude'] == {'id', 'endpoint'}

    # * test: api_route_tags_round_trip_to_data_yaml
    def test_api_route_tags_round_trip_to_data_yaml(self) -> None:
        '''
        Test that a non-empty tags list survives to_data.yaml serialization.

        :return: None
        :rtype: None
        '''

        # Construct a route aggregate with tags.
        aggregate = ApiRouteAggregate(
            id='add',
            endpoint='calc.add',
            path='/add',
            methods=['POST'],
            status_code=200,
            tags=['calculator', 'arithmetic'],
        )

        # Serialize via the YAML write role.
        yaml_obj = ApiRouteYamlObject.from_model(aggregate)
        data = yaml_obj.to_primitive(role='to_data.yaml')

        # Verify tags survive the round-trip.
        assert 'tags' in data
        assert data['tags'] == ['calculator', 'arithmetic']

# ** tester: test_api_router_yaml_object
@use_tester(
    type='transfer_object',
    target_cls=ApiRouterYamlObject,
    aggregate_cls=ApiRouterAggregate,
    sample_data=ROUTER_YAML_DATA,
    aggregate_sample_data=ROUTER_AGGREGATE_DATA,
    map_kwargs={'name': 'users'},
    equality_fields=['name', 'prefix'],
)
class TestApiRouterYamlObject:
    '''
    Bound transfer-object tester for ApiRouterYamlObject.
    '''

    # * test: api_router_yaml_object_map
    def test_api_router_yaml_object_map(self) -> None:
        '''
        Test that ApiRouterYamlObject.map() produces a valid ApiRouterAggregate with nested routes.

        :return: None
        :rtype: None
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

    # * test: api_router_from_model_round_trip
    def test_api_router_from_model_round_trip(self, test_ctx) -> None:
        '''
        Test that from_model round-trips correctly for ApiRouter.

        :param test_ctx: The bound transfer-object tester context.
        :type test_ctx: object
        :return: None
        :rtype: None
        '''

        # Build a router aggregate with a route.
        router = test_ctx.make_target()
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
