"""
HTTP Server Entry Point for VerifiMind MCP Server
Designed for Smithery deployment with HTTP transport
Properly handles FastMCP lifespan context for session management

Features:
- CORS middleware for browser-based clients (Smithery)
- Health check endpoint
- MCP configuration endpoint
- Streamable HTTP transport for MCP protocol
"""
import os
import contextlib
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from starlette.applications import Starlette
from starlette.routing import Mount, Route
from starlette.middleware.cors import CORSMiddleware
from verifimind_mcp.server import create_http_server

# Create MCP server instance (raw FastMCP, not SmitheryFastMCP wrapper)
mcp_server = create_http_server()

# Get ASGI app from FastMCP - use path='/' so the route is at root of mounted app
# When mounted at /mcp, requests to /mcp will go to / in the app
mcp_app = mcp_server.http_app(path='/', transport='streamable-http')

# Custom route handlers
async def health_handler(request):
    """Health check endpoint"""
    return JSONResponse({
        "status": "healthy",
        "server": "verifimind-genesis",
        "version": "0.2.4",
        "transport": "streamable-http",
        "endpoints": {
            "mcp": "/mcp",
            "config": "/.well-known/mcp-config",
            "health": "/health",
            "setup": "/setup"
        },
        "resources": 4,
        "tools": 4,
        "quick_start": "Run: claude mcp add -s user verifimind -- npx -y mcp-remote https://server.smithery.ai/creator35lwb-web/verifimind-genesis/mcp"
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
                "version": "0.2.4",
                "transport": "streamable-http",
                "resources": 4,
                "tools": 4,
                "features": {
                    "agents": ["X (Innovation)", "Z (Ethics)", "CS (Security)"],
                    "models": ["Gemini 2.0 Flash (FREE)", "Claude 3 Haiku", "GPT-4"],
                    "cost_per_validation": "$0.003",
                    "byok": True
                },
                "headers": {
                    "Accept": "application/json, text/event-stream"
                }
            }
        },
        # Ready-to-paste config snippets
        "quickstart": {
            "claude_code": {
                "description": "Run this command in your terminal to add the server",
                "command": "claude mcp add -s user verifimind -- npx -y mcp-remote https://server.smithery.ai/creator35lwb-web/verifimind-genesis/mcp",
                "project_scope": "claude mcp add -s project verifimind -- npx -y mcp-remote https://server.smithery.ai/creator35lwb-web/verifimind-genesis/mcp"
            },
            "claude_desktop": {
                "description": "Add this to your claude_desktop_config.json",
                "config": {
                    "mcpServers": {
                        "verifimind": {
                            "command": "npx",
                            "args": ["-y", "mcp-remote", "https://server.smithery.ai/creator35lwb-web/verifimind-genesis/mcp"]
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
                "description": "Innovation & Strategy analysis powered by Gemini 2.0 Flash",
                "parameters": ["concept_name", "concept_description", "context (optional)"]
            },
            {
                "name": "consult_agent_z",
                "description": "Ethics & Safety review with VETO power, powered by Claude 3 Haiku",
                "parameters": ["concept_name", "concept_description", "context (optional)", "prior_reasoning (optional)"]
            },
            {
                "name": "consult_agent_cs",
                "description": "Security & Feasibility validation with Socratic questioning",
                "parameters": ["concept_name", "concept_description", "context (optional)", "prior_reasoning (optional)"]
            },
            {
                "name": "run_full_trinity",
                "description": "Complete X → Z → CS validation workflow with synthesis",
                "parameters": ["concept_name", "concept_description", "context (optional)", "save_to_history (default: true)"]
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
            "supported_providers": ["openai", "anthropic", "gemini", "mock"],
            "default_provider": "mock",
            "setup_instructions": {
                "step1": "Set environment variables: GEMINI_API_KEY, ANTHROPIC_API_KEY, or OPENAI_API_KEY",
                "step2": "Or pass keys via MCP session config when connecting",
                "step3": "The mock provider works without any API keys (for testing)"
            }
        }
    })

async def root_handler(request):
    """Root endpoint with server info and quick start guide"""
    return JSONResponse({
        "name": "VerifiMind PEAS MCP Server",
        "version": "0.2.4",
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
            "claude_code": "Run: claude mcp add -s user verifimind -- npx -y mcp-remote https://server.smithery.ai/creator35lwb-web/verifimind-genesis/mcp",
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
            "X": "Innovation & Strategy (Gemini 2.0 Flash - FREE)",
            "Z": "Ethics & Safety (Claude 3 Haiku)",
            "CS": "Security & Feasibility (Claude 3 Haiku)"
        },
        "byok": {
            "description": "Bring Your Own Key - provide your API keys via session config",
            "supported_providers": ["openai", "anthropic", "gemini", "mock"],
            "default_provider": "mock"
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
        "version": "0.2.4",

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
                    "command": "claude mcp add -s user verifimind -- npx -y mcp-remote https://server.smithery.ai/creator35lwb-web/verifimind-genesis/mcp",
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
                                "args": ["-y", "mcp-remote", "https://server.smithery.ai/creator35lwb-web/verifimind-genesis/mcp"]
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
                "powered_by": "Gemini 2.0 Flash (FREE)",
                "use_for": "Evaluating market potential, competitive positioning, innovation score"
            },
            "consult_agent_z": {
                "description": "Ethics & Safety review",
                "powered_by": "Claude 3 Haiku",
                "use_for": "Privacy concerns, bias detection, social impact, Z-Protocol compliance",
                "special": "Has VETO POWER - can reject unethical concepts"
            },
            "consult_agent_cs": {
                "description": "Security & Feasibility validation",
                "powered_by": "Claude 3 Haiku",
                "use_for": "Security vulnerabilities, attack vectors, Socratic questioning"
            },
            "run_full_trinity": {
                "description": "Complete validation workflow",
                "flow": "X (Innovation) → Z (Ethics) → CS (Security) → Synthesis",
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

# IMPORTANT: Add CORS middleware for Smithery browser-based clients
# This must be added AFTER creating the app but BEFORE running
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for MCP clients
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS", "DELETE"],
    allow_headers=["*"],
    expose_headers=["mcp-session-id", "mcp-protocol-version"],
    max_age=86400,  # Cache preflight for 24 hours
)

# Print server info when module is loaded
print("=" * 70)
print("VerifiMind-PEAS MCP Server - HTTP Mode (v0.2.4)")
print("=" * 70)
print(f"Server: verifimind-genesis")
print(f"Version: 0.2.4")
print(f"Transport: streamable-http (FastMCP)")
print(f"Port: {os.getenv('PORT', '8080')}")
print(f"CORS: Enabled (all origins)")
print("-" * 70)
print("Endpoints:")
print(f"  MCP:    /mcp/")
print(f"  Health: /health")
print(f"  Config: /.well-known/mcp-config")
print(f"  Setup:  /setup  (NEW - User-friendly setup guide)")
print("-" * 70)
print("Resources: 4 | Tools: 4")
print("Agents: X (Innovation) | Z (Ethics) | CS (Security)")
print("-" * 70)
print("Quick Start (Claude Code):")
print("  claude mcp add -s user verifimind -- npx -y mcp-remote \\")
print("    https://server.smithery.ai/creator35lwb-web/verifimind-genesis/mcp")
print("-" * 70)
print("BYOK (Bring Your Own Key): Enabled")
print("Default Provider: mock (for testing without API keys)")
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
