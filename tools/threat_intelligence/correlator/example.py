#!/usr/bin/env python3
"""Example usage of the Threat Correlator module."""

from datetime import datetime

from threat_correlator import (
    CVE,
    Asset,
    STIXObject,
    ThreatCorrelator,
    ThreatIndicator,
)


def example_basic_correlation():
    """Demonstrate basic vulnerability-to-threat correlation."""
    print("=" * 70)
    print("Example 1: Basic Vulnerability-to-Threat Correlation")
    print("=" * 70)

    # Initialize correlator
    correlator = ThreatCorrelator({"cache_enabled": True, "min_correlation_score": 0.5})

    # Create CVE vulnerabilities
    cves = [
        CVE(
            cve_id="CVE-2024-1234",
            description="Remote code execution vulnerability in Apache",
            cvss_score=9.8,
            cvss_vector="CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H",
            exploit_available=True,
            epss_score=0.85,
            published_date="2024-01-15T00:00:00Z",
        ),
        CVE(
            cve_id="CVE-2024-5678",
            description="SQL injection vulnerability",
            cvss_score=7.5,
            exploit_available=False,
            epss_score=0.15,
            published_date="2024-02-01T00:00:00Z",
        ),
    ]

    # Create STIX threat objects
    now = datetime.now().isoformat()
    threats = [
        STIXObject(
            id="indicator--123",
            type="indicator",
            created=now,
            modified=now,
            name="CVE-2024-1234 Exploitation Campaign",
            description="Active exploitation of CVE-2024-1234 by APT28",
            labels=["exploit", "active-exploitation"],
            external_references=[
                {"source_name": "cve", "external_id": "CVE-2024-1234"},
                {"source_name": "mitre-attack", "external_id": "T1190"},
            ],
        ),
        STIXObject(
            id="threat-actor--456",
            type="threat-actor",
            created=now,
            modified=now,
            name="APT28",
            description="Nation-state actor exploiting web vulnerabilities",
            external_references=[
                {"source_name": "cve", "external_id": "CVE-2024-1234"}
            ],
        ),
    ]

    # Correlate vulnerabilities
    correlations = correlator.correlate_vulnerabilities(cves, threats)

    print(f"\nFound {len(correlations)} correlations:\n")
    for correlation in correlations:
        print(f"CVE ID: {correlation.cve_id}")
        print(f"  Correlation Score: {correlation.correlation_score:.2f}")
        print(
            "  Active Exploitation: "
            f"{'YES' if correlation.active_exploitation else 'NO'}"
        )
        print(
            "  Exploit Available: "
            f"{'YES' if correlation.exploit_available else 'NO'}"
        )
        print(f"  Threat Actors: {', '.join(correlation.threat_actors)}")
        print(f"  ATT&CK Techniques: {', '.join(correlation.techniques)}")
        print(f"  Threat Indicators: {len(correlation.threat_indicators)}")
        print()


def example_asset_risk_analysis():
    """Demonstrate asset risk analysis."""
    print("=" * 70)
    print("Example 2: Asset Risk Analysis")
    print("=" * 70)

    correlator = ThreatCorrelator()

    # Define assets
    assets = [
        Asset(
            asset_id="asset-001",
            name="Production Web Server",
            type="server",
            ip_addresses=["10.0.1.100"],
            software=[
                {"name": "apache", "version": "2.4.50"},
                {"name": "openssl", "version": "1.1.1"},
                {"name": "php", "version": "8.1.0"},
            ],
            criticality="CRITICAL",
        ),
        Asset(
            asset_id="asset-002",
            name="Developer Workstation",
            type="workstation",
            ip_addresses=["192.168.1.200"],
            software=[{"name": "chrome", "version": "120.0"}],
            criticality="MEDIUM",
        ),
    ]

    # Define threat indicators
    now = datetime.now().isoformat()
    threats = [
        ThreatIndicator(
            indicator_id="threat-001",
            type="cve",
            value="CVE-2024-1234",
            threat_type="exploit",
            confidence=0.95,
            severity="CRITICAL",
            first_seen=now,
            last_seen=now,
            tags=["remote-code-execution", "apache"],
        ),
        ThreatIndicator(
            indicator_id="threat-002",
            type="ip",
            value="10.0.1.100",
            threat_type="malware",
            confidence=0.7,
            severity="HIGH",
            first_seen=now,
            last_seen=now,
            tags=["botnet", "c2-communication"],
        ),
    ]

    # Analyze asset risk
    risk_assessments = correlator.analyze_asset_risk(assets, threats)

    print(f"\nRisk assessments for {len(assets)} assets:\n")
    for risk in risk_assessments:
        print(f"Asset ID: {risk.asset_id}")
        print(f"  Risk Score: {risk.risk_score:.1f}/100")
        print(
            f"  Threats: {risk.threat_count} total "
            f"({risk.critical_threats} critical)"
        )
        print(f"  Vulnerable Software: {len(risk.vulnerable_software)} components")
        print(f"  Exposure Window: {risk.exposure_window} days")
        print("  Recommendations:")
        for rec in risk.recommendations[:3]:
            print(f"    - {rec}")
        print()


