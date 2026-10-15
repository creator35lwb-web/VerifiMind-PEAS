"""Z-B1a completion diagnostics — the offline acceptance matrix.

Contract: private Hub `.macp/briefs/20260924_T_to_RNA_z_b1a_observability_contract.md`
(T S185) with RNA's one bounded correction (the envelope rides on EVERY stage
carrier, standalone CS included). Baseline: public main
9d87787cca40bd1c16a428e0d1ff2e96d657b6e4, whose runtime subtree is v0.5.64's.
The implementation head is bound by the hosted checks at that exact SHA.

Nothing here calls a live provider. Every Groq path runs the production
`GroqProvider.generate` body against a fake SDK transport; every server path
runs the registered tool bodies in-process through fastmcp.

Discriminating controls: each positive assertion has a sibling that must fail
(a different value, a missing field, a rejected type), so a check that examined
nothing cannot pass.
"""

import json
import logging
import math
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest

from verifimind_mcp import config_helper, server
from verifimind_mcp.agents import CSAgent, XAgent, ZAgent
from verifimind_mcp.llm.provider import (
    COMPLETION_DIAGNOSTICS_ATTR,
    GROQ_8K_TPM_COMPLETION_CAP,
    GroqProvider,
    completion_diagnostics_snapshot,
)
from verifimind_mcp.models.concepts import Concept
from verifimind_mcp.models.reasoning import (
    CSAgentAnalysis,
    ReasoningStep,
    XAgentAnalysis,
    ZAgentAnalysis,
)
from verifimind_mcp.utils import trinity_retry
from verifimind_mcp.utils.completion_diagnostics import (
    COMPLETION_DIAGNOSTICS_NOTE,
    COMPLETION_DIAGNOSTICS_SCOPE,
    completion_diagnostics_envelope,
    snapshot_from_exception,
)
from verifimind_mcp.utils.token_monitor import (
    check_cs_agent_response,
    check_z_agent_response,
    unavailable_agent_token_monitor,
)
from verifimind_mcp.utils.trinity_retry import (
    TrinityRetryBudget,
    analyze_with_completion_retry,
)

from .mcp_tool_harness import call

GROQ_MODEL = "openai/gpt-oss-120b"
REASONING_SENTINEL = "SENTINEL-HIDDEN-REASONING-TEXT-9f1c"
PROMPT_SENTINEL = "SENTINEL-PROMPT-TEXT-4b7e"
ENVELOPE_KEYS = {
    "provider", "model", "status", "sent_reservation", "completion_tokens",
    "reasoning_tokens", "reasoning_share", "scope", "note",
}
REQUEST_KEYS = {"model", "messages", "temperature", "max_tokens"}


# ---------------------------------------------------------------- fakes
def _usage(completion=None, reasoning="absent", prompt=10):
    """A usage object. reasoning='absent' -> no details attribute at all."""
    total = prompt + completion if isinstance(completion, int) and not isinstance(completion, bool) else None
    usage = SimpleNamespace(prompt_tokens=prompt, completion_tokens=completion, total_tokens=total)
    if reasoning != "absent":
        usage.completion_tokens_details = (
            None if reasoning is None else SimpleNamespace(reasoning_tokens=reasoning)
        )
    return usage


def _response(text='{"ok": true}', usage="default", finish_reason="stop", reasoning_text=None):
    message = SimpleNamespace(content=text)
    if reasoning_text is not None:
        message.reasoning = reasoning_text
    response = SimpleNamespace(choices=[SimpleNamespace(message=message, finish_reason=finish_reason)])
    if usage != "omit":
        response.usage = _usage(42, 7) if usage == "default" else usage
    return response


class _FakeGroqError(Exception):
    """Mimics the SDK error surface: `.body` dict and `.response.headers`."""

    def __init__(self, code=None, message="", limit_header=None, status_code=413):
        super().__init__(message)
        self.status_code = status_code
        self.body = {"error": {"code": code, "message": message, "type": "tokens"}}
        headers = {}
        if limit_header is not None:
            headers["x-ratelimit-limit-tokens"] = limit_header
        self.response = type("R", (), {"status_code": status_code, "headers": headers})()


