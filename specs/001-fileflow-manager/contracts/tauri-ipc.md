# Tauri IPC Command Contracts

**Feature**: FileFlow Manager
**Created**: 2025-11-03
**Purpose**: Define all Tauri IPC commands for frontend-backend communication

## Overview

All commands are invoked from the Svelte frontend using Tauri's `invoke()` API. Commands execute in the Python backend via the sidecar process and return results as JSON.

**Error Handling**: All commands return Result<T, CommandError> where CommandError has:
```typescript
interface CommandError {
  code: string;        // Machine-readable error code
  message: string;     // Human-readable error message
  details?: any;       // Optional additional context
}
```

---

## File Scanning Commands

### `scan_files`

Scan source directories for files matching active rules and return preview of planned operations.

**Request**:
```typescript
interface ScanFilesRequest {
  dry_run: boolean;           // If true, only preview without executing
  rule_ids?: string[];        // Optional: scan specific rules only (omit for all active rules)
}
```

**Response**:
```typescript
interface ScanFilesResponse {
  scan_id: string;                    // Unique scan identifier
  timestamp: string;                  // ISO 8601 timestamp
  total_files_scanned: number;        // Total files examined
  files_matched: number;              // Files matching at least one rule
  planned_operations: FileOperation[]; // Operations to be performed
  duplicate_pairs: DuplicatePair[];   // Detected duplicates
  large_files: FileMetadata[];        // Files exceeding large file threshold
  old_files: FileMetadata[];          // Files exceeding old file threshold
  estimated_space_freed_mb: number;   // Space to be freed by duplicate deletion
  scan_duration_ms: number;           // Time taken for scan
}

interface FileOperation {
  id: string;                  // Operation ID for execution
  operation_type: "move" | "delete" | "skip";
  source_path: string;
  destination_path: string | null;
  file_size: number;
  rule_id: string;
  rule_name: string;
  skip_reason?: "name_conflict" | "permission_denied" | "already_processed";
}

interface DuplicatePair {
  original_path: string;
  duplicate_path: string;
  checksum: string;
  file_size: number;
}
```

**Errors**:
- `SCAN_FAILED`: General scan failure
- `INVALID_RULE_ID`: Specified rule_id doesn't exist
- `PERMISSION_DENIED`: Cannot read source directories
- `CONFIG_INVALID`: Configuration is invalid or missing

**Example**:
```typescript
const result = await invoke<ScanFilesResponse>('scan_files', {
  dry_run: true
});
```

---

### `execute_operations`

Execute specific file operations from a previous scan.

**Request**:
```typescript
interface ExecuteOperationsRequest {
  operation_ids: string[];     // IDs from ScanFilesResponse.planned_operations
  confirm_deletions: boolean;  // Must be true to execute delete operations
}
```

**Response**:
```typescript
interface ExecuteOperationsResponse {
  execution_id: string;
  timestamp: string;
  total_operations: number;
  successful_operations: number;
  failed_operations: number;
  skipped_operations: number;
  results: OperationResult[];
  duration_ms: number;
}

interface OperationResult {
  operation_id: string;
  success: boolean;
  error_message?: string;
  error_code?: "PERMISSION_DENIED" | "FILE_NOT_FOUND" | "DISK_FULL" | "NAME_CONFLICT";
}
```

**Errors**:
- `EXECUTION_FAILED`: General execution failure
- `INVALID_OPERATION_ID`: Operation ID not found in recent scans
- `DELETION_NOT_CONFIRMED`: confirm_deletions=false but delete operations present
- `DISK_SPACE_INSUFFICIENT`: Not enough disk space for operations

**Example**:
```typescript
const result = await invoke<ExecuteOperationsResponse>('execute_operations', {
  operation_ids: ['op-123', 'op-456'],
  confirm_deletions: true
});
```

---

### `cancel_operation`

Cancel an in-progress scan or execution operation.

**Request**:
```typescript
interface CancelOperationRequest {
  operation_id: string;  // scan_id or execution_id
}
```

**Response**:
```typescript
interface CancelOperationResponse {
  success: boolean;
  message: string;  // e.g., "Operation cancelled successfully"
}
```

