"""
WP-B — FailoverExecutor deterministic failure injection (T S88 D-88-2..5 +
S90 B-90-1..9 amendment regressions)
=========================================================================

The runtime-failover contract, enforced with shaped fakes (no SDK, no
network). v2 adds a named regression for each of T's five independently
reproduced S90 counterexamples — terminal-auth circuit poisoning, the
same-family "hop", the blind 429 retry, the stranded half-open probe, and
fail-open evidence — plus backup admission, MCP terminal payloads, and the
Z-veto / degraded-cap synthesis invariants after a hop.

Design: Hub #81 (WP-B design v2); reviews:
.macp/reviews/20260723_T_wpA_exit_and_wpB_design_review.md (S88) and
.macp/reviews/20260724_T_pr304_wpb_implementation_review.md (S90).
"""

import asyncio
import json
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

import verifimind_mcp.llm as llm_pkg
import verifimind_mcp.llm.failover as fo
from verifimind_mcp.server import (
    attach_failover_disclosure,
    failover_error_payload,
    trinity_failover_meta,
)


# --- shaped fakes (duck-typed like the raw SDK exceptions) -------------------

class RateLimitError(Exception):
    def __init__(self, retry_after=None):
        super().__init__("rate limited")
        if retry_after is not None:
            self.retry_after = retry_after


class _Headers(dict):
    pass


class _HeaderResponse:
    def __init__(self, headers):
        self.headers = _Headers(headers)
        self.status_code = 429


class RateLimitHeaderError(Exception):
    """429 whose Retry-After lives on response.headers (either HTTP form)."""

    def __init__(self, headers):
        super().__init__("rate limited")
        self.response = _HeaderResponse(headers)


class AuthenticationError(Exception):
    pass


class APIConnectionError(Exception):
    pass


class InternalServerError(Exception):
    pass


class APITimeoutError(Exception):
    pass


class BadRequestError(Exception):
    pass


def _ok(quality="real"):
    return {"content": {"x": 1}, "usage": {"output_tokens": 5},
            "_inference_quality": quality}


class FakeProvider:
    """Scripted provider: each generate() pops one item — an Exception to
    raise or a response dict to return. Records every call's kwargs so tests
    can assert the per-attempt token bound (B-92-4)."""

    def __init__(self, script, model_name="groq/test-model"):
        self._script = list(script)
        self._model_name = model_name
        self.calls = 0
        self.seen_kwargs = []

    async def generate(self, **kwargs):
        await asyncio.sleep(0)
        self.calls += 1
        self.seen_kwargs.append(kwargs)
        item = self._script.pop(0)
        if isinstance(item, Exception):
            raise item
        return item

    def get_model_name(self):
        return self._model_name


class HangingProvider(FakeProvider):
    async def generate(self, **kwargs):
        self.calls += 1
        await asyncio.Event().wait()  # blocks until cancelled / timed out


EVIDENCE_BUILD = "abc1234"


@pytest.fixture(autouse=True)
def _failover_env(monkeypatch, tmp_path):
    """Every test starts flag-ON with a VALID evidence tuple (fail-closed
    otherwise, B-90-7), clean circuits/admission, fast budgets; dark-mode and
    evidence tests override explicitly. The tested-at stamp is generated
    fresh per test — B-92-2's future-rejection correctly invalidated a
    hardcoded midnight stamp the first time it ran (the validator catching
    its own suite's stale evidence). B-95-1: the build identity is an
    IMAGE-OWNED FILE (never an env var) — the fixture writes a per-test
    identity file matching the evidence value. Yields the stamp for tests
    that assert surface projection."""
    tested_at = datetime.now(timezone.utc).isoformat()
    monkeypatch.setenv(fo.ENABLE_ENV, "true")
    monkeypatch.setenv(fo.EVIDENCE_TESTED_ENV, tested_at)
    monkeypatch.setenv(fo.EVIDENCE_BUILD_ENV, EVIDENCE_BUILD)
    identity_file = tmp_path / "build_commit_sha"
    identity_file.write_text(EVIDENCE_BUILD, encoding="utf-8")
    monkeypatch.setattr(fo, "_BUILD_IDENTITY_FILE", str(identity_file))
    monkeypatch.delenv("K_REVISION", raising=False)
    monkeypatch.delenv("BUILD_COMMIT_SHA", raising=False)
    monkeypatch.setenv(fo.ATTEMPT_TIMEOUT_ENV, "0.5")
    monkeypatch.setenv(fo.TOTAL_DEADLINE_ENV, "5")
    fo.reset_circuits()
    yield tested_at
    fo.reset_circuits()


@pytest.fixture
def gemini_backup(monkeypatch):
    """Route the resolved 'gemini' hop target to a scripted fake."""
    backup = FakeProvider([_ok()], model_name="gemini/backup-model")

    def _fake_get_provider(name):
        assert name == "gemini"
        return backup
    monkeypatch.setattr(llm_pkg, "get_provider", _fake_get_provider)
    return backup


def _marked(script, agent="Z", active="groq", fallback="gemini",
            model_name="groq/test-model"):
    return fo.mark_hosted_failover(
        FakeProvider(script, model_name), agent, active, fallback)


def _run(provider, prompt="p", **kwargs):
    return asyncio.run(fo.generate_with_failover(
        provider, prompt=prompt, output_schema={}, temperature=0.2,
        max_tokens=64, **kwargs))


async def _await_cancelled(task):
    """Effectful cancellation receipt (replaces a bare `await` inside a
    raises block, which scanners flag as an ineffectual statement): awaiting
    a cancelled task raises CancelledError — captured as a boolean."""
    try:
        await task
    except asyncio.CancelledError:
        return True
    return False


# ---------------------------------------------------------------------------
# Dark mode + locality consent (D-88-3)
# ---------------------------------------------------------------------------

def test_flag_off_is_plain_delegation(monkeypatch):
    monkeypatch.setenv(fo.ENABLE_ENV, "")
    provider = _marked([_ok()])
    response = _run(provider)
    assert "_provider_attempts" not in response  # no telemetry keys added
    assert provider.calls == 1


def test_flag_off_failure_raises_raw_exception(monkeypatch):
    monkeypatch.setenv(fo.ENABLE_ENV, "")
    provider = _marked([APIConnectionError()])
    with pytest.raises(APIConnectionError):
        _run(provider)


def test_unmarked_byok_provider_never_hops(monkeypatch):
    """A session/ephemeral BYOK provider (no marker) raises straight through
    even with the flag ON — a bad user key must never consume hosted keys."""
    hop_calls = []
    monkeypatch.setattr(llm_pkg, "get_provider",
                        lambda name: hop_calls.append(name))
    provider = FakeProvider([AuthenticationError()])  # NOT marked
    with pytest.raises(AuthenticationError):
        _run(provider)
    assert hop_calls == []


