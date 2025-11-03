# API Contracts Overview

**Feature**: FileFlow Manager
**Created**: 2025-11-03
**Status**: Design Phase

## Purpose

This directory contains all API contract specifications for FileFlow Manager. These contracts define the interfaces between system components and serve as the source of truth for implementation.

## Contract Documents

### [tauri-ipc.md](./tauri-ipc.md)

Defines all Tauri IPC commands for communication between the Svelte frontend and Python backend.

**Covers**:
- File scanning commands (scan_files, execute_operations, cancel_operation)
- Rule management commands (get_rules, create_rule, update_rule, delete_rule, toggle_rule)
- File management commands (get_large_files, get_old_files, delete_files)
- Operation history commands (get_operation_history)
- Configuration commands (get_configuration, update_configuration, export/import, detect_screenshot_location)
- System commands (get_system_status, clear_cache)
- Progress events for long-running operations

**Key Details**:
- 25+ IPC commands
- TypeScript request/response interfaces
- Comprehensive error handling with error codes
- Progress event system for async operations
- 30-second timeout for normal operations, 5 minutes for scan/execute

### [cli.md](./cli.md)

Defines all CLI commands and their interfaces for terminal usage.

**Covers**:
- Main commands: scan, rules, files, history, config, daemon, detect-screenshots
- Rule management: list, show, create, update, delete, enable, disable
- File management: large, old, duplicates
- Configuration: show, edit, export, import, validate, reset
- Multiple output formats: table, JSON, simple
- Interactive and non-interactive modes
- Shell completion support

**Key Details**:
- Full feature parity with GUI
- Interactive creation wizards
- Rich table output with colors
- JSON output for scripting
- Environment variable support
- Exit code conventions

## Design Principles

### 1. Consistency

All APIs follow consistent patterns:
- Request/response structure
- Error handling (error codes + messages)
- Naming conventions (snake_case for backend, camelCase for frontend)
- Validation rules

### 2. Type Safety

- TypeScript interfaces for all Tauri IPC
- Pydantic models for all Python data
- Explicit validation at API boundaries
- No implicit type coercion

### 3. Error Handling

Standard error format across all APIs:
```typescript
interface CommandError {
  code: string;        // Machine-readable (e.g., "VALIDATION_FAILED")
  message: string;     // Human-readable (e.g., "Rule name is required")
  details?: any;       // Optional context
}
```

Common error codes:
- `VALIDATION_FAILED`: Input validation failed
- `PERMISSION_DENIED`: Insufficient permissions
- `FILE_NOT_FOUND`: File doesn't exist
- `CONFIG_INVALID`: Configuration error
- `DATABASE_ERROR`: Database operation failed
- `DISK_FULL`: Insufficient disk space

### 4. Async Operations

Long-running operations (scan, execute) support:
- Progress events via Tauri event system
- Cancellation support
- Timeout handling
- Non-blocking execution

### 5. Idempotency

Where possible, operations are idempotent:
- Enabling an already-enabled rule succeeds
- Creating duplicate rules returns existing rule
- Multiple scans with same parameters return same results

## Contract Guarantees

### Breaking Changes

Changes that break these contracts require major version bump:
- Removing or renaming commands
- Changing required parameters
- Changing response structure
- Removing error codes

### Non-Breaking Changes

These changes do NOT break contracts:
- Adding new optional parameters
- Adding new response fields
- Adding new error codes
- Adding new commands

### Versioning

API version: **1.0.0**

Version information available via:
- Tauri IPC: `get_system_status` response includes API version
- CLI: `fileflow --version` shows API version

## Request/Response Examples

### Tauri IPC Example

**Request** (from Svelte):
```typescript
import { invoke } from '@tauri-apps/api';

const result = await invoke<ScanFilesResponse>('scan_files', {
  dry_run: true,
  rule_ids: ['screenshot-org']
});

console.log(`Found ${result.files_matched} files`);
```

**Response**:
```json
{
  "scan_id": "scan-550e8400-e29b-41d4-a716-446655440000",
  "timestamp": "2025-11-03T10:30:45.123Z",
  "total_files_scanned": 247,
  "files_matched": 42,
  "planned_operations": [...],
  "duplicate_pairs": [],
  "estimated_space_freed_mb": 0,
  "scan_duration_ms": 1230
}
```

**Error Response**:
```json
{
  "code": "PERMISSION_DENIED",
  "message": "Cannot read directory: /Users/daniel/Desktop",
  "details": {
    "directory": "/Users/daniel/Desktop",
    "required_permission": "read"
  }
}
```

### CLI Example

**Command**:
```bash
fileflow scan --dry-run --rules screenshot-org
```

**Output** (table format):
```
FileFlow Scan Results
════════════════════════════════════════════════════════════════

Scan completed in 1.2s

Files Scanned:       247
Files Matched:        42

Planned Operations
────────────────────────────────────────────────────────────────
MOVE    Screenshot 2025-11-03 at 10.30.45.png
        → ~/Downloads/screenshots/2025/11/03/
        (Rule: Screenshot Organization)

... [41 more operations]

To execute these operations, run:
  fileflow scan --execute --rules screenshot-org
```

