#!/usr/bin/env python3
"""
Architecture Management & Documentation Platform - Main CLI
Issue #40: TOOL-ARCH-001

Main CLI interface for architecture management platform.
Provides commands for ADR management, C4 diagrams, fitness tests, and ASR tracking.

Usage:
    python issue_40_arch_manager.py adr-create --title "Use Microservices"
    python issue_40_arch_manager.py c4-generate --model model.yml --type context
    python issue_40_arch_manager.py fitness-test --rules rules.yml --codebase ./src
    python issue_40_arch_manager.py asr-extract --repo owner/repo --issue 123
"""

import os
import sys
from pathlib import Path

import click
from colorama import Fore, Style, init
from tabulate import tabulate

# Import our modules
from issue_40_adr_manager import ADRManager
from issue_40_asr_tracker import ASRExtractor, ASRTracker
from issue_40_c4_generator import C4Generator
from issue_40_fitness_functions import FitnessTester

# Initialize colorama
init(autoreset=True)


def print_success(message: str) -> None:
    """Print success message."""
    click.echo(f"{Fore.GREEN}✓ {message}{Style.RESET_ALL}")


def print_error(message: str) -> None:
    """Print error message."""
    click.echo(f"{Fore.RED}✗ {message}{Style.RESET_ALL}", err=True)


def print_warning(message: str) -> None:
    """Print warning message."""
    click.echo(f"{Fore.YELLOW}⚠ {message}{Style.RESET_ALL}")


def print_info(message: str) -> None:
    """Print info message."""
    click.echo(f"{Fore.BLUE}ℹ {message}{Style.RESET_ALL}")


@click.group()
@click.version_option(version="1.0.0")
def cli():
    """
    Architecture Management & Documentation Platform

    Manage ADRs, generate C4 diagrams, run fitness tests, and track ASRs.
    """
    pass


# ============================================================================
# ADR Commands
# ============================================================================


@cli.group()
def adr():
    """Architecture Decision Record commands."""
    pass


@adr.command("create")
@click.option("--title", required=True, help="ADR title")
@click.option("--context", required=True, help="Context and problem statement")
@click.option("--decision", required=True, help="The decision made")
@click.option("--consequences", required=True, help="Consequences of the decision")
@click.option("--status", default="proposed", help="ADR status (proposed/accepted)")
@click.option("--deciders", help="Comma-separated list of deciders")
@click.option("--issue", help="GitHub issue URL or number")
@click.option("--adr-dir", default="docs/adr", help="ADR directory")
def adr_create(title, context, decision, consequences, status, deciders, issue, adr_dir):
    """Create a new Architecture Decision Record."""
    try:
        manager = ADRManager(adr_dir=adr_dir)

        deciders_list = None
        if deciders:
            deciders_list = [d.strip() for d in deciders.split(",")]

        adr = manager.create(
            title=title,
            context=context,
            decision=decision,
            consequences=consequences,
            status=status,
            deciders=deciders_list,
            technical_story=issue,
        )

        print_success(f"Created ADR-{adr.number:03d}: {adr.title}")
        print_info(f"File: {adr_dir}/ADR-{adr.number:03d}.md")

    except Exception as e:
        print_error(f"Failed to create ADR: {e}")
        sys.exit(1)


@adr.command("supersede")
@click.option("--adr-number", required=True, type=int, help="ADR number to supersede")
@click.option("--title", required=True, help="New ADR title")
@click.option("--context", required=True, help="New context")
@click.option("--decision", required=True, help="New decision")
@click.option("--adr-dir", default="docs/adr", help="ADR directory")
def adr_supersede(adr_number, title, context, decision, adr_dir):
    """Supersede an existing ADR."""
    try:
        manager = ADRManager(adr_dir=adr_dir)
        new_adr = manager.supersede(adr_number, title, context, decision)

        print_success(f"ADR-{adr_number:03d} superseded by ADR-{new_adr.number:03d}")
        print_info(f"New ADR: {adr_dir}/ADR-{new_adr.number:03d}.md")

    except Exception as e:
        print_error(f"Failed to supersede ADR: {e}")
        sys.exit(1)


