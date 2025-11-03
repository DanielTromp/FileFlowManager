# Implementation Plan: FileFlow Manager

**Branch**: `001-fileflow-manager` | **Date**: 2025-11-03 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/001-fileflow-manager/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

FileFlow Manager is an intelligent, automated file organization system for macOS that enables users to organize files using extensible rule-based management. The core value proposition is automated screenshot organization (P1 MVP), with extensibility for custom rules (P2), and utility features for large/old file cleanup (P3).

**Technical Approach**: Desktop application with Python 3.10+ backend handling file operations, rule engine, and data persistence; Tauri + Svelte frontend for native macOS GUI; IPC bridge for backend-frontend communication; SQLite for operation history and checksum caching; Typer for full-featured CLI.

## Technical Context

**Language/Version**: Python 3.10+, TypeScript 5.0+, Rust (for Tauri bridge)
**Primary Dependencies**:
  - Backend: Typer (CLI), Pydantic (validation), tomli/tomllib (TOML parsing)
  - Frontend: Tauri 1.5+, Svelte 4+, TypeScript 5+
  - Database: SQLite 3
**Storage**: SQLite (operation history, checksum cache), TOML files (configuration)
**Testing**: pytest (Python backend), Vitest (TypeScript/Svelte frontend), integration tests for IPC
**Target Platform**: macOS 10.15 (Catalina) or newer
**Project Type**: Desktop application (web architecture: Python backend + Tauri/Svelte frontend)
**Performance Goals**:
  - Process 1,000 files in < 30 seconds
  - Calculate SHA-256 for 100MB file in < 2 seconds
  - GUI startup in < 3 seconds
  - Configuration reload < 500ms
**Constraints**:
  - Memory footprint < 200MB
  - No blocking operations on main GUI thread
  - Atomic file operations where possible
  - Operations >5 seconds must show progress indicator
**Scale/Scope**:
  - Single-user desktop application
  - Handle 10,000+ files efficiently
  - 4 main GUI tabs + settings dialog
  - Unlimited custom rules
  - 30+ day uptime without restart

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Core Principles Compliance

- ✅ **Data Safety First**: Dry-run mode mandatory, SHA-256 verification, operation logging, no silent deletion
- ✅ **User Control & Transparency**: All rules visible/editable in GUI, human-readable TOML config, audit logs, toggleable rules
- ✅ **Extensibility & Future-Proofing**: Unlimited custom rules, user-configurable mappings, TOML schema evolution support
- ✅ **Cross-Device Compatibility**: Auto-detect screenshot location, environment variable expansion, portable configuration
- ✅ **Performance & Reliability**: Atomic operations, non-blocking GUI, cancellable background ops, <200MB memory

### Immutable Constraints Compliance

- ✅ **Technical Stack**: Python 3.10+ backend, Tauri + Svelte frontend, TOML config, SQLite database, Typer CLI
- ✅ **File Integrity Rules**: SHA-256 checksums, checksum caching, preserve timestamps/permissions
- ✅ **Architecture Boundaries**: GUI ↔ Backend via Tauri IPC only, CLI-first design, hot-reload config, independent rule toggle
- ✅ **User Experience Mandates**: Progress indicators for >5s ops, actionable errors, confirmation for destructive actions, responsive GUI

### Non-Negotiable Features Coverage

1. ✅ Dry Run Mode: Implemented in rule engine
2. ✅ Duplicate Detection: SHA-256 checksum-based in duplicate_detector module
3. ✅ Date Organization: YYYY/MM/DD structure in date_organizer module
4. ✅ Rollback Logging: SQLite operation history with full audit trail
5. ✅ File Type Presets: Default rules in config/defaults.py
6. ✅ Large File Detection: Threshold-based detection in file_scanner module
7. ✅ Old File Detection: Age-based detection in file_scanner module
8. ✅ Multi-tab GUI: 4 tabs (Dashboard, Rules, Large Files, Old Files) in Svelte routes
9. ✅ CLI Interface: Full feature parity via Typer commands
10. ✅ Config Export/Import: TOML read/write in config_manager module

### Forbidden Patterns Avoidance

- ✅ No silent deletion: All deletes require confirmation OR checksum verification
- ✅ No hardcoded paths: Environment variables (${DESKTOP}, ${DOWNLOADS}) + auto-detection
- ✅ No blocking main thread: Background workers for file operations, async Tauri commands
- ✅ No plain text secrets: N/A (no secrets stored)
- ✅ No in-place modifications: Only move and delete operations
- ✅ No ignored errors: Comprehensive error handling with user-facing messages
- ✅ No sequential processing: Thread pool for parallel file scanning
- ✅ No proprietary formats: TOML (standard, human-readable)
- ✅ No tight coupling: Rules use env vars and templates, not hardcoded paths

### Success Criteria Targets

