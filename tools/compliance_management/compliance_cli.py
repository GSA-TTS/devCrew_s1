#!/usr/bin/env python3
"""
Compliance CLI for policy evaluation and compliance management.

Command-line interface for devCrew_s1 TOOL-SEC-011 compliance management platform.
"""

import argparse
import json
import sys
from pathlib import Path
from typing import List, Optional

from .policy_engine import PolicyEngine
from .compliance_manager import ComplianceManager, ComplianceFramework
from .policy_validator import PolicyValidator
from .regulatory_mapper import RegulatoryMapper
from .audit_reporter import AuditReporter, ReportFormat


def create_parser() -> argparse.ArgumentParser:
    """Create CLI argument parser."""
    parser = argparse.ArgumentParser(
        prog="compliance-cli",
        description="Compliance Management & Policy Enforcement Platform",
    )
    parser.add_argument(
        "--version", action="version", version="%(prog)s 1.0.0"
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # evaluate-policy command
    eval_parser = subparsers.add_parser(
        "evaluate-policy", help="Evaluate input against a policy"
    )
    eval_parser.add_argument(
        "--policy", "-p", required=True, help="Policy file path or name"
    )
    eval_parser.add_argument(
        "--input", "-i", required=True, help="Input data file (JSON)"
    )
    eval_parser.add_argument(
        "--output", "-o", help="Output file for results"
    )
    eval_parser.add_argument(
        "--format", "-f", choices=["json", "text"], default="json"
    )

    # validate-compliance command
    validate_parser = subparsers.add_parser(
        "validate-compliance", help="Validate compliance against frameworks"
    )
    validate_parser.add_argument(
        "--input", "-i", required=True, help="System data file (JSON)"
    )
    validate_parser.add_argument(
        "--frameworks", "-fw", nargs="+",
        choices=["gdpr", "hipaa", "fedramp", "soc2", "iso_27001", "nist_800_53", "all"],
        default=["all"], help="Frameworks to validate"
    )
    validate_parser.add_argument(
        "--output", "-o", help="Output file for results"
    )
    validate_parser.add_argument(
        "--format", "-f", choices=["json", "text"], default="json"
    )

    # generate-report command
    report_parser = subparsers.add_parser(
        "generate-report", help="Generate compliance report"
    )
    report_parser.add_argument(
        "--input", "-i", required=True, help="System data file (JSON)"
    )
    report_parser.add_argument(
        "--output", "-o", required=True, help="Output report file"
    )
    report_parser.add_argument(
        "--format", "-f", choices=["html", "csv", "json", "pdf"],
        default="html", help="Report format"
    )
    report_parser.add_argument(
        "--org", help="Organization name for report"
    )
    report_parser.add_argument(
        "--frameworks", "-fw", nargs="+", default=["all"],
        help="Frameworks to include"
    )

    # map-controls command
    map_parser = subparsers.add_parser(
        "map-controls", help="Map policies to regulatory controls"
    )
    map_parser.add_argument(
        "--rule", "-r", help="Specific rule to map"
    )
    map_parser.add_argument(
        "--framework", "-fw", help="Filter by framework"
    )
    map_parser.add_argument(
        "--output", "-o", help="Output file for mapping"
    )
    map_parser.add_argument(
        "--matrix", action="store_true", help="Generate full compliance matrix"
    )

    # test-policy command
    test_parser = subparsers.add_parser(
        "test-policy", help="Test policy syntax and rules"
    )
    test_parser.add_argument(
        "--policy", "-p", required=True, help="Policy file to test"
    )
    test_parser.add_argument(
        "--tests", "-t", help="Test cases file (YAML)"
    )
    test_parser.add_argument(
        "--verbose", "-v", action="store_true", help="Verbose output"
    )

    # list-rules command
    list_parser = subparsers.add_parser(
        "list-rules", help="List available rules"
    )
    list_parser.add_argument(
        "--format", "-f", choices=["json", "text"], default="text"
    )

    # list-frameworks command
    subparsers.add_parser(
        "list-frameworks", help="List supported compliance frameworks"
    )

    return parser


def cmd_evaluate_policy(args: argparse.Namespace) -> int:
    """Execute evaluate-policy command."""
    try:
        input_path = Path(args.input)
        if not input_path.exists():
            print(f"Error: Input file not found: {args.input}", file=sys.stderr)
            return 1

        with open(input_path) as f:
            input_data = json.load(f)

        engine = PolicyEngine()

        policy_path = Path(args.policy)
        if policy_path.exists():
            engine.load_policy(policy_path)
            policy_name = policy_path.stem
        else:
            # Use as policy name with default content
            default_policy = "package compliance\ndefault allow = false"
            engine.load_policy_from_string(default_policy, args.policy)
            policy_name = args.policy

        result = engine.evaluate(policy_name, input_data)

        if args.format == "json":
            output = json.dumps(result.to_dict(), indent=2)
        else:
            output = format_policy_result_text(result)

        if args.output:
            Path(args.output).write_text(output)
            print(f"Results written to: {args.output}")
        else:
            print(output)

        return 0 if result.decision.value == "allow" else 1

    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in input file: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


def cmd_validate_compliance(args: argparse.Namespace) -> int:
    """Execute validate-compliance command."""
    try:
        input_path = Path(args.input)
        if not input_path.exists():
            print(f"Error: Input file not found: {args.input}", file=sys.stderr)
            return 1

        with open(input_path) as f:
            input_data = json.load(f)

        manager = ComplianceManager()

        if "all" in args.frameworks:
            frameworks = list(ComplianceFramework)
        else:
            frameworks = [ComplianceFramework(fw) for fw in args.frameworks]

        results = {}
        for fw in frameworks:
            results[fw] = manager.assess_compliance(fw, input_data)

        if args.format == "json":
            output_data = {
                fw.value: score.to_dict() for fw, score in results.items()
            }
            output = json.dumps(output_data, indent=2)
        else:
            output = format_compliance_text(results)

        if args.output:
            Path(args.output).write_text(output)
            print(f"Results written to: {args.output}")
        else:
            print(output)

        all_compliant = all(
            s.score >= 100 for s in results.values()
        )
        return 0 if all_compliant else 1

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


def cmd_generate_report(args: argparse.Namespace) -> int:
    """Execute generate-report command."""
    try:
        input_path = Path(args.input)
        if not input_path.exists():
            print(f"Error: Input file not found: {args.input}", file=sys.stderr)
            return 1

        with open(input_path) as f:
            input_data = json.load(f)

        manager = ComplianceManager()

        if "all" in args.frameworks:
            frameworks = list(ComplianceFramework)
        else:
            frameworks = [ComplianceFramework(fw) for fw in args.frameworks]

        scores = {}
        for fw in frameworks:
            scores[fw] = manager.assess_compliance(fw, input_data)

        org_name = args.org or "Organization"
        reporter = AuditReporter(organization_name=org_name)

        format_map = {
            "html": ReportFormat.HTML,
            "csv": ReportFormat.CSV,
            "json": ReportFormat.JSON,
            "pdf": ReportFormat.PDF,
        }
        report_format = format_map.get(args.format, ReportFormat.HTML)

        output_path = Path(args.output)
        reporter.generate_report(scores, report_format, output_path)

        print(f"Report generated: {args.output}")
        return 0

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


def cmd_map_controls(args: argparse.Namespace) -> int:
    """Execute map-controls command."""
    try:
        mapper = RegulatoryMapper()

        if args.matrix:
            frameworks = [args.framework] if args.framework else None
            matrix = mapper.generate_compliance_matrix(frameworks)
            output = json.dumps(matrix.to_dict(), indent=2)
        elif args.rule:
            mapping = mapper.get_mapping(args.rule)
            if mapping:
                output = json.dumps(mapping.to_dict(), indent=2)
            else:
                print(f"No mapping found for rule: {args.rule}", file=sys.stderr)
                return 1
        else:
            # List all mappings
            all_mappings = {}
            for rule in mapper._mappings:
                m = mapper.get_mapping(rule)
                if m:
                    all_mappings[rule] = m.to_dict()
            output = json.dumps(all_mappings, indent=2)

        if args.output:
            Path(args.output).write_text(output)
            print(f"Mapping written to: {args.output}")
        else:
            print(output)

        return 0

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


def cmd_test_policy(args: argparse.Namespace) -> int:
    """Execute test-policy command."""
    try:
        policy_path = Path(args.policy)
        if not policy_path.exists():
            print(f"Error: Policy file not found: {args.policy}", file=sys.stderr)
            return 1

        validator = PolicyValidator()
        result = validator.validate_file(policy_path)

        print(f"Policy: {result.policy_name}")
        print(f"Type: {result.policy_type}")
        print(f"Status: {result.status.value}")
        print(f"Errors: {result.error_count}")
        print(f"Warnings: {result.warning_count}")

        if args.verbose and result.issues:
            print("\nIssues:")
            for issue in result.issues:
                print(f"  Line {issue.line}: [{issue.severity}] {issue.message}")

        if args.tests:
            test_path = Path(args.tests)
            if test_path.exists():
                test_content = test_path.read_text()
                tests = validator.create_test_from_yaml(test_content)
                policy_content = policy_path.read_text()
                test_results = validator.run_tests(policy_content, tests)

                print(f"\nTest Results: {len(test_results)} tests")
                passed = sum(1 for t in test_results if t.passed)
                print(f"Passed: {passed}/{len(test_results)}")

                if args.verbose:
                    for tr in test_results:
                        status = "PASS" if tr.passed else "FAIL"
                        print(f"  {tr.test_name}: {status}")

        return 0 if result.is_valid else 1

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


def cmd_list_rules(args: argparse.Namespace) -> int:
    """Execute list-rules command."""
    engine = PolicyEngine()
    rules = engine.get_available_rules()

    if args.format == "json":
        print(json.dumps(rules, indent=2))
    else:
        print("Available Rules:")
        for rule in sorted(rules):
            print(f"  - {rule}")

    return 0


def cmd_list_frameworks() -> int:
    """Execute list-frameworks command."""
    print("Supported Compliance Frameworks:")
    for fw in ComplianceFramework:
        print(f"  - {fw.value}: {fw.name.replace('_', ' ')}")
    return 0


def format_policy_result_text(result) -> str:
    """Format policy result as text."""
    lines = [
        f"Policy: {result.policy_name}",
        f"Decision: {result.decision.value}",
        f"Evaluation Time: {result.evaluation_time_ms:.2f}ms",
    ]
    if result.violations:
        lines.append("Violations:")
        for v in result.violations:
            lines.append(f"  - [{v.get('severity', 'unknown')}] {v.get('message', '')}")
    return "\n".join(lines)


def format_compliance_text(results) -> str:
    """Format compliance results as text."""
    lines = ["Compliance Assessment Results", "=" * 40]
    for fw, score in results.items():
        lines.extend([
            f"\n{fw.value.upper()}",
            f"  Score: {score.score:.1f}%",
            f"  Status: {score.status.value}",
            f"  Controls: {score.passed_controls}/{score.total_controls} passed",
        ])
    return "\n".join(lines)


def main(argv: Optional[List[str]] = None) -> int:
    """Main entry point."""
    parser = create_parser()
    args = parser.parse_args(argv)

    if not args.command:
        parser.print_help()
        return 0

    commands = {
        "evaluate-policy": cmd_evaluate_policy,
        "validate-compliance": cmd_validate_compliance,
        "generate-report": cmd_generate_report,
        "map-controls": cmd_map_controls,
        "test-policy": cmd_test_policy,
        "list-rules": lambda a: cmd_list_rules(a),
        "list-frameworks": lambda a: cmd_list_frameworks(),
    }

    handler = commands.get(args.command)
    if handler:
        return handler(args)

    parser.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
