"""
Attribution Verification Tool
Verify app creation attribution and certificates
"""

import json
import sys
from pathlib import Path
from datetime import datetime
from src.blockchain.attribution_integration import AttributionSystem


def print_section(title: str):
    """Print formatted section header"""
    print("\n" + "=" * 80)
    print(title.center(80))
    print("=" * 80)


def print_subsection(title: str):
    """Print formatted subsection header"""
    print("\n" + "-" * 80)
    print(title)
    print("-" * 80)


def verify_app_attribution(app_id: str):
    """Verify attribution for a specific app"""
    print_section("ATTRIBUTION VERIFICATION")

    attribution = AttributionSystem()

    # Get blockchain proof
    proof = attribution.blockchain.get_creation_proof(app_id)

    if not proof:
        print(f"\n[ERROR] No attribution found for app ID: {app_id}")
        return False

    print_subsection("Application Information")
    print(f"App ID: {proof['app_id']}")
    print(f"App Name: {proof['app_name']}")
    print(f"Created: {proof['created_at']}")

    print_subsection("Creator Information")
    creator_id = proof['creator_id']
    creator = attribution.registry.get_creator(creator_id)

    if creator:
        print(f"Creator ID: {creator.creator_id}")
        print(f"Name: {creator.name}")
        print(f"Email: {creator.email}")
        print(f"Registered: {datetime.fromtimestamp(creator.created_at).isoformat()}")
    else:
        print(f"Creator ID: {creator_id}")
        print("[WARNING] Creator details not found in registry")

    print_subsection("Blockchain Verification")
    print(f"Block Index: #{proof['block_index']}")
    print(f"Block Hash: {proof['block_hash']}")
    print(f"Previous Hash: {proof['previous_hash']}")
    print(f"Chain Verified: {'✓ VERIFIED' if proof['verified'] else '✗ NOT VERIFIED'}")

    print_subsection("Verification Result")
    if proof['verified']:
        print("\n✓ ATTRIBUTION VERIFIED")
        print(f"\nThis app was created by {creator.name if creator else creator_id}")
        print(f"Creation is permanently recorded on the blockchain at block #{proof['block_index']}")
        print("This attribution cannot be altered or disputed.")
    else:
        print("\n✗ VERIFICATION FAILED")
        print("The blockchain chain integrity check failed.")
        print("This attribution may have been tampered with.")

    return proof['verified']


def verify_certificate(certificate_path: str):
    """Verify an attribution certificate file"""
    print_section("CERTIFICATE VERIFICATION")

    cert_path = Path(certificate_path)
    if not cert_path.exists():
        print(f"\n[ERROR] Certificate file not found: {certificate_path}")
        return False

    # Load certificate
    try:
        with open(cert_path, 'r', encoding='utf-8') as f:
            if cert_path.suffix == '.json':
                cert_data = json.load(f)
            else:
                # Text certificate
                print("\n[INFO] Text certificate format")
                print("Attempting to extract data from text certificate...")

                content = f.read()
                print(content)

                # Basic validation
                if "VERIFIMIND" in content and "ATTRIBUTION CERTIFICATE" in content:
                    print("\n✓ Certificate format valid")
                    return True
                else:
                    print("\n✗ Invalid certificate format")
                    return False

        print_subsection("Certificate Data")
        print(f"Certificate ID: {cert_data.get('certificate_id')}")
        print(f"Issued: {cert_data.get('issued_at')}")

        print_subsection("Application")
        app = cert_data.get('application', {})
        print(f"App ID: {app.get('app_id')}")
        print(f"App Name: {app.get('app_name')}")
        print(f"Category: {app.get('category')}")

        print_subsection("Creator")
        creator = cert_data.get('creator', {})
        print(f"Creator ID: {creator.get('creator_id')}")
        print(f"Name: {creator.get('name')}")
        print(f"Email: {creator.get('email')}")

        print_subsection("Blockchain Proof")
        blockchain = cert_data.get('blockchain_proof', {})
        print(f"Block Index: #{blockchain.get('block_index')}")
        print(f"Block Hash: {blockchain.get('block_hash')}")
        print(f"Chain Verified: {blockchain.get('chain_verified')}")

        # Verify against blockchain
        print_subsection("Blockchain Cross-Verification")
        attribution = AttributionSystem()
        app_id = app.get('app_id')
        proof = attribution.blockchain.get_creation_proof(app_id)

        if proof:
            if proof['block_hash'] == blockchain.get('block_hash'):
                print("\n✓ CERTIFICATE VERIFIED")
                print("Certificate matches blockchain record")
                return True
            else:
                print("\n✗ CERTIFICATE MISMATCH")
                print("Certificate does not match blockchain record")
                return False
        else:
            print("\n[WARNING] No blockchain record found")
            print("Certificate cannot be verified against blockchain")
            return False

    except json.JSONDecodeError:
        print("\n[ERROR] Invalid JSON certificate format")
        return False
    except Exception as e:
        print(f"\n[ERROR] Failed to verify certificate: {e}")
        return False


