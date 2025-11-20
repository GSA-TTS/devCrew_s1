#!/usr/bin/env bash
###############################################################################
# Test Runner Script
#
# Convenience script to run all tests or specific test modules
###############################################################################

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Color codes
readonly GREEN='\033[0;32m'
readonly RED='\033[0;31m'
readonly YELLOW='\033[1;33m'
readonly BLUE='\033[0;34m'
readonly CYAN='\033[0;36m'
readonly WHITE='\033[1;37m'
readonly NC='\033[0m'

# Test tracking
declare -a PASSED_MODULES=()
declare -a FAILED_MODULES=()

# Configuration
VERBOSE=false

###############################################################################
# Functions
###############################################################################

show_help() {
    cat <<EOF
Test Runner for DevGRU Setup

Usage: ./run_tests.sh [OPTIONS] [MODULE]

Options:
  --verbose, -v        Enable verbose output
  --help, -h          Show this help message

Modules:
  all                 Run all test modules (default)
  os                  Run OS detection tests
  python              Run Python verification tests
  modules             Run module integration tests
  suite               Run full test suite

Examples:
  # Run all tests
  ./run_tests.sh

  # Run specific test module
  ./run_tests.sh python

  # Run with verbose output
  ./run_tests.sh --verbose

EOF
}

run_test_module() {
    local module_name="$1"
    local module_script="$2"

    echo ""
    echo -e "${CYAN}========================================${NC}"
    echo -e "${CYAN}Running: ${module_name}${NC}"
    echo -e "${CYAN}========================================${NC}"

    if [[ -f "${module_script}" ]]; then
        if bash "${module_script}"; then
            PASSED_MODULES+=("${module_name}")
            return 0
        else
            FAILED_MODULES+=("${module_name}")
            return 1
        fi
    else
        echo -e "${RED}✗ Test module not found: ${module_script}${NC}"
        FAILED_MODULES+=("${module_name}")
        return 1
    fi
}

run_all_tests() {
    echo -e "${BLUE}==================================================${NC}"
    echo -e "${BLUE}  DevGRU Setup - Running All Test Modules${NC}"
    echo -e "${BLUE}==================================================${NC}"

    # Run individual test modules
    run_test_module "OS Detection Tests" "${SCRIPT_DIR}/test_os_detection.sh" || true
    run_test_module "Python Verification Tests" "${SCRIPT_DIR}/test_python_verification.sh" || true
    run_test_module "Module Integration Tests" "${SCRIPT_DIR}/test_module_integration.sh" || true

    # Run comprehensive test suite
    run_test_module "Full Test Suite" "${SCRIPT_DIR}/test_setup.sh" || true
}

print_summary() {
    echo ""
    echo -e "${CYAN}========================================${NC}"
    echo -e "${CYAN}Test Summary${NC}"
    echo -e "${CYAN}========================================${NC}"

    local total=$((${#PASSED_MODULES[@]} + ${#FAILED_MODULES[@]}))
    local passed=${#PASSED_MODULES[@]}
    local failed=${#FAILED_MODULES[@]}

    echo -e "${WHITE}Total Modules: ${total}${NC}"
    echo -e "${GREEN}Passed:        ${passed}${NC}"
    echo -e "${RED}Failed:        ${failed}${NC}"
    echo ""

    if [[ ${passed} -gt 0 ]]; then
        echo -e "${GREEN}Passed Modules:${NC}"
        for module in "${PASSED_MODULES[@]}"; do
            echo -e "  ${GREEN}✓${NC} ${module}"
        done
        echo ""
    fi

    if [[ ${failed} -gt 0 ]]; then
        echo -e "${RED}Failed Modules:${NC}"
        for module in "${FAILED_MODULES[@]}"; do
            echo -e "  ${RED}✗${NC} ${module}"
        done
        echo ""
    fi

    # Calculate success rate
    local success_rate=0
    if [[ ${total} -gt 0 ]]; then
        success_rate=$((passed * 100 / total))
    fi

    echo -e "Success Rate: ${success_rate}%"
    echo ""

    if [[ ${failed} -eq 0 ]]; then
        echo -e "${GREEN}All tests passed!${NC}"
        return 0
    else
        echo -e "${RED}Some tests failed.${NC}"
        return 1
    fi
}

###############################################################################
# Main
###############################################################################

main() {
    local test_module="all"

    # Parse arguments
    while [[ $# -gt 0 ]]; do
        case "$1" in
            --verbose|-v)
                VERBOSE=true
                shift
                ;;
            --help|-h)
                show_help
                exit 0
                ;;
            -*)
                echo "Unknown option: $1"
                show_help
                exit 1
                ;;
            *)
                test_module="$1"
                shift
                ;;
        esac
    done

    # Run tests
    case "${test_module}" in
        all)
            run_all_tests
            ;;
        os)
            run_test_module "OS Detection Tests" "${SCRIPT_DIR}/test_os_detection.sh"
            ;;
        python)
            run_test_module "Python Verification Tests" "${SCRIPT_DIR}/test_python_verification.sh"
            ;;
        modules)
            run_test_module "Module Integration Tests" "${SCRIPT_DIR}/test_module_integration.sh"
            ;;
        suite)
            run_test_module "Full Test Suite" "${SCRIPT_DIR}/test_setup.sh"
            ;;
        *)
            echo -e "${RED}Unknown test module: ${test_module}${NC}"
            show_help
            exit 1
            ;;
    esac

    # Print summary
    print_summary

    return $?
}

main "$@"
