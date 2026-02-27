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

# VerifiMind PEAS favicon (48x48 PNG, ~4.7KB)
# Generated from docs/assets/branding/VerifiMind-PEAS-Icon.png
# Dark background fill (#0f2d3f) for transparent corners
import base64 as _b64
_FAVICON_B64 = (
    "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"
    "AABJRU5ErkJggg=="
)
FAVICON_BYTES = _b64.b64decode(_FAVICON_B64)

HELP_URL = "https://github.com/creator35lwb-web/VerifiMind-PEAS#-common-mistakes-read-this-first"


async def robots_handler(request):
    """Serve robots.txt to suppress crawler 404s."""
    return PlainTextResponse(ROBOTS_TXT)


async def favicon_handler(request):
    """Serve the VerifiMind PEAS favicon (48x48 PNG)."""
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
