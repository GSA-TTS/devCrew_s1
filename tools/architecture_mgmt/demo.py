#!/usr/bin/env python3
"""
Demo script for Architecture Management & Documentation Platform
Issue #40: TOOL-ARCH-001

Demonstrates all core features:
- ADR creation and management
- C4 diagram generation
- Fitness function testing
- ASR tracking
"""

import tempfile
from pathlib import Path

from adr_manager import ADRManager
from asr_tracker import ASRExtractor, ASRTracker
from c4_generator import C4Generator, C4Model
from fitness_functions import FitnessRule, FitnessTester


def demo_adr_management():
    """Demonstrate ADR management."""
    print("\n" + "=" * 70)
    print("ADR MANAGEMENT DEMO")
    print("=" * 70)

    with tempfile.TemporaryDirectory() as tmpdir:
        manager = ADRManager(adr_dir=tmpdir)

        # Create first ADR
        adr1 = manager.create(
            title="Use Microservices Architecture",
            context="Need scalable backend architecture for 10K+ concurrent users",
            decision="Adopt microservices architecture with service mesh",
            consequences="Increased operational complexity but better scalability",
            status="accepted",
            decision_drivers=[
                "Scalability requirements (10K+ RPS)",
                "Team autonomy (5+ development teams)",
                "Independent deployment capability",
            ],
            considered_options=[
                "Monolithic architecture",
                "Microservices architecture",
                "Modular monolith",
            ],
        )

        print(f"\n✓ Created ADR-{adr1.number:03d}: {adr1.title}")
        print(f"  Status: {adr1.status}")
        print(f"  Date: {adr1.date}")

        # Create second ADR
        adr2 = manager.create(
            title="Use PostgreSQL for Transactional Data",
            context="Need reliable database for transactional workloads",
            decision="Use PostgreSQL as primary database",
            consequences="Excellent reliability and features, but requires DBA expertise",
            status="accepted",
        )

        print(f"\n✓ Created ADR-{adr2.number:03d}: {adr2.title}")

        # List all ADRs
        adrs = manager.list_adrs()
        print(f"\n✓ Total ADRs: {len(adrs)}")

        # Generate index
        index = manager.generate_index()
        print(f"\n✓ Generated ADR index ({len(index)} characters)")

        # Search
        results = manager.search("microservices")
        print(f"\n✓ Search results for 'microservices': {len(results)} found")


def demo_c4_diagrams():
    """Demonstrate C4 diagram generation."""
    print("\n" + "=" * 70)
    print("C4 DIAGRAM GENERATION DEMO")
    print("=" * 70)

    with tempfile.TemporaryDirectory() as tmpdir:
        # Create model
        model = C4Model(name="E-Commerce Platform", description="Online shopping system")

        # Add elements
        model.add_person("customer", "Customer", "Online shopper")
        model.add_person("admin", "Administrator", "System admin")

        model.add_software_system(
            "platform", "E-Commerce Platform", "Main shopping platform"
        )

        model.add_software_system(
            "payment", "Payment Gateway", "Third-party payment", external=True
        )

        # Add relationships
        model.add_relationship("customer", "platform", "Browses and purchases", "HTTPS")
        model.add_relationship("admin", "platform", "Manages products", "HTTPS")
        model.add_relationship("platform", "payment", "Processes payments", "API")

        print(f"\n✓ Created C4 model: {model.name}")
        print(f"  People: {len(model.people)}")
        print(f"  Systems: {len(model.software_systems)}")
        print(f"  Relationships: {len(model.relationships)}")

        # Generate diagrams
        generator = C4Generator()
        results = generator.generate_from_model(
            model, tmpdir, diagram_type="context", formats=["plantuml"]
        )

        print(f"\n✓ Generated diagrams:")
        for format_type, files in results.items():
            print(f"  {format_type}: {len(files)} file(s)")
            for file in files:
                file_path = Path(file)
                if file_path.exists():
                    size = file_path.stat().st_size
                    print(f"    - {file_path.name} ({size} bytes)")


