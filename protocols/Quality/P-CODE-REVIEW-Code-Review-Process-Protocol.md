# CODE-REVIEW-001: Code Reviewing Protocol

**Version**: 1.0
**Last Updated**: 2025-11-17
**Status**: Active
**Owner**: Code-Reviewer

## Objective

Ensure comprehensive, consistent, and high-quality code review practices across all development projects, combining automated tool analysis with human expertise to identify bugs, security vulnerabilities, maintainability issues, and adherence to coding standards while fostering knowledge sharing and team collaboration.

## Trigger

- Pull request creation requiring code review approval
- Pre-commit hook execution for automated quality checks
- Feature development completion requiring quality validation
- Bug fix implementation requiring verification
- Security-sensitive code changes requiring additional scrutiny
- Architectural changes requiring cross-team review
- Performance-critical code modifications
- External contributor submissions requiring thorough review

## Agents

- **Primary**: Code-Reviewer
- **Supporting**: Senior-Developer (architectural review), Security-Engineer (security review), Performance-Engineer (performance analysis)
- **Review**: Technical-Lead (final approval), QA-Engineer (testing validation)
- **Coordination**: Development-Team-Lead (resource allocation), Project-Manager (timeline impact)

## Tool Requirements

- **TOOL-COLLAB-001** (GitHub Integration): Pull request management and repository operations
  - Execute: PR creation, review assignment, status updates, merge operations
  - Integration: CLI commands, API calls, webhook handling
- **TOOL-SEC-001** (SAST Scanner): Static code analysis and quality validation
  - Execute: Pre-commit hooks (flake8, mypy, pylint, bandit, black, isort), security scanning
  - Integration: CLI scanning, CI/CD pipeline integration, IDE plugins
- **TOOL-CICD-001** (Pipeline Platform): Automated quality gates and workflow execution
  - Execute: Automated review workflows, quality gate enforcement
  - Integration: Pipeline configuration, automated triggers

## Prerequisites

- Development environment configured with **TOOL-SEC-001** and **TOOL-COLLAB-001**
- Pre-commit hooks installed and functional via **TOOL-SEC-001** integration
- Pull request template and review guidelines established in **TOOL-COLLAB-001**
- Code quality standards and style guides documented
- **TOOL-SEC-001** configured for security scanning and code quality analysis
- Performance benchmarking infrastructure available
- **TOOL-COLLAB-001** integrated with issue tracking workflow

## Steps

### Step 1: Automated Pre-Commit Analysis (Estimated Time: 15m)
**Action**:
Execute comprehensive automated code quality checks before human review:

```bash
# Create audit directory structure
issue_number="${ISSUE_NUMBER:-$(git rev-parse --short HEAD)}"
timestamp=$(date +"%m%d%y_%H%M")
audit_dir="docs/audits/issue_${issue_number}"
mkdir -p "$audit_dir"

# Execute pre-commit checks with comprehensive reporting
execute_precommit_analysis() {
  echo "=== Pre-Commit Analysis Report ===" > "${audit_dir}/issue_${issue_number}_precommit_${timestamp}.md"
  echo "**Issue**: #${issue_number}" >> "${audit_dir}/issue_${issue_number}_precommit_${timestamp}.md"
  echo "**Timestamp**: $(date)" >> "${audit_dir}/issue_${issue_number}_precommit_${timestamp}.md"
  echo "**Git Commit**: $(git rev-parse HEAD)" >> "${audit_dir}/issue_${issue_number}_precommit_${timestamp}.md"  # TOOL-COLLAB-001
  echo "" >> "${audit_dir}/issue_${issue_number}_precommit_${timestamp}.md"

  # Code formatting analysis via TOOL-SEC-001
  echo "## Code Formatting (Black + isort)" >> "${audit_dir}/issue_${issue_number}_precommit_${timestamp}.md"
  black --check --diff . >> "${audit_dir}/issue_${issue_number}_precommit_${timestamp}.md" 2>&1 || echo "Black formatting issues detected"  # TOOL-SEC-001
  isort --check-only --diff . >> "${audit_dir}/issue_${issue_number}_precommit_${timestamp}.md" 2>&1 || echo "Import sorting issues detected"  # TOOL-SEC-001

  # Style and syntax analysis
  echo "## Style Analysis (flake8)" >> "${audit_dir}/issue_${issue_number}_precommit_${timestamp}.md"
  flake8 --max-line-length=88 --statistics --format='%(path)s:%(row)d:%(col)d: %(code)s %(text)s' . >> "${audit_dir}/issue_${issue_number}_precommit_${timestamp}.md" 2>&1

  # Type checking analysis
  echo "## Type Analysis (mypy)" >> "${audit_dir}/issue_${issue_number}_precommit_${timestamp}.md"
  mypy --ignore-missing-imports --show-error-codes --show-error-context . >> "${audit_dir}/issue_${issue_number}_precommit_${timestamp}.md" 2>&1

  # Code quality analysis
  echo "## Code Quality (pylint)" >> "${audit_dir}/issue_${issue_number}_precommit_${timestamp}.md"
  pylint --output-format=text --score=yes --reports=yes . >> "${audit_dir}/issue_${issue_number}_precommit_${timestamp}.md" 2>&1

  # Security analysis
  echo "## Security Analysis (bandit)" >> "${audit_dir}/issue_${issue_number}_precommit_${timestamp}.md"
  bandit -r . -f txt -o "${audit_dir}/bandit_report_${timestamp}.txt" 2>&1
  cat "${audit_dir}/bandit_report_${timestamp}.txt" >> "${audit_dir}/issue_${issue_number}_precommit_${timestamp}.md"

  # Complexity analysis
  echo "## Complexity Analysis" >> "${audit_dir}/issue_${issue_number}_precommit_${timestamp}.md"
  find . -name "*.py" -exec python -c "
import ast
import sys
from radon.complexity import cc_visit

with open(sys.argv[1], 'r') as f:
    try:
        tree = ast.parse(f.read())
        complexity = cc_visit(tree)
        for item in complexity:
            if item.complexity > 10:
                print(f'{sys.argv[1]}:{item.lineno}: {item.name} complexity: {item.complexity} (high)')
    except:
        pass
" {} \; >> "${audit_dir}/issue_${issue_number}_precommit_${timestamp}.md" 2>/dev/null
}

# Execute analysis
execute_precommit_analysis
```

Generate analysis summary:
```yaml
precommit_summary_${issue_number}.yaml:
  analysis_timestamp: "${timestamp}"
  issue_number: "${issue_number}"
  tools_executed:
    - tool: "black"
      status: "pass|fail"
      issues_count: 0
    - tool: "isort"
      status: "pass|fail"
      issues_count: 0
    - tool: "flake8"
      status: "pass|fail"
      issues_count: 0
    - tool: "mypy"
      status: "pass|fail"
      issues_count: 0
    - tool: "pylint"
      status: "pass|fail"
      score: 0.0
    - tool: "bandit"
      status: "pass|fail"
      security_issues: 0
  overall_status: "pass|conditional|fail"
  critical_issues: 0
  blocking_issues: []
```

