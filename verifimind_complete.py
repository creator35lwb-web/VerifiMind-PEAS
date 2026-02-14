"""
VerifiMind Complete System v2.0.1 - Idea to App in One Command
Corrected Version - December 2025

Full end-to-end orchestration:
X, Z, CS agents -> Socratic Validation -> PDF Report -> Iterative Generation

Fixes Applied:
- All helper methods implemented (_build_app_spec, _detect_category, etc.)
- Fixed dict vs object attribute access for CS results
- Graceful PDF generation error handling (doesn't kill pipeline)
- Improved console output formatting
- Better error propagation and logging
"""

import asyncio
import sys
import argparse
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, Tuple, List
from dataclasses import dataclass, field
import uuid

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
)
from src.core.pdf_generator import ValidationReportGenerator
from src.llm.llm_provider import LLMProviderFactory

logger = get_logger(__name__)


# =============================================================================
# Data Classes
# =============================================================================

@dataclass
class GenerationHistory:
    """Track generation iteration history."""
    iterations: List[Dict[str, Any]] = field(default_factory=list)
    total_iterations: int = 0
    initial_score: float = 0.0
    final_score: float = 0.0
    improvement_percentage: float = 0.0
    
    def add_iteration(self, iteration_data: Dict[str, Any]):
        self.iterations.append(iteration_data)
        self.total_iterations = len(self.iterations)


@dataclass 
class AppSpecification:
    """Application specification for code generation."""
    app_id: str
    app_name: str
    description: str
    category: str
    core_features: List[str] = field(default_factory=list)
    compliance_features: List[str] = field(default_factory=list)
    tech_stack: Dict[str, str] = field(default_factory=dict)
    target_users: str = ""
    business_model: str = ""
    security_requirements: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'app_id': self.app_id,
            'app_name': self.app_name,
            'description': self.description,
            'category': self.category,
            'core_features': self.core_features,
            'compliance_features': self.compliance_features,
            'tech_stack': self.tech_stack,
            'target_users': self.target_users,
            'business_model': self.business_model,
            'security_requirements': self.security_requirements
        }


# =============================================================================
# Console Output Helpers
# =============================================================================

class ConsoleOutput:
    """Helper class for consistent console formatting."""
    
    RESET = '\033[0m'
    BOLD = '\033[1m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    
    @staticmethod
    def header(text: str, width: int = 70):
        print("\n" + "=" * width)
        print(text)
        print("=" * width)
    
    @staticmethod
    def subheader(text: str, width: int = 70):
        print("\n" + "-" * width)
        print(text)
        print("-" * width)
    
    @staticmethod
    def success(text: str):
        print(f"✅ {text}")
    
    @staticmethod
    def warning(text: str):
        print(f"⚠️  {text}")
    
    @staticmethod
    def error(text: str):
        print(f"❌ {text}")
    
    @staticmethod
    def info(text: str):
        print(f"ℹ️  {text}")
    
    @staticmethod
    def bullet(text: str, indent: int = 3):
        print(" " * indent + f"• {text}")


# =============================================================================
# Main Class
# =============================================================================

