# AGENTS.md — Tiferet OpenAPI (v0.1.0)

## Project Overview

**Tiferet OpenAPI** is a shared OpenAPI abstraction layer for the Tiferet framework. It provides the common domain objects, service interfaces, domain events, mappers, YAML-backed repository, and context classes that both [tiferet-flask](https://github.com/greatstrength/tiferet-flask) and [tiferet-fast](https://github.com/greatstrength/tiferet-fast) depend on.

- **Repository:** https://github.com/greatstrength/tiferet-openapi
- **Branch:** `main`
- **Python:** ≥ 3.10
- **Version:** `0.1.0`
- **Dependencies:** `tiferet >= 2.0.0b1`

## Architecture

### Package Layout

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

### Key Concepts

- **Domain Objects** (`domain/openapi.py`): `ApiRoute` and `ApiRouter` — read-only Pydantic v2 domain models extending `DomainObject` with `Field` annotations. `ApiRoute` includes an `endpoint` field (format: `router_name.route_id`).
- **Service Interface** (`interfaces/openapi.py`): `OpenApiService` — abstract contract for API configuration access (`get_routers`, `get_route`, `get_status_code`). Returns domain objects.
- **Domain Events** (`events/openapi.py`): `GetRouters`, `GetRoute`, `GetStatusCode` — receive `OpenApiService` via constructor injection. `GetRoute` parses dotted endpoint strings (e.g., `calc.add`). `GetStatusCode` uses `@DomainEvent.parameters_required`.
- **Mappers** (`mappers/openapi.py`): `ApiRouteAggregate`, `ApiRouterAggregate` (mutable, direct Pydantic constructors), `ApiRouteYamlObject`, `ApiRouterYamlObject` (serialization via `_ROLES` ClassVar, `model_validate`, `@classmethod from_model`). `ApiRouterYamlObject.routes` is a `Dict[str, ApiRouteYamlObject]` keyed by route ID; `map()` converts to a list with endpoint derivation.
- **Repository** (`repos/openapi.py`): `OpenApiYamlRepository` — `YamlLoader`-backed implementation of `OpenApiService`. Constructor params: `openapi_yaml_file`, `root_key` (default `'openapi'`), `encoding`. The `root_key` enables compatibility with `flask.yml`, `fast.yml`, and unified `openapi.yml` formats.
- **Contexts** (`contexts/openapi.py`, `contexts/request.py`): `OpenApiContext` — receives `DomainEvent` instances (`get_route_evt`, `get_status_code_evt`), wraps `.execute` internally. `handle_error` raises `TiferetAPIError` with `status_code`. `handle_response` returns `(response, status_code)` tuple. `OpenApiRequestContext` serializes Pydantic `BaseModel` results via `model_dump()`.

### Runtime Flow (within a framework adapter)

1. Framework adapter (e.g., `FlaskAppBuilder`) loads settings and service provider.
2. `OpenApiContext` is instantiated with `DomainEvent` instances for route and status code lookup.
3. On request, `context.run()` parses the request, executes the feature, and returns a response with status code.
4. `handle_error` resolves HTTP status via `get_status_code_handler`, raises `TiferetAPIError` with `status_code`.
5. `handle_response` retrieves the route via `get_route_handler` and returns `(response, route.status_code)`.

## Structured Code Style

All code follows tiferet v2 artifact comment conventions:

- `# ***` — Top-level sections: `imports`, `exports`, `models`, `events`, `contexts`, `interfaces`, `mappers`, `repos`
- `# **` — Mid-level: `core`, `infra`, `app` (for imports); `model: <name>`, `event: <name>`, etc.
- `# *` — Low-level: `attribute: <name>`, `init`, `method: <name>`, `method: <name> (static)`

**Spacing:** One empty line between major sections, after docstrings, and between code snippets within methods.

**Docstrings:** RST format with `:param`, `:type`, `:return`, `:rtype`.

See the [tiferet AGENTS.md](https://github.com/greatstrength/tiferet) for the full style guide.

## Testing

- **Framework:** `pytest`
- **Test location:** Co-located in `<package>/tests/` directories.
- **Run tests:** `pytest tiferet_openapi/ -v`
- **Patterns:**
  - Domain/mapper tests use direct Pydantic constructors and the harness-based `AggregateTestBase` / `TransferObjectTestBase`.
  - Event tests use `DomainEvent.handle()` with mocked `OpenApiService`.
  - Repo tests are integration tests using `tmp_path` with real temporary YAML files.
  - Context tests use `mock.Mock(spec=DomainEvent)` for event dependencies.

## Key Files

- `tiferet_openapi/__init__.py` — Version (`__version__`) and public exports
- `tiferet_openapi/domain/openapi.py` — `ApiRoute`, `ApiRouter` domain objects
- `tiferet_openapi/interfaces/openapi.py` — `OpenApiService` interface
- `tiferet_openapi/events/openapi.py` — `GetRouters`, `GetRoute`, `GetStatusCode` domain events
- `tiferet_openapi/mappers/openapi.py` — Aggregates and TransferObjects
- `tiferet_openapi/repos/openapi.py` — `OpenApiYamlRepository`
- `tiferet_openapi/contexts/openapi.py` — `OpenApiContext`
- `tiferet_openapi/contexts/request.py` — `OpenApiRequestContext`

## YAML Configuration Format

```yaml
openapi:  # root_key — can be 'flask', 'fast', or any custom key
  routers:
    calc:
      prefix: /calc
      routes:
        add:
          path: /add
          methods: [POST]
          status_code: 200
  errors:
    INVALID_INPUT: 400
    DIVISION_BY_ZERO: 422
```

## Public Exports

```python
from tiferet_openapi import (
    # Domain
    ApiRoute, ApiRouter,
    # Interface
    OpenApiService,
    # Events
    GetRouters, GetRoute, GetStatusCode,
    # Mappers
    ApiRouteAggregate, ApiRouterAggregate,
    ApiRouteYamlObject, ApiRouterYamlObject,
    # Repository
    OpenApiYamlRepository,
    # Contexts
    OpenApiContext, OpenApiRequestContext,
)
```
