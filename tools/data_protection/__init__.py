"""
Data Protection & Encryption Platform for devCrew_s1.

TOOL-SEC-012: Comprehensive encryption toolkit supporting AES-256-GCM,
RSA, NaCl, envelope encryption, and secrets management integration.
"""

from .encryption_engine import EncryptionEngine, AESGCMCipher, RSACipher, NaClCipher
from .key_manager import KeyManager, DerivedKey
from .envelope_encryption import EnvelopeEncryption
from .field_encryption import FieldEncryption
from .secrets_integration import SecretsClient, VaultClient
from .sops_integration import SOPSManager

__version__ = "1.0.0"
__all__ = [
    "EncryptionEngine",
    "AESGCMCipher",
    "RSACipher",
    "NaClCipher",
    "KeyManager",
    "DerivedKey",
    "EnvelopeEncryption",
    "FieldEncryption",
    "SecretsClient",
    "VaultClient",
    "SOPSManager",
]
