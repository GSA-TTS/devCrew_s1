#!/usr/bin/env python3
"""
Example usage of the Security Scanner module.

This script demonstrates various scanning scenarios and features.
"""

import json
from pathlib import Path

from security_scanner import (
    SBOMFormat,
    ScannerConfig,
    ScannerType,
    SecurityScanner,
    SeverityLevel,
)


def example_basic_scan():
    """Example 1: Basic image scanning."""
    print("=" * 80)
    print("Example 1: Basic Image Scan")
    print("=" * 80)

    try:
        scanner = SecurityScanner()
        result = scanner.scan_image("alpine:latest")

        print(f"\nImage: {result.image}")
        print(f"Scan time: {result.scan_time}")
        print(f"Scanner versions: {result.scanner_version}")

        print("\nVulnerability Summary:")
        summary = result.get_summary()
        print(f"  Total: {summary['vulnerabilities']['total']}")
        print(f"  Critical: {summary['vulnerabilities']['critical']}")
        print(f"  High: {summary['vulnerabilities']['high']}")
        print(f"  Medium: {summary['vulnerabilities']['medium']}")
        print(f"  Low: {summary['vulnerabilities']['low']}")
        print(f"  Fixable: {summary['vulnerabilities']['fixable']}")

        if result.critical_count > 0:
            print("\nCritical Vulnerabilities:")
            for vuln in result.vulnerabilities:
                if vuln.severity == SeverityLevel.CRITICAL:
                    print(f"  - {vuln.id}: {vuln.title}")
                    print(f"    Package: {vuln.package_name} {vuln.installed_version}")
                    if vuln.fixed_version:
                        print(f"    Fix: Upgrade to {vuln.fixed_version}")
                    if vuln.cvss_score:
                        print(f"    CVSS: {vuln.cvss_score}")

    except Exception as e:
        print(f"Error: {e}")


def example_high_severity_scan():
    """Example 2: Scan with severity filtering."""
    print("\n" + "=" * 80)
    print("Example 2: High Severity Scan")
    print("=" * 80)

    try:
        config = ScannerConfig(
            severity_threshold=SeverityLevel.HIGH, ignore_unfixed=True
        )
        scanner = SecurityScanner(config)
        result = scanner.scan_image("nginx:latest")

        print(f"\nImage: {result.image}")
        print(f"Total vulnerabilities (HIGH+): {result.total_vulnerabilities}")
        print(f"Critical: {result.critical_count}")
        print(f"High: {result.high_count}")

        # Show only fixable vulnerabilities
        fixable = [v for v in result.vulnerabilities if v.is_fixable()]
        print(f"\nFixable vulnerabilities: {len(fixable)}")

        if fixable:
            print("\nFixable Issues:")
            for vuln in fixable[:5]:  # Show first 5
                print(
                    f"  - {vuln.id} ({vuln.severity.value}): "
                    f"{vuln.package_name} {vuln.installed_version} "
                    f"-> {vuln.fixed_version}"
                )

    except Exception as e:
        print(f"Error: {e}")


def example_comprehensive_scan():
    """Example 3: Comprehensive scan with all features."""
    print("\n" + "=" * 80)
    print("Example 3: Comprehensive Scan")
    print("=" * 80)

    try:
        config = ScannerConfig(
            scanner_type=ScannerType.TRIVY,
            scan_misconfig=True,
            scan_secrets=True,
            scan_licenses=True,
            enable_cache=True,
        )
        scanner = SecurityScanner(config)
        result = scanner.scan_image("ubuntu:20.04")

        print(f"\nImage: {result.image}")

        # Vulnerabilities
        print(f"\nVulnerabilities: {result.total_vulnerabilities}")
        if result.total_vulnerabilities > 0:
            print(f"  Critical: {result.critical_count}")
            print(f"  High: {result.high_count}")
            print(f"  Medium: {result.medium_count}")

        # Misconfigurations
        print(f"\nMisconfigurations: {len(result.misconfigurations)}")
        if result.misconfigurations:
            print("\nMisconfiguration Examples:")
            for misconfig in result.misconfigurations[:3]:
                print(f"  - {misconfig.id}: {misconfig.title}")
                print(f"    Severity: {misconfig.severity.value}")
                print(f"    File: {misconfig.file_path}")

        # Secrets
        print(f"\nSecrets Found: {len(result.secrets)}")
        if result.secrets:
            print("\nWarning: Secrets detected in image!")
            for secret in result.secrets:
                print(f"  - {secret.type} in {secret.file_path}")

        # Has critical findings?
        if result.has_critical_findings():
            print("\n[!] Image has CRITICAL security issues!")
        else:
            print("\n[+] No critical security issues found")

    except Exception as e:
        print(f"Error: {e}")


def example_dual_scanner():
    """Example 4: Using both Trivy and Grype."""
    print("\n" + "=" * 80)
    print("Example 4: Dual Scanner (Trivy + Grype)")
    print("=" * 80)

    try:
        config = ScannerConfig(scanner_type=ScannerType.BOTH, enable_cache=False)
        scanner = SecurityScanner(config)

        print("Scanning with both Trivy and Grype...")
        result = scanner.scan_image("python:3.9-slim")

        print(f"\nImage: {result.image}")
        print(f"Scanners used: {', '.join(result.scanner_version.keys())}")
        print(f"Total vulnerabilities (deduplicated): {result.total_vulnerabilities}")

        # Show scanner distribution
        trivy_vulns = [v for v in result.vulnerabilities if v.scanner == "trivy"]
        grype_vulns = [v for v in result.vulnerabilities if v.scanner == "grype"]

        print(f"\nFound by Trivy: {len(trivy_vulns)}")
        print(f"Found by Grype: {len(grype_vulns)}")

        # Vulnerabilities with CVSS scores
        scored = [v for v in result.vulnerabilities if v.cvss_score is not None]
        if scored:
            avg_cvss = sum(v.cvss_score for v in scored) / len(scored)
            print(f"\nAverage CVSS Score: {avg_cvss:.2f}")

    except Exception as e:
        print(f"Error: {e}")


