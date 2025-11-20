#!/usr/bin/env bash
#
# Python Setup Module for DevGru Multi-OS Prerequisites
# Supports: macOS, Ubuntu/Debian, RHEL/CentOS, Windows WSL2
#
# This script installs Python 3.10+ and sets up a virtual environment
# Should be sourced by the main setup script
#

set -euo pipefail

# Color codes for output
readonly RED='\033[0;31m'
readonly GREEN='\033[0;32m'
readonly YELLOW='\033[1;33m'
readonly BLUE='\033[0;34m'
readonly NC='\033[0m' # No Color

# Python version requirements
readonly MIN_PYTHON_VERSION="3.10"
readonly VENV_PATH="${HOME}/.devgru_venv"

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $*"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $*"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $*"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $*" >&2
}

# Detect operating system
detect_os() {
    if [[ "$OSTYPE" == "darwin"* ]]; then
        echo "macos"
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        if grep -qi "microsoft" /proc/version 2>/dev/null; then
            echo "wsl2"
        elif [ -f /etc/os-release ]; then
            . /etc/os-release
            case "$ID" in
                ubuntu|debian)
                    echo "debian"
                    ;;
                rhel|centos|fedora|rocky|almalinux)
                    echo "rhel"
                    ;;
                *)
                    echo "unknown"
                    ;;
            esac
        else
            echo "unknown"
        fi
    else
        echo "unknown"
    fi
}

# Check if Python version meets minimum requirements
check_python_version() {
    local python_cmd=$1

    if ! command -v "$python_cmd" &> /dev/null; then
        return 1
    fi

    local version
    version=$($python_cmd --version 2>&1 | sed -n 's/^Python \([0-9]*\.[0-9]*\).*/\1/p')

    if [ -z "$version" ]; then
        return 1
    fi

    # Compare versions using sort -V
    if printf '%s\n%s\n' "$MIN_PYTHON_VERSION" "$version" | sort -V -C; then
        echo "$version"
        return 0
    else
        return 1
    fi
}

# Install Python on macOS using Homebrew
install_python_macos() {
    log_info "Installing Python on macOS using Homebrew..."

    # Check if Homebrew is installed
    if ! command -v brew &> /dev/null; then
        log_error "Homebrew is not installed. Please install Homebrew first:"
        log_error "  /bin/bash -c \"\$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\""
        return 1
    fi

    # Update Homebrew
    log_info "Updating Homebrew..."
    if ! brew update; then
        log_warning "Failed to update Homebrew, continuing anyway..."
    fi

    # Install Python
    log_info "Installing Python 3..."
    if brew install python@3.11; then
        log_success "Python installed successfully via Homebrew"

        # Link Python if needed
        brew link --overwrite python@3.11 2>/dev/null || true

        return 0
    else
        log_error "Failed to install Python via Homebrew"
        return 1
    fi
}

# Install Python on Debian/Ubuntu
install_python_debian() {
    log_info "Installing Python on Debian/Ubuntu using apt..."

    # Update package list
    log_info "Updating package list..."
    if ! sudo apt-get update; then
        log_error "Failed to update package list"
        return 1
    fi

    # Install Python and required packages
    log_info "Installing Python 3.11 and dependencies..."
    if sudo apt-get install -y \
        python3.11 \
        python3.11-venv \
        python3.11-dev \
        python3-pip \
        build-essential \
        libssl-dev \
        libffi-dev; then

        log_success "Python installed successfully via apt"

        # Create symlinks if python3 doesn't exist or is older
        if ! command -v python3 &> /dev/null || ! check_python_version python3 &> /dev/null; then
            sudo update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.11 1 2>/dev/null || true
        fi

        return 0
    else
        log_error "Failed to install Python via apt"
        return 1
    fi
}

# Install Python on RHEL/CentOS
install_python_rhel() {
    log_info "Installing Python on RHEL/CentOS using dnf..."

    # Determine package manager (dnf or yum)
    local pkg_manager="dnf"
    if ! command -v dnf &> /dev/null; then
        pkg_manager="yum"
    fi

    log_info "Using package manager: $pkg_manager"

    # Install EPEL repository if not available
    if ! sudo $pkg_manager repolist | grep -q epel; then
        log_info "Installing EPEL repository..."
        sudo $pkg_manager install -y epel-release || true
    fi

    # Install Python
    log_info "Installing Python 3.11 and dependencies..."
    if sudo $pkg_manager install -y \
        python3.11 \
        python3.11-devel \
        python3-pip \
        gcc \
        gcc-c++ \
        make \
        openssl-devel \
        libffi-devel; then

        log_success "Python installed successfully via $pkg_manager"

        # Create symlinks if python3 doesn't exist or is older
        if ! command -v python3 &> /dev/null || ! check_python_version python3 &> /dev/null; then
            sudo alternatives --install /usr/bin/python3 python3 /usr/bin/python3.11 1 2>/dev/null || true
        fi

        return 0
    else
        log_error "Failed to install Python via $pkg_manager"
        return 1
    fi
}

# Install Python on WSL2 (uses Debian method)
install_python_wsl2() {
    log_info "Installing Python on Windows WSL2..."
    log_info "WSL2 detected - using Debian/Ubuntu installation method"
    install_python_debian
}

