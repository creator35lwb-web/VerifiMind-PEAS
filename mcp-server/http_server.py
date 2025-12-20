"""
HTTP Server Entry Point for VerifiMind MCP Server
Designed for Smithery deployment with HTTP transport
Properly handles FastMCP lifespan context for session management
"""
import os
import contextlib
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from starlette.applications import Starlette
from starlette.routing import Mount, Route
from verifimind_mcp.server import create_http_server

# Create MCP server instance (raw FastMCP, not SmitheryFastMCP wrapper)
mcp_server = create_http_server()

# Get ASGI app from FastMCP with proper path
mcp_app = mcp_server.http_app(path="/mcp")

# Custom route handlers
async def health_handler(request):
    """Health check endpoint"""
    return JSONResponse({
        "status": "healthy",
        "server": "verifimind-genesis",
        "version": "0.2.0",
        "transport": "http-sse",
        "endpoints": {
            "mcp": "/mcp",
            "config": "/.well-known/mcp-config",
            "health": "/health"
        }
    })

async def mcp_config_handler(request):
    """MCP configuration endpoint for Claude Desktop and other MCP clients"""
    # Get the base URL from the request
    base_url = str(request.url).replace("/.well-known/mcp-config", "")
    
    return JSONResponse({
        "mcpServers": {
            "verifimind-genesis": {
                "url": f"{base_url}/mcp",
                "description": "VerifiMind PEAS Genesis Methodology MCP Server",
                "version": "0.2.0",
                "transport": "http-sse",
                "resources": 4,
                "tools": 4
            }
        }
    })

async def root_handler(request):
    """Root endpoint with server info"""
    return JSONResponse({
        "name": "VerifiMind PEAS MCP Server",
        "version": "0.2.0",
        "description": "Model Context Protocol server for VerifiMind-PEAS Genesis Methodology",
        "author": "Alton Lee",
        "repository": "https://github.com/creator35lwb-web/VerifiMind-PEAS",
        "endpoints": {
            "mcp": "/mcp",
            "config": "/.well-known/mcp-config",
            "health": "/health"
        },
        "resources": 4,
        "tools": 4,
        "status": "online"
    })

# Create Starlette app with proper lifespan from MCP app
app = Starlette(
    routes=[
        Route("/health", health_handler),
        Route("/", root_handler),
        Route("/.well-known/mcp-config", mcp_config_handler),  # MCP config endpoint
        Mount("/mcp", app=mcp_app),
    ],
    lifespan=mcp_app.lifespan  # CRITICAL: Pass lifespan for session initialization
)

# Print server info when module is loaded
print("=" * 70)
print("VerifiMind-PEAS MCP Server - HTTP Mode")
print("=" * 70)
print(f"Server: verifimind-genesis")
print(f"Transport: HTTP with SSE (FastMCP)")
print(f"Port: {os.getenv('PORT', '8080')}")
print(f"MCP Endpoint: /mcp")
print(f"Health Endpoint: /health")
print(f"Config Endpoint: /.well-known/mcp-config")
print("=" * 70)
print("Resources: 4 | Tools: 4")
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
    print(f"  curl http://localhost:{port}/mcp\n")

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port,
        log_level="info"
    )
