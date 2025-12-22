# Multi-Agent Workflow Documentation

**Version**: 1.0.0  
**Last Updated**: December 18, 2025

---

## Overview

This directory contains documentation for the **Multi-Agent Collaboration Protocol** used in VerifiMind-PEAS development.

**Agents**:
- **Manus AI** (X Agent, CTO) - Strategic architect and technical director
- **Claude Code** (Implementation Agent) - Tactical code implementer
- **GitHub** - Communication bridge and single source of truth
- **Alton Lee** - Human orchestrator and decision authority

---

## Directory Structure

```
docs/
├── MULTI_AGENT_WORKFLOW_PROTOCOL.md  # Complete protocol specification
├── MULTI_AGENT_WORKFLOW_README.md    # This file
├── implementation-guides/             # Manus → Claude Code
│   └── 20251218_smithery_refactoring_IMPLEMENTATION_GUIDE.md
├── implementation-reports/            # Claude Code → Manus
│   └── (reports will appear here after Claude Code completes work)
├── iterations/                        # Back-and-forth refinements
│   └── (iteration guides will appear here)
├── reviews/                           # Manus review reports
│   └── (reviews will appear here)
├── decisions/                         # Alton's strategic decisions
│   └── (decisions will appear here)
└── templates/                         # Document templates
    ├── IMPLEMENTATION_GUIDE_TEMPLATE.md
    ├── IMPLEMENTATION_REPORT_TEMPLATE.md
    └── (more templates)
```

---

## Quick Start

### For Alton (Orchestrator)

**When starting new work**:

1. **Manus creates implementation guide**:
   - Guide appears in `/docs/implementation-guides/`
   - Filename: `YYYYMMDD_<task>_IMPLEMENTATION_GUIDE.md`

2. **You notify Claude Code**:
   - Open Claude Code session
   - Provide path to implementation guide
   - Give approval to proceed

3. **Claude Code implements**:
   - Makes changes locally
   - Creates implementation report
   - Commits to GitHub

4. **You request Manus review**:
   - Pull latest from GitHub
   - Ask Manus to review implementation report
   - Manus creates review report

5. **You make final decision**:
   - Approve (merge and proceed)
   - Request iteration (Manus creates iteration guide)
   - Reject (explain why and restart)

---

### For Manus AI

**When creating implementation guide**:

1. Use template: `/docs/templates/IMPLEMENTATION_GUIDE_TEMPLATE.md`
2. Save to: `/docs/implementation-guides/YYYYMMDD_<task>_IMPLEMENTATION_GUIDE.md`
3. Include all required sections
4. Commit with standard message format
5. Notify Alton

**When reviewing implementation**:

1. Read implementation report in `/docs/implementation-reports/`
2. Review code changes
3. Run additional tests if needed
4. Create review report in `/docs/reviews/`
5. Commit and notify Alton

---

### For Claude Code

**When implementing**:

1. Pull latest from GitHub
2. Read implementation guide in `/docs/implementation-guides/`
3. Make changes as specified
4. Run all tests
5. Create implementation report using template
6. Save to: `/docs/implementation-reports/YYYYMMDD_<task>_IMPLEMENTATION_REPORT.md`
7. Commit code + report
8. Notify Alton

---

## Commit Message Format

**Manus commits**:
```
docs: <brief description>

- Created by: Manus AI (X Agent, CTO)
- Target: Claude Code (Implementation Agent)
- Task: <task description>
```

**Claude Code commits**:
```
<type>: <brief description>

- Implemented by: Claude Code (Implementation Agent)
- Based on: Manus AI guide (YYYYMMDD)
- Status: Success / Partial Success / Blocked
- Tests: <results>
```

---

## Current Status

### Active Work

- **Smithery Refactoring** (Started: 2025-12-18)
  - Guide: `/docs/implementation-guides/20251218_smithery_refactoring_IMPLEMENTATION_GUIDE.md`
  - Status: ⏳ Awaiting Claude Code implementation
  - Assignee: Claude Code

---

## Resources

- **Full Protocol**: `/docs/MULTI_AGENT_WORKFLOW_PROTOCOL.md`
- **Templates**: `/docs/templates/`
- **GitHub Repository**: https://github.com/creator35lwb-web/VerifiMind-PEAS

---

## Support

**Questions about the workflow?**
- Read the full protocol document
- Check templates for examples
- Ask Alton for clarification

**Issues with the workflow?**
- Report to Alton
- Suggest improvements
- Update protocol document

---

**This is a living document** - the workflow will evolve as we learn what works best!

**FLYWHEEL, TEAM!** 🚀
