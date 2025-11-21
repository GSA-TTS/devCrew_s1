"""
Digital Signing & Verification Platform.

A comprehensive cryptographic signing solution supporting container images,
files, and documents with multiple signing methods (GPG, Cosign, X.509).

Key Components:
- GPGHandler: GPG-style key generation and signing
- CertificateManager: X.509 certificate operations
- CosignManager: Container image signing simulation
- VerificationEngine: Multi-format signature verification
- HSMClient: Hardware Security Module mock interface
- PolicyEngine: Policy-based verification rules
"""

from cert_manager import CertificateManager
from cosign_manager import CosignManager
from gpg_handler import GPGHandler
from hsm_client import HSMClient
from policy_engine import PolicyEngine
from verification_engine import VerificationEngine

__version__ = "1.0.0"
__author__ = "devCrew_s1"

__all__ = [
    "GPGHandler",
    "CertificateManager",
    "CosignManager",
    "VerificationEngine",
    "HSMClient",
    "PolicyEngine",
]