def _tpm_error(requested, limit=8000):
    return _FakeGroqError(
        code="rate_limit_exceeded",
        message=(f"Request too large for model `{GROQ_MODEL}` in organization `org_x` "
                 f"service tier `on_demand` on tokens per minute (TPM): Limit {limit}, "
                 f"Requested {requested}, please reduce your message size and try again."),
        limit_header=str(limit),
    )


class _ImmutableError(Exception):
    """An exception type that refuses new attributes (a third-party contract we must not break)."""

    def __setattr__(self, name, value):
        raise TypeError(f"immutable exception: cannot set {name}")


class _RaisingUsage:
    """A usage object whose attribute access raises — must read as 'not reported'."""

    def __getattr__(self, name):
        if name.startswith("__"):
            raise AttributeError(name)  # dunder lookups (pytest ids, repr) stay ordinary
        raise RuntimeError("usage access exploded")


def _groq(monkeypatch, side_effect):
    monkeypatch.setenv("GROQ_API_KEY", "gsk_test")
    provider = GroqProvider(model=GROQ_MODEL)
    provider.client = MagicMock()
    calls = []

    async def fake_create(**kwargs):
        calls.append(dict(kwargs))
        outcome = side_effect[len(calls) - 1] if isinstance(side_effect, list) else side_effect
        if isinstance(outcome, BaseException):
            raise outcome
        return outcome

    provider.client.chat.completions.create = AsyncMock(side_effect=fake_create)
    return provider, calls


def _steps():
    return [ReasoningStep(step_number=1, thought="bounded reasoning", confidence=0.9)]


def _results():
    x = XAgentAnalysis(reasoning_steps=_steps(), innovation_score=8.8, strategic_value=8.4,
                       opportunities=["o"], risks=["r"], recommendation="Proceed.", confidence=0.9)
    z = ZAgentAnalysis(reasoning_steps=_steps(), ethics_score=8.6, z_protocol_compliance=True,
                       ethical_concerns=["c"], mitigation_measures=["m"], recommendation="Proceed.",
                       veto_triggered=False, confidence=0.9)
    cs = CSAgentAnalysis(reasoning_steps=_steps(), security_score=8.2, vulnerabilities=["v"],
                         attack_vectors=["a"], security_recommendations=["s"], socratic_questions=["q"],
                         recommendation="Proceed.", confidence=0.9)
    for r in (x, z, cs):
        r._inference_quality = "real"
    return x, z, cs


def _snapshot(completion=3395, reasoning=1000, reservation=3395, status="reported"):
    return completion_diagnostics_snapshot(
        provider="groq", model=GROQ_MODEL, sent_reservation=reservation,
        usage=_usage(completion, reasoning), status=status,
    )


class _NamedProvider:
    def __init__(self, name):
        self.name = name

    def get_model_name(self):
        return self.name


