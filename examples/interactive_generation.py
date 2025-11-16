"""
Interactive Application Generation
Allows users to describe their own app idea and generate it
"""

import asyncio
import json
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


async def interactive_app_generation():
    """
    Interactive: User describes their own app idea
    Shows complete flow from idea to generated code
    """

    print("=" * 80)
    print("VerifiMind(TM) - Interactive Application Generator")
    print("=" * 80)
    print()
    print("Welcome! Let's build your app together.")
    print()

    # Step 1: Get user's app idea
    print("[Step 1] Tell us about your app idea")
    print("-" * 80)
    print()
    print("Please describe your app idea in detail.")
    print("Include:")
    print("  - What the app does")
    print("  - Who it's for (target users)")
    print("  - Key features you want")
    print("  - Any specific requirements")
    print()
    print("Type your description below (press Enter twice when done):")
    print("-" * 80)

    # Collect multi-line user input
    lines = []
    empty_count = 0
    while True:
        try:
            line = input()
            if line.strip() == "":
                empty_count += 1
                if empty_count >= 2:
                    break
            else:
                empty_count = 0
                lines.append(line)
        except EOFError:
            break

    user_idea = "\n".join(lines)

    if not user_idea.strip():
        print("\n[ERROR] No app idea provided. Exiting.")
        return

    print()
    print("[Received] Your app idea:")
    print("-" * 80)
    print(user_idea)
    print()

    # Get app name
    print("[Step 2] App Name")
    print("-" * 80)
    app_name = input("Enter your app name (e.g., MyAwesomeApp): ").strip()
    if not app_name:
        app_name = "MyGeneratedApp"
        print(f"[Using default name: {app_name}]")
    print()

    # Get category
    print("[Step 3] App Category")
    print("-" * 80)
    print("Available categories:")
    print("  1. Health & Wellness")
    print("  2. Education")
    print("  3. E-commerce")
    print("  4. Social")
    print("  5. Productivity")
    print("  6. Entertainment")
    print("  7. Finance")
    print("  8. Other")

    category_choice = input("\nSelect category (1-8): ").strip()
    categories = {
        "1": "Health & Wellness",
        "2": "Education",
        "3": "E-commerce",
        "4": "Social",
        "5": "Productivity",
        "6": "Entertainment",
        "7": "Finance",
        "8": "Other"
    }
    category = categories.get(category_choice, "Other")
    print(f"[Selected] {category}")
    print()

    # Get deployment target
    print("[Step 4] Deployment Target")
    print("-" * 80)
    print("Where do you want to deploy?")
    print("  1. Vercel (recommended for full-stack apps)")
    print("  2. AWS")
    print("  3. Google Cloud")
    print("  4. Azure")
    print("  5. Self-hosted")

    deploy_choice = input("\nSelect deployment target (1-5): ").strip()
    deploy_targets = {
        "1": "vercel",
        "2": "aws",
        "3": "gcp",
        "4": "azure",
        "5": "self-hosted"
    }
    deployment_target = deploy_targets.get(deploy_choice, "vercel")
    print(f"[Selected] {deployment_target}")
    print()

    # Create concept input
    concept = ConceptInput(
        id=f"concept-{app_name.lower().replace(' ', '-')}",
        description=user_idea,
        category=category,
        user_context={
            "app_name": app_name,
            "deployment_target": deployment_target
        },
        session_id="interactive-session-001"
    )

    # Step 5: Three-agent validation
    print("[Step 5] Three-Agent Validation")
    print("-" * 80)

    # Initialize agents (mock LLM provider)
    mock_llm = None
    config = {}

    x_agent = XIntelligentAgent("x-agent-1", mock_llm, config)
    z_agent = ZGuardianAgent("z-agent-1", mock_llm, config)
    cs_agent = CSSecurityAgent("cs-agent-1", mock_llm, config)

    orchestrator = AgentOrchestrator(x_agent, z_agent, cs_agent)

    print("Running parallel agent analysis on your app idea...")
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
    print("\n[Conflict Resolution]")
    decision = orchestrator.resolve_conflicts(results)
    print(f"  Decision: {decision['decision']}")
    print(f"  Reason: {decision['reason']}")

    if decision['decision'] == 'REJECT':
        print("\n[ERROR] Your app idea was rejected by the validation agents.")
        print("Please review the recommendations and try again.")
        return

    print()

    # Step 6: Select template
    print("[Step 6] Selecting Best Template")
    print("-" * 80)

    # For now, use meditation_app template as default
    # In future, implement smart template selection based on app idea
    template = template_library.get_template('meditation_app')
    print(f"Selected template: {template.name}")
    print(f"Technology stack: {template.tech_stack}")
    print()

    # Step 7: Generate application specification
    print("[Step 7] Creating Application Specification")
    print("-" * 80)

    # Create app specification
    app_spec = AppSpecification(
        app_id=f"app-{app_name.lower().replace(' ', '-')}-001",
        app_name=app_name,
        description=user_idea[:200],  # First 200 chars as description
        category=category,
        target_users=["Users"],  # Can be enhanced with NLP extraction
        core_features=[
            {
                "name": "Core Feature 1",
                "description": "Primary functionality based on user idea",
                "usage_instructions": "Users interact with main features"
            }
        ],
        x_validation=results['X'].analysis,
        z_validation=results['Z'].analysis,
        cs_validation=results['CS'].analysis,
        database_entities=template.entities,
        api_endpoints=template.api_endpoints,
        auth_requirements={
            "type": "jwt",
            "roles": ["user"],
            "mfa": False
        },
        ui_pages=template.ui_pages,
        compliance_features=template.compliance_features,
        security_features=template.security_features,
        deployment_target=deployment_target,
        custom_domain=f"{app_name.lower().replace(' ', '')}.app",
        metadata={
            "template_id": template.id,
            "generated_by": "VerifiMind v1.0",
            "interactive_mode": True
        }
    )

    print(f"[OK] Application specification created")
    print(f"   - Database entities: {len(app_spec.database_entities)}")
    print(f"   - API endpoints: {len(app_spec.api_endpoints)}")
    print(f"   - UI pages: {len(app_spec.ui_pages)}")
    print(f"   - Compliance features: {len(app_spec.compliance_features)}")
    print(f"   - Security features: {len(app_spec.security_features)}")
    print()

    # Step 8: Generate the application code
    print("[Step 8] Generating Application Code")
    print("-" * 80)
    print("This may take a few moments...")
    print()

    engine = CodeGenerationEngine(config={})
    generated_app = await engine.generate_application(app_spec)

    print()
    print("[OK] Application Generated Successfully!")
    print("=" * 80)
    print(f"App Name: {generated_app.app_name}")
    print(f"App ID: {generated_app.app_id}")
    print(f"Generated at: {generated_app.generated_at}")
    print()

    print("[Generated Files]")
    print("-" * 80)
    all_files = {**generated_app.backend_code, **generated_app.frontend_code}
    for filepath in sorted(all_files.keys())[:15]:
        print(f"  {filepath}")
    if len(all_files) > 15:
        print(f"  ... and {len(all_files) - 15} more files")
    print()

    print("[Documentation]")
    print("-" * 80)
    print("  README.md")
    print("  API_DOCUMENTATION.md")
    print("  USER_GUIDE.md")
    print()

    # Step 9: Save generated app
    print("[Saving] Saving generated files...")
    await save_generated_app(generated_app)
    print(f"[OK] Files saved to ./output/{generated_app.app_name}/")
    print()

    # Summary
    print("=" * 80)
    print("[SUCCESS] Your app is ready to deploy!")
    print("=" * 80)
    print()
    print(f"Output location: ./output/{generated_app.app_name}/")
    print()
    print("Next steps:")
    print(f"  1. cd output/{generated_app.app_name}")
    print("  2. npm install")
    print("  3. npm run dev")
    print("  4. Review and customize the code")
    print("  5. Deploy to production")
    print()

    return generated_app


