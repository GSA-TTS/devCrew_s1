# Privacy Management & Data Protection Platform

TOOL-DATA-003: A comprehensive privacy management platform for PII detection, data anonymization, consent management, compliance validation, and audit logging.

## Features

- **PII Detection**: Detect emails, phones, SSNs, credit cards, IP addresses, names, and addresses
- **Data Anonymization**: Masking, hashing, pseudonymization, generalization, and suppression
- **Consent Management**: Record, check, and revoke user consent with full history
- **Compliance Validation**: GDPR and CCPA compliance checks with scoring
- **Audit Logging**: Tamper-evident logging with hash-based integrity verification

## Installation

```bash
cd tools/privacy_management
pip install -r requirements.txt
```

## Quick Start

### Python API

```python
from privacy_manager import PrivacyManager

# Initialize
manager = PrivacyManager()

# Scan for PII
result = manager.scan_for_pii("Contact: john@example.com, 555-123-4567")
print(result["summary"])  # {'email': 1, 'phone': 1}

# Anonymize data
anonymized = manager.anonymize_data(
    "SSN: 123-45-6789",
    method="masking"
)
print(anonymized)  # SSN: ***-**-6789

# Record consent
manager.record_consent("user123", ["marketing", "analytics"], opt_in=True)

# Check consent
has_consent = manager.check_consent("user123", "marketing")

# Validate compliance
report = manager.validate_compliance("gdpr")
print(f"Compliance score: {report['score']}%")
```

### CLI Usage

```bash
# Scan text for PII
python privacy_manager.py scan-pii "Email: test@example.com"

# Anonymize text
python privacy_manager.py anonymize "SSN: 123-45-6789" --method masking

# Check consent
python privacy_manager.py check-consent user123 marketing

# Validate compliance
python privacy_manager.py validate-compliance gdpr

# View audit logs
python privacy_manager.py audit-log --limit 10
```

## Components

### PII Detector

```python
from pii_detector import PIIDetector, PIIType

detector = PIIDetector()
matches = detector.scan_text("Contact: user@test.com")
```

### Data Anonymizer

```python
from data_anonymizer import DataAnonymizer, AnonymizationMethod

anonymizer = DataAnonymizer()
masked = anonymizer.mask("1234567890")  # ******7890
hashed = anonymizer.hash_value("sensitive")
pseudo = anonymizer.pseudonymize("user@test.com")
```

### Consent Manager

```python
from consent_manager import ConsentManager, ConsentPurpose

consent = ConsentManager()
consent.record_consent("user1", [ConsentPurpose.MARKETING], opt_in=True)
consent.check_consent("user1", ConsentPurpose.MARKETING)  # True
consent.revoke_consent("user1", [ConsentPurpose.MARKETING])
```

### Compliance Validator

```python
from compliance_validator import ComplianceValidator, ComplianceFramework

validator = ComplianceValidator()
report = validator.generate_compliance_report(ComplianceFramework.GDPR)
```

### Audit Logger

```python
from audit_logger import AuditLogger, AuditEventType

logger = AuditLogger(log_file="audit.log")
logger.log_event(AuditEventType.DATA_ACCESS, "User viewed record", user_id="user1")
events = logger.query_logs(user_id="user1")
```

## Testing

```bash
# Run all tests
pytest test_privacy.py -v

# Run specific test class
pytest test_privacy.py::TestPIIDetector -v

# Run with coverage
pytest test_privacy.py --cov=. --cov-report=term-missing
```

## License

MIT License
