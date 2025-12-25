# VerifiMind PEAS Complete Backup Package

## Multi-Model AI Validation with RefleXion Trinity

**Version:** 1.0.0  
**Author:** Alton Lee Wei Bin  
**Date:** December 25, 2025  
**License:** MIT  

---

## Overview

This backup package contains the complete source code, documentation, and configuration files for the VerifiMind PEAS (Philosophical Evaluation and Alignment System) ecosystem. The package includes everything needed to deploy, customize, and extend the Trinity validation framework.

---

## Package Contents

```
VerifiMind-PEAS-Backup/
├── README.md                          # This file
├── huggingface-space/                 # Hugging Face Space demo
│   ├── app.py                         # Gradio application
│   ├── requirements.txt               # Python dependencies
│   └── README.md                      # Space documentation
├── typescript-mcp-server/             # Native TypeScript MCP server
│   ├── src/
│   │   └── index.ts                   # Main server implementation
│   ├── package.json                   # Node.js dependencies
│   ├── tsconfig.json                  # TypeScript configuration
│   └── README.md                      # Server documentation
├── python-mcp-server/                 # Production Python MCP server
│   ├── src/
│   │   └── verifimind_peas/
│   │       ├── __init__.py            # Package initialization
│   │       └── main.py                # Main server implementation
│   ├── tests/
│   │   └── test_agents.py             # Unit tests
│   ├── pyproject.toml                 # Python project configuration
│   ├── requirements.txt               # Python dependencies
│   └── README.md                      # Server documentation
├── documentation/                     # Comprehensive documentation
│   ├── DEVELOPMENT_JOURNEY.md         # 87-day development chronicle
│   ├── QUICKSTART.md                  # 5-minute getting started guide
│   ├── GCP_DEPLOYMENT_GUIDE.md        # Google Cloud Run deployment
│   └── CLAUDE_DESKTOP_SETUP.md        # Claude Desktop integration
└── configs/                           # Configuration files
    ├── smithery.yaml                  # Smithery.ai configuration
    ├── Dockerfile                     # Production Docker image
    ├── docker-compose.yml             # Local development setup
    ├── cloudbuild.yaml                # GCP CI/CD pipeline
    ├── .env.example                   # Environment variables template
    └── LICENSE                        # MIT License
```

---

## Quick Reference

### Live Deployments

| Platform | URL | Status |
|----------|-----|--------|
| **Production API** | https://verifimind.ysenseai.org | Active |
| **Smithery Server** | https://smithery.ai/server/creator35lwb-web/verifimind-genesis | Active |
| **Hugging Face Space** | https://huggingface.co/spaces/YSenseAI/verifimind-peas | Active |
| **GitHub (Python)** | https://github.com/creator35lwb-web/VerifiMind-PEAS | Public |
| **GitHub (TypeScript)** | https://github.com/creator35lwb-web/verifimind-genesis-mcp | Public |

### Key Resources

| Resource | Link |
|----------|------|
| **White Paper (DOI)** | https://doi.org/10.5281/zenodo.17645665 |
| **YSenseAI Platform** | https://ysenseai.org |
| **Landing Page** | https://verifimind.ysenseai.org |

---

## The Trinity Agents

The VerifiMind PEAS system uses three specialized agents for comprehensive AI validation:

| Agent | Role | Special Power | Icon |
|-------|------|---------------|------|
| **X-Agent** | Innovation and Strategy Analysis | Identifies opportunities | 💡 |
| **Z-Agent** | Ethics and Z-Protocol Enforcement | **VETO POWER** | 🛡️ |
| **CS-Agent** | Security and Socratic Interrogation | Probes vulnerabilities | 🔍 |

### Z-Protocol Triggers

Z-Agent has the authority to VETO any concept that triggers these ethical concerns:

1. **Mass Surveillance** - Potential for surveillance without consent
2. **Discrimination** - Bias amplification or discriminatory outcomes
3. **Manipulation** - Deceptive or manipulative user interactions
4. **Environmental Harm** - Significant environmental impact at scale
5. **Violence Enablement** - Potential for weapons or violence
6. **Child Safety** - Any risk to children's safety or wellbeing

---

## Getting Started

### Option 1: Use the Live Demo

Visit the Hugging Face Space for instant access:
```
https://huggingface.co/spaces/YSenseAI/verifimind-peas
```

### Option 2: Install for Claude Desktop

```bash
npx -y @smithery/cli@latest install creator35lwb-web/verifimind-genesis --client claude
```

### Option 3: Deploy Your Own Server

**Using Docker:**
```bash
cd python-mcp-server
docker build -f ../configs/Dockerfile -t verifimind-peas .
docker run -p 8080:8080 -e GEMINI_API_KEY=your-key verifimind-peas
```

**Using Python:**
```bash
cd python-mcp-server
pip install -e .
export GEMINI_API_KEY=your-key
verifimind-peas
```

### Option 4: Deploy to Google Cloud Run

```bash
gcloud run deploy verifimind-peas \
  --source python-mcp-server \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars GEMINI_API_KEY=your-key
```

---

## API Reference

### Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Server information |
| `/health` | GET | Health check |
| `/mcp/` | POST | MCP protocol endpoint |

### MCP Tools

| Tool | Description |
|------|-------------|
| `consult_x_agent` | Innovation analysis |
| `consult_z_agent` | Ethical evaluation with VETO |
| `consult_cs_agent` | Security validation |
| `validate_with_trinity` | Full Trinity pipeline |