def example_sbom_generation():
    """Example 5: SBOM generation."""
    print("\n" + "=" * 80)
    print("Example 5: SBOM Generation")
    print("=" * 80)

    try:
        scanner = SecurityScanner()

        # Scan with SBOM
        result = scanner.scan_image(
            "node:16-alpine", generate_sbom=True, sbom_format=SBOMFormat.CYCLONEDX_JSON
        )

        print(f"\nImage: {result.image}")
        print(f"Vulnerabilities: {result.total_vulnerabilities}")

        if result.sbom:
            print("\nSBOM Generated:")
            print(f"  Format: CycloneDX")
            print(f"  Components: {len(result.sbom.get('components', []))}")

            # Save SBOM to file
            sbom_file = Path("sbom-node.json")
            sbom_file.write_text(json.dumps(result.sbom, indent=2))
            print(f"  Saved to: {sbom_file.absolute()}")

        # Generate standalone SBOM
        print("\nGenerating standalone SPDX SBOM...")
        spdx_sbom = scanner.generate_sbom("node:16-alpine", SBOMFormat.SPDX_JSON)

        spdx_file = Path("sbom-node-spdx.json")
        spdx_file.write_text(json.dumps(spdx_sbom, indent=2))
        print(f"SPDX SBOM saved to: {spdx_file.absolute()}")

    except Exception as e:
        print(f"Error: {e}")


def example_ignore_list():
    """Example 6: Using ignore list for false positives."""
    print("\n" + "=" * 80)
    print("Example 6: Ignore List")
    print("=" * 80)

    try:
        # First scan without ignore list
        scanner1 = SecurityScanner()
        result1 = scanner1.scan_image("redis:alpine")
        print(f"\nWithout ignore list: {result1.total_vulnerabilities} vulnerabilities")

        # Collect some CVE IDs to ignore (example)
        ignore_cves = [v.id for v in result1.vulnerabilities[:2]]
        print(f"Ignoring: {', '.join(ignore_cves)}")

        # Scan with ignore list
        config = ScannerConfig(ignore_list=ignore_cves)
        scanner2 = SecurityScanner(config)
        result2 = scanner2.scan_image("redis:alpine")

        print(f"With ignore list: {result2.total_vulnerabilities} vulnerabilities")
        print(f"Filtered out: {result1.total_vulnerabilities - result2.total_vulnerabilities}")

    except Exception as e:
        print(f"Error: {e}")


def example_cache_management():
    """Example 7: Cache management."""
    print("\n" + "=" * 80)
    print("Example 7: Cache Management")
    print("=" * 80)

    try:
        cache_dir = Path("/tmp/scanner-cache-demo")
        config = ScannerConfig(enable_cache=True, cache_dir=cache_dir, cache_ttl=3600)
        scanner = SecurityScanner(config)

        # First scan (no cache)
        print("\nFirst scan (will be cached)...")
        result1 = scanner.scan_image("busybox:latest")
        print(f"Vulnerabilities: {result1.total_vulnerabilities}")

        # Second scan (from cache)
        print("\nSecond scan (from cache)...")
        result2 = scanner.scan_image("busybox:latest")
        print(f"Vulnerabilities: {result2.total_vulnerabilities}")

        # Check cache
        cache_files = list(cache_dir.glob("*.json"))
        print(f"\nCache files: {len(cache_files)}")

        # Clear cache
        cleared = scanner.clear_cache()
        print(f"Cleared {cleared} cache entries")

    except Exception as e:
        print(f"Error: {e}")


def example_database_update():
    """Example 8: Update vulnerability databases."""
    print("\n" + "=" * 80)
    print("Example 8: Database Update")
    print("=" * 80)

    try:
        scanner = SecurityScanner()

        print("\nUpdating vulnerability databases...")
        scanner.update_vulnerability_database()

        print("Database update complete!")
        print("\nScanner versions:")
        for scanner_name in scanner.scanners_available:
            version = scanner._get_scanner_version(scanner_name)
            print(f"  {scanner_name}: {version}")

    except Exception as e:
        print(f"Error: {e}")


def main():
    """Run all examples."""
    print("\n")
    print("=" * 80)
    print("Security Scanner - Example Usage")
    print("=" * 80)

    # Check scanner availability
    scanner = SecurityScanner()
    print(f"\nAvailable scanners: {', '.join(scanner.scanners_available)}")

    # Run examples
    examples = [
        ("Basic Scan", example_basic_scan),
        ("High Severity Scan", example_high_severity_scan),
        ("Comprehensive Scan", example_comprehensive_scan),
        ("Dual Scanner", example_dual_scanner),
        ("SBOM Generation", example_sbom_generation),
        ("Ignore List", example_ignore_list),
        ("Cache Management", example_cache_management),
        ("Database Update", example_database_update),
    ]

    print("\nAvailable examples:")
    for i, (name, _) in enumerate(examples, 1):
        print(f"  {i}. {name}")

    print("\nRunning selected examples...\n")

    # Run a subset of examples (to avoid long execution)
    # In production, you'd select which to run
    example_basic_scan()
    example_high_severity_scan()
    example_comprehensive_scan()

    print("\n" + "=" * 80)
    print("Examples complete!")
    print("=" * 80)


if __name__ == "__main__":
    main()
