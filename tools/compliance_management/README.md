# Compliance Management & Policy Enforcement Platform

**TOOL-SEC-011** - Part of devCrew_s1 security tooling

A comprehensive compliance management platform supporting multiple regulatory frameworks including GDPR, HIPAA, FedRAMP, SOC2, ISO 27001, and NIST 800-53.

## Features

- **Policy Engine**: OPA-style policy evaluation with Rego support and caching
- **Multi-Framework Compliance**: GDPR, HIPAA, FedRAMP, SOC2, ISO 27001, NIST 800-53
- **Policy Validation**: Syntax validation for Rego and YAML policies
- **Regulatory Mapping**: Map policies to regulatory controls with compliance matrix
- **Audit Reporting**: Generate reports in PDF, HTML, CSV, and JSON formats
- **Violation Tracking**: Full lifecycle management with severity levels

## Installation

```bash
pip install -r requirements.txt
```

## Quick Start

### Python API

```python
from compliance_management import (
    ComplianceManager,
    ComplianceFramework,
    PolicyEngine,
    AuditReporter,
    ReportFormat,
)

# Assess compliance
manager = ComplianceManager()
system_data = {
    "encryption_enabled": True,
    "access_controls": ["admin", "user"],
    "audit_logging_enabled": True,
    "mfa_enabled": True,
    "breach_notification_process": True,
}

# Single framework assessment
score = manager.assess_compliance(ComplianceFramework.GDPR, system_data)
print(f"GDPR Score: {score.score}% - {score.status.value}")

# All frameworks
all_scores = manager.assess_all_frameworks(system_data)
for framework, score in all_scores.items():
    print(f"{framework.value}: {score.score}%")

# Generate report
reporter = AuditReporter(organization_name="Your Organization")
reporter.generate_report(all_scores, ReportFormat.HTML, Path("report.html"))
```

### CLI Usage

```bash
# List available rules
python -m compliance_management.compliance_cli list-rules

# List supported frameworks
python -m compliance_management.compliance_cli list-frameworks

# Validate compliance
python -m compliance_management.compliance_cli validate-compliance \
    --input system_data.json \
    --frameworks gdpr hipaa

# Generate report
python -m compliance_management.compliance_cli generate-report \
    --input system_data.json \
    --output report.html \
    --format html \
    --org "Your Organization"

# Evaluate policy
python -m compliance_management.compliance_cli evaluate-policy \
    --policy policy.rego \
    --input data.json

# Map controls
python -m compliance_management.compliance_cli map-controls --matrix

# Test policy
python -m compliance_management.compliance_cli test-policy \
    --policy policy.rego \
    --tests tests.yaml
```

## Components

### Policy Engine (`policy_engine.py`)

Evaluates policies against input data with caching support.

```python
from compliance_management import PolicyEngine

engine = PolicyEngine()
engine.load_policy_from_string(policy_content, "my_policy")
result = engine.evaluate("my_policy", input_data)
print(f"Decision: {result.decision.value}")
```

### Compliance Manager (`compliance_manager.py`)

Manages compliance assessments across frameworks.

```python
from compliance_management import ComplianceManager, ComplianceFramework

manager = ComplianceManager()
score = manager.assess_compliance(ComplianceFramework.HIPAA, data)
```

### Policy Validator (`policy_validator.py`)

Validates policy syntax and runs tests.

```python
from compliance_management import PolicyValidator

validator = PolicyValidator()
result = validator.validate_rego(policy_content, "policy_name")
if result.is_valid:
    print("Policy is valid")
```

### Regulatory Mapper (`regulatory_mapper.py`)

Maps rules to regulatory controls.

```python
from compliance_management import RegulatoryMapper

mapper = RegulatoryMapper()
mapping = mapper.get_mapping("data_encryption")
matrix = mapper.generate_compliance_matrix()
```

### Audit Reporter (`audit_reporter.py`)

Generates compliance reports.

```python
from compliance_management import AuditReporter, ReportFormat

reporter = AuditReporter(organization_name="Org")
reporter.generate_report(scores, ReportFormat.HTML, Path("report.html"))
```

### Violation Tracker (`violation_tracker.py`)

Tracks compliance violations through their lifecycle.

```python
from compliance_management import ViolationTracker, ViolationSeverity

tracker = ViolationTracker()
violation = tracker.create_violation(
    rule_name="data_encryption",
    framework="gdpr",
    control_id="GDPR-32",
    severity=ViolationSeverity.HIGH,
    description="Encryption not enabled",
    resource="database",
)
```

## Supported Frameworks

| Framework | Controls | Description |
|-----------|----------|-------------|
| GDPR | 5 | EU General Data Protection Regulation |
| HIPAA | 5 | Health Insurance Portability and Accountability Act |
| FedRAMP | 6 | Federal Risk and Authorization Management Program |
| SOC2 | 5 | Service Organization Control 2 |
| ISO 27001 | 6 | Information Security Management |
| NIST 800-53 | 7 | Security and Privacy Controls |

## Input Data Format

```json
{
    "encryption_enabled": true,
    "access_controls": ["admin", "user", "readonly"],
    "audit_logging_enabled": true,
    "retention_policy": "90 days",
    "consent_obtained": true,
    "data_minimized": true,
    "breach_notification_process": true,
    "mfa_enabled": true,
    "firewall_enabled": true,
    "vulnerability_scanning": true
}
```

## Running Tests

```bash
# Run all tests
pytest tools/compliance_management/test_compliance.py -v

# Run with coverage
pytest tools/compliance_management/test_compliance.py -v --cov=tools/compliance_management --cov-report=term-missing
```

## Protocols Implemented

- **P-AGILE-PRIVACY**: Privacy-first design with consent management
- **GOV-PaC**: Policy as Code governance
- **P-SECURITY-SCAN**: Security scanning integration
- **SCM-SBOM**: Software Bill of Materials support
- **SCM-SLSA**: Supply chain security levels
- **SCM-VEX**: Vulnerability Exploitability eXchange
- **SEC-THREAT-MODEL**: Threat modeling support

## License

Part of devCrew_s1 security tooling.
