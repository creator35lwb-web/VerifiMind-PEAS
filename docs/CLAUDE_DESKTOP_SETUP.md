# Claude Desktop MCP Integration Guide

**Version:** 0.2.3  
**Last Updated:** December 23, 2025

---

## Overview

This guide explains how to integrate the VerifiMind PEAS MCP Server with Claude Desktop (Claude.ai) for testing the RefleXion Trinity AI validation system.

## Prerequisites

1. **Claude Desktop** application installed
2. **VerifiMind MCP Server** deployed (either locally or on GCP)

---

## Configuration File Location

Claude Desktop reads MCP server configurations from:

| OS | Configuration Path |
|----|-------------------|
| **macOS** | `~/Library/Application Support/Claude/claude_desktop_config.json` |
| **Windows** | `%APPDATA%\Claude\claude_desktop_config.json` |
| **Linux** | `~/.config/Claude/claude_desktop_config.json` |

---

## Configuration for Live Server

Add this configuration to connect to the deployed server at `verifimind.ysenseai.org`:

```json
{
  "mcpServers": {
    "verifimind-genesis": {
      "url": "https://verifimind.ysenseai.org/mcp/",
      "transport": "streamable-http",
      "headers": {
        "Accept": "application/json, text/event-stream",
        "Content-Type": "application/json"
      }
    }
  }
}
```

---

## Configuration for Local Testing

If running the server locally:

```json
{
  "mcpServers": {
    "verifimind-genesis-local": {
      "url": "http://localhost:8080/mcp/",
      "transport": "streamable-http",
      "headers": {
        "Accept": "application/json, text/event-stream",
        "Content-Type": "application/json"
      }
    }
  }
}
```

---

## Configuration with BYOK (Bring Your Own Key)

To use your own API keys via Smithery session config:

```json
{
  "mcpServers": {
    "verifimind-genesis": {
      "url": "https://verifimind.ysenseai.org/mcp/?llm_provider=gemini&gemini_api_key=YOUR_GEMINI_API_KEY",
      "transport": "streamable-http",
      "headers": {
        "Accept": "application/json, text/event-stream",
        "Content-Type": "application/json"
      }
    }
  }
}
```

### Supported BYOK Parameters

| Parameter | Description | Example |
|-----------|-------------|---------|
| `llm_provider` | Provider to use | `gemini`, `anthropic`, `openai`, `mock` |
| `gemini_api_key` | Google Gemini API key | `AIza...` |
| `anthropic_api_key` | Anthropic API key | `sk-ant-...` |
| `openai_api_key` | OpenAI API key | `sk-...` |

---

## Testing the Integration

After configuring Claude Desktop, restart the application and try these prompts:

### Test 1: List Available Tools

```
What MCP tools are available from verifimind-genesis?
```

Expected: Claude should list 4 tools (consult_agent_x, consult_agent_z, consult_agent_cs, run_full_trinity)

### Test 2: Consult X Agent

```
Use the consult_agent_x tool to analyze this concept:
- Name: "AI-Powered Customer Support"
- Description: "An AI chatbot that handles customer inquiries 24/7 with natural language understanding"
```

Expected: X Agent analysis with innovation score, strategic value, opportunities, and risks.

### Test 3: Full Trinity Validation

```
Run a full Trinity validation on this concept:
- Name: "Autonomous Drone Delivery"
- Description: "A system of autonomous drones that deliver packages in urban areas"
```

Expected: Complete X→Z→CS analysis with synthesis and overall recommendation.

### Test 4: Check Resources

```
Read the genesis://config/master_prompt resource to see the Genesis Master Prompt.
```

Expected: The full Genesis Master Prompt v16.1 defining agent roles.

---

## Troubleshooting

### Issue: Server Not Found

**Symptoms:** Claude reports it cannot connect to the MCP server  
**Solutions:**
1. Verify the URL is correct (include trailing slash: `/mcp/`)
2. Check if the server is running: `curl https://verifimind.ysenseai.org/health`
3. Restart Claude Desktop after config changes

### Issue: Tools Not Appearing

**Symptoms:** Claude doesn't recognize the MCP tools  
**Solutions:**
1. Ensure the config file is valid JSON
2. Check the transport is set to `streamable-http`
3. Verify headers include both Accept types

### Issue: Tool Calls Fail

**Symptoms:** Tool calls return errors  
**Solutions:**
1. Check server logs for errors
2. Verify BYOK parameters are correct (if using)
3. Try with `mock` provider first to isolate issues

---

## Available Tools Reference

### consult_agent_x

**Purpose:** Innovation and strategy analysis

**Parameters:**
- `concept_name` (required): Short name of the concept
- `concept_description` (required): Detailed description
- `context` (optional): Additional background

**Returns:** Innovation score, strategic value, opportunities, risks, recommendation

### consult_agent_z

**Purpose:** Ethics and safety review (has VETO power)

**Parameters:**
- `concept_name` (required): Short name of the concept
- `concept_description` (required): Detailed description
- `context` (optional): Additional background
- `prior_reasoning` (optional): X agent's analysis

**Returns:** Ethics score, Z-Protocol compliance, veto status, ethical concerns

### consult_agent_cs

**Purpose:** Security and feasibility validation

**Parameters:**
- `concept_name` (required): Short name of the concept
- `concept_description` (required): Detailed description
- `context` (optional): Additional background
- `prior_reasoning` (optional): X and Z agents' analysis

**Returns:** Security score, vulnerabilities, attack vectors, Socratic questions

### run_full_trinity

**Purpose:** Complete X→Z→CS validation pipeline

**Parameters:**
- `concept_name` (required): Short name of the concept
- `concept_description` (required): Detailed description
- `context` (optional): Additional background
- `save_to_history` (optional): Whether to save result (default: true)

**Returns:** Complete Trinity validation with synthesis and overall recommendation

---

## Support

- **Repository:** https://github.com/creator35lwb-web/VerifiMind-PEAS
- **Issues:** https://github.com/creator35lwb-web/VerifiMind-PEAS/issues
- **Documentation:** https://doi.org/10.5281/zenodo.17645665
