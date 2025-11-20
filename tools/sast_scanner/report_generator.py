"""
SARIF Report Generator for SAST Tool (Issue #39)
Generates standardized SARIF format reports from scan results.

TOOL-SEC-001: Static Application Security Testing Scanner
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class SARIFReportGenerator:
    """
    Generates SARIF (Static Analysis Results Interchange Format) reports.
    SARIF 2.1.0 specification compliant.
    """

    SARIF_VERSION = "2.1.0"
    SCHEMA_URI = (
        "https://raw.githubusercontent.com/oasis-tcs/sarif-spec/"
        "master/Schemata/sarif-schema-2.1.0.json"
    )

    def __init__(self, tool_name: str = "devgru_sast", tool_version: str = "1.0.0"):
        """
        Initialize SARIF report generator.

        Args:
            tool_name: Name of the SAST tool
            tool_version: Version of the SAST tool
        """
        self.tool_name = tool_name
        self.tool_version = tool_version

    def generate(
        self,
        findings: List[Dict[str, Any]],
        scan_path: Path,
        scanner_info: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """
        Generate SARIF report from findings.

        Args:
            findings: List of security findings
            scan_path: Path that was scanned
            scanner_info: Additional scanner information

        Returns:
            SARIF report as dictionary
        """
        logger.info(f"Generating SARIF report for {len(findings)} findings")

        # Build SARIF document
        sarif_report = {
            "$schema": self.SCHEMA_URI,
            "version": self.SARIF_VERSION,
            "runs": [
                self._create_run(findings, scan_path, scanner_info or {}),
            ],
        }

        return sarif_report

    def _create_run(
        self,
        findings: List[Dict[str, Any]],
        scan_path: Path,
        scanner_info: Dict[str, str],
    ) -> Dict[str, Any]:
        """
        Create a SARIF run object.

        Args:
            findings: List of findings
            scan_path: Scan path
            scanner_info: Scanner metadata

        Returns:
            SARIF run object
        """
        # Extract unique rules from findings
        rules = self._extract_rules(findings)

        run = {
            "tool": {
                "driver": {
                    "name": scanner_info.get("scanner", self.tool_name),
                    "version": self.tool_version,
                    "informationUri": "https://github.com/GSA-TTS/devCrew_s1",
                    "rules": rules,
                }
            },
            "results": self._convert_findings_to_results(findings, scan_path),
            "invocations": [
                {
                    "executionSuccessful": True,
                    "endTimeUtc": datetime.utcnow().isoformat() + "Z",
                }
            ],
            "properties": {
                "scanPath": str(scan_path),
                "totalFindings": len(findings),
            },
        }

        return run

    def _extract_rules(self, findings: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Extract unique rules from findings.

        Args:
            findings: List of findings

        Returns:
            List of SARIF rule objects
        """
        rules_dict: Dict[str, Dict[str, Any]] = {}

        for finding in findings:
            rule_id = finding.get("rule_id", "unknown")

            if rule_id not in rules_dict:
                rules_dict[rule_id] = {
                    "id": rule_id,
                    "name": rule_id,
                    "shortDescription": {
                        "text": finding.get("message", "Security issue detected")[:100]
                    },
                    "fullDescription": {
                        "text": finding.get("message", "No description available")
                    },
                    "defaultConfiguration": {
                        "level": self._map_severity_to_level(
                            finding.get("severity", "INFO")
                        )
                    },
                    "properties": {
                        "tags": self._extract_tags(finding),
                        "precision": self._map_confidence_to_precision(
                            finding.get("confidence", "MEDIUM")
                        ),
                    },
                }

                # Add CWE information if available
                cwe_list = finding.get("cwe", [])
                if cwe_list:
                    rules_dict[rule_id]["properties"]["cwe"] = cwe_list

                # Add OWASP information if available
                owasp_list = finding.get("owasp", [])
                if owasp_list:
                    rules_dict[rule_id]["properties"]["owasp"] = owasp_list

                # Add help/references
                if finding.get("references"):
                    rules_dict[rule_id]["helpUri"] = finding["references"][0]

        return list(rules_dict.values())

    def _convert_findings_to_results(
        self, findings: List[Dict[str, Any]], scan_path: Path
    ) -> List[Dict[str, Any]]:
        """
        Convert findings to SARIF results.

        Args:
            findings: List of findings
            scan_path: Base scan path

        Returns:
            List of SARIF result objects
        """
        results = []

        for finding in findings:
            result = {
                "ruleId": finding.get("rule_id", "unknown"),
                "level": self._map_severity_to_level(finding.get("severity", "INFO")),
                "message": {"text": finding.get("message", "Security issue detected")},
                "locations": [
                    {
                        "physicalLocation": {
                            "artifactLocation": {
                                "uri": self._normalize_path(
                                    finding.get("file_path", ""), scan_path
                                ),
                                "uriBaseId": "%SRCROOT%",
                            },
                            "region": {
                                "startLine": finding.get("start_line", 1),
                                "endLine": finding.get("end_line", 1),
                                "startColumn": finding.get("start_col", 1),
                                "endColumn": finding.get("end_col", 1),
                                "snippet": {
                                    "text": finding.get("code_snippet", "")
                                },
                            },
                        }
                    }
                ],
                "properties": {
                    "confidence": finding.get("confidence", "MEDIUM"),
                    "category": finding.get("category", "security"),
                },
            }

            # Add fix information if available
            if finding.get("fix"):
                result["fixes"] = [
                    {
                        "description": {"text": "Apply suggested fix"},
                        "artifactChanges": [
                            {
                                "artifactLocation": {
                                    "uri": self._normalize_path(
                                        finding.get("file_path", ""), scan_path
                                    )
                                },
                                "replacements": [
                                    {
                                        "deletedRegion": {
                                            "startLine": finding.get("start_line", 1),
                                            "endLine": finding.get("end_line", 1),
                                        },
                                        "insertedContent": {
                                            "text": finding.get("fix", "")
                                        },
                                    }
                                ],
                            }
                        ],
                    }
                ]

            results.append(result)

        return results

    def _extract_tags(self, finding: Dict[str, Any]) -> List[str]:
        """
        Extract tags from finding metadata.

        Args:
            finding: Finding dictionary

        Returns:
            List of tags
        """
        tags = ["security"]

        # Add severity tag
        severity = finding.get("severity", "").lower()
        if severity:
            tags.append(severity)

        # Add category tag
        category = finding.get("category", "")
        if category:
            tags.append(category)

        # Add CWE tags
        for cwe in finding.get("cwe", []):
            tags.append(f"cwe-{cwe.replace('CWE-', '')}")

        # Add OWASP tags
        for owasp in finding.get("owasp", []):
            tags.append(f"owasp-{owasp.split(':')[0].lower()}")

        return tags

    def _map_severity_to_level(self, severity: str) -> str:
        """
        Map severity to SARIF level.

        Args:
            severity: Severity string (CRITICAL, HIGH, MEDIUM, LOW, INFO)

        Returns:
            SARIF level (error, warning, note)
        """
        severity_upper = severity.upper()

        if severity_upper in ("CRITICAL", "HIGH"):
            return "error"
        elif severity_upper == "MEDIUM":
            return "warning"
        else:  # LOW, INFO
            return "note"

    def _map_confidence_to_precision(self, confidence: str) -> str:
        """
        Map confidence to SARIF precision.

        Args:
            confidence: Confidence level (HIGH, MEDIUM, LOW)

        Returns:
            SARIF precision (high, medium, low)
        """
        return confidence.lower()

    def _normalize_path(self, file_path: str, base_path: Path) -> str:
        """
        Normalize file path relative to base scan path.

        Args:
            file_path: Absolute or relative file path
            base_path: Base scan path

        Returns:
            Normalized relative path
        """
        try:
            path_obj = Path(file_path)
            if path_obj.is_absolute():
                # Try to make it relative to base_path
                try:
                    return str(path_obj.relative_to(base_path))
                except ValueError:
                    # If not under base_path, return as-is
                    return str(path_obj)
            return file_path
        except Exception as e:
            logger.warning(f"Failed to normalize path {file_path}: {e}")
            return file_path

    def export_to_file(
        self, sarif_report: Dict[str, Any], output_path: Path
    ) -> None:
        """
        Export SARIF report to file.

        Args:
            sarif_report: SARIF report dictionary
            output_path: Output file path

        Raises:
            IOError: If file write fails
        """
        try:
            output_path.parent.mkdir(parents=True, exist_ok=True)

            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(sarif_report, f, indent=2)

            logger.info(f"SARIF report exported to: {output_path}")

        except Exception as e:
            logger.error(f"Failed to export SARIF report: {e}")
            raise IOError(f"Failed to write SARIF report: {e}") from e

    def validate_sarif(self, sarif_report: Dict[str, Any]) -> bool:
        """
        Validate SARIF report structure (basic validation).

        Args:
            sarif_report: SARIF report dictionary

        Returns:
            True if valid, False otherwise
        """
        try:
            # Check required top-level fields
            if "$schema" not in sarif_report:
                logger.error("Missing $schema field")
                return False

            if "version" not in sarif_report:
                logger.error("Missing version field")
                return False

            if "runs" not in sarif_report or not isinstance(
                sarif_report["runs"], list
            ):
                logger.error("Missing or invalid runs field")
                return False

            # Check each run
            for run in sarif_report["runs"]:
                if "tool" not in run:
                    logger.error("Missing tool field in run")
                    return False

                if "results" not in run:
                    logger.error("Missing results field in run")
                    return False

            logger.info("SARIF report validation passed")
            return True

        except Exception as e:
            logger.error(f"SARIF validation error: {e}")
            return False