**Expected Outcome**: Comprehensive automated analysis with detailed reporting
**Validation**: All tools executed successfully, results documented, critical issues flagged

### Step 2: Pull Request Validation (Estimated Time: 20m)
**Action**:
For significant changes (EPIC issues, architectural changes), execute enhanced pull request validation:

```bash
# Determine if enhanced validation is needed
determine_review_scope() {
  local pr_scope="standard"

  # Check if EPIC issue
  if gh issue view "${issue_number}" --json labels | jq -r '.labels[].name' | grep -q "epic"; then
    pr_scope="enhanced"
  fi

  # Check for architectural changes
  if git diff --name-only origin/main...HEAD | grep -E "(architecture|config|schema|migration)" >/dev/null; then
    pr_scope="enhanced"
  fi

  # Check for security-sensitive files
  if git diff --name-only origin/main...HEAD | grep -E "(auth|security|crypto|key)" >/dev/null; then
    pr_scope="security"
  fi

  echo "$pr_scope"
}

# Execute enhanced pull request checks
execute_enhanced_pr_checks() {
  local scope="$1"

  echo "=== Enhanced Pull Request Analysis ===" > "${audit_dir}/issue_${issue_number}_pullrequest_${timestamp}.md"
  echo "**Scope**: ${scope}" >> "${audit_dir}/issue_${issue_number}_pullrequest_${timestamp}.md"
  echo "**Files Changed**: $(git diff --name-only origin/main...HEAD | wc -l)" >> "${audit_dir}/issue_${issue_number}_pullrequest_${timestamp}.md"
  echo "" >> "${audit_dir}/issue_${issue_number}_pullrequest_${timestamp}.md"

  # Diff analysis
  echo "## Change Analysis" >> "${audit_dir}/issue_${issue_number}_pullrequest_${timestamp}.md"
  echo "### Files Modified" >> "${audit_dir}/issue_${issue_number}_pullrequest_${timestamp}.md"
  git diff --name-status origin/main...HEAD >> "${audit_dir}/issue_${issue_number}_pullrequest_${timestamp}.md"

  echo "### Lines of Code Changed" >> "${audit_dir}/issue_${issue_number}_pullrequest_${timestamp}.md"
  git diff --stat origin/main...HEAD >> "${audit_dir}/issue_${issue_number}_pullrequest_${timestamp}.md"

  # Test coverage analysis
  echo "## Test Coverage Analysis" >> "${audit_dir}/issue_${issue_number}_pullrequest_${timestamp}.md"
  if command -v pytest >/dev/null; then
    pytest --cov=. --cov-report=term-missing --cov-report=html:"${audit_dir}/coverage_${timestamp}" \
      >> "${audit_dir}/issue_${issue_number}_pullrequest_${timestamp}.md" 2>&1 || echo "Test execution failed"
  fi

  # Documentation analysis
  echo "## Documentation Analysis" >> "${audit_dir}/issue_${issue_number}_pullrequest_${timestamp}.md"
  if git diff --name-only origin/main...HEAD | grep -E "\.(md|rst|txt)$" >/dev/null; then
    echo "Documentation files modified:" >> "${audit_dir}/issue_${issue_number}_pullrequest_${timestamp}.md"
    git diff --name-only origin/main...HEAD | grep -E "\.(md|rst|txt)$" >> "${audit_dir}/issue_${issue_number}_pullrequest_${timestamp}.md"
  else
    echo "⚠️ No documentation updated for this change" >> "${audit_dir}/issue_${issue_number}_pullrequest_${timestamp}.md"
  fi

  # Breaking change analysis
  echo "## Breaking Change Analysis" >> "${audit_dir}/issue_${issue_number}_pullrequest_${timestamp}.md"
  analyze_breaking_changes >> "${audit_dir}/issue_${issue_number}_pullrequest_${timestamp}.md"
}

# Analyze breaking changes
analyze_breaking_changes() {
  echo "Analyzing potential breaking changes..."

  # API signature changes
  if git diff origin/main...HEAD | grep -E "^-.*def |^-.*class " >/dev/null; then
    echo "⚠️ Potential API changes detected:"
    git diff origin/main...HEAD | grep -E "^-.*def |^-.*class "
  fi

  # Database schema changes
  if git diff --name-only origin/main...HEAD | grep -E "(migration|schema)" >/dev/null; then
    echo "⚠️ Database schema changes detected"
  fi

  # Configuration changes
  if git diff --name-only origin/main...HEAD | grep -E "(config|settings|env)" >/dev/null; then
    echo "⚠️ Configuration changes detected"
  fi
}

# Execute based on scope
review_scope=$(determine_review_scope)
if [ "$review_scope" != "standard" ]; then
  execute_enhanced_pr_checks "$review_scope"
fi
```

**Expected Outcome**: Enhanced validation for complex changes with comprehensive analysis
**Validation**: Review scope determined, appropriate checks executed, change impact assessed

### Step 3: Issue and Failure Analysis (Estimated Time: 25m)
**Action**:
Parse and categorize all identified issues from automated tools:

