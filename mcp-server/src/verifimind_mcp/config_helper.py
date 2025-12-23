"""
Configuration helper for VerifiMind MCP Server.

Safely handles session config from Smithery and provides
fallback to environment variables or MockProvider.
"""

import os
from typing import Any, Optional


def get_provider_from_config(ctx: Any = None):
    """
    Get LLM provider based on session config or environment variables.
    
    Priority:
    1. Session config (BYOK - Bring Your Own Key)
    2. Environment variables
    3. MockProvider (fallback for testing)
    
    Args:
        ctx: FastMCP Context with optional session_config
        
    Returns:
        Configured LLMProvider instance
    """
    from .llm import MockProvider, get_provider
    
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
                    
                    if llm_provider == "openai" and openai_key:
                        from .llm import OpenAIProvider
                        return OpenAIProvider(api_key=openai_key)
                    elif llm_provider == "anthropic" and anthropic_key:
                        from .llm import AnthropicProvider
                        return AnthropicProvider(api_key=anthropic_key)
                    elif llm_provider == "gemini" and gemini_key:
                        from .llm import GeminiProvider
                        return GeminiProvider(api_key=gemini_key)
                    elif llm_provider == "mock":
                        return MockProvider()
        except (AttributeError, TypeError):
            # Config doesn't have expected attributes - fall through to env vars
            pass
    
    # Try environment variables
    try:
        # Check if any API key is set in environment
        if os.getenv("OPENAI_API_KEY") or os.getenv("ANTHROPIC_API_KEY") or os.getenv("GEMINI_API_KEY"):
            return get_provider()
    except ValueError:
        # No API key configured
        pass
    
    # Fallback to MockProvider
    return MockProvider()