class VerifiMindComplete:
    """
    Complete VerifiMind System - Orchestrates entire flow from idea to app.
    
    v2.0.1 Features:
    - Integrates 'Concept Scrutinizer' Socratic Engine
    - Generates PDF Validation Report
    - Graceful error handling throughout
    - Complete helper method implementations
    """

    # Category keywords for auto-detection
    CATEGORY_KEYWORDS = {
        'health': ['health', 'medical', 'patient', 'doctor', 'hospital', 'clinic', 'wellness', 'fitness', 'therapy', 'mental health'],
        'finance': ['finance', 'banking', 'payment', 'investment', 'trading', 'money', 'budget', 'expense', 'crypto', 'wallet'],
        'education': ['education', 'learning', 'student', 'teacher', 'course', 'school', 'university', 'training', 'tutor'],
        'ecommerce': ['shop', 'store', 'product', 'cart', 'checkout', 'marketplace', 'retail', 'inventory', 'order'],
        'social': ['social', 'community', 'chat', 'messaging', 'friend', 'network', 'share', 'post', 'feed'],
        'productivity': ['productivity', 'task', 'project', 'workflow', 'schedule', 'calendar', 'todo', 'organize'],
        'ai_ml': ['ai', 'machine learning', 'ml', 'neural', 'model', 'prediction', 'automation', 'intelligent'],
        'iot': ['iot', 'device', 'sensor', 'smart home', 'connected', 'embedded', 'hardware'],
    }

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}

        # Initialize LLM provider
        provider_type = self.config.get('llm_provider', 'openai')
        api_key = self.config.get('openai_api_key') or self.config.get('anthropic_api_key')
        
        if api_key:
            self.llm = LLMProviderFactory.create_provider(provider_type=provider_type, api_key=api_key)
        else:
            # Try environment variables
            self.llm = LLMProviderFactory.create_provider(provider_type=provider_type)

        logger.info(f"Initialized LLM provider: {provider_type}")

        # Initialize validation agents (X-Z-CS Trinity)
        self.x_agent = XIntelligentAgent("x-1", self.llm, self.config)
        self.z_agent = ZGuardianAgent("z-1", self.llm, self.config)
        
        # CS Agent includes the 'Concept Scrutinizer' Engine
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
        output_dir = self.config.get('output_dir', 'output')
        self.pdf_reporter = ValidationReportGenerator(output_dir=output_dir)

    async def create_app_from_idea(
        self,
        idea_description: str,
        app_name: Optional[str] = None,
        category: Optional[str] = None,
        output_dir: str = "output",
        skip_generation: bool = False
    ) -> Tuple[Optional[Any], Optional[GenerationHistory], Optional[str]]:
        """
        Complete flow: Idea -> Socratic Validation -> PDF Report -> App Generation
        
        Args:
            idea_description: The startup/app idea to validate and build
            app_name: Optional custom app name (auto-generated if not provided)
            category: Optional category (auto-detected if not provided)
            output_dir: Directory for output files
            skip_generation: If True, only run validation (no code generation)
            
        Returns:
            Tuple of (generated_app, generation_history, pdf_path)
        """
        logger.info(f"Starting app generation from idea: {idea_description[:100]}...")

        ConsoleOutput.header("VerifiMind™ PEAS - Genesis Ecosystem v2.0")
        print(f"\nYour Idea: {idea_description}\n")

        # --- PHASE 1: GENESIS VALIDATION (X-Z-CS TRINITY) ---
        ConsoleOutput.header("PHASE 1: GENESIS VALIDATION (The Trinity)")
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
        ConsoleOutput.bullet("X Intelligent: Analyzing Innovation & Market Strategy...")
        ConsoleOutput.bullet("Z Guardian: Validating Ethics & Compliance...")
        ConsoleOutput.bullet("CS Security: Executing Socratic Concept Scrutiny...")
        
        agent_results = await self.orchestrator.run_full_analysis(concept)

        # 2. Conflict Resolution
        decision = self.orchestrator.resolve_conflicts(agent_results)
        self._print_agent_results(agent_results, decision)

        # 3. STOP if Rejected
        if decision['decision'] == 'reject':
            logger.warning(f"Concept rejected: {decision['reason']}")
            ConsoleOutput.error("CONCEPT REJECTED by Trinity Protocol")
            print(f"Reason: {decision['reason']}")
            return None, None, None

        # --- PHASE 1.5: GENERATE VALIDATION REPORT ---
        ConsoleOutput.subheader("Generating Genesis Validation Report...")
        
        # Build app spec for the report header
        app_spec = await self._build_app_spec(
            idea_description, 
            app_name, 
            category, 
            agent_results
        )
        
        # Extract deep Socratic data from CS agent response (FIX: handle dict properly)
        socratic_data = self._extract_socratic_data(agent_results.get('CS'))
        
        # Generate PDF with error handling (FIX: don't kill pipeline on failure)
        pdf_path = await self._generate_pdf_safe(app_spec, agent_results, socratic_data)
        
        if pdf_path:
            ConsoleOutput.success(f"REPORT GENERATED: {pdf_path}")
            ConsoleOutput.bullet("Includes: Socratic Challenges, Strategic Roadmap, IP Proof")
        else:
            ConsoleOutput.warning("Report generation failed (continuing without report)")

        # Check if we should skip code generation
        if skip_generation:
            ConsoleOutput.info("Skipping code generation (validation only mode)")
            return None, None, pdf_path

        # --- PHASE 2: APPLICATION SPECIFICATION ---
        ConsoleOutput.header("PHASE 2: BUILDING APPLICATION SPECIFICATION")
        
        logger.info(f"App specification complete: {app_spec.app_name}")
        ConsoleOutput.success("Application Specification Ready")
        ConsoleOutput.bullet(f"App Name: {app_spec.app_name}")
        ConsoleOutput.bullet(f"Category: {app_spec.category}")
        ConsoleOutput.bullet(f"Core Features: {len(app_spec.core_features)}")
        ConsoleOutput.bullet(f"Compliance Level: {len(app_spec.compliance_features)} Constraints")

        # --- PHASE 3: ITERATIVE CODE GENERATION ---
        ConsoleOutput.header("PHASE 3: ITERATIVE CODE GENERATION")
        
        try:
            generated_app, history = await self.generator.generate_with_iterations(
                spec=app_spec,
                output_dir=output_dir
            )
        except Exception as e:
            logger.error(f"Code generation failed: {e}", exc_info=True)
            ConsoleOutput.error(f"Code generation failed: {e}")
            return None, None, pdf_path

        # --- PHASE 4: FINAL OUTPUT ---
        ConsoleOutput.header("GENESIS CYCLE COMPLETE!")
        
        self._print_final_output(generated_app, history, app_spec.app_name, output_dir, pdf_path)

        return generated_app, history, pdf_path

    # =========================================================================
    # Helper Methods (Previously Missing - Now Implemented)
    # =========================================================================

    async def _build_app_spec(
        self,
        idea_description: str,
        app_name: Optional[str],
        category: Optional[str],
        agent_results: Dict[str, Any]
    ) -> AppSpecification:
        """
        Build comprehensive app specification from idea and validation results.
        """
        # Auto-generate app name if not provided
        if not app_name:
            app_name = self._generate_app_name(idea_description)
        
        # Auto-detect category if not provided
        if not category:
            category = self._detect_category(idea_description)
        
        # Extract features and requirements from agent results
        core_features = self._extract_core_features(idea_description, agent_results)
        compliance_features = self._extract_compliance_features(agent_results)
        security_requirements = self._extract_security_requirements(agent_results)
        
        # Build tech stack recommendation
        tech_stack = self._recommend_tech_stack(category)
        
        return AppSpecification(
            app_id=f"app-{uuid.uuid4().hex[:12]}",
            app_name=app_name,
            description=idea_description,
            category=category,
            core_features=core_features,
            compliance_features=compliance_features,
            tech_stack=tech_stack,
            target_users=self._extract_target_users(idea_description),
            business_model="",
            security_requirements=security_requirements
        )

    def _generate_app_name(self, description: str) -> str:
        """Generate a reasonable app name from description."""
        # Extract key nouns/concepts
        words = description.lower().split()
        
        # Filter out common words
        stop_words = {'a', 'an', 'the', 'is', 'are', 'was', 'were', 'be', 'been', 
                      'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will',
                      'would', 'could', 'should', 'may', 'might', 'must', 'shall',
                      'can', 'need', 'to', 'of', 'in', 'for', 'on', 'with', 'at',
                      'by', 'from', 'up', 'about', 'into', 'through', 'during',
                      'before', 'after', 'above', 'below', 'between', 'under',
                      'again', 'further', 'then', 'once', 'that', 'this', 'these',
                      'those', 'and', 'but', 'or', 'nor', 'so', 'yet', 'both',
                      'each', 'few', 'more', 'most', 'other', 'some', 'such', 'no',
                      'not', 'only', 'own', 'same', 'than', 'too', 'very', 'just',
                      'app', 'application', 'platform', 'system', 'tool', 'service'}
        
        key_words = [w for w in words if w not in stop_words and len(w) > 3][:3]
        
        if key_words:
            # CamelCase the key words
            name = ''.join(word.capitalize() for word in key_words)
            return f"{name}App"
        else:
            # Fallback
            return f"Genesis_{datetime.now().strftime('%Y%m%d')}"

    def _detect_category(self, description: str) -> str:
        """Auto-detect category from description keywords."""
        description_lower = description.lower()
        
        scores = {}
        for category, keywords in self.CATEGORY_KEYWORDS.items():
            score = sum(1 for kw in keywords if kw in description_lower)
            if score > 0:
                scores[category] = score
        
        if scores:
            return max(scores, key=scores.get)
        return 'general'

    def _extract_core_features(
        self, 
        description: str, 
        agent_results: Dict[str, Any]
    ) -> List[str]:
        """Extract core features from description and X agent analysis."""
        features = []
        
        # Get X agent suggestions
        x_result = agent_results.get('X')
        if x_result:
            x_analysis = self._safe_get(x_result, 'analysis', '')
            # Look for feature mentions in analysis
            if 'feature' in x_analysis.lower():
                features.append("Feature-rich user interface")
        
        # Basic features based on category
        category = self._detect_category(description)
        
        category_features = {
            'health': ['HIPAA-compliant data handling', 'Secure patient records', 'Appointment scheduling'],
            'finance': ['Transaction processing', 'Account management', 'Security compliance'],
            'education': ['Course management', 'Progress tracking', 'Interactive content'],
            'ecommerce': ['Product catalog', 'Shopping cart', 'Payment processing'],
            'social': ['User profiles', 'Content feed', 'Messaging system'],
            'productivity': ['Task management', 'Collaboration tools', 'Progress tracking'],
            'ai_ml': ['Model integration', 'Data pipeline', 'Results visualization'],
        }
        
        features.extend(category_features.get(category, ['Core functionality', 'User management']))
        
        return features[:5]

    def _extract_compliance_features(self, agent_results: Dict[str, Any]) -> List[str]:
        """Extract compliance requirements from Z agent analysis."""
        compliance = []
        
        z_result = agent_results.get('Z')
        if z_result:
            z_analysis = self._safe_get(z_result, 'analysis', '')
            
            # Check for mentioned regulations
            if 'gdpr' in z_analysis.lower():
                compliance.append("GDPR compliance required")
            if 'hipaa' in z_analysis.lower():
                compliance.append("HIPAA compliance required")
            if 'ccpa' in z_analysis.lower():
                compliance.append("CCPA compliance required")
            if 'child' in z_analysis.lower() or 'coppa' in z_analysis.lower():
                compliance.append("COPPA compliance required")
            
            # Get recommendations
            recommendations = self._safe_get(z_result, 'recommendations', [])
            compliance.extend(recommendations[:3])
        
        if not compliance:
            compliance = ["Data privacy protection", "User consent management"]
        
        return compliance

    def _extract_security_requirements(self, agent_results: Dict[str, Any]) -> List[str]:
        """Extract security requirements from CS agent analysis."""
        security = []
        
        cs_result = agent_results.get('CS')
        if cs_result:
            # Handle both dict and object access (FIX applied)
            if isinstance(cs_result, dict):
                security_scan = cs_result.get('security_scan', {})
                mitigations = security_scan.get('mitigations', [])
            else:
                security_scan = getattr(cs_result, 'security_scan', {})
                mitigations = security_scan.get('mitigations', []) if isinstance(security_scan, dict) else []
            
            security.extend(mitigations[:5])
        
        if not security:
            security = [
                "Input validation and sanitization",
                "Authentication and authorization",
                "Encrypted data transmission (TLS)"
            ]
        
        return security

    def _extract_target_users(self, description: str) -> str:
        """Extract target user description from idea."""
        # Look for user-related phrases
        user_indicators = ['for', 'users', 'customers', 'people', 'professionals', 'businesses']
        
        words = description.split()
        for i, word in enumerate(words):
            if word.lower() in user_indicators and i + 1 < len(words):
                # Return the next few words as potential user description
                return ' '.join(words[i:i+5])
        
        return "General users"

    def _recommend_tech_stack(self, category: str) -> Dict[str, str]:
        """Recommend tech stack based on category."""
        base_stack = {
            'frontend': 'React + Next.js',
            'backend': 'Node.js + Express',
            'database': 'PostgreSQL',
            'auth': 'NextAuth.js',
            'hosting': 'Vercel + AWS',
        }
        
        category_additions = {
            'health': {'compliance': 'AWS HIPAA-eligible services'},
            'finance': {'security': 'PCI-DSS compliant infrastructure'},
            'ai_ml': {'ml_framework': 'Python + FastAPI', 'ml_ops': 'MLflow'},
            'iot': {'messaging': 'MQTT', 'backend': 'Go + gRPC'},
        }
        
        if category in category_additions:
            base_stack.update(category_additions[category])
        
        return base_stack

    def _extract_socratic_data(self, cs_result: Any) -> Dict[str, Any]:
        """
        Extract Socratic analysis data from CS agent result.
        Handles both dict and object formats (FIX applied).
        """
        if cs_result is None:
            return {}
        
        if isinstance(cs_result, dict):
            return cs_result.get('socratic_analysis', {})
        else:
            # Object with attribute
            return getattr(cs_result, 'socratic_analysis', {})

    async def _generate_pdf_safe(
        self,
        app_spec: AppSpecification,
        agent_results: Dict[str, Any],
        socratic_data: Dict[str, Any]
    ) -> Optional[str]:
        """
        Generate PDF report with error handling.
        Returns None if generation fails instead of raising exception.
        (FIX: don't kill pipeline on PDF failure)
        """
        try:
            pdf_path = self.pdf_reporter.generate(
                app_spec, 
                agent_results, 
                socratic_data
            )
            return pdf_path
        except Exception as e:
            logger.error(f"PDF generation failed: {e}", exc_info=True)
            return None

    def _safe_get(self, obj: Any, attr: str, default: Any = None) -> Any:
        """Safely get attribute from object or dict."""
        if obj is None:
            return default
        if isinstance(obj, dict):
            return obj.get(attr, default)
        return getattr(obj, attr, default)

    # =========================================================================
    # Output Methods
    # =========================================================================

    def _print_agent_results(
        self, 
        agent_results: Dict[str, Any], 
        decision: Dict[str, Any]
    ):
        """Print formatted agent results summary."""
        ConsoleOutput.subheader("Agent Analysis Complete")
        
        for agent_key in ['X', 'Z', 'CS']:
            result = agent_results.get(agent_key)
            if result:
                status = self._safe_get(result, 'status', 'unknown')
                analysis = self._safe_get(result, 'analysis', 'No analysis')[:100]
                
                status_icon = '✅' if status == 'success' else '⚠️' if status == 'warning' else '❌'
                print(f"{status_icon} {agent_key}: {analysis}...")
        
        print(f"\nTrinity Decision: {decision['decision'].upper()}")
        if decision.get('reason'):
            print(f"Reason: {decision['reason']}")

    def _print_final_output(
        self,
        generated_app: Any,
        history: GenerationHistory,
        app_name: str,
        output_dir: str,
        pdf_path: Optional[str]
    ):
        """Print final output information including Report."""
        ConsoleOutput.success("APPLICATION GENERATED SUCCESSFULLY!")
        
        print(f"\n📦 Deliverables:")
        ConsoleOutput.bullet(f"Codebase: {output_dir}/{app_name}/")
        if pdf_path:
            ConsoleOutput.bullet(f"Report: {pdf_path}")
        
        print(f"\n📊 Quality Metrics:")
        ConsoleOutput.bullet(f"Final Score: {history.final_score:.1f}/100")
        ConsoleOutput.bullet(f"Improvement: +{history.improvement_percentage:.1f}%")
        ConsoleOutput.bullet(f"Total Iterations: {history.total_iterations}")

        print(f"\n🚀 Next Steps:")
        if pdf_path:
            ConsoleOutput.bullet(f"Review {os.path.basename(pdf_path)} for strategic insights", indent=3)
        ConsoleOutput.bullet(f"cd {output_dir}/{app_name} && npm install", indent=3)
        ConsoleOutput.bullet("npm run dev (for development)", indent=3)
        ConsoleOutput.bullet("npm run deploy (for production)", indent=3)


