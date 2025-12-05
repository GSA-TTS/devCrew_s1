#!/usr/bin/env bash
###############################################################################
# DevGRU Multi-OS Prerequisites Setup Script
#
# Purpose: Automated setup script for DevGRU development environment
# Author: devCrew_s1
# Created: 2025-11-20
# Issue: GitHub Issue #67
#
# Supports:
#   - macOS (Intel and Apple Silicon)
#   - Ubuntu/Debian Linux
#   - RHEL/CentOS/Fedora
#   - Windows WSL2 (Ubuntu)
#
# Profiles:
#   - minimal: Python 3.10+ + 5 core packages
#   - standard: minimal + 15 optional packages (default)
#   - full: standard + databases + external tools
#   - security: standard + security tools
#   - cloud-aws: standard + AWS SDK
#   - cloud-azure: standard + Azure SDK
#   - cloud-gcp: standard + GCP SDK
#
# Usage: ./setup_devgru.sh [OPTIONS]
#   Options:
#     --profile PROFILE     Installation profile (default: standard)
#     --dry-run            Show what would be installed without installing
#     --verbose            Enable verbose output
#     --skip-databases     Skip database installations
#     --skip-tools         Skip external tools installation
#     --help               Show this help message
#
###############################################################################

# Strict error handling
set -euo pipefail

###############################################################################
# Global Variables
###############################################################################

# Script metadata
readonly SCRIPT_VERSION="1.0.0"
readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly WORK_DIR="/tmp/issue67_work"
readonly PREREQS_FILE="${WORK_DIR}/prerequisites_validated.json"

# Logging configuration
readonly LOG_DIR="${SCRIPT_DIR}/logs"
readonly LOG_FILE="${LOG_DIR}/setup_$(date +%Y%m%d_%H%M%S).log"

# Installation state tracking
readonly STATE_DIR="${SCRIPT_DIR}/.state"
readonly STATE_FILE="${STATE_DIR}/installation_state.json"

# Color codes for output
readonly COLOR_RESET='\033[0m'
readonly COLOR_RED='\033[0;31m'
readonly COLOR_GREEN='\033[0;32m'
readonly COLOR_YELLOW='\033[0;33m'
readonly COLOR_BLUE='\033[0;34m'
readonly COLOR_MAGENTA='\033[0;35m'
readonly COLOR_CYAN='\033[0;36m'

# Default configuration
PROFILE="standard"
DRY_RUN=false
VERBOSE=false
SKIP_DATABASES=false
SKIP_TOOLS=false

# System detection results
OS_TYPE=""
OS_VERSION=""
ARCH=""
PACKAGE_MANAGER=""

# Installation tracking
declare -a INSTALLED_PACKAGES=()
declare -a FAILED_PACKAGES=()
declare -a ROLLBACK_COMMANDS=()

###############################################################################
# Utility Functions
###############################################################################

# Print colored messages
log_info() {
    # Ensure log directory exists
    mkdir -p "${LOG_DIR}" 2>/dev/null || true
    echo -e "${COLOR_BLUE}[INFO]${COLOR_RESET} $*" | tee -a "${LOG_FILE}"
}

log_success() {
    mkdir -p "${LOG_DIR}" 2>/dev/null || true
    echo -e "${COLOR_GREEN}[SUCCESS]${COLOR_RESET} $*" | tee -a "${LOG_FILE}"
}

log_warning() {
    mkdir -p "${LOG_DIR}" 2>/dev/null || true
    echo -e "${COLOR_YELLOW}[WARNING]${COLOR_RESET} $*" | tee -a "${LOG_FILE}"
}

log_error() {
    mkdir -p "${LOG_DIR}" 2>/dev/null || true
    echo -e "${COLOR_RED}[ERROR]${COLOR_RESET} $*" | tee -a "${LOG_FILE}"
}

log_debug() {
    if [[ "${VERBOSE}" == true ]]; then
        mkdir -p "${LOG_DIR}" 2>/dev/null || true
        echo -e "${COLOR_MAGENTA}[DEBUG]${COLOR_RESET} $*" | tee -a "${LOG_FILE}"
    fi
}

log_section() {
    mkdir -p "${LOG_DIR}" 2>/dev/null || true
    echo "" | tee -a "${LOG_FILE}"
    echo -e "${COLOR_CYAN}========================================${COLOR_RESET}" | tee -a "${LOG_FILE}"
    echo -e "${COLOR_CYAN}$*${COLOR_RESET}" | tee -a "${LOG_FILE}"
    echo -e "${COLOR_CYAN}========================================${COLOR_RESET}" | tee -a "${LOG_FILE}"
}

