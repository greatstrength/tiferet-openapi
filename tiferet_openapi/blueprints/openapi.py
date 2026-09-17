'''Tiferet OpenAPI Blueprints'''

# *** imports

# ** core
from typing import Any, Callable, Dict

# ** infra
from tiferet.blueprints import core
from tiferet.contexts.app import AppSession
from tiferet.contexts.cache import CacheContext
from tiferet.events import DomainEvent

# ** app
from ..contexts.openapi import OpenApiSessionContext
from ..contexts.request import OpenApiRequestContext

# *** functions

# ** function: create_openapi_request_context
def create_openapi_request_context(interface_id: str,
        feature_id: str,
        headers: Dict[str, str] = None,
        data: Dict[str, Any] = None) -> OpenApiRequestContext:
    '''
    Compose an OpenAPI request context for a feature execution.

    Mirrors ``core.create_request_context`` but constructs an
    ``OpenApiRequestContext`` so ``handle_response`` serializes Pydantic
    ``BaseModel`` results before ``build_response`` runs.

    :param interface_id: The interface id stamped onto the request headers.
    :type interface_id: str
    :param feature_id: The feature id seeded on the request context.
    :type feature_id: str
    :param headers: The request headers merged with the interface id.
    :type headers: Dict[str, str]
    :param data: The request data payload.
    :type data: Dict[str, Any]
    :return: The composed OpenAPI request context.
    :rtype: OpenApiRequestContext
    '''

    # Compose and return the OpenAPI request context, stamping the interface id onto the headers.
    return OpenApiRequestContext(
        headers={**(headers or {}), 'interface_id': interface_id},
        data=data,
        feature_id=feature_id,
    )

# *** blueprints

# ** blueprint: get_route_handler
def get_route_handler(get_route_evt: DomainEvent) -> Callable:
    '''
    Build a route-lookup closure from the resolved get-route event.

    :param get_route_evt: The domain event for retrieving a route.
    :type get_route_evt: DomainEvent
    :return: A callable that retrieves a route by endpoint.
    :rtype: Callable
    '''

    # Build the handler closure with the event captured.
    def handler(**kwargs) -> Any:

        # Delegate to the captured event.
        return get_route_evt.execute(**kwargs)

    # Return the closure.
    return handler

# ** blueprint: get_status_code_handler
def get_status_code_handler(get_status_code_evt: DomainEvent) -> Callable:
    '''
    Build a status-code-lookup closure from the resolved get-status-code event.

    :param get_status_code_evt: The domain event for retrieving a status code.
    :type get_status_code_evt: DomainEvent
    :return: A callable that retrieves an HTTP status code by error code.
    :rtype: Callable
    '''

    # Build the handler closure with the event captured.
    def handler(**kwargs) -> Any:

        # Delegate to the captured event.
        return get_status_code_evt.execute(**kwargs)

    # Return the closure.
    return handler

# ** blueprint: get_routers_handler
def get_routers_handler(get_routers_evt: DomainEvent) -> Callable:
    '''
    Build a routers-lookup closure from the resolved get-routers event.

    :param get_routers_evt: The domain event for retrieving all routers.
    :type get_routers_evt: DomainEvent
    :return: A callable that retrieves the configured routers.
    :rtype: Callable
    '''

    # Build the handler closure with the event captured.
    def handler(**kwargs) -> Any:

        # Delegate to the captured event.
        return get_routers_evt.execute(**kwargs)

    # Return the closure.
    return handler

# ** blueprint: build_openapi_session_context
def build_openapi_session_context(app_session: AppSession,
        cache: CacheContext,
        get_route_evt: DomainEvent,
        get_status_code_evt: DomainEvent,
        get_routers_evt: DomainEvent,
        create_request_handler: Callable = None,
        **extra_kwargs) -> OpenApiSessionContext:
    '''
    Build a fully wired OpenAPI session context from a resolved app session.

    This is a composition helper, not a full ``build_app``-shaped blueprint:
    ``tiferet-openapi`` is a library that ``tiferet-flask`` / ``tiferet-fast``
    extend further with their own request/response glue. The caller supplies
    the cache and app session; this helper wraps the OpenAPI events as
    handler callables and wires the app service container and resolver.

    :param app_session: The resolved app session definition.
    :type app_session: AppSession
    :param cache: The pre-built shared cache context.
    :type cache: CacheContext
    :param get_route_evt: The domain event for retrieving a route.
    :type get_route_evt: DomainEvent
    :param get_status_code_evt: The domain event for retrieving a status code.
    :type get_status_code_evt: DomainEvent
    :param get_routers_evt: The domain event for retrieving all routers.
    :type get_routers_evt: DomainEvent
    :param create_request_handler: Optional request-construction handler;
        defaults to ``core.create_request_context`` when omitted.
    :type create_request_handler: Callable
    :param extra_kwargs: Additional keyword arguments forwarded to the
        context constructor.
    :type extra_kwargs: dict
    :return: The wired OpenAPI session context.
    :rtype: OpenApiSessionContext
    '''

    # Build the app service container and compose the feature-level resolver.
    app_container = core.build_app_service_container(cache, app_session)
    resolver = core.build_service_resolver(app_container)

    # Delegate handler wiring, collaborator resolution, and construction.
    return core.compose_session_context(
        OpenApiSessionContext,
        app_session,
        cache,
        app_container,
        resolver,
        create_request_handler=create_request_handler or core.create_request_context,
        response_handler=core.response_handler,
        get_route_handler=get_route_handler(get_route_evt),
        get_status_code_handler=get_status_code_handler(get_status_code_evt),
        get_routers_handler=get_routers_handler(get_routers_evt),
        **extra_kwargs,
    )
