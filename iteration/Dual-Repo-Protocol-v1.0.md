# VerifiMind-PEAS Dual-Repo Protocol v1.0

**Created:** January 29, 2026
**Authors:** Claude Code, Manus AI (CTO), Alton Lee Wei Bin
**Status:** ACTIVE

---

## Overview

This protocol defines the workflow for managing VerifiMind-PEAS development across two repositories with different visibility levels, ensuring proper separation between internal development and public releases.

---

## Repository Structure

| Repository | Visibility | Purpose | URL |
|------------|------------|---------|-----|
| **VerifiMind-PEAS** | PUBLIC | Stable releases, methodology docs, public MCP server | github.com/creator35lwb-web/VerifiMind-PEAS |
| **verifimind-genesis-mcp** | PRIVATE | Internal development, iteration, CTO communications | github.com/creator35lwb-web/verifimind-genesis-mcp |

---

## Content Classification

### PUBLIC Repo (VerifiMind-PEAS)

**What goes here:**
- Stable, tested releases (tagged versions)
- Public documentation (README, guides, tutorials)
- CHANGELOG.md (public-facing changes only)
- SERVER_STATUS.md (operational status)
- MCP server code (`mcp-server/` folder)
- Validation examples and case studies
- Community-facing issues and discussions

**What does NOT go here:**
- Internal iteration discussions
- CTO alignment reports
- Development roadmap drafts
- Experimental features before validation
- Cost analysis / budget discussions
- Security vulnerability details (until patched)

### PRIVATE Repo (verifimind-genesis-mcp)

**What goes here:**
- Internal development iterations
- CTO Alignment Reports (Manus AI communications)
- Claude Code session handoffs
- Experimental features and POCs
- Cost analysis and budget planning
- Security vulnerability investigations
- Pre-release testing and validation
- Internal roadmap discussions
- Architecture decision records (ADRs)

---

## Communication Protocol

### Claude Code ↔ Manus AI (CTO)

```
┌─────────────────┐     GitHub Issue/PR      ┌─────────────────┐
│   Claude Code   │ ───────────────────────► │    Manus AI     │
│  (Implementer)  │                          │     (CTO)       │
│                 │ ◄─────────────────────── │                 │
└─────────────────┘     Review/Approval      └─────────────────┘
         │                                            │
         │                                            │
         ▼                                            ▼
┌─────────────────────────────────────────────────────────────┐
│              PRIVATE REPO: verifimind-genesis-mcp           │
│                                                             │
│  - Alignment Updates (Issues)                               │
│  - Implementation PRs                                       │
│  - CTO Review Comments                                      │
│  - Architecture Decisions                                   │
└─────────────────────────────────────────────────────────────┘
         │
         │ After CTO Approval
         ▼
┌─────────────────────────────────────────────────────────────┐
│              PUBLIC REPO: VerifiMind-PEAS                   │
│                                                             │
│  - Stable Release Commit                                    │
│  - CHANGELOG Update                                         │
│  - Public Documentation                                     │
└─────────────────────────────────────────────────────────────┘
```

### Communication Templates

#### 1. Alignment Update (Claude Code → Manus AI)

**Location:** PRIVATE repo Issue
**Title Format:** `[Alignment] v{version} - {summary}`

```markdown
# Alignment Update for Manus AI (CTO)

**Date:** {date}
**From:** Claude Code
**Version:** {version}

## Summary
{1-2 sentence summary}

## Changes Implemented
- {change 1}
- {change 2}

## Technical Details
{brief technical explanation}

## Testing Results
{test results summary}

## Next Steps
{recommended next actions}

## Awaiting
- [ ] CTO Review
- [ ] CTO Approval for public release
```

#### 2. CTO Response Template

```markdown
## CTO Review

**Status:** {APPROVED / NEEDS_CHANGES / DEFERRED}

### Feedback
{feedback}

### Required Changes (if any)
- {change 1}

### Approval for Public Release
- [ ] Approved for VerifiMind-PEAS main branch
```

---

## Workflow Protocol

### Phase 1: Development (PRIVATE)

1. **Claude Code** creates feature branch in PRIVATE repo
2. **Claude Code** implements changes
3. **Claude Code** creates Alignment Update issue
4. **Claude Code** links PR to issue
5. Wait for CTO review

