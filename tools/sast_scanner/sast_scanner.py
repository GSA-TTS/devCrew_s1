#!/usr/bin/env python3
"""
Main SAST Scanner Implementation (Issue #39)
Orchestrates Semgrep and Bandit scanners with result aggregation and reporting.

TOOL-SEC-001: Static Application Security Testing Scanner

Usage:
    python sast_scanner.py scan --path src/
    python sast_scanner.py scan-python --path src/
    python sast_scanner.py generate-baseline --path src/
    python sast_scanner.py compare-baseline --path src/
"""

import json
import logging
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

import click
from rich.console import Console
from rich.logging import RichHandler
from rich.table import Table

# Import our scanner modules
try:
    from bandit_wrapper import BanditScanner
    from report_generator import HTMLReportGenerator, SARIFReportGenerator
    from semgrep_wrapper import SemgrepScanner
except ImportError as e:
    print(f"Error importing scanner modules: {e}")
    print("Ensure all scanner modules are in the same directory")
    sys.exit(1)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    handlers=[RichHandler(rich_tracebacks=True)],
)
logger = logging.getLogger(__name__)

console = Console()


class SASTScanner:
    """
    Main SAST scanner that orchestrates multiple security scanners.
    """

    def __init__(self):
        """Initialize the SAST scanner."""
        self.semgrep_scanner: Optional[SemgrepScanner] = None
        self.bandit_scanner: Optional[BanditScanner] = None
        self.sarif_generator = SARIFReportGenerator()
        self.html_generator = HTMLReportGenerator()

    def scan(
        self,
        path: Path,
        severity_threshold: str = "INFO",
        exclude_patterns: Optional[List[str]] = None,
        use_semgrep: bool = True,
        use_bandit: bool = True,
        semgrep_config: str = "p/owasp-top-ten",
        custom_rules: Optional[Path] = None,
    ) -> Dict[str, Any]:
        """
        Execute comprehensive SAST scan.

        Args:
            path: Path to scan
            severity_threshold: Minimum severity level
            exclude_patterns: Patterns to exclude
            use_semgrep: Enable Semgrep scanner
            use_bandit: Enable Bandit scanner (Python only)
            semgrep_config: Semgrep configuration
            custom_rules: Path to custom rules

        Returns:
            Aggregated scan results
        """
        all_findings: List[Dict[str, Any]] = []
        scanner_results = {}

        # Run Semgrep if enabled
        if use_semgrep:
            try:
                console.print("[bold blue]Running Semgrep scanner...[/bold blue]")
                self.semgrep_scanner = SemgrepScanner(
                    config=semgrep_config, custom_rules=custom_rules
                )
                semgrep_results = self.semgrep_scanner.scan(
                    path=path,
                    severity_threshold=severity_threshold,
                    exclude_patterns=exclude_patterns,
                )
                all_findings.extend(semgrep_results["findings"])
                scanner_results["semgrep"] = semgrep_results
                num_findings = len(semgrep_results['findings'])
                console.print(
                    f"[green]Semgrep: Found {num_findings} issues[/green]"
                )
            except Exception as e:
                logger.error(f"Semgrep scan failed: {e}")
                console.print(f"[red]Semgrep scan failed: {e}[/red]")

        # Run Bandit if enabled and path contains Python code
        if use_bandit and self._contains_python_files(path):
            try:
                console.print("[bold blue]Running Bandit scanner...[/bold blue]")
                self.bandit_scanner = BanditScanner(
                    confidence_level="MEDIUM", severity_level=severity_threshold
                )
                bandit_results = self.bandit_scanner.scan(
                    path=path, exclude_patterns=exclude_patterns
                )
                all_findings.extend(bandit_results["findings"])
                scanner_results["bandit"] = bandit_results
                num_findings = len(bandit_results['findings'])
                console.print(
                    f"[green]Bandit: Found {num_findings} issues[/green]"
                )
            except Exception as e:
                logger.error(f"Bandit scan failed: {e}")
                console.print(f"[red]Bandit scan failed: {e}[/red]")

        # Aggregate results
        aggregated = self._aggregate_results(all_findings, scanner_results, path)

        return aggregated

    def scan_python(
        self,
        path: Path,
        severity_threshold: str = "INFO",
        exclude_patterns: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Python-specific scan with both Semgrep and Bandit.

        Args:
            path: Path to scan
            severity_threshold: Minimum severity level
            exclude_patterns: Patterns to exclude

        Returns:
            Aggregated scan results
        """
        console.print("[bold]Starting Python-specific security scan[/bold]")

        return self.scan(
            path=path,
            severity_threshold=severity_threshold,
            exclude_patterns=exclude_patterns,
            use_semgrep=True,
            use_bandit=True,
            semgrep_config="p/python",
        )

    def generate_baseline(self, path: Path, output_path: Path) -> None:
        """
        Generate baseline from current scan results.

        Args:
            path: Path to scan
            output_path: Path to save baseline
        """
        console.print("[bold]Generating baseline...[/bold]")

        # Scan with lowest threshold to capture everything
        results = self.scan(path=path, severity_threshold="INFO")

        # Create baseline
        baseline = {
            "scan_path": str(path),
            "total_findings": len(results["findings"]),
            "findings": results["findings"],
            "summary": results["summary"],
            "created_at": results["scan_metadata"]["timestamp"],
        }

        # Save baseline
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(baseline, f, indent=2)

        console.print(f"[green]Baseline saved to: {output_path}[/green]")

    def compare_baseline(
        self, path: Path, baseline_path: Path, fail_on_new: bool = False
    ) -> Dict[str, Any]:
        """
        Compare current scan against baseline.

        Args:
            path: Path to scan
            baseline_path: Path to baseline file
            fail_on_new: Exit with error if new findings detected

        Returns:
            Comparison results
        """
        console.print("[bold]Comparing against baseline...[/bold]")

        # Load baseline
        with open(baseline_path, "r", encoding="utf-8") as f:
            baseline = json.load(f)

        # Scan current state
        current_results = self.scan(path=path, severity_threshold="INFO")

        # Compare
        baseline_finding_ids = {
            self._get_finding_id(f) for f in baseline["findings"]
        }
        current_finding_ids = {
            self._get_finding_id(f) for f in current_results["findings"]
        }

        new_findings = [
            f
            for f in current_results["findings"]
            if self._get_finding_id(f) not in baseline_finding_ids
        ]
        resolved_findings = [
            f
            for f in baseline["findings"]
            if self._get_finding_id(f) not in current_finding_ids
        ]

        comparison = {
            "baseline_findings": len(baseline["findings"]),
            "current_findings": len(current_results["findings"]),
            "new_findings": new_findings,
            "resolved_findings": resolved_findings,
            "new_count": len(new_findings),
            "resolved_count": len(resolved_findings),
        }

        # Display results
        self._display_comparison(comparison)

        # Handle fail_on_new
        if fail_on_new and len(new_findings) > 0:
            msg = "[bold red]New security findings detected! "
            msg += "Failing as requested.[/bold red]"
            console.print(msg)
            sys.exit(1)

        return comparison

    def export_sarif(
        self, results: Dict[str, Any], output_path: Path
    ) -> None:
        """
        Export results as SARIF format.

        Args:
            results: Scan results
            output_path: Output file path
        """
        console.print("[bold]Exporting SARIF report...[/bold]")

        sarif_report = self.sarif_generator.generate(
            findings=results["findings"],
            scan_path=Path(results["scan_path"]),
            scanner_info={"scanner": "devgru_sast"},
        )

        # Validate SARIF
        if self.sarif_generator.validate_sarif(sarif_report):
            self.sarif_generator.export_to_file(sarif_report, output_path)
            console.print(f"[green]SARIF report saved to: {output_path}[/green]")
        else:
            console.print("[red]SARIF validation failed[/red]")

    def export_html(self, results: Dict[str, Any], output_path: Path) -> None:
        """
        Export results as HTML report.

        Args:
            results: Scan results
            output_path: Output file path
        """
        console.print("[bold]Exporting HTML report...[/bold]")

        html_report = self.html_generator.generate(
            findings=results["findings"], summary=results["summary"]
        )

        self.html_generator.export_to_file(html_report, output_path)
        console.print(f"[green]HTML report saved to: {output_path}[/green]")

    def _contains_python_files(self, path: Path) -> bool:
        """Check if path contains Python files."""
        if path.is_file():
            return path.suffix == ".py"

        # Check for .py files in directory
        return any(path.rglob("*.py"))

    def _aggregate_results(
        self,
        all_findings: List[Dict[str, Any]],
        scanner_results: Dict[str, Any],
        scan_path: Path,
    ) -> Dict[str, Any]:
        """
        Aggregate results from multiple scanners.

        Args:
            all_findings: All findings from scanners
            scanner_results: Individual scanner results
            scan_path: Scanned path

        Returns:
            Aggregated results dictionary
        """
        # Deduplicate findings
        deduplicated = self._deduplicate_findings(all_findings)

        # Generate combined summary
        summary = self._generate_combined_summary(deduplicated)

        return {
            "scan_path": str(scan_path),
            "findings": deduplicated,
            "summary": summary,
            "scanner_results": scanner_results,
            "scan_metadata": {
                "timestamp": self._get_timestamp(),
                "scanners_used": list(scanner_results.keys()),
            },
        }

    def _deduplicate_findings(
        self, findings: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Remove duplicate findings based on file, line, and rule ID.

        Args:
            findings: List of findings

        Returns:
            Deduplicated findings
        """
        seen = set()
        deduplicated = []

        for finding in findings:
            finding_id = self._get_finding_id(finding)

            if finding_id not in seen:
                seen.add(finding_id)
                deduplicated.append(finding)

        logger.info(
            f"Deduplicated {len(findings)} findings to {len(deduplicated)}"
        )

        return deduplicated

    def _get_finding_id(self, finding: Dict[str, Any]) -> str:
        """Generate unique ID for a finding."""
        return (
            f"{finding.get('file_path', '')}:"
            f"{finding.get('start_line', 0)}:"
            f"{finding.get('rule_id', '')}"
        )

    def _generate_combined_summary(
        self, findings: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Generate summary statistics for all findings."""
        severity_counts = {
            "CRITICAL": 0,
            "HIGH": 0,
            "MEDIUM": 0,
            "LOW": 0,
            "INFO": 0,
        }
        cwe_counts: Dict[str, int] = {}
        owasp_counts: Dict[str, int] = {}
        file_counts: Dict[str, int] = {}

        for finding in findings:
            # Count severities
            severity = finding.get("severity", "INFO")
            if severity in severity_counts:
                severity_counts[severity] += 1

            # Count CWEs
            for cwe in finding.get("cwe", []):
                cwe_counts[cwe] = cwe_counts.get(cwe, 0) + 1

            # Count OWASP
            for owasp in finding.get("owasp", []):
                owasp_counts[owasp] = owasp_counts.get(owasp, 0) + 1

            # Count files
            file_path = finding.get("file_path", "unknown")
            file_counts[file_path] = file_counts.get(file_path, 0) + 1

        return {
            "total_findings": len(findings),
            "by_severity": severity_counts,
            "by_cwe": cwe_counts,
            "by_owasp": owasp_counts,
            "by_file": file_counts,
            "files_affected": len(file_counts),
        }

    def _display_comparison(self, comparison: Dict[str, Any]) -> None:
        """Display baseline comparison results."""
        table = Table(title="Baseline Comparison")
        table.add_column("Metric", style="cyan")
        table.add_column("Count", style="magenta")

        table.add_row("Baseline Findings", str(comparison["baseline_findings"]))
        table.add_row("Current Findings", str(comparison["current_findings"]))
        table.add_row(
            "New Findings", f"[red]{comparison['new_count']}[/red]"
        )
        table.add_row(
            "Resolved Findings", f"[green]{comparison['resolved_count']}[/green]"
        )

        console.print(table)

    @staticmethod
    def _get_timestamp() -> str:
        """Get current timestamp in ISO format."""
        from datetime import datetime

        return datetime.utcnow().isoformat() + "Z"


# CLI Commands
@click.group()
@click.version_option(version="1.0.0")
def cli():
    """devgru_sast - Static Application Security Testing Scanner"""
    pass


@cli.command()
@click.option(
    "--path", "-p", type=click.Path(exists=True), required=True, help="Path to scan"
)
@click.option(
    "--output",
    "-o",
    type=click.Path(),
    default="sast_report.sarif",
    help="Output file path",
)
@click.option(
    "--severity",
    "-s",
    type=click.Choice(["INFO", "LOW", "MEDIUM", "HIGH", "CRITICAL"]),
    default="INFO",
    help="Minimum severity threshold",
)
@click.option(
    "--format",
    "-f",
    type=click.Choice(["sarif", "json", "html"]),
    default="sarif",
    help="Output format",
)
@click.option(
    "--exclude", "-e", multiple=True, help="Patterns to exclude from scan"
)
@click.option(
    "--config",
    "-c",
    default="p/owasp-top-ten",
    help="Semgrep configuration",
)
@click.option(
    "--custom-rules",
    type=click.Path(exists=True),
    help="Path to custom Semgrep rules",
)
@click.option("--no-semgrep", is_flag=True, help="Disable Semgrep scanner")
@click.option("--no-bandit", is_flag=True, help="Disable Bandit scanner")
def scan(
    path, output, severity, format, exclude, config, custom_rules, no_semgrep, no_bandit
):
    """Execute SAST scan on specified path."""
    scanner = SASTScanner()

    # Convert path strings to Path objects
    scan_path = Path(path)
    output_path = Path(output)
    custom_rules_path = Path(custom_rules) if custom_rules else None

    # Run scan
    results = scanner.scan(
        path=scan_path,
        severity_threshold=severity,
        exclude_patterns=list(exclude) if exclude else None,
        use_semgrep=not no_semgrep,
        use_bandit=not no_bandit,
        semgrep_config=config,
        custom_rules=custom_rules_path,
    )

    # Display summary
    _display_results_summary(results)

    # Export results
    if format == "sarif":
        scanner.export_sarif(results, output_path)
    elif format == "html":
        scanner.export_html(results, output_path)
    elif format == "json":
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2)
        console.print(f"[green]JSON report saved to: {output_path}[/green]")

    # Exit with error code if HIGH or CRITICAL findings
    if (
        results["summary"]["by_severity"]["HIGH"] > 0
        or results["summary"]["by_severity"].get("CRITICAL", 0) > 0
    ):
        sys.exit(1)


@cli.command()
@click.option(
    "--path", "-p", type=click.Path(exists=True), required=True, help="Path to scan"
)
@click.option(
    "--output",
    "-o",
    type=click.Path(),
    default="sast_report.sarif",
    help="Output file path",
)
@click.option(
    "--severity",
    "-s",
    type=click.Choice(["LOW", "MEDIUM", "HIGH"]),
    default="MEDIUM",
    help="Minimum severity threshold",
)
def scan_python(path, output, severity):
    """Execute Python-specific scan with Semgrep + Bandit."""
    scanner = SASTScanner()

    scan_path = Path(path)
    output_path = Path(output)

    results = scanner.scan_python(
        path=scan_path, severity_threshold=severity
    )

    _display_results_summary(results)

    scanner.export_sarif(results, output_path)

    # Exit with error code if HIGH findings
    if results["summary"]["by_severity"]["HIGH"] > 0:
        sys.exit(1)


@cli.command()
@click.option(
    "--path", "-p", type=click.Path(exists=True), required=True, help="Path to scan"
)
@click.option(
    "--output",
    "-o",
    type=click.Path(),
    default="baseline.json",
    help="Output baseline file",
)
def generate_baseline(path, output):
    """Generate baseline from current scan results."""
    scanner = SASTScanner()
    scanner.generate_baseline(Path(path), Path(output))


@cli.command()
@click.option(
    "--path", "-p", type=click.Path(exists=True), required=True, help="Path to scan"
)
@click.option(
    "--baseline",
    "-b",
    type=click.Path(exists=True),
    required=True,
    help="Baseline file",
)
@click.option(
    "--fail-on-new", is_flag=True, help="Exit with error if new findings detected"
)
def compare_baseline(path, baseline, fail_on_new):
    """Compare current scan against baseline."""
    scanner = SASTScanner()
    scanner.compare_baseline(Path(path), Path(baseline), fail_on_new)


def _display_results_summary(results: Dict[str, Any]) -> None:
    """Display scan results summary."""
    summary = results["summary"]

    # Create summary table
    table = Table(title="SAST Scan Results")
    table.add_column("Severity", style="cyan")
    table.add_column("Count", style="magenta")

    by_severity = summary["by_severity"]
    table.add_row("CRITICAL", f"[red bold]{by_severity.get('CRITICAL', 0)}[/red bold]")
    table.add_row("HIGH", f"[red]{by_severity['HIGH']}[/red]")
    table.add_row("MEDIUM", f"[yellow]{by_severity['MEDIUM']}[/yellow]")
    table.add_row("LOW", f"[green]{by_severity['LOW']}[/green]")
    table.add_row("INFO", f"[blue]{by_severity['INFO']}[/blue]")
    table.add_row("TOTAL", f"[bold]{summary['total_findings']}[/bold]")

    console.print(table)

    # Display top CWEs if any
    if summary["by_cwe"]:
        console.print("\n[bold]Top CWEs:[/bold]")
        sorted_cwes = sorted(
            summary["by_cwe"].items(), key=lambda x: x[1], reverse=True
        )[:5]
        for cwe, count in sorted_cwes:
            console.print(f"  {cwe}: {count}")

    # Display affected files count
    console.print(f"\n[bold]Files Affected:[/bold] {summary['files_affected']}")


if __name__ == "__main__":
    cli()