class HTMLReportGenerator:
    """
    Generates HTML reports from scan findings.
    """

    def generate(
        self, findings: List[Dict[str, Any]], summary: Dict[str, Any]
    ) -> str:
        """
        Generate HTML report from findings.

        Args:
            findings: List of findings
            summary: Summary statistics

        Returns:
            HTML report as string
        """
        html_template = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>SAST Scan Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        h1 {{ color: #333; }}
        .summary {{ background: #f5f5f5; padding: 15px; border-radius: 5px;
                    margin-bottom: 20px; }}
        .finding {{ border: 1px solid #ddd; padding: 10px;
                    margin-bottom: 10px; border-radius: 5px; }}
        .critical {{ border-left: 5px solid #d32f2f; }}
        .high {{ border-left: 5px solid #f57c00; }}
        .medium {{ border-left: 5px solid #fbc02d; }}
        .low {{ border-left: 5px solid #388e3c; }}
        .info {{ border-left: 5px solid #1976d2; }}
        .severity {{ font-weight: bold; padding: 3px 8px;
                     border-radius: 3px; color: white; }}
        .code {{ background: #f5f5f5; padding: 10px;
                 font-family: monospace; overflow-x: auto; }}
        table {{ border-collapse: collapse; width: 100%;
                 margin-bottom: 20px; }}
        th, td {{ border: 1px solid #ddd; padding: 8px;
                  text-align: left; }}
        th {{ background-color: #4CAF50; color: white; }}
    </style>
</head>
<body>
    <h1>SAST Scan Report</h1>
    <div class="summary">
        <h2>Summary</h2>
        <p><strong>Total Findings:</strong> {total}</p>
        <p><strong>Critical:</strong> {critical} |
           <strong>High:</strong> {high} |
           <strong>Medium:</strong> {medium} |
           <strong>Low:</strong> {low} |
           <strong>Info:</strong> {info}</p>
        <p><strong>Generated:</strong> {timestamp}</p>
    </div>

    <h2>Findings</h2>
    {findings_html}
</body>
</html>
        """

        # Generate findings HTML
        findings_html = ""
        for idx, finding in enumerate(findings, 1):
            severity = finding.get("severity", "INFO").lower()
            rule_id = finding.get('rule_id', 'Unknown')
            sev = finding.get('severity', 'INFO')
            file_path = finding.get('file_path', 'Unknown')
            start_line = finding.get('start_line', 0)
            msg = finding.get('message', 'No description')
            snippet = finding.get('code_snippet', '')

            findings_html += f"""
            <div class="finding {severity}">
                <h3>Finding #{idx}: {rule_id}</h3>
                <p><span class="severity {severity}">{sev}</span></p>
                <p><strong>File:</strong> {file_path}</p>
                <p><strong>Line:</strong> {start_line}</p>
                <p><strong>Message:</strong> {msg}</p>
                <div class="code"><pre>{snippet}</pre></div>
            </div>
            """

        # Get severity counts
        by_severity = summary.get("by_severity", {})

        return html_template.format(
            total=summary.get("total_findings", 0),
            critical=by_severity.get("CRITICAL", 0),
            high=by_severity.get("HIGH", 0),
            medium=by_severity.get("MEDIUM", 0),
            low=by_severity.get("LOW", 0),
            info=by_severity.get("INFO", 0),
            timestamp=datetime.now().isoformat(),
            findings_html=findings_html,
        )

    def export_to_file(self, html_report: str, output_path: Path) -> None:
        """
        Export HTML report to file.

        Args:
            html_report: HTML report string
            output_path: Output file path
        """
        try:
            output_path.parent.mkdir(parents=True, exist_ok=True)

            with open(output_path, "w", encoding="utf-8") as f:
                f.write(html_report)

            logger.info(f"HTML report exported to: {output_path}")

        except Exception as e:
            logger.error(f"Failed to export HTML report: {e}")
            raise IOError(f"Failed to write HTML report: {e}") from e