# ---------------------------------------------------------------- 1. the snapshot builder
@pytest.mark.parametrize("usage, expected", [
    (_usage(3395, 1000), {"completion_tokens": 3395, "reasoning_tokens": 1000, "reasoning_share": round(1000 / 3395, 4)}),
    (_usage(3395), {"completion_tokens": 3395, "reasoning_tokens": None, "reasoning_share": None}),          # no details attr
    (_usage(3395, None), {"completion_tokens": 3395, "reasoning_tokens": None, "reasoning_share": None}),    # details None
    (_usage(3395, True), {"completion_tokens": 3395, "reasoning_tokens": None, "reasoning_share": None}),    # bool rejected
    (_usage(3395, "1000"), {"completion_tokens": 3395, "reasoning_tokens": None, "reasoning_share": None}),  # string rejected
    (_usage(3395, -1), {"completion_tokens": 3395, "reasoning_tokens": None, "reasoning_share": None}),      # negative rejected
    (_usage(3395, math.nan), {"completion_tokens": 3395, "reasoning_tokens": None, "reasoning_share": None}),  # non-finite rejected
    (_usage(3395, 12.0), {"completion_tokens": 3395, "reasoning_tokens": None, "reasoning_share": None}),    # float rejected
    (_usage(0, 0), {"completion_tokens": 0, "reasoning_tokens": 0, "reasoning_share": None}),                # valid zero, no ratio
    (_usage(100, 150), {"completion_tokens": 100, "reasoning_tokens": 150, "reasoning_share": None}),        # reasoning > completion: reported, no ratio
    (_usage("many", 5), {"completion_tokens": None, "reasoning_tokens": 5, "reasoning_share": None}),        # bad completion
    (_RaisingUsage(), {"completion_tokens": None, "reasoning_tokens": None, "reasoning_share": None}),       # throwing usage
])
def test_snapshot_reads_provider_counters_defensively(usage, expected):
    snap = completion_diagnostics_snapshot(
        provider="groq", model=GROQ_MODEL, sent_reservation=3395, usage=usage, status="reported",
    )
    assert {k: snap[k] for k in expected} == expected
    assert snap["sent_reservation"] == 3395 and snap["usage_present"] is True
    assert snap["scope"] == COMPLETION_DIAGNOSTICS_SCOPE


def test_snapshot_without_usage_and_reservation_validation():
    missing = completion_diagnostics_snapshot(provider="groq", model=GROQ_MODEL, sent_reservation=3395, usage=None, status="usage_missing")
    assert missing["usage_present"] is False and missing["completion_tokens"] is None and missing["reasoning_tokens"] is None
    for bad in (0, -5, True, None, "3395"):
        snap = completion_diagnostics_snapshot(provider="groq", model=GROQ_MODEL, sent_reservation=bad, usage=None, status="not_sent")
        assert snap["sent_reservation"] is None, bad
    # discriminating positive: a valid reservation survives
    assert completion_diagnostics_snapshot(provider="groq", model=GROQ_MODEL, sent_reservation=4096, usage=None, status="no_response")["sent_reservation"] == 4096


# ---------------------------------------------------------------- 2. the Groq adapter, attempt by attempt
@pytest.mark.asyncio
async def test_success_carries_snapshot_and_the_request_is_unchanged(monkeypatch, caplog):
    provider, calls = _groq(monkeypatch, _response(usage=_usage(42, 7), reasoning_text=REASONING_SENTINEL))
    with caplog.at_level(logging.DEBUG):
        result = await provider.generate(PROMPT_SENTINEL, output_schema=None, temperature=0.3, max_tokens=4096)

    assert len(calls) == 1 and set(calls[0]) == REQUEST_KEYS
    assert calls[0]["messages"][0]["content"] == PROMPT_SENTINEL
    assert "reasoning_tokens" not in calls[0]["messages"][0]["content"]
    sent = calls[0]["max_tokens"]
    snap = result[COMPLETION_DIAGNOSTICS_ATTR]
    assert snap["status"] == "reported" and snap["sent_reservation"] == sent
    assert snap["completion_tokens"] == 42 and snap["reasoning_tokens"] == 7 and snap["reasoning_share"] == round(7 / 42, 4)
    # legacy contract untouched, plus exactly one new key
    assert result["_completion_token_reservation"] == sent and result["usage"]["output_tokens"] == 42
    assert set(result) == {"content", "usage", "_inference_quality", "_schema_repaired_fields",
                           "_schema_incomplete_fields", "_completion_token_reservation", COMPLETION_DIAGNOSTICS_ATTR}
    # privacy: the fake reasoning text and the prompt never reach the result or the logs
    assert REASONING_SENTINEL not in json.dumps(result) and REASONING_SENTINEL not in caplog.text
    assert PROMPT_SENTINEL not in caplog.text


@pytest.mark.asyncio
async def test_schema_guidance_suffix_carries_no_diagnostic_text(monkeypatch):
    provider, calls = _groq(monkeypatch, _response())
    schema = ZAgentAnalysis.model_json_schema()
    await provider.generate("p", output_schema=schema, temperature=0.3, max_tokens=4096)
    content = calls[0]["messages"][0]["content"]
    assert content.endswith("JSON:") and "diagnostic" not in content.lower() and "reasoning_tokens" not in content


