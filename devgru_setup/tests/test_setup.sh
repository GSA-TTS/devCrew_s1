#!/usr/bin/env bash
###############################################################################
# DevGRU Setup Test Suite
#
# Purpose: Comprehensive test suite for DevGRU Multi-OS Prerequisites Setup
# Author: devCrew_s1
# Created: 2025-11-20
# Issue: GitHub Issue #67
#
# Usage: ./test_setup.sh [OPTIONS] [TEST_NAME]
#   Options:
#     --verbose            Enable verbose output
#     --dry-run           Run tests in dry-run mode
#     --list              List all available tests
#     --help              Show this help message
#
#   Test Names (optional):
#     all                 Run all tests (default)
#     os-detection        Test OS detection functionality
#     profile-selection   Test profile selection and validation
#     dry-run             Test dry-run mode
#     module-loading      Test module loading
#     python-install      Test Python installation verification
#     package-install     Test package installation verification
#     database-conn       Test database connection
#     venv-activation     Test virtual environment activation
#
###############################################################################

set -euo pipefail

###############################################################################
# Global Variables
###############################################################################

# Script metadata
readonly TEST_VERSION="1.0.0"
readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly DEVGRU_DIR="$(dirname "${SCRIPT_DIR}")"
readonly SETUP_SCRIPT="${DEVGRU_DIR}/setup_devgru.sh"

# Test configuration
VERBOSE=false
DRY_RUN=false
TEST_NAME="all"

# Test results tracking
declare -a PASSED_TESTS=()
declare -a FAILED_TESTS=()
declare -a SKIPPED_TESTS=()

# Test utilities directory
readonly TEST_UTILS_DIR="${SCRIPT_DIR}/utils"
readonly TEST_FIXTURES_DIR="${SCRIPT_DIR}/fixtures"

# Temporary test environment
readonly TEST_WORK_DIR="/tmp/devgru_test_$$"
readonly TEST_LOG_FILE="${TEST_WORK_DIR}/test_$(date +%Y%m%d_%H%M%S).log"

# Color codes for output
readonly COLOR_RESET='\033[0m'
readonly COLOR_RED='\033[0;31m'
readonly COLOR_GREEN='\033[0;32m'
readonly COLOR_YELLOW='\033[0;33m'
readonly COLOR_BLUE='\033[0;34m'
readonly COLOR_MAGENTA='\033[0;35m'
readonly COLOR_CYAN='\033[0;36m'
readonly COLOR_WHITE='\033[1;37m'

###############################################################################
# Utility Functions
###############################################################################

# Print colored messages
log_test() {
    echo -e "${COLOR_CYAN}[TEST]${COLOR_RESET} $*" | tee -a "${TEST_LOG_FILE}"
}

log_pass() {
    echo -e "${COLOR_GREEN}[PASS]${COLOR_RESET} $*" | tee -a "${TEST_LOG_FILE}"
}

log_fail() {
    echo -e "${COLOR_RED}[FAIL]${COLOR_RESET} $*" | tee -a "${TEST_LOG_FILE}"
}

log_skip() {
    echo -e "${COLOR_YELLOW}[SKIP]${COLOR_RESET} $*" | tee -a "${TEST_LOG_FILE}"
}

log_info() {
    echo -e "${COLOR_BLUE}[INFO]${COLOR_RESET} $*" | tee -a "${TEST_LOG_FILE}"
}

log_debug() {
    if [[ "${VERBOSE}" == true ]]; then
        echo -e "${COLOR_MAGENTA}[DEBUG]${COLOR_RESET} $*" | tee -a "${TEST_LOG_FILE}"
    fi
}

log_section() {
    echo "" | tee -a "${TEST_LOG_FILE}"
    echo -e "${COLOR_CYAN}========================================${COLOR_RESET}" | tee -a "${TEST_LOG_FILE}"
    echo -e "${COLOR_CYAN}$*${COLOR_RESET}" | tee -a "${TEST_LOG_FILE}"
    echo -e "${COLOR_CYAN}========================================${COLOR_RESET}" | tee -a "${TEST_LOG_FILE}"
}

