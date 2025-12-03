# Software Composition Analysis (SCA) Scanner

![Python](https://img.shields.io/badge/python-3.10+-blue.svg)
![License](https://img.shields.io/badge/license-Apache%202.0-green.svg)
![Status](https://img.shields.io/badge/status-production-brightgreen.svg)

## Overview

The SCA Scanner is a comprehensive Software Composition Analysis platform designed for the devCrew_s1 project. It provides enterprise-grade dependency vulnerability scanning, license compliance validation, and supply chain security analysis across multiple programming language ecosystems.

The scanner combines real-time CVE database lookups with SBOM generation capabilities, enabling development teams to identify security vulnerabilities, ensure license compliance, and maintain supply chain integrity throughout the software development lifecycle.

This tool integrates seamlessly with CI/CD pipelines and supports industry-standard protocols including SCM-SBOM, SCM-SLSA, and SCM-VEX for comprehensive software composition transparency and vulnerability communication.

### Key Capabilities

- **Multi-Language Support**: Scan Python, Node.js, Java, Go, Ruby, and Rust dependencies
- **Real-Time Vulnerability Detection**: Query NVD, OSV, and GitHub Advisory databases
- **License Compliance**: Validate against organizational policies with SPDX compliance checking
- **SBOM Generation**: Produce SPDX 2.3 and CycloneDX 1.4 format SBOMs
- **Supply Chain Security**: Detect dependency confusion, typosquatting, and malicious patterns
- **Intelligent Remediation**: Get actionable upgrade recommendations with breaking change analysis
- **CI/CD Integration**: Native support for GitHub Actions, GitLab CI, and Jenkins
- **Offline Capability**: Local caching for air-gapped environments

### Protocol Support

- **SCM-SBOM**: Generate standardized Software Bill of Materials in SPDX 2.3 and CycloneDX 1.4 formats
- **SCM-SLSA**: Supply chain provenance verification following SLSA framework guidelines
- **SCM-VEX**: Vulnerability Exploitability eXchange documents in OpenVEX format for status communication

## Features

### Dependency Scanning

The scanner automatically detects and parses dependency manifests across multiple ecosystems:

- **Python**: requirements.txt, Pipfile.lock, poetry.lock, pyproject.toml
- **Node.js**: package.json, package-lock.json, yarn.lock, pnpm-lock.yaml
- **Java**: pom.xml, build.gradle, build.gradle.kts
- **Go**: go.mod, go.sum
- **Ruby**: Gemfile.lock
- **Rust**: Cargo.lock

Features include transitive dependency analysis, lockfile parsing, and dependency tree resolution.

### Vulnerability Matching

Real-time CVE lookups with:

- Multiple database integration (NVD, OSV, GitHub Advisory Database)
- CVSS 3.1 severity scoring
- Local caching for performance and offline operation
- Rate limiting and connection pooling
- Batch processing for large dependency sets

### License Compliance

Comprehensive license validation featuring:

- SPDX license identifier detection and normalization
- Configurable policy engine with allow/deny lists
- Copyleft license detection (GPL, AGPL, etc.)
- OSI-approved license validation
- License compatibility analysis
- Multi-license expression parsing

### SBOM Generation

Industry-standard SBOM formats:

- **SPDX 2.3**: JSON format with full metadata and relationships
- **CycloneDX 1.4**: JSON and XML formats with component relationships
- SHA256 hash generation for package integrity
- Schema validation for compliance
- Package URL (PURL) support

### Supply Chain Security

Advanced security analysis including:

- Package integrity verification
- Dependency confusion attack detection
- Typosquatting analysis against popular packages
- Malicious pattern detection in package code
- Package health scoring (downloads, releases, maintainer activity)
- Maintainer trust scoring

### Remediation Recommendations

Intelligent upgrade guidance with:

- Semantic versioning-aware upgrade paths
- Breaking change detection and analysis
- Alternative package suggestions
- Priority scoring based on severity and exploitability
- Migration effort estimation
- Patch availability checking

### CI/CD Integration

Native integration support for:

- GitHub Actions with SARIF output
- GitLab CI Security Dashboard
- Jenkins pipeline integration
- Fail-on-severity thresholds
- JSON and SARIF report formats

## Prerequisites

- **Python**: 3.10 or higher
- **pip**: Latest version recommended
- **Optional**: API keys for enhanced functionality
  - NVD API key for higher rate limits
  - GitHub token for Advisory Database access

### Required Packages

The scanner requires the following Python packages (automatically installed):

```
requests>=2.31.0
cachetools>=5.3.0
packaging>=23.1
tomli>=2.0.1; python_version < "3.11"
license-expression>=30.1.0
jsonschema>=4.19.0
packageurl-python>=0.11.2
```

## Installation

### Basic Installation

```bash
cd /Users/tamnguyen/Documents/GitHub/devCrew_s1/tools/sca_scanner
pip install -r requirements.txt
```

### Development Installation

For development with testing capabilities:

```bash
pip install -r requirements.txt
pip install -r requirements-dev.txt  # If available
```

### Verify Installation

```bash
python -c "from tools.sca_scanner import DependencyScanner; print('Installation successful')"
```

## Quick Start

### Basic Vulnerability Scan

Scan a Python project for vulnerabilities:

```bash
python sca_cli.py scan --manifest requirements.txt
```

### Generate SBOM

Create an SPDX format SBOM:

```bash
python sca_cli.py sbom --manifest package.json --format spdx --output sbom.json
```

### License Compliance Check

Validate licenses against a policy:

```bash
python sca_cli.py licenses --manifest requirements.txt --policy license-policy.yaml
```

### Comprehensive Security Scan

Run a full security analysis with all features:

```bash
python sca_cli.py report --manifest requirements.txt \
  --vulnerabilities \
  --licenses \
  --supply-chain \
  --output comprehensive-report.json
```

## Usage

### Scan Command

The `scan` command performs vulnerability scanning on dependencies.

**Basic Usage:**

```bash
python sca_cli.py scan --manifest <manifest_file>
```

**Options:**

- `--manifest PATH`: Path to dependency manifest file (required)
- `--severity LEVEL`: Minimum severity to report (CRITICAL, HIGH, MEDIUM, LOW)
- `--fail-on-severity LEVEL`: Exit with error if vulnerabilities at or above this level are found
- `--output PATH`: Path to output JSON report
- `--databases DB1,DB2`: Comma-separated list of databases to query (nvd,osv,github)
- `--cache-ttl SECONDS`: Cache time-to-live in seconds (default: 86400)
- `--no-cache`: Disable caching

**Examples:**

```bash
# Scan with HIGH severity threshold
python sca_cli.py scan --manifest requirements.txt --severity HIGH

# Fail CI/CD pipeline on CRITICAL vulnerabilities
python sca_cli.py scan --manifest package.json --fail-on-severity CRITICAL --output scan-results.json

# Scan using only OSV database
python sca_cli.py scan --manifest go.mod --databases osv --no-cache

# Scan with custom cache TTL
python sca_cli.py scan --manifest Cargo.lock --cache-ttl 3600
```

### SBOM Command

Generate Software Bill of Materials in multiple formats.

**Basic Usage:**

```bash
python sca_cli.py sbom --manifest <manifest_file> --output <output_file>
```

**Options:**

- `--manifest PATH`: Path to dependency manifest file (required)
- `--format FORMAT`: SBOM format (spdx, cyclonedx) - default: spdx
- `--output PATH`: Output file path (required)
- `--output-format FORMAT`: Serialization format (json, xml) - default: json
- `--document-name NAME`: SBOM document name
- `--project-name NAME`: Project name for SBOM metadata
- `--validate`: Validate SBOM against schema

**SPDX Examples:**

```bash
# Generate SPDX 2.3 SBOM in JSON format
python sca_cli.py sbom \
  --manifest requirements.txt \
  --format spdx \
  --output sbom-spdx.json \
  --document-name "MyProject-SBOM" \
  --project-name "MyProject"

# Generate with validation
python sca_cli.py sbom \
  --manifest package.json \
  --format spdx \
  --output sbom.json \
  --validate
```

**CycloneDX Examples:**

```bash
# Generate CycloneDX 1.4 SBOM in JSON format
python sca_cli.py sbom \
  --manifest pom.xml \
  --format cyclonedx \
  --output sbom-cdx.json

# Generate CycloneDX in XML format
python sca_cli.py sbom \
  --manifest build.gradle \
  --format cyclonedx \
  --output sbom-cdx.xml \
  --output-format xml
```

### Licenses Command

Perform license compliance validation and policy enforcement.

**Basic Usage:**

```bash
python sca_cli.py licenses --manifest <manifest_file>
```

**Options:**

- `--manifest PATH`: Path to dependency manifest file (required)
- `--policy PATH`: Path to license policy YAML file
- `--output PATH`: Output file for license report
- `--format FORMAT`: Output format (json, table) - default: table
- `--fail-on-violation`: Exit with error if policy violations found

**Examples:**

```bash
# Check licenses with default policy
python sca_cli.py licenses --manifest requirements.txt

# Check against custom policy
python sca_cli.py licenses \
  --manifest package.json \
  --policy custom-license-policy.yaml \
  --output license-report.json

# Fail CI/CD on violations
python sca_cli.py licenses \
  --manifest go.mod \
  --policy license-policy.yaml \
  --fail-on-violation
```

**Policy File Format:**

Create `license-policy.yaml`:

```yaml
# Allowed licenses
allowed_licenses:
  - MIT
  - Apache-2.0
  - BSD-2-Clause
  - BSD-3-Clause
  - ISC
  - CC0-1.0
  - Unlicense

# Explicitly denied licenses
denied_licenses:
  - GPL-3.0
  - GPL-3.0-only
  - GPL-3.0-or-later
  - AGPL-3.0
  - AGPL-3.0-only
  - AGPL-3.0-or-later

# Conditional licenses (require review)
conditional_licenses:
  - LGPL-2.1
  - LGPL-3.0
  - MPL-2.0
  - EPL-2.0

# Require OSI-approved licenses
require_osi_approved: true

# Allow unknown licenses with warning
allow_unknown: false
```

### VEX Command

Generate Vulnerability Exploitability eXchange documents.

**Basic Usage:**

```bash
python sca_cli.py vex --manifest <manifest_file> --output <vex_file>
```

**Options:**

- `--manifest PATH`: Path to dependency manifest file (required)
- `--output PATH`: Output VEX document path (required)
- `--format FORMAT`: VEX format (openvex, csaf) - default: openvex
- `--status STATUS`: Default vulnerability status (affected, not_affected, under_investigation)
- `--justification TEXT`: Justification for vulnerability status

**Examples:**

```bash
# Generate OpenVEX document
python sca_cli.py vex \
  --manifest requirements.txt \
  --output project.vex.json \
  --format openvex

# Document vulnerabilities as not affected with justification
python sca_cli.py vex \
  --manifest package.json \
  --output vex-statement.json \
  --status not_affected \
  --justification "Vulnerability in unused code path"
```

### Report Command

Generate comprehensive security reports combining all analysis features.

**Basic Usage:**

```bash
python sca_cli.py report --manifest <manifest_file> --output <report_file>
```

**Options:**

- `--manifest PATH`: Path to dependency manifest file (required)
- `--output PATH`: Output report path (required)
- `--vulnerabilities`: Include vulnerability scan results
- `--licenses`: Include license compliance report
- `--supply-chain`: Include supply chain security analysis
- `--remediation`: Include remediation recommendations
- `--format FORMAT`: Output format (json, html, sarif) - default: json
- `--severity LEVEL`: Minimum severity threshold

**Examples:**

```bash
# Comprehensive report with all features
python sca_cli.py report \
  --manifest requirements.txt \
  --output full-report.json \
  --vulnerabilities \
  --licenses \
  --supply-chain \
  --remediation

# Vulnerability-focused report for CI/CD
python sca_cli.py report \
  --manifest package.json \
  --output security-report.sarif \
  --vulnerabilities \
  --format sarif \
  --severity HIGH

# HTML report for stakeholders
python sca_cli.py report \
  --manifest go.mod \
  --output security-dashboard.html \
  --vulnerabilities \
  --licenses \
  --supply-chain \
  --format html
```

## Configuration

### sca-config.yaml

Create a configuration file to customize scanner behavior:

```yaml
# Vulnerability Scanning Configuration
vulnerability_scanning:
  # Minimum severity to report (CRITICAL, HIGH, MEDIUM, LOW)
  severity_threshold: HIGH

  # Vulnerability databases to query
  databases:
    - nvd
    - osv
    - github

  # CVEs to ignore (with justification)
  ignored_vulnerabilities:
    - cve: CVE-2023-12345
      reason: "Not applicable - vulnerability in unused feature"
      expires: "2024-12-31"
    - cve: CVE-2023-67890
      reason: "Mitigated by network controls"
      expires: "2025-06-30"

  # Cache configuration
  cache_ttl: 86400  # 24 hours in seconds
  cache_dir: ".sca_cache"

# License Compliance Configuration
license_compliance:
  # Policy file path
  policy_file: "license-policy.yaml"

  # Fail on policy violations
  fail_on_violation: true

  # Require all licenses to be SPDX-compliant
  require_spdx: true

# SBOM Generation Configuration
sbom:
  # Default format
  default_format: "spdx"

  # Include development dependencies
  include_dev_dependencies: false

  # Generate package hashes
  generate_hashes: true

  # SBOM metadata
  metadata:
    creator: "DevCrew SCA Scanner"
    supplier: "Organization: devCrew_s1"

# Supply Chain Security Configuration
supply_chain:
  # Enable typosquatting detection
  check_typosquatting: true

  # Enable dependency confusion detection
  check_dependency_confusion: true

  # Enable malicious pattern detection
  check_malicious_patterns: true

  # Package health thresholds
  health_thresholds:
    min_downloads_monthly: 1000
    min_releases_yearly: 4
    max_unmaintained_days: 730

# API Configuration
api:
  # API keys for enhanced functionality
  nvd_api_key: "${NVD_API_KEY}"
  github_token: "${GITHUB_TOKEN}"

  # Request timeout in seconds
  timeout: 10

  # Rate limiting
  rate_limit:
    requests_per_minute: 30

# Output Configuration
output:
  # Default output format
  default_format: "json"

  # Pretty print JSON output
  json_indent: 2

  # Include verbose details
  verbose: false

# CI/CD Integration
cicd:
  # Fail pipeline on severity threshold
  fail_on_severity: "HIGH"

  # Generate SARIF for code scanning
  generate_sarif: true

  # Upload results to security dashboard
  upload_results: false
```

**Using Configuration File:**

```bash
# Load configuration from file
python sca_cli.py scan --manifest requirements.txt --config sca-config.yaml

# Override specific options
python sca_cli.py scan \
  --manifest requirements.txt \
  --config sca-config.yaml \
  --severity CRITICAL
```

### license-policy.yaml

Comprehensive license policy configuration:

```yaml
# License Policy Configuration

# Explicitly allowed licenses
allowed_licenses:
  # Permissive licenses
  - MIT
  - Apache-2.0
  - BSD-2-Clause
  - BSD-3-Clause
  - ISC
  - Unlicense
  - CC0-1.0

  # Weak copyleft (with restrictions)
  - LGPL-2.1
  - LGPL-3.0
  - MPL-2.0

# Explicitly denied licenses
denied_licenses:
  # Strong copyleft
  - GPL-2.0
  - GPL-2.0-only
  - GPL-2.0-or-later
  - GPL-3.0
  - GPL-3.0-only
  - GPL-3.0-or-later
  - AGPL-3.0
  - AGPL-3.0-only
  - AGPL-3.0-or-later

  # Proprietary
  - Proprietary
  - Commercial

# Licenses requiring manual review
conditional_licenses:
  - EPL-2.0
  - CDDL-1.0
  - CPL-1.0
  - CC-BY-SA-4.0

# Policy rules
rules:
  # Require OSI-approved licenses
  require_osi_approved: true

  # Allow unknown licenses (with warning)
  allow_unknown: false

  # Allow deprecated SPDX identifiers
  allow_deprecated: false

  # Fail on license conflicts
  fail_on_conflicts: true

# Ecosystem-specific overrides
ecosystem_overrides:
  python:
    # Allow PSF license for Python stdlib packages
    additional_allowed:
      - PSF-2.0
      - Python-2.0

  javascript:
    # Allow Artistic license for Perl-related packages
    additional_allowed:
      - Artistic-2.0

# Package-specific exceptions
package_exceptions:
  - package: "readline"
    ecosystem: "python"
    allowed_licenses:
      - GPL-3.0
    reason: "System library, dynamically linked"

  - package: "gnu-sed"
    ecosystem: "npm"
    allowed_licenses:
      - GPL-3.0
    reason: "Development tool, not distributed"

# Notification settings
notifications:
  # Warn about packages with multiple licenses
  warn_multiple_licenses: true

  # Warn about license expression complexity
  warn_complex_expressions: true

  # Email notifications for violations
  email_on_violation: false
  email_recipients:
    - security@devCrew_s1.example.com
```

## Output Formats

### JSON Report

The scanner produces structured JSON reports with complete vulnerability, license, and supply chain information.

**Example Vulnerability Report:**

```json
{
  "scan_id": "550e8400-e29b-41d4-a716-446655440000",
  "timestamp": "2025-12-03T10:30:00Z",
  "scanner_version": "1.0.0",
  "manifest": {
    "path": "/path/to/requirements.txt",
    "type": "requirements.txt",
    "ecosystem": "pypi"
  },
  "summary": {
    "total_dependencies": 45,
    "direct_dependencies": 15,
    "transitive_dependencies": 30,
    "vulnerabilities": {
      "critical": 0,
      "high": 2,
      "medium": 5,
      "low": 8,
      "total": 15
    },
    "licenses": {
      "compliant": 40,
      "violations": 5,
      "unknown": 0
    }
  },
  "findings": [
    {
      "package": "requests",
      "version": "2.25.0",
      "ecosystem": "pypi",
      "is_direct": true,
      "vulnerabilities": [
        {
          "id": "CVE-2023-32681",
          "description": "Requests is vulnerable to unintended proxy usage",
          "severity": "HIGH",
          "cvss_score": 7.5,
          "cvss_vector": "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:N/A:N",
          "cwe": ["CWE-918"],
          "affected_versions": ">=2.0.0,<2.31.0",
          "fixed_versions": ["2.31.0"],
          "published": "2023-05-26T14:15:00Z",
          "references": [
            "https://nvd.nist.gov/vuln/detail/CVE-2023-32681",
            "https://github.com/psf/requests/security/advisories/GHSA-j8r2-6x86-q33q"
          ],
          "source": "nvd"
        }
      ],
      "licenses": [
        {
          "license": "Apache-2.0",
          "spdx_id": "Apache-2.0",
          "is_osi_approved": true,
          "policy_status": "allowed",
          "policy_violation": false
        }
      ],
      "supply_chain": {
        "integrity_verified": true,
        "typosquatting_risk": false,
        "dependency_confusion_risk": false,
        "health_score": 95,
        "trust_score": 98
      },
      "remediation": {
        "recommended_version": "2.31.0",
        "upgrade_type": "minor",
        "breaking_changes": false,
        "priority_score": 85,
        "action": "Upgrade to version 2.31.0 to fix CVE-2023-32681",
        "confidence": "high"
      }
    }
  ],
  "statistics": {
    "scan_duration_seconds": 12.5,
    "dependencies_scanned": 45,
    "api_calls": 45,
    "cache_hits": 38,
    "cache_misses": 7
  }
}
```

### SBOM Formats

#### SPDX 2.3 Format

```json
{
  "spdxVersion": "SPDX-2.3",
  "dataLicense": "CC0-1.0",
  "SPDXID": "SPDXRef-DOCUMENT",
  "name": "MyProject-SBOM",
  "documentNamespace": "https://devCrew_s1.example.com/sboms/550e8400-e29b-41d4-a716-446655440000",
  "creationInfo": {
    "created": "2025-12-03T10:30:00Z",
    "creators": [
      "Tool: DevCrew SCA Scanner-1.0.0",
      "Organization: devCrew_s1"
    ],
    "licenseListVersion": "3.21"
  },
  "packages": [
    {
      "SPDXID": "SPDXRef-Package-requests-2.31.0",
      "name": "requests",
      "versionInfo": "2.31.0",
      "downloadLocation": "https://pypi.org/project/requests/2.31.0",
      "filesAnalyzed": false,
      "licenseConcluded": "Apache-2.0",
      "licenseDeclared": "Apache-2.0",
      "copyrightText": "Copyright (c) Kenneth Reitz",
      "externalRefs": [
        {
          "referenceCategory": "PACKAGE-MANAGER",
          "referenceType": "purl",
          "referenceLocator": "pkg:pypi/requests@2.31.0"
        }
      ],
      "checksums": [
        {
          "algorithm": "SHA256",
          "checksumValue": "942c5a758f98d2333389d7f09d82b1e8c35c2d0f"
        }
      ]
    }
  ],
  "relationships": [
    {
      "spdxElementId": "SPDXRef-DOCUMENT",
      "relationshipType": "DESCRIBES",
      "relatedSpdxElement": "SPDXRef-Package-MyProject"
    },
    {
      "spdxElementId": "SPDXRef-Package-MyProject",
      "relationshipType": "DEPENDS_ON",
      "relatedSpdxElement": "SPDXRef-Package-requests-2.31.0"
    }
  ]
}
```

#### CycloneDX 1.4 Format

```json
{
  "bomFormat": "CycloneDX",
  "specVersion": "1.4",
  "serialNumber": "urn:uuid:550e8400-e29b-41d4-a716-446655440000",
  "version": 1,
  "metadata": {
    "timestamp": "2025-12-03T10:30:00Z",
    "tools": [
      {
        "vendor": "devCrew_s1",
        "name": "SCA Scanner",
        "version": "1.0.0"
      }
    ],
    "component": {
      "type": "application",
      "name": "MyProject",
      "version": "1.0.0"
    }
  },
  "components": [
    {
      "type": "library",
      "bom-ref": "pkg:pypi/requests@2.31.0",
      "name": "requests",
      "version": "2.31.0",
      "purl": "pkg:pypi/requests@2.31.0",
      "licenses": [
        {
          "license": {
            "id": "Apache-2.0"
          }
        }
      ],
      "hashes": [
        {
          "alg": "SHA-256",
          "content": "942c5a758f98d2333389d7f09d82b1e8c35c2d0f"
        }
      ],
      "externalReferences": [
        {
          "type": "website",
          "url": "https://requests.readthedocs.io"
        },
        {
          "type": "vcs",
          "url": "https://github.com/psf/requests"
        }
      ]
    }
  ],
  "dependencies": [
    {
      "ref": "pkg:pypi/myproject@1.0.0",
      "dependsOn": [
        "pkg:pypi/requests@2.31.0"
      ]
    }
  ]
}
```

### SARIF Output

GitHub Code Scanning compatible SARIF format:

```json
{
  "$schema": "https://raw.githubusercontent.com/oasis-tcs/sarif-spec/master/Schemata/sarif-schema-2.1.0.json",
  "version": "2.1.0",
  "runs": [
    {
      "tool": {
        "driver": {
          "name": "DevCrew SCA Scanner",
          "version": "1.0.0",
          "informationUri": "https://github.com/devCrew_s1/sca-scanner",
          "rules": [
            {
              "id": "CVE-2023-32681",
              "name": "requests: Unintended Proxy Usage",
              "shortDescription": {
                "text": "CVE-2023-32681 in requests package"
              },
              "fullDescription": {
                "text": "Requests is vulnerable to unintended proxy usage which could lead to SSRF attacks."
              },
              "help": {
                "text": "Upgrade requests to version 2.31.0 or later."
              },
              "properties": {
                "security-severity": "7.5",
                "tags": ["security", "vulnerability", "cve"]
              }
            }
          ]
        }
      },
      "results": [
        {
          "ruleId": "CVE-2023-32681",
          "level": "error",
          "message": {
            "text": "Package 'requests' version 2.25.0 has a HIGH severity vulnerability (CVE-2023-32681)"
          },
          "locations": [
            {
              "physicalLocation": {
                "artifactLocation": {
                  "uri": "requirements.txt"
                },
                "region": {
                  "startLine": 15
                }
              }
            }
          ],
          "fixes": [
            {
              "description": {
                "text": "Upgrade to version 2.31.0"
              }
            }
          ]
        }
      ]
    }
  ]
}
```

### VEX Documents

OpenVEX format for vulnerability status communication:

```json
{
  "@context": "https://openvex.dev/ns",
  "@id": "https://devCrew_s1.example.com/vex/2025-001",
  "author": "DevCrew_s1 Security Team",
  "timestamp": "2025-12-03T10:30:00Z",
  "version": 1,
  "statements": [
    {
      "vulnerability": "CVE-2023-32681",
      "products": [
        {
          "@id": "pkg:pypi/requests@2.25.0"
        }
      ],
      "status": "not_affected",
      "justification": "vulnerable_code_not_in_execute_path",
      "impact_statement": "The vulnerable proxy functionality is not used in our application. All HTTP requests are made using explicit proxy configuration.",
      "action_statement": "No action required. We have verified that our usage patterns do not trigger the vulnerable code path."
    },
    {
      "vulnerability": "CVE-2023-45857",
      "products": [
        {
          "@id": "pkg:pypi/pillow@9.0.0"
        }
      ],
      "status": "fixed",
      "action_statement": "Upgraded to Pillow 10.1.0 which includes the fix for this vulnerability."
    },
    {
      "vulnerability": "CVE-2024-12345",
      "products": [
        {
          "@id": "pkg:npm/axios@0.21.0"
        }
      ],
      "status": "under_investigation",
      "action_statement": "Security team is currently investigating the impact of this vulnerability on our application. Expected resolution by 2025-12-15."
    }
  ]
}
```

## CI/CD Integration

### GitHub Actions

Add SCA scanning to your GitHub Actions workflow:

```yaml
name: Security Scan

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]
  schedule:
    # Run daily at 2 AM UTC
    - cron: '0 2 * * *'

jobs:
  sca-scan:
    name: Software Composition Analysis
    runs-on: ubuntu-latest

    permissions:
      contents: read
      security-events: write  # For SARIF upload

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'

      - name: Install SCA Scanner
        run: |
          pip install -r tools/sca_scanner/requirements.txt

      - name: Run vulnerability scan
        env:
          NVD_API_KEY: ${{ secrets.NVD_API_KEY }}
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: |
          python tools/sca_scanner/sca_cli.py scan \
            --manifest requirements.txt \
            --severity HIGH \
            --fail-on-severity CRITICAL \
            --output scan-results.json

      - name: Generate SARIF report
        if: always()
        run: |
          python tools/sca_scanner/sca_cli.py report \
            --manifest requirements.txt \
            --vulnerabilities \
            --format sarif \
            --output sca-results.sarif

      - name: Upload SARIF to GitHub Security
        if: always()
        uses: github/codeql-action/upload-sarif@v2
        with:
          sarif_file: sca-results.sarif

      - name: Upload scan results
        if: always()
        uses: actions/upload-artifact@v3
        with:
          name: sca-scan-results
          path: |
            scan-results.json
            sca-results.sarif

      - name: License compliance check
        run: |
          python tools/sca_scanner/sca_cli.py licenses \
            --manifest requirements.txt \
            --policy tools/sca_scanner/license-policy.yaml \
            --fail-on-violation

      - name: Generate SBOM
        run: |
          python tools/sca_scanner/sca_cli.py sbom \
            --manifest requirements.txt \
            --format spdx \
            --output sbom.spdx.json \
            --document-name "${{ github.repository }}-sbom" \
            --project-name "${{ github.repository }}"

      - name: Upload SBOM artifact
        uses: actions/upload-artifact@v3
        with:
          name: sbom
          path: sbom.spdx.json
```

### GitLab CI

Add to your `.gitlab-ci.yml`:

```yaml
stages:
  - security
  - report

variables:
  SCA_SCANNER_PATH: "tools/sca_scanner"

sca_scan:
  stage: security
  image: python:3.10

  before_script:
    - pip install -r $SCA_SCANNER_PATH/requirements.txt

  script:
    # Run vulnerability scan
    - |
      python $SCA_SCANNER_PATH/sca_cli.py scan \
        --manifest requirements.txt \
        --severity HIGH \
        --fail-on-severity CRITICAL \
        --output gl-sca-report.json

    # Generate GitLab security report format
    - |
      python $SCA_SCANNER_PATH/sca_cli.py report \
        --manifest requirements.txt \
        --vulnerabilities \
        --format gitlab \
        --output gl-dependency-scanning-report.json

    # License compliance
    - |
      python $SCA_SCANNER_PATH/sca_cli.py licenses \
        --manifest requirements.txt \
        --policy $SCA_SCANNER_PATH/license-policy.yaml \
        --output gl-license-scanning-report.json \
        --format gitlab

  artifacts:
    reports:
      dependency_scanning: gl-dependency-scanning-report.json
      license_scanning: gl-license-scanning-report.json
    paths:
      - gl-sca-report.json
    expire_in: 30 days

  allow_failure: false

  only:
    - branches
    - merge_requests

sbom_generation:
  stage: report
  image: python:3.10

  before_script:
    - pip install -r $SCA_SCANNER_PATH/requirements.txt

  script:
    - |
      python $SCA_SCANNER_PATH/sca_cli.py sbom \
        --manifest requirements.txt \
        --format spdx \
        --output sbom.spdx.json \
        --document-name "$CI_PROJECT_NAME-sbom" \
        --project-name "$CI_PROJECT_NAME"

    - |
      python $SCA_SCANNER_PATH/sca_cli.py sbom \
        --manifest requirements.txt \
        --format cyclonedx \
        --output sbom.cdx.json

  artifacts:
    paths:
      - sbom.spdx.json
      - sbom.cdx.json
    expire_in: 90 days

  only:
    - main
    - tags
```

### Jenkins

Add to your `Jenkinsfile`:

```groovy
pipeline {
    agent any

    environment {
        SCA_SCANNER_PATH = 'tools/sca_scanner'
        NVD_API_KEY = credentials('nvd-api-key')
        SEVERITY_THRESHOLD = 'HIGH'
    }

    stages {
        stage('Setup') {
            steps {
                sh '''
                    python3 -m venv venv
                    . venv/bin/activate
                    pip install -r ${SCA_SCANNER_PATH}/requirements.txt
                '''
            }
        }

        stage('Vulnerability Scan') {
            steps {
                sh '''
                    . venv/bin/activate
                    python ${SCA_SCANNER_PATH}/sca_cli.py scan \
                        --manifest requirements.txt \
                        --severity ${SEVERITY_THRESHOLD} \
                        --fail-on-severity CRITICAL \
                        --output scan-results.json
                '''
            }
        }

        stage('License Compliance') {
            steps {
                sh '''
                    . venv/bin/activate
                    python ${SCA_SCANNER_PATH}/sca_cli.py licenses \
                        --manifest requirements.txt \
                        --policy ${SCA_SCANNER_PATH}/license-policy.yaml \
                        --output license-report.json \
                        --fail-on-violation
                '''
            }
        }

        stage('Supply Chain Analysis') {
            steps {
                sh '''
                    . venv/bin/activate
                    python ${SCA_SCANNER_PATH}/sca_cli.py report \
                        --manifest requirements.txt \
                        --supply-chain \
                        --output supply-chain-report.json
                '''
            }
        }

        stage('Generate SBOM') {
            when {
                branch 'main'
            }
            steps {
                sh '''
                    . venv/bin/activate
                    python ${SCA_SCANNER_PATH}/sca_cli.py sbom \
                        --manifest requirements.txt \
                        --format spdx \
                        --output sbom.spdx.json \
                        --document-name "${JOB_NAME}-sbom" \
                        --project-name "${JOB_NAME}"
                '''
            }
        }

        stage('Generate Reports') {
            steps {
                sh '''
                    . venv/bin/activate
                    python ${SCA_SCANNER_PATH}/sca_cli.py report \
                        --manifest requirements.txt \
                        --vulnerabilities \
                        --licenses \
                        --supply-chain \
                        --format html \
                        --output security-dashboard.html
                '''
            }
        }
    }

    post {
        always {
            archiveArtifacts artifacts: '''
                scan-results.json,
                license-report.json,
                supply-chain-report.json,
                security-dashboard.html
            ''', allowEmptyArchive: true

            publishHTML([
                allowMissing: false,
                alwaysLinkToLastBuild: true,
                keepAll: true,
                reportDir: '.',
                reportFiles: 'security-dashboard.html',
                reportName: 'Security Dashboard'
            ])
        }

        success {
            echo 'SCA scan completed successfully'
        }

        failure {
            emailext (
                subject: "SCA Scan Failed: ${env.JOB_NAME} - ${env.BUILD_NUMBER}",
                body: """
                    The SCA scan has detected critical vulnerabilities or policy violations.

                    Job: ${env.JOB_NAME}
                    Build: ${env.BUILD_NUMBER}
                    URL: ${env.BUILD_URL}

                    Please review the scan results and take appropriate action.
                """,
                to: 'security@devCrew_s1.example.com'
            )
        }
    }
}
```

## Python API

### Basic Usage

```python
from pathlib import Path
from tools.sca_scanner import DependencyScanner, VulnerabilityMatcher

# Initialize scanner
scanner = DependencyScanner(scan_path="requirements.txt")

# Scan for dependencies
dependencies = scanner.scan()

print(f"Found {len(dependencies)} dependencies")

# Get direct dependencies only
direct_deps = scanner.get_direct_dependencies(dependencies)
print(f"Direct dependencies: {len(direct_deps)}")

# Export to JSON
scanner.export_to_json(dependencies, "dependencies.json")
```

### Vulnerability Scanning

```python
from tools.sca_scanner import VulnerabilityMatcher, DependencyScanner

# Configure vulnerability matcher
config = {
    "databases": ["nvd", "osv", "github"],
    "cache_ttl": 86400,
    "api_keys": {
        "nvd": "your-nvd-api-key",
        "github": "your-github-token"
    }
}

matcher = VulnerabilityMatcher(config=config)

# Scan dependencies
scanner = DependencyScanner("requirements.txt")
dependencies = scanner.scan()

# Convert to required format
dep_list = [
    {
        "package": dep.name,
        "version": dep.version,
        "ecosystem": dep.ecosystem.value
    }
    for dep in dependencies
]

# Find vulnerabilities
vulnerabilities = matcher.find_vulnerabilities(dep_list)

# Filter by severity
high_severity = [
    v for v in vulnerabilities
    if v.get("severity") in ["HIGH", "CRITICAL"]
]

print(f"Found {len(high_severity)} high/critical vulnerabilities")
```

### License Checking

```python
from tools.sca_scanner import LicenseChecker, DependencyScanner

# Initialize license checker
checker = LicenseChecker()

# Load policy from file
with open("license-policy.yaml") as f:
    import yaml
    policy = yaml.safe_load(f)

checker.set_policy(policy)

# Scan dependencies
scanner = DependencyScanner("requirements.txt")
dependencies = scanner.scan()

# Check licenses
results = []
for dep in dependencies:
    license_info = checker.check_package(
        package=dep.name,
        version=dep.version,
        ecosystem=dep.ecosystem.value
    )
    results.append(license_info)

# Find violations
violations = [r for r in results if r.policy_violation]
print(f"Found {len(violations)} license policy violations")

# Generate compliance report
report = checker.generate_compliance_report(results)
```

### SBOM Generation

```python
from tools.sca_scanner import SBOMGenerator, DependencyScanner

# Initialize SBOM generator
generator = SBOMGenerator()

# Scan dependencies
scanner = DependencyScanner("requirements.txt")
dependencies = scanner.scan()

# Convert to SBOM format
dep_list = [dep.to_dict() for dep in dependencies]

# SBOM metadata
metadata = {
    "document_name": "MyProject-SBOM",
    "project_name": "MyProject",
    "creator": "DevCrew SCA Scanner",
    "supplier": "Organization: devCrew_s1"
}

# Generate SPDX SBOM
spdx_json = generator.generate(
    dependencies=dep_list,
    metadata=metadata,
    format="spdx",
    output_format="json"
)

# Save to file
Path("sbom.spdx.json").write_text(spdx_json)

# Generate CycloneDX SBOM
cdx_json = generator.generate(
    dependencies=dep_list,
    metadata=metadata,
    format="cyclonedx",
    output_format="json"
)

Path("sbom.cdx.json").write_text(cdx_json)
```

### Complete Analysis

```python
from tools.sca_scanner import (
    DependencyScanner,
    VulnerabilityMatcher,
    LicenseChecker,
    RemediationAdvisor,
    SupplyChainAnalyzer
)

def comprehensive_scan(manifest_path: str) -> dict:
    """Perform comprehensive security analysis."""

    # 1. Scan dependencies
    scanner = DependencyScanner(manifest_path)
    dependencies = scanner.scan()
    dep_list = [dep.to_dict() for dep in dependencies]

    print(f"Scanned {len(dependencies)} dependencies")

    # 2. Find vulnerabilities
    vuln_matcher = VulnerabilityMatcher()
    vulnerabilities = vuln_matcher.find_vulnerabilities([
        {
            "package": d["name"],
            "version": d["version"],
            "ecosystem": d["ecosystem"]
        }
        for d in dep_list
    ])

    print(f"Found {len(vulnerabilities)} vulnerabilities")

    # 3. Check licenses
    license_checker = LicenseChecker()
    license_results = []
    for dep in dependencies:
        info = license_checker.check_package(
            dep.name, dep.version, dep.ecosystem.value
        )
        license_results.append(info)

    # 4. Analyze supply chain
    sc_analyzer = SupplyChainAnalyzer()
    supply_chain = sc_analyzer.analyze([
        {
            "name": d["name"],
            "version": d["version"],
            "ecosystem": d["ecosystem"]
        }
        for d in dep_list
    ])

    # 5. Get remediation advice
    advisor = RemediationAdvisor()
    remediations = []
    for vuln in vulnerabilities:
        remediation = advisor.get_remediation(
            package=vuln["package"],
            current_version=vuln["version"],
            vulnerability=vuln
        )
        remediations.append(remediation)

    # Compile results
    return {
        "dependencies": dep_list,
        "vulnerabilities": vulnerabilities,
        "licenses": [r.__dict__ for r in license_results],
        "supply_chain": supply_chain,
        "remediations": [r.__dict__ for r in remediations],
        "summary": {
            "total_dependencies": len(dependencies),
            "vulnerabilities_found": len(vulnerabilities),
            "license_violations": sum(
                1 for r in license_results if r.policy_violation
            ),
            "supply_chain_risks": sum(
                1 for s in supply_chain
                if s.get("risk_level") in ["high", "critical"]
            )
        }
    }

# Run comprehensive scan
results = comprehensive_scan("requirements.txt")

# Save results
import json
Path("comprehensive-scan.json").write_text(
    json.dumps(results, indent=2, default=str)
)
```

## Protocol Support

### SCM-SBOM

The SCA Scanner implements comprehensive SBOM generation following industry standards:

**SPDX 2.3 Support:**
- Full SPDX document structure with relationships
- Package metadata including licenses, checksums, external references
- SPDX ID assignment for all components
- Dependency relationship mapping (DESCRIBES, DEPENDS_ON, CONTAINS)
- License expression support (AND, OR operators)
- Package URL (PURL) integration

**CycloneDX 1.4 Support:**
- BOM metadata with tool and component information
- Component relationships and dependencies
- License information (SPDX IDs and expressions)
- External references (website, VCS, documentation)
- Hash generation (SHA-256, SHA-1, MD5)
- Service component support

**Usage Example:**

```python
from tools.sca_scanner import SBOMGenerator, DependencyScanner

scanner = DependencyScanner("requirements.txt")
dependencies = scanner.scan()

generator = SBOMGenerator()
metadata = {
    "document_name": "devCrew_s1-SBOM",
    "project_name": "devCrew_s1",
    "document_namespace": "https://devCrew_s1.example.com/sboms/2025/001"
}

# Generate SPDX SBOM
spdx_sbom = generator.generate(
    [d.to_dict() for d in dependencies],
    metadata,
    format="spdx",
    output_format="json"
)

# Validate against schema
generator.validate_sbom(spdx_sbom, "spdx")
```

### SCM-SLSA

Supply chain provenance and SLSA (Supply-chain Levels for Software Artifacts) support:

**Features:**
- Package integrity verification via checksums
- Build provenance metadata generation
- Dependency resolution transparency
- Tamper detection through hash validation
- Reproducible build support

**SLSA Level Support:**
- **Level 1**: Documentation of build process, SBOM generation
- **Level 2**: Version control integration, build service attestation
- **Level 3**: Enhanced provenance, non-falsifiable audit log

**Usage Example:**

```python
from tools.sca_scanner import SupplyChainAnalyzer

analyzer = SupplyChainAnalyzer()

# Analyze with SLSA provenance
results = analyzer.analyze([
    {"name": "requests", "version": "2.31.0", "ecosystem": "python"}
])

for result in results:
    print(f"Package: {result['package']}")
    print(f"Integrity: {result['integrity_verified']}")
    print(f"Provenance: {result.get('provenance', {})}")
    print(f"SLSA Level: {result.get('slsa_level', 'N/A')}")
```

### SCM-VEX

Vulnerability Exploitability eXchange (VEX) document generation following OpenVEX specification:

**VEX Statement Types:**
- `not_affected`: Vulnerability exists but doesn't affect the product
- `affected`: Product is affected by the vulnerability
- `fixed`: Vulnerability has been remediated
- `under_investigation`: Impact assessment in progress

**Justification Categories:**
- `component_not_present`: Vulnerable component not included
- `vulnerable_code_not_present`: Vulnerable code removed
- `vulnerable_code_not_in_execute_path`: Code exists but not executed
- `vulnerable_code_cannot_be_controlled_by_adversary`: Cannot be exploited
- `inline_mitigations_already_exist`: Mitigations in place

**Usage Example:**

```python
from tools.sca_scanner import VEXGenerator, VulnerabilityMatcher

# Find vulnerabilities
matcher = VulnerabilityMatcher()
vulnerabilities = matcher.find_vulnerabilities(dependencies)

# Generate VEX document
vex_gen = VEXGenerator()
vex_document = vex_gen.generate(
    vulnerabilities=vulnerabilities,
    statements=[
        {
            "vulnerability": "CVE-2023-32681",
            "products": ["pkg:pypi/requests@2.25.0"],
            "status": "not_affected",
            "justification": "vulnerable_code_not_in_execute_path",
            "impact_statement": "Proxy functionality not used",
            "action_statement": "No action required"
        }
    ],
    metadata={
        "author": "devCrew_s1 Security Team",
        "id": "https://devCrew_s1.example.com/vex/2025-001"
    }
)

# Export VEX document
Path("security.vex.json").write_text(
    json.dumps(vex_document, indent=2)
)
```

## Architecture

The SCA Scanner is built with a modular architecture consisting of 7 core modules:

### 1. DependencyScanner (`dependency_scanner.py`)

**Purpose**: Multi-language dependency detection and parsing

**Responsibilities:**
- Manifest file auto-detection (requirements.txt, package.json, pom.xml, etc.)
- Dependency parsing for Python, Node.js, Java, Go, Ruby, and Rust
- Transitive dependency resolution
- Dependency tree construction
- Lockfile analysis

**Key Classes:**
- `DependencyScanner`: Main scanner class
- `Dependency`: Data model for dependency information
- `Ecosystem`: Enum for supported package ecosystems

### 2. VulnerabilityMatcher (`vulnerability_matcher.py`)

**Purpose**: CVE lookup and severity scoring

**Responsibilities:**
- NVD API integration with rate limiting
- OSV database queries
- GitHub Advisory Database access
- CVSS 3.1 severity scoring
- Local caching for offline operation
- Batch processing for performance

**Key Features:**
- Connection pooling
- TTL-based caching
- Multiple database aggregation
- Version range matching

### 3. LicenseChecker (`license_checker.py`)

**Purpose**: License compliance validation

**Responsibilities:**
- SPDX license identifier detection
- License policy enforcement
- Copyleft detection (GPL, AGPL, LGPL)
- OSI-approved license validation
- License compatibility analysis
- Multi-license expression parsing

**Key Classes:**
- `LicenseChecker`: Main checker class
- `LicenseInfo`: License metadata model
- `PolicyStatus`: Compliance status enum
- `LicenseCategory`: License categorization

### 4. SBOMGenerator (`sbom_generator.py`)

**Purpose**: Generate SBOM in multiple formats

**Responsibilities:**
- SPDX 2.3 document generation
- CycloneDX 1.4 document generation
- JSON and XML serialization
- Schema validation
- Package hash generation (SHA-256)
- PURL generation

**Key Features:**
- Format abstraction layer
- Validation engine
- Relationship mapping
- External reference generation

### 5. RemediationAdvisor (`remediation_advisor.py`)

**Purpose**: Upgrade recommendations and remediation guidance

**Responsibilities:**
- Upgrade path calculation
- Breaking change detection
- Semantic versioning analysis
- Alternative package suggestions
- Priority scoring
- Migration effort estimation

**Key Classes:**
- `RemediationAdvisor`: Main advisor class
- `Remediation`: Remediation recommendation model
- `UpgradeType`: Version upgrade classification
- `Alternative`: Alternative package suggestion

### 6. SupplyChainAnalyzer (`supply_chain_analyzer.py`)

**Purpose**: Supply chain security analysis

**Responsibilities:**
- Package integrity verification
- Dependency confusion detection
- Typosquatting analysis
- Malicious pattern detection
- Package health scoring
- Maintainer trust analysis

**Key Features:**
- Edit distance calculation for typosquatting
- Pattern matching for malicious code
- Metadata analysis (downloads, releases, age)
- Risk scoring algorithms

### 7. CLI Interface (`sca_cli.py`)

**Purpose**: Command-line interface

**Commands:**
- `scan`: Vulnerability scanning
- `sbom`: SBOM generation
- `licenses`: License compliance checking
- `vex`: VEX document generation
- `report`: Comprehensive reporting

**Key Features:**
- Rich terminal output with colors
- Progress indicators
- Table formatting
- JSON/SARIF/HTML output
- Configuration file support

## Troubleshooting

### Common Issues and Solutions

#### Network Connectivity

**Issue**: API requests timing out or failing

```
Error: Connection timeout when querying NVD API
```

**Solutions:**

1. Check internet connectivity:
```bash
curl -I https://services.nvd.nist.gov
```

2. Configure proxy if behind corporate firewall:
```bash
export HTTP_PROXY=http://proxy.company.com:8080
export HTTPS_PROXY=http://proxy.company.com:8080
```

3. Increase timeout in configuration:
```yaml
api:
  timeout: 30  # Increase from default 10 seconds
```

4. Use cached results:
```bash
python sca_cli.py scan --manifest requirements.txt --cache-ttl 86400
```

#### API Rate Limiting

**Issue**: Rate limit exceeded errors

```
Error: Rate limit exceeded for NVD API (429)
```

**Solutions:**

1. Obtain API key for higher limits:
   - NVD: https://nvd.nist.gov/developers/request-an-api-key
   - GitHub: https://github.com/settings/tokens

2. Configure API keys:
```bash
export NVD_API_KEY=your-api-key
export GITHUB_TOKEN=your-github-token
```

3. Reduce concurrent requests:
```yaml
api:
  rate_limit:
    requests_per_minute: 20  # Reduce from default 30
```

4. Use local caching:
```bash
python sca_cli.py scan --manifest requirements.txt --cache-ttl 604800  # 7 days
```

#### Missing Dependencies

**Issue**: Import errors when running scanner

```
ModuleNotFoundError: No module named 'license_expression'
```

**Solutions:**

1. Reinstall dependencies:
```bash
pip install --force-reinstall -r requirements.txt
```

2. Check Python version:
```bash
python --version  # Must be 3.10+
```

3. Use virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

4. Install missing package individually:
```bash
pip install license-expression
```

#### Permission Errors

**Issue**: Cannot write output files

```
PermissionError: [Errno 13] Permission denied: 'sbom.json'
```

**Solutions:**

1. Check file permissions:
```bash
ls -la sbom.json
```

2. Remove write-protected file:
```bash
chmod +w sbom.json
```

3. Write to different location:
```bash
python sca_cli.py sbom --manifest requirements.txt --output ~/reports/sbom.json
```

4. Run with appropriate permissions:
```bash
sudo python sca_cli.py sbom ...  # Use with caution
```

#### Manifest Parsing Errors

**Issue**: Failed to parse manifest file

```
ManifestParseError: Failed to parse requirements.txt: Invalid requirement line
```

**Solutions:**

1. Validate manifest syntax:
```bash
# Python
pip check

# Node.js
npm install --dry-run

# Go
go mod verify
```

2. Check for unsupported features:
   - Remove VCS URLs: `git+https://...`
   - Remove local paths: `file:///...`
   - Use pinned versions: `package==1.2.3` instead of `package>=1.2.3`

3. Generate clean manifest:
```bash
# Python
pip freeze > requirements-clean.txt

# Node.js
npm list --json > package-list.json
```

#### Memory Issues

**Issue**: Scanner runs out of memory with large projects

```
MemoryError: Unable to allocate array
```

**Solutions:**

1. Scan by ecosystem:
```bash
# Scan Python dependencies only
python sca_cli.py scan --manifest requirements.txt --output python-scan.json

# Scan Node.js dependencies separately
python sca_cli.py scan --manifest package.json --output node-scan.json
```

2. Disable caching:
```bash
python sca_cli.py scan --manifest requirements.txt --no-cache
```

3. Increase Python memory limit:
```bash
# Linux/Mac
ulimit -v unlimited
python sca_cli.py scan ...

# Or use
python -X dev sca_cli.py scan ...
```

#### False Positives

**Issue**: Scanner reports vulnerabilities in unused code paths

**Solutions:**

1. Generate VEX document to document false positives:
```bash
python sca_cli.py vex \
  --manifest requirements.txt \
  --output false-positives.vex.json \
  --status not_affected \
  --justification "vulnerable_code_not_in_execute_path"
```

2. Configure ignored vulnerabilities:
```yaml
# sca-config.yaml
vulnerability_scanning:
  ignored_vulnerabilities:
    - cve: CVE-2023-12345
      reason: "Not applicable - vulnerability in test dependencies"
      expires: "2025-12-31"
```

3. Use supply chain analysis to verify:
```bash
python sca_cli.py report \
  --manifest requirements.txt \
  --supply-chain \
  --output detailed-analysis.json
```

### Debug Mode

Enable debug logging for troubleshooting:

```bash
export SCA_DEBUG=1
python sca_cli.py scan --manifest requirements.txt
```

Or in Python:

```python
import logging
logging.basicConfig(level=logging.DEBUG)

from tools.sca_scanner import DependencyScanner
scanner = DependencyScanner("requirements.txt")
```

## Contributing

We welcome contributions to the SCA Scanner! This tool is part of the devCrew_s1 project.

### Development Setup

1. Clone the repository:
```bash
git clone https://github.com/devCrew_s1/devCrew_s1.git
cd devCrew_s1/tools/sca_scanner
```

2. Create virtual environment:
```bash
python -m venv venv
source venv/bin/activate
```

3. Install development dependencies:
```bash
pip install -r requirements.txt
pip install -r requirements-dev.txt  # Testing tools
```

4. Run pre-commit hooks:
```bash
pre-commit install
pre-commit run --all-files
```

### Code Quality Standards

All contributions must pass:

- **Black**: Code formatting
- **isort**: Import sorting
- **Flake8**: Style guide enforcement (max line length: 88)
- **Pylint**: Static code analysis
- **Mypy**: Type checking with `--ignore-missing-imports`
- **Bandit**: Security analysis

Run quality checks:

```bash
# Format code
black .
isort .

# Check style
flake8 --max-line-length=88

# Type checking
mypy . --ignore-missing-imports

# Security scan
bandit -r . -ll
```

### Testing

Write tests for all new features:

```bash
# Run all tests
pytest -v

# Run specific test file
pytest tests/test_dependency_scanner.py -v

# Run with coverage
pytest --cov=. --cov-report=html
```

### Submitting Changes

1. Create a feature branch:
```bash
git checkout -b feature/your-feature-name
```

2. Make changes and commit:
```bash
git add .
git commit -m "feat: add new feature description"
```

3. Push and create pull request:
```bash
git push origin feature/your-feature-name
```

4. Ensure all CI checks pass

### Commit Message Format

Follow conventional commits:

- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation changes
- `test:` Test additions or changes
- `refactor:` Code refactoring
- `perf:` Performance improvements
- `chore:` Maintenance tasks

## License

This project is licensed under the Apache License 2.0. See the LICENSE file in the devCrew_s1 repository for details.

```
Copyright (c) 2025 devCrew_s1

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
```

## References

### Standards and Specifications

- **NVD API**: [https://nvd.nist.gov/developers](https://nvd.nist.gov/developers)
- **OSV**: [https://osv.dev](https://osv.dev)
- **GitHub Advisory Database**: [https://github.com/advisories](https://github.com/advisories)
- **SPDX**: [https://spdx.dev](https://spdx.dev)
- **CycloneDX**: [https://cyclonedx.org](https://cyclonedx.org)
- **SLSA**: [https://slsa.dev](https://slsa.dev)
- **OpenVEX**: [https://openvex.dev](https://openvex.dev)
- **Package URL (PURL)**: [https://github.com/package-url/purl-spec](https://github.com/package-url/purl-spec)
- **CVSS**: [https://www.first.org/cvss/](https://www.first.org/cvss/)

### Documentation

- **SPDX 2.3 Specification**: [https://spdx.github.io/spdx-spec/v2.3/](https://spdx.github.io/spdx-spec/v2.3/)
- **CycloneDX 1.4 Specification**: [https://cyclonedx.org/docs/1.4/](https://cyclonedx.org/docs/1.4/)
- **SARIF 2.1.0**: [https://docs.oasis-open.org/sarif/sarif/v2.1.0/sarif-v2.1.0.html](https://docs.oasis-open.org/sarif/sarif/v2.1.0/sarif-v2.1.0.html)
- **OpenVEX Specification**: [https://github.com/openvex/spec](https://github.com/openvex/spec)

### Tools and Libraries

- **Python Packaging**: [https://packaging.python.org](https://packaging.python.org)
- **SPDX Tools**: [https://github.com/spdx/tools-python](https://github.com/spdx/tools-python)
- **CycloneDX Python Library**: [https://github.com/CycloneDX/cyclonedx-python-lib](https://github.com/CycloneDX/cyclonedx-python-lib)
- **License Expression**: [https://github.com/nexB/license-expression](https://github.com/nexB/license-expression)

### Community

- **devCrew_s1 Repository**: [https://github.com/devCrew_s1/devCrew_s1](https://github.com/devCrew_s1/devCrew_s1)
- **Issue Tracker**: [https://github.com/devCrew_s1/devCrew_s1/issues](https://github.com/devCrew_s1/devCrew_s1/issues)
- **Contributing Guide**: [https://github.com/devCrew_s1/devCrew_s1/blob/main/CONTRIBUTING.md](https://github.com/devCrew_s1/devCrew_s1/blob/main/CONTRIBUTING.md)

---

**Built with ❤️ by the devCrew_s1 team**

For questions or support, please open an issue in the [GitHub repository](https://github.com/devCrew_s1/devCrew_s1).