def test_unmarked_ollama_stays_local(monkeypatch):
    hop_calls = []
    monkeypatch.setattr(llm_pkg, "get_provider",
                        lambda name: hop_calls.append(name))
    provider = FakeProvider([APIConnectionError()],
                            model_name="ollama/llama3.2")  # NOT marked
    with pytest.raises(APIConnectionError):
        _run(provider)
    assert hop_calls == []


def test_hosted_resolution_marks_with_resolved_chain(monkeypatch):
    """config_helper wiring: the hosted env-key branch marks AND attaches the
    resolved chain (B-90-2); session BYOK gets neither."""
    for key in ("GROQ_API_KEY", "GEMINI_API_KEY", "ANTHROPIC_API_KEY",
                "X_AGENT_PROVIDER", "Z_AGENT_PROVIDER"):
        monkeypatch.delenv(key, raising=False)
    monkeypatch.setenv("GROQ_API_KEY", "gsk_hosted")
    from verifimind_mcp.config_helper import get_agent_provider
    hosted = get_agent_provider("Z")
    assert fo.hosted_failover_agent(hosted) == "Z"
    assert fo.hosted_hop_chain(hosted) == ("gemini",)

    class Cfg:
        llm_provider = "groq"
        groq_api_key = "gsk_byok_user"

    class Ctx:
        session_config = Cfg()

    byok = get_agent_provider("Z", Ctx())
    assert fo.hosted_failover_agent(byok) is None
    assert fo.hosted_hop_chain(byok) == ()


def test_marker_excludes_mock_and_same_family_targets():
    same_family = _marked([_ok()], active="gemini", fallback="gemini",
                          model_name="gemini/gemini-3.5-flash-lite")
    assert fo.hosted_hop_chain(same_family) == ()          # B-90-2
    mock_fallback = _marked([_ok()], agent="X", active="gemini",
                            fallback="mock",
                            model_name="gemini/gemini-3.5-flash-lite")
    assert fo.hosted_hop_chain(mock_fallback) == ()        # no-silent-mock
    normal = _marked([_ok()])
    assert fo.hosted_hop_chain(normal) == ("gemini",)


def test_no_silent_mock_on_exhaustion():
    """Agent X (empty chain): a hop-class failure surfaces an explicit
    error — never a synthetic response."""
    provider = _marked([APITimeoutError()], agent="X", active="gemini",
                       fallback="mock",
                       model_name="gemini/gemini-3.5-flash-lite")
    with pytest.raises(fo.FailoverExhaustedError) as excinfo:
        _run(provider)
    assert excinfo.value.error_code == "FAILOVER_EXHAUSTED"
    assert excinfo.value.attempts[0]["outcome_class"] == "attempt_timeout"


# ---------------------------------------------------------------------------
# B-90-2 regression: a hop must cross provider families
# ---------------------------------------------------------------------------

def test_gemini_primary_never_hops_to_gemini(monkeypatch):
    """T's reproduced counterexample: gemini -> gemini with
    _failover_occurred=true. Now: empty resolved chain -> explicit
    exhaustion, single family in the trail, no fake failover."""
    hop_calls = []
    monkeypatch.setattr(llm_pkg, "get_provider",
                        lambda name: hop_calls.append(name))
    provider = _marked([InternalServerError(), InternalServerError()],
                       active="gemini", fallback="gemini",
                       model_name="gemini/gemini-3.5-flash-lite")
    with pytest.raises(fo.FailoverExhaustedError) as excinfo:
        _run(provider)
    assert hop_calls == []
    assert {a["provider"] for a in excinfo.value.attempts} == {"gemini"}


def test_hop_crosses_provider_families(gemini_backup):
    provider = _marked([APITimeoutError()])
    response = _run(provider)
    families = [a["provider"] for a in response["_provider_attempts"]]
    assert families == ["groq", "gemini"]
    assert response["_failover_occurred"] is True


# ---------------------------------------------------------------------------
# Failure-class policy (D-88-2) + B-90-1 circuit hygiene
# ---------------------------------------------------------------------------

def test_classify_auth_is_terminal_and_circuit_neutral():
    decision = fo.classify_failure(AuthenticationError())
    assert decision.action == fo.TERMINAL
    assert decision.circuit_relevant is False


def test_classify_invalid_request_is_terminal():
    assert fo.classify_failure(BadRequestError()).action == fo.TERMINAL


def test_classify_429_with_retry_after_retries():
    decision = fo.classify_failure(RateLimitError(retry_after=7))
    assert decision.action == fo.RETRY
    assert decision.retry_after == pytest.approx(7.0)
    assert decision.circuit_relevant is False


def test_classify_429_without_retry_after_hops():
    """B-90-3 regression: absent Retry-After must NOT blind-retry."""
    decision = fo.classify_failure(RateLimitError())
    assert decision.action == fo.HOP
    assert decision.reason_class == "rate_limited_no_retry_after"


def test_classify_timeout_hops():
    assert fo.classify_failure(APITimeoutError()).action == fo.HOP


def test_classify_unknown_is_terminal_conservative():
    assert fo.classify_failure(ValueError("weird")).action == fo.TERMINAL


def test_terminal_auth_failures_do_not_poison_circuit(monkeypatch):
    """B-90-1 regression: T reproduced terminal_auth_circuit_state=open after
    three auth failures. Terminal classes are circuit-neutral now."""
    monkeypatch.setattr(llm_pkg, "get_provider", lambda name: None)
    for _ in range(fo.CIRCUIT_FAILURE_THRESHOLD + 1):
        provider = _marked([AuthenticationError()])
        with pytest.raises(fo.FailoverTerminalError):
            _run(provider)
    assert fo.circuit_snapshot().get("groq", "closed") == "closed"
    healthy = _marked([_ok()])
    response = _run(healthy)          # a valid request still uses the primary
    assert healthy.calls == 1
    assert response["_failover_occurred"] is False


def test_rate_limit_failures_do_not_poison_circuit(gemini_backup):
    for _ in range(fo.CIRCUIT_FAILURE_THRESHOLD + 1):
        gemini_backup._script.append(_ok())
        provider = _marked([RateLimitError()])   # no Retry-After -> hop
        _run(provider)
    assert fo.circuit_snapshot().get("groq", "closed") == "closed"


def test_terminal_failure_is_typed_with_original_cause(gemini_backup):
    provider = _marked([AuthenticationError()])
    with pytest.raises(fo.FailoverTerminalError) as excinfo:
        _run(provider)
    assert excinfo.value.error_code == "HOSTED_PROVIDER_TERMINAL"
    assert excinfo.value.final_reason_class == "auth_or_config"
    assert isinstance(excinfo.value.__cause__, AuthenticationError)
    assert gemini_backup.calls == 0


def test_safety_refusal_is_a_response_not_a_failure(gemini_backup):
    """A refusal arrives as a normal completion — the executor returns it
    verbatim and never consults the classifier."""
    refusal = {"content": {"analysis": "I cannot help with that."},
               "usage": {}, "_inference_quality": "real"}
    provider = _marked([refusal])
    response = _run(provider)
    assert response["content"]["analysis"].startswith("I cannot")
    assert gemini_backup.calls == 0
    assert response["_failover_occurred"] is False


