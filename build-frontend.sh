#!/usr/bin/env bash
# Production build script for FileFlow Manager frontend
# Builds Tauri application with Svelte frontend for macOS

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}===========================================${NC}"
echo -e "${GREEN}FileFlow Manager - Frontend Build${NC}"
echo -e "${GREEN}===========================================${NC}"
echo ""

# Check prerequisites
echo -e "${YELLOW}[1/8] Checking prerequisites...${NC}"

if ! command -v node &> /dev/null; then
    echo -e "${RED}Error: Node.js is not installed${NC}"
    exit 1
fi

NODE_VERSION=$(node --version)
echo "  ✓ Node.js $NODE_VERSION"

if ! command -v pnpm &> /dev/null; then
    echo -e "${RED}Error: pnpm is not installed${NC}"
    echo "  Install with: npm install -g pnpm"
    exit 1
fi

PNPM_VERSION=$(pnpm --version)
echo "  ✓ pnpm $PNPM_VERSION"

if ! command -v cargo &> /dev/null; then
    echo -e "${RED}Error: Rust/Cargo is not installed${NC}"
    echo "  Install from: https://rustup.rs"
    exit 1
fi

CARGO_VERSION=$(cargo --version | awk '{print $2}')
echo "  ✓ Cargo $CARGO_VERSION"

# Navigate to frontend directory
cd "$(dirname "$0")/frontend"

# Clean previous builds
echo -e "\n${YELLOW}[2/8] Cleaning previous builds...${NC}"
rm -rf dist/ src-tauri/target/release/
echo "  ✓ Build directories cleaned"

# Install dependencies
echo -e "\n${YELLOW}[3/8] Installing dependencies...${NC}"
pnpm install --frozen-lockfile
echo "  ✓ Dependencies installed"

# Run linting
echo -e "\n${YELLOW}[4/8] Running linting checks...${NC}"
if pnpm lint; then
    echo "  ✓ ESLint passed"
else
    echo -e "${RED}  ✗ ESLint failed${NC}"
    exit 1
fi

# Run type checking
echo -e "\n${YELLOW}[5/8] Running type checking...${NC}"
if pnpm type-check; then
    echo "  ✓ TypeScript check passed"
else
    echo -e "${RED}  ✗ TypeScript check failed${NC}"
    exit 1
fi

if pnpm check; then
    echo "  ✓ Svelte check passed"
else
    echo -e "${RED}  ✗ Svelte check failed${NC}"
    exit 1
fi

# Build Vite frontend
echo -e "\n${YELLOW}[6/8] Building Vite frontend...${NC}"
if pnpm build; then
    echo "  ✓ Vite build successful"
else
    echo -e "${RED}  ✗ Vite build failed${NC}"
    exit 1
fi

# Build Tauri application
echo -e "\n${YELLOW}[7/8] Building Tauri application...${NC}"
if pnpm tauri build; then
    echo "  ✓ Tauri build successful"
else
    echo -e "${RED}  ✗ Tauri build failed${NC}"
    exit 1
fi

# Locate build artifacts
echo -e "\n${YELLOW}[8/8] Locating build artifacts...${NC}"

DMG_FILE=$(find src-tauri/target/release/bundle/dmg -name "*.dmg" 2>/dev/null | head -1)
APP_FILE=$(find src-tauri/target/release/bundle/macos -name "*.app" 2>/dev/null | head -1)

# Display build artifacts
echo -e "\n${GREEN}===========================================${NC}"
echo -e "${GREEN}Build Complete!${NC}"
echo -e "${GREEN}===========================================${NC}"
echo ""
echo "Build artifacts:"

if [ -n "$DMG_FILE" ] && [ -f "$DMG_FILE" ]; then
    SIZE=$(du -h "$DMG_FILE" | awk '{print $1}')
    echo "  💿 $(basename "$DMG_FILE") ($SIZE)"
    echo "     Location: $DMG_FILE"
fi

if [ -n "$APP_FILE" ] && [ -d "$APP_FILE" ]; then
    SIZE=$(du -sh "$APP_FILE" | awk '{print $1}')
    echo "  📱 $(basename "$APP_FILE") ($SIZE)"
    echo "     Location: $APP_FILE"
fi

echo ""
echo -e "${GREEN}Next steps:${NC}"
echo "  • Test the DMG: open \"$DMG_FILE\""
echo "  • Test the app: open \"$APP_FILE\""
echo "  • Sign for distribution: codesign --deep --force --verify --verbose --sign \"Developer ID\" \"$APP_FILE\""
echo "  • Notarize: xcrun notarytool submit \"$DMG_FILE\""
echo ""