**Errors**:
- `OPERATION_NOT_FOUND`: Operation ID doesn't exist
- `OPERATION_ALREADY_COMPLETED`: Cannot cancel completed operation

---

## Rule Management Commands

### `get_rules`

Retrieve all configured rules.

**Request**: None (no parameters)

**Response**:
```typescript
interface GetRulesResponse {
  rules: Rule[];
}

interface Rule {
  id: string;
  enabled: boolean;
  name: string;
  description: string;
  source_patterns: string[];
  source_directories: string[];
  destination: string;
  organize_by_date: boolean;
  file_types: string[];
  priority: number;
  exclude_patterns: string[];
  min_size_kb?: number;
  max_size_kb?: number;
  min_age_days?: number;
  max_age_days?: number;
  created_at: string;        // ISO 8601
  last_modified: string;     // ISO 8601
}
```

**Errors**:
- `CONFIG_READ_FAILED`: Cannot read configuration file

---

### `create_rule`

Create a new rule.

**Request**:
```typescript
interface CreateRuleRequest {
  rule: Omit<Rule, 'id' | 'created_at' | 'last_modified'>;
}
```

**Response**:
```typescript
interface CreateRuleResponse {
  rule: Rule;  // The created rule with generated ID and timestamps
}
```

**Errors**:
- `VALIDATION_FAILED`: Rule validation failed (details in error.details)
- `CONFIG_WRITE_FAILED`: Cannot write to configuration file
- `DUPLICATE_RULE_NAME`: Rule with this name already exists

**Validation Rules**:
- name: 1-100 characters, must be unique
- source_patterns: At least 1 pattern
- source_directories: At least 1 directory, must exist or use environment variables
- destination: Must be valid path or use environment variables
- priority: 1-1000
- file_types: At least 1 type

---

### `update_rule`

Update an existing rule.

**Request**:
```typescript
interface UpdateRuleRequest {
  rule_id: string;
  updates: Partial<Omit<Rule, 'id' | 'created_at' | 'last_modified'>>;
}
```

**Response**:
```typescript
interface UpdateRuleResponse {
  rule: Rule;  // The updated rule
}
```

**Errors**:
- `RULE_NOT_FOUND`: Rule ID doesn't exist
- `VALIDATION_FAILED`: Updated rule fails validation
- `CONFIG_WRITE_FAILED`: Cannot write to configuration file

---

### `delete_rule`

Delete a rule.

**Request**:
```typescript
interface DeleteRuleRequest {
  rule_id: string;
}
```

**Response**:
```typescript
interface DeleteRuleResponse {
  success: boolean;
  message: string;
}
```

**Errors**:
- `RULE_NOT_FOUND`: Rule ID doesn't exist
- `CONFIG_WRITE_FAILED`: Cannot write to configuration file

---

### `toggle_rule`

Enable or disable a rule without deleting it.

**Request**:
```typescript
interface ToggleRuleRequest {
  rule_id: string;
  enabled: boolean;
}
```

**Response**:
```typescript
interface ToggleRuleResponse {
  rule: Rule;  // The updated rule
}
```

**Errors**:
- `RULE_NOT_FOUND`: Rule ID doesn't exist
- `CONFIG_WRITE_FAILED`: Cannot write to configuration file

---

## File Management Commands

### `get_large_files`

Get files exceeding size threshold from monitored directories.

**Request**:
```typescript
interface GetLargeFilesRequest {
  threshold_mb: number;           // Minimum file size in MB
  directories?: string[];         // Optional: specific directories (omit for all monitored)
  sort_by?: "size" | "modified";  // Default: "size"
  sort_order?: "asc" | "desc";    // Default: "desc"
}
```

**Response**:
```typescript
interface GetLargeFilesResponse {
  files: FileMetadata[];
  total_count: number;
  total_size_mb: number;
}

interface FileMetadata {
  path: string;
  filename: string;
  extension: string;
  size_bytes: number;
  size_mb: number;
  created_at: string;
  modified_at: string;
  age_days: number;
}
```

**Errors**:
- `INVALID_THRESHOLD`: Threshold must be > 0
- `SCAN_FAILED`: Failed to scan directories

