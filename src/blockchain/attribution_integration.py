"""
Attribution System Integration
Integrates blockchain attribution into the app generation workflow
"""

import os
from datetime import datetime
from typing import Dict, Any, Optional, Tuple
from pathlib import Path

from .attribution_chain import AttributionChain
from .creator_identity import CreatorRegistry, CreatorSession, CreatorIdentity
from .attribution_certificate import CertificateManager, AttributionCertificate


class AttributionSystem:
    """
    Complete attribution system integration
    Manages creator registration, blockchain recording, and certificate generation
    """

    def __init__(
        self,
        data_dir: Optional[str] = None,
        auto_register: bool = True
    ):
        """
        Initialize attribution system

        Args:
            data_dir: Directory for storing attribution data
            auto_register: Automatically register new creators
        """
        self.data_dir = Path(data_dir or "./data/attribution")
        self.data_dir.mkdir(parents=True, exist_ok=True)

        # Initialize subsystems
        self.blockchain = AttributionChain(
            storage_path=str(self.data_dir / "blockchain.json")
        )
        self.registry = CreatorRegistry(
            storage_path=str(self.data_dir / "registry.json")
        )
        self.certificates = CertificateManager(
            storage_path=str(self.data_dir / "certificates")
        )

        self.auto_register = auto_register
        self.active_session: Optional[CreatorSession] = None

    def register_creator(
        self,
        name: str,
        email: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Tuple[CreatorIdentity, str]:
        """
        Register a new creator

        Args:
            name: Creator's full name
            email: Creator's email
            metadata: Additional creator metadata

        Returns:
            Tuple of (CreatorIdentity, private_key)
        """
        print(f"[ATTRIBUTION] Registering creator: {name}")
        identity, private_key = self.registry.register_creator(name, email, metadata)

        # Save private key to secure file
        keys_dir = self.data_dir / "keys"
        keys_dir.mkdir(exist_ok=True)
        key_file = keys_dir / f"{identity.creator_id}_private.key"

        with open(key_file, 'w', encoding='utf-8') as f:
            f.write(f"# VerifiMind Creator Private Key\n")
            f.write(f"# Creator: {name}\n")
            f.write(f"# Email: {email}\n")
            f.write(f"# ID: {identity.creator_id}\n")
            f.write(f"# KEEP THIS FILE SECURE AND PRIVATE!\n\n")
            f.write(f"{private_key}\n")

        print(f"[ATTRIBUTION] Private key saved to: {key_file}")
        print(f"[ATTRIBUTION] IMPORTANT: Keep this file secure!")

        return identity, private_key

    def login_creator(
        self,
        creator_id: str,
        private_key: str
    ) -> CreatorSession:
        """
        Create a session for a creator

        Args:
            creator_id: Creator's unique ID
            private_key: Creator's private key

        Returns:
            CreatorSession instance
        """
        print(f"[ATTRIBUTION] Logging in creator: {creator_id}")
        session = CreatorSession(creator_id, private_key, self.registry)
        self.active_session = session
        print(f"[ATTRIBUTION] Session created: {session.session_id}")
        return session

    def login_creator_by_email(
        self,
        email: str,
        private_key: str
    ) -> CreatorSession:
        """Login creator using email instead of ID"""
        creator = self.registry.get_creator_by_email(email)
        if not creator:
            raise ValueError(f"No creator found with email: {email}")
        return self.login_creator(creator.creator_id, private_key)

    def auto_register_creator_interactive(self) -> Tuple[CreatorIdentity, str]:
        """
        Interactively register a new creator
        Prompts for name, email, and metadata
        """
        print("\n" + "=" * 80)
        print("CREATOR REGISTRATION")
        print("=" * 80)
        print("\nWelcome to VerifiMind! Let's register you as a creator.")
        print("This will give you attribution for all apps you create.\n")

        # Get creator info
        name = input("Full Name: ").strip()
        email = input("Email: ").strip()

        # Optional metadata
        print("\nOptional Information (press Enter to skip):")
        organization = input("Organization: ").strip()
        location = input("Location: ").strip()

        metadata = {}
        if organization:
            metadata['organization'] = organization
        if location:
            metadata['location'] = location

        # Register
        identity, private_key = self.register_creator(name, email, metadata)

        print("\n" + "=" * 80)
        print("REGISTRATION SUCCESSFUL!")
        print("=" * 80)
        print(f"\nCreator ID: {identity.creator_id}")
        print(f"Private Key has been saved securely")
        print(f"\nIMPORTANT: Keep your private key safe!")
        print(f"You'll need it to prove ownership of your creations.\n")

        return identity, private_key

    def attribute_app_creation(
        self,
        app_id: str,
        app_name: str,
        app_metadata: Dict[str, Any],
        creator_id: Optional[str] = None,
        private_key: Optional[str] = None
    ) -> Tuple[AttributionCertificate, str]:
        """
        Attribute an app creation to a creator

        Args:
            app_id: Unique app identifier
            app_name: Name of the app
            app_metadata: App metadata (description, category, features, etc.)
            creator_id: Creator ID (uses active session if not provided)
            private_key: Private key (uses active session if not provided)

        Returns:
            Tuple of (AttributionCertificate, certificate_path)
        """
        # Get or create session
        if self.active_session:
            session = self.active_session
        elif creator_id and private_key:
            session = self.login_creator(creator_id, private_key)
        else:
            raise ValueError("No active session and no credentials provided")

        print(f"\n[ATTRIBUTION] Attributing app creation to {session.creator.name}")

        # Create blockchain record
        print(f"[ATTRIBUTION] Recording on blockchain...")
        block = self.blockchain.add_attribution(
            creator_id=session.creator_id,
            app_id=app_id,
            app_name=app_name,
            metadata=app_metadata
        )

        # Sign the operation
        operation_data = {
            "type": "app_creation",
            "app_id": app_id,
            "app_name": app_name,
            "block_index": block.index,
            "block_hash": block.hash,
            "timestamp": block.timestamp
        }
        signature = session.sign_operation(operation_data)

        # Get blockchain proof
        proof = self.blockchain.get_creation_proof(app_id)

        # Generate certificate
        print(f"[ATTRIBUTION] Generating certificate...")
        certificate = self.certificates.create_certificate(
            app_data={
                "app_id": app_id,
                "app_name": app_name,
                "category": app_metadata.get('category', 'Unknown'),
                "description": app_metadata.get('description', ''),
                "created_at": datetime.fromtimestamp(block.timestamp).isoformat(),
                "generator_version": app_metadata.get('generator_version', 'v1.0')
            },
            creator_data={
                "creator_id": session.creator_id,
                "name": session.creator.name,
                "email": session.creator.email,
                "registered_at": datetime.fromtimestamp(session.creator.created_at).isoformat()
            },
            blockchain_proof=proof,
            signature=signature
        )

        cert_path = self.data_dir / "certificates" / app_id / f"{certificate.certificate_id}_certificate.txt"

        print(f"[ATTRIBUTION] ✓ Attribution complete!")
        print(f"[ATTRIBUTION] Block: #{block.index} | Hash: {block.hash[:16]}...")
        print(f"[ATTRIBUTION] Certificate: {certificate.certificate_id}")

        return certificate, str(cert_path)

    def verify_app_ownership(
        self,
        app_id: str,
        creator_id: str
    ) -> bool:
        """Verify that a creator owns an app"""
        return self.blockchain.verify_ownership(app_id, creator_id)

    def get_creator_apps(
        self,
        creator_id: str
    ) -> list:
        """Get all apps created by a specific creator"""
        attributions = self.blockchain.get_creator_attributions(creator_id)
        return [
            {
                "app_id": block.app_id,
                "app_name": block.app_name,
                "created_at": datetime.fromtimestamp(block.timestamp).isoformat(),
                "block_index": block.index,
                "block_hash": block.hash
            }
            for block in attributions
        ]

    def export_creator_portfolio(
        self,
        creator_id: str,
        output_path: str
    ):
        """Export a creator's complete portfolio"""
        import json

        creator = self.registry.get_creator(creator_id)
        if not creator:
            raise ValueError(f"Creator not found: {creator_id}")

        apps = self.get_creator_apps(creator_id)

        portfolio = {
            "creator": creator.to_public_dict(),
            "total_apps": len(apps),
            "apps": apps,
            "exported_at": datetime.now().isoformat()
        }

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(portfolio, f, indent=2)

        print(f"[ATTRIBUTION] Portfolio exported to: {output_path}")

    def get_system_statistics(self) -> Dict[str, Any]:
        """Get attribution system statistics"""
        blockchain_stats = self.blockchain.get_statistics()

        return {
            "blockchain": blockchain_stats,
            "registry": {
                "total_creators": len(self.registry),
                "total_registrations": len(self.registry)
            },
            "system_status": "operational",
            "version": "1.0"
        }


# Convenience function for quick attribution
def quick_attribute_app(
    app_id: str,
    app_name: str,
    creator_name: str,
    creator_email: str,
    app_metadata: Optional[Dict[str, Any]] = None,
    data_dir: Optional[str] = None
) -> AttributionCertificate:
    """
    Quick attribution for an app (auto-registers creator if needed)

    Args:
        app_id: Unique app identifier
        app_name: Name of the app
        creator_name: Creator's name
        creator_email: Creator's email
        app_metadata: Optional app metadata
        data_dir: Optional data directory

    Returns:
        AttributionCertificate
    """
    system = AttributionSystem(data_dir=data_dir)

    # Try to get existing creator
    creator = system.registry.get_creator_by_email(creator_email)

    if not creator:
        # Register new creator
        print(f"[ATTRIBUTION] Registering new creator: {creator_name}")
        identity, private_key = system.register_creator(
            name=creator_name,
            email=creator_email
        )
        creator_id = identity.creator_id
    else:
        # Load private key from file
        creator_id = creator.creator_id
        key_file = Path(data_dir or "./data/attribution") / "keys" / f"{creator_id}_private.key"

        if not key_file.exists():
            raise ValueError(f"Private key file not found for creator: {creator_id}")

        with open(key_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            private_key = lines[-1].strip()

    # Create attribution
    certificate, _ = system.attribute_app_creation(
        app_id=app_id,
        app_name=app_name,
        app_metadata=app_metadata or {},
        creator_id=creator_id,
        private_key=private_key
    )

    return certificate


# Example usage
if __name__ == "__main__":
    print("Testing Attribution System Integration...")
    print("=" * 80)

    # Create system
    system = AttributionSystem(data_dir="./test_attribution_data")

    # Register creator
    print("\n1. Registering creator...")
    identity, private_key = system.register_creator(
        name="Alice Johnson",
        email="alice@example.com",
        metadata={"organization": "Tech Startup"}
    )

    # Login creator
    print("\n2. Logging in creator...")
    session = system.login_creator(identity.creator_id, private_key)

    # Attribute app creation
    print("\n3. Attributing app creation...")
    certificate, cert_path = system.attribute_app_creation(
        app_id="app-test-001",
        app_name="MyAwesomeApp",
        app_metadata={
            "description": "A test application",
            "category": "Productivity",
            "generator_version": "v1.0"
        }
    )

    # Verify ownership
    print("\n4. Verifying ownership...")
    is_owner = system.verify_app_ownership("app-test-001", identity.creator_id)
    print(f"   Alice owns MyAwesomeApp: {is_owner}")

    # Get creator's apps
    print("\n5. Getting creator's apps...")
    apps = system.get_creator_apps(identity.creator_id)
    print(f"   Alice has created {len(apps)} app(s)")

    # System statistics
    print("\n6. System statistics:")
    import json
    stats = system.get_system_statistics()
    print(json.dumps(stats, indent=2))

    print("\n" + "=" * 80)
    print("Attribution system integration test complete!")
