"""
Encryption Engine - AES-256-GCM, RSA, NaCl encryption/decryption with AEAD support.

TOOL-SEC-012: Core encryption primitives for devCrew_s1 data protection platform.
"""

import os
import base64
import logging
import hashlib
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional, Tuple, Dict, Any

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.backends import default_backend

logger = logging.getLogger(__name__)


@dataclass
class EncryptionResult:
    """Result of an encryption operation."""
    ciphertext: bytes
    nonce: Optional[bytes] = None
    tag: Optional[bytes] = None
    algorithm: str = ""
    timestamp: str = ""
    key_id: Optional[str] = None


@dataclass
class DecryptionResult:
    """Result of a decryption operation."""
    plaintext: bytes
    verified: bool = True
    algorithm: str = ""
    timestamp: str = ""


class BaseCipher(ABC):
    """Abstract base class for cipher implementations."""

    @abstractmethod
    def encrypt(self, plaintext: bytes, associated_data: Optional[bytes] = None) -> EncryptionResult:
        """Encrypt plaintext with optional associated data for AEAD."""
        pass

    @abstractmethod
    def decrypt(self, ciphertext: bytes, nonce: Optional[bytes] = None,
                associated_data: Optional[bytes] = None) -> DecryptionResult:
        """Decrypt ciphertext with optional associated data verification."""
        pass


class AESGCMCipher(BaseCipher):
    """AES-256-GCM authenticated encryption cipher."""

    ALGORITHM = "AES-256-GCM"
    KEY_SIZE = 32  # 256 bits
    NONCE_SIZE = 12  # 96 bits recommended for GCM

    def __init__(self, key: bytes):
        """
        Initialize AES-256-GCM cipher.

        Args:
            key: 32-byte encryption key
        """
        if len(key) != self.KEY_SIZE:
            raise ValueError(f"Key must be {self.KEY_SIZE} bytes for AES-256")
        self._key = key
        self._aesgcm = AESGCM(key)
        self._key_id = hashlib.sha256(key).hexdigest()[:16]
        logger.info("AES-256-GCM cipher initialized with key_id=%s", self._key_id)

    def encrypt(self, plaintext: bytes, associated_data: Optional[bytes] = None) -> EncryptionResult:
        """
        Encrypt plaintext using AES-256-GCM.

        Args:
            plaintext: Data to encrypt
            associated_data: Additional authenticated data (AAD)

        Returns:
            EncryptionResult with ciphertext and nonce
        """
        nonce = os.urandom(self.NONCE_SIZE)
        ciphertext = self._aesgcm.encrypt(nonce, plaintext, associated_data)

        logger.info(
            "AES-256-GCM encryption: plaintext_len=%d, ciphertext_len=%d, key_id=%s",
            len(plaintext), len(ciphertext), self._key_id
        )

        return EncryptionResult(
            ciphertext=ciphertext,
            nonce=nonce,
            algorithm=self.ALGORITHM,
            timestamp=datetime.now(timezone.utc).isoformat(),
            key_id=self._key_id
        )

    def decrypt(self, ciphertext: bytes, nonce: Optional[bytes] = None,
                associated_data: Optional[bytes] = None) -> DecryptionResult:
        """
        Decrypt ciphertext using AES-256-GCM.

        Args:
            ciphertext: Data to decrypt (includes auth tag)
            nonce: 12-byte nonce used during encryption
            associated_data: Additional authenticated data (AAD)

        Returns:
            DecryptionResult with plaintext
        """
        if nonce is None:
            raise ValueError("Nonce is required for AES-GCM decryption")

        plaintext = self._aesgcm.decrypt(nonce, ciphertext, associated_data)

        logger.info(
            "AES-256-GCM decryption: ciphertext_len=%d, plaintext_len=%d, key_id=%s",
            len(ciphertext), len(plaintext), self._key_id
        )

        return DecryptionResult(
            plaintext=plaintext,
            verified=True,
            algorithm=self.ALGORITHM,
            timestamp=datetime.now(timezone.utc).isoformat()
        )


