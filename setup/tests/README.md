# DevGRU Setup Test Suite

Comprehensive test suite for the DevGRU Multi-OS Prerequisites Setup Script.

## Overview

This test suite provides thorough testing coverage for all components of the DevGRU setup system, including:

- OS detection and platform compatibility
- Profile selection and validation
- Dry-run mode functionality
- Module loading and integration
- Python installation verification
- Package installation verification
- Database connection testing
- Virtual environment activation
- Logging and state management

## Directory Structure

```
tests/
├── README.md                      # This file
├── test_setup.sh                  # Main comprehensive test suite
├── run_tests.sh                   # Convenience test runner
├── test_os_detection.sh           # OS detection tests
├── test_python_verification.sh    # Python verification tests
├── test_module_integration.sh     # Module integration tests
└── utils/
    └── test_helpers.sh            # Shared test utilities and helpers
```

## Quick Start

### Run All Tests

```bash
cd setup/tests
./run_tests.sh
```

### Run Specific Test Module

```bash
# Run OS detection tests
./run_tests.sh os

# Run Python verification tests
./run_tests.sh python

# Run module integration tests
./run_tests.sh modules

# Run full test suite
./run_tests.sh suite
```

### Run Individual Tests

```bash
# Run main test suite
./test_setup.sh

# Run with verbose output
./test_setup.sh --verbose

# List available tests
./test_setup.sh --list

# Run specific test
./test_setup.sh python-install
```

## Test Modules

### 1. Main Test Suite (`test_setup.sh`)

The comprehensive test suite that includes all test cases:

**Test Cases:**
1. OS Detection - Validates operating system identification
2. Profile Selection - Tests profile validation logic
3. Dry-Run Mode - Verifies dry-run functionality
4. Module Loading - Checks module availability and syntax
5. Python Installation - Verifies Python version requirements
6. Package Installation - Tests package installation verification
7. Database Connection - Validates database client detection
8. Virtual Environment - Tests venv creation and activation
9. Setup Script Help - Verifies help documentation
10. Logging Functionality - Tests logging system
11. Prerequisites File - Validates prerequisites structure
12. State Management - Tests state directory and files

**Usage:**
```bash
./test_setup.sh [OPTIONS] [TEST_NAME]

Options:
  --verbose            Enable verbose output
  --dry-run           Run tests in dry-run mode
  --list              List all available tests
  --help              Show help message

Test Names:
  all                 Run all tests (default)
  os-detection        Test OS detection
  profile-selection   Test profile selection
  dry-run             Test dry-run mode
  module-loading      Test module loading
  python-install      Test Python installation
  package-install     Test package installation
  database-conn       Test database connection
  venv-activation     Test virtual environment
```

### 2. OS Detection Tests (`test_os_detection.sh`)

Focused tests for operating system detection:

**Tests:**
- Current OS type detection (macOS, Debian, RHEL, WSL2)
- System architecture detection (x86_64, arm64)
- Package manager detection (brew, apt, yum)
- OS-specific tool verification
- WSL2 environment detection

**Usage:**
```bash
./test_os_detection.sh
```

### 3. Python Verification Tests (`test_python_verification.sh`)

Tests for Python installation and configuration:

**Tests:**
- Python availability check
- Python version validation (3.10+)
- pip availability and version
- venv module availability
- Virtual environment creation
- Python development headers
- Essential Python modules
- pip install functionality

**Usage:**
```bash
./test_python_verification.sh
```

### 4. Module Integration Tests (`test_module_integration.sh`)

Tests for module loading and integration:

**Tests:**
- All required modules exist
- Module syntax validation
- Module executability
- python_setup module functions
- Module documentation
- Requirements files validation
- Main setup script validation
- Directory structure validation

**Usage:**
```bash
./test_module_integration.sh
```

### 5. Test Runner (`run_tests.sh`)

Convenience script to run all or specific test modules:

**Usage:**
```bash
./run_tests.sh [OPTIONS] [MODULE]

Options:
  --verbose, -v        Enable verbose output
  --help, -h          Show help message

Modules:
  all                 Run all test modules (default)
  os                  Run OS detection tests
  python              Run Python verification tests
  modules             Run module integration tests
  suite               Run full test suite
```

## Test Utilities

### Test Helpers (`utils/test_helpers.sh`)

Shared utility functions available to all tests:

**Mock and Fixture Utilities:**
- `create_mock_prerequisites()` - Create mock prerequisites JSON
- `create_test_env()` - Create temporary test environment
- `cleanup_test_env()` - Clean up test environment

**System Information Helpers:**
- `get_os_type()` - Get current OS type
- `get_package_manager()` - Get package manager for current OS
- `is_ci_environment()` - Check if running in CI/CD

**Command Execution Helpers:**
- `run_and_capture()` - Run command and capture output
- `run_with_timeout()` - Run command with timeout
- `command_succeeds()` - Check if command succeeds
- `command_fails()` - Check if command fails

**Python-Specific Helpers:**
- `python_version_meets_requirement()` - Check Python version
- `pip_package_installed()` - Check if pip package is installed
- `get_pip_package_version()` - Get pip package version
- `create_test_venv()` - Create test virtual environment
- `activate_venv()` - Activate virtual environment