# Execute command with logging
execute_cmd() {
    local cmd="$*"
    log_debug "Executing: ${cmd}"

    if [[ "${DRY_RUN}" == true ]]; then
        log_info "[DRY-RUN] Would execute: ${cmd}"
        return 0
    fi

    if [[ "${VERBOSE}" == true ]]; then
        eval "${cmd}" 2>&1 | tee -a "${LOG_FILE}"
    else
        eval "${cmd}" >> "${LOG_FILE}" 2>&1
    fi
}

# Check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check if running as root
is_root() {
    [[ "${EUID}" -eq 0 ]]
}

# Prompt for confirmation
confirm() {
    local prompt="$1"
    local response

    if [[ "${DRY_RUN}" == true ]]; then
        return 0
    fi

    read -r -p "${prompt} [y/N] " response
    case "${response}" in
        [yY][eE][sS]|[yY])
            return 0
            ;;
        *)
            return 1
            ;;
    esac
}

# Add rollback command
add_rollback() {
    local cmd="$*"
    ROLLBACK_COMMANDS+=("${cmd}")
    log_debug "Added rollback command: ${cmd}"
}

# Execute rollback
execute_rollback() {
    log_warning "Executing rollback procedures..."

    local count="${#ROLLBACK_COMMANDS[@]}"
    if [[ "${count}" -eq 0 ]]; then
        log_info "No rollback commands to execute"
        return 0
    fi

    # Execute rollback commands in reverse order
    for ((i=count-1; i>=0; i--)); do
        local cmd="${ROLLBACK_COMMANDS[i]}"
        log_info "Rollback: ${cmd}"
        eval "${cmd}" >> "${LOG_FILE}" 2>&1 || log_error "Rollback command failed: ${cmd}"
    done

    log_success "Rollback completed"
}

# Save installation state
save_state() {
    mkdir -p "${STATE_DIR}"

    # Create JSON arrays safely
    local installed_json="[]"
    local failed_json="[]"

    if [[ "${#INSTALLED_PACKAGES[@]}" -gt 0 ]]; then
        installed_json=$(printf '%s\n' "${INSTALLED_PACKAGES[@]}" | jq -R . | jq -s .)
    fi

    if [[ "${#FAILED_PACKAGES[@]}" -gt 0 ]]; then
        failed_json=$(printf '%s\n' "${FAILED_PACKAGES[@]}" | jq -R . | jq -s .)
    fi

    cat > "${STATE_FILE}" <<EOF
{
  "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "profile": "${PROFILE}",
  "os_type": "${OS_TYPE}",
  "os_version": "${OS_VERSION}",
  "arch": "${ARCH}",
  "installed_packages": ${installed_json},
  "failed_packages": ${failed_json}
}
EOF

    log_debug "Installation state saved to ${STATE_FILE}"
}

###############################################################################
# System Detection Functions
###############################################################################

detect_os() {
    log_section "Detecting Operating System"

    # Detect OS type
    if [[ "$OSTYPE" == "darwin"* ]]; then
        OS_TYPE="macos"
        OS_VERSION=$(sw_vers -productVersion)
        PACKAGE_MANAGER="brew"
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        if [[ -f /etc/os-release ]]; then
            . /etc/os-release
            case "${ID}" in
                ubuntu|debian)
                    OS_TYPE="debian"
                    OS_VERSION="${VERSION_ID}"
                    PACKAGE_MANAGER="apt"
                    ;;
                rhel|centos|fedora)
                    OS_TYPE="rhel"
                    OS_VERSION="${VERSION_ID}"
                    PACKAGE_MANAGER="yum"
                    ;;
                *)
                    log_error "Unsupported Linux distribution: ${ID}"
                    exit 1
                    ;;
            esac
        fi

        # Check for WSL2
        if grep -qi microsoft /proc/version 2>/dev/null; then
            log_info "Detected Windows WSL2 environment"
            OS_TYPE="${OS_TYPE}-wsl2"
        fi
    else
        log_error "Unsupported operating system: ${OSTYPE}"
        exit 1
    fi

    # Detect architecture
    ARCH=$(uname -m)
    case "${ARCH}" in
        x86_64|amd64)
            ARCH="x86_64"
            ;;
        arm64|aarch64)
            ARCH="arm64"
            ;;
        *)
            log_warning "Unusual architecture detected: ${ARCH}"
            ;;
    esac

    log_success "OS Type: ${OS_TYPE}"
    log_success "OS Version: ${OS_VERSION}"
    log_success "Architecture: ${ARCH}"
    log_success "Package Manager: ${PACKAGE_MANAGER}"
}

