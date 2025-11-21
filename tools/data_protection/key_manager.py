"""
Key Manager - Key generation, rotation, versioning, and derivation.

TOOL-SEC-012: Key management for devCrew_s1 data protection platform.
Supports PBKDF2, scrypt key derivation and key versioning.
"""

import os
import base64
import hashlib
import logging
import json
import secrets
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, List, Any
from pathlib import Path

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.kdf.scrypt import Scrypt
from cryptography.hazmat.backends import default_backend

logger = logging.getLogger(__name__)


@dataclass
class DerivedKey:
    """Result of key derivation operation."""
    key: bytes
    salt: bytes
    algorithm: str
    iterations: Optional[int] = None
    timestamp: str = ""
    key_id: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary (excluding raw key)."""
        return {
            "salt": base64.b64encode(self.salt).decode(),
            "algorithm": self.algorithm,
            "iterations": self.iterations,
            "timestamp": self.timestamp,
            "key_id": self.key_id
        }


@dataclass
class KeyVersion:
    """Versioned key metadata."""
    version: int
    key_id: str
    created_at: str
    expires_at: Optional[str] = None
    status: str = "active"  # active, rotated, revoked
    algorithm: str = "AES-256-GCM"
    _key: bytes = field(default=b"", repr=False)


class KeyManager:
    """
    Manages encryption keys with versioning, rotation, and derivation.

    Supports:
    - Key generation for various algorithms
    - PBKDF2 and scrypt key derivation
    - Key versioning and rotation
    - Secure key storage interface
    """

    PBKDF2_DEFAULT_ITERATIONS = 600000  # OWASP 2023 recommendation
    SCRYPT_N = 2**14  # CPU/memory cost
    SCRYPT_R = 8      # Block size
    SCRYPT_P = 1      # Parallelization

    def __init__(self, storage_path: Optional[Path] = None):
        """
        Initialize key manager.

        Args:
            storage_path: Optional path for key metadata storage
        """
        self._storage_path = storage_path
        self._keys: Dict[str, KeyVersion] = {}
        self._current_version: Dict[str, int] = {}
        self._audit_log: List[Dict[str, Any]] = []

        if storage_path and storage_path.exists():
            self._load_metadata()

        logger.info("KeyManager initialized")

    def generate_key(self, key_size: int = 32, purpose: str = "encryption") -> bytes:
        """
        Generate a cryptographically secure random key.

        Args:
            key_size: Key size in bytes (default 32 for AES-256)
            purpose: Key purpose for audit logging

        Returns:
            Random key bytes
        """
        key = os.urandom(key_size)
        key_id = hashlib.sha256(key).hexdigest()[:16]

        self._log_operation("generate_key", {
            "key_size": key_size,
            "purpose": purpose,
            "key_id": key_id
        })

        logger.info("Generated %d-byte key for %s, key_id=%s", key_size, purpose, key_id)
        return key

    def derive_key_pbkdf2(
        self,
        password: bytes,
        salt: Optional[bytes] = None,
        key_size: int = 32,
        iterations: Optional[int] = None
    ) -> DerivedKey:
        """
        Derive a key from password using PBKDF2-HMAC-SHA256.

        Args:
            password: Password or passphrase bytes
            salt: Optional salt (generated if not provided)
            key_size: Desired key size in bytes
            iterations: Number of iterations (uses secure default if not specified)

        Returns:
            DerivedKey with key and parameters
        """
        if salt is None:
            salt = os.urandom(16)

        if iterations is None:
            iterations = self.PBKDF2_DEFAULT_ITERATIONS

        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=key_size,
            salt=salt,
            iterations=iterations,
            backend=default_backend()
        )

        key = kdf.derive(password)
        key_id = hashlib.sha256(key).hexdigest()[:16]

        result = DerivedKey(
            key=key,
            salt=salt,
            algorithm="PBKDF2-HMAC-SHA256",
            iterations=iterations,
            timestamp=datetime.now(timezone.utc).isoformat(),
            key_id=key_id
        )

        self._log_operation("derive_key_pbkdf2", {
            "key_size": key_size,
            "iterations": iterations,
            "key_id": key_id
        })

        logger.info(
            "Derived key via PBKDF2: iterations=%d, key_id=%s",
            iterations, key_id
        )

        return result

    def derive_key_scrypt(
        self,
        password: bytes,
        salt: Optional[bytes] = None,
        key_size: int = 32,
        n: Optional[int] = None,
        r: Optional[int] = None,
        p: Optional[int] = None
    ) -> DerivedKey:
        """
        Derive a key from password using scrypt.

        Args:
            password: Password or passphrase bytes
            salt: Optional salt (generated if not provided)
            key_size: Desired key size in bytes
            n: CPU/memory cost parameter
            r: Block size parameter
            p: Parallelization parameter

        Returns:
            DerivedKey with key and parameters
        """
        if salt is None:
            salt = os.urandom(16)

        n = n or self.SCRYPT_N
        r = r or self.SCRYPT_R
        p = p or self.SCRYPT_P

        kdf = Scrypt(
            salt=salt,
            length=key_size,
            n=n,
            r=r,
            p=p,
            backend=default_backend()
        )

        key = kdf.derive(password)
        key_id = hashlib.sha256(key).hexdigest()[:16]

        result = DerivedKey(
            key=key,
            salt=salt,
            algorithm=f"scrypt-n{n}-r{r}-p{p}",
            timestamp=datetime.now(timezone.utc).isoformat(),
            key_id=key_id
        )

        self._log_operation("derive_key_scrypt", {
            "key_size": key_size,
            "n": n,
            "r": r,
            "p": p,
            "key_id": key_id
        })

        logger.info("Derived key via scrypt: n=%d, r=%d, p=%d, key_id=%s", n, r, p, key_id)

        return result

    def create_key_version(
        self,
        name: str,
        key: bytes,
        algorithm: str = "AES-256-GCM",
        ttl_days: Optional[int] = None
    ) -> KeyVersion:
        """
        Create a new versioned key.

        Args:
            name: Key name/identifier
            key: Key bytes
            algorithm: Associated encryption algorithm
            ttl_days: Optional time-to-live in days

        Returns:
            KeyVersion with metadata
        """
        current_version = self._current_version.get(name, 0)
        new_version = current_version + 1

        key_id = hashlib.sha256(key).hexdigest()[:16]
        created_at = datetime.now(timezone.utc)
        expires_at = None
        if ttl_days:
            expires_at = (created_at + timedelta(days=ttl_days)).isoformat()

        version = KeyVersion(
            version=new_version,
            key_id=key_id,
            created_at=created_at.isoformat(),
            expires_at=expires_at,
            status="active",
            algorithm=algorithm,
            _key=key
        )

        version_key = f"{name}:v{new_version}"
        self._keys[version_key] = version
        self._current_version[name] = new_version

        # Mark previous version as rotated
        if current_version > 0:
            prev_key = f"{name}:v{current_version}"
            if prev_key in self._keys:
                self._keys[prev_key].status = "rotated"

        self._log_operation("create_key_version", {
            "name": name,
            "version": new_version,
            "key_id": key_id,
            "algorithm": algorithm
        })

        logger.info(
            "Created key version: name=%s, version=%d, key_id=%s",
            name, new_version, key_id
        )

        self._save_metadata()
        return version

    def get_key(self, name: str, version: Optional[int] = None) -> Optional[KeyVersion]:
        """
        Retrieve a key by name and optional version.

        Args:
            name: Key name
            version: Specific version (latest if not specified)

        Returns:
            KeyVersion if found
        """
        if version is None:
            version = self._current_version.get(name, 0)

        version_key = f"{name}:v{version}"
        key_version = self._keys.get(version_key)

        if key_version:
            self._log_operation("get_key", {
                "name": name,
                "version": version,
                "key_id": key_version.key_id
            })

        return key_version

    def rotate_key(self, name: str, new_key: Optional[bytes] = None) -> KeyVersion:
        """
        Rotate a key to a new version.

        Args:
            name: Key name to rotate
            new_key: New key bytes (generated if not provided)

        Returns:
            New KeyVersion
        """
        current = self.get_key(name)
        if current is None:
            raise ValueError(f"Key not found: {name}")

        if new_key is None:
            # Determine key size from current key
            new_key = self.generate_key(len(current._key))

        new_version = self.create_key_version(
            name=name,
            key=new_key,
            algorithm=current.algorithm,
            ttl_days=None  # Inherit from policy
        )

        logger.info(
            "Rotated key: name=%s, old_version=%d, new_version=%d",
            name, current.version, new_version.version
        )

        return new_version

    def revoke_key(self, name: str, version: int) -> bool:
        """
        Revoke a specific key version.

        Args:
            name: Key name
            version: Version to revoke

        Returns:
            True if revoked successfully
        """
        version_key = f"{name}:v{version}"
        if version_key not in self._keys:
            return False

        self._keys[version_key].status = "revoked"
        self._keys[version_key]._key = b""  # Clear key material

        self._log_operation("revoke_key", {
            "name": name,
            "version": version
        })

        logger.info("Revoked key: name=%s, version=%d", name, version)
        self._save_metadata()
        return True

    def list_keys(self, name: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        List key metadata.

        Args:
            name: Filter by key name (all if not specified)

        Returns:
            List of key metadata dictionaries
        """
        results = []
        for key, version in self._keys.items():
            if name is None or key.startswith(f"{name}:"):
                results.append({
                    "name": key.split(":")[0],
                    "version": version.version,
                    "key_id": version.key_id,
                    "created_at": version.created_at,
                    "expires_at": version.expires_at,
                    "status": version.status,
                    "algorithm": version.algorithm
                })
        return results

    def get_audit_log(self) -> List[Dict[str, Any]]:
        """Return audit log of key operations."""
        return self._audit_log.copy()

    def _log_operation(self, operation: str, details: Dict[str, Any]) -> None:
        """Log a key management operation."""
        self._audit_log.append({
            "operation": operation,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            **details
        })

    def _save_metadata(self) -> None:
        """Save key metadata to storage (excluding key material)."""
        if self._storage_path is None:
            return

        metadata = {
            "keys": {},
            "current_versions": self._current_version
        }

        for key, version in self._keys.items():
            metadata["keys"][key] = {
                "version": version.version,
                "key_id": version.key_id,
                "created_at": version.created_at,
                "expires_at": version.expires_at,
                "status": version.status,
                "algorithm": version.algorithm
            }

        self._storage_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self._storage_path, "w") as f:
            json.dump(metadata, f, indent=2)

    def _load_metadata(self) -> None:
        """Load key metadata from storage."""
        if self._storage_path is None or not self._storage_path.exists():
            return

        try:
            with open(self._storage_path) as f:
                metadata = json.load(f)

            self._current_version = metadata.get("current_versions", {})

            for key, data in metadata.get("keys", {}).items():
                self._keys[key] = KeyVersion(
                    version=data["version"],
                    key_id=data["key_id"],
                    created_at=data["created_at"],
                    expires_at=data.get("expires_at"),
                    status=data.get("status", "active"),
                    algorithm=data.get("algorithm", "AES-256-GCM"),
                    _key=b""  # Key material not stored
                )

            logger.info("Loaded key metadata: %d keys", len(self._keys))
        except (json.JSONDecodeError, KeyError) as e:
            logger.error("Failed to load key metadata: %s", e)
