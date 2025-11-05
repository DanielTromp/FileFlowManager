# FileFlow Backend

Python backend for FileFlow Manager - intelligent automated file organization system for macOS.

## Overview

The FileFlow backend provides:
- **Rule-based file organization engine** with priority ordering and pattern matching
- **SHA-256 duplicate detection** with checksum caching for performance
- **SQLite database** for operation history and cache management
- **TOML configuration** with environment variable expansion
- **Full-featured CLI** with 20+ commands (via Typer)
- **Tauri IPC handlers** for GUI integration (via Poetry script invocation)
- **Atomic file operations** with metadata preservation

## Architecture

```
backend/
├── fileflow_core/          # Core file operations and business logic
│   ├── models.py           # Pydantic data models (Config, Rule, FileMetadata, OperationRecord)
│   ├── file_scanner.py     # Parallel directory scanning with ThreadPoolExecutor
│   ├── file_operations.py  # Atomic file moves/deletes with error handling
│   ├── duplicate_detector.py  # SHA-256 checksum calculation and comparison
│   ├── date_organizer.py   # Date extraction and path generation (YYYY/MM/DD)
│   ├── rule_engine.py      # Rule matching and execution with dry-run support
│   ├── logging_config.py   # Structured logging configuration
│   └── exceptions.py       # Custom exceptions (ConfigError, DatabaseError, etc.)
│
├── fileflow_config/        # Configuration management
│   ├── config_manager.py   # TOML read/write with validation and env var expansion
│   ├── rule_schema.py      # Rule validation and priority management
│   └── defaults.py         # Default configuration and rules
│
├── fileflow_storage/       # Data persistence
│   ├── database.py         # SQLite operations (operation history, file tracking)
│   ├── cache.py            # Checksum cache (avoid recalculation)
│   └── migrations.py       # Database schema migrations
│
├── fileflow_cli/           # Command-line interface
│   ├── __main__.py         # Entry point (python -m fileflow_cli)
│   └── commands.py         # Typer commands (20+ commands across 5 categories)
│
└── fileflow_api/           # Tauri IPC integration
    └── tauri_commands.py   # JSON-based command handlers for frontend
```

## Installation

### Prerequisites
- Python 3.10 or newer
- Poetry 1.6+ for dependency management

### Install Dependencies

```bash
cd backend
poetry install
```

This installs all dependencies including:
- `typer` - CLI framework
- `pydantic` - Data validation
- `rich` - Terminal formatting
- `pytest` - Testing framework

## Usage

### CLI Commands (20+ commands)

#### File Organization

```bash
# Scan and organize files (dry-run by default)
poetry run fileflow scan

# Execute file operations (skips dry-run)
poetry run fileflow scan --execute
```

#### Rule Management

```bash
# List all organization rules
poetry run fileflow rules list

# Show detailed rule information
poetry run fileflow rules show <rule-id>

# Create new rule (interactive prompts)
poetry run fileflow rules create

# Update existing rule
poetry run fileflow rules update <rule-id> --name "New Name" --priority 5

# Delete rule
poetry run fileflow rules delete <rule-id>

# Enable/disable rules
poetry run fileflow rules enable <rule-id>
poetry run fileflow rules disable <rule-id>
```

#### File Discovery

```bash
# Find large files (>100MB by default)
poetry run fileflow files large

# Find old files (>90 days by default)
poetry run fileflow files old

# Delete specified files
poetry run fileflow files delete <path1> <path2> ...
```

#### Configuration Management

```bash
# Show current configuration
poetry run fileflow config-show

# Export configuration to file
poetry run fileflow config-export ~/backup.toml

# Import configuration (replaces existing)
poetry run fileflow config-import ~/backup.toml

# Import and merge (adds rules, keeps existing)
poetry run fileflow config-import-merge ~/backup.toml

# Validate configuration file
poetry run fileflow config-validate [path]

# Edit configuration in $EDITOR
poetry run fileflow config-edit

# Reset to default configuration
poetry run fileflow config-reset [--force] [--keep-rules]
```

#### Utilities

```bash
# Auto-detect macOS screenshot save location
poetry run fileflow detect-screenshots
```

### Configuration

Configuration is stored in `~/.config/fileflow/fileflow.toml` and auto-created on first run.

**Example Configuration**:

```toml
[general]
  log_level = "INFO"
  enable_notifications = true
  cache_enabled = true

[paths]
  screenshot_source = "${DESKTOP}"
  screenshot_destination = "${DOWNLOADS}/screenshots"
  monitored_directories = ["${DESKTOP}", "${DOWNLOADS}"]

[thresholds]
  large_file_mb = 100
  old_file_days = 90

[[rules]]
  id = "screenshot-org"
  enabled = true
  name = "Screenshot Organization"
  description = "Automatically organize screenshots by date"
  source_patterns = ["Screenshot*.png", "Screen Shot*.png"]
  source_directories = ["${DESKTOP}", "${DOWNLOADS}"]
  destination = "${DOWNLOADS}/screenshots"
  organize_by_date = true
  file_types = ["png", "jpg", "jpeg"]
  priority = 1
```

**Environment Variables Supported**:
- `${HOME}` - User home directory
- `${DESKTOP}` - ~/Desktop
- `${DOWNLOADS}` - ~/Downloads
- `${DOCUMENTS}` - ~/Documents
- `${PICTURES}` - ~/Pictures

## Module Details

### fileflow_core

**Purpose**: Core business logic for file organization

**Key Components**:

- `models.py` - Pydantic v2 data models:
  - `GeneralConfig` - General settings
  - `PathConfig` - Directory paths
  - `Thresholds` - Size/age thresholds
  - `Rule` - Organization rule definition
  - `Config` - Main configuration model
  - `FileMetadata` - File information
  - `OperationRecord` - Operation audit trail

- `file_scanner.py` - Directory scanning:
  - Parallel scanning with `ThreadPoolExecutor`
  - Pattern matching with glob
  - Metadata extraction (size, dates, permissions)

- `file_operations.py` - Safe file operations:
  - Atomic moves with fallback to copy+delete
  - Metadata preservation (timestamps, permissions)
  - Error handling with detailed messages

- `duplicate_detector.py` - Duplicate detection:
  - SHA-256 checksum calculation (chunked for large files)
  - Checksum caching in SQLite
  - Comparison by content, not name

- `date_organizer.py` - Date-based organization:
  - Extract dates from filenames
  - Generate YYYY/MM/DD folder structure
  - Template variable substitution

- `rule_engine.py` - Rule processing:
  - Priority-based rule execution
  - Pattern matching and filtering
  - Dry-run mode for safety
  - Operation planning and execution

### fileflow_config

**Purpose**: Configuration management and validation

**Key Components**:

- `config_manager.py` - TOML configuration:
  - Read/write TOML files
  - Environment variable expansion
  - Validation with Pydantic
  - Import/export with merge strategies
  - Automatic backup before changes

- `rule_schema.py` - Rule validation:
  - Priority conflict detection
  - Pattern syntax validation
  - Directory existence checking

- `defaults.py` - Default configuration:
  - Screenshot organization rule (enabled by default)
  - Image, video, code organization rules (disabled)
  - Sensible defaults for all settings

### fileflow_storage

**Purpose**: Data persistence and caching

**Key Components**:

- `database.py` - SQLite operations:
  - Operation history tracking
  - File operation records (move, delete, skip)
  - Query interface for history

- `cache.py` - Checksum cache:
  - Store SHA-256 checksums by file path + mtime
  - Avoid recalculation for unchanged files
  - Cache invalidation on file modification

- `migrations.py` - Schema evolution:
  - Database version tracking
  - Automatic migrations on schema changes

### fileflow_cli

**Purpose**: Command-line interface

**Key Components**:

- `commands.py` - Typer-based CLI:
  - 20+ commands across 5 categories
  - Rich terminal output with colors and tables
  - Interactive prompts for configuration
  - Comprehensive help text

**Command Categories**:
1. **File Organization** - `scan`
2. **Rule Management** - `rules list/show/create/update/delete/enable/disable`
3. **File Discovery** - `files large/old/delete`
4. **Configuration** - `config-show/export/import/import-merge/validate/edit/reset`
5. **Utilities** - `detect-screenshots`

### fileflow_api

**Purpose**: Tauri IPC integration for GUI

**Key Components**:

- `tauri_commands.py` - JSON-based command handlers:
  - Invoked by Tauri Rust bridge via Poetry subprocess
  - Takes JSON input, returns JSON output
  - Matches Tauri IPC contract in `../specs/001-fileflow-manager/contracts/tauri-ipc.md`

