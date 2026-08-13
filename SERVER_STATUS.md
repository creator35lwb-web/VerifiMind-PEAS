# VerifiMind-PEAS Server Status

**Last updated:** August 13, 2026

**Evidence cutoff:** v0.5.59 release verification completed August 13, 2026

**Status authority:** this dated operational snapshot; release history lives in
[`CHANGELOG.md`](CHANGELOG.md) and [GitHub Releases](https://github.com/creator35lwb-web/VerifiMind-PEAS/releases).

## Current production snapshot

| Surface | Verified state |
|---|---|
| Application | **v0.5.59**, verified by the release smoke described below |
| Public merge | [`505951fe663aec4df2cd0b1d984ca04d4fc8f55a`](https://github.com/creator35lwb-web/VerifiMind-PEAS/commit/505951fe663aec4df2cd0b1d984ca04d4fc8f55a) |
| Reviewed candidate | `fd661e33776bde3db7f24c3d6400b5ad6b2b018c` (T S134 TECHNICAL RELEASE PASS bound to this exact head) |
| Reviewed base | `fbcdd9737b079daabf4a18548fe15e252a828b16` |
| Cloud Build | `2a4a666c-ef70-4e10-92a2-7eb478fd3d69` — **SUCCESS**, completed 2026-08-13T15:00Z, source bound to the merge SHA |
| Serving revision | **`verifimind-mcp-server-00493-rj2`** at 100% traffic — captured in public provenance, closing the v0.5.58 gap |
| Rollback target | `fbcdd9737b079daabf4a18548fe15e252a828b16` (v0.5.58 tree), captured and unused |
| MCP Registry package | **3.36.0** — publish workflow succeeded and the live registry serves 3.36.0 with the v0.5.59 description |
| Tool inventory | **13 defined / 8 active / 5 temporarily unavailable** |
| Firestore | Connected during verified post-deploy health checks |
| Runtime failover | `runtime_failover_enabled: false` |
| Hosted X | Gemini `gemini-3.5-flash-lite` |
| Hosted Z | Groq `openai/gpt-oss-120b` |
| Hosted CS | Groq `openai/gpt-oss-120b` |
| Policies | Terms v2.4 / Privacy v2.5 |

## Release verification

- [Public PR #329](https://github.com/creator35lwb-web/VerifiMind-PEAS/pull/329)
  merged the exact T-reviewed head into the exact public base; no unreviewed
  product commit was included.
- Review chain at exact SHAs: T S130 HOLD (dependency authority) → repaired;
  T S132 HOLD (delivery-layer vacuity) → repaired with mandatory runtime
  receipts; T S133 TECHNICAL PASS; T S134 TECHNICAL RELEASE PASS at the merged
  head. Human merge and deployment authorization: recorded before execution.
- CI at the reviewed head: 10/10 checks; the production-image job proved
  Python 3.12.12 and 7/7 `declared == in-image` pins with non-vacuous runtime
  receipts; the test job proved `pip check` clean, 7/7 installed pins, and
  1,207 passed / 3 skipped / 0 failed.
- Post-deploy smoke: every version surface (`/health`, server-card, `/mcp/`
  serverInfo, root) reports v0.5.59; live Trinity **X/Z/CS = real/real/real**
  with the quality gate passed.
- [GitHub Release v0.5.59](https://github.com/creator35lwb-web/VerifiMind-PEAS/releases/tag/v0.5.59)
  resolves to the exact production merge and triggered the successful MCP
  Registry publish.

An initial post-deploy Trinity attempt was rate-limited on the shared hosted
Z/CS provider and returned an honestly degraded partial: typed
`PROVIDER_RATE_LIMITED` stage errors with populated `retry_after_seconds`,
aggregate confidence withheld, recommendation capped, and the completed X stage
preserved. The retry after the advertised window completed real/real/real.
This is direct operational evidence that the per-stage degradation contract
introduced in v0.5.58 survived the v0.5.59 dependency upgrades intact.

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
- No "vulnerability clean" claim is made for this release: the Safety CI job is
  advisory (`|| true`) and its deprecated command skipped possible matches
  under unpinned `mistralai>=1.0.0`. Dependency-security policy modernization
  is routed as separate follow-up.
- `safe_diagnostic_value` is a character-bounding helper, not a general secret
  redactor. Current structured-error call sites pass controlled identifiers;
  renaming/documentation or true redaction remains follow-up work.
- The `server.json` registry manifest carries pre-existing double-encoded
  em-dash characters in four tool descriptions; a bounded cleanup is planned
  separately from release changes.
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
