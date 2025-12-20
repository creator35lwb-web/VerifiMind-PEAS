# Dockerfile for VerifiMind MCP Server - Smithery Deployment
# Python 3.12 with uv package manager for fast dependency installation

FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

# Set working directory
WORKDIR /app

# Copy all source code (needed for package installation)
COPY . .

# Install the package and dependencies using uv
RUN uv pip install --system --no-cache .

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PORT=8081

# Expose the port (Smithery will map this)
EXPOSE 8081

# Run the MCP server with Uvicorn HTTP server
# Smithery sets PORT=8081, server will be available at /mcp endpoint
CMD ["sh", "-c", "uvicorn http_server:app --host 0.0.0.0 --port ${PORT}"]
