"""
Architecture Fitness Functions - Architecture Validation & Testing
Issue #40: TOOL-ARCH-001

Provides architecture fitness function capabilities:
- Define architecture validation rules
- Execute fitness tests on codebase
- Detect architecture violations
- Generate compliance reports
"""

import ast
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Set

import yaml
from radon.complexity import cc_visit
from radon.metrics import h_visit, mi_visit


@dataclass
class FitnessViolation:
    """Represents a fitness function violation."""

    rule_name: str
    severity: str  # ERROR, WARNING, INFO
    message: str
    file_path: Optional[str] = None
    line_number: Optional[int] = None
    details: Optional[Dict] = None


@dataclass
class FitnessResult:
    """Results from fitness function execution."""

    total_rules: int
    passed_rules: int
    failed_rules: int
    violations: List[FitnessViolation] = field(default_factory=list)
    execution_time: float = 0.0

    @property
    def violation_count(self) -> int:
        """Get total violation count."""
        return len(self.violations)

    @property
    def success_rate(self) -> float:
        """Get success rate as percentage."""
        if self.total_rules == 0:
            return 100.0
        return (self.passed_rules / self.total_rules) * 100.0

    def get_violations_by_severity(self, severity: str) -> List[FitnessViolation]:
        """Get violations filtered by severity."""
        return [v for v in self.violations if v.severity == severity]


@dataclass
class FitnessRule:
    """Defines an architecture fitness rule."""

    name: str
    type: str  # dependency, naming, complexity, structure, etc.
    severity: str  # ERROR, WARNING, INFO
    enabled: bool = True
    parameters: Dict = field(default_factory=dict)


class DependencyAnalyzer:
    """Analyzes code dependencies."""

    def __init__(self, codebase_path: str):
        """
        Initialize dependency analyzer.

        Args:
            codebase_path: Path to codebase root
        """
        self.codebase_path = Path(codebase_path)

    def get_imports(self, file_path: Path) -> Set[str]:
        """
        Extract imports from a Python file.

        Args:
            file_path: Path to Python file

        Returns:
            Set of imported module names
        """
        try:
            content = file_path.read_text()
            tree = ast.parse(content)
            imports = set()

            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.add(alias.name.split(".")[0])
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        imports.add(node.module.split(".")[0])

            return imports
        except Exception:
            return set()

    def check_layer_dependencies(
        self, file_path: Path, allowed_layers: List[str]
    ) -> List[str]:
        """
        Check if file only imports from allowed layers.

        Args:
            file_path: File to check
            allowed_layers: List of allowed layer names

        Returns:
            List of violated imports
        """
        imports = self.get_imports(file_path)
        violations = []

        for imp in imports:
            # Check if import is from internal layers
            if any(imp.startswith(layer) for layer in allowed_layers):
                continue

            # Check if import violates layer rules
            # This is a simplified check
            if not self._is_standard_library(imp):
                violations.append(imp)

        return violations

    def _is_standard_library(self, module_name: str) -> bool:
        """Check if module is from standard library."""
        stdlib_modules = {
            "os",
            "sys",
            "re",
            "json",
            "yaml",
            "pathlib",
            "datetime",
            "typing",
            "dataclasses",
            "abc",
            "collections",
            "itertools",
            "functools",
        }
        return module_name in stdlib_modules


class ComplexityAnalyzer:
    """Analyzes code complexity metrics."""

    @staticmethod
    def get_cyclomatic_complexity(file_path: Path) -> Dict[str, int]:
        """
        Calculate cyclomatic complexity for functions in a file.

        Args:
            file_path: Path to Python file

        Returns:
            Dictionary mapping function names to complexity scores
        """
        try:
            content = file_path.read_text()
            results = cc_visit(content)
            return {r.name: r.complexity for r in results}
        except Exception:
            return {}

    @staticmethod
    def get_maintainability_index(file_path: Path) -> Optional[float]:
        """
        Calculate maintainability index for a file.

        Args:
            file_path: Path to Python file

        Returns:
            Maintainability index (0-100) or None
        """
        try:
            content = file_path.read_text()
            mi = mi_visit(content, multi=True)
            return mi if isinstance(mi, (int, float)) else None
        except Exception:
            return None

    @staticmethod
    def get_halstead_metrics(file_path: Path) -> Optional[Dict]:
        """
        Calculate Halstead complexity metrics.

        Args:
            file_path: Path to Python file

        Returns:
            Dictionary of Halstead metrics or None
        """
        try:
            content = file_path.read_text()
            metrics = h_visit(content)
            return {
                "volume": metrics.volume,
                "difficulty": metrics.difficulty,
                "effort": metrics.effort,
            }
        except Exception:
            return None