@pytest.mark.asyncio
async def test_truncation_exception_carries_the_same_attempt_snapshot(monkeypatch):
    provider, calls = _groq(monkeypatch, _response(usage=_usage(3395, 1000), finish_reason="length"))
    with pytest.raises(ValueError, match="truncated before completion") as info:
        await provider.generate("p", output_schema=None, temperature=0.3, max_tokens=4096)
    exc = info.value
    snap = snapshot_from_exception(exc)
    assert snap["status"] == "reported" and snap["sent_reservation"] == calls[0]["max_tokens"]
    assert snap["completion_tokens"] == 3395 and snap["reasoning_tokens"] == 1000
    # legacy telemetry and the truncation verdict are byte-for-byte what they were
    assert exc._provider_output_truncated is True
    assert exc._completion_token_reservation == calls[0]["max_tokens"] and exc._provider_reported_output_tokens == 3395
    monitor = unavailable_agent_token_monitor(configured_ceiling=8192, exc=exc, truncated=True)
    assert monitor["token_count"] == 3395 and monitor["ceiling"] == calls[0]["max_tokens"] and monitor["truncated"] is True


@pytest.mark.asyncio
async def test_truncation_without_usage_reports_usage_missing_and_keeps_legacy_nulls(monkeypatch):
    provider, calls = _groq(monkeypatch, _response(usage="omit", finish_reason="length"))
    with pytest.raises(ValueError) as info:
        await provider.generate("p", output_schema=None, temperature=0.3, max_tokens=4096)
    exc = info.value
    snap = snapshot_from_exception(exc)
    assert snap["status"] == "usage_missing" and snap["sent_reservation"] == calls[0]["max_tokens"]
    assert snap["completion_tokens"] is None and snap["reasoning_tokens"] is None
    assert getattr(exc, "_provider_reported_output_tokens", None) is None
    monitor = unavailable_agent_token_monitor(configured_ceiling=8192, exc=exc, truncated=True)
    assert monitor["token_count"] is None and monitor["ceiling"] == calls[0]["max_tokens"]


@pytest.mark.asyncio
async def test_local_admission_refusal_is_not_sent_and_has_no_reservation(monkeypatch):
    provider, calls = _groq(monkeypatch, _response())
    with pytest.raises(ValueError, match="not admissible") as info:
        await provider.generate("x" * 30000, output_schema=None, temperature=0.3, max_tokens=4096)
    exc = info.value
    assert calls == []
    snap = snapshot_from_exception(exc)
    assert snap["status"] == "not_sent" and snap["sent_reservation"] is None and snap["completion_tokens"] is None
    assert getattr(exc, "_completion_token_reservation", None) is None


@pytest.mark.asyncio
async def test_recovery_snapshot_comes_only_from_the_final_attempt(monkeypatch):
    first_reservation = GROQ_8K_TPM_COMPLETION_CAP  # a 4,000-char prompt is admitted at the cap
    provider, calls = _groq(monkeypatch, [
        _tpm_error(requested=first_reservation + 3500),          # provider says the prompt really cost 3,500
        _response(usage=_usage(77, 11)),                          # distinct sentinel counters for attempt 2
    ])
    result = await provider.generate("x" * 4000, output_schema=None, temperature=0.3, max_tokens=4096)
    assert len(calls) == 2 and calls[0]["max_tokens"] == first_reservation
    retry_budget = calls[1]["max_tokens"]
    assert retry_budget == 8000 - 3500 - 512 and retry_budget != first_reservation
    snap = result[COMPLETION_DIAGNOSTICS_ATTR]
    assert snap["sent_reservation"] == retry_budget and snap["completion_tokens"] == 77 and snap["reasoning_tokens"] == 11
    assert result["_completion_token_reservation"] == retry_budget