def demo_fitness_functions():
    """Demonstrate fitness function testing."""
    print("\n" + "=" * 70)
    print("FITNESS FUNCTION TESTING DEMO")
    print("=" * 70)

    # Create test Python file
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write("""
class UserService:
    def get_user(self, user_id):
        return {"id": user_id, "name": "Test"}

class InvalidName:
    pass

def complex_function(x, y, z):
    if x > 0:
        if y > 0:
            if z > 0:
                return x + y + z
    return 0
""")
        test_file = Path(f.name)

    try:
        test_dir = test_file.parent

        # Create tester with rules
        tester = FitnessTester()

        # Add rules
        tester.add_rule(
            FitnessRule(
                name="Cyclomatic Complexity Check",
                type="complexity",
                severity="WARNING",
                parameters={"threshold": 5, "metric": "cyclomatic"},
            )
        )

        tester.add_rule(
            FitnessRule(
                name="Service Naming Convention",
                type="naming",
                severity="WARNING",
                parameters={"pattern": r"^[A-Z][a-zA-Z0-9]*Service$", "target": "classes"},
            )
        )

        print(f"\n✓ Created {len(tester.rules)} fitness rules")

        # Run tests
        result = tester.test(str(test_dir))

        print(f"\n✓ Test Results:")
        print(f"  Total Rules: {result.total_rules}")
        print(f"  Passed: {result.passed_rules}")
        print(f"  Failed: {result.failed_rules}")
        print(f"  Success Rate: {result.success_rate:.1f}%")
        print(f"  Violations: {result.violation_count}")
        print(f"  Execution Time: {result.execution_time:.3f}s")

        # Show violations
        if result.violations:
            print(f"\n✓ Violations:")
            for v in result.violations[:3]:
                print(f"  [{v.severity}] {v.rule_name}")
                print(f"    {v.message}")

    finally:
        test_file.unlink()


def demo_asr_tracking():
    """Demonstrate ASR tracking."""
    print("\n" + "=" * 70)
    print("ASR TRACKING DEMO")
    print("=" * 70)

    with tempfile.TemporaryDirectory() as tmpdir:
        extractor = ASRExtractor()
        tracker = ASRTracker(asr_dir=tmpdir)

        # Extract ASR from text
        asr1 = extractor.extract_from_text(
            text="System must handle 10,000 concurrent users with response time under 200ms",
            title="High Performance Requirement",
            source="Requirements Document",
        )

        if asr1:
            tracker.save_asr(asr1)
            print(f"\n✓ Extracted {asr1.id}: {asr1.title}")
            print(f"  Category: {asr1.category}")
            print(f"  Priority: {asr1.priority}")
            print(f"  Quality Attributes: {', '.join(asr1.quality_attributes or [])}")

        # Create another ASR
        asr2 = extractor.extract_from_text(
            text="System must encrypt all data at rest and in transit using AES-256",
            title="Data Encryption Requirement",
            source="Security Policy",
        )

        if asr2:
            tracker.save_asr(asr2)
            print(f"\n✓ Extracted {asr2.id}: {asr2.title}")
            print(f"  Category: {asr2.category}")

        # List ASRs
        asrs = tracker.list_asrs()
        print(f"\n✓ Total ASRs: {len(asrs)}")

        # Link to ADR
        if asrs:
            tracker.link_asr_to_adr(asrs[0].id, 1)
            print(f"\n✓ Linked {asrs[0].id} to ADR-001")

        # Generate reports
        matrix = tracker.generate_traceability_matrix()
        print(f"\n✓ Generated traceability matrix ({len(matrix)} characters)")

        summary = tracker.generate_summary_report()
        print(f"\n✓ Generated summary report ({len(summary)} characters)")


def main():
    """Run all demos."""
    print("\n" + "=" * 70)
    print("ARCHITECTURE MANAGEMENT & DOCUMENTATION PLATFORM DEMO")
    print("Issue #40: TOOL-ARCH-001")
    print("=" * 70)

    try:
        demo_adr_management()
        demo_c4_diagrams()
        demo_fitness_functions()
        demo_asr_tracking()

        print("\n" + "=" * 70)
        print("ALL DEMOS COMPLETED SUCCESSFULLY!")
        print("=" * 70)
        print("\nFor more information, see README.md")
        print("Run tests with: pytest test_arch_manager.py -v")

    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
