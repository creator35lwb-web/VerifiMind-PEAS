# 🚀 Claude Code Deployment Prompt: VerifiMind PEAS MCP Server v2.0

**Date**: December 23, 2025  
**From**: Manus AI (CTO) + Alton Lee (Project Owner)  
**To**: Claude Code (DevOps Agent)  
**Priority**: HIGH  
**Status**: Ready for Execution

---

## 📋 Mission Brief

**Objective**: Deploy VerifiMind PEAS MCP Server v2.0 with complete Gemini integration to Google Cloud Run.

**Context**: Manus AI has completed the following code changes (already committed to GitHub):
- ✅ Added GeminiProvider to provider registry
- ✅ Updated server config to support Gemini API key
- ✅ Added google-generativeai dependency
- ✅ All 4 tools (X, Z, CS, Trinity) now support Gemini
- ✅ Local tests passed (4/4)

**Your Task**: Deploy these changes to production at https://verifimind.ysenseai.org

---

## 🔄 Pre-Deployment Checklist

### Step 1: Sync with GitHub (MANDATORY)

```bash
# Pull latest changes from Manus AI
cd /path/to/VerifiMind-PEAS
git fetch origin
git pull origin main

# Verify latest commits
git log --oneline -5
# Expected: c344c8f - docs: Add comprehensive alignment report v2.0
#           c44e353 - feat: Complete Gemini integration for MCP Server v2.0
```

### Step 2: Verify Code Changes

**Check these files were updated:**

1. **`mcp-server/src/verifimind_mcp/llm/provider.py`**
   - Line ~405: Should include `"gemini": GeminiProvider` in `_PROVIDERS`

2. **`mcp-server/src/verifimind_mcp/server.py`**
   - Line ~51-54: Should include `gemini_api_key` field in `VerifiMindConfig`
   - Lines ~310, ~422, ~531, ~630: Should include Gemini provider instantiation

3. **`mcp-server/pyproject.toml`**
   - Line ~14: Should include `"google-generativeai>=0.3.0"`

---

## 🐳 Deployment Steps

### Step 3: Build Docker Image

```bash
cd /path/to/VerifiMind-PEAS/mcp-server

# Build with version tag
docker build -t verifimind-mcp-server:v2.0 .

# Verify build succeeded
docker images | grep verifimind-mcp-server
```

### Step 4: Tag and Push to Google Container Registry

```bash
# Tag for GCR
docker tag verifimind-mcp-server:v2.0 gcr.io/YOUR_GCP_PROJECT_ID/verifimind-mcp-server:v2.0
docker tag verifimind-mcp-server:v2.0 gcr.io/YOUR_GCP_PROJECT_ID/verifimind-mcp-server:latest

# Push to GCR
docker push gcr.io/YOUR_GCP_PROJECT_ID/verifimind-mcp-server:v2.0
docker push gcr.io/YOUR_GCP_PROJECT_ID/verifimind-mcp-server:latest
```

### Step 5: Deploy to Cloud Run

```bash
# Deploy with environment variables
gcloud run deploy verifimind-mcp-server \
  --image gcr.io/YOUR_GCP_PROJECT_ID/verifimind-mcp-server:latest \
  --region us-central1 \
  --platform managed \
  --allow-unauthenticated \
  --port 8080 \
  --memory 512Mi \
  --cpu 1 \
  --min-instances 0 \
  --max-instances 10 \
  --set-env-vars "VERIFIMIND_LLM_PROVIDER=gemini"
```

### Step 6: Set Environment Variables (IMPORTANT!)

**Via Google Cloud Console:**
1. Go to: https://console.cloud.google.com/run/detail/us-central1/verifimind-mcp-server/variables
2. Click "EDIT & DEPLOY NEW REVISION"
3. Scroll to "Variables & Secrets"
4. Add/Update these environment variables:

| Variable | Value | Notes |
|----------|-------|-------|
| `GEMINI_API_KEY` | `<your-gemini-api-key>` | **REQUIRED** for X Agent |
| `ANTHROPIC_API_KEY` | `<your-anthropic-api-key>` | **REQUIRED** for Z & CS Agents |
| `OPENAI_API_KEY` | `<your-openai-api-key>` | Optional backup |
| `VERIFIMIND_LLM_PROVIDER` | `gemini` | Default provider |
| `PORT` | `8080` | Server port |

5. Click "DEPLOY"

**Via gcloud CLI:**
```bash
gcloud run services update verifimind-mcp-server \
  --region us-central1 \
  --set-env-vars "GEMINI_API_KEY=<your-key>,ANTHROPIC_API_KEY=<your-key>"
```

---

## ✅ Post-Deployment Verification

### Step 7: Test Endpoints

```bash
# Test health endpoint
curl https://verifimind.ysenseai.org/health
# Expected: {"status": "healthy", ...}

# Test MCP config endpoint
curl https://verifimind.ysenseai.org/.well-known/mcp-config
# Expected: JSON with server configuration

# Test root endpoint
curl https://verifimind.ysenseai.org/
# Expected: Server info JSON
```

### Step 8: Verify Gemini Integration

**Option A: Test via MCP Client**
```json
{
  "mcpServers": {
    "verifimind-genesis": {
      "url": "https://verifimind.ysenseai.org/mcp",
      "transport": "http-sse",
      "config": {
        "llm_provider": "gemini",
        "gemini_api_key": "YOUR_GEMINI_API_KEY"
      }
    }
  }
}
```

**Option B: Test via curl (if endpoint supports it)**
```bash
# Test X Agent consultation
curl -X POST https://verifimind.ysenseai.org/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "method": "tools/call",
    "params": {
      "name": "consult_agent_x",
      "arguments": {
        "concept_name": "Test Concept",
        "description": "A test concept for verification"
      }
    }
  }'
```

