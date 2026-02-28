# VerifiMind™ PEAS Roadmap

<div align="center">

**Building the Future of Ethical AI Validation**

*Last Updated: March 1, 2026*

[![Version](https://img.shields.io/badge/Current-v0.4.5-blue.svg)](CHANGELOG.md)
[![Next](https://img.shields.io/badge/Next-v0.5.0_Foundation-orange.svg)](#v050-foundation)
[![Status](https://img.shields.io/badge/Status-Active%20Development-brightgreen.svg)](#current-status)

</div>

---

## 📋 Table of Contents

- [Vision & Philosophy](#-vision--philosophy)
- [Current Status](#-current-status)
- [Completed Milestones](#-completed-milestones)
- [Roadmap Timeline](#-roadmap-timeline)
- [Version Details](#-version-details)
- [Multi-Standard Strategy](#-multi-standard-strategy)
- [Sustainability Model](#-sustainability-model)
- [Community & Contribution](#-community--contribution)
- [Metrics & Goals](#-metrics--goals)

---

## 🎯 Vision & Philosophy

### Core Principle

> **"The methodology is free. The convenience is optional."**

VerifiMind-PEAS is committed to keeping the Genesis Prompt Engineering Methodology **free and open-source forever**. We believe ethical AI validation should be accessible to everyone, regardless of resources.

### What's Free Forever

| Component | Status | Description |
|-----------|--------|-------------|
| Genesis Methodology | ✅ Free | The complete 5-step validation process |
| MCP Server Code | ✅ Free | Full source code on GitHub |
| Documentation | ✅ Free | All guides, tutorials, and white papers |
| Self-Hosting | ✅ Free | Deploy on your own infrastructure |
| BYOK Support | ✅ Free | Use your own API keys (v0.4.5+) |
| Community Support | ✅ Free | GitHub Discussions & Issues |

### What May Be Paid (Future)

| Component | Status | Description |
|-----------|--------|-------------|
| Hosted Orchestration | 🔮 Future | Managed multi-agent routing & synthesis |
| Priority Support | 🔮 Future | Dedicated response times |
| Custom Integrations | 🔮 Future | Enterprise-specific features |
| Training & Workshops | 🔮 Future | Team onboarding sessions |

> *"Education is free, but consultation and management is personalized charges."*

---

## 📊 Current Status

### v0.4.5 BYOK Live (Current Release)

**Released:** February 28, 2026 | **PR:** [#55](https://github.com/creator35lwb-web/VerifiMind-PEAS/pull/55)

| Feature | Status | Notes |
|---------|--------|-------|
| MCP Server (Streamable-HTTP) | ✅ Live | verifimind.ysenseai.org |
| Official MCP Registry | ✅ Listed | registry.modelcontextprotocol.io |
| HuggingFace Demo | ✅ Live | Wisdom Canvas (YSenseAI/wisdom-canvas) |
| 4 Core Tools | ✅ Available | validate_concept, analyze_security, check_ethics, synthesize_insights |
| **BYOK Per-Tool-Call** | ✅ **LIVE** | Ephemeral provider override on every tool call |
| Auto-Detect Key Format | ✅ Working | `gsk_` → Groq, `sk-ant-` → Anthropic, `sk-` → OpenAI, etc. |
| Multi-Provider Support | ✅ Working | Gemini, OpenAI, Anthropic, Groq, Mistral, Ollama |
| Rate Limiting | ✅ Active | 10 req/min per IP, 100 req/min global |
| Smart Fallback | ✅ Working | Per-agent provider support |
| Input Sanitization | ✅ Active | Prompt injection detection (v0.3.5+) |
| CI/CD Pipeline | ✅ Active | Bandit SAST + 175 automated tests |

**BYOK Validation:** Triple-validated by Manus AI (6/6), Claude Code (6/6), and CI pipeline (175 tests).

### Platform Listings

| Platform | Status | Link |
|----------|--------|------|
| Official MCP Registry | ✅ Listed | [registry.modelcontextprotocol.io](https://registry.modelcontextprotocol.io/?q=verifimind) |
| GitHub | ✅ Active | [creator35lwb-web/VerifiMind-PEAS](https://github.com/creator35lwb-web/VerifiMind-PEAS) |
| HuggingFace Spaces | ✅ Live | [YSenseAI/wisdom-canvas](https://huggingface.co/spaces/YSenseAI/wisdom-canvas) |
| Zenodo (DOI) | ✅ Published | [10.5281/zenodo.17645665](https://doi.org/10.5281/zenodo.17645665) |
| Landing Page | ✅ Live | [verifimind.ysenseai.org](https://verifimind.ysenseai.org) |

### Active Users

Based on our server logs (7-day analysis):

- **19,542** total log entries
- **Claude-User** connections detected (real MCP client usage!)
- **Cursor** client connections
- **Browser** visitors from Chrome 144

**Thank you to our early adopters!** 🙏

---

## ✅ Completed Milestones

### v0.4.x Series (February 2026)

| Version | Release Date | Key Achievement |
|---------|-------------|-----------------|
| v0.4.5 | Feb 28, 2026 | **BYOK Live** — Per-tool-call provider override with auto-detect |
| v0.4.4 | Feb 27, 2026 | Version bump, 48x48 favicon with dark background |
| v0.4.3 | Feb 26, 2026 | Streamable-HTTP transport upgrade |
| v0.4.2 | Feb 25, 2026 | Multi-Model Trinity (Gemini + Anthropic + Perplexity) |
| v0.4.1 | Feb 24, 2026 | Agent model labels, enhanced health endpoint |
| v0.4.0 | Feb 23, 2026 | Unified prompt templates, MCP Registry listing |

### v0.3.x Series (January 2026)

| Version | Release Date | Key Achievement |
|---------|-------------|-----------------|
| v0.3.5 | Jan 30, 2026 | Input sanitization, prompt injection detection |
| v0.3.4 | Jan 29, 2026 | Rate limiting, smart fallback |
| v0.3.0 | Jan 15, 2026 | Initial GCP Cloud Run deployment |

### Pre-Release (December 2025 – January 2026)

| Milestone | Date | Achievement |
|-----------|------|-------------|
| Zenodo DOI | Jan 2026 | [10.5281/zenodo.17645665](https://doi.org/10.5281/zenodo.17645665) |
| White Paper | Dec 2025 | Genesis Prompt Engineering Methodology published |
| First Commit | Dec 2025 | Project inception |

---

## 🗓️ Roadmap Timeline

```
2026 Q1 (DONE)              2026 Q1-Q2                  2026 Q2
   │                            │                          │
   ▼                            ▼                          ▼
┌──────────┐              ┌──────────┐              ┌──────────┐
│  v0.4.5  │              │  v0.5.0  │              │  v0.5.x  │
│  BYOK    │──────────────│ Founda-  │──────────────│ Stabi-   │
│  Live ✅  │              │  tion    │              │  lity    │
└──────────┘              └──────────┘              └──────────┘
   Feb 2026                Mar-Apr 2026              Apr-May 2026

2026 Q2-Q3                  2026 Q3                    2026 Q3+
   │                          │                          │
   ▼                          ▼                          ▼
┌──────────┐              ┌──────────┐              ┌──────────┐
│  v0.6.0  │              │  v0.7.0  │              │  v0.8.0+ │
│  Agent   │──────────────│  MCP     │──────────────│  Quad    │
│  Skills  │              │  App     │              │  CLI     │
└──────────┘              └──────────┘              └──────────┘
  May-Jun 2026              Jun-Jul 2026             Q3+ 2026
                                                   (Discussion)
```

---

## 📦 Version Details

### v0.5.0: Foundation
**Target:** March–April 2026 | **Priority:** CRITICAL

The most important release — building the solid foundation everything else depends on.

| Feature | Description | Status |
|---------|-------------|--------|
| Smithery Sunset Migration | Ensure all users migrate to direct MCP config | 🔲 Planned |
| Streamable-HTTP Primary | Complete transition from SSE to streamable-HTTP | 🔲 Planned |
| Security Specification | Formal security model document (Z-Protocol spec) | 🔲 Planned |
| Comprehensive Test Suite | Target: 200+ tests (currently 175) | 🔲 Planned |
| Documentation Overhaul | Updated guides for v0.4.5+ features | 🔲 Planned |
| Error Handling v2 | Structured error responses with recovery hints | 🔲 Planned |
| Health Endpoint v2 | Enhanced diagnostics, uptime tracking | 🔲 Planned |
| BYOK Hardening | Edge case handling, provider timeout management | 🔲 Planned |

**Why Foundation First?**

> Every feature we build after v0.5.0 depends on the foundation being rock-solid. BYOK, Agent Skills, MCP App — all of these are only as reliable as the core engine underneath. v0.5.0 is about making that engine unbreakable.

**Smithery Sunset Note:** March 1, 2026 marks the Smithery platform sunset. Users who discovered VerifiMind-PEAS through Smithery need clear migration guidance to direct MCP configuration.

---

### v0.5.x: Stability
**Target:** April–May 2026 | **Priority:** HIGH

Production hardening and reliability improvements.

| Feature | Description | Status |
|---------|-------------|--------|
| Production Hardening | Memory optimization, connection pooling | 🔲 Planned |
| Performance Optimization | Response time improvements, caching | 🔲 Planned |
| Monitoring & Alerting | Structured logging, uptime monitoring | 🔲 Planned |
| BYOK Analytics | Anonymous usage patterns for provider optimization | 🔲 Planned |
| Migration Guide | Smithery → direct MCP config documentation | 🔲 Planned |

---

### v0.6.0: Agent Skills Support
**Target:** May–June 2026 | **Priority:** HIGH

Vendor-neutral Agent Skills standard support for multi-platform compatibility.

| Feature | Description | Status |
|---------|-------------|--------|
| /.well-known/agent-skills.json | Standard discovery manifest | 🔲 Planned |
| /skills/ Endpoints | OpenAPI-like skill definitions | 🔲 Planned |
| Multi-Vendor Support | Works with non-Anthropic agents | 🔲 Planned |
| Skill Versioning | Track skill evolution | 🔲 Planned |
| Core Extraction | Shared validation engine module | 🔲 Planned |

**Why Agent Skills?**

Agent Skills (agentskills.io) is an emerging **vendor-neutral** standard initiated by Vercel. Unlike MCP (Anthropic-specific), Agent Skills works across multiple AI platforms.

| Aspect | MCP | Agent Skills |
|--------|-----|--------------|
| Origin | Anthropic | Vercel (open consortium) |
| Adoption | Claude-centric | Multi-vendor |
| Discovery | Manual config | Automatic via /.well-known |
| Format | JSON-RPC | OpenAPI-like |

**Proposed Structure:**
```
verifimind.ysenseai.org/
├── /mcp/                      → MCP Server (existing)
├── /.well-known/
│   └── agent-skills.json      → Agent Skills manifest (new)
└── /skills/
    ├── validate-concept/
    ├── analyze-security/
    ├── check-ethics/
    └── genesis-council/
```

---

### v0.7.0: MCP App Development
**Target:** June–July 2026 | **Priority:** MEDIUM

Transform VerifiMind-PEAS from an MCP Server into an **MCP App** with rich UI.

| Feature | Description | Status |
|---------|-------------|--------|
| Visual Dashboard | AI Council session visualization | 🔲 Planned |
| Persistent History | Store validation sessions | 🔲 Planned |
| One-Click Install | MCP App Store distribution | 🔲 Planned |
| Rich UI | Interactive validation interface | 🔲 Planned |
| Local Model Support | Ollama, LM Studio integration | 🔲 Planned |

**Background:** Anthropic announced MCP Apps (January 2026) — evolving MCP from tools to full applications.

| Aspect | MCP Tools (Current) | MCP Apps (New) |
|--------|---------------------|----------------|
| Scope | Single-function tools | Full applications |
| UI | None | Rich interfaces |
| State | Stateless | Stateful sessions |
| Distribution | Manual config | App store model |

---

### v0.8.0+: Quad Validation CLI (Discussion Phase)
**Target:** Q3+ 2026 | **Priority:** FUTURE | **Status:** Discussion Only

> ⚠️ **This feature is in discussion phase only.** It will NOT be implemented until the foundation (v0.5.0–v0.7.0) is robust and proven. The separate repository `verifimind-quad-cli` will be created only when the commercialization readiness gate is met.

A standalone CLI tool for simultaneous 4-agent validation orchestration.

| Feature | Description | Status |
|---------|-------------|--------|
| 4-Agent Orchestration | Run Y, X, Z, CS simultaneously | 💬 Discussion |
| G-Agent (Grok) | Fifth agent for additional perspective | 💬 Discussion |
| Shared Core | Imports from extracted VerifiMind core engine | 💬 Discussion |
| CLI Interface | Click/Typer-based command line tool | 💬 Discussion |
| Separate Repository | verifimind-quad-cli (when ready) | 💬 Discussion |

**Commercialization Readiness Gate:**
1. ✅ v0.5.0 Foundation complete and stable
2. 🔲 Proven BYOK adoption (>20 active BYOK users)
3. 🔲 Community demand for CLI interface validated
4. 🔲 Core engine extracted as shared module (v0.6.0)
5. 🔲 Security specification inherited from v0.5.0

**Architecture Decision:** The quad-cli will be a **separate repository** that imports from a shared core engine. This follows the industry pattern (Terraform, Kubernetes, Docker) of keeping a monorepo until the core is stable, then splitting interfaces when there's proven demand.

---

## 🌐 Multi-Standard Strategy

### Genesis Skills Package Vision

VerifiMind-PEAS aims to be the **reference implementation** for ethical multi-model AI validation, available across multiple standards:

```
                    ┌─────────────────────────────────┐
                    │     Genesis Skills Package      │
                    │  "Ethical AI Validation Suite"  │
                    └─────────────────────────────────┘
                                    │
            ┌───────────────────────┼───────────────────────┐
            │                       │                       │
    ┌───────▼───────┐      ┌───────▼───────┐      ┌───────▼───────┐
    │   MCP Server  │      │  Agent Skills │      │   MCP App     │
    │  (v0.4.5 ✅)  │      │    (v0.6.0)   │      │   (v0.7.0)    │
    └───────────────┘      └───────────────┘      └───────────────┘
            │                       │                       │
            └───────────────────────┼───────────────────────┘
                                    │
                    ┌───────────────▼───────────────┐
                    │      VerifiMind-PEAS Core     │
                    │   Genesis Methodology Engine  │
                    └───────────────────────────────┘
                                    │
                         ┌──────────▼──────────┐
                         │   Quad CLI (v0.8.0+)│
                         │   (Discussion Only) │
                         └─────────────────────┘
```

### Academic Validation

Our "AI Council" methodology has received independent academic validation:

> **"Cyborg Orchestration in LLM Council-Double Delphi"**  
> Author: Valeri Chukhlomin (SSRN, December 2025)  
> [https://papers.ssrn.com/sol3/papers.cfm?abstract_id=5990855](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=5990855)

| Academic Term | VerifiMind Equivalent |
|---------------|----------------------|
| LLM Council | AI Council (Y, X, Z, CS) |
| Cyborg Orchestration | Human-Centric Orchestration |
| Double Delphi | Multi-Model Validation |
| Problem Structuring Methods | Genesis 5-Step Process |

---

## 💰 Sustainability Model

### The Challenge

As an open-source project with real infrastructure costs, we face the classic sustainability paradox:
- Open-source = Free for users
- Infrastructure = Real costs (GCP, domains)
- Growth = More costs (more users = more API calls)

### Our Solution: BYOK-First

```
┌─────────────────────────────────────────────────────────────┐
│                    Cost Distribution                         │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Maintainer Costs (Fixed)          User Costs (Variable)   │
│  ─────────────────────────         ────────────────────    │
│  • GCP Cloud Run (~RM60/mo)        • Their own API keys    │
│  • Domain (~RM5/mo)                • Their token usage     │
│  • GitHub (Free)                   • Optional donations    │
│                                                             │
│  Result: Costs stay fixed regardless of user growth         │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Commercialization Path (Future)

| Layer | Free/Paid | Rationale |
|-------|-----------|-----------|
| Genesis Methodology | FREE forever | Education is free |
| MCP Server (self-host) | FREE forever | Open-source commitment |
| MCP Server (hosted, BYOK) | FREE | Users pay their own API costs |
| Quad-CLI (open-source) | FREE (future) | Code is always free |
| Hosted Orchestration | PAID (future) | Managed routing & synthesis |
| Enterprise Dashboard | PAID (future) | Analytics & management |

> *"Education is free, but consultation and management is personalized charges."*

### Transparency

| Metric | Current | Target |
|--------|---------|--------|
| Monthly Infrastructure Cost | ~RM 87-97 | < RM 100 |
| Budget Allocation | RM 100/month | 1-year experiment |
| Revenue | RM 0 | Not primary goal (yet) |
| Funding Source | Personal | Community (future) |

### How You Can Help

1. **Use BYOK** — Bring your own API keys to reduce server costs
2. **Star the repo** — Visibility helps attract contributors
3. **Report issues** — Help us improve without hiring QA
4. **Contribute code** — PRs welcome!
5. **Spread the word** — Tell others about ethical AI validation

---

## 👥 Community & Contribution

### Get Involved

| Channel | Purpose | Link |
|---------|---------|------|
| GitHub Discussions | Questions, ideas, feedback | [Discussions](https://github.com/creator35lwb-web/VerifiMind-PEAS/discussions) |
| GitHub Issues | Bug reports, feature requests | [Issues](https://github.com/creator35lwb-web/VerifiMind-PEAS/issues) |
| X (Twitter) | Updates & announcements | [@YSenseAI](https://x.com/YSenseAI) |
| Landing Page | Project overview & demos | [verifimind.ysenseai.org](https://verifimind.ysenseai.org) |

### Contribution Areas

| Area | Skill Level | Impact |
|------|-------------|--------|
| Documentation | Beginner | High |
| Bug Fixes | Intermediate | High |
| New LLM Providers | Intermediate | High |
| Agent Skills Implementation | Intermediate | High |
| Testing | Beginner | Medium |
| Translations | Beginner | Medium |

---

## 📈 Metrics & Goals

### Zenodo Publication Impact

| Publication | Views | Downloads | Download Rate |
|-------------|-------|-----------|---------------|
| **VerifiMind-PEAS** | **302** | **75** | **24.8%** |
| YSenseAI White Paper | 200 | 9 | 4.5% |
| GodelAI C-S-P Framework | 92 | 0 | 0% |
| **Total** | **605** | **88** | **14.5%** |

### Year 1 Targets (2026)

| Metric | Current | Q1 Target | Q2 Target | Year-End |
|--------|---------|-----------|-----------|----------|
| GitHub Stars | ~10 | 100 | 300 | 500 |
| Monthly MCP Connections | ~50 | 100 | 200 | 500 |
| BYOK Users | ~5 | 20 | 50 | 100 |
| Contributors | 1 | 3 | 5 | 10 |
| Automated Tests | 175 | 200 | 250 | 300 |

### Success Indicators

- ✅ Listed on Official MCP Registry
- ✅ Live production deployment (GCP Cloud Run)
- ✅ Real user activity detected (19K+ log entries)
- ✅ HuggingFace demo live (Wisdom Canvas)
- ✅ DOI-cited publication (Zenodo)
- ✅ BYOK multi-provider support (v0.4.5)
- ✅ Triple-validated BYOK (Manus AI + Claude Code + CI)
- ✅ Landing page live (verifimind.ysenseai.org)
- 🔲 First external contributor
- 🔲 100 GitHub stars
- 🔲 Agent Skills support (v0.6.0)
- 🔲 Featured in AI newsletter/blog
- 🔲 v0.5.0 Foundation release

---

## 📞 Contact & Support

**Maintainer:** Team YSenseAI

- **Website:** [verifimind.ysenseai.org](https://verifimind.ysenseai.org)
- **GitHub:** [@creator35lwb-web](https://github.com/creator35lwb-web)
- **White Paper:** [DOI 10.5281/zenodo.17645665](https://doi.org/10.5281/zenodo.17645665)

---

<div align="center">

**Built with 💙 by Team YSenseAI**

*"Crystal Balls Inside the Black Box"*

</div>
