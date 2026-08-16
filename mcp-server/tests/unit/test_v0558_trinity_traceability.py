"""v0.5.58 flagship-tool truth, degradation, and model-currency contracts."""

import json
import logging
from datetime import date
from unittest.mock import AsyncMock, MagicMock

import pytest

from verifimind_mcp import config_helper, server
from verifimind_mcp.agents import CSAgent, XAgent, ZAgent
from verifimind_mcp.llm.provider import (
    MODEL_CURRENCY_MAX_AGE_DAYS,
    PROVIDER_CONFIGS,
    PROVIDER_DEFAULT_CEREBRAS_MODEL,
    REMOTE_BYOK_PROVIDER_IDS,
    GroqProvider,
    provider_catalog_currency_issues,
)
from verifimind_mcp.models.reasoning import (
    CSAgentAnalysis,
    ReasoningStep,
    XAgentAnalysis,
    ZAgentAnalysis,
)
from verifimind_mcp.utils.provider_failures import (
    provider_failure_contract,
    trinity_stage_failure,
)
from verifimind_mcp.utils.synthesis import create_synthesis

from .mcp_tool_harness import call


def _steps():
    return [ReasoningStep(step_number=1, thought="bounded reasoning", confidence=0.9)]


def _real_results():
    x_result = XAgentAnalysis(
        reasoning_steps=_steps(),
        innovation_score=8.8,
        strategic_value=8.4,
        opportunities=["Useful opportunity"],
        risks=["Execution risk"],
        recommendation="Proceed deliberately.",
        confidence=0.9,
    )
    z_result = ZAgentAnalysis(
        reasoning_steps=_steps(),
        ethics_score=8.6,
        z_protocol_compliance=True,
        ethical_concerns=["Consent controls need explicit verification."],
        mitigation_measures=["Add consent withdrawal tests."],
        recommendation="Proceed after mitigation.",
        veto_triggered=False,
        confidence=0.9,
    )
    cs_result = CSAgentAnalysis(
        reasoning_steps=_steps(),
        security_score=8.2,
        vulnerabilities=["Rate-limit policy needs an abuse test."],
        attack_vectors=["Quota exhaustion"],
        security_recommendations=["Add an admission-control test."],
        socratic_questions=["What happens during provider exhaustion?"],
        recommendation="Proceed after the bounded repair.",
        confidence=0.9,
    )
    for result in (x_result, z_result, cs_result):
        result._inference_quality = "real"
    return x_result, z_result, cs_result


def test_founder_summary_never_claims_absence_when_z_or_cs_lists_findings():
    synthesis = create_synthesis(*_real_results())
    what_works = synthesis.founder_summary["what_works"]

    assert "No major ethical or legal concerns for this concept." not in what_works
    assert "No significant security risks identified." not in what_works
    assert any("No Z-Protocol veto" in item for item in what_works)
    assert any("No critical security blocker" in item for item in what_works)
    assert "Consent controls need explicit verification." in synthesis.founder_summary[
        "things_to_address"
    ]
    assert "Rate-limit policy needs an abuse test." in synthesis.founder_summary[
        "things_to_address"
    ]


def test_founder_summary_allows_bounded_absence_claims_only_when_lists_are_empty():
    x_result, z_result, cs_result = _real_results()
    z_result.ethical_concerns = []
    cs_result.vulnerabilities = []

    what_works = create_synthesis(
        x_result, z_result, cs_result
    ).founder_summary["what_works"]

    assert "No major ethical or legal concerns were identified in this review." in what_works
    assert "No significant security risks were identified in this review." in what_works


class _NamedProvider:
    def __init__(self, name):
        self.name = name

    def get_model_name(self):
        return self.name


class _RateLimitError(Exception):
    status_code = 429
    retry_after = 7


@pytest.fixture(scope="module")
def app():
    return server.create_http_server()


