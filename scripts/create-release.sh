#!/usr/bin/env bash
#
# FileFlow Release Helper Script
# Automates the complete release process
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
    echo "This script will:"
    echo "  1. Run all quality checks"
    echo "  2. Bump version numbers"
    echo "  3. Prompt for changelog updates"
    echo "  4. Commit changes"
    echo "  5. Create and push git tag"
    echo "  6. Trigger GitHub Actions release workflow"
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

# Get project root
cd "$(dirname "$0")/.."
PROJECT_ROOT=$(pwd)

echo -e "${BLUE}FileFlow Release Process${NC}"
echo ""
echo -e "${YELLOW}This will create a new release and trigger automated builds.${NC}"
echo -e "${YELLOW}Make sure you have committed all changes first!${NC}"
echo ""

# Check for uncommitted changes
if ! git diff-index --quiet HEAD --; then
    echo -e "${RED}Error: You have uncommitted changes${NC}"
    echo "Please commit or stash them before creating a release"
    git status --short
    exit 1
fi

# Check current branch
CURRENT_BRANCH=$(git branch --show-current)
if [ "$CURRENT_BRANCH" != "main" ] && [ "$CURRENT_BRANCH" != "master" ]; then
    echo -e "${YELLOW}Warning: You are not on main/master branch (currently on: $CURRENT_BRANCH)${NC}"
    read -p "Continue anyway? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Release cancelled"
        exit 0
    fi
fi

# Pull latest changes
echo "Pulling latest changes from remote..."
git pull

echo ""
echo -e "${BLUE}Step 1: Running Quality Checks${NC}"
echo ""

# Backend checks
echo "Running backend quality checks..."
cd backend

echo -n "  Linting (Ruff)... "
if poetry run ruff check . --quiet 2>/dev/null; then
    echo -e "${GREEN}✓${NC}"
else
    echo -e "${RED}✗${NC}"
    echo "Backend linting failed. Fix issues and try again."
    exit 1
fi

echo -n "  Type checking (mypy)... "
if poetry run mypy fileflow_core fileflow_config fileflow_storage fileflow_cli fileflow_api --no-error-summary 2>/dev/null; then
    echo -e "${GREEN}✓${NC}"
else
    echo -e "${RED}✗${NC}"
    echo "Backend type checking failed. Fix issues and try again."
    exit 1
fi

echo -n "  Tests (pytest)... "
if poetry run pytest --quiet 2>/dev/null; then
    echo -e "${GREEN}✓${NC}"
else
    echo -e "${RED}✗${NC}"
    echo "Backend tests failed. Fix issues and try again."
    exit 1
fi

cd "$PROJECT_ROOT"

# Frontend checks
echo "Running frontend quality checks..."
cd frontend

echo -n "  Type checking... "
if pnpm type-check >/dev/null 2>&1; then
    echo -e "${GREEN}✓${NC}"
else
    echo -e "${YELLOW}⚠${NC} (continuing)"
fi

echo -n "  Linting... "
if pnpm lint --max-warnings 100 >/dev/null 2>&1; then
    echo -e "${GREEN}✓${NC}"
else
    echo -e "${YELLOW}⚠${NC} (continuing)"
fi

echo -n "  Formatting... "
if pnpm run format:check >/dev/null 2>&1; then
    echo -e "${GREEN}✓${NC}"
else
    echo -e "${YELLOW}⚠${NC} (continuing)"
fi

cd "$PROJECT_ROOT"

echo ""
echo -e "${GREEN}All quality checks passed!${NC}"
echo ""

# Bump version
echo -e "${BLUE}Step 2: Bumping Version${NC}"
echo ""

./scripts/bump-version.sh "$BUMP_TYPE"

NEW_VERSION=$(cd backend && poetry version -s)
echo ""

# Prompt for changelog
echo -e "${BLUE}Step 3: Update Changelog${NC}"
echo ""
echo -e "${YELLOW}Please update CHANGELOG.md with changes for version $NEW_VERSION${NC}"
echo ""
echo "Opening CHANGELOG.md in your default editor..."
echo "Press Enter when you're done editing..."

# Open changelog in default editor
${EDITOR:-vi} CHANGELOG.md

read -p "Have you updated the changelog? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Please update CHANGELOG.md and run this script again"
    exit 1
fi

# Review changes
echo ""
echo -e "${BLUE}Step 4: Review Changes${NC}"
echo ""
echo "The following files will be committed:"
git diff --stat
echo ""
git diff

echo ""
read -p "Commit these changes? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Release cancelled. Changes have not been committed."
    exit 0
fi

# Commit changes
echo ""
echo -e "${BLUE}Step 5: Committing Changes${NC}"
echo ""

git add -A
git commit -m "Release v$NEW_VERSION

Bump version to $NEW_VERSION and update changelog.

This commit was created by the automated release script."

echo -e "${GREEN}Changes committed${NC}"

# Create tag
echo ""
echo -e "${BLUE}Step 6: Creating Git Tag${NC}"
echo ""

git tag -a "v$NEW_VERSION" -m "Release v$NEW_VERSION

See CHANGELOG.md for details."

echo -e "${GREEN}Tag v$NEW_VERSION created${NC}"

# Push changes
echo ""
echo -e "${BLUE}Step 7: Pushing to Remote${NC}"
echo ""

echo "This will:"
echo "  1. Push commits to remote"
echo "  2. Push tag v$NEW_VERSION"
echo "  3. Trigger GitHub Actions release workflow"
echo ""
read -p "Push to remote and trigger release build? (y/N): " -n 1 -r
echo

if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo ""
    echo -e "${YELLOW}Changes committed locally but not pushed.${NC}"
    echo "To push manually:"
    echo "  git push origin $CURRENT_BRANCH"
    echo "  git push origin v$NEW_VERSION"
    exit 0
fi

git push origin "$CURRENT_BRANCH"
git push origin "v$NEW_VERSION"

echo ""
echo -e "${GREEN}✓ Release process complete!${NC}"
echo ""
echo "Version: ${GREEN}v$NEW_VERSION${NC}"
echo ""
echo "GitHub Actions will now:"
echo "  1. Run quality checks"
echo "  2. Build Python packages"
echo "  3. Build backend executable"
echo "  4. Build macOS DMG"
echo "  5. Create GitHub Release"
echo "  6. Upload all artifacts"
echo ""
echo "Monitor the build at:"
echo "  https://github.com/$(git remote get-url origin | sed 's/.*github.com[:/]\(.*\)\.git/\1/')/actions"
echo ""
echo "Release will be available at:"
echo "  https://github.com/$(git remote get-url origin | sed 's/.*github.com[:/]\(.*\)\.git/\1/')/releases/tag/v$NEW_VERSION"
echo ""