```python
# Failure analysis and categorization
import re
import yaml
from pathlib import Path
from typing import Dict, List, Any

class CodeReviewAnalyzer:
    def __init__(self, issue_number: str, audit_dir: str):
        self.issue_number = issue_number
        self.audit_dir = Path(audit_dir)
        self.failure_tracker = {
            "critical_issues": [],
            "major_issues": [],
            "minor_issues": [],
            "style_issues": [],
            "security_issues": [],
            "performance_issues": [],
            "tool_conflicts": []
        }

    def parse_precommit_results(self, precommit_file: str) -> None:
        """Parse pre-commit results and categorize issues"""
        with open(precommit_file, 'r') as f:
            content = f.read()

        # Parse flake8 issues
        flake8_issues = re.findall(r'(.+):(\d+):(\d+): ([EWFCRN]\d+) (.+)', content)
        for file_path, line, col, code, message in flake8_issues:
            severity = self._categorize_flake8_issue(code)
            self.failure_tracker[f"{severity}_issues"].append({
                "tool": "flake8",
                "file": file_path,
                "line": int(line),
                "column": int(col),
                "code": code,
                "message": message,
                "severity": severity
            })

        # Parse mypy issues
        mypy_issues = re.findall(r'(.+):(\d+): (error|warning|note): (.+)', content)
        for file_path, line, level, message in mypy_issues:
            severity = "critical" if level == "error" else "minor"
            self.failure_tracker[f"{severity}_issues"].append({
                "tool": "mypy",
                "file": file_path,
                "line": int(line),
                "level": level,
                "message": message,
                "severity": severity
            })

        # Parse bandit security issues
        bandit_issues = re.findall(r'>> Issue: \[(.+)\] (.+)', content)
        for severity_code, description in bandit_issues:
            self.failure_tracker["security_issues"].append({
                "tool": "bandit",
                "severity_code": severity_code,
                "description": description,
                "severity": "critical" if "HIGH" in severity_code else "major"
            })

        # Parse pylint issues
        pylint_score = re.search(r'Your code has been rated at ([\d.]+)/10', content)
        if pylint_score and float(pylint_score.group(1)) < 7.0:
            self.failure_tracker["major_issues"].append({
                "tool": "pylint",
                "issue": "low_code_quality",
                "score": float(pylint_score.group(1)),
                "message": f"Code quality score {pylint_score.group(1)}/10 below threshold (7.0)",
                "severity": "major"
            })

    def _categorize_flake8_issue(self, code: str) -> str:
        """Categorize flake8 issues by severity"""
        critical_codes = ['E999', 'F821', 'F822', 'F831']  # Syntax errors, undefined names
        major_codes = ['E301', 'E302', 'E303', 'W292', 'W293']  # Formatting issues

        if code in critical_codes:
            return "critical"
        elif code in major_codes:
            return "major"
        elif code.startswith('E'):
            return "minor"
        else:
            return "style"

    def detect_tool_conflicts(self) -> None:
        """Detect conflicts between different tools"""
        # Example: Black vs flake8 line length conflicts
        black_line_length = 88
        flake8_line_length_issues = [
            issue for issue in self.failure_tracker["style_issues"]
            if issue.get("tool") == "flake8" and "E501" in issue.get("code", "")
        ]

        if flake8_line_length_issues:
            self.failure_tracker["tool_conflicts"].append({
                "tools": ["black", "flake8"],
                "conflict": "line_length_mismatch",
                "description": "flake8 line length conflicts with black formatting",
                "resolution": "Configure flake8 max-line-length to 88",
                "affected_issues": len(flake8_line_length_issues)
            })

    def generate_failure_tracker(self) -> None:
        """Generate structured failure tracker markdown"""
        tracker_path = self.audit_dir / "failure_tracker.md"

        with open(tracker_path, 'w') as f:
            f.write(f"# Failure Tracker - Issue #{self.issue_number}\n\n")
            f.write(f"**Generated**: {datetime.now().isoformat()}\n\n")

            # Summary
            total_issues = sum(len(issues) for category, issues in self.failure_tracker.items() if category != "tool_conflicts")
            f.write(f"## Summary\n")
            f.write(f"- **Total Issues**: {total_issues}\n")
            f.write(f"- **Critical**: {len(self.failure_tracker['critical_issues'])}\n")
            f.write(f"- **Major**: {len(self.failure_tracker['major_issues'])}\n")
            f.write(f"- **Minor**: {len(self.failure_tracker['minor_issues'])}\n")
            f.write(f"- **Style**: {len(self.failure_tracker['style_issues'])}\n")
            f.write(f"- **Security**: {len(self.failure_tracker['security_issues'])}\n")
            f.write(f"- **Tool Conflicts**: {len(self.failure_tracker['tool_conflicts'])}\n\n")

            # Detailed issues by category
            for category, issues in self.failure_tracker.items():
                if issues:
                    f.write(f"## {category.replace('_', ' ').title()}\n\n")
                    for i, issue in enumerate(issues, 1):
                        f.write(f"### {i}. {issue.get('tool', 'Unknown')} - {issue.get('message', issue.get('description', 'No description'))}\n")
                        f.write(f"- **File**: {issue.get('file', 'N/A')}\n")
                        f.write(f"- **Line**: {issue.get('line', 'N/A')}\n")
                        f.write(f"- **Severity**: {issue.get('severity', 'unknown')}\n")
                        if 'code' in issue:
                            f.write(f"- **Code**: {issue['code']}\n")
                        f.write("\n")

        # Generate YAML summary for automation
        summary_path = self.audit_dir / f"failure_summary_{self.issue_number}.yaml"
        with open(summary_path, 'w') as f:
            yaml.dump(self.failure_tracker, f, default_flow_style=False)

# Execute failure analysis
analyzer = CodeReviewAnalyzer(issue_number, audit_dir)
precommit_file = f"{audit_dir}/issue_{issue_number}_precommit_{timestamp}.md"
if Path(precommit_file).exists():
    analyzer.parse_precommit_results(precommit_file)

analyzer.detect_tool_conflicts()
analyzer.generate_failure_tracker()
```

**Expected Outcome**: Structured analysis of all issues with categorization and conflict detection
**Validation**: All issues parsed and categorized, tool conflicts identified, failure tracker generated

### Step 4: Tool Configuration Optimization (Estimated Time: 15m)
**Action**:
Resolve tool conflicts and optimize configuration for consistent results:

```bash
# Tool configuration optimization
optimize_tool_configurations() {
  echo "=== Tool Configuration Optimization ===" > "${audit_dir}/tool_optimization_${timestamp}.md"

  # Check for common conflicts
  check_black_flake8_conflict() {
    if grep -q "E501" "${audit_dir}/failure_tracker.md" 2>/dev/null; then
      echo "## Black + flake8 Line Length Conflict" >> "${audit_dir}/tool_optimization_${timestamp}.md"
      echo "**Issue**: flake8 E501 conflicts with black formatting" >> "${audit_dir}/tool_optimization_${timestamp}.md"
      echo "**Solution**: Configure flake8 max-line-length to 88" >> "${audit_dir}/tool_optimization_${timestamp}.md"

      # Update setup.cfg or pyproject.toml
      if [ -f "setup.cfg" ]; then
        sed -i.bak '/\[flake8\]/a max-line-length = 88' setup.cfg
        echo "Updated setup.cfg with max-line-length = 88" >> "${audit_dir}/tool_optimization_${timestamp}.md"
      elif [ -f "pyproject.toml" ]; then
        if ! grep -q "max-line-length" pyproject.toml; then
          echo -e "\n[tool.flake8]\nmax-line-length = 88" >> pyproject.toml
          echo "Updated pyproject.toml with max-line-length = 88" >> "${audit_dir}/tool_optimization_${timestamp}.md"
        fi
      fi
    fi
  }

  # Check for mypy + pylint conflicts
  check_mypy_pylint_conflict() {
    if grep -q "import-error" "${audit_dir}/failure_tracker.md" 2>/dev/null; then
      echo "## MyPy + PyLint Import Conflict" >> "${audit_dir}/tool_optimization_${timestamp}.md"
      echo "**Issue**: Import resolution differences between mypy and pylint" >> "${audit_dir}/tool_optimization_${timestamp}.md"
      echo "**Solution**: Align ignore patterns and import resolution" >> "${audit_dir}/tool_optimization_${timestamp}.md"
    fi
  }

  # Check for bandit false positives
  check_bandit_optimization() {
    if grep -q "nosec" "${audit_dir}"/*.md 2>/dev/null; then
      echo "## Bandit False Positives" >> "${audit_dir}/tool_optimization_${timestamp}.md"
      echo "**Issue**: Legitimate nosec comments may indicate tool tuning needed" >> "${audit_dir}/tool_optimization_${timestamp}.md"
      echo "**Solution**: Review bandit configuration for project-specific rules" >> "${audit_dir}/tool_optimization_${timestamp}.md"
    fi
  }

  check_black_flake8_conflict
  check_mypy_pylint_conflict
  check_bandit_optimization
}

# Generate unified configuration
generate_unified_config() {
  echo "## Recommended Unified Configuration" >> "${audit_dir}/tool_optimization_${timestamp}.md"
  echo "" >> "${audit_dir}/tool_optimization_${timestamp}.md"
  echo "### pyproject.toml" >> "${audit_dir}/tool_optimization_${timestamp}.md"
  echo '```toml' >> "${audit_dir}/tool_optimization_${timestamp}.md"
  cat << 'EOF' >> "${audit_dir}/tool_optimization_${timestamp}.md"
