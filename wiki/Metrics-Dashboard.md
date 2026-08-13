# Metrics Evidence Register

> **Document boundary — dated evidence.** This page records measurements from named observation windows. It is not a live dashboard and must not be used as proof of current production health, current adoption, or causal product impact. For live technical state, use [Current Production Status](Current-Production-Status).

Metrics age differently from software. A release can be verified at an exact commit; an engagement estimate depends on a time window, filters, identity assumptions, and a reproducible query. Every number on this page therefore travels with its report, period, method, and limitations.

## Public snapshot: Report 102

**Observation period:** 2026-07-08 through 2026-07-15

**Method recorded by the report:** Success-Gated v2.5, Maxis-Hardened, CDN-cluster-aware

**Status:** historical snapshot; not a statement about 2026-08-10

| Measure | Reported value | What it means |
|---|---:|---|
| Value Confirmation Rate | 61.7% | 6,511 of 10,556 valid sessions sent at least a second tool-call request |
| Robust-value share | 23.4% | Share of valid sessions with five or more prompts |
| Cumulative verified-engagement window | 11,000+ hours | Sum of first-to-last request intervals after the report’s exclusions; not active attention time |
| Estimated unique endpoints | 5,400+ | Confidence-tiered endpoint estimate, not a count of identified people |
| Weekly active endpoints | 348 | Endpoints observed in the stated reporting week |
| Connection success rate | 77.1% | Valid sessions divided by total sessions under the report’s classifier |
| Early-adopter active-week cohort | 70 | High-usage endpoints active in that reporting week |
| Early-adopter honest-baseline reach | 166 | Audited proxy after prefix/CDN collapse and success gating |
| Consent-first UUID registrations | 1 | Firestore-verified registration count recorded for that report |

These figures are reproduced as a dated record. Later reports may revise them as identity resolution, bot detection, or source completeness improves.

## Definitions and limits

### Value Confirmation Rate

Formula:

```text
sessions with at least two tool-call requests / valid sessions
```

A follow-up request is a behavioral proxy for continued engagement. It is **not direct proof** that the first answer was correct, useful, or responsible, and it does not establish causation.

### Verified-engagement window

The measure uses elapsed time between an endpoint’s first and last qualifying request in a session. It is an interval proxy, not measured human attention. Background clients, pauses, shared endpoints, and identity classification can affect it.

### Endpoint counts

An endpoint is not necessarily a person or organization. NAT, VPNs, mobile carrier infrastructure, shared clients, and CDN behavior can merge or split apparent identities. Public reporting must say **endpoint**, not **user**, unless a separate consented identity measure supports the claim.

### Early-adopter measures

The three cohort measures are orthogonal and must not be added together:

- **Active-week:** qualifying endpoints active in the report window.
- **Honest-baseline reach:** the report’s conservative forensic deduplication proxy.
- **Registered:** consent-first UUID records.

## Evidence quality rules

A metric is publishable only when the accompanying artifact states:

1. the observation start and end time, including timezone;
2. the source systems and ingestion coverage;
3. success, owner, bot, scraper, proxy, and CDN filters;
4. the identity unit being counted;
5. the query or pipeline version;
6. known missing data and corrections; and
7. the reviewer and publication date.

If any of those are missing, label the number **provisional**. Never silently replace a prior number; publish a correction with its reason and effect.

## Audit lineage

- **Phase 47 (March 2026):** forensic deduplication removed duplicate and bot traffic and corrected earlier engagement and VCR estimates downward.
- **Later pipeline hardening:** success gating, duplicate-ingestion protection, proxy-prefix handling, and CDN-cluster classification were added to reduce overcounting.
- **Report 102:** the public snapshot above reflects those controls as documented for its July 2026 window.

The underlying operational reports and raw production logs are not reproduced by this Wiki page. That limits independent reproduction and must be stated alongside any citation.

## Citation form

Use a dated citation, for example:

> VerifiMind PEAS, COO Report 102, observation window 2026-07-08 to 2026-07-15, Success-Gated v2.5 methodology.

Do not write “current metrics” unless a newly generated, reviewed artifact covers the claimed date. Production health belongs to the status page; product effectiveness requires separate evaluation evidence.
