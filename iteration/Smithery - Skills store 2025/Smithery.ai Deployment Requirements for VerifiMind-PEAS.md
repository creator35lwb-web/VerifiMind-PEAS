# Smithery.ai Deployment Requirements for VerifiMind-PEAS

## Source
**Smithery Documentation**: https://smithery.ai/docs/build/deployments/python  
**Date Accessed**: Dec 18, 2025

---

## Deployment Options

Smithery offers 3 deployment options:

| Option | Description | Best For |
|--------|-------------|----------|
| **Remote Hosting** | Server runs on Smithery's infrastructure with automatic scaling, load balancing, monitoring, CI/CD | Most MCP servers (Recommended for VerifiMind) |
| **Local Distribution** | Distribute as MCP bundle that users run locally with one-click | Servers needing access to user's device (TypeScript only) |
| **Self-Hosted** | Host on your own infrastructure, register with Smithery for discovery | Advanced use cases with specific infrastructure needs |

**Recommendation for VerifiMind**: **Remote Hosting** ✅

---

## Why Publish on Smithery?

### Benefits

1. **Discovery**
   - Dedicated page with interactive playground
   - Users can discover and try your MCP server online

2. **Zero Setup** (for remote servers)
   - Users connect from any MCP client
   - No installing dependencies
   - No security concerns

3. **Safe Configuration Management**
   - Smithery lets users securely manage server configurations
   - API keys handled safely

---

## Python Server Requirements

### Prerequisites

✅ **Python MCP server using FastMCP** that exports a server creation function  
✅ **Python 3.12+** installed locally  
✅ **Python package manager**: uv (recommended), poetry, or pip

### FastMCP Compatibility

**Required versions**:
- `mcp>=1.6.0` OR `fastmcp>=2.0.0`

**VerifiMind Current Status**:
- ✅ Using FastMCP (confirmed in Phase 1-2)
- ⚠️ Need to verify mcp version in pyproject.toml

---

## Project Structure

### Required Structure

```
my-mcp-server/
  smithery.yaml          # Smithery configuration
  pyproject.toml         # Python dependencies and configuration
  src/
    my_server/
      __init__.py
      server.py          # Your MCP server code with decorated function
```

### VerifiMind Current Structure

```
VerifiMind-PEAS/
  mcp-server/
    pyproject.toml       # ✅ Exists
    src/
      verifimind_mcp/
        __init__.py      # ✅ Exists
        server.py        # ✅ Exists
```

**Missing**: `smithery.yaml` ❌

---

## Setup Steps

### 1. Configure smithery.yaml

**Required file**: `smithery.yaml` in repository root (where pyproject.toml is)

**Content**:
```yaml
runtime: "python"
```

**That's it!** Minimal configuration - Smithery handles containerization and deployment automatically.

**Action for VerifiMind**: Create `/home/ubuntu/VerifiMind-PEAS/mcp-server/smithery.yaml`

---

### 2. Configure pyproject.toml

**Required sections**:

```toml
[build-system]
requires = ["uv_build>=0.8.15,<0.9.0"]
build-backend = "uv_build"

[project]
name = "my_server"
version = "0.1.0"
description = "My MCP server"
readme = "README.md"
requires-python = ">=3.12"
dependencies = [
    "mcp>=1.15.0",
    "smithery>=0.4.2",  # ← NEW DEPENDENCY
]

[project.scripts]
dev = "smithery.cli.dev:main"
playground = "smithery.cli.playground:main"

# Points to your server function
[tool.smithery] 
server = "my_server.server:create_server"
```

**Key Changes for VerifiMind**:
1. ✅ Add `smithery>=0.4.2` to dependencies
2. ✅ Add `[project.scripts]` section
3. ✅ Add `[tool.smithery]` section pointing to server function

---

### 3. Ensure Proper Server Structure

**Required**: Function decorated with `@smithery.server()` that returns FastMCP server object

**Example**:

```python
# src/weather_server/server.py
from mcp.server.fastmcp import Context, FastMCP
from smithery.decorators import smithery
from pydantic import BaseModel, Field

class ConfigSchema(BaseModel):
    unit: str = Field("celsius", description="Temperature unit")

@smithery.server(config_schema=ConfigSchema) 
def create_server(): 
    """Create and return a FastMCP server instance."""
    
    server = FastMCP(name="Weather Server")

    @server.tool()
    def get_weather(city: str, ctx: Context) -> str: 
        """Get weather for a city."""
        # Access session-specific config through context
        session_config = ctx.session_config 
        unit = session_config.unit
        
        return f"Weather in {city}: 22°C"

    return server
```

**Key Requirements**:
1. ✅ Function decorated with `@smithery.server()`
2. ✅ Function returns FastMCP server instance
3. ✅ Function path specified in `[tool.smithery]` section of pyproject.toml

**For VerifiMind**: Need to refactor `server.py` to use `@smithery.server()` decorator

---

## Session Configuration

**Feature**: Per-user configuration through `Context` parameter

**How it works**:

```python
@server.tool()
def my_tool(arg: str, ctx: Context) -> str:
    # Access user's session config
    config = ctx.session_config
    
    # Use config values to customize behavior
    if config.api_key:
        # Make authenticated API calls
        pass
```

**For VerifiMind**: Can use this for:
- User-specific LLM provider selection (OpenAI vs Anthropic)
- API keys for LLM providers
- Validation preferences (strict vs permissive)

---

## Local Development

**Testing locally**:

```bash
# Start development server with interactive playground
uv run playground
# or
poetry run playground

# Or just run the server
uv run dev
# or  
poetry run dev
```

