# DevGRU Setup - Troubleshooting Guide

## Table of Contents

1. [Installation Issues](#installation-issues)
2. [Permission Problems](#permission-problems)
3. [Package Conflicts](#package-conflicts)
4. [Database Connection Issues](#database-connection-issues)
5. [Python Version Issues](#python-version-issues)
6. [Virtual Environment Problems](#virtual-environment-problems)
7. [Network and Firewall Issues](#network-and-firewall-issues)
8. [Platform-Specific Problems](#platform-specific-problems)
9. [Debugging Tips](#debugging-tips)
10. [Log File Locations](#log-file-locations)
11. [FAQ](#faq)

---

## Installation Issues

### Script Won't Execute

**Problem**: Script doesn't run when executed

**Symptoms**:
```bash
./setup_devgru.sh
-bash: ./setup_devgru.sh: Permission denied
```

**Solutions**:

1. Make the script executable:
```bash
chmod +x /Users/tamnguyen/Documents/GitHub/devCrew_s1/devgru_setup/setup_devgru.sh
```

2. Verify the script is executable:
```bash
ls -lh /Users/tamnguyen/Documents/GitHub/devCrew_s1/devgru_setup/setup_devgru.sh
# Should show: -rwxr-xr-x
```

3. Run with bash explicitly:
```bash
bash /Users/tamnguyen/Documents/GitHub/devCrew_s1/devgru_setup/setup_devgru.sh
```

---

### Missing Prerequisites File

**Problem**: Script cannot find prerequisites_validated.json

**Symptoms**:
```
[ERROR] Prerequisites file not found: /tmp/issue67_work/prerequisites_validated.json
```

**Solutions**:

1. Verify the prerequisites file exists:
```bash
ls -lh /tmp/issue67_work/prerequisites_validated.json
```

2. If missing, regenerate prerequisites:
```bash
# Navigate to project directory
cd /Users/tamnguyen/Documents/GitHub/devCrew_s1/devgru_setup

# Ensure work directory exists
mkdir -p /tmp/issue67_work

# Check if there's a prerequisites generation script
ls -la | grep -i prereq
```

3. Verify JSON validity:
```bash
cat /tmp/issue67_work/prerequisites_validated.json | jq .
```

---

### Package Manager Not Found

**Problem**: System package manager is not detected

**Symptoms**:
```
[ERROR] Unsupported package manager: none
```

**Solutions**:

**macOS**:
```bash
# Install Homebrew
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Add Homebrew to PATH (Apple Silicon)
echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> ~/.zprofile
eval "$(/opt/homebrew/bin/brew shellenv)"

# Add Homebrew to PATH (Intel)
echo 'eval "$(/usr/local/bin/brew shellenv)"' >> ~/.zprofile
eval "$(/usr/local/bin/brew shellenv)"
```

**Ubuntu/Debian**:
```bash
# Update package lists
sudo apt-get update

# Verify apt is available
which apt-get
```

**RHEL/CentOS/Fedora**:
```bash
# Verify yum/dnf is available
which yum || which dnf

# Update package cache
sudo yum makecache || sudo dnf makecache
```

---

### Installation Hangs or Freezes

**Problem**: Installation process stops responding

**Solutions**:

1. Check for prompts requiring user input:
   - Press Enter if waiting for confirmation
   - Look for password prompts

2. Verify network connectivity:
```bash
# Test internet connection
ping -c 3 8.8.8.8

# Test DNS resolution
nslookup pypi.org
```

3. Cancel and restart with verbose mode:
```bash
# Press Ctrl+C to cancel
# Run with verbose output
./setup_devgru.sh --profile standard --verbose
```

4. Check system resources:
```bash
# Check available disk space
df -h

# Check memory usage
free -h    # Linux
vm_stat    # macOS

# Check running processes
top
```

---

## Permission Problems

### Sudo Password Required

**Problem**: Installation requires sudo password but fails

**Solutions**:

1. Run with proper privileges:
```bash
# Test sudo access
sudo -v

# Run setup script (it will request sudo when needed)
./setup_devgru.sh
```

2. Configure sudo to cache credentials longer:
```bash
# Edit sudoers file (carefully!)
sudo visudo

# Add this line (allows 60 minutes of cached sudo):
Defaults timestamp_timeout=60
```

3. For non-interactive environments:
```bash
# Add user to sudoers with NOPASSWD (use with caution!)
# This should only be done in secure, controlled environments
echo "$(whoami) ALL=(ALL) NOPASSWD:ALL" | sudo tee /etc/sudoers.d/devgru_setup
```

---

### Python Package Permission Denied

**Problem**: Cannot install Python packages due to permissions

**Symptoms**:
```
ERROR: Could not install packages due to an OSError: [Errno 13] Permission denied
```

**Solutions**:

1. Use --user flag for pip:
```bash
python3 -m pip install --user package_name
```

2. Fix pip directory permissions:
```bash
# macOS/Linux
sudo chown -R $(whoami) ~/.local/lib/python3.*/site-packages
```

3. Use virtual environment (recommended):
```bash
python3 -m venv ~/.devgru_venv
source ~/.devgru_venv/bin/activate
pip install package_name
```

4. On macOS, use system-specific Python:
```bash
# Avoid using system Python
brew install python@3.10
python3.10 -m pip install package_name
```

---

### File System Write Errors

**Problem**: Cannot write to logs or state directories

**Solutions**:

1. Check directory permissions:
```bash
ls -la /Users/tamnguyen/Documents/GitHub/devCrew_s1/devgru_setup/
```

2. Fix permissions:
```bash
cd /Users/tamnguyen/Documents/GitHub/devCrew_s1/devgru_setup
chmod 755 .
chmod -R 755 logs/ .state/
```

3. Check disk space:
```bash
df -h /Users/tamnguyen/Documents/GitHub/devCrew_s1
```

---

## Package Conflicts

### Conflicting Package Versions

**Problem**: Package version conflicts during installation

**Symptoms**:
```
ERROR: package-a 1.0 has requirement package-b>=2.0, but you'll have package-b 1.5
```

**Solutions**:

1. Use virtual environment to isolate dependencies:
```bash
python3 -m venv devgru_clean_env
source devgru_clean_env/bin/activate
pip install --upgrade pip
./setup_devgru.sh
```

2. Upgrade conflicting packages:
```bash
pip install --upgrade package-b
```

3. Use pip's dependency resolver:
```bash
pip install --use-feature=2020-resolver package_name
```

4. Check installed versions:
```bash
pip list | grep package-name
pip show package-name
```

---

### Homebrew Formula Conflicts

**Problem**: Homebrew package conflicts on macOS

**Symptoms**:
```
Error: Cannot install package because conflicting formulae are installed
```

**Solutions**:

1. List conflicting packages:
```bash
brew list | grep package-name
```

2. Unlink conflicting formula:
```bash
brew unlink conflicting-package
brew install desired-package
```

3. Update Homebrew and upgrade packages:
```bash
brew update
brew upgrade
brew cleanup
```

4. Check for broken symlinks:
```bash
brew doctor
```

---

### Python Package Build Failures

**Problem**: Package fails to compile during installation

**Symptoms**:
```
error: command 'gcc' failed with exit status 1
```

**Solutions**:

**macOS**:
```bash
# Install Xcode Command Line Tools
xcode-select --install

# Install build dependencies via Homebrew
brew install gcc openssl readline sqlite3 xz zlib

# Set compiler flags
export CFLAGS="-I$(brew --prefix openssl)/include"
export LDFLAGS="-L$(brew --prefix openssl)/lib"
```

**Ubuntu/Debian**:
```bash
# Install build essentials
sudo apt-get update
sudo apt-get install -y build-essential python3-dev libssl-dev libffi-dev

# For specific packages
sudo apt-get install -y libpq-dev              # For psycopg2
sudo apt-get install -y libxml2-dev libxslt-dev # For lxml
```

**RHEL/CentOS**:
```bash
# Install development tools
sudo yum groupinstall -y "Development Tools"
sudo yum install -y python3-devel openssl-devel libffi-devel
```

---

## Database Connection Issues

### Redis Connection Refused

**Problem**: Cannot connect to Redis server

**Symptoms**:
```
redis.exceptions.ConnectionError: Error 61 connecting to localhost:6379. Connection refused.
```

**Solutions**:

1. Verify Redis is running:
```bash
# macOS
brew services list | grep redis
redis-cli ping  # Should return PONG

# Linux
sudo systemctl status redis
sudo systemctl start redis

# Check process
ps aux | grep redis-server
```

2. Start Redis manually:
```bash
# macOS
brew services start redis

# Linux with systemd
sudo systemctl start redis

# Manual start
redis-server /etc/redis/redis.conf
```

3. Check Redis port:
```bash
# Verify Redis is listening
lsof -i :6379
netstat -an | grep 6379

# Test connection
redis-cli -h localhost -p 6379 ping
```

4. Check Redis configuration:
```bash
# macOS
cat $(brew --prefix)/etc/redis.conf | grep bind

# Linux
cat /etc/redis/redis.conf | grep bind

# Ensure it allows local connections
bind 127.0.0.1 ::1
```

5. Check firewall:
```bash
# macOS
sudo pfctl -sr | grep 6379

# Linux (firewalld)
sudo firewall-cmd --list-ports

# Linux (ufw)
sudo ufw status
```

---

### PostgreSQL Connection Failed

**Problem**: Cannot connect to PostgreSQL database

**Symptoms**:
```
psycopg2.OperationalError: could not connect to server: Connection refused
```

**Solutions**:

1. Verify PostgreSQL is running:
```bash
# macOS
brew services list | grep postgresql
psql --version

# Linux
sudo systemctl status postgresql
sudo -u postgres psql -c "SELECT version();"

# Check process
ps aux | grep postgres
```

2. Start PostgreSQL:
```bash
# macOS
brew services start postgresql@15

# Linux
sudo systemctl start postgresql
sudo systemctl enable postgresql

# Check status
sudo systemctl is-active postgresql
```

3. Initialize PostgreSQL database (if first time):
```bash
# macOS
initdb /usr/local/var/postgres

# Linux
sudo postgresql-setup --initdb
```

4. Check PostgreSQL port:
```bash
# Default port is 5432
lsof -i :5432
netstat -an | grep 5432
```

5. Fix connection settings:
```bash
# Find postgresql.conf
# macOS: /usr/local/var/postgres/postgresql.conf
# Linux: /etc/postgresql/15/main/postgresql.conf

# Ensure these settings:
listen_addresses = 'localhost'
port = 5432

# Find pg_hba.conf and ensure local connections are allowed:
# TYPE  DATABASE        USER            ADDRESS                 METHOD
local   all             all                                     trust
host    all             all             127.0.0.1/32            md5
```

6. Create user and database:
```bash
# Connect as postgres user
sudo -u postgres psql

# In psql:
CREATE USER devgru WITH PASSWORD 'your_password';
CREATE DATABASE devgru_db OWNER devgru;
GRANT ALL PRIVILEGES ON DATABASE devgru_db TO devgru;
\q

# Test connection
psql -h localhost -U devgru -d devgru_db
```

---

### Neo4j Installation Issues

**Problem**: Neo4j requires manual installation or fails to start

**Solutions**:

1. Install via Homebrew (macOS):
```bash
brew install neo4j
brew services start neo4j
```

2. Install via apt (Ubuntu/Debian):
```bash
# Add Neo4j repository
wget -O - https://debian.neo4j.com/neotechnology.gpg.key | sudo apt-key add -
echo 'deb https://debian.neo4j.com stable latest' | sudo tee /etc/apt/sources.list.d/neo4j.list
sudo apt-get update
sudo apt-get install neo4j

# Start Neo4j
sudo systemctl start neo4j
```

3. Run via Docker (recommended for all platforms):
```bash
docker run -d \
  --name neo4j \
  -p 7474:7474 -p 7687:7687 \
  -e NEO4J_AUTH=neo4j/your_password \
  -v $HOME/neo4j/data:/data \
  neo4j:5.15
```

4. Access Neo4j Browser:
```bash
# Open in browser
open http://localhost:7474  # macOS
xdg-open http://localhost:7474  # Linux

# Default credentials: neo4j/neo4j (change on first login)
```

5. Check Neo4j status:
```bash
# If installed as service
neo4j status

# If running in Docker
docker ps | grep neo4j
docker logs neo4j
```

---

## Python Version Issues

### Python Version Too Old

**Problem**: System Python is older than 3.10

**Symptoms**:
```
[ERROR] Python 3.10+ is required, but found Python 3.8
```

**Solutions**:

1. Install Python 3.10+ using pyenv (recommended):
```bash
# Install pyenv
curl https://pyenv.run | bash

# Add to shell configuration (~/.bashrc, ~/.zshrc)
export PATH="$HOME/.pyenv/bin:$PATH"
eval "$(pyenv init -)"
eval "$(pyenv virtualenv-init -)"

# Restart shell or source config
source ~/.zshrc  # or ~/.bashrc

# Install Python 3.10
pyenv install 3.10.13
pyenv global 3.10.13

# Verify
python --version
```

2. Install via Homebrew (macOS):
```bash
brew install python@3.10
brew link python@3.10

# Add to PATH
export PATH="/usr/local/opt/python@3.10/bin:$PATH"

# Verify
python3.10 --version
```

3. Install via apt (Ubuntu/Debian):
```bash
# Add deadsnakes PPA (for older Ubuntu versions)
sudo add-apt-repository ppa:deadsnakes/ppa
sudo apt-get update
sudo apt-get install -y python3.10 python3.10-venv python3.10-dev

# Set as default
sudo update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.10 1
```

4. Install via dnf (RHEL/Fedora):
```bash
sudo dnf install python3.10 python3.10-devel
```

---

### Multiple Python Versions Conflict

**Problem**: Multiple Python versions causing confusion

**Solutions**:

1. List all Python installations:
```bash
# Find Python executables
which -a python python3 python3.10 python3.11

# Check versions
python --version
python3 --version
python3.10 --version
```

2. Use specific Python version:
```bash
# Instead of python3, use:
python3.10 -m pip install package_name
```

3. Set up aliases in shell config:
```bash
# Add to ~/.bashrc or ~/.zshrc
alias python=python3.10
alias pip='python3.10 -m pip'
```

4. Use pyenv to manage versions:
```bash
pyenv versions
pyenv global 3.10.13
pyenv local 3.10.13  # For specific directory
```

---

### pip Not Found or Outdated

**Problem**: pip is not installed or too old

**Solutions**:

1. Install pip:
```bash
# macOS/Linux
python3 -m ensurepip --upgrade

# Ubuntu/Debian
sudo apt-get install python3-pip

# RHEL/CentOS
sudo yum install python3-pip
```

2. Upgrade pip:
```bash
python3 -m pip install --upgrade pip
```

3. Use get-pip.py:
```bash
curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py
python3 get-pip.py
rm get-pip.py
```

4. Fix pip SSL certificate errors:
```bash
pip install --trusted-host pypi.org --trusted-host files.pythonhosted.org --upgrade pip
```

---

## Virtual Environment Problems

### Cannot Create Virtual Environment

**Problem**: venv module fails to create virtual environment

**Symptoms**:
```
Error: Command '['/path/to/venv/bin/python3', '-m', 'ensurepip']' returned non-zero exit status 1
```

**Solutions**:

1. Install python3-venv:
```bash
# Ubuntu/Debian
sudo apt-get install python3.10-venv

# RHEL/CentOS
sudo yum install python310-venv
```

2. Create venv with system site packages:
```bash
python3 -m venv --system-site-packages myenv
```

3. Use virtualenv instead of venv:
```bash
pip install virtualenv
virtualenv -p python3.10 myenv
```

---

### Virtual Environment Activation Fails

**Problem**: Cannot activate virtual environment

**Solutions**:

1. Check activation script exists:
```bash
ls -la myenv/bin/activate
```

2. Use correct activation command:
```bash
# Bash/Zsh
source myenv/bin/activate

# Fish shell
source myenv/bin/activate.fish

# Csh/Tcsh
source myenv/bin/activate.csh

# Windows (if using WSL2)
source myenv/Scripts/activate
```

3. Fix activation script permissions:
```bash
chmod +x myenv/bin/activate
```

4. Manually set environment variables:
```bash
export VIRTUAL_ENV="/path/to/myenv"
export PATH="$VIRTUAL_ENV/bin:$PATH"
```

---

### Packages Not Found After Installation

**Problem**: Installed packages not accessible in virtual environment

**Solutions**:

1. Verify you're in the correct virtual environment:
```bash
which python
echo $VIRTUAL_ENV
```

2. Reinstall package in virtual environment:
```bash
source myenv/bin/activate
pip install package_name
pip list | grep package_name
```

3. Check sys.path:
```bash
python -c "import sys; print('\n'.join(sys.path))"
```

4. Recreate virtual environment:
```bash
deactivate
rm -rf myenv
python3 -m venv myenv
source myenv/bin/activate
pip install -r requirements.txt
```

---

## Network and Firewall Issues

### Cannot Download Packages

**Problem**: Network errors during package downloads

**Symptoms**:
```
URLError: <urlopen error [Errno 8] nodename nor servname provided, or not known>
```

**Solutions**:

1. Check internet connectivity:
```bash
ping -c 3 8.8.8.8
ping -c 3 pypi.org
curl -I https://pypi.org
```

2. Check DNS resolution:
```bash
nslookup pypi.org
dig pypi.org

# Try alternative DNS
echo "nameserver 8.8.8.8" | sudo tee /etc/resolv.conf
```

3. Configure proxy (if behind corporate firewall):
```bash
# Set proxy environment variables
export http_proxy="http://proxy.company.com:8080"
export https_proxy="http://proxy.company.com:8080"
export no_proxy="localhost,127.0.0.1"

# For pip specifically
pip install --proxy http://proxy.company.com:8080 package_name
```

4. Use different PyPI mirror:
```bash
pip install -i https://pypi.tuna.tsinghua.edu.cn/simple package_name
```

---

### SSL Certificate Verification Failed

**Problem**: SSL certificate errors during downloads

**Symptoms**:
```
SSLError: [SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed
```

**Solutions**:

1. Update certificates:
```bash
# macOS
pip install --upgrade certifi
/Applications/Python\ 3.10/Install\ Certificates.command

# Ubuntu/Debian
sudo apt-get install ca-certificates
sudo update-ca-certificates

# RHEL/CentOS
sudo yum install ca-certificates
sudo update-ca-trust
```

2. Install certificates for Python:
```bash
python3 -m pip install --upgrade pip setuptools certifi
```

3. Temporary workaround (not recommended for production):
```bash
pip install --trusted-host pypi.org --trusted-host files.pythonhosted.org package_name
```

4. Configure pip to trust hosts:
```bash
# Create/edit ~/.pip/pip.conf
mkdir -p ~/.pip
cat > ~/.pip/pip.conf << EOF
[global]
trusted-host = pypi.org
               files.pythonhosted.org
EOF
```

---

### Firewall Blocking Connections

**Problem**: Firewall preventing access to services

**Solutions**:

1. Check firewall status:
```bash
# macOS
sudo pfctl -s rules

# Linux (firewalld)
sudo firewall-cmd --list-all

# Linux (ufw)
sudo ufw status verbose

# Linux (iptables)
sudo iptables -L -n
```

2. Allow specific ports:
```bash
# macOS - Application Firewall
sudo /usr/libexec/ApplicationFirewall/socketfilterfw --add /path/to/python3

# Linux (firewalld)
sudo firewall-cmd --permanent --add-port=5432/tcp  # PostgreSQL
sudo firewall-cmd --permanent --add-port=6379/tcp  # Redis
sudo firewall-cmd --permanent --add-port=7687/tcp  # Neo4j
sudo firewall-cmd --reload

# Linux (ufw)
sudo ufw allow 5432/tcp
sudo ufw allow 6379/tcp
sudo ufw allow 7687/tcp
```

3. Temporarily disable firewall (for testing only):
```bash
# macOS
sudo pfctl -d

# Linux (ufw)
sudo ufw disable

# Linux (firewalld)
sudo systemctl stop firewalld
```

---

## Platform-Specific Problems

### macOS: System Integrity Protection (SIP)

**Problem**: SIP prevents modifications to system directories

**Symptoms**:
```
Operation not permitted
```

**Solutions**:

1. Never modify system Python - use Homebrew Python:
```bash
brew install python@3.10
```

2. Use user-level installations:
```bash
pip install --user package_name
```

3. Use virtual environments (recommended):
```bash
python3 -m venv myenv
source myenv/bin/activate
```

4. Check SIP status:
```bash
csrutil status
```

Note: Do NOT disable SIP unless absolutely necessary and you understand security implications.

---

### macOS: Apple Silicon (M1/M2/M3) Compatibility

**Problem**: Packages fail on ARM64 architecture

**Solutions**:

1. Use Rosetta 2 for x86_64 packages:
```bash
# Install Rosetta 2
softwareupdate --install-rosetta

# Create x86_64 Homebrew
arch -x86_64 /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Use x86_64 brew
arch -x86_64 brew install python@3.10
```

2. Install native ARM packages when available:
```bash
brew install python@3.10  # Native ARM version
```

3. Check architecture:
```bash
uname -m  # Should show arm64
python3 -c "import platform; print(platform.machine())"
```

---

### macOS: Command Line Tools Not Installed

**Problem**: Missing development tools for compiling packages

**Solutions**:

1. Install Xcode Command Line Tools:
```bash
xcode-select --install
```

2. Verify installation:
```bash
xcode-select -p
# Should output: /Library/Developer/CommandLineTools

gcc --version
clang --version
```

3. Reset Command Line Tools if corrupted:
```bash
sudo rm -rf /Library/Developer/CommandLineTools
xcode-select --install
```

---

### Linux: Missing Development Headers

**Problem**: Cannot compile Python packages due to missing headers

**Solutions**:

**Ubuntu/Debian**:
```bash
sudo apt-get update
sudo apt-get install -y \
  build-essential \
  python3-dev \
  python3.10-dev \
  libssl-dev \
  libffi-dev \
  libxml2-dev \
  libxslt1-dev \
  zlib1g-dev \
  libjpeg-dev \
  libpq-dev
```

**RHEL/CentOS/Fedora**:
```bash
sudo yum groupinstall -y "Development Tools"
sudo yum install -y \
  python3-devel \
  python310-devel \
  openssl-devel \
  libffi-devel \
  libxml2-devel \
  libxslt-devel \
  zlib-devel \
  libjpeg-devel \
  postgresql-devel
```

---

### WSL2: Path and Permission Issues

**Problem**: Windows and Linux path conflicts in WSL2

**Solutions**:

1. Use Linux paths exclusively:
```bash
# Good
cd /home/username/project

# Avoid
cd /mnt/c/Users/Username/project
```

2. Fix line ending issues:
```bash
# Convert CRLF to LF
dos2unix setup_devgru.sh

# Or use sed
sed -i 's/\r$//' setup_devgru.sh
```

3. Set proper file permissions:
```bash
# In /etc/wsl.conf
[automount]
options = "metadata,umask=22,fmask=11"

# Restart WSL2
wsl --shutdown
```

4. Check WSL version:
```bash
wsl --list --verbose
# Should show version 2
```

---

### WSL2: Systemd Services Not Running

**Problem**: Services like PostgreSQL don't start in WSL2

**Solutions**:

1. Enable systemd in WSL2 (Windows 11+):
```bash
# Add to /etc/wsl.conf
[boot]
systemd=true

# Restart WSL
wsl --shutdown
```

2. Manual service start:
```bash
sudo service postgresql start
sudo service redis-server start
```

3. Use Docker for services:
```bash
# Install Docker Desktop for Windows with WSL2 backend
# Run services in containers
docker run -d -p 5432:5432 postgres:15
docker run -d -p 6379:6379 redis:7
```

---

### RHEL/CentOS: Package Repository Issues

**Problem**: Required packages not found in default repositories

**Solutions**:

1. Enable EPEL repository:
```bash
# RHEL 8/9
sudo dnf install epel-release

# CentOS 8
sudo dnf install epel-release
```

2. Enable PowerTools/CodeReady repository:
```bash
# RHEL 8
sudo subscription-manager repos --enable codeready-builder-for-rhel-8-$(arch)-rpms

# CentOS 8
sudo dnf config-manager --set-enabled powertools

# Rocky Linux 8
sudo dnf config-manager --set-enabled powertools
```

3. Update repository cache:
```bash
sudo dnf clean all
sudo dnf makecache
```

---

## Debugging Tips

### Enable Verbose Mode

Run the script with verbose output to see detailed information:

```bash
./setup_devgru.sh --profile standard --verbose
```

This will show:
- All executed commands
- Debug messages
- Detailed error information

---

### Use Dry-Run Mode

Test what would be installed without making changes:

```bash
./setup_devgru.sh --profile full --dry-run
```

This helps:
- Preview installation steps
- Identify potential issues
- Verify prerequisites

---

### Check Installation Logs

Review detailed logs for troubleshooting:

```bash
# Find latest log file
ls -lt /Users/tamnguyen/Documents/GitHub/devCrew_s1/devgru_setup/logs/

# View log
cat /Users/tamnguyen/Documents/GitHub/devCrew_s1/devgru_setup/logs/setup_YYYYMMDD_HHMMSS.log

# Search for errors
grep -i error /Users/tamnguyen/Documents/GitHub/devCrew_s1/devgru_setup/logs/setup_*.log

# Search for warnings
grep -i warning /Users/tamnguyen/Documents/GitHub/devCrew_s1/devgru_setup/logs/setup_*.log

# View last 50 lines
tail -50 /Users/tamnguyen/Documents/GitHub/devCrew_s1/devgru_setup/logs/setup_*.log
```

---

### Verify System Environment

Check system configuration:

```bash
# OS and version
uname -a
cat /etc/os-release  # Linux

# Architecture
uname -m

# Python environment
python3 --version
which python3
python3 -c "import sys; print(sys.executable)"

# pip configuration
python3 -m pip --version
python3 -m pip config list

# Environment variables
env | grep -i python
env | grep -i path

# Disk space
df -h

# Memory
free -h  # Linux
vm_stat  # macOS
```

---

### Test Package Installation Manually

Try installing a problematic package manually:

```bash
# Activate verbose pip output
python3 -m pip install -v package_name

# Use isolated mode
python3 -m pip install --isolated package_name

# Ignore installed packages
python3 -m pip install --ignore-installed package_name

# Show what would be installed
python3 -m pip install --dry-run package_name
```

---

### Check Process and Port Usage

Verify services are running and ports are accessible:

```bash
# List all listening ports
lsof -i -P -n | grep LISTEN    # macOS/Linux
netstat -tulpn | grep LISTEN   # Linux

# Check specific port
lsof -i :6379  # Redis
lsof -i :5432  # PostgreSQL
lsof -i :7687  # Neo4j

# List running processes
ps aux | grep python
ps aux | grep redis
ps aux | grep postgres
```

---

### Validate JSON Configuration

Check configuration files for syntax errors:

```bash
# Validate prerequisites file
jq empty /tmp/issue67_work/prerequisites_validated.json

# Pretty print JSON
jq . /tmp/issue67_work/prerequisites_validated.json

# Query specific fields
jq '.core_packages' /tmp/issue67_work/prerequisites_validated.json
jq '.installed_packages' /Users/tamnguyen/Documents/GitHub/devCrew_s1/devgru_setup/.state/installation_state.json
```

---

### Test Network Connectivity

Diagnose network issues:

```bash
# Test basic connectivity
ping -c 3 8.8.8.8

# Test DNS
nslookup pypi.org
dig pypi.org

# Test HTTPS connection
curl -I https://pypi.org
curl -I https://files.pythonhosted.org

# Check proxy settings
echo $http_proxy
echo $https_proxy

# Test download speed
curl -o /dev/null https://files.pythonhosted.org/packages/any
```

---

### Rollback Failed Installation

If installation fails and you need to rollback:

```bash
# The script will prompt for rollback
# Or manually check what was installed:
cat /Users/tamnguyen/Documents/GitHub/devCrew_s1/devgru_setup/.state/installation_state.json | jq -r '.installed_packages[]'

# Uninstall Python packages
pip uninstall -y package_name

# Remove system packages (macOS)
brew uninstall package_name

# Remove system packages (Ubuntu/Debian)
sudo apt-get remove -y package_name

# Remove system packages (RHEL/CentOS)
sudo yum remove -y package_name
```

---

## Log File Locations

### Main Setup Logs

Location: `/Users/tamnguyen/Documents/GitHub/devCrew_s1/devgru_setup/logs/`

- **Setup logs**: `setup_YYYYMMDD_HHMMSS.log`
  - Contains all installation steps
  - Shows commands executed
  - Records errors and warnings

- **Installation reports**: `installation_report_YYYYMMDD_HHMMSS.txt`
  - Summary of installation
  - List of installed packages
  - Failed packages
  - Next steps

### State File

Location: `/Users/tamnguyen/Documents/GitHub/devCrew_s1/devgru_setup/.state/installation_state.json`

Contains:
- Timestamp of installation
- Profile used
- OS type and version
- Architecture
- List of installed packages
- List of failed packages

### System Logs

**macOS**:
```bash
# Homebrew logs
~/Library/Logs/Homebrew/

# System logs
/var/log/system.log
log show --predicate 'process == "setup_devgru"' --last 1h
```

**Linux**:
```bash
# System logs
/var/log/syslog        # Ubuntu/Debian
/var/log/messages      # RHEL/CentOS

# Journal logs
journalctl -xe
journalctl -u redis
journalctl -u postgresql
```

### Package Manager Logs

**Homebrew (macOS)**:
```bash
# Installation logs
brew log package_name

# Service logs
brew services list
tail -f $(brew --prefix)/var/log/redis.log
tail -f $(brew --prefix)/var/log/postgres.log
```

**APT (Ubuntu/Debian)**:
```bash
# Installation logs
/var/log/apt/history.log
/var/log/apt/term.log

# dpkg logs
/var/log/dpkg.log
```

**YUM/DNF (RHEL/CentOS)**:
```bash
# Installation logs
/var/log/yum.log    # CentOS 7
/var/log/dnf.log    # CentOS 8+, Fedora
```

---

## FAQ

### Q: How do I completely uninstall everything?

**A**: Use the following steps:

```bash
# 1. Check what was installed
cat /Users/tamnguyen/Documents/GitHub/devCrew_s1/devgru_setup/.state/installation_state.json | jq -r '.installed_packages[]'

# 2. Uninstall Python packages
pip freeze | xargs pip uninstall -y

# 3. Remove virtual environment if created
rm -rf ~/.devgru_venv

# 4. Remove system packages (be careful!)
# macOS
brew list | xargs brew uninstall

# Ubuntu/Debian
sudo apt-get autoremove -y

# 5. Clean up state and logs
rm -rf /Users/tamnguyen/Documents/GitHub/devCrew_s1/devgru_setup/.state/
rm -rf /Users/tamnguyen/Documents/GitHub/devCrew_s1/devgru_setup/logs/
```

---

### Q: Can I run the script multiple times?

**A**: Yes, the script is idempotent and checks if packages are already installed. However:

- Already installed packages will be skipped
- You can use `--dry-run` to preview changes
- Different profiles can be used for different purposes

---

### Q: How do I upgrade installed packages?

**A**: Upgrade packages separately from the setup script:

```bash
# Upgrade Python packages
pip list --outdated
pip install --upgrade package_name

# Or upgrade all packages
pip list --outdated --format=freeze | cut -d = -f 1 | xargs -n1 pip install -U

# Upgrade system packages (macOS)
brew update
brew upgrade

# Upgrade system packages (Ubuntu/Debian)
sudo apt-get update
sudo apt-get upgrade

# Upgrade system packages (RHEL/CentOS)
sudo yum update
```

---

### Q: Which profile should I use?

**A**: Choose based on your needs:

- **minimal**: CI/CD pipelines, minimal footprint (5 packages)
- **standard**: General development (20 packages) - **Recommended**
- **full**: Complete stack with databases and tools
- **security**: Security auditing and compliance
- **cloud-aws**: AWS development
- **cloud-azure**: Azure development
- **cloud-gcp**: GCP development

---

### Q: Can I customize the installation?

**A**: Yes, you can:

1. Edit requirements files:
   - `/Users/tamnguyen/Documents/GitHub/devCrew_s1/devgru_setup/requirements/requirements-core.txt`
   - `/Users/tamnguyen/Documents/GitHub/devCrew_s1/devgru_setup/requirements/requirements-optional.txt`

2. Use skip options:
   ```bash
   ./setup_devgru.sh --profile full --skip-databases --skip-tools
   ```

3. Install additional packages after setup:
   ```bash
   pip install additional_package
   ```

---

### Q: How do I check if installation was successful?

**A**: Run these verification commands:

```bash
# 1. Check Python version
python3 --version  # Should be 3.10+

# 2. Verify pip works
pip --version

# 3. Test core packages
python3 -c "import pandas, requests, pydantic, celery; print('Core packages OK')"

# 4. List installed packages
pip list

# 5. Check installation report
cat /Users/tamnguyen/Documents/GitHub/devCrew_s1/devgru_setup/logs/installation_report_*.txt

# 6. Verify databases (if installed)
redis-cli ping        # Should return PONG
psql --version        # Should show PostgreSQL 15+
```

---

### Q: What if I encounter a package not listed here?

**A**: For unlisted issues:

1. Check the detailed log files
2. Search for the error message online
3. Try installing the package manually with verbose output:
   ```bash
   python3 -m pip install -v package_name
   ```
4. Report the issue with:
   - Error message
   - Log file contents
   - System information (OS, version, architecture)
   - Installation command used

---

### Q: How do I configure cloud provider credentials?

**A**: After installing cloud profiles:

**AWS**:
```bash
# Configure credentials
aws configure

# Verify
aws sts get-caller-identity
```

**Azure**:
```bash
# Login
az login

# Set subscription
az account set --subscription "subscription-id"

# Verify
az account show
```

**GCP**:
```bash
# Login
gcloud auth login

# Set project
gcloud config set project project-id

# Verify
gcloud auth list
gcloud config list
```

---

### Q: Where can I get additional help?

**A**: Resources:

1. **Documentation**:
   - Main README: `/Users/tamnguyen/Documents/GitHub/devCrew_s1/devgru_setup/README.md`
   - Quick Start: `/Users/tamnguyen/Documents/GitHub/devCrew_s1/devgru_setup/QUICK_START.md`
   - This Guide: `/Users/tamnguyen/Documents/GitHub/devCrew_s1/devgru_setup/docs/TROUBLESHOOTING.md`

2. **Logs**:
   - Setup logs: `/Users/tamnguyen/Documents/GitHub/devCrew_s1/devgru_setup/logs/`
   - State file: `/Users/tamnguyen/Documents/GitHub/devCrew_s1/devgru_setup/.state/installation_state.json`

3. **Command Help**:
   ```bash
   ./setup_devgru.sh --help
   ```

4. **Python Documentation**:
   - https://docs.python.org/3/
   - https://pip.pypa.io/en/stable/

5. **Package Managers**:
   - Homebrew: https://docs.brew.sh/
   - APT: https://wiki.debian.org/Apt
   - DNF: https://dnf.readthedocs.io/

---

## Quick Reference Commands

### Essential Troubleshooting Commands

```bash
# Check setup status
cat /Users/tamnguyen/Documents/GitHub/devCrew_s1/devgru_setup/.state/installation_state.json | jq .

# View latest log
tail -100 /Users/tamnguyen/Documents/GitHub/devCrew_s1/devgru_setup/logs/setup_*.log

# Test with dry-run
./setup_devgru.sh --profile standard --dry-run

# Run with verbose output
./setup_devgru.sh --profile standard --verbose

# Check Python and pip
python3 --version && pip --version

# List installed packages
pip list

# Verify core packages
python3 -c "import pandas, requests, pydantic, celery, playwright; print('All core packages OK')"

# Check service status (macOS)
brew services list

# Check service status (Linux)
sudo systemctl status redis postgresql

# Test database connections
redis-cli ping
psql --version
```

---

## Reporting Issues

When reporting issues, include:

1. **Error message**: Exact error from logs
2. **System info**: OS, version, architecture
3. **Command used**: Full command that failed
4. **Log excerpt**: Relevant log file sections
5. **Steps to reproduce**: What you did before the error

**Example Issue Report**:

```
Issue: PostgreSQL installation fails on macOS

System: macOS 13.5, Apple Silicon (arm64)

Command:
./setup_devgru.sh --profile full

Error:
[ERROR] Failed to install PostgreSQL
Error: postgresql@15: Failed to download resource

Log location:
/Users/tamnguyen/Documents/GitHub/devCrew_s1/devgru_setup/logs/setup_20251120_143022.log

Steps to reproduce:
1. Run setup with full profile
2. Error occurs during PostgreSQL installation

Additional context:
Network connection is stable, other packages installed successfully.
```

---

## Conclusion

This troubleshooting guide covers the most common issues encountered during DevGRU setup. For issues not covered here:

1. Check the main documentation
2. Review log files with verbose output
3. Test components individually
4. Search for specific error messages
5. Report new issues with detailed information

Remember:
- Always use `--dry-run` first
- Check logs for detailed error information
- Use virtual environments for isolation
- Keep packages updated
- Document custom configurations
