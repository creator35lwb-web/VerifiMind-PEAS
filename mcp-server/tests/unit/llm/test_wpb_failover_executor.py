"""
WP-B — FailoverExecutor deterministic failure injection (T S88 D-88-2..5)
=========================================================================

The runtime-failover contract, enforced with shaped fakes (no SDK, no
network): locality consent (BYOK/Ollama never enter, mock never a target),
the retry-vs-hop matrices, Retry-After handling, bounded budgets +
cancellation, cooldown circuit, quality/veto preservation, telemetry
redaction, and the dark-mode guarantee (flag off == byte-identical legacy
behavior). Design: Hub #81 (WP-B design v2); review basis:
.macp/reviews/20260723_T_wpA_exit_and_wpB_design_review.md.
"""

import asyncio

import pytest

from verifimind_mcp.llm import failover as fo
from verifimind_mcp.llm.failover import (
    FailoverExhaustedError,
    classify_failure,
    generate_with_failover,
    hosted_failover_agent,
    mark_hosted_failover,
    runtime_hop_chain,
)


# --- shaped fakes (duck-typed like the raw SDK exceptions) -------------------

class RateLimitError(Exception):
    def __init__(self, retry_after=None):
        super().__init__("rate limited")
        if retry_after is not None:
            self.retry_after = retry_after


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
    raise or a response dict to return."""

    def __init__(self, script, model_name="groq/test-model"):
        self._script = list(script)
        self._model_name = model_name
        self.calls = 0

    async def generate(self, **kwargs):
        await asyncio.sleep(0)
        self.calls += 1
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


@pytest.fixture(autouse=True)
def _failover_env(monkeypatch):
    """Every test starts flag-ON with clean circuits and fast budgets;
    dark-mode tests turn the flag off explicitly."""
    monkeypatch.setenv(fo.ENABLE_ENV, "true")
    monkeypatch.setenv(fo.ATTEMPT_TIMEOUT_ENV, "0.5")
    monkeypatch.setenv(fo.TOTAL_DEADLINE_ENV, "5")
    fo.reset_circuits()
    yield
    fo.reset_circuits()


@pytest.fixture
def gemini_backup(monkeypatch):
    """Route Z's hop target ('gemini') to a scripted fake."""
    backup = FakeProvider([_ok()], model_name="gemini/backup-model")

    def _fake_get_provider(name):
        assert name == "gemini"
        return backup
    import verifimind_mcp.llm as llm_pkg
    monkeypatch.setattr(llm_pkg, "get_provider", _fake_get_provider)
    return backup


def _marked(script, agent="Z", model_name="groq/test-model"):
    return mark_hosted_failover(FakeProvider(script, model_name), agent)


def _run(provider, **kwargs):
    return asyncio.run(generate_with_failover(
        provider, prompt="p", output_schema={}, temperature=0.2,
        max_tokens=64, **kwargs))


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
    import verifimind_mcp.llm as llm_pkg
    monkeypatch.setattr(llm_pkg, "get_provider",
                        lambda name: hop_calls.append(name))
    provider = FakeProvider([AuthenticationError()])  # NOT marked
    with pytest.raises(AuthenticationError):
        _run(provider)
    assert hop_calls == []


def test_unmarked_ollama_stays_local(monkeypatch):
    hop_calls = []
    import verifimind_mcp.llm as llm_pkg
    monkeypatch.setattr(llm_pkg, "get_provider",
                        lambda name: hop_calls.append(name))
    provider = FakeProvider([APIConnectionError()],
                            model_name="ollama/llama3.2")  # NOT marked
    with pytest.raises(APIConnectionError):
        _run(provider)
    assert hop_calls == []


def test_hosted_resolution_marks_and_session_byok_does_not(monkeypatch):
    """config_helper wiring: hosted env-key branch marks; session BYOK not."""
    for key in ("GROQ_API_KEY", "GEMINI_API_KEY", "ANTHROPIC_API_KEY",
                "X_AGENT_PROVIDER", "Z_AGENT_PROVIDER"):
        monkeypatch.delenv(key, raising=False)
    monkeypatch.setenv("GROQ_API_KEY", "gsk_hosted")
    from verifimind_mcp.config_helper import get_agent_provider
    hosted = get_agent_provider("Z")
    assert hosted_failover_agent(hosted) == "Z"

    class Cfg:
        llm_provider = "groq"
        groq_api_key = "gsk_byok_user"

    class Ctx:
        session_config = Cfg()

    byok = get_agent_provider("Z", Ctx())
    assert hosted_failover_agent(byok) is None


