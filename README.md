# FileFlow Manager

**Intelligent automated file organization system for macOS**

Version: 0.9.0 (Beta)
Status: Development - Phase 7 Complete (All User Stories), Phase 8 in Progress (Polish)

## Overview

Started as a Spec Kit https://github.com/github/spec-kit test and worked like a charm, now available for Mac.
FileFlow Manager is an intelligent, automated file organization system for macOS that helps you keep your files organized using extensible rule-based management. It automatically organizes screenshots by date, allows custom organization rules for any file type, identifies large and old files for cleanup, and supports configuration import/export for portability across machines.

**Key Features:**
- Automated screenshot organization with date-based folder structure (YYYY/MM/DD)
- Extensible custom rule engine for organizing any file type
- Duplicate file detection using SHA-256 checksums
- Large file discovery and cleanup (configurable threshold)
- Old file discovery and cleanup (configurable age threshold)
- Configuration import/export for easy setup on new machines
- Both CLI and native macOS GUI interfaces
- Dry-run mode for safe preview before execution
- Complete operation history tracking

## Features Implemented

### ✅ Phase 1: Setup (Complete)
- Project structure initialized
- Python backend with Poetry dependency management
- Tauri + Svelte frontend with pnpm
- Development tooling (Black, Ruff, ESLint, Prettier)
- Comprehensive .gitignore for multi-language project

### ✅ Phase 2: Foundational Infrastructure (Complete)

**Backend Foundation**:
- Pydantic data models with full validation
- SQLite database with operations tracking and checksum cache
- TOML configuration management with environment variable expansion
- Rule validation and schema
- SHA-256 checksum caching for performance
- Parallel file scanning with ThreadPoolExecutor
- Atomic file operations (move, delete) with metadata preservation
- Structured logging and custom exceptions
- Database migrations framework

**Frontend Foundation**:
- Tauri IPC bridge (Rust)
- TypeScript type definitions matching backend models
- API wrapper functions for all Tauri commands
- Svelte stores for state management (scan, rules, files, settings)
- Reusable UI components (ProgressBar, ConfirmDialog, FileList)
- Tailwind CSS + daisyUI styling
- Base layout with navigation

### ✅ Phase 3-7: All User Stories Complete

**User Story 1 - Screenshot Organization**:
- Screenshot pattern detection and date extraction
- Date-based folder organization (YYYY/MM/DD)
- Duplicate detection using SHA-256 checksums
- Default screenshot organization rule
- CLI: `fileflow scan`, `fileflow detect-screenshots`
- GUI: Dashboard with scan/execute buttons

**User Story 2 - Custom Rule Creation**:
- Full rule CRUD operations (create, read, update, delete)
- Rule validation and priority management
- GUI rule editor with all configurable options
- Enable/disable rules without deleting
- CLI: `fileflow rules list`, `fileflow rules show <id>`, `fileflow rules create`, `fileflow rules update`, `fileflow rules delete`, `fileflow rules enable/disable`
- GUI: Complete Rules tab with rule editor dialog

**User Story 3 - Large File Cleanup**:
- Configurable size threshold (default 100MB)
- Scan across all monitored directories
- Sort by size, filter by location
- Batch delete with confirmation and space estimate
- CLI: `fileflow files large`, `fileflow files delete`
- GUI: Large Files tab with filtering and batch actions

**User Story 4 - Old File Cleanup**:
- Configurable age threshold (default 90 days)
- Scan based on modification date
- Sort by age, filter by type
- Batch delete with confirmation
- CLI: `fileflow files old`, `fileflow files delete`
- GUI: Old Files tab with filtering and batch actions

**User Story 5 - Configuration Portability**:
- Export configuration to any location
- Import with merge or replace strategies
- Environment variable expansion (${HOME}, ${DESKTOP}, etc.)
- Configuration validation and error reporting
- CLI: `fileflow config-show`, `fileflow config-export`, `fileflow config-import`, `fileflow config-import-merge`, `fileflow config-validate`, `fileflow config-edit`, `fileflow config-reset`
- GUI: Settings tab with export/import/preview

