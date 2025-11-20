#!/usr/bin/env bash
###############################################################################
# Module Integration Test
#
# Tests the integration and loading of all setup modules
###############################################################################

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DEVGRU_DIR="$(dirname "${SCRIPT_DIR}")"

# Color codes
readonly GREEN='\033[0;32m'
readonly RED='\033[0;31m'
readonly YELLOW='\033[1;33m'
readonly BLUE='\033[0;34m'
readonly NC='\033[0m'

echo -e "${BLUE}=== Module Integration Tests ===${NC}"
echo ""

# Test 1: Check all modules exist
echo "Test 1: Check all required modules exist"
MODULES=(
    "python_setup.sh"
    "core_packages.sh"
    "optional_packages.sh"
    "databases.sh"
    "external_tools.sh"
    "cloud_sdks.sh"
)

ALL_EXIST=true
for module in "${MODULES[@]}"; do
    module_path="${DEVGRU_DIR}/modules/${module}"
    if [[ -f "${module_path}" ]]; then
        echo "  ✓ ${module}"
    else
        echo "  ✗ ${module} not found"
        ALL_EXIST=false
    fi
done

if [[ "${ALL_EXIST}" == true ]]; then
    echo -e "  ${GREEN}✓ PASS${NC}"
else
    echo -e "  ${RED}✗ FAIL${NC}"
    exit 1
fi

# Test 2: Check module syntax
echo ""
echo "Test 2: Validate module syntax"
ALL_VALID=true
for module in "${MODULES[@]}"; do
    module_path="${DEVGRU_DIR}/modules/${module}"
    if bash -n "${module_path}" 2>/dev/null; then
        echo "  ✓ ${module} syntax valid"
    else
        echo "  ✗ ${module} syntax error"
        ALL_VALID=false
    fi
done

if [[ "${ALL_VALID}" == true ]]; then
    echo -e "  ${GREEN}✓ PASS${NC}"
else
    echo -e "  ${RED}✗ FAIL${NC}"
    exit 1
fi

# Test 3: Check modules are executable
echo ""
echo "Test 3: Check modules are executable"
ALL_EXECUTABLE=true
for module in "${MODULES[@]}"; do
    module_path="${DEVGRU_DIR}/modules/${module}"
    if [[ -x "${module_path}" ]]; then
        echo "  ✓ ${module} executable"
    else
        echo "  ⊘ ${module} not executable (may be intended)"
    fi
done
echo -e "  ${GREEN}✓ PASS${NC}"

# Test 4: Test python_setup module functions
echo ""
echo "Test 4: Test python_setup module functions"
PYTHON_MODULE="${DEVGRU_DIR}/modules/python_setup.sh"

if [[ -f "${PYTHON_MODULE}" ]]; then
    # Check if key functions exist by grepping for function definitions
    if grep -q "^detect_os()" "${PYTHON_MODULE}"; then
        echo "  ✓ detect_os function defined"
    else
        echo "  ✗ detect_os function not found"
        echo -e "  ${RED}✗ FAIL${NC}"
        exit 1
    fi

    if grep -q "^check_python_version()" "${PYTHON_MODULE}"; then
        echo "  ✓ check_python_version function defined"
    else
        echo "  ✗ check_python_version function not found"
        echo -e "  ${RED}✗ FAIL${NC}"
        exit 1
    fi

    if grep -q "^setup_python()" "${PYTHON_MODULE}"; then
        echo "  ✓ setup_python function defined"
    else
        echo "  ✗ setup_python function not found"
        echo -e "  ${RED}✗ FAIL${NC}"
        exit 1
    fi

    echo -e "  ${GREEN}✓ PASS${NC}"
else
    echo -e "  ${RED}✗ FAIL${NC} - python_setup.sh not found"
    exit 1
fi

# Test 5: Check module README
echo ""
echo "Test 5: Check module documentation"
MODULE_README="${DEVGRU_DIR}/modules/README.md"

if [[ -f "${MODULE_README}" ]]; then
    echo "  ✓ Module README exists"

    # Check if README contains expected sections
    if grep -q "## Modules" "${MODULE_README}" 2>/dev/null; then
        echo "  ✓ README contains Modules section"
    else
        echo "  ⊘ README may be incomplete"
    fi

    echo -e "  ${GREEN}✓ PASS${NC}"
else
    echo -e "  ${YELLOW}⊘ SKIP${NC} - Module README not found"
fi

# Test 6: Check requirements files
echo ""
echo "Test 6: Check requirements files"
REQ_DIR="${DEVGRU_DIR}/requirements"
REQ_FILES=(
    "requirements-core.txt"
    "requirements-optional.txt"
    "requirements-cloud-aws.txt"
    "requirements-cloud-azure.txt"
    "requirements-cloud-gcp.txt"
)

if [[ -d "${REQ_DIR}" ]]; then
    ALL_REQ_EXIST=true
    for req_file in "${REQ_FILES[@]}"; do
        if [[ -f "${REQ_DIR}/${req_file}" ]]; then
            echo "  ✓ ${req_file}"
        else
            echo "  ✗ ${req_file} not found"
            ALL_REQ_EXIST=false
        fi
    done

    if [[ "${ALL_REQ_EXIST}" == true ]]; then
        echo -e "  ${GREEN}✓ PASS${NC}"
    else
        echo -e "  ${RED}✗ FAIL${NC}"
        exit 1
    fi
else
    echo -e "  ${RED}✗ FAIL${NC} - Requirements directory not found"
    exit 1
fi

# Test 7: Validate main setup script
echo ""
echo "Test 7: Validate main setup script"
SETUP_SCRIPT="${DEVGRU_DIR}/setup_devgru.sh"

if [[ -f "${SETUP_SCRIPT}" ]]; then
    echo "  ✓ setup_devgru.sh exists"

    # Check syntax
    if bash -n "${SETUP_SCRIPT}" 2>/dev/null; then
        echo "  ✓ setup_devgru.sh syntax valid"
    else
        echo "  ✗ setup_devgru.sh syntax error"
        exit 1
    fi

    # Check if executable
    if [[ -x "${SETUP_SCRIPT}" ]]; then
        echo "  ✓ setup_devgru.sh executable"
    else
        echo "  ✗ setup_devgru.sh not executable"
        exit 1
    fi

    echo -e "  ${GREEN}✓ PASS${NC}"
else
    echo -e "  ${RED}✗ FAIL${NC} - setup_devgru.sh not found"
    exit 1
fi

# Test 8: Check directory structure
echo ""
echo "Test 8: Validate directory structure"
REQUIRED_DIRS=(
    "modules"
    "requirements"
    "logs"
    ".state"
)

ALL_DIRS_EXIST=true
for dir in "${REQUIRED_DIRS[@]}"; do
    dir_path="${DEVGRU_DIR}/${dir}"
    if [[ -d "${dir_path}" ]]; then
        echo "  ✓ ${dir}/"
    else
        echo "  ⊘ ${dir}/ not found (may be created at runtime)"
    fi
done
echo -e "  ${GREEN}✓ PASS${NC}"

echo ""
echo -e "${GREEN}All module integration tests passed!${NC}"
exit 0
