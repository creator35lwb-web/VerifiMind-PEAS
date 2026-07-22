# Changelog

All notable changes to the VerifiMind PEAS project will be documented in this file.

Full version history also available at [verifimind.ysenseai.org/changelog](https://verifimind.ysenseai.org/changelog).

> **Disclosure policy (since v0.5.33):** The internal `CHANGELOG.md` retains full forensic details (specific blocked IPs, probe paths, request counts, UA strings) for attribution and audit trail. The public-facing `/changelog` rendered by the server intentionally omits specific IP addresses to avoid signalling to attackers and to keep customer-facing copy clean. PRs and commits remain the canonical source for forensic detail.

---

## v0.5.53 - Mistral Currency + Ollama Contract (July 23, 2026)

Two lanes from Alton's model-diversity direction (S78): the **EU-sovereignty BYOK lane** (Mistral) and a health check on the **keyless local open-source path** (Ollama).

### What changed
- **Mistral BYOK default `mistral-medium-3` → `mistral-medium-3.5`** (live-verified on a real key 2026-07-22: chat probe OK; 25k TPM / 50 RPM observed — more headroom than Groq's 8k). `mistral-medium-3` retained for continuity. Jurisdictional diversity (US frontier + EU sovereign + open weights) is a genuine Layer-2 model-diversity axis. Thanks to the v0.5.51 truth contract, the menu change propagates to /health, /setup, and the server card with zero copy edits.
- **Ollama SDK boundary tested for the first time** (the provider shipped in v0.4.x with zero boundary tests — the same gap class Gemini had before resilience batch 2). 10 mocked-httpx contract tests: keyless construction, request shape (`num_predict`, `stream:false`, schema-guidance injection), token-field mapping, fence-strip/prose-extraction, error propagation.
- **FINDING F-RES-3 (pinned, routed):** Ollama's parse-failure path returns `_inference_quality: "real"` while shipping `{"raw_response", "parse_error"}` content — unlike Gemini/Groq, which mark the same situation `"fallback"`. Downstream quality gates would not fire on an Ollama parse failure. Candidate fix routed to the parse-ladder lane (with F-RES-2); behavior pinned so any change is conscious.
- Version surfaces: both constants, 12 version tests, `server.json` (registry `3.30.0`).

### Verification
- 760 unit + 79 registration tests green (12 new), coverage 73.99%
- Mistral: PRE-verified via direct live API probes (models list + chat completions on `mistral-medium-3.5` and `mistral-medium-3`); hosted free-tier routing UNCHANGED (X/Z/CS untouched)

**PR:** #302.

---

## v0.5.52 - Discovery Truth Repair (July 22, 2026)

T's Session 87 verification (WP-A, P0) found the v0.5.51 truth contract only **partially projected**: `/setup` still claimed "Gemini 1.5 Flash" powered the X seat, described hosted Z/CS as "Claude (if BYOK) or Gemini", carried a `X (Gemini) -> Z (Claude/Gemini)` flow, stamped the free coordination tools "Pioneer tier", and miscounted the tool composition; the startup banner told the v0.3-era routing story; and `/mcp/test` actively told users to "Upgrade to Pioneer for coordination tools" — a false paywall claim (everything is free since v0.5.28).

### What changed
- **`/setup` trinity descriptions, flow, and banner now project from `get_public_contract()`** — same anti-drift mechanism as v0.5.51, extended to the surfaces it missed.
- **`/mcp/test` message corrected**: "All 13 tools (Trinity + templates + coordination) are free for everyone."
- **All "Pioneer tier" stamps removed** from tool descriptions (MCP config + server card + setup); tool composition corrected to "4 Trinity + 6 template + 3 coordination".
- **NEW `test_v0552_discovery_truth.py`**: renders the ACTUAL handlers and scans source + payloads for the named stale-claim shapes — T's audit findings become permanent CI. The source-scan caught 6 further "Pioneer tier" stamps my manual sweep missed, pre-merge.
- Version surfaces: both constants, 11 version tests, `server.json` (registry `3.29.0`).

### Verification
- 748 unit + 79 registration tests green, coverage 73.43%
- WP-A exit: cross-surface agreement tests prove `/health`, `/setup`, MCP config, and root serve one truth; live GET evidence recorded post-deploy

**PR:** #301.

---

## v0.5.51 - Public Truth Contract + Gemini Currency (July 22, 2026)

Implements the P0 from T's Session 85 **Live Publication Truth Audit** (D-85-2): every endpoint returned 200 while the discovery surfaces (`/setup`, MCP config, `/health`, landing data) *disagreed with each other* about models, routing, and versions — one surface still claimed "Gemini 2.0 Flash," another denied that per-agent routing exists. "Availability is not currency."

### What changed
- **NEW `verifimind_mcp/contract.py` — the canonical truth object.** `get_public_contract()` generates version + per-agent free-tier routing + BYOK provider menus from the live runtime constants. Surfaces now PROJECT from it instead of hand-maintaining copy: `/health` gains `free_tier_routing`, the root feature list and server-card copy are generated, and the false "per-agent selection is not supported" claim is corrected. A new anti-drift test suite asserts surface↔contract agreement, so the next migration that misses a surface fails CI instead of shipping a contradiction.
- **Gemini currency (Alton + live-verified 2026-07-22):** free-tier X default `gemini-2.5-flash` → **`gemini-3.5-flash-lite`** (GA; Google's documented migration target; "structured JSON parsing" strength = the X-seat workload; direct responder — no thinking-token burn). BYOK menu adds **`gemini-3.6-flash`** (GA frontier) and retains `gemini-3.5-flash` (thinking model — budget output accordingly), `gemini-2.5-flash`, `gemini-3.1-pro-preview`. All IDs live-verified via ListModels + generateContent on the free-tier key.
- **Coordination template MACP v2.5 (#77, T-approved):** handoff records now stamp `MACP v2.5 "Loop Engineering"` (was v2.2 "Identity" — the acknowledged Gate #6 lag, now retired).
- Version surfaces: both `SERVER_VERSION` constants, 10 version tests, `server.json` (registry `3.28.0`).

### Verification
- 742 unit + 79 registration tests green (14 new contract tests), coverage 73.43%
- **PRE-deploy live smoke through the production XAgent path** on `gemini-3.5-flash-lite`: schema-valid, 7 genuine reasoning steps, no synthetic fills. (An ad-hoc prompt without the Genesis structure DID produce mis-keyed steps — evidence the prompt architecture, not luck, carries the contract.)

**PR:** #300.

---

## v0.5.50 - Honest Registration Degradation (July 20, 2026)

Resolution of **F-RES-1**, the headline finding of the Foundation Inspection resilience pass (Hub #81): with Firestore unavailable, `POST /early-adopters/register` returned a full success response — "Your UUID is your access key — save it" — for a UUID that was **never persisted** and would never resolve at `/whoami`, the status endpoint, or the dashboard. The degradation was disclosed only to the server log, never to the user. Decision by Alton (option a: disclose, keep availability); the behavior change consciously updates the pinned F-RES-1 contract test.

### What changed
- **`RegistrationResponse.persisted`** (new field, default `True`): the Firestore-unavailable branch now returns `persisted: false`, an explicit *"your registration was NOT saved — no data was stored, please try again"* message, and no benefit promises. The endpoint stays available (no 5xx) — honest degradation, not hard failure.
- **`/register` page**: the form JS branches on `persisted === false` and shows the retry error state instead of the success screen — a 200 with an unsaved record can no longer masquerade as a completed registration.
- **`/health` gains `firestore`** (`connected` | `unconfigured` | `error`): persistence degradation is now *observable*. The structural lesson — prior health checks never covered the storage dependency, so a silent-orphan window could not be seen from outside.
- Version surfaces: both `SERVER_VERSION` constants, 9 version-assertion tests, `server.json` (registry `3.27.0`).

### Forensics (verify-before-invite discipline)
Before acting on the finding, the funnel was live-probed end-to-end (register → persist → resolve → cleanup: healthy today) and GCP logs swept for the degradation signature — zero occurrences within the 30-day log-retention window; earlier eras are unqueryable by retention, which is exactly why `/health` now carries the signal permanently. A public re-registration invitation for anyone whose UUID does not resolve follows separately.

713 unit tests pass (3 skipped), coverage 71.98%. **PR:** #295.

---

## v0.5.49 - Groq Migration + CIDR Layer (July 16, 2026)

Deadline-driven model migration (Groq decommissions `llama-3.3-70b-versatile` on **August 16, 2026**) bundled with the first CIDR-range blocklist layer and MCP protocol-version reporting. The free-tier stack becomes the "frontier + open-source" hybrid T+L designed (D-65-6/7/8): Gemini 2.5 Flash (frontier) + GPT-OSS 120B (open-source) as the two free pillars. 637 unit tests pass (3 skipped); every new model ID live-verified against the Groq API before listing.

### What changed
- **Groq default → `openai/gpt-oss-120b`** (D-65-6). Live verification caught that the migration plan's bare `gpt-oss-120b` **returns 404** — Groq namespaces the ID. Aspirational-name class error prevented for the third release running (v0.5.47 caught `gemini-3.1-pro`; the verify-before-listing rule pays again).
- **Groq fast option → `qwen/qwen3.6-27b`** (D-65-7) replacing deprecated `llama-3.1-8b-instant`; `meta-llama/llama-4-scout-17b-16e-instruct` retained. First Qwen model in production BYOK ("models as features").
- **Reasoning-model output handling:** `<think>…</think>` blocks now stripped in the shared JSON-extraction path (`strip_markdown_code_fences`) — Qwen3.x prefixes answers with thinking tags that would otherwise break structured parsing for every provider path.
- **`/health` now reports `protocol_version`** (MCP SDK `LATEST_PROTOCOL_VERSION`; AY/AZ ask from the MCP 2026-07-28 RC assessment) so clients can check compatibility pre-connect.
- **Scanner #27 + CIDR layer (PR #281, merged 2026-07-16):** `45.148.10.194` (CONFIG_SECRET_SCANNER — 959 GET/72h, 949×404, zero leak) is the **4th** confirmed-malicious IP from `45.148.10.0/24`, meeting the pre-agreed threshold (v0.5.48 watch-item). NEW `BLOCKED_CIDRS` layer blocks the whole /24 (`CONFIG_SECRET_SCANNER_NET`) — exact-match wins first, CIDR fallback catches unlisted successors; malformed-XFF-safe; IP-version-matched. Sentinel 30-day sweep: 7 IPs from this /24, zero benign traffic ever. T (CTO) formally approved both decisions separately.
- **BYOK_GUIDE table refresh:** correction-propagation sweep aligned all provider rows to `PROVIDER_CONFIGS` (OpenAI `gpt-5.5`, Mistral `mistral-medium-3`, Cerebras `llama-3.3-70b` — v0.5.47 currency had missed the guide).
- **TPM-admission clamp (post-deploy smoke catch, fix-forward same hour):** Groq's on_demand admission rejects any request whose input + `max_tokens` reservation exceeds the model's TPM limit — and both new models sit at **8,000 TPM** (llama-3.3 was 12,000, which silently absorbed the v0.5.46 `8192` reservation; limits live-read from `x-ratelimit-limit-tokens`). The first post-deploy Trinity smoke 413'd (`Requested 8106 > 8000`). Completion reservation now clamped to `4096` for the two 8k-TPM models — observed Z/CS outputs run ~1k tokens, so ~4× headroom, zero quality impact. Post-fix smoke: real/real/real.
- **Deps:** uvicorn 0.51.0 (#277), fastmcp 3.4.4 (#278); `mcp` stays pinned 1.28.1.

### Watch-items
- Cerebras `llama-3.3-70b` default: unverifiable without a key (no CEREBRAS_API_KEY held); Groq's llama-3.3 sunset may foreshadow Cerebras — monitor.
- Groq deprecated IDs remain live upstream until Aug 16; users pinning them explicitly get provider-side errors after that date.

### Why
Migrating 31 days before the decommission cliff, not after it. The hybrid free-tier stack structurally embodies the model-heterogeneity thesis (the infrastructure IS the methodology), at zero burn-rate. The CIDR layer ends per-IP whack-a-mole against a subnet with zero benign history — forecast (70%): the next `45.148.10.x` scanner is silently 403'd with no deploy.

**PRs:** #277, #278, #281, this release PR.

---

## v0.5.48 - Scanner Cluster Block (June 28, 2026)

Security-hygiene batch: three config/secret/RCE scanners blocked at the application layer (`BLOCKED_IPS` 23 → 26), one rotation-proof UA block added, two crawler UAs flagged for monitoring. Zero sensitive-path 200s confirmed across all three IPs. AY+AZ flagged the cluster in Report 099 / `.macp/handoffs/20260628_AY_AZ_to_RNA_probe_blocklist_tlm_config_scanners.md`; Sentinel independently re-verified against live GCP logs (30-day window) before recommending action. No functional change; 613 unit tests pass (3 skipped), full suite gated in CI.

### What changed
- **Probe #24 — `45.148.10.62` (CONFIG_SECRET_SCANNER):** weekly cron scanner (four rounds Jun 5/10/17/27 ~16:00 UTC, ~30 req/session, rotating browser UAs). Probed `.git/config`, `.env` tree (18+ variants), `wp-config.php`, `phpinfo.php`, `aws.config.js`. 80×404 (67%), 36×429 (30%), 4×200 on root `/` only — zero leak. Same `45.148.10.0/24` as probe #23 (`45.148.10.15`, blocked 2026-06-18).
- **Probe #25 — `45.148.10.67` (CONFIG_SECRET_SCANNER, `TLM-Audit-Scanner/1.0`):** extreme-velocity single burst 2026-06-27 02:43:36–53 UTC (~59 req/s, 17 s, 1,000+ req). Self-identifying UA static on 100% of requests. Multi-technology credential dictionary: Stripe (`stripe-credentials.json`, `stripe-keys.json`, `stripe.env`), Terraform (`.tfvars`, `.tfstate(.backup)`), AWS Lambda (`var/task/amplify.yml`, `docker-compose.yml`, `serverless.yaml`, `next.config.*`), WordPress (`wp-config.php*`, `wp-json/gravitysmtp`, `wp-content/mysql.sql`), `.env` tree (v1/v2/v3/staging/src/srv/shop), Webmin CGI. 635×302 (HTTP→HTTPS), 364×429 (36%), 4×200 (`/`, `/register`, `/?phpinfo=1`, `/?pp=env` — all public-safe). Zero sensitive 200s. Same /24 as #23/#24.
- **Probe #26 — `93.123.109.103` (CONFIG_RCE_SCANNER, new class):** single 6-minute burst 2026-06-24 04:41–47 UTC, 180 req @ ~0.5 req/s. Primary UA Firefox/47.0 (2016-era, static); secondary Chrome/Win10 + empty UA at overlapping timestamps (proxy cluster / multi-tool). Dictionary includes `.aws/credentials` (highest-value target), `swagger.json`, `backend/config/default.yml`, `storage/logs/laravel.log`, `apis/controllers/users.js`, `admin/controllers/merchant.js`. **Escalation:** embedded Node.js `child_process.execSync` RCE probe in a query param (`?param=test?cmd=<base64: echo VULN_TEST>`) targeting JS injection (SSTI/eval). Server is Python/FastAPI — probe returned root-page HTML, zero execution, zero leak. 108×404 (60%), 64×429 (36%), 5×200 (root + ignored query params), 3×302. New signature class `CONFIG_RCE_SCANNER`.
- **UA block — `TLM-Audit-Scanner`:** substring added to `BLOCKED_UA_PATTERNS`; rotation-proof coverage for probe #25 and any successor IPs in the /24.
- **Crawler UAs `agent-tools.cloud-crawler/0.1` + `mcp-rugpull-research/1.0`:** MONITOR only — originate via Cloudflare edge `172.68.23.137`, 57 live hits all 307/redirect, no config/credential probing. No UA block at this volume; re-evaluate if >20/7d or behavior shifts to credential paths.

### /24 watch-item
Three IPs now blocked in `45.148.10.0/24` (#23 + #24 + #25) within 10 days — likely a coordinated campaign or shared rented scan infra. Per Alton 2026-06-28: **remarked as a watch-item, no CIDR `/24` block now** — revisit the CIDR decision (route to T) only if a **4th** IP from this /24 appears within ~30 days.

### Why
All three scanners were already fully deflected by existing defense layers (zero sensitive-path 200s), but L1 IP blocks convert their residual handler-reach to instant 403s at zero processing cost and eliminate recurring log noise. The RCE-probe dimension on `93.123.109.103` raises urgency above hygiene-only. No engagement-metric impact (scanner hits already scrubbed from Report 099). AY+AZ forensics + Sentinel verification 2026-06-28; Alton-approved.

**PR:** _pending_

---

## v0.5.47 - Model Currency (June 23, 2026)

Keeps the BYOK frontier-model menu current and migrates the Gemini integration to the supported SDK. All model IDs were live-verified against each provider before listing (no aspirational names). The default free-tier path (Gemini 2.5 Flash + Groq) is unchanged — cost and stability preserved. 699 tests pass; pre-deploy live Trinity smoke green on both the default and a frontier BYOK config.

### What changed
- **Gemini SDK migration** — `GeminiProvider` moved from the deprecated `google-generativeai` to the current `google-genai` client SDK, required to serve Gemini 3.x. `gemini-3.1-pro-preview` and `gemini-3.5-flash` added as BYOK/frontier options (live-verified end-to-end). The default stays `gemini-2.5-flash` (free-tier, fast, stable).
- **OpenAI → GPT-5.5** — BYOK default updated to `gpt-5.5`; added a gpt-5.x request-contract fix (`max_completion_tokens` instead of `max_tokens`; default-temperature only). gpt-4.x behavior unchanged.
- **Mistral → Medium 3** — BYOK default updated to `mistral-medium-3`.
- **Probe #23** — config/secret scanner `45.148.10.15` added to the IP blocklist (CI/CD + cloud-config + credential enumeration sweep; zero leak).

### Why
Verification quality scales with model quality — keeping the curated BYOK menu current is a user value-add ("models as features"). The Gemini SDK migration was a hard prerequisite for Gemini 3.x (the old SDK 404s on `gemini-3.1-pro-preview`). Live-verifying every ID first caught that `gemini-3.1-pro` is not a real id (the listable id is `gemini-3.1-pro-preview`). Qwen deferred to v0.5.48 (pending an API key). R-S51 (XV-verified) + T+L S45/S46/S51.

**PR:** _pending_

---

## v0.5.46 - BYOK Robustness (June 19, 2026)

Production-hardening bundle surfaced by dogfooding our own M2 P3 evaluation — every fix serves real BYOK users *and* unblocked the clean 100/100 critique-quality baseline run. Strictly additive: no behavior change on the default free-tier path. 698 tests pass (690 + 8 new), 0 regressions.

### What changed
- **Provider-format normalization** — `config_helper.py` now accepts `provider/model` shorthand (e.g. `anthropic/claude-opus-4-8`), splitting it server-side, honoring the model, and returning an actionable error on a bad provider. Fixes the June-17 production rejection of valid `provider/model` BYOK configs.
- **max_tokens** — Z/CS agents raised 4096 → 8192 (`concepts.py`); Groq clamped per-provider via new `_effective_max_tokens()` (`base_agent.py`). The 4096 ceiling was truncating verbose models mid-JSON.
- **Token-monitor repair** — `_output_tokens` is now populated on agent results (`base_agent.py`); the Z-ceiling monitor had silently read 0 since v0.5.3, leaving us blind to truncation.
- **Evidence-coercion** — structured `evidence`/`thought` (dict/list) returned by some providers (e.g. mistral-small) is coerced to a JSON string in `ReasoningStep`, fixing schema-conformance failures in multi-provider runs.

### Why
The M2 P3 evaluation exercised non-default BYOK providers for the first time, surfacing latent gaps that never bit the working default (Gemini X + Groq Z/CS) path. Fixing them ships value to BYOK users (a minority we couldn't previously see, because the monitor was dark) and produced the clean baseline measurement. T+L Session 46 D-46-1/D-46-2 concurred; deploy ratified S47 D-47-1 + Alton.

**PR:** #262

---

## v0.5.45 - Probe Blocklist (MCP-scanner family) (June 16, 2026)

Security/metrics-integrity patch: blocks an MCP-endpoint scanner family that was polluting engagement metrics, plus a self-declared MCP scanner flagged by the orchestrator. `BLOCKED_IPS` 10 → 22; `BLOCKED_UA_PATTERNS` adds three rotation-proof substrings.

### What changed
- **AgentSure-MCPScan family (9 IPs)** — UA `Mozilla/5.0 (compatible; AgentSure-MCPScan/0.1; +https://agentsure.tech)`. Primary IP `152.55.176.35` ran a daily cron (~21:37 UTC, Jun 5–10) with a ~39,779s (~11h) engagement window on Jun 5 alone — polluting "flying hours" as if it were verified engagement. 8 rotating Azure-range IPs share the UA. Zero `/register` intent. AY+AZ forensics 2026-06-12.
- **LeakIX l9scan (2 IPs)** — UA `l9scan/2.0 (+https://leakix.net)`; internet background path-enumeration (`/console/`, `/server-status`, `/about`…). Blocked for metrics cleanliness.
- **MCP Endpoint Scanner (1 IP, `14.194.11.238`)** — UA `MCP-Inspector/1.8.0 (security-scan)`; single 100-second burst on 2026-06-15 (330 req @ ~3.3 req/s), 23-path MCP transport dictionary sweep with embedded JSON-RPC capability-enum payloads (`initialize`, `tools/list`, `resources/list`, `prompts/list`); AS45820 TATAIDC Bengaluru IN. **86% rate-limited (429), zero 200, zero leak.** Orchestrator-flagged; Sentinel investigation 2026-06-16 confirmed BLOCK.
- **UA-substring blocks (rotation-proof):** `AgentSure-MCPScan`, `l9scan`, `(security-scan)` (the last is surgical — catches the self-declared-scanner suffix without colliding with standard MCP Inspector usage).

### Why
Without these blocks, Report 097+ would inherit ~11h of scanner activity as verified engagement. The honest-metrics gate held — AY held Report 097 generation until this deploy. No real handler was reached by any blocked actor (zero 200s); the defense stack (rate limiter + 404/redirect handlers) already held, but L1 blocks convert these to instant 403s at zero rate-limiter cost.

**PR:** #259

---

## v0.5.44 - Reasoning Visible (June 12, 2026)

Makes the auditable reasoning layer — the core of the product — visible in tool responses by default. The X/Z/CS agents already generated per-step reasoning, framework citations, an ethics scoring breakdown, and Socratic questions on every call; previously the flagship `run_full_trinity` JSON response trimmed all of it and returned only scores. This is serialization, not new inference — no added cost or latency.

### What changed

- **New `reasoning` block on `run_full_trinity`** via a `detail` parameter:
  - `detail="standard"` (**new default**) — returns the reasoning block: per-agent reasoning steps, Z's 5-dimension ethics scoring breakdown + framework citations + detected jurisdictions, CS's threat level + Socratic questions + attack vectors, and the per-agent inference quality (with the v0.5.43 `inference_warning`).
  - `detail="full"` — adds per-step evidence and the heaviest structured fields (12-dimension security matrix, 6-stage record, MACP assessment, market-competition analysis).
  - `detail="summary"` — omits the reasoning block, reproducing the exact pre-v0.5.44 response shape (opt-out for cost/context-tight clients).
- **The block is strictly additive** — every existing response field is unchanged at every level; a `summary` call is byte-compatible with prior releases.
- **`consult_agent_x/z/cs`** gain the same `detail` ladder — they previously dropped per-step evidence and the structured fields (scoring breakdown, jurisdictions, threat level, etc.).
- **Markdown report** (`Accept: text/markdown`) now renders the ethics scoring breakdown, detected jurisdictions, CS threat level, and the degraded-inference warning; its generator-version stamp is sourced from the live server version (was pinned at a stale `0.4.1`).
- **Discovery surfaces** (server-card, `/setup`) updated to advertise auditable-reasoning-by-default and the corrected `save_to_history` default.

### Why

VerifiMind's differentiator is auditable, multi-model verification reasoning — and it was being computed, then discarded before reaching the caller. A skeptic received a bare score indistinguishable from any rubric API. Returning the reasoning by default is the proof surface for the epistemic-verification positioning, and the object downstream evaluation scores. Approved by T+L Session 41 (default `standard`; `full` stays free).

**PR:** #256

---

## v0.5.43 - Foundation Integrity (June 11, 2026)

Patch release hardening the verification core and the MCP resource surface — three integrity fixes surfaced by a foundation-effectiveness audit (Issue #68), plus two currency fixes.

### What changed

- **Ethics veto fail-safe (P0):** The Z Guardian veto and ethics score could previously be read off *degraded* inference — if the Z model's JSON was truncated and repaired with schema defaults, the veto flag defaulted to "not triggered" and the ethics score to a midpoint, so a concept that should have been stopped could surface a clean recommendation. The synthesis layer now detects degraded ethics inference (`partial`/`fallback`), caps the recommendation at REVISE, holds the overall score out of the proceed range, and returns an explicit `inference_warning` requiring human review. Genuine (`real`) and test (`mock`) inference are unaffected.
- **Validation-history privacy (P0):** `save_to_history` now defaults to **off**, and the `genesis://history/latest` and `genesis://history/all` resources return only non-identifying summaries / aggregate statistics. Previously the history store was shared per server instance and the resources could surface one caller's concept text to another; concept names and descriptions are no longer exposed through these resources.
- **Methodology resource accuracy (P0):** The `genesis://config/master_prompt` resource is now generated directly from the live agent configuration, so it always reflects the exact X / Z / CS prompts the agents run. It previously served an outdated prompt collection that no longer matched production.
- **Current-date awareness (P1):** Every agent prompt is now anchored to the real current date, so market-recency reasoning and regulatory-deadline checks no longer drift toward the model's training cutoff.
- **Version currency (P1):** `genesis://state/project_info` now reports the live server version.

### Why

A live-tested audit of the flagship `run_full_trinity` tool confirmed the core is effective (the ethics veto fires; production runs genuinely multi-model; scoring is proportional) but found the verdict could rest on synthesized defaults in the degraded path, and that the resource surface had drifted from production. Fail-safe-first behavior and resource accuracy are foundational to an epistemic-verification product.

**PR:** #254

---

## v0.5.42 - Server-Card Description Refresh (June 9, 2026)

Patch release: refreshes the `/.well-known/mcp/server-card.json` MCP discovery surface, which carried stale copy.

### What changed
- **Server-card description refreshed:** removed stale "Genesis v4.2 Sentinel-Verified / Z-Protocol v1.1 (21 frameworks)" marketing; replaced with current accurate descriptors — **13 free MCP tools** (Trinity + prompt-template library + coordination), **BYOK across 6 providers** (Gemini, Anthropic, OpenAI, Groq, Cerebras, Mistral), free tier on Gemini 2.5 Flash.
- **Docstring corrected:** server-card handler is a general MCP discovery card (Smithery listing sunset 2026-03-01), not Smithery-specific.
- **BYOK provider list** in the config schema corrected to the full 6 key-based providers.

### Why
Pre-submission accuracy pass (Google Challenge): the public MCP discovery surface should reflect the current v0.5.41+ feature set, not pre-rebuild marketing copy.

---

## v0.5.41 - Register Page Dead-Link Fix (June 5, 2026)

Patch release: fixes a dead link on the registration page that undermined the v0.5.40 funnel fix.

### What changed

- **`/register` dead link → `/whoami`:** The "Already registered? check your status" link pointed to `/early-adopters/status/` (bare, no UUID) which returned **HTTP 404**. Repointed to `/whoami` (the v0.5.40 self-serve tier/status endpoint, returns 200, accepts `?uuid=` or the `X-VerifiMind-UUID` header). A dead link on the conversion-critical registration page — caught by Alton, fixed same day.

### Why
The v0.5.40 funnel fix removed the structural 404 on the status endpoint itself; this removes the last dead link pointing *at* it from the registration UI. The funnel is now clean end-to-end.

---

## v0.5.40 - Registration Funnel Fix + /whoami + Model Currency (June 5, 2026)

Closes the Scholar UUID registration funnel leak (AY/AZ forensic audit 2026-06-05: 89 interested IPs/30d, 16/16 UUID holders 404-ing on status check, 2.2% conversion), implements `/whoami` self-service tier endpoint (D-30-3), and bumps model list to `claude-opus-4-8`.

### What changed

**Registration funnel — D-30-3 (T+L ruling 2026-06-05)**

- **B3 consolidation:** `rate_limiter.py` reads `early_adopters` (single source of truth) instead of `ea_registrations`. Closes the mismatch that caused Scholar UUID holders to be tier-resolved as anonymous.
- **`/early-adopters/status/{uuid}` fix:** Returns `200 + register CTA` for valid UUIDs without an EA record (was `404` — blocked 16/16 UUID holders per AY/AZ 30d GCP audit). `400` still returned for missing/malformed UUIDs.
- **`/whoami` endpoint (new):** Self-serve tier/status check — reads `X-VerifiMind-UUID` header or `?uuid=` query param. Returns tier, status, rate-limit, and next-step guidance. Rate-limit-exempt. Serves D-29-2 intent-signal work.

**Model currency**

- `provider.py`: `claude-opus-4-7` → `claude-opus-4-8` (current Anthropic Opus, for BYOK users).
- `skills/ai-council/run_council.py`: `claude-sonnet-4-20250514` → `claude-sonnet-4-6` (Z-Agent, unblocks 4-agent AI Council quorum — Issue #68).

---

## v0.5.39 - Registry Scanner Block + P2 Batch-2 (June 1, 2026)

Combines a security-hygiene IP block (10th entry — AY+AZ forensics 2026-05-30) with the second batch of SonarCloud P2 dup-literal constant extractions. Behavior-identical refactors; defense outcome verified zero leak on the new actor (zero handler reached in 400 prior requests).

### What changed

**Blocklist — 10th entry**

- **`3.137.30.179`** — added as **AISEC_REGISTRY_SCANNER**. User-Agent `aisec-registry/0.2 (+https://sec.sqrx.io)` on **100% of 400 requests**; 5-day cron-like persistence (May 23–27, ~80 req/day); **MCP/OAuth surface enumeration** (89× POST `/mcp` + 89× GET `/mcp/.well-known/oauth-{authorization-server,protected-resource,mcp}`); HTTP 200 = **0** (never reached a real handler), 268× 429 (rate-limited), 88× 404 (OAuth discovery failures). Not a builder, not a Scholar conversion candidate, no `/register` intent. AY+AZ forensics 2026-05-30 (see `.macp/handoffs/20260530_AY_to_RNA_block_ip10_3_137_30_179.md`). **`BLOCKED_IPS`: 10 entries total** (was 9).

**SonarCloud P2 batch-2 — 8 module-level constants extracted from 25 dup-literal occurrences**

- `mcp-server/src/verifimind_mcp/llm/provider.py` — extracted **4 provider-default-model constants**: `PROVIDER_DEFAULT_GEMINI_MODEL` ("gemini-2.5-flash", 3×), `PROVIDER_DEFAULT_OPENAI_MODEL` ("gpt-4.1-mini", 3×), `PROVIDER_DEFAULT_GROQ_MODEL` ("llama-3.3-70b-versatile", 3×), `PROVIDER_DEFAULT_CEREBRAS_MODEL` ("llama-3.3-70b", 3×).
- `mcp-server/src/verifimind_mcp/server.py` — extracted **4 agent/prompt constants**: `AGENT_X_NAME` ("X Intelligent", 4×), `AGENT_Z_NAME` ("Z Guardian", 3×), `AGENT_CS_NAME` ("CS Security", 3×), `MASTER_PROMPT_FILENAME` ("reflexion-master-prompts-v1.1.md", 3×).

**Scope discipline (substance preservation per Genesis §13.X proposal)**

- **Deferred (1 candidate):** `"?"` placeholder at `provider.py:361` — extracting a single-char marker to a named constant would add more cognitive load than the SonarCloud noise it removes. Alternative: mark Safe in SonarCloud UI.
- **Out of P2 batch-2 scope:** S3776 cognitive-complexity refactors (6 in provider.py, 1 in server.py) — slated for P2 batch-3 (function-level refactors, different risk profile than mechanical extractions).
- **False-match audit pre-flight (PASSED):** verified `"gemini-2.5-flash"` ≠ `"gemini-2.5-flash-lite"` substring and `"llama-3.3-70b"` ≠ `"llama-3.3-70b-versatile"` substring (closing-quote bracketing prevents replace_all collision).

### Files
- `mcp-server/src/verifimind_mcp/middleware/ip_blocklist.py` — +1 entry with forensic comment
- `mcp-server/src/verifimind_mcp/llm/provider.py` — 4 constants (12 occurrences → 4 definitions)
- `mcp-server/src/verifimind_mcp/server.py` — 4 constants (13 occurrences → 4 definitions)

---

## v0.5.38 - Scanner Block (May 29, 2026)

Adds two scanners to the application-layer IP blocklist after GCP log forensic analysis (Sentinel investigation, 2026-05-29). Defense layers caught everything; zero data leak on either actor.

### What changed

- **`4.228.83.111` (Azure/Microsoft)** — added as **CMS_WEBSHELL_SCANNER**. Two bursts (2026-05-21 + 2026-05-26 14:40–14:42 UTC); ~310 req/7d; **null User-Agent** on every request. WordPress and generic PHP webshell dictionary: `wp-login.php`, `xmlrpc.php`, `wp-admin/alfa.php`, `wp-content/uploads/goods.php`, `wso.php`, `gecko.php`, `chosen.php`, `lock360.php`, `god4m.php`, ~140 additional PHP webshell names (one mixed-case `randkeyword.PhP7` — extension-case evasion attempt). Defense breakdown: 50% caught by HTTP→HTTPS redirect (Layer 3), 37% rate-limited (429, Layer 2), 13% returned 404. **Zero 200 responses.** No VerifiMind handler was reached; scanner is unaware it is hitting a Python/FastAPI service — indiscriminate spray.

- **`2602:fb54:99a::` (IPv6)** — added as **SECRET_SCANNER** (same class as `195.178.110.199`, blocked 2026-05-13). Single 15-second burst 2026-05-25 19:13:03–19:13:18 UTC, 65 requests at ~4.3 req/s. **Rotating User-Agent across 18+ distinct browser/OS strings** per request (Windows/Chrome v145–147, Edge v146–147, macOS/Safari, Linux/Firefox v149–150, iOS/Safari) — botnet / distributed-proxy pattern, distinguishing this actor from the static-UA SECRET_SCANNER blocked 2026-05-13. Three-phase probe: (1) GCP-specific service-account JSON files (`serviceAccountKey.json` was literally the first probe — GCP-aware attacker), then 20+ credential JSON names; (2) `.env` variant tree across 28 paths including `.env.production.*` / `.env.local.*` backup variants; (3) `.git` internals (`HEAD`, `config`, `logs/HEAD`, `refs/heads/main`, `refs/heads/master`). Defense breakdown: 60% rate-limited (429), 34% returned 404, **3× 200 — all on the public root `/`** (known-safe surface, zero leak). Address-only block, not `/48`: the prefix scan returned only the base address, no multi-host rotation evidence.

- **Cross-correlation:** the two actors operated **19 hours apart** with different tooling (null UA vs rotating UA) and different target classes (CMS vs secrets) — **independent actors, not coordinated infrastructure.**

- **`BLOCKED_IPS`:** 9 entries total (was 7).

### Files
- `mcp-server/src/verifimind_mcp/middleware/ip_blocklist.py` — 2 new entries with forensic comments

---

## v0.5.37 - Tier Clarity (May 26, 2026)

Branches the 429 rate-limit CTA so the response fits *why* the caller is anonymous, and surfaces `uuid_status` for diagnosis. Driven by a tier-setup audit (findings T1–T6).

### What changed
- **429 response body now branches on `uuid_status` (`absent` | `invalid` | `valid`):**
  - *No UUID header* → acquisition CTA: register a free Scholar UUID (30/60s + BYOK + dashboard), with the Privacy-Doctrine-v1.0 line and a founder/feedback note.
  - *UUID header present but invalid* → **recovery** hint (`VERIFIMIND_UUID` unset / `your-uuid-here` placeholder → see `/setup`) instead of wrongly pitching registration to someone who already has a UUID.
- `uuid_status` added to the 429 JSON body and the rate-limit warning log (observability for misconfigured-Scholar detection — AY funnel signal).
- CTA logic extracted to a pure `_build_rate_limit_cta()` helper with 4 new unit tests.
- Version bump 0.5.36 → 0.5.37 (both `SERVER_VERSION` surfaces + 9 test files); `server.json` 3.13.0 → 3.14.0.

### Why
A tier-setup audit — prompted by a Scholar-tier user being rate-limited as Anonymous — found: the rate limiter resolves tier *solely* from the `X-VerifiMind-UUID` header (T1); the downgrade to Anonymous is silent (T2); the tool-response `tier` field (from `tier_gate`, = "not Pioneer") contradicts the rate-limiter tier (T5); and the rate limiter reads an **empty** `ea_registrations` collection for Pioneer quota while real registrations live in `early_adopters` (T6 — Pioneer rate tier effectively dead). v0.5.37 ships the user-facing half (recovery CTA + diagnosis). The deeper reconciliation (T3/T6 — single source of truth for caller tier; fix the collection mismatch) is routed to T (CTO) in a forensic audit report — see PRIVATE `.macp/handoffs/`.

### Evidence
AY/AZ Report 092 (May 21–24) showed active anonymous builders hitting the IP-tier wall with 0 registrations — the exact cohort the branched CTA targets.

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