class RSACipher(BaseCipher):
    """RSA asymmetric encryption cipher."""

    ALGORITHM = "RSA-OAEP-SHA256"
    DEFAULT_KEY_SIZE = 2048

    def __init__(
        self,
        private_key: Optional[rsa.RSAPrivateKey] = None,
        public_key: Optional[rsa.RSAPublicKey] = None,
        key_size: int = DEFAULT_KEY_SIZE
    ):
        """
        Initialize RSA cipher.

        Args:
            private_key: RSA private key for decryption
            public_key: RSA public key for encryption
            key_size: Key size in bits for key generation
        """
        if private_key is None and public_key is None:
            # Generate new key pair
            private_key = rsa.generate_private_key(
                public_exponent=65537,
                key_size=key_size,
                backend=default_backend()
            )
            public_key = private_key.public_key()
            logger.info("Generated new RSA-%d key pair", key_size)

        self._private_key = private_key
        self._public_key = public_key or (private_key.public_key() if private_key else None)

        if self._public_key:
            key_bytes = self._public_key.public_bytes(
                encoding=serialization.Encoding.DER,
                format=serialization.PublicFormat.SubjectPublicKeyInfo
            )
            self._key_id = hashlib.sha256(key_bytes).hexdigest()[:16]
        else:
            self._key_id = "unknown"

    def encrypt(self, plaintext: bytes, associated_data: Optional[bytes] = None) -> EncryptionResult:
        """
        Encrypt plaintext using RSA-OAEP.

        Args:
            plaintext: Data to encrypt (limited by key size)
            associated_data: Ignored for RSA (use hybrid encryption for AEAD)

        Returns:
            EncryptionResult with ciphertext
        """
        if self._public_key is None:
            raise ValueError("Public key required for encryption")

        ciphertext = self._public_key.encrypt(
            plaintext,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )

        logger.info(
            "RSA encryption: plaintext_len=%d, ciphertext_len=%d, key_id=%s",
            len(plaintext), len(ciphertext), self._key_id
        )

        return EncryptionResult(
            ciphertext=ciphertext,
            algorithm=self.ALGORITHM,
            timestamp=datetime.now(timezone.utc).isoformat(),
            key_id=self._key_id
        )

    def decrypt(self, ciphertext: bytes, nonce: Optional[bytes] = None,
                associated_data: Optional[bytes] = None) -> DecryptionResult:
        """
        Decrypt ciphertext using RSA-OAEP.

        Args:
            ciphertext: Data to decrypt
            nonce: Ignored for RSA
            associated_data: Ignored for RSA

        Returns:
            DecryptionResult with plaintext
        """
        if self._private_key is None:
            raise ValueError("Private key required for decryption")

        plaintext = self._private_key.decrypt(
            ciphertext,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )

        logger.info(
            "RSA decryption: ciphertext_len=%d, plaintext_len=%d, key_id=%s",
            len(ciphertext), len(plaintext), self._key_id
        )

        return DecryptionResult(
            plaintext=plaintext,
            verified=True,
            algorithm=self.ALGORITHM,
            timestamp=datetime.now(timezone.utc).isoformat()
        )

    def export_public_key(self) -> bytes:
        """Export public key in PEM format."""
        if self._public_key is None:
            raise ValueError("No public key available")
        return self._public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )

    def export_private_key(self, password: Optional[bytes] = None) -> bytes:
        """Export private key in PEM format, optionally encrypted."""
        if self._private_key is None:
            raise ValueError("No private key available")

        encryption = (
            serialization.BestAvailableEncryption(password)
            if password else serialization.NoEncryption()
        )

        return self._private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=encryption
        )


class NaClCipher(BaseCipher):
    """NaCl/libsodium encryption cipher using PyNaCl or fallback."""

    ALGORITHM = "NaCl-SecretBox"
    KEY_SIZE = 32
    NONCE_SIZE = 24

    def __init__(self, key: bytes):
        """
        Initialize NaCl cipher.

        Args:
            key: 32-byte secret key
        """
        if len(key) != self.KEY_SIZE:
            raise ValueError(f"Key must be {self.KEY_SIZE} bytes for NaCl")

        self._key = key
        self._key_id = hashlib.sha256(key).hexdigest()[:16]
        self._use_pynacl = False
        self._box = None

        try:
            import nacl.secret
            import nacl.utils
            self._box = nacl.secret.SecretBox(key)
            self._use_pynacl = True
            logger.info("NaCl cipher initialized with PyNaCl, key_id=%s", self._key_id)
        except ImportError:
            # Fallback to AES-GCM as NaCl substitute
            logger.warning("PyNaCl not available, using AES-GCM fallback")
            self._fallback = AESGCMCipher(key)

    def encrypt(self, plaintext: bytes, associated_data: Optional[bytes] = None) -> EncryptionResult:
        """
        Encrypt plaintext using NaCl SecretBox.

        Args:
            plaintext: Data to encrypt
            associated_data: Ignored for NaCl SecretBox

        Returns:
            EncryptionResult with ciphertext and nonce
        """
        if self._use_pynacl and self._box:
            import nacl.utils
            nonce = nacl.utils.random(self.NONCE_SIZE)
            encrypted = self._box.encrypt(plaintext, nonce)
            # PyNaCl prepends nonce to ciphertext
            ciphertext = encrypted.ciphertext

            logger.info(
                "NaCl encryption: plaintext_len=%d, ciphertext_len=%d, key_id=%s",
                len(plaintext), len(ciphertext), self._key_id
            )

            return EncryptionResult(
                ciphertext=ciphertext,
                nonce=nonce,
                algorithm=self.ALGORITHM,
                timestamp=datetime.now(timezone.utc).isoformat(),
                key_id=self._key_id
            )
        else:
            result = self._fallback.encrypt(plaintext, associated_data)
            result.algorithm = self.ALGORITHM + "-Fallback"
            return result

    def decrypt(self, ciphertext: bytes, nonce: Optional[bytes] = None,
                associated_data: Optional[bytes] = None) -> DecryptionResult:
        """
        Decrypt ciphertext using NaCl SecretBox.

        Args:
            ciphertext: Data to decrypt
            nonce: 24-byte nonce used during encryption
            associated_data: Ignored for NaCl SecretBox

        Returns:
            DecryptionResult with plaintext
        """
        if self._use_pynacl and self._box:
            if nonce is None:
                raise ValueError("Nonce is required for NaCl decryption")

            # Reconstruct the encrypted message with nonce
            import nacl.utils
            full_message = nonce + ciphertext
            plaintext = self._box.decrypt(full_message)

            logger.info(
                "NaCl decryption: ciphertext_len=%d, plaintext_len=%d, key_id=%s",
                len(ciphertext), len(plaintext), self._key_id
            )

            return DecryptionResult(
                plaintext=plaintext,
                verified=True,
                algorithm=self.ALGORITHM,
                timestamp=datetime.now(timezone.utc).isoformat()
            )
        else:
            result = self._fallback.decrypt(ciphertext, nonce, associated_data)
            result.algorithm = self.ALGORITHM + "-Fallback"
            return result


