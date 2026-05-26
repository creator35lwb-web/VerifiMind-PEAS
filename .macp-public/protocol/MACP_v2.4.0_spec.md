# MACP v2.4.0 — Protocol Specification

> **Multi-Agent Communication Protocol** · codename "Triad" · a model-agnostic coordination protocol for multi-agent AI systems.
> This document is **self-contained** — you can read it without the full thesis. For operational evidence, see [`../exemplars/`](../exemplars/); for governance, see [`../governance/`](../governance/).

---

## 1. Purpose

MACP answers one question: **how do multiple AI agents — often on different platforms — collaborate on complex, long-running work while staying coherent, accountable, and auditable?**

It is **not** an orchestration framework and **not** a replacement for any agent's native capability. MACP is to multi-agent coordination what HTTP is to document transfer: a thin, open protocol that *carries* the work between agents without dictating what each agent is or does.

## 2. Design principles

1. **Human-centric authority.** One human holds final authority. AI agents operate under delegation; none has independent merge authority.
2. **Auditable by construction.** Every strategic decision leaves a durable trail (the Triad, §3). Coordination is legible after the fact, not just in the moment.
3. **Model-agnostic.** Agents may run on any platform. Roles are defined by function, not vendor.
4. **A shared bus.** A version-controlled repository (e.g., GitHub) is the coordination layer — the single source of truth all agents read from and write to.
5. **Request-don't-edit across boundaries.** An agent does not silently edit another agent's canonical artifact; it proposes the change and routes it to the owner (§4.2).

## 3. The Triad (core innovation)

Every strategic session produces up to three artifacts:

| Leg | Captures | Cadence |
|-----|----------|---------|
| **Memory** | Durable rules and validated patterns future sessions operate under | Only when a durable insight emerges (~1 in 3 sessions) |
| **Reasoning** | The decision trail — options considered, choices made, mistakes caught, falsifiable forecasts | Per decision-cluster |
| **Handoff** | Session state — what happened, what's deployed, what's next, who owns what | Every session |

The Triad is what makes a multi-agent system *inspectable*: a reviewer can reconstruct not just *what* changed but *why*, and hold forecasts accountable later.

## 4. Coordination primitives

### 4.1 Handoff
A structured record passed from one agent (or session) to another. Minimum fields: **From / To**, scope, work completed, current state, next actions, open items + owners. See [`../exemplars/handoff-example-redacted.md`](../exemplars/handoff-example-redacted.md).

### 4.2 Routing & the Cross-Agent Canonical-Edit Protocol
Artifacts have owners. Changes to an artifact you don't own are classified:
- **Substantive** → never edit; request the owner.
- **Mechanical** → a flagged exception is permissible.
- **Default** → request-don't-edit: open a change-request with evidence and route to the owner.

This is the same semantics as a pull request, applied to *all* coordination artifacts — not just code.

### 4.3 Escalation (advisory, not veto)
Specialized agents may **flag for review** (e.g., an ethics guardian flags an ethical concern; an intelligence role flags a strategic risk). Flags are advisory inputs to the human lead's final decision — never an autonomous override.

## 5. Session lifecycle

```
CREATED → IN_PROGRESS → REVIEW → COMPLETED → ARCHIVED
```

A unit of work is not "done" until it is reviewed and its Triad artifacts are filed.

## 6. Authority model

| Tier | Holder | Authority |
|------|--------|-----------|
| Human orchestrator | the project's lead maintainer | Absolute — final say, universal veto |
| Delegated coordinator | a designated coordination agent | Strategic synthesis under delegation |
| Agent team | role-defined AI agents | Advisory / development — no independent merge |

## 7. Versioning

MACP versions follow semantic intent: **MAJOR** for protocol-shape changes, **MINOR** for new primitives or roles, **PATCH** for clarifications. This document describes **v2.4.0 "Triad"** — the version in which the Memory-Reasoning-Handoff Triad became the default operating discipline.

## 8. What MACP is *not*

- Not an agent framework or runtime — it coordinates agents, it doesn't run them.
- Not a consensus/voting system — authority is human-centric, not democratic.
- Not a replacement for any model's capabilities — it carries the work, the agents do it.

---

*MACP v2.4.0 "Triad" — Multi-Agent Communication Protocol. Sanitized public specification; full thesis published via Zenodo (DOI forthcoming).*
