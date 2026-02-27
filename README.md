<div align="center">
  <img src="docs/assets/branding/VerifiMind-PEAS-Icon.png" alt="VerifiMind PEAS" width="200"/>

  # VerifiMind™ PEAS

  **A Validation-First Methodology for Ethical and Secure Application Development**

  Transform your vision into validated, ethical, secure applications through systematic multi-model AI orchestration — from concept to deployment, with human-centered wisdom validation.

  [![Version](https://img.shields.io/badge/version-v0.4.5-blue.svg)](CHANGELOG.md)
  [![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
  [![Status](https://img.shields.io/badge/status-Operational-success.svg)](SERVER_STATUS.md)
  [![Genesis v2.0 DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.17972751.svg)](https://doi.org/10.5281/zenodo.17972751)
  [![MACP & LEP DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.18504478.svg)](https://doi.org/10.5281/zenodo.18504478)
  
  [![API](https://img.shields.io/badge/API-verifimind.ysenseai.org-success)](https://verifimind.ysenseai.org)
  [![MCP Registry](https://img.shields.io/badge/MCP%20Registry-Listed-purple)](https://registry.modelcontextprotocol.io/?q=verifimind)
  [![Smithery](https://img.shields.io/badge/Smithery-Sunset%20March%201-lightgrey)](https://smithery.ai/server/creator35lwb-web/verifimind-genesis)
  [![Landing Page](https://img.shields.io/badge/Landing%20Page-verifimind.io-cyan)](https://verifimind.io)
  [![HuggingFace](https://img.shields.io/badge/🤗%20HuggingFace-Demo-yellow)](https://huggingface.co/spaces/YSenseAI/verifimind-peas)
[![Roadmap](https://img.shields.io/badge/Roadmap-2026-orange)](ROADMAP.md)

</div>

---

## MCP Server: Production Deployed

> **v0.4.5 Live** — 1,750+ verified consultation hours delivered | 662 users | 80%+ MCP integration rate | **BYOK Live: per-tool-call provider override** | **Multi-Model Trinity: X=Gemini, Z=Groq/Llama, CS=Groq/Llama** | `_overall_quality: "full"` — all agents returning real inference | C-S-P methodology pipeline | 10 MCP tools, 19 templates, input sanitization, and CI/CD pipeline. [Health Check](https://verifimind.ysenseai.org/health)

VerifiMind PEAS is now **live and accessible** across multiple platforms:

| Platform | Type | Access | Status |
|----------|------|--------|--------|
| **GCP Cloud Run** | Production API | [verifimind.ysenseai.org](https://verifimind.ysenseai.org) | ✅ LIVE |
| **Official MCP Registry** | Registry Listing | [registry.modelcontextprotocol.io](https://registry.modelcontextprotocol.io/?q=verifimind) | ✅ LISTED |
| **Smithery.ai** | Native MCP | [Install for Claude Desktop](https://smithery.ai/server/creator35lwb-web/verifimind-genesis) | ⚠️ SUNSET March 1, 2026 |
| **Landing Page** | Showcase | [verifimind.io](https://verifimind.io) | ✅ LIVE |
| **Hugging Face** | Interactive Demo | [YSenseAI/verifimind-peas](https://huggingface.co/spaces/YSenseAI/verifimind-peas) | ✅ LIVE |

### Quick Start

> **Important**: Use `streamable-http` transport (not `http-sse`) and always include the trailing slash `/mcp/`.  
> 📖 **[Full Multi-Client Setup & Troubleshooting Guide](docs/MCP_Server_Troubleshooting_Guide.md)**

**Claude Code** (Terminal command — recommended):
```bash
claude mcp add -s user verifimind -- npx -y mcp-remote https://verifimind.ysenseai.org/mcp/
```

**Claude Desktop** (Edit config file — [macOS](~/Library/Application Support/Claude/claude_desktop_config.json) | [Windows](%APPDATA%\Claude\claude_desktop_config.json)):
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

**Cursor / VS Code Copilot** (`.cursor/mcp.json` or `.vscode/mcp.json`):
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

**ChatGPT Codex CLI** (`~/.codex/config.toml`):
```toml
[mcp_servers.verifimind]
url = "https://verifimind.ysenseai.org/mcp/"
transport = "streamable_http"
```
> ⚠️ Codex CLI v0.98.0 has a [known bug](https://github.com/openai/codex/issues/11284) with streamable-http. See [Troubleshooting Guide](docs/MCP_Server_Troubleshooting_Guide.md#-tools-list-empty-codex-cli) for workaround.

**OpenAI Agents SDK** (Python):
```python
from agents.mcp import MCPServerStreamableHttp
server = MCPServerStreamableHttp(name="VerifiMind", params={"url": "https://verifimind.ysenseai.org/mcp/"})
```

🎮 **[Interactive Demo](https://huggingface.co/spaces/YSenseAI/verifimind-peas)**

### Common Mistakes

Based on production log analysis (February 2026), these are the most frequent connection errors new users encounter:

| Mistake | What Happens | Fix |
|---------|-------------|-----|
| **Visiting the URL in a browser** | You see a `406 Not Acceptable` error | This is an API, not a website. Use an MCP client (Claude Desktop, Cursor, etc.) |
| **Missing trailing slash** `/mcp` | `405 Method Not Allowed` | Always use `/mcp/` with the trailing slash |
| **Using GET instead of POST** | `400 Bad Request` | MCP protocol requires POST requests with JSON-RPC body |
| **Using `http-sse` transport** | Connection fails | Use `streamable-http` transport (not `http-sse`) |
| **Connecting to Smithery proxy** | May stop working March 1, 2026 | Use the direct URL: `https://verifimind.ysenseai.org/mcp/` |

> 💡 **Quick test**: Run `curl https://verifimind.ysenseai.org/health` — if you see `"status": "healthy"`, the server is up. Then configure your MCP client using the Quick Start instructions above.

> ⚠️ **Smithery.ai Sunset Notice**: Smithery.ai's legacy architecture will be sunset on **March 1, 2026**. If you are currently connecting via `server.smithery.ai`, please switch to the direct URL `https://verifimind.ysenseai.org/mcp/` before that date. All Quick Start instructions above already use the direct URL.

### API Keys & BYOK (v0.4.5+)

| Platform | API Key Required | Notes |
|----------|------------------|-------|
| **GCP Server** / **MCP Registry** | ❌ No (default) | Server-side configured, ready to use |
| **GCP Server** (BYOK) | ✅ Optional | Pass `api_key` + `llm_provider` per tool call to use your own key |
| **HuggingFace Demo** | ❌ No | Server-side configured |
| **Smithery** | ✅ Yes (BYOK) | Bring Your Own Key (sunset March 1, 2026) |

**v0.4.5 BYOK Live** — You can now override the default provider on any individual tool call by passing `api_key` and `llm_provider` parameters. The server auto-detects key format (e.g., `gsk_` → Groq, `sk-ant-` → Anthropic, `sk-` → OpenAI). If no key is provided, the server uses its default Gemini/Groq configuration. Triple-validated by Manus AI (6/6), Claude Code (6/6), and CI (175 tests). [PR #55](https://github.com/creator35lwb-web/VerifiMind-PEAS/pull/55)

**Supported BYOK Providers**: Gemini, Groq, OpenAI, Anthropic, Mistral, Ollama, Perplexity

**Get FREE API Keys**: [Google AI Studio](https://aistudio.google.com/apikey) | [Groq Console](https://console.groq.com/keys)

### MCP Tools (10 Total)

The VerifiMind MCP server exposes 10 tools organized into two categories: **Core Validation** (4 tools) and **Template Management** (6 tools, added in v0.4.0).

| Tool | Category | Description |
|------|----------|-------------|
| `consult_agent_x` | Core | Innovation & Strategy analysis (Gemini FREE) |
| `consult_agent_z` | Core | Ethics & Safety review with VETO power |
| `consult_agent_cs` | Core | Security & Feasibility validation |
| `run_full_trinity` | Core | Complete X → Z → CS validation pipeline |
| `list_prompt_templates` | Template | List/filter templates by agent, category, tags |
| `get_prompt_template` | Template | Retrieve template by ID with full content |
| `export_prompt_template` | Template | Export to Markdown or JSON format |
| `register_custom_template` | Template | Create custom prompt templates |
| `import_template_from_url` | Template | Import from GitHub Gist or raw URL |
| `get_template_statistics` | Template | Registry statistics and usage data |

### Template Library (6 Libraries, 19 Templates)

v0.4.0 introduced the **Unified Prompt Template** system with pre-built, versioned YAML templates aligned to Genesis Methodology phases.

| Library | Agent | Genesis Phase | Templates |
|---------|-------|---------------|:---------:|
| `startup_validation` | X | Phase 1: Conceptualization | 3 |
| `market_research` | X | Phase 1: Conceptualization | 3 |
| `ethics_review` | Z | Phase 2: Critical Scrutiny | 3 |
| `security_audit` | CS | Phase 3: External Validation | 3 |
| `technical_review` | CS | Phase 3: External Validation | 3 |
| `trinity_synthesis` | ALL | Phase 4: Synthesis | 4 |

Templates support custom variables with type validation, export to Markdown/JSON, import from URL, and version control with changelogs. Users can also register custom templates at runtime.

### Security Features (v0.3.5+)

All MCP tools include **input sanitization** to protect against prompt injection, XSS, null byte injection, and input length abuse. The system detects 15+ prompt injection patterns and logs suspicious activity without blocking legitimate requests.

### CI/CD Pipeline

Automated testing and security scanning runs on every push to `main` via GitHub Actions:
- Unit tests and integration tests (Python 3.11)
- Security scanning with Bandit (static analysis) and Safety (dependency audit)
- Coverage reporting with configurable thresholds

---

## 📊 Verified Service Metrics

> Cross-validated by FLYWHEEL TEAM (CSO R — Manus AI, COO AY — Antigravity) against raw GCP Cloud Run logs. Scrapers excluded. Conservative rounding applied.

| Metric | Value | Methodology |
|--------|-------|-------------|
| **Verified Consultation Hours** | **1,750+** (all-time) | Session duration: first-to-last request per user per day. Scrapers excluded via User-Agent audit classification. |
| **Total Users** | **662** | Unique users across all platforms |
| **MCP Integration Rate** | **80%+** | Programmatic (Node.js + Python) vs. browser traffic by User-Agent header |
| **MCP Tools Available** | **10** (4 core + 6 template) | Core: consult_agent_x, consult_agent_z, consult_agent_cs, run_full_trinity |
| **Multi-Model Providers** | **X=Gemini, Z=Groq, CS=Groq** | Per-agent provider routing for optimal structured output |
| **BYOK Live** | **Per-tool-call override** | Users can pass own API key + provider on any call (v0.4.5+) |
| **Trinity Quality** | **`_overall_quality: "full"`** | All 3 agents returning real inference (v0.4.4+) |

### Adoption Trajectory (Flying Hours ✈️)

| Week | Period | Weekly Hours | Cumulative Hours | Users |
|------|--------|-------------|-----------------|-------|
| W02 | Jan 06–12 | 38.0h | 38h | 21 |
| W03 | Jan 13–19 | 115.3h | 153h | 55 |
| W04 | Jan 20–26 | 262.4h | 416h | 96 |
| W05 | Jan 27–Feb 02 | 309.6h | 725h | 105 |
| W06 | Feb 03–09 | 425.4h | 1,151h | 117 |
| W07 | Feb 10–16 | 409.0h | 1,198h | 172 |
| W08 | Feb 16–22 | 404.8h | 1,556h | 143 |
| W09 | Feb 23–Mar 1 | 198.5h | 1,755h | 46 |

### Traffic Classification Breakdown

| Category | Share | Hours | Description |
|----------|-------|-------|-------------|
| **MCP Client** | 80.3% | 1,409.5h | Tool users via Node.js/Python MCP clients |
| **Human Browser** | 4.7% | 82.9h | Direct web visitors (HuggingFace, landing page) |
| **API Integration** | 15.0% | 262.3h | Programmatic API consumers |
| **Scraper** | — | Excluded | Excluded from verified total |

> **Verified Total** = MCP + Browser + API. Scrapers excluded. Owner/Bot excluded.

### Client Integration by User-Agent

| Client | Share | Description |
|--------|-------|-------------|
| Node.js | 65.3% | MCP clients via Claude Code, VS Code, Cursor |
| Python SDK | 20.3% | Python-based MCP integrations |
| Browser | 8.5% | Direct web visitors |
| Claude/Anthropic | 4.5% | Claude Desktop / Claude Code native clients |
| Other | 1.4% | Miscellaneous clients |

> **Key Insight:** Over 85% of all traffic is machine-to-machine MCP integration, confirming VerifiMind PEAS is used as an integrated tool in developer workflows — not merely visited as a web demo. This traffic is invisible to traditional web analytics platforms like SimilarWeb.

> **Data Source:** GCP Cloud Run HTTP Load Balancer logs. Audit classification via User-Agent analysis. Owner traffic excluded. Scraper traffic excluded via conservative classification. Full methodology documented in internal reports (Report 024). Last updated: 2026-02-26.

---

## 🌟 What is VerifiMind-PEAS?

**VerifiMind-PEAS is a methodology framework**, not a code generation platform.

We provide a systematic approach to **multi-model AI validation** that ensures your applications are:
- ✅ **Validated** through diverse AI perspectives
- ✅ **Ethical** with built-in wisdom validation
- ✅ **Secure** with systematic vulnerability assessment
- ✅ **Human-centered** with you as the orchestrator

### **What We Provide**

**Core Methodology**:
- ✅ **Genesis Methodology**: Systematic 5-step validation process
- ✅ **X-Z-CS RefleXion Trinity**: Specialized AI agents (Innovation, Ethics, Security)
- ✅ **Genesis Master Prompts**: Stateful memory system for project continuity
- ✅ **Comprehensive Documentation**: Guides, tutorials, case studies

**Integration Support**:
- ✅ Works with **any LLM** (Claude, GPT, Gemini, Kimi, Grok, Qwen, etc.)
- ✅ Integration guides for **Claude Code**, **Cursor**, and generic LLMs
- ✅ No installation required - just read and apply!

### **What We Do NOT Provide**

**We are NOT**:
- ❌ A code generation platform
- ❌ A web interface for application scaffolding
- ❌ A no-code platform integration
- ❌ An automated deployment system

**We ARE**:
- ✅ A methodology you apply with your existing AI tools
- ✅ A framework for systematic validation
- ✅ A community of practice for ethical AI development

---

## 🎯 Latest Achievements

### v0.4.5 — BYOK Live: Per-Tool-Call Provider Override (February 28, 2026)

The v0.4.5 release introduces **Bring Your Own Key (BYOK) Live** — users can now pass their own `api_key` and `llm_provider` on any individual tool call to override the server's default provider. The server auto-detects key format from prefix patterns (`gsk_` → Groq, `sk-ant-` → Anthropic, `sk-` → OpenAI, `AIza` → Gemini) and creates ephemeral provider instances per request. Keys are never stored — used once and discarded. When no BYOK key is provided, the server falls back to its default Gemini/Groq configuration seamlessly. Response metadata includes `_byok: true/false` for full transparency. Triple-validated by Manus AI (6/6 pass), Claude Code (6/6 pass), and CI pipeline (175 tests). [PR #55](https://github.com/creator35lwb-web/VerifiMind-PEAS/pull/55)

### v0.4.4 — Multi-Model Trinity: Full Quality (February 27, 2026)

The v0.4.4 release achieves **`_overall_quality: "full"`** — all three Trinity agents now return real AI inference with zero fallback defaults. Agent X (Innovator) runs on Gemini 2.5 Flash for creative analysis, while Agent Z (Guardian) and Agent CS (Validator) are routed to Groq/Llama-3.3-70b for reliable structured JSON output. The GroqProvider was upgraded with the full C-S-P extraction pipeline: `strip_markdown_code_fences()`, `_extract_best_json()` with field-overlap scoring, `_merge_json_objects()`, and `_fill_schema_defaults()`. Quality markers (`_inference_quality`, `_agent_chain_status`, `_overall_quality`) are embedded in every response for full transparency. 16 PRs merged (#33–#48), all CI passed. 12 new unit tests added.

### v0.4.3 — C-S-P Pipeline & System Notice (February 27, 2026)

The v0.4.3 release implements the **C-S-P (Compression–State–Propagation) methodology** from the GodelAI framework, applied directly to the Trinity pipeline. Robust JSON extraction with `raw_decode()` and field-overlap scoring replaces brittle regex parsing. State validation checkpoints between Trinity stages prevent garbage propagation. System notice (`_system_notice`) field added to all tool responses for transparent user communication. Gemini JSON mode (`response_mime_type: "application/json"`) tested and integrated.

### v0.4.2 — Mock Mode Resolved & Transparent Disclosure (February 26, 2026)

The v0.4.2 release resolves the **mock mode issue** that affected all Trinity consultations from v0.4.0–v0.4.1. The root cause was a deprecated Gemini model endpoint (`gemini-2.0-flash` → `gemini-2.5-flash`). A transparent disclosure was published ([Discussion #31](https://github.com/creator35lwb-web/VerifiMind-PEAS/discussions/31)) acknowledging the issue and explaining the "Structural Scaffolding Value" thesis — even in mock mode, the framework provided value by forcing structured multi-perspective reasoning. CodeQL security alerts reduced from 13 to 0.

### Genesis v3.1 — CS Agent Multi-Stage Verification Protocol (February 2026)

Genesis v3.1 introduces a **4-Stage Security Verification Protocol** for the CS Agent: Detection → Self-Examination (MANDATORY) → Severity Rating → Human Review. Self-examination is mandatory — every finding must be proven AND disproven before escalation. No auto-fixes. Human oversight is always the final stage. This is a workflow enhancement only — zero code changes to the server foundation. Inspired by [Claude Code Security](https://docs.anthropic.com/en/docs/claude-code/security) principles. Full protocol documentation: [`docs/security/`](docs/security/).

### v0.4.1 — Markdown-First Output & Smithery Sunset (February 14, 2026)

The v0.4.1 release introduces **Markdown-first output** with content negotiation — clients can now request `Accept: text/markdown` to receive validation reports in Markdown format (80% token reduction vs JSON). This aligns with the broader industry shift toward Markdown as the agent-native communication format (see [Cloudflare: Markdown for Agents](https://blog.cloudflare.com/markdown-for-agents/)). All 13 Smithery proxy URL references were removed from server endpoints in preparation for the Smithery.ai legacy architecture sunset on March 1, 2026. The `pdf_generator.py` is deprecated — retained only for Zenodo DOI and enterprise compliance. Server version bumped with 155 total tests passing at 54.27% coverage.

### v0.4.0 — Unified Prompt Templates (January 30, 2026)

The v0.4.0 release introduced the **Unified Prompt Template** system, adding 6 new MCP tools (10 total) and 19 pre-built YAML templates organized across 6 libraries. Templates are aligned to Genesis Methodology phases, support custom variables with type validation, and can be exported to Markdown or JSON. Users can import templates from GitHub Gists or raw URLs, and register custom templates at runtime. This release also includes the MACP v2.0 specification (DOI: [10.5281/zenodo.18504478](https://doi.org/10.5281/zenodo.18504478)) and the L (GODEL) Ethical Operating Framework v1.1.

### v0.3.5 — Security Hardening (January 30, 2026)

Comprehensive input sanitization was added to all MCP tools, protecting against prompt injection (15+ patterns), XSS attacks, null byte injection, and input length abuse. All 29 sanitization unit tests pass. A CI/CD pipeline was established with GitHub Actions for automated testing and security scanning (Bandit, Safety) on every push.

### Standardization Protocol v1.0 (December 2025)

The standardization phase generated **57 complete Trinity validation reports** across seven domains including financial services, healthcare, education, and civic technology. By combining Gemini’s free tier for innovation analysis with Claude for ethics and security validation, we achieved sustainable costs (~$0.003 per validation) while maintaining research-grade quality. The 65% veto rate confirms our ethical safeguards work as designed.

### **Key Metrics**

| Metric | Value | Significance |
|--------|-------|-------------|
| **MCP Tools** | 10 | 4 core validation + 6 template management |
| **Templates** | 19 | Pre-built across 6 libraries |
| **Validation Reports** | 57 | Proof of methodology at scale |
| **Success Rate** | 95% | Reliable, production-ready system |
| **Cost per Validation** | ~$0.003 | Sustainable for solo developers |
| **Veto Rate** | 65% | Strong ethical safeguards working |
| **LLM Providers** | 7 | Gemini, OpenAI, Anthropic, Groq, Mistral, Ollama, Perplexity |
| **Multi-Model Routing** | X=Gemini, Z=Groq, CS=Groq | Per-agent provider optimization |
| **Trinity Quality** | `_overall_quality: "full"` | All agents returning real inference (v0.4.4+) |
| **Total Users** | 662 | Unique users across all platforms |

### **Version History**

| Version | Date | Highlights |
|---------|------|------------|
| **v0.4.5** | Feb 28, 2026 | **BYOK Live**: per-tool-call provider override, auto-detect key format, triple-validated |
| **v0.4.4** | Feb 27, 2026 | Multi-Model Trinity (`_overall_quality: "full"`), X=Gemini, Z/CS=Groq |
| **v0.4.3** | Feb 27, 2026 | C-S-P pipeline, system notice, robust JSON extraction |
| **v0.4.2** | Feb 26, 2026 | Mock mode resolved, transparent disclosure, CodeQL 13→0 |
| **Genesis v3.1** | Feb 2026 | CS Agent 4-Stage Verification Protocol, zero code changes |
| **v0.4.1** | Feb 14, 2026 | Markdown-first output, Smithery URL removal, PDF deprecated |
| **v0.4.0** | Jan 30, 2026 | Unified Prompt Templates, 6 new tools, MACP v2.0 |
| **v0.3.5** | Jan 30, 2026 | Input sanitization, CI/CD pipeline |
| **v0.3.2** | Jan 29, 2026 | Gemini 2.5-flash model update |
| **v0.3.1** | Jan 29, 2026 | Smart Fallback, rate limiting, per-agent providers |
| **v0.3.0** | Jan 28, 2026 | BYOK multi-provider support (7 providers) |
| **v0.2.0** | Dec 25, 2025 | Multi-platform distribution |
| **v0.1.0** | Dec 21, 2025 | Initial MCP server deployment |

**[View Full Changelog →](CHANGELOG.md)** | **[View 57 Trinity Validation Reports →](validation_archive/)**

---

## 📚 Case Studies: Real-World Applications

VerifiMind-PEAS has been applied to validate real-world projects from concept to production. These case studies demonstrate the practical application of our methodology.

### MarketPulse v5.0

**AI-Powered Daily Market Intelligence for Value Investors**

| Attribute | Value |
|-----------|-------|
| **Project** | [MarketPulse](https://github.com/creator35lwb-web/MarketPulse) |
| **Version** | 5.0 (Production Ready) |
| **Validation Date** | January 2026 |
| **Status** | ✅ VALIDATED |

MarketPulse is an open-source n8n workflow that delivers comprehensive daily market briefings for value investors. It demonstrates the "Bootstrapper's Edge" philosophy—leveraging free-tier infrastructure and open-source AI to build persistent, high-value intelligence systems at minimal cost.

**Trinity Validation Results:**
- **X-Agent (Innovation):** ✅ Approved - Democratizes financial intelligence through clever synthesis of free tools.
- **Z-Agent (Ethics):** ✅ Approved - Includes clear disclaimers that this is not financial advice.
- **CS-Agent (Security):** ✅ Approved - Secure credential management through n8n's built-in system.

📖 **[Read the Full MarketPulse Case Study →](docs/case-studies/MarketPulse_Case_Study.md)**

---

## 💡 Why VerifiMind-PEAS?

### **The Problem: Single-Model Bias**

**Most AI development relies on a single model** (e.g., only Claude, only GPT).

**This creates**:
- 🔴 **Single-model bias**: One perspective, blind spots
- 🔴 **Inconsistent quality**: No systematic validation
- 🔴 **Ethical gaps**: No wisdom validation
- 🔴 **Security vulnerabilities**: No systematic security review

### **The Solution: Multi-Model Orchestration**

**VerifiMind-PEAS orchestrates multiple AI models** for diverse perspectives:

1. **X Intelligent Agent** (Innovation): Generates creative solutions
2. **Z Guardian Agent** (Ethics): Validates ethical alignment
3. **CS Security Agent** (Security): Identifies vulnerabilities

**By synthesizing diverse AI perspectives under human direction**, you achieve:
- ✅ **Objective validation**: Multiple models check each other
- ✅ **Ethical alignment**: Wisdom validation built-in
- ✅ **Security assurance**: Systematic vulnerability assessment
- ✅ **Human-centered**: You orchestrate, AI assists

### **Honest Positioning**

**Multi-model orchestration is not new.** Developers have been using multiple AI models (Claude, GPT, Gemini) together for years. What makes VerifiMind-PEAS different is **how we structure this orchestration** through the **X-Z-CS RefleXion Trinity** and **Genesis Master Prompts**.

**Our genuine novelty**:
- ✅ **X-Z-CS RefleXion Trinity**: Specialized validation roles (Innovation, Ethics, Security) with no prior art found
- ✅ **Genesis Master Prompts**: Stateful memory system for project continuity across multi-model workflows
- ✅ **Wisdom validation**: Ethical alignment and cultural sensitivity as first-class concerns
- ✅ **Human-at-center**: You orchestrate (not just review), AI assists (not automates)

**What we build on** (established practices):
- Multi-model usage (common practice since 2023)
- Agent-based architectures (LangChain, AutoGen, CrewAI)
- Human-in-the-loop validation (industry standard)

**Our contribution**: Transforming ad-hoc multi-model usage into **systematic validation methodology** with **wisdom validation** and **human-centered orchestration**.

### **Competitive Positioning: Complementary, Not Competing**

VerifiMind-PEAS operates as a **validation layer ABOVE execution frameworks**. We don't replace LangChain, AutoGen, or CrewAI — we complement them.

**Think of it this way**:
- **Execution frameworks** (LangChain, AutoGen, CrewAI): "How to build and run AI agents"
- **VerifiMind-PEAS**: "How to validate what those agents produce"

**Comparison Table**:

| **Framework** | **Layer** | **Focus** | **Human Role** | **VerifiMind-PEAS Relationship** |
|---------------|-----------|-----------|----------------|----------------------------------|
| **LangChain** | Execution | Tool integration, chains | In-loop (reviewer) | **Validates LangChain outputs** for ethics + security |
| **AutoGen** | Execution | Multi-agent automation | In-loop (supervisor) | **Validates AutoGen conversations** for wisdom alignment |
| **CrewAI** | Execution | Role-based agents | In-loop (manager) | **Validates CrewAI results** for cultural sensitivity |
| **OpenAI Swarm** | Execution | Lightweight handoffs | In-loop (router) | **Provides memory layer** via Genesis Master Prompts |
| **VerifiMind-PEAS** | **Validation** | **Wisdom validation** | **At-center (orchestrator)** | **Validation layer above all execution frameworks** |

**Industry focus**: Code execution, task automation, agent coordination  
**VerifiMind-PEAS focus**: **Wisdom validation, ethical alignment, human-centered orchestration**

**Result**: Use VerifiMind-PEAS **with** LangChain/AutoGen/CrewAI to add validation layer. We complement, not compete.

---

## 🔄 How It Works: The Genesis Methodology

<p align="center">
  <img src="docs/assets/diagrams/Genesis Methodology 5-Step Process.png" alt="Genesis Methodology 5-Step Process" width="800"/>
</p>

The **Genesis Methodology** is a systematic 5-step process for multi-model AI validation:

### **Step 1: Initial Conceptualization**
- **Human** defines the problem or vision
- **AI** (X Intelligent Agent) generates initial concepts and solutions
- **Output**: Initial concept with creative possibilities

### **Step 2: Critical Scrutiny**
- **AI** (Z Guardian Agent) validates ethical alignment
- **AI** (CS Security Agent) identifies security vulnerabilities
- **Multiple models** challenge and validate each other
- **Output**: Validated concept with ethical and security considerations

### **Step 3: External Validation**
- **Independent AI** analysis confirms systematic approach
- **Research** validates against academic literature and industry best practices
- **Output**: Externally validated concept with evidence

### **Step 4: Synthesis**
- **Human** orchestrates final synthesis
- **Human** makes decisions based on AI perspectives
- **Human** documents decisions in Genesis Master Prompt
- **Output**: Final decision with documented rationale

### **Step 5: Iteration**
- **Recursive refinement** based on feedback
- **Continuous improvement** through multiple cycles
- **Genesis Master Prompt** updated with learnings
- **Output**: Refined concept ready for next phase

**This process ensures every output is validated through diverse AI perspectives before final human approval.**

---

## 🏗️ Architecture: The X-Z-CS RefleXion Trinity

<p align="center">
  <img src="docs/assets/diagrams/AI Council Multi-Model Orchestration and Validation.png" alt="AI Council Architecture" width="800"/>
</p>

VerifiMind-PEAS implements a **multi-model orchestration** architecture where:

### **Human Orchestrator** (You)
- **Role**: Center of decision-making
- **Responsibility**: Synthesize AI perspectives, make final decisions
- **Tools**: Genesis Master Prompts, integration guides

### **X Intelligent Agent** (Analyst/Researcher)
- **Role**: Market intelligence and feasibility analysis
- **Focus**: Research, technical feasibility, market analysis
- **Models**: Perplexity, GPT-4, Gemini (research-focused)
- **Note**: X agent focuses on analytical research and validation

### **Z Guardian Agent** (Ethics)
- **Role**: Compliance and human-centered design protector
- **Focus**: Ethical alignment, cultural sensitivity, accessibility
- **Models**: Claude, GPT-4 (ethics-focused)

### **CS Security Agent** (Security)
- **Role**: Cybersecurity protection layer
- **Focus**: Vulnerability assessment, threat modeling, security best practices
- **Models**: GPT-4, Claude (security-focused)
- **Genesis v3.1**: 4-Stage Verification Protocol — Detection → Self-Examination → Severity Rating → Human Review ([docs](docs/security/CS_Agent_Multi_Stage_Verification_Protocol.md))

**This architecture synergizes diverse AI perspectives under human direction for objective, validated results.**

### **About Y Agent (Innovator)**

You may see **Y Agent (Innovator)** in some diagrams. This agent is part of the broader **YSenseAI™** project, which focuses on innovation and strategic vision. The complete ecosystem includes:

- **Y Agent (YSenseAI™)**: Innovation and creative ideation
- **X Agent (VerifiMind-PEAS)**: Research and analytical validation
- **Z Agent (VerifiMind-PEAS)**: Ethical compliance
- **CS Agent (VerifiMind-PEAS)**: Security validation

**VerifiMind-PEAS focuses on the X-Z-CS Trinity** (Research, Ethics, Security), while **YSenseAI™ provides the Y Agent** (Innovation). Together, they form a complete validation framework.

---

## 💡 The Concept: Crystal Balls Inside the Black Box

<p align="center">
  <img src="docs/assets/diagrams/Crystall Balls inside Black Box.png" alt="Crystal Balls Inside Black Box" width="600"/>
</p>

Instead of treating AI as an opaque "black box," VerifiMind-PEAS places multiple "crystal balls" (diverse AI models) inside the box to illuminate the path forward.

**Each crystal ball represents a specialized AI agent with a unique perspective**:

- **Y (Innovator)**: Generates creative concepts and strategic vision (from YSenseAI™)
- **X (Analyst)**: Researches feasibility and market intelligence (from VerifiMind-PEAS)
- **Z (Guardian)**: Ensures ethical compliance and safety (from VerifiMind-PEAS)
- **CS (Validator)**: Validates claims against external evidence and security best practices (from VerifiMind-PEAS)

**Note**: The diagram shows the complete 4-agent system (Y-X-Z-CS). VerifiMind-PEAS specifically implements the **X-Z-CS Trinity**, while **Y Agent comes from YSenseAI™**.

**By orchestrating these diverse perspectives under human direction**, we achieve objective, validated results that no single AI model can provide.

---

## 🚀 Getting Started

### **No Installation Required!**

**VerifiMind-PEAS is a methodology, not software.** You don't need to install anything!

### **Step 1: Read the Genesis Master Prompt Guide**

**Start here**: [Genesis Master Prompt Guide](docs/guides/GENESIS_MASTER_PROMPT_GUIDE.md)

**This comprehensive guide teaches you**:
- What is a Genesis Master Prompt?
- Why Genesis Master Prompts matter
- Step-by-step tutorial (meditation app example)
- Real-world validation (87-day journey)
- Advanced techniques
- Common mistakes and solutions

**Time**: 30 minutes to read, lifetime of value

### **Step 2: Choose Your AI Tool**

**VerifiMind-PEAS works with any LLM**:
- ✅ **Claude** (Anthropic)
- ✅ **GPT-4** (OpenAI)
- ✅ **Gemini** (Google)
- ✅ **Kimi** (Moonshot AI)
- ✅ **Grok** (xAI)
- ✅ **Qwen** (Alibaba)
- ✅ **Any other LLM**

**Recommended**: Use at least 2-3 LLMs for multi-model validation.

### **Step 3: Follow Integration Guides**

**Choose your integration approach**:

1. **[Claude Code Integration](docs/guides/CLAUDE_CODE_INTEGRATION.md)**
   - Paste GitHub repo URL → Claude applies methodology
   - Best for: Code-focused projects

2. **[Cursor Integration](docs/guides/CURSOR_INTEGRATION.md)**
   - Paste GitHub repo URL → Cursor applies methodology
   - Best for: IDE-integrated development

3. **[Generic LLM Integration](docs/guides/GENERIC_LLM_INTEGRATION.md)**
   - Copy-paste Genesis Master Prompt → Any LLM applies methodology
   - Best for: Platform-agnostic approach

### **Step 4: Start Your First Project**

**Follow the tutorial in the Genesis Master Prompt Guide**:
1. Create your Genesis Master Prompt
2. Start first session with X Intelligent Agent (innovation)
3. Validate with Z Guardian Agent (ethics)
4. Validate with CS Security Agent (security)
5. Synthesize perspectives and make decision
6. Update Genesis Master Prompt
7. Repeat!

**Example projects**:
- Meditation timer app (tutorial example)
- AI-powered attribution system (YSenseAI™)
- Multi-model validation framework (VerifiMind-PEAS itself)

---

## 💻 Reference Implementation (Optional)

**VerifiMind-PEAS is a methodology framework** that can be applied with any LLM or tool. **You do NOT need code to use VerifiMind-PEAS.**

However, for developers who want to see a complete implementation or need a starter template, we provide a **Python reference implementation**.

### **What's Included**

The reference implementation demonstrates how to automate the X-Z-CS Trinity:

- **X Intelligent Agent**: Innovation engine for business viability analysis
- **Z Guardian Agent**: Ethical compliance validation (GDPR, UNESCO AI Ethics)
- **CS Security Agent**: Security validation with Socratic questioning engine (Concept Scrutinizer)
- **Orchestrator**: Multi-agent coordination and conflict resolution
- **PDF Report Generator**: Audit trail documentation

**Status**: 85% production-ready (Phase 1-2 complete, Phase 3-6 in progress)

### **Three Ways to Use VerifiMind-PEAS**

**Option 1: Apply Methodology Manually** (No code required)
- Use Genesis Master Prompts with your preferred LLM
- Follow integration guides (Claude Code, Cursor, Generic LLM)
- Orchestrate X-Z-CS validation yourself
- **Best for**: Non-technical users, custom workflows

**Option 2: Use Reference Implementation** (Python developers)
- Clone repository: `git clone https://github.com/creator35lwb-web/VerifiMind-PEAS`
- Install dependencies: `pip install -r requirements.txt`
- Run validation: `python verifimind_complete.py --idea "Your app idea"`
- **Best for**: Developers who want automation, learning how X-Z-CS works

**Option 3: Extend Reference Implementation** (Contributors)
- Fork repository and add new agents, validation engines, or integrations
- Submit pull request to share with community
- **Best for**: Researchers, advanced developers, open-source contributors

### **Documentation**

- **[Code Foundation Completion Summary](docs/CODE_FOUNDATION_COMPLETION_SUMMARY.md)**: Current implementation status (85% complete)
- **[Code Foundation Analysis](docs/CODE_FOUNDATION_ANALYSIS.md)**: Technical architecture and design decisions
- **[Requirements](requirements.txt)**: Python dependencies

### **Important Notes**

**The reference implementation is**:
- ✅ A **learning resource** (see how methodology translates to code)
- ✅ A **starter template** (fork and customize for your needs)
- ✅ A **validation proof** (shows methodology is executable)

**The reference implementation is NOT**:
- ❌ A required component (you can apply methodology without code)
- ❌ A production-ready SaaS (this is a reference, not a hosted service)
- ❌ The only way to implement (you can use other languages, tools, approaches)

**Remember**: VerifiMind-PEAS is a **methodology framework**. The code is ONE way to implement it, not THE way.

---

## 📚 Documentation

### **Core Methodology**

- **[Genesis Methodology White Paper v1.1](docs/white_paper/Genesis_Methodology_White_Paper_v1.1.md)**: Comprehensive academic documentation
- **[Genesis Master Prompt Guide](docs/guides/GENESIS_MASTER_PROMPT_GUIDE.md)**: Practical implementation guide
- **[X-Z-CS RefleXion Trinity Master Prompts](reflexion-master-prompts-v1.1.md)**: Specialized agent prompts (Chinese)

### **Integration Guides**

- **[Claude Code Integration](docs/guides/CLAUDE_CODE_INTEGRATION.md)**
- **[Cursor Integration](docs/guides/CURSOR_INTEGRATION.md)**
- **[Generic LLM Integration](docs/guides/GENERIC_LLM_INTEGRATION.md)**

### **Documentation Best Practices**

**VerifiMind-PEAS includes a comprehensive documentation framework** for managing context across multi-model LLM workflows.

**Three-Layer Architecture**:
1. **Genesis Master Prompt** (Project Memory) - Single source of truth, updated after every session
2. **Module Documentation** (Deep Context) - Feature-specific details organized in `/docs`
3. **Session Notes** (Iteration History) - Complete audit trail of decisions and insights

**Why This Matters**:
- ✅ **Context persistence** across LLM sessions (no manual re-entry)
- ✅ **Platform-agnostic** (works with Claude, GPT, Gemini, Kimi, Grok, Qwen, etc.)
- ✅ **Multi-model workflows** (consistent context for X-Z-CS validation)
- ✅ **Complete audit trail** (track every decision and iteration)

**Learn more**: **[Documentation Best Practices Guide](docs/guides/DOCUMENTATION_BEST_PRACTICES.md)**

**Templates**:
- [Genesis Master Prompt Template](templates/GenesisMasterPromptTemplate.md)
- [Module Documentation Template](templates/ModuleDocumentationTemplate.md)
- [Session Notes Template](templates/SessionNotesTemplate.md)

### **Case Studies**

- **[YSenseAI™ 87-Day Journey](https://journey.manus.space/)** (Landing Pages): Real-world validation of Genesis Methodology
- **[VerifiMind-PEAS Development](https://verifimind.io/)** (Landing Pages): Meta-application of methodology to itself

### **Operations & Troubleshooting**

- **[MCP Server Troubleshooting Guide](docs/MCP_Server_Troubleshooting_Guide.md)**: Common HTTP status codes, configuration errors, and solutions
- **[GCP Monitoring Setup Guide](docs/GCP_Monitoring_Setup_Guide.md)**: Dashboard, alerting, and log query reference
- **[GCP Deployment Guide](docs/GCP_DEPLOYMENT_GUIDE.md)**: Cloud Run deployment instructions
- **[Server Status](SERVER_STATUS.md)**: Current operational status

### **Additional Resources**

- **[Roadmap](ROADMAP.md)**: Strategic development plan
- **[Changelog](CHANGELOG.md)**: Detailed version history
- **[Contributing Guidelines](CONTRIBUTING.md)**: How to contribute
- **[Zenodo Publication Guide](docs/white_paper/Zenodo-Publication-Guide-v1.1.md)**: Defensive publication documentation
- **[MACP v2.0 Specification](docs/MACP_v2.0_Specification.md)**: Multi-Agent Communication Protocol
- **[L (GODEL) Ethical Operating Framework](docs/L_GODEL_Ethical_Operating_Framework.md)**: Ethical constitution for AI agents

---

## 🔧 Troubleshooting

### ⚠️ Common Mistakes (Read This First!)

Based on real production logs, **83.7% of all errors** come from three configuration mistakes. If you are having trouble connecting, check these first:

#### Mistake #1: Wrong URL Path (405 Method Not Allowed)

**Symptom**: You get a `405 Method Not Allowed` error.

**Cause**: You are sending requests to `https://verifimind.ysenseai.org/` instead of `https://verifimind.ysenseai.org/mcp/`.

**Fix**: Always include `/mcp/` in the URL:
```json
{
  "mcpServers": {
    "verifimind-peas": {
      "url": "https://verifimind.ysenseai.org/mcp/"
    }
  }
}
```

#### Mistake #2: Using GET Instead of POST (400 Bad Request)

**Symptom**: You get a `400 Bad Request` error.

**Cause**: Your client is sending a GET request. The MCP protocol requires POST for method calls.

**Fix**: Ensure your MCP client configuration uses `streamable-http` transport (not `http-sse`):
```json
{
  "mcpServers": {
    "verifimind-peas": {
      "url": "https://verifimind.ysenseai.org/mcp/",
      "transport": "streamable-http"
    }
  }
}
```

#### Mistake #3: Opening the URL in a Browser (406 Not Acceptable)

**Symptom**: You get a `406 Not Acceptable` or see an error page in your browser.

**Cause**: `verifimind.ysenseai.org` is an **MCP server API**, not a website. It is designed to be accessed by MCP clients (Claude Desktop, Cursor, VS Code, etc.), not web browsers.

**Fix**: Use an MCP client to connect. If you want to browse the project, visit:
- **Landing Page**: [verifimind.io](https://verifimind.io)
- **GitHub**: [github.com/creator35lwb-web/VerifiMind-PEAS](https://github.com/creator35lwb-web/VerifiMind-PEAS)

### HTTP Status Code Reference

| Status Code | Meaning | Solution |
|:-----------:|---------|----------|
| **302/307** | Redirect (normal) | Use `https://verifimind.ysenseai.org/mcp/` with trailing slash |
| **400** | Bad Request | Verify JSON syntax, use POST (not GET), include `Content-Type: application/json` |
| **404** | Not Found | Check URL for typos; use the correct `/mcp/` endpoint |
| **405** | Method Not Allowed | You are hitting `/` instead of `/mcp/` — add the `/mcp/` path |
| **406** | Not Acceptable | You are visiting the API URL in a browser — use an MCP client instead |

**Quick connectivity test:**
```bash
curl https://verifimind.ysenseai.org/mcp/
```

**Full troubleshooting guide:** **[MCP_Server_Troubleshooting_Guide.md](docs/MCP_Server_Troubleshooting_Guide.md)**

### Operational Insights

Traffic analysis from GCP Cloud Run logs (2-week sample, February 2026) provides the following operational baseline:

| Metric | Value | Notes |
|--------|-------|-------|
| **Total Requests** | 8,578 | 14-day sample, excluding health checks |
| **All-Time Users** | 530+ | Cumulative unique users |
| **Active Users (Week)** | 118 | Weekly active users |
| **Retention Rate** | 11.3% | Improving (up from 7.4%) |
| **Top Client** | Node.js MCP (67.7%) | Primary integration method |
| **Cursor IDE** | 12.5% | Growing IDE adoption |
| **Server Errors (5xx)** | 0 | Zero server errors in production |
| **Average Latency** | 4.30ms | Exceptional response time |
| **Monthly Cost** | $0 | Within GCP free tier |

The server runs on GCP Cloud Run with zero minimum instances (cold start architecture) to maintain a **$0/month operating cost**. GCP Global Uptime Checks monitor the `/health` endpoint every 5 minutes with email alerts to the project maintainer. All monitoring features operate within GCP’s free tier.

---

## 🌍 Real-World Validation

### **87-Day Journey: YSenseAI™ + VerifiMind-PEAS**

**Creator**: Alton Lee Wei Bin (creator35lwb)  
**Duration**: 87 days (September - November 2025)  
**Projects**: YSenseAI™ (AI attribution infrastructure) + VerifiMind-PEAS (validation methodology)

**Challenges**:
- Solo builder with non-tech background
- Multiple LLMs (Kimi, Claude, GPT, Gemini, Qwen, Grok)
- Hundreds of conversations across 87 days
- Complex technical and philosophical concepts

**Results**:
- ✅ **YSenseAI™**: Fully documented AI attribution infrastructure
- ✅ **VerifiMind-PEAS**: Complete methodology framework with white paper
- ✅ **Defensive Publication**: DOI 10.5281/zenodo.17645665
- ✅ **Zero context loss**: Genesis Master Prompts maintained continuity

**Key Insights**:
1. **Genesis Master Prompts scale**: Started with 1 page, grew to 50+ pages
2. **Multi-model validation works**: Different LLMs provided complementary perspectives
3. **Human-at-center is critical**: AI provides perspectives, human synthesizes and decides
4. **Iteration is key**: Continuous refinement through 87 days led to success

**Read the full case study**: [YSenseAI™ 87-Day Journey](https://journey.manus.space/)

---

## 🤝 Community

### **Join the Discussion**

- **[GitHub Discussions](https://github.com/creator35lwb-web/VerifiMind-PEAS/discussions)**: Ask questions, share insights, collaborate
- **[Twitter/X](https://x.com/creator35lwb)**: Follow updates and announcements
- **[Email](mailto:creator35lwb@gmail.com)**: Direct contact for inquiries

### **How to Contribute**

We welcome contributions from the community!

**Ways to contribute**:
- 📝 **Share case studies**: Document your experience using VerifiMind-PEAS
- 🌍 **Translate documentation**: Help make VerifiMind-PEAS accessible globally
- 💬 **Answer questions**: Help others in GitHub Discussions
- 🐛 **Report issues**: Identify unclear documentation or gaps
- 🎓 **Create tutorials**: Share your learning journey

**Read more**: [Contributing Guidelines](CONTRIBUTING.md)

---

## 🗺️ Roadmap

**Current Phase**: Phase 6 — Feature Enhancement & Strategic Pivot (Q1 2026)

**Status**: Phases 1–5 COMPLETE ✅ | v0.4.1 DEPLOYED 🎉 | v0.5.0 IN PLANNING

**North Star**: Position VerifiMind-PEAS as the **trust and verification layer for the emerging Agentic Web**.

### **Phase 1–4: Foundation** ✅ COMPLETE

Phases 1 through 4 established the methodology framework, MCP server implementation, production deployment on GCP Cloud Run, and multi-platform distribution across Smithery.ai, Hugging Face, and the Official MCP Registry.

### **Phase 5: Hardening & Standardization** ✅ COMPLETE

**Completed** (January 2026):

- ✅ **v0.3.0–v0.3.5**: BYOK multi-provider (7 providers), smart fallback, rate limiting, input sanitization
- ✅ **v0.4.0**: Unified Prompt Templates (19 templates, 6 libraries, 6 new tools)
- ✅ **CI/CD pipeline**: GitHub Actions with unit tests, security scanning (Bandit, Safety)
- ✅ **MACP v2.0**: Multi-Agent Communication Protocol published (DOI: 10.5281/zenodo.18504478)
- ✅ **L (GODEL) Ethical Operating Framework v1.1**: Fairness, bias mitigation, update mechanism
- ✅ **GCP Monitoring**: Uptime checks, alerting, log analysis pipeline

### **Phase 6: Feature Enhancement & Strategic Pivot** 🚧 CURRENT

**Completed** (February 2026):

- ✅ **v0.4.1**: Markdown-first output with content negotiation (80% token reduction)
- ✅ **Smithery URL removal**: All 13 proxy references replaced with direct URL
- ✅ **PDF deprecated**: Retained only for Zenodo DOI and enterprise compliance
- ✅ **Branch protection**: Main branch ruleset with required PR reviews and CI checks
- ✅ **CodeQL remediation**: All 102 security alerts resolved across 4 waves
- ✅ **Strategic pivot**: "Trust Layer for the Agentic Web" vision formalized
- ✅ **Genesis Master Prompt v4.0**: Ecosystem-level prompt iterated
- ✅ **Genesis v3.1**: CS Agent Multi-Stage Verification Protocol — 4-stage workflow (Detection → Self-Examination → Severity Rating → Human Review), zero code changes
- ✅ **Security docs published**: [`docs/security/`](docs/security/) — Protocol spec and Severity Rating Framework synced to public repo

**In Progress** (February–March 2026):

- ⏳ **v0.5.0 Agent Skills**: `/.well-known/agent-skills.json` for automated discovery
- ⏳ **MACP v2.0 as MCP Skills**: Expose collaboration protocols as discoverable skills
- ⏳ **Landing page**: [verifimind.io](https://verifimind.io) with anti-lock-in narrative
- ⏳ **Dynamic UI proof-of-concept**: MCP + A2A convergence research
- ⏳ **Community engagement**: GitHub Discussions, VS Code Live engagement

### **Future Phases** 📋 PLANNED

- **Phase 7**: Local Model Support & A2A Integration (Q2 2026) — Ollama-first, A2A protocol research
- **Phase 8**: Enterprise Features (Q2–Q3 2026) — Team collaboration, audit logging
- **Phase 9**: Ecosystem Expansion (Q3 2026) — IDE extensions, "Verified by Z-Protocol" GenUI Safety Standard

**Key Metrics**:
| Metric | Value | Significance |
|--------|-------|--------------|
| **MCP Tools** | 10 | 4 core + 6 template management |
| **Templates** | 19 | Pre-built across 6 libraries |
| **Validation Reports** | 57+ | Proof of methodology at scale |
| **Platforms Live** | 4 | GCP, MCP Registry, HuggingFace, verifimind.io |
| **LLM Providers** | 7 | Gemini, OpenAI, Anthropic, Groq, Mistral, Ollama, Perplexity |
| **All-Time Users** | 530+ | Cumulative unique users |
| **Cost per Validation** | ~$0.003 | Sustainable for all developers |

**See Examples**: [/validation_archive/](/validation_archive/) | [Examples](/examples/)

**Read more**: [Roadmap](ROADMAP.md) | [v0.5.0 Agent Skills Specification](iteration/v0.5.0_Agent_Skills_Specification.md)

---

## 📖 Defensive Publication

### **Prior Art Established**

**VerifiMind-PEAS establishes prior art** for the Genesis Prompt Engineering methodology and prevents others from patenting this approach to multi-model AI validation.

**Published**: November 19, 2025  
**DOI**: [10.5281/zenodo.17645665](https://doi.org/10.5281/zenodo.17645665)  
**License**: MIT License

**Core Innovations**:
1. **Genesis Methodology**: Systematic 5-step multi-model validation process
2. **X-Z-CS RefleXion Trinity**: Specialized AI agents (Innovation, Ethics, Security)
3. **Genesis Master Prompts**: Stateful memory system for project continuity
4. **Human-at-Center Orchestration**: Human as orchestrator (not reviewer)

**Evidence of Prior Use**:
- **YSenseAI™**: AI-powered attribution infrastructure (87-day development)
- **VerifiMind-PEAS**: Multi-model validation methodology framework
- **Concept Scrutinizer (概念审思者)**: Socratic validation framework

**Read more**: [Zenodo Publication Guide](docs/white_paper/Zenodo-Publication-Guide-v1.1.md)

---

## 📚 How to Cite

### **Citing VerifiMind-PEAS v0.4.1 (MCP Server)**

If you use the VerifiMind-PEAS MCP server in your research or project, please cite:

**APA Style**:
```
Lee, A., Manus AI, & Claude Code. (2026). VerifiMind-PEAS: Prompt Engineering Attribution System (Version 0.4.1) [Computer software]. GitHub. https://github.com/creator35lwb-web/VerifiMind-PEAS
```

**BibTeX**:
```bibtex
@software{verifimind_peas_v040_2026,
  author = {Lee, Alton and {Manus AI} and {Claude Code}},
  title = {VerifiMind-PEAS: Prompt Engineering Attribution System},
  year = {2026},
  version = {0.4.1},
  url = {https://github.com/creator35lwb-web/VerifiMind-PEAS},
  doi = {10.5281/zenodo.17980791},
  note = {MCP server for multi-model AI validation with Unified Prompt Templates}
}
```

**IEEE Style**:
```
A. Lee, Manus AI, and Claude Code, "VerifiMind-PEAS: Prompt Engineering Attribution System," Version 0.4.1, GitHub, 2026. [Online]. Available: https://github.com/creator35lwb-web/VerifiMind-PEAS
```

### **Citing Genesis Methodology v2.0 (Methodology)**

If you use or reference the Genesis Prompt Engineering Methodology, please cite:

**APA Style**:
```
Lee, A., & Manus AI. (2025). Genesis Prompt Engineering Methodology v2.0: Multi-Agent AI Validation Framework (Version 2.0.0) [Methodology]. Zenodo. https://doi.org/10.5281/zenodo.17972751
```

**BibTeX**:
```bibtex
@misc{genesis_v2_2025,
  author = {Lee, Alton and {Manus AI}},
  title = {Genesis Prompt Engineering Methodology v2.0: Multi-Agent AI Validation Framework},
  year = {2025},
  version = {2.0.0},
  url = {https://doi.org/10.5281/zenodo.17972751},
  doi = {10.5281/zenodo.17972751},
  note = {Validated through 87-day production development, 21,356 words}
}
```

**IEEE Style**:
```
A. Lee and Manus AI, "Genesis Prompt Engineering Methodology v2.0: Multi-Agent AI Validation Framework," Version 2.0.0, Zenodo, 2025. [Online]. Available: https://doi.org/10.5281/zenodo.17972751
```

### **GitHub Citation**

GitHub provides automatic citation support. Click the **"Cite this repository"** button on the repository page to get formatted citations in APA and BibTeX formats.

### **DOI Badges**

**VerifiMind-PEAS v1.1.0**:  
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.17980791.svg)](https://doi.org/10.5281/zenodo.17980791)

**Genesis Methodology v2.0**:  
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.17972751.svg)](https://doi.org/10.5281/zenodo.17972751)

*Note: DOI badges will be updated after Zenodo registration is complete.*

### **Release Information**

**VerifiMind-PEAS MCP Server v0.4.1** (Current):
- **Release Date**: February 14, 2026
- **Highlights**: Markdown-first output, Smithery URL removal, PDF deprecated
- **Changelog**: [CHANGELOG.md](CHANGELOG.md)
- **Status**: Production deployed on GCP Cloud Run

**VerifiMind-PEAS v1.1.0** (Methodology):
- **Release Date**: December 18, 2025
- **Tag**: `verifimind-v1.1.0`
- **Release Notes**: [RELEASE_NOTES_V1.1.0.md](RELEASE_NOTES_V1.1.0.md)
- **Status**: Production-ready, deployment-ready for Smithery marketplace

**Genesis Methodology v2.0**:
- **Release Date**: December 18, 2025
- **Tag**: `genesis-v2.0`
- **Release Notes**: [RELEASE_NOTES_GENESIS_V2.0.md](RELEASE_NOTES_GENESIS_V2.0.md)
- **Status**: Production-validated through 87-day development journey

---

## 📜 License

### Open Source License (MIT)

**VerifiMind-PEAS is released under the MIT License** for personal, educational, and open-source use.

Copyright (c) 2025-2026 Alton Lee Wei Bin (creator35lwb)

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

### Commercial License

**For enterprises requiring additional features, support, and legal protections**, we offer commercial licensing options:

- 🏢 **Enterprise Deployment**: Production environments with SLA requirements
- 🔒 **Proprietary Extensions**: Building proprietary features on top of the framework
- 📞 **Priority Support**: Dedicated support channels and guaranteed response times
- 🛡️ **Indemnification**: Legal protection and IP indemnification
- 📊 **Compliance**: Audit trails and compliance reports for regulated industries

**Read more**: [Commercial License](COMMERCIAL-LICENSE.md)

---

## ™️ Trademark Notice

The following are trademarks of Alton Lee:

- **VerifiMind™** - Primary brand
- **Genesis Methodology™** - Validation methodology
- **RefleXion Trinity™** - X-Z-CS agent architecture

**Usage Guidelines**:
- ✅ Use freely for personal and educational purposes
- ✅ Reference in documentation and discussions
- ❌ Do not use in product names without permission
- ❌ Do not imply official endorsement without permission

Forks and derivatives may use the open-source code under MIT license, but must use different branding.

---

## 📞 Contact

**General Inquiries**: creator35lwb@gmail.com  
**Twitter/X**: [@creator35lwb](https://x.com/creator35lwb)  
**GitHub Discussions**: [Join discussions](https://github.com/creator35lwb-web/VerifiMind-PEAS/discussions)  
**MCP Server**: [verifimind.ysenseai.org](https://verifimind.ysenseai.org) (LIVE — v0.4.0)  
**Landing Page**: [verifimind.io](https://verifimind.io)

---

## 🙏 Acknowledgments

### FLYWHEEL TEAM

VerifiMind-PEAS is developed through the **FLYWHEEL TEAM** multi-agent collaboration protocol:

| Agent | Role | Contribution |
|-------|------|--------------|
| **Alton Lee** (L/GODEL) | Human Orchestrator & Founder | Vision, strategy, final decisions |
| **Manus AI** (T/CTO) | Strategic Architecture | Documentation, roadmap, ecosystem alignment |
| **Claude Code** | Implementation | Code, testing, deployment, CI/CD |
| **Gemini** (Antigravity) | GCP Operations | Log analysis, monitoring, troubleshooting |
| **Perplexity** | Real-Time Research | Market intelligence, competitive analysis |

### LLM Providers

- **Google Gemini**: Default FREE provider for innovation analysis and GCP operations
- **Anthropic Claude**: Ethics and safety validation, code implementation
- **OpenAI GPT-4**: Technical analysis and structured output
- **Moonshot AI Kimi**: Innovation and creative insights
- **xAI Grok**: Alternative perspectives and validation
- **Alibaba Qwen**: Multilingual support
- **Groq / Mistral / Perplexity / Ollama**: BYOK multi-provider support

### Special Thanks

- **Open-source community**: For inspiration and collaboration
- **Early adopters**: For feedback and validation (444 users and counting)
- **Academic researchers**: For theoretical foundations
- **Google Cloud Platform**: For generous free tier enabling $0/month operations

---

<div align="center">

**Transform your vision into validated, ethical, secure applications.**

**Start with the [Genesis Master Prompt Guide](docs/guides/GENESIS_MASTER_PROMPT_GUIDE.md) today!** 🚀

[![GitHub Stars](https://img.shields.io/github/stars/creator35lwb-web/VerifiMind-PEAS?style=social)](https://github.com/creator35lwb-web/VerifiMind-PEAS)
[![Twitter Follow](https://img.shields.io/twitter/follow/creator35lwb?style=social)](https://x.com/creator35lwb)

</div>
