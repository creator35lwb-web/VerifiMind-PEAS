"""CS round 2 (2026-09-02) availability findings at ``d125bce`` — regressions.

F1  the execution-mode body peek buffered without bound: an OOM primitive for
    any anonymous caller once the gate is on and ``AUTH_BOUNDARY_MODE`` is
    ``execution`` (the S155 truncation fix had removed the read bound)
F3  Firestore transaction failures escaped ``run_transaction`` as HTTP 500
    instead of the fail-closed, retryable 503 the boundary promises
F2  the trusted ``X-Forwarded-For`` element was a hardcoded index rather than
    a bound property of the deployment's ingress (``TRUSTED_PROXY_HOPS``)

Each test reproduces the reviewer's attack and asserts the repair. Every test
marked "d125bce:" in a comment was proven to FAIL against the ``d125bce``
modules before the repair (module-swap proof in the S159 record).
"""

import asyncio
import math
import types
import warnings
from unittest.mock import patch

import pytest
import google.auth.exceptions as gaexc
from google.api_core import exceptions as gexc

warnings.filterwarnings("ignore", category=DeprecationWarning)

from verifimind_mcp.middleware import rate_limiter
from verifimind_mcp.middleware.mcp_auth_boundary import _MAX_PEEK_BODY, McpAuthBoundary
from verifimind_mcp.oauth import endpoints, stores
from verifimind_mcp.utils import client_ip as trust

from .oauth_fakes import FakeFirestore
from .test_auth_boundary import _InnerApp, _Sink, _issue_access, _receive_for, _scope


@pytest.fixture()
def env(monkeypatch):
    monkeypatch.setenv("VERIFIMIND_ENVIRONMENT", "development")
    monkeypatch.setenv("VERIFIMIND_PUBLIC_ORIGIN", "http://localhost:8080")
    monkeypatch.setenv("OAUTH_ISSUANCE_ENABLED", "true")
    monkeypatch.setenv("REGISTRATION_GATE_ENABLED", "true")
    monkeypatch.setenv("AUTH_BOUNDARY_MODE", "execution")


@pytest.fixture()
def db(env):
    fake = FakeFirestore()
    stores.clear_caches()
    with patch("verifimind_mcp.registration._get_firestore", return_value=fake):
        yield fake
    stores.clear_caches()


# ── F1: the body peek is bounded and the replay is spliced ──────────────────

CHUNK = 64 * 1024
CHUNKS = 4 * math.ceil(_MAX_PEEK_BODY / CHUNK)  # always four times the peek cap
READS_TO_CROSS_CAP = math.ceil(_MAX_PEEK_BODY / CHUNK) + 1
# Derived from the cap so the bound cannot go vacuous if the cap ever grows:
# the stream must exceed the cap by a wide margin, or an unbounded reader
# (the d125bce behaviour) would pass the F1 tests.
assert CHUNKS * CHUNK >= 3 * _MAX_PEEK_BODY
assert READS_TO_CROSS_CAP < CHUNKS


def _streaming_receive(chunks=CHUNKS, size=CHUNK):
    """An ASGI ``receive`` that streams ``chunks`` × ``size`` bytes and counts
    how many times the boundary asked for more."""
    state = {"calls": 0}

    async def receive():
        state["calls"] += 1
        index = state["calls"]
        if index > chunks:
            return {"type": "http.request", "body": b"", "more_body": False}
        return {
            "type": "http.request",
            "body": b"x" * size,
            "more_body": index < chunks,
        }

    return receive, state


def _run(boundary, scope, receive):
    sink = _Sink()
    asyncio.run(boundary(scope, receive, sink))
    return sink


class _EntryProbe(_InnerApp):
    """Records how many body reads the boundary had performed before the
    downstream app was entered — i.e. how much it BUFFERED."""

    def __init__(self, state):
        super().__init__()
        self._state = state
        self.reads_at_entry = None

    async def __call__(self, scope, receive, send):
        self.reads_at_entry = self._state["calls"]
        return await super().__call__(scope, receive, send)


