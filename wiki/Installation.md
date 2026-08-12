# Installation and Connection Playbook

This page covers the durable connection workflow. Client configuration formats
and the server's runtime contract can change, so verify both ends before
debugging an old example.

## Canonical runtime sources

Check these first:

| Source | What it owns |
|---|---|
| [`/health`](https://verifimind.ysenseai.org/health) | live runtime version, MCP protocol version, routing, model-catalog freshness, failover state, and tool availability |
| [`/setup`](https://verifimind.ysenseai.org/setup) | current connection guidance and supported hosted/BYOK configuration |
| [Server card](https://verifimind.ysenseai.org/.well-known/mcp/server-card.json) | machine-readable discovery and tool descriptions |
| [Current Production Status](Current-Production-Status) | release SHA, deployment evidence, and reviewed operating notes |
| [`server.json`](https://github.com/creator35lwb-web/VerifiMind-PEAS/blob/main/server.json) | MCP Registry package metadata |

If this page disagrees with a live source, the live source wins.

## Prerequisites

- An MCP-compatible client.
- HTTPS access to `verifimind.ysenseai.org`.
- A current Node.js LTS runtime only when using the `mcp-remote` stdio bridge.

Registration and BYOK are optional. The active hosted tools can be used without
submitting a provider key or UUID.

## Endpoint and transport

- Hosted endpoint: `https://verifimind.ysenseai.org/mcp/`
- Transport: `streamable-http`
- Use the trailing slash in client configuration to avoid redirect handling
  differences between MCP clients.

Do not configure the legacy Smithery endpoint or `http-sse` transport.

## Connect a client

### Claude Code

```bash
claude mcp add -s user verifimind -- npx -y mcp-remote https://verifimind.ysenseai.org/mcp/
```

Restart or reload the client, then inspect its MCP server list.

### Claude Desktop

Add this entry to the client's MCP configuration:

```json
{
  "mcpServers": {
    "verifimind": {
      "command": "npx",
      "args": [
        "-y",
        "mcp-remote",
        "https://verifimind.ysenseai.org/mcp/"
      ]
    }
  }
}
```

The configuration-file location is owned by the Claude Desktop release you are
using. Confirm it in the current client documentation, then restart the app.

### Cursor or VS Code

For clients with native streamable-HTTP support:

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

Some clients use `mcpServers` instead of `servers`. Follow the schema for the
installed client version.

### Other native MCP clients

Configure a streamable-HTTP server using the same endpoint. Managed clients
normally set MCP headers and session behavior themselves. Custom clients should
follow the protocol version reported by [`/health`](https://verifimind.ysenseai.org/health),
not a protocol version copied from an old guide.

## Verify the connection

### 1. Verify live health

```bash
curl https://verifimind.ysenseai.org/health
```

Confirm:

- `status` is healthy;
- `inference_mode` is live;
- `version` matches [Current Production Status](Current-Production-Status);
- `tool_availability` reports 13 defined, 8 active, and 5 temporarily
  unavailable;
- routing, model-catalog status, and runtime-failover state are present.

Do not treat a healthy endpoint as proof that every defined tool is callable.

### 2. Inspect discovered tools

The client should discover 13 schemas:

- **4 active Trinity tools:** `consult_agent_x`, `consult_agent_z`,
  `consult_agent_cs`, and `run_full_trinity`.
- **4 active built-in template reads:** `list_prompt_templates`,
  `get_prompt_template`, `export_prompt_template`, and
  `get_template_statistics`.
- **5 maintenance-denial schemas:** `register_custom_template`,
  `import_template_from_url`, `coordination_handoff_create`,
  `coordination_handoff_read`, and `coordination_team_status`.

The five maintenance tools remain visible so clients do not silently lose
schema compatibility. Calling one should produce its explicit temporary-
unavailability response; it should not mutate or disclose data.

### 3. Run a bounded test

Start with one active tool:

> Use `consult_agent_x` to identify three assumptions in this concept. Keep the
> answer short and label uncertainty.

Then test the complete flow:

> Use `run_full_trinity` to review this concept. Do not save it to history.
> Report any degraded or unavailable stage before summarizing the findings.

## Privacy-conscious setup

- `save_to_history` defaults to `false`; leave it false for confidential or
  sensitive concepts.
- A UUID is optional and is separate from aggregate-history opt-in.
- BYOK credentials are request-scoped, but the selected provider receives the
  material needed for that inference. Review that provider's terms and account
  settings.
- Do not paste credentials into a prompt, tracked file, issue, or discussion.
- Read the live [Privacy Policy](https://verifimind.ysenseai.org/privacy) and
  [Terms](https://verifimind.ysenseai.org/terms).

## Troubleshooting

| Symptom | Check |
|---|---|
| Redirect or silent connection failure | Configure the full `/mcp/` URL with trailing slash |
| Client tries SSE-only transport | Select `streamable-http` or use the `mcp-remote` bridge |
| Tools do not appear | Remove/re-add the server and clear the client's cached tool schema |
| Five tools return maintenance errors | Expected current containment; use the eight active tools |
| Coordination call returns a temporary-disabled error | Keep coordination state in your own private repository; no public shared namespace is available |
| Custom-template mutation is denied | Use built-in template reads or manage custom templates locally |
| Provider/model claim differs from this Wiki | Trust `/health`, `/setup`, and the server card |
| `403` or timeout | Check network/proxy policy, then consult the repository troubleshooting guide |

For deeper transport diagnostics, use the
[MCP Server Troubleshooting Guide](https://github.com/creator35lwb-web/VerifiMind-PEAS/blob/main/docs/MCP_Server_Troubleshooting_Guide.md).

## MCP Registry

VerifiMind PEAS is listed in the
[official MCP Registry](https://registry.modelcontextprotocol.io/?q=verifimind).
The package version changes independently from the runtime version. Read it
from the current [`server.json`](https://github.com/creator35lwb-web/VerifiMind-PEAS/blob/main/server.json)
instead of copying a number into setup instructions.

---

[← Home](Home) · [Tool reference](MCP-Tools-Reference) · [BYOK](BYOK-Guide)
