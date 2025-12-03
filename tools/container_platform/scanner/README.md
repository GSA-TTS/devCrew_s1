# Security Scanner Module

Comprehensive container security scanning module for the Container Platform Management tool.

## Overview

The Security Scanner provides multi-scanner support for vulnerability detection, SBOM generation, misconfiguration scanning, and secret detection with intelligent caching and result aggregation.

## Features

### Core Capabilities

- **Multi-Scanner Support**: Integration with both Trivy and Grype
- **Vulnerability Scanning**: CVE detection with severity filtering
- **SBOM Generation**: SPDX and CycloneDX format support
- **Misconfiguration Detection**: Dockerfile and Kubernetes manifest scanning
- **Secret Detection**: Embedded credentials and API keys
- **License Compliance**: Package license analysis
- **Result Caching**: TTL-based caching for improved performance
- **Ignore Lists**: Filter known false positives

### Scanner Integrations

#### Trivy
- Primary scanner with comprehensive features
- CVE database from NVD and vendor advisories
- Supports all feature types (vulnerabilities, misconfigs, secrets, licenses)
- SBOM generation support

#### Grype
- Alternative/complementary scanner
- Fast vulnerability detection
- Good for CI/CD pipelines
- Can run alongside Trivy for cross-validation

## Installation

### Prerequisites

Install at least one scanner:

```bash
# Install Trivy (recommended)
# macOS
brew install aquasecurity/trivy/trivy

# Linux
curl -sfL https://raw.githubusercontent.com/aquasecurity/trivy/main/contrib/install.sh | sh -s -- -b /usr/local/bin

# Install Grype (optional)
# macOS
brew install anchore/grype/grype

# Linux
curl -sSfL https://raw.githubusercontent.com/anchore/grype/main/install.sh | sh -s -- -b /usr/local/bin
```

### Python Dependencies

```bash
pip install pydantic
```

## Usage

### Basic Scanning

```python
from scanner import SecurityScanner, ScannerConfig, SeverityLevel

# Initialize scanner with defaults
scanner = SecurityScanner()

# Scan an image
result = scanner.scan_image("nginx:latest")

# Print summary
print(result.get_summary())
print(f"Critical vulnerabilities: {result.critical_count}")
print(f"Fixable vulnerabilities: {result.fixable_count}")
```

### Advanced Configuration

```python
from pathlib import Path
from scanner import (
    SecurityScanner,
    ScannerConfig,
    ScannerType,
    SeverityLevel,
    SBOMFormat
)

# Configure scanner
config = ScannerConfig(
    scanner_type=ScannerType.BOTH,  # Use both Trivy and Grype
    severity_threshold=SeverityLevel.HIGH,  # Only HIGH and CRITICAL
    ignore_unfixed=True,  # Skip vulnerabilities without fixes
    enable_cache=True,
    cache_ttl=3600,  # 1 hour cache
    cache_dir=Path("~/.scan-cache").expanduser(),
    output_dir=Path("./scan-results"),
    ignore_list=["CVE-2023-12345"],  # Known false positives
    scan_misconfig=True,
    scan_secrets=True,
    scan_licenses=True,
)

scanner = SecurityScanner(config)

# Scan with SBOM generation
result = scanner.scan_image(
    "myapp:v1.0",
    generate_sbom=True,
    sbom_format=SBOMFormat.CYCLONEDX_JSON
)

# Access different finding types
for vuln in result.vulnerabilities:
    if vuln.severity == SeverityLevel.CRITICAL:
        print(f"CRITICAL: {vuln.id} in {vuln.package_name}")
        print(f"  Installed: {vuln.installed_version}")
        if vuln.fixed_version:
            print(f"  Fix available: {vuln.fixed_version}")

for misconfig in result.misconfigurations:
    print(f"Misconfiguration: {misconfig.title}")
    print(f"  File: {misconfig.file_path}:{misconfig.line_number}")
    print(f"  Remediation: {misconfig.remediation}")

for secret in result.secrets:
    print(f"SECRET FOUND: {secret.type} in {secret.file_path}")
```

