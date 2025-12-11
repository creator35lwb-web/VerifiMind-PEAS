# Cursor Integration Guide

**How to Use VerifiMind-PEAS Methodology with Cursor AI IDE**

**Version**: 1.0  
**Last Updated**: December 11, 2025  
**Prerequisites**: Cursor installed (free or paid)

---

## Table of Contents

1. [Introduction](#introduction)
2. [Why Cursor?](#why-cursor)
3. [Quick Start](#quick-start)
4. [Step-by-Step Tutorial](#step-by-step-tutorial)
5. [Best Practices](#best-practices)
6. [Troubleshooting](#troubleshooting)
7. [FAQ](#faq)

---

## Introduction

**This guide teaches you how to apply the VerifiMind-PEAS methodology using Cursor AI IDE.**

**What you'll learn**:
- How to use Cursor with Genesis Master Prompts
- How Cursor automatically understands your codebase
- How to use Cursor as X, Z, or CS agent
- Best practices for IDE-integrated validation

**Time**: 15 minutes to read, immediate application

---

## Why Cursor?

### **Advantages of Cursor for VerifiMind-PEAS**

**1. Codebase Understanding**
- Cursor indexes your entire codebase automatically
- Understands project structure without manual prompting
- Perfect for validating existing projects

**2. IDE Integration**
- Work in your development environment
- No context switching between IDE and browser
- Can make code changes directly

**3. Multi-Model Support**
- Supports GPT-4, Claude, and other models
- Easy to switch between models for multi-model validation
- Perfect for X-Z-CS RefleXion Trinity

**4. Long Context**
- Can reference entire codebase in conversations
- Supports long Genesis Master Prompts
- Maintains conversation history

### **When to Use Cursor**

**Use Cursor for**:
- ✅ **Code-focused projects** (validating architecture, implementation)
- ✅ **Existing codebases** (refactoring, security audits)
- ✅ **Technical validation** (CS Security Agent)
- ✅ **Implementation work** (writing code based on validated concepts)

**Use other tools for**:
- **Claude.ai**: Conceptual validation (Z Guardian Agent)
- **Kimi**: Innovation and research (X Intelligent Agent)
- **Perplexity**: External validation (academic research)

**Best approach**: Use Cursor + web-based LLMs for complete validation.

---

## Quick Start

### **Method 1: Open Project + Ask**

**Step 1**: Open your project in Cursor

**Step 2**: Press `Cmd+K` (Mac) or `Ctrl+K` (Windows/Linux) to open Cursor chat

**Step 3**: Paste your Genesis Master Prompt:

```
I'm building a meditation timer app. Here's my Genesis Master Prompt:

[Paste entire Genesis Master Prompt]

Please act as CS Security Agent (security perspective) from the VerifiMind-PEAS methodology and analyze the security implications of this codebase.
```

**Step 4**: Cursor analyzes your code and applies the methodology!

**That's it!** Cursor will:
- ✅ Read your entire codebase
- ✅ Understand project structure
- ✅ Apply Genesis Methodology
- ✅ Provide security-focused validation

---

### **Method 2: Use Composer for Multi-File Changes**

**Step 1**: Press `Cmd+I` (Mac) or `Ctrl+I` (Windows/Linux) to open Composer

**Step 2**: Paste your Genesis Master Prompt + request:

```
I'm building a meditation timer app. Here's my Genesis Master Prompt:

[Paste entire Genesis Master Prompt]

Based on CS Security Agent recommendations, please:
1. Add input validation to all API endpoints
2. Implement rate limiting
3. Add CORS configuration
4. Add security headers

Make the necessary changes across multiple files.
```

**Step 3**: Cursor makes changes across your codebase!

---

## Step-by-Step Tutorial

### **Tutorial: Security Audit of Meditation App with Cursor**

**Scenario**: You've built a meditation timer app. You want to validate the security (CS Security Agent perspective).

**Time**: 45 minutes

---

### **Step 1: Prepare Your Genesis Master Prompt**

**Create** `meditation_app_genesis.md` in your project root:

```markdown
# Meditation App - Genesis Master Prompt

**Project**: Meditation Timer App for Busy Professionals  
**Creator**: [Your Name]  
**Started**: December 11, 2025

## Vision

Build a meditation timer app for busy professionals.

**Tech Stack**:
- Frontend: React + Tailwind CSS
- Backend: Node.js + Express
- Database: PostgreSQL
- Authentication: JWT

**Current State**:
- ✅ Frontend complete
- ✅ Backend API complete
- ✅ Authentication implemented
- ⏳ Security audit needed

## Architecture

**API Endpoints**:
- POST /api/auth/register
- POST /api/auth/login
- GET /api/sessions (get user's meditation history)
- POST /api/sessions (log completed session)
- GET /api/preferences
- PUT /api/preferences

**Database Schema**:
- users (id, email, password_hash, created_at)
- meditation_sessions (id, user_id, duration_minutes, completed_at)
- user_preferences (user_id, default_duration, sound_preference, notification_enabled)

## Security Concerns

**From Z Guardian Agent validation**:
1. Password storage must use bcrypt
2. JWT tokens must have expiration
3. SQL injection prevention needed
4. CORS configuration needed
5. Rate limiting needed
6. HTTPS enforcement needed

## Next Steps

1. Security audit with CS Security Agent
2. Implement security recommendations
3. Penetration testing
```

**Save in your project root.**

---

### **Step 2: Open Project in Cursor**

**Launch Cursor** and open your meditation app project.

**Cursor will automatically**:
- ✅ Index your codebase
- ✅ Understand project structure
- ✅ Be ready to analyze

---

### **Step 3: Start Security Audit**

**Press** `Cmd+K` (Mac) or `Ctrl+K` (Windows/Linux)

**Paste**:

```
I'm building a meditation timer app. Here's my Genesis Master Prompt:

[Paste entire Genesis Master Prompt from Step 1]

Please act as CS Security Agent (security perspective) from the VerifiMind-PEAS methodology and perform a comprehensive security audit of this codebase.

Analyze:
1. Authentication implementation (JWT, password hashing)
2. API endpoint security (input validation, authorization)
3. Database security (SQL injection, parameterized queries)
4. CORS configuration
5. Rate limiting
6. Security headers

For each issue found, provide:
- Severity (Critical, High, Medium, Low)
- Current implementation
- Recommended fix
- Code example
```

---

### **Step 4: Cursor Provides Security Audit**

**Cursor's Response** (example):

```
I'll act as CS Security Agent and perform a comprehensive security audit of your meditation app.

## Security Audit Report

### 1. Authentication Implementation

**File**: `server/auth.js`

**Issue 1: Weak Password Hashing**
- **Severity**: CRITICAL
- **Current**: Using bcrypt with 10 rounds
- **Problem**: 10 rounds is outdated (2025 standards require 12+ rounds)
- **Recommended**: Increase to 12 rounds

**Code Fix**:
```javascript
// Current (WEAK)
const hash = await bcrypt.hash(password, 10);

// Recommended (SECURE)
const hash = await bcrypt.hash(password, 12);
```

**Issue 2: JWT Token Never Expires**
- **Severity**: HIGH
- **Current**: JWT tokens have no expiration
- **Problem**: Stolen tokens valid forever
- **Recommended**: Set 7-day expiration

**Code Fix**:
```javascript
// Current (INSECURE)
const token = jwt.sign({ userId: user.id }, process.env.JWT_SECRET);

// Recommended (SECURE)
const token = jwt.sign(
  { userId: user.id },
  process.env.JWT_SECRET,
  { expiresIn: '7d' }
);
```

### 2. API Endpoint Security

**File**: `server/routes/sessions.js`

**Issue 3: No Input Validation**
- **Severity**: HIGH
- **Current**: No validation on POST /api/sessions
- **Problem**: Can submit invalid data (negative duration, etc.)
- **Recommended**: Add input validation with Joi or Zod

**Code Fix**:
```javascript
// Current (INSECURE)
app.post('/api/sessions', async (req, res) => {
  const { duration_minutes } = req.body;
  // No validation!
  await db.query('INSERT INTO meditation_sessions ...');
});

// Recommended (SECURE)
const Joi = require('joi');

const sessionSchema = Joi.object({
  duration_minutes: Joi.number().integer().min(1).max(120).required()
});

app.post('/api/sessions', async (req, res) => {
  const { error, value } = sessionSchema.validate(req.body);
  if (error) return res.status(400).json({ error: error.details[0].message });
  
  const { duration_minutes } = value;
  await db.query('INSERT INTO meditation_sessions ...');
});
```

**Issue 4: Missing Authorization Check**
- **Severity**: CRITICAL
- **Current**: No check if user owns the session they're accessing
- **Problem**: User A can access User B's meditation history
- **Recommended**: Add authorization middleware

**Code Fix**:
```javascript
// Current (INSECURE)
app.get('/api/sessions', async (req, res) => {
  const sessions = await db.query('SELECT * FROM meditation_sessions WHERE user_id = $1', [req.user.id]);
  res.json(sessions);
});

// Recommended (SECURE)
app.get('/api/sessions', authenticateToken, async (req, res) => {
  // authenticateToken middleware verifies JWT and sets req.user
  const sessions = await db.query('SELECT * FROM meditation_sessions WHERE user_id = $1', [req.user.id]);
  res.json(sessions);
});
```

### 3. Database Security

**File**: `server/db.js`

**Issue 5: SQL Injection Vulnerability**
- **Severity**: CRITICAL
- **Current**: String concatenation in queries
- **Problem**: Allows SQL injection attacks
- **Recommended**: Use parameterized queries

**Code Fix**:
```javascript
// Current (VULNERABLE)
const email = req.body.email;
const query = `SELECT * FROM users WHERE email = '${email}'`;
// Attacker can input: ' OR '1'='1

// Recommended (SECURE)
const email = req.body.email;
const query = 'SELECT * FROM users WHERE email = $1';
const result = await db.query(query, [email]);
```

### 4. CORS Configuration

**File**: `server/index.js`

**Issue 6: CORS Allows All Origins**
- **Severity**: HIGH
- **Current**: `cors({ origin: '*' })`
- **Problem**: Any website can make requests to your API
- **Recommended**: Restrict to your frontend domain

**Code Fix**:
```javascript
// Current (INSECURE)
app.use(cors({ origin: '*' }));

// Recommended (SECURE)
app.use(cors({
  origin: process.env.FRONTEND_URL || 'https://yourdomain.com',
  credentials: true
}));
```

### 5. Rate Limiting

**File**: `server/index.js`

**Issue 7: No Rate Limiting**
- **Severity**: MEDIUM
- **Current**: No rate limiting on any endpoint
- **Problem**: Vulnerable to brute force attacks, DDoS
- **Recommended**: Add rate limiting with express-rate-limit

**Code Fix**:
```javascript
// Install: npm install express-rate-limit

const rateLimit = require('express-rate-limit');

// General rate limit
const generalLimiter = rateLimit({
  windowMs: 15 * 60 * 1000, // 15 minutes
  max: 100 // 100 requests per 15 minutes
});

// Strict rate limit for auth endpoints
const authLimiter = rateLimit({
  windowMs: 15 * 60 * 1000,
  max: 5 // 5 login attempts per 15 minutes
});

app.use('/api/', generalLimiter);
app.use('/api/auth/', authLimiter);
```

### 6. Security Headers

**File**: `server/index.js`

**Issue 8: Missing Security Headers**
- **Severity**: MEDIUM
- **Current**: No security headers
- **Problem**: Vulnerable to XSS, clickjacking, etc.
- **Recommended**: Add helmet middleware

**Code Fix**:
```javascript
// Install: npm install helmet

const helmet = require('helmet');

app.use(helmet({
  contentSecurityPolicy: {
    directives: {
      defaultSrc: ["'self'"],
      styleSrc: ["'self'", "'unsafe-inline'"],
      scriptSrc: ["'self'"],
      imgSrc: ["'self'", "data:", "https:"],
    },
  },
}));
```

## Summary

**Total Issues Found**: 8
- **Critical**: 3 (SQL injection, no authorization, weak password hashing)
- **High**: 3 (no JWT expiration, no input validation, CORS misconfiguration)
- **Medium**: 2 (no rate limiting, missing security headers)

**Recommended Actions** (Priority Order):
1. Fix SQL injection (CRITICAL)
2. Add authorization checks (CRITICAL)
3. Increase bcrypt rounds (CRITICAL)
4. Add JWT expiration (HIGH)
5. Add input validation (HIGH)
6. Fix CORS configuration (HIGH)
7. Add rate limiting (MEDIUM)
8. Add security headers (MEDIUM)

**Estimated Time**: 4-6 hours to implement all fixes

Would you like me to implement these fixes using Composer?
```

---

### **Step 5: Implement Fixes with Composer**

**Press** `Cmd+I` (Mac) or `Ctrl+I` (Windows/Linux) to open Composer

**Paste**:

```
Based on the CS Security Agent audit, please implement all 8 security fixes:

1. Increase bcrypt rounds to 12
2. Add JWT expiration (7 days)
3. Add input validation with Joi
4. Add authorization middleware
5. Fix SQL injection (use parameterized queries)
6. Fix CORS configuration
7. Add rate limiting
8. Add helmet security headers

Make the necessary changes across all files.
```

**Cursor will**:
- ✅ Make changes across multiple files
- ✅ Show you a diff of all changes
- ✅ Let you accept or reject each change

---

### **Step 6: Update Genesis Master Prompt**

**After implementing fixes, update your Genesis Master Prompt**:

```markdown
# Meditation App - Genesis Master Prompt

[... previous sections ...]

## Decisions Made

### **Decision 1: Security Fixes Implemented**
- **What**: Implemented all 8 security recommendations from CS Security Agent
- **Why**: Critical vulnerabilities identified (SQL injection, no authorization, weak hashing)
- **Changes**:
  1. ✅ Increased bcrypt rounds to 12
  2. ✅ Added JWT expiration (7 days)
  3. ✅ Added input validation with Joi
  4. ✅ Added authorization middleware
  5. ✅ Fixed SQL injection (parameterized queries)
  6. ✅ Fixed CORS configuration
  7. ✅ Added rate limiting
  8. ✅ Added helmet security headers
- **Rationale**: Security from day one (not an afterthought)

## Next Steps

1. Penetration testing (validate fixes)
2. Deploy to production (HTTPS enforced)
3. Monitor security logs
```

**Save the updated Genesis Master Prompt.**

---

## Best Practices

### **1. Use Cursor for Code-Focused Validation**

**Cursor is best for**:
- ✅ Security audits (CS Security Agent)
- ✅ Code refactoring
- ✅ Implementation work

**Use web-based LLMs for**:
- **Claude.ai**: Conceptual validation (Z Guardian Agent)
- **Kimi**: Innovation (X Intelligent Agent)

---

### **2. Keep Genesis Master Prompt in Project Root**

**Create** `genesis_master_prompt.md` in your project root.

**Benefits**:
- ✅ Easy to find and update
- ✅ Version controlled with Git
- ✅ Team members can access

---

### **3. Use Composer for Multi-File Changes**

**Composer** (`Cmd+I` / `Ctrl+I`) is perfect for:
- ✅ Implementing security fixes across multiple files
- ✅ Refactoring architecture
- ✅ Adding new features

**Chat** (`Cmd+K` / `Ctrl+K`) is perfect for:
- ✅ Analysis and validation
- ✅ Asking questions
- ✅ Getting recommendations

---

### **4. Switch Models for Different Agents**

**Cursor supports multiple models**:
- **GPT-4**: Best for technical implementation (X Intelligent Agent, CS Security Agent)
- **Claude**: Best for ethics and safety (Z Guardian Agent)

**How to switch**:
1. Open Cursor settings
2. Select model (GPT-4 or Claude)
3. Use different models for different agent roles

---

### **5. Review All Changes Before Accepting**

**Cursor can make mistakes!**

**Always**:
- ✅ Review diffs carefully
- ✅ Test changes locally
- ✅ Run security tests
- ✅ Commit incrementally

**Never**:
- ❌ Accept all changes blindly
- ❌ Skip testing
- ❌ Commit without review

---

## Troubleshooting

### **Problem 1: Cursor Doesn't Understand Codebase**

**Symptom**: Cursor provides generic advice instead of codebase-specific analysis.

**Solution**: Re-index codebase:

1. Open Cursor settings
2. Click "Re-index codebase"
3. Wait for indexing to complete
4. Try again

---

### **Problem 2: Cursor Makes Incorrect Changes**

**Symptom**: Composer makes changes that break the code.

**Solution**: Reject changes and provide more context:

```
The changes you made broke the authentication flow. Here's the error:

[Paste error message]

Please fix the issue while maintaining the security improvements.
```

---

### **Problem 3: Cursor Doesn't Apply Methodology**

**Symptom**: Cursor provides generic code review instead of VerifiMind-PEAS validation.

**Solution**: Be explicit about the methodology:

```
Please act as CS Security Agent from the VerifiMind-PEAS methodology.

The VerifiMind-PEAS methodology is a systematic 5-step multi-model validation process. Your role as CS Security Agent is to:
1. Identify security vulnerabilities
2. Assess severity (Critical, High, Medium, Low)
3. Provide specific code fixes
4. Explain rationale

Please perform a comprehensive security audit of this codebase.
```

---

### **Problem 4: Genesis Master Prompt Too Long**

**Symptom**: Cursor truncates Genesis Master Prompt.

**Solution**: Summarize in chat, link to full document:

```
I'm building a meditation timer app. Full context in genesis_master_prompt.md (in project root).

Summary:
- Tech stack: React + Node.js + PostgreSQL
- Current phase: Security audit
- Previous validations: X Intelligent Agent (innovation), Z Guardian Agent (ethics)

Please act as CS Security Agent and perform security audit.
```

---

## FAQ

### **Q1: Do I need a paid Cursor account?**

**A**: Free tier works, but paid is recommended for VerifiMind-PEAS.

**Free tier**:
- ✅ 50 chat messages per month
- ✅ Basic features
- ⚠️ May not be enough for full validation

**Paid tier** (Cursor Pro, $20/month):
- ✅ Unlimited chat messages
- ✅ Unlimited Composer uses
- ✅ Priority support
- ✅ **Recommended for VerifiMind-PEAS**

---

### **Q2: Can I use Cursor for all three agents (X, Z, CS)?**

**A**: Yes, but not recommended.

**Cursor is best for**:
- ✅ **CS Security Agent** (security) - **BEST**
- ✅ **X Intelligent Agent** (implementation) - **GOOD**
- ⚠️ **Z Guardian Agent** (ethics) - **OKAY**

**Recommendation**: Use Cursor for CS (security) and X (implementation), use Claude.ai for Z (ethics).

**Why**: Multi-model validation requires diverse perspectives. Using only Cursor = single-model bias.

---

### **Q3: How do I switch between agent roles in Cursor?**

**A**: Start a new chat for each agent role.

**Method 1**: Clear chat history
- Press `Cmd+K` / `Ctrl+K`
- Click "Clear chat"
- Start new conversation with different agent role

**Method 2**: Use separate chat windows
- Open multiple Cursor windows
- Use each window for different agent role

**Tip**: Document which model/agent was used for each validation in Genesis Master Prompt.

---

### **Q4: Can Cursor access my private repositories?**

**A**: Cursor only accesses files you open locally.

**Cursor**:
- ✅ Indexes files in your local project
- ✅ Can read any file you open
- ❌ Cannot access remote repositories
- ❌ Cannot make commits (you control Git)

**Privacy**: Your code stays local unless you explicitly share.

---

### **Q5: How do I use Cursor with Genesis Master Prompts?**

**A**: Three approaches:

**Approach 1**: Paste in chat
```
Here's my Genesis Master Prompt:

[Paste entire prompt]

Please act as CS Security Agent...
```

**Approach 2**: Save in project root
```
Full context in genesis_master_prompt.md (project root).

Please read it and act as CS Security Agent...
```

**Approach 3**: Summarize key points
```
Summary of Genesis Master Prompt:
- Project: Meditation timer app
- Tech stack: React + Node.js + PostgreSQL
- Current phase: Security audit

Please act as CS Security Agent...
```

---

### **Q6: Can I use Cursor with other VerifiMind-PEAS tools?**

**A**: Yes! Cursor works great with other tools.

**Recommended workflow**:
1. **Conceptual validation**: Claude.ai (Z Guardian Agent)
2. **Innovation**: Kimi (X Intelligent Agent)
3. **Implementation**: Cursor (CS Security Agent + coding)
4. **Research**: Perplexity (external validation)

**Cursor is one tool in your VerifiMind-PEAS toolkit.**

---

## Conclusion

**Cursor is an excellent choice for code-focused VerifiMind-PEAS validation**, especially for security audits (CS Security Agent) and implementation work.

**Key Takeaways**:
- ✅ Cursor excels at codebase analysis and security audits
- ✅ IDE integration enables seamless validation + implementation
- ✅ Composer enables multi-file changes
- ✅ Best used in combination with web-based LLMs (Claude, Kimi)

**Next Steps**:
1. Read [Genesis Master Prompt Guide](GENESIS_MASTER_PROMPT_GUIDE.md)
2. Create your Genesis Master Prompt
3. Open your project in Cursor
4. Start validating!
5. Use other LLMs for multi-model validation

**Questions?** Join the discussion on [GitHub](https://github.com/creator35lwb-web/VerifiMind-PEAS/discussions) or reach out on [Twitter/X](https://x.com/creator35lwb).

**Happy coding!** 🚀

---

**Author**: Alton Lee Wei Bin (creator35lwb)  
**Version**: 1.0  
**Last Updated**: December 11, 2025  
**License**: MIT License
