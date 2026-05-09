'''Tiferet OpenAPI Domain Objects'''

# *** imports

# ** core
from typing import List

# ** infra
from pydantic import Field

# ** app
from tiferet import DomainObject


# *** models

# ** model: api_route
class ApiRoute(DomainObject):
    '''
    A domain object representing an API route configuration.
    '''

    # * attribute: id
    id: str = Field(
        ...,
        description='The unique identifier of the route.',
    )

    # * attribute: endpoint
    endpoint: str = Field(
        ...,
        description='The fully-qualified endpoint (router_name.route_id).',
    )

    # * attribute: path
    path: str = Field(
        ...,
        description='The URL path as string.',
    )

    # * attribute: methods
    methods: List[str] = Field(
        ...,
        description='HTTP methods this route is limited to.',
    )

    # * attribute: status_code
    status_code: int = Field(
        default=200,
        description='The default HTTP status code.',
    )


# ** model: api_router
class ApiRouter(DomainObject):
    '''
    A domain object representing an API router configuration.
    '''

    # * attribute: name
    name: str = Field(
        ...,
        description='The name of the router.',
    )

    # * attribute: prefix
    prefix: str | None = Field(
        default=None,
        description='The URL prefix for all routes.',
    )

    # * attribute: routes
    routes: List[ApiRoute] = Field(
        default_factory=list,
        description='Routes in this router.',
    )