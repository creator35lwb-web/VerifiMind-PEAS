"""v0.5.58 carries forward core-integrity and containment contracts."""

import asyncio
import builtins
import inspect
import json
import logging
import sys
from types import SimpleNamespace

import pytest
from unittest.mock import AsyncMock, MagicMock

from verifimind_mcp import server
from verifimind_mcp.agents import CSAgent, ZAgent
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


@pytest.mark.parametrize("degraded_agent", ["X", "CS"])
def test_trusted_z_veto_rejects_when_a_sibling_stage_is_degraded(degraded_agent):
    results = _agent_results()
    results["Z"].veto_triggered = True
    results[degraded_agent]._inference_quality = "fallback"

    synthesis = create_synthesis(results["X"], results["Z"], results["CS"])

    assert synthesis.recommendation == "reject"
    assert synthesis.veto_triggered is True
    assert synthesis.overall_score is None
    assert synthesis.analysis_incomplete is True
    assert "STOPPED:" in synthesis.founder_summary["verdict"]


def test_degraded_z_raw_veto_is_not_treated_as_trusted():
    results = _agent_results()
    results["Z"].veto_triggered = True
    results["Z"]._inference_quality = "partial"

    synthesis = create_synthesis(results["X"], results["Z"], results["CS"])

    assert synthesis.recommendation == "revise"
    assert synthesis.veto_triggered is None
    assert "STOPPED:" not in synthesis.founder_summary["verdict"]
    assert "VETO TRIGGERED" not in synthesis.summary


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
async def test_mock_trinity_withholds_all_synthetic_decision_fields(app, caplog):
    with caplog.at_level(logging.WARNING, logger="verifimind_mcp.server"):
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
    quality_records = [
        record
        for record in caplog.records
        if "Trinity quality gate withheld aggregate confidence" in record.message
    ]
    assert len(quality_records) == 1
    assert "x=mock z=mock cs=mock overall=synthetic" in quality_records[0].message
    assert "Integrity probe" not in quality_records[0].message


@pytest.mark.asyncio
async def test_history_write_failure_is_not_reported_as_saved(app, monkeypatch):
    monkeypatch.setattr(server, "load_validation_history", server._empty_validation_history)
    monkeypatch.setattr(server, "save_validation_history", lambda _history: False)

    payload = await call(app, "run_full_trinity", {
        "concept_name": "History truth probe",
        "concept_description": "Verify failed persistence is never claimed",
        "llm_provider": "mock",
        "save_to_history": True,
    })

    assert payload["saved_to_history"] is False
    assert "could not be persisted" in payload["_history_warning"]
    assert payload["history_retention"]["max_entries"] == 20


@pytest.mark.asyncio
async def test_history_write_success_reports_bounded_contract(app, monkeypatch):
    captured = {}

    def save(history):
        captured.update(history)
        return True

    monkeypatch.setattr(server, "load_validation_history", server._empty_validation_history)
    monkeypatch.setattr(server, "save_validation_history", save)

    payload = await call(app, "run_full_trinity", {
        "concept_name": "History contract probe",
        "concept_description": "Verify successful opt-in persistence receipt",
        "llm_provider": "mock",
        "save_to_history": True,
    })

    assert payload["saved_to_history"] is True
    assert "_history_warning" not in payload
    assert payload["history_retention"] == server.validation_history_retention_contract()
    assert len(captured["validations"]) == 1


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


def test_cs_standard_evidence_fields_are_quality_required_with_full_exemptions():
    cs_schema = CSAgentAnalysis.model_json_schema()
    standard_evidence = {
        "threat_level",
        "agentic_threats",
        "reasoning_layer_findings",
    }
    full_only = {
        "stages_completed",
        "dimensions_evaluated",
        "macp_security_assessment",
        "standards_referenced",
    }
    assert all(
        cs_schema["properties"][field].get("quality_required") is True
        for field in standard_evidence
    )
    assert all(
        cs_schema["properties"][field].get("quality_required") is not True
        for field in full_only
    )

    x_schema = XAgentAnalysis.model_json_schema()
    x_enhancements = {
        "competitive_position",
        "competitive_analysis",
        "next_steps",
        "research_prompts",
        "market_competition",
    }
    assert all(
        x_schema["properties"][field].get("quality_required") is not True
        for field in x_enhancements
    )

    incomplete = GeminiProvider._quality_incomplete_fields(
        {field: None for field in standard_evidence}, cs_schema
    )
    assert set(incomplete) == standard_evidence