@pytest.mark.asyncio
async def test_terminal_retry_failure_reports_no_response_for_the_final_attempt(monkeypatch):
    provider, calls = _groq(monkeypatch, [
        _tpm_error(requested=GROQ_8K_TPM_COMPLETION_CAP + 3500),
        RuntimeError("transport failed on the recovery attempt"),
    ])
    with pytest.raises(RuntimeError) as info:
        await provider.generate("x" * 4000, output_schema=None, temperature=0.3, max_tokens=4096)
    assert len(calls) == 2
    snap = snapshot_from_exception(info.value)
    assert snap["status"] == "no_response" and snap["sent_reservation"] == calls[1]["max_tokens"]
    assert snap["completion_tokens"] is None and snap["reasoning_tokens"] is None


@pytest.mark.asyncio
async def test_unrecoverable_first_failure_reports_no_response_with_the_sent_reservation(monkeypatch):
    provider, calls = _groq(monkeypatch, [_FakeGroqError(code="rate_limit_exceeded", message="Limit 8000, Requested 9000", status_code=429)])
    with pytest.raises(_FakeGroqError) as info:
        await provider.generate("p", output_schema=None, temperature=0.3, max_tokens=4096)
    assert len(calls) == 1
    snap = snapshot_from_exception(info.value)
    assert snap["status"] == "no_response" and snap["sent_reservation"] == calls[0]["max_tokens"]


@pytest.mark.asyncio
async def test_immutable_exception_keeps_its_own_contract(monkeypatch):
    provider, calls = _groq(monkeypatch, [_ImmutableError("slots only")])
    with pytest.raises(_ImmutableError) as info:
        await provider.generate("p", output_schema=None, temperature=0.3, max_tokens=4096)
    assert snapshot_from_exception(info.value) is None and str(info.value) == "slots only"


def test_cause_chain_walk_is_bounded_and_cycle_safe():
    a, b = ValueError("a"), ValueError("b")
    a.__cause__, b.__cause__ = b, a  # cycle
    assert snapshot_from_exception(a) is None
    b._completion_diagnostics = _snapshot()
    assert snapshot_from_exception(a)["completion_tokens"] == 3395
    deep = ValueError("root"); deep._completion_diagnostics = _snapshot(completion=1)
    chain = deep
    for _ in range(6):  # deeper than the walk: must NOT be found
        outer = ValueError("wrap"); outer.__cause__ = chain; chain = outer
    assert snapshot_from_exception(chain) is None


# ---------------------------------------------------------------- 3. the agent boundary
class _DictProvider:
    def __init__(self, response, name=f"groq/{GROQ_MODEL}"):
        self._response, self._name = response, name

    def get_model_name(self):
        return self._name

    async def generate(self, prompt, output_schema=None, temperature=0.7, max_tokens=4096):
        return self._response


def _valid_z_content():
    return {
        "reasoning_steps": [{"step_number": 1, "thought": "t", "confidence": 0.9}],
        "ethics_score": 8.0, "z_protocol_compliance": True, "ethical_concerns": [],
        "mitigation_measures": [], "recommendation": "ok", "veto_triggered": False, "confidence": 0.9,
    }


@pytest.mark.asyncio
async def test_result_carries_the_adapter_snapshot_unchanged():
    snap = _snapshot()
    agent = ZAgent(llm_provider=_DictProvider({
        "content": _valid_z_content(), "usage": {"output_tokens": 3395, "input_tokens": 10, "total_tokens": 3405},
        "_inference_quality": "real", "_completion_token_reservation": 3395, COMPLETION_DIAGNOSTICS_ATTR: snap,
    }))
    result = await agent.analyze(Concept(name="n", description="d", context=None))
    assert result._completion_diagnostics == snap and result._completion_diagnostics is not snap
    assert result._output_tokens == 3395 and result._completion_token_reservation == 3395


