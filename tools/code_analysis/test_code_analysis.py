"""
Comprehensive tests for Code Analysis & Quality Metrics Platform.

Tests cover all components: complexity analyzer, code smell detector,
tech debt tracker, refactoring advisor, and metrics reporter.
"""

import json
import tempfile
import unittest
from pathlib import Path

from complexity_analyzer import (
    ComplexityAnalyzer,
    HalsteadMetrics,
    ComplexityVisitor,
)
from code_smell_detector import (
    CodeSmellDetector,
    CodeSmell,
    CodeSmellConfig,
    SmellSeverity,
)
from tech_debt_tracker import (
    TechDebtTracker,
    TechDebtItem,
    DebtPriority,
    DebtCategory,
)
from refactoring_advisor import (
    RefactoringAdvisor,
    RefactoringSuggestion,
    RefactoringType,
)
from metrics_reporter import (
    MetricsReporter,
    ReportFormat,
    ReportConfig,
)


# Sample code for testing
SIMPLE_FUNCTION = '''
def add(a, b):
    return a + b
'''

COMPLEX_FUNCTION = '''
def complex_function(a, b, c, d, e, f):
    result = 0
    if a > 0:
        if b > 0:
            if c > 0:
                for i in range(d):
                    if i % 2 == 0:
                        result += i
                    else:
                        result -= i
            else:
                result = -1
        elif b < 0:
            result = b
        else:
            result = 0
    else:
        while e > 0:
            e -= 1
            result += e
    return result
'''

LARGE_CLASS = '''
class LargeClass:
    def __init__(self):
        self.a = 1
        self.b = 2
        self.c = 3
        self.d = 4
        self.e = 5

    def method1(self): pass
    def method2(self): pass
    def method3(self): pass
    def method4(self): pass
    def method5(self): pass
    def method6(self): pass
    def method7(self): pass
    def method8(self): pass
    def method9(self): pass
    def method10(self): pass
    def method11(self): pass
    def method12(self): pass
    def method13(self): pass
    def method14(self): pass
    def method15(self): pass
    def method16(self): pass
    def method17(self): pass
    def method18(self): pass
    def method19(self): pass
    def method20(self): pass
    def method21(self): pass
'''

CODE_WITH_TODOS = '''
def process_data(data):
    # TODO: Add input validation
    result = []
    for item in data:
        # FIXME: This is inefficient
        result.append(item * 2)
    # HACK: Temporary workaround
    return result
'''

FEATURE_ENVY_CODE = '''
class Order:
    def calculate_total(self, customer):
        # Lots of calls to customer
        discount = customer.get_discount()
        tax = customer.get_tax_rate()
        shipping = customer.get_shipping_address()
        payment = customer.get_payment_method()
        history = customer.get_order_history()
        loyalty = customer.get_loyalty_points()
        return 100 * (1 - discount) * (1 + tax)
'''


class TestHalsteadMetrics(unittest.TestCase):
    """Tests for Halstead metrics calculations."""

    def test_empty_metrics(self):
        """Test metrics with zero values."""
        metrics = HalsteadMetrics()
        self.assertEqual(metrics.vocabulary, 0)
        self.assertEqual(metrics.length, 0)
        self.assertEqual(metrics.volume, 0.0)
        self.assertEqual(metrics.difficulty, 0.0)

    def test_metrics_calculations(self):
        """Test metric calculations with real values."""
        metrics = HalsteadMetrics(n1=10, n2=8, N1=50, N2=30)
        self.assertEqual(metrics.vocabulary, 18)
        self.assertEqual(metrics.length, 80)
        self.assertGreater(metrics.volume, 0)
        self.assertGreater(metrics.difficulty, 0)
        self.assertGreater(metrics.effort, 0)
        self.assertGreater(metrics.time_to_program, 0)
        self.assertGreater(metrics.bugs_estimate, 0)

    def test_to_dict(self):
        """Test conversion to dictionary."""
        metrics = HalsteadMetrics(n1=5, n2=3, N1=20, N2=10)
        d = metrics.to_dict()
        self.assertIn("vocabulary", d)
        self.assertIn("volume", d)
        self.assertIn("effort", d)


