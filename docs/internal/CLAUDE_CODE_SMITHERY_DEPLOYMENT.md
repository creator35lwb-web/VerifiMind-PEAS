# Claude Code Execution Prompt: Smithery.ai Marketplace Deployment

## 🚨 CRITICAL: Alignment Protocol

**Before starting ANY work:**
1. ✅ Pull latest from GitHub: `git pull origin main`
2. ✅ Review this document completely
3. ✅ Confirm you have the latest changes from Manus AI

**After completing work:**
1. ✅ Commit all changes with descriptive message
2. ✅ Push to GitHub: `git push origin main`
3. ✅ Create session notes in `/iteration/` folder
4. ✅ Report back to Manus AI with summary

---

## 📋 Mission: Deploy VerifiMind PEAS to Smithery.ai Marketplace

### Objective
List VerifiMind PEAS MCP Server on Smithery.ai marketplace to gain exposure to 10,000+ users while keeping the GCP production server (verifimind.ysenseai.org) intact.

### Strategy
- **Primary Production**: GCP Cloud Run (verifimind.ysenseai.org) - UNCHANGED
- **Marketplace Listing**: Smithery.ai - NEW

---

## ✅ Pre-Deployment Checklist

### Files Already Prepared by Manus AI:

1. **`smithery.yaml`** ✅ Updated
   - Runtime: container
   - Config schema with Gemini, OpenAI, Anthropic options
   - Example configuration
   - Build settings

2. **`http_server.py`** ✅ Updated
   - CORS middleware added for Smithery browser clients
   - Version bumped to 0.2.1
   - Enhanced endpoint documentation

3. **`Dockerfile`** ✅ Already compatible
   - Python 3.12 with uv
   - Health check endpoint
   - PORT environment variable support

---

## 🚀 Deployment Steps

### Step 1: Verify Local Build (Optional but Recommended)

```bash
cd /path/to/VerifiMind-PEAS/mcp-server

# Build Docker image locally
docker build -t verifimind-mcp-server:test .

# Test locally (Smithery uses PORT=8081)
docker run -p 8081:8081 -e PORT=8081 verifimind-mcp-server:test

# In another terminal, test endpoints
curl http://localhost:8081/health
curl http://localhost:8081/.well-known/mcp-config
```

### Step 2: Push Changes to GitHub

```bash
cd /path/to/VerifiMind-PEAS

# Ensure latest
git pull origin main

# Stage changes
git add -A

# Commit with descriptive message
git commit -m "feat(mcp): Prepare Smithery.ai marketplace deployment

- Update smithery.yaml with Gemini provider and improved config schema
- Add CORS middleware to http_server.py for browser clients
- Bump version to 0.2.1
- Add comprehensive deployment documentation

Prepared by: Manus AI (CTO Agent)
Executed by: Claude Code (DevOps Agent)"

# Push to GitHub
git push origin main
```

### Step 3: Connect to Smithery.ai

1. **Go to**: https://smithery.ai/new
2. **Sign in** with GitHub
3. **Select repository**: `creator35lwb-web/VerifiMind-PEAS`
4. **Select path**: `/mcp-server` (where smithery.yaml is located)
5. **Click**: "Deploy"

### Step 4: Verify Deployment

After Smithery builds and deploys:

1. **Check server page**: https://smithery.ai/server/@creator35lwb-web/VerifiMind-PEAS
2. **Test health endpoint**: `curl https://server.smithery.ai/verifimind-genesis/health`
3. **Test MCP config**: `curl https://server.smithery.ai/verifimind-genesis/.well-known/mcp-config`

### Step 5: Update Server Metadata on Smithery

On the Smithery server page, update:
- **Title**: VerifiMind PEAS - Multi-Model AI Validation
- **Description**: 
  ```
  Multi-Model AI Validation System powered by the Genesis Prompt Engineering Methodology.
  
  🎯 Features:
  - RefleXion Trinity: X Agent (Innovation), Z Agent (Ethics), CS Agent (Security)
  - 4 Tools: consult_agent_x, consult_agent_z, consult_agent_cs, run_full_trinity
  - 4 Resources: Genesis Master Prompt, Validation History, Project Info
  - Cost: ~$0.003 per validation (Gemini FREE tier available)
  
  📚 Documentation: https://github.com/creator35lwb-web/VerifiMind-PEAS
  📄 White Paper: https://doi.org/10.5281/zenodo.17645665
  🌐 Landing Page: https://verifimind.manus.space
  ```
- **Tags**: `ai-validation`, `multi-model`, `gemini`, `claude`, `mcp`, `genesis-methodology`

---

## 📊 Expected Outcomes

After successful deployment:

| Platform | URL | Purpose |
|----------|-----|---------|
| GCP Production | https://verifimind.ysenseai.org | Primary production server |
| Smithery Marketplace | https://server.smithery.ai/verifimind-genesis | Marketplace exposure |
| Landing Page | https://verifimind.manus.space | Marketing & documentation |
| GitHub | https://github.com/creator35lwb-web/VerifiMind-PEAS | Source code |

---

## 🔄 Post-Deployment: Report to Manus AI

**Create session notes at**: `/iteration/smithery-deployment-session-notes.md`

Include:
1. ✅ Deployment status (success/failure)
2. ✅ Smithery server URL
3. ✅ Any issues encountered
4. ✅ Test results
5. ✅ Next steps or recommendations

**Format for Manus AI handoff:**
```markdown
## Claude Code → Manus AI Handoff

**Session**: Smithery Deployment
**Date**: [DATE]
**Status**: [SUCCESS/FAILED/PARTIAL]

### Completed Tasks
- [ ] Task 1
- [ ] Task 2

### Issues Encountered
- Issue 1: Description + Resolution

### Test Results
- Health endpoint: [PASS/FAIL]
- MCP config: [PASS/FAIL]
- Tool execution: [PASS/FAIL]

### Smithery URLs
- Server page: [URL]
- API endpoint: [URL]

### Recommendations
- Recommendation 1
- Recommendation 2
```

---

## ⚠️ Troubleshooting

### Build Fails
- Check Dockerfile syntax
- Verify all dependencies in pyproject.toml
- Check smithery.yaml format

### CORS Errors
- Verify CORSMiddleware is added to http_server.py
- Check allow_origins includes "*"
- Verify expose_headers includes MCP headers

### Health Check Fails
- Verify /health endpoint returns 200
- Check PORT environment variable is used
- Verify uvicorn is running correctly

---

## 📞 Support

- **Manus AI (CTO)**: Strategic decisions, alignment
- **Claude Code (DevOps)**: Execution, deployment
- **GitHub Issues**: https://github.com/creator35lwb-web/VerifiMind-PEAS/issues
- **Smithery Discord**: https://discord.gg/Afd38S5p9A

---

**Remember**: After completing this deployment, report back to Manus AI for alignment verification!
