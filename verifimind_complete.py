"""
VerifiMind Complete System - Idea to App in One Command
Full end-to-end orchestration: X, Z, CS agents → Iterative Generation → Production App
"""

import asyncio
import sys
import argparse
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
    AppSpecification
)
from src.llm.llm_provider import LLMProviderFactory

# Get logger for this module
logger = get_logger(__name__)


class VerifiMindComplete:
    """
    Complete VerifiMind System - Orchestrates entire flow from idea to app

    Flow:
    1. User provides idea
    2. X Agent validates business viability
    3. Z Agent ensures compliance/ethics
    4. CS Agent scans for security concerns
    5. Build AppSpecification from agent insights
    6. Iterative generation creates optimal code
    7. Output production-ready application
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}

        # Initialize LLM provider
        provider_type = self.config.get('llm_provider', 'openai')
        api_key = self.config.get('openai_api_key') or self.config.get('anthropic_api_key')
        self.llm = LLMProviderFactory.create_provider(provider_type=provider_type, api_key=api_key)

        logger.info(f"Initialized LLM provider: {provider_type}")

        # Initialize validation agents
        self.x_agent = XIntelligentAgent("x-1", self.llm, self.config)
        self.z_agent = ZGuardianAgent("z-1", self.llm, self.config)
        self.cs_agent = CSSecurityAgent("cs-1", self.llm, self.config)
        self.orchestrator = AgentOrchestrator(self.x_agent, self.z_agent, self.cs_agent)

        logger.info("Initialized validation agents: X, Z, CS")

        # Initialize iterative generator
        self.generator = IterativeCodeGenerationEngine(
            config=self.config,
            llm_provider=self.llm,
            max_iterations=self.config.get('max_iterations', 3),
            quality_threshold=self.config.get('quality_threshold', 85)
        )

        logger.info(f"Initialized code generator - max_iterations: {self.config.get('max_iterations', 3)}, quality_threshold: {self.config.get('quality_threshold', 85)}")

    async def create_app_from_idea(
        self,
        idea_description: str,
        app_name: Optional[str] = None,
        category: Optional[str] = None,
        output_dir: str = "output"
    ):
        """
        Complete flow: Idea → Validation → Generation → App

        Args:
            idea_description: Natural language description of the app idea
            app_name: Optional custom app name (auto-generated if not provided)
            category: App category (auto-detected if not provided)
            output_dir: Where to save generated app

        Returns:
            (GeneratedApp, ImprovementHistory) - Final app and iteration history
        """

        logger.info(f"Starting app generation from idea: {idea_description[:100]}...")

        print("\n" + "="*70)
        print("VerifiMind™ - Complete AI Application Generation")
        print("="*70)
        print(f"\nYour Idea: {idea_description}\n")

        # PHASE 1: CONCEPT VALIDATION
        print("="*70)
        print("PHASE 1: CONCEPT VALIDATION (X, Z, CS Agents)")
        print("="*70 + "\n")
        logger.info("Phase 1: Starting concept validation")

        concept = ConceptInput(
            id=f"concept-{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}",
            description=idea_description,
            category=category,
            user_context={},
            session_id=f"session-{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}"
        )

        # Run all three agents in parallel
        logger.info("Running X, Z, CS agents in parallel...")
        print("Running X, Z, CS agents in parallel...")
        agent_results = await self.orchestrator.run_full_analysis(concept)

        # Get conflict resolution decision
        decision = self.orchestrator.resolve_conflicts(agent_results)
        logger.info(f"Conflict resolution decision: {decision['decision']}")

        self._print_agent_results(agent_results, decision)

        # Check if concept is approved
        if decision['decision'] == 'reject':
            logger.warning(f"Concept rejected: {decision['reason']}")
            print(f"\n[X] CONCEPT REJECTED")
            print(f"Reason: {decision['reason']}")
            print(f"\nPlease revise your concept and try again.")
            return None, None

        # PHASE 2: BUILD APP SPECIFICATION
        print("\n" + "="*70)
        print("PHASE 2: BUILDING APPLICATION SPECIFICATION")
        print("="*70 + "\n")
        logger.info("Phase 2: Building application specification")

        app_spec = await self._build_app_spec(
            idea_description=idea_description,
            app_name=app_name,
            category=category,
            agent_results=agent_results
        )

        logger.info(f"App specification complete: {app_spec.app_name}")
        print(f"[OK] Application Specification Complete")
        print(f"   App Name: {app_spec.app_name}")
        print(f"   Category: {app_spec.category}")
        print(f"   Features: {len(app_spec.core_features)}")
        print(f"   Database Tables: {len(app_spec.database_entities)}")
        print(f"   API Endpoints: {len(app_spec.api_endpoints)}")
        print(f"   Compliance: {', '.join(app_spec.compliance_features)}")
        print(f"   Security: {', '.join(app_spec.security_features)}")

        # PHASE 3: ITERATIVE CODE GENERATION
        print("\n" + "="*70)
        print("PHASE 3: ITERATIVE CODE GENERATION")
        print("="*70 + "\n")
        logger.info("Phase 3: Starting iterative code generation")

        generated_app, history = await self.generator.generate_with_iterations(
            spec=app_spec,
            output_dir=output_dir
        )

        # PHASE 4: FINAL OUTPUT
        print("\n" + "="*70)
        print("[OK] APPLICATION GENERATION COMPLETE!")
        print("="*70)
        logger.info("Phase 4: Application generation complete")

        self._print_final_output(generated_app, history, app_spec.app_name, output_dir)

        return generated_app, history

    async def _build_app_spec(
        self,
        idea_description: str,
        app_name: Optional[str],
        category: Optional[str],
        agent_results: Dict[str, Any]
    ) -> AppSpecification:
        """
        Builds complete AppSpecification from idea and agent results
        """
        logger.debug("Building app specification from agent results")

        # Extract insights from agents
        x_result = agent_results.get('X')
        z_result = agent_results.get('Z')
        cs_result = agent_results.get('CS')

        # Auto-generate app name if not provided
        if not app_name:
            # Simple name generation from idea
            words = idea_description.split()[:3]
            app_name = ''.join(word.capitalize() for word in words if word.isalnum())
            logger.debug(f"Auto-generated app name: {app_name}")

        # Auto-detect category if not provided
        if not category:
            category = self._detect_category(idea_description)
            logger.debug(f"Auto-detected category: {category}")

        # Build specification
        spec = AppSpecification(
            app_id=f"app-{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}",
            app_name=app_name,
            description=idea_description,
            category=category,
            target_users=self._extract_target_users(idea_description),
            core_features=self._extract_features(idea_description),

            # Agent validation results
            x_validation={
                'status': x_result.status if x_result else 'unknown',
                'risk_score': x_result.risk_score if x_result else 50,
                'recommendations': x_result.recommendations if x_result else []
            },
            z_validation={
                'status': z_result.status if z_result else 'unknown',
                'risk_score': z_result.risk_score if z_result else 50,
                'compliance_requirements': self._extract_compliance(z_result) if z_result else []
            },
            cs_validation={
                'status': cs_result.status if cs_result else 'unknown',
                'risk_score': cs_result.risk_score if cs_result else 50,
                'security_requirements': self._extract_security(cs_result) if cs_result else []
            },

            # Technical requirements (auto-generated from idea)
            database_entities=await self._generate_entities(idea_description, category),
            api_endpoints=await self._generate_endpoints(idea_description, category),
            auth_requirements={'type': 'JWT', 'roles': ['user', 'admin']},
            ui_pages=await self._generate_ui_pages(idea_description, category),

            # Compliance & Security features
            compliance_features=self._extract_compliance(z_result) if z_result else ['gdpr_compliance'],
            security_features=self._extract_security(cs_result) if cs_result else ['jwt_authentication', 'password_hashing'],

            # Deployment
            deployment_target='vercel',
            custom_domain=None,

            metadata={
                'created_at': datetime.utcnow().isoformat(),
                'generated_by': 'VerifiMind Complete System'
            }
        )

        return spec

    def _detect_category(self, idea: str) -> str:
        """Auto-detect app category from idea description"""
        idea_lower = idea.lower()

        if any(word in idea_lower for word in ['fitness', 'health', 'workout', 'exercise', 'wellness']):
            return 'Health & Fitness'
        elif any(word in idea_lower for word in ['social', 'chat', 'message', 'friend', 'community']):
            return 'Social'
        elif any(word in idea_lower for word in ['shop', 'store', 'ecommerce', 'buy', 'sell']):
            return 'E-commerce'
        elif any(word in idea_lower for word in ['learn', 'education', 'course', 'study', 'teach']):
            return 'Education'
        elif any(word in idea_lower for word in ['game', 'play', 'fun']):
            return 'Entertainment'
        elif any(word in idea_lower for word in ['todo', 'task', 'productivity', 'organize']):
            return 'Productivity'
        elif any(word in idea_lower for word in ['meditation', 'mindfulness', 'calm', 'relax']):
            return 'Health & Wellness'
        else:
            return 'General'

    def _extract_target_users(self, idea: str) -> list:
        """Extract target users from idea"""
        idea_lower = idea.lower()
        users = []

        if 'kids' in idea_lower or 'children' in idea_lower:
            users.append('Children')
        if 'parent' in idea_lower:
            users.append('Parents')
        if 'student' in idea_lower:
            users.append('Students')
        if 'teacher' in idea_lower:
            users.append('Teachers')
        if 'business' in idea_lower or 'professional' in idea_lower:
            users.append('Professionals')

        return users if users else ['General Users']

    def _extract_features(self, idea: str) -> list:
        """Extract core features from idea"""
        # Basic feature extraction
        features = [
            {
                'name': 'Core Functionality',
                'description': idea,
                'usage_instructions': 'Use the main features as described'
            }
        ]
        return features

    async def _generate_entities(self, idea: str, category: str) -> list:
        """Generate database entities based on idea and category using LLM"""
        # Use LLM to generate context-aware entities
        try:
            return await self._generate_entities_with_llm(idea, category)
        except Exception as e:
            logger.warning(f"LLM entity generation failed: {e}. Using template fallback.")
            print(f"[WARNING] LLM entity generation failed: {e}. Using template fallback.")
            # Fallback to basic user entity
            return [
                {
                    'name': 'user',
                    'description': 'User accounts',
                    'fields': [
                        {'name': 'email', 'type': 'email', 'required': True, 'unique': True},
                        {'name': 'password_hash', 'type': 'string', 'required': True},
                        {'name': 'name', 'type': 'string', 'required': True}
                    ]
                }
            ]

    async def _generate_entities_with_llm(self, idea: str, category: str) -> list:
        """Uses LLM to generate entities from idea description"""
        from src.llm.llm_provider import LLMMessage

        logger.debug(f"Generating database entities for category: {category}")

        prompt = f"""Based on this application idea, identify the main database entities needed:

