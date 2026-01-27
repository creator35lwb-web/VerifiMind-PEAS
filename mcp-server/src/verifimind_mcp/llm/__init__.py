"""
LLM Provider module for VerifiMind-PEAS MCP Server.

BYOK v0.3.0 - Multi-Provider Support with Fallback

Provides a unified interface for interacting with different LLM providers,
enabling users to bring their own API keys (BYOK).

Supported Providers:
- Gemini (FREE tier available)
- Groq (FREE tier available)
- OpenAI
- Anthropic
- Mistral
- Ollama (local, FREE)
- Mock (testing)
"""

from .provider import (
    # Base class
    LLMProvider,
    LLMResponse,
    # Provider implementations
    OpenAIProvider,
    AnthropicProvider,
    GeminiProvider,
    GroqProvider,
    MistralProvider,
    OllamaProvider,
    MockProvider,
    # Factory functions
    get_provider,
    get_provider_with_fallback,
    register_provider,
    # Configuration
    PROVIDER_CONFIGS,
    get_provider_info,
    list_providers,
    list_free_tier_providers,
    validate_provider_config,
)

__all__ = [
    # Base class
    "LLMProvider",
    "LLMResponse",
    # Provider implementations
    "OpenAIProvider",
    "AnthropicProvider",
    "GeminiProvider",
    "GroqProvider",
    "MistralProvider",
    "OllamaProvider",
    "MockProvider",
    # Factory functions
    "get_provider",
    "get_provider_with_fallback",
    "register_provider",
    # Configuration
    "PROVIDER_CONFIGS",
    "get_provider_info",
    "list_providers",
    "list_free_tier_providers",
    "validate_provider_config",
]
