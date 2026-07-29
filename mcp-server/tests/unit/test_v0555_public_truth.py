"""v0.5.55 — integrated release and current public-truth contract."""

import asyncio
import json
from pathlib import Path

from verifimind_mcp.pages import (
    get_privacy_page,
    get_register_page,
    get_terms_page,
)
from verifimind_mcp.policies import (
    PRIVACY_POLICY,
    PRIVACY_POLICY_VERSION,
    TERMS_AND_CONDITIONS,
    TERMS_VERSION,
)


class _URL:
    scheme = "https"
    netloc = "verifimind.ysenseai.org"


class _Request:
    url = _URL()

    def __init__(self, accept=""):
        self.headers = {
            "host": "verifimind.ysenseai.org",
            "accept": accept,
        }


def _json_response(handler, accept=""):
    response = asyncio.run(handler(_Request(accept)))
    return json.loads(response.body)


def test_version_and_tool_availability_are_exact_across_discovery_surfaces():
    import http_server

    expected = {
        "defined": 13,
        "active": 10,
        "temporarily_unavailable": 3,
        "unavailable_tools": [
            "coordination_handoff_create",
            "coordination_handoff_read",
            "coordination_team_status",
        ],
        "reason": "owner-scoped access-control maintenance",
    }

    health = _json_response(http_server.health_handler)
    config = _json_response(http_server.mcp_config_handler)
    setup = _json_response(http_server.setup_handler)

    assert http_server.SERVER_VERSION == "0.5.55"
    assert health["version"] == "0.5.55"
    assert health["tool_availability"] == expected
    assert (
        config["mcpServers"]["verifimind-genesis"]["tool_availability"]
        == expected
    )
    assert setup["available_tools"]["_availability"] == expected


def test_registry_manifest_has_same_current_availability_truth():
    manifest_path = Path(__file__).resolve().parents[3] / "server.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    assert manifest["version"] == "3.32.0"
    assert "v0.5.55" in manifest["description"]
    assert "10 active tools" in manifest["description"]
    tools = manifest["_meta"][
        "io.modelcontextprotocol.registry/publisher-provided"
    ]["tools"]
    coordination = [
        tool for tool in tools if tool["name"].startswith("coordination_")
    ]
    assert len(coordination) == 3
    assert all(
        "TEMPORARILY UNAVAILABLE (maintenance)" in tool["description"]
        for tool in coordination
    )


def test_register_page_has_no_timed_free_access_marketing():
    page = get_register_page()
    forbidden = (
        "3 months FREE",
        "6 months FREE",
        "3 months free",
        "6 months free",
        "Free until:",
        "All 13 tools",
        "Free forever",
    )
    for claim in forbidden:
        assert claim not in page
    assert "10 active tools" in page
    assert "time-limited access entitlement" in page
    assert "UUID (identifier)" in page
    assert "UUID (access key)" not in page


def test_html_and_json_policy_surfaces_share_versions_and_current_truth():
    import http_server

    privacy_json = _json_response(http_server.privacy_handler, "application/json")
    terms_json = _json_response(http_server.terms_handler, "application/json")

    assert PRIVACY_POLICY_VERSION == privacy_json["version"] == "2.3"
    assert TERMS_VERSION == terms_json["version"] == "2.2"
    assert privacy_json["content"] == PRIVACY_POLICY
    assert terms_json["content"] == TERMS_AND_CONDITIONS

    surfaces = (
        PRIVACY_POLICY,
        TERMS_AND_CONDITIONS,
        get_privacy_page(),
        get_terms_page(),
    )
    for surface in surfaces:
        assert "3 months free" not in surface
        assert "6 months free" not in surface
        assert "all 13 tools" not in surface.lower()
        assert "10" in surface
        assert "active" in surface.lower()
