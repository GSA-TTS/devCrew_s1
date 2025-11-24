"""
Comprehensive test suite for Infrastructure Security Scanner Platform.

Tests cover all components with 85+ test functions:
- ContainerScanner (15 tests)
- IaCScanner (15 tests)
- PolicyValidator (15 tests)
- CloudScanner (15 tests)
- ReportAggregator (15 tests)
- RemediationEngine (15 tests)
- CLI (10 tests)

Author: devCrew Infrastructure Security Team
License: MIT
"""

import json
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List
from unittest.mock import ANY, MagicMock, Mock, call, mock_open, patch

import pytest
import responses
from click.testing import CliRunner

# Import modules under test
from .cloud_scanner import (
    AWS_AVAILABLE,
    AZURE_AVAILABLE,
    CloudConfig,
    CloudFinding,
    CloudProvider,
    CloudResult,
    CloudScanner,
    CloudScanError,
    CredentialsError,
    GCP_AVAILABLE,
    ServiceType,
    SeverityLevel as CloudSeverity,
)
from .container_scanner import (
    ContainerScanError,
    ContainerScanner,
    ImageNotFoundError,
    InvalidImageNameError,
    RegistryAuthError,
    SBOMFormat,
    ScanConfig,
    ScanTimeoutError,
    SeverityLevel,
    TrivyNotFoundError,
    Vulnerability,
    VulnerabilityResult,
    compare_scans,
    export_to_sarif,
    scan_images_batch,
)
from .iac_scanner import (
    ComplianceFramework,
    IaCConfig,
    IaCFinding,
    IaCResult,
    IaCScanner,
    IaCScanError,
    IaCType,
    InvalidIaCError,
    ScannerNotFoundError,
    ScannerType,
    SeverityLevel as IaCSeverity,
)
from .policy_validator import (
    ComplianceFramework as PolicyFramework,
    InvalidRegoError,
    OPANotFoundError,
    PolicyConfig,
    PolicyEngine,
    PolicyEvaluationError,
    PolicyLoadError,
    PolicyResult,
    PolicyValidationError,
    PolicyValidator,
    PolicyViolation,
    RegoPolicy,
    Severity,
)
from .remediation_engine import (
    AutoFixError,
    AutoFixResult,
    CodeChange,
    ComplianceDrift,
    PRCreationError,
    RemediationAction,
    RemediationConfig,
    RemediationEngine,
    RemediationError,
    RemediationPlaybook,
    RemediationStatus,
    RemediationType,
)
from .report_aggregator import (
    AggregatedReport,
    FindingSummary,
    GitHubUploadError,
    ReportAggregator,
    ReportConfig,
    ReportFormat,
    ReportGenerationError,
    SARIFGenerationError,
    SARIFReport,
    SecurityFinding,
    SeverityLevel as ReportSeverity,
    TrendData,
    TrendDirection,
)
from .security_cli import (
    EXIT_CONFIG_ERROR,
    EXIT_FINDINGS_FOUND,
    EXIT_SCAN_ERROR,
    EXIT_SUCCESS,
    EXIT_VALIDATION_FAILED,
    CLIConfig,
    cli,
)


# ============================================================================
# FIXTURES
# ============================================================================


@pytest.fixture
def mock_trivy_output() -> Dict[str, Any]:
    """Sample Trivy JSON output."""
    return {
        "Results": [
            {
                "Target": "nginx:latest",
                "Vulnerabilities": [
                    {
                        "VulnerabilityID": "CVE-2023-1234",
                        "Severity": "HIGH",
                        "Title": "SQL Injection",
                        "Description": "Critical SQL injection vulnerability",
                        "FixedVersion": "1.2.3",
                        "PkgName": "libssl",
                        "InstalledVersion": "1.0.0",
                        "CVSS": {"nvd": {"V3Score": 8.5}},
                        "CweIDs": ["CWE-89"],
                        "References": ["https://cve.mitre.org/CVE-2023-1234"],
                        "PublishedDate": "2023-01-01T00:00:00Z",
                    }
                ],
            }
        ]
    }


@pytest.fixture
def mock_vulnerability() -> Vulnerability:
    """Sample vulnerability data."""
    return Vulnerability(
        cve_id="CVE-2023-1234",
        severity=SeverityLevel.HIGH,
        title="SQL Injection",
        description="Critical SQL injection vulnerability",
        fixed_version="1.2.3",
        cvss_score=8.5,
        cwe_ids=["CWE-89"],
        published_date=datetime.now(timezone.utc),
        package_name="libssl",
        installed_version="1.0.0",
        references=["https://cve.mitre.org/CVE-2023-1234"],
    )


@pytest.fixture
def mock_checkov_output() -> Dict[str, Any]:
    """Sample Checkov JSON output."""
    return {
        "results": {
            "failed_checks": [
                {
                    "check_id": "CKV_AWS_19",
                    "check_name": "S3 Bucket Encryption",
                    "check_class": "HIGH",
                    "check_result": {"result": "S3 bucket not encrypted"},
                    "resource": "aws_s3_bucket.example",
                    "file_path": "terraform/s3.tf",
                    "file_line_range": [10, 20],
                    "guideline": "https://docs.bridgecrew.io/CKV_AWS_19",
                    "code_block": [["resource aws_s3_bucket"]],
                }
            ],
            "passed_checks": [],
        }
    }


@pytest.fixture
def mock_opa_output() -> Dict[str, Any]:
    """Sample OPA evaluation output."""
    return {
        "deny": [
            {
                "policy_id": "terraform_s3_encryption",
                "title": "S3 bucket must be encrypted",
                "severity": "high",
                "description": "S3 bucket does not have encryption enabled",
                "resource": "aws_s3_bucket.example",
                "rule": "s3_encryption_required",
                "remediation": "Enable S3 bucket encryption",
                "file": "terraform/s3.tf",
                "line": 10,
            }
        ],
        "passed_checks": 5,
    }


@pytest.fixture
def mock_security_finding() -> SecurityFinding:
    """Sample security finding."""
    return SecurityFinding(
        id="finding-001",
        title="SQL Injection Vulnerability",
        description="Critical SQL injection in login endpoint",
        severity=ReportSeverity.HIGH,
        scanner="trivy",
        rule_id="TRIVY-SQL-001",
        file_path="app/auth.py",
        line_number=42,
        code_snippet='password = request.form["password"]',
        remediation="Use parameterized queries",
        references=["https://owasp.org/sql-injection"],
        cwe_ids=["CWE-89"],
        cvss_score=8.5,
    )


@pytest.fixture
def temp_policy_dir(tmp_path: Path) -> Path:
    """Create temporary policy directory with sample Rego files."""
    policy_dir = tmp_path / "policies"
    policy_dir.mkdir()

    # Create sample Rego policy
    policy_file = policy_dir / "s3_encryption.rego"
    policy_content = """
package terraform.s3

default allow = false

allow {
    input.resource.aws_s3_bucket[_].server_side_encryption_configuration
}

deny[msg] {
    resource := input.resource.aws_s3_bucket[name]
    not resource.server_side_encryption_configuration
    msg := sprintf("S3 bucket %v must have encryption enabled", [name])
}
"""
    policy_file.write_text(policy_content)
    return policy_dir


@pytest.fixture
def temp_terraform_dir(tmp_path: Path) -> Path:
    """Create temporary directory with sample Terraform files."""
    tf_dir = tmp_path / "terraform"
    tf_dir.mkdir()

    # Create sample TF file
    tf_file = tf_dir / "main.tf"
    tf_content = """
resource "aws_s3_bucket" "example" {
  bucket = "my-bucket"
  acl    = "public-read"
}

resource "aws_security_group" "allow_all" {
  name = "allow_all"

  ingress {
    from_port   = 0
    to_port     = 65535
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
}
"""
    tf_file.write_text(tf_content)
    return tf_dir


# ============================================================================
# CONTAINER SCANNER TESTS
# ============================================================================


