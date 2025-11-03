# FileFlow Manager - Developer Quickstart

**Feature**: FileFlow Manager
**Created**: 2025-11-03
**Purpose**: Get developers up and running with the FileFlow Manager development environment

## Prerequisites

Before starting, ensure you have:

- **macOS 10.15 (Catalina) or newer** (required for target platform)
- **Python 3.10 or newer** (`python3 --version`)
- **Node.js 18.0 or newer** (`node --version`)
- **Rust 1.70 or newer** (`rustc --version`) - for Tauri
- **pnpm** (`npm install -g pnpm`)
- **Git** (`git --version`)

Optional but recommended:
- **VS Code** or **PyCharm** for development
- **iTerm2** or another modern terminal

## Quick Start (5 minutes)

### 1. Clone and Setup

```bash
# Clone the repository
git clone <repository-url>
cd fileflow-manager

# Run setup script (installs all dependencies)
./setup.sh
```

The setup script will:
- Install Python dependencies via Poetry
- Install Node.js dependencies via pnpm
- Set up pre-commit hooks
- Create default configuration
- Initialize SQLite database
- Verify all tools are installed

### 2. Run Development Server

**Terminal 1** - Start backend:
```bash
cd backend
poetry run python -m fileflow_api
```

**Terminal 2** - Start frontend:
```bash
cd frontend
pnpm tauri dev
```

The GUI application will launch automatically. Changes to Svelte files auto-reload.

### 3. Run CLI

```bash
cd backend
poetry run fileflow --help
```

## Detailed Setup

### Backend Setup (Python)

#### 1. Install Poetry

```bash
curl -sSL https://install.python-poetry.org | python3 -
```

Add to PATH:
```bash
export PATH="$HOME/.local/bin:$PATH"
```

#### 2. Install Dependencies

```bash
cd backend
poetry install
```

This installs:
- Core dependencies (Typer, Pydantic, tomli/tomllib)
- Development dependencies (pytest, black, ruff, mypy)
- All pinned versions from `poetry.lock`

#### 3. Verify Installation

```bash
poetry run python -c "import typer; print('Backend setup successful!')"
```

#### 4. Run Tests

```bash
# Run all tests
poetry run pytest

# Run with coverage
poetry run pytest --cov=fileflow_core --cov-report=html

# Run specific test file
poetry run pytest tests/unit/test_rule_engine.py

# Run tests matching pattern
poetry run pytest -k "test_screenshot"
```

#### 5. Code Quality

```bash
# Format code with Black
poetry run black .

# Lint with Ruff
poetry run ruff check .

# Type check with mypy
poetry run mypy fileflow_core fileflow_config fileflow_storage
```

### Frontend Setup (Tauri + Svelte)

#### 1. Install Dependencies

```bash
cd frontend
pnpm install
```

This installs:
- Tauri dependencies
- Svelte and SvelteKit
- TypeScript
- Tailwind CSS and daisyUI
- Development tools (Vite, Vitest, Prettier)

#### 2. Install Tauri CLI

```bash
pnpm add -D @tauri-apps/cli
```

#### 3. Verify Installation

```bash
pnpm tauri info
```

Should show:
- Tauri version
- Node.js version
- pnpm version
- Rust version
- OS information

#### 4. Run Development Server

```bash
# Development mode (hot reload)
pnpm tauri dev

# Run frontend only (no Tauri, for UI development)
pnpm dev
```

#### 5. Run Tests

```bash
# Run unit tests
pnpm test

# Run tests in watch mode
pnpm test:watch

# Run with coverage
pnpm test:coverage
```

#### 6. Code Quality

```bash
# Format with Prettier
pnpm format

# Lint with ESLint
pnpm lint

# Type check with TypeScript
pnpm type-check
```

### Rust Bridge Setup (Tauri)

The Rust code is in `frontend/src-tauri/`. It bridges Svelte frontend with Python backend.

#### Build Rust Bridge

```bash
cd frontend/src-tauri
cargo build
```

#### Run Rust Tests

```bash
cargo test
```

#### Format Rust Code

```bash
cargo fmt
```

## Project Structure

