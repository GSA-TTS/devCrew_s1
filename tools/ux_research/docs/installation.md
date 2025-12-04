# Installation Guide

Complete installation instructions for the UX Research & Design Feedback Platform.

## Table of Contents

- [System Requirements](#system-requirements)
- [Platform-Specific Installation](#platform-specific-installation)
  - [macOS](#macos)
  - [Linux](#linux)
  - [Windows](#windows)
- [Browser Driver Setup](#browser-driver-setup)
- [API Key Configuration](#api-key-configuration)
- [Verification Steps](#verification-steps)
- [Development Installation](#development-installation)
- [Docker Installation](#docker-installation)
- [Troubleshooting](#troubleshooting)

## System Requirements

### Minimum Requirements

- **Python**: 3.10 or higher
- **Node.js**: 18.0 or higher (for pa11y integration)
- **RAM**: 4 GB minimum, 8 GB recommended
- **Disk Space**: 2 GB for browsers and dependencies
- **Operating System**:
  - macOS 11 (Big Sur) or higher
  - Ubuntu 20.04 LTS or higher
  - Windows 10 or higher

### Recommended Requirements

- **Python**: 3.11+
- **Node.js**: 20 LTS
- **RAM**: 16 GB
- **Disk Space**: 5 GB
- **CPU**: 4+ cores for parallel auditing

## Platform-Specific Installation

### macOS

#### Prerequisites

```bash
# Install Homebrew (if not already installed)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install Python 3.11
brew install python@3.11

# Install Node.js 20 LTS
brew install node@20

# Verify installations
python3 --version  # Should be 3.11+
node --version     # Should be 18+
npm --version
```

#### Install UX Research Platform

```bash
# Clone devCrew_s1 repository
cd ~/Documents/GitHub
git clone https://github.com/your-org/devCrew_s1.git
cd devCrew_s1/tools/ux_research

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install Python dependencies
pip install -r requirements.txt

# Install Playwright browsers
playwright install

# Install Node.js dependencies
npm install -g pa11y pa11y-ci lighthouse

# Add CLI to PATH (optional)
echo 'export PATH="$PATH:$(pwd)/cli"' >> ~/.zshrc
source ~/.zshrc
```

#### macOS-Specific Notes

- **Gatekeeper**: First run may require allowing browsers in System Preferences
- **Permissions**: Grant Terminal access to screen recording for screenshot capture
- **M1/M2 Macs**: All dependencies have native ARM support

### Linux

#### Ubuntu/Debian

```bash
# Update package lists
sudo apt update && sudo apt upgrade -y

# Install Python 3.11
sudo apt install -y python3.11 python3.11-venv python3-pip

# Install Node.js 20 LTS
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt install -y nodejs

# Install system dependencies for browsers
sudo apt install -y \
  libglib2.0-0 \
  libnss3 \
  libnspr4 \
  libatk1.0-0 \
  libatk-bridge2.0-0 \
  libcups2 \
  libdrm2 \
  libdbus-1-3 \
  libxkbcommon0 \
  libxcomposite1 \
  libxdamage1 \
  libxfixes3 \
  libxrandr2 \
  libgbm1 \
  libpango-1.0-0 \
  libcairo2 \
  libasound2

# Clone repository
cd ~/Documents
git clone https://github.com/your-org/devCrew_s1.git
cd devCrew_s1/tools/ux_research

# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Install Playwright browsers
playwright install

# Install Node.js dependencies
sudo npm install -g pa11y pa11y-ci lighthouse
```

#### Red Hat/CentOS/Fedora

```bash
# Install Python 3.11
sudo dnf install -y python3.11 python3.11-devel

# Install Node.js 20 LTS
curl -fsSL https://rpm.nodesource.com/setup_20.x | sudo bash -
sudo dnf install -y nodejs

# Install system dependencies
sudo dnf install -y \
  gtk3 \
  nss \
  atk \
  cups-libs \
  libdrm \
  libXdamage \
  libXrandr \
  mesa-libgbm \
  alsa-lib

# Follow Ubuntu instructions for remaining steps
```

#### Linux-Specific Notes

- **Headless Servers**: Use `DISPLAY=:99` for headless environments
- **Docker**: See [Docker Installation](#docker-installation) for containerized setup
- **Permissions**: May need `sudo` for system-wide npm packages

### Windows

#### Prerequisites

```powershell
# Install Chocolatey (if not already installed)
Set-ExecutionPolicy Bypass -Scope Process -Force
[System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072
iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))

# Install Python 3.11
choco install python311 -y

# Install Node.js 20 LTS
choco install nodejs-lts -y

# Refresh environment variables
refreshenv

# Verify installations
python --version
node --version
npm --version
```

#### Install UX Research Platform

```powershell
# Clone repository
cd C:\Users\YourUsername\Documents
git clone https://github.com/your-org/devCrew_s1.git
cd devCrew_s1\tools\ux_research

# Create virtual environment
python -m venv venv
.\venv\Scripts\Activate.ps1

# Upgrade pip
python -m pip install --upgrade pip

# Install Python dependencies
pip install -r requirements.txt

# Install Playwright browsers
playwright install

# Install Node.js dependencies
npm install -g pa11y pa11y-ci lighthouse
```

#### Windows-Specific Notes

- **PowerShell Execution Policy**: May need to run as Administrator
- **Path Issues**: Add Python and Node to PATH if not automatic
- **WSL2**: Consider using Windows Subsystem for Linux for better performance

## Browser Driver Setup

### Playwright Browsers

```bash
# Install all browsers (Chromium, Firefox, WebKit)
playwright install

# Install specific browsers only
playwright install chromium
playwright install firefox
playwright install webkit

# Install with system dependencies (Linux)
playwright install --with-deps
```

### Verify Browser Installation

```bash
# Test browser launch
python3 << EOF
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page()
    page.goto("https://example.com")
    print(f"Page title: {page.title()}")
    browser.close()
EOF
```

### Browser Storage Locations

- **macOS**: `~/Library/Caches/ms-playwright`
- **Linux**: `~/.cache/ms-playwright`
- **Windows**: `%USERPROFILE%\AppData\Local\ms-playwright`

## API Key Configuration

### Environment Variables

Create a `.env` file in `tools/ux_research/`:

```bash
# Google Analytics (optional)
GOOGLE_ANALYTICS_PROPERTY_ID=UA-XXXXXXXXX-X
GOOGLE_ANALYTICS_KEY_FILE=path/to/service-account.json

# Hotjar (optional)
HOTJAR_SITE_ID=XXXXXXX
HOTJAR_API_KEY=your-api-key-here

# GitHub Issues Integration (optional)
GITHUB_TOKEN=ghp_your_token_here
GITHUB_REPO=your-org/your-repo

# Slack Notifications (optional)
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL

# Email Notifications (optional)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
```

### Google Analytics Setup

1. Create a service account in Google Cloud Console
2. Enable Google Analytics Reporting API
3. Download JSON key file
4. Grant service account access to Analytics property
5. Set `GOOGLE_ANALYTICS_KEY_FILE` path in `.env`

### Hotjar Setup

1. Log in to Hotjar account
2. Navigate to Account Settings > API Access
3. Generate new API key
4. Set `HOTJAR_API_KEY` in `.env`

### GitHub Token Setup

```bash
# Generate personal access token
# https://github.com/settings/tokens
# Required scopes: repo, write:discussion

# Set token in environment
export GITHUB_TOKEN=ghp_your_token_here

# Or add to .env file
echo "GITHUB_TOKEN=ghp_your_token_here" >> .env
```

## Verification Steps

### 1. Verify Python Installation

```bash
# Check Python version
python3 --version  # Should be 3.10+

# Check pip version
pip --version

# Verify virtual environment
which python  # Should point to venv/bin/python
```

### 2. Verify Dependencies

```bash
# Check installed packages
pip list

# Verify key packages
python3 << EOF
import playwright
import axe_playwright_python
import nltk
import pandas
print("All dependencies installed successfully!")
EOF
```

### 3. Verify Playwright Browsers

```bash
# List installed browsers
playwright --version

# Test browser launch
python3 -c "from playwright.sync_api import sync_playwright; p = sync_playwright().start(); b = p.chromium.launch(); b.close(); p.stop(); print('Browser test passed!')"
```

### 4. Verify Node.js Dependencies

```bash
# Check pa11y installation
pa11y --version

# Check Lighthouse installation
lighthouse --version
```

### 5. Run Test Suite

```bash
# Run all tests
pytest -v

# Run quick smoke tests
pytest tests/test_integration.py -k "test_basic" -v
```

### 6. Test CLI

```bash
# Check CLI installation
ux-tool --version

# Run help command
ux-tool --help

# Test basic audit
ux-tool audit --url https://example.com --wcag-level A
```

## Development Installation

### Install Development Dependencies

```bash
# Activate virtual environment
source venv/bin/activate  # macOS/Linux
.\venv\Scripts\Activate.ps1  # Windows

# Install dev dependencies
pip install -r requirements-dev.txt

# Install pre-commit hooks
pre-commit install
```

### Development Tools Included

- **pytest**: Test framework
- **pytest-cov**: Code coverage
- **pytest-asyncio**: Async test support
- **black**: Code formatter
- **isort**: Import sorter
- **flake8**: Linter
- **mypy**: Type checker
- **bandit**: Security scanner
- **pre-commit**: Git hooks

### Run Development Checks

```bash
# Format code
black .
isort .

# Lint code
flake8

# Type check
mypy tools/ux_research --ignore-missing-imports

# Security scan
bandit -r tools/ux_research

# Run all pre-commit hooks
pre-commit run --all-files
```

## Docker Installation

### Dockerfile

Create `Dockerfile` in `tools/ux_research/`:

```dockerfile
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    nodejs \
    npm \
    wget \
    gnupg \
    libglib2.0-0 \
    libnss3 \
    libnspr4 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxrandr2 \
    libgbm1 \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright browsers
RUN playwright install --with-deps

# Install Node.js dependencies
RUN npm install -g pa11y pa11y-ci lighthouse

# Copy application code
COPY . .

# Run as non-root user
RUN useradd -m -u 1000 uxuser && chown -R uxuser:uxuser /app
USER uxuser

# Set entrypoint
ENTRYPOINT ["python", "-m", "ux_research.cli.ux_cli"]
```

### Docker Compose

Create `docker-compose.yml`:

```yaml
version: '3.8'

services:
  ux-research:
    build: .
    volumes:
      - ./reports:/app/reports
      - ./config:/app/config
    environment:
      - GOOGLE_ANALYTICS_PROPERTY_ID=${GOOGLE_ANALYTICS_PROPERTY_ID}
      - HOTJAR_SITE_ID=${HOTJAR_SITE_ID}
      - GITHUB_TOKEN=${GITHUB_TOKEN}
    command: --help
```

### Build and Run

```bash
# Build Docker image
docker build -t ux-research:latest .

# Run audit
docker run --rm -v $(pwd)/reports:/app/reports \
  ux-research:latest audit --url https://example.com

# Use docker-compose
docker-compose up
```

## Troubleshooting

### Issue: Python version mismatch

```bash
# Error: Python 3.9 detected, 3.10+ required

# Solution: Install Python 3.11
# macOS
brew install python@3.11

# Ubuntu
sudo apt install python3.11

# Windows
choco install python311
```

### Issue: Playwright installation fails

```bash
# Error: Failed to download browsers

# Solution 1: Install with dependencies
playwright install --with-deps

# Solution 2: Set proxy (if behind corporate firewall)
export HTTPS_PROXY=http://proxy.company.com:8080
playwright install

# Solution 3: Manual download
PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD=1 pip install playwright
playwright install chromium
```

### Issue: Permission denied on Linux

```bash
# Error: Permission denied when running browsers

# Solution: Add user to required groups
sudo usermod -a -G video $USER
sudo usermod -a -G render $USER

# Logout and login for changes to take effect
```

### Issue: pa11y not found

```bash
# Error: pa11y: command not found

# Solution: Install globally
sudo npm install -g pa11y pa11y-ci

# Or add npm global bin to PATH
export PATH="$PATH:$(npm config get prefix)/bin"
```

### Issue: Memory errors during audits

```bash
# Error: JavaScript heap out of memory

# Solution: Increase Node.js memory
export NODE_OPTIONS="--max-old-space-size=4096"

# Or reduce concurrent audits in config
crawling:
  max_concurrent: 2  # Reduce from default 5
```

### Issue: SSL certificate errors

```bash
# Error: SSL: CERTIFICATE_VERIFY_FAILED

# Solution 1: Install certificates (macOS)
/Applications/Python\ 3.11/Install\ Certificates.command

# Solution 2: Set certificate path
export REQUESTS_CA_BUNDLE=/etc/ssl/certs/ca-certificates.crt

# Solution 3: Disable verification (not recommended for production)
export PYTHONHTTPSVERIFY=0
```

### Issue: Import errors after installation

```bash
# Error: ModuleNotFoundError: No module named 'ux_research'

# Solution 1: Verify virtual environment
which python  # Should point to venv

# Solution 2: Install in editable mode
pip install -e .

# Solution 3: Add to PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:/path/to/devCrew_s1/tools"
```

### Getting Help

If issues persist:

1. Check logs in `~/.ux-research/logs/`
2. Run with debug mode: `ux-tool --debug audit --url https://example.com`
3. Create issue on GitHub with error message and system info
4. Contact Platform Engineering team

## Next Steps

After successful installation:

1. Review [WCAG Guide](wcag_guide.md) to understand compliance standards
2. Follow [Accessibility Testing Guide](accessibility_testing.md) for workflows
3. Configure [CI/CD Integration](ci_cd_integration.md) for automated testing
4. Explore [Feedback Analysis](feedback_analysis.md) for user insights

## Update Instructions

```bash
# Pull latest changes
cd devCrew_s1
git pull origin master

# Update dependencies
cd tools/ux_research
pip install --upgrade -r requirements.txt

# Update Playwright browsers
playwright install

# Run tests to verify
pytest -v
```

## Uninstallation

```bash
# Remove virtual environment
rm -rf venv

# Remove Playwright browsers
rm -rf ~/Library/Caches/ms-playwright  # macOS
rm -rf ~/.cache/ms-playwright  # Linux
rmdir /s "%USERPROFILE%\AppData\Local\ms-playwright"  # Windows

# Uninstall global npm packages
npm uninstall -g pa11y pa11y-ci lighthouse

# Remove configuration
rm -rf ~/.ux-research
```