# Main Python installation function
install_python() {
    local os_type
    os_type=$(detect_os)

    log_info "Detected operating system: $os_type"

    case "$os_type" in
        macos)
            install_python_macos
            ;;
        debian)
            install_python_debian
            ;;
        rhel)
            install_python_rhel
            ;;
        wsl2)
            install_python_wsl2
            ;;
        *)
            log_error "Unsupported operating system: $os_type"
            return 1
            ;;
    esac
}

# Verify Python installation
verify_python_installation() {
    log_info "Verifying Python installation..."

    # Try different Python commands
    local python_cmd=""
    for cmd in python3.11 python3 python; do
        if command -v "$cmd" &> /dev/null; then
            python_cmd="$cmd"
            break
        fi
    done

    if [ -z "$python_cmd" ]; then
        log_error "Python command not found after installation"
        return 1
    fi

    # Check version
    local version
    if version=$(check_python_version "$python_cmd"); then
        log_success "Python $version is installed and meets minimum requirements (>= $MIN_PYTHON_VERSION)"
        export PYTHON_CMD="$python_cmd"
        return 0
    else
        log_error "Python version does not meet minimum requirements (>= $MIN_PYTHON_VERSION)"
        log_error "Found: $($python_cmd --version 2>&1)"
        return 1
    fi
}

# Set up virtual environment
setup_virtual_environment() {
    log_info "Setting up virtual environment at $VENV_PATH..."

    # Remove existing venv if it exists and is corrupted
    if [ -d "$VENV_PATH" ]; then
        if [ ! -f "$VENV_PATH/bin/activate" ] && [ ! -f "$VENV_PATH/Scripts/activate" ]; then
            log_warning "Removing corrupted virtual environment..."
            rm -rf "$VENV_PATH"
        else
            log_info "Virtual environment already exists at $VENV_PATH"
            log_info "To recreate it, delete the directory and run this script again"
            return 0
        fi
    fi

    # Create virtual environment
    if ! "$PYTHON_CMD" -m venv "$VENV_PATH"; then
        log_error "Failed to create virtual environment"
        return 1
    fi

    log_success "Virtual environment created at $VENV_PATH"

    # Activate virtual environment
    if [ -f "$VENV_PATH/bin/activate" ]; then
        # shellcheck disable=SC1091
        source "$VENV_PATH/bin/activate"
    elif [ -f "$VENV_PATH/Scripts/activate" ]; then
        # shellcheck disable=SC1091
        source "$VENV_PATH/Scripts/activate"
    else
        log_error "Virtual environment activation script not found"
        return 1
    fi

    log_success "Virtual environment activated"

    return 0
}

# Upgrade pip and essential packages
upgrade_pip_packages() {
    log_info "Upgrading pip, setuptools, and wheel..."

    # Ensure we're using the virtual environment's pip
    local pip_cmd
    if [ -n "${VIRTUAL_ENV:-}" ]; then
        pip_cmd="$VIRTUAL_ENV/bin/pip"
    else
        log_error "Virtual environment not activated"
        return 1
    fi

    # Upgrade pip
    if ! "$pip_cmd" install --upgrade pip; then
        log_error "Failed to upgrade pip"
        return 1
    fi

    # Upgrade setuptools and wheel
    if ! "$pip_cmd" install --upgrade setuptools wheel; then
        log_error "Failed to upgrade setuptools and wheel"
        return 1
    fi

    log_success "Successfully upgraded pip, setuptools, and wheel"

    # Display versions
    log_info "Installed versions:"
    "$pip_cmd" --version
    "$pip_cmd" show setuptools | grep Version || true
    "$pip_cmd" show wheel | grep Version || true

    return 0
}

# Main function to orchestrate Python setup
setup_python() {
    log_info "=== Python Setup Module ==="
    log_info "Minimum Python version required: $MIN_PYTHON_VERSION"

    # Check if Python is already installed and meets requirements
    local python_installed=false
    for cmd in python3.11 python3 python; do
        if check_python_version "$cmd" &> /dev/null; then
            local version
            version=$(check_python_version "$cmd")
            log_success "Python $version is already installed and meets requirements"
            export PYTHON_CMD="$cmd"
            python_installed=true
            break
        fi
    done

    # Install Python if not already installed
    if [ "$python_installed" = false ]; then
        log_info "Python not found or version too old. Installing..."

        if ! install_python; then
            log_error "Python installation failed"
            return 1
        fi

        if ! verify_python_installation; then
            log_error "Python installation verification failed"
            return 1
        fi
    fi

    # Set up virtual environment
    if ! setup_virtual_environment; then
        log_error "Virtual environment setup failed"
        return 1
    fi

    # Upgrade pip and packages
    if ! upgrade_pip_packages; then
        log_error "Failed to upgrade pip packages"
        return 1
    fi

    log_success "=== Python setup completed successfully ==="
    log_info "Python command: $PYTHON_CMD"
    log_info "Virtual environment: $VENV_PATH"
    log_info ""
    log_info "To activate the virtual environment manually, run:"
    log_info "  source $VENV_PATH/bin/activate"

    return 0
}

# Run the main setup if script is executed directly (not sourced)
if [ "${BASH_SOURCE[0]:-}" = "${0}" ]; then
    setup_python
fi