```
fileflow-manager/
├── backend/                      # Python backend
│   ├── fileflow_core/           # Core file operations
│   ├── fileflow_config/         # Configuration management
│   ├── fileflow_storage/        # Database and cache
│   ├── fileflow_cli/            # CLI interface
│   ├── fileflow_api/            # Tauri IPC handlers
│   ├── tests/                   # Python tests
│   ├── pyproject.toml           # Poetry configuration
│   └── poetry.lock              # Locked dependencies
│
├── frontend/                    # Tauri + Svelte frontend
│   ├── src/                     # Svelte application
│   │   ├── routes/              # Tab components
│   │   └── lib/                 # Shared components, stores, utils
│   ├── src-tauri/               # Rust bridge code
│   │   └── src/main.rs          # Tauri main + Python sidecar
│   ├── package.json             # Node.js dependencies
│   ├── pnpm-lock.yaml           # Locked dependencies
│   └── vite.config.ts           # Vite configuration
│
├── specs/                       # Feature specifications
│   └── 001-fileflow-manager/
│       ├── spec.md              # Feature specification
│       ├── plan.md              # Implementation plan
│       ├── research.md          # Technical research
│       ├── data-model.md        # Data models
│       ├── contracts/           # API contracts
│       └── quickstart.md        # This file
│
├── .specify/                    # Specify framework
│   ├── memory/
│   │   └── constitution.md      # Project constitution
│   └── templates/               # Specify templates
│
├── setup.sh                     # Setup script
└── README.md                    # Project overview
```

## Development Workflows

### Running Full Stack

**Option 1: Separate terminals** (recommended for development)

Terminal 1 - Backend:
```bash
cd backend
poetry run python -m fileflow_api
```

Terminal 2 - Frontend:
```bash
cd frontend
pnpm tauri dev
```

**Option 2: Integrated** (backend runs as Tauri sidecar)

```bash
cd frontend
pnpm tauri dev
```

Backend starts automatically as subprocess. See logs in Tauri console.

### Testing Changes

**Backend changes**:
1. Edit Python files in `backend/fileflow_*/`
2. Backend auto-reloads (if using sidecar mode)
3. Or restart backend terminal

**Frontend changes**:
1. Edit Svelte files in `frontend/src/`
2. Frontend auto-reloads (Vite HMR)
3. See changes immediately in GUI

**Rust bridge changes**:
1. Edit `frontend/src-tauri/src/main.rs`
2. Tauri rebuilds automatically
3. GUI restarts

### CLI Development

**Interactive testing**:
```bash
cd backend
poetry run fileflow scan --dry-run
poetry run fileflow rules list
```

**Test with custom config**:
```bash
poetry run fileflow --config ./test-config.toml scan
```

### Database Development

**Inspect database**:
```bash
sqlite3 ~/.config/fileflow/fileflow.db
```

**View operations table**:
```sql
SELECT * FROM operations ORDER BY timestamp DESC LIMIT 10;
```

**View checksum cache**:
```sql
SELECT * FROM checksum_cache LIMIT 10;
```

**Reset database**:
```bash
rm ~/.config/fileflow/fileflow.db
poetry run python -m fileflow_storage.database --init
```

## Configuration

### Development Config

Create `backend/dev-config.toml`:

```toml
[general]
log_level = "DEBUG"
cache_enabled = true

[paths]
screenshot_source = "/tmp/test-screenshots"
screenshot_destination = "/tmp/organized-screenshots"
monitored_directories = ["/tmp/test-screenshots"]

[thresholds]
large_file_mb = 10  # Lower threshold for testing
old_file_days = 7   # Lower threshold for testing

[[rules]]
id = "test-screenshot-org"
enabled = true
name = "Test Screenshot Organization"
description = "Test rule for development"
source_patterns = ["Screenshot*.png"]
source_directories = ["/tmp/test-screenshots"]
destination = "/tmp/organized-screenshots"
organize_by_date = true
file_types = ["png"]
priority = 1
```

### Test Data

Create test files:
```bash
# Create test directories
mkdir -p /tmp/test-screenshots
mkdir -p /tmp/organized-screenshots

# Create test screenshot files
touch "/tmp/test-screenshots/Screenshot 2025-11-03 at 10.30.45.png"
touch "/tmp/test-screenshots/Screenshot 2025-11-03 at 14.22.10.png"
touch "/tmp/test-screenshots/Screenshot 2025-11-02 at 09.15.33.png"

# Create large test file (100MB)
dd if=/dev/zero of=/tmp/test-screenshots/large-file.dat bs=1m count=100

# Create old test file (modified 100 days ago)
touch -t $(date -v-100d +%Y%m%d%H%M.%S) /tmp/test-screenshots/old-file.txt
```