---

### `get_old_files`

Get files older than age threshold from monitored directories.

**Request**:
```typescript
interface GetOldFilesRequest {
  threshold_days: number;         // Minimum file age in days
  directories?: string[];         // Optional: specific directories
  file_types?: string[];          // Optional: filter by extension
  sort_by?: "age" | "size";       // Default: "age"
  sort_order?: "asc" | "desc";    // Default: "desc"
}
```

**Response**:
```typescript
interface GetOldFilesResponse {
  files: FileMetadata[];
  total_count: number;
  total_size_mb: number;
}
```

**Errors**:
- `INVALID_THRESHOLD`: Threshold must be > 0
- `SCAN_FAILED`: Failed to scan directories

---

### `delete_files`

Delete specified files with confirmation.

**Request**:
```typescript
interface DeleteFilesRequest {
  file_paths: string[];
  confirm: boolean;  // Must be true to execute
}
```

**Response**:
```typescript
interface DeleteFilesResponse {
  total_files: number;
  deleted_count: number;
  failed_count: number;
  results: DeleteResult[];
  space_freed_mb: number;
}

interface DeleteResult {
  path: string;
  success: boolean;
  error_message?: string;
}
```

**Errors**:
- `DELETION_NOT_CONFIRMED`: confirm=false
- `NO_FILES_SPECIFIED`: file_paths is empty

---

## Operation History Commands

### `get_operation_history`

Retrieve operation history from database.

**Request**:
```typescript
interface GetOperationHistoryRequest {
  limit?: number;                 // Default: 100
  offset?: number;                // Default: 0
  operation_type?: "move" | "delete" | "skip";
  rule_id?: string;
  start_date?: string;            // ISO 8601
  end_date?: string;              // ISO 8601
}
```

**Response**:
```typescript
interface GetOperationHistoryResponse {
  operations: HistoryOperation[];
  total_count: number;
  has_more: boolean;
}

interface HistoryOperation {
  id: string;
  timestamp: string;
  operation_type: "move" | "delete" | "skip";
  source_path: string;
  destination_path: string | null;
  file_size: number;
  checksum: string;
  rule_id: string;
  rule_name: string;
  dry_run: boolean;
  success: boolean;
  error_message: string | null;
}
```

**Errors**:
- `DATABASE_ERROR`: Failed to query database

---

## Configuration Commands

### `get_configuration`

Get current application configuration.

**Request**: None

**Response**:
```typescript
interface GetConfigurationResponse {
  config: Configuration;
}

interface Configuration {
  general: {
    log_level: "DEBUG" | "INFO" | "WARNING" | "ERROR";
    auto_run_on_startup: boolean;
    auto_run_interval_minutes: number;
    enable_notifications: boolean;
    cache_enabled: boolean;
  };
  paths: {
    screenshot_source: string;
    screenshot_destination: string;
    monitored_directories: string[];
  };
  thresholds: {
    large_file_mb: number;
    old_file_days: number;
  };
  duplicate_handling: {
    auto_delete_duplicates: boolean;
    always_keep_oldest: boolean;
  };
}
```

**Errors**:
- `CONFIG_READ_FAILED`: Cannot read configuration

---

### `update_configuration`

Update application configuration.

**Request**:
```typescript
interface UpdateConfigurationRequest {
  updates: Partial<Configuration>;
}
```

**Response**:
```typescript
interface UpdateConfigurationResponse {
  config: Configuration;  // Updated configuration
}
```

**Errors**:
- `VALIDATION_FAILED`: Configuration validation failed
- `CONFIG_WRITE_FAILED`: Cannot write configuration

---

### `export_configuration`

Export configuration to file.

**Request**:
```typescript
interface ExportConfigurationRequest {
  destination_path: string;  // Where to save TOML file
}
```

**Response**:
```typescript
interface ExportConfigurationResponse {
  success: boolean;
  file_path: string;
  message: string;
}
```

**Errors**:
- `EXPORT_FAILED`: Cannot write to destination
- `PERMISSION_DENIED`: No write access to destination

---

### `import_configuration`

Import configuration from file.

