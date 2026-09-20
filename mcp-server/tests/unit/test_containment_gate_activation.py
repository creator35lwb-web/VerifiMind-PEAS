"""Containment stays request-blind when the registration gate is activated.

The previous gate-on behaviour challenged anonymous GET /mcp/test and looked up
well-formed bearers before returning maintenance 503. Those tests recorded a
residual, not an endorsed contract. The bounded repair now makes all eight
maintenance-contained pairs answer 503 regardless of bearer or boundary mode.
The exact exemption must remain bound to the maintenance route; both directions
of that relationship are tested below so lifting containment cannot silently
leave a live route unauthenticated. Gate-on cases run in subprocesses to avoid
leaking re-imported http_server state into later tests.
"""
import json
import os
import subprocess
import sys
import textwrap

import pytest

CONTAINMENT_ERROR = "account_service_temporarily_unavailable"
UUID = "01970000-0000-7000-8000-000000000077"

CONTAINED_PAIRS = (
    ("GET", "/whoami"),
    ("POST", "/early-adopters/register"),
    ("GET", f"/early-adopters/status/{UUID}"),
    ("GET", f"/early-adopters/dashboard/{UUID}"),
    ("POST", "/early-adopters/feedback"),
    ("POST", f"/early-adopters/optout/{UUID}"),
    ("GET", "/mcp/test"),
    ("POST", "/register"),
)

# Well-formed by GRAMMAR only (`<kind-prefix>.<token-id>.<secret>`): never minted, never stored.
WELL_FORMED_ACCESS = "vmat.unknown-token-id.not-a-real-secret-value"
WELL_FORMED_PAT = "vmpat.unknown-token-id.not-a-real-secret-value"
WELL_FORMED_REFRESH = "vmrt.unknown-token-id.not-a-real-secret-value"

_DRIVER = textwrap.dedent(
    """
    import json, os, sys
    sys.path.insert(0, os.path.join(os.getcwd(), "src"))
    sys.path.insert(0, os.getcwd())
    from starlette.testclient import TestClient

    spec = json.loads(sys.argv[1])
    os.environ["REGISTRATION_GATE_ENABLED"] = "true" if spec["gate"] else "false"
    os.environ["AUTH_BOUNDARY_MODE"] = spec["mode"]

    calls = []
    if spec["record_io"]:
        from verifimind_mcp import registration, registration_lookup
        from verifimind_mcp.middleware import rate_limiter
        from verifimind_mcp.oauth import stores

        def record(label, original):
            def wrapper(*a, **k):
                calls.append(label)
                return original(*a, **k)
            return wrapper

        if spec.get("store_down"):
            # Deterministic outage: never depends on ambient credentials or the network.
            registration._get_firestore = record("registration._get_firestore", lambda *a, **k: None)
        else:
            registration._get_firestore = record("registration._get_firestore", registration._get_firestore)
        # The OAuth credential store. Without these three, a "no backend I/O" assertion cannot
        # see the lookup a well-formed bearer performs.
        stores._cache_get = record("stores._cache_get", stores._cache_get)
        stores._db = record("stores._db", stores._db)
        stores._read = record("stores._read", stores._read)
        registration_lookup.resolve_registration = record(
            "registration_lookup.resolve_registration", registration_lookup.resolve_registration)
        rate_limiter._resolve_uuid_tier = record(
            "rate_limiter._resolve_uuid_tier", rate_limiter._resolve_uuid_tier)

    import http_server

    out = []
    with TestClient(http_server.app) as client:
        for case in spec["requests"]:
            calls.clear()
            response = client.request(
                case["method"], case["path"],
                headers=case.get("headers") or {},
                **({"content": case["raw_body"].encode()} if case.get("raw_body") is not None
                   else {"json": {}} if case["method"] == "POST" else {}),
            )
            presented = (case.get("headers") or {}).get("Authorization", "")
            presented = presented.split(" ", 1)[1] if " " in presented else ""
            out.append({
                "method": case["method"], "path": case["path"],
                "status": response.status_code,
                "reflects_bearer": bool(presented) and presented in response.text,
                "contained": CONTAINMENT_ERROR in response.text,
                "www_authenticate": bool(response.headers.get("www-authenticate")),
                "retry_after": response.headers.get("retry-after"),
                "reflects_uuid": UUID_MARK in response.text,
                "backend_calls": sorted(set(calls)),
            })
    print("@@RESULT@@" + json.dumps(out))
    """
).replace("CONTAINMENT_ERROR", repr(CONTAINMENT_ERROR)).replace("UUID_MARK", repr(UUID))


