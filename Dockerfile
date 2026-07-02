# Dockerfile for VerifiMind MCP Server — repo-root build context
# (used by cloudbuild.yaml / the Cloud Build trigger; mirrors mcp-server/Dockerfile)
# Python 3.12 with uv package manager for fast dependency installation

FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

# Set working directory
WORKDIR /app

# Install curl for healthcheck
RUN apt-get update && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/*

# Copy mcp-server source code
# Build-context exclusions (tests/, docs/, .env, ...) enforced by root .dockerignore
COPY mcp-server/ .

# Install the package and dependencies using uv
RUN uv pip install --system --no-cache .

# Run as a dedicated non-root user; /app stays writable for the opt-in
# validation-history file (server.py writes to Path.cwd()).
RUN groupadd --system app \
    && useradd --system --gid app --home-dir /app --shell /usr/sbin/nologin app \
    && chown -R app:app /app
USER app

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PORT=8080

# Expose the port (Cloud Run will map this)
EXPOSE 8080

# Healthcheck for container orchestrators (Cloud Run uses its own probes)
HEALTHCHECK --interval=5s --timeout=3s --start-period=10s --retries=3 \
  CMD curl -f http://localhost:${PORT}/health || exit 1

# Run the MCP server with Uvicorn HTTP server (available at /mcp endpoint)
CMD ["sh", "-c", "uvicorn http_server:app --host 0.0.0.0 --port ${PORT}"]
