"""
Envelope Encryption - DEK/KEK management and multi-layer encryption.

TOOL-SEC-012: Envelope encryption pattern for devCrew_s1 data protection.
"""

import os
import base64
import hashlib
import json
import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional, Dict, Any, Callable

from .encryption_engine import AESGCMCipher, RSACipher, EncryptionResult

logger = logging.getLogger(__name__)


@dataclass
class EnvelopeEncryptedData:
    """Result of envelope encryption."""
    encrypted_dek: bytes
    encrypted_data: bytes
    nonce: bytes
    kek_id: str
    dek_algorithm: str = "AES-256-GCM"
    kek_algorithm: str = "RSA-OAEP-SHA256"
    timestamp: str = ""
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "encrypted_dek": base64.b64encode(self.encrypted_dek).decode(),
            "encrypted_data": base64.b64encode(self.encrypted_data).decode(),
            "nonce": base64.b64encode(self.nonce).decode(),
            "kek_id": self.kek_id,
            "dek_algorithm": self.dek_algorithm,
            "kek_algorithm": self.kek_algorithm,
            "timestamp": self.timestamp,
            "metadata": self.metadata
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "EnvelopeEncryptedData":
        """Deserialize from dictionary."""
        return cls(
            encrypted_dek=base64.b64decode(data["encrypted_dek"]),
            encrypted_data=base64.b64decode(data["encrypted_data"]),
            nonce=base64.b64decode(data["nonce"]),
            kek_id=data["kek_id"],
            dek_algorithm=data.get("dek_algorithm", "AES-256-GCM"),
            kek_algorithm=data.get("kek_algorithm", "RSA-OAEP-SHA256"),
            timestamp=data.get("timestamp", ""),
            metadata=data.get("metadata", {})
        )

    def to_bytes(self) -> bytes:
        """Serialize to JSON bytes."""
        return json.dumps(self.to_dict()).encode()

    @classmethod
    def from_bytes(cls, data: bytes) -> "EnvelopeEncryptedData":
        """Deserialize from JSON bytes."""
        return cls.from_dict(json.loads(data.decode()))


