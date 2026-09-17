"""Served-copy truth while the legacy UUID containment holds.

The containment (``security_containment``) closes every legacy account route and ignores
caller-supplied UUIDs. These contracts pin that what a person or an MCP client is actually
SERVED says so: no surface advertises a closed workflow, promises a UUID benefit that no
longer exists, or sends a rights request somewhere it cannot be handled.

Each contract reads the served surface — the ASGI route, or the MCP tool schema — never a
template in isolation. Element checks use markup patterns, not bare words: the shared page
shell's CSS contains words such as ``email``, ``confirm`` and ``uuid``, so a word search
passes on any page rendered through it. The qualified deletion timeline on the opt-out page
is pinned separately, by ``test_v0555_public_truth``.

Every contract here is valid only while the containment invariant is closed. The first test
makes that coupling explicit: the reviewed change that restores UUID trust must revisit this
copy in the same change.
"""

import asyncio
import json
import re

import pytest
from starlette.testclient import TestClient

import http_server
from verifimind_mcp import security_containment
from verifimind_mcp.policies.privacy_policy import PRIVACY_POLICY

EMAIL = re.compile(r"[\w.+-]+@[\w-]+\.[\w.]+")
CLOSED_ACCOUNT_PATHS = (
    "/whoami",
    "/early-adopters/register",
    "/early-adopters/status",
    "/early-adopters/dashboard",
    "/early-adopters/feedback",
    "/early-adopters/optout",
    "/mcp/test",
)


@pytest.fixture(scope="module")
def client():
    with TestClient(http_server.app, raise_server_exceptions=True) as c:
        yield c


def _served_html(client, path):
    response = client.get(path, headers={"Accept": "text/html"})
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    return response.text


# HTML element names are case-insensitive, so this test oracle matches them that way.
# It is a test oracle over pages this server renders, not a sanitizer.
_STYLE_ELEMENT = re.compile(r"<style\b[^>]*>.*?</style[^>]*>", flags=re.IGNORECASE | re.DOTALL)
_SCRIPT_ELEMENT = re.compile(r"<script\b[^>]*>(.*?)</script[^>]*>", flags=re.IGNORECASE | re.DOTALL)


def _markup(html):
    """The page without its inline stylesheet, so CSS selectors cannot satisfy a check."""
    return _STYLE_ELEMENT.sub("", html)


def _scripts(html):
    """The body of every script element, whatever the element name's letter case."""
    return [s.strip() for s in _SCRIPT_ELEMENT.findall(html)]


def _text(fragment):
    """Visible text with whitespace collapsed, so line-wrapped copy can be matched."""
    return " ".join(re.sub(r"<[^>]+>", " ", fragment).split())


def _maintenance_response():
    response = asyncio.run(http_server.legacy_identity_maintenance_handler(None))
    return json.loads(response.body)


# ── the oracle itself: mixed-case element names ───────────────────────────────

def test_markup_oracle_removes_mixed_case_style_elements():
    # known-positive: a lowercase-only pattern leaves this stylesheet, and its
    # selector text, in the "markup" every element check reads
    fixture = '<StYlE media="screen">input[type="email"] { color: red }</sTyLe >\n<p>kept</p>'
    stripped = _markup(fixture)
    assert 'type="email"' not in stripped
    assert "<p>kept</p>" in stripped


def test_script_oracle_detects_mixed_case_script_elements():
    # known-positive: a lowercase-only pattern reports no script at all here
    fixture = '<p>page</p>\n<ScRiPt type="module">sendBeacon()</sCrIpT\n >'
    assert _scripts(fixture) == ["sendBeacon()"]


# ── the coupling ──────────────────────────────────────────────────────────────

def test_copy_contracts_hold_only_while_uuid_trust_is_contained():
    # pin: passes before and after this repair. It exists so that flipping the invariant
    # fails here too, and the copy is revisited in the same reviewed change.
    assert security_containment.TRUST_UNAUTHENTICATED_UUID_INPUT is False, (
        "UUID trust was restored: revisit the served account copy in the same change"
    )


# ── setup: the home page ──────────────────────────────────────────────────────

def test_home_page_setup_never_instructs_a_uuid_header_or_promises_a_uuid_tier(client):
    page = _markup(_served_html(client, "/"))
    for claim in (
        "X-VerifiMind-UUID",
        "VERIFIMIND_UUID",
        "Scholar Tier",
        "Higher Rate Limits",
        "30 req/60s",
        "/mcp/test?key=",
        'href="/register"',
    ):
        assert claim not in page, f"the home page still serves {claim!r}"


def test_home_page_says_accounts_are_unavailable_and_tools_stay_free(client):
    page = _markup(_served_html(client, "/"))
    card = re.search(r'<div class="card-scholar" id="account-status">(.*?)</div>', page, flags=re.S)
    assert card, "the home page has no account-status notice"
    text = _text(card.group(1))
    assert "temporarily unavailable during security maintenance" in text
    assert "no account and no UUID" in text
    assert "has no effect" in text
    assert 'href="/optout"' in card.group(1)