@pytest.mark.asyncio
async def test_post_usage_schema_failure_keeps_the_whole_snapshot():
    snap = _snapshot()
    bad = _valid_z_content(); bad["ethics_score"] = "not a number"
    agent = ZAgent(llm_provider=_DictProvider({
        "content": bad, "usage": {"output_tokens": 3395}, "_inference_quality": "real",
        "_completion_token_reservation": 3395, COMPLETION_DIAGNOSTICS_ATTR: snap,
    }))
    with pytest.raises(Exception) as info:
        await agent.analyze(Concept(name="n", description="d", context=None))
    exc = info.value
    assert exc._completion_token_reservation == 3395               # legacy behaviour kept
    assert snapshot_from_exception(exc)["completion_tokens"] == 3395  # counters no longer lost


@pytest.mark.asyncio
async def test_non_dict_provider_response_yields_no_snapshot():
    agent = ZAgent(llm_provider=_DictProvider(_valid_z_content(), name="mock/test-model"))
    result = await agent.analyze(Concept(name="n", description="d", context=None))
    assert getattr(result, "_completion_diagnostics", None) is None


# ---------------------------------------------------------------- 4. the orchestration retry: distinct per-attempt sentinels
class _RetryableError(Exception):
    status_code = 429
    retry_after = 3


@pytest.mark.asyncio
async def test_completion_retry_delivers_only_the_final_attempt(monkeypatch):
    async def _no_sleep(_seconds):
        return None
    monkeypatch.setattr(trinity_retry, "_sleep", _no_sleep)
    first = _RetryableError("first"); first._completion_diagnostics = _snapshot(completion=111, reasoning=1)
    x, z, _ = _results(); z._completion_diagnostics = _snapshot(completion=222, reasoning=2)
    attempts = iter([first, z])

    async def analyze_call():
        outcome = next(attempts)
        if isinstance(outcome, BaseException):
            raise outcome
        return outcome

    budget = TrinityRetryBudget()
    result = await analyze_with_completion_retry(analyze_call, agent_id="Z", byok=False, session_id="s", budget=budget)
    assert result._completion_diagnostics["completion_tokens"] == 222
    assert budget.summary()["Z"]["outcome"] == "recovered"

    second = _RetryableError("second"); second._completion_diagnostics = _snapshot(completion=333, reasoning=3)
    attempts = iter([first, second])
    with pytest.raises(_RetryableError) as info:
        await analyze_with_completion_retry(analyze_call, agent_id="Z", byok=False, session_id="s", budget=TrinityRetryBudget())
    assert snapshot_from_exception(info.value)["completion_tokens"] == 333 and info.value._trinity_retry_attempted is True


# ---------------------------------------------------------------- 5. the public envelope
def test_envelope_never_attributes_groq_to_another_provider():
    gem = completion_diagnostics_envelope(SimpleNamespace(), _NamedProvider("gemini/gemini-3.5-flash-lite"))
    assert gem["provider"] == "gemini" and gem["status"] == "unsupported" and gem["completion_tokens"] is None
    groq = completion_diagnostics_envelope(SimpleNamespace(), _NamedProvider(f"groq/{GROQ_MODEL}"))
    assert groq["provider"] == "groq" and groq["status"] == "unavailable"
    assert set(gem) == ENVELOPE_KEYS and gem["scope"] == COMPLETION_DIAGNOSTICS_SCOPE and gem["note"] == COMPLETION_DIAGNOSTICS_NOTE


def test_envelope_revalidates_a_tampered_snapshot():
    tampered = _snapshot(); tampered.update({"completion_tokens": "3395", "reasoning_share": 7.5, "status": "made-up", "model": None})
    env = completion_diagnostics_envelope(SimpleNamespace(_completion_diagnostics=tampered), _NamedProvider(f"groq/{GROQ_MODEL}"))
    assert env["completion_tokens"] is None and env["reasoning_share"] is None and env["status"] == "unavailable"
    assert env["model"] == GROQ_MODEL  # falls back to the resolved provider identity
    good = completion_diagnostics_envelope(SimpleNamespace(_completion_diagnostics=_snapshot()), None)
    assert good == {**good, "provider": "groq", "model": GROQ_MODEL, "status": "reported", "sent_reservation": 3395,
                    "completion_tokens": 3395, "reasoning_tokens": 1000, "reasoning_share": round(1000 / 3395, 4)}


