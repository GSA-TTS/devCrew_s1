"""
Field Encryption - Database column encryption and deterministic encryption.

TOOL-SEC-012: Field-level encryption for devCrew_s1 data protection.
"""

import os
import base64
import hashlib
import hmac
import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List, Union

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.backends import default_backend

logger = logging.getLogger(__name__)


@dataclass
class EncryptedField:
    """Encrypted field value with metadata."""
    ciphertext: bytes
    nonce: bytes
    field_name: str
    is_deterministic: bool = False
    key_version: int = 1

    def to_string(self) -> str:
        """Encode as base64 string for storage."""
        prefix = "det:" if self.is_deterministic else "rnd:"
        data = self.nonce + self.ciphertext
        return f"{prefix}v{self.key_version}:{base64.b64encode(data).decode()}"

    @classmethod
    def from_string(cls, encoded: str, field_name: str) -> "EncryptedField":
        """Decode from base64 string."""
        parts = encoded.split(":", 2)
        if len(parts) != 3:
            raise ValueError("Invalid encrypted field format")

        is_deterministic = parts[0] == "det"
        key_version = int(parts[1][1:])
        data = base64.b64decode(parts[2])

        # First 12 bytes are nonce for AES-GCM
        nonce = data[:12]
        ciphertext = data[12:]

        return cls(
            ciphertext=ciphertext,
            nonce=nonce,
            field_name=field_name,
            is_deterministic=is_deterministic,
            key_version=key_version
        )