[tool.black]
line-length = 88
target-version = ['py38']

[tool.isort]
profile = "black"
line_length = 88

[tool.flake8]
max-line-length = 88
extend-ignore = ["E203", "W503"]

[tool.mypy]
python_version = "3.8"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true

[tool.pylint.messages_control]
disable = ["C0103", "R0903"]

[tool.bandit]
exclude_dirs = ["tests", "test_*.py"]
skips = ["B101", "B601"]
EOF
  echo '```' >> "${audit_dir}/tool_optimization_${timestamp}.md"
}

optimize_tool_configurations
generate_unified_config
```

**Expected Outcome**: Optimized tool configurations with conflict resolution
**Validation**: Tool conflicts resolved, unified configuration generated, documentation updated

### Step 5: Human Code Review (Estimated Time: 45m)
**Action**:
Conduct systematic human review focusing on areas automated tools cannot evaluate:

```yaml
human_review_checklist_${issue_number}.yaml:
  architectural_review:
    design_patterns:
      score: 1-5  # 1=poor, 5=excellent
      notes: "Evaluation of design pattern usage and appropriateness"
      issues: []

    code_organization:
      score: 1-5
      notes: "Module structure, separation of concerns, cohesion"
      issues: []

    interface_design:
      score: 1-5
      notes: "API design, function signatures, abstraction levels"
      issues: []

  logic_and_correctness:
    algorithm_efficiency:
      score: 1-5
      notes: "Algorithm choice and implementation efficiency"
      issues: []

    edge_case_handling:
      score: 1-5
      notes: "Proper handling of edge cases and error conditions"
      issues: []

    business_logic_accuracy:
      score: 1-5
      notes: "Correctness of business logic implementation"
      issues: []

  maintainability:
    code_readability:
      score: 1-5
      notes: "Variable names, function clarity, commenting"
      issues: []

    documentation_quality:
      score: 1-5
      notes: "Docstrings, comments, README updates"
      issues: []

    test_coverage_adequacy:
      score: 1-5
      notes: "Test comprehensiveness and quality"
      issues: []

  security_and_performance:
    security_best_practices:
      score: 1-5
      notes: "Secure coding practices, input validation"
      issues: []

    performance_considerations:
      score: 1-5
      notes: "Performance implications, resource usage"
      issues: []

    scalability_impact:
      score: 1-5
      notes: "Impact on system scalability"
      issues: []

  overall_assessment:
    recommendation: "approve|approve_with_conditions|request_changes|reject"
    blocking_issues: []
    suggestions: []
    follow_up_actions: []
```

Conduct systematic review:
```markdown
# Human Code Review Report
## Issue: #${issue_number}
## Reviewer: ${reviewer_name}
## Review Date: $(date)

### Change Summary
**Files Modified**: $(git diff --name-only origin/main...HEAD | wc -l)
**Lines Added**: $(git diff --stat origin/main...HEAD | tail -1 | grep -o '[0-9]* insertion' | cut -d' ' -f1)
**Lines Removed**: $(git diff --stat origin/main...HEAD | tail -1 | grep -o '[0-9]* deletion' | cut -d' ' -f1)

### Architectural Assessment
- **Design Patterns**: [Score 1-5] [Comments]
- **Code Organization**: [Score 1-5] [Comments]
- **Interface Design**: [Score 1-5] [Comments]

### Logic and Correctness
- **Algorithm Efficiency**: [Score 1-5] [Comments]
- **Edge Case Handling**: [Score 1-5] [Comments]
- **Business Logic**: [Score 1-5] [Comments]

### Security Review
- **Input Validation**: [Pass/Fail] [Comments]
- **Authentication/Authorization**: [Pass/Fail] [Comments]
- **Data Sanitization**: [Pass/Fail] [Comments]

### Performance Analysis
- **Resource Usage**: [Acceptable/Concerning] [Comments]
- **Scalability Impact**: [Positive/Neutral/Negative] [Comments]
- **Bottleneck Identification**: [None/Minor/Major] [Comments]

### Recommendations
1. [Specific actionable feedback]
2. [Specific actionable feedback]
3. [Specific actionable feedback]

### Final Decision
☐ **Approve** - Ready to merge
☐ **Approve with Conditions** - Minor issues to address
☐ **Request Changes** - Significant issues requiring fixes
☐ **Reject** - Major problems requiring redesign
```

**Expected Outcome**: Comprehensive human review with detailed feedback and recommendations
**Validation**: All review areas assessed, specific feedback provided, clear recommendation given

### Step 6: Test Coverage and Quality Analysis (Estimated Time: 20m)
**Action**:
Analyze test coverage and quality to ensure adequate testing:

```bash
# Test coverage analysis
analyze_test_coverage() {
  echo "=== Test Coverage Analysis ===" > "${audit_dir}/test_coverage_${timestamp}.md"

  # Run pytest with coverage
  if command -v pytest >/dev/null; then
    echo "## Coverage Report" >> "${audit_dir}/test_coverage_${timestamp}.md"
    pytest --cov=. --cov-report=term-missing --cov-report=html:"${audit_dir}/htmlcov" \
      --cov-report=xml:"${audit_dir}/coverage.xml" \
      --junitxml="${audit_dir}/junit.xml" \
      >> "${audit_dir}/test_coverage_${timestamp}.md" 2>&1

    # Extract coverage percentage
    coverage_percent=$(grep -o "TOTAL.*[0-9]\+%" "${audit_dir}/test_coverage_${timestamp}.md" | grep -o "[0-9]\+%" | head -1)
    echo "**Overall Coverage**: ${coverage_percent:-0%}" >> "${audit_dir}/test_coverage_${timestamp}.md"
  fi

  # Analyze test quality
  echo "## Test Quality Analysis" >> "${audit_dir}/test_coverage_${timestamp}.md"

  # Count test files and test functions
  test_files=$(find . -name "test_*.py" -o -name "*_test.py" | wc -l)
  test_functions=$(grep -r "def test_" . --include="*.py" | wc -l)

  echo "- **Test Files**: ${test_files}" >> "${audit_dir}/test_coverage_${timestamp}.md"
  echo "- **Test Functions**: ${test_functions}" >> "${audit_dir}/test_coverage_${timestamp}.md"

  # Check for test patterns
  if grep -r "assert" . --include="test_*.py" >/dev/null 2>&1; then
    assert_count=$(grep -r "assert" . --include="test_*.py" | wc -l)
    echo "- **Assertions**: ${assert_count}" >> "${audit_dir}/test_coverage_${timestamp}.md"
  fi

  # Check for mock usage
  if grep -r "mock\|Mock\|patch" . --include="test_*.py" >/dev/null 2>&1; then
    mock_count=$(grep -r "mock\|Mock\|patch" . --include="test_*.py" | wc -l)
    echo "- **Mock Usage**: ${mock_count} instances" >> "${audit_dir}/test_coverage_${timestamp}.md"
  fi

  # Identify untested files
  echo "## Untested Files" >> "${audit_dir}/test_coverage_${timestamp}.md"
  python3 -c "
import coverage
import os

cov = coverage.Coverage()
try:
    cov.load()
    missing = []
    for filename in cov.get_data().measured_files():
        if filename.endswith('.py') and not filename.endswith('test.py'):
            analysis = cov.analysis(filename)
            if not analysis[1]:  # No executed lines
                missing.append(filename)

    if missing:
        print('Files with no test coverage:')
        for f in missing:
            print(f'- {f}')
    else:
        print('All measured files have some test coverage.')
except:
    print('Coverage data not available')
" >> "${audit_dir}/test_coverage_${timestamp}.md" 2>/dev/null || echo "Coverage analysis not available" >> "${audit_dir}/test_coverage_${timestamp}.md"
}

