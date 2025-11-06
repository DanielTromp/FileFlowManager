#!/usr/bin/env bash
#
# FileFlow Manager - Setup Script
# Installs dependencies, initializes database, and verifies tools
#

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
info() {
    echo -e "${BLUE}ℹ ${NC}$1"
}

success() {
    echo -e "${GREEN}✓${NC} $1"
}

warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

error() {
    echo -e "${RED}✗${NC} $1"
}

# Check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Version comparison helper
version_ge() {
    printf '%s\n%s\n' "$2" "$1" | sort -V -C
}

echo ""
echo "╔════════════════════════════════════════╗"
echo "║   FileFlow Manager - Setup Script     ║"
echo "╚════════════════════════════════════════╝"
echo ""

#
# 1. CHECK PREREQUISITES
#
info "Checking prerequisites..."

# Check Python
if command_exists python3; then
    PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
    if version_ge "$PYTHON_VERSION" "3.10.0"; then
        success "Python $PYTHON_VERSION (required: 3.10+)"
    else
        error "Python $PYTHON_VERSION found, but 3.10+ required"
        exit 1
    fi
else
    error "Python 3 not found. Please install Python 3.10+"
    echo "  Visit: https://www.python.org/downloads/"
    exit 1
fi

# Check Poetry
if command_exists poetry; then
    POETRY_VERSION=$(poetry --version 2>&1 | awk '{print $3}' | tr -d ')')
    success "Poetry $POETRY_VERSION"
else
    error "Poetry not found"
    echo "  Install with: curl -sSL https://install.python-poetry.org | python3 -"
    echo "  Or visit: https://python-poetry.org/docs/#installation"
    exit 1
fi

# Check Node.js
if command_exists node; then
    NODE_VERSION=$(node --version | tr -d 'v')
    if version_ge "$NODE_VERSION" "18.0.0"; then
        success "Node.js $NODE_VERSION (required: 18+)"
    else
        error "Node.js $NODE_VERSION found, but 18+ required"
        exit 1
    fi
else
    error "Node.js not found. Please install Node.js 18+"
    echo "  Visit: https://nodejs.org/"
    exit 1
fi

# Check pnpm
if command_exists pnpm; then
    PNPM_VERSION=$(pnpm --version)
    success "pnpm $PNPM_VERSION"
else
    warning "pnpm not found. Installing globally..."
    npm install -g pnpm
    if [ $? -eq 0 ]; then
        success "pnpm installed successfully"
    else
        error "Failed to install pnpm"
        exit 1
    fi
fi

# Check Rust (for Tauri)
if command_exists rustc; then
    RUST_VERSION=$(rustc --version | awk '{print $2}')
    success "Rust $RUST_VERSION"
else
    warning "Rust not found. Installing..."
    curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
    source "$HOME/.cargo/env"
    if command_exists rustc; then
        success "Rust installed successfully"
    else
        error "Failed to install Rust"
        exit 1
    fi
fi

echo ""
info "All prerequisites satisfied!"
echo ""

#
# 2. INSTALL BACKEND DEPENDENCIES
#
info "Installing backend dependencies..."
cd backend

if [ -f "pyproject.toml" ]; then
    poetry install
    if [ $? -eq 0 ]; then
        success "Backend dependencies installed"
    else
        error "Failed to install backend dependencies"
        exit 1
    fi
else
    error "backend/pyproject.toml not found"
    exit 1
fi

cd ..

#
# 3. INSTALL FRONTEND DEPENDENCIES
#
info "Installing frontend dependencies..."
cd frontend

if [ -f "package.json" ]; then
    pnpm install
    if [ $? -eq 0 ]; then
        success "Frontend dependencies installed"
    else
        error "Failed to install frontend dependencies"
        exit 1
    fi
else
    error "frontend/package.json not found"
    exit 1
fi

cd ..

#
# 4. INITIALIZE CONFIGURATION
#
info "Initializing configuration..."

CONFIG_DIR="$HOME/.config/fileflow"
CONFIG_FILE="$CONFIG_DIR/fileflow.toml"

if [ -f "$CONFIG_FILE" ]; then
    success "Configuration already exists at $CONFIG_FILE"
else
    info "Configuration will be created on first run"
fi

#
# 5. VERIFY TOOLS
#
echo ""
info "Verifying installation..."

# Test backend CLI
cd backend
if poetry run fileflow --help >/dev/null 2>&1; then
    success "Backend CLI is functional"
else
    error "Backend CLI verification failed"
    exit 1
fi
cd ..

# Test frontend build tools
cd frontend
if pnpm --version >/dev/null 2>&1; then
    success "Frontend build tools are functional"
else
    error "Frontend build tools verification failed"
    exit 1
fi
cd ..

#
# 6. DISPLAY SUMMARY
#
echo ""
echo "╔════════════════════════════════════════╗"
echo "║          Setup Complete! ✓             ║"
echo "╚════════════════════════════════════════╝"
echo ""
echo "Next steps:"
echo ""
echo "  ${BLUE}1.${NC} Run the CLI:"
echo "     ${GREEN}cd backend${NC}"
echo "     ${GREEN}poetry run fileflow scan${NC}"
echo ""
echo "  ${BLUE}2.${NC} Run the GUI (development mode):"
echo "     ${GREEN}cd frontend${NC}"
echo "     ${GREEN}pnpm tauri dev${NC}"
echo ""
echo "  ${BLUE}3.${NC} Build for production:"
echo "     ${GREEN}cd frontend${NC}"
echo "     ${GREEN}pnpm tauri build${NC}"
echo ""
echo "Documentation:"
echo "  • Root README:     ${YELLOW}README.md${NC}"
echo "  • Backend README:  ${YELLOW}backend/README.md${NC}"
echo "  • Frontend README: ${YELLOW}frontend/README.md${NC}"
echo "  • Quickstart:      ${YELLOW}specs/001-fileflow-manager/quickstart.md${NC}"
echo ""
echo "Configuration: ${YELLOW}~/.config/fileflow/fileflow.toml${NC}"
echo "Database:      ${YELLOW}~/.config/fileflow/fileflow.db${NC}"
echo "Logs:          ${YELLOW}~/.local/share/fileflow/fileflow.log${NC}"
echo ""
