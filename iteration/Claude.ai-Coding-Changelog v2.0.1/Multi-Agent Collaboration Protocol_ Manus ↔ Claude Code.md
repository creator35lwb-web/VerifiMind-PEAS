# Multi-Agent Collaboration Protocol: Manus ↔ Claude Code
## VerifiMind PEAS Development Workflow Standard

**Version**: 1.0.0  
**Effective Date**: December 23, 2025  
**Status**: ✅ **ACTIVE**  
**Author**: Alton Lee (Project Owner) + Manus AI (CTO)

---

## 📋 Executive Summary

This protocol establishes the standard operating procedures for multi-agent collaboration between **Manus AI** and **Claude Code** when developing VerifiMind PEAS. Following this protocol ensures:

- ✅ **Zero conflicts** between environments
- ✅ **Consistent codebase** across all agents
- ✅ **Clear ownership** of responsibilities
- ✅ **Smooth handoffs** between sessions
- ✅ **Robust alignment** for every iteration

---

## 🎯 Protocol Objectives

### Primary Goals
1. **Prevent Merge Conflicts**: Clear separation of concerns
2. **Ensure Alignment**: Every session starts with sync
3. **Maintain Quality**: Code reviews before commits
4. **Enable Collaboration**: Seamless handoffs between agents
5. **Document Progress**: Comprehensive session notes

### Success Metrics
- **Conflict Rate**: 0% (target)
- **Alignment Time**: < 5 minutes per session
- **Handoff Quality**: 100% context preservation
- **Code Quality**: All tests pass before commit

---

## 🏗️ Architecture: Agent Roles & Responsibilities

### 🤖 Manus AI (CTO Role)
**Primary Responsibilities:**
- ✅ **Code Development**: Core functionality, features, bug fixes
- ✅ **Architecture Decisions**: System design, provider selection
- ✅ **Testing**: Unit tests, integration tests, validation
- ✅ **Documentation**: Technical docs, code comments, README
- ✅ **GitHub Commits**: Code changes, feature branches

**Ownership Areas:**
```
/mcp-server/src/           # Core MCP server code
/mcp-server/tests/         # Test suites
/docs/                     # Technical documentation
/validation_archive/       # Validation reports
*.md (root level)          # Project documentation
```

**Commit Message Prefix:**
```
feat:    # New feature
fix:     # Bug fix
docs:    # Documentation
test:    # Tests
refactor: # Code refactoring
```

---

### 🔧 Claude Code (DevOps Role)
**Primary Responsibilities:**
- ✅ **Deployment**: Docker builds, Cloud Run deployment
- ✅ **Infrastructure**: Domain setup, SSL, environment variables
- ✅ **Monitoring**: Logs, health checks, performance
- ✅ **Configuration**: Dockerfile, deployment configs
- ✅ **Troubleshooting**: Production issues, debugging

**Ownership Areas:**
```
/mcp-server/Dockerfile     # Container configuration
/mcp-server/*.yaml         # Deployment configs
/iteration/                # Session notes, research
/mcp-server/DEPLOYMENT_*.md # Deployment documentation
```

**Commit Message Prefix:**
```
deploy:  # Deployment changes
infra:   # Infrastructure
config:  # Configuration
ops:     # Operations
```

---

## 🔄 Workflow: Session Protocol

### Phase 1: Session Start (MANDATORY)

**Every session MUST begin with:**

```bash
# Step 1: Pull latest from GitHub
cd /home/ubuntu/VerifiMind-PEAS
git fetch origin
git pull origin main

# Step 2: Check for uncommitted changes
git status

# Step 3: Review recent commits
git log --oneline -10

# Step 4: Verify no conflicts
git diff origin/main
```

**Checklist:**
- [ ] Pulled latest from GitHub
- [ ] No uncommitted changes
- [ ] Reviewed recent commits
- [ ] No conflicts detected

---

### Phase 2: Work Execution

**Before Making Changes:**
1. **Identify ownership** - Is this Manus AI or Claude Code territory?
2. **Check for conflicts** - Any recent changes in same files?
3. **Communicate intent** - Document what you're about to do

**During Work:**
1. **Make atomic commits** - One logical change per commit
2. **Test before commit** - Run relevant tests
3. **Document changes** - Update relevant docs

**Commit Template:**
```
<type>: <short description>

<detailed description>

✅ Changes:
- <change 1>
- <change 2>

✅ Testing:
- <test result>

🔗 Related: <issue/PR number if applicable>
```

---

### Phase 3: Session End (MANDATORY)

**Every session MUST end with:**

```bash
# Step 1: Commit all changes
git add -A
git status
git commit -m "<type>: <description>"

# Step 2: Push to GitHub
git push origin main

# Step 3: Verify push succeeded
git log --oneline -5
```

