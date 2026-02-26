"""
VerifiMind Iterative Code Generation Demo
Demonstrates the RefleXion pattern - generate, reflect, improve, iterate

This demo shows how VerifiMind continuously improves generated code through
self-reflection and iteration until quality thresholds are met.
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.generation.iterative_generator import IterativeCodeGenerationEngine
from src.generation.core_generator import AppSpecification
from src.llm.llm_provider import LLMProvider
from datetime import datetime


async def main():
    """Main demo function"""

    print("""
╔═══════════════════════════════════════════════════════════════════╗
║                                                                   ║
║     VerifiMind™ - Iterative Code Generation Demo                 ║
║     RefleXion Pattern: Generate → Reflect → Improve → Iterate    ║
║                                                                   ║
╚═══════════════════════════════════════════════════════════════════╝

This demo will:
1. Generate an initial version of a kids meditation app (v1.0)
2. Reflect on code quality, security, and compliance
3. Identify improvements needed
4. Generate improved version (v1.1)
5. Continue until quality threshold is met or max iterations reached

Press Enter to start...
""")
    input()

    # Initialize LLM provider (will use mock if no API key)
    config = {
        'openai_api_key': None,  # Set to use real OpenAI
        'anthropic_api_key': None  # Set to use real Anthropic
    }
    llm_provider = LLMProvider(config)

    # Initialize iterative generator
    generator = IterativeCodeGenerationEngine(
        config=config,
        llm_provider=llm_provider,
        max_iterations=3,  # Maximum 3 iterations
        quality_threshold=85  # Target 85/100 quality score
    )

    # Create app specification for kids meditation app
    app_spec = AppSpecification(
        app_id="app-" + datetime.utcnow().strftime("%Y%m%d-%H%M%S"),
        app_name="KidsCalmMind",
        description="A meditation app for children aged 6-12 to help with anxiety through guided breathing exercises",
        category="Health & Wellness",
        target_users=["Children aged 6-12", "Parents", "Educators"],

        core_features=[
            {
                "name": "Guided Meditation",
                "description": "Age-appropriate breathing exercises and mindfulness sessions",
                "usage_instructions": "Select an exercise and follow the guided instructions"
            },
            {
                "name": "Parental Dashboard",
                "description": "Parents can monitor their child's usage and progress",
                "usage_instructions": "Log in as parent to view child's activity"
            },
            {
                "name": "Progress Tracking",
                "description": "Track meditation sessions and streak",
                "usage_instructions": "View your progress in the dashboard"
            }
        ],

        # Validation results (would come from X, Z, CS agents)
        x_validation={
            "status": "approved",
            "market_opportunity": 0.8,
            "technical_feasibility": 0.9
        },
        z_validation={
            "status": "needs_coppa_compliance",
            "compliance_requirements": ["COPPA", "GDPR", "Age Verification"]
        },
        cs_validation={
            "status": "approved",
            "security_requirements": ["Authentication", "Data Encryption"]
        },

        # Technical requirements
        database_entities=[
            {
                "name": "parent",
                "description": "Parent/guardian accounts",
                "fields": [
                    {"name": "email", "type": "email", "required": True, "unique": True},
                    {"name": "password_hash", "type": "string", "required": True},
                    {"name": "name", "type": "string", "required": True},
                    {"name": "verified", "type": "boolean", "default": "FALSE"}
                ]
            },
            {
                "name": "child",
                "description": "Child profiles",
                "fields": [
                    {"name": "name", "type": "string", "required": True},
                    {"name": "age", "type": "integer", "required": True},
                    {"name": "parent_id", "type": "string", "required": True, "foreign_key": {"table": "parents"}},
                    {"name": "daily_limit_minutes", "type": "integer", "default": "15"}
                ]
            },
            {
                "name": "meditation_session",
                "description": "Meditation session records",
                "fields": [
                    {"name": "child_id", "type": "string", "required": True, "foreign_key": {"table": "children"}},
                    {"name": "exercise_id", "type": "string", "required": True, "foreign_key": {"table": "exercises"}},
                    {"name": "duration_minutes", "type": "integer", "required": True},
                    {"name": "completed", "type": "boolean", "default": "FALSE"}
                ]
            },
            {
                "name": "exercise",
                "description": "Meditation exercises library",
                "fields": [
                    {"name": "title", "type": "string", "required": True},
                    {"name": "description", "type": "text", "required": True},
                    {"name": "duration_minutes", "type": "integer", "required": True},
                    {"name": "age_min", "type": "integer", "default": "6"},
                    {"name": "age_max", "type": "integer", "default": "12"}
                ]
            }
        ],

        api_endpoints=[
            {
                "method": "POST",
                "path": "/api/auth/parent/register",
                "description": "Register a new parent account",
                "request_body": {"email": "string", "password": "string", "name": "string"},
                "response": {"token": "string", "parent_id": "string"}
            },
            {
                "method": "POST",
                "path": "/api/auth/parent/login",
                "description": "Parent login",
                "request_body": {"email": "string", "password": "string"},
                "response": {"token": "string"}
            },
            {
                "method": "POST",
                "path": "/api/children",
                "description": "Create a child profile",
                "request_body": {"name": "string", "age": "number"},
                "response": {"child_id": "string"}
            },
            {
                "method": "GET",
                "path": "/api/children/:id",
                "description": "Get child profile",
                "response": {"child": "object"}
            },
            {
                "method": "GET",
                "path": "/api/exercises",
                "description": "Get meditation exercises",
                "response": {"exercises": "array"}
            },
            {
                "method": "POST",
                "path": "/api/sessions",
                "description": "Start a meditation session",
                "request_body": {"child_id": "string", "exercise_id": "string"},
                "response": {"session_id": "string"}
            },
            {
                "method": "PUT",
                "path": "/api/sessions/:id/complete",
                "description": "Mark session as completed",
                "response": {"session": "object"}
            }
        ],

        auth_requirements={
            "type": "JWT",
            "roles": ["parent", "child"]
        },

        ui_pages=[
            {"name": "parent_dashboard", "description": "Parent monitoring dashboard"},
            {"name": "child_meditation", "description": "Child meditation interface"},
            {"name": "exercise_library", "description": "Browse meditation exercises"}
        ],

        compliance_features=[
            "age_verification",
            "parental_consent",
            "coppa_compliance"
        ],

        security_features=[
            "jwt_authentication",
            "password_hashing",
            "input_validation"
        ],

        deployment_target="vercel",
        custom_domain=None,

        metadata={
            "created_at": datetime.utcnow().isoformat(),
            "demo_mode": True
        }
    )

    print("\n🎯 Target Application: KidsCalmMind")
    print("   Category: Health & Wellness")
    print("   Users: Children 6-12 + Parents")
    print("   Compliance: COPPA + GDPR")
    print("   Features: Guided meditation, parental controls, progress tracking\n")

    # Run iterative generation
    try:
        _generated_app, _history = await generator.generate_with_iterations(
            spec=app_spec,
            output_dir="output"
        )

        # Print version summary
        print("\n")
        generator.print_version_summary(app_spec.app_id)

        # Print next steps
        print("\n" + "="*70)
        print("✅ GENERATION COMPLETE!")
        print("="*70)
        print(f"\n📁 Output Location: output/{app_spec.app_name}/")
        print(f"\n📂 Files Generated:")
        print(f"   • versions/v1.0/ - Initial version")
        print(f"   • versions/v1.1/ - Improved version (if iterated)")
        print(f"   • versions/v1.2/ - Further improved (if iterated)")
        print(f"   • verifimind_history.json - Complete iteration history")
        print(f"   • ITERATION_HISTORY.md - Readable comparison report")
        print(f"\n🚀 Next Steps:")
        print(f"   1. Review the ITERATION_HISTORY.md for detailed comparison")
        print(f"   2. Check each version folder to see improvements")
        print(f"   3. Read REFLECTION_REPORT_vX.X.json for detailed analysis")
        print(f"   4. Deploy the final version!")
        print(f"\n{'='*70}\n")

        print(f"💡 Key Insight:")
        print(f"   This is the RefleXion pattern in action - each iteration")
        print(f"   analyzed the generated code, identified issues, and improved")
        print(f"   the next version automatically. The final code is better than")
        print(f"   what any single-pass generator could create!\n")

    except Exception as e:
        print(f"\n❌ Error during generation: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    print("\n🚀 Starting VerifiMind Iterative Generation Demo...\n")
    asyncio.run(main())