@adr.command("list")
@click.option("--status", help="Filter by status")
@click.option("--adr-dir", default="docs/adr", help="ADR directory")
def adr_list(status, adr_dir):
    """List all ADRs."""
    try:
        manager = ADRManager(adr_dir=adr_dir)
        adrs = manager.list_adrs(status_filter=status)

        if not adrs:
            print_warning("No ADRs found")
            return

        # Prepare table data
        headers = ["Number", "Title", "Status", "Date"]
        rows = [[f"ADR-{adr.number:03d}", adr.title, adr.status, adr.date] for adr in adrs]

        print(f"\n{Fore.CYAN}Architecture Decision Records{Style.RESET_ALL}")
        print(tabulate(rows, headers=headers, tablefmt="grid"))
        print(f"\nTotal: {len(adrs)} ADRs")

    except Exception as e:
        print_error(f"Failed to list ADRs: {e}")
        sys.exit(1)


@adr.command("index")
@click.option("--adr-dir", default="docs/adr", help="ADR directory")
@click.option("--output", help="Output file path")
def adr_index(adr_dir, output):
    """Generate ADR index."""
    try:
        manager = ADRManager(adr_dir=adr_dir)
        output_file = output or f"{adr_dir}/INDEX.md"
        index_content = manager.generate_index(output_file)

        print_success(f"Generated ADR index: {output_file}")
        print(f"\n{index_content}")

    except Exception as e:
        print_error(f"Failed to generate index: {e}")
        sys.exit(1)


# ============================================================================
# C4 Diagram Commands
# ============================================================================


@cli.group()
def c4():
    """C4 diagram generation commands."""
    pass


@c4.command("generate")
@click.option("--model", required=True, help="Model file (YAML or DSL)")
@click.option("--output-dir", default="diagrams", help="Output directory")
@click.option("--type", default="context", help="Diagram type (context/container/component)")
@click.option("--format", multiple=True, default=["png"], help="Output formats")
def c4_generate(model, output_dir, type, format):
    """Generate C4 diagrams from model."""
    try:
        generator = C4Generator()
        model_path = Path(model)

        if not model_path.exists():
            print_error(f"Model file not found: {model}")
            sys.exit(1)

        print_info(f"Generating {type} diagram from {model}")

        # Check file extension
        if model_path.suffix in [".yml", ".yaml"]:
            # Parse YAML model
            model_obj = generator.parse_yaml_model(str(model_path))
            results = generator.generate_from_model(
                model_obj, output_dir, diagram_type=type, formats=list(format)
            )
        else:
            # Assume it's a Structurizr DSL file
            results = generator.generate_from_dsl(model, output_dir, formats=list(format))

        # Print results
        for fmt, files in results.items():
            print_success(f"Generated {len(files)} {fmt} file(s)")
            for file in files:
                print_info(f"  - {file}")

    except Exception as e:
        print_error(f"Failed to generate diagrams: {e}")
        sys.exit(1)


# ============================================================================
# Fitness Test Commands
# ============================================================================


@cli.group()
def fitness():
    """Architecture fitness test commands."""
    pass


