#!/usr/bin/env bash
#
# Test script for python_setup.sh module
#

set -e

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Source the python_setup module
# shellcheck disable=SC1091
source "$SCRIPT_DIR/python_setup.sh"

echo "=== Testing Python Setup Module ==="
echo ""

echo "Test 1: OS Detection"
OS_TYPE=$(detect_os)
echo "  Detected OS: $OS_TYPE"
echo ""

echo "Test 2: Python Version Check"
for cmd in python3 python python3.11 python3.10; do
    if command -v "$cmd" &> /dev/null; then
        if version=$(check_python_version "$cmd"); then
            echo "  $cmd: version $version (meets requirements)"
        else
            echo "  $cmd: version check failed"
        fi
    fi
done
echo ""

echo "Test 3: Available Python Commands"
for cmd in python3 python python3.12 python3.11 python3.10; do
    if command -v "$cmd" &> /dev/null; then
        echo "  Found: $cmd ($($cmd --version 2>&1))"
    fi
done
echo ""

echo "=== All tests completed ==="
