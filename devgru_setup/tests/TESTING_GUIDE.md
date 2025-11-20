# DevGRU Setup Testing Guide

Quick reference for running and understanding the DevGRU setup test suite.

## Quick Start

```bash
# Navigate to tests directory
cd devgru_setup/tests

# Run all tests
./run_tests.sh

# That's it! The test runner will execute all test modules and report results.
```

## Common Test Commands

```bash
# Run all tests
./run_tests.sh

# Run all tests with verbose output
./run_tests.sh --verbose

# Run specific test module
./run_tests.sh os              # OS detection tests
./run_tests.sh python          # Python verification tests
./run_tests.sh modules         # Module integration tests
./run_tests.sh suite           # Full comprehensive test suite

# Run individual test scripts directly
./test_os_detection.sh
./test_python_verification.sh
./test_module_integration.sh
./test_setup.sh

# Run specific test from main suite
./test_setup.sh python-install
./test_setup.sh venv-activation
./test_setup.sh --list         # Show all available tests
```

## Understanding Test Output

### Success (All Tests Pass)
```
========================================
Test Summary
========================================
Total Modules: 4
Passed:        4
Failed:        0

Success Rate: 100%

All tests passed!
```

### Partial Success (Some Tests Skipped)
```
Total Tests:   13
Passed:        12
Failed:        0
Skipped:       1

Success Rate: 92%
```

Skipped tests are normal when certain components (like databases) aren't installed.

### Failure
```
Failed Tests:
  ✗ Module Loading
  ✗ Python Installation

Success Rate: 67%
```

Check the detailed output or run with `--verbose` for debugging.

## Test Modules Overview

### 1. OS Detection Tests (`test_os_detection.sh`)
**Purpose:** Verify OS and platform detection
**What it tests:**
- OS type (macOS, Debian, RHEL, WSL2)
- Architecture (x86_64, arm64)
- Package manager detection
- OS-specific tools

**Expected result:** All tests pass on supported platforms

### 2. Python Verification Tests (`test_python_verification.sh`)
**Purpose:** Verify Python installation and configuration
**What it tests:**
- Python 3.10+ availability
- pip functionality
- Virtual environment support
- Essential Python modules
- Development headers

**Expected result:** All tests pass if Python 3.10+ is installed

### 3. Module Integration Tests (`test_module_integration.sh`)
**Purpose:** Verify all setup modules are present and valid
**What it tests:**
- Module file existence
- Bash syntax validation
- Function definitions
- Requirements files
- Directory structure

**Expected result:** All tests pass

### 4. Full Test Suite (`test_setup.sh`)
**Purpose:** Comprehensive testing of all setup functionality
**What it tests:**
- All of the above plus:
- Profile selection logic
- Dry-run mode
- Logging system
- State management
- Database client detection

**Expected result:** Most tests pass, some may skip if optional components aren't installed

## Interpreting Test Results

### Test Status Indicators

- `✓ PASS` - Test passed successfully
- `✗ FAIL` - Test failed, needs attention
- `⊘ SKIP` - Test skipped (usually because dependency not installed)

### Common Skip Scenarios

1. **Database tests skip** - Normal if you haven't installed PostgreSQL, Redis, or MySQL
2. **Package installation tests skip** - Normal on fresh systems without test packages
3. **Python development headers skip** - May occur if python3-dev package not installed

### What Should Never Fail

These tests should always pass on supported systems:
- OS Detection
- Profile Selection
- Module Loading
- Setup Script Help
- Logging Functionality
- Directory Structure

### Expected Skips for Different Profiles

**Minimal Profile:**
- Database connection tests
- Most package installation tests

**Standard Profile:**
- Database connection tests
- Advanced tool tests

**Full Profile:**
- Fewer skips, most tests should pass

## Troubleshooting

### "Permission denied" errors
```bash
chmod +x tests/*.sh tests/utils/*.sh
```

### "Module not found" errors
Check you're in the correct directory:
```bash
cd /path/to/devgru_setup/tests
pwd  # Should end in .../devgru_setup/tests
```

### Python version too old
Install Python 3.10 or higher:
```bash
# macOS
brew install python@3.11

# Ubuntu/Debian
sudo apt-get install python3.11

# RHEL/CentOS
sudo yum install python311
```

### All tests fail immediately
Check dependencies:
```bash
# Verify required tools
which jq curl git bash

# Install missing tools
# macOS: brew install jq
# Ubuntu: sudo apt-get install jq
# RHEL: sudo yum install jq
```

## Testing Before Installation