def _run(requests, *, gate, mode="connection", record_io=False, store_down=False):
    """Drive the real app in a subprocess so gate-on module state cannot leak."""
    server_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    spec = {"gate": gate, "mode": mode, "record_io": record_io, "store_down": store_down,
            "requests": requests}
    completed = subprocess.run(
        [sys.executable, "-B", "-c", _DRIVER, json.dumps(spec)],
        cwd=server_root, capture_output=True, text=True, timeout=300,
    )
    assert "@@RESULT@@" in completed.stdout, completed.stderr[-2000:] or completed.stdout[-2000:]
    return json.loads(completed.stdout.split("@@RESULT@@", 1)[1].splitlines()[0])


def _requests_for_all_pairs(headers=None, raw_body=None):
    return [
        {"method": m, "path": p, "headers": headers,
         "raw_body": raw_body if (raw_body is not None and m == "POST") else None}
        for m, p in CONTAINED_PAIRS
    ]


class TestGateDarkContainmentIsRequestShapeBlind:
    """The current production configuration: all eight answer the same way."""

    @pytest.mark.parametrize("headers,label", [
        (None, "no authorization header"),
        ({"Authorization": "Bearer not-a-real-token"}, "invalid bearer"),
        ({"Authorization": f"Bearer {UUID}"}, "bearer naming a uuid"),
        ({"Authorization": "Basic Zm9vOmJhcg=="}, "non-bearer scheme"),
    ])
    def test_authorization_header_does_not_change_the_answer(self, headers, label):
        for row in _run(_requests_for_all_pairs(headers), gate=False):
            assert row["status"] == 503, (label, row)
            assert row["contained"], (label, row)
            assert row["retry_after"] == "3600", (label, row)
            assert not row["reflects_uuid"], (label, row)

    def test_malformed_body_does_not_change_the_answer(self):
        for row in _run(_requests_for_all_pairs(raw_body="{not json at all"), gate=False):
            assert row["status"] == 503, row
            assert row["contained"], row
            assert not row["reflects_uuid"], row


class TestGateOnContainmentIsRequestBlind:
    """The old eight preemption pins are replaced with the repaired contract."""

    @pytest.mark.parametrize("mode", ["connection", "execution"])
    def test_all_eight_pairs_remain_contained(self, mode):
        rows = _run(_requests_for_all_pairs(), gate=True, mode=mode)
        assert len(rows) == len(CONTAINED_PAIRS) == 8
        for row in rows:
            assert row["status"] == 503, row
            assert row["contained"], row
            assert row["retry_after"] == "3600", row
            assert not row["www_authenticate"], row
            assert not row["reflects_uuid"], row

    @pytest.mark.parametrize("mode", ["connection", "execution"])
    @pytest.mark.parametrize("headers,label", [
        (None, "no bearer"),
        ({"Authorization": "Bearer nope"}, "malformed bearer"),
        ({"Authorization": f"Bearer {UUID}"}, "uuid-shaped bearer"),
        ({"Authorization": f"Bearer {WELL_FORMED_REFRESH}"}, "well-formed refresh"),
        ({"Authorization": f"Bearer {WELL_FORMED_ACCESS}"}, "well-formed access"),
        ({"Authorization": f"Bearer {WELL_FORMED_PAT}"}, "well-formed personal"),
        ({"Authorization": "Basic Zm9vOmJhcg=="}, "non-bearer scheme"),
    ])
    def test_mcp_test_never_challenges_or_reads_credentials(self, mode, headers, label):
        [row] = _run([{"method": "GET", "path": "/mcp/test", "headers": headers}],
                     gate=True, mode=mode, record_io=True, store_down=True)
        assert row["status"] == 503, (mode, label, row)
        assert row["contained"], (mode, label, row)
        assert row["retry_after"] == "3600", (mode, label, row)
        assert not row["www_authenticate"], (mode, label, row)
        assert row["backend_calls"] == [], (mode, label, row)
        assert not row["reflects_bearer"], (mode, label, row)
        assert not row["reflects_uuid"], (mode, label, row)

    @pytest.mark.parametrize("mode", ["connection", "execution"])
    def test_malformed_body_does_not_change_containment(self, mode):
        for row in _run(_requests_for_all_pairs(raw_body="{not json at all"),
                        gate=True, mode=mode):
            assert row["status"] == 503, row
            assert row["contained"], row
            assert row["retry_after"] == "3600", row


