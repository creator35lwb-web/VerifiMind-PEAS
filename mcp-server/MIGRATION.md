# Migration Guide: Smithery → Direct MCP Connection

**Effective:** March 1, 2026 (Smithery free hosting sunset)

---

## What Changed

Smithery free hosting ended on March 1, 2026. Our GCP Cloud Run deployment at
`https://verifimind.ysenseai.org` is **unaffected** — the server is live and operational.

Smithery CLI and registry remain active for discovery. Only free hosting sunset.

---

## Before (Smithery-hosted connection)

```bash
# Old method — no longer needed
claude mcp add -s user verifimind -- npx -y @smithery/cli@latest run @creator35lwb-web/verifimind-peas --client claude
```

## After (Direct MCP connection — current)

```bash
# Current method — use this
claude mcp add -s user verifimind-gcp -- npx -y mcp-remote https://verifimind.ysenseai.org/mcp/
```

---

## One-Time Migration Steps

```bash
# Step 1: Remove any old Smithery-based connection
claude mcp remove verifimind -s user 2>/dev/null || true
claude mcp remove verifimind-gcp -s user 2>/dev/null || true

# Step 2: Add the direct connection
claude mcp add -s user verifimind-gcp -- npx -y mcp-remote https://verifimind.ysenseai.org/mcp/

# Step 3: Start a NEW Claude Code session
# (Required to reload tool schemas, including BYOK parameters)
```

---

## Claude Desktop

Add this to `claude_desktop_config.json`:

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

**Config file locations:**
- Windows: `%APPDATA%\Claude\claude_desktop_config.json`
- macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
- Linux: `~/.config/Claude/claude_desktop_config.json`

---

## What's New in v0.5.0

After migrating, you have access to all v0.5.0 features:

- **BYOK** — Pass your own LLM API keys per tool call (see `docs/BYOK_GUIDE.md`)
- **Session tracing** — `_session_id` in Trinity responses for log correlation
- **Structured errors** — `error_code` + `recovery_hint` on failures
- **Health v2** — `/health` now includes uptime, `session_id_tracing` feature flag

---

## Verify Connection

```bash
curl https://verifimind.ysenseai.org/health | jq '{version, status, byok_live: .features.byok_live}'
# Expected: {"version": "0.5.0", "status": "healthy", "byok_live": true}
```
