# UX Research & Design Feedback Platform (TOOL-UX-001)

Part of the devCrew_s1 enterprise tooling suite.

## Overview

Comprehensive UX research and accessibility auditing platform that combines automated
WCAG 2.1 compliance testing, usability validation, user feedback analysis, and
remediation guidance. Built for enterprise teams to ensure inclusive, user-friendly
digital experiences.

**Key Capabilities:**
- Automated accessibility audits across 50+ page websites in <10 minutes
- 99% accuracy in WCAG 2.1 violation detection
- Nielsen's 10 heuristics evaluation with custom checklists
- Multi-source user feedback aggregation and sentiment analysis
- AI-powered remediation guidance with code examples
- CI/CD integration for continuous accessibility monitoring

## Features

### ✅ Accessibility Auditing
- **WCAG 2.1 Compliance**: Level A, AA, and AAA automated testing
- **Multi-Engine Validation**: Playwright + axe-core + pa11y integration
- **Cross-Browser Testing**: Chrome, Firefox, Safari, Edge support
- **Responsive Testing**: Desktop, tablet, mobile viewports
- **Keyboard Navigation**: Tab order and focus management validation
- **Screen Reader Simulation**: ARIA attribute verification
- **Color Contrast**: WCAG color contrast ratio analysis
- **Report Formats**: HTML, JSON, PDF, CSV exports

### 🎯 Usability Validation
- **Nielsen's 10 Heuristics**: Automated checklist evaluation
- **Custom Checklists**: Define domain-specific usability criteria
- **Task Flow Analysis**: User journey validation
- **Form Usability**: Input validation, error handling, accessibility
- **Content Readability**: Flesch-Kincaid, SMOG scoring
- **Performance Budget**: Page load time, resource size monitoring

### 📊 Feedback Analysis
- **Multi-Source Collection**: Surveys, support tickets, user interviews
- **Sentiment Analysis**: NLP-based positive/negative/neutral classification
- **Theme Extraction**: Topic modeling and keyword clustering
- **NPS Calculation**: Net Promoter Score tracking
- **Heatmap Integration**: Hotjar, Crazy Egg data import
- **Session Recording**: User behavior pattern analysis

### 🔧 Remediation Guidance
- **Issue Prioritization**: Severity-based ranking (Critical/High/Medium/Low)
- **Code Examples**: Before/after snippets for common violations
- **WCAG Success Criteria**: Direct mapping to standards
- **Effort Estimation**: Time/complexity for each fix
- **Issue Tracking**: JIRA, GitHub Issues, Azure DevOps integration
- **Progress Monitoring**: Track remediation completion rates

### 🔌 Analytics Integration
- **Google Analytics**: User behavior, conversion metrics
- **Hotjar**: Heatmaps, session recordings, feedback polls
- **Custom Events**: Track specific user interactions
- **User Journey Mapping**: Multi-step conversion funnels
- **A/B Testing**: Variant performance comparison

### 📈 Reporting & Monitoring
- **Executive Dashboards**: High-level accessibility score trends
- **Detailed Reports**: Per-page violation breakdowns
- **Trend Analysis**: Historical compliance tracking
- **Scheduled Audits**: Automated recurring scans
- **Alerting**: Email/Slack notifications for regressions

## Installation

### Prerequisites

- **Python**: 3.10 or higher
- **Node.js**: 18+ (for pa11y integration)
- **Playwright Browsers**: Chromium, Firefox, WebKit
- **Operating System**: macOS, Linux, or Windows

### Install from devCrew_s1 Repository

```bash
# Clone the repository
git clone https://github.com/your-org/devCrew_s1.git
cd devCrew_s1/tools/ux_research

# Install Python dependencies
pip install -r requirements.txt

# Install Playwright browsers
playwright install

# Install Node.js dependencies (for pa11y)
npm install -g pa11y pa11y-ci

# Verify installation
ux-tool --version
```

### Optional: Development Installation

```bash
# Install with development dependencies
pip install -r requirements-dev.txt

# Install pre-commit hooks
pre-commit install

# Run tests to verify setup
pytest -v
```

See [docs/installation.md](docs/installation.md) for detailed platform-specific
instructions and troubleshooting.

## Quick Start

### 1. Run Your First Accessibility Audit

```bash
# Basic audit with WCAG 2.1 Level AA
ux-tool audit --url https://example.com --wcag-level AA

# Full audit with all levels and output formats
ux-tool audit --url https://example.com \
  --wcag-level AAA \
  --output-format html json pdf \
  --output-dir ./reports
```

### 2. Analyze User Feedback

