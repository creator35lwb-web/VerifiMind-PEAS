"""Simple script to update remaining src files"""
from pathlib import Path

# Replacements
replacements = {
    "RefleXion™": "VerifiMind™",
    "RefleXion": "VerifiMind",
    "REFLEXION": "VERIFIMIND",
    "reflexion": "verifimind",
}

# Files to update
files = [
    "src/agents/base_agent.py",
    "src/agents/cs_security_agent.py",
    "src/agents/x_intelligent_agent.py",
    "src/agents/z_guardian_agent.py",
    "src/blockchain/attribution_certificate.py",
    "src/blockchain/attribution_chain.py",
    "src/blockchain/attribution_integration.py",
    "src/blockchain/creator_identity.py",
    "src/blockchain/__init__.py",
    "src/generation/core_generator.py",
    "src/generation/frontend_generator.py",
    "src/llm/llm_provider.py",
    "src/templates/template_library.py",
]

project_root = Path(__file__).parent

for file_rel in files:
    file_path = project_root / file_rel

    if not file_path.exists():
        print(f"[SKIP] {file_rel} (not found)")
        continue

    try:
        # Read
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        original = content

        # Replace
        for old, new in replacements.items():
            content = content.replace(old, new)

        # Write if changed
        if content != original:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"[OK] {file_rel}")
        else:
            print(f"[NO CHANGE] {file_rel}")

    except Exception as e:
        print(f"[ERROR] {file_rel}: {e}")

print("\nDone!")