# ---------------------------------------------------------------- 6. the server carriers
@pytest.fixture(scope="module")
def app():
    return server.create_http_server()


def _wire(monkeypatch, x=None, z=None, cs=None, providers=None):
    providers = providers or {
        "X": _NamedProvider("gemini/gemini-3.5-flash-lite"),
        "Z": _NamedProvider(f"groq/{GROQ_MODEL}"),
        "CS": _NamedProvider(f"groq/{GROQ_MODEL}"),
    }
    monkeypatch.setattr(config_helper, "get_agent_provider", lambda agent_id, _ctx=None: providers[agent_id])

    def _make(outcome):
        async def _analyze(_self, _concept, _prior=None, _metrics=None):
            if isinstance(outcome, BaseException):
                raise outcome
            return outcome
        return _analyze

    if x is not None:
        monkeypatch.setattr(XAgent, "analyze", _make(x))
    if z is not None:
        monkeypatch.setattr(ZAgent, "analyze", _make(z))
    if cs is not None:
        monkeypatch.setattr(CSAgent, "analyze", _make(cs))
    monkeypatch.setattr(server, "persist_trinity_result", lambda *a, **k: None)

    async def _no_stagger(_z, _cs):
        return False
    monkeypatch.setattr(trinity_retry, "stagger_if_shared_provider", _no_stagger)


@pytest.mark.asyncio
async def test_trinity_payload_carries_per_stage_envelopes_and_monitors_are_unchanged(app, monkeypatch):
    x, z, cs = _results()
    z._output_tokens, z._completion_token_reservation = 2625, 4096
    z._completion_diagnostics = _snapshot(completion=2625, reasoning=900, reservation=4096)
    cs._output_tokens, cs._completion_token_reservation = 3204, 3740
    cs._completion_diagnostics = _snapshot(completion=3204, reasoning=1100, reservation=3740)
    z._hidden = REASONING_SENTINEL
    _wire(monkeypatch, x=x, z=z, cs=cs)

    payload = await call(app, "run_full_trinity", {"concept_name": "n", "concept_description": "d", "detail": "standard"})

    assert payload["_x_completion_diagnostics"]["status"] == "unsupported" and payload["_x_completion_diagnostics"]["provider"] == "gemini"
    zd, csd = payload["_z_completion_diagnostics"], payload["_cs_completion_diagnostics"]
    assert (zd["status"], zd["sent_reservation"], zd["completion_tokens"], zd["reasoning_tokens"]) == ("reported", 4096, 2625, 900)
    assert (csd["status"], csd["sent_reservation"], csd["completion_tokens"], csd["reasoning_tokens"]) == ("reported", 3740, 3204, 1100)
    # legacy monitors: identical to what the unchanged monitor functions compute
    assert payload["_z_token_monitor"] == check_z_agent_response(2625, ceiling=4096, configured_ceiling=8192)
    assert payload["_cs_token_monitor"] == check_cs_agent_response(3204, ceiling=3740, configured_ceiling=8192)
    assert payload["_agent_chain_status"] == {"x_agent": "real", "z_agent": "real", "cs_agent": "real"}
    assert REASONING_SENTINEL not in json.dumps(payload)


@pytest.mark.asyncio
async def test_trinity_failed_stage_envelope_comes_from_the_exception(app, monkeypatch):
    x, _, cs = _results()
    truncated = ValueError(f"Groq response truncated before completion (model={GROQ_MODEL}, finish_reason=length).")
    truncated._provider_output_truncated = True
    truncated._completion_token_reservation, truncated._provider_reported_output_tokens = 3395, 3395
    truncated._completion_diagnostics = _snapshot(completion=3395, reasoning=1200, reservation=3395)
    _wire(monkeypatch, x=x, z=truncated, cs=cs)

    payload = await call(app, "run_full_trinity", {"concept_name": "n", "concept_description": "d", "detail": "standard"})

    assert payload["_stage_errors"]["Z"]["error_code"] == "PROVIDER_OUTPUT_TRUNCATED"
    zd = payload["_z_completion_diagnostics"]
    assert (zd["status"], zd["sent_reservation"], zd["completion_tokens"], zd["reasoning_tokens"]) == ("reported", 3395, 3395, 1200)
    expected_monitor = unavailable_agent_token_monitor(configured_ceiling=8192, exc=truncated, truncated=True)
    assert payload["_z_token_monitor"] == expected_monitor and payload["_z_token_monitor"]["truncated"] is True
    assert payload["_overall_quality"] != "full" and payload["synthesis"]["analysis_incomplete"] is True


