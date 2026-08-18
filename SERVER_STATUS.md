# VerifiMind-PEAS Server Status

**Last updated:** August 18, 2026

**Evidence cutoff:** v0.5.60 release verification completed August 18, 2026

**Status authority:** this dated operational snapshot; release history lives in
[`CHANGELOG.md`](CHANGELOG.md) and [GitHub Releases](https://github.com/creator35lwb-web/VerifiMind-PEAS/releases).

## Current production snapshot

| Surface | Verified state |
|---|---|
| Application | **v0.5.60**, verified by the release smoke described below |
| Public merge | [`41d3187672d7350b35b2f5084918db805971801c`](https://github.com/creator35lwb-web/VerifiMind-PEAS/commit/41d3187672d7350b35b2f5084918db805971801c) |
| Reviewed candidate | `1c2f56a67afc8f3c865a9956925e6f669d0b281e` (T TECHNICAL PASS after four exact-head review rounds, S135–S139) |
| Reviewed base | `d7396c71c65a3e2a15ae7fb441d646aaf4ec5a45` |
| Cloud Build | `d7dd84c2-053f-4e06-85d6-c0df5ad2d9cc` — **SUCCESS**, completed 2026-08-18T07:44Z, source bound to the merge SHA |
| Serving revision | **`verifimind-mcp-server-00494-qr9`** at 100% traffic |
| Rollback target | `d7396c71c65a3e2a15ae7fb441d646aaf4ec5a45` (v0.5.59 tree), captured and unused |
| MCP Registry package | **3.37.0** — publish workflow succeeded; live registry serves 3.37.0 with the v0.5.60 description |
| Tool inventory | **13 defined / 8 active / 5 temporarily unavailable** |
| Firestore | Connected during verified post-deploy health checks |
| Runtime failover | `runtime_failover_enabled: false` |
| Hosted X | Gemini `gemini-3.5-flash-lite` |
| Hosted Z | Groq `openai/gpt-oss-120b` |
| Hosted CS | Groq `openai/gpt-oss-120b` |
| Policies | Terms v2.4 / Privacy v2.5 |

## Release verification

- [Public PR #331](https://github.com/creator35lwb-web/VerifiMind-PEAS/pull/331)
  merged the exact T-reviewed head into the exact public base; no unreviewed
  product commit was included.
- Review chain at exact SHAs: four independent T review rounds (S135–S139),
  each contributing exact-head counterexamples now pinned by **eight
  discriminating regressions** (each set fails at its parent head and passes
  repaired). T TECHNICAL PASS at the merged head. Human merge and deployment
  authorization: recorded before execution.
- CI at the reviewed head: 10/10 checks; the production-image job proved
  Python 3.12.12 with exact pins and non-vacuous runtime receipts; the test
  job proved 1,248 passed / 3 skipped / 0 failed.
- Post-deploy smoke: every version surface (`/health`, server-card, `/mcp/`
  serverInfo) reports v0.5.60; `/health` is served with `Cache-Control:
  no-store`; live Trinity **X/Z/CS = real/real/real** with the quality gate
  passed and both token monitors (`_z_token_monitor`, `_cs_token_monitor`)
  reporting live values.
- **The completion retry executed in production during the smoke:** a
  rate-limited Z stage slept the provider-stated 7.5 seconds, re-executed,
  and recovered — disclosed in `_stage_retries` — while a CS truncation on
  the same run was correctly NOT retried (no provider-stated wait) and
  degraded honestly per-stage. Run-lifecycle events (`trinity_run_started` /
  `trinity_run_completed`, exactly once per run) are live: the production
  completion rate is measurable for the first time.
- [GitHub Release v0.5.60](https://github.com/creator35lwb-web/VerifiMind-PEAS/releases/tag/v0.5.60)
  resolves to the exact production merge and triggered the successful MCP
  Registry publish.

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