**Request**:
```typescript
interface ImportConfigurationRequest {
  source_path: string;  // Path to TOML file
  merge: boolean;       // If true, merge with existing; if false, replace
}
```

**Response**:
```typescript
interface ImportConfigurationResponse {
  success: boolean;
  rules_imported: number;
  rules_updated: number;
  message: string;
}
```

**Errors**:
- `IMPORT_FAILED`: Cannot read source file
- `VALIDATION_FAILED`: Invalid TOML syntax or schema
- `FILE_NOT_FOUND`: Source file doesn't exist

---

### `detect_screenshot_location`

Auto-detect macOS screenshot save location.

**Request**: None

**Response**:
```typescript
interface DetectScreenshotLocationResponse {
  location: string;  // Detected path (e.g., "/Users/daniel/Desktop")
  method: "system_default" | "user_preference" | "fallback";
  confidence: "high" | "medium" | "low";
}
```

**Errors**:
- `DETECTION_FAILED`: Cannot determine screenshot location

---

## System Commands

### `get_system_status`

Get application system status and health.

**Request**: None

**Response**:
```typescript
interface GetSystemStatusResponse {
  status: "healthy" | "degraded" | "error";
  uptime_seconds: number;
  memory_usage_mb: number;
  database_size_mb: number;
  cache_size_mb: number;
  active_operations: number;
  last_scan_time: string | null;
  issues: SystemIssue[];
}

interface SystemIssue {
  severity: "warning" | "error";
  code: string;
  message: string;
  suggested_action: string;
}
```

**Errors**: None (returns degraded/error status instead)

---

### `clear_cache`

Clear checksum cache and operation history.

**Request**:
```typescript
interface ClearCacheRequest {
  clear_checksums: boolean;
  clear_history: boolean;
  older_than_days?: number;  // Optional: only clear items older than X days
}
```

**Response**:
```typescript
interface ClearCacheResponse {
  checksums_deleted: number;
  history_deleted: number;
  space_freed_mb: number;
}
```

**Errors**:
- `DATABASE_ERROR`: Failed to clear cache

---

## Progress Events

For long-running operations (scan, execute), the backend emits progress events via Tauri's event system.

**Event**: `operation_progress`

```typescript
interface OperationProgressEvent {
  operation_id: string;
  operation_type: "scan" | "execute";
  progress_percent: number;      // 0-100
  current_file: string;          // Currently processing file
  files_processed: number;
  total_files: number;
  estimated_time_remaining_ms: number;
}
```

**Usage**:
```typescript
import { listen } from '@tauri-apps/api/event';

const unlisten = await listen<OperationProgressEvent>('operation_progress', (event) => {
  console.log(`Progress: ${event.payload.progress_percent}%`);
});
```

---

## Common Error Codes

| Code | Description | User Action |
|------|-------------|-------------|
| `VALIDATION_FAILED` | Input validation failed | Check input and try again |
| `PERMISSION_DENIED` | Insufficient permissions | Check file/directory permissions |
| `FILE_NOT_FOUND` | File doesn't exist | Verify file path |
| `CONFIG_INVALID` | Configuration is invalid | Check configuration file syntax |
| `CONFIG_READ_FAILED` | Cannot read config | Check file permissions |
| `CONFIG_WRITE_FAILED` | Cannot write config | Check file permissions and disk space |
| `DATABASE_ERROR` | Database operation failed | Check database file integrity |
| `DISK_FULL` | Insufficient disk space | Free up disk space |
| `OPERATION_CANCELLED` | User cancelled operation | None |
| `SCAN_FAILED` | Scan operation failed | Check permissions and paths |
| `EXECUTION_FAILED` | Execution failed | Check operation log |

---

## Notes

1. **Async Operations**: All commands are async and return Promises
2. **Timeouts**: Commands timeout after 30 seconds for normal operations, 5 minutes for scan/execute
3. **Concurrency**: Only one scan or execute operation can run at a time
4. **State Management**: Frontend should cache configuration and rules to minimize IPC calls
5. **Error Recovery**: All commands are idempotent where possible
6. **Versioning**: API version is 1.0.0, changes require version bump
