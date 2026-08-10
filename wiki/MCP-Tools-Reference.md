# MCP Tools Reference

This page explains the stable purpose and availability class of each public
tool. Exact JSON schemas are discoverable through MCP `tools/list` and are owned
by the running server.

## Source boundary

Before integrating against a tool, check:

- [`/health`](https://verifimind.ysenseai.org/health) for live availability,
  routing, and failover state;
- [`/setup`](https://verifimind.ysenseai.org/setup) for current configuration;
- the [server card](https://verifimind.ysenseai.org/.well-known/mcp/server-card.json)
  for machine-readable discovery;
- [Current Production Status](Current-Production-Status) for release and
  deployment provenance;
- the current
  [server implementation](https://github.com/creator35lwb-web/VerifiMind-PEAS/blob/main/mcp-server/src/verifimind_mcp/server.py)
  when exact behavior matters.

## Availability at a glance

Production currently defines **13** tool schemas:

| Class | Count | Behavior |
|---|---:|---|
| Active Trinity analysis | 4 | Runs X, Z, CS, or the X → Z → CS sequence |
| Active built-in template reads | 4 | Lists, reads, exports, or summarizes built-in templates |
| Temporarily unavailable custom-template mutation | 2 | Returns a maintenance denial; performs no mutation |
| Temporarily unavailable coordination | 3 | Returns a containment denial; performs no public read or write |

That is **13 defined / 8 active / 5 temporarily unavailable**. “Free” is a
pricing statement; “active” is an availability statement. Do not conflate them.

## Active Trinity tools

### `consult_agent_x`

Innovation and strategy review. X explores novelty, alternatives, positioning,
assumptions, and execution trade-offs.

Common inputs include a concept name, concept description, optional context,
reasoning detail, optional BYOK provider/key, and optional UUID.

### `consult_agent_z`

Ethics and compliance-oriented review. Z examines affected people, rights,
fairness, governance, applicable frameworks, and ethical red lines.

It can receive trustworthy prior reasoning from X. A Z veto is a strong
human-review signal, not a legal determination.

### `consult_agent_cs`

Security review. CS examines threats, vulnerabilities, misuse, data handling,
system integrity, and assumptions that require testing.

It can receive trustworthy prior reasoning from X and Z. Its output is not a
penetration test or security certification.

### `run_full_trinity`

Runs X → Z → CS and synthesizes the completed stages into one structured result.
Later stages receive only reasoning that passed the stage-quality gate.

Important options:

| Option | Stable meaning |
|---|---|
| `detail` | Controls response detail; discover allowed values from the live schema |
| `llm_provider` + `api_key` | Optional global BYOK override |
| `x_provider` / `z_provider` / `cs_provider` and matching keys | Optional per-stage BYOK overrides; these take precedence over the global override |
| `save_to_history` | Optional aggregate-history opt-in; defaults to `false` |
| `user_uuid` | Optional pseudonymous usage identity; separate from aggregate-history opt-in |

## Active built-in template reads

Only built-in template data is exposed while custom-template storage is under
security maintenance.

| Tool | Purpose |
|---|---|
| `list_prompt_templates` | List built-in templates, optionally filtered by agent/category/tags |
| `get_prompt_template` | Retrieve one built-in template by ID |
| `export_prompt_template` | Export a built-in template in a supported representation |
| `get_template_statistics` | Return statistics for the built-in registry |

Treat template text as guidance. Review it before applying it to sensitive or
high-consequence work.

## Temporarily unavailable tools

### Custom-template mutation

| Tool | Current behavior |
|---|---|
| `register_custom_template` | Returns `CUSTOM_TEMPLATE_TEMPORARILY_DISABLED` |
| `import_template_from_url` | Returns `CUSTOM_TEMPLATE_TEMPORARILY_DISABLED` |

These tools remain unavailable pending owner-scoped storage and URL-fetch
hardening. Arguments are retained for schema compatibility; a call does not
create or import a template.

### Coordination

| Tool | Current behavior |
|---|---|
| `coordination_handoff_create` | Returns `COORDINATION_TEMPORARILY_DISABLED` |
| `coordination_handoff_read` | Returns `COORDINATION_TEMPORARILY_DISABLED` |
| `coordination_team_status` | Returns `COORDINATION_TEMPORARILY_DISABLED` |

There is no supported public shared or anonymous coordination namespace. While
containment remains in force, keep coordination artifacts in a repository or
storage system whose ownership and access controls you manage.

Incident context and open limitations are recorded in
[Public Statements](Public-Statements).

## Output-integrity contract

Interpret a response using quality and completeness, not only scores:

- Generated findings, recommendations, reasoning, and veto state are published
  only for stages that satisfy the real-inference quality gate.
- A failed stage is identified as unavailable/degraded; trustworthy sibling
  stages may remain available.
- An incomplete Trinity cannot present an aggregate score or confidence as
  though all three stages completed.
- Normalized provider failures distinguish classes such as rate limit,
  truncation, timeout, and authentication where evidence supports that class.
- Recovery guidance should match the actual failure and retryability.
- A missing stage is not evidence that the stage found no problem.

The human reviewer should always record what was checked, what failed, and what
remains open.

## History and privacy

`save_to_history` defaults to `false`.

If explicitly enabled, aggregate history is:

- shared within the running service instance rather than owner-scoped;
- bounded to the newest 20 opt-in results;
- pruned on read/write and cleared when the instance is replaced;
- not governed by a guaranteed fixed time-based retention period;
- not written for exception-incomplete Trinity runs.

Supplying `user_uuid` is a separate optional choice and may create pseudonymous
metadata/history described by the live
[Privacy Policy](https://verifimind.ysenseai.org/privacy). Leave both options
off for private or sensitive concepts.

## BYOK and routing

BYOK is supported by the active Trinity tools. The hosted free tier may route
different stages to different providers; a global BYOK override can instead
select one provider for all stages, and per-stage overrides can mix providers.

Provider lists, model IDs, construction fallback, and runtime failover are
volatile. Read them from [`/health`](https://verifimind.ysenseai.org/health)
and [`/setup`](https://verifimind.ysenseai.org/setup). See the
[BYOK Guide](BYOK-Guide) for the stable operating rules.

---

[← Home](Home) · [Installation](Installation) · [BYOK](BYOK-Guide)
