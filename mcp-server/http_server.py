"""
HTTP Server Entry Point for VerifiMind MCP Server
Designed for Smithery deployment with HTTP transport
Uses FastMCP's http_app() mounted in FastAPI for full endpoint control
"""
import os
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from verifimind_mcp.server import create_server

# Create main FastAPI app for custom routes
app = FastAPI(
    title="VerifiMind-PEAS MCP Server",
    description="Model Context Protocol server for Genesis Methodology validation",
    version="0.2.0"
)

# Create MCP server instance
mcp_server = create_server()

# Mount MCP server at /mcp endpoint
# This exposes the MCP protocol with SSE transport
app.mount("/mcp", mcp_server.http_app())

# Custom endpoints for Smithery discovery and monitoring

@app.get("/.well-known/mcp-config")
async def mcp_config():
    """
    Smithery server discovery endpoint.
    Provides metadata about the MCP server for client configuration.
    """
    return JSONResponse({
        "mcpServers": {
            "verifimind-genesis": {
                "url": "/mcp",
                "transport": "sse",
                "metadata": {
                    "name": "VerifiMind PEAS Genesis",
                    "version": "0.2.0",
                    "description": "Model Context Protocol server for VerifiMind-PEAS Genesis Methodology",
                    "author": "Alton Lee",
                    "homepage": "https://github.com/creator35lwb-web/VerifiMind-PEAS"
                },
                "capabilities": {
                    "resources": {
                        "count": 4,
                        "list": [
                            "genesis://config/master_prompt",
                            "genesis://history/latest",
                            "genesis://history/all",
                            "genesis://state/project_info"
                        ]
                    },
                    "tools": {
                        "count": 4,
                        "list": [
                            "consult_agent_x",
                            "consult_agent_z",
                            "consult_agent_cs",
                            "run_full_trinity"
                        ]
                    }
                }
            }
        }
    })


@app.get("/health")
async def health():
    """
    Health check endpoint for monitoring.
    Returns server status and basic information.
    """
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


@app.get("/")
async def root():
    """
    Root endpoint providing server information and available endpoints.
    """
    return JSONResponse({
        "name": "VerifiMind PEAS MCP Server",
        "version": "0.2.0",
        "description": "Model Context Protocol server for VerifiMind-PEAS Genesis Methodology",
        "author": "Alton Lee",
        "repository": "https://github.com/creator35lwb-web/VerifiMind-PEAS",
        "endpoints": {
            "mcp": "/mcp",
            "config": "/.well-known/mcp-config",
            "health": "/health",
            "docs": "/docs",
            "redoc": "/redoc"
        },
        "resources": 4,
        "tools": 4,
        "status": "online"
    })


# Add .well-known/mcp-config endpoint for Smithery discovery
from fastapi.responses import JSONResponse

@app.get("/.well-known/mcp-config")
async def mcp_config():
    """
    MCP Server Configuration Endpoint
    
    This endpoint is required by Smithery to discover the MCP server
    and its capabilities without authentication.
    """
    return JSONResponse({
        "mcpServers": {
            "verifimind-genesis": {
                "url": "/mcp",
                "transport": "sse",
                "metadata": {
                    "name": "VerifiMind PEAS Genesis",
                    "version": "0.2.0",
                    "description": "Model Context Protocol server for VerifiMind-PEAS Genesis Methodology",
                    "author": "Alton Lee",
                    "homepage": "https://github.com/creator35lwb-web/VerifiMind-PEAS"
                },
                "capabilities": {
                    "resources": {
                        "count": 4,
                        "list": [
                            "genesis://config/master_prompt",
                            "genesis://history/latest",
                            "genesis://history/all",
                            "genesis://state/project_info"
                        ]
                    },
                    "tools": {
                        "count": 4,
                        "list": [
                            "consult_agent_x",
                            "consult_agent_z",
                            "consult_agent_cs",
                            "run_full_trinity"
                        ]
                    }
                }
            }
        }
    })

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring"""
    return JSONResponse({
        "status": "healthy",
        "server": "verifimind-genesis",
        "version": "0.2.0"
    })

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with server information"""
    return JSONResponse({
        "name": "VerifiMind PEAS MCP Server",
        "version": "0.2.0",
        "description": "Model Context Protocol server for VerifiMind-PEAS Genesis Methodology",
        "endpoints": {
            "mcp": "/mcp",
            "config": "/.well-known/mcp-config",
            "health": "/health"
        },
        "resources": 4,
        "tools": 4
    })

# Print server info when module is loaded
print("=" * 70)
print("VerifiMind-PEAS MCP Server - HTTP Mode")
print("=" * 70)
print(f"Server: verifimind-genesis")
print(f"Transport: HTTP with SSE (FastMCP)")
print(f"Port: {os.getenv('PORT', '8081')}")
print(f"MCP Endpoint: /mcp")
print(f"Config Endpoint: /.well-known/mcp-config")
print(f"Health Endpoint: /health")
print("=" * 70)
print("Resources: 4 | Tools: 4")
print("Server ready for connections...")
print("=" * 70)


# For direct execution (testing)
if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", "8081"))

    print(f"\nStarting HTTP server on 0.0.0.0:{port}")
    print(f"Try:")
    print(f"  curl http://localhost:{port}/")
    print(f"  curl http://localhost:{port}/health")
    print(f"  curl http://localhost:{port}/.well-known/mcp-config")
    print(f"  curl http://localhost:{port}/mcp\n")

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port,
        log_level="info"
    )
