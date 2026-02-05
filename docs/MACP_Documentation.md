# Multi-Agent Communication Protocol (MACP) Documentation

**Version:** 1.0.0  
**Author:** Godel (Manus AI)

---

## 1. Overview

The Multi-Agent Communication Protocol (MACP) provides a standardized framework for seamless collaboration and handoffs between multiple AI agents working on a shared project within a GitHub repository. It enables persistent, multi-agent teams that work together across time and models.

### 1.1. Core Principles

1.  **Role-Based Specialization:** Agents have persistent roles with clear responsibilities.
2.  **GitHub as Bridge:** All communication happens through GitHub (README, commits, docs).
3.  **Validation First:** Trinity validation before implementation.
4.  **Sequential Phases:** Complete one phase before starting the next.
5.  **Multi-Model Leverage:** Use different models for different strengths.
6.  **Living Documentation:** Documentation evolves with the project.

---

## 2. How to Use MACP

### 2.1. For a New Agent Joining a Project

1.  **Read `README.md`**: Understand the current project status and active agent notes.
2.  **Read `.macp/agents.json`**: Identify your role and responsibilities.
3.  **Read `.macp/handoffs.json`**: Review the latest handoff record for immediate next steps.
4.  **Read `GENESIS_MASTER_PROMPT.md`**: Gain full project context and specifications.
5.  **Execute Work**: Perform assigned tasks according to your role.
6.  **Update Documentation**: Modify `README.md`, `CHANGELOG.md`, and other relevant documents.
7.  **Create Handoff Record**: Add a new entry to `.macp/handoffs.json` with a summary of work completed and next steps for the next agent.
8.  **Commit Changes**: Use the standard commit message format to push all changes to GitHub.

### 2.2. Example Workflow: RoleNoteAI

**Scenario:** Agent R (Manus AI) is taking over from Agent RNA (Claude Code).

1.  **Agent R reads `README.md`**: Sees that Phase 3a is complete and the next focus is Phase 3b.
2.  **Agent R reads `.macp/handoffs.json`**: Finds `handoff-001` with details on what RNA completed and what R should do next.
3.  **Agent R reads `GENESIS_MASTER_PROMPT.md`**: Understands the full vision and architecture of RoleNoteAI.
4.  **Agent R executes work**: Performs strategic planning and market research for Phase 3b.
5.  **Agent R updates `README.md`**: Adds new CSO notes with strategic findings.
6.  **Agent R creates `handoff-002` in `.macp/handoffs.json`**: Summarizes strategic findings and provides next steps for RNA (e.g., implement new feature based on market research).
7.  **Agent R commits changes**: `feat(strategy): add market research for phase 3b

Agent: R
Phase: Phase 3b
Handoff: handoff-002`

---

## 3. MACP Specification

For the full technical specification, please refer to the [MACP v1.0 Specification](MACP_v1.0_Specification.md).

---

## 4. Benefits of MACP

-   **Standardization:** Consistent collaboration across all projects.
-   **Continuity:** Seamless handoffs between different AI models.
-   **Context Preservation:** No loss of information between agent sessions.
-   **Scalability:** Easily add new agents and projects to the ecosystem.
-   **Transparency:** Clear, auditable history of all agent contributions.

---

**End of MACP Documentation**
