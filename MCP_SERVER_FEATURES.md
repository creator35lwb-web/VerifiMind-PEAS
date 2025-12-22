# VerifiMind PEAS MCP Server - Complete Features Guide

**Version**: 0.2.0  
**Status**: ✅ **LIVE** at https://verifimind.ysenseai.org  
**Last Updated**: December 23, 2025

---

## 🎯 What Does the MCP Server Provide?

The VerifiMind PEAS MCP Server provides **two types of capabilities** through the Model Context Protocol:

1. **Resources** (4) - Read-only data that LLMs can access
2. **Tools** (4) - Actions that LLMs can execute

---

## 📚 Resources (Context for LLMs)

Resources provide **context and knowledge** that your LLM can read to understand the VerifiMind methodology.

### 1. Genesis Master Prompt
| Property | Value |
|----------|-------|
| **URI** | `genesis://config/master_prompt` |
| **Format** | Markdown |
| **Version** | v16.1 |
| **Purpose** | Complete methodology guide for X, Z, CS agents |

**What it provides:**
- Complete RefleXion Trinity methodology
- Agent role definitions (X Intelligent, Z Guardian, CS Security)
- Chain of Thought reasoning templates
- Scoring criteria and thresholds
- Decision-making frameworks

**How LLMs use it:**
When your LLM reads this resource, it gains the complete VerifiMind methodology context, enabling it to:
- Understand the three-agent validation approach
- Apply consistent evaluation criteria
- Generate structured validation reports

---

### 2. Latest Validation Result
| Property | Value |
|----------|-------|
| **URI** | `genesis://history/latest` |
| **Format** | JSON |
| **Purpose** | Most recent validation for reference |

**What it provides:**
- Previous validation concept and results
- Agent perspectives (X, Z, CS)
- Conflict resolution outcomes
- Final verdict and recommendations

**How LLMs use it:**
- Learn from previous validation patterns
- Maintain consistency across sessions
- Reference past decisions

---

### 3. Complete Validation History
| Property | Value |
|----------|-------|
| **URI** | `genesis://history/all` |
| **Format** | JSON |
| **Purpose** | Full validation archive |

**What it provides:**
- All past validations
- Metadata and statistics
- Trend analysis data

**How LLMs use it:**
- Analyze validation patterns over time
- Identify common issues
- Improve future recommendations

---

### 4. Project Information
| Property | Value |
|----------|-------|
| **URI** | `genesis://state/project_info` |
| **Format** | JSON |
| **Purpose** | Project metadata |

**What it provides:**
- Architecture overview
- Agent role descriptions
- Version information
- Documentation links

---

## 🔧 Tools (Actions LLMs Can Execute)

Tools allow your LLM to **actively validate concepts** using the RefleXion Trinity methodology.

### 1. Consult X Intelligent Agent
| Property | Value |
|----------|-------|
| **Tool Name** | `consult_agent_x` |
| **Model** | Gemini 2.0 Flash (FREE!) |
| **Focus** | Innovation & Strategy |

**Parameters:**
```json
{
  "concept_name": "string (required)",
  "concept_description": "string (required)",
  "context": "string (optional)"
}
```

**What X Intelligent analyzes:**
- ✅ Innovation potential (novelty, uniqueness)
- ✅ Strategic value (market fit, competitive advantage)
- ✅ Market opportunities (growth potential, timing)
- ✅ Competitive positioning (differentiation)
- ✅ Scalability assessment

**Output includes:**
- Reasoning chain (step-by-step analysis)
- Innovation score (0-100)
- Strategic value score (0-100)
- Opportunities list
- Risks list
- Recommendation
- Confidence level

---

### 2. Consult Z Guardian Agent
| Property | Value |
|----------|-------|
| **Tool Name** | `consult_agent_z` |
| **Model** | Claude 3 Haiku |
| **Focus** | Ethics & Safety |

**Parameters:**
```json
{
  "concept_name": "string (required)",
  "concept_description": "string (required)",
  "context": "string (optional)"
}
```

**What Z Guardian analyzes:**
- ✅ Ethical alignment (moral implications)
- ✅ Social impact (community effects)
- ✅ Bias detection (fairness concerns)
- ✅ Privacy considerations
- ✅ Long-term consequences

**Output includes:**
- Reasoning chain
- Ethics score (0-100)
- Safety score (0-100)
- Ethical concerns list
- Mitigation recommendations
- Approval status

---

### 3. Consult CS Security Agent
| Property | Value |
|----------|-------|
| **Tool Name** | `consult_agent_cs` |
| **Model** | Claude 3 Haiku |
| **Focus** | Security & Feasibility |

