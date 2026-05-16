# VerifiMind PEAS MCP Server — Features Guide

**Version:** v0.5.34
**Status:** ✅ **LIVE** at [verifimind.ysenseai.org](https://verifimind.ysenseai.org)
**Last Updated:** May 17, 2026 — Phase 90 "Adoption First"

> All **13 tools free forever** under the [Core Tools Always Free pledge](https://github.com/creator35lwb-web/VerifiMind-PEAS#core-tools-always-free-pledge) (Option B, May 9, 2026).

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
| **Version** | Genesis v4.2 "Sentinel-Verified" |
| **Purpose** | Complete X / Z / CS agent methodology, citation architecture |

### 2. Latest Validation Result

| Property | Value |
|---|---|
| **URI** | `genesis://history/latest` |
| **Format** | JSON |
| **Purpose** | Most recent Trinity validation for reference |

### 3. Complete Validation History

| Property | Value |
|---|---|
| **URI** | `genesis://history/all` |
| **Format** | JSON |
| **Purpose** | Full validation archive with metadata + statistics |

### 4. Project Information

| Property | Value |
|---|---|
| **URI** | `genesis://state/project_info` |
| **Format** | JSON |
| **Purpose** | Architecture overview, agent roles, version + docs links |

---

## 🔧 Tools — 13 Free Forever

### Trinity Validation (4)

The X → Z → CS Trinity is the core multi-model validation pipeline. Each agent sees the prior agents' reasoning (Chain of Thought).

#### `consult_agent_x` — Innovation & Strategy Analysis

| Property | Value |
|---|---|
| **Agent** | X (Innovation) v4.2 |
| **Default model** | Gemini 2.5 Flash (FREE) |
| **Focus** | Competitive positioning vs LangChain, CrewAI, AutoGen, OpenAI Swarm |

**Parameters:** `concept_name`, `concept_description`, `context` (optional), `llm_provider` (BYOK), `api_key` (BYOK), `user_uuid` (optional)

**Returns:** Reasoning chain · innovation_score · strategic_value_score · opportunities · risks · recommendation · confidence

---

#### `consult_agent_z` — Ethics & Compliance Review

| Property | Value |
|---|---|
| **Agent** | Z (Guardian) v4.2 "Sentinel-Verified" |
| **Default model** | Gemini 2.5 Flash |
| **Focus** | 21-framework, 4-tier jurisdictional coverage (International / EU / US / ASEAN) |

**Parameters:** Same as X, plus `prior_reasoning` (auto-passed in Trinity chain)

**Returns:** Reasoning chain · ethics_score · safety_score · frameworks_cited · concerns · mitigations · approval status (Z holds veto power)

---

#### `consult_agent_cs` — Security Validation

| Property | Value |
|---|---|
| **Agent** | CS (Security) v1.1 "Sentinel-Verified" |
| **Default model** | Gemini 2.5 Flash |
| **Focus** | 6-stage pipeline, 12-dimension analysis, OWASP Agentic AI Top 10, reasoning-layer audit |

**Parameters:** Same as Z

**Returns:** Reasoning chain · security_score · feasibility_score · standards_cited · vulnerabilities · compliance_issues · implementation recommendations

---

#### `run_full_trinity` — Complete X → Z → CS Pipeline

| Property | Value |
|---|---|
| **Tool name** | `run_full_trinity` |
| **Models** | Multi-model with Chain of Thought (each agent sees prior reasoning) |
| **Focus** | Complete validation with unified assessment |

**Parameters:** `concept_name`, `concept_description`, `context`, `save_to_history`, plus **per-agent BYOK overrides** (`x_provider`/`x_api_key`, `z_provider`/`z_api_key`, `cs_provider`/`cs_api_key`)

**Per-agent BYOK:** You can run X on Gemini (free), Z on Claude, and CS on GPT in a single Trinity call.

**Returns:** All three agent analyses · conflict resolution · synthesized verdict · PROCEED / REVISE / REJECT recommendation · overall_score · action items

---

### Template Library (6)

Prompt-template registry for X / Z / CS agents. Templates are versioned, taggable, and exportable.

| Tool | Purpose |
|---|---|
| `list_prompt_templates` | List with optional filtering by agent / category / tags |
| `get_prompt_template` | Get a specific template by ID — full content + variables |
| `export_prompt_template` | Export a template to Markdown or JSON format |
| `register_custom_template` | Register a new custom prompt template for X / Z / CS |
| `import_template_from_url` | Import from a URL — GitHub Gist, raw GitHub file, JSON/YAML |
| `get_template_statistics` | Counts by agent, phase, type |

---

### Coordination Tools (3) — 🆕 NEW in v0.5.16

MACP v2.2 coordination layer for multi-agent FLYWHEEL workflows. Same free-forever pledge.

| Tool | Purpose |
|---|---|
| `coordination_handoff_create` | Create a structured MACP v2.2 handoff record between agents |
| `coordination_handoff_read` | Read the most recent coordination handoff(s) with agent filtering |
| `coordination_team_status` | Return current team coordination state — active agents, pending handoffs, last session summary |

---

## 🔐 BYOK — Bring Your Own Key

All Trinity validation tools and template tools support **per-tool-call BYOK** (v0.4.5+, hardened in v0.5.0):

- Pass `api_key` + `llm_provider` to override the default Gemini free-tier
- Auto-detect: keys starting with `sk-ant-` → Anthropic (Claude 4.6, 4.7), `sk-` → OpenAI, `gsk_` → Groq
- Supported providers: Gemini, OpenAI, Anthropic (Claude 4.6/4.7), Groq, Mistral, Cerebras, Ollama, xAI
- Keys are **ephemeral** — never logged, never stored, used only for the single call
- Retry logic with graceful degradation for invalid keys

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

### Step 2 — LLM reads Resources (automatic)

When connected, your LLM can access the Genesis Master Prompt + validation history without explicit prompting.

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
| **Multi-model validation** | Different AI models catch different issues — X / Z / CS run on independent providers when BYOK |
| **Per-agent BYOK** | Mix providers per call (X on Gemini, Z on Claude, CS on GPT) |
| **Structured analysis** | Consistent, comparable results across runs |
| **Honest scope** | We publish [The Validation Paradox](https://verifimind.ysenseai.org/research/paradox) acknowledging what we are NOT |
| **Public clock** | [Evaluation Roadmap v1.0](https://verifimind.ysenseai.org/research/evaluation-roadmap) — pre-registered milestones, thresholds, kill-conditions |

### For Developers

| Benefit | Description |
|---|---|
| **MCP standard** | Works with any MCP-compatible client (Claude / Cursor / VS Code / Windsurf / Codex / Agents SDK) |
| **streamable-http** | Current MCP 2025-03-26 spec; no legacy SSE |
| **Direct HTTP** | Standard REST/HTTP endpoints |
| **Open source** | Full code on [GitHub](https://github.com/creator35lwb-web/VerifiMind-PEAS) |
| **Extensible** | Register custom templates; BYOK for any provider |

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
   - **Z (Ethics, Sentinel-Verified):** *"Privacy frameworks engaged: GDPR Art. 25 (privacy by design), EU AI Act Art. 14 (human oversight). Concerns: identity verification without compromising anonymity is genuinely hard. Frameworks cited: GDPR, EU-AI-Act, NIST-Privacy-Framework."*
   - **CS (Security, Sentinel-Verified):** *"6-stage pipeline reveals: (1) Smart contract risks (OWASP A05), (2) cryptographic implementation hazards, (3) supply chain attacks on ZK libraries. Standards cited: OWASP Agentic AI Top 10, NIST SP 800-218 (SSDF)."*
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
- **MACP & LEP Protocol:** [10.5281/zenodo.18504478](https://doi.org/10.5281/zenodo.18504478)
- **Original Concept Paper (2025):** [10.5281/zenodo.17645665](https://doi.org/10.5281/zenodo.17645665)

---

**Server Status:** ✅ **LIVE**
**URL:** https://verifimind.ysenseai.org
**Version:** v0.5.34
**Phase:** 90 "Adoption First" (monetization on STANDBY — all 13 tools free forever)
