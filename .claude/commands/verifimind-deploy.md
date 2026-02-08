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

2. **Build container:**
   ```bash
   cd mcp-server
   gcloud builds submit --tag gcr.io/YOUR_GCP_PROJECT_ID/verifimind-mcp-server:v{VERSION}
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
