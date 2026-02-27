# MACP Handoff: CTO T → CTO RNA | Session 9 — v0.4.5 BYOK Live Implementation Guide

**Date:** 2026-02-28
**From:** CTO T (CSO R / Manus AI)
**To:** CTO RNA (Claude Code)
**Priority:** P0 — BYOK is advertised but non-functional in production
**Estimated Effort:** 4 hours

---

## Executive Summary

BYOK (Bring Your Own Key) has been advertised in the README, Smithery listing, and landing page since v0.3.0. The code exists in `config_helper.py` and `server.py` but is **unreachable in GCP Cloud Run production** because the Smithery session config passthrough was lost during the transport migration. This handoff provides the exact implementation plan to make BYOK live.

---

## Current State (v0.4.4)

| Component | Status |
|-----------|--------|
| `VerifiMindConfig` Pydantic model (server.py L50-82) | ✅ Defined — 5 provider keys |
| `_get_provider_from_session_config()` (config_helper.py) | ✅ Coded — reads `ctx.session_config` |
| `get_agent_provider()` 6-step fallback | ✅ Working — env vars only in production |
| Per-tool BYOK params | ❌ NOT implemented — tools don't accept `api_key` or `llm_provider` |
| Smithery config passthrough | ❌ BROKEN — GCP Cloud Run doesn't pass session config |
| Quad CLI G-Agent (Grok) | ✅ Scaffolded — needs xai_api_key in BYOK |

---

## Root Cause

The `create_http_server()` function creates a single FastMCP instance at startup. The Smithery runtime passed user config to `create_server(config)` per-session, but the GCP Cloud Run HTTP transport calls `create_http_server()` once with no user config. The `ctx.session_config` is always `None` in production.

---

## Implementation Plan: Per-Tool-Call BYOK (Option B)

This is the recommended approach because it works with ALL MCP clients (Claude Desktop, Claude.ai, Cursor, etc.) without requiring transport-level changes.

### Step 1: Add BYOK params to all 4 consultation tools

In `mcp-server/src/verifimind_mcp/server.py`, update each tool signature:

```python
# BEFORE (current):
async def consult_agent_x(
    concept_name: str,
    concept_description: str,
    context: Optional[str] = None,
    ctx: Context = None
) -> dict:

# AFTER (v0.4.5):
async def consult_agent_x(
    concept_name: str,
    concept_description: str,
    context: Optional[str] = None,
    llm_provider: Optional[str] = None,
    api_key: Optional[str] = None,
    ctx: Context = None
) -> dict:
```

Apply the same pattern to `consult_agent_z`, `consult_agent_cs`, and `run_full_trinity`.

For `run_full_trinity`, add per-agent overrides:

```python
async def run_full_trinity(
    concept_name: str,
    concept_description: str,
    context: Optional[str] = None,
    save_to_history: bool = True,
    llm_provider: Optional[str] = None,
    api_key: Optional[str] = None,
    x_provider: Optional[str] = None,
    x_api_key: Optional[str] = None,
    z_provider: Optional[str] = None,
    z_api_key: Optional[str] = None,
    cs_provider: Optional[str] = None,
    cs_api_key: Optional[str] = None,
    ctx: Context = None
) -> dict:
```

### Step 2: Create ephemeral provider factory

Add to `config_helper.py`:

