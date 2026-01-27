# Claude Code Implementation Guide: BYOK v0.3.0

**From:** Manus AI (T), CTO - Team YSenseAI  
**To:** Claude Code  
**Date:** January 28, 2026  
**Version:** v0.3.0 Implementation  
**GitHub Bridge:** https://github.com/creator35lwb-web/VerifiMind-PEAS

---

## 📋 Executive Summary

This guide provides Claude Code with complete specifications to implement **BYOK (Bring Your Own Key) Enhancement v0.3.0** for the VerifiMind-PEAS MCP server. The goal is to enable users to connect their own LLM API keys for multiple providers, making the system sustainable without increasing maintainer costs.

---

## 🎯 Objective

Implement full multi-provider BYOK support that allows users to:
1. Specify their preferred LLM provider via environment variables
2. Use their own API keys for token consumption
3. Optionally override the default model
4. Have fallback options if primary provider fails

---

## 📁 Repository Context

**Repository:** `creator35lwb-web/VerifiMind-PEAS`  
**Branch:** `main`  
**Current Version:** v0.2.5  
**Target Version:** v0.3.0

### Key Files to Modify

| File | Purpose | Action |
|------|---------|--------|
| `mcp-server/src/llm_provider.py` | LLM provider abstraction | Create/Modify |
| `mcp-server/src/config.py` | Configuration management | Modify |
| `mcp-server/src/tools/*.py` | Tool implementations | Modify |
| `.env.example` | Environment template | Update |
| `MCP_SETUP_GUIDE.md` | User documentation | Update |
| `CHANGELOG.md` | Version history | Update |

---

## 🔧 Technical Specifications

### 1. Environment Variables

```bash
# Required
LLM_PROVIDER=gemini  # Options: gemini, openai, anthropic, groq, mistral, ollama, mock

# Provider-specific keys (only one required based on LLM_PROVIDER)
GEMINI_API_KEY=your-gemini-key
OPENAI_API_KEY=your-openai-key
ANTHROPIC_API_KEY=your-anthropic-key
GROQ_API_KEY=your-groq-key
MISTRAL_API_KEY=your-mistral-key

# Optional overrides
LLM_MODEL=gemini-1.5-flash  # Override default model for provider
LLM_TEMPERATURE=0.7         # Override default temperature
LLM_MAX_TOKENS=4096         # Override max tokens

# Fallback (optional)
LLM_FALLBACK_PROVIDER=mock  # Use if primary fails
```

### 2. Provider Configuration

```python
# mcp-server/src/llm_providers/config.py

PROVIDER_CONFIGS = {
    "gemini": {
        "name": "Google Gemini",
        "default_model": "gemini-1.5-flash",
        "models": ["gemini-1.5-flash", "gemini-1.5-pro", "gemini-2.0-flash-exp"],
        "api_key_env": "GEMINI_API_KEY",
        "base_url": "https://generativelanguage.googleapis.com/v1beta",
        "free_tier": True,
        "rate_limit": 15,  # requests per minute on free tier
    },
    "openai": {
        "name": "OpenAI",
        "default_model": "gpt-4o-mini",
        "models": ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo"],
        "api_key_env": "OPENAI_API_KEY",
        "base_url": "https://api.openai.com/v1",
        "free_tier": False,
    },
    "anthropic": {
        "name": "Anthropic Claude",
        "default_model": "claude-3-5-sonnet-20241022",
        "models": ["claude-3-5-sonnet-20241022", "claude-3-opus-20240229"],
        "api_key_env": "ANTHROPIC_API_KEY",
        "base_url": "https://api.anthropic.com/v1",
        "free_tier": False,
    },
    "groq": {
        "name": "Groq",
        "default_model": "llama-3.3-70b-versatile",
        "models": ["llama-3.3-70b-versatile", "mixtral-8x7b-32768"],
        "api_key_env": "GROQ_API_KEY",
        "base_url": "https://api.groq.com/openai/v1",
        "free_tier": True,
        "rate_limit": 30,
    },
    "mistral": {
        "name": "Mistral AI",
        "default_model": "mistral-small-latest",
        "models": ["mistral-small-latest", "mistral-large-latest"],
        "api_key_env": "MISTRAL_API_KEY",
        "base_url": "https://api.mistral.ai/v1",
        "free_tier": False,
    },
    "ollama": {
        "name": "Ollama (Local)",
        "default_model": "llama3.2",
        "models": [],  # Dynamic based on local installation
        "api_key_env": None,  # No API key needed
        "base_url": "http://localhost:11434/v1",
        "free_tier": True,
    },
    "mock": {
        "name": "Mock Provider",
        "default_model": "mock-v1",
        "models": ["mock-v1"],
        "api_key_env": None,
        "base_url": None,
        "free_tier": True,
    },
}
```

### 3. LLM Provider Interface