def test_mock_is_never_a_hop_target():
    assert runtime_hop_chain("X") == []       # X's fallback is mock => no hop
    assert runtime_hop_chain("Z") == ["gemini"]
    assert runtime_hop_chain("CS") == ["gemini"]


def test_no_silent_mock_on_exhaustion():
    """Agent X (no hop target): a hop-class failure surfaces an explicit
    error — never a synthetic response."""
    provider = _marked([APITimeoutError()], agent="X",
                       model_name="gemini/gemini-3.5-flash-lite")
    with pytest.raises(FailoverExhaustedError) as excinfo:
        _run(provider)
    assert excinfo.value.error_code == "FAILOVER_EXHAUSTED"
    assert excinfo.value.attempts[0]["outcome_class"] == "attempt_timeout"


# ---------------------------------------------------------------------------
# Failure-class policy (D-88-2)
# ---------------------------------------------------------------------------

def test_classify_auth_is_terminal():
    assert classify_failure(AuthenticationError()).action == fo.TERMINAL


def test_classify_invalid_request_is_terminal():
    assert classify_failure(BadRequestError()).action == fo.TERMINAL


def test_classify_429_carries_retry_after():
    decision = classify_failure(RateLimitError(retry_after=7))
    assert decision.action == fo.RETRY
    assert decision.retry_after == pytest.approx(7.0)


def test_classify_timeout_hops():
    assert classify_failure(APITimeoutError()).action == fo.HOP


def test_classify_unknown_is_terminal_conservative():
    assert classify_failure(ValueError("weird")).action == fo.TERMINAL


def test_terminal_failure_raises_original_no_hop(gemini_backup):
    provider = _marked([AuthenticationError()])
    with pytest.raises(AuthenticationError):
        _run(provider)
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
# Retry / hop execution paths
# ---------------------------------------------------------------------------

def test_primary_success_no_failover_machinery(gemini_backup):
    provider = _marked([_ok()])
    response = _run(provider)
    assert response["_failover_occurred"] is False
    assert [a["outcome_class"] for a in response["_provider_attempts"]] == ["success"]
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
    with pytest.raises(FailoverExhaustedError) as excinfo:
        _run(provider)
    assert [a["provider"] for a in excinfo.value.attempts] == ["groq", "gemini"]


def test_attempt_cap_is_three(gemini_backup):
    gemini_backup._script = [APIConnectionError()]
    provider = _marked([APIConnectionError(), APIConnectionError()])
    with pytest.raises(FailoverExhaustedError) as excinfo:
        _run(provider)
    assert len(excinfo.value.attempts) == 3


def test_hop_construction_failure_is_explicit(monkeypatch):
    import verifimind_mcp.llm as llm_pkg

    def _boom(name):
        raise ValueError("GEMINI_API_KEY not configured")
    monkeypatch.setattr(llm_pkg, "get_provider", _boom)
    provider = _marked([APITimeoutError()])
    with pytest.raises(FailoverExhaustedError) as excinfo:
        _run(provider)
    assert excinfo.value.attempts[-1]["outcome_class"] == "hop_construction_failed"


# ---------------------------------------------------------------------------
# Bounded execution + cancellation (D-88-4)
# ---------------------------------------------------------------------------

def test_per_attempt_timeout_fires_and_hops(monkeypatch, gemini_backup):
    monkeypatch.setenv(fo.ATTEMPT_TIMEOUT_ENV, "0.05")
    provider = mark_hosted_failover(HangingProvider([]), "Z")
    response = _run(provider)
    assert gemini_backup.calls == 1
    assert response["_provider_attempts"][0]["outcome_class"] == "attempt_timeout"


def test_total_deadline_exhaustion(monkeypatch):
    monkeypatch.setenv(fo.TOTAL_DEADLINE_ENV, "-1")  # already expired
    provider = _marked([_ok()])
    with pytest.raises(FailoverExhaustedError) as excinfo:
        _run(provider)
    assert "deadline" in str(excinfo.value)
    assert provider.calls == 0