# Execute test coverage analysis
analyze_test_coverage
```

**Expected Outcome**: Detailed test coverage analysis with quality metrics
**Validation**: Coverage percentage calculated, test quality assessed, gaps identified

### Step 7: Security and Vulnerability Assessment (Estimated Time: 25m)
**Action**:
Conduct detailed security review beyond automated scanning:

```python
# Enhanced security analysis
import subprocess
import json
import yaml
from pathlib import Path

class SecurityAnalyzer:
    def __init__(self, audit_dir: str):
        self.audit_dir = Path(audit_dir)
        self.security_report = {
            "vulnerability_scan": {},
            "dependency_check": {},
            "code_secrets_scan": {},
            "security_hotspots": [],
            "recommendations": []
        }

    def run_dependency_check(self) -> None:
        """Check for known vulnerabilities in dependencies"""
        try:
            # Safety check for Python dependencies
            result = subprocess.run(['safety', 'check', '--json'],
                                  capture_output=True, text=True, timeout=60)
            if result.returncode == 0:
                self.security_report["dependency_check"] = {
                    "status": "clean",
                    "vulnerabilities": []
                }
            else:
                vulns = json.loads(result.stdout) if result.stdout else []
                self.security_report["dependency_check"] = {
                    "status": "vulnerabilities_found",
                    "count": len(vulns),
                    "vulnerabilities": vulns
                }
        except Exception as e:
            self.security_report["dependency_check"] = {
                "status": "error",
                "message": str(e)
            }

    def scan_for_secrets(self) -> None:
        """Scan for potential secrets in code"""
        secret_patterns = [
            (r'password\s*=\s*["\'][^"\']+["\']', 'hardcoded_password'),
            (r'api_key\s*=\s*["\'][^"\']+["\']', 'api_key'),
            (r'secret_key\s*=\s*["\'][^"\']+["\']', 'secret_key'),
            (r'token\s*=\s*["\'][^"\']+["\']', 'token'),
            (r'["\'][A-Za-z0-9]{32,}["\']', 'potential_key'),
        ]

        findings = []
        for py_file in Path('.').rglob('*.py'):
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    for i, line in enumerate(content.split('\n'), 1):
                        for pattern, secret_type in secret_patterns:
                            if re.search(pattern, line, re.IGNORECASE):
                                findings.append({
                                    "file": str(py_file),
                                    "line": i,
                                    "type": secret_type,
                                    "content": line.strip()[:100] + "..." if len(line) > 100 else line.strip()
                                })
            except Exception:
                continue

        self.security_report["code_secrets_scan"] = {
            "status": "completed",
            "findings_count": len(findings),
            "findings": findings
        }

    def identify_security_hotspots(self) -> None:
        """Identify potential security hotspots in code"""
        hotspot_patterns = [
            ("exec(", "code_execution"),
            ("eval(", "code_evaluation"),
            ("subprocess.", "subprocess_usage"),
            ("os.system(", "system_command"),
            ("pickle.load", "pickle_usage"),
            ("yaml.load(", "yaml_load"),
            ("shell=True", "shell_injection_risk"),
        ]

        hotspots = []
        for py_file in Path('.').rglob('*.py'):
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    for i, line in enumerate(content.split('\n'), 1):
                        for pattern, risk_type in hotspot_patterns:
                            if pattern in line and not line.strip().startswith('#'):
                                hotspots.append({
                                    "file": str(py_file),
                                    "line": i,
                                    "risk_type": risk_type,
                                    "pattern": pattern,
                                    "context": line.strip()
                                })
            except Exception:
                continue

        self.security_report["security_hotspots"] = hotspots

    def generate_recommendations(self) -> None:
        """Generate security recommendations based on findings"""
        recommendations = []

        # Dependency recommendations
        if self.security_report["dependency_check"].get("status") == "vulnerabilities_found":
            recommendations.append({
                "category": "dependencies",
                "priority": "high",
                "recommendation": "Update vulnerable dependencies identified in dependency check"
            })

        # Secrets recommendations
        if self.security_report["code_secrets_scan"].get("findings_count", 0) > 0:
            recommendations.append({
                "category": "secrets",
                "priority": "critical",
                "recommendation": "Remove hardcoded secrets and use environment variables or secret management"
            })

        # Hotspot recommendations
        if len(self.security_report["security_hotspots"]) > 0:
            recommendations.append({
                "category": "hotspots",
                "priority": "medium",
                "recommendation": "Review security hotspots for proper input validation and sanitization"
            })

        self.security_report["recommendations"] = recommendations

    def save_report(self, timestamp: str) -> None:
        """Save security analysis report"""
        report_path = self.audit_dir / f"security_analysis_{timestamp}.yaml"
        with open(report_path, 'w') as f:
            yaml.dump(self.security_report, f, default_flow_style=False)

        # Generate markdown summary
        md_path = self.audit_dir / f"security_summary_{timestamp}.md"
        with open(md_path, 'w') as f:
            f.write("# Security Analysis Summary\n\n")

            # Dependency check
            dep_status = self.security_report["dependency_check"].get("status", "unknown")
            f.write(f"## Dependency Vulnerabilities: {dep_status.upper()}\n")
            if dep_status == "vulnerabilities_found":
                count = self.security_report["dependency_check"].get("count", 0)
                f.write(f"- **Vulnerabilities Found**: {count}\n")
            f.write("\n")

            # Secrets scan
            secrets_count = self.security_report["code_secrets_scan"].get("findings_count", 0)
            f.write(f"## Code Secrets Scan: {secrets_count} findings\n")
            if secrets_count > 0:
                f.write("⚠️ **Action Required**: Remove hardcoded secrets\n")
            f.write("\n")

            # Security hotspots
            hotspots_count = len(self.security_report["security_hotspots"])
            f.write(f"## Security Hotspots: {hotspots_count} identified\n")
            if hotspots_count > 0:
                f.write("Review the following patterns for security implications:\n")
                for hotspot in self.security_report["security_hotspots"]:
                    f.write(f"- {hotspot['file']}:{hotspot['line']} - {hotspot['risk_type']}\n")
            f.write("\n")

            # Recommendations
            if self.security_report["recommendations"]:
                f.write("## Recommendations\n")
                for rec in self.security_report["recommendations"]:
                    f.write(f"- **{rec['priority'].upper()}**: {rec['recommendation']}\n")