verify_prerequisites() {
    log_section "Verifying Prerequisites"

    # Check if prerequisites file exists
    if [[ ! -f "${PREREQS_FILE}" ]]; then
        log_error "Prerequisites file not found: ${PREREQS_FILE}"
        log_error "Please ensure the prerequisites have been validated first"
        exit 1
    fi

    # Verify JSON validity
    if ! jq empty "${PREREQS_FILE}" 2>/dev/null; then
        log_error "Invalid JSON in prerequisites file"
        exit 1
    fi

    log_success "Prerequisites file validated"

    # Check for required tools
    local required_tools=("jq" "curl" "git")
    local missing_tools=()

    for tool in "${required_tools[@]}"; do
        if ! command_exists "${tool}"; then
            missing_tools+=("${tool}")
        fi
    done

    if [[ "${#missing_tools[@]}" -gt 0 ]]; then
        log_error "Missing required tools: ${missing_tools[*]}"
        log_info "Please install missing tools and try again"
        exit 1
    fi

    log_success "All required tools are available"
}

###############################################################################
# Package Manager Functions
###############################################################################

update_package_manager() {
    log_section "Updating Package Manager"

    case "${PACKAGE_MANAGER}" in
        brew)
            execute_cmd "brew update"
            ;;
        apt)
            execute_cmd "sudo apt-get update -y"
            ;;
        yum)
            execute_cmd "sudo yum update -y"
            ;;
        *)
            log_error "Unsupported package manager: ${PACKAGE_MANAGER}"
            exit 1
            ;;
    esac

    log_success "Package manager updated"
}

install_system_package() {
    local package_name="$1"
    local package_version="${2:-}"

    log_info "Installing system package: ${package_name}"

    case "${PACKAGE_MANAGER}" in
        brew)
            if brew list "${package_name}" &>/dev/null; then
                log_info "Package already installed: ${package_name}"
            else
                execute_cmd "brew install ${package_name}"
                add_rollback "brew uninstall ${package_name}"
            fi
            ;;
        apt)
            if dpkg -l | grep -q "^ii  ${package_name}"; then
                log_info "Package already installed: ${package_name}"
            else
                execute_cmd "sudo apt-get install -y ${package_name}"
                add_rollback "sudo apt-get remove -y ${package_name}"
            fi
            ;;
        yum)
            if rpm -qa | grep -q "${package_name}"; then
                log_info "Package already installed: ${package_name}"
            else
                execute_cmd "sudo yum install -y ${package_name}"
                add_rollback "sudo yum remove -y ${package_name}"
            fi
            ;;
    esac

    INSTALLED_PACKAGES+=("${package_name}")
}

###############################################################################
# Python Installation Functions
###############################################################################

install_python() {
    log_section "Installing Python 3.10+"

    local required_version="3.10"

    # Check if Python 3.10+ is already installed
    if command_exists python3; then
        local current_version=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
        if awk -v ver="${current_version}" -v req="${required_version}" 'BEGIN{if(ver>=req) exit 0; exit 1}'; then
            log_success "Python ${current_version} is already installed"
            return 0
        fi
    fi

    log_info "Installing Python ${required_version}+"

    case "${OS_TYPE}" in
        macos*)
            install_system_package "python@3.10"
            ;;
        debian*)
            install_system_package "python3.10"
            install_system_package "python3.10-venv"
            install_system_package "python3-pip"
            ;;
        rhel*)
            install_system_package "python310"
            install_system_package "python310-pip"
            ;;
    esac

    # Verify installation
    if python3 --version | grep -q "3.1[0-9]"; then
        log_success "Python installation successful"
    else
        log_error "Python installation failed"
        exit 1
    fi
}

install_pip_package() {
    local package_name="$1"
    local package_version="${2:-}"

    local package_spec="${package_name}"
    if [[ -n "${package_version}" ]]; then
        package_spec="${package_name}>=${package_version}"
    fi

    log_info "Installing Python package: ${package_spec}"

    if python3 -m pip show "${package_name}" &>/dev/null; then
        log_info "Package already installed: ${package_name}"
    else
        execute_cmd "python3 -m pip install '${package_spec}'"
        add_rollback "python3 -m pip uninstall -y ${package_name}"
        INSTALLED_PACKAGES+=("${package_name}")
    fi
}

