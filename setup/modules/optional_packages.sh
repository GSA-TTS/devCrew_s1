#!/bin/bash

###############################################################################
# Optional Python Packages Installation Module
# Part of devCrew_s1 Multi-OS Prerequisites Setup Script
# GitHub Issue #67
###############################################################################

set -e

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Counter for tracking installations
SUCCESSFUL_INSTALLS=0
FAILED_INSTALLS=0
TOTAL_PACKAGES=15

###############################################################################
# Helper Functions
###############################################################################

print_header() {
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

# Check if Python is available
check_python() {
    if command -v python3 &> /dev/null; then
        PYTHON_CMD="python3"
    elif command -v python &> /dev/null; then
        PYTHON_CMD="python"
    else
        print_error "Python is not installed. Please install Python 3.10+ first."
        exit 1
    fi

    # Verify Python version
    PYTHON_VERSION=$($PYTHON_CMD --version 2>&1 | awk '{print $2}')
    print_info "Using Python $PYTHON_VERSION"
}

# Check if pip is available
check_pip() {
    if ! $PYTHON_CMD -m pip --version &> /dev/null; then
        print_error "pip is not installed. Please install pip first."
        exit 1
    fi

    PIP_VERSION=$($PYTHON_CMD -m pip --version | awk '{print $2}')
    print_info "Using pip $PIP_VERSION"
}

# Install a single package with error handling
install_package() {
    local package_name=$1
    local package_version=$2

    print_info "Installing ${package_name}==${package_version}..."

    if $PYTHON_CMD -m pip install "${package_name}==${package_version}" --no-cache-dir 2>&1 | tee /tmp/pip_install_${package_name}.log; then
        print_success "${package_name} installed successfully"
        ((SUCCESSFUL_INSTALLS++))
        return 0
    else
        print_error "Failed to install ${package_name}"
        print_warning "Check /tmp/pip_install_${package_name}.log for details"
        ((FAILED_INSTALLS++))
        return 1
    fi
}

# Verify package installation
verify_package() {
    local package_name=$1

    if $PYTHON_CMD -c "import ${package_name}" 2>/dev/null; then
        return 0
    else
        # Try alternative import names
        case $package_name in
            "beautifulsoup4")
                if $PYTHON_CMD -c "import bs4" 2>/dev/null; then
                    return 0
                fi
                ;;
            "sentence-transformers")
                if $PYTHON_CMD -c "import sentence_transformers" 2>/dev/null; then
                    return 0
                fi
                ;;
        esac
        return 1
    fi
}

###############################################################################
# Main Installation Process
###############################################################################

main() {
    print_header "Optional Python Packages Installation"

    # Pre-flight checks
    check_python
    check_pip

    echo ""
    print_info "Starting installation of $TOTAL_PACKAGES optional packages..."
    echo ""

    # Define packages array with versions from prerequisites_validated.json
    declare -A PACKAGES=(
        ["fastapi"]="0.104"
        ["sqlalchemy"]="2.0"
        ["pytest"]="7.4"
        ["langchain"]="0.1"
        ["spacy"]="3.7"
        ["beautifulsoup4"]="4.12"
        ["scrapy"]="2.11"
        ["docker"]="7.0"
        ["kubernetes"]="1.27"
        ["safety"]="3.0"
        ["bandit"]="1.7.5"
        ["checkov"]="3.1"
        ["numpy"]="1.24"
        ["sentence-transformers"]="2.2"
        ["chromadb"]="0.4"
    )

    # Install packages in order
    print_header "Installing Web Framework & Database"
    install_package "fastapi" "${PACKAGES[fastapi]}"
    install_package "sqlalchemy" "${PACKAGES[sqlalchemy]}"

    echo ""
    print_header "Installing Testing Framework"
    install_package "pytest" "${PACKAGES[pytest]}"

    echo ""
    print_header "Installing AI & NLP Tools"
    install_package "langchain" "${PACKAGES[langchain]}"
    install_package "spacy" "${PACKAGES[spacy]}"
    install_package "sentence-transformers" "${PACKAGES[sentence-transformers]}"
    install_package "chromadb" "${PACKAGES[chromadb]}"

    echo ""
    print_header "Installing Web Scraping Tools"
    install_package "beautifulsoup4" "${PACKAGES[beautifulsoup4]}"
    install_package "scrapy" "${PACKAGES[scrapy]}"

    echo ""
    print_header "Installing Container & Orchestration SDKs"
    install_package "docker" "${PACKAGES[docker]}"
    install_package "kubernetes" "${PACKAGES[kubernetes]}"

    echo ""
    print_header "Installing Security Tools"
    install_package "safety" "${PACKAGES[safety]}"
    install_package "bandit" "${PACKAGES[bandit]}"
    install_package "checkov" "${PACKAGES[checkov]}"

    echo ""
    print_header "Installing Data Science Tools"
    install_package "numpy" "${PACKAGES[numpy]}"

    # Special handling for spaCy model
    echo ""
    print_header "Downloading spaCy English Model"
    print_info "Installing en_core_web_sm model for spaCy..."

    if $PYTHON_CMD -m spacy download en_core_web_sm 2>&1 | tee /tmp/spacy_model_install.log; then
        print_success "spaCy English model installed successfully"
    else
        print_error "Failed to install spaCy English model"
        print_warning "Check /tmp/spacy_model_install.log for details"
    fi

    # Verification phase
    echo ""
    print_header "Verifying Installations"

    VERIFICATION_FAILED=0

    for package in "${!PACKAGES[@]}"; do
        print_info "Verifying ${package}..."
        if verify_package "$package"; then
            print_success "${package} verified"
        else
            print_warning "${package} could not be verified (import test failed)"
            ((VERIFICATION_FAILED++))
        fi
    done

    # Special verification for spaCy model
    print_info "Verifying spaCy model..."
    if $PYTHON_CMD -c "import spacy; spacy.load('en_core_web_sm')" 2>/dev/null; then
        print_success "spaCy model verified"
    else
        print_warning "spaCy model could not be verified"
        ((VERIFICATION_FAILED++))
    fi

    # Final summary
    echo ""
    print_header "Installation Summary"
    echo -e "Total packages: ${BLUE}${TOTAL_PACKAGES}${NC}"
    echo -e "Successfully installed: ${GREEN}${SUCCESSFUL_INSTALLS}${NC}"
    echo -e "Failed installations: ${RED}${FAILED_INSTALLS}${NC}"
    echo -e "Verification warnings: ${YELLOW}${VERIFICATION_FAILED}${NC}"

    if [ $FAILED_INSTALLS -eq 0 ]; then
        echo ""
        print_success "All optional packages installed successfully!"
        return 0
    else
        echo ""
        print_warning "Some packages failed to install. Check logs in /tmp/ for details."
        return 1
    fi
}

###############################################################################
# Script Entry Point
###############################################################################

# Run main function
main "$@"
exit_code=$?

echo ""
print_info "Optional packages installation completed with exit code: $exit_code"
exit $exit_code
