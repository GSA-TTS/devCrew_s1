"""
Complexity Analyzer Module.

Provides cyclomatic complexity, cognitive complexity, and Halstead metrics
analysis for Python source code using AST parsing.
"""

import ast
import math
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Any


@dataclass
class HalsteadMetrics:
    """Halstead software metrics."""

    n1: int = 0  # Number of distinct operators
    n2: int = 0  # Number of distinct operands
    N1: int = 0  # Total number of operators
    N2: int = 0  # Total number of operands

    @property
    def vocabulary(self) -> int:
        """Program vocabulary (n = n1 + n2)."""
        return self.n1 + self.n2

    @property
    def length(self) -> int:
        """Program length (N = N1 + N2)."""
        return self.N1 + self.N2

    @property
    def calculated_length(self) -> float:
        """Calculated program length."""
        if self.n1 == 0 or self.n2 == 0:
            return 0.0
        return self.n1 * math.log2(self.n1) + self.n2 * math.log2(self.n2)

    @property
    def volume(self) -> float:
        """Program volume (V = N * log2(n))."""
        if self.vocabulary == 0:
            return 0.0
        return self.length * math.log2(self.vocabulary)

    @property
    def difficulty(self) -> float:
        """Program difficulty (D = (n1/2) * (N2/n2))."""
        if self.n2 == 0:
            return 0.0
        return (self.n1 / 2) * (self.N2 / self.n2)

    @property
    def effort(self) -> float:
        """Program effort (E = D * V)."""
        return self.difficulty * self.volume

    @property
    def time_to_program(self) -> float:
        """Time to program in seconds (T = E / 18)."""
        return self.effort / 18

    @property
    def bugs_estimate(self) -> float:
        """Estimated number of bugs (B = V / 3000)."""
        return self.volume / 3000

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "n1": self.n1,
            "n2": self.n2,
            "N1": self.N1,
            "N2": self.N2,
            "vocabulary": self.vocabulary,
            "length": self.length,
            "calculated_length": round(self.calculated_length, 2),
            "volume": round(self.volume, 2),
            "difficulty": round(self.difficulty, 2),
            "effort": round(self.effort, 2),
            "time_to_program": round(self.time_to_program, 2),
            "bugs_estimate": round(self.bugs_estimate, 4),
        }


@dataclass
class ComplexityMetrics:
    """Complexity metrics for a function or method."""

    name: str
    lineno: int
    cyclomatic: int = 1
    cognitive: int = 0
    halstead: HalsteadMetrics = field(default_factory=HalsteadMetrics)
    lines_of_code: int = 0
    parameters: int = 0
    nested_depth: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "lineno": self.lineno,
            "cyclomatic_complexity": self.cyclomatic,
            "cognitive_complexity": self.cognitive,
            "halstead": self.halstead.to_dict(),
            "lines_of_code": self.lines_of_code,
            "parameters": self.parameters,
            "nested_depth": self.nested_depth,
        }


