"""
HTTP Server Entry Point for VerifiMind MCP Server
Designed for GCP Cloud Run deployment with HTTP transport
Properly handles FastMCP lifespan context for session management

v0.4.1 Features:
- Markdown-first report generation (Accept: text/markdown)
- Unified Prompt Templates (6 new MCP tools)
- Input sanitization for prompt injection protection
- CORS middleware for browser-based MCP clients
- Rate limiting for EDoS protection (Economic Denial of Sustainability)
- Health check endpoint with rate limit stats
- MCP configuration endpoint
- Streamable HTTP transport for MCP protocol
- Smart Fallback per-agent provider system
"""
import os
from fastapi.responses import JSONResponse
from starlette.applications import Starlette
from starlette.responses import HTMLResponse, PlainTextResponse, RedirectResponse, Response
from starlette.routing import Mount, Route
from starlette.middleware.cors import CORSMiddleware
from verifimind_mcp.server import create_http_server
from verifimind_mcp.middleware import RateLimitMiddleware, get_rate_limit_stats

# Create MCP server instance
mcp_server = create_http_server()

# Get ASGI app from FastMCP - use path='/' so the route is at root of mounted app
# When mounted at /mcp, requests to /mcp will go to / in the app
mcp_app = mcp_server.http_app(path='/', transport='streamable-http')

# Server version
SERVER_VERSION = "0.4.4"

# Custom route handlers
async def health_handler(request):
    """Health check endpoint with rate limit stats"""
    rate_stats = get_rate_limit_stats()

    return JSONResponse({
        "status": "healthy",
        "server": "verifimind-genesis",
        "version": SERVER_VERSION,
        "transport": "streamable-http",
        "endpoints": {
            "mcp": "/mcp",
            "config": "/.well-known/mcp-config",
            "health": "/health",
            "setup": "/setup"
        },
        "resources": 4,
        "tools": 10,
        "features": {
            "smart_fallback": True,
            "per_agent_providers": True,
            "multi_model_routing": True,
            "quality_markers": True,
            "rate_limiting": True,
            "free_tier_default": True,
            "input_sanitization": True
        },
        "rate_limits": {
            "per_ip": f"{rate_stats['ip_limit']} req/{rate_stats['window_seconds']}s",
            "global": f"{rate_stats['global_limit']} req/{rate_stats['window_seconds']}s",
            "current_load": f"{rate_stats['global_requests_in_window']}/{rate_stats['global_limit']}"
        },
        "quick_start": "Run: claude mcp add -s user verifimind -- npx -y mcp-remote https://verifimind.ysenseai.org/mcp/"
    })