def example_sbom_analysis():
    """Demonstrate SBOM threat analysis."""
    print("=" * 70)
    print("Example 3: SBOM Threat Analysis")
    print("=" * 70)

    correlator = ThreatCorrelator()

    # SPDX format SBOM
    sbom = {
        "spdxVersion": "SPDX-2.3",
        "SPDXID": "SPDXRef-DOCUMENT",
        "name": "Application SBOM",
        "packages": [
            {
                "name": "log4j",
                "versionInfo": "2.14.1",
                "SPDXID": "SPDXRef-Package-log4j",
            },
            {
                "name": "spring-boot",
                "versionInfo": "2.5.0",
                "SPDXID": "SPDXRef-Package-spring",
            },
            {
                "name": "jackson-databind",
                "versionInfo": "2.12.3",
                "SPDXID": "SPDXRef-Package-jackson",
            },
            {"name": "commons-io", "versionInfo": "2.11.0"},
        ],
    }

    # Threat indicators
    now = datetime.now().isoformat()
    threats = [
        ThreatIndicator(
            indicator_id=f"threat-{i}",
            type="cve",
            value=f"CVE-2024-{1000 + i}",
            threat_type="exploit",
            confidence=0.9 - (i * 0.1),
            severity=["CRITICAL", "HIGH", "MEDIUM"][i % 3],
            first_seen=now,
            last_seen=now,
            tags=["dependency-vulnerability"],
        )
        for i in range(5)
    ]

    # Analyze SBOM
    analysis = correlator.analyze_sbom(sbom, threats)

    print("\nSBOM Analysis Results:\n")
    print(f"Total Components: {analysis.total_components}")
    print(f"Vulnerable Components: {analysis.vulnerable_components}")
    print(f"Threat Exposure Score: {analysis.threat_exposure:.1f}/100")
    print(f"Critical Vulnerabilities: {len(analysis.critical_vulns)}")
    print(f"High Vulnerabilities: {len(analysis.high_vulns)}")
    print("\nRecommendations:")
    for rec in analysis.recommendations:
        print(f"  - {rec}")
    print()


def example_exploit_prediction():
    """Demonstrate exploit likelihood prediction."""
    print("=" * 70)
    print("Example 4: Exploit Likelihood Prediction")
    print("=" * 70)

    correlator = ThreatCorrelator()

    # High-risk CVE
    cve_high_risk = CVE(
        cve_id="CVE-2024-1234",
        cvss_score=9.8,
        exploit_available=True,
        epss_score=0.95,
        published_date="2024-01-15T00:00:00Z",
    )

    # Low-risk CVE
    cve_low_risk = CVE(
        cve_id="CVE-2024-9999",
        cvss_score=3.1,
        exploit_available=False,
        epss_score=0.05,
        published_date="2024-11-01T00:00:00Z",
    )

    # Threat intelligence
    now = datetime.now().isoformat()
    threats = [
        STIXObject(
            id="indicator--123",
            type="indicator",
            created=now,
            modified=now,
            labels=["active-exploitation"],
            external_references=[
                {"source_name": "cve", "external_id": "CVE-2024-1234"}
            ],
        )
    ]

    # Predict exploit likelihood
    likelihood_high = correlator.predict_exploit_likelihood(cve_high_risk, threats)
    likelihood_low = correlator.predict_exploit_likelihood(cve_low_risk, [])

    print("\nExploit Likelihood Predictions:\n")
    print(f"{cve_high_risk.cve_id} (CVSS: {cve_high_risk.cvss_score}):")
    print(f"  Likelihood: {likelihood_high:.1%}")
    print(f"  EPSS: {cve_high_risk.epss_score:.1%}")
    print("  Exploit Available: YES")
    print("  Active Exploitation: YES\n")

    print(f"{cve_low_risk.cve_id} (CVSS: {cve_low_risk.cvss_score}):")
    print(f"  Likelihood: {likelihood_low:.1%}")
    print(f"  EPSS: {cve_low_risk.epss_score:.1%}")
    print("  Exploit Available: NO")
    print("  Active Exploitation: NO\n")


def main():
    """Run all examples."""
    print("\n")
    print("*" * 70)
    print("Threat Correlator Module - Usage Examples")
    print("*" * 70)
    print()

    example_basic_correlation()
    print()

    example_asset_risk_analysis()
    print()

    example_sbom_analysis()
    print()

    example_exploit_prediction()
    print()

    print("=" * 70)
    print("Examples completed successfully!")
    print("=" * 70)
    print()


if __name__ == "__main__":
    main()
