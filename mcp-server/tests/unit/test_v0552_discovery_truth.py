"""
v0.5.52 — Discovery Truth Repair (T S87 Work Package A, P0)
===========================================================

T's S87 verification found the v0.5.51 truth contract only PARTIALLY projected:
/setup still claimed "Gemini 1.5 Flash", "Claude (if BYOK) or Gemini" hosted
Z/CS, a "X (Gemini) -> Z (Claude/Gemini) -> ..." flow, stale "Pioneer" tier
stamps on the free coordination tools, and a wrong tool composition; the
startup banner carried the same v0.3-era routing story.

WP-A exit: contract tests prove /health, /setup, MCP config, and root agree
with the generated contract. These tests render the ACTUAL handlers and scan
for the stale tokens by name — the audit's findings become permanent CI.
"""

import asyncio
import json

import pytest

from verifimind_mcp.contract import get_public_contract


class _URL:
    scheme = "https"
    netloc = "verifimind.ysenseai.org"


class _Req:
    headers = {"host": "verifimind.ysenseai.org"}
    url = _URL()


def _render(handler):
    import http_server
    response = asyncio.run(handler(_Req()))
    return json.loads(response.body)


STALE_TOKENS = (
    "Gemini 1.5", "gemini-1.5", "Gemini 2.0", "gemini-2.0",
    "Claude/Gemini",              # the false hosted Z/CS routing story
    "Pioneer tier",               # pre-v0.5.28 tier stamp on free tools
    "Upgrade to Pioneer",         # false paywall claim (free since v0.5.28)
    "10 Trinity + 3 Coordination",  # wrong tool composition
)


# ---------------------------------------------------------------------------
# /setup agrees with the contract (the WP-A repair)
# ---------------------------------------------------------------------------

def test_setup_carries_no_stale_tokens():
    import http_server
    text = json.dumps(_render(http_server.setup_handler))
    for token in STALE_TOKENS:
        assert token not in text, f"stale claim resurfaced in /setup: {token}"


def test_setup_trinity_descriptions_project_the_contract():
    import http_server
    routing = get_public_contract()["free_tier_routing"]
    tools = _render(http_server.setup_handler)["available_tools"]["trinity"]
    assert routing["X"]["model"] in tools["consult_agent_x"]["powered_by"]
    assert routing["Z"]["model"] in tools["consult_agent_z"]["powered_by"]
    assert routing["CS"]["model"] in tools["consult_agent_cs"]["powered_by"]
    flow = tools["run_full_trinity"]["flow"]
    for agent in ("X", "Z", "CS"):
        assert f"{routing[agent]['provider']}/{routing[agent]['model']}" in flow


def test_setup_coordination_tools_marked_free():
    import http_server
    coord = _render(http_server.setup_handler)["available_tools"]["coordination"]
    for tool in coord.values():
        assert "Free" in tool["tier"]


# ---------------------------------------------------------------------------
# The whole discovery source is stale-free (source-level backstop)
# ---------------------------------------------------------------------------

def test_http_server_source_carries_no_stale_routing_story():
    import http_server, inspect
    src = inspect.getsource(http_server)
    for token in STALE_TOKENS:
        assert token not in src, f"stale claim in http_server source: {token}"


# ---------------------------------------------------------------------------
# Cross-surface agreement: /health, /setup, root all serve ONE truth
# ---------------------------------------------------------------------------

def test_health_and_setup_agree_on_the_x_model():
    import http_server
    health = _render(http_server.health_handler)
    setup = _render(http_server.setup_handler)
    x_model = get_public_contract()["free_tier_routing"]["X"]["model"]
    assert health["free_tier_routing"]["X"]["model"] == x_model
    assert x_model in setup["available_tools"]["trinity"]["consult_agent_x"]["powered_by"]


def test_versions_agree_across_surfaces():
    import http_server
    contract_version = get_public_contract()["version"]
    assert _render(http_server.health_handler)["version"] == contract_version
    assert http_server.SERVER_VERSION == contract_version == "0.5.53"
