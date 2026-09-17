'''Tiferet OpenAPI Blueprint Tests'''

# *** imports

# ** core
from unittest import mock

# ** infra
import pytest
from tiferet.blueprints import core
from tiferet.contexts.cache import CacheContext
from tiferet.domain import AppSession

# ** app
from ..openapi import (
    build_openapi_session_context,
    create_openapi_request_context,
    get_route_handler,
)
from ...contexts.openapi import OpenApiSessionContext
from ...contexts.request import OpenApiRequestContext

# *** fixtures

# ** fixture: cache
@pytest.fixture
def cache() -> CacheContext:
    '''
    Bootstrap cache pre-seeded with all framework defaults.

    :return: A CacheContext seeded by core.build_cache.
    :rtype: CacheContext
    '''

    return core.build_cache()

# ** fixture: app_session
@pytest.fixture
def app_session() -> AppSession:
    '''
    AppSession bound to the OpenAPI session context under test.

    :return: An AppSession domain object.
    :rtype: AppSession
    '''

    return AppSession(id='test_api', name='Test API')

# *** tests

# ** test: build_openapi_session_context_constructs_context
def test_build_openapi_session_context_constructs_context(
        app_session: AppSession,
        cache: CacheContext,
    ) -> None:
    '''
    Test that build_openapi_session_context constructs a wired OpenApiSessionContext.

    :param app_session: The AppSession domain object.
    :type app_session: AppSession
    :param cache: The bootstrap cache.
    :type cache: CacheContext
    '''

    # Build the session context from cache and session only.
    context = build_openapi_session_context(app_session, cache)

    # Assert the constructed context, bound session, and default handlers.
    assert isinstance(context, OpenApiSessionContext)
    assert context.domain is app_session
    assert context._create_request is core.create_request_context
    assert context._build_response is core.response_handler
    assert callable(context._get_route)
    assert callable(context._get_status_code)
    assert callable(context._get_routers)

# ** test: build_openapi_session_context_accepts_custom_request_handler
def test_build_openapi_session_context_accepts_custom_request_handler(
        app_session: AppSession,
        cache: CacheContext,
    ) -> None:
    '''
    Test that build_openapi_session_context accepts a custom request handler.

    :param app_session: The AppSession domain object.
    :type app_session: AppSession
    :param cache: The bootstrap cache.
    :type cache: CacheContext
    '''

    # Build the session context with the OpenAPI request-context factory.
    context = build_openapi_session_context(
        app_session,
        cache,
        create_request_handler=create_openapi_request_context,
    )

    # Assert the custom request handler is wired.
    assert context._create_request is create_openapi_request_context

# ** test: get_route_handler_resolves_event_via_get_dependency
def test_get_route_handler_resolves_event_via_get_dependency() -> None:
    '''
    Test that get_route_handler resolves the event through get_dependency.
    '''

    # Stub the DI resolver to return a mock get-route event.
    get_route_evt = mock.Mock()
    get_route_evt.execute = mock.Mock(return_value='route')
    get_dependency = mock.Mock(return_value=get_route_evt)

    # Invoke the handler closure.
    result = get_route_handler(get_dependency)(endpoint='calc.add')

    # Assert DI resolution and event execution.
    get_dependency.assert_called_once_with('get_route_evt', 'app')
    get_route_evt.execute.assert_called_once_with(endpoint='calc.add')
    assert result == 'route'

# ** test: create_openapi_request_context_returns_openapi_request_context
def test_create_openapi_request_context_returns_openapi_request_context() -> None:
    '''
    Test that create_openapi_request_context returns an OpenApiRequestContext.
    '''

    # Create an OpenAPI request context.
    request = create_openapi_request_context(
        'test_api',
        'calc.add',
        headers={'content-type': 'application/json'},
        data={'a': 1, 'b': 2},
    )

    # Assert the request type, feature, data, and stamped interface id.
    assert isinstance(request, OpenApiRequestContext)
    assert request.feature_id == 'calc.add'
    assert request.data == {'a': 1, 'b': 2}
    assert request.headers.get('interface_id') == 'test_api'