class TestComplexityAnalyzer(unittest.TestCase):
    """Tests for ComplexityAnalyzer."""

    def setUp(self):
        """Set up test fixtures."""
        self.analyzer = ComplexityAnalyzer(
            cyclomatic_threshold=5,
            cognitive_threshold=10,
        )

    def test_simple_function(self):
        """Test analysis of simple function."""
        result = self.analyzer.analyze_code(SIMPLE_FUNCTION)
        self.assertIn("functions", result)
        self.assertEqual(len(result["functions"]), 1)
        func = result["functions"][0]
        self.assertEqual(func["name"], "add")
        self.assertEqual(func["cyclomatic_complexity"], 1)

    def test_complex_function_violations(self):
        """Test complex function triggers violations."""
        result = self.analyzer.analyze_code(COMPLEX_FUNCTION)
        self.assertIn("violations", result)
        # Should have cyclomatic and possibly other violations
        violations = result["violations"]
        violation_types = [v["type"] for v in violations]
        self.assertIn("cyclomatic_complexity", violation_types)

    def test_file_analysis(self):
        """Test file-based analysis."""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".py", delete=False
        ) as f:
            f.write(SIMPLE_FUNCTION)
            f.flush()
            result = self.analyzer.analyze_file(f.name)
            self.assertEqual(result["filename"], f.name)
            self.assertIn("functions", result)

    def test_syntax_error_handling(self):
        """Test handling of syntax errors."""
        result = self.analyzer.analyze_code("def broken(")
        self.assertIn("error", result)

    def test_class_methods(self):
        """Test class method analysis."""
        code = '''
class MyClass:
    def method1(self):
        return 1
    def method2(self):
        return 2
'''
        result = self.analyzer.analyze_code(code)
        self.assertIn("classes", result)
        self.assertIn("MyClass", result["classes"])
        self.assertEqual(len(result["classes"]["MyClass"]), 2)

    def test_summary_statistics(self):
        """Test summary statistics calculation."""
        result = self.analyzer.analyze_code(COMPLEX_FUNCTION)
        summary = result["summary"]
        self.assertIn("total_functions", summary)
        self.assertIn("avg_cyclomatic", summary)
        self.assertIn("max_cyclomatic", summary)


class TestComplexityVisitor(unittest.TestCase):
    """Tests for ComplexityVisitor AST walker."""

    def test_boolean_operations(self):
        """Test boolean operations add to complexity."""
        import ast

        code = "if a and b and c: pass"
        tree = ast.parse(code)
        visitor = ComplexityVisitor()
        visitor.visit(tree)
        # 'if' + 2 additional 'and' conditions
        self.assertGreater(visitor.cyclomatic, 1)

    def test_nested_depth_tracking(self):
        """Test nested depth is tracked correctly."""
        import ast

        code = '''
if a:
    if b:
        if c:
            pass
'''
        tree = ast.parse(code)
        visitor = ComplexityVisitor()
        visitor.visit(tree)
        self.assertEqual(visitor.max_depth, 3)


