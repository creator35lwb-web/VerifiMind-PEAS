# Claude Code Integration Guide

**How to Use VerifiMind-PEAS Methodology with Claude Code (Anthropic)**

**Version**: 1.0  
**Last Updated**: December 11, 2025  
**Prerequisites**: Claude account (free or paid)

---

## Table of Contents

1. [Introduction](#introduction)
2. [Why Claude Code?](#why-claude-code)
3. [Quick Start](#quick-start)
4. [Step-by-Step Tutorial](#step-by-step-tutorial)
5. [Best Practices](#best-practices)
6. [Troubleshooting](#troubleshooting)
7. [FAQ](#faq)

---

## Introduction

**This guide teaches you how to apply the VerifiMind-PEAS methodology using Claude Code.**

**What you'll learn**:
- How to share your GitHub repository with Claude
- How Claude automatically applies Genesis Methodology
- How to use Claude as X, Z, or CS agent
- Best practices for multi-model validation

**Time**: 15 minutes to read, immediate application

---

## Why Claude Code?

### **Advantages of Claude for VerifiMind-PEAS**

**1. Ethics-Focused**
- Claude is trained with Constitutional AI (ethics built-in)
- Perfect for **Z Guardian Agent** (ethics validation)
- Strong safety and alignment capabilities

**2. Long Context Window**
- Claude supports 200K+ tokens
- Can read entire GitHub repositories
- Perfect for Genesis Master Prompts

**3. Repository Analysis**
- Paste GitHub URL → Claude reads entire repo
- Understands project structure automatically
- Applies methodology without manual prompting

**4. Code Understanding**
- Excellent at understanding complex codebases
- Can validate technical architecture
- Provides detailed security analysis

### **When to Use Claude**

**Use Claude for**:
- ✅ **Ethics validation** (Z Guardian Agent)
- ✅ **Safety analysis** (risk assessment)
- ✅ **Long-form reasoning** (complex decisions)
- ✅ **Repository analysis** (understanding existing code)

**Use other LLMs for**:
- **Kimi**: Innovation and creative insights (X Intelligent Agent)
- **GPT-4**: Technical implementation and coding
- **Gemini**: Research and synthesis

**Best approach**: Use Claude + at least one other LLM for multi-model validation.

---

## Quick Start

### **Method 1: Repository URL (Simplest)**

**Step 1**: Open Claude (claude.ai)

**Step 2**: Paste your GitHub repository URL:

```
I'm working on a project. Please analyze this repository and apply the VerifiMind-PEAS Genesis Methodology:

https://github.com/creator35lwb-web/VerifiMind-PEAS

Act as Z Guardian Agent (ethics perspective) and help me validate the ethical alignment of this project.
```

**Step 3**: Claude reads the repository and applies the methodology automatically!

**That's it!** Claude will:
- ✅ Read README, documentation, code
- ✅ Understand project vision and goals
- ✅ Apply Genesis Methodology (5-step process)
- ✅ Provide ethics-focused validation

---

### **Method 2: Genesis Master Prompt (More Control)**

**Step 1**: Create your Genesis Master Prompt (see [Genesis Master Prompt Guide](GENESIS_MASTER_PROMPT_GUIDE.md))

**Step 2**: Open Claude (claude.ai)

**Step 3**: Paste your Genesis Master Prompt:

```
I'm building a meditation timer app. Here's my Genesis Master Prompt:

[Paste entire Genesis Master Prompt]

Please act as Z Guardian Agent (ethics perspective) and help me validate the ethical alignment of this concept.
```

**Step 4**: Claude applies the methodology based on your prompt!

---

## Step-by-Step Tutorial

### **Tutorial: Validating a Meditation App with Claude**

**Scenario**: You're building a meditation timer app for busy professionals. You want to validate the ethical alignment.

**Time**: 30 minutes

---

### **Step 1: Prepare Your Genesis Master Prompt**

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

**Target Users**: Busy professionals (desk workers, managers, entrepreneurs)

**Success Criteria**: Users meditate at least 3x per week

**Positioning**: "Meditation that fits your schedule"

## Current State

**Phase**: Concept validation  
**Status**: Seeking ethics validation

## Open Questions

1. Are there any ethical concerns with positioning meditation as a "productivity tool"?
2. How do we ensure accessibility for users with different needs?
3. What privacy considerations should we address?
4. How do we avoid "wellness washing" (overselling meditation benefits)?
```

---

### **Step 2: Open Claude and Paste Genesis Master Prompt**

**Go to**: https://claude.ai

**Paste**:

```
I'm building a meditation timer app. Here's my Genesis Master Prompt:

[Paste entire Genesis Master Prompt from Step 1]

Please act as Z Guardian Agent (ethics perspective) from the VerifiMind-PEAS methodology and help me validate the ethical alignment of this concept.

Specifically, please analyze:
1. Ethical concerns with positioning meditation as a "productivity tool"
2. Accessibility considerations
3. Privacy implications
4. Risk of "wellness washing"

Provide recommendations for each concern.
```

---

### **Step 3: Claude Provides Ethics Validation**

**Claude's Response** (example):

```
I'll act as Z Guardian Agent and provide ethics-focused validation of your meditation app concept.

## Ethical Analysis

### 1. Positioning Meditation as "Productivity Tool"

**Concern**: Risk of commodifying mindfulness and reinforcing hustle culture.

**Analysis**:
- Meditation has proven mental health benefits beyond productivity
- Framing as "productivity tool" may attract users, but could oversimplify practice
- Risk of users viewing meditation as another task to optimize

**Recommendations**:
- ✅ Frame as "well-being practice" first, productivity benefit second
- ✅ Include educational content on meditation's holistic benefits
- ✅ Avoid language like "maximize efficiency" or "optimize performance"
- ✅ Emphasize stress reduction, mental clarity, emotional balance

**Revised Positioning**: "Meditation for well-being, designed for busy schedules"

### 2. Accessibility Considerations

**Concern**: "Busy professionals" may exclude other demographics.

**Analysis**:
- Current positioning focuses on desk workers
- May exclude: students, caregivers, shift workers, people with disabilities
- 5-minute sessions may not work for everyone (some need longer, some shorter)

**Recommendations**:
- ✅ Use inclusive language: "Anyone with a busy schedule"
- ✅ Offer multiple duration options (1, 3, 5, 10, 15 minutes)
- ✅ Provide accessibility features (screen reader support, keyboard navigation)
- ✅ Include guided vs unguided options (some prefer silence)

**Revised Target Users**: "Anyone seeking mindfulness in their daily routine"

### 3. Privacy Implications

**Concern**: Tracking meditation habits is sensitive personal data.

**Analysis**:
- Meditation history reveals mental health patterns
- Could be misused by employers (tracking employee stress)
- Data breaches could expose vulnerable information

**Recommendations**:
- ✅ Make data collection opt-in (not opt-out)
- ✅ Store data locally by default (not cloud)
- ✅ Provide data export and deletion options
- ✅ Clear privacy policy (no selling data, no third-party sharing)
- ✅ Consider anonymous usage (no account required)

**Privacy Principle**: "Your meditation practice is private by default"

### 4. Risk of "Wellness Washing"

**Concern**: Overselling meditation as cure for systemic work stress.

**Analysis**:
- Meditation helps manage stress, but doesn't fix toxic work environments
- Risk of shifting responsibility from employers to employees
- Could perpetuate "self-care" as solution to structural problems

**Recommendations**:
- ✅ Be honest about what meditation can/can't do
- ✅ Include disclaimer: "Meditation is a tool, not a cure"
- ✅ Avoid claims like "eliminate stress" or "cure burnout"
- ✅ Encourage users to address root causes of stress (not just symptoms)

**Honest Messaging**: "Meditation helps you manage stress, but it's not a substitute for addressing work-life balance"

## Overall Assessment

**Ethical Alignment**: 7/10 (Good with improvements needed)

**Strengths**:
- Clear value proposition
- Addresses real pain point
- Simple, focused feature set

**Concerns**:
- Positioning as "productivity tool" needs refinement
- Accessibility could be broader
- Privacy considerations need explicit design
- Risk of wellness washing needs mitigation

**Recommendation**: Implement the 4 recommendations above to achieve 9/10 ethical alignment.

## Next Steps

1. Revise positioning and messaging
2. Expand accessibility features
3. Design privacy-first architecture
4. Create honest, balanced marketing copy

Would you like me to help you implement any of these recommendations?
```

---

### **Step 4: Update Genesis Master Prompt**

**After Claude's validation, update your Genesis Master Prompt**:

```markdown
# Meditation App - Genesis Master Prompt

[... previous sections ...]

## Decisions Made

### **Decision 1: Ethical Positioning**
- **What**: Frame as "well-being practice" (not "productivity tool")
- **Why**: Z Guardian Agent identified risk of wellness washing
- **Revised Positioning**: "Meditation for well-being, designed for busy schedules"
- **Rationale**: Attracts users without commodifying mindfulness

### **Decision 2: Inclusive Target Audience**
- **What**: "Anyone seeking mindfulness" (not just "busy professionals")
- **Why**: Z Guardian Agent identified accessibility concerns
- **Rationale**: Broader reach, more inclusive

### **Decision 3: Privacy-First Design**
- **What**: Local storage by default, opt-in cloud sync, no data selling
- **Why**: Z Guardian Agent identified privacy implications
- **Rationale**: Build trust, respect user privacy

### **Decision 4: Honest Messaging**
- **What**: "Meditation helps manage stress, not cure burnout"
- **Why**: Z Guardian Agent identified wellness washing risk
- **Rationale**: Ethical marketing, realistic expectations

## Next Steps

1. Revise marketing copy (implement ethical positioning)
2. Design privacy-first architecture
3. Validate with X Intelligent Agent (innovation perspective)
4. Validate with CS Security Agent (security perspective)
```

**Save the updated Genesis Master Prompt.**

---

### **Step 5: Continue with Other Agents**

**Now validate with other AI agents**:

**X Intelligent Agent** (Innovation):
- Use **Kimi** or **GPT-4** for creative insights
- Paste updated Genesis Master Prompt
- Ask for innovation perspective

**CS Security Agent** (Security):
- Use **GPT-4** or **Claude** for security analysis
- Paste updated Genesis Master Prompt
- Ask for security perspective

**Synthesize all perspectives** → Make final decision → Update Genesis Master Prompt

---

## Best Practices

### **1. Be Specific About Agent Role**

**Good**:
```
Please act as Z Guardian Agent (ethics perspective) from the VerifiMind-PEAS methodology and validate the ethical alignment of this concept.
```

**Bad**:
```
What do you think about this idea?
```

**Why**: Specific role prompting ensures Claude applies the methodology correctly.

---

### **2. Provide Complete Context**

**Good**:
```
I'm building a meditation app. Here's my Genesis Master Prompt:

[Paste entire Genesis Master Prompt]

Please act as Z Guardian Agent...
```

**Bad**:
```
I'm building a meditation app. Is it ethical?
```

**Why**: Complete context enables better validation.

---

### **3. Ask for Specific Analysis**

**Good**:
```
Please analyze:
1. Ethical concerns with positioning
2. Accessibility considerations
3. Privacy implications
4. Risk of wellness washing
```

**Bad**:
```
Tell me if this is ethical.
```

**Why**: Specific questions get specific answers.

---

### **4. Document Decisions in Genesis Master Prompt**

**After every Claude session**:
1. Review Claude's recommendations
2. Make decisions based on recommendations
3. **Update Genesis Master Prompt** with decisions and rationale
4. Save for next session

**Why**: Maintains continuity, prevents repeating discussions.

---

### **5. Use Claude for Ethics, Other LLMs for Innovation**

**Claude is best for**:
- ✅ Ethics validation (Z Guardian Agent)
- ✅ Safety analysis
- ✅ Risk assessment

**Use other LLMs for**:
- **Kimi**: Innovation (X Intelligent Agent)
- **GPT-4**: Implementation (technical details)
- **Gemini**: Research (academic validation)

**Why**: Multi-model validation provides diverse perspectives.

---

## Troubleshooting

### **Problem 1: Claude Doesn't Apply Methodology**

**Symptom**: Claude provides generic advice instead of VerifiMind-PEAS validation.

**Solution**: Be explicit about the methodology:

```
Please act as Z Guardian Agent from the VerifiMind-PEAS methodology.

The VerifiMind-PEAS methodology is a systematic 5-step multi-model validation process:
1. Initial Conceptualization
2. Critical Scrutiny (your role)
3. External Validation
4. Synthesis
5. Iteration

Please provide ethics-focused validation of this concept.
```

---

### **Problem 2: Claude Can't Access GitHub Repository**

**Symptom**: "I can't access external URLs"

**Solution**: Copy-paste repository content instead:

```
I'm working on a project. Here's the README:

[Paste README content]

Here's the main code file:

[Paste code]

Please act as Z Guardian Agent and validate the ethical alignment.
```

---

### **Problem 3: Response is Too Generic**

**Symptom**: Claude provides surface-level analysis.

**Solution**: Ask follow-up questions:

```
Thank you for the analysis. Can you go deeper on the privacy implications?

Specifically:
1. What data should we collect vs avoid?
2. How should we handle data breaches?
3. What privacy regulations apply (GDPR, CCPA)?
4. Should we offer anonymous usage?
```

---

### **Problem 4: Claude Disagrees with Other LLMs**

**Symptom**: Claude's recommendations conflict with Kimi or GPT-4.

**Solution**: This is a feature, not a bug!

**Conflicting perspectives mean**:
- ✅ Multiple valid viewpoints exist
- ✅ Trade-offs need to be considered
- ✅ Human judgment is required

**Your role as human orchestrator**:
1. Understand each perspective
2. Identify trade-offs
3. Make decision based on your values
4. Document decision in Genesis Master Prompt

---

## FAQ

### **Q1: Do I need a paid Claude account?**

**A**: No, free Claude account works fine!

**Free tier**:
- ✅ Sufficient for most VerifiMind-PEAS use cases
- ✅ Long context window (200K tokens)
- ✅ Repository analysis

**Paid tier** (Claude Pro):
- ✅ More messages per day
- ✅ Priority access during peak times
- ✅ Longer conversations

**Recommendation**: Start with free tier, upgrade if you hit limits.

---

### **Q2: Can I use Claude for all three agents (X, Z, CS)?**

**A**: Yes, but not recommended.

**Claude can act as**:
- ✅ **Z Guardian Agent** (ethics) - **BEST**
- ✅ **CS Security Agent** (security) - **GOOD**
- ⚠️ **X Intelligent Agent** (innovation) - **OKAY**

**Recommendation**: Use Claude for Z (ethics), use Kimi or GPT-4 for X (innovation), use GPT-4 for CS (security).

**Why**: Multi-model validation requires diverse perspectives. Using only Claude = single-model bias.

---

### **Q3: How do I switch between agent roles in the same conversation?**

**A**: Explicitly state the role switch:

```
Thank you for the ethics validation (Z Guardian Agent).

Now, please switch to CS Security Agent (security perspective) and analyze the security implications of this architecture.
```

**Tip**: For clearer separation, use separate conversations for each agent role.

---

### **Q4: Can Claude read my entire GitHub repository?**

**A**: Yes, if you paste the URL!

**Claude can**:
- ✅ Read public GitHub repositories
- ✅ Understand project structure
- ✅ Analyze code, documentation, issues

**Claude cannot**:
- ❌ Access private repositories (unless you paste content)
- ❌ Make commits or changes
- ❌ Run code or tests

**Tip**: For private repos, copy-paste key files instead of sharing URL.

---

### **Q5: How long should my Genesis Master Prompt be for Claude?**

**A**: 5-20 pages is ideal.

**Claude supports**:
- ✅ 200K+ tokens (approximately 150,000 words)
- ✅ Very long Genesis Master Prompts

**Recommendation**:
- **Start**: 1-2 pages
- **Grow**: 5-20 pages over time
- **Maximum**: 50 pages (if needed)

**Tip**: If Genesis Master Prompt exceeds 50 pages, split into multiple documents and link them.

---

### **Q6: Can I use Claude Code (VS Code extension)?**

**A**: Yes! Claude Code extension works great with VerifiMind-PEAS.

**Benefits**:
- ✅ Integrated in VS Code
- ✅ Can read your codebase directly
- ✅ Can make code changes

**How to use**:
1. Install Claude Code extension in VS Code
2. Open your project
3. Ask Claude to act as Z Guardian Agent
4. Claude analyzes your code and provides ethics validation

**Tip**: Claude Code is best for code-focused projects. For conceptual validation, use claude.ai web interface.

---

## Conclusion

**Claude is an excellent choice for VerifiMind-PEAS methodology**, especially for ethics validation (Z Guardian Agent).

**Key Takeaways**:
- ✅ Claude excels at ethics and safety analysis
- ✅ Long context window supports Genesis Master Prompts
- ✅ Repository analysis enables automatic methodology application
- ✅ Best used in combination with other LLMs (Kimi, GPT-4, Gemini)

**Next Steps**:
1. Read [Genesis Master Prompt Guide](GENESIS_MASTER_PROMPT_GUIDE.md)
2. Create your Genesis Master Prompt
3. Open Claude and start validating!
4. Update Genesis Master Prompt after each session
5. Use other LLMs for multi-model validation

**Questions?** Join the discussion on [GitHub](https://github.com/creator35lwb-web/VerifiMind-PEAS/discussions) or reach out on [Twitter/X](https://x.com/creator35lwb).

**Happy validating!** 🚀

---

**Author**: Alton Lee Wei Bin (creator35lwb)  
**Version**: 1.0  
**Last Updated**: December 11, 2025  
**License**: MIT License
