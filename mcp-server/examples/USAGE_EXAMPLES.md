# VerifiMind MCP Server - Usage Examples

This document provides practical examples of using the VerifiMind MCP Server with Claude Desktop and other MCP clients.

---

## Prerequisites

- VerifiMind MCP Server installed and configured (see [README.md](../README.md))
- Claude Desktop with MCP server connected
- VerifiMind-PEAS repository with Master Prompt file

---

## Example 1: Accessing the Genesis Master Prompt

### Scenario

You want to understand the roles and responsibilities of the X, Z, and CS agents in the Genesis Methodology.

### Conversation

**You**:
```
Can you show me the Genesis Master Prompt? I want to understand how the X, Z, 
and CS agents are defined.
```

**Claude** (with VerifiMind MCP):
```
I'll read the Genesis Master Prompt from the VerifiMind context.

[Reads from genesis://config/master_prompt]

The Genesis Master Prompt v16.1 defines three specialized agents in the 
RefleXion Trinity:

**X Intelligent (Innovation Engine)**:
- Role: Innovation and strategy analysis
- Model: Gemini
- Focus: Creative solutions, strategic thinking, opportunity identification
- Approach: "Yes, and..." mindset, builds on ideas

**Z Guardian (Ethical Sentinel)**:
- Role: Ethical review and Z-Protocol enforcement
- Model: Claude
- Focus: Privacy, consent, fairness, transparency
- Approach: Socratic questioning, identifies ethical concerns
- Special Power: Veto authority on ethical violations

**CS Security (Security Validator)**:
- Role: Security validation and Socratic interrogation
- Model: Perplexity
- Focus: Vulnerabilities, attack vectors, security best practices
- Approach: Adversarial thinking, "What could go wrong?"

The prompt includes detailed instructions for each agent's analysis framework,
output format (JSON schema), and interaction patterns.

Would you like me to explain any specific agent's role in more detail?
```

### What Happened

1. Claude detected your request for the Master Prompt
2. Claude accessed the `genesis://config/master_prompt` resource through MCP
3. Claude read the complete Master Prompt (10,000+ characters)
4. Claude summarized the key information in a user-friendly format

**Key Benefit**: You didn't need to manually copy-paste the Master Prompt from the file. Claude accessed it directly through MCP.

---

## Example 2: Understanding Project Architecture

### Scenario

You're new to VerifiMind-PEAS and want to understand the project structure and architecture.

### Conversation

**You**:
```
What is the VerifiMind-PEAS project? Can you give me an overview of its 
architecture and purpose?
```

**Claude** (with VerifiMind MCP):
```
Let me check the project information from VerifiMind.

[Reads from genesis://state/project_info]

**VerifiMind-PEAS** is a Perspective-Enhanced AI Systems framework implementing 
the Genesis Methodology for multi-model AI validation and orchestration.

**Key Information**:
- **Version**: 2.0.1
- **Methodology**: Genesis Methodology
- **Architecture**: RefleXion Trinity (X-Z-CS)

**The RefleXion Trinity consists of**:

1. **X Intelligent** (Innovation Engine)
   - Model: Gemini
   - Role: Innovation and strategy analysis
   
2. **Z Guardian** (Ethical Sentinel)
   - Model: Claude
   - Role: Ethical review and Z-Protocol enforcement
   
3. **CS Security** (Security Validator)
   - Model: Perplexity
   - Role: Security validation and Socratic interrogation

**Purpose**: The framework enables "Human-at-Center" AI validation by providing
diverse perspectives (innovation, ethics, security) on concepts, proposals, and
implementations. The human orchestrator synthesizes these perspectives to make
informed decisions.

**Resources**:
- Repository: https://github.com/creator35lwb-web/VerifiMind-PEAS
- White Paper: Genesis Methodology v1.1
- Master Prompt: v16.1

Would you like to know more about how the validation process works?
```

### What Happened

1. Claude accessed `genesis://state/project_info` resource
2. Claude received structured JSON with project metadata
3. Claude formatted the information in a readable way

**Key Benefit**: Project information is always up-to-date and accessible without manual documentation updates.

