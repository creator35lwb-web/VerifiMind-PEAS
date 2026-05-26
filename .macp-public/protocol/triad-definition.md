# The Memory-Reasoning-Handoff Triad

> The core discipline of MACP v2.4.0. Three artifacts that make multi-agent work auditable.

A multi-agent system is only as trustworthy as its paper trail. The Triad is MACP's answer: three complementary artifacts, each with a distinct purpose, lifespan, and cadence.

---

## Handoff — *state*

**Purpose:** continuity. Anyone (human or agent) picking up the work can see where it stands.

**Lifespan:** session-scoped.
**Cadence:** every session that did work.

**Contains:** From/To, what was completed, current state (what's live/deployed), next actions, open items with owners, files touched.

---

## Reasoning — *process*

**Purpose:** accountability for *judgment*. Not what changed, but **why** — and what was rejected.

**Lifespan:** session-scoped.
**Cadence:** per decision-cluster. (Skipped only for purely mechanical sessions.)

**Contains:** numbered decisions (trigger → chosen path → why → confidence), mistakes caught mid-flight, and **falsifiable forecasts** — predictions with a stated check, so the team can later confirm or refute them.

The forecast discipline matters: it converts opinion into something that can be proven wrong.

---

## Memory — *durable rules*

**Purpose:** learning. Rules that future sessions should operate under by default.

**Lifespan:** cross-session (persistent).
**Cadence:** only when a durable insight emerges — roughly one session in three. Memory is not a session log; it is the distilled, reusable rule.

**Contains:** one fact per entry, typed (user / feedback / project / reference), with *why* and *how to apply*, cross-linked to related memories.

---

## Why three, not one

Each leg fails differently if merged with another:
- Handoff alone → you know the *state* but not the *reasoning*; you repeat past mistakes.
- Reasoning alone → you know the *decisions* but lose *durable rules*; every session re-derives them.
- Memory alone → you have *rules* but no *audit trail* to justify them.

Together, they make a multi-agent system that can explain itself — to its own future sessions, to its human lead, and to an external reviewer.

---

*Part of the MACP v2.4.0 public specification. See [`MACP_v2.4.0_spec.md`](MACP_v2.4.0_spec.md).*
