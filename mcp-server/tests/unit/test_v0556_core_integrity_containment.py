"""v0.5.56 core-integrity and custom-template containment contract."""

import asyncio
import inspect
import json

import pytest
from unittest.mock import AsyncMock, MagicMock

from verifimind_mcp import server
from verifimind_mcp.agents import ZAgent
from verifimind_mcp.agents.base_agent import BaseAgent
from verifimind_mcp.availability import get_tool_availability
from verifimind_mcp.llm.provider import GeminiProvider, GroqProvider
from verifimind_mcp.models import Concept
from verifimind_mcp.models.reasoning import (
    CSAgentAnalysis,
    ReasoningStep,
    XAgentAnalysis,
    ZAgentAnalysis,
)
from verifimind_mcp.templates import import_url
from verifimind_mcp.templates.registry import TemplateRegistry
from verifimind_mcp.reporting.markdown_reporter import generate_markdown_summary
from verifimind_mcp.utils.reasoning_view import build_reasoning_block
from verifimind_mcp.utils.synthesis import create_synthesis

from .mcp_tool_harness import call


def _steps():
    return [ReasoningStep(step_number=1, thought="real reasoning", confidence=0.94)]


def _agent_results():
    x = XAgentAnalysis(
        reasoning_steps=_steps(),
        innovation_score=9.0,
        strategic_value=9.0,
        opportunities=["REAL-X-OPPORTUNITY"],
        risks=["REAL-X-RISK"],
        recommendation="build",
        confidence=0.94,
    )
    z = ZAgentAnalysis(
        reasoning_steps=_steps(),
        ethics_score=9.0,
        z_protocol_compliance=True,
        ethical_concerns=["REAL-Z-CONCERN"],
        mitigation_measures=["REAL-Z-MITIGATION"],
        recommendation="safe",
        confidence=0.94,
        jurisdiction_detected=["Global"],
        compliance_timeline=["Review before launch"],
        scoring_breakdown={"ethical_alignment": {"score": 9}},
        applicable_frameworks={"tier_1_international": ["UDHR"]},
    )
    cs = CSAgentAnalysis(
        reasoning_steps=_steps(),
        security_score=9.0,
        vulnerabilities=["PLACEHOLDER-VULNERABILITY"],
        attack_vectors=["PLACEHOLDER-ATTACK"],
        security_recommendations=["PLACEHOLDER-SECURITY-REC"],
        socratic_questions=["What fails?"],
        recommendation="secure",
        confidence=0.94,
    )
    for result in (x, z, cs):
        result._inference_quality = "real"
    return {"X": x, "Z": z, "CS": cs}


def test_all_real_trinity_retains_decision_confidence():
    results = _agent_results()
    synthesis = create_synthesis(results["X"], results["Z"], results["CS"])

    assert synthesis.recommendation == "proceed"
    assert synthesis.overall_score == 9.0
    assert synthesis.confidence == 0.94
    assert synthesis.confidence_valid is True
    assert synthesis.analysis_incomplete is False
    assert synthesis.quality_gate["passed"] is True


@pytest.mark.parametrize("agent_id", ["X", "Z", "CS"])
@pytest.mark.parametrize(
    "quality", ["partial", "fallback", "mock", "unknown", "unavailable"]
)
def test_any_non_real_required_stage_fails_closed(agent_id, quality):
    results = _agent_results()
    results[agent_id]._inference_quality = quality

    synthesis = create_synthesis(results["X"], results["Z"], results["CS"])

    assert synthesis.recommendation == "revise"
    assert synthesis.overall_score is None
    assert synthesis.confidence is None
    assert synthesis.confidence_valid is False
    assert synthesis.analysis_incomplete is True
    assert synthesis.degraded_agents == [agent_id]
    assert synthesis.quality_gate["passed"] is False
    assert synthesis.quality_gate["agents"][agent_id] == quality
    assert synthesis.inference_warning
    assert synthesis.founder_summary["verdict"].startswith("NEEDS HUMAN REVIEW")
    score_field = {
        "X": "innovation_score",
        "Z": "ethics_score",
        "CS": "security_score",
    }[agent_id]
    assert getattr(synthesis, score_field) is None
    if agent_id == "Z":
        assert synthesis.veto_triggered is None

    serialized = json.dumps(synthesis.model_dump())
    if agent_id == "X":
        assert "REAL-X-OPPORTUNITY" not in serialized
    if agent_id == "Z":
        assert "REAL-Z-CONCERN" not in serialized
    if agent_id == "CS":
        assert "PLACEHOLDER-VULNERABILITY" not in serialized