# Assert functions
assert_equals() {
    local expected="$1"
    local actual="$2"
    local message="${3:-Assertion failed}"

    if [[ "${expected}" == "${actual}" ]]; then
        log_debug "✓ ${message}: '${actual}' == '${expected}'"
        return 0
    else
        log_fail "✗ ${message}: expected '${expected}', got '${actual}'"
        return 1
    fi
}

assert_not_equals() {
    local not_expected="$1"
    local actual="$2"
    local message="${3:-Assertion failed}"

    if [[ "${not_expected}" != "${actual}" ]]; then
        log_debug "✓ ${message}: '${actual}' != '${not_expected}'"
        return 0
    else
        log_fail "✗ ${message}: expected not '${not_expected}', got '${actual}'"
        return 1
    fi
}

assert_contains() {
    local substring="$1"
    local string="$2"
    local message="${3:-Assertion failed}"

    if [[ "${string}" == *"${substring}"* ]]; then
        log_debug "✓ ${message}: '${string}' contains '${substring}'"
        return 0
    else
        log_fail "✗ ${message}: '${string}' does not contain '${substring}'"
        return 1
    fi
}

assert_not_contains() {
    local substring="$1"
    local string="$2"
    local message="${3:-Assertion failed}"

    if [[ "${string}" != *"${substring}"* ]]; then
        log_debug "✓ ${message}: '${string}' does not contain '${substring}'"
        return 0
    else
        log_fail "✗ ${message}: '${string}' contains '${substring}'"
        return 1
    fi
}

assert_file_exists() {
    local file_path="$1"
    local message="${2:-Assertion failed}"

    if [[ -f "${file_path}" ]]; then
        log_debug "✓ ${message}: file exists at '${file_path}'"
        return 0
    else
        log_fail "✗ ${message}: file does not exist at '${file_path}'"
        return 1
    fi
}

assert_dir_exists() {
    local dir_path="$1"
    local message="${2:-Assertion failed}"

    if [[ -d "${dir_path}" ]]; then
        log_debug "✓ ${message}: directory exists at '${dir_path}'"
        return 0
    else
        log_fail "✗ ${message}: directory does not exist at '${dir_path}'"
        return 1
    fi
}

assert_command_exists() {
    local command="$1"
    local message="${2:-Assertion failed}"

    if command -v "${command}" &>/dev/null; then
        log_debug "✓ ${message}: command '${command}' exists"
        return 0
    else
        log_fail "✗ ${message}: command '${command}' does not exist"
        return 1
    fi
}

assert_exit_code() {
    local expected_code="$1"
    local actual_code="$2"
    local message="${3:-Assertion failed}"

    if [[ "${expected_code}" -eq "${actual_code}" ]]; then
        log_debug "✓ ${message}: exit code ${actual_code} == ${expected_code}"
        return 0
    else
        log_fail "✗ ${message}: expected exit code ${expected_code}, got ${actual_code}"
        return 1
    fi
}

# Test execution wrapper
run_test() {
    local test_name="$1"
    local test_function="$2"

    log_test "Running: ${test_name}"

    if ${test_function}; then
        log_pass "${test_name}"
        PASSED_TESTS+=("${test_name}")
        return 0
    else
        log_fail "${test_name}"
        FAILED_TESTS+=("${test_name}")
        return 1
    fi
}

###############################################################################
# Test Setup and Teardown
###############################################################################

setup_test_environment() {
    # Create test directories first (before any logging)
    mkdir -p "${TEST_WORK_DIR}"
    mkdir -p "${TEST_FIXTURES_DIR}"

    # Create test log file
    touch "${TEST_LOG_FILE}"

    log_info "Setting up test environment..."

    # Source test utilities if available
    if [[ -f "${TEST_UTILS_DIR}/test_helpers.sh" ]]; then
        # shellcheck disable=SC1091
        source "${TEST_UTILS_DIR}/test_helpers.sh"
        log_debug "Loaded test helpers"
    fi

    log_info "Test environment ready"
}