###############################################################################
# Profile Installation Functions
###############################################################################

install_core_packages() {
    log_section "Installing Core Packages"

    local core_packages=$(jq -r '.core_packages[] | "\(.name)|\(.version)"' "${PREREQS_FILE}")

    while IFS='|' read -r name version; do
        install_pip_package "${name}" "${version}"
    done <<< "${core_packages}"

    log_success "Core packages installation completed"
}

install_optional_packages() {
    log_section "Installing Optional Packages"

    local optional_packages=$(jq -r '.optional_packages[] | "\(.name)|\(.version)"' "${PREREQS_FILE}")

    while IFS='|' read -r name version; do
        install_pip_package "${name}" "${version}"
    done <<< "${optional_packages}"

    log_success "Optional packages installation completed"
}

install_databases() {
    if [[ "${SKIP_DATABASES}" == true ]]; then
        log_warning "Skipping database installations"
        return 0
    fi

    log_section "Installing Databases"

    local databases=$(jq -r '.databases[] | "\(.name)|\(.version)"' "${PREREQS_FILE}")

    while IFS='|' read -r name version; do
        case "${name}" in
            redis)
                install_system_package "redis"
                ;;
            postgresql)
                install_system_package "postgresql@15"
                ;;
            neo4j)
                log_info "Neo4j requires manual installation via Docker or system package"
                log_info "Visit: https://neo4j.com/docs/operations-manual/current/installation/"
                ;;
        esac
    done <<< "${databases}"

    log_success "Database installations completed"
}

install_external_tools() {
    if [[ "${SKIP_TOOLS}" == true ]]; then
        log_warning "Skipping external tools installation"
        return 0
    fi

    log_section "Installing External Tools"

    local tools=$(jq -r '.external_tools[] | "\(.name)|\(.version)"' "${PREREQS_FILE}")

    while IFS='|' read -r name version; do
        case "${name}" in
            docker)
                log_info "Docker requires manual installation"
                log_info "Visit: https://docs.docker.com/get-docker/"
                ;;
            terraform)
                install_system_package "terraform"
                ;;
            trivy)
                install_system_package "trivy"
                ;;
            node)
                install_system_package "node@18"
                ;;
            airflow)
                log_info "Airflow should be installed via pip in a virtual environment"
                ;;
        esac
    done <<< "${tools}"

    log_success "External tools installation completed"
}

install_cloud_sdk_aws() {
    log_section "Installing AWS SDK"

    local aws_packages=$(jq -r '.cloud_sdks.aws[] | "\(.name)|\(.version)"' "${PREREQS_FILE}")

    while IFS='|' read -r name version; do
        install_pip_package "${name}" "${version}"
    done <<< "${aws_packages}"

    # Install AWS CLI
    if ! command_exists aws; then
        log_info "Installing AWS CLI"
        case "${OS_TYPE}" in
            macos*)
                install_system_package "awscli"
                ;;
            *)
                execute_cmd "curl 'https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip' -o '/tmp/awscliv2.zip'"
                execute_cmd "unzip -q /tmp/awscliv2.zip -d /tmp/"
                execute_cmd "sudo /tmp/aws/install"
                execute_cmd "rm -rf /tmp/aws /tmp/awscliv2.zip"
                ;;
        esac
    fi

    log_success "AWS SDK installation completed"
}

install_cloud_sdk_azure() {
    log_section "Installing Azure SDK"

    local azure_packages=$(jq -r '.cloud_sdks.azure[] | "\(.name)|\(.version)"' "${PREREQS_FILE}")

    while IFS='|' read -r name version; do
        install_pip_package "${name}" "${version}"
    done <<< "${azure_packages}"

    # Install Azure CLI
    if ! command_exists az; then
        log_info "Installing Azure CLI"
        case "${OS_TYPE}" in
            macos*)
                install_system_package "azure-cli"
                ;;
            debian*)
                execute_cmd "curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash"
                ;;
            rhel*)
                execute_cmd "sudo rpm --import https://packages.microsoft.com/keys/microsoft.asc"
                execute_cmd "sudo dnf install -y azure-cli"
                ;;
        esac
    fi

    log_success "Azure SDK installation completed"
}