class TestCodeSmellDetector(unittest.TestCase):
    """Tests for CodeSmellDetector."""

    def setUp(self):
        """Set up test fixtures."""
        config = CodeSmellConfig(
            max_method_lines=10,
            max_class_methods=10,
            max_parameters=3,
        )
        self.detector = CodeSmellDetector(config=config)

    def test_detect_long_method(self):
        """Test detection of long methods."""
        result = self.detector.detect(COMPLEX_FUNCTION)
        smells = result["smells"]
        smell_names = [s["name"] for s in smells]
        self.assertIn("long_method", smell_names)

    def test_detect_too_many_parameters(self):
        """Test detection of too many parameters."""
        result = self.detector.detect(COMPLEX_FUNCTION)
        smells = result["smells"]
        smell_names = [s["name"] for s in smells]
        self.assertIn("too_many_parameters", smell_names)

    def test_detect_too_many_methods(self):
        """Test detection of too many methods."""
        result = self.detector.detect(LARGE_CLASS)
        smells = result["smells"]
        smell_names = [s["name"] for s in smells]
        self.assertIn("too_many_methods", smell_names)

    def test_feature_envy_detection(self):
        """Test feature envy detection."""
        result = self.detector.detect(FEATURE_ENVY_CODE)
        smells = result["smells"]
        smell_names = [s["name"] for s in smells]
        self.assertIn("feature_envy", smell_names)

    def test_deep_nesting_detection(self):
        """Test deep nesting detection."""
        config = CodeSmellConfig(max_nested_depth=2)
        detector = CodeSmellDetector(config=config)
        result = detector.detect(COMPLEX_FUNCTION)
        smells = result["smells"]
        smell_names = [s["name"] for s in smells]
        self.assertIn("deep_nesting", smell_names)

    def test_smell_severity(self):
        """Test smell severity levels."""
        result = self.detector.detect(LARGE_CLASS)
        smells = result["smells"]
        severities = {s["severity"] for s in smells}
        # Should have various severity levels
        self.assertTrue(len(severities) >= 1)

    def test_summary_generation(self):
        """Test summary is generated correctly."""
        result = self.detector.detect(COMPLEX_FUNCTION)
        summary = result["summary"]
        self.assertIn("total", summary)
        self.assertIn("by_severity", summary)
        self.assertIn("by_type", summary)


class TestCodeSmell(unittest.TestCase):
    """Tests for CodeSmell dataclass."""

    def test_to_dict(self):
        """Test conversion to dictionary."""
        smell = CodeSmell(
            name="long_method",
            description="Method is too long",
            severity=SmellSeverity.HIGH,
            location="file.py::method",
            lineno=10,
            suggestion="Extract methods",
        )
        d = smell.to_dict()
        self.assertEqual(d["name"], "long_method")
        self.assertEqual(d["severity"], "high")
        self.assertEqual(d["lineno"], 10)


