"""
Semgrep Scanner Wrapper for SAST Tool (Issue #39)
Integrates Semgrep for multi-language static security analysis.

TOOL-SEC-001: Static Application Security Testing Scanner
"""

import json
import logging
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class SemgrepScanner:
    """
    Wrapper for Semgrep security scanner.
    Supports OWASP Top 10 and CWE Top 25 detection.
    """

    OWASP_CONFIGS = {
        "owasp-top-ten": "p/owasp-top-ten",
        "security-audit": "p/security-audit",
        "cwe-top-25": "p/cwe-top-25",
    }

    LANGUAGE_SUPPORT = [
        "python",
        "javascript",
        "typescript",
        "go",
        "java",
        "c",
        "cpp",
        "ruby",
        "php",
        "kotlin",
        "swift",
    ]

    def __init__(
        self,
        config: str = "p/owasp-top-ten",
        custom_rules: Optional[Path] = None,
        timeout: int = 300,
    ):
        """
        Initialize Semgrep scanner.

        Args:
            config: Semgrep config/ruleset to use (default: OWASP Top 10)
            custom_rules: Path to custom Semgrep rules directory
            timeout: Timeout in seconds for scan execution
        """
        self.config = config
        self.custom_rules = custom_rules
        self.timeout = timeout
        self._verify_installation()

    def _verify_installation(self) -> None:
        """Verify Semgrep is installed and accessible."""
        try:
            result = subprocess.run(
                ["semgrep", "--version"],  # nosec B603 B607
                capture_output=True,
                text=True,
                timeout=10,
            )
            if result.returncode != 0:
                raise RuntimeError("Semgrep not found or not working")
            logger.info(f"Semgrep version: {result.stdout.strip()}")
        except (subprocess.TimeoutExpired, FileNotFoundError) as e:
            raise RuntimeError(f"Semgrep installation check failed: {e}") from e

    def scan(
        self,
        path: Path,
        severity_threshold: str = "INFO",
        exclude_patterns: Optional[List[str]] = None,
        autofix: bool = False,
    ) -> Dict[str, Any]:
        """
        Execute Semgrep scan on specified path.

        Args:
            path: Path to scan (file or directory)
            severity_threshold: Minimum severity (INFO, WARNING, ERROR)
            exclude_patterns: List of patterns to exclude
            autofix: Enable autofix suggestions

        Returns:
            Dict containing scan results with findings

        Raises:
            RuntimeError: If scan fails
        """
        if not path.exists():
            raise FileNotFoundError(f"Scan path does not exist: {path}")

        logger.info(f"Starting Semgrep scan on: {path}")
        logger.info(f"Using config: {self.config}")

        # Build command
        cmd = [
            "semgrep",
            "--config",
            self.config,
            "--json",
            "--metrics=off",  # Disable metrics collection
            "--severity",
            severity_threshold,
        ]

        # Add custom rules if specified
        if self.custom_rules and self.custom_rules.exists():
            cmd.extend(["--config", str(self.custom_rules)])
            logger.info(f"Using custom rules from: {self.custom_rules}")

        # Add exclude patterns
        if exclude_patterns:
            for pattern in exclude_patterns:
                cmd.extend(["--exclude", pattern])

        # Add autofix flag
        if autofix:
            cmd.append("--autofix")

        # Add scan path
        cmd.append(str(path))

        try:
            result = subprocess.run(
                cmd,  # nosec B603
                capture_output=True,
                text=True,
                timeout=self.timeout,
            )

            # Semgrep returns exit code 1 when findings are present
            if result.returncode not in (0, 1):
                logger.error(f"Semgrep scan failed: {result.stderr}")
                raise RuntimeError(
                    f"Semgrep scan failed with exit code {result.returncode}"
                )

            # Parse JSON output
            scan_results = json.loads(result.stdout)

            # Extract findings
            findings = self._process_results(scan_results)

            logger.info(
                f"Semgrep scan completed. Found {len(findings)} findings."
            )

            return {
                "scanner": "semgrep",
                "scan_path": str(path),
                "config": self.config,
                "findings": findings,
                "summary": self._generate_summary(findings),
            }

        except subprocess.TimeoutExpired as e:
            logger.error(f"Semgrep scan timeout after {self.timeout}s")
            raise RuntimeError(f"Scan timeout: {e}") from e
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Semgrep JSON output: {e}")
            raise RuntimeError(f"Invalid JSON output: {e}") from e

    def _process_results(self, raw_results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Process and normalize Semgrep results.

        Args:
            raw_results: Raw Semgrep JSON output

        Returns:
            List of normalized findings
        """
        findings = []

        for result in raw_results.get("results", []):
            finding = {
                "rule_id": result.get("check_id", "unknown"),
                "severity": result.get("extra", {})
                .get("severity", "INFO")
                .upper(),
                "message": result.get("extra", {}).get("message", "No description"),
                "file_path": result.get("path", ""),
                "start_line": result.get("start", {}).get("line", 0),
                "end_line": result.get("end", {}).get("line", 0),
                "start_col": result.get("start", {}).get("col", 0),
                "end_col": result.get("end", {}).get("col", 0),
                "code_snippet": result.get("extra", {}).get("lines", ""),
                # Metadata
                "cwe": result.get("extra", {}).get("metadata", {}).get("cwe", []),
                "owasp": result.get("extra", {})
                .get("metadata", {})
                .get("owasp", []),
                "confidence": result.get("extra", {})
                .get("metadata", {})
                .get("confidence", "MEDIUM"),
                "category": result.get("extra", {})
                .get("metadata", {})
                .get("category", "security"),
                # Fix information
                "fix": result.get("extra", {}).get("fix", None),
                "references": result.get("extra", {})
                .get("metadata", {})
                .get("references", []),
            }
            findings.append(finding)

        return findings

    def _generate_summary(self, findings: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Generate summary statistics for findings.

        Args:
            findings: List of findings

        Returns:
            Summary dictionary
        """
        severity_counts = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0, "INFO": 0}

        cwe_counts: Dict[str, int] = {}
        owasp_counts: Dict[str, int] = {}

        for finding in findings:
            # Count severities
            severity = finding.get("severity", "INFO")
            if severity in severity_counts:
                severity_counts[severity] += 1

            # Count CWEs
            for cwe in finding.get("cwe", []):
                cwe_counts[cwe] = cwe_counts.get(cwe, 0) + 1

            # Count OWASP categories
            for owasp in finding.get("owasp", []):
                owasp_counts[owasp] = owasp_counts.get(owasp, 0) + 1

        return {
            "total_findings": len(findings),
            "by_severity": severity_counts,
            "by_cwe": cwe_counts,
            "by_owasp": owasp_counts,
        }

    @classmethod
    def list_available_configs(cls) -> List[str]:
        """List available Semgrep configurations."""
        return list(cls.OWASP_CONFIGS.keys())

    @classmethod
    def get_supported_languages(cls) -> List[str]:
        """Get list of supported programming languages."""
        return cls.LANGUAGE_SUPPORT.copy()
