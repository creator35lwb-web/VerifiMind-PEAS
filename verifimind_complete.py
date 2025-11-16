"""
VerifiMind Complete System - Idea to App in One Command
Full end-to-end orchestration: X, Z, CS agents → Iterative Generation → Production App
"""

import asyncio
import sys
import logging
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

# Import logging setup FIRST
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

        # Initialize validation agents
        self.x_agent = XIntelligentAgent("x-1", self.llm, self.config)
        self.z_agent = ZGuardianAgent("z-1", self.llm, self.config)
        self.cs_agent = CSSecurityAgent("cs-1", self.llm, self.config)
        self.orchestrator = AgentOrchestrator(self.x_agent, self.z_agent, self.cs_agent)

        # Initialize iterative generator
        self.generator = IterativeCodeGenerationEngine(
            config=self.config,
            llm_provider=self.llm,
            max_iterations=self.config.get('max_iterations', 3),
            quality_threshold=self.config.get('quality_threshold', 85)
        )

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

        logger.info("="*70)
        logger.info("VerifiMind™ - Complete AI Application Generation")
        logger.info("="*70)
        logger.info(f"Your Idea: {idea_description}")

        # PHASE 1: CONCEPT VALIDATION
        logger.info("="*70)
        logger.info("PHASE 1: CONCEPT VALIDATION (X, Z, CS Agents)")
        logger.info("="*70)

        concept = ConceptInput(
            id=f"concept-{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}",
            description=idea_description,
            category=category,
            user_context={},
            session_id=f"session-{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}"
        )

        # Run all three agents in parallel
        logger.info("Running X, Z, CS agents in parallel...")
        logger.debug(f"Concept ID: {concept.id}, Session ID: {concept.session_id}")
        agent_results = await self.orchestrator.run_full_analysis(concept)

        # Get conflict resolution decision
        decision = self.orchestrator.resolve_conflicts(agent_results)

        self._print_agent_results(agent_results, decision)

        # Check if concept is approved
        if decision['decision'] == 'reject':
            logger.error("CONCEPT REJECTED")
            logger.error(f"Reason: {decision['reason']}")
            logger.info("Please revise your concept and try again.")
            return None, None

        # PHASE 2: BUILD APP SPECIFICATION
        logger.info("="*70)
        logger.info("PHASE 2: BUILDING APPLICATION SPECIFICATION")
        logger.info("="*70)

        app_spec = await self._build_app_spec(
            idea_description=idea_description,
            app_name=app_name,
            category=category,
            agent_results=agent_results
        )

        logger.info("Application Specification Complete")
        logger.info(f"  App Name: {app_spec.app_name}")
        logger.info(f"  Category: {app_spec.category}")
        logger.info(f"  Features: {len(app_spec.core_features)}")
        logger.info(f"  Database Tables: {len(app_spec.database_entities)}")
        logger.info(f"  API Endpoints: {len(app_spec.api_endpoints)}")
        logger.info(f"  Compliance: {', '.join(app_spec.compliance_features)}")
        logger.info(f"  Security: {', '.join(app_spec.security_features)}")

        # PHASE 3: ITERATIVE CODE GENERATION
        logger.info("="*70)
        logger.info("PHASE 3: ITERATIVE CODE GENERATION")
        logger.info("="*70)

        generated_app, history = await self.generator.generate_with_iterations(
            spec=app_spec,
            output_dir=output_dir
        )

        # PHASE 4: FINAL OUTPUT
        logger.info("="*70)
        logger.info("APPLICATION GENERATION COMPLETE!")
        logger.info("="*70)

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

        # Extract insights from agents
        x_result = agent_results.get('X')
        z_result = agent_results.get('Z')
        cs_result = agent_results.get('CS')

        # Auto-generate app name if not provided
        if not app_name:
            # Simple name generation from idea
            words = idea_description.split()[:3]
            app_name = ''.join(word.capitalize() for word in words if word.isalnum())

        # Auto-detect category if not provided
        if not category:
            category = self._detect_category(idea_description)

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
        logger.info(f"AI generated {len(entities)} entities from concept")
        logger.debug(f"Entities: {[e.get('name') for e in entities]}")
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
            logger.info(f"AI generated {len(domain_endpoints)} domain-specific API endpoints")
        except Exception as e:
            logger.warning(f"Domain endpoint generation failed: {e}. Using base endpoints only.")

        return endpoints

    async def _generate_domain_endpoints_with_llm(self, idea: str, category: str) -> list:
        """Uses LLM to generate domain-specific API endpoints"""
        from src.llm.llm_provider import LLMMessage

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
            logger.info(f"AI generated {len(domain_pages)} domain-specific UI pages")
        except Exception as e:
            logger.warning(f"Domain page generation failed: {e}. Using base pages only.")

        return pages

    async def _generate_domain_pages_with_llm(self, idea: str, category: str) -> list:
        """Uses LLM to generate domain-specific pages"""
        from src.llm.llm_provider import LLMMessage

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
        """Log agent validation results"""
        logger.info("AGENT VALIDATION RESULTS:")

        for agent_type in ['X', 'Z', 'CS']:
            result = results.get(agent_type)
            if result:
                log_level = logging.INFO if result.status == 'success' else (
                    logging.WARNING if result.status == 'warning' else logging.ERROR
                )

                logger.log(log_level, f"{agent_type} Agent ({result.agent_type}):")
                logger.log(log_level, f"  Status: {result.status}")
                logger.log(log_level, f"  Risk Score: {result.risk_score:.1f}/100")
                if result.recommendations:
                    logger.log(log_level, f"  Recommendations: {len(result.recommendations)}")
                    for rec in result.recommendations[:2]:
                        logger.log(log_level, f"    * {rec}")

        logger.info(f"FINAL DECISION: {decision['decision'].upper()}")
        logger.info(f"  Reason: {decision['reason']}")
        logger.info(f"  Priority Agent: {decision.get('priority_agent', 'N/A')}")

    def _print_final_output(self, generated_app, history, app_name: str, output_dir: str):
        """Log final output information"""
        logger.info("APPLICATION GENERATED SUCCESSFULLY!")
        logger.info(f"Output Location: {output_dir}/{app_name}/")

        logger.info("Quality Metrics:")
        logger.info(f"  Final Score: {history.final_score:.1f}/100")
        logger.info(f"  Improvement: +{history.improvement_percentage:.1f}%")
        logger.info(f"  Total Iterations: {history.total_iterations}")

        logger.info("Generated Files:")
        logger.info(f"  * Backend: {len(generated_app.backend_code)} files")
        logger.info(f"  * Frontend: {len(generated_app.frontend_code)} files")
        logger.info(f"  * Database: schema.sql")
        logger.info(f"  * Documentation: README.md, API.md, USER_GUIDE.md")
        logger.info(f"  * Versions: v1.0 - v1.{history.total_iterations - 1}")

        logger.info("Next Steps:")
        logger.info(f"  1. cd {output_dir}/{app_name}")
        logger.info(f"  2. Review ITERATION_HISTORY.md for quality improvements")
        logger.info(f"  3. Check versions/ folder to see evolution")
        logger.info(f"  4. Deploy using: npm install && npm run deploy")

        logger.info("Your app is production-ready!")


