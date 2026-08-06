"""v0.5.57 — current public-truth and containment contract."""

import asyncio
from html import escape
import json
from pathlib import Path

from verifimind_mcp.pages import (
    get_optout_page,
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
from verifimind_mcp.policies.privacy_policy import (
    PRIVACY_POLICY_EFFECTIVE_DATE,
)
from verifimind_mcp.policies.terms import TERMS_EFFECTIVE_DATE


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


def _flat(text):
    """Normalize prose wrapping without weakening exact-wording assertions."""
    return " ".join(text.split())


def test_version_and_tool_availability_are_exact_across_discovery_surfaces():
    import http_server

    expected = {
        "defined": 13,
        "active": 8,
        "temporarily_unavailable": 5,
        "unavailable_tools": [
            "coordination_handoff_create",
            "coordination_handoff_read",
            "coordination_team_status",
            "register_custom_template",
            "import_template_from_url",
        ],
        "reason": "owner-scoped access-control and custom-template security maintenance",
        "reason_groups": {
            "coordination_owner_isolation": [
                "coordination_handoff_create",
                "coordination_handoff_read",
                "coordination_team_status",
            ],
            "custom_template_isolation_and_url_fetch": [
                "register_custom_template",
                "import_template_from_url",
            ],
        },
    }

    health = _json_response(http_server.health_handler)
    config = _json_response(http_server.mcp_config_handler)
    setup = _json_response(http_server.setup_handler)

    assert http_server.SERVER_VERSION == "0.5.57"
    assert health["version"] == "0.5.57"
    assert health["tool_availability"] == expected
    assert (
        config["mcpServers"]["verifimind-genesis"]["tool_availability"]
        == expected
    )
    assert setup["available_tools"]["_availability"] == expected


def test_registry_manifest_has_same_current_availability_truth():
    manifest_path = Path(__file__).resolve().parents[3] / "server.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    assert manifest["version"] == "3.34.0"
    assert "v0.5.57" in manifest["description"]
    assert "8 active tools" in manifest["description"]
    assert len(manifest["description"]) <= 100
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
    custom_mutation = [
        tool for tool in tools
        if tool["name"] in {"register_custom_template", "import_template_from_url"}
    ]
    assert len(custom_mutation) == 2
    assert all(
        "TEMPORARILY UNAVAILABLE (security maintenance)" in tool["description"]
        for tool in custom_mutation
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
    assert "8 active tools" in page
    assert "time-limited access entitlement" in page
    assert "UUID (identifier)" in page
    assert "UUID (access key)" not in page


def test_html_and_json_policy_surfaces_share_versions_and_current_truth():
    import http_server

    privacy_json = _json_response(http_server.privacy_handler, "application/json")
    terms_json = _json_response(http_server.terms_handler, "application/json")

    assert PRIVACY_POLICY_VERSION == privacy_json["version"] == "2.5"
    assert TERMS_VERSION == terms_json["version"] == "2.4"
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
        assert "8" in surface
        assert "active" in surface.lower()


def test_browser_policy_pages_render_the_canonical_json_text_not_a_second_copy():
    privacy_html = get_privacy_page()
    terms_html = get_terms_page()
    malay_marker = "12. NOTIS PERLINDUNGAN DATA PERIBADI — BAHASA MALAYSIA"
    privacy_en, privacy_ms = PRIVACY_POLICY.strip().split(malay_marker, 1)

    assert escape(privacy_en.rstrip()) in privacy_html
    assert escape(malay_marker + privacy_ms) in privacy_html
    assert escape(TERMS_AND_CONDITIONS.strip()) in terms_html
    assert '<pre class="policy-text" lang="en">' in privacy_html
    assert '<pre class="policy-text" lang="ms">' in privacy_html
    assert "version-badge\">v2.0" not in privacy_html


def test_pages_module_has_no_second_embedded_policy_copy():
    pages_source = (
        Path(__file__).resolve().parents[2]
        / "src"
        / "verifimind_mcp"
        / "pages.py"
    ).read_text(encoding="utf-8")

    assert "_PRIVACY_BODY" not in pages_source
    assert "_TERMS_BODY" not in pages_source
    assert "No other third parties receive your data today" not in pages_source
    assert "Omit the flag and nothing is retained" not in pages_source


def test_effective_dates_and_immediate_revision_classification_converge():
    import http_server

    privacy_json = _json_response(http_server.privacy_handler, "application/json")
    terms_json = _json_response(http_server.terms_handler, "application/json")

    assert PRIVACY_POLICY_EFFECTIVE_DATE == "2026-08-06"
    assert TERMS_EFFECTIVE_DATE == "2026-08-06"
    assert privacy_json["effective_date"] == PRIVACY_POLICY_EFFECTIVE_DATE
    assert terms_json["effective_date"] == TERMS_EFFECTIVE_DATE
    for surface in (PRIVACY_POLICY, TERMS_AND_CONDITIONS):
        assert "effective on publication" in surface
        assert "future material adverse changes at least 14 days" in surface


def test_deletion_timeline_is_qualified_on_every_live_surface():
    surfaces = (
        PRIVACY_POLICY,
        TERMS_AND_CONDITIONS,
        get_privacy_page(),
        get_terms_page(),
        get_optout_page(),
    )
    for surface in surfaces:
        lowered = surface.lower()
        assert "7 business days" in lowered
        assert "target" in lowered
        assert "security/legal hold" in lowered

    rendered = "\n".join(surfaces)
    assert "data purged within 7 business days" not in rendered
    assert "will be purged within 7 business days" not in rendered
    assert "purged within 7 days" not in rendered


def test_history_copy_distinguishes_uuid_metadata_full_history_and_security_logs():
    surfaces = (PRIVACY_POLICY, get_privacy_page())
    for surface in surfaces:
        prose = _flat(surface)
        assert "Omitting user_uuid prevents that UUID-linked metadata" in prose
        assert "ordinary IP/request security logs may still be retained" in prose
        assert "save_to_history=true" in prose
        assert "shared, instance-local JSON history" in prose
        assert "at most the 20 newest opt-in results" in prose
        assert "no fixed time-based retention period is guaranteed" in prose
        assert "scores, recommendations" in prose
        assert "nothing is retained" not in prose


def test_processor_notice_tracks_hosted_routing_and_byok_classes():
    from verifimind_mcp.contract import get_public_contract

    contract = get_public_contract()
    active = {
        entry["provider"]
        for entry in contract["free_tier_routing"].values()
    }
    policy_names = {
        "gemini": "Google Gemini",
        "groq": "Groq",
    }
    for provider in active:
        assert policy_names[provider] in PRIVACY_POLICY

    assert contract["runtime_failover_enabled"] is False
    assert "in-flight provider failover is currently disabled" in _flat(PRIVACY_POLICY)
    for provider in ("OpenAI", "Anthropic", "Cerebras", "Mistral"):
        assert provider in PRIVACY_POLICY
    assert "No other third parties receive your data" not in get_privacy_page()


def test_private_rights_channel_and_bilingual_notice_are_explicit():
    policy = _flat(PRIVACY_POLICY)
    assert "only a limited account-status summary" in policy
    assert "not a complete personal-data access response" in policy
    assert "alton@ysenseai.org" in PRIVACY_POLICY
    assert "Do not post personal data in a public" in policy
    assert "alamat e-mel" in PRIVACY_POLICY
    assert "HAK DAN SALURAN PERMINTAAN PERIBADI" in PRIVACY_POLICY
    assert 'lang="ms"' in get_privacy_page()