# ---------------------------------------------------------------------------
# Retry / hop execution paths (incl. B-90-3 Retry-After forms)
# ---------------------------------------------------------------------------

def test_primary_success_no_failover_machinery(gemini_backup):
    provider = _marked([_ok()])
    response = _run(provider)
    assert response["_failover_occurred"] is False
    assert [a["outcome_class"] for a in response["_provider_attempts"]] == ["success"]
    assert len(response["_failover_correlation"]) == 8
    assert gemini_backup.calls == 0


def test_connection_error_retries_same_provider(gemini_backup):
    provider = _marked([APIConnectionError(), _ok()])
    response = _run(provider)
    assert provider.calls == 2
    assert gemini_backup.calls == 0
    assert response["_failover_occurred"] is False
    assert [a["outcome_class"] for a in response["_provider_attempts"]] == [
        "connection_error", "success"]


def test_retry_spent_then_hop(gemini_backup):
    provider = _marked([InternalServerError(), InternalServerError()])
    response = _run(provider)
    assert provider.calls == 2
    assert gemini_backup.calls == 1
    assert response["_failover_occurred"] is True
    assert response["_provider_attempts"][-1]["provider"] == "gemini"
    assert response["_provider_attempts"][-1]["outcome_class"] == "success"


def test_timeout_class_hops_without_retry(gemini_backup):
    provider = _marked([APITimeoutError()])
    response = _run(provider)
    assert provider.calls == 1          # no same-provider retry
    assert gemini_backup.calls == 1
    assert response["_failover_occurred"] is True


def test_429_with_small_retry_after_waits_and_retries(gemini_backup):
    provider = _marked([RateLimitError(retry_after=0.01), _ok()])
    response = _run(provider)
    assert provider.calls == 2
    assert gemini_backup.calls == 0
    assert response["_failover_occurred"] is False


def test_429_without_retry_after_hops_immediately(gemini_backup):
    """B-90-3 regression: T reproduced primary=2 backup=0 on a bare 429."""
    provider = _marked([RateLimitError()])
    response = _run(provider)
    assert provider.calls == 1          # exactly one primary call — no blind retry
    assert gemini_backup.calls == 1
    assert response["_failover_occurred"] is True


def test_429_with_http_date_retry_after_waits(gemini_backup):
    from email.utils import format_datetime
    soon = format_datetime(datetime.now(timezone.utc))  # ~0s wait
    provider = _marked([RateLimitHeaderError({"Retry-After": soon}), _ok()])
    response = _run(provider)
    assert provider.calls == 2
    assert gemini_backup.calls == 0
    assert response["_failover_occurred"] is False


def test_429_with_malformed_retry_after_hops(gemini_backup):
    provider = _marked([RateLimitHeaderError({"Retry-After": "soonish"})])
    _run(provider)
    assert provider.calls == 1
    assert gemini_backup.calls == 1


def test_429_with_negative_retry_after_clamps_to_immediate_retry(gemini_backup):
    provider = _marked([RateLimitError(retry_after=-5), _ok()])
    _run(provider)
    assert provider.calls == 2          # negative clamps to 0 => one retry
    assert gemini_backup.calls == 0


def test_429_with_retry_after_beyond_budget_hops_immediately(gemini_backup):
    provider = _marked([RateLimitError(retry_after=9999)])
    response = _run(provider)
    assert provider.calls == 1          # no blind wait on a drained quota
    assert gemini_backup.calls == 1
    assert response["_failover_occurred"] is True


def test_hop_budget_is_one(gemini_backup):
    """Backup failure after the single hop is exhaustion — never a 2nd hop."""
    gemini_backup._script = [InternalServerError()]
    provider = _marked([APITimeoutError()])
    with pytest.raises(fo.FailoverExhaustedError) as excinfo:
        _run(provider)
    assert [a["provider"] for a in excinfo.value.attempts] == ["groq", "gemini"]


def test_attempt_cap_is_three(gemini_backup):
    gemini_backup._script = [APIConnectionError()]
    provider = _marked([APIConnectionError(), APIConnectionError()])
    with pytest.raises(fo.FailoverExhaustedError) as excinfo:
        _run(provider)
    assert len(excinfo.value.attempts) == 3


def test_hop_construction_failure_is_explicit(monkeypatch):

    def _boom(name):
        raise ValueError("GEMINI_API_KEY not configured")
    monkeypatch.setattr(llm_pkg, "get_provider", _boom)
    provider = _marked([APITimeoutError()])
    with pytest.raises(fo.FailoverExhaustedError) as excinfo:
        _run(provider)
    assert excinfo.value.attempts[-1]["outcome_class"] == "hop_construction_failed"


# ---------------------------------------------------------------------------
# Bounded execution + cancellation (D-88-4, B-90-4)
# ---------------------------------------------------------------------------

def test_per_attempt_timeout_fires_and_hops(monkeypatch, gemini_backup):
    monkeypatch.setenv(fo.ATTEMPT_TIMEOUT_ENV, "0.05")
    provider = fo.mark_hosted_failover(HangingProvider([]), "Z", "groq", "gemini")
    response = _run(provider)
    assert gemini_backup.calls == 1
    assert response["_provider_attempts"][0]["outcome_class"] == "attempt_timeout"


def test_total_deadline_exhaustion(monkeypatch):
    monkeypatch.setenv(fo.TOTAL_DEADLINE_ENV, "-1")  # already expired
    provider = _marked([_ok()])
    with pytest.raises(fo.FailoverExhaustedError) as excinfo:
        _run(provider)
    assert "deadline" in str(excinfo.value)
    assert provider.calls == 0


def test_cancellation_propagates():
    provider = fo.mark_hosted_failover(HangingProvider([]), "Z", "groq", "gemini")

    async def _cancel_run():
        task = asyncio.ensure_future(fo.generate_with_failover(
            provider, prompt="p", output_schema={}, temperature=0.2,
            max_tokens=64))
        await asyncio.sleep(0.05)
        task.cancel()
        assert await _await_cancelled(task) is True
    asyncio.run(_cancel_run())


def test_cancellation_releases_half_open_probe():
    """B-90-4 regression: T reproduced half_open_allows_after_cancel=False.
    A cancelled probe attempt must release the permit so a later request can
    probe the half-open circuit."""
    opened = time.monotonic() - fo.CIRCUIT_COOLDOWN_S - 1
    for _ in range(fo.CIRCUIT_FAILURE_THRESHOLD):
        fo.record_provider_failure("groq", now=opened)
    assert fo._circuit_for("groq").state(time.monotonic()) == "half_open"

    provider = fo.mark_hosted_failover(HangingProvider([]), "Z", "groq", "gemini")

    async def _cancel_run():
        task = asyncio.ensure_future(fo.generate_with_failover(
            provider, prompt="p", output_schema={}, temperature=0.2,
            max_tokens=64))
        await asyncio.sleep(0.05)
        task.cancel()
        assert await _await_cancelled(task) is True
    asyncio.run(_cancel_run())
    allowed, probe = fo.acquire_slot("groq")
    assert allowed is True              # the permit was released, not stranded
    assert probe is True


