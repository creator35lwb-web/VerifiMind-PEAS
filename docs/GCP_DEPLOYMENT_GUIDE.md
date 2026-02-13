# VerifiMind PEAS MCP Server - Google Cloud Run Deployment Guide

**Version:** 0.2.3  
**Last Updated:** December 23, 2025  
**Target:** Google Cloud Run (verifimind.ysenseai.org)

---

## Overview

This guide provides step-by-step instructions for deploying the VerifiMind PEAS MCP Server to Google Cloud Run. The server implements the Model Context Protocol (MCP) for AI validation using the RefleXion Trinity methodology (X-Z-CS agents).

## Prerequisites

Before deployment, ensure you have:

1. **Google Cloud CLI** (`gcloud`) installed and authenticated
2. **Docker** installed (for local testing, optional)
3. **Git** access to the repository
4. **GCP Project** with Cloud Run API enabled

## Repository Information

| Repository | URL | Purpose |
|------------|-----|---------|
| Primary | https://github.com/creator35lwb-web/VerifiMind-PEAS | Full project with documentation |
| Lightweight | https://github.com/creator35lwb-web/verifimind-mcp-server | Deployment-optimized (use this) |

---

## Deployment Steps

### Step 1: Clone the Repository

```bash
# Clone the lightweight deployment repo
git clone https://github.com/creator35lwb-web/verifimind-mcp-server.git
cd verifimind-mcp-server

# Verify you have the latest version (0.2.3)
git pull origin main
```

### Step 2: Verify the Dockerfile

The repository includes a `Dockerfile` optimized for Cloud Run:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Install the package
RUN pip install -e .

# Expose port (Cloud Run uses PORT env var)
EXPOSE 8080

# Run the HTTP server
CMD ["python", "http_server.py"]
```

### Step 3: Set GCP Project Configuration

```bash
# Set your GCP project
export PROJECT_ID="your-gcp-project-id"
export REGION="asia-southeast1"  # or your preferred region
export SERVICE_NAME="verifimind-mcp-server"

# Configure gcloud
gcloud config set project $PROJECT_ID
gcloud config set run/region $REGION
```

### Step 4: Build and Push Container Image

```bash
# Enable required APIs
gcloud services enable cloudbuild.googleapis.com
gcloud services enable run.googleapis.com
gcloud services enable artifactregistry.googleapis.com

# Create Artifact Registry repository (if not exists)
gcloud artifacts repositories create verifimind \
    --repository-format=docker \
    --location=$REGION \
    --description="VerifiMind MCP Server images"

# Configure Docker for Artifact Registry
gcloud auth configure-docker ${REGION}-docker.pkg.dev

# Build and push using Cloud Build
gcloud builds submit --tag ${REGION}-docker.pkg.dev/${PROJECT_ID}/verifimind/${SERVICE_NAME}:v0.2.3
```

### Step 5: Deploy to Cloud Run

```bash
# Deploy the service
gcloud run deploy $SERVICE_NAME \
    --image ${REGION}-docker.pkg.dev/${PROJECT_ID}/verifimind/${SERVICE_NAME}:v0.2.3 \
    --platform managed \
    --region $REGION \
    --allow-unauthenticated \
    --port 8080 \
    --memory 512Mi \
    --cpu 1 \
    --min-instances 0 \
    --max-instances 10 \
    --timeout 300 \
    --set-env-vars "VERIFIMIND_LLM_PROVIDER=mock"
```

### Step 6: Configure Custom Domain (Optional)

If you want to use `verifimind.ysenseai.org`:

```bash
# Map custom domain
gcloud run domain-mappings create \
    --service $SERVICE_NAME \
    --domain verifimind.ysenseai.org \
    --region $REGION
```

Then update your DNS records as instructed by GCP.

### Step 7: Verify Deployment

```bash
# Get the service URL
SERVICE_URL=$(gcloud run services describe $SERVICE_NAME --region $REGION --format 'value(status.url)')
echo "Service URL: $SERVICE_URL"

# Test health endpoint
curl -s $SERVICE_URL/health | jq .

# Test root endpoint
curl -s $SERVICE_URL/ | jq .

# Test MCP initialize (note the trailing slash!)
curl -s -X POST $SERVICE_URL/mcp/ \
    -H "Content-Type: application/json" \
    -H "Accept: application/json, text/event-stream" \
    -d '{"jsonrpc": "2.0", "method": "initialize", "params": {"protocolVersion": "2024-11-05", "capabilities": {}, "clientInfo": {"name": "test", "version": "1.0"}}, "id": 1}'
```

---

## Expected Responses

### Health Check (`/health`)

```json
{
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
}
```

### MCP Initialize (`POST /mcp/`)

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "protocolVersion": "2024-11-05",
    "capabilities": {
      "prompts": {"listChanged": true},
      "resources": {"subscribe": false, "listChanged": true},
      "tools": {"listChanged": true}
    },
    "serverInfo": {
      "name": "verifimind-genesis",
      "version": "2.14.1"
    }
  }
}
```

---

## Important Notes

### MCP Endpoint Requirements

| Requirement | Value |
|-------------|-------|
| **Endpoint** | `/mcp/` (trailing slash required!) |
| **Method** | POST |
| **Content-Type** | `application/json` |
| **Accept** | `application/json, text/event-stream` (both required!) |
| **Transport** | streamable-http |

### Available Tools

| Tool | Description |
|------|-------------|
| `consult_agent_x` | Innovation & Strategy analysis |
| `consult_agent_z` | Ethics & Safety review (has VETO power) |
| `consult_agent_cs` | Security & Feasibility validation |
| `run_full_trinity` | Complete X→Z→CS validation pipeline |

### Available Resources

| Resource URI | Description |
|--------------|-------------|
| `genesis://config/master_prompt` | Genesis Master Prompt v16.1 |
| `genesis://history/latest` | Latest validation result |
| `genesis://history/all` | Complete validation history |
| `genesis://state/project_info` | Project metadata |

---

## Troubleshooting

### Issue: 307 Redirect

**Cause:** Missing trailing slash on `/mcp` endpoint  
**Solution:** Use `/mcp/` (with trailing slash)

### Issue: 406 Not Acceptable

**Cause:** Missing `text/event-stream` in Accept header  
**Solution:** Set `Accept: application/json, text/event-stream`

### Issue: Empty Response

**Cause:** Old server version (< 0.2.3)  
**Solution:** Redeploy with latest code

### Issue: Tool Call Error

**Cause:** Session config not properly initialized  
**Solution:** Ensure you're using the session ID from initialize response

---

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `PORT` | 8080 | Server port (Cloud Run sets this) |
| `VERIFIMIND_LLM_PROVIDER` | mock | Default LLM provider |
| `GEMINI_API_KEY` | - | For Gemini provider (BYOK) |
| `ANTHROPIC_API_KEY` | - | For Anthropic provider (BYOK) |
| `OPENAI_API_KEY` | - | For OpenAI provider (BYOK) |

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 0.2.3 | 2024-12-23 | Fixed MCP routing, added config_helper, BYOK support |
| 0.2.2 | 2024-12-22 | Added streamable-http transport |
| 0.2.1 | 2024-12-21 | Initial HTTP deployment |

---

## Support

- **Repository Issues:** https://github.com/creator35lwb-web/VerifiMind-PEAS/issues
- **Documentation:** https://doi.org/10.5281/zenodo.17645665
- **Landing Page:** https://verifimind.io
