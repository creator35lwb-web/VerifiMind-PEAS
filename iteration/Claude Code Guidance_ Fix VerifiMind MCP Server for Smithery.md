# Claude Code Guidance: Fix VerifiMind MCP Server for Smithery

## Current Situation

**Status**: Deployment succeeded, but server connection failed

**Error**: `{"error":"Failed to connect to upstream server"}`

**Server URL**: https://smithery.ai/server/creator35lwb-web/verifimind-mcp-server (404)

---

## What Works

✅ **Build**: Docker image builds successfully
✅ **Deployment**: Container deploys to Smithery
✅ **Code Structure**: Files are correctly organized
✅ **Dependencies**: All packages installed correctly

---

## What's Broken

❌ **Server Connection**: Smithery can't connect to the HTTP server
❌ **Health Check**: Server fails Smithery's health check
❌ **Public URL**: Server not accessible (404 error)

---

## Root Cause (Suspected)

### Issue: FastMCP http_app() Method

**File**: `/mcp-server/http_server.py`

**Current Code**:
```python
from verifimind_mcp.server import create_server

mcp_server = create_server()
app = mcp_server.http_app()  # ← THIS MIGHT BE WRONG!
```

**Problem**: `FastMCP` might not have an `http_app()` method, or it works differently for Smithery.

