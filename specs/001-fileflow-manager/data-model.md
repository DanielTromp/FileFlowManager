# Data Model: FileFlow Manager

**Created**: 2025-11-03
**Phase**: 1 - Design
**Status**: Complete

## Overview

This document defines all data entities, their fields, relationships, validation rules, and state transitions for FileFlow Manager.

## Entity Relationships

```
┌─────────────────┐
│  Configuration  │
└────────┬────────┘
         │ contains
         ↓
    ┌────────┐
    │  Rule  │────────┐
    └────┬───┘        │
         │ matches    │ triggers
         ↓            ↓
┌──────────────┐  ┌──────────────────┐
│FileMetadata  │  │ FileOperation    │
└──────┬───────┘  └────────┬─────────┘
       │                   │
       │ has               │ logs to
       ↓                   ↓
┌────────────────┐  ┌──────────────┐
│ChecksumCache   │  │  Database    │
└────────────────┘  └──────────────┘
```

## Core Entities

### 1. Rule

**Purpose**: Defines a file organization rule with matching criteria and destination

**Fields**:

| Field | Type | Required | Default | Validation | Description |
|-------|------|----------|---------|------------|-------------|
| `id` | str | ✅ | auto | unique, slug format | Unique identifier (e.g., "screenshots") |
| `enabled` | bool | ✅ | true | - | Whether rule is active |
| `name` | str | ✅ | - | 1-100 chars | Display name |
| `description` | str | ✅ | - | 0-500 chars | User-facing description |
| `source_patterns` | list[str] | ✅ | - | 1+ patterns | Glob patterns (e.g., ["Screenshot*.png"]) |
| `source_directories` | list[str] | ✅ | - | 1+ valid paths | Directories to scan |
| `destination` | str | ✅ | - | valid path template | Target directory with templates |
| `organize_by_date` | bool | ✅ | false | - | Create YYYY/MM/DD subdirectories |
| `file_types` | list[str] | ✅ | - | 1+ extensions | File extensions to match (e.g., [".png"]) |
| `priority` | int | ✅ | 10 | 1-1000 | Execution order (lower = first) |
| `exclude_patterns` | list[str] | ❌ | [] | glob patterns | Patterns to exclude |
| `min_size_kb` | int \\| None | ❌ | None | >= 0 | Minimum file size in KB |
| `max_size_kb` | int \\| None | ❌ | None | >= min_size_kb | Maximum file size in KB |
| `min_age_days` | int \\| None | ❌ | None | >= 0 | Minimum file age in days |
| `max_age_days` | int \\| None | ❌ | None | >= min_age_days | Maximum file age in days |

**Validation Rules**:
- `source_patterns` must be valid glob patterns
- `source_directories` must exist or be creatable
- `destination` must be writable
- `file_types` must start with "."
- `priority` determines execution order (conflicts resolved by config file order)
- Template variables in `destination`: `{year}`, `{month}`, `{day}`, `{name}`
- Environment variables in paths: `${DESKTOP}`, `${DOWNLOADS}`, `${DOCUMENTS}`, `${HOME}`

**State Transitions**:
```
[Created] → enabled=true → [Active]
[Active] → enabled=false → [Disabled]
[Active/Disabled] → [Deleted] (removed from config)
```

**Example**:
```python
from pydantic import BaseModel, Field, field_validator

class Rule(BaseModel):
    id: str = Field(..., pattern=r'^[a-z0-9_-]+$')
    enabled: bool = True
    name: str = Field(..., min_length=1, max_length=100)
    description: str = Field(..., max_length=500)
    source_patterns: list[str] = Field(..., min_length=1)
    source_directories: list[str] = Field(..., min_length=1)
    destination: str
    organize_by_date: bool = False
    file_types: list[str] = Field(..., min_length=1)
    priority: int = Field(10, ge=1, le=1000)
    exclude_patterns: list[str] = Field(default_factory=list)
    min_size_kb: int | None = Field(None, ge=0)
    max_size_kb: int | None = Field(None, ge=0)
    min_age_days: int | None = Field(None, ge=0)
    max_age_days: int | None = Field(None, ge=0)

    @field_validator('file_types')
    def validate_file_types(cls, v):
        for ext in v:
            if not ext.startswith('.'):
                raise ValueError(f"File extension must start with '.': {ext}")
        return v

    @field_validator('max_size_kb')
    def validate_max_size(cls, v, info):
        if v is not None and info.data.get('min_size_kb') is not None:
            if v < info.data['min_size_kb']:
                raise ValueError("max_size_kb must be >= min_size_kb")
        return v
```

---

### 2. FileMetadata

**Purpose**: Represents metadata about a file for scanning and matching

