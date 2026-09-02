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
from ..openapi import build_openapi_session_context, create_openapi_request_context
from ...contexts.openapi import OpenApiSessionContext
from ...contexts.request import OpenApiRequestContext


# *** fixtures

# ** fixture: cache
@pytest.fixture
def cache() -> CacheContext:
    '''
    A bootstrap cache pre-seeded with all framework defaults.

    :return: The pre-seeded cache context.
    :rtype: CacheContext
    '''
    return core.build_cache()


# ** fixture: app_session
@pytest.fixture
def app_session() -> AppSession:
    '''
    A sample AppSession domain object for testing.

    :return: A sample app session.
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
    Test that build_openapi_session_context successfully constructs an
    OpenApiSessionContext given a resolved app_session and cache.

    :param app_session: The resolved app session definition.
    :type app_session: AppSession
    :param cache: The pre-built shared cache context.
    :type cache: CacheContext
    '''

    # Build the OpenAPI session context with mock event collaborators.
    context = build_openapi_session_context(
        app_session,
        cache,
        get_route_evt=mock.Mock(),
        get_status_code_evt=mock.Mock(),
        get_routers_evt=mock.Mock(),
    )

    # Assert the constructed context is fully wired and bound to the app session.
    assert isinstance(context, OpenApiSessionContext)
    assert context.domain is app_session
    assert context._create_request is core.create_request_context
    assert context._build_response is core.response_handler


# ** test: build_openapi_session_context_accepts_custom_request_handler
def test_build_openapi_session_context_accepts_custom_request_handler(
        app_session: AppSession,
        cache: CacheContext,
    ) -> None:
    '''
    Test that build_openapi_session_context wires a caller-supplied
    create_request_handler instead of the default.

    :param app_session: The resolved app session definition.
    :type app_session: AppSession
    :param cache: The pre-built shared cache context.
    :type cache: CacheContext
    '''

    # Build the context with the OpenAPI request-context factory.
    context = build_openapi_session_context(
        app_session,
        cache,
        get_route_evt=mock.Mock(),
        get_status_code_evt=mock.Mock(),
        get_routers_evt=mock.Mock(),
        create_request_handler=create_openapi_request_context,
    )

    # Assert the custom handler is wired.
    assert context._create_request is create_openapi_request_context


# ** test: create_openapi_request_context_returns_openapi_request_context
def test_create_openapi_request_context_returns_openapi_request_context() -> None:
    '''
    Test that create_openapi_request_context builds an OpenApiRequestContext
    stamped with the interface id.
    '''

    # Build the request context.
    request = create_openapi_request_context(
        'test_api',
        'calc.add',
        headers={'content-type': 'application/json'},
        data={'a': 1, 'b': 2},
    )

    # Assert the result is an OpenApiRequestContext with the expected fields.
    assert isinstance(request, OpenApiRequestContext)
    assert request.feature_id == 'calc.add'
    assert request.data == {'a': 1, 'b': 2}
    assert request.headers.get('interface_id') == 'test_api'