@pytest.mark.asyncio
async def test_z_rate_limit_preserves_x_runs_cs_and_withholds_aggregate(
    app, monkeypatch, capsys
):
    x_result, _, cs_result = _real_results()
    cs_prior_agent_ids = []
    history_calls = []

    providers = {
        "X": _NamedProvider("gemini/gemini-3.5-flash-lite"),
        "Z": _NamedProvider("groq/openai/gpt-oss-120b"),
        "CS": _NamedProvider("groq/openai/gpt-oss-120b"),
    }
    monkeypatch.setattr(
        config_helper, "get_trinity_providers", lambda _ctx: providers
    )

    async def x_analyze(_self, _concept, _prior=None, _metrics=None):
        return x_result

    async def z_analyze(_self, _concept, _prior=None, _metrics=None):
        raise _RateLimitError("SENSITIVE-PROVIDER-BODY-and-billing-link")

    async def cs_analyze(_self, _concept, prior=None, _metrics=None):
        cs_prior_agent_ids.extend(chain.agent_id for chain in prior.chains)
        return cs_result

    monkeypatch.setattr(XAgent, "analyze", x_analyze)
    monkeypatch.setattr(ZAgent, "analyze", z_analyze)
    monkeypatch.setattr(CSAgent, "analyze", cs_analyze)
    monkeypatch.setattr(
        server,
        "load_validation_history",
        lambda: (_ for _ in ()).throw(AssertionError("history must not be read")),
    )
    monkeypatch.setattr(
        server,
        "persist_trinity_result",
        lambda *args, **kwargs: history_calls.append((args, kwargs)),
    )

    payload = await call(app, "run_full_trinity", {
        "concept_name": "PRIVATE-CONCEPT-MUST-NOT-BE-LOGGED",
        "concept_description": "Verify bounded stage degradation.",
        "save_to_history": True,
    })

    assert payload["_overall_quality"] == "partial"
    assert payload["status"] == "partial"
    assert payload["_agent_chain_status"] == {
        "x_agent": "real",
        "z_agent": "unavailable",
        "cs_agent": "real",
    }
    assert payload["_agents_completed"] == ["X", "CS"]
    assert payload["_agents_failed"] == ["Z"]
    assert cs_prior_agent_ids == ["X"]
    assert payload["x_analysis"]["innovation_score"] == 8.8
    assert payload["z_analysis"]["ethics_score"] is None
    assert payload["z_analysis"]["veto_triggered"] is None
    assert payload["cs_analysis"]["security_score"] == 8.2
    assert payload["synthesis"]["overall_score"] is None
    assert payload["synthesis"]["confidence"] is None
    assert payload["synthesis"]["recommendation"] == "revise"
    assert payload["saved_to_history"] is False
    assert "stages failed" in payload["_history_warning"]
    assert history_calls == []

    stage_error = payload["_stage_errors"]["Z"]
    assert stage_error == {
        "error_code": "PROVIDER_RATE_LIMITED",
        "message": (
            "The provider temporarily rejected this stage because capacity was exhausted."
        ),
        "recovery_hint": "Retry after at least 7 seconds.",
        "provider": "groq",
        "model": "openai/gpt-oss-120b",
        "retryable": True,
        "retry_after_seconds": 7.0,
        # v0.5.60 contract EXTENSION: the orchestrator spent its one bounded
        # completion retry on this stage (7s is within the cap; the fake fails
        # both attempts) and discloses that fact. Every v0.5.58 field above is
        # unchanged — the degradation contract itself did not move.
        "retry_attempted": True,
    }
    # v0.5.60: the retry summary surfaces what was actually attempted.
    assert payload["_stage_retries"]["Z"]["outcome"] == "failed_again"
    assert payload["_stage_retries"]["Z"]["on_error_code"] == "PROVIDER_RATE_LIMITED"
    assert payload["_z_token_monitor"]["risk_level"] == "UNAVAILABLE"

    stderr = capsys.readouterr().err
    assert "SENSITIVE-PROVIDER-BODY" not in stderr
    assert "PRIVATE-CONCEPT-MUST-NOT-BE-LOGGED" not in stderr
    structured = [
        json.loads(line)
        for line in stderr.splitlines()
        if line.startswith("{") and "trinity_provider_failure" in line
    ]
    assert structured
    assert structured[-1]["severity"] == "ERROR"
    assert structured[-1]["error_code"] == "PROVIDER_RATE_LIMITED"
    assert structured[-1]["agent"] == "Z"

    # v0.5.60: run-lifecycle events — exactly one started and one completed
    # per run, the completed carrying the honest outcome. This is the
    # completion-rate denominator that never existed before.
    started = [
        json.loads(line) for line in stderr.splitlines()
        if line.startswith("{") and "trinity_run_started" in line
    ]
    completed = [
        json.loads(line) for line in stderr.splitlines()
        if line.startswith("{") and "trinity_run_completed" in line
    ]
    assert len(started) == 1
    assert len(completed) == 1
    assert completed[0]["outcome"] == "partial"
    assert completed[0]["agents_failed"] == ["Z"]
    assert completed[0]["retried_stages"] == ["Z"]
    assert completed[0]["session_id"] == started[0]["session_id"]


