# VerifiMind-PEAS Project Instructions for Claude Code

**CRITICAL: Read this file completely before starting any work.**

---

## Project Overview

VerifiMind-PEAS is a multi-model AI validation framework with the X-Z-CS RefleXion Trinity.

**Current Version:** v0.3.4
**Status:** OPERATIONAL
**Server:** https://verifimind.ysenseai.org

---

## MANDATORY: Dual-Repo Protocol

This project uses a **Dual-Repo Protocol** for development. You MUST follow this protocol strictly.

### Repository Structure

| Repository | Visibility | Purpose | When to Use |
|------------|------------|---------|-------------|
| **VerifiMind-PEAS** | PUBLIC | Stable releases, public docs | Final approved changes only |
| **verifimind-genesis-mcp** | PRIVATE | Internal development, CTO comms | All development work |

### Protocol Rules

1. **All development work happens in PRIVATE repo first**
2. **Create alignment issue for CTO (Manus AI) before major changes**
3. **Only sync to PUBLIC repo after CTO approval**
4. **Never commit internal discussions to PUBLIC repo**

### Full Protocol Document

Read: `iteration/Dual-Repo-Protocol-v1.0.md`

---

## Session Start Checklist

When starting a new session, ALWAYS:

1. [ ] Read this CLAUDE.md file
2. [ ] Check SERVER_STATUS.md for current deployment status
3. [ ] Check CHANGELOG.md for recent changes
4. [ ] Check GitHub issues in PRIVATE repo for pending CTO reviews
5. [ ] Read latest session handoff in `iteration/Session_Handoff_*.md`

---

## Communication Protocol

### Claude Code → Manus AI (CTO)

**Location:** PRIVATE repo (verifimind-genesis-mcp)
**Method:** GitHub Issues with label `cto-alignment`

**Template:**
```markdown
# Alignment Update for Manus AI (CTO)

**Date:** {date}
**From:** Claude Code
**Version:** {version}

## Summary
{summary}

## Changes Implemented
- {changes}

## Awaiting
- [ ] CTO Review
- [ ] CTO Approval
```

### When to Create Alignment Issues

- New feature implementation
- Version deployment
- Architecture changes
- Bug fixes affecting production
- Protocol changes

---

## Key Files

| File | Purpose | Update When |
|------|---------|-------------|
| `CHANGELOG.md` | Public changelog | After releases |
| `SERVER_STATUS.md` | Deployment status | After deployments |
| `iteration/Dual-Repo-Protocol-v1.0.md` | Workflow protocol | Protocol changes |
| `mcp-server/http_server.py` | Server version | Code changes |

---

## Development Workflow

```
1. Start work in PRIVATE repo
   ↓
2. Implement changes
   ↓
3. Create alignment issue (label: cto-alignment)
   ↓
4. Wait for CTO approval
   ↓
5. After approval: sync to PUBLIC repo
   ↓
6. Update CHANGELOG.md
   ↓
7. Deploy if needed
   ↓
8. Update SERVER_STATUS.md
```

---

## Session End Checklist

Before ending a session, ALWAYS:

1. [ ] Create session handoff document in `iteration/Session_Handoff_{date}.md`
2. [ ] Commit and push all changes
3. [ ] Update any pending alignment issues
4. [ ] Note any blockers or pending CTO reviews

### Session Handoff Template

Save to: `iteration/Session_Handoff_{YYYYMMDD}.md`

```markdown
# Session Handoff - {date}

## Work Completed
- {item 1}
- {item 2}

## Current State
- Server Version: {version}
- Deployment Status: {status}
- Pending CTO Reviews: {issues}

## Next Session Should
1. {action 1}
2. {action 2}

## Open Issues
- {blockers}

## Files Modified
- {files}
```

---

## GCP Deployment

**Project:** YOUR_GCP_PROJECT_ID
**Region:** us-central1
**Service:** verifimind-mcp-server

**Deploy Command:**
```bash
gcloud run deploy verifimind-mcp-server \
  --image gcr.io/YOUR_GCP_PROJECT_ID/verifimind-mcp-server:v{VERSION} \
  --region us-central1 \
  --max-instances 3 \
  --allow-unauthenticated
```

---

## Important Contacts

- **CTO (Manus AI):** Review via PRIVATE repo issues
- **Project Lead (Alton Lee):** Via GitHub discussions

---

## Existing Protocols Reference

1. **Dual-Repo Protocol:** `iteration/Dual-Repo-Protocol-v1.0.md`
2. **Communication Protocol:** GitHub Issues in PRIVATE repo
3. **Changelog Protocol:** `CHANGELOG.md` format
4. **Session Handoff:** `iteration/Session_Handoff_*.md`
5. **CTO Alignment:** `iteration/Claude_Code_Alignment_Summary_Jan29.md`

---

## Current Roadmap (from CTO)

| Version | Target | Focus | Status |
|---------|--------|-------|--------|
| v0.4.0 | Feb 2026 | Unified Prompt Templates | NEXT |
| v0.5.0 | Mar 2026 | Agent Skills | Planned |
| v0.6.0 | Apr-May 2026 | MCP App | Planned |
| v0.7.0 | Jun 2026 | Local Models | Planned |

**Reference:** `ROADMAP.md`, `iteration/Claude_Code_Alignment_Summary_Jan29.md`

---

## Custom Skills (Slash Commands)

The following custom skills are available for this project:

| Skill | Purpose | Usage |
|-------|---------|-------|
| `/verifimind-status` | Check server and repo status | `/verifimind-status` |
| `/verifimind-deploy` | Deploy to GCP Cloud Run | `/verifimind-deploy 0.4.0` |
| `/verifimind-align` | Create CTO alignment issue | `/verifimind-align 0.4.0 "Summary"` |
| `/verifimind-handoff` | Create session handoff | `/verifimind-handoff` |
| `/verifimind-sync` | Sync PRIVATE → PUBLIC | `/verifimind-sync files...` |
| `/verifimind-test` | Test Trinity validation | `/verifimind-test "Concept" "Desc"` |

**Location:** `.claude/commands/`

---

## Quick Reference Commands

```bash
# Check server health
curl https://verifimind.ysenseai.org/health

# Clone PRIVATE repo (for development)
gh repo clone creator35lwb-web/verifimind-genesis-mcp

# Create alignment issue
gh issue create --repo creator35lwb-web/verifimind-genesis-mcp --label cto-alignment

# Build and deploy
cd mcp-server
gcloud builds submit --tag gcr.io/YOUR_GCP_PROJECT_ID/verifimind-mcp-server:v{VERSION}
gcloud run deploy verifimind-mcp-server --image gcr.io/YOUR_GCP_PROJECT_ID/verifimind-mcp-server:v{VERSION} --region us-central1
```

---

**Last Updated:** January 29, 2026
**Protocol Version:** 1.0
