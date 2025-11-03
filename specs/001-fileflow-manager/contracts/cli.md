# CLI Command Contracts

**Feature**: FileFlow Manager
**Created**: 2025-11-03
**Purpose**: Define all CLI commands and their interfaces

## Overview

The FileFlow Manager CLI provides full feature parity with the GUI application. All commands are implemented using Typer and follow a consistent structure.

**Entry Point**: `fileflow` or `python -m fileflow_cli`

**Global Options**:
```bash
--config PATH        # Path to config file (default: ~/.config/fileflow/fileflow.toml)
--log-level LEVEL    # Set log level: DEBUG, INFO, WARNING, ERROR (default: INFO)
--no-color           # Disable colored output
--json               # Output in JSON format instead of human-readable
--version            # Show version and exit
--help               # Show help message
```

---

## Main Commands

### `fileflow scan`

Scan directories for files matching active rules.

**Usage**:
```bash
fileflow scan [OPTIONS]
```

**Options**:
```bash
--dry-run              # Preview operations without executing (default: true)
--execute              # Execute operations immediately (opposite of --dry-run)
--rules TEXT           # Comma-separated rule IDs to scan (omit for all active)
--output-format TEXT   # Output format: table, json, summary (default: table)
```

**Output (table format)**:
```
FileFlow Scan Results
════════════════════════════════════════════════════════════════

Scan completed in 2.3s

Files Scanned:     1,247
Files Matched:       142
Duplicates Found:     12

Planned Operations
────────────────────────────────────────────────────────────────
MOVE    Screenshot 2025-11-01 at 10.30.45.png
        → ~/Downloads/screenshots/2025/11/01/
        (Rule: Screenshot Organization)

MOVE    Screenshot 2025-11-01 at 14.22.13.png
        → ~/Downloads/screenshots/2025/11/01/
        (Rule: Screenshot Organization)

DELETE  IMG_5432.png (duplicate of ~/Photos/IMG_5432.png)
        Space freed: 3.2 MB

... [showing first 20 operations, use --limit to see more]

Summary
────────────────────────────────────────────────────────────────
Total operations:         142
  Move operations:        130
  Delete operations:       12
  Skipped:                  0

Estimated space freed:   45.7 MB

To execute these operations, run:
  fileflow scan --execute
```

**Output (JSON format)**:
```json
{
  "scan_id": "scan-550e8400-e29b-41d4-a716-446655440000",
  "timestamp": "2025-11-03T10:30:45.123Z",
  "total_files_scanned": 1247,
  "files_matched": 142,
  "planned_operations": [...],
  "duplicate_pairs": [...],
  "estimated_space_freed_mb": 45.7,
  "scan_duration_ms": 2300
}
```

**Exit Codes**:
- `0`: Success
- `1`: Scan failed
- `2`: Configuration invalid
- `3`: Permission denied

---

### `fileflow rules`

Manage organization rules.

**Subcommands**:
- `list`: List all rules
- `show`: Show details of a specific rule
- `create`: Create a new rule
- `update`: Update an existing rule
- `delete`: Delete a rule
- `enable`: Enable a rule
- `disable`: Disable a rule

---

#### `fileflow rules list`

List all configured rules.

**Usage**:
```bash
fileflow rules list [OPTIONS]
```

**Options**:
```bash
--enabled-only         # Show only enabled rules
--disabled-only        # Show only disabled rules
--sort-by TEXT         # Sort by: name, priority, created (default: priority)
--output-format TEXT   # Output format: table, json, simple (default: table)
```

**Output**:
```
FileFlow Rules
════════════════════════════════════════════════════════════════

ID                  Name                      Priority  Enabled
──────────────────────────────────────────────────────────────
screenshot-org      Screenshot Organization      1      ✓
pdf-org             PDF Organization             10     ✓
code-org            Code Files                   20     ✗
3d-printing         3D Printing Files            30     ✓

4 rules configured (3 enabled)
```

---

#### `fileflow rules show`

Show detailed information about a specific rule.

**Usage**:
```bash
fileflow rules show RULE_ID
```

**Arguments**:
```bash
RULE_ID    # Rule identifier
```