class NamingAnalyzer:
    """Analyzes naming conventions."""

    @staticmethod
    def check_class_naming(file_path: Path, pattern: str) -> List[str]:
        """
        Check if class names match pattern.

        Args:
            file_path: Path to Python file
            pattern: Regex pattern for class names

        Returns:
            List of violating class names
        """
        try:
            content = file_path.read_text()
            tree = ast.parse(content)
            violations = []

            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    if not re.match(pattern, node.name):
                        violations.append(node.name)

            return violations
        except Exception:
            return []

    @staticmethod
    def check_function_naming(file_path: Path, pattern: str) -> List[str]:
        """
        Check if function names match pattern.

        Args:
            file_path: Path to Python file
            pattern: Regex pattern for function names

        Returns:
            List of violating function names
        """
        try:
            content = file_path.read_text()
            tree = ast.parse(content)
            violations = []

            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    if not re.match(pattern, node.name):
                        violations.append(node.name)

            return violations
        except Exception:
            return []


class FitnessTester:
    """Executes architecture fitness functions."""

    def __init__(self, rules_file: Optional[str] = None):
        """
        Initialize fitness tester.

        Args:
            rules_file: Path to YAML file with fitness rules
        """
        self.rules: List[FitnessRule] = []

        if rules_file:
            self.load_rules(rules_file)

    def load_rules(self, rules_file: str) -> None:
        """
        Load fitness rules from YAML file.

        Args:
            rules_file: Path to YAML file
        """
        with open(rules_file, "r") as f:
            data = yaml.safe_load(f)

        self.rules = []
        for rule_data in data.get("rules", []):
            rule = FitnessRule(
                name=rule_data["name"],
                type=rule_data["type"],
                severity=rule_data.get("severity", "WARNING"),
                enabled=rule_data.get("enabled", True),
                parameters=rule_data.get("parameters", {}),
            )
            self.rules.append(rule)

    def add_rule(self, rule: FitnessRule) -> None:
        """Add a fitness rule."""
        self.rules.append(rule)

    def test(self, codebase_path: str) -> FitnessResult:
        """
        Execute all fitness tests on codebase.

        Args:
            codebase_path: Path to codebase root

        Returns:
            FitnessResult with test results
        """
        import time

        start_time = time.time()

        violations = []
        passed = 0
        failed = 0

        codebase = Path(codebase_path)

        for rule in self.rules:
            if not rule.enabled:
                continue

            try:
                rule_violations = self._execute_rule(rule, codebase)
                if rule_violations:
                    violations.extend(rule_violations)
                    failed += 1
                else:
                    passed += 1
            except Exception as e:
                violation = FitnessViolation(
                    rule_name=rule.name,
                    severity="ERROR",
                    message=f"Rule execution failed: {str(e)}",
                )
                violations.append(violation)
                failed += 1

        execution_time = time.time() - start_time

        return FitnessResult(
            total_rules=len([r for r in self.rules if r.enabled]),
            passed_rules=passed,
            failed_rules=failed,
            violations=violations,
            execution_time=execution_time,
        )

    def _execute_rule(
        self, rule: FitnessRule, codebase: Path
    ) -> List[FitnessViolation]:
        """Execute a single fitness rule."""
        if rule.type == "complexity":
            return self._check_complexity(rule, codebase)
        elif rule.type == "naming":
            return self._check_naming(rule, codebase)
        elif rule.type == "dependency":
            return self._check_dependencies(rule, codebase)
        elif rule.type == "structure":
            return self._check_structure(rule, codebase)
        else:
            return []

    def _check_complexity(
        self, rule: FitnessRule, codebase: Path
    ) -> List[FitnessViolation]:
        """Check complexity metrics."""
        violations = []
        threshold = rule.parameters.get("threshold", 10)
        metric_type = rule.parameters.get("metric", "cyclomatic")

        analyzer = ComplexityAnalyzer()

        for py_file in codebase.rglob("*.py"):
            if "venv" in str(py_file) or ".venv" in str(py_file):
                continue

            if metric_type == "cyclomatic":
                complexities = analyzer.get_cyclomatic_complexity(py_file)
                for func_name, complexity in complexities.items():
                    if complexity > threshold:
                        violation = FitnessViolation(
                            rule_name=rule.name,
                            severity=rule.severity,
                            message=(
                                f"Function '{func_name}' has cyclomatic complexity "
                                f"{complexity} (threshold: {threshold})"
                            ),
                            file_path=str(py_file),
                            details={"complexity": complexity, "threshold": threshold},
                        )
                        violations.append(violation)

            elif metric_type == "maintainability":
                mi = analyzer.get_maintainability_index(py_file)
                if mi is not None and mi < threshold:
                    violation = FitnessViolation(
                        rule_name=rule.name,
                        severity=rule.severity,
                        message=(
                            f"File has low maintainability index {mi:.2f} "
                            f"(threshold: {threshold})"
                        ),
                        file_path=str(py_file),
                        details={"maintainability_index": mi, "threshold": threshold},
                    )
                    violations.append(violation)

        return violations

    def _check_naming(
        self, rule: FitnessRule, codebase: Path
    ) -> List[FitnessViolation]:
        """Check naming conventions."""
        violations = []
        pattern = rule.parameters.get("pattern", ".*")
        target = rule.parameters.get("target", "classes")

        analyzer = NamingAnalyzer()

        for py_file in codebase.rglob("*.py"):
            if "venv" in str(py_file) or ".venv" in str(py_file):
                continue

            if target == "classes":
                violating_names = analyzer.check_class_naming(py_file, pattern)
                for name in violating_names:
                    violation = FitnessViolation(
                        rule_name=rule.name,
                        severity=rule.severity,
                        message=(
                            f"Class '{name}' does not match naming pattern '{pattern}'"
                        ),
                        file_path=str(py_file),
                    )
                    violations.append(violation)

            elif target == "functions":
                violating_names = analyzer.check_function_naming(py_file, pattern)
                for name in violating_names:
                    violation = FitnessViolation(
                        rule_name=rule.name,
                        severity=rule.severity,
                        message=(
                            f"Function '{name}' does not match "
                            f"naming pattern '{pattern}'"
                        ),
                        file_path=str(py_file),
                    )
                    violations.append(violation)

        return violations

    def _check_dependencies(
        self, rule: FitnessRule, codebase: Path
    ) -> List[FitnessViolation]:
        """Check dependency rules."""
        violations = []
        allowed_layers = rule.parameters.get("allowed_layers", [])

        analyzer = DependencyAnalyzer(str(codebase))

        for py_file in codebase.rglob("*.py"):
            if "venv" in str(py_file) or ".venv" in str(py_file):
                continue

            violating_imports = analyzer.check_layer_dependencies(py_file, allowed_layers)

            for imp in violating_imports:
                violation = FitnessViolation(
                    rule_name=rule.name,
                    severity=rule.severity,
                    message=f"Unauthorized dependency on '{imp}'",
                    file_path=str(py_file),
                )
                violations.append(violation)

        return violations

    def _check_structure(
        self, rule: FitnessRule, codebase: Path
    ) -> List[FitnessViolation]:
        """Check structural rules."""
        violations = []
        required_dirs = rule.parameters.get("required_directories", [])

        for required_dir in required_dirs:
            dir_path = codebase / required_dir
            if not dir_path.exists():
                violation = FitnessViolation(
                    rule_name=rule.name,
                    severity=rule.severity,
                    message=f"Required directory '{required_dir}' not found",
                )
                violations.append(violation)

        return violations

    def generate_report(self, result: FitnessResult, output_file: Optional[str] = None) -> str:
        """
        Generate fitness test report.

        Args:
            result: FitnessResult object
            output_file: Optional output file path

        Returns:
            Report as string
        """
        lines = ["# Architecture Fitness Test Report\n"]
        lines.append(f"**Execution Time**: {result.execution_time:.2f}s\n")
        lines.append(f"**Total Rules**: {result.total_rules}\n")
        lines.append(f"**Passed**: {result.passed_rules}\n")
        lines.append(f"**Failed**: {result.failed_rules}\n")
        lines.append(f"**Success Rate**: {result.success_rate:.1f}%\n")
        lines.append(f"**Total Violations**: {result.violation_count}\n")
        lines.append("\n")

        # Group violations by severity
        for severity in ["ERROR", "WARNING", "INFO"]:
            severity_violations = result.get_violations_by_severity(severity)
            if severity_violations:
                lines.append(f"## {severity} ({len(severity_violations)})\n\n")

                for v in severity_violations:
                    lines.append(f"### {v.rule_name}\n")
                    lines.append(f"**Message**: {v.message}\n")
                    if v.file_path:
                        lines.append(f"**File**: {v.file_path}\n")
                    if v.line_number:
                        lines.append(f"**Line**: {v.line_number}\n")
                    if v.details:
                        lines.append(f"**Details**: {v.details}\n")
                    lines.append("\n")

        report = "\n".join(lines)

        if output_file:
            Path(output_file).write_text(report)

        return report
