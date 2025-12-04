# VEX Documentation Guide

Comprehensive guide for generating and managing Vulnerability Exploitability eXchange (VEX) documents.

## Table of Contents

- [Overview](#overview)
- [VEX Formats](#vex-formats)
- [Creating VEX Documents](#creating-vex-documents)
- [Status Values](#status-values)
- [Justifications](#justifications)
- [VEX Chaining](#vex-chaining)
- [Best Practices](#best-practices)

## Overview

VEX (Vulnerability Exploitability eXchange) documents communicate the exploitability status of vulnerabilities in software products. They help downstream consumers understand which CVEs affect their specific deployment.

### Why Use VEX?

- **Reduce Alert Fatigue**: Clarify which vulnerabilities are not applicable
- **Improve Risk Assessment**: Provide context on exploitability
- **Track Remediation**: Document fixes and mitigations
- **Compliance**: Meet security disclosure requirements
- **Supply Chain Security**: Share vulnerability status with customers

### VEX Use Cases

1. **Software Vendors**: Communicate vulnerability status to customers
2. **DevOps Teams**: Track vulnerability remediation progress
3. **Security Teams**: Document risk acceptance decisions
4. **Compliance**: Meet SBOM + VEX requirements (EO 14028)

## VEX Formats

The platform supports two VEX formats:

### OpenVEX

OpenVEX is a community-driven, minimal VEX implementation.

**Pros:**
- Simple and lightweight
- Easy to implement
- JSON-based
- Good for automation

**Cons:**
- Less detailed than CSAF
- Newer format (less tooling)

### CSAF 2.0

Common Security Advisory Framework 2.0 is a comprehensive advisory format.

**Pros:**
- Comprehensive and detailed
- Industry standard
- Rich metadata support
- Extensive tooling

**Cons:**
- More complex
- Larger file sizes
- Steeper learning curve

## Creating VEX Documents

### Using CLI

#### Generate OpenVEX Document

```bash
# Basic VEX document
python -m cli.threat_cli vex \
  --product "myapp:2.1.0" \
  --format openvex \
  --output vex_document.json

# From vulnerability list
python -m cli.threat_cli vex \
  --product "myapp:2.1.0" \
  --vulnerabilities vuln_list.json \
  --format openvex \
  --output vex_document.json

# From SBOM
python -m cli.threat_cli vex \
  --product "myapp:2.1.0" \
  --sbom sbom.json \
  --sbom-format cyclonedx \
  --format openvex \
  --output vex_document.json
```

#### Generate CSAF Document

```bash
# CSAF 2.0 advisory
python -m cli.threat_cli vex \
  --product "myapp:2.1.0" \
  --vulnerabilities vuln_list.json \
  --format csaf \
  --output csaf_advisory.json

# With metadata
python -m cli.threat_cli vex \
  --product "myapp:2.1.0" \
  --vendor "ACME Corp" \
  --vulnerabilities vuln_list.json \
  --format csaf \
  --title "Security Advisory for MyApp 2.1.0" \
  --output csaf_advisory.json
```

### Using Python API

#### OpenVEX Example

```python
from vex.vex_generator import VEXGenerator
from datetime import datetime

# Initialize generator
vex_gen = VEXGenerator(format="openvex")

# Create VEX document
vex_doc = vex_gen.create_document(
    document_id="vex-myapp-2.1.0-20241204",
    product_id="pkg:npm/myapp@2.1.0",
    product_name="MyApp",
    version="2.1.0",
    vendor="ACME Corp",
    release_date=datetime.now()
)

# Add vulnerability statements
vex_doc.add_vulnerability(
    cve_id="CVE-2024-1234",
    status="not_affected",
    justification="vulnerable_code_not_present",
    impact_statement="The vulnerable function is not included in our build"
)

vex_doc.add_vulnerability(
    cve_id="CVE-2024-5678",
    status="affected",
    action_statement="Update to version 2.1.1 which includes the fix",
    action_statement_timestamp=datetime.now()
)

vex_doc.add_vulnerability(
    cve_id="CVE-2024-9999",
    status="fixed",
    action_statement="Fixed in this release",
    action_statement_timestamp=datetime(2024, 12, 1)
)

# Save document
vex_doc.save("myapp_vex.json")
print(f"VEX document created: {vex_doc.document_id}")
```

#### CSAF Example

```python
from vex.vex_generator import VEXGenerator
from datetime import datetime

# Initialize CSAF generator
vex_gen = VEXGenerator(format="csaf")

# Create CSAF document
csaf_doc = vex_gen.create_document(
    document_id="ACME-SA-2024-001",
    title="Security Advisory for MyApp 2.1.0",
    publisher={
        "name": "ACME Corp Security Team",
        "category": "vendor",
        "namespace": "https://acme.example.com"
    },
    tracking={
        "current_release_date": datetime.now(),
        "id": "ACME-SA-2024-001",
        "initial_release_date": datetime(2024, 12, 1),
        "revision_history": [
            {
                "number": "1.0",
                "date": datetime(2024, 12, 1),
                "summary": "Initial release"
            }
        ],
        "status": "final",
        "version": "1.0"
    }
)

# Add product tree
csaf_doc.add_product(
    product_id="CSAFPID-0001",
    name="MyApp",
    version="2.1.0",
    cpe="cpe:2.3:a:acme:myapp:2.1.0:*:*:*:*:*:*:*"
)

# Add vulnerabilities
csaf_doc.add_vulnerability(
    cve_id="CVE-2024-1234",
    title="SQL Injection in User Authentication",
    product_ids=["CSAFPID-0001"],
    scores=[
        {
            "cvss_v3": {
                "version": "3.1",
                "vectorString": "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H",
                "baseScore": 9.8,
                "baseSeverity": "CRITICAL"
            }
        }
    ],
    threat_status="not_affected",
    threat_details="The authentication module uses parameterized queries, making SQL injection impossible.",
    remediations=[
        {
            "category": "vendor_fix",
            "details": "Not affected - secure coding practices in place"
        }
    ]
)

# Save CSAF document
csaf_doc.save("myapp_csaf.json")
```

## Status Values

VEX documents use four status values to describe vulnerability exploitability:

### not_affected

The product is not affected by the vulnerability.

**When to Use:**
- Vulnerable code is not present
- Vulnerable code is present but not executed
- Vulnerability cannot be exploited in this context
- Compensating controls prevent exploitation

**Example:**

```python
vex_doc.add_vulnerability(
    cve_id="CVE-2024-1234",
    status="not_affected",
    justification="vulnerable_code_not_present",
    impact_statement="We use a different implementation that doesn't contain the vulnerable code path"
)
```

### affected

The product is affected and vulnerable.

**When to Use:**
- Vulnerability is present and exploitable
- No fix available yet
- Fix available but not yet applied

**Example:**

```python
vex_doc.add_vulnerability(
    cve_id="CVE-2024-5678",
    status="affected",
    action_statement="Upgrade to version 2.2.0 or apply hotfix available at https://example.com/hotfix",
    action_statement_timestamp=datetime.now()
)
```

### fixed

The vulnerability has been remediated.

**When to Use:**
- Patch has been applied
- Vulnerable code has been removed
- Vulnerability fixed in this version

**Example:**

```python
vex_doc.add_vulnerability(
    cve_id="CVE-2024-9999",
    status="fixed",
    action_statement="Fixed in version 2.1.0",
    action_statement_timestamp=datetime(2024, 12, 1)
)
```

### under_investigation

Still analyzing the vulnerability's impact.

**When to Use:**
- New CVE just published
- Impact analysis in progress
- Waiting for vendor information

**Example:**

```python
vex_doc.add_vulnerability(
    cve_id="CVE-2024-NEW",
    status="under_investigation",
    action_statement="Impact assessment in progress. Expected completion: 2024-12-10",
    action_statement_timestamp=datetime.now()
)
```

## Justifications

When status is "not_affected", provide a justification explaining why.

### vulnerable_code_not_present

The vulnerable code is not in the product.

```python
vex_doc.add_vulnerability(
    cve_id="CVE-2024-1234",
    status="not_affected",
    justification="vulnerable_code_not_present",
    impact_statement="Our build excludes the affected module entirely"
)
```

### vulnerable_code_not_in_execute_path

Code is present but never executed.

```python
vex_doc.add_vulnerability(
    cve_id="CVE-2024-1234",
    status="not_affected",
    justification="vulnerable_code_not_in_execute_path",
    impact_statement="The vulnerable function exists but is disabled by configuration and cannot be reached"
)
```

### vulnerable_code_cannot_be_controlled_by_adversary

Code runs but attacker cannot control it.

```python
vex_doc.add_vulnerability(
    cve_id="CVE-2024-1234",
    status="not_affected",
    justification="vulnerable_code_cannot_be_controlled_by_adversary",
    impact_statement="Input is sanitized and validated before reaching the vulnerable code, preventing exploitation"
)
```

### inline_mitigations_already_exist

Product includes protections against exploitation.

```python
vex_doc.add_vulnerability(
    cve_id="CVE-2024-1234",
    status="not_affected",
    justification="inline_mitigations_already_exist",
    impact_statement="Our WAF rules and input validation prevent exploitation of this vulnerability"
)
```

### component_not_present

The vulnerable component is not included.

```python
vex_doc.add_vulnerability(
    cve_id="CVE-2024-1234",
    status="not_affected",
    justification="component_not_present",
    impact_statement="This vulnerability affects the optional analytics module which we don't use"
)
```

## VEX Chaining

VEX documents can be chained to provide updates and corrections.

### Creating VEX Chains

```python
# Original VEX document
vex_v1 = vex_gen.create_document(
    document_id="vex-myapp-2.1.0-v1",
    product_id="pkg:npm/myapp@2.1.0",
    version="2.1.0"
)

vex_v1.add_vulnerability(
    cve_id="CVE-2024-1234",
    status="under_investigation"
)

vex_v1.save("vex_v1.json")

# Updated VEX document (after investigation)
vex_v2 = vex_gen.create_document(
    document_id="vex-myapp-2.1.0-v2",
    product_id="pkg:npm/myapp@2.1.0",
    version="2.1.0",
    supersedes="vex-myapp-2.1.0-v1"  # Chain to previous
)

vex_v2.add_vulnerability(
    cve_id="CVE-2024-1234",
    status="not_affected",
    justification="vulnerable_code_not_present",
    impact_statement="Investigation complete: vulnerable code not in our build"
)

vex_v2.save("vex_v2.json")
```

### Version History

```python
# Track changes across versions
vex_doc = vex_gen.create_document(
    document_id="vex-myapp-2024-q4",
    product_id="pkg:npm/myapp@*",
    version_history=[
        {
            "version": "1.0",
            "date": "2024-12-01",
            "changes": "Initial release"
        },
        {
            "version": "1.1",
            "date": "2024-12-04",
            "changes": "Added CVE-2024-5678 status update"
        }
    ]
)
```

## OpenVEX Format Details

### Document Structure

```json
{
  "@context": "https://openvex.dev/ns/v0.2.0",
  "@id": "https://example.com/vex/myapp-2.1.0",
  "author": "ACME Corp Security Team",
  "timestamp": "2024-12-04T10:30:00Z",
  "version": "1",

  "statements": [
    {
      "vulnerability": {
        "name": "CVE-2024-1234"
      },
      "products": [
        {
          "@id": "pkg:npm/myapp@2.1.0"
        }
      ],
      "status": "not_affected",
      "justification": "vulnerable_code_not_present",
      "impact_statement": "The vulnerable function is not included in our build",
      "timestamp": "2024-12-04T10:30:00Z"
    }
  ]
}
```

### Product Identifiers

OpenVEX uses Package URLs (purl) for product identification:

```python
# npm package
"pkg:npm/express@4.18.2"

# Python package
"pkg:pypi/django@4.2.0"

# Container image
"pkg:oci/nginx@sha256:abc123..."

# Maven artifact
"pkg:maven/org.springframework/spring-core@6.0.0"

# Generic
"pkg:generic/myapp@2.1.0"
```

### Subcomponents

```python
vex_doc.add_vulnerability(
    cve_id="CVE-2024-1234",
    product_ids=["pkg:npm/myapp@2.1.0"],
    subcomponents=[
        "pkg:npm/express@4.18.2",
        "pkg:npm/lodash@4.17.21"
    ],
    status="not_affected",
    justification="vulnerable_code_not_present"
)
```

## CSAF Format Details

### Document Structure

```json
{
  "document": {
    "category": "csaf_vex",
    "csaf_version": "2.0",
    "publisher": {
      "category": "vendor",
      "name": "ACME Corp",
      "namespace": "https://acme.example.com"
    },
    "title": "Security Advisory for MyApp 2.1.0",
    "tracking": {
      "current_release_date": "2024-12-04T10:30:00Z",
      "id": "ACME-SA-2024-001",
      "initial_release_date": "2024-12-01T00:00:00Z",
      "revision_history": [...],
      "status": "final",
      "version": "1.0"
    }
  },
  "product_tree": {...},
  "vulnerabilities": [...]
}
```

### Product Tree

```python
csaf_doc.add_product_tree(
    branches=[
        {
            "category": "vendor",
            "name": "ACME Corp",
            "branches": [
                {
                    "category": "product_name",
                    "name": "MyApp",
                    "branches": [
                        {
                            "category": "product_version",
                            "name": "2.1.0",
                            "product": {
                                "product_id": "CSAFPID-0001",
                                "name": "MyApp 2.1.0",
                                "product_identification_helper": {
                                    "cpe": "cpe:2.3:a:acme:myapp:2.1.0:*:*:*:*:*:*:*",
                                    "purl": "pkg:generic/myapp@2.1.0"
                                }
                            }
                        }
                    ]
                }
            ]
        }
    ]
)
```

### Threats and Remediations

```python
csaf_doc.add_vulnerability(
    cve_id="CVE-2024-1234",
    product_ids=["CSAFPID-0001"],
    threats=[
        {
            "category": "impact",
            "details": "No impact as vulnerable code is not present",
            "product_ids": ["CSAFPID-0001"]
        }
    ],
    threat_status="not_affected",
    remediations=[
        {
            "category": "vendor_fix",
            "details": "Not affected - no action required",
            "product_ids": ["CSAFPID-0001"]
        }
    ]
)
```

## Automated VEX Generation

### From SBOM

```bash
# Generate VEX from SBOM
python -m cli.threat_cli vex \
  --sbom sbom.json \
  --sbom-format cyclonedx \
  --product "myapp:2.1.0" \
  --format openvex \
  --output vex_document.json \
  --auto-analyze
```

### From Scan Results

```python
from vex.vex_generator import VEXGenerator

# Load scan results (Trivy, Grype, etc.)
with open('scan_results.json') as f:
    scan_data = json.load(f)

# Generate VEX
vex_gen = VEXGenerator(format="openvex")
vex_doc = vex_gen.from_scan_results(
    scan_data=scan_data,
    scanner="trivy",
    product_id="pkg:oci/myapp@sha256:abc123",
    auto_justify=True  # Attempt automatic justifications
)

vex_doc.save("vex_from_scan.json")
```

### CI/CD Integration

```yaml
# .github/workflows/vex-generation.yml
name: Generate VEX

on:
  release:
    types: [published]

jobs:
  generate-vex:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2

      - name: Generate SBOM
        run: cyclonedx-py -o sbom.json

      - name: Scan for Vulnerabilities
        run: trivy sbom sbom.json --format json > scan.json

      - name: Generate VEX Document
        run: |
          python -m cli.threat_cli vex \
            --sbom sbom.json \
            --scan-results scan.json \
            --product "${{ github.repository }}:${{ github.event.release.tag_name }}" \
            --format openvex \
            --output vex_document.json

      - name: Sign VEX Document
        run: cosign sign-blob vex_document.json --output-signature vex_document.sig

      - name: Attach to Release
        uses: actions/upload-release-asset@v1
        with:
          upload_url: ${{ github.event.release.upload_url }}
          asset_path: vex_document.json
          asset_name: vex_document.json
          asset_content_type: application/json
```

## VEX Validation

### Validate VEX Document

```bash
# Validate OpenVEX
python -m cli.threat_cli validate-vex \
  --file vex_document.json \
  --format openvex

# Validate CSAF
python -m cli.threat_cli validate-vex \
  --file csaf_advisory.json \
  --format csaf

# Strict validation
python -m cli.threat_cli validate-vex \
  --file vex_document.json \
  --strict
```

### Python API

```python
from vex.vex_validator import VEXValidator

validator = VEXValidator()

# Validate document
result = validator.validate(
    vex_file="vex_document.json",
    format="openvex",
    strict=True
)

if result.is_valid:
    print("VEX document is valid")
else:
    print("Validation errors:")
    for error in result.errors:
        print(f"  - {error}")
```

## Best Practices

### Documentation

1. **Be Specific in Impact Statements**
   ```python
   # Good
   impact_statement="We use bcrypt for password hashing, not the affected MD5 implementation"

   # Bad
   impact_statement="Not affected"
   ```

2. **Provide Action Statements**
   ```python
   action_statement="Upgrade to version 2.2.0 which includes the fix, or apply hotfix patch-2024-001 available at https://example.com/patches"
   ```

3. **Include Timestamps**
   ```python
   action_statement_timestamp=datetime.now()
   ```

### Maintenance

1. **Update Regularly**
   - Review VEX documents when new CVEs are discovered
   - Update status as vulnerabilities are fixed
   - Maintain version history

2. **Automate Where Possible**
   - Generate from SBOMs
   - Integrate with CI/CD
   - Auto-update on releases

3. **Sign VEX Documents**
   ```bash
   # Sign with cosign
   cosign sign-blob vex_document.json \
     --output-signature vex_document.sig

   # Verify signature
   cosign verify-blob vex_document.json \
     --signature vex_document.sig \
     --key cosign.pub
   ```

### Distribution

1. **Publish with Releases**
   - Include VEX with software releases
   - Upload to release assets
   - Link from release notes

2. **Make Discoverable**
   - Use standard naming: `vex_<product>_<version>.json`
   - Include in SBOM as external reference
   - Publish at well-known URLs

3. **Provide Machine-Readable Access**
   - VEX API endpoint
   - Include in container labels
   - Add to package metadata

## Examples

Complete examples available in `examples/vex/`:

- `basic_openvex.json` - Simple OpenVEX document
- `basic_csaf.json` - Simple CSAF document
- `comprehensive_vex.json` - Full-featured example
- `vex_chain.json` - VEX chaining example

## Next Steps

- Learn about [MITRE ATT&CK Mapping](attack_mapping.md)
- Set up [SIEM Integration](siem_integration.md)
- Review [Troubleshooting Guide](troubleshooting.md)
