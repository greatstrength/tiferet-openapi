# Tiferet OpenAPI — A Shared OpenAPI Abstraction Layer for the Tiferet Framework

## Introduction

Tiferet OpenAPI provides the shared abstraction layer that both [tiferet-flask](https://github.com/greatstrength/tiferet-flask) and [tiferet-fast](https://github.com/greatstrength/tiferet-fast) depend on for OpenAPI-style API development. It extracts the common domain objects, service interfaces, domain events, mappers, YAML-backed repository, and context classes that were previously duplicated across both framework adapters.

By unifying these components into a single package, tiferet-openapi eliminates code duplication, ensures behavioral consistency between Flask and FastAPI adapters, and provides a clean foundation for building new framework adapters.

## Installation

### From PyPI

```bash
pip install tiferet-openapi
```

### For Development

```bash
git clone https://github.com/greatstrength/tiferet-openapi.git
cd tiferet-openapi
python3.10 -m venv .venv
source .venv/bin/activate
pip install -e ".[test]"
```

## Architecture

Tiferet OpenAPI follows the Tiferet framework's layered Domain-Driven Design architecture:

```
tiferet_openapi/
├── __init__.py          — Version and public exports
├── domain/              — ApiRoute, ApiRouter (DomainObject, Pydantic v2)
├── interfaces/          — OpenApiService (Service ABC)
├── events/              — GetRouters, GetRoute, GetStatusCode (DomainEvent)
├── mappers/             — Aggregates and TransferObjects for YAML round-trip
├── repos/               — OpenApiYamlRepository (YamlLoader-backed OpenApiService)
└── contexts/            — OpenApiContext (AppInterfaceContext), OpenApiRequestContext
```

### Domain Objects

`ApiRoute` and `ApiRouter` are read-only Pydantic v2 domain models that represent API routing configuration:

- **`ApiRoute`** — An individual route with `id`, `endpoint` (format: `router_name.route_id`), `path`, `methods`, and `status_code`.
- **`ApiRouter`** — A named group of routes with an optional URL `prefix`.

### Service Interface

`OpenApiService` is the abstract contract for API configuration access:

- `get_routers()` — Retrieve all configured routers.
- `get_route(route_id, router_name=None)` — Look up a single route.
- `get_status_code(error_code)` — Map an error code to an HTTP status code.

### Domain Events

Three domain events encapsulate the service operations for use in the feature workflow:

- **`GetRouters`** — Retrieves all routers via the injected `OpenApiService`.
- **`GetRoute`** — Parses a dotted endpoint string (e.g., `calc.add`) and retrieves the matching route.
- **`GetStatusCode`** — Looks up the HTTP status code for a given error code.

### Mappers

Aggregates and TransferObjects bridge YAML configuration and runtime domain objects:

- **`ApiRouteAggregate`**, **`ApiRouterAggregate`** — Mutable aggregates with route management methods.
- **`ApiRouteYamlObject`**, **`ApiRouterYamlObject`** — YAML serialization with `_ROLES`-based role control, `map()` for aggregate construction, `from_model()` for reverse mapping.

### Repository

`OpenApiYamlRepository` is the YAML-backed implementation of `OpenApiService`. It accepts a parameterized `root_key` (defaults to `"openapi"`) enabling compatibility with multiple YAML formats:

- `root_key="openapi"` — unified `openapi.yml` format
- `root_key="flask"` — legacy `flask.yml` format
- `root_key="fast"` — legacy `fast.yml` format

### Contexts

- **`OpenApiContext(AppInterfaceContext)`** — Shared API context that receives `DomainEvent` instances for route and status code lookup. Provides `parse_request`, `handle_error` (with HTTP status code resolution), and `handle_response` (returning `(response, status_code)` tuples).
- **`OpenApiRequestContext(RequestContext)`** — Pydantic-aware request context that serializes `BaseModel` results via `model_dump()`, with support for lists, dicts, `None`, and primitives.

## YAML Configuration Format

The repository reads configuration from a YAML file with the following structure:

```yaml
openapi:  # root_key (can be 'flask', 'fast', or any custom key)
  routers:
    calc:
      prefix: /calc
      routes:
        add:
          path: /add
          methods:
            - POST
          status_code: 200
        subtract:
          path: /subtract
          methods:
            - POST
          status_code: 200
    health:
      routes:
        ping:
          path: /ping
          methods:
            - GET
          status_code: 200
  errors:
    INVALID_INPUT: 400
    DIVISION_BY_ZERO: 422
    NOT_FOUND: 404
```

## Usage

Tiferet OpenAPI is consumed by framework-specific adapters. Here's how the shared components integrate:

### In tiferet-flask / tiferet-fast

Framework adapters extend `OpenApiContext` and use `OpenApiYamlRepository` as their configuration backend:

```python
# Framework adapter context (e.g., FlaskApiContext)
from tiferet_openapi import OpenApiContext, OpenApiRequestContext

class FlaskApiContext(OpenApiContext):
    # Inherits parse_request, handle_error, handle_response
    # Adds Flask-specific builder logic
    pass
```

### Direct Repository Usage

```python
from tiferet_openapi import OpenApiYamlRepository

# Load configuration
repo = OpenApiYamlRepository(
    openapi_yaml_file='app/configs/openapi.yml',
    root_key='openapi',
)

# Retrieve all routers
routers = repo.get_routers()
for router in routers:
    print(f"{router.name}: {router.prefix}")
    for route in router.routes:
        print(f"  {route.endpoint} -> {route.path} [{', '.join(route.methods)}]")

# Look up a specific route
route = repo.get_route('add', router_name='calc')
print(f"Route: {route.endpoint}, Status: {route.status_code}")

# Map error code to HTTP status
status = repo.get_status_code('INVALID_INPUT')  # Returns 400
status = repo.get_status_code('UNKNOWN')         # Returns 500 (default)
```

## Testing

Run the test suite:

```bash
pytest tiferet_openapi/ -v
```

Tests are co-located in `<package>/tests/` directories:
- **Domain/mapper tests** use direct Pydantic constructors.
- **Event tests** use `DomainEvent.handle()` with mocked `OpenApiService`.
- **Repo tests** are integration tests using `tmp_path` with real YAML files.
- **Context tests** use `mock.Mock(spec=DomainEvent)` for event dependencies.

## License

MIT — see [LICENSE](LICENSE) for details.
