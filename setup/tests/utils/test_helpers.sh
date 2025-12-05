#!/usr/bin/env bash
###############################################################################
# Test Helper Functions for DevGRU Setup Test Suite
#
# This file provides common utility functions for testing
# Should be sourced by test scripts
###############################################################################

set -euo pipefail

###############################################################################
# Mock and Fixture Utilities
###############################################################################

# Create a mock prerequisites JSON file
create_mock_prerequisites() {
    local output_file="${1:-/tmp/mock_prerequisites.json}"

    cat > "${output_file}" <<'EOF'
{
  "core_packages": [
    {"name": "requests", "version": "2.31.0"},
    {"name": "pyyaml", "version": "6.0.1"},
    {"name": "jinja2", "version": "3.1.2"},
    {"name": "pytest", "version": "7.4.0"},
    {"name": "black", "version": "23.7.0"}
  ],
  "optional_packages": [
    {"name": "pandas", "version": "2.0.3"},
    {"name": "numpy", "version": "1.24.3"},
    {"name": "matplotlib", "version": "3.7.2"},
    {"name": "scikit-learn", "version": "1.3.0"},
    {"name": "jupyter", "version": "1.0.0"}
  ],
  "databases": [
    {"name": "redis", "version": "7.0"},
    {"name": "postgresql", "version": "15.0"},
    {"name": "neo4j", "version": "5.0"}
  ],
  "external_tools": [
    {"name": "docker", "version": "24.0"},
    {"name": "terraform", "version": "1.5"},
    {"name": "node", "version": "18.0"}
  ],
  "cloud_sdks": {
    "aws": [
      {"name": "boto3", "version": "1.28.0"},
      {"name": "awscli", "version": "2.13.0"}
    ],
    "azure": [
      {"name": "azure-identity", "version": "1.13.0"},
      {"name": "azure-mgmt-compute", "version": "30.0.0"}
    ],
    "gcp": [
      {"name": "google-cloud-storage", "version": "2.10.0"},
      {"name": "google-cloud-bigquery", "version": "3.11.0"}
    ]
  }
}
EOF

    echo "${output_file}"
}

# Create a temporary test environment
create_test_env() {
    local test_dir="${1:-/tmp/devgru_test_env_$$}"

    mkdir -p "${test_dir}"
    mkdir -p "${test_dir}/logs"
    mkdir -p "${test_dir}/.state"
    mkdir -p "${test_dir}/modules"

    echo "${test_dir}"
}

# Clean up test environment
cleanup_test_env() {
    local test_dir="$1"

    if [[ -d "${test_dir}" ]]; then
        rm -rf "${test_dir}"
    fi
}

###############################################################################
# System Information Helpers
###############################################################################

# Get the current OS type
get_os_type() {
    if [[ "$OSTYPE" == "darwin"* ]]; then
        echo "macos"
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        if grep -qi microsoft /proc/version 2>/dev/null; then
            echo "wsl2"
        elif [[ -f /etc/os-release ]]; then
            . /etc/os-release
            case "${ID}" in
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
    else
        echo "unknown"
    fi
}

# Get the package manager for the current OS
get_package_manager() {
    local os_type
    os_type=$(get_os_type)

    case "${os_type}" in
        macos)
            echo "brew"
            ;;
        debian|wsl2)
            echo "apt"
            ;;
        rhel)
            echo "yum"
            ;;
        *)
            echo "unknown"
            ;;
    esac
}

# Check if running in CI/CD environment
is_ci_environment() {
    [[ -n "${CI:-}" ]] || [[ -n "${GITHUB_ACTIONS:-}" ]] || [[ -n "${TRAVIS:-}" ]] || [[ -n "${CIRCLECI:-}" ]]
}

###############################################################################
# Command Execution Helpers
###############################################################################

# Run command and capture output
run_and_capture() {
    local cmd="$*"
    local output_file="/tmp/test_output_$$.txt"
    local exit_code

    eval "${cmd}" > "${output_file}" 2>&1 || exit_code=$?
    exit_code=${exit_code:-0}

    cat "${output_file}"
    rm -f "${output_file}"

    return ${exit_code}
}

# Run command with timeout
run_with_timeout() {
    local timeout_duration="$1"
    shift
    local cmd="$*"

    if command -v timeout &>/dev/null; then
        timeout "${timeout_duration}" bash -c "${cmd}"
    else
        # Fallback for systems without timeout command
        eval "${cmd}"
    fi
}

# Check if a command succeeds
command_succeeds() {
    local cmd="$*"
    eval "${cmd}" &>/dev/null
}

# Check if a command fails
command_fails() {
    local cmd="$*"
    ! eval "${cmd}" &>/dev/null
}

###############################################################################
# File and Directory Helpers
###############################################################################