**Fields**:

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `path` | str | ✅ | - | Full absolute file path |
| `filename` | str | ✅ | - | File name with extension |
| `extension` | str | ✅ | - | File extension (includes ".") |
| `size_bytes` | int | ✅ | - | File size in bytes |
| `created_at` | datetime | ✅ | - | File creation timestamp |
| `modified_at` | datetime | ✅ | - | File last modification timestamp |
| `checksum` | str \\| None | ❌ | None | SHA-256 hash (lazy loaded) |
| `matched_rules` | list[str] | ❌ | [] | IDs of rules that match this file |

**Computed Fields**:
- `size_kb`: `size_bytes / 1024`
- `size_mb`: `size_bytes / (1024 * 1024)`
- `age_days`: Days since `modified_at`

**Validation Rules**:
- `path` must exist at time of scan
- `extension` extracted from `filename`
- `checksum` calculated on-demand or from cache

**Example**:
```python
from datetime import datetime
from pathlib import Path
from pydantic import BaseModel, computed_field

class FileMetadata(BaseModel):
    path: str
    filename: str
    extension: str
    size_bytes: int
    created_at: datetime
    modified_at: datetime
    checksum: str | None = None
    matched_rules: list[str] = Field(default_factory=list)

    @classmethod
    def from_path(cls, file_path: Path) -> 'FileMetadata':
        """Create FileMetadata from a file path."""
        stat = file_path.stat()
        return cls(
            path=str(file_path.absolute()),
            filename=file_path.name,
            extension=file_path.suffix,
            size_bytes=stat.st_size,
            created_at=datetime.fromtimestamp(stat.st_ctime),
            modified_at=datetime.fromtimestamp(stat.st_mtime)
        )

    @computed_field
    @property
    def size_mb(self) -> float:
        return self.size_bytes / (1024 * 1024)

    @computed_field
    @property
    def age_days(self) -> int:
        return (datetime.now() - self.modified_at).days
```

---

### 3. FileOperation

**Purpose**: Audit record of a file operation (move, delete, skip)

**Fields**:

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `id` | str | ✅ | UUID4 | Unique operation ID |
| `timestamp` | datetime | ✅ | now | When operation occurred |
| `operation_type` | OperationType | ✅ | - | "move", "delete", or "skip" |
| `source_path` | str | ✅ | - | Original file path |
| `destination_path` | str \\| None | ✅ | - | Target path (None for delete/skip) |
| `file_size` | int | ✅ | - | File size in bytes |
| `checksum` | str | ✅ | - | SHA-256 hash |
| `rule_id` | str | ✅ | - | Rule that triggered operation |
| `dry_run` | bool | ✅ | - | Whether this was a dry-run |
| `success` | bool | ✅ | - | Whether operation succeeded |
| `error_message` | str \\| None | ❌ | None | Error message if failed |
| `duplicate_of` | str \\| None | ❌ | None | Operation ID of original (if duplicate) |

**Enum: OperationType**:
```python
from enum import Enum

class OperationType(str, Enum):
    MOVE = "move"
    DELETE = "delete"
    SKIP = "skip"
```

**Validation Rules**:
- `destination_path` required for "move", None for "delete"/"skip"
- `error_message` required if `success=false`
- `duplicate_of` only set when operation is duplicate deletion

**Database Schema**:
```sql
CREATE TABLE operations (
    id TEXT PRIMARY KEY,
    timestamp DATETIME NOT NULL,
    operation_type TEXT NOT NULL CHECK(operation_type IN ('move', 'delete', 'skip')),
    source_path TEXT NOT NULL,
    destination_path TEXT,
    file_size INTEGER NOT NULL,
    checksum TEXT NOT NULL,
    rule_id TEXT NOT NULL,
    dry_run BOOLEAN NOT NULL,
    success BOOLEAN NOT NULL,
    error_message TEXT,
    duplicate_of TEXT,
    FOREIGN KEY (duplicate_of) REFERENCES operations(id)
);

CREATE INDEX idx_operations_timestamp ON operations(timestamp);
CREATE INDEX idx_operations_rule ON operations(rule_id);
CREATE INDEX idx_operations_checksum ON operations(checksum);
```

**Example**:
```python
from uuid import uuid4
from datetime import datetime
from pydantic import BaseModel

class FileOperation(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    timestamp: datetime = Field(default_factory=datetime.now)
    operation_type: OperationType
    source_path: str
    destination_path: str | None
    file_size: int
    checksum: str
    rule_id: str
    dry_run: bool
    success: bool
    error_message: str | None = None
    duplicate_of: str | None = None
```

---

### 4. ScanResult

**Purpose**: Result of a scan operation, containing matched files and planned operations

**Fields**:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `total_files` | int | ✅ | Total files scanned |
| `matched_files` | int | ✅ | Files matching rules |
| `large_files` | list[FileMetadata] | ✅ | Files exceeding size threshold |
| `old_files` | list[FileMetadata] | ✅ | Files exceeding age threshold |
| `duplicates` | list[tuple[FileMetadata, FileMetadata]] | ✅ | Duplicate file pairs |
| `operations` | list[FileOperation] | ✅ | Planned/executed operations |
| `estimated_space_freed_mb` | float | ✅ | Estimated space savings |