class TestF1BoundedBodyPeek:
    def test_anonymous_oversized_stream_is_challenged_unread(self, env):
        receive, state = _streaming_receive()
        inner = _InnerApp()
        sink = _run(McpAuthBoundary(inner), _scope(), receive)
        assert sink.status == 401 and not inner.called
        # d125bce: read all 64 chunks (4 MiB) before challenging.
        assert state["calls"] <= READS_TO_CROSS_CAP

    def test_authenticated_oversized_stream_arrives_intact_and_bounded(self, db):
        access, _refresh = _issue_access(db)
        receive, state = _streaming_receive()
        inner = _EntryProbe(state)
        sink = _run(
            McpAuthBoundary(inner),
            _scope(headers={"Authorization": f"Bearer {access}"}),
            receive,
        )
        assert sink.status == 200 and inner.called
        # Nothing truncated — the S155 concern the unbounded read was meant
        # to solve is solved by splicing instead.
        assert len(inner.body) == CHUNKS * CHUNK
        # d125bce: 64 reads buffered before the app was entered.
        assert inner.reads_at_entry <= READS_TO_CROSS_CAP

    def test_small_body_replay_is_unchanged(self, env):
        body = b'{"jsonrpc":"2.0","id":1,"method":"initialize","params":{}}'
        inner = _InnerApp()
        sink = _run(McpAuthBoundary(inner), _scope(), _receive_for(body))
        assert sink.status == 200 and inner.body == body

    def test_disconnect_mid_read_is_still_protected(self, env):
        state = {"calls": 0}

        async def receive():
            state["calls"] += 1
            return {"type": "http.disconnect"}

        inner = _InnerApp()
        sink = _run(McpAuthBoundary(inner), _scope(), receive)
        assert sink.status == 401 and not inner.called and state["calls"] == 1

    def test_replay_hands_over_to_the_live_stream_after_the_buffer(self, env):
        # Pre-existing at d125bce (found by the S159 F1 lens): after the
        # buffered messages the replay returned an EMPTY http.request sentinel
        # forever instead of awaiting the live receive. The MCP streamable-HTTP
        # path hands this receive to the SSE disconnect listener, which loops
        # on it — a non-blocking sentinel never yields the event loop and
        # freezes the whole instance on the first anonymous non-gated call.
        body = b'{"jsonrpc":"2.0","id":1,"method":"initialize","params":{}}'
        state = {"calls": 0}

        async def receive():
            state["calls"] += 1
            if state["calls"] == 1:
                return {"type": "http.request", "body": body, "more_body": False}
            return {"type": "http.disconnect"}

        class _SseLikeApp(_InnerApp):
            saw_disconnect = None

            async def __call__(self, scope, receive, send):
                self.called = True
                first = await receive()
                self.body += first.get("body", b"")
                # The disconnect listener: loop on receive until the client
                # goes away. d125bce: the sentinel came back forever.
                for _ in range(10):
                    message = await receive()
                    if message["type"] == "http.disconnect":
                        self.saw_disconnect = True
                        break
                else:
                    self.saw_disconnect = False
                await send({"type": "http.response.start", "status": 200, "headers": []})
                await send({"type": "http.response.body", "body": b"ok"})

        inner = _SseLikeApp()
        sink = _run(McpAuthBoundary(inner), _scope(), receive)
        assert sink.status == 200 and inner.body == body
        assert inner.saw_disconnect is True
        assert state["calls"] == 2  # the body, then ONE live call → disconnect


# ── F3: backend failures fail CLOSED (503), never generic (500) ─────────────

class _ScriptedApi:
    """Scripted GAPIC surface behind a REAL firestore ``Transaction``: each
    plan is a list consumed per call; an exception entry is raised, anything
    else returns a canned response. No network."""

    def __init__(self, begin=(), commit=(), rollback=()):
        self.begin_plan = list(begin)
        self.commit_plan = list(commit)
        self.rollback_plan = list(rollback)
        self.calls = []

    def _step(self, plan, name):
        self.calls.append(name)
        if plan:
            item = plan.pop(0)
            if isinstance(item, BaseException):
                raise item

    def begin_transaction(self, request, metadata=None):
        self._step(self.begin_plan, "begin")
        return types.SimpleNamespace(transaction=b"txn-1")

    def commit(self, request, metadata=None):
        self._step(self.commit_plan, "commit")
        return types.SimpleNamespace(write_results=[], commit_time=None)

    def rollback(self, request, metadata=None):
        self._step(self.rollback_plan, "rollback")
        return None


