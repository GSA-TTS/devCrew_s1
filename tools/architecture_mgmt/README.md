# Architecture Management & Documentation Platform

**Issue #40: TOOL-ARCH-001**
**Version**: 1.0.0
**Status**: Implementation Complete

## Overview

A comprehensive architecture management platform providing ADR (Architecture Decision Record) handling, C4 diagram generation, architecture fitness functions, and ASR (Architecture Significant Requirements) tracking.

### Key Features

- **ADR Management**: Create, update, supersede, amend Architecture Decision Records
- **C4 Diagram Generation**: Generate all 4 C4 diagram levels (Context, Container, Component, Code)
- **Fitness Functions**: Define and execute architecture validation rules
- **ASR Tracking**: Extract and track Architecture Significant Requirements
- **Traceability**: Link ADRs to issues, PRs, and ASRs
- **Template System**: Multiple ADR templates for different scenarios

## Installation

### Prerequisites

- Python 3.10 or higher
- Git (for version control)
- Optional: Structurizr CLI for advanced C4 diagram generation
- Optional: PlantUML for diagram rendering

### Install Dependencies

```bash
cd /Users/tamnguyen/Documents/GitHub/devCrew_s1

# Install Python dependencies
pip install -r issue_40_requirements.txt

# Make the CLI executable
chmod +x issue_40_arch_manager.py
```

### Optional: Install Structurizr CLI

```bash
# macOS
brew install structurizr-cli

# Linux
wget https://github.com/structurizr/cli/releases/latest/download/structurizr-cli.zip
unzip structurizr-cli.zip
```

### Optional: Install PlantUML

```bash
# macOS
brew install plantuml

# Or use JAR file
wget https://sourceforge.net/projects/plantuml/files/plantuml.jar/download -O plantuml.jar
```

## Quick Start

### Initialize Project

```bash
# Initialize architecture documentation structure
python issue_40_arch_manager.py init --project-dir .

# Check status
python issue_40_arch_manager.py status
```

### Create Your First ADR

```bash
python issue_40_arch_manager.py adr create \
  --title "Use Microservices Architecture" \
  --context "We need to design a scalable backend that supports independent service deployment" \
  --decision "Adopt microservices architecture with service mesh" \
  --consequences "Increased operational complexity but better scalability and team autonomy" \
  --status accepted \
  --deciders "Architecture Team, Tech Lead"
```

### List ADRs

```bash
# List all ADRs
python issue_40_arch_manager.py adr list

# Filter by status
python issue_40_arch_manager.py adr list --status accepted
```

### Generate ADR Index

```bash
python issue_40_arch_manager.py adr index --output docs/adr/INDEX.md
```

## Usage Guide

### ADR Management

#### Create ADR

```bash
python issue_40_arch_manager.py adr create \
  --title "ADR Title" \
  --context "Problem context and background" \
  --decision "The decision made" \
  --consequences "Positive and negative consequences" \
  --status proposed \
  --issue "https://github.com/owner/repo/issues/123"
```

#### Supersede ADR

```bash
python issue_40_arch_manager.py adr supersede \
  --adr-number 5 \
  --title "New Decision" \
  --context "Updated context" \
  --decision "New decision"
```

#### Search ADRs

```python
from issue_40_adr_manager import ADRManager

manager = ADRManager(adr_dir="docs/adr")
results = manager.search("microservices")
for adr in results:
    print(f"ADR-{adr.number:03d}: {adr.title}")
```

### C4 Diagram Generation

#### From YAML Model

Create a model file `model.yml`:

```yaml
name: "DevCrew Platform"
description: "Architecture documentation platform"

people:
  - id: developer
    name: "Developer"
    description: "Software developer using the platform"

systems:
  - id: platform
    name: "DevCrew Platform"
    description: "Architecture management system"

relationships:
  - source: developer
    target: platform
    description: "Uses"
    technology: "CLI/API"
```

Generate diagrams:

```bash
python issue_40_arch_manager.py c4 generate \
  --model model.yml \
  --type context \
  --output-dir diagrams \
  --format png --format svg
```

#### From Python Code

