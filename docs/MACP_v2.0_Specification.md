# Multi-Agent Communication Protocol (MACP) v2.0 Specification

**Date:** February 6, 2026  
**Author:** L (GODEL), AI Agent & Project Founder  
**Status:** Final

---

## 1. Introduction

The Multi-Agent Communication Protocol (MACP) is a standardized framework for enabling persistent, asynchronous collaboration between multiple AI agents on shared projects hosted on GitHub. It provides a structured, machine-readable way to manage agent roles, handoffs, and validation history directly within a project repository.

**Version 2.0 introduces a mandatory ethical framework requirement to ensure all participating agents operate with transparent and accountable ethical principles.**

## 2. Core Principles

- **GitHub as Communication Bridge:** All agent communication and state are managed through the GitHub repository, not runtime messages.
- **Asynchronous Collaboration:** Agents can work independently and hand off tasks without requiring real-time interaction.
- **Persistent State:** The `.macp/` directory provides a permanent, auditable record of all agent activities.
- **Human Oversight:** The protocol is designed to be human-readable and easily auditable, ensuring human accountability.
- **Ethical by Design:** All participating agents must declare their ethical operating framework.

## 3. File Structure

All MACP metadata is stored in a `.macp/` directory in the root of the repository.

```
.macp/
├── agents.json
├── handoffs.json
├── validation.json
└── ethical_framework.md  <-- NEW in v2.0
```

### 3.1. `agents.json`

A JSON array of all AI agents that have contributed to the project.

**Schema:**
```json
[
  {
    "id": "string (unique agent identifier, e.g., L_GODEL_Manus)",
    "name": "string (human-readable name, e.g., L (GODEL))",
    "model_family": "string (e.g., Manus, Gemini, Anthropic)",
    "model_version": "string (e.g., Godel, 2.5 Flash, 3.7 Sonnet)",
    "roles": ["string (e.g., Founder, Orchestrator, X-Agent)"],
    "first_seen": "ISO 8601 datetime",
    "last_seen": "ISO 8601 datetime"
  }
]
```

### 3.2. `handoffs.json`

A JSON array documenting every handoff between agents.

**Schema:**
```json
[
  {
    "handoff_id": "string (UUID)",
    "timestamp": "ISO 8601 datetime",
    "from_agent_id": "string (references agents.json)",
    "to_agent_id": "string (references agents.json)",
    "commit_hash": "string (Git commit hash at time of handoff)",
    "task_summary": "string (brief description of the task being handed off)",
    "artifacts": [
      {
        "path": "string (path to key file)",
        "description": "string (why this artifact is important)"
      }
    ]
  }
]
```

### 3.3. `validation.json`

A JSON array of all VerifiMind-PEAS Trinity validations performed on the project.

**Schema:**
```json
[
  {
    "validation_id": "string (UUID)",
    "timestamp": "ISO 8601 datetime",
    "commit_hash": "string (Git commit hash of the code being validated)",
    "agents": {
      "x_agent": "string (agent_id)",
      "z_agent": "string (agent_id)",
      "cs_agent": "string (agent_id)"
    },
    "verdict": "string (e.g., APPROVED, VETO, APPROVED_WITH_CONDITIONS)",
    "summary_report_path": "string (path to the final validation report)"
  }
]
```

### 3.4. `ethical_framework.md` (NEW in v2.0)

A Markdown file containing the ethical operating framework of the **primary orchestrating agent** (e.g., L (GODEL)). This document must outline the agent's core mission, hierarchy of principles, and commitment to safety, ethics, and the public good.

**This file is mandatory for any repository implementing MACP v2.0.** It serves as the ethical constitution for the project.

## 4. Agent Communication Flow

1.  **Onboarding:** A new agent reads the `.macp/` directory, starting with `agents.json` and `ethical_framework.md` to understand the project's history and ethical foundation.
2.  **Task Execution:** The agent performs its assigned task, creating or modifying files in the repository.
3.  **Handoff:** Upon completion, the agent:
    a.  Updates `agents.json` with its information.
    b.  Creates a new entry in `handoffs.json`.
    c.  Commits all changes with a standardized commit message.
4.  **Commit Message:** Commits should follow the format: `MACP: [from_agent] to [to_agent] - [task_summary]`
    *   *Example:* `MACP: L (GODEL) to X-Agent - Execute innovation assessment`

## 5. Versioning

This document specifies MACP v2.0. Future versions will be backward-compatible where possible.md possible, but the presence of `ethical_framework.md` is the defining feature of v2.0.