### Database Management

```python
# Update vulnerability databases
scanner.update_vulnerability_database()  # Update all scanners
scanner.update_vulnerability_database("trivy")  # Update specific scanner

# Clear cache
removed = scanner.clear_cache()
print(f"Removed {removed} cached results")
```

### Scanner Selection

```python
# Use only Trivy
config = ScannerConfig(scanner_type=ScannerType.TRIVY)
scanner = SecurityScanner(config)

# Use only Grype
config = ScannerConfig(scanner_type=ScannerType.GRYPE)
scanner = SecurityScanner(config)

# Use both for comprehensive coverage
config = ScannerConfig(scanner_type=ScannerType.BOTH)
scanner = SecurityScanner(config)
# Results will be aggregated and deduplicated
```

## Data Models

### Vulnerability

```python
class Vulnerability(BaseModel):
    id: str                          # CVE-2023-0001
    severity: SeverityLevel          # CRITICAL, HIGH, MEDIUM, LOW
    title: str                       # Short description
    description: str                 # Detailed description
    package_name: str                # Affected package
    installed_version: str           # Current version
    fixed_version: Optional[str]     # Fixed in version
    cvss_score: Optional[float]      # CVSS score (0-10)
    cvss_vector: Optional[str]       # CVSS vector string
    cwe_ids: List[str]               # CWE identifiers
    published_date: Optional[datetime]
    references: List[str]            # Reference URLs
    scanner: str                     # Scanner that found it
```

### Misconfiguration

```python
class Misconfiguration(BaseModel):
    id: str                          # Check ID
    type: MisconfigType              # DOCKERFILE, KUBERNETES, SECRETS
    severity: SeverityLevel
    title: str
    description: str
    file_path: str                   # File with issue
    line_number: Optional[int]       # Line number
    remediation: str                 # How to fix
    references: List[str]
```

### ScanResult

```python
class ScanResult(BaseModel):
    image: str                       # Scanned image
    scan_time: datetime
    scanner_version: Dict[str, str]  # Scanner versions used
    vulnerabilities: List[Vulnerability]
    misconfigurations: List[Misconfiguration]
    secrets: List[SecretFinding]
    licenses: List[LicenseFinding]
    sbom: Optional[Dict[str, Any]]
    metadata: Dict[str, Any]

    # Convenience properties
    @property
    def total_vulnerabilities(self) -> int
    @property
    def critical_count(self) -> int
    @property
    def high_count(self) -> int
    @property
    def fixable_count(self) -> int
```

## Caching

The scanner implements intelligent caching to improve performance:

- Cache keys include image name and scan configuration
- Configurable TTL (default: 1 hour)
- Automatic cache invalidation on config changes
- Cache stored in user home directory by default

```python
# Disable caching
config = ScannerConfig(enable_cache=False)

# Custom cache location and TTL
config = ScannerConfig(
    enable_cache=True,
    cache_dir=Path("/tmp/scan-cache"),
    cache_ttl=7200  # 2 hours
)
```

## Error Handling

```python
from scanner import (
    SecurityScanError,
    ScannerNotFoundError,
    ImageNotFoundError,
    ScanTimeoutError,
    InvalidImageNameError
)

try:
    result = scanner.scan_image("nginx:latest")
except ScannerNotFoundError:
    print("No scanners installed")
except ImageNotFoundError:
    print("Image not found in registry")
except ScanTimeoutError:
    print("Scan timed out")
except InvalidImageNameError:
    print("Invalid image name format")
except SecurityScanError as e:
    print(f"Scan error: {e}")
```

## Performance Considerations

### Scan Performance

- First scan: Includes database update (slow)
- Subsequent scans: Use cached database (fast)
- Large images: May take several minutes
- Recommended timeout: 600s (10 minutes)

### Optimization Tips