install_cloud_sdk_gcp() {
    log_section "Installing GCP SDK"

    local gcp_packages=$(jq -r '.cloud_sdks.gcp[] | "\(.name)|\(.version)"' "${PREREQS_FILE}")

    while IFS='|' read -r name version; do
        install_pip_package "${name}" "${version}"
    done <<< "${gcp_packages}"

    # Install gcloud CLI
    if ! command_exists gcloud; then
        log_info "Installing Google Cloud SDK"
        log_info "Visit: https://cloud.google.com/sdk/docs/install"
    fi

    log_success "GCP SDK installation completed"
}

install_security_tools() {
    log_section "Installing Security Tools"

    # Install security-related packages
    local security_packages=("safety" "bandit" "checkov")

    for package in "${security_packages[@]}"; do
        local version=$(jq -r ".optional_packages[] | select(.name==\"${package}\") | .version" "${PREREQS_FILE}")
        if [[ -n "${version}" ]]; then
            install_pip_package "${package}" "${version}"
        fi
    done

    log_success "Security tools installation completed"
}

###############################################################################
# Profile Selection and Execution
###############################################################################

execute_profile() {
    log_section "Executing Profile: ${PROFILE}"

    case "${PROFILE}" in
        minimal)
            install_python
            install_core_packages
            ;;
        standard)
            install_python
            install_core_packages
            install_optional_packages
            ;;
        full)
            install_python
            install_core_packages
            install_optional_packages
            install_databases
            install_external_tools
            ;;
        security)
            install_python
            install_core_packages
            install_optional_packages
            install_security_tools
            ;;
        cloud-aws)
            install_python
            install_core_packages
            install_optional_packages
            install_cloud_sdk_aws
            ;;
        cloud-azure)
            install_python
            install_core_packages
            install_optional_packages
            install_cloud_sdk_azure
            ;;
        cloud-gcp)
            install_python
            install_core_packages
            install_optional_packages
            install_cloud_sdk_gcp
            ;;
        *)
            log_error "Unknown profile: ${PROFILE}"
            exit 1
            ;;
    esac

    log_success "Profile execution completed"
}

###############################################################################
# Post-Installation Functions
###############################################################################

verify_installation() {
    log_section "Verifying Installation"

    local failed=false

    # Verify Python
    if command_exists python3; then
        local python_version=$(python3 --version)
        log_success "Python: ${python_version}"
    else
        log_error "Python verification failed"
        failed=true
    fi

    # Verify pip
    if python3 -m pip --version &>/dev/null; then
        log_success "pip is available"
    else
        log_error "pip verification failed"
        failed=true
    fi

    # Verify installed packages
    log_info "Verifying installed packages..."
    for package in "${INSTALLED_PACKAGES[@]}"; do
        if python3 -m pip show "${package}" &>/dev/null || command_exists "${package}"; then
            log_debug "✓ ${package}"
        else
            log_warning "✗ ${package} verification failed"
            FAILED_PACKAGES+=("${package}")
        fi
    done

    if [[ "${failed}" == true ]]; then
        log_error "Installation verification failed"
        return 1
    fi

    log_success "Installation verification passed"
}

