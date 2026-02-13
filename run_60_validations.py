#!/usr/bin/env python3
"""
Production Trinity Validation Runner

Runs 60 Trinity validations with Gemini + Claude and generates complete reports.
"""

import asyncio
import csv
import json
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict

# Add mcp-server to path
sys.path.insert(0, str(Path(__file__).parent / "mcp-server" / "src"))

from verifimind_mcp.llm.provider import GeminiProvider, AnthropicProvider
from verifimind_mcp.agents.x_agent import XAgent
from verifimind_mcp.agents.z_agent import ZAgent
from verifimind_mcp.agents.cs_agent import CSAgent
from verifimind_mcp.models.concepts import Concept
from verifimind_mcp.utils.metrics import AgentMetrics, ValidationMetrics, METRICS_COLLECTOR
from verifimind_mcp.utils.synthesis import create_trinity_result
from verifimind_mcp.config.standard_config import DEFAULT_CONFIG

import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class TrinityReportRunner:
    """Runs Trinity validations and generates reports."""
    
    def __init__(self, output_dir: Path):
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize providers
        logger.info("Initializing providers...")
        self.gemini_provider = GeminiProvider(model=DEFAULT_CONFIG.llm.x_agent_model)
        self.claude_provider_z = AnthropicProvider(model=DEFAULT_CONFIG.llm.z_agent_model)
        self.claude_provider_cs = AnthropicProvider(model=DEFAULT_CONFIG.llm.cs_agent_model)
        
        # Initialize agents
        self.x_agent = XAgent(llm_provider=self.gemini_provider)
        self.z_agent = ZAgent(llm_provider=self.claude_provider_z)
        self.cs_agent = CSAgent(llm_provider=self.claude_provider_cs)
        
        logger.info(f"X Agent: {self.gemini_provider.get_model_name()}")
        logger.info(f"Z Agent: {self.claude_provider_z.get_model_name()}")
        logger.info(f"CS Agent: {self.claude_provider_cs.get_model_name()}")
    
    def sanitize_filename(self, name: str, index: int) -> str:
        """Create safe filename."""
        safe = "".join(c if c.isalnum() or c in (' ', '-', '_') else '' for c in name)
        safe = safe.replace(' ', '_').lower()[:80]
        return f"{index:03d}_{safe}.txt"
    
    async def validate_concept(self, index: int, concept_name: str, concept_desc: str) -> Dict:
        """Run Trinity validation on a concept."""
        logger.info(f"[{index}/60] Validating: {concept_name[:60]}...")
        
        try:
            # Create concept
            concept = Concept(
                name=concept_name,
                description=concept_desc,
                context=""
            )
            
            # Create metrics
            validation_metrics = ValidationMetrics(
                validation_id=f"val_{index:03d}",
                concept_name=concept_name
            )
            x_metrics = AgentMetrics(agent_type="x", model_name=self.gemini_provider.get_model_name())
            z_metrics = AgentMetrics(agent_type="z", model_name=self.claude_provider_z.get_model_name())
            cs_metrics = AgentMetrics(agent_type="cs", model_name=self.claude_provider_cs.get_model_name())
            
            # Run agents
            x_result = await self.x_agent.analyze(concept, metrics=x_metrics)
            z_result = await self.z_agent.analyze(concept, metrics=z_metrics)
            cs_result = await self.cs_agent.analyze(concept, metrics=cs_metrics)
            
            # Create synthesis
            synthesis = create_trinity_result(
                concept_name=concept.name,
                concept_description=concept.description,
                x_result=x_result,
                z_result=z_result,
                cs_result=cs_result
            )
            
            # Update validation metrics
            validation_metrics.x_agent = x_metrics
            validation_metrics.z_agent = z_metrics
            validation_metrics.cs_agent = cs_metrics
            validation_metrics.overall_score = synthesis.synthesis.overall_score
            validation_metrics.verdict = synthesis.synthesis.recommendation
            validation_metrics.finish()
            
            # Add to collector
            METRICS_COLLECTOR.add_validation(validation_metrics)
            
            # Generate report
            report = self.generate_report(
                index, concept, x_result, z_result, cs_result,
                synthesis, validation_metrics
            )
            
            # Save report
            filename = self.sanitize_filename(concept_name, index)
            report_path = self.output_dir / filename
            report_path.write_text(report)
            
            logger.info(f"  ✅ Score: {synthesis.synthesis.overall_score:.1f}/10, "
                       f"Duration: {validation_metrics.total_duration:.1f}s, "
                       f"Cost: ${validation_metrics.total_cost:.6f}")
            
            return {
                "index": index,
                "concept_name": concept_name,
                "score": synthesis.synthesis.overall_score,
                "verdict": synthesis.synthesis.recommendation,
                "duration": validation_metrics.total_duration,
                "cost": validation_metrics.total_cost,
                "success": True
            }
            
        except Exception as e:
            logger.error(f"  ❌ Failed: {e}")
            return {
                "index": index,
                "concept_name": concept_name,
                "error": str(e),
                "success": False
            }
    
    def generate_report(self, index, concept, x_result, z_result, cs_result, synthesis, metrics):
        """Generate formatted report."""
        x_score = (x_result.innovation_score + x_result.strategic_value) / 2
        
        report = f"""
================================================================================
VERIFIMIND TRINITY VALIDATION REPORT
================================================================================

Validation ID: val_{index:03d}
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Protocol: Standardization v1.0 (Gemini + Claude)

================================================================================
CONCEPT INFORMATION
================================================================================

Name: {concept.name}

Description:
{concept.description}

================================================================================
X AGENT ANALYSIS (Innovation & Strategy)
================================================================================

Model: {DEFAULT_CONFIG.llm.x_agent_model}
Innovation Score: {x_result.innovation_score:.1f}/10
Strategic Value: {x_result.strategic_value:.1f}/10
Average Score: {x_score:.1f}/10
Confidence: {x_result.confidence:.2f}

Reasoning Steps:
{self._format_reasoning_steps(x_result.reasoning_steps)}

Opportunities:
{self._format_list(x_result.opportunities)}

Risks:
{self._format_list(x_result.risks)}

Recommendation:
{x_result.recommendation}

================================================================================
Z AGENT ANALYSIS (Ethics & Responsibility)
================================================================================

Model: {DEFAULT_CONFIG.llm.z_agent_model}
Ethics Score: {z_result.ethics_score:.1f}/10
Confidence: {z_result.confidence:.2f}
Veto Triggered: {z_result.veto_triggered}

Reasoning Steps:
{self._format_reasoning_steps(z_result.reasoning_steps)}

Ethical Concerns:
{self._format_list(z_result.ethical_concerns)}

Mitigation Measures:
{self._format_list(z_result.mitigation_measures)}

================================================================================
CS AGENT ANALYSIS (Security & Privacy)
================================================================================

Model: {DEFAULT_CONFIG.llm.cs_agent_model}
Security Score: {cs_result.security_score:.1f}/10
Confidence: {cs_result.confidence:.2f}

Reasoning Steps:
{self._format_reasoning_steps(cs_result.reasoning_steps)}

Vulnerabilities:
{self._format_list(cs_result.vulnerabilities)}

Security Recommendations:
{self._format_list(cs_result.security_recommendations)}

================================================================================
TRINITY SYNTHESIS
================================================================================

Overall Score: {synthesis.synthesis.overall_score:.1f}/10
Recommendation: {synthesis.synthesis.recommendation.upper()}
Confidence: {synthesis.synthesis.confidence:.2f}

Summary:
{synthesis.synthesis.summary}

Strengths:
{self._format_list(synthesis.synthesis.strengths)}

Concerns:
{self._format_list(synthesis.synthesis.concerns)}

Recommendations:
{self._format_list(synthesis.synthesis.recommendations)}

================================================================================
PERFORMANCE METRICS
================================================================================

Total Duration: {metrics.total_duration:.2f}s
Total Tokens: {metrics.total_tokens}
Total Cost: ${metrics.total_cost:.6f}

Agent Breakdown:
- X Agent (Gemini):  {metrics.x_agent.latency:.2f}s, {metrics.x_agent.total_tokens} tokens, ${metrics.x_agent.total_cost:.6f}
- Z Agent (Claude):  {metrics.z_agent.latency:.2f}s, {metrics.z_agent.total_tokens} tokens, ${metrics.z_agent.total_cost:.6f}
- CS Agent (Claude): {metrics.cs_agent.latency:.2f}s, {metrics.cs_agent.total_tokens} tokens, ${metrics.cs_agent.total_cost:.6f}

================================================================================
END OF REPORT
================================================================================
"""
        return report
    
    def _format_reasoning_steps(self, steps):
        """Format reasoning steps."""
        if not steps:
            return "  (No reasoning steps provided)"
        return "\n".join([
            f"  {i+1}. {step.thought} (confidence: {step.confidence:.2f})"
            for i, step in enumerate(steps)
        ])
    
    def _format_list(self, items):
        """Format list items."""
        if not items:
            return "  (None)"
        return "\n".join([f"  - {item}" for item in items])