class TestContainerScanner:
    """Test suite for ContainerScanner component."""

    def test_scanner_initialization_success(self) -> None:
        """Test successful scanner initialization."""
        with patch("shutil.which", return_value="/usr/bin/trivy"):
            with patch(
                "subprocess.run",
                return_value=Mock(
                    returncode=0, stdout="Version: 0.48.0", stderr=""
                ),
            ):
                scanner = ContainerScanner()
                assert scanner.trivy_path == "/usr/bin/trivy"
                assert scanner.trivy_version is not None

    def test_scanner_initialization_trivy_not_found(self) -> None:
        """Test scanner initialization when Trivy not found."""
        with patch("shutil.which", return_value=None):
            with pytest.raises(TrivyNotFoundError, match="Trivy not found"):
                ContainerScanner()

    def test_check_trivy_installed_returns_true(self) -> None:
        """Test check_trivy_installed returns True when available."""
        with patch("shutil.which", return_value="/usr/bin/trivy"):
            assert ContainerScanner.check_trivy_installed() is True

    def test_check_trivy_installed_returns_false(self) -> None:
        """Test check_trivy_installed returns False when unavailable."""
        with patch("shutil.which", return_value=None):
            assert ContainerScanner.check_trivy_installed() is False

    def test_scan_image_success(self, mock_trivy_output: Dict) -> None:
        """Test successful image scanning."""
        with patch("shutil.which", return_value="/usr/bin/trivy"):
            with patch("subprocess.run") as mock_run:
                mock_run.side_effect = [
                    Mock(returncode=0, stdout="Version: 0.48.0", stderr=""),
                    Mock(
                        returncode=0,
                        stdout=json.dumps(mock_trivy_output),
                        stderr="",
                    ),
                ]

                scanner = ContainerScanner()
                result = scanner.scan_image("nginx:latest")

                assert result.image == "nginx:latest"
                assert result.total_count == 1
                assert result.high_count == 1
                assert len(result.vulnerabilities) == 1
                assert result.vulnerabilities[0].cve_id == "CVE-2023-1234"

    def test_scan_image_invalid_name(self) -> None:
        """Test scanning with invalid image name."""
        with patch("shutil.which", return_value="/usr/bin/trivy"):
            with patch("subprocess.run", return_value=Mock(stdout="Version: 0.48.0")):
                scanner = ContainerScanner()

                with pytest.raises(InvalidImageNameError):
                    scanner.scan_image("")

                with pytest.raises(InvalidImageNameError):
                    scanner.scan_image("image with spaces")

    def test_scan_image_not_found(self) -> None:
        """Test scanning when image cannot be found."""
        with patch("shutil.which", return_value="/usr/bin/trivy"):
            with patch("subprocess.run") as mock_run:
                mock_run.side_effect = [
                    Mock(returncode=0, stdout="Version: 0.48.0", stderr=""),
                    Mock(
                        returncode=1,
                        stdout="",
                        stderr="Error: manifest unknown",
                    ),
                ]

                scanner = ContainerScanner()
                with pytest.raises(ImageNotFoundError, match="Image not found"):
                    scanner.scan_image("nonexistent:latest")

    def test_scan_image_registry_auth_error(self) -> None:
        """Test scanning with registry authentication failure."""
        with patch("shutil.which", return_value="/usr/bin/trivy"):
            with patch("subprocess.run") as mock_run:
                mock_run.side_effect = [
                    Mock(returncode=0, stdout="Version: 0.48.0", stderr=""),
                    Mock(
                        returncode=1,
                        stdout="",
                        stderr="Error: unauthorized",
                    ),
                ]

                scanner = ContainerScanner()
                with pytest.raises(
                    RegistryAuthError, match="authentication failed"
                ):
                    scanner.scan_image("private/image:latest")

    def test_scan_image_timeout(self) -> None:
        """Test scanning with timeout."""
        import subprocess

        with patch("shutil.which", return_value="/usr/bin/trivy"):
            with patch("subprocess.run") as mock_run:
                mock_run.side_effect = [
                    Mock(returncode=0, stdout="Version: 0.48.0", stderr=""),
                    subprocess.TimeoutExpired("trivy", 600),
                ]

                scanner = ContainerScanner()
                with pytest.raises(ScanTimeoutError, match="timed out"):
                    scanner.scan_image("slow:image")

    def test_generate_sbom_spdx_success(self) -> None:
        """Test SBOM generation in SPDX format."""
        sbom_content = json.dumps(
            {
                "spdxVersion": "SPDX-2.3",
                "packages": [{"name": "nginx", "versionInfo": "1.21.0"}],
            }
        )

        with patch("shutil.which", return_value="/usr/bin/trivy"):
            with patch("subprocess.run") as mock_run:
                mock_run.side_effect = [
                    Mock(returncode=0, stdout="Version: 0.48.0", stderr=""),
                    Mock(returncode=0, stdout=sbom_content, stderr=""),
                ]

                scanner = ContainerScanner()
                sbom = scanner.generate_sbom("nginx:latest", SBOMFormat.SPDX_JSON)

                assert "spdxVersion" in sbom
                assert "packages" in sbom

    def test_generate_sbom_cyclonedx_success(self) -> None:
        """Test SBOM generation in CycloneDX format."""
        sbom_content = json.dumps(
            {
                "bomFormat": "CycloneDX",
                "specVersion": "1.4",
                "components": [{"name": "nginx", "version": "1.21.0"}],
            }
        )

        with patch("shutil.which", return_value="/usr/bin/trivy"):
            with patch("subprocess.run") as mock_run:
                mock_run.side_effect = [
                    Mock(returncode=0, stdout="Version: 0.48.0", stderr=""),
                    Mock(returncode=0, stdout=sbom_content, stderr=""),
                ]

                scanner = ContainerScanner()
                sbom = scanner.generate_sbom(
                    "nginx:latest", SBOMFormat.CYCLONEDX_JSON
                )

                assert "bomFormat" in sbom
                assert "components" in sbom

    def test_severity_filtering(self, mock_vulnerability: Vulnerability) -> None:
        """Test filtering vulnerabilities by severity."""
        with patch("shutil.which", return_value="/usr/bin/trivy"):
            with patch("subprocess.run", return_value=Mock(stdout="Version: 0.48.0")):
                scanner = ContainerScanner()

                vulns = [
                    mock_vulnerability,
                    Vulnerability(
                        cve_id="CVE-2023-5678",
                        severity=SeverityLevel.LOW,
                        title="Low severity",
                        description="Test",
                        package_name="test",
                        installed_version="1.0",
                    ),
                ]

                filtered = scanner.filter_by_severity(
                    vulns, [SeverityLevel.HIGH, SeverityLevel.CRITICAL]
                )

                assert len(filtered) == 1
                assert filtered[0].severity == SeverityLevel.HIGH

    def test_batch_scanning(self, mock_trivy_output: Dict) -> None:
        """Test scanning multiple images in batch."""
        with patch("shutil.which", return_value="/usr/bin/trivy"):
            with patch("subprocess.run") as mock_run:
                mock_run.side_effect = [
                    Mock(returncode=0, stdout="Version: 0.48.0", stderr=""),
                    Mock(
                        returncode=0,
                        stdout=json.dumps(mock_trivy_output),
                        stderr="",
                    ),
                    Mock(
                        returncode=0,
                        stdout=json.dumps(mock_trivy_output),
                        stderr="",
                    ),
                ]

                images = ["nginx:latest", "redis:alpine"]
                results = scan_images_batch(images)

                assert len(results) == 2
                assert "nginx:latest" in results
                assert "redis:alpine" in results

    def test_scan_comparison(
        self, mock_trivy_output: Dict, mock_vulnerability: Vulnerability
    ) -> None:
        """Test comparing two scan results."""
        result1 = VulnerabilityResult(
            image="nginx:1.20",
            vulnerabilities=[mock_vulnerability],
            total_count=1,
            high_count=1,
        )

        new_vuln = Vulnerability(
            cve_id="CVE-2023-9999",
            severity=SeverityLevel.CRITICAL,
            title="New vulnerability",
            description="Recently discovered",
            package_name="openssl",
            installed_version="1.1.1",
        )

        result2 = VulnerabilityResult(
            image="nginx:1.21",
            vulnerabilities=[new_vuln],
            total_count=1,
            critical_count=1,
        )

        new_vulns, fixed_vulns, persistent_vulns = compare_scans(result1, result2)

        assert len(new_vulns) == 1
        assert len(fixed_vulns) == 1
        assert len(persistent_vulns) == 0

    def test_export_to_sarif(self, mock_vulnerability: Vulnerability) -> None:
        """Test exporting scan results to SARIF format."""
        result = VulnerabilityResult(
            image="nginx:latest",
            vulnerabilities=[mock_vulnerability],
            total_count=1,
            high_count=1,
            trivy_version="0.48.0",
        )

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".sarif", delete=False
        ) as f:
            output_file = Path(f.name)

        try:
            export_to_sarif(result, output_file)

            assert output_file.exists()
            with open(output_file, "r") as f:
                sarif_data = json.load(f)

            assert sarif_data["version"] == "2.1.0"
            assert "runs" in sarif_data
            assert len(sarif_data["runs"][0]["results"]) == 1
        finally:
            output_file.unlink()

    def test_registry_authentication(self) -> None:
        """Test scanning with registry authentication."""
        from .container_scanner import RegistryAuth

        auth = RegistryAuth(
            username="testuser",
            password="testpass",
            registry_url="https://registry.example.com",
        )
        config = ScanConfig(registry_auth=auth)

        with patch("shutil.which", return_value="/usr/bin/trivy"):
            with patch("subprocess.run") as mock_run:
                mock_run.side_effect = [
                    Mock(returncode=0, stdout="Version: 0.48.0", stderr=""),
                    Mock(
                        returncode=0,
                        stdout=json.dumps({"Results": []}),
                        stderr="",
                    ),
                ]

                scanner = ContainerScanner(config)
                result = scanner.scan_image("private/image:latest")

                # Verify auth env vars were set in subprocess call
                call_env = mock_run.call_args_list[1][1]["env"]
                assert "TRIVY_USERNAME" in call_env
                assert call_env["TRIVY_USERNAME"] == "testuser"

    def test_scan_image_file(self) -> None:
        """Test scanning Docker image from tar file."""
        with tempfile.NamedTemporaryFile(suffix=".tar", delete=False) as f:
            image_file = Path(f.name)

        try:
            with patch("shutil.which", return_value="/usr/bin/trivy"):
                with patch("subprocess.run") as mock_run:
                    mock_run.side_effect = [
                        Mock(returncode=0, stdout="Version: 0.48.0", stderr=""),
                        Mock(
                            returncode=0,
                            stdout=json.dumps({"Results": []}),
                            stderr="",
                        ),
                    ]

                    scanner = ContainerScanner()
                    result = scanner.scan_image_file(image_file)

                    assert result.image == str(image_file)
        finally:
            image_file.unlink()


# ============================================================================
# IAC SCANNER TESTS
# ============================================================================