# Create a temporary file with content
create_temp_file() {
    local content="$1"
    local extension="${2:-.txt}"

    local temp_file
    temp_file=$(mktemp "/tmp/devgru_test_XXXXXX${extension}")

    echo "${content}" > "${temp_file}"

    echo "${temp_file}"
}

# Compare two files
files_are_equal() {
    local file1="$1"
    local file2="$2"

    if [[ ! -f "${file1}" ]] || [[ ! -f "${file2}" ]]; then
        return 1
    fi

    diff -q "${file1}" "${file2}" &>/dev/null
}

# Check if directory is empty
directory_is_empty() {
    local dir="$1"

    if [[ ! -d "${dir}" ]]; then
        return 1
    fi

    [[ -z "$(ls -A "${dir}")" ]]
}

# Get file line count
get_line_count() {
    local file="$1"

    if [[ ! -f "${file}" ]]; then
        echo "0"
        return
    fi

    wc -l < "${file}" | tr -d ' '
}

###############################################################################
# Python-Specific Helpers
###############################################################################

# Check if Python version meets minimum requirement
python_version_meets_requirement() {
    local required_version="${1:-3.10}"
    local python_cmd="${2:-python3}"

    if ! command -v "${python_cmd}" &>/dev/null; then
        return 1
    fi

    local current_version
    current_version=$("${python_cmd}" --version 2>&1 | sed -n 's/^Python \([0-9]*\.[0-9]*\).*/\1/p')

    if [[ -z "${current_version}" ]]; then
        return 1
    fi

    # Compare versions
    printf '%s\n%s\n' "${required_version}" "${current_version}" | sort -V -C
}

# Check if pip package is installed
pip_package_installed() {
    local package_name="$1"
    local python_cmd="${2:-python3}"

    "${python_cmd}" -m pip show "${package_name}" &>/dev/null
}

# Get pip package version
get_pip_package_version() {
    local package_name="$1"
    local python_cmd="${2:-python3}"

    "${python_cmd}" -m pip show "${package_name}" 2>/dev/null | grep "^Version:" | cut -d' ' -f2
}

# Create a virtual environment
create_test_venv() {
    local venv_path="${1:-/tmp/test_venv_$$}"
    local python_cmd="${2:-python3}"

    "${python_cmd}" -m venv "${venv_path}" &>/dev/null

    echo "${venv_path}"
}

# Activate virtual environment
activate_venv() {
    local venv_path="$1"

    if [[ -f "${venv_path}/bin/activate" ]]; then
        # shellcheck disable=SC1091
        source "${venv_path}/bin/activate"
        return 0
    elif [[ -f "${venv_path}/Scripts/activate" ]]; then
        # shellcheck disable=SC1091
        source "${venv_path}/Scripts/activate"
        return 0
    else
        return 1
    fi
}

###############################################################################
# Database Helpers
###############################################################################

# Check if PostgreSQL is running
postgres_is_running() {
    if command -v pg_isready &>/dev/null; then
        pg_isready -q 2>/dev/null
    else
        # Fallback: check for common PostgreSQL ports
        if command -v lsof &>/dev/null; then
            lsof -i :5432 &>/dev/null
        else
            return 1
        fi
    fi
}

# Check if Redis is running
redis_is_running() {
    if command -v redis-cli &>/dev/null; then
        redis-cli ping &>/dev/null
    else
        # Fallback: check for common Redis ports
        if command -v lsof &>/dev/null; then
            lsof -i :6379 &>/dev/null
        else
            return 1
        fi
    fi
}

# Check if MySQL is running
mysql_is_running() {
    if command -v mysqladmin &>/dev/null; then
        mysqladmin ping &>/dev/null
    else
        # Fallback: check for common MySQL ports
        if command -v lsof &>/dev/null; then
            lsof -i :3306 &>/dev/null
        else
            return 1
        fi
    fi
}

###############################################################################
# JSON Helpers
###############################################################################

# Validate JSON file
json_is_valid() {
    local json_file="$1"

    if [[ ! -f "${json_file}" ]]; then
        return 1
    fi

    if command -v jq &>/dev/null; then
        jq empty "${json_file}" 2>/dev/null
    else
        # Fallback: use python
        if command -v python3 &>/dev/null; then
            python3 -c "import json; json.load(open('${json_file}'))" 2>/dev/null
        else
            return 1
        fi
    fi
}

# Extract JSON value
get_json_value() {
    local json_file="$1"
    local key_path="$2"

    if [[ ! -f "${json_file}" ]]; then
        return 1
    fi

    if command -v jq &>/dev/null; then
        jq -r "${key_path}" "${json_file}" 2>/dev/null
    else
        return 1
    fi
}

# Count JSON array elements
count_json_array() {
    local json_file="$1"
    local array_path="$2"

    if [[ ! -f "${json_file}" ]]; then
        echo "0"
        return
    fi

    if command -v jq &>/dev/null; then
        jq "${array_path} | length" "${json_file}" 2>/dev/null || echo "0"
    else
        echo "0"
    fi
}

