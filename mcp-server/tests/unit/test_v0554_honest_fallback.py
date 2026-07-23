"""
v0.5.54 — Honest Fallback Semantics (T S88 review, D-88-1)
==========================================================

T's S88 review narrowed the WP-A exit: the route/version projection passed,
but discovery still described construction-time provider selection as "smart
fallback" — wording that reads as request-time failover, behavior the runtime
does not execute (runtime failover is WP-B, unbuilt). MCP-config Z/CS
descriptions carried a v0.3-era "Claude if BYOK, else Gemini FREE" story,
hosted-option copy was Gemini-only, and Cerebras copy carried a blanket
"FREE — 1M tokens/day" guarantee that is account-dependent in reality.

These tests enforce T's exit criteria 1-7: the contract names the distinction
(construction_fallback vs runtime_failover_enabled=False until WP-B deploys
with failure evidence), every generated surface projects it, and both
required-current and forbidden-stale strings are asserted. Criterion 8 (live
GET receipt) lives on the release evidence, not in CI.
"""

import asyncio
import json

from verifimind_mcp.contract import get_public_contract


class _URL:
    scheme = "https"
    netloc = "verifimind.ysenseai.org"


class _Req:
    headers = {"host": "verifimind.ysenseai.org"}
    url = _URL()


def _render(handler):
    response = asyncio.run(handler(_Req()))
    return json.loads(response.body)


# Claim shapes T S88 forbade (matched case-insensitively where noted).
FORBIDDEN_RUNTIME_CLAIMS = ("smart fallback", "smart_fallback")
FORBIDDEN_STALE_COPY = (
    "Claude if BYOK",              # v0.3-era hosted Z/CS routing story
    "1M tokens/day",               # blanket Cerebras quota guarantee
    "developer-provided Gemini key",  # Gemini-only hosted-option copy
)


def _assert_clean(text, surface):
    lowered = text.lower()
    for claim in FORBIDDEN_RUNTIME_CLAIMS:
        assert claim not in lowered, f"runtime-failover claim in {surface}: {claim}"
    for claim in FORBIDDEN_STALE_COPY:
        assert claim not in text, f"stale copy in {surface}: {claim}"


# ---------------------------------------------------------------------------
# The contract itself names the semantics (criteria 1-2)
# ---------------------------------------------------------------------------

def test_contract_runtime_failover_explicitly_false():
    contract = get_public_contract()
    assert contract["runtime_failover_enabled"] is False
    assert "construction" in contract["fallback_semantics"]
    assert "does not fail over" in contract["fallback_semantics"]


def test_contract_routing_names_construction_fallback():
    for entry in get_public_contract()["free_tier_routing"].values():
        assert "construction_fallback" in entry
        assert "fallback_provider" not in entry  # the ambiguous name is gone


# ---------------------------------------------------------------------------
# /health projects the distinction (criteria 1-3)
# ---------------------------------------------------------------------------

def test_health_serves_runtime_failover_disabled():
    import http_server
    payload = _render(http_server.health_handler)
    assert payload["runtime_failover_enabled"] is False
    assert payload["fallback_semantics"] == get_public_contract()["fallback_semantics"]


def test_health_features_are_honest():
    import http_server
    features = _render(http_server.health_handler)["features"]
    assert features["construction_fallback"] is True
    assert features["runtime_failover"] is False
    assert "smart_fallback" not in features


def test_health_body_carries_no_forbidden_claims():
    import http_server
    response = asyncio.run(http_server.health_handler(_Req()))
    _assert_clean(response.body.decode(), "/health")


# ---------------------------------------------------------------------------
# MCP config: current hosted descriptions, no stale copy (criteria 4-6)
# ---------------------------------------------------------------------------

def test_mcp_config_tool_descriptions_project_the_contract():
    import http_server
    routing = get_public_contract()["free_tier_routing"]
    tools = {t["name"]: t for t in _render(http_server.mcp_config_handler)["tools"]}
    for agent, tool in (("X", "consult_agent_x"), ("Z", "consult_agent_z"),
                        ("CS", "consult_agent_cs")):
        desc = tools[tool]["description"]
        assert routing[agent]["model"] in desc
        assert routing[agent]["provider"] in desc
        assert "BYOK" in desc


def test_mcp_config_hosted_option_is_multi_provider():
    import http_server
    payload = _render(http_server.mcp_config_handler)
    option = payload["authentication"]["setup_options"]["option_1_use_hosted"]
    assert "multi-provider" in option["description"]


def test_mcp_config_cerebras_copy_is_account_qualified():
    import http_server
    payload = _render(http_server.mcp_config_handler)
    cerebras = payload["authentication"]["get_free_api_keys"]["cerebras"]
    assert "vary by account" in cerebras
    assert "1M tokens/day" not in cerebras


def test_mcp_config_features_are_honest():
    import http_server
    payload = _render(http_server.mcp_config_handler)
    features = payload["mcpServers"]["verifimind-genesis"]["features"]
    assert features["construction_fallback"] is True
    assert features["runtime_failover"] is False
    assert "smart_fallback" not in features


def test_mcp_config_body_carries_no_forbidden_claims():
    import http_server
    response = asyncio.run(http_server.mcp_config_handler(_Req()))
    _assert_clean(response.body.decode(), "mcp-config")


# ---------------------------------------------------------------------------
# /setup makes no runtime-failover claim (criterion 3)
# ---------------------------------------------------------------------------

def test_setup_body_carries_no_forbidden_claims():
    import http_server
    response = asyncio.run(http_server.setup_handler(_Req()))
    _assert_clean(response.body.decode(), "/setup")


# ---------------------------------------------------------------------------
# Source-level backstop across the whole discovery module (criterion 7)
# ---------------------------------------------------------------------------

def test_http_server_source_carries_no_forbidden_claims():
    import http_server, inspect
    _assert_clean(inspect.getsource(http_server), "http_server source")