**Database Helpers:**
- `postgres_is_running()` - Check PostgreSQL status
- `redis_is_running()` - Check Redis status
- `mysql_is_running()` - Check MySQL status

**JSON Helpers:**
- `json_is_valid()` - Validate JSON file
- `get_json_value()` - Extract JSON value
- `count_json_array()` - Count JSON array elements

**Network Helpers:**
- `url_is_accessible()` - Check URL accessibility
- `port_is_open()` - Check if port is open

**Validation Helpers:**
- `is_valid_email()` - Validate email format
- `is_valid_semver()` - Validate semantic version
- `is_valid_url()` - Validate URL format

## Assertion Functions

The main test suite includes comprehensive assertion functions:

### Basic Assertions
- `assert_equals(expected, actual, message)` - Assert equality
- `assert_not_equals(not_expected, actual, message)` - Assert inequality
- `assert_contains(substring, string, message)` - Assert substring presence
- `assert_not_contains(substring, string, message)` - Assert substring absence

### File System Assertions
- `assert_file_exists(file_path, message)` - Assert file exists
- `assert_dir_exists(dir_path, message)` - Assert directory exists

### Command Assertions
- `assert_command_exists(command, message)` - Assert command available
- `assert_exit_code(expected_code, actual_code, message)` - Assert exit code

## Writing New Tests

### Basic Test Structure

```bash
#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Source test helpers
if [[ -f "${SCRIPT_DIR}/utils/test_helpers.sh" ]]; then
    # shellcheck disable=SC1091
    source "${SCRIPT_DIR}/utils/test_helpers.sh"
fi

# Your test code here
echo "Test: My New Test"

if [[ condition ]]; then
    echo "✓ PASS"
    exit 0
else
    echo "✗ FAIL"
    exit 1
fi
```

### Using Assertions

```bash
# Example test with assertions
test_my_feature() {
    local expected="value"
    local actual=$(my_command)

    assert_equals "${expected}" "${actual}" "My command returns expected value"
    assert_file_exists "/path/to/file" "Output file was created"
    assert_command_exists "my_tool" "Required tool is installed"

    return 0
}

# Run test
run_test "My Feature Test" test_my_feature
```

### Using Test Helpers

```bash
# Create test environment
test_env=$(create_test_env)

# Create mock prerequisites
prereqs=$(create_mock_prerequisites "${test_env}/prereqs.json")

# Check Python version
if python_version_meets_requirement "3.10"; then
    echo "Python version is sufficient"
fi

# Clean up
cleanup_test_env "${test_env}"
```

## Test Output

### Success Output
```
========================================
Test Results Summary
========================================

Total Tests:   12
Passed:        12
Failed:        0
Skipped:       0

Success Rate: 100%
```

### Failure Output
```
========================================
Test Results Summary
========================================

Total Tests:   12
Passed:        10
Failed:        2
Skipped:       0

Failed Tests:
  ✗ Database Connection
  ✗ Package Installation

Success Rate: 83%
```

## Continuous Integration

### GitHub Actions Example

```yaml
name: Test Suite

on: [push, pull_request]

jobs:
  test:
    runs-on: ${{ matrix.os }}
    strategy:
      matrix:
        os: [ubuntu-latest, macos-latest]

    steps:
      - uses: actions/checkout@v3

      - name: Run tests
        run: |
          cd setup/tests
          ./run_tests.sh --verbose
```

## Troubleshooting

### Common Issues

**Tests fail due to missing Python:**
- Some tests will skip if Python is not installed
- Install Python 3.10+ to run all tests

**Permission denied errors:**
- Make sure all test scripts are executable:
  ```bash
  chmod +x tests/*.sh tests/utils/*.sh
  ```

**Module not found errors:**
- Ensure you're running tests from the correct directory
- Check that all module files exist in `modules/` directory

**Database connection tests fail:**
- These tests will skip if database clients are not installed
- This is expected for minimal/standard profiles

### Verbose Mode

For detailed debugging information, run tests with verbose mode:

```bash
./test_setup.sh --verbose
./run_tests.sh --verbose
```

This will show:
- Individual assertion results
- Command execution details
- Intermediate values and calculations

### Log Files

Test logs are saved in `/tmp/devgru_test_*/`:
- `test_YYYYMMDD_HHMMSS.log` - Detailed test execution log
- `test_report.txt` - Summary report

## Best Practices

1. **Always clean up test artifacts**
   - Remove temporary files and directories
   - Use trap handlers for cleanup on exit

2. **Use meaningful test names**
   - Names should describe what is being tested
   - Use descriptive assertion messages

3. **Test edge cases**
   - Test both success and failure scenarios
   - Test boundary conditions

4. **Make tests independent**
   - Each test should run in isolation
   - Don't rely on test execution order

5. **Use test helpers**
   - Leverage existing helper functions
   - Add new helpers for common operations

6. **Document test purpose**
   - Add comments explaining complex test logic
   - Update this README when adding new tests

## Contributing

When adding new tests:

1. Follow the existing test structure
2. Add appropriate assertions
3. Include cleanup code
4. Update this README
5. Make the test script executable
6. Test on multiple platforms if possible

## License

Same as the main DevGRU project.

## Support

For issues or questions about the test suite:
- Check the troubleshooting section
- Review test output with --verbose flag
- Consult the main DevGRU documentation
- Open an issue on GitHub (Issue #67)
