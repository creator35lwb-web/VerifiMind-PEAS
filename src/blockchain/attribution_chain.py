"""
Attribution Blockchain - Immutable record of app creation
Tracks who created what, when, and provides proof of ownership
"""

import hashlib
import json
import time
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from pathlib import Path


@dataclass
class AttributionBlock:
    """Single block in the attribution blockchain"""
    index: int
    timestamp: float
    creator_id: str
    app_id: str
    app_name: str
    data: Dict[str, Any]
    previous_hash: str
    nonce: int = 0
    hash: str = ""

    def calculate_hash(self) -> str:
        """Calculate SHA-256 hash of block"""
        block_string = json.dumps({
            "index": self.index,
            "timestamp": self.timestamp,
            "creator_id": self.creator_id,
            "app_id": self.app_id,
            "app_name": self.app_name,
            "data": self.data,
            "previous_hash": self.previous_hash,
            "nonce": self.nonce
        }, sort_keys=True)
        return hashlib.sha256(block_string.encode()).hexdigest()

    def mine_block(self, difficulty: int = 4):
        """
        Mine block with proof-of-work
        Difficulty: number of leading zeros required
        """
        target = "0" * difficulty
        while self.hash[:difficulty] != target:
            self.nonce += 1
            self.hash = self.calculate_hash()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)


class AttributionChain:
    """
    Blockchain for tracking app creation attribution
    Provides immutable proof of creation and ownership
    """

    def __init__(self, storage_path: Optional[str] = None):
        self.chain: List[AttributionBlock] = []
        self.difficulty = 4  # Number of leading zeros for proof-of-work
        self.storage_path = Path(storage_path or "./data/attribution_chain.json")
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)

        # Load existing chain or create genesis block
        if self.storage_path.exists():
            self.load_chain()
        else:
            self.create_genesis_block()

    def create_genesis_block(self):
        """Create the first block in the chain"""
        genesis_block = AttributionBlock(
            index=0,
            timestamp=time.time(),
            creator_id="VERIFIMIND_SYSTEM",
            app_id="GENESIS",
            app_name="VerifiMind Attribution Chain",
            data={
                "message": "Genesis block - VerifiMind Attribution System initialized",
                "version": "1.0",
                "created_at": datetime.now().isoformat()
            },
            previous_hash="0"
        )
        genesis_block.hash = genesis_block.calculate_hash()
        self.chain.append(genesis_block)
        self.save_chain()

    def get_latest_block(self) -> AttributionBlock:
        """Get the most recent block"""
        return self.chain[-1]

    def add_attribution(
        self,
        creator_id: str,
        app_id: str,
        app_name: str,
        metadata: Dict[str, Any]
    ) -> AttributionBlock:
        """
        Add a new attribution record to the blockchain

        Args:
            creator_id: Unique creator identifier
            app_id: Unique application identifier
            app_name: Name of the generated application
            metadata: Additional attribution data (description, features, etc.)

        Returns:
            The created attribution block
        """
        previous_block = self.get_latest_block()

        new_block = AttributionBlock(
            index=len(self.chain),
            timestamp=time.time(),
            creator_id=creator_id,
            app_id=app_id,
            app_name=app_name,
            data={
                **metadata,
                "created_at": datetime.now().isoformat(),
                "creation_method": "VerifiMind AI Generator"
            },
            previous_hash=previous_block.hash
        )

        # Mine the block (proof of work)
        print(f"[BLOCKCHAIN] Mining attribution block for {app_name}...")
        new_block.mine_block(self.difficulty)
        print(f"[BLOCKCHAIN] Block mined! Hash: {new_block.hash[:16]}...")

        self.chain.append(new_block)
        self.save_chain()

        return new_block

    def verify_chain(self) -> bool:
        """
        Verify the integrity of the entire blockchain

        Returns:
            True if chain is valid, False otherwise
        """
        for i in range(1, len(self.chain)):
            current_block = self.chain[i]
            previous_block = self.chain[i - 1]

            # Verify hash
            if current_block.hash != current_block.calculate_hash():
                print(f"[ERROR] Block {i} has invalid hash")
                return False

            # Verify chain linkage
            if current_block.previous_hash != previous_block.hash:
                print(f"[ERROR] Block {i} has invalid previous_hash")
                return False

            # Verify proof of work
            if not current_block.hash.startswith("0" * self.difficulty):
                print(f"[ERROR] Block {i} has invalid proof of work")
                return False

        return True

    def get_creator_attributions(self, creator_id: str) -> List[AttributionBlock]:
        """Get all attributions for a specific creator"""
        return [
            block for block in self.chain
            if block.creator_id == creator_id and block.index > 0
        ]

    def get_app_attribution(self, app_id: str) -> Optional[AttributionBlock]:
        """Get attribution record for a specific app"""
        for block in reversed(self.chain):
            if block.app_id == app_id and block.index > 0:
                return block
        return None

    def verify_ownership(self, app_id: str, creator_id: str) -> bool:
        """Verify that a creator owns an app"""
        attribution = self.get_app_attribution(app_id)
        if attribution:
            return attribution.creator_id == creator_id
        return False

    def get_creation_proof(self, app_id: str) -> Optional[Dict[str, Any]]:
        """
        Get immutable proof of creation for an app

        Returns:
            Dictionary with creation proof details
        """
        attribution = self.get_app_attribution(app_id)
        if not attribution:
            return None

        return {
            "app_id": app_id,
            "app_name": attribution.app_name,
            "creator_id": attribution.creator_id,
            "created_at": datetime.fromtimestamp(attribution.timestamp).isoformat(),
            "block_index": attribution.index,
            "block_hash": attribution.hash,
            "previous_hash": attribution.previous_hash,
            "data": attribution.data,
            "verified": self.verify_chain(),
            "blockchain_version": "1.0"
        }

    def save_chain(self):
        """Save blockchain to disk"""
        chain_data = {
            "version": "1.0",
            "difficulty": self.difficulty,
            "blocks": [block.to_dict() for block in self.chain],
            "saved_at": datetime.now().isoformat()
        }

        with open(self.storage_path, 'w', encoding='utf-8') as f:
            json.dump(chain_data, f, indent=2)

    def load_chain(self):
        """Load blockchain from disk"""
        try:
            with open(self.storage_path, 'r', encoding='utf-8') as f:
                chain_data = json.load(f)

            self.difficulty = chain_data.get('difficulty', 4)
            self.chain = [
                AttributionBlock(**block_data)
                for block_data in chain_data['blocks']
            ]

            # Verify loaded chain
            if not self.verify_chain():
                raise ValueError("Loaded chain failed verification")

            print(f"[BLOCKCHAIN] Loaded chain with {len(self.chain)} blocks")
        except Exception as e:
            print(f"[WARNING] Failed to load chain: {e}")
            self.create_genesis_block()

    def export_chain(self, output_path: str):
        """Export entire blockchain to JSON file"""
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump({
                "version": "1.0",
                "difficulty": self.difficulty,
                "total_blocks": len(self.chain),
                "verified": self.verify_chain(),
                "blocks": [block.to_dict() for block in self.chain]
            }, f, indent=2)

    def get_statistics(self) -> Dict[str, Any]:
        """Get blockchain statistics"""
        creators = set()
        apps = set()

        for block in self.chain[1:]:  # Skip genesis
            creators.add(block.creator_id)
            apps.add(block.app_id)

        return {
            "total_blocks": len(self.chain),
            "total_creators": len(creators),
            "total_apps": len(apps),
            "chain_valid": self.verify_chain(),
            "difficulty": self.difficulty,
            "genesis_timestamp": datetime.fromtimestamp(self.chain[0].timestamp).isoformat(),
            "latest_timestamp": datetime.fromtimestamp(self.get_latest_block().timestamp).isoformat()
        }

    def __len__(self) -> int:
        """Return number of blocks in chain"""
        return len(self.chain)

    def __repr__(self) -> str:
        return f"<AttributionChain blocks={len(self.chain)} verified={self.verify_chain()}>"