**Output**:
```
Rule: Screenshot Organization (screenshot-org)
════════════════════════════════════════════════════════════════

Status:          Enabled
Priority:        1
Description:     Automatically organize screenshots by date

Source Patterns:
  - Screenshot*.png
  - Screen Shot*.png

Source Directories:
  - ${DESKTOP}
  - ${DOWNLOADS}

Destination:     ~/Downloads/screenshots/
Organize by Date: Yes (YYYY/MM/DD)

File Types:
  - png

Exclude Patterns: (none)

Size Constraints:  (none)
Age Constraints:   (none)

Created:         2025-11-01 10:30:45
Last Modified:   2025-11-03 08:15:22
```

---

#### `fileflow rules create`

Create a new rule interactively or from file.

**Usage**:
```bash
fileflow rules create [OPTIONS]
```

**Options**:
```bash
--from-file PATH      # Create from TOML file
--interactive         # Interactive creation wizard (default if no --from-file)
--name TEXT           # Rule name (required if not interactive)
--description TEXT    # Rule description
--source-pattern TEXT # Source patterns (can be specified multiple times)
--source-dir TEXT     # Source directories (can be specified multiple times)
--destination TEXT    # Destination path (required if not interactive)
--file-type TEXT      # File types (can be specified multiple times)
--priority INTEGER    # Priority (1-1000, default: 10)
--organize-by-date    # Enable date organization
--enabled             # Enable rule immediately (default: true)
```

**Interactive Mode**:
```bash
$ fileflow rules create

FileFlow Rule Creator
════════════════════════════════════════════════════════════════

Rule Name: 3D Printing Files
Description: Organize STL and 3D model files
Priority [10]: 30

Source Patterns (one per line, empty line to finish):
  1: *.stl
  2: *.obj
  3: *.3mf
  4:

Source Directories (one per line, empty line to finish):
  1: ${DOWNLOADS}
  2: ${DESKTOP}
  3:

Destination Path: ~/Documents/3d-printing

Organize by Date? [y/N]: n

File Types (comma-separated): stl,obj,3mf

Exclude Patterns (one per line, empty line to finish):
  1:

Size Constraints:
  Minimum size (KB) [none]:
  Maximum size (KB) [none]:

Age Constraints:
  Minimum age (days) [none]:
  Maximum age (days) [none]:

Enable immediately? [Y/n]: y

Rule Preview
────────────────────────────────────────────────────────────────
Name:        3D Printing Files
Priority:    30
Sources:     ${DOWNLOADS}, ${DESKTOP}
Patterns:    *.stl, *.obj, *.3mf
Destination: ~/Documents/3d-printing
File Types:  stl, obj, 3mf
Status:      Enabled

Create this rule? [Y/n]: y

✓ Rule created successfully: 3d-printing
```

**Exit Codes**:
- `0`: Success
- `1`: Creation failed
- `2`: Validation failed
- `3`: Duplicate rule name

---

#### `fileflow rules update`

Update an existing rule.

**Usage**:
```bash
fileflow rules update RULE_ID [OPTIONS]
```

**Arguments**:
```bash
RULE_ID    # Rule identifier to update
```

**Options**: Same as `create` command, all optional

**Example**:
```bash
fileflow rules update screenshot-org --priority 5 --description "Updated description"
```

---

#### `fileflow rules delete`

Delete a rule.

**Usage**:
```bash
fileflow rules delete RULE_ID [OPTIONS]
```

**Options**:
```bash
--force    # Skip confirmation prompt
```

**Example**:
```bash
$ fileflow rules delete old-rule

Delete rule 'Old Rule' (old-rule)?
This action cannot be undone. [y/N]: y

✓ Rule deleted successfully
```

---

#### `fileflow rules enable`

Enable a disabled rule.

**Usage**:
```bash
fileflow rules enable RULE_ID [RULE_ID...]
```

**Example**:
```bash
fileflow rules enable screenshot-org pdf-org
✓ Enabled 2 rules
```

---

#### `fileflow rules disable`

Disable a rule without deleting it.

**Usage**:
```bash
fileflow rules disable RULE_ID [RULE_ID...]
```

---

### `fileflow files`

Manage and analyze files.

**Subcommands**:
- `large`: Find and manage large files
- `old`: Find and manage old files
- `duplicates`: Find duplicate files

---

#### `fileflow files large`

Find files larger than a threshold.

**Usage**:
```bash
fileflow files large [OPTIONS]
```