def test_degraded_reasoning_and_markdown_scores_are_withheld():
    results = _agent_results()
    results["Z"]._inference_quality = "fallback"
    synthesis = create_synthesis(results["X"], results["Z"], results["CS"])

    reasoning = build_reasoning_block(
        results["X"],
        results["Z"],
        results["CS"],
        {"x_agent": "real", "z_agent": "fallback", "cs_agent": "real"},
        "degraded",
        synthesis.inference_warning,
        "full",
    )
    assert reasoning["z"]["withheld"] is True
    assert "REAL-Z-CONCERN" not in json.dumps(reasoning["z"])

    from verifimind_mcp.models.results import (
        TrinityResult,
        ValidationHistory,
        ValidationHistoryEntry,
    )

    trinity_result = TrinityResult(
        validation_id="v0556",
        concept_name="Integrity probe",
        concept_description="probe",
        x_analysis=results["X"],
        z_analysis=results["Z"],
        cs_analysis=results["CS"],
        synthesis=synthesis,
    )
    report = generate_markdown_summary(trinity_result)
    assert "**Score:** unavailable" in report
    assert "| Z Guardian | unavailable |" in report
    history_entry = ValidationHistoryEntry.from_trinity_result(trinity_result)
    assert history_entry.overall_score is None
    assert history_entry.veto_triggered is None
    history_stats = ValidationHistory(entries=[history_entry]).get_statistics()
    assert history_stats["average_score"] is None
    assert history_stats["veto_rate"] is None
    assert history_stats["scored_validations"] == 0


@pytest.mark.asyncio
async def test_mock_trinity_withholds_all_synthetic_decision_fields(app):
    payload = await call(app, "run_full_trinity", {
        "concept_name": "Integrity probe",
        "concept_description": "Verify degraded output containment",
        "llm_provider": "mock",
    })

    assert payload["_overall_quality"] == "synthetic"
    assert payload["synthesis"]["overall_score"] is None
    assert payload["synthesis"]["confidence"] is None
    assert payload["synthesis"]["analysis_incomplete"] is True
    assert payload["x_analysis"]["innovation_score"] is None
    assert payload["x_analysis"]["recommendation"] is None
    assert payload["z_analysis"]["ethics_score"] is None
    assert payload["z_analysis"]["veto_triggered"] is None
    assert payload["z_analysis"]["recommendation"] is None
    assert payload["cs_analysis"]["security_score"] is None
    assert payload["cs_analysis"]["vulnerability_count"] is None
    assert payload["cs_analysis"]["recommendation"] is None
    assert all(payload["reasoning"][stage]["withheld"] for stage in ("x", "z", "cs"))


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("tool_name", "score_field", "decision_field"),
    [
        ("consult_agent_x", "innovation_score", "recommendation"),
        ("consult_agent_z", "ethics_score", "veto_triggered"),
        ("consult_agent_cs", "security_score", "recommendation"),
    ],
)
async def test_standalone_consults_withhold_mock_generated_fields(
    app, tool_name, score_field, decision_field
):
    payload = await call(app, tool_name, {
        "concept_name": "Integrity probe",
        "concept_description": "Verify standalone degraded containment",
        "llm_provider": "mock",
    })

    assert payload["_inference_quality"] == "mock"
    assert payload["analysis_incomplete"] is True
    assert payload[score_field] is None
    assert payload[decision_field] is None
    assert payload["reasoning_steps"] == []
    assert payload["_warning"]


@pytest.mark.asyncio
async def test_shared_agent_boundary_downgrades_evidence_incomplete_byok_z():
    class EvidenceIncompleteProvider:
        def get_model_name(self):
            return "test/evidence-incomplete"

        async def generate(self, *args, **kwargs):
            return {
                "content": {
                    "reasoning_steps": [
                        {"step_number": 1, "thought": "analysis", "confidence": 0.9}
                    ],
                    "ethics_score": 9.0,
                    "z_protocol_compliance": True,
                    "ethical_concerns": [],
                    "mitigation_measures": [],
                    "recommendation": "proceed",
                    "confidence": 0.9,
                },
                "usage": {},
                "_inference_quality": "real",
            }

    result = await ZAgent(llm_provider=EvidenceIncompleteProvider()).analyze(
        Concept(name="probe", description="probe")
    )

    assert result._inference_quality == "partial"
    assert set(result._schema_incomplete_fields) == {
        "jurisdiction_detected",
        "compliance_timeline",
        "scoring_breakdown",
        "applicable_frameworks",
    }


