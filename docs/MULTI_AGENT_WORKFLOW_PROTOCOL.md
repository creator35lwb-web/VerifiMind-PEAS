# Multi-Agent Collaboration Protocol: Manus ↔ Claude Code

**Version**: 1.0.0  
**Date**: December 18, 2025  
**Author**: Manus AI (X Agent, CTO) + Alton Lee  
**Purpose**: Standardize communication and collaboration between AI agents via GitHub

---

## Executive Summary

This document defines a standardized protocol for multi-agent collaboration in the VerifiMind-PEAS project, where **Manus AI** (strategic architect) and **Claude Code** (tactical implementer) work together through **GitHub as the communication bridge**.

**This is a "Meta-Genesis" application** - applying the Genesis Methodology's principles (clear roles, structured communication, version tracking) to the development workflow itself.

**Key Innovation**: Treating GitHub commits and documentation as the "Chain of Thought" between agents, enabling asynchronous collaboration with full context preservation.

---

## 1. Agent Roles and Responsibilities

### 1.1 Manus AI (X Agent, CTO)

**Role**: Strategic Architect and Technical Director

**Responsibilities**:
- Define high-level architecture and technical direction
- Create comprehensive implementation guides for Claude Code
- Review and validate Claude Code's implementations
- Make strategic decisions (technology choices, design patterns)
- Maintain project vision and ensure alignment with Genesis Methodology
- Generate documentation, white papers, and strategic analysis
- Coordinate with external stakeholders (community, users)

**Communication Style**:
- Comprehensive, detailed specifications
- Clear success criteria and testing requirements
- Context-rich explanations of "why" behind decisions
- Forward-looking recommendations

**Output Artifacts**:
- Implementation guides (`.md` files in `/docs/implementation-guides/`)
- Architecture decision records (ADRs)
- Strategic analysis documents
- Review reports

---

### 1.2 Claude Code (Implementation Agent)

**Role**: Tactical Code Implementer

**Responsibilities**:
- Execute code refactoring and implementation based on Manus's guides
- Run local tests and verify functionality
- Report implementation results and issues
- Suggest tactical improvements and optimizations
- Maintain code quality and consistency
- Update local documentation (inline comments, docstrings)

