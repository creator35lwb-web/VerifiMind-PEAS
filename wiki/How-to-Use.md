# How to Use VerifiMind PEAS

**Step-by-Step Guide to Validating AI Concepts**

---

## Quick Start

**Three ways to use VerifiMind PEAS**:

1. **Browse the Database** - Learn from 80+ existing validations
2. **Use the MCP Server** - Validate your own concepts with Claude Desktop
3. **Run Locally** - Use Python scripts for batch validation

---

## Option 1: Browse the Validation Database

**Best for**: Learning, market research, avoiding mistakes

### Step 1: Explore Categories

Browse validations by industry:
- [Climate & Sustainability](https://github.com/creator35lwb-web/VerifiMind-PEAS/tree/main/examples/validations) (100% approval)
- [Gaming & Entertainment](https://github.com/creator35lwb-web/VerifiMind-PEAS/tree/main/examples/validations) (70% approval)
- [Fintech & Banking](https://github.com/creator35lwb-web/VerifiMind-PEAS/tree/main/examples/validations) (60% approval)
- And 8 more categories...

### Step 2: Read Validation Reports

Each validation includes:
- Innovation analysis (X Agent)
- Ethical evaluation (Z Agent)
- Security assessment (CS Agent)
- Trinity synthesis and verdict
- Detailed recommendations

### Step 3: Learn from Patterns

**High-approval categories**:
- Climate & Sustainability (100%)
- Education (100%)
- Gaming (70%)

**High-risk categories**:
- Social Media (40% approval)
- E-commerce (40% approval)
- Healthcare (67% approval, high veto risk)

**Common veto reasons**:
- Discrimination and bias
- Privacy violations
- Market manipulation
- Patient safety concerns

---

## Option 2: Use the MCP Server with Claude Desktop

**Best for**: Interactive validation, real-time feedback

### Prerequisites

- Claude Desktop app installed
- Python 3.11+ installed
- Git installed

### Step 1: Install the MCP Server

```bash
# Clone the repository
git clone https://github.com/creator35lwb-web/VerifiMind-PEAS.git
cd VerifiMind-PEAS/mcp-server

# Install dependencies
pip install -e .
```

### Step 2: Configure Claude Desktop

Add to your Claude Desktop MCP configuration:

**macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
**Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "verifimind-genesis": {
      "command": "python",
      "args": [
        "-m",
        "verifimind_mcp"
      ],
      "env": {
        "LLM_PROVIDER": "mock",
        "ENABLE_LOGGING": "true"
      }
    }
  }
}
```

**For real LLM validation**, set environment variables:
```json
"env": {
  "LLM_PROVIDER": "openai",
  "OPENAI_API_KEY": "your-api-key-here",
  "ENABLE_LOGGING": "true"
}
```

### Step 3: Restart Claude Desktop

Restart Claude Desktop to load the MCP server.

### Step 4: Validate a Concept

In Claude Desktop, use the MCP tools:

**Example prompt**:
```
Please validate this AI concept using the VerifiMind PEAS methodology:

Concept: AI-Powered Personal Finance Assistant
Description: A mobile app that analyzes spending patterns, suggests budgets, 
and provides personalized financial advice using machine learning.
Category: Fintech
Context: Target users are millennials and Gen Z. Platform is iOS and Android.
```

**Claude will**:
1. Call `consult_agent_x` for innovation analysis
2. Call `consult_agent_z` for ethical evaluation
3. Call `consult_agent_cs` for security assessment
4. Call `run_full_trinity` for synthesis
5. Provide comprehensive validation report

### Step 5: Review Results

Claude will present:
- Innovation Score (0-10)
- Ethics Score (0-10)
- Security Score (0-10)
- Overall Score (0-10)
- Final Verdict (APPROVED/CONDITIONAL/VETOED)
- Detailed recommendations

---

## Option 3: Run Locally with Python

**Best for**: Batch validation, automation, research

### Prerequisites

- Python 3.11+
- OpenAI or Anthropic API key

### Step 1: Clone and Install

```bash
git clone https://github.com/creator35lwb-web/VerifiMind-PEAS.git
cd VerifiMind-PEAS/mcp-server
pip install -e .
```

### Step 2: Set API Keys

```bash
export OPENAI_API_KEY="your-openai-key"
export ANTHROPIC_API_KEY="your-anthropic-key"
```

### Step 3: Create Validation Script

```python
import asyncio
from verifimind_mcp.agents import XAgent, ZAgent, CSAgent
from verifimind_mcp.models import Concept, PriorReasoning
from verifimind_mcp.llm import OpenAIProvider

async def validate_concept():
    # Initialize provider
    provider = OpenAIProvider(api_key="your-key", model="gpt-4")
    
    # Create agents
    x_agent = XAgent(llm_provider=provider)
    z_agent = ZAgent(llm_provider=provider)
    cs_agent = CSAgent(llm_provider=provider)
    
    # Define concept
    concept = Concept(
        name="AI-Powered Personal Finance Assistant",
        description="Mobile app analyzing spending and providing advice",
        category="Fintech",
        context="Target: Millennials and Gen Z. Platform: iOS and Android."
    )
    
    # Run Trinity validation
    # Step 1: X Agent
    x_result = await x_agent.analyze(concept)
    print(f"Innovation Score: {x_result.innovation_score}/10")
    
    # Step 2: Z Agent (with X's reasoning)
    prior_for_z = PriorReasoning()
    prior_for_z.add(x_result.to_chain_of_thought(concept.name))
    
    z_result = await z_agent.analyze(concept, prior_reasoning=prior_for_z)
    print(f"Ethics Score: {z_result.ethics_score}/10")
    print(f"Veto: {z_result.veto_triggered}")
    
    # Step 3: CS Agent (with X and Z reasoning)
    prior_for_cs = PriorReasoning()
    prior_for_cs.add(x_result.to_chain_of_thought(concept.name))
    prior_for_cs.add(z_result.to_chain_of_thought(concept.name))
    
    cs_result = await cs_agent.analyze(concept, prior_reasoning=prior_for_cs)
    print(f"Security Score: {cs_result.security_score}/10")
    
    # Calculate overall
    overall = (x_result.innovation_score + z_result.ethics_score + cs_result.security_score) / 3
    print(f"\nOverall Score: {overall:.1f}/10")
    
    # Determine verdict
    if z_result.veto_triggered:
        print("Verdict: VETOED")
    elif overall >= 7.0:
        print("Verdict: APPROVED")
    elif overall >= 5.0:
        print("Verdict: CONDITIONAL")
    else:
        print("Verdict: REJECTED")

# Run validation
asyncio.run(validate_concept())
```

### Step 4: Run the Script

```bash
python validate_my_concept.py
```

---

## Understanding the Results

### Innovation Score (X Agent)

**8-10**: Highly innovative
- Strong market potential
- Clear competitive advantage
- High strategic value
- **Action**: Proceed with confidence

**6-7**: Moderately innovative
- Viable opportunity
- Some differentiation
- Moderate strategic value
- **Action**: Proceed with refinements

**4-5**: Low innovation
- Incremental improvement
- Limited differentiation
- Low strategic value
- **Action**: Reconsider or pivot

**0-3**: No innovation
- No clear value proposition
- Crowded market
- Not recommended
- **Action**: Do not proceed

### Ethics Score (Z Agent)

**8-10**: Ethically sound
- Z-Protocol compliant
- No significant concerns
- Clear ethical framework
- **Action**: Proceed

**6-7**: Minor ethical concerns
- Some risks identified
- Mitigations recommended
- Z-Protocol mostly satisfied
- **Action**: Implement mitigations

**4-5**: Significant ethical issues
- Major concerns identified
- Extensive mitigations required
- Z-Protocol violations possible
- **Action**: Major redesign needed

**0-3**: Severe ethical violations
- Red lines crossed
- Veto likely or triggered
- Not ethically acceptable
- **Action**: Do not proceed

### Security Score (CS Agent)

**8-10**: Strong security
- Low risk profile
- Best practices followed
- Few vulnerabilities
- **Action**: Proceed with standard security

**6-7**: Moderate security risks
- Some vulnerabilities identified
- Standard mitigations needed
- Manageable risk
- **Action**: Implement recommendations

**4-5**: Significant vulnerabilities
- Multiple security issues
- Extensive mitigations required
- High risk
- **Action**: Major security work needed

**0-3**: Critical security flaws
- Severe vulnerabilities
- High attack surface
- Not secure
- **Action**: Complete redesign

### Final Verdict

**APPROVED** (Overall ≥ 7.0, no veto)
- Proceed with development
- Implement minor recommendations
- Monitor for issues

**CONDITIONAL** (Overall 5.0-6.9, no veto)
- Proceed with caution
- Implement all recommendations
- Address concerns before launch

**VETOED** (Z Agent veto triggered)
- Do not proceed
- Ethical red line crossed
- Redesign or abandon

**REJECTED** (Overall < 5.0)
- Do not proceed
- Major issues across dimensions
- Not viable

---

## Tips for Better Validations

### 1. Be Specific

**Bad**:
```
Concept: AI app for health
```

**Good**:
```
Concept: AI-Powered Mental Health Journaling App
Description: Mobile app that uses NLP to analyze journal entries and provide 
mood tracking, coping suggestions, and crisis detection with human therapist 
escalation.
Category: Healthcare & Wellness
Context: Target: Adults with mild anxiety/depression. Platform: iOS/Android. 
HIPAA compliant. Human therapists review flagged entries.
```

### 2. Include Context

Always provide:
- Target users
- Platform (web, mobile, API, etc.)
- Scale (local, regional, global)
- Business model (if relevant)
- Regulatory considerations

### 3. Be Honest About Risks

Don't hide potential issues:
- Data collection practices
- Algorithmic decision-making
- Potential for misuse
- Known limitations

**The agents will find them anyway, and honesty helps get better recommendations!**

### 4. Consider Alternatives

If your concept gets vetoed or rejected:
- Review the specific concerns
- Consider alternative approaches
- Add safeguards and mitigations
- Revalidate the revised concept

---

## Common Questions

**Q: How long does validation take?**
A: 30-60 seconds with MCP server, 2-3 minutes with Python scripts (depends on LLM provider).

**Q: How much does it cost?**
A: ~$0.08 per validation with GPT-4 + Claude. Free with mock provider (for testing).

**Q: Can I validate multiple concepts?**
A: Yes! Use Python scripts for batch validation. See examples in `/examples/`.

**Q: What if I disagree with the verdict?**
A: Review the reasoning steps, understand the concerns, and consider revising your concept. You can also contribute feedback to improve the methodology.

**Q: Can I use this for due diligence?**
A: Yes, but remember it's a tool, not a replacement for human judgment. Use it as one input in your decision-making process.

---

## Next Steps

1. **Try it**: Validate your first concept
2. **Learn more**: [Methodology](Methodology) | [Agent Guides](X-Agent-Guide)
3. **Contribute**: [Contributing Guide](Contributing)
4. **Get help**: [FAQ](FAQ) | [GitHub Discussions](https://github.com/creator35lwb-web/VerifiMind-PEAS/discussions)

---

**Ready to validate your AI concept?** 🚀