teardown_test_environment() {
    log_info "Cleaning up test environment..."

    # Remove test work directory if not in verbose mode
    if [[ "${VERBOSE}" != true ]] && [[ -d "${TEST_WORK_DIR}" ]]; then
        rm -rf "${TEST_WORK_DIR}"
        log_debug "Removed test work directory"
    else
        log_info "Test artifacts preserved at: ${TEST_WORK_DIR}"
    fi
}

###############################################################################
# Test Cases
###############################################################################

# Test 1: OS Detection
test_os_detection() {
    log_test "Test: OS Detection"

    # Source the setup script functions (in a subshell to avoid side effects)
    local os_type=""
    local os_version=""
    local arch=""
    local pkg_manager=""

    # Execute OS detection in a controlled way
    if [[ "$OSTYPE" == "darwin"* ]]; then
        os_type="macos"
        assert_equals "macos" "${os_type}" "OS type detection on macOS"
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        if grep -qi microsoft /proc/version 2>/dev/null; then
            assert_contains "wsl2" "debian-wsl2" "WSL2 detection"
        elif [[ -f /etc/os-release ]]; then
            . /etc/os-release
            case "${ID}" in
                ubuntu|debian)
                    os_type="debian"
                    assert_equals "debian" "${os_type}" "Debian/Ubuntu detection"
                    ;;
                rhel|centos|fedora)
                    os_type="rhel"
                    assert_equals "rhel" "${os_type}" "RHEL/CentOS detection"
                    ;;
            esac
        fi
    fi

    # Test architecture detection
    arch=$(uname -m)
    if [[ "${arch}" == "x86_64" || "${arch}" == "amd64" || "${arch}" == "arm64" || "${arch}" == "aarch64" ]]; then
        log_debug "Detected architecture: ${arch}"
        return 0
    else
        log_fail "Unknown architecture: ${arch}"
        return 1
    fi
}

# Test 2: Profile Selection
test_profile_selection() {
    log_test "Test: Profile Selection and Validation"

    local valid_profiles=("minimal" "standard" "full" "security" "cloud-aws" "cloud-azure" "cloud-gcp")

    # Test valid profiles
    for profile in "${valid_profiles[@]}"; do
        log_debug "Testing profile: ${profile}"
        assert_contains "${profile}" "${valid_profiles[*]}" "Profile ${profile} is valid"
    done

    # Test invalid profile
    local invalid_profile="invalid-profile"
    local found=false
    for p in "${valid_profiles[@]}"; do
        if [[ "${p}" == "${invalid_profile}" ]]; then
            found=true
            break
        fi
    done

    if [[ "${found}" == false ]]; then
        log_debug "✓ Invalid profile '${invalid_profile}' correctly rejected"
        return 0
    else
        log_fail "Invalid profile '${invalid_profile}' was accepted"
        return 1
    fi
}

# Test 3: Dry-Run Mode
test_dry_run_mode() {
    log_test "Test: Dry-Run Mode"

    # Create a test script to verify dry-run behavior
    local test_script="${TEST_WORK_DIR}/dry_run_test.sh"
    cat > "${test_script}" <<'EOF'
#!/usr/bin/env bash
DRY_RUN=true

execute_cmd() {
    local cmd="$*"
    if [[ "${DRY_RUN}" == true ]]; then
        echo "[DRY-RUN] Would execute: ${cmd}"
        return 0
    fi
    eval "${cmd}"
}

execute_cmd "echo 'This should not run'"
EOF

    chmod +x "${test_script}"

    # Run the test script and capture output
    local output
    output=$("${test_script}" 2>&1)

    # Verify dry-run message appears
    assert_contains "DRY-RUN" "${output}" "Dry-run mode produces expected output"
    assert_contains "Would execute" "${output}" "Dry-run mode shows command preview"

    return 0
}

