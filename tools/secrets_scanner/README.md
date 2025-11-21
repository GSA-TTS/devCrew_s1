# Secrets Scanner & Detection Platform

**TOOL-SEC-006** - devCrew_s1 Security Tools

A comprehensive secret detection platform with pattern matching, Shannon entropy analysis, Git history scanning, and remediation guidance.

## Features

- **50+ Built-in Patterns**: AWS, GitHub, Google/GCP, Slack, Stripe, private keys, database URIs, and more
- **Shannon Entropy Analysis**: Detect high-entropy strings that may be secrets
- **Git History Scanning**: Scan commits and branches for historical secret leaks
- **Baseline Management**: Track known secrets, mark false positives, version control
- **SARIF Output**: Compatible with GitHub Code Scanning and other security tools
- **Verification Engine**: Validate secret formats and check token status
- **Remediation Guide**: Priority scoring and rotation workflows

## Installation

```bash
# Navigate to the secrets scanner directory
cd devCrew_s1/tools/secrets_scanner

# Install optional dependencies for testing
pip install -r requirements.txt
```

## Quick Start

### Command Line Interface

```bash
# Scan current directory
python -m secrets_scanner.secrets_cli scan .

# Scan with JSON output
python -m secrets_scanner.secrets_cli scan . --format json --output results.json

# Scan with SARIF output (for GitHub Code Scanning)
python -m secrets_scanner.secrets_cli scan . --format sarif --output results.sarif

# Scan git history
python -m secrets_scanner.secrets_cli scan . --git-history --commits 100

# Create baseline
python -m secrets_scanner.secrets_cli baseline create --path .

# List available patterns
python -m secrets_scanner.secrets_cli patterns
```

### Python API

```python
from secrets_scanner import SecretScanner, PatternManager, BaselineManager

# Basic scan
scanner = SecretScanner()
result = scanner.scan_directory("/path/to/code")

print(f"Found {result.finding_count} secrets")
for finding in result.findings:
    print(f"[{finding.severity.value}] {finding.pattern_name}")
    print(f"  File: {finding.file_path}:{finding.line_number}")

# Scan with baseline filtering
baseline_mgr = BaselineManager(".secrets.baseline")
baseline_mgr.load()
new_findings = baseline_mgr.get_new_findings(result)

# Git history scanning
from secrets_scanner import GitScanner

git_scanner = GitScanner("/path/to/repo")
branch_scan = git_scanner.scan_branch("main", limit=100)
print(f"Found {branch_scan.total_findings} secrets in git history")
```

## Components

### SecretScanner

Core scanning engine with pattern matching and entropy analysis.

```python
from secrets_scanner import SecretScanner

scanner = SecretScanner(
    entropy_threshold=4.5,  # Shannon entropy threshold
    max_file_size=10*1024*1024,  # Skip files larger than 10MB
)

# Scan content string
findings = scanner.scan_content("AWS_KEY=AKIAIOSFODNN7EXAMPLE")

# Scan single file
findings = scanner.scan_file("config.py")

# Scan directory
result = scanner.scan_directory("/path/to/code", recursive=True)

# Calculate entropy
entropy = scanner.calculate_shannon_entropy("random_string_here")
```

### PatternManager

Manages 50+ built-in patterns and supports custom patterns.

```python
from secrets_scanner import PatternManager, SecretPattern, PatternSeverity

pm = PatternManager()

# List all patterns
patterns = pm.get_all_patterns()
print(f"Total patterns: {pm.pattern_count()}")

# Filter by category
aws_patterns = pm.get_patterns_by_category("aws")

# Add custom pattern
custom = SecretPattern(
    name="my_api_key",
    pattern=r"MYAPP_[A-Z0-9]{32}",
    severity=PatternSeverity.HIGH,
    description="My Application API Key",
    category="custom",
)
pm.add_custom_pattern(custom)
```

### BaselineManager

Tracks known secrets and manages false positives.

```python
from secrets_scanner import BaselineManager

manager = BaselineManager(".secrets.baseline")

# Create baseline from scan
manager.create_from_scan(scan_result)
manager.save()

# Load existing baseline
manager.load()

# Mark false positive
manager.add_false_positive(
    hash_value="abc123...",
    reason="Test credential, not used in production",
    added_by="developer@example.com"
)

# Filter out baselined findings
new_findings = manager.filter_baselined(scan_result.findings)

# Audit baseline
audit = manager.audit_baseline(scan_result)
print(f"New secrets: {audit['new_secrets_found']}")
```

### GitScanner

Scans git history for secrets.