###############################################################################
# Network Helpers
###############################################################################

# Check if a URL is accessible
url_is_accessible() {
    local url="$1"
    local timeout="${2:-5}"

    if command -v curl &>/dev/null; then
        curl -fsSL --max-time "${timeout}" "${url}" &>/dev/null
    elif command -v wget &>/dev/null; then
        wget -q --timeout="${timeout}" --spider "${url}" &>/dev/null
    else
        return 1
    fi
}

# Check if a port is open
port_is_open() {
    local host="${1:-localhost}"
    local port="$2"
    local timeout="${3:-2}"

    if command -v nc &>/dev/null; then
        nc -z -w "${timeout}" "${host}" "${port}" &>/dev/null
    elif command -v timeout &>/dev/null; then
        timeout "${timeout}" bash -c "cat < /dev/null > /dev/tcp/${host}/${port}" 2>/dev/null
    else
        return 1
    fi
}

###############################################################################
# Logging Helpers
###############################################################################

# Create a timestamped log entry
log_timestamp() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')]"
}

# Log to file only (no stdout)
log_silent() {
    local message="$*"
    local log_file="${TEST_LOG_FILE:-/tmp/test.log}"

    echo "$(log_timestamp) ${message}" >> "${log_file}"
}

# Count log entries matching pattern
count_log_matches() {
    local log_file="$1"
    local pattern="$2"

    if [[ ! -f "${log_file}" ]]; then
        echo "0"
        return
    fi

    grep -c "${pattern}" "${log_file}" 2>/dev/null || echo "0"
}

###############################################################################
# Performance Helpers
###############################################################################

# Measure command execution time
measure_execution_time() {
    local cmd="$*"
    local start_time
    local end_time
    local duration

    start_time=$(date +%s)
    eval "${cmd}" &>/dev/null
    end_time=$(date +%s)

    duration=$((end_time - start_time))

    echo "${duration}"
}

# Wait for condition with timeout
wait_for_condition() {
    local condition="$1"
    local timeout="${2:-30}"
    local interval="${3:-1}"

    local elapsed=0

    while [[ ${elapsed} -lt ${timeout} ]]; do
        if eval "${condition}"; then
            return 0
        fi

        sleep "${interval}"
        elapsed=$((elapsed + interval))
    done

    return 1
}

###############################################################################
# Cleanup Helpers
###############################################################################

# Register cleanup function
register_cleanup() {
    local cleanup_cmd="$*"

    # Add to cleanup array (if supported)
    if [[ -n "${CLEANUP_COMMANDS+x}" ]]; then
        CLEANUP_COMMANDS+=("${cleanup_cmd}")
    fi
}

# Execute all registered cleanups
execute_cleanups() {
    if [[ -n "${CLEANUP_COMMANDS+x}" ]]; then
        for cleanup_cmd in "${CLEANUP_COMMANDS[@]}"; do
            eval "${cleanup_cmd}" &>/dev/null || true
        done
    fi
}

###############################################################################
# Test Data Generators
###############################################################################

# Generate random string
generate_random_string() {
    local length="${1:-16}"

    if command -v openssl &>/dev/null; then
        openssl rand -base64 32 | tr -dc 'a-zA-Z0-9' | head -c "${length}"
    else
        cat /dev/urandom | tr -dc 'a-zA-Z0-9' | head -c "${length}"
    fi
}

# Generate test configuration file
generate_test_config() {
    local config_file="${1:-/tmp/test_config.yml}"

    cat > "${config_file}" <<'EOF'
---
test_configuration:
  profile: standard
  dry_run: false
  verbose: true
  skip_databases: false
  skip_tools: false

environment:
  python_version: "3.10"
  venv_path: "/tmp/test_venv"
  log_level: "INFO"

packages:
  core:
    - requests
    - pyyaml
    - pytest
  optional:
    - pandas
    - numpy
EOF

    echo "${config_file}"
}

###############################################################################
# Validation Helpers
###############################################################################

# Validate email format
is_valid_email() {
    local email="$1"

    [[ "${email}" =~ ^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$ ]]
}

# Validate semantic version
is_valid_semver() {
    local version="$1"

    [[ "${version}" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]
}

# Validate URL format
is_valid_url() {
    local url="$1"

    [[ "${url}" =~ ^https?://[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}(/.*)?$ ]]
}

###############################################################################
# Export functions for use in tests
###############################################################################

# Make functions available to calling scripts
export -f create_mock_prerequisites
export -f create_test_env
export -f cleanup_test_env
export -f get_os_type
export -f get_package_manager
export -f is_ci_environment
export -f run_and_capture
export -f run_with_timeout
export -f command_succeeds
export -f command_fails
export -f python_version_meets_requirement
export -f pip_package_installed
export -f get_pip_package_version
export -f json_is_valid
export -f get_json_value
export -f url_is_accessible
export -f port_is_open
export -f generate_random_string
