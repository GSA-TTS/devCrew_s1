# UX Research & Design Feedback Platform CLI

Command-line interface for the UX Research & Design Feedback Platform, providing accessibility auditing, usability validation, and user feedback analysis.

## Installation

```bash
# Install dependencies
pip install -r ../requirements.txt

# Or install the package
pip install -e ..
```

## Usage

### Basic Commands

```bash
# Show help
ux-tool --help

# Show specific command help
ux-tool audit --help
```

### Accessibility Audit

```bash
# Basic audit
ux-tool audit --url https://example.com

# WCAG AAA audit with multiple browsers
ux-tool audit --url https://example.com \
  --wcag-level AAA \
  --browsers chromium firefox webkit \
  --output audit-results.json

# Dry run (simulate without execution)
ux-tool audit --url https://example.com --dry-run
```

### Feedback Analysis

```bash
# Analyze sentiment
ux-tool feedback --source surveys.csv --analyze sentiment

# Multiple analysis types
ux-tool feedback --source feedback.csv \
  --analyze sentiment \
  --analyze topics \
  --analyze nps \
  --output feedback-analysis.json
```

### Usability Heuristics Evaluation

```bash
# Evaluate using Nielsen's 10 heuristics
ux-tool heuristics --url https://example.com

# Use custom checklist
ux-tool heuristics --url https://example.com \
  --checklist custom-heuristics.yaml \
  --output heuristics-report.html
```

### Analytics Analysis

```bash
# Analyze Google Analytics data
ux-tool analyze --platform google_analytics \
  --start-date 2025-01-01 \
  --end-date 2025-01-31 \
  --metrics bounce_rate conversion_rate

# Hotjar analysis
ux-tool analyze --platform hotjar \
  --start-date 2025-01-01 \
  --end-date 2025-01-31
```

### Report Generation

```bash
# Generate HTML report
ux-tool report --type accessibility \
  --output accessibility-report.html

# Generate comprehensive report with data
ux-tool report --type comprehensive \
  --data-dir ./audit-results \
  --output comprehensive-report.html \
  --format html

# Generate PDF report (requires WeasyPrint)
ux-tool report --type accessibility \
  --output report.html \
  --format pdf
```

### Continuous Monitoring

```bash
# Basic monitoring
ux-tool monitor --url https://example.com \
  --interval 3600 \
  --max-runs 24

# With alerting
ux-tool monitor --url https://example.com \
  --threshold-critical 5 \
  --threshold-serious 10 \
  --alert-email admin@example.com \
  --webhook https://hooks.slack.com/services/XXX
```

### Configuration Management

```bash
# Show current configuration
ux-tool config --action show

# Initialize new configuration
ux-tool config --action init \
  --config-file my-config.yaml

# Validate configuration
ux-tool config --action validate

# Update configuration value
ux-tool config --action set \
  --key audit.wcag_level \
  --value AAA
```

## Configuration

The CLI uses YAML configuration files. Default configuration file: `ux-audit-config.yaml`

### Main Configuration File (`ux-audit-config.yaml`)

```yaml
audit:
  wcag_level: "AA"
  browsers: ["chromium", "firefox"]
  viewports:
    mobile: [375, 667]
    tablet: [768, 1024]
    desktop: [1920, 1080]

feedback:
  sources:
    surveys: "surveys.csv"
  min_confidence: 0.7

analytics:
  google_analytics:
    property_id: "123456"
```

### Heuristics Checklist (`heuristics-checklist.yaml`)

Contains Nielsen's 10 usability heuristics with automated and manual checks.

### Feedback Sources (`feedback-sources.yaml`)

Configuration for various feedback platforms (Hotjar, UserTesting, Zendesk, etc.).

## Global Options

```bash
# Use custom configuration file
ux-tool --config custom-config.yaml audit --url https://example.com

# Verbose output
ux-tool --verbose audit --url https://example.com

# Quiet mode (suppress non-essential output)
ux-tool --quiet audit --url https://example.com
```

## Output Formats

Supported output formats:
- **JSON**: Machine-readable format
- **HTML**: Human-readable reports with styling
- **PDF**: Print-ready documents (requires WeasyPrint)
- **YAML**: Configuration-friendly format
- **Markdown**: Documentation-friendly format

## Exit Codes

- **0**: Success
- **1**: Error or critical issues found
- **2**: Invalid arguments or configuration

## Examples

### Complete Workflow

```bash
# 1. Run accessibility audit
ux-tool audit --url https://example.com \
  --wcag-level AA \
  --output audit.json

# 2. Evaluate usability heuristics
ux-tool heuristics --url https://example.com \
  --output heuristics.json

# 3. Analyze feedback
ux-tool feedback --source surveys.csv \
  --analyze sentiment topics nps \
  --output feedback.json

# 4. Generate comprehensive report
ux-tool report --type comprehensive \
  --data-dir . \
  --output final-report.html
```

### CI/CD Integration

```yaml
# .github/workflows/ux-audit.yml
name: UX Audit
on: [push]
jobs:
  audit:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Run UX audit
        run: |
          pip install -r requirements.txt
          ux-tool audit --url ${{ secrets.DEPLOY_URL }} \
            --output audit-results.json
          ux-tool report --type accessibility \
            --data-dir . \
            --output audit-report.html
      - name: Upload results
        uses: actions/upload-artifact@v2
        with:
          name: ux-audit-results
          path: |
            audit-results.json
            audit-report.html
```

## Testing

Run the test suite:

```bash
# Run all tests
pytest test_ux_cli.py -v

# Run with coverage
pytest test_ux_cli.py --cov=ux_cli --cov-report=html

# Run specific test class
pytest test_ux_cli.py::TestAuditCommand -v
```

## Architecture

```
cli/
├── __init__.py           # Module exports
├── ux_cli.py             # Main CLI implementation (1,069 lines)
├── test_ux_cli.py        # Comprehensive test suite (774 lines)
└── README.md             # This file
```

### Key Components

1. **Configuration Management**: YAML-based configuration with validation
2. **Rich Terminal UI**: Color-coded output with progress bars and tables
3. **Module Integration**: Interfaces with all platform modules
4. **Error Handling**: Graceful error handling with detailed messages
5. **Output Flexibility**: Multiple output formats (JSON, HTML, PDF)

## Features

- 7 main commands: audit, feedback, heuristics, analyze, report, monitor, config
- Rich terminal output with colors and formatting
- Progress bars for long-running operations
- Table-based results display
- Multiple output formats
- Dry-run mode for testing
- Verbose and quiet modes
- Configuration management
- Continuous monitoring with alerting
- Exit codes for CI/CD integration

## Requirements

See `../requirements.txt` for full dependency list. Key dependencies:

- click >= 8.1.7 (CLI framework)
- rich >= 13.7.0 (Terminal UI)
- pyyaml >= 6.0.1 (Configuration)
- jinja2 >= 3.1.2 (Report templates)

## Development

### Code Quality

```bash
# Format code
black ux_cli.py test_ux_cli.py --line-length=88

# Sort imports
isort ux_cli.py test_ux_cli.py

# Check style
flake8 ux_cli.py --max-line-length=88

# Type checking
mypy ux_cli.py --ignore-missing-imports
```

### Adding New Commands

1. Add `@cli.command()` decorator
2. Define click options
3. Implement command logic
4. Add error handling
5. Write tests in `test_ux_cli.py`

## License

Part of the devCrew_s1 UX Research & Design Feedback Platform (TOOL-UX-001).

## Support

For issues and feature requests, please create an issue in the devCrew_s1 repository.
