"""
v0.5.51 — Public Truth Contract (T S85 audit, D-85-2) + Gemini currency
=======================================================================

T's Live Publication Truth Audit found "discovery-contract drift": /setup, MCP
config, /health, and landing copy each hand-maintained their own model/routing
story and disagreed (down to a "Gemini 2.0 Flash" claim). The fix is
structural: `verifimind_mcp.contract.get_public_contract()` is the single
generated truth, and every surface PROJECTS from it.

These tests are the anti-drift gate: they assert the surfaces AGREE with the
contract, so the next model migration that misses a surface fails CI instead
of shipping a contradiction. (Cross-surface consistency: a defect can live
between artifacts and inside none.)
"""

import json

import pytest

from verifimind_mcp.contract import get_public_contract, free_tier_models_display
from verifimind_mcp.llm.provider import (
    PROVIDER_CONFIGS,
    PROVIDER_DEFAULT_GEMINI_MODEL,
    PROVIDER_DEFAULT_GROQ_MODEL,
)


# ---------------------------------------------------------------------------
# Contract shape + derivation from live constants
# ---------------------------------------------------------------------------

def test_contract_version_matches_server_constant():
    from verifimind_mcp.server import SERVER_VERSION
    assert get_public_contract()["version"] == SERVER_VERSION == "0.5.53"


def test_contract_routing_covers_all_three_agents():
    routing = get_public_contract()["free_tier_routing"]
    assert set(routing) == {"X", "Z", "CS"}
    for entry in routing.values():
        assert entry["provider"] and entry["model"] and entry["fallback_provider"]


def test_x_seat_routes_to_gemini_default():
    x = get_public_contract()["free_tier_routing"]["X"]
    assert x["provider"] == "gemini"
    assert x["model"] == PROVIDER_DEFAULT_GEMINI_MODEL


def test_z_cs_route_to_groq_default():
    routing = get_public_contract()["free_tier_routing"]
    for aid in ("Z", "CS"):
        assert routing[aid]["provider"] == "groq"
        assert routing[aid]["model"] == PROVIDER_DEFAULT_GROQ_MODEL


def test_byok_providers_mirror_provider_configs():
    byok = get_public_contract()["byok_providers"]
    assert "mock" not in byok and "ollama" not in byok
    for name, cfg in byok.items():
        assert cfg["default_model"] == PROVIDER_CONFIGS[name]["default_model"]
        assert cfg["models"] == list(PROVIDER_CONFIGS[name]["models"])


def test_contract_is_json_serializable():
    json.dumps(get_public_contract())


# ---------------------------------------------------------------------------
# Gemini currency (v0.5.51) — the migration this release ships
# ---------------------------------------------------------------------------

def test_gemini_default_is_35_flash_lite():
    assert PROVIDER_DEFAULT_GEMINI_MODEL == "gemini-3.5-flash-lite"
    assert PROVIDER_CONFIGS["gemini"]["default_model"] == "gemini-3.5-flash-lite"


def test_gemini_menu_current():
    models = PROVIDER_CONFIGS["gemini"]["models"]
    assert "gemini-3.6-flash" in models
    assert "gemini-3.5-flash" in models
    assert "gemini-2.5-flash" in models       # retained for continuity
    assert "gemini-2.0-flash" not in models   # the drift the audit caught


def test_gemini_still_free_tier():
    assert PROVIDER_CONFIGS["gemini"]["free_tier"] is True


# ---------------------------------------------------------------------------
# Surface agreement — the anti-drift gate (D-85-2)
# ---------------------------------------------------------------------------

def test_health_projects_the_routing_contract():
    import http_server
    import asyncio
    response = asyncio.run(http_server.health_handler(None))
    payload = json.loads(response.body)
    assert payload["free_tier_routing"] == get_public_contract()["free_tier_routing"]
    assert payload["version"] == get_public_contract()["version"]


def test_display_list_is_generated_not_handwritten():
    display = free_tier_models_display()
    assert any(PROVIDER_DEFAULT_GEMINI_MODEL in item for item in display)
    assert any(PROVIDER_DEFAULT_GROQ_MODEL in item for item in display)


def test_server_card_copy_carries_current_gemini_default():
    import http_server
    assert PROVIDER_DEFAULT_GEMINI_MODEL in http_server.GEMINI_DEFAULT_DISPLAY
    assert "2.0" not in http_server.GEMINI_DEFAULT_DISPLAY


def test_no_stale_gemini_claims_in_http_server_source():
    """The audit's smoking gun ('Gemini 2.0 Flash') must never return: no
    hand-written stale Gemini version strings in the discovery surfaces."""
    import http_server, inspect
    src = inspect.getsource(http_server)
    assert "Gemini 2.0 Flash" not in src
    assert "Gemini 2.5 Flash" not in src  # display copy must come from the constant


# ---------------------------------------------------------------------------
# Coordination template currency (#77): MACP v2.5 stamp
# ---------------------------------------------------------------------------

def test_handoff_template_stamps_macp_25():
    from verifimind_mcp.coordination.handoff_store import build_handoff_record
    from verifimind_mcp.coordination.handoff_formatter import format_handoff_markdown
    record = build_handoff_record(
        agent_id="RNA", session_type="contract-test",
        completed=["x"], decisions=[], artifacts=[], pending=[], blockers=[],
        next_agent=None,
    )
    assert record["macp_version"] == "2.5"
    md = format_handoff_markdown(record)
    assert 'MACP Version: 2.5 "Loop Engineering"' in md
    assert "2.2" not in md