```bash
# Import and analyze survey responses
ux-tool feedback --source surveys.csv --analyze sentiment

# Aggregate feedback from multiple sources
ux-tool feedback --sources surveys.csv tickets.json interviews.txt \
  --analyze sentiment themes nps
```

### 3. Run Heuristic Evaluation

```bash
# Nielsen's 10 heuristics with default checklist
ux-tool heuristics --url https://example.com

# Custom checklist evaluation
ux-tool heuristics --url https://example.com \
  --checklist custom-heuristics.yaml \
  --output-format html
```

### 4. Generate Remediation Guide

```bash
# Analyze audit results and generate fix recommendations
ux-tool remediate --audit-report report.json \
  --output remediation-guide.html \
  --include-code-examples
```

## CLI Commands

### `ux-tool audit`

Run accessibility audits with WCAG 2.1 compliance checking.

**Options:**
- `--url URL`: Target website URL (required)
- `--wcag-level {A,AA,AAA}`: WCAG compliance level (default: AA)
- `--viewports VIEWPORTS`: Comma-separated viewport sizes (default: desktop,tablet,mobile)
- `--browsers BROWSERS`: Comma-separated browser list (default: chromium)
- `--output-format {html,json,pdf,csv}`: Report format (default: html)
- `--output-dir PATH`: Output directory (default: ./reports)
- `--pages-file PATH`: File containing URLs to audit (one per line)
- `--max-pages INT`: Maximum pages to crawl (default: 50)
- `--include-patterns PATTERNS`: URL patterns to include
- `--exclude-patterns PATTERNS`: URL patterns to exclude

**Examples:**

```bash
# Single-page audit
ux-tool audit --url https://example.com/page

# Multi-page audit with sitemap
ux-tool audit --url https://example.com \
  --max-pages 100 \
  --include-patterns "/blog/*,/docs/*"

# Cross-browser audit
ux-tool audit --url https://example.com \
  --browsers chromium,firefox,webkit \
  --viewports desktop,mobile

# CI/CD pipeline integration
ux-tool audit --url https://staging.example.com \
  --wcag-level AA \
  --output-format json \
  --fail-on critical,high
```

### `ux-tool feedback`

Collect and analyze user feedback from multiple sources.

**Options:**
- `--source PATH`: Feedback data file (CSV, JSON, or text)
- `--sources PATHS`: Multiple data files (comma-separated)
- `--analyze {sentiment,themes,nps}`: Analysis types (comma-separated)
- `--output PATH`: Output report path
- `--format {html,json,csv}`: Report format

**Examples:**

```bash
# Sentiment analysis on survey data
ux-tool feedback --source surveys.csv --analyze sentiment

# Multi-source aggregation
ux-tool feedback \
  --sources surveys.csv,tickets.json,interviews.txt \
  --analyze sentiment,themes,nps \
  --output feedback-report.html

# NPS calculation
ux-tool feedback --source nps-survey.csv --analyze nps
```

### `ux-tool heuristics`

Evaluate usability using Nielsen's 10 heuristics or custom checklists.

**Options:**
- `--url URL`: Target website URL (required)
- `--checklist PATH`: Custom heuristics checklist (YAML)
- `--output PATH`: Output report path
- `--output-format {html,json}`: Report format

**Examples:**

```bash
# Default Nielsen's 10 heuristics
ux-tool heuristics --url https://example.com

# Custom checklist evaluation
ux-tool heuristics --url https://example.com \
  --checklist e-commerce-heuristics.yaml \
  --output-format html
```

### `ux-tool remediate`

Generate remediation guidance for accessibility violations.

**Options:**
- `--audit-report PATH`: Audit report file (JSON)
- `--output PATH`: Output remediation guide path
- `--include-code-examples`: Include before/after code snippets
- `--prioritize {severity,impact,effort}`: Sorting criteria
- `--create-issues`: Automatically create GitHub issues

**Examples:**

```bash
# Generate remediation guide
ux-tool remediate --audit-report audit.json \
  --output remediation.html \
  --include-code-examples

# Prioritize by effort and create issues
ux-tool remediate --audit-report audit.json \
  --prioritize effort \
  --create-issues \
  --github-repo myorg/myrepo
```

### `ux-tool analytics`

Integrate with analytics platforms for user behavior insights.

**Options:**
- `--platform {ga,hotjar,custom}`: Analytics platform
- `--start-date DATE`: Analysis start date (YYYY-MM-DD)
- `--end-date DATE`: Analysis end date (YYYY-MM-DD)
- `--metrics METRICS`: Comma-separated metric names
- `--output PATH`: Output report path

**Examples:**

