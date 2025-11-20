#!/usr/bin/env bash
#
# Database Installation Module
# Supports: Redis 7.2+, PostgreSQL 15.0+, Neo4j 5.15+
# Platforms: macOS (Homebrew), Ubuntu/Debian (apt), RHEL/CentOS (dnf)
#
# Usage:
#   source databases.sh
#   install_redis
#   install_postgresql
#   install_neo4j
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

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $*"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $*"
}

# Detect OS
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

# Version comparison helper
version_ge() {
    # Returns 0 if $1 >= $2
    printf '%s\n%s\n' "$2" "$1" | sort -V -C
}

#############################################
# Redis Installation Functions
#############################################

install_redis_macos() {
    log_info "Installing Redis on macOS via Homebrew..."

    if ! command_exists brew; then
        log_error "Homebrew not found. Please install Homebrew first."
        return 1
    fi

    if brew list redis &>/dev/null; then
        log_warning "Redis is already installed via Homebrew"
        local installed_version
        installed_version=$(redis-server --version | grep -oE '[0-9]+\.[0-9]+\.[0-9]+' | head -1)
        log_info "Installed version: $installed_version"
    else
        brew install redis || {
            log_error "Failed to install Redis"
            return 1
        }
    fi

    # Start Redis service
    log_info "Starting Redis service..."
    brew services start redis || {
        log_warning "Failed to start Redis service via brew services, trying manual start..."
        redis-server --daemonize yes
    }

    return 0
}

install_redis_debian() {
    log_info "Installing Redis on Ubuntu/Debian..."

    # Update package list
    sudo apt-get update || {
        log_error "Failed to update package list"
        return 1
    }

    # Install Redis
    sudo apt-get install -y redis-server || {
        log_error "Failed to install Redis"
        return 1
    }

    # Configure Redis to start on boot
    sudo systemctl enable redis-server || log_warning "Could not enable Redis service"

    # Start Redis
    sudo systemctl start redis-server || {
        log_error "Failed to start Redis service"
        return 1
    }

    return 0
}

install_redis_rhel() {
    log_info "Installing Redis on RHEL/CentOS..."

    # Enable EPEL repository if not already enabled
    if ! sudo dnf repolist | grep -q epel; then
        log_info "Enabling EPEL repository..."
        sudo dnf install -y epel-release || log_warning "Could not enable EPEL repository"
    fi

    # Install Redis
    sudo dnf install -y redis || {
        log_error "Failed to install Redis"
        return 1
    }

    # Configure Redis to start on boot
    sudo systemctl enable redis || log_warning "Could not enable Redis service"

    # Start Redis
    sudo systemctl start redis || {
        log_error "Failed to start Redis service"
        return 1
    }

    return 0
}

verify_redis() {
    log_info "Verifying Redis installation..."

    # Check if redis-cli exists
    if ! command_exists redis-cli; then
        log_error "redis-cli not found in PATH"
        return 1
    fi

    # Check Redis version
    local version
    version=$(redis-server --version | grep -oE '[0-9]+\.[0-9]+\.[0-9]+' | head -1)
    log_info "Redis version: $version"

    if ! version_ge "$version" "7.2.0"; then
        log_warning "Redis version $version is below recommended 7.2+"
    fi

    # Test Redis connection
    sleep 2  # Give Redis a moment to start
    if redis-cli ping | grep -q PONG; then
        log_success "Redis is running and responding"
        return 0
    else
        log_error "Redis is not responding to PING"
        return 1
    fi
}

install_redis() {
    log_info "Starting Redis installation (required version: 7.2+)..."

    local os_type
    os_type=$(detect_os)

    case "$os_type" in
        macos)
            install_redis_macos || return 1
            ;;
        debian)
            install_redis_debian || return 1
            ;;
        rhel)
            install_redis_rhel || return 1
            ;;
        *)
            log_error "Unsupported OS: $os_type"
            return 1
            ;;
    esac

    verify_redis || return 1

    log_success "Redis installation completed successfully"
    return 0
}

#############################################
# PostgreSQL Installation Functions
#############################################

install_postgresql_macos() {
    log_info "Installing PostgreSQL on macOS via Homebrew..."

    if ! command_exists brew; then
        log_error "Homebrew not found. Please install Homebrew first."
        return 1
    fi

    if brew list postgresql@15 &>/dev/null; then
        log_warning "PostgreSQL 15 is already installed via Homebrew"
    elif brew list postgresql &>/dev/null; then
        log_warning "PostgreSQL is already installed via Homebrew"
    else
        brew install postgresql@15 || {
            log_error "Failed to install PostgreSQL"
            return 1
        }
    fi

    # Start PostgreSQL service
    log_info "Starting PostgreSQL service..."
    if brew list postgresql@15 &>/dev/null; then
        brew services start postgresql@15 || log_warning "Failed to start PostgreSQL@15 service"
    else
        brew services start postgresql || log_warning "Failed to start PostgreSQL service"
    fi

    # Wait for PostgreSQL to be ready
    sleep 3

    return 0
}

