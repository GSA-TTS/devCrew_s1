"""
GPG Handler - Pure Python implementation for key generation and signing.

Provides RSA and ECDSA key generation, file signing with detached signatures,
signature verification, and key import/export operations using the cryptography library.

This module provides a pure Python fallback when python-gnupg is not available.
"""

import hashlib
import json
import os
from datetime import datetime, timedelta
from typing import Dict, Optional

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec, padding, rsa


class GPGHandler:
    """
    Handle GPG-style key generation, signing, and verification.

    Uses pure Python cryptography library as fallback for GPG operations.
    """

    def __init__(self, keyring_dir: Optional[str] = None):
        """
        Initialize GPG handler.

        Args:
            keyring_dir: Directory to store keys (default: temp directory)
        """
        if keyring_dir is None:
            import tempfile

            self.keyring_dir = tempfile.mkdtemp(prefix="gpg_keyring_")
        else:
            self.keyring_dir = keyring_dir
            os.makedirs(self.keyring_dir, exist_ok=True)

        self.keys: Dict[str, Dict] = {}
        self._load_keys()

    def _load_keys(self) -> None:
        """Load existing keys from keyring directory."""
        keyring_file = os.path.join(self.keyring_dir, "keyring.json")
        if os.path.exists(keyring_file):
            with open(keyring_file, "r") as f:
                self.keys = json.load(f)

    def _save_keys(self) -> None:
        """Save keys to keyring directory."""
        keyring_file = os.path.join(self.keyring_dir, "keyring.json")
        with open(keyring_file, "w") as f:
            json.dump(self.keys, f, indent=2)

    def generate_key(
        self,
        name: str,
        email: str,
        algorithm: str = "rsa",
        key_size: int = 2048,
        curve: str = "secp256r1",
        expires_days: Optional[int] = None,
    ) -> str:
        """
        Generate a new signing key.

        Args:
            name: Name associated with key
            email: Email associated with key
            algorithm: "rsa" or "ecdsa"
            key_size: Key size for RSA (2048, 3072, 4096)
            curve: EC curve for ECDSA (secp256r1, secp384r1, secp521r1)
            expires_days: Days until expiration (None for no expiration)

        Returns:
            Key ID (hex string)
        """
        # Generate private key
        if algorithm.lower() == "rsa":
            private_key = rsa.generate_private_key(
                public_exponent=65537, key_size=key_size, backend=default_backend()
            )
        elif algorithm.lower() == "ecdsa":
            curve_map = {
                "secp256r1": ec.SECP256R1(),
                "secp384r1": ec.SECP384R1(),
                "secp521r1": ec.SECP521R1(),
            }
            ec_curve = curve_map.get(curve, ec.SECP256R1())
            private_key = ec.generate_private_key(ec_curve, backend=default_backend())
        else:
            raise ValueError(f"Unsupported algorithm: {algorithm}")

        # Generate key ID from public key fingerprint
        public_key = private_key.public_key()
        public_bytes = public_key.public_bytes(
            encoding=serialization.Encoding.DER,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )
        key_id = hashlib.sha256(public_bytes).hexdigest()[:16]

        # Calculate expiration
        created = datetime.now()
        expires = None
        if expires_days is not None:
            expires = created + timedelta(days=expires_days)

        # Serialize keys
        private_pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        ).decode("utf-8")

        public_pem = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        ).decode("utf-8")

        # Store key metadata
        self.keys[key_id] = {
            "key_id": key_id,
            "name": name,
            "email": email,
            "algorithm": algorithm,
            "key_size": key_size if algorithm == "rsa" else None,
            "curve": curve if algorithm == "ecdsa" else None,
            "created": created.isoformat(),
            "expires": expires.isoformat() if expires else None,
            "private_key": private_pem,
            "public_key": public_pem,
        }

        # Save key to file
        key_file = os.path.join(self.keyring_dir, f"{key_id}.key")
        with open(key_file, "w") as f:
            json.dump(self.keys[key_id], f, indent=2)

        self._save_keys()

        return key_id

    def sign_file(self, file_path: str, key_id: str, detached: bool = True) -> str:
        """
        Sign a file with the specified key.

        Args:
            file_path: Path to file to sign
            key_id: Key ID to use for signing
            detached: Create detached signature (default: True)

        Returns:
            Path to signature file
        """
        if key_id not in self.keys:
            raise ValueError(f"Key not found: {key_id}")

        # Read file content
        with open(file_path, "rb") as f:
            data = f.read()

        # Load private key
        key_data = self.keys[key_id]
        private_key = serialization.load_pem_private_key(
            key_data["private_key"].encode("utf-8"),
            password=None,
            backend=default_backend(),
        )

        # Sign data
        if key_data["algorithm"] == "rsa":
            signature = private_key.sign(
                data,
                padding.PSS(
                    mgf=padding.MGF1(hashes.SHA256()),
                    salt_length=padding.PSS.MAX_LENGTH,
                ),
                hashes.SHA256(),
            )
        else:  # ecdsa
            signature = private_key.sign(data, ec.ECDSA(hashes.SHA256()))

        # Write signature
        sig_path = f"{file_path}.sig" if detached else file_path
        if detached:
            with open(sig_path, "wb") as f:
                f.write(signature)
        else:
            # For attached signatures, prepend signature info
            with open(sig_path, "wb") as f:
                sig_header = json.dumps(
                    {
                        "key_id": key_id,
                        "algorithm": key_data["algorithm"],
                        "timestamp": datetime.now().isoformat(),
                    }
                ).encode("utf-8")
                f.write(b"-----BEGIN SIGNATURE-----\n")
                f.write(sig_header)
                f.write(b"\n")
                f.write(signature)
                f.write(b"\n-----END SIGNATURE-----\n")
                f.write(data)

        return sig_path

    def verify_signature(
        self, file_path: str, signature_path: str, key_id: Optional[str] = None
    ) -> Dict:
        """
        Verify a file signature.

        Args:
            file_path: Path to signed file
            signature_path: Path to signature file
            key_id: Key ID to verify with (optional, auto-detect from signature)

        Returns:
            Verification result dictionary
        """
        # Read file and signature
        with open(file_path, "rb") as f:
            data = f.read()

        with open(signature_path, "rb") as f:
            signature = f.read()

        # Auto-detect key if not specified
        if key_id is None:
            # Try all keys
            for kid in self.keys:
                result = self._verify_with_key(data, signature, kid)
                if result["valid"]:
                    return result
            return {"valid": False, "error": "No valid key found"}

        return self._verify_with_key(data, signature, key_id)

    def _verify_with_key(self, data: bytes, signature: bytes, key_id: str) -> Dict:
        """Verify signature with specific key."""
        if key_id not in self.keys:
            return {"valid": False, "error": f"Key not found: {key_id}"}

        key_data = self.keys[key_id]

        # Load public key
        public_key = serialization.load_pem_public_key(
            key_data["public_key"].encode("utf-8"), backend=default_backend()
        )

        # Verify signature
        try:
            if key_data["algorithm"] == "rsa":
                public_key.verify(
                    signature,
                    data,
                    padding.PSS(
                        mgf=padding.MGF1(hashes.SHA256()),
                        salt_length=padding.PSS.MAX_LENGTH,
                    ),
                    hashes.SHA256(),
                )
            else:  # ecdsa
                public_key.verify(signature, data, ec.ECDSA(hashes.SHA256()))

            return {
                "valid": True,
                "key_id": key_id,
                "signer": f"{key_data['name']} <{key_data['email']}>",
                "algorithm": key_data["algorithm"],
                "verified_at": datetime.now().isoformat(),
            }
        except Exception as e:
            return {"valid": False, "error": str(e), "key_id": key_id}

    def export_public_key(self, key_id: str) -> str:
        """
        Export public key in PEM format.

        Args:
            key_id: Key ID to export

        Returns:
            PEM-encoded public key
        """
        if key_id not in self.keys:
            raise ValueError(f"Key not found: {key_id}")

        return self.keys[key_id]["public_key"]

    def export_private_key(self, key_id: str) -> str:
        """
        Export private key in PEM format.

        Args:
            key_id: Key ID to export

        Returns:
            PEM-encoded private key
        """
        if key_id not in self.keys:
            raise ValueError(f"Key not found: {key_id}")

        return self.keys[key_id]["private_key"]

    def is_key_expired(self, key_id: str) -> bool:
        """
        Check if a key is expired.

        Args:
            key_id: Key ID to check

        Returns:
            True if expired, False otherwise
        """
        if key_id not in self.keys:
            raise ValueError(f"Key not found: {key_id}")

        key_data = self.keys[key_id]
        if key_data["expires"] is None:
            return False

        expires = datetime.fromisoformat(key_data["expires"])
        return datetime.now() > expires

    def list_keys(self) -> list:
        """
        List all keys in keyring.

        Returns:
            List of key metadata dictionaries
        """
        return [
            {
                "key_id": k["key_id"],
                "name": k["name"],
                "email": k["email"],
                "algorithm": k["algorithm"],
                "created": k["created"],
                "expires": k["expires"],
                "expired": self.is_key_expired(k["key_id"]),
            }
            for k in self.keys.values()
        ]

    def delete_key(self, key_id: str) -> None:
        """
        Delete a key from keyring.

        Args:
            key_id: Key ID to delete
        """
        if key_id not in self.keys:
            raise ValueError(f"Key not found: {key_id}")

        # Remove from memory
        del self.keys[key_id]

        # Remove key file
        key_file = os.path.join(self.keyring_dir, f"{key_id}.key")
        if os.path.exists(key_file):
            os.remove(key_file)

        self._save_keys()
