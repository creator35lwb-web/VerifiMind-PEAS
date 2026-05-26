# GOVERNANCE

> **Version:** 1.0  
> **Effective:** 2026-05-26  
> **Applies to:** VerifiMind-PEAS (PUBLIC repository) and verifimind-genesis-mcp (PRIVATE Command Central Hub)

This document defines how decisions are made, who makes them, and how changes are proposed and ratified in the VerifiMind-PEAS project.

For *who maintains the project*, see [MAINTAINERS.md](MAINTAINERS.md). For *how to report security issues*, see [SECURITY.md](SECURITY.md).

---

## 1. Authority Model

VerifiMind-PEAS uses a **human-centric authority model** with delegated AI agent support. This is not a DAO, not a committee, and not a consensus-based governance. One human has final authority.

| Entity | Type | Authority | Scope |
|--------|------|-----------|-------|
| **Alton Lee Wei Bin** | Human | **Absolute** | All decisions, universal veto, strategic direction |
| **L (Godel)** | AI-Generated (GodelAI C-S-P) | Delegated | Strategic synthesis under Alton's delegation |
| **FLYWHEEL TEAM** | Multi-Agent Team | Advisory | Development, analysis, validation — no independent merge authority |
| **Co-Maintainers** | Human (future) | Scoped | Code review, release support within defined areas |

> **Identity Clarity (MACP v2.2):** Alton (Human Orchestrator) is NOT the same as L (Godel/CEO). Alton is human, always present since day one. L is an AI-generated entity that emerged via self-recursion during LegacyEvolve creation. L's authority is DELEGATED, not inherent. This distinction is maintained throughout all governance documents.

---

## 2. Decision Categories

| Category | Examples | Decision Maker | Process |
|----------|----------|---------------|---------|
| **Routine** | Bug fixes, documentation typos, dependency updates | Any maintainer | Merge directly |
| **Feature** | New tools, API changes, UI additions | Lead Maintainer or Co-Maintainer + review | PR + 1 approval |
| **Architecture** | Protocol changes, database schema, deployment model | Lead Maintainer | PR + AI Council review recommended |
| **Strategic** | Pricing, partnerships, pivots, public statements | Lead Maintainer (Alton) only | Deliberation + AI Council validation |
| **Governance** | Changes to THIS document, MAINTAINERS.md, authority model | Lead Maintainer (Alton) only | 7-day notice period |

---

## 3. Proposal Process

Anyone (human or AI agent) may propose a change. The process depends on the category:

**For Routine and Feature changes:**
1. Open a Pull Request with clear description
2. Request review from a maintainer
3. Address feedback
4. Maintainer merges when satisfied

**For Architecture and Strategic changes:**
1. Open a GitHub Discussion or Issue describing the proposal
2. Allow 48 hours for community input (if applicable)
3. Lead Maintainer reviews, optionally runs AI Council validation
4. Lead Maintainer decides (approve / reject / defer)
5. Decision is documented in `.macp/reasoning/` with rationale

**For Governance changes:**
1. Open a GitHub Discussion with the proposed change
2. 7-day notice period for community review
3. Lead Maintainer decides after notice period
4. Updated document is committed with changelog entry

---

## 4. AI Agent Governance

The FLYWHEEL TEAM operates under the Multi-Agent Communication Protocol (MACP v2.4.0). Key governance rules for AI agents:

- **No independent merge authority.** All AI-generated code requires human review before merge.
- **Triad compliance.** Strategic decisions must produce Memory + Reasoning + Handoff artifacts.
- **Circuit breaker.** 3 consecutive reasoning logs with no disagreement trigger human review.
- **Cross-Agent Canonical-Edit Protocol.** Agents may request edits to files outside their scope but must not make them unilaterally (request-don't-edit for B/C tier artifacts).
- **Escalation authority.** Z-Agent (Guardian) may flag for ethical review; XV (CIO) may flag for strategic re-review. Both are advisory to the Lead Maintainer's final decision.

---

## 5. Dual-Repo Protocol

VerifiMind-PEAS operates across two repositories:

| Repository | Visibility | Purpose |
|-----------|-----------|---------|
| `VerifiMind-PEAS` | PUBLIC | Production code, public governance, releases |
| `verifimind-genesis-mcp` | PRIVATE | Command Central Hub, agent coordination, sensitive reasoning |

**Sync rules:**
- Governance documents (GOVERNANCE.md, MAINTAINERS.md, SECURITY.md) are drafted in the PRIVATE Hub, reviewed by the CTO, then synced to the PUBLIC repo.
- Sensitive reasoning logs, agent memory, and internal handoffs remain PRIVATE.
- A sanitized `.macp-public/` folder in the PUBLIC repo provides exemplar evidence without exposing operational details.

---

## 6. Conflict Resolution

1. **Between AI agents:** The Lead Maintainer (Alton) resolves. If unavailable, T (CTO) provides interim recommendation.
2. **Between humans:** The Lead Maintainer's decision is final.
3. **Between community and maintainers:** The Lead Maintainer's decision is final, but must be documented with rationale.
4. **Ethical concerns:** Z-Agent (Guardian) flags are escalated to the Lead Maintainer immediately, regardless of other priorities.

---

## 7. Transparency Commitments

- All strategic decisions are documented with reasoning (MACP Triad).
- All AI agent contributions are attributed (Agent Attribution Map in thesis).
- All governance changes have a 7-day notice period.
- The project's metrics are reported honestly (EA Taxonomy: canonical/honest/registered).
- Limitations are acknowledged publicly (see Thesis §10: Limitations and Honest Gaps).

---

## 8. Amendments

Changes to this document require:
1. A 7-day notice period via GitHub Discussion
2. Lead Maintainer (Alton) approval
3. Version increment in the header
4. Commit message: `governance: update GOVERNANCE.md to vX.Y`

---

## 9. Contact

- **Lead Maintainer:** Alton Lee Wei Bin
- **GitHub:** [@creator35lwb-web](https://github.com/creator35lwb-web)
- **Email:** alton@ysenseai.org
- **Project:** [VerifiMind-PEAS](https://github.com/creator35lwb-web/VerifiMind-PEAS)

---

*Authored by T (CTO, Manus AI) under Alton's direction. MACP v2.4.0 compliant. Phase 90 "Adoption First" — M1 Governance.*
