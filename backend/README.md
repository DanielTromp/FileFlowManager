# FileFlow Backend

Python backend for FileFlow Manager - intelligent automated file organization system for macOS.

## Installation

```bash
poetry install
```

## Usage

```bash
# Run dry-run scan
poetry run fileflow scan --dry-run

# Execute file operations
poetry run fileflow scan --execute

# Detect screenshot location
poetry run fileflow detect-screenshots
```

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
