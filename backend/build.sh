#!/usr/bin/env bash
#
# FileFlow Backend - Build Script
# Creates distributable packages (wheel and source distribution)
#

set -e  # Exit on error

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}Building FileFlow Backend...${NC}"
echo ""

# Clean previous builds
if [ -d "dist" ]; then
    echo "Cleaning previous builds..."
    rm -rf dist/
fi

# Run quality checks first
echo "Running quality checks..."
echo -n "  Linting (Ruff)... "
if poetry run ruff check . --quiet; then
    echo -e "${GREEN}✓${NC}"
else
    echo "Failed"
    exit 1
fi

echo -n "  Type checking (mypy)... "
if poetry run mypy fileflow_core fileflow_config fileflow_storage fileflow_cli fileflow_api --no-error-summary 2>/dev/null; then
    echo -e "${GREEN}✓${NC}"
else
    echo "Warning: Type checking found issues (continuing anyway)"
fi

echo -n "  Tests (pytest)... "
if poetry run pytest --quiet 2>/dev/null; then
    echo -e "${GREEN}✓${NC}"
else
    echo "Warning: Tests found issues (continuing anyway)"
fi

echo ""
echo "Building packages..."

# Build with Poetry
poetry build

echo ""
echo -e "${GREEN}Build complete!${NC}"
echo ""
echo "Artifacts created in dist/:"
ls -lh dist/

echo ""
echo "To install locally:"
echo "  pip install dist/fileflow-*.whl"
echo ""
echo "To publish to PyPI:"
echo "  poetry publish"
echo ""
