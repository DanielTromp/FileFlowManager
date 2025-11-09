#!/usr/bin/env bash
#
# FileFlow Version Bump Script
# Updates version in all necessary files
#

set -e  # Exit on error

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Usage function
usage() {
    echo "Usage: $0 [patch|minor|major|VERSION]"
    echo ""
    echo "Examples:"
    echo "  $0 patch      # 0.1.0 -> 0.1.1"
    echo "  $0 minor      # 0.1.0 -> 0.2.0"
    echo "  $0 major      # 0.1.0 -> 1.0.0"
    echo "  $0 1.2.3      # Set to specific version 1.2.3"
    exit 1
}

if [ $# -ne 1 ]; then
    usage
fi

BUMP_TYPE=$1

# Get project root (one level up from scripts/)
cd "$(dirname "$0")/.."
PROJECT_ROOT=$(pwd)

echo -e "${BLUE}FileFlow Version Bump${NC}"
echo ""

# Get current version from backend pyproject.toml
CURRENT_VERSION=$(cd backend && poetry version -s)
echo "Current version: ${YELLOW}$CURRENT_VERSION${NC}"

# Bump version in backend
cd backend
case "$BUMP_TYPE" in
    patch|minor|major)
        NEW_VERSION=$(poetry version "$BUMP_TYPE" -s)
        ;;
    *)
        # Assume it's a specific version
        poetry version "$BUMP_TYPE"
        NEW_VERSION=$(poetry version -s)
        ;;
esac

echo "New version:     ${GREEN}$NEW_VERSION${NC}"
echo ""

cd "$PROJECT_ROOT"

# Update frontend package.json
echo "Updating frontend/package.json..."
cd frontend
npm version "$NEW_VERSION" --no-git-tag-version --allow-same-version
cd "$PROJECT_ROOT"

# Update Tauri config
echo "Updating frontend/src-tauri/tauri.conf.json..."
if [ -f "frontend/src-tauri/tauri.conf.json" ]; then
    # Use sed to update version in Tauri config (macOS compatible)
    if [[ "$OSTYPE" == "darwin"* ]]; then
        sed -i '' "s/\"version\": \".*\"/\"version\": \"$NEW_VERSION\"/" frontend/src-tauri/tauri.conf.json
    else
        sed -i "s/\"version\": \".*\"/\"version\": \"$NEW_VERSION\"/" frontend/src-tauri/tauri.conf.json
    fi
fi

# Update Cargo.toml
echo "Updating frontend/src-tauri/Cargo.toml..."
if [ -f "frontend/src-tauri/Cargo.toml" ]; then
    if [[ "$OSTYPE" == "darwin"* ]]; then
        sed -i '' "s/^version = \".*\"/version = \"$NEW_VERSION\"/" frontend/src-tauri/Cargo.toml
    else
        sed -i "s/^version = \".*\"/version = \"$NEW_VERSION\"/" frontend/src-tauri/Cargo.toml
    fi
fi

echo ""
echo -e "${GREEN}✓ Version updated to $NEW_VERSION in:${NC}"
echo "  • backend/pyproject.toml"
echo "  • frontend/package.json"
echo "  • frontend/src-tauri/tauri.conf.json"
echo "  • frontend/src-tauri/Cargo.toml"
echo ""
echo "Next steps:"
echo "  1. Review changes: git diff"
echo "  2. Commit changes: git add -A && git commit -m \"Bump version to $NEW_VERSION\""
echo "  3. Create tag: git tag v$NEW_VERSION"
echo "  4. Push: git push && git push --tags"
echo ""