@pytest.mark.asyncio
async def test_shared_agent_boundary_downgrades_evidence_incomplete_byok_cs():
    class EvidenceIncompleteProvider:
        def get_model_name(self):
            return "test/evidence-incomplete"

        async def generate(self, *args, **kwargs):
            return {
                "content": {
                    "reasoning_steps": [
                        {"step_number": 1, "thought": "analysis", "confidence": 0.9}
                    ],
                    "security_score": 9.0,
                    "vulnerabilities": [],
                    "attack_vectors": [],
                    "security_recommendations": [],
                    "socratic_questions": ["What fails?"],
                    "recommendation": "proceed",
                    "confidence": 0.9,
                },
                "usage": {},
                "_inference_quality": "real",
            }

    result = await CSAgent(llm_provider=EvidenceIncompleteProvider()).analyze(
        Concept(name="probe", description="probe")
    )

    assert result._inference_quality == "partial"
    assert set(result._schema_incomplete_fields) == {
        "threat_level",
        "agentic_threats",
        "reasoning_layer_findings",
    }


def test_result_optional_fields_have_explicit_null_defaults():
    from verifimind_mcp.models.results import (
        TrinitySynthesis,
        ValidationHistoryEntry,
    )

    for field_name in (
        "innovation_score",
        "ethics_score",
        "security_score",
        "overall_score",
        "confidence",
    ):
        field = TrinitySynthesis.model_fields[field_name]
        assert field.is_required() is False
        assert field.default is None

    for field_name in ("overall_score", "veto_triggered"):
        field = ValidationHistoryEntry.model_fields[field_name]
        assert field.is_required() is False
        assert field.default is None


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


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("tool_name", "registry_method", "arguments"),
    [
        ("list_prompt_templates", "list_templates", {}),
        ("get_prompt_template", "get_template", {"template_id": "probe"}),
        ("export_prompt_template", "get_template", {"template_id": "probe"}),
        ("get_template_statistics", "get_statistics", {}),
    ],
)
async def test_public_template_read_errors_do_not_reflect_internal_exceptions(
    app, monkeypatch, tool_name, registry_method, arguments
):
    secret = "SENSITIVE-TEMPLATE-INTERNAL"

    def fail(*args, **kwargs):
        raise RuntimeError(secret)

    monkeypatch.setattr(TemplateRegistry, registry_method, fail)
    payload = await call(app, tool_name, arguments)

    assert payload["status"] == "error"
    assert payload["error"] == server.TEMPLATE_READ_UNAVAILABLE
    assert secret not in json.dumps(payload)


def test_master_prompt_import_error_does_not_reflect_internal_exception(monkeypatch):
    secret = "SENSITIVE-MASTER-PROMPT-INTERNAL"
    original_import = builtins.__import__

    def fail_concepts_import(name, *args, **kwargs):
        if "models.concepts" in name:
            raise RuntimeError(secret)
        return original_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", fail_concepts_import)
    payload = server.load_master_prompt()

    assert payload == server.MASTER_PROMPT_UNAVAILABLE
    assert secret not in payload


def test_validation_history_error_does_not_reflect_internal_path(monkeypatch):
    secret = "SENSITIVE-HISTORY-PATH"

    class UnreadableHistoryPath:
        def exists(self):
            return True

        def __fspath__(self):
            raise PermissionError(secret)

    monkeypatch.setattr(server, "HISTORY_PATH", UnreadableHistoryPath())

    payload = server.load_validation_history()

    assert payload == {
        "error": server.VALIDATION_HISTORY_UNAVAILABLE,
        "validations": [],
    }
    assert secret not in json.dumps(payload)