```python
# Supported provider key format detection
KEY_FORMAT_PATTERNS = {
    "gsk_": "groq",
    "sk-": "openai", 
    "AIza": "gemini",
    "sk-ant-": "anthropic",
    "xai-": "xai",  # Grok/xAI
}

def create_ephemeral_provider(llm_provider: Optional[str], api_key: Optional[str], agent_id: str = "X"):
    """
    Create a one-time provider from per-tool-call BYOK params.
    Security: Provider is created per-call and garbage collected after use.
    Never stored in server state.
    
    Args:
        llm_provider: Explicit provider name, or None for auto-detect
        api_key: User's API key
        agent_id: Agent ID for fallback to default provider
    
    Returns:
        LLMProvider instance, or None if no BYOK params provided
    """
    if not api_key and not llm_provider:
        return None  # No BYOK — use server default
    
    from .llm import (
        GeminiProvider, GroqProvider, OpenAIProvider,
        AnthropicProvider, MistralProvider, OllamaProvider, MockProvider
    )
    
    # Auto-detect provider from key format if not specified
    if api_key and not llm_provider:
        for prefix, provider_name in KEY_FORMAT_PATTERNS.items():
            if api_key.startswith(prefix):
                llm_provider = provider_name
                break
        if not llm_provider:
            raise ValueError(
                "Cannot auto-detect provider from API key format. "
                "Please specify llm_provider explicitly: "
                "'gemini', 'groq', 'openai', 'anthropic', 'mistral', 'xai'"
            )
    
    provider_map = {
        "gemini": GeminiProvider,
        "groq": GroqProvider,
        "openai": OpenAIProvider,
        "anthropic": AnthropicProvider,
        "mistral": MistralProvider,
        "ollama": OllamaProvider,
        "mock": MockProvider,
    }
    
    if llm_provider not in provider_map:
        raise ValueError(f"Unsupported provider: {llm_provider}. Supported: {list(provider_map.keys())}")
    
    provider_class = provider_map[llm_provider]
    
    if llm_provider in ["mock", "ollama"]:
        return provider_class()
    elif api_key:
        return provider_class(api_key=api_key)
    else:
        # Provider specified but no key — try env var fallback
        return get_agent_provider(agent_id)
```

### Step 3: Update tool handlers to use ephemeral providers

In each tool handler, add BYOK resolution before agent creation:

```python
# In consult_agent_x handler:
try:
    from .config_helper import create_ephemeral_provider, get_agent_provider
    
    # BYOK: User-provided key takes priority
    provider = create_ephemeral_provider(llm_provider, api_key, "X")
    if provider is None:
        # No BYOK — use server default with smart fallback
        provider = get_agent_provider("X", ctx)
    
    agent = XAgent(llm_provider=provider)
    # ... rest of handler
    
    # Add BYOK metadata to response
    response["_provider_used"] = type(provider).__name__.replace("Provider", "").lower()
    response["_byok"] = api_key is not None
```

### Step 4: Update run_full_trinity for per-agent BYOK

```python
# In run_full_trinity handler:
from .config_helper import create_ephemeral_provider, get_trinity_providers

# Per-agent BYOK overrides
providers = {}
for agent_id, (prov, key) in {
    "X": (x_provider or llm_provider, x_api_key or api_key),
    "Z": (z_provider or llm_provider, z_api_key or api_key),
    "CS": (cs_provider or llm_provider, cs_api_key or api_key),
}.items():
    ephemeral = create_ephemeral_provider(prov, key, agent_id)
    providers[agent_id] = ephemeral if ephemeral else get_agent_provider(agent_id, ctx)

x_agent = XAgent(llm_provider=providers["X"])
z_agent = ZAgent(llm_provider=providers["Z"])
cs_agent = CSAgent(llm_provider=providers["CS"])
```

### Step 5: Add xAI/Grok provider for Quad Validation

Create `mcp-server/src/verifimind_mcp/llm/xai_provider.py`:

```python
"""xAI/Grok Provider for VerifiMind BYOK."""
import os
from .provider import LLMProvider, LLMResponse

class XAIProvider(LLMProvider):
    """xAI Grok provider using OpenAI-compatible API."""
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("XAI_API_KEY")
        if not self.api_key:
            raise ValueError("xAI API key required")
        self.base_url = "https://api.x.ai/v1"
        self.model = "grok-4-1-fast-reasoning"
    
    async def generate(self, prompt: str, **kwargs) -> LLMResponse:
        # Use OpenAI-compatible endpoint
        import httpx
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/chat/completions",
                headers={"Authorization": f"Bearer {self.api_key}"},
                json={
                    "model": self.model,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": kwargs.get("temperature", 0.7),
                },
                timeout=60.0
            )
            response.raise_for_status()
            data = response.json()
            return LLMResponse(
                content=data["choices"][0]["message"]["content"],
                model=self.model,
                provider="xai"
            )
```

