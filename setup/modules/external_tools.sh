#!/usr/bin/env bash
#
# External Tools Installation Module for devCrew_s1
# Supports: macOS, Ubuntu/Debian, RHEL/CentOS
#
# Tools: Docker 24.0+, Terraform 1.6+, Trivy 0.48+, Node.js 18+, Apache Airflow 2.7+
#

set -euo pipefail

# Color codes for output
readonly RED='\033[0;31m'
readonly GREEN='\033[0;32m'
readonly YELLOW='\033[1;33m'
readonly BLUE='\033[0;34m'
readonly NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $*"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $*"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $*"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $*" >&2
}

# Detect OS type
detect_os() {
    if [[ "$OSTYPE" == "darwin"* ]]; then
        echo "macos"
    elif [[ -f /etc/os-release ]]; then
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
}

# Check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Version comparison function
version_ge() {
    # Returns 0 if $1 >= $2
    printf '%s\n%s\n' "$2" "$1" | sort -V -C
}

# ============================================================================
# DOCKER INSTALLATION
# ============================================================================

install_docker_macos() {
    log_info "Installing Docker on macOS..."

    if command_exists docker; then
        log_warn "Docker is already installed"
        return 0
    fi

    if ! command_exists brew; then
        log_error "Homebrew is required but not installed"
        log_info "Please install Homebrew first: https://brew.sh"
        return 1
    fi

    brew install --cask docker || {
        log_error "Failed to install Docker"
        return 1
    }

    log_success "Docker installed successfully"
    log_warn "Please start Docker Desktop manually from Applications"
    return 0
}

install_docker_debian() {
    log_info "Installing Docker on Debian/Ubuntu..."

    if command_exists docker; then
        log_warn "Docker is already installed"
        return 0
    fi

    # Remove old versions
    sudo apt-get remove -y docker docker-engine docker.io containerd runc 2>/dev/null || true

    # Update package index
    sudo apt-get update || {
        log_error "Failed to update package index"
        return 1
    }

    # Install prerequisites
    sudo apt-get install -y \
        ca-certificates \
        curl \
        gnupg \
        lsb-release || {
        log_error "Failed to install prerequisites"
        return 1
    }

    # Add Docker's official GPG key
    sudo install -m 0755 -d /etc/apt/keyrings
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
    sudo chmod a+r /etc/apt/keyrings/docker.gpg

    # Set up repository
    echo \
        "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
        $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
        sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

    # Install Docker
    sudo apt-get update
    sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin || {
        log_error "Failed to install Docker"
        return 1
    }

    # Add current user to docker group
    sudo usermod -aG docker "$USER" || log_warn "Could not add user to docker group"

    log_success "Docker installed successfully"
    log_warn "You may need to log out and back in for group changes to take effect"
    return 0
}

install_docker_rhel() {
    log_info "Installing Docker on RHEL/CentOS..."

    if command_exists docker; then
        log_warn "Docker is already installed"
        return 0
    fi

    # Remove old versions
    sudo dnf remove -y docker docker-client docker-client-latest docker-common \
        docker-latest docker-latest-logrotate docker-logrotate docker-engine 2>/dev/null || true

    # Install prerequisites
    sudo dnf install -y dnf-plugins-core || {
        log_error "Failed to install prerequisites"
        return 1
    }

    # Add Docker repository
    sudo dnf config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo || {
        log_error "Failed to add Docker repository"
        return 1
    }

    # Install Docker
    sudo dnf install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin || {
        log_error "Failed to install Docker"
        return 1
    }

    # Start Docker
    sudo systemctl start docker
    sudo systemctl enable docker

    # Add current user to docker group
    sudo usermod -aG docker "$USER" || log_warn "Could not add user to docker group"

    log_success "Docker installed successfully"
    log_warn "You may need to log out and back in for group changes to take effect"
    return 0
}

verify_docker() {
    log_info "Verifying Docker installation..."

    if ! command_exists docker; then
        log_error "Docker is not installed"
        return 1
    fi

    local docker_version
    docker_version=$(docker --version | grep -oP '\d+\.\d+' | head -1)

    if version_ge "$docker_version" "24.0"; then
        log_success "Docker $docker_version is installed (>= 24.0)"
        return 0
    else
        log_error "Docker version $docker_version is too old (requires >= 24.0)"
        return 1
    fi
}

# ============================================================================
# TERRAFORM INSTALLATION
# ============================================================================

