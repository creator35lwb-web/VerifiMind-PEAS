"""
VerifiMind Complete System - Idea to App in One Command
Full end-to-end orchestration: X, Z, CS agents -> Socratic Validation -> PDF Report -> Iterative Generation
"""

import asyncio
import sys
import argparse
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.core.logging_config import setup_logging, get_logger
from src.agents import (
    XIntelligentAgent,
    ZGuardianAgent,
    CSSecurityAgent,
    AgentOrchestrator,
    ConceptInput
)
from src.generation import (
    IterativeCodeGenerationEngine,
    AppSpecification,
    ValidationReportGenerator  # NEW: Import PDF Generator
)
from src.llm.llm_provider import LLMProviderFactory

# Get logger for this module
logger = get_logger(__name__)


class VerifiMindComplete:
    """
    Complete VerifiMind System - Orchestrates entire flow from idea to app.
    
    Updated for v2.0-beta:
    - Integrates 'Concept Scrutinizer' Socratic Engine
    - Generates PDF Validation Report
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}

        # Initialize LLM provider
        provider_type = self.config.get('llm_provider', 'openai')
        api_key = self.config.get('openai_api_key') or self.config.get('anthropic_api_key')
        self.llm = LLMProviderFactory.create_provider(provider_type=provider_type, api_key=api_key)

        logger.info(f"Initialized LLM provider: {provider_type}")

        # Initialize validation agents (RefleXion Trinity)
        self.x_agent = XIntelligentAgent("x-1", self.llm, self.config)
        self.z_agent = ZGuardianAgent("z-1", self.llm, self.config)
        
        # CS Agent now includes the 'Concept Scrutinizer' Engine
        self.cs_agent = CSSecurityAgent("cs-1", self.llm, self.config)
        
        self.orchestrator = AgentOrchestrator(self.x_agent, self.z_agent, self.cs_agent)

        logger.info("Initialized validation agents: X, Z, CS (with Socratic Engine)")

        # Initialize iterative generator
        self.generator = IterativeCodeGenerationEngine(
            config=self.config,
            llm_provider=self.llm,
            max_iterations=self.config.get('max_iterations', 3),
            quality_threshold=self.config.get('quality_threshold', 85)
        )
        
        # Initialize PDF Reporter
        self.pdf_reporter = ValidationReportGenerator(output_dir=self.config.get('output_dir', 'output'))

    async def create_app_from_idea(
        self,
        idea_description: str,
        app_name: Optional[str] = None,
        category: Optional[str] = None,
        output_dir: str = "output"
    ):
        """
        Complete flow: Idea -> Socratic Validation -> PDF Report -> App Generation
        """

        logger.info(f"Starting app generation from idea: {idea_description[:100]}...")

        print("\n" + "="*70)
        print("VerifiMind™ PEAS - Genesis Ecosystem v2.0-beta")
        print("="*70)
        print(f"\nYour Idea: {idea_description}\n")

        # --- PHASE 1: GENESIS VALIDATION (X-Z-CS TRINITY) ---
        print("="*70)
        print("PHASE 1: GENESIS VALIDATION (The Trinity)")
        print("="*70 + "\n")
        logger.info("Phase 1: Starting Socratic validation")

        concept = ConceptInput(
            id=f"concept-{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}",
            description=idea_description,
            category=category,
            user_context={},
            session_id=f"session-{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}"
        )

        # 1. Run Agents (Includes Deep Socratic Scrutiny in CS Agent)
        print("Running X, Z, CS agents in parallel...")
        print("   🧠 X Intelligent: Analyzing Innovation & Market Strategy...")
        print("   ⚖️  Z Guardian: Validating Ethics & Child Digital Health...")
        print("   🛡️  CS Security: Executing Socratic Concept Scrutiny...")
        
        agent_results = await self.orchestrator.run_full_analysis(concept)

        # 2. Conflict Resolution
        decision = self.orchestrator.resolve_conflicts(agent_results)
        self._print_agent_results(agent_results, decision)

        # 3. STOP if Rejected
        if decision['decision'] == 'reject':
            logger.warning(f"Concept rejected: {decision['reason']}")
            print(f"\n[X] CONCEPT REJECTED by Trinity Protocol")
            print(f"Reason: {decision['reason']}")
            return None, None

        # --- PHASE 1.5: GENERATE VALIDATION REPORT ---
        print("\n" + "-"*70)
        print("Generating Genesis Validation Report...")
        
        # Build temp app spec for the report header
        temp_spec = await self._build_app_spec(idea_description, app_name, category, agent_results)
        
        # Extract deep Socratic data from CS agent response
        cs_result = agent_results.get('CS')
        socratic_data = cs_result.socratic_analysis if hasattr(cs_result, 'socratic_analysis') else {}
        
        # Generate PDF
        pdf_path = self.pdf_reporter.generate(temp_spec, agent_results, socratic_data)
        
        print(f"✅ REPORT GENERATED: {pdf_path}")
        print(f"   (Includes: Socratic Challenges, Strategic Roadmap, IP Proof)")
        print("-" * 70 + "\n")

        # Optional: Ask user to confirm before code generation?
        # confirm = input("Proceed to Code Generation? (y/n): ")
        # if confirm.lower() != 'y': return None, None

        # --- PHASE 2: APPLICATION SPECIFICATION ---
        print("="*70)
        print("PHASE 2: BUILDING APPLICATION SPECIFICATION")
        print("="*70 + "\n")
        
        # Use the spec we already built
        app_spec = temp_spec 

        logger.info(f"App specification complete: {app_spec.app_name}")
        print(f"[OK] Application Specification Ready")
        print(f"   App Name: {app_spec.app_name}")
        print(f"   Category: {app_spec.category}")
        print(f"   Core Features: {len(app_spec.core_features)}")
        print(f"   Compliance Level: {len(app_spec.compliance_features)} Constraints")

        # --- PHASE 3: ITERATIVE CODE GENERATION ---
        print("\n" + "="*70)
        print("PHASE 3: ITERATIVE CODE GENERATION")
        print("="*70 + "\n")
        
        generated_app, history = await self.generator.generate_with_iterations(
            spec=app_spec,
            output_dir=output_dir
        )

        # --- PHASE 4: FINAL OUTPUT ---
        print("\n" + "="*70)
        print("[OK] GENESIS CYCLE COMPLETE!")
        print("="*70)
        
        self._print_final_output(generated_app, history, app_spec.app_name, output_dir, pdf_path)

        return generated_app, history

    # ... [Keep existing helper methods: _build_app_spec, _detect_category, etc.] ...

    def _print_final_output(self, generated_app, history, app_name: str, output_dir: str, pdf_path: str):
        """Print final output information including Report"""
        print(f"\n[SUCCESS] APPLICATION GENERATED SUCCESSFULLY!")
        print(f"\n[OUTPUT] Deliverables:")
        print(f"   📂 Codebase:   {output_dir}/{app_name}/")
        print(f"   📄 Report:     {pdf_path}")
        
        print(f"\n[METRICS] Quality Metrics:")
        print(f"   Final Score: {history.final_score:.1f}/100")
        print(f"   Improvement: +{history.improvement_percentage:.1f}%")
        print(f"   Total Iterations: {history.total_iterations}")

        print(f"\n[NEXT] Next Steps:")
        print(f"   1. Review {os.path.basename(pdf_path)} for strategic insights")
        print(f"   2. cd {output_dir}/{app_name} && npm install")
        print(f"   3. Deploy using: npm run deploy")

# ... [Keep existing parse_arguments and main functions] ...