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
SERVER_VERSION = "0.4.1"

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

async def root_handler(request):
    """Root endpoint with server info and quick start guide"""
    return JSONResponse({
        "name": "VerifiMind PEAS MCP Server",
        "version": SERVER_VERSION,
        "description": "Model Context Protocol server for VerifiMind-PEAS Genesis Methodology - Multi-Model AI Validation System",
        "author": "Alton Lee",
        "repository": "https://github.com/creator35lwb-web/VerifiMind-PEAS",
        "documentation": "https://doi.org/10.5281/zenodo.17645665",
        "landing_page": "https://verifimind.manus.space",
        "status": "online",
        "endpoints": {
            "mcp": "/mcp/",
            "config": "/.well-known/mcp-config",
            "health": "/health",
            "setup": "/setup"
        },
        "quick_start": {
            "claude_code": "Run: claude mcp add -s user verifimind -- npx -y mcp-remote https://verifimind.ysenseai.org/mcp/",
            "verify": "Run: claude mcp list",
            "docs": "Visit: /.well-known/mcp-config for full setup instructions"
        },
        "tools": [
            "consult_agent_x - Innovation & Strategy",
            "consult_agent_z - Ethics & Safety (has VETO power)",
            "consult_agent_cs - Security & Feasibility",
            "run_full_trinity - Complete X → Z → CS validation"
        ],
        "resources": 4,
        "agents": {
            "X": "Innovation & Strategy (Gemini 1.5 Flash - FREE)",
            "Z": "Ethics & Safety (Claude if BYOK, else Gemini FREE)",
            "CS": "Security & Feasibility (Claude if BYOK, else Gemini FREE)"
        },
        "smart_fallback": {
            "description": "v0.3.1 - Per-agent provider selection with FREE tier default",
            "default": "Gemini 1.5 Flash (FREE) for all agents",
            "upgrade": "Z and CS auto-upgrade to Claude if ANTHROPIC_API_KEY is set"
        },
        "byok": {
            "description": "Bring Your Own Key - provide your API keys via session config",
            "supported_providers": ["openai", "anthropic", "gemini", "groq", "mistral", "ollama", "mock"],
            "default_provider": "gemini (FREE)"
        },
        "rate_limiting": {
            "enabled": True,
            "per_ip": "10 req/min",
            "description": "EDoS protection enabled"
        }
    })


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

# Create Starlette app with proper lifespan from MCP app
app = Starlette(
    routes=[
        Route("/health", health_handler),
        Route("/", root_handler),
        Route("/setup", setup_handler),  # User-friendly setup guide
        Route("/.well-known/mcp-config", mcp_config_handler),  # MCP config endpoint
        Mount("/mcp", app=mcp_app),  # Mount MCP app at /mcp - routes will be /mcp/ (from /)
    ],
    lifespan=mcp_app.lifespan  # CRITICAL: Pass lifespan for session initialization
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
