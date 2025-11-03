# Research: FileFlow Manager

**Created**: 2025-11-03
**Phase**: 0 - Technology Research & Decisions
**Status**: Complete

## Overview

This document captures technology research and decisions for FileFlow Manager, resolving all technical unknowns before design and implementation.

## 1. Backend Framework & Libraries

### 1.1 CLI Framework: Typer vs Click

**Decision**: Use **Typer**

**Rationale**:
- Modern, type-hint based API (better DX than Click's decorators)
- Built on top of Click (proven, stable foundation)
- Automatic help generation from type hints and docstrings
- Rich integration for beautiful terminal output
- Better async support for future daemon mode
- Active maintenance and growing adoption

**Alternatives Considered**:
- **Click**: Mature but more verbose, lacks type hints
- **argparse**: Standard library but too low-level for complex CLI
- **Fire**: Too magical, less control over help text

**References**:
- [Typer Documentation](https://typer.tiangolo.com/)
- [Rich Integration](https://rich.readthedocs.io/)

### 1.2 TOML Parsing: tomli vs toml

**Decision**: Use **tomli** (Python <3.11) / **tomllib** (Python 3.11+)

**Rationale**:
- `tomllib` is standard library in Python 3.11+ (zero dependencies)
- `tomli` is the backport for Python 3.10 (same API, minimal dependency)
- Read-only is sufficient for config loading (write via tomli_w if needed)
- Fully spec-compliant TOML 1.0.0 parser
- Fast, C-accelerated parsing

**Alternatives Considered**:
- **toml**: Older, unmaintained, not TOML 1.0.0 compliant
- **tomlkit**: Preserves formatting but slower, overkill for our needs

**Implementation**:
```python
try:
    import tomllib  # Python 3.11+
except ModuleNotFoundError:
    import tomli as tomllib  # Python 3.10 backport
```

**References**:
- [PEP 680 - tomllib](https://peps.python.org/pep-0680/)

### 1.3 Data Validation: Pydantic

**Decision**: Use **Pydantic v2**

**Rationale**:
- Type-safe data validation with Python type hints
- Automatic JSON/dict serialization
- Excellent error messages for invalid configs
- Fast (Rust-powered core in v2)
- Industry standard for data validation

**Use Cases**:
- Validate rule configurations from TOML
- Ensure required fields present and correct types
- Provide helpful error messages for user config mistakes
- Serialize/deserialize for IPC with Tauri

**Alternatives Considered**:
- **dataclasses + manual validation**: Too much boilerplate
- **attrs**: Less focused on validation
- **marshmallow**: Older, slower, less type-safe

**References**:
- [Pydantic V2 Documentation](https://docs.pydantic.dev/latest/)

### 1.4 Database: SQLite with sqlite3

**Decision**: Use **sqlite3** (standard library)

**Rationale**:
- Zero-dependency (built into Python)
- Perfect for single-user desktop app
- ACID transactions for operation logging
- Write-ahead logging (WAL) for crash safety
- Simple file-based storage
- No server required

**Schema Strategy**:
- `operations` table: Audit log of all file operations
- `checksum_cache` table: SHA-256 cache for performance
- Indexes on: timestamp, checksum, rule_id
- Migrations handled via version table + Python scripts

**Alternatives Considered**:
- **PostgreSQL/MySQL**: Overkill, requires server
- **TinyDB/Shelve**: Less robust, no SQL querying
- **JSON files**: No transactions, no querying

**References**:
- [Python sqlite3 docs](https://docs.python.org/3/library/sqlite3.html)
- [SQLite WAL mode](https://www.sqlite.org/wal.html)

## 2. Frontend Framework & Architecture

### 2.1 Desktop Framework: Tauri vs Electron

**Decision**: Use **Tauri 1.5+**

**Rationale**:
- Native performance (uses system WebView, not Chromium)
- Smaller bundle size (~3MB vs ~50MB for Electron)
- Better security model (no Node.js in frontend)
- Lower memory footprint
- Rust bridge for Python subprocess communication
- Active development and growing ecosystem
- Constitutional requirement (Immutable Constraints)

**Architecture**:
- Tauri Rust bridge spawns Python subprocess
- IPC via Tauri commands (JSON-based)
- Frontend calls Rust, Rust calls Python backend
- Python runs as separate process (clean separation)

**Alternatives Considered**:
- **Electron**: Heavier, higher memory, less secure
- **PyQt/PySide**: Python-based but less modern UI, harder to style
- **Tkinter**: Too basic, outdated look

**References**:
- [Tauri Documentation](https://tauri.app/)
- [Tauri vs Electron Comparison](https://tauri.app/v1/references/benchmarks/)

### 2.2 UI Framework: Svelte vs React/Vue

**Decision**: Use **Svelte 4+** (with SvelteKit for routing)

**Rationale**:
- Compiles to vanilla JavaScript (no runtime overhead)
- Simpler state management than React/Vue
- Smaller bundle size
- Better performance (less re-rendering)
- Cleaner syntax for reactive components
- Constitutional requirement (Immutable Constraints)
- Built-in stores for state management

**Component Strategy**:
- Reusable components (RuleEditor, FileList, ProgressBar)
- Svelte stores for global state (rules, files, scan status)
- Route-based tabs (Dashboard, Rules, LargeFiles, OldFiles)
- TypeScript for type safety

**Alternatives Considered**:
- **React**: Larger runtime, more complex state management
- **Vue**: Good but Svelte simpler for this use case
- **Vanilla JS**: Too much boilerplate for complex UI

**References**:
- [Svelte Documentation](https://svelte.dev/)
- [SvelteKit Documentation](https://kit.svelte.dev/)

### 2.3 Styling: Tailwind CSS vs Component Libraries

**Decision**: Use **Tailwind CSS** with **daisyUI** components

**Rationale**:
- Utility-first CSS for rapid development
- Small bundle size (purges unused classes)
- Consistent design system
- daisyUI provides macOS-like components
- Easy customization for native macOS look
- No heavy component library dependencies

**Design System**:
- macOS-inspired color palette
- Native-looking buttons, inputs, dialogs
- Dark mode support (future)
- Accessibility built-in (daisyUI)

**Alternatives Considered**:
- **Material UI / Ant Design**: Too heavy, non-native look
- **Pure CSS**: Too much work, inconsistent
- **Bootstrap**: Dated, not native-looking

**References**:
- [Tailwind CSS Documentation](https://tailwindcss.com/)
- [daisyUI Components](https://daisyui.com/)

## 3. IPC & Communication

### 3.1 Tauri-Python Bridge

**Decision**: **Sidecar pattern** (Python as subprocess)

**Implementation**:
1. Tauri Rust bridge spawns Python process on app start
2. Communication via stdin/stdout JSON RPC
3. Python backend exposes functions as JSON-RPC methods
4. Tauri commands wrap JSON-RPC calls

**Alternative Pattern** (if JSON-RPC too complex):
1. Python backend runs HTTP server (FastAPI)
2. Tauri calls localhost HTTP endpoints
3. More overhead but simpler debugging

**Rationale for Sidecar**:
- Clean process separation
- Python backend can run independently (CLI mode)
- Crash isolation (Python crash doesn't kill GUI)
- Easier testing (can test Python in isolation)

**Error Handling**:
- Rust catches Python subprocess errors
- Frontend shows user-friendly error messages
- Backend logs detailed errors for debugging

**References**:
- [Tauri Sidecar](https://tauri.app/v1/guides/building/sidecar/)
- [JSON-RPC 2.0 Spec](https://www.jsonrpc.org/specification)

### 3.2 Type Safety Across Layers

**Decision**: **Shared TypeScript/Python types** via code generation

**Strategy**:
1. Define Pydantic models in Python (source of truth)
2. Generate TypeScript interfaces from Pydantic models
3. Use [pydantic-to-typescript](https://github.com/phillipdupuis/pydantic-to-typescript) or manual sync
4. Ensure type safety in both layers

**Alternative** (if code gen too complex):
- Manual TypeScript interfaces mirroring Pydantic models
- Document mapping in both codebases
- Integration tests to catch mismatches

**References**:
- [pydantic-to-typescript](https://github.com/phillipdupuis/pydantic-to-typescript)

## 4. File Operations & Safety

### 4.1 Atomic File Operations

**Decision**: Use **os.replace()** for atomic moves

**Rationale**:
- `os.replace()` is atomic on POSIX systems (macOS)
- Overwrites destination atomically
- Safer than `shutil.move()` (which may not be atomic)
- Preserves permissions and ownership

**Implementation**:
```python
import os
from pathlib import Path

def move_file_atomic(src: Path, dst: Path) -> None:
    """Move file atomically, preserving metadata."""
    # Create destination directory if needed
    dst.parent.mkdir(parents=True, exist_ok=True)

    # Atomic move
    os.replace(src, dst)

    # Preserve timestamps (replace doesn't preserve mtime)
    shutil.copystat(src, dst)
```

**Alternatives Considered**:
- **shutil.move()**: Not guaranteed atomic
- **Copy + delete**: Risk of data loss if delete fails

**References**:
- [os.replace() docs](https://docs.python.org/3/library/os.html#os.replace)

### 4.2 SHA-256 Checksum Performance

**Decision**: **Chunked reading** with **hashlib**

**Implementation**:
```python
import hashlib

def calculate_sha256(file_path: Path, chunk_size: int = 65536) -> str:
    """Calculate SHA-256 in chunks for large files."""
    sha256 = hashlib.sha256()
    with open(file_path, 'rb') as f:
        while chunk := f.read(chunk_size):
            sha256.update(chunk)
    return sha256.hexdigest()
```

**Chunk Size Optimization**:
- 64KB chunks (65536 bytes) - balance between memory and I/O
- Larger chunks (1MB) for SSD-only systems (future optimization)
- Tested to meet <2s for 100MB file requirement

**Alternatives Considered**:
- **xxHash**: Faster but not cryptographically secure
- **MD5**: Faster but collision-prone (constitutional prohibition)
- **BLAKE3**: Faster but less standard than SHA-256

**References**:
- [hashlib documentation](https://docs.python.org/3/library/hashlib.html)

### 4.3 Parallel File Scanning

**Decision**: **ThreadPoolExecutor** for I/O-bound operations

**Rationale**:
- File I/O is I/O-bound (not CPU-bound)
- Threads better than processes for I/O (less overhead)
- Python GIL not a bottleneck for I/O operations
- Simpler than multiprocessing

**Implementation**:
```python
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

def scan_directories_parallel(directories: list[Path], max_workers: int = 4) -> list[FileMetadata]:
    """Scan multiple directories in parallel."""
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(scan_directory, d) for d in directories]
        results = [f.result() for f in futures]
    return [item for sublist in results for item in sublist]  # Flatten
```

**Worker Count**: 4 threads (balance between parallelism and overhead)

**Alternatives Considered**:
- **asyncio**: More complex, not needed for simple I/O
- **multiprocessing**: Overkill, higher overhead

**References**:
- [ThreadPoolExecutor docs](https://docs.python.org/3/library/concurrent.futures.html#threadpoolexecutor)

## 5. Testing Strategy

### 5.1 Backend Testing: pytest

**Decision**: **pytest** with **pytest-cov** for coverage

**Test Structure**:
```
tests/
├── unit/
│   ├── test_config_manager.py
│   ├── test_file_scanner.py
│   ├── test_duplicate_detector.py
│   └── ...
├── integration/
│   ├── test_rule_engine.py
│   ├── test_cli_commands.py
│   └── test_database.py
└── fixtures/
    ├── sample_files/
    └── test_configs/
```

**Coverage Target**: 90%+ (constitutional requirement)

**Key Testing Patterns**:
- Use `tmp_path` fixture for file operations
- Mock external calls (macOS defaults read)
- Parameterized tests for edge cases
- Integration tests with real SQLite database

**Alternatives Considered**:
- **unittest**: Standard library but more verbose
- **nose2**: Less popular than pytest

**References**:
- [pytest documentation](https://docs.pytest.org/)

### 5.2 Frontend Testing: Vitest

**Decision**: **Vitest** for unit/component tests

**Rationale**:
- Fast, Vite-native test runner
- Compatible with Svelte
- Similar API to Jest (familiar)
- Built-in coverage

**Test Structure**:
```
tests/
└── unit/
    ├── components/
    │   ├── RuleEditor.test.ts
    │   └── FileList.test.ts
    └── stores/
        ├── rules.test.ts
        └── scan.test.ts
```

**Testing Approach**:
- Component testing with @testing-library/svelte
- Store testing in isolation
- Mock Tauri commands

**Alternatives Considered**:
- **Jest**: Slower, requires more configuration
- **Cypress**: E2E only, too heavy for unit tests

**References**:
- [Vitest documentation](https://vitest.dev/)
- [Testing Library Svelte](https://testing-library.com/docs/svelte-testing-library/intro/)

## 6. Development Tools

### 6.1 Python Tooling

**Decisions**:
- **Package Manager**: Poetry (dependency management + packaging)
- **Linter**: Ruff (fast, modern, replaces Flake8/isort/pyupgrade)
- **Formatter**: Black (uncompromising, standard)
- **Type Checker**: mypy (strict type checking)

**Configuration**:
```toml
# pyproject.toml
[tool.black]
line-length = 100

[tool.ruff]
line-length = 100
select = ["E", "F", "I", "N", "W"]

[tool.mypy]
strict = true
```

**References**:
- [Poetry](https://python-poetry.org/)
- [Ruff](https://docs.astral.sh/ruff/)

### 6.2 Frontend Tooling

**Decisions**:
- **Package Manager**: pnpm (fast, disk-efficient)
- **Bundler**: Vite (fast, modern, Svelte-optimized)
- **Linter**: ESLint with typescript-eslint
- **Formatter**: Prettier

**Configuration**:
```json
// .prettierrc
{
  "semi": true,
  "singleQuote": true,
  "tabWidth": 2
}
```

**References**:
- [pnpm](https://pnpm.io/)
- [Vite](https://vitejs.dev/)

## 7. macOS Integration

### 7.1 Screenshot Location Detection

**Decision**: Use `defaults read` command

**Implementation**:
```python
import subprocess
from pathlib import Path

def detect_screenshot_location() -> Path:
    """Detect macOS screenshot save location."""
    try:
        result = subprocess.run(
            ["defaults", "read", "com.apple.screencapture", "location"],
            capture_output=True,
            text=True,
            check=True,
            timeout=5
        )
        return Path(result.stdout.strip()).expanduser()
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
        # Fallback to default Desktop location
        return Path.home() / "Desktop"
```

**Fallback Strategy**:
1. Try `defaults read` first
2. If fails, use `~/Desktop` (macOS default before custom location)
3. Allow user manual override in settings

**References**:
- [macOS defaults command](https://ss64.com/osx/defaults.html)

### 7.2 macOS Notifications

**Decision**: Use **pync** (Python) or **Tauri notifications API**

**Rationale**:
- pync wraps macOS native notification system
- Tauri provides cross-platform notification API
- User can disable in preferences

**Implementation** (Tauri approach - preferred):
```typescript
import { sendNotification } from '@tauri-apps/api/notification';

await sendNotification({
  title: 'FileFlow Manager',
  body: 'Organization complete: 15 files moved'
});
```

**Alternatives Considered**:
- **pync**: Python-only, requires manual integration
- **plyer**: Cross-platform but heavier

**References**:
- [Tauri Notifications](https://tauri.app/v1/api/js/notification/)

## 8. Performance Optimizations

### 8.1 Checksum Caching Strategy

**Decision**: **SQLite cache with mtime/size validation**

**Cache Invalidation Logic**:
```python
def get_cached_checksum(file_path: Path) -> str | None:
    """Get cached checksum if still valid."""
    stat = file_path.stat()

    cached = db.query_checksum_cache(str(file_path))
    if not cached:
        return None

    # Invalidate if file changed (size or mtime different)
    if cached.file_size != stat.st_size or cached.modified_time != stat.st_mtime:
        return None

    return cached.checksum
```

**Cache Cleanup**: Remove entries older than 30 days (configurable)

**Expected Hit Rate**: 80%+ for repeated scans

### 8.2 Progress Reporting

**Decision**: **Streaming updates** via Tauri events

**Implementation**:
```python
# Backend emits progress events
def scan_with_progress(rules: list[Rule]) -> ScanResult:
    total_files = count_files(rules)
    processed = 0

    for file in scan_files(rules):
        processed += 1
        emit_progress(processed, total_files)  # Tauri event
        # ... process file
```

```typescript
// Frontend listens for progress events
listen('scan:progress', (event) => {
  const { processed, total } = event.payload;
  progressStore.set({ processed, total });
});
```

**Alternatives Considered**:
- **Polling**: Less efficient, delayed updates
- **No progress**: Violates constitutional requirement (<5s operations)

## 9. Deployment & Distribution

### 9.1 Build System

**Decision**: **Tauri CLI** for bundling

**Artifacts**:
- macOS: `.app` bundle (signed)
- macOS: `.dmg` installer (for distribution)

**Build Process**:
1. Build Python backend with PyInstaller (single executable)
2. Include Python executable in Tauri bundle as sidecar
3. Build Svelte frontend with Vite
4. Package everything with Tauri CLI

**References**:
- [Tauri Building](https://tauri.app/v1/guides/building/)

### 9.2 Code Signing (macOS)

**Decision**: **Apple Developer Certificate** (for distribution)

**Requirements**:
- Developer ID Application certificate
- Notarization for macOS 10.15+
- Gatekeeper bypass (prevents "unidentified developer" warning)

**Process**:
1. Sign `.app` bundle with `codesign`
2. Notarize with `xcrun notarytool`
3. Staple notarization ticket

**References**:
- [Apple Code Signing](https://developer.apple.com/support/code-signing/)
- [Tauri macOS Signing](https://tauri.app/v1/guides/distribution/sign-macos/)

## 10. Summary of Key Decisions

| Category | Decision | Rationale |
|----------|----------|-----------|
| CLI Framework | Typer | Type-safe, modern, Rich integration |
| TOML Parser | tomli/tomllib | Standard library (3.11+), spec-compliant |
| Validation | Pydantic v2 | Type-safe, fast, excellent errors |
| Database | SQLite3 | Built-in, perfect for single-user |
| Desktop Framework | Tauri 1.5+ | Native performance, small bundle |
| UI Framework | Svelte 4+ | Compiled, simple, fast |
| Styling | Tailwind + daisyUI | Utility-first, native-looking |
| IPC | Sidecar (subprocess) | Clean separation, crash isolation |
| File Operations | os.replace() | Atomic moves on macOS |
| Checksums | SHA-256 (hashlib) | Secure, constitutional requirement |
| Parallelism | ThreadPoolExecutor | I/O-bound, simpler than multiprocessing |
| Python Testing | pytest + pytest-cov | Industry standard, 90%+ coverage |
| Frontend Testing | Vitest | Fast, Vite-native |
| Python Tooling | Poetry + Ruff + Black | Modern, fast, standard |
| Frontend Tooling | pnpm + Vite + Prettier | Fast, efficient |
| Notifications | Tauri API | Native, cross-platform |
| Distribution | Tauri bundle + sign | macOS .app/.dmg with notarization |

## Next Steps

All technical unknowns resolved. Ready to proceed to **Phase 1: Design & Contracts**.

**Phase 1 Outputs**:
1. `data-model.md`: Entity definitions and relationships
2. `contracts/`: API contracts (Tauri commands, CLI interface)
3. `quickstart.md`: Setup and build instructions

**Ready to proceed**: ✅
