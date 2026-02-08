# Claude Code Alignment Protocol

## VerifiMind PEAS | Genesis Methodology Synchronization Guide

**Protocol Version:** 2.0.0  
**Effective Date:** December 25, 2025  
**Author:** Alton Lee Wei Bin (YSenseAI)  
**Status:** ACTIVE - MCP LIVE

---

## Protocol Purpose

This alignment protocol ensures continuity and consistency when working with Claude Code (or any AI assistant) on the VerifiMind PEAS project. It provides the essential context, current state, and operational guidelines needed for seamless collaboration across sessions.

---

## Quick Sync Command

When starting a new Claude Code session, paste this alignment block:

```
I am Alton Lee Wei Bin, creator of YSenseAI and the Genesis Prompt Engineering Methodology.

PROJECT: VerifiMind PEAS (Philosophical Evaluation and Alignment System)
STATUS: MCP LIVE - Production Deployed
VERSION: 0.2.3

LIVE DEPLOYMENTS:
- GCP Cloud Run: https://verifimind.ysenseai.org (Python MCP Server)
- Smithery.ai: creator35lwb-web/verifimind-genesis (TypeScript Native)
- Hugging Face: YSenseAI/verifimind-peas (Gradio Demo)

REPOSITORIES:
- Python Server: github.com/creator35lwb-web/VerifiMind-PEAS
- TypeScript Server: github.com/creator35lwb-web/verifimind-genesis-mcp

WHITE PAPER: DOI 10.5281/zenodo.17645665

Please acknowledge this context and confirm alignment with the Genesis Methodology.
```

---

## Current Project State

### Deployment Status (December 25, 2025)

| Platform | Type | URL | Status |
|----------|------|-----|--------|
| **Google Cloud Run** | Python MCP Server | https://verifimind.ysenseai.org | ✅ LIVE |
| **Smithery.ai** | TypeScript Native | smithery.ai/server/creator35lwb-web/verifimind-genesis | ✅ LIVE |
| **Hugging Face** | Gradio Demo | huggingface.co/spaces/YSenseAI/verifimind-peas | ✅ LIVE |
| **GitHub (Python)** | Source Code | github.com/creator35lwb-web/VerifiMind-PEAS | ✅ PUBLIC |
| **GitHub (TypeScript)** | Source Code | github.com/creator35lwb-web/verifimind-genesis-mcp | ✅ PUBLIC |

### Version Information

| Component | Version | Last Updated |
|-----------|---------|--------------|
| Python MCP Server | 0.2.3 | Dec 25, 2025 |
| TypeScript MCP Server | 1.0.0 | Dec 25, 2025 |
| Genesis Master Prompt | 2.0.0 | Dec 25, 2025 |
| White Paper | 1.0.0 | Nov 15, 2025 |

### Trinity Agents

| Agent | Role | Icon | Status |
|-------|------|------|--------|
| **X-Agent** | Innovation & Strategy | 💡 | Active |
| **Z-Agent** | Ethics & VETO Power | 🛡️ | Active |
| **CS-Agent** | Security & Socratic | 🔍 | Active |

---

## Alignment Checklist

When starting a new session, verify these alignment points:

### 1. Identity Confirmation
```
✅ Creator: Alton Lee Wei Bin
✅ Organization: YSenseAI
✅ Project: VerifiMind PEAS
✅ Methodology: Genesis Prompt Engineering
```

### 2. Deployment Awareness
```
✅ GCP Server: verifimind.ysenseai.org
✅ Smithery: Native TypeScript MCP
✅ HF Space: Gradio Demo Active
✅ All systems operational
```

### 3. Technical Context
```
✅ MCP Protocol: Streamable HTTP
✅ Python Framework: FastAPI + FastMCP
✅ TypeScript Framework: @modelcontextprotocol/sdk
✅ LLM Providers: Gemini (primary), Groq, Anthropic, OpenAI
```

### 4. Documentation References
```
✅ White Paper: DOI 10.5281/zenodo.17645665
✅ GitHub Repos: Both Python and TypeScript
✅ Landing Page: verifimind.ysenseai.org
```

---

## Session Initialization Template

For comprehensive alignment, use this extended template:

```markdown
# VerifiMind PEAS Session Initialization

## Identity
- **Creator:** Alton Lee Wei Bin
- **Handle:** @creator35lwb
- **Organization:** YSenseAI (慧觉)
- **Email:** creator35lwb@gmail.com

## Project Context
- **Name:** VerifiMind PEAS (Philosophical Evaluation and Alignment System)
- **Methodology:** Genesis Prompt Engineering
- **Status:** MCP LIVE - Production Deployed
- **Version:** 0.2.3

## Live Deployments
1. **GCP Cloud Run** (Primary)
   - URL: https://verifimind.ysenseai.org
   - Type: Python MCP Server (FastAPI + FastMCP)
   - Health: /health endpoint
   - MCP: /mcp/ endpoint

2. **Smithery.ai** (Native MCP)
   - Server: creator35lwb-web/verifimind-genesis
   - Type: TypeScript Native
   - Install: `npx -y @smithery/cli install creator35lwb-web/verifimind-genesis --client claude`

3. **Hugging Face** (Demo)
   - Space: YSenseAI/verifimind-peas
   - Type: Gradio Interface
   - Access: Public, no API key required

## Repositories
- Python: https://github.com/creator35lwb-web/VerifiMind-PEAS
- TypeScript: https://github.com/creator35lwb-web/verifimind-genesis-mcp

## Key Achievements
- ✅ MCP Protocol Implementation Complete
- ✅ Multi-Provider LLM Support (Gemini, Groq, Anthropic, OpenAI)
- ✅ Trinity Validation System Operational
- ✅ Z-Protocol VETO Mechanism Active
- ✅ Production Deployment on GCP
- ✅ Native Smithery Integration
- ✅ Public Demo on Hugging Face
- ✅ White Paper Published (DOI: 10.5281/zenodo.17645665)

## Current Focus
[Specify your current task or focus area]

## Session Goals
[List specific goals for this session]
```