Run tests to verify your system is ready:

```bash
cd devgru_setup/tests
./run_tests.sh

# Check results
# - 100% pass rate: System fully ready
# - 75-99% pass rate: System mostly ready, review skips
# - <75% pass rate: Address failures before setup
```

## Testing After Installation

Verify installation succeeded:

```bash
cd devgru_setup/tests
./run_tests.sh

# After installation, expect:
# - Fewer skipped tests
# - Package installation tests passing
# - Database tests passing (if full profile)
```

## Continuous Testing

### During Development

```bash
# Quick test while developing
./test_setup.sh profile-selection

# Full validation
./run_tests.sh
```

### Before Committing Changes

```bash
# Run full test suite
./run_tests.sh --verbose

# Ensure all module tests pass
./test_module_integration.sh
```

## Advanced Usage

### Custom Test Selection

```bash
# Run only specific tests from main suite
./test_setup.sh os-detection
./test_setup.sh python-install
./test_setup.sh module-loading
```

### Verbose Debugging

```bash
# Maximum verbosity
./test_setup.sh --verbose

# Save verbose output
./test_setup.sh --verbose 2>&1 | tee test_output.log
```

### Test Logs

Test logs are saved in `/tmp/devgru_test_*/`:
```bash
# Find recent test logs
ls -lt /tmp/devgru_test_*/

# View latest test log
cat /tmp/devgru_test_*/test_*.log
```

## Writing Your Own Tests

### Basic Template

```bash
#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Source helpers (optional)
if [[ -f "${SCRIPT_DIR}/utils/test_helpers.sh" ]]; then
    source "${SCRIPT_DIR}/utils/test_helpers.sh"
fi

# Your test
echo "Test: My Custom Test"

if [[ condition ]]; then
    echo "✓ PASS"
    exit 0
else
    echo "✗ FAIL"
    exit 1
fi
```

### Using Test Helpers

```bash
# Check OS type
os_type=$(get_os_type)

# Check Python version
if python_version_meets_requirement "3.10"; then
    echo "✓ PASS"
fi

# Validate JSON
if json_is_valid "/path/to/file.json"; then
    echo "✓ PASS"
fi

# Create test environment
test_env=$(create_test_env)
# ... use test_env ...
cleanup_test_env "${test_env}"
```

## CI/CD Integration

### GitHub Actions

```yaml
name: DevGRU Tests
on: [push, pull_request]

jobs:
  test:
    runs-on: ${{ matrix.os }}
    strategy:
      matrix:
        os: [ubuntu-latest, macos-latest]
    steps:
      - uses: actions/checkout@v3
      - name: Run Tests
        run: |
          cd devgru_setup/tests
          ./run_tests.sh
```

### GitLab CI

```yaml
test:
  script:
    - cd devgru_setup/tests
    - ./run_tests.sh
  only:
    - branches
```

## Performance Benchmarks

Expected test execution times:

- **test_os_detection.sh**: < 1 second
- **test_python_verification.sh**: 3-5 seconds
- **test_module_integration.sh**: 1-2 seconds
- **test_setup.sh (full)**: 10-15 seconds
- **run_tests.sh (all)**: 15-25 seconds

If tests take significantly longer, investigate:
- Network connectivity (if tests download anything)
- Disk I/O (check disk space and performance)
- System load (other processes running)

## Best Practices

1. **Always run tests before installation**
   ```bash
   ./run_tests.sh  # Check system readiness
   ```

2. **Run tests after installation**
   ```bash
   ./run_tests.sh  # Verify installation
   ```

3. **Run tests after making changes**
   ```bash
   ./run_tests.sh  # Ensure nothing broke
   ```

4. **Keep test output for debugging**
   ```bash
   ./run_tests.sh --verbose 2>&1 | tee test_results.log
   ```

5. **Address failures before proceeding**
   - Don't ignore test failures
   - Investigate skipped tests if unexpected
   - Fix issues before running setup

## Getting Help

If tests fail unexpectedly:

1. Run with verbose output: `./test_setup.sh --verbose`
2. Check test logs in `/tmp/devgru_test_*/`
3. Verify system requirements in main README.md
4. Review TROUBLESHOOTING.md in docs/
5. Check GitHub Issue #67 for known issues

## Summary

The test suite is designed to:
- ✓ Verify system compatibility
- ✓ Validate prerequisites
- ✓ Ensure setup scripts work correctly
- ✓ Catch issues before installation
- ✓ Provide clear pass/fail reporting

Run `./run_tests.sh` regularly to ensure everything works as expected!
