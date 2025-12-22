# 🚀 Quick Start for Claude Code

## Mission

**Fix http_server.py so VerifiMind MCP server works on Smithery**

---

## Problem

**Server deploys but Smithery can't connect to it**

Error: "NO .well-known/mcp-config found"

---

## What to Do

### 1. Read the Full Handoff

**File**: `/home/ubuntu/CLAUDE_CODE_HANDOFF.md`

**Contains**:
- Everything we've tried
- What works and what doesn't
- Exact errors
- What needs to be fixed
- How to test
- Success criteria

### 2. Research

**Find out how to**:
- Integrate FastMCP with Smithery properly
- Add custom FastAPI routes to Smithery app
- Create `.well-known/mcp-config` endpoint

**Search for**:
- Smithery documentation
- FastMCP HTTP examples
- Other MCP servers on Smithery
- GitHub issues

### 3. Fix http_server.py

**Location**: `/home/ubuntu/VerifiMind-PEAS/mcp-server/http_server.py`

**Must have**:
- `/mcp` endpoint (MCP with SSE)
- `/.well-known/mcp-config` endpoint
- `/health` endpoint
- `/` root endpoint

### 4. Test Locally

```bash
cd /home/ubuntu/VerifiMind-PEAS/mcp-server
docker build -t verifimind-test .
docker run -p 8081:8081 verifimind-test

# Test endpoints
curl http://localhost:8081/
curl http://localhost:8081/health
curl http://localhost:8081/.well-known/mcp-config
```

### 5. Deploy

```bash
cd /home/ubuntu/VerifiMind-PEAS
git add mcp-server/http_server.py
git commit -m "fix: Working HTTP server with Smithery integration"
git push origin main
```

Then redeploy on Smithery: https://smithery.ai/server/creator35lwb-web/verifimind-peas/deployments

---

## Key Files

**To fix**: `/home/ubuntu/VerifiMind-PEAS/mcp-server/http_server.py`

**Working**: 
- `Dockerfile` ✅
- `pyproject.toml` ✅
- `src/verifimind_mcp/server.py` ✅

**Don't change**: Dockerfile, pyproject.toml, server.py

---

## Success Looks Like

**Local test**:
```bash
$ curl http://localhost:8081/.well-known/mcp-config
{"mcpServers": {...}}  ← Returns JSON!
```

**Smithery deployment**:
```
✅ Config found at /.well-known/mcp-config
✅ 4 tools discovered
✅ Server available!
```

---

## Repository

**URL**: https://github.com/creator35lwb-web/VerifiMind-PEAS

**Branch**: main

**Directory**: mcp-server/

---

## Need Help?

**Read**: CLAUDE_CODE_HANDOFF.md (full details)

**Ask**: Alton or Manus

---

## Let's Go Team! 💪🚀