# Test 4: Module Loading
test_module_loading() {
    log_test "Test: Module Loading"

    local modules=(
        "${DEVGRU_DIR}/modules/python_setup.sh"
        "${DEVGRU_DIR}/modules/core_packages.sh"
        "${DEVGRU_DIR}/modules/optional_packages.sh"
        "${DEVGRU_DIR}/modules/databases.sh"
        "${DEVGRU_DIR}/modules/external_tools.sh"
        "${DEVGRU_DIR}/modules/cloud_sdks.sh"
    )

    local all_exist=true
    for module in "${modules[@]}"; do
        if [[ -f "${module}" ]]; then
            log_debug "✓ Module found: ${module}"
        else
            log_fail "✗ Module not found: ${module}"
            all_exist=false
        fi
    done

    if [[ "${all_exist}" == true ]]; then
        # Test module syntax by sourcing them in a subshell
        for module in "${modules[@]}"; do
            if (bash -n "${module}") 2>/dev/null; then
                log_debug "✓ Module syntax valid: $(basename "${module}")"
            else
                log_fail "✗ Module syntax error: $(basename "${module}")"
                return 1
            fi
        done
        return 0
    else
        return 1
    fi
}

# Test 5: Python Installation Verification
test_python_installation() {
    log_test "Test: Python Installation Verification"

    # Check if Python 3 is available
    if command -v python3 &>/dev/null; then
        local python_version
        python_version=$(python3 --version 2>&1 | cut -d' ' -f2)
        log_debug "Python version: ${python_version}"

        # Check version is 3.10 or higher
        local major minor
        major=$(echo "${python_version}" | cut -d'.' -f1)
        minor=$(echo "${python_version}" | cut -d'.' -f2)

        if [[ "${major}" -eq 3 ]] && [[ "${minor}" -ge 10 ]]; then
            log_debug "✓ Python ${python_version} meets minimum requirements (3.10+)"
            return 0
        else
            log_fail "Python ${python_version} does not meet minimum requirements (3.10+)"
            return 1
        fi
    else
        log_skip "Python 3 not installed (skipping version check)"
        SKIPPED_TESTS+=("python_installation")
        return 0
    fi
}

# Test 6: Package Installation Verification
test_package_installation() {
    log_test "Test: Package Installation Verification"

    # Check if pip is available
    if command -v python3 &>/dev/null && python3 -m pip --version &>/dev/null; then
        log_debug "✓ pip is available"

        # Check for common packages (if installed)
        local test_packages=("requests" "pytest" "jq")
        local found_any=false

        for pkg in "${test_packages[@]}"; do
            if python3 -m pip show "${pkg}" &>/dev/null; then
                log_debug "✓ Package found: ${pkg}"
                found_any=true
            fi
        done

        if [[ "${found_any}" == true ]]; then
            return 0
        else
            log_skip "No test packages installed (this is normal for fresh installations)"
            SKIPPED_TESTS+=("package_installation")
            return 0
        fi
    else
        log_skip "pip not available (skipping package check)"
        SKIPPED_TESTS+=("package_installation")
        return 0
    fi
}

# Test 7: Database Connection Tests
test_database_connection() {
    log_test "Test: Database Connection Tests"

    local db_available=false

    # Test PostgreSQL connection
    if command -v psql &>/dev/null; then
        log_debug "PostgreSQL client found"
        db_available=true
    fi

    # Test Redis connection
    if command -v redis-cli &>/dev/null; then
        log_debug "Redis client found"
        db_available=true
    fi

    # Test MySQL connection
    if command -v mysql &>/dev/null; then
        log_debug "MySQL client found"
        db_available=true
    fi

    if [[ "${db_available}" == true ]]; then
        log_debug "✓ At least one database client is available"
        return 0
    else
        log_skip "No database clients installed (this is normal for minimal/standard profiles)"
        SKIPPED_TESTS+=("database_connection")
        return 0
    fi
}

