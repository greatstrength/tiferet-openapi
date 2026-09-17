'''Tiferet OpenAPI Context Tests'''

# *** imports

# ** core
from typing import Callable
from unittest import mock

# ** infra
import pytest
from tiferet import TiferetError, TiferetAPIError
from tiferet.contexts.app import AppSessionContext
from tiferet.domain import AppSession
from tiferet.events import DomainEvent

# ** app
from ...domain import ApiRoute, ApiRouter
from ..openapi import OpenApiSessionContext
from ..request import OpenApiRequestContext


# *** fixtures

# ** fixture: app_session
@pytest.fixture
def app_session() -> AppSession:
    '''
    AppSession bound to the OpenAPI session context under test.

    :return: An AppSession domain object.
    :rtype: AppSession
    '''

    return AppSession(id='test_api', name='Test API')


# ** fixture: get_dependency
@pytest.fixture
def get_dependency() -> Callable:
    '''
    Mock DI resolution handler.

    :return: A mock callable.
    :rtype: Callable
    '''

    return mock.Mock()


# ** fixture: response_handler
@pytest.fixture
def response_handler() -> Callable:
    '''
    Mock response-building handler.

    :return: A mock callable returning a sample response.
    :rtype: Callable
    '''

    return mock.Mock(return_value={'sum': 3})


# ** fixture: raise_error_handler
@pytest.fixture
def raise_error_handler() -> Callable:
    '''
    Mock error handler that raises TiferetAPIError.

    :return: A mock callable that raises TiferetAPIError.
    :rtype: Callable
    '''

    # Raise a TiferetAPIError for any incoming error.
    def handler(error, **kwargs):
        raise TiferetAPIError(
            error_code=getattr(error, 'error_code', 'APP_ERROR'),
            name='App Error',
            message=str(error),
        )

    return mock.Mock(side_effect=handler)


# ** fixture: mock_get_route_evt
@pytest.fixture
def mock_get_route_evt() -> DomainEvent:
    '''
    Mock domain event for get_route.

    :return: A mock DomainEvent with an execute method.
    :rtype: DomainEvent
    '''
    evt = mock.Mock(spec=DomainEvent)
    evt.execute = mock.Mock()
    return evt


# ** fixture: mock_get_status_code_evt
@pytest.fixture
def mock_get_status_code_evt() -> DomainEvent:
    '''
    Mock domain event for get_status_code.

    :return: A mock DomainEvent with an execute method.
    :rtype: DomainEvent
    '''
    evt = mock.Mock(spec=DomainEvent)
    evt.execute = mock.Mock()
    return evt


# ** fixture: mock_get_routers_evt
@pytest.fixture
def mock_get_routers_evt() -> DomainEvent:
    '''
    Mock domain event for get_routers.

    :return: A mock DomainEvent with an execute method.
    :rtype: DomainEvent
    '''
    evt = mock.Mock(spec=DomainEvent)
    evt.execute = mock.Mock()
    return evt


# ** fixture: context
@pytest.fixture
def context(
        app_session: AppSession,
        get_dependency: Callable,
        mock_get_route_evt: DomainEvent,
        mock_get_status_code_evt: DomainEvent,
        mock_get_routers_evt: DomainEvent,
        raise_error_handler: Callable,
        response_handler: Callable,
    ) -> OpenApiSessionContext:
    '''
    Create an OpenApiSessionContext for testing.

    :param app_session: The bound AppSession domain object.
    :type app_session: AppSession
    :param get_dependency: The mock DI resolution handler.
    :type get_dependency: Callable
    :param mock_get_route_evt: The mock get_route domain event.
    :type mock_get_route_evt: DomainEvent
    :param mock_get_status_code_evt: The mock get_status_code domain event.
    :type mock_get_status_code_evt: DomainEvent
    :param mock_get_routers_evt: The mock get_routers domain event.
    :type mock_get_routers_evt: DomainEvent
    :param raise_error_handler: The mock error-handling handler.
    :type raise_error_handler: Callable
    :param response_handler: The mock response-building handler.
    :type response_handler: Callable
    :return: The OpenApiSessionContext instance.
    :rtype: OpenApiSessionContext
    '''

    return OpenApiSessionContext.from_domain(
        app_session,
        get_dependency=get_dependency,
        get_route_evt=mock_get_route_evt,
        get_status_code_evt=mock_get_status_code_evt,
        get_routers_evt=mock_get_routers_evt,
        raise_error_handler=raise_error_handler,
        response_handler=response_handler,
    )


# *** tests

# ** test: open_api_session_context_extends_app_session_context
def test_open_api_session_context_extends_app_session_context() -> None:
    '''
    Test that OpenApiSessionContext extends AppSessionContext.
    '''

    assert issubclass(OpenApiSessionContext, AppSessionContext)