# Execute security analysis
security_analyzer = SecurityAnalyzer(audit_dir)
security_analyzer.run_dependency_check()
security_analyzer.scan_for_secrets()
security_analyzer.identify_security_hotspots()
security_analyzer.generate_recommendations()
security_analyzer.save_report(timestamp)
```

**Expected Outcome**: Comprehensive security analysis with vulnerability identification and recommendations
**Validation**: Security scan completed, vulnerabilities identified, recommendations provided

### Step 8: Performance and Scalability Review (Estimated Time: 20m)
**Action**:
Assess performance implications and scalability impact of code changes:

```bash
# Performance analysis
analyze_performance_impact() {
  echo "=== Performance Analysis ===" > "${audit_dir}/performance_analysis_${timestamp}.md"

  # Profile code execution if performance tests exist
  if [ -d "tests/performance" ] || [ -f "performance_test.py" ]; then
    echo "## Performance Test Results" >> "${audit_dir}/performance_analysis_${timestamp}.md"

    # Run performance tests
    python -m pytest tests/performance/ -v --benchmark-only --benchmark-json="${audit_dir}/benchmark_${timestamp}.json" \
      >> "${audit_dir}/performance_analysis_${timestamp}.md" 2>&1 || echo "Performance tests not available"
  fi

  # Analyze complexity changes
  echo "## Complexity Analysis" >> "${audit_dir}/performance_analysis_${timestamp}.md"

  # Check for O(n²) patterns
  echo "### Algorithmic Complexity Warnings" >> "${audit_dir}/performance_analysis_${timestamp}.md"
  if git diff origin/main...HEAD | grep -E "for.*for|while.*while" >/dev/null; then
    echo "⚠️ Nested loops detected - review for O(n²) complexity" >> "${audit_dir}/performance_analysis_${timestamp}.md"
  fi

  # Check for database query patterns
  if git diff origin/main...HEAD | grep -E "\.filter\(|\.all\(\)|\.get\(" >/dev/null; then
    echo "⚠️ Database queries detected - ensure proper indexing and query optimization" >> "${audit_dir}/performance_analysis_${timestamp}.md"
  fi

  # Memory usage analysis
  echo "### Memory Usage Patterns" >> "${audit_dir}/performance_analysis_${timestamp}.md"
  if git diff origin/main...HEAD | grep -E "list\(|dict\(|\[\]|\{\}" >/dev/null; then
    echo "ℹ️ Data structure creation detected - consider memory efficiency" >> "${audit_dir}/performance_analysis_${timestamp}.md"
  fi

  # Scalability considerations
  echo "## Scalability Impact" >> "${audit_dir}/performance_analysis_${timestamp}.md"

  # Check for concurrency patterns
  if git diff origin/main...HEAD | grep -E "threading|multiprocessing|asyncio|async def" >/dev/null; then
    echo "🔄 Concurrency patterns detected - review for thread safety and async best practices" >> "${audit_dir}/performance_analysis_${timestamp}.md"
  fi

  # Check for caching opportunities
  if git diff origin/main...HEAD | grep -E "cache|memoize|lru_cache" >/dev/null; then
    echo "💾 Caching implementation detected - verify cache invalidation strategy" >> "${audit_dir}/performance_analysis_${timestamp}.md"
  fi
}

# Execute performance analysis
analyze_performance_impact
```

**Expected Outcome**: Performance impact assessment with scalability considerations
**Validation**: Performance patterns analyzed, scalability implications identified, recommendations provided

### Step 9: Final Review Consolidation (Estimated Time: 15m)
**Action**:
Consolidate all review findings into a comprehensive final report:

```bash
# Consolidate review findings
consolidate_review_findings() {
  echo "=== Comprehensive Code Review Report ===" > "${audit_dir}/final_review_report_${timestamp}.md"
  echo "**Issue**: #${issue_number}" >> "${audit_dir}/final_review_report_${timestamp}.md"
  echo "**Review Date**: $(date)" >> "${audit_dir}/final_review_report_${timestamp}.md"
  echo "**Reviewer**: Code-Reviewer" >> "${audit_dir}/final_review_report_${timestamp}.md"
  echo "" >> "${audit_dir}/final_review_report_${timestamp}.md"

  # Executive summary
  echo "## Executive Summary" >> "${audit_dir}/final_review_report_${timestamp}.md"

  # Count issues by category
  critical_issues=$(grep -c "critical" "${audit_dir}/failure_tracker.md" 2>/dev/null || echo "0")
  security_issues=$(grep -c "security" "${audit_dir}"/security_*.md 2>/dev/null || echo "0")
  performance_warnings=$(grep -c "⚠️" "${audit_dir}/performance_analysis_${timestamp}.md" 2>/dev/null || echo "0")

  echo "- **Critical Issues**: ${critical_issues}" >> "${audit_dir}/final_review_report_${timestamp}.md"
  echo "- **Security Concerns**: ${security_issues}" >> "${audit_dir}/final_review_report_${timestamp}.md"
  echo "- **Performance Warnings**: ${performance_warnings}" >> "${audit_dir}/final_review_report_${timestamp}.md"

  # Review decision logic
  total_blocking_issues=$((critical_issues + security_issues))

  if [ "$total_blocking_issues" -eq 0 ]; then
    if [ "$performance_warnings" -eq 0 ]; then
      review_decision="✅ **APPROVED** - Ready to merge"
    else
      review_decision="⚠️ **APPROVED WITH CONDITIONS** - Address performance considerations"
    fi
  elif [ "$total_blocking_issues" -le 2 ]; then
    review_decision="🔄 **REQUEST CHANGES** - Fix critical issues before merge"
  else
    review_decision="❌ **REJECTED** - Significant issues require redesign"
  fi

  echo "" >> "${audit_dir}/final_review_report_${timestamp}.md"
  echo "## Review Decision" >> "${audit_dir}/final_review_report_${timestamp}.md"
  echo "$review_decision" >> "${audit_dir}/final_review_report_${timestamp}.md"

  # Include links to detailed reports
  echo "" >> "${audit_dir}/final_review_report_${timestamp}.md"
  echo "## Detailed Reports" >> "${audit_dir}/final_review_report_${timestamp}.md"
  echo "- [Automated Analysis](./issue_${issue_number}_precommit_${timestamp}.md)" >> "${audit_dir}/final_review_report_${timestamp}.md"
  echo "- [Failure Tracker](./failure_tracker.md)" >> "${audit_dir}/final_review_report_${timestamp}.md"
  echo "- [Security Analysis](./security_analysis_${timestamp}.yaml)" >> "${audit_dir}/final_review_report_${timestamp}.md"
  echo "- [Performance Analysis](./performance_analysis_${timestamp}.md)" >> "${audit_dir}/final_review_report_${timestamp}.md"

  if [ -f "${audit_dir}/issue_${issue_number}_pullrequest_${timestamp}.md" ]; then
    echo "- [Pull Request Analysis](./issue_${issue_number}_pullrequest_${timestamp}.md)" >> "${audit_dir}/final_review_report_${timestamp}.md"
  fi
}