class _ScriptedClient:
    """A non-fake client whose transactions are the LIBRARY's own
    ``Transaction`` objects driven by the scripted API — so the real
    ``transactional`` wrapper, retry, and rollback paths execute."""
    is_fake = False
    _database_string = "projects/p/databases/(default)"
    _rpc_metadata = []

    def __init__(self, api):
        self._firestore_api = api

    def transaction(self, **kwargs):
        from google.cloud.firestore_v1.transaction import Transaction
        return Transaction(self, **kwargs)


def _run_real(api, func=lambda _txn: "ok"):
    with patch("verifimind_mcp.registration._get_firestore", return_value=_ScriptedClient(api)):
        return stores.run_transaction(func)


class TestF3RealTransactionWrapper:
    """The shapes the LIBRARY produces, not hand-built ones. The adversarial
    lens refuted the first S159 repair exactly here: a failed BeginTransaction
    surfaces as ``ValueError('...cannot be rolled back')`` whose only link to
    the backend error is ``__context__``."""

    @pytest.mark.parametrize("exc", [
        gexc.ServiceUnavailable("backend"),
        gexc.DeadlineExceeded("deadline"),
        gexc.Unauthenticated("creds"),
        gexc.InternalServerError("500"),
        gexc.RetryError("deadline of 60s exceeded", gexc.ServiceUnavailable("x")),
        gaexc.RefreshError("token refresh failed"),
    ], ids=["ServiceUnavailable", "DeadlineExceeded", "Unauthenticated",
            "InternalServerError", "RetryError", "RefreshError"])
    def test_begin_failure_surfaces_as_store_unavailable(self, exc):
        # d125bce AND the first S159 repair: the rollback ValueError escaped.
        with pytest.raises(stores.StoreUnavailable):
            _run_real(_ScriptedApi(begin=[exc]))

    def test_commit_aborted_then_retry_begin_fails(self):
        with pytest.raises(stores.StoreUnavailable):
            _run_real(_ScriptedApi(
                begin=[None, gexc.ServiceUnavailable("backend")],
                commit=[gexc.Aborted("contention")],
            ))

    def test_commit_aborted_until_retries_are_exhausted(self):
        # The library's real ValueError-from-Aborted wrapper (d125bce: escaped).
        with pytest.raises(stores.StoreUnavailable):
            _run_real(_ScriptedApi(commit=[gexc.Aborted("contention")] * 5))

    def test_commit_failure_with_a_failing_rollback(self):
        with pytest.raises(stores.StoreUnavailable):
            _run_real(_ScriptedApi(
                commit=[gexc.ServiceUnavailable("x")],
                rollback=[gexc.ServiceUnavailable("rollback")],
            ))

    def test_read_failure_inside_the_transaction(self):
        def func(_txn):
            raise gexc.DeadlineExceeded("read")
        with pytest.raises(stores.StoreUnavailable):
            _run_real(_ScriptedApi(), func)

    def test_application_signal_passes_through_as_the_same_instance(self):
        signal = stores._RefreshReuseDetected("grant-1")

        def func(_txn):
            raise signal
        with pytest.raises(stores._RefreshReuseDetected) as info:
            _run_real(_ScriptedApi(), func)
        assert info.value is signal

    def test_programming_error_is_not_masked(self):
        def func(_txn):
            raise KeyError("a bug, not the backend")
        with pytest.raises(KeyError):
            _run_real(_ScriptedApi(), func)

    def test_success_returns_the_result(self):
        assert _run_real(_ScriptedApi()) == "ok"


