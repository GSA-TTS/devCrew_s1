"""
Software Composition Analysis (SCA) Scanner

A comprehensive dependency vulnerability scanning and software composition analysis
platform supporting multiple programming languages and protocols.
"""

__version__ = "1.0.0"
__author__ = "DevCrew Team"

from .dependency_scanner import DependencyScanner
from .vulnerability_matcher import VulnerabilityMatcher
from .license_checker import LicenseChecker
from .sbom_generator import SBOMGenerator
from .remediation_advisor import RemediationAdvisor
from .supply_chain_analyzer import SupplyChainAnalyzer

__all__ = [
    "DependencyScanner",
    "VulnerabilityMatcher",
    "LicenseChecker",
    "SBOMGenerator",
    "RemediationAdvisor",
    "SupplyChainAnalyzer",
]
