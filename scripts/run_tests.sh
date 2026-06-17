#!/bin/bash
#
# SUTRA Test Runner
# Runs test suites with different configurations
#

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHONPATH="${PROJECT_ROOT}/src:${PYTHONPATH}"
export PYTHONPATH

# Logging function
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

# Success message
success_msg() {
    log "${GREEN}SUCCESS: $1${NC}"
}

# Warning message
warning_msg() {
    log "${YELLOW}WARNING: $1${NC}"
}

# Error message
error_exit() {
    log "${RED}ERROR: $1${NC}"
    exit 1
}

# Run unit tests
run_unit_tests() {
    log "Running unit tests..."
    
    cd "${PROJECT_ROOT}"
    
    pytest tests/ -v -m "unit" --tb=short \
        --cov=src --cov-report=term-missing \
        --cov-report=html:htmlcov/unit \
        --junitxml=reports/unit-tests.xml
    
    success_msg "Unit tests completed"
}

# Run integration tests
run_integration_tests() {
    log "Running integration tests..."
    
    cd "${PROJECT_ROOT}"
    
    pytest tests/ -v -m "integration" --tb=short \
        --cov=src --cov-report=term-missing \
        --cov-report=html:htmlcov/integration \
        --junitxml=reports/integration-tests.xml
    
    success_msg "Integration tests completed"
}

# Run performance tests
run_performance_tests() {
    log "Running performance tests..."
    
    cd "${PROJECT_ROOT}"
    
    pytest tests/ -v -m "performance" --tb=short \
        --junitxml=reports/performance-tests.xml
    
    success_msg "Performance tests completed"
}

# Run all tests
run_all_tests() {
    log "Running all tests..."
    
    cd "${PROJECT_ROOT}"
    
    pytest tests/ -v --tb=short \
        --cov=src --cov-report=term-missing \
        --cov-report=html:htmlcov/all \
        --cov-report=xml:reports/coverage.xml \
        --junitxml=reports/all-tests.xml
    
    success_msg "All tests completed"
}

# Run tests with coverage
run_coverage_tests() {
    log "Running tests with coverage..."
    
    cd "${PROJECT_ROOT}"
    
    pytest tests/ -v --tb=short \
        --cov=src \
        --cov-report=term-missing \
        --cov-report=html:htmlcov \
        --cov-report=xml:reports/coverage.xml \
        --cov-fail-under=75
    
    success_msg "Coverage tests completed"
}

# Run specific test file
run_specific_test() {
    local test_file=$1
    
    if [ -z "${test_file}" ]; then
        error_exit "Test file not specified"
    fi
    
    log "Running specific test: ${test_file}"
    
    cd "${PROJECT_ROOT}"
    
    pytest "${test_file}" -v --tb=short
    
    success_msg "Test completed: ${test_file}"
}

# Run tests in watch mode
run_watch_tests() {
    log "Running tests in watch mode..."
    
    cd "${PROJECT_ROOT}"
    
    pytest-watch tests/ -v --tb=short
    
    success_msg "Watch mode completed"
}

# Generate coverage report
generate_coverage_report() {
    log "Generating coverage report..."
    
    cd "${PROJECT_ROOT}"
    
    pytest tests/ --cov=src --cov-report=html:htmlcov --cov-report=term
    
    success_msg "Coverage report generated: htmlcov/index.html"
}

# Check code quality
check_code_quality() {
    log "Checking code quality..."
    
    cd "${PROJECT_ROOT}"
    
    # Run Black
    log "Running Black..."
    black --check src/ tests/ || warning_msg "Black check failed"
    
    # Run Flake8
    log "Running Flake8..."
    flake8 src/ tests/ || warning_msg "Flake8 check failed"
    
    # Run MyPy
    log "Running MyPy..."
    mypy src/ || warning_msg "MyPy check failed"
    
    # Run Pylint
    log "Running Pylint..."
    pylint src/ || warning_msg "Pylint check failed"
    
    success_msg "Code quality check completed"
}

# Run security scan
run_security_scan() {
    log "Running security scan..."
    
    cd "${PROJECT_ROOT}"
    
    # Run Bandit
    log "Running Bandit..."
    bandit -r src/ -f json -o reports/bandit-report.json || warning_msg "Bandit scan found issues"
    
    # Run Safety
    log "Running Safety..."
    safety check --json --output reports/safety-report.json || warning_msg "Safety scan found issues"
    
    success_msg "Security scan completed"
}

# Run dependency scan
run_dependency_scan() {
    log "Running dependency scan..."
    
    cd "${PROJECT_ROOT}"
    
    # Check for outdated dependencies
    pip list --outdated --format=json > reports/outdated-deps.json || warning_msg "Dependency scan failed"
    
    success_msg "Dependency scan completed"
}

# Create test reports directory
create_reports_dir() {
    mkdir -p reports
    mkdir -p htmlcov
}

# Main script logic
case "${1:-all}" in
    unit)
        create_reports_dir
        run_unit_tests
        ;;
    integration)
        create_reports_dir
        run_integration_tests
        ;;
    performance)
        create_reports_dir
        run_performance_tests
        ;;
    all)
        create_reports_dir
        run_all_tests
        ;;
    coverage)
        create_reports_dir
        run_coverage_tests
        ;;
    specific)
        run_specific_test "${2}"
        ;;
    watch)
        run_watch_tests
        ;;
    report)
        generate_coverage_report
        ;;
    quality)
        check_code_quality
        ;;
    security)
        create_reports_dir
        run_security_scan
        ;;
    dependencies)
        create_reports_dir
        run_dependency_scan
        ;;
    full)
        create_reports_dir
        run_all_tests
        check_code_quality
        run_security_scan
        run_dependency_scan
        success_msg "Full test suite completed"
        ;;
    *)
        echo "Usage: $0 <command> [args]"
        echo ""
        echo "Commands:"
        echo "  unit           - Run unit tests"
        echo "  integration    - Run integration tests"
        echo "  performance    - Run performance tests"
        echo "  all            - Run all tests (default)"
        echo "  coverage       - Run tests with coverage"
        echo "  specific       - Run specific test file"
        echo "  watch          - Run tests in watch mode"
        echo "  report         - Generate coverage report"
        echo "  quality        - Check code quality"
        echo "  security       - Run security scan"
        echo "  dependencies   - Run dependency scan"
        echo "  full           - Run full test suite (tests + quality + security)"
        exit 1
        ;;
esac

exit 0