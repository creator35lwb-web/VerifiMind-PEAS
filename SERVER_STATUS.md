# VerifiMind-PEAS Server Status

**Last Updated:** July 7, 2026

---

## Current Status: Operational

**v0.5.48 "Scanner Cluster Block" — deployed June 28, 2026**

The VerifiMind MCP server is fully operational. All security gates passed. (Per-version public detail now lives in [GitHub Releases](https://github.com/creator35lwb-web/VerifiMind-PEAS/releases) since the `/changelog` redirect in v0.5.36.)

- 13 MCP tools (4 core Trinity + 6 template management + 3 coordination) — **all free for everyone**
- **Scanner Cluster Block (v0.5.48)**: blocked a coordinated config/secret/RCE scanner cluster — `45.148.10.62` + `45.148.10.67` (CONFIG_SECRET_SCANNER, same `45.148.10.0/24` as probe #23) and `93.123.109.103` (CONFIG_RCE_SCANNER, new class — carried a Node.js `child_process.execSync` RCE probe our Python/FastAPI ignored: zero execution/leak). `TLM-Audit-Scanner` UA-substring block added (rotation-proof). `BLOCKED_IPS` 23 → 26. Zero sensitive-path 200s on all three (Sentinel re-verified live GCP, 30d). `/24` remarked as a watch-item — revisit CIDR only on a 4th IP (Alton 2026-06-28). 613 unit tests; AY+AZ Report 099 + Sentinel forensics — June 28, 2026
- **Model Currency (v0.5.47)**: BYOK frontier menu refreshed + Gemini SDK migration. `GeminiProvider` moved to the supported `google-genai` SDK (enables Gemini 3.x); `gemini-3.1-pro-preview`/`gemini-3.5-flash` added as BYOK options. OpenAI BYOK default → `gpt-5.5` (+ gpt-5.x `max_completion_tokens` fix); Mistral → `mistral-medium-3`. All IDs live-verified before listing. Default free-tier path (Gemini 2.5 Flash + Groq) unchanged — cost/stability preserved. Probe #23 (config/secret scanner) blocked. 699 tests; pre-deploy live Trinity smoke green. R-S51 + T+L S45/S46/S51 — June 23, 2026
- **BYOK Robustness (v0.5.46)**: production-hardening bundle surfaced by dogfooding the M2 P3 evaluation — `provider/model` shorthand now accepted server-side (fixes June-17 prod rejection of valid BYOK configs), Z/CS `max_tokens` raised 4096 → 8192 (Groq clamped per-provider) to stop verbose-model truncation, the Z token-monitor repaired (silently read 0 since v0.5.3), and structured provider evidence coerced to string for schema conformance. Strictly additive — no change to the default free-tier path. 698 tests pass. T+L S46 D-46-1/2 + S47 D-47-1 + Alton — June 19, 2026
- **Probe Blocklist (v0.5.45)**: blocked an MCP-endpoint scanner family polluting engagement metrics — AgentSure-MCPScan (9 IPs; primary `152.55.176.35` logged ~11h of cron-driven fake "engagement"), LeakIX l9scan (2 IPs), and a self-declared `MCP-Inspector (security-scan)` IP (`14.194.11.238`, orchestrator-flagged, Sentinel-confirmed: 330-req/100s dictionary sweep, zero 200, zero leak). `BLOCKED_IPS` 10 → 22; UA-substring blocks added for `AgentSure-MCPScan` / `l9scan` / `(security-scan)` (rotation-proof, live-verified 403). Honest-metrics gate held — AY held Report 097 until this deploy. AY+AZ forensics 2026-06-12 + Sentinel 2026-06-16 — June 16, 2026
- **Reasoning Visible (v0.5.44)**: the auditable reasoning layer is now returned by default. `run_full_trinity` gains a `detail` parameter — `standard` (default) returns a `reasoning` block (per-agent reasoning steps, Z's 5-dimension ethics scoring breakdown + framework citations + jurisdictions, CS threat level + Socratic questions, per-agent inference quality incl. `inference_warning`); `full` adds per-step evidence + the 12-dimension/6-stage/MACP detail; `summary` reproduces the exact prior response shape (opt-out). Strictly additive — no existing field changed. `consult_agent_x/z/cs` gain the same ladder; markdown report renders the breakdown + jurisdictions + threat level + degraded-inference warning. Zero new inference cost (serialization only). T+L Session 41 approved (default `standard`, `full` free). 16 new tests — June 12, 2026
- **Foundation Integrity (v0.5.43)**: three integrity fixes from the Issue #68 foundation audit — (1) ethics-veto fail-safe: degraded Z inference (`partial`/`fallback`) now caps the recommendation at REVISE + emits `inference_warning` instead of allowing a clean pass on synthesized defaults; (2) validation-history privacy: `save_to_history` defaults off and `genesis://history/*` resources return non-identifying aggregates only (no cross-instance concept-text exposure); (3) `genesis://config/master_prompt` now generated from live agent config (was serving a stale prompt collection). Plus current-date injection into agent prompts and `project_info` version currency. 10 new regression tests — June 11, 2026
- **Server-Card Description Refresh (v0.5.42)**: `/.well-known/mcp/server-card.json` refreshed — stale "Genesis v4.2" copy → current descriptors (13 free tools, BYOK 6 providers); docstring de-Smithery'd (listing sunset 2026-03-01); pre-submission accuracy pass — June 9, 2026
- **Register Page Dead-Link Fix (v0.5.41)**: `/register` "check your status" link pointed to `/early-adopters/status/` (bare, 404) — repointed to `/whoami` self-serve endpoint. Last dead link in the registration funnel, caught by Alton — June 5, 2026
- **Registration Funnel Fix + /whoami (v0.5.40)**: Closes Scholar UUID registration funnel leak — `rate_limiter.py` now reads `early_adopters` (single source of truth, D-30-3); `/early-adopters/status/{uuid}` returns `200 + register CTA` instead of `404` for valid unregistered UUIDs; new `/whoami` endpoint for self-serve tier/status check; `claude-opus-4-8` model currency bump — June 5, 2026
- **Registry Scanner Block + P2 Batch-2 (v0.5.39)**: 10th IP added to application-layer blocklist (BLOCKED_IPS: 10 entries total) — `3.137.30.179` (AISEC_REGISTRY_SCANNER); UA `aisec-registry/0.2 (+https://sec.sqrx.io)` on 100% of 400 requests over 5-day cron-like persistence (May 23–27, ~80 req/day); MCP/OAuth surface enumeration (89× POST `/mcp` + 89× GET `/mcp/.well-known/oauth-*` discovery); HTTP 200 = 0 (never reached a real handler), 268× 429, 88× 404. Not a builder, no `/register` intent. AY+AZ forensics 2026-05-30. + SonarCloud P2 batch-2: 8 module-level constants extracted from 25 dup-literal occurrences in `llm/provider.py` (4 provider-default-model constants) and `server.py` (4 agent/prompt constants); behavior-identical refactors; substance preservation per Genesis §13.X proposal — June 1, 2026
- **Scanner Block (v0.5.38)**: 2 additional scanners added to application-layer IP blocklist (9 entries total) — `4.228.83.111` (CMS_WEBSHELL_SCANNER, Azure; null UA, 310 req/7d in 2 bursts, WordPress + PHP webshell dictionary) and `2602:fb54:99a::` (SECRET_SCANNER, IPv6; rotating UA across 18+ browser strings — botnet pattern; 65 req single 15-sec burst probing GCP service-account JSON + .env tree + .git internals). GCP forensic analysis (Sentinel investigation): zero 200 on any sensitive endpoint, zero data leak on either actor; defense layers caught everything (50–60% rate-limited, 13–34% 404). Independent actors (19h apart, different tooling). Address-only block on the IPv6 — no /48 rotation evidence — May 29, 2026
- **Tier Clarity (v0.5.37)**: 429 rate-limit CTA now branches on `uuid_status` — a *misconfigured Scholar* (UUID header present but invalid) gets a recovery hint (`VERIFIMIND_UUID` / `/setup`), while a true anonymous caller gets the register-for-Scholar acquisition CTA (+ BYOK + dashboard, Privacy-Doctrine-v1.0 line, founder/feedback note). `uuid_status` surfaced in the body + warning log. Shipped from a tier-setup audit (T1–T6); the T3/T6 reconciliation (rate-limiter reads empty `ea_registrations` vs real `early_adopters`; single source of truth for caller tier) routed to T (CTO) — May 26, 2026
- **Changelog Hygiene (v0.5.33)**: Retroactively sanitized public `/changelog` to remove specific blocked-IP addresses from v0.5.30 and v0.5.32 entries; matches v0.5.22 / v0.5.26 disclosure pattern. Full forensics preserved in internal `CHANGELOG.md`, PR bodies, and commit history. Added disclosure-policy header to internal CHANGELOG. PR# links added to public v0.5.30 / v0.5.32 entries — May 13, 2026
- **Secret Scanner Block + SonarCloud P1 (v0.5.32)**: 7th IP added to application-layer blocklist — credential/secret enumeration scanner, 788 req single burst on May 12 (probed `.env` variants, `.git/*`, `.terraform.*`, `.stripe/`, `?phpinfo=1`, CI configs). 77% caught by rate limiter; zero leak (4 served 200 = safe root response only). SonarCloud P1 cleanup: extracted `MCP_ENDPOINT_PATH`/`MCP_SERVER_URL`/`MCP_REMOTE_QUICKSTART` constants (removed 13 duplicate literals); refactored `http_exception_handler` cognitive complexity 23 → ≤15; CodeQL `py/empty-except` × 2 resolved; logger.exception() in registration 500 path — May 13, 2026
- **SonarCloud P0 (v0.5.31)**: Resolved 14 SonarCloud Vulnerabilities + 15 BLOCKER severity items per XV's May 12 audit. Workflow permissions scoped to job level; TLS 1.2 explicit minimum; broken `__all__` in templates/library removed; 8 false-positive suppressions with NOSONAR + justification comments; deprecated `datetime.utcnow()` replaced. Expected impact: Security count 14 → 1, BLOCKER 15 → 0 — May 13, 2026
- **Config Scanner Block (v0.5.30)**: `85.121.126.250` added to IP blocklist — config/secret enumeration scanner probed ~25 secret/config paths in 1 second (`/api/env`, `/firebase-config.json`, `/swagger.json`, `/openapi.json`, `/.well-known/jwks.json`, etc.) with rotating user agents. Cost-effective defense for solo builder — Cloud Armor pricing not justified at our scale. 6 IPs blocked total — May 12, 2026
- **Growth-First Pages (v0.5.29)**: `/terms` → v2.1, `/privacy` → v2.2, `/register` benefit cards updated. All pricing removed from public-facing pages. No current paid services. "Growth First, Monetization Later" pledge now consistent across server and landing page. Polar payment infrastructure preserved for future services — May 12, 2026
- **Tools Free (v0.5.28)**: Option B refactor PR1 of 3 — paywall removed from the 3 coordination tools (`coordination_handoff_create`, `coordination_handoff_read`, `coordination_team_status`). `pioneer_key` is now optional; anonymous callers are namespaced under `"anonymous"`. Fulfills Core Tools Always Free pledge ratified May 9, 2026 by L + Alton + T — May 10, 2026
- **Version Alignment (v0.5.27)**: `/mcp/` `serverInfo.version` now reports application version (0.5.27) instead of FastMCP library version (3.2.4); all four version-reporting surfaces consistent. P0 credibility fix per External Model Council review (Claude Opus 4.7 + GPT-5.5 + Gemini 3.1 Pro) — May 10, 2026
- **SSRF Scanner Block (v0.5.26 patch)**: `195.178.110.157` (AS48090 Techoff SRV; 90-req scan, 18 SSRF probes targeting cloud IMDS) added as 5th IP blocklist entry — May 7, 2026
- **Scanner Block + HTTP Compliance (v0.5.26)**: `54.67.34.241` (AWS EC2 us-west-1 unauthorized prober, 96 hits/2d) added to IP blocklist; HEAD `/mcp/` fixed — returns 200 with proper headers (was 405)
- **Health Transparency (v0.5.25)**: `/health` now reports `inference_mode` — `"live"` / `"degraded"` / `"mock"` — resolves 9-day mock-mode blindspot; AY monitoring and GCP uptime checks can now detect env var wipe immediately
- **Cowork Research (v0.5.24)**: XV's strategic analysis of Anthropic Cowork on 3P published at `/research/cowork` — 10 sections, self-correction as Section 5 (real-time Validation Paradox case study), L (CEO) approved; 4-pill research nav across all pages
- **BYOK Hardening (v0.5.23)**: All 7 providers audited — Cerebras key prefix fix (`csk-`), model update (`llama-3.3-70b`), Anthropic JSON fence stripping, Mistral package added, mock transparency (`_warning` field, `"synthetic"` overall_quality)
- **Research Navigation (v0.5.23)**: `/research`, `/library`, `/research/paradox` fully interlinked with consistent `site-nav` + section pill strips
- **IP Blocklist (v0.5.22)**: 3 rogue IPs blocked at application layer (T Security Directive 2026-04-27) — AWS IPv6 fuzzing bot, content scraper (2,007 AbuseIPDB reports), unauthorized YellowMCP scanner; `[IP_BLOCKED]` / `[UA_BLOCKED]` audit logging to GCP log stream
- **P0 Hotfix (v0.5.21)**: All 13 tools now correctly listed in `/.well-known/mcp-config` and Smithery server card (coordination tools were missing since v0.5.16); structured `[TOOL_NOT_FOUND]` logging added to GCP log stream
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
- GCP Cloud Run revision: `verifimind-mcp-server-00465-mdr` (v0.5.48 code + exact SDK pins; auto-deployed 2026-07-06 19:51 UTC by the Cloud Build trigger on the PR #271 pin merge — build `607f90bf` from commit `291c1c6`. Supersedes `00464-4f5`, the 2026-07-02 trigger deploy from PR #269, and `00463-mvj` from the June-28 release deploy)
- CI/CD pipeline passing — 682 tests passing (696 collected, 14 skipped), 0 CodeQL medium+ alerts

---

## Server Information

| Property | Value |
|----------|-------|
| **Endpoint** | `https://verifimind.ysenseai.org/mcp` |
| **Health Check** | `https://verifimind.ysenseai.org/health` |
| **Register** | `https://verifimind.ysenseai.org/register` |
| **Server Version** | 0.5.33 "Changelog Hygiene" (deployed May 13, 2026) |
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
| **CI/CD Pipeline** | ✅ Passing | 510 tests (CI), Bandit, Safety |

---

## Release Gate Status

| Version | Blind Tests | Gate | Released |
|---------|-------------|------|---------|
| **v0.5.22 "IP Blocklist Security Layer"** | CI gate — 628 tests, 0 CodeQL alerts; PR #182 | ✅ **PASSED** | April 30, 2026 |
| **v0.5.21 "P0 Tool Manifest Audit"** | CI gate — 596 tests, 0 CodeQL alerts; PRs #179 #180 #181 | ✅ **PASSED** | April 30, 2026 |
| **v0.5.20 "Root UX + BYOK v0.4.0"** | CI gate — 510 tests, 0 CodeQL alerts; PRs #168 #169 | ✅ **PASSED** | April 27, 2026 |
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
| May 6, 2026 | IP block 54.67.34.241 (unauthorized AWS scanner); HEAD /mcp/ 405→200 fix | v0.5.26 | Complete |
| May 1, 2026 | inference_mode in /health — live/degraded/mock; resolves 9-day mock-mode blindspot | v0.5.25 | Complete |
| Apr 30, 2026 | IP Blocklist middleware — 3 rogue IPs blocked (T Security Directive), [IP_BLOCKED]/[UA_BLOCKED] audit logging | v0.5.22 | Complete |
| Apr 30, 2026 | P0 Tool Manifest Audit — all 13 tools in mcp-config + Smithery; structured [TOOL_NOT_FOUND] logging | v0.5.21 | Complete |
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
