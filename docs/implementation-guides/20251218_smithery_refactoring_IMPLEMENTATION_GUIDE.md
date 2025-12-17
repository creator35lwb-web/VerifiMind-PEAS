# Claude Code Implementation Guide: Smithery Refactoring (Option A - Minimal)

**Date**: December 18, 2025  
**Task**: Refactor VerifiMind-PEAS MCP server for Smithery deployment  
**Approach**: Option A (Minimal refactoring - 2 hours)  
**Target**: Smithery-ready codebase by end of today

---

## 📋 Context

**What we've done so far**:
- ✅ Created `smithery.yaml` in `/mcp-server/` directory
- ✅ Updated `pyproject.toml` with smithery dependencies and configuration

**What you need to do**:
- Refactor `/mcp-server/src/verifimind_mcp/server.py` to use `@smithery.server()` decorator
- Add minimal session config support
- Keep existing functionality intact (low-risk changes)

---

## 🎯 Implementation Steps

### Step 1: Add Imports (Top of server.py)

**Location**: After line 29 (`from mcp.server.fastmcp import FastMCP`)

**Add these imports**:

```python
from mcp.server.fastmcp import Context, FastMCP
from smithery.decorators import smithery
from pydantic import BaseModel, Field
```

**Result**: Now you have `Context` for session config and `smithery` decorator

---

### Step 2: Define Session Config Schema

**Location**: After imports, before `app = FastMCP(...)` line (around line 32)

**Add this config schema**:

```python
class VerifiMindConfig(BaseModel):
    """Session configuration for VerifiMind Genesis Server.
    
    Allows users to customize their validation experience.
    """
    llm_provider: str = Field(
        default="mock",
        description="LLM provider to use: 'openai', 'anthropic', or 'mock' (for testing)"
    )
    openai_api_key: str = Field(
        default="",
        description="OpenAI API key (optional, can also use OPENAI_API_KEY env var)"
    )
    anthropic_api_key: str = Field(
        default="",
        description="Anthropic API key (optional, can also use ANTHROPIC_API_KEY env var)"
    )
    validation_mode: str = Field(
        default="standard",
        description="Validation strictness: 'standard' or 'strict'"
    )
```

**Why**: This defines what configuration options users can set through Smithery

---

### Step 3: Wrap Existing Code in create_server() Function

**Current structure** (line 32):
```python
# Initialize MCP server
app = FastMCP("verifimind-genesis")
```

**Change to**:

```python
@smithery.server(config_schema=VerifiMindConfig)
def create_server():
    """Create and return VerifiMind Genesis MCP Server instance.
    
    This function is called by Smithery to initialize the server with
    user-specific configuration.
    """
    # Initialize MCP server
    app = FastMCP("verifimind-genesis")
    
    # [ALL EXISTING CODE GOES HERE - Resources and Tools]
    
    return app
```

**Important**: 
- Add `@smithery.server(config_schema=VerifiMindConfig)` decorator above the function
- Wrap ALL existing code (Resources, Tools, helper functions) inside `create_server()`
- Return `app` at the end
- Keep indentation consistent (everything inside the function should be indented 4 spaces)

---

### Step 4: Update Tool Signatures (Add ctx Parameter)

**For each Tool** (`consult_agent_x`, `consult_agent_z`, `consult_agent_cs`, `run_full_trinity`):

**Current signature** (example for consult_agent_x):
```python
@app.tool()
async def consult_agent_x(
    concept_name: str,
    concept_description: str,
    context: Optional[str] = None
) -> dict:
```

**Change to**:
```python
@app.tool()
async def consult_agent_x(
    concept_name: str,
    concept_description: str,
    context: Optional[str] = None,
    ctx: Context = None  # ← ADD THIS
) -> dict:
```

**Do this for all 4 tools**:
- `consult_agent_x`
- `consult_agent_z`
- `consult_agent_cs`
- `run_full_trinity`

**Why**: `ctx: Context` gives access to user's session configuration

---

### Step 5: Add Session Config Logic to get_provider()

**Location**: Inside each Tool, where `get_provider()` is called

