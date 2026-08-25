# VerifiMind-PEAS Server Status

**Last updated:** August 26, 2026

**Evidence cutoff:** v0.5.62 release verification completed August 22, 2026 (18:09–18:15 UTC; deployment observed by T on August 21, 2026 13:09 UTC). Post-release maintenance verified through August 26, 2026 (see the maintenance note below).

**Status authority:** this dated operational snapshot; release history lives in
[`CHANGELOG.md`](CHANGELOG.md) and [GitHub Releases](https://github.com/creator35lwb-web/VerifiMind-PEAS/releases).

## Current production snapshot

| Surface | Verified state |
|---|---|
| Application | **v0.5.62**, verified by the release smoke described below |
| Public merge | [`b434979ea68da0a2326ad3f62dac30888b93dfcd`](https://github.com/creator35lwb-web/VerifiMind-PEAS/commit/b434979ea68da0a2326ad3f62dac30888b93dfcd) |
| Reviewed candidate | `73b3fe2049f1764437d278d43b68a6bbc3f89bcb` (T S144 EXACT-HEAD TECHNICAL PASS at `ff24dc1` + Alton-authorized identity commit, RNA S147; T S146 exact-head rebind PASS) |
| Reviewed base | `398700276c22230a9dc0a64ecd4196f43f921f07` |
| Cloud Build | `e3ca9551-0292-4b02-9cbf-0cc2b92daa3e` — **SUCCESS**, started 4s post-merge 2026-08-21, source bound to the merge SHA |
| Serving revision | **`verifimind-mcp-server-00503-rxh`** at 100% traffic (release revision `00496-g7s`; superseded by post-release maintenance — see note below) |
| Rollback target | `398700276c22230a9dc0a64ecd4196f43f921f07` (v0.5.61 tree), captured and unused |
| MCP Registry package | **3.39.0** — publish workflow succeeded on the v0.5.62 Release event; live registry API-verified serving 3.39.0 with the v0.5.62 description and the repaired em-dash/arrow tool descriptions (encoding defect healed) |
| Tool inventory | **13 defined / 8 active / 5 temporarily unavailable** |
| Firestore | Connected during verified post-deploy health checks |
| Runtime failover | `runtime_failover_enabled: false` |
| Hosted X | Gemini `gemini-3.5-flash-lite` |
| Hosted Z | Groq `openai/gpt-oss-120b` |
| Hosted CS | Groq `openai/gpt-oss-120b` |
| Policies | Terms v2.4 / Privacy v2.5 |

## Release verification

- [Public PR #340](https://github.com/creator35lwb-web/VerifiMind-PEAS/pull/340)
  merged the exact T-PASSED head into the exact public base; no unreviewed
  product commit was included.
- Chain at exact SHAs: T S142 observability review → T S144 CodeQL cleanup
  **EXACT-HEAD TECHNICAL PASS at `ff24dc1`** → Alton's bounded identity
  authorization → RNA-executed identity commit `73b3fe2` (runtime 0.5.62,
  Registry 3.39.0, four double-encoded `server.json` tool descriptions
  repaired) → T S146 exact-head rebind PASS → human merge and auto-deploy.
  Observability additions only; no hosted routing, failover-policy, provider
  catalogue, or dependency change.
- Gates at the reviewed head: all hosted CI checks passed; docs contract
  280 checks; unit suite 1,179 passed / 2 skipped / 0 failed (T's independent
  replay: 1,178 passed / 3 explained skips, 83 registration, 280 doc checks).
- Post-deploy smoke: `/health` 0.5.62 with `Cache-Control: no-store`; live
  Trinity **X/Z/CS = real/real/real** through a raw Streamable-HTTP JSON-RPC
  session, quality gate passed, no degraded agents. The new observability
  produced its first production receipts: `tool_invoked` events live in
  structured logs (17 in the first 48 hours), and the CS monitor reported
  89.5% utilization of a **3,708-token effective completion reservation**
  (`configured_ceiling` 8,192, `ceiling_source:
  provider_completion_reservation`) — the previously invisible admission
  clamp, now measured.
- [GitHub Release v0.5.62](https://github.com/creator35lwb-web/VerifiMind-PEAS/releases/tag/v0.5.62)
  resolves to the exact production merge and triggered the successful MCP
  Registry publish (3.39.0, API-verified).

## Post-release maintenance (August 25–26, 2026)

Release identity is unchanged: v0.5.62 at merge `b434979e`. Two bounded
maintenance events advanced the serving revision without any application-code,
routing, policy, or version change:

- **Credential hardening (2026-08-25):** all secret configuration was migrated
  from plaintext environment variables to **Google Secret Manager references**
  (config revisions `00500`–`00502`, same release image), prior credentials
  were revoked at their providers, and one retired legacy variable was removed
  entirely. Each rotated credential was proven by a live real-inference run
  before the old one was revoked; the post-rotation Trinity smoke returned
  **X/Z/CS = real/real/real** with the quality gate passed. No secret values
  appear in any repository, log, or transcript.
- **Dependency maintenance (2026-08-25):** [PR #342](https://github.com/creator35lwb-web/VerifiMind-PEAS/pull/342)
  (Uvicorn `0.52.3` → `0.52.4`) merged as `158f9e0` and auto-deployed via
  Cloud Build `103ef552-dc05-42c0-9a79-d96f7ae31e92` to serving revision
  **`00503-rxh`** (healthy restart 16:53 UTC, v0.5.62 unchanged).
  [PR #343](https://github.com/creator35lwb-web/VerifiMind-PEAS/pull/343)
  touched `.github/**` only and correctly caused no deployment.

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

## Known limitations and follow-up

- Coordination and custom-template mutation remain contained, not restored.
- Runtime cross-provider failover remains disabled. The hosted routing shown
  above is construction-time routing, not request-time failover.
- CS output truncation remains an intermittent hosted-provider behavior
  (~1 event/day baseline); it is now instrumented (`_cs_token_monitor`) and
  deliberately not auto-retried (no provider-stated wait). Structural
  mitigation is tracked with the provider-split decision.
- No "vulnerability clean" claim is made for this release: the Safety CI job
  is advisory (`|| true`) and skipped possible matches under unpinned
  `mistralai>=1.0.0`. Dependency-security policy modernization is separate
  follow-up.
- `safe_diagnostic_value` is a character-bounding helper, not a general secret
  redactor; renaming/documentation remains follow-up work.
- The `server.json` registry manifest carries pre-existing double-encoded
  em-dash characters in four tool descriptions; a bounded cleanup is planned
  with the next registry-version change.
- Qualified-counsel review and any retrospective incident-notification decision
  remain parallel human/legal work. Software verification does not close them.

## Public endpoints

- MCP: `https://verifimind.ysenseai.org/mcp/`
- Health: `https://verifimind.ysenseai.org/health`
- Discovery: `https://verifimind.ysenseai.org/.well-known/mcp-config`
- Setup: `https://verifimind.ysenseai.org/setup`
- Register: `https://verifimind.ysenseai.org/register`
- Terms: `https://verifimind.ysenseai.org/terms`
- Privacy: `https://verifimind.ysenseai.org/privacy`
- Public statements: `https://github.com/creator35lwb-web/VerifiMind-PEAS/wiki/Public-Statements`
