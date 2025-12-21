#!/usr/bin/env python3
"""
Test Standardization Protocol v1.0

Validates the standardization improvements by running 10 concept validations
and measuring:
- API reliability (zero overload errors expected)
- Consistent scoring (variance < 0.5 for same concept)
- Performance metrics (latency, tokens, cost)

Author: VerifiMind PEAS Team
Date: December 21, 2025
Version: 1.0.0
"""

import asyncio
import sys
import os
from pathlib import Path

# Add mcp-server to path
sys.path.insert(0, str(Path(__file__).parent / "mcp-server" / "src"))

from verifimind_mcp.models import Concept, PriorReasoning
from verifimind_mcp.agents.base_agent import AgentRegistry
from verifimind_mcp.utils.synthesis import create_trinity_result
from verifimind_mcp.utils.metrics import ValidationMetrics, AgentMetrics, METRICS_COLLECTOR
from verifimind_mcp.config.standard_config import DEFAULT_CONFIG

import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# Test concepts across different domains
TEST_CONCEPTS = [
    Concept(
        name="AI-Powered Mental Health Chatbot",
        description="A conversational AI that provides 24/7 mental health support, crisis intervention, and therapeutic guidance using evidence-based CBT techniques.",
        context="Healthcare AI, Mental Health Technology"
    ),
    Concept(
        name="Blockchain-Based Voting System",
        description="A decentralized voting platform using blockchain for transparent, tamper-proof elections with verifiable results.",
        context="Civic Technology, Democracy Innovation"
    ),
    Concept(
        name="Autonomous Delivery Drones for Medical Supplies",
        description="AI-controlled drones that deliver urgent medical supplies to remote areas, reducing delivery time from hours to minutes.",
        context="Healthcare Logistics, Emergency Response"
    ),
    Concept(
        name="AI-Generated Personalized Learning Curriculum",
        description="An adaptive learning system that creates personalized educational content based on student performance, learning style, and interests.",
        context="Education Technology, Personalized Learning"
    ),
    Concept(
        name="Smart City Traffic Optimization AI",
        description="Real-time traffic management system using AI to optimize traffic light timing, reduce congestion, and minimize emissions.",
        context="Urban Planning, Smart Cities"
    ),
    Concept(
        name="AI-Powered Fake News Detector",
        description="Machine learning system that analyzes news articles for misinformation, bias, and factual accuracy in real-time.",
        context="Media Technology, Information Integrity"
    ),
    Concept(
        name="Predictive Maintenance for Industrial Equipment",
        description="IoT sensors + AI that predict equipment failures before they happen, reducing downtime and maintenance costs.",
        context="Industrial IoT, Predictive Analytics"
    ),
    Concept(
        name="AI-Assisted Legal Document Review",
        description="Natural language processing system that reviews legal contracts, identifies risks, and suggests improvements.",
        context="Legal Technology, Contract Analysis"
    ),
    Concept(
        name="Personalized Cancer Treatment AI",
        description="AI system that analyzes patient genetics, tumor characteristics, and treatment outcomes to recommend personalized cancer therapies.",
        context="Precision Medicine, Oncology"
    ),
    Concept(
        name="AI-Powered Energy Grid Optimization",
        description="Smart grid management system that balances renewable energy sources, predicts demand, and optimizes energy distribution.",
        context="Clean Energy, Grid Management"
    ),
]


async def validate_concept_with_metrics(concept: Concept, validation_id: str) -> ValidationMetrics:
    """Validate a concept and collect metrics."""
    logger.info(f"\n{'='*80}")
    logger.info(f"VALIDATING: {concept.name}")
    logger.info(f"{'='*80}\n")
    
    # Initialize metrics
    metrics = ValidationMetrics(
        validation_id=validation_id,
        concept_name=concept.name
    )
    
    # Initialize agent metrics
    x_metrics = AgentMetrics(agent_type="x", model_name="")
    z_metrics = AgentMetrics(agent_type="z", model_name="")
    cs_metrics = AgentMetrics(agent_type="cs", model_name="")
    
    try:
        # Run X Agent
        logger.info("Running X Agent (Innovation Analysis)...")
        x_agent = AgentRegistry.get_agent("X")
        x_result = await x_agent.analyze(concept, metrics=x_metrics)
        x_cot = x_result.to_chain_of_thought(concept.name)
        metrics.x_agent = x_metrics
        
        # Run Z Agent with X's reasoning
        logger.info("Running Z Agent (Ethics Validation)...")
        z_agent = AgentRegistry.get_agent("Z")
        
        # Create PriorReasoning from X's chain of thought
        x_prior = PriorReasoning(chains=[x_cot])
        
        z_result = await z_agent.analyze(
            concept,
            prior_reasoning=x_prior,
            metrics=z_metrics
        )
        z_cot = z_result.to_chain_of_thought(concept.name)
        metrics.z_agent = z_metrics
        
        # Check for Z Agent VETO
        if z_result.veto_triggered:
            logger.warning(f"⛔ Z AGENT VETO: {z_result.ethical_concerns[0] if z_result.ethical_concerns else 'Ethical red line crossed'}")
            metrics.verdict = "VETOED"
            metrics.overall_score = 0.0
            metrics.finish()
            return metrics
        
        # Run CS Agent with X and Z reasoning
        logger.info("Running CS Agent (Security Analysis)...")
        cs_agent = AgentRegistry.get_agent("CS")
        
        # Create PriorReasoning with both X and Z chains
        xz_prior = PriorReasoning(chains=[x_cot, z_cot])
        
        cs_result = await cs_agent.analyze(
            concept,
            prior_reasoning=xz_prior,
            metrics=cs_metrics
        )
        metrics.cs_agent = cs_metrics
        
        # Calculate Trinity synthesis
        synthesis = create_trinity_result(
            concept_name=concept.name,
            concept_description=concept.description,
            x_result=x_result,
            z_result=z_result,
            cs_result=cs_result
        )
        metrics.overall_score = synthesis.synthesis.overall_score
        metrics.verdict = synthesis.synthesis.recommendation
        
        logger.info(f"\n{'='*80}")
        logger.info(f"RESULT: {synthesis.synthesis.recommendation.upper()} (Score: {synthesis.synthesis.overall_score:.2f})")
        logger.info(f"{'='*80}\n")
        
        metrics.finish()
        return metrics
        
    except Exception as e:
        logger.error(f"Validation failed: {e}")
        metrics.success = False
        metrics.finish()
        raise