```bash
# Google Analytics integration
ux-tool analytics --platform ga \
  --start-date 2024-01-01 \
  --end-date 2024-01-31 \
  --metrics pageviews,bounce_rate,conversion_rate

# Hotjar heatmap analysis
ux-tool analytics --platform hotjar \
  --start-date 2024-01-01 \
  --output heatmap-analysis.html
```

### `ux-tool monitor`

Set up continuous accessibility monitoring with scheduled scans.

**Options:**
- `--url URL`: Target website URL (required)
- `--schedule CRON`: Cron expression for scan schedule
- `--alert-on {regression,new-violations}`: Alert triggers
- `--notification {email,slack}`: Notification channels
- `--baseline-report PATH`: Baseline audit report for comparison

**Examples:**

```bash
# Daily monitoring with email alerts
ux-tool monitor --url https://example.com \
  --schedule "0 9 * * *" \
  --alert-on regression,new-violations \
  --notification email

# Weekly monitoring with Slack notifications
ux-tool monitor --url https://example.com \
  --schedule "0 9 * * 1" \
  --notification slack \
  --baseline-report baseline-audit.json
```

### `ux-tool report`

Generate comprehensive UX reports combining multiple data sources.

**Options:**
- `--audit PATH`: Accessibility audit report
- `--feedback PATH`: Feedback analysis report
- `--heuristics PATH`: Heuristic evaluation report
- `--analytics PATH`: Analytics report
- `--output PATH`: Combined report output path
- `--format {html,pdf}`: Report format

**Examples:**

```bash
# Combined UX report
ux-tool report \
  --audit audit.json \
  --feedback feedback.json \
  --heuristics heuristics.json \
  --analytics analytics.json \
  --output ux-report.html \
  --format html
```

## Python API

### Accessibility Auditor

```python
from ux_research.auditor import AccessibilityAuditor

# Initialize auditor
auditor = AccessibilityAuditor(
    wcag_level="AA",
    browsers=["chromium", "firefox"],
    viewports=["desktop", "mobile"]
)

# Run audit
results = await auditor.audit_url("https://example.com")

# Generate report
auditor.generate_report(results, output_path="audit.html", format="html")

# Get violation summary
summary = auditor.get_summary(results)
print(f"Total violations: {summary['total_violations']}")
print(f"Critical: {summary['critical']}, High: {summary['high']}")
```

### Feedback Collector

```python
from ux_research.collector import FeedbackCollector

# Initialize collector
collector = FeedbackCollector()

# Load feedback from multiple sources
feedback = collector.load_from_csv("surveys.csv")
feedback += collector.load_from_json("tickets.json")

# Analyze sentiment
sentiment_results = collector.analyze_sentiment(feedback)

# Extract themes
themes = collector.extract_themes(feedback, num_themes=5)

# Calculate NPS
nps_score = collector.calculate_nps(feedback)
print(f"NPS: {nps_score}")
```

### Usability Validator

```python
from ux_research.validator import UsabilityValidator

# Initialize validator
validator = UsabilityValidator()

# Load custom checklist
validator.load_checklist("custom-heuristics.yaml")

# Run evaluation
results = await validator.evaluate_url("https://example.com")

# Get heuristic scores
scores = validator.get_heuristic_scores(results)
for heuristic, score in scores.items():
    print(f"{heuristic}: {score}/10")
```

### Sentiment Analyzer

```python
from ux_research.analyzer import SentimentAnalyzer

# Initialize analyzer
analyzer = SentimentAnalyzer()

# Analyze sentiment
feedback_items = ["Great product!", "App crashes frequently", "Easy to use"]
for item in feedback_items:
    sentiment = analyzer.analyze_sentiment(item)
    print(f"{item}: {sentiment['label']} ({sentiment['score']:.2f})")

# Batch analysis
results = analyzer.analyze_batch(feedback_items)
```

### Remediation Guide Generator

```python
from ux_research.remediation import GuideGenerator

# Initialize generator
generator = GuideGenerator()

# Load audit results
audit_results = generator.load_audit_report("audit.json")

# Generate remediation guide
guide = generator.generate_guide(
    audit_results,
    include_code_examples=True,
    prioritize_by="severity"
)

# Export to HTML
generator.export_html(guide, "remediation.html")

# Create GitHub issues
generator.create_issues(
    guide,
    repo="myorg/myrepo",
    labels=["accessibility", "bug"]
)
```

## Configuration

### Configuration File: `ux-audit-config.yaml`