def test_public_agent_error_does_not_reflect_provider_content():
    payload = server._agent_exception_payload(
        ValueError("SENSITIVE-RAW-MODEL-CONTENT"),
        "Z Guardian",
        "probe",
    )
    assert "SENSITIVE-RAW-MODEL-CONTENT" not in json.dumps(payload)
    assert payload["error_code"] == "AGENT_ANALYSIS_ERROR"
    assert payload["_inference_quality"] == "unavailable"


def test_present_null_required_field_is_reported_as_repaired():
    schema = {
        "required": ["confidence", "items"],
        "properties": {
            "confidence": {"type": "number", "minimum": 0, "maximum": 1},
            "items": {"type": "array"},
        },
    }
    data, repaired = GeminiProvider._fill_schema_defaults_with_repairs(
        {"confidence": None, "items": []}, schema
    )

    assert data["confidence"] == 0.5
    assert data["items"] == []
    assert repaired == ["confidence"]


def test_z_promised_evidence_fields_are_quality_required_not_fabricated():
    schema = ZAgentAnalysis.model_json_schema()
    promised = {
        "jurisdiction_detected",
        "compliance_timeline",
        "scoring_breakdown",
        "applicable_frameworks",
    }
    assert all(
        schema["properties"][field].get("quality_required") is True
        for field in promised
    )

    incomplete = GeminiProvider._quality_incomplete_fields(
        {field: None for field in promised}, schema
    )
    assert set(incomplete) == promised


@pytest.mark.asyncio
async def test_groq_present_null_promised_z_field_downgrades_quality():
    provider = GroqProvider(
        model="openai/gpt-oss-120b", api_key="gsk_test"
    )
    provider.client = MagicMock()
    payload = {
        "reasoning_steps": [
            {"step_number": 1, "thought": "analysis", "confidence": 0.9}
        ],
        "ethics_score": 9.0,
        "z_protocol_compliance": True,
        "ethical_concerns": [],
        "mitigation_measures": [],
        "recommendation": "proceed",
        "confidence": 0.92,
        "jurisdiction_detected": ["Global"],
        "compliance_timeline": ["Review before launch"],
        "scoring_breakdown": None,
        "applicable_frameworks": {"tier_1_international": ["UDHR"]},
    }
    response = MagicMock()
    response.choices = [MagicMock()]
    response.choices[0].finish_reason = "stop"
    response.choices[0].message.content = json.dumps(payload)
    response.usage.prompt_tokens = 100
    response.usage.completion_tokens = 100
    response.usage.total_tokens = 200
    provider.client.chat.completions.create = AsyncMock(return_value=response)

    result = await provider.generate(
        "probe",
        output_schema=ZAgentAnalysis.model_json_schema(),
        max_tokens=1024,
    )

    assert result["_inference_quality"] == "partial"
    assert result["_schema_repaired_fields"] == []
    assert result["_schema_incomplete_fields"] == ["scoring_breakdown"]
    assert result["content"]["scoring_breakdown"] is None
    request_prompt = (
        provider.client.chat.completions.create.await_args.kwargs["messages"][0]["content"]
    )
    for promised_field in (
        "jurisdiction_detected",
        "compliance_timeline",
        "scoring_breakdown",
        "applicable_frameworks",
    ):
        assert promised_field in request_prompt


@pytest.fixture(scope="module")
def app():
    return server.create_http_server()


@pytest.mark.asyncio
async def test_custom_template_mutation_tools_fail_closed_without_reflection(app):
    secret = "DO-NOT-REFLECT-CUSTOM-CONTENT"
    registered = await call(app, "register_custom_template", {
        "name": "private",
        "agent_id": "X",
        "content": secret,
    })
    imported = await call(app, "import_template_from_url", {
        "url": "https://127.0.0.1/private.json",
    })

    for payload in (registered, imported):
        assert payload["status"] == "error"
        assert payload["error_code"] == "CUSTOM_TEMPLATE_TEMPORARILY_DISABLED"
        assert secret not in json.dumps(payload)
        assert "127.0.0.1" not in json.dumps(payload)
        assert "_system_notice" not in payload


@pytest.mark.asyncio
async def test_public_template_reads_exclude_process_local_custom_entries(app):
    registry = TemplateRegistry()
    template_id = "custom-v0556-isolation-probe"
    registry.unregister_custom_template(template_id)
    registry.register_custom_template(
        name="Isolation probe",
        agent_id="X",
        content="PRIVATE-TEMPLATE-CONTENT",
        template_id=template_id,
    )
    try:
        listing = await call(app, "list_prompt_templates", {})
        fetched = await call(app, "get_prompt_template", {
            "template_id": template_id,
        })
        exported = await call(app, "export_prompt_template", {
            "template_id": template_id,
        })
        stats = await call(app, "get_template_statistics", {})

        assert template_id not in json.dumps(listing)
        assert fetched["status"] == "not_found"
        assert exported["status"] == "not_found"
        assert "PRIVATE-TEMPLATE-CONTENT" not in json.dumps((fetched, exported))
        assert stats["custom_templates"] == 0
        assert stats["total_templates"] == stats["builtin_templates"]
    finally:
        registry.unregister_custom_template(template_id)