**Computed Fields**:
- `duplicate_count`: `len(duplicates)`
- `operation_summary`: Count by operation type

**Example**:
```python
from pydantic import BaseModel, computed_field

class ScanResult(BaseModel):
    total_files: int
    matched_files: int
    large_files: list[FileMetadata]
    old_files: list[FileMetadata]
    duplicates: list[tuple[FileMetadata, FileMetadata]]
    operations: list[FileOperation]
    estimated_space_freed_mb: float

    @computed_field
    @property
    def operation_summary(self) -> dict[str, int]:
        """Count operations by type."""
        summary = {"move": 0, "delete": 0, "skip": 0}
        for op in self.operations:
            summary[op.operation_type] += 1
        return summary
```

---

### 5. Configuration

**Purpose**: Application-wide configuration including rules and settings

**Fields**:

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `version` | str | ✅ | "1.0.0" | Config file version |
| `general` | GeneralSettings | ✅ | defaults | General app settings |
| `paths` | PathSettings | ✅ | defaults | Path configurations |
| `detection` | DetectionSettings | ✅ | defaults | Detection thresholds |
| `rules` | dict[str, Rule] | ✅ | {} | Rules by ID |
| `duplicate_handling` | DuplicateSettings | ✅ | defaults | Duplicate handling settings |
| `notifications` | NotificationSettings | ✅ | defaults | Notification preferences |

**Sub-Entities**:

#### GeneralSettings
| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `auto_run_enabled` | bool | false | Enable automatic background scanning |
| `auto_run_interval_minutes` | int | 30 | Interval for auto-run (minutes) |
| `log_level` | LogLevel | INFO | Logging level |
| `log_retention_days` | int | 90 | How long to keep logs |
| `checksum_cache_enabled` | bool | true | Enable checksum caching |

#### PathSettings
| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `screenshot_source` | str | "auto" | Screenshot source location |
| `screenshot_destination` | str | "${DOWNLOADS}/screenshots" | Screenshot destination |
| `default_downloads` | str | "${DOWNLOADS}" | Default downloads folder |

#### DetectionSettings
| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `large_file_threshold_mb` | int | 100 | Large file threshold (MB) |
| `old_file_threshold_days` | int | 90 | Old file threshold (days) |

#### DuplicateSettings
| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `check_by_checksum` | bool | true | Use SHA-256 for duplicates |
| `delete_duplicates_with_same_checksum` | bool | true | Auto-delete exact duplicates |
| `skip_duplicates_with_different_content` | bool | true | Skip name conflicts |
| `log_all_duplicates` | bool | true | Log all duplicate detections |

#### NotificationSettings
| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `show_completion_notification` | bool | true | Show notification on completion |
| `show_error_notification` | bool | true | Show notification on error |
| `show_duplicate_found_notification` | bool | false | Show notification for duplicates |

**TOML Representation**:
```toml
[general]
version = "1.0.0"
auto_run_enabled = false
auto_run_interval_minutes = 30
log_level = "INFO"
log_retention_days = 90
checksum_cache_enabled = true

[paths]
screenshot_source = "auto"
screenshot_destination = "${DOWNLOADS}/screenshots"
default_downloads = "${DOWNLOADS}"

[detection]
large_file_threshold_mb = 100
old_file_threshold_days = 90

[rules.screenshots]
# ... (Rule fields)

[duplicate_handling]
check_by_checksum = true
delete_duplicates_with_same_checksum = true
skip_duplicates_with_different_content = true
log_all_duplicates = true

[notifications]
show_completion_notification = true
show_error_notification = true
show_duplicate_found_notification = false
```

---

### 6. ChecksumCacheEntry

**Purpose**: Cached SHA-256 checksum for a file

**Fields**:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `file_path` | str | ✅ | Absolute file path (unique key) |
| `checksum` | str | ✅ | SHA-256 hash (64 hex chars) |
| `file_size` | int | ✅ | File size in bytes (for invalidation) |
| `modified_time` | datetime | ✅ | File mtime (for invalidation) |
| `cached_at` | datetime | ✅ | When cache entry was created |

**Cache Invalidation**:
- Entry invalidated if:
  - `file_size` doesn't match current file size
  - `modified_time` doesn't match current file mtime
  - `cached_at` older than 30 days (configurable)

**Database Schema**:
```sql
CREATE TABLE checksum_cache (
    file_path TEXT PRIMARY KEY,
    checksum TEXT NOT NULL,
    file_size INTEGER NOT NULL,
    modified_time DATETIME NOT NULL,
    cached_at DATETIME NOT NULL
);

CREATE INDEX idx_cache_checksum ON checksum_cache(checksum);
CREATE INDEX idx_cache_cached_at ON checksum_cache(cached_at);
```

