"""
Bandit Scanner Wrapper for SAST Tool (Issue #39)
Integrates Bandit for Python-specific security analysis.

TOOL-SEC-001: Static Application Security Testing Scanner
"""

import json
import logging
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class BanditScanner:
    """
    Wrapper for Bandit Python security scanner.
    Detects security issues specific to Python code.
    """

    SEVERITY_MAP = {
        "LOW": "LOW",
        "MEDIUM": "MEDIUM",
        "HIGH": "HIGH",
    }

    CONFIDENCE_MAP = {
        "LOW": "LOW",
        "MEDIUM": "MEDIUM",
        "HIGH": "HIGH",
    }

    def __init__(
        self,
        confidence_level: str = "MEDIUM",
        severity_level: str = "LOW",
        timeout: int = 300,
    ):
        """
        Initialize Bandit scanner.

        Args:
            confidence_level: Minimum confidence (LOW, MEDIUM, HIGH)
            severity_level: Minimum severity (LOW, MEDIUM, HIGH)
            timeout: Timeout in seconds for scan execution
        """
        self.confidence_level = confidence_level.upper()
        self.severity_level = severity_level.upper()
        self.timeout = timeout
        self._verify_installation()

    def _verify_installation(self) -> None:
        """Verify Bandit is installed and accessible."""
        try:
            result = subprocess.run(
                ["bandit", "--version"],  # nosec B603 B607
                capture_output=True,
                text=True,
                timeout=10,
            )
            if result.returncode != 0:
                raise RuntimeError("Bandit not found or not working")
            logger.info(f"Bandit version: {result.stdout.strip()}")
        except (subprocess.TimeoutExpired, FileNotFoundError) as e:
            raise RuntimeError(f"Bandit installation check failed: {e}") from e

    def scan(
        self,
        path: Path,
        exclude_patterns: Optional[List[str]] = None,
        recursive: bool = True,
    ) -> Dict[str, Any]:
        """
        Execute Bandit scan on specified path.

        Args:
            path: Path to scan (file or directory)
            exclude_patterns: List of patterns to exclude
            recursive: Recursively scan directories

        Returns:
            Dict containing scan results with findings

        Raises:
            RuntimeError: If scan fails
        """
        if not path.exists():
            raise FileNotFoundError(f"Scan path does not exist: {path}")

        logger.info(f"Starting Bandit scan on: {path}")
        logger.info(
            f"Confidence: {self.confidence_level}, Severity: {self.severity_level}"
        )

        # Build command
        cmd = [
            "bandit",
            "-f",
            "json",
            "-ll",  # Only show issues of a given severity level or higher
            "-ii",  # Only show issues of a given confidence level or higher
        ]

        # Add recursive flag for directories
        if path.is_dir() and recursive:
            cmd.append("-r")

        # Add exclude patterns
        if exclude_patterns:
            exclude_str = ",".join(exclude_patterns)
            cmd.extend(["--exclude", exclude_str])

        # Add scan path
        cmd.append(str(path))

        try:
            result = subprocess.run(
                cmd,  # nosec B603
                capture_output=True,
                text=True,
                timeout=self.timeout,
            )

            # Bandit returns exit code 1 when findings are present
            if result.returncode not in (0, 1):
                logger.error(f"Bandit scan failed: {result.stderr}")
                raise RuntimeError(
                    f"Bandit scan failed with exit code {result.returncode}"
                )

            # Parse JSON output
            scan_results = json.loads(result.stdout)

            # Extract and filter findings
            findings = self._process_results(scan_results)
            filtered_findings = self._filter_findings(findings)

            logger.info(
                f"Bandit scan completed. Found {len(filtered_findings)} findings."
            )

            return {
                "scanner": "bandit",
                "scan_path": str(path),
                "findings": filtered_findings,
                "summary": self._generate_summary(filtered_findings),
                "metrics": scan_results.get("metrics", {}),
            }

        except subprocess.TimeoutExpired as e:
            logger.error(f"Bandit scan timeout after {self.timeout}s")
            raise RuntimeError(f"Scan timeout: {e}") from e
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Bandit JSON output: {e}")
            raise RuntimeError(f"Invalid JSON output: {e}") from e

    def _process_results(self, raw_results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Process and normalize Bandit results.

        Args:
            raw_results: Raw Bandit JSON output

        Returns:
            List of normalized findings
        """
        findings = []

        for result in raw_results.get("results", []):
            # Extract CWE from test_id (e.g., B201 maps to CWE-327)
            cwe = self._map_bandit_to_cwe(result.get("test_id", ""))

            finding = {
                "rule_id": result.get("test_id", "unknown"),
                "severity": result.get("issue_severity", "MEDIUM").upper(),
                "confidence": result.get("issue_confidence", "MEDIUM").upper(),
                "message": result.get("issue_text", "No description"),
                "file_path": result.get("filename", ""),
                "start_line": result.get("line_number", 0),
                "end_line": result.get("line_number", 0),
                "start_col": result.get("col_offset", 0),
                "end_col": result.get("col_offset", 0)
                + len(result.get("code", "")),
                "code_snippet": result.get("code", ""),
                # Metadata
                "cwe": [cwe] if cwe else [],
                "owasp": self._map_bandit_to_owasp(result.get("test_id", "")),
                "category": "security",
                "test_name": result.get("test_name", ""),
                # Additional info
                "more_info": result.get("more_info", ""),
            }
            findings.append(finding)

        return findings

    def _filter_findings(self, findings: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Filter findings based on severity and confidence thresholds.

        Args:
            findings: List of findings

        Returns:
            Filtered list of findings
        """
        severity_order = {"LOW": 1, "MEDIUM": 2, "HIGH": 3, "CRITICAL": 4}
        confidence_order = {"LOW": 1, "MEDIUM": 2, "HIGH": 3}

        min_severity = severity_order.get(self.severity_level, 1)
        min_confidence = confidence_order.get(self.confidence_level, 1)

        filtered = []
        for finding in findings:
            finding_severity = severity_order.get(finding.get("severity", "LOW"), 1)
            finding_confidence = confidence_order.get(
                finding.get("confidence", "LOW"), 1
            )

            if (
                finding_severity >= min_severity
                and finding_confidence >= min_confidence
            ):
                filtered.append(finding)

        return filtered

    def _generate_summary(self, findings: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Generate summary statistics for findings.

        Args:
            findings: List of findings

        Returns:
            Summary dictionary
        """
        severity_counts = {"HIGH": 0, "MEDIUM": 0, "LOW": 0}
        confidence_counts = {"HIGH": 0, "MEDIUM": 0, "LOW": 0}
        test_id_counts: Dict[str, int] = {}

        for finding in findings:
            # Count severities
            severity = finding.get("severity", "MEDIUM")
            if severity in severity_counts:
                severity_counts[severity] += 1

            # Count confidence levels
            confidence = finding.get("confidence", "MEDIUM")
            if confidence in confidence_counts:
                confidence_counts[confidence] += 1

            # Count test IDs
            test_id = finding.get("rule_id", "unknown")
            test_id_counts[test_id] = test_id_counts.get(test_id, 0) + 1

        return {
            "total_findings": len(findings),
            "by_severity": severity_counts,
            "by_confidence": confidence_counts,
            "by_test_id": test_id_counts,
        }

    def _map_bandit_to_cwe(self, test_id: str) -> str:
        """
        Map Bandit test IDs to CWE identifiers.

        Args:
            test_id: Bandit test ID (e.g., B201)

        Returns:
            CWE identifier (e.g., CWE-327)
        """
        # Mapping based on Bandit documentation
        cwe_mapping = {
            "B102": "CWE-78",  # exec_used
            "B103": "CWE-78",  # set_bad_file_permissions
            "B104": "CWE-259",  # hardcoded_bind_all_interfaces
            "B105": "CWE-259",  # hardcoded_password_string
            "B106": "CWE-259",  # hardcoded_password_funcarg
            "B107": "CWE-259",  # hardcoded_password_default
            "B108": "CWE-377",  # hardcoded_tmp_directory
            "B201": "CWE-78",  # flask_debug_true
            "B301": "CWE-327",  # pickle
            "B302": "CWE-327",  # marshal
            "B303": "CWE-327",  # md5
            "B304": "CWE-327",  # insecure_cipher
            "B305": "CWE-327",  # insecure_cipher_mode
            "B306": "CWE-377",  # mktemp_q
            "B307": "CWE-502",  # eval
            "B308": "CWE-327",  # mark_safe
            "B310": "CWE-22",  # urllib_urlopen
            "B311": "CWE-330",  # random
            "B312": "CWE-327",  # telnetlib
            "B313": "CWE-327",  # xml_bad_cElementTree
            "B314": "CWE-327",  # xml_bad_ElementTree
            "B315": "CWE-327",  # xml_bad_expatreader
            "B316": "CWE-327",  # xml_bad_expatbuilder
            "B317": "CWE-327",  # xml_bad_sax
            "B318": "CWE-327",  # xml_bad_minidom
            "B319": "CWE-327",  # xml_bad_pulldom
            "B320": "CWE-327",  # xml_bad_etree
            "B321": "CWE-327",  # ftplib
            "B323": "CWE-327",  # unverified_context
            "B324": "CWE-327",  # hashlib_insecure_functions
            "B401": "CWE-78",  # import_telnetlib
            "B402": "CWE-327",  # import_ftplib
            "B403": "CWE-327",  # import_pickle
            "B404": "CWE-78",  # import_subprocess
            "B501": "CWE-295",  # request_with_no_cert_validation
            "B502": "CWE-295",  # ssl_with_bad_version
            "B503": "CWE-295",  # ssl_with_bad_defaults
            "B504": "CWE-295",  # ssl_with_no_version
            "B505": "CWE-327",  # weak_cryptographic_key
            "B506": "CWE-287",  # yaml_load
            "B507": "CWE-295",  # ssh_no_host_key_verification
            "B601": "CWE-78",  # paramiko_calls
            "B602": "CWE-78",  # subprocess_popen_with_shell_equals_true
            "B603": "CWE-78",  # subprocess_without_shell_equals_true
            "B604": "CWE-78",  # any_other_function_with_shell_equals_true
            "B605": "CWE-78",  # start_process_with_a_shell
            "B606": "CWE-78",  # start_process_with_no_shell
            "B607": "CWE-78",  # start_process_with_partial_path
            "B608": "CWE-89",  # hardcoded_sql_expressions
            "B609": "CWE-78",  # linux_commands_wildcard_injection
            "B610": "CWE-78",  # django_extra_used
            "B611": "CWE-78",  # django_rawsql_used
            "B701": "CWE-327",  # jinja2_autoescape_false
            "B702": "CWE-327",  # use_of_mako_templates
            "B703": "CWE-1188",  # django_mark_safe
        }

        return cwe_mapping.get(test_id, "")

    def _map_bandit_to_owasp(self, test_id: str) -> List[str]:
        """
        Map Bandit test IDs to OWASP Top 10 categories.

        Args:
            test_id: Bandit test ID

        Returns:
            List of OWASP categories
        """
        # Map common Bandit findings to OWASP 2021 categories
        owasp_mapping = {
            "B102": ["A03:2021-Injection"],  # exec
            "B105": ["A07:2021-Identification and Authentication Failures"],
            "B106": ["A07:2021-Identification and Authentication Failures"],
            "B107": ["A07:2021-Identification and Authentication Failures"],
            "B201": ["A05:2021-Security Misconfiguration"],
            "B301": ["A02:2021-Cryptographic Failures"],
            "B303": ["A02:2021-Cryptographic Failures"],
            "B304": ["A02:2021-Cryptographic Failures"],
            "B305": ["A02:2021-Cryptographic Failures"],
            "B307": ["A03:2021-Injection"],
            "B311": ["A02:2021-Cryptographic Failures"],
            "B501": ["A02:2021-Cryptographic Failures"],
            "B502": ["A02:2021-Cryptographic Failures"],
            "B505": ["A02:2021-Cryptographic Failures"],
            "B602": ["A03:2021-Injection"],
            "B603": ["A03:2021-Injection"],
            "B608": ["A03:2021-Injection"],
        }

        return owasp_mapping.get(test_id, [])

    @staticmethod
    def get_supported_checks() -> List[str]:
        """Get list of Bandit security checks."""
        return [
            "B102",
            "B103",
            "B104",
            "B105",
            "B106",
            "B107",
            "B108",
            "B201",
            "B301-B324",
            "B401-B404",
            "B501-B507",
            "B601-B611",
            "B701-B703",
        ]
