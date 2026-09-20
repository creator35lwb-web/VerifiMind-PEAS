"""Test-only ASGI harness that reaches the DORMANT public handlers directly.

**Provenance, and the limit of what this proves.**

Legacy-UUID containment re-points the public route table: `/whoami`, `/register`,
`/early-adopters/{register,status,dashboard,feedback,optout}` and `/mcp/test` are all bound to
`legacy_identity_maintenance_handler`, which answers a request-blind `503` and reads nothing.
The original handlers were **not deleted** — they are dormant behind those routes.

Evidence from this harness is therefore about **handler and service-primitive behaviour**, never
about what the public endpoint currently does. A pass here is **not** a claim that any of these
surfaces is publicly reachable. The current-route truth is pinned separately and must stay that
way (T S176, plane-1/plane-2 split):

  * `tests/unit/test_legacy_uuid_containment.py` — the eight contained pairs, gate-dark
  * `tests/unit/test_containment_gate_activation.py` — the same pairs across gate activation

Why an ASGI harness rather than calling the handler as a function: several displaced tests assert
the **wire** answer, and part of that answer is produced by Starlette's exception mapping, not by
the handler. `register_handler` re-raises `EnvironmentMisconfigured`; the `503`
`service_misconfigured` body those tests assert is rendered by `environment_misconfigured_handler`
registered on the app. A bare call would raise instead of returning that response, so the harness
**reproduces the production exception mapping** while deliberately omitting production middleware.

Deliberately **not** included, so this app cannot be mistaken for the real one:
  * the auth boundary, rate limiter and IP blocklist middleware
  * every route that is not one of the dormant handlers under test
  * the MCP mount and its lifespan
"""
from starlette.applications import Starlette
from starlette.routing import Route
from starlette.testclient import TestClient

import http_server

try:  # pragma: no cover - present on every tree at or after the round-3 repair
    from verifimind_mcp.oauth.config import EnvironmentMisconfigured
except ImportError:  # an older tree replayed as a known-bad control
    EnvironmentMisconfigured = None

# The dormant handlers, at the paths and verbs they served before containment.
DORMANT_ROUTES = (
    ("/whoami", http_server.whoami_handler, ["GET"]),
    ("/register", http_server.register_handler, ["POST"]),
    ("/early-adopters/register", http_server.ea_register_handler, ["POST"]),
    ("/early-adopters/status/{uuid}", http_server.ea_status_handler, ["GET"]),
    ("/early-adopters/dashboard/{uuid}", http_server.ea_dashboard_handler, ["GET"]),
    ("/early-adopters/feedback", http_server.ea_feedback_handler, ["POST"]),
    ("/early-adopters/optout/{uuid}", http_server.ea_optout_handler, ["POST"]),
)


def build_dormant_app() -> Starlette:
    """A minimal app carrying only the dormant handlers and production's exception mapping."""
    app = Starlette(
        routes=[Route(path, handler, methods=methods) for path, handler, methods in DORMANT_ROUTES],
        exception_handlers={
            # Identical to the production mapping for the exceptions these handlers raise.
            404: http_server.http_exception_handler,
            400: http_server.http_exception_handler,
            405: http_server.http_exception_handler,
            406: http_server.http_exception_handler,
        },
    )
    # Registered only when the tree under test HAS this mapping. On the composed tree it always
    # does, so production fidelity is unchanged; on an older tree replayed as a known-bad control
    # the mapping simply does not exist yet, and the displaced case must still discriminate on
    # BEHAVIOUR rather than erroring on a symbol the old tree never defined.
    _env_handler = getattr(http_server, "environment_misconfigured_handler", None)
    if EnvironmentMisconfigured is not None and _env_handler is not None:
        app.add_exception_handler(EnvironmentMisconfigured, _env_handler)
    app.router.redirect_slashes = False
    return app


def dormant_client(*, raise_server_exceptions: bool = True) -> TestClient:
    """A TestClient over the dormant-handler app. Isolated from `http_server.app`.

    `raise_server_exceptions=False` renders an unhandled server exception as the HTTP 500
    production would send, so a STATUS assertion fails rather than the exception propagating
    into the test. Callers that relied on that in the production client must keep it here.
    """
    return TestClient(build_dormant_app(), raise_server_exceptions=raise_server_exceptions)


def assert_harness_is_not_the_production_app():
    """Guard: if this harness ever routes through the contained production table, every test
    using it would be measuring containment instead of the handler, and would still look green."""
    app = build_dormant_app()
    paths = {route.path for route in app.routes}
    assert paths == {path for path, _handler, _methods in DORMANT_ROUTES}, paths
    handlers = {route.endpoint for route in app.routes}
    # Resolved defensively, NOT as a direct attribute. This guard must keep its full strength on
    # any tree that HAS containment, while still being runnable against a PRE-containment tree —
    # that is how the displaced cases are replayed against their known-bad old heads. A direct
    # `http_server.legacy_identity_maintenance_handler` raises AttributeError there, so every
    # old-head control would error on a MISSING SYMBOL instead of discriminating on behaviour,
    # and a vacuous control is indistinguishable from a passing one.
    contained = getattr(http_server, "legacy_identity_maintenance_handler", None)
    assert contained is None or contained not in handlers, (
        "the dormant harness must not bind the containment handler"
    )