def test_circuit_neutral_failure_releases_half_open_probe(monkeypatch):
    """A terminal failure during a half-open probe must not strand the
    permit either (it records no circuit outcome by design)."""
    monkeypatch.setattr(llm_pkg, "get_provider", lambda name: None)
    opened = time.monotonic() - fo.CIRCUIT_COOLDOWN_S - 1
    for _ in range(fo.CIRCUIT_FAILURE_THRESHOLD):
        fo.record_provider_failure("groq", now=opened)
    provider = _marked([AuthenticationError()])
    with pytest.raises(fo.FailoverTerminalError):
        _run(provider)
    allowed, _ = fo.acquire_slot("groq")
    assert allowed is True


# ---------------------------------------------------------------------------
# Cooldown circuit (D-88-4)
# ---------------------------------------------------------------------------

def test_circuit_opens_after_threshold_and_cools_down():
    for _ in range(fo.CIRCUIT_FAILURE_THRESHOLD):
        fo.record_provider_failure("groq", now=100.0)
    assert fo.circuit_allows("groq", now=101.0) is False          # open
    half_open_at = 100.0 + fo.CIRCUIT_COOLDOWN_S + 1
    assert fo.circuit_allows("groq", now=half_open_at) is True    # one probe
    assert fo.circuit_allows("groq", now=half_open_at) is False   # only one


def test_circuit_open_skips_doomed_primary(gemini_backup):
    for _ in range(fo.CIRCUIT_FAILURE_THRESHOLD):
        fo.record_provider_failure("groq")
    provider = _marked([_ok()])           # primary WOULD succeed, but is open
    response = _run(provider)
    assert provider.calls == 0
    assert gemini_backup.calls == 1
    assert response["_failover_occurred"] is True


def test_circuit_success_closes():
    for _ in range(fo.CIRCUIT_FAILURE_THRESHOLD):
        fo.record_provider_failure("groq", now=100.0)
    fo.record_provider_success("groq")
    assert fo.circuit_allows("groq", now=101.0) is True
    assert fo.circuit_snapshot()["groq"] == "closed"


def test_circuit_snapshot_is_aggregate_only():
    fo.record_provider_failure("groq")
    snapshot = fo.circuit_snapshot()
    assert set(snapshot) == {"groq"}
    assert snapshot["groq"] in ("closed", "open", "half_open")


# ---------------------------------------------------------------------------
# Backup admission bulkhead (B-90-5, per-process)
# ---------------------------------------------------------------------------

def test_backup_admission_rejects_at_limit(gemini_backup):
    for _ in range(fo.DEFAULT_BACKUP_ADMISSION_LIMIT):
        assert fo.admit_backup("gemini") is True     # saturate the bulkhead
    provider = _marked([APITimeoutError()])
    with pytest.raises(fo.FailoverExhaustedError) as excinfo:
        _run(provider)
    assert excinfo.value.attempts[-1]["outcome_class"] == "backup_admission_rejected"
    assert gemini_backup.calls == 0


def test_backup_admission_released_after_attempt(gemini_backup):
    provider = _marked([APITimeoutError()])
    _run(provider)                        # hop succeeds
    assert fo.admission_snapshot() == {}  # nothing held after completion


def test_backup_admission_released_on_backup_failure(gemini_backup):
    gemini_backup._script = [InternalServerError()]
    provider = _marked([APITimeoutError()])
    with pytest.raises(fo.FailoverExhaustedError):
        _run(provider)
    assert fo.admission_snapshot() == {}


def test_admission_scope_is_labeled_per_process():
    assert fo.ADMISSION_SCOPE == "per-process"


# ---------------------------------------------------------------------------
# Evidence semantics (B-90-7): fail-closed enablement
# ---------------------------------------------------------------------------

def test_flag_without_evidence_stays_disabled(monkeypatch):
    """B-90-7 regression: T reproduced runtime env true while surfaces
    disagreed. The flag alone must never enable."""
    monkeypatch.delenv(fo.EVIDENCE_TESTED_ENV, raising=False)
    monkeypatch.delenv(fo.EVIDENCE_BUILD_ENV, raising=False)
    assert fo.runtime_failover_enabled() is False
    provider = _marked([_ok()])
    response = _run(provider)
    assert "_provider_attempts" not in response   # dark path — fail closed


def test_malformed_evidence_timestamp_stays_disabled(monkeypatch):
    monkeypatch.setenv(fo.EVIDENCE_TESTED_ENV, "soon")
    assert fo.runtime_failover_enabled() is False


def test_evidence_without_build_stays_disabled(monkeypatch):
    monkeypatch.delenv(fo.EVIDENCE_BUILD_ENV, raising=False)
    assert fo.runtime_failover_enabled() is False


def test_full_evidence_tuple_enables():
    assert fo.evidence_state()["valid"] is True
    assert fo.runtime_failover_enabled() is True


def test_contract_flips_live_with_the_flag(monkeypatch):
    from verifimind_mcp.contract import get_public_contract
    on = get_public_contract()
    assert on["runtime_failover_enabled"] is True
    assert "bounded runtime failover" in on["fallback_semantics"]
    assert on["free_tier_routing"]["Z"]["runtime_hop_chain"] == ["gemini"]
    assert on["free_tier_routing"]["X"]["runtime_hop_chain"] == []

    monkeypatch.setenv(fo.ENABLE_ENV, "")
    off = get_public_contract()
    assert off["runtime_failover_enabled"] is False
    assert "does not fail over" in off["fallback_semantics"]


def test_health_failover_block_carries_validated_evidence(monkeypatch, _failover_env):
    import http_server

    lit = json.loads(asyncio.run(http_server.health_handler(None)).body)
    assert lit["runtime_failover_enabled"] is True
    assert lit["features"]["runtime_failover"] is True
    assert lit["failover"]["failover_contract_tested_at"] == _failover_env
    assert lit["failover"]["build"] == EVIDENCE_BUILD
    assert lit["failover"]["admission_scope"] == "per-process"
    assert isinstance(lit["failover"]["circuit"], dict)

    monkeypatch.setenv(fo.ENABLE_ENV, "")
    dark = json.loads(asyncio.run(http_server.health_handler(None)).body)
    assert dark["runtime_failover_enabled"] is False
    assert "failover" not in dark