**Available Handlers**:
- `scan_files` - Scan and organize files
- `execute_operations` - Execute planned operations
- `get_rules` - List all rules
- `get_rule` - Get single rule details
- `create_rule` - Create new rule
- `update_rule` - Update existing rule
- `delete_rule` - Delete rule
- `enable_rule` - Enable rule
- `disable_rule` - Disable rule
- `find_large_files` - Discover large files
- `find_old_files` - Discover old files
- `delete_files` - Delete specified files
- `get_operation_history` - Query operation history
- `get_configuration` - Get current config
- `export_configuration` - Export config to file
- `import_configuration` - Import config from file

## Development

### Running Tests

```bash
# Run all tests
poetry run pytest

# Run with coverage
poetry run pytest --cov=fileflow_core --cov=fileflow_config --cov=fileflow_storage

# Run specific test file
poetry run pytest tests/test_file_scanner.py
```

### Code Quality

```bash
# Format code with Black
poetry run black .

# Lint with Ruff
poetry run ruff check .

# Type check with mypy
poetry run mypy .
```

### Logging

Logs are written to `~/.local/share/fileflow/fileflow.log` with rotation.

**Log Levels** (configurable in `fileflow.toml`):
- `DEBUG` - Detailed information for debugging
- `INFO` - General information (default)
- `WARNING` - Warning messages
- `ERROR` - Error messages

**Example Log Output**:

```
2025-11-05 10:30:45,123 INFO [fileflow_core.file_scanner] Scanning directory: /Users/user/Desktop
2025-11-05 10:30:45,456 INFO [fileflow_core.rule_engine] Matched 15 files with rule 'screenshot-org'
2025-11-05 10:30:45,789 INFO [fileflow_core.file_operations] Moved file: Screenshot 2025-11-05.png -> ~/Downloads/screenshots/2025/11/05/
```

### Database Schema

**tables**:
- `operations` - Operation history
  - `id` - Primary key
  - `timestamp` - Operation time
  - `operation_type` - move/delete/skip
  - `source_path` - Original file path
  - `destination_path` - Target path (if moved)
  - `file_size` - File size in bytes
  - `checksum` - SHA-256 checksum
  - `rule_id` - Rule that triggered operation
  - `is_dry_run` - Boolean flag
  - `success` - Boolean flag
  - `error_message` - Error details (if failed)

- `checksum_cache` - Checksum cache
  - `file_path` - Absolute file path
  - `mtime` - Modification time
  - `checksum` - SHA-256 checksum
  - `cached_at` - Cache timestamp

## API Reference

For Tauri IPC contract details, see:
- `../specs/001-fileflow-manager/contracts/tauri-ipc.md`

For data model documentation, see:
- `../specs/001-fileflow-manager/data-model.md`

## Performance Considerations

- **Parallel Scanning**: Uses `ThreadPoolExecutor` with 4 workers by default
- **Checksum Caching**: Avoids recalculation for unchanged files (saves 2-3s per 100MB file)
- **Chunked Hashing**: Processes large files in 8KB chunks to avoid memory issues
- **Database Indexing**: Operations table indexed by timestamp and rule_id

**Performance Targets**:
- Process 1,000 files in <30 seconds
- Calculate SHA-256 for 100MB file in <2 seconds
- Configuration reload <500ms

## Troubleshooting

### Common Issues

**Issue**: `Config file not found`
**Solution**: Run any command - config is auto-created on first run

**Issue**: `Permission denied` errors
**Solution**: Check file permissions with `ls -la` and ensure you have read/write access

**Issue**: `Database locked` error
**Solution**: Only one FileFlow instance can run at a time. Close other instances.

**Issue**: Screenshots not detected
**Solution**: Run `poetry run fileflow detect-screenshots` to auto-detect save location

### Debug Mode

Enable debug logging in `~/.config/fileflow/fileflow.toml`:

```toml
[general]
  log_level = "DEBUG"
```

Then check logs in `~/.local/share/fileflow/fileflow.log`.

## Contributing

When contributing to the backend:

1. **Write tests** for new functionality
2. **Update type hints** for all functions
3. **Add docstrings** (Google style)
4. **Run code quality tools** before committing
5. **Update this README** if adding new modules/commands

## License

TBD