## Common Tasks

### Add New Python Module

```bash
cd backend
poetry add <package-name>

# Development dependency
poetry add --group dev <package-name>
```

### Add New npm Package

```bash
cd frontend
pnpm add <package-name>

# Development dependency
pnpm add -D <package-name>
```

### Create New Migration

```bash
cd backend
poetry run python -m fileflow_storage.migrations create <migration_name>
```

### Format All Code

```bash
# Python
cd backend
poetry run black .
poetry run ruff check . --fix

# TypeScript/Svelte
cd frontend
pnpm format
pnpm lint --fix

# Rust
cd frontend/src-tauri
cargo fmt
```

### Run All Tests

```bash
# Python tests
cd backend
poetry run pytest

# TypeScript tests
cd frontend
pnpm test

# Rust tests
cd frontend/src-tauri
cargo test

# Integration tests (requires both backend and frontend running)
cd backend
poetry run pytest tests/integration/
```

### Build Production

**Backend CLI**:
```bash
cd backend
poetry build
# Creates dist/fileflow-*.whl and dist/fileflow-*.tar.gz
```

**GUI Application**:
```bash
cd frontend
pnpm tauri build
# Creates installer in src-tauri/target/release/bundle/
```

### Clean Build Artifacts

```bash
# Python
cd backend
rm -rf dist/ build/ *.egg-info .pytest_cache .mypy_cache .ruff_cache

# Node.js
cd frontend
rm -rf node_modules dist .svelte-kit

# Rust
cd frontend/src-tauri
cargo clean
```

## Debugging

### Backend Debugging

**VS Code** (`backend/.vscode/launch.json`):
```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Python: FileFlow CLI",
      "type": "python",
      "request": "launch",
      "module": "fileflow_cli",
      "args": ["scan", "--dry-run"],
      "console": "integratedTerminal",
      "justMyCode": false
    },
    {
      "name": "Python: Pytest",
      "type": "python",
      "request": "launch",
      "module": "pytest",
      "args": ["-v"],
      "console": "integratedTerminal"
    }
  ]
}
```

**PyCharm**: Right-click on `fileflow_cli/__main__.py` → Debug

**Print debugging**:
```python
import logging
logger = logging.getLogger(__name__)
logger.debug(f"Variable value: {value}")
```

### Frontend Debugging

**Chrome DevTools**:
- Tauri app opens with DevTools
- Press `Cmd+Option+I` to toggle
- Use Console, Network, Elements tabs

**VS Code** (`frontend/.vscode/launch.json`):
```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Tauri Development",
      "type": "chrome",
      "request": "launch",
      "url": "http://localhost:1420",
      "webRoot": "${workspaceFolder}/src"
    }
  ]
}
```

**Console logging**:
```typescript
console.log('Debug:', variable);
console.error('Error:', error);
```

### Rust Debugging

**VS Code** with rust-analyzer extension:
- Set breakpoints in `.rs` files
- Press F5 to debug

**Print debugging**:
```rust
println!("Debug: {:?}", variable);
eprintln!("Error: {:?}", error);
```

### Database Debugging

**Enable query logging**:
```python
import logging
logging.getLogger('sqlalchemy.engine').setLevel(logging.DEBUG)
```

**Inspect queries**:
```bash
sqlite3 ~/.config/fileflow/fileflow.db ".log stdout"
```

## Troubleshooting

### "Module not found" (Python)

```bash
cd backend
poetry install
poetry run python -c "import fileflow_core"
```

### "Command not found: pnpm"

```bash
npm install -g pnpm
```

### "Rust compiler not found"

```bash
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
source $HOME/.cargo/env
```

### "Tauri dev fails to start"

```bash
cd frontend
rm -rf node_modules pnpm-lock.yaml
pnpm install
pnpm tauri dev
```

### "Database locked"

```bash
# Stop all FileFlow processes
pkill -f fileflow

# Remove lock file
rm ~/.config/fileflow/fileflow.db-lock
```

### "Permission denied" on macOS

Grant Full Disk Access to Terminal:
1. System Preferences → Security & Privacy → Privacy
2. Full Disk Access → Add Terminal.app

