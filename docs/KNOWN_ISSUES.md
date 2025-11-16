# Known Issues & Limitations

**VerifiMind Version**: 1.0.0
**Last Updated**: October 12, 2025
**Status**: Active Development

---

## 📋 Issue Categories

- 🔴 **Critical**: Blocks core functionality, needs immediate fix
- 🟡 **High**: Major limitation, workaround available
- 🟢 **Medium**: Minor issue, acceptable for now
- 🔵 **Low**: Enhancement opportunity, not blocking

---

## 🔴 Critical Issues

### 1. Iterative Improvement Not Applying Fixes

**Issue ID**: CRIT-001
**Severity**: 🔴 Critical
**Component**: Iterative Generation Engine
**File**: `src/generation/iterative_generator.py`

**Description**:
Reflection Agent identifies issues correctly, but iterations don't effectively fix them. Score remains stuck across iterations (e.g., 55.4/100 → 55.4/100 → 55.4/100).

**Example**:
```
Iteration 1: Score 55.4 - "Password hashing missing"
Iteration 2: Score 55.4 - "Password hashing missing" (not fixed)
Iteration 3: Score 55.4 - "Password hashing missing" (still not fixed)
```

**Root Cause**:
- `apply_improvements()` extracts issues as text
- Spec modification doesn't translate to actual code changes
- LLM regenerates similar code without applying specific fixes