**Evidence**:
- Server builds successfully (no import errors)
- Server deploys successfully (container starts)
- Server connection fails (can't reach HTTP endpoint)
- This suggests the HTTP app isn't being created correctly

---

## Solution Approach

### Option 1: Use Smithery's create_smithery_server

**Smithery provides its own HTTP wrapper** for MCP servers.

**Change http_server.py to**:
```python
"""
HTTP Server Entry Point for VerifiMind MCP Server
Designed for Smithery deployment with HTTP transport
"""
import os
from fastapi import FastAPI
from smithery.server import create_smithery_server
from verifimind_mcp.server import create_server

# Create FastAPI app
app = FastAPI()

# Create MCP server
mcp_server = create_server()

# Add Smithery SSE endpoint at /mcp
create_smithery_server(app, mcp_server)

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", "8081"))
    uvicorn.run(app, host="0.0.0.0", port=port)
```

**Why this should work**:
- `create_smithery_server` is designed for Smithery deployment
- It handles SSE (Server-Sent Events) correctly
- It creates the `/mcp` endpoint automatically
- It's the official Smithery approach

### Option 2: Use FastMCP's Built-in HTTP Support

**If FastMCP has built-in HTTP support**, use it directly:

```python
from verifimind_mcp.server import create_server

# Create MCP server
mcp_server = create_server()

# Get ASGI app (might be different method name)
app = mcp_server.get_asgi_app()  # or .asgi_app() or .app
```

**Check FastMCP documentation** for the correct method name.

### Option 3: Manual SSE Implementation

**If neither works**, implement SSE manually:

```python
from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse
from verifimind_mcp.server import create_server
import json

app = FastAPI()
mcp_server = create_server()

@app.post("/mcp")
async def mcp_endpoint(request: Request):
    """MCP endpoint with SSE support"""
    async def event_stream():
        # Read request body
        body = await request.json()
        
        # Process MCP request
        response = await mcp_server.handle_request(body)
        
        # Send SSE response
        yield f"data: {json.dumps(response)}\n\n"
    
    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )
```

---

## Files to Fix

### Priority 1: http_server.py

**Location**: `/mcp-server/http_server.py`

**Current Issue**: Using `mcp_server.http_app()` which might not exist

**Fix**: Use `create_smithery_server` from `smithery.server`

**Test**: Build Docker image locally and run to verify

### Priority 2: Dependencies

**Location**: `/mcp-server/pyproject.toml`

**Check**: Ensure `smithery>=0.4.2` is installed

**Current**:
```toml
dependencies = [
    "smithery>=0.4.2",  # ← Should be present
    ...
]
```

**If missing**, add it and rebuild.

---

## Testing Locally

### Step 1: Build Docker Image

```bash
cd /home/ubuntu/VerifiMind-PEAS/mcp-server
docker build -t verifimind-mcp:test .
```

**Expected**: Build succeeds (we know this works)

### Step 2: Run Container

```bash
docker run -p 8081:8081 verifimind-mcp:test
```

**Expected**: Server starts without errors

**Watch for**:
- Python import errors
- Module not found errors
- AttributeError (if http_app() doesn't exist)

### Step 3: Test HTTP Endpoint

```bash
curl http://localhost:8081/mcp
```

**Expected**: Some response (even an error is OK, as long as it responds)

**If no response**: Server isn't listening correctly

### Step 4: Check Logs

**Look for**:
- "Server ready for connections..."
- Uvicorn startup messages
- Any Python tracebacks
- Port binding messages

---

## Smithery Requirements

### HTTP Server Must

1. **Bind to 0.0.0.0:8081**
   - Use PORT environment variable
   - Listen on all interfaces

2. **Expose /mcp endpoint**
   - POST requests accepted
   - SSE (Server-Sent Events) supported
   - MCP protocol implemented

3. **Respond to health checks**
   - Return 200 OK on connection
   - List available tools
   - Validate MCP messages

4. **Use correct transport**
   - HTTP with SSE (not stdio)
   - Streamable responses
   - Keep-alive connections

---

## Quick Fix Steps

### For Claude Code to Execute

1. **Read current http_server.py**
   ```bash
   cat /mcp-server/http_server.py
   ```

2. **Replace with Smithery-compatible version**
   ```python
   # Use Option 1 code above
   ```

3. **Test locally**
   ```bash
   docker build -t test .
   docker run -p 8081:8081 test
   ```

4. **If successful, commit and push**
   ```bash
   git add http_server.py
   git commit -m "fix: Use smithery.server for HTTP endpoint"
   git push origin main
   ```

5. **Redeploy on Smithery**
   - Go to https://smithery.ai/new/github
   - Select VerifiMind-PEAS
   - Deploy again

---

## Expected Outcome

### After Fix

**Build logs should show**:
```
[✓] Building Docker image...
[✓] Image built successfully
[✓] Deploying image...
[✓] Server started
[✓] Health check passed
[✓] Server available at https://smithery.ai/server/creator35lwb-web/verifimind-mcp-server
```

**Server page should show**:
- Server name: verifimind-mcp-server
- Status: Active
- Tools: 4 tools listed
- Resources: 4 resources listed
- Install button available

**Testing should work**:
- Add to Claude Desktop
- Connect successfully
- List tools
- Execute validations

---

## Debugging Tips

### If Build Fails

**Check**:
- Dockerfile syntax
- Python imports
- Dependencies in pyproject.toml

**Fix**: Review build logs, fix errors, retry

### If Server Starts But Crashes

**Check**:
- Container logs (docker logs)
- Python tracebacks
- Import errors

**Fix**: Fix code errors, rebuild, retry

### If Server Runs But Can't Connect

**Check**:
- Port binding (should be 0.0.0.0:8081)
- Endpoint path (should be /mcp)
- SSE headers
- MCP protocol implementation

**Fix**: Review http_server.py, fix endpoint, retry

### If Health Check Fails

**Check**:
- /mcp endpoint responds
- MCP protocol correct
- Tools list returned
- No authentication required

**Fix**: Implement health check endpoint, retry

---

## Reference: Working Example

**Smithery Example Server Structure**:

```python
# http_server.py
from fastapi import FastAPI
from smithery.server import create_smithery_server
from your_package.server import create_server

app = FastAPI()
mcp_server = create_server()
create_smithery_server(app, mcp_server)
```

**This is the pattern Smithery expects!**

---

## Summary for Claude Code

**Task**: Fix http_server.py to work with Smithery

**Problem**: Current implementation uses `mcp_server.http_app()` which doesn't work

**Solution**: Use `create_smithery_server` from `smithery.server`

**Steps**:
1. Read current http_server.py
2. Replace with Smithery-compatible version (Option 1 above)
3. Test locally with Docker
4. Commit and push to GitHub
5. Redeploy on Smithery
6. Verify server is accessible

**Expected Result**: Server connects successfully, tools are listed, server is public

---

## Files Reference

**Repository**: https://github.com/creator35lwb-web/VerifiMind-PEAS

**Branch**: main

**Directory**: mcp-server/

**Key Files**:
- `http_server.py` ← **FIX THIS FILE**
- `Dockerfile` ← Already correct
- `pyproject.toml` ← Already correct
- `smithery.yaml` ← Already correct
- `src/verifimind_mcp/server.py` ← Already correct

**Only http_server.py needs to be fixed!**

---

## Contact

**If you need help**:
- Share the error logs
- Share the Docker build output
- Share the server startup logs
- I'll help diagnose further

**Good luck!** 🚀
