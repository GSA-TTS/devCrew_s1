# Code Analysis & Quality Metrics Platform

A comprehensive Python code analysis tool that provides complexity metrics, code smell detection, technical debt tracking, and refactoring suggestions.

## Features

- **Complexity Analysis**: Cyclomatic complexity, cognitive complexity, and Halstead metrics
- **Code Smell Detection**: Identifies long methods, large classes, deep nesting, feature envy, and more
- **Technical Debt Tracking**: Track, categorize, and prioritize technical debt items
- **Refactoring Advisor**: Suggests appropriate refactoring patterns based on detected issues
- **Multiple Report Formats**: JSON, HTML, Text, and Markdown output

## Installation

No external dependencies required. Uses Python standard library only.

```bash
cd tools/code_analysis
python -m pytest test_code_analysis.py -v
```

## Usage

### Command Line Interface

```bash
# Analyze a single file
python code_analyzer.py analyze path/to/file.py

# Analyze a directory
python code_analyzer.py analyze src/ --format html --output report.html

# With custom thresholds
python code_analyzer.py analyze . --cyclomatic-threshold 15 --max-method-lines 50

# Exclude test files
python code_analyzer.py analyze src/ --exclude 'test_*' '*_test.py'

# Manage technical debt
python code_analyzer.py debt scan --path src/
python code_analyzer.py debt list
python code_analyzer.py debt summary
```

### Python API

```python
from complexity_analyzer import ComplexityAnalyzer
from code_smell_detector import CodeSmellDetector
from tech_debt_tracker import TechDebtTracker
from refactoring_advisor import RefactoringAdvisor
from metrics_reporter import MetricsReporter, ReportFormat

# Analyze complexity
analyzer = ComplexityAnalyzer(cyclomatic_threshold=10)
result = analyzer.analyze_file("myfile.py")
print(f"Max complexity: {result['summary']['max_cyclomatic']}")

# Detect code smells
detector = CodeSmellDetector()
smells = detector.detect_file("myfile.py")
for smell in smells["smells"]:
    print(f"[{smell['severity']}] {smell['name']} at line {smell['lineno']}")

# Get refactoring suggestions
advisor = RefactoringAdvisor()
suggestions = advisor.analyze(smells["smells"])
for s in suggestions:
    print(f"Suggestion: {s.title}")
    print(f"  Steps: {s.steps}")

# Track technical debt
tracker = TechDebtTracker(storage_path=".tech_debt.json")
tracker.scan_directory("src/")
summary = tracker.get_summary()
print(f"Total debt items: {summary['total_items']}")
print(f"Estimated hours: {summary['total_estimated_hours']}")

# Generate report
reporter = MetricsReporter()
report = reporter.generate(result, ReportFormat.HTML, "report.html")
```

## Metrics Explained

### Cyclomatic Complexity
Measures the number of linearly independent paths through code. Each decision point (if, for, while, etc.) increases complexity.
- **Threshold default**: 10
- **1-10**: Simple, low risk
- **11-20**: Moderate complexity
- **21-50**: High complexity, consider refactoring
- **51+**: Very high risk, refactor immediately

### Cognitive Complexity
Measures how difficult code is to understand, accounting for nesting depth and control flow breaks.
- **Threshold default**: 15

### Halstead Metrics
- **Volume**: Program size based on operators and operands
- **Difficulty**: How hard the program is to understand
- **Effort**: Estimated mental effort to develop
- **Bugs Estimate**: Predicted number of bugs

## Code Smells Detected

| Smell | Description | Default Threshold |
|-------|-------------|-------------------|
| long_method | Method has too many lines | 30 lines |
| large_class | Class has too many lines | 300 lines |
| too_many_methods | Class has too many methods | 20 methods |
| too_many_parameters | Function has too many parameters | 5 parameters |
| deep_nesting | Code has too many nested levels | 4 levels |
| too_many_branches | Function has too many branches | 10 branches |
| too_many_returns | Function has too many return statements | 4 returns |
| feature_envy | Method uses another object's data excessively | 5 calls |
| god_class | Class doing too much (large + many methods) | Combined threshold |

## Refactoring Patterns

The advisor suggests these refactoring patterns:

- **Extract Method**: Break long methods into smaller, focused methods
- **Extract Class**: Split large classes into smaller, cohesive classes
- **Introduce Parameter Object**: Group related parameters into an object
- **Guard Clause**: Replace nested conditionals with early returns
- **Replace Conditional with Polymorphism**: Use inheritance instead of switch/if chains
- **Move Method**: Move method to the class it uses most
- **Decompose Conditional**: Extract conditions and branches to methods
- **Strategy Pattern**: Define interchangeable algorithm families

## Configuration

### ComplexityAnalyzer

```python
ComplexityAnalyzer(
    cyclomatic_threshold=10,    # Max cyclomatic complexity
    cognitive_threshold=15,     # Max cognitive complexity
    max_parameters=5,           # Max function parameters
    max_nested_depth=4,         # Max nesting depth
)
```

### CodeSmellDetector

```python
from code_smell_detector import CodeSmellConfig

config = CodeSmellConfig(
    max_method_lines=30,
    max_class_lines=300,
    max_class_methods=20,
    max_parameters=5,
    max_returns=4,
    max_branches=10,
    min_duplicate_lines=6,
    max_nested_depth=4,
    max_attributes=15,
    max_local_variables=15,
)
detector = CodeSmellDetector(config=config)
```

## Output Examples

### JSON Output
```json
{
  "summary": {
    "total_functions": 10,
    "avg_cyclomatic": 5.2,
    "max_cyclomatic": 15,
    "total_smells": 3
  },
  "violations": [...],
  "smells": [...],
  "suggestions": [...]
}
```

### HTML Report
Generates a styled HTML report with:
- Summary metrics dashboard
- Violations table with severity highlighting
- Code smells with suggestions
- Refactoring recommendations with step-by-step guidance

## License

MIT License