---

## Example 3: Checking Validation History

### Scenario

You've run several validations using `verifimind_complete.py` and want to review the results.

### Conversation

**You**:
```
What was the result of my latest validation? Can you summarize the key findings?
```

**Claude** (with VerifiMind MCP):
```
Let me check your validation history.

[Reads from genesis://history/latest]

**Latest Validation Result**:

**Concept**: "Add facial recognition authentication to mobile app"

**X Intelligent Perspective** (Innovation):
- Verdict: APPROVED_WITH_CONDITIONS
- Key Points:
  - Significant UX improvement (reduces authentication friction)
  - Recommends liveness detection to prevent spoofing
  - Suggests multi-factor approach combining facial + PIN

**Z Guardian Perspective** (Ethics):
- Verdict: REJECTED
- Key Concerns:
  - Biometric privacy risks (GDPR Article 9 special category data)
  - Consent management complexity
  - Potential discrimination against users with facial differences
- Recommendations:
  - Implement Z-Protocol consent layers
  - Provide alternative authentication methods
  - Conduct bias testing across diverse demographics

**CS Security Perspective** (Security):
- Verdict: APPROVED_WITH_CONDITIONS
- Key Concerns:
  - Presentation attacks (photos, videos, masks)
  - Model inversion attacks (reconstructing faces from embeddings)
  - Storage security of biometric templates
- Recommendations:
  - Implement liveness detection
  - Use secure enclave for biometric storage
  - Add rate limiting to prevent brute force

**Final Resolution**: APPROVED_WITH_MODIFICATIONS (Z veto overridden with conditions)

**Required Modifications**:
1. Implement robust consent management (Z-Protocol compliant)
2. Add liveness detection (X and CS recommendation)
3. Combine with secondary authentication factor (X recommendation)
4. Conduct bias testing across demographics (Z requirement)
5. Use secure enclave for storage (CS requirement)

Would you like me to elaborate on any of these perspectives or recommendations?
```

### What Happened

1. Claude accessed `genesis://history/latest` resource
2. Claude received the complete validation result in JSON format
3. Claude parsed and summarized all three agent perspectives
4. Claude highlighted the conflict resolution and final decision

**Key Benefit**: Validation results are immediately accessible without opening JSON files or running scripts.

---

## Example 4: Analyzing Validation Trends

### Scenario

You want to understand patterns in your validation history over time.

### Conversation

**You**:
```
Can you analyze my complete validation history and tell me if there are any 
patterns? Which agent tends to be most critical?
```

**Claude** (with VerifiMind MCP):
```
Let me analyze your complete validation history.

[Reads from genesis://history/all]

**Validation History Analysis**:

**Total Validations**: 15 (over 3 months)

**Verdict Distribution**:
- X Intelligent: 12 APPROVED, 2 APPROVED_WITH_CONDITIONS, 1 REJECTED
- Z Guardian: 5 APPROVED, 6 APPROVED_WITH_CONDITIONS, 4 REJECTED
- CS Security: 8 APPROVED, 6 APPROVED_WITH_CONDITIONS, 1 REJECTED

**Key Patterns**:

1. **Z Guardian is Most Critical**:
   - Highest rejection rate (27% vs X's 7% and CS's 7%)
   - Most frequent use of veto power (3 times)
   - Primary concerns: Privacy, consent, bias

2. **X Intelligent is Most Optimistic**:
   - Highest approval rate (80% straight approval)
   - Rarely rejects outright (only 1 rejection)
   - Focuses on feasibility and innovation potential

3. **CS Security is Balanced**:
   - Moderate approval rate (53% straight approval)
   - Focuses on technical security rather than ethical concerns
   - Most conditions relate to implementation details

**Common Conflict Patterns**:
- X approves, Z rejects: 4 cases (all related to privacy/consent)
- X approves, CS rejects: 1 case (security vulnerability)
- All three disagree: 0 cases (good sign of methodology alignment)

**Recommendations**:
1. Consider Z Guardian feedback earlier in ideation phase
2. Privacy and consent should be addressed before X analysis
3. Your conflict resolution strategy (Z veto with conditions) is working well

Would you like me to dive deeper into any specific validation or pattern?
```

