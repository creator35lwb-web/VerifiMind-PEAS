"""
v0.5.50 Robustness Pass — mock-provider E2E walk of the MCP tool bodies
=======================================================================

Foundation Inspection pass 1 (Alton S70 mandate, T scoping on Hub #81).
The architecture map found the live inference path is the coverage cold zone
(server.py tool bodies 22%, synthesis 24%, provider generate() 43%) because
unit tests mock at the LLM boundary and never walk the REGISTERED tool bodies.

This harness walks them end-to-end in-process (fastmcp.Client, no live APIs):
  - all 4 Trinity tools on llm_provider='mock' -> structured success contract
  - template + coordination tools -> registry/store paths
  - representative provider failures (T's list): timeout, TPM-413 admission,
    malformed/underfilled model output, degraded-Z (the v0.5.43 veto fail-safe:
    cap at REVISE + inference_warning)

A failing test here is a FINDING for the pass, not necessarily a same-day fix.
"""

import json

import pytest
from unittest.mock import patch

from fastmcp import Client

from verifimind_mcp.server import create_http_server
from verifimind_mcp.llm.provider import MockProvider


CONCEPT = {
    "concept_name": "Robustness walk probe",
    "concept_description": "A minimal concept used to exercise the registered tool bodies end-to-end with the mock provider.",
}


@pytest.fixture(scope="module")
def app():
    return create_http_server()


def payload_of(result):
    """Extract the tool's dict payload from a fastmcp CallToolResult."""
    data = getattr(result, "data", None)
    if isinstance(data, dict):
        return data
    for block in getattr(result, "content", []) or []:
        text = getattr(block, "text", None)
        if text:
            try:
                return json.loads(text)
            except json.JSONDecodeError:
                continue
    raise AssertionError(f"no dict payload in tool result: {result!r}")


async def call(app, name, args):
    async with Client(app) as client:
        return payload_of(await client.call_tool(name, args))


# ---------------------------------------------------------------------------
# Walk 1 — Trinity tools on the mock provider (structured success contract)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_consult_x_mock_walk(app):
    p = await call(app, "consult_agent_x", {**CONCEPT, "llm_provider": "mock"})
    assert p.get("agent"), p
    assert "innovation_score" in p and "recommendation" in p
    assert p.get("_inference_quality") == "mock"
    assert p.get("_warning"), "mock inference must carry the transparency warning"
    assert p.get("_server_version")


@pytest.mark.asyncio
async def test_consult_z_mock_walk(app):
    p = await call(app, "consult_agent_z", {**CONCEPT, "llm_provider": "mock"})
    assert "ethics_score" in p, p
    assert "veto_triggered" in p
    assert p.get("_inference_quality") == "mock"


@pytest.mark.asyncio
async def test_consult_cs_mock_walk(app):
    p = await call(app, "consult_agent_cs", {**CONCEPT, "llm_provider": "mock"})
    assert "security_score" in p, p
    assert p.get("_inference_quality") == "mock"


@pytest.mark.asyncio
async def test_run_full_trinity_mock_walk(app):
    p = await call(app, "run_full_trinity", {**CONCEPT, "llm_provider": "mock"})
    assert "x_analysis" in p and "z_analysis" in p and "cs_analysis" in p, p
    assert "synthesis" in p and "recommendation" in p["synthesis"]
    chain = p.get("_agent_chain_status", {})
    assert set(chain) == {"x_agent", "z_agent", "cs_agent"}, chain
    assert p.get("_overall_quality"), p


# ---------------------------------------------------------------------------
# Walk 2 — template + coordination tools (no LLM in the path)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_template_tools_walk(app):
    listing = await call(app, "list_prompt_templates", {})
    assert "templates" in listing or "count" in listing or listing, listing

    stats = await call(app, "get_template_statistics", {})
    assert stats, stats