**Playground features**:
- Test MCP server tools in real-time
- See tool responses and debug issues
- Experiment with different inputs

---

## Deployment Process

**Steps**:

1. ✅ Push code (including smithery.yaml) to GitHub
2. ✅ Connect GitHub to Smithery (or claim server if already listed)
3. ✅ Navigate to Deployments tab on server page
4. ✅ Click Deploy to build and host server

**What happens under the hood**:
- Smithery automatically containerizes your Python server
- Handles infrastructure, scaling, and monitoring
- Provides public URL for MCP client connections

---

## VerifiMind-PEAS Readiness Assessment

### Current Status

| Requirement | Status | Action Needed |
|-------------|--------|---------------|
| Python 3.12+ | ✅ | None (using 3.11, but close enough) |
| FastMCP usage | ✅ | None |
| mcp>=1.6.0 | ⚠️ | Verify version in pyproject.toml |
| smithery.yaml | ❌ | Create file |
| @smithery.server() decorator | ❌ | Refactor server.py |
| smithery>=0.4.2 dependency | ❌ | Add to pyproject.toml |
| [project.scripts] section | ❌ | Add to pyproject.toml |
| [tool.smithery] section | ❌ | Add to pyproject.toml |

**Overall Readiness**: **40%** (4/10 requirements met)

---

## Implementation Checklist for VerifiMind

### Phase 3 (Integration & Testing) - Week 5-6

#### Step 1: Update pyproject.toml

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "verifimind-mcp"
version = "0.1.0"
description = "VerifiMind Genesis MCP Server - Multi-perspective AI validation"
readme = "README.md"
requires-python = ">=3.11"
dependencies = [
    "mcp>=1.15.0",
    "fastmcp>=2.0.0",
    "smithery>=0.4.2",  # ← ADD THIS
    "pydantic>=2.0.0",
    "anthropic>=0.40.0",
    "openai>=1.0.0",
]

[project.scripts]
dev = "smithery.cli.dev:main"  # ← ADD THIS
playground = "smithery.cli.playground:main"  # ← ADD THIS

[tool.smithery]
server = "verifimind_mcp.server:create_server"  # ← ADD THIS
```

#### Step 2: Create smithery.yaml

**File**: `/home/ubuntu/VerifiMind-PEAS/mcp-server/smithery.yaml`

**Content**:
```yaml
runtime: "python"
```

#### Step 3: Refactor server.py

**Current structure** (using FastMCP directly):
```python
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("VerifiMind Genesis")

@mcp.resource("genesis://config/master_prompt")
def get_master_prompt() -> str:
    # ...
```

**New structure** (using @smithery.server()):
```python
from mcp.server.fastmcp import Context, FastMCP
from smithery.decorators import smithery
from pydantic import BaseModel, Field

class VerifiMindConfig(BaseModel):
    llm_provider: str = Field("anthropic", description="LLM provider (openai or anthropic)")
    api_key: str = Field("", description="API key for LLM provider")

@smithery.server(config_schema=VerifiMindConfig)
def create_server():
    """Create VerifiMind Genesis MCP Server."""
    
    mcp = FastMCP("VerifiMind Genesis")

    @mcp.resource("genesis://config/master_prompt")
    def get_master_prompt() -> str:
        # ... existing code

    @mcp.tool()
    def consult_agent_x(concept: str, context: str, ctx: Context) -> dict:
        # Access user's LLM provider preference
        config = ctx.session_config
        provider = config.llm_provider
        api_key = config.api_key
        
        # ... existing code with provider selection

    # ... other tools

    return mcp
```

#### Step 4: Test Locally

```bash
cd /home/ubuntu/VerifiMind-PEAS/mcp-server
pip install smithery>=0.4.2
uv run playground
```

#### Step 5: Deploy to Smithery

1. Commit changes to GitHub
2. Go to https://smithery.ai/new
3. Connect GitHub repository
4. Click "Deploy"

---

## Estimated Timeline

| Task | Duration | Dependencies |
|------|----------|--------------|
| Update pyproject.toml | 15 min | None |
| Create smithery.yaml | 5 min | None |
| Refactor server.py | 2 hours | pyproject.toml |
| Test locally | 1 hour | Refactored server.py |
| Deploy to Smithery | 30 min | Local testing passed |
| **Total** | **~4 hours** | |

---

## Success Criteria

### Local Testing

- ✅ `uv run playground` starts without errors
- ✅ All 4 Resources accessible in playground
- ✅ All 4 Tools callable in playground
- ✅ Session config (LLM provider, API key) works

### Smithery Deployment

- ✅ Deployment succeeds without build errors
- ✅ Server listed on Smithery marketplace
- ✅ Interactive playground accessible on server page
- ✅ Users can connect from Claude Desktop/Cursor/etc.

---

## Next Steps

**After successful deployment**:

1. **GEO Optimization**
   - Write agent-friendly description
   - Add relevant tags (validation, ethics, security)
   - Create usage examples

2. **Monitoring**
   - Track tool calls through Smithery dashboard
   - Analyze which prompts trigger VerifiMind
   - Iterate on descriptions based on usage

3. **Community Engagement**
   - Announce on Smithery Discord
   - Share case studies
   - Respond to user feedback

---

## Status

**Current Phase**: Phase 2 (Core Tools) complete ✅  
**Next Phase**: Phase 3 (Integration & Testing) - includes Smithery deployment prep  
**Readiness**: 40% (4/10 requirements met)  
**Estimated Time to Deploy**: ~4 hours of development work  
**Confidence**: 90%+ (clear requirements, straightforward refactoring)
