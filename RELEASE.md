# Release Process

This document explains how to create a new release of FileFlow Manager with automated DMG building and GitHub Release creation.

## Automated Release Workflow

The project uses GitHub Actions to automatically build and release the macOS DMG when you create a version tag.

### How to Create a New Release

1. **Update Version Numbers**

   Use the automated version bump script (recommended):
   ```bash
   ./scripts/bump-version.sh [patch|minor|major|VERSION]
   ```

   Examples:
   ```bash
   ./scripts/bump-version.sh patch    # 0.1.0 -> 0.1.1
   ./scripts/bump-version.sh minor    # 0.1.0 -> 0.2.0
   ./scripts/bump-version.sh major    # 0.1.0 -> 1.0.0
   ./scripts/bump-version.sh 1.2.3    # Set to 1.2.3
   ```

   This automatically updates:
   - `backend/pyproject.toml`
   - `frontend/package.json`
   - `frontend/src-tauri/tauri.conf.json`
   - `frontend/src-tauri/Cargo.toml`

2. **Commit the Version Changes**

   ```bash
   git add -A
   git commit -m "Bump version to 1.0.0"
   git push
   ```

3. **Create and Push a Version Tag**

   ```bash
   git tag v1.0.0
   git push origin v1.0.0
   ```

   **Important**: The tag must start with `v` (e.g., `v1.0.0`, `v1.2.3-beta`)

4. **Wait for the Build**

   - GitHub Actions will automatically start building
   - Go to: `https://github.com/YOUR_USERNAME/YOUR_REPO/actions`
   - Watch the "Release" workflow progress
   - Build typically takes 10-15 minutes on macOS runners

5. **Release is Published**

   Once complete, the release will be available at:
   - `https://github.com/YOUR_USERNAME/YOUR_REPO/releases`
   - The DMG will be attached as a downloadable asset

## What the Workflow Does

The `.github/workflows/release.yml` workflow:

1. ✅ Builds the Python backend executable with PyInstaller
2. ✅ Installs frontend dependencies
3. ✅ Builds the Tauri app (including DMG creation)
4. ✅ Creates a GitHub Release
5. ✅ Uploads the DMG as a release asset

## Manual Build (for testing)

### Quick Setup

Use the automated setup script to install all dependencies:

```bash
./setup.sh
```

This will:
- Check prerequisites (Python 3.10+, Poetry, Node.js, pnpm, Rust)
- Install backend dependencies
- Install frontend dependencies
- Run quality checks
- Verify installation

### Build Backend Package

Build Python wheel and source distribution:

```bash
cd backend
./build.sh
```

Creates:
- `dist/fileflow-X.Y.Z-py3-none-any.whl`
- `dist/fileflow-X.Y.Z.tar.gz`

### Build Backend Executable

Build standalone executable for Tauri:

```bash
cd backend
./build_executable.sh
```

Creates:
- `dist/fileflow-backend/fileflow-backend`
- Architecture-specific symlinks

### Build Frontend/DMG

Build macOS application with Tauri:

```bash
cd frontend
./build-release.sh
```

This will:
- Check backend binary exists
- Create architecture-specific symlinks
- Run quality checks (type check, lint, format)
- Build Tauri DMG

The DMG will be located at:
```
frontend/src-tauri/target/release/bundle/dmg/FileFlow Manager_X.Y.Z_*.dmg
```

## Release Checklist

Before creating a release:

- [ ] All tests passing in CI
- [ ] Version numbers updated in both files
- [ ] CHANGELOG updated (if you maintain one)
- [ ] Any breaking changes documented
- [ ] Manual testing completed on macOS

## Troubleshooting

### Build fails with "fileflow-backend not found"
- Make sure the backend build step completed successfully
- Check the workflow logs for PyInstaller errors

### DMG signing issues
- For public releases, you'll need to configure code signing
- Update `tauri.conf.json` with your signing identity
- Add signing secrets to GitHub repository settings

### Workflow doesn't trigger
- Ensure the tag starts with `v`
- Check that the tag was pushed: `git push origin --tags`
- Verify the workflow file is in the default branch

## Version Naming Convention

Follow semantic versioning:
- `v1.0.0` - Major release
- `v1.1.0` - Minor release (new features)
- `v1.0.1` - Patch release (bug fixes)
- `v1.0.0-beta.1` - Pre-release

## Updating the Release Notes

After the automatic release is created, you can edit it on GitHub to:
- Add detailed changelog
- Include screenshots
- Highlight key features
- Add upgrade instructions