**Checklist:**
- [ ] All changes committed
- [ ] Pushed to GitHub
- [ ] Verified push succeeded
- [ ] Session notes updated

---

## 📝 Handoff Protocol

### Manus AI → Claude Code Handoff

**Required Information:**
```markdown
## Handoff: Manus AI → Claude Code

**Date**: [Date]
**Session**: [Session ID]

### What Was Done
- [List of changes made]

### What Needs To Be Done
- [List of tasks for Claude Code]

### Files Changed
- [List of modified files]

### Testing Status
- [Test results]

### Environment Variables Needed
- [List of env vars if applicable]

### Known Issues
- [Any issues to be aware of]

### GitHub Commit
- Commit: [hash]
- Branch: main
```

---

### Claude Code → Manus AI Handoff

**Required Information:**
```markdown
## Handoff: Claude Code → Manus AI

**Date**: [Date]
**Session**: [Session ID]

### What Was Done
- [List of deployment/infra changes]

### What Needs To Be Done
- [List of tasks for Manus AI]

### Deployment Status
- [Current deployment state]

### Files Changed
- [List of modified files]

### Environment Variables Set
- [List of env vars configured]

### Known Issues
- [Any issues to be aware of]

### GitHub Commit
- Commit: [hash]
- Branch: main
```

---

## 🚨 Conflict Resolution Protocol

### Prevention (Best Practice)

1. **Clear Ownership**: Each file has one owner
2. **Communication**: Document intent before changes
3. **Atomic Commits**: Small, focused changes
4. **Frequent Sync**: Pull before every session

### Detection

```bash
# Check for conflicts before starting work
git fetch origin
git diff HEAD origin/main --stat

# If conflicts exist, review them
git diff HEAD origin/main
```

### Resolution

**If Conflict Detected:**

1. **STOP** - Do not make changes
2. **ANALYZE** - Understand what changed
3. **COMMUNICATE** - Discuss with other agent
4. **RESOLVE** - Merge carefully
5. **VERIFY** - Test after resolution

**Resolution Commands:**
```bash
# Option 1: Accept remote changes (their version)
git checkout --theirs <file>

# Option 2: Accept local changes (our version)
git checkout --ours <file>

# Option 3: Manual merge
# Edit file manually, then:
git add <file>
git commit -m "resolve: Merge conflict in <file>"
```

---

## 📊 File Ownership Matrix

| Directory/File | Owner | Notes |
|----------------|-------|-------|
| `/mcp-server/src/**/*.py` | Manus AI | Core code |
| `/mcp-server/tests/**/*.py` | Manus AI | Tests |
| `/mcp-server/Dockerfile` | Claude Code | Container |
| `/mcp-server/*.yaml` | Claude Code | Configs |
| `/mcp-server/pyproject.toml` | **SHARED** | Coordinate |
| `/docs/**/*.md` | Manus AI | Documentation |
| `/iteration/**/*` | Claude Code | Session notes |
| `/validation_archive/**/*` | Manus AI | Reports |
| `README.md` | **SHARED** | Coordinate |
| `*.md` (root) | Manus AI | Project docs |
| `/mcp-server/DEPLOYMENT_*.md` | Claude Code | Deploy docs |

### SHARED Files Protocol

For files marked **SHARED** (e.g., `pyproject.toml`, `README.md`):

1. **Announce intent** before editing
2. **Pull latest** immediately before editing
3. **Make minimal changes** - only what's needed
4. **Commit immediately** after editing
5. **Push immediately** after commit

---

## 🔐 Environment Variables Protocol

### Manus AI Responsibilities
- Define required environment variables
- Document in code and README
- Test with mock/placeholder values

### Claude Code Responsibilities
- Set environment variables in Cloud Run
- Manage secrets securely
- Document in deployment guides

### Variable Naming Convention
```
VERIFIMIND_*         # VerifiMind-specific
GEMINI_API_KEY       # Gemini API
ANTHROPIC_API_KEY    # Anthropic API
OPENAI_API_KEY       # OpenAI API
PORT                 # Server port
```

---

## 📋 Session Notes Template

**Location**: `/iteration/sessions/YYYY-MM-DD_<agent>_<topic>.md`

```markdown
# Session Notes: [Topic]

**Date**: [YYYY-MM-DD]
**Agent**: [Manus AI / Claude Code]
**Duration**: [X hours]
**Status**: [Completed / In Progress]

## Objectives
- [ ] Objective 1
- [ ] Objective 2

## Changes Made
### Files Modified
- `path/to/file.py` - Description

### Commits
- `abc1234` - commit message

## Testing
- [ ] Unit tests passed
- [ ] Integration tests passed
- [ ] Manual testing completed

## Issues Encountered
- Issue 1: Description + Resolution

## Next Steps
- [ ] Task for next session

## Handoff Notes
[Notes for the other agent]
```

