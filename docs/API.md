# FileFlow Manager API Documentation

This document describes the APIs available in FileFlow Manager for both CLI and programmatic use.

## Table of Contents

1. [CLI API](#cli-api)
2. [Python API](#python-api)
3. [Tauri Commands API](#tauri-commands-api)
4. [Data Models](#data-models)
5. [Error Handling](#error-handling)

---

## CLI API

The CLI is built with Typer and provides a rich command-line interface.

### File Operations

#### scan

Scan and organize files according to rules.

```bash
fileflow scan [OPTIONS]
```

**Options:**
- `--execute` / `--dry-run` - Execute operations vs dry run (default: dry-run)
- `--rule-ids TEXT` - Specific rules to run (default: all enabled)

**Examples:**
```bash
# Dry run with all enabled rules
fileflow scan

# Execute all enabled rules
fileflow scan --execute

# Run specific rules only
fileflow scan --rule-ids screenshot-org,pdf-org --execute
```

**Returns:**
- Exit code 0 on success
- Exit code 1 on error

#### detect-screenshots

Detect likely screenshot location.

```bash
fileflow detect-screenshots
```

**Output:**
```
Detected screenshot directory: /Users/username/Desktop
```

---

### Rule Management

#### rules list

List all configured rules.

```bash
fileflow rules list [OPTIONS]
```

**Options:**
- `--output FORMAT` - Output format: table, json, simple (default: table)
- `--limit INT` - Limit number of rules shown
- `--page INT` - Page number for pagination
- `--no-pagination` - Disable pagination

**Examples:**
```bash
# List all rules (paginated)
fileflow rules list

# Export as JSON
fileflow rules list --output json

# Show first 5 rules
fileflow rules list --limit 5

# Show page 2
fileflow rules list --page 2
```

**JSON Output:**
```json
{
  "status": "success",
  "data": [
    {
      "id": "screenshot-org",
      "name": "Screenshot Organization",
      "priority": 100,
      "enabled": true,
      "source_patterns": ["Screenshot*.png"],
      "source_directories": ["~/Desktop"],
      "destination": "~/Pictures/Screenshots"
    }
  ],
  "metadata": {
    "total_rules": 5,
    "shown_rules": 5,
    "enabled_rules": 4
  }
}
```

#### rules show

Show details of a specific rule.

```bash
fileflow rules show <RULE_ID>
```

**Arguments:**
- `RULE_ID` - ID of the rule to show

**Example:**
```bash
fileflow rules show screenshot-org
```

#### rules create

Create a new rule interactively.

```bash
fileflow rules create
```

**Interactive Prompts:**
1. Rule ID (unique identifier)
2. Name (human-readable name)
3. Description
4. Priority (1-100)
5. Source patterns (comma-separated)
6. Source directories (comma-separated paths)
7. Destination directory
8. Organize by date (y/n)
9. Detect duplicates (y/n)

#### rules update

Update an existing rule.

```bash
fileflow rules update <RULE_ID> [OPTIONS]
```

**Options:**
- `--name TEXT` - New name
- `--priority INT` - New priority
- `--enabled / --disabled` - Enable/disable rule
- ... (other rule fields)

**Example:**
```bash
fileflow rules update screenshot-org --priority 95 --enabled
```

#### rules delete

Delete a rule.

```bash
fileflow rules delete <RULE_ID> [OPTIONS]
```

**Options:**
- `--force` - Skip confirmation

**Example:**
```bash
fileflow rules delete old-rule --force
```

#### rules enable / disable

Enable or disable a rule.

```bash
fileflow rules enable <RULE_ID>
fileflow rules disable <RULE_ID>
```

---

### File Discovery

#### files large

Find large files.

```bash
fileflow files large [OPTIONS]
```

**Options:**
- `--threshold INT` - Size threshold in MB (default: 100)
- `--output FORMAT` - Output format (table, json)

**Example:**
```bash
fileflow files large --threshold 500 --output json
```

#### files old

Find old files.

```bash
fileflow files old [OPTIONS]
```

**Options:**
- `--days INT` - Age threshold in days (default: 365)
- `--output FORMAT` - Output format (table, json)

**Example:**
```bash
fileflow files old --days 180
```

#### files delete

Delete files.

```bash
fileflow files delete <PATHS...> [OPTIONS]
```

**Arguments:**
- `PATHS` - Paths to delete (space-separated)

**Options:**
- `--force` - Skip confirmation

**Example:**
```bash
fileflow files delete /path/to/file1.txt /path/to/file2.txt --force
```

---

### Configuration

#### config-show

Show current configuration.

```bash
fileflow config-show [OPTIONS]
```

**Options:**
- `--output FORMAT` - Output format (yaml, json, toml)

**Example:**
```bash
fileflow config-show --output json
```

#### config-export

Export configuration to file.

```bash
fileflow config-export <PATH>
```

**Arguments:**
- `PATH` - Output file path

**Example:**
```bash
fileflow config-export ~/backup/fileflow-config.toml
```

#### config-import

Import configuration from file (replace mode).

```bash
fileflow config-import <PATH>
```

**Arguments:**
- `PATH` - Input file path

**Example:**
```bash
fileflow config-import ~/backup/fileflow-config.toml
```

#### config-import-merge

Import configuration from file (merge mode).

```bash
fileflow config-import-merge <PATH>
```

**Example:**
```bash
fileflow config-import-merge ~/shared/extra-rules.toml
```

#### config-validate

Validate configuration file.

```bash
fileflow config-validate [PATH]
```

**Arguments:**
- `PATH` - Config file to validate (default: current config)

**Example:**
```bash
fileflow config-validate ~/test-config.toml
```

#### config-edit

Open configuration in editor.

```bash
fileflow config-edit
```

Opens config in `$EDITOR` (or `vi` if not set).

#### config-reset

Reset configuration to defaults.

```bash
fileflow config-reset [OPTIONS]
```

**Options:**
- `--force` - Skip confirmation

**Example:**
```bash
fileflow config-reset --force
```

---

## Python API

For programmatic use in Python scripts.

### File Operations

```python
from fileflow_core.scanner import FileScanner
from fileflow_config.config_manager import ConfigManager

# Load configuration
config_mgr = ConfigManager(config_path)
config = config_mgr.load()

# Create scanner
scanner = FileScanner(config)

# Scan files
operations = scanner.scan(dry_run=True)

# Execute operations
results = scanner.execute_operations(operations)
```

### Configuration Management

```python
from fileflow_config.config_manager import ConfigManager
from fileflow_core.models import Rule

# Create config manager
config_mgr = ConfigManager(config_path)

# Load config
config = config_mgr.load()

# Add a rule
new_rule = Rule(
    id="my-rule",
    name="My Rule",
    enabled=True,
    priority=80,
    source_patterns=["*.txt"],
    source_directories=["~/Documents"],
    destination="~/Archive"
)
config.rules.append(new_rule)

# Save config
config_mgr.save(config)
```

### Database Operations

```python
from fileflow_storage.database import Database

# Create database
db = Database(db_path)

# Log operation
db.log_operation(
    operation_type="move",
    source_path="/path/to/source.txt",
    destination_path="/path/to/dest.txt",
    rule_id="my-rule",
    success=True
)

# Get operation history
operations = db.get_operations(limit=100)
```

### Cache Operations

```python
from fileflow_storage.cache import ChecksumCache

# Create cache
cache = ChecksumCache(db)

# Get or compute checksum
checksum = cache.get_or_compute_checksum("/path/to/file.txt")

# Check if file is duplicate
is_dup = cache.is_duplicate(checksum)

# Clear cache
cache.clear()
```

---

## Tauri Commands API

For frontend integration (TypeScript/JavaScript).

### File Operations

#### scan_files

Scan files according to rules.

```typescript
import { invoke } from '@tauri-apps/api/tauri';

interface ScanFilesArgs {
  ruleIds: string[];
  dryRun: boolean;
}

interface ScanResult {
  operations: Operation[];
  stats: {
    totalFiles: number;
    totalOperations: number;
    spaceSaved: number;
  };
}

const result = await invoke<ScanResult>('scan_files', {
  ruleIds: ['screenshot-org', 'pdf-org'],
  dryRun: true
});
```

#### execute_operations

Execute file operations.

```typescript
interface ExecuteArgs {
  operations: Operation[];
}

interface ExecuteResult {
  successful: number;
  failed: number;
  errors: string[];
}

const result = await invoke<ExecuteResult>('execute_operations', {
  operations: pendingOperations
});
```

### Rule Management

#### get_rules

Get all rules.

```typescript
interface Rule {
  id: string;
  name: string;
  enabled: boolean;
  priority: number;
  sourcePatterns: string[];
  sourceDirectories: string[];
  destination: string;
  organizeByDate: boolean;
  detectDuplicates: boolean;
}

const rules = await invoke<Rule[]>('get_rules', {});
```

#### create_rule

Create a new rule.

```typescript
const newRule: Rule = {
  id: 'my-rule',
  name: 'My Rule',
  enabled: true,
  priority: 80,
  sourcePatterns: ['*.txt'],
  sourceDirectories: ['~/Documents'],
  destination: '~/Archive',
  organizeByDate: false,
  detectDuplicates: false
};

await invoke('create_rule', { rule: newRule });
```

#### update_rule

Update an existing rule.

```typescript
await invoke('update_rule', {
  ruleId: 'my-rule',
  rule: updatedRule
});
```

#### delete_rule

Delete a rule.

```typescript
await invoke('delete_rule', { ruleId: 'my-rule' });
```

### File Discovery

#### find_large_files

Find large files.

```typescript
interface LargeFilesArgs {
  thresholdMb: number;
}

interface FileInfo {
  path: string;
  sizeBytes: number;
  modifiedAt: string;
  fileType: string;
}

const files = await invoke<FileInfo[]>('find_large_files', {
  thresholdMb: 100
});
```

#### find_old_files

Find old files.

```typescript
interface OldFilesArgs {
  ageDays: number;
}

const files = await invoke<FileInfo[]>('find_old_files', {
  ageDays: 365
});
```

#### delete_files

Delete multiple files.

```typescript
interface DeleteFilesArgs {
  paths: string[];
}

interface DeleteResult {
  deleted: number;
  failed: number;
  errors: string[];
}

const result = await invoke<DeleteResult>('delete_files', {
  paths: ['/path/to/file1.txt', '/path/to/file2.txt']
});
```

### Configuration

#### get_configuration

Get current configuration.

```typescript
interface Configuration {
  rules: Rule[];
  settings: Settings;
}

const config = await invoke<Configuration>('get_configuration', {});
```

#### export_configuration

Export configuration to file.

```typescript
await invoke('export_configuration', {
  path: '/path/to/export.toml'
});
```

#### import_configuration

Import configuration from file.

```typescript
await invoke('import_configuration', {
  path: '/path/to/import.toml',
  mergeMode: 'replace'  // or 'merge'
});
```

#### clear_cache

Clear checksum cache.

```typescript
await invoke('clear_cache', {});
```

---

## Data Models

### Rule

```typescript
interface Rule {
  // Identity
  id: string;
  name: string;
  description?: string;

  // Behavior
  enabled: boolean;
  priority: number;  // 1-100, higher runs first

  // Source selection
  sourcePatterns: string[];  // Glob patterns
  sourceDirectories: string[];
  excludePatterns?: string[];

  // Filters
  fileTypes?: string[];  // ['documents', 'images', etc.]
  minSizeKb?: number;
  maxSizeKb?: number;
  minAgeDays?: number;
  maxAgeDays?: number;

  // Destination
  destination: string;
  organizeByDate: boolean;
  detectDuplicates: boolean;

  // Metadata
  createdAt: string;  // ISO 8601
  lastModified: string;  // ISO 8601
}
```

### Operation

```typescript
interface Operation {
  id: string;
  operationType: 'move' | 'delete' | 'skip';
  sourcePath: string;
  destinationPath?: string;
  ruleId?: string;
  fileSize: number;
  duplicate: boolean;
  createdAt: string;
}
```

### FileInfo

```typescript
interface FileInfo {
  path: string;
  sizeBytes: number;
  modifiedAt: string;  // ISO 8601
  createdAt: string;  // ISO 8601
  fileType: string;  // 'document', 'image', 'video', etc.
  extension: string;
}
```

### Configuration

```typescript
interface Configuration {
  rules: Rule[];
  settings: {
    defaultScanDirs: string[];
    excludeDirs: string[];
    logLevel: 'debug' | 'info' | 'warning' | 'error';
  };
}
```

---

## Error Handling

### Exit Codes (CLI)

```python
class ExitCode:
    SUCCESS = 0
    GENERAL_ERROR = 1
    CONFIG_ERROR = 2
    DATABASE_ERROR = 3
    FILE_OPERATION_ERROR = 4
    INVALID_USAGE = 5
    OPERATION_CANCELLED = 6
```

### Error Response Format (JSON)

```json
{
  "status": "error",
  "message": "Human-readable error message",
  "code": "ERROR_CODE",
  "details": {
    "field": "Additional context"
  }
}
```

### Common Errors

**ConfigError**:
```json
{
  "status": "error",
  "message": "Failed to load configuration",
  "code": "CONFIG_ERROR",
  "details": {
    "path": "~/.config/fileflow/fileflow.toml",
    "reason": "File not found"
  }
}
```

**ValidationError**:
```json
{
  "status": "error",
  "message": "Invalid rule configuration",
  "code": "VALIDATION_ERROR",
  "details": {
    "field": "priority",
    "value": 150,
    "constraint": "Must be between 1 and 100"
  }
}
```

**FileOperationError**:
```json
{
  "status": "error",
  "message": "Failed to move file",
  "code": "FILE_OPERATION_ERROR",
  "details": {
    "source": "/path/to/source.txt",
    "destination": "/path/to/dest.txt",
    "reason": "Permission denied"
  }
}
```

### Error Handling Best Practices

**CLI**:
```bash
# Check exit code
fileflow scan --execute
if [ $? -eq 0 ]; then
    echo "Success"
else
    echo "Failed"
fi
```

**Python**:
```python
try:
    operations = scanner.scan()
except FileNotFoundError as e:
    print(f"File not found: {e}")
except PermissionError as e:
    print(f"Permission denied: {e}")
except Exception as e:
    print(f"Unexpected error: {e}")
```

**TypeScript**:
```typescript
try {
  const result = await invoke('scan_files', { ... });
} catch (error) {
  console.error('Scan failed:', error);
  // Show error to user
  showNotification({
    type: 'error',
    message: `Scan failed: ${error}`
  });
}
```

---

## Rate Limits and Performance

### Recommendations

- **Batch operations**: Process files in batches of 100-1000 for optimal performance
- **Concurrent operations**: Use up to CPU count workers for parallel processing
- **Cache**: Checksum cache significantly speeds up duplicate detection
- **Database**: SQLite handles 10,000+ operations efficiently

### Performance Tips

1. **Large scans**: Use pagination for UI display
2. **Duplicate detection**: Clear cache if files changed significantly
3. **Pattern matching**: Specific patterns are faster than wildcards
4. **Database queries**: Add indexes for frequently queried fields (already done)

---

## Changelog

### Version 0.1.2
- Added loading states to all async operations
- European date/time format throughout
- Help button linking to documentation

### Version 0.1.1
- Architecture-specific backend binary support
- Shell permissions for URL opening

### Version 0.1.0
- Initial API release
- Full CRUD for rules
- File organization and discovery
- Configuration management

---

## Support

For API questions:
- Check examples in this document
- Review source code comments
- Open a GitHub Discussion
- Open a GitHub Issue for bugs

For feature requests:
- Open a GitHub Issue with "enhancement" label
- Describe your use case
- Provide API design suggestions
