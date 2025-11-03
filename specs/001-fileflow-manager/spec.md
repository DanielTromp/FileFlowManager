# Feature Specification: FileFlow Manager

**Feature Branch**: `001-fileflow-manager`
**Created**: 2025-11-03
**Status**: Draft
**Input**: User description: "Intelligent automated file organization system for macOS with extensible rule-based management"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Screenshot Organization (Priority: P1)

As a macOS user who takes frequent screenshots, I want screenshots automatically organized by date so that I can easily find them later without manually sorting through my Desktop or Downloads folder.

**Why this priority**: Screenshots are the most common pain point for macOS users - they clutter the Desktop/Downloads and are difficult to find later. This is the core value proposition and demonstrates immediate benefit.

**Independent Test**: Can be fully tested by taking screenshots, triggering organization (dry-run first, then execute), and verifying they're moved to `~/Downloads/screenshots/YYYY/MM/DD/` structure while preserving all file metadata.

**Acceptance Scenarios**:

1. **Given** 10 screenshots on Desktop with pattern "Screenshot 2025-11-03 at 10.30.45.png", **When** user runs dry-run scan, **Then** system shows preview of moving files to `~/Downloads/screenshots/2025/11/03/` without actually moving them
2. **Given** dry-run preview shows correct organization plan, **When** user executes organization, **Then** all screenshots are moved to date-organized folders and Desktop is clean
3. **Given** user has already organized screenshots once, **When** user takes new screenshot and runs organization again, **Then** system only processes new screenshot and doesn't re-process existing organized files
4. **Given** duplicate screenshot exists in both Desktop and destination folder with identical SHA-256 checksum, **When** organization runs, **Then** system detects duplicate and offers to delete the Desktop copy while preserving original

---

### User Story 2 - Custom Rule Creation (Priority: P2)

As a user with specific organization needs (e.g., 3D printing files, code files, audio files), I want to create custom rules so that I can organize any file type into any folder structure I choose.

**Why this priority**: After proving value with screenshots, extensibility is critical for long-term adoption. Users need to organize more than just screenshots to justify keeping the app installed.

**Independent Test**: Can be fully tested by creating a new rule through the GUI (e.g., "Organize .stl files to ~/Downloads/3d-printing"), placing test files matching the pattern, and verifying they're organized according to the custom rule.

**Acceptance Scenarios**:

1. **Given** user opens Rules Configuration tab, **When** user clicks "Add New Rule", **Then** rule editor dialog opens with empty form and variable hints ({year}, {month}, {day}, {name})
2. **Given** user fills in rule details (name, source patterns, source directories, destination, file types, priority), **When** user clicks "Save Rule", **Then** new rule appears in rules list with correct status and can be toggled on/off
3. **Given** multiple rules with different priorities exist, **When** a file matches multiple rules, **Then** only the highest priority (lowest number) rule processes the file
4. **Given** user has enabled a custom rule for .stl files, **When** user downloads an .stl file and runs organization, **Then** file moves to the custom destination specified in the rule

---

### User Story 3 - Large File Cleanup (Priority: P3)

As a user running low on disk space, I want to see all files larger than a threshold (e.g., 100MB) across monitored directories so that I can quickly identify and delete space hogs.

**Why this priority**: This is a valuable utility feature but not core to the file organization mission. Users can achieve immediate space savings and see tangible benefit beyond organization.

**Independent Test**: Can be fully tested by placing files of various sizes (50MB, 150MB, 500MB, 2GB) in monitored directories, navigating to "Large Files" tab, adjusting threshold, and verifying correct files appear sorted by size with accurate size display.

**Acceptance Scenarios**:

1. **Given** user is on Large Files tab with threshold set to 100MB, **When** page loads, **Then** system displays all files >100MB from monitored directories sorted by size (largest first) with file path, modification date, and size
2. **Given** multiple large files are displayed, **When** user selects 3 files and clicks "Delete Selected", **Then** system shows confirmation dialog with total space to be freed
3. **Given** user confirms deletion, **When** deletion completes, **Then** files are permanently deleted, list refreshes, and total count/size updates
4. **Given** user adjusts threshold from 100MB to 500MB, **When** threshold changes, **Then** list immediately updates to show only files >500MB

---

### User Story 4 - Old File Cleanup (Priority: P3)

As a user who wants to maintain a clean filesystem, I want to see all files older than a threshold (e.g., 90 days) so that I can review and delete outdated files I no longer need.

**Why this priority**: Similar to large file cleanup, this is a utility feature that adds value but is not core to the organization mission. Helps users maintain hygiene over time.

**Independent Test**: Can be fully tested by placing files with various modification dates in monitored directories, navigating to "Old Files" tab, adjusting age threshold, and verifying correct files appear sorted by age with accurate date display.

**Acceptance Scenarios**:

1. **Given** user is on Old Files tab with threshold set to 90 days, **When** page loads, **Then** system displays all files with modification date >90 days ago sorted by age (oldest first) with file path, modification date, and size
2. **Given** user adjusts threshold from 90 to 180 days, **When** threshold changes, **Then** list updates to show only files older than 180 days
3. **Given** user selects "Select All", **When** all files are selected, **Then** "Delete Selected" button shows total count and space to be freed
4. **Given** user deletes old files, **When** deletion completes, **Then** files are removed and file count decreases