class TestF3ChainWalk:
    """Library-independent pins of the chain semantics."""

    def test_cause_chain_is_walked(self):
        outer = RuntimeError("outer")
        mid = ValueError("mid")
        mid.__cause__ = gexc.Aborted("c")
        outer.__cause__ = mid
        assert stores.is_backend_failure(outer)

    def test_context_chain_is_walked_unless_suppressed(self):
        exc = ValueError("The transaction has no transaction ID, so it cannot be rolled back.")
        exc.__context__ = gexc.ServiceUnavailable("begin")
        assert stores.is_backend_failure(exc)
        exc.__suppress_context__ = True
        assert not stores.is_backend_failure(exc)

    def test_unrelated_exceptions_are_not_backend_failures(self):
        assert not stores.is_backend_failure(ValueError("plain"))
        assert not stores.is_backend_failure(stores._RefreshReuseDetected("g"))

    def test_raw_grpc_transport_error_is_a_backend_failure(self):
        # Defence in depth: GAPIC wraps every Firestore RPC, so this shape is
        # not reachable in production — but it is a backend failure.
        import grpc
        assert stores.is_backend_failure(grpc.RpcError("raw transport"))


class _FailingDoc:
    def __init__(self, exc):
        self._exc = exc

    def set(self, *_a, **_k):
        raise self._exc

    def update(self, *_a, **_k):
        raise self._exc

    def delete(self, *_a, **_k):
        raise self._exc

    def get(self, *_a, **_k):
        raise self._exc


class _FailingCollection:
    def __init__(self, exc):
        self._exc = exc

    def document(self, _doc_id):
        return _FailingDoc(self._exc)

    def where(self, *_a, **_k):
        return self

    def limit(self, _n):
        return self

    def get(self):
        raise self._exc


class _FailingDb:
    """Non-fake client whose every document/query RPC fails."""
    is_fake = False

    def __init__(self, exc):
        self._exc = exc

    def collection(self, _name):
        return _FailingCollection(self._exc)


_STORE_CALLS = [
    ("register_client", lambda: stores.register_client(
        client_name="c", redirect_uris=["https://c/cb"], registration_path="dcr")),
    ("persist_code", lambda: stores.persist_code(
        code_id="id", code_secret_hash="h", client_id="c", subject_uuid="s",
        redirect_uri="https://c/cb", code_challenge="x", scope="mcp")),
    ("issue_pat", lambda: stores.issue_pat(
        subject_uuid="s", actor_class="external", parent_grant_id="g")),
    ("put_verification", lambda: stores.put_verification(
        email="a@b.c", code="123456", purpose="authorize", session_id="sid")),
    ("revoke_grant_family", lambda: stores.revoke_grant_family("g")),
    ("revoke_all_for_subject", lambda: stores.revoke_all_for_subject("s")),
    ("put_authorize_session", lambda: stores.put_authorize_session("sid", {"k": "v"})),
    ("update_authorize_session", lambda: stores.update_authorize_session("sid", {"k": "v"})),
    ("drop_authorize_session", lambda: stores.drop_authorize_session("sid")),
    ("get_client", lambda: stores.get_client("cid")),
]


class TestF3StoreCallsFailClosed:
    """Class sweep beyond CS's literal finding: every raw Firestore write and
    query in the store maps a backend failure to StoreUnavailable."""

    @pytest.mark.parametrize("name,call", _STORE_CALLS, ids=[n for n, _ in _STORE_CALLS])
    def test_backend_failure_surfaces_as_store_unavailable(self, env, name, call):
        # d125bce: the raw google.api_core exception escaped (generic 500)
        # from every write; only _read mapped it.
        with patch("verifimind_mcp.registration._get_firestore",
                   return_value=_FailingDb(gexc.ServiceUnavailable("backend"))):
            with pytest.raises(stores.StoreUnavailable):
                call()