async def mcp_config_handler(request):
    """MCP configuration endpoint for Claude Desktop and other MCP clients.

    Returns comprehensive setup information including:
    - Ready-to-paste config snippets for Claude Code and Claude Desktop
    - Explicit tool listings
    - BYOK authentication instructions
    """
    # Get the base URL from the request
    scheme = request.headers.get("x-forwarded-proto", request.url.scheme)
    host = request.headers.get("host", request.url.netloc)
    base_url = f"{scheme}://{host}"

    return JSONResponse({
        "mcpServers": {
            "verifimind-genesis": {
                "url": f"{base_url}/mcp/",
                "description": "VerifiMind PEAS Genesis Methodology MCP Server - Multi-Model AI Validation with RefleXion Trinity",
                "version": SERVER_VERSION,
                "transport": "streamable-http",
                "resources": 4,
                "tools": 10,
                "features": {
                    "agents": ["X (Innovation)", "Z (Ethics)", "CS (Security)"],
                    "models": ["Gemini 1.5 Flash (FREE)", "Claude 3.5 Sonnet (BYOK)", "GPT-4o (BYOK)"],
                    "cost_per_validation": "$0 (FREE tier)",
                    "byok": True,
                    "smart_fallback": True,
                    "rate_limiting": True
                },
                "headers": {
                    "Accept": "application/json, text/event-stream, text/markdown"
                }
            }
        },
        # Ready-to-paste config snippets
        "quickstart": {
            "claude_code": {
                "description": "Run this command in your terminal to add the server",
                "command": "claude mcp add -s user verifimind -- npx -y mcp-remote https://verifimind.ysenseai.org/mcp/",
                "project_scope": "claude mcp add -s project verifimind -- npx -y mcp-remote https://verifimind.ysenseai.org/mcp/"
            },
            "claude_desktop": {
                "description": "Add this to your claude_desktop_config.json",
                "config": {
                    "mcpServers": {
                        "verifimind": {
                            "command": "npx",
                            "args": ["-y", "mcp-remote", "https://verifimind.ysenseai.org/mcp/"]
                        }
                    }
                },
                "config_path": {
                    "windows": "%APPDATA%\\Claude\\claude_desktop_config.json",
                    "macos": "~/Library/Application Support/Claude/claude_desktop_config.json",
                    "linux": "~/.config/Claude/claude_desktop_config.json"
                }
            },
            "direct_http": {
                "description": "For custom MCP clients using HTTP transport",
                "url": f"{base_url}/mcp/",
                "transport": "streamable-http",
                "method": "POST",
                "headers": {
                    "Content-Type": "application/json",
                    "Accept": "application/json, text/event-stream"
                }
            }
        },
        # Explicit tool listings
        "tools": [
            {
                "name": "consult_agent_x",
                "description": "Innovation & Strategy analysis (Smart Fallback: Gemini FREE)",
                "parameters": ["concept_name", "concept_description", "context (optional)"]
            },
            {
                "name": "consult_agent_z",
                "description": "Ethics & Safety review with VETO power (Smart Fallback: Claude if BYOK, else Gemini FREE)",
                "parameters": ["concept_name", "concept_description", "context (optional)", "prior_reasoning (optional)"]
            },
            {
                "name": "consult_agent_cs",
                "description": "Security & Feasibility validation (Smart Fallback: Claude if BYOK, else Gemini FREE)",
                "parameters": ["concept_name", "concept_description", "context (optional)", "prior_reasoning (optional)"]
            },
            {
                "name": "run_full_trinity",
                "description": "Complete X → Z → CS validation with per-agent optimized providers",
                "parameters": ["concept_name", "concept_description", "context (optional)", "save_to_history (default: true)"]
            },
            # v0.4.0 Template Tools
            {
                "name": "list_prompt_templates",
                "description": "List available prompt templates with filtering",
                "parameters": ["agent_id (optional)", "category (optional)", "tags (optional)"]
            },
            {
                "name": "get_prompt_template",
                "description": "Get a specific template by ID",
                "parameters": ["template_id", "include_content (default: true)"]
            },
            {
                "name": "export_prompt_template",
                "description": "Export template to Markdown or JSON",
                "parameters": ["template_id", "format (markdown/json)"]
            },
            {
                "name": "register_custom_template",
                "description": "Register a new custom prompt template",
                "parameters": ["name", "agent_id", "content", "category", "description", "tags"]
            },
            {
                "name": "import_template_from_url",
                "description": "Import template from URL (GitHub Gist, raw file)",
                "parameters": ["url", "validate (default: true)"]
            },
            {
                "name": "get_template_statistics",
                "description": "Get template registry statistics",
                "parameters": []
            }
        ],
        # Resources
        "resources": [
            {"uri": "genesis://config/master_prompt", "description": "Genesis Master Prompt v16.1"},
            {"uri": "genesis://history/latest", "description": "Most recent validation result"},
            {"uri": "genesis://history/all", "description": "Complete validation history"},
            {"uri": "genesis://state/project_info", "description": "Project metadata and agent info"}
        ],
        # BYOK Authentication
        "authentication": {
            "description": "Bring Your Own Key (BYOK) - provide API keys via session config",
            "supported_providers": ["openai", "anthropic", "gemini", "groq", "mock"],
            "default_provider": "mock",
            "important_note": "ONE provider is used for ALL agents (X, Z, CS). Per-agent provider selection is not supported.",
            "hosted_server_config": {
                "agent_x": "Gemini 2.0 Flash (developer key - FREE)",
                "agent_z": "Uses same provider as configured",
                "agent_cs": "Uses same provider as configured",
                "default": "Mock provider (no API key needed)"
            },
            "setup_options": {
                "option_1_use_hosted": {
                    "description": "Use the hosted server with developer-provided Gemini key",
                    "cost": "FREE (covered by developer)",
                    "action": "Just use the tools - no configuration needed"
                },
                "option_2_environment_variables": {
                    "description": "Set environment variables before starting Claude Code",
                    "variables": {
                        "LLM_PROVIDER": "gemini | anthropic | openai | groq | mock",
                        "GEMINI_API_KEY": "your-gemini-api-key",
                        "ANTHROPIC_API_KEY": "your-anthropic-api-key",
                        "OPENAI_API_KEY": "your-openai-api-key",
                        "GROQ_API_KEY": "your-groq-api-key"
                    },
                    "example_bash": "export GEMINI_API_KEY='your-key' && export LLM_PROVIDER='gemini' && claude",
                    "example_powershell": "$env:GEMINI_API_KEY='your-key'; $env:LLM_PROVIDER='gemini'; claude"
                },
                "option_3_claude_desktop_env": {
                    "description": "Add env to Claude Desktop config",
                    "config_example": {
                        "mcpServers": {
                            "verifimind": {
                                "command": "npx",
                                "args": ["-y", "mcp-remote", "https://verifimind.ysenseai.org/mcp/"],
                                "env": {
                                    "LLM_PROVIDER": "gemini",
                                    "GEMINI_API_KEY": "your-api-key"
                                }
                            }
                        }
                    }
                }
            },
            "get_free_api_keys": {
                "gemini": "https://aistudio.google.com (FREE tier)",
                "groq": "https://console.groq.com (FREE tier)",
                "anthropic": "https://console.anthropic.com (paid)",
                "openai": "https://platform.openai.com (paid)"
            },
            "security_warning": "NEVER share API keys in chat messages. Use environment variables or config files."
        }
    })