install_terraform_macos() {
    log_info "Installing Terraform on macOS..."

    if ! command_exists brew; then
        log_error "Homebrew is required but not installed"
        return 1
    fi

    # Recommend tfenv for version management
    if ! command_exists tfenv; then
        log_info "Installing tfenv for Terraform version management..."
        brew install tfenv || {
            log_error "Failed to install tfenv"
            return 1
        }
    fi

    if command_exists terraform; then
        log_warn "Terraform is already installed"
        return 0
    fi

    # Install Terraform via tfenv
    tfenv install 1.6.0 || {
        log_error "Failed to install Terraform"
        return 1
    }
    tfenv use 1.6.0

    log_success "Terraform installed successfully via tfenv"
    log_info "Use 'tfenv install <version>' to install other versions"
    return 0
}

install_terraform_debian() {
    log_info "Installing Terraform on Debian/Ubuntu..."

    if command_exists terraform; then
        log_warn "Terraform is already installed"
        return 0
    fi

    # Install tfenv for version management
    if ! command_exists tfenv; then
        log_info "Installing tfenv for Terraform version management..."
        git clone --depth=1 https://github.com/tfutils/tfenv.git ~/.tfenv || {
            log_error "Failed to clone tfenv repository"
            return 1
        }

        # Add to PATH
        if ! grep -q "tfenv/bin" ~/.bashrc; then
            echo 'export PATH="$HOME/.tfenv/bin:$PATH"' >> ~/.bashrc
        fi
        export PATH="$HOME/.tfenv/bin:$PATH"
    fi

    # Install Terraform
    ~/.tfenv/bin/tfenv install 1.6.0 || {
        log_error "Failed to install Terraform"
        return 1
    }
    ~/.tfenv/bin/tfenv use 1.6.0

    log_success "Terraform installed successfully via tfenv"
    log_info "Use 'tfenv install <version>' to install other versions"
    log_warn "Please restart your shell or run: source ~/.bashrc"
    return 0
}

install_terraform_rhel() {
    log_info "Installing Terraform on RHEL/CentOS..."

    if command_exists terraform; then
        log_warn "Terraform is already installed"
        return 0
    fi

    # Install tfenv for version management
    if ! command_exists tfenv; then
        log_info "Installing tfenv for Terraform version management..."
        git clone --depth=1 https://github.com/tfutils/tfenv.git ~/.tfenv || {
            log_error "Failed to clone tfenv repository"
            return 1
        }

        # Add to PATH
        if ! grep -q "tfenv/bin" ~/.bashrc; then
            echo 'export PATH="$HOME/.tfenv/bin:$PATH"' >> ~/.bashrc
        fi
        export PATH="$HOME/.tfenv/bin:$PATH"
    fi

    # Install Terraform
    ~/.tfenv/bin/tfenv install 1.6.0 || {
        log_error "Failed to install Terraform"
        return 1
    }
    ~/.tfenv/bin/tfenv use 1.6.0

    log_success "Terraform installed successfully via tfenv"
    log_info "Use 'tfenv install <version>' to install other versions"
    log_warn "Please restart your shell or run: source ~/.bashrc"
    return 0
}

verify_terraform() {
    log_info "Verifying Terraform installation..."

    if ! command_exists terraform; then
        log_error "Terraform is not installed"
        return 1
    fi

    local terraform_version
    terraform_version=$(terraform version -json | grep -oP '"terraform_version":"\K[^"]+' 2>/dev/null || terraform version | grep -oP 'Terraform v\K[\d.]+')

    if version_ge "$terraform_version" "1.6.0"; then
        log_success "Terraform $terraform_version is installed (>= 1.6.0)"
        return 0
    else
        log_error "Terraform version $terraform_version is too old (requires >= 1.6.0)"
        return 1
    fi
}

# ============================================================================
# TRIVY INSTALLATION
# ============================================================================

install_trivy_macos() {
    log_info "Installing Trivy on macOS..."

    if command_exists trivy; then
        log_warn "Trivy is already installed"
        return 0
    fi

    if ! command_exists brew; then
        log_error "Homebrew is required but not installed"
        return 1
    fi

    brew install aquasecurity/trivy/trivy || {
        log_error "Failed to install Trivy"
        return 1
    }

    log_success "Trivy installed successfully"
    return 0
}

install_trivy_debian() {
    log_info "Installing Trivy on Debian/Ubuntu..."

    if command_exists trivy; then
        log_warn "Trivy is already installed"
        return 0
    fi

    # Download and install from GitHub releases
    local trivy_version="0.48.0"
    local arch
    arch=$(dpkg --print-architecture)

    log_info "Downloading Trivy v${trivy_version}..."

    local temp_dir
    temp_dir=$(mktemp -d)
    cd "$temp_dir" || return 1

    curl -sfL "https://github.com/aquasecurity/trivy/releases/download/v${trivy_version}/trivy_${trivy_version}_Linux-64bit.tar.gz" -o trivy.tar.gz || {
        log_error "Failed to download Trivy"
        rm -rf "$temp_dir"
        return 1
    }

    tar -xzf trivy.tar.gz || {
        log_error "Failed to extract Trivy"
        rm -rf "$temp_dir"
        return 1
    }

    sudo install -m 755 trivy /usr/local/bin/trivy || {
        log_error "Failed to install Trivy"
        rm -rf "$temp_dir"
        return 1
    }

    rm -rf "$temp_dir"

    log_success "Trivy installed successfully"
    return 0
}

