"""
v0.5.43 Foundation Integrity — regression tests for the P0 fixes.

Covers:
- P0-1: Z veto fail-safe polarity on DEGRADED real inference (partial/fallback)
- P0-2: cross-tenant validation-history leak — resources expose no raw concept text
- P0-3: master_prompt resource serves the live production prompts (no stale PII)
- P1-4: project_info advertises the real SERVER_VERSION
"""

from types import SimpleNamespace

import pytest

from verifimind_mcp.utils.synthesis import (
    calculate_overall_score,
    determine_recommendation,
)
from verifimind_mcp import server


def _x(score=8.0):
    return SimpleNamespace(innovation_score=score, strategic_value=score)


def _z(ethics=9.0, veto=False, quality="real"):
    ns = SimpleNamespace(ethics_score=ethics, veto_triggered=veto)
    ns._inference_quality = quality
    return ns


def _cs(security=9.0):
    return SimpleNamespace(security_score=security)


# ---------- P0-1: fail-safe polarity ----------

def test_clean_high_score_proceeds_when_inference_real():
    """Baseline: a clean, real-inference run with high scores still proceeds."""
    score = calculate_overall_score(_x(9.0), _z(9.0), _cs(9.0), z_quality="real")
    rec = determine_recommendation(score, _z(9.0), _cs(9.0), z_quality="real")
    assert rec == "proceed"
    assert score >= 7.5


@pytest.mark.parametrize("degraded", ["partial", "fallback"])
def test_degraded_z_inference_never_auto_passes(degraded):
    """A high-scoring run must NOT proceed if Z inference was degraded — the veto
    flag and ethics score could be synthesized schema defaults."""
    z = _z(ethics=9.0, veto=False, quality=degraded)
    score = calculate_overall_score(_x(9.0), z, _cs(9.0), z_quality=degraded)
    rec = determine_recommendation(score, z, _cs(9.0), z_quality=degraded)
    assert rec == "revise", f"degraded={degraded} must cap at revise, got {rec}"
    assert score <= 4.0, f"degraded score must stay out of proceed bands, got {score}"


def test_mock_inference_excluded_from_failsafe():
    """'mock' is test-mode with its own synthetic warning — it must NOT trip the
    degraded-inference fail-safe (would break every mock-based test)."""
    z = _z(ethics=9.0, veto=False, quality="mock")
    score = calculate_overall_score(_x(9.0), z, _cs(9.0), z_quality="mock")
    rec = determine_recommendation(score, z, _cs(9.0), z_quality="mock")
    assert rec == "proceed"


def test_veto_still_rejects_regardless_of_quality():
    z = _z(ethics=2.0, veto=True, quality="real")
    score = calculate_overall_score(_x(9.0), z, _cs(9.0), z_quality="real")
    rec = determine_recommendation(score, z, _cs(9.0), z_quality="real")
    assert rec == "reject"
    assert score <= 3.0


# ---------- P0-2: history resources leak no raw concept text ----------

def test_latest_validation_resource_omits_concept_text(monkeypatch):
    leaky = {
        "validation_id": "abc123",
        "concept_name": "SECRET STARTUP IDEA",
        "concept_description": "confidential description that must not leak",
        "completed_at": "2026-06-11T00:00:00",
        "synthesis": {"recommendation": "proceed", "overall_score": 8.0, "veto_triggered": False},
    }
    monkeypatch.setattr(server, "get_latest_validation", lambda: leaky)
    out = server._redacted_latest_validation()
    blob = str(out)
    assert "SECRET STARTUP IDEA" not in blob
    assert "confidential description" not in blob
    assert out["recommendation"] == "proceed"
    assert out["validation_id"] == "abc123"


def test_aggregate_stats_omit_concept_text(monkeypatch):
    history = {
        "validations": [
            {"concept_name": "Idea A", "concept_description": "desc A",
             "synthesis": {"recommendation": "proceed", "veto_triggered": False}},
            {"concept_name": "Idea B", "concept_description": "desc B",
             "synthesis": {"recommendation": "reject", "veto_triggered": True}},
        ],
        "metadata": {"last_updated": "2026-06-11"},
    }
    monkeypatch.setattr(server, "load_validation_history", lambda: history)
    out = server._aggregate_validation_stats()
    blob = str(out)
    assert "Idea A" not in blob and "Idea B" not in blob
    assert "desc A" not in blob and "desc B" not in blob
    assert out["total_validations"] == 2
    assert out["veto_count"] == 1
    assert out["recommendation_distribution"] == {"proceed": 1, "reject": 1}


# ---------- P0-3: master_prompt is live + free of stale PII/targets ----------

def test_master_prompt_serves_live_prompts():
    doc = server.load_master_prompt()
    assert "Genesis Methodology" in doc
    # Real agent roles present
    assert "X Intelligent" in doc and "Z Guardian" in doc and "CS Security" in doc
    # Reflects current server version
    assert server.SERVER_VERSION in doc


def test_master_prompt_drops_stale_internal_artifacts():
    doc = server.load_master_prompt()
    # The old v1.1 collection embedded a personal email and internal revenue target
    assert "creator35lwb@gmail.com" not in doc
    assert "5亿美元" not in doc  # internal 2030 revenue target
    assert "200万用户" not in doc


# ---------- P1-4: project_info version currency ----------

def test_project_info_reports_real_version():
    info = server.get_project_info()
    assert info["mcp_server_version"] == server.SERVER_VERSION
