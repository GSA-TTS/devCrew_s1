# Threat Correlation Guide

Guide for correlating threat intelligence with your asset inventory and software bill of materials (SBOM).

## Table of Contents

- [Overview](#overview)
- [Asset Inventory Format](#asset-inventory-format)
- [SBOM Integration](#sbom-integration)
- [Risk Scoring Methodology](#risk-scoring-methodology)
- [Correlation Workflows](#correlation-workflows)
- [Advanced Correlation](#advanced-correlation)
- [Automation](#automation)

## Overview

Threat correlation matches threat intelligence data against your organization's assets to identify relevant risks. This helps prioritize vulnerabilities and threats based on actual exposure.

### What Gets Correlated

- **Vulnerabilities (CVEs)** with installed software
- **Indicators of Compromise (IOCs)** with network/host data
- **Threat Actors** with targeted industries/technologies
- **Attack Patterns** with security controls
- **Malware** with file hashes and behaviors

### Benefits

- Prioritize remediation efforts
- Reduce alert fatigue
- Focus on applicable threats
- Track remediation progress
- Generate risk reports

## Asset Inventory Format

### Basic Asset Format (JSON)

```json
{
  "assets": [
    {
      "id": "asset-001",
      "name": "web-server-01",
      "type": "server",
      "criticality": "high",
      "environment": "production",

      "location": {
        "site": "datacenter-1",
        "zone": "dmz",
        "ip": "10.0.1.100"
      },

      "software": [
        {
          "name": "nginx",
          "version": "1.24.0",
          "vendor": "NGINX Inc",
          "cpe": "cpe:2.3:a:nginx:nginx:1.24.0:*:*:*:*:*:*:*"
        },
        {
          "name": "OpenSSL",
          "version": "3.0.8",
          "cpe": "cpe:2.3:a:openssl:openssl:3.0.8:*:*:*:*:*:*:*"
        }
      ],

      "os": {
        "name": "Ubuntu",
        "version": "22.04",
        "cpe": "cpe:2.3:o:canonical:ubuntu_linux:22.04:*:*:*:lts:*:*:*"
      },

      "exposure": {
        "internet_facing": true,
        "authenticated_access": false,
        "ports": [80, 443]
      },

      "owner": "web-team@example.com",
      "tags": ["web", "public", "production"]
    }
  ]
}
```

### Asset Properties

#### Required Fields

- `id` - Unique asset identifier
- `name` - Human-readable asset name
- `type` - Asset type (server, workstation, container, etc.)
- `software` - List of installed software

#### Optional Fields

- `criticality` - Business criticality (low, medium, high, critical)
- `environment` - Environment (dev, staging, production)
- `location` - Physical/logical location
- `os` - Operating system details
- `exposure` - Network exposure information
- `owner` - Responsible team/person
- `tags` - Classification tags

### Criticality Levels

```json
{
  "criticality": "critical",
  "criticality_score": 10,
  "criticality_factors": {
    "business_impact": 10,
    "data_sensitivity": 9,
    "user_count": 5000,
    "revenue_impact": "high",
    "compliance_scope": ["PCI-DSS", "SOC2"]
  }
}
```

### Asset Types

Supported asset types:

- **Servers**: `server`, `web_server`, `database_server`, `app_server`
- **Workstations**: `workstation`, `laptop`, `desktop`
- **Network**: `firewall`, `router`, `switch`, `load_balancer`
- **Containers**: `container`, `pod`, `docker_image`
- **Cloud**: `ec2_instance`, `lambda_function`, `s3_bucket`
- **Mobile**: `mobile_device`, `tablet`
- **IoT**: `iot_device`, `sensor`

### Exposure Classification

```json
{
  "exposure": {
    "internet_facing": true,
    "authentication_required": false,
    "encryption_enabled": true,
    "ports": [80, 443, 8080],
    "protocols": ["HTTP", "HTTPS"],
    "access_control": "none",
    "attack_surface": "high"
  }
}
```

## SBOM Integration

### CycloneDX Format

```json
{
  "bomFormat": "CycloneDX",
  "specVersion": "1.5",
  "version": 1,
  "metadata": {
    "component": {
      "type": "application",
      "name": "my-webapp",
      "version": "2.1.0"
    }
  },
  "components": [
    {
      "type": "library",
      "name": "express",
      "version": "4.18.2",
      "purl": "pkg:npm/express@4.18.2",
      "licenses": [{"license": {"id": "MIT"}}],
      "hashes": [
        {
          "alg": "SHA-256",
          "content": "abc123..."
        }
      ]
    }
  ]
}
```

### SPDX Format

```json
{
  "spdxVersion": "SPDX-2.3",
  "dataLicense": "CC0-1.0",
  "SPDXID": "SPDXRef-DOCUMENT",
  "name": "my-webapp-2.1.0",
  "documentNamespace": "https://example.com/my-webapp/2.1.0",
  "packages": [
    {
      "SPDXID": "SPDXRef-Package-express",
      "name": "express",
      "versionInfo": "4.18.2",
      "packageFileName": "express-4.18.2.tgz",
      "licenseConcluded": "MIT"
    }
  ]
}
```

### Generate SBOM

#### For Python Projects

```bash
# Using cyclonedx-bom
pip install cyclonedx-bom
cyclonedx-py -o sbom.json

# Using syft
syft dir:. -o cyclonedx-json > sbom.json
```

#### For Node.js Projects

```bash
# Using @cyclonedx/bom
npm install -g @cyclonedx/bom
cyclonedx-npm --output-file sbom.json

# Using syft
syft dir:. -o cyclonedx-json > sbom.json
```

#### For Container Images

```bash
# Using syft
syft nginx:latest -o cyclonedx-json > sbom.json

# Using trivy
trivy image --format cyclonedx nginx:latest > sbom.json
```

#### For Multiple Ecosystems

```bash
# Using syft (auto-detects)
syft dir:. -o cyclonedx-json > sbom.json
```

## Risk Scoring Methodology

### Risk Score Calculation

Risk Score = (Threat Score × Exposure Score × Criticality Score) / 100

#### Threat Score (0-10)

Based on vulnerability severity and exploitability:

```python
threat_score = (
    cvss_score * 0.5 +
    exploitability * 0.3 +
    threat_intelligence * 0.2
)
```

Factors:
- CVSS Base Score (0-10)
- Exploitability (0-10): Known exploits, PoC availability
- Threat Intelligence (0-10): Active exploitation, threat actor interest

#### Exposure Score (0-10)

Based on asset exposure and attack surface:

```python
exposure_score = (
    internet_facing * 4 +
    authentication_strength * 3 +
    network_segmentation * 2 +
    access_controls * 1
) / 10
```

Factors:
- Internet-facing: 10 (public), 5 (internal), 0 (isolated)
- Authentication: 0 (none), 3 (weak), 7 (MFA), 10 (cert-based)
- Network Segmentation: 10 (none), 5 (some), 0 (full)
- Access Controls: Evaluated based on implementation

#### Criticality Score (0-10)

Based on business impact:

```python
criticality_score = (
    business_impact * 0.4 +
    data_sensitivity * 0.3 +
    availability_requirement * 0.3
)
```

Factors:
- Business Impact: 10 (revenue-critical), 5 (important), 0 (dev)
- Data Sensitivity: 10 (PII/PHI), 7 (confidential), 3 (internal), 0 (public)
- Availability: 10 (24/7 critical), 5 (business hours), 0 (best effort)

### Risk Levels

- **Critical (9.0-10.0)**: Immediate action required
- **High (7.0-8.9)**: Remediate within 7 days
- **Medium (4.0-6.9)**: Remediate within 30 days
- **Low (0.1-3.9)**: Remediate within 90 days
- **Info (0.0)**: No action required

## Correlation Workflows

### Basic Correlation

```bash
# Correlate threats with assets
python -m cli.threat_cli correlate \
  --assets assets.json \
  --output correlation_report.json

# With risk scoring
python -m cli.threat_cli correlate \
  --assets assets.json \
  --risk-scoring \
  --output risk_report.json
```

### SBOM Correlation

```bash
# Correlate threats with SBOM
python -m cli.threat_cli correlate \
  --sbom sbom.json \
  --format cyclonedx \
  --output sbom_threats.json

# Multiple SBOMs
python -m cli.threat_cli correlate \
  --sbom-dir ./sboms/ \
  --format cyclonedx \
  --output combined_report.json
```

### Filtered Correlation

```bash
# Only high/critical risks
python -m cli.threat_cli correlate \
  --assets assets.json \
  --min-risk 7.0 \
  --output high_risk.json

# Specific asset types
python -m cli.threat_cli correlate \
  --assets assets.json \
  --asset-types server,container \
  --output server_threats.json

# Specific vulnerabilities
python -m cli.threat_cli correlate \
  --assets assets.json \
  --cve-ids CVE-2024-1234,CVE-2024-5678 \
  --output specific_cves.json
```

### Continuous Correlation

```bash
# Run correlation daemon
python -m cli.threat_cli correlate \
  --assets assets.json \
  --daemon \
  --interval 3600 \
  --output-dir /var/reports/correlation/

# Alert on new high-risk findings
python -m cli.threat_cli correlate \
  --assets assets.json \
  --daemon \
  --alert-on-new \
  --min-risk 8.0 \
  --email security-team@example.com
```

## Advanced Correlation

### Python API

```python
from correlator.threat_correlator import ThreatCorrelator
import json

# Initialize correlator
correlator = ThreatCorrelator(
    threat_db="elasticsearch://localhost:9200",
    cache_enabled=True
)

# Load assets
with open('assets.json') as f:
    assets = json.load(f)

# Correlate threats
results = correlator.correlate(
    assets=assets['assets'],
    threat_types=['cve', 'malware', 'ioc'],
    include_context=True
)

# Process results
for asset_id, threats in results.items():
    asset = next(a for a in assets['assets'] if a['id'] == asset_id)

    print(f"\nAsset: {asset['name']} ({asset_id})")
    print(f"Threats Found: {len(threats)}")

    # Calculate risk score
    risk_score = correlator.calculate_risk_score(
        asset=asset,
        threats=threats
    )

    print(f"Risk Score: {risk_score['total_score']:.2f}/10")
    print(f"Critical: {risk_score['critical_count']}")
    print(f"High: {risk_score['high_count']}")

    # Get recommendations
    recommendations = correlator.get_recommendations(
        asset=asset,
        threats=threats,
        risk_score=risk_score
    )

    print(f"\nTop Recommendations:")
    for rec in recommendations[:3]:
        print(f"- {rec['action']}")
        print(f"  Priority: {rec['priority']}")
        print(f"  Impact: Reduces risk by {rec['risk_reduction']:.1f}")
```

### Asset-Specific Correlation

```python
# Correlate single asset
asset_threats = correlator.correlate_asset(
    asset_id="asset-001",
    asset_data=asset_data,
    lookback_days=90
)

# Find threats for specific software
software_threats = correlator.find_threats_for_software(
    software_name="nginx",
    software_version="1.24.0",
    include_future_versions=True
)

# Check if asset is affected by specific CVE
is_affected = correlator.is_asset_affected(
    asset_id="asset-001",
    cve_id="CVE-2024-1234"
)

# Get exploitable vulnerabilities
exploitable = correlator.get_exploitable_vulnerabilities(
    asset_id="asset-001",
    check_internet_exposure=True
)
```

### SBOM Analysis

```python
from correlator.sbom_analyzer import SBOMAnalyzer

# Initialize analyzer
analyzer = SBOMAnalyzer(correlator=correlator)

# Analyze SBOM
sbom_analysis = analyzer.analyze_sbom(
    sbom_file="sbom.json",
    sbom_format="cyclonedx"
)

print(f"Total Components: {sbom_analysis['total_components']}")
print(f"Vulnerable Components: {sbom_analysis['vulnerable_count']}")
print(f"Critical Vulnerabilities: {sbom_analysis['critical_count']}")

# Get component details
for component in sbom_analysis['vulnerable_components']:
    print(f"\n{component['name']} {component['version']}")
    print(f"  CVEs: {', '.join(component['cves'])}")
    print(f"  Risk Score: {component['risk_score']:.1f}")
    print(f"  Fix: Upgrade to {component['fixed_version']}")

# Compare SBOMs (before/after update)
comparison = analyzer.compare_sboms(
    old_sbom="sbom_v1.json",
    new_sbom="sbom_v2.json"
)

print(f"New Vulnerabilities: {comparison['new_vulnerabilities']}")
print(f"Fixed Vulnerabilities: {comparison['fixed_vulnerabilities']}")
print(f"Risk Change: {comparison['risk_delta']:+.1f}")
```

### Context-Aware Correlation

```python
# Add context to improve correlation
context = {
    "industry": "financial_services",
    "compliance_frameworks": ["PCI-DSS", "SOC2"],
    "threat_landscape": "high_targeted",
    "security_maturity": "advanced"
}

# Correlate with context
contextual_results = correlator.correlate_with_context(
    assets=assets,
    context=context,
    prioritize_by_context=True
)

# Context affects:
# - Threat actor relevance
# - Attack pattern likelihood
# - Compliance impact
# - Remediation urgency
```

### Threat Attribution

```python
# Match threats to threat actors
attributions = correlator.attribute_threats(
    threats=threat_data,
    assets=assets
)

for attribution in attributions:
    print(f"Threat Actor: {attribution['actor_name']}")
    print(f"Targeted Assets: {len(attribution['targeted_assets'])}")
    print(f"Tactics: {', '.join(attribution['tactics'])}")
    print(f"Confidence: {attribution['confidence']}%")
```

### Correlation Reports

```python
# Generate comprehensive report
report = correlator.generate_report(
    assets=assets,
    threats=threats,
    include_executive_summary=True,
    include_technical_details=True,
    format="pdf"
)

report.save("threat_correlation_report.pdf")

# Generate remediation plan
remediation = correlator.generate_remediation_plan(
    results=correlation_results,
    prioritize_by="risk",
    group_by="asset",
    include_timelines=True
)

remediation.export("remediation_plan.xlsx")
```

## Automation

### Scheduled Correlation

```python
# automated_correlation.py
from correlator.threat_correlator import ThreatCorrelator
from datetime import datetime
import schedule
import json

def run_correlation():
    """Run correlation and alert on new findings."""

    correlator = ThreatCorrelator()

    # Load assets
    with open('/opt/assets/inventory.json') as f:
        assets = json.load(f)

    # Run correlation
    results = correlator.correlate(
        assets=assets['assets'],
        risk_scoring=True
    )

    # Check for high-risk findings
    high_risk = [
        r for r in results.values()
        if r['risk_score']['total_score'] >= 8.0
    ]

    if high_risk:
        # Send alerts
        correlator.send_alert(
            findings=high_risk,
            recipients=['security-team@example.com'],
            severity='high'
        )

        # Create tickets
        for finding in high_risk:
            correlator.create_ticket(
                system='jira',
                finding=finding,
                priority='P1'
            )

    # Save report
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    with open(f'/var/reports/correlation_{timestamp}.json', 'w') as f:
        json.dump(results, f, indent=2)

# Schedule correlation
schedule.every(1).hours.do(run_correlation)

# Run immediately on start
run_correlation()

# Keep running
while True:
    schedule.run_pending()
    time.sleep(60)
```

### CI/CD Integration

```yaml
# .github/workflows/security-scan.yml
name: Security Scan

on:
  push:
    branches: [main, develop]
  pull_request:
  schedule:
    - cron: '0 0 * * *'  # Daily

jobs:
  sbom-correlation:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2

      - name: Generate SBOM
        run: |
          pip install cyclonedx-bom
          cyclonedx-py -o sbom.json

      - name: Setup Threat Intel
        run: |
          pip install -r tools/threat_intelligence/requirements.txt

      - name: Correlate SBOM with Threats
        id: correlate
        run: |
          python -m cli.threat_cli correlate \
            --sbom sbom.json \
            --format cyclonedx \
            --output threats.json \
            --min-risk 7.0 \
            --fail-on-critical

      - name: Upload Results
        if: always()
        uses: actions/upload-artifact@v2
        with:
          name: security-scan-results
          path: threats.json

      - name: Comment PR
        if: github.event_name == 'pull_request'
        uses: actions/github-script@v6
        with:
          script: |
            const fs = require('fs');
            const results = JSON.parse(fs.readFileSync('threats.json'));

            const comment = `## Security Scan Results

            - Critical: ${results.summary.critical_count}
            - High: ${results.summary.high_count}
            - Medium: ${results.summary.medium_count}

            ${results.summary.critical_count > 0 ? '⚠️ Critical vulnerabilities found!' : '✅ No critical issues'}
            `;

            github.rest.issues.createComment({
              issue_number: context.issue.number,
              owner: context.repo.owner,
              repo: context.repo.repo,
              body: comment
            });
```

### Webhook Integration

```python
# webhook_handler.py
from flask import Flask, request, jsonify
from correlator.threat_correlator import ThreatCorrelator

app = Flask(__name__)
correlator = ThreatCorrelator()

@app.route('/webhook/asset-change', methods=['POST'])
def handle_asset_change():
    """Handle asset inventory changes."""

    data = request.json

    # Run correlation for changed asset
    result = correlator.correlate_asset(
        asset_id=data['asset_id'],
        asset_data=data['asset_data']
    )

    # Alert if high risk
    if result['risk_score']['total_score'] >= 8.0:
        correlator.send_alert(
            finding=result,
            recipients=['security-team@example.com']
        )

    return jsonify({
        'status': 'success',
        'risk_score': result['risk_score']['total_score'],
        'threats_found': len(result['threats'])
    })

@app.route('/webhook/new-threat', methods=['POST'])
def handle_new_threat():
    """Handle new threat intelligence."""

    threat_data = request.json

    # Check which assets are affected
    affected_assets = correlator.find_affected_assets(
        threat=threat_data
    )

    if affected_assets:
        # Create tickets for affected assets
        for asset in affected_assets:
            correlator.create_ticket(
                system='jira',
                asset=asset,
                threat=threat_data
            )

    return jsonify({
        'status': 'success',
        'affected_assets': len(affected_assets)
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
```

## Best Practices

1. **Keep Asset Inventory Updated**
   - Automate inventory collection
   - Validate asset data regularly
   - Include all software versions

2. **Use CPE Identifiers**
   - Improves correlation accuracy
   - Standardized format
   - Widely supported

3. **Maintain SBOMs**
   - Generate SBOMs for all applications
   - Update SBOMs on every release
   - Include transitive dependencies

4. **Context is Key**
   - Include asset criticality
   - Document network exposure
   - Track business impact

5. **Automate Where Possible**
   - Scheduled correlation
   - CI/CD integration
   - Webhook-based triggers

6. **Review and Tune**
   - Adjust risk scoring
   - Refine filters
   - Update criticality ratings

## Next Steps

- Generate [VEX Documents](vex_documentation.md)
- Map to [MITRE ATT&CK](attack_mapping.md)
- Integrate with [SIEM](siem_integration.md)
