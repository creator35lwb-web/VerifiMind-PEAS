# Architecture

> **Document boundary — textbook.** This page describes stable system boundaries. Mutable versions, providers, models, tool counts, and incident state live in [Current Production Status](Current-Production-Status).

VerifiMind PEAS is a human-directed validation system exposed through the Model Context Protocol (MCP). Its architecture separates the **method** used to reason, the **runtime** that executes tools, and the **evidence plane** that lets a release be checked after deployment.

## System view

```text
MCP client
   |
   v
Public MCP boundary ---- health / setup / policy surfaces
   |
   v
Tool registry and request controls
   |
   +---- built-in template reads
   |
   +---- Trinity orchestration
            |---- X: opportunity and critical analysis
            |---- Z: ethics and safety
            |---- CS: security
            `---- synthesis: completeness, disagreement, human-review state
                         |
                         v
                 structured response

Evidence plane: source SHA -> CI -> build -> deployment -> smoke -> release -> registry
```

The coordination subsystem is a separate trust domain. It is not required for Trinity validation and must not be treated as available merely because its tool definitions are discoverable.

## Architectural layers

### 1. MCP boundary

The public boundary accepts streamable HTTP MCP requests and exposes machine-readable discovery. Transport compatibility does not imply tool availability: clients must distinguish **defined**, **active**, and **temporarily unavailable** tools.

Request controls belong at this boundary, including input validation, rate limits, and non-enumerating error behavior. Health and setup endpoints are observability surfaces; they are not substitutes for a real tool invocation.

### 2. Tool registry

The registry describes the callable contract. A tool can remain defined while being unavailable so clients receive an explicit maintenance or containment response instead of a disappearing schema. Availability is a runtime fact and is recorded only in [Current Production Status](Current-Production-Status).

### 3. Trinity orchestration

The orchestration layer invokes X, Z, and CS as distinct analytical seats, preserves their provenance, and produces a synthesis. A seat is complete only when genuine inference succeeds. If a seat fails or returns unusable output:

- its generated score, confidence, verdict, and counts are withheld;
- successful seats can remain visible;
- the overall result is marked incomplete;
- the failing seat, provider, model, and typed failure are identified without leaking secrets; and
- the result is routed for human review.

An ethics veto remains semantically stronger than a numeric average.

### 4. Provider adapters and BYOK

Provider adapters normalize model invocation and failure categories. Default routes are deployment configuration, not architecture, and therefore live in the status page. Bring-your-own-key overrides are request-scoped inputs; their handling must follow the current Terms, Privacy Policy, and provider contract.

Provider diversity can reduce shared failure modes, but provider names alone do not prove independence. Model family, quota domain, request path, prompt construction, and fallback behavior all matter.

### 5. Synthesis and reporting

The synthesis layer must preserve uncertainty. It may summarize evidence, but it cannot convert a failed stage into a score or turn “no risk identified by this check” into “no risk exists.” Structured output should retain enough provenance for a reviewer to trace a conclusion back to a seat and its evidence.

### 6. Persistence

Persistence is opt-in and bounded by the public data contract. Incomplete Trinity runs must not enter shared validation history. Storage success or failure must be reported truthfully; an unavailable store cannot be represented as a successful write or deletion.

### 7. Coordination trust domain

Multi-agent coordination records have different authorization and ownership requirements from validation results. Coordination tool definitions may remain discoverable while their implementations are contained. Restoration requires owner-scoped access control, negative-path verification, and explicit authorization. See [Trust and Safety](Trust-and-Safety) and the public trust ledger.

## Deployment and evidence plane

The canonical release chain is:

```text
reviewed source commit
  -> exact-SHA CI and security gates
  -> immutable build identity
  -> production deployment
  -> live health, discovery, and real-inference smoke
  -> GitHub Release at the deployed SHA
  -> MCP Registry publication at that SHA
  -> production-status and trust-ledger update
```

Each arrow is an evidence boundary. A successful build does not prove the intended revision is serving; a healthy endpoint does not prove Trinity inference; a release tag does not prove registry publication. The [Operations Playbook](Operations-Playbook) defines the checks and stop conditions.

## Trust boundaries

| Boundary | Primary risk | Required control |
|---|---|---|
| Client to MCP service | malformed or abusive input | validation, rate limits, safe errors |
| Service to model provider | secret or prompt leakage, provider failure | scoped credentials, sanitized logs, typed failures |
| Seat to synthesis | false completeness | provenance and fail-closed field withholding |
| Runtime to persistence | unauthorized or misleading storage | consent, owner scope, bounded retention, truthful errors |
| Coordination caller to record | cross-owner disclosure or mutation | containment until owner-scoped authorization exists |
| Source to deployment | wrong bytes or mutable identity | exact-SHA build and deployment evidence |
| Deployment to public claim | stale or premature status | post-deploy verification and dated truth update |

## Canonical references

- [Genesis Methodology](Genesis-Methodology) — durable validation method
- [Current Production Status](Current-Production-Status) — mutable live snapshot
- [Operations Playbook](Operations-Playbook) — release and incident procedure
- [Trust and Safety](Trust-and-Safety) — trust contract and disclosure boundaries
- [Public Statements](Public-Statements) — append-only public record
- [Repository architecture diagram](https://github.com/creator35lwb-web/VerifiMind-PEAS/blob/main/docs/architecture/VerifiMind-PEAS-Architecture-Diagram.md) — detailed implementation diagrams