def parse_arguments():
    """
    Parse command-line arguments for VerifiMind PEAS.

    Returns:
        Parsed arguments namespace
    """
    parser = argparse.ArgumentParser(
        description='VerifiMind PEAS - Genesis Prompt Ecosystem for Application Synthesis',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  # Interactive mode (prompts for idea)
  python verifimind_complete.py

  # With prompt file
  python verifimind_complete.py --prompt-file ./prompts/my_app.txt

  # Full specification
  python verifimind_complete.py \\
    --prompt-file ./prompts/fitness_app.txt \\
    --output-dir ./generated_apps/fitness_tracker \\
    --model claude-3-5-sonnet-20241022 \\
    --verbose

  # Test mode (uses example restaurant ordering system)
  python verifimind_complete.py --test

  # Specify app name and category
  python verifimind_complete.py \\
    --prompt-file ./prompts/idea.txt \\
    --app-name "MyAwesomeApp" \\
    --category "Productivity"

Environment Variables:
  OPENAI_API_KEY       - OpenAI API key (required if using OpenAI)
  ANTHROPIC_API_KEY    - Anthropic API key (required if using Claude)
  LLM_PROVIDER         - Default LLM provider: 'openai' or 'anthropic'
  LOG_LEVEL            - Logging level: DEBUG, INFO, WARNING, ERROR
  LOG_FILE             - Custom log file path (default: logs/verifimind.log)
        '''
    )

    # Input source (mutually exclusive group)
    input_group = parser.add_mutually_exclusive_group()
    input_group.add_argument(
        '--prompt-file',
        type=str,
        metavar='PATH',
        help='Path to text file containing the app idea/description'
    )
    input_group.add_argument(
        '--idea',
        type=str,
        metavar='TEXT',
        help='App idea as a direct command-line string'
    )
    input_group.add_argument(
        '--test',
        action='store_true',
        help='Run in test mode with example restaurant ordering system'
    )

    # Output configuration
    parser.add_argument(
        '--output-dir',
        type=str,
        default='./output',
        metavar='PATH',
        help='Directory where generated app will be saved (default: ./output)'
    )

    # App specification
    parser.add_argument(
        '--app-name',
        type=str,
        metavar='NAME',
        help='Custom name for the generated app (auto-generated if not provided)'
    )
    parser.add_argument(
        '--category',
        type=str,
        metavar='CATEGORY',
        choices=['Health & Fitness', 'Social', 'E-commerce', 'Education',
                 'Entertainment', 'Productivity', 'Health & Wellness', 'General'],
        help='App category (auto-detected if not provided)'
    )

    # LLM configuration
    parser.add_argument(
        '--model',
        type=str,
        metavar='MODEL',
        help='LLM model to use (e.g., gpt-4, claude-3-5-sonnet-20241022). Overrides LLM_PROVIDER env var.'
    )
    parser.add_argument(
        '--provider',
        type=str,
        choices=['openai', 'anthropic'],
        metavar='PROVIDER',
        help='LLM provider: openai or anthropic (default: from LLM_PROVIDER env var or openai)'
    )

    # Generation parameters
    parser.add_argument(
        '--max-iterations',
        type=int,
        default=3,
        metavar='N',
        help='Maximum number of iterative refinement cycles (default: 3)'
    )
    parser.add_argument(
        '--quality-threshold',
        type=float,
        default=85.0,
        metavar='SCORE',
        help='Minimum quality score threshold (0-100, default: 85.0)'
    )

    # Logging and debugging
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Enable verbose (DEBUG level) logging'
    )
    parser.add_argument(
        '--log-file',
        type=str,
        metavar='PATH',
        help='Custom log file path (default: logs/verifimind.log)'
    )

    # Interactive mode flag
    parser.add_argument(
        '--interactive',
        action='store_true',
        help='Force interactive mode even if prompt-file is provided (for testing)'
    )

    return parser.parse_args()


async def main():
    """Main entry point with argument parsing"""
    import os
    from dotenv import load_dotenv

    # Load environment variables
    load_dotenv()

    # Parse command-line arguments
    args = parse_arguments()

    # Initialize logging with appropriate level
    log_level = 'DEBUG' if args.verbose else os.getenv('LOG_LEVEL', 'INFO')
    log_file = args.log_file or os.getenv('LOG_FILE', 'logs/verifimind.log')
    setup_logging(log_level=log_level, log_file=log_file)

    logger.info("=" * 70)
    logger.info("VerifiMind PEAS - Complete AI Application Generation")
    logger.info("=" * 70)
    logger.debug(f"Command-line arguments: {vars(args)}")

    # Determine LLM provider and model
    if args.model:
        # Extract provider from model name
        if 'gpt' in args.model.lower():
            llm_provider = 'openai'
            model = args.model
        elif 'claude' in args.model.lower():
            llm_provider = 'anthropic'
            model = args.model
        else:
            llm_provider = args.provider or os.getenv('LLM_PROVIDER', 'openai')
            model = args.model
    else:
        llm_provider = args.provider or os.getenv('LLM_PROVIDER', 'openai')
        model = 'gpt-4' if llm_provider == 'openai' else 'claude-3-5-sonnet-20241022'

    logger.info(f"LLM Configuration: {llm_provider} / {model}")

    # Initialize VerifiMind system
    config = {
        'max_iterations': args.max_iterations,
        'quality_threshold': args.quality_threshold,
        'llm_provider': llm_provider,
        'openai_api_key': os.getenv('OPENAI_API_KEY'),
        'anthropic_api_key': os.getenv('ANTHROPIC_API_KEY'),
        'model': model
    }

    verifimind = VerifiMindComplete(config=config)

    # Determine app idea from various sources
    idea = None
    app_name = args.app_name
    category = args.category

    if args.test:
        # Test mode
        idea = "create a restaurant order numbering system. The orders is count by number and selected items by clients. Customization order given a list of selection add-on sub-items."
        logger.info("TEST MODE: Using restaurant ordering system concept")

    elif args.prompt_file:
        # Read from file
        prompt_path = Path(args.prompt_file)
        if not prompt_path.exists():
            logger.error(f"Prompt file not found: {args.prompt_file}")
            sys.exit(1)

        logger.info(f"Reading app idea from: {args.prompt_file}")
        try:
            idea = prompt_path.read_text(encoding='utf-8').strip()
            if not idea:
                logger.error("Prompt file is empty")
                sys.exit(1)
            logger.debug(f"Loaded idea: {idea[:100]}...")
        except Exception as e:
            logger.error(f"Failed to read prompt file: {e}")
            sys.exit(1)

    elif args.idea:
        # Direct command-line string
        idea = args.idea.strip()
        logger.info("Using idea from command-line argument")

    else:
        # Interactive mode
        logger.info("Interactive mode: Please describe your app idea")
        print("\n" + "=" * 70)
        print("Welcome to VerifiMind PEAS!")
        print("=" * 70)
        print("\nDescribe your app idea in natural language.")
        print("Example: 'A fitness tracking app for runners to log workouts'\n")
        print("[?] Your app idea: ", end="", flush=True)

        idea = input().strip()

        if not idea:
            # Use default example
            idea = "A fitness tracking app for runners to log workouts and track progress"
            logger.info(f"No input provided. Using example: {idea}")
            print(f"\nUsing example idea: {idea}\n")

    # Validate idea
    if not idea or len(idea) < 10:
        logger.error("App idea is too short (minimum 10 characters)")
        sys.exit(1)

    # Generate app
    logger.info(f"Starting app generation with idea: '{idea[:80]}...'")

    try:
        generated_app, history = await verifimind.create_app_from_idea(
            idea_description=idea,
            app_name=app_name,
            category=category,
            output_dir=args.output_dir
        )

        if generated_app:
            logger.info("=" * 70)
            logger.info("SUCCESS! Application generation completed.")
            logger.info("=" * 70)
            return 0
        else:
            logger.warning("Application generation was rejected or failed.")
            return 1

    except KeyboardInterrupt:
        logger.warning("Generation interrupted by user (Ctrl+C)")
        return 130
    except Exception as e:
        logger.error(f"Application generation failed: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