# ── registration ──────────────────────────────────────────────────────────────

def test_registration_page_serves_no_form_and_reaches_no_closed_route(client):
    html = _served_html(client, "/register")
    page = _markup(html)
    for element in (r"<form\b", r"<input\b", r"<textarea\b", r"<select\b", r"<button\b[^>]*type=\"submit\""):
        assert not re.search(element, page), f"the registration page still serves {element}"
    assert _scripts(html) == [""], "the registration page still serves a script"
    for path in CLOSED_ACCOUNT_PATHS:
        assert path not in page, f"the registration page still references {path}"


def test_registration_page_says_it_is_unavailable_and_where_requests_go(client):
    page = _markup(_served_html(client, "/register"))
    notice = re.search(r'<div class="card" id="registration-status">(.*?)\n</div>', page, flags=re.S)
    assert notice, "the registration page has no status notice"
    text = _text(notice.group(1))
    assert "Registration is temporarily unavailable" in text
    assert "temporarily unavailable during security maintenance" in text
    assert "standard anonymous rate limit" in text
    for href in ('href="/optout"', 'href="/terms"', 'href="/privacy"'):
        assert href in notice.group(1)


# ── opt-out ───────────────────────────────────────────────────────────────────

def test_optout_page_serves_no_self_service_form(client):
    html = _served_html(client, "/optout")
    page = _markup(html)
    for element in (r"<form\b", r"<input\b", r"<button\b"):
        assert not re.search(element, page), f"the opt-out page still serves {element}"
    assert _scripts(html) == [""], "the opt-out page still serves a script"
    for path in CLOSED_ACCOUNT_PATHS:
        assert path not in page, f"the opt-out page still references {path}"


def test_optout_request_channel_matches_the_maintenance_response_and_the_privacy_policy(client):
    page = _markup(_served_html(client, "/optout"))
    paragraph = re.search(r'<p id="private-request-channel">(.*?)</p>', page, flags=re.S)
    assert paragraph, "the opt-out page names no private request channel"
    text = _text(paragraph.group(1))

    served = set(EMAIL.findall(text))
    maintenance = set(EMAIL.findall(_maintenance_response()["privacy_request"]))
    policy = set(EMAIL.findall(PRIVACY_POLICY))
    assert served, "the request channel names no address"
    assert served == maintenance, "the page and the maintenance response name different channels"
    assert served <= policy, "the page names a channel the Privacy Policy does not"

    # the same wording contract the containment holds its own maintenance response to
    lowered = text.lower()
    for phrase in ("access, correction, or deletion", "email", "verify", "public issue or comment"):
        assert phrase in lowered
    assert "deleted" not in lowered


# ── Opt-out deletion truth ──────────────────────────────────────────────────

def test_optout_deletion_copy_matches_the_canonical_policy(client):
    page = _markup(_served_html(client, "/optout"))
    note = re.search(r'<p class="deletion-note">(.*?)</p>', page, flags=re.S)
    assert note, "the opt-out page has no deletion-scope note"
    note_markup = note.group(1)
    note_text = _text(note_markup)
    page_text = _text(page)
    policy_text = " ".join(PRIVACY_POLICY.split())

    for stale_claim in (
        "Privacy Policy v1.0",
        "Deletion is processed within",
        "Your UUID is retained",
    ):
        assert stale_claim not in page_text

    canonical_scope = (
        "Pseudonymous UUID-validation records are included in the scope of an "
        "account deletion request"
    )
    assert canonical_scope in note_text
    assert canonical_scope in policy_text
    assert "lawful or documented security/legal hold" in note_text
    assert 'href="/privacy"' in note_markup
    assert ">Privacy Policy</a>" in note_markup
    assert "targeted for purge within 7 business days" in page_text
    assert "may limit or delay deletion" in page_text


# ── Trinity history description ──────────────────────────────────────────────

def _served_tools():
    from verifimind_mcp import server

    return asyncio.run(server._create_mcp_instance().list_tools())


def test_trinity_history_description_no_longer_promises_uuid_keyed_history():
    tools = {tool.name: tool for tool in _served_tools()}
    description = tools["run_full_trinity"].parameters["properties"]["save_to_history"]["description"]
    text = " ".join(description.split())
    assert "may still be written" not in text
    assert "has no effect" in text
    assert "no UUID-keyed validation history is written" in text


def test_no_served_tool_schema_promises_uuid_keyed_history():
    # class-level guard: the stale claim lived in one parameter description; no tool
    # description or parameter description anywhere in the served schema may carry it.
    for tool in _served_tools():
        blob = " ".join(json.dumps({"description": tool.description, "parameters": tool.parameters}).split())
        assert "may still be written to UUID-keyed" not in blob, tool.name
