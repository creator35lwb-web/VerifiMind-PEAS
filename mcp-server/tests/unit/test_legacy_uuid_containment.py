"""Emergency containment for unauthenticated legacy UUID account surfaces.

The public route table, not the old service functions, is the security
boundary. Every legacy identity operation must terminate at one request-blind
503 handler until authenticated subject binding replaces it.
"""

import json
from contextlib import ExitStack
from unittest.mock import patch

import pytest
from starlette.routing import Mount, Route
from starlette.testclient import TestClient

import http_server
from verifimind_mcp.middleware import rate_limiter
from verifimind_mcp.security_containment import (
    LEGACY_UUID_INCIDENT_REFERENCE,
    TRUST_UNAUTHENTICATED_UUID_INPUT,
)
from verifimind_mcp.utils import trinity_history, uuid_tracer


CONTAINED_ROUTES = (
    ("GET", "/whoami"),
    ("POST", "/early-adopters/register"),
    ("GET", "/early-adopters/status/{uuid}"),
    ("GET", "/early-adopters/dashboard/{uuid}"),
    ("POST", "/early-adopters/feedback"),
    ("POST", "/early-adopters/optout/{uuid}"),
    ("GET", "/mcp/test"),
    ("POST", "/register"),
)

OLD_PUBLIC_HANDLERS = {
    http_server.whoami_handler,
    http_server.ea_register_handler,
    http_server.ea_status_handler,
    http_server.ea_dashboard_handler,
    http_server.ea_feedback_handler,
    http_server.ea_optout_handler,
    http_server.mcp_test_handler,
    http_server.register_handler,
}

BACKEND_NAMES = (
    "register_early_adopter",
    "register_user",
    "get_ea_status",
    "read_trinity_history",
    "submit_feedback",
    "process_optout",
    "check_tier",
)

EXPECTED_BODY = {
    "error": "account_service_temporarily_unavailable",
    "message": (
        "Account and UUID-linked operations are temporarily unavailable "
        "during security maintenance. No account data was read or changed."
    ),
    "privacy_request": (
        "For an urgent access, correction, or deletion request, email "
        "alton@ysenseai.org (fallback: creator35lwb@gmail.com) and include "
        "your UUID plus enough private information to verify the request. "
        "Do not post an identifier in a public issue or comment."
    ),
    "retryable": True,
    "incident": LEGACY_UUID_INCIDENT_REFERENCE,
}

CONTAINED_HTTP_REQUESTS = (
    ("GET", "/whoami"),
    ("POST", "/early-adopters/register"),
    ("GET", "/early-adopters/status/01970000-0000-7000-8000-000000000077"),
    ("GET", "/early-adopters/dashboard/01970000-0000-7000-8000-000000000077"),
    ("POST", "/early-adopters/feedback"),
    ("POST", "/early-adopters/optout/01970000-0000-7000-8000-000000000077"),
    ("GET", "/mcp/test"),
    ("POST", "/register"),
)


def _route(path: str, method: str) -> Route:
    matches = [
        route
        for route in http_server.app.routes
        if isinstance(route, Route)
        and route.path == path
        and method in (route.methods or set())
    ]
    assert len(matches) == 1, (path, method, matches)
    return matches[0]


class RequestTrap:
    """Any attempted request inspection makes the containment test fail."""

    def __getattribute__(self, name):
        if name.startswith("__"):
            return object.__getattribute__(self, name)
        raise AssertionError(f"containment handler inspected request.{name}")


@pytest.mark.parametrize("method,path", CONTAINED_ROUTES)
def test_every_legacy_route_is_bound_only_to_containment(method, path):
    endpoint = _route(path, method).endpoint
    assert endpoint is http_server.legacy_identity_maintenance_handler
    assert endpoint not in OLD_PUBLIC_HANDLERS


@pytest.mark.asyncio
@pytest.mark.parametrize("method,path", CONTAINED_ROUTES)
async def test_every_route_returns_one_request_blind_non_reflecting_503(method, path):
    response = await _route(path, method).endpoint(RequestTrap())

    assert response.status_code == 503
    assert response.headers["cache-control"] == "no-store"
    assert response.headers["retry-after"] == "3600"
    assert json.loads(response.body) == EXPECTED_BODY

    rendered = response.body.decode("utf-8")
    for caller_value in (
        "01970000-0000-7000-8000-000000000077",
        "new@example.com",
        "existing@example.com",
        "not-json",
    ):
        assert caller_value not in rendered


