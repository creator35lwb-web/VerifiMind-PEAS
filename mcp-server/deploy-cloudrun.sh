#!/bin/bash
# ============================================================================
# VerifiMind-PEAS Cloud Run Deployment Script
# v0.5.6 - With EDoS Protection + Firestore EA Registration
# ============================================================================
#
# This script deploys the MCP server to Google Cloud Run with:
# - Hard-capped auto-scaling (max 3 instances)
# - Rate limiting enabled
# - FREE tier Gemini as default
# - Firestore EA registration (FIRESTORE_PROJECT_ID auto-set)
# - Cost-optimized settings
#
# Prerequisites:
#   gcloud auth login
#   gcloud config set project ysense-platform-v4-1
#
# Usage:
#   chmod +x deploy-cloudrun.sh
#   ./deploy-cloudrun.sh
#
# ============================================================================

set -e  # Exit on error

# ── Configuration ────────────────────────────────────────────────────────────
SERVICE_NAME="verifimind-mcp-server"
REGION="us-central1"
PROJECT_ID=$(gcloud config get-value project 2>/dev/null)

# Read SERVER_VERSION from source (single source of truth)
SERVER_VERSION=$(python3 -c "
import sys; sys.path.insert(0, 'src')
from verifimind_mcp.server import SERVER_VERSION
print(SERVER_VERSION)
" 2>/dev/null || echo "unknown")

IMAGE_TAG="gcr.io/$PROJECT_ID/$SERVICE_NAME:v$SERVER_VERSION"

# ── Protection settings ───────────────────────────────────────────────────────
MAX_INSTANCES=3           # Hard cap - prevents runaway scaling
MIN_INSTANCES=0           # Scale to zero when idle (cost savings)
CONCURRENCY=10            # Max concurrent requests per instance
TIMEOUT=600               # Request timeout in seconds — 600s for Anthropic BYOK Trinity (3-agent chain ~200-300s)
MEMORY="512Mi"
CPU="1"

# ── Rate limiting ─────────────────────────────────────────────────────────────
RATE_LIMIT_PER_IP=10
RATE_LIMIT_GLOBAL=100

# ── Preflight checks ──────────────────────────────────────────────────────────
if [[ -z "$PROJECT_ID" ]]; then
    echo "ERROR: No GCP project set. Run: gcloud config set project ysense-platform-v4-1"
    exit 1
fi

echo "============================================================================"
echo "VerifiMind-PEAS Cloud Run Deployment"
echo "============================================================================"
echo "Project:        $PROJECT_ID"
echo "Service:        $SERVICE_NAME"
echo "Region:         $REGION"
echo "Version:        v$SERVER_VERSION"
echo "Image:          $IMAGE_TAG"
echo "Max Instances:  $MAX_INSTANCES (HARD CAP - EDoS Protection)"
echo "Memory:         $MEMORY"
echo "Firestore:      $PROJECT_ID (same GCP project)"
echo "============================================================================"

# ── Confirm deployment ────────────────────────────────────────────────────────
read -p "Deploy with these settings? (y/N): " confirm
if [[ $confirm != [yY] ]]; then
    echo "Deployment cancelled."
    exit 0
fi

# ── Step 1: Build the container image ────────────────────────────────────────
echo ""
echo "Step 1: Building container image..."
cd "$(dirname "$0")"

gcloud builds submit \
    --tag "$IMAGE_TAG" \
    --timeout=600s

# ── Step 2: Deploy to Cloud Run ───────────────────────────────────────────────
echo ""
echo "Step 2: Deploying to Cloud Run..."

# NOTE: --update-env-vars preserves existing env vars (API keys set separately).
# Only the listed vars are updated; GEMINI_API_KEY, GROQ_API_KEY etc. are untouched.
gcloud run deploy $SERVICE_NAME \
    --image "$IMAGE_TAG" \
    --region $REGION \
    --platform managed \
    --allow-unauthenticated \
    --max-instances $MAX_INSTANCES \
    --min-instances $MIN_INSTANCES \
    --concurrency $CONCURRENCY \
    --timeout ${TIMEOUT}s \
    --memory $MEMORY \
    --cpu $CPU \
    --update-env-vars "RATE_LIMIT_PER_IP=$RATE_LIMIT_PER_IP,RATE_LIMIT_GLOBAL=$RATE_LIMIT_GLOBAL,LLM_PROVIDER=gemini,FIRESTORE_PROJECT_ID=$PROJECT_ID" \
    --port 8080

# ── Step 3: Post-deploy verification ─────────────────────────────────────────
echo ""
echo "Step 3: Verifying deployment..."
SERVICE_URL=$(gcloud run services describe $SERVICE_NAME --region $REGION --format="value(status.url)")

sleep 5  # Allow cold start

HEALTH=$(curl -sf "$SERVICE_URL/health" 2>/dev/null || echo '{"error":"unreachable"}')
echo "Health response: $HEALTH"

DEPLOYED_VERSION=$(echo "$HEALTH" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('version','unknown'))" 2>/dev/null || echo "parse error")

echo ""
echo "============================================================================"
if [[ "$DEPLOYED_VERSION" == "$SERVER_VERSION" ]]; then
    echo "DEPLOYMENT SUCCESSFUL — v$SERVER_VERSION is live"
else
    echo "WARNING: Expected v$SERVER_VERSION but got '$DEPLOYED_VERSION' — check logs"
fi
echo "============================================================================"
echo "Service URL:        $SERVICE_URL"
echo "Custom Domain:      https://verifimind.ysenseai.org"
echo "Health Check:       $SERVICE_URL/health"
echo "MCP Endpoint:       $SERVICE_URL/mcp/"
echo "EA Registration:    $SERVICE_URL/early-adopters/register"
echo "Privacy Policy:     $SERVICE_URL/privacy"
echo "Terms:              $SERVICE_URL/terms"
echo "============================================================================"
echo ""
echo "PROTECTION SETTINGS:"
echo "  Max Instances:    $MAX_INSTANCES (hard cap)"
echo "  Rate Limiting:    $RATE_LIMIT_PER_IP req/min per IP"
echo "  Global Limit:     $RATE_LIMIT_GLOBAL req/min per instance"
echo "  Default LLM:      Gemini (FREE tier)"
echo "  Firestore:        $PROJECT_ID"
echo "============================================================================"
echo ""
echo "ESTIMATED MONTHLY COST (worst case):"
echo "  Normal usage:     ~\$5-10/month"
echo "  Under attack:     ~\$20-30/month (capped by max instances)"
echo "  Firestore (EA):   FREE tier covers first ~500 EA records"
echo "============================================================================"
echo ""
echo "GCP Console (verify deployment):"
echo "  Cloud Run:   https://console.cloud.google.com/run/detail/$REGION/$SERVICE_NAME/revisions?project=$PROJECT_ID"
echo "  Logs:        https://console.cloud.google.com/run/detail/$REGION/$SERVICE_NAME/logs?project=$PROJECT_ID"
echo "  Firestore:   https://console.cloud.google.com/firestore/databases/-default-/data/panel?project=$PROJECT_ID"
echo ""