# Example usage and testing
if __name__ == "__main__":
    print("Testing Attribution Blockchain...")
    print("=" * 80)

    # Create chain
    chain = AttributionChain("./test_attribution_chain.json")

    # Add some test attributions
    print("\nAdding test attributions...")

    creator1 = "CREATOR_001_ALICE"
    block1 = chain.add_attribution(
        creator_id=creator1,
        app_id="app-meditation-001",
        app_name="MindfulKids",
        metadata={
            "description": "Meditation app for children",
            "category": "Health & Wellness",
            "features": ["Breathing exercises", "Parent dashboard"]
        }
    )

    creator2 = "CREATOR_002_BOB"
    block2 = chain.add_attribution(
        creator_id=creator2,
        app_id="app-ecommerce-001",
        app_name="QuickShop",
        metadata={
            "description": "E-commerce platform",
            "category": "E-commerce",
            "features": ["Product catalog", "Shopping cart", "Checkout"]
        }
    )

    # Verify chain
    print("\nVerifying blockchain...")
    print(f"Chain valid: {chain.verify_chain()}")

    # Get creator attributions
    print(f"\nAttributions for {creator1}:")
    for block in chain.get_creator_attributions(creator1):
        print(f"  - {block.app_name} (Block #{block.index})")

    # Get creation proof
    print("\nCreation proof for app-meditation-001:")
    proof = chain.get_creation_proof("app-meditation-001")
    print(json.dumps(proof, indent=2))

    # Statistics
    print("\nBlockchain statistics:")
    stats = chain.get_statistics()
    print(json.dumps(stats, indent=2))

    print("\n" + "=" * 80)
    print("Attribution blockchain test complete!")