generate_report() {
    log_section "Installation Report"

    local report_file="${LOG_DIR}/installation_report_$(date +%Y%m%d_%H%M%S).txt"

    cat > "${report_file}" <<EOF
DevGRU Setup Installation Report
================================

Timestamp: $(date)
Profile: ${PROFILE}
OS Type: ${OS_TYPE}
OS Version: ${OS_VERSION}
Architecture: ${ARCH}

Installed Packages (${#INSTALLED_PACKAGES[@]}):
$(printf '  - %s\n' "${INSTALLED_PACKAGES[@]}")

Failed Packages (${#FAILED_PACKAGES[@]}):
$(printf '  - %s\n' "${FAILED_PACKAGES[@]}")

Log File: ${LOG_FILE}
State File: ${STATE_FILE}

Next Steps:
1. Review the log file for any warnings or errors
2. Verify package installations with: pip list
3. Configure cloud provider credentials if applicable
4. Set up virtual environments for project isolation
5. Review project-specific requirements

EOF

    cat "${report_file}" | tee -a "${LOG_FILE}"
    log_success "Report saved to: ${report_file}"
}

###############################################################################
# Command-Line Argument Parsing
###############################################################################

show_help() {
    cat <<EOF
DevGRU Multi-OS Prerequisites Setup Script v${SCRIPT_VERSION}

Usage: ./setup_devgru.sh [OPTIONS]

Options:
  --profile PROFILE     Installation profile (default: standard)
                        Available profiles:
                          minimal    - Python 3.10+ + 5 core packages
                          standard   - minimal + 15 optional packages
                          full       - standard + databases + external tools
                          security   - standard + security tools
                          cloud-aws  - standard + AWS SDK
                          cloud-azure- standard + Azure SDK
                          cloud-gcp  - standard + GCP SDK

  --dry-run            Show what would be installed without installing
  --verbose            Enable verbose output
  --skip-databases     Skip database installations
  --skip-tools         Skip external tools installation
  --help               Show this help message

Examples:
  # Install standard profile
  ./setup_devgru.sh

  # Install full profile with verbose output
  ./setup_devgru.sh --profile full --verbose

  # Test installation with dry-run
  ./setup_devgru.sh --profile security --dry-run

  # Install AWS cloud profile without databases
  ./setup_devgru.sh --profile cloud-aws --skip-databases

For more information, visit: https://github.com/devCrew_s1
EOF
}

parse_arguments() {
    while [[ $# -gt 0 ]]; do
        case "$1" in
            --profile)
                PROFILE="$2"
                shift 2
                ;;
            --dry-run)
                DRY_RUN=true
                shift
                ;;
            --verbose)
                VERBOSE=true
                shift
                ;;
            --skip-databases)
                SKIP_DATABASES=true
                shift
                ;;
            --skip-tools)
                SKIP_TOOLS=true
                shift
                ;;
            --help|-h)
                show_help
                exit 0
                ;;
            *)
                log_error "Unknown option: $1"
                show_help
                exit 1
                ;;
        esac
    done

    # Validate profile
    local valid_profiles=("minimal" "standard" "full" "security" "cloud-aws" "cloud-azure" "cloud-gcp")
    local valid=false
    for p in "${valid_profiles[@]}"; do
        if [[ "${PROFILE}" == "${p}" ]]; then
            valid=true
            break
        fi
    done

    if [[ "${valid}" != true ]]; then
        log_error "Invalid profile: ${PROFILE}"
        log_info "Valid profiles: ${valid_profiles[*]}"
        exit 1
    fi
}

###############################################################################
# Cleanup and Signal Handling
###############################################################################

cleanup() {
    local exit_code=$?

    if [[ ${exit_code} -ne 0 ]]; then
        log_error "Setup failed with exit code: ${exit_code}"

        if confirm "Do you want to rollback changes?"; then
            execute_rollback
        fi
    fi

    # Save installation state
    save_state

    log_info "Cleanup completed"
    exit ${exit_code}
}

handle_interrupt() {
    log_warning "Setup interrupted by user"
    cleanup
}

# Set up signal handlers
trap cleanup EXIT
trap handle_interrupt INT TERM

###############################################################################
# Main Execution
###############################################################################

main() {
    # Parse command-line arguments
    parse_arguments "$@"

    # Create log directory
    mkdir -p "${LOG_DIR}"
    mkdir -p "${STATE_DIR}"

    # Print banner
    log_section "DevGRU Setup Script v${SCRIPT_VERSION}"

    log_info "Profile: ${PROFILE}"
    log_info "Dry Run: ${DRY_RUN}"
    log_info "Verbose: ${VERBOSE}"
    log_info "Skip Databases: ${SKIP_DATABASES}"
    log_info "Skip Tools: ${SKIP_TOOLS}"
    log_info "Log File: ${LOG_FILE}"

    if [[ "${DRY_RUN}" == true ]]; then
        log_warning "DRY RUN MODE - No actual changes will be made"
    fi

    # Check for root privileges warning
    if is_root; then
        log_warning "Running as root is not recommended"
        if ! confirm "Continue anyway?"; then
            log_info "Setup cancelled by user"
            exit 0
        fi
    fi

    # Execute setup steps
    detect_os
    verify_prerequisites
    update_package_manager
    execute_profile
    verify_installation
    generate_report

    # Success message
    log_section "Setup Completed Successfully!"
    log_success "DevGRU environment has been configured with profile: ${PROFILE}"
    log_success "Total packages installed: ${#INSTALLED_PACKAGES[@]}"

    if [[ "${#FAILED_PACKAGES[@]}" -gt 0 ]]; then
        log_warning "Some packages failed to install: ${#FAILED_PACKAGES[@]}"
        log_warning "Check the log file for details: ${LOG_FILE}"
    fi

    log_info "Next steps:"
    log_info "  1. Review the installation report"
    log_info "  2. Configure cloud provider credentials (if applicable)"
    log_info "  3. Create a virtual environment for your projects"
    log_info "  4. Install project-specific dependencies"

    return 0
}

# Execute main function
main "$@"