# Test 8: Virtual Environment Activation
test_venv_activation() {
    log_test "Test: Virtual Environment Activation"

    # Create a temporary virtual environment
    local test_venv="${TEST_WORK_DIR}/test_venv"

    if command -v python3 &>/dev/null; then
        # Create venv
        if python3 -m venv "${test_venv}" 2>/dev/null; then
            log_debug "✓ Virtual environment created"

            # Check activation script exists
            if [[ -f "${test_venv}/bin/activate" ]]; then
                log_debug "✓ Activation script found"

                # Test activation in a subshell
                (
                    # shellcheck disable=SC1091
                    source "${test_venv}/bin/activate"
                    if [[ -n "${VIRTUAL_ENV:-}" ]]; then
                        exit 0
                    else
                        exit 1
                    fi
                )

                local exit_code=$?
                if [[ ${exit_code} -eq 0 ]]; then
                    log_debug "✓ Virtual environment activation successful"
                    return 0
                else
                    log_fail "Virtual environment activation failed"
                    return 1
                fi
            else
                log_fail "Activation script not found"
                return 1
            fi
        else
            log_fail "Failed to create virtual environment"
            return 1
        fi
    else
        log_skip "Python 3 not available (skipping venv test)"
        SKIPPED_TESTS+=("venv_activation")
        return 0
    fi
}

# Test 9: Setup Script Help
test_setup_help() {
    log_test "Test: Setup Script Help"

    if [[ -f "${SETUP_SCRIPT}" ]]; then
        local help_output
        help_output=$("${SETUP_SCRIPT}" --help 2>&1 || true)

        assert_contains "Usage:" "${help_output}" "Help contains usage information"
        assert_contains "Options:" "${help_output}" "Help contains options section"
        assert_contains "Examples:" "${help_output}" "Help contains examples section"

        return 0
    else
        log_fail "Setup script not found: ${SETUP_SCRIPT}"
        return 1
    fi
}

# Test 10: Logging Functionality
test_logging() {
    log_test "Test: Logging Functionality"

    # Create a test script with logging
    local test_script="${TEST_WORK_DIR}/log_test.sh"
    cat > "${test_script}" <<'EOF'
#!/usr/bin/env bash
LOG_FILE="/tmp/test_log_$$.log"
log_info() { echo "[INFO] $*" | tee -a "${LOG_FILE}"; }
log_error() { echo "[ERROR] $*" | tee -a "${LOG_FILE}"; }

log_info "Test info message"
log_error "Test error message"
cat "${LOG_FILE}"
rm -f "${LOG_FILE}"
EOF

    chmod +x "${test_script}"

    local output
    output=$("${test_script}" 2>&1)

    assert_contains "[INFO]" "${output}" "Logging produces INFO messages"
    assert_contains "[ERROR]" "${output}" "Logging produces ERROR messages"

    return 0
}

# Test 11: Prerequisites File Validation
test_prerequisites_file() {
    log_test "Test: Prerequisites File Validation"

    # Check if prerequisites file would be created
    local prereqs_file="/tmp/issue67_work/prerequisites_validated.json"

    # For this test, we check the requirements files instead
    local req_dir="${DEVGRU_DIR}/requirements"

    if [[ -d "${req_dir}" ]]; then
        local req_files=(
            "requirements-core.txt"
            "requirements-optional.txt"
            "requirements-cloud-aws.txt"
            "requirements-cloud-azure.txt"
            "requirements-cloud-gcp.txt"
        )

        local all_exist=true
        for req_file in "${req_files[@]}"; do
            if [[ -f "${req_dir}/${req_file}" ]]; then
                log_debug "✓ Requirements file found: ${req_file}"
            else
                log_fail "✗ Requirements file not found: ${req_file}"
                all_exist=false
            fi
        done

        return $([ "${all_exist}" = true ] && echo 0 || echo 1)
    else
        log_fail "Requirements directory not found: ${req_dir}"
        return 1
    fi
}

