# FileFlow Backend

Python backend for FileFlow Manager - intelligent automated file organization system for macOS.

## Installation

```bash
poetry install
```

## Usage

```bash
# Scan and organize files (executes immediately)
poetry run fileflow scan

# Detect screenshot location
poetry run fileflow detect-screenshots
```

**Note**: The CLI currently executes operations immediately. Configuration is loaded from `~/.config/fileflow/fileflow.toml` (auto-created on first run).

## Modules

- `fileflow_core`: Core file operations, scanning, and rule engine
- `fileflow_config`: Configuration management and validation
- `fileflow_storage`: Database and cache operations
- `fileflow_cli`: Command-line interface
- `fileflow_api`: Tauri IPC command handlers

## Development

```bash
# Run tests
poetry run pytest

# Format code
poetry run black .

# Lint code
poetry run ruff check .

# Type check
poetry run mypy .
```
