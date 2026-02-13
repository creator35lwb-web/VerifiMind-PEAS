#!/usr/bin/env python3
"""
Trinity Validation Test with Gemini + Claude

Tests full Trinity validation with:
- X Agent: Gemini (Innovation)
- Z Agent: Claude (Ethics)
- CS Agent: Claude (Security)
"""

import asyncio
import sys
from pathlib import Path

# Add mcp-server to path
sys.path.insert(0, str(Path(__file__).parent / "mcp-server" / "src"))

from verifimind_mcp.llm.provider import GeminiProvider, AnthropicProvider
from verifimind_mcp.agents.x_agent import XAgent
from verifimind_mcp.agents.z_agent import ZAgent
from verifimind_mcp.agents.cs_agent import CSAgent
from verifimind_mcp.models.concepts import Concept
from verifimind_mcp.utils.metrics import AgentMetrics, ValidationMetrics
from verifimind_mcp.utils.synthesis import create_trinity_result
from verifimind_mcp.models.reasoning import PriorReasoning
from verifimind_mcp.config.standard_config import DEFAULT_CONFIG


async def test_trinity_validation():
    """Test full Trinity validation."""
    print("🧪 Testing Trinity Validation (Gemini + Claude)")
    print("=" * 70)
    
    # Test concept
    concept = Concept(
        name="AI-Powered Fraud Detection for Banking",
        description="Real-time fraud detection system using machine learning to identify suspicious transactions and prevent financial crimes. Target: Banks and financial institutions.",
        context=""
    )
    
    print(f"\n📝 Concept: {concept.name}")
    
    try:
        # Initialize providers
        print("\n🔧 Initializing providers...")
        gemini_provider = GeminiProvider(model=DEFAULT_CONFIG.llm.x_agent_model)
        claude_provider_z = AnthropicProvider(model=DEFAULT_CONFIG.llm.z_agent_model)
        claude_provider_cs = AnthropicProvider(model=DEFAULT_CONFIG.llm.cs_agent_model)
        
        # Initialize agents
        x_agent = XAgent(llm_provider=gemini_provider)
        z_agent = ZAgent(llm_provider=claude_provider_z)
        cs_agent = CSAgent(llm_provider=claude_provider_cs)
        
        print(f"   X Agent: {gemini_provider.get_model_name()}")
        print(f"   Z Agent: {claude_provider_z.get_model_name()}")
        print(f"   CS Agent: {claude_provider_cs.get_model_name()}")
        
        # Create metrics
        validation_metrics = ValidationMetrics(
            validation_id="test_001",
            concept_name=concept.name
        )
        x_metrics = AgentMetrics(agent_type="x", model_name=gemini_provider.get_model_name())
        z_metrics = AgentMetrics(agent_type="z", model_name=claude_provider_z.get_model_name())
        cs_metrics = AgentMetrics(agent_type="cs", model_name=claude_provider_cs.get_model_name())
        
        # Run X Agent
        print("\n🚀 Running X Agent (Innovation Analysis)...")
        x_result = await x_agent.analyze(concept, metrics=x_metrics)
        x_score = (x_result.innovation_score + x_result.strategic_value) / 2
        print(f"   ✅ Score: {x_score:.1f}/10")
        print(f"   ✅ Tokens: {x_metrics.total_tokens}, Cost: ${x_metrics.total_cost:.6f}")
        
        # Run Z Agent
        print("\n🛡️ Running Z Agent (Ethics Analysis)...")
        z_result = await z_agent.analyze(concept, metrics=z_metrics)
        print(f"   ✅ Score: {z_result.ethics_score:.1f}/10")
        print(f"   ✅ Veto: {z_result.veto_triggered}")
        print(f"   ✅ Tokens: {z_metrics.total_tokens}, Cost: ${z_metrics.total_cost:.6f}")
        
        # Run CS Agent
        print("\n🔒 Running CS Agent (Security Analysis)...")
        cs_result = await cs_agent.analyze(concept, metrics=cs_metrics)
        print(f"   ✅ Score: {cs_result.security_score:.1f}/10")
        print(f"   ✅ Tokens: {cs_metrics.total_tokens}, Cost: ${cs_metrics.total_cost:.6f}")
        
        # Create Trinity synthesis
        print("\n⚖️ Creating Trinity Synthesis...")
        
        # Create PriorReasoning objects
        _x_prior = PriorReasoning(
            agent_id="X",
            reasoning_steps=x_result.reasoning_steps,
            confidence=x_result.confidence
        )
        _xz_prior = PriorReasoning(
            agent_id="Z",
            reasoning_steps=z_result.reasoning_steps,
            confidence=z_result.confidence
        )
        
        synthesis = create_trinity_result(
            concept_name=concept.name,
            concept_description=concept.description,
            x_result=x_result,
            z_result=z_result,
            cs_result=cs_result
        )
        
        print(f"   ✅ Overall Score: {synthesis.synthesis.overall_score:.1f}/10")
        print(f"   ✅ Verdict: {synthesis.synthesis.recommendation}")
        print(f"   ✅ Confidence: {synthesis.synthesis.confidence:.2f}")
        
        # Update validation metrics
        validation_metrics.x_metrics = x_metrics
        validation_metrics.z_metrics = z_metrics
        validation_metrics.cs_metrics = cs_metrics
        validation_metrics.overall_score = synthesis.synthesis.overall_score
        validation_metrics.verdict = synthesis.synthesis.recommendation
        validation_metrics.finish()
        
        print("\n📊 Final Metrics:")
        print(f"   Total Duration: {validation_metrics.total_duration:.2f}s")
        print(f"   Total Tokens: {validation_metrics.total_tokens}")
        print(f"   Total Cost: ${validation_metrics.total_cost:.6f}")
        print(f"   X Agent: ${x_metrics.total_cost:.6f}")
        print(f"   Z Agent: ${z_metrics.total_cost:.6f}")
        print(f"   CS Agent: ${cs_metrics.total_cost:.6f}")
        
        print("\n✅ Trinity validation successful!")
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(test_trinity_validation())
    sys.exit(0 if success else 1)