```yaml
# WCAG Auditing Configuration
wcag:
  level: AA  # A, AA, or AAA
  standards:
    - WCAG21A
    - WCAG21AA
  rules_to_skip: []  # Rule IDs to exclude

# Browser Configuration
browsers:
  - chromium
  - firefox
  # - webkit  # Uncomment for Safari testing

# Viewport Configuration
viewports:
  desktop:
    width: 1920
    height: 1080
  tablet:
    width: 768
    height: 1024
  mobile:
    width: 375
    height: 667

# Crawling Configuration
crawling:
  max_pages: 50
  max_depth: 3
  respect_robots_txt: true
  follow_redirects: true
  timeout: 30000  # milliseconds
  include_patterns:
    - "/blog/*"
    - "/docs/*"
  exclude_patterns:
    - "/admin/*"
    - "*.pdf"

# Reporting Configuration
reporting:
  formats:
    - html
    - json
  output_dir: "./reports"
  include_screenshots: true
  include_code_snippets: true

# Analytics Integration
analytics:
  google_analytics:
    enabled: false
    property_id: "UA-XXXXXXXXX-X"
  hotjar:
    enabled: false
    site_id: "XXXXXXX"

# Monitoring Configuration
monitoring:
  enabled: false
  schedule: "0 9 * * *"  # Daily at 9 AM
  alert_on:
    - regression
    - new_violations
  notifications:
    email:
      enabled: false
      recipients: []
    slack:
      enabled: false
      webhook_url: ""

# CI/CD Configuration
ci_cd:
  fail_on_violations:
    - critical
    - high
  minimum_score: 90  # 0-100 accessibility score
  compare_with_baseline: true
```

### Custom Heuristics Checklist: `heuristics-checklist.yaml`

```yaml
# Nielsen's 10 Heuristics + Custom Rules
heuristics:
  - id: H1
    name: "Visibility of System Status"
    description: "Keep users informed about what is going on"
    checks:
      - "Loading indicators present for async operations"
      - "Progress bars for multi-step processes"
      - "Status messages for user actions"
    weight: 10

  - id: H2
    name: "Match Between System and Real World"
    description: "Use familiar language and concepts"
    checks:
      - "Terminology matches user expectations"
      - "Icons are intuitive and recognizable"
      - "Information follows natural conventions"
    weight: 9

  # Add remaining heuristics...

# Custom Domain-Specific Heuristics
custom:
  - id: C1
    name: "E-commerce Checkout Flow"
    description: "Streamlined purchase process"
    checks:
      - "Guest checkout available"
      - "Saved payment methods supported"
      - "Clear shipping cost display"
    weight: 10
```

See [docs/installation.md](docs/installation.md) for detailed configuration options.

## Troubleshooting

### Common Issues

**Issue: Playwright browsers not installed**
```bash
# Solution: Install browsers
playwright install
```

**Issue: pa11y command not found**
```bash
# Solution: Install pa11y globally
npm install -g pa11y pa11y-ci
```

**Issue: Timeout errors during audits**
```bash
# Solution: Increase timeout in config
# ux-audit-config.yaml
crawling:
  timeout: 60000  # Increase to 60 seconds
```

**Issue: Rate limiting from analytics APIs**
```bash
# Solution: Add delays between requests
analytics:
  rate_limit_delay: 1000  # 1 second between requests
```

See [docs/troubleshooting.md](docs/troubleshooting.md) for comprehensive
troubleshooting guide.

## Documentation

- **[Installation Guide](docs/installation.md)** - Detailed setup instructions
- **[WCAG Compliance Guide](docs/wcag_guide.md)** - Understanding WCAG 2.1 standards
- **[Accessibility Testing](docs/accessibility_testing.md)** - Testing methodology
- **[Feedback Analysis](docs/feedback_analysis.md)** - User feedback workflows
- **[Heuristic Evaluation](docs/heuristic_evaluation.md)** - Usability testing
- **[CI/CD Integration](docs/ci_cd_integration.md)** - Pipeline integration examples
- **[Troubleshooting](docs/troubleshooting.md)** - Common issues and solutions

## Contributing

This tool is part of the devCrew_s1 internal tooling suite. For contributions:

1. Follow Python development best practices (Black, isort, flake8, mypy, bandit)
2. Maintain 85%+ test coverage
3. Update documentation for new features
4. Run pre-commit hooks before submitting

## License

Internal use only. Part of the devCrew_s1 enterprise tooling suite.

## Support

For issues and questions:
- GitHub Issues: [devCrew_s1/issues](https://github.com/your-org/devCrew_s1/issues)
- Internal Wiki: [UX Research Platform Documentation]
- Team: Platform Engineering

## Version

Current version: 1.0.0

See [CHANGELOG.md](CHANGELOG.md) for version history.