# Execute consolidation
consolidate_review_findings
```

**Expected Outcome**: Comprehensive final review report with clear decision and recommendations
**Validation**: All findings consolidated, decision logic applied, detailed reports linked

### Step 10: Review Documentation and Approval Workflow (Estimated Time: 10m)
**Action**:
Document review process and initiate approval workflow:

```yaml
review_metadata_${issue_number}.yaml:
  review_id: "CR_${issue_number}_${timestamp}"
  issue_number: "${issue_number}"
  review_date: "$(date -Iseconds)"
  reviewer: "Code-Reviewer"

  review_scope:
    automated_tools: ["black", "isort", "flake8", "mypy", "pylint", "bandit"]
    human_review_areas: ["architecture", "logic", "security", "performance", "maintainability"]
    enhanced_checks: true

  findings_summary:
    total_files_reviewed: $(git diff --name-only origin/main...HEAD | wc -l)
    lines_changed: $(git diff --stat origin/main...HEAD | tail -1)
    critical_issues: ${critical_issues}
    security_issues: ${security_issues}
    performance_warnings: ${performance_warnings}

  review_decision:
    status: "approved|approved_with_conditions|request_changes|rejected"
    blocking_issues: []
    required_actions: []
    recommendations: []

  approval_workflow:
    technical_lead_required: true
    security_review_required: ${security_issues > 0}
    performance_review_required: ${performance_warnings > 3}
    qa_validation_required: true

  next_steps:
    - "Address identified critical issues"
    - "Update documentation as needed"
    - "Ensure test coverage ≥80%"
    - "Obtain required approvals"
```

Generate approval tracking:
```bash
# Create approval tracking file
echo "# Approval Tracking - Issue #${issue_number}" > "${audit_dir}/approval_tracking.md"
echo "" >> "${audit_dir}/approval_tracking.md"
echo "## Required Approvals" >> "${audit_dir}/approval_tracking.md"
echo "- [ ] Code Review (Code-Reviewer)" >> "${audit_dir}/approval_tracking.md"
echo "- [ ] Technical Lead Approval" >> "${audit_dir}/approval_tracking.md"

if [ "$security_issues" -gt 0 ]; then
  echo "- [ ] Security Review (Security-Engineer)" >> "${audit_dir}/approval_tracking.md"
fi

if [ "$performance_warnings" -gt 3 ]; then
  echo "- [ ] Performance Review (Performance-Engineer)" >> "${audit_dir}/approval_tracking.md"
fi

