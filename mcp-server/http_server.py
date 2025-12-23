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
        "version": "0.2.3",
        "transport": "streamable-http",
        "endpoints": {
            "mcp": "/mcp",
            "config": "/.well-known/mcp-config",
            "health": "/health"
        },
        "resources": 4,
        "tools": 4
    })

async def mcp_config_handler(request):
    """MCP configuration endpoint for Claude Desktop and other MCP clients"""
    # Get the base URL from the request
    scheme = request.headers.get("x-forwarded-proto", request.url.scheme)
    host = request.headers.get("host", request.url.netloc)
    base_url = f"{scheme}://{host}"
    
    return JSONResponse({
        "mcpServers": {
            "verifimind-genesis": {
                "url": f"{base_url}/mcp/",
                "description": "VerifiMind PEAS Genesis Methodology MCP Server - Multi-Model AI Validation with RefleXion Trinity",
                "version": "0.2.3",
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
        }
    })

async def root_handler(request):
    """Root endpoint with server info"""
    return JSONResponse({
        "name": "VerifiMind PEAS MCP Server",
        "version": "0.2.3",
        "description": "Model Context Protocol server for VerifiMind-PEAS Genesis Methodology - Multi-Model AI Validation System",
        "author": "Alton Lee",
        "repository": "https://github.com/creator35lwb-web/VerifiMind-PEAS",
        "documentation": "https://doi.org/10.5281/zenodo.17645665",
        "landing_page": "https://verifimind.manus.space",
        "endpoints": {
            "mcp": "/mcp/",
            "config": "/.well-known/mcp-config",
            "health": "/health"
        },
        "resources": 4,
        "tools": 4,
        "agents": {
            "X": "Innovation & Strategy (Gemini 2.0 Flash - FREE)",
            "Z": "Ethics & Safety (Claude 3 Haiku)",
            "CS": "Security & Feasibility (Claude 3 Haiku)"
        },
        "byok": {
            "description": "Bring Your Own Key - provide your API keys via session config",
            "supported_providers": ["openai", "anthropic", "gemini", "mock"],
            "default_provider": "mock"
        },
        "status": "online"
    })

# Create Starlette app with proper lifespan from MCP app
app = Starlette(
    routes=[
        Route("/health", health_handler),
        Route("/", root_handler),
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
print("VerifiMind-PEAS MCP Server - HTTP Mode (v0.2.3)")
print("=" * 70)
print(f"Server: verifimind-genesis")
print(f"Version: 0.2.3")
print(f"Transport: streamable-http (FastMCP)")
print(f"Port: {os.getenv('PORT', '8080')}")
print(f"CORS: Enabled (all origins)")
print("-" * 70)
print(f"MCP Endpoint: /mcp/")
print(f"Health Endpoint: /health")
print(f"Config Endpoint: /.well-known/mcp-config")
print("-" * 70)
print("Resources: 4 | Tools: 4")
print("Agents: X (Innovation) | Z (Ethics) | CS (Security)")
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