class FieldEncryption:
    """
    Field-level encryption for database columns.

    Supports:
    - Randomized encryption (different ciphertext each time)
    - Deterministic encryption (same plaintext = same ciphertext, enables queries)
    - Per-field key derivation
    - Key versioning for rotation
    """

    NONCE_SIZE = 12

    def __init__(self, master_key: bytes, key_version: int = 1):
        """
        Initialize field encryption.

        Args:
            master_key: 32-byte master key for field key derivation
            key_version: Current key version
        """
        if len(master_key) != 32:
            raise ValueError("Master key must be 32 bytes")

        self._master_key = master_key
        self._key_version = key_version
        self._field_keys: Dict[str, bytes] = {}
        self._audit_log: list = []

        logger.info("FieldEncryption initialized with key_version=%d", key_version)

    def _derive_field_key(self, field_name: str) -> bytes:
        """Derive a unique key for a specific field."""
        if field_name in self._field_keys:
            return self._field_keys[field_name]

        hkdf = HKDF(
            algorithm=hashes.SHA256(),
            length=32,
            salt=None,
            info=f"field:{field_name}:v{self._key_version}".encode(),
            backend=default_backend()
        )
        field_key = hkdf.derive(self._master_key)
        self._field_keys[field_name] = field_key

        return field_key

    def _deterministic_nonce(self, field_name: str, plaintext: bytes) -> bytes:
        """Generate deterministic nonce using HMAC."""
        # Use HMAC to derive nonce from plaintext - same plaintext = same nonce
        key = self._derive_field_key(field_name + ":nonce")
        h = hmac.new(key, plaintext, hashlib.sha256)
        return h.digest()[:self.NONCE_SIZE]

    def encrypt_field(
        self,
        field_name: str,
        value: Union[str, bytes],
        deterministic: bool = False
    ) -> EncryptedField:
        """
        Encrypt a field value.

        Args:
            field_name: Name of the database field/column
            value: Value to encrypt (string or bytes)
            deterministic: If True, same value produces same ciphertext

        Returns:
            EncryptedField with encrypted value
        """
        if isinstance(value, str):
            plaintext = value.encode("utf-8")
        else:
            plaintext = value

        field_key = self._derive_field_key(field_name)
        aesgcm = AESGCM(field_key)

        if deterministic:
            nonce = self._deterministic_nonce(field_name, plaintext)
        else:
            nonce = os.urandom(self.NONCE_SIZE)

        ciphertext = aesgcm.encrypt(nonce, plaintext, field_name.encode())

        result = EncryptedField(
            ciphertext=ciphertext,
            nonce=nonce,
            field_name=field_name,
            is_deterministic=deterministic,
            key_version=self._key_version
        )

        self._log_operation("encrypt_field", {
            "field_name": field_name,
            "deterministic": deterministic,
            "plaintext_size": len(plaintext)
        })

        logger.debug(
            "Encrypted field: name=%s, deterministic=%s, size=%d",
            field_name, deterministic, len(plaintext)
        )

        return result

    def decrypt_field(self, encrypted: EncryptedField) -> bytes:
        """
        Decrypt an encrypted field.

        Args:
            encrypted: EncryptedField to decrypt

        Returns:
            Decrypted value as bytes
        """
        field_key = self._derive_field_key(encrypted.field_name)
        aesgcm = AESGCM(field_key)

        plaintext = aesgcm.decrypt(
            encrypted.nonce,
            encrypted.ciphertext,
            encrypted.field_name.encode()
        )

        self._log_operation("decrypt_field", {
            "field_name": encrypted.field_name,
            "deterministic": encrypted.is_deterministic
        })

        logger.debug("Decrypted field: name=%s", encrypted.field_name)

        return plaintext

    def decrypt_field_string(self, encrypted: EncryptedField) -> str:
        """Decrypt field and return as UTF-8 string."""
        return self.decrypt_field(encrypted).decode("utf-8")

    def encrypt_row(
        self,
        row: Dict[str, Any],
        encrypt_fields: List[str],
        deterministic_fields: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Encrypt specified fields in a row dictionary.

        Args:
            row: Dictionary representing a database row
            encrypt_fields: List of field names to encrypt
            deterministic_fields: Fields to encrypt deterministically

        Returns:
            Row with specified fields encrypted
        """
        deterministic_fields = deterministic_fields or []
        result = row.copy()

        for field_name in encrypt_fields:
            if field_name in row and row[field_name] is not None:
                is_det = field_name in deterministic_fields
                encrypted = self.encrypt_field(field_name, row[field_name], is_det)
                result[field_name] = encrypted.to_string()

        return result

    def decrypt_row(
        self,
        row: Dict[str, Any],
        encrypted_fields: List[str]
    ) -> Dict[str, Any]:
        """
        Decrypt specified fields in a row dictionary.

        Args:
            row: Dictionary with encrypted field values
            encrypted_fields: List of field names that are encrypted

        Returns:
            Row with specified fields decrypted
        """
        result = row.copy()

        for field_name in encrypted_fields:
            if field_name in row and row[field_name] is not None:
                encrypted = EncryptedField.from_string(row[field_name], field_name)
                result[field_name] = self.decrypt_field_string(encrypted)

        return result

    def generate_searchable_hash(self, field_name: str, value: Union[str, bytes]) -> str:
        """
        Generate a searchable hash for blind index queries.

        This allows equality searches on encrypted data without
        revealing the plaintext.

        Args:
            field_name: Field name for key derivation
            value: Value to hash

        Returns:
            Base64-encoded hash for indexing
        """
        if isinstance(value, str):
            value = value.encode("utf-8")

        # Use a separate key for hashing
        hash_key = self._derive_field_key(field_name + ":hash")
        h = hmac.new(hash_key, value, hashlib.sha256)

        return base64.b64encode(h.digest()).decode()

    def rotate_key(self, new_master_key: bytes, new_version: int) -> "FieldEncryption":
        """
        Create a new FieldEncryption instance with rotated key.

        Note: Existing encrypted data must be re-encrypted with the new key.

        Args:
            new_master_key: New 32-byte master key
            new_version: New key version number

        Returns:
            New FieldEncryption instance
        """
        logger.info(
            "Key rotation: old_version=%d, new_version=%d",
            self._key_version, new_version
        )

        return FieldEncryption(new_master_key, new_version)

    def get_audit_log(self) -> list:
        """Return audit log of field operations."""
        return self._audit_log.copy()

    def _log_operation(self, operation: str, details: Dict[str, Any]) -> None:
        """Log a field encryption operation."""
        self._audit_log.append({
            "operation": operation,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            **details
        })


class EncryptedColumnType:
    """
    SQLAlchemy-compatible encrypted column type.

    Usage with SQLAlchemy:
        class User(Base):
            ssn = Column(EncryptedColumnType(field_encryption, "ssn", deterministic=True))
    """

    def __init__(
        self,
        field_encryption: FieldEncryption,
        field_name: str,
        deterministic: bool = False
    ):
        """
        Initialize encrypted column type.

        Args:
            field_encryption: FieldEncryption instance
            field_name: Column/field name
            deterministic: Use deterministic encryption
        """
        self._fe = field_encryption
        self._field_name = field_name
        self._deterministic = deterministic

    def process_bind_param(self, value: Optional[str]) -> Optional[str]:
        """Encrypt value before storing."""
        if value is None:
            return None
        encrypted = self._fe.encrypt_field(
            self._field_name, value, self._deterministic
        )
        return encrypted.to_string()

    def process_result_value(self, value: Optional[str]) -> Optional[str]:
        """Decrypt value after loading."""
        if value is None:
            return None
        encrypted = EncryptedField.from_string(value, self._field_name)
        return self._fe.decrypt_field_string(encrypted)
