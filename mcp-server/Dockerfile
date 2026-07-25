# Dockerfile for VerifiMind MCP Server — Cloud Run production image
# (built by `gcloud builds submit` from mcp-server/, see deploy-cloudrun.sh)
# Python 3.12 with uv package manager for fast dependency installation

FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

# Set working directory
WORKDIR /app

# Install curl for healthcheck
RUN apt-get update && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/*

# Copy all source code (needed for package installation)
# Build-context exclusions (tests/, docs/, .env, ...) enforced by .dockerignore
COPY . .

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

# B-94-1/B-95-1: immutable build identity carried BY THE IMAGE as a FILE —
# the WP-B failover evidence gate compares FAILOVER_EVIDENCE_BUILD against
# /app/.build_commit_sha. A file cannot be shadowed by Cloud Run service
# configuration (unlike ENV, which service-level vars override and which
# persists across revisions), so artifact B can never inherit artifact A's
# identity. Baked at build time via --build-arg COMMIT_SHA=<source sha>;
# empty when absent => the evidence gate fails closed.
ARG COMMIT_SHA=""
RUN printf '%s' "${COMMIT_SHA}" > /app/.build_commit_sha

# Expose the port (Cloud Run will map this)
EXPOSE 8080

# Healthcheck for container orchestrators (Cloud Run uses its own probes)
HEALTHCHECK --interval=5s --timeout=3s --start-period=10s --retries=3 \
  CMD curl -f http://localhost:${PORT}/health || exit 1

# Run the MCP server with Uvicorn HTTP server (available at /mcp endpoint)
CMD ["sh", "-c", "uvicorn http_server:app --host 0.0.0.0 --port ${PORT}"]
