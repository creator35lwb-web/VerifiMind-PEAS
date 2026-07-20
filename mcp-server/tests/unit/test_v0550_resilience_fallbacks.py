"""
v0.5.50 Resilience Pass — fallback chains + Firestore degradation
=================================================================

Foundation Inspection pass 2, batch 1 (Hub #81; T S84: "Resilience is next").
The robustness risk matrix routed two MED residuals here:

1. The provider fallback chain (`_resolve_fallback_chain` / `get_provider_with_
   fallback` / `get_agent_provider`) — the order BYOK -> Groq -> Cerebras -> mock
   was documented but never proven in CI.
2. Firestore degradation (`registration.py`) — the db-None paths were dark.

FINDING F-RES-1 (pinned below, routed for decision): with Firestore down,
`register_early_adopter` returns a SUCCESS response carrying a UUID that was
never persisted — the user is told "save your UUID" but /whoami will never
recognize it. Graceful degradation by design (warning logged), but silent to
the user. Candidate fixes (T/Alton decision): disclose degradation in the
response message, or fail explicitly with 503. Current behavior is PINNED
here so any change is conscious.
"""

import asyncio

import pytest

from verifimind_mcp.llm.provider import (
    MockProvider,
    GroqProvider,
    get_provider,
    get_provider_with_fallback,
    _resolve_fallback_chain,
)
from verifimind_mcp.config_helper import get_agent_provider
import verifimind_mcp.registration as reg


ENV_KEYS = [
    "LLM_PROVIDER", "VERIFIMIND_LLM_PROVIDER", "LLM_FALLBACK_PROVIDER",
    "LLM_MODEL", "VERIFIMIND_LLM_MODEL",
    "OPENAI_API_KEY", "ANTHROPIC_API_KEY", "GEMINI_API_KEY",
    "GROQ_API_KEY", "CEREBRAS_API_KEY", "MISTRAL_API_KEY",
    "FIRESTORE_PROJECT_ID", "GOOGLE_CLOUD_PROJECT",
]


@pytest.fixture
def clean_env(monkeypatch):
    for k in ENV_KEYS:
        monkeypatch.delenv(k, raising=False)
    return monkeypatch


# ---------------------------------------------------------------------------
# The fallback cascade order (v0.4.0 contract: BYOK -> Groq -> Cerebras -> mock)
# ---------------------------------------------------------------------------

def test_chain_no_keys_is_mock_only(clean_env):
    assert _resolve_fallback_chain(exclude="anthropic") == ["mock"]


def test_chain_prefers_groq_then_cerebras_then_mock(clean_env):
    clean_env.setenv("GROQ_API_KEY", "gsk_x")
    clean_env.setenv("CEREBRAS_API_KEY", "csk_x")
    assert _resolve_fallback_chain(exclude="anthropic") == ["groq", "cerebras", "mock"]


def test_chain_excludes_the_failed_provider(clean_env):
    clean_env.setenv("GROQ_API_KEY", "gsk_x")
    clean_env.setenv("CEREBRAS_API_KEY", "csk_x")
    assert _resolve_fallback_chain(exclude="groq") == ["cerebras", "mock"]


def test_chain_explicit_override_wins(clean_env):
    clean_env.setenv("GROQ_API_KEY", "gsk_x")
    clean_env.setenv("LLM_FALLBACK_PROVIDER", "cerebras")
    assert _resolve_fallback_chain(exclude="anthropic") == ["cerebras", "mock"]


# ---------------------------------------------------------------------------
# get_provider env resolution
# ---------------------------------------------------------------------------

def test_get_provider_defaults_to_mock_with_no_env(clean_env):
    assert isinstance(get_provider(), MockProvider)


def test_get_provider_honors_llm_provider_env(clean_env):
    clean_env.setenv("LLM_PROVIDER", "mock")
    assert isinstance(get_provider(), MockProvider)


def test_get_provider_legacy_env_var_supported(clean_env):
    clean_env.setenv("VERIFIMIND_LLM_PROVIDER", "mock")
    assert isinstance(get_provider(), MockProvider)


def test_get_provider_unknown_name_raises(clean_env):
    with pytest.raises(ValueError) as e:
        get_provider("notaprovider")
    assert "Unknown provider" in str(e.value)


def test_get_provider_groq_via_env_key(clean_env):
    clean_env.setenv("GROQ_API_KEY", "gsk_x")
    p = get_provider("groq")
    assert isinstance(p, GroqProvider)


# ---------------------------------------------------------------------------
# get_provider_with_fallback — the cascade actually cascades
# ---------------------------------------------------------------------------

def test_fallback_cascades_keyless_primary_to_groq(clean_env):
    """anthropic with no key raises at construction -> cascade lands on Groq."""
    clean_env.setenv("GROQ_API_KEY", "gsk_x")
    p = asyncio.run(get_provider_with_fallback("anthropic"))
    assert isinstance(p, GroqProvider)


def test_fallback_lands_on_mock_when_nothing_available(clean_env):
    p = asyncio.run(get_provider_with_fallback("anthropic"))
    assert isinstance(p, MockProvider)


# ---------------------------------------------------------------------------
# get_agent_provider — the per-agent resolution never raises
# ---------------------------------------------------------------------------

def test_agent_provider_bare_environment_is_mock(clean_env):
    assert isinstance(get_agent_provider("X"), MockProvider)


def test_agent_provider_malformed_ctx_falls_through(clean_env):
    class BadCtx:
        session_config = object()  # has no llm_provider attribute
    assert isinstance(get_agent_provider("Z", BadCtx()), MockProvider)


def test_agent_provider_ctx_mock_config(clean_env):
    class Cfg:
        llm_provider = "mock"
    class Ctx:
        session_config = Cfg()
    assert isinstance(get_agent_provider("CS", Ctx()), MockProvider)


def test_agent_provider_ctx_byok_groq(clean_env):
    class Cfg:
        llm_provider = "groq"
        groq_api_key = "gsk_byok"
    class Ctx:
        session_config = Cfg()
    p = get_agent_provider("Z", Ctx())
    assert isinstance(p, GroqProvider)


# ---------------------------------------------------------------------------
# Firestore degradation (db unavailable) — graceful, never crashing
# ---------------------------------------------------------------------------

@pytest.fixture
def no_firestore(clean_env):
    clean_env.setattr(reg, "_firestore_client", None)
    return clean_env


def test_get_firestore_none_without_project(no_firestore):
    assert reg._get_firestore() is None


def test_ea_status_returns_none_when_db_down(no_firestore):
    assert asyncio.run(reg.get_ea_status("some-uuid")) is None


def test_register_degrades_gracefully_without_db(no_firestore):
    """F-RES-1 (PINNED current behavior — routed for decision): registration
    with Firestore down still returns success + a UUID that was NEVER
    persisted. No crash, email masked — but the degradation is silent to the
    user, whose UUID will never resolve. Any change to this behavior must
    consciously update this test."""
    data = reg.EarlyAdopterRegistration(
        email="resilience-probe@example.com",
        tc_accepted=True,
        privacy_acknowledged=True,
    )
    resp = asyncio.run(reg.register_early_adopter(data))
    assert resp.uuid  # a UUID is issued...
    assert "@" in resp.email_masked and "resilience-probe" not in resp.email_masked
    assert resp.tier == "early_adopter"
    # ...but nothing was persisted: the same environment cannot look it up.
    assert asyncio.run(reg.get_ea_status(resp.uuid)) is None