def test_truncation_has_typed_trace_and_never_reflects_provider_body(capsys):
    secret = "SENSITIVE-TRUNCATED-PROVIDER-CONTENT"
    exc = ValueError(
        "Groq response truncated before completion "
        f"(finish_reason=length). {secret}"
    )

    placeholder, record = trinity_stage_failure(
        agent_id="CS",
        provider=_NamedProvider("groq/openai/gpt-oss-120b"),
        exc=exc,
        byok=False,
        session_id="trace123",
    )

    assert placeholder._inference_quality == "unavailable"
    assert record["error_code"] == "PROVIDER_OUTPUT_TRUNCATED"
    assert record["provider"] == "groq"
    assert record["model"] == "openai/gpt-oss-120b"
    assert secret not in json.dumps(record)
    stderr = capsys.readouterr().err
    assert secret not in stderr
    event = json.loads(stderr.strip())
    assert event["severity"] == "ERROR"
    assert event["session_id"] == "trace123"


def test_standalone_error_classifier_distinguishes_byok_auth_from_hosted_auth():
    class AuthenticationError(Exception):
        status_code = 401

    exc = AuthenticationError("SENSITIVE-KEY-DIAGNOSTIC")
    assert provider_failure_contract(exc, byok=True)["error_code"] == "BYOK_AUTH_FAILED"
    assert provider_failure_contract(exc, byok=False)["error_code"] == "PROVIDER_AUTH_FAILED"


def test_request_too_large_has_a_typed_non_reflecting_contract():
    class RequestTooLarge(Exception):
        status_code = 413

    contract = provider_failure_contract(
        RequestTooLarge("SENSITIVE-PROVIDER-BODY"), byok=False
    )
    assert contract["error_code"] == "PROVIDER_REQUEST_TOO_LARGE"
    assert contract["retryable"] is False
    assert "SENSITIVE-PROVIDER-BODY" not in json.dumps(contract)


@pytest.mark.asyncio
async def test_groq_adapter_does_not_log_raw_sdk_error(caplog):
    secret = "SENSITIVE-ORG-ID-AND-BILLING-URL"
    provider = GroqProvider(model="openai/gpt-oss-120b", api_key="gsk_test")
    provider.client = MagicMock()
    provider.client.chat.completions.create = AsyncMock(
        side_effect=_RateLimitError(secret)
    )

    with caplog.at_level(logging.ERROR, logger="verifimind_mcp.llm.provider"):
        with pytest.raises(_RateLimitError):
            await provider.generate("probe", max_tokens=1024)

    messages = "\n".join(record.getMessage() for record in caplog.records)
    assert secret not in messages
    assert "exception_type=_RateLimitError" in messages


def test_cerebras_catalog_uses_live_ids_and_rejects_retired_ids():
    config = PROVIDER_CONFIGS["cerebras"]
    assert PROVIDER_DEFAULT_CEREBRAS_MODEL == "gpt-oss-120b"
    assert config["default_model"] == "gpt-oss-120b"
    assert config["models"] == ["gpt-oss-120b", "zai-glm-4.7", "gemma-4-31b"]
    assert "llama-3.3-70b" not in config["models"]
    assert "llama-3.1-8b" not in config["models"]


def test_all_six_remote_byok_catalogs_pass_the_currency_gate():
    assert REMOTE_BYOK_PROVIDER_IDS == {
        "gemini", "openai", "anthropic", "groq", "cerebras", "mistral",
    }
    assert MODEL_CURRENCY_MAX_AGE_DAYS == 90
    assert provider_catalog_currency_issues(as_of=date(2026, 8, 7)) == {}

    stale = provider_catalog_currency_issues(as_of=date(2027, 1, 1))
    assert set(stale) == set(REMOTE_BYOK_PROVIDER_IDS)
    assert all("verification_stale" in findings for findings in stale.values())


def test_health_contract_exposes_model_catalog_currency():
    from verifimind_mcp.contract import get_public_contract

    contract = get_public_contract()
    assert contract["byok_model_catalog"] == {
        "status": "current",
        "max_age_days": 90,
        "issues": {},
    }
    assert all(
        contract["byok_providers"][provider_id]["models_verified_at"]
        for provider_id in REMOTE_BYOK_PROVIDER_IDS
    )