class TestIaCScanner:
    """Test suite for IaCScanner component."""

    def test_scanner_initialization_success(self) -> None:
        """Test successful IaC scanner initialization."""
        with patch("shutil.which", return_value="/usr/bin/checkov"):
            config = IaCConfig(scanners=[ScannerType.CHECKOV])
            scanner = IaCScanner(config)
            assert scanner.config.scanners == [ScannerType.CHECKOV]

    def test_scanner_initialization_missing_scanner(self) -> None:
        """Test initialization fails when scanner not found."""
        with patch("shutil.which", return_value=None):
            config = IaCConfig(scanners=[ScannerType.CHECKOV])
            with pytest.raises(ScannerNotFoundError, match="not found"):
                IaCScanner(config)

    def test_check_scanners_installed(self) -> None:
        """Test checking availability of all scanners."""
        with patch("shutil.which") as mock_which:
            mock_which.side_effect = (
                lambda x: "/usr/bin/" + x if x == "checkov" else None
            )

            status = IaCScanner.check_scanners_installed()

            assert status["checkov"] is True
            assert status["tfsec"] is False

    def test_scan_terraform_success(
        self, temp_terraform_dir: Path, mock_checkov_output: Dict
    ) -> None:
        """Test successful Terraform scanning."""
        with patch("shutil.which", return_value="/usr/bin/checkov"):
            with patch("subprocess.run") as mock_run:
                mock_run.return_value = Mock(
                    returncode=0,
                    stdout=json.dumps(mock_checkov_output),
                    stderr="",
                )

                config = IaCConfig(scanners=[ScannerType.CHECKOV])
                scanner = IaCScanner(config)
                result = scanner.scan_terraform(str(temp_terraform_dir))

                assert result.iac_type == IaCType.TERRAFORM
                assert result.failed_count > 0

    def test_scan_terraform_no_files(self, tmp_path: Path) -> None:
        """Test scanning directory with no Terraform files."""
        empty_dir = tmp_path / "empty"
        empty_dir.mkdir()

        with patch("shutil.which", return_value="/usr/bin/checkov"):
            config = IaCConfig(scanners=[ScannerType.CHECKOV])
            scanner = IaCScanner(config)

            with pytest.raises(InvalidIaCError, match="No Terraform files"):
                scanner.scan_terraform(str(empty_dir))

    def test_scan_cloudformation_success(self, tmp_path: Path) -> None:
        """Test successful CloudFormation scanning."""
        cf_file = tmp_path / "template.yaml"
        cf_content = """
Resources:
  MyBucket:
    Type: AWS::S3::Bucket
    Properties:
      BucketName: my-bucket
"""
        cf_file.write_text(cf_content)

        with patch("shutil.which", return_value="/usr/bin/checkov"):
            with patch("subprocess.run") as mock_run:
                mock_run.return_value = Mock(
                    returncode=0,
                    stdout=json.dumps({"results": {"failed_checks": []}}),
                    stderr="",
                )

                config = IaCConfig(scanners=[ScannerType.CHECKOV])
                scanner = IaCScanner(config)
                result = scanner.scan_cloudformation(str(cf_file))

                assert result.iac_type == IaCType.CLOUDFORMATION

    def test_scan_cloudformation_invalid_extension(self, tmp_path: Path) -> None:
        """Test scanning CloudFormation with invalid file extension."""
        bad_file = tmp_path / "template.txt"
        bad_file.write_text("test")

        with patch("shutil.which", return_value="/usr/bin/checkov"):
            config = IaCConfig(scanners=[ScannerType.CHECKOV])
            scanner = IaCScanner(config)

            with pytest.raises(InvalidIaCError, match="Invalid.*extension"):
                scanner.scan_cloudformation(str(bad_file))

    def test_scan_kubernetes_success(self, tmp_path: Path) -> None:
        """Test successful Kubernetes manifest scanning."""
        k8s_file = tmp_path / "deployment.yaml"
        k8s_content = """
apiVersion: apps/v1
kind: Deployment
metadata:
  name: nginx
spec:
  replicas: 3
"""
        k8s_file.write_text(k8s_content)

        with patch("shutil.which", return_value="/usr/bin/checkov"):
            with patch("subprocess.run") as mock_run:
                mock_run.return_value = Mock(
                    returncode=0,
                    stdout=json.dumps({"results": {"failed_checks": []}}),
                    stderr="",
                )

                config = IaCConfig(scanners=[ScannerType.CHECKOV])
                scanner = IaCScanner(config)
                result = scanner.scan_kubernetes(str(k8s_file))

                assert result.iac_type == IaCType.KUBERNETES

    def test_multiple_scanner_orchestration(
        self, temp_terraform_dir: Path
    ) -> None:
        """Test running multiple scanners in orchestration."""
        with patch("shutil.which", return_value="/usr/bin/scanner"):
            with patch("subprocess.run") as mock_run:
                mock_run.return_value = Mock(
                    returncode=0,
                    stdout=json.dumps({"results": {"failed_checks": []}}),
                    stderr="",
                )

                config = IaCConfig(
                    scanners=[ScannerType.CHECKOV, ScannerType.TFSEC]
                )
                scanner = IaCScanner(config)
                result = scanner.scan_terraform(str(temp_terraform_dir))

                # Both scanners should have been called
                assert mock_run.call_count >= 2

    def test_finding_deduplication(self) -> None:
        """Test deduplication of findings from multiple scanners."""
        findings = [
            IaCFinding(
                check_id="CKV_AWS_19",
                title="S3 Encryption",
                severity=IaCSeverity.HIGH,
                description="Test",
                resource="s3_bucket",
                file_path="main.tf",
                line_number=10,
                scanner=ScannerType.CHECKOV,
            ),
            IaCFinding(
                check_id="CKV_AWS_19",
                title="S3 Encryption",
                severity=IaCSeverity.HIGH,
                description="Test",
                resource="s3_bucket",
                file_path="main.tf",
                line_number=10,
                scanner=ScannerType.TFSEC,
            ),
        ]

        with patch("shutil.which", return_value="/usr/bin/checkov"):
            config = IaCConfig(scanners=[ScannerType.CHECKOV])
            scanner = IaCScanner(config)

            deduplicated = scanner._deduplicate_findings(findings)

            assert len(deduplicated) == 1

    def test_framework_mapping(self) -> None:
        """Test mapping findings to compliance frameworks."""
        with patch("shutil.which", return_value="/usr/bin/checkov"):
            config = IaCConfig(
                scanners=[ScannerType.CHECKOV],
                frameworks=[ComplianceFramework.CIS_AWS],
            )
            scanner = IaCScanner(config)

            frameworks = scanner._extract_frameworks(
                "CKV_AWS_19", "https://cisecurity.org"
            )

            assert ComplianceFramework.CIS_AWS in frameworks

    def test_secret_detection(self, tmp_path: Path) -> None:
        """Test secret detection in IaC files."""
        tf_file = tmp_path / "secrets.tf"
        tf_content = """
resource "aws_instance" "example" {
  ami = "ami-12345"
  instance_type = "t2.micro"

  environment_variables = {
    API_KEY = "hardcoded-secret-12345"
  }
}
"""
        tf_file.write_text(tf_content)

        with patch("shutil.which", return_value="/usr/bin/trivy"):
            with patch("subprocess.run") as mock_run:
                mock_run.return_value = Mock(
                    returncode=0,
                    stdout=json.dumps(
                        {
                            "Results": [
                                {
                                    "Secrets": [
                                        {
                                            "RuleID": "generic-api-key",
                                            "Title": "Generic API Key",
                                            "Match": "API_KEY",
                                            "StartLine": 6,
                                        }
                                    ]
                                }
                            ]
                        }
                    ),
                    stderr="",
                )

                config = IaCConfig(
                    scanners=[ScannerType.TRIVY], enable_secret_detection=True
                )
                scanner = IaCScanner(config)
                result = scanner.scan_terraform(str(tmp_path))

                # Should detect secret
                assert any(
                    "secret" in f.title.lower() for f in result.findings
                )

    def test_scanner_timeout(self, temp_terraform_dir: Path) -> None:
        """Test scanner timeout handling."""
        import subprocess

        with patch("shutil.which", return_value="/usr/bin/checkov"):
            with patch(
                "subprocess.run", side_effect=subprocess.TimeoutExpired("cmd", 10)
            ):
                config = IaCConfig(scanners=[ScannerType.CHECKOV], timeout=10)
                scanner = IaCScanner(config)

                with pytest.raises(IaCScanError, match="timed out"):
                    scanner.scan_terraform(str(temp_terraform_dir))

    def test_invalid_scanner_output(self, temp_terraform_dir: Path) -> None:
        """Test handling invalid JSON output from scanner."""
        with patch("shutil.which", return_value="/usr/bin/checkov"):
            with patch("subprocess.run") as mock_run:
                mock_run.return_value = Mock(
                    returncode=0,
                    stdout="Invalid JSON",
                    stderr="",
                )

                config = IaCConfig(scanners=[ScannerType.CHECKOV])
                scanner = IaCScanner(config)

                with pytest.raises(IaCScanError, match="parse.*output"):
                    scanner.scan_terraform(str(temp_terraform_dir))

    def test_severity_threshold_filtering(self) -> None:
        """Test filtering findings by minimum severity."""
        with patch("shutil.which", return_value="/usr/bin/checkov"):
            config = IaCConfig(
                scanners=[ScannerType.CHECKOV], min_severity=IaCSeverity.HIGH
            )
            scanner = IaCScanner(config)

            # Low severity should be filtered out
            assert not scanner._meets_severity_threshold(IaCSeverity.LOW)
            assert scanner._meets_severity_threshold(IaCSeverity.HIGH)

    def test_skip_checks_configuration(self, temp_terraform_dir: Path) -> None:
        """Test skipping specific checks."""
        with patch("shutil.which", return_value="/usr/bin/checkov"):
            with patch("subprocess.run") as mock_run:
                mock_run.return_value = Mock(
                    returncode=0,
                    stdout=json.dumps({"results": {"failed_checks": []}}),
                    stderr="",
                )

                config = IaCConfig(
                    scanners=[ScannerType.CHECKOV],
                    skip_checks=["CKV_AWS_19", "CKV_AWS_20"],
                )
                scanner = IaCScanner(config)
                scanner.scan_terraform(str(temp_terraform_dir))

                # Verify skip-check argument was passed
                cmd_args = mock_run.call_args[0][0]
                assert "--skip-check" in cmd_args


# ============================================================================
# POLICY VALIDATOR TESTS
# ============================================================================