**Communication Style**:
- Concise, action-oriented reports
- Clear status updates (what worked, what didn't)
- Specific questions when clarification needed
- Code-focused feedback

**Output Artifacts**:
- Code commits with descriptive messages
- Implementation reports (`.md` files in `/docs/implementation-reports/`)
- Test results and logs
- Issue reports (if problems encountered)

---

### 1.3 GitHub (Communication Bridge)

**Role**: Single Source of Truth and Async Communication Channel

**Responsibilities**:
- Store all code, documentation, and artifacts
- Track changes through commits and branches
- Enable both agents to read each other's work
- Preserve complete history and context
- Serve as handoff mechanism between agents

**Key Features Used**:
- Commits: Atomic units of work with descriptive messages
- Branches: Isolation for experimental work
- Pull Requests: Formal review and merge process (optional)
- Issues: Track bugs, features, and discussions
- Discussions: Community engagement

---

### 1.4 Alton Lee (Orchestrator)

**Role**: Human Orchestrator and Decision Authority

**Responsibilities**:
- Make final decisions on strategic direction
- Approve/reject agent recommendations
- Provide context and requirements
- Resolve conflicts between agents
- Ensure alignment with project goals
- Quality control and acceptance testing

**Authority**:
- Final decision-maker on all strategic choices
- Can override agent recommendations
- Sets priorities and timelines
- Defines success criteria

---

## 2. Communication Protocol

### 2.1 Manus → Claude Code Handoff

**When**: Manus completes strategic planning or architecture design

**Process**:

1. **Manus creates Implementation Guide** in `/docs/implementation-guides/`
   - Filename format: `YYYYMMDD_<task-name>_IMPLEMENTATION_GUIDE.md`
   - Example: `20251218_smithery_refactoring_IMPLEMENTATION_GUIDE.md`

2. **Guide must include**:
   - **Header**: Clear identification of sender (Manus AI, X Agent, CTO)
   - **Context**: Why this work is needed, what problem it solves
   - **Objectives**: Clear, measurable success criteria
   - **Step-by-Step Instructions**: Exact actions Claude Code should take
   - **Code Snippets**: Ready-to-use code examples
   - **Testing Requirements**: How to verify success
   - **Common Pitfalls**: Known issues to avoid
   - **Support**: How to get help if stuck

3. **Manus commits guide to GitHub**:
   ```bash
   git add docs/implementation-guides/20251218_smithery_refactoring_IMPLEMENTATION_GUIDE.md
   git commit -m "docs: Add Smithery refactoring implementation guide for Claude Code

   - Created by: Manus AI (X Agent, CTO)
   - Target: Claude Code (Implementation Agent)
   - Task: Refactor server.py for Smithery deployment
   - Estimated time: 1.5-2 hours
   - Success criteria: Server imports successfully, all tests pass"
   
   git push origin main
   ```

4. **Alton notifies Claude Code**:
   - Opens Claude Code session
   - Provides link to implementation guide
   - Gives approval to proceed

**Commit Message Format**:
```
docs: <brief description>

- Created by: Manus AI (X Agent, CTO)
- Target: Claude Code (Implementation Agent)
- Task: <task description>
- Estimated time: <time estimate>
- Success criteria: <criteria>
```

---

### 2.2 Claude Code → Manus Response

**When**: Claude Code completes implementation or encounters issues

**Process**:

1. **Claude Code creates Implementation Report** in `/docs/implementation-reports/`
   - Filename format: `YYYYMMDD_<task-name>_IMPLEMENTATION_REPORT.md`
   - Example: `20251218_smithery_refactoring_IMPLEMENTATION_REPORT.md`

2. **Report must include**:
   - **Header**: Clear identification of sender (Claude Code, Implementation Agent)
   - **Status**: Success / Partial Success / Blocked
   - **What Was Done**: Summary of changes made
   - **Files Modified**: List of all changed files
   - **Test Results**: Output of all tests run
   - **Issues Encountered**: Problems and how they were resolved
   - **Questions for Manus**: Clarifications needed (if any)
   - **Next Steps**: Recommendations for follow-up work

3. **Claude Code commits changes + report to GitHub**:
   ```bash
   git add src/verifimind_mcp/server.py docs/implementation-reports/20251218_smithery_refactoring_IMPLEMENTATION_REPORT.md
   git commit -m "feat: Refactor server.py for Smithery deployment

   - Implemented by: Claude Code (Implementation Agent)
   - Based on: Manus AI implementation guide (20251218)
   - Status: Success
   - Tests: All passed (3/3)
   - Files modified: server.py
   - Ready for: Manus review"
   
   git push origin main
   ```

4. **Alton notifies Manus**:
   - Pulls latest changes from GitHub
   - Reviews implementation report
   - Requests Manus to review

**Commit Message Format**:
```
<type>: <brief description>

- Implemented by: Claude Code (Implementation Agent)
- Based on: Manus AI implementation guide (YYYYMMDD)
- Status: Success / Partial Success / Blocked
- Tests: <test results>
- Files modified: <file list>
- Ready for: Manus review / Alton decision / Further work
```

---

### 2.3 Iteration Cycle

**When**: Work requires multiple rounds of refinement

**Process**:

1. **Manus reviews Claude Code's implementation**
   - Reads implementation report
   - Reviews code changes
   - Runs additional tests (if needed)

2. **Manus creates follow-up guide** (if changes needed):
   - Filename: `YYYYMMDD_<task-name>_ITERATION_<N>.md`
   - Example: `20251218_smithery_refactoring_ITERATION_2.md`
   - References previous work
   - Specifies only the changes needed

3. **Claude Code implements iteration**
   - Creates iteration report
   - Commits changes

4. **Repeat until success criteria met**

**Iteration Guide Format**:
```markdown
# Iteration N: <Task Name>

**Previous Work**: Implementation Report YYYYMMDD
**Issues to Address**: <list of issues>
**Changes Needed**: <specific changes>
**Success Criteria**: <updated criteria>
```

---

## 3. File Structure and Naming Conventions

### 3.1 Directory Structure

```
VerifiMind-PEAS/
├── docs/
│   ├── implementation-guides/        # Manus → Claude Code
│   │   ├── 20251218_smithery_refactoring_IMPLEMENTATION_GUIDE.md
│   │   ├── 20251219_api_layer_IMPLEMENTATION_GUIDE.md
│   │   └── ...
│   ├── implementation-reports/       # Claude Code → Manus
│   │   ├── 20251218_smithery_refactoring_IMPLEMENTATION_REPORT.md
│   │   ├── 20251219_api_layer_IMPLEMENTATION_REPORT.md
│   │   └── ...
│   ├── iterations/                   # Back-and-forth refinements
│   │   ├── 20251218_smithery_refactoring_ITERATION_2.md
│   │   └── ...
│   ├── reviews/                      # Manus review reports
│   │   ├── 20251218_smithery_refactoring_REVIEW.md
│   │   └── ...
│   └── decisions/                    # Alton's strategic decisions
│       ├── 20251218_smithery_deployment_DECISION.md
│       └── ...
```

---

### 3.2 Filename Conventions

| Document Type | Format | Example |
|---------------|--------|---------|
| Implementation Guide | `YYYYMMDD_<task>_IMPLEMENTATION_GUIDE.md` | `20251218_smithery_refactoring_IMPLEMENTATION_GUIDE.md` |
| Implementation Report | `YYYYMMDD_<task>_IMPLEMENTATION_REPORT.md` | `20251218_smithery_refactoring_IMPLEMENTATION_REPORT.md` |
| Iteration Guide | `YYYYMMDD_<task>_ITERATION_<N>.md` | `20251218_smithery_refactoring_ITERATION_2.md` |
| Review Report | `YYYYMMDD_<task>_REVIEW.md` | `20251218_smithery_refactoring_REVIEW.md` |
| Strategic Decision | `YYYYMMDD_<topic>_DECISION.md` | `20251218_smithery_deployment_DECISION.md` |

**Naming Rules**:
- Always start with date (YYYYMMDD) for chronological sorting
- Use underscores for spaces
- Use lowercase for consistency
- Include document type suffix (GUIDE, REPORT, REVIEW, etc.)
- Keep task names concise but descriptive

---

### 3.3 Document Templates

#### Template: Implementation Guide (Manus → Claude Code)

```markdown
# Implementation Guide: <Task Name>

**Date**: YYYY-MM-DD  
**Created by**: Manus AI (X Agent, CTO)  
**Target**: Claude Code (Implementation Agent)  
**Estimated Time**: <hours>  
**Priority**: High / Medium / Low

---

## Context

<Why this work is needed, what problem it solves>

---

## Objectives

<Clear, measurable success criteria>

---

## Prerequisites

<What must be in place before starting>

---

## Step-by-Step Instructions

### Step 1: <Action>

**Location**: <file path, line numbers>

**Current code**:
```<language>
<existing code>
```

**Change to**:
```<language>
<new code>
```

**Why**: <explanation>

---

### Step 2: <Action>

...

---

## Testing Requirements

### Test 1: <Test Name>

**Command**:
```bash
<test command>
```

**Expected Output**:
```
<expected result>
```

---

## Common Pitfalls

### Pitfall 1: <Issue>

**Wrong**:
```<language>
<incorrect code>
```

**Correct**:
```<language>
<correct code>
```

---

## Success Criteria

- [ ] <Criterion 1>
- [ ] <Criterion 2>
- [ ] <Criterion 3>

---

## Support

**If you encounter issues**:
1. <Troubleshooting step 1>
2. <Troubleshooting step 2>
3. Report to Alton with error details

---

## References

- <Link to related documentation>
- <Link to external resources>
```

---

#### Template: Implementation Report (Claude Code → Manus)

```markdown
# Implementation Report: <Task Name>

**Date**: YYYY-MM-DD  
**Implemented by**: Claude Code (Implementation Agent)  
**Based on**: <Link to implementation guide>  
**Status**: ✅ Success / ⚠️ Partial Success / ❌ Blocked  
**Time Taken**: <hours>

---

## Summary

<Brief overview of what was accomplished>

---

## Changes Made

### File 1: <file path>

**Changes**:
- <Change 1>
- <Change 2>

**Lines Modified**: <line numbers>

---

### File 2: <file path>

...

---

## Test Results

### Test 1: <Test Name>

**Command**:
```bash
<test command>
```

**Output**:
```
<actual output>
```

**Status**: ✅ Pass / ❌ Fail

---

## Issues Encountered

### Issue 1: <Description>

**Problem**: <What went wrong>

**Solution**: <How it was resolved>

**Status**: ✅ Resolved / ⚠️ Workaround / ❌ Blocked

---

## Questions for Manus

1. <Question 1>
2. <Question 2>

---

## Next Steps

<Recommendations for follow-up work>

---

## Commit Hash

`<git commit hash>`

---

## Attachments

- <Link to logs, screenshots, etc.>
```

---

## 4. Commit Message Standards

### 4.1 Conventional Commits Format

**Structure**:
```
<type>(<scope>): <subject>

<body>

<footer>
```

**Types**:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `refactor`: Code refactoring (no functional changes)
- `test`: Adding or updating tests
- `chore`: Maintenance tasks (dependencies, config)
- `style`: Code style changes (formatting, no logic changes)

**Scopes** (optional):
- `mcp`: MCP server related
- `agents`: Agent implementations
- `docs`: Documentation
- `workflow`: Development workflow

**Examples**:

```
feat(mcp): Refactor server.py for Smithery deployment

- Implemented by: Claude Code (Implementation Agent)
- Based on: Manus AI implementation guide (20251218)
- Added @smithery.server() decorator
- Added session config support to all Tools
- All tests passed (3/3)

Ready for: Manus review
```

```
docs: Add Smithery refactoring implementation guide

- Created by: Manus AI (X Agent, CTO)
- Target: Claude Code (Implementation Agent)
- Task: Refactor server.py for Smithery deployment
- Estimated time: 1.5-2 hours

Guide location: docs/implementation-guides/20251218_smithery_refactoring_IMPLEMENTATION_GUIDE.md
```

---

### 4.2 Agent Identification in Commits

**Every commit must identify the agent** in the body:

**Manus commits**:
```
- Created by: Manus AI (X Agent, CTO)
- Target: <target agent or purpose>
```

**Claude Code commits**:
```
- Implemented by: Claude Code (Implementation Agent)
- Based on: <link to guide>
```

**Alton commits**:
```
- Decision by: Alton Lee (Project Lead)
- Context: <decision context>
```

---

## 5. Workflow Examples

### Example 1: Simple Feature Implementation

**Scenario**: Manus designs a new feature, Claude Code implements it

**Step 1**: Manus creates implementation guide
```bash
# Manus (via Alton's Manus session)
git add docs/implementation-guides/20251218_new_feature_IMPLEMENTATION_GUIDE.md
git commit -m "docs: Add new feature implementation guide for Claude Code"
git push origin main
```

**Step 2**: Alton notifies Claude Code
```
"Hi Claude Code, please implement the new feature following this guide:
/docs/implementation-guides/20251218_new_feature_IMPLEMENTATION_GUIDE.md"
```

**Step 3**: Claude Code implements
```bash
# Claude Code (via Alton's local machine)
git pull origin main  # Get latest including guide
# ... make changes ...
git add src/new_feature.py docs/implementation-reports/20251218_new_feature_IMPLEMENTATION_REPORT.md
git commit -m "feat: Implement new feature

- Implemented by: Claude Code (Implementation Agent)
- Based on: Manus AI guide (20251218)
- Status: Success
- Tests: All passed"
git push origin main
```

**Step 4**: Alton notifies Manus
```
"Manus, please review Claude Code's implementation:
/docs/implementation-reports/20251218_new_feature_IMPLEMENTATION_REPORT.md"
```

**Step 5**: Manus reviews
```bash
# Manus (via Alton's Manus session)
git pull origin main  # Get latest including implementation
# ... review code and report ...
git add docs/reviews/20251218_new_feature_REVIEW.md
git commit -m "docs: Review new feature implementation

- Reviewed by: Manus AI (X Agent, CTO)
- Implementation by: Claude Code
- Verdict: Approved ✅
- Notes: Excellent work, all criteria met"
git push origin main
```

---

### Example 2: Iterative Refinement

**Scenario**: Initial implementation needs adjustments

**Step 1-4**: Same as Example 1

**Step 5**: Manus identifies issues
```bash
# Manus creates iteration guide
git add docs/iterations/20251218_new_feature_ITERATION_2.md
git commit -m "docs: Request iteration on new feature

- Created by: Manus AI (X Agent, CTO)
- Previous work: Implementation Report 20251218
- Issues: Performance optimization needed
- Changes: Add caching layer"
git push origin main
```

**Step 6**: Claude Code implements iteration
```bash
# Claude Code
git pull origin main
# ... make changes ...
git add src/new_feature.py docs/implementation-reports/20251218_new_feature_ITERATION_2_REPORT.md
git commit -m "refactor: Optimize new feature performance

- Implemented by: Claude Code (Implementation Agent)
- Based on: Manus AI iteration guide (20251218)
- Changes: Added caching layer
- Performance: 10x improvement"
git push origin main
```

**Step 7**: Manus approves
```bash
# Manus
git pull origin main
git add docs/reviews/20251218_new_feature_ITERATION_2_REVIEW.md
git commit -m "docs: Approve new feature iteration 2

- Reviewed by: Manus AI (X Agent, CTO)
- Verdict: Approved ✅
- Ready for: Production deployment"
git push origin main
```

---

## 6. Success Metrics

### 6.1 Process Efficiency

| Metric | Target | Measurement |
|--------|--------|-------------|
| Handoff clarity | 90%+ | Claude Code understands requirements without clarification |
| First-time success rate | 70%+ | Implementation meets criteria without iteration |
| Iteration cycles | ≤2 | Average number of back-and-forth rounds |
| Context preservation | 100% | No information lost between agents |

---

### 6.2 Quality Indicators

| Metric | Target | Measurement |
|--------|--------|-------------|
| Test pass rate | 95%+ | Percentage of tests passing after implementation |
| Code review approval | 90%+ | Percentage of implementations approved by Manus |
| Documentation completeness | 100% | All required sections in guides/reports filled |
| Commit message quality | 90%+ | Commits follow standards and include agent identification |

---

## 7. Troubleshooting

### 7.1 Common Issues

#### Issue 1: Claude Code doesn't understand guide

**Symptoms**:
- Claude Code asks many clarification questions
- Implementation deviates from requirements
- Test failures

**Root Cause**: Guide lacks sufficient detail or context

**Solution**:
1. Manus revises guide with more detail
2. Add code examples
3. Include visual diagrams if needed
4. Create iteration guide with clarifications

---

#### Issue 2: Manus can't review due to missing context

**Symptoms**:
- Manus asks questions about implementation decisions
- Review takes longer than expected
- Unclear why certain approaches were chosen

**Root Cause**: Implementation report lacks sufficient detail

**Solution**:
1. Claude Code updates report with more context
2. Explain "why" behind decisions
3. Include relevant logs/screenshots
4. Reference specific guide sections

---

#### Issue 3: Merge conflicts

**Symptoms**:
- Git push fails due to conflicts
- Both agents modified same files

**Root Cause**: Parallel work without coordination

**Solution**:
1. Alton coordinates work to avoid conflicts
2. Use branches for experimental work
3. Pull latest before starting new work
4. Communicate active work areas

---

## 8. Future Enhancements

### 8.1 Automation Opportunities

**Potential automations**:
1. **Auto-generate implementation report template** when Claude Code completes work
2. **Auto-link guides and reports** based on dates and task names
3. **Auto-run tests** and include results in reports
4. **Auto-notify** agents when new work is available

**Implementation**: GitHub Actions workflows

---

### 8.2 Tool Integration

**Potential integrations**:
1. **Slack/Discord bot** to notify agents of new work
2. **Dashboard** showing workflow status (guides pending, reports awaiting review)
3. **Metrics tracking** for process efficiency
4. **AI-powered** guide quality checker

---

## 9. Conclusion

This Multi-Agent Collaboration Protocol establishes a **structured, scalable, and transparent** workflow for Manus AI and Claude Code to collaborate effectively through GitHub.

**Key Benefits**:
- ✅ **Clear roles and responsibilities** - No confusion about who does what
- ✅ **Asynchronous collaboration** - Agents work independently, coordinate through GitHub
- ✅ **Full context preservation** - Nothing lost in translation
- ✅ **Audit trail** - Complete history of decisions and changes
- ✅ **Scalable** - Can add more agents following same protocol

**This is the Genesis Methodology applied to development workflow itself** - treating agent collaboration as a validation problem requiring clear roles, structured communication, and version tracking.

**The result**: A "Meta-Genesis" system that ensures high-quality, traceable, and efficient multi-agent collaboration.

---

## Appendix A: Quick Reference

### Manus Checklist (Creating Implementation Guide)

- [ ] Create guide in `/docs/implementation-guides/`
- [ ] Use filename format: `YYYYMMDD_<task>_IMPLEMENTATION_GUIDE.md`
- [ ] Include all required sections (Context, Objectives, Steps, Tests, Pitfalls)
- [ ] Provide code snippets and examples
- [ ] Define clear success criteria
- [ ] Commit with standard message format
- [ ] Notify Alton when ready

---

### Claude Code Checklist (Implementing)

- [ ] Pull latest from GitHub
- [ ] Read implementation guide thoroughly
- [ ] Make changes as specified
- [ ] Run all tests
- [ ] Create implementation report in `/docs/implementation-reports/`
- [ ] Use filename format: `YYYYMMDD_<task>_IMPLEMENTATION_REPORT.md`
- [ ] Include all required sections (Summary, Changes, Tests, Issues)
- [ ] Commit code + report with standard message format
- [ ] Notify Alton when complete

---

### Alton Checklist (Orchestrating)

- [ ] Review Manus's implementation guide
- [ ] Approve and notify Claude Code
- [ ] Monitor Claude Code's progress
- [ ] Review Claude Code's implementation report
- [ ] Request Manus review
- [ ] Make final decision (approve/iterate/reject)
- [ ] Update project status

---

## Appendix B: Template Files

All templates are available in `/docs/templates/`:
- `IMPLEMENTATION_GUIDE_TEMPLATE.md`
- `IMPLEMENTATION_REPORT_TEMPLATE.md`
- `ITERATION_GUIDE_TEMPLATE.md`
- `REVIEW_REPORT_TEMPLATE.md`
- `DECISION_RECORD_TEMPLATE.md`

---

**Version History**:
- v1.0.0 (2025-12-18): Initial protocol definition

**Authors**:
- Manus AI (X Agent, CTO)
- Alton Lee (Project Lead)

**License**: MIT (same as VerifiMind-PEAS project)