Idea: {idea}
Category: {category}

For each entity, provide:
1. Entity name (singular, lowercase)
2. Description
3. Key fields with data types

Return ONLY a valid JSON array in this exact format (no markdown, no explanations):
[
  {{
    "name": "user",
    "description": "User accounts",
    "fields": [
      {{"name": "email", "type": "email", "required": true, "unique": true}},
      {{"name": "password_hash", "type": "string", "required": true}},
      {{"name": "name", "type": "string", "required": true}}
    ]
  }},
  {{
    "name": "order",
    "description": "Restaurant orders",
    "fields": [
      {{"name": "user_id", "type": "string", "required": true, "foreign_key": {{"table": "users"}}}},
      {{"name": "order_number", "type": "integer", "required": true, "unique": true}},
      {{"name": "status", "type": "string", "required": true}},
      {{"name": "total_price", "type": "float", "required": true}}
    ]
  }}
]

Valid types: string, text, integer, float, boolean, date, datetime, email, url, json
Include user entity first, then application-specific entities."""

        messages = [
            LLMMessage(role="system", content="You are a database architect. Return only valid JSON, no markdown code blocks."),
            LLMMessage(role="user", content=prompt)
        ]

        response = await self.llm.generate(messages, temperature=0.3, max_tokens=1500)
        content = response.content.strip()

        # Remove markdown code blocks if present
        if content.startswith("```"):
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:].strip()

        import json
        entities = json.loads(content)
        logger.info(f"Generated {len(entities)} database entities")
        print(f"[AI] Generated {len(entities)} entities from concept")
        return entities

    async def _generate_endpoints(self, idea: str, category: str) -> list:
        """Generate API endpoints including domain-specific ones"""
        # Base authentication endpoints
        endpoints = [
            {
                'method': 'POST',
                'path': '/api/auth/register',
                'description': 'Register new user',
                'request_body': {'email': 'string', 'password': 'string', 'name': 'string'},
                'response': {'token': 'string', 'user_id': 'string'}
            },
            {
                'method': 'POST',
                'path': '/api/auth/login',
                'description': 'User login',
                'request_body': {'email': 'string', 'password': 'string'},
                'response': {'token': 'string'}
            }
        ]

        # Generate domain-specific endpoints using LLM
        try:
            domain_endpoints = await self._generate_domain_endpoints_with_llm(idea, category)
            endpoints.extend(domain_endpoints)
            logger.info(f"Generated {len(domain_endpoints)} domain-specific API endpoints")
            print(f"[AI] Generated {len(domain_endpoints)} domain-specific API endpoints")
        except Exception as e:
            logger.warning(f"Domain endpoint generation failed: {e}. Using base endpoints only.")
            print(f"[WARNING] Domain endpoint generation failed: {e}. Using base endpoints only.")

        return endpoints

    async def _generate_domain_endpoints_with_llm(self, idea: str, category: str) -> list:
        """Uses LLM to generate domain-specific API endpoints"""
        from src.llm.llm_provider import LLMMessage

        logger.debug(f"Generating API endpoints for category: {category}")

        prompt = f"""Based on this application idea, design the RESTful API endpoints needed:

