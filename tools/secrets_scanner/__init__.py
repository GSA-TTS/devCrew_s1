"""
Secrets Scanner & Detection Platform for devCrew_s1.

TOOL-SEC-006: Comprehensive secret detection with pattern matching,
entropy analysis, and Git history scanning.
"""

from .secret_scanner import SecretScanner, SecretFinding, ScanResult
from .git_scanner import GitScanner, CommitScan, BranchScan
from .baseline_manager import BaselineManager, Baseline
from .pattern_manager import PatternManager, SecretPattern
from .verification_engine import VerificationEngine, VerificationResult
from .remediation_guide import RemediationGuide, RemediationStep

__version__ = "1.0.0"
__all__ = [
    "SecretScanner",
    "SecretFinding",
    "ScanResult",
    "GitScanner",
    "CommitScan",
    "BranchScan",
    "BaselineManager",
    "Baseline",
    "PatternManager",
    "SecretPattern",
    "VerificationEngine",
    "VerificationResult",
    "RemediationGuide",
    "RemediationStep",
]