install_trivy_rhel() {
    log_info "Installing Trivy on RHEL/CentOS..."

    if command_exists trivy; then
        log_warn "Trivy is already installed"
        return 0
    fi

    # Download and install from GitHub releases
    local trivy_version="0.48.0"

    log_info "Downloading Trivy v${trivy_version}..."

    local temp_dir
    temp_dir=$(mktemp -d)
    cd "$temp_dir" || return 1

    curl -sfL "https://github.com/aquasecurity/trivy/releases/download/v${trivy_version}/trivy_${trivy_version}_Linux-64bit.tar.gz" -o trivy.tar.gz || {
        log_error "Failed to download Trivy"
        rm -rf "$temp_dir"
        return 1
    }

    tar -xzf trivy.tar.gz || {
        log_error "Failed to extract Trivy"
        rm -rf "$temp_dir"
        return 1
    }

    sudo install -m 755 trivy /usr/local/bin/trivy || {
        log_error "Failed to install Trivy"
        rm -rf "$temp_dir"
        return 1
    }

    rm -rf "$temp_dir"

    log_success "Trivy installed successfully"
    return 0
}

verify_trivy() {
    log_info "Verifying Trivy installation..."

    if ! command_exists trivy; then
        log_error "Trivy is not installed"
        return 1
    fi

    local trivy_version
    trivy_version=$(trivy --version | grep -oP 'Version: \K[\d.]+')

    if version_ge "$trivy_version" "0.48.0"; then
        log_success "Trivy $trivy_version is installed (>= 0.48.0)"
        return 0
    else
        log_error "Trivy version $trivy_version is too old (requires >= 0.48.0)"
        return 1
    fi
}

# ============================================================================
# NODE.JS INSTALLATION
# ============================================================================

install_nodejs_macos() {
    log_info "Installing Node.js on macOS..."

    if command_exists node; then
        log_warn "Node.js is already installed"
        return 0
    fi

    if ! command_exists brew; then
        log_error "Homebrew is required but not installed"
        return 1
    fi

    brew install node@18 || {
        log_error "Failed to install Node.js"
        return 1
    }

    # Link Node.js
    brew link --force --overwrite node@18 || log_warn "Could not link Node.js"

    log_success "Node.js installed successfully"
    return 0
}

install_nodejs_debian() {
    log_info "Installing Node.js on Debian/Ubuntu..."

    if command_exists node; then
        log_warn "Node.js is already installed"
        return 0
    fi

    # Install Node.js from NodeSource repository
    curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash - || {
        log_error "Failed to add NodeSource repository"
        return 1
    }

    sudo apt-get install -y nodejs || {
        log_error "Failed to install Node.js"
        return 1
    }

    log_success "Node.js installed successfully"
    return 0
}

install_nodejs_rhel() {
    log_info "Installing Node.js on RHEL/CentOS..."

    if command_exists node; then
        log_warn "Node.js is already installed"
        return 0
    fi

    # Install Node.js from NodeSource repository
    curl -fsSL https://rpm.nodesource.com/setup_18.x | sudo bash - || {
        log_error "Failed to add NodeSource repository"
        return 1
    }

    sudo dnf install -y nodejs || {
        log_error "Failed to install Node.js"
        return 1
    }

    log_success "Node.js installed successfully"
    return 0
}

verify_nodejs() {
    log_info "Verifying Node.js installation..."

    if ! command_exists node; then
        log_error "Node.js is not installed"
        return 1
    fi

    local node_version
    node_version=$(node --version | grep -oP '\d+' | head -1)

    if [[ "$node_version" -ge 18 ]]; then
        log_success "Node.js v$(node --version) is installed (>= v18)"
        log_info "npm version: $(npm --version)"
        return 0
    else
        log_error "Node.js version $node_version is too old (requires >= v18)"
        return 1
    fi
}

# ============================================================================
# APACHE AIRFLOW INSTALLATION
# ============================================================================

