# VerifiMind-PEAS Server Status

**Last Updated:** April 27, 2026

---

## Current Status: Operational

**v0.5.20 "Root UX + BYOK v0.4.0" deployed successfully on April 27, 2026**

The VerifiMind MCP server is fully operational. All security gates passed. 487 tests, 0 CodeQL medium+ alerts. GCP revision `verifimind-mcp-server-00369-7cf`.

- 13 MCP tools (4 core Trinity + 6 template management + 3 coordination)
- **BYOK v0.4.0**: Cerebras provider (llama3.1-70b, 1M tokens/day FREE), `claude-sonnet-4-6` / `claude-opus-4-7` defaults, `gpt-4.1-mini` default, smart fallback chain (BYOK → Groq → Cerebras → mock)
- **Root Page UX**: Copy buttons on all 4 config code blocks, Scholar UUID tier card, URL tip callout directing users to `/mcp/` with trailing slash
- **BYOK Guide (P0 fix)**: `gemini-2.0-flash` (deprecated March 31, 2026) replaced with `gemini-2.5-flash`; Claude.ai Opus 4.7 API key classifier warning; Model Freshness deprecation table
- **UUID Tier-Aware Rate Limiting (v0.5.19)**: Anonymous 10 req/60s / Scholar 30 req/60s / Pioneer 100 req/60s; `X-RateLimit-Tier` on every response
- **Validation Paradox (v0.5.19)**: All 6 FLYWHEEL TEAM reflections published at `/research/paradox`
- **Scholar Dashboard (v0.5.18)**: `GET /early-adopters/dashboard/{uuid}` — personal Trinity validation history
- **UUID Header Auto-Flow (v0.5.17)**: `X-VerifiMind-UUID` auto-sent via mcp-remote on every call
- **Polar Pioneer Tier ($9/mo, v0.5.13)**: Circuit breaker, fail-closed, 20+ sanitization patterns
- **Z-Protocol v1.1**: 21 frameworks, 4 tiers + `frameworks_cited[]` per step
- **CS Agent v1.1**: 6-stage, 12-dimension, OWASP Agentic AI Top 10
- Input sanitization active (20+ secret patterns)
- Rate limiting and EDoS protection active
- GCP Cloud Run revision: `verifimind-mcp-server-00369-7cf`
- CI/CD pipeline passing — 487 tests, 0 CodeQL medium+ alerts

---

## Server Information

| Property | Value |
|----------|-------|
| **Endpoint** | `https://verifimind.ysenseai.org/mcp` |
| **Health Check** | `https://verifimind.ysenseai.org/health` |
| **Register** | `https://verifimind.ysenseai.org/register` |
| **Server Version** | 0.5.20 "Root UX + BYOK v0.4.0" (deployed April 27, 2026) |
| **Transport** | Streamable HTTP (SSE) |
| **Default Provider** | Gemini 2.5 Flash (FREE) / Groq Llama 3.3 (FREE fallback) |
| **BYOK Providers** | Gemini, Groq, Cerebras (FREE), OpenAI, Anthropic, Mistral, Ollama |
| **Monthly Cost** | ~$0 normal usage (GCP free tier + Gemini free) |

---

## Pioneer Program Status

| Tier | Slots Used | Max Slots | Free Months | Access |
|------|-----------|-----------|-------------|--------|
| **Pilot** | 1 | 50 | 6 months | Invite code via SYSTEM_NOTICE (active MCP users) |
| **Early Adopter** | 0 | 100 | 3 months | Public — `/register` |

**Benefits active from:** v0.6.0-Beta launch (targeted June 2026)
**Waitlist:** Email `alton@ysenseai.org` or DM `@creator35lwb` on X

---

## Monitoring

| Feature | Status | Details |
|---------|--------|---------|
| **GCP Uptime Check** | ✅ Active | 5-minute intervals, email alerts |
| **Error Rate Alert** | ✅ Active | Threshold: >50 errors in 5 minutes |
| **Traffic Spike Alert** | ✅ Active | Threshold: >500 requests in 1 hour |
| **CI/CD Pipeline** | ✅ Passing | Unit tests, Bandit, Safety |

---

## Release Gate Status

| Version | Blind Tests | Gate | Released |
|---------|-------------|------|---------|
| **v0.5.20 "Root UX + BYOK v0.4.0"** | CI gate — 487 tests, 0 CodeQL alerts; PRs #168 #169 | ✅ **PASSED** | April 27, 2026 |
| **v0.5.19 "Validation Paradox"** | UUID rate limiter + 404 fixes + research publication | ✅ **PASSED** | April 21, 2026 |
| **v0.5.14–v0.5.18** | Coordination layer, UUID tracer, Scholar dashboard chain | ✅ **PASSED** | April 2026 |
| **v0.5.13 "Fortify"** | Security gate — 485 tests, 0 CodeQL alerts, X-Agent 4/4 conditions met | ✅ **PASSED** | April 12, 2026 |
| **v0.5.10 "Trinity Verified"** | 3/3 (HireAI veto, Recipe Buddy proceed, Kuih proceed) — Alton, April 5, 2026 | ✅ **PASSED** | April 5, 2026 |
| **v0.5.9 "BYOK Model Refresh"** | Anthropic BYOK unblocked | ✅ **PASSED** | April 5, 2026 |
| **v0.5.8 "Trinity Restored"** | Trinity pipeline restored | ✅ **PASSED** | April 5, 2026 |
| **v0.5.7 "Two-Tier Pioneer"** | — | ✅ **CI PASSED** | April 5, 2026 |
| **v0.5.6 "Gateway"** | CI passing | ✅ **PASSED** | March 23, 2026 |
| **v0.5.2 "Sentinel-Verified"** | 11/11 correct outcomes (L, March 9, 2026) | ✅ **PASSED** | March 9, 2026 |
| v0.5.1 "Sentinel" | Blind #1: partial citations | ⚠️ Gate open | March 7, 2026 |

