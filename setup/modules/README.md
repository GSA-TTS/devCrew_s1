# DevGru Setup Modules

This directory contains modular installation scripts for setting up development prerequisites.

## Available Modules

### databases.sh

Installs and configures database systems required by devCrew_s1 tools.

**Databases Supported:**
- **Redis 7.2+** (HIGH priority - used by 7 tools)
- **PostgreSQL 15.0+** (MEDIUM priority - used by 3 tools)
- **Neo4j 5.15+** (LOW priority - used by 1 tool)

**Supported Platforms:**
- macOS (via Homebrew)
- Ubuntu/Debian (via apt)
- RHEL/CentOS/Fedora (via dnf)

**Usage:**

```bash
# Source the module
source setup/modules/databases.sh

# Install individual databases
install_redis
install_postgresql
install_neo4j

# Or install all at once
install_all_databases
```

**Features:**
- Automatic OS detection
- Version verification (ensures minimum required versions)
- Service startup and configuration
- Connection testing
- Comprehensive error handling
- Color-coded output for easy reading

**Requirements:**
- **macOS:** Homebrew must be installed
- **Linux:** sudo privileges required
- **Neo4j:** Docker must be installed and running

**Neo4j Notes:**
- Neo4j is installed via Docker for maximum compatibility
- Default credentials: neo4j / password
- Browser UI: http://localhost:7474
- Bolt protocol: bolt://localhost:7687
- Change the default password after first login!

**Verification:**

Each installation function includes automatic verification:
- Redis: Tests connection with `redis-cli ping`
- PostgreSQL: Verifies version and connection with `psql`
- Neo4j: Checks Docker container status and version

**Error Handling:**

All functions include comprehensive error handling:
- Pre-installation checks (package managers, Docker daemon)
- Installation failure detection
- Service startup verification
- Connection testing
- Clear error messages with troubleshooting hints

## Development

### Adding New Modules

When creating new installation modules:

1. Follow the existing structure and naming conventions
2. Include OS detection and multi-platform support
3. Implement verification functions
4. Add comprehensive error handling
5. Make scripts executable: `chmod +x module.sh`
6. Test on all supported platforms
7. Update this README

### Module Template Structure

```bash
#!/usr/bin/env bash
set -euo pipefail

# Color codes and logging functions
# OS detection
# Command existence checks
# Version comparison helpers

# Installation functions per OS
install_tool_macos() { ... }
install_tool_debian() { ... }
install_tool_rhel() { ... }

# Verification function
verify_tool() { ... }

# Main installation function
install_tool() {
    local os_type=$(detect_os)
    case "$os_type" in
        macos) install_tool_macos ;;
        debian) install_tool_debian ;;
        rhel) install_tool_rhel ;;
        *) log_error "Unsupported OS" ;;
    esac
    verify_tool
}

# Help message when executed directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    cat <<EOF
Tool Installation Module
Usage: source module.sh && install_tool
EOF
fi
```

## Testing

To test a module without actually installing:

```bash
# Syntax check
bash -n databases.sh

# Verify functions are defined
source databases.sh
type -t install_redis
type -t install_postgresql
type -t install_neo4j

# Test OS detection
detect_os

# Show help
bash databases.sh
```

## Troubleshooting

### Common Issues

**macOS: Homebrew not found**
```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

**Linux: Insufficient privileges**
```bash
# Ensure your user has sudo access
sudo -v
```

**Neo4j: Docker not running**
```bash
# macOS
open -a Docker

# Linux
sudo systemctl start docker
```

**Neo4j: Port conflicts**
```bash
# Check if ports 7474 or 7687 are in use
lsof -i :7474
lsof -i :7687

# Stop conflicting services or remove existing container
docker rm -f neo4j
```

## License

Part of devCrew_s1 project. See main repository LICENSE for details.