# ** test: open_api_session_context_stores_event_collaborators
def test_open_api_session_context_stores_event_collaborators(
        context: OpenApiSessionContext,
        mock_get_route_evt: DomainEvent,
        mock_get_status_code_evt: DomainEvent,
        mock_get_routers_evt: DomainEvent,
    ) -> None:
    '''
    Test that OpenApiSessionContext stores the OpenAPI event collaborators.

    :param context: The OpenApiSessionContext instance.
    :type context: OpenApiSessionContext
    :param mock_get_route_evt: The mock get_route domain event.
    :type mock_get_route_evt: DomainEvent
    :param mock_get_status_code_evt: The mock get_status_code domain event.
    :type mock_get_status_code_evt: DomainEvent
    :param mock_get_routers_evt: The mock get_routers domain event.
    :type mock_get_routers_evt: DomainEvent
    '''

    assert context._get_route_evt is mock_get_route_evt
    assert context._get_status_code_evt is mock_get_status_code_evt
    assert context._get_routers_evt is mock_get_routers_evt


# ** test: handle_error_tiferet_error_status_code
def test_handle_error_tiferet_error_status_code(
        context: OpenApiSessionContext,
        mock_get_status_code_evt: DomainEvent,
    ) -> None:
    '''
    Test that handle_error resolves status code via get_status_code_handler for TiferetError.

    :param context: The OpenApiSessionContext instance.
    :type context: OpenApiSessionContext
    :param mock_get_status_code_evt: The mock get_status_code domain event.
    :type mock_get_status_code_evt: DomainEvent
    '''

    # Configure the mock to return 400 status code.
    mock_get_status_code_evt.execute.return_value = 400

    # Create a TiferetError.
    error = TiferetError('INVALID_INPUT', 'bad input')

    # Assert TiferetAPIError is raised with the correct status code.
    with pytest.raises(TiferetAPIError) as exc_info:
        context.handle_error(error)

    assert exc_info.value.status_code == 400
    mock_get_status_code_evt.execute.assert_called_once_with(error_code='INVALID_INPUT')


# ** test: handle_error_non_tiferet_error_500
def test_handle_error_non_tiferet_error_500(
        context: OpenApiSessionContext,
    ) -> None:
    '''
    Test that handle_error returns 500 for non-Tiferet exceptions.

    :param context: The OpenApiSessionContext instance.
    :type context: OpenApiSessionContext
    '''

    # Create a generic exception.
    error = RuntimeError('unexpected failure')

    # Assert TiferetAPIError is raised with status code 500.
    with pytest.raises(TiferetAPIError) as exc_info:
        context.handle_error(error)

    assert exc_info.value.status_code == 500


# ** test: build_response_returns_tuple
def test_build_response_returns_tuple(
        context: OpenApiSessionContext,
        mock_get_route_evt: DomainEvent,
        response_handler: Callable,
    ) -> None:
    '''
    Test that build_response returns (response, status_code) tuple.

    :param context: The OpenApiSessionContext instance.
    :type context: OpenApiSessionContext
    :param mock_get_route_evt: The mock get_route domain event.
    :type mock_get_route_evt: DomainEvent
    :param response_handler: The mock response-building handler.
    :type response_handler: Callable
    '''

    # Create a mock route with status_code.
    mock_route = mock.Mock()
    mock_route.status_code = 201
    mock_get_route_evt.execute.return_value = mock_route

    # Create a request.
    request = OpenApiRequestContext(feature_id='calc.add')

    # Build the response.
    response, status_code = context.build_response(request)

    # Assert the response and status code.
    assert response == response_handler.return_value
    assert status_code == 201
    response_handler.assert_called_once_with(request)
    mock_get_route_evt.execute.assert_called_once_with(endpoint='calc.add')


# ** test: build_response_unknown_route_defaults_200
def test_build_response_unknown_route_defaults_200(
        context: OpenApiSessionContext,
        mock_get_route_evt: DomainEvent,
    ) -> None:
    '''
    Test that build_response defaults to status code 200 when the route is unknown.

    :param context: The OpenApiSessionContext instance.
    :type context: OpenApiSessionContext
    :param mock_get_route_evt: The mock get_route domain event.
    :type mock_get_route_evt: DomainEvent
    '''

    # Configure the mock to return no route.
    mock_get_route_evt.execute.return_value = None

    # Create a request for an unknown feature.
    request = OpenApiRequestContext(feature_id='unknown.feature')

    # Build the response.
    response, status_code = context.build_response(request)

    # Assert the unknown route defaults to 200.
    assert status_code == 200


