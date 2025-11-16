"""
Creator Identity System
Manages unique creator IDs, digital signatures, and registration
"""

import hashlib
import json
import secrets
import time
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from pathlib import Path


@dataclass
class CreatorIdentity:
    """
    Represents a unique creator in the VerifiMind system
    Each creator gets a unique ID and cryptographic signature
    """
    creator_id: str
    name: str
    email: str
    public_key: str
    private_key_hash: str  # Hash of private key (never store actual private key)
    created_at: float
    metadata: Dict[str, Any]
    signature: str = ""

    def __post_init__(self):
        if not self.signature:
            self.signature = self.generate_signature()

    def generate_signature(self) -> str:
        """Generate cryptographic signature for creator"""
        data = f"{self.creator_id}{self.name}{self.email}{self.public_key}{self.created_at}"
        return hashlib.sha256(data.encode()).hexdigest()

    def verify_signature(self) -> bool:
        """Verify creator signature is valid"""
        expected = self.generate_signature()
        return self.signature == expected

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)

    def to_public_dict(self) -> Dict[str, Any]:
        """Convert to public dictionary (no private key hash)"""
        data = self.to_dict()
        data.pop('private_key_hash', None)
        return data


class CreatorRegistry:
    """
    Central registry for all creators
    Manages creator registration, verification, and lookup
    """

    def __init__(self, storage_path: Optional[str] = None):
        self.storage_path = Path(storage_path or "./data/creator_registry.json")
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        self.creators: Dict[str, CreatorIdentity] = {}
        self.email_to_id: Dict[str, str] = {}

        if self.storage_path.exists():
            self.load_registry()

    def generate_creator_id(self, name: str, email: str) -> str:
        """
        Generate unique creator ID
        Format: CREATOR_{TIMESTAMP}_{HASH}
        """
        timestamp = int(time.time() * 1000)
        data = f"{name}{email}{timestamp}{secrets.token_hex(8)}"
        hash_part = hashlib.sha256(data.encode()).hexdigest()[:12].upper()
        return f"CREATOR_{timestamp}_{hash_part}"

    def generate_key_pair(self) -> tuple[str, str]:
        """
        Generate public/private key pair
        Returns: (public_key, private_key)
        """
        # Generate cryptographically secure random keys
        private_key = secrets.token_hex(32)  # 256-bit private key
        public_key = hashlib.sha256(private_key.encode()).hexdigest()
        return public_key, private_key

    def register_creator(
        self,
        name: str,
        email: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> tuple[CreatorIdentity, str]:
        """
        Register a new creator

        Args:
            name: Creator's full name
            email: Creator's email address
            metadata: Additional metadata (organization, location, etc.)

        Returns:
            Tuple of (CreatorIdentity, private_key)
        """
        # Check if email already registered
        if email in self.email_to_id:
            raise ValueError(f"Email {email} is already registered")

        # Generate ID and keys
        creator_id = self.generate_creator_id(name, email)
        public_key, private_key = self.generate_key_pair()
        private_key_hash = hashlib.sha256(private_key.encode()).hexdigest()

        # Create identity
        identity = CreatorIdentity(
            creator_id=creator_id,
            name=name,
            email=email,
            public_key=public_key,
            private_key_hash=private_key_hash,
            created_at=time.time(),
            metadata=metadata or {}
        )

        # Store in registry
        self.creators[creator_id] = identity
        self.email_to_id[email] = creator_id

        # Save registry
        self.save_registry()

        print(f"[REGISTRY] Creator registered: {name} ({creator_id})")

        # Return identity and private key (creator must save this securely!)
        return identity, private_key

    def get_creator(self, creator_id: str) -> Optional[CreatorIdentity]:
        """Get creator by ID"""
        return self.creators.get(creator_id)

    def get_creator_by_email(self, email: str) -> Optional[CreatorIdentity]:
        """Get creator by email"""
        creator_id = self.email_to_id.get(email)
        if creator_id:
            return self.creators.get(creator_id)
        return None

    def verify_creator(self, creator_id: str, private_key: str) -> bool:
        """
        Verify a creator using their private key

        Args:
            creator_id: Creator's unique ID
            private_key: Creator's private key

        Returns:
            True if verification succeeds
        """
        creator = self.get_creator(creator_id)
        if not creator:
            return False

        # Verify private key
        private_key_hash = hashlib.sha256(private_key.encode()).hexdigest()
        if private_key_hash != creator.private_key_hash:
            return False

        # Verify signature
        return creator.verify_signature()

    def get_creator_stats(self, creator_id: str) -> Dict[str, Any]:
        """Get statistics for a creator"""
        creator = self.get_creator(creator_id)
        if not creator:
            return {}

        return {
            "creator_id": creator_id,
            "name": creator.name,
            "registered_at": datetime.fromtimestamp(creator.created_at).isoformat(),
            "verified": creator.verify_signature(),
            "metadata": creator.metadata
        }

    def list_creators(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """List all registered creators (public info only)"""
        creators = list(self.creators.values())
        if limit:
            creators = creators[:limit]
        return [c.to_public_dict() for c in creators]

    def save_registry(self):
        """Save registry to disk"""
        registry_data = {
            "version": "1.0",
            "total_creators": len(self.creators),
            "creators": [creator.to_dict() for creator in self.creators.values()],
            "saved_at": datetime.now().isoformat()
        }

        with open(self.storage_path, 'w', encoding='utf-8') as f:
            json.dump(registry_data, f, indent=2)

    def load_registry(self):
        """Load registry from disk"""
        try:
            with open(self.storage_path, 'r', encoding='utf-8') as f:
                registry_data = json.load(f)

            for creator_data in registry_data['creators']:
                creator = CreatorIdentity(**creator_data)
                self.creators[creator.creator_id] = creator
                self.email_to_id[creator.email] = creator.creator_id

            print(f"[REGISTRY] Loaded {len(self.creators)} creators")
        except Exception as e:
            print(f"[WARNING] Failed to load registry: {e}")

    def export_registry(self, output_path: str):
        """Export registry to JSON file (public data only)"""
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump({
                "version": "1.0",
                "total_creators": len(self.creators),
                "creators": self.list_creators()
            }, f, indent=2)

    def __len__(self) -> int:
        return len(self.creators)

    def __repr__(self) -> str:
        return f"<CreatorRegistry creators={len(self.creators)}>"


class CreatorSession:
    """
    Manages a creator's session
    Handles authentication and operation signing
    """

    def __init__(self, creator_id: str, private_key: str, registry: CreatorRegistry):
        self.creator_id = creator_id
        self.private_key = private_key
        self.registry = registry
        self.session_id = secrets.token_hex(16)
        self.created_at = time.time()

        # Verify creator
        if not registry.verify_creator(creator_id, private_key):
            raise ValueError("Invalid creator credentials")

        self.creator = registry.get_creator(creator_id)

    def sign_operation(self, operation_data: Dict[str, Any]) -> str:
        """
        Sign an operation (e.g., app creation) with creator's private key

        Args:
            operation_data: Data to sign

        Returns:
            Cryptographic signature
        """
        data_string = json.dumps(operation_data, sort_keys=True)
        signature_data = f"{data_string}{self.private_key}{self.session_id}"
        return hashlib.sha256(signature_data.encode()).hexdigest()

    def verify_operation_signature(
        self,
        operation_data: Dict[str, Any],
        signature: str
    ) -> bool:
        """Verify an operation signature"""
        expected_signature = self.sign_operation(operation_data)
        return signature == expected_signature

    def get_session_info(self) -> Dict[str, Any]:
        """Get session information"""
        return {
            "session_id": self.session_id,
            "creator_id": self.creator_id,
            "creator_name": self.creator.name,
            "created_at": datetime.fromtimestamp(self.created_at).isoformat(),
            "active": True
        }


# Example usage and testing
if __name__ == "__main__":
    print("Testing Creator Identity System...")
    print("=" * 80)

    # Create registry
    registry = CreatorRegistry("./test_creator_registry.json")

    # Register creators
    print("\nRegistering creators...")

    alice, alice_key = registry.register_creator(
        name="Alice Johnson",
        email="alice@example.com",
        metadata={
            "organization": "Tech Startup Inc.",
            "location": "San Francisco, CA"
        }
    )
    print(f"Alice registered: {alice.creator_id}")
    print(f"Alice's private key: {alice_key[:16]}... (keep this secure!)")

    bob, bob_key = registry.register_creator(
        name="Bob Smith",
        email="bob@example.com",
        metadata={
            "organization": "Independent Developer",
            "location": "New York, NY"
        }
    )
    print(f"Bob registered: {bob.creator_id}")

    # Verify creators
    print("\nVerifying creators...")
    alice_verified = registry.verify_creator(alice.creator_id, alice_key)
    print(f"Alice verified: {alice_verified}")

    # Create session
    print("\nCreating Alice's session...")
    session = CreatorSession(alice.creator_id, alice_key, registry)
    print(f"Session created: {session.session_id}")

    # Sign operation
    print("\nSigning app creation operation...")
    operation = {
        "type": "app_creation",
        "app_name": "MyAwesomeApp",
        "timestamp": time.time()
    }
    signature = session.sign_operation(operation)
    print(f"Operation signature: {signature[:32]}...")

    # List creators
    print("\nRegistered creators:")
    for creator in registry.list_creators():
        print(f"  - {creator['name']} ({creator['creator_id']})")

    # Statistics
    print("\nRegistry statistics:")
    print(f"Total creators: {len(registry)}")

    print("\n" + "=" * 80)
    print("Creator identity system test complete!")