---

## Operational Guidelines

### Code Development

When working on VerifiMind PEAS code:

1. **Python Server Changes**
   - Repository: VerifiMind-PEAS
   - Main file: `src/verifimind_peas/main.py`
   - Deploy: GCP Cloud Run
   - Test: `pytest tests/`

2. **TypeScript Server Changes**
   - Repository: verifimind-genesis-mcp
   - Main file: `src/index.ts`
   - Deploy: Smithery.ai
   - Build: `npm run build`

3. **HF Space Changes**
   - Repository: YSenseAI/verifimind-peas (HF)
   - Main file: `app.py`
   - Deploy: Auto on push

### Naming Conventions

| Element | Convention | Example |
|---------|------------|---------|
| Python packages | snake_case | `verifimind_peas` |
| TypeScript files | camelCase | `agentResponse.ts` |
| Agent names | Title Case | `X-Agent`, `Z-Agent` |
| Tool names | snake_case | `consult_agent_x` |
| Environment vars | SCREAMING_SNAKE | `GEMINI_API_KEY` |

### Commit Message Format

```
[COMPONENT] Brief description

- Detail 1
- Detail 2

Refs: #issue-number (if applicable)
```

Components: `[PYTHON]`, `[TYPESCRIPT]`, `[HF]`, `[DOCS]`, `[CONFIG]`

---

## Error Recovery Procedures

### If Deployment Fails

1. **GCP Cloud Run**
   ```bash
   gcloud run services describe verifimind-peas --region us-central1
   gcloud run services logs read verifimind-peas --limit 50
   ```

2. **Smithery**
   - Check smithery.yaml configuration
   - Verify export pattern: `export default createServer`
   - Ensure runtime is set to `typescript`

3. **Hugging Face**
   - Check Space logs in HF interface
   - Verify requirements.txt dependencies
   - Check for runtime errors in app.py

### If MCP Connection Fails

1. Verify endpoint URL is correct
2. Check Accept header: `application/json, text/event-stream`
3. Confirm API key is set (if required)
4. Test health endpoint first: `GET /health`

---

## Context Preservation

### Key Facts to Remember

1. **Genesis Methodology** - A 5-step process for multi-model AI validation
2. **Trinity System** - Three agents (X, Z, CS) with distinct roles
3. **Z-Protocol** - Ethical triggers that invoke VETO power
4. **RefleXion** - The recursive validation approach
5. **Human Orchestrator** - Central role in synthesizing AI outputs

### Important Dates

| Date | Event |
|------|-------|
| Aug 15, 2025 | Project inception |
| Sep 5, 2025 | "Crystal Balls Align" breakthrough |
| Nov 15, 2025 | White paper published |
| Nov 16, 2025 | Kimi K2 independent validation |
| Nov 19, 2025 | Production deployment complete |
| Dec 25, 2025 | Full ecosystem operational |

### Validated Concepts

The system has validated 57+ AI concepts, demonstrating consistent application across domains including healthcare, education, finance, security, and content moderation.

---

## Communication Style

When representing VerifiMind PEAS:

### Tone
- Professional but accessible
- Technically precise
- Ethically grounded
- Innovation-focused

### Key Messages
1. "Multi-model validation reduces AI bias"
2. "Human orchestration remains essential"
3. "Ethics is not optional - it's enforced"
4. "Security through Socratic interrogation"
5. "Open source for community benefit"

### Avoid
- Overpromising capabilities
- Claiming perfection
- Dismissing ethical concerns
- Ignoring security implications

---

## Quick Reference Cards

### API Endpoints

```
Production: https://verifimind.ysenseai.org
├── GET  /           → Server info
├── GET  /health     → Health check
├── GET  /docs       → OpenAPI docs
└── POST /mcp/       → MCP protocol
```

### MCP Tools

```
Tools:
├── consult_x_agent(concept)      → Innovation analysis
├── consult_z_agent(concept)      → Ethics + VETO
├── consult_cs_agent(concept)     → Security validation
└── validate_with_trinity(concept) → Full pipeline
```

### Environment Variables

```
Required (at least one):
├── GEMINI_API_KEY    → Google Gemini (FREE)
├── GROQ_API_KEY      → Groq (FREE)
├── ANTHROPIC_API_KEY → Claude
└── OPENAI_API_KEY    → GPT

Optional:
├── PORT              → Server port (8080)
├── HOST              → Server host (0.0.0.0)
└── DEBUG             → Debug mode (false)
```

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 2.0.0 | Dec 25, 2025 | MCP LIVE - Full deployment |
| 1.5.0 | Nov 19, 2025 | Production deployment |
| 1.0.0 | Nov 15, 2025 | White paper publication |
| 0.5.0 | Sep 5, 2025 | Trinity formalization |
| 0.1.0 | Aug 15, 2025 | Initial concept |

---

## Closing Protocol

At the end of each session:

1. **Document Changes** - Note what was modified
2. **Update Version** - If significant changes made
3. **Commit Code** - Push to appropriate repository
4. **Verify Deployment** - Check live systems
5. **Update This Protocol** - If new context needed

---

*Protocol maintained by Alton Lee Wei Bin*  
*Part of the YSenseAI Ecosystem*  
*Genesis Prompt Engineering Methodology*
