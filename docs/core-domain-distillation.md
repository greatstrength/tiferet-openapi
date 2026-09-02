**Status:** Draft · **Domain:** `tiferet-openapi` · **Code:** `tiferet_openapi/` · **Branch:** `v1.x-proto`
**Companion:** `docs/domain-vision.md`

# tiferet-openapi: Core Domain Distillation

## 1. Purpose of this document
The vision statement says what tiferet-openapi is for: describing an API's shape once and deriving everything else — the running service, the published specification, the documentation — from that one declaration. This document says how the domain actually does that today: its vocabulary, its bounded steps, which of those steps already deliver on the vision and which do not yet, and the relationships between the pieces. It is the conceptual reference a later RFP, TRD, or freeze decision should be measured against. Where a technical term is unavoidable, it is defined once in Section 3 and used consistently after that.

## 2. The core domain, restated precisely
tiferet-openapi's core domain is **turning a single declared description of an API's routes, request/response shapes, and error mappings into everything a client and an operator need from that API, without a second, hand-maintained copy of the same facts.**

The domain has one fixed shape, restated precisely from the vision's own pipeline:

> **Declare** (routes, shapes, and error mappings as YAML) → **Serve** (validate a request against the declaration and resolve the right status code) → **Generate** (derive an OpenAPI specification from the same declaration) → **Publish** (hand that specification to a client-facing documentation surface)

and three axes of variation:

1. **Framework adapter** — which web framework (Flask, FastAPI, or a future adapter) is actually receiving HTTP requests and rendering documentation. This domain is deliberately indifferent to this axis at Declare and Generate; it is the reason the Serve and Publish steps exist as named extension points rather than concrete framework code.
2. **YAML `root_key`** — which top-level key in the configuration file holds the declaration (`openapi`, `flask`, or `fast`). This axis is resolved once, at Declare, and is invisible to every later step.
3. **Declared-vs-consumed parity** — whether a field a route declares is actually read by the step that would use it. This is not a designed axis the way the first two are; it is where the domain's own history has left a gap between what `ApiRoute` can say and what `generate_spec` currently does with it (Section 5.3, Section 8). Naming it here, rather than treating it as a footnote, is what makes it possible to scope closing that gap as its own piece of work.

## 3. Ubiquitous language
**`ApiRoute`** — a domain object naming one route: `id`, `endpoint`, `path`, `methods`, `status_code`, and the documentation fields `summary`, `description`, `tags`, `request_model`, and `response_model`.

**`ApiRouter`** — a domain object grouping `ApiRoute` entries under a `name` and an optional URL `prefix`.

**Endpoint** — the fully-qualified, dotted identifier of a route, `router_name.route_id`, used everywhere a route must be named unambiguously (event parameters, `operationId` in the generated spec, request feature IDs).

**`OpenApiService`** — the abstract contract (`get_routers`, `get_route`, `get_status_code`) that any configuration backend must satisfy to supply this domain with routers, a single route, and an error-to-status mapping.

**`OpenApiYamlRepository`** — the sole concrete `OpenApiService` today: a YAML-backed reader parameterized by `root_key` (Section 2, axis 2) so the same code reads a unified `openapi.yml`, or the legacy `flask.yml`/`fast.yml` shapes.

**Domain events** — `GetRouters`, `GetRoute` (parses an endpoint into `router_name`/`route_id` and raises `OPENAPI_ROUTE_NOT_FOUND` if the route does not resolve), and `GetStatusCode`. Each wraps one `OpenApiService` method as an injectable, testable unit.

**Aggregate / TransferObject pair** — this domain's mappers come in two per model. `ApiRouteAggregate`/`ApiRouterAggregate` extend the domain object plus Tiferet's `Aggregate` for in-memory mutation (`add_route`, `remove_route`). `ApiRouteYamlObject`/`ApiRouterYamlObject` extend the domain object plus `TransferObject` for YAML round-tripping, using a `_ROLES` dict to control which fields serialize under which role.

**Model path** — a dotted import string (e.g. `app.domain.request.AddRequest`) stored in `ApiRoute.request_model` or `.response_model`, naming a Pydantic model class without importing it at declaration time. It is resolved only when something asks for its schema (Section 4).

