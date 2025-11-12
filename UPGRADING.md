# Upgrading FileFlow Manager

This guide helps you upgrade FileFlow Manager to newer versions and migrate your configuration and data safely.

## Table of Contents

- [Before You Upgrade](#before-you-upgrade)
- [Backup Your Data](#backup-your-data)
- [Upgrade Methods](#upgrade-methods)
- [Version-Specific Migration](#version-specific-migration)
- [Configuration Migration](#configuration-migration)
- [Database Migration](#database-migration)
- [Rollback Procedure](#rollback-procedure)
- [Troubleshooting Upgrades](#troubleshooting-upgrades)

## Before You Upgrade

### Check Current Version

**DMG Installation**:
```bash
# Check installed version
/Applications/FileFlow\ Manager.app/Contents/Resources/backend/fileflow-backend --version
```

**Development Installation**:
```bash
cd backend
poetry run fileflow --version
```

### Review Release Notes

Before upgrading, review the release notes for:
- **Breaking changes**: Changes that may affect your configuration or workflows
- **New features**: Features you might want to use
- **Bug fixes**: Issues that have been resolved
- **Migration steps**: Special steps required for this upgrade

Release notes: https://github.com/DanielTromp/Filefly-specify/releases

### Compatibility Check

**macOS Version**:
- Minimum: macOS 10.15 (Catalina)
- Recommended: macOS 12.0+ (Monterey)

**Python Version** (Development only):
- Minimum: Python 3.10
- Recommended: Python 3.11+

**Node.js Version** (Development only):
- Minimum: Node.js 18.0
- Recommended: Node.js 20+

## Backup Your Data

**ALWAYS backup before upgrading!**

### Backup Script

```bash
#!/bin/bash
# backup-fileflow.sh

BACKUP_DIR="$HOME/FileFlow-Backups/$(date +%Y%m%d-%H%M%S)"
mkdir -p "$BACKUP_DIR"

echo "Backing up FileFlow data to: $BACKUP_DIR"

# Backup configuration
if [ -d "$HOME/.config/fileflow" ]; then
    echo "Backing up configuration..."
    cp -r "$HOME/.config/fileflow" "$BACKUP_DIR/config"
fi

# Backup database and logs
if [ -d "$HOME/.local/share/fileflow" ]; then
    echo "Backing up database and logs..."
    cp -r "$HOME/.local/share/fileflow" "$BACKUP_DIR/data"
fi

# Export current configuration
if [ -f "$HOME/.config/fileflow/fileflow.toml" ]; then
    echo "Exporting configuration..."
    cp "$HOME/.config/fileflow/fileflow.toml" "$BACKUP_DIR/fileflow-config-export.toml"
fi

echo "Backup complete: $BACKUP_DIR"
echo "Backup contains:"
ls -lh "$BACKUP_DIR"
```

### Manual Backup

```bash
# Create backup directory
mkdir -p ~/FileFlow-Backups/$(date +%Y%m%d)

# Backup configuration
cp -r ~/.config/fileflow ~/FileFlow-Backups/$(date +%Y%m%d)/config

# Backup database and logs
cp -r ~/.local/share/fileflow ~/FileFlow-Backups/$(date +%Y%m%d)/data
```

### What to Backup

1. **Configuration** (`~/.config/fileflow/`):
   - `fileflow.toml` - Your rules and settings
   - Custom configurations

2. **Database** (`~/.local/share/fileflow/`):
   - `fileflow.db` - Operation history
   - Checksum cache

3. **Logs** (`~/.local/share/fileflow/`):
   - `fileflow.log` - Recent activity logs

## Upgrade Methods

### Method 1: DMG Upgrade (End Users)

**Steps**:

1. **Backup your data** (see above)

2. **Download new DMG** from releases page

3. **Quit FileFlow** if running:
   ```bash
   # Force quit if needed
   pkill -9 "FileFlow Manager"
   ```

4. **Install new version**:
   - Open the new DMG
   - Drag FileFlow Manager to Applications (replace existing)
   - Eject DMG

5. **First launch**:
   - Right-click > Open (if unsigned)
   - Allow security permissions if prompted

6. **Verify upgrade**:
   - Configuration should be preserved
   - Check operation history is intact
   - Test basic operations

### Method 2: Development Upgrade

**Steps**:

1. **Backup your data** (see above)

2. **Update code**:
   ```bash
   cd /path/to/Filefly-specify

   # Stash any local changes
   git stash

   # Pull latest changes
   git pull origin main

   # Apply stashed changes if needed
   git stash pop
   ```

3. **Update backend dependencies**:
   ```bash
   cd backend

   # Update Poetry itself
   poetry self update

   # Update dependencies
   poetry update

   # Or for specific packages
   poetry update typer pydantic
   ```

4. **Update frontend dependencies**:
   ```bash
   cd frontend

   # Update pnpm
   npm install -g pnpm@latest

   # Update dependencies
   pnpm update

   # Or update specific packages
   pnpm update @tauri-apps/cli
   ```

5. **Run migrations** (if needed):
   ```bash
   cd backend
   poetry run python -m fileflow_storage.migrations upgrade
   ```

6. **Rebuild**:
   ```bash
   # Backend
   cd backend
   poetry install

   # Frontend
   cd frontend
   pnpm install
   pnpm tauri build
   ```

## Version-Specific Migration

### Upgrading to 1.0.0 (From Beta)

**Breaking Changes**:
- None expected (first stable release)

**New Features**:
- UI polish (loading spinners, dark mode)
- European date formats
- Automated releases

**Migration Steps**:
1. Backup data
2. Install new version
3. Configuration is compatible (no changes needed)

### Upgrading to 0.2.0 (From 0.1.x)

**Breaking Changes**:
- Configuration format changes (if any)
- Database schema updates

**Migration Steps**:

1. **Export old configuration**:
   ```bash
   cd backend
   poetry run fileflow config-export ~/old-config-backup.toml
   ```

2. **Upgrade application**

3. **Import configuration**:
   ```bash
   # After upgrade
   poetry run fileflow config-import-merge ~/old-config-backup.toml
   ```

4. **Verify rules**:
   ```bash
   poetry run fileflow rules list
   ```

### Future Version Migrations

Version-specific migration instructions will be added here as new versions are released.

## Configuration Migration

### Configuration Format Changes

If a new version changes the configuration format:

1. **Export current config**:
   ```bash
   cd backend
   poetry run fileflow config-export ~/pre-upgrade-config.toml
   ```

2. **Upgrade application**

3. **Compare configurations**:
   ```bash
   # Old config
   cat ~/pre-upgrade-config.toml

   # New default config
   cat ~/.config/fileflow/fileflow.toml
   ```

4. **Migrate settings manually**:
   - Copy rules from old config to new
   - Update any renamed settings
   - Add new required settings

5. **Validate new config**:
   ```bash
   poetry run fileflow config-validate
   ```

### Migrating Rules

If you have many custom rules:

```bash
# Extract rules from old config
grep -A 20 "\[\[rules\]\]" ~/pre-upgrade-config.toml > ~/rules-backup.toml

# Review and manually add to new config
# Edit ~/.config/fileflow/fileflow.toml
# Paste rules under [[rules]] section

# Validate
poetry run fileflow config-validate
```

### Environment Variable Changes

If environment variable handling changes:

```toml
# Old format (example - not actual breaking change)
screenshot_source = "~/Desktop"

# New format
screenshot_source = "${DESKTOP}"
```

Update your configuration accordingly.

## Database Migration

### Automatic Migration

FileFlow includes automatic database migration:

```bash
cd backend

# Check migration status
poetry run python -m fileflow_storage.migrations status

# Run pending migrations
poetry run python -m fileflow_storage.migrations upgrade

# Rollback if needed
poetry run python -m fileflow_storage.migrations downgrade
```

### Manual Migration

If automatic migration fails:

1. **Backup database**:
   ```bash
   cp ~/.local/share/fileflow/fileflow.db ~/fileflow-db-backup.db
   ```

2. **Export data**:
   ```bash
   sqlite3 ~/.local/share/fileflow/fileflow.db ".dump" > ~/fileflow-dump.sql
   ```

3. **Create new database**:
   ```bash
   rm ~/.local/share/fileflow/fileflow.db
   cd backend
   poetry run fileflow scan --dry-run  # Creates new DB with latest schema
   ```

4. **Import compatible data** (manual SQL editing may be needed):
   ```bash
   sqlite3 ~/.local/share/fileflow/fileflow.db < ~/fileflow-dump.sql
   ```

### Verifying Database Migration

```bash
# Check database schema version
sqlite3 ~/.local/share/fileflow/fileflow.db "PRAGMA user_version;"

# Check table structure
sqlite3 ~/.local/share/fileflow/fileflow.db ".schema"

# Query operation history
sqlite3 ~/.local/share/fileflow/fileflow.db "SELECT COUNT(*) FROM operations;"
```

## Rollback Procedure

If the upgrade causes problems:

### DMG Installation Rollback

1. **Quit new version**:
   ```bash
   pkill -9 "FileFlow Manager"
   ```

2. **Remove new version**:
   ```bash
   rm -rf "/Applications/FileFlow Manager.app"
   ```

3. **Reinstall old version**:
   - Download old DMG from releases
   - Install old version

4. **Restore backup**:
   ```bash
   # Restore configuration
   rm -rf ~/.config/fileflow
   cp -r ~/FileFlow-Backups/[date]/config ~/.config/fileflow

   # Restore database
   rm -rf ~/.local/share/fileflow
   cp -r ~/FileFlow-Backups/[date]/data ~/.local/share/fileflow
   ```

### Development Rollback

1. **Checkout previous version**:
   ```bash
   cd /path/to/Filefly-specify

   # Find the previous version tag
   git tag -l

   # Checkout that tag
   git checkout v0.1.0
   ```

2. **Restore dependencies**:
   ```bash
   cd backend
   poetry install

   cd ../frontend
   pnpm install
   ```

3. **Restore backup** (if needed):
   ```bash
   # Restore configuration
   cp ~/FileFlow-Backups/[date]/config/fileflow.toml ~/.config/fileflow/

   # Restore database
   cp ~/FileFlow-Backups/[date]/data/fileflow.db ~/.local/share/fileflow/
   ```

## Troubleshooting Upgrades

### "Configuration invalid" After Upgrade

**Solution**:
```bash
# Backup current config
cp ~/.config/fileflow/fileflow.toml ~/fileflow-invalid.toml

# Reset to defaults
cd backend
poetry run fileflow config-reset

# Manually merge your rules
# Compare ~/fileflow-invalid.toml with ~/.config/fileflow/fileflow.toml
# Copy rules and settings that are still valid
```

### "Database schema mismatch" Error

**Solution**:
```bash
cd backend

# Run migrations
poetry run python -m fileflow_storage.migrations upgrade

# If migrations fail, recreate database
mv ~/.local/share/fileflow/fileflow.db ~/.local/share/fileflow/fileflow.db.old
poetry run fileflow scan --dry-run  # Creates new DB
```

### "Module not found" Errors

**Solution**:
```bash
# Backend
cd backend
rm -rf .venv
poetry install

# Frontend
cd frontend
rm -rf node_modules
pnpm install
```

### Old Version Still Running

**Solution**:
```bash
# Check running processes
ps aux | grep fileflow

# Kill all FileFlow processes
pkill -9 fileflow
pkill -9 "FileFlow Manager"

# Verify
ps aux | grep fileflow

# Start new version
```

### Configuration Missing After Upgrade

**Solution**:
```bash
# Restore from backup
cp ~/FileFlow-Backups/[date]/config/fileflow.toml ~/.config/fileflow/

# Or import from backup
cd backend
poetry run fileflow config-import ~/FileFlow-Backups/[date]/fileflow-config-export.toml
```

## Best Practices

### Pre-Upgrade Checklist

- [ ] Read release notes for breaking changes
- [ ] Backup configuration, database, and logs
- [ ] Export configuration to external file
- [ ] Note current version number
- [ ] Close all FileFlow instances
- [ ] Have rollback plan ready

### Post-Upgrade Checklist

- [ ] Verify configuration is intact
- [ ] Check operation history is accessible
- [ ] Test basic operations (scan, rules list)
- [ ] Verify GUI works correctly
- [ ] Check logs for errors
- [ ] Test new features

### Upgrade Testing (Development)

Before upgrading production:

1. **Test in development environment**:
   ```bash
   # Create test environment
   mkdir -p ~/fileflow-test
   cd ~/fileflow-test
   git clone https://github.com/DanielTromp/Filefly-specify.git
   cd Filefly-specify
   git checkout v1.0.0  # New version
   ```

2. **Copy production data to test**:
   ```bash
   # Use separate config for testing
   export FILEFLOW_CONFIG=~/fileflow-test/config.toml
   cp ~/.config/fileflow/fileflow.toml ~/fileflow-test/config.toml
   ```

3. **Test upgrade** in test environment

4. **If successful**, upgrade production

## Getting Help

If you encounter issues during upgrade:

1. **Check this guide** for troubleshooting steps
2. **Review logs**: `~/.local/share/fileflow/fileflow.log`
3. **Consult [TROUBLESHOOTING.md](TROUBLESHOOTING.md)**
4. **Open a GitHub Issue** with:
   - Old version number
   - New version number
   - Upgrade method (DMG or development)
   - Error messages and logs
   - Steps you've already tried

## Downgrade Support

**Downgrades are not officially supported** but can be done:

1. **Backup everything**
2. **Uninstall current version**
3. **Install old version**
4. **Restore backups**
5. **Note**: Database may be incompatible (may lose operation history)

## Future Upgrade Paths

This document will be updated with each release to include:
- Version-specific migration instructions
- Breaking changes and workarounds
- New features requiring configuration changes
- Database schema migrations

**Stay Updated**: Watch the repository for release notifications.

## Migration Support Timeline

- **Beta versions (0.x.x)**: Best effort support, breaking changes possible
- **Stable versions (1.x.x)**: Full migration support, backward compatibility maintained
- **Major versions (2.0.0+)**: Migration guides provided, may have breaking changes

Thank you for using FileFlow Manager!
