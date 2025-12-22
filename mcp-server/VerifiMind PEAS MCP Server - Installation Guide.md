# VerifiMind PEAS MCP Server - Installation Guide

**Version**: 0.2.0  
**Last Updated**: December 21, 2024  
**Author**: Manus AI

---

## Overview

The VerifiMind PEAS MCP Server provides access to the Genesis Methodology validation framework through the Model Context Protocol. This server enables AI assistants like Claude to consult three specialized agents—X Intelligent (innovation), Z Guardian (ethics), and CS Security (security)—for comprehensive concept validation.

---

## System Requirements

The server requires Python 3.11 or higher and works on macOS, Linux, and Windows systems. Before installation, ensure your system meets the following prerequisites:

| Requirement | Minimum Version | Recommended Version |
|------------|----------------|---------------------|
| Python | 3.11 | 3.12 |
| pip | 23.0 | Latest |
| Git | 2.30 | Latest |
| Available RAM | 512 MB | 1 GB |
| Disk Space | 100 MB | 500 MB |

---

## Installation Steps

### Step 1: Clone the Repository

Begin by cloning the VerifiMind PEAS repository to your local machine:

```bash
git clone https://github.com/creator35lwb-web/VerifiMind-PEAS.git
cd VerifiMind-PEAS/mcp-server
```

This command downloads the complete project including the MCP server implementation, master prompts, and validation history.

### Step 2: Install Dependencies

The server uses modern Python packaging tools for dependency management. Install the required packages using pip:

```bash
pip install -e .
```

The `-e` flag installs the package in editable mode, allowing you to modify the source code without reinstalling. This command installs all required dependencies including FastMCP, Pydantic, and LLM provider libraries.

### Step 3: Configure LLM Provider (Optional)

The server supports three LLM providers for agent consultations. While the mock provider works without configuration, real LLM providers require API keys for full functionality.

#### Option A: OpenAI (Recommended)

Create a `.env` file in the `mcp-server` directory:

```bash
OPENAI_API_KEY=sk-your-openai-api-key-here
```

OpenAI provides robust language models with good performance for validation tasks. The server uses GPT-4 by default when OpenAI is configured.

#### Option B: Anthropic

Alternatively, configure Anthropic's Claude models:

```bash
ANTHROPIC_API_KEY=sk-ant-your-anthropic-api-key-here
```

Anthropic's models excel at nuanced reasoning and ethical analysis, making them particularly suitable for Z Guardian consultations.

#### Option C: Mock Provider (Testing)

For testing purposes, the server includes a mock provider that generates simulated responses without requiring API keys. This mode is automatically used when no API keys are configured.

---

## Claude Desktop Integration

To use the VerifiMind PEAS MCP Server with Claude Desktop, you need to register the server in Claude's configuration file.

### Locate Configuration File

The Claude Desktop configuration file location varies by operating system:

| Operating System | Configuration Path |
|-----------------|-------------------|
| macOS | `~/Library/Application Support/Claude/claude_desktop_config.json` |
| Windows | `%APPDATA%\Claude\claude_desktop_config.json` |
| Linux | `~/.config/Claude/claude_desktop_config.json` |

### Add Server Configuration

Open the configuration file in a text editor and add the VerifiMind PEAS server to the `mcpServers` section:

```json
{
  "mcpServers": {
    "verifimind-genesis": {
      "command": "python",
      "args": [
        "-m",
        "src.verifimind_mcp.server"
      ],
      "cwd": "/absolute/path/to/VerifiMind-PEAS/mcp-server",
      "env": {
        "OPENAI_API_KEY": "sk-your-key-here"
      }
    }
  }
}
```

**Important**: Replace `/absolute/path/to/VerifiMind-PEAS/mcp-server` with the actual absolute path to your installation directory. The `env` section is optional if you configured API keys in a `.env` file.

### Restart Claude Desktop

After saving the configuration file, completely quit and restart Claude Desktop. The VerifiMind PEAS server will appear in the available tools list, indicated by a hammer icon in the Claude interface.

---

## Verification

To verify the installation, you can test the server directly from the command line before integrating with Claude Desktop.

### Test Server Startup

Run the following command to start the server in standalone mode:

```bash
python -m src.verifimind_mcp.server
```

If the server starts successfully, you will see output indicating that the MCP server is running and listening for connections. Press `Ctrl+C` to stop the server.

### Test in Claude Desktop

Once integrated with Claude Desktop, verify the installation by asking Claude to use the VerifiMind tools. Try this prompt:

> "Use the consult_agent_x tool to analyze the innovation potential of a concept called 'AI-powered code review assistant'."

Claude should successfully invoke the tool and return a structured analysis from the X Intelligent agent.

---

## Available Resources and Tools

The VerifiMind PEAS MCP Server exposes four resources and four tools through the Model Context Protocol.