---

### User Story 5 - Configuration Portability (Priority: P4)

As a user with multiple Macs or who wants to backup my setup, I want to export and import my configuration so that I can use the same rules on all my devices or recover my setup after reinstalling.

**Why this priority**: This is important for power users and multi-device workflows, but most users will configure once and not need this feature frequently.

**Independent Test**: Can be fully tested by configuring multiple custom rules, exporting configuration to a TOML file, clearing all rules, importing the TOML file, and verifying all rules are restored with correct settings.

**Acceptance Scenarios**:

1. **Given** user has configured 5 custom rules, **When** user clicks Settings > Export Configuration and chooses location, **Then** system writes fileflow.toml to chosen location with all rule definitions
2. **Given** user has exported configuration on Mac A, **When** user copies fileflow.toml to Mac B and clicks Import Configuration, **Then** all rules from Mac A appear on Mac B with identical settings
3. **Given** imported config contains paths like "${DESKTOP}", **When** rules execute on new Mac, **Then** environment variables correctly resolve to the new Mac's Desktop path

---

### Edge Cases

- What happens when a file matches multiple rules with the same priority?
  - System processes in the order rules appear in configuration (first rule wins)
- What happens when destination folder doesn't exist?
  - System creates the directory structure automatically
- What happens when moving a file would overwrite an existing file with the same name but different content?
  - System skips the operation and logs a "name_conflict" skip reason
- What happens when a file is locked or in use by another application?
  - System logs a permission error with retry suggestion and continues processing other files
- What happens when a file is deleted or moved between dry-run and execution?
  - System logs "file not found" error and continues with remaining operations
- What happens when user has screenshots saved to a custom location (not Desktop)?
  - System auto-detects location via `defaults read com.apple.screencapture location` on first run
- What happens when disk space is insufficient to move a large file?
  - System checks available space before operation and shows clear error with space required vs available
- What happens when a filename contains special characters or is extremely long?
  - System preserves special characters and handles long filenames according to filesystem limits
- What happens when user manually edits the TOML config file with invalid syntax?
  - System shows validation error on next load with specific line/column of syntax error
- What happens when the SQLite database becomes corrupted?
  - System falls back to operating without history (warns user) and provides "rebuild database" option

## Requirements *(mandatory)*

### Functional Requirements

#### Core Organization

- **FR-001**: System MUST scan specified source directories for files matching configured rules
- **FR-002**: System MUST provide dry-run mode that shows what would happen without executing any file operations
- **FR-003**: System MUST move files to destination directories while preserving original modification timestamps and file permissions
- **FR-004**: System MUST organize files into date-based subdirectories (YYYY/MM/DD) when rule specifies organize_by_date=true
- **FR-005**: System MUST process rules in priority order (lowest priority number first)
- **FR-006**: System MUST skip files already processed by higher-priority rules (no double-processing)

#### Duplicate Detection

- **FR-007**: System MUST calculate SHA-256 checksums for duplicate detection
- **FR-008**: System MUST cache checksums in SQLite database to avoid recalculation
- **FR-009**: System MUST detect duplicates by comparing checksums, not file names
- **FR-010**: System MUST offer to delete duplicate files when source and destination have identical checksums
- **FR-011**: System MUST skip files with same name but different checksums (name conflict) and log the skip reason

#### Rule Management

- **FR-012**: System MUST support unlimited custom rules with user-defined names, descriptions, patterns, and destinations
- **FR-013**: System MUST allow users to enable/disable rules independently without deleting them
- **FR-014**: System MUST support glob patterns for file matching (e.g., "Screenshot*.png", "*.pdf")
- **FR-015**: System MUST support exclude patterns to prevent certain files from matching (e.g., exclude "Screenshot*" from generic image rule)
- **FR-016**: System MUST support environment variable expansion in paths (${DESKTOP}, ${DOWNLOADS}, ${DOCUMENTS}, ${HOME})
- **FR-017**: System MUST support template variables in destination paths ({year}, {month}, {day}, {name})
- **FR-018**: System MUST validate rule configuration before saving (e.g., source directories exist, destination is writable)

#### Configuration

- **FR-019**: System MUST store all configuration in human-readable TOML format
- **FR-020**: System MUST support configuration export to user-chosen file location
- **FR-021**: System MUST support configuration import from user-chosen file location
- **FR-022**: System MUST detect screenshot location automatically using macOS system preferences
- **FR-023**: System MUST allow manual override of detected screenshot location
- **FR-024**: System MUST apply configuration changes without requiring application restart

#### Large File Management

- **FR-025**: System MUST identify files larger than configurable threshold (default 100MB) across monitored directories
- **FR-026**: System MUST display large files sorted by size with path, size, and modification date
- **FR-027**: System MUST allow filtering large files by location
- **FR-028**: System MUST support batch deletion of selected large files with confirmation
- **FR-029**: System MUST show total space to be freed before confirming deletion

#### Old File Management