**Cleanup Strategy**:
- Automatic cleanup on app startup (delete entries > 30 days old)
- Manual cleanup via CLI: `fileflow config clear-cache`

**Example**:
```python
from datetime import datetime
from pydantic import BaseModel

class ChecksumCacheEntry(BaseModel):
    file_path: str
    checksum: str = Field(..., pattern=r'^[a-f0-9]{64}$')
    file_size: int
    modified_time: datetime
    cached_at: datetime = Field(default_factory=datetime.now)

    def is_valid(self, current_size: int, current_mtime: datetime) -> bool:
        """Check if cache entry is still valid."""
        return (
            self.file_size == current_size and
            self.modified_time == current_mtime
        )
```

---

## Entity Lifecycle Examples

### Example 1: Screenshot Organization Flow

```python
# 1. User creates/enables screenshot rule
rule = Rule(
    id="screenshots",
    enabled=True,
    name="Screenshot Organization",
    source_patterns=["Screenshot*.png"],
    source_directories=["${DESKTOP}"],
    destination="${DOWNLOADS}/screenshots/{year}/{month}/{day}",
    organize_by_date=True,
    file_types=[".png"],
    priority=1
)

# 2. Scanner finds matching files
file_meta = FileMetadata.from_path(Path("~/Desktop/Screenshot 2025-11-03 at 10.30.45.png"))
file_meta.checksum = calculate_sha256(file_meta.path)  # Lazy load checksum
file_meta.matched_rules = ["screenshots"]

# 3. Rule engine creates operation
operation = FileOperation(
    operation_type=OperationType.MOVE,
    source_path=file_meta.path,
    destination_path="~/Downloads/screenshots/2025/11/03/Screenshot 2025-11-03 at 10.30.45.png",
    file_size=file_meta.size_bytes,
    checksum=file_meta.checksum,
    rule_id="screenshots",
    dry_run=True,  # First pass
    success=False  # Not executed yet
)

# 4. User executes (dry_run=False)
operation.dry_run = False
execute_operation(operation)  # Actually moves the file
operation.success = True
log_operation(operation)  # Persist to database

# 5. Cache checksum for future
cache_entry = ChecksumCacheEntry(
    file_path=operation.destination_path,
    checksum=operation.checksum,
    file_size=operation.file_size,
    modified_time=file_meta.modified_at
)
cache_checksum(cache_entry)
```

### Example 2: Duplicate Detection

```python
# 1. Scanner finds potential duplicates
file1 = FileMetadata.from_path(Path("~/Desktop/photo.jpg"))
file2 = FileMetadata.from_path(Path("~/Downloads/photo.jpg"))

# 2. Calculate checksums (check cache first)
file1.checksum = get_cached_checksum(file1.path) or calculate_sha256(file1.path)
file2.checksum = get_cached_checksum(file2.path) or calculate_sha256(file2.path)

# 3. Detect duplicate
if file1.checksum == file2.checksum:
    # Exact duplicate found
    original_op = get_operation_by_checksum(file1.checksum)  # Find original

    duplicate_op = FileOperation(
        operation_type=OperationType.DELETE,
        source_path=file2.path,
        destination_path=None,
        file_size=file2.size_bytes,
        checksum=file2.checksum,
        rule_id="screenshots",
        dry_run=False,
        success=True,
        duplicate_of=original_op.id if original_op else None
    )
    delete_file(file2.path, verify_checksum=file2.checksum)
    log_operation(duplicate_op)
```

## Validation Summary

| Entity | Pydantic Model | Database Table | Config File |
|--------|----------------|----------------|-------------|
| Rule | ✅ | ❌ | ✅ (TOML) |
| FileMetadata | ✅ | ❌ | ❌ |
| FileOperation | ✅ | ✅ (operations) | ❌ |
| ScanResult | ✅ | ❌ | ❌ |
| Configuration | ✅ | ❌ | ✅ (TOML) |
| ChecksumCacheEntry | ✅ | ✅ (checksum_cache) | ❌ |

## Data Flow

```
┌───────────┐
│ TOML File │
└─────┬─────┘
      │ parse
      ↓
┌──────────────┐
│Configuration │
└──────┬───────┘
       │ extract
       ↓
   ┌──────┐
   │ Rule │
   └───┬──┘
       │ scan
       ↓
┌──────────────┐     ┌─────────────────┐
│FileMetadata  │────→│FileOperation    │
└──────────────┘     └────────┬────────┘
                              │ persist
                              ↓
                      ┌───────────────┐
                      │SQLite Database│
                      └───────────────┘
```

## Next Steps

Data model complete. Ready to proceed to **API Contracts** definition.
