"""
HSM Client - Hardware Security Module mock interface.

Provides mock HSM/KMS operations for testing environments.
Simulates key storage, signing, and verification operations.
"""

import uuid
from datetime import datetime
from typing import Dict, List, Optional

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec, padding, rsa


class HSMClient:
    """
    Mock Hardware Security Module client.

    Simulates HSM operations for testing without actual hardware.
    """

    def __init__(self, backend: str = "mock", config: Optional[Dict] = None):
        """
        Initialize HSM client.

        Args:
            backend: HSM backend type ("mock", "pkcs11", "aws-kms", "gcp-kms")
            config: Backend-specific configuration
        """
        self.backend = backend
        self.config = config or {}
        self.keys: Dict[str, Dict] = {}
        self.connected = True

    def is_connected(self) -> bool:
        """
        Check if HSM is connected.

        Returns:
            True if connected
        """
        return self.connected

    def connect(self) -> bool:
        """
        Connect to HSM.

        Returns:
            True if connection successful
        """
        self.connected = True
        return True

    def disconnect(self) -> None:
        """Disconnect from HSM."""
        self.connected = False

    def generate_key(
        self,
        key_type: str,
        key_size: int = 2048,
        label: Optional[str] = None,
        extractable: bool = False,
    ) -> str:
        """
        Generate a key in the HSM.

        Args:
            key_type: "rsa" or "ecdsa"
            key_size: Key size (2048, 3072, 4096 for RSA; 256, 384, 521 for ECDSA)
            label: Key label/name
            extractable: Whether key can be exported

        Returns:
            Key ID
        """
        if not self.connected:
            raise RuntimeError("HSM not connected")

        # Generate key
        if key_type.lower() == "rsa":
            private_key = rsa.generate_private_key(
                public_exponent=65537, key_size=key_size, backend=default_backend()
            )
        elif key_type.lower() == "ecdsa":
            curve_map = {256: ec.SECP256R1(), 384: ec.SECP384R1(), 521: ec.SECP521R1()}
            private_key = ec.generate_private_key(
                curve_map.get(key_size, ec.SECP256R1()), backend=default_backend()
            )
        else:
            raise ValueError(f"Unsupported key type: {key_type}")

        # Generate key ID
        key_id = str(uuid.uuid4())

        # Store key metadata
        self.keys[key_id] = {
            "id": key_id,
            "label": label or f"key-{key_id[:8]}",
            "key_type": key_type,
            "key_size": key_size,
            "extractable": extractable,
            "created": datetime.now().isoformat(),
            "usage_count": 0,
            "last_used": None,
            "private_key": private_key,  # In real HSM, this would never be exposed
        }

        return key_id

    def list_keys(self, label_filter: Optional[str] = None) -> List[Dict]:
        """
        List keys in HSM.

        Args:
            label_filter: Optional label filter

        Returns:
            List of key metadata
        """
        if not self.connected:
            raise RuntimeError("HSM not connected")

        keys = []
        for key_data in self.keys.values():
            if label_filter and label_filter not in key_data["label"]:
                continue

            # Return metadata only (no private key)
            keys.append(
                {
                    "id": key_data["id"],
                    "label": key_data["label"],
                    "key_type": key_data["key_type"],
                    "key_size": key_data["key_size"],
                    "extractable": key_data["extractable"],
                    "created": key_data["created"],
                    "usage_count": key_data["usage_count"],
                    "last_used": key_data["last_used"],
                }
            )

        return keys

    def get_public_key(self, key_id: str) -> str:
        """
        Get public key from HSM.

        Args:
            key_id: Key ID

        Returns:
            Public key PEM
        """
        if not self.connected:
            raise RuntimeError("HSM not connected")

        if key_id not in self.keys:
            raise ValueError(f"Key not found: {key_id}")

        private_key = self.keys[key_id]["private_key"]
        public_key = private_key.public_key()

        return public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        ).decode("utf-8")

    def sign(self, key_id: str, data: bytes, algorithm: str = "sha256") -> bytes:
        """
        Sign data with HSM key.

        Args:
            key_id: Key ID to use for signing
            data: Data to sign
            algorithm: Hash algorithm ("sha256", "sha384", "sha512")

        Returns:
            Signature bytes
        """
        if not self.connected:
            raise RuntimeError("HSM not connected")

        if key_id not in self.keys:
            raise ValueError(f"Key not found: {key_id}")

        key_data = self.keys[key_id]
        private_key = key_data["private_key"]

        # Map algorithm
        hash_algo = {
            "sha256": hashes.SHA256(),
            "sha384": hashes.SHA384(),
            "sha512": hashes.SHA512(),
        }.get(algorithm, hashes.SHA256())

        # Sign based on key type
        if key_data["key_type"] == "rsa":
            signature = private_key.sign(
                data,
                padding.PSS(
                    mgf=padding.MGF1(hash_algo), salt_length=padding.PSS.MAX_LENGTH
                ),
                hash_algo,
            )
        else:  # ecdsa
            signature = private_key.sign(data, ec.ECDSA(hash_algo))

        # Update usage stats
        key_data["usage_count"] += 1
        key_data["last_used"] = datetime.now().isoformat()

        return signature

    def verify(
        self, key_id: str, data: bytes, signature: bytes, algorithm: str = "sha256"
    ) -> bool:
        """
        Verify signature with HSM key.

        Args:
            key_id: Key ID
            data: Original data
            signature: Signature to verify
            algorithm: Hash algorithm

        Returns:
            True if signature is valid
        """
        if not self.connected:
            raise RuntimeError("HSM not connected")

        if key_id not in self.keys:
            raise ValueError(f"Key not found: {key_id}")

        key_data = self.keys[key_id]
        private_key = key_data["private_key"]
        public_key = private_key.public_key()

        # Map algorithm
        hash_algo = {
            "sha256": hashes.SHA256(),
            "sha384": hashes.SHA384(),
            "sha512": hashes.SHA512(),
        }.get(algorithm, hashes.SHA256())

        # Verify based on key type
        try:
            if key_data["key_type"] == "rsa":
                public_key.verify(
                    signature,
                    data,
                    padding.PSS(
                        mgf=padding.MGF1(hash_algo), salt_length=padding.PSS.MAX_LENGTH
                    ),
                    hash_algo,
                )
            else:  # ecdsa
                public_key.verify(signature, data, ec.ECDSA(hash_algo))
            return True
        except Exception:
            return False

    def delete_key(self, key_id: str) -> None:
        """
        Delete key from HSM.

        Args:
            key_id: Key ID to delete
        """
        if not self.connected:
            raise RuntimeError("HSM not connected")

        if key_id not in self.keys:
            raise ValueError(f"Key not found: {key_id}")

        del self.keys[key_id]

    def export_key(self, key_id: str) -> str:
        """
        Export private key (if extractable).

        Args:
            key_id: Key ID

        Returns:
            Private key PEM

        Raises:
            ValueError: If key is not extractable
        """
        if not self.connected:
            raise RuntimeError("HSM not connected")

        if key_id not in self.keys:
            raise ValueError(f"Key not found: {key_id}")

        key_data = self.keys[key_id]

        if not key_data["extractable"]:
            raise ValueError("Key is not extractable")

        private_key = key_data["private_key"]
        return private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        ).decode("utf-8")

    def get_key_info(self, key_id: str) -> Dict:
        """
        Get key information.

        Args:
            key_id: Key ID

        Returns:
            Key metadata dictionary
        """
        if not self.connected:
            raise RuntimeError("HSM not connected")

        if key_id not in self.keys:
            raise ValueError(f"Key not found: {key_id}")

        key_data = self.keys[key_id]

        return {
            "id": key_data["id"],
            "label": key_data["label"],
            "key_type": key_data["key_type"],
            "key_size": key_data["key_size"],
            "extractable": key_data["extractable"],
            "created": key_data["created"],
            "usage_count": key_data["usage_count"],
            "last_used": key_data["last_used"],
        }

    def backup_keys(self, output_file: str, password: str) -> None:
        """
        Backup extractable keys to encrypted file.

        Args:
            output_file: Path to backup file
            password: Encryption password
        """
        if not self.connected:
            raise RuntimeError("HSM not connected")

        import json

        backup_data = {
            "backend": self.backend,
            "created": datetime.now().isoformat(),
            "keys": [],
        }

        for key_data in self.keys.values():
            if key_data["extractable"]:
                backup_data["keys"].append(
                    {
                        "id": key_data["id"],
                        "label": key_data["label"],
                        "key_type": key_data["key_type"],
                        "key_size": key_data["key_size"],
                    }
                )

        # In production, this would be encrypted with password
        with open(output_file, "w") as f:
            json.dump(backup_data, f, indent=2)

    def get_hsm_info(self) -> Dict:
        """
        Get HSM information.

        Returns:
            HSM information dictionary
        """
        return {
            "backend": self.backend,
            "connected": self.connected,
            "total_keys": len(self.keys),
            "config": {k: v for k, v in self.config.items() if k != "password"},
        }