def list_creator_apps(creator_id: str = None, email: str = None):
    """List all apps created by a specific creator"""
    print_section("CREATOR PORTFOLIO")

    attribution = AttributionSystem()

    # Get creator
    if email:
        creator = attribution.registry.get_creator_by_email(email)
        if not creator:
            print(f"\n[ERROR] No creator found with email: {email}")
            return
        creator_id = creator.creator_id
    elif creator_id:
        creator = attribution.registry.get_creator(creator_id)
        if not creator:
            print(f"\n[ERROR] No creator found with ID: {creator_id}")
            return
    else:
        print("\n[ERROR] Must provide either creator_id or email")
        return

    print_subsection("Creator Information")
    print(f"Creator ID: {creator.creator_id}")
    print(f"Name: {creator.name}")
    print(f"Email: {creator.email}")
    print(f"Registered: {datetime.fromtimestamp(creator.created_at).isoformat()}")

    # Get apps
    apps = attribution.get_creator_apps(creator_id)

    print_subsection(f"Created Applications ({len(apps)})")

    if not apps:
        print("\n[INFO] No apps created yet")
        return

    for i, app in enumerate(apps, 1):
        print(f"\n{i}. {app['app_name']}")
        print(f"   App ID: {app['app_id']}")
        print(f"   Created: {app['created_at']}")
        print(f"   Block: #{app['block_index']}")
        print(f"   Hash: {app['block_hash'][:32]}...")


def verify_ownership(app_id: str, creator_id: str = None, email: str = None):
    """Verify that a creator owns an app"""
    print_section("OWNERSHIP VERIFICATION")

    attribution = AttributionSystem()

    # Get creator
    if email:
        creator = attribution.registry.get_creator_by_email(email)
        if not creator:
            print(f"\n[ERROR] No creator found with email: {email}")
            return False
        creator_id = creator.creator_id
    elif not creator_id:
        print("\n[ERROR] Must provide either creator_id or email")
        return False

    # Verify ownership
    is_owner = attribution.verify_app_ownership(app_id, creator_id)

    print(f"App ID: {app_id}")
    print(f"Creator ID: {creator_id}")
    print()

    if is_owner:
        print("✓ OWNERSHIP VERIFIED")
        print(f"Creator {creator_id} is the verified owner of this app")
        return True
    else:
        print("✗ OWNERSHIP NOT VERIFIED")
        print(f"Creator {creator_id} is NOT the owner of this app")
        return False


def show_blockchain_stats():
    """Show blockchain statistics"""
    print_section("BLOCKCHAIN STATISTICS")

    attribution = AttributionSystem()
    stats = attribution.get_system_statistics()

    print_subsection("Blockchain")
    blockchain = stats['blockchain']
    print(f"Total Blocks: {blockchain['total_blocks']}")
    print(f"Total Creators: {blockchain['total_creators']}")
    print(f"Total Apps: {blockchain['total_apps']}")
    print(f"Chain Valid: {'✓ VERIFIED' if blockchain['chain_valid'] else '✗ NOT VERIFIED'}")
    print(f"Difficulty: {blockchain['difficulty']}")

    print_subsection("Registry")
    registry = stats['registry']
    print(f"Total Creators: {registry['total_creators']}")

    print_subsection("System")
    print(f"Status: {stats['system_status'].upper()}")
    print(f"Version: {stats['version']}")


def main():
    """Main CLI interface"""
    if len(sys.argv) < 2:
        print("VerifiMind Attribution Verification Tool")
        print()
        print("Usage:")
        print("  python verify_attribution.py app <app_id>")
        print("  python verify_attribution.py cert <certificate_path>")
        print("  python verify_attribution.py creator --email <email>")
        print("  python verify_attribution.py creator --id <creator_id>")
        print("  python verify_attribution.py ownership <app_id> --email <email>")
        print("  python verify_attribution.py ownership <app_id> --id <creator_id>")
        print("  python verify_attribution.py stats")
        print()
        return

    command = sys.argv[1]

    if command == "app" and len(sys.argv) >= 3:
        verify_app_attribution(sys.argv[2])

    elif command == "cert" and len(sys.argv) >= 3:
        verify_certificate(sys.argv[2])

    elif command == "creator":
        if "--email" in sys.argv:
            idx = sys.argv.index("--email")
            list_creator_apps(email=sys.argv[idx + 1])
        elif "--id" in sys.argv:
            idx = sys.argv.index("--id")
            list_creator_apps(creator_id=sys.argv[idx + 1])

    elif command == "ownership" and len(sys.argv) >= 3:
        app_id = sys.argv[2]
        if "--email" in sys.argv:
            idx = sys.argv.index("--email")
            verify_ownership(app_id, email=sys.argv[idx + 1])
        elif "--id" in sys.argv:
            idx = sys.argv.index("--id")
            verify_ownership(app_id, creator_id=sys.argv[idx + 1])

    elif command == "stats":
        show_blockchain_stats()

    else:
        print("[ERROR] Invalid command or missing arguments")
        print("Run without arguments to see usage")


if __name__ == "__main__":
    main()