class ComplexityVisitor(ast.NodeVisitor):
    """AST visitor for calculating complexity metrics."""

    # Operators for Halstead metrics
    OPERATORS = {
        ast.Add, ast.Sub, ast.Mult, ast.Div, ast.Mod, ast.Pow,
        ast.LShift, ast.RShift, ast.BitOr, ast.BitXor, ast.BitAnd,
        ast.FloorDiv, ast.And, ast.Or, ast.Not, ast.Invert,
        ast.UAdd, ast.USub, ast.Eq, ast.NotEq, ast.Lt, ast.LtE,
        ast.Gt, ast.GtE, ast.Is, ast.IsNot, ast.In, ast.NotIn,
    }

    # Control flow keywords that increase cyclomatic complexity
    COMPLEXITY_NODES = (
        ast.If, ast.For, ast.While, ast.ExceptHandler,
        ast.With, ast.Assert, ast.comprehension,
    )

    def __init__(self) -> None:
        self.operators: Dict[str, int] = {}
        self.operands: Dict[str, int] = {}
        self.cyclomatic = 1
        self.cognitive = 0
        self.max_depth = 0
        self._current_depth = 0

    def _increment_operator(self, op: str) -> None:
        """Track operator occurrence."""
        self.operators[op] = self.operators.get(op, 0) + 1

    def _increment_operand(self, op: str) -> None:
        """Track operand occurrence."""
        self.operands[op] = self.operands.get(op, 0) + 1

    def visit_BinOp(self, node: ast.BinOp) -> None:
        """Visit binary operation."""
        op_name = type(node.op).__name__
        self._increment_operator(op_name)
        self.generic_visit(node)

    def visit_UnaryOp(self, node: ast.UnaryOp) -> None:
        """Visit unary operation."""
        op_name = type(node.op).__name__
        self._increment_operator(op_name)
        self.generic_visit(node)

    def visit_BoolOp(self, node: ast.BoolOp) -> None:
        """Visit boolean operation."""
        op_name = type(node.op).__name__
        # Each 'and'/'or' adds to cyclomatic complexity
        self.cyclomatic += len(node.values) - 1
        self._increment_operator(op_name)
        self.generic_visit(node)

    def visit_Compare(self, node: ast.Compare) -> None:
        """Visit comparison."""
        for op in node.ops:
            op_name = type(op).__name__
            self._increment_operator(op_name)
        self.generic_visit(node)

    def visit_Name(self, node: ast.Name) -> None:
        """Visit name (variable)."""
        self._increment_operand(node.id)
        self.generic_visit(node)

    def visit_Constant(self, node: ast.Constant) -> None:
        """Visit constant."""
        self._increment_operand(str(node.value))
        self.generic_visit(node)

    def visit_If(self, node: ast.If) -> None:
        """Visit if statement."""
        self.cyclomatic += 1
        self._increment_operator("if")
        self._current_depth += 1
        self.max_depth = max(self.max_depth, self._current_depth)
        # Cognitive complexity: nesting adds penalty
        self.cognitive += 1 + self._current_depth - 1
        self.generic_visit(node)
        self._current_depth -= 1

        # Handle elif
        for child in node.orelse:
            if isinstance(child, ast.If):
                self.cyclomatic += 1
                self._increment_operator("elif")

    def visit_For(self, node: ast.For) -> None:
        """Visit for loop."""
        self.cyclomatic += 1
        self._increment_operator("for")
        self._current_depth += 1
        self.max_depth = max(self.max_depth, self._current_depth)
        self.cognitive += 1 + self._current_depth - 1
        self.generic_visit(node)
        self._current_depth -= 1

    def visit_While(self, node: ast.While) -> None:
        """Visit while loop."""
        self.cyclomatic += 1
        self._increment_operator("while")
        self._current_depth += 1
        self.max_depth = max(self.max_depth, self._current_depth)
        self.cognitive += 1 + self._current_depth - 1
        self.generic_visit(node)
        self._current_depth -= 1

    def visit_ExceptHandler(self, node: ast.ExceptHandler) -> None:
        """Visit except handler."""
        self.cyclomatic += 1
        self._increment_operator("except")
        self.cognitive += 1
        self.generic_visit(node)

    def visit_With(self, node: ast.With) -> None:
        """Visit with statement."""
        self._increment_operator("with")
        self._current_depth += 1
        self.max_depth = max(self.max_depth, self._current_depth)
        self.generic_visit(node)
        self._current_depth -= 1

    def visit_Lambda(self, node: ast.Lambda) -> None:
        """Visit lambda expression."""
        self._increment_operator("lambda")
        self.cognitive += 1
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call) -> None:
        """Visit function call."""
        self._increment_operator("()")
        self.generic_visit(node)

    def visit_Subscript(self, node: ast.Subscript) -> None:
        """Visit subscript."""
        self._increment_operator("[]")
        self.generic_visit(node)

    def visit_Attribute(self, node: ast.Attribute) -> None:
        """Visit attribute access."""
        self._increment_operator(".")
        self._increment_operand(node.attr)
        self.generic_visit(node)

    def visit_comprehension(self, node: ast.comprehension) -> None:
        """Visit comprehension."""
        self.cyclomatic += 1
        self.cognitive += 1
        self.generic_visit(node)

    def visit_IfExp(self, node: ast.IfExp) -> None:
        """Visit ternary expression."""
        self.cyclomatic += 1
        self._increment_operator("ternary")
        self.cognitive += 1
        self.generic_visit(node)

    def visit_Assert(self, node: ast.Assert) -> None:
        """Visit assert statement."""
        self.cyclomatic += 1
        self._increment_operator("assert")
        self.generic_visit(node)

    def get_halstead_metrics(self) -> HalsteadMetrics:
        """Calculate Halstead metrics from collected operators/operands."""
        return HalsteadMetrics(
            n1=len(self.operators),
            n2=len(self.operands),
            N1=sum(self.operators.values()),
            N2=sum(self.operands.values()),
        )