- **FR-030**: System MUST identify files older than configurable threshold (default 90 days) based on modification date
- **FR-031**: System MUST display old files sorted by age with path, size, and modification date
- **FR-032**: System MUST allow filtering old files by type
- **FR-033**: System MUST support batch deletion of selected old files with confirmation

#### Operation History

- **FR-034**: System MUST log all file operations (move, delete, skip) to SQLite database with timestamp, source path, destination path, file size, checksum, rule ID, success status, and error message
- **FR-035**: System MUST display operation history with most recent operations first
- **FR-036**: System MUST allow users to view operation history limited to recent N operations (configurable, default 100)
- **FR-037**: System MUST retain operation logs for configurable period (default 90 days)

#### User Interface

- **FR-038**: System MUST provide GUI with four tabs: Dashboard (triggers & status), Rules Configuration, Large Files, Old Files
- **FR-039**: System MUST show last scan time and active rule count on Dashboard
- **FR-040**: System MUST provide Dry Run and Execute buttons on Dashboard
- **FR-041**: System MUST provide rule editor dialog for creating/editing rules with all configurable options
- **FR-042**: System MUST provide CLI interface with full feature parity to GUI operations
- **FR-043**: System MUST show progress indicators for operations taking >5 seconds
- **FR-044**: System MUST provide actionable error messages that tell users what to do (e.g., "Check file permissions" not just "Permission denied")

#### Safety & Reliability

- **FR-045**: System MUST require explicit user confirmation before deleting any files
- **FR-046**: System MUST never delete files silently without checksum verification or user confirmation
- **FR-047**: System MUST validate checksums before declaring files as duplicates
- **FR-048**: System MUST handle permission errors gracefully without crashing
- **FR-049**: System MUST handle disk space errors gracefully with clear messaging
- **FR-050**: System MUST use atomic file operations where possible to prevent partial moves
- **FR-051**: System MUST not modify files in-place (only move or delete operations)
- **FR-052**: System MUST preserve original file metadata (permissions, timestamps) during move operations

### Key Entities

- **Rule**: Represents a file organization rule with pattern matching criteria, source directories, destination template, priority, and enabled status. Each rule can match multiple files and specifies how those files should be organized.

- **File Metadata**: Represents information about a file including path, filename, extension, size, creation/modification timestamps, cached checksum, and which rules matched it. Used for scanning and decision-making.

- **File Operation Record**: Represents a single file operation (move, delete, skip) with complete audit trail including timestamp, source/destination paths, file size, checksum, which rule triggered it, whether it was a dry-run, success status, and error message. Stored in SQLite for history.

- **Scan Result**: Represents the outcome of scanning source directories, including total files found, files matching rules, detected large files, detected old files, duplicate pairs, planned operations, and estimated space savings. Used to show dry-run previews.

- **Configuration**: Represents all user settings including general settings (log level, auto-run settings, cache enabled), path mappings (screenshot source/destination), detection thresholds (large file size, old file age), all rules, duplicate handling preferences, and notification preferences. Stored in TOML format.

- **Checksum Cache Entry**: Represents a cached SHA-256 checksum for a file including file path, checksum value, file size, modification time (for invalidation), and cache timestamp. Stored in SQLite to avoid recalculating checksums.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Non-technical users can configure their first rule in under 2 minutes from opening the app
- **SC-002**: System processes 1,000 files in under 30 seconds on average hardware (2020 MacBook Air or equivalent)
- **SC-003**: Zero data loss incidents during normal operations (no files accidentally deleted or corrupted)
- **SC-004**: Application starts and displays main interface in under 3 seconds
- **SC-005**: Configuration reload (after import or manual edit) completes in under 500 milliseconds
- **SC-006**: Users can understand what happened by reading the operation log (80% of test users can correctly explain what happened to their files)
- **SC-007**: Adding a new file type category takes under 1 minute (measured from clicking "Add Rule" to successful save)
- **SC-008**: Application runs stable for 30+ days without restart or memory leaks (< 200MB memory footprint maintained)
- **SC-009**: Dry-run preview matches actual execution results 100% of the time (no surprises after execute)
- **SC-010**: 90% of users successfully organize their first batch of files on first attempt without errors
- **SC-011**: Checksum calculation for 100MB file completes in under 2 seconds
- **SC-012**: Moving 100 files across different rules completes in under 3 seconds

### Assumptions

- macOS 10.15 (Catalina) or newer is the target platform
- Users have standard directory permissions for their Home folder (Desktop, Downloads, Documents)
- Users understand basic filesystem concepts (folders, file extensions, file sizes)
- Average hardware has SSD storage (HDD performance may be slower)
- Screenshot patterns follow macOS defaults: "Screenshot YYYY-MM-DD at HH.MM.SS.png" or "Screen Shot YYYY-MM-DD at HH.MM.SS PM.png"
- Users want to organize files in their user directory (not system-wide organization)
- Configuration survives system crashes without corruption (TOML atomic writes + SQLite journaling provide this)
- Users have sufficient disk space for moving files (system checks before operations)
- File operations are not interrupted by system sleep or shutdown (operations are cancellable)