@pytest.mark.asyncio
async def test_trinity_markdown_carrier_delivers_the_envelopes(app, monkeypatch):
    """The markdown carrier is selected by the request's Accept header, not a tool
    argument, so this drives the registered tool's own function with a fake
    request context — the same body the MCP dispatch runs."""
    x, z, cs = _results()
    z._completion_diagnostics = _snapshot(completion=10, reasoning=2, reservation=4096)
    _wire(monkeypatch, x=x, z=z, cs=cs)
    tool = await app.get_tool("run_full_trinity")
    ctx = SimpleNamespace(request_context={"accept": "text/markdown"})
    payload = await tool.fn(concept_name="n", concept_description="d", ctx=ctx)
    assert payload.get("format") == "markdown" and "content" in payload
    assert payload["_z_completion_diagnostics"]["completion_tokens"] == 10
    assert payload["_cs_completion_diagnostics"]["status"] == "unavailable"  # Groq-named provider, no snapshot
    assert payload["_x_completion_diagnostics"]["status"] == "unsupported"


@pytest.mark.asyncio
async def test_standalone_z_carries_envelope_at_standard_but_summary_keeps_legacy_bytes(app, monkeypatch):
    _, z, _ = _results()
    z._completion_diagnostics = _snapshot(completion=2625, reasoning=900, reservation=4096)
    _wire(monkeypatch, z=z)
    standard = await call(app, "consult_agent_z", {"concept_name": "n", "concept_description": "d", "detail": "standard"})
    assert standard["_completion_diagnostics"]["completion_tokens"] == 2625 and standard["_completion_diagnostics"]["provider"] == "groq"
    summary = await call(app, "consult_agent_z", {"concept_name": "n", "concept_description": "d", "detail": "summary"})
    assert "_completion_diagnostics" not in summary


@pytest.mark.asyncio
async def test_standalone_x_and_cs_carry_envelopes_too(app, monkeypatch):
    x, _, cs = _results()
    cs._completion_diagnostics = _snapshot(completion=3204, reasoning=1100, reservation=3740)
    _wire(monkeypatch, x=x, cs=cs)
    xp = await call(app, "consult_agent_x", {"concept_name": "n", "concept_description": "d"})
    assert xp["_completion_diagnostics"]["status"] == "unsupported" and xp["_completion_diagnostics"]["provider"] == "gemini"
    csp = await call(app, "consult_agent_cs", {"concept_name": "n", "concept_description": "d"})
    assert csp["_completion_diagnostics"]["completion_tokens"] == 3204 and csp["_completion_diagnostics"]["sent_reservation"] == 3740


@pytest.mark.asyncio
async def test_standalone_cs_failure_payload_carries_the_failed_attempt(app, monkeypatch):
    truncated = ValueError(f"Groq response truncated before completion (model={GROQ_MODEL}, finish_reason=length).")
    truncated._provider_output_truncated = True
    truncated._completion_diagnostics = _snapshot(completion=3738, reasoning=1500, reservation=3738)
    _wire(monkeypatch, cs=truncated)
    payload = await call(app, "consult_agent_cs", {"concept_name": "n", "concept_description": "d"})
    assert payload["error_code"] == "PROVIDER_OUTPUT_TRUNCATED" and payload["_inference_quality"] == "unavailable"
    env = payload["_completion_diagnostics"]
    assert (env["status"], env["sent_reservation"], env["completion_tokens"], env["reasoning_tokens"]) == ("reported", 3738, 3738, 1500)
    assert REASONING_SENTINEL not in json.dumps(payload)
