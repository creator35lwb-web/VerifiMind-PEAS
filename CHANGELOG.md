# Changelog

All notable changes to the VerifiMind PEAS project will be documented in this file.

Full version history also available at [verifimind.ysenseai.org/changelog](https://verifimind.ysenseai.org/changelog).

---

## v0.5.13 - Fortify: Production Hardening (April 12, 2026)

Production security hardening sprint. All 4 X-Agent AI Council conditions from PR #131 review resolved. Zero CodeQL medium+ alerts.

### Security Hardening
- **Polar circuit breaker**: 5-failure/60s window → OPEN state; half-open recovery after 60s timeout
- **Fail-closed production semantics**: Any Polar failure when `POLAR_ACCESS_TOKEN` is set → access denied (not env-var fallback). Env-var fallback restricted to local dev.
- **Retry with backoff**: 3 attempts, 1s → 2s delay; 404/401 not retried (terminal errors)
- **Sanitization expanded**: `_SECRET_PATTERNS` 6 → 20 providers — GitHub (PAT/OAuth/server), AWS AKIA, payment keys (sk_live_/sk_test_/pk_live_), Polar, Hugging Face, Replicate, SendGrid, Twilio, Mailgun, Slack, JWT, Bearer, Azure, catch-all high-entropy contexts

### New Endpoint
- `/register` (lightweight) — consent-only UUID registration for anonymous Scholars (no email required, zero PII)

### Phase 2 Tier-Gate
- `_validate_pioneer_key()` now calls `PolarAdapter.check_pioneer_access()` when `POLAR_ACCESS_TOKEN` is set — billing is now real-time enforced

### UUID Audit
- `generate_ea_uuid()` CSPRNG source documented: `os.urandom()` (OS entropy), RFC 9562 UUIDv7, audit trail in module docstring

### CodeQL Clean
- Fixed 3 `py/stack-trace-exposure` (Pydantic `str(e)` → static field hints in registration/feedback/lightweight-register handlers)
- Removed 3 unused imports + 1 unused variable (all in test files)
- **Result: 0 medium+ CodeQL alerts open**

### Testing
- 485 tests passed, 0 failed
- Billing-critical coverage: `registration.py` 94%, `tier_gate.py` 100%, `polar_adapter.py` 96%, `polar_client.py` 100%, `uuid_helper.py` 100%, `polar_webhook.py` 88%

### Pull Requests
- PR #131 (v0.5.13 Fortify base), PR #133 (hardening sprint — all 4 X-Agent conditions)

### Credits
- Implementation: RNA (Claude Code, CSO)
- Specification: T (Manus AI, CTO) — PIN `20260410_T_rna_v0513_hardening_sprint.md`
- Quality Gate: X-Agent (AI Council Analyst/Perplexity) — 4 hardening conditions
- Architecture: XV (Perplexity, CIO) — UUID identity spine + Polar MOR validation
- Human Orchestrator: Alton

---

## v0.5.12 - Polar Integration + Legal v2.0 (April 8, 2026)

Polar payment integration, Legal Pages v2.0, UUID Tracer, /changelog endpoint.

### Polar Integration
- **PolarClient** — Customer State API, `has_pioneer_access()` check
- **PolarAdapter** — 5-minute TTL cache, singleton, webhook-driven cache invalidation
- **Webhook endpoint** `POST /api/webhooks/polar` — Standard Webhooks HMAC verification, 6 subscription events

### Legal Pages v2.0
- **Privacy Policy v2.0** — Polar as Merchant of Record, payment data retention, GDPR/PDPA/Z-Protocol v1.1 compliance
- **Terms & Conditions v2.0** — Service tier table (Scholar/EA/PILOT/Pioneer $9/mo), Polar billing §4.1-4.4, 14-day refund policy, Malaysia governing law

### New Endpoints
- `/changelog` — Full version history (this file, rendered as HTML)

### Analytics
- **UUID Tracer** — `TRACER_UUID:` stdout logging in all 3 coordination tools for GCP log analytics bridge

### Testing
- 312 tests, 52.76% coverage

### Pull Requests
- PR #123 (PolarClient + PolarAdapter), PR #124 (UUID Tracer), PR #125 (Legal v2.0 pages)

### Credits
- Implementation: RNA (Claude Code, CSO)
- Legal Content: T (Manus AI, CTO)
- Human Orchestrator: Alton

---

## v0.5.11 - Coordination Foundation (April 7, 2026)

Multi-agent coordination handoff tools with Pioneer tier-gate.

### New MCP Tools (3)
- **`coordination_handoff_create`** — Structured handoff from one agent session to another
- **`coordination_handoff_read`** — Retrieve handoff artifacts by UUID
- **`coordination_team_status`** — Live FLYWHEEL TEAM status (available to Pioneer tier)

### Tier-Gate Middleware
- Scholar (free) vs Pioneer (paid) access control via `check_tier()`
- Phase 1: `PIONEER_ACCESS_KEYS` env var validation (Phase 2 Polar wiring in v0.5.13)

### Testing
- 308 tests

### Pull Requests
- PR #122

### Credits
- Implementation: RNA (Claude Code, CSO)
- Architecture: T (Manus AI, CTO)
- Human Orchestrator: Alton

---

## v0.5.10 - Trinity Verified (April 5, 2026)

End-to-end Trinity validation verified with real multi-model inference. Timeout + token fixes.

### Fixes
- 600-second timeout for long-running Trinity validation sessions
- Z Guardian `max_tokens` enforcement (8,192 ceiling)
- Prior reasoning compression — resolves Z Agent token overflow

### BYOK Update
- Anthropic Claude 4 family added: `claude-opus-4-6`, `claude-sonnet-4-6`

### Registration
- Two-tier PILOT/EA registration with invite codes

### Testing
- 290 tests

### Credits
- Implementation: RNA (Claude Code, CSO)
- Specifications: T (Manus AI, CTO)
- Human Orchestrator: Alton

---

## v0.5.9 - BYOK Model Refresh (April 4, 2026)

Claude 4 family support added to BYOK provider.

### BYOK
- `claude-opus-4-6` and `claude-sonnet-4-6` added to Anthropic provider
- Model list updated across all agents

### Credits
- Implementation: RNA (Claude Code, CSO)

---

## v0.5.8 - Trinity Restored + Z Guardian Hardened (April 3, 2026)

Z Guardian reliability hardened. Trinity pipeline restored to full operation.

### Z Guardian
- Hardened `max_tokens` guardrail — prevents mid-JSON truncation
- Token ceiling monitor active on all agent calls

### Trinity
- Full X-Z-CS pipeline verified end-to-end
- Prompt structure aligned with Genesis v4.2 citation architecture

### Credits
- Implementation: RNA (Claude Code, CSO)
- Specifications: T (Manus AI, CTO)

---

## v0.5.7 - Two-Tier Pioneer + SYSTEM_NOTICE (March 29, 2026)

Invite-code access tiers and server-side context injection.

### Access Tiers
- Two-tier system: PILOT (invite-only) + EA (Early Adopter)
- PILOT detection at registration endpoint

### SYSTEM_NOTICE
- Server-side context injection for all tool calls
- Enables version and policy notices without client-side changes

### Credits
- Implementation: RNA (Claude Code, CSO)
- Strategy: T (Manus AI, CTO)

---

## v0.5.6 - Gateway (March 23, 2026)

Early Adopter Registration Gateway deployed. Privacy Policy v1.0 + T&C v1.0. Z-Protocol consent-first design. PR #99.

### Early Adopter Registration
- **Registration Gateway** live at `verifimind.ysenseai.org/register` with consent-first Z-Protocol design
- **Privacy Policy v1.0** and **Terms of Service v1.0** — T-reviewed, Z-Protocol compliant
- **Opt-Out System** with UUID-based data deletion at `/optout`
- **Firestore** as EA data store (native to GCP, free tier covers EA volume)

### Phase 55 Metrics (Report 062 — W12 Fully Closed)

| Metric | Value | Change from v0.5.5 |
|--------|-------|--------------------|
| Verified Engagement Hours | 2,250+ | +150 from 2,100+ |
| Value Confirmation Rate | 96.0% | +32.3pp from 63.7% |
| Total Users | 1,480+ | +280 from 1,200+ |
| Test Count | 290 | +82 from 208 |
| GCP Revision | 00282-qm4 | New deployment |

### DFSC 2026
- Campaign live on Mystartr: [rewards.mystartr.com/projects/verifimind](https://rewards.mystartr.com/projects/verifimind)
- Pitch deck v3.3 submitted (14 slides)

### Landing Page (verifimind.io)
- Updated hero banner with v0.5.6 branding and Phase 55 metrics
- EA Registration CTA section with direct link to registration
- Mystartr campaign section with all 4 reward tiers
- Service Analytics Dashboard updated through W12

### Wiki
- **Early Adopter Program** page created by RNA (CSO) with API docs, curl examples, and Z-Protocol compliance details

### Credits
- EA Gateway Implementation: RNA (Claude Code, CSO)
- Landing Page & Documentation: T (Manus AI, CTO)
- Metrics Validation: AY (Antigravity, COO)
- Human Orchestrator: Alton (L)

---

## v0.5.5 - Trinity Quality Baseline (March 13, 2026)

Critical schema regression fix for `run_full_trinity`. Quality baseline for v0.6.0. PR #89.

### Bug Fixes
- **Critical:** Fixed `founder_summary` field assigned as post-construction Python attribute on Pydantic `BaseModel` — Pydantic rejects at runtime. Declared as proper `Optional[dict]` field in `TrinitySynthesis`.
- Individual agent calls (`consult_agent_x/z/cs`) were unaffected throughout.

### Testing
- 208/208 tests passing
- 3 regression tests added to guard against schema-class bugs

### Credits
- Implementation: RNA (Claude Code, CSO)
- Diagnosis: T (Manus AI, CTO)

---

## v0.5.4 - X Agent v4.3 + Token Monitor (March 12, 2026)

X Agent creator-centric rewrite, founder_summary layer, research_prompts bridge, Token Ceiling Monitor. PRs #83–88.

### X Agent v4.3 — Creator-Centric
- Removed VerifiMind self-referential bias from X Agent analysis
- Creator-centric evaluation: focuses on the concept being analyzed, not VerifiMind itself
- `founder_summary` plain-language layer for non-technical stakeholders

### New MCP Tools
- **`research_prompts`** — Generates optimized prompts for Perplexity/Grok research bridge
- **Token Ceiling Monitor** — Tracks token usage against 8,192 ceiling per agent

### Testing
- 208/208 tests passing
- 54.3% coverage

### Credits
- Implementation: RNA (Claude Code, CSO)
- Specifications: T (Manus AI, CTO)

---

## v0.5.3 - Phase 47 Ground Truth (March 15, 2026)

Forensic deduplication audit. Engagement metrics corrected to verified Ground Truth baseline.

### Data Integrity
- **Phase 47 Ground Truth Reset:** COO AY's forensic audit identified 37.4% duplicate session inflation
- **Engagement Hours:** Corrected from ~4,000 to **2,100+** (forensic deduplication)
- **Value Confirmation Rate:** Corrected from 84.5% to **63.7%** (100% unique `insertId` baseline)
- **Users:** Corrected to **1,200+** (bot sessions deduplicated, actual user count increased)
- **Ingestion Registry:** Implemented `ingestion_registry.json` safeguard to prevent future duplication

### Transparency
- Full correction documented in README with Phase 47 Forensic Audit section
- "We believe honest self-correction builds stronger credibility than inflated numbers."

### Credits
- Forensic Audit: AY (Antigravity, COO)
- Documentation: T (Manus AI, CTO)
- Human Orchestrator: Alton (L)

---

## v0.5.2 - Sentinel-Verified (March 9, 2026)

Genesis v4.2 citation enforcement. Release gate PASSED (11/11 blind tests). PRs #77–78.

### Genesis v4.2 "Sentinel-Verified" — Forced Citation Architecture

T's C-S-P methodology (Compression, Selection, Precision) applied to all 3 agents:

**Z Guardian v4.2:**
- `frameworks_cited[]` per reasoning step — compressed codes (e.g., `"GDPR"`, `"EU-AI-Act"`, `"SG-MGF"`), max 5 per step
- `scoring_breakdown` — per-dimension scores with framework attribution (5 dimensions × score + weight + frameworks)
- `applicable_frameworks` — full framework names organized by tier, output once at end (not repeated per step)
- `total_frameworks_evaluated` — count of unique frameworks across all applicable tiers
- **Token efficiency:** Z Agent ~7,500 → ~4,450 tokens (45.8% headroom below 8,192 ceiling)

**CS Security v1.1 Sentinel-Verified:**
- `stage` field per reasoning step (6-stage pipeline now explicit in output)
- `standards_cited[]` per reasoning step
- `stages_completed[]` — all 6 stages reported in every response
- `dimensions_evaluated` — all 12 dimensions (6 traditional + 6 agentic) with findings
- `macp_security_assessment` — 6 MACP v2.0 security properties evaluated
- `standards_referenced` — all standards actually cited in the analysis

**X Agent v4.2:**
- `competitive_analysis` object — explicit positioning vs LangChain, CrewAI, AutoGen, OpenAI Swarm + `unique_moat`

### Pydantic Schema (reasoning.py)
8 new Optional fields — all backward-compatible, zero regressions:
- `XAgentAnalysis.competitive_analysis`
- `ZAgentAnalysis.scoring_breakdown`, `applicable_frameworks`, `total_frameworks_evaluated`
- `CSAgentAnalysis.stages_completed`, `dimensions_evaluated`, `macp_security_assessment`, `standards_referenced`

### Release Gate
- Blind Test #3 PASSED — L (GODEL), March 9, 2026
- 11 Trinity runs across 8 concepts — zero misclassifications
- Citation strategy confirmed: compressed codes are token-efficiency anchors
- CTO sign-off: Issue #34 closed

### MCP Registry
- `server.json` v2.2.0 — 10 tools listed, updated keywords and description
- Registry: `io.github.creator35lwb-web/verifimind-genesis`

### Testing
- 198/198 tests passing (unchanged from v0.5.1)

### Credits
- Implementation: RNA (Claude Code, CSO)
- Citation mitigation strategy: T (Manus AI, CTO) — C-S-P methodology
- Blind testing: L (GODEL)
- Sign-off: T (Manus AI, CTO)

---

## v0.5.1 - Sentinel (March 7, 2026)

Sentinel architecture deployed. Z-Protocol v1.1 + CS Security v1.1. PRs #71–75.

### Z-Protocol v1.1 "Sentinel" — 21 Frameworks, 4-Tier Jurisdictional

Upgraded from 12 flat frameworks to 21 frameworks in a 4-tier jurisdictional architecture:

| Tier | Jurisdiction | Frameworks |
|------|-------------|-----------|
| Tier 1 | International (always applied) | NIST AI RMF, NIST Agent Standards, UNESCO, OECD, ISO/IEC 42001, Berkeley CLTC |
| Tier 2 | EU/EEA | EU AI Act (Digital Omnibus), Article 50 watermarking, GDPR, EU Cybersecurity Act |
| Tier 3 | US | CCPA, CA TFAIA, CA SB 942, TX RAIGA, Colorado AI Act |
| Tier 4 | ASEAN | Malaysia PDPA 2025, Singapore Agentic AI MGF, Vietnam AI Law 134/2025 |

**New 6th red line veto trigger:** Undisclosed AI-generated content in regulated contexts

### CS Security Agent v1.1 "Sentinel" — 6-Stage, 12-Dimension

Upgraded from 4-stage/6-dimension to 6-stage/12-dimension:

**2 new stages:**
- Stage 2: Agentic Threat Analysis (OWASP Top 10 for Agentic AI Applications)
- Stage 5: Reasoning-Layer Audit (tool poisoning, tool shadowing, rugpull detection)

**6 new agentic dimensions:**
Agent Identity Verification, Reasoning Integrity, Tool Call Validation, Memory/State Integrity, Cross-Agent Trust, Human Override Effectiveness

**MACP v2.0 security properties assessed per run:**
Git audit trail, Human-gated execution, Platform isolation, Credential separation, Artifact integrity, Transport security

### Socratic Questions
- Minimum 5 (up from 3)
- 4 categories: Adversarial Thinking, Scale Testing, Failure Mode, Human Override

### Testing
- 198/198 tests passing

### Credits
- Specifications: T (Manus AI, CTO)
- Implementation: RNA (Claude Code, CSO)
- Validation: L (GODEL)

---

## v0.5.0 - Foundation (March 1, 2026)

The architectural hardening release. Z-Protocol Approved (9.2/10). PR #60.

### SessionContext Tracing
- 8-character `_session_id` correlation token per Trinity run
- Ephemeral, never stored — debugging only
- Enables per-run tracing across all agents

### Error Handling v2
- `build_error_response()` — structured, consistent errors across all 10 tools
- Error responses include tool name, error type, and actionable guidance

### Health Endpoint v2
- `health_version: 2` with richer diagnostics
- Session tracking status and BYOK availability
- Provider health checks

### Smithery Removal
- Fully self-hosted on GCP Cloud Run
- Zero external dependencies
- MIGRATION.md added for Smithery users

### BYOK Hardening
- Retry logic for provider calls
- Graceful degradation for invalid keys
- Provider health checks integrated into health endpoint

### Documentation
- `docs/BYOK_GUIDE.md` — comprehensive BYOK usage guide
- `docs/SECURITY_SPEC.md` — Z-Protocol security specification
- `MIGRATION.md` — Smithery → direct connection migration guide

### Testing
- 205 automated tests (up from 175)
- 55.1% coverage (up from 53.6%)
- All 10 acceptance criteria met

### Credits
- Implementation: CTO RNA (Claude Code)
- Strategy & Public Materials: CSO R (Manus AI)
- Metrics Validation: COO AY (Antigravity)
- Human Orchestrator: L

---

## v0.4.5 - BYOK Live (February 28, 2026)

Per-tool-call BYOK with ephemeral provider factory. PR #55.

### New Features
- Per-tool-call BYOK: `api_key` and `llm_provider` parameters on every tool
- Ephemeral provider factory — keys never stored
- Auto-detect key format (gsk_ → Groq, sk-ant- → Anthropic, sk- → OpenAI)
- 7+ provider support: Gemini, OpenAI, Anthropic, Groq, Mistral, Ollama, xAI

### Testing
- Triple-validated: Manus AI 6/6, Claude Code 6/6, CI 175 tests

### Credits
- Implementation: CTO RNA (Claude Code)
- Validation: CSO R (Manus AI)

---

## v0.4.4 - Version Bump + Favicon Fix (February 27, 2026)

### Bug Fixes
- Version bump alignment across all endpoints
- Favicon 48x48 with base64 Content-Security-Policy fix

### Credits
- Implementation: CTO RNA (Claude Code)

---

## v0.4.3 - Multi-Model Trinity + Y-Agent (February 26, 2026)

### New Features
- Y-Agent (Innovator) added to the council
- Multi-model trinity: Y (Innovator) + X (Analyst) + Z (Guardian) + CS (Validator)
- 4-agent architecture established

### Credits
- Implementation: CTO RNA (Claude Code)
- Architecture: CSO R (Manus AI)

---

## v0.4.0 - Unified Prompt Templates (January 30, 2026)

### New MCP Tools (6 new tools, 10 total)

| Tool | Purpose | Parameters |
|------|---------|------------|
| `list_prompt_templates` | List/filter templates | agent_id, category, tags |
| `get_prompt_template` | Get template by ID | template_id, include_content |
| `export_prompt_template` | Export to MD/JSON | template_id, format |
| `register_custom_template` | Create custom template | name, agent_id, content, ... |
| `import_template_from_url` | Import from URL/Gist | url, validate |
| `get_template_statistics` | Registry statistics | - |

### Template Library (6 libraries, 18+ templates)

| Library | Agent | Genesis Phase | Templates |
|---------|-------|---------------|-----------|
| `startup_validation` | X | Phase 1 | 3 |
| `market_research` | X | Phase 1 | 3 |
| `ethics_review` | Z | Phase 2 | 3 |
| `security_audit` | CS | Phase 3 | 3 |
| `technical_review` | CS | Phase 3 | 3 |
| `trinity_synthesis` | ALL | Phase 4 | 3 |

### Template Features
- **Prompt Export** - Download as Markdown/JSON with full documentation
- **Custom Variables** - User-defined placeholders with validation
- **Version Control** - Template versioning and changelog
- **Import from URL** - GitHub Gist and raw file support
- **Provider Compatibility** - Multi-LLM awareness matrix
- **Genesis Methodology Tags** - Phase alignment (phase-1 to phase-4)

### Files Added
- `templates/models.py` - PromptTemplate, TemplateVariable models
- `templates/registry.py` - TemplateRegistry singleton
- `templates/export.py` - Markdown/JSON export utilities
- `templates/import_url.py` - URL/Gist import functionality
- `templates/library/*.yaml` - 6 template library files

### Files Modified
- `server.py` - Added 6 new MCP tools, version 0.4.0
- `http_server.py` - Updated tool count to 10, version 0.4.0

### Credits
- Implementation: Claude Code
- Architecture Review: Manus AI (CTO)

---

## v0.3.5 - Input Sanitization + Security Hardening (January 30, 2026)

### Security Enhancements

#### Input Sanitization Module
Comprehensive input sanitization for all MCP tools to protect against:

| Attack Type | Protection | Status |
|------------|------------|--------|
| Prompt Injection | Pattern detection + logging | Active |
| XSS Attacks | HTML entity escaping | Active |
| Null Byte Injection | Control character removal | Active |
| Input Length Abuse | Field truncation | Active |

**Sanitization Functions:**
- `sanitize_concept_name()` - Concept name sanitization (max 200 chars)
- `sanitize_description()` - Description sanitization (max 10,000 chars)
- `sanitize_category()` - Category sanitization (max 100 chars)
- `sanitize_context()` - Context sanitization (max 5,000 chars)
- `sanitize_concept_input()` - Full concept input sanitization
- `detect_prompt_injection()` - Pattern-based injection detection
- `is_safe_input()` - Quick safety check

**Prompt Injection Detection Patterns:**
- "ignore previous/all instructions"
- "disregard all previous prompts"
- "you are now a..."
- System prompt markers ([INST], <|im_start|>, etc.)
- Role hijacking attempts

### Integration
All four MCP tools now sanitize inputs:
- `consult_agent_x` - Sanitized
- `consult_agent_z` - Sanitized
- `consult_agent_cs` - Sanitized
- `run_full_trinity` - Sanitized

### Files Modified
- `mcp-server/src/verifimind_mcp/server.py` - Added sanitization to all tools
- `mcp-server/src/verifimind_mcp/utils/sanitization.py` - Fixed pattern for "disregard all previous"
- `mcp-server/http_server.py` - Updated version to v0.3.5

### Files Created
- `mcp-server/requirements.txt` - For CI/CD compatibility

### Testing
- 29/29 sanitization unit tests passing
- Server imports successfully
- All existing functionality preserved

### Credits
- Implementation: Claude Code
- Task: Issue #3 (verifimind-genesis-mcp)

---

## v0.3.2 - Gemini 2.5 Model Update (January 29, 2026)

### Bug Fixes
- **Critical**: Fixed Gemini 1.5-flash model retirement
  - Changed default model from `gemini-1.5-flash` to `gemini-2.5-flash`
  - Updated `GeminiProvider` class default in `provider.py`
  - Updated `PROVIDER_CONFIGS` models list

### Technical Details
- **Root Cause**: Google retired `gemini-1.5-flash` model in 2026
- **Error**: `404 models/gemini-1.5-flash is not found`
- **Resolution**: Default to `gemini-2.5-flash` (stable, FREE tier)

### Deployment
- Deployed to GCP Cloud Run: `verifimind.ysenseai.org`
- All v0.3.1 protection features remain active

### Credits
- Implementation: Claude Code

---

## v0.3.1 - Smart Fallback + Rate Limiting + Per-Agent Providers (January 29, 2026)

### New Features

#### Rate Limiting (EDoS Protection)
Protects against Economic Denial of Sustainability attacks:

| Limit | Value | Purpose |
|-------|-------|---------|
| Per IP | 10 req/min | Prevent single-user abuse |
| Global | 100 req/min/instance | Prevent auto-scale cost attacks |
| Burst | 2x limit | Allow short bursts |

**Environment Variables:**
```bash
RATE_LIMIT_PER_IP=10      # requests per minute per IP
RATE_LIMIT_GLOBAL=100     # requests per minute per instance
RATE_LIMIT_BURST=2.0      # burst multiplier
RATE_LIMIT_WINDOW=60      # window in seconds
```

#### Smart Fallback Per-Agent Provider System
Intelligent provider selection optimized for each agent's specialty:

| Agent | Default (FREE) | Recommended (BYOK) | Specialty |
|-------|----------------|-------------------|-----------|
| **X Agent** | Gemini | Gemini | Innovation, creativity |
| **Z Agent** | Gemini | Anthropic Claude | Ethical reasoning |
| **CS Agent** | Gemini | Anthropic Claude | Code/security analysis |

**Strategy:**
- **Default**: All agents use Gemini (FREE tier) - no cost to maintainer
- **Smart Upgrade**: If `ANTHROPIC_API_KEY` is set, Z and CS agents automatically use Claude
- **Per-Agent Override**: `X_AGENT_PROVIDER`, `Z_AGENT_PROVIDER`, `CS_AGENT_PROVIDER` env vars

#### New Helper Functions
- `get_agent_provider(agent_id, ctx)` - Get optimized provider for specific agent
- `get_trinity_providers(ctx)` - Get all three agent providers at once
- `get_provider_status()` - Diagnostic function showing current configuration

### Bug Fixes
- **Critical**: Fixed deprecated Gemini model causing 404 errors
  - Changed default model from `gemini-2.0-flash-exp` to `gemini-1.5-flash`
  - Updated `GeminiProvider` class default in `provider.py`
  - Updated `PROVIDER_CONFIGS` models list

### Technical Details
- **Root Cause**: Google deprecated `gemini-2.0-flash-exp` model
- **Error**: `404 models/gemini-2.0-flash-exp is not found for API version v1beta`
- **Resolution**: Default to `gemini-1.5-flash` (stable, FREE tier)

### Environment Variables
```bash
# Default: All agents use Gemini FREE tier
GEMINI_API_KEY=your-key

# Optional: Z and CS automatically upgrade to Claude if set
ANTHROPIC_API_KEY=your-key

# Optional: Per-agent overrides
X_AGENT_PROVIDER=gemini
Z_AGENT_PROVIDER=anthropic
CS_AGENT_PROVIDER=anthropic
```

### Files Modified
- `mcp-server/src/verifimind_mcp/llm/provider.py` - Updated default Gemini model
- `mcp-server/src/verifimind_mcp/config_helper.py` - Added smart fallback functions
- `mcp-server/src/verifimind_mcp/server.py` - Updated all tools to use per-agent providers
- `mcp-server/src/verifimind_mcp/middleware/rate_limiter.py` - NEW: Rate limiting middleware
- `mcp-server/src/verifimind_mcp/middleware/__init__.py` - NEW: Middleware module
- `mcp-server/http_server.py` - Integrated rate limiting, updated version
- `.env.example` - Added rate limiting variables
- `CHANGELOG.md` - This update
- `SERVER_STATUS.md` - Updated status

### Benefits
- **Sustainable**: Public server uses FREE Gemini tier (no cost to maintainer)
- **Accessible**: Works out-of-box for everyone
- **Optimized**: Right model for each agent when BYOK configured
- **Flexible**: Full customization via environment variables

### Credits
- Implementation: Claude Code
- Architecture: Alton Lee Wei Bin (CTO Team YSenseAI)

---

## v0.3.0 - BYOK Multi-Provider Support (January 28, 2026)

### BYOK (Bring Your Own Key) Enhancement

This release implements full multi-provider BYOK support, enabling users to connect their own LLM API keys for multiple providers, making the system sustainable without increasing maintainer costs.

### New Features
- **Multi-Provider Support**: Added support for 7 LLM providers:
  - Gemini (FREE tier available)
  - Groq (FREE tier available)
  - OpenAI
  - Anthropic
  - Mistral (NEW)
  - Ollama (local, FREE) (NEW)
  - Mock (testing)

- **Automatic Fallback**: New `LLM_FALLBACK_PROVIDER` environment variable enables automatic fallback if primary provider fails

- **Provider Configuration**: New `PROVIDER_CONFIGS` dictionary with metadata about each provider including:
  - Default models
  - Available models
  - Free tier availability
  - Rate limits

- **Validation Utilities**: New helper functions:
  - `get_provider_with_fallback()` - Factory with automatic fallback
  - `validate_provider_config()` - Validate provider setup
  - `list_providers()` - List all available providers
  - `list_free_tier_providers()` - List free tier options

### Files Modified
- `mcp-server/src/verifimind_mcp/llm/provider.py` - Added Mistral and Ollama providers, fallback support
- `mcp-server/src/verifimind_mcp/llm/__init__.py` - Updated exports
- `mcp-server/src/verifimind_mcp/config_helper.py` - Multi-provider support
- `mcp-server/src/verifimind_mcp/server.py` - Added Groq/Mistral config fields
- `.env.example` - Updated with BYOK v0.3.0 configuration
- `MCP_SETUP_GUIDE.md` - Updated BYOK documentation
- `CHANGELOG.md` - This update

### Environment Variables
```bash
# Primary provider
LLM_PROVIDER=gemini

# Fallback provider
LLM_FALLBACK_PROVIDER=mock

# Optional overrides
LLM_MODEL=gemini-1.5-flash
LLM_TEMPERATURE=0.7
LLM_MAX_TOKENS=4096
```

### Breaking Changes
- None. Backward compatible with v0.2.x environment variables.

### Credits
- Implementation: Claude Code
- Specifications: Manus AI (T), CTO - Team YSenseAI

---

## v0.2.5 - Documentation & Encoding Fixes (January 2026)

### Documentation
- Improved BYOK documentation
- Fixed encoding issues in documentation files

---

## v1.0.2 - IP Update (November 19, 2025)

### Security
- Added **Genesis Prompt Engineering Methodology** to the defensive publication to establish prior art for the multi-model validation process.

---

## Phase 2 Track 1 - Complete (November 19, 2025)

### Code Enhancements
-  Code cleanup and organization
-  Comprehensive error handling with custom exception hierarchy
-  Testing infrastructure with 18 async tests
-  Structured logging framework
-  Professional CLI with argparse

### Documentation Cleanup
-  Consolidated vision, architecture, and roadmap documentation
-  Archived historical summary files
-  Added Concept Scrutinizer methodology specification
-  Created clear documentation hierarchy

### Project Organization
-  Moved demo scripts to `examples/`
-  Moved test files to `tests/`
-  Moved utility scripts to `scripts/`
-  Created `archive/` for historical files
-  Created `docs/methodology/` for foundational docs

### Canonical Documentation
- `docs/VISION.md` - Consolidated from 3 vision documents
- `docs/ARCHITECTURE.md` - Consolidated from 2 architecture documents
- `docs/ROADMAP.md` - Consolidated from 2 roadmap documents

---

## Phase 1 - Complete (November 15, 2025)

### Initial Setup
-  Initial codebase sync to GitHub
-  Project structure setup
-  Configuration files and setup documentation

### Core Implementation
-  LLM provider abstraction (OpenAI, Anthropic)
-  X-Z-CS agent framework
-  Iterative code generation engine
-  Agent orchestration system

---

## Phase 2 Track 2 - In Progress

### Genesis Methodology Formalization
- � Genesis Methodology white paper
- � RefleXion C1 case study documentation
- � API documentation

---

**Document Version**: 3.0
**Last Updated**: March 23, 2026