# ** test: generate_spec_single_router
def test_generate_spec_single_router(
        context: OpenApiSessionContext,
        mock_get_routers_evt: DomainEvent,
    ) -> None:
    '''
    Test that generate_spec produces a valid OpenAPI 3.0 spec for a single router.

    :param context: The OpenApiSessionContext instance.
    :type context: OpenApiSessionContext
    :param mock_get_routers_evt: The mock get_routers domain event.
    :type mock_get_routers_evt: DomainEvent
    '''

    # Configure mock routers.
    mock_get_routers_evt.execute.return_value = [
        ApiRouter(
            name='calc',
            prefix='/calc',
            routes=[
                ApiRoute(id='add', endpoint='calc.add', path='/add', methods=['POST'], status_code=200),
                ApiRoute(id='subtract', endpoint='calc.subtract', path='/subtract', methods=['POST'], status_code=200),
            ],
        ),
    ]

    # Generate the spec.
    spec = context.generate_spec(title='Calculator API', version='1.0.0', description='A calculator.')

    # Assert the spec structure.
    assert spec['openapi'] == '3.0.3'
    assert spec['info']['title'] == 'Calculator API'
    assert spec['info']['version'] == '1.0.0'
    assert spec['info']['description'] == 'A calculator.'
    assert '/calc/add' in spec['paths']
    assert '/calc/subtract' in spec['paths']
    assert spec['paths']['/calc/add']['post']['operationId'] == 'calc.add'
    assert spec['paths']['/calc/subtract']['post']['operationId'] == 'calc.subtract'
    assert '200' in spec['paths']['/calc/add']['post']['responses']


# ** test: generate_spec_multi_router
def test_generate_spec_multi_router(
        context: OpenApiSessionContext,
        mock_get_routers_evt: DomainEvent,
    ) -> None:
    '''
    Test that generate_spec handles multiple routers.

    :param context: The OpenApiSessionContext instance.
    :type context: OpenApiSessionContext
    :param mock_get_routers_evt: The mock get_routers domain event.
    :type mock_get_routers_evt: DomainEvent
    '''

    # Configure mock routers.
    mock_get_routers_evt.execute.return_value = [
        ApiRouter(
            name='calc',
            prefix='/calc',
            routes=[
                ApiRoute(id='add', endpoint='calc.add', path='/add', methods=['POST'], status_code=200),
            ],
        ),
        ApiRouter(
            name='health',
            prefix='',
            routes=[
                ApiRoute(id='ping', endpoint='health.ping', path='/ping', methods=['GET'], status_code=200),
            ],
        ),
    ]

    # Generate the spec.
    spec = context.generate_spec()

    # Assert paths from both routers.
    assert '/calc/add' in spec['paths']
    assert '/ping' in spec['paths']
    assert spec['paths']['/ping']['get']['operationId'] == 'health.ping'


# ** test: generate_spec_defaults
def test_generate_spec_defaults(
        context: OpenApiSessionContext,
        mock_get_routers_evt: DomainEvent,
    ) -> None:
    '''
    Test that generate_spec uses default parameter values.

    :param context: The OpenApiSessionContext instance.
    :type context: OpenApiSessionContext
    :param mock_get_routers_evt: The mock get_routers domain event.
    :type mock_get_routers_evt: DomainEvent
    '''

    # Configure mock with empty routers.
    mock_get_routers_evt.execute.return_value = []

    # Generate the spec with defaults.
    spec = context.generate_spec()

    # Assert default values.
    assert spec['info']['title'] == 'API'
    assert spec['info']['version'] == '1.0.0'
    assert spec['info']['description'] == ''
    assert spec['paths'] == {}


# ** test: generate_spec_multiple_methods
def test_generate_spec_multiple_methods(
        context: OpenApiSessionContext,
        mock_get_routers_evt: DomainEvent,
    ) -> None:
    '''
    Test that generate_spec maps each HTTP method to a separate operation entry.

    :param context: The OpenApiSessionContext instance.
    :type context: OpenApiSessionContext
    :param mock_get_routers_evt: The mock get_routers domain event.
    :type mock_get_routers_evt: DomainEvent
    '''

    # Configure mock with a route that has multiple methods.
    mock_get_routers_evt.execute.return_value = [
        ApiRouter(
            name='items',
            prefix='/api',
            routes=[
                ApiRoute(id='item', endpoint='items.item', path='/item', methods=['GET', 'POST'], status_code=200),
            ],
        ),
    ]

    # Generate the spec.
    spec = context.generate_spec()

    # Assert both methods are present.
    assert 'get' in spec['paths']['/api/item']
    assert 'post' in spec['paths']['/api/item']
    assert spec['paths']['/api/item']['get']['operationId'] == 'items.item'
    assert spec['paths']['/api/item']['post']['operationId'] == 'items.item'


# ** test: create_docs_handler_returns_none
def test_create_docs_handler_returns_none(context: OpenApiSessionContext) -> None:
    '''
    Test that create_docs_handler returns None by default.

    :param context: The OpenApiSessionContext instance.
    :type context: OpenApiSessionContext
    '''

    # Assert the base create_docs_handler returns None.
    assert context.create_docs_handler() is None
