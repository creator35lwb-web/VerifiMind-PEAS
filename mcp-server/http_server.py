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
