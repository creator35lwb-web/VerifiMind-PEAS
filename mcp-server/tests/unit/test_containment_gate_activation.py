"""Plane 1 of T S176's re-expression contract: containment across gate activation.

`test_legacy_uuid_containment.py` already pins the eight contained pairs under the current
**gate-dark** configuration. This module adds the two things that file does not cover:

1.  **Gate activation.** `McpAuthBoundary` matches `/mcp/*` when `REGISTRATION_GATE_ENABLED`
    is true, so it can answer before `legacy_identity_maintenance_handler` ever runs. Measured:
    exactly **one of the eight** pairs changes — `GET /mcp/test` returns `401 invalid_token`
    with a `WWW-Authenticate` challenge instead of the request-blind maintenance `503`. The
    other seven are unaffected because they are not under `/mcp/`.

    The preempted answer is **not** request-blind. A bearer that is not bearer-valid is refused
    before any lookup, but a **well-formed** access or personal token is looked up in the
    credential store, so at gate activation a route meant to be uniformly maintenance-contained
    becomes a live authentication endpoint whose answer varies by token kind. An earlier
    revision of this module asserted "no backend I/O" from three bearer variants that were all
    malformed - one equivalence class - and so never exercised the path a well-formed credential
    takes. That claim was wider than its evidence; both classes are now pinned separately.

    These tests **record that measurement**; they do not endorse it. Per T S176 the preemption
    is a **production-code residual** for separate authority to decide, and pinning it here is
    what makes a future silent change visible. If T rules that request-blind containment must
    hold across gate activation, the fix belongs in production code and these expectations
    change with it.

    **Limit, stated rather than glossed.** The well-formed cases run with the store forced
    unavailable, so what they pin is "the lookup is attempted, and an outage is answered with
    the token-store outage contract rather than the maintenance contract". What a **live** store
    answers for a well-formed unknown token is not measured here and is not claimed.

2.  **Request-shape variation.** The containment answer must not depend on an `Authorization`
    header or a malformed body, in either gate state.

Every gate-on case runs in a **subprocess**. Enabling the gate requires re-importing
`http_server` with different environment, and doing that in-process would leave the reloaded
modules cached for every later test in the session.
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

# The single pair the auth boundary preempts when the gate is enabled.
PREEMPTED_PAIR = ("GET", "/mcp/test")

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


class TestGateActivationPreemptsExactlyOnePair:
    """RECORDED RESIDUAL, not an endorsement — see the module docstring.

    T S176 rules whether request-blind containment must survive gate activation. Until then
    these tests pin the measured behaviour - including that the preempted route consults the
    credential store for a well-formed bearer - so it cannot change unnoticed.
    """

    def test_seven_of_eight_pairs_are_unaffected_by_gate_activation(self):
        rows = _run(_requests_for_all_pairs(), gate=True)
        unaffected = [r for r in rows if (r["method"], r["path"]) != PREEMPTED_PAIR]
        assert len(unaffected) == 7, rows
        for row in unaffected:
            assert row["status"] == 503, row
            assert row["contained"], row
            assert row["retry_after"] == "3600", row

    def test_mcp_test_is_preempted_by_the_auth_boundary(self):
        [row] = _run([{"method": "GET", "path": "/mcp/test"}], gate=True)
        assert row["status"] == 401, row
        assert not row["contained"], row
        assert row["www_authenticate"], "a preempting boundary must still challenge explicitly"

    def test_preemption_holds_in_execution_mode_too(self):
        [row] = _run([{"method": "GET", "path": "/mcp/test"}], gate=True, mode="execution")
        assert row["status"] == 401, row
        assert not row["contained"], row

    @pytest.mark.parametrize("headers,label", [
        (None, "no bearer"),
        ({"Authorization": "Bearer nope"}, "invalid bearer"),
        ({"Authorization": f"Bearer {UUID}"}, "bearer naming a uuid"),
        ({"Authorization": f"Bearer {WELL_FORMED_REFRESH}"}, "well-formed refresh token"),
    ])
    def test_a_bearer_that_is_not_bearer_valid_is_refused_before_any_lookup(self, headers, label):
        """ONE equivalence class, whatever the parametrize list looks like.

        The first three fail the wire-format parse; the fourth parses, but a refresh token is
        not an accepted bearer kind. All four are rejected before any store is consulted. This
        says nothing about a well-formed access or personal token - that path is pinned in
        `test_a_well_formed_bearer_is_looked_up_in_the_credential_store` below.
        """
        [row] = _run([{"method": "GET", "path": "/mcp/test", "headers": headers}],
                     gate=True, record_io=True, store_down=True)
        assert row["status"] == 401, (label, row)
        assert row["backend_calls"] == [], (label, row)
        assert not row["reflects_uuid"], (label, row)
        assert not row["reflects_bearer"], (label, row)

    @pytest.mark.parametrize("token,label", [
        (WELL_FORMED_ACCESS, "well-formed access token"),
        (WELL_FORMED_PAT, "well-formed personal token"),
    ])
    def test_a_well_formed_bearer_is_looked_up_in_the_credential_store(self, token, label):
        """The class the earlier revision never exercised - and the reason the residual is not
        "contract-shape only".

        A well-formed unknown bearer reaches the credential store. With the store unavailable
        the answer is the token-store OUTAGE contract, not the maintenance contract: a route
        intended to be request-blind now distinguishes token kinds and reports store health.
        RECORDED, not endorsed; see the module docstring for the limit on this measurement.
        """
        [row] = _run([{"method": "GET", "path": "/mcp/test",
                       "headers": {"Authorization": f"Bearer {token}"}}],
                     gate=True, record_io=True, store_down=True)
        assert row["status"] == 503, (label, row)
        assert not row["contained"], (label, "an outage answer must not be mistaken for containment", row)
        assert row["retry_after"] != "3600", (label, "this is not the maintenance Retry-After", row)
        assert "stores._read" in row["backend_calls"], (label, row)
        assert "stores._db" in row["backend_calls"], (label, row)
        assert not row["reflects_bearer"], (label, row)


class TestTheProbeItselfCanFail:
    """Known-negative: the subprocess harness must be able to report a non-contained answer.

    Without this, every assertion above could be passing because the driver never reaches the
    app — the failure mode this project has hit three times.
    """

    def test_a_route_outside_containment_is_reported_as_not_contained(self):
        [row] = _run([{"method": "GET", "path": "/health"}], gate=False)
        assert row["status"] == 200, row
        assert not row["contained"], "the /health route must not answer with the containment body"
