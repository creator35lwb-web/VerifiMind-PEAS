# Roadmap

> **Document boundary — plans and evidence gates.** A roadmap item is not a shipped feature, a release promise, or evidence of current production state. Completed work must be proven by release and deployment evidence and then reflected in [Current Production Status](Current-Production-Status).

VerifiMind PEAS follows two related but different tracks:

1. the **Evaluation Roadmap**, a pre-registered research plan; and
2. the **product and operations backlog**, which responds to production evidence and safety obligations.

Keeping those tracks separate prevents a planned research milestone from being mistaken for a product release.

## Status vocabulary

| Label | Meaning |
|---|---|
| **Proposed** | Under discussion; no commitment or implementation claim |
| **Planned** | Accepted direction with a named evidence gate; schedule may change |
| **In progress** | Work exists on a branch or in a review; not live |
| **Released** | Tagged source exists at an exact commit |
| **Deployed** | The exact released source is verified in production |
| **Verified** | Required post-deploy and research evidence passed |
| **Deferred / stopped** | Work intentionally paused or ended, with rationale recorded |

“Merged,” “released,” “deployed,” and “verified” are different states. Use the narrowest one supported by evidence.

## Evaluation Roadmap v1.0

The canonical research plan is [Evaluation Roadmap v1.0](https://verifimind.ysenseai.org/research/evaluation-roadmap), bound by the [`roadmap-v1.0`](https://github.com/creator35lwb-web/VerifiMind-PEAS/releases/tag/roadmap-v1.0) tag. Its published year-one window is May 2026 through April 2027.

| Milestone | Published target | Evidence objective |
|---|---|---|
| M0 | May 2026 | Publish and bind the roadmap |
| M1 | June 2026 | Establish governance and co-maintainer pathway |
| M2 | July 2026 | Publish a seed labeled evaluation set |
| M3 | September 2026 | Report inter-rater and repeatability agreement with uncertainty |
| M4 | October 2026 | Onboard a co-maintainer or publish a concession and retrospective |
| M5 | November 2026 | Demonstrate a restricted CS execution sandbox and threat model |
| M6 | January 2027 | Report Z calibration and abstention quality |
| M7 | February 2027 | Run a readiness-gated external benchmark |
| M8 | March 2027 | Publish a NIST AI RMF self-attestation with external critique |
| M9 | April 2027 | Publish the year-one retrospective and continue/pivot/sunset decision |

The dates above are the plan as published, not an assertion that a milestone was completed. The canonical roadmap and its evidence artifacts determine status. Missed targets and failed thresholds should be reported in the same format as successful ones.

## Current evidence gates

These are durable priorities derived from the project’s present trust obligations. They are not promises of a particular version or date.

### Coordination restoration

The coordination incident `VM-IR-2026-07-28-COORD-01` is **contained, not closed**. Restoration remains blocked until there is:

- owner-scoped authorization for every read and write;
- negative-path tests from unauthorized and anonymous callers;
- migration and deletion handling for existing records;
- logging sufficient to investigate future access; and
- separate human authorization to restore the tools.

Containment, legal review, notification analysis, technical remediation, and closure are separate gates.

### Trinity independence and resilience

The architecture needs evidence that its analytical seats do not share avoidable failure modes. Work in this area should measure:

- provider and model-family diversity;
- quota and outage correlation;
- behavior when one, two, or all three seats fail;
- false-completeness resistance; and
- whether any failover preserves provenance and safety semantics.

Runtime failover must never be inferred from the existence of failover code; its enabled state is a production fact.

### Release truth automation

The release process should mechanically bind source SHA, CI, build, serving revision, smoke, GitHub Release, registry publication, and the public status update. A missing link is a release-record defect even when the service is healthy.

### Evaluation quality

Engagement measures are useful operating signals but do not validate correctness. Product claims should advance through labeled datasets, reproducible comparisons, calibration, disagreement analysis, and external critique under the Evaluation Roadmap.

## Change rules

1. Put volatile facts in [Current Production Status](Current-Production-Status), not here.
2. Link every “released” or “verified” claim to exact evidence.
3. Keep research targets distinguishable from product delivery.
4. Record deferrals, failed gates, and changed assumptions rather than rewriting history.
5. Do not assign a release number until scope and evidence gates are authorized.
6. Update public claims only after production verification, never from a candidate branch.

## Related records

- [Operations Playbook](Operations-Playbook) — release and incident gates
- [Trust and Safety](Trust-and-Safety) — standing obligations
- [Metrics Evidence Register](Metrics-Dashboard) — dated measurements, not roadmap completion proof
- [Public Statements](Public-Statements) — append-only disclosures
- [Publications](Publications) — immutable research and protocol records