### Tests failing

```bash
# Clear test cache
cd backend
rm -rf .pytest_cache
poetry run pytest --cache-clear

cd ../frontend
rm -rf node_modules/.vite
pnpm test
```

## Performance Tips

### Development

1. **Use sidecar mode**: Faster startup than separate backend terminal
2. **Enable caching**: Set `cache_enabled = true` in config
3. **Limit scan scope**: Use smaller test directories
4. **Use dry-run by default**: Faster than actual file operations

### Testing

1. **Run specific tests**: `pytest tests/unit/test_specific.py` instead of full suite
2. **Parallel testing**: `pytest -n auto` (requires pytest-xdist)
3. **Skip slow tests**: `pytest -m "not slow"`

### Building

1. **Use release mode**: `pnpm tauri build --release`
2. **Enable optimizations**: Set `opt-level = 3` in Cargo.toml
3. **Bundle size**: Run `pnpm tauri build --bundles app` for smaller builds

## Code Style Guidelines

### Python (Black + Ruff)

- Line length: 88 characters (Black default)
- Imports: Sorted with isort
- Type hints: Required for public functions
- Docstrings: Google style

```python
from pathlib import Path

def process_file(file_path: Path, dry_run: bool = False) -> bool:
    """Process a single file according to rules.

    Args:
        file_path: Path to file to process
        dry_run: If True, only preview changes

    Returns:
        True if processing succeeded, False otherwise

    Raises:
        FileNotFoundError: If file doesn't exist
    """
    ...
```

### TypeScript (Prettier + ESLint)

- Line length: 100 characters
- Semicolons: Required
- Quotes: Single quotes
- Trailing commas: Always

```typescript
import type { ScanFilesResponse } from '$lib/types';

export async function scanFiles(dryRun: boolean): Promise<ScanFilesResponse> {
  const result = await invoke<ScanFilesResponse>('scan_files', {
    dry_run: dryRun,
  });
  return result;
}
```

### Svelte (Prettier)

```svelte
<script lang="ts">
  import { onMount } from 'svelte';
  import type { Rule } from '$lib/types';

  export let rules: Rule[] = [];

  onMount(() => {
    loadRules();
  });
</script>

<div class="rules-list">
  {#each rules as rule (rule.id)}
    <RuleCard {rule} />
  {/each}
</div>

<style>
  .rules-list {
    display: grid;
    gap: 1rem;
  }
</style>
```

## Next Steps

After completing this quickstart:

1. **Read the specification**: [spec.md](./spec.md)
2. **Review the data model**: [data-model.md](./data-model.md)
3. **Study the API contracts**: [contracts/](./contracts/)
4. **Check the implementation plan**: [plan.md](./plan.md)
5. **Start with tasks.md**: Run `/speckit.tasks` to generate implementation tasks

## Resources

### Documentation

- [Typer Documentation](https://typer.tiangolo.com/)
- [Pydantic Documentation](https://docs.pydantic.dev/)
- [Tauri Documentation](https://tauri.app/v1/guides/)
- [Svelte Documentation](https://svelte.dev/docs)
- [SvelteKit Documentation](https://kit.svelte.dev/docs)
- [Tailwind CSS Documentation](https://tailwindcss.com/docs)
- [daisyUI Documentation](https://daisyui.com/)

### Tools

- [Poetry](https://python-poetry.org/)
- [pnpm](https://pnpm.io/)
- [Vite](https://vitejs.dev/)
- [Vitest](https://vitest.dev/)
- [pytest](https://docs.pytest.org/)
- [Ruff](https://docs.astral.sh/ruff/)
- [Black](https://black.readthedocs.io/)

### Related Files

- [constitution.md](../../.specify/memory/constitution.md) - Project constitution
- [spec.md](./spec.md) - Feature specification
- [plan.md](./plan.md) - Implementation plan
- [research.md](./research.md) - Technical research
- [data-model.md](./data-model.md) - Data models
- [contracts/](./contracts/) - API contracts

## Questions?

For questions about:
- **Setup issues**: Check [Troubleshooting](#troubleshooting) section
- **Architecture decisions**: See [research.md](./research.md)
- **Data structures**: See [data-model.md](./data-model.md)
- **API contracts**: See [contracts/](./contracts/)
- **Requirements**: See [spec.md](./spec.md)