@fitness.command("test")
@click.option("--rules", required=True, help="Rules file (YAML)")
@click.option("--codebase", default=".", help="Codebase path to test")
@click.option("--report", help="Report output file")
@click.option("--fail-on-error", is_flag=True, help="Exit with error if violations found")
def fitness_test(rules, codebase, report, fail_on_error):
    """Run architecture fitness tests."""
    try:
        tester = FitnessTester(rules_file=rules)

        print_info(f"Running {len(tester.rules)} fitness tests on {codebase}")

        result = tester.test(codebase)

        # Print summary
        print(f"\n{Fore.CYAN}Fitness Test Results{Style.RESET_ALL}")
        print(f"Total Rules: {result.total_rules}")
        print(f"Passed: {Fore.GREEN}{result.passed_rules}{Style.RESET_ALL}")
        print(f"Failed: {Fore.RED}{result.failed_rules}{Style.RESET_ALL}")
        print(f"Success Rate: {result.success_rate:.1f}%")
        print(f"Execution Time: {result.execution_time:.2f}s")
        print(f"Total Violations: {result.violation_count}")

        # Print violations by severity
        for severity in ["ERROR", "WARNING", "INFO"]:
            violations = result.get_violations_by_severity(severity)
            if violations:
                color = Fore.RED if severity == "ERROR" else (
                    Fore.YELLOW if severity == "WARNING" else Fore.BLUE
                )
                print(f"\n{color}{severity}: {len(violations)}{Style.RESET_ALL}")
                for v in violations[:5]:  # Show first 5
                    print(f"  - {v.rule_name}: {v.message}")
                if len(violations) > 5:
                    print(f"  ... and {len(violations) - 5} more")

        # Generate report if requested
        if report:
            report_content = tester.generate_report(result, report)
            print_success(f"Generated report: {report}")

        # Exit with error if violations found and flag set
        if fail_on_error and result.violation_count > 0:
            sys.exit(1)

    except Exception as e:
        print_error(f"Failed to run fitness tests: {e}")
        sys.exit(1)


# ============================================================================
# ASR Commands
# ============================================================================


@cli.group()
def asr():
    """Architecture Significant Requirements commands."""
    pass


@asr.command("extract")
@click.option("--repo", required=True, help="GitHub repository (owner/repo)")
@click.option("--issue", required=True, type=int, help="Issue number")
@click.option("--token", envvar="GITHUB_TOKEN", help="GitHub token")
@click.option("--asr-dir", default="docs/asr", help="ASR directory")
def asr_extract(repo, issue, token, asr_dir):
    """Extract ASR from GitHub issue."""
    try:
        if not token:
            print_error("GitHub token required. Set GITHUB_TOKEN env var or use --token")
            sys.exit(1)

        extractor = ASRExtractor(github_token=token)
        tracker = ASRTracker(asr_dir=asr_dir)

        print_info(f"Extracting ASR from {repo}#{issue}")

        asr = extractor.extract_from_github_issue(repo, issue)

        if not asr:
            print_warning("Issue is not architecturally significant")
            sys.exit(0)

        tracker.save_asr(asr)

        print_success(f"Extracted {asr.id}: {asr.title}")
        print_info(f"Category: {asr.category}")
        print_info(f"Priority: {asr.priority}")
        print_info(f"File: {asr_dir}/{asr.id}.md")

    except Exception as e:
        print_error(f"Failed to extract ASR: {e}")
        sys.exit(1)


@asr.command("list")
@click.option("--category", help="Filter by category")
@click.option("--status", help="Filter by status")
@click.option("--asr-dir", default="docs/asr", help="ASR directory")
def asr_list(category, status, asr_dir):
    """List all ASRs."""
    try:
        tracker = ASRTracker(asr_dir=asr_dir)
        asrs = tracker.list_asrs(category=category, status=status)

        if not asrs:
            print_warning("No ASRs found")
            return

        # Prepare table data
        headers = ["ID", "Title", "Category", "Priority", "Status", "ADRs"]
        rows = [
            [
                asr.id,
                asr.title[:50] + "..." if len(asr.title) > 50 else asr.title,
                asr.category,
                asr.priority,
                asr.status,
                len(asr.related_adrs),
            ]
            for asr in asrs
        ]

        print(f"\n{Fore.CYAN}Architecture Significant Requirements{Style.RESET_ALL}")
        print(tabulate(rows, headers=headers, tablefmt="grid"))
        print(f"\nTotal: {len(asrs)} ASRs")

    except Exception as e:
        print_error(f"Failed to list ASRs: {e}")
        sys.exit(1)


@asr.command("link")
@click.option("--asr-id", required=True, help="ASR ID")
@click.option("--adr-number", required=True, type=int, help="ADR number")
@click.option("--asr-dir", default="docs/asr", help="ASR directory")
def asr_link(asr_id, adr_number, asr_dir):
    """Link ASR to ADR."""
    try:
        tracker = ASRTracker(asr_dir=asr_dir)

        if tracker.link_asr_to_adr(asr_id, adr_number):
            print_success(f"Linked {asr_id} to ADR-{adr_number:03d}")
        else:
            print_error(f"ASR {asr_id} not found")
            sys.exit(1)

    except Exception as e:
        print_error(f"Failed to link ASR: {e}")
        sys.exit(1)


