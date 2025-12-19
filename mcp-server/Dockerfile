# Dockerfile for VerifiMind MCP Server - Smithery Deployment
# Python 3.12 with uv package manager for fast dependency installation

FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

# Set working directory
WORKDIR /app

# Copy dependency files AND readme first (for better layer caching)
COPY pyproject.toml README.md ./

# Install dependencies using uv
RUN uv pip install --system --no-cache -e .

# Copy the entire source code
COPY . .

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PORT=8081

# Expose the port (Smithery will map this)
EXPOSE 8081

# Run the MCP server with Uvicorn HTTP server
# Smithery sets PORT=8081, server will be available at /mcp endpoint
CMD ["sh", "-c", "uvicorn http_server:app --host 0.0.0.0 --port ${PORT}"]