install_airflow_common() {
    log_info "Installing Apache Airflow..."

    if command_exists airflow; then
        log_warn "Apache Airflow is already installed"
        return 0
    fi

    # Check if Python is installed
    if ! command_exists python3; then
        log_error "Python 3 is required but not installed"
        return 1
    fi

    local python_version
    python_version=$(python3 --version | grep -oP '\d+\.\d+' | head -1)

    if ! version_ge "$python_version" "3.8"; then
        log_error "Python version $python_version is too old (requires >= 3.8)"
        return 1
    fi

    # Check if pip is installed
    if ! command_exists pip3; then
        log_error "pip3 is required but not installed"
        return 1
    fi

    # Set Airflow version and constraints
    local airflow_version="2.7.0"
    local python_version_constraint
    python_version_constraint=$(python3 --version | grep -oP '\d+\.\d+' | head -1)
    local constraint_url="https://raw.githubusercontent.com/apache/airflow/constraints-${airflow_version}/constraints-${python_version_constraint}.txt"

    log_info "Installing Apache Airflow ${airflow_version} with Python ${python_version_constraint} constraints..."

    # Install Airflow
    pip3 install "apache-airflow==${airflow_version}" --constraint "$constraint_url" || {
        log_error "Failed to install Apache Airflow"
        return 1
    }

    log_success "Apache Airflow installed successfully"
    log_info "To initialize Airflow, run: airflow db init"
    log_info "To start Airflow webserver, run: airflow webserver -p 8080"
    log_info "To start Airflow scheduler, run: airflow scheduler"
    return 0
}

verify_airflow() {
    log_info "Verifying Apache Airflow installation..."

    if ! command_exists airflow; then
        log_error "Apache Airflow is not installed"
        return 1
    fi

    local airflow_version
    airflow_version=$(airflow version 2>/dev/null | grep -oP '\d+\.\d+' | head -1)

    if version_ge "$airflow_version" "2.7"; then
        log_success "Apache Airflow $airflow_version is installed (>= 2.7)"
        return 0
    else
        log_error "Apache Airflow version $airflow_version is too old (requires >= 2.7)"
        return 1
    fi
}

# ============================================================================
# MAIN INSTALLATION ORCHESTRATION
# ============================================================================

install_external_tools() {
    local os_type
    os_type=$(detect_os)

    log_info "Detected OS: $os_type"

    if [[ "$os_type" == "unknown" ]]; then
        log_error "Unsupported operating system"
        return 1
    fi

    local failed_tools=()

    # Docker
    log_info "=== Installing Docker ==="
    case "$os_type" in
        macos)
            install_docker_macos || failed_tools+=("Docker")
            ;;
        debian)
            install_docker_debian || failed_tools+=("Docker")
            ;;
        rhel)
            install_docker_rhel || failed_tools+=("Docker")
            ;;
    esac
    verify_docker || failed_tools+=("Docker-verify")
    echo ""

    # Terraform
    log_info "=== Installing Terraform ==="
    case "$os_type" in
        macos)
            install_terraform_macos || failed_tools+=("Terraform")
            ;;
        debian)
            install_terraform_debian || failed_tools+=("Terraform")
            ;;
        rhel)
            install_terraform_rhel || failed_tools+=("Terraform")
            ;;
    esac
    verify_terraform || failed_tools+=("Terraform-verify")
    echo ""

    # Trivy
    log_info "=== Installing Trivy ==="
    case "$os_type" in
        macos)
            install_trivy_macos || failed_tools+=("Trivy")
            ;;
        debian)
            install_trivy_debian || failed_tools+=("Trivy")
            ;;
        rhel)
            install_trivy_rhel || failed_tools+=("Trivy")
            ;;
    esac
    verify_trivy || failed_tools+=("Trivy-verify")
    echo ""

    # Node.js
    log_info "=== Installing Node.js ==="
    case "$os_type" in
        macos)
            install_nodejs_macos || failed_tools+=("Node.js")
            ;;
        debian)
            install_nodejs_debian || failed_tools+=("Node.js")
            ;;
        rhel)
            install_nodejs_rhel || failed_tools+=("Node.js")
            ;;
    esac
    verify_nodejs || failed_tools+=("Node.js-verify")
    echo ""

    # Apache Airflow
    log_info "=== Installing Apache Airflow ==="
    install_airflow_common || failed_tools+=("Apache Airflow")
    verify_airflow || failed_tools+=("Apache Airflow-verify")
    echo ""

    # Summary
    log_info "=== Installation Summary ==="
    if [[ ${#failed_tools[@]} -eq 0 ]]; then
        log_success "All external tools installed successfully!"
        return 0
    else
        log_error "The following tools failed to install or verify:"
        for tool in "${failed_tools[@]}"; do
            log_error "  - $tool"
        done
        return 1
    fi
}

# ============================================================================
# ENTRY POINT
# ============================================================================

main() {
    log_info "Starting external tools installation for devCrew_s1..."
    echo ""

    install_external_tools
    local exit_code=$?

    echo ""
    if [[ $exit_code -eq 0 ]]; then
        log_success "External tools installation completed successfully!"
        log_info "You may need to restart your shell for all changes to take effect"
    else
        log_error "External tools installation completed with errors"
        log_info "Please review the error messages above and retry"
    fi

    return $exit_code
}

# Run main function if script is executed directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