```python
# Skip database updates for faster scans
config = ScannerConfig(skip_db_update=True)

# Use cache for repeated scans
config = ScannerConfig(enable_cache=True)

# Scan only high severity issues
config = ScannerConfig(
    severity_threshold=SeverityLevel.HIGH,
    ignore_unfixed=True
)

# Disable extra scans
config = ScannerConfig(
    scan_misconfig=False,
    scan_secrets=False,
    scan_licenses=False
)
```

## Integration Examples

### CI/CD Pipeline

```python
#!/usr/bin/env python3
import sys
from scanner import SecurityScanner, SeverityLevel

def main():
    scanner = SecurityScanner()
    result = scanner.scan_image("myapp:latest")

    # Fail on critical vulnerabilities
    if result.critical_count > 0:
        print(f"FAIL: {result.critical_count} critical vulnerabilities")
        for vuln in result.vulnerabilities:
            if vuln.severity == SeverityLevel.CRITICAL:
                print(f"  - {vuln.id}: {vuln.title}")
        sys.exit(1)

    # Fail on secrets
    if len(result.secrets) > 0:
        print(f"FAIL: {len(result.secrets)} secrets found")
        sys.exit(1)

    print("PASS: No critical issues")
    return 0

if __name__ == "__main__":
    sys.exit(main())
```

### Report Generation

```python
import json
from pathlib import Path

def generate_report(result):
    """Generate JSON report."""
    report = {
        "image": result.image,
        "scan_time": result.scan_time.isoformat(),
        "summary": result.get_summary(),
        "vulnerabilities": [
            {
                "id": v.id,
                "severity": v.severity.value,
                "package": v.package_name,
                "version": v.installed_version,
                "fixed": v.fixed_version,
                "cvss": v.cvss_score,
            }
            for v in result.vulnerabilities
        ],
        "critical_findings": result.has_critical_findings(),
    }

    Path("scan-report.json").write_text(
        json.dumps(report, indent=2)
    )

scanner = SecurityScanner()
result = scanner.scan_image("nginx:latest")
generate_report(result)
```

## Testing

Run the test suite:

```bash
# Run all tests
pytest test_security_scanner.py -v

# Run specific test class
pytest test_security_scanner.py::TestSecurityScanner -v

# Run with coverage
pytest test_security_scanner.py --cov=security_scanner --cov-report=html
```

## Architecture

### Module Structure

```
scanner/
├── __init__.py              # Public API exports
├── security_scanner.py      # Main implementation (1239 lines)
├── test_security_scanner.py # Test suite
└── README.md               # This file
```

### Class Hierarchy

```
SecurityScanner
├── Scanner detection and initialization
├── Cache management
├── Trivy integration (_run_trivy_scan, _parse_trivy_results)
├── Grype integration (_run_grype_scan, _parse_grype_results)
├── Result aggregation (_aggregate_vulnerabilities)
└── Public API (scan_image, generate_sbom, update_database)

Pydantic Models
├── ScannerConfig         # Configuration
├── Vulnerability         # Vulnerability finding
├── Misconfiguration      # Misconfiguration finding
├── SecretFinding         # Secret detection
├── LicenseFinding        # License issue
└── ScanResult            # Complete scan results
```

## Limitations

- Requires at least one scanner (Trivy or Grype) installed
- SBOM generation requires Trivy
- Secret scanning requires Trivy
- License scanning requires Trivy
- Misconfiguration scanning requires Trivy
- Cache does not persist across image updates

## Contributing

When contributing to this module:

1. Follow Black code formatting (line length: 88)
2. Add type hints to all functions
3. Include comprehensive docstrings
4. Update tests for new functionality
5. Run quality checks: `black`, `flake8`, `mypy`

## License

MIT License - Part of devCrew_s1 Container Platform Management tool.

## Support

For issues and questions:
- Issue: #58 in devCrew_s1 repository
- Protocol: TOOL-CONTAINER-PLATFORM