async def save_generated_app(app: GeneratedApp):
    """Saves generated application to disk"""
    import os
    from pathlib import Path

    base_dir = Path(f"./output/{app.app_name}")
    base_dir.mkdir(parents=True, exist_ok=True)

    # Save backend files
    for filepath, code in app.backend_code.items():
        file_path = base_dir / filepath
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(code, encoding='utf-8')

    # Save frontend files
    for filepath, code in app.frontend_code.items():
        file_path = base_dir / filepath
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(code, encoding='utf-8')

    # Save database schema
    (base_dir / "database" / "schema.sql").parent.mkdir(exist_ok=True)
    (base_dir / "database" / "schema.sql").write_text(app.database_schema, encoding='utf-8')

    # Save documentation
    (base_dir / "README.md").write_text(app.readme, encoding='utf-8')
    (base_dir / "docs" / "API.md").parent.mkdir(exist_ok=True)
    (base_dir / "docs" / "API.md").write_text(app.api_docs, encoding='utf-8')
    (base_dir / "docs" / "USER_GUIDE.md").write_text(app.user_guide, encoding='utf-8')

    # Save metadata
    metadata = {
        "app_id": app.app_id,
        "app_name": app.app_name,
        "generated_at": app.generated_at.isoformat(),
        "generator_version": app.generator_version,
        "technology_stack": app.technology_stack,
    }
    (base_dir / "verifimind_metadata.json").write_text(
        json.dumps(metadata, indent=2), encoding='utf-8'
    )


if __name__ == "__main__":
    print("\n[Starting] Interactive VerifiMind App Generator...\n")
    asyncio.run(interactive_app_generation())
    print("Generation complete!\n")