1. ✅ First rule in <2 min: Simple GUI workflow with sensible defaults
2. ✅ 1000 files in <30s: Parallel processing + checksum caching
3. ✅ Zero data loss: Dry-run + checksums + atomic operations + logging
4. ✅ Config survives crashes: TOML atomic writes + SQLite journaling
5. ✅ Understandable logs: Human-readable operation history with clear descriptions
6. ✅ Add file type in <1 min: Rule editor with templates and hints
7. ✅ 30+ days uptime: No memory leaks, proper resource cleanup, error recovery

**GATE STATUS**: ✅ PASS - All constitutional requirements met. No violations to justify.

## Project Structure

### Documentation (this feature)

```text
specs/[###-feature]/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
backend/                          # Python backend (file operations, logic)
├── fileflow_core/                # Core file operation modules
│   ├── __init__.py
│   ├── models.py                 # Data classes (FileMetadata, etc.)
│   ├── file_scanner.py           # Directory scanning, pattern matching
│   ├── file_operations.py        # Move, delete operations
│   ├── duplicate_detector.py     # SHA-256 duplicate detection
│   ├── date_organizer.py         # Date-based path generation
│   └── rule_engine.py            # Rule execution orchestration
├── fileflow_config/              # Configuration management
│   ├── __init__.py
│   ├── config_manager.py         # TOML config read/write
│   ├── rule_schema.py            # Rule validation and schema
│   └── defaults.py               # Default rules and presets
├── fileflow_storage/             # Persistence layer
│   ├── __init__.py
│   ├── database.py               # SQLite operations
│   ├── cache.py                  # Checksum cache management
│   └── migrations.py             # Database schema migrations
├── fileflow_cli/                 # Command-line interface
│   ├── __init__.py
│   ├── __main__.py               # CLI entry point
│   └── commands.py               # Typer command definitions
├── fileflow_api/                 # Tauri IPC interface
│   ├── __init__.py
│   └── tauri_commands.py         # Tauri command handlers
├── tests/                        # Python tests
│   ├── unit/                     # Unit tests for each module
│   ├── integration/              # Integration tests
│   └── fixtures/                 # Test data and fixtures
├── pyproject.toml                # Python project configuration
├── poetry.lock                   # Dependency lock file
└── README.md                     # Backend documentation

frontend/                         # Tauri + Svelte frontend
├── src/                          # Svelte application
│   ├── routes/
│   │   ├── Dashboard.svelte      # Tab 1: Triggers & status
│   │   ├── Rules.svelte          # Tab 2: Rule configuration
│   │   ├── LargeFiles.svelte     # Tab 3: Large file management
│   │   └── OldFiles.svelte       # Tab 4: Old file management
│   ├── lib/
│   │   ├── components/
│   │   │   ├── RuleEditor.svelte      # Rule creation/edit dialog
│   │   │   ├── FileList.svelte        # Reusable file list
│   │   │   ├── ProgressBar.svelte     # Operation progress
│   │   │   ├── ConfirmDialog.svelte   # Confirmation dialogs
│   │   │   └── RuleCard.svelte        # Rule display card
│   │   ├── stores/
│   │   │   ├── scan.ts           # Scan state management
│   │   │   ├── rules.ts          # Rules state management
│   │   │   ├── files.ts          # Files state management
│   │   │   └── settings.ts       # Settings state management
│   │   ├── api.ts                # Tauri command wrappers
│   │   ├── types.ts              # TypeScript interfaces
│   │   └── utils.ts              # Utility functions
│   ├── app.html                  # HTML template
│   └── app.css                   # Global styles
├── src-tauri/                    # Tauri Rust bridge
│   ├── src/
│   │   └── main.rs               # Tauri main + Python bridge
│   ├── tauri.conf.json           # Tauri configuration
│   ├── Cargo.toml                # Rust dependencies
│   └── icons/                    # Application icons
├── tests/                        # Frontend tests
│   └── unit/                     # Vitest unit tests
├── package.json                  # Node.js dependencies
├── pnpm-lock.yaml                # pnpm lock file
├── vite.config.ts                # Vite configuration
├── tsconfig.json                 # TypeScript configuration
└── README.md                     # Frontend documentation

config/                           # User configuration (at runtime)
├── fileflow.toml                 # Main configuration file
└── fileflow.db                   # SQLite database

.gitignore                        # Git ignore patterns
README.md                         # Project overview
LICENSE                           # License file
```

**Structure Decision**: This is a desktop application using **Option 2: Web application architecture** (backend + frontend). The Python backend (`backend/`) handles all file operations, business logic, and data persistence, while the Tauri + Svelte frontend (`frontend/`) provides the native macOS GUI. Communication occurs through Tauri IPC commands bridged via Rust (`src-tauri/src/main.rs`).

**Rationale**: This structure provides clean separation between backend logic and frontend presentation, enables independent development and testing of each layer, supports both GUI and CLI interfaces from the same backend, and allows the backend to be fully functional without the GUI (CLI-first design per constitution).

## Complexity Tracking

N/A - No constitutional violations. All requirements align with constitutional principles and constraints.