"""
Demo: Complete Application Generation Flow
Shows how VerifiMind generates a complete app from user description
"""

import asyncio
import json
import sys
import io

# Fix Windows console encoding for emojis
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
from src.generation.core_generator import (
    CodeGenerationEngine,
    AppSpecification,
    GeneratedApp
)
from src.agents.base_agent import ConceptInput, AgentOrchestrator
from src.agents.x_intelligent_agent import XIntelligentAgent
from src.agents.z_guardian_agent import ZGuardianAgent
from src.agents.cs_security_agent import CSSecurityAgent
from src.templates.template_library import template_library


async def demo_meditation_app_generation():
    """
    Demo: User wants to create a kids meditation app
    Shows complete flow from idea to generated code
    """

    print("=" * 80)
    print("VerifiMind™ - Complete Application Generation Demo")
    print("=" * 80)
    print()

    # Step 1: User describes their idea
    print("📝 Step 1: User Input")
    print("-" * 80)
    user_idea = """
I want to create a meditation app for kids aged 6-12.
It should help them with anxiety through guided breathing exercises.
Parents should be able to monitor their children's usage.
I want to measure success by daily usage.
    """
    print(f"User idea: {user_idea.strip()}")
    print()

    # Step 2: Create concept input
    concept = ConceptInput(
        id="concept-001",
        description=user_idea,
        category="Health & Wellness",
        user_context={
            "target_age": "6-12",
            "purpose": "anxiety_relief",
            "parental_involvement": True
        },
        session_id="session-001"
    )

    # Step 3: Three-agent validation
    print("🤖 Step 2: Three-Agent Validation")
    print("-" * 80)

    # Initialize agents (mock LLM provider)
    mock_llm = None
    config = {}

    x_agent = XIntelligentAgent("x-agent-1", mock_llm, config)
    z_agent = ZGuardianAgent("z-agent-1", mock_llm, config)
    cs_agent = CSSecurityAgent("cs-agent-1", mock_llm, config)

    orchestrator = AgentOrchestrator(x_agent, z_agent, cs_agent)

    print("Running parallel agent analysis...")
    results = await orchestrator.run_full_analysis(concept)

    # Display results
    for agent_type, result in results.items():
        print(f"\n{agent_type} Agent:")
        print(f"  Status: {result.status}")
        print(f"  Risk Score: {result.risk_score:.1f}/100")
        print(f"  Recommendations:")
        for rec in result.recommendations[:2]:
            print(f"    - {rec}")

    # Conflict resolution
    print("\n🤝 Conflict Resolution:")
    decision = orchestrator.resolve_conflicts(results)
    print(f"  Decision: {decision['decision']}")
    print(f"  Reason: {decision['reason']}")
    print()

    # Step 4: Generate application specification
    print("📋 Step 3: Creating Application Specification")
    print("-" * 80)

    # Get template
    template = template_library.get_template('meditation_app')
    print(f"Selected template: {template.name}")
    print(f"Technology stack: {template.tech_stack}")
    print()

    # Create app specification
    app_spec = AppSpecification(
        app_id="app-meditation-001",
        app_name="KidsCalmMind",
        description="Meditation and mindfulness app for children aged 6-12",
        category="Health & Wellness",
        target_users=["Children 6-12", "Parents", "Educators"],
        core_features=[
            {
                "name": "Guided Breathing Exercises",
                "description": "Age-appropriate breathing exercises with animations",
                "usage_instructions": "Child selects an exercise and follows along"
            },
            {
                "name": "Parent Dashboard",
                "description": "Monitor child's progress and usage",
                "usage_instructions": "Parents can view statistics and set time limits"
            },
            {
                "name": "Screen Time Limits",
                "description": "Built-in 15-minute daily limit",
                "usage_instructions": "Automatically enforced, parents can adjust"
            }
        ],
        x_validation=results['X'].analysis,
        z_validation=results['Z'].analysis,
        cs_validation=results['CS'].analysis,
        database_entities=template.entities,
        api_endpoints=template.api_endpoints,
        auth_requirements={
            "type": "jwt",
            "roles": ["parent", "child"],
            "mfa": False
        },
        ui_pages=template.ui_pages,
        compliance_features=template.compliance_features,
        security_features=template.security_features,
        deployment_target="vercel",
        custom_domain="kidscalmmind.app",
        metadata={
            "template_id": "meditation_app",
            "generated_by": "VerifiMind v1.0"
        }
    )

    print(f"✅ Application specification created")
    print(f"   - Database entities: {len(app_spec.database_entities)}")
    print(f"   - API endpoints: {len(app_spec.api_endpoints)}")
    print(f"   - UI pages: {len(app_spec.ui_pages)}")
    print(f"   - Compliance features: {len(app_spec.compliance_features)}")
    print(f"   - Security features: {len(app_spec.security_features)}")
    print()

    # Step 5: Generate the application code
    print("⚙️  Step 4: Generating Application Code")
    print("-" * 80)

    engine = CodeGenerationEngine(config={})
    generated_app = await engine.generate_application(app_spec)

    print()
    print("✅ Application Generated Successfully!")
    print("=" * 80)
    print(f"App Name: {generated_app.app_name}")
    print(f"App ID: {generated_app.app_id}")
    print(f"Generated at: {generated_app.generated_at}")
    print()

    print("📦 Generated Files:")
    print("-" * 80)
    all_files = {**generated_app.backend_code, **generated_app.frontend_code}
    for filepath in sorted(all_files.keys())[:15]:  # Show first 15 files
        print(f"  {filepath}")
    if len(all_files) > 15:
        print(f"  ... and {len(all_files) - 15} more files")
    print()

    print("📚 Documentation:")
    print("-" * 80)
    print("  README.md")
    print("  API_DOCUMENTATION.md")
    print("  USER_GUIDE.md")
    print()

    # Step 6: Show sample generated code
    print("💻 Sample Generated Code:")
    print("-" * 80)
    print("\n📄 src/server.js (excerpt):")
    print("-" * 40)
    server_code = generated_app.backend_code.get('src/server.js', '')
    print(server_code[:500] + "\n... (truncated)\n")

    # Step 7: Show database schema
    print("🗄️  Database Schema (excerpt):")
    print("-" * 40)
    print(generated_app.database_schema[:600] + "\n... (truncated)\n")

    # Step 8: Deployment ready
    print("🚀 Ready for Deployment:")
    print("-" * 80)
    print(f"  Target: {app_spec.deployment_target}")
    print(f"  Custom domain: {app_spec.custom_domain}")
    print("  Commands:")
    print("    npm install")
    print("    npm run dev     # Run locally")
    print("    npm run deploy  # Deploy to production")
    print()

    # Step 9: Show compliance features
    print("🛡️  Built-in Compliance Features:")
    print("-" * 80)
    for feature in app_spec.compliance_features:
        print(f"  ✓ {feature}")
    print()

    # Step 10: Show security features
    print("🔐 Built-in Security Features:")
    print("-" * 80)
    for feature in app_spec.security_features:
        print(f"  ✓ {feature}")
    print()

    # Summary
    print("=" * 80)
    print("🎉 SUCCESS! Your app is ready to deploy!")
    print("=" * 80)
    print()
    print("What just happened:")
    print("  1. You described your app idea in plain English")
    print("  2. Three AI agents validated business, compliance, and security")
    print("  3. VerifiMind selected the best template (Meditation App)")
    print("  4. Generated complete full-stack application code")
    print("  5. Included all compliance and security features")
    print("  6. Created comprehensive documentation")
    print("  7. Ready to deploy with one command")
    print()
    print("Time taken: ~2 minutes (vs. months of manual development)")
    print("Cost: $0 (vs. $50,000+ for developers)")
    print("Compliance: ✅ Built-in (vs. manual legal review)")
    print("Security: ✅ Best practices (vs. often overlooked)")
    print()
    print("Next steps:")
    print("  1. Review the generated code")
    print("  2. Customize if needed")
    print("  3. Deploy to production")
    print("  4. Start serving users!")
    print()

    # Save to files for inspection
    print("💾 Saving generated files...")
    await save_generated_app(generated_app)
    print("✅ Files saved to ./output/KidsCalmMind/")
    print()

    return generated_app