ROOT_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>VerifiMind-PEAS MCP Server</title>
<link rel="icon" type="image/png" href="/favicon.ico">
<style>
  body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
         max-width: 680px; margin: 40px auto; padding: 0 20px; color: #1a1a2e;
         background: #f8f9fa; line-height: 1.6; }
  h1 { color: #16213e; border-bottom: 3px solid #0f3460; padding-bottom: 8px; }
  code { background: #e8eaf6; padding: 2px 6px; border-radius: 4px; font-size: 0.9em; }
  pre { background: #1a1a2e; color: #e0e0e0; padding: 16px; border-radius: 8px;
        overflow-x: auto; font-size: 0.85em; }
  .badge { display: inline-block; background: #0f3460; color: #fff; padding: 2px 10px;
           border-radius: 12px; font-size: 0.8em; }
  a { color: #0f3460; }
  .card { background: #fff; border: 1px solid #dee2e6; border-radius: 8px;
          padding: 16px; margin: 12px 0; }
</style>
</head>
<body>
<h1>VerifiMind-PEAS MCP Server <span class="badge">v""" + SERVER_VERSION + """</span></h1>
<p>This is an <strong>MCP (Model Context Protocol) server</strong>, not a website.
Connect using an MCP client such as Claude Desktop, Claude Code, or Cursor.</p>

<div class="card">
<h3>Quick Start &mdash; Claude Code</h3>
<pre>claude mcp add -s user verifimind -- npx -y mcp-remote https://verifimind.ysenseai.org/mcp/</pre>
</div>

<div class="card">
<h3>Quick Start &mdash; Claude Desktop</h3>
<p>Add to your <code>claude_desktop_config.json</code>:</p>
<pre>{
  "mcpServers": {
    "verifimind": {
      "command": "npx",
      "args": ["-y", "mcp-remote", "https://verifimind.ysenseai.org/mcp/"]
    }
  }
}</pre>
</div>

<h3>Links</h3>
<ul>
  <li><a href="https://verifimind.io">Landing Page</a></li>
  <li><a href="https://github.com/creator35lwb-web/VerifiMind-PEAS">GitHub Repository</a></li>
  <li><a href="/health">Health Check</a></li>
  <li><a href="/.well-known/mcp-config">Full MCP Configuration</a></li>
  <li><a href="/setup">Setup Guide (JSON)</a></li>
</ul>
<p><small>10 tools &middot; 4 resources &middot; X-Z-CS RefleXion Trinity &middot;
<a href="https://doi.org/10.5281/zenodo.17972751">DOI 10.5281/zenodo.17972751</a></small></p>
</body>
</html>"""


async def root_handler(request):
    """Root endpoint — HTML for browsers, JSON for API clients."""
    accept = request.headers.get("accept", "")
    if "text/html" in accept:
        return HTMLResponse(ROOT_HTML)
    return JSONResponse({
        "name": "VerifiMind PEAS MCP Server",
        "version": SERVER_VERSION,
        "mcp_endpoint": "/mcp/",
        "documentation": "https://github.com/creator35lwb-web/VerifiMind-PEAS",
        "landing_page": "https://verifimind.io",
        "message": "Connect to /mcp/ using an MCP client (Claude Desktop, Cursor, VS Code)",
        "endpoints": {
            "mcp": "/mcp/",
            "config": "/.well-known/mcp-config",
            "health": "/health",
            "setup": "/setup"
        },
        "quick_start": "claude mcp add -s user verifimind -- npx -y mcp-remote https://verifimind.ysenseai.org/mcp/"
    })


async def root_post_redirect(request):
    """POST / redirects to /mcp/ — catches misconfigured Claude Desktop clients."""
    return RedirectResponse(url="/mcp/", status_code=307)


async def setup_handler(request):
    """User-friendly setup page with step-by-step instructions"""
    # Get the base URL from the request
    scheme = request.headers.get("x-forwarded-proto", request.url.scheme)
    host = request.headers.get("host", request.url.netloc)
    base_url = f"{scheme}://{host}"

    return JSONResponse({
        "title": "VerifiMind MCP Server Setup Guide",
        "version": SERVER_VERSION,

        "step_1_choose_client": {
            "description": "Choose your MCP client",
            "options": ["Claude Code (CLI)", "Claude Desktop (App)", "Custom Client"]
        },

        "step_2_claude_code": {
            "title": "Setup for Claude Code",
            "steps": [
                {
                    "step": 1,
                    "action": "Open terminal and run",
                    "command": "claude mcp add -s user verifimind -- npx -y mcp-remote https://verifimind.ysenseai.org/mcp/",
                    "note": "Use '-s project' instead of '-s user' for project-specific setup"
                },
                {
                    "step": 2,
                    "action": "Verify connection",
                    "command": "claude mcp list",
                    "expected": "verifimind: ... - Connected"
                },
                {
                    "step": 3,
                    "action": "Restart Claude Code",
                    "command": "Exit and re-run 'claude' in your terminal"
                },
                {
                    "step": 4,
                    "action": "Check available tools",
                    "command": "Type /mcp in Claude Code"
                }
            ]
        },

        "step_2_claude_desktop": {
            "title": "Setup for Claude Desktop",
            "steps": [
                {
                    "step": 1,
                    "action": "Find your config file",
                    "paths": {
                        "windows": "%APPDATA%\\Claude\\claude_desktop_config.json",
                        "macos": "~/Library/Application Support/Claude/claude_desktop_config.json",
                        "linux": "~/.config/Claude/claude_desktop_config.json"
                    }
                },
                {
                    "step": 2,
                    "action": "Add this configuration",
                    "config": {
                        "mcpServers": {
                            "verifimind": {
                                "command": "npx",
                                "args": ["-y", "mcp-remote", "https://verifimind.ysenseai.org/mcp/"]
                            }
                        }
                    }
                },
                {
                    "step": 3,
                    "action": "Restart Claude Desktop"
                }
            ]
        },

        "step_3_test": {
            "title": "Test the connection",
            "example_prompts": [
                "Use the run_full_trinity tool to validate a concept called 'AI-powered code review' that uses machine learning to detect bugs",
                "Consult Agent X about the innovation potential of blockchain voting systems",
                "Ask Agent Z to evaluate the ethics of facial recognition in schools"
            ]
        },

        "available_tools": {
            "consult_agent_x": {
                "description": "Innovation & Strategy analysis",
                "powered_by": "Gemini 1.5 Flash (FREE) - Smart Fallback",
                "use_for": "Evaluating market potential, competitive positioning, innovation score"
            },
            "consult_agent_z": {
                "description": "Ethics & Safety review",
                "powered_by": "Claude (if BYOK) or Gemini FREE - Smart Fallback",
                "use_for": "Privacy concerns, bias detection, social impact, Z-Protocol compliance",
                "special": "Has VETO POWER - can reject unethical concepts"
            },
            "consult_agent_cs": {
                "description": "Security & Feasibility validation",
                "powered_by": "Claude (if BYOK) or Gemini FREE - Smart Fallback",
                "use_for": "Security vulnerabilities, attack vectors, Socratic questioning"
            },
            "run_full_trinity": {
                "description": "Complete validation workflow with per-agent optimized providers",
                "flow": "X (Gemini) -> Z (Claude/Gemini) -> CS (Claude/Gemini) -> Synthesis",
                "use_for": "Comprehensive concept validation with all three agents"
            }
        },

        "troubleshooting": {
            "no_mcp_servers_found": {
                "problem": "/mcp shows 'No MCP servers configured'",
                "solutions": [
                    "Make sure you ran 'claude mcp add' (not just edited settings.json)",
                    "Check with 'claude mcp list' outside of Claude Code",
                    "Restart Claude Code completely"
                ]
            },
            "connection_failed": {
                "problem": "Server shows as disconnected",
                "solutions": [
                    "Check your internet connection",
                    f"Verify server is online: curl {base_url}/health",
                    "Try removing and re-adding: claude mcp remove verifimind && claude mcp add ..."
                ]
            }
        }
    })

ROBOTS_TXT = """\
User-agent: *
Disallow: /mcp/
Allow: /health
Allow: /.well-known/

# VerifiMind-PEAS MCP Server
# Landing page: https://verifimind.io
# GitHub: https://github.com/creator35lwb-web/VerifiMind-PEAS
"""

# VerifiMind PEAS favicon (32x32 PNG, ~2.7KB)
# Generated from docs/assets/branding/VerifiMind-PEAS-Icon.png
import base64 as _b64
_FAVICON_B64 = (
    "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"
)
FAVICON_BYTES = _b64.b64decode(_FAVICON_B64)

HELP_URL = "https://github.com/creator35lwb-web/VerifiMind-PEAS#-common-mistakes-read-this-first"


async def robots_handler(request):
    """Serve robots.txt to suppress crawler 404s."""
    return PlainTextResponse(ROBOTS_TXT)


async def favicon_handler(request):
    """Serve the VerifiMind PEAS favicon (32x32 PNG)."""
    return Response(content=FAVICON_BYTES, media_type="image/png")


async def http_exception_handler(request, exc):
    """Return actionable error messages for common HTTP errors."""
    status = exc.status_code
    if status == 405:
        return JSONResponse({
            "error": "Method Not Allowed",
            "message": "The MCP endpoint is at /mcp/ — you may have the wrong URL path.",
            "mcp_endpoint": "/mcp/",
            "help": HELP_URL,
        }, status_code=405)
    if status == 400:
        return JSONResponse({
            "error": "Bad Request",
            "message": "Invalid MCP request. Ensure you are using POST with Content-Type: application/json.",
            "help": HELP_URL,
        }, status_code=400)
    if status == 406:
        return JSONResponse({
            "error": "Not Acceptable",
            "message": "This is an MCP server API, not a website. Use an MCP client to connect.",
            "landing_page": "https://verifimind.io",
            "help": HELP_URL,
        }, status_code=406)
    # Default for other errors
    return JSONResponse({
        "error": exc.detail if hasattr(exc, 'detail') else str(exc),
        "help": HELP_URL,
    }, status_code=status)


# Create Starlette app with proper lifespan from MCP app
app = Starlette(
    routes=[
        Route("/health", health_handler),
        Route("/", root_handler, methods=["GET", "HEAD"]),
        Route("/", root_post_redirect, methods=["POST"]),
        Route("/robots.txt", robots_handler),
        Route("/favicon.ico", favicon_handler),
        Route("/setup", setup_handler),
        Route("/.well-known/mcp-config", mcp_config_handler),
        Mount("/mcp", app=mcp_app),
    ],
    lifespan=mcp_app.lifespan,  # CRITICAL: Pass lifespan for session initialization
    exception_handlers={400: http_exception_handler, 405: http_exception_handler, 406: http_exception_handler},
)

# IMPORTANT: Add middleware in correct order
# 1. Rate limiting (first, to block before any processing)
# 2. CORS (second, for browser clients)

# Rate limiting middleware - EDoS protection
# Prevents auto-scale cost attacks and API abuse
app.add_middleware(RateLimitMiddleware)

# CORS middleware for browser-based MCP clients
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for MCP clients
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS", "DELETE"],
    allow_headers=["*"],
    expose_headers=["mcp-session-id", "mcp-protocol-version", "X-RateLimit-Limit", "X-RateLimit-Remaining", "X-RateLimit-Reset"],
    max_age=86400,  # Cache preflight for 24 hours
)

# Print server info when module is loaded
print("=" * 70)
print(f"VerifiMind-PEAS MCP Server - HTTP Mode (v{SERVER_VERSION})")
print("=" * 70)
print(f"Server: verifimind-genesis")
print(f"Version: {SERVER_VERSION}")
print(f"Transport: streamable-http (FastMCP)")
print(f"Port: {os.getenv('PORT', '8080')}")
print("-" * 70)
print("SECURITY FEATURES (v0.3.5):")
print(f"  Input Sanitization: Prompt injection protection (v0.3.5)")
print(f"  Rate Limiting: {os.getenv('RATE_LIMIT_PER_IP', '10')} req/min per IP")
print(f"  Global Limit:  {os.getenv('RATE_LIMIT_GLOBAL', '100')} req/min per instance")
print(f"  CORS: Enabled (all origins)")
print("-" * 70)
print("SMART FALLBACK (v0.3.1):")
print("  X Agent:  Gemini (FREE) - Innovation/Strategy")
print("  Z Agent:  Gemini (FREE) -> Claude if ANTHROPIC_API_KEY set")
print("  CS Agent: Gemini (FREE) -> Claude if ANTHROPIC_API_KEY set")
print("-" * 70)
print("Endpoints:")
print(f"  MCP:    /mcp/")
print(f"  Health: /health")
print(f"  Config: /.well-known/mcp-config")
print(f"  Setup:  /setup")
print("-" * 70)
print("Resources: 4 | Tools: 10")
print("Agents: X (Innovation) | Z (Ethics) | CS (Security)")
print("-" * 70)
print("Quick Start (Claude Code):")
print("  claude mcp add -s user verifimind -- npx -y mcp-remote \\")
print("    https://verifimind.ysenseai.org/mcp/")
print("=" * 70)
print("Server ready for connections...")
print("=" * 70)

# For direct execution (testing)
if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", "8080"))

    print(f"\nStarting HTTP server on 0.0.0.0:{port}")
    print(f"Try:")
    print(f"  curl http://localhost:{port}/")
    print(f"  curl http://localhost:{port}/health")
    print(f"  curl -X POST http://localhost:{port}/mcp/ -H 'Content-Type: application/json' -H 'Accept: application/json, text/event-stream' -d '{{...}}'\n")

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port,
        log_level="info"
    )
