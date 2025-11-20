#!/bin/bash
# Cloud SDKs Installation Module
# Installs AWS, Azure, and GCP Python SDKs for devCrew_s1 project
# Part of Multi-OS Prerequisites Setup Script (GitHub Issue #67)

set -e

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
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

# Check if pip is available
check_pip() {
    if ! command -v pip &> /dev/null && ! command -v pip3 &> /dev/null; then
        log_error "pip or pip3 is not installed. Please install Python and pip first."
        return 1
    fi

    # Prefer pip3 if available
    if command -v pip3 &> /dev/null; then
        PIP_CMD="pip3"
    else
        PIP_CMD="pip"
    fi

    log_info "Using pip command: $PIP_CMD"
    return 0
}

# Verify package installation
verify_package() {
    local package_name=$1
    local import_name=${2:-$package_name}

    if python3 -c "import ${import_name}" 2>/dev/null; then
        local version=$(python3 -c "import ${import_name}; print(getattr(${import_name}, '__version__', 'unknown'))" 2>/dev/null || echo "unknown")
        log_success "Verified ${package_name} (version: ${version})"
        return 0
    else
        log_error "Failed to verify ${package_name}"
        return 1
    fi
}

# Install AWS SDKs
install_aws_sdks() {
    log_info "Installing AWS SDKs..."

    local aws_packages=(
        "boto3>=1.34"
    )

    local failed_packages=()

    for package in "${aws_packages[@]}"; do
        local package_name=$(echo "$package" | cut -d'>' -f1 | cut -d'=' -f1)
        log_info "Installing ${package}..."

        if $PIP_CMD install "${package}" --upgrade 2>&1 | tee /tmp/pip_install.log; then
            # Verify installation
            if verify_package "$package_name" "$package_name"; then
                log_success "Successfully installed ${package}"
            else
                log_warning "${package} installed but verification failed"
                failed_packages+=("$package_name")
            fi
        else
            log_error "Failed to install ${package}"
            failed_packages+=("$package_name")
        fi
    done

    if [ ${#failed_packages[@]} -eq 0 ]; then
        log_success "All AWS SDKs installed successfully"
        return 0
    else
        log_error "Failed to install the following AWS packages: ${failed_packages[*]}"
        return 1
    fi
}

# Install Azure SDKs
install_azure_sdks() {
    log_info "Installing Azure SDKs..."

    local azure_packages=(
        "azure-mgmt-resource>=23.0"
        "azure-storage-blob>=12.0"
        "azure-mgmt-costmanagement>=4.0"
    )

    local failed_packages=()

    for package in "${azure_packages[@]}"; do
        local package_name=$(echo "$package" | cut -d'>' -f1 | cut -d'=' -f1)
        log_info "Installing ${package}..."

        if $PIP_CMD install "${package}" --upgrade 2>&1 | tee /tmp/pip_install.log; then
            # Convert package name to import name (replace hyphens with underscores)
            local import_name=$(echo "$package_name" | sed 's/-/_/g')

            # For azure packages, we need to handle the namespace differently
            if [[ "$package_name" == "azure-mgmt-resource" ]]; then
                import_name="azure.mgmt.resource"
            elif [[ "$package_name" == "azure-storage-blob" ]]; then
                import_name="azure.storage.blob"
            elif [[ "$package_name" == "azure-mgmt-costmanagement" ]]; then
                import_name="azure.mgmt.costmanagement"
            fi

            # Verify installation
            if verify_package "$package_name" "$import_name"; then
                log_success "Successfully installed ${package}"
            else
                log_warning "${package} installed but verification failed"
                failed_packages+=("$package_name")
            fi
        else
            log_error "Failed to install ${package}"
            failed_packages+=("$package_name")
        fi
    done

    if [ ${#failed_packages[@]} -eq 0 ]; then
        log_success "All Azure SDKs installed successfully"
        return 0
    else
        log_error "Failed to install the following Azure packages: ${failed_packages[*]}"
        return 1
    fi
}

# Install GCP SDKs
install_gcp_sdks() {
    log_info "Installing GCP SDKs..."

    local gcp_packages=(
        "google-cloud-storage>=2.14"
        "google-cloud-billing>=1.12"
        "google-cloud-resource-manager>=1.11"
    )

    local failed_packages=()

    for package in "${gcp_packages[@]}"; do
        local package_name=$(echo "$package" | cut -d'>' -f1 | cut -d'=' -f1)
        log_info "Installing ${package}..."

        if $PIP_CMD install "${package}" --upgrade 2>&1 | tee /tmp/pip_install.log; then
            # Convert package name to import name
            local import_name=$(echo "$package_name" | sed 's/-/_/g' | sed 's/google_cloud/google.cloud/')

            # Verify installation
            if verify_package "$package_name" "$import_name"; then
                log_success "Successfully installed ${package}"
            else
                log_warning "${package} installed but verification failed"
                failed_packages+=("$package_name")
            fi
        else
            log_error "Failed to install ${package}"
            failed_packages+=("$package_name")
        fi
    done

    if [ ${#failed_packages[@]} -eq 0 ]; then
        log_success "All GCP SDKs installed successfully"
        return 0
    else
        log_error "Failed to install the following GCP packages: ${failed_packages[*]}"
        return 1
    fi
}

# Install all cloud SDKs
install_all_cloud_sdks() {
    log_info "Starting Cloud SDKs installation..."

    # Check pip availability
    if ! check_pip; then
        log_error "Cannot proceed without pip. Please install Python and pip first."
        return 1
    fi

    local overall_status=0

    # Install AWS SDKs
    if install_aws_sdks; then
        log_success "AWS SDKs installation completed"
    else
        log_warning "AWS SDKs installation completed with errors"
        overall_status=1
    fi

    echo ""

    # Install Azure SDKs
    if install_azure_sdks; then
        log_success "Azure SDKs installation completed"
    else
        log_warning "Azure SDKs installation completed with errors"
        overall_status=1
    fi

    echo ""

    # Install GCP SDKs
    if install_gcp_sdks; then
        log_success "GCP SDKs installation completed"
    else
        log_warning "GCP SDKs installation completed with errors"
        overall_status=1
    fi

    echo ""

    if [ $overall_status -eq 0 ]; then
        log_success "All Cloud SDKs installed successfully!"
        return 0
    else
        log_warning "Cloud SDKs installation completed with some errors. Please review the output above."
        return 1
    fi
}

# Show usage information
show_usage() {
    cat << EOF
Cloud SDKs Installation Module

Usage: $0 [OPTION]

Options:
    --all           Install all cloud SDKs (AWS, Azure, GCP)
    --aws           Install only AWS SDKs
    --azure         Install only Azure SDKs
    --gcp           Install only GCP SDKs
    --help          Show this help message

Examples:
    $0 --all        # Install all cloud SDKs
    $0 --aws        # Install only AWS SDKs
    $0 --azure --gcp # Install Azure and GCP SDKs

EOF
}

# Main execution
main() {
    if [ $# -eq 0 ]; then
        log_info "No arguments provided. Installing all cloud SDKs..."
        install_all_cloud_sdks
        exit $?
    fi

    local install_aws=false
    local install_azure=false
    local install_gcp=false
    local install_all=false

    # Parse arguments
    while [ $# -gt 0 ]; do
        case $1 in
            --all)
                install_all=true
                shift
                ;;
            --aws)
                install_aws=true
                shift
                ;;
            --azure)
                install_azure=true
                shift
                ;;
            --gcp)
                install_gcp=true
                shift
                ;;
            --help)
                show_usage
                exit 0
                ;;
            *)
                log_error "Unknown option: $1"
                show_usage
                exit 1
                ;;
        esac
    done

    # Check pip availability
    if ! check_pip; then
        log_error "Cannot proceed without pip. Please install Python and pip first."
        exit 1
    fi

    local overall_status=0

    # Install based on flags
    if [ "$install_all" = true ]; then
        install_all_cloud_sdks
        exit $?
    fi

    if [ "$install_aws" = true ]; then
        if install_aws_sdks; then
            log_success "AWS SDKs installation completed"
        else
            log_warning "AWS SDKs installation completed with errors"
            overall_status=1
        fi
        echo ""
    fi

    if [ "$install_azure" = true ]; then
        if install_azure_sdks; then
            log_success "Azure SDKs installation completed"
        else
            log_warning "Azure SDKs installation completed with errors"
            overall_status=1
        fi
        echo ""
    fi

    if [ "$install_gcp" = true ]; then
        if install_gcp_sdks; then
            log_success "GCP SDKs installation completed"
        else
            log_warning "GCP SDKs installation completed with errors"
            overall_status=1
        fi
        echo ""
    fi

    exit $overall_status
}

# Run main function if script is executed directly
if [ "${BASH_SOURCE[0]}" == "${0}" ]; then
    main "$@"
fi
