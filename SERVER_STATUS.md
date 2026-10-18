# VerifiMind-PEAS Server Status

**Last updated:** October 18, 2026

**Evidence cutoff:** v0.5.66 deployment verified October 18, 2026, 03:05–04:35 UTC
(11:05–12:35 in Malaysia, the operator's timezone); Release and Registry 05:08 UTC,
verified 05:22 UTC. The v0.5.65 release
deployment was verified October 15, 2026 (`00515-q9f`, then the configuration-only
ambient-notice refresh `00516-48g`); earlier revisions are listed in the
deployments table.

**Status authority:** this dated operational snapshot; release history lives in
[`CHANGELOG.md`](CHANGELOG.md) and [GitHub Releases](https://github.com/creator35lwb-web/VerifiMind-PEAS/releases).

## Current production snapshot

| Surface | Verified state |
|---|---|
| Application | **v0.5.66** — runtime currency: FastMCP 4.0.10 / MCP SDK 2.2.0 / Starlette 1.7.0 / FastAPI 0.142.2 / uvicorn 0.54.0 / cryptography 50.0.2 as one tested set in both manifests; no application-code, routing, policy or authentication change (Privacy Policy v2.7 / Terms v2.6 unchanged); protocol era `2026-07-28` advertised and served |
| Public merge | [`2903bb8d3ec4a24e143b359d52b77920ffa8fe25`](https://github.com/creator35lwb-web/VerifiMind-PEAS/commit/2903bb8d3ec4a24e143b359d52b77920ffa8fe25) (PR #382) |
| Merged head | `5a56e137c079c0a48fc6090ddc03835c740227f6` (the CTO-reviewed head: bounded exact-head PASS, bound to the merge after it landed; the merge tree `a05076e23cbf` equals the head's tree) |
| Merge base | `a65b3aec209ef223aa61f7b6b36868fa4d01bede` |
| Cloud Build | `019112d5-b6b8-4497-a136-3276df9038f9` — **SUCCESS**, started 6 s after the merge, `COMMIT_SHA` bound to the merge, Python 3.12.12, installed pins listed in the build log; image `sha256:fc705da94716925264c316b99ccba695258635f4361895458de634ff933fd5de` |
| Serving revision | **`verifimind-mcp-server-00518-pkp`** at 100% traffic, Ready — a configuration-only revision (ambient service notice refreshed, October 18, 2026 at 04:33 UTC) on the **same image digest** as the v0.5.66 release revision `verifimind-mcp-server-00517-l2d`; configuration otherwise identical |
| Previous revision | `verifimind-mcp-server-00517-l2d` — the v0.5.66 release revision (same image; created October 18, 2026 at 03:06 UTC), retained as the rollback target; `00516-48g` and `00515-q9f` (v0.5.65 image) are also retained |
| MCP Registry package | **3.43.0** — published by the [v0.5.66 GitHub Release](https://github.com/creator35lwb-web/VerifiMind-PEAS/releases/tag/v0.5.66) on October 18, 2026 at 05:08 UTC through the registry workflow; API-verified live and marked latest. The Release tag resolves to `623f0203` (the docs-only truth-conversion merge #383 that followed the deployment); its `mcp-server/` subtree and `server.json` are identical to the deployed merge `2903bb8d` |
| Tool inventory | **13 defined / 8 active / 5 temporarily unavailable** |
| MCP transport | Streamable HTTP, **stateless** (no session header); protocol `2026-07-28` advertised and served sessionless; the handshake eras up to `2025-11-25` remain supported on the same mount |
| Firestore | Connected during verified post-deploy health checks |
| Runtime failover | `runtime_failover_enabled: false` |
| Hosted X | Gemini `gemini-3.5-flash-lite` |
| Hosted Z | Groq `openai/gpt-oss-120b` |
| Hosted CS | Groq `openai/gpt-oss-120b` |
| Account service | Registration and UUID-linked account features are **temporarily unavailable during security maintenance** (since September 17, 2026) |
| Ambient MCP notice | Delivered as `_system_notice` on every tool response since `verifimind-mcp-server-00518-pkp`: *"v0.5.66 is live (MCP 2026-07-28): 8 active tools, 5 temporarily unavailable, all free. Registration for the four execution tools starts on a date announced at https://verifimind.ysenseai.org/terms at least 14 days in advance, not before. Account features remain in maintenance."* (the single change from the previous value is the version) |
| OAuth 2.1 authorization server | Deployed **dark**: credential issuance off, MCP enforcement off. The two discovery documents are served; the OAuth endpoints answer `503` |
| Policies | Terms v2.6 / Privacy v2.7, published and effective October 15, 2026: the registration requirement for the four execution tools takes effect on a date announced on the policy pages at least 14 days in advance, and not before (no date has been announced) |

## Release verification

- [Public PR #382](https://github.com/creator35lwb-web/VerifiMind-PEAS/pull/382) was merged by the
  maintainer on 2026-10-18 at 03:04:49 UTC (11:04 in Malaysia). The merge tree
  `a05076e23cbf` is identical to the reviewed head's tree — the tree every
  hosted check (9 of 9 at the exact head, image parity included) and the
  pre-merge smoke exercised.
- Review: the CTO's bounded exact-head review passed at `5a56e137` (independent
  credential-free replay: unit 1,652 passed / 2 skipped at 80.49% coverage,
  registration 84, integration 7 / 11 skipped, notices and manifest parity 19
  with five negative controls caught, docs contract 307, keyless transport
  15/15) and was bound to the merge after it landed. No application code
  changed except the two version constants; the delta is five dependency pins,
  the third-party notice re-binding and the release identity.
- Build: Cloud Build `019112d5-b6b8-4497-a136-3276df9038f9` started 6 s after the
  merge from the exact merge source (`COMMIT_SHA` bound), on Python 3.12.12;
  its log lists the installed pins (fastmcp 4.0.10, fastmcp-slim 4.0.10, mcp
  2.2.0, mcp-types 2.2.0, starlette 1.7.0, fastapi 0.142.2, uvicorn 0.54.0,
  cryptography 50.0.2, httpx2 2.13.1). Image
  `sha256:fc705da94716925264c316b99ccba695258635f4361895458de634ff933fd5de`.
- Configuration: `00517-l2d` carries the same environment-variable names,
  resources, concurrency and timeout as `00516-48g`. **No authentication gate
  variable is set**, so credential issuance and MCP enforcement both sit at
  their code default, which is off. `00518-pkp` differs from it only in the
  ambient-notice text.
- Post-deploy read-back (anonymous, paced, October 18, 04:21–04:24 UTC):
  20 of 20 — `/health` 0.5.66 with `protocol_version 2026-07-28`, Firestore
  connected, inference live, catalogue current; the server card agrees; the
  eight contained account routes answer the maintenance `503`; OAuth discovery
  served and the five endpoints dark; three handshake eras and the sessionless
  2026-07-28 era (`tools/list`, `server/discover`, `tools/call`) answer with no
  session header; `/terms` v2.6 and `/privacy` v2.7 dated October 15, 2026.
- Versioned smoke oracle (04:24–04:30 UTC): **48 pass / 0 stop / 0 instrument**
  against production, after a known-positive on local keyless servers of both
  trees — exactly the four version legs fired on the previous tree (v0.5.65)
  and every leg passed on the deployed tree. The typed BYOK failure contract
  held (invalid key → `BYOK_AUTH_FAILED` per stage, decision surface withheld).
- **Trinity, as observed: one anonymous run — X real, Z real, CS unavailable.**
  The Groq completion output for CS was truncated at its 3,775-token
  reservation (`PROVIDER_OUTPUT_TRUNCATED`); outcome `partial`, 36 s; the
  honest-degradation contract held (analysis marked incomplete, confidence
  withheld, recommendation capped, CS analysis block withheld, nothing written
  to history); no failover attempt. One run is not a reliability figure: the
  pre-merge smoke on this identical tree completed X/Z/CS real/real/real
  locally, and the Z/CS limitation recorded below is the standing condition,
  not a regression of this release.
- Ambient notice: refreshed at 04:33 UTC as the configuration-only revision
  `00518-pkp` (same image); every tool response now carries the v0.5.66 text.
- [GitHub Release v0.5.66](https://github.com/creator35lwb-web/VerifiMind-PEAS/releases/tag/v0.5.66)
  was published by the maintainer on October 18, 2026 at 05:08 UTC and
  triggered the MCP Registry publish (**3.43.0**, API-verified live and marked
  latest). The tag resolves to `623f0203`, the docs-only truth-conversion merge
  (#383) rather than the deployment merge itself; the two commits have an
  identical `mcp-server/` subtree and `server.json`, so the released source and
  the registry manifest are the deployed ones. The tag caused no build (the
  deploy trigger is path-filtered to runtime paths).

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

Each build ran from the exact `main` commit shown; `00504-c8d` was a
configuration-only revision on the existing image. The application version
stayed at 0.5.62 until `00508-dj8`, was 0.5.63 from `00508-dj8` through `00512-hgk`, was 0.5.64 from `00513-klm` through `00514-dnc`, was 0.5.65 from `00515-q9f` through `00516-48g`, and is 0.5.66 from `00517-l2d` on (`00518-pkp` is a configuration-only revision on the same image). PR #348
(`codeql-action` pins, `.github/` only) merged the same day and correctly
caused no build.

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
  required — it is never silently mocked. In our own post-deploy smokes this
  month this has been frequent, not rare: neither v0.5.63 smoke run completed
  in full, and the v0.5.64 pre-merge smoke saw CS fail on Groq on the same tree
  and on the previous framework; the single v0.5.64 post-deploy run completed
  with CS at 86% of its reservation; the single v0.5.66 post-deploy run did
  not complete (CS truncated at a 3,775-token reservation) while the pre-merge
  run on the identical tree did. The completion retry added in v0.5.60 covers provider rate-limit
  rejections that state a wait; a truncated or structurally incomplete answer
  is deliberately not retried, because a blind re-run inside the same
  reservation has no provider-guaranteed payoff. A structural fix — separate
  provider lanes for Z and CS, or a shorter CS output contract — is being
  investigated next and is not part of v0.5.63, v0.5.64, v0.5.65 or v0.5.66. BYOK callers can avoid the
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
- Runtime cross-provider failover remains disabled. The hosted routing shown
  above is construction-time routing, not request-time failover.
- No "vulnerability clean" claim is made for this release. The dependency audit
  is a strict, fail-closed `pip-audit` of the deployment project and reported 0
  known vulnerabilities on the day it ran; `mistralai` is still declared as a
  range (`>=1.0.0`), so that package is audited at whatever version resolves
  on the day.
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
