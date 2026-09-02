**Status:** Draft · **Domain:** `tiferet-openapi` · **Code:** `tiferet_openapi/` · **Branch:** `docs-domain-vision`

# tiferet-openapi: Domain Vision Statement

## The bet: describe an API once, not once per framework
Most teams building a web API end up documenting it twice: once as working route
code in whichever framework they picked, and again as a separate specification
file a different person maintains — usually badly, because it drifts the moment
the code changes and nobody notices until a client breaks. Support more than one
framework — a Flask service here, a FastAPI service there — and that second
problem doubles: the same route, described twice, drifting twice, in two
different dialects.

tiferet-openapi's bet is that a route's shape — its path, the methods it
answers to, what goes in, what comes back, what it's called in the published
documentation, and what a client sees when it fails — is one fact, not two.
Declared once, in one place, it should drive both the running service and the
documentation a client reads about it. Which framework happens to be running
underneath should be a detail an operator picks, not a second copy of the
truth someone has to keep in sync by hand.

## What this domain makes real
tiferet-openapi is the shared layer that lets a Tiferet-based API declare its
routes, its inputs and outputs, and its error-to-status-code mapping once, in
a plain configuration file, and get back everything a published API needs
from that single declaration: a working router any framework adapter can
run, request and response shapes a client can validate against, a generated
industry-standard specification (OpenAPI) describing all of it, and a
documentation page a client can open and read — without a person writing any
of those by hand or keeping them in sync after the fact.

## What we get for it
**One source of truth, many framework adapters.** [tiferet-flask](https://github.com/greatstrength/tiferet-flask) and [tiferet-fast](https://github.com/greatstrength/tiferet-fast) already share this layer instead of each maintaining its own copy of route and error-handling logic. Every adapter added after them inherits the same declared routes, the same generated documentation, and the same error behavior for free — the cost of a third or fourth framework adapter drops to "wire it up," not "rebuild the documentation layer again."

**Documentation that can't quietly go stale.** Because the published specification is generated from the same declaration that drives the running service, a route that changes in the declaration changes in the documentation automatically. There is no second file to remember to update, and no way for the two to disagree.

**Errors are documented, not just handled.** A client integrating against the API needs to know not just that a request can fail, but what failure looks like and what status code to expect. Mapping error conditions to HTTP status codes and documenting error response shapes are part of the same declaration as the routes themselves, so failure modes show up in the published documentation instead of being discovered by a client in production.

**Adding or changing a route is an edit to data, not a code review of routing logic.** A route's path, methods, inputs, outputs, and documentation text live in a declaration a non-framework-expert can read and change. Nobody needs to trace through routing code to answer "what does this endpoint accept," and nobody needs framework-specific knowledge to add a new one.

**A published contract a client can act on without reading source code.** The generated specification is the kind of document API tooling already knows how to consume — for generating client code, for automated contract testing, for a browsable reference page. tiferet-openapi's job is to make that document correct and current by construction, not to invent a new format someone has to learn.

## The core of the work
Every API surfaced through tiferet-openapi goes through the same journey:

> **Declare** routes, request/response shapes, and error mappings as
> configuration → **serve** requests against that declaration, validating
> shape and resolving the right status code → **generate** an OpenAPI
> specification straight from the same declaration → **publish** that
> specification as a documentation page a client can open.

The design commitment underneath all four steps: the specification is
*derived*, never hand-maintained. Nothing about the published documentation
is allowed to be a fact that exists only in the documentation — every line of
it traces back to the same declaration the running service already obeys.
That is what makes the fourth step, publishing, safe to treat as a detail
instead of a second job.

## What it deliberately does not do
tiferet-openapi does not run a web server or own the wire-level details of
receiving an HTTP request — that belongs to whichever framework (Flask,
FastAPI, or a future adapter) is doing the actual serving. It describes and
validates the shape of what crosses that wire; it does not replace the
server carrying it.

It does not decide what a route's business logic does. Declaring a route
here says what it looks like from the outside, not what happens once a
request reaches it — that belongs to the feature or workflow the route
triggers.

It does not build its own documentation viewer. It produces the
specification a viewer reads; which viewer a given framework adapter chooses
to serve it through is that adapter's decision, not this domain's.

It does not validate business rules. Confirming that a request has the
right shape is in scope; confirming that the values inside it make sense for
the business is not — that judgment belongs to the domain logic the route
calls into.

---

*Companion document:* `docs/core-domain-distillation.md` — the detailed
walkthrough of the domain's vocabulary, behaviors, and the relationships
between its parts.