### What Happened

1. Claude accessed `genesis://history/all` resource
2. Claude received all 15 validation results
3. Claude performed statistical analysis across all validations
4. Claude identified patterns and provided actionable insights

**Key Benefit**: Historical analysis is possible without writing custom scripts or manually reviewing JSON files.

---

## Example 5: Comparing Current Concept with Past Validations

### Scenario

You're considering a new feature and want to see if similar concepts were validated before.

### Conversation

**You**:
```
I'm thinking of adding a "social sharing" feature where users can share their 
achievements on social media. Have I validated anything similar before? What 
were the concerns?
```

**Claude** (with VerifiMind MCP):
```
Let me search your validation history for similar concepts.

[Reads from genesis://history/all]

**Similar Past Validations Found**:

**Validation #7** (2 months ago): "Social media integration for user profiles"
- X Intelligent: APPROVED (saw viral growth potential)
- Z Guardian: APPROVED_WITH_CONDITIONS (privacy concerns about data sharing)
- CS Security: APPROVED_WITH_CONDITIONS (OAuth security, API rate limiting)
- Final: APPROVED_WITH_MODIFICATIONS

**Key Concerns Raised**:

**From Z Guardian**:
- Users must explicitly consent to each share (not blanket permission)
- Shared content should not include personally identifiable information
- Users must be able to revoke sharing permissions easily
- Clear privacy policy explaining what data is shared with which platforms

**From CS Security**:
- Use OAuth 2.0 with PKCE for social media authentication
- Implement rate limiting to prevent spam
- Validate all user-generated content before sharing (XSS prevention)
- Store social media tokens securely (encrypted, not in plaintext)

**Modifications Implemented**:
1. Granular consent per share (not blanket)
2. Privacy-preserving share templates (no PII)
3. OAuth 2.0 with PKCE
4. Rate limiting (5 shares per hour per user)

**Recommendation for Your New Feature**:
Based on this past validation, you should:
1. Design consent flow early (Z Guardian will scrutinize this)
2. Plan OAuth integration from the start (CS Security requirement)
3. Create privacy-preserving share templates
4. Implement rate limiting to prevent abuse

Would you like me to help you draft a concept description that addresses these 
known concerns upfront?
```

### What Happened

1. Claude accessed complete validation history
2. Claude searched for semantically similar concepts
3. Claude extracted relevant concerns and recommendations
4. Claude provided proactive guidance for the new feature

**Key Benefit**: Institutional knowledge from past validations is preserved and accessible, preventing repeated mistakes.

---

## Example 6: Understanding the Genesis Methodology

### Scenario

You're explaining VerifiMind-PEAS to a colleague and want to provide accurate information about the methodology.

### Conversation

**You**:
```
Can you explain the Genesis Methodology in simple terms? My colleague wants to 
understand how it's different from just using one AI model.
```

**Claude** (with VerifiMind MCP):
```
Let me reference the official VerifiMind documentation.

[Reads from genesis://config/master_prompt and genesis://state/project_info]

**The Genesis Methodology in Simple Terms**:

**The Problem**:
When you ask a single AI model to validate an idea, you get one perspective. 
That perspective might be biased toward innovation (missing ethical concerns) 
or biased toward caution (missing opportunities).

**The Solution**:
The Genesis Methodology uses THREE specialized AI models, each with a distinct 
role:

1. **X Intelligent** (The Optimist):
   - Asks: "How can we make this work?"
   - Focuses on innovation, strategy, opportunities
   - Thinks like an entrepreneur

2. **Z Guardian** (The Ethicist):
   - Asks: "Should we do this?"
   - Focuses on privacy, consent, fairness, transparency
   - Thinks like a privacy advocate
   - Has VETO POWER on ethical violations

3. **CS Security** (The Skeptic):
   - Asks: "What could go wrong?"
   - Focuses on security, vulnerabilities, attack vectors
   - Thinks like a security researcher

**The Process**:
1. You describe your concept
2. All three agents analyze it simultaneously (parallel, not sequential)
3. Each agent provides their verdict: APPROVED, APPROVED_WITH_CONDITIONS, or REJECTED
4. If they disagree, a conflict resolution strategy is applied (Z has veto power)
5. YOU (the human) make the final decision based on all three perspectives

**Why It Works**:
- **Perspective Diversity**: You get innovation, ethics, and security perspectives
- **Bias Reduction**: No single model's bias dominates
- **Human-at-Center**: You remain in control; AI provides perspectives, not decisions
- **Institutional Memory**: All validations are logged for future reference

**Key Difference from Single-Model Approach**:
- Single Model: "This is a good idea" (but from whose perspective?)
- Genesis Methodology: "X says it's innovative, Z says it raises privacy concerns, 
  CS says it needs security hardening. Here's what each recommends. You decide."

**Analogy**:
It's like having three trusted advisors with different expertise reviewing your 
business decisions, instead of just one advisor who might miss important angles.

Does this help explain it? Would you like me to walk through a specific example?
```