```python
# mcp-server/src/llm_providers/base.py

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from dataclasses import dataclass

@dataclass
class LLMResponse:
    content: str
    model: str
    provider: str
    tokens_used: int
    latency_ms: float
    raw_response: Optional[Dict[str, Any]] = None

class BaseLLMProvider(ABC):
    """Abstract base class for LLM providers."""
    
    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self.api_key = api_key
        self.model = model or self.default_model
        
    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Return the provider name."""
        pass
    
    @property
    @abstractmethod
    def default_model(self) -> str:
        """Return the default model for this provider."""
        pass
    
    @abstractmethod
    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> LLMResponse:
        """Generate a response from the LLM."""
        pass
    
    @abstractmethod
    async def validate_connection(self) -> bool:
        """Validate that the provider is accessible."""
        pass
```

### 4. Provider Implementations

Create individual provider files:

```
mcp-server/src/llm_providers/
├── __init__.py
├── base.py
├── config.py
├── factory.py
├── gemini.py
├── openai_provider.py
├── anthropic_provider.py
├── groq.py
├── mistral.py
├── ollama.py
└── mock.py
```

**Example: Gemini Provider**

```python
# mcp-server/src/llm_providers/gemini.py

import os
import time
import httpx
from typing import Optional
from .base import BaseLLMProvider, LLMResponse

class GeminiProvider(BaseLLMProvider):
    """Google Gemini LLM provider."""
    
    @property
    def provider_name(self) -> str:
        return "gemini"
    
    @property
    def default_model(self) -> str:
        return "gemini-1.5-flash"
    
    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> LLMResponse:
        start_time = time.time()
        
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent"
        
        contents = []
        if system_prompt:
            contents.append({"role": "user", "parts": [{"text": system_prompt}]})
            contents.append({"role": "model", "parts": [{"text": "Understood."}]})
        contents.append({"role": "user", "parts": [{"text": prompt}]})
        
        payload = {
            "contents": contents,
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": max_tokens,
            }
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                url,
                json=payload,
                params={"key": self.api_key},
                timeout=60.0
            )
            response.raise_for_status()
            data = response.json()
        
        content = data["candidates"][0]["content"]["parts"][0]["text"]
        tokens = data.get("usageMetadata", {}).get("totalTokenCount", 0)
        
        return LLMResponse(
            content=content,
            model=self.model,
            provider=self.provider_name,
            tokens_used=tokens,
            latency_ms=(time.time() - start_time) * 1000,
            raw_response=data
        )
    
    async def validate_connection(self) -> bool:
        try:
            response = await self.generate("Hello", max_tokens=10)
            return bool(response.content)
        except Exception:
            return False
```

### 5. Provider Factory

```python
# mcp-server/src/llm_providers/factory.py

import os
from typing import Optional
from .base import BaseLLMProvider
from .config import PROVIDER_CONFIGS
from .gemini import GeminiProvider
from .openai_provider import OpenAIProvider
from .anthropic_provider import AnthropicProvider
from .groq import GroqProvider
from .mistral import MistralProvider
from .ollama import OllamaProvider
from .mock import MockProvider

PROVIDER_CLASSES = {
    "gemini": GeminiProvider,
    "openai": OpenAIProvider,
    "anthropic": AnthropicProvider,
    "groq": GroqProvider,
    "mistral": MistralProvider,
    "ollama": OllamaProvider,
    "mock": MockProvider,
}

def get_llm_provider(
    provider_name: Optional[str] = None,
    api_key: Optional[str] = None,
    model: Optional[str] = None,
) -> BaseLLMProvider:
    """Factory function to get the appropriate LLM provider."""
    
    # Get provider from env if not specified
    provider_name = provider_name or os.getenv("LLM_PROVIDER", "mock")
    provider_name = provider_name.lower()
    
    if provider_name not in PROVIDER_CLASSES:
        raise ValueError(f"Unknown provider: {provider_name}. Available: {list(PROVIDER_CLASSES.keys())}")
    
    # Get API key from env if not specified
    if api_key is None:
        config = PROVIDER_CONFIGS.get(provider_name, {})
        api_key_env = config.get("api_key_env")
        if api_key_env:
            api_key = os.getenv(api_key_env)
    
    # Get model from env if not specified
    if model is None:
        model = os.getenv("LLM_MODEL")
    
    provider_class = PROVIDER_CLASSES[provider_name]
    return provider_class(api_key=api_key, model=model)


async def get_llm_provider_with_fallback() -> BaseLLMProvider:
    """Get LLM provider with fallback support."""
    
    primary_provider = os.getenv("LLM_PROVIDER", "mock")
    fallback_provider = os.getenv("LLM_FALLBACK_PROVIDER", "mock")
    
    try:
        provider = get_llm_provider(primary_provider)
        if await provider.validate_connection():
            return provider
    except Exception as e:
        print(f"Primary provider {primary_provider} failed: {e}")
    
    # Try fallback
    if fallback_provider != primary_provider:
        try:
            provider = get_llm_provider(fallback_provider)
            if await provider.validate_connection():
                print(f"Using fallback provider: {fallback_provider}")
                return provider
        except Exception as e:
            print(f"Fallback provider {fallback_provider} failed: {e}")
    
    # Last resort: mock provider
    return get_llm_provider("mock")
```

