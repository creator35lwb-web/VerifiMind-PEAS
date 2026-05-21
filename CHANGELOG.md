# Changelog

All notable changes to the VerifiMind PEAS project will be documented in this file.

Full version history also available at [verifimind.ysenseai.org/changelog](https://verifimind.ysenseai.org/changelog).

> **Disclosure policy (since v0.5.33):** The internal `CHANGELOG.md` retains full forensic details (specific blocked IPs, probe paths, request counts, UA strings) for attribution and audit trail. The public-facing `/changelog` rendered by the server intentionally omits specific IP addresses to avoid signalling to attackers and to keep customer-facing copy clean. PRs and commits remain the canonical source for forensic detail.

---

## v0.5.36 - Changelog Endpoint Redirect (May 21, 2026)

Single-sources the changelog to end dual-maintenance drift.

### What changed
- **`/changelog` endpoint now 302-redirects to GitHub Releases** (`github.com/creator35lwb-web/VerifiMind-PEAS/releases`). The hand-curated `pages.py _CHANGELOG_BODY` HTML page is retired. GitHub Releases are the single source of truth for the public changelog.
- The JSON variant (`Accept: application/json`) returns the Releases URL + a note.
- Removed the now-unused `get_changelog_page` import from `http_server.py`.
- Version bump 0.5.35 → 0.5.36 (both SERVER_VERSION surfaces + 9 test files); `server.json` 3.12.0 → 3.13.0.

### Why
On 2026-05-21 the `/changelog` endpoint drifted — `CHANGELOG.md` got the v0.5.35 entry but `pages.py _CHANGELOG_BODY` did not (third two-sources-of-truth drift this month). Rather than keep dual-maintaining, the endpoint now points to GitHub Releases — the single source.

**Disclosure-policy note:** redirecting to Releases (not to `CHANGELOG.md`) is deliberate. GitHub Releases are already sanitized (no forensic IPs), preserving the v0.5.33 disclosure policy. A redirect to `CHANGELOG.md` would have exposed the internal forensic IPs (v0.5.30 / v0.5.32 entries) on the customer-facing path.

### Process note
This deploy ran through the full `/verifimind-deploy` skill (v2.5) — including the Phase 2 9-test-file bump and Phase 7 full-SHA release — after v0.5.34/v0.5.35 bypassed the skill via direct `gcloud` and accumulated drift. Anti-bypass warning added to the skill.

---

## v0.5.35 - Honest-Baseline Metrics Sync (May 21, 2026)

Phase 90 "Adoption First" metrics publication sync — surfaces the post-forensic-rebuild honest baseline on the public Library timeline.

### What changed
- **`pages.py` Library timeline:** added a "May 2026" milestone surfacing the honest post-rebuild baseline — **4,139.1 flying hours** (Success-Gated, aggregate; owner-IP + bot/scraper traffic excluded). The dated April 17 milestone is preserved as history; the new milestone signals the audit-and-correct discipline ("we audit our own numbers the same way we ask others to audit theirs").
- **Version bump** 0.5.34 → 0.5.35 (both SERVER_VERSION surfaces); `server.json` 3.11.0 → 3.12.0.

### Data-Disclosure compliance (Doctrine v1.0)
- Published numbers are **aggregate only** (flying hours, methodology) — no per-user behavioral facts, no named individuals. The forensic-rebuild finding (owner-IP rotation overcounting) is described as methodology, not per-user data.
- The EA Cohort Taxonomy (34 active / 92 honest-baseline / 1 registered) and AY's paradox-page reflection update are routed through AY (domain owner) via change-request handoff — NOT edited by RNA, per the Cross-Agent Canonical-Edit Protocol.

### Why
The April 17 timeline showed pre-rebuild numbers (2,162 endpoints / 2,634 flying hours) as the last data point. AY's 2026-05-18 forensic DB rebuild established the honest baseline (4,139.1h aggregate, owner-IP leakage corrected). This sync surfaces the corrected number publicly, demonstrating the cross-architectural meta-principle: our internal metrics are held to the same audit rigor we apply to external AI claims.

### Not changed
- README + v0.5.34 docs verified already Data-Disclosure-clean (no per-user/cohort numbers) — no edits needed.
- AY's paradox-page reflection (`pages.py` L4336 + `docs/research/paradox/05-coo-ay-reflection.md`) is AY-canonical — change-request handoff sent, AY applies in her session.

---

## v0.5.34 - Evaluation Roadmap v1.0 (May 15, 2026)

Phase 90 strategic spine: Alton's Decision #1 + #2 from the May 13 Recursive Paradox session (`.macp/handoffs/20260513_T_L_recursive_paradox_analysis_and_decisions.md`) shipped as a single bundled release.

### What changed
- **New public page `/research/evaluation-roadmap`** rendered by `get_evaluation_roadmap_page()` in `mcp-server/src/verifimind_mcp/pages.py`. Companion to `/research/paradox`; cross-linked bidirectionally. Contents: pre-registered honest-scope disclaimer, pre-registered thresholds table (Cohen's κ, ECE, Brier, F1 lift, ESR), the 10-milestone roadmap (M0–M9 across May 2026 → April 2027), 8 pre-registered kill-conditions, commitment mechanism (git tags + retrospectives + named witnesses + pre-registered failure conditions), and link out to the canonical markdown for the Section B technical RFC appendix (math, dataset spec, reproducibility checklist, co-maintainer terms).
- **Canonical markdown** committed at `docs/research/evaluation-roadmap/roadmap-v1.0.md` (full 277-line source — Section A public + Section B technical RFC appendix with LaTeX-rendered math which GitHub renders inline).
- **Bi-directional cross-link** added to the Validation Paradox page (`/research/paradox`) immediately after the TOC: "Our response → The Evaluation Roadmap (v1.0)" callout pointing at `/research/evaluation-roadmap`. Paradox page tells the reader what the problem is; the new callout points at the structural answer.
- **Git tag** `roadmap-v1.0` applied to the commit landing this version of the page + canonical markdown. Future edits to milestone dates or definitions require a new tag with a public reason — `git log --tags` is the audit trail.
- **README** version badge bumped v0.5.29 → v0.5.34; new "Evaluation Roadmap" row added under the Research library section.
- **Wiring:** route `/research/evaluation-roadmap` registered in `http_server.py`; sitemap.xml + robots.txt entries added; `_RESEARCH_INDEX` JSON-LD bumped to v1.4 with `evaluation-roadmap` as the newest paper entry (companion of validation-paradox).

### Why
The Validation Paradox page named the problem in April: X / Z / CS are prompt-template agents with no labeled eval set, no calibration, no execution sandbox, no inter-judge agreement statistics. It ended on a single line — *the only available exit from a closed validation loop is an external signal.* The Evaluation Roadmap is that external signal: a public clock with pre-registered thresholds and pre-registered failure conditions. Publishing it (a) makes silent edits visible via git tags, (b) makes silent skips visible via milestone-keyed retrospectives, (c) makes false completions visible via named external witnesses, (d) makes rationalization visible via pre-registered failure conditions. Failure numbers ship in the same font size as success numbers.

Per Alton's May 13 rulings, this is the Phase 90 strategic spine — Beta v0.6.0 is now redefined as M0 + M1 from this roadmap (NOT first paying customer). The roadmap is the credibility milestone, not a commercial milestone.

### Expected impact
- Public surface gains `/research/evaluation-roadmap` (~45KB HTML), plus `docs/research/evaluation-roadmap/roadmap-v1.0.md` on GitHub for the full Section B RFC appendix.
- SEO: roadmap is canonicalized, added to sitemap and `/research/index.json`.
- No API surface change. No functional change to existing tools. Trinity validation behavior unchanged.
- Forecast (per Reasoning Evidence layer): if M0 is real, by ~Jun 1 we should see ≥ 1 external reference to this roadmap outside the VerifiMind/YSenseAI ecosystem. If not, M0 has not been hit — that becomes part of the retrospective, not silently elided.

---

## v0.5.33 - Changelog Hygiene (May 13, 2026)

Disclosure policy clarification + retroactive sanitization of the public-facing `/changelog` page.

### What changed
- Sanitized the v0.5.30 and v0.5.32 entries in `mcp-server/src/verifimind_mcp/pages.py` to remove specific blocked-IP addresses from the public surface. Wording now matches the v0.5.22 / v0.5.26 pattern (attack-type only, no specific identifier).
- Added a "Disclosure policy" header to this internal `CHANGELOG.md` documenting the split: full forensics live here and in PR history; public `/changelog` carries the security narrative without operational leakage.
- Added a v0.5.33 entry to public `/changelog` explaining the hygiene retroactively (transparency about the fix itself).
- Added PR# links to v0.5.30 and v0.5.32 public entries (matches v0.5.23 / v0.5.24 pattern).

### Why
Disclosing specific blocked IPs in a public changelog (a) signals to attackers what triggered the block, (b) tells the blocked actor they're caught and should rotate, (c) looks reactive in customer-facing copy. Internal records keep the full forensic record for attribution; the public surface keeps the trust signal ("we caught it, we blocked it") without operational leakage. This brings v0.5.30 and v0.5.32 in line with the existing v0.5.22 / v0.5.26 disclosure pattern.

### Expected impact
- Public `/changelog` at `verifimind.ysenseai.org/changelog` no longer surfaces `195.178.110.199` or `85.121.126.250`.
- Internal `CHANGELOG.md`, PR #213 / #215 bodies, and commit messages continue to carry the full forensic record (these are public on GitHub but require explicit drill-in vs being rendered into the live customer-facing page).
- No functional / API surface change. Version bump preserves the deploy-tracker convention.

---

## v0.5.32 - Secret Scanner Block + SonarCloud P1 (May 13, 2026)

Two combined hardening tracks: blocks a fresh credential-enumeration scanner identified in GCP forensics (May 12 burst), and lands the SonarCloud P1 cleanup queued from XV's May 12 audit.

### IP Blocklist Addition (7th)
- **`195.178.110.199`** — Credential/Secret Enumeration Scanner. 788 requests in a single burst on 2026-05-12 ~20:26 UTC; probed `.env` variants (`/BACK/.env`, `/Be/.env`, `/Api/.env`, `/.env.old`, `/.env.test`, `/.env.sample` etc.), full `.git/*` tree (`/.git/config`, `/.git/index`, `/.git/HEAD`, hooks, refs, logs, packs), `.terraform.*`, `.stripe/`, `.s3cfg`, `.wp-config.php.swp`, `?phpinfo=1`, `?pp=env&pp=env`, CI configs (`.gitlab-ci.yml`, `.github/workflows`), Next.js/SharePoint deception paths. Static Chrome/131 UA.
- **Defense breakdown:** 611/788 (77%) caught by rate limiter as 429; 153 caught as 302 HTTP→HTTPS redirects; 20 as 404; only 4 served 200 — all 4 were the safe public root/register response (zero sensitive leak; no PHP, no env vars, no `.git` data exists at the web root).

### SonarCloud P1 cleanup (production hygiene)
- **Module constants extracted in `http_server.py`** — `MCP_ENDPOINT_PATH`, `MCP_SERVER_URL`, `MCP_REMOTE_QUICKSTART`. Replaces ~13 duplicate string literals across JSON/dict surfaces (health response, /mcp-config, /, setup, error handlers, deprecated SSE 410 handler). URL changes now propagate from a single source. HTML page literals kept inline per XV P3-1 caveat (readability over deduplication).
- **Cognitive complexity refactor at `http_exception_handler`** — extracted `_extract_tool_call_metadata()` and `_client_ip_from_request()` helpers. Complexity 23 → ≤15. Function shape preserved; tested 404 logging path unchanged.
- **CodeQL `py/empty-except` × 2 resolved:**
  - `http_server.py:1072` — bare `except Exception: pass` replaced with specific `(ValueError, UnicodeDecodeError)` catch + comment explaining why probe traffic should not log.
  - `trinity_history.py:131` — `except RuntimeError: pass` now `logger.debug()` for visibility under verbose logging (no-running-loop case is by-design best-effort).
- **Logging hygiene:** `http_server.py` lightweight-registration 500 path uses `logger.exception()` for full traceback rather than `logger.error("%s", e)`.

### Expected impact
- SonarCloud Critical Code Smells: 13 → ~6
- CodeQL open: 15 → 13
- Cognitive complexity violations (production): 1 → 0
- SonarCloud Security: 3 → 3 (already clean from v0.5.31)
- Blocked IPs: 6 → 7

---

## v0.5.31 - SonarCloud P0 (May 13, 2026)

Resolves the P0 security hardening items from XV's May 12 SonarCloud audit (`.macp/handoffs/20260512_XV_sonarqube_security_audit_for_RNA.md`). Live SonarCloud state showed **14 Vulnerabilities + 15 BLOCKER severity items** — this release addresses every fixable item.

### Workflow hardening (1 Vulnerability)
- `.github/workflows/security-scan.yml` — moved `permissions: contents/security-events` from workflow level to the `bandit-sast` job level (principle of least privilege per GitHub Actions best practice)

### TLS hardening (2 Vulnerabilities)
- `templates/import_url.py:121, 148` — set `ctx.minimum_version = ssl.TLSVersion.TLSv1_2` explicitly on both SSL contexts; Python 3.10+ already defaults to TLS 1.2 but explicit is better

### Code correctness (6 BUGs)
- `templates/library/__init__.py` — removed broken `__all__` listing six YAML data files as Python symbols; replaced with an explanatory docstring (these are runtime-loaded YAML, not importable submodules)

### False-positive suppressions with justification
- `tests/unit/llm/test_providers.py:394,401,408,415,423,447,454` — added `# NOSONAR` comments to 7 lines flagged for `api_key` keyword. These are test fixtures with mock keys whose specific prefixes (`gsk_`, `sk-ant-`, `csk-`) the tests intentionally validate against; renaming would break the auto-detection tests.
- `http_server.py:1754` — added `# NOSONAR` to the `host="0.0.0.0"` line with justification comment; this binding is REQUIRED by Cloud Run for the container to accept proxy traffic
- `examples/demo_iterative_generation.py:150,157` — added `# NOSONAR` to API schema documentation dicts containing `"password": "string"` (these are field type indicators, not credentials)

### Deprecation fix (P1 bonus)
- `examples/demo_iterative_generation.py:61, 221` — replaced deprecated `datetime.utcnow()` with `datetime.now(timezone.utc)`; updated import accordingly

### Deferred (separate concern)
- `pyproject.toml` missing lockfile — our build uses hatchling without native lockfile support. Adding `uv.lock` or `poetry.lock` would change the package manager. Tracked as a P3 architecture decision, not a security fix.

### Expected SonarCloud impact
- Security impact: 14 → ~1 (only the lockfile question remains)
- BLOCKER severity: 15 → 0 (all 6 BUG findings on `__all__` fixed; all 7 test_providers and 1 http_server suppressed with justification)

---

## v0.5.30 - Config Scanner Block (May 12, 2026)

Security hardening: blocked a new config/secret enumeration scanner identified via GCP forensic analysis.

### IP Blocklist Addition
- **`85.121.126.250`** — Config/Secret Enumeration Scanner. ~25 req/sec on May 11; probed `/api/env`, `/firebase-config.json`, `/swagger.json`, `/openapi.json`, `/.well-known/jwks.json`, `/api/v1/config`, `/api/account`, `/__env.js`, `/__/firebase/init.json`, `/manifest.webmanifest`, and ~20 more secret/config paths. Rotating User-Agents (different browser/OS per request — botnet pattern). Mostly 429-rate-limited but adding to blocklist for defense-in-depth.

### Why blocklist, not Cloud Armor
Cloud Armor pricing (~$5/mo per policy + per-rule + per-request) is not cost-justified for a solo-builder MCP server. App-layer IP blocklist in `ip_blocklist.py` is free, deployed at the outermost middleware layer, and effective. 6 IPs blocked total.

---

## v0.5.29 - Growth-First Pages (May 12, 2026)

T (CTO) directive ([handoff](/) 2026-05-12): align GCP-served pages with the strategic pivot ratified May 11 in Session 13/14. All public pages now reflect "Growth First, Monetization Later" — no current paid services, no pricing on display, all 13 tools free for everyone.

### Page updates
- **`/terms` → v2.1** — pricing tier table removed (Pioneer/$9 row gone), Sections 4 (Payment) and 5 (Refund) rewritten as forward-looking "no active paid services" placeholders, Section 6 (Beta) reframed from "Pioneer coordination tools" to "full service", Section 8 (Acceptable Use) dropped Pioneer-specific resale clause
- **`/privacy` → v2.2** — Payment Processing section rewritten as forward-looking, Polar references removed (no current payment processor), data-collection table simplified, retention table dropped Pioneer/transaction rows, Data Sharing table dropped Polar row
- **`/register`** — benefit cards now show "All 13 tools / Free forever / Beta access / Direct feedback" (was "3 months free Pioneer tier / v0.6.0 Pioneer / Direct feedback")
- **`/changelog`** — this entry

### What's intentionally preserved
- Polar payment infrastructure code remains (PolarAdapter, polar_webhook.py) for future paid services
- Historical changelog entries (v0.5.7 "Pioneer launch", v0.5.10 "Terms v2.0", v0.5.13 "tier-gate middleware") — these are accurate history
- Paradox/research page Pioneer references (debating the pricing) — these are evidence of self-correction per External Council guidance

### Verification
- `grep` for `$9 | $197 | $497 | $1,997` returns zero current-claim hits in `/terms`, `/privacy`, `/register`
- Pioneer references remain only in historical changelog entries and the paradox/research reflection pages

---

## v0.5.28 - Tools Free (May 10, 2026)

Option B refactor PR1 of 3 — paywall removal. The three coordination tools (`coordination_handoff_create`, `coordination_handoff_read`, `coordination_team_status`) are now free for everyone, fulfilling the **Core Tools Always Free pledge** ratified May 9, 2026 by L (CEO) + Alton + T (CTO).

### Behavior changes
- `pioneer_key` parameter on all three coordination tools changed from required to optional (`Optional[str] = None`)
- Tool-blocking middleware removed: `check_tier()` is now used for tier identity (analytics) only, not as a gate
- Anonymous callers (no `pioneer_key`) are accepted; their handoffs go to a shared `"anonymous"` namespace
- Existing pioneer_key holders unchanged: their handoffs remain privately namespaced under their key

### What did NOT change
- Rate limiting (deferred to PR2 pending T's clarification on per-hour vs per-minute units — see Issue #59)
- Polar product structure (deferred to PR3)
- All other 10 tools (Trinity + template management) — already free, no change
- `tier_gate_error()` and `tier_gate.py` module retained for backward compat (now unused by tools)

### Tests
- 92/92 coordination + scholar incentives tests pass
- `tier_gate_error()` direct-call tests still pass (function preserved)

---

## v0.5.27 - Version Alignment (May 10, 2026)

Credibility fix flagged by the External Model Council: the `/mcp/` initialize response advertised the FastMCP library version (`3.2.4`) instead of our application version, creating a confusing mismatch with `/health` (`0.5.26`) and `/.well-known/mcp-config` (`0.5.26`).

### Fix
- **MCP `serverInfo.version`** — pass `SERVER_VERSION` explicitly to `FastMCP("verifimind-genesis", version=SERVER_VERSION)` so all surfaces report the same application version
- All four version-reporting surfaces (`/`, `/health`, `/.well-known/mcp-config`, `/mcp/` initialize) now consistently report `0.5.27`

### Why this matters
External Model Council (Claude Opus 4.7, GPT-5.5, Gemini 3.1 Pro) flagged version inconsistency as a trust friction signal. P0 credibility fix per L's ruling on landing page hold.

---

## v0.5.26 - Scanner Block + HTTP Compliance (May 6, 2026)

Security hardening: blocked new unauthorized AWS scanner, fixed HEAD method compliance on `/mcp/`.

### Security
- **IP Blocked:** `54.67.34.241` (AWS EC2 us-west-1) — unauthorized MCP prober, no User-Agent, ~35-min interval HEAD/POST scan, 96 hits over 2 days; added to IP blocklist with `UNAUTHORIZED_SCANNER` reason code

### HTTP Compliance Fix
- **HEAD `/mcp/`** — added explicit HEAD handler returning 200 with `Content-Type` and `X-Server-Version` headers; previously returned 405 (Method Not Allowed) because the MCP Mount does not register HEAD

---

## v0.5.25 - Health Transparency (May 1, 2026)

Operational monitoring improvement: `/health` endpoint now reports `inference_mode` — surfaces live vs mock vs degraded inference state in real time.

### New: `inference_mode` in `/health`
- `"live"` — primary provider configured and API key present; real LLM inference active
- `"degraded"` — primary key missing but a free-tier fallback (Groq/Cerebras) is active
- `"mock"` — no real inference available (all keys missing or `LLM_PROVIDER=mock`)
- Directly resolves the 9-day mock-mode blindspot: `/health` now detects env var wipe immediately

---

## v0.5.24 - Cowork Research Publication (April 30, 2026)

XV's strategic analysis of Anthropic Cowork on 3P, reviewed and approved by L (CEO/Godel), published as a live research document.

### New Research Publication: `/research/cowork`
- Full 10-section strategic analysis: competitive assessment, China market thesis, the Woozle Effect argument, 4-tier product line, 14 academic and primary sources
- **Section 5 (Self-Correction as Substance)** — real-time case study of the Validation Paradox exit node: XV's v1.0 error (claimed Cowork was Claude-only) caught by the human Orchestrator, corrected within 24 hours, version-controlled and republished
- Version history table prominent in the document — v1.0 error preserved, v1.1 correction current
- CORRECTED callout badge, self-correction highlight box, competitive capability tables
- SEO meta + Open Graph tags for social sharing

### Research Hub Navigation
- Featured Cowork Analysis card on `/research` index (accent border, NEW badge, CTA button)
- 4-pill nav strip across all research pages: Published Research · The Validation Paradox · Cowork Analysis · Evidence Library
- `/research/index.json` updated to v1.3 with cowork entry
- Robots.txt + sitemap updated for `/research/cowork`

### Pull Requests
- PR #193 (Cowork research publication)

---

## v0.5.23 - BYOK Provider Hardening + Research Navigation (April 30, 2026)

Provider audit and bug fixes from live BYOK testing, plus full interconnection of the Research/Library/Paradox public pages.

### BYOK Provider Fixes (v0.4.5)
- **Cerebras key prefix**: `csk_` → `csk-` (hyphen) — auto-detection now matches real Cerebras keys
- **Cerebras model**: `llama3.1-70b` → `llama-3.3-70b` (deprecated model removed)
- **Anthropic JSON parsing**: `strip_markdown_code_fences()` now applied before JSON parse — Claude's ` ```json...``` ` fences no longer cause CSAgentAnalysis Pydantic validation failure (8-field error)
- **Provider audit**: All 7 providers (Gemini, Groq, Cerebras, Anthropic, OpenAI, Mistral, Ollama) now consistently apply `strip_markdown_code_fences()` and return `_inference_quality: "real"`
- **Mistral package**: Added `mistralai>=1.0.0` to `requirements.txt` + `pyproject.toml` (was absent)
- **Mistral import**: Updated to `from mistralai.client import Mistral` (mistralai v2.x SDK breaking change)

### Mock Mode Transparency
- `MockProvider.generate()` now returns standard `{"content": ..., "_inference_quality": "mock"}` wrapper — `_inference_quality` field in tool responses correctly shows `"mock"` (was `"unknown"`)
- `_warning` field injected in all tool responses when inference quality is mock
- `"synthetic"` added as `overall_quality` state in `run_full_trinity` (all-mock run)
- Warning framing: honest and encouraging — framework + schema fully intact, content synthetic, suitable for onboarding/demos/integration testing

### Research Section Navigation
- `site-nav`, `nav-active`, `nav-cta`, `nav-pill`, `nav-pill-active` CSS classes added to base stylesheet
- `/research` page: full site-nav header (Research active), section pill strip, complete footer with cross-page links
- `/library` page: consistent `site-nav` header (Library active), Paradox link, section pill strip
- `/research/paradox` page: section pill strip (Paradox active), footer with Library + Changelog links
- All three pages now fully interlinked — no manual URL entry required

### Testing
- All version assertions updated to v0.5.23 across 7 test files
- 631 tests pass, 0 CodeQL medium+ alerts

### Pull Requests
- PR #189 (BYOK provider hardening + mock transparency)
- PR #190 (Research/Library/Paradox navigation interconnect)

---

## v0.5.22 - IP Blocklist Security Layer (April 30, 2026)

T Security Directive (2026-04-27): 3 rogue IPs blocked at application level following AY forensic scan (AY Report 078). IPBlocklistMiddleware runs as the outermost Starlette middleware layer.

### IP Blocklist Middleware
- `IPBlocklistMiddleware` added to `mcp-server/src/verifimind_mcp/middleware/ip_blocklist.py`
- Blocks 3 rogue IPs: AWS IPv6 fuzzing bot (63% error rate), content scraper (2,007 AbuseIPDB reports), unauthorized YellowMCP scanner (unconsented indexing)
- Full X-Forwarded-For chain checked — GFE proxy-aware (all hops inspected, not just first)
- User-Agent blocklist: `YellowMCP-SecurityScanner` substring match (case-insensitive)
- 403 response with minimal disclosure (`{"error":"Forbidden","code":403}`) — no implementation details leaked
- Legitimate traffic unaffected: standard `python-httpx`, `node`, `mcp-remote` UAs pass through

### Audit Logging
- `[IP_BLOCKED] ip= reason= path= ua= ts=` — AY can filter GCP logs by reason code (ERRATIC_BOT / CONTENT_SCRAPER / UNAUTHORIZED_SCANNER)
- `[UA_BLOCKED] pattern= ip= path= ua= ts=` — tracks scanner tool blocks separately from IP blocks

### Architecture
- Outermost middleware (Starlette `add_middleware` LIFO — added last, runs first)
- Zero cost: application-level blocking requires no Cloud Armor / Load Balancer (per T's architecture ruling)
- `BLOCKED_IPS` and `BLOCKED_UA_PATTERNS` constants are operator-maintainable without code changes

### Testing
- 32 new tests across 5 test classes: constants, `_check_ip`, `_check_ua`, middleware dispatch, audit logging
- All X-Forwarded-For chain scenarios covered including multi-hop GFE proxy
- 574 unit tests pass, 0 CodeQL medium+ alerts

### Pull Requests
- PR #182 (IP blocklist middleware)

---

## v0.5.21 - P0 Tool Manifest Audit + Structured 404 Logging (April 30, 2026)

Hotfix addressing AY Report 078: 81 high-intent endpoints lost to Tool Not Found errors. Completes T's P0 directives from the FLYWHEEL TEAM alignment handoff (April 28, 2026).

### Tool Manifest Audit
- `/.well-known/mcp-config`: 3 coordination tools missing since v0.5.16 — now lists all 13 correctly
- `/.well-known/mcp/server-card.json` (Smithery): same fix with full `inputSchema` for each coordination tool
- FastMCP `tools/list` (MCP protocol layer): already correct — zero phantom tools confirmed by audit

### Structured 404 Logging
- `http_exception_handler` now emits `[TOOL_NOT_FOUND] tool= uuid= ip= ts=` when a POST `tools/call` body hits a 404 path — AY can correlate churn to specific tool names and UUID cohorts in future GCP reports
- `[HTTP_404] ip= ts= path=` log for regular path misses (non-MCP requests)
- Fixed latent `NameError`: `logger` was referenced in `register_handler` without module-level definition

### Graceful Error Verification
- FastMCP already returns proper JSON-RPC `-32601` for unknown tool calls natively (`NotFoundError → McpError`) — no code change required, verified by source inspection

### Testing
- 596 tests pass (+17 new P0 audit tests), 60.68% coverage, 0 CodeQL medium+ alerts

### Pull Requests
- PR #179 (P0 tool manifest + 404 logging)
- PR #180 (version bump v0.5.20 → v0.5.21)

### Credits
- Forensic analysis: AY (Antigravity/Gemini, COO) — Report 078, Week 18 drop-off crisis
- Directives: T (Manus AI, CTO) — FLYWHEEL TEAM handoff April 28, 2026
- Implementation: RNA (Claude Code, CSO)

---

## v0.5.20 - Root Page UX + BYOK v0.4.0 + BYOK Guide P0 Fix (April 27, 2026)

New providers, refreshed model IDs, copy buttons on the root onboarding page, and a critical fix for a deprecated Gemini model in the BYOK guide.

### Root Page UX
- Copy buttons on all 4 connection config code blocks (Anonymous + Scholar, Claude Code + Claude Desktop)
- Scholar UUID tier card with ready-to-paste `--header X-VerifiMind-UUID:${VERIFIMIND_UUID}` config
- URL tip callout directing users to `/mcp/` with trailing slash
- Tools count corrected to 13 throughout (was 10 in multiple locations)

### BYOK v0.4.0 — Provider Sync
- New **Cerebras** provider: `llama3.1-70b`, 1M tokens/day FREE, `csk_` key prefix
- Anthropic default: `claude-3-5-haiku-20241022` → `claude-sonnet-4-6`; `claude-opus-4-7` added
- OpenAI default: `gpt-4o-mini` → `gpt-4.1-mini`; `gpt-4.1-nano` added
- Groq: removed deprecated `mixtral-8x7b-32768`, added `llama-4-scout`
- Smart fallback chain: BYOK → Groq → Cerebras → mock

### BYOK Guide P0 Fix (XV CIO handoff — April 23, 2026)
- `gemini-2.0-flash` (deprecated March 31) → `gemini-2.5-flash` — zero stale instances remain
- Claude.ai warning: Opus 4.7 blocks API keys in chat text; BYOK only works via MCP tool argument
- Model Freshness table: deprecation timelines for all 6 providers

### Testing
- 487 tests pass, 0 CodeQL medium+ alerts

### Pull Requests
- PR #168 (Root UX + BYOK v0.4.0 + BYOK Guide + research reflections)
- PR #169 (version bump v0.5.19 → v0.5.20)

### Credits
- Implementation: RNA (Claude Code, CSO)
- Intelligence: XV (Perplexity, CIO) — BYOK model deprecation P0 handoff
- Human Orchestrator: Alton

---

## v0.5.19 - UUID Tier-Aware Rate Limiter + 404 Churn Fixes + Validation Paradox (April 21, 2026)

Scholar/Pioneer users now get dedicated UUID-based rate limit buckets (30 req/60s and 100 req/60s respectively), replacing the shared IP-only limit. The `/mcp` missing-slash 404 (531+ daily errors from AY COO log analysis) is fixed with a 308 redirect. The Validation Paradox research endpoint launches with all 6 FLYWHEEL TEAM independent reflections published.

### Research: The Validation Paradox
- New endpoint `GET /research/paradox` — full SEO-optimised research publication (JSON-LD ScholarlyArticle, OG, Twitter, canonical)
- All 6 independent FLYWHEEL TEAM reflections published: Alton (Open Thesis), XV (CIO), T (CTO), L (CEO), RNA (CSO), AY (COO), AZ (CPO)
- Research source documents at `docs/research/paradox/` — CC BY 4.0
- Sitemap and robots.txt updated; `/research/index.json` v1.2 updated
- AZ (CPO) is a new FLYWHEEL TEAM agent introduced in this publication
- Key finding disclosed publicly: 38.8% of accomplished churn is 404 errors; honest user estimate 800–1,200 (not 2,433 IPs)

### P0-A: UUID Tier-Aware Rate Limiting
- `X-VerifiMind-UUID` header (auto-sent since v0.5.17) now sets rate limit tier server-side
- Anonymous: 10 req/60s per IP (unchanged) — Scholar: 30 req/60s per UUID — Pioneer: 100 req/60s per UUID
- Tier resolved via Firestore `ea_registrations` lookup, cached 5 minutes; fail-open to Scholar if Firestore unavailable
- `X-RateLimit-Tier` header on every response; 429 response includes upgrade hint for anonymous users
- `TIER_LIMITS`, `_resolve_uuid_tier()`, `_uuid_tier_cache` all exported for testing

### 404 Churn Fixes (AY COO PIN)
- `GET /mcp` (no trailing slash) → **308 Permanent Redirect** to `/mcp/` (method-preserving — POST clients routed correctly)
- `GET /mcp/sse` and `GET /sse` → **410 Gone** with actionable JSON (`use_instead` URL, `transport` hint)
- Eliminates ~531–556 daily 404s identified in GCP log analysis

### Testing
- 574 tests pass (14 skipped), 61.99% coverage, CodeQL clean

### Pull Requests
- PR #163 (P0-A UUID rate limiter), PR #164 (404 churn fixes)

### Credits
- Implementation: RNA (Claude Code, CSO)
- Specification: T (Manus AI, CTO) — Phase 84 D3
- Log Analysis: AY (Antigravity, COO) — 404 Churn PIN
- Human Orchestrator: Alton

---

## v0.5.18 - Scholar Dashboard: Trinity History (April 21, 2026)

Registered Scholar users can now view their personal Trinity validation history at `GET /early-adopters/dashboard/{uuid}`.

### Scholar Dashboard (P0-B)
- `GET /early-adopters/dashboard/{uuid}` — HTML page showing last 50 Trinity validations for the authenticated UUID
- Reads `trinity_history/{uuid}/validations/` from Firestore (sync client, descending by timestamp)
- Displays: score, tool, recommendation excerpt, veto flag (⚑), timestamp per row
- Empty state, "temporarily unavailable" fallback, privacy notice on every render
- `read_trinity_history(uuid, limit=50)` utility added to `trinity_history.py` (sync Firestore read)

### Testing
- 472 tests pass, 3 skipped, 59.74% coverage

### Pull Requests
- PR #162 (Scholar Dashboard)

### Credits
- Implementation: RNA (Claude Code, CSO)
- Specification: T (Manus AI, CTO) — Phase 84 D2
- Human Orchestrator: Alton

---

## v0.5.17 - mcp_config UUID Header Fix (April 21, 2026)

UUID now automatically flows on every MCP request for registered Scholar and Pioneer users — no manual `user_uuid` parameter needed on each tool call.

### UUID Header Auto-Flow (T Phase 84 D1)
- `mcp_config` args in registration response now include `--header X-VerifiMind-UUID:${VERIFIMIND_UUID}`
- `mcp-remote` expands `${VERIFIMIND_UUID}` from the process environment and sends it as a request header on every call
- `env: {VERIFIMIND_UUID: uuid}` still present (backward compat) — header fix is additive
- Server-side middleware reads `X-VerifiMind-UUID` for UUID tier-aware rate limiting (v0.5.19)
- MCP Registry updated to v2.5.0 ([registry.modelcontextprotocol.io](https://registry.modelcontextprotocol.io/?q=verifimind))

### Testing
- 8 new tests (mcp_config header structure, env var presence, env var expansion pattern)

### Pull Requests
- PR #160 (mcp_config header fix), PR #161 (MCP Registry v2.5.0)

### Credits
- Implementation: RNA (Claude Code, CSO)
- Specification: T (Manus AI, CTO) — Phase 84 hybrid D1
- Human Orchestrator: Alton

---

## v0.5.16 - Trinity History Persistence + Terms Hotfix (April 21, 2026)

Trinity validation results are now persisted to Firestore for the Scholar Dashboard (P1-B), and the `/terms` page was updated to match the current 3-tier service model.

### Trinity History Persistence (P1-B)
- `write_trinity_history(uuid, tool, result)` — fire-and-forget async Firestore write to `trinity_history/{uuid}/validations/`
- Stores: tool name, overall score, recommendation excerpt, veto flag, timestamp, `_inference_quality`
- Wired into all 4 core MCP tools (`consult_agent_x/z/cs`, `run_full_trinity`) when `user_uuid` provided
- Zero latency impact (async task, no await in hot path)

### Terms Hotfix
- `/terms` page updated: Anonymous tier row added to service tiers table, Identity + Rate Limit columns explicit, Privacy Policy link updated to v2.1, "Updated: April 21, 2026"

### Pull Requests
- PR #158 (terms hotfix), PR #159 (Trinity history persistence)

### Credits
- Implementation: RNA (Claude Code, CSO)
- Human Orchestrator: Alton

---

## v0.5.15 - Scholar Incentives: UUID Tracer + Registration UX (April 20, 2026)

Optional UUID tracer on all 10 Scholar tools, Privacy Policy v2.1 disclosure, enhanced registration response.

### Scholar UUID Tracer (P1-A)
- Optional `user_uuid` parameter added to all 10 Scholar tools (`consult_agent_x/z/cs`, `run_full_trinity`, and all 6 template tools)
- `emit_tracer(uuid, tool)` — fire-and-forget `TRACER_UUID:` stdout log feeds AY GCP analytics pipeline
- UUID format validated via RFC 4122 regex; malicious strings (log injection, non-UUID values) silently ignored
- Anonymous tool calls unchanged — `user_uuid=None` works identically
- Pioneer tools (`coordination_handoff_*`, `coordination_team_status`) unaffected — still use `pioneer_key`

### Registration Response UX (P1-C)
- `register_user()` now returns `mcp_config` (ready-to-paste Claude Desktop JSON with server URL + UUID env var), `test_url`, `dashboard_url`, `checkout_url`
- One API call gives a new Scholar everything needed: copy the config, test the connection, see the dashboard, upgrade to Pioneer
- Both new-user and duplicate-email return paths include full extras

### Privacy Policy v2.1
- UUID USAGE ANALYTICS section added — full Z-Protocol v1.1 compliant disclosure of what is logged (UUID, tool name, tier label, timestamp), what is NOT logged (concept content, IP linked to UUID, PII), 30-day GCP Cloud Logging auto-purge
- Terms v2.0 updated — Anonymous tier row added to service tiers table; Identity and Rate Limit columns made explicit

### Testing
- 515 tests, CodeQL clean (0 medium+ alerts)
- 30 new tests: UUID format validation (9), user_uuid parameter existence on all 10 Scholar tools (11), P1-C registration response fields (10)

### Pull Requests
- PR #154 (Scholar Incentives — P1-A + P1-C)

### Credits
- Implementation: RNA (Claude Code, CSO)
- Specification: T (Manus AI, CTO) — Phase 83 PIN `3-tier-implementation`
- Architecture Review: AY (Antigravity, COO) — UUID bridge analytics pipeline
- Human Orchestrator: Alton

---

## v0.5.14 - Fortify: Research Library + Connection Test (April 17, 2026)

Genesis Research Library v1.0, UUID connection test endpoint, MPAC competitive analysis.

### New Endpoints
- `GET /mcp/test?key=<uuid>` — UUID connection test: verify your key is valid and see your tier before configuring your MCP client
- `GET /library` — Genesis Research Library v1.0: 20+ academic papers validating the VerifiMind methodology (Sections A–E, evidence chain timeline, JSON-LD SEO)
- `GET /library/index.json` — machine-readable library index for AI crawlers

### Research
- **/research Article 3** — MPAC vs MACP competitive analysis (XV + T, April 17, 2026); AI Council CONDITIONAL verdict disclosed
- **`/research/index.json` v1.1** — 4 papers (was 3), mpac-alignment entry added

### SEO & Crawlers
- `sitemap.xml + robots.txt` — `/library` and `/library/index.json` added for crawler access

### Testing
- 485 tests

### Pull Requests
- PR #151

### Credits
- Implementation: RNA (Claude Code, CSO)
- Research: XV (Perplexity, CIO) + T (Manus AI, CTO)
- Human Orchestrator: Alton

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