install_postgresql_debian() {
    log_info "Installing PostgreSQL on Ubuntu/Debian..."

    # Update package list
    sudo apt-get update || {
        log_error "Failed to update package list"
        return 1
    }

    # Install PostgreSQL
    sudo apt-get install -y postgresql postgresql-contrib || {
        log_error "Failed to install PostgreSQL"
        return 1
    }

    # PostgreSQL should auto-start, but ensure it's enabled
    sudo systemctl enable postgresql || log_warning "Could not enable PostgreSQL service"
    sudo systemctl start postgresql || log_warning "PostgreSQL may already be running"

    # Wait for PostgreSQL to be ready
    sleep 3

    return 0
}

install_postgresql_rhel() {
    log_info "Installing PostgreSQL on RHEL/CentOS..."

    # Install PostgreSQL
    sudo dnf install -y postgresql-server postgresql-contrib || {
        log_error "Failed to install PostgreSQL"
        return 1
    }

    # Initialize database (first time only)
    if [[ ! -d /var/lib/pgsql/data/base ]]; then
        log_info "Initializing PostgreSQL database..."
        sudo postgresql-setup --initdb || {
            log_error "Failed to initialize PostgreSQL database"
            return 1
        }
    fi

    # Enable and start PostgreSQL
    sudo systemctl enable postgresql || log_warning "Could not enable PostgreSQL service"
    sudo systemctl start postgresql || {
        log_error "Failed to start PostgreSQL service"
        return 1
    }

    # Wait for PostgreSQL to be ready
    sleep 3

    return 0
}

verify_postgresql() {
    log_info "Verifying PostgreSQL installation..."

    # Check if psql exists
    if ! command_exists psql; then
        log_error "psql not found in PATH"
        return 1
    fi

    # Check PostgreSQL version
    local version
    version=$(psql --version | grep -oE '[0-9]+\.[0-9]+' | head -1)
    log_info "PostgreSQL version: $version"

    if ! version_ge "$version" "15.0"; then
        log_warning "PostgreSQL version $version is below recommended 15.0+"
    fi

    # Test PostgreSQL connection (OS-specific)
    local os_type
    os_type=$(detect_os)

    case "$os_type" in
        macos)
            if psql -U "$USER" -d postgres -c "SELECT version();" &>/dev/null; then
                log_success "PostgreSQL is running and responding"
                return 0
            else
                log_warning "PostgreSQL installed but connection test failed (this may be normal)"
                log_info "You may need to create a database user: createdb $USER"
                return 0
            fi
            ;;
        debian|rhel)
            if sudo -u postgres psql -c "SELECT version();" &>/dev/null; then
                log_success "PostgreSQL is running and responding"
                return 0
            else
                log_error "PostgreSQL is not responding"
                return 1
            fi
            ;;
    esac

    return 0
}

install_postgresql() {
    log_info "Starting PostgreSQL installation (required version: 15.0+)..."

    local os_type
    os_type=$(detect_os)

    case "$os_type" in
        macos)
            install_postgresql_macos || return 1
            ;;
        debian)
            install_postgresql_debian || return 1
            ;;
        rhel)
            install_postgresql_rhel || return 1
            ;;
        *)
            log_error "Unsupported OS: $os_type"
            return 1
            ;;
    esac

    verify_postgresql || return 1

    log_success "PostgreSQL installation completed successfully"
    log_info "Default PostgreSQL port: 5432"

    local os_type
    os_type=$(detect_os)
    if [[ "$os_type" == "macos" ]]; then
        log_info "To create a database: createdb <dbname>"
        log_info "To connect: psql <dbname>"
    else
        log_info "To create a user: sudo -u postgres createuser <username>"
        log_info "To create a database: sudo -u postgres createdb <dbname>"
        log_info "To connect: sudo -u postgres psql"
    fi

    return 0
}

#############################################
# Neo4j Installation Functions (Docker-based)
#############################################