class TestTechDebtTracker(unittest.TestCase):
    """Tests for TechDebtTracker."""

    def setUp(self):
        """Set up test fixtures."""
        self.tracker = TechDebtTracker()

    def test_add_item(self):
        """Test adding debt items."""
        item = TechDebtItem(
            id="",
            title="Fix broken test",
            description="Test is flaky",
            category=DebtCategory.TESTING,
            priority=DebtPriority.HIGH,
            location="tests/test_example.py",
            lineno=42,
        )
        item_id = self.tracker.add_item(item)
        self.assertIsNotNone(item_id)
        self.assertEqual(len(self.tracker.items), 1)

    def test_remove_item(self):
        """Test removing debt items."""
        item = TechDebtItem(
            id="test123",
            title="Test item",
            description="Description",
            category=DebtCategory.CODE_QUALITY,
            priority=DebtPriority.LOW,
            location="file.py",
            lineno=1,
        )
        self.tracker.add_item(item)
        result = self.tracker.remove_item("test123")
        self.assertTrue(result)
        self.assertEqual(len(self.tracker.items), 0)

    def test_scan_file_todos(self):
        """Test scanning file for TODOs."""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".py", delete=False
        ) as f:
            f.write(CODE_WITH_TODOS)
            f.flush()
            items = self.tracker.scan_file(f.name)
            self.assertGreaterEqual(len(items), 3)  # TODO, FIXME, HACK

    def test_import_from_analysis(self):
        """Test importing from analysis results."""
        smells = [
            {
                "name": "long_method",
                "description": "Method too long",
                "severity": "high",
                "location": "file.py::method",
                "lineno": 10,
            }
        ]
        violations = [
            {
                "function": "complex_func",
                "type": "cyclomatic_complexity",
                "value": 15,
                "threshold": 10,
                "lineno": 5,
            }
        ]
        items = self.tracker.import_from_analysis(smells, violations)
        self.assertEqual(len(items), 2)

    def test_get_prioritized(self):
        """Test getting items sorted by priority."""
        self.tracker.add_item(TechDebtItem(
            id="", title="Low", description="", category=DebtCategory.CODE_QUALITY,
            priority=DebtPriority.LOW, location="", lineno=1,
        ))
        self.tracker.add_item(TechDebtItem(
            id="", title="Critical", description="", category=DebtCategory.SECURITY,
            priority=DebtPriority.CRITICAL, location="", lineno=1,
        ))
        prioritized = self.tracker.get_prioritized()
        self.assertEqual(prioritized[0].priority, DebtPriority.CRITICAL)

    def test_get_summary(self):
        """Test summary generation."""
        self.tracker.add_item(TechDebtItem(
            id="", title="Item 1", description="", category=DebtCategory.CODE_QUALITY,
            priority=DebtPriority.HIGH, location="", lineno=1, estimated_hours=2.0,
        ))
        summary = self.tracker.get_summary()
        self.assertEqual(summary["total_items"], 1)
        self.assertEqual(summary["total_estimated_hours"], 2.0)

    def test_persistence(self):
        """Test saving and loading from file."""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False
        ) as f:
            storage_path = f.name

        tracker1 = TechDebtTracker(storage_path=storage_path)
        tracker1.add_item(TechDebtItem(
            id="persist1", title="Persistent", description="Test persistence",
            category=DebtCategory.ARCHITECTURE, priority=DebtPriority.MEDIUM,
            location="file.py", lineno=1,
        ))

        # Create new tracker that loads from same file
        tracker2 = TechDebtTracker(storage_path=storage_path)
        self.assertEqual(len(tracker2.items), 1)
        self.assertEqual(tracker2.items[0].id, "persist1")

        # Cleanup
        Path(storage_path).unlink()


class TestTechDebtItem(unittest.TestCase):
    """Tests for TechDebtItem dataclass."""

    def test_auto_id_generation(self):
        """Test automatic ID generation."""
        item = TechDebtItem(
            id="",
            title="Test",
            description="Desc",
            category=DebtCategory.CODE_QUALITY,
            priority=DebtPriority.LOW,
            location="file.py",
            lineno=1,
        )
        self.assertTrue(len(item.id) > 0)

    def test_auto_timestamp(self):
        """Test automatic timestamp generation."""
        item = TechDebtItem(
            id="",
            title="Test",
            description="Desc",
            category=DebtCategory.CODE_QUALITY,
            priority=DebtPriority.LOW,
            location="file.py",
            lineno=1,
        )
        self.assertTrue(len(item.created_at) > 0)

    def test_from_dict(self):
        """Test creation from dictionary."""
        data = {
            "id": "abc123",
            "title": "Test",
            "description": "Desc",
            "category": "code_quality",
            "priority": "HIGH",
            "location": "file.py",
            "lineno": 42,
        }
        item = TechDebtItem.from_dict(data)
        self.assertEqual(item.id, "abc123")
        self.assertEqual(item.priority, DebtPriority.HIGH)


