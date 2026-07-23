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
    # provider with its default model, plus the CONSTRUCTION fallback — the
    # provider selected at client-construction time when the primary cannot be
    # built (missing key/config). This is NOT request-time failover: once a
    # request is in flight, it does not hop providers (T S88 D-88-1; runtime
    # failover is WP-B and gated behind runtime_failover_enabled below). The
    # BYOK session config and per-agent env overrides sit above this baseline.
    free_tier_routing = {}
    for agent_id, cfg in AGENT_PROVIDER_DEFAULTS.items():
        provider = cfg.get("recommended") or cfg.get("default", "mock")
        free_tier_routing[agent_id] = {
            "provider": provider,
            "model": _default_model(provider),
            "construction_fallback": cfg.get("fallback", "mock"),
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

    # WP-B: the runtime hop chain is config truth (what failover WOULD do),
    # served even while disabled; the flag is a LIVE read of the deploy-gated
    # env switch (default off => False, same served value as v0.5.54).
    from .llm.failover import runtime_failover_enabled, runtime_hop_chain
    for agent_id, entry in free_tier_routing.items():
        entry["runtime_hop_chain"] = runtime_hop_chain(agent_id)

    enabled = runtime_failover_enabled()
    return {
        "version": SERVER_VERSION,
        "free_tier_routing": free_tier_routing,
        # v0.5.54 (T S88 D-88-1/D-88-2): honest failover semantics. Serving
        # True requires the WP-B deploy + failure-injection evidence + the
        # Alton-gated env flip; no surface may claim runtime failover before.
        "runtime_failover_enabled": enabled,
        "fallback_semantics": (
            "bounded runtime failover between hosted free-tier providers"
            if enabled else
            "construction-time provider selection; an in-flight request does "
            "not fail over between providers"
        ),
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
