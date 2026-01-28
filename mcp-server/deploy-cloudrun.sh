#!/bin/bash
# ============================================================================
# VerifiMind-PEAS Cloud Run Deployment Script
# v0.3.1 - With EDoS Protection Settings
# ============================================================================
#
# This script deploys the MCP server to Google Cloud Run with:
# - Hard-capped auto-scaling (max 3 instances)
# - Rate limiting enabled
# - FREE tier Gemini as default
# - Cost-optimized settings
#
# Prerequisites:
#   gcloud auth login
#   gcloud config set project YOUR_PROJECT_ID
#
# Usage:
#   chmod +x deploy-cloudrun.sh
#   ./deploy-cloudrun.sh
#
# ============================================================================

set -e  # Exit on error

# Configuration
SERVICE_NAME="verifimind-mcp"
REGION="asia-southeast1"  # Singapore (closest to Southeast Asia)
PROJECT_ID=$(gcloud config get-value project)

# CRITICAL: Protection settings
MAX_INSTANCES=3           # Hard cap - prevents runaway scaling
MIN_INSTANCES=0           # Scale to zero when idle (cost savings)
CONCURRENCY=10            # Max concurrent requests per instance
TIMEOUT=60                # Request timeout in seconds
MEMORY="512Mi"            # Memory limit
CPU="1"                   # CPU limit

# Rate limiting (environment variables)
RATE_LIMIT_PER_IP=10
RATE_LIMIT_GLOBAL=100

echo "============================================================================"
echo "VerifiMind-PEAS Cloud Run Deployment"
echo "============================================================================"
echo "Project:       $PROJECT_ID"
echo "Service:       $SERVICE_NAME"
echo "Region:        $REGION"
echo "Max Instances: $MAX_INSTANCES (HARD CAP - EDoS Protection)"
echo "Memory:        $MEMORY"
echo "CPU:           $CPU"
echo "============================================================================"

# Confirm deployment
read -p "Deploy with these settings? (y/N): " confirm
if [[ $confirm != [yY] ]]; then
    echo "Deployment cancelled."
    exit 0
fi

# Step 1: Build the container image
echo ""
echo "Step 1: Building container image..."
cd "$(dirname "$0")"

gcloud builds submit \
    --tag "gcr.io/$PROJECT_ID/$SERVICE_NAME:v0.3.1" \
    --timeout=600s

# Step 2: Deploy to Cloud Run with protection settings
echo ""
echo "Step 2: Deploying to Cloud Run with EDoS protection..."

gcloud run deploy $SERVICE_NAME \
    --image "gcr.io/$PROJECT_ID/$SERVICE_NAME:v0.3.1" \
    --region $REGION \
    --platform managed \
    --allow-unauthenticated \
    --max-instances $MAX_INSTANCES \
    --min-instances $MIN_INSTANCES \
    --concurrency $CONCURRENCY \
    --timeout ${TIMEOUT}s \
    --memory $MEMORY \
    --cpu $CPU \
    --set-env-vars "RATE_LIMIT_PER_IP=$RATE_LIMIT_PER_IP,RATE_LIMIT_GLOBAL=$RATE_LIMIT_GLOBAL,LLM_PROVIDER=gemini" \
    --port 8080

# Step 3: Get service URL
echo ""
echo "Step 3: Getting service URL..."
SERVICE_URL=$(gcloud run services describe $SERVICE_NAME --region $REGION --format="value(status.url)")

echo ""
echo "============================================================================"
echo "DEPLOYMENT COMPLETE!"
echo "============================================================================"
echo "Service URL:    $SERVICE_URL"
echo "Health Check:   $SERVICE_URL/health"
echo "MCP Endpoint:   $SERVICE_URL/mcp/"
echo "Setup Guide:    $SERVICE_URL/setup"
echo "============================================================================"
echo ""
echo "PROTECTION SETTINGS APPLIED:"
echo "  - Max Instances: $MAX_INSTANCES (hard cap)"
echo "  - Rate Limiting: $RATE_LIMIT_PER_IP req/min per IP"
echo "  - Global Limit:  $RATE_LIMIT_GLOBAL req/min per instance"
echo "  - Default LLM:   Gemini (FREE tier)"
echo "============================================================================"
echo ""
echo "ESTIMATED MONTHLY COST (worst case):"
echo "  - Normal usage:  ~\$5-10/month"
echo "  - Under attack:  ~\$20-30/month (capped by max instances)"
echo "============================================================================"
echo ""
echo "To test: curl $SERVICE_URL/health"
echo ""
