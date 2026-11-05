# VerifiMind-PEAS Server Status

**Last updated:** November 5, 2026

**Evidence cutoff:** v0.5.68 deployment verified November 5, 2026, 09:14–09:35 UTC
(17:14–17:35 in Malaysia, the operator's timezone). The v0.5.67 deployments of
October 27 and November 1, 2026 (`00519-4c2` through `00522-hnp`) are summarized
below; v0.5.66 was verified October 18, 2026, and earlier revisions are listed
in the deployments table.

**Status authority:** this dated operational snapshot; release history lives in
[`CHANGELOG.md`](CHANGELOG.md) and [GitHub Releases](https://github.com/creator35lwb-web/VerifiMind-PEAS/releases).

## Current production snapshot

| Surface | Verified state |
|---|---|
| Application | **v0.5.68** — security currency: Authlib 1.9.4 / joserfc 1.7.7 / pydantic 2.14.2 as one tested set in both manifests, on v0.5.67's runtime stack (FastMCP 4.1.2 / MCP SDK 2.2.0 / Starlette 1.8.0 / FastAPI 0.143.3 / uvicorn 0.54.0 / cryptography 50.0.2); Cerebras and Groq BYOK catalogues re-verified; no routing, policy or authentication change (Privacy Policy v2.7 / Terms v2.6 unchanged); protocol era `2026-07-28` advertised and served |
| Public merge | [`35ea615d491da1aa590ef89b839c1683dbc149be`](https://github.com/creator35lwb-web/VerifiMind-PEAS/commit/35ea615d491da1aa590ef89b839c1683dbc149be) (PR #399) |
| Merged head | `7059cde74c97c88250ace95ad9602eb3481b7ec3` (the CTO-reviewed head: bounded exact-head PASS before the merge; the merge tree `8ed95ee71b2b` equals the head's tree) |
| Merge base | `f0c2782466592b94bb4092ea6340a556557b32bb` |
| Cloud Build | `5401b7a8-cb46-4b22-8074-38933b0e9ce8` — **SUCCESS**, started 7 s after the merge, `COMMIT_SHA` bound to the merge, Python 3.12.12, installed pins listed in the build log; image `sha256:44174c353bcfed93064d745a747058d40b4cdc051399d192c805b5ce32d44340` |
| Serving revision | **`verifimind-mcp-server-00523-pwq`** at 100% traffic, Ready, created November 5, 2026 at 09:15 UTC on the build's image digest; environment-variable names, scale, concurrency and timeout identical to `00522-hnp` |
| Previous revision | `verifimind-mcp-server-00522-hnp` — v0.5.67 with #396 (image `sha256:1e5c9ce7ab80cac4e9d3e0dcb2df1f58a03f586525c574b9f4e8ccf64d99d63b`), retained as the rollback target |
| MCP Registry package | **3.43.0** — still the live package, published by the [v0.5.66 GitHub Release](https://github.com/creator35lwb-web/VerifiMind-PEAS/releases/tag/v0.5.66) on October 18, 2026. The GitHub Release for v0.5.68, which also covers v0.5.67, publishes **3.45.0**; the 3.44.0 manifest prepared for v0.5.67 was never published |
| Tool inventory | **13 defined / 8 active / 5 temporarily unavailable** |
| MCP transport | Streamable HTTP, **stateless** (no session header); protocol `2026-07-28` advertised and served sessionless; the handshake eras up to `2025-11-25` remain supported on the same mount |
| Firestore | Connected during verified post-deploy health checks |
| Runtime failover | `runtime_failover_enabled: false` |
| Hosted X | Gemini `gemini-3.5-flash-lite` |
| Hosted Z | Groq `openai/gpt-oss-120b` |
| Hosted CS | Groq `openai/gpt-oss-120b` |
| BYOK model catalogue | `current` on `/health`. Cerebras and Groq re-verified November 4, 2026; the next 90-day windows lapse December 20 (OpenAI) and December 23 (Gemini, Anthropic, Mistral) |
| Account service | Registration and UUID-linked account features are **temporarily unavailable during security maintenance** (since September 17, 2026) |
| Ambient MCP notice | **Out of date.** Every tool response still carries, as `_system_notice`, the text set for v0.5.66: *"v0.5.66 is live (MCP 2026-07-28): 8 active tools, 5 temporarily unavailable, all free. Registration for the four execution tools starts on a date announced at https://verifimind.ysenseai.org/terms at least 14 days in advance, not before. Account features remain in maintenance."* Cloud Build deployments carry the service configuration forward, so the value has not changed since `00518-pkp`; everything in it except the version is current. A configuration-only refresh is a separate maintainer decision |
| OAuth 2.1 authorization server | Deployed **dark**: credential issuance off, MCP enforcement off. The two discovery documents are served; the OAuth endpoints answer `503` |
| Policies | Terms v2.6 / Privacy v2.7, published and effective October 15, 2026: the registration requirement for the four execution tools takes effect on a date announced on the policy pages at least 14 days in advance, and not before (no date has been announced) |

## Release verification

- [Public PR #399](https://github.com/creator35lwb-web/VerifiMind-PEAS/pull/399) was merged by the
  maintainer on 2026-11-05 at 09:14:01 UTC (17:14 in Malaysia). The merge tree
  `8ed95ee71b2b` is identical to the reviewed head's tree, the tree every
  hosted check at the exact head exercised.
- Review: the CTO's bounded exact-head review passed at `7059cde7`
  (independent credential-free replay: unit 1,704 passed / 2 skipped,
  registration 84, docs contract 315, security CI passed, plus 22 loopback
  transport checks and 7 transport tests). It found no blocking code issue and
  one nonblocking documentation correction, applied to the PR description
  before the merge and to `CHANGELOG.md` with this snapshot: the advisory count
  is a dated reading of three sources (17 records), not a complete inventory,
  and one pydantic advisory concerns a schema on the request path.
- Build: Cloud Build `5401b7a8-cb46-4b22-8074-38933b0e9ce8` started 7 s after
  the merge from the exact merge source (`COMMIT_SHA` bound), on Python
  3.12.12; its log lists the installed pins (authlib 1.9.4, joserfc 1.7.7,
  pydantic 2.14.2, pydantic-core 2.50.2, fastmcp 4.1.2, fastmcp-slim 4.1.2,
  mcp 2.2.0, mcp-types 2.2.0, starlette 1.8.0, fastapi 0.143.3, uvicorn 0.54.0,
  cryptography 50.0.2, httpx2 2.16.0). Image
  `sha256:44174c353bcfed93064d745a747058d40b4cdc051399d192c805b5ce32d44340`. It
  is the only build since the #396 build of November 1.
- Configuration: `00523-pwq` carries the same 11 environment-variable names,
  scale (at most 3 instances), concurrency (10) and timeout (600 s) as
  `00522-hnp`. **No authentication gate variable and no `FASTMCP_*` variable
  is set**, so credential issuance and MCP enforcement both sit at their code
  default, which is off.
- Hosted checks on the merge commit: 12 of 12 succeeded, including image
  dependency parity and the dependency audit, which had failed on `main` since
  late October while the old Authlib and joserfc pins were in place. GitHub
  closed all 18 Dependabot alerts at 09:15 UTC (nine advisories, each in both
  manifests); none is open.
- Versioned smoke oracle (09:19–09:29 UTC): **46 pass / 0 stop / 0 instrument**
  against production. Its known-positive ran first, also against production:
  told to expect 0.5.67, the same oracle stopped on exactly its four version
  checks. `/health` reports 0.5.68 with `protocol_version 2026-07-28`, Firestore
  connected, inference live and the catalogue current; the server card agrees;
  the eight contained account routes answer the maintenance `503`; OAuth
  discovery is served and the five endpoints are dark; the unavailable-tool
  denials, the protocol eras, the typed BYOK failure contract (invalid key →
  `BYOK_AUTH_FAILED` per stage, decision surface withheld) and a reflection
  scan over 42 response bodies all passed.
- **Trinity, as observed: one anonymous run — X real, Z real, CS real,
  outcome full,** 39.5 s; Z used 3,116 of its 4,096-token completion
  reservation and CS 3,578 of 3,757; no stage error and no failover attempt.
  One run is not a reliability figure; see the known limitation below.
- Advisories, read at 09:19 UTC in the upstream repositories, GitHub's advisory
  database and OSV: no record names Authlib 1.9.4, joserfc 1.7.7 or pydantic
  2.14.2, and OSV has no record for any of the 12 exact pins checked.

### v0.5.67 (October 27 to November 1, 2026)

This snapshot was not converted for v0.5.67; its record is in
[`CHANGELOG.md`](CHANGELOG.md). PR #385 (FastMCP 4.1.1 / Starlette 1.8.0 /
FastAPI 0.143.3 as one tested set) and PR #368 (completion diagnostics) merged
about a minute apart on October 27, followed the same day by #393 (FastMCP
4.1.2) and on November 1 by #396 (diagnostics containment). Each runtime merge
built and deployed once (`00519-4c2` to `00522-hnp` in the table below). The
versioned oracle passed 48/0/0, 46/0/0 and 48/0/0 after the #368, #393 and #396
deployments, each after a known-positive, and the three anonymous Trinity runs
were partial (CS rate-limited), full, and partial (CS truncated at its
completion reservation). No GitHub Release or Registry publication was made for
v0.5.67; the v0.5.68 Release covers both versions.

## Deployments since the previous snapshot (August 26, 2026)

| Date (UTC) | Serving revision | Source | Change |
|---|---|---|---|
| 2026-09-01 | `00504-c8d` | configuration only, same image | One malformed, unused secret-backed variable removed. No code, routing or version change |
| 2026-09-17 | `00505-cvt` | [PR #354](https://github.com/creator35lwb-web/VerifiMind-PEAS/pull/354) → `3727662a` | Maintenance mode for legacy account features: registration and UUID-linked account routes answer a fixed maintenance response |
| 2026-09-17 | `00506-7n8` | [PR #355](https://github.com/creator35lwb-web/VerifiMind-PEAS/pull/355) → `32881961` | Test-only change; maintenance behaviour re-verified at runtime |
| 2026-09-20 | `00507-bzj` | [PR #356](https://github.com/creator35lwb-web/VerifiMind-PEAS/pull/356) → `4e357fec` | OpenAI BYOK catalogue re-verified live; verification date advanced under the 90-day currency contract |
| 2026-09-21 | `00508-dj8` | [PR #346](https://github.com/creator35lwb-web/VerifiMind-PEAS/pull/346) → `07b422f1` | **v0.5.63** — authentication foundation, dark |
| 2026-09-22 | `00509-m7g` | [PR #357](https://github.com/creator35lwb-web/VerifiMind-PEAS/pull/357) → `a8e8f541` | uvicorn `0.52.4 → 0.53.0` (both manifests); Cloud Build `c4ff91e5-7d69-4b85-a158-b08a0f4ae6d5`; the image's installed pin confirmed in the build log; v0.5.63 unchanged. Read-back: `/health` 0.5.63, all eight legacy account routes still answer the maintenance `503`, both OAuth discovery documents `200`, all five OAuth endpoints `503` (dark), anonymous MCP `initialize` `200` with no session header, policies unchanged. No Trinity smoke was run for this server-framework change |
| 2026-09-22 | `00510-8h9` | [PR #349](https://github.com/creator35lwb-web/VerifiMind-PEAS/pull/349) → `b5baa879` | pydantic `2.13.4 → 2.13.5` (both manifests); Cloud Build `aaa84c2b-6482-4ff0-b44e-3952a0eef5aa`; installed pins confirmed in the build log. The PR had been opened against a 26 August base and was merged without a rebase, so its checks predated v0.5.63; the gap was closed after deploy by running the full unit suite on the exact deployed tree with pydantic 2.13.5 (1,648 passed, 4 skipped, 0 failed). Read-back identical to `00509-m7g`: containment `503` on all eight routes, OAuth dark, anonymous MCP unchanged, `/health` 0.5.63. No Trinity smoke |
| 2026-09-23 | `00511-kf7` | [PR #364](https://github.com/creator35lwb-web/VerifiMind-PEAS/pull/364) → `7687325d` | BYOK catalogue currency: Gemini, Mistral and Anthropic model lists re-verified live on September 23 (listing calls only); `mistral-large-latest` retired because it no longer exists at the provider; hosted routing unchanged; Cloud Build `2cfb12fc-5b7e-4cf3-a364-e76b8a4326e2`. Read-back identical to `00510-8h9`; `/health` catalogue `current`. No Trinity smoke |
| 2026-09-23 | `00512-hgk` | configuration only, same image as `00511-kf7` | Ambient service notice refreshed. The previous notice predated the account-feature maintenance and had been suppressed by the server's own consistency check since September 17, so tool responses carried no notice; the new notice states the current tool availability, the announced October 20, 2026 account requirement, and that account features are in maintenance. Delivery confirmed in a live tool response |
| 2026-09-24 | `00513-klm` | [PR #362](https://github.com/creator35lwb-web/VerifiMind-PEAS/pull/362) → `2685d4c7` | **v0.5.64** — FastMCP `3.4.7 → 4.0.5` and MCP SDK `1.28.1 → 2.2.0` as one tested set (both manifests); protocol era `2026-07-28` served sessionless; Cloud Build `50896a37-f06e-484a-beb8-6647435f0eb6`; installed pins in the image: fastmcp 4.0.5, mcp 2.2.0, mcp-types 2.2.0, httpx2 2.13.1, starlette 1.6.0, uvicorn 0.53.0, pydantic 2.13.5 (Python 3.12.12). Post-deploy Trinity smoke recorded as observed — see the release verification |
| 2026-09-24 | `00514-dnc` | configuration only, same image as `00513-klm` | Ambient service notice refreshed for v0.5.64 (it carried the advance notice of the October 20 date, since superseded by v0.5.65) |
| 2026-10-15 | `00515-q9f` | [PR #377](https://github.com/creator35lwb-web/VerifiMind-PEAS/pull/377) → `ba9b20a6` | **v0.5.65** — Privacy Policy v2.7 / Terms v2.6: the fixed October 20, 2026 registration date is replaced by a standing promise of at least 14 days' notice on the policy pages; policy text and release identity only, no behaviour change; Cloud Build `da4c87ec-d836-452b-a312-6c64178cb389` |
| 2026-10-15 | `00516-48g` | configuration only, same image as `00515-q9f` | Ambient service notice refreshed on the maintainer's GO: the previous value (set for v0.5.64 on September 24) still announced the withdrawn October 20 date on every tool response; the new value states the standing notice promise. Delivery verified on both protocol paths; rollback value captured |
| 2026-10-18 | `00517-l2d` | [PR #382](https://github.com/creator35lwb-web/VerifiMind-PEAS/pull/382) → `2903bb8d` | **v0.5.66** — runtime currency: fastmcp `4.0.5 → 4.0.10`, starlette `1.6.0 → 1.7.0`, fastapi `0.141.1 → 0.142.2`, uvicorn[standard] `0.53.0 → 0.54.0`, cryptography `50.0.1 → 50.0.2` as one tested set (both manifests; `mcp` stays 2.2.0); Cloud Build `019112d5-b6b8-4497-a136-3276df9038f9`; installed pins confirmed in the build log; third-party notice re-bound to the cryptography 50.0.2 artifacts |
| 2026-10-18 | `00518-pkp` | configuration only, same image as `00517-l2d` | Ambient service notice refreshed for v0.5.66 (the previous value still announced v0.5.65 on a 0.5.66 server; the single change is the version) |
| 2026-10-27 | `00519-4c2` | [PR #385](https://github.com/creator35lwb-web/VerifiMind-PEAS/pull/385) → `1109bb61` | **v0.5.67** — runtime currency II: fastmcp `4.0.10 → 4.1.1`, starlette `1.7.0 → 1.8.0`, fastapi `0.142.2 → 0.143.3` as one tested set (both manifests; `mcp` stays 2.2.0); Cloud Build `8d935f95-cbde-4552-9298-a98e4f890e81`; replaced within minutes by `00520-v5b` |
| 2026-10-27 | `00520-v5b` | [PR #368](https://github.com/creator35lwb-web/VerifiMind-PEAS/pull/368) → `798f0c4e` | Completion diagnostics envelope (observability only); Cloud Build `15a851f5-ce4d-45b5-85c8-6da20f7310a9`; oracle 48/0/0, one Trinity run partial (CS rate-limited) |
| 2026-10-27 | `00521-47n` | [PR #393](https://github.com/creator35lwb-web/VerifiMind-PEAS/pull/393) → `19120178` | fastmcp `4.1.1 → 4.1.2` (both manifests), fixing two FastMCP advisories; Cloud Build `c1f30520-68e1-4e25-b2c1-93b8a0e60774`; oracle 46/0/0, one Trinity run full |
| 2026-11-01 | `00522-hnp` | [PR #396](https://github.com/creator35lwb-web/VerifiMind-PEAS/pull/396) → `a73ed068` | Diagnostics containment (the first #368 hardening item); Cloud Build `1cc6200c-bbc5-4b71-bb1e-87494b38f7d4`; oracle 48/0/0, one Trinity run partial (CS truncated) |
| 2026-11-05 | `00523-pwq` | [PR #399](https://github.com/creator35lwb-web/VerifiMind-PEAS/pull/399) → `35ea615d` | **v0.5.68** — security currency: Authlib `1.8.0 → 1.9.4`, joserfc `1.7.5 → 1.7.7`, pydantic `2.13.5 → 2.14.2` as one tested set (both manifests); Cerebras and Groq BYOK catalogues re-verified; Cloud Build `5401b7a8-cb46-4b22-8074-38933b0e9ce8`; oracle 46/0/0, one Trinity run full |

Each build ran from the exact `main` commit shown; `00504-c8d` was a
configuration-only revision on the existing image. The application version
stayed at 0.5.62 until `00508-dj8`, was 0.5.63 from `00508-dj8` through `00512-hgk`, was 0.5.64 from `00513-klm` through `00514-dnc`, was 0.5.65 from `00515-q9f` through `00516-48g`, was 0.5.66 from `00517-l2d` through `00518-pkp` (a configuration-only revision on the same image), was 0.5.67 from `00519-4c2` through `00522-hnp`, and is 0.5.68 from `00523-pwq` on. PR #348
(`codeql-action` pins, `.github/` only) merged the same day and correctly
caused no build. Since v0.5.66 the docs-only merges #383, #384, #394, #395 and #397 and the
GitHub Actions update #376 also caused no build.

## Availability

The five temporarily unavailable tools are:

- `coordination_handoff_create`
- `coordination_handoff_read`
- `coordination_team_status`
- `register_custom_template`
- `import_template_from_url`

The three coordination tools return `COORDINATION_TEMPORARILY_DISABLED`; the two
custom-template mutation tools return `CUSTOM_TEMPLATE_TEMPORARILY_DISABLED`.
Built-in template reads and all four validation tools remain available. The
Core Tools Always Free pledge is unchanged.

Registration and UUID-linked account features — registration, account status,
the personal dashboard, feedback submission and the self-service opt-out — are
temporarily unavailable during security maintenance. The affected routes answer a fixed
`503` that reads and changes no account data; the registration page says so
in plain words. **You do not need an account to use VerifiMind today:** every
active tool works anonymously at the standard rate limit. For an urgent access,
correction or deletion request, use the private channel on the
[opt-out page](https://verifimind.ysenseai.org/optout).

## Announced change: registration for the execution tools

Terms v2.6 and Privacy v2.7 (effective October 15, 2026) replace the fixed
**October 20, 2026** date that the previous revisions announced. The standing
promise is: the four execution tools (`consult_agent_x`, `consult_agent_z`,
`consult_agent_cs`, `run_full_trinity`) will require an authenticated session
tied to a free registered account from a date that will be announced on the
policy pages at least 14 days in advance, and not before. Tool discovery, the
template-read tools and every web page stay open without registration, and the
tools remain free.

As of this snapshot **no date has been announced and nothing enforces that
requirement**: both gates are off, and anonymous execution works. Announcing a
date is itself a policy revision with at least 14 days' notice, and turning
enforcement on is a separate release decision; this file will record both when
they happen.

## Known limitations and follow-up

- **Hosted Trinity runs do not reliably complete in full.** The hosted Z and
  CS stages share one Groq model and therefore one per-minute token admission
  budget. CS receives an effective completion reservation of roughly 3.6–3.9k
  tokens against a configured 8,192, so whether a run finishes depends on how
  long that answer happens to be. When it does not fit, the run is reported as
  degraded or partial, the recommendation is capped and human review is
  required — it is never silently mocked. In our own post-deploy smokes since
  September this has been frequent, not rare: neither v0.5.63 smoke run completed
  in full, and the v0.5.64 pre-merge smoke saw CS fail on Groq on the same tree
  and on the previous framework; the single v0.5.64 post-deploy run completed
  with CS at 86% of its reservation; the single v0.5.66 post-deploy run did
  not complete (CS truncated at a 3,775-token reservation) while the pre-merge
  run on the identical tree did. Of the four post-deploy runs since v0.5.67,
  two completed in full (after #393 and after v0.5.68) and two did not (CS
  rate-limited after #368, CS truncated at a 3,772-token reservation after
  #396). The completion retry added in v0.5.60 covers provider rate-limit
  rejections that state a wait; a truncated or structurally incomplete answer
  is deliberately not retried, because a blind re-run inside the same
  reservation has no provider-guaranteed payoff. A structural fix — separate
  provider lanes for Z and CS, or a shorter CS output contract — has not
  been made and is not part of any release through v0.5.68. BYOK callers can avoid the
  shared budget by routing the two stages to different providers
  (`z_provider` / `cs_provider`).
- The OAuth 2.1 surfaces have not been through an isolated staging run, and in
  production they have so far been exercised only by our own probes. While
  issuance is dark, an MCP client that reads the discovery documents
  proactively will find an authorization server whose endpoints answer `503`.
  Anonymous connection is verified with a Claude Code client; it has not been
  verified with every OAuth-capable client. If yours fails to connect, please
  [open an issue](https://github.com/creator35lwb-web/VerifiMind-PEAS/issues).
- Coordination and custom-template mutation remain contained, not restored.
- The completion-diagnostics envelope added in v0.5.67 (#368) has two open
  hardening items: after a retry it can report an earlier attempt's snapshot
  as the final one, and a received but empty or inconsistent provider
  response can be reported as no response, or with an inconsistent reasoning
  share. The envelope is designed as observability only.
- The model-freshness table in `mcp-server/docs/BYOK_GUIDE.md` still names
  `llama-3.3-70b` as the Cerebras default; the guide's provider table and the
  code use `gpt-oss-120b`. The row is corrected with the next runtime change,
  because any change under `mcp-server/` deploys.
- Runtime cross-provider failover remains disabled. The hosted routing shown
  above is construction-time routing, not request-time failover.
- No "vulnerability clean" claim is made for this release. The dependency audit
  is a strict, fail-closed `pip-audit` of the deployment project and passed on
  the v0.5.68 merge commit. Advisory databases lag the upstream projects: on
  November 5, 2026, eight of the seventeen records that named the old pins
  were still only in the upstream repositories, so a passing audit is a dated
  reading, not an inventory. `mistralai` is still declared as a range
  (`>=1.0.0`), so that package is audited at whatever version resolves on the
  day.
- `safe_diagnostic_value` is a character-bounding helper, not a general secret
  redactor; renaming/documentation remains follow-up work.
- Qualified-counsel review and any retrospective incident-notification decision
  remain parallel human/legal work. Software verification does not close them.

## Public endpoints

- MCP: `https://verifimind.ysenseai.org/mcp/`
- Health: `https://verifimind.ysenseai.org/health`
- Discovery: `https://verifimind.ysenseai.org/.well-known/mcp-config`
- Setup: `https://verifimind.ysenseai.org/setup`
- Register: `https://verifimind.ysenseai.org/register` (maintenance notice)
- Terms: `https://verifimind.ysenseai.org/terms`
- Privacy: `https://verifimind.ysenseai.org/privacy`
- OAuth discovery (dark): `https://verifimind.ysenseai.org/.well-known/oauth-authorization-server`
  and `https://verifimind.ysenseai.org/.well-known/oauth-protected-resource`
- Public statements: `https://github.com/creator35lwb-web/VerifiMind-PEAS/wiki/Public-Statements`