class EnvelopeEncryption:
    """
    Implements envelope encryption pattern with DEK/KEK separation.

    The envelope encryption pattern:
    1. Generate a random Data Encryption Key (DEK)
    2. Encrypt data with DEK using symmetric encryption (AES-256-GCM)
    3. Encrypt DEK with Key Encryption Key (KEK) using asymmetric encryption
    4. Store encrypted DEK alongside encrypted data

    Benefits:
    - Fast symmetric encryption for data
    - Secure key distribution via asymmetric encryption
    - Easy key rotation (only re-encrypt DEK)
    - Multiple recipients support
    """

    DEK_SIZE = 32  # AES-256

    def __init__(
        self,
        kek_cipher: Optional[RSACipher] = None,
        kms_encrypt: Optional[Callable[[bytes], bytes]] = None,
        kms_decrypt: Optional[Callable[[bytes], bytes]] = None
    ):
        """
        Initialize envelope encryption.

        Args:
            kek_cipher: RSA cipher for KEK operations
            kms_encrypt: Optional KMS encrypt function
            kms_decrypt: Optional KMS decrypt function
        """
        self._kek_cipher = kek_cipher
        self._kms_encrypt = kms_encrypt
        self._kms_decrypt = kms_decrypt
        self._audit_log: list = []

        if kek_cipher is None and kms_encrypt is None:
            # Generate default RSA key pair
            self._kek_cipher = RSACipher(key_size=2048)
            logger.info("EnvelopeEncryption initialized with generated RSA-2048 KEK")
        else:
            logger.info("EnvelopeEncryption initialized with provided KEK")

    def encrypt(
        self,
        plaintext: bytes,
        associated_data: Optional[bytes] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> EnvelopeEncryptedData:
        """
        Encrypt data using envelope encryption.

        Args:
            plaintext: Data to encrypt
            associated_data: Additional authenticated data for AEAD
            metadata: Optional metadata to include

        Returns:
            EnvelopeEncryptedData with encrypted DEK and data
        """
        # Generate random DEK
        dek = os.urandom(self.DEK_SIZE)
        dek_id = hashlib.sha256(dek).hexdigest()[:16]

        # Encrypt data with DEK
        dek_cipher = AESGCMCipher(dek)
        data_result = dek_cipher.encrypt(plaintext, associated_data)

        # Encrypt DEK with KEK
        if self._kms_encrypt:
            encrypted_dek = self._kms_encrypt(dek)
            kek_id = "kms"
            kek_algorithm = "KMS"
        elif self._kek_cipher:
            kek_result = self._kek_cipher.encrypt(dek)
            encrypted_dek = kek_result.ciphertext
            kek_id = kek_result.key_id or "unknown"
            kek_algorithm = kek_result.algorithm
        else:
            raise ValueError("No KEK cipher or KMS configured")

        result = EnvelopeEncryptedData(
            encrypted_dek=encrypted_dek,
            encrypted_data=data_result.ciphertext,
            nonce=data_result.nonce,
            kek_id=kek_id,
            dek_algorithm="AES-256-GCM",
            kek_algorithm=kek_algorithm,
            timestamp=datetime.now(timezone.utc).isoformat(),
            metadata=metadata or {}
        )

        self._log_operation("envelope_encrypt", {
            "plaintext_size": len(plaintext),
            "ciphertext_size": len(data_result.ciphertext),
            "dek_id": dek_id,
            "kek_id": kek_id
        })

        logger.info(
            "Envelope encryption: plaintext_len=%d, dek_id=%s, kek_id=%s",
            len(plaintext), dek_id, kek_id
        )

        return result

    def decrypt(
        self,
        envelope: EnvelopeEncryptedData,
        associated_data: Optional[bytes] = None
    ) -> bytes:
        """
        Decrypt envelope-encrypted data.

        Args:
            envelope: Envelope encrypted data
            associated_data: Additional authenticated data for AEAD verification

        Returns:
            Decrypted plaintext
        """
        # Decrypt DEK with KEK
        if self._kms_decrypt and envelope.kek_algorithm == "KMS":
            dek = self._kms_decrypt(envelope.encrypted_dek)
        elif self._kek_cipher:
            dek_result = self._kek_cipher.decrypt(envelope.encrypted_dek)
            dek = dek_result.plaintext
        else:
            raise ValueError("No KEK cipher or KMS configured for decryption")

        dek_id = hashlib.sha256(dek).hexdigest()[:16]

        # Decrypt data with DEK
        dek_cipher = AESGCMCipher(dek)
        data_result = dek_cipher.decrypt(
            envelope.encrypted_data,
            envelope.nonce,
            associated_data
        )

        self._log_operation("envelope_decrypt", {
            "ciphertext_size": len(envelope.encrypted_data),
            "plaintext_size": len(data_result.plaintext),
            "dek_id": dek_id,
            "kek_id": envelope.kek_id
        })

        logger.info(
            "Envelope decryption: ciphertext_len=%d, dek_id=%s, kek_id=%s",
            len(envelope.encrypted_data), dek_id, envelope.kek_id
        )

        return data_result.plaintext

    def rewrap_dek(
        self,
        envelope: EnvelopeEncryptedData,
        new_kek_cipher: Optional[RSACipher] = None,
        new_kms_encrypt: Optional[Callable[[bytes], bytes]] = None
    ) -> EnvelopeEncryptedData:
        """
        Re-encrypt DEK with a new KEK (for key rotation).

        Args:
            envelope: Existing envelope encrypted data
            new_kek_cipher: New RSA cipher for KEK
            new_kms_encrypt: New KMS encrypt function

        Returns:
            New EnvelopeEncryptedData with re-wrapped DEK
        """
        # Decrypt existing DEK
        if self._kms_decrypt and envelope.kek_algorithm == "KMS":
            dek = self._kms_decrypt(envelope.encrypted_dek)
        elif self._kek_cipher:
            dek_result = self._kek_cipher.decrypt(envelope.encrypted_dek)
            dek = dek_result.plaintext
        else:
            raise ValueError("Cannot decrypt existing DEK")

        # Re-encrypt DEK with new KEK
        if new_kms_encrypt:
            new_encrypted_dek = new_kms_encrypt(dek)
            new_kek_id = "kms"
            new_kek_algorithm = "KMS"
        elif new_kek_cipher:
            new_kek_result = new_kek_cipher.encrypt(dek)
            new_encrypted_dek = new_kek_result.ciphertext
            new_kek_id = new_kek_result.key_id or "unknown"
            new_kek_algorithm = new_kek_result.algorithm
        else:
            raise ValueError("No new KEK provided")

        new_envelope = EnvelopeEncryptedData(
            encrypted_dek=new_encrypted_dek,
            encrypted_data=envelope.encrypted_data,
            nonce=envelope.nonce,
            kek_id=new_kek_id,
            dek_algorithm=envelope.dek_algorithm,
            kek_algorithm=new_kek_algorithm,
            timestamp=datetime.now(timezone.utc).isoformat(),
            metadata=envelope.metadata
        )

        self._log_operation("rewrap_dek", {
            "old_kek_id": envelope.kek_id,
            "new_kek_id": new_kek_id
        })

        logger.info(
            "DEK rewrapped: old_kek_id=%s, new_kek_id=%s",
            envelope.kek_id, new_kek_id
        )

        return new_envelope

    def get_audit_log(self) -> list:
        """Return audit log of envelope operations."""
        return self._audit_log.copy()

    def _log_operation(self, operation: str, details: Dict[str, Any]) -> None:
        """Log an envelope encryption operation."""
        self._audit_log.append({
            "operation": operation,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            **details
        })


class MultiLayerEncryption:
    """
    Multi-layer encryption for defense in depth.

    Applies multiple encryption layers with different keys/algorithms.
    """

    def __init__(self, layers: list):
        """
        Initialize multi-layer encryption.

        Args:
            layers: List of (cipher, name) tuples to apply in order
        """
        self._layers = layers
        self._audit_log: list = []
        logger.info("MultiLayerEncryption initialized with %d layers", len(layers))

    def encrypt(self, plaintext: bytes) -> Dict[str, Any]:
        """
        Encrypt data through all layers.

        Returns:
            Dictionary with ciphertext and layer metadata
        """
        data = plaintext
        layer_info = []

        for cipher, name in self._layers:
            result = cipher.encrypt(data)
            data = result.ciphertext

            info = {
                "name": name,
                "algorithm": result.algorithm,
                "nonce": base64.b64encode(result.nonce).decode() if result.nonce else None
            }
            layer_info.append(info)

        self._audit_log.append({
            "operation": "multi_layer_encrypt",
            "layers": len(self._layers),
            "timestamp": datetime.now(timezone.utc).isoformat()
        })

        return {
            "ciphertext": data,
            "layers": layer_info
        }

    def decrypt(self, encrypted: Dict[str, Any]) -> bytes:
        """
        Decrypt data through all layers in reverse.

        Args:
            encrypted: Dictionary from encrypt()

        Returns:
            Decrypted plaintext
        """
        data = encrypted["ciphertext"]
        layer_info = encrypted["layers"]

        # Decrypt in reverse order
        for (cipher, name), info in zip(reversed(self._layers), reversed(layer_info)):
            nonce = base64.b64decode(info["nonce"]) if info.get("nonce") else None
            result = cipher.decrypt(data, nonce)
            data = result.plaintext

        self._audit_log.append({
            "operation": "multi_layer_decrypt",
            "layers": len(self._layers),
            "timestamp": datetime.now(timezone.utc).isoformat()
        })

        return data
