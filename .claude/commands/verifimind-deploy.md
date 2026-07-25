# /verifimind-deploy

Deploy VerifiMind-PEAS to GCP Cloud Run.

## Usage

```
/verifimind-deploy [version]
```

## Workflow

1. **Pre-flight checks:**
   - Verify GCP authentication
   - Check current server health
   - Confirm version number

2. **Build container** (B-94-1: every deploy path bakes the immutable build
   identity into the image — `--tag` alone cannot pass `--build-arg`, hence
   the config file; NEVER set `BUILD_COMMIT_SHA` at the service level):
   ```bash
   cd mcp-server
   gcloud builds submit \
     --config=cloudbuild-image.yaml \
     --substitutions=_IMAGE_TAG=gcr.io/YOUR_GCP_PROJECT_ID/verifimind-mcp-server:v{VERSION},_COMMIT_SHA=$(git rev-parse HEAD)
   ```

3. **Deploy to Cloud Run:**
   ```bash
   gcloud run deploy verifimind-mcp-server \
     --image gcr.io/YOUR_GCP_PROJECT_ID/verifimind-mcp-server:v{VERSION} \
     --region us-central1 \
     --max-instances 3 \
     --min-instances 0 \
     --concurrency 10 \
     --timeout 60s \
     --memory 512Mi \
     --cpu 1 \
     --allow-unauthenticated \
     --port 8080
   ```

4. **Post-deployment:**
   - Verify health check
   - Update SERVER_STATUS.md
   - Update http_server.py version
   - Commit and push changes

5. **Update PRIVATE repo:**
   - Create alignment issue for CTO
   - Sync deployment status

## Example

```
/verifimind-deploy 0.3.5
```