def test_cancellation_propagates():
    provider = mark_hosted_failover(HangingProvider([]), "Z")

    async def _cancel_run():
        task = asyncio.ensure_future(generate_with_failover(
            provider, prompt="p", output_schema={}, temperature=0.2,
            max_tokens=64))
        await asyncio.sleep(0.05)
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task
    asyncio.run(_cancel_run())


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
# Quality / veto preservation + telemetry contract (D-88-2 g6)
# ---------------------------------------------------------------------------

def test_hop_never_upgrades_inference_quality(gemini_backup):
    gemini_backup._script = [_ok(quality="fallback")]
    provider = _marked([APITimeoutError()])
    response = _run(provider)
    assert response["_inference_quality"] == "fallback"   # degraded stays degraded


def test_telemetry_is_privacy_minimal(gemini_backup):
    provider = _marked([InternalServerError(), InternalServerError()])
    response = _run(provider)
    for attempt in response["_provider_attempts"]:
        assert set(attempt) == {"provider", "model", "outcome_class", "duration_ms"}


def test_exhaustion_error_carries_no_prompt_content():
    provider = _marked([AuthenticationError()], agent="X")
    secret_prompt = "TOP-SECRET-CONCEPT-TEXT"
    with pytest.raises(Exception) as excinfo:
        asyncio.run(generate_with_failover(
            provider, prompt=secret_prompt, output_schema={},
            temperature=0.2, max_tokens=64))
    assert secret_prompt not in repr(excinfo.value)


# ---------------------------------------------------------------------------
# Surface projection (D-88-5): contract + /health + payload helpers
# ---------------------------------------------------------------------------

def test_contract_flips_live_with_the_flag(monkeypatch):
    from verifimind_mcp.contract import get_public_contract
    monkeypatch.setenv(fo.ENABLE_ENV, "")
    off = get_public_contract()
    assert off["runtime_failover_enabled"] is False
    assert "does not fail over" in off["fallback_semantics"]
    assert off["free_tier_routing"]["Z"]["runtime_hop_chain"] == ["gemini"]
    assert off["free_tier_routing"]["X"]["runtime_hop_chain"] == []

    monkeypatch.setenv(fo.ENABLE_ENV, "true")
    on = get_public_contract()
    assert on["runtime_failover_enabled"] is True
    assert "bounded runtime failover" in on["fallback_semantics"]


def test_health_failover_block_only_when_enabled(monkeypatch):
    import http_server
    import json

    monkeypatch.setenv(fo.ENABLE_ENV, "")
    dark = json.loads(asyncio.run(http_server.health_handler(None)).body)
    assert dark["runtime_failover_enabled"] is False
    assert "failover" not in dark

    monkeypatch.setenv(fo.ENABLE_ENV, "true")
    monkeypatch.setenv("FAILOVER_CONTRACT_TESTED_AT", "2026-07-24T00:00:00Z@abc1234")
    lit = json.loads(asyncio.run(http_server.health_handler(None)).body)
    assert lit["runtime_failover_enabled"] is True
    assert lit["features"]["runtime_failover"] is True
    assert lit["failover"]["failover_contract_tested_at"].startswith("2026-07-24")
    assert isinstance(lit["failover"]["circuit"], dict)


def test_payload_helpers_disclose_actual_provider():
    from verifimind_mcp.server import actual_provider_used, attach_failover_disclosure

    class _Result:
        _provider_attempts = [
            {"provider": "groq", "model": "groq/test-model",
             "outcome_class": "attempt_timeout", "duration_ms": 30},
            {"provider": "gemini", "model": "gemini/backup-model",
             "outcome_class": "success", "duration_ms": 900},
        ]
        _failover_occurred = True

    class _Primary:
        def get_model_name(self):
            return "groq/test-model"

    assert actual_provider_used(_Result(), _Primary()) == "gemini/backup-model"
    payload = {}
    attach_failover_disclosure(payload, _Result())
    assert payload["_failover_occurred"] is True

    class _Plain:
        pass
    assert actual_provider_used(_Plain(), _Primary()) == "groq/test-model"
    plain_payload = {}
    attach_failover_disclosure(plain_payload, _Plain())
    assert plain_payload == {}   # absent on the normal path — strictly additive
