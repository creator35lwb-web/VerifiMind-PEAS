# VerifiMind PEAS Quick Start Guide

Get started with VerifiMind PEAS MCP Server in under 5 minutes.

---

## Installation Options

### Option 1: Smithery (Recommended)

The easiest way to use VerifiMind PEAS is through Smithery.ai:

**For Claude Desktop:**
```bash
npx -y @smithery/cli@latest install creator35lwb-web/verifimind-genesis --client claude
```

**For Claude Code:**
```bash
npx -y @smithery/cli@latest install creator35lwb-web/verifimind-genesis --client claude-code
```

**For Cursor:**
```bash
npx -y @smithery/cli@latest install creator35lwb-web/verifimind-genesis --client cursor
```

### Option 2: Direct URL

Add to your MCP client configuration:

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

---

## Available Tools

| Tool | Description |
|------|-------------|
| `consult_agent_x` | Innovation & Strategy analysis |
| `consult_agent_z` | Ethics & Z-Protocol validation |
| `consult_agent_cs` | Security & vulnerability assessment |
| `run_full_trinity` | Complete X → Z → CS validation |

---

## Example Usage

### Single Agent Consultation

```
Use consult_agent_x to analyze "AI-powered code review tool"
```

**Response:**
- Innovation Score: 7.5/10
- Strategic Value: 8.0/10
- Opportunities: Market differentiation, efficiency gains
- Risks: Competition, technical complexity

### Full Trinity Validation

```
Use run_full_trinity to validate "Autonomous drone delivery service"
```

**Response:**
- X Agent: Innovation analysis
- Z Agent: Ethical review (with VETO power)
- CS Agent: Security assessment
- Synthesis: Overall recommendation

---

## Provider Configuration (BYOK)

By default, the server uses **mock responses** for testing. To enable real AI analysis:

### Free Options

| Provider | How to Get API Key |
|----------|-------------------|
| **Gemini** | [Google AI Studio](https://aistudio.google.com/apikey) |
| **Groq** | [Groq Console](https://console.groq.com/keys) |

### Paid Options

| Provider | How to Get API Key |
|----------|-------------------|
| **Anthropic** | [Anthropic Console](https://console.anthropic.com/) |
| **OpenAI** | [OpenAI Platform](https://platform.openai.com/api-keys) |

---

## Links

- **Smithery Page**: https://smithery.ai/server/creator35lwb-web/verifimind-genesis
- **GitHub (Python)**: https://github.com/creator35lwb-web/VerifiMind-PEAS
- **GitHub (TypeScript)**: https://github.com/creator35lwb-web/verifimind-genesis-mcp
- **Documentation**: https://github.com/creator35lwb-web/VerifiMind-PEAS/tree/main/docs

---

## Support

For issues or questions:
- Open an issue on [GitHub](https://github.com/creator35lwb-web/VerifiMind-PEAS/issues)
- Visit [YSenseAI](https://ysenseai.org)

---

*Happy validating! 🚀*