def test_http_500_error_does_not_reflect_exception_detail():
    import http_server

    secret = "SENSITIVE-HTTP-INTERNAL"
    response = asyncio.run(
        http_server.http_exception_handler(
            None,
            SimpleNamespace(status_code=500, detail=secret),
        )
    )
    payload = json.loads(response.body)

    assert payload["error"] == "Internal server error"
    assert secret not in json.dumps(payload)


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
    target, error = import_url._validate_resolved_target(
        "https://raw.githubusercontent.com/user/repo/main/template.json"
    )
    assert target is None
    assert error == "Template host resolved to a non-public address"


def test_template_host_allowlist_is_exact():
    assert import_url.ALLOWED_TEMPLATE_HOSTS == frozenset({
        "gist.github.com",
        "gist.githubusercontent.com",
        "raw.githubusercontent.com",
    })


def _public_template_dns_result():
    return [
        (
            import_url.socket.AF_INET,
            import_url.socket.SOCK_STREAM,
            import_url.socket.IPPROTO_TCP,
            "",
            ("93.184.216.34", 443),
        )
    ]


def test_async_url_fetch_uses_only_the_validated_dns_result(monkeypatch):
    url = "https://raw.githubusercontent.com/user/repo/main/template.json"
    dns_calls = []
    captured = {}

    def resolve_once(*args, **kwargs):
        dns_calls.append((args, kwargs))
        return _public_template_dns_result()

    class FakeContent:
        async def iter_chunked(self, _size):
            yield b"{}"

    class FakeResponse:
        status = 200
        reason = "OK"
        content_length = 2
        content = FakeContent()

        async def __aenter__(self):
            return self

        async def __aexit__(self, *_args):
            return False

    class FakeSession:
        def __init__(self, *, connector, timeout):
            captured["connector"] = connector
            captured["timeout"] = timeout

        async def __aenter__(self):
            return self

        async def __aexit__(self, *_args):
            return False

        def get(self, requested_url, *, allow_redirects):
            captured["url"] = requested_url
            captured["allow_redirects"] = allow_redirects
            return FakeResponse()

    def fake_connector(**kwargs):
        captured["connector_kwargs"] = kwargs
        return SimpleNamespace(**kwargs)

    fake_aiohttp = SimpleNamespace(
        TCPConnector=fake_connector,
        ClientTimeout=lambda **kwargs: SimpleNamespace(**kwargs),
        ClientSession=FakeSession,
    )

    monkeypatch.setattr(import_url.socket, "getaddrinfo", resolve_once)
    monkeypatch.setitem(sys.modules, "aiohttp", fake_aiohttp)

    content, error = asyncio.run(import_url._fetch_url_content(url))

    assert content == "{}"
    assert error is None
    assert len(dns_calls) == 1
    assert captured["url"] == url
    assert captured["allow_redirects"] is False
    assert captured["connector_kwargs"]["use_dns_cache"] is False

    resolver = captured["connector_kwargs"]["resolver"]
    resolved = asyncio.run(
        resolver.resolve("raw.githubusercontent.com", 443, import_url.socket.AF_UNSPEC)
    )
    assert [item["host"] for item in resolved] == ["93.184.216.34"]
    assert len(dns_calls) == 1