def test_mcp_config_projects_the_live_flag(monkeypatch):
    """B-90-7 regression: T reproduced MCP config reporting false while the
    runtime env was true. The features block now reads the contract."""
    import http_server

    class _URL:
        scheme = "https"
        netloc = "verifimind.ysenseai.org"

    class _Req:
        headers = {"host": "verifimind.ysenseai.org"}
        url = _URL()

    lit = json.loads(asyncio.run(http_server.mcp_config_handler(_Req())).body)
    assert lit["mcpServers"]["verifimind-genesis"]["features"]["runtime_failover"] is True

    monkeypatch.setenv(fo.ENABLE_ENV, "")
    dark = json.loads(asyncio.run(http_server.mcp_config_handler(_Req())).body)
    assert dark["mcpServers"]["verifimind-genesis"]["features"]["runtime_failover"] is False


# ---------------------------------------------------------------------------
# MCP boundary contract (B-90-8)
# ---------------------------------------------------------------------------

def test_failover_error_payload_exhausted_contract():
    exc = fo.FailoverExhaustedError(
        "hop budget exhausted",
        [{"provider": "groq", "model": "groq/test-model",
          "outcome_class": "server_error", "duration_ms": 20},
         {"provider": "gemini", "model": "gemini/backup-model",
          "outcome_class": "server_error", "duration_ms": 30}],
        "server_error", "abcd1234",
        final_provider="gemini", hop_executed=True)
    payload = failover_error_payload(exc, "Trinity", "TestConcept")
    assert payload["error_code"] == "FAILOVER_EXHAUSTED"
    assert payload["attempt_count"] == 2
    assert payload["final_reason_class"] == "server_error"
    assert payload["_failover_occurred"] is True
    assert payload["final_provider"] == "gemini"
    assert payload["_failover_correlation"] == "abcd1234"
    assert payload["_inference_quality"] == "unavailable"
    assert payload["concept"] == "TestConcept"


def test_failover_error_payload_never_infers_failover_from_trail():
    """B-92-1 regression (T's probe): a proposed-but-REJECTED hop leaves two
    provider names in the trail, but the payload must carry the executor's
    explicit truth — no failover, no backup provider."""
    exc = fo.FailoverExhaustedError(
        "backup gemini admission limit reached",
        [{"provider": "groq", "model": "groq/test-model",
          "outcome_class": "attempt_timeout", "duration_ms": 30},
         {"provider": "gemini", "model": "gemini",
          "outcome_class": "backup_admission_rejected", "duration_ms": 0}],
        "backup_admission_rejected", "feed4321",
        final_provider="groq", hop_executed=False)
    payload = failover_error_payload(exc, "Z")
    assert payload["final_reason_class"] == "backup_admission_rejected"
    assert payload["_failover_occurred"] is False   # trail has 2 names — irrelevant
    assert payload["final_provider"] == "groq"      # the one that actually ran


def test_failover_error_payload_terminal_distinct_from_byok():
    exc = fo.FailoverTerminalError(
        "hosted provider groq terminal failure (auth_or_config)",
        [{"provider": "groq", "model": "groq/test-model",
          "outcome_class": "auth_or_config", "duration_ms": 10}],
        "auth_or_config", "beef5678",
        final_provider="groq", hop_executed=False)
    payload = failover_error_payload(exc, "Z")
    assert payload["error_code"] == "HOSTED_PROVIDER_TERMINAL"
    assert payload["error_code"] != "BYOK_AUTH_FAILED"
    assert payload["_failover_occurred"] is False
    assert payload["final_reason_class"] == "auth_or_config"


def test_error_payload_carries_no_prompt_content():
    exc = fo.FailoverExhaustedError("x", [{"provider": "groq", "model": "m",
                                        "outcome_class": "server_error",
                                        "duration_ms": 1}],
                                 "server_error", "cafe0000")
    secret = "TOP-SECRET-CONCEPT-TEXT"
    payload = failover_error_payload(exc, "Z")
    assert secret not in json.dumps(payload)


# ---------------------------------------------------------------------------
# Quality / veto / synthesis invariants after a hop (B-90-9)
# ---------------------------------------------------------------------------

class _XStub:
    innovation_score = 8.0
    strategic_value = 8.0


class _ZStub:
    def __init__(self, ethics_score=8.0, veto=False):
        self.ethics_score = ethics_score
        self.veto_triggered = veto


class _CSStub:
    security_score = 8.0


def test_hop_never_upgrades_inference_quality(gemini_backup):
    gemini_backup._script = [_ok(quality="fallback")]
    provider = _marked([APITimeoutError()])
    response = _run(provider)
    assert response["_inference_quality"] == "fallback"   # degraded stays degraded


def test_degraded_hop_quality_still_caps_synthesis_at_revise(gemini_backup):
    """B-90-9: the degraded-cap consumers read the hop's TRUE final quality —
    a hopped consultation that landed degraded cannot auto-clear a concept."""
    from verifimind_mcp.utils.synthesis import (
        calculate_overall_score, determine_recommendation,
    )
    gemini_backup._script = [_ok(quality="fallback")]
    provider = _marked([APITimeoutError()])
    z_quality = _run(provider)["_inference_quality"]
    assert z_quality == "fallback"

    score = calculate_overall_score(_XStub(), _ZStub(), _CSStub(), z_quality)
    assert score <= 4.0                                    # degraded cap holds
    assert determine_recommendation(score, _ZStub(), _CSStub(), z_quality) == "revise"


def test_z_veto_preserved_after_hop(gemini_backup):
    """B-90-9: a veto carried by a hopped-to provider's output still rejects
    and still caps the score at 3.0 — failover never dilutes the veto."""
    from verifimind_mcp.utils.synthesis import (
        calculate_overall_score, determine_recommendation,
    )
    gemini_backup._script = [_ok(quality="real")]
    provider = _marked([APITimeoutError()])
    z_quality = _run(provider)["_inference_quality"]

    veto_z = _ZStub(ethics_score=2.0, veto=True)
    score = calculate_overall_score(_XStub(), veto_z, _CSStub(), z_quality)
    assert score <= 3.0                                    # veto cap holds
    assert determine_recommendation(score, veto_z, _CSStub(), z_quality) == "reject"


def test_telemetry_is_privacy_minimal(gemini_backup):
    provider = _marked([InternalServerError(), InternalServerError()])
    response = _run(provider)
    for attempt in response["_provider_attempts"]:
        assert set(attempt) == {"provider", "model", "outcome_class", "duration_ms"}


def test_terminal_error_carries_no_prompt_content():
    provider = _marked([AuthenticationError()])
    secret_prompt = "TOP-SECRET-CONCEPT-TEXT"
    with pytest.raises(fo.FailoverTerminalError) as excinfo:
        _run(provider, prompt=secret_prompt)
    assert secret_prompt not in repr(excinfo.value)
    assert secret_prompt not in repr(excinfo.value.attempts)


# ---------------------------------------------------------------------------
# B-92-1: explicit terminal truth — the payload carries what ACTUALLY happened
# ---------------------------------------------------------------------------