---

## ✅ Compliance Checklist

### Before Every Session
- [ ] Pulled latest from GitHub
- [ ] Checked for uncommitted changes
- [ ] Reviewed recent commits
- [ ] Verified no conflicts
- [ ] Identified file ownership

### During Session
- [ ] Working within ownership boundaries
- [ ] Making atomic commits
- [ ] Testing changes
- [ ] Documenting progress

### After Every Session
- [ ] All changes committed
- [ ] Pushed to GitHub
- [ ] Session notes created
- [ ] Handoff notes prepared (if needed)

### Before Deployment
- [ ] All tests pass
- [ ] Documentation updated
- [ ] Environment variables documented
- [ ] Deployment checklist reviewed

---

## 🎓 Best Practices

### DO ✅
- Pull before every session
- Make atomic commits
- Test before committing
- Document changes
- Communicate intent
- Follow ownership boundaries
- Create handoff notes

### DON'T ❌
- Edit files outside your ownership
- Make large, multi-purpose commits
- Commit without testing
- Skip documentation
- Work without syncing first
- Ignore conflicts
- Leave sessions without pushing

---

## 📞 Escalation Protocol

### Level 1: Minor Conflict
**Symptoms**: Small overlap in changes
**Resolution**: Coordinate via handoff notes
**Timeline**: Resolve in next session

### Level 2: Major Conflict
**Symptoms**: Significant code conflicts
**Resolution**: Stop work, document issue, coordinate
**Timeline**: Resolve before continuing

### Level 3: Critical Issue
**Symptoms**: Production down, data loss risk
**Resolution**: Immediate coordination, rollback if needed
**Timeline**: Resolve immediately

---

## 📈 Protocol Metrics

### Track These Metrics
1. **Conflicts per week**: Target 0
2. **Alignment time per session**: Target < 5 min
3. **Handoff quality score**: Target 100%
4. **Test pass rate**: Target 100%
5. **Documentation coverage**: Target 100%

### Review Schedule
- **Weekly**: Quick metrics review
- **Monthly**: Protocol effectiveness review
- **Quarterly**: Protocol update if needed

---

## 🔄 Protocol Updates

### How to Update This Protocol
1. Propose change in session notes
2. Discuss with other agent
3. Update protocol document
4. Commit with message: `protocol: Update collaboration protocol`
5. Notify all agents

### Version History
| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2025-12-23 | Initial protocol |

---

## 📚 Related Documents

- **ALIGNMENT_REPORT_V2.0.md** - Latest alignment analysis
- **DEPLOYMENT_CHECKLIST_V2.0.md** - Deployment guide
- **ITERATION_JOURNEY_REPORT.md** - Development history
- **docs/guides/CLAUDE_CODE_INTEGRATION.md** - Claude integration guide

---

## ✅ Protocol Adoption

### Acknowledgment
By working on VerifiMind PEAS, all agents agree to follow this protocol.

### Effective Date
This protocol is effective immediately upon commit to GitHub.

### Enforcement
- All sessions must follow this protocol
- Violations should be documented and resolved
- Protocol updates require coordination

---

**Protocol Status**: ✅ **ACTIVE**  
**Last Updated**: December 23, 2025  
**Next Review**: January 23, 2026

---

## 🎯 Quick Reference Card

```
┌─────────────────────────────────────────────────────────────┐
│         MULTI-AGENT COLLABORATION PROTOCOL v1.0             │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  SESSION START:                                             │
│  1. git fetch origin && git pull origin main                │
│  2. git status (check for conflicts)                        │
│  3. git log --oneline -10 (review recent)                   │
│                                                             │
│  OWNERSHIP:                                                 │
│  • Manus AI: /src/, /tests/, /docs/, validation_archive/    │
│  • Claude Code: Dockerfile, *.yaml, /iteration/, deploy/    │
│  • SHARED: pyproject.toml, README.md (coordinate!)          │
│                                                             │
│  SESSION END:                                               │
│  1. git add -A && git commit -m "<type>: <desc>"            │
│  2. git push origin main                                    │
│  3. Create session notes (if significant work)              │
│                                                             │
│  CONFLICT RESOLUTION:                                       │
│  1. STOP - Don't make changes                               │
│  2. ANALYZE - Understand what changed                       │
│  3. COMMUNICATE - Discuss with other agent                  │
│  4. RESOLVE - Merge carefully                               │
│  5. VERIFY - Test after resolution                          │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

**End of Protocol Document**
