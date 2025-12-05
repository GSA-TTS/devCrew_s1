#!/bin/bash
###############################################################################
# Core Python Packages Installation Module
#
# Purpose: Install core Python packages required for devCrew_s1 project
# Packages: pandas, requests, pydantic, celery, playwright
#
# Part of: GitHub Issue #67 - Multi-OS Prerequisites Setup Script
# Created: 2025-11-20
###############################################################################

set -e  # Exit on error
set -u  # Exit on undefined variable

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Script directory and project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"

###############################################################################
# Logging Functions
###############################################################################

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

###############################################################################
# Virtual Environment Management
###############################################################################

activate_venv() {
    log_info "Checking for virtual environment..."

    # Check common venv locations
    local venv_paths=(
        "${PROJECT_ROOT}/venv"
        "${PROJECT_ROOT}/.venv"
        "${HOME}/.virtualenvs/devCrew_s1"
    )

    for venv_path in "${venv_paths[@]}"; do
        if [ -d "$venv_path" ]; then
            log_info "Found virtual environment at: $venv_path"

            # Activate based on OS
            if [ -f "$venv_path/bin/activate" ]; then
                # shellcheck disable=SC1091
                source "$venv_path/bin/activate"
                log_success "Virtual environment activated"
                return 0
            elif [ -f "$venv_path/Scripts/activate" ]; then
                # Windows path
                # shellcheck disable=SC1091
                source "$venv_path/Scripts/activate"
                log_success "Virtual environment activated"
                return 0
            fi
        fi
    done

    log_warning "No virtual environment found. Creating one at ${PROJECT_ROOT}/venv"
    python3 -m venv "${PROJECT_ROOT}/venv"
    # shellcheck disable=SC1091
    source "${PROJECT_ROOT}/venv/bin/activate"
    log_success "Virtual environment created and activated"
}

###############################################################################
# Package Installation Functions
###############################################################################

check_pip() {
    log_info "Checking pip installation..."

    if ! command -v pip &> /dev/null; then
        log_error "pip not found. Please install pip first."
        exit 1
    fi

    # Upgrade pip to latest version
    log_info "Upgrading pip to latest version..."
    pip install --upgrade pip
    log_success "pip is ready"
}

install_core_packages() {
    log_info "Installing core Python packages..."

    # Core packages with version constraints from prerequisites_validated.json
    local packages=(
        "pandas>=2.0"
        "requests>=2.31"
        "pydantic>=2.5"
        "celery>=5.3.4"
        "playwright>=1.40"
    )

    local failed_packages=()

    for package in "${packages[@]}"; do
        log_info "Installing ${package}..."

        if pip install "${package}"; then
            log_success "${package} installed successfully"
        else
            log_error "Failed to install ${package}"
            failed_packages+=("${package}")
        fi
    done

    # Check for installation failures
    if [ ${#failed_packages[@]} -ne 0 ]; then
        log_error "The following packages failed to install:"
        for pkg in "${failed_packages[@]}"; do
            echo "  - $pkg"
        done
        return 1
    fi

    log_success "All core packages installed successfully"
}

install_playwright_browsers() {
    log_info "Installing Playwright Chromium browser..."

    if playwright install chromium; then
        log_success "Playwright Chromium browser installed successfully"
    else
        log_error "Failed to install Playwright browser"
        log_warning "You may need to run 'playwright install chromium' manually"
        return 1
    fi
}

###############################################################################
# Verification Functions
###############################################################################

verify_package_installation() {
    local package_name=$1
    local import_name=${2:-$package_name}

    if python3 -c "import ${import_name}" 2>/dev/null; then
        return 0
    else
        return 1
    fi
}

verify_all_packages() {
    log_info "Verifying package installations..."

    local packages=(
        "pandas:pandas"
        "requests:requests"
        "pydantic:pydantic"
        "celery:celery"
        "playwright:playwright"
    )

    local verification_failed=false

    for package_info in "${packages[@]}"; do
        IFS=':' read -r package_name import_name <<< "$package_info"

        log_info "Verifying ${package_name}..."

        if verify_package_installation "$package_name" "$import_name"; then
            # Get installed version
            local version=$(pip show "$package_name" | grep "Version:" | cut -d' ' -f2)
            log_success "${package_name} ${version} is installed and importable"
        else
            log_error "${package_name} verification failed"
            verification_failed=true
        fi
    done

    if [ "$verification_failed" = true ]; then
        log_error "Package verification failed"
        return 1
    fi

    log_success "All packages verified successfully"
}

verify_playwright_installation() {
    log_info "Verifying Playwright browser installation..."

    # Check if playwright browsers are installed
    if playwright install --dry-run chromium 2>&1 | grep -q "is already installed"; then
        log_success "Playwright Chromium browser is installed"
        return 0
    elif [ -d "$HOME/.cache/ms-playwright" ] || [ -d "$HOME/Library/Caches/ms-playwright" ]; then
        log_success "Playwright browser cache found"
        return 0
    else
        log_warning "Playwright browser installation could not be verified"
        return 1
    fi
}

###############################################################################
# Error Handling
###############################################################################

handle_error() {
    local exit_code=$?
    log_error "Installation failed with exit code: $exit_code"
    log_info "Please check the error messages above for details"
    exit "$exit_code"
}

trap handle_error ERR

###############################################################################
# Main Execution
###############################################################################

main() {
    log_info "=== Core Python Packages Installation ==="
    log_info "Project Root: ${PROJECT_ROOT}"
    log_info "Started at: $(date)"
    echo ""

    # Step 1: Activate virtual environment
    activate_venv
    echo ""

    # Step 2: Check and upgrade pip
    check_pip
    echo ""

    # Step 3: Install core packages
    install_core_packages
    echo ""

    # Step 4: Install Playwright browsers
    install_playwright_browsers
    echo ""

    # Step 5: Verify installations
    verify_all_packages
    echo ""

    # Step 6: Verify Playwright
    verify_playwright_installation
    echo ""

    log_success "=== Core packages installation completed successfully ==="
    log_info "Completed at: $(date)"

    # Display installed package versions
    echo ""
    log_info "Installed package versions:"
    pip list | grep -E "pandas|requests|pydantic|celery|playwright" || true
}

# Run main function if script is executed directly
if [ "${BASH_SOURCE[0]}" -eq "${0}" ]; then
    main "$@"
fi