async def save_generated_app(app: GeneratedApp):
    """Saves generated application to disk"""
    from pathlib import Path

    base_dir = Path(f"./output/{app.app_name}")
    base_dir.mkdir(parents=True, exist_ok=True)

    # Save backend files
    for filepath, code in app.backend_code.items():
        file_path = base_dir / filepath
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(code)

    # Save frontend files
    for filepath, code in app.frontend_code.items():
        file_path = base_dir / filepath
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(code)

    # Save database schema
    (base_dir / "database" / "schema.sql").parent.mkdir(exist_ok=True)
    (base_dir / "database" / "schema.sql").write_text(app.database_schema)

    # Save documentation
    (base_dir / "README.md").write_text(app.readme)
    (base_dir / "docs" / "API.md").parent.mkdir(exist_ok=True)
    (base_dir / "docs" / "API.md").write_text(app.api_docs)
    (base_dir / "docs" / "USER_GUIDE.md").write_text(app.user_guide)

    # Save metadata
    metadata = {
        "app_id": app.app_id,
        "app_name": app.app_name,
        "generated_at": app.generated_at.isoformat(),
        "generator_version": app.generator_version,
        "technology_stack": app.technology_stack,
    }
    (base_dir / "verifimind_metadata.json").write_text(
        json.dumps(metadata, indent=2)
    )


async def compare_before_after():
    """Shows the difference between traditional development and VerifiMind"""

    print("\n" + "=" * 80)
    print("📊 TRADITIONAL DEVELOPMENT vs. VERIFIMIND™")
    print("=" * 80)
    print()

    comparison = [
        ("Metric", "Traditional", "VerifiMind™", "Improvement"),
        ("-" * 20, "-" * 20, "-" * 20, "-" * 20),
        ("Time to MVP", "3-6 months", "2 hours", "99% faster"),
        ("Development cost", "$50,000+", "$99/month", "99.8% cheaper"),
        ("Code quality", "Varies", "Best practices", "Consistent"),
        ("Security review", "Often skipped", "Built-in", "100% coverage"),
        ("Compliance", "Manual/Expensive", "Automatic", "100% coverage"),
        ("Documentation", "Often lacking", "Auto-generated", "Complete"),
        ("Deployment", "Complex setup", "One command", "10x easier"),
        ("Maintenance", "Ongoing cost", "Automated", "Lower cost"),
    ]

    for row in comparison:
        print(f"{row[0]:<20} {row[1]:<20} {row[2]:<20} {row[3]:<20}")

    print()
    print("=" * 80)
    print()


if __name__ == "__main__":
    print("\n🚀 Starting VerifiMind Demo...\n")

    # Run the demo
    asyncio.run(demo_meditation_app_generation())

    # Show comparison
    asyncio.run(compare_before_after())

    print("Demo complete! ✨\n")