@pytest.mark.asyncio
async def test_containment_calls_no_registration_history_tier_or_deletion_backend():
    def forbidden(*_args, **_kwargs):
        raise AssertionError("contained route reached a backend")

    with ExitStack() as stack:
        for name in BACKEND_NAMES:
            stack.enter_context(
                patch.object(http_server, name, side_effect=forbidden)
            )

        # Kept below as an explicit loop rather than a client request: the
        # RequestTrap proves that malformed bodies, headers, path values and
        # query values are never parsed before denial.
        for method, path in CONTAINED_ROUTES:
            response = await _route(path, method).endpoint(RequestTrap())
            assert response.status_code == 503


def test_policy_pages_and_core_mcp_routes_are_not_contained():
    assert _route("/privacy", "GET").endpoint is http_server.privacy_handler
    assert _route("/terms", "GET").endpoint is http_server.terms_handler
    assert _route("/register", "GET").endpoint is http_server.register_page_handler
    assert _route("/optout", "GET").endpoint is http_server.optout_page_handler
    assert _route("/mcp/", "HEAD").endpoint is http_server.mcp_head_handler

    mounts = [
        route for route in http_server.app.routes
        if isinstance(route, Mount) and route.path == "/mcp"
    ]
    assert len(mounts) == 1


def test_privacy_fallback_is_actionable_without_claiming_automated_deletion():
    text = EXPECTED_BODY["privacy_request"].lower()
    assert "access, correction, or deletion" in text
    assert "email" in text
    assert "creator35lwb@gmail.com" in text
    assert "verify" in text
    assert "public issue or comment" in text
    assert "deleted" not in text


def test_shared_uuid_trust_boundary_is_hard_coded_closed():
    assert TRUST_UNAUTHENTICATED_UUID_INPUT is False


def test_full_asgi_stack_never_resolves_or_discloses_uuid_tier():
    supplied_uuids = (
        "01970000-0000-7000-8000-000000000077",
        "01970000-0000-7000-8000-000000000088",
    )
    fresh_store = rate_limiter.RateLimitStore()

    with (
        patch.object(rate_limiter, "_rate_limit_store", fresh_store),
        patch.object(rate_limiter, "_resolve_uuid_tier", return_value="pioneer") as resolver,
        TestClient(http_server.app) as client,
    ):
        for method, path in CONTAINED_HTTP_REQUESTS:
            bodies = []
            for supplied_uuid in supplied_uuids:
                response = client.request(
                    method,
                    path,
                    headers={"X-VerifiMind-UUID": supplied_uuid},
                    content=b"caller-controlled-body",
                )
                assert response.status_code == 503
                assert response.headers["cache-control"] == "no-store"
                assert response.headers["retry-after"] == "3600"
                assert response.headers.get("x-ratelimit-tier") in (None, "anonymous")
                bodies.append(response.json())
            assert bodies == [EXPECTED_BODY, EXPECTED_BODY]

        mcp_response = client.head(
            "/mcp/",
            headers={"X-VerifiMind-UUID": supplied_uuids[0]},
        )
        assert mcp_response.headers["x-ratelimit-tier"] == "anonymous"

    resolver.assert_not_called()
    assert not fresh_store.uuid_requests


def test_valid_uuid_tool_argument_cannot_emit_attributed_log_or_history(capsys):
    supplied_uuid = "01970000-0000-7000-8000-000000000077"
    with patch.object(
        trinity_history,
        "_build_record",
        side_effect=AssertionError("history record constructed during containment"),
    ) as build_record:
        uuid_tracer.emit_tracer(supplied_uuid, "consult_agent_x")
        trinity_history.persist_trinity_result(
            supplied_uuid,
            "consult_agent_x",
            {"innovation_score": 8.0},
        )

    assert capsys.readouterr().out == ""
    build_record.assert_not_called()


def test_rate_limit_denial_is_also_uuid_blind():
    supplied_uuid = "01970000-0000-7000-8000-000000000077"
    fresh_store = rate_limiter.RateLimitStore()

    with (
        patch.object(rate_limiter, "_rate_limit_store", fresh_store),
        patch.object(fresh_store, "check_and_record", return_value=(False, 17, "ip")),
        patch.object(rate_limiter, "_resolve_uuid_tier", return_value="pioneer") as resolver,
        TestClient(http_server.app) as client,
    ):
        response = client.post(
            "/mcp/",
            headers={"X-VerifiMind-UUID": supplied_uuid},
            json={"jsonrpc": "2.0", "method": "initialize", "id": 1},
        )

    assert response.status_code == 429
    assert response.headers["x-ratelimit-tier"] == "anonymous"
    body = response.json()
    assert body["tier"] == "anonymous"
    assert body["uuid_status"] == "disabled"
    assert body["upgrade_hint"] is None
    assert body["from_the_builder"] is None
    assert supplied_uuid not in response.text
    resolver.assert_not_called()