### Resources

Resources provide read-only access to validation context and project information:

| Resource URI | Description | Format |
|-------------|-------------|--------|
| `genesis://config/master_prompt` | Complete Genesis Master Prompt v16.1 defining agent roles | Markdown |
| `genesis://history/latest` | Most recent validation result with all agent perspectives | JSON |
| `genesis://history/all` | Complete validation history from all past consultations | JSON |
| `genesis://state/project_info` | Project metadata, architecture, and documentation links | JSON |

### Tools

Tools enable active consultation with the three validation agents:

| Tool Name | Purpose | Key Capabilities |
|-----------|---------|------------------|
| `consult_agent_x` | Innovation and strategy analysis | Innovation potential, strategic value, market opportunities |
| `consult_agent_z` | Ethical review and Z-Protocol enforcement | Ethics, privacy, bias detection, social impact (with veto power) |
| `consult_agent_cs` | Security validation | Vulnerability assessment, attack vectors, Socratic interrogation |
| `run_full_trinity` | Complete validation pipeline | Orchestrates all three agents with conflict resolution |

Each tool accepts a concept name, description, and optional context. The tools return structured analyses with reasoning chains, scores, and actionable recommendations.

---

## Troubleshooting

### Server Fails to Start

If the server fails to start, verify that all dependencies are correctly installed:

```bash
pip install --upgrade -e .
```

Ensure you are using Python 3.11 or higher by checking your version:

```bash
python --version
```

### Claude Desktop Doesn't Show Tools

If Claude Desktop does not display the VerifiMind tools after restart, check the following:

1. **Configuration Path**: Verify that you edited the correct `claude_desktop_config.json` file for your operating system.
2. **JSON Syntax**: Ensure the configuration file contains valid JSON with no syntax errors.
3. **Absolute Path**: Confirm that the `cwd` field contains an absolute path, not a relative path.
4. **Server Permissions**: Verify that the Python executable has permission to run the server script.

### API Key Errors

If you encounter API key errors when using real LLM providers, ensure your API keys are correctly configured:

```bash
# Test OpenAI key
python -c "import openai; openai.api_key='your-key'; print('✅ Key valid')"

# Test Anthropic key
python -c "import anthropic; print('✅ Anthropic installed')"
```

The mock provider will automatically activate if API keys are missing or invalid, allowing you to test the server functionality without incurring API costs.

---

## Advanced Configuration

### Custom Validation Mode

The server supports two validation modes that control the strictness of agent evaluations:

```json
{
  "mcpServers": {
    "verifimind-genesis": {
      "command": "python",
      "args": ["-m", "src.verifimind_mcp.server"],
      "cwd": "/path/to/mcp-server",
      "env": {
        "VALIDATION_MODE": "strict"
      }
    }
  }
}
```

**Standard mode** (default) applies balanced validation criteria suitable for most concepts. **Strict mode** increases scrutiny across all three agents, requiring higher scores for approval and triggering Z Guardian veto more readily.

### Master Prompt Customization

Advanced users can customize the agent behavior by modifying the master prompt file located at:

```
VerifiMind-PEAS/reflexion-master-prompts-v1.1.md
```

After modifying the master prompt, restart the MCP server to load the updated instructions. Custom prompts enable fine-tuning of agent personalities, evaluation criteria, and reasoning approaches.

---

## Next Steps

After successfully installing the VerifiMind PEAS MCP Server, you can begin validating concepts through Claude Desktop. The server maintains a validation history in `verifimind_history.json`, allowing you to track all consultations over time.

For deployment to production environments, consider hosting the server on Google Cloud Run for remote access. Detailed deployment instructions are available in the project repository.

To contribute to the VerifiMind PEAS project or report issues, visit the GitHub repository at https://github.com/creator35lwb-web/VerifiMind-PEAS.

---

## Support and Documentation

For additional support and documentation, refer to the following resources:

- **White Paper**: [Genesis Methodology White Paper v1.1](https://github.com/creator35lwb-web/VerifiMind-PEAS/docs/white_paper/Genesis_Methodology_White_Paper_v1.1.md)
- **Repository**: [VerifiMind-PEAS on GitHub](https://github.com/creator35lwb-web/VerifiMind-PEAS)
- **Master Prompts**: [RefleXion Master Prompts v1.1](https://github.com/creator35lwb-web/VerifiMind-PEAS/reflexion-master-prompts-v1.1.md)
- **Issues**: [GitHub Issues](https://github.com/creator35lwb-web/VerifiMind-PEAS/issues)

The VerifiMind PEAS project is actively maintained and welcomes contributions from the community. Whether you are validating AI concepts, extending the methodology, or integrating with new platforms, the Genesis Methodology provides a robust framework for ethical and secure AI development.
