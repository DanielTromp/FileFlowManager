#!/usr/bin/env bash
#
# FileFlow Frontend - Release Build Script
# Creates production DMG build with all optimizations
#

set -e  # Exit on error

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}Building FileFlow Manager for macOS (DMG)...${NC}"
echo ""

# Get project root
cd "$(dirname "$0")"

# Ensure backend binary is built first
echo "Checking backend binary..."
if [ ! -f "../backend/dist/fileflow-backend/fileflow-backend" ]; then
    echo -e "${YELLOW}Backend binary not found. Building...${NC}"
    cd ../backend

    # Create executable with PyInstaller or similar
    if ! ./build_executable.sh; then
        echo -e "${RED}Failed to build backend binary${NC}"
        exit 1
    fi

    cd ../frontend
    echo -e "${GREEN}✓ Backend binary built${NC}"
else
    echo -e "${GREEN}✓ Backend binary found${NC}"
fi

# Check architecture-specific symlinks
echo "Checking architecture-specific symlinks..."
ARCH=$(uname -m)
if [ "$ARCH" = "arm64" ] || [ "$ARCH" = "aarch64" ]; then
    BACKEND_LINK="../backend/dist/fileflow-backend-aarch64-apple-darwin"
else
    BACKEND_LINK="../backend/dist/fileflow-backend-x86_64-apple-darwin"
fi

if [ ! -L "$BACKEND_LINK" ]; then
    echo "Creating architecture-specific symlink..."
    ln -sf fileflow-backend/fileflow-backend "$BACKEND_LINK"
    echo -e "${GREEN}✓ Symlink created: $BACKEND_LINK${NC}"
fi

echo ""
echo "Running frontend quality checks..."

# Run type checking
echo -n "  Type checking... "
if pnpm type-check >/dev/null 2>&1; then
    echo -e "${GREEN}✓${NC}"
else
    echo -e "${YELLOW}⚠ (continuing)${NC}"
fi

# Run linting
echo -n "  Linting... "
if pnpm lint --max-warnings 100 >/dev/null 2>&1; then
    echo -e "${GREEN}✓${NC}"
else
    echo -e "${YELLOW}⚠ (continuing)${NC}"
fi

# Run formatting check
echo -n "  Formatting... "
if pnpm run format:check >/dev/null 2>&1; then
    echo -e "${GREEN}✓${NC}"
else
    echo -e "${YELLOW}⚠ (continuing)${NC}"
fi

echo ""
echo "Building Tauri application..."
echo ""

# Build with Tauri
pnpm tauri build

echo ""
echo -e "${GREEN}Build complete!${NC}"
echo ""

# Find and display the DMG file
DMG_FILE=$(find src-tauri/target/release/bundle/dmg -name "*.dmg" 2>/dev/null | head -1)
if [ -n "$DMG_FILE" ]; then
    DMG_SIZE=$(du -h "$DMG_FILE" | cut -f1)
    echo "DMG created: $DMG_FILE"
    echo "Size: $DMG_SIZE"
    echo ""
    echo "To install:"
    echo "  1. Open the DMG: open \"$DMG_FILE\""
    echo "  2. Drag FileFlow Manager to Applications"
    echo ""
    echo "To distribute:"
    echo "  1. Sign the app (if you have a Developer ID)"
    echo "  2. Notarize with Apple (for Gatekeeper)"
    echo "  3. Upload to GitHub Releases"
else
    echo -e "${YELLOW}Warning: DMG file not found in expected location${NC}"
    echo "Check src-tauri/target/release/bundle/ for build artifacts"
fi

echo ""