def test_admission_rejected_terminal_truth(gemini_backup):
    """T's S92 probe, permanent: saturated admission => the terminal reason is
    the rejection (not the preceding timeout), no failover is reported, and
    the final provider is the one that actually ran inference."""
    for _ in range(fo.DEFAULT_BACKUP_ADMISSION_LIMIT):
        assert fo.admit_backup("gemini") is True
    provider = _marked([APITimeoutError()])
    with pytest.raises(fo.FailoverExhaustedError) as excinfo:
        _run(provider)
    exc = excinfo.value
    assert exc.final_reason_class == "backup_admission_rejected"
    assert exc.final_provider == "groq"
    assert exc.hop_executed is False
    assert exc.attempts[-1]["outcome_class"] == "backup_admission_rejected"
    assert gemini_backup.calls == 0     # backup inference never executed


def test_hop_target_circuit_skip_terminal_truth(gemini_backup):
    for _ in range(fo.CIRCUIT_FAILURE_THRESHOLD):
        fo.record_provider_failure("gemini")
    provider = _marked([APITimeoutError()])
    with pytest.raises(fo.FailoverExhaustedError) as excinfo:
        _run(provider)
    exc = excinfo.value
    assert exc.final_reason_class == "hop_target_circuit_open"
    assert exc.final_provider == "groq"
    assert exc.hop_executed is False
    assert gemini_backup.calls == 0


def test_construction_failure_terminal_truth(monkeypatch):

    def _boom(name):
        raise ValueError("GEMINI_API_KEY not configured")
    monkeypatch.setattr(llm_pkg, "get_provider", _boom)
    provider = _marked([APITimeoutError()])
    with pytest.raises(fo.FailoverExhaustedError) as excinfo:
        _run(provider)
    exc = excinfo.value
    assert exc.final_reason_class == "hop_construction_failed"
    assert exc.final_provider == "groq"
    assert exc.hop_executed is False


def test_deadline_terminal_truth(monkeypatch):
    monkeypatch.setenv(fo.TOTAL_DEADLINE_ENV, "-1")
    provider = _marked([_ok()])
    with pytest.raises(fo.FailoverExhaustedError) as excinfo:
        _run(provider)
    exc = excinfo.value
    assert exc.final_reason_class == "total_deadline_exhausted"
    assert exc.final_provider is None   # no inference attempt ever ran
    assert exc.hop_executed is False


def test_executed_hop_reports_true_final_provider(gemini_backup):
    gemini_backup._script = [InternalServerError()]
    provider = _marked([APITimeoutError()])
    with pytest.raises(fo.FailoverExhaustedError) as excinfo:
        _run(provider)
    exc = excinfo.value
    assert exc.hop_executed is True            # backup inference DID run
    assert exc.final_provider == "gemini"
    assert exc.final_reason_class == "server_error"


# ---------------------------------------------------------------------------
# B-92-2: evidence validation is genuinely fail-closed
# ---------------------------------------------------------------------------

def test_evidence_rejects_date_only(monkeypatch):
    """T's S92 probe: FAILOVER_CONTRACT_TESTED_AT=2026-07-25 must NOT validate."""
    monkeypatch.setenv(fo.EVIDENCE_TESTED_ENV, "2026-07-25")
    assert fo.evidence_state()["valid"] is False
    assert fo.runtime_failover_enabled() is False


def test_evidence_rejects_naive_timestamp(monkeypatch):
    monkeypatch.setenv(fo.EVIDENCE_TESTED_ENV, "2026-07-25T00:00:00")
    assert fo.evidence_state()["valid"] is False


def test_evidence_rejects_material_future_timestamp(monkeypatch):
    """T's S92 probe: 2999-01-01T00:00:00Z must NOT validate (evidence cannot
    postdate reality beyond bounded clock skew)."""
    monkeypatch.setenv(fo.EVIDENCE_TESTED_ENV, "2999-01-01T00:00:00Z")
    assert fo.evidence_state()["valid"] is False


def test_evidence_allows_bounded_clock_skew(monkeypatch):
    near = (datetime.now(timezone.utc) + timedelta(seconds=60)).isoformat()
    monkeypatch.setenv(fo.EVIDENCE_TESTED_ENV, near)
    assert fo.evidence_state()["valid"] is True
    far = (datetime.now(timezone.utc)
           + timedelta(seconds=2 * fo.EVIDENCE_CLOCK_SKEW_S)).isoformat()
    monkeypatch.setenv(fo.EVIDENCE_TESTED_ENV, far)
    assert fo.evidence_state()["valid"] is False


def test_evidence_rejects_weak_build_identity(monkeypatch):
    """T's S92 probe: FAILOVER_EVIDENCE_BUILD=x must NOT validate."""
    monkeypatch.setenv(fo.EVIDENCE_BUILD_ENV, "x")
    assert fo.evidence_state()["valid"] is False
    assert fo.runtime_failover_enabled() is False


def _write_identity(monkeypatch, tmp_path, value):
    """Point the image-owned identity file at a fresh per-test value
    (None = the file is absent, as in an image built without the bake)."""
    identity_file = tmp_path / "identity_override"
    if value is None:
        monkeypatch.setattr(fo, "_BUILD_IDENTITY_FILE",
                            str(tmp_path / "missing_identity"))
        return
    identity_file.write_text(value, encoding="utf-8")
    monkeypatch.setattr(fo, "_BUILD_IDENTITY_FILE", str(identity_file))


def test_unrelated_sha_never_validates_against_live_revision(monkeypatch, tmp_path):
    """B-93-1 regression — T's S93 counterexample verbatim: a SHA-shaped but
    unrelated value ('deadbee') must NOT enable when the live revision names
    a different artifact and no image identity matches."""
    monkeypatch.setenv("K_REVISION", "verifimind-mcp-server-00484-qrt")
    _write_identity(monkeypatch, tmp_path, None)
    monkeypatch.setenv(fo.EVIDENCE_BUILD_ENV, "deadbee")
    assert fo.evidence_state()["valid"] is False
    assert fo.runtime_failover_enabled() is False


def test_sha_syntax_alone_never_validates(monkeypatch, tmp_path):
    """B-93-1: with NO binding source at all (no K_REVISION, no image
    identity file), a well-formed SHA identifies nothing and must fail."""
    _write_identity(monkeypatch, tmp_path, None)
    monkeypatch.setenv(fo.EVIDENCE_BUILD_ENV, "abc1234")
    assert fo.evidence_state()["valid"] is False
    assert fo.runtime_failover_enabled() is False


def test_sha_binds_only_to_image_owned_identity(monkeypatch, tmp_path):
    """The Cloud Run flip path: FAILOVER_EVIDENCE_BUILD must equal the
    identity the image itself carries — matching enables, any other fails."""
    _write_identity(monkeypatch, tmp_path, "9352f4cabc")
    monkeypatch.setenv(fo.EVIDENCE_BUILD_ENV, "9352f4cabc")
    assert fo.evidence_state()["valid"] is True
    monkeypatch.setenv(fo.EVIDENCE_BUILD_ENV, "deadbee")
    assert fo.evidence_state()["valid"] is False


