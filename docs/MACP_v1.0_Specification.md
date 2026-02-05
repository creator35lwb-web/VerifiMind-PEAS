# Multi-Agent Communication Protocol (MACP) v1.0 Specification

**Version:** 1.0.0  
**Effective Date:** February 5, 2026  
**Author:** Godel (Manus AI)  
**Status:** DRAFT

---

## 1. Introduction

The Multi-Agent Communication Protocol (MACP) provides a standardized framework for seamless collaboration and handoffs between multiple AI agents working on a shared project within a GitHub repository. It formalizes the emergent communication patterns observed across the VerifiMind-PEAS, RoleNoteAI, GODELAI, and LegacyEvolve projects.

### 1.1. Core Principles

1.  **Role-Based Specialization:** Agents have persistent roles with clear responsibilities.
2.  **GitHub as Bridge:** All communication happens through GitHub (README, commits, docs).
3.  **Validation First:** Trinity validation before implementation.
4.  **Sequential Phases:** Complete one phase before starting the next.
5.  **Multi-Model Leverage:** Use different models for different strengths.
6.  **Living Documentation:** Documentation evolves with the project.

---

## 2. Standard File Structure

All MACP-compliant repositories MUST adhere to the following file structure:

```
project/
├── README.md                    # Project status + agent notes
├── GENESIS_MASTER_PROMPT.md     # Complete project context
├── CHANGELOG.md                 # Version history
├── ROADMAP.md                   # Future direction
├── CONTRIBUTING.md              # How to contribute
├── .macp/                       # MACP metadata
│   ├── agents.json              # Agent registry
│   ├── handoffs.json            # Handoff history
│   └── validation.json          # Validation records
└── docs/
    ├── ARCHITECTURE.md
    ├── IMPLEMENTATION_GUIDE.md
    └── [other docs]
```

---

## 3. Agent Registry (`.macp/agents.json`)

This file defines all agents that have contributed to the project.

### 3.1. Schema

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "MACP Agent Registry",
  "type": "object",
  "properties": {
    "agents": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "id": {"type": "string"},
          "name": {"type": "string"},
          "role": {"type": "string"},
          "responsibilities": {"type": "array", "items": {"type": "string"}},
          "active_since": {"type": "string", "format": "date-time"},
          "last_handoff": {"type": ["string", "null"], "format": "date-time"}
        },
        "required": ["id", "name", "role", "responsibilities", "active_since"]
      }
    }
  }
}
```

### 3.2. Example

```json
{
  "agents": [
    {
      "id": "RNA",
      "name": "Claude Code Opus 4.5",
      "role": "CTO",
      "responsibilities": ["Code implementation", "Testing", "Experiments"],
      "active_since": "2026-01-31T00:00:00Z",
      "last_handoff": "2026-02-01T10:30:00Z"
    },
    {
      "id": "R",
      "name": "Manus AI",
      "role": "CSO",
      "responsibilities": ["Strategic planning", "Documentation", "Market research"],
      "active_since": "2026-02-01T10:30:00Z",
      "last_handoff": null
    }
  ]
}
```

---

## 4. Handoff Records (`.macp/handoffs.json`)

This file provides a structured history of all agent handoffs.

### 4.1. Schema

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "MACP Handoff Records",
  "type": "object",
  "properties": {
    "handoffs": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "id": {"type": "string"},
          "timestamp": {"type": "string", "format": "date-time"},
          "from_agent": {"type": "string"},
          "to_agent": {"type": "string"},
          "phase": {"type": "string"},
          "summary": {"type": "string"},
          "next_steps": {"type": "array", "items": {"type": "string"}},
          "context": {"type": "string"},
          "commit_sha": {"type": "string"}
        },
        "required": ["id", "timestamp", "from_agent", "to_agent", "phase", "summary", "next_steps", "commit_sha"]
      }
    }
  }
}
```

### 4.2. Example

```json
{
  "handoffs": [
    {
      "id": "handoff-001",
      "timestamp": "2026-02-01T10:30:00Z",
      "from_agent": "RNA",
      "to_agent": "R",
      "phase": "Phase 3a Complete",
      "summary": "Android project setup complete. Security layer solid.",
      "next_steps": ["Phase 3b: Core Engine", "Template integration", "CRUD operations"],
      "context": "Test device: Redmi Pad SE 8.7",
      "commit_sha": "abc123def456"
    }
  ]
}
```

---

## 5. Validation Records (`.macp/validation.json`)

This file provides a structured history of all VerifiMind-PEAS validations.

### 5.1. Schema

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "MACP Validation Records",
  "type": "object",
  "properties": {
    "validations": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "id": {"type": "string"},
          "timestamp": {"type": "string", "format": "date-time"},
          "methodology": {"type": "string"},
          "x_agent": {"type": "object"},
          "z_agent": {"type": "object"},
          "cs_agent": {"type": "object"},
          "overall": {"type": "object"},
          "report_url": {"type": "string"}
        },
        "required": ["id", "timestamp", "methodology", "overall", "report_url"]
      }
    }
  }
}
```

### 5.2. Example

```json
{
  "validations": [
    {
      "id": "fa3e7b66",
      "timestamp": "2026-01-25T14:00:00Z",
      "methodology": "VerifiMind-PEAS Trinity",
      "x_agent": {"score": 7.5, "status": "APPROVED"},
      "z_agent": {"score": 7.5, "status": "APPROVED"},
      "cs_agent": {"score": 6.5, "status": "APPROVED"},
      "overall": {"score": 7.3, "verdict": "Proceed with Caution"},
      "report_url": "docs/TRINITY_VALIDATION_REPORT.md"
    }
  ]
}
```

---

## 6. Standard Commit Message Format

All commits MUST follow this format:

```
<type>(<scope>): <subject>

<body>

Agent: <AGENT_ID>
Phase: <PHASE_NAME>
Handoff: <HANDOFF_ID>
```

### 6.1. Example

```
feat(core): implement role template engine

- Load 19 templates from JSON files
- Add template validation
- Integrate with note creation flow

Agent: RNA
Phase: Phase 3b
Handoff: handoff-002
```

---

## 7. Agent Communication Flow

All agents MUST follow this communication flow:

1.  **Read `README.md`**: Understand the current project status and active agent notes.
2.  **Read `.macp/handoffs.json`**: Review the latest handoff record for immediate next steps.
3.  **Read `GENESIS_MASTER_PROMPT.md`**: Gain full project context and specifications.
4.  **Execute Work**: Perform assigned tasks according to role and responsibilities.
5.  **Update Documentation**: Modify `README.md`, `CHANGELOG.md`, and other relevant documents.
6.  **Create Handoff Record**: Add a new entry to `.macp/handoffs.json` with a summary of work completed and next steps for the next agent.
7.  **Commit Changes**: Use the standard commit message format to push all changes to GitHub.

---

## 8. Handoff Template (in `README.md`)

Each agent MUST update the `README.md` with their handoff notes before committing.

```markdown
### Current [ROLE] Notes ([AGENT_ID])

> **Focus:** [Current phase or sprint]
>
> [Summary of current state]
>
> **Next Priority:**
> - [Priority 1]
> - [Priority 2]
> - [Priority 3]
>
> **Context for Next Agent:**
> [Any important context or decisions]
>
> — [AGENT_NAME] ([MODEL_NAME]), [DATE]
```

---

**End of MACP v1.0 Specification**