Register in `llm/__init__.py` and add to `config_helper.py` provider maps.

### Step 6: Update tool descriptions for BYOK awareness

Each tool's docstring should mention BYOK:

```python
"""
Consult X Intelligent agent for innovation and strategy analysis.

BYOK (Bring Your Own Key): Optionally provide your own API key.
- llm_provider: 'gemini' (FREE), 'groq' (FREE), 'openai', 'anthropic', 'mistral', 'xai'
- api_key: Your API key (auto-detects provider from key format if llm_provider not set)
If no BYOK params provided, uses server's default provider (Gemini FREE tier).
"""
```

### Step 7: Version bump and deploy

1. Update `SERVER_VERSION` in both `server.py` and `http_server.py` to `"0.4.5"`
2. Update version docstring at top of `server.py`
3. Deploy to GCP Cloud Run
4. Test BYOK with Groq free key: `gsk_<YOUR_GROQ_KEY_HERE>`

---

## Security Checklist

| Requirement | Implementation |
|-------------|---------------|
| Never store user keys | Ephemeral providers — created per-call, garbage collected |
| Never log user keys | `api_key` param excluded from logging |
| Rate limiting | Already in place (10 req/60s per IP) |
| Input sanitization | Already in place (v0.3.5) |
| Key format validation | `KEY_FORMAT_PATTERNS` validates known formats |
| Error handling | Invalid keys return clear error, don't expose internals |

---

## Test Checklist

```
[ ] consult_agent_x with no BYOK → uses server Gemini (default)
[ ] consult_agent_x with llm_provider="groq", api_key="gsk_..." → uses Groq
[ ] consult_agent_x with api_key="gsk_..." only → auto-detects Groq
[ ] consult_agent_x with invalid api_key → clear error message
[ ] consult_agent_z with BYOK → uses user's provider
[ ] consult_agent_cs with BYOK → uses user's provider
[ ] run_full_trinity with global BYOK → all 3 agents use same provider
[ ] run_full_trinity with per-agent BYOK → X=Gemini, Z=Groq, CS=Anthropic
[ ] run_full_trinity with mixed (some BYOK, some default) → correct routing
[ ] _byok: true in response when user key used
[ ] _provider_used shows correct provider name
[ ] No user keys in server logs
[ ] Rate limiting still works with BYOK
[ ] Health endpoint shows byok_enabled: true
```

---

## Files to Modify

| File | Changes |
|------|---------|
| `mcp-server/src/verifimind_mcp/server.py` | Add BYOK params to 4 tools, update handlers |
| `mcp-server/src/verifimind_mcp/config_helper.py` | Add `create_ephemeral_provider()`, `KEY_FORMAT_PATTERNS` |
| `mcp-server/src/verifimind_mcp/llm/xai_provider.py` | NEW — xAI/Grok provider |
| `mcp-server/src/verifimind_mcp/llm/__init__.py` | Register XAIProvider |
| `mcp-server/http_server.py` | Version bump to 0.4.5, add `byok_enabled: true` to health |

---

## After Deployment: Landing Page Update

Once v0.4.5 is confirmed working, CTO T will:
1. Update landing page BYOK section with "LIVE" badge
2. Add BYOK usage examples to the MCP Server tools section
3. Update inference quality chart to show BYOK vs server-provided split
4. Update Discussion #50 with BYOK announcement

---

## MACP Protocol Compliance

- **Artifact Location:** `.macp/handoffs/20260228_T_session9_v045_byok_implementation.md`
- **Sandbox Boundary:** All code examples reference production paths in `mcp-server/`
- **No secrets in artifact:** Groq test key referenced by description only in test checklist
- **Bidirectional:** Awaiting CTO RNA handoff with deployment confirmation
