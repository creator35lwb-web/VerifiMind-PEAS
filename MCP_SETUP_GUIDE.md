# VerifiMind™ PEAS - MCP Server Setup Guide

**Connect your AI assistant to the RefleXion Trinity validation system in minutes.**

---

## Quick Start (Copy & Paste)

### Claude Code

Open **Settings > MCP Servers** and add:

```json
{
  "mcpServers": {
    "verifimind-genesis": {
      "url": "https://verifimind.ysenseai.org/mcp",
      "transport": "http-sse"
    }
  }
}
```

### Claude Desktop

Edit your configuration file:
- **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

Add the same configuration as above.

### Cursor

Open Settings (Cmd/Ctrl+Shift+P > "Preferences: Open Settings (JSON)") and add:

```json
{
  "mcp.servers": {
    "verifimind-genesis": {
      "url": "https://verifimind.ysenseai.org/mcp",
      "transport": "http-sse"
    }
  }
}
```

---

## One-Click Setup Script

For automated setup, run:

```bash
curl -fsSL https://raw.githubusercontent.com/creator35lwb-web/VerifiMind-PEAS/main/scripts/setup-mcp.sh | bash
```

Or clone and run locally:

```bash
git clone https://github.com/creator35lwb-web/VerifiMind-PEAS.git
cd VerifiMind-PEAS
chmod +x scripts/setup-mcp.sh
./scripts/setup-mcp.sh
```

---

## Available Tools

The MCP server provides four validation tools based on the RefleXion Trinity methodology:

| Tool | Model | Description |
|------|-------|-------------|
| `consult_agent_x` | Gemini 2.0 Flash (FREE) | Innovation & Strategy Analysis - Evaluates ideas for market potential, competitive advantage, and strategic value |
| `consult_agent_z` | Claude 3 Haiku | Ethics & Safety Review - Assesses ethical implications, safety considerations, and potential risks |
| `consult_agent_cs` | Claude 3 Haiku | Security & Feasibility Validation - Analyzes technical feasibility, security aspects, and implementation challenges |
| `run_full_trinity` | Multi-Model | Complete X → Z → CS Validation - Runs all three agents in sequence for comprehensive analysis |

---

## Usage Examples

Once connected, you can use the tools directly in your AI conversations:

### Single Agent Consultation

```
"Use the consult_agent_x tool to analyze my startup idea: 
A platform that connects local farmers directly with restaurants."
```

### Full Trinity Validation

```
"Run the full trinity validation on my project concept:
An AI-powered code review system for enterprise teams."
```

### Specific Concerns

```
"Use consult_agent_z to evaluate the ethical implications of 
using facial recognition for attendance tracking in schools."
```

---

## BYOK v0.3.0 (Bring Your Own Keys)

VerifiMind PEAS supports **7 LLM providers** with automatic fallback support. Choose based on your needs:

### Supported Providers

| Provider | Free Tier | Default Model | Notes |
|----------|-----------|---------------|-------|
| **Gemini** | Yes | gemini-1.5-flash | Recommended for free usage |
| **Groq** | Yes | llama-3.3-70b-versatile | Fast inference, generous limits |
| **OpenAI** | No | gpt-4o-mini | Most capable models |
| **Anthropic** | No | claude-3-5-sonnet-20241022 | Best for complex reasoning |
| **Mistral** | No | mistral-small-latest | Good balance of cost/performance |
| **Ollama** | Yes (local) | llama3.2 | Run locally, complete privacy |
| **Mock** | Yes | mock-v1 | For testing only |

### Environment Variables

Set these in your environment:

```bash
# Primary provider (choose one)
export LLM_PROVIDER="gemini"  # Options: gemini, groq, openai, anthropic, mistral, ollama, mock

# Fallback if primary fails (optional)
export LLM_FALLBACK_PROVIDER="mock"

# API key for your chosen provider
export GEMINI_API_KEY="your-gemini-key"        # FREE tier available!
export GROQ_API_KEY="your-groq-key"            # FREE tier available!
export OPENAI_API_KEY="your-openai-key"
export ANTHROPIC_API_KEY="your-anthropic-key"
export MISTRAL_API_KEY="your-mistral-key"

# Optional: Override default model
export LLM_MODEL="gemini-1.5-pro"

# Optional: Override parameters
export LLM_TEMPERATURE="0.7"
export LLM_MAX_TOKENS="4096"
```

### Get Free API Keys

1. **Google Gemini (Recommended)**: https://aistudio.google.com/apikey
2. **Groq**: https://console.groq.com/keys
3. **Ollama (Local)**: https://ollama.ai - No API key needed!

### Benefits of BYOK
- Choose your preferred provider
- Higher rate limits with your own keys
- Use your own billing
- Access to premium models
- Full control over API usage
- Automatic fallback if primary fails

---

## Self-Hosting

For full control and privacy, you can run your own VerifiMind PEAS instance:

### Prerequisites
- Python 3.11+
- API keys for Anthropic and/or Google Gemini

### Quick Start

```bash
git clone https://github.com/creator35lwb-web/VerifiMind-PEAS.git
cd VerifiMind-PEAS
pip install -r requirements.txt
python -m verifimind.server
```

### Docker

```bash
docker pull ysenseai/verifimind-peas
docker run -p 8000:8000 -e ANTHROPIC_API_KEY=xxx ysenseai/verifimind-peas
```

---

## Troubleshooting

### Connection Issues

**Problem**: "Unable to connect to MCP server"

**Solutions**:
1. Verify the server is online: https://verifimind.ysenseai.org/health
2. Check your network allows HTTPS connections
3. Ensure the URL uses `https://` not `http://`
4. Restart your AI client after adding the configuration

### Authentication Errors

**Problem**: "Authentication failed" or "Invalid API key"

**Solutions**:
1. The public server doesn't require authentication for basic use
2. If using BYOK, verify your API keys are correctly set
3. Check that environment variables are exported in your shell

### Rate Limiting

**Problem**: "Rate limit exceeded"

**Solutions**:
1. Wait a few minutes and try again
2. Consider using BYOK for higher limits
3. Use `consult_agent_x` (Gemini) which has generous free tier

### Tool Not Found

**Problem**: "Tool 'consult_agent_x' not found"

**Solutions**:
1. Verify the MCP configuration is correct
2. Restart your AI client
3. Check the server status at https://verifimind.ysenseai.org/health

---

## Verification

After setup, verify the connection by asking your AI:

```
"List the available MCP tools from the verifimind-genesis server."
```

You should see the four tools: `consult_agent_x`, `consult_agent_z`, `consult_agent_cs`, and `run_full_trinity`.

---

## Resources

| Resource | Link |
|----------|------|
| Live Server | https://verifimind.ysenseai.org |
| Health Check | https://verifimind.ysenseai.org/health |
| MCP Config | https://verifimind.ysenseai.org/.well-known/mcp-config |
| GitHub Repository | https://github.com/creator35lwb-web/VerifiMind-PEAS |
| White Paper | https://doi.org/10.5281/zenodo.17645665 |
| Landing Page | https://verifimind.ysenseai.org |

---

## Support

- **GitHub Issues**: [Report a bug](https://github.com/creator35lwb-web/VerifiMind-PEAS/issues)
- **GitHub Discussions**: [Ask questions](https://github.com/creator35lwb-web/VerifiMind-PEAS/discussions)
- **Twitter/X**: [@creator35lwb](https://twitter.com/creator35lwb)

---

**VerifiMind™ PEAS** - Multi-Agent AI Validation System  
Powered by the Genesis Prompt Engineering Methodology  
© 2025 Alton Lee Wei Bin. Protected by defensive publication.