## Project Structure

```
.
├── backend/                      # Python backend
│   ├── fileflow_core/           # Core file operations
│   │   ├── models.py            # Pydantic data models
│   │   ├── file_scanner.py      # Directory scanning
│   │   ├── file_operations.py   # Atomic file ops
│   │   ├── duplicate_detector.py # Duplicate detection
│   │   ├── date_organizer.py    # Date-based organization
│   │   ├── rule_engine.py       # Rule processing
│   │   ├── logging_config.py    # Logging setup
│   │   └── exceptions.py        # Custom exceptions
│   ├── fileflow_config/         # Configuration
│   │   ├── config_manager.py    # TOML config management
│   │   ├── rule_schema.py       # Rule validation
│   │   └── defaults.py          # Default rules
│   ├── fileflow_storage/        # Persistence
│   │   ├── database.py          # SQLite operations
│   │   ├── cache.py             # Checksum cache
│   │   └── migrations.py        # DB migrations
│   ├── fileflow_cli/            # CLI interface
│   │   ├── __main__.py          # Entry point
│   │   └── commands.py          # Typer commands
│   └── pyproject.toml           # Poetry config
│
├── frontend/                    # Tauri + Svelte frontend
│   ├── src/
│   │   ├── routes/
│   │   │   ├── +layout.svelte   # Base layout
│   │   │   ├── +page.svelte     # Index
│   │   │   └── Dashboard.svelte # Main dashboard
│   │   ├── lib/
│   │   │   ├── components/      # Reusable components
│   │   │   ├── stores/          # State management
│   │   │   ├── api.ts           # Tauri API wrappers
│   │   │   └── types.ts         # TypeScript types
│   │   ├── app.css              # Global styles
│   │   └── app.html             # HTML template
│   ├── src-tauri/
│   │   ├── src/main.rs          # Tauri bridge
│   │   ├── Cargo.toml           # Rust dependencies
│   │   └── tauri.conf.json      # Tauri config
│   └── package.json             # Node.js dependencies
│
├── specs/001-fileflow-manager/  # Design documents
│   ├── spec.md                  # Feature specification
│   ├── plan.md                  # Implementation plan
│   ├── tasks.md                 # Task breakdown (40/170 complete)
│   ├── data-model.md            # Data models
│   ├── contracts/               # API contracts
│   └── quickstart.md            # Developer guide
│
└── README.md                    # This file
```

## Technology Stack

### Backend
- **Python 3.10+** with type hints
- **Poetry** - Dependency management
- **Typer** - CLI framework
- **Pydantic v2** - Data validation
- **SQLite 3** - Database
- **pytest** - Testing

### Frontend
- **Tauri 1.5+** - Desktop framework
- **Svelte 4+** - UI framework
- **TypeScript 5.0+** - Type safety
- **Tailwind CSS + daisyUI** - Styling
- **Vite** - Build tool

### Development Tools
- **Black, Ruff** - Python formatting/linting
- **ESLint, Prettier** - TypeScript/Svelte formatting
- **mypy** - Python type checking

## Current Status

### Completed (136 tasks / 170 total = 80%)
- ✅ Phase 1: Setup (9/9 tasks)
- ✅ Phase 2: Foundational (18/18 tasks)
- ✅ Phase 3: User Story 1 - Screenshot Organization (24/24 tasks, 100%)
- ✅ Phase 4: User Story 2 - Custom Rule Creation (29/29 tasks, 100%)
- ✅ Phase 5: User Story 3 - Large File Cleanup (18/18 tasks, 100%)
- ✅ Phase 6: User Story 4 - Old File Cleanup (16/16 tasks, 100%)
- ✅ Phase 7: User Story 5 - Configuration Portability (22/22 tasks, 100%)
- 🔄 Phase 8: Polish & Cross-Cutting Concerns (0/34 tasks, in progress)