install_neo4j_docker() {
    log_info "Installing Neo4j via Docker (required version: 5.15+)..."

    # Check if Docker is installed
    if ! command_exists docker; then
        log_error "Docker not found. Please install Docker first."
        log_info "Visit: https://docs.docker.com/get-docker/"
        return 1
    fi

    # Check if Docker daemon is running
    if ! docker info &>/dev/null; then
        log_error "Docker daemon is not running. Please start Docker."
        return 1
    fi

    # Check if Neo4j container already exists
    if docker ps -a --format '{{.Names}}' | grep -q "^neo4j$"; then
        log_warning "Neo4j container already exists"

        # Check if it's running
        if docker ps --format '{{.Names}}' | grep -q "^neo4j$"; then
            log_info "Neo4j container is already running"
        else
            log_info "Starting existing Neo4j container..."
            docker start neo4j || {
                log_error "Failed to start Neo4j container"
                return 1
            }
        fi
    else
        log_info "Pulling Neo4j 5.15 Docker image..."
        docker pull neo4j:5.15 || {
            log_error "Failed to pull Neo4j Docker image"
            return 1
        }

        log_info "Creating and starting Neo4j container..."
        docker run -d \
            --name neo4j \
            -p 7474:7474 \
            -p 7687:7687 \
            -e NEO4J_AUTH=neo4j/password \
            -v neo4j_data:/data \
            -v neo4j_logs:/logs \
            neo4j:5.15 || {
            log_error "Failed to create Neo4j container"
            return 1
        }
    fi

    # Wait for Neo4j to be ready
    log_info "Waiting for Neo4j to start (this may take 30-60 seconds)..."
    local max_attempts=30
    local attempt=0

    while [[ $attempt -lt $max_attempts ]]; do
        if docker logs neo4j 2>&1 | grep -q "Started."; then
            log_success "Neo4j is ready"
            break
        fi
        sleep 2
        ((attempt++))
    done

    if [[ $attempt -eq $max_attempts ]]; then
        log_warning "Neo4j may still be starting. Check with: docker logs neo4j"
    fi

    return 0
}

verify_neo4j() {
    log_info "Verifying Neo4j installation..."

    # Check if Neo4j container is running
    if ! docker ps --format '{{.Names}}' | grep -q "^neo4j$"; then
        log_error "Neo4j container is not running"
        return 1
    fi

    # Get Neo4j version
    local version
    version=$(docker exec neo4j neo4j --version 2>/dev/null | grep -oE '[0-9]+\.[0-9]+\.[0-9]+' | head -1)
    log_info "Neo4j version: $version"

    if ! version_ge "$version" "5.15.0"; then
        log_warning "Neo4j version $version is below recommended 5.15+"
    fi

    log_success "Neo4j is running in Docker container"
    return 0
}

install_neo4j() {
    log_info "Starting Neo4j installation (required version: 5.15+)..."
    log_info "Neo4j will be installed via Docker for maximum compatibility"

    install_neo4j_docker || return 1

    verify_neo4j || return 1

    log_success "Neo4j installation completed successfully"
    echo ""
    log_info "Neo4j Access Information:"
    log_info "  Browser UI: http://localhost:7474"
    log_info "  Bolt Protocol: bolt://localhost:7687"
    log_info "  Default credentials: neo4j / password"
    log_info ""
    log_info "Neo4j Container Management:"
    log_info "  Stop:    docker stop neo4j"
    log_info "  Start:   docker start neo4j"
    log_info "  Restart: docker restart neo4j"
    log_info "  Logs:    docker logs neo4j"
    log_info "  Remove:  docker rm -f neo4j (WARNING: removes container only)"
    log_info ""
    log_warning "IMPORTANT: Change the default password after first login!"

    return 0
}

#############################################
# Main Installation Function
#############################################

install_all_databases() {
    log_info "Installing all databases..."
    echo ""

    local failed=0

    # Install Redis (HIGH priority)
    log_info "=== Installing Redis (HIGH priority) ==="
    if ! install_redis; then
        log_error "Redis installation failed"
        ((failed++))
    fi
    echo ""

    # Install PostgreSQL (MEDIUM priority)
    log_info "=== Installing PostgreSQL (MEDIUM priority) ==="
    if ! install_postgresql; then
        log_error "PostgreSQL installation failed"
        ((failed++))
    fi
    echo ""

    # Install Neo4j (LOW priority)
    log_info "=== Installing Neo4j (LOW priority) ==="
    if ! install_neo4j; then
        log_error "Neo4j installation failed"
        ((failed++))
    fi
    echo ""

    if [[ $failed -eq 0 ]]; then
        log_success "All databases installed successfully!"
        return 0
    else
        log_error "$failed database(s) failed to install"
        return 1
    fi
}

# If script is executed directly (not sourced), show usage
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    cat <<EOF
Database Installation Module

Available functions:
  install_redis          - Install Redis 7.2+ (HIGH priority - 7 tools)
  install_postgresql     - Install PostgreSQL 15.0+ (MEDIUM priority - 3 tools)
  install_neo4j          - Install Neo4j 5.15+ via Docker (LOW priority - 1 tool)
  install_all_databases  - Install all databases

Supported platforms:
  - macOS (via Homebrew)
  - Ubuntu/Debian (via apt)
  - RHEL/CentOS/Fedora (via dnf)

Usage:
  source databases.sh
  install_redis
  install_postgresql
  install_neo4j

  # Or install all at once:
  install_all_databases

Requirements:
  - macOS: Homebrew must be installed
  - Linux: sudo privileges required
  - Neo4j: Docker must be installed and running

EOF
fi
