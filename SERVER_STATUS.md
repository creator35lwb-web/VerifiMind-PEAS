# VerifiMind-PEAS Server Status

**Last updated:** August 10, 2026

**Evidence cutoff:** v0.5.58 release verification completed August 7, 2026

**Status authority:** this dated operational snapshot; release history lives in
[`CHANGELOG.md`](CHANGELOG.md) and [GitHub Releases](https://github.com/creator35lwb-web/VerifiMind-PEAS/releases).

## Current production snapshot

| Surface | Verified state |
|---|---|
| Application | **v0.5.58**, verified by the release smoke described below |
| Public merge | [`3019f5c4889d8334063d4a2d9243e87d96fc93a8`](https://github.com/creator35lwb-web/VerifiMind-PEAS/commit/3019f5c4889d8334063d4a2d9243e87d96fc93a8) |
| Reviewed candidate | `67815f7bbf2070af68bdf14bea76b2b14c4d2f42` |
| Reviewed base | `08f136c7faaeb3150d2c399ee7fee0d7e74fe2de` |
| Cloud Build | `be6ed621-c0b8-49a3-a9f3-7ba36e68c7ea` — **SUCCESS**, completed 2026-08-07T20:35:03Z |
| Serving revision | **Not captured in the public v0.5.58 provenance record; no revision is inferred here** |
| Rollback target | `08f136c7faaeb3150d2c399ee7fee0d7e74fe2de`, captured and unused |
| MCP Registry package | **3.35.0** |
| Tool inventory | **13 defined / 8 active / 5 temporarily unavailable** |
| Firestore | Connected during verified post-deploy health checks |
| Runtime failover | `runtime_failover_enabled: false` |
| Hosted X | Gemini `gemini-3.5-flash-lite` |
| Hosted Z | Groq `openai/gpt-oss-120b` |
| Hosted CS | Groq `openai/gpt-oss-120b` |
| Policies | Terms v2.4 / Privacy v2.5 |

## Release verification

- [Public PR #324](https://github.com/creator35lwb-web/VerifiMind-PEAS/pull/324)
  merged the exact reviewed head into the exact reviewed base; no unreviewed
  product commit was included.
- T automation: **9/9 remote checks passed** at the unchanged reviewed head.
- RNA security review: **PASS**.
- Independent CS run 6: **PASS**, including simultaneous X/Z/CS failure and
  all-provider exception-propagation checks.
- Human merge and deployment authorization: recorded before execution.
- Post-deploy smoke: **31 pass / 0 stop / 0 instrument**.
- [GitHub Release v0.5.58](https://github.com/creator35lwb-web/VerifiMind-PEAS/releases/tag/v0.5.58)
  resolves to the exact production merge.

The real-inference smoke encountered an unforced X-stage failure while Z and CS
completed. Production preserved both successful stages, marked X unavailable,
withheld aggregate confidence, and returned an honestly incomplete result. This
is direct operational evidence for v0.5.58's per-stage degradation contract.

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
- `safe_diagnostic_value` is a character-bounding helper, not a general secret
  redactor. Current structured-error call sites pass controlled identifiers;
  renaming/documentation or true redaction remains follow-up work.
- The public release evidence does not contain a serving revision identifier.
  The merge, build, health, release tag, and smoke identities above are the
  available public provenance.
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
