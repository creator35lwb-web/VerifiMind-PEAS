"""
Interactive Application Generation with Blockchain Attribution
Allows users to describe their own app idea and generate it with full attribution
"""

import asyncio
import json
from pathlib import Path
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
from src.blockchain.attribution_integration import AttributionSystem


async def interactive_app_generation_with_attribution():
    """
    Interactive: User describes their own app idea and gets full attribution
    Includes blockchain recording and certificate generation
    """

    print("=" * 80)
    print("VerifiMind(TM) - Interactive Application Generator")
    print("with Blockchain Attribution")
    print("=" * 80)
    print()
    print("Welcome! Let's build your app and establish your ownership.")
    print()

    # Initialize attribution system
    attribution = AttributionSystem()

    # Step 1: Creator Registration / Login
    print("[Step 1] Creator Authentication")
    print("-" * 80)
    print()
    print("Do you have an existing VerifiMind creator account?")
    has_account = input("(y/n): ").strip().lower()
    print()

    if has_account == 'y':
        # Login existing creator
        print("Please provide your credentials:")
        email = input("Email: ").strip()

        # Load private key
        creator = attribution.registry.get_creator_by_email(email)
        if not creator:
            print(f"\n[ERROR] No creator found with email: {email}")
            print("Please register as a new creator.")
            return None

        # Find private key file
        key_file = Path(f"./data/attribution/keys/{creator.creator_id}_private.key")
        if not key_file.exists():
            print(f"\n[ERROR] Private key file not found.")
            print(f"Expected: {key_file}")
            return None

        with open(key_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            private_key = lines[-1].strip()

        # Login
        try:
            session = attribution.login_creator(creator.creator_id, private_key)
            print(f"\n[SUCCESS] Welcome back, {session.creator.name}!")
        except Exception as e:
            print(f"\n[ERROR] Login failed: {e}")
            return None
    else:
        # Register new creator
        print("Let's register you as a new creator!")
        identity, private_key = attribution.auto_register_creator_interactive()
        session = attribution.login_creator(identity.creator_id, private_key)

    print()

    # Step 2: Get user's app idea
    print("[Step 2] Tell us about your app idea")
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
        return None

    print()
    print("[Received] Your app idea:")
    print("-" * 80)
    print(user_idea)
    print()

    # Get app name
    print("[Step 3] App Name")
    print("-" * 80)
    app_name = input("Enter your app name (e.g., MyAwesomeApp): ").strip()
    if not app_name:
        app_name = "MyGeneratedApp"
        print(f"[Using default name: {app_name}]")
    print()

    # Get category
    print("[Step 4] App Category")
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
    print("[Step 5] Deployment Target")
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
            "deployment_target": deployment_target,
            "creator_id": session.creator_id
        },
        session_id=session.session_id
    )

    # Step 6: Three-agent validation
    print("[Step 6] Three-Agent Validation")
    print("-" * 80)

    # Initialize agents
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
        return None

    print()

    # Step 7: Select template
    print("[Step 7] Selecting Best Template")
    print("-" * 80)

    template = template_library.get_template('meditation_app')
    print(f"Selected template: {template.name}")
    print(f"Technology stack: {template.tech_stack}")
    print()

    # Step 8: Generate application specification
    print("[Step 8] Creating Application Specification")
    print("-" * 80)

    app_id = f"app-{app_name.lower().replace(' ', '-')}-{session.creator_id[-8:]}"

    app_spec = AppSpecification(
        app_id=app_id,
        app_name=app_name,
        description=user_idea[:200],
        category=category,
        target_users=["Users"],
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
            "interactive_mode": True,
            "creator_id": session.creator_id,
            "creator_name": session.creator.name
        }
    )

    print(f"[OK] Application specification created")
    print(f"   - Database entities: {len(app_spec.database_entities)}")
    print(f"   - API endpoints: {len(app_spec.api_endpoints)}")
    print(f"   - UI pages: {len(app_spec.ui_pages)}")
    print()

    # Step 9: Generate the application code
    print("[Step 9] Generating Application Code")
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
    print()

    # Step 10: Blockchain Attribution
    print("[Step 10] Recording Attribution on Blockchain")
    print("=" * 80)

    certificate, cert_path = attribution.attribute_app_creation(
        app_id=app_id,
        app_name=app_name,
        app_metadata={
            "description": user_idea[:200],
            "category": category,
            "deployment_target": deployment_target,
            "generator_version": "v1.0",
            "features": [f["name"] for f in app_spec.core_features]
        }
    )

    print()
    print("[Attribution Complete!]")
    print("-" * 80)
    print(f"Creator: {session.creator.name}")
    print(f"Certificate ID: {certificate.certificate_id}")
    print(f"Certificate saved to: {cert_path}")
    print()

    # Step 11: Save generated app
    print("[Step 11] Saving Generated Files")
    print("-" * 80)
    await save_generated_app(generated_app)
    print(f"[OK] Files saved to ./output/{generated_app.app_name}/")

    # Copy certificate to app directory
    app_output_dir = Path(f"./output/{generated_app.app_name}")
    cert_output = app_output_dir / "ATTRIBUTION_CERTIFICATE.txt"
    with open(cert_path, 'r', encoding='utf-8') as src:
        with open(cert_output, 'w', encoding='utf-8') as dst:
            dst.write(src.read())
    print(f"[OK] Attribution certificate copied to app directory")
    print()

    # Summary
    print("=" * 80)
    print("[SUCCESS] Your app is ready with full attribution!")
    print("=" * 80)
    print()
    print(f"Output location: ./output/{generated_app.app_name}/")
    print(f"Attribution certificate: ./output/{generated_app.app_name}/ATTRIBUTION_CERTIFICATE.txt")
    print()
    print("What you got:")
    print(f"  1. Complete full-stack application code")
    print(f"  2. Blockchain-verified proof of creation")
    print(f"  3. Attribution certificate with QR code")
    print(f"  4. Immutable ownership record")
    print()
    print("Next steps:")
    print(f"  1. cd output/{generated_app.app_name}")
    print("  2. npm install")
    print("  3. npm run dev")
    print("  4. Review and customize the code")
    print("  5. Deploy to production")
    print()
    print("Your copyright is protected by blockchain!")
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
    print("\n[Starting] Interactive VerifiMind App Generator with Attribution...\n")
    asyncio.run(interactive_app_generation_with_attribution())
    print("Generation complete!\n")