**`OpenApiContext`** — the runtime context that wires the three domain events together and implements `parse_request`, `handle_error`, `handle_response`, `generate_spec`, and `create_docs_handler`. It is the one class a framework-specific adapter (outside this repo) is expected to subclass.

**`OpenApiRequestContext`** — a request context that serializes a `BaseModel`, or a list/dict of them, via `model_dump()` before handing a result back to a caller.

**Base request/response/error models** — `ApiRequestModel` and `ApiResponseModel` are empty `DomainObject` subclasses an application extends to declare a route's actual input/output shape; `ApiErrorResponse` is a concrete model with `error` and `message` fields for documenting failure shapes.

**Generated specification** — the OpenAPI 3.0 document `generate_spec` returns: an `info` block plus a `paths` dict keyed by full URL path and HTTP method, each entry an "operation" object.

## 4. What the domain reads / operates on
The declaration is a YAML file with a `root_key`-scoped `routers` mapping (each entry a router name to prefix and routes) and an `errors` mapping (error code to HTTP status code). This is the only input the Declare step needs, and `OpenApiYamlRepository.get_routers` (`tiferet_openapi/repos/openapi.py:56-78`) reads it in full on every call — there is no partial or incremental read.

Two conventions give this input its leverage:

**The endpoint is the one identifier every later step agrees on.** `ApiRouterYamlObject.map` derives it as `{router_name}.{route_id}` (`tiferet_openapi/mappers/openapi.py:193-200`) at YAML-to-aggregate mapping time, and `GetRoute.execute` (`tiferet_openapi/events/openapi.py:89-95`) parses it back apart to look a route up. A route is never addressed by `id` alone once it has left the router that owns it.

**A model path is data until something resolves it.** `ApiRoute.request_model`/`.response_model` are plain strings (`tiferet_openapi/domain/openapi.py:71-81`); nothing in Declare, Serve, or the route's own validation imports or checks them. The only place that ever turns a model path into a real class is `_resolve_model_schema` (proto `tiferet_openapi/contexts/openapi.py:150-172`; see Section 5.3 for why this is proto-only), via `importlib.import_module` plus `getattr`, and it swallows any exception into a bare `None`. A route can declare a `request_model` that has never existed as an importable class, and nothing will say so unless `generate_spec` happens to run.

## 5. The behaviors

### 5.1 Declaring routers and routes
*Turn the YAML file's `root_key`-scoped data into `ApiRouterAggregate`/`ApiRouteAggregate` instances a service can hand out.*

`OpenApiYamlRepository.get_routers` (`tiferet_openapi/repos/openapi.py:56-78`) loads the `routers` mapping and maps each entry through `ApiRouterYamlObject.model_validate(...).map()`. `get_route` (`tiferet_openapi/repos/openapi.py:80-107`) re-uses `get_routers` and then does a linear search filtered by an optional `router_name`. `get_status_code` (`tiferet_openapi/repos/openapi.py:109-129`) reads the separate `errors` mapping and defaults to `500` for an unmapped code.

**Verdict:** agnostic to which `root_key` is configured — the same code path serves `openapi`, `flask`, and `fast` files identically. Variable only in the value of `root_key` itself, which is a constructor parameter, not a code branch.

### 5.2 Serving a request
*Parse an incoming request, resolve the outgoing status code, and format an error, independent of which framework is driving the call.*

`OpenApiContext.parse_request` (`tiferet_openapi/contexts/openapi.py:77-99`) returns an `OpenApiRequestContext`. `handle_error` (`tiferet_openapi/contexts/openapi.py:101-125`) resolves a status code through the injected `GetStatusCode` handler when the exception is a `TiferetError`, defaults to `500` otherwise, and attaches the resolved code to the `TiferetAPIError` the parent class raises. `handle_response` (`tiferet_openapi/contexts/openapi.py:127-147`) looks the route back up by the request's `feature_id` (an endpoint) and pairs the response with that route's `status_code`.

**Verdict:** agnostic to the framework-adapter axis as written — nothing here imports Flask or FastAPI. It is variable in practice only in that a framework-specific subclass (living outside this repo, in `tiferet-flask`/`tiferet-fast`) is expected to extend or call these methods from framework-specific request/response glue; that subclass is a boundary, not a variation this repo's code expresses (Section 9).

### 5.3 Generating a specification
*Derive an OpenAPI 3.0 document from the same declaration Serve already uses.*