**Parameters:**
```json
{
  "concept_name": "string (required)",
  "concept_description": "string (required)",
  "context": "string (optional)"
}
```

**What CS Security analyzes:**
- ✅ Technical feasibility
- ✅ Security vulnerabilities
- ✅ Compliance requirements
- ✅ Implementation risks
- ✅ Resource requirements

**Output includes:**
- Reasoning chain
- Security score (0-100)
- Feasibility score (0-100)
- Vulnerabilities list
- Compliance issues
- Implementation recommendations

---

### 4. Run Full Trinity Validation
| Property | Value |
|----------|-------|
| **Tool Name** | `run_full_trinity` |
| **Models** | Gemini + Claude (multi-model) |
| **Focus** | Complete validation |

**Parameters:**
```json
{
  "concept_name": "string (required)",
  "concept_description": "string (required)",
  "context": "string (optional)"
}
```

**What it does:**
Runs all three agents sequentially (X → Z → CS) and synthesizes results.

**Output includes:**
- All three agent analyses
- Conflict resolution (if agents disagree)
- Synthesized verdict
- Overall recommendation
- Confidence score
- Action items

---

## 🔄 How It Works: User Flow

### Step 1: Connect MCP Client
```json
{
  "mcpServers": {
    "verifimind-genesis": {
      "url": "https://verifimind.ysenseai.org/mcp",
      "transport": "http-sse"
    }
  }
}
```

### Step 2: LLM Reads Resources (Automatic)
When connected, your LLM can access:
- Genesis Master Prompt → Understands methodology
- Validation History → Learns from past validations

### Step 3: User Describes Concept
User tells their LLM about their idea:
> "I want to build a meditation app for busy professionals..."

### Step 4: LLM Calls Tools
The LLM can now call:
- `consult_agent_x` → Get innovation analysis
- `consult_agent_z` → Get ethics review
- `consult_agent_cs` → Get security assessment
- `run_full_trinity` → Get complete validation

### Step 5: User Receives Structured Report
The LLM presents a comprehensive validation report with:
- Multi-perspective analysis
- Scores and metrics
- Actionable recommendations

---

## 💡 Key Benefits

### For Users
| Benefit | Description |
|---------|-------------|
| **Multi-Model Validation** | Different AI models catch different issues |
| **Structured Analysis** | Consistent, comparable results |
| **Ethical Review** | Built-in ethics and safety checks |
| **Cost Effective** | ~$0.003 per validation |
| **Transparent Reasoning** | Chain of Thought shows logic |

### For Developers
| Benefit | Description |
|---------|-------------|
| **MCP Standard** | Works with any MCP-compatible client |
| **REST API** | Standard HTTP endpoints |
| **Open Source** | Full code on GitHub |
| **Extensible** | Add custom agents or providers |

---

## 📊 Cost Analysis

| Component | Model | Cost per 1M tokens |
|-----------|-------|-------------------|
| X Agent | Gemini 2.0 Flash | **$0.00** (FREE!) |
| Z Agent | Claude 3 Haiku | $0.25 / $1.25 |
| CS Agent | Claude 3 Haiku | $0.25 / $1.25 |

**Average cost per Trinity validation: ~$0.003**

---

## 🔗 Endpoints Summary

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Server info |
| `/health` | GET | Health check |
| `/.well-known/mcp-config` | GET | MCP configuration |
| `/mcp` | SSE | MCP protocol endpoint |

---

## 🎬 Demo Scenario

**User**: "I want to validate my idea for a decentralized voting system"

**LLM with MCP**:
1. Reads `genesis://config/master_prompt` → Understands methodology
2. Calls `run_full_trinity` with concept details
3. Receives:
   - **X Intelligent**: "High innovation score (85), strong market timing..."
   - **Z Guardian**: "Ethical concerns about voter privacy, recommend..."
   - **CS Security**: "Technical feasibility good, but smart contract risks..."
4. Synthesizes: "Overall: PROCEED WITH CAUTION. Address privacy and security concerns before launch."

---

## 📚 Related Documentation

- **GitHub**: https://github.com/creator35lwb-web/VerifiMind-PEAS
- **Genesis Master Prompt v2.0**: `/genesis-master-prompts-v2.0-en.md`
- **Validation Archive**: `/validation_archive/reports/` (57 reports)
- **Iteration Journey**: `/ITERATION_JOURNEY_REPORT.md`

---

**Server Status**: ✅ **LIVE**  
**URL**: https://verifimind.ysenseai.org  
**Version**: 0.2.0