---

## Maintenance History

| Date | Action | Version | Status |
|------|--------|---------|--------|
| Apr 27, 2026 | BYOK v0.4.0 (Cerebras, claude-sonnet-4-6, gpt-4.1-mini) + root UX + BYOK guide P0 fix | v0.5.20 | Complete |
| Apr 21, 2026 | UUID tier-aware rate limiter + 404 churn fixes + Validation Paradox publication | v0.5.19 | Complete |
| Apr 21, 2026 | Scholar Dashboard GET /early-adopters/dashboard/{uuid} | v0.5.18 | Complete |
| Apr 21, 2026 | UUID header auto-flow via mcp-remote, MCP Registry v2.5.0 | v0.5.17 | Complete |
| Apr 21, 2026 | Coordination layer — 3 MACP coordination tools | v0.5.16 | Complete |
| Apr 21, 2026 | UUID tracer P1-A, Z-Guardian hardened | v0.5.15 | Complete |
| Apr 21, 2026 | 3-tier conflict resolution, AI Council | v0.5.14 | Complete |
| Apr 12, 2026 | Polar circuit breaker + fail-closed + 20+ sanitization patterns + 485 tests, 0 CodeQL alerts | v0.5.13 | Complete |
| Apr 12, 2026 | /register endpoint, Phase 2 tier-gate (Polar), Firestore handoffs, sanitization active | v0.5.13 | Complete |
| Apr 5, 2026 | Z max_tokens 8192→4096 + Cloud Run 600s timeout | v0.5.10 | Complete |
| Apr 5, 2026 | Anthropic BYOK model refresh (Claude 4 family) + OpenAI model update | v0.5.9 | Complete |
| Apr 5, 2026 | Trinity token overflow fix + Z Guardian veto hardened | v0.5.8 | Complete |
| Apr 5, 2026 | Two-tier Pioneer Program + SYSTEM_NOTICE activation | v0.5.7 | Complete |
| Mar 23, 2026 | UUID + EA registration (Firestore), /register + /optout UI, MCP Registry v2.3.0 | v0.5.6 | Complete |
| Mar 13, 2026 | TrinitySynthesis Pydantic schema fix (founder_summary field) | v0.5.5 | Complete |
| Mar 13, 2026 | X Agent v4.3 + founder_summary + research_prompts | v0.5.4 | Complete |
| Mar 12, 2026 | Token Ceiling Monitor (Z Agent) | v0.5.3 | Complete |
| Mar 9, 2026 | Genesis v4.2 + v0.5.2 deployed — Release Gate PASSED | v0.5.2 | Complete |
| Mar 7, 2026 | Z-Protocol v1.1 Sentinel + CS Agent v1.1 deployed | v0.5.1 | Complete |
| Mar 1, 2026 | BYOK v2 (per-agent keys) + SessionContext deployed | v0.5.0 | Complete |
| Jan 30, 2026 | Unified Prompt Templates deployed | v0.4.0 | Complete |
| Jan 30, 2026 | Input sanitization deployed | v0.3.5 | Complete |
| Jan 29, 2026 | Gemini 2.5-flash model update | v0.3.2 | Complete |
| Jan 29, 2026 | Smart Fallback + Rate Limiting | v0.3.1 | Complete |
| Jan 28, 2026 | BYOK multi-provider support | v0.3.0 | Complete |

---

## Resolved Issues

### Issue #1: Gemini Model Deprecation
**Status:** RESOLVED (v0.3.2, January 29, 2026)

### Issue #2: Input Sanitization
**Status:** RESOLVED (v0.3.5, January 30, 2026)

### Issue #3: Trinity Token Overflow (Groq 12K limit)
**Status:** RESOLVED (v0.5.8, April 5, 2026)
Compressed prior reasoning from ~17,900 → ~8,400 tokens.

### Issue #4: Anthropic BYOK 404 (Retired Model Strings)
**Status:** RESOLVED (v0.5.9, April 5, 2026)
All Claude 3.x model IDs updated to Claude 4 family.

### Issue #5: Cloud Run 60s Timeout (Anthropic Trinity)
**Status:** RESOLVED (v0.5.10, April 5, 2026)
Cloud Run timeout increased from 60s → 600s.

---

## Workarounds

If you experience connectivity issues:

1. **Verify URL**: Use `https://verifimind.ysenseai.org/mcp/` (with trailing slash)
2. **Test connectivity**: `curl https://verifimind.ysenseai.org/mcp/`
3. **Use BYOK**: Configure your own API keys for premium providers
4. **Self-Host**: Run your own instance with your API keys

**Full troubleshooting guide**: [MCP_Server_Troubleshooting_Guide.md](docs/MCP_Server_Troubleshooting_Guide.md)
