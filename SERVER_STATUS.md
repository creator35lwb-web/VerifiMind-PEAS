# VerifiMind-PEAS Server Status

**Last Updated:** April 5, 2026

---

## Current Status: Operational

**v0.5.8 "Trinity Restored" deployed successfully on April 5, 2026**

The VerifiMind MCP server is fully operational with the following capabilities:

- 10 MCP tools (4 core validation + 6 template management)
- 19 pre-built prompt templates across 6 libraries
- **Trinity Restored + Z Guardian Hardened (v0.5.8)**: `run_full_trinity` fixed — compressed `prior_reasoning` (evidence stripped, steps truncated to 300 chars) keeps total request under Groq 12K TPM limit. CS `max_tokens` reduced 8192→4096. Z Guardian veto now code-enforced: `ethics_score < 4.0` triggers auto-veto regardless of LLM output, guarding against prompt dilution regressions. Z prompt restructured — Red Line veto checks moved to TOP with 5 concrete VETO EXAMPLES.
- **Two-Tier Pioneer Program (v0.5.7)**: Pilot (invite-only, 6 months free, 50 slots) + Early Adopter (public, 3 months free, 100 slots). Pilot tier assigned via `PILOT_INVITE_CODE` env var — never hardcoded. `SlotCapReachedError` → 410 Gone with waitlist message. Tier badge + benefit summary on registration success.
- **SYSTEM_NOTICE Sanitization (v0.5.7)**: 280-char max, allow-list `[A-Za-z0-9 .,!?'"-()/:@#]`, URL domain allow-list (`verifimind.ysenseai.org`, `verifimind.io`, `ysenseai.org`). Safe to activate after IAM lockdown (Track D).
- **X Agent v4.3 (v0.5.4)**: Removed VerifiMind internal bias — X now evaluates any concept from the CREATOR's perspective. Dynamic `market_competition` block (real competitors in the concept's own domain). `founder_summary` plain-language synthesis with `verdict`, `what_works`, `things_to_address`, `next_steps`. `research_prompts`: 2-3 ready-to-paste Perplexity/Grok queries for deeper market validation.
- **Token Ceiling Monitor (v0.5.3)**: Z Agent response token tracking — `_z_token_monitor` field in every `run_full_trinity` response with `risk_level` (LOW/MEDIUM/HIGH/CRITICAL), `utilization %`, and `truncated` flag. Server-side WARNING logs on HIGH/CRITICAL.
- **404 Retention Fix (AY COO Report 041)**: Catch-all 404 handler returns actionable JSON with correct MCP endpoint + troubleshooting link — targets 70% drop-off from misconfigured MCP clients.
- **Genesis v4.2 "Sentinel-Verified"**: Forced citation patterns — Z Guardian and CS Security now cite specific framework names in every reasoning step output
- **Z-Protocol v1.1**: 21 frameworks, 4 tiers + `frameworks_cited[]` per step, `scoring_breakdown`, `applicable_frameworks` by tier
- **CS Agent v1.1**: 6-stage, 12-dimension + `stage` + `standards_cited[]` per step, `stages_completed`, `dimensions_evaluated`, `macp_security_assessment`
- Input sanitization active on all tools
- Gemini 2.5-flash as default FREE provider
- Rate limiting and EDoS protection active (registration endpoint exempt)
- GCP Cloud Run revision `verifimind-mcp-server-00287-*` (auto-deployed via CI/CD on PR #114 merge)
- CI/CD pipeline passing (GitHub Actions — all 7 checks pass)

---

## Server Information

| Property | Value |
|----------|-------|
| **Endpoint** | `https://verifimind.ysenseai.org/mcp` |
| **Health Check** | `https://verifimind.ysenseai.org/health` |
| **Register** | `https://verifimind.ysenseai.org/register` |
| **Server Version** | 0.5.8 "Trinity Restored" (deployed April 5, 2026) |
| **Transport** | Streamable HTTP (SSE) |
| **Default Provider** | Gemini 2.5-flash (FREE) |
| **BYOK Providers** | Gemini, OpenAI, Anthropic, Groq, Mistral, Ollama, Perplexity |
| **Monthly Cost** | $0 (GCP free tier) |

---

## Pioneer Program Status

| Tier | Slots Used | Max Slots | Free Months | Access |
|------|-----------|-----------|-------------|--------|
| **Pilot** | 1 | 50 | 6 months | Invite code via SYSTEM_NOTICE (active MCP users) |
| **Early Adopter** | 0 | 100 | 3 months | Public — `/register` |

**Waitlist:** Email `alton@ysenseai.org` or DM `@creator35lwb` on X
**Benefits active from:** v0.6.0-Beta launch (targeted June 2026)

---

## Monitoring

| Feature | Status | Details |
|---------|--------|---------|
| **GCP Uptime Check** | ✅ Active | 5-minute intervals, email alerts |
| **Error Rate Alert** | ✅ Active | Threshold: >50 errors in 5 minutes |
| **Traffic Spike Alert** | ✅ Active | Threshold: >500 requests in 1 hour |
| **CI/CD Pipeline** | ✅ Passing | Unit tests, Bandit, Safety |

---

## Pending Activation (Alton — GCP Console)

| Action | Priority | Blocker for |
|--------|----------|-------------|
| GCP IAM lockdown (Track D) | **HIGH** | SYSTEM_NOTICE activation (Track E) |
| Rotate `GEMINI_API_KEY` + `GROQ_API_KEY` | **HIGH** | Security (exposed Mar 24) |
| Set `PILOT_INVITE_CODE` env var | After Track D | Pilot tier invite flow |
| Set `SYSTEM_NOTICE` env var | After Track D + deploy | Track E (EA cohort invite) |

---

## Resolved Issues

### Issue #1: Gemini Model Deprecation
**Status:** RESOLVED (v0.3.2, January 29, 2026)

Google deprecated `gemini-2.0-flash-exp`. Updated default to `gemini-2.5-flash` (stable, FREE tier).

### Issue #2: Input Sanitization
**Status:** RESOLVED (v0.3.5, January 30, 2026)

Added comprehensive input sanitization to all MCP tools. 29/29 unit tests passing.

---

## Workarounds

If you experience connectivity issues:

1. **Verify URL**: Use `https://verifimind.ysenseai.org/mcp/` (with trailing slash)
2. **Test connectivity**: `curl https://verifimind.ysenseai.org/mcp/`
3. **Use BYOK**: Configure your own API keys for premium providers
4. **Self-Host**: Run your own instance with your API keys

**Full troubleshooting guide**: [MCP_Server_Troubleshooting_Guide.md](docs/MCP_Server_Troubleshooting_Guide.md)

---

## Release Gate Status

| Version | Blind Tests | Gate | Released |
|---------|-------------|------|---------|
| **v0.5.8 "Trinity Restored"** | — | ✅ **CI PASSED** | April 5, 2026 |
| **v0.5.7 "Two-Tier Pioneer"** | — | ✅ **CI PASSED** | April 5, 2026 |
| **v0.5.6 "Gateway"** | CI passing | ✅ **PASSED** | March 23, 2026 |
| **v0.5.2 "Sentinel-Verified"** | 11/11 correct outcomes (L, March 9, 2026) | ✅ **PASSED** | March 9, 2026 |
| v0.5.1 "Sentinel" | Blind #1: partial citations | ⚠️ Gate open | March 7, 2026 |

---

## Maintenance History

| Date | Action | Version | Status |
|------|--------|---------|--------|
| Apr 5, 2026 | Trinity restored — compressed prior_reasoning, Z Guardian veto hardened | v0.5.8 | Complete |
| Apr 5, 2026 | Two-tier Pioneer Program (Pilot + EA), SYSTEM_NOTICE sanitization | v0.5.7 | Complete |
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

## Updates

For real-time updates:

- **GitHub Issues:** [Report or track issues](https://github.com/creator35lwb-web/VerifiMind-PEAS/issues)
- **GitHub Discussions:** [Community support](https://github.com/creator35lwb-web/VerifiMind-PEAS/discussions)

---

*VerifiMind-PEAS FLYWHEEL TEAM*