echo "- [ ] QA Validation (QA-Engineer)" >> "${audit_dir}/approval_tracking.md"
echo "" >> "${audit_dir}/approval_tracking.md"
echo "## Review History" >> "${audit_dir}/approval_tracking.md"
echo "- $(date): Initial code review completed by Code-Reviewer" >> "${audit_dir}/approval_tracking.md"
```

**Expected Outcome**: Complete review documentation with approval workflow initiated
**Validation**: Review metadata captured, approval tracking established, workflow documented

## Expected Outputs

- **Primary Artifact**: Comprehensive Code Review Report `final_review_report_${issue_number}_${timestamp}.md`
- **Secondary Artifacts**:
  - Automated analysis results (`issue_${issue_number}_precommit_${timestamp}.md`)
  - Failure tracker with categorized issues (`failure_tracker.md`)
  - Enhanced pull request analysis (`issue_${issue_number}_pullrequest_${timestamp}.md`)
  - Tool configuration optimization (`tool_optimization_${timestamp}.md`)
  - Security analysis report (`security_analysis_${timestamp}.yaml`)
  - Performance impact assessment (`performance_analysis_${timestamp}.md`)
  - Test coverage analysis (`test_coverage_${timestamp}.md`)
  - Review metadata and approval tracking
- **Success Indicators**:
  - Zero critical issues remaining
  - Security vulnerabilities addressed or accepted
  - Test coverage ≥80%
  - Performance impact assessed and acceptable
  - All required approvals obtained
  - Clear documentation of review decisions and rationale

## Failure Handling

### Failure Scenario 1: Critical Issues Blocking Merge
- **Symptoms**: Multiple critical issues identified by automated tools or human review
- **Root Cause**: Code quality below acceptable standards, security vulnerabilities, logic errors
- **Impact**: High - Cannot merge until issues resolved
- **Resolution**:
  1. Categorize critical issues by type and severity
  2. Provide specific guidance for each issue resolution
  3. Block pull request merge until all critical issues addressed
  4. Re-run full review process after fixes implemented
  5. Escalate to Technical Lead if pattern of quality issues persists
- **Prevention**: Earlier code quality checks, developer training, better development practices

### Failure Scenario 2: Tool Configuration Conflicts
- **Symptoms**: Different tools providing conflicting guidance (e.g., black vs flake8 formatting)
- **Root Cause**: Inconsistent tool configuration, outdated settings
- **Impact**: Medium - Developer confusion, wasted time resolving conflicts
- **Resolution**:
  1. Identify specific tool conflicts from analysis
  2. Update tool configurations for consistency
  3. Document unified configuration approach
  4. Test configuration changes with sample code
  5. Update developer documentation and training materials
- **Prevention**: Regular tool configuration review, unified configuration management

### Failure Scenario 3: Security Vulnerabilities Detected
- **Symptoms**: Bandit, dependency check, or manual review identifies security issues
- **Root Cause**: Insecure coding practices, outdated dependencies, inadequate input validation
- **Impact**: Critical - Security exposure, potential compliance violations
- **Resolution**:
  1. Immediate escalation to Security-Engineer for assessment
  2. Block merge until security issues resolved or accepted risk documented
  3. Implement security fixes or compensating controls
  4. Update security guidelines and training
  5. Consider security-focused code review for team
- **Prevention**: Security training, secure coding standards, regular dependency updates

### Failure Scenario 4: Inadequate Test Coverage
- **Symptoms**: Test coverage below 80% threshold, critical code paths untested
- **Root Cause**: Insufficient test development, complex code difficult to test
- **Impact**: Medium - Risk of bugs in production, maintenance difficulties
- **Resolution**:
  1. Identify specific areas lacking test coverage
  2. Require additional tests before merge approval
  3. Provide guidance on testing strategies for complex code
  4. Consider refactoring to improve testability
  5. Update testing guidelines and requirements
- **Prevention**: Test-driven development practices, coverage monitoring, testing training

### Failure Scenario 5: Performance Degradation Risk
- **Symptoms**: Code changes introduce performance anti-patterns, scalability concerns
- **Root Cause**: Inefficient algorithms, poor data structure choices, lack of performance consideration
- **Impact**: Medium - Potential production performance issues, user experience degradation
- **Resolution**:
  1. Escalate to Performance-Engineer for detailed analysis
  2. Implement performance benchmarks if not available
  3. Optimize identified performance bottlenecks
  4. Document performance considerations and trade-offs
  5. Establish performance testing requirements
- **Prevention**: Performance-aware development practices, regular performance testing, optimization training

## Rollback/Recovery

**Trigger**: Critical issues discovered during Steps 7-9 (security, performance, consolidation) requiring code changes

**Standard Approach**: Invoke **P-RECOVERY** protocol for transactional rollback

**P-RECOVERY Integration**:
1. Before Step 7: CreateBranch to create isolated workspace (`code_review_fixes_${issue_number}_${timestamp}`)
2. Execute Steps 7-10 with checkpoints after security analysis, performance review, and final consolidation
3. On success: MergeBranch commits review results and any configuration fixes atomically
4. On failure: DiscardBranch rolls back review process, maintains original code state
5. P-RECOVERY handles retry logic with escalation to Technical Lead
6. P-RECOVERY escalates to NotifyHuman if persistent quality issues indicate systemic problems

**Custom Rollback** (code-review-specific):
1. If critical security issues found: Immediate branch protection, escalation to Security team
2. If review process errors: Reset to clean state, re-run automated analysis
3. Preserve all review artifacts for audit trail and learning
4. Document review process issues for improvement

**Verification**: Code review completed with clear decision or review process safely reset
**Data Integrity**: Medium risk - review decisions affect code quality and security

## Validation Criteria

### Quantitative Thresholds
- Critical issues: 0 remaining before merge approval
- Security vulnerabilities: 0 high/critical unresolved
- Test coverage: ≥80% for new/modified code
- Code quality score (pylint): ≥7.0/10
- Performance regression: <10% in benchmarks
- Review completion time: ≤2 hours for standard changes, ≤4 hours for complex changes

### Boolean Checks
- All automated tools executed successfully: Pass/Fail
- Human review completed: Pass/Fail
- Security assessment performed: Pass/Fail
- Test coverage validated: Pass/Fail
- Performance impact assessed: Pass/Fail
- Required approvals obtained: Pass/Fail

### Qualitative Assessments
- Code maintainability: Excellent/Good/Needs Improvement
- Architecture alignment: Strong/Adequate/Poor
- Documentation quality: Comprehensive/Adequate/Insufficient

**Overall Success**: All quantitative thresholds met AND all boolean checks pass AND qualitative assessments adequate

## HITL Escalation

### Automatic Triggers
- Critical issues count >3
- Security vulnerabilities with CVSS >7.0
- Test coverage <60%
- Code quality score <5.0/10
- Review time exceeding 4 hours
- Tool execution failures preventing analysis

### Manual Triggers
- Novel architectural patterns requiring senior review
- Cross-team impact requiring coordination
- Performance implications requiring specialist analysis
- Security implications for sensitive components
- Disagreement between reviewers requiring resolution

### Escalation Procedure
1. **Level 1 - Technical Lead**: Complex technical decisions, architecture alignment, quality standards
2. **Level 2 - Senior Engineering**: Cross-team coordination, architectural decisions, technical conflicts
3. **Level 3 - Security/Performance Specialists**: Domain-specific expertise for critical issues
4. **Level 4 - Engineering Management**: Resource allocation, process improvements, systemic quality issues

## Related Protocols

### Upstream (Prerequisites)
- P-FEATURE-DEV: Feature development producing code requiring review
- P-BUG-FIX: Bug fixes requiring verification before deployment
- P-TDD: Test-driven development ensuring adequate test coverage

### Downstream (Consumers)
- P-QGATE-Automated-Quality-Gate: Quality gates consuming review results
- Deployment-Pipeline: CI/CD pipeline requiring review approval
- Documentation-Update: Documentation updates based on review findings

### Alternatives
- Automated-Only-Review: For low-risk changes requiring only automated validation
- Pair-Programming: For complex changes benefiting from real-time collaboration
- Asynchronous-Review: For distributed teams requiring flexible review timing

## Test Scenarios

### Happy Path Scenarios

#### Scenario 1: Standard Feature Review
- **Setup**: New feature implementation with comprehensive tests and documentation
- **Execution**: Run CODE-REVIEW-001 with standard review scope
- **Expected Result**: Clean automated analysis, positive human review, approval for merge
- **Validation**: Zero critical issues, >80% test coverage, all approvals obtained

#### Scenario 2: Bug Fix Validation
- **Setup**: Bug fix with regression test and minimal scope changes
- **Execution**: CODE-REVIEW-001 with focus on fix verification and testing
- **Expected Result**: Fix validated, regression prevented, efficient review process
- **Validation**: Bug fix verified, tests pass, no new issues introduced

### Failure Scenarios

#### Scenario 3: Security Vulnerability Detection
- **Setup**: Code change inadvertently introduces SQL injection vulnerability
- **Execution**: CODE-REVIEW-001 security analysis detects vulnerability
- **Expected Result**: Security issue flagged, merge blocked, Security-Engineer escalation
- **Validation**: Vulnerability identified, appropriate escalation, fix required before merge

#### Scenario 4: Performance Regression
- **Setup**: Algorithm change introduces O(n²) complexity in critical path
- **Execution**: CODE-REVIEW-001 performance analysis identifies complexity issue
- **Expected Result**: Performance concern raised, optimization required
- **Validation**: Performance issue identified, recommendations provided, follow-up required

### Edge Cases

#### Scenario 5: Tool Configuration Conflicts
- **Setup**: Multiple formatting tools provide conflicting guidance
- **Execution**: CODE-REVIEW-001 detects and resolves configuration conflicts
- **Expected Result**: Unified configuration implemented, conflicts resolved
- **Validation**: Tool configurations aligned, developer experience improved

## Metadata

### Version History
| Version | Date | Changes | Author |
|---------|------|---------|--------|
| 1.0 | 2025-10-08 | Initial comprehensive protocol creation, expanded from 10-line stub to full 14-section code review protocol | Claude Code (Sonnet 4) |

### Review Cycle
- **Frequency**: Quarterly (aligned with development process improvements and tool updates)
- **Next Review**: 2026-01-08
- **Reviewers**: Technical Lead, Code-Reviewer supervisor, Development Team Lead

### Compliance Status
- **Framework Standards**: ✅ Compliant with 14-section template
- **Development Standards**: ✅ Aligned with software engineering best practices and code quality standards
- **Security Audit**: Required (handles security vulnerability detection and assessment)
- **Last Validation**: 2025-10-08