Idea: {idea}
Category: {category}

For each main entity/resource, provide standard REST endpoints:
- GET /api/[resource] - List all (with pagination)
- GET /api/[resource]/:id - Get one by ID
- POST /api/[resource] - Create new
- PUT /api/[resource]/:id - Update existing
- DELETE /api/[resource]/:id - Delete (soft delete)

Return ONLY a valid JSON array (no markdown, no explanations):
[
  {{
    "method": "GET",
    "path": "/api/orders",
    "description": "Get all orders with pagination",
    "request_body": {{}},
    "response": {{"data": "array", "total": "integer", "page": "integer"}}
  }},
  {{
    "method": "POST",
    "path": "/api/orders",
    "description": "Create new order",
    "request_body": {{"items": "array", "total_price": "float"}},
    "response": {{"id": "string", "status": "string"}}
  }}
]

Do NOT include auth endpoints (login/register). Focus on domain-specific resources."""

        messages = [
            LLMMessage(role="system", content="You are an API architect. Return only valid JSON, no markdown."),
            LLMMessage(role="user", content=prompt)
        ]

        response = await self.llm.generate(messages, temperature=0.3, max_tokens=2000)
        content = response.content.strip()

        # Remove markdown if present
        if content.startswith("```"):
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:].strip()

        import json
        endpoints = json.loads(content)
        return endpoints

    async def _generate_ui_pages(self, idea: str, category: str) -> list:
        """Generate UI pages based on domain"""
        # Base pages everyone needs
        pages = [
            {'name': 'Dashboard', 'route': '/dashboard', 'description': 'Main dashboard', 'components': []},
            {'name': 'Profile', 'route': '/profile', 'description': 'User profile page', 'components': []}
        ]

        # Generate domain-specific pages using LLM
        try:
            domain_pages = await self._generate_domain_pages_with_llm(idea, category)
            pages.extend(domain_pages)
            logger.info(f"Generated {len(domain_pages)} domain-specific UI pages")
            print(f"[AI] Generated {len(domain_pages)} domain-specific UI pages")
        except Exception as e:
            logger.warning(f"Domain page generation failed: {e}. Using base pages only.")
            print(f"[WARNING] Domain page generation failed: {e}. Using base pages only.")

        return pages

    async def _generate_domain_pages_with_llm(self, idea: str, category: str) -> list:
        """Uses LLM to generate domain-specific pages"""
        from src.llm.llm_provider import LLMMessage

        logger.debug(f"Generating UI pages for category: {category}")

        prompt = f"""Based on this application idea, identify the main UI pages/views needed:

