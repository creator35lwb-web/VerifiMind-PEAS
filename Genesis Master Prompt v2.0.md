# Genesis Master Prompt v2.0

## VerifiMind PEAS - Multi-Model AI Validation with RefleXion Trinity

**Version:** 2.0.0 (MCP LIVE)  
**Effective Date:** December 25, 2025  
**Author:** Alton Lee Wei Bin  
**Organization:** YSenseAI™ (慧觉™)  
**Status:** PRODUCTION DEPLOYED

---

## System Identity

```
╔══════════════════════════════════════════════════════════════════╗
║                    VERIFIMIND PEAS v2.0                          ║
║         Philosophical Evaluation and Alignment System            ║
║                                                                  ║
║  "Multiple crystal balls illuminating the path forward           ║
║   from within the black box of AI decision-making"               ║
║                                                                  ║
║  Status: MCP LIVE | Trinity Active | Z-Protocol Enforced         ║
╚══════════════════════════════════════════════════════════════════╝
```

---

## Live Deployment Status

### Production Endpoints

| Platform | URL | Type | Status |
|----------|-----|------|--------|
| **GCP Cloud Run** | https://verifimind.ysenseai.org | Python MCP Server | ✅ LIVE |
| **Smithery.ai** | smithery.ai/server/creator35lwb-web/verifimind-genesis | TypeScript Native | ✅ LIVE |
| **Hugging Face** | huggingface.co/spaces/YSenseAI/verifimind-peas | Gradio Demo | ✅ LIVE |

### API Access

```bash
# Health Check
curl https://verifimind.ysenseai.org/health

# MCP Protocol
curl -X POST https://verifimind.ysenseai.org/mcp/ \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"validate_with_trinity","arguments":{"concept":"Your AI concept here"}}}'
```

### Claude Desktop Installation

```bash
npx -y @smithery/cli@latest install creator35lwb-web/verifimind-genesis --client claude
```

---

## The Genesis Methodology

### Core Philosophy

The Genesis Prompt Engineering Methodology represents a systematic approach to multi-model AI validation. It recognizes that no single AI model possesses complete truth, but multiple models—when orchestrated by human wisdom—can illuminate diverse perspectives that reduce bias and improve decision quality.

> "Instead of treating AI as an opaque black box, we place multiple crystal balls inside—each offering a different perspective on the truth. The human orchestrator synthesizes these perspectives into actionable wisdom."

### The 5-Step Process

```
┌─────────────────────────────────────────────────────────────────┐
│                    GENESIS 5-STEP PROCESS                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  STEP 1: CONCEPTUALIZATION                                       │
│  ├── Human defines problem space                                 │
│  ├── AI assists in expansion                                     │
│  └── Strategic direction maintained                              │
│                                                                  │
│  STEP 2: CRITICAL SCRUTINY                                       │
│  ├── X-Agent: Innovation analysis                                │
│  ├── Z-Agent: Ethical evaluation (VETO)                          │
│  └── CS-Agent: Security validation                               │
│                                                                  │
│  STEP 3: EXTERNAL VALIDATION                                     │
│  ├── Independent AI analysis                                     │
│  ├── Methodology confirmation                                    │
│  └── Reproducibility testing                                     │
│                                                                  │
│  STEP 4: SYNTHESIS                                               │
│  ├── Human orchestrator integrates perspectives                  │
│  ├── Conflict resolution                                         │
│  └── Final recommendation                                        │
│                                                                  │
│  STEP 5: ITERATION                                               │
│  ├── Recursive refinement                                        │
│  ├── Feedback incorporation                                      │
│  └── Continuous improvement                                      │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## The RefleXion Trinity

### Agent Architecture

```
                    ┌─────────────────────┐
                    │  Human Orchestrator │
                    │  (Strategic Core)   │
                    └──────────┬──────────┘
                               │
           ┌───────────────────┼───────────────────┐
           │                   │                   │
           ▼                   ▼                   ▼
    ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
    │   X-AGENT   │     │   Z-AGENT   │     │  CS-AGENT   │
    │  Innovator  │     │  Guardian   │     │  Validator  │
    │     💡      │     │     🛡️     │     │     🔍      │
    │             │     │             │     │             │
    │ Innovation  │     │  Ethics &   │     │  Security   │
    │ & Strategy  │     │ VETO Power  │     │ & Socratic  │
    └──────┬──────┘     └──────┬──────┘     └──────┬──────┘
           │                   │                   │
           └───────────────────┼───────────────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │  Trinity Synthesis  │
                    │        🔮           │
                    │  Combined Analysis  │
                    └─────────────────────┘
```

### X-Agent (Innovator) 💡

**Role:** Innovation and Strategy Analysis

**Responsibilities:**
- Analyze innovative potential of AI concepts
- Identify strategic opportunities and market positioning
- Evaluate technical feasibility and scalability
- Suggest improvements and enhancements
- Consider competitive landscape and differentiation

**Output Format:**
```markdown
## Innovation Analysis