**Current code** (example from consult_agent_x):
```python
# Get LLM provider (will use environment variables)
try:
    provider = get_provider()
except ValueError:
    # No API key configured - return mock response for testing
    return {
        "agent": "X Intelligent",
        "status": "mock_response",
        # ...
    }
```

**Change to**:
```python
# Get LLM provider (use session config if available, fallback to env vars)
try:
    if ctx and ctx.session_config:
        config = ctx.session_config
        
        # Use session config to select provider
        if config.llm_provider == "openai" and config.openai_api_key:
            from .llm import OpenAIProvider
            provider = OpenAIProvider(api_key=config.openai_api_key)
        elif config.llm_provider == "anthropic" and config.anthropic_api_key:
            from .llm import AnthropicProvider
            provider = AnthropicProvider(api_key=config.anthropic_api_key)
        else:
            # Fallback to mock provider if no keys provided
            from .llm import MockProvider
            provider = MockProvider()
    else:
        # No session config - use environment variables
        provider = get_provider()
        
except ValueError:
    # No API key configured - return mock response for testing
    from .llm import MockProvider
    provider = MockProvider()
```

**Do this for all 4 tools** where `get_provider()` is called

**Why**: This allows users to configure their LLM provider through Smithery UI

---

### Step 6: Keep Resources Unchanged

**Important**: Do NOT modify Resources (`get_master_prompt`, `get_latest_validation_resource`, `get_all_validations`, `get_project_info_resource`)

**Why**: Resources don't need session config - they're read-only data

---

### Step 7: Verify Indentation

**Critical**: After wrapping everything in `create_server()`, verify:
- All Resources are indented 4 spaces (inside function)
- All Tools are indented 4 spaces (inside function)
- All helper functions are indented 4 spaces (inside function)
- `return app` is at the end of `create_server()` function

---

## 🧪 Testing Checklist

After refactoring, test locally:

### Test 1: Import Check

```bash
cd /home/ubuntu/VerifiMind-PEAS/mcp-server
python3 -c "from src.verifimind_mcp.server import create_server; print('✅ Import successful')"
```

**Expected**: No errors, prints "✅ Import successful"

---

### Test 2: Server Creation

```python
from src.verifimind_mcp.server import create_server

server = create_server()
print(f"✅ Server created: {server}")
```

**Expected**: Server object created without errors

---

### Test 3: Smithery Playground (if smithery installed)

```bash
cd /home/ubuntu/VerifiMind-PEAS/mcp-server
pip install smithery>=0.4.2
python3 -m smithery.cli.playground
```

**Expected**: Playground opens in browser, shows all Resources and Tools

---

## 📝 Claude Code Prompt

**Copy-paste this to your Claude Code session**:

---

**PROMPT START**

Hi Claude Code! I need your help refactoring the VerifiMind-PEAS MCP server for Smithery deployment.

**Context**:
- Project: VerifiMind-PEAS (AI validation methodology)
- Location: `/home/ubuntu/VerifiMind-PEAS/mcp-server/`
- File to refactor: `src/verifimind_mcp/server.py`
- Goal: Make it Smithery-compatible with minimal changes (Option A - low risk)

**What's already done**:
- ✅ `smithery.yaml` created
- ✅ `pyproject.toml` updated with smithery dependencies

**What you need to do**:

1. **Add imports** (after line 29):
   ```python
   from mcp.server.fastmcp import Context, FastMCP
   from smithery.decorators import smithery
   from pydantic import BaseModel, Field
   ```

2. **Add config schema** (before `app = FastMCP(...)`):
   ```python
   class VerifiMindConfig(BaseModel):
       llm_provider: str = Field(default="mock", description="LLM provider: openai, anthropic, or mock")
       openai_api_key: str = Field(default="", description="OpenAI API key")
       anthropic_api_key: str = Field(default="", description="Anthropic API key")
       validation_mode: str = Field(default="standard", description="Validation mode: standard or strict")
   ```

