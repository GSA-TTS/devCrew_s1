"""
Code Analysis & Quality Metrics Platform.

Provides tools for analyzing Python code quality including:
- Cyclomatic and cognitive complexity analysis
- Code smell detection
- Technical debt tracking
- Refactoring suggestions
- Metrics reporting
"""

from .complexity_analyzer import (
    ComplexityAnalyzer,
    ComplexityMetrics,
    HalsteadMetrics,
)
from .code_smell_detector import (
    CodeSmellDetector,
    CodeSmell,
    SmellSeverity,
)
from .tech_debt_tracker import (
    TechDebtTracker,
    TechDebtItem,
    DebtPriority,
)
from .refactoring_advisor import (
    RefactoringAdvisor,
    RefactoringSuggestion,
    RefactoringType,
)
from .metrics_reporter import (
    MetricsReporter,
    ReportFormat,
)

__all__ = [
    "ComplexityAnalyzer",
    "ComplexityMetrics",
    "HalsteadMetrics",
    "CodeSmellDetector",
    "CodeSmell",
    "SmellSeverity",
    "TechDebtTracker",
    "TechDebtItem",
    "DebtPriority",
    "RefactoringAdvisor",
    "RefactoringSuggestion",
    "RefactoringType",
    "MetricsReporter",
    "ReportFormat",
]

__version__ = "1.0.0"
