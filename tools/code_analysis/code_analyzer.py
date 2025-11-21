"""
Code Analyzer - Main CLI Interface.

Integrates all code analysis components into a unified command-line tool.
"""

import argparse
import logging
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional

from complexity_analyzer import ComplexityAnalyzer
from code_smell_detector import CodeSmellDetector, CodeSmellConfig
from tech_debt_tracker import TechDebtTracker
from refactoring_advisor import RefactoringAdvisor
from metrics_reporter import MetricsReporter, ReportFormat


logger = logging.getLogger(__name__)


class CodeAnalyzer:
    """Main code analysis CLI application."""

    def __init__(
        self,
        cyclomatic_threshold: int = 10,
        cognitive_threshold: int = 15,
        max_method_lines: int = 30,
        max_class_lines: int = 300,
        max_parameters: int = 5,
        debt_storage: Optional[str] = None,
    ) -> None:
        """
        Initialize the code analyzer.

        Args:
            cyclomatic_threshold: Max cyclomatic complexity
            cognitive_threshold: Max cognitive complexity
            max_method_lines: Max lines per method
            max_class_lines: Max lines per class
            max_parameters: Max function parameters
            debt_storage: Path to store tech debt items
        """
        self.complexity_analyzer = ComplexityAnalyzer(
            cyclomatic_threshold=cyclomatic_threshold,
            cognitive_threshold=cognitive_threshold,
            max_parameters=max_parameters,
        )

        smell_config = CodeSmellConfig(
            max_method_lines=max_method_lines,
            max_class_lines=max_class_lines,
            max_parameters=max_parameters,
        )
        self.smell_detector = CodeSmellDetector(config=smell_config)
        self.debt_tracker = TechDebtTracker(storage_path=debt_storage)
        self.refactoring_advisor = RefactoringAdvisor()
        self.reporter = MetricsReporter()

    def analyze_file(self, filepath: str | Path) -> Dict[str, Any]:
        """
        Analyze a single Python file.

        Args:
            filepath: Path to Python file

        Returns:
            Complete analysis results
        """
        filepath = Path(filepath)
        if not filepath.exists():
            return {"error": f"File not found: {filepath}"}

        if not filepath.suffix == ".py":
            return {"error": f"Not a Python file: {filepath}"}

        # Run complexity analysis
        complexity_result = self.complexity_analyzer.analyze_file(filepath)

        # Run smell detection
        smell_result = self.smell_detector.detect_file(filepath)

        # Get refactoring suggestions
        suggestions = self.refactoring_advisor.analyze(
            smells=smell_result.get("smells", []),
            complexity_violations=complexity_result.get("violations", []),
        )
        refactoring_result = self.refactoring_advisor.to_dict(suggestions)

        # Import findings to debt tracker
        self.debt_tracker.import_from_analysis(
            smells=smell_result.get("smells", []),
            complexity_violations=complexity_result.get("violations", []),
        )

        # Scan for TODOs/FIXMEs
        self.debt_tracker.scan_file(filepath)

        return {
            "filename": str(filepath),
            "complexity": complexity_result,
            "smells": smell_result,
            "refactoring": refactoring_result,
            "tech_debt": self.debt_tracker.to_dict(),
        }

    def analyze_directory(
        self,
        directory: str | Path,
        exclude_patterns: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Analyze all Python files in a directory.

        Args:
            directory: Directory to analyze
            exclude_patterns: Patterns to exclude (e.g., ['test_*', '*_test.py'])

        Returns:
            Aggregated analysis results
        """
        directory = Path(directory)
        if not directory.is_dir():
            return {"error": f"Not a directory: {directory}"}

        exclude_patterns = exclude_patterns or []
        results: List[Dict[str, Any]] = []
        total_violations = []
        total_smells = []
        total_suggestions = []

        for filepath in directory.rglob("*.py"):
            # Skip excluded patterns
            if any(filepath.match(p) for p in exclude_patterns):
                continue

            # Skip __pycache__ and virtual environments
            if "__pycache__" in str(filepath) or "venv" in str(filepath):
                continue

            result = self.analyze_file(filepath)
            results.append(result)

            # Aggregate results
            if "complexity" in result:
                violations = result["complexity"].get("violations", [])
                for v in violations:
                    v["file"] = str(filepath)
                total_violations.extend(violations)

            if "smells" in result:
                total_smells.extend(result["smells"].get("smells", []))

            if "refactoring" in result:
                total_suggestions.extend(
                    result["refactoring"].get("suggestions", [])
                )

        # Calculate aggregate summary
        summary = self._aggregate_summary(results)

        return {
            "directory": str(directory),
            "files_analyzed": len(results),
            "summary": summary,
            "violations": total_violations,
            "smells": total_smells,
            "suggestions": total_suggestions,
            "tech_debt": self.debt_tracker.to_dict(),
            "file_results": results,
        }

    def generate_report(
        self,
        analysis_result: Dict[str, Any],
        format: ReportFormat = ReportFormat.TEXT,
        output_path: Optional[str] = None,
    ) -> str:
        """
        Generate a report from analysis results.

        Args:
            analysis_result: Results from analyze_file or analyze_directory
            format: Output format
            output_path: Optional path to save report

        Returns:
            Generated report string
        """
        # Prepare data for reporter
        report_data = {
            "summary": analysis_result.get("summary", {}),
            "violations": analysis_result.get("violations", []),
            "smells": analysis_result.get("smells", []),
            "suggestions": analysis_result.get("suggestions", []),
            "tech_debt": analysis_result.get("tech_debt", {}),
        }

        return self.reporter.generate(report_data, format, output_path)

    def _aggregate_summary(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Aggregate summary from multiple file results."""
        total_functions = 0
        total_violations = 0
        total_smells = 0
        total_loc = 0
        max_cyclomatic = 0
        max_cognitive = 0

        for result in results:
            if "complexity" in result:
                summary = result["complexity"].get("summary", {})
                total_functions += summary.get("total_functions", 0)
                total_loc += summary.get("total_loc", 0)
                max_cyclomatic = max(
                    max_cyclomatic, summary.get("max_cyclomatic", 0)
                )
                max_cognitive = max(
                    max_cognitive, summary.get("max_cognitive", 0)
                )
                total_violations += len(
                    result["complexity"].get("violations", [])
                )

            if "smells" in result:
                total_smells += result["smells"].get("summary", {}).get("total", 0)

        return {
            "files_analyzed": len(results),
            "total_functions": total_functions,
            "total_lines_of_code": total_loc,
            "total_violations": total_violations,
            "total_smells": total_smells,
            "max_cyclomatic_complexity": max_cyclomatic,
            "max_cognitive_complexity": max_cognitive,
        }


def setup_logging(verbose: bool = False) -> None:
    """Setup logging configuration."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )


def main() -> int:
    """Main entry point for CLI."""
    parser = argparse.ArgumentParser(
        description="Code Analysis & Quality Metrics Platform",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s analyze path/to/file.py
  %(prog)s analyze src/ --format html --output report.html
  %(prog)s analyze . --exclude 'test_*' --cyclomatic-threshold 15
        """,
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Analyze command
    analyze_parser = subparsers.add_parser(
        "analyze", help="Analyze Python code"
    )
    analyze_parser.add_argument(
        "path", help="File or directory to analyze"
    )
    analyze_parser.add_argument(
        "--format", "-f",
        choices=["json", "html", "text", "markdown"],
        default="text",
        help="Output format (default: text)",
    )
    analyze_parser.add_argument(
        "--output", "-o",
        help="Output file path",
    )
    analyze_parser.add_argument(
        "--cyclomatic-threshold",
        type=int,
        default=10,
        help="Max cyclomatic complexity (default: 10)",
    )
    analyze_parser.add_argument(
        "--cognitive-threshold",
        type=int,
        default=15,
        help="Max cognitive complexity (default: 15)",
    )
    analyze_parser.add_argument(
        "--max-method-lines",
        type=int,
        default=30,
        help="Max lines per method (default: 30)",
    )
    analyze_parser.add_argument(
        "--max-parameters",
        type=int,
        default=5,
        help="Max function parameters (default: 5)",
    )
    analyze_parser.add_argument(
        "--exclude",
        nargs="*",
        default=[],
        help="Patterns to exclude",
    )
    analyze_parser.add_argument(
        "--debt-storage",
        help="Path to store technical debt items",
    )
    analyze_parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose output",
    )

    # Debt command
    debt_parser = subparsers.add_parser(
        "debt", help="Manage technical debt"
    )
    debt_parser.add_argument(
        "action",
        choices=["list", "scan", "summary"],
        help="Debt action",
    )
    debt_parser.add_argument(
        "--path", "-p",
        help="Path to scan",
    )
    debt_parser.add_argument(
        "--storage",
        default=".tech_debt.json",
        help="Path to debt storage file",
    )

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    setup_logging(getattr(args, "verbose", False))

    if args.command == "analyze":
        analyzer = CodeAnalyzer(
            cyclomatic_threshold=args.cyclomatic_threshold,
            cognitive_threshold=args.cognitive_threshold,
            max_method_lines=args.max_method_lines,
            max_parameters=args.max_parameters,
            debt_storage=args.debt_storage,
        )

        path = Path(args.path)
        if path.is_file():
            result = analyzer.analyze_file(path)
        else:
            result = analyzer.analyze_directory(path, args.exclude)

        # Generate report
        format_map = {
            "json": ReportFormat.JSON,
            "html": ReportFormat.HTML,
            "text": ReportFormat.TEXT,
            "markdown": ReportFormat.MARKDOWN,
        }
        report = analyzer.generate_report(
            result,
            format=format_map[args.format],
            output_path=args.output,
        )

        if not args.output:
            print(report)

        # Return non-zero if there are critical issues
        violations = result.get("violations", [])
        if violations:
            return 1
        return 0

    elif args.command == "debt":
        tracker = TechDebtTracker(storage_path=args.storage)

        if args.action == "scan" and args.path:
            items = tracker.scan_directory(args.path)
            print(f"Found {len(items)} technical debt items")
            for item in items:
                print(f"  [{item.priority.name}] {item.title} at {item.location}:{item.lineno}")

        elif args.action == "list":
            items = tracker.get_prioritized()
            for item in items:
                print(f"[{item.priority.name}] {item.id}: {item.title}")
                print(f"  Location: {item.location}:{item.lineno}")
                print(f"  Category: {item.category.value}")
                print()

        elif args.action == "summary":
            summary = tracker.get_summary()
            print("Technical Debt Summary")
            print("-" * 40)
            print(f"Total items: {summary['total_items']}")
            print(f"Estimated hours: {summary['total_estimated_hours']}")
            print(f"Critical: {summary['critical_count']}")
            print(f"High: {summary['high_count']}")

        return 0

    return 1


if __name__ == "__main__":
    sys.exit(main())