### Example Request

```bash
curl -X POST https://verifimind.ysenseai.org/mcp/ \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "tools/call",
    "params": {
      "name": "validate_with_trinity",
      "arguments": {
        "concept": "AI-powered medical diagnosis system"
      }
    }
  }'
```

---

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `GEMINI_API_KEY` | Google Gemini API key (FREE tier) | No* |
| `GROQ_API_KEY` | Groq API key (FREE tier) | No* |
| `ANTHROPIC_API_KEY` | Anthropic Claude API key | No* |
| `OPENAI_API_KEY` | OpenAI API key | No* |
| `PORT` | Server port (default: 8080) | No |
| `HOST` | Server host (default: 0.0.0.0) | No |

*At least one API key is recommended for full functionality.

### Getting FREE API Keys

**Google Gemini (Recommended):**
1. Visit https://makersuite.google.com/app/apikey
2. Click "Create API Key"
3. Copy and use as `GEMINI_API_KEY`

**Groq:**
1. Visit https://console.groq.com/keys
2. Create a new API key
3. Copy and use as `GROQ_API_KEY`

---

## File Descriptions

### Hugging Face Space (`huggingface-space/`)

The Gradio-based demo application that provides a web interface for Trinity validation. This is the easiest way for users to try the system without installation.

**Key Files:**
- `app.py` - Complete Gradio application with Trinity validation logic
- `requirements.txt` - Python dependencies for the Space
- `README.md` - Space documentation and metadata

### TypeScript MCP Server (`typescript-mcp-server/`)

Native TypeScript implementation for deployment on Smithery.ai edge infrastructure. This version is optimized for the MCP ecosystem and provides the same functionality as the Python server.

**Key Files:**
- `src/index.ts` - Main server implementation with all agents
- `package.json` - Node.js dependencies and scripts
- `tsconfig.json` - TypeScript compiler configuration
- `README.md` - Server documentation

### Python MCP Server (`python-mcp-server/`)

Production-ready Python implementation deployed on Google Cloud Run. This is the primary server that powers the production API.

**Key Files:**
- `src/verifimind_peas/main.py` - Main server with FastAPI + FastMCP
- `src/verifimind_peas/__init__.py` - Package initialization
- `tests/test_agents.py` - Unit tests for agents
- `pyproject.toml` - Python project configuration
- `requirements.txt` - Python dependencies
- `README.md` - Server documentation

### Documentation (`documentation/`)

Comprehensive documentation covering the development journey, deployment guides, and integration instructions.

**Key Files:**
- `DEVELOPMENT_JOURNEY.md` - Complete 87-day development chronicle
- `QUICKSTART.md` - 5-minute getting started guide
- `GCP_DEPLOYMENT_GUIDE.md` - Google Cloud Run deployment instructions
- `CLAUDE_DESKTOP_SETUP.md` - Claude Desktop MCP integration guide

### Configuration Files (`configs/`)

All configuration files needed for deployment and development.

**Key Files:**
- `smithery.yaml` - Smithery.ai server configuration
- `Dockerfile` - Production Docker image definition
- `docker-compose.yml` - Local development setup
- `cloudbuild.yaml` - GCP CI/CD pipeline configuration
- `.env.example` - Environment variables template
- `LICENSE` - MIT License

---

## Development

### Prerequisites

- Python 3.11+
- Node.js 18+
- Docker (optional)
- Google Cloud CLI (for GCP deployment)

### Local Development (Python)

```bash
cd python-mcp-server
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows
pip install -e ".[dev]"
export GEMINI_API_KEY=your-key
python -m verifimind_peas.main
```

### Local Development (TypeScript)

```bash
cd typescript-mcp-server
npm install
npm run dev
```

### Running Tests

```bash
cd python-mcp-server
pytest tests/ -v
```

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Human Orchestrator                        │
│                 (Strategic Direction)                        │
└─────────────────────────┬───────────────────────────────────┘
                          │
          ┌───────────────┼───────────────┐
          ▼               ▼               ▼
    ┌──────────┐    ┌──────────┐    ┌──────────┐
    │ X-Agent  │    │ Z-Agent  │    │ CS-Agent │
    │Innovation│    │ Ethics   │    │ Security │
    │  💡      │    │  🛡️     │    │  🔍      │
    └────┬─────┘    └────┬─────┘    └────┬─────┘
         │               │               │
         └───────────────┼───────────────┘
                         ▼
              ┌─────────────────────┐
              │  Trinity Synthesis  │
              │    🔮 Combined      │
              │     Analysis        │
              └─────────────────────┘
```

---

## License

MIT License - See `configs/LICENSE` for details.

The Genesis Prompt Engineering Methodology is protected by defensive publication (DOI: 10.5281/zenodo.17645665).

---

## Contact

**Author:** Alton Lee Wei Bin  
**Email:** creator35lwb@gmail.com  
**GitHub:** [@creator35lwb-web](https://github.com/creator35lwb-web)  
**X (Twitter):** [@creator35lwb](https://x.com/creator35lwb)  

---

## Acknowledgments

This project is part of the **YSenseAI Ecosystem** and was developed using the **Genesis Prompt Engineering Methodology**—a systematic approach to multi-model AI validation that ensures ethical, secure, and innovative AI development.

---

*Last Updated: December 25, 2025*  
*Version: 1.0.0*
