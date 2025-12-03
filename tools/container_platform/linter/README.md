# Dockerfile Linter

Comprehensive Dockerfile validation with hadolint integration and custom organizational rules.

## Features

### Core Capabilities

1. **hadolint Integration**
   - Industry-standard Dockerfile best practices
   - JSON output parsing
   - Automatic binary detection
   - Graceful degradation when not installed

2. **Security Checks**
   - Root user detection (CUSTOM-SEC-001, CUSTOM-SEC-002)
   - Hardcoded secrets detection (CUSTOM-SEC-003)
   - Vulnerable base image detection (CUSTOM-SEC-004)
   - Pattern matching for common security anti-patterns

3. **Build Optimization**
   - Layer optimization recommendations (CUSTOM-OPT-001)
   - apt-get best practices (CUSTOM-OPT-002)
   - Build cache optimization (CUSTOM-OPT-003)
   - Multi-stage build suggestions (CUSTOM-OPT-004)

4. **Compliance Validation**
   - OCI annotation compliance (CUSTOM-COMP-001)
   - Required label checking
   - Industry standard adherence

5. **Best Practices**
   - HEALTHCHECK instruction validation (CUSTOM-BEST-001)
   - WORKDIR usage recommendations (CUSTOM-BEST-002)
   - Metadata completeness

## Installation

### Prerequisites

```bash
# Optional: Install hadolint for industry-standard checks
# macOS
brew install hadolint

# Linux
wget -O /usr/local/bin/hadolint \
  https://github.com/hadolint/hadolint/releases/latest/download/hadolint-Linux-x86_64
chmod +x /usr/local/bin/hadolint

# Docker
docker pull hadolint/hadolint
```

### Python Dependencies

```bash
pip install -r requirements.txt
```

## Usage

### Basic Usage

```python
from tools.container_platform.linter import DockerfileLinter

# Initialize linter
linter = DockerfileLinter()

# Check if hadolint is available
installed, version = linter.check_hadolint_installed()
if not installed:
    print(linter.get_installation_instructions())

# Lint a Dockerfile
result = linter.lint_file('path/to/Dockerfile')

# Generate text report
print(linter.generate_report(result, format='text'))

# Access findings
print(f"Errors: {result.error_count}")
print(f"Warnings: {result.warning_count}")
for finding in result.findings:
    print(f"{finding.rule_id}: {finding.description}")
```

### Advanced Configuration

```python
from tools.container_platform.linter import (
    DockerfileLinter,
    LintRule,
    LintSeverity,
    RuleCategory
)

# Custom rules
custom_rules = [
    LintRule(
        rule_id="ORG-001",
        description="Must use company base image",
        severity=LintSeverity.ERROR,
        category=RuleCategory.COMPLIANCE,
        fix_suggestion="Use company-approved base images",
        documentation_url="https://docs.company.com/docker"
    )
]

# Initialize with custom configuration
linter = DockerfileLinter(
    hadolint_path="/usr/local/bin/hadolint",
    custom_rules=custom_rules,
    strict_mode=True  # All warnings become errors
)

result = linter.lint_file('Dockerfile')
```

### Output Formats

#### Text Report

```python
report = linter.generate_report(result, format='text')
print(report)
```

#### JSON Report

```python
import json

report = linter.generate_report(result, format='json')
data = json.loads(report)
print(json.dumps(data, indent=2))
```

#### SARIF Report

```python
# SARIF 2.1.0 format for CI/CD integration
sarif = linter.generate_report(result, format='sarif')
with open('dockerfile-lint.sarif', 'w') as f:
    f.write(sarif)
```

## Custom Rules

### Security Rules

| Rule ID | Description | Severity | Fix |
|---------|-------------|----------|-----|
| CUSTOM-SEC-001 | No USER instruction | ERROR | Add USER instruction before CMD/ENTRYPOINT |
| CUSTOM-SEC-002 | Running as root | ERROR | Use non-root user |
| CUSTOM-SEC-003 | Hardcoded secrets | ERROR | Use build args or environment variables |
| CUSTOM-SEC-004 | Vulnerable base images | WARNING | Pin to specific version tags |

### Optimization Rules

| Rule ID | Description | Severity | Fix |
|---------|-------------|----------|-----|
| CUSTOM-OPT-001 | Too many RUN commands | INFO | Combine RUN commands with && |
| CUSTOM-OPT-002 | apt-get without --no-install-recommends | WARNING | Add --no-install-recommends flag |
| CUSTOM-OPT-003 | Poor COPY ordering | INFO | Copy dependency files before source |
| CUSTOM-OPT-004 | Single-stage build | INFO | Use multi-stage builds |

### Compliance Rules

| Rule ID | Description | Severity | Fix |
|---------|-------------|----------|-----|
| CUSTOM-COMP-001 | Missing OCI labels | WARNING | Add required OCI annotations |

### Best Practice Rules

