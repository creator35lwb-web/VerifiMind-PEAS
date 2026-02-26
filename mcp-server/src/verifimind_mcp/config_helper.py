"""
Configuration helper for VerifiMind MCP Server.

BYOK v0.3.1 - Smart Fallback with Per-Agent Provider Support

Safely handles session config from Smithery and provides
intelligent fallback to environment variables or free tier providers.

Smart Fallback Strategy:
- Default: All agents use Gemini (FREE tier - no cost to maintainer)
- If ANTHROPIC_API_KEY is set: Z and CS agents upgrade to Claude
- Per-agent overrides available via environment variables

Agent-Specific Recommendations:
- X Agent (Innovation): Gemini - Creative, innovative thinking
- Z Agent (Ethics): Anthropic Claude - Strong ethical reasoning
- CS Agent (Security): Anthropic Claude - Powerful code/security analysis

Supported Providers:
- Gemini (FREE tier available) - Default for all agents
- Groq (FREE tier available)
- OpenAI
- Anthropic - Recommended for Z and CS agents
- Mistral
- Ollama (local, FREE)
- Mock (testing)
"""

import os
import logging
from typing import Any

logger = logging.getLogger(__name__)

# ============================================================================
# AGENT-SPECIFIC PROVIDER RECOMMENDATIONS (v0.3.1)
# ============================================================================

AGENT_PROVIDER_DEFAULTS = {
    "X": {
        "default": "gemini",           # FREE tier - creative/innovative
        "recommended": "gemini",       # Gemini excels at innovation
        "fallback": "mock"
    },
    "Z": {
        "default": "gemini",           # FREE tier
        "recommended": "groq",         # v0.4.4: Groq/Llama for structured ethics output
        "fallback": "gemini"
    },
    "CS": {
        "default": "gemini",           # FREE tier
        "recommended": "groq",         # v0.4.4: Groq/Llama for reliable structured security output
        "fallback": "gemini"
    }
}


def get_agent_provider(agent_id: str, ctx: Any = None):
    """
    Get LLM provider optimized for a specific agent with smart fallback.

    BYOK v0.3.1: Per-agent provider selection with intelligent fallback.

    Strategy:
    1. Check per-agent environment variable (X_AGENT_PROVIDER, Z_AGENT_PROVIDER, CS_AGENT_PROVIDER)
    2. Check if recommended provider API key is available
    3. Fall back to free tier (Gemini)
    4. Final fallback to Mock

    Args:
        agent_id: Agent identifier ("X", "Z", or "CS")
        ctx: FastMCP Context with optional session_config

    Returns:
        Configured LLMProvider instance optimized for the agent
    """
    from .llm import (
        MockProvider,
        get_provider,
        GeminiProvider,
        AnthropicProvider,
    )

    agent_id = agent_id.upper()
    if agent_id not in AGENT_PROVIDER_DEFAULTS:
        agent_id = "X"  # Default to X agent config

    agent_config = AGENT_PROVIDER_DEFAULTS[agent_id]

    # 1. Check per-agent environment variable override
    per_agent_env = f"{agent_id}_AGENT_PROVIDER"
    per_agent_provider = os.getenv(per_agent_env)

    if per_agent_provider:
        logger.info(f"Agent {agent_id}: Using override provider '{per_agent_provider}' from {per_agent_env}")
        try:
            return get_provider(per_agent_provider)
        except ValueError as e:
            logger.warning(f"Agent {agent_id}: Override provider failed: {e}")

    # 2. Check session config (BYOK from Smithery)
    if ctx is not None:
        provider = _get_provider_from_session_config(ctx, agent_id)
        if provider:
            return provider

    # 3. Smart fallback: Use recommended provider if API key available
    recommended = agent_config["recommended"]

    if recommended == "anthropic" and os.getenv("ANTHROPIC_API_KEY"):
        logger.info(f"Agent {agent_id}: Using recommended provider 'anthropic' (API key found)")
        try:
            return AnthropicProvider()
        except Exception as e:
            logger.warning(f"Agent {agent_id}: Anthropic failed: {e}")

    if recommended == "groq" and os.getenv("GROQ_API_KEY"):
        logger.info(f"Agent {agent_id}: Using recommended provider 'groq' (API key found)")
        try:
            from .llm import GroqProvider
            return GroqProvider()
        except Exception as e:
            logger.warning(f"Agent {agent_id}: Groq failed: {e}")

    # 4. Fall back to Gemini (FREE tier)
    if os.getenv("GEMINI_API_KEY"):
        logger.info(f"Agent {agent_id}: Using Gemini (FREE tier)")
        try:
            return GeminiProvider()
        except Exception as e:
            logger.warning(f"Agent {agent_id}: Gemini failed: {e}")

    # 5. Try Groq as another free option
    if os.getenv("GROQ_API_KEY"):
        logger.info(f"Agent {agent_id}: Using Groq (FREE tier)")
        try:
            from .llm import GroqProvider
            return GroqProvider()
        except Exception as e:
            logger.warning(f"Agent {agent_id}: Groq failed: {e}")

    # 6. Final fallback to Mock
    logger.info(f"Agent {agent_id}: Using MockProvider (no API keys configured)")
    return MockProvider()


