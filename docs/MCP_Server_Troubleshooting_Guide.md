# VerifiMind MCP Server — Troubleshooting & Multi-Client Setup Guide

> **Server**: `https://verifimind.ysenseai.org`
> **MCP Endpoint**: `https://verifimind.ysenseai.org/mcp/`
> **Transport**: `streamable-http` (MCP 2025-03-26 spec)
> **Version**: v0.5.34
> **Last Updated**: May 17, 2026 — Phase 90 "Adoption First"
> **Tools**: 13 free forever (4 Trinity validation + 6 template library + 3 coordination) — see [Core Tools Always Free pledge](https://github.com/creator35lwb-web/VerifiMind-PEAS#core-tools-always-free-pledge)

---

## Table of Contents

1. [Quick Connectivity Test](#quick-connectivity-test)
2. [Multi-Client Configuration](#multi-client-configuration)
   - [Claude Code (CLI)](#claude-code-cli)
   - [Claude Desktop](#claude-desktop)
   - [ChatGPT Codex CLI](#chatgpt-codex-cli)
   - [Cursor / VS Code Copilot](#cursor--vs-code-copilot)
   - [Custom MCP Clients (Direct HTTP)](#custom-mcp-clients-direct-http)
   - [OpenAI Agents SDK (Python)](#openai-agents-sdk-python)
3. [Common Errors & Solutions](#common-errors--solutions)
   - [202 Accepted (NOT an error)](#-202-accepted-not-an-error)
   - [307 Redirect on `/`](#-307-redirect-on-)
   - [308 Permanent Redirect (most common SDK-client failure)](#-308-permanent-redirect-most-common-sdk-client-failure)
   - [400 Bad Request / Parse Error](#-400-bad-request--parse-error)
   - [403 Forbidden / Tunnel Error / Blocklist](#-403-forbidden--tunnel-error--blocklist)
   - [404 Not Found](#-404-not-found)
   - [405 Method Not Allowed](#-405-method-not-allowed)
   - [406 Not Acceptable (missing Accept header)](#-406-not-acceptable-missing-accept-header)
   - [429 Too Many Requests](#-429-too-many-requests)
   - [401 Unauthorized (Smithery)](#-401-unauthorized-smithery)
   - [Tools List Empty (Codex CLI)](#-tools-list-empty-codex-cli)
4. [Transport Types Explained](#transport-types-explained)
5. [Known Client-Specific Issues](#known-client-specific-issues)
6. [Server Endpoints Reference](#server-endpoints-reference)
7. [Still Having Issues?](#still-having-issues)

---

## Quick Connectivity Test

Before configuring any client, verify the server is reachable from your network:

```bash
# Test 1: Health check (should return JSON with "status": "healthy")
curl https://verifimind.ysenseai.org/health

# Test 2: MCP endpoint (MUST include trailing slash)
curl -X POST https://verifimind.ysenseai.org/mcp/ \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-03-26","capabilities":{},"clientInfo":{"name":"test","version":"1.0"}}}'
```

**Expected**: HTTP 200 with `text/event-stream` response containing `serverInfo`.

> **If you get 403 / tunnel error**: This is typically a corporate network, proxy, or firewall restriction — **not** a JSON configuration error. See [403 Forbidden](#-403-forbidden--tunnel-error) section below.

---

## Multi-Client Configuration

### Claude Code (CLI)

The recommended method for Claude Code users:

```bash
# User-scoped (available in all projects)
claude mcp add -s user verifimind -- npx -y mcp-remote https://verifimind.ysenseai.org/mcp/

# Project-scoped (current project only)
claude mcp add -s project verifimind -- npx -y mcp-remote https://verifimind.ysenseai.org/mcp/

# Verify
claude mcp list
```

After adding, restart Claude Code and type `/mcp` to see available tools.

---

### Claude Desktop

Edit your config file:

| OS | Config Path |
|----|-------------|
| macOS | `~/Library/Application Support/Claude/claude_desktop_config.json` |
| Windows | `%APPDATA%\Claude\claude_desktop_config.json` |
| Linux | `~/.config/Claude/claude_desktop_config.json` |

```json
{
  "mcpServers": {
    "verifimind": {
      "command": "npx",
      "args": ["-y", "mcp-remote", "https://verifimind.ysenseai.org/mcp/"]
    }
  }
}
```

Restart Claude Desktop after saving.

---

### ChatGPT Codex CLI

> **⚠️ Known Issue**: Codex CLI v0.98.0 has a [confirmed bug](https://github.com/openai/codex/issues/11284) where some Streamable HTTP MCP servers fail to initialize (tools list appears empty). This is a Codex CLI issue, not a VerifiMind server issue.

**Option A: Direct connection (may fail due to Codex bug)**

Edit `~/.codex/config.toml`:

```toml
[mcp_servers.verifimind]
url = "https://verifimind.ysenseai.org/mcp/"
transport = "streamable_http"
```

**Option B: Workaround using supergateway bridge (recommended)**

If Option A shows empty tools, use `supergateway` to bridge streamable-http → stdio:

```bash
# Install supergateway
npm install -g supergateway

# Run the bridge (keep this terminal open)
supergateway --sse "https://verifimind.ysenseai.org/mcp/"
```

Then configure Codex to use the local stdio bridge:

```toml
[mcp_servers.verifimind]
command = "supergateway"
args = ["--sse", "https://verifimind.ysenseai.org/mcp/"]
```

**Option C: Using OpenAI Agents SDK (Python)**

See the [OpenAI Agents SDK](#openai-agents-sdk-python) section below.

> **Important**: Do NOT use `"transport": "http-sse"` — our server uses `streamable-http`, not legacy SSE. These are different protocols.

---

### Cursor / VS Code Copilot

Create or edit `.cursor/mcp.json` (Cursor) or `.vscode/mcp.json` (VS Code) in your project root:

```json
{
  "servers": {
    "verifimind": {
      "url": "https://verifimind.ysenseai.org/mcp/",
      "transport": "streamable-http"
    }
  }
}
```

For Cursor, you can also use the global settings: **Settings → MCP → Add Server**.

---

### Custom MCP Clients (Direct HTTP)

For any MCP client that supports direct HTTP configuration:

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

**Critical requirements:**
- URL **MUST** include trailing slash: `/mcp/` (not `/mcp`)
- Transport **MUST** be `streamable-http` (not `http-sse`, not `sse`)
- POST requests must include headers:
  - `Content-Type: application/json`
  - `Accept: application/json, text/event-stream`

---

### OpenAI Agents SDK (Python)

For developers building agents with the OpenAI Agents SDK:

```python
import asyncio
from agents import Agent, Runner
from agents.mcp import MCPServerStreamableHttp

async def main():
    async with MCPServerStreamableHttp(
        name="VerifiMind Genesis",
        params={
            "url": "https://verifimind.ysenseai.org/mcp/",
        },
        cache_tools_list=True,
    ) as server:
        agent = Agent(
            name="Validator",
            instructions="Use VerifiMind tools to validate concepts.",
            mcp_servers=[server],
        )
        result = await Runner.run(
            agent, 
            "Use run_full_trinity to validate the concept 'AI-powered code review'"
        )
        print(result.final_output)

asyncio.run(main())
```

**Requirements**: `pip install openai-agents`

---

## Common Errors & Solutions

### ✅ 202 Accepted (NOT an error)

**Symptoms:**
```
HTTP 202 Accepted
```

**Root Cause**: This is the **normal streamable-http MCP acceptance response**, not an error. The server has accepted your JSON-RPC request and will stream the actual response via SSE (Server-Sent Events) on the same connection.

**What to expect:**
- Your client should continue listening on the SSE stream after the 202
- The actual response (`tools/list`, `tools/call` result, etc.) arrives as `text/event-stream` data frames
- Compliant MCP clients (Claude / Cursor / VS Code / Windsurf / Agents SDK) handle this automatically

**Solution**: No action needed. If your client reports 202 as a failure, it's not implementing streamable-http correctly — check that you set `"transport": "streamable-http"` (NOT `"sse"` or `"http-sse"`).

---

### 🔄 307 Redirect on `/`

**Symptoms:**
```
HTTP/2 307
location: https://verifimind.ysenseai.org/...
```

**Root Cause**: Hitting the root URL `/` (not `/mcp/`) triggers a 307 to redirect to the appropriate landing surface. Some clients pointed at the bare domain (no path) will see this.

**Solution**: Configure your MCP client with the full path including trailing slash:
```
✅ https://verifimind.ysenseai.org/mcp/
❌ https://verifimind.ysenseai.org/
❌ https://verifimind.ysenseai.org
```

---

### 🔁 308 Permanent Redirect (most common SDK-client failure)

**Symptoms:**
```
HTTP/2 308 Permanent Redirect
location: https://verifimind.ysenseai.org/mcp/
```

Or in `python-httpx`, `node`, `requests`, `axios`:
```
RemoteProtocolError: Server disconnected without sending a response
ConnectionError after POST to /mcp
Empty body / no JSON response
```

**Root Cause**: This is the **#1 SDK-client failure mode**. POST request hit `/mcp` (no trailing slash). The server replies with `308 Permanent Redirect` to `/mcp/`. Per RFC 7538, programmatic HTTP clients **must NOT change the POST method** when following a 308 — but many SDKs either don't follow 308s on POST, or drop the body on redirect, causing silent failures.

**Affected clients (observed in production logs):**
- `python-httpx` (any version)
- `node-fetch`, `axios` (depends on configuration)
- Raw `requests` library (Python) with `allow_redirects=False`
- Custom MCP clients that don't follow POST redirects

**Solution**: Always configure your MCP client with the trailing slash:
```
✅ https://verifimind.ysenseai.org/mcp/
❌ https://verifimind.ysenseai.org/mcp
```

This is the **same fix as 307** but with permanent redirect semantics. The fastest test:
```bash
# This succeeds with 200
curl -X POST https://verifimind.ysenseai.org/mcp/ \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-03-26","capabilities":{},"clientInfo":{"name":"test","version":"1.0"}}}'

# This returns 308 (and many SDKs fail here silently)
curl -X POST https://verifimind.ysenseai.org/mcp \  # ← missing slash
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize"}'
```

> **Production data, May 17, 2026:** 14× 308 redirect hits in 24h, all from `python-httpx` or `node`. If you're building a custom MCP client, this is the bug your users will hit first.

---

### 🚫 403 Forbidden / Tunnel Error / Blocklist

**Symptoms:**
```
403 / tunnel error
curl: (403) Forbidden
```

**Root Cause**: This has **two distinct causes** — diagnose which:

**Cause A — Network-level issue (most common for new users):**
- Corporate proxy or firewall blocking outbound HTTPS to GCP
- VPN interfering with SSL/TLS handshake
- ISP-level content filtering
- China mainland network restrictions (GCP endpoints may be blocked)

**Cause B — Sentinel blocklist (production security layer):**
- Your IP has been added to the application-layer blocklist by Sentinel (the security operations sub-agent) because it matched a known scanner / probe / credential-enumeration pattern
- 7 IPs currently blocked (security scanners, MCP probers, secret enumeration scripts)
- See [`mcp-server/src/verifimind_mcp/middleware/ip_blocklist.py`](https://github.com/creator35lwb-web/VerifiMind-PEAS/blob/main/mcp-server/src/verifimind_mcp/middleware/ip_blocklist.py) for the active list

**Solutions for Cause A:**
1. Try from a different network (mobile hotspot, home WiFi)
2. Disable VPN temporarily and retry
3. Check if your proxy requires authentication
4. Use `curl -v https://verifimind.ysenseai.org/health` to see where the connection fails
5. If behind corporate proxy, ask IT to whitelist `*.ysenseai.org` and `*.run.app`

**Solutions for Cause B:**
- If you believe you've been blocked in error, file a [GitHub Issue](https://github.com/creator35lwb-web/VerifiMind-PEAS/issues) with your IP and request review
- Note: legitimate MCP traffic from named user-agents (Claude / Cursor / Codex / Agents SDK / claude-user / mcp-remote) is never blocked

---

### 🔧 Tools List Empty (Codex CLI)

**Symptoms:**
- MCP server appears in Codex but shows 0 tools
- Initialization or handshake fails silently
- Works in Claude/Cursor but not in Codex

**Root Cause**: Known Codex CLI bug ([#11284](https://github.com/openai/codex/issues/11284)) affecting Streamable HTTP MCP servers.

**Solution**: Use the `supergateway` bridge workaround described in the [Codex CLI section](#chatgpt-codex-cli) above.

---

### ❌ 404 Not Found

**Symptoms:**
```
HTTP 404 Not Found
```

**Common causes:**
- Typo in URL
- Using `/sse` or `/mcp/sse` endpoint (does not exist — we use streamable-http, not legacy SSE)
- Accessing non-existent resource paths

**Solution**: Use the correct endpoint: `https://verifimind.ysenseai.org/mcp/`

---

### 🚫 405 Method Not Allowed

**Symptoms:**
```
HTTP 405 Method Not Allowed
```

**Root Cause**: Using wrong HTTP method for the endpoint.

**Solution**:
- **MCP endpoint** (`/mcp/`): Use **POST** for protocol messages, **GET** for SSE stream with session ID
- **Health** (`/health`): Use **GET**
- **Config** (`/.well-known/mcp-config`): Use **GET**

---

### ⚠️ 400 Bad Request / Parse Error

**Symptoms:**
```
400 Bad Request
Parse error
```

**Common causes:**
- Following a 307 redirect with `curl -L` (POST body is lost on redirect)
- Invalid JSON in request body
- Missing `Content-Type: application/json` header

**Solution**:
1. Use the URL with trailing slash to avoid redirects
2. Validate your JSON syntax
3. Include required headers

---

### 🚫 406 Not Acceptable (missing Accept header)

**Symptoms:**
```
HTTP 406 Not Acceptable
```

**Root Cause**: streamable-http requires the client to advertise that it accepts BOTH JSON and event-stream responses. Missing or restrictive `Accept` header triggers 406.

**Solution**: Always send the full dual Accept header on POST requests:
```
Accept: application/json, text/event-stream
```

```bash
# ❌ Causes 406
curl -X POST https://verifimind.ysenseai.org/mcp/ \
  -H "Content-Type: application/json" \
  -H "Accept: application/json" \           # missing event-stream
  -d '{"jsonrpc":"2.0",...}'

# ✅ Correct
curl -X POST https://verifimind.ysenseai.org/mcp/ \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0",...}'
```

Most managed MCP clients (Claude / Cursor / VS Code / Agents SDK) handle this automatically. Custom clients must set both.

---

### ⏱️ 429 Too Many Requests

**Symptoms:**
```
HTTP 429 Too Many Requests
Rate limit exceeded
```

**Root Cause**: Server rate limiting (10 requests per 60 seconds per IP).

**Solution**: Wait 60 seconds and retry. For higher limits, contact the maintainer.

---

### 🔑 401 Unauthorized (Smithery)

**Symptoms:**
```
401 Missing Authorization header
```

**Root Cause**: You're connecting through the Smithery proxy URL (`server.smithery.ai/...`) which requires Smithery authentication.

**Solution**: Use the direct GCP URL instead:
```
✅ https://verifimind.ysenseai.org/mcp/
❌ https://server.smithery.ai/creator35lwb-web/verifimind-genesis/mcp
```

The direct URL is free and requires no authentication.

---

## Transport Types Explained

Understanding transport types is critical for correct configuration:

| Transport | Protocol | Our Server | When to Use |
|-----------|----------|------------|-------------|
| `streamable-http` | MCP 2025-03-26 | ✅ **Supported** | Default for all clients |
| `http-sse` / `sse` | Legacy SSE | ❌ Not supported | Do NOT use |
| `stdio` | Local subprocess | Via `mcp-remote` bridge | Claude Desktop, Codex workaround |

**Our server uses `streamable-http`** — the current MCP specification. This is different from legacy SSE (`http-sse`). If your client config has `"transport": "http-sse"` or `"transport": "sse"`, change it to `"transport": "streamable-http"`.

---

## Known Client-Specific Issues

| Client | Version | Issue | Status | Workaround |
|--------|---------|-------|--------|------------|
| Codex CLI | v0.98.0 | Empty tools list with streamable-http | [Open Bug #11284](https://github.com/openai/codex/issues/11284) | Use `supergateway` bridge |
| ChatGPT Apps | Beta | MCP only for Business/Enterprise/Edu | Platform limitation | Use Codex CLI or Agents SDK |
| Claude Desktop | All | Requires `mcp-remote` for HTTP servers | By design | Use `npx -y mcp-remote` |
| Cursor | Latest | Works natively | ✅ No issues | — |
| VS Code Copilot | Latest | Works natively | ✅ No issues | — |

---

## Server Endpoints Reference

| Endpoint | Method | Purpose |
|---|---|---|
| `/` | GET | Server info and capabilities |
| `/health` | GET | Health check (status, version, rate limits, feature flags) |
| `/mcp/` | POST | MCP protocol endpoint (streamable-http) |
| `/mcp/` | GET | SSE stream (requires `mcp-session-id` header) |
| `/mcp/` | DELETE | Session termination |
| `/mcp/test?key=<uuid>` | GET | Verify UUID + connection health |
| `/.well-known/mcp-config` | GET | Auto-discovery config for MCP clients |
| `/setup` | GET | Interactive setup guide (JSON) |
| `/changelog` | GET | Full version history |
| `/research` | GET | Published research index |
| `/research/paradox` | GET | The Validation Paradox publication |
| `/research/evaluation-roadmap` | GET | Pre-registered Evaluation Roadmap v1.0 |
| `/research/cowork` | GET | Cowork on 3P analysis |
| `/library` | GET | Genesis Research Library (20+ papers) |
| `/register` · `/optout` | GET / POST | Early Adopter UUID registration / opt-out |
| `/privacy` · `/terms` | GET | Policy pages |

---

## Still Having Issues?

1. **Check server status**: `curl https://verifimind.ysenseai.org/health`
2. **Get full config**: `curl https://verifimind.ysenseai.org/.well-known/mcp-config`
3. **Interactive setup**: `curl https://verifimind.ysenseai.org/setup`
4. **GitHub Issues**: [VerifiMind-PEAS Issues](https://github.com/creator35lwb-web/VerifiMind-PEAS/issues)
5. **GCP Monitoring**: See [GCP Monitoring Setup Guide](./GCP_Monitoring_Setup_Guide.md)

---

*This guide covers VerifiMind MCP Server v0.5.34 (Phase 90 "Adoption First"). For the latest version, check the [GitHub repository](https://github.com/creator35lwb-web/VerifiMind-PEAS) or [/changelog](https://verifimind.ysenseai.org/changelog).*

**Related docs:**
- [MCP_SERVER_FEATURES.md](https://github.com/creator35lwb-web/VerifiMind-PEAS/blob/main/MCP_SERVER_FEATURES.md) — Full features guide (13 tools, configuration examples)
- [Wiki Installation](https://github.com/creator35lwb-web/VerifiMind-PEAS/wiki/Installation) — Step-by-step setup
- [Evaluation Roadmap](https://verifimind.ysenseai.org/research/evaluation-roadmap) — What we plan to measure (pre-registered milestones)
- [Validation Paradox](https://verifimind.ysenseai.org/research/paradox) — What we are NOT (honest scope statement)
