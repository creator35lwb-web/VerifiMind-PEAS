"""
Configuration helper for VerifiMind MCP Server.

BYOK v0.3.0 - Multi-Provider Support with Fallback

Safely handles session config from Smithery and provides
fallback to environment variables or MockProvider.

Supported Providers:
- Gemini (FREE tier available)
- Groq (FREE tier available)
- OpenAI
- Anthropic
- Mistral
- Ollama (local, FREE)
- Mock (testing)
"""

import os
from typing import Any, Optional


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
