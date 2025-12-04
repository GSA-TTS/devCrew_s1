#!/bin/bash
# Test runner script for UX Research & Design Feedback Platform
#
# Usage:
#   ./run_tests.sh [options]
#
# Options:
#   all         - Run all tests (default)
#   unit        - Run unit tests only
#   integration - Run integration tests only
#   performance - Run performance tests only
#   coverage    - Run tests with coverage report
#   fast        - Run fast tests only (exclude slow)
#   parallel    - Run tests in parallel
#   benchmark   - Run performance benchmarks
#   clean       - Clean test artifacts

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Project root
PROJECT_ROOT="/Users/tamnguyen/Documents/GitHub/devCrew_s1"
TEST_DIR="${PROJECT_ROOT}/tools/ux_research/tests"

# Function to print colored output
print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if pytest is installed
check_dependencies() {
    if ! command -v pytest &> /dev/null; then
        print_error "pytest is not installed"
        print_info "Installing test dependencies..."
        pip install -r "${TEST_DIR}/requirements-test.txt"
    fi
}

# Function to run all tests
run_all_tests() {
    print_info "Running all tests..."
    cd "${PROJECT_ROOT}"
    pytest "${TEST_DIR}" -v \
        --tb=short \
        --color=yes \
        --durations=10
}

# Function to run unit tests
run_unit_tests() {
    print_info "Running unit tests..."
    cd "${PROJECT_ROOT}"
    pytest "${TEST_DIR}" -v -m unit
}

# Function to run integration tests
run_integration_tests() {
    print_info "Running integration tests..."
    cd "${PROJECT_ROOT}"
    pytest "${TEST_DIR}/test_integration.py" -v \
        --tb=short
}

# Function to run performance tests
run_performance_tests() {
    print_info "Running performance tests..."
    cd "${PROJECT_ROOT}"
    pytest "${TEST_DIR}/test_performance.py" -v \
        --durations=0
}

# Function to run tests with coverage
run_coverage() {
    print_info "Running tests with coverage..."
    cd "${PROJECT_ROOT}"
    pytest "${TEST_DIR}" \
        --cov=tools/ux_research \
        --cov-report=html \
        --cov-report=term-missing \
        --cov-report=xml \
        --cov-fail-under=85 \
        -v

    print_info "Coverage report generated in htmlcov/index.html"
}

# Function to run fast tests
run_fast_tests() {
    print_info "Running fast tests (excluding slow)..."
    cd "${PROJECT_ROOT}"
    pytest "${TEST_DIR}" -v -m "not slow"
}

# Function to run tests in parallel
run_parallel_tests() {
    print_info "Running tests in parallel..."
    cd "${PROJECT_ROOT}"
    pytest "${TEST_DIR}" -v -n auto
}

# Function to run benchmarks
run_benchmarks() {
    print_info "Running performance benchmarks..."
    cd "${PROJECT_ROOT}"
    pytest "${TEST_DIR}/test_performance.py" \
        --benchmark-only \
        --benchmark-sort=mean \
        --benchmark-columns=min,max,mean,stddev \
        -v
}

# Function to clean test artifacts
clean_artifacts() {
    print_info "Cleaning test artifacts..."
    cd "${PROJECT_ROOT}"

    # Remove pytest cache
    find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
    find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true

    # Remove coverage files
    rm -rf htmlcov/
    rm -f .coverage
    rm -f coverage.xml

    # Remove benchmark files
    rm -rf .benchmarks/

    print_info "Cleanup complete"
}

# Function to show test statistics
show_statistics() {
    print_info "Test Statistics:"
    cd "${PROJECT_ROOT}"

    echo ""
    echo "Test Files:"
    find "${TEST_DIR}" -name "test_*.py" -type f | wc -l

    echo ""
    echo "Test Functions:"
    grep -r "def test_" "${TEST_DIR}" | wc -l

    echo ""
    echo "Test Classes:"
    grep -r "class Test" "${TEST_DIR}" | wc -l
}

# Main script logic
main() {
    check_dependencies

    case "${1:-all}" in
        all)
            run_all_tests
            ;;
        unit)
            run_unit_tests
            ;;
        integration)
            run_integration_tests
            ;;
        performance)
            run_performance_tests
            ;;
        coverage)
            run_coverage
            ;;
        fast)
            run_fast_tests
            ;;
        parallel)
            run_parallel_tests
            ;;
        benchmark)
            run_benchmarks
            ;;
        clean)
            clean_artifacts
            ;;
        stats)
            show_statistics
            ;;
        help|--help|-h)
            echo "Usage: $0 [option]"
            echo ""
            echo "Options:"
            echo "  all         - Run all tests (default)"
            echo "  unit        - Run unit tests only"
            echo "  integration - Run integration tests only"
            echo "  performance - Run performance tests only"
            echo "  coverage    - Run tests with coverage report"
            echo "  fast        - Run fast tests only"
            echo "  parallel    - Run tests in parallel"
            echo "  benchmark   - Run performance benchmarks"
            echo "  clean       - Clean test artifacts"
            echo "  stats       - Show test statistics"
            echo "  help        - Show this help message"
            ;;
        *)
            print_error "Unknown option: $1"
            print_info "Run '$0 help' for usage information"
            exit 1
            ;;
    esac
}

# Run main function
main "$@"