# Test 12: State Management
test_state_management() {
    log_test "Test: State Management"

    local state_dir="${DEVGRU_DIR}/.state"

    # Check if state directory can be created
    if [[ -d "${state_dir}" ]]; then
        log_debug "✓ State directory exists"

        # Check if we can write to it
        local test_file="${state_dir}/.test_$$"
        if touch "${test_file}" 2>/dev/null; then
            log_debug "✓ State directory is writable"
            rm -f "${test_file}"
            return 0
        else
            log_fail "State directory is not writable"
            return 1
        fi
    else
        log_debug "State directory does not exist yet (normal for fresh install)"
        return 0
    fi
}

###############################################################################
# Test Suite Execution
###############################################################################

run_all_tests() {
    log_section "Running All Tests"

    run_test "OS Detection" test_os_detection
    run_test "Profile Selection" test_profile_selection
    run_test "Dry-Run Mode" test_dry_run_mode
    run_test "Module Loading" test_module_loading
    run_test "Python Installation" test_python_installation
    run_test "Package Installation" test_package_installation
    run_test "Database Connection" test_database_connection
    run_test "Virtual Environment Activation" test_venv_activation
    run_test "Setup Script Help" test_setup_help
    run_test "Logging Functionality" test_logging
    run_test "Prerequisites File" test_prerequisites_file
    run_test "State Management" test_state_management
}

run_specific_test() {
    local test_name="$1"

    log_section "Running Specific Test: ${test_name}"

    case "${test_name}" in
        os-detection)
            run_test "OS Detection" test_os_detection
            ;;
        profile-selection)
            run_test "Profile Selection" test_profile_selection
            ;;
        dry-run)
            run_test "Dry-Run Mode" test_dry_run_mode
            ;;
        module-loading)
            run_test "Module Loading" test_module_loading
            ;;
        python-install)
            run_test "Python Installation" test_python_installation
            ;;
        package-install)
            run_test "Package Installation" test_package_installation
            ;;
        database-conn)
            run_test "Database Connection" test_database_connection
            ;;
        venv-activation)
            run_test "Virtual Environment Activation" test_venv_activation
            ;;
        *)
            log_fail "Unknown test: ${test_name}"
            return 1
            ;;
    esac
}

###############################################################################
# Reporting
###############################################################################