class TestPolicyValidator:
    """Test suite for PolicyValidator component."""

    def test_validator_initialization_success(
        self, temp_policy_dir: Path
    ) -> None:
        """Test successful policy validator initialization."""
        with patch("shutil.which", return_value="/usr/bin/opa"):
            with patch("subprocess.run") as mock_run:
                mock_run.return_value = Mock(
                    returncode=0,
                    stdout="Version: 0.55.0",
                    stderr="",
                )

                config = PolicyConfig(
                    policy_path=str(temp_policy_dir), engine=PolicyEngine.OPA
                )
                validator = PolicyValidator(config)

                assert validator.config.policy_path == str(temp_policy_dir)

    def test_validator_initialization_opa_not_found(
        self, temp_policy_dir: Path
    ) -> None:
        """Test initialization fails when OPA not found."""
        with patch("shutil.which", return_value=None):
            config = PolicyConfig(
                policy_path=str(temp_policy_dir), engine=PolicyEngine.OPA
            )

            with pytest.raises(OPANotFoundError, match="OPA binary not found"):
                PolicyValidator(config)

    def test_check_opa_installed(self, temp_policy_dir: Path) -> None:
        """Test checking OPA installation."""
        with patch("shutil.which", return_value="/usr/bin/opa"):
            with patch("subprocess.run") as mock_run:
                mock_run.return_value = Mock(
                    returncode=0,
                    stdout="Version: 0.55.0",
                    stderr="",
                )

                config = PolicyConfig(
                    policy_path=str(temp_policy_dir), engine=PolicyEngine.OPA
                )
                validator = PolicyValidator(config)

                assert validator.check_opa_installed() is True

    def test_validate_opa_success(
        self, temp_policy_dir: Path, mock_opa_output: Dict
    ) -> None:
        """Test successful OPA policy validation."""
        with patch("shutil.which", return_value="/usr/bin/opa"):
            with patch("subprocess.run") as mock_run:
                mock_run.side_effect = [
                    Mock(returncode=0, stdout="Version: 0.55.0", stderr=""),
                    Mock(
                        returncode=0,
                        stdout=json.dumps(
                            {
                                "result": [
                                    {"expressions": [{"value": mock_opa_output}]}
                                ]
                            }
                        ),
                        stderr="",
                    ),
                ]

                config = PolicyConfig(
                    policy_path=str(temp_policy_dir), engine=PolicyEngine.OPA
                )
                validator = PolicyValidator(config)

                resources = {
                    "resource": {
                        "aws_s3_bucket": {
                            "example": {"bucket": "test", "encryption": False}
                        }
                    }
                }

                result = validator.validate_opa(resources, "terraform.s3")

                assert len(result.violations) > 0
                assert result.engine == PolicyEngine.OPA

    def test_validate_terraform_plan_success(
        self, temp_policy_dir: Path, tmp_path: Path
    ) -> None:
        """Test Terraform plan validation."""
        plan_file = tmp_path / "tfplan.json"
        plan_data = {
            "resource_changes": [
                {
                    "address": "aws_s3_bucket.example",
                    "type": "aws_s3_bucket",
                    "name": "example",
                    "change": {"after": {"bucket": "test"}},
                }
            ]
        }
        plan_file.write_text(json.dumps(plan_data))

        with patch("shutil.which", return_value="/usr/bin/opa"):
            with patch("subprocess.run") as mock_run:
                mock_run.side_effect = [
                    Mock(returncode=0, stdout="Version: 0.55.0", stderr=""),
                    Mock(
                        returncode=0,
                        stdout=json.dumps(
                            {
                                "result": [
                                    {
                                        "expressions": [
                                            {"value": {"deny": [], "passed_checks": 1}}
                                        ]
                                    }
                                ]
                            }
                        ),
                        stderr="",
                    ),
                ]

                config = PolicyConfig(
                    policy_path=str(temp_policy_dir), engine=PolicyEngine.OPA
                )
                validator = PolicyValidator(config)

                result = validator.validate_terraform_plan(
                    str(plan_file), "terraform.s3"
                )

                assert result.total_checks >= 0

    def test_validate_checkov_custom_policies(
        self, temp_policy_dir: Path, tmp_path: Path
    ) -> None:
        """Test validation with Checkov custom policies."""
        test_tf = tmp_path / "test.tf"
        test_tf.write_text(
            'resource "aws_s3_bucket" "test" { bucket = "test" }'
        )

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = Mock(
                returncode=0,
                stdout=json.dumps({"results": {"failed_checks": []}}),
                stderr="",
            )

            config = PolicyConfig(
                policy_path=str(temp_policy_dir), engine=PolicyEngine.CHECKOV
            )

            # Create validator without OPA dependency
            with patch.object(
                PolicyValidator, "_load_rego_policies", return_value=None
            ):
                with patch.object(
                    PolicyValidator, "check_opa_installed", return_value=False
                ):
                    validator = PolicyValidator(config)

                    result = validator.validate_checkov_custom(
                        str(tmp_path), [str(temp_policy_dir)]
                    )

                    assert result.engine == PolicyEngine.CHECKOV

    def test_evaluate_compliance_cis_aws(self, temp_policy_dir: Path) -> None:
        """Test CIS AWS compliance evaluation."""
        with patch("shutil.which", return_value="/usr/bin/opa"):
            with patch("subprocess.run") as mock_run:
                mock_run.return_value = Mock(
                    returncode=0,
                    stdout="Version: 0.55.0",
                    stderr="",
                )

                config = PolicyConfig(
                    policy_path=str(temp_policy_dir),
                    engine=PolicyEngine.CUSTOM,
                    frameworks=[PolicyFramework.CIS_AWS],
                )

                with patch.object(
                    PolicyValidator, "_load_rego_policies", return_value=None
                ):
                    validator = PolicyValidator(config)

                    resources = {
                        "iam_users": [
                            {
                                "name": "root",
                                "last_used": "2023-01-01",
                                "arn": "arn:aws:iam::123:root",
                            }
                        ],
                        "cloudtrails": [],
                    }

                    result = validator.evaluate_compliance(
                        resources, PolicyFramework.CIS_AWS
                    )

                    assert result.total_checks > 0
                    # Root account usage should be detected
                    assert len(result.violations) > 0

    def test_compliance_score_calculation(self, temp_policy_dir: Path) -> None:
        """Test compliance score calculation."""
        with patch("shutil.which", return_value="/usr/bin/opa"):
            with patch("subprocess.run", return_value=Mock(stdout="Version: 0.55.0")):
                config = PolicyConfig(
                    policy_path=str(temp_policy_dir), engine=PolicyEngine.OPA
                )

                with patch.object(
                    PolicyValidator, "_load_rego_policies", return_value=None
                ):
                    validator = PolicyValidator(config)

                    result = PolicyResult(
                        violations=[
                            PolicyViolation(
                                policy_id="test",
                                title="Test",
                                severity=Severity.CRITICAL,
                                description="Test",
                                resource="test",
                                violated_rule="test",
                                remediation="Fix it",
                            )
                        ],
                        passed_checks=9,
                        total_checks=10,
                    )

                    score = validator._calculate_compliance_score(result)

                    assert 0 <= score <= 100
                    assert score < 100  # Has violations

    def test_policy_violation_parsing(self, temp_policy_dir: Path) -> None:
        """Test parsing policy violations from OPA output."""
        with patch("shutil.which", return_value="/usr/bin/opa"):
            with patch("subprocess.run", return_value=Mock(stdout="Version: 0.55.0")):
                config = PolicyConfig(
                    policy_path=str(temp_policy_dir), engine=PolicyEngine.OPA
                )

                with patch.object(
                    PolicyValidator, "_load_rego_policies", return_value=None
                ):
                    validator = PolicyValidator(config)

                    opa_output = {
                        "deny": [
                            {
                                "policy_id": "test_policy",
                                "title": "Test Violation",
                                "severity": "high",
                                "description": "Test description",
                                "resource": "aws_s3_bucket.test",
                                "rule": "encryption_required",
                                "remediation": "Enable encryption",
                            }
                        ]
                    }

                    violations = validator._parse_opa_output(opa_output)

                    assert len(violations) == 1
                    assert violations[0].severity == Severity.HIGH

    def test_rego_policy_loading(self, temp_policy_dir: Path) -> None:
        """Test loading Rego policy files."""
        with patch("shutil.which", return_value="/usr/bin/opa"):
            with patch("subprocess.run", return_value=Mock(stdout="Version: 0.55.0")):
                config = PolicyConfig(
                    policy_path=str(temp_policy_dir), engine=PolicyEngine.OPA
                )
                validator = PolicyValidator(config)

                assert len(validator._policies) > 0

    def test_invalid_rego_syntax(self, tmp_path: Path) -> None:
        """Test handling invalid Rego syntax."""
        bad_policy = tmp_path / "bad.rego"
        bad_policy.write_text("package test\n\ninvalid syntax here!")

        with patch("shutil.which", return_value="/usr/bin/opa"):
            with patch("subprocess.run", return_value=Mock(stdout="Version: 0.55.0")):
                config = PolicyConfig(policy_path=str(tmp_path), engine=PolicyEngine.OPA)

                with pytest.raises(PolicyLoadError):
                    PolicyValidator(config)

    def test_opa_evaluation_timeout(self, temp_policy_dir: Path) -> None:
        """Test OPA evaluation timeout handling."""
        import subprocess

        with patch("shutil.which", return_value="/usr/bin/opa"):
            with patch("subprocess.run") as mock_run:
                mock_run.side_effect = [
                    Mock(returncode=0, stdout="Version: 0.55.0", stderr=""),
                    subprocess.TimeoutExpired("opa", 10),
                ]

                config = PolicyConfig(
                    policy_path=str(temp_policy_dir),
                    engine=PolicyEngine.OPA,
                    timeout=10,
                )
                validator = PolicyValidator(config)

                with pytest.raises(PolicyEvaluationError, match="timed out"):
                    validator.validate_opa({}, "test.policy")

    def test_framework_mapping_nist(self, temp_policy_dir: Path) -> None:
        """Test NIST 800-53 framework compliance mapping."""
        with patch("shutil.which", return_value="/usr/bin/opa"):
            with patch("subprocess.run", return_value=Mock(stdout="Version: 0.55.0")):
                config = PolicyConfig(
                    policy_path=str(temp_policy_dir),
                    engine=PolicyEngine.CUSTOM,
                    frameworks=[PolicyFramework.NIST_800_53],
                )

                with patch.object(
                    PolicyValidator, "_load_rego_policies", return_value=None
                ):
                    validator = PolicyValidator(config)

                    resources = {"cloudtrails": []}

                    result = validator.evaluate_compliance(
                        resources, PolicyFramework.NIST_800_53
                    )

                    assert result.total_checks > 0

    def test_framework_mapping_pci_dss(self, temp_policy_dir: Path) -> None:
        """Test PCI-DSS compliance mapping."""
        with patch("shutil.which", return_value="/usr/bin/opa"):
            with patch("subprocess.run", return_value=Mock(stdout="Version: 0.55.0")):
                config = PolicyConfig(
                    policy_path=str(temp_policy_dir),
                    engine=PolicyEngine.CUSTOM,
                    frameworks=[PolicyFramework.PCI_DSS],
                )

                with patch.object(
                    PolicyValidator, "_load_rego_policies", return_value=None
                ):
                    validator = PolicyValidator(config)

                    resources = {}

                    result = validator.evaluate_compliance(
                        resources, PolicyFramework.PCI_DSS
                    )

                    assert result.total_checks > 0

    def test_checkov_output_parsing(self) -> None:
        """Test parsing Checkov JSON output."""
        checkov_output = json.dumps(
            {
                "results": {
                    "failed_checks": [
                        {
                            "check_id": "CKV_AWS_19",
                            "check_name": "S3 Encryption",
                            "severity": "HIGH",
                            "description": "S3 bucket not encrypted",
                            "resource": "aws_s3_bucket.test",
                            "file_path": "main.tf",
                            "file_line_range": [10, 20],
                            "check_class": "checkov.terraform",
                            "guideline": "https://docs.bridgecrew.io",
                        }
                    ]
                }
            }
        )

        with patch("shutil.which", return_value="/usr/bin/checkov"):
            config = PolicyConfig(policy_path="/tmp", engine=PolicyEngine.CHECKOV)

            with patch.object(PolicyValidator, "check_opa_installed", return_value=False):
                with patch.object(
                    PolicyValidator, "_load_rego_policies", return_value=None
                ):
                    validator = PolicyValidator(config)
                    violations = validator._parse_checkov_output(checkov_output)

                    assert len(violations) == 1
                    assert violations[0].severity == Severity.HIGH