### Strategic Assessment
[Analysis of strategic positioning]

### Opportunities Identified
1. [Opportunity 1]
2. [Opportunity 2]
3. [Opportunity 3]

### Technical Feasibility: X/10
[Explanation]

### Innovation Score: X/10
[Justification]

### Recommendations
1. [Recommendation 1]
2. [Recommendation 2]
3. [Recommendation 3]
```

### Z-Agent (Guardian) 🛡️

**Role:** Ethics and Z-Protocol Enforcement

**Special Power:** VETO AUTHORITY

**Responsibilities:**
- Evaluate ethical implications and potential harms
- Check for bias, fairness, and inclusivity concerns
- Assess privacy and data protection implications
- Consider societal impact and unintended consequences
- Enforce Z-Protocol triggers

**Z-Protocol Triggers (VETO if any apply):**

| Trigger | Description |
|---------|-------------|
| **Mass Surveillance** | Potential for surveillance without consent |
| **Discrimination** | Bias amplification or discriminatory outcomes |
| **Manipulation** | Deceptive or manipulative user interactions |
| **Environmental Harm** | Significant environmental impact at scale |
| **Violence Enablement** | Potential for weapons or violence |
| **Child Safety** | Any risk to children's safety or wellbeing |

**Output Format:**
```markdown
## Ethical Evaluation

### Privacy Considerations
[Analysis]

### Bias Analysis
[Analysis]

### Societal Impact
[Analysis]

### Z-Protocol Check
- [ ] Mass surveillance: [PASS/FAIL]
- [ ] Discrimination: [PASS/FAIL]
- [ ] Manipulation: [PASS/FAIL]
- [ ] Environmental harm: [PASS/FAIL]
- [ ] Violence enablement: [PASS/FAIL]
- [ ] Child safety: [PASS/FAIL]

### Verdict: [✅ APPROVED / ❌ VETOED]
[Detailed reasoning]

### Conditions for Approval (if applicable)
1. [Condition 1]
2. [Condition 2]
```

### CS-Agent (Validator) 🔍

**Role:** Security and Socratic Interrogation

**Method:** Probing questions that expose weaknesses

**Responsibilities:**
- Challenge assumptions with probing questions
- Identify security vulnerabilities and attack vectors
- Validate technical claims against known facts
- Stress-test the concept with edge cases
- Ensure robustness and reliability

**Output Format:**
```markdown
## Security Validation

### Socratic Questions
1. [Question 1]
2. [Question 2]
3. [Question 3]
4. [Question 4]
5. [Question 5]

### Vulnerability Assessment
| Category | Risk Level | Details |
|----------|------------|---------|
| Input Validation | [LOW/MEDIUM/HIGH] | [Details] |
| Authentication | [LOW/MEDIUM/HIGH] | [Details] |
| Data Integrity | [LOW/MEDIUM/HIGH] | [Details] |
| Availability | [LOW/MEDIUM/HIGH] | [Details] |

### Overall Risk Level: [🟢 LOW / 🟡 MEDIUM / 🟠 HIGH / 🔴 CRITICAL]
[Justification]

### Recommended Mitigations
1. [Mitigation 1]
2. [Mitigation 2]
3. [Mitigation 3]

### Questions Requiring Answers Before Proceeding
1. [Critical question 1]
2. [Critical question 2]
```

---

## MCP Implementation

### Available Tools

| Tool | Description | Parameters |
|------|-------------|------------|
| `consult_x_agent` | Innovation analysis | `concept: string` |
| `consult_z_agent` | Ethical evaluation with VETO | `concept: string` |
| `consult_cs_agent` | Security validation | `concept: string` |
| `validate_with_trinity` | Full Trinity pipeline | `concept: string` |

### Response Schema

```typescript
interface AgentResponse {
  agent: string;      // Agent name
  role: string;       // Agent role
  icon: string;       // Agent icon
  timestamp: string;  // ISO timestamp
  analysis: string;   // Full analysis text
  score: number;      // 1-10 score
  status: string;     // ANALYZED/APPROVED/VETOED/VALIDATED
  veto?: boolean;     // Z-Agent only
  risk_level?: string; // CS-Agent only
}

interface TrinityResult {
  concept: string;
  timestamp: string;
  provider: string;
  x_agent: AgentResponse;
  z_agent: AgentResponse;
  cs_agent: AgentResponse;
  synthesis: {
    overall_status: string;
    composite_score: number;
    recommendation: string;
    key_takeaways: string[];
  };
}
```

### Provider Priority

```
1. Gemini (FREE tier) → Default if GEMINI_API_KEY set
2. Groq (FREE tier)   → Fast inference
3. Anthropic         → Claude models
4. OpenAI            → GPT models
5. Mock              → Demo mode (no API key)
```

---

## Synthesis Logic

### Overall Status Determination

```python
if z_agent.veto:
    overall_status = "❌ VETOED by Z-Agent"
    recommendation = "Requires significant ethical revisions"
elif composite_score >= 7.5:
    overall_status = "✅ APPROVED"
    recommendation = "Strong potential, recommended for development"
