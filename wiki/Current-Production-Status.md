# Current Production Status

> **Document boundary — mutable live reference.** This is a dated evidence snapshot, not a timeless description. If a live source disagrees with this page, treat the field as stale, preserve the discrepancy, and open a bounded truth correction.

**Snapshot date:** 2026-08-10

**Release event:** v0.5.58 deployed 2026-08-07

**Production hostname:** [https://verifimind.ysenseai.org](https://verifimind.ysenseai.org)

## Release identity

| Field | Verified value |
|---|---|
| Production version | **0.5.58** |
| Source merge commit | [`3019f5c4889d8334063d4a2d9243e87d96fc93a8`](https://github.com/creator35lwb-web/VerifiMind-PEAS/commit/3019f5c4889d8334063d4a2d9243e87d96fc93a8) |
| Pull request | [#324](https://github.com/creator35lwb-web/VerifiMind-PEAS/pull/324) |
| GitHub Release | [v0.5.58](https://github.com/creator35lwb-web/VerifiMind-PEAS/releases/tag/v0.5.58), targeted at the source merge commit above |
| Cloud Build | `be6ed621-c0b8-49a3-a9f3-7ba36e68c7ea` |
| Serving revision | Not recorded in this public Wiki evidence set; do not infer one from the build ID |
| Post-deploy smoke | **31 PASS / 0 STOP / 0 INSTRUMENT** |

The GitHub Release title is “Harden Trinity Degradation and Provider Currency.” A release tag, build, and serving revision are separate identifiers even when they derive from the same source.

## Protocol and tool contract

| Field | Verified value |
|---|---|
| MCP transport endpoint | `https://verifimind.ysenseai.org/mcp/` |
| MCP protocol | **2025-11-25** |
| Tool inventory | **13 defined / 8 active / 5 temporarily unavailable** |
| Runtime failover | **false** |
| MCP Registry metadata version | **3.35.0** |
| Registry publication | Successful at release SHA via [workflow run 31216980480](https://github.com/creator35lwb-web/VerifiMind-PEAS/actions/runs/31216980480) |

`runtime failover: false` reports the deployed configuration. It does not mean failure handling is absent: v0.5.58 preserves successful seats and marks a run incomplete when another seat fails. It does mean documentation must not claim automatic runtime provider failover is enabled.

## Default Trinity routes

| Seat | Provider | Model |
|---|---|---|
| X | Gemini | `gemini-3.5-flash-lite` |
| Z | Groq | `openai/gpt-oss-120b` |
| CS | Groq | `openai/gpt-oss-120b` |

These are default production routes for the v0.5.58 evidence snapshot. BYOK can select a supported request-scoped provider. Two seats using the same provider/model weakens failure-domain diversity and must not be described as three-provider independence.

## Tool availability

### Active: 8

Trinity:

- `consult_agent_x`
- `consult_agent_z`
- `consult_agent_cs`
- `run_full_trinity`

Built-in template reads:

- `list_prompt_templates`
- `get_prompt_template`
- `export_prompt_template`
- `get_template_statistics`

### Temporarily unavailable: 5

Custom-template writes/imports:

- `register_custom_template`
- `import_template_from_url`

Contained coordination tools:

- `coordination_handoff_create`
- `coordination_handoff_read`
- `coordination_team_status`

The defined tool count includes unavailable tools so clients receive an explicit status instead of a silently changing schema.

## Trust and disclosure state

| Matter | State |
|---|---|
| [Public Statement 001](Statement-001-Trinity-Integrity) | **Live / current** |
| `VM-IR-2026-07-28-COORD-01` | **CONTAINED, NOT CLOSED** |
| Coordination tools | Unavailable pending owner-scoped authorization and separate restoration approval |
| Custom-template registration/import | Unavailable pending owner-scoped storage and URL-fetch protections |

Containment does not establish that no unauthorized access occurred and does not settle any separate legal-notification question. See [Trust and Safety](Trust-and-Safety) and [Public Statements](Public-Statements).

## What v0.5.58 proves

The release evidence demonstrates that:

- a real provider-stage failure can preserve successful seats while withholding the failed seat;
- the result is explicitly incomplete and routed for human review;
- typed provider failures carry accurate retry and recovery semantics;
- incomplete runs are not written to shared history;
- summary text no longer converts identified ethics or security concerns into absolute “no concern” claims; and
- the configured provider catalog passed the release’s currency checks.

It does not prove every provider failure mode, permanent availability, model independence, legal compliance, or general decision-quality improvement.

## Evidence sources

Use these in order and preserve disagreements:

1. [Live `/health`](https://verifimind.ysenseai.org/health) — runtime version, protocol, counts, providers, failover, and service health.
2. [Live `/setup`](https://verifimind.ysenseai.org/setup) — client-facing setup and tool availability summary.
3. [GitHub Release v0.5.58](https://github.com/creator35lwb-web/VerifiMind-PEAS/releases/tag/v0.5.58) — immutable release target.
4. [PR #324](https://github.com/creator35lwb-web/VerifiMind-PEAS/pull/324) and source commit — merge provenance.
5. Cloud Build and post-deploy smoke receipt — build and behavioral evidence.
6. [MCP Registry workflow](https://github.com/creator35lwb-web/VerifiMind-PEAS/actions/runs/31216980480) and `server.json` — distribution metadata.
7. [Public Statement 001](Statement-001-Trinity-Integrity) — durable disclosure and remaining risks.

The absence of the exact serving-revision name from this public evidence set is a provenance gap, not permission to invent it.

## Update rule

Update this page after any production change to version, source SHA, build/revision, protocol, tool availability, provider/model routes, failover state, registry metadata, or incident status. Record the observation date and link exact evidence. Do not copy production facts into textbook pages.
