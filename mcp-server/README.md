# VerifiMind MCP Server

**Model Context Protocol server for VerifiMind-PEAS Genesis Methodology**

![Version](https://img.shields.io/badge/version-0.1.0-blue)
![Python](https://img.shields.io/badge/python-3.11%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![Status](https://img.shields.io/badge/status-MVP-yellow)

---

## Overview

The VerifiMind MCP Server exposes the Genesis Methodology's RefleXion Trinity (X-Z-CS) validation framework through the Model Context Protocol. This enables AI applications like Claude Desktop, Cursor, and VS Code to access VerifiMind's validation capabilities directly through natural language conversation.

**Current Status**: **Week 1-2 MVP (Genesis Context Server)**

This MVP focuses on solving the "Linkage Point" problem: enabling multiple AI models to reference the exact same context without human re-transmission.

---

## What is MCP?

The Model Context Protocol (MCP) is an open standard for connecting AI applications to external systems. Think of MCP like **USB-C for AI** - a universal way to connect AI models to tools, data, and workflows.

**Learn more**: [Model Context Protocol Documentation](https://modelcontextprotocol.io/)

---

## Features (Week 1-2 MVP)

### **Resources Exposed**

The Genesis Context Server currently exposes four resources:

| **Resource URI** | **Description** | **Format** |
|------------------|-----------------|------------|
| `genesis://config/master_prompt` | Genesis Master Prompt v16.1 defining X, Z, CS agent roles | Markdown |
| `genesis://history/latest` | Most recent validation result from VerifiMind-PEAS | JSON |
| `genesis://history/all` | Complete validation history with metadata and statistics | JSON |
| `genesis://state/project_info` | Project metadata and architecture information | JSON |

**Resources** are application-controlled context that AI models can read to understand project state, methodology, and validation history. This eliminates manual copy-paste between different AI chat interfaces.

---

## Installation

### Prerequisites

- Python 3.11 or higher
- pip (Python package installer)
- VerifiMind-PEAS repository cloned locally

### Step 1: Clone Repository (if not already done)

```bash
git clone https://github.com/creator35lwb-web/VerifiMind-PEAS.git
cd VerifiMind-PEAS/mcp-server
```

### Step 2: Create Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### Step 3: Install Dependencies

```bash
pip install mcp fastmcp pydantic python-dotenv
```

### Step 4: Test Server

```bash
python src/verifimind_mcp/server.py
```

You should see output confirming all tests passed:

```
============================================================
Genesis Context Server - Week 1-2 MVP
============================================================

Testing resource loading...

1. Testing Master Prompt loading...
   ✓ Loaded 10012 characters
   
2. Testing validation history loading...
   ✓ Loaded 0 validations
   
3. Testing latest validation retrieval...
   ✓ Latest validation status: no_validations
   
4. Testing project info retrieval...
   ✓ Project: VerifiMind-PEAS
   ✓ Methodology: Genesis Methodology
   ✓ Version: 2.0.1

============================================================
All tests passed! Server is ready.
============================================================
```

---

## Configuration

### Claude Desktop

To use VerifiMind MCP Server with Claude Desktop, add the following to your Claude Desktop configuration file:

**macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`  
**Windows**: `%APPDATA%\Claude\claude_desktop_config.json`  
**Linux**: `~/.config/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "verifimind-genesis": {
      "command": "python",
      "args": [
        "-m",
        "verifimind_mcp.server"
      ],
      "cwd": "/absolute/path/to/VerifiMind-PEAS/mcp-server",
      "env": {
        "PYTHONPATH": "/absolute/path/to/VerifiMind-PEAS/mcp-server/src"
      }
    }
  }
}
```

**Important**: Replace `/absolute/path/to/VerifiMind-PEAS` with the actual absolute path to your VerifiMind-PEAS repository.

**Example** (macOS/Linux):
```json
{
  "mcpServers": {
    "verifimind-genesis": {
      "command": "/home/ubuntu/VerifiMind-PEAS/mcp-server/venv/bin/python",
      "args": [
        "-m",
        "verifimind_mcp.server"
      ],
      "cwd": "/home/ubuntu/VerifiMind-PEAS/mcp-server",
      "env": {
        "PYTHONPATH": "/home/ubuntu/VerifiMind-PEAS/mcp-server/src"
      }
    }
  }
}
```

After adding the configuration:
1. Restart Claude Desktop
2. Look for the 🔌 icon in the bottom-right corner
3. Click to see connected MCP servers
4. You should see "verifimind-genesis" listed

---

## Usage

Once configured, you can interact with VerifiMind resources through natural language in Claude Desktop:

### Example 1: Access Master Prompt

**You**: "Can you show me the Genesis Master Prompt?"

**Claude** (with MCP): *Reads from `genesis://config/master_prompt` and displays the complete Master Prompt v16.1*

### Example 2: Check Project Information

**You**: "What is the VerifiMind-PEAS project architecture?"

**Claude** (with MCP): *Reads from `genesis://state/project_info` and explains the RefleXion Trinity (X-Z-CS) architecture*

### Example 3: Review Validation History

**You**: "What was the result of the latest validation?"

**Claude** (with MCP): *Reads from `genesis://history/latest` and summarizes the validation result including X, Z, CS perspectives*

---

## Architecture

### Genesis Context Server (Week 1-2 MVP)

```
┌─────────────────────────────────────────────┐
│         Claude Desktop (Host)               │
│                                             │
│  ┌───────────────────────────────────────┐ │
│  │  MCP Client                           │ │
│  │  (Manages connection to server)       │ │
│  └───────────┬───────────────────────────┘ │
└──────────────┼─────────────────────────────┘
               │ JSON-RPC over stdio
               ↓
┌──────────────────────────────────────────────┐
│  Genesis Context Server (MCP Server)         │
│                                              │
│  Resources:                                  │
│  ├── genesis://config/master_prompt         │
│  ├── genesis://history/latest               │
│  ├── genesis://history/all                  │
│  └── genesis://state/project_info           │
│                                              │
│  Data Sources:                               │
│  ├── reflexion-master-prompts-v1.1.md       │
│  └── verifimind_history.json                │
└──────────────────────────────────────────────┘
```

---

## Roadmap

### ✅ Phase 1: Foundation (Week 1-2) - **CURRENT**

- [x] MCP server project structure
- [x] Genesis Context Server with Resources
- [x] Master Prompt exposure
- [x] Validation history exposure
- [x] Project information exposure
- [x] Local testing
- [x] Claude Desktop configuration

### 🚧 Phase 2: Core Tools (Week 3-4) - **NEXT**

- [ ] Implement `consult_agent_x()` tool
- [ ] Implement `consult_agent_z()` tool
- [ ] Implement `consult_agent_cs()` tool
- [ ] Implement `run_full_trinity()` tool
- [ ] Test parallel agent invocation
- [ ] Complete RefleXion Trinity through MCP

### 📅 Phase 3: State Management (Week 5-6)

- [ ] Implement session management (Streamable HTTP transport)
- [ ] Add `update_project_state()` tool with human approval workflow
- [ ] Integrate VersionTracker for persistent state
- [ ] Multi-turn validation workflow support

### 📅 Phase 4: Deployment (Week 7-8)

- [ ] Deploy to Smithery.ai hosted service
- [ ] Implement OAuth 2.1 authentication
- [ ] Add comprehensive logging for compliance
- [ ] Submit to GitHub MCP Registry
- [ ] Public release and community launch

---

## Development

### Project Structure

```
mcp-server/
├── pyproject.toml           # Project metadata and dependencies
├── README.md                # This file
├── src/
│   └── verifimind_mcp/
│       ├── __init__.py      # Package initialization
│       └── server.py        # Genesis Context Server implementation
├── tests/                   # Unit tests (coming in Phase 2)
├── examples/                # Usage examples and configurations
└── venv/                    # Virtual environment (created during installation)
```

### Running Tests

```bash
# Activate virtual environment
source venv/bin/activate

# Run server tests
python src/verifimind_mcp/server.py
```

### Code Style

This project follows:
- **Black** for code formatting (line length: 100)
- **Ruff** for linting
- **Type hints** for all function signatures

---

## Troubleshooting

### Issue: "ModuleNotFoundError: No module named 'mcp'"

**Solution**: Ensure you've activated the virtual environment and installed dependencies:

```bash
source venv/bin/activate
pip install mcp fastmcp pydantic python-dotenv
```

### Issue: "Master Prompt file not found"

**Solution**: Ensure you're running the server from the `mcp-server` directory and that `reflexion-master-prompts-v1.1.md` exists in the repository root:

```bash
cd /path/to/VerifiMind-PEAS/mcp-server
ls ../reflexion-master-prompts-v1.1.md  # Should exist
python src/verifimind_mcp/server.py
```

### Issue: "No validation history found"

**Solution**: This is expected for the MVP. Validation history is generated by running `verifimind_complete.py`. The MCP server will show a helpful message indicating no validations exist yet.

### Issue: Claude Desktop doesn't show the MCP server

**Solution**: 
1. Check that `claude_desktop_config.json` has correct absolute paths
2. Restart Claude Desktop completely (quit and reopen)
3. Check Claude Desktop logs for errors:
   - macOS: `~/Library/Logs/Claude/mcp*.log`
   - Windows: `%APPDATA%\Claude\logs\mcp*.log`

---

## Contributing

Contributions are welcome! This is an early-stage MVP, and we're actively developing new features.

**Areas for contribution**:
- Phase 2: Implementing Tools (agent consultation)
- Phase 3: State management and session handling
- Testing and documentation
- Integration with other IDEs (Cursor, VS Code, Windsurf)

Please see the main [VerifiMind-PEAS CONTRIBUTING.md](../CONTRIBUTING.md) for guidelines.

---

## License

MIT License - see [LICENSE](../LICENSE) for details.

---

## References

- [Model Context Protocol Documentation](https://modelcontextprotocol.io/)
- [VerifiMind-PEAS Main Repository](https://github.com/creator35lwb-web/VerifiMind-PEAS)
- [Genesis Methodology White Paper v1.1](../docs/white_paper/Genesis_Methodology_White_Paper_v1.1.md)
- [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk)
- [FastMCP Framework](https://github.com/jlowin/fastmcp)

---

## Support

For questions, issues, or feedback:

- **GitHub Discussions**: [VerifiMind-PEAS Discussions](https://github.com/creator35lwb-web/VerifiMind-PEAS/discussions)
- **GitHub Issues**: [Report a Bug](https://github.com/creator35lwb-web/VerifiMind-PEAS/issues)
- **Email**: creator35lwb@gmail.com

---

**Built with ❤️ by the VerifiMind-PEAS community**

**FLYWHEEL, TEAM!** 🚀
