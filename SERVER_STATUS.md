# VerifiMind-PEAS Server Status

**Last updated:** July 30, 2026
**Status authority:** current operational snapshot; release history lives in
[`CHANGELOG.md`](CHANGELOG.md) and GitHub Releases.

## Current production snapshot

- Production application version last verified by T: **v0.5.54**
- MCP protocol advertised by production: **2025-11-25**
- Tool inventory: **13 defined / 10 active / 3 temporarily unavailable**
- Contained tools:
  - `coordination_handoff_create`
  - `coordination_handoff_read`
  - `coordination_team_status`
- Containment reason: owner-scoped authentication and authorization are not yet
  implemented for coordination records.
- Containment behavior: fail closed for every credential shape; callers should
  preserve handoff state in their own private repository.
- Current paid services: **none**
- Registration: free UUID/cohort registration; not a time-limited access
  entitlement.

This status does not claim that every historical coordination record is safe,
that the incident has completed legal disposition, or that v0.5.55 is deployed.

## v0.5.55 release candidate

Branch: `t/integrated-v0.5.55-release`
Base: post-containment `main` at `a2cc98e`

Included:

- PR #309 discovery-parity hardening, repaired to cover the root registry
  manifest and duplicate occurrences.
- PR #310 Anthropic Claude 5 thinking-block and token-budget repair, completed
  for both documented truncation stop reasons.
- PR #312 containment-denial integrity repair.
- Cross-surface availability truth: 13 defined / 10 active / 3 unavailable.
- Registration and policy-surface truth repair.

Explicitly excluded:

- PR #311 Groq admission logic. The observed failures justify investigation,
  but not the submitted causal claim or an algorithm that can violate its own
  reservation invariant.
- MCP protocol 2026-07-28 support. This remains a separate compatibility lane.
- Re-enabling coordination tools. Re-enablement requires owner-scoped access
  control, migration handling, and adversarial authorization tests.

## Measured verification

| Gate | Result |
|---|---:|
| Focused security/truth/registration lane | 193 passed |
| Full unit suite | 990 passed, 3 skipped |
| Registration + integration suite | 86 passed, 11 skipped |
| Diff whitespace gate | Clean |
| Production deployment | Not performed |

The 11 skipped integration tests require live-service credentials or explicit
integration configuration; they are not counted as passes.

## Release gates still open

1. Human approval of the Terms v2.2 / Privacy v2.3 publication copy, with
   counsel review if required.
2. Independent CS security validation on the exact candidate head.
3. CI on the pushed exact head with no substitution of a nearby commit.
4. Pre-deploy secret scan and immutable build identity capture.
5. Controlled deployment followed by `/health`, discovery, registration,
   policy, and real-inference smoke checks.
6. Post-deploy evidence recorded back into the private Command Central Hub.

## Active follow-up lanes

- Design the authenticated, owner-scoped coordination replacement and data
  migration/retention plan.
- Diagnose Groq failures from provider evidence before changing admission
  arithmetic; preserve request privacy in diagnostics.
- Add MCP 2026-07-28 dual-version support without conflating it with this
  security release.
- Complete L/Manus publication verification for the landing source of truth.
- Compress governance principles into a smaller invariant set rather than
  extending release scope.

## Public endpoints

- MCP: `https://verifimind.ysenseai.org/mcp/`
- Health: `https://verifimind.ysenseai.org/health`
- Setup: `https://verifimind.ysenseai.org/setup`
- Register: `https://verifimind.ysenseai.org/register`
- Terms: `https://verifimind.ysenseai.org/terms`
- Privacy: `https://verifimind.ysenseai.org/privacy`

Endpoint availability alone is not release evidence; the response content and
declared execution semantics must also match the deployed behavior.
