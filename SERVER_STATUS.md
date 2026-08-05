# VerifiMind-PEAS Server Status

**Last updated:** August 1, 2026
**Status authority:** current operational snapshot; release history lives in
[`CHANGELOG.md`](CHANGELOG.md) and GitHub Releases.

## Current production snapshot

- Production application version verified by T: **v0.5.55**
- MCP protocol advertised by production: **2025-11-25**
- Tool inventory reported by production: **13 defined / 10 active / 3 temporarily unavailable**
- Contained production tools:
  - `coordination_handoff_create`
  - `coordination_handoff_read`
  - `coordination_team_status`
- Production still exposes the two custom-template mutation tools. Their
  containment is the critical v0.5.56 change and is not yet deployed.
- Hosted routing reported by production:
  - X: Gemini `gemini-3.5-flash-lite`
  - Z: Groq `openai/gpt-oss-120b`
  - CS: Groq `openai/gpt-oss-120b`
- Current paid services: **none**
- Registration: free UUID/cohort registration; not a time-limited access
  entitlement.

Endpoint availability alone is not release evidence. Production v0.5.55 is
healthy, but its custom-template mutation exposure and incomplete Trinity
quality semantics remain the reasons for this bounded candidate.

## v0.5.56 release candidate

Branch: `agent/v0556-core-integrity-containment`
Base: production-aligned `main` at `dd78cbe`

Included:

- X/Z/CS-symmetric fail-closed quality gating for Trinity and standalone tools.
- Null/withheld scores, verdict state, confidence, recommendations, and
  reasoning for every degraded required stage.
- No propagation or history persistence of schema-generated degraded output.
- Explicit missing/null schema-repair diagnostics and Z evidence completeness
  checks.
- Groq token-ceiling completion guard.
- Fail-closed custom-template registration and URL import; built-in-only public
  template reads.
- Dormant URL-import hardening: strict GitHub HTTPS allowlist, public DNS
  addresses, no redirects, TLS 1.2+, timeout, response-size cap, and UTF-8.
- Canonical public availability: **13 defined / 8 active / 5 unavailable**.
- Terms v2.3, Privacy v2.4, registration, discovery, changelog, README, and MCP
  Registry parity.
- Raw provider-output logging removed from diagnostics.

Explicitly excluded:

- Re-enabling coordination or custom-template mutation tools.
- MCP protocol 2026-07-28 support; that remains a separate compatibility lane.
- Production deployment or external announcement before exact-head RNA review
  and human authorization.

## Measured verification

| Gate | Result |
|---|---:|
| Focused integrity/containment/reporting lane | 75 passed |
| Full unit suite | 1055 passed, 3 skipped |
| Registration and policy suite | 79 passed |
| Integration suite | 7 passed, 11 environment-gated skips |
| Full Python server Bandit scan | 0 findings |
| Diff whitespace gate | Clean |
| Production deployment | Not performed |

The 11 skipped integration tests require live-service credentials or explicit
integration configuration; they are not counted as passes. The unit skips are
existing optional-provider conditions.

## Release gates still open

1. Push the bounded candidate and bind review to its exact commit.
2. RNA (CSO) independent security review of the exact draft-PR head.
3. GitHub CI and security checks on that same head.
4. Human approval of Terms v2.3 / Privacy v2.4 publication copy, with counsel
   review if required.
5. Human merge and deployment authorization.
6. Post-deploy `/health`, discovery, registration, policies, template
   containment, and real-inference Trinity smoke checks.
7. Record immutable deployment evidence back into the private Command Central
   Hub before any public announcement.

## Active follow-up lanes

- Build authenticated, owner-scoped coordination and custom-template storage,
  including migration, retention, and adversarial authorization tests.
- Add MCP 2026-07-28 dual-version support without coupling it to this security
  release.
- Validate real X/Z/CS inference quality after deployment, including forced
  fallback and truncation cases.
- Complete L/Manus publication verification for the landing source of truth.
- Compress governance principles into a smaller invariant set rather than
  extending release scope.

## Public endpoints

- MCP: `https://verifimind.ysenseai.org/mcp/`
- Health: `https://verifimind.ysenseai.org/health`
- Discovery: `https://verifimind.ysenseai.org/.well-known/mcp-config`
- Setup: `https://verifimind.ysenseai.org/setup`
- Register: `https://verifimind.ysenseai.org/register`
- Terms: `https://verifimind.ysenseai.org/terms`
- Privacy: `https://verifimind.ysenseai.org/privacy`