```python
from secrets_scanner import GitScanner

git_scanner = GitScanner("/path/to/repo")

# Scan recent commits
commits = git_scanner.get_commits(limit=50)
for commit in commits:
    scan = git_scanner.scan_commit(commit.sha)
    if scan.findings:
        print(f"Secrets in {commit.sha}: {len(scan.findings)}")

# Scan entire branch
branch_scan = git_scanner.scan_branch("main", limit=100)

# Get authors with exposed secrets
authors = git_scanner.get_authors_with_secrets(branch_scan)
```

### VerificationEngine

Validates detected secrets.

```python
from secrets_scanner import VerificationEngine

engine = VerificationEngine(verify_live=False)

# Verify a finding
result = engine.verify(finding)
print(f"Status: {result.status.value}")
print(f"Details: {result.details}")

# Batch verify
results = engine.verify_all(findings)
report = engine.generate_report(results)
```

### RemediationGuide

Provides rotation workflows and priority scoring.

```python
from secrets_scanner import RemediationGuide

guide = RemediationGuide()

# Get priority score
score = guide.calculate_priority_score(finding)
priority = guide.get_priority(score)

# Get rotation workflow
workflow = guide.get_workflow("aws_access_key_id")
for step in workflow.steps:
    print(f"{step.order}. {step.action}")
    print(f"   {step.description}")

# Generate remediation report
report = guide.generate_report(finding)
print(f"Priority: {report.priority.name}")
print(f"Actions: {report.recommended_actions}")
```

## Supported Secret Types

### Cloud Providers
- AWS Access Keys, Secret Keys, Session Tokens
- Google API Keys, OAuth Secrets, Service Accounts
- Azure Client Secrets
- DigitalOcean Tokens

### Version Control
- GitHub Tokens (PAT, OAuth, App, Fine-grained)
- GitHub OAuth Secrets

### Communication
- Slack Tokens (Bot, User, App)
- Slack Webhooks
- Twilio API Keys
- SendGrid API Keys
- Mailchimp API Keys

### Payment
- Stripe Keys (Live, Test, Publishable)
- PayPal Client Secrets
- Square Access Tokens

### Private Keys
- RSA, DSA, EC, PGP Private Keys
- OpenSSH Keys
- PKCS8 Keys
- Certificates

### Databases
- PostgreSQL, MySQL, MongoDB URIs
- Redis URIs
- JDBC Connection Strings

### Generic
- API Keys, Secrets, Passwords
- Bearer Tokens, Basic Auth
- JWT Tokens
- High-entropy strings

## Output Formats

### JSON
```bash
python -m secrets_scanner.secrets_cli scan . --format json
```

### SARIF (GitHub Code Scanning)
```bash
python -m secrets_scanner.secrets_cli scan . --format sarif
```

### Text (Default)
```bash
python -m secrets_scanner.secrets_cli scan .
```

## Baseline File Format

The `.secrets.baseline` file uses JSON format:

```json
{
  "version": "1.0.0",
  "generated_at": "2024-01-15T10:30:00Z",
  "plugins_used": [],
  "filters_used": [],
  "results": {
    "path/to/file.py": [
      {
        "hash": "abc123...",
        "pattern_name": "aws_access_key_id",
        "file_path": "path/to/file.py",
        "line_number": 42,
        "is_false_positive": false,
        "reason": "",
        "added_date": "2024-01-15T10:30:00Z",
        "added_by": ""
      }
    ]
  }
}
```

## CI/CD Integration

### GitHub Actions

```yaml
name: Secret Scan

on: [push, pull_request]

jobs:
  secret-scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
        with:
          fetch-depth: 0

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Run secret scan
        run: |
          python -m secrets_scanner.secrets_cli scan . \
            --format sarif \
            --output results.sarif \
            --baseline .secrets.baseline

      - name: Upload SARIF
        uses: github/codeql-action/upload-sarif@v2
        with:
          sarif_file: results.sarif
```

### Pre-commit Hook

```yaml
# .pre-commit-config.yaml
repos:
  - repo: local
    hooks:
      - id: secrets-scan
        name: Secrets Scanner
        entry: python -m secrets_scanner.secrets_cli scan
        language: python
        types: [python]
        pass_filenames: false
```

## Running Tests

```bash
# Run all tests
python -m pytest tools/secrets_scanner/test_secrets.py -v

# Run with coverage
python -m pytest tools/secrets_scanner/test_secrets.py -v --cov=tools/secrets_scanner --cov-report=term-missing
```

## License

Part of the devCrew_s1 project.