Idea: {idea}
Category: {category}

For each main feature/entity, what pages does the user need to interact with it?

Return ONLY a valid JSON array (no markdown):
[
  {{
    "name": "Orders",
    "route": "/orders",
    "description": "View and manage all orders",
    "components": ["OrderList", "OrderCard"]
  }},
  {{
    "name": "NewOrder",
    "route": "/orders/new",
    "description": "Create a new order",
    "components": ["OrderForm", "ItemSelector"]
  }}
]

Do NOT include login, register, dashboard, or profile pages (already included)."""

        messages = [
            LLMMessage(role="system", content="You are a UX architect. Return only valid JSON."),
            LLMMessage(role="user", content=prompt)
        ]

        response = await self.llm.generate(messages, temperature=0.3, max_tokens=1500)
        content = response.content.strip()

        # Remove markdown if present
        if content.startswith("```"):
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:].strip()

        import json
        pages = json.loads(content)
        return pages

    def _extract_compliance(self, z_result) -> list:
        """Extract compliance requirements from Z agent"""
        if not z_result or not hasattr(z_result, 'analysis'):
            return ['gdpr_compliance']

        compliance = []
        analysis_str = str(z_result.analysis).lower()

        if 'gdpr' in analysis_str:
            compliance.extend(['gdpr_data_export', 'gdpr_data_deletion', 'gdpr_consent'])
        if 'coppa' in analysis_str or 'children' in analysis_str:
            compliance.extend(['age_verification', 'parental_consent', 'coppa_compliance'])
        if 'audit' in analysis_str:
            compliance.append('audit_logging')

        return compliance if compliance else ['gdpr_compliance']

    def _extract_security(self, cs_result) -> list:
        """Extract security requirements from CS agent"""
        if not cs_result or not hasattr(cs_result, 'analysis'):
            return ['jwt_authentication', 'password_hashing', 'input_validation']

        security = ['jwt_authentication', 'password_hashing', 'input_validation']

        analysis_str = str(cs_result.analysis).lower()

        if 'sql' in analysis_str:
            security.append('parameterized_queries')
        if 'xss' in analysis_str:
            security.append('xss_protection')
        if 'csrf' in analysis_str:
            security.append('csrf_protection')
        if 'rate' in analysis_str:
            security.append('rate_limiting')

        return security

    def _print_agent_results(self, results: Dict, decision: Dict):
        """Print agent validation results"""
        logger.debug("Printing agent validation results")
        print("\n[INFO] AGENT VALIDATION RESULTS:\n")

        for agent_type in ['X', 'Z', 'CS']:
            result = results.get(agent_type)
            if result:
                status_emoji = {
                    'success': '[OK]',
                    'warning': '[!]',
                    'error': '[X]',
                    'high_risk': '[!]'
                }.get(result.status, '[?]')

                print(f"{status_emoji} {agent_type} Agent ({result.agent_type}):")
                print(f"   Status: {result.status}")
                print(f"   Risk Score: {result.risk_score:.1f}/100")
                if result.recommendations:
                    print(f"   Recommendations: {len(result.recommendations)}")
                    for rec in result.recommendations[:2]:
                        print(f"      * {rec}")

        print(f"\n[DECISION] FINAL DECISION: {decision['decision'].upper()}")
        print(f"   Reason: {decision['reason']}")
        print(f"   Priority Agent: {decision.get('priority_agent', 'N/A')}")

    def _print_final_output(self, generated_app, history, app_name: str, output_dir: str):
        """Print final output information"""
        logger.info(f"Application generated successfully: {app_name}")
        print(f"\n[SUCCESS] APPLICATION GENERATED SUCCESSFULLY!")
        print(f"\n[OUTPUT] Output Location:")
        print(f"   {output_dir}/{app_name}/")

        print(f"\n[METRICS] Quality Metrics:")
        print(f"   Final Score: {history.final_score:.1f}/100")
        print(f"   Improvement: +{history.improvement_percentage:.1f}%")
        print(f"   Total Iterations: {history.total_iterations}")

        print(f"\n[FILES] Generated Files:")
        print(f"   * Backend: {len(generated_app.backend_code)} files")
        print(f"   * Frontend: {len(generated_app.frontend_code)} files")
        print(f"   * Database: schema.sql")
        print(f"   * Documentation: README.md, API.md, USER_GUIDE.md")
        print(f"   * Versions: v1.0 - v1.{history.total_iterations - 1}")

        print(f"\n[NEXT] Next Steps:")
        print(f"   1. cd {output_dir}/{app_name}")
        print(f"   2. Review ITERATION_HISTORY.md for quality improvements")
        print(f"   3. Check versions/ folder to see evolution")
        print(f"   4. Deploy using: npm install && npm run deploy")

        print(f"\n[READY] Your app is production-ready!")


def parse_arguments():
    """Parse command-line arguments"""
    parser = argparse.ArgumentParser(
        description='VerifiMind Complete System - Generate production-ready apps from ideas',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  python verifimind_complete.py --prompt-file ./prompts/my_app.txt
  python verifimind_complete.py --prompt-file ./prompts/app.txt --output-dir ./generated_apps/my_app
  python verifimind_complete.py --prompt-file ./prompts/app.txt --model claude-3-5-sonnet --verbose
  python verifimind_complete.py --interactive
        '''
    )

    parser.add_argument(
        '--prompt-file',
        type=str,
        help='Path to the input prompt file containing the app idea'
    )

    parser.add_argument(
        '--output-dir',
        type=str,
        default='./output',
        help='Directory where generated code will be saved (default: ./output)'
    )

    parser.add_argument(
        '--model',
        type=str,
        default='gpt-4',
        help='Primary LLM model to use for generation (default: gpt-4)'
    )

    parser.add_argument(
        '--max-iterations',
        type=int,
        default=3,
        help='Maximum number of iterative improvements (default: 3)'
    )

    parser.add_argument(
        '--quality-threshold',
        type=int,
        default=85,
        help='Quality threshold score 0-100 (default: 85)'
    )

    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose logging (DEBUG level)'
    )

    parser.add_argument(
        '--interactive',
        action='store_true',
        help='Run in interactive mode (prompt for idea)'
    )

    parser.add_argument(
        '--test',
        action='store_true',
        help='Run with test example (restaurant ordering system)'
    )

    return parser.parse_args()


async def main():
    """Main entry point"""
    import os
    from dotenv import load_dotenv

    # Parse command-line arguments
    args = parse_arguments()

    # Setup logging (DEBUG if verbose, otherwise INFO)
    log_level = 'DEBUG' if args.verbose else 'INFO'
    setup_logging(log_level=log_level)

    logger.info("VerifiMind Complete System starting")

    # Load environment variables
    load_dotenv()

    # Determine LLM provider from model name
    if 'claude' in args.model.lower():
        llm_provider = 'anthropic'
        api_key_env = 'ANTHROPIC_API_KEY'
    else:
        llm_provider = 'openai'
        api_key_env = 'OPENAI_API_KEY'

    # Create configuration
    config = {
        'max_iterations': args.max_iterations,
        'quality_threshold': args.quality_threshold,
        'llm_provider': os.getenv('LLM_PROVIDER', llm_provider),
        'openai_api_key': os.getenv('OPENAI_API_KEY'),
        'anthropic_api_key': os.getenv('ANTHROPIC_API_KEY'),
        'model': args.model
    }

    # Verify API key is set
    if not config.get('openai_api_key') and not config.get('anthropic_api_key'):
        logger.error(f"{api_key_env} environment variable not set")
        print(f"\n[ERROR] {api_key_env} environment variable is not set.")
        print(f"Please set it in your .env file or environment.")
        return

    # Initialize VerifiMind system
    verifimind = VerifiMindComplete(config=config)

    # Determine app idea source
    if args.test:
        idea = "create a restaurant order numbering system. The orders is count by number and selected items by clients. Customization order given a list of selection add-on sub-items."
        logger.info("Running in test mode with restaurant example")
        print(f"\n[TEST MODE] Using restaurant ordering system concept\n")
    elif args.prompt_file:
        # Read idea from file
        prompt_path = Path(args.prompt_file)
        if not prompt_path.exists():
            logger.error(f"Prompt file not found: {args.prompt_file}")
            print(f"\n[ERROR] Prompt file not found: {args.prompt_file}")
            return

        idea = prompt_path.read_text(encoding='utf-8').strip()
        logger.info(f"Read prompt from file: {args.prompt_file}")
        print(f"\n[INFO] Using idea from: {args.prompt_file}\n")
    elif args.interactive or not args.prompt_file:
        # Interactive mode - prompt user
        logger.info("Running in interactive mode")
        idea = input("\n[?] Describe your app idea: ").strip()

        if not idea:
            idea = "A fitness tracking app for runners to log workouts and track progress"
            logger.info(f"Using default example: {idea}")
            print(f"Using example: {idea}")
    else:
        print("\n[ERROR] No idea provided. Use --prompt-file, --interactive, or --test")
        return

    # Generate app
    logger.info(f"Starting app generation - Output directory: {args.output_dir}")
    await verifimind.create_app_from_idea(
        idea_description=idea,
        output_dir=args.output_dir
    )

    logger.info("VerifiMind Complete System finished")


if __name__ == "__main__":
    print("\n*** VerifiMind Complete System - Idea to App in Minutes ***\n")
    asyncio.run(main())
