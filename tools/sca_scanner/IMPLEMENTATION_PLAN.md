# SCA Scanner Implementation Plan

## Overview
Software Composition Analysis Scanner for devCrew_s1 repository (Issue #55)

## Module Architecture

### 1. DependencyScanner (`dependency_scanner.py`)
**Purpose**: Multi-language dependency detection and parsing
**Key Features**:
- Manifest file detection (requirements.txt, package.json, pom.xml, go.mod, Gemfile, Cargo.toml)
- Dependency tree resolution
- Transitive dependency analysis
- Lockfile parsing

**Dependencies**:
- Python stdlib (pathlib, json, re, subprocess)
- packaging (for version parsing)
- tomli (for TOML parsing)

### 2. VulnerabilityMatcher (`vulnerability_matcher.py`)
**Purpose**: CVE lookup and severity scoring
**Key Features**:
- NVD API integration
- OSV database integration
- GitHub Advisory Database queries
- Local caching for offline operation
- CVSS 3.1 scoring

**Dependencies**:
- requests (HTTP client)
- cachetools (local caching)
- packaging (version comparison)

### 3. LicenseChecker (`license_checker.py`)
**Purpose**: License compliance validation
**Key Features**:
- SPDX license identifier detection
- License policy engine
- Compatibility analysis
- Copyleft detection

**Dependencies**:
- license-expression (SPDX parsing)
- requests (metadata lookup)

### 4. SBOMGenerator (`sbom_generator.py`)
**Purpose**: Generate SBOM in multiple formats
**Key Features**:
- SPDX 2.3 generation
- CycloneDX 1.4 generation
- SBOM validation
- Hash generation (SHA256)

**Dependencies**:
- spdx-tools (SPDX library)
- cyclonedx-python-lib (CycloneDX library)
- jsonschema (validation)

### 5. RemediationAdvisor (`remediation_advisor.py`)
**Purpose**: Upgrade recommendations
**Key Features**:
- Upgrade path calculation
- Breaking change detection
- Alternative package suggestions
- Semantic versioning analysis

**Dependencies**:
- packaging (version parsing)
- semver (semantic versioning)

### 6. SupplyChainAnalyzer (`supply_chain_analyzer.py`)
**Purpose**: Supply chain security analysis
**Key Features**:
- SLSA provenance verification
- Package tampering detection
- Dependency confusion detection
- Malicious package indicators

**Dependencies**:
- requests
- hashlib (built-in)

### 7. CLI Interface (`sca_cli.py`)
**Purpose**: Command-line interface
**Commands**:
- scan: Vulnerability scan
- sbom: Generate SBOM
- licenses: License compliance check
- vex: Generate VEX document
- report: Comprehensive report

**Dependencies**:
- click (CLI framework)
- rich (terminal formatting)
- tabulate (table formatting)

## Implementation Guidelines

### Code Quality
- Type hints for all functions
- Docstrings (Google style)
- Error handling with custom exceptions
- Logging with structured output
- 90%+ test coverage

### Security
- No hardcoded credentials
- Input validation
- Safe subprocess execution
- Secure temporary file handling

### Performance
- Async I/O for API calls
- Connection pooling
- Request batching
- Local caching

## Testing Strategy

### Unit Tests (`test_sca_scanner.py`)
- Mock external APIs
- Test error conditions
- Edge cases (empty files, malformed data)
- Performance benchmarks

### Integration Tests
- Real API calls (with rate limiting)
- End-to-end workflows
- Multi-language projects

## Configuration Files

### `sca-config.yaml`
```yaml
severity_threshold: HIGH
ignored_vulnerabilities:
  - CVE-2023-xxxxx
vuln_databases:
  - nvd
  - osv
  - github
cache_ttl: 86400
```

### `license-policy.yaml`
```yaml
allowed_licenses:
  - MIT
  - Apache-2.0
  - BSD-3-Clause
denied_licenses:
  - GPL-3.0
  - AGPL-3.0
```

## Output Formats

### JSON Report
```json
{
  "scan_id": "uuid",
  "timestamp": "ISO8601",
  "summary": {
    "total_dependencies": 100,
    "vulnerabilities": {
      "critical": 0,
      "high": 2,
      "medium": 5,
      "low": 10
    }
  },
  "findings": []
}
```

### SARIF Output (for CI/CD)
- GitHub Code Scanning compatible
- GitLab Security Dashboard compatible

## Documentation Structure

### README.md
- Overview
- Installation
- Quick start
- Configuration
- Examples

### User Guide
- Detailed usage
- All commands
- Configuration options
- Troubleshooting

### API Documentation
- Python API reference
- Integration examples
