# Troubleshooting Guide

Common issues and solutions for the UX Research & Design Feedback Platform.

## Table of Contents

- [Installation Issues](#installation-issues)
- [Browser Driver Issues](#browser-driver-issues)
- [API and Authentication](#api-and-authentication)
- [Performance Issues](#performance-issues)
- [Audit Errors](#audit-errors)
- [Report Generation](#report-generation)
- [CI/CD Integration](#cicd-integration)
- [Getting Help](#getting-help)

## Installation Issues

### Issue: Python version incompatibility

**Symptoms:**
```
ERROR: Package requires Python 3.10 or higher
```

**Solution:**
```bash
# Check Python version
python --version

# Install Python 3.11 (recommended)
# macOS
brew install python@3.11

# Ubuntu
sudo apt install python3.11 python3.11-venv

# Windows
choco install python311

# Create virtual environment with correct version
python3.11 -m venv venv
source venv/bin/activate  # macOS/Linux
.\venv\Scripts\Activate.ps1  # Windows
```

### Issue: pip install fails with SSL errors

**Symptoms:**
```
SSL: CERTIFICATE_VERIFY_FAILED
```

**Solution:**
```bash
# macOS: Install certificates
/Applications/Python\ 3.11/Install\ Certificates.command

# Or set certificate path
export REQUESTS_CA_BUNDLE=/etc/ssl/certs/ca-certificates.crt

# Or upgrade certifi
pip install --upgrade certifi

# Last resort (not recommended for production)
pip install --trusted-host pypi.org --trusted-host files.pythonhosted.org -r requirements.txt
```

### Issue: Permission denied during installation

**Symptoms:**
```
ERROR: Could not install packages due to an OSError: [Errno 13] Permission denied
```

**Solution:**
```bash
# Don't use sudo with pip! Use virtual environment instead
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# If you must install globally (not recommended)
pip install --user -r requirements.txt
```

### Issue: Dependency conflicts

**Symptoms:**
```
ERROR: pip's dependency resolver does not currently take into account all packages
```

**Solution:**
```bash
# Clear pip cache
pip cache purge

# Upgrade pip
pip install --upgrade pip

# Install with --upgrade-strategy
pip install --upgrade-strategy eager -r requirements.txt

# Or create fresh virtual environment
rm -rf venv
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Browser Driver Issues

### Issue: Playwright browsers not installed

**Symptoms:**
```
Executable doesn't exist at /path/to/ms-playwright/chromium
```

**Solution:**
```bash
# Install browsers
playwright install

# Install specific browser
playwright install chromium

# Install with system dependencies (Linux)
playwright install --with-deps

# Verify installation
playwright --version
```

### Issue: Browser crashes immediately

**Symptoms:**
```
Browser closed unexpectedly
Error: Browser process exited with code: 127
```

**Solution:**
```bash
# Linux: Install missing dependencies
playwright install-deps

# Check system requirements
ulimit -n  # Should be > 1024

# Increase file descriptor limit
ulimit -n 4096

# Run with debug logging
DEBUG=pw:api ux-tool audit --url https://example.com
```

### Issue: Headless mode fails

**Symptoms:**
```
Error: Failed to launch browser in headless mode
```

**Solution:**
```bash
# Try headed mode for debugging
ux-tool audit --url https://example.com --no-headless

# Or use different browser
ux-tool audit --url https://example.com --browser firefox

# Check display server (Linux)
export DISPLAY=:0
```

### Issue: Browser timeout

**Symptoms:**
```
Timeout 30000ms exceeded while waiting for page to load
```

**Solution:**
```bash
# Increase timeout
ux-tool audit --url https://example.com \
  --page-timeout 60000 \
  --navigation-timeout 30000

# Or in config file
# ux-audit-config.yaml
crawling:
  timeout: 60000
  navigation_timeout: 30000
```

## API and Authentication

### Issue: Google Analytics authentication fails

**Symptoms:**
```
Error: Could not authenticate with Google Analytics API
```

**Solution:**
```bash
# Verify service account key file exists
ls -la /path/to/service-account.json

# Check permissions
chmod 600 /path/to/service-account.json

# Verify environment variable
echo $GOOGLE_ANALYTICS_KEY_FILE

# Test authentication
python3 << EOF
from google.oauth2 import service_account
credentials = service_account.Credentials.from_service_account_file(
    '/path/to/service-account.json'
)
print("Authentication successful")
EOF
```

### Issue: Hotjar API rate limiting

**Symptoms:**
```
Error: 429 Too Many Requests
```

**Solution:**
```bash
# Add delay between requests in config
# ux-audit-config.yaml
analytics:
  hotjar:
    rate_limit_delay: 2000  # 2 seconds

# Or use pagination
ux-tool feedback --source hotjar \
  --date-range 2024-01-01:2024-01-07 \
  --page-size 50
```

### Issue: GitHub token expired

**Symptoms:**
```
Error: 401 Unauthorized
```

**Solution:**
```bash
# Generate new token at https://github.com/settings/tokens
# Required scopes: repo, write:discussion

# Update environment variable
export GITHUB_TOKEN=ghp_new_token_here

# Or update .env file
echo "GITHUB_TOKEN=ghp_new_token_here" >> .env

# Verify token
gh auth status
```

### Issue: Zendesk API connection fails

**Symptoms:**
```
Error: Could not connect to Zendesk API
```

**Solution:**
```bash
# Verify domain format (no https://)
ZENDESK_DOMAIN=yourcompany.zendesk.com  # Correct
ZENDESK_DOMAIN=https://yourcompany.zendesk.com  # Wrong

# Test connection
curl -u ${ZENDESK_EMAIL}/token:${ZENDESK_API_KEY} \
  https://${ZENDESK_DOMAIN}/api/v2/tickets.json

# Check API key format
echo $ZENDESK_API_KEY | wc -c  # Should be ~40 characters
```

## Performance Issues

### Issue: Audit takes too long

**Symptoms:**
```
Audit running for >30 minutes on small site
```

**Solution:**
```bash
# Reduce concurrent pages
ux-tool audit --url https://example.com --parallel 2

# Limit pages scanned
ux-tool audit --url https://example.com --max-pages 20

# Skip screenshots
ux-tool audit --url https://example.com --no-screenshots

# Use faster browser
ux-tool audit --url https://example.com --browser chromium

# Monitor progress
ux-tool audit --url https://example.com --verbose
```

### Issue: High memory usage

**Symptoms:**
```
JavaScript heap out of memory
```

**Solution:**
```bash
# Increase Node.js memory
export NODE_OPTIONS="--max-old-space-size=4096"

# Reduce parallel execution
ux-tool audit --url https://example.com --parallel 1

# Process in batches
ux-tool audit --url https://example.com \
  --max-pages 50 \
  --batch-size 10

# Monitor memory usage
top -p $(pgrep -f ux-tool)
```

### Issue: Network timeouts

**Symptoms:**
```
Error: net::ERR_TIMED_OUT
```

**Solution:**
```bash
# Check network connectivity
ping example.com

# Use VPN if behind firewall
# ...

# Increase timeout
ux-tool audit --url https://example.com \
  --timeout 90000

# Retry on failure
ux-tool audit --url https://example.com \
  --retry 3 \
  --retry-delay 5000
```

### Issue: Slow sentiment analysis

**Symptoms:**
```
Sentiment analysis taking hours on 10k feedback items
```

**Solution:**
```bash
# Use batch processing
ux-tool feedback --source feedback.csv \
  --analyze sentiment \
  --batch-size 100 \
  --parallel 4

# Enable caching
ux-tool feedback --source feedback.csv \
  --analyze sentiment \
  --cache-results

# Use faster model (lower accuracy)
ux-tool feedback --source feedback.csv \
  --analyze sentiment \
  --model fast
```

## Audit Errors

### Issue: Accessibility rules fail to load

**Symptoms:**
```
Error: Could not load axe-core rules
```

**Solution:**
```bash
# Reinstall axe-core
pip uninstall axe-playwright-python
pip install axe-playwright-python

# Clear browser cache
rm -rf ~/.cache/ms-playwright

# Reinstall browsers
playwright install --force

# Test with minimal example
python3 << EOF
from playwright.sync_api import sync_playwright
from axe_playwright_python.sync_playwright import Axe

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page()
    page.goto("https://example.com")
    axe = Axe()
    results = axe.run(page)
    print(f"Found {len(results['violations'])} violations")
    browser.close()
EOF
```

### Issue: False positives in color contrast

**Symptoms:**
```
Color contrast failures on elements with images/gradients
```

**Solution:**
```bash
# Skip specific rules
ux-tool audit --url https://example.com \
  --skip-rules color-contrast

# Or configure in YAML
# ux-audit-config.yaml
wcag:
  rules_to_skip:
    - color-contrast

# Manual review of flagged elements
# Check audit report for specific elements and verify manually
```

### Issue: Can't audit authenticated pages

**Symptoms:**
```
Error: Login required
```

**Solution:**
```bash
# Method 1: Login via form
ux-tool audit --url https://example.com/dashboard \
  --auth-user admin@example.com \
  --auth-password 'SecurePass' \
  --auth-method form \
  --login-url https://example.com/login

# Method 2: Use cookies
# 1. Login manually and export cookies
# 2. Save to cookies.json
# 3. Use in audit
ux-tool audit --url https://example.com/dashboard \
  --cookies cookies.json

# Method 3: Use session token
ux-tool audit --url https://example.com/dashboard \
  --headers "Authorization: Bearer YOUR_TOKEN"

# Verify authentication worked
ux-tool audit --url https://example.com/dashboard \
  --auth-user admin@example.com \
  --auth-password 'SecurePass' \
  --verify-auth \
  --verbose
```

### Issue: CORS errors during audit

**Symptoms:**
```
Error: Cross-Origin Request Blocked
```

**Solution:**
```bash
# This is expected for security reasons
# Audit continues despite CORS errors

# If blocking audit, whitelist audit server
# Add to server CORS headers:
Access-Control-Allow-Origin: *
Access-Control-Allow-Methods: GET, POST

# Or use proxy
ux-tool audit --url https://example.com \
  --proxy http://proxy.company.com:8080
```

## Report Generation

### Issue: PDF generation fails

**Symptoms:**
```
Error: Failed to generate PDF report
```

**Solution:**
```bash
# Install required dependencies
# macOS
brew install wkhtmltopdf

# Ubuntu
sudo apt install wkhtmltopdf

# Or use HTML to PDF service
ux-tool report --audit audit.json \
  --output report.html

# Then convert with browser
# Open report.html in Chrome and Print to PDF

# Or use Python library
pip install weasyprint
```

### Issue: Report images not loading

**Symptoms:**
```
Report shows broken image icons
```

**Solution:**
```bash
# Ensure screenshots are captured
ux-tool audit --url https://example.com \
  --include-screenshots

# Check screenshot directory
ls -la reports/screenshots/

# Use absolute paths in report
ux-tool report --audit audit.json \
  --output report.html \
  --absolute-paths

# Embed images in HTML
ux-tool report --audit audit.json \
  --output report.html \
  --embed-images
```

### Issue: JSON report malformed

**Symptoms:**
```
Error: Invalid JSON in audit report
```

**Solution:**
```bash
# Validate JSON
jq empty audit.json  # Will error if invalid

# Regenerate report
rm audit.json
ux-tool audit --url https://example.com \
  --output-format json

# Check for incomplete write
ls -lh audit.json  # Check file size

# Ensure audit completed
tail -20 audit.log
```

## CI/CD Integration

### Issue: GitHub Actions workflow fails

**Symptoms:**
```
Error: Process completed with exit code 1
```

**Solution:**
```yaml
# Add debug logging
- name: Run audit
  run: |
    set -x  # Enable debug mode
    ux-tool audit --url ${{ secrets.STAGING_URL }} --verbose

# Check secrets are set
- name: Verify secrets
  run: |
    if [ -z "${{ secrets.STAGING_URL }}" ]; then
      echo "STAGING_URL secret not set"
      exit 1
    fi

# Test locally with act
act pull_request

# Check logs
# Go to Actions tab > Select workflow run > View logs
```

### Issue: Playwright browsers not found in CI

**Symptoms:**
```
Error: Executable doesn't exist at /home/runner/.cache/ms-playwright
```

**Solution:**
```yaml
# Install browsers in CI
- name: Install Playwright browsers
  run: |
    playwright install chromium --with-deps

# Or use Docker image with browsers pre-installed
jobs:
  audit:
    runs-on: ubuntu-latest
    container:
      image: mcr.microsoft.com/playwright:v1.40.0-focal
```

### Issue: CI timeout

**Symptoms:**
```
Error: The job running on runner has exceeded the maximum execution time of 360 minutes
```

**Solution:**
```yaml
# Reduce scope
- name: Run audit
  run: |
    ux-tool audit --url $URL --max-pages 20

# Or increase timeout
jobs:
  audit:
    timeout-minutes: 60  # Default is 360

# Or split into multiple jobs
jobs:
  audit-main:
    steps:
      - run: ux-tool audit --url $URL --include-patterns "/main/*"

  audit-docs:
    steps:
      - run: ux-tool audit --url $URL --include-patterns "/docs/*"
```

### Issue: Artifacts not uploaded

**Symptoms:**
```
Warning: Artifact upload failed
```

**Solution:**
```yaml
# Check file exists
- name: Check reports
  run: ls -la reports/

# Use correct path
- uses: actions/upload-artifact@v4
  with:
    name: reports
    path: ./reports/  # Note leading ./

# Continue on error
- uses: actions/upload-artifact@v4
  if: always()
  with:
    name: reports
    path: ./reports/
```

## Getting Help

### Enable Debug Logging

```bash
# Verbose output
ux-tool audit --url https://example.com --verbose

# Debug mode (even more detail)
ux-tool audit --url https://example.com --debug

# Save logs to file
ux-tool audit --url https://example.com --debug 2>&1 | tee audit.log

# Playwright debug
DEBUG=pw:api ux-tool audit --url https://example.com
```

### Check System Information

```bash
# Python version
python --version

# Installed packages
pip list

# Playwright browsers
playwright --version

# System info
uname -a  # Linux/macOS
systeminfo  # Windows

# Available memory
free -h  # Linux
vm_stat  # macOS
```

### Run Diagnostic Script

```bash
#!/bin/bash
# diagnostic.sh

echo "=== System Information ==="
python --version
node --version
pip --version

echo -e "\n=== Installed Packages ==="
pip list | grep -E "playwright|axe|nltk|pandas"

echo -e "\n=== Playwright Browsers ==="
ls -lh ~/.cache/ms-playwright/ 2>/dev/null || echo "No browsers installed"

echo -e "\n=== Environment Variables ==="
env | grep -E "GOOGLE|GITHUB|ZENDESK|HOTJAR" | sed 's/=.*$/=***/'

echo -e "\n=== Quick Test ==="
python3 << EOF
try:
    from playwright.sync_api import sync_playwright
    print("✓ Playwright import successful")
    with sync_playwright() as p:
        browser = p.chromium.launch()
        print("✓ Browser launch successful")
        browser.close()
except Exception as e:
    print(f"✗ Error: {e}")
EOF
```

### Create Support Ticket

When creating a support ticket, include:

1. **Error message**: Full error output
2. **Command used**: Exact command that failed
3. **System info**: OS, Python version, package versions
4. **Logs**: Output of `--verbose` or `--debug`
5. **Steps to reproduce**: Minimal example
6. **Expected vs actual**: What should happen vs what happens

**Template:**
```markdown
## Environment
- OS: macOS 13.5
- Python: 3.11.5
- UX Research Platform: 1.0.0
- Playwright: 1.40.0

## Issue Description
Brief description of the problem

## Steps to Reproduce
1. Run command: `ux-tool audit --url https://example.com`
2. Observe error

## Error Message
```
[Paste full error message]
```

## Expected Behavior
Audit should complete successfully

## Actual Behavior
Audit fails with timeout error

## Logs
```
[Attach audit.log or paste relevant logs]
```

## Attempted Solutions
- Tried increasing timeout
- Reinstalled browsers
- etc.
```

### Community Support

- **GitHub Issues**: https://github.com/your-org/devCrew_s1/issues
- **Internal Wiki**: [Link to wiki]
- **Slack Channel**: #ux-research-platform
- **Email**: platform-engineering@company.com

### Known Issues

Check the [GitHub Issues](https://github.com/your-org/devCrew_s1/issues) page
for known issues and workarounds.

**Common known issues:**
- pa11y integration requires Node.js 18+ (planned fix: v1.1.0)
- PDF generation requires wkhtmltopdf (documented limitation)
- Large sites (>500 pages) may require memory tuning (performance optimization planned)

## Quick Fixes Checklist

- [ ] Python 3.10+ installed
- [ ] Virtual environment activated
- [ ] Dependencies installed (`pip install -r requirements.txt`)
- [ ] Playwright browsers installed (`playwright install`)
- [ ] Environment variables set (if using APIs)
- [ ] Sufficient disk space (>2GB free)
- [ ] Network connectivity to target site
- [ ] No firewall blocking browser traffic
- [ ] Logs reviewed for specific errors
- [ ] Latest version of platform (`git pull`)

## Emergency Workarounds

### If all else fails:

**Option 1: Docker**
```bash
docker pull mcr.microsoft.com/playwright:v1.40.0-focal
docker run -it --rm \
  -v $(pwd)/reports:/reports \
  mcr.microsoft.com/playwright:v1.40.0-focal \
  bash -c "pip install ux-research && ux-tool audit --url https://example.com"
```

**Option 2: Use Online Tools**
- axe DevTools: https://www.deque.com/axe/devtools/
- WAVE: https://wave.webaim.org/
- Lighthouse: Chrome DevTools

**Option 3: Manual Audit**
- Follow [WCAG Guide](wcag_guide.md) for manual checklist
- Use browser extensions for quick checks
- Document findings manually

## Still Stuck?

If you've tried everything and still experiencing issues:

1. **Search existing issues**: Someone may have encountered this before
2. **Create detailed issue**: Include all diagnostic information
3. **Ask in Slack**: #ux-research-platform channel
4. **Email support**: platform-engineering@company.com

Response times:
- Critical issues: 2-4 hours
- High priority: 24 hours
- Medium/low: 2-3 business days
