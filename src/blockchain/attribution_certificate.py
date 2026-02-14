"""
Attribution Certificate Generator
Creates verifiable certificates of app creation and ownership
"""

import json
import qrcode
from datetime import datetime
from typing import Dict, Any, Optional
from pathlib import Path
from io import BytesIO


class AttributionCertificate:
    """
    Generates attribution certificates for created applications
    Includes blockchain proof, creator info, and verification QR code
    """

    def __init__(self, attribution_data: Dict[str, Any]):
        self.data = attribution_data
        self.certificate_id = self._generate_certificate_id()

    def _generate_certificate_id(self) -> str:
        """Generate unique certificate ID"""
        import hashlib
        data_str = json.dumps(self.data, sort_keys=True)
        return f"CERT-{hashlib.sha256(data_str.encode()).hexdigest()[:16].upper()}"

    def generate_text_certificate(self) -> str:
        """Generate text-based certificate"""
        template = """
================================================================================
                    VERIFIMIND™ ATTRIBUTION CERTIFICATE
                      Proof of Creation & Ownership
================================================================================

Certificate ID:     {certificate_id}
Issued:            {issued_at}

--------------------------------------------------------------------------------
                           APPLICATION INFORMATION
--------------------------------------------------------------------------------

App Name:          {app_name}
App ID:            {app_id}
Category:          {category}
Description:       {description}

--------------------------------------------------------------------------------
                            CREATOR INFORMATION
--------------------------------------------------------------------------------

Creator ID:        {creator_id}
Creator Name:      {creator_name}
Email:             {creator_email}
Registration:      {creator_registered}

--------------------------------------------------------------------------------
                         BLOCKCHAIN VERIFICATION
--------------------------------------------------------------------------------

Block Index:       #{block_index}
Block Hash:        {block_hash}
Previous Hash:     {previous_hash}
Timestamp:         {timestamp}
Chain Verified:    {chain_verified}

--------------------------------------------------------------------------------
                            DIGITAL SIGNATURE
--------------------------------------------------------------------------------

Signature:         {signature}

--------------------------------------------------------------------------------
                          COPYRIGHT & LICENSE
--------------------------------------------------------------------------------

This certificate provides immutable proof that {creator_name} created
"{app_name}" using the VerifiMind™ AI Application Generator.

Creation Date:     {creation_date}
Generator Version: {generator_version}

COPYRIGHT NOTICE:
The application code and design are attributed to {creator_name}.
This attribution is permanently recorded on the VerifiMind blockchain
and cannot be altered or disputed.

LICENSE:
All rights reserved by the creator. The creator retains full copyright
and ownership of the generated application code.

VERIFICATION:
This certificate can be verified at any time by checking the blockchain
record at block index #{block_index} with hash {block_hash}.

To verify online, visit: https://verifimind.verify/cert/{certificate_id}
Or scan the QR code included with this certificate.

================================================================================
              VerifiMind™ - Transform Ideas into Production Apps
                     Blockchain Attribution System v1.0
================================================================================

Generated: {generated_at}
"""

        return template.format(
            certificate_id=self.certificate_id,
            issued_at=datetime.now().strftime("%B %d, %Y at %H:%M:%S UTC"),
            app_name=self.data.get('app_name', 'Unknown'),
            app_id=self.data.get('app_id', 'Unknown'),
            category=self.data.get('category', 'Unknown'),
            description=self.data.get('description', 'No description provided')[:200],
            creator_id=self.data.get('creator_id', 'Unknown'),
            creator_name=self.data.get('creator_name', 'Unknown'),
            creator_email=self.data.get('creator_email', 'Unknown'),
            creator_registered=self.data.get('creator_registered', 'Unknown'),
            block_index=self.data.get('block_index', 0),
            block_hash=self.data.get('block_hash', 'N/A')[:64],
            previous_hash=self.data.get('previous_hash', 'N/A')[:64],
            timestamp=self.data.get('timestamp', 'Unknown'),
            chain_verified='✓ VERIFIED' if self.data.get('chain_verified') else '✗ NOT VERIFIED',
            signature=self.data.get('signature', 'N/A')[:64],
            creation_date=self.data.get('creation_date', 'Unknown'),
            generator_version=self.data.get('generator_version', 'v1.0'),
            generated_at=datetime.now().strftime("%B %d, %Y at %H:%M:%S UTC")
        )

    def generate_json_certificate(self) -> Dict[str, Any]:
        """Generate machine-readable JSON certificate"""
        return {
            "certificate_id": self.certificate_id,
            "version": "1.0",
            "issued_at": datetime.now().isoformat(),
            "certificate_type": "APP_CREATION_ATTRIBUTION",
            "application": {
                "app_id": self.data.get('app_id'),
                "app_name": self.data.get('app_name'),
                "category": self.data.get('category'),
                "description": self.data.get('description'),
                "created_at": self.data.get('creation_date')
            },
            "creator": {
                "creator_id": self.data.get('creator_id'),
                "name": self.data.get('creator_name'),
                "email": self.data.get('creator_email'),
                "registered_at": self.data.get('creator_registered')
            },
            "blockchain_proof": {
                "block_index": self.data.get('block_index'),
                "block_hash": self.data.get('block_hash'),
                "previous_hash": self.data.get('previous_hash'),
                "timestamp": self.data.get('timestamp'),
                "chain_verified": self.data.get('chain_verified', False)
            },
            "digital_signature": {
                "signature": self.data.get('signature'),
                "algorithm": "SHA-256"
            },
            "copyright": {
                "owner": self.data.get('creator_name'),
                "all_rights_reserved": True,
                "attribution_required": True
            },
            "verification": {
                "url": f"https://verifimind.verify/cert/{self.certificate_id}",
                "qr_code_available": True
            }
        }

    def generate_qr_code(self, output_path: Optional[str] = None) -> Optional[bytes]:
        """
        Generate QR code for certificate verification

        Args:
            output_path: Optional path to save QR code image

        Returns:
            QR code image bytes if no output_path, None otherwise
        """
        try:
            # Create verification URL
            verification_data = {
                "certificate_id": self.certificate_id,
                "app_id": self.data.get('app_id'),
                "block_hash": self.data.get('block_hash'),
                "verify_url": f"https://verifimind.verify/cert/{self.certificate_id}"
            }

            # Generate QR code
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_H,
                box_size=10,
                border=4,
            )
            qr.add_data(json.dumps(verification_data))
            qr.make(fit=True)

            img = qr.make_image(fill_color="black", back_color="white")

            if output_path:
                img.save(output_path)
                return None
            else:
                buffer = BytesIO()
                img.save(buffer, format='PNG')
                return buffer.getvalue()
        except ImportError:
            print("[WARNING] qrcode library not installed. QR code generation skipped.")
            return None

    def save_certificate(self, output_dir: str, include_qr: bool = True):
        """
        Save complete certificate package

        Args:
            output_dir: Directory to save certificate files
            include_qr: Whether to generate QR code
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        # Save text certificate
        text_cert_path = output_path / f"{self.certificate_id}_certificate.txt"
        with open(text_cert_path, 'w', encoding='utf-8') as f:
            f.write(self.generate_text_certificate())

        # Save JSON certificate
        json_cert_path = output_path / f"{self.certificate_id}_certificate.json"
        with open(json_cert_path, 'w', encoding='utf-8') as f:
            json.dump(self.generate_json_certificate(), f, indent=2)

        # Save QR code
        qr_path = None
        if include_qr:
            qr_path = output_path / f"{self.certificate_id}_qrcode.png"
            self.generate_qr_code(str(qr_path))

        return {
            "text_certificate": str(text_cert_path),
            "json_certificate": str(json_cert_path),
            "qr_code": str(qr_path) if include_qr else None
        }

    def verify_certificate(self, blockchain_data: Dict[str, Any]) -> bool:
        """
        Verify certificate against blockchain data

        Args:
            blockchain_data: Data from blockchain to verify against

        Returns:
            True if certificate is valid
        """
        # Check block hash
        if self.data.get('block_hash') != blockchain_data.get('block_hash'):
            return False

        # Check app ID
        if self.data.get('app_id') != blockchain_data.get('app_id'):
            return False

        # Check creator ID
        if self.data.get('creator_id') != blockchain_data.get('creator_id'):
            return False

        return True

    def __repr__(self) -> str:
        return f"<AttributionCertificate id={self.certificate_id}>"


class CertificateManager:
    """Manages attribution certificates"""

    def __init__(self, storage_path: Optional[str] = None):
        self.storage_path = Path(storage_path or "./data/certificates")
        self.storage_path.mkdir(parents=True, exist_ok=True)

    def create_certificate(
        self,
        app_data: Dict[str, Any],
        creator_data: Dict[str, Any],
        blockchain_proof: Dict[str, Any],
        signature: str
    ) -> AttributionCertificate:
        """
        Create a new attribution certificate

        Args:
            app_data: Application information
            creator_data: Creator information
            blockchain_proof: Blockchain proof data
            signature: Digital signature

        Returns:
            AttributionCertificate instance
        """
        certificate_data = {
            "app_id": app_data.get('app_id'),
            "app_name": app_data.get('app_name'),
            "category": app_data.get('category', 'Unknown'),
            "description": app_data.get('description', ''),
            "creation_date": app_data.get('created_at'),
            "generator_version": app_data.get('generator_version', 'v1.0'),
            "creator_id": creator_data.get('creator_id'),
            "creator_name": creator_data.get('name'),
            "creator_email": creator_data.get('email'),
            "creator_registered": creator_data.get('registered_at'),
            "block_index": blockchain_proof.get('block_index'),
            "block_hash": blockchain_proof.get('block_hash'),
            "previous_hash": blockchain_proof.get('previous_hash'),
            "timestamp": blockchain_proof.get('created_at'),
            "chain_verified": blockchain_proof.get('verified', False),
            "signature": signature
        }

        certificate = AttributionCertificate(certificate_data)

        # Save certificate
        app_id = app_data.get('app_id', 'unknown')
        cert_dir = self.storage_path / app_id
        certificate.save_certificate(str(cert_dir))

        print(f"[CERTIFICATE] Created: {certificate.certificate_id}")

        return certificate

    def get_certificate(self, certificate_id: str) -> Optional[Dict[str, Any]]:
        """Get certificate by ID"""
        # Search for certificate file
        for cert_file in self.storage_path.rglob(f"{certificate_id}_certificate.json"):
            with open(cert_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return None

    def verify_certificate_file(self, certificate_path: str) -> bool:
        """Verify a certificate file"""
        try:
            with open(certificate_path, 'r', encoding='utf-8') as f:
                cert_data = json.load(f)

            # Basic validation
            required_fields = ['certificate_id', 'application', 'creator', 'blockchain_proof']
            return all(field in cert_data for field in required_fields)
        except Exception:
            return False


# Example usage
if __name__ == "__main__":
    print("Testing Attribution Certificate System...")
    print("=" * 80)

    # Sample data
    app_data = {
        "app_id": "app-test-001",
        "app_name": "TestApp",
        "category": "Productivity",
        "description": "A test application",
        "created_at": datetime.now().isoformat(),
        "generator_version": "v1.0"
    }

    creator_data = {
        "creator_id": "CREATOR_12345_ABCDEF",
        "name": "John Doe",
        "email": "john@example.com",
        "registered_at": datetime.now().isoformat()
    }

    blockchain_proof = {
        "block_index": 42,
        "block_hash": "0000abc123def456...",
        "previous_hash": "0000xyz789uvw012...",
        "created_at": datetime.now().isoformat(),
        "verified": True
    }

    signature = "a1b2c3d4e5f6..."

    # Create certificate manager
    manager = CertificateManager("./test_certificates")

    # Create certificate
    print("\nCreating attribution certificate...")
    certificate = manager.create_certificate(
        app_data, creator_data, blockchain_proof, signature
    )

    # Display text certificate
    print("\n" + certificate.generate_text_certificate())

    print("\n" + "=" * 80)
    print("Certificate system test complete!")