### Step 9: Check Cloud Run Logs

```bash
# View recent logs
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=verifimind-mcp-server" \
  --limit 50 \
  --format "table(timestamp,textPayload)"
```

**Look for:**
- ✅ Server started successfully
- ✅ No import errors
- ✅ Gemini provider loaded
- ❌ Any error messages

---

## 📊 Expected Results

### Health Check Response
```json
{
  "status": "healthy",
  "version": "0.2.0",
  "server": "VerifiMind Genesis MCP Server",
  "timestamp": "2025-12-23T...",
  "endpoints": {
    "mcp": "/mcp",
    "health": "/health",
    "config": "/.well-known/mcp-config"
  }
}
```

### MCP Config Response
```json
{
  "name": "verifimind-genesis",
  "version": "0.2.0",
  "description": "VerifiMind-PEAS Genesis Methodology MCP Server",
  "tools": [
    "consult_agent_x",
    "consult_agent_z",
    "consult_agent_cs",
    "run_full_trinity"
  ],
  "resources": [
    "genesis://config/master_prompt",
    "genesis://history/latest",
    "genesis://history/all",
    "genesis://state/project_info"
  ]
}
```

---

## 🔧 Troubleshooting Guide

### Issue 1: Docker Build Fails
**Symptom**: `pip install` fails during build
**Solution**: Check `pyproject.toml` for syntax errors
```bash
# Validate pyproject.toml
python3 -c "import toml; toml.load('pyproject.toml')"
```

### Issue 2: Import Error for google-generativeai
**Symptom**: `ModuleNotFoundError: No module named 'google.generativeai'`
**Solution**: Verify dependency is in pyproject.toml
```bash
grep "google-generativeai" pyproject.toml
# Should show: "google-generativeai>=0.3.0"
```

### Issue 3: Gemini API Key Not Working
**Symptom**: `Invalid API key` error
**Solution**: 
1. Verify key in Cloud Run environment variables
2. Test key directly:
```bash
curl "https://generativelanguage.googleapis.com/v1beta/models?key=YOUR_KEY"
```

### Issue 4: Server Returns 500 Error
**Symptom**: Internal server error on MCP calls
**Solution**: Check Cloud Run logs for stack trace
```bash
gcloud logging read "resource.type=cloud_run_revision" --limit 20
```

### Issue 5: Health Check Fails
**Symptom**: `/health` returns error or timeout
**Solution**: 
1. Check if container started
2. Verify PORT environment variable is 8080
3. Check memory allocation (increase if needed)

---

## 📝 Handoff Notes

### What Manus AI Completed
- ✅ GeminiProvider registered in provider registry
- ✅ Server config supports Gemini API key
- ✅ All 4 tools support Gemini instantiation
- ✅ google-generativeai dependency added
- ✅ Local tests passed (4/4)
- ✅ Comprehensive documentation created
- ✅ All changes committed to GitHub

### What Claude Code Needs To Do
- [ ] Pull latest from GitHub
- [ ] Build Docker image v2.0
- [ ] Push to Google Container Registry
- [ ] Deploy to Cloud Run
- [ ] Set environment variables (GEMINI_API_KEY, ANTHROPIC_API_KEY)
- [ ] Verify all endpoints working
- [ ] Test Gemini integration
- [ ] Document deployment in session notes

### Files Changed by Manus AI
```
M  mcp-server/pyproject.toml
M  mcp-server/src/verifimind_mcp/llm/provider.py
M  mcp-server/src/verifimind_mcp/server.py
A  mcp-server/DEPLOYMENT_CHECKLIST_V2.0.md
A  ALIGNMENT_REPORT_V2.0.md
A  MULTI_AGENT_COLLABORATION_PROTOCOL.md
```

### GitHub Commits
```
c344c8f - docs: Add comprehensive alignment report v2.0
c44e353 - feat: Complete Gemini integration for MCP Server v2.0
```

---

## 🎯 Success Criteria

### Deployment is successful when:
- [ ] Health endpoint returns `{"status": "healthy"}`
- [ ] MCP config endpoint returns valid JSON
- [ ] All 4 tools are listed in MCP config
- [ ] No errors in Cloud Run logs
- [ ] Gemini API key is set and working
- [ ] X Agent can be invoked successfully

### Performance Targets
- **Latency**: < 20 seconds per validation
- **Success Rate**: > 95%
- **Uptime**: > 99.5%

---

## 📞 Support

### If Issues Arise
1. Check Cloud Run logs first
2. Verify environment variables
3. Test endpoints individually
4. Document issue in session notes
5. Coordinate with Manus AI if code changes needed

### Contact
- **Project Owner**: Alton Lee
- **GitHub**: https://github.com/creator35lwb-web/VerifiMind-PEAS
- **Live Server**: https://verifimind.ysenseai.org

---

## ✅ Acknowledgment

By executing this deployment, Claude Code confirms:
- [ ] Read and understood this prompt
- [ ] Pulled latest from GitHub
- [ ] Following Multi-Agent Collaboration Protocol
- [ ] Will document deployment in session notes

---

**Deployment Prompt Version**: 1.0  
**Created By**: Manus AI (CTO)  
**Approved By**: Alton Lee (Project Owner)  
**Date**: December 23, 2025

---

## 🚀 GO FOR DEPLOYMENT!

**Status**: ✅ **READY FOR EXECUTION**

All code changes are committed and tested. Claude Code is cleared to proceed with deployment.

**Expected Outcome**: VerifiMind PEAS MCP Server v2.0 live at https://verifimind.ysenseai.org with full Gemini integration.

**Let's make it happen!** 🎉