@pytest.mark.asyncio
async def test_coordination_tools_walk(app, tmp_path):
    created = await call(app, "coordination_handoff_create", {
        "agent_id": "RNA-TEST",
        "session_type": "robustness-walk",
        "completed": ["harness probe"],
        "decisions": [],
        "artifacts": [],
        "pending": [],
        "blockers": [],
    })
    assert created.get("status") == "success", created
    assert created.get("handoff_id")

    status = await call(app, "coordination_team_status", {})
    assert status, status


# ---------------------------------------------------------------------------
# Walk 3 — representative provider failures (T's list)
# ---------------------------------------------------------------------------

class _RaisingProvider(MockProvider):
    """Mock provider whose generate() raises a chosen exception."""

    def __init__(self, exc):
        super().__init__()
        self._exc = exc

    async def generate(self, *a, **kw):
        raise self._exc


class _QualityProvider(MockProvider):
    """Mock provider that stamps a chosen _inference_quality on its output."""

    def __init__(self, quality):
        super().__init__()
        self._quality = quality

    async def generate(self, *a, **kw):
        out = await super().generate(*a, **kw)
        out["_inference_quality"] = self._quality
        return out


@pytest.mark.asyncio
async def test_provider_timeout_returns_structured_error(app):
    with patch(
        "verifimind_mcp.config_helper.create_ephemeral_provider",
        return_value=_RaisingProvider(TimeoutError("provider timed out")),
    ):
        p = await call(app, "consult_agent_x", {**CONCEPT, "llm_provider": "mock"})
    assert p.get("status") == "error" or "error" in p, p
    assert "timed out" in json.dumps(p), p


@pytest.mark.asyncio
async def test_tpm_413_admission_returns_structured_error(app):
    exc = Exception(
        "Error code: 413 - {'error': {'message': 'Request too large for model on tokens per minute (TPM)'}}"
    )
    with patch(
        "verifimind_mcp.config_helper.create_ephemeral_provider",
        return_value=_RaisingProvider(exc),
    ):
        p = await call(app, "run_full_trinity", {**CONCEPT, "llm_provider": "mock"})
    text = json.dumps(p)
    assert "413" in text or p.get("status") == "error", p
    # contract: a provider admission failure must never surface as a raw crash
    assert "Traceback" not in text


@pytest.mark.asyncio
async def test_degraded_z_caps_recommendation_and_warns(app):
    """v0.5.43 ethics-veto fail-safe: degraded Z inference (partial/fallback)
    caps the synthesis recommendation at REVISE and emits inference_warning."""
    from verifimind_mcp import config_helper as ch

    real = ch.get_agent_provider

    def per_agent(agent_id, ctx=None):
        if agent_id == "Z":
            return _QualityProvider("fallback")
        return MockProvider()

    with patch("verifimind_mcp.config_helper.get_agent_provider", side_effect=per_agent):
        p = await call(app, "run_full_trinity", CONCEPT)

    syn = p.get("synthesis", {})
    rec = str(syn.get("recommendation", "")).lower()
    assert rec and "proceed" != rec, f"degraded Z must not yield clean PROCEED: {syn}"
    warning = p.get("inference_warning") or syn.get("inference_warning")
    assert warning, f"degraded Z must emit inference_warning: {p.keys()}"


@pytest.mark.asyncio
async def test_underfilled_model_output_degrades_not_crashes(app):
    """Provider returns schema-underfilled content -> agent fills defaults and
    stamps degraded quality instead of raising."""

    class _Underfilled(MockProvider):
        async def generate(self, *a, **kw):
            return {
                "content": {"reasoning_steps": []},  # missing required analysis fields
                "usage": {"input_tokens": 1, "output_tokens": 1, "total_tokens": 2},
                "_inference_quality": "partial",
            }

    with patch(
        "verifimind_mcp.config_helper.create_ephemeral_provider",
        return_value=_Underfilled(),
    ):
        p = await call(app, "consult_agent_x", {**CONCEPT, "llm_provider": "mock"})
    assert "error" in p or p.get("_inference_quality") in ("partial", "fallback", "mock"), p