def test_sync_pinned_connection_uses_numeric_socket_and_original_sni(monkeypatch):
    url = "https://raw.githubusercontent.com/user/repo/main/template.json"
    dns_calls = []

    def resolve_once(*args, **kwargs):
        dns_calls.append((args, kwargs))
        return _public_template_dns_result()

    monkeypatch.setattr(import_url.socket, "getaddrinfo", resolve_once)
    target, error = import_url._validate_resolved_target(url)
    assert error is None
    assert target is not None

    captured = {}

    class FakeSocket:
        def settimeout(self, timeout):
            captured["timeout"] = timeout

        def bind(self, source_address):
            captured["source_address"] = source_address

        def connect(self, sockaddr):
            captured["sockaddr"] = sockaddr

        def setsockopt(self, *_args):
            pass

        def close(self):
            captured["closed"] = True

    class FakeTLSContext:
        verify_mode = import_url.ssl.CERT_REQUIRED
        check_hostname = True

        def wrap_socket(self, sock, *, server_hostname):
            captured["server_hostname"] = server_hostname
            return sock

    monkeypatch.setattr(
        import_url.socket,
        "socket",
        lambda family, socktype, protocol: FakeSocket(),
    )
    connection = import_url._PinnedHTTPSConnection(
        target.hostname,
        target.port,
        pinned_target=target,
        context=FakeTLSContext(),
        timeout=3,
    )

    connection.connect()

    assert captured["sockaddr"] == ("93.184.216.34", 443)
    assert captured["server_hostname"] == "raw.githubusercontent.com"
    assert len(dns_calls) == 1
    connection.close()


def test_sync_url_fetch_uses_pinned_connection_and_original_host(monkeypatch):
    url = "https://raw.githubusercontent.com/user/repo/main/template.json?raw=1"
    dns_calls = []
    captured = {}

    def resolve_once(*args, **kwargs):
        dns_calls.append((args, kwargs))
        return _public_template_dns_result()

    class FakeResponse:
        status = 200
        reason = "OK"

        @staticmethod
        def getheader(_name):
            return "2"

        @staticmethod
        def read(_limit):
            return b"{}"

    class FakeConnection:
        def __init__(
            self,
            host,
            port,
            *,
            pinned_target,
            context,
            timeout,
        ):
            captured["host"] = host
            captured["port"] = port
            captured["pinned_target"] = pinned_target
            captured["timeout"] = timeout

        def request(self, method, target, *, headers):
            captured["method"] = method
            captured["request_target"] = target
            captured["headers"] = headers

        @staticmethod
        def getresponse():
            return FakeResponse()

        def close(self):
            captured["closed"] = True

    monkeypatch.setattr(import_url.socket, "getaddrinfo", resolve_once)
    monkeypatch.setattr(import_url, "_PinnedHTTPSConnection", FakeConnection)

    content, error = import_url._fetch_url_content_sync(url)

    assert content == "{}"
    assert error is None
    assert len(dns_calls) == 1
    assert captured["host"] == "raw.githubusercontent.com"
    assert captured["pinned_target"].addresses[0].ip == "93.184.216.34"
    assert captured["request_target"] == "/user/repo/main/template.json?raw=1"
    assert captured["headers"] == {"Host": "raw.githubusercontent.com"}
    assert captured["closed"] is True


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
    master_prompt = next(
        resource
        for resource in card["resources"]
        if resource["uri"] == "genesis://config/master_prompt"
    )
    routing = get_public_contract()["free_tier_routing"]

    assert card["version"] == "0.5.62"
    assert "8 MCP tools are active" in card["description"]
    assert "5 tools" in card["description"]
    for agent_id in ("X", "Z", "CS"):
        assert routing[agent_id]["model"] in card["description"]
        assert routing[agent_id]["provider"] in card["description"]
    assert run_full["inputSchema"]["properties"]["save_to_history"]["default"] is False
    assert "At most 20 newest entries" in (
        run_full["inputSchema"]["properties"]["save_to_history"]["description"]
    )
    assert "PROCEED/REFINE/HALT" not in run_full["description"]
    assert "proceed_with_caution" in run_full["description"]
    assert master_prompt["name"] == "Genesis Methodology — Live Production Prompts"
    assert "v4.2" not in master_prompt["name"]
    history_all = next(
        resource
        for resource in card["resources"]
        if resource["uri"] == "genesis://history/all"
    )
    assert "Bounded aggregate statistics" in history_all["description"]
    assert "Complete validation history" not in history_all["description"]


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
