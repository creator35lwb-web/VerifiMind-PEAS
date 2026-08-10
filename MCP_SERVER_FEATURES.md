# VerifiMind PEAS MCP Server — Features Guide

**Production Version:** v0.5.58
**MCP Registry Package:** 3.35.0
**Status:** ✅ **LIVE** at [verifimind.ysenseai.org](https://verifimind.ysenseai.org)
**Last Updated:** August 10, 2026 — v0.5.58 production alignment

> All **13 tools free forever** under the [Core Tools Always Free pledge](https://github.com/creator35lwb-web/VerifiMind-PEAS#core-tools-always-free-pledge) (Option B, May 9, 2026).
> **Current availability:** 8 active; 3 coordination and 2 custom-template mutation tools temporarily unavailable during security maintenance.

---

## 🎯 What is VerifiMind PEAS?

VerifiMind PEAS is an opinionated MCP server for **structured multi-LLM critique**. Three specialized agents — Innovation, Ethics, Security — review your concept before you build it.

**Capabilities exposed via Model Context Protocol:**

1. **Resources (4)** — Read-only data that LLMs can access for methodology context
2. **Tools (13)** — Actions that LLMs can execute: 4 Trinity validation + 6 template library + 3 coordination

**What this is NOT:** "Verification" in the formal-methods sense. The output is structured multi-LLM critique, not a mathematical proof. We make this distinction explicitly — see our [Evaluation Roadmap](https://verifimind.ysenseai.org/research/evaluation-roadmap) and [The Validation Paradox](https://verifimind.ysenseai.org/research/paradox).

---

## 📚 Resources (4)

Resources provide **context and knowledge** for LLMs to understand the VerifiMind methodology before invoking tools.

### 1. Genesis Master Prompt

| Property | Value |
|---|---|
| **URI** | `genesis://config/master_prompt` |
| **Format** | Markdown |
| **Version** | Production methodology resource (version-independent discovery identity) |
| **Purpose** | X / Z / CS agent methodology and citation architecture |

### 2. Latest Validation Summary

| Property | Value |
|---|---|
| **URI** | `genesis://history/latest` |
| **Format** | JSON |
| **Purpose** | Privacy-safe, non-identifying summary of the newest eligible shared-history entry |

### 3. Bounded Validation Statistics

| Property | Value |
|---|---|
| **URI** | `genesis://history/all` |
| **Format** | JSON |
| **Purpose** | Aggregate statistics over at most 20 eligible shared-history entries; not a full archive |

### 4. Project Information

| Property | Value |
|---|---|
| **URI** | `genesis://state/project_info` |
| **Format** | JSON |
| **Purpose** | Architecture overview, agent roles, version + docs links |

---

## 🔧 Tools — 13 Free Forever

### Trinity Validation (4)

The X → Z → CS Trinity is the core multi-model validation pipeline. Each later stage receives the prior completed stage's structured analysis. Only documented output fields are passed forward; hidden model internals are not exposed.

#### `consult_agent_x` — Innovation & Strategy Analysis

| Property | Value |
|---|---|
| **Agent** | X (Innovation) |
| **Hosted model** | Gemini `gemini-3.5-flash-lite` |
| **Focus** | Competitive positioning vs LangChain, CrewAI, AutoGen, OpenAI Swarm |

**Parameters:** `concept_name`, `concept_description`, `context` (optional), `llm_provider` (BYOK), `api_key` (BYOK), `user_uuid` (optional)

**Returns:** Structured analysis · innovation_score · strategic_value_score · opportunities · risks · recommendation · confidence

---

#### `consult_agent_z` — Ethics & Compliance Review

| Property | Value |
|---|---|
| **Agent** | Z (Guardian) |
| **Hosted model** | Groq `openai/gpt-oss-120b` |
| **Focus** | 21-framework, 4-tier jurisdictional coverage (International / EU / US / ASEAN) |

**Parameters:** Same as X, plus `prior_reasoning` (the prior stage's structured analysis, auto-passed in Trinity)

**Returns:** Structured analysis · ethics_score · safety_score · frameworks_cited · concerns · mitigations · approval status (Z holds veto power)

---

#### `consult_agent_cs` — Security Validation

| Property | Value |
|---|---|
| **Agent** | CS (Security) |
| **Hosted model** | Groq `openai/gpt-oss-120b` |
| **Focus** | 6-stage pipeline, 12-dimension analysis, OWASP Agentic AI Top 10, reasoning-layer audit |

**Parameters:** Same as Z

**Returns:** Structured analysis · security_score · feasibility_score · standards_cited · vulnerabilities · compliance_issues · implementation recommendations

---

#### `run_full_trinity` — Complete X → Z → CS Pipeline

| Property | Value |
|---|---|
| **Tool name** | `run_full_trinity` |
| **Models** | Multi-model, with completed structured stage output passed forward |
| **Focus** | Complete validation with unified assessment |

**Parameters:** `concept_name`, `concept_description`, `context`, `save_to_history`, plus **per-agent BYOK overrides** (`x_provider`/`x_api_key`, `z_provider`/`z_api_key`, `cs_provider`/`cs_api_key`)

**Per-agent BYOK:** You can configure X for Gemini, Z for Anthropic, and CS for OpenAI in a single Trinity call. Provider eligibility, limits, and cost depend on the caller's provider accounts.

**Returns:** All three agent analyses · conflict resolution · synthesized verdict · PROCEED / REVISE / REJECT recommendation · overall_score · action items

---

### Template Library (6)

Prompt-template registry for X / Z / CS agents. Templates are versioned, taggable, and exportable.

| Tool | Purpose |
|---|---|
| `list_prompt_templates` | List with optional filtering by agent / category / tags |
| `get_prompt_template` | Get a specific template by ID — full content + variables |
| `export_prompt_template` | Export a template to Markdown or JSON format |
| `register_custom_template` | ⛔ temporarily unavailable pending owner-scoped storage |
| `import_template_from_url` | ⛔ temporarily unavailable pending owner isolation and URL-fetch hardening |
| `get_template_statistics` | Counts by agent, phase, type |

---

### Coordination Tools (3) — ⛔ TEMPORARILY UNAVAILABLE

**These three tools are disabled and return `COORDINATION_TEMPORARILY_DISABLED` for every caller.**

Records created through them were stored in a shared, unauthenticated namespace; they are no longer readable or writable through the public API. **No validation or built-in template read tool is affected.** They will return only after private, owner-scoped storage ships. Incident reference: `VM-IR-2026-07-28-COORD-01`.

This is a security containment, **not** a paywall and not a tier change — the free-forever pledge is unchanged.

| Tool | Status |
|---|---|
| `coordination_handoff_create` | ⛔ disabled |
| `coordination_handoff_read` | ⛔ disabled |
| `coordination_team_status` | ⛔ disabled |

---

## 🔐 BYOK — Bring Your Own Key

All four Trinity validation tools support **per-tool-call BYOK** (v0.4.5+, hardened in v0.5.0):

- Pass `api_key` + `llm_provider` to override the hosted provider for that stage
- Auto-detect: keys starting with `sk-ant-` → Anthropic (Claude 4.6, 4.7), `sk-` → OpenAI, `gsk_` → Groq
- Supported providers: Gemini, OpenAI, Anthropic, Groq, Mistral, Cerebras, and local Ollama
- Keys are **ephemeral** — never logged, never stored, used only for the single call
- Provider failures use typed per-stage degradation; runtime cross-provider failover remains disabled

See the [BYOK Guide](https://github.com/creator35lwb-web/VerifiMind-PEAS/wiki/BYOK-Guide) for full provider matrix + key-format reference.

---

## 🔌 Connection — Configuration Examples

> **Critical requirements (read these first):**
> - URL **MUST** end with trailing slash: `/mcp/` (not `/mcp`) — programmatic clients that don't follow POST redirects will fail on the 308 without this
> - Transport **MUST** be `streamable-http` (the current MCP spec, NOT legacy `http-sse` or `sse`)
> - POST requests must include both headers: `Content-Type: application/json` AND `Accept: application/json, text/event-stream`

### Claude Code (CLI) — recommended

```bash
claude mcp add -s user verifimind -- npx -y mcp-remote https://verifimind.ysenseai.org/mcp/
```

### Claude Desktop

```json
{
  "mcpServers": {
    "verifimind": {
      "command": "npx",
      "args": ["-y", "mcp-remote", "https://verifimind.ysenseai.org/mcp/"]
    }
  }
}
```

### Cursor / VS Code / Windsurf

`.cursor/mcp.json` or `.vscode/mcp.json`:

```json
{
  "servers": {
    "verifimind": {
      "url": "https://verifimind.ysenseai.org/mcp/",
      "transport": "streamable-http"
    }
  }
}
```

### Custom MCP Client (direct HTTP)

```json
{
  "mcpServers": {
    "verifimind-genesis": {
      "url": "https://verifimind.ysenseai.org/mcp/",
      "transport": "streamable-http"
    }
  }
}
```

For troubleshooting (`403`, `308`, `307`, `404`, `400`, `429`, etc.), see the full [MCP Server Troubleshooting Guide](https://github.com/creator35lwb-web/VerifiMind-PEAS/blob/main/docs/MCP_Server_Troubleshooting_Guide.md).

---

## 🔄 User Flow

### Step 1 — Connect MCP Client

Use one of the configurations above. Restart your client after configuration.

### Step 2 — Client may discover and read Resources

Resource behavior depends on the MCP client. Compatible clients can request the Genesis Master Prompt, a privacy-safe latest-validation summary, and bounded aggregate history statistics.

### Step 3 — Describe your concept

> *"I want to build a meditation app for busy professionals using AI for personalized session recommendations..."*

### Step 4 — LLM calls Trinity tools

The LLM can now call:
- `consult_agent_x` → innovation analysis with competitive positioning
- `consult_agent_z` → ethics review with framework citations
- `consult_agent_cs` → security validation with reasoning-layer audit
- `run_full_trinity` → complete X → Z → CS pipeline with synthesis

### Step 5 — Receive structured report

The LLM presents a comprehensive validation with multi-perspective analysis, scores, framework citations, and actionable recommendations.

---

## 💡 Key Benefits

### For Users

| Benefit | Description |
|---|---|
| **All 13 tools free forever** | Core Tools Always Free pledge (Option B, May 2026) |
| **Multi-model validation** | Different AI models catch different issues — X / Z / CS can use separately configured providers when BYOK overrides are supplied |
| **Per-agent BYOK** | Mix providers per call (X on Gemini, Z on Claude, CS on GPT) |
| **Structured analysis** | Consistent, comparable results across runs |
| **Honest scope** | We publish [The Validation Paradox](https://verifimind.ysenseai.org/research/paradox) acknowledging what we are NOT |
| **Public clock** | [Evaluation Roadmap v1.0](https://verifimind.ysenseai.org/research/evaluation-roadmap) — pre-registered milestones, thresholds, kill-conditions |

### For Developers

| Benefit | Description |
|---|---|
| **MCP standard** | Works with any MCP-compatible client (Claude / Cursor / VS Code / Windsurf / Codex / Agents SDK) |
| **streamable-http** | Current production advertises MCP 2025-11-25; no legacy SSE |
| **Direct HTTP** | Standard REST/HTTP endpoints |
| **Open source** | Full code on [GitHub](https://github.com/creator35lwb-web/VerifiMind-PEAS) |
| **Extensible** | Open-source codebase; Trinity tools support the documented BYOK providers |

---

## 🔗 Endpoints

| Endpoint | Method | Purpose |
|---|---|---|
| `/` | GET | Server info + capabilities |
| `/health` | GET | Health check (version, rate limits, feature flags) |
| `/mcp/` | POST | MCP protocol endpoint (streamable-http) |
| `/mcp/` | GET | SSE stream (requires `mcp-session-id` header) |
| `/mcp/` | DELETE | Session termination |
| `/.well-known/mcp-config` | GET | Auto-discovery config for MCP clients |
| `/setup` | GET | Interactive setup guide (JSON) |
| `/mcp/test?key=<uuid>` | GET | Verify UUID + connection health |
| `/research` | GET | Published research index |
| `/research/paradox` | GET | The Validation Paradox publication |
| `/research/evaluation-roadmap` | GET | Pre-registered Evaluation Roadmap v1.0 (tagged `roadmap-v1.0`) |
| `/research/cowork` | GET | Cowork on 3P analysis (XV) |
| `/library` | GET | Genesis Research Library (20+ papers) |
| `/register` | GET / POST | Early Adopter UUID registration (consent-only) |
| `/optout` | GET | Opt-out + data deletion |
| `/changelog` | GET | Full version history (sanitized) |
| `/privacy` · `/terms` | GET | Policy pages |

Machine-readable index: [`/research/index.json`](https://verifimind.ysenseai.org/research/index.json) (v1.4).

---

## 🎬 Demo Scenario

**User:** *"I want to validate my idea for a decentralized voting system using zero-knowledge proofs."*

**LLM with VerifiMind MCP:**

1. Reads `genesis://config/master_prompt` — understands the X-Z-CS methodology
2. Calls `run_full_trinity` with the concept
3. Receives structured analysis:
   - **X (Innovation):** *"Strong novelty signal vs existing e-voting platforms. Strategic angle: privacy-preserving by default is a clear differentiator. Risks: regulatory acceptance, voter usability."*
   - **Z (Ethics):** *"Privacy frameworks engaged: GDPR Art. 25 (privacy by design), EU AI Act Art. 14 (human oversight). Concerns: identity verification without compromising anonymity is genuinely hard. Frameworks cited: GDPR, EU-AI-Act, NIST-Privacy-Framework."*
   - **CS (Security):** *"6-stage pipeline reveals: (1) Smart contract risks (OWASP A05), (2) cryptographic implementation hazards, (3) supply chain attacks on ZK libraries. Standards cited: OWASP Agentic AI Top 10, NIST SP 800-218 (SSDF)."*
4. **Synthesized verdict:** PROCEED WITH CAUTION — address Z's identity-anonymity tension and CS's smart contract / cryptographic supply chain concerns before launch. Suggested next step: prototype with formal verification + third-party security audit.

---

## 📚 Related Documentation

### Live pages (verifimind.ysenseai.org)
- [`/research`](https://verifimind.ysenseai.org/research) — Published research index
- [`/research/paradox`](https://verifimind.ysenseai.org/research/paradox) — The Validation Paradox (what we are NOT)
- [`/research/evaluation-roadmap`](https://verifimind.ysenseai.org/research/evaluation-roadmap) — Pre-registered milestones, thresholds, kill-conditions
- [`/research/cowork`](https://verifimind.ysenseai.org/research/cowork) — Cowork on 3P strategic analysis
- [`/library`](https://verifimind.ysenseai.org/library) — Genesis Research Library
- [`/changelog`](https://verifimind.ysenseai.org/changelog) — Full version history

### GitHub
- **Repository:** [creator35lwb-web/VerifiMind-PEAS](https://github.com/creator35lwb-web/VerifiMind-PEAS)
- **Wiki:** [VerifiMind PEAS Wiki](https://github.com/creator35lwb-web/VerifiMind-PEAS/wiki)
- **Troubleshooting Guide:** [`docs/MCP_Server_Troubleshooting_Guide.md`](https://github.com/creator35lwb-web/VerifiMind-PEAS/blob/main/docs/MCP_Server_Troubleshooting_Guide.md)
- **Evaluation Roadmap (canonical markdown):** [`docs/research/evaluation-roadmap/roadmap-v1.0.md`](https://github.com/creator35lwb-web/VerifiMind-PEAS/blob/main/docs/research/evaluation-roadmap/roadmap-v1.0.md)
- **MCP Registry:** [registry.modelcontextprotocol.io](https://registry.modelcontextprotocol.io/?q=verifimind)

### Academic
- **Genesis Methodology White Paper:** [10.5281/zenodo.17972751](https://doi.org/10.5281/zenodo.17972751)
- **MACP v2.5 "Loop Engineering":** [10.5281/zenodo.21345820](https://doi.org/10.5281/zenodo.21345820)
- **Original Concept Paper (2025):** [10.5281/zenodo.17645665](https://doi.org/10.5281/zenodo.17645665)

---

**Server Status:** ✅ **LIVE**
**URL:** https://verifimind.ysenseai.org
**Production Version:** v0.5.58
**MCP Registry Package:** 3.35.0
**Availability:** 13 defined / 8 active / 5 temporarily unavailable
**Runtime Failover:** disabled