### What Happened

1. Claude accessed Master Prompt and project info
2. Claude synthesized information from multiple resources
3. Claude explained the methodology in accessible language
4. Claude provided analogies and comparisons

**Key Benefit**: Accurate, up-to-date methodology explanation without consulting multiple documentation files.

---

## Tips for Effective Usage

### 1. Be Specific in Your Requests

**Less Effective**:
```
Tell me about VerifiMind
```

**More Effective**:
```
What are the specific roles of X, Z, and CS agents in the Genesis Methodology?
```

### 2. Reference Resources Explicitly (Optional)

While Claude will automatically access relevant resources, you can be explicit:

```
Can you read the Master Prompt (genesis://config/master_prompt) and explain 
the Z-Protocol rules?
```

### 3. Ask for Comparisons and Analysis

```
Compare my last 5 validations and tell me if Z Guardian's concerns are 
consistent across similar concepts.
```

### 4. Request Actionable Guidance

```
Based on past validations, what should I prepare before validating a new 
authentication feature?
```

### 5. Leverage Historical Context

```
I'm revisiting the "social sharing" concept from 2 months ago. What were the 
unresolved concerns, and have I addressed them in other validations since then?
```

---

## Limitations (Week 1-2 MVP)

The current MVP has the following limitations:

1. **Read-Only**: Resources are read-only. You cannot update validation history through MCP yet.
2. **No Tools**: Agent consultation (X, Z, CS) is not yet available. This comes in Phase 2 (Week 3-4).
3. **No State Management**: Multi-turn validation workflows are not yet supported. This comes in Phase 3 (Week 5-6).
4. **Local Only**: Server runs locally via stdio transport. Hosted deployment comes in Phase 4 (Week 7-8).

---

## Coming in Phase 2 (Week 3-4)

### New Tools

- `consult_agent_x(concept, context)` - Request innovation analysis from X Intelligent
- `consult_agent_z(proposal, context)` - Request ethical review from Z Guardian
- `consult_agent_cs(architecture, context)` - Request security validation from CS Security
- `run_full_trinity(concept, context)` - Execute complete RefleXion Trinity analysis

### Example Future Usage

**You**:
```
Analyze this concept through the RefleXion Trinity: "Add end-to-end encryption 
to our messaging feature"
```

**Claude** (with Tools):
```
I'll run the complete RefleXion Trinity analysis for you.

[Calls run_full_trinity tool]

**X Intelligent Perspective**:
[Innovation analysis...]

**Z Guardian Perspective**:
[Ethical review...]

**CS Security Perspective**:
[Security validation...]

**Synthesis**:
[Combined analysis with recommendations...]
```

---

## Support

For questions or issues with the MCP server:

- **GitHub Discussions**: [VerifiMind-PEAS Discussions](https://github.com/creator35lwb-web/VerifiMind-PEAS/discussions)
- **GitHub Issues**: [Report a Bug](https://github.com/creator35lwb-web/VerifiMind-PEAS/issues)

---

**Happy Validating!** 🚀
