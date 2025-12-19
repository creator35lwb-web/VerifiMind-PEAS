"""
HTTP Server Entry Point for VerifiMind MCP Server
Designed for Smithery deployment with HTTP transport
Uses Smithery's create_smithery_server for proper SSE support
"""
import os
from fastapi import FastAPI
from smithery.server import create_smithery_server
from verifimind_mcp.server import create_server

# Create FastAPI app
app = FastAPI(
    title="VerifiMind-PEAS MCP Server",
    description="Model Context Protocol server for Genesis Methodology validation",
    version="0.1.0"
)

# Create MCP server instance
mcp_server = create_server()

# Add Smithery SSE endpoint at /mcp
# This creates the proper HTTP endpoint with Server-Sent Events support
create_smithery_server(app, mcp_server)

# Print server info when module is loaded
print("=" * 70)
print("VerifiMind-PEAS MCP Server - Smithery Mode")
print("=" * 70)
print(f"Server: verifimind-mcp")
print(f"Transport: HTTP with SSE (Smithery)")
print(f"Port: {os.getenv('PORT', '8081')}")
print(f"Endpoint: /mcp")
print("=" * 70)
print("Resources: 4 | Tools: 4")
print("Server ready for Smithery connections...")
print("=" * 70)

# For direct execution (optional, mainly for testing)
if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", "8081"))

    print(f"\nStarting HTTP server on 0.0.0.0:{port}")
    print(f"MCP endpoint: http://0.0.0.0:{port}/mcp\n")

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port,
        log_level="info"
    )
