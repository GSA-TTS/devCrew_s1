# Accessibility Testing Guide

Comprehensive guide to running accessibility audits, interpreting results, and
implementing remediation.

## Table of Contents

- [Testing Overview](#testing-overview)
- [Running Audits](#running-audits)
- [Interpreting Results](#interpreting-results)
- [Remediation Process](#remediation-process)
- [CI/CD Integration](#cicd-integration)
- [Best Practices](#best-practices)
- [Manual Testing](#manual-testing)
- [Performance Optimization](#performance-optimization)

## Testing Overview

### What Gets Tested

The UX Research Platform performs comprehensive accessibility audits covering:

**Automated Checks (35-40% of WCAG):**
- Image alt text presence and quality
- Color contrast ratios (text, UI components)
- Form labels and associations
- Heading structure and hierarchy
- Link text descriptiveness
- HTML validation and semantics
- ARIA attributes correctness
- Keyboard navigation support
- Language declarations
- Document structure

**Manual Testing Required (60-65% of WCAG):**
- Screen reader compatibility
- Keyboard-only navigation flows
- Focus management in dynamic content
- Context-sensitive help
- Error recovery processes
- Time-dependent content usability
- Cognitive accessibility

### Testing Engines

The platform uses multiple engines for comprehensive coverage:

1. **axe-core** (Deque Systems)
   - 90+ automated rules
   - Industry-standard engine
   - High accuracy, few false positives

2. **Playwright** (Microsoft)
   - Browser automation
   - Multi-browser testing
   - Screenshot capture

3. **pa11y** (Optional)
   - HTML_CodeSniffer rules
   - Additional validation
   - Command-line integration

## Running Audits

### Basic Single-Page Audit

```bash
# Test one page with default settings (WCAG 2.1 Level AA)
ux-tool audit --url https://example.com

# Specify WCAG level
ux-tool audit --url https://example.com --wcag-level AAA

# Test with multiple browsers
ux-tool audit --url https://example.com \
  --browsers chromium,firefox,webkit
```

### Multi-Page Website Audit

```bash
# Crawl entire site (default: 50 pages max)
ux-tool audit --url https://example.com --max-pages 50

# Increase page limit
ux-tool audit --url https://example.com --max-pages 200

# Use sitemap for page discovery
ux-tool audit --url https://example.com \
  --sitemap https://example.com/sitemap.xml

# Audit specific pages from file
cat > pages.txt << EOF
https://example.com/
https://example.com/about
https://example.com/contact
https://example.com/products
EOF

ux-tool audit --pages-file pages.txt
```

### URL Pattern Filtering

```bash
# Include specific URL patterns
ux-tool audit --url https://example.com \
  --include-patterns "/blog/*,/docs/*,/help/*"

# Exclude patterns
ux-tool audit --url https://example.com \
  --exclude-patterns "/admin/*,/api/*,*.pdf"

# Combine include and exclude
ux-tool audit --url https://example.com \
  --include-patterns "/products/*" \
  --exclude-patterns "*/admin/*,*/cart/*"
```

### Viewport and Responsive Testing

```bash
# Test desktop only
ux-tool audit --url https://example.com --viewports desktop

# Test multiple viewports
ux-tool audit --url https://example.com \
  --viewports desktop,tablet,mobile

# Custom viewport sizes
ux-tool audit --url https://example.com \
  --viewports "1920x1080,1024x768,375x667"
```

### Output Formats

```bash
# HTML report (default, human-readable)
ux-tool audit --url https://example.com --output-format html

# JSON (for programmatic processing)
ux-tool audit --url https://example.com --output-format json

# PDF (for sharing with stakeholders)
ux-tool audit --url https://example.com --output-format pdf

# CSV (for spreadsheet analysis)
ux-tool audit --url https://example.com --output-format csv

# Multiple formats
ux-tool audit --url https://example.com \
  --output-format html,json,pdf \
  --output-dir ./reports/$(date +%Y%m%d)
```

### Advanced Options

```bash
# Authenticate before testing
ux-tool audit --url https://example.com \
  --auth-user admin@example.com \
  --auth-password 'SecureP@ss' \
  --auth-method form

# Use cookies for authentication
ux-tool audit --url https://example.com \
  --cookies cookies.json

# Set custom headers
ux-tool audit --url https://example.com \
  --headers "Authorization: Bearer TOKEN" \
  --headers "X-Custom-Header: Value"

# Adjust timeouts
ux-tool audit --url https://example.com \
  --page-timeout 60000 \
  --navigation-timeout 30000

# Run in headless mode (default)
ux-tool audit --url https://example.com --headless

# Run with visible browser (debugging)
ux-tool audit --url https://example.com --no-headless

# Parallel execution (faster for multi-page)
ux-tool audit --url https://example.com \
  --max-pages 100 \
  --parallel 5  # 5 concurrent pages
```

## Interpreting Results

### Report Structure

**HTML Report Sections:**

1. **Executive Summary**
   - Total violations count
   - Accessibility score (0-100)
   - WCAG conformance level achieved
   - Trend comparison (if baseline exists)

2. **Violation Breakdown by Severity**
   - Critical: Complete blockers for assistive tech
   - High: Major accessibility barriers
   - Medium: Usability issues for some users
   - Low: Minor improvements recommended

3. **Per-Page Analysis**
   - Individual page scores
   - Specific violations per page
   - Screenshots highlighting issues

4. **Violation Details**
   - WCAG success criterion
   - Impact description
   - Affected elements (CSS selectors)
   - Code snippets
   - Remediation guidance

5. **Trend Analysis** (if historical data)
   - Score changes over time
   - New/fixed/persisting violations
   - Improvement recommendations

### JSON Report Schema

```json
{
  "metadata": {
    "url": "https://example.com",
    "scan_date": "2024-01-15T10:30:00Z",
    "wcag_level": "AA",
    "total_pages": 25,
    "scan_duration_seconds": 180
  },
  "summary": {
    "score": 87,
    "grade": "B",
    "total_violations": 42,
    "by_severity": {
      "critical": 0,
      "high": 3,
      "medium": 15,
      "low": 24
    },
    "by_principle": {
      "perceivable": 20,
      "operable": 12,
      "understandable": 8,
      "robust": 2
    }
  },
  "violations": [
    {
      "id": "color-contrast",
      "impact": "serious",
      "wcag": ["1.4.3"],
      "description": "Insufficient color contrast",
      "help": "Ensure text contrast ratio is at least 4.5:1",
      "help_url": "https://dequeuniversity.com/rules/axe/4.8/color-contrast",
      "nodes": [
        {
          "html": "<button class=\"btn-secondary\">Click Me</button>",
          "target": [".btn-secondary"],
          "page": "https://example.com/products",
          "screenshot": "reports/screenshots/violation-001.png",
          "failure_summary": "Contrast ratio: 3.2:1 (minimum: 4.5:1)"
        }
      ]
    }
  ],
  "pages": [
    {
      "url": "https://example.com/",
      "score": 95,
      "violations": 2,
      "load_time_ms": 1250
    }
  ]
}
```

### Understanding Severity Levels

**Critical (Impact: Critical)**
- Prevents assistive technology from functioning
- Blocks content access entirely
- Legal compliance risk: High
- Fix priority: Immediate

Examples:
- Missing alt text on critical images
- Keyboard trap (cannot tab away)
- Missing form labels
- Invalid ARIA breaking screen readers

**High (Impact: Serious)**
- Major barriers for users with disabilities
- Content difficult or impossible to access
- Legal compliance risk: Medium-High
- Fix priority: This sprint

Examples:
- Insufficient color contrast (3:1 instead of 4.5:1)
- Non-descriptive link text ("click here")
- Missing heading structure
- Inaccessible form error messages

**Medium (Impact: Moderate)**
- Usability issues for some users
- Content accessible but difficult
- Legal compliance risk: Medium
- Fix priority: Next 2-3 sprints

Examples:
- Low color contrast (4:1 instead of 4.5:1)
- Redundant link text
- Inconsistent navigation
- Missing skip links

**Low (Impact: Minor)**
- Minor improvements recommended
- Minimal impact on users
- Legal compliance risk: Low
- Fix priority: Backlog

Examples:
- HTML validation warnings
- Suboptimal ARIA usage (but functional)
- Minor contrast issues on non-essential elements
- Missing lang attributes on inline content

### Accessibility Score

**Calculation:**
```
Base Score = 100

Deductions:
- Critical violation: -10 points each
- High violation: -5 points each
- Medium violation: -2 points each
- Low violation: -1 point each

Final Score = max(0, Base Score - Total Deductions)
```

**Grade Mapping:**
- **95-100 (A+)**: Excellent - Production ready
- **90-94 (A)**: Very Good - Minor fixes recommended
- **80-89 (B)**: Good - Some improvements needed
- **70-79 (C)**: Fair - Significant work required
- **60-69 (D)**: Poor - Major accessibility issues
- **0-59 (F)**: Failing - Not accessible

### Filtering Results

**CLI Filtering:**
```bash
# Show only critical/high violations
ux-tool audit --url https://example.com \
  --severity critical,high

# Show specific WCAG criteria
ux-tool audit --url https://example.com \
  --rules color-contrast,image-alt,label

# Exclude low priority issues
ux-tool audit --url https://example.com \
  --exclude-severity low
```

**Python API Filtering:**
```python
from ux_research.auditor import AccessibilityAuditor

auditor = AccessibilityAuditor()
results = await auditor.audit_url("https://example.com")

# Filter by severity
critical = [v for v in results.violations if v.impact == "critical"]
high = [v for v in results.violations if v.impact == "serious"]

# Filter by WCAG criterion
contrast_issues = [
    v for v in results.violations
    if "1.4.3" in v.wcag_criteria
]

# Filter by page
homepage_issues = [
    v for v in results.violations
    if any(n.page == "https://example.com/" for n in v.nodes)
]
```

## Remediation Process

### Workflow

1. **Prioritize Violations**
   ```bash
   # Generate prioritized remediation guide
   ux-tool remediate --audit-report audit.json \
     --prioritize severity \
     --output remediation.html
   ```

2. **Assign to Developers**
   ```bash
   # Create GitHub issues automatically
   ux-tool remediate --audit-report audit.json \
     --create-issues \
     --github-repo myorg/myrepo \
     --labels accessibility,bug \
     --assign-to @accessibility-team
   ```

3. **Implement Fixes**
   - Review remediation guidance
   - Apply code changes
   - Test locally

4. **Verify Fixes**
   ```bash
   # Re-run audit on specific pages
   ux-tool audit --pages-file fixed-pages.txt \
     --baseline audit-before.json \
     --compare
   ```

5. **Track Progress**
   ```bash
   # Generate progress report
   ux-tool report \
     --baseline audit-week1.json \
     --current audit-week2.json \
     --output progress-report.html
   ```

### Remediation Guide Example

**Generated Guide Structure:**
```markdown
# Accessibility Remediation Guide

## Sprint Priority (3 Critical, 5 High)

### 1. Missing Form Labels (Critical) - 2 hours
**WCAG**: 3.3.2 (Level A)
**Pages Affected**: /checkout, /contact
**Impact**: Screen reader users cannot fill forms

**Current Code:**
<input type="email" name="email" placeholder="Email">

**Fixed Code:**
<label for="email">Email Address:</label>
<input type="email" id="email" name="email" placeholder="Email">

**Testing**: Verify with NVDA/JAWS

---

### 2. Insufficient Contrast - Primary Buttons (High) - 1 hour
**WCAG**: 1.4.3 (Level AA)
**Pages Affected**: All pages (42 instances)
**Contrast Ratio**: 3.2:1 (needs 4.5:1)

**Current Code:**
.btn-primary {
  color: #777777;
  background: #ffffff;
}

**Fixed Code:**
.btn-primary {
  color: #595959; /* 4.6:1 contrast */
  background: #ffffff;
}

**Testing**: Use DevTools contrast checker
```

### Bulk Fixes

**CSS Pattern Fixes:**
```bash
# Find all low-contrast text
ux-tool audit --url https://example.com \
  --rules color-contrast \
  --output-format csv > contrast-issues.csv

# Review and update CSS variables
# Update theme colors in one place
```

**JavaScript for ARIA:**
```javascript
// Batch add ARIA labels to buttons without text
document.querySelectorAll('button:not([aria-label])').forEach(btn => {
  if (!btn.textContent.trim() && btn.querySelector('svg')) {
    const title = btn.getAttribute('title') || 'Button';
    btn.setAttribute('aria-label', title);
  }
});
```

## CI/CD Integration

See [CI/CD Integration Guide](ci_cd_integration.md) for complete examples.

**Quick GitHub Actions Integration:**
```yaml
# .github/workflows/accessibility.yml
name: Accessibility Audit

on:
  pull_request:
  push:
    branches: [main, develop]

jobs:
  audit:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install UX Research Platform
        run: |
          pip install -r tools/ux_research/requirements.txt
          playwright install chromium

      - name: Run Accessibility Audit
        run: |
          ux-tool audit \
            --url https://staging.example.com \
            --wcag-level AA \
            --output-format json \
            --output-dir ./reports

      - name: Check for Critical/High Issues
        run: |
          ux-tool audit --url https://staging.example.com \
            --fail-on critical,high \
            --exit-code

      - name: Upload Report
        uses: actions/upload-artifact@v3
        if: always()
        with:
          name: accessibility-report
          path: ./reports/
```

## Best Practices

### Test Early and Often

```bash
# Component-level testing during development
ux-tool audit --url http://localhost:3000/components/button

# Page-level testing before PR
ux-tool audit --url http://localhost:3000/checkout

# Full site audit before release
ux-tool audit --url https://staging.example.com --max-pages 100
```

### Establish Baselines

```bash
# Create baseline after initial fixes
ux-tool audit --url https://example.com \
  --output-format json \
  --output baseline-2024-01.json

# Compare against baseline
ux-tool audit --url https://example.com \
  --baseline baseline-2024-01.json \
  --fail-on regression
```

### Set Quality Gates

```bash
# Enforce minimum score
ux-tool audit --url https://staging.example.com \
  --minimum-score 90 \
  --exit-code

# Block on new critical/high issues
ux-tool audit --url https://staging.example.com \
  --fail-on critical,high \
  --compare-baseline baseline.json
```

### Test Dynamic Content

```bash
# Wait for SPA to load
ux-tool audit --url https://example.com/app \
  --wait-for-selector ".app-loaded" \
  --page-timeout 30000

# Interact before testing
ux-tool audit --url https://example.com \
  --script "document.querySelector('.show-menu').click()" \
  --wait-after-script 1000
```

### Accessibility Regression Testing

```bash
#!/bin/bash
# regression-test.sh

# Run audit
ux-tool audit --url $SITE_URL \
  --output-format json \
  --output current.json

# Compare with previous
if [ -f previous.json ]; then
  ux-tool compare --before previous.json --after current.json

  # Check for new violations
  NEW_VIOLATIONS=$(jq '.new_violations | length' comparison.json)

  if [ $NEW_VIOLATIONS -gt 0 ]; then
    echo "❌ $NEW_VIOLATIONS new accessibility violations detected"
    exit 1
  else
    echo "✅ No accessibility regressions"
  fi
fi

# Save for next run
cp current.json previous.json
```

## Manual Testing

### Keyboard Navigation Checklist

```bash
# Steps to test:
1. Unplug mouse (or don't use it)
2. Tab through all interactive elements
3. Verify visible focus indicator on each element
4. Use Enter/Space to activate buttons and links
5. Test dropdown menus with arrow keys
6. Try Shift+Tab for reverse navigation
7. Ensure no keyboard traps (can always tab away)
8. Test Esc key to close modals/menus

# Common keyboard shortcuts to test:
- Tab: Next focusable element
- Shift+Tab: Previous focusable element
- Enter: Activate links and buttons
- Space: Activate buttons and checkboxes
- Arrow keys: Navigate within dropdowns, radio groups
- Esc: Close modals, cancel operations
```

### Screen Reader Testing

**NVDA (Windows, Free):**
```bash
# Download: https://www.nvaccess.org/download/

# Common commands:
- Ctrl: Stop reading
- Insert+Down: Start reading
- H: Next heading
- K: Next link
- F: Next form field
- T: Next table
- Insert+F7: List all elements
```

**VoiceOver (macOS, Built-in):**
```bash
# Enable: Cmd+F5

# Common commands:
- VO+A: Start reading
- VO+Right/Left: Navigate elements
- VO+Space: Activate element
- VO+U: Rotor (list elements)
- VO+H: Next heading
```

**Testing Script:**
```
1. Navigate to homepage
2. Listen to page landmarks
3. Navigate by headings (H key)
4. Navigate by links (K key)
5. Fill out forms (F key)
6. Verify table structure (T key)
7. Test ARIA live regions (dynamic content)
8. Verify focus announcements
```

### Color/Contrast Testing

```bash
# Grayscale test (remove all color)
# Browser DevTools > Rendering > Emulate vision deficiencies > Achromatopsia

# Color blindness simulation
# Protanopia (red-blind): 1% of males
# Deuteranopia (green-blind): 1% of males
# Tritanopia (blue-blind): 0.001%

# Tools:
- Chrome DevTools: Rendering > Emulate vision deficiencies
- Color Oracle (desktop app): Free color blindness simulator
- Contrast Checker: WebAIM or DevTools

# Test checklist:
- ✅ Information not conveyed by color alone
- ✅ Color-blind users can distinguish links
- ✅ Form errors not indicated by color only
- ✅ Charts have patterns/textures, not just color
```

## Performance Optimization

### Speed Up Large Audits

```bash
# Increase parallel execution
ux-tool audit --url https://example.com \
  --max-pages 200 \
  --parallel 10  # 10 concurrent pages

# Use faster browser (Chromium is fastest)
ux-tool audit --url https://example.com \
  --browsers chromium

# Skip screenshots (faster)
ux-tool audit --url https://example.com \
  --no-screenshots

# Reduce viewport testing
ux-tool audit --url https://example.com \
  --viewports desktop  # Test desktop only
```

### Caching

```bash
# Cache audit results for re-analysis
ux-tool audit --url https://example.com \
  --cache-results \
  --cache-ttl 3600  # 1 hour

# Reuse cached results
ux-tool report --cache-id abc123 --format pdf
```

### Resource Limits

```bash
# Set memory limits (Docker)
docker run --memory=4g ux-research \
  audit --url https://example.com --max-pages 100

# Timeout configuration
ux-tool audit --url https://example.com \
  --page-timeout 30000 \
  --navigation-timeout 10000
```

## Next Steps

1. **Learn WCAG Standards**: Review [WCAG Guide](wcag_guide.md)
2. **Integrate into CI/CD**: Follow [CI/CD Integration](ci_cd_integration.md)
3. **Analyze User Feedback**: See [Feedback Analysis](feedback_analysis.md)
4. **Heuristic Evaluation**: Check [Heuristic Evaluation](heuristic_evaluation.md)

## Quick Reference Commands

```bash
# Basic audit
ux-tool audit --url https://example.com

# Full site audit with all outputs
ux-tool audit --url https://example.com \
  --max-pages 100 \
  --wcag-level AA \
  --output-format html,json,pdf \
  --output-dir ./reports

# CI/CD pipeline
ux-tool audit --url https://staging.example.com \
  --fail-on critical,high \
  --minimum-score 85 \
  --exit-code

# Compare with baseline
ux-tool audit --url https://example.com \
  --baseline baseline.json \
  --fail-on regression
```