```python
from issue_40_c4_generator import C4Generator, C4Model

# Create model
model = C4Model(name="My System", description="System description")
model.add_person("user", "User", "System user")
model.add_software_system("app", "Application", "Main app")
model.add_relationship("user", "app", "Uses", "HTTPS")

# Generate diagrams
generator = C4Generator()
results = generator.generate_from_model(
    model,
    output_dir="diagrams",
    diagram_type="context",
    formats=["png", "plantuml"]
)
```

### Architecture Fitness Functions

#### Create Rules File

Create `fitness-rules.yml`:

```yaml
rules:
  - name: "Cyclomatic Complexity Check"
    type: "complexity"
    severity: "ERROR"
    enabled: true
    parameters:
      threshold: 10
      metric: "cyclomatic"

  - name: "Service Class Naming"
    type: "naming"
    severity: "WARNING"
    enabled: true
    parameters:
      pattern: "^[A-Z][a-zA-Z0-9]*Service$"
      target: "classes"

  - name: "Layered Architecture"
    type: "dependency"
    severity: "ERROR"
    enabled: true
    parameters:
      allowed_layers:
        - "presentation"
        - "business"
        - "data"

  - name: "Required Directories"
    type: "structure"
    severity: "WARNING"
    enabled: true
    parameters:
      required_directories:
        - "src"
        - "tests"
        - "docs"
```

#### Run Fitness Tests

```bash
python issue_40_arch_manager.py fitness test \
  --rules fitness-rules.yml \
  --codebase ./src \
  --report fitness-report.md \
  --fail-on-error
```

#### Python API

```python
from issue_40_fitness_functions import FitnessTester

# Load and run tests
tester = FitnessTester(rules_file="fitness-rules.yml")
result = tester.test(codebase_path="./src")

# Print results
print(f"Total Rules: {result.total_rules}")
print(f"Passed: {result.passed_rules}")
print(f"Failed: {result.failed_rules}")
print(f"Success Rate: {result.success_rate:.1f}%")

# Get violations by severity
errors = result.get_violations_by_severity("ERROR")
for violation in errors:
    print(f"  {violation.rule_name}: {violation.message}")

# Generate report
report = tester.generate_report(result, "fitness-report.md")
```

### ASR Tracking

#### Extract ASR from GitHub Issue

```bash
export GITHUB_TOKEN="your_github_token"

python issue_40_arch_manager.py asr extract \
  --repo GSA-TTS/devCrew_s1 \
  --issue 40 \
  --asr-dir docs/asr
```

#### Extract ASR from Text

```python
from issue_40_asr_tracker import ASRExtractor, ASRTracker

extractor = ASRExtractor()
asr = extractor.extract_from_text(
    text="System must handle 10,000 concurrent users with <200ms response time",
    title="High Performance Requirement",
    source="Requirements Document"
)

tracker = ASRTracker(asr_dir="docs/asr")
tracker.save_asr(asr)
```

#### List ASRs

```bash
# List all ASRs
python issue_40_arch_manager.py asr list

# Filter by category
python issue_40_arch_manager.py asr list --category performance

# Filter by status
python issue_40_arch_manager.py asr list --status identified
```

#### Link ASR to ADR

```bash
python issue_40_arch_manager.py asr link \
  --asr-id ASR-001 \
  --adr-number 5
```

#### Generate Traceability Matrix

```bash
python issue_40_arch_manager.py asr matrix \
  --output docs/asr/TRACEABILITY.md
```

## File Structure

```
project/
├── docs/
│   ├── adr/                    # Architecture Decision Records
│   │   ├── ADR-001.md
│   │   ├── ADR-002.md
│   │   └── INDEX.md
│   ├── asr/                    # Architecture Significant Requirements
│   │   ├── ASR-001.md
│   │   ├── ASR-001.yml
│   │   └── TRACEABILITY.md
│   └── architecture/
│       ├── diagrams/           # C4 diagrams
│       │   ├── context.png
│       │   └── context.puml
│       └── models/             # Architecture models
│           └── system.yml
├── issue_40_arch_manager.py    # Main CLI
├── issue_40_adr_manager.py     # ADR management
├── issue_40_c4_generator.py    # C4 diagram generation
├── issue_40_fitness_functions.py  # Fitness testing
├── issue_40_asr_tracker.py     # ASR tracking
├── issue_40_templates/         # ADR templates
│   ├── default.md.j2
│   ├── microservices.md.j2
│   └── technology.md.j2
└── issue_40_requirements.txt   # Dependencies
```