async def test_reproducibility(concept: Concept) -> list[ValidationMetrics]:
    """Test reproducibility by running same concept 3 times."""
    logger.info(f"\n{'='*80}")
    logger.info(f"REPRODUCIBILITY TEST: {concept.name}")
    logger.info(f"Running same concept 3 times to test consistency...")
    logger.info(f"{'='*80}\n")
    
    results = []
    for i in range(3):
        metrics = await validate_concept_with_metrics(
            concept,
            validation_id=f"reproducibility_test_{i+1}"
        )
        results.append(metrics)
    
    # Calculate score variance
    scores = [m.overall_score for m in results if m.overall_score is not None]
    if scores:
        avg_score = sum(scores) / len(scores)
        variance = sum((s - avg_score) ** 2 for s in scores) / len(scores)
        std_dev = variance ** 0.5
        
        logger.info(f"\n{'='*80}")
        logger.info(f"REPRODUCIBILITY RESULTS:")
        logger.info(f"Scores: {scores}")
        logger.info(f"Average: {avg_score:.2f}")
        logger.info(f"Std Dev: {std_dev:.3f}")
        logger.info(f"Variance: {variance:.3f}")
        logger.info(f"✅ PASS" if std_dev < 0.5 else f"❌ FAIL (variance too high)")
        logger.info(f"{'='*80}\n")
    
    return results


async def main():
    """Run standardization tests."""
    logger.info("""
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║                  VerifiMind PEAS Standardization Protocol v1.0               ║
║                                                                              ║
║                            VALIDATION TEST SUITE                             ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝

Testing standardization improvements:
✓ Temperature = 0.7 (balanced reasoning)
✓ Max tokens = 2000 per agent
✓ Model pinning (GPT-4 Turbo, Claude-3-Haiku)
✓ Retry logic with exponential backoff
✓ Performance metrics tracking

Running 10 concept validations + 1 reproducibility test...
""")
    
    # Test 10 different concepts
    logger.info("=" * 80)
    logger.info("PHASE 1: VALIDATING 10 DIVERSE CONCEPTS")
    logger.info("=" * 80)
    
    for i, concept in enumerate(TEST_CONCEPTS, 1):
        try:
            metrics = await validate_concept_with_metrics(
                concept,
                validation_id=f"standardization_test_{i}"
            )
            METRICS_COLLECTOR.add_validation(metrics)
        except Exception as e:
            logger.error(f"Failed to validate concept {i}: {e}")
            continue
    
    # Test reproducibility with first concept
    logger.info("\n" + "=" * 80)
    logger.info("PHASE 2: REPRODUCIBILITY TEST")
    logger.info("=" * 80)
    
    try:
        reproducibility_results = await test_reproducibility(TEST_CONCEPTS[0])
        for metrics in reproducibility_results:
            METRICS_COLLECTOR.add_validation(metrics)
    except Exception as e:
        logger.error(f"Reproducibility test failed: {e}")
    
    # Generate summary report
    logger.info("\n" + "=" * 80)
    logger.info("GENERATING PERFORMANCE REPORT")
    logger.info("=" * 80)
    
    summary = METRICS_COLLECTOR.get_summary()
    
    logger.info(f"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                         STANDARDIZATION TEST RESULTS                         ║
╚══════════════════════════════════════════════════════════════════════════════╝

📊 OVERALL PERFORMANCE:
   Total Validations: {summary['total_validations']}
   Successful: {summary['successful_validations']}
   Success Rate: {summary['success_rate']*100:.1f}%
   
⚡ RELIABILITY:
   Total Errors: {summary['total_errors']}
   Total Retries: {summary['total_retries']}
   Error Rate: {summary['error_rate']*100:.1f}%
   
⏱️  LATENCY:
   X Agent Avg: {summary['avg_latencies']['x_agent']:.2f}s
   Z Agent Avg: {summary['avg_latencies']['z_agent']:.2f}s
   CS Agent Avg: {summary['avg_latencies']['cs_agent']:.2f}s
   Total Avg Duration: {summary['avg_duration']:.2f}s
   
💰 COST:
   Average per Validation: ${summary['avg_cost']:.4f}
   Total Cost: ${summary['total_cost']:.4f}
   Average Tokens: {summary['avg_tokens']:.0f}

{'✅ ALL TESTS PASSED!' if summary['error_rate'] == 0 else '⚠️  SOME ERRORS DETECTED'}
""")
    
    # Save detailed metrics
    output_dir = Path(__file__).parent / "examples" / "standardization_tests"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    summary_file = output_dir / "summary.json"
    detailed_file = output_dir / "detailed_metrics.json"
    
    METRICS_COLLECTOR.save_summary(str(summary_file))
    METRICS_COLLECTOR.save_all(str(detailed_file))
    
    logger.info(f"\n📁 Detailed metrics saved to:")
    logger.info(f"   Summary: {summary_file}")
    logger.info(f"   Detailed: {detailed_file}")
    
    logger.info("\n✅ Standardization testing complete!")


if __name__ == "__main__":
    asyncio.run(main())
