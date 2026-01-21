# Multi-Agent Collaboration Protocol

**Version:** 1.0.0
**Established:** January 21, 2026
**Status:** Active

---

## Overview

This protocol defines how multiple AI agents (Manus AI, Claude Code, and others) collaborate on the VerifiMind PEAS project using **GitHub as the central bridge** for all iterations and updates.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    GITHUB (Bridge)                          │
│         creator35lwb-web/VerifiMind-PEAS                   │
│                                                             │
│  • Source of Truth for all iterations                      │
│  • Alignment checkpoint before any work                    │
│  • Commit all changes for cross-agent visibility           │
└─────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        ▼                     ▼                     ▼
┌───────────────┐     ┌───────────────┐     ┌───────────────┐
│   Manus AI    │     │  Claude Code  │     │  Other Agents │
│    (CTO)      │     │  (Executor)   │     │   (Future)    │
└───────────────┘     └───────────────┘     └───────────────┘
        │                     │                     │
        └─────────────────────┴─────────────────────┘
                              │
              ┌───────────────┼───────────────┐
              ▼               ▼               ▼
      ┌─────────────┐ ┌─────────────┐ ┌─────────────┐
      │ HuggingFace │ │  Smithery   │ │ MCP Registry│
      │   (Demo)    │ │   (MCP)     │ │  (Listed)   │
      └─────────────┘ └─────────────┘ └─────────────┘
```

---

## Repositories

| Repository | Purpose | Language | Platform |
|------------|---------|----------|----------|
| `VerifiMind-PEAS` | Main repo, GCP production server | Python | GCP Cloud Run |
| `verifimind-genesis-mcp` | Smithery MCP server | TypeScript | Smithery.ai |
| `YSenseAI/verifimind-peas` | Interactive demo | Python/Gradio | HuggingFace |

---

## Agent Roles

### Manus AI (CTO)
- Strategic planning and direction
- Creates Implementation Guides
- Reviews and adds finishing touches (badges, etc.)
- High-level architecture decisions

### Claude Code (Executor)
- Executes technical tasks from Implementation Guides
- Writes and pushes code
- Runs deployments and workflows
- Validates platform health

### Other Agents (Future)
- Follow same alignment protocol
- Check GitHub before starting
- Commit all changes with clear messages

---

## Standard Protocol

### Phase 1: Alignment (Before Starting Work)

```bash
# 1. Navigate to project directory
cd /path/to/VerifiMind-PEAS

# 2. Pull latest from GitHub
git pull origin main

# 3. Check recent commits for context
git log --oneline -10

# 4. Check for Implementation Guides
ls iteration/

# 5. Read any new guides or updates
cat iteration/[latest-guide].md
```

### Phase 2: Execution (Doing the Work)

- Follow Implementation Guide tasks
- Make changes incrementally
- Test changes when possible
- Document any issues discovered

### Phase 3: Commit (After Completing Work)

```bash
# 1. Stage changes
git add [files]

# 2. Commit with clear message and co-author
git commit -m "feat/fix/docs: Description

[Optional detailed explanation]

Co-Authored-By: [Agent Name] <noreply@anthropic.com>"

# 3. Push to GitHub immediately
git push origin main

# 4. Verify on GitHub
gh api repos/creator35lwb-web/VerifiMind-PEAS/commits?per_page=1
```

### Phase 4: Cross-Platform Sync (If Needed)

- Update HuggingFace if demo changes needed
- Update Smithery repo if MCP server changes needed
- Update MCP Registry if version/manifest changes needed

---

## Commit Message Format

```
<type>: <short description>

[optional body with more details]

Co-Authored-By: <Agent Name> <noreply@anthropic.com>
```

**Types:**
- `feat` - New feature
- `fix` - Bug fix
- `docs` - Documentation only
- `refactor` - Code restructuring
- `test` - Adding tests
- `chore` - Maintenance tasks

---

## Session Handoff Format

When one agent completes work and another may continue:

```markdown
HANDOFF: [FROM Agent] → [TO Agent]
DATE: [Date]

COMPLETED:
- [Task 1]
- [Task 2]

PENDING:
- [Task 3]
- [Task 4]

COMMITS:
- [sha] - [message]
- [sha] - [message]

NOTES:
- [Important context]
- [Any blockers or issues]
```

---

## Key Principles

| Principle | Description |
|-----------|-------------|
| **Alignment First** | Always pull & check GitHub before starting any work |
| **Commit Everything** | All changes must be committed for cross-agent visibility |
| **Clear Messages** | Commit messages explain what was done and why |
| **Immediate Push** | Push to GitHub immediately after committing |
| **Cross-Platform Sync** | Keep HuggingFace, Smithery, and Registry aligned |
| **Documentation** | Update iteration/ folder and guides as needed |

---

## Platform Links

| Platform | URL |
|----------|-----|
| **GitHub (Main)** | https://github.com/creator35lwb-web/VerifiMind-PEAS |
| **GitHub (Smithery)** | https://github.com/creator35lwb-web/verifimind-genesis-mcp |
| **GCP Production** | https://verifimind.ysenseai.org |
| **MCP Registry** | https://registry.modelcontextprotocol.io/?q=verifimind |
| **Smithery** | https://smithery.ai/server/creator35lwb-web/verifimind-genesis |
| **HuggingFace** | https://huggingface.co/spaces/YSenseAI/verifimind-peas |
| **GitHub Actions** | https://github.com/creator35lwb-web/VerifiMind-PEAS/actions |

---

## Quick Reference Commands

```bash
# Check alignment
git pull origin main && git log --oneline -5

# Check GitHub CLI auth
gh auth status

# View recent commits on GitHub
gh api repos/creator35lwb-web/VerifiMind-PEAS/commits?per_page=5 --jq '.[] | {sha: .sha[0:7], message: .commit.message | split("\n")[0]}'

# Check platform health
curl -s https://verifimind.ysenseai.org/health

# List GitHub Actions workflows
gh workflow list --repo creator35lwb-web/VerifiMind-PEAS
```

---

**Protocol Established:** January 21, 2026
**Last Updated:** January 21, 2026
**Maintained By:** YSenseAI Team
