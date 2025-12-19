"""
HTTP Server Entry Point for VerifiMind MCP Server
Designed for Smithery deployment with HTTP transport
"""
import os
import sys
from pathlib import Path

# Add src directory to Python path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

# Import the server creation function
from verifimind_mcp.server import create_server

# Create the MCP server instance
mcp_server = create_server()

# Create ASGI application for uvicorn
# This exposes the MCP server at /mcp endpoint
app = mcp_server.http_app()

# Print server info when module is loaded
print("=" * 70)
print("VerifiMind-PEAS MCP Server - HTTP Mode")
print("=" * 70)
print(f"Server: verifimind-genesis")
print(f"Transport: HTTP (Smithery Streamable)")
print(f"Port: {os.getenv('PORT', '8081')}")
print(f"Endpoint: /mcp")
print("=" * 70)
print("Resources: 4 | Tools: 4")
print("Server ready for connections...")
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