class ComplexityAnalyzer:
    """Analyzes Python code complexity."""

    def __init__(
        self,
        cyclomatic_threshold: int = 10,
        cognitive_threshold: int = 15,
        max_parameters: int = 5,
        max_nested_depth: int = 4,
    ) -> None:
        """
        Initialize analyzer with thresholds.

        Args:
            cyclomatic_threshold: Max acceptable cyclomatic complexity
            cognitive_threshold: Max acceptable cognitive complexity
            max_parameters: Max acceptable function parameters
            max_nested_depth: Max acceptable nesting depth
        """
        self.cyclomatic_threshold = cyclomatic_threshold
        self.cognitive_threshold = cognitive_threshold
        self.max_parameters = max_parameters
        self.max_nested_depth = max_nested_depth

    def analyze_code(self, source: str, filename: str = "<string>") -> Dict[str, Any]:
        """
        Analyze source code and return complexity metrics.

        Args:
            source: Python source code string
            filename: Name of the file for reporting

        Returns:
            Dictionary with file-level and function-level metrics
        """
        try:
            tree = ast.parse(source)
        except SyntaxError as e:
            return {
                "filename": filename,
                "error": f"Syntax error: {e}",
                "functions": [],
                "classes": [],
                "summary": {},
            }

        functions: List[ComplexityMetrics] = []
        classes: Dict[str, List[ComplexityMetrics]] = {}

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
                # Check if inside a class
                parent_class = self._find_parent_class(tree, node)
                metrics = self._analyze_function(node, source)

                if parent_class:
                    if parent_class not in classes:
                        classes[parent_class] = []
                    classes[parent_class].append(metrics)
                else:
                    functions.append(metrics)

        # Calculate summary
        all_funcs = functions + [m for methods in classes.values() for m in methods]
        summary = self._calculate_summary(all_funcs)

        return {
            "filename": filename,
            "functions": [f.to_dict() for f in functions],
            "classes": {
                name: [m.to_dict() for m in methods]
                for name, methods in classes.items()
            },
            "summary": summary,
            "violations": self._find_violations(all_funcs),
        }

    def analyze_file(self, filepath: str | Path) -> Dict[str, Any]:
        """
        Analyze a Python file.

        Args:
            filepath: Path to Python file

        Returns:
            Dictionary with complexity metrics
        """
        filepath = Path(filepath)
        if not filepath.exists():
            return {"filename": str(filepath), "error": "File not found"}

        try:
            source = filepath.read_text(encoding="utf-8")
            return self.analyze_code(source, str(filepath))
        except Exception as e:
            return {"filename": str(filepath), "error": str(e)}

    def _analyze_function(
        self,
        node: ast.FunctionDef | ast.AsyncFunctionDef,
        source: str,
    ) -> ComplexityMetrics:
        """Analyze a single function/method."""
        visitor = ComplexityVisitor()
        visitor.visit(node)

        # Calculate lines of code
        lines = source.splitlines()
        if hasattr(node, "end_lineno") and node.end_lineno:
            loc = node.end_lineno - node.lineno + 1
        else:
            loc = len([line for line in lines[node.lineno - 1:] if line.strip()])

        # Count parameters
        params = len(node.args.args) + len(node.args.posonlyargs)
        params += len(node.args.kwonlyargs)
        if node.args.vararg:
            params += 1
        if node.args.kwarg:
            params += 1

        return ComplexityMetrics(
            name=node.name,
            lineno=node.lineno,
            cyclomatic=visitor.cyclomatic,
            cognitive=visitor.cognitive,
            halstead=visitor.get_halstead_metrics(),
            lines_of_code=loc,
            parameters=params,
            nested_depth=visitor.max_depth,
        )

    def _find_parent_class(
        self,
        tree: ast.Module,
        target: ast.AST,
    ) -> Optional[str]:
        """Find parent class name for a method."""
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                for child in ast.walk(node):
                    if child is target:
                        return node.name
        return None

    def _calculate_summary(
        self,
        functions: List[ComplexityMetrics],
    ) -> Dict[str, Any]:
        """Calculate summary statistics."""
        if not functions:
            return {
                "total_functions": 0,
                "avg_cyclomatic": 0,
                "avg_cognitive": 0,
                "max_cyclomatic": 0,
                "max_cognitive": 0,
                "total_loc": 0,
            }

        cyclomatic_values = [f.cyclomatic for f in functions]
        cognitive_values = [f.cognitive for f in functions]

        return {
            "total_functions": len(functions),
            "avg_cyclomatic": round(sum(cyclomatic_values) / len(functions), 2),
            "avg_cognitive": round(sum(cognitive_values) / len(functions), 2),
            "max_cyclomatic": max(cyclomatic_values),
            "max_cognitive": max(cognitive_values),
            "total_loc": sum(f.lines_of_code for f in functions),
        }

    def _find_violations(
        self,
        functions: List[ComplexityMetrics],
    ) -> List[Dict[str, Any]]:
        """Find threshold violations."""
        violations = []
        for func in functions:
            if func.cyclomatic > self.cyclomatic_threshold:
                violations.append({
                    "function": func.name,
                    "lineno": func.lineno,
                    "type": "cyclomatic_complexity",
                    "value": func.cyclomatic,
                    "threshold": self.cyclomatic_threshold,
                })
            if func.cognitive > self.cognitive_threshold:
                violations.append({
                    "function": func.name,
                    "lineno": func.lineno,
                    "type": "cognitive_complexity",
                    "value": func.cognitive,
                    "threshold": self.cognitive_threshold,
                })
            if func.parameters > self.max_parameters:
                violations.append({
                    "function": func.name,
                    "lineno": func.lineno,
                    "type": "too_many_parameters",
                    "value": func.parameters,
                    "threshold": self.max_parameters,
                })
            if func.nested_depth > self.max_nested_depth:
                violations.append({
                    "function": func.name,
                    "lineno": func.lineno,
                    "type": "deep_nesting",
                    "value": func.nested_depth,
                    "threshold": self.max_nested_depth,
                })
        return violations