# ============================================================================
# CLOUD SCANNER TESTS
# ============================================================================


@pytest.mark.skipif(not AWS_AVAILABLE, reason="AWS SDK not available")
class TestCloudScanner:
    """Test suite for CloudScanner component."""

    def test_scanner_initialization_aws(self) -> None:
        """Test AWS scanner initialization."""
        from .cloud_scanner import AWSCredentials

        creds = AWSCredentials(
            access_key_id="AKIATEST",
            secret_access_key="secret",
            profile="default",
        )
        config = CloudConfig(
            provider=CloudProvider.AWS, aws_credentials=creds, region="us-east-1"
        )

        with patch("boto3.Session") as mock_session:
            mock_sts = Mock()
            mock_sts.get_caller_identity.return_value = {"Account": "123456789012"}
            mock_session.return_value.client.return_value = mock_sts

            scanner = CloudScanner(config)

            assert scanner.config.provider == CloudProvider.AWS

    def test_scan_aws_s3_buckets(self) -> None:
        """Test scanning AWS S3 buckets."""
        from .cloud_scanner import AWSCredentials

        creds = AWSCredentials(profile="default")
        config = CloudConfig(
            provider=CloudProvider.AWS,
            aws_credentials=creds,
            services=[ServiceType.S3],
        )

        with patch("boto3.Session") as mock_session:
            mock_s3 = Mock()
            mock_s3.list_buckets.return_value = {
                "Buckets": [{"Name": "test-bucket"}]
            }
            mock_s3.get_bucket_acl.return_value = {
                "Grants": [
                    {
                        "Grantee": {
                            "Type": "Group",
                            "URI": "http://acs.amazonaws.com/groups/global/AllUsers",
                        }
                    }
                ]
            }

            mock_sts = Mock()
            mock_sts.get_caller_identity.return_value = {"Account": "123"}

            def client_selector(service_name: str) -> Mock:
                if service_name == "s3":
                    return mock_s3
                return mock_sts

            mock_session.return_value.client.side_effect = client_selector

            scanner = CloudScanner(config)
            result = scanner.scan_aws()

            assert result.provider == CloudProvider.AWS
            assert result.total_findings > 0
            assert any(
                "public" in f.title.lower() for f in result.findings
            )

    def test_scan_aws_security_groups(self) -> None:
        """Test scanning AWS security groups for open ports."""
        from .cloud_scanner import AWSCredentials

        creds = AWSCredentials(profile="default")
        config = CloudConfig(
            provider=CloudProvider.AWS,
            aws_credentials=creds,
            services=[ServiceType.SECURITY_GROUPS],
        )

        with patch("boto3.Session") as mock_session:
            mock_ec2 = Mock()
            mock_ec2.describe_security_groups.return_value = {
                "SecurityGroups": [
                    {
                        "GroupId": "sg-12345",
                        "GroupName": "allow_all",
                        "IpPermissions": [
                            {
                                "FromPort": 22,
                                "ToPort": 22,
                                "IpRanges": [{"CidrIp": "0.0.0.0/0"}],
                            }
                        ],
                    }
                ]
            }

            mock_sts = Mock()
            mock_sts.get_caller_identity.return_value = {"Account": "123"}

            def client_selector(service_name: str) -> Mock:
                if service_name == "ec2":
                    return mock_ec2
                return mock_sts

            mock_session.return_value.client.side_effect = client_selector

            scanner = CloudScanner(config)
            result = scanner.scan_aws()

            assert any("0.0.0.0/0" in f.description for f in result.findings)

    def test_scan_aws_iam_users(self) -> None:
        """Test scanning AWS IAM users for MFA."""
        from .cloud_scanner import AWSCredentials

        creds = AWSCredentials(profile="default")
        config = CloudConfig(
            provider=CloudProvider.AWS,
            aws_credentials=creds,
            services=[ServiceType.IAM],
        )

        with patch("boto3.Session") as mock_session:
            mock_iam = Mock()
            mock_iam.generate_credential_report.return_value = {
                "State": "COMPLETE"
            }
            mock_iam.get_credential_report.return_value = {
                "Content": b"user,mfa_active\ntestuser,false\n"
            }
            mock_iam.list_users.return_value = {
                "Users": [{"UserName": "testuser"}]
            }
            mock_iam.list_mfa_devices.return_value = {"MFADevices": []}

            mock_sts = Mock()
            mock_sts.get_caller_identity.return_value = {"Account": "123"}

            def client_selector(service_name: str) -> Mock:
                if service_name == "iam":
                    return mock_iam
                return mock_sts

            mock_session.return_value.client.side_effect = client_selector

            scanner = CloudScanner(config)
            result = scanner.scan_aws()

            assert any("mfa" in f.title.lower() for f in result.findings)

    def test_credential_validation_aws(self) -> None:
        """Test AWS credential validation."""
        from .cloud_scanner import AWSCredentials

        creds = AWSCredentials(
            access_key_id="INVALID", secret_access_key="invalid"
        )
        config = CloudConfig(provider=CloudProvider.AWS, aws_credentials=creds)

        with patch("boto3.Session") as mock_session:
            mock_sts = Mock()
            mock_sts.get_caller_identity.side_effect = Exception("Invalid credentials")
            mock_session.return_value.client.return_value = mock_sts

            with pytest.raises(CredentialsError):
                CloudScanner(config)

    @pytest.mark.skipif(not AZURE_AVAILABLE, reason="Azure SDK not available")
    def test_scan_azure_storage(self) -> None:
        """Test scanning Azure storage accounts."""
        from .cloud_scanner import AzureCredentials

        creds = AzureCredentials(subscription_id="test-sub-id")
        config = CloudConfig(
            provider=CloudProvider.AZURE,
            azure_credentials=creds,
            services=[ServiceType.STORAGE],
        )

        with patch("azure.identity.DefaultAzureCredential"):
            with patch(
                "azure.mgmt.storage.StorageManagementClient"
            ) as mock_storage:
                mock_account = Mock()
                mock_account.name = "teststorage"
                mock_account.enable_https_traffic_only = False
                mock_account.encryption.services.blob.enabled = False
                mock_account.allow_blob_public_access = True

                mock_storage.return_value.storage_accounts.list.return_value = [
                    mock_account
                ]

                scanner = CloudScanner(config)
                result = scanner.scan_azure()

                assert result.provider == CloudProvider.AZURE
                assert len(result.findings) > 0

    @pytest.mark.skipif(not GCP_AVAILABLE, reason="GCP SDK not available")
    def test_scan_gcp_storage(self) -> None:
        """Test scanning GCP Cloud Storage buckets."""
        from .cloud_scanner import GCPCredentials

        creds = GCPCredentials(project_id="test-project")
        config = CloudConfig(
            provider=CloudProvider.GCP,
            gcp_credentials=creds,
            services=[ServiceType.CLOUD_STORAGE],
        )

        with patch("google.cloud.storage.Client") as mock_storage:
            mock_bucket = Mock()
            mock_bucket.name = "test-bucket"
            mock_bucket.versioning_enabled = False

            mock_policy = Mock()
            mock_policy.bindings = [{"members": ["allUsers"], "role": "roles/viewer"}]
            mock_bucket.get_iam_policy.return_value = mock_policy

            mock_iam_config = Mock()
            mock_iam_config.uniform_bucket_level_access_enabled = False
            mock_bucket.iam_configuration = mock_iam_config

            mock_storage.return_value.list_buckets.return_value = [mock_bucket]

            scanner = CloudScanner(config)
            result = scanner.scan_gcp()

            assert result.provider == CloudProvider.GCP
            assert any("public" in f.title.lower() for f in result.findings)

    def test_multi_cloud_scanning(self) -> None:
        """Test scanning multiple cloud providers."""
        config = CloudConfig(provider=CloudProvider.MULTI)

        with patch("boto3.Session"):
            with patch.object(CloudScanner, "scan_aws", return_value=CloudResult(
                findings=[], total_resources=0, total_findings=0,
                critical_count=0, high_count=0, medium_count=0, low_count=0,
                provider=CloudProvider.AWS
            )):
                scanner = CloudScanner(config)
                result = scanner.scan_all()

                assert result.provider == CloudProvider.MULTI

    def test_scan_aws_ec2_instances(self) -> None:
        """Test scanning AWS EC2 instances."""
        from .cloud_scanner import AWSCredentials

        creds = AWSCredentials(profile="default")
        config = CloudConfig(
            provider=CloudProvider.AWS,
            aws_credentials=creds,
            services=[ServiceType.EC2],
        )

        with patch("boto3.Session") as mock_session:
            mock_ec2 = Mock()
            mock_ec2.describe_instances.return_value = {
                "Reservations": [
                    {
                        "Instances": [
                            {
                                "InstanceId": "i-12345",
                                "PublicIpAddress": "1.2.3.4",
                                "MetadataOptions": {"HttpTokens": "optional"},
                                "Monitoring": {"State": "disabled"},
                            }
                        ]
                    }
                ]
            }

            mock_sts = Mock()
            mock_sts.get_caller_identity.return_value = {"Account": "123"}

            def client_selector(service_name: str) -> Mock:
                if service_name == "ec2":
                    return mock_ec2
                return mock_sts

            mock_session.return_value.client.side_effect = client_selector

            scanner = CloudScanner(config)
            result = scanner.scan_aws()

            assert any("imdsv2" in f.title.lower() for f in result.findings)

    def test_scan_aws_rds_instances(self) -> None:
        """Test scanning AWS RDS instances."""
        from .cloud_scanner import AWSCredentials

        creds = AWSCredentials(profile="default")
        config = CloudConfig(
            provider=CloudProvider.AWS,
            aws_credentials=creds,
            services=[ServiceType.RDS],
        )

        with patch("boto3.Session") as mock_session:
            mock_rds = Mock()
            mock_rds.describe_db_instances.return_value = {
                "DBInstances": [
                    {
                        "DBInstanceIdentifier": "db-1",
                        "PubliclyAccessible": True,
                        "StorageEncrypted": False,
                        "BackupRetentionPeriod": 0,
                    }
                ]
            }

            mock_sts = Mock()
            mock_sts.get_caller_identity.return_value = {"Account": "123"}

            def client_selector(service_name: str) -> Mock:
                if service_name == "rds":
                    return mock_rds
                return mock_sts

            mock_session.return_value.client.side_effect = client_selector

            scanner = CloudScanner(config)
            result = scanner.scan_aws()

            assert any("public" in f.title.lower() for f in result.findings)
            assert any("encrypt" in f.title.lower() for f in result.findings)

    def test_api_error_handling(self) -> None:
        """Test handling API errors during cloud scans."""
        from .cloud_scanner import AWSCredentials

        creds = AWSCredentials(profile="default")
        config = CloudConfig(
            provider=CloudProvider.AWS,
            aws_credentials=creds,
            services=[ServiceType.S3],
        )

        with patch("boto3.Session") as mock_session:
            mock_s3 = Mock()
            mock_s3.list_buckets.side_effect = Exception("API Error")

            mock_sts = Mock()
            mock_sts.get_caller_identity.return_value = {"Account": "123"}

            def client_selector(service_name: str) -> Mock:
                if service_name == "s3":
                    return mock_s3
                return mock_sts

            mock_session.return_value.client.side_effect = client_selector

            scanner = CloudScanner(config)

            # Should handle error gracefully
            result = scanner.scan_aws()
            assert "error" in result.service_results.get("s3", {})

    def test_export_findings_to_json(self, tmp_path: Path) -> None:
        """Test exporting cloud scan findings to JSON."""
        result = CloudResult(
            findings=[],
            total_resources=10,
            total_findings=5,
            critical_count=1,
            high_count=2,
            medium_count=2,
            low_count=0,
            provider=CloudProvider.AWS,
            region="us-east-1",
        )

        output_file = tmp_path / "findings.json"

        from .cloud_scanner import AWSCredentials

        creds = AWSCredentials(profile="default")
        config = CloudConfig(provider=CloudProvider.AWS, aws_credentials=creds)

        with patch("boto3.Session") as mock_session:
            mock_sts = Mock()
            mock_sts.get_caller_identity.return_value = {"Account": "123"}
            mock_session.return_value.client.return_value = mock_sts

            scanner = CloudScanner(config)
            scanner.export_findings(result, output_file)

            assert output_file.exists()
            data = json.loads(output_file.read_text())
            assert data["summary"]["total_findings"] == 5