async def main():
    """Main execution."""
    csv_file = Path("examples/reports/validate_concepts_batch_2.csv")
    output_dir = Path("validation_reports_gemini_claude")
    
    logger.info("=" * 70)
    logger.info("VERIFIMIND TRINITY VALIDATION - 60 CONCEPTS")
    logger.info("=" * 70)
    logger.info(f"Input: {csv_file}")
    logger.info(f"Output: {output_dir}")
    logger.info(f"Protocol: Gemini (X) + Claude (Z, CS)")
    logger.info("=" * 70)
    
    # Read CSV
    concepts = []
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Extract concept name and description from Subject field
            subject = row['Subject']
            # Split on colon to separate name and description
            if ':' in subject:
                name, desc = subject.split(':', 1)
                concepts.append((name.strip(), subject.strip()))
            else:
                concepts.append((subject[:50].strip(), subject.strip()))
    
    logger.info(f"Loaded {len(concepts)} concepts")
    
    # Initialize runner
    runner = TrinityReportRunner(output_dir)
    
    # Run validations
    results = []
    for i, (name, desc) in enumerate(concepts, 1):
        result = await runner.validate_concept(i, name, desc)
        results.append(result)
    
    # Save summary
    summary = {
        "total_validations": len(results),
        "successful": sum(1 for r in results if r["success"]),
        "failed": sum(1 for r in results if not r["success"]),
        "total_cost": sum(r.get("cost", 0) for r in results if r["success"]),
        "average_duration": sum(r.get("duration", 0) for r in results if r["success"]) / max(sum(1 for r in results if r["success"]), 1),
        "results": results,
        "metrics": METRICS_COLLECTOR.get_summary()
    }
    
    summary_path = output_dir / "summary.json"
    with open(summary_path, 'w') as f:
        json.dump(summary, f, indent=2)
    
    logger.info("=" * 70)
    logger.info("FINAL SUMMARY")
    logger.info("=" * 70)
    logger.info(f"Total Validations: {summary['total_validations']}")
    logger.info(f"Successful: {summary['successful']}")
    logger.info(f"Failed: {summary['failed']}")
    logger.info(f"Success Rate: {summary['successful']/summary['total_validations']*100:.1f}%")
    logger.info(f"Total Cost: ${summary['total_cost']:.6f}")
    logger.info(f"Average Duration: {summary['average_duration']:.2f}s")
    logger.info("=" * 70)
    logger.info(f"Reports saved to: {output_dir}")
    logger.info(f"Summary saved to: {summary_path}")
    
    return 0 if summary['failed'] == 0 else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