# =============================================================================
# CLI Interface
# =============================================================================

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description='VerifiMind PEAS - Genesis Ecosystem: Idea to App',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python verifimind_complete.py "AI-powered pet food delivery for busy professionals"
  python verifimind_complete.py --name "PetFeeder" --category "ecommerce" "Pet food subscription service"
  python verifimind_complete.py --validate-only "Healthcare patient portal with appointment scheduling"
        """
    )
    
    parser.add_argument(
        'idea',
        type=str,
        help='The startup/app idea to validate and build'
    )
    
    parser.add_argument(
        '--name', '-n',
        type=str,
        default=None,
        help='Custom application name (auto-generated if not provided)'
    )
    
    parser.add_argument(
        '--category', '-c',
        type=str,
        default=None,
        choices=['health', 'finance', 'education', 'ecommerce', 'social', 'productivity', 'ai_ml', 'iot', 'general'],
        help='Application category (auto-detected if not provided)'
    )
    
    parser.add_argument(
        '--output', '-o',
        type=str,
        default='output',
        help='Output directory for generated files (default: output)'
    )
    
    parser.add_argument(
        '--validate-only', '-v',
        action='store_true',
        help='Run validation only, skip code generation'
    )
    
    parser.add_argument(
        '--provider', '-p',
        type=str,
        default='openai',
        choices=['openai', 'anthropic'],
        help='LLM provider to use (default: openai)'
    )
    
    parser.add_argument(
        '--max-iterations',
        type=int,
        default=3,
        help='Maximum code generation iterations (default: 3)'
    )
    
    parser.add_argument(
        '--quality-threshold',
        type=int,
        default=85,
        help='Quality score threshold for completion (default: 85)'
    )
    
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )
    
    return parser.parse_args()


async def main():
    """Main entry point."""
    args = parse_arguments()
    
    # Setup logging
    log_level = 'DEBUG' if args.verbose else 'INFO'
    setup_logging(log_level=log_level)
    
    # Build config
    config = {
        'llm_provider': args.provider,
        'max_iterations': args.max_iterations,
        'quality_threshold': args.quality_threshold,
        'output_dir': args.output,
    }
    
    # Initialize and run
    try:
        verifimind = VerifiMindComplete(config)
        
        generated_app, history, pdf_path = await verifimind.create_app_from_idea(
            idea_description=args.idea,
            app_name=args.name,
            category=args.category,
            output_dir=args.output,
            skip_generation=args.validate_only
        )
        
        if generated_app or args.validate_only:
            sys.exit(0)
        else:
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n\nOperation cancelled by user.")
        sys.exit(130)
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        ConsoleOutput.error(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
