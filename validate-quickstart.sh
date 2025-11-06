#!/usr/bin/env bash
# Quickstart Validation Script for FileFlow Manager
# Tests all instructions from specs/001-fileflow-manager/quickstart.md

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

PASSED=0
FAILED=0

echo -e "${BLUE}==========================================${NC}"
echo -e "${BLUE}FileFlow Manager - Quickstart Validation${NC}"
echo -e "${BLUE}==========================================${NC}"
echo ""

# Helper function to check command
check_test() {
    local test_name="$1"
    local test_result="$2"

    if [ "$test_result" -eq 0 ]; then
        echo -e "${GREEN}✓${NC} $test_name"
        PASSED=$((PASSED + 1))
    else
        echo -e "${RED}✗${NC} $test_name"
        FAILED=$((FAILED + 1))
    fi
    # Always return 0 so set -e doesn't exit on test failure
    return 0
}

# Test 1: Prerequisites - Python 3.10+
echo -e "${YELLOW}[1/11] Checking Python version...${NC}"
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version | awk '{print $2}')
    PYTHON_MAJOR=$(echo "$PYTHON_VERSION" | cut -d. -f1)
    PYTHON_MINOR=$(echo "$PYTHON_VERSION" | cut -d. -f2)

    if [ "$PYTHON_MAJOR" -ge 3 ] && [ "$PYTHON_MINOR" -ge 10 ]; then
        check_test "Python 3.10+ installed (found $PYTHON_VERSION)" 0
    else
        check_test "Python 3.10+ installed (found $PYTHON_VERSION - too old)" 1
    fi
else
    check_test "Python 3.10+ installed" 1
fi

# Test 2: Prerequisites - Node.js 18+
echo -e "${YELLOW}[2/11] Checking Node.js version...${NC}"
if command -v node &> /dev/null; then
    NODE_VERSION=$(node --version | sed 's/v//')
    NODE_MAJOR=$(echo "$NODE_VERSION" | cut -d. -f1)

    if [ "$NODE_MAJOR" -ge 18 ]; then
        check_test "Node.js 18+ installed (found $NODE_VERSION)" 0
    else
        check_test "Node.js 18+ installed (found $NODE_VERSION - too old)" 1
    fi
else
    check_test "Node.js 18+ installed" 1
fi

# Test 3: Prerequisites - Rust 1.70+
echo -e "${YELLOW}[3/11] Checking Rust version...${NC}"
# Source cargo environment if not in PATH
[ -f "$HOME/.cargo/env" ] && source "$HOME/.cargo/env"

if command -v cargo &> /dev/null; then
    RUST_VERSION=$(cargo --version | awk '{print $2}')
    RUST_MAJOR=$(echo "$RUST_VERSION" | cut -d. -f1)
    RUST_MINOR=$(echo "$RUST_VERSION" | cut -d. -f2)

    if [ "$RUST_MAJOR" -ge 1 ] && [ "$RUST_MINOR" -ge 70 ]; then
        check_test "Rust 1.70+ installed (found $RUST_VERSION)" 0
    else
        check_test "Rust 1.70+ installed (found $RUST_VERSION - too old)" 1
    fi
else
    check_test "Rust 1.70+ installed" 1
fi

# Test 4: Prerequisites - pnpm
echo -e "${YELLOW}[4/11] Checking pnpm...${NC}"
if command -v pnpm &> /dev/null; then
    PNPM_VERSION=$(pnpm --version)
    check_test "pnpm installed (found $PNPM_VERSION)" 0
else
    check_test "pnpm installed" 1
fi

# Test 5: Prerequisites - Poetry
echo -e "${YELLOW}[5/11] Checking Poetry...${NC}"
if command -v poetry &> /dev/null; then
    POETRY_VERSION=$(poetry --version | awk '{print $3}')
    check_test "Poetry installed (found $POETRY_VERSION)" 0
else
    check_test "Poetry installed" 1
fi

# Test 6: Backend dependencies installed
echo -e "${YELLOW}[6/11] Checking backend dependencies...${NC}"
if [ -d "backend/.venv" ] || poetry -C backend env info &> /dev/null; then
    check_test "Backend dependencies installed (Poetry virtualenv exists)" 0
else
    check_test "Backend dependencies installed" 1
fi

# Test 7: Frontend dependencies installed
echo -e "${YELLOW}[7/11] Checking frontend dependencies...${NC}"
if [ -d "frontend/node_modules" ]; then
    check_test "Frontend dependencies installed (node_modules exists)" 0
else
    check_test "Frontend dependencies installed" 1
fi

# Test 8: Backend CLI help command
echo -e "${YELLOW}[8/11] Testing backend CLI...${NC}"
cd backend
if poetry run fileflow --help &> /dev/null; then
    check_test "Backend CLI: fileflow --help" 0
else
    check_test "Backend CLI: fileflow --help" 1
fi
cd ..

# Test 9: Backend CLI rules list
echo -e "${YELLOW}[9/11] Testing backend CLI rules list...${NC}"
cd backend
if poetry run fileflow rules list &> /dev/null; then
    check_test "Backend CLI: fileflow rules list" 0
else
    check_test "Backend CLI: fileflow rules list" 1
fi
cd ..

# Test 10: Backend API server startup (timeout test)
echo -e "${YELLOW}[10/11] Testing backend API server startup...${NC}"
cd backend
# Start server in background, wait 5 seconds, check if running, then kill
timeout 5 poetry run python -m fileflow_api &> /tmp/fileflow-api-test.log &
API_PID=$!
sleep 2

if kill -0 $API_PID 2>/dev/null; then
    check_test "Backend API server starts successfully" 0
    kill $API_PID 2>/dev/null || true
else
    check_test "Backend API server starts successfully" 1
fi
cd ..

# Test 11: Frontend type checking
echo -e "${YELLOW}[11/11] Testing frontend type checking...${NC}"
cd frontend
if pnpm type-check &> /dev/null; then
    check_test "Frontend type checking passes" 0
else
    check_test "Frontend type checking passes" 1
fi
cd ..

# Summary
echo ""
echo -e "${BLUE}==========================================${NC}"
echo -e "${BLUE}Validation Summary${NC}"
echo -e "${BLUE}==========================================${NC}"
echo ""
echo -e "Passed: ${GREEN}$PASSED${NC}"
echo -e "Failed: ${RED}$FAILED${NC}"
echo ""

if [ "$FAILED" -eq 0 ]; then
    echo -e "${GREEN}All quickstart validation tests passed!${NC}"
    echo ""
    exit 0
else
    echo -e "${RED}Some validation tests failed. Review output above.${NC}"
    echo ""
    exit 1
fi