def test_service_env_can_never_shadow_image_identity(monkeypatch, tmp_path):
    """B-95-1 regression — T's S95 reproduction: a PERSISTED service-level
    BUILD_COMMIT_SHA env var (inherited from artifact A across revisions)
    must be IGNORED — env vars are not a trust source. Only the image-owned
    file binds; with image B's file absent or different, A's evidence dies
    even though the stale env var still matches it."""
    monkeypatch.setenv("K_REVISION", "verifimind-mcp-server-00500-bbb")
    monkeypatch.setenv("BUILD_COMMIT_SHA", "aaaa111")   # stale service override
    monkeypatch.setenv(fo.EVIDENCE_BUILD_ENV, "aaaa111")
    _write_identity(monkeypatch, tmp_path, None)        # image B: no bake
    assert fo.evidence_state()["valid"] is False
    assert fo.runtime_failover_enabled() is False
    _write_identity(monkeypatch, tmp_path, "bbbb222")   # image B: own identity
    assert fo.evidence_state()["valid"] is False
    assert fo.runtime_failover_enabled() is False


def test_evidence_accepts_running_revision_binding(monkeypatch):
    monkeypatch.setenv("K_REVISION", "verifimind-mcp-server-00490-abc")
    monkeypatch.setenv(fo.EVIDENCE_BUILD_ENV, "verifimind-mcp-server-00490-abc")
    assert fo.evidence_state()["valid"] is True
    monkeypatch.setenv(fo.EVIDENCE_BUILD_ENV, "verifimind-mcp-server-00489-old")
    assert fo.evidence_state()["valid"] is False   # stale revision != running


# ---------------------------------------------------------------------------
# B-92-3: correlation survives to SUCCESSFUL MCP-facing payloads
# ---------------------------------------------------------------------------

def test_base_agent_lifts_correlation_end_to_end(gemini_backup):
    """Full stack: marked provider -> failover hop -> BaseAgent.analyze ->
    result carries attempts + correlation -> the payload writer exposes them.
    This asserts the actual MCP-facing success contract, not the executor."""
    from verifimind_mcp.agents.x_agent import XAgent
    from verifimind_mcp.models import Concept

    valid_x = {
        "reasoning_steps": [{"step_number": 1, "thought": "t"}],
        "innovation_score": 7.0, "strategic_value": 7.0,
        "opportunities": [], "risks": [], "recommendation": "proceed",
        "confidence": 0.8,
    }
    gemini_backup._script = [{"content": valid_x,
                              "usage": {"output_tokens": 5},
                              "_inference_quality": "real"}]
    provider = _marked([APITimeoutError()])
    agent = XAgent(llm_provider=provider)
    result = asyncio.run(agent.analyze(Concept(name="C", description="D")))

    assert result._failover_occurred is True
    assert len(result._failover_correlation) == 8
    payload = {}
    attach_failover_disclosure(payload, result)
    assert payload["_failover_correlation"] == result._failover_correlation
    assert payload["_failover_occurred"] is True
    assert payload["_provider_attempts"][-1]["provider"] == "gemini"


def test_trinity_meta_exposes_per_stage_correlations():

    class _Plain:
        pass

    class _Hopped:
        _provider_attempts = [
            {"provider": "groq", "model": "m",
             "outcome_class": "attempt_timeout", "duration_ms": 3},
            {"provider": "gemini", "model": "m2",
             "outcome_class": "success", "duration_ms": 9}]
        _failover_occurred = True
        _failover_correlation = "cafe1234"

    meta = trinity_failover_meta({"X": _Plain(), "Z": _Hopped(), "CS": _Plain()})
    assert set(meta["_provider_attempts"]) == {"Z"}
    assert meta["_failover_occurred"] is True
    assert meta["_failover_correlations"] == {"Z": "cafe1234"}
    assert trinity_failover_meta({"X": _Plain(), "Z": _Plain(), "CS": _Plain()}) == {}


# ---------------------------------------------------------------------------
# B-92-4: permanent concurrency + aggregate-budget evidence
# ---------------------------------------------------------------------------

class HangingBackup:
    """Backup that holds its admission slot until released — lets tests prove
    CONCURRENT bulkhead behavior deterministically."""

    def __init__(self, release):
        self._release = release
        self.calls = 0

    async def generate(self, **kwargs):
        self.calls += 1
        await self._release.wait()
        return _ok()

    def get_model_name(self):
        return "gemini/backup-model"


def test_concurrent_backup_admission_bulkhead(monkeypatch):
    """Executor-level (T B-92-4): four concurrent consultations hop; with
    limit 2, exactly two hold admission while two reject; released holders
    complete as genuine failover; nothing stays held."""
    monkeypatch.setenv(fo.ADMISSION_LIMIT_ENV, "2")

    async def scenario():
        release = asyncio.Event()
        backup = HangingBackup(release)
        monkeypatch.setattr(llm_pkg, "get_provider", lambda name: backup)

        async def one():
            return await fo.generate_with_failover(
                _marked([APITimeoutError()]), prompt="p", output_schema={},
                temperature=0.2, max_tokens=64)

        tasks = [asyncio.ensure_future(one()) for _ in range(4)]
        for _ in range(200):                      # bounded wait, no fixed sleep
            await asyncio.sleep(0.01)
            if sum(t.done() for t in tasks) >= 2 and backup.calls >= 2:
                break
        assert fo.admission_snapshot() == {"gemini": 2}   # exactly limit held
        rejected = [t.exception() for t in tasks if t.done()]
        assert len(rejected) == 2
        for exc in rejected:
            assert isinstance(exc, fo.FailoverExhaustedError)
            assert exc.final_reason_class == "backup_admission_rejected"
            assert exc.hop_executed is False
        release.set()
        results = await asyncio.gather(*[t for t in tasks if not t.done()])
        assert all(r["_failover_occurred"] is True for r in results)
        assert fo.admission_snapshot() == {}              # every hold returned
    asyncio.run(scenario())


def test_cancelled_admitted_backup_returns_hold(monkeypatch):

    async def scenario():
        release = asyncio.Event()
        backup = HangingBackup(release)
        monkeypatch.setattr(llm_pkg, "get_provider", lambda name: backup)
        task = asyncio.ensure_future(fo.generate_with_failover(
            _marked([APITimeoutError()]), prompt="p", output_schema={},
            temperature=0.2, max_tokens=64))
        for _ in range(200):
            await asyncio.sleep(0.01)
            if backup.calls == 1:
                break
        assert fo.admission_snapshot() == {"gemini": 1}   # admitted + in flight
        task.cancel()
        assert await _await_cancelled(task) is True
        assert fo.admission_snapshot() == {}              # hold returned on cancel
    asyncio.run(scenario())


def test_consultation_call_and_token_ceiling(gemini_backup):
    """The aggregate consultation budget, stated and enforced: at most
    MAX_ATTEMPTS inference calls, each bounded by the caller's max_tokens —
    the worst-case output-token ceiling is MAX_ATTEMPTS x max_tokens."""
    gemini_backup._script = [APIConnectionError()]
    provider = _marked([APIConnectionError(), APIConnectionError()])
    with pytest.raises(fo.FailoverExhaustedError):
        _run(provider)
    assert provider.calls + gemini_backup.calls == fo.MAX_ATTEMPTS
    for kwargs in provider.seen_kwargs + gemini_backup.seen_kwargs:
        assert kwargs["max_tokens"] == 64


