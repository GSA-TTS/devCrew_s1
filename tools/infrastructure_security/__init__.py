"""
Infrastructure Security Scanner Platform.

Multi-functional security platform enabling container vulnerability detection,
IaC security scanning, policy-as-code validation, and cloud configuration
auditing. Supports automated security scanning with Trivy, Checkov, tfsec,
Terrascan, and OPA for comprehensive infrastructure security analysis.
"""

__version__ = "1.0.0"
__author__ = "devCrew_s1"

from .container_scanner import (
    ContainerScanner,
    ScanConfig,
    VulnerabilityResult,
    SBOMFormat,
)
from .iac_scanner import (
    IaCScanner,
    IaCType,
    ScannerType,
    IaCFinding,
)
from .policy_validator import (
    PolicyValidator,
    PolicyEngine,
    PolicyViolation,
    ComplianceFramework,
)
from .cloud_scanner import (
    CloudScanner,
    CloudProvider,
    CloudFinding,
    ServiceType,
)
from .report_aggregator import (
    ReportAggregator,
    ReportFormat,
    AggregatedReport,
    SARIFReport,
)
from .remediation_engine import (
    RemediationEngine,
    RemediationAction,
    AutoFixResult,
)

__all__ = [
    "ContainerScanner",
    "ScanConfig",
    "VulnerabilityResult",
    "SBOMFormat",
    "IaCScanner",
    "IaCType",
    "ScannerType",
    "IaCFinding",
    "PolicyValidator",
    "PolicyEngine",
    "PolicyViolation",
    "ComplianceFramework",
    "CloudScanner",
    "CloudProvider",
    "CloudFinding",
    "ServiceType",
    "ReportAggregator",
    "ReportFormat",
    "AggregatedReport",
    "SARIFReport",
    "RemediationEngine",
    "RemediationAction",
    "AutoFixResult",
]