class TestF3CeremonyOutagesAre503:
    @staticmethod
    def _request(form):
        async def _form():
            return form
        return types.SimpleNamespace(
            form=_form, headers={}, client=types.SimpleNamespace(host="10.0.0.1"))

    def test_verify_code_outage_is_503_not_invalid_code(self, env, monkeypatch):
        monkeypatch.setattr(endpoints.stores, "get_authorize_session",
                            lambda _sid: {"client_name": "c"})

        def _raise(**_kw):
            raise stores.StoreUnavailable("backend")
        monkeypatch.setattr(endpoints.stores, "claim_verification", _raise)
        response = asyncio.run(endpoints.oauth_authorize_post_handler(self._request({
            "sid": "s", "action": "verify_code", "email": "a@b.c", "code": "123456",
        })))
        # d125bce: 200 "That code is not valid (or expired)" during an outage.
        assert response.status_code == 503

    def test_session_read_outage_is_503_not_session_expired(self, env, monkeypatch):
        def _raise(_sid):
            raise stores.StoreUnavailable("backend")
        monkeypatch.setattr(endpoints.stores, "get_authorize_session", _raise)
        response = asyncio.run(endpoints.oauth_authorize_post_handler(
            self._request({"sid": "s", "action": "consent"})))
        # d125bce: 400 "Session expired" during an outage.
        assert response.status_code == 503

    def test_subject_resolution_backend_failure_returns_none(self, env):
        with patch("verifimind_mcp.registration._get_firestore",
                   return_value=_FailingDb(gexc.ServiceUnavailable("backend"))):
            # d125bce: the RPC exception escaped the consent step (generic 500).
            assert endpoints._resolve_or_create_subject("a@b.c") is None


# ── F2: the trusted XFF element is bound to the ingress, not hardcoded ──────

def _request(xff=None, real_ip=None, peer="10.0.0.1"):
    headers = {}
    if xff is not None:
        headers["x-forwarded-for"] = xff
    if real_ip is not None:
        headers["x-real-ip"] = real_ip
    return types.SimpleNamespace(headers=headers, client=types.SimpleNamespace(host=peer))


# caller-supplied, then the two elements a trusted ingress may append
CHAIN = "198.51.100.7, 203.0.113.9, 192.0.2.1"
RESOLVERS = [rate_limiter.get_client_ip, endpoints._client_ip]


class TestF2TrustedProxyHops:
    @pytest.mark.parametrize("resolver", RESOLVERS)
    def test_default_depth_takes_the_gfe_appended_last_element(self, monkeypatch, resolver):
        monkeypatch.delenv("TRUSTED_PROXY_HOPS", raising=False)
        assert resolver(_request(CHAIN)) == "192.0.2.1"

    @pytest.mark.parametrize("resolver", RESOLVERS)
    def test_depth_two_selects_the_client_behind_a_google_external_lb(self, monkeypatch, resolver):
        monkeypatch.setenv("TRUSTED_PROXY_HOPS", "2")
        # d125bce: 192.0.2.1 — the load balancer, one bucket for everyone.
        assert resolver(_request(CHAIN)) == "203.0.113.9"

    @pytest.mark.parametrize("resolver", RESOLVERS)
    def test_chain_shorter_than_trust_depth_uses_the_direct_peer(self, monkeypatch, resolver):
        monkeypatch.setenv("TRUSTED_PROXY_HOPS", "2")
        # d125bce: the caller-supplied element became the key.
        assert resolver(_request("198.51.100.7")) == "10.0.0.1"

    @pytest.mark.parametrize(
        "raw,expected",
        [("", 1), ("abc", 1), ("0", 1), ("-3", 1), ("2", 2), ("99", trust.MAX_TRUSTED_PROXY_HOPS)],
    )
    def test_env_parsing_defaults_and_clamps(self, monkeypatch, raw, expected):
        monkeypatch.setenv("TRUSTED_PROXY_HOPS", raw)
        assert trust.trusted_proxy_hops() == expected

    def test_no_forwarded_chain_preserves_the_prior_fallbacks(self, monkeypatch):
        monkeypatch.delenv("TRUSTED_PROXY_HOPS", raising=False)
        assert rate_limiter.get_client_ip(_request(real_ip="203.0.113.5")) == "203.0.113.5"
        assert rate_limiter.get_client_ip(_request()) == "10.0.0.1"
        # The issuance limiter never honoured X-Real-IP; it still does not.
        assert endpoints._client_ip(_request(real_ip="203.0.113.5")) == "10.0.0.1"
        assert endpoints._client_ip(_request()) == "10.0.0.1"

    def test_ingress_trust_disclosure_matches_configuration(self, monkeypatch):
        monkeypatch.setenv("TRUSTED_PROXY_HOPS", "2")
        assert trust.ingress_trust() == {
            "trusted_proxy_hops": 2,
            "client_element": "X-Forwarded-For[-2]",
            "short_chain_policy": "direct peer",
        }
