# VerifiMind-PEAS Server Status

**Last updated:** August 19, 2026

**Evidence cutoff:** v0.5.61 release verification completed August 18, 2026 (21:02–21:50 UTC)

**Status authority:** this dated operational snapshot; release history lives in
[`CHANGELOG.md`](CHANGELOG.md) and [GitHub Releases](https://github.com/creator35lwb-web/VerifiMind-PEAS/releases).

## Current production snapshot

| Surface | Verified state |
|---|---|
| Application | **v0.5.61**, verified by the release smoke described below |
| Public merge | [`ba02fd0262ff91fb9452d2f025ee7e7cb7c59fea`](https://github.com/creator35lwb-web/VerifiMind-PEAS/commit/ba02fd0262ff91fb9452d2f025ee7e7cb7c59fea) |
| Reviewed candidate | `fa6a35aafc2f4c9e7a33aa8f4ccfca9a3fe9a1ae` (T TECHNICAL RELEASE PASS, S141 — identity executed by T on Alton's bounded authorization) |
| Reviewed base | `f289f2796da1f7ed95fcf72a1abdd25d57f63c63` |
| Cloud Build | `82444203-10d0-4e79-a11b-f8d7ce3ecc76` — **SUCCESS**, completed 2026-08-18T21:02Z, source bound to the merge SHA |
| Serving revision | **`verifimind-mcp-server-00495-whr`** at 100% traffic |
| Rollback target | `f289f2796da1f7ed95fcf72a1abdd25d57f63c63` (v0.5.60 tree), captured and unused |
| MCP Registry package | **3.38.0** — publish workflow succeeded; live registry serves 3.38.0 with the v0.5.61 description |
| Tool inventory | **13 defined / 8 active / 5 temporarily unavailable** |
| Firestore | Connected during verified post-deploy health checks |
| Runtime failover | `runtime_failover_enabled: false` |
| Hosted X | Gemini `gemini-3.5-flash-lite` |
| Hosted Z | Groq `openai/gpt-oss-120b` |
| Hosted CS | Groq `openai/gpt-oss-120b` |
| Policies | Terms v2.4 / Privacy v2.5 |

## Release verification

- [Public PR #338](https://github.com/creator35lwb-web/VerifiMind-PEAS/pull/338)
  merged the exact T-PASSED head into the exact public base; no unreviewed
  product commit was included.
- Chain at exact SHAs: RNA current-main rebind (`27d76b3`, receipts bound to
  synthetic `8750ec74`) → T acceptance of the dependency graph → Alton's
  bounded identity authorization → T-executed identity commit → **T TECHNICAL
  RELEASE PASS at `fa6a35aa`** → human merge and deployment by the project
  owner. Framework deltas only (FastMCP 3.4.7, Starlette 1.6.0, Uvicorn
  0.52.3); no VerifiMind application code or policy changed.
- CI at the reviewed head: 10/10 checks; production-image job proved Python
  3.12.12 with 7/7 exact in-image pins and non-vacuous runtime receipts; test
  job proved `pip check` clean, 7/7 installed pins, 1,248 passed / 3 skipped /
  0 failed.
- Post-deploy smoke: `/health` 0.5.61 with `Cache-Control: no-store`; live
  Trinity **X/Z/CS = real/real/real** with the quality gate passed and both
  token monitors live. An earlier smoke leg recorded the completion retry's
  **second production recovery** (rate-limited Z, provider-stated 4.5s wait,
  recovered) and one CS truncation at the known ~1/day intermittent rate,
  correctly not retried.
- [GitHub Release v0.5.61](https://github.com/creator35lwb-web/VerifiMind-PEAS/releases/tag/v0.5.61)
  resolves to the exact production merge and triggered the successful MCP
  Registry publish (3.38.0, API-verified).

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