**Impact**:
- Wasted API calls (2-3 iterations with no improvement)
- User expectations not met (quality doesn't improve)
- System appears broken

**Workaround**:
- Use completion guides to fix issues manually
- Ignore iteration scores, use v1.0 as foundation

**Proposed Fix**:
```python
async def apply_improvements(spec, issues):
    # Convert issues to actionable code modifications
    for issue in issues:
        if "password hashing" in issue.description:
            spec.security_features.append("bcrypt_password_hashing")
            spec.implementation_notes["auth_controller"] = "Use bcrypt.hash(password, 10)"

    # Pass specific implementation instructions to LLM
    spec.generation_context = build_generation_context(issues)
    return spec
```

**Status**: 🚧 In Progress
**Target Fix**: v1.1.0

---

### 2. Entity Detection Timeout

**Issue ID**: CRIT-002
**Severity**: 🔴 Critical
**Component**: Specification Builder
**File**: `verifimind_complete.py`, line 212

**Description**:
LLM-powered entity detection hangs indefinitely when trying to analyze concept and generate database entities.

**Example**:
```python
# This call never returns:
entities = await self._generate_entities_with_llm(idea, category)
# Timeout after 5+ minutes
```

**Root Cause**:
- Using GPT-4 for entity detection (slow model)
- No timeout configured
- Complex prompt with JSON parsing

**Impact**:
- Complete system hang
- Cannot test end-to-end flow
- Falls back to template (only users table)

**Workaround**:
- Use template fallback (automatic)
- Manually specify entities in config
- Skip LLM entity detection

**Proposed Fix**:
```python
# 1. Use faster model
llm_provider = LLMProviderFactory.create_provider(
    provider_type="openai",
    model="gpt-3.5-turbo"  # Faster!
)

# 2. Add timeout
async with asyncio.timeout(10):  # 10 second limit
    entities = await self._generate_entities_with_llm(...)

# 3. Simpler prompt (less JSON parsing)
```

**Status**: 🆘 Urgent
**Target Fix**: v1.0.1

---

## 🟡 High Priority Issues

### 3. Only Generates Users Table

**Issue ID**: HIGH-001
**Severity**: 🟡 High
**Component**: Database Schema Generator

**Description**:
Generated applications only include `users` table, missing domain-specific tables (orders, menu_items, etc.).

**Example**:
- Input: "Restaurant ordering system with menu and customizations"
- Output: Only `users` table (email, password, name)
- Missing: `orders`, `menu_items`, `order_items`, `customizations`

**Root Cause**:
- Entity detection fallback to template
- Template only includes user entity
- LLM entity detection timing out (see CRIT-002)

**Impact**:
- Generated app is generic, not domain-specific
- 60-80% of work left for user to complete
- Value proposition unclear

**Workaround**:
- Follow COMPLETION_GUIDE.md Phase 1
- Use Claude Code/Cursor to add tables
- Takes 15-20 minutes

**Proposed Fix**:
- Fix entity detection timeout (CRIT-002)
- Add pre-defined entity templates for common categories
- Allow manual entity specification in config

**Status**: 🚧 In Progress
**Dependencies**: CRIT-002

---

### 4. Anthropic API Not Working

**Issue ID**: HIGH-002
**Severity**: 🟡 High
**Component**: LLM Provider
**File**: `src/llm/llm_provider.py`

**Description**:
Anthropic Claude API returns 404 errors for all models despite valid API keys.

**Models Tested**:
- ❌ claude-3-opus-20240229 (404)
- ❌ claude-3-5-sonnet-20241022 (404)
- ❌ claude-3-5-sonnet-20240620 (404)
- ❌ claude-3-sonnet-20240229 (404)

**API Keys Tested**:
- sk-ant-api03-_XI8wp3KyZB0... (valid, no access)
- sk-ant-api03-lqKb2byeMMb7... (valid, no access)

**Error**:
```json
{
  "type": "not_found_error",
  "message": "model: claude-3-opus-20240229"
}
```

**Root Cause**:
- API keys don't have model access permissions
- Subscription level issue
- Model names might be incorrect

**Impact**:
- Cannot use Anthropic Claude
- Limited to OpenAI (single point of failure)
- No fallback if OpenAI unavailable

**Workaround**:
- Use OpenAI GPT-4 instead
- Local models (Ollama) as fallback

**Proposed Fix**:
- Verify Anthropic subscription level
- Contact Anthropic support for model access
- Update to correct model names when available

**Status**: 🔍 Investigating
**Blocke**r: External (Anthropic API access)

---

### 5. Quality Scores Inconsistent

**Issue ID**: HIGH-003
**Severity**: 🟡 High
**Component**: Reflection Agent
**File**: `src/agents/reflection_agent.py`

**Description**:
Quality scores don't always reflect actual code quality. LLM-generated code sometimes scores lower than template code.

**Example**:
```
Template Code:
- Lines: 387
- Quality: 64.9/100
- Security: 75/100

LLM-Generated Code:
- Lines: 450 (more code)
- Quality: 55.4/100 (worse score?)
- Security: 25/100 (worse security?)
```

**Root Cause**:
- LLM-generated code has more detailed comments → flagged as verbose
- LLM adds try-catch → flagged as "inconsistent error handling"
- Reflection Agent needs calibration

**Impact**:
- Users lose trust in scores
- Iteration logic stops too early
- Better code penalized

**Workaround**:
- Ignore overall score
- Focus on specific issues identified
- Manual code review

**Proposed Fix**:
- Recalibrate Reflection Agent scoring
- Adjust issue severity weights
- Add positive pattern recognition (good practices)

**Status**: 🔬 Analysis Needed

---

### 6. No Frontend Generation

**Issue ID**: HIGH-004
**Severity**: 🟡 High
**Component**: Frontend Generator

**Description**:
Frontend code is not generated. FrontendGenerator is a placeholder.

**Impact**:
- Users must build entire frontend from scratch
- No UI templates provided
- Value proposition reduced

**Workaround**:
- Follow COMPLETION_GUIDE.md Phase 5
- Use Claude Code/Cursor to create React app
- Takes 45-60 minutes

**Proposed Fix**:
- Implement basic React scaffolding
- Generate:
  - App.js with routing
  - Login/Register pages
  - API client setup
  - Basic styling (Tailwind)

**Status**: 📅 Planned for v1.2.0

---

## 🟢 Medium Priority Issues

### 7. Windows Console Encoding Issues

**Issue ID**: MED-001
**Severity**: 🟢 Medium (Fixed)
**Component**: Output formatting

**Description**:
Windows console (cp1252) couldn't display Unicode emojis, causing `UnicodeEncodeError`.

**Status**: ✅ Fixed in v1.0.0
**Solution**: Replaced all emojis with ASCII markers ([OK], [WARNING], etc.)

---

### 8. CS Agent False Positives (Concept Mode)

**Issue ID**: MED-002
**Severity**: 🟢 Medium (Fixed)
**Component**: CS Security Agent

**Description**:
CS Agent was blocking legitimate concepts due to aggressive pattern matching on natural language.

**Examples**:
- "order system" → Flagged as SQL keyword
- "select menu" → Flagged as SQL injection
- "user system" → Flagged as suspicious

**Status**: ✅ Fixed in v1.0.0
**Solution**: Dual-mode scanning (concept vs code)

---

### 9. Generated Code Missing Dependencies

**Issue ID**: MED-003
**Severity**: 🟢 Medium
**Component**: API Generator

**Description**:
Some generated files reference dependencies that don't exist.

**Example**:
```javascript
// src/controllers/auth.js
const Auth = require('../models/auth');  // File doesn't exist!
```

**Root Cause**:
- Template-based route/controller generation
- Not aware of actual models generated
- Inconsistency between generators

**Impact**:
- Runtime errors when testing
- User confusion
- Extra debugging time

**Workaround**:
- Check generated files manually
- Fix imports before running

**Proposed Fix**:
- Post-generation validation
- Cross-reference all imports
- Generate dependency graph

**Status**: 🔧 Needs Fix

---

### 10. No Deployment Automation

**Issue ID**: MED-004
**Severity**: 🟢 Medium
**Component**: Deployment Generator

**Description**:
Deployment configuration is not generated. DeploymentGenerator is a placeholder.

**Impact**:
- Users must configure deployment manually
- No Docker/Kubernetes configs
- No CI/CD pipelines

**Workaround**:
- Deploy manually to Railway, Render, Vercel
- Follow platform-specific docs

**Proposed Fix**:
- Generate Dockerfile
- Generate docker-compose.yml
- Generate GitHub Actions workflow
- Generate platform-specific configs (Vercel, Railway)

**Status**: 📅 Planned for v1.3.0

---

## 🔵 Low Priority Issues

### 11. No Test Generation

**Issue ID**: LOW-001
**Severity**: 🔵 Low
**Component**: Code Generator

**Description**:
Unit tests and integration tests are not generated.

**Impact**:
- Users must write tests manually
- Test coverage unknown
- Quality assurance manual

**Workaround**:
- Write tests using Jest (backend)
- Write tests using React Testing Library (frontend)

**Status**: 📅 Planned for v2.0.0

---

### 12. Limited Template Selection

**Issue ID**: LOW-002
**Severity**: 🔵 Low
**Component**: Template Selector

**Description**:
Only one template available: "basic_crud". No options for different architectures.

**Impact**:
- Limited flexibility
- One-size-fits-all approach
- No microservices, serverless, etc.

**Status**: 📅 Planned for v1.4.0

---

### 13. No Visual Editor

**Issue ID**: LOW-003
**Severity**: 🔵 Low
**Component**: User Interface

**Description**:
CLI-only interface. No web-based visual editor for concept refinement.

**Impact**:
- Less accessible for non-technical users
- No preview before generation
- Limited editing capabilities

**Status**: 📅 Planned for v2.0.0

---

### 14. No Version Control Integration

**Issue ID**: LOW-004
**Severity**: 🔵 Low
**Component**: Output Management

**Description**:
Generated code not automatically committed to git.

**Impact**:
- Users must manually initialize git
- No automatic versioning
- No integration with GitHub

**Workaround**:
```bash
cd output/AppName/versions/v1.2
git init
git add .
git commit -m "Initial commit from VerifiMind"
```

**Status**: 📅 Planned for v1.5.0

---

## 🐛 Bugs

### BUG-001: datetime.utcnow() Deprecation Warnings

**Severity**: 🔵 Low
**Component**: Multiple files

**Description**:
Python 3.13 deprecation warnings for `datetime.utcnow()`.

**Warning**:
```
DeprecationWarning: datetime.datetime.utcnow() is deprecated
Use datetime.datetime.now(datetime.UTC) instead
```

**Files Affected**:
- verifimind_complete.py (lines 96, 100, 187, 226)
- Various timestamp generation

**Fix**:
```python
# Replace:
datetime.utcnow()

# With:
datetime.now(datetime.UTC)
```

**Status**: ✏️ Minor fix needed

---

### BUG-002: Async Event Loop Conflict

**Severity**: 🟢 Medium (Fixed)
**Component**: Specification Builder

**Description**:
`asyncio.run()` called from within running event loop caused errors.

**Error**:
```
RuntimeError: asyncio.run() cannot be called from a running event loop
```

**Status**: ✅ Fixed in v1.0.0
**Solution**: Changed from `asyncio.run()` to `await` pattern

---

## 📊 Performance Issues

### PERF-001: Slow Iteration Time

**Current**: 30-40 seconds per iteration
**Target**: <20 seconds per iteration

**Causes**:
- Large LLM prompts
- Sequential file generation
- Full code regeneration each iteration

**Proposed Optimizations**:
- Use GPT-3.5-turbo for simple files
- Generate files in parallel
- Only regenerate changed files

---

### PERF-002: No Caching

**Impact**: Every generation hits LLM API (slow + expensive)

**Proposed Fix**:
- Cache common patterns
- Cache entity schemas
- Cache similar concepts

---

## 🔒 Security Concerns

### SEC-001: API Keys in .env File

**Severity**: 🟡 Medium
**Type**: Configuration

**Risk**:
- .env file could be accidentally committed
- API keys exposed in git history

**Mitigation**:
- .env is in .gitignore
- Documentation warns about this
- Consider secret management system

**Status**: ⚠️ Acceptable for now, improve in v2.0

---

### SEC-002: No Rate Limiting on VerifiMind Itself

**Severity**: 🟢 Low
**Type**: Resource Management

**Risk**:
- User could spam generations
- Exhaust API quotas
- High costs

**Mitigation**:
- Currently single-user system
- Add rate limiting when multi-user

**Status**: 📅 Planned for v2.0 (Multi-user)

---

## 🔧 Workarounds & Solutions

### General Workaround Strategy

For most issues, the recommended workflow is:

1. **Generate Foundation** (VerifiMind)
   - Get 40-60% scaffold in 2-3 minutes
   - Validated concept
   - Security features built-in

2. **Complete with AI** (Claude Code/Cursor)
   - Follow COMPLETION_GUIDE.md
   - Add domain-specific features
   - 2 hours to completion

3. **Polish & Test** (Manual)
   - Fix any remaining issues
   - Add tests
   - Deploy

This hybrid approach works well despite current limitations.

---

## 📈 Issue Tracking

### Issues by Severity

| Severity | Open | Fixed | Total |
|----------|------|-------|-------|
| 🔴 Critical | 2 | 0 | 2 |
| 🟡 High | 5 | 0 | 5 |
| 🟢 Medium | 4 | 2 | 6 |
| 🔵 Low | 4 | 0 | 4 |
| **Total** | **15** | **2** | **17** |

### Issues by Component

| Component | Issues |
|-----------|--------|
| Iterative Generator | 2 |
| LLM Provider | 1 |
| Code Generator | 4 |
| Reflection Agent | 1 |
| CS Agent | 1 (fixed) |
| Configuration | 2 |
| Output | 2 |
| UI | 2 |
| Performance | 2 |

---

## 📞 Reporting Issues

If you encounter a new issue:

1. **Check this document** - Issue might be known
2. **Check COMPLETION_GUIDE.md** - Workaround might exist
3. **Document clearly**:
   - Steps to reproduce
   - Expected vs actual behavior
   - Error messages
   - System info (OS, Python version)

---

## 🎯 Priority Fix Order

### v1.0.1 (Immediate)
1. CRIT-002: Entity detection timeout (blocking)
2. HIGH-003: Quality score calibration
3. BUG-001: datetime deprecation warnings

### v1.1.0 (Near-term)
1. CRIT-001: Iterative improvement effectiveness
2. HIGH-001: Domain-specific table generation
3. MED-003: Generated code dependencies

### v1.2.0 (Short-term)
1. HIGH-004: Frontend generation
2. MED-004: Deployment automation
3. PERF-001: Iteration speed optimization

---

**Document Maintenance**: This document is updated with each release. Last review: October 12, 2025.

**Next Review**: With v1.0.1 release

---

*See also*:
- `DEVELOPMENT_HISTORY.md` for historical context
- `ROADMAP.md` for planned fixes and features
- `CONTRIBUTING.md` for how to help fix issues
