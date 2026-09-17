'''Tiferet OpenAPI Domain Object Tests'''

# *** imports

# ** app
from tiferet import use_tester
from ..openapi import ApiRoute, ApiRouter

# *** constants

# ** constant: sample_route_data
SAMPLE_ROUTE_DATA = {
    'id': 'get_users',
    'endpoint': 'users.get_users',
    'path': '/users',
    'methods': ['GET'],
    'status_code': 200,
}

# ** constant: sample_router_data
SAMPLE_ROUTER_DATA = {
    'name': 'users',
    'prefix': '/api/v1',
    'routes': [SAMPLE_ROUTE_DATA],
}

# *** testers

# ** tester: test_api_route
@use_tester(
    type='domain',
    target_cls=ApiRoute,
    sample_data=SAMPLE_ROUTE_DATA,
    equality_fields=['id', 'endpoint', 'path', 'methods', 'status_code'],
)
class TestApiRoute:
    '''
    Bound domain tester for ApiRoute.
    '''

    # * test: api_route_constructor
    def test_api_route_constructor(self, test_ctx) -> None:
        '''
        Test that ApiRoute can be instantiated with all required fields.

        :param test_ctx: The bound domain tester context.
        :type test_ctx: object
        :return: None
        :rtype: None
        '''

        # Construct from sample data and assert field equality.
        test_ctx.assert_new()

    # * test: api_route_status_code_default
    def test_api_route_status_code_default(self) -> None:
        '''
        Test that status_code defaults to 200 when not provided.

        :return: None
        :rtype: None
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

    # * test: api_route_swagger_fields
    def test_api_route_swagger_fields(self) -> None:
        '''
        Test that ApiRoute accepts all 5 optional Swagger metadata fields.

        :return: None
        :rtype: None
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

    # * test: api_route_swagger_fields_defaults
    def test_api_route_swagger_fields_defaults(self) -> None:
        '''
        Test that new Swagger metadata fields default correctly when not provided.

        :return: None
        :rtype: None
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

# ** tester: test_api_router
@use_tester(
    type='domain',
    target_cls=ApiRouter,
    sample_data=SAMPLE_ROUTER_DATA,
    equality_fields=['name', 'prefix'],
)
class TestApiRouter:
    '''
    Bound domain tester for ApiRouter.
    '''

    # * test: api_router_constructor
    def test_api_router_constructor(self, test_ctx) -> None:
        '''
        Test that ApiRouter can be instantiated with nested ApiRoute instances.

        :param test_ctx: The bound domain tester context.
        :type test_ctx: object
        :return: None
        :rtype: None
        '''

        # Construct the router from sample data.
        router = test_ctx.make_target()

        # Assert identity fields and nested route identity.
        test_ctx.assert_new(target=router)
        assert len(router.routes) == 1
        assert router.routes[0].id == SAMPLE_ROUTE_DATA['id']

    # * test: api_router_prefix_default
    def test_api_router_prefix_default(self) -> None:
        '''
        Test that prefix defaults to None when not provided.

        :return: None
        :rtype: None
        '''

        # Create a router without specifying prefix.
        router = ApiRouter(name='default')

        # Verify the default prefix.
        assert router.prefix is None

    # * test: api_router_routes_default
    def test_api_router_routes_default(self) -> None:
        '''
        Test that routes defaults to an empty list when not provided.

        :return: None
        :rtype: None
        '''

        # Create a router without specifying routes.
        router = ApiRouter(name='empty')

        # Verify the default routes.
        assert router.routes == []
