#!/usr/bin/env bash
###############################################################################
# OS Detection Test Module
#
# Tests the OS detection functionality of the DevGRU setup script
###############################################################################

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Source test helpers
if [[ -f "${SCRIPT_DIR}/utils/test_helpers.sh" ]]; then
    # shellcheck disable=SC1091
    source "${SCRIPT_DIR}/utils/test_helpers.sh"
fi

# Color codes
readonly GREEN='\033[0;32m'
readonly RED='\033[0;31m'
readonly BLUE='\033[0;34m'
readonly NC='\033[0m'

echo -e "${BLUE}=== OS Detection Tests ===${NC}"
echo ""

# Test 1: Detect current OS
echo "Test 1: Detect current OS type"
OS_TYPE=$(get_os_type 2>/dev/null || echo "unknown")
echo "  Detected OS: ${OS_TYPE}"

if [[ "${OS_TYPE}" != "unknown" ]]; then
    echo -e "  ${GREEN}✓ PASS${NC}"
else
    echo -e "  ${RED}✗ FAIL${NC}"
    exit 1
fi

# Test 2: Detect architecture
echo ""
echo "Test 2: Detect system architecture"
ARCH=$(uname -m)
echo "  Architecture: ${ARCH}"

if [[ "${ARCH}" =~ ^(x86_64|amd64|arm64|aarch64)$ ]]; then
    echo -e "  ${GREEN}✓ PASS${NC}"
else
    echo -e "  ${RED}✗ FAIL${NC} - Unsupported architecture"
    exit 1
fi

# Test 3: Detect package manager
echo ""
echo "Test 3: Detect package manager"
PKG_MGR=$(get_package_manager 2>/dev/null || echo "unknown")
echo "  Package Manager: ${PKG_MGR}"

if [[ "${PKG_MGR}" != "unknown" ]]; then
    echo -e "  ${GREEN}✓ PASS${NC}"
else
    echo -e "  ${RED}✗ FAIL${NC}"
    exit 1
fi

# Test 4: Check OS-specific tools
echo ""
echo "Test 4: Verify OS-specific tools"
case "${OS_TYPE}" in
    macos)
        if command -v sw_vers &>/dev/null; then
            echo "  macOS version: $(sw_vers -productVersion)"
            echo -e "  ${GREEN}✓ PASS${NC}"
        else
            echo -e "  ${RED}✗ FAIL${NC} - sw_vers not found"
            exit 1
        fi
        ;;
    debian|wsl2)
        if [[ -f /etc/os-release ]]; then
            . /etc/os-release
            echo "  Distribution: ${NAME} ${VERSION}"
            echo -e "  ${GREEN}✓ PASS${NC}"
        else
            echo -e "  ${RED}✗ FAIL${NC} - /etc/os-release not found"
            exit 1
        fi
        ;;
    rhel)
        if [[ -f /etc/os-release ]]; then
            . /etc/os-release
            echo "  Distribution: ${NAME} ${VERSION}"
            echo -e "  ${GREEN}✓ PASS${NC}"
        else
            echo -e "  ${RED}✗ FAIL${NC} - /etc/os-release not found"
            exit 1
        fi
        ;;
    *)
        echo -e "  ${RED}✗ FAIL${NC} - Unknown OS type"
        exit 1
        ;;
esac

# Test 5: Check WSL2 detection
echo ""
echo "Test 5: WSL2 detection (if applicable)"
if grep -qi microsoft /proc/version 2>/dev/null; then
    echo "  WSL2 environment detected"
    echo -e "  ${GREEN}✓ PASS${NC}"
else
    echo "  Not a WSL2 environment"
    echo -e "  ${GREEN}✓ PASS${NC}"
fi

echo ""
echo -e "${GREEN}All OS detection tests passed!${NC}"
exit 0
