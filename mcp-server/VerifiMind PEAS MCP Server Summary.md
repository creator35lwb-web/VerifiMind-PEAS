# VerifiMind PEAS MCP Server Summary

## 📦 Server Information

**Name**: `verifimind-genesis`
**Version**: 0.2.0
**Repository**: https://github.com/creator35lwb-web/VerifiMind-PEAS

---

## 📚 Resources (4 total)

### 1. `genesis://config/master_prompt`
**Description**: Genesis Master Prompt v16.1
- Complete prompt defining roles for X Intelligent, Z Guardian, and CS Security agents
- Ensures consistent agent behavior across all validation workflows
- Format: Markdown
- Version: v16.1

### 2. `genesis://history/latest`
**Description**: Latest Validation Result
- Most recent validation result from VerifiMind-PEAS
- Includes agent perspectives (X, Z, CS)
- Includes conflict resolution and final verdict
- Format: JSON

### 3. `genesis://history/all`
**Description**: Complete Validation History
- All validation results from the project
- Historical record of all agent consultations
- Format: JSON

### 4. `genesis://state/project_info`
**Description**: Project Information
- Metadata about VerifiMind-PEAS project
- Architecture details (RefleXion Trinity: X-Z-CS)
- Agent roles and capabilities
- Version information
- Documentation links
- Format: JSON

---

## 🔧 Tools (4 total)

### 1. `consult_agent_x`
**Purpose**: Consult X Intelligent agent for innovation and strategy analysis

**Capabilities**:
- Innovation potential assessment
- Strategic value analysis
- Market opportunity identification
- Competitive positioning
- Growth potential evaluation

**Parameters**:
- `concept_name` (required): Short name or title of the concept
- `concept_description` (required): Detailed description
- `context` (optional): Additional context or background

**Returns**: Structured analysis with reasoning chain, scores, and recommendations

---

### 2. `consult_agent_z`
**Purpose**: Consult Z Guardian agent for ethical review and Z-Protocol enforcement

**Capabilities**:
- Ethics assessment
- Privacy evaluation
- Bias detection
- Social impact analysis
- Z-Protocol compliance check
- **Has veto power** over concepts

**Parameters**:
- `concept_name` (required): Short name or title of the concept
- `concept_description` (required): Detailed description
- `context` (optional): Additional context or background

**Returns**: Ethical analysis with veto power if concerns found

---

### 3. `consult_agent_cs`
**Purpose**: Consult CS Security agent for security validation

**Capabilities**:
- Security vulnerability assessment
- Attack vector identification
- Socratic interrogation methodology
- Security best practices validation
- Threat modeling

**Parameters**:
- `concept_name` (required): Short name or title of the concept
- `concept_description` (required): Detailed description
- `context` (optional): Additional context or background

**Returns**: Security analysis with vulnerability assessment

---

### 4. `run_full_trinity`
**Purpose**: Run complete X → Z → CS validation pipeline

**Capabilities**:
- Orchestrates all three agents in sequence
- Handles conflict resolution
- Provides comprehensive validation verdict
- Saves results to validation history

**Parameters**:
- `concept_name` (required): Short name or title of the concept
- `concept_description` (required): Detailed description
- `context` (optional): Additional context or background

**Returns**: Complete validation report with all agent perspectives and final verdict

---

## 🏗️ Architecture

**RefleXion Trinity**:
1. **X Intelligent** - Innovation and Strategy Engine
2. **Z Guardian** - Ethical Review (with veto power)
3. **CS Security** - Security Validation (Socratic method)

**Validation Flow**:
```
Concept → X (Innovation) → Z (Ethics) → CS (Security) → Final Verdict
```

---

## 🔑 Configuration

**LLM Providers Supported**:
- OpenAI (requires API key)
- Anthropic (requires API key)
- Mock Provider (for testing, no API key needed)

**Configuration Options**:
- `llm_provider`: "openai", "anthropic", or "mock"
- `openai_api_key`: OpenAI API key (optional)
- `anthropic_api_key`: Anthropic API key (optional)
- `validation_mode`: "standard" or "strict"

---

## 📖 Documentation

- **White Paper**: https://github.com/creator35lwb-web/VerifiMind-PEAS/docs/white_paper/Genesis_Methodology_White_Paper_v1.1.md
- **Repository**: https://github.com/creator35lwb-web/VerifiMind-PEAS
- **Master Prompts**: https://github.com/creator35lwb-web/VerifiMind-PEAS/reflexion-master-prompts-v1.1.md

---

## ✅ Status

- ✅ Server imports successfully
- ✅ Server creates successfully
- ✅ 4 resources registered
- ✅ 4 tools registered
- ✅ Ready for local installation
- ✅ Ready for marketplace listing