class TestRefactoringAdvisor(unittest.TestCase):
    """Tests for RefactoringAdvisor."""

    def setUp(self):
        """Set up test fixtures."""
        self.advisor = RefactoringAdvisor()

    def test_analyze_smells(self):
        """Test analyzing code smells."""
        smells = [
            {
                "name": "long_method",
                "description": "Method too long",
                "severity": "high",
                "location": "file.py::method",
                "lineno": 10,
            }
        ]
        suggestions = self.advisor.analyze(smells)
        self.assertGreater(len(suggestions), 0)
        suggestion_types = [s.refactoring_type for s in suggestions]
        self.assertIn(RefactoringType.EXTRACT_METHOD, suggestion_types)

    def test_analyze_complexity_violations(self):
        """Test analyzing complexity violations."""
        violations = [
            {
                "function": "complex_func",
                "type": "cyclomatic_complexity",
                "value": 15,
                "threshold": 10,
                "lineno": 5,
                "file": "file.py",
            }
        ]
        suggestions = self.advisor.analyze([], violations)
        self.assertGreater(len(suggestions), 0)

    def test_get_refactoring_guidance(self):
        """Test getting detailed guidance."""
        guidance = self.advisor.get_refactoring_guidance(
            RefactoringType.EXTRACT_METHOD
        )
        self.assertIn("description", guidance)
        self.assertIn("steps", guidance)
        self.assertIn("example", guidance)

    def test_suggest_for_smell(self):
        """Test getting suggestions for specific smell."""
        suggestions = self.advisor.suggest_for_smell("god_class")
        self.assertIn(RefactoringType.EXTRACT_CLASS, suggestions)

    def test_to_dict(self):
        """Test conversion to dictionary."""
        smells = [
            {
                "name": "deep_nesting",
                "description": "Too deep",
                "severity": "high",
                "location": "file.py",
                "lineno": 1,
            }
        ]
        suggestions = self.advisor.analyze(smells)
        result = self.advisor.to_dict(suggestions)
        self.assertIn("suggestions", result)
        self.assertIn("summary", result)


class TestRefactoringSuggestion(unittest.TestCase):
    """Tests for RefactoringSuggestion dataclass."""

    def test_to_dict(self):
        """Test conversion to dictionary."""
        suggestion = RefactoringSuggestion(
            refactoring_type=RefactoringType.GUARD_CLAUSE,
            title="Apply Guard Clause",
            description="Use early returns",
            location="file.py::method",
            lineno=10,
            impact="medium",
            effort="low",
            steps=["Step 1", "Step 2"],
        )
        d = suggestion.to_dict()
        self.assertEqual(d["refactoring_type"], "guard_clause")
        self.assertEqual(d["impact"], "medium")
        self.assertEqual(len(d["steps"]), 2)


class TestMetricsReporter(unittest.TestCase):
    """Tests for MetricsReporter."""

    def setUp(self):
        """Set up test fixtures."""
        self.reporter = MetricsReporter()
        self.sample_data = {
            "summary": {
                "total_functions": 10,
                "total_smells": 5,
                "max_cyclomatic": 15,
            },
            "violations": [
                {
                    "function": "complex_func",
                    "type": "cyclomatic_complexity",
                    "value": 15,
                    "threshold": 10,
                    "lineno": 5,
                }
            ],
            "smells": [
                {
                    "name": "long_method",
                    "severity": "high",
                    "location": "file.py::method",
                    "lineno": 10,
                    "description": "Method too long",
                }
            ],
            "suggestions": [
                {
                    "title": "Extract Method",
                    "description": "Extract code to method",
                    "location": "file.py::method",
                    "lineno": 10,
                    "impact": "high",
                    "effort": "low",
                    "steps": ["Step 1"],
                }
            ],
        }

    def test_generate_json(self):
        """Test JSON report generation."""
        report = self.reporter.generate(self.sample_data, ReportFormat.JSON)
        data = json.loads(report)
        self.assertIn("summary", data)
        self.assertIn("generated_at", data)

    def test_generate_html(self):
        """Test HTML report generation."""
        report = self.reporter.generate(self.sample_data, ReportFormat.HTML)
        self.assertIn("<html", report)
        self.assertIn("Code Analysis Report", report)
        self.assertIn("long_method", report)

    def test_generate_text(self):
        """Test text report generation."""
        report = self.reporter.generate(self.sample_data, ReportFormat.TEXT)
        self.assertIn("SUMMARY", report)
        self.assertIn("COMPLEXITY VIOLATIONS", report)
        self.assertIn("CODE SMELLS", report)

    def test_generate_markdown(self):
        """Test Markdown report generation."""
        report = self.reporter.generate(self.sample_data, ReportFormat.MARKDOWN)
        self.assertIn("# Code Analysis Report", report)
        self.assertIn("## Summary", report)
        self.assertIn("|", report)  # Table syntax

    def test_output_to_file(self):
        """Test writing report to file."""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False
        ) as f:
            output_path = f.name

        self.reporter.generate(
            self.sample_data, ReportFormat.JSON, output_path
        )

        with open(output_path) as f:
            data = json.load(f)
            self.assertIn("summary", data)

        Path(output_path).unlink()

    def test_custom_config(self):
        """Test reporter with custom configuration."""
        config = ReportConfig(
            title="Custom Report",
            include_suggestions=False,
            max_items_per_section=5,
        )
        reporter = MetricsReporter(config=config)
        report = reporter.generate(self.sample_data, ReportFormat.TEXT)
        self.assertIn("Custom Report", report)

    def test_combine_results(self):
        """Test combining results from multiple analyzers."""
        complexity_result = {
            "filename": "file.py",
            "summary": {"total_functions": 5, "max_cyclomatic": 10},
            "violations": [],
        }
        smell_result = {
            "filename": "file.py",
            "summary": {"total": 3},
            "smells": [],
        }
        refactoring_result = {
            "summary": {"total": 2},
            "suggestions": [],
        }

        combined = self.reporter.combine_results(
            complexity_result, smell_result, refactoring_result
        )

        self.assertIn("summary", combined)
        self.assertEqual(combined["summary"]["total_functions"], 5)
        self.assertEqual(combined["summary"]["total_smells"], 3)