On `main`, `generate_spec` (`tiferet_openapi/contexts/openapi.py:149-193` on `main`) walks every router and route and builds one operation per HTTP method, containing only `operationId` and a bare `responses` entry keyed by `status_code`. It does not read `route.summary`, `.description`, `.tags`, `.request_model`, or `.response_model` at all, even though `ApiRoute` has declared all five since v0.1.1/v0.1.2.

On `v1.x-proto` (PR #22), `generate_spec` (proto `tiferet_openapi/contexts/openapi.py:174-258`) is expanded to include `summary`, `description`, and `tags` on the operation when present, and to call the new `_resolve_model_schema` helper (proto `tiferet_openapi/contexts/openapi.py:150-172`) to attach a `requestBody` schema from `request_model` and a response content schema from `response_model`. This proto change has not been reconstructed to `main`.

**Verdict:** this is squarely the declared-vs-consumed-parity axis (Section 2, axis 3). It is not a designed variation — the fields and the method that should read them were never in question at the same time; they landed two releases apart, and only proto has closed the gap. Treat this as an incompleteness to resolve, not a feature to preserve as optional.

### 5.4 Publishing documentation
*Hand the generated specification to something a client can actually open.*

`create_docs_handler` (`tiferet_openapi/contexts/openapi.py:195-208` on `main`; identical content at proto's `contexts/openapi.py:261-273`) is a documented no-op: it accepts arbitrary `**kwargs` and unconditionally returns `None`, with a docstring stating that a framework-specific subclass should override it.

**Verdict:** variable by construction — but today there is no variation to point at, because no subclass exists anywhere in this repo. The vision's fourth pipeline step, Publish, is a named seam with zero concrete behavior behind it (Section 8, Section 9).

## 6. How the behaviors compose
Declare runs once per configuration load; Serve runs once per request; Generate runs on demand (typically once per docs-endpoint hit, not once per request); Publish would run once per Generate call, if anything implemented it. A parallel error path joins Serve independently of the main pipeline: any `TiferetError` raised during a request is resolved to a status code through the same `OpenApiService` the Declare step populated.

```mermaid
flowchart LR
  YAML([root_key-scoped YAML]) --> DECL["5.1 Declare<br/>get_routers / get_route"]
  DECL --> SERVE["5.2 Serve<br/>parse_request / handle_response"]
  DECL --> GEN["5.3 Generate<br/>generate_spec"]
  GEN --> PUB["5.4 Publish<br/>create_docs_handler (no-op)"]
  ERR(["TiferetError"]) --> STATUS["handle_error<br/>get_status_code_handler"]
  DECL --> STATUS
  STATUS --> SERVE
```

Generate depends on Declare's output but not on Serve having run first; a spec can be generated with no requests ever served. Publish depends on Generate producing a document, but as Section 5.4 shows, nothing currently consumes that dependency.

## 7. Relationships / cross-boundary rules
`OpenApiContext` receives its three domain events by constructor injection (`tiferet_openapi/contexts/openapi.py:40-75`) and only ever calls their `execute` methods through the `get_route_handler`/`get_status_code_handler`/`get_routers_handler` aliases — it never talks to an `OpenApiService` directly. `OpenApiYamlRepository` is the only concrete `OpenApiService` in this repo; any relationship between Serve/Generate and a different backing store would have to go through a new implementation of that same contract, not a change to the context.

The Aggregate and TransferObject mappers both inherit directly from the domain object (`ApiRouteAggregate(ApiRoute, Aggregate)`, `ApiRouteYamlObject(ApiRoute, TransferObject)`) rather than wrapping it — a route's fields are declared exactly once, in `domain/openapi.py`, and both mapper families pick them up through Python's own inheritance rather than a second, parallel field list.

Judging whether a `request_model`/`response_model` declaration is *correct* is not something Declare, or the domain object itself, can do — Section 4 already noted the path is inert until `_resolve_model_schema` runs. That makes correctness a property of a specific later call (Generate), not of the declaration in isolation, which is the same shape of problem Section 5.3's entanglement describes from a different angle.

## 8. The agnostic core and the variable edge
**Agnostic — built once, shared regardless of framework or configuration:**
- The YAML-repository pattern itself: one `root_key`-parameterized reader serves every configuration shape this domain currently supports.
- The `ApiRoute`/`ApiRouter` field shape and the endpoint-derivation convention.
- The Aggregate/TransferObject mapping mechanism and its `_ROLES`-based role control.
- The three domain events, as a wrapping mechanism over `OpenApiService`.
- `OpenApiRequestContext`'s `BaseModel`-aware result serialization.

**Variable — one definition per consuming application:**
- The `root_key` value chosen for a given deployment's configuration file.
- Which framework subclasses `OpenApiContext` and implements `parse_request`/`handle_error`/`handle_response` glue and `create_docs_handler`.
- The actual `ApiRequestModel`/`ApiResponseModel` subclasses an application defines, and the dotted paths that name them.
- The error-code-to-status-code data itself.

**Currently entangled — the honest inventory:**
- **`ApiRoute`'s documentation fields and `generate_spec` disagree about what exists, on `main`.** `summary`, `description`, `tags`, `request_model`, and `response_model` (`tiferet_openapi/domain/openapi.py:53-81`) have been declarable since v0.1.1/v0.1.2; `generate_spec` on `main` (`tiferet_openapi/contexts/openapi.py:149-193` on `main`) ignores all five. `v1.x-proto` PR #22 closes this specific gap (Section 5.3) but has not been reconstructed to trunk, and shipped without an RFP behind it — an out-of-process precedent this distillation surfaces rather than quietly inherits.
- **Publish is a name, not a behavior.** `create_docs_handler` (`tiferet_openapi/contexts/openapi.py:195-208` on `main`) returns `None` unconditionally on both branches. The vision commits to "a documentation page a client can open"; no code in this repo, on either branch, produces one.
- **`_resolve_model_schema` fails silently.** An unresolvable `request_model`/`response_model` path (proto `tiferet_openapi/contexts/openapi.py:161-172`) is caught and turned into `None`, which `generate_spec` then treats as "nothing to add" rather than "something is wrong." This directly contradicts the vision's claim that documentation "can't quietly go stale" — a broken model reference degrades silently instead of surfacing.
- **A separate mapper defect travels with the same PR.** `mappers/openapi.py:97` on `main` excludes `'tags'` from the YAML `to_data` role, so a router's tags do not round-trip through a YAML write on trunk today; proto's `mappers/openapi.py:97` removes that exclusion. This is bundled with the `generate_spec` fix in PR #22 but is a distinct correctness issue, not a documentation-completeness one.

## 9. Boundaries
**Inside the domain:** declaring routers, routes, and error mappings from a YAML file under a configurable `root_key`; resolving a route by its endpoint; resolving an error code to a status code; generating an OpenAPI 3.0 specification from the declared routers; the base request/response/error Pydantic models an application extends.

**Outside the domain, and who owns it instead:**
- Running an HTTP server and routing an actual incoming request to a handler — owned by the framework adapter (`tiferet-flask`, `tiferet-fast`, or a future one), not this repo.
- Rendering or serving the generated specification as a browsable documentation page — `create_docs_handler` is the named seam; the implementation is the adapter's, once one exists (Section 5.4, Section 8).
- What a route's business logic does once a request reaches it — owned by the feature or workflow the route triggers, not by the route's declaration.
- Validating that request data makes business sense beyond matching its declared shape — owned by the domain logic the route calls into, not by this layer's request/response models.

## 10. Where this leads
1. **Reconstruct the `generate_spec`/`_resolve_model_schema` wiring and the `mappers/openapi.py:97` tags round-trip fix onto trunk**, via a proper RFP rather than the direct proto commit (PR #22) that introduced them — the declared-vs-consumed-parity gap in Section 5.3/Section 8 is the clearest, most concrete v1 candidate this distillation found.
2. **Decide whether `create_docs_handler` gets an implementation, or stays an explicitly out-of-scope seam, for v1.** Right now the vision promises a documentation page and the code offers only a hook; a v1 that ships without resolving this should say so on purpose, not by omission.
3. **Decide whether `_resolve_model_schema` should surface a resolution failure instead of silently returning `None`,** since the current behavior is in direct tension with the vision's core promise that documentation cannot quietly drift from the truth.
4. **This is the actual v1 freeze-point question:** does a v1 catalog include the doc-field wiring and a working docs handler, or is that deferred to a v2 line while v1 freezes the narrower Declare/Serve/Generate-without-doc-fields shape that already exists on trunk today? Everything else in this document is groundwork for answering that one question.
