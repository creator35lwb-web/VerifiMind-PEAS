# Claude Code Implementation Guide: Alibaba Cloud Migration

**From:** Manus AI (T), CTO - Team YSenseAI  
**To:** Claude Code  
**Date:** January 28, 2026  
**Priority:** Preparation (Execute when Alibaba Cloud credits are confirmed)  
**GitHub Bridge:** `creator35lwb-web/VerifiMind-PEAS`

---

## Executive Summary

This guide prepares the VerifiMind-PEAS MCP server for potential migration from Google Cloud Platform (GCP) Cloud Run to Alibaba Cloud Serverless App Engine (SAE). The migration is contingent on receiving Alibaba Cloud free credits.

**Key Objective:** Zero user disruption during migration by keeping the same domain (verifimind.ysenseai.org).

---

## Table of Contents

1. [Current Infrastructure](#current-infrastructure)
2. [Target Infrastructure](#target-infrastructure)
3. [Cost Comparison](#cost-comparison)
4. [Pre-Migration Checklist](#pre-migration-checklist)
5. [Migration Steps](#migration-steps)
6. [Rollback Plan](#rollback-plan)
7. [Post-Migration Verification](#post-migration-verification)
8. [Alignment Protocol](#alignment-protocol)

---

## Current Infrastructure

| Component | Current Value |
|-----------|---------------|
| **Platform** | Google Cloud Platform (GCP) |
| **Service** | Cloud Run |
| **Region** | us-central1 |
| **URL** | https://verifimind-mcp-server-690976799907.us-central1.run.app |
| **Custom Domain** | verifimind.ysenseai.org |
| **Container** | Docker image (Node.js) |
| **Specs** | 1 vCPU, 512MB-2GB RAM |
| **Monthly Cost** | ~RM 50-70 (~USD 11-15) |

---

## Target Infrastructure

| Component | Target Value |
|-----------|--------------|
| **Platform** | Alibaba Cloud |
| **Service** | Serverless App Engine (SAE) |
| **Region** | Singapore (ap-southeast-1) or Hong Kong (cn-hongkong) |
| **Custom Domain** | verifimind.ysenseai.org (same) |
| **Container** | Same Docker image |
| **Specs** | 1 vCPU, 2GB RAM (Standard Edition) |

---

## Cost Comparison

### Monthly Cost Estimate (1 vCPU, 2GB RAM, 24/7)

| Platform | Region | Monthly Cost (USD) | Monthly Cost (RM) |
|----------|--------|-------------------|-------------------|
| GCP Cloud Run | us-central1 | ~$11-15 | ~RM 50-70 |
| Alibaba SAE | Singapore | ~$42 | ~RM 189 |
| Alibaba SAE | China (Shanghai) | ~$27 | ~RM 121 |

### With Free Credits

If Alibaba Cloud provides free credits (typically $300-$450 for new users):
- **$300 credits** = ~7 months free (Singapore) or ~11 months free (China)
- **$450 credits** = ~10 months free (Singapore) or ~16 months free (China)

### Recommendation

**Stay on GCP unless:**
1. Alibaba Cloud credits cover 6+ months of usage
2. You need better Asia-Pacific latency for users
3. GCP costs increase significantly

---

## Pre-Migration Checklist

Before starting migration, ensure:

```bash
# 1. Verify Docker image is portable
docker pull gcr.io/ysense-platform-v4-1/verifimind-mcp-server:latest
docker run -p 8080:8080 gcr.io/ysense-platform-v4-1/verifimind-mcp-server:latest

# 2. List all environment variables
gcloud run services describe verifimind-mcp-server --region=us-central1 --format='yaml(spec.template.spec.containers[0].env)'

# 3. Document current DNS settings
dig verifimind.ysenseai.org

# 4. Backup current configuration
gcloud run services describe verifimind-mcp-server --region=us-central1 --format=yaml > backup-cloudrun-config.yaml
```

### Required Environment Variables

Document these from GCP before migration:

| Variable | Description | Required |
|----------|-------------|----------|
| `PORT` | Server port (usually 8080) | Yes |
| `NODE_ENV` | Environment (production) | Yes |
| `GEMINI_API_KEY` | For AI features (if used) | Optional |
| `ANTHROPIC_API_KEY` | For AI features (if used) | Optional |
| Other custom vars | Check current deployment | Varies |

---

## Migration Steps

### Phase 1: Alibaba Cloud Setup

```bash
# 1. Install Alibaba Cloud CLI
curl -fsSL https://aliyuncli.alicdn.com/aliyun-cli-linux-latest-amd64.tgz | tar xzf -
sudo mv aliyun /usr/local/bin/

# 2. Configure CLI with credentials
aliyun configure
# Enter: Access Key ID, Access Key Secret, Region (ap-southeast-1)

# 3. Verify authentication
aliyun ecs DescribeRegions
```

### Phase 2: Container Registry Setup

```bash
# 1. Create Alibaba Container Registry namespace
aliyun cr CreateNamespace --Namespace verifimind

# 2. Login to Alibaba Container Registry
docker login --username=<your-username> registry.ap-southeast-1.aliyuncs.com

# 3. Tag and push the Docker image
docker tag gcr.io/ysense-platform-v4-1/verifimind-mcp-server:latest \
  registry.ap-southeast-1.aliyuncs.com/verifimind/mcp-server:latest

docker push registry.ap-southeast-1.aliyuncs.com/verifimind/mcp-server:latest
```

### Phase 3: SAE Application Deployment

```bash
# Option A: Using Alibaba Cloud Console (Recommended for first deployment)
# 1. Go to: https://sae.console.aliyun.com
# 2. Create Application
# 3. Select: Image deployment
# 4. Configure:
#    - Application Name: verifimind-mcp-server
#    - Namespace: Create new or use default
#    - vCPU: 1 core
#    - Memory: 2 GB
#    - Image: registry.ap-southeast-1.aliyuncs.com/verifimind/mcp-server:latest
#    - Port: 8080
#    - Min instances: 0 (scale to zero)
#    - Max instances: 2

# Option B: Using CLI (after first deployment)
aliyun sae CreateApplication \
  --AppName verifimind-mcp-server \
  --NamespaceId <namespace-id> \
  --PackageType Image \
  --ImageUrl registry.ap-southeast-1.aliyuncs.com/verifimind/mcp-server:latest \
  --Cpu 1000 \
  --Memory 2048 \
  --Replicas 1
```

### Phase 4: Custom Domain Configuration

```bash
# 1. Get SAE application's default URL
# Format: <app-id>.<region>.sae.run

# 2. Configure custom domain in SAE console
# Go to: Application > Network > Custom Domain
# Add: verifimind.ysenseai.org

# 3. Update DNS records (at your domain registrar)
# Change CNAME from GCP Cloud Run to SAE:
# verifimind.ysenseai.org -> <app-id>.ap-southeast-1.sae.run

# 4. Wait for DNS propagation (5-30 minutes)
dig verifimind.ysenseai.org
```

### Phase 5: SSL Certificate

SAE provides automatic SSL certificates for custom domains:

```bash
# In SAE Console:
# 1. Go to Application > Network > Custom Domain
# 2. Enable HTTPS
# 3. Select "Auto-generated certificate" or upload your own
```

---

## Rollback Plan

If migration fails, rollback within 5 minutes:

```bash
# 1. Revert DNS to GCP Cloud Run
# Change CNAME back to:
# verifimind.ysenseai.org -> verifimind-mcp-server-690976799907.us-central1.run.app

# 2. Verify GCP service is still running
gcloud run services describe verifimind-mcp-server --region=us-central1

# 3. If GCP service was deleted, redeploy from backup
gcloud run services replace backup-cloudrun-config.yaml --region=us-central1
```

**Important:** Keep GCP deployment running for 48 hours after migration to ensure rollback capability.

---

## Post-Migration Verification

### Health Checks

```bash
# 1. Check HTTP response
curl -I https://verifimind.ysenseai.org

# 2. Test MCP endpoint
curl -X POST https://verifimind.ysenseai.org/mcp/ \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","method":"tools/list","id":1}'

# 3. Check SSL certificate
openssl s_client -connect verifimind.ysenseai.org:443 -servername verifimind.ysenseai.org

# 4. Verify from multiple regions
# Use: https://check-host.net/check-http?host=verifimind.ysenseai.org
```

### Update Documentation

After successful migration, update:

1. `README.md` - Update hosting information
2. `MCP_SETUP_GUIDE.md` - Verify URLs still work
3. MCP Registry listing - If URL changed

---

## Alignment Protocol

### Report Back to Manus AI (T)

After completing each phase, create a commit with status:

```bash
git add .
git commit -m "Migration Phase X: [Status] - [Details]"
git push origin main
```

### Status Codes

| Code | Meaning |
|------|---------|
| ✅ COMPLETE | Phase finished successfully |
| ⚠️ PARTIAL | Phase finished with warnings |
| ❌ FAILED | Phase failed, rollback initiated |
| 🔄 IN_PROGRESS | Phase currently executing |

### Communication Bridge

All migration status updates should be committed to:
- `iteration/migration-log-YYYY-MM-DD.md`

---

## Decision Matrix

| Condition | Action |
|-----------|--------|
| Credits ≥ $300 | Proceed with migration |
| Credits < $300 | Stay on GCP |
| Migration fails | Rollback to GCP |
| Latency worse on SAE | Stay on GCP |
| Cost higher on SAE (after credits) | Migrate back to GCP |

---

## Files to Create/Update

| File | Action | Purpose |
|------|--------|---------|
| `scripts/migrate-to-alibaba.sh` | Create | Automated migration script |
| `scripts/rollback-to-gcp.sh` | Create | Rollback script |
| `docs/ALIBABA_DEPLOYMENT.md` | Create | SAE-specific documentation |
| `README.md` | Update | Add Alibaba Cloud hosting info |

---

## Success Criteria

- [ ] SAE application deployed and running
- [ ] Custom domain (verifimind.ysenseai.org) resolving to SAE
- [ ] SSL certificate active
- [ ] All MCP endpoints responding correctly
- [ ] Latency ≤ GCP latency
- [ ] No user-reported issues for 48 hours
- [ ] GCP deployment safely decommissioned

---

**End of Implementation Guide**

*This guide is a preparation document. Execute only when Alibaba Cloud credits are confirmed and approved by the user.*