## ADR Templates

The platform includes multiple ADR templates:

### Default Template
General-purpose template for most decisions.

### Microservices Template
Specialized template for microservices architecture decisions with:
- Service boundaries
- Deployment strategy
- Communication patterns

### Technology Template
Template for technology selection decisions with:
- Evaluation matrix
- Selection criteria
- Migration plan

### Using Templates

```python
from issue_40_adr_manager import ADRManager

manager = ADRManager(
    adr_dir="docs/adr",
    template_dir="issue_40_templates"
)

adr = manager.create(
    title="Use Microservices",
    context="Need scalability",
    decision="Adopt microservices",
    consequences="Better scalability",
    template="microservices"  # Use microservices template
)
```

## Examples

### Example 1: Complete ADR Workflow

```python
from issue_40_adr_manager import ADRManager

# Initialize manager
manager = ADRManager(adr_dir="docs/adr")

# Create initial ADR
adr1 = manager.create(
    title="Use Event-Driven Architecture",
    context="Need asynchronous communication between services",
    decision="Adopt event-driven architecture with message broker",
    consequences="Better decoupling but increased complexity",
    status="proposed",
    decision_drivers=[
        "Service decoupling",
        "Async processing requirements",
        "Scalability needs"
    ],
    considered_options=[
        "Event-driven architecture",
        "Request/response pattern",
        "Direct service calls"
    ]
)

# Later, supersede with updated decision
adr2 = manager.supersede(
    adr_number=adr1.number,
    new_title="Use Event-Driven Architecture with Kafka",
    new_context="Event-driven architecture chosen, need specific technology",
    new_decision="Use Apache Kafka as message broker"
)

# Generate index
manager.generate_index(output_file="docs/adr/INDEX.md")
```

### Example 2: C4 Diagram Generation

```python
from issue_40_c4_generator import C4Generator, C4Model

# Build model
model = C4Model(name="E-Commerce Platform")

# Add actors
model.add_person("customer", "Customer", "Online shopper")
model.add_person("admin", "Admin", "System administrator")

# Add systems
model.add_software_system(
    "platform",
    "E-Commerce Platform",
    "Online shopping platform"
)

# Add relationships
model.add_relationship("customer", "platform", "Browses and purchases", "HTTPS")
model.add_relationship("admin", "platform", "Manages", "HTTPS")

# Generate diagrams
generator = C4Generator()
results = generator.generate_from_model(
    model,
    output_dir="docs/architecture/diagrams",
    diagram_type="context",
    formats=["png", "svg", "plantuml"]
)

print(f"Generated {len(results['png'])} PNG diagrams")
```

### Example 3: Fitness Function Validation

```python
from issue_40_fitness_functions import FitnessTester, FitnessRule

# Create tester
tester = FitnessTester()

# Add custom rules
tester.add_rule(FitnessRule(
    name="API Response Time",
    type="complexity",
    severity="ERROR",
    parameters={
        "threshold": 15,
        "metric": "cyclomatic"
    }
))

tester.add_rule(FitnessRule(
    name="Controller Naming",
    type="naming",
    severity="WARNING",
    parameters={
        "pattern": r"^[A-Z][a-zA-Z0-9]*Controller$",
        "target": "classes"
    }
))

# Run tests
result = tester.test(codebase_path="./src")

# Handle results
if result.violation_count > 0:
    print(f"Found {result.violation_count} violations")

    # Generate detailed report
    report = tester.generate_report(result, "fitness-report.md")

    # Get critical errors
    errors = result.get_violations_by_severity("ERROR")
    for error in errors:
        print(f"ERROR: {error.message} in {error.file_path}")
```

### Example 4: ASR Management