def _get_provider_from_session_config(ctx: Any, agent_id: str):
    """Extract provider from session config if available."""
    from .llm import (
        MockProvider,
        OpenAIProvider,
        AnthropicProvider,
        GeminiProvider,
        GroqProvider,
        MistralProvider,
        OllamaProvider,
    )

    try:
        config = getattr(ctx, 'session_config', None)
        if config is None:
            return None

        llm_provider = getattr(config, 'llm_provider', None)
        if not llm_provider:
            return None

        # Get API keys from config
        openai_key = getattr(config, 'openai_api_key', '')
        anthropic_key = getattr(config, 'anthropic_api_key', '')
        gemini_key = getattr(config, 'gemini_api_key', '')
        groq_key = getattr(config, 'groq_api_key', '')
        mistral_key = getattr(config, 'mistral_api_key', '')

        provider_map = {
            "openai": (OpenAIProvider, openai_key),
            "anthropic": (AnthropicProvider, anthropic_key),
            "gemini": (GeminiProvider, gemini_key),
            "groq": (GroqProvider, groq_key),
            "mistral": (MistralProvider, mistral_key),
            "ollama": (OllamaProvider, None),
            "mock": (MockProvider, None),
        }

        if llm_provider in provider_map:
            provider_class, api_key = provider_map[llm_provider]
            if llm_provider in ["mock", "ollama"]:
                return provider_class()
            elif api_key:
                logger.info(f"Agent {agent_id}: Using session config provider '{llm_provider}'")
                return provider_class(api_key=api_key)

    except (AttributeError, TypeError):
        pass  # Session config doesn't have expected attributes — fall through

    return None


def get_provider_from_config(ctx: Any = None):
    """
    Get LLM provider based on session config or environment variables.

    BYOK v0.3.0: Supports multiple providers with automatic fallback.

    Priority:
    1. Session config (BYOK - Bring Your Own Key)
    2. Environment variables (LLM_PROVIDER, {PROVIDER}_API_KEY)
    3. MockProvider (fallback for testing)

    Args:
        ctx: FastMCP Context with optional session_config

    Returns:
        Configured LLMProvider instance
    """
    from .llm import (
        MockProvider,
        get_provider,
        OpenAIProvider,
        AnthropicProvider,
        GeminiProvider,
        GroqProvider,
        MistralProvider,
        OllamaProvider,
    )

    # Try to get provider from session config (BYOK)
    if ctx is not None:
        try:
            config = getattr(ctx, 'session_config', None)
            if config is not None:
                # Check if config has the expected attributes (not EmptyConfig)
                llm_provider = getattr(config, 'llm_provider', None)

                if llm_provider:
                    # Get API keys from config
                    openai_key = getattr(config, 'openai_api_key', '')
                    anthropic_key = getattr(config, 'anthropic_api_key', '')
                    gemini_key = getattr(config, 'gemini_api_key', '')
                    groq_key = getattr(config, 'groq_api_key', '')
                    mistral_key = getattr(config, 'mistral_api_key', '')

                    # Map provider to class and key
                    provider_map = {
                        "openai": (OpenAIProvider, openai_key),
                        "anthropic": (AnthropicProvider, anthropic_key),
                        "gemini": (GeminiProvider, gemini_key),
                        "groq": (GroqProvider, groq_key),
                        "mistral": (MistralProvider, mistral_key),
                        "ollama": (OllamaProvider, None),  # No API key needed
                        "mock": (MockProvider, None),
                    }

                    if llm_provider in provider_map:
                        provider_class, api_key = provider_map[llm_provider]
                        if llm_provider in ["mock", "ollama"]:
                            return provider_class()
                        elif api_key:
                            return provider_class(api_key=api_key)
        except (AttributeError, TypeError):
            # Config doesn't have expected attributes - fall through to env vars
            pass

    # Try environment variables
    try:
        # Check if any API key is set in environment or LLM_PROVIDER is configured
        llm_provider = os.getenv("LLM_PROVIDER") or os.getenv("VERIFIMIND_LLM_PROVIDER")
        has_api_key = any([
            os.getenv("OPENAI_API_KEY"),
            os.getenv("ANTHROPIC_API_KEY"),
            os.getenv("GEMINI_API_KEY"),
            os.getenv("GROQ_API_KEY"),
            os.getenv("MISTRAL_API_KEY"),
        ])

        # If provider is explicitly set to ollama or mock, or if any API key exists
        if llm_provider in ["ollama", "mock"] or has_api_key or llm_provider:
            return get_provider()
    except ValueError:
        # No API key configured
        pass

    # Fallback to MockProvider
    return MockProvider()