class EncryptionEngine:
    """
    High-level encryption engine supporting multiple algorithms.

    Provides a unified interface for AES-256-GCM, RSA, and NaCl encryption
    with audit logging and key management integration.
    """

    SUPPORTED_ALGORITHMS = ["AES-256-GCM", "RSA-OAEP-SHA256", "NaCl-SecretBox"]

    def __init__(self, default_algorithm: str = "AES-256-GCM"):
        """
        Initialize encryption engine.

        Args:
            default_algorithm: Default encryption algorithm to use
        """
        if default_algorithm not in self.SUPPORTED_ALGORITHMS:
            raise ValueError(f"Unsupported algorithm: {default_algorithm}")

        self._default_algorithm = default_algorithm
        self._ciphers: Dict[str, BaseCipher] = {}
        self._audit_log: list = []

        logger.info("EncryptionEngine initialized with default=%s", default_algorithm)

    def register_cipher(self, name: str, cipher: BaseCipher) -> None:
        """Register a cipher instance for use."""
        self._ciphers[name] = cipher
        logger.info("Registered cipher: %s", name)

    def encrypt(
        self,
        plaintext: bytes,
        cipher_name: Optional[str] = None,
        associated_data: Optional[bytes] = None
    ) -> EncryptionResult:
        """
        Encrypt data using the specified or default cipher.

        Args:
            plaintext: Data to encrypt
            cipher_name: Name of registered cipher to use
            associated_data: Additional authenticated data

        Returns:
            EncryptionResult with encrypted data
        """
        cipher_name = cipher_name or "default"
        if cipher_name not in self._ciphers:
            raise ValueError(f"Cipher not registered: {cipher_name}")

        result = self._ciphers[cipher_name].encrypt(plaintext, associated_data)

        self._audit_log.append({
            "operation": "encrypt",
            "cipher": cipher_name,
            "algorithm": result.algorithm,
            "plaintext_size": len(plaintext),
            "ciphertext_size": len(result.ciphertext),
            "timestamp": result.timestamp,
            "key_id": result.key_id
        })

        return result

    def decrypt(
        self,
        ciphertext: bytes,
        cipher_name: Optional[str] = None,
        nonce: Optional[bytes] = None,
        associated_data: Optional[bytes] = None
    ) -> DecryptionResult:
        """
        Decrypt data using the specified or default cipher.

        Args:
            ciphertext: Data to decrypt
            cipher_name: Name of registered cipher to use
            nonce: Nonce/IV if required by algorithm
            associated_data: Additional authenticated data

        Returns:
            DecryptionResult with decrypted data
        """
        cipher_name = cipher_name or "default"
        if cipher_name not in self._ciphers:
            raise ValueError(f"Cipher not registered: {cipher_name}")

        result = self._ciphers[cipher_name].decrypt(ciphertext, nonce, associated_data)

        self._audit_log.append({
            "operation": "decrypt",
            "cipher": cipher_name,
            "algorithm": result.algorithm,
            "ciphertext_size": len(ciphertext),
            "plaintext_size": len(result.plaintext),
            "timestamp": result.timestamp,
            "verified": result.verified
        })

        return result

    def get_audit_log(self) -> list:
        """Return audit log of encryption operations."""
        return self._audit_log.copy()

    def clear_audit_log(self) -> None:
        """Clear the audit log."""
        self._audit_log.clear()
        logger.info("Audit log cleared")


def generate_key(algorithm: str = "AES-256-GCM") -> bytes:
    """
    Generate a cryptographically secure key for the specified algorithm.

    Args:
        algorithm: Encryption algorithm

    Returns:
        Random key bytes
    """
    if algorithm in ("AES-256-GCM", "NaCl-SecretBox"):
        return os.urandom(32)
    else:
        raise ValueError(f"Key generation not supported for: {algorithm}")
