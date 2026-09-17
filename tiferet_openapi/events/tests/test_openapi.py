'''Tiferet OpenAPI Domain Event Tests'''

# *** imports

# ** core
from unittest import mock

# ** infra
import pytest
from tiferet import TiferetError, use_tester

# ** app
from ...domain import ApiRoute, ApiRouter
from ...interfaces import OpenApiService
from ..openapi import GetRouters, GetRoute, GetStatusCode

# *** fixtures

# ** fixture: mock_openapi_service
@pytest.fixture
def mock_openapi_service() -> OpenApiService:
    '''
    A mock OpenApiService for testing.

    :return: A mock OpenApiService instance.
    :rtype: OpenApiService
    '''

    return mock.Mock(spec=OpenApiService)

# ** fixture: sample_route
@pytest.fixture
def sample_route() -> ApiRoute:
    '''
    A sample ApiRoute instance.

    :return: An ApiRoute instance.
    :rtype: ApiRoute
    '''

    return ApiRoute(
        id='add',
        endpoint='calc.add',
        path='/add',
        methods=['POST'],
        status_code=200,
    )

# ** fixture: sample_router
@pytest.fixture
def sample_router(sample_route: ApiRoute) -> ApiRouter:
    '''
    A sample ApiRouter instance.

    :param sample_route: A sample ApiRoute instance.
    :type sample_route: ApiRoute
    :return: An ApiRouter instance.
    :rtype: ApiRouter
    '''

    return ApiRouter(
        name='calc',
        prefix='/api',
        routes=[sample_route],
    )

# *** testers

# ** tester: test_get_routers
@use_tester(
    type='domain_event',
    target_cls=GetRouters,
    dependencies={
        'openapi_service': {
            'module_path': 'tiferet_openapi.interfaces',
            'class_name': 'OpenApiService',
        },
    },
)
class TestGetRouters:
    '''
    Bound domain-event tester for GetRouters.
    '''

    # * test: get_routers_success
    def test_get_routers_success(
            self,
            test_ctx,
            mock_openapi_service: OpenApiService,
            sample_router: ApiRouter,
        ) -> None:
        '''
        Test that GetRouters returns the list from the mock service.

        :param test_ctx: The bound domain-event tester context.
        :type test_ctx: object
        :param mock_openapi_service: The mock OpenAPI service.
        :type mock_openapi_service: OpenApiService
        :param sample_router: The sample router.
        :type sample_router: ApiRouter
        :return: None
        :rtype: None
        '''

        # Arrange the service to return a list of routers.
        mock_openapi_service.get_routers.return_value = [sample_router]

        # Execute the event via the tester handle helper.
        result = test_ctx.handle(
            dependencies={'openapi_service': mock_openapi_service},
        )

        # Assert the result matches the expected routers.
        assert result == [sample_router]
        mock_openapi_service.get_routers.assert_called_once()

# ** tester: test_get_route
@use_tester(
    type='domain_event',
    target_cls=GetRoute,
    dependencies={
        'openapi_service': {
            'module_path': 'tiferet_openapi.interfaces',
            'class_name': 'OpenApiService',
        },
    },
    sample_kwargs={'endpoint': 'calc.add'},
)
class TestGetRoute:
    '''
    Bound domain-event tester for GetRoute.
    '''

    # * test: get_route_success
    def test_get_route_success(
            self,
            test_ctx,
            mock_openapi_service: OpenApiService,
            sample_route: ApiRoute,
        ) -> None:
        '''
        Test that GetRoute correctly parses "calc.add" into router_name="calc", route_id="add".

        :param test_ctx: The bound domain-event tester context.
        :type test_ctx: object
        :param mock_openapi_service: The mock OpenAPI service.
        :type mock_openapi_service: OpenApiService
        :param sample_route: The sample route.
        :type sample_route: ApiRoute
        :return: None
        :rtype: None
        '''

        # Arrange the service to return the sample route.
        mock_openapi_service.get_route.return_value = sample_route

        # Execute the event via the tester handle helper.
        result = test_ctx.handle(
            dependencies={'openapi_service': mock_openapi_service},
            endpoint='calc.add',
        )

        # Assert the result and service call.
        assert result is sample_route
        mock_openapi_service.get_route.assert_called_once_with('add', 'calc')

    # * test: get_route_not_found
    def test_get_route_not_found(
            self,
            test_ctx,
            mock_openapi_service: OpenApiService,
        ) -> None:
        '''
        Test that GetRoute raises OPENAPI_ROUTE_NOT_FOUND when route is None.

        :param test_ctx: The bound domain-event tester context.
        :type test_ctx: object
        :param mock_openapi_service: The mock OpenAPI service.
        :type mock_openapi_service: OpenApiService
        :return: None
        :rtype: None
        '''

        # Arrange the service to return None.
        mock_openapi_service.get_route.return_value = None

        # Execute and expect a TiferetError.
        with pytest.raises(TiferetError) as exc_info:
            test_ctx.handle(
                dependencies={'openapi_service': mock_openapi_service},
                endpoint='calc.missing',
            )

        # Assert the error code.
        assert exc_info.value.error_code == 'OPENAPI_ROUTE_NOT_FOUND'

    # * test: get_route_single_segment
    def test_get_route_single_segment(
            self,
            test_ctx,
            mock_openapi_service: OpenApiService,
            sample_route: ApiRoute,
        ) -> None:
        '''
        Test that GetRoute handles single-segment endpoints (no router prefix).

        :param test_ctx: The bound domain-event tester context.
        :type test_ctx: object
        :param mock_openapi_service: The mock OpenAPI service.
        :type mock_openapi_service: OpenApiService
        :param sample_route: The sample route.
        :type sample_route: ApiRoute
        :return: None
        :rtype: None
        '''

        # Arrange the service to return the sample route.
        mock_openapi_service.get_route.return_value = sample_route

        # Execute with a single-segment endpoint.
        result = test_ctx.handle(
            dependencies={'openapi_service': mock_openapi_service},
            endpoint='add',
        )

        # Assert the service was called with no router_name.
        assert result is sample_route
        mock_openapi_service.get_route.assert_called_once_with('add', None)

# ** tester: test_get_status_code
@use_tester(
    type='domain_event',
    target_cls=GetStatusCode,
    dependencies={
        'openapi_service': {
            'module_path': 'tiferet_openapi.interfaces',
            'class_name': 'OpenApiService',
        },
    },
    sample_kwargs={'error_code': 'NOT_FOUND'},
)
class TestGetStatusCode:
    '''
    Bound domain-event tester for GetStatusCode.
    '''

    # * test: get_status_code_success
    def test_get_status_code_success(
            self,
            test_ctx,
            mock_openapi_service: OpenApiService,
        ) -> None:
        '''
        Test that GetStatusCode returns the status code from the mock service.

        :param test_ctx: The bound domain-event tester context.
        :type test_ctx: object
        :param mock_openapi_service: The mock OpenAPI service.
        :type mock_openapi_service: OpenApiService
        :return: None
        :rtype: None
        '''

        # Arrange the service to return 404.
        mock_openapi_service.get_status_code.return_value = 404

        # Execute the event via the tester handle helper.
        result = test_ctx.handle(
            dependencies={'openapi_service': mock_openapi_service},
            error_code='NOT_FOUND',
        )

        # Assert the result and service call.
        assert result == 404
        mock_openapi_service.get_status_code.assert_called_once_with('NOT_FOUND')