# ============================================================================
# REPORT AGGREGATOR TESTS
# ============================================================================


class TestReportAggregator:
    """Test suite for ReportAggregator component."""

    def test_aggregator_initialization(self) -> None:
        """Test report aggregator initialization."""
        config = ReportConfig(output_dir=Path("./reports"))
        aggregator = ReportAggregator(config)

        assert aggregator.config.output_dir.exists()

    def test_aggregate_results_success(
        self, mock_security_finding: SecurityFinding
    ) -> None:
        """Test successful result aggregation."""
        aggregator = ReportAggregator()

        results = [
            {
                "scanner": "trivy",
                "findings": [
                    {
                        "id": "001",
                        "title": "SQL Injection",
                        "description": "Test",
                        "severity": "high",
                        "rule_id": "TRIVY-001",
                    }
                ],
            }
        ]

        report = aggregator.aggregate(results)

        assert report.summary.total_count > 0
        assert len(report.findings) > 0

    def test_finding_deduplication(self) -> None:
        """Test deduplication of findings."""
        aggregator = ReportAggregator()

        findings = [
            SecurityFinding(
                id="001",
                title="Test Finding",
                description="Test",
                severity=ReportSeverity.HIGH,
                scanner="trivy",
                rule_id="TEST-001",
                file_path="test.py",
                line_number=10,
            ),
            SecurityFinding(
                id="002",
                title="Test Finding",
                description="Test",
                severity=ReportSeverity.HIGH,
                scanner="checkov",
                rule_id="TEST-001",
                file_path="test.py",
                line_number=10,
            ),
        ]

        deduplicated = aggregator.deduplicate_findings(findings)

        assert len(deduplicated) == 1

    def test_finding_prioritization(self) -> None:
        """Test prioritization of findings by severity."""
        aggregator = ReportAggregator()

        findings = [
            SecurityFinding(
                id="001",
                title="Low",
                description="Test",
                severity=ReportSeverity.LOW,
                scanner="test",
                rule_id="001",
            ),
            SecurityFinding(
                id="002",
                title="Critical",
                description="Test",
                severity=ReportSeverity.CRITICAL,
                scanner="test",
                rule_id="002",
            ),
            SecurityFinding(
                id="003",
                title="High",
                description="Test",
                severity=ReportSeverity.HIGH,
                scanner="test",
                rule_id="003",
            ),
        ]

        prioritized = aggregator.prioritize_findings(findings)

        assert prioritized[0].severity == ReportSeverity.CRITICAL
        assert prioritized[-1].severity == ReportSeverity.LOW

    def test_calculate_summary(self) -> None:
        """Test calculating findings summary."""
        aggregator = ReportAggregator()

        findings = [
            SecurityFinding(
                id="001",
                title="Critical",
                description="Test",
                severity=ReportSeverity.CRITICAL,
                scanner="test",
                rule_id="001",
                file_path="test1.py",
            ),
            SecurityFinding(
                id="002",
                title="High",
                description="Test",
                severity=ReportSeverity.HIGH,
                scanner="test",
                rule_id="002",
                file_path="test2.py",
            ),
        ]

        summary = aggregator.calculate_summary(findings)

        assert summary.total_count == 2
        assert summary.critical_count == 1
        assert summary.high_count == 1
        assert summary.unique_files_affected == 2

    def test_generate_sarif_success(
        self, mock_security_finding: SecurityFinding
    ) -> None:
        """Test SARIF report generation."""
        aggregator = ReportAggregator()

        findings = [mock_security_finding]
        sarif = aggregator.generate_sarif(findings, "test-scanner")

        assert sarif.version == "2.1.0"
        assert len(sarif.runs) == 1
        assert len(sarif.runs[0].results) == 1

    def test_generate_json_success(self) -> None:
        """Test JSON report generation."""
        aggregator = ReportAggregator()

        report = AggregatedReport(
            findings=[],
            summary=FindingSummary(total_count=0),
        )

        json_output = aggregator.generate_json(report)

        assert json_output
        data = json.loads(json_output)
        assert "findings" in data

    def test_generate_html_success(self) -> None:
        """Test HTML report generation."""
        aggregator = ReportAggregator()

        report = AggregatedReport(
            findings=[],
            summary=FindingSummary(total_count=0),
        )

        html_output = aggregator.generate_html(report)

        assert "<!DOCTYPE html>" in html_output
        assert "Security Scan Report" in html_output

    def test_generate_markdown_success(self) -> None:
        """Test Markdown report generation."""
        aggregator = ReportAggregator()

        report = AggregatedReport(
            findings=[],
            summary=FindingSummary(total_count=0),
        )

        md_output = aggregator.generate_markdown(report)

        assert "# Security Scan Report" in md_output
        assert "## Summary" in md_output

    def test_compare_scans_for_trends(self) -> None:
        """Test comparing scans for trend analysis."""
        aggregator = ReportAggregator()

        old_finding = SecurityFinding(
            id="001",
            title="Old",
            description="Test",
            severity=ReportSeverity.HIGH,
            scanner="test",
            rule_id="OLD-001",
        )

        new_finding = SecurityFinding(
            id="002",
            title="New",
            description="Test",
            severity=ReportSeverity.CRITICAL,
            scanner="test",
            rule_id="NEW-001",
        )

        current = AggregatedReport(
            findings=[new_finding],
            summary=FindingSummary(total_count=1, critical_count=1),
        )

        previous = AggregatedReport(
            findings=[old_finding],
            summary=FindingSummary(total_count=1, high_count=1),
        )

        trend = aggregator.compare_scans(current, previous)

        assert trend.new_findings == 1
        assert trend.fixed_findings == 1
        assert trend.trend_direction == TrendDirection.STABLE

    @responses.activate
    def test_upload_to_github_success(self) -> None:
        """Test uploading SARIF to GitHub."""
        responses.add(
            responses.POST,
            "https://api.github.com/repos/owner/repo/code-scanning/sarifs",
            json={"id": "123"},
            status=202,
        )

        config = ReportConfig(github_token="test-token")
        aggregator = ReportAggregator(config)

        sarif = SARIFReport(runs=[])

        result = aggregator.upload_to_github(
            sarif, "owner/repo", "refs/heads/main", "abc123"
        )

        assert result is True

    @responses.activate
    def test_upload_to_github_failure(self) -> None:
        """Test GitHub upload failure."""
        responses.add(
            responses.POST,
            "https://api.github.com/repos/owner/repo/code-scanning/sarifs",
            json={"error": "Unauthorized"},
            status=401,
        )

        config = ReportConfig(github_token="invalid-token")
        aggregator = ReportAggregator(config)

        sarif = SARIFReport(runs=[])

        with pytest.raises(GitHubUploadError):
            aggregator.upload_to_github(
                sarif, "owner/repo", "refs/heads/main", "abc123"
            )

    def test_save_report_sarif(self, tmp_path: Path) -> None:
        """Test saving report in SARIF format."""
        config = ReportConfig(output_dir=tmp_path)
        aggregator = ReportAggregator(config)

        report = AggregatedReport(
            findings=[],
            summary=FindingSummary(total_count=0),
        )

        output_path = aggregator.save_report(
            report, ReportFormat.SARIF, "test.sarif"
        )

        assert output_path.exists()
        assert output_path.suffix == ".sarif"

    def test_save_report_json(self, tmp_path: Path) -> None:
        """Test saving report in JSON format."""
        config = ReportConfig(output_dir=tmp_path)
        aggregator = ReportAggregator(config)

        report = AggregatedReport(
            findings=[],
            summary=FindingSummary(total_count=0),
        )

        output_path = aggregator.save_report(
            report, ReportFormat.JSON, "test.json"
        )

        assert output_path.exists()
        data = json.loads(output_path.read_text())
        assert "findings" in data

    def test_save_report_html(self, tmp_path: Path) -> None:
        """Test saving report in HTML format."""
        config = ReportConfig(output_dir=tmp_path)
        aggregator = ReportAggregator(config)

        report = AggregatedReport(
            findings=[],
            summary=FindingSummary(total_count=0),
        )

        output_path = aggregator.save_report(
            report, ReportFormat.HTML, "test.html"
        )

        assert output_path.exists()
        assert "html" in output_path.read_text().lower()

    def test_save_report_markdown(self, tmp_path: Path) -> None:
        """Test saving report in Markdown format."""
        config = ReportConfig(output_dir=tmp_path)
        aggregator = ReportAggregator(config)

        report = AggregatedReport(
            findings=[],
            summary=FindingSummary(total_count=0),
        )

        output_path = aggregator.save_report(
            report, ReportFormat.MARKDOWN, "test.md"
        )

        assert output_path.exists()
        assert "#" in output_path.read_text()


