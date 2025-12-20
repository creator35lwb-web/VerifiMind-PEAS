# Deploy VerifiMind PEAS MCP Server to Google Cloud Platform

This guide covers deploying the VerifiMind PEAS MCP Server to Google Cloud Run.

---

## Prerequisites

1. **Google Cloud Account** with billing enabled
2. **gcloud CLI** installed ([Install Guide](https://cloud.google.com/sdk/docs/install))
3. **Docker** installed and running
4. **GCP Project** created

---

## Quick Start

### 1. Set Up GCP Project

```bash
# Set your project ID
export GCP_PROJECT_ID="your-project-id"
export GCP_REGION="us-central1"  # Optional: change region

# Login to GCP
gcloud auth login

# Set default project
gcloud config set project ${GCP_PROJECT_ID}

# Enable required APIs
gcloud services enable run.googleapis.com
gcloud services enable containerregistry.googleapis.com
```

### 2. Configure Docker for GCP

```bash
# Configure Docker to use gcloud as a credential helper
gcloud auth configure-docker
```

### 3. Deploy to Cloud Run

**Option A: Using the deployment script (Recommended)**

```bash
cd mcp-server
chmod +x deploy-gcp.sh
./deploy-gcp.sh
```

**Option B: Manual deployment**

```bash
cd mcp-server

# Build Docker image
docker build -t gcr.io/${GCP_PROJECT_ID}/verifimind-mcp-server:latest .

# Push to Google Container Registry
docker push gcr.io/${GCP_PROJECT_ID}/verifimind-mcp-server:latest

# Deploy to Cloud Run
gcloud run deploy verifimind-mcp-server \
  --image gcr.io/${GCP_PROJECT_ID}/verifimind-mcp-server:latest \
  --platform managed \
  --region ${GCP_REGION} \
  --allow-unauthenticated \
  --port 8081 \
  --memory 512Mi \
  --cpu 1 \
  --set-env-vars "PORT=8081,PYTHONUNBUFFERED=1"
```

---

## Configuration

### Environment Variables

Set environment variables during deployment:

```bash
gcloud run deploy verifimind-mcp-server \
  --set-env-vars "PORT=8081,OPENAI_API_KEY=your-key-here"
```

### Update Service

To update the deployed service:

```bash
# Rebuild and redeploy
./deploy-gcp.sh

# Or update environment variables only
gcloud run services update verifimind-mcp-server \
  --region ${GCP_REGION} \
  --set-env-vars "OPENAI_API_KEY=new-key"
```

---

## Access Control

### Public Access (Default)

The deployment script sets `--allow-unauthenticated` for public access.

### Private Access (Recommended for Production)

For private access with authentication:

```bash
gcloud run deploy verifimind-mcp-server \
  --no-allow-unauthenticated \
  # ... other flags
```

Then invoke with authentication:

```bash
curl -H "Authorization: Bearer $(gcloud auth print-identity-token)" \
  https://your-service-url/health
```

---

## Testing Deployment

After deployment, test the endpoints:

```bash
# Get service URL
SERVICE_URL=$(gcloud run services describe verifimind-mcp-server \
  --platform managed \
  --region ${GCP_REGION} \
  --format 'value(status.url)')

# Test health endpoint
curl ${SERVICE_URL}/health

# Test root endpoint
curl ${SERVICE_URL}/

# Test MCP endpoint
curl ${SERVICE_URL}/mcp
```

---

## Claude Desktop Integration

Add the Cloud Run URL to your Claude Desktop config:

```json
{
  "mcpServers": {
    "verifimind-genesis": {
      "url": "https://your-cloud-run-url/mcp",
      "transport": "sse"
    }
  }
}
```

---

## Monitoring

### View Logs

```bash
gcloud run services logs read verifimind-mcp-server \
  --region ${GCP_REGION} \
  --limit 50
```

### View Metrics

Visit Cloud Run console:
```
https://console.cloud.google.com/run?project=${GCP_PROJECT_ID}
```

---

## Cost Optimization

Cloud Run pricing is based on:
- **CPU time**: Charged per 100ms
- **Memory**: Charged per GB-second
- **Requests**: First 2M requests/month free

**Estimated costs** for low usage:
- ~$0.05-$0.20 per month for < 1000 requests/month
- Free tier covers most development/testing usage

### Cost-Saving Tips

1. Use `--max-instances` to limit scaling
2. Set `--cpu-throttling` for cost-optimized CPU allocation
3. Use `--concurrency` to handle multiple requests per instance

---

## Troubleshooting

### Build Fails

```bash
# Check Docker build locally
docker build -t test-image .
docker run -p 8081:8081 test-image
```

### Deployment Fails

```bash
# Check service logs
gcloud run services logs read verifimind-mcp-server --limit 100

# Check service details
gcloud run services describe verifimind-mcp-server --region ${GCP_REGION}
```

### Container Crashes

```bash
# Check recent revisions
gcloud run revisions list --service verifimind-mcp-server

# Rollback to previous revision
gcloud run services update-traffic verifimind-mcp-server \
  --to-revisions REVISION_NAME=100
```

---

## Cleanup

To delete the service and save costs:

```bash
gcloud run services delete verifimind-mcp-server --region ${GCP_REGION}
```

---

## Support

- **Documentation**: [Google Cloud Run Docs](https://cloud.google.com/run/docs)
- **Pricing**: [Cloud Run Pricing](https://cloud.google.com/run/pricing)
- **Project Issues**: [GitHub Issues](https://github.com/creator35lwb-web/VerifiMind-PEAS/issues)