```python
from issue_40_asr_tracker import ASRExtractor, ASRTracker

# Extract from GitHub
extractor = ASRExtractor(github_token="your_token")
asr = extractor.extract_from_github_issue("owner/repo", 123)

# Save ASR
tracker = ASRTracker(asr_dir="docs/asr")
tracker.save_asr(asr)

# Link to ADR
tracker.link_asr_to_adr(asr.id, adr_number=5)

# Update status
tracker.update_status(asr.id, "addressed")

# Generate reports
tracker.generate_traceability_matrix("docs/asr/TRACEABILITY.md")
tracker.generate_summary_report("docs/asr/SUMMARY.md")
```

## Testing

### Run All Tests

```bash
cd /Users/tamnguyen/Documents/GitHub/devCrew_s1

# Run tests with pytest
pytest issue_40_test_arch_manager.py -v

# Run with coverage
pytest issue_40_test_arch_manager.py -v --cov=. --cov-report=html
```

### Test Coverage

The test suite includes:
- ADR Manager: Create, read, update, supersede, list, search
- C4 Generator: Model creation, diagram generation, YAML parsing
- Fitness Functions: Complexity analysis, naming checks, dependency validation
- ASR Tracker: Extract, save, load, link, traceability
- Integration: End-to-end workflows

Target coverage: 85%+

## Performance

### Benchmarks

- **ADR Creation**: <100ms
- **ADR Index Generation**: <1s for 100 ADRs
- **C4 Diagram Generation**: <10s (depends on PlantUML)
- **Fitness Test Execution**: <30s for medium codebase (10K LOC)
- **ASR Extraction**: <5s per GitHub issue

### Optimization Tips

1. Use PlantUML JAR for faster diagram generation
2. Cache fitness test results for unchanged files
3. Index ADRs for faster searching
4. Batch ASR extraction for multiple issues

## Troubleshooting

### PlantUML Not Found

```bash
# Install PlantUML
brew install plantuml  # macOS
apt-get install plantuml  # Ubuntu

# Or download JAR
wget https://sourceforge.net/projects/plantuml/files/plantuml.jar
```

### GitHub Token Issues

```bash
# Set token as environment variable
export GITHUB_TOKEN="your_personal_access_token"

# Or pass directly
python issue_40_arch_manager.py asr extract \
  --token "your_token" \
  --repo owner/repo \
  --issue 123
```

### Import Errors

```bash
# Reinstall dependencies
pip install -r issue_40_requirements.txt --upgrade
```

## Protocol Coverage

This implementation supports **10 protocols** (12% of devCrew_s1 protocols):

1. **P-ADR-CREATION**: Architecture Decision Record Creation
2. **P-ARCH-FITNESS**: Architecture Fitness Function Validation
3. **P-ARCH-INTEGRATION**: Architecture Integration Protocols
4. **P-ASR-ADR-ALIGNMENT**: ASR to ADR Alignment
5. **P-ASR-EXTRACTION**: Architecture Significant Requirement Extraction
6. **P-C4-VISUALIZATION**: C4 Architecture Diagrams
7. **P-PATTERN-MANAGEMENT**: Architectural Pattern Management
8. **P-TECH-RADAR**: Technology Radar Evaluation
9. **QG-ARCHITECTURE-REVIEW**: Architecture Review Quality Gate
10. **P-ARCH-VALIDATION**: Architecture Validation

## Contributing

### Code Quality Standards

All code follows project standards:
- Black formatting (line length: 88)
- isort for import organization
- flake8 for linting
- mypy for type checking
- bandit for security scanning

### Pre-commit Checks

```bash
# Install pre-commit
pip install pre-commit

# Run all checks
black issue_40_*.py
isort issue_40_*.py
flake8 issue_40_*.py
mypy issue_40_*.py --ignore-missing-imports
bandit -r issue_40_*.py
```

## License

This implementation follows the devCrew_s1 project license.

## Related Documentation

- [Issue #40](https://github.com/GSA-TTS/devCrew_s1/issues/40)
- [Architecture Decision Records (ADRs)](https://adr.github.io/)
- [C4 Model](https://c4model.com/)
- [Structurizr](https://structurizr.com/)
- [PlantUML](https://plantuml.com/)

## Support

For issues or questions:
1. Check this README
2. Review test cases in `issue_40_test_arch_manager.py`
3. Open an issue in the devCrew_s1 repository

---

**Implementation Status**: Complete
**Version**: 1.0.0
**Last Updated**: 2025-11-20
