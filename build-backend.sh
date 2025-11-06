#!/usr/bin/env bash
# Production build script for FileFlow Manager backend
# Builds Python wheel and source distribution using Poetry

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}===========================================${NC}"
echo -e "${GREEN}FileFlow Manager - Backend Build${NC}"
echo -e "${GREEN}===========================================${NC}"
echo ""

# Check prerequisites
echo -e "${YELLOW}[1/6] Checking prerequisites...${NC}"

if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Error: Python 3 is not installed${NC}"
    exit 1
fi

PYTHON_VERSION=$(python3 --version | awk '{print $2}')
echo "  ✓ Python $PYTHON_VERSION"

if ! command -v poetry &> /dev/null; then
    echo -e "${RED}Error: Poetry is not installed${NC}"
    echo "  Install with: curl -sSL https://install.python-poetry.org | python3 -"
    exit 1
fi

POETRY_VERSION=$(poetry --version | awk '{print $3}')
echo "  ✓ Poetry $POETRY_VERSION"

# Navigate to backend directory
cd "$(dirname "$0")/backend"

# Clean previous builds
echo -e "\n${YELLOW}[2/6] Cleaning previous builds...${NC}"
rm -rf dist/ build/ *.egg-info/
echo "  ✓ Build directories cleaned"

# Install dependencies
echo -e "\n${YELLOW}[3/6] Installing dependencies...${NC}"
poetry install --no-interaction --no-root
echo "  ✓ Dependencies installed"

# Run linting
echo -e "\n${YELLOW}[4/6] Running linting checks...${NC}"
if poetry run ruff check .; then
    echo "  ✓ Ruff linting passed"
else
    echo -e "${RED}  ✗ Ruff linting failed${NC}"
    exit 1
fi

if poetry run black --check .; then
    echo "  ✓ Black formatting passed"
else
    echo -e "${RED}  ✗ Black formatting failed${NC}"
    echo "  Run 'poetry run black .' to fix formatting"
    exit 1
fi

# Run type checking
echo -e "\n${YELLOW}[5/6] Running type checking...${NC}"
if poetry run mypy fileflow_core fileflow_config fileflow_storage fileflow_cli fileflow_api; then
    echo "  ✓ Type checking passed"
else
    echo -e "${RED}  ✗ Type checking failed${NC}"
    exit 1
fi

# Build distributions
echo -e "\n${YELLOW}[6/6] Building distributions...${NC}"
if poetry build; then
    echo "  ✓ Build successful"
else
    echo -e "${RED}  ✗ Build failed${NC}"
    exit 1
fi

# Display build artifacts
echo -e "\n${GREEN}===========================================${NC}"
echo -e "${GREEN}Build Complete!${NC}"
echo -e "${GREEN}===========================================${NC}"
echo ""
echo "Build artifacts:"
for file in dist/*; do
    if [ -f "$file" ]; then
        SIZE=$(du -h "$file" | awk '{print $1}')
        echo "  📦 $(basename "$file") ($SIZE)"
    fi
done

echo ""
echo -e "${GREEN}Next steps:${NC}"
echo "  • Test the wheel: pip install dist/fileflow-*.whl"
echo "  • Publish to PyPI: poetry publish"
echo ""