### 6. Update Tool Implementations

Modify each tool to use the provider factory:

```python
# mcp-server/src/tools/genesis_validate.py

from ..llm_providers.factory import get_llm_provider_with_fallback

async def genesis_validate(concept: str, context: str = "") -> dict:
    """Validate a concept using the Genesis methodology."""
    
    provider = await get_llm_provider_with_fallback()
    
    system_prompt = """You are a Genesis Methodology validator. 
    Analyze the given concept through multiple perspectives:
    1. Innovation potential (Y Agent)
    2. Critical analysis (X Agent)
    3. Ethical considerations (Z Agent)
    4. Security implications (CS Agent)
    """
    
    prompt = f"""
    Concept: {concept}
    Context: {context}
    
    Provide a comprehensive validation analysis.
    """
    
    response = await provider.generate(
        prompt=prompt,
        system_prompt=system_prompt,
        temperature=0.7,
        max_tokens=4096
    )
    
    return {
        "validation": response.content,
        "provider": response.provider,
        "model": response.model,
        "tokens_used": response.tokens_used,
        "latency_ms": response.latency_ms
    }
```

---

## 📝 Implementation Checklist

### Phase 1: Core Infrastructure
- [ ] Create `mcp-server/src/llm_providers/` directory structure
- [ ] Implement `base.py` with abstract base class
- [ ] Implement `config.py` with provider configurations
- [ ] Implement `factory.py` with provider factory

### Phase 2: Provider Implementations
- [ ] Implement `gemini.py` (priority - free tier)
- [ ] Implement `groq.py` (priority - free tier)
- [ ] Implement `openai_provider.py`
- [ ] Implement `anthropic_provider.py`
- [ ] Implement `mistral.py`
- [ ] Implement `ollama.py`
- [ ] Update `mock.py` for testing

### Phase 3: Tool Integration
- [ ] Update `genesis_validate.py` to use provider factory
- [ ] Update `trinity_analyze.py` to use provider factory
- [ ] Update `z_protocol_check.py` to use provider factory
- [ ] Update `reflexion_improve.py` to use provider factory

### Phase 4: Configuration & Documentation
- [ ] Update `.env.example` with all provider options
- [ ] Update `MCP_SETUP_GUIDE.md` with BYOK instructions
- [ ] Update `README.md` Quick Start section
- [ ] Add provider-specific setup guides

### Phase 5: Testing & Deployment
- [ ] Write unit tests for each provider
- [ ] Write integration tests for provider switching
- [ ] Test with free tier providers (Gemini, Groq)
- [ ] Update `CHANGELOG.md`
- [ ] Tag release v0.3.0
- [ ] Deploy to GCP Cloud Run

---

## 🧪 Testing Requirements

### Unit Tests

```python
# tests/test_llm_providers.py

import pytest
from mcp_server.llm_providers.factory import get_llm_provider

def test_get_mock_provider():
    provider = get_llm_provider("mock")
    assert provider.provider_name == "mock"

def test_get_gemini_provider():
    provider = get_llm_provider("gemini", api_key="test-key")
    assert provider.provider_name == "gemini"

def test_unknown_provider_raises():
    with pytest.raises(ValueError):
        get_llm_provider("unknown_provider")

@pytest.mark.asyncio
async def test_mock_provider_generate():
    provider = get_llm_provider("mock")
    response = await provider.generate("Test prompt")
    assert response.content
    assert response.provider == "mock"
```

### Integration Tests

```python
# tests/test_byok_integration.py

import os
import pytest

@pytest.mark.skipif(not os.getenv("GEMINI_API_KEY"), reason="No Gemini API key")
@pytest.mark.asyncio
async def test_gemini_integration():
    from mcp_server.llm_providers.factory import get_llm_provider
    
    provider = get_llm_provider("gemini")
    response = await provider.generate("Say hello in one word")
    
    assert response.content
    assert response.provider == "gemini"
    assert response.tokens_used > 0
```

---

## 📊 Success Criteria

| Criteria | Metric |
|----------|--------|
| All providers implemented | 7/7 providers |
| Unit test coverage | > 80% |
| Integration tests pass | All free tier providers |
| Documentation updated | All files listed |
| Deployment successful | GCP Cloud Run live |
| No breaking changes | Existing mock provider works |

---

## 🔄 Alignment Protocol

After completing this implementation:

1. **Commit all changes** with descriptive message
2. **Push to main branch** on GitHub
3. **Report back** to Manus AI (CTO) with:
   - Files modified/created
   - Tests passed/failed
   - Any issues encountered
   - Deployment status

**GitHub is our communication bridge.** All progress should be trackable through commits.

---

## 📞 Contact

**Manus AI (T), CTO**  
Team YSenseAI  
GitHub: https://github.com/creator35lwb-web/VerifiMind-PEAS

---

*"The methodology is free. The convenience is optional."*