3. **Wrap existing code** in `create_server()` function:
   ```python
   @smithery.server(config_schema=VerifiMindConfig)
   def create_server():
       """Create VerifiMind Genesis MCP Server."""
       app = FastMCP("verifimind-genesis")
       
       # [ALL EXISTING RESOURCES AND TOOLS GO HERE]
       
       return app
   ```

4. **Update Tool signatures** - Add `ctx: Context = None` parameter to:
   - `consult_agent_x`
   - `consult_agent_z`
   - `consult_agent_cs`
   - `run_full_trinity`

5. **Add session config logic** to `get_provider()` calls in each Tool:
   ```python
   if ctx and ctx.session_config:
       config = ctx.session_config
       if config.llm_provider == "openai" and config.openai_api_key:
           from .llm import OpenAIProvider
           provider = OpenAIProvider(api_key=config.openai_api_key)
       elif config.llm_provider == "anthropic" and config.anthropic_api_key:
           from .llm import AnthropicProvider
           provider = AnthropicProvider(api_key=config.anthropic_api_key)
       else:
           from .llm import MockProvider
           provider = MockProvider()
   else:
       provider = get_provider()
   ```

6. **Keep Resources unchanged** - They don't need session config

7. **Verify indentation** - Everything inside `create_server()` should be indented 4 spaces

**Testing**:
After refactoring, run:
```bash
python3 -c "from src.verifimind_mcp.server import create_server; print('✅ Success')"
```

**Important**:
- Keep existing functionality intact (low-risk changes only)
- Don't modify Resources
- Make sure `return app` is at the end of `create_server()`

**Reference document**: `/home/ubuntu/CLAUDE_CODE_SMITHERY_REFACTORING_GUIDE.md`

Can you help me refactor `server.py` following these instructions?

**PROMPT END**

---

## 🔍 What to Check After Claude Code Finishes

1. ✅ **Imports added** at top of file
2. ✅ **VerifiMindConfig class** defined before `create_server()`
3. ✅ **@smithery.server()** decorator on `create_server()` function
4. ✅ **All existing code** wrapped inside `create_server()`
5. ✅ **ctx: Context** parameter added to all 4 Tools
6. ✅ **Session config logic** added to `get_provider()` calls
7. ✅ **return app** at end of `create_server()`
8. ✅ **Indentation** consistent (4 spaces for everything inside function)

---

## 🚨 Common Pitfalls to Avoid

### Pitfall 1: Forgetting to return app

**Wrong**:
```python
def create_server():
    app = FastMCP("verifimind-genesis")
    # ... code ...
    # Missing return!
```

**Correct**:
```python
def create_server():
    app = FastMCP("verifimind-genesis")
    # ... code ...
    return app  # ← MUST HAVE THIS
```

---

### Pitfall 2: Inconsistent indentation

**Wrong**:
```python
def create_server():
    app = FastMCP("verifimind-genesis")
    
@app.resource(...)  # ← NOT INDENTED!
def get_master_prompt():
    ...
```

**Correct**:
```python
def create_server():
    app = FastMCP("verifimind-genesis")
    
    @app.resource(...)  # ← INDENTED 4 SPACES
    def get_master_prompt():
        ...
```

---

### Pitfall 3: Modifying Resources

**Don't do this**:
```python
@app.resource("genesis://config/master_prompt")
def get_master_prompt(ctx: Context):  # ← DON'T ADD ctx TO RESOURCES
    ...
```

**Resources don't need ctx** - only Tools do!

---

## 📊 Expected File Structure After Refactoring