class TestTheGateStaysShutForEverythingElse:
    """The exemption matches one exact (method, path) pair, not a prefix."""

    @pytest.mark.parametrize("method,path", [
        ("POST", "/mcp"),
        ("POST", "/mcp/"),
        ("GET", "/mcp"),
        ("POST", "/mcp/test"),
        ("GET", "/mcp/test/"),
        ("GET", "/mcp/test/x"),
        ("GET", "/mcp/testing"),
        ("GET", "/mcp/Test"),
        ("GET", "/mcp/test;x=1"),
        ("GET", "/mcp//test"),
    ])
    def test_near_misses_still_meet_the_connection_auth_boundary(self, method, path):
        [row] = _run([{"method": method, "path": path}], gate=True)
        assert row["status"] == 401, (method, path, row)
        assert row["www_authenticate"], (method, path, row)
        assert not row["contained"], (method, path, row)

    def test_percent_encoded_spelling_agrees_with_the_router(self):
        # Both the ASGI boundary and router receive the decoded path.
        [row] = _run([{"method": "GET", "path": "/mcp/%74est"}], gate=True)
        assert row["status"] == 503 and row["contained"], row


class TestTheExemptionIsBoundToTheRouteTable:
    """Lifting containment must fail tests until the exemption is removed."""

    def test_every_exempt_pair_is_maintenance_bound(self):
        import http_server
        from verifimind_mcp.middleware.mcp_auth_boundary import MAINTENANCE_CONTAINED_PAIRS

        assert MAINTENANCE_CONTAINED_PAIRS, "an empty exemption cannot pass vacuously"
        for method, path in MAINTENANCE_CONTAINED_PAIRS:
            bound = [route for route in http_server.app.routes
                     if getattr(route, "path", None) == path
                     and method in (getattr(route, "methods", None) or ())]
            assert len(bound) == 1, (method, path, bound)
            assert bound[0].endpoint is http_server.legacy_identity_maintenance_handler

    def test_every_maintenance_bound_mcp_pair_is_exempt(self):
        import http_server
        from verifimind_mcp.middleware.mcp_auth_boundary import MAINTENANCE_CONTAINED_PAIRS

        under_mcp = {
            (method, route.path)
            for route in http_server.app.routes
            if getattr(route, "endpoint", None) is http_server.legacy_identity_maintenance_handler
            and (route.path == "/mcp" or route.path.startswith("/mcp/"))
            for method in (route.methods or ()) if method not in ("HEAD", "OPTIONS")
        }
        assert under_mcp == set(MAINTENANCE_CONTAINED_PAIRS), (under_mcp, MAINTENANCE_CONTAINED_PAIRS)


class TestTheProbeItselfCanFail:
    """Known-negative: the subprocess harness must be able to report a non-contained answer.

    Without this, every assertion above could be passing because the driver never reaches the
    app — the failure mode this project has hit three times.
    """

    def test_a_route_outside_containment_is_reported_as_not_contained(self):
        [row] = _run([{"method": "GET", "path": "/health"}], gate=False)
        assert row["status"] == 200, row
        assert not row["contained"], "the /health route must not answer with the containment body"
