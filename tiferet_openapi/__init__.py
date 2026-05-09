# *** exports

# ** app
# Export the main domain objects, interfaces, events, mappers, repos, and contexts.
# Use a try-except block to avoid import errors on build systems.
try:
    from .domain import ApiRoute, ApiRouter
    from .interfaces import OpenApiService
    from .events import GetRouters, GetRoute, GetStatusCode
    from .mappers import (
        ApiRouteAggregate,
        ApiRouterAggregate,
        ApiRouteYamlObject,
        ApiRouterYamlObject,
    )
    from .repos import OpenApiYamlRepository
    from .contexts import OpenApiContext, OpenApiRequestContext
except Exception as e:
    import os, sys
    # Only print warning if TIFERET_SILENT_IMPORTS is not set to a truthy value
    if not os.getenv('TIFERET_SILENT_IMPORTS'):
        print(f"Warning: Failed to import Tiferet OpenAPI modules: {e}", file=sys.stderr)
    pass

# *** version
__version__ = "0.1.0"