**Output** (JSON format):
```bash
fileflow scan --dry-run --rules screenshot-org --output-format json
```

```json
{
  "scan_id": "scan-550e8400-e29b-41d4-a716-446655440000",
  "timestamp": "2025-11-03T10:30:45.123Z",
  "total_files_scanned": 247,
  "files_matched": 42,
  "planned_operations": [...],
  "scan_duration_ms": 1230
}
```

## Data Flow

### File Organization Flow

```
1. User triggers scan (GUI or CLI)
   ↓
2. Frontend → Backend: invoke('scan_files', {dry_run: true})
   ↓
3. Backend scans directories, matches rules, detects duplicates
   ↓ (emits progress events)
4. Backend → Frontend: ScanFilesResponse with planned operations
   ↓
5. User reviews operations in GUI
   ↓
6. User confirms execution
   ↓
7. Frontend → Backend: invoke('execute_operations', {operation_ids, confirm: true})
   ↓
8. Backend executes operations
   ↓ (emits progress events)
9. Backend → Frontend: ExecuteOperationsResponse with results
   ↓
10. Backend → Database: Log operations to SQLite
    ↓
11. Frontend displays results to user
```

### Rule Creation Flow

```
1. User opens rule editor (GUI) or runs create command (CLI)
   ↓
2. User fills in rule details
   ↓
3. Frontend validates input
   ↓
4. Frontend → Backend: invoke('create_rule', {rule})
   ↓
5. Backend validates rule (Pydantic)
   ↓
6. Backend saves to TOML config
   ↓
7. Backend → Frontend: CreateRuleResponse with created rule
   ↓
8. Frontend updates rules list
```

## Implementation Checklist

When implementing these contracts:

### Backend (Python)

- [ ] Create Pydantic models for all request/response types
- [ ] Implement Tauri command handlers in `fileflow_api/tauri_commands.py`
- [ ] Implement CLI commands in `fileflow_cli/commands.py`
- [ ] Add input validation for all commands
- [ ] Implement error handling with standard error codes
- [ ] Add progress event emission for long-running operations
- [ ] Write unit tests for each command
- [ ] Write integration tests for request/response flow

### Frontend (TypeScript/Svelte)

- [ ] Create TypeScript interfaces matching contract types
- [ ] Create API wrapper functions in `lib/api.ts`
- [ ] Implement error handling UI for all error codes
- [ ] Add progress indicators for long-running operations
- [ ] Create event listeners for progress events
- [ ] Write unit tests for API wrappers
- [ ] Write integration tests with mocked backend

### Documentation

- [ ] Generate API documentation from contracts
- [ ] Add usage examples for each command
- [ ] Document all error codes with user-facing explanations
- [ ] Create troubleshooting guide for common errors

## Testing Strategy

### Contract Testing

Each contract should have:

1. **Request Validation Tests**: Verify all invalid inputs are rejected
2. **Response Schema Tests**: Verify responses match contract structure
3. **Error Code Tests**: Verify all documented error codes are returned correctly
4. **Integration Tests**: Verify end-to-end request/response flow

### Example Test Cases

**Tauri IPC**:
```typescript
describe('scan_files command', () => {
  test('returns valid ScanFilesResponse', async () => {
    const response = await invoke('scan_files', { dry_run: true });
    expect(response).toHaveProperty('scan_id');
    expect(response).toHaveProperty('planned_operations');
    expect(Array.isArray(response.planned_operations)).toBe(true);
  });

  test('returns PERMISSION_DENIED when directory unreadable', async () => {
    await expect(
      invoke('scan_files', { dry_run: true })
    ).rejects.toMatchObject({
      code: 'PERMISSION_DENIED'
    });
  });
});
```

**CLI**:
```bash
# Test dry-run scan
./test_cli.sh "fileflow scan --dry-run" \
  --expect-exit 0 \
  --expect-output "Scan completed"

# Test invalid rule ID
./test_cli.sh "fileflow scan --rules invalid-rule" \
  --expect-exit 1 \
  --expect-output "INVALID_RULE_ID"
```

## Maintenance

### Adding New Commands

1. Document in appropriate contract file (tauri-ipc.md or cli.md)
2. Add request/response interfaces
3. Define error codes
4. Add examples
5. Update this README with new command count
6. Increment API version if breaking change

### Modifying Existing Commands

1. Update contract documentation
2. Mark changes as breaking or non-breaking
3. Update API version if breaking
4. Add migration guide if breaking
5. Update all tests

## Related Documents

- [spec.md](../spec.md): Feature specification and requirements
- [data-model.md](../data-model.md): Data entity definitions
- [research.md](../research.md): Technical research and decisions
- [plan.md](../plan.md): Implementation plan

## Questions?

For questions about these contracts, see:
- Technical decisions: [research.md](../research.md)
- Data structures: [data-model.md](../data-model.md)
- Requirements: [spec.md](../spec.md)
