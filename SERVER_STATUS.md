# VerifiMind-PEAS Server Status

**Last updated:** August 6, 2026
**Status authority:** current operational snapshot; release history lives in
[`CHANGELOG.md`](CHANGELOG.md) and [GitHub Releases](https://github.com/creator35lwb-web/VerifiMind-PEAS/releases).

## Current production snapshot

- Production application version: **v0.5.56**
- Source commit: **`40a489245702d2db23b2d1f6fd8eb124e33c0f15`** (PR #315)
- Cloud Build: **`28db0855-cb06-4802-b952-75623318345f`** — successful
- MCP protocol advertised by production: **2025-11-25**
- Tool inventory: **13 defined / 8 active / 5 temporarily unavailable**
- Temporarily unavailable:
  - `coordination_handoff_create`
  - `coordination_handoff_read`
  - `coordination_team_status`
  - `register_custom_template`
  - `import_template_from_url`
- Firestore: connected at the verified deployment smoke
- Runtime provider failover: disabled and disclosed
- Hosted routing:
  - X: Gemini `gemini-3.5-flash-lite`
  - Z: Groq `openai/gpt-oss-120b`
  - CS: Groq `openai/gpt-oss-120b`
- Current paid services: **none**
- Registration: free UUID/cohort registration; not a time-limited entitlement
- Live policies: Terms v2.3 and Privacy v2.4

Post-deploy verification completed with **24 pass / 0 stop / 0 instrument**,
including a real X-Z-CS chain in which all three stages reported real inference.
This is operational evidence, not a legal certification or an incident-closure
claim.

## Release publication

- [v0.5.55 — Integrated Security and Public-Truth Repair](https://github.com/creator35lwb-web/VerifiMind-PEAS/releases/tag/v0.5.55)
  is bound to merge commit `dd78cbe4ce05d57fdd3978a5ea1b4dda55b2826f`.
- [v0.5.56 — Core Integrity, Containment, and Legal Truth](https://github.com/creator35lwb-web/VerifiMind-PEAS/releases/tag/v0.5.56)
  is bound to merge commit `40a489245702d2db23b2d1f6fd8eb124e33c0f15`
  and is the latest GitHub Release.

The two missing release records were restored on August 6, 2026. Creating those
records did not merge code or trigger a deployment.

## v0.5.57 release candidate (not deployed)

The bounded post-release reliability lane contains:

- MCP Registry description shortened below the 100-character hard limit.
- Discovery-card prompt resource renamed from stale `v4.2` copy to the live
  production-methodology identity.
- Firestore opt-out read/write failures normalized to a structured,
  non-enumerating HTTP 503 without false deletion success.
- Opt-in shared history capped at the 20 newest entries, pruned on every
  read/write, cleared on instance replacement, and reported truthfully when a
  write fails.
- Terms v2.4 / Privacy v2.5 wording that describes the enforced entry-bound
  retention contract; human/RNA review remains required before publication.
- Dead duplicate Privacy/Terms HTML bodies removed so canonical policy modules
  are the only served legal-text source.

The private Command Central Gate #1 provenance repair is isolated separately in
private draft PR #82. It requires an explicit canonical public checkout, full
expected SHA, matching origin/root/HEAD, and a clean worktree.

## Gates before v0.5.57 can merge or deploy

1. Complete local unit, integration, security, and canonical-currency gates.
2. Publish the bounded public change as a draft PR tied to one exact SHA.
3. Obtain RNA/security review of that exact head.
4. Obtain human approval of Terms v2.4 / Privacy v2.5 publication wording, with qualified
   counsel review where appropriate.
5. Resolve or explicitly hold the nine-PR backlog without bulk-merging stale or
   failing branches.
6. Obtain separate human merge/deployment authorization.
7. After deployment, verify health, discovery, policy, opt-out failure behavior,
   bounded history, registry publication, and real-inference Trinity behavior.

## Known limitations and follow-up lanes

- Coordination and custom-template mutation remain contained, not restored.
- Owner-scoped persistence, migration, and deletion remain separate design work.
- MCP 2026-07-28 dual-version support remains a compatibility lane.
- Runtime cross-provider failover remains disabled.
- Counsel review and any retrospective incident-notification decision remain
  parallel human/legal work and are not closed by software tests.

## Public endpoints

- MCP: `https://verifimind.ysenseai.org/mcp/`
- Health: `https://verifimind.ysenseai.org/health`
- Discovery: `https://verifimind.ysenseai.org/.well-known/mcp-config`
- Setup: `https://verifimind.ysenseai.org/setup`
- Register: `https://verifimind.ysenseai.org/register`
- Terms: `https://verifimind.ysenseai.org/terms`
- Privacy: `https://verifimind.ysenseai.org/privacy`
