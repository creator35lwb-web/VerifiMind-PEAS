#!/bin/bash
# Deploy VerifiMind PEAS MCP Server to Google Cloud Run

set -e  # Exit on error

# Configuration
PROJECT_ID="${GCP_PROJECT_ID:-verifimind-peas}"
REGION="${GCP_REGION:-us-central1}"
SERVICE_NAME="verifimind-mcp-server"
IMAGE_NAME="gcr.io/${PROJECT_ID}/${SERVICE_NAME}"

echo "======================================================================="
echo "Deploying VerifiMind PEAS MCP Server to Google Cloud Run"
echo "======================================================================="
echo "Project ID: ${PROJECT_ID}"
echo "Region: ${REGION}"
echo "Service Name: ${SERVICE_NAME}"
echo "======================================================================="

# Step 1: Build Docker image
echo ""
echo "[1/4] Building Docker image..."
docker build -t ${IMAGE_NAME}:latest .

# Step 2: Push to Google Container Registry
echo ""
echo "[2/4] Pushing image to Google Container Registry..."
docker push ${IMAGE_NAME}:latest

# Step 3: Deploy to Cloud Run
echo ""
echo "[3/4] Deploying to Cloud Run..."
gcloud run deploy ${SERVICE_NAME} \
  --image ${IMAGE_NAME}:latest \
  --platform managed \
  --region ${REGION} \
  --allow-unauthenticated \
  --port 8081 \
  --memory 512Mi \
  --cpu 1 \
  --timeout 300 \
  --max-instances 10 \
  --set-env-vars "PORT=8081,PYTHONUNBUFFERED=1,LOG_LEVEL=INFO" \
  --project ${PROJECT_ID}

# Step 4: Get service URL
echo ""
echo "[4/4] Getting service URL..."
SERVICE_URL=$(gcloud run services describe ${SERVICE_NAME} \
  --platform managed \
  --region ${REGION} \
  --format 'value(status.url)' \
  --project ${PROJECT_ID})

echo ""
echo "======================================================================="
echo "✅ Deployment successful!"
echo "======================================================================="
echo "Service URL: ${SERVICE_URL}"
echo ""
echo "Test endpoints:"
echo "  curl ${SERVICE_URL}/health"
echo "  curl ${SERVICE_URL}/"
echo "  curl ${SERVICE_URL}/mcp"
echo ""
echo "MCP endpoint for Claude Desktop:"
echo "  ${SERVICE_URL}/mcp"
echo "======================================================================="