### Phase 2: Review (PRIVATE)

1. **Manus AI (CTO)** reviews implementation
2. **Manus AI** provides feedback via issue comments
3. **Claude Code** addresses feedback
4. **Manus AI** approves for public release

### Phase 3: Public Release (PUBLIC)

1. **Claude Code** cherry-picks/merges approved changes to PUBLIC repo
2. **Claude Code** updates CHANGELOG.md
3. **Claude Code** updates SERVER_STATUS.md (if applicable)
4. **Claude Code** creates release tag (if major version)
5. **Claude Code** deploys to production (if applicable)

---

## Version Synchronization

### Version Numbering

```
MAJOR.MINOR.PATCH

MAJOR: Breaking changes, major features
MINOR: New features, non-breaking
PATCH: Bug fixes, small improvements
```

### Sync Points

| Event | PRIVATE Repo | PUBLIC Repo |
|-------|--------------|-------------|
| Development starts | Create branch | - |
| Implementation complete | Create PR + Issue | - |
| CTO Approved | Merge PR | Cherry-pick/merge |
| Release ready | - | Tag + CHANGELOG |
| Deployed | Update internal docs | Update SERVER_STATUS |

---

## File Synchronization

### Files that sync PRIVATE → PUBLIC

| File | Sync Trigger | Notes |
|------|--------------|-------|
| `mcp-server/src/**` | After CTO approval | Core server code |
| `CHANGELOG.md` | After release | Public changes only |
| `SERVER_STATUS.md` | After deployment | Operational status |
| `README.md` | After major changes | Public documentation |

### Files that stay PRIVATE only

| File | Reason |
|------|--------|
| `iteration/*.md` | Internal communications |
| `CTO_Report_*.md` | CTO alignment reports |
| `.internal/` | Internal documentation |
| Cost analysis docs | Budget sensitive |
| Security investigations | Pre-patch sensitive |

---

## Session Handoff Protocol

### Claude Code Session End

When ending a Claude Code session, create handoff document:

**Location:** PRIVATE repo `iteration/` folder
**Filename:** `Session_Handoff_{date}.md`

```markdown
# Session Handoff

**Date:** {date}
**Session ID:** {if available}

## Work Completed
- {item 1}
- {item 2}

## Current State
- Server Version: {version}
- Deployment Status: {status}
- Pending PRs: {list}

## Next Session Should
1. {action 1}
2. {action 2}

## Open Issues
- {issue 1}

## Files Modified This Session
- {file 1}
- {file 2}
```

---

## Integration with Existing Protocols

### CHANGELOG Protocol

- **PRIVATE repo:** Detailed technical changelog with internal notes
- **PUBLIC repo:** User-facing changelog (CHANGELOG.md)

### Job Scope Protocol

All job scopes defined by CTO are tracked in PRIVATE repo issues with label `job-scope`.

### Communication Protocol (Claude Code ↔ Manus AI)

All CTO communications happen via PRIVATE repo issues with label `cto-alignment`.

---

## Quick Reference

### For Claude Code

```bash
# Development workflow
1. Work in PRIVATE repo for iterations
2. Create alignment issue for CTO
3. After approval, sync to PUBLIC repo
4. Update CHANGELOG and deploy

# Commit message format
feat(scope): description     # New feature
fix(scope): description      # Bug fix
docs: description            # Documentation
chore: description           # Maintenance
```

### For Manus AI (CTO)

```
1. Review alignment issues in PRIVATE repo
2. Provide feedback via issue comments
3. Approve for public release when ready
4. Track progress via issue labels
```

---

## Labels for PRIVATE Repo

| Label | Purpose |
|-------|---------|
| `cto-alignment` | Alignment updates for CTO review |
| `job-scope` | Job scope definitions |
| `approved` | Approved for public release |
| `needs-changes` | Requires modifications |
| `in-progress` | Currently being worked on |
| `internal-only` | Never sync to public |

---

## Summary

This dual-repo protocol ensures:

1. **Clean separation** between internal development and public releases
2. **Proper review process** with CTO approval gates
3. **Transparent communication** via GitHub issues
4. **Consistent versioning** across both repos
5. **Secure handling** of sensitive information

---

**Protocol Version:** 1.0
**Last Updated:** January 29, 2026
**Next Review:** February 2026