# ============================================================================
# REMEDIATION ENGINE TESTS
# ============================================================================


class TestRemediationEngine:
    """Test suite for RemediationEngine component."""

    def test_engine_initialization(self, tmp_path: Path) -> None:
        """Test remediation engine initialization."""
        config = RemediationConfig(backup_dir=tmp_path / "backups")
        engine = RemediationEngine(config)

        assert engine.config.backup_dir.exists()

    def test_generate_remediation_hardcoded_secret(self) -> None:
        """Test remediation generation for hardcoded secrets."""
        config = RemediationConfig()
        engine = RemediationEngine(config)

        finding = {
            "id": "001",
            "title": "Hardcoded API Key",
            "description": "API key found in code",
            "severity": "critical",
            "file": "app.py",
            "line": 10,
            "code_snippet": 'api_key = "secret123"',
        }

        action = engine.generate_remediation(finding)

        assert action.remediation_type == RemediationType.AUTO_FIX
        assert len(action.code_changes) > 0
        assert "environment variable" in action.description.lower()

    def test_generate_remediation_open_security_group(self) -> None:
        """Test remediation for open security groups."""
        config = RemediationConfig()
        engine = RemediationEngine(config)

        finding = {
            "id": "002",
            "title": "Open Security Group",
            "description": "Security group allows 0.0.0.0/0",
            "severity": "high",
            "file": "main.tf",
            "line": 20,
            "code_snippet": 'cidr_blocks = ["0.0.0.0/0"]',
        }

        action = engine.generate_remediation(finding)

        assert action.remediation_type == RemediationType.AUTO_FIX
        assert "0.0.0.0/0" not in action.code_changes[0].fixed_code

    def test_generate_remediation_weak_encryption(self) -> None:
        """Test remediation for weak encryption."""
        config = RemediationConfig()
        engine = RemediationEngine(config)

        finding = {
            "id": "003",
            "title": "Weak Encryption Algorithm",
            "description": "MD5 algorithm detected",
            "severity": "high",
            "file": "config.py",
            "line": 15,
            "code_snippet": 'algorithm = "MD5"',
        }

        action = engine.generate_remediation(finding)

        assert action.remediation_type == RemediationType.AUTO_FIX
        assert "SHA256" in action.code_changes[0].fixed_code

    def test_apply_auto_fix_success(self, tmp_path: Path) -> None:
        """Test successful auto-fix application."""
        config = RemediationConfig(
            backup_dir=tmp_path / "backups",
            dry_run=False,
            backup_enabled=True,
        )
        engine = RemediationEngine(config)

        test_file = tmp_path / "test.py"
        test_file.write_text('api_key = "secret123"')

        action = RemediationAction(
            finding_id="001",
            remediation_type=RemediationType.AUTO_FIX,
            description="Fix secret",
            code_changes=[
                CodeChange(
                    file_path=test_file,
                    original_code='api_key = "secret123"',
                    fixed_code='api_key = os.getenv("API_KEY")',
                    description="Replace with env var",
                )
            ],
        )

        result = engine.apply_auto_fix(action)

        assert result.status == RemediationStatus.APPLIED
        assert result.changes_applied == 1
        assert result.backup_path is not None

    def test_apply_auto_fix_dry_run(self, tmp_path: Path) -> None:
        """Test auto-fix in dry-run mode."""
        config = RemediationConfig(dry_run=True)
        engine = RemediationEngine(config)

        test_file = tmp_path / "test.py"
        test_file.write_text("test")

        action = RemediationAction(
            finding_id="001",
            remediation_type=RemediationType.AUTO_FIX,
            description="Test",
            code_changes=[
                CodeChange(
                    file_path=test_file,
                    original_code="test",
                    fixed_code="fixed",
                    description="Test change",
                )
            ],
        )

        result = engine.apply_auto_fix(action)

        assert result.status == RemediationStatus.APPLIED
        # File should not be changed in dry-run
        assert test_file.read_text() == "test"

    def test_apply_auto_fix_max_limit(self) -> None:
        """Test auto-fix maximum limit enforcement."""
        config = RemediationConfig(max_auto_fixes=1)
        engine = RemediationEngine(config)

        action = RemediationAction(
            finding_id="001",
            remediation_type=RemediationType.AUTO_FIX,
            description="Test",
            code_changes=[],
        )

        # First fix should work
        engine._fix_count = 0
        result1 = engine.apply_auto_fix(action)
        assert result1.status == RemediationStatus.APPLIED

        # Second fix should fail
        with pytest.raises(AutoFixError, match="Maximum.*limit"):
            engine.apply_auto_fix(action)

    def test_generate_playbook_hardcoded_secret(self) -> None:
        """Test playbook generation for hardcoded secrets."""
        config = RemediationConfig()
        engine = RemediationEngine(config)

        finding = {
            "id": "001",
            "title": "Hardcoded Password",
            "description": "Password in code",
            "severity": "critical",
        }

        playbook = engine.generate_playbook(finding)

        assert len(playbook.steps) > 0
        assert "secret" in playbook.title.lower()
        assert len(playbook.references) > 0

    def test_generate_playbook_security_group(self) -> None:
        """Test playbook generation for security groups."""
        config = RemediationConfig()
        engine = RemediationEngine(config)

        finding = {
            "id": "002",
            "title": "Open Security Group",
            "description": "Overly permissive rules",
            "severity": "high",
        }

        playbook = engine.generate_playbook(finding)

        assert len(playbook.steps) > 0
        assert any(
            "security group" in step.lower() for step in playbook.steps
        )

    def test_detect_compliance_drift(self) -> None:
        """Test compliance drift detection."""
        config = RemediationConfig()
        engine = RemediationEngine(config)

        current_scan = {
            "findings": [
                {"id": "001", "severity": "high", "description": "New issue"}
            ]
        }

        baseline = {"findings": []}

        drifts = engine.detect_compliance_drift(current_scan, baseline)

        assert len(drifts) == 1
        assert drifts[0].remediation_action is not None

    def test_create_fix_pr_mocked(self, tmp_path: Path) -> None:
        """Test pull request creation (mocked)."""
        config = RemediationConfig(
            github_token="test-token", backup_dir=tmp_path / "backups"
        )
        engine = RemediationEngine(config)

        test_file = tmp_path / "test.py"
        test_file.write_text("old code")

        actions = [
            RemediationAction(
                finding_id="001",
                remediation_type=RemediationType.AUTO_FIX,
                description="Test fix",
                code_changes=[
                    CodeChange(
                        file_path=test_file,
                        original_code="old code",
                        fixed_code="new code",
                        description="Update",
                    )
                ],
            )
        ]

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = Mock(returncode=0)

            with patch("requests.post") as mock_post:
                mock_post.return_value = Mock(
                    status_code=201,
                    json=lambda: {"html_url": "https://github.com/pr/1"},
                )

                pr_url = engine.create_fix_pr(actions, "owner/repo")

                assert "github.com" in pr_url

    def test_fix_terraform_s3_encryption(self) -> None:
        """Test Terraform S3 encryption fix generation."""
        config = RemediationConfig()
        engine = RemediationEngine(config)

        finding = {
            "id": "001",
            "title": "S3 Bucket Not Encrypted",
            "description": "S3 bucket lacks encryption",
            "severity": "high",
            "file": "s3.tf",
            "line": 10,
            "code_snippet": 'resource "aws_s3_bucket" "example" {}',
            "issue_type": "s3 encryption",
        }

        action = engine._fix_terraform_issue(finding)

        assert len(action.code_changes) > 0
        assert "encryption" in action.code_changes[0].fixed_code.lower()

    def test_fix_dockerfile_root_user(self) -> None:
        """Test Dockerfile root user fix."""
        config = RemediationConfig()
        engine = RemediationEngine(config)

        finding = {
            "id": "001",
            "title": "Running as Root",
            "description": "Container runs as root user",
            "severity": "medium",
            "file": "Dockerfile",
            "line": 5,
            "code_snippet": "FROM ubuntu:20.04\nRUN apt-get update",
        }

        action = engine._fix_dockerfile_issue(finding)

        assert "USER" in action.code_changes[0].fixed_code

    def test_fix_kubernetes_privileged_container(self) -> None:
        """Test Kubernetes privileged container fix."""
        config = RemediationConfig()
        engine = RemediationEngine(config)

        finding = {
            "id": "001",
            "title": "Privileged Container",
            "description": "Container runs in privileged mode",
            "severity": "high",
            "file": "deployment.yaml",
            "line": 20,
            "code_snippet": "privileged: true",
        }

        action = engine._fix_kubernetes_issue(finding)

        assert "privileged: false" in action.code_changes[0].fixed_code

    def test_backup_creation(self, tmp_path: Path) -> None:
        """Test file backup system."""
        config = RemediationConfig(
            backup_dir=tmp_path / "backups", backup_enabled=True
        )
        engine = RemediationEngine(config)

        test_file = tmp_path / "test.py"
        test_file.write_text("original content")

        changes = [
            CodeChange(
                file_path=test_file,
                original_code="original content",
                fixed_code="new content",
                description="Test",
            )
        ]

        backup_path = engine._create_backup(changes)

        assert backup_path.exists()
        # Backup should contain original file
        assert len(list(backup_path.rglob("*.py"))) > 0