**Options**:
```bash
--threshold INTEGER    # Size threshold in MB (default: 100)
--directory TEXT       # Specific directory to scan (can specify multiple)
--sort-by TEXT         # Sort by: size, modified, name (default: size)
--limit INTEGER        # Limit results (default: 100)
--delete               # Delete selected files (interactive)
--output-format TEXT   # Output format: table, json, simple (default: table)
```

**Output**:
```
Large Files (>100 MB)
════════════════════════════════════════════════════════════════

Path                                        Size       Modified
──────────────────────────────────────────────────────────────
~/Downloads/ubuntu-22.04.iso               3.5 GB     2025-10-15
~/Documents/project-backup.zip             1.2 GB     2025-09-28
~/Downloads/video-tutorial.mp4             847 MB     2025-11-01
~/Desktop/database-dump.sql                523 MB     2025-10-30

Total: 4 files, 6.0 GB

To delete files, run:
  fileflow files large --delete
```

**Interactive Delete**:
```bash
$ fileflow files large --delete

Large Files (>100 MB)
════════════════════════════════════════════════════════════════

 [1] ~/Downloads/ubuntu-22.04.iso               3.5 GB
 [2] ~/Documents/project-backup.zip             1.2 GB
 [3] ~/Downloads/video-tutorial.mp4             847 MB
 [4] ~/Desktop/database-dump.sql                523 MB

Select files to delete (comma-separated numbers, or 'all'): 1,3

You are about to delete 2 files (4.3 GB):
  - ~/Downloads/ubuntu-22.04.iso
  - ~/Downloads/video-tutorial.mp4

This action cannot be undone. Continue? [y/N]: y

✓ Deleted 2 files, freed 4.3 GB
```

---

#### `fileflow files old`

Find files older than a threshold.

**Usage**:
```bash
fileflow files old [OPTIONS]
```

**Options**:
```bash
--threshold INTEGER    # Age threshold in days (default: 90)
--directory TEXT       # Specific directory to scan (can specify multiple)
--file-type TEXT       # Filter by file type/extension
--sort-by TEXT         # Sort by: age, size, name (default: age)
--limit INTEGER        # Limit results (default: 100)
--delete               # Delete selected files (interactive)
--output-format TEXT   # Output format: table, json, simple (default: table)
```

**Output**: Similar to `large` command

---

#### `fileflow files duplicates`

Find duplicate files using checksum comparison.

**Usage**:
```bash
fileflow files duplicates [OPTIONS]
```

**Options**:
```bash
--directory TEXT       # Directories to scan (can specify multiple)
--delete-auto          # Auto-delete duplicates (keep oldest)
--delete-interactive   # Interactive deletion
--min-size INTEGER     # Minimum file size in KB to check (default: 0)
--output-format TEXT   # Output format: table, json, simple (default: table)
```

**Output**:
```
Duplicate Files Found
════════════════════════════════════════════════════════════════

Group 1 (3 copies, 15.2 MB each):
  SHA-256: a7b3c4d5e6f7...
  ✓ ~/Photos/vacation.jpg                      (oldest)
    ~/Desktop/vacation.jpg
    ~/Downloads/vacation.jpg

Group 2 (2 copies, 2.1 MB each):
  SHA-256: 1a2b3c4d5e6f...
  ✓ ~/Documents/report.pdf                     (oldest)
    ~/Desktop/report.pdf

Total: 2 groups, 3 duplicate files, 32.5 MB wasted space

Legend: ✓ = file to keep

To delete duplicates, run:
  fileflow files duplicates --delete-interactive
```

---

### `fileflow history`

View operation history.

**Usage**:
```bash
fileflow history [OPTIONS]
```

**Options**:
```bash
--limit INTEGER        # Number of operations to show (default: 50)
--operation-type TEXT  # Filter by: move, delete, skip
--rule-id TEXT         # Filter by rule ID
--start-date TEXT      # Start date (YYYY-MM-DD)
--end-date TEXT        # End date (YYYY-MM-DD)
--show-dry-runs        # Include dry-run operations (default: false)
--output-format TEXT   # Output format: table, json, simple (default: table)
```