def get_trinity_providers(ctx: Any = None):
    """
    Get optimized providers for all three Trinity agents.

    BYOK v0.3.1: Returns a dict of providers, each optimized for its agent role.

    Returns:
        Dict with keys 'X', 'Z', 'CS' mapping to their respective providers.

    Example:
        providers = get_trinity_providers(ctx)
        x_agent = XAgent(llm_provider=providers['X'])
        z_agent = ZAgent(llm_provider=providers['Z'])
        cs_agent = CSAgent(llm_provider=providers['CS'])
    """
    return {
        "X": get_agent_provider("X", ctx),
        "Z": get_agent_provider("Z", ctx),
        "CS": get_agent_provider("CS", ctx),
    }


def get_provider_status():
    """
    Get current provider configuration status for diagnostics.

    Returns:
        Dict with provider availability and recommendations.
    """
    status = {
        "version": "0.3.1",
        "strategy": "smart_fallback",
        "providers": {
            "gemini": {
                "available": bool(os.getenv("GEMINI_API_KEY")),
                "free_tier": True,
                "recommended_for": ["X"]
            },
            "anthropic": {
                "available": bool(os.getenv("ANTHROPIC_API_KEY")),
                "free_tier": False,
                "recommended_for": ["Z", "CS"]
            },
            "groq": {
                "available": bool(os.getenv("GROQ_API_KEY")),
                "free_tier": True,
                "recommended_for": []
            },
            "openai": {
                "available": bool(os.getenv("OPENAI_API_KEY")),
                "free_tier": False,
                "recommended_for": []
            },
            "mistral": {
                "available": bool(os.getenv("MISTRAL_API_KEY")),
                "free_tier": False,
                "recommended_for": []
            },
        },
        "agent_assignments": {},
        "notes": []
    }

    # Determine actual agent assignments
    for agent_id in ["X", "Z", "CS"]:
        recommended = AGENT_PROVIDER_DEFAULTS[agent_id]["recommended"]

        # Check per-agent override first
        override = os.getenv(f"{agent_id}_AGENT_PROVIDER")
        if override:
            status["agent_assignments"][agent_id] = f"{override} (override)"
            continue

        # Check if recommended is available
        if recommended == "anthropic" and os.getenv("ANTHROPIC_API_KEY"):
            status["agent_assignments"][agent_id] = "anthropic (recommended)"
        elif os.getenv("GEMINI_API_KEY"):
            status["agent_assignments"][agent_id] = "gemini (free tier)"
        elif os.getenv("GROQ_API_KEY"):
            status["agent_assignments"][agent_id] = "groq (free tier)"
        else:
            status["agent_assignments"][agent_id] = "mock (no API keys)"
            status["notes"].append(f"Set GEMINI_API_KEY for free tier access")

    # Add recommendations
    if not os.getenv("GEMINI_API_KEY"):
        status["notes"].append("Get free Gemini API key: https://aistudio.google.com/apikey")

    if not os.getenv("ANTHROPIC_API_KEY"):
        status["notes"].append("For optimal Z/CS performance, add ANTHROPIC_API_KEY")

    return status
