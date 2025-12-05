#!/usr/bin/env bash
###############################################################################
# Python Verification Test Module
#
# Tests Python installation and version verification
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
readonly YELLOW='\033[1;33m'
readonly BLUE='\033[0;34m'
readonly NC='\033[0m'

echo -e "${BLUE}=== Python Verification Tests ===${NC}"
echo ""

# Test 1: Check Python availability
echo "Test 1: Check Python availability"
PYTHON_FOUND=false
for cmd in python3 python python3.11 python3.10; do
    if command -v "${cmd}" &>/dev/null; then
        PYTHON_CMD="${cmd}"
        PYTHON_FOUND=true
        echo "  Found: ${cmd}"
        break
    fi
done

if [[ "${PYTHON_FOUND}" == true ]]; then
    echo -e "  ${GREEN}✓ PASS${NC}"
else
    echo -e "  ${YELLOW}⊘ SKIP${NC} - Python not installed"
    exit 0
fi

# Test 2: Check Python version
echo ""
echo "Test 2: Check Python version"
PYTHON_VERSION=$("${PYTHON_CMD}" --version 2>&1 | cut -d' ' -f2)
echo "  Python version: ${PYTHON_VERSION}"

MAJOR=$(echo "${PYTHON_VERSION}" | cut -d'.' -f1)
MINOR=$(echo "${PYTHON_VERSION}" | cut -d'.' -f2)

if [[ "${MAJOR}" -eq 3 ]] && [[ "${MINOR}" -ge 10 ]]; then
    echo -e "  ${GREEN}✓ PASS${NC} - Version meets minimum requirement (3.10+)"
else
    echo -e "  ${RED}✗ FAIL${NC} - Version does not meet minimum requirement (3.10+)"
    exit 1
fi

# Test 3: Check pip availability
echo ""
echo "Test 3: Check pip availability"
if "${PYTHON_CMD}" -m pip --version &>/dev/null; then
    PIP_VERSION=$("${PYTHON_CMD}" -m pip --version | cut -d' ' -f2)
    echo "  pip version: ${PIP_VERSION}"
    echo -e "  ${GREEN}✓ PASS${NC}"
else
    echo -e "  ${RED}✗ FAIL${NC} - pip not available"
    exit 1
fi

# Test 4: Check venv module
echo ""
echo "Test 4: Check venv module availability"
if "${PYTHON_CMD}" -m venv --help &>/dev/null; then
    echo "  venv module is available"
    echo -e "  ${GREEN}✓ PASS${NC}"
else
    echo -e "  ${RED}✗ FAIL${NC} - venv module not available"
    exit 1
fi

# Test 5: Test virtual environment creation
echo ""
echo "Test 5: Test virtual environment creation"
TEST_VENV="/tmp/test_venv_$$"

if "${PYTHON_CMD}" -m venv "${TEST_VENV}" 2>/dev/null; then
    echo "  Virtual environment created successfully"

    # Check activation script
    if [[ -f "${TEST_VENV}/bin/activate" ]] || [[ -f "${TEST_VENV}/Scripts/activate" ]]; then
        echo "  Activation script found"
        echo -e "  ${GREEN}✓ PASS${NC}"

        # Clean up
        rm -rf "${TEST_VENV}"
    else
        echo -e "  ${RED}✗ FAIL${NC} - Activation script not found"
        rm -rf "${TEST_VENV}"
        exit 1
    fi
else
    echo -e "  ${RED}✗ FAIL${NC} - Failed to create virtual environment"
    exit 1
fi

# Test 6: Check Python development headers
echo ""
echo "Test 6: Check Python development headers"
if "${PYTHON_CMD}" -c "import sysconfig; print(sysconfig.get_path('include'))" &>/dev/null; then
    INCLUDE_DIR=$("${PYTHON_CMD}" -c "import sysconfig; print(sysconfig.get_path('include'))")

    if [[ -d "${INCLUDE_DIR}" ]]; then
        echo "  Python headers found at: ${INCLUDE_DIR}"
        echo -e "  ${GREEN}✓ PASS${NC}"
    else
        echo -e "  ${YELLOW}⊘ SKIP${NC} - Python headers not found (may need python3-dev package)"
    fi
else
    echo -e "  ${YELLOW}⊘ SKIP${NC} - Cannot determine include path"
fi

# Test 7: Check essential Python modules
echo ""
echo "Test 7: Check essential Python modules"
ESSENTIAL_MODULES=("sys" "os" "json" "re" "subprocess")
ALL_FOUND=true

for module in "${ESSENTIAL_MODULES[@]}"; do
    if "${PYTHON_CMD}" -c "import ${module}" 2>/dev/null; then
        echo "  ✓ ${module}"
    else
        echo "  ✗ ${module} not found"
        ALL_FOUND=false
    fi
done

if [[ "${ALL_FOUND}" == true ]]; then
    echo -e "  ${GREEN}✓ PASS${NC}"
else
    echo -e "  ${RED}✗ FAIL${NC} - Some essential modules are missing"
    exit 1
fi

# Test 8: Test pip install functionality
echo ""
echo "Test 8: Test pip install functionality (in venv)"
TEST_VENV="/tmp/test_venv_pip_$$"

if "${PYTHON_CMD}" -m venv "${TEST_VENV}" 2>/dev/null; then
    # Activate venv and try to install a small package
    if [[ -f "${TEST_VENV}/bin/activate" ]]; then
        (
            # shellcheck disable=SC1091
            source "${TEST_VENV}/bin/activate"

            if pip install --quiet --no-cache-dir wheel 2>/dev/null; then
                echo "  Successfully installed test package"
                exit 0
            else
                echo "  Failed to install test package"
                exit 1
            fi
        )

        exit_code=$?
        rm -rf "${TEST_VENV}"

        if [[ ${exit_code} -eq 0 ]]; then
            echo -e "  ${GREEN}✓ PASS${NC}"
        else
            echo -e "  ${RED}✗ FAIL${NC}"
            exit 1
        fi
    else
        echo -e "  ${YELLOW}⊘ SKIP${NC} - Cannot activate venv"
        rm -rf "${TEST_VENV}"
    fi
else
    echo -e "  ${RED}✗ FAIL${NC} - Cannot create test venv"
    exit 1
fi

echo ""
echo -e "${GREEN}All Python verification tests passed!${NC}"
exit 0