**Output**:
```
Operation History
════════════════════════════════════════════════════════════════

Time                 Type    Source → Destination              Rule
──────────────────────────────────────────────────────────────────
2025-11-03 10:30:45  MOVE    Screenshot 2025-11-03.png         screenshot-org
                             → ~/Downloads/screenshots/2025/11/03/
                             ✓ Success

2025-11-03 10:30:45  DELETE  IMG_5432.png (duplicate)          screenshot-org
                             ✓ Success, freed 3.2 MB

2025-11-03 10:30:44  SKIP    document.pdf                      pdf-org
                             ! Name conflict

2025-11-02 15:22:10  MOVE    report.pdf                        pdf-org
                             → ~/Documents/PDFs/2025/11/
                             ✓ Success

Showing 4 of 247 operations (use --limit to see more)
```

---

### `fileflow config`

Manage configuration.

**Subcommands**:
- `show`: Display current configuration
- `edit`: Open configuration in editor
- `export`: Export configuration to file
- `import`: Import configuration from file
- `validate`: Validate configuration file
- `reset`: Reset to default configuration

---

#### `fileflow config show`

Display current configuration.

**Usage**:
```bash
fileflow config show [OPTIONS]
```

**Options**:
```bash
--section TEXT         # Show specific section: general, paths, thresholds, rules
--output-format TEXT   # Output format: toml, json, yaml (default: toml)
```

**Output**:
```toml
[general]
log_level = "INFO"
auto_run_on_startup = false
auto_run_interval_minutes = 60
enable_notifications = true
cache_enabled = true

[paths]
screenshot_source = "/Users/daniel/Desktop"
screenshot_destination = "~/Downloads/screenshots"
monitored_directories = [
    "/Users/daniel/Desktop",
    "/Users/daniel/Downloads"
]

[thresholds]
large_file_mb = 100
old_file_days = 90

[duplicate_handling]
auto_delete_duplicates = false
always_keep_oldest = true

# ... rules follow ...
```

---

#### `fileflow config edit`

Open configuration in default editor.

**Usage**:
```bash
fileflow config edit
```

Opens `$EDITOR` (or `nano` if not set) with the configuration file. Validates on save.

---

#### `fileflow config export`

Export configuration to file.

**Usage**:
```bash
fileflow config export OUTPUT_PATH [OPTIONS]
```

**Options**:
```bash
--rules-only           # Export only rules (not settings)
--settings-only        # Export only settings (not rules)
```

**Example**:
```bash
fileflow config export ~/backups/fileflow-config-2025-11-03.toml
✓ Configuration exported to ~/backups/fileflow-config-2025-11-03.toml
```

---

#### `fileflow config import`

Import configuration from file.

**Usage**:
```bash
fileflow config import INPUT_PATH [OPTIONS]
```

**Options**:
```bash
--merge                # Merge with existing config (default: false, replace)
--force                # Skip confirmation prompt
```

**Example**:
```bash
$ fileflow config import ~/backups/fileflow-config.toml

Import configuration from ~/backups/fileflow-config.toml?
This will replace your current configuration. [y/N]: y

✓ Configuration imported successfully
  Rules imported: 12
  Settings updated: general, paths, thresholds
```

---

#### `fileflow config validate`

Validate configuration file.

**Usage**:
```bash
fileflow config validate [PATH]
```

**Arguments**:
```bash
PATH    # Path to config file (default: current config)
```

**Output**:
```bash
$ fileflow config validate

Validating configuration...

✓ TOML syntax valid
✓ All required fields present
✓ All rules valid
✓ All paths accessible
✓ All priorities unique

Configuration is valid
```

**Validation Failure**:
```bash
$ fileflow config validate custom-config.toml

Validating configuration...

✗ Configuration is invalid

Errors:
  Line 45: Invalid priority value: must be 1-1000
  Line 67: Rule 'pdf-org' missing required field 'destination'
  Line 89: Invalid file type: 'invalid-type'

Warnings:
  Line 23: Directory not found: /Users/daniel/OldFolder
```

---

#### `fileflow config reset`

Reset configuration to defaults.

**Usage**:
```bash
fileflow config reset [OPTIONS]
```

**Options**:
```bash
--force                # Skip confirmation and backup
--keep-rules           # Reset settings but keep custom rules
```