# ---------------------------------------------------------------------------
# B-94-1: identity binds ACROSS deployment transitions — machine-checkable
# receipts that every live deploy path bakes the comparator INTO the image
# and never sets it at the service level (a service value would let artifact
# B inherit artifact A's evidence).
# ---------------------------------------------------------------------------

_MCP_SERVER_DIR = Path(__file__).resolve().parents[3]
_REPO_ROOT = _MCP_SERVER_DIR.parent


def test_artifact_b_cannot_inherit_artifact_a_evidence(monkeypatch, tmp_path):
    """B-94-1 regression — T's S94 counterexample: image A stamps evidence A
    and enables; a different artifact B must NOT stay enabled on A's
    evidence, whether B carries no identity file or its own different one."""
    _write_identity(monkeypatch, tmp_path, "aaaa111")     # image A, baked file
    monkeypatch.setenv(fo.EVIDENCE_BUILD_ENV, "aaaa111")  # operator stamped A
    assert fo.runtime_failover_enabled() is True          # artifact A: enabled

    # transition 1: image B built WITHOUT the bake (a non-conforming path) —
    # image-carried semantics mean the identity file VANISHES with the image
    _write_identity(monkeypatch, tmp_path, None)
    monkeypatch.setenv("K_REVISION", "verifimind-mcp-server-00500-bbb")
    assert fo.evidence_state()["valid"] is False
    assert fo.runtime_failover_enabled() is False         # stale evidence dies

    # transition 2: image B carries its OWN identity — A's evidence still dies
    _write_identity(monkeypatch, tmp_path, "bbbb222")
    assert fo.evidence_state()["valid"] is False
    assert fo.runtime_failover_enabled() is False


def test_dockerfiles_bake_immutable_identity():
    """Both production Dockerfiles must carry the ARG->ENV bake so the
    comparator travels with the image, never with the service."""
    for dockerfile in (_REPO_ROOT / "Dockerfile", _MCP_SERVER_DIR / "Dockerfile"):
        src = dockerfile.read_text(encoding="utf-8")
        assert "ARG COMMIT_SHA" in src, dockerfile
        # B-95-1: the identity is a FILE (service-unshadowable), never ENV
        assert '> /app/.build_commit_sha' in src, dockerfile
        assert "ENV BUILD_COMMIT_SHA" not in src, dockerfile


def test_trigger_pipeline_bakes_identity_and_never_service_sets_it():
    """Root cloudbuild.yaml (the trigger path): --build-arg present in the
    build step; BUILD_COMMIT_SHA absent from every service env-var flag."""
    src = (_REPO_ROOT / "cloudbuild.yaml").read_text(encoding="utf-8")
    assert "--build-arg" in src
    assert "COMMIT_SHA=$COMMIT_SHA" in src
    for line in src.splitlines():
        if "env-vars" in line or "BUILD_COMMIT_SHA=" in line:
            assert "BUILD_COMMIT_SHA=" not in line, (
                "service-level comparator reintroduces cross-deploy inheritance")


def test_manual_deploy_path_bakes_identity():
    """deploy-cloudrun.sh (the /verifimind-deploy path) must build via
    cloudbuild-image.yaml with the commit substitution — `gcloud builds
    submit --tag` cannot pass --build-arg, which was B-94-1's opening."""
    script = (_MCP_SERVER_DIR / "deploy-cloudrun.sh").read_text(encoding="utf-8")
    assert "cloudbuild-image.yaml" in script
    assert "_COMMIT_SHA=" in script
    assert "git rev-parse HEAD" in script
    config = (_MCP_SERVER_DIR / "cloudbuild-image.yaml").read_text(encoding="utf-8")
    assert "--build-arg" in config
    assert "COMMIT_SHA=$_COMMIT_SHA" in config
    for line in script.splitlines():
        if "BUILD_COMMIT_SHA=" in line and not line.strip().startswith("#"):
            raise AssertionError("deploy script must never service-set the comparator")


def test_manual_deploy_rejects_dirty_source():
    """B-95-2 receipt: `gcloud builds submit` uploads WORKING-DIRECTORY
    bytes while `git rev-parse HEAD` names the committed tree — the script
    must refuse dirty/untracked state and require origin/main parity BEFORE
    computing the identity label, so bytes B can never wear label A."""
    script = (_MCP_SERVER_DIR / "deploy-cloudrun.sh").read_text(encoding="utf-8")
    assert "git status --porcelain" in script
    assert "git fetch origin" in script
    assert "origin/main" in script
    # the guards must run BEFORE the build is submitted
    assert script.index("git status --porcelain") < script.index("cloudbuild-image.yaml")
    assert script.index("origin/main") < script.index("cloudbuild-image.yaml")


def test_legacy_deploy_path_hard_retired():
    """B-95-3 receipt: deploy-gcp.sh must be a fail-closed stub — no build,
    no push, no deploy commands; execution exits 1."""
    stub = (_MCP_SERVER_DIR / "deploy-gcp.sh").read_text(encoding="utf-8")
    assert "RETIREMENT-STUB-MARKER" in stub
    assert "exit 1" in stub
    for live_command in ("gcloud run deploy", "gcloud builds submit",
                         "docker build", "docker push"):
        assert live_command not in stub, f"retired stub still carries: {live_command}"


def test_deploy_surface_inventory_closed():
    """B-95-3 receipt: EVERY tracked executable/config surface capable of
    building or deploying verifimind-mcp-server is either an authorized
    attested path or a retirement stub — the inventory is machine-closed,
    not documented-by-convention."""
    import subprocess
    listing = subprocess.run(
        ["git", "ls-files"], cwd=str(_REPO_ROOT),
        capture_output=True, text=True, check=True).stdout.splitlines()
    authorized = {
        "cloudbuild.yaml",                    # trigger path (attested)
        "mcp-server/cloudbuild-image.yaml",   # manual build config (attested)
        "mcp-server/deploy-cloudrun.sh",      # manual path (guarded + attested)
    }
    retired_stubs = {"mcp-server/deploy-gcp.sh"}
    offenders = []
    for name in listing:
        if not name.endswith((".sh", ".yaml", ".yml")):
            continue  # executable/config surfaces only; prose cannot deploy
        try:
            text = (_REPO_ROOT / name).read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        deployish = ("gcloud run deploy" in text or "builds submit" in text
                     or "docker push" in text)
        if "verifimind-mcp-server" in text and deployish:
            if name in authorized:
                continue
            if name in retired_stubs:
                offenders.append(f"{name} (stub carries live commands)")
            else:
                offenders.append(name)
    assert offenders == [], f"unattested deploy surfaces: {offenders}"