### All User Stories: COMPLETE
- ✅ Screenshot organization with intelligent date-based structure
- ✅ Custom rule creation with full CRUD operations
- ✅ Large file discovery and cleanup
- ✅ Old file discovery and cleanup
- ✅ Configuration import/export with environment variable support
- ✅ Full-featured CLI with 20+ commands
- ✅ Native macOS GUI with 5 tabs (Dashboard, Rules, Large Files, Old Files, Settings)
- ✅ Complete Tauri IPC bridge connecting GUI to Python backend

### Remaining Work (Phase 8 - Polish)
- Error handling improvements and comprehensive error messages
- Performance optimization (caching, parallel processing)
- System integration (health checks, cache management)
- CLI enhancements (history, duplicates, shell completion, JSON output)
- GUI polish (keyboard shortcuts, dark mode, loading states, notifications)
- Documentation (backend/frontend READMEs, docstrings, CI/CD)
- Build & distribution (setup scripts, DMG packaging, production testing)

## Getting Started

### Prerequisites
- macOS 10.15 (Catalina) or newer
- Python 3.10+
- Node.js 18.0+
- Rust 1.70+ (for Tauri)
- pnpm

### Installation

1. **Clone the repository**:
```bash
git clone <repository-url>
cd fileflow-manager
```

2. **Install backend dependencies**:
```bash
cd backend
poetry install
```

3. **Install frontend dependencies**:
```bash
cd frontend
pnpm install
```

### Development

**Run CLI** (production-ready with 20+ commands):
```bash
cd backend

# File organization
poetry run fileflow scan                    # Organize files with dry-run
poetry run fileflow scan --execute          # Execute file operations

# Rule management
poetry run fileflow rules list              # List all rules
poetry run fileflow rules show <id>         # Show rule details
poetry run fileflow rules create            # Create new rule (interactive)
poetry run fileflow rules update <id>       # Update rule
poetry run fileflow rules delete <id>       # Delete rule
poetry run fileflow rules enable <id>       # Enable rule
poetry run fileflow rules disable <id>      # Disable rule

# File discovery
poetry run fileflow files large             # Find large files
poetry run fileflow files old               # Find old files
poetry run fileflow files delete <paths...> # Delete files

# Configuration
poetry run fileflow config-show             # Show current configuration
poetry run fileflow config-export <path>    # Export configuration
poetry run fileflow config-import <path>    # Import configuration (replace)
poetry run fileflow config-import-merge <path>  # Import and merge
poetry run fileflow config-validate [path]  # Validate configuration
poetry run fileflow config-edit             # Edit configuration in $EDITOR
poetry run fileflow config-reset            # Reset to defaults

# Utilities
poetry run fileflow detect-screenshots      # Detect screenshot location
```

**Run GUI** (fully functional native macOS app):
```bash
cd frontend
pnpm tauri dev
```

The GUI provides 5 tabs:
- **Dashboard**: Scan and organize files with dry-run preview
- **Rules**: Create and manage organization rules
- **Large Files**: Discover and cleanup large files
- **Old Files**: Discover and cleanup old files
- **Settings**: Import/export configuration, view current settings

## Documentation

- **Specification**: `specs/001-fileflow-manager/spec.md`
- **Implementation Plan**: `specs/001-fileflow-manager/plan.md`
- **Task Breakdown**: `specs/001-fileflow-manager/tasks.md`
- **Data Models**: `specs/001-fileflow-manager/data-model.md`
- **API Contracts**: `specs/001-fileflow-manager/contracts/`
- **Developer Quickstart**: `specs/001-fileflow-manager/quickstart.md`

## License

TBD

## Contributing

This project is currently in early development. Contributions will be welcome once the MVP is complete.