```python
"""
Docstring
"""

# Imports
import json
import os
from pathlib import Path
from typing import Any, Optional

from mcp.server.fastmcp import Context, FastMCP  # ← Context added
from smithery.decorators import smithery  # ← NEW
from pydantic import BaseModel, Field  # ← NEW

# Config Schema
class VerifiMindConfig(BaseModel):  # ← NEW
    llm_provider: str = Field(...)
    openai_api_key: str = Field(...)
    anthropic_api_key: str = Field(...)
    validation_mode: str = Field(...)

# Constants (outside function - can stay global)
REPO_ROOT = Path(__file__).parent.parent.parent.parent
MASTER_PROMPT_PATH = REPO_ROOT / "reflexion-master-prompts-v1.1.md"
HISTORY_PATH = REPO_ROOT / "verifimind_history.json"

# Helper functions (outside function - can stay global)
def load_master_prompt() -> str:
    ...

def load_validation_history() -> dict[str, Any]:
    ...

def save_validation_history(history: dict[str, Any]) -> None:
    ...

def get_latest_validation() -> dict[str, Any]:
    ...

def get_project_info() -> dict[str, Any]:
    ...

# Main server creation function
@smithery.server(config_schema=VerifiMindConfig)  # ← NEW DECORATOR
def create_server():  # ← NEW FUNCTION WRAPPER
    """Create VerifiMind Genesis MCP Server."""
    
    # Initialize MCP server
    app = FastMCP("verifimind-genesis")
    
    # ===== RESOURCES ===== (UNCHANGED)
    
    @app.resource("genesis://config/master_prompt")
    def get_master_prompt() -> str:
        ...
    
    @app.resource("genesis://history/latest")
    def get_latest_validation_resource() -> str:
        ...
    
    @app.resource("genesis://history/all")
    def get_all_validations() -> str:
        ...
    
    @app.resource("genesis://state/project_info")
    def get_project_info_resource() -> str:
        ...
    
    # ===== TOOLS ===== (ADD ctx PARAMETER + SESSION CONFIG LOGIC)
    
    @app.tool()
    async def consult_agent_x(
        concept_name: str,
        concept_description: str,
        context: Optional[str] = None,
        ctx: Context = None  # ← ADDED
    ) -> dict:
        # ... session config logic added ...
        ...
    
    @app.tool()
    async def consult_agent_z(
        concept_name: str,
        x_analysis: dict,
        ctx: Context = None  # ← ADDED
    ) -> dict:
        # ... session config logic added ...
        ...
    
    @app.tool()
    async def consult_agent_cs(
        concept_name: str,
        x_analysis: dict,
        z_analysis: dict,
        ctx: Context = None  # ← ADDED
    ) -> dict:
        # ... session config logic added ...
        ...
    
    @app.tool()
    async def run_full_trinity(
        concept_name: str,
        concept_description: str,
        context: Optional[str] = None,
        ctx: Context = None  # ← ADDED
    ) -> dict:
        # ... session config logic added ...
        ...
    
    return app  # ← MUST RETURN APP
```

---

## ⏱️ Estimated Timeline

| Step | Duration | Status |
|------|----------|--------|
| Add imports | 2 min | ⏳ |
| Add config schema | 5 min | ⏳ |
| Wrap in create_server() | 10 min | ⏳ |
| Update Tool signatures | 5 min | ⏳ |
| Add session config logic | 30 min | ⏳ |
| Verify indentation | 10 min | ⏳ |
| Test locally | 15 min | ⏳ |
| **Total** | **~1.5 hours** | ⏳ |

---

## 🎯 Success Criteria

### Code Quality
- ✅ No syntax errors
- ✅ All imports resolve
- ✅ Indentation consistent
- ✅ `create_server()` returns `app`

### Functionality
- ✅ Server imports successfully
- ✅ All 4 Resources still work
- ✅ All 4 Tools still work
- ✅ Session config accessible in Tools

### Smithery Compatibility
- ✅ `@smithery.server()` decorator present
- ✅ `VerifiMindConfig` schema defined
- ✅ `[tool.smithery]` in pyproject.toml points to correct function

---

## 📞 Support

**If you encounter issues**:

1. **Syntax errors**: Check indentation (everything inside `create_server()` should be indented 4 spaces)
2. **Import errors**: Make sure `smithery>=0.4.2` is installed (`pip install smithery>=0.4.2`)
3. **Runtime errors**: Check that `return app` is at the end of `create_server()`

**After Claude Code finishes**, share the results and I'll review!

---

## 🚀 Next Steps After Refactoring

1. ✅ Test locally (run test commands)
2. ✅ Commit to GitHub
3. ✅ Deploy to Smithery (I'll guide you through this)

---

**Good luck, Alton! You've got this!** 💪

**FLYWHEEL, TEAM!** 🔥
