# Troubleshooting Guide - FileFlow Manager

This guide helps you diagnose and fix common issues with FileFlow Manager.

## Table of Contents

- [Installation Issues](#installation-issues)
- [Permission Errors](#permission-errors)
- [Configuration Problems](#configuration-problems)
- [File Operation Failures](#file-operation-failures)
- [Performance Issues](#performance-issues)
- [Database Issues](#database-issues)
- [GUI Problems](#gui-problems)
- [Build and Development Issues](#build-and-development-issues)
- [macOS-Specific Issues](#macos-specific-issues)
- [Getting Help](#getting-help)

## Installation Issues

### DMG Won't Open - "FileFlow Manager is damaged"

**Problem**: macOS blocks the app with a message about the app being damaged or from an unidentified developer.

**Solution**: This is macOS Gatekeeper protection. The app is not signed yet. Try these methods:

**Option 1: Right-click method (easiest)**
1. Locate FileFlow Manager in your Applications folder
2. Right-click (or Control-click) on the app
3. Select "Open" from the menu
4. Click "Open" in the security dialog
5. The app will now run (you only need to do this once)

**Option 2: Command line method**
```bash
xattr -d com.apple.quarantine "/Applications/FileFlow Manager.app"
```

**Option 3: System Settings method**
1. Try to open the app normally (it will be blocked)
2. Go to System Settings > Privacy & Security
3. Scroll down to find the blocked app message
4. Click "Open Anyway"

### Poetry Not Found

**Problem**: `poetry: command not found`

**Solution**:
```bash
# Install Poetry
curl -sSL https://install.python-poetry.org | python3 -

# Add to PATH
export PATH="$HOME/.local/bin:$PATH"

# Add to shell profile permanently
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc
```

### Rust Compiler Not Found

**Problem**: `error: rustc not found` or `cargo: command not found`

**Solution**:
```bash
# Install Rust
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh

# Source Rust environment
source $HOME/.cargo/env

# Add to shell profile permanently
echo 'source $HOME/.cargo/env' >> ~/.zshrc
```

### pnpm Not Found

**Problem**: `pnpm: command not found`

**Solution**:
```bash
# Install pnpm globally
npm install -g pnpm

# Or use corepack (Node.js 16.13+)
corepack enable
corepack prepare pnpm@latest --activate
```

### Python Version Too Old

**Problem**: `Python 3.10 or newer required`

**Solution**:
```bash
# Check current version
python3 --version

# Install Python 3.10+ using Homebrew
brew install python@3.10

# Or download from python.org
# https://www.python.org/downloads/
```

## Permission Errors

### "Permission denied" When Accessing Files

**Problem**: FileFlow can't read or write files in certain directories.

**Solution**: Grant Full Disk Access to Terminal or the FileFlow app.

**For Terminal** (Development):
1. System Settings > Privacy & Security > Full Disk Access
2. Click the lock icon to make changes
3. Click "+" and add Terminal.app (or iTerm2, etc.)
4. Restart Terminal

**For FileFlow App** (Production DMG):
1. System Settings > Privacy & Security > Full Disk Access
2. Click "+" and add FileFlow Manager from Applications
3. Restart the app

### "Operation not permitted" on System Directories

**Problem**: Can't access Desktop, Documents, or Downloads folders.

**Solution**: macOS requires explicit permission for these directories.

1. Run FileFlow once - it will request permission
2. Allow access in the permission dialog
3. If you denied it by mistake:
   - System Settings > Privacy & Security > Files and Folders
   - Find FileFlow Manager
   - Enable access to needed folders

### "Read-only file system" Error

**Problem**: Can't write to destination directory.

**Solution**:
```bash
# Check if destination is read-only
ls -la /path/to/destination

# Check mounted volumes
mount | grep "read-only"

# If external drive, remount with write access
diskutil unmount /Volumes/VolumeName
diskutil mount /Volumes/VolumeName
```

## Configuration Problems

### Configuration File Not Found

**Problem**: `Config file not found at ~/.config/fileflow/fileflow.toml`

**Solution**: This is normal on first run. FileFlow auto-creates the config file.

```bash
# Run any command to create default config
cd backend
poetry run fileflow scan --dry-run

# Or manually create the directory
mkdir -p ~/.config/fileflow

# The config file will be created automatically
```

### Configuration Validation Errors

**Problem**: `Invalid configuration` or `TOML parse error`

**Solution**:
```bash
# Validate configuration
cd backend
poetry run fileflow config-validate

# Check for syntax errors
cat ~/.config/fileflow/fileflow.toml

# Reset to default configuration
poetry run fileflow config-reset

# Or backup and recreate
mv ~/.config/fileflow/fileflow.toml ~/.config/fileflow/fileflow.toml.backup
poetry run fileflow scan --dry-run  # Creates new config
```

### Environment Variables Not Expanding

**Problem**: Paths like `${DESKTOP}` not being replaced with actual paths.

**Solution**: Ensure you're using supported environment variables:

```toml
# Supported variables:
screenshot_source = "${DESKTOP}"          # ~/Desktop
screenshot_destination = "${DOWNLOADS}"   # ~/Downloads
monitored_directories = ["${DOCUMENTS}"]  # ~/Documents
# Also: ${HOME}, ${PICTURES}

# NOT supported (use absolute paths):
screenshot_source = "$DESKTOP"           # Wrong - use ${DESKTOP}
screenshot_source = "~/Desktop"          # Wrong - use ${DESKTOP}
```

### Import Configuration Fails

**Problem**: `Failed to import configuration from file`

**Solution**:
```bash
# Validate the file first
cd backend
poetry run fileflow config-validate /path/to/config.toml

# Check for common issues:
# 1. File must be valid TOML
# 2. All required sections must be present
# 3. Rule IDs must be unique
# 4. Paths must be valid

# Import with merge instead of replace
poetry run fileflow config-import-merge /path/to/config.toml
```

## File Operation Failures

### Files Not Being Organized

**Problem**: Scan completes but no files are moved.

**Diagnosis**:
```bash
# Enable debug logging
# Edit ~/.config/fileflow/fileflow.toml
[general]
  log_level = "DEBUG"

# Run scan and check logs
cd backend
poetry run fileflow scan --dry-run
cat ~/.local/share/fileflow/fileflow.log
```

**Common causes**:
1. **Rules disabled**: Check `poetry run fileflow rules list`
2. **No matching files**: Verify source patterns match your files
3. **Dry-run mode**: Use `--execute` flag to actually move files
4. **Source directory wrong**: Check `source_directories` in rule config

### Duplicate Detection Not Working

**Problem**: Duplicate files not being detected.

**Solution**:
```bash
# Enable checksum cache
# Edit ~/.config/fileflow/fileflow.toml
[general]
  cache_enabled = true

# Clear and rebuild cache
cd backend
poetry run python -c "
from fileflow_storage.cache import ChecksumCache
cache = ChecksumCache()
cache.clear()
"

# Run scan again
poetry run fileflow scan --dry-run
```

### "Disk space full" Errors

**Problem**: Operation fails due to insufficient disk space.

**Solution**:
```bash
# Check available space
df -h /path/to/destination

# Clean up large files first
cd backend
poetry run fileflow files large --threshold 100  # Find files >100MB

# Free up space
poetry run fileflow files old --days 365  # Find files >1 year old
```

### File Moves Fail on External Drives

**Problem**: Files can't be moved to external drives.

**Common causes**:
1. **Drive not mounted**: Check `ls /Volumes/`
2. **Read-only mount**: See "Read-only file system" above
3. **File system incompatibility**: Some file systems don't support macOS metadata
4. **Insufficient permissions**: External drives may need special permissions

**Solution**:
```bash
# Check mount status
mount | grep /Volumes

# Remount with write access
diskutil unmount /Volumes/DriveName
diskutil mount /Volumes/DriveName

# Grant FileFlow permission to access external volumes
# System Settings > Privacy & Security > Files and Folders
```

## Performance Issues

### Scan Takes Too Long

**Problem**: File scanning is very slow.

**Solutions**:

1. **Enable checksum caching**:
   ```toml
   # Edit ~/.config/fileflow/fileflow.toml
   [general]
     cache_enabled = true
   ```

2. **Reduce monitored directories**:
   ```toml
   # Edit ~/.config/fileflow/fileflow.toml
   [paths]
     monitored_directories = [
       "${DESKTOP}",    # Only essential directories
       "${DOWNLOADS}"
     ]
   ```

3. **Adjust thread pool size**:
   ```python
   # In fileflow_core/file_scanner.py (development only)
   # Default is 4 workers, can increase for faster scanning
   ```

4. **Exclude large directories**:
   ```toml
   [[rules]]
     exclude_patterns = [
       "**/node_modules/**",
       "**/.git/**",
       "**/Library/**"
     ]
   ```

### High Memory Usage

**Problem**: FileFlow uses too much memory.

**Solution**:
```bash
# Limit concurrent operations
# Scan fewer files at once
poetry run fileflow scan --dry-run  # Processes in batches

# Clear checksum cache
cd backend
poetry run python -c "
from fileflow_storage.cache import ChecksumCache
cache = ChecksumCache()
cache.clear()
"

# Reduce monitored directories
```

### GUI Feels Sluggish

**Problem**: Frontend is slow or unresponsive.

**Solution**:
```bash
# Clear frontend cache
cd frontend
rm -rf .svelte-kit node_modules/.vite

# Reinstall dependencies
pnpm install

# Rebuild
pnpm tauri build

# For development, use release mode
pnpm tauri dev --release
```

## Database Issues

### "Database locked" Error

**Problem**: `SQLite database is locked`

**Solution**:
```bash
# Check for running FileFlow processes
ps aux | grep fileflow

# Kill all FileFlow processes
pkill -f fileflow

# If that doesn't work, remove lock file
rm ~/.config/fileflow/fileflow.db-lock

# Restart FileFlow
```

### Database Corruption

**Problem**: `Database disk image is malformed` or similar SQLite errors.

**Solution**:
```bash
# Backup current database
cp ~/.config/fileflow/fileflow.db ~/.config/fileflow/fileflow.db.backup

# Try to repair
sqlite3 ~/.config/fileflow/fileflow.db "PRAGMA integrity_check;"

# If corrupted, dump and recreate
sqlite3 ~/.config/fileflow/fileflow.db ".dump" > dump.sql
rm ~/.config/fileflow/fileflow.db
sqlite3 ~/.config/fileflow/fileflow.db < dump.sql

# If repair fails, start fresh (loses operation history)
rm ~/.config/fileflow/fileflow.db
cd backend
poetry run fileflow scan --dry-run  # Recreates database
```

### Operation History Missing

**Problem**: Can't see past operations in GUI or CLI.

**Solution**:
```bash
# Check if database exists
ls -la ~/.config/fileflow/fileflow.db

# Query database directly
sqlite3 ~/.config/fileflow/fileflow.db "SELECT COUNT(*) FROM operations;"

# If empty, run some operations
cd backend
poetry run fileflow scan --execute

# Check logs
cat ~/.local/share/fileflow/fileflow.log
```

## GUI Problems

### Tauri Dev Won't Start

**Problem**: `pnpm tauri dev` fails to start.

**Solution**:
```bash
# Check if port 5173 is in use
lsof -ti:5173

# Kill process using the port
lsof -ti:5173 | xargs kill

# Clear cache and restart
cd frontend
rm -rf node_modules/.vite
pnpm tauri dev

# Check for Rust/Cargo issues
cd src-tauri
cargo clean
cargo build
```

### "Failed to execute Python backend" Error

**Problem**: GUI can't communicate with backend.

**Solution**:
```bash
# Ensure Poetry is in PATH
which poetry

# Ensure backend dependencies are installed
cd backend
poetry install

# Test backend CLI directly
poetry run fileflow --help

# Check Tauri logs for detailed error
# Look in terminal running `pnpm tauri dev`

# Verify Python path in Tauri config
# frontend/src-tauri/src/main.rs
```

### Hot Reload Not Working

**Problem**: Changes to Svelte files don't update automatically.

**Solution**:
```bash
cd frontend

# Restart dev server
# Ctrl+C to stop
pnpm tauri dev

# Clear Vite cache
rm -rf node_modules/.vite .svelte-kit

# Check file permissions
ls -la src/

# Restart with verbose logging
RUST_LOG=debug pnpm tauri dev
```

### GUI Shows Blank Screen

**Problem**: App window is completely blank or white.

**Solution**:
```bash
# Open DevTools (if app window is visible)
# Right-click > Inspect Element
# Check Console for errors

# Rebuild frontend
cd frontend
pnpm build
pnpm tauri dev

# Check Content Security Policy
# frontend/src-tauri/tauri.conf.json
# Ensure CSP allows necessary resources
```

## Build and Development Issues

### Poetry Install Fails

**Problem**: `poetry install` fails with dependency conflicts.

**Solution**:
```bash
cd backend

# Update Poetry
curl -sSL https://install.python-poetry.org | python3 -

# Clear Poetry cache
poetry cache clear pypi --all

# Remove lock file and reinstall
rm poetry.lock
poetry install

# If still fails, use --no-cache
poetry install --no-cache
```

### pnpm Install Fails

**Problem**: `pnpm install` fails with dependency errors.

**Solution**:
```bash
cd frontend

# Clear pnpm cache
pnpm store prune

# Remove lock file and node_modules
rm -rf node_modules pnpm-lock.yaml

# Reinstall
pnpm install

# If still fails, try npm
npm install
```

### Tauri Build Fails

**Problem**: `pnpm tauri build` fails.

**Solution**:
```bash
cd frontend

# Ensure backend is built first
cd ../backend
poetry build
cd ../frontend

# Clean Rust build
cd src-tauri
cargo clean
cd ..

# Rebuild
pnpm tauri build

# Check for specific errors:
# - Missing Xcode Command Line Tools: xcode-select --install
# - Rust version too old: rustup update
# - Missing dependencies: brew install [dependency]
```

### Tests Failing

**Problem**: `pytest` or `pnpm test` fails.

**Solution**:
```bash
# Backend tests
cd backend

# Clear test cache
rm -rf .pytest_cache

# Run tests with verbose output
poetry run pytest -v

# Run specific failing test
poetry run pytest tests/path/to/test.py::test_function -v

# Check for import errors
poetry run python -c "import fileflow_core"

# Frontend tests
cd frontend

# Clear test cache
rm -rf node_modules/.vite

# Run tests
pnpm test

# Update snapshots if needed
pnpm test -- -u
```

## macOS-Specific Issues

### Screenshot Location Not Detected

**Problem**: Can't auto-detect where screenshots are saved.

**Solution**:
```bash
# Check current screenshot location
defaults read com.apple.screencapture location

# If not set, screenshots go to Desktop by default
# Set custom location
defaults write com.apple.screencapture location ~/Downloads/Screenshots
killall SystemUIServer

# Update FileFlow config
cd backend
poetry run fileflow detect-screenshots
```

### App Won't Open on Another Mac

**Problem**: DMG works on your Mac but not others.

**Solution**: This is a code signing issue. The app needs to be signed and notarized.

**Short-term workaround** (for testers):
```bash
# On the other Mac
xattr -d com.apple.quarantine "/Applications/FileFlow Manager.app"
```

**Long-term solution** (for distribution):
1. Get Apple Developer ID
2. Sign the app during build
3. Notarize with Apple
4. See [RELEASE.md](RELEASE.md) for details

### File System Events Not Working

**Problem**: FileFlow doesn't detect new files automatically.

**Note**: FileFlow currently operates in scan mode, not continuous monitoring.

**Current behavior**:
- Manual scanning only (via GUI or CLI)
- No automatic detection of new files
- Run scan when you want to organize files

**Future enhancement**: Real-time file system monitoring is planned for a future version.

## Getting Help

### Enable Debug Logging

For any issue, enable debug logging first:

```toml
# Edit ~/.config/fileflow/fileflow.toml
[general]
  log_level = "DEBUG"
```

Then check logs:
```bash
tail -f ~/.local/share/fileflow/fileflow.log
```

### Collect Diagnostic Information

When reporting issues, include:

1. **Environment**:
   ```bash
   # Run validation script
   ./validate-quickstart.sh

   # System info
   sw_vers
   python3 --version
   node --version
   rustc --version
   ```

2. **Logs**:
   ```bash
   # Last 100 lines of logs
   tail -n 100 ~/.local/share/fileflow/fileflow.log
   ```

3. **Configuration** (remove sensitive paths):
   ```bash
   cat ~/.config/fileflow/fileflow.toml
   ```

4. **Error message**: Full error text and stack trace

### Where to Get Help

1. **Check documentation**:
   - [README.md](README.md) - Overview and features
   - [quickstart.md](specs/001-fileflow-manager/quickstart.md) - Setup guide
   - [CONTRIBUTING.md](CONTRIBUTING.md) - Development guide

2. **Search existing issues**:
   - GitHub Issues: https://github.com/DanielTromp/Filefly-specify/issues

3. **Ask for help**:
   - Open a GitHub Issue with diagnostic information
   - Use the bug report template
   - Include all diagnostic information above

### Common Commands Reference

```bash
# Validation
./validate-quickstart.sh

# Reset everything
rm -rf ~/.config/fileflow ~/.local/share/fileflow
cd backend && poetry run fileflow scan --dry-run

# Check logs
tail -f ~/.local/share/fileflow/fileflow.log

# Test backend
cd backend && poetry run fileflow --help

# Test frontend
cd frontend && pnpm tauri dev

# Rebuild everything
cd backend && poetry install && poetry build
cd frontend && pnpm install && pnpm tauri build
```

## Still Having Issues?

If this guide doesn't solve your problem:

1. **Run the validation script**: `./validate-quickstart.sh`
2. **Enable debug logging**: Set `log_level = "DEBUG"` in config
3. **Open a GitHub Issue**: Include all diagnostic information
4. **Be patient**: We'll help you resolve the issue

Thank you for using FileFlow Manager!