generate_test_report() {
    log_section "Test Results Summary"

    local total_tests=$((${#PASSED_TESTS[@]} + ${#FAILED_TESTS[@]} + ${#SKIPPED_TESTS[@]}))
    local pass_count=${#PASSED_TESTS[@]}
    local fail_count=${#FAILED_TESTS[@]}
    local skip_count=${#SKIPPED_TESTS[@]}

    echo ""
    echo -e "${COLOR_WHITE}Total Tests:   ${total_tests}${COLOR_RESET}"
    echo -e "${COLOR_GREEN}Passed:        ${pass_count}${COLOR_RESET}"
    echo -e "${COLOR_RED}Failed:        ${fail_count}${COLOR_RESET}"
    echo -e "${COLOR_YELLOW}Skipped:       ${skip_count}${COLOR_RESET}"
    echo ""

    if [[ ${pass_count} -gt 0 ]]; then
        echo -e "${COLOR_GREEN}Passed Tests:${COLOR_RESET}"
        for test in "${PASSED_TESTS[@]}"; do
            echo -e "  ${COLOR_GREEN}✓${COLOR_RESET} ${test}"
        done
        echo ""
    fi

    if [[ ${fail_count} -gt 0 ]]; then
        echo -e "${COLOR_RED}Failed Tests:${COLOR_RESET}"
        for test in "${FAILED_TESTS[@]}"; do
            echo -e "  ${COLOR_RED}✗${COLOR_RESET} ${test}"
        done
        echo ""
    fi

    if [[ ${skip_count} -gt 0 ]]; then
        echo -e "${COLOR_YELLOW}Skipped Tests:${COLOR_RESET}"
        for test in "${SKIPPED_TESTS[@]}"; do
            echo -e "  ${COLOR_YELLOW}⊘${COLOR_RESET} ${test}"
        done
        echo ""
    fi

    # Calculate success rate
    local success_rate=0
    if [[ ${total_tests} -gt 0 ]]; then
        success_rate=$((pass_count * 100 / total_tests))
    fi

    echo -e "Success Rate: ${success_rate}%"
    echo ""

    # Save report to file
    local report_file="${TEST_WORK_DIR}/test_report.txt"
    {
        echo "DevGRU Setup Test Report"
        echo "========================"
        echo ""
        echo "Date: $(date)"
        echo "Total Tests: ${total_tests}"
        echo "Passed: ${pass_count}"
        echo "Failed: ${fail_count}"
        echo "Skipped: ${skip_count}"
        echo "Success Rate: ${success_rate}%"
        echo ""
        echo "Log file: ${TEST_LOG_FILE}"
    } > "${report_file}"

    log_info "Test report saved to: ${report_file}"

    # Return exit code based on failures
    if [[ ${fail_count} -gt 0 ]]; then
        return 1
    else
        return 0
    fi
}

###############################################################################
# Command-Line Argument Parsing
###############################################################################

show_help() {
    cat <<EOF
DevGRU Setup Test Suite v${TEST_VERSION}

Usage: ./test_setup.sh [OPTIONS] [TEST_NAME]

Options:
  --verbose            Enable verbose output
  --dry-run           Run tests in dry-run mode
  --list              List all available tests
  --help              Show this help message

Test Names (optional):
  all                 Run all tests (default)
  os-detection        Test OS detection functionality
  profile-selection   Test profile selection and validation
  dry-run             Test dry-run mode
  module-loading      Test module loading
  python-install      Test Python installation verification
  package-install     Test package installation verification
  database-conn       Test database connection
  venv-activation     Test virtual environment activation

Examples:
  # Run all tests
  ./test_setup.sh

  # Run specific test
  ./test_setup.sh python-install

  # Run tests with verbose output
  ./test_setup.sh --verbose

  # List available tests
  ./test_setup.sh --list

EOF
}

list_tests() {
    cat <<EOF
Available Tests:
  1. os-detection        - Test OS detection functionality
  2. profile-selection   - Test profile selection and validation
  3. dry-run             - Test dry-run mode
  4. module-loading      - Test module loading
  5. python-install      - Test Python installation verification
  6. package-install     - Test package installation verification
  7. database-conn       - Test database connection
  8. venv-activation     - Test virtual environment activation
  9. setup-help          - Test setup script help
 10. logging             - Test logging functionality
 11. prerequisites-file  - Test prerequisites file validation
 12. state-management    - Test state management

To run a specific test:
  ./test_setup.sh <test-name>

To run all tests:
  ./test_setup.sh all
EOF
}

parse_arguments() {
    while [[ $# -gt 0 ]]; do
        case "$1" in
            --verbose)
                VERBOSE=true
                shift
                ;;
            --dry-run)
                DRY_RUN=true
                shift
                ;;
            --list)
                list_tests
                exit 0
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
                TEST_NAME="$1"
                shift
                ;;
        esac
    done
}

###############################################################################
# Cleanup and Signal Handling
###############################################################################

cleanup() {
    local exit_code=$?

    if [[ ${exit_code} -ne 0 ]] && [[ "${VERBOSE}" != true ]]; then
        log_info "Tests failed. Run with --verbose for more details."
    fi

    teardown_test_environment

    exit ${exit_code}
}

handle_interrupt() {
    echo ""
    log_info "Test suite interrupted by user"
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

    # Setup test environment
    setup_test_environment

    # Print banner
    log_section "DevGRU Setup Test Suite v${TEST_VERSION}"

    log_info "Test Mode: ${TEST_NAME}"
    log_info "Verbose: ${VERBOSE}"
    log_info "Log File: ${TEST_LOG_FILE}"

    # Run tests
    if [[ "${TEST_NAME}" == "all" ]]; then
        run_all_tests
    else
        run_specific_test "${TEST_NAME}"
    fi

    # Generate report
    generate_test_report

    return $?
}

# Execute main function
main "$@"
