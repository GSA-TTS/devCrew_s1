# Platform-Specific Documentation

## Table of Contents

1. [Overview](#overview)
2. [macOS Platform](#macos-platform)
3. [Ubuntu/Debian Platform](#ubuntudebian-platform)
4. [RHEL/CentOS/Fedora Platform](#rhelcentosfedora-platform)
5. [Windows WSL2 Platform](#windows-wsl2-platform)
6. [Version Compatibility Matrix](#version-compatibility-matrix)
7. [Performance Optimization](#performance-optimization)
8. [Known Limitations](#known-limitations)
9. [Troubleshooting by Platform](#troubleshooting-by-platform)

---

## Overview

This document provides platform-specific guidance for installing and configuring the DevGRU development environment. Each platform has unique considerations, prerequisites, and optimization strategies that are essential for successful deployment.

### Supported Platforms

| Platform | Versions | Architectures | Status |
|----------|----------|--------------|--------|
| macOS | 10.15+ (Catalina and later) | x86_64, arm64 (M1/M2/M3) | Fully Supported |
| Ubuntu | 20.04 LTS, 22.04 LTS, 24.04 LTS | x86_64, arm64 | Fully Supported |
| Debian | 10 (Buster), 11 (Bullseye), 12 (Bookworm) | x86_64, arm64 | Fully Supported |
| RHEL | 8.x, 9.x | x86_64, arm64 | Fully Supported |
| CentOS | Stream 8, Stream 9 | x86_64, arm64 | Fully Supported |
| Fedora | 35+, 36+, 37+ | x86_64, arm64 | Fully Supported |
| Windows WSL2 | Ubuntu 20.04+, Debian 11+ | x86_64 | Fully Supported |

---

## macOS Platform

### Prerequisites

#### 1. Homebrew Installation

Homebrew is the primary package manager for macOS and is **required** before running the DevGRU setup script.

```bash
# Install Homebrew
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Verify installation
brew --version

# Add Homebrew to PATH (if not already added)
# For Intel Macs:
echo 'eval "$(/usr/local/bin/brew shellenv)"' >> ~/.zprofile
eval "$(/usr/local/bin/brew shellenv)"

# For Apple Silicon Macs (M1/M2/M3):
echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> ~/.zprofile
eval "$(/opt/homebrew/bin/brew shellenv)"
```

#### 2. Command Line Tools

Install Xcode Command Line Tools for essential build utilities:

```bash
# Install Command Line Tools
xcode-select --install

# Verify installation
xcode-select -p
# Expected output: /Library/Developer/CommandLineTools
```

#### 3. Rosetta 2 (Apple Silicon Only)

For M1/M2/M3 Macs, install Rosetta 2 for x86_64 compatibility:

```bash
# Install Rosetta 2
softwareupdate --install-rosetta --agree-to-license

# Verify installation
/usr/sbin/sysctl -n machdep.cpu.brand_string
```

### System Integrity Protection (SIP) Considerations

#### What is SIP?

System Integrity Protection (SIP) is a macOS security feature that restricts root user access to protected system files and directories.

#### Impact on DevGRU Setup

- **Low Impact**: DevGRU setup primarily uses Homebrew and user-space installations
- **Protected Paths**: `/System`, `/usr` (except `/usr/local`), and system applications
- **Allowed Paths**: `/usr/local`, `/opt/homebrew`, user home directory

#### When to Disable SIP

**NOT RECOMMENDED** for DevGRU setup. Only disable if:
- Installing kernel extensions
- Modifying system frameworks
- Debugging low-level system components

#### How to Check SIP Status

```bash
# Check SIP status
csrutil status
# Output: System Integrity Protection status: enabled
```

#### Safe Installation Practices

```bash
# Use Homebrew's designated paths
brew --prefix
# Intel: /usr/local
# Apple Silicon: /opt/homebrew

# Install to user-writable locations
pip install --user package_name

# Use virtual environments
python3 -m venv ~/.venvs/devgru
```

### M1/M2/M3 (Apple Silicon) Compatibility

#### Architecture Detection

The DevGRU script automatically detects your Mac's architecture:

```bash
# Check architecture
uname -m
# Output: arm64 (Apple Silicon) or x86_64 (Intel)
```

#### Native vs. Rosetta Packages

| Package | Native arm64 | Rosetta x86_64 | Notes |
|---------|-------------|----------------|-------|
| Homebrew | Yes | Yes (via arch -x86_64) | Prefer native |
| Python 3.10+ | Yes | Yes | Excellent native support |
| Node.js 18+ | Yes | Yes | Full native support |
| Docker Desktop | Yes | N/A | Native with Rosetta containers |
| PostgreSQL | Yes | Yes | Native recommended |
| Redis | Yes | Yes | Native recommended |

#### Running Commands in Different Architectures

```bash
# Run as native arm64 (default on M1/M2/M3)
python3 --version

# Force x86_64 mode using Rosetta
arch -x86_64 python3 --version

# Install x86_64 Homebrew (legacy compatibility)
arch -x86_64 /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

#### Known M1/M2/M3 Issues

1. **NumPy/SciPy Performance**
   - Solution: Install via Homebrew for optimized builds
   ```bash
   brew install numpy scipy
   ```

2. **TensorFlow/PyTorch**
   - Solution: Use Apple Metal acceleration
   ```bash
   pip install tensorflow-macos tensorflow-metal
   pip install torch torchvision torchaudio
   ```

3. **Docker Container Architecture**
   - Solution: Specify platform explicitly
   ```bash
   docker run --platform linux/amd64 image_name
   ```

### macOS Version-Specific Notes

#### macOS 14 (Sonoma) and Later
- Enhanced security for network operations
- Requires explicit permission for Python network access
- Gatekeeper may block unsigned binaries

```bash
# Allow Python network access
sudo codesign --force --deep --sign - $(which python3)

# Bypass Gatekeeper for specific apps
xattr -d com.apple.quarantine /path/to/application
```

#### macOS 13 (Ventura)
- Improved Python framework support
- Better virtualization performance for Docker

#### macOS 12 (Monterey)
- Universal Control may interfere with USB debugging
- Enhanced privacy controls for disk access

### Performance Optimization (macOS)

#### 1. Homebrew Optimization

```bash
# Disable analytics for faster operations
brew analytics off

# Clean up old versions
brew cleanup -s

# Update Homebrew efficiently
brew update --auto-update

# Use shallow clones
export HOMEBREW_NO_GITHUB_API=1
```

#### 2. Python Performance

```bash
# Use Homebrew Python (optimized for macOS)
brew install python@3.10

# Install packages with binary wheels
pip install --prefer-binary package_name

# Enable compiler optimizations
export CFLAGS="-O3 -march=native"
export CXXFLAGS="-O3 -march=native"
```

#### 3. Database Performance

```bash
# PostgreSQL optimization
brew services start postgresql@15
echo "shared_buffers = 256MB" >> $(brew --prefix)/var/postgresql@15/postgresql.conf

# Redis optimization
brew services start redis
echo "maxmemory 512mb" >> $(brew --prefix)/etc/redis.conf
echo "maxmemory-policy allkeys-lru" >> $(brew --prefix)/etc/redis.conf
```

#### 4. Filesystem Performance

```bash
# Disable Spotlight indexing for development directories
sudo mdutil -i off ~/Development

# Exclude from Time Machine backups
tmutil addexclusion ~/Development/node_modules
tmutil addexclusion ~/Development/.venv
```

### macOS-Specific Environment Variables

```bash
# Add to ~/.zshrc or ~/.bash_profile

# Homebrew optimization
export HOMEBREW_NO_AUTO_UPDATE=1
export HOMEBREW_NO_ANALYTICS=1

# Python optimization
export PYTHONUNBUFFERED=1
export PIP_REQUIRE_VIRTUALENV=true

# Build optimization
export ARCHFLAGS="-arch $(uname -m)"

# OpenSSL paths (for Python packages)
export LDFLAGS="-L$(brew --prefix)/opt/openssl@3/lib"
export CPPFLAGS="-I$(brew --prefix)/opt/openssl@3/include"
```

---

## Ubuntu/Debian Platform

### Prerequisites

#### 1. System Update

Always update system packages before installation:

```bash
# Update package index
sudo apt-get update

# Upgrade existing packages
sudo apt-get upgrade -y

# Install essential build tools
sudo apt-get install -y build-essential
```

#### 2. Required System Packages

```bash
# Development tools
sudo apt-get install -y \
    curl \
    wget \
    git \
    jq \
    ca-certificates \
    gnupg \
    lsb-release

# Python development headers
sudo apt-get install -y \
    python3-dev \
    python3-pip \
    python3-venv \
    python3-setuptools

# Compiler and libraries
sudo apt-get install -y \
    gcc \
    g++ \
    make \
    libssl-dev \
    libffi-dev \
    libxml2-dev \
    libxslt1-dev \
    zlib1g-dev
```

#### 3. Non-Root User Setup

```bash
# Create DevGRU user (if needed)
sudo adduser devgru

# Add to sudo group
sudo usermod -aG sudo devgru

# Add to docker group (after Docker installation)
sudo usermod -aG docker devgru
```

### Repository Configuration

#### Adding PPAs (Personal Package Archives)

PPAs provide newer versions of packages than the default Ubuntu repositories.

```bash
# Add deadsnakes PPA for Python versions
sudo add-apt-repository ppa:deadsnakes/ppa -y
sudo apt-get update

# Install specific Python version
sudo apt-get install -y python3.10 python3.10-venv python3.10-dev

# Verify installation
python3.10 --version
```

#### Official Package Repositories

##### Docker Repository

```bash
# Add Docker's official GPG key
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | \
    sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
sudo chmod a+r /etc/apt/keyrings/docker.gpg

# Set up Docker repository
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] \
  https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Install Docker
sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io
```

##### PostgreSQL Repository

```bash
# Add PostgreSQL APT repository
sudo sh -c 'echo "deb http://apt.postgresql.org/pub/repos/apt $(lsb_release -cs)-pgdg main" > \
    /etc/apt/sources.list.d/pgdg.list'
wget --quiet -O - https://www.postgresql.org/media/keys/ACCC4CF8.asc | sudo apt-key add -
sudo apt-get update

# Install PostgreSQL 15
sudo apt-get install -y postgresql-15 postgresql-contrib-15
```

##### Redis Repository

```bash
# Add Redis repository
curl -fsSL https://packages.redis.io/gpg | sudo gpg --dearmor -o /usr/share/keyrings/redis-archive-keyring.gpg
echo "deb [signed-by=/usr/share/keyrings/redis-archive-keyring.gpg] \
    https://packages.redis.io/deb $(lsb_release -cs) main" | \
    sudo tee /etc/apt/sources.list.d/redis.list

# Install Redis
sudo apt-get update
sudo apt-get install -y redis
```

### Package Dependencies

#### Core Dependencies by Profile

##### Minimal Profile
```bash
sudo apt-get install -y \
    python3.10 \
    python3.10-venv \
    python3.10-dev \
    python3-pip
```

##### Standard Profile
```bash
# Minimal + additional libraries
sudo apt-get install -y \
    libpq-dev \
    libmysqlclient-dev \
    libsqlite3-dev \
    libcurl4-openssl-dev \
    libssl-dev
```

##### Full Profile
```bash
# Standard + databases and tools
sudo apt-get install -y \
    redis-server \
    postgresql-15 \
    postgresql-contrib-15 \
    nodejs \
    npm
```

### Ubuntu Version-Specific Notes

#### Ubuntu 24.04 LTS (Noble Numbat)
- Python 3.12 default
- Enhanced snap confinement
- AppArmor security profiles

```bash
# Python 3.10 may require PPA
sudo add-apt-repository ppa:deadsnakes/ppa -y
sudo apt-get install -y python3.10 python3.10-venv
```

#### Ubuntu 22.04 LTS (Jammy Jellyfish)
- Python 3.10 default (perfect for DevGRU)
- Wayland default display server
- systemd-oomd enabled

```bash
# Optimal version for DevGRU - no additional Python setup needed
python3 --version  # Should be 3.10.x
```

#### Ubuntu 20.04 LTS (Focal Fossa)
- Python 3.8 default
- Requires Python 3.10 installation

```bash
# Install Python 3.10
sudo add-apt-repository ppa:deadsnakes/ppa -y
sudo apt-get update
sudo apt-get install -y python3.10 python3.10-venv python3.10-dev

# Set Python 3.10 as default
sudo update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.10 1
```

### Performance Optimization (Ubuntu/Debian)

#### 1. APT Configuration

```bash
# Create APT optimization config
sudo tee /etc/apt/apt.conf.d/99custom <<EOF
Acquire::http::Timeout "10";
Acquire::ftp::Timeout "10";
APT::Get::Assume-Yes "true";
APT::Install-Recommends "false";
APT::Install-Suggests "false";
EOF

# Enable parallel downloads
echo 'Acquire::Queue-Mode "access";' | sudo tee -a /etc/apt/apt.conf.d/99custom
```

#### 2. Systemd Service Optimization

```bash
# Optimize PostgreSQL
sudo systemctl edit postgresql@15-main <<EOF
[Service]
Nice=-5
IOSchedulingClass=realtime
IOSchedulingPriority=0
EOF

# Optimize Redis
sudo systemctl edit redis-server <<EOF
[Service]
LimitNOFILE=65535
Nice=-5
EOF

# Reload systemd
sudo systemctl daemon-reload
```

#### 3. Kernel Parameters

```bash
# Add to /etc/sysctl.conf
sudo tee -a /etc/sysctl.conf <<EOF
# Network performance
net.core.rmem_max = 16777216
net.core.wmem_max = 16777216
net.ipv4.tcp_rmem = 4096 87380 16777216
net.ipv4.tcp_wmem = 4096 65536 16777216

# File handles
fs.file-max = 2097152
fs.nr_open = 2097152

# Shared memory (for databases)
kernel.shmmax = 17179869184
kernel.shmall = 4194304
EOF

# Apply changes
sudo sysctl -p
```

#### 4. I/O Scheduler Optimization

```bash
# Check current I/O scheduler
cat /sys/block/sda/queue/scheduler

# Set deadline scheduler for SSDs
echo deadline | sudo tee /sys/block/sda/queue/scheduler

# Make permanent
echo 'ACTION=="add|change", KERNEL=="sd[a-z]", ATTR{queue/scheduler}="deadline"' | \
    sudo tee /etc/udev/rules.d/60-ioschedulers.rules
```

### Ubuntu/Debian-Specific Environment Variables

```bash
# Add to ~/.bashrc or ~/.profile

# Python optimization
export PYTHONUNBUFFERED=1
export PIP_DISABLE_PIP_VERSION_CHECK=1

# Compiler optimization
export MAKEFLAGS="-j$(nproc)"
export CFLAGS="-O2 -march=native"
export CXXFLAGS="-O2 -march=native"

# PostgreSQL client
export PGHOST=localhost
export PGUSER=postgres

# Locale settings
export LC_ALL=en_US.UTF-8
export LANG=en_US.UTF-8
```

---

## RHEL/CentOS/Fedora Platform

### Prerequisites

#### 1. EPEL Repository (Enterprise Linux)

EPEL (Extra Packages for Enterprise Linux) is **essential** for RHEL/CentOS systems.

```bash
# RHEL/CentOS 8
sudo dnf install -y epel-release
sudo dnf config-manager --set-enabled powertools

# RHEL/CentOS 9
sudo dnf install -y epel-release
sudo dnf config-manager --set-enabled crb

# Verify EPEL
sudo dnf repolist | grep epel
```

#### 2. Development Tools

```bash
# Install Development Tools group
sudo dnf groupinstall -y "Development Tools"

# Install essential packages
sudo dnf install -y \
    gcc \
    gcc-c++ \
    make \
    git \
    curl \
    wget \
    jq \
    openssl-devel \
    libffi-devel \
    zlib-devel \
    bzip2-devel \
    readline-devel \
    sqlite-devel
```

#### 3. Python 3.10 Installation

```bash
# RHEL/CentOS 8/9
sudo dnf install -y python3.10 python3.10-devel python3.10-pip

# Fedora 35+
sudo dnf install -y python3.10 python3-pip python3-devel

# Verify installation
python3.10 --version
```

#### 4. System Updates

```bash
# Update all packages
sudo dnf update -y

# Clean package cache
sudo dnf clean all

# Rebuild cache
sudo dnf makecache
```

### SELinux Considerations

#### What is SELinux?

Security-Enhanced Linux (SELinux) is a mandatory access control (MAC) system that provides fine-grained security policies.

#### SELinux Modes

| Mode | Description | Use Case |
|------|-------------|----------|
| Enforcing | SELinux policies are enforced | Production environments |
| Permissive | SELinux logs violations but doesn't enforce | Development/Testing |
| Disabled | SELinux is completely disabled | Not recommended |

#### Check SELinux Status

```bash
# Check SELinux status
sestatus

# Check current mode
getenforce

# View SELinux context
ls -Z /path/to/directory
```

#### SELinux Configuration for DevGRU

##### Option 1: Keep SELinux Enabled (Recommended)

```bash
# Allow Python to make network connections
sudo setsebool -P httpd_can_network_connect 1

# Allow database connections
sudo setsebool -P httpd_can_network_connect_db 1

# Allow access to user directories
sudo setsebool -P httpd_enable_homedirs 1

# Set proper context for application directories
sudo semanage fcontext -a -t httpd_sys_content_t "/opt/devgru(/.*)?"
sudo restorecon -Rv /opt/devgru

# Allow custom ports (e.g., 8000)
sudo semanage port -a -t http_port_t -p tcp 8000
```

##### Option 2: Permissive Mode for Development

```bash
# Set to permissive mode (temporary)
sudo setenforce 0

# Make permanent
sudo sed -i 's/^SELINUX=enforcing/SELINUX=permissive/' /etc/selinux/config

# Verify
getenforce  # Should show: Permissive
```

##### Option 3: Disable SELinux (Not Recommended)

```bash
# Only for isolated development environments
sudo sed -i 's/^SELINUX=.*/SELINUX=disabled/' /etc/selinux/config

# Reboot required
sudo reboot
```

#### SELinux Troubleshooting

```bash
# View SELinux denials
sudo ausearch -m avc -ts recent

# Generate SELinux policy from denials
sudo ausearch -m avc -ts recent | audit2allow -M devgru_policy

# Install generated policy
sudo semodule -i devgru_policy.pp

# List loaded policies
sudo semodule -l | grep devgru
```

### RHEL Version-Specific Notes

#### RHEL 9 / CentOS Stream 9
- Python 3.9 default, Python 3.10 available
- SELinux more restrictive
- Uses dnf exclusively (yum is symlink)

```bash
# Enable CodeReady Builder (CRB) repository
sudo dnf config-manager --set-enabled crb

# Install Python 3.10
sudo dnf install -y python3.10 python3.10-devel
```

#### RHEL 8 / CentOS Stream 8
- Python 3.6 default, multiple versions available
- AppStream and PowerTools repositories

```bash
# Enable PowerTools repository
sudo dnf config-manager --set-enabled powertools

# Install Python 3.10 from AppStream
sudo dnf module install -y python310
```

#### Fedora 37+
- Cutting-edge packages
- Python 3.11+ default
- Frequent updates

```bash
# Python 3.10 may not be default
sudo dnf install -y python3.10

# Use alternatives system
sudo alternatives --config python3
```

### Package Management Optimization

#### 1. DNF Configuration

```bash
# Optimize DNF
sudo tee -a /etc/dnf/dnf.conf <<EOF
max_parallel_downloads=10
fastestmirror=True
deltarpm=True
keepcache=True
EOF
```

#### 2. Repository Priorities

```bash
# Install priorities plugin
sudo dnf install -y dnf-plugin-priorities

# Set EPEL priority (lower = higher priority)
echo "priority=10" | sudo tee -a /etc/yum.repos.d/epel.repo
```

#### 3. Systemd Service Management

```bash
# Enable and start PostgreSQL
sudo systemctl enable --now postgresql-15

# Enable and start Redis
sudo systemctl enable --now redis

# Check service status
sudo systemctl status postgresql-15 redis
```

### RHEL-Specific Environment Variables

```bash
# Add to ~/.bashrc or ~/.bash_profile

# Python paths
export PATH="/usr/local/bin:$PATH"
export PYTHONPATH="/usr/local/lib/python3.10/site-packages:$PYTHONPATH"

# Compiler flags
export CFLAGS="-O2 -g -pipe -Wall"
export CXXFLAGS="-O2 -g -pipe -Wall"

# SELinux-aware development
export SELINUX_ENABLED=$(getenforce)

# Database connections
export PGHOST=localhost
export PGPORT=5432
```

### Firewall Configuration

```bash
# Allow HTTP/HTTPS
sudo firewall-cmd --permanent --add-service=http
sudo firewall-cmd --permanent --add-service=https

# Allow custom ports
sudo firewall-cmd --permanent --add-port=8000/tcp
sudo firewall-cmd --permanent --add-port=5432/tcp  # PostgreSQL
sudo firewall-cmd --permanent --add-port=6379/tcp  # Redis

# Reload firewall
sudo firewall-cmd --reload

# Verify rules
sudo firewall-cmd --list-all
```

---

## Windows WSL2 Platform

### Prerequisites

#### 1. Enable WSL2

```powershell
# Run in PowerShell as Administrator

# Enable WSL
dism.exe /online /enable-feature /featurename:Microsoft-Windows-Subsystem-Linux /all /norestart

# Enable Virtual Machine Platform
dism.exe /online /enable-feature /featurename:VirtualMachinePlatform /all /norestart

# Restart Windows
Restart-Computer
```

#### 2. Install WSL2 Kernel Update

```powershell
# Download and install WSL2 kernel update
# https://aka.ms/wsl2kernel

# Set WSL2 as default version
wsl --set-default-version 2

# Verify WSL2
wsl --list --verbose
```

#### 3. Install Ubuntu Distribution

```powershell
# List available distributions
wsl --list --online

# Install Ubuntu 22.04 (recommended)
wsl --install -d Ubuntu-22.04

# Or install from Microsoft Store
# Search for "Ubuntu 22.04 LTS"
```

#### 4. Initial WSL2 Configuration

```bash
# Inside WSL2 Ubuntu terminal

# Update system
sudo apt-get update && sudo apt-get upgrade -y

# Install prerequisites
sudo apt-get install -y \
    build-essential \
    curl \
    git \
    jq \
    python3.10 \
    python3.10-venv \
    python3-pip
```

### WSL2 Setup Optimization

#### 1. Memory and CPU Configuration

Create or edit `.wslconfig` in Windows user directory:

```powershell
# Windows path: C:\Users\<YourUsername>\.wslconfig
```

```ini
[wsl2]
# Memory allocation (50% of total RAM)
memory=8GB

# CPU cores (50% of total cores)
processors=4

# Swap space
swap=4GB
swapFile=C:\\temp\\wsl-swap.vhdx

# Limit memory usage
localhostForwarding=true

# Enable nested virtualization (for Docker)
nestedVirtualization=true

# Kernel command line
kernelCommandLine=vsyscall=emulate
```

Apply changes:
```powershell
# Shutdown WSL to apply changes
wsl --shutdown

# Restart WSL
wsl
```

#### 2. Network Configuration

```bash
# Inside WSL2

# Fix DNS issues
sudo tee /etc/wsl.conf <<EOF
[network]
generateResolvConf = false
EOF

# Set custom DNS
sudo rm /etc/resolv.conf
sudo tee /etc/resolv.conf <<EOF
nameserver 8.8.8.8
nameserver 8.8.4.4
EOF

# Prevent overwrite
sudo chattr +i /etc/resolv.conf
```

#### 3. File System Performance

```bash
# Mount options in /etc/wsl.conf
sudo tee -a /etc/wsl.conf <<EOF
[automount]
enabled = true
options = "metadata,umask=22,fmask=11"
mountFsTab = true

[interop]
enabled = true
appendWindowsPath = true
EOF

# Restart WSL
exit
# In PowerShell: wsl --shutdown
```

### Performance Tips

#### 1. Use Linux Filesystem for Development

**IMPORTANT**: Always work within the Linux filesystem (`/home/user/`), not Windows filesystem (`/mnt/c/`).

```bash
# Good performance (Linux filesystem)
mkdir -p ~/projects/devgru
cd ~/projects/devgru

# Poor performance (Windows filesystem - AVOID)
# cd /mnt/c/Users/YourName/projects/devgru
```

Performance comparison:
- Linux filesystem: **100%** (baseline)
- Windows filesystem via `/mnt/c/`: **5-10%** (20x slower)

#### 2. Enable systemd (WSL 0.67.6+)

```bash
# Edit /etc/wsl.conf
sudo tee -a /etc/wsl.conf <<EOF
[boot]
systemd=true
EOF

# Restart WSL
exit
# In PowerShell: wsl --shutdown

# Verify systemd
ps -p 1 -o comm=
# Output should be: systemd
```

Benefits:
- Proper service management (`systemctl`)
- Better process isolation
- Standard Linux service patterns

#### 3. Docker Desktop Integration

```bash
# Install Docker Desktop for Windows with WSL2 backend
# Download from: https://www.docker.com/products/docker-desktop

# In WSL2, verify Docker
docker --version
docker run hello-world

# Use Docker Compose
docker-compose --version
```

#### 4. VS Code Integration

```bash
# Install VS Code Remote - WSL extension
# In WSL2 terminal:
code .

# This opens VS Code with WSL2 backend
# Provides native Linux development experience
```

### Interoperability Features

#### 1. Windows-Linux File Access

```bash
# Access Windows files from WSL2
cd /mnt/c/Users/YourName/Documents

# Access WSL2 files from Windows Explorer
# \\wsl$\Ubuntu-22.04\home\username\
```

#### 2. Run Windows Commands from WSL2

```bash
# Execute Windows commands
cmd.exe /c dir
powershell.exe -Command "Get-Process"

# Open Windows applications
explorer.exe .
code.exe .
```

#### 3. Environment Variables

```bash
# Access Windows environment variables
echo $USERPROFILE  # May not work
/mnt/c/Windows/System32/cmd.exe /C "echo %USERPROFILE%"

# Set shared environment variables
export WSLENV=USERPROFILE/p:TEMP/p
```

### Known Limitations

#### 1. File System Performance

- **Limitation**: Cross-filesystem operations are slow
- **Impact**: 10-20x slower when accessing Windows files from WSL2
- **Workaround**: Keep development files in Linux filesystem

#### 2. Networking

- **Limitation**: WSL2 uses virtualized network (NAT)
- **Impact**: Localhost ports may not be directly accessible from Windows
- **Workaround**: Use port forwarding or `localhostForwarding=true` in `.wslconfig`

```bash
# Port forwarding (PowerShell as Admin)
netsh interface portproxy add v4tov4 listenport=8000 listenaddress=0.0.0.0 connectport=8000 connectaddress=172.x.x.x
```

#### 3. USB Device Access

- **Limitation**: Limited USB device passthrough
- **Impact**: Direct hardware access not available
- **Workaround**: Use usbipd-win project
  - https://github.com/dorssel/usbipd-win

#### 4. GUI Applications

- **Limitation**: WSL2 requires WSLg for GUI apps (Windows 11+)
- **Impact**: Limited GUI support on Windows 10
- **Workaround**: Use X server (VcXsrv, Xming)

```bash
# Install X server on Windows
# Download VcXsrv: https://sourceforge.net/projects/vcxsrv/

# In WSL2, set DISPLAY
export DISPLAY=$(cat /etc/resolv.conf | grep nameserver | awk '{print $2}'):0

# Test GUI
xclock &
```

#### 5. Systemd Limitations

- **Limitation**: Systemd requires WSL 0.67.6+ and manual enablement
- **Impact**: Service management may not work on older WSL versions
- **Workaround**: Use manual service start scripts

```bash
# Without systemd, start services manually
sudo service postgresql start
sudo service redis-server start
```

#### 6. Memory Management

- **Limitation**: WSL2 VM may consume excessive memory
- **Impact**: Host system slowdown
- **Workaround**: Configure memory limits in `.wslconfig`

```bash
# Reclaim memory (PowerShell as Admin)
wsl --shutdown

# Or drop WSL2 caches
# Inside WSL2:
sudo sh -c "echo 3 > /proc/sys/vm/drop_caches"
```

### WSL2-Specific Environment Variables

```bash
# Add to ~/.bashrc

# Display for GUI apps
export DISPLAY=$(cat /etc/resolv.conf | grep nameserver | awk '{print $2}'):0

# Windows user path
export WINDOWS_USER=$(cmd.exe /c "echo %USERNAME%" 2>/dev/null | tr -d '\r')

# Shared directories
export WINDOWS_HOME="/mnt/c/Users/$WINDOWS_USER"

# Development paths
export DEV_HOME="$HOME/projects"

# WSL-specific Python settings
export PYTHONUNBUFFERED=1
export PIP_DISABLE_PIP_VERSION_CHECK=1
```

### WSL2 Troubleshooting

#### WSL2 Won't Start

```powershell
# Check WSL status
wsl --status

# Update WSL
wsl --update

# Repair installation
wsl --install --repair
```

#### Network Issues

```bash
# Reset network (PowerShell as Admin)
wsl --shutdown
netsh winsock reset
netsh int ip reset all
```

#### Disk Space

```powershell
# Compact WSL2 virtual disk
wsl --shutdown
diskpart
# In diskpart:
# select vdisk file="C:\Users\<user>\AppData\Local\Packages\CanonicalGroupLimited.Ubuntu22.04LTS_...\LocalState\ext4.vhdx"
# compact vdisk
```

---

## Version Compatibility Matrix

### Python Versions

| Python Version | macOS | Ubuntu 20.04 | Ubuntu 22.04 | RHEL 8 | RHEL 9 | WSL2 | DevGRU Status |
|----------------|-------|--------------|--------------|---------|---------|------|---------------|
| 3.8 | ✓ | ✓ (default) | ✓ | ✓ | ✓ | ✓ | Minimum |
| 3.9 | ✓ | ✓ | ✓ | ✓ | ✓ (default) | ✓ | Supported |
| **3.10** | **✓** | **✓** | **✓ (default)** | **✓** | **✓** | **✓** | **Recommended** |
| 3.11 | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | Supported |
| 3.12 | ✓ | ⚠️ | ✓ | ⚠️ | ⚠️ | ✓ | Experimental |

**Legend**: ✓ Fully Supported | ⚠️ Partial Support | ✗ Not Supported

### Database Compatibility

#### PostgreSQL

| Version | macOS | Ubuntu | RHEL | WSL2 | Notes |
|---------|-------|---------|------|------|-------|
| 12 | ✓ | ✓ | ✓ | ✓ | End of Life: Nov 2024 |
| 13 | ✓ | ✓ | ✓ | ✓ | EOL: Nov 2025 |
| 14 | ✓ | ✓ | ✓ | ✓ | Supported |
| **15** | **✓** | **✓** | **✓** | **✓** | **Recommended** |
| 16 | ✓ | ✓ | ✓ | ✓ | Latest |

#### Redis

| Version | macOS | Ubuntu | RHEL | WSL2 | Notes |
|---------|-------|---------|------|------|-------|
| 6.x | ✓ | ✓ | ✓ | ✓ | Legacy |
| **7.0** | **✓** | **✓** | **✓** | **✓** | **Stable** |
| **7.2** | **✓** | **✓** | **✓** | **✓** | **Recommended** |

#### Neo4j

| Version | macOS | Ubuntu | RHEL | WSL2 | Notes |
|---------|-------|---------|------|------|-------|
| 4.x | ✓ | ✓ | ✓ | ✓ | Legacy |
| **5.x** | **✓** | **✓** | **✓** | **⚠️** | **Recommended** (Docker for WSL2) |

### External Tools

#### Docker

| Version | macOS Intel | macOS ARM | Ubuntu | RHEL | WSL2 | Notes |
|---------|-------------|-----------|---------|------|------|-------|
| 20.10.x | ✓ | ✓ | ✓ | ✓ | ✓ | Minimum |
| 23.0.x | ✓ | ✓ | ✓ | ✓ | ✓ | Stable |
| **24.0.x** | **✓** | **✓** | **✓** | **✓** | **✓** | **Recommended** |

#### Node.js

| Version | macOS | Ubuntu | RHEL | WSL2 | DevGRU Status |
|---------|-------|---------|------|------|---------------|
| 16.x LTS | ✓ | ✓ | ✓ | ✓ | Minimum |
| **18.x LTS** | **✓** | **✓** | **✓** | **✓** | **Recommended** |
| 20.x LTS | ✓ | ✓ | ✓ | ✓ | Supported |

#### Terraform

| Version | macOS | Ubuntu | RHEL | WSL2 | Notes |
|---------|-------|---------|------|------|-------|
| 1.4.x | ✓ | ✓ | ✓ | ✓ | Stable |
| 1.5.x | ✓ | ✓ | ✓ | ✓ | Stable |
| **1.6.x** | **✓** | **✓** | **✓** | **✓** | **Recommended** |

### Cloud SDK Compatibility

#### AWS CLI

| Version | macOS | Ubuntu | RHEL | WSL2 | Features |
|---------|-------|---------|------|------|----------|
| 1.x | ✓ | ✓ | ✓ | ✓ | Legacy Python |
| **2.x** | **✓** | **✓** | **✓** | **✓** | **Standalone binary** |

#### Azure CLI

| Version | macOS | Ubuntu | RHEL | WSL2 | Installation |
|---------|-------|---------|------|------|--------------|
| **2.x** | **✓** | **✓** | **✓** | **✓** | **apt/yum/brew** |

#### Google Cloud SDK

| Version | macOS | Ubuntu | RHEL | WSL2 | Installation |
|---------|-------|---------|------|------|--------------|
| **Latest** | **✓** | **✓** | **✓** | **✓** | **Manual/Script** |

### Python Package Compatibility

Critical packages across platforms:

| Package | Version | macOS Intel | macOS ARM | Ubuntu | RHEL | WSL2 | Notes |
|---------|---------|-------------|-----------|---------|------|------|-------|
| pandas | 2.0+ | ✓ | ✓ | ✓ | ✓ | ✓ | Core |
| numpy | 1.24+ | ✓ | ⚠️ | ✓ | ✓ | ✓ | ARM: use Homebrew |
| scipy | 1.10+ | ✓ | ⚠️ | ✓ | ✓ | ✓ | ARM: use Homebrew |
| tensorflow | 2.15+ | ✓ | ⚠️ | ✓ | ✓ | ✓ | ARM: use tensorflow-macos |
| pytorch | 2.1+ | ✓ | ✓ | ✓ | ✓ | ✓ | Full support |
| langchain | 0.1+ | ✓ | ✓ | ✓ | ✓ | ✓ | Full support |
| fastapi | 0.104+ | ✓ | ✓ | ✓ | ✓ | ✓ | Full support |

---

## Performance Optimization

### General Performance Tips

#### 1. Use Package Managers Efficiently

```bash
# macOS - Homebrew
brew bundle install  # Install from Brewfile
brew cleanup -s      # Clean up old versions

# Ubuntu/Debian
sudo apt-get autoremove -y  # Remove unused packages
sudo apt-get autoclean      # Clean package cache

# RHEL/Fedora
sudo dnf autoremove -y      # Remove unused packages
sudo dnf clean all          # Clean package cache
```

#### 2. Optimize Python Package Installation

```bash
# Use binary wheels (faster than source builds)
pip install --prefer-binary package_name

# Install from local cache
pip install --no-index --find-links=/path/to/cache package_name

# Parallel installations (pip 21.0+)
pip install --use-feature=fast-deps package_name

# Compile with optimizations
CFLAGS="-O3 -march=native" pip install package_name
```

#### 3. Virtual Environment Best Practices

```bash
# Use venv (built-in, fastest)
python3 -m venv venv

# Or use virtualenv (more features)
virtualenv venv

# Or use conda (heavy, for data science)
conda create -n devgru python=3.10

# Activate and install requirements
source venv/bin/activate
pip install -r requirements.txt
```

#### 4. Database Performance Tuning

##### PostgreSQL

```bash
# Edit postgresql.conf
sudo nano $(pg_config --sysconfdir)/postgresql.conf

# Key settings for development:
shared_buffers = 256MB
effective_cache_size = 1GB
maintenance_work_mem = 128MB
wal_buffers = 16MB
min_wal_size = 1GB
max_wal_size = 4GB
```

##### Redis

```bash
# Edit redis.conf
sudo nano /etc/redis/redis.conf

# Key settings:
maxmemory 512mb
maxmemory-policy allkeys-lru
save ""  # Disable persistence for dev
appendonly no
```

### Platform-Specific Optimization

#### macOS Optimization

```bash
# Disable Spotlight indexing for dev directories
sudo mdutil -i off ~/Development

# Disable Time Machine for dev directories
tmutil addexclusion ~/Development/node_modules
tmutil addexclusion ~/Development/.venv

# Use RAM disk for temporary files
diskutil erasevolume HFS+ "RAMDisk" `hdiutil attach -nomount ram://4194304`
export TMPDIR=/Volumes/RAMDisk
```

#### Linux Optimization

```bash
# Increase file watchers (for development tools)
echo fs.inotify.max_user_watches=524288 | sudo tee -a /etc/sysctl.conf
sudo sysctl -p

# Optimize swap usage
echo vm.swappiness=10 | sudo tee -a /etc/sysctl.conf
sudo sysctl -p

# Enable transparent huge pages
echo always | sudo tee /sys/kernel/mm/transparent_hugepage/enabled
```

#### WSL2 Optimization

```bash
# Compact WSL2 disk (Windows PowerShell as Admin)
wsl --shutdown
Optimize-VHD -Path "C:\Users\<user>\AppData\Local\Packages\...\ext4.vhdx" -Mode Full

# Inside WSL2: Limit memory usage
sudo sh -c "echo 3 > /proc/sys/vm/drop_caches"
```

### Monitoring and Profiling

#### System Resource Monitoring

```bash
# macOS
top -o cpu          # CPU usage
fs_usage -f network # Network I/O
iotop              # Disk I/O

# Linux
htop               # Interactive process viewer
iotop              # Disk I/O
nethogs            # Network usage per process

# All platforms
python3 -m py_spy top -- python script.py  # Python profiling
```

#### Database Monitoring

```bash
# PostgreSQL
psql -c "SELECT * FROM pg_stat_activity;"

# Redis
redis-cli INFO stats
redis-cli --latency
```

---

## Known Limitations

### Platform-Specific Limitations

#### macOS Limitations

1. **Case-Insensitive Filesystem (Default)**
   - Impact: `File.txt` and `file.txt` are the same file
   - Workaround: Format disk as APFS (Case-sensitive) or use case-sensitive disk images

2. **SIP Restrictions**
   - Impact: Cannot modify system directories even with sudo
   - Workaround: Use user-space installations (Homebrew, pip --user)

3. **Apple Silicon Compatibility**
   - Impact: Some x86_64 packages may not have ARM builds
   - Workaround: Use Rosetta 2 or wait for native builds

4. **Gatekeeper Security**
   - Impact: Unsigned binaries may be blocked
   - Workaround: `xattr -d com.apple.quarantine file` or System Preferences > Security

#### Ubuntu/Debian Limitations

1. **Snap Package Confinement**
   - Impact: Snap packages may not access all system resources
   - Workaround: Use traditional apt packages instead of snap

2. **AppArmor Restrictions**
   - Impact: Security profiles may block legitimate operations
   - Workaround: Adjust AppArmor profiles or disable for specific applications

3. **PPA Dependencies**
   - Impact: PPAs may conflict with official repositories
   - Workaround: Use apt pinning to manage priorities

4. **LTS Kernel Limitations**
   - Impact: Older kernels may not support latest hardware features
   - Workaround: Install HWE (Hardware Enablement) kernel

```bash
sudo apt-get install --install-recommends linux-generic-hwe-22.04
```

#### RHEL/CentOS Limitations

1. **Package Availability**
   - Impact: Fewer packages in default repositories compared to Ubuntu
   - Workaround: Enable EPEL and additional repositories

2. **SELinux Enforcement**
   - Impact: Legitimate operations may be blocked by SELinux policies
   - Workaround: Create custom SELinux policies or use permissive mode for dev

3. **Subscription Requirements (RHEL)**
   - Impact: Access to repositories requires Red Hat subscription
   - Workaround: Use CentOS Stream or Rocky Linux

4. **Older Default Packages**
   - Impact: Stable but older package versions
   - Workaround: Use Software Collections (SCL) or build from source

#### WSL2 Limitations

1. **File System Performance**
   - Impact: 10-20x slower when accessing Windows files
   - Workaround: Keep all development files in Linux filesystem

2. **Networking NAT Mode**
   - Impact: Complex port forwarding, localhost issues
   - Workaround: Use `localhostForwarding=true` in `.wslconfig`

3. **No Direct USB Access**
   - Impact: Cannot access USB devices directly
   - Workaround: Use usbipd-win for USB passthrough

4. **Limited GUI Support**
   - Impact: GUI applications require WSLg (Windows 11) or X server
   - Workaround: Install VcXsrv or upgrade to Windows 11

5. **Systemd Requirement**
   - Impact: Systemd not enabled by default
   - Workaround: Manually enable in `/etc/wsl.conf` (WSL 0.67.6+)

6. **Memory Overconsumption**
   - Impact: WSL2 VM may use excessive memory
   - Workaround: Configure limits in `.wslconfig`

### Package-Specific Limitations

#### TensorFlow/PyTorch on Apple Silicon

- **Limitation**: Standard TensorFlow doesn't use Metal acceleration
- **Workaround**: Use `tensorflow-macos` and `tensorflow-metal`

```bash
pip install tensorflow-macos tensorflow-metal
```

#### Neo4j on WSL2

- **Limitation**: Native installation may have issues
- **Workaround**: Use Docker

```bash
docker run -d \
  --name neo4j \
  -p 7474:7474 -p 7687:7687 \
  -e NEO4J_AUTH=neo4j/password \
  neo4j:5.15
```

#### Docker on macOS

- **Limitation**: Uses virtualization (slower than Linux)
- **Workaround**: Use VirtioFS for better file sharing performance

#### Playwright on RHEL/CentOS

- **Limitation**: Missing system dependencies
- **Workaround**: Install additional libraries

```bash
sudo dnf install -y \
  alsa-lib \
  at-spi2-atk \
  cups-libs \
  libdrm \
  libxkbcommon \
  mesa-libgbm
```

---

## Troubleshooting by Platform

### macOS Troubleshooting

#### Issue: Homebrew Permission Errors

```bash
# Fix Homebrew permissions
sudo chown -R $(whoami) $(brew --prefix)/*

# Reset Homebrew
cd $(brew --prefix)
git fetch origin
git reset --hard origin/master
```

#### Issue: Python Certificate Errors

```bash
# Install certificates
/Applications/Python\ 3.10/Install\ Certificates.command

# Or manually
pip install --upgrade certifi
```

#### Issue: Command Line Tools Missing

```bash
# Reinstall Command Line Tools
sudo rm -rf /Library/Developer/CommandLineTools
xcode-select --install
```

### Ubuntu/Debian Troubleshooting

#### Issue: Package Conflicts

```bash
# Fix broken packages
sudo apt-get install -f

# Reconfigure packages
sudo dpkg --configure -a

# Clean and update
sudo apt-get clean
sudo apt-get update
sudo apt-get upgrade -y
```

#### Issue: Python pip Not Found

```bash
# Install pip for Python 3.10
sudo apt-get install -y python3.10-distutils
curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py
python3.10 get-pip.py
```

#### Issue: Database Connection Refused

```bash
# Check PostgreSQL status
sudo systemctl status postgresql

# Start if stopped
sudo systemctl start postgresql

# Enable on boot
sudo systemctl enable postgresql

# Check listening ports
sudo netstat -tulpn | grep postgres
```

### RHEL/CentOS Troubleshooting

#### Issue: EPEL Repository Not Found

```bash
# RHEL 8
sudo dnf install -y https://dl.fedoraproject.org/pub/epel/epel-release-latest-8.noarch.rpm

# RHEL 9
sudo dnf install -y https://dl.fedoraproject.org/pub/epel/epel-release-latest-9.noarch.rpm
```

#### Issue: SELinux Denials

```bash
# Check for denials
sudo ausearch -m avc -ts recent

# Generate policy
sudo ausearch -m avc -ts recent | audit2allow -M mypolicy

# Install policy
sudo semodule -i mypolicy.pp
```

#### Issue: Firewall Blocking Connections

```bash
# Check firewall status
sudo firewall-cmd --state

# List rules
sudo firewall-cmd --list-all

# Add port
sudo firewall-cmd --permanent --add-port=8000/tcp
sudo firewall-cmd --reload
```

### WSL2 Troubleshooting

#### Issue: WSL2 Not Starting

```powershell
# Update WSL (PowerShell as Admin)
wsl --update

# Shutdown and restart
wsl --shutdown
wsl

# Check status
wsl --status
```

#### Issue: Network Not Working

```bash
# Inside WSL2
sudo rm /etc/resolv.conf
echo "nameserver 8.8.8.8" | sudo tee /etc/resolv.conf
sudo chattr +i /etc/resolv.conf
```

#### Issue: Disk Space Full

```powershell
# Compact disk (PowerShell as Admin)
wsl --shutdown

# Use diskpart
diskpart
# In diskpart:
select vdisk file="C:\Users\<user>\AppData\Local\Packages\...\ext4.vhdx"
compact vdisk
exit
```

#### Issue: Slow Performance

```bash
# Ensure using Linux filesystem
pwd
# Should be /home/user/..., NOT /mnt/c/...

# If in Windows filesystem, move files
mv /mnt/c/projects ~/projects
cd ~/projects
```

---

## Additional Resources

### Official Documentation

- **macOS**: https://developer.apple.com/documentation
- **Ubuntu**: https://help.ubuntu.com/
- **RHEL**: https://access.redhat.com/documentation
- **WSL2**: https://docs.microsoft.com/en-us/windows/wsl/

### Package Managers

- **Homebrew**: https://brew.sh/
- **APT**: https://wiki.debian.org/Apt
- **DNF/YUM**: https://docs.fedoraproject.org/en-US/quick-docs/dnf/

### Python Resources

- **Python.org**: https://www.python.org/
- **PyPI**: https://pypi.org/
- **pip Documentation**: https://pip.pypa.io/

### Database Documentation

- **PostgreSQL**: https://www.postgresql.org/docs/
- **Redis**: https://redis.io/documentation
- **Neo4j**: https://neo4j.com/docs/

### Cloud SDKs

- **AWS CLI**: https://docs.aws.amazon.com/cli/
- **Azure CLI**: https://docs.microsoft.com/en-us/cli/azure/
- **Google Cloud SDK**: https://cloud.google.com/sdk/docs

---

## Support and Contribution

For platform-specific issues or contributions:

1. **GitHub Issues**: https://github.com/devCrew_s1/issues
2. **Documentation**: https://github.com/devCrew_s1/docs
3. **Community Discussions**: https://github.com/devCrew_s1/discussions

When reporting platform-specific issues, include:
- OS version (`sw_vers`, `lsb_release -a`, `cat /etc/os-release`)
- Architecture (`uname -m`)
- Python version (`python3 --version`)
- Installation logs from `devgru_setup/logs/`

---

**Last Updated**: 2025-11-20
**Version**: 1.0.0
**Maintainer**: devCrew_s1