@pytest.mark.parametrize("url", [
    "https://127.0.0.1/internal",
    "https://localhost/secret",
    "http://169.254.169.254/latest/meta-data.json",
    "https://example.com/template.json",
])
def test_template_url_validator_rejects_internal_and_arbitrary_hosts(url):
    valid, source_type, error = import_url.validate_template_url(url)
    assert valid is False
    assert source_type == ""
    assert error


def test_allowed_host_resolving_private_fails_closed(monkeypatch):
    monkeypatch.setattr(
        import_url.socket,
        "getaddrinfo",
        lambda *args, **kwargs: [
            (
                import_url.socket.AF_INET,
                import_url.socket.SOCK_STREAM,
                6,
                "",
                ("127.0.0.1", 443),
            )
        ],
    )
    error = import_url._validate_resolved_target(
        "https://raw.githubusercontent.com/user/repo/main/template.json"
    )
    assert error == "Template host resolved to a non-public address"


def test_url_fetcher_binds_redirect_and_size_controls():
    source = inspect.getsource(import_url._fetch_url_content)
    assert "allow_redirects=False" in source
    assert "MAX_TEMPLATE_DOWNLOAD_BYTES" in source
    assert "iter_chunked" in source


def test_stale_all_tools_system_notice_is_suppressed(monkeypatch):
    monkeypatch.setattr(
        server,
        "SYSTEM_NOTICE",
        "All 13 tools free forever. Register at verifimind.ysenseai.org/register",
    )
    payload = server.wrap_response({"status": "ok"})
    assert "_system_notice" not in payload

    monkeypatch.setattr(server, "SYSTEM_NOTICE", "All tools free forever")
    payload = server.wrap_response({"status": "ok"})
    assert "_system_notice" not in payload


def test_non_conflicting_system_notice_can_still_be_delivered(monkeypatch):
    monkeypatch.setattr(server, "SYSTEM_NOTICE", "Maintenance window at 03:00 UTC")
    payload = server.wrap_response({"status": "ok"})
    assert payload["_system_notice"] == "Maintenance window at 03:00 UTC"


def test_accurate_thirteen_tool_notice_can_be_delivered(monkeypatch):
    notice = "13 tools defined; 8 active; 5 temporarily unavailable"
    monkeypatch.setattr(server, "SYSTEM_NOTICE", notice)
    payload = server.wrap_response({"status": "ok"})
    assert payload["_system_notice"] == notice


def test_discovery_card_matches_runtime_privacy_and_routing_contract():
    import http_server
    from verifimind_mcp.contract import get_public_contract

    response = asyncio.run(http_server.smithery_server_card_handler(None))
    card = json.loads(response.body)
    run_full = next(tool for tool in card["tools"] if tool["name"] == "run_full_trinity")
    routing = get_public_contract()["free_tier_routing"]

    assert card["version"] == "0.5.56"
    assert "8 MCP tools are active" in card["description"]
    assert "5 tools" in card["description"]
    for agent_id in ("X", "Z", "CS"):
        assert routing[agent_id]["model"] in card["description"]
        assert routing[agent_id]["provider"] in card["description"]
    assert run_full["inputSchema"]["properties"]["save_to_history"]["default"] is False
    assert "PROCEED/REFINE/HALT" not in run_full["description"]
    assert "proceed_with_caution" in run_full["description"]


def test_availability_contract_contains_exact_five_tools():
    availability = get_tool_availability()
    assert availability["defined"] == 13
    assert availability["active"] == 8
    assert availability["temporarily_unavailable"] == 5
    assert set(availability["unavailable_tools"]) == {
        "coordination_handoff_create",
        "coordination_handoff_read",
        "coordination_team_status",
        "register_custom_template",
        "import_template_from_url",
    }


def test_provider_diagnostics_do_not_log_raw_model_content():
    source = inspect.getsource(GeminiProvider)
    assert "Raw response:" not in source
    assert "clean_content[:300]" not in source
    assert "clean_content[:200]" not in source
    agent_source = inspect.getsource(BaseAgent.analyze)
    assert "concept.name" not in agent_source
    assert "analysis failed: {e}" not in agent_source
