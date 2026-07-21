"""
Public truth contract — the canonical provider/routing/version object (v0.5.51).

T's Session 85 Live Publication Truth Audit (D-85-2) found "discovery-contract
drift": /setup, the MCP config, /health, release evidence, and landing copy
each hand-maintained their own description of models, routing, and versions —
and disagreed. The drift mechanism was independent copy edits.

This module is the single generated truth. Every public surface that describes
providers, per-agent routing, or the version MUST project from
``get_public_contract()`` instead of hardcoding copy. Values are derived from
the live runtime constants (PROVIDER_CONFIGS, provider default-model constants,
AGENT_PROVIDER_DEFAULTS, SERVER_VERSION), so a model migration or version bump
propagates everywhere in one edit — the same pattern as /health's ``firestore``
field: make the truth observable, don't police the copies.
"""

from typing import Any, Dict


def get_public_contract() -> Dict[str, Any]:
    """Build the canonical public contract from live runtime constants."""
    # Lazy imports: server.py does not import this module, so no cycles.
    from .server import SERVER_VERSION
    from .config_helper import AGENT_PROVIDER_DEFAULTS
    from .llm.provider import PROVIDER_CONFIGS

    def _default_model(provider: str) -> str:
        return PROVIDER_CONFIGS.get(provider, {}).get("default_model", "")

    # Free-tier routing as deployed: each agent's preferred ("recommended")
    # provider with its default model, plus the fallback provider. The BYOK
    # session config and per-agent env overrides sit above this baseline.
    free_tier_routing = {}
    for agent_id, cfg in AGENT_PROVIDER_DEFAULTS.items():
        provider = cfg.get("recommended") or cfg.get("default", "mock")
        free_tier_routing[agent_id] = {
            "provider": provider,
            "model": _default_model(provider),
            "fallback_provider": cfg.get("fallback", "mock"),
        }

    byok_providers = {
        name: {
            "default_model": cfg.get("default_model", ""),
            "models": list(cfg.get("models", [])),
            "free_tier": bool(cfg.get("free_tier", False)),
        }
        for name, cfg in PROVIDER_CONFIGS.items()
        if name not in ("mock", "ollama")
    }

    return {
        "version": SERVER_VERSION,
        "free_tier_routing": free_tier_routing,
        "byok_providers": byok_providers,
    }


def free_tier_models_display() -> list:
    """Human-readable model list for landing/root surfaces, generated (never
    hand-written) so display copy cannot drift from the runtime truth."""
    contract = get_public_contract()
    routing = contract["free_tier_routing"]
    seen = []
    for agent_id in ("X", "Z", "CS"):
        entry = routing.get(agent_id)
        if not entry:
            continue
        label = f"{entry['model']} ({entry['provider']}, FREE)"
        if label not in seen:
            seen.append(label)
    return seen
