# MITRE ATT&CK Mapping Guide

Guide for mapping threats to MITRE ATT&CK framework techniques and generating detection gap analysis.

## Table of Contents

- [Overview](#overview)
- [ATT&CK Framework Basics](#attck-framework-basics)
- [Technique Mapping](#technique-mapping)
- [Navigator Layer Generation](#navigator-layer-generation)
- [Detection Gap Analysis](#detection-gap-analysis)
- [Mitigation Recommendations](#mitigation-recommendations)

## Overview

The MITRE ATT&CK framework is a globally-accessible knowledge base of adversary tactics and techniques based on real-world observations. This platform maps threat intelligence to ATT&CK to help understand adversary behavior and identify detection gaps.

### Benefits

- **Understand Threat Landscape**: See which tactics and techniques are being used
- **Identify Detection Gaps**: Find unmonitored attack vectors
- **Prioritize Detections**: Focus on most relevant techniques
- **Track Coverage**: Measure detection capability improvements
- **Communication**: Common language for security discussions

## ATT&CK Framework Basics

### ATT&CK Matrices

The platform supports multiple ATT&CK matrices:

- **Enterprise**: Attacks against enterprise networks and cloud
- **Mobile**: Mobile device attacks
- **ICS**: Industrial Control Systems attacks

Default: Enterprise ATT&CK

### Tactics (Why)

14 tactical goals adversaries try to achieve:

1. **Reconnaissance**: Gather information for planning
2. **Resource Development**: Acquire resources for operations
3. **Initial Access**: Get into the network
4. **Execution**: Run malicious code
5. **Persistence**: Maintain presence
6. **Privilege Escalation**: Gain higher-level permissions
7. **Defense Evasion**: Avoid detection
8. **Credential Access**: Steal account credentials
9. **Discovery**: Learn about the environment
10. **Lateral Movement**: Move through the network
11. **Collection**: Gather data of interest
12. **Command and Control**: Communicate with compromised systems
13. **Exfiltration**: Steal data
14. **Impact**: Disrupt, degrade, or destroy systems

### Techniques (How)

Specific methods adversaries use to achieve tactical goals.

Example:
- Tactic: Initial Access
- Technique: T1566 - Phishing
- Sub-technique: T1566.001 - Spearphishing Attachment

## Technique Mapping

### CLI Usage

#### Map Threat Intelligence

```bash
# Map all threat intelligence
python -m cli.threat_cli attack-map \
  --output attack_mapping.json

# Map specific threats
python -m cli.threat_cli attack-map \
  --threat-file threats.json \
  --output attack_mapping.json

# Map by date range
python -m cli.threat_cli attack-map \
  --start-date 2024-11-01 \
  --end-date 2024-12-01 \
  --output attack_mapping.json

# Map specific threat actors
python -m cli.threat_cli attack-map \
  --threat-actors "APT29,APT28" \
  --output attack_mapping.json
```

#### Generate Navigator Layer

```bash
# Generate ATT&CK Navigator layer
python -m cli.threat_cli attack-map \
  --threat-file threats.json \
  --navigator-layer \
  --output navigator_layer.json

# With technique counts
python -m cli.threat_cli attack-map \
  --threat-file threats.json \
  --navigator-layer \
  --show-counts \
  --output navigator_layer.json

# Colored by frequency
python -m cli.threat_cli attack-map \
  --threat-file threats.json \
  --navigator-layer \
  --color-by frequency \
  --output navigator_layer.json
```

### Python API

#### Basic Mapping

```python
from attack.attack_mapper import ATTACKMapper
import json

# Initialize mapper
mapper = ATTACKMapper(
    attack_version="v14.1",
    domain="enterprise-attack"
)

# Load threat data
with open('threats.json') as f:
    threats = json.load(f)

# Map threats to techniques
mappings = mapper.map_threats_to_techniques(threats)

# Print results
for threat_id, techniques in mappings.items():
    print(f"\nThreat: {threat_id}")
    for technique in techniques:
        print(f"  {technique['id']}: {technique['name']}")
        print(f"    Tactic: {technique['tactic']}")
        print(f"    Confidence: {technique['confidence']}%")
```

#### Automatic Mapping

```python
# Automatic mapping from indicators
threat_data = {
    "indicators": [
        {
            "type": "malware",
            "name": "Cobalt Strike",
            "description": "Cobalt Strike beacon detected"
        }
    ]
}

# Map automatically
mappings = mapper.auto_map(threat_data)

# Cobalt Strike automatically maps to:
# T1071.001 - Application Layer Protocol: Web Protocols
# T1055 - Process Injection
# T1059.001 - Command and Scripting Interpreter: PowerShell
# T1105 - Ingress Tool Transfer
# etc.
```

#### Map by Threat Actor

```python
# Get threat actor techniques
actor_techniques = mapper.get_threat_actor_techniques(
    actor_name="APT29",
    include_software=True  # Include tools used by actor
)

print(f"APT29 uses {len(actor_techniques)} techniques:")
for technique in actor_techniques:
    print(f"  {technique['id']}: {technique['name']}")

# Get all actors using a technique
actors_using = mapper.get_actors_using_technique(
    technique_id="T1566.001"  # Spearphishing Attachment
)

print(f"Threat actors using T1566.001:")
for actor in actors_using:
    print(f"  - {actor['name']}")
```

#### Map by Malware

```python
# Get malware techniques
malware_techniques = mapper.get_malware_techniques(
    malware_name="Emotet"
)

print(f"Emotet uses {len(malware_techniques)} techniques:")
for technique in malware_techniques:
    print(f"  {technique['id']}: {technique['name']}")
```

### Mapping Strategies

#### Indicator-Based Mapping

```python
# Map from IOCs
iocs = [
    {
        "type": "domain",
        "value": "malicious.example.com",
        "context": "C2 communication"
    }
]

techniques = mapper.map_from_iocs(iocs)
# Returns: T1071 (Application Layer Protocol), T1568 (Dynamic Resolution)
```

#### Behavior-Based Mapping

```python
# Map from observed behaviors
behaviors = [
    "Process created with suspicious command line",
    "Registry key modified for persistence",
    "Network connection to external IP",
    "File encrypted with .locked extension"
]

techniques = mapper.map_from_behaviors(behaviors)
# Returns: T1059, T1547, T1071, T1486
```

#### Pattern-Based Mapping

```python
# Map from attack patterns in STIX
stix_pattern = "[process:command_line CONTAINS 'powershell.exe -enc']"

techniques = mapper.map_from_stix_pattern(stix_pattern)
# Returns: T1059.001 (PowerShell), T1027 (Obfuscated Files)
```

## Navigator Layer Generation

### Basic Layer

```python
from attack.navigator import NavigatorLayer

# Create layer
layer = NavigatorLayer(
    name="Threat Intelligence - December 2024",
    description="Threats observed in December 2024"
)

# Add techniques
layer.add_technique(
    technique_id="T1566.001",
    score=5,
    color="#ff0000",
    comment="10 incidents this month"
)

layer.add_technique(
    technique_id="T1059.001",
    score=3,
    color="#ff9900"
)

# Save layer
layer.save("december_threats.json")
```

### Threat-Based Layer

```python
# Generate layer from threats
layer = mapper.generate_navigator_layer(
    threats=threat_data,
    layer_name="Active Threats",
    color_by="frequency",  # or "severity", "recency"
    show_counts=True
)

layer.save("active_threats_layer.json")
```

### Coverage Layer

```python
# Compare threat techniques with detections
coverage_layer = mapper.generate_coverage_layer(
    threat_techniques=threat_techniques,
    detection_techniques=current_detections,
    layer_name="Detection Coverage"
)

# Techniques colored by coverage:
# Green: Detected
# Yellow: Partial detection
# Red: No detection

coverage_layer.save("coverage_layer.json")
```

### Multi-Layer Comparison

```python
# Create multiple layers for comparison
layers = []

# Layer 1: Q3 threats
q3_layer = mapper.generate_navigator_layer(
    threats=q3_threats,
    layer_name="Q3 2024 Threats"
)
layers.append(q3_layer)

# Layer 2: Q4 threats
q4_layer = mapper.generate_navigator_layer(
    threats=q4_threats,
    layer_name="Q4 2024 Threats"
)
layers.append(q4_layer)

# Export for Navigator
mapper.export_multi_layer(
    layers=layers,
    output="quarterly_comparison.json"
)
```

### Custom Styling

```python
# Create layer with custom styling
layer = NavigatorLayer(
    name="Custom Layer",
    gradient={
        "colors": ["#ffffff", "#ff0000"],
        "minValue": 0,
        "maxValue": 10
    }
)

# Add techniques with scores
for technique_id, count in technique_counts.items():
    layer.add_technique(
        technique_id=technique_id,
        score=count,
        comment=f"Observed {count} times"
    )

layer.save("custom_layer.json")
```

## Detection Gap Analysis

### Identify Gaps

```bash
# Compare threats with current detections
python -m cli.threat_cli attack-map \
  --threat-file threats.json \
  --detections current_detections.json \
  --gap-analysis \
  --output gaps.json

# With prioritization
python -m cli.threat_cli attack-map \
  --threat-file threats.json \
  --detections current_detections.json \
  --gap-analysis \
  --prioritize \
  --output prioritized_gaps.json
```

### Python API

```python
from attack.gap_analyzer import GapAnalyzer

# Initialize analyzer
analyzer = GapAnalyzer(mapper=mapper)

# Load detections
with open('current_detections.json') as f:
    detections = json.load(f)

# Perform gap analysis
gaps = analyzer.analyze_gaps(
    threat_techniques=threat_techniques,
    detection_techniques=detections,
    prioritize=True
)

# Print gaps by priority
for gap in gaps.get_high_priority():
    print(f"\nGAP: {gap['technique_id']} - {gap['technique_name']}")
    print(f"  Tactic: {gap['tactic']}")
    print(f"  Priority: {gap['priority_score']:.1f}/10")
    print(f"  Reason: {gap['priority_reason']}")
    print(f"  Threat Count: {gap['threat_count']}")
    print(f"  Recommendation: {gap['recommendation']}")
```

### Gap Prioritization

Gaps are prioritized based on:

1. **Threat Frequency**: How often the technique is seen
2. **Severity**: CVSS scores of related vulnerabilities
3. **Exploitability**: Known exploits and active use
4. **Asset Exposure**: Number of exposed assets
5. **Threat Actor Interest**: APT groups using this technique

```python
# Custom prioritization
gaps = analyzer.analyze_gaps(
    threat_techniques=threat_techniques,
    detection_techniques=detections,
    prioritize=True,
    priority_weights={
        'frequency': 0.3,
        'severity': 0.25,
        'exploitability': 0.25,
        'exposure': 0.15,
        'actor_interest': 0.05
    }
)
```

### Coverage Metrics

```python
# Calculate coverage metrics
metrics = analyzer.calculate_coverage(
    threat_techniques=threat_techniques,
    detection_techniques=detections
)

print(f"Coverage Metrics:")
print(f"  Overall Coverage: {metrics['overall_coverage']}%")
print(f"  Tactics Covered: {metrics['tactics_covered']}/{metrics['total_tactics']}")
print(f"  Techniques Covered: {metrics['techniques_covered']}/{metrics['total_techniques']}")
print(f"  Critical Gaps: {metrics['critical_gaps']}")
print(f"  High Priority Gaps: {metrics['high_priority_gaps']}")

# Coverage by tactic
for tactic, coverage in metrics['tactic_coverage'].items():
    print(f"  {tactic}: {coverage}%")
```

### Gap Remediation Plan

```python
# Generate remediation plan
plan = analyzer.generate_remediation_plan(
    gaps=gaps,
    budget_hours=160,  # Two person-weeks
    prioritize_by='roi'  # Return on investment
)

print("Remediation Plan:")
for item in plan['items']:
    print(f"\n{item['rank']}. {item['technique_id']}: {item['technique_name']}")
    print(f"   Effort: {item['effort_hours']} hours")
    print(f"   Impact: Covers {item['threat_count']} threats")
    print(f"   ROI: {item['roi']:.2f}")
    print(f"   Implementation: {item['implementation_approach']}")
```

## Mitigation Recommendations

### Get Mitigations

```python
# Get mitigations for a technique
mitigations = mapper.get_mitigations(
    technique_id="T1566.001"  # Spearphishing Attachment
)

for mitigation in mitigations:
    print(f"Mitigation: {mitigation['id']} - {mitigation['name']}")
    print(f"  Description: {mitigation['description']}")
    print(f"  Effectiveness: {mitigation['effectiveness']}")
```

### Comprehensive Mitigation Plan

```python
# Get mitigations for all threat techniques
mitigation_plan = mapper.generate_mitigation_plan(
    techniques=threat_techniques,
    current_controls=existing_controls,
    prioritize=True
)

for item in mitigation_plan:
    print(f"\n{item['technique_id']}: {item['technique_name']}")
    print(f"  Current Coverage: {item['current_coverage']}%")
    print(f"  Recommended Mitigations:")
    for mitigation in item['recommendations']:
        print(f"    - {mitigation['name']}")
        print(f"      Implementation: {mitigation['implementation']}")
        print(f"      Cost: {mitigation['estimated_cost']}")
```

### Detection Rules

```python
# Generate detection rule recommendations
detection_rules = mapper.get_detection_rules(
    technique_id="T1059.001",  # PowerShell
    rule_format="sigma"  # or "splunk", "elastic", "yara"
)

for rule in detection_rules:
    print(f"Rule: {rule['name']}")
    print(f"  Platform: {rule['platform']}")
    print(f"  Severity: {rule['severity']}")
    print(f"  Rule:\n{rule['rule_content']}")
```

## Advanced Features

### Threat Actor Tracking

```python
# Track threat actor activity
actor_activity = mapper.track_threat_actor(
    actor_name="APT29",
    time_range="2024-Q4",
    include_campaigns=True
)

print(f"APT29 Activity - Q4 2024:")
print(f"  Campaigns: {actor_activity['campaign_count']}")
print(f"  Techniques Used: {len(actor_activity['techniques'])}")
print(f"  New Techniques: {len(actor_activity['new_techniques'])}")
print(f"  Targeted Industries: {', '.join(actor_activity['industries'])}")
```

### Technique Evolution

```python
# Track how techniques evolve
evolution = mapper.track_technique_evolution(
    technique_id="T1059.001",
    time_range="last_year"
)

print(f"PowerShell (T1059.001) Evolution:")
print(f"  Usage Trend: {evolution['trend']}")  # increasing/decreasing
print(f"  New Procedures: {evolution['new_procedure_count']}")
print(f"  Updated Mitigations: {evolution['mitigation_updates']}")
```

### Campaign Analysis

```python
# Analyze attack campaign
campaign_techniques = mapper.analyze_campaign(
    campaign_indicators=campaign_iocs,
    campaign_behaviors=observed_behaviors,
    campaign_malware=malware_samples
)

# Get campaign techniques ordered by kill chain
for phase in campaign_techniques['kill_chain']:
    print(f"\n{phase['phase']}:")
    for technique in phase['techniques']:
        print(f"  {technique['id']}: {technique['name']}")
```

### Heatmap Generation

```python
# Generate technique heatmap
heatmap = mapper.generate_heatmap(
    data=threat_data,
    metric="frequency",  # or "severity", "recency"
    time_period="monthly",
    output_format="html"
)

heatmap.save("technique_heatmap.html")
```

## Integration Examples

### With SIEM

```python
# Export to SIEM for correlation
siem_export = mapper.export_for_siem(
    techniques=threat_techniques,
    format="splunk",
    include_iocs=True
)

# Creates lookup table for Splunk:
# technique_id, technique_name, tactic, severity, iocs
```

### With Ticketing System

```python
# Create tickets for detection gaps
for gap in high_priority_gaps:
    ticket = {
        'title': f"Detection Gap: {gap['technique_name']}",
        'description': f"""
        Technique: {gap['technique_id']} - {gap['technique_name']}
        Tactic: {gap['tactic']}
        Priority: {gap['priority_score']}/10

        Threats using this technique: {gap['threat_count']}

        Recommendation: {gap['recommendation']}

        References:
        - ATT&CK: https://attack.mitre.org/techniques/{gap['technique_id']}
        """,
        'priority': 'High' if gap['priority_score'] >= 7 else 'Medium',
        'labels': ['detection-gap', 'attack-technique', gap['tactic']]
    }

    # Create Jira ticket
    jira.create_issue(ticket)
```

## Best Practices

1. **Regular Updates**
   - Update ATT&CK data monthly
   - Re-map threats quarterly
   - Review coverage continuously

2. **Prioritize Gaps**
   - Focus on high-frequency techniques
   - Consider threat actor targeting
   - Balance effort vs. impact

3. **Document Assumptions**
   - Explain mapping decisions
   - Note confidence levels
   - Track sources

4. **Validate Mappings**
   - Review automated mappings
   - Involve analysts
   - Test detections

5. **Integrate with Workflow**
   - Link to threat intelligence
   - Connect to detection engineering
   - Align with vulnerability management

## Resources

- **ATT&CK Website**: https://attack.mitre.org/
- **ATT&CK Navigator**: https://mitre-attack.github.io/attack-navigator/
- **STIX to ATT&CK**: Automatic mapping in platform
- **Community Layers**: Share and import community layers

## Next Steps

- Set up [SIEM Integration](siem_integration.md)
- Manage [IOCs](ioc_management.md)
- Review [Troubleshooting](troubleshooting.md)
