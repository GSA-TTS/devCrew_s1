#!/usr/bin/env python3
"""
CLI for Secrets Scanner - devCrew_s1 TOOL-SEC-006.

Commands: scan, baseline, verify, rotate
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Optional

from .baseline_manager import BaselineManager
from .git_scanner import GitScanner
from .pattern_manager import PatternManager, PatternSeverity
from .remediation_guide import RemediationGuide
from .secret_scanner import ScanResult, SecretScanner
from .verification_engine import VerificationEngine


def create_parser() -> argparse.ArgumentParser:
    """Create argument parser."""
    parser = argparse.ArgumentParser(
        prog="secrets-scanner",
        description="Secrets Scanner & Detection Platform - devCrew_s1",
    )
    parser.add_argument(
        "--version", action="version", version="%(prog)s 1.0.0"
    )

    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # Scan command
    scan_parser = subparsers.add_parser("scan", help="Scan for secrets")
    scan_parser.add_argument(
        "path", nargs="?", default=".", help="Path to scan (default: current directory)"
    )
    scan_parser.add_argument(
        "--recursive", "-r", action="store_true", default=True,
        help="Scan recursively (default: True)"
    )
    scan_parser.add_argument(
        "--no-recursive", action="store_false", dest="recursive",
        help="Do not scan recursively"
    )
    scan_parser.add_argument(
        "--baseline", "-b", type=str, help="Baseline file path"
    )
    scan_parser.add_argument(
        "--output", "-o", type=str, help="Output file path"
    )
    scan_parser.add_argument(
        "--format", "-f", choices=["json", "sarif", "text"],
        default="text", help="Output format"
    )
    scan_parser.add_argument(
        "--severity", "-s", choices=["critical", "high", "medium", "low"],
        help="Minimum severity to report"
    )
    scan_parser.add_argument(
        "--categories", "-c", nargs="+", help="Categories to include"
    )
    scan_parser.add_argument(
        "--entropy", action="store_true", help="Include entropy-based detection"
    )
    scan_parser.add_argument(
        "--git-history", action="store_true", help="Scan git history"
    )
    scan_parser.add_argument(
        "--commits", type=int, default=100,
        help="Number of commits to scan (default: 100)"
    )

    # Baseline command
    baseline_parser = subparsers.add_parser(
        "baseline", help="Manage baseline file"
    )
    baseline_parser.add_argument(
        "action", choices=["create", "update", "audit", "export"],
        help="Baseline action"
    )
    baseline_parser.add_argument(
        "--path", "-p", type=str, default=".",
        help="Path to scan"
    )
    baseline_parser.add_argument(
        "--baseline", "-b", type=str, default=".secrets.baseline",
        help="Baseline file path"
    )
    baseline_parser.add_argument(
        "--output", "-o", type=str, help="Output file for export"
    )

    # Verify command
    verify_parser = subparsers.add_parser(
        "verify", help="Verify detected secrets"
    )
    verify_parser.add_argument(
        "path", nargs="?", default=".", help="Path to scan"
    )
    verify_parser.add_argument(
        "--live", action="store_true",
        help="Perform live verification (makes API calls)"
    )
    verify_parser.add_argument(
        "--output", "-o", type=str, help="Output file"
    )
    verify_parser.add_argument(
        "--format", "-f", choices=["json", "text"], default="text",
        help="Output format"
    )

    # Rotate command
    rotate_parser = subparsers.add_parser(
        "rotate", help="Get rotation guidance"
    )
    rotate_parser.add_argument(
        "path", nargs="?", default=".", help="Path to scan"
    )
    rotate_parser.add_argument(
        "--pattern", "-p", type=str, help="Specific pattern to get guidance for"
    )
    rotate_parser.add_argument(
        "--output", "-o", type=str, help="Output file"
    )
    rotate_parser.add_argument(
        "--format", "-f", choices=["json", "text"], default="text",
        help="Output format"
    )

    # Patterns command
    patterns_parser = subparsers.add_parser(
        "patterns", help="List available patterns"
    )
    patterns_parser.add_argument(
        "--category", "-c", type=str, help="Filter by category"
    )
    patterns_parser.add_argument(
        "--severity", "-s", choices=["critical", "high", "medium", "low"],
        help="Filter by severity"
    )
    patterns_parser.add_argument(
        "--export", type=str, help="Export patterns to file"
    )

    return parser


def cmd_scan(args: argparse.Namespace) -> int:
    """Execute scan command."""
    scanner = SecretScanner()
    path = Path(args.path)

    # Scan filesystem
    if path.is_file():
        findings = scanner.scan_file(path)
        result = ScanResult(findings=findings, files_scanned=1)
    else:
        result = scanner.scan_directory(path, recursive=args.recursive)

    # Add entropy detection if requested
    if args.entropy and path.is_dir():
        for file_path in path.rglob("*"):
            if file_path.is_file():
                try:
                    content = file_path.read_text(errors="ignore")
                    entropy_findings = scanner.scan_high_entropy_strings(
                        content, str(file_path)
                    )
                    result.findings.extend(entropy_findings)
                except (OSError, UnicodeDecodeError):
                    pass

    # Scan git history if requested
    if args.git_history:
        try:
            git_scanner = GitScanner(path)
            branch_scan = git_scanner.scan_branch(limit=args.commits)
            for commit_scan in branch_scan.commit_scans:
                result.findings.extend(commit_scan.findings)
        except ValueError as e:
            print(f"Warning: {e}", file=sys.stderr)

    # Apply baseline filtering
    if args.baseline:
        baseline_mgr = BaselineManager(args.baseline)
        try:
            baseline_mgr.load()
            result.findings = baseline_mgr.filter_baselined(result.findings)
        except (FileNotFoundError, json.JSONDecodeError):
            pass

    # Filter by severity
    if args.severity:
        severity = PatternSeverity(args.severity)
        result.findings = scanner.filter_findings(
            result.findings, min_severity=severity
        )

    # Filter by categories
    if args.categories:
        result.findings = scanner.filter_findings(
            result.findings, categories=args.categories
        )

    # Deduplicate
    result.findings = scanner.deduplicate_findings(result.findings)

    # Output
    output = format_output(result, args.format)

    if args.output:
        Path(args.output).write_text(output)
        print(f"Results written to {args.output}")
    else:
        print(output)

    # Return non-zero if findings exist
    return 1 if result.findings else 0


def cmd_baseline(args: argparse.Namespace) -> int:
    """Execute baseline command."""
    baseline_mgr = BaselineManager(args.baseline)
    scanner = SecretScanner()

    if args.action == "create":
        result = scanner.scan_directory(args.path)
        baseline_mgr.create_from_scan(result)
        baseline_mgr.save()
        print(f"Baseline created with {baseline_mgr.baseline.entry_count} entries")

    elif args.action == "update":
        baseline_mgr.load()
        result = scanner.scan_directory(args.path)
        baseline_mgr.update_from_scan(result)
        baseline_mgr.save()
        print(f"Baseline updated with {baseline_mgr.baseline.entry_count} entries")

    elif args.action == "audit":
        baseline_mgr.load()
        result = scanner.scan_directory(args.path)
        audit = baseline_mgr.audit_baseline(result)
        print(json.dumps(audit, indent=2))

    elif args.action == "export":
        baseline_mgr.load()
        fps = baseline_mgr.export_false_positives()
        output = json.dumps(fps, indent=2)
        if args.output:
            Path(args.output).write_text(output)
        else:
            print(output)

    return 0


def cmd_verify(args: argparse.Namespace) -> int:
    """Execute verify command."""
    scanner = SecretScanner()
    verifier = VerificationEngine(verify_live=args.live)

    result = scanner.scan_directory(args.path)
    results = verifier.verify_all(result.findings)
    report = verifier.generate_report(results)

    if args.format == "json":
        output = json.dumps(report, indent=2)
    else:
        output = format_verification_text(results)

    if args.output:
        Path(args.output).write_text(output)
    else:
        print(output)

    return 0


def cmd_rotate(args: argparse.Namespace) -> int:
    """Execute rotate command."""
    guide = RemediationGuide()

    if args.pattern:
        workflow = guide.get_workflow(args.pattern)
        if workflow:
            if args.format == "json":
                output = json.dumps(workflow.to_dict(), indent=2)
            else:
                output = format_workflow_text(workflow)
        else:
            print(f"No workflow found for pattern: {args.pattern}")
            return 1
    else:
        scanner = SecretScanner()
        result = scanner.scan_directory(args.path)
        reports = guide.batch_report(result.findings)
        summary = guide.get_summary(reports)

        if args.format == "json":
            output = json.dumps(summary, indent=2)
        else:
            output = format_remediation_text(reports)

    if args.output:
        Path(args.output).write_text(output)
    else:
        print(output)

    return 0


def cmd_patterns(args: argparse.Namespace) -> int:
    """Execute patterns command."""
    pm = PatternManager()
    patterns = pm.get_all_patterns()

    if args.category:
        patterns = [p for p in patterns if p.category == args.category]

    if args.severity:
        severity = PatternSeverity(args.severity)
        patterns = [p for p in patterns if p.severity == severity]

    if args.export:
        data = pm.export_patterns()
        Path(args.export).write_text(json.dumps(data, indent=2))
        print(f"Exported {len(patterns)} patterns to {args.export}")
    else:
        print(f"Available patterns: {len(patterns)}\n")
        for p in patterns:
            print(f"  [{p.severity.value.upper()}] {p.name}")
            print(f"    Category: {p.category}")
            print(f"    Description: {p.description}")
            print()

    return 0


def format_output(result: ScanResult, fmt: str) -> str:
    """Format scan result for output."""
    if fmt == "json":
        return json.dumps(result.to_dict(), indent=2)
    elif fmt == "sarif":
        return json.dumps(result.to_sarif(), indent=2)
    else:
        lines = [
            "=" * 60,
            "SECRETS SCAN RESULTS - devCrew_s1",
            "=" * 60,
            f"Files scanned: {result.files_scanned}",
            f"Scan duration: {result.scan_duration:.2f}s",
            f"Total findings: {result.finding_count}",
            f"Critical: {result.critical_count}",
            f"High: {result.high_count}",
            "",
        ]

        if result.findings:
            lines.append("FINDINGS:")
            lines.append("-" * 40)
            for f in result.findings:
                lines.append(f"[{f.severity.value.upper()}] {f.pattern_name}")
                lines.append(f"  File: {f.file_path}:{f.line_number}")
                lines.append(f"  Description: {f.pattern_description}")
                if f.entropy:
                    lines.append(f"  Entropy: {f.entropy:.2f}")
                lines.append("")

        if result.errors:
            lines.append("ERRORS:")
            for e in result.errors:
                lines.append(f"  - {e}")

        return "\n".join(lines)


def format_verification_text(results: list) -> str:
    """Format verification results as text."""
    lines = ["VERIFICATION RESULTS", "=" * 40, ""]

    for r in results:
        lines.append(f"Pattern: {r.finding.pattern_name}")
        lines.append(f"Status: {r.status.value}")
        lines.append(f"Message: {r.message}")
        lines.append("")

    return "\n".join(lines)


def format_workflow_text(workflow) -> str:
    """Format rotation workflow as text."""
    lines = [
        f"ROTATION WORKFLOW: {workflow.service_name}",
        "=" * 40,
        f"Pattern: {workflow.pattern_name}",
        f"Estimated time: {workflow.estimated_time}",
        "",
        "STEPS:",
    ]

    for step in workflow.steps:
        lines.append(f"  {step.order}. {step.action}")
        lines.append(f"     {step.description}")
        if step.command:
            lines.append(f"     Command: {step.command}")
        lines.append("")

    if workflow.notes:
        lines.append(f"Notes: {workflow.notes}")

    return "\n".join(lines)


def format_remediation_text(reports: list) -> str:
    """Format remediation reports as text."""
    lines = ["REMEDIATION REPORT", "=" * 40, ""]

    for r in reports:
        lines.append(f"[{r.priority.name}] {r.finding.pattern_name}")
        lines.append(f"  File: {r.finding.file_path}")
        lines.append(f"  Score: {r.priority_score}")
        lines.append(f"  Impact: {r.impact_assessment[:100]}...")
        lines.append("")

    return "\n".join(lines)


def main(argv: Optional[list] = None) -> int:
    """Main entry point."""
    parser = create_parser()
    args = parser.parse_args(argv)

    if not args.command:
        parser.print_help()
        return 0

    commands = {
        "scan": cmd_scan,
        "baseline": cmd_baseline,
        "verify": cmd_verify,
        "rotate": cmd_rotate,
        "patterns": cmd_patterns,
    }

    return commands[args.command](args)


if __name__ == "__main__":
    sys.exit(main())
