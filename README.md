# FileFlow Manager

**Intelligent automated file organization system for macOS**

Version: 0.1.1
Status: Beta - Core features complete, polishing in progress

## Overview

FileFlow Manager is an intelligent, automated file organization system for macOS that helps you keep your files organized using extensible rule-based management. It automatically organizes screenshots by date, allows custom organization rules for any file type, identifies large and old files for cleanup, and supports configuration import/export for portability across machines.

**Key Features:**
- 🗂️ Automated screenshot organization with date-based folder structure (DD-MM-YYYY)
- ⚙️ Extensible custom rule engine for organizing any file type
- 🔍 Duplicate file detection using SHA-256 checksums
- 📦 Large file discovery and cleanup (configurable threshold)
- 🕒 Old file discovery and cleanup (configurable age threshold)
- 💾 Configuration import/export for easy setup on new machines
- 🖥️ Native macOS GUI with modern interface (dark mode, loading states, notifications)
- ⌨️ Full-featured CLI with 20+ commands
- 👁️ Dry-run mode for safe preview before execution
- 📊 Complete operation history tracking
- 🌍 European date/time format (24-hour clock, DD-MM-YYYY)

## Getting Started

### Installing from DMG (End Users)

1. **Download the latest DMG** from the [Releases page](https://github.com/DanielTromp/Filefly-specify/releases)
2. **Open the DMG** and drag FileFlow Manager to your Applications folder
3. **Bypass macOS Gatekeeper** (required for unsigned apps):

   **Option 1: Right-click method (easiest)**
   - Locate FileFlow Manager in your Applications folder
   - Right-click (or Control-click) on the app
   - Select "Open" from the menu
   - Click "Open" in the security dialog
   - The app will now run (you only need to do this once)

   **Option 2: Command line method**
   ```bash
   xattr -d com.apple.quarantine "/Applications/FileFlow Manager.app"
   ```

   **Option 3: System Settings method**
   - Try to open the app normally (it will be blocked)
   - Go to System Settings > Privacy & Security
   - Scroll down to find the blocked app message
   - Click "Open Anyway"

**Note:** This app is currently unsigned. We plan to add code signing in a future release.

### Development Setup

#### Prerequisites
- macOS 10.15 (Catalina) or newer
- Python 3.10+
- Node.js 18.0+
- Rust 1.70+ (for Tauri)
- pnpm

#### Installation

1. **Clone the repository**:
```bash
git clone https://github.com/DanielTromp/Filefly-specify.git
cd Filefly-specify
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

#### Running the Application

**GUI Application** (Recommended):
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

**CLI Interface**:
```bash
cd backend

# File organization
poetry run fileflow scan                    # Organize files with dry-run
poetry run fileflow scan --execute          # Execute file operations

# Rule management
poetry run fileflow rules list              # List all rules
poetry run fileflow rules create            # Create new rule (interactive)

# File discovery
poetry run fileflow files large             # Find large files
poetry run fileflow files old               # Find old files

# Configuration
poetry run fileflow config-show             # Show current configuration
poetry run fileflow config-export <path>    # Export configuration
poetry run fileflow config-import <path>    # Import configuration
```

See [CLI Commands](#cli-commands) for the full list of available commands.

### Creating Your First Release

Once you're ready to distribute the app:

```bash
# 1. Update version in package.json and tauri.conf.json
# 2. Commit the changes
git add frontend/package.json frontend/src-tauri/tauri.conf.json
git commit -m "Bump version to 1.0.0"

# 3. Create and push a tag
git tag v1.0.0
git push origin v1.0.0
```

GitHub Actions will automatically:
- Build the backend executable
- Create the macOS DMG
- Publish a GitHub Release with the DMG attached

See [RELEASE.md](RELEASE.md) for detailed release instructions.

## Features

### Automated Screenshot Organization
- Intelligent screenshot detection based on filename patterns
- Date extraction from screenshot filenames
- Organization into YYYY/MM/DD folder structure
- Duplicate detection using SHA-256 checksums
- Configurable destination directory

### Custom Organization Rules
- Full CRUD operations (create, read, update, delete)
- Rule priorities and enable/disable functionality
- Pattern matching (glob patterns, file extensions)
- Age and size filters
- Exclude patterns for fine-grained control
- Date-based organization option
- Duplicate detection per rule

### File Cleanup Tools
- **Large Files**: Find files above a size threshold (default 100MB)
- **Old Files**: Find files older than a date threshold (default 365 days)
- Batch deletion with confirmation
- Space reclamation estimates
- File type filtering
- Pagination for large result sets

### Configuration Management
- Export configuration to TOML files
- Import with merge or replace strategies
- Environment variable expansion (${HOME}, ${DESKTOP}, etc.)
- Configuration validation and error reporting
- Easy portability across machines

### Polish & User Experience
- ✨ Loading spinners on all async operations
- 🌍 European date/time format (24-hour, DD-MM-YYYY)
- 🌙 Dark mode support
- 🔔 Desktop notifications for operations
- ⌨️ Keyboard shortcuts
- 📱 Responsive layout (40%-30%-30% dashboard cards)
- 🆘 Help button linking to documentation

## Technology Stack

### Backend
- **Python 3.10+** with type hints
- **Poetry** - Dependency management
- **Typer** - CLI framework
- **Pydantic v2** - Data validation
- **SQLite 3** - Database
- **PyInstaller** - Executable packaging
- **pytest** - Testing

### Frontend
- **Tauri 1.5+** - Desktop framework (Rust)
- **Svelte 4+** - UI framework
- **TypeScript 5.0+** - Type safety
- **Tailwind CSS + daisyUI** - Styling
- **Vite** - Build tool

### Development & CI/CD
- **Black, Ruff** - Python formatting/linting
- **ESLint, Prettier** - TypeScript/Svelte formatting
- **mypy** - Python type checking
- **GitHub Actions** - Automated builds and releases

## CLI Commands

### File Operations
```bash
fileflow scan                           # Dry-run scan
fileflow scan --execute                 # Execute operations
fileflow detect-screenshots             # Detect screenshot location
```

### Rule Management
```bash
fileflow rules list                     # List all rules
fileflow rules show <id>                # Show rule details
fileflow rules create                   # Create new rule
fileflow rules update <id>              # Update rule
fileflow rules delete <id>              # Delete rule
fileflow rules enable <id>              # Enable rule
fileflow rules disable <id>             # Disable rule
```

### File Discovery
```bash
fileflow files large [--threshold MB]   # Find large files
fileflow files old [--days N]           # Find old files
fileflow files delete <paths...>        # Delete files
```

### Configuration
```bash
fileflow config-show                    # Show configuration
fileflow config-export <path>           # Export config
fileflow config-import <path>           # Import (replace)
fileflow config-import-merge <path>     # Import (merge)
fileflow config-validate [path]         # Validate config
fileflow config-edit                    # Edit in $EDITOR
fileflow config-reset                   # Reset to defaults
```

## Project Structure

```
.
├── backend/                      # Python backend
│   ├── fileflow_core/           # Core file operations
│   ├── fileflow_config/         # Configuration management
│   ├── fileflow_storage/        # Database & cache
│   ├── fileflow_cli/            # CLI interface
│   ├── fileflow_api/            # API server
│   └── pyproject.toml           # Poetry config
│
├── frontend/                    # Tauri + Svelte frontend
│   ├── src/
│   │   ├── routes/              # Svelte pages
│   │   ├── lib/
│   │   │   ├── components/      # Reusable components
│   │   │   ├── stores/          # State management
│   │   │   ├── utils/           # Utilities (date formatting)
│   │   │   ├── api.ts           # Tauri API wrappers
│   │   │   └── types.ts         # TypeScript types
│   │   └── app.css              # Global styles
│   ├── src-tauri/
│   │   ├── src/main.rs          # Rust Tauri bridge
│   │   ├── backend.rs           # Backend integration
│   │   └── tauri.conf.json      # Tauri config
│   └── package.json             # Node.js dependencies
│
├── .github/workflows/           # CI/CD pipelines
│   ├── ci.yml                   # Tests & linting
│   └── release.yml              # Automated releases
│
├── specs/                       # Design documents
│   └── 001-fileflow-manager/
│
├── RELEASE.md                   # Release process guide
└── README.md                    # This file
```

## Documentation

- **Release Process**: [RELEASE.md](RELEASE.md)
- **Feature Specification**: `specs/001-fileflow-manager/spec.md`
- **Implementation Plan**: `specs/001-fileflow-manager/plan.md`
- **Task Breakdown**: `specs/001-fileflow-manager/tasks.md`
- **Developer Quickstart**: `specs/001-fileflow-manager/quickstart.md`

## Development

### Running Tests
```bash
# Backend tests
cd backend
poetry run pytest

# Frontend tests
cd frontend
pnpm test
```

### Linting & Formatting
```bash
# Backend
cd backend
poetry run ruff check .
poetry run black --check .
poetry run mypy fileflow_core fileflow_config fileflow_storage

# Frontend
cd frontend
pnpm lint
pnpm format --check
pnpm type-check
```

### Building for Production
```bash
# Backend executable
cd backend
chmod +x build_executable.sh
./build_executable.sh

# Frontend DMG
cd frontend
pnpm tauri build
```

The DMG will be located at:
```
frontend/src-tauri/target/release/bundle/dmg/FileFlow Manager_0.1.0_universal.dmg
```

## Project Origin

This project started as a test of [Spec Kit](https://github.com/github/spec-kit) and worked like a charm! It's now a fully-featured macOS application for automated file organization.

## License

TBD

## Contributing

This project is currently in active development. Contributions will be welcome once v1.0 is released.