| Rule ID | Description | Severity | Fix |
|---------|-------------|----------|-----|
| CUSTOM-BEST-001 | No HEALTHCHECK | INFO | Add HEALTHCHECK instruction |
| CUSTOM-BEST-002 | Using cd instead of WORKDIR | WARNING | Use WORKDIR instruction |

## Secret Detection Patterns

The linter detects common secret patterns:

- **Passwords**: `password=`, `passwd=`, `pwd=`
- **API Keys**: `api_key=`, `apikey=`
- **Secrets/Tokens**: `secret=`, `token=`
- **AWS Credentials**: AWS-related key patterns
- **Private Keys**: References to private keys

## OCI Label Requirements

Required OCI labels for compliance:

- `org.opencontainers.image.title`
- `org.opencontainers.image.version`
- `org.opencontainers.image.created`
- `org.opencontainers.image.description`
- `org.opencontainers.image.authors`

## Examples

### Example 1: Basic Validation

```dockerfile
# Bad Dockerfile
FROM ubuntu:latest
RUN apt-get update
RUN apt-get install python3
COPY . .
CMD ["python3", "app.py"]
```

Findings:
- ERROR: No USER instruction
- WARNING: Using latest tag
- WARNING: Missing --no-install-recommends
- INFO: No HEALTHCHECK
- WARNING: Missing OCI labels

### Example 2: Good Dockerfile

```dockerfile
FROM ubuntu:22.04

LABEL org.opencontainers.image.title="My App" \
      org.opencontainers.image.version="1.0.0" \
      org.opencontainers.image.created="2024-01-01" \
      org.opencontainers.image.description="Application description" \
      org.opencontainers.image.authors="team@company.com"

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        python3 \
        python3-pip && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

COPY . .

RUN groupadd -r appuser && useradd -r -g appuser appuser
USER appuser

HEALTHCHECK --interval=30s --timeout=3s \
  CMD python3 -c "import requests; requests.get('http://localhost:8000/health')"

CMD ["python3", "app.py"]
```

Findings: None (clean Dockerfile)

## Integration

### CI/CD Pipeline

```yaml
# GitHub Actions
- name: Lint Dockerfile
  run: |
    python -m tools.container_platform.linter \
      --dockerfile Dockerfile \
      --format sarif \
      --output dockerfile-lint.sarif

- name: Upload SARIF
  uses: github/codeql-action/upload-sarif@v2
  with:
    sarif_file: dockerfile-lint.sarif
```

### Pre-commit Hook

```yaml
# .pre-commit-config.yaml
- repo: local
  hooks:
    - id: dockerfile-lint
      name: Dockerfile Linter
      entry: python -m tools.container_platform.linter
      language: system
      files: Dockerfile
```

## Performance

- Average scan time: < 1 second per Dockerfile
- Memory usage: < 50MB
- Supports concurrent linting of multiple files
- Efficient regex-based pattern matching

## Extensibility

### Adding Custom Rules

```python
from tools.container_platform.linter import (
    DockerfileLinter,
    LintRule,
    LintSeverity,
    RuleCategory
)

# Define custom rule
company_rule = LintRule(
    rule_id="COMPANY-001",
    description="Must include security contact label",
    severity=LintSeverity.ERROR,
    category=RuleCategory.COMPLIANCE,
    fix_suggestion="Add LABEL security.contact='security@company.com'"
)

# Use custom rule
linter = DockerfileLinter(custom_rules=[company_rule])
```

### Implementing Custom Checks

Extend the `DockerfileLinter` class:

```python
class CustomDockerfileLinter(DockerfileLinter):
    def _run_custom_checks(self, content, lines):
        findings = super()._run_custom_checks(content, lines)

        # Add your custom check
        if "EXPOSE 22" in content:
            findings.append(
                LintFinding(
                    rule_id="CUSTOM-SEC-999",
                    description="SSH port exposed",
                    severity=LintSeverity.ERROR,
                    category=RuleCategory.SECURITY,
                    fix_suggestion="Remove EXPOSE 22 - SSH should not be exposed"
                )
            )

        return findings
```

## Troubleshooting

### hadolint Not Found

If hadolint is not installed:
- Custom checks will still run
- Install hadolint for complete validation
- Use `check_hadolint_installed()` to verify

### False Positives

If you encounter false positives:
- Review the specific rule ID
- Check if the finding is actually valid
- Consider using exceptions for specific cases
- Submit feedback to improve detection

### Performance Issues

For large Dockerfiles:
- Linting is typically very fast (< 1s)
- If slow, check hadolint configuration
- Consider running in parallel for multiple files

## Architecture

```
DockerfileLinter
├── hadolint Integration
│   ├── Binary detection
│   ├── JSON output parsing
│   └── Error handling
├── Custom Checks
│   ├── Security validation
│   ├── Optimization detection
│   ├── Compliance checking
│   └── Best practices
└── Reporting
    ├── Text format
    ├── JSON format
    └── SARIF format
```

## Contributing

To add new checks:

1. Define the rule in appropriate category
2. Implement detection logic in `_check_*` method
3. Add tests for the new rule
4. Update documentation
5. Submit pull request

## License

Part of the Container Platform Management tool.