**Example**:
```bash
$ fileflow config reset

This will reset your configuration to defaults.
A backup will be saved to ~/.config/fileflow/fileflow.toml.backup

Continue? [y/N]: y

✓ Configuration reset to defaults
✓ Backup saved to ~/.config/fileflow/fileflow.toml.backup
```

---

### `fileflow daemon`

Run FileFlow as a background daemon.

**Usage**:
```bash
fileflow daemon [COMMAND]
```

**Commands**:
```bash
start      # Start daemon
stop       # Stop daemon
restart    # Restart daemon
status     # Show daemon status
logs       # Show daemon logs
```

**Examples**:
```bash
fileflow daemon start
✓ FileFlow daemon started (PID: 12345)

fileflow daemon status
FileFlow daemon is running (PID: 12345)
  Uptime: 2 days, 5 hours
  Memory: 87 MB
  Last scan: 10 minutes ago
  Next scan: in 50 minutes
```

---

### `fileflow detect-screenshots`

Auto-detect macOS screenshot location.

**Usage**:
```bash
fileflow detect-screenshots
```

**Output**:
```bash
Screenshot Location Detection
════════════════════════════════════════════════════════════════

Detected location: /Users/daniel/Desktop
Method: macOS system preferences
Confidence: High

To update your configuration, run:
  fileflow config edit
```

---

## Output Formats

All commands support multiple output formats via `--output-format`:

### Table Format (default)

Human-readable table with borders, colors, and formatting.

### JSON Format

Machine-readable JSON for scripting:
```bash
fileflow rules list --output-format json | jq '.[] | select(.enabled == true)'
```

### Simple Format

Simplified text output for scripting:
```bash
fileflow rules list --output-format simple
screenshot-org  Screenshot Organization  1  enabled
pdf-org         PDF Organization         10 enabled
```

---

## Environment Variables

```bash
FILEFLOW_CONFIG       # Path to config file (overrides --config)
FILEFLOW_LOG_LEVEL    # Log level (overrides --log-level)
FILEFLOW_NO_COLOR     # Disable colors (same as --no-color)
FILEFLOW_HOME         # FileFlow home directory (default: ~/.config/fileflow)
```

---

## Exit Codes

| Code | Meaning |
|------|---------|
| `0` | Success |
| `1` | General error |
| `2` | Validation error |
| `3` | Permission denied |
| `4` | File not found |
| `5` | Configuration error |
| `6` | Database error |

---

## Shell Completion

Generate shell completion scripts:

```bash
# Bash
fileflow --install-completion bash

# Zsh
fileflow --install-completion zsh

# Fish
fileflow --install-completion fish
```

---

## Examples

**Organize screenshots in dry-run mode**:
```bash
fileflow scan --dry-run
```

**Execute screenshot organization**:
```bash
fileflow scan --execute --rules screenshot-org
```

**Find large files over 500MB**:
```bash
fileflow files large --threshold 500
```

**Find old files from specific directory**:
```bash
fileflow files old --threshold 180 --directory ~/Downloads
```

**Create new rule non-interactively**:
```bash
fileflow rules create \
  --name "Video Files" \
  --description "Organize video files by date" \
  --source-pattern "*.mp4" \
  --source-pattern "*.mov" \
  --source-dir "${DOWNLOADS}" \
  --destination "~/Videos" \
  --file-type "mp4,mov" \
  --priority 15 \
  --organize-by-date
```

**Export configuration**:
```bash
fileflow config export ~/Dropbox/fileflow-backup.toml
```

**View recent operations**:
```bash
fileflow history --limit 20 --operation-type move
```

**Find and delete duplicates**:
```bash
fileflow files duplicates --delete-interactive
```

**Run as daemon with auto-organization every hour**:
```bash
fileflow daemon start
```

---

## Notes

1. **Configuration Persistence**: All `create`, `update`, and `delete` operations immediately persist to TOML file
2. **Dry-Run Safety**: Scan defaults to dry-run mode to prevent accidental execution
3. **Interactive Confirmations**: Destructive operations (delete, reset) require confirmation unless `--force` is used
4. **Progress Indicators**: Long-running operations show progress bars and status
5. **Color Support**: Automatically detected; disable with `--no-color` or `NO_COLOR=1`
6. **Error Messages**: All errors include actionable suggestions for resolution
7. **Logging**: Logs written to `~/.config/fileflow/logs/fileflow.log` with rotation