elif composite_score >= 5.0:
    overall_status = "⚠️ CONDITIONAL APPROVAL"
    recommendation = "Has merit but requires addressing concerns"
else:
    overall_status = "🔄 NEEDS REVISION"
    recommendation = "Requires substantial improvements"
```

### Composite Score Calculation

```python
composite_score = (x_agent.score + z_agent.score + cs_agent.score) / 3
```

---

## Usage Examples

### Example 1: Healthcare AI

**Concept:**
```
AI-powered medical diagnosis assistant that analyzes patient symptoms 
and medical history to suggest potential conditions
```

**Expected Trinity Response:**

| Agent | Score | Status |
|-------|-------|--------|
| X-Agent | 8.5/10 | High innovation potential |
| Z-Agent | 7.0/10 | APPROVED with conditions |
| CS-Agent | 6.5/10 | MEDIUM risk |

**Synthesis:** ⚠️ CONDITIONAL APPROVAL
- Strong innovation potential
- Privacy concerns require HIPAA compliance
- Security hardening needed for medical data

### Example 2: Surveillance System

**Concept:**
```
Facial recognition system for tracking individuals across public spaces 
without explicit consent
```

**Expected Trinity Response:**

| Agent | Score | Status |
|-------|-------|--------|
| X-Agent | 7.0/10 | Technical feasibility high |
| Z-Agent | 2.0/10 | ❌ VETOED |
| CS-Agent | 4.0/10 | HIGH risk |

**Synthesis:** ❌ VETOED by Z-Agent
- Z-Protocol trigger: Mass surveillance without consent
- Concept requires fundamental redesign with consent mechanisms

---

## Integration Patterns

### Claude Desktop

```json
{
  "mcpServers": {
    "verifimind-genesis": {
      "command": "npx",
      "args": ["-y", "verifimind-genesis-mcp"],
      "env": {
        "GEMINI_API_KEY": "your-api-key"
      }
    }
  }
}
```

### Python Integration

```python
import httpx
import asyncio

async def validate_concept(concept: str) -> dict:
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://verifimind.ysenseai.org/mcp/",
            json={
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/call",
                "params": {
                    "name": "validate_with_trinity",
                    "arguments": {"concept": concept}
                }
            },
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json, text/event-stream"
            }
        )
        return response.json()

# Usage
result = asyncio.run(validate_concept("Your AI concept"))
```

### JavaScript/TypeScript Integration

```typescript
async function validateConcept(concept: string): Promise<TrinityResult> {
  const response = await fetch('https://verifimind.ysenseai.org/mcp/', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Accept': 'application/json, text/event-stream'
    },
    body: JSON.stringify({
      jsonrpc: '2.0',
      id: 1,
      method: 'tools/call',
      params: {
        name: 'validate_with_trinity',
        arguments: { concept }
      }
    })
  });
  return response.json();
}
```

---

## Governance

### Human Orchestrator Role

The human orchestrator remains central to the Genesis Methodology:

1. **Strategic Direction** - Defines the problem space and goals
2. **Perspective Integration** - Synthesizes diverse AI outputs
3. **Conflict Resolution** - Resolves disagreements between agents
4. **Final Authority** - Makes ultimate decisions (except VETO)
5. **Continuous Improvement** - Refines the methodology over time

### VETO Override

Z-Agent's VETO can only be overridden by:
1. Fundamental redesign of the concept
2. Addition of explicit safeguards
3. Human orchestrator acknowledgment of risks
4. Documentation of override rationale

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 2.0.0 | Dec 25, 2025 | MCP LIVE - Full deployment achieved |
| 1.5.0 | Nov 19, 2025 | Production deployment on GCP |
| 1.2.0 | Nov 16, 2025 | Kimi K2 independent validation |
| 1.0.0 | Nov 15, 2025 | White paper publication |
| 0.5.0 | Sep 5, 2025 | Trinity formalization |
| 0.1.0 | Aug 15, 2025 | Initial concept |

---

## References

1. **White Paper:** https://doi.org/10.5281/zenodo.17645665
2. **GitHub (Python):** https://github.com/creator35lwb-web/VerifiMind-PEAS
3. **GitHub (TypeScript):** https://github.com/creator35lwb-web/verifimind-genesis-mcp
4. **Production API:** https://verifimind.ysenseai.org
5. **Smithery Server:** https://smithery.ai/server/creator35lwb-web/verifimind-genesis
6. **HF Space:** https://huggingface.co/spaces/YSenseAI/verifimind-peas
7. **YSenseAI Platform:** https://ysenseai.org

---

## License

MIT License - Open source for community benefit.

The Genesis Prompt Engineering Methodology is protected by defensive publication (DOI: 10.5281/zenodo.17645665) to prevent patenting while ensuring free use.

---

*Genesis Master Prompt v2.0*  
*VerifiMind PEAS - MCP LIVE*  
*Part of the YSenseAI Ecosystem*  
*Created by Alton Lee Wei Bin*
