# Generic LLM Integration Guide

**How to Use VerifiMind-PEAS Methodology with Any LLM**

**Version**: 1.0  
**Last Updated**: December 11, 2025  
**Prerequisites**: Access to any LLM (free or paid)

---

## Table of Contents

1. [Introduction](#introduction)
2. [Supported LLMs](#supported-lms)
3. [Quick Start](#quick-start)
4. [Step-by-Step Tutorial](#step-by-step-tutorial)
5. [Multi-Model Validation Workflow](#multi-model-validation-workflow)
6. [Best Practices](#best-practices)
7. [Troubleshooting](#troubleshooting)
8. [FAQ](#faq)

---

## Introduction

**This guide teaches you how to apply the VerifiMind-PEAS methodology with ANY LLM.**

**What you'll learn**:
- How to use Genesis Master Prompts with any AI tool
- How to assign agent roles (X, Z, CS) to different LLMs
- How to orchestrate multi-model validation
- Platform-agnostic best practices

**Time**: 15 minutes to read, works with any LLM

---

## Supported LLMs

**VerifiMind-PEAS works with ANY LLM that accepts text input.**

### **Tested and Recommended**

**Tier 1** (Excellent for VerifiMind-PEAS):
- ✅ **Claude** (Anthropic) - Best for ethics (Z Guardian Agent)
- ✅ **GPT-4** (OpenAI) - Best for implementation (X Intelligent Agent, CS Security Agent)
- ✅ **Gemini** (Google) - Best for research and analysis
- ✅ **Kimi** (Moonshot AI) - Best for innovation (X Intelligent Agent)

**Tier 2** (Good for VerifiMind-PEAS):
- ✅ **Grok** (xAI) - Good for alternative perspectives
- ✅ **Qwen** (Alibaba) - Good for multilingual support
- ✅ **Perplexity** - Good for external validation (research)
- ✅ **DeepSeek** - Good for technical analysis

**Tier 3** (Experimental):
- ⚠️ **Llama** (Meta) - Open-source, self-hosted
- ⚠️ **Mistral** - Open-source, European alternative
- ⚠️ **Other open-source models** - Varies by quality

### **Model Selection Guide**

**For X Intelligent Agent (Innovation)**:
- **Best**: Kimi, GPT-4, Gemini
- **Why**: Creative, strategic thinking

**For Z Guardian Agent (Ethics)**:
- **Best**: Claude, GPT-4
- **Why**: Strong safety and alignment training

**For CS Security Agent (Security)**:
- **Best**: GPT-4, Claude
- **Why**: Technical depth, security knowledge

**Recommended combination**: Kimi (X) + Claude (Z) + GPT-4 (CS)

---

## Quick Start

### **Universal 3-Step Process**

**This works with ANY LLM:**

---

### **Step 1: Create Genesis Master Prompt**

**Create** `project_genesis.md`:

```markdown
# [Project Name] - Genesis Master Prompt

**Project**: [One-line description]  
**Creator**: [Your name]  
**Started**: [Date]

## Vision

[What you're building and why]

## Current State

**Phase**: [Current phase]  
**Status**: [Current status]

## Decisions Made

[Key decisions and rationale]

## Open Questions

1. [Question 1]
2. [Question 2]

## Next Steps

1. [Next step 1]
2. [Next step 2]
```

**See**: [Genesis Master Prompt Guide](GENESIS_MASTER_PROMPT_GUIDE.md) for detailed template

---

### **Step 2: Paste to LLM + Assign Agent Role**

**Open any LLM** (Claude, GPT, Kimi, etc.)

**Paste**:

```
I'm building [project name]. Here's my Genesis Master Prompt:

[Paste entire Genesis Master Prompt]

Please act as [X Intelligent Agent / Z Guardian Agent / CS Security Agent] from the VerifiMind-PEAS methodology and provide [innovation / ethics / security] validation.
```

**Replace**:
- `[project name]`: Your project name
- `[X Intelligent Agent / Z Guardian Agent / CS Security Agent]`: Choose agent role
- `[innovation / ethics / security]`: Choose focus area

---

### **Step 3: Update Genesis Master Prompt**

**After LLM provides validation**:
1. Review recommendations
2. Make decisions
3. **Update Genesis Master Prompt** with:
   - Decisions made
   - Rationale
   - Next steps
4. Save for next session

**Repeat** with different LLMs for multi-model validation!

---

## Step-by-Step Tutorial

### **Tutorial: Multi-Model Validation of Meditation App**

**Scenario**: You're building a meditation timer app. You want to validate with X, Z, and CS agents using different LLMs.

**Time**: 60 minutes  
**LLMs**: Kimi (X), Claude (Z), GPT-4 (CS)

---

### **Step 1: Create Genesis Master Prompt**

**Create** `meditation_app_genesis.md`:

```markdown
# Meditation App - Genesis Master Prompt

**Project**: Meditation Timer App for Busy Professionals  
**Creator**: [Your Name]  
**Started**: December 11, 2025

## Vision

Build a meditation timer app for busy professionals who want to meditate but "don't have time."

**Key Features**:
- Ultra-short sessions (3, 5, 10 minutes)
- Office-friendly sounds (no chanting)
- Desktop notifications (remind during work)
- Simple streak tracking

**Target Users**: Busy professionals

**Success Criteria**: Users meditate at least 3x per week

## Current State

**Phase**: Concept validation  
**Status**: Seeking multi-model validation

## Open Questions

1. Is this concept innovative enough?
2. Are there ethical concerns?
3. What security considerations apply?

## Next Steps

1. Validate with X Intelligent Agent (innovation)
2. Validate with Z Guardian Agent (ethics)
3. Validate with CS Security Agent (security)
4. Synthesize perspectives and make decisions
```

---

### **Step 2: Validate with X Intelligent Agent (Kimi)**

**Open Kimi** (kimi.moonshot.cn)

**Paste**:

```
I'm building a meditation timer app. Here's my Genesis Master Prompt:

[Paste entire Genesis Master Prompt]

Please act as X Intelligent Agent (innovation perspective) from the VerifiMind-PEAS methodology and help me validate this concept.

Analyze:
1. Innovation potential (is this differentiated?)
2. Market opportunity (is there demand?)
3. Technical feasibility (can this be built?)
4. Strategic recommendations (how to improve?)
```

**Kimi's Response** (example):

```
As X Intelligent Agent, here's my innovation analysis:

## Innovation Assessment

**Differentiation**: 7/10
- Ultra-short sessions (3-5 min) differentiate from Headspace (10-30 min)
- Office-friendly positioning is unique
- BUT: Meditation apps are crowded market

**Market Opportunity**: 8/10
- "Busy professionals" is large, underserved segment
- Pain point is real ("I don't have time")
- Willingness to pay is high (professional demographic)

**Technical Feasibility**: 9/10
- Simple tech stack (React + Node.js)
- No complex AI or ML required
- Can build MVP in 2-4 weeks

**Strategic Recommendations**:
1. **Niche down further**: "Meditation for software engineers" or "Meditation for managers"
2. **Add unique feature**: Integration with calendar (auto-schedule meditation breaks)
3. **Freemium model**: Free 5-min sessions, paid for 3-min and 10-min
4. **B2B opportunity**: Sell to companies (employee wellness programs)

**Innovation Score**: 7.5/10 (Good, with room for improvement)
```

**Update Genesis Master Prompt** with Kimi's insights.

---

### **Step 3: Validate with Z Guardian Agent (Claude)**

**Open Claude** (claude.ai)

**Paste**:

```
I'm building a meditation timer app. Here's my updated Genesis Master Prompt:

[Paste updated Genesis Master Prompt with Kimi's insights]

Please act as Z Guardian Agent (ethics perspective) from the VerifiMind-PEAS methodology and help me validate the ethical alignment of this concept.

Analyze:
1. Ethical concerns (wellness washing, accessibility, etc.)
2. Privacy implications (tracking meditation habits)
3. Inclusivity (is "busy professionals" too narrow?)
4. Recommendations for ethical alignment
```

**Claude's Response** (example):

```
As Z Guardian Agent, here's my ethics analysis:

## Ethical Assessment

**Concern 1: Wellness Washing**
- Positioning meditation as "productivity tool" may oversimplify practice
- Risk of reinforcing hustle culture
- **Recommendation**: Frame as "well-being practice" first

**Concern 2: Privacy**
- Tracking meditation habits is sensitive personal data
- Could be misused by employers
- **Recommendation**: Local storage by default, opt-in cloud sync

**Concern 3: Inclusivity**
- "Busy professionals" excludes other demographics
- 5-minute sessions may not work for everyone
- **Recommendation**: Use "anyone with a busy schedule", offer 1-15 min options

**Concern 4: Accessibility**
- No mention of screen reader support, keyboard navigation
- **Recommendation**: Build with WCAG 2.1 AA compliance

**Ethical Alignment**: 6/10 (Needs improvement)

**Recommendations**:
1. Revise positioning (well-being, not productivity)
2. Privacy-first design (local storage default)
3. Inclusive language and features
4. Accessibility from day one
```

**Update Genesis Master Prompt** with Claude's insights.

---

### **Step 4: Validate with CS Security Agent (GPT-4)**

**Open GPT-4** (chat.openai.com)

**Paste**:

```
I'm building a meditation timer app. Here's my updated Genesis Master Prompt:

[Paste updated Genesis Master Prompt with Kimi + Claude insights]

Please act as CS Security Agent (security perspective) from the VerifiMind-PEAS methodology and help me identify security considerations.

Analyze:
1. Authentication security (if user accounts)
2. Data security (meditation history)
3. API security (if backend)
4. Client-side security (if web app)
5. Recommendations for secure implementation
```

**GPT-4's Response** (example):

```
As CS Security Agent, here's my security analysis:

## Security Assessment

**Authentication**:
- If implementing user accounts: Use bcrypt (12+ rounds), JWT with expiration
- Consider OAuth (Google, Apple) for easier onboarding
- **Recommendation**: Implement 2FA for premium users

**Data Security**:
- Meditation history is sensitive (mental health data)
- **Recommendation**: Encrypt at rest (AES-256), encrypt in transit (TLS 1.3)
- **Recommendation**: Implement data export and deletion (GDPR compliance)

**API Security**:
- If backend API: Implement rate limiting, input validation, CORS
- **Recommendation**: Use API gateway (AWS API Gateway, Cloudflare)

**Client-Side Security**:
- If web app: Implement CSP headers, XSS protection
- **Recommendation**: Use helmet.js, sanitize user input

**Security Score**: 5/10 (Needs security-first design)

**Recommendations**:
1. Design security architecture before coding
2. Use security checklist (OWASP Top 10)
3. Implement logging and monitoring
4. Plan for security audits and penetration testing
```

**Update Genesis Master Prompt** with GPT-4's insights.

---

### **Step 5: Synthesize Perspectives**

**Now you have three perspectives**:
- **X (Kimi)**: Innovation score 7.5/10, strategic recommendations
- **Z (Claude)**: Ethics score 6/10, ethical concerns
- **CS (GPT-4)**: Security score 5/10, security requirements

**Your role as human orchestrator**:
1. **Synthesize**: What are the common themes?
2. **Prioritize**: What's most important?
3. **Decide**: What will you implement?
4. **Document**: Update Genesis Master Prompt with decisions

**Example synthesis**:

```markdown
## Synthesis (Human Orchestrator)

**Common Themes**:
1. All three agents agree: Concept is viable but needs refinement
2. Innovation (X): Differentiation is good, but can be stronger
3. Ethics (Z): Positioning and privacy need attention
4. Security (CS): Security-first design is critical

**Priorities**:
1. **HIGH**: Revise positioning (well-being, not productivity) - Ethics concern
2. **HIGH**: Design security architecture - Security concern
3. **MEDIUM**: Privacy-first design (local storage) - Ethics + Security
4. **MEDIUM**: Niche down further (e.g., "for software engineers") - Innovation
5. **LOW**: B2B opportunity - Innovation (future phase)

**Decisions Made**:

### Decision 1: Ethical Positioning
- **What**: Frame as "well-being practice" (not "productivity tool")
- **Why**: Z Guardian Agent identified wellness washing risk
- **Revised Positioning**: "Meditation for well-being, designed for busy schedules"

### Decision 2: Security-First Architecture
- **What**: Design security architecture before coding
- **Why**: CS Security Agent identified critical security gaps
- **Implementation**: Use OWASP checklist, bcrypt, JWT, rate limiting, encryption

### Decision 3: Privacy-First Design
- **What**: Local storage by default, opt-in cloud sync
- **Why**: Z Guardian Agent + CS Security Agent both emphasized privacy
- **Implementation**: IndexedDB for local storage, end-to-end encryption for cloud

### Decision 4: Target Audience Refinement
- **What**: "Meditation for software engineers" (niche down)
- **Why**: X Intelligent Agent recommended stronger differentiation
- **Rationale**: Software engineers are high-stress, high-income, tech-savvy

## Next Steps

1. Create security architecture document
2. Design privacy-first data model
3. Revise marketing copy (ethical positioning)
4. Build MVP with security + privacy built-in
```

**Update Genesis Master Prompt** with synthesis and decisions.

---

## Multi-Model Validation Workflow

### **The Complete Workflow**

**This is the core VerifiMind-PEAS process:**

```
1. CREATE Genesis Master Prompt
   ↓
2. VALIDATE with X Intelligent Agent (Innovation)
   - Use: Kimi, GPT-4, or Gemini
   - Focus: Innovation, strategy, market opportunity
   ↓
3. UPDATE Genesis Master Prompt
   ↓
4. VALIDATE with Z Guardian Agent (Ethics)
   - Use: Claude or GPT-4
   - Focus: Ethics, privacy, accessibility, inclusivity
   ↓
5. UPDATE Genesis Master Prompt
   ↓
6. VALIDATE with CS Security Agent (Security)
   - Use: GPT-4 or Claude
   - Focus: Security, vulnerabilities, threat modeling
   ↓
7. UPDATE Genesis Master Prompt
   ↓
8. SYNTHESIZE perspectives (Human Orchestrator)
   - Identify common themes
   - Prioritize recommendations
   - Make decisions
   ↓
9. UPDATE Genesis Master Prompt with decisions
   ↓
10. ITERATE (repeat for next phase)
```

### **Why This Works**

**Diverse perspectives**:
- Each LLM has different training data, architecture, optimization
- Different LLMs = different "subjective experiences"
- Synthesizing diverse perspectives = more objective validation

**Human-at-center**:
- AI provides perspectives
- **Human synthesizes and decides**
- Human documents decisions in Genesis Master Prompt

**Continuous improvement**:
- Genesis Master Prompt evolves with project
- Each iteration builds on previous learnings
- Project memory maintained across sessions

---

## Best Practices

### **1. Use At Least 2-3 LLMs**

**Minimum**: 2 LLMs (e.g., Kimi + Claude)  
**Recommended**: 3 LLMs (e.g., Kimi + Claude + GPT-4)  
**Optimal**: 4+ LLMs (add Gemini, Grok, Perplexity)

**Why**: Single-model bias is real. Multiple models provide diverse perspectives.

---

### **2. Assign Specific Agent Roles**

**Don't**:
```
What do you think about my meditation app?
```

**Do**:
```
Please act as X Intelligent Agent (innovation perspective) from the VerifiMind-PEAS methodology and analyze the innovation potential of this concept.
```

**Why**: Specific role prompting ensures consistent methodology application.

---

### **3. Update Genesis Master Prompt After Every Session**

**After EVERY LLM conversation**:
1. Review recommendations
2. Make decisions (or note for later)
3. **Update Genesis Master Prompt**
4. Save file

**Why**: Maintains project continuity, prevents repeating discussions.

---

### **4. Document Decisions with Rationale**

**Don't**:
```
## Decisions Made
- Use React
```

**Do**:
```
## Decisions Made

### Decision 1: Tech Stack
- **What**: React + Tailwind CSS (frontend)
- **Why**: X Intelligent Agent recommended modern, well-supported stack
- **Alternative considered**: Vue, plain HTML/CSS/JS
- **Rationale**: React has best ecosystem for future growth
```

**Why**: Future you (or team members) will thank you for documenting rationale.

---

### **5. Synthesize, Don't Just Collect**

**Don't**:
- Collect recommendations from 3 LLMs
- Implement everything blindly

**Do**:
- Collect recommendations from 3 LLMs
- **Identify common themes**
- **Prioritize** based on your values and constraints
- **Make decisions** as human orchestrator
- **Document** synthesis in Genesis Master Prompt

**Why**: You're the orchestrator, not a passive collector. AI assists, you decide.

---

## Troubleshooting

### **Problem 1: LLM Doesn't Apply Methodology**

**Symptom**: LLM provides generic advice instead of VerifiMind-PEAS validation.

**Solution**: Be more explicit:

```
Please act as X Intelligent Agent from the VerifiMind-PEAS methodology.

The VerifiMind-PEAS methodology is a systematic 5-step multi-model validation process:
1. Initial Conceptualization
2. Critical Scrutiny (your role)
3. External Validation
4. Synthesis
5. Iteration

As X Intelligent Agent, your role is to provide innovation-focused analysis:
- Assess differentiation and market opportunity
- Evaluate technical feasibility
- Provide strategic recommendations

Please analyze this concept from an innovation perspective.
```

---

### **Problem 2: Conflicting Recommendations**

**Symptom**: Kimi says "do A", Claude says "do B", GPT-4 says "do C".

**Solution**: This is a feature, not a bug!

**Conflicting recommendations mean**:
- Multiple valid perspectives exist
- Trade-offs need to be considered
- Human judgment is required

**Your role**:
1. Understand each perspective
2. Identify trade-offs
3. Make decision based on your values and priorities
4. Document decision in Genesis Master Prompt

**Example**:
- **Kimi**: "Use microservices for scalability"
- **Claude**: "Start with monolith for simplicity"
- **GPT-4**: "Use serverless for cost efficiency"
- **You**: "Start with monolith (MVP speed), plan for microservices later (document in Genesis Master Prompt)"

---

### **Problem 3: Genesis Master Prompt Gets Too Long**

**Symptom**: Genesis Master Prompt exceeds 50 pages, hard to maintain.

**Solution**: Split into multiple documents:

**Main prompt** (`project_genesis.md`, 5-10 pages):
```markdown
# Project Genesis Master Prompt

[Vision, current state, decisions, next steps]

## Technical Details

See [Technical Architecture](technical_architecture.md) for detailed system design.

## Research Findings

See [Research](research.md) for academic papers and competitor analysis.
```

**Separate documents**:
- `technical_architecture.md` (detailed specs)
- `research.md` (research findings)
- `decisions.md` (decision log)

**In LLM conversations**: Paste main prompt, reference other documents as needed.

---

### **Problem 4: LLM Doesn't Understand Context**

**Symptom**: LLM asks basic questions that are answered in Genesis Master Prompt.

**Solution**: Check if you pasted the full prompt:

1. **Copy** entire Genesis Master Prompt
2. **Paste** into LLM (don't truncate)
3. **Verify** LLM received full context (ask "What project am I building?")

**If still doesn't understand**: Summarize key points at the top:

```
I'm building a meditation timer app for busy professionals.

**Quick Context**:
- Target: Busy professionals (software engineers)
- Features: 3-5-10 min sessions, office-friendly sounds
- Tech stack: React + Node.js + PostgreSQL
- Current phase: Concept validation

Full context below:

[Paste full Genesis Master Prompt]
```

---

## FAQ

### **Q1: Which LLM should I use?**

**A**: Use at least 2-3 LLMs for multi-model validation.

**Recommended combination**:
- **Kimi** (X Intelligent Agent - innovation)
- **Claude** (Z Guardian Agent - ethics)
- **GPT-4** (CS Security Agent - security)

**Budget-friendly combination**:
- **Gemini** (free, good for X and Z)
- **Claude** (free tier, good for Z)
- **GPT-3.5** (cheaper, good for CS)

**Don't limit yourself to one LLM!**

---

### **Q2: Do I need paid accounts?**

**A**: No, free tiers work fine for most use cases.

**Free tiers**:
- **Claude**: Free tier with generous limits
- **GPT-3.5**: Free via some platforms
- **Gemini**: Free with Google account
- **Kimi**: Free tier available

**Paid tiers** (optional):
- **Claude Pro** ($20/month): Unlimited messages
- **GPT-4** ($20/month): Better quality
- **Cursor Pro** ($20/month): IDE integration

**Recommendation**: Start with free tiers, upgrade if you hit limits.

---

### **Q3: How long does multi-model validation take?**

**A**: 30-90 minutes per validation cycle.

**Breakdown**:
- X Intelligent Agent (Kimi): 15-30 min
- Z Guardian Agent (Claude): 15-30 min
- CS Security Agent (GPT-4): 15-30 min
- Synthesis (Human): 15-30 min

**Total**: 60-120 min for complete validation cycle

**Tip**: You don't need to do all three in one sitting. Spread over multiple days if needed.

---

### **Q4: Can I use only one LLM?**

**A**: Yes, but not recommended.

**Using only one LLM**:
- ✅ Faster (no switching between tools)
- ✅ Simpler (one account, one interface)
- ❌ Single-model bias (miss alternative perspectives)
- ❌ Lower quality validation

**Using multiple LLMs**:
- ✅ Diverse perspectives (more objective)
- ✅ Higher quality validation
- ✅ Catch blind spots
- ❌ Takes more time

**Recommendation**: Use at least 2 LLMs (e.g., Claude + GPT-4).

---

### **Q5: What if I don't have access to recommended LLMs?**

**A**: VerifiMind-PEAS works with ANY LLM!

**Alternatives**:
- **Can't access Kimi**: Use GPT-4 or Gemini for X Intelligent Agent
- **Can't access Claude**: Use GPT-4 for Z Guardian Agent
- **Can't access GPT-4**: Use Claude or Gemini for CS Security Agent

**The methodology matters more than the specific LLM.**

---

### **Q6: How do I know if validation is complete?**

**A**: Validation is complete when:

1. ✅ All three agents (X, Z, CS) have provided input
2. ✅ You've synthesized perspectives
3. ✅ You've made decisions
4. ✅ You've updated Genesis Master Prompt
5. ✅ You're ready to move to next phase

**Validation is iterative**: You'll repeat this process multiple times as your project evolves.

---

### **Q7: Can I use VerifiMind-PEAS for non-technical projects?**

**A**: Absolutely!

**VerifiMind-PEAS works for**:
- ✅ Software development
- ✅ Business strategy
- ✅ Research projects
- ✅ Creative projects (writing, art)
- ✅ Personal projects (life planning, goal setting)

**Any project that benefits from diverse perspectives and systematic validation.**

---

## Conclusion

**VerifiMind-PEAS is platform-agnostic** - it works with any LLM that accepts text input.

**Key Takeaways**:
- ✅ Use at least 2-3 LLMs for multi-model validation
- ✅ Assign specific agent roles (X, Z, CS)
- ✅ Update Genesis Master Prompt after every session
- ✅ Synthesize perspectives as human orchestrator
- ✅ Document decisions with rationale

**The Universal Workflow**:
1. Create Genesis Master Prompt
2. Validate with X Intelligent Agent (innovation)
3. Validate with Z Guardian Agent (ethics)
4. Validate with CS Security Agent (security)
5. Synthesize perspectives
6. Update Genesis Master Prompt
7. Iterate!

**Next Steps**:
1. Read [Genesis Master Prompt Guide](GENESIS_MASTER_PROMPT_GUIDE.md)
2. Create your Genesis Master Prompt
3. Choose your LLMs
4. Start validating!

**Questions?** Join the discussion on [GitHub](https://github.com/creator35lwb-web/VerifiMind-PEAS/discussions) or reach out on [Twitter/X](https://x.com/creator35lwb).

**Happy validating!** 🚀

---

**Author**: Alton Lee Wei Bin (creator35lwb)  
**Version**: 1.0  
**Last Updated**: December 11, 2025  
**License**: MIT License
