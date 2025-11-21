"""
Code Smell Detector Module.

Detects common code smells in Python source code including:
- Long methods
- Large classes
- Duplicate code patterns
- God classes
- Feature envy
- Data clumps
"""

import ast
import hashlib
import re
from collections import defaultdict
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Dict, List, Any, Optional, Set


class SmellSeverity(Enum):
    """Severity levels for code smells."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class CodeSmell:
    """Represents a detected code smell."""

    name: str
    description: str
    severity: SmellSeverity
    location: str
    lineno: int
    end_lineno: Optional[int] = None
    suggestion: str = ""
    confidence: float = 1.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "description": self.description,
            "severity": self.severity.value,
            "location": self.location,
            "lineno": self.lineno,
            "end_lineno": self.end_lineno,
            "suggestion": self.suggestion,
            "confidence": self.confidence,
        }


@dataclass
class CodeSmellConfig:
    """Configuration for code smell detection thresholds."""

    max_method_lines: int = 30
    max_class_lines: int = 300
    max_class_methods: int = 20
    max_parameters: int = 5
    max_returns: int = 4
    max_branches: int = 10
    min_duplicate_lines: int = 6
    max_nested_depth: int = 4
    max_attributes: int = 15
    max_local_variables: int = 15


class DuplicateDetector:
    """Detects duplicate code blocks."""

    def __init__(self, min_lines: int = 6) -> None:
        self.min_lines = min_lines
        self.code_blocks: Dict[str, List[Dict[str, Any]]] = defaultdict(list)

    def add_block(
        self,
        code: str,
        filename: str,
        start_line: int,
        end_line: int,
    ) -> None:
        """Add a code block for duplicate detection."""
        # Normalize code for comparison
        normalized = self._normalize_code(code)
        if len(normalized.splitlines()) >= self.min_lines:
            block_hash = hashlib.md5(normalized.encode()).hexdigest()
            self.code_blocks[block_hash].append({
                "filename": filename,
                "start_line": start_line,
                "end_line": end_line,
                "code": code,
            })

    def _normalize_code(self, code: str) -> str:
        """Normalize code for comparison."""
        lines = []
        for line in code.splitlines():
            # Remove comments and normalize whitespace
            line = re.sub(r"#.*$", "", line)
            line = line.strip()
            if line:
                lines.append(line)
        return "\n".join(lines)

    def get_duplicates(self) -> List[Dict[str, Any]]:
        """Get all detected duplicates."""
        duplicates = []
        for block_hash, locations in self.code_blocks.items():
            if len(locations) > 1:
                duplicates.append({
                    "hash": block_hash,
                    "occurrences": len(locations),
                    "locations": locations,
                    "lines": len(locations[0]["code"].splitlines()),
                })
        return duplicates


class CodeSmellVisitor(ast.NodeVisitor):
    """AST visitor for detecting code smells within functions/classes."""

    def __init__(self) -> None:
        self.returns = 0
        self.branches = 0
        self.local_vars: Set[str] = set()
        self.max_depth = 0
        self._current_depth = 0
        self.external_calls: Dict[str, int] = defaultdict(int)

    def visit_Return(self, node: ast.Return) -> None:
        """Count return statements."""
        self.returns += 1
        self.generic_visit(node)

    def visit_If(self, node: ast.If) -> None:
        """Track if statements."""
        self.branches += 1
        self._current_depth += 1
        self.max_depth = max(self.max_depth, self._current_depth)
        self.generic_visit(node)
        self._current_depth -= 1

    def visit_For(self, node: ast.For) -> None:
        """Track for loops."""
        self.branches += 1
        self._current_depth += 1
        self.max_depth = max(self.max_depth, self._current_depth)
        self.generic_visit(node)
        self._current_depth -= 1

    def visit_While(self, node: ast.While) -> None:
        """Track while loops."""
        self.branches += 1
        self._current_depth += 1
        self.max_depth = max(self.max_depth, self._current_depth)
        self.generic_visit(node)
        self._current_depth -= 1

    def visit_Assign(self, node: ast.Assign) -> None:
        """Track local variable assignments."""
        for target in node.targets:
            if isinstance(target, ast.Name):
                self.local_vars.add(target.id)
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call) -> None:
        """Track external calls for feature envy detection."""
        if isinstance(node.func, ast.Attribute):
            if isinstance(node.func.value, ast.Name):
                self.external_calls[node.func.value.id] += 1
        self.generic_visit(node)


class CodeSmellDetector:
    """Detects code smells in Python source code."""

    def __init__(self, config: Optional[CodeSmellConfig] = None) -> None:
        """
        Initialize detector with configuration.

        Args:
            config: Configuration for smell detection thresholds
        """
        self.config = config or CodeSmellConfig()
        self.duplicate_detector = DuplicateDetector(self.config.min_duplicate_lines)

    def detect(self, source: str, filename: str = "<string>") -> Dict[str, Any]:
        """
        Detect code smells in source code.

        Args:
            source: Python source code string
            filename: Name of the file for reporting

        Returns:
            Dictionary with detected smells and summary
        """
        try:
            tree = ast.parse(source)
        except SyntaxError as e:
            return {
                "filename": filename,
                "error": f"Syntax error: {e}",
                "smells": [],
                "summary": {},
            }

        smells: List[CodeSmell] = []
        lines = source.splitlines()

        # Analyze module level
        smells.extend(self._detect_module_smells(tree, lines, filename))

        # Analyze classes
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                smells.extend(self._detect_class_smells(node, lines, filename))

        # Analyze functions/methods
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
                smells.extend(self._detect_function_smells(node, lines, filename))

        # Detect duplicates
        self._add_function_blocks(tree, source, filename)

        return {
            "filename": filename,
            "smells": [s.to_dict() for s in smells],
            "duplicates": self.duplicate_detector.get_duplicates(),
            "summary": self._summarize(smells),
        }

    def detect_file(self, filepath: str | Path) -> Dict[str, Any]:
        """
        Detect code smells in a Python file.

        Args:
            filepath: Path to Python file

        Returns:
            Dictionary with detected smells
        """
        filepath = Path(filepath)
        if not filepath.exists():
            return {"filename": str(filepath), "error": "File not found"}

        try:
            source = filepath.read_text(encoding="utf-8")
            return self.detect(source, str(filepath))
        except Exception as e:
            return {"filename": str(filepath), "error": str(e)}

    def _detect_module_smells(
        self,
        tree: ast.Module,
        lines: List[str],
        filename: str,
    ) -> List[CodeSmell]:
        """Detect module-level smells."""
        smells = []

        # Check for too many global variables
        global_vars = [
            node for node in tree.body
            if isinstance(node, ast.Assign)
        ]
        if len(global_vars) > self.config.max_attributes:
            smells.append(CodeSmell(
                name="too_many_globals",
                description=f"Module has {len(global_vars)} global variables",
                severity=SmellSeverity.MEDIUM,
                location=filename,
                lineno=1,
                suggestion="Consider grouping related globals into classes",
            ))

        return smells

    def _detect_class_smells(
        self,
        node: ast.ClassDef,
        lines: List[str],
        filename: str,
    ) -> List[CodeSmell]:
        """Detect class-level code smells."""
        smells = []
        end_line = getattr(node, "end_lineno", node.lineno + 1)
        class_lines = end_line - node.lineno + 1

        # Large class
        if class_lines > self.config.max_class_lines:
            smells.append(CodeSmell(
                name="large_class",
                description=f"Class '{node.name}' has {class_lines} lines",
                severity=SmellSeverity.HIGH,
                location=f"{filename}::{node.name}",
                lineno=node.lineno,
                end_lineno=end_line,
                suggestion="Consider splitting into smaller classes",
            ))

        # Count methods
        methods = [
            n for n in node.body
            if isinstance(n, ast.FunctionDef | ast.AsyncFunctionDef)
        ]
        if len(methods) > self.config.max_class_methods:
            smells.append(CodeSmell(
                name="too_many_methods",
                description=f"Class '{node.name}' has {len(methods)} methods",
                severity=SmellSeverity.MEDIUM,
                location=f"{filename}::{node.name}",
                lineno=node.lineno,
                suggestion="Consider extracting related methods to new classes",
            ))

        # Count instance attributes
        attributes = self._count_class_attributes(node)
        if attributes > self.config.max_attributes:
            smells.append(CodeSmell(
                name="too_many_attributes",
                description=f"Class '{node.name}' has {attributes} attributes",
                severity=SmellSeverity.MEDIUM,
                location=f"{filename}::{node.name}",
                lineno=node.lineno,
                suggestion="Consider grouping related attributes",
            ))

        # God class detection
        if (
            class_lines > self.config.max_class_lines * 0.7
            and len(methods) > self.config.max_class_methods * 0.7
        ):
            smells.append(CodeSmell(
                name="god_class",
                description=f"Class '{node.name}' appears to be a God Class",
                severity=SmellSeverity.CRITICAL,
                location=f"{filename}::{node.name}",
                lineno=node.lineno,
                suggestion="Apply Single Responsibility Principle",
            ))

        return smells

    def _detect_function_smells(
        self,
        node: ast.FunctionDef | ast.AsyncFunctionDef,
        lines: List[str],
        filename: str,
    ) -> List[CodeSmell]:
        """Detect function-level code smells."""
        smells = []
        end_line = getattr(node, "end_lineno", node.lineno + 1)
        func_lines = end_line - node.lineno + 1

        # Long method
        if func_lines > self.config.max_method_lines:
            smells.append(CodeSmell(
                name="long_method",
                description=f"Function '{node.name}' has {func_lines} lines",
                severity=SmellSeverity.HIGH,
                location=f"{filename}::{node.name}",
                lineno=node.lineno,
                end_lineno=end_line,
                suggestion="Consider extracting smaller functions",
            ))

        # Too many parameters
        param_count = (
            len(node.args.args) + len(node.args.posonlyargs)
            + len(node.args.kwonlyargs)
        )
        if node.args.vararg:
            param_count += 1
        if node.args.kwarg:
            param_count += 1

        if param_count > self.config.max_parameters:
            smells.append(CodeSmell(
                name="too_many_parameters",
                description=f"Function '{node.name}' has {param_count} parameters",
                severity=SmellSeverity.MEDIUM,
                location=f"{filename}::{node.name}",
                lineno=node.lineno,
                suggestion="Consider using parameter objects or builders",
            ))

        # Analyze function body
        visitor = CodeSmellVisitor()
        visitor.visit(node)

        # Too many returns
        if visitor.returns > self.config.max_returns:
            smells.append(CodeSmell(
                name="too_many_returns",
                description=f"Function '{node.name}' has {visitor.returns} returns",
                severity=SmellSeverity.LOW,
                location=f"{filename}::{node.name}",
                lineno=node.lineno,
                suggestion="Consider simplifying control flow",
            ))

        # Too many branches
        if visitor.branches > self.config.max_branches:
            smells.append(CodeSmell(
                name="too_many_branches",
                description=f"Function '{node.name}' has {visitor.branches} branches",
                severity=SmellSeverity.MEDIUM,
                location=f"{filename}::{node.name}",
                lineno=node.lineno,
                suggestion="Consider using polymorphism or strategy pattern",
            ))

        # Deep nesting
        if visitor.max_depth > self.config.max_nested_depth:
            smells.append(CodeSmell(
                name="deep_nesting",
                description=f"Function '{node.name}' has depth {visitor.max_depth}",
                severity=SmellSeverity.HIGH,
                location=f"{filename}::{node.name}",
                lineno=node.lineno,
                suggestion="Consider guard clauses or extracting methods",
            ))

        # Too many local variables
        if len(visitor.local_vars) > self.config.max_local_variables:
            smells.append(CodeSmell(
                name="too_many_variables",
                description=(
                    f"Function '{node.name}' has "
                    f"{len(visitor.local_vars)} local variables"
                ),
                severity=SmellSeverity.MEDIUM,
                location=f"{filename}::{node.name}",
                lineno=node.lineno,
                suggestion="Consider extracting helper functions",
            ))

        # Feature envy detection
        if visitor.external_calls:
            max_external = max(visitor.external_calls.values())
            if max_external > 5:
                external_obj = max(
                    visitor.external_calls,
                    key=visitor.external_calls.get,
                )
                smells.append(CodeSmell(
                    name="feature_envy",
                    description=(
                        f"Function '{node.name}' makes {max_external} calls "
                        f"to '{external_obj}'"
                    ),
                    severity=SmellSeverity.MEDIUM,
                    location=f"{filename}::{node.name}",
                    lineno=node.lineno,
                    suggestion=f"Consider moving this logic to '{external_obj}'",
                    confidence=0.7,
                ))

        return smells

    def _count_class_attributes(self, node: ast.ClassDef) -> int:
        """Count instance attributes in a class."""
        attributes: Set[str] = set()
        for item in ast.walk(node):
            if isinstance(item, ast.Attribute):
                if (
                    isinstance(item.value, ast.Name)
                    and item.value.id == "self"
                ):
                    attributes.add(item.attr)
        return len(attributes)

    def _add_function_blocks(
        self,
        tree: ast.Module,
        source: str,
        filename: str,
    ) -> None:
        """Add function bodies for duplicate detection."""
        lines = source.splitlines()
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
                end_line = getattr(node, "end_lineno", node.lineno + 10)
                code = "\n".join(lines[node.lineno - 1:end_line])
                self.duplicate_detector.add_block(
                    code, filename, node.lineno, end_line
                )

    def _summarize(self, smells: List[CodeSmell]) -> Dict[str, Any]:
        """Summarize detected smells."""
        by_severity = defaultdict(int)
        by_name = defaultdict(int)

        for smell in smells:
            by_severity[smell.severity.value] += 1
            by_name[smell.name] += 1

        return {
            "total": len(smells),
            "by_severity": dict(by_severity),
            "by_type": dict(by_name),
        }
