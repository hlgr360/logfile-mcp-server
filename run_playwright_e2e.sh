#!/bin/bash
"""
AI: Playwright E2E test runner script.

Runs the complete Playwright test suite for the log analysis application.
Ensures proper test environment setup and cleanup.
"""

set -e  # Exit on any error

echo "🎭 Starting Playwright E2E Tests..."
echo "=================================="

# Get the script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}✓${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

# Check if uv is available
if ! command -v uv &> /dev/null; then
    print_error "uv is not installed or not in PATH"
    exit 1
fi

print_status "uv package manager found"

# Check if Playwright is installed
echo "Checking Playwright installation..."
if ! uv run python -c "import playwright" 2>/dev/null; then
    print_error "Playwright is not installed"
    print_warning "Installing Playwright..."
    uv add playwright
fi

print_status "Playwright Python package available"

# Install Playwright browsers if needed
echo "Ensuring Playwright browsers are installed..."
uv run playwright install chromium
print_status "Playwright browsers ready"

# Check for demo database or create it
echo "Preparing test database..."
if [ ! -f "demo.db" ]; then
    print_warning "demo.db not found, creating with sample data..."
    uv run python -c "
from tests.fixtures.test_database import TestDatabaseFactory
import shutil

# Create demo database using shared test factory with sample log processing
db_ops = TestDatabaseFactory.create_test_database('demo.db', use_sample_logs=True)
db_ops.db_connection.close()
print('Demo database created with consistent test data')
"
else
    print_status "Test database demo.db found"
fi

# Run the Playwright tests
echo "Running Playwright E2E tests..."
echo "=================================="

# Set environment variables for testing
export PYTHONPATH="${SCRIPT_DIR}:${PYTHONPATH:-}"

# Run tests with verbose output
if uv run pytest tests/playwright/ -v --tb=short --maxfail=5; then
    echo "=================================="
    print_status "All Playwright E2E tests passed!"
    echo "🎉 Test suite completed successfully"
    exit 0
else
    echo "=================================="
    print_error "Some Playwright E2E tests failed!"
    echo "💥 Check the output above for details"
    exit 1
fi