@asr.command("matrix")
@click.option("--asr-dir", default="docs/asr", help="ASR directory")
@click.option("--output", help="Output file path")
def asr_matrix(asr_dir, output):
    """Generate ASR-to-ADR traceability matrix."""
    try:
        tracker = ASRTracker(asr_dir=asr_dir)
        output_file = output or f"{asr_dir}/TRACEABILITY.md"

        matrix = tracker.generate_traceability_matrix(output_file)

        print_success(f"Generated traceability matrix: {output_file}")
        print(f"\n{matrix}")

    except Exception as e:
        print_error(f"Failed to generate matrix: {e}")
        sys.exit(1)


# ============================================================================
# Utility Commands
# ============================================================================


@cli.command("init")
@click.option("--project-dir", default=".", help="Project directory")
def init_project(project_dir):
    """Initialize architecture documentation structure."""
    try:
        project_path = Path(project_dir)

        # Create directory structure
        directories = [
            "docs/adr",
            "docs/asr",
            "docs/architecture/diagrams",
            "docs/architecture/models",
        ]

        for dir_path in directories:
            full_path = project_path / dir_path
            full_path.mkdir(parents=True, exist_ok=True)
            print_success(f"Created directory: {dir_path}")

        # Create initial ADR
        manager = ADRManager(adr_dir=str(project_path / "docs/adr"))
        adr = manager.create(
            title="Record Architecture Decisions",
            context="We need to document architecture decisions for future reference.",
            decision="Use Architecture Decision Records (ADRs) to document decisions.",
            consequences=(
                "ADRs will provide a historical record of decisions and their context."
            ),
            status="accepted",
        )

        print_success(f"Created initial ADR: ADR-{adr.number:03d}")
        print_info("\nArchitecture documentation structure initialized!")

    except Exception as e:
        print_error(f"Failed to initialize project: {e}")
        sys.exit(1)


@cli.command("status")
@click.option("--project-dir", default=".", help="Project directory")
def show_status(project_dir):
    """Show architecture documentation status."""
    try:
        project_path = Path(project_dir)

        print(f"\n{Fore.CYAN}Architecture Documentation Status{Style.RESET_ALL}\n")

        # Check ADRs
        adr_dir = project_path / "docs/adr"
        if adr_dir.exists():
            manager = ADRManager(adr_dir=str(adr_dir))
            adrs = manager.list_adrs()
            print(f"ADRs: {len(adrs)}")

            # Count by status
            statuses = {}
            for adr in adrs:
                statuses[adr.status] = statuses.get(adr.status, 0) + 1
            for status, count in sorted(statuses.items()):
                print(f"  - {status}: {count}")
        else:
            print("ADRs: Not initialized")

        # Check ASRs
        asr_dir = project_path / "docs/asr"
        if asr_dir.exists():
            tracker = ASRTracker(asr_dir=str(asr_dir))
            asrs = tracker.list_asrs()
            print(f"\nASRs: {len(asrs)}")

            # Count by category
            categories = {}
            for asr in asrs:
                categories[asr.category] = categories.get(asr.category, 0) + 1
            for category, count in sorted(categories.items()):
                print(f"  - {category}: {count}")
        else:
            print("\nASRs: Not initialized")

        # Check diagrams
        diagram_dir = project_path / "docs/architecture/diagrams"
        if diagram_dir.exists():
            diagrams = list(diagram_dir.glob("*.png")) + list(diagram_dir.glob("*.svg"))
            print(f"\nDiagrams: {len(diagrams)}")
        else:
            print("\nDiagrams: Not initialized")

    except Exception as e:
        print_error(f"Failed to show status: {e}")
        sys.exit(1)


if __name__ == "__main__":
    cli()
