# Trust and Safety

> **Document boundary — trust contract.** This page states durable safety commitments and the status language used when those commitments fail. Dated disclosures live in [Public Statements](Public-Statements); mutable runtime facts live in [Current Production Status](Current-Production-Status).

VerifiMind PEAS is designed to make the limits of AI-assisted validation visible. Trust is not a badge or a score. It is the ability to inspect what ran, what failed, what evidence supports a claim, and who remains accountable.

## Standing commitments

### Human accountability

AI agents provide structured decision support. A human owns the decision, the deployment, and any real-world consequences. VerifiMind output is not legal, medical, financial, security, or regulatory certification.

### No false completeness

When a Trinity seat does not produce genuine inference:

- its generated findings, score, confidence, verdict, and derived counts are withheld;
- the failed seat and typed failure are named;
- successful seats may be retained with provenance;
- the overall result is marked incomplete; and
- human review is required.

A summary must not contradict a risk listed in its own analysis. “No risk identified by this check” must never be rewritten as “no risk exists.”

### Veto preservation

A trusted Z ethics veto is not averaged away by favorable numeric scores. Disagreement is evidence and remains visible to the decision owner.

### Honest availability

Defined tools, active tools, and temporarily unavailable tools are different states. Unavailable functions remain clearly reported and return a safe denial or maintenance response. They are not marketed as operational.

### Evidence before claims

Release, deployment, smoke, registry, and incident claims require their own evidence. A healthy endpoint does not prove real inference, and containment does not prove incident closure.

### Minimal and truthful logging

Provider failure logs must carry enough information to diagnose the failure without recording API keys, provider response bodies, or account metadata. Inability to correlate logs is reported as an evidence limitation, not converted into a finding that no access occurred.

## Current standing disclosure: COORD-01

Incident `VM-IR-2026-07-28-COORD-01` is **CONTAINED, NOT CLOSED**.

The three coordination tools remain unavailable:

- `coordination_handoff_create`
- `coordination_handoff_read`
- `coordination_team_status`

The vulnerable code paths were removed from callable operation and anonymous containment behavior was verified. That does **not** establish that no unauthorized access occurred. Historical request logs and tool telemetry could not be correlated sufficiently to determine what was read.

Restoration requires owner-scoped access control, adversarial authorization tests, adequate audit logging, independent verification, and explicit human authorization. Statutory-notification and other legal questions remain a separate counsel-led track and are not represented as resolved here.

The canonical dated disclosure is [Public Statements](Public-Statements). Corrections belong there as dated addenda, never as silent rewrites.

## Other unavailable capabilities

Custom-template registration and URL import remain unavailable while owner-scoped storage and URL-fetch protections are completed. Their exact names and the current total availability contract are recorded in [Current Production Status](Current-Production-Status).

## Provider and model safety

Provider-backed inference introduces changing model catalogs, quotas, outages, authentication failures, and shared failure domains. The system must:

- identify the provider and model used by each seat;
- classify rate limit, truncation, timeout, and authentication failures accurately;
- avoid logging secret or provider response content;
- reject retired defaults through currency gates;
- preserve partial successful analysis without manufacturing completeness; and
- disclose whether runtime failover is enabled.

Multiple named agents are not automatically independent. Any claim of model diversity should state provider, model family, quota/failure domain, and observation date.

## Data and privacy boundary

Use the live [Terms](https://verifimind.ysenseai.org/terms) and [Privacy Policy](https://verifimind.ysenseai.org/privacy) for the operative public data contract. Wiki summaries do not override them.

Standing engineering rules include:

- consent before optional identity-linked persistence;
- bounded history and truthful storage/deletion outcomes;
- no persistence of incomplete Trinity runs;
- non-enumerating responses for account or record operations;
- server-side request forgery controls for any URL fetch; and
- private channels for access, correction, deletion, and security reports.

Do not put credentials, provider keys, personal data, or incident-subject details in public issues, logs, examples, or statements.

## Responsible reporting

Report security or privacy concerns privately to **alton@ysenseai.org**. Include only the minimum reproduction detail needed; do not include third-party personal data or live secrets.

Public disclosure follows these rules:

1. state what is observed and what remains unknown;
2. distinguish containment, remediation, restoration, and closure;
3. avoid legal conclusions without qualified counsel;
4. bind release claims to exact evidence;
5. publish failures alongside fixes; and
6. correct durable statements by dated addendum.

## What this page does not claim

- No verification process is exhaustive.
- No model score proves safety or compliance.
- Open source does not eliminate deployment or data-handling risk.
- A successful security scan does not prove the absence of vulnerabilities.
- Current containment does not answer historical-access questions.
- Engagement does not prove correctness, benefit, or safety.

## Related records

- [Statement 001 — Trinity Integrity](Statement-001-Trinity-Integrity)
- [Current Production Status](Current-Production-Status)
- [Operations Playbook](Operations-Playbook)
- [Genesis Methodology](Genesis-Methodology)
- [SECURITY.md](https://github.com/creator35lwb-web/VerifiMind-PEAS/blob/main/SECURITY.md)