class TestIntegration(unittest.TestCase):
    """Integration tests combining multiple components."""

    def test_full_analysis_pipeline(self):
        """Test complete analysis pipeline."""
        # Analyze code
        analyzer = ComplexityAnalyzer()
        complexity_result = analyzer.analyze_code(COMPLEX_FUNCTION)

        detector = CodeSmellDetector()
        smell_result = detector.detect(COMPLEX_FUNCTION)

        advisor = RefactoringAdvisor()
        suggestions = advisor.analyze(
            smell_result.get("smells", []),
            complexity_result.get("violations", []),
        )

        tracker = TechDebtTracker()
        tracker.import_from_analysis(
            smell_result.get("smells", []),
            complexity_result.get("violations", []),
        )

        reporter = MetricsReporter()
        combined = reporter.combine_results(
            complexity_result,
            smell_result,
            advisor.to_dict(suggestions),
            tracker.to_dict(),
        )

        # Generate reports in all formats
        json_report = reporter.generate(combined, ReportFormat.JSON)
        html_report = reporter.generate(combined, ReportFormat.HTML)
        text_report = reporter.generate(combined, ReportFormat.TEXT)
        md_report = reporter.generate(combined, ReportFormat.MARKDOWN)

        # Verify all reports generated successfully
        self.assertIn("summary", json_report)
        self.assertIn("<html", html_report)
        self.assertIn("SUMMARY", text_report)
        self.assertIn("# Code Analysis Report", md_report)

    def test_file_based_analysis(self):
        """Test file-based analysis workflow."""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".py", delete=False
        ) as f:
            f.write(COMPLEX_FUNCTION)
            f.write("\n")
            f.write(CODE_WITH_TODOS)
            f.flush()
            filepath = f.name

        try:
            analyzer = ComplexityAnalyzer()
            result = analyzer.analyze_file(filepath)
            self.assertIn("functions", result)

            detector = CodeSmellDetector()
            smells = detector.detect_file(filepath)
            self.assertIn("smells", smells)

            tracker = TechDebtTracker()
            todos = tracker.scan_file(filepath)
            self.assertGreater(len(todos), 0)
        finally:
            Path(filepath).unlink()


if __name__ == "__main__":
    unittest.main()
