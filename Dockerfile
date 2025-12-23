# Dockerfile for VerifiMind MCP Server - Smithery Deployment
# Python 3.12 with uv package manager for fast dependency installation

FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

# Set working directory
WORKDIR /app

# Install curl for healthcheck
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

# Copy mcp-server source code
COPY mcp-server/ .

# Install the package and dependencies using uv
RUN uv pip install --system --no-cache .

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PORT=8080

# Expose the port (Cloud Run will map this)
EXPOSE 8080

# Add healthcheck so Smithery knows when server is ready
HEALTHCHECK --interval=5s --timeout=3s --start-period=10s --retries=3 \
  CMD curl -f http://localhost:${PORT}/health || exit 1

# Run the MCP server with Uvicorn HTTP server
# Smithery sets PORT=8081, server will be available at /mcp endpoint
CMD ["sh", "-c", "uvicorn http_server:app --host 0.0.0.0 --port ${PORT}"]