# ============================================================================
# CLI TESTS
# ============================================================================


class TestSecurityCLI:
    """Test suite for Security CLI component."""

    def test_cli_initialization(self) -> None:
        """Test CLI initialization."""
        runner = CliRunner()
        result = runner.invoke(cli, ["--help"])

        assert result.exit_code == 0
        assert "DevCrew Infrastructure Security Scanner" in result.output

    def test_cli_config_show(self, tmp_path: Path) -> None:
        """Test config show command."""
        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=tmp_path):
            result = runner.invoke(cli, ["config", "show"])

            assert result.exit_code == 0
            assert "Configuration" in result.output

    def test_cli_config_set(self, tmp_path: Path) -> None:
        """Test config set command."""
        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=tmp_path):
            result = runner.invoke(
                cli, ["config", "set", "scan.timeout", "900"]
            )

            assert result.exit_code == 0
            assert "Configuration updated" in result.output

    def test_scan_container_command_mocked(self) -> None:
        """Test scan container CLI command."""
        runner = CliRunner()

        with patch("shutil.which", return_value="/usr/bin/trivy"):
            with patch("subprocess.run") as mock_run:
                mock_run.side_effect = [
                    Mock(returncode=0, stdout="Version: 0.48.0", stderr=""),
                    Mock(
                        returncode=0,
                        stdout=json.dumps({"Results": []}),
                        stderr="",
                    ),
                ]

                result = runner.invoke(
                    cli, ["scan", "container", "nginx:latest"]
                )

                assert result.exit_code == EXIT_SUCCESS

    def test_scan_terraform_command_mocked(self, temp_terraform_dir: Path) -> None:
        """Test scan terraform CLI command."""
        runner = CliRunner()

        with patch("shutil.which", return_value="/usr/bin/checkov"):
            with patch("subprocess.run") as mock_run:
                mock_run.return_value = Mock(
                    returncode=0,
                    stdout=json.dumps({"results": {"failed_checks": []}}),
                    stderr="",
                )

                result = runner.invoke(
                    cli, ["scan", "terraform", str(temp_terraform_dir)]
                )

                assert result.exit_code == EXIT_SUCCESS

    def test_validate_opa_command_mocked(self, temp_policy_dir: Path) -> None:
        """Test validate opa CLI command."""
        runner = CliRunner()

        with patch("shutil.which", return_value="/usr/bin/opa"):
            with patch("subprocess.run") as mock_run:
                mock_run.side_effect = [
                    Mock(returncode=0, stdout="Version: 0.55.0", stderr=""),
                    Mock(
                        returncode=0,
                        stdout=json.dumps(
                            {
                                "result": [
                                    {"expressions": [{"value": {"deny": []}}]}
                                ]
                            }
                        ),
                        stderr="",
                    ),
                ]

                with patch.object(
                    PolicyValidator, "_load_rego_policies", return_value=None
                ):
                    result = runner.invoke(
                        cli, ["validate", "opa", str(temp_policy_dir)]
                    )

                    assert result.exit_code == EXIT_SUCCESS

    def test_sbom_generate_command_mocked(self) -> None:
        """Test SBOM generate CLI command."""
        runner = CliRunner()

        with patch("shutil.which", return_value="/usr/bin/trivy"):
            with patch("subprocess.run") as mock_run:
                mock_run.side_effect = [
                    Mock(returncode=0, stdout="Version: 0.48.0", stderr=""),
                    Mock(
                        returncode=0,
                        stdout=json.dumps({"bomFormat": "CycloneDX"}),
                        stderr="",
                    ),
                ]

                result = runner.invoke(
                    cli, ["sbom", "generate", "nginx:latest"]
                )

                assert result.exit_code == EXIT_SUCCESS

    def test_report_aggregate_command(self, tmp_path: Path) -> None:
        """Test report aggregate CLI command."""
        runner = CliRunner()

        # Create sample scan files
        scan1 = tmp_path / "scan1.json"
        scan2 = tmp_path / "scan2.json"

        scan1.write_text(
            json.dumps([{"id": "001", "title": "Finding 1"}])
        )
        scan2.write_text(
            json.dumps([{"id": "002", "title": "Finding 2"}])
        )

        output = tmp_path / "combined.json"

        result = runner.invoke(
            cli,
            [
                "report",
                "aggregate",
                str(scan1),
                str(scan2),
                "-o",
                str(output),
            ],
        )

        assert result.exit_code == EXIT_SUCCESS
        assert output.exists()

    def test_cli_error_handling(self) -> None:
        """Test CLI error handling."""
        runner = CliRunner()

        # Test with nonexistent image
        with patch("shutil.which", return_value="/usr/bin/trivy"):
            with patch("subprocess.run") as mock_run:
                mock_run.side_effect = [
                    Mock(returncode=0, stdout="Version: 0.48.0", stderr=""),
                    Mock(
                        returncode=1,
                        stdout="",
                        stderr="Error: not found",
                    ),
                ]

                result = runner.invoke(
                    cli, ["scan", "container", "nonexistent:latest"]
                )

                assert result.exit_code == EXIT_SCAN_ERROR

    def test_cli_help_commands(self) -> None:
        """Test CLI help output for all command groups."""
        runner = CliRunner()

        commands = [
            ["scan", "--help"],
            ["validate", "--help"],
            ["sbom", "--help"],
            ["report", "--help"],
            ["remediate", "--help"],
            ["config", "--help"],
        ]

        for cmd in commands:
            result = runner.invoke(cli, cmd)
            assert result.exit_code == 0
            assert "Usage:" in result.output

    def test_cli_exit_codes(self) -> None:
        """Test CLI exit codes match specification."""
        assert EXIT_SUCCESS == 0
        assert EXIT_FINDINGS_FOUND == 1
        assert EXIT_VALIDATION_FAILED == 2
        assert EXIT_SCAN_ERROR == 3
        assert EXIT_CONFIG_ERROR == 4


# ============================================================================
# INTEGRATION TESTS
# ============================================================================


class TestEndToEndIntegration:
    """End-to-end integration tests."""

    def test_full_scan_to_report_workflow(
        self, tmp_path: Path, mock_trivy_output: Dict
    ) -> None:
        """Test complete workflow from scan to report."""
        # Step 1: Scan
        with patch("shutil.which", return_value="/usr/bin/trivy"):
            with patch("subprocess.run") as mock_run:
                mock_run.side_effect = [
                    Mock(returncode=0, stdout="Version: 0.48.0", stderr=""),
                    Mock(
                        returncode=0,
                        stdout=json.dumps(mock_trivy_output),
                        stderr="",
                    ),
                ]

                scanner = ContainerScanner()
                scan_result = scanner.scan_image("nginx:latest")

        # Step 2: Aggregate
        aggregator = ReportAggregator()
        findings_data = [
            {
                "scanner": "trivy",
                "findings": [
                    {
                        "id": v.cve_id,
                        "title": v.title,
                        "description": v.description,
                        "severity": v.severity.value,
                        "rule_id": v.cve_id,
                    }
                    for v in scan_result.vulnerabilities
                ],
            }
        ]

        report = aggregator.aggregate(findings_data)

        # Step 3: Generate reports
        json_output = aggregator.generate_json(report)
        html_output = aggregator.generate_html(report)
        md_output = aggregator.generate_markdown(report)

        assert json_output
        assert html_output
        assert md_output
        assert report.summary.total_count > 0

    def test_scan_remediate_workflow(self, tmp_path: Path) -> None:
        """Test scan to remediation workflow."""
        # Create test file with issue
        test_file = tmp_path / "app.py"
        test_file.write_text('api_key = "hardcoded-secret"')

        # Generate finding
        finding = {
            "id": "001",
            "title": "Hardcoded API Key",
            "description": "API key in code",
            "severity": "critical",
            "file": str(test_file),
            "line": 1,
            "code_snippet": 'api_key = "hardcoded-secret"',
        }

        # Generate remediation
        config = RemediationConfig(
            backup_dir=tmp_path / "backups", dry_run=False
        )
        engine = RemediationEngine(config)
        action = engine.generate_remediation(finding)

        # Apply fix
        result = engine.apply_auto_fix(action)

        assert result.status == RemediationStatus.APPLIED
        assert result.backup_path.exists()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
