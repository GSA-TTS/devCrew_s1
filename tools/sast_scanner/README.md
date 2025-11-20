# SAST Scanner - Issue #39 Implementation

**TOOL-SEC-001: Static Application Security Testing Scanner**

A comprehensive Static Application Security Testing (SAST) tool that integrates Semgrep and Bandit to provide multi-language security vulnerability detection with SARIF export capabilities.

## Overview

This implementation provides:
- **Multi-language support**: Python, JavaScript, TypeScript, Go, Java, C/C++, and more
- **OWASP Top 10 detection**: Comprehensive coverage of OWASP security vulnerabilities
- **CWE Top 25 coverage**: Detection of Common Weakness Enumeration patterns
- **Custom rules support**: Define custom Semgrep YAML rules
- **False positive management**: Baseline tracking and comparison
- **SARIF export**: Standardized reporting format for CI/CD integration
- **HTML reports**: Human-readable security reports

## Files Created

All files are prefixed with `issue_39_` to avoid conflicts:

1. **issue_39_sast_scanner.py** - Main CLI and orchestration
2. **issue_39_semgrep_wrapper.py** - Semgrep scanner integration
3. **issue_39_bandit_wrapper.py** - Bandit scanner integration (Python-specific)
4. **issue_39_report_generator.py** - SARIF and HTML report generation
5. **issue_39_test_sast_scanner.py** - Comprehensive test suite
6. **issue_39_requirements.txt** - Python dependencies
7. **issue_39_custom_rules/** - Example custom Semgrep rules
   - `sql-injection.yml` - SQL injection detection rules
   - `hardcoded-secrets.yml` - Hardcoded credential detection
   - `xss-vulnerabilities.yml` - Cross-site scripting detection
   - `insecure-crypto.yml` - Weak cryptography detection
8. **issue_39_README.md** - This documentation

## Installation

### Prerequisites

1. **Python 3.10+**
2. **Semgrep** (v1.45.0 or higher)
3. **Bandit** (v1.7.5 or higher)

### Install Python Dependencies

```bash
cd /Users/tamnguyen/Documents/GitHub/devCrew_s1

# Install Python dependencies
pip install -r issue_39_requirements.txt
```

### Install Semgrep

```bash
# Using pip
pip install semgrep

# Or using Homebrew (macOS)
brew install semgrep

# Verify installation
semgrep --version
```

### Install Bandit

```bash
# Using pip
pip install bandit

# Or use existing bandit from devgru_setup
# Bandit is already available in the devgru_setup environment

# Verify installation
bandit --version
```

## Usage

### Basic Scan

Scan a directory with default settings (OWASP Top 10):

```bash
python issue_39_sast_scanner.py scan --path src/
```

### Python-Specific Scan

Use both Semgrep and Bandit for Python code:

```bash
python issue_39_sast_scanner.py scan-python --path src/ --severity HIGH
```

### Custom Rules

Scan with custom Semgrep rules:

```bash
python issue_39_sast_scanner.py scan \
    --path src/ \
    --custom-rules issue_39_custom_rules/ \
    --config p/security-audit
```

### Generate SARIF Report

Export results in SARIF format for GitHub Code Scanning:

```bash
python issue_39_sast_scanner.py scan \
    --path src/ \
    --output results.sarif \
    --format sarif
```

### Generate HTML Report

Create human-readable HTML report:

```bash
python issue_39_sast_scanner.py scan \
    --path src/ \
    --output report.html \
    --format html
```

### Baseline Management

Generate a baseline to track known issues:

```bash
# Generate baseline
python issue_39_sast_scanner.py generate-baseline \
    --path src/ \
    --output baseline.json

# Compare current scan against baseline
python issue_39_sast_scanner.py compare-baseline \
    --path src/ \
    --baseline baseline.json \
    --fail-on-new
```

### Advanced Options

```bash
python issue_39_sast_scanner.py scan \
    --path src/ \
    --severity MEDIUM \
    --exclude "*/tests/*" \
    --exclude "*/migrations/*" \
    --config p/owasp-top-ten \
    --format sarif \
    --output security-report.sarif
```

## CLI Reference

### Commands

#### `scan`
Execute comprehensive SAST scan.

**Options:**
- `--path, -p`: Path to scan (required)
- `--output, -o`: Output file path (default: `sast_report.sarif`)
- `--severity, -s`: Minimum severity threshold [INFO, LOW, MEDIUM, HIGH, CRITICAL]
- `--format, -f`: Output format [sarif, json, html]
- `--exclude, -e`: Patterns to exclude (can be specified multiple times)
- `--config, -c`: Semgrep configuration (default: `p/owasp-top-ten`)
- `--custom-rules`: Path to custom Semgrep rules directory
- `--no-semgrep`: Disable Semgrep scanner
- `--no-bandit`: Disable Bandit scanner

#### `scan-python`
Python-specific scan with Semgrep + Bandit.

**Options:**
- `--path, -p`: Path to scan (required)
- `--output, -o`: Output file path (default: `sast_report.sarif`)
- `--severity, -s`: Minimum severity threshold [LOW, MEDIUM, HIGH]

#### `generate-baseline`
Generate baseline from current scan results.

**Options:**
- `--path, -p`: Path to scan (required)
- `--output, -o`: Output baseline file (default: `baseline.json`)

#### `compare-baseline`
Compare current scan against baseline.

**Options:**
- `--path, -p`: Path to scan (required)
- `--baseline, -b`: Baseline file path (required)
- `--fail-on-new`: Exit with error if new findings detected

## Python API Usage

### Basic Scanning

```python
from pathlib import Path
from issue_39_sast_scanner import SASTScanner

# Initialize scanner
scanner = SASTScanner()

# Run comprehensive scan
results = scanner.scan(
    path=Path("src/"),
    severity_threshold="HIGH",
    use_semgrep=True,
    use_bandit=True
)

# Access findings
print(f"Total findings: {results['summary']['total_findings']}")
for finding in results['findings']:
    print(f"{finding['severity']}: {finding['message']}")
```

### Semgrep Only

```python
from issue_39_semgrep_wrapper import SemgrepScanner
from pathlib import Path

# Initialize Semgrep scanner
semgrep = SemgrepScanner(
    config="p/owasp-top-ten",
    custom_rules=Path("issue_39_custom_rules/")
)

# Scan with Semgrep
results = semgrep.scan(
    path=Path("src/"),
    severity_threshold="HIGH",
    exclude_patterns=["*/tests/*"]
)

print(f"Found {len(results['findings'])} issues")
```

### Bandit Only

```python
from issue_39_bandit_wrapper import BanditScanner
from pathlib import Path

# Initialize Bandit scanner
bandit = BanditScanner(
    confidence_level="HIGH",
    severity_level="MEDIUM"
)

# Scan with Bandit
results = bandit.scan(
    path=Path("src/"),
    exclude_patterns=["tests", "migrations"]
)

print(f"Found {len(results['findings'])} issues")
```

### Export Reports

```python
from issue_39_report_generator import SARIFReportGenerator, HTMLReportGenerator
from pathlib import Path

# Generate SARIF report
sarif_gen = SARIFReportGenerator()
sarif_report = sarif_gen.generate(
    findings=results['findings'],
    scan_path=Path("src/")
)
sarif_gen.export_to_file(sarif_report, Path("report.sarif"))

# Generate HTML report
html_gen = HTMLReportGenerator()
html_report = html_gen.generate(
    findings=results['findings'],
    summary=results['summary']
)
html_gen.export_to_file(html_report, Path("report.html"))
```

## Custom Rules

### Creating Custom Semgrep Rules

Create YAML files in the `issue_39_custom_rules/` directory:

```yaml
rules:
  - id: my-custom-rule
    pattern: |
      dangerous_function($ARG)
    message: |
      Detected use of dangerous_function which is not secure.
      Use safe_function instead.
    languages: [python]
    severity: ERROR
    metadata:
      category: security
      cwe:
        - "CWE-676"
      owasp:
        - "A01:2021-Broken Access Control"
      confidence: HIGH
```

### Using Custom Rules

```bash
python issue_39_sast_scanner.py scan \
    --path src/ \
    --custom-rules issue_39_custom_rules/
```

## OWASP Top 10 Coverage

| OWASP Category | Detection | Example CWE |
|----------------|-----------|-------------|
| A01:2021 - Broken Access Control | ✅ | CWE-22, CWE-639 |
| A02:2021 - Cryptographic Failures | ✅ | CWE-327, CWE-328 |
| A03:2021 - Injection | ✅ | CWE-79, CWE-89 |
| A04:2021 - Insecure Design | ⚠️ Partial | CWE-209 |
| A05:2021 - Security Misconfiguration | ✅ | CWE-16 |
| A06:2021 - Vulnerable Components | ⚠️ Via SCA | CWE-1104 |
| A07:2021 - Auth Failures | ✅ | CWE-287, CWE-522 |
| A08:2021 - Software Integrity | ⚠️ Partial | CWE-494 |
| A09:2021 - Logging Failures | ✅ | CWE-778 |
| A10:2021 - SSRF | ✅ | CWE-918 |

## Testing

### Run All Tests

```bash
cd /Users/tamnguyen/Documents/GitHub/devCrew_s1

# Run tests with coverage
pytest issue_39_test_sast_scanner.py -v --cov=. --cov-report=term-missing

# Run specific test class
pytest issue_39_test_sast_scanner.py::TestSemgrepScanner -v

# Run with verbose output
pytest issue_39_test_sast_scanner.py -v -s
```

### Test Coverage

The test suite includes:
- Unit tests for all scanner components
- SARIF and HTML report generation tests
- Finding deduplication tests
- Baseline management tests
- Integration tests (require actual scanners)
- Performance tests

## CI/CD Integration

### GitHub Actions

```yaml
name: Security Scan

on: [push, pull_request]

jobs:
  sast:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'

      - name: Install dependencies
        run: |
          pip install -r issue_39_requirements.txt
          pip install semgrep bandit

      - name: Run SAST scan
        run: |
          python issue_39_sast_scanner.py scan \
            --path src/ \
            --output results.sarif \
            --format sarif \
            --severity HIGH

      - name: Upload SARIF
        uses: github/codeql-action/upload-sarif@v2
        with:
          sarif_file: results.sarif
```

### GitLab CI

```yaml
sast:
  stage: test
  image: python:3.10
  script:
    - pip install -r issue_39_requirements.txt
    - pip install semgrep bandit
    - python issue_39_sast_scanner.py scan --path src/ --output gl-sast-report.json --format json
  artifacts:
    reports:
      sast: gl-sast-report.json
```

## Performance

Based on requirements from Issue #39:

- **Small projects** (10K LOC): < 30 seconds
- **Medium projects** (50K LOC): < 2 minutes
- **Large projects** (100K LOC): < 5 minutes
- **False positive rate**: < 5% (with baseline tracking)
- **Detection rate**: 90%+ for OWASP Top 10

## Troubleshooting

### Semgrep Not Found

```bash
# Check if Semgrep is installed
which semgrep

# Install if missing
pip install semgrep

# Or use Homebrew
brew install semgrep
```

### Bandit Not Found

```bash
# Check if Bandit is installed
which bandit

# Install if missing
pip install bandit

# Or use from devgru_setup
export PATH="/path/to/devgru_setup:$PATH"
```

### Permission Denied Errors

```bash
# Make scanner executable
chmod +x issue_39_sast_scanner.py

# Run with python explicitly
python issue_39_sast_scanner.py scan --path src/
```

### Large Scan Timeouts

```python
# Increase timeout in Python API
from issue_39_semgrep_wrapper import SemgrepScanner

scanner = SemgrepScanner(timeout=600)  # 10 minutes
```

## Limitations

1. **Language Support**: Limited to languages supported by Semgrep and Bandit
2. **False Positives**: Some false positives are inherent to static analysis
3. **Context Awareness**: Cannot detect all runtime-dependent vulnerabilities
4. **Custom Rules**: Requires Semgrep YAML syntax knowledge
5. **Performance**: Large codebases may require longer scan times

## Future Enhancements

Potential improvements for production use:

1. **SonarQube Integration**: Add enterprise-grade analysis
2. **ML-based False Positive Reduction**: Use machine learning to reduce false positives
3. **Incremental Scanning**: Only scan changed files
4. **Multi-threading**: Parallel scanning for better performance
5. **Cloud Integration**: Support for cloud-based scanning services
6. **IDE Plugins**: Real-time scanning in development environments

## References

- [Semgrep Documentation](https://semgrep.dev/docs/)
- [Bandit Documentation](https://bandit.readthedocs.io/)
- [SARIF Specification](https://docs.oasis-open.org/sarif/sarif/v2.1.0/sarif-v2.1.0.html)
- [OWASP Top 10 2021](https://owasp.org/Top10/)
- [CWE Top 25](https://cwe.mitre.org/top25/)

## Support

For issues or questions:
1. Check the troubleshooting section above
2. Review test cases in `issue_39_test_sast_scanner.py`
3. Refer to Issue #39 in the devCrew_s1 repository
4. Consult Semgrep and Bandit documentation

## License

This implementation is part of the devCrew_s1 project and follows the same license terms.

---

**Implementation Date**: November 2024
**Issue Reference**: #39
**Tool ID**: TOOL-SEC-001
**Status**: Ready for Testing
