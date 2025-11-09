# Contributing to FileFlow Manager

Thank you for your interest in contributing to FileFlow Manager! This document provides guidelines and instructions for contributing to the project.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Workflow](#development-workflow)
- [Code Style Guidelines](#code-style-guidelines)
- [Testing Requirements](#testing-requirements)
- [Documentation Requirements](#documentation-requirements)
- [Pull Request Process](#pull-request-process)
- [Reporting Bugs](#reporting-bugs)
- [Suggesting Features](#suggesting-features)
- [Questions](#questions)

## Code of Conduct

### Our Pledge

We are committed to providing a welcoming and inclusive experience for everyone. We expect all contributors to:

- Use welcoming and inclusive language
- Be respectful of differing viewpoints and experiences
- Accept constructive criticism gracefully
- Focus on what is best for the community
- Show empathy towards other community members

### Unacceptable Behavior

- Harassment, trolling, or derogatory comments
- Publishing others' private information without permission
- Other conduct which could reasonably be considered inappropriate

## Getting Started

### Prerequisites

Before you begin, ensure you have:

- macOS 10.15 (Catalina) or newer
- Python 3.10+
- Node.js 18.0+
- Rust 1.70+
- pnpm
- Poetry
- Git

See [quickstart.md](specs/001-fileflow-manager/quickstart.md) for detailed setup instructions.

### Initial Setup

#### Quick Setup (Recommended)

1. **Fork the repository** on GitHub
2. **Clone your fork** and run automated setup:
   ```bash
   git clone https://github.com/YOUR-USERNAME/Filefly-specify.git
   cd Filefly-specify

   # Run automated setup
   ./setup.sh
   ```
3. **Add upstream remote**:
   ```bash
   git remote add upstream https://github.com/DanielTromp/Filefly-specify.git
   ```

The `setup.sh` script will:
- Check prerequisites (Python 3.10+, Poetry, Node.js, pnpm, Rust)
- Install missing tools (pnpm, Rust if needed)
- Install all dependencies (backend + frontend)
- Run quality checks to verify installation

#### Manual Setup (Advanced)

1. **Fork the repository** on GitHub
2. **Clone your fork**:
   ```bash
   git clone https://github.com/YOUR-USERNAME/Filefly-specify.git
   cd Filefly-specify
   ```
3. **Add upstream remote**:
   ```bash
   git remote add upstream https://github.com/DanielTromp/Filefly-specify.git
   ```
4. **Install dependencies**:
   ```bash
   # Backend
   cd backend
   poetry install

   # Frontend
   cd ../frontend
   pnpm install
   ```
5. **Validate setup**:
   ```bash
   ./validate-quickstart.sh
   ```

## Development Workflow

### Creating a Branch

Always create a new branch for your work:

```bash
# Update your local main branch
git checkout main
git pull upstream main

# Create a feature branch
git checkout -b feature/your-feature-name

# Or a bugfix branch
git checkout -b fix/bug-description
```

**Branch naming conventions**:
- Feature branches: `feature/short-description`
- Bug fixes: `fix/bug-description`
- Documentation: `docs/what-changed`
- Refactoring: `refactor/what-changed`

### Making Changes

1. **Make your changes** following the code style guidelines below
2. **Test your changes** thoroughly
3. **Run code quality tools** before committing
4. **Commit with clear messages** (see commit guidelines below)

### Commit Message Guidelines

We follow the [Conventional Commits](https://www.conventionalcommits.org/) specification:

```
<type>(<scope>): <description>

[optional body]

[optional footer]
```

**Types**:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, no logic changes)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks

**Examples**:
```bash
feat(rules): add support for regex patterns in rule matching
fix(scanner): resolve race condition in parallel file scanning
docs(readme): update installation instructions for macOS
refactor(core): extract duplicate detection into separate module
test(rules): add tests for rule priority ordering
```

### Keeping Your Branch Updated

Regularly sync your branch with upstream:

```bash
git checkout main
git pull upstream main
git checkout your-branch
git rebase main
```

## Code Style Guidelines

### Python (Backend)

We use **Black**, **Ruff**, and **mypy** for code quality.

**Formatting and Linting**:
```bash
cd backend

# Format code with Black
poetry run black .

# Lint with Ruff
poetry run ruff check .

# Fix auto-fixable issues
poetry run ruff check . --fix

# Type check with mypy
poetry run mypy fileflow_core fileflow_config fileflow_storage
```

**Style Requirements**:
- Line length: 88 characters (Black default)
- Use type hints for all function parameters and return values
- Use Google-style docstrings for all public functions
- Sort imports with isort (integrated with Black)

**Example**:
```python
from pathlib import Path
from typing import List, Optional

def process_files(
    file_paths: List[Path],
    dry_run: bool = False,
    max_workers: Optional[int] = None
) -> int:
    """Process multiple files according to organization rules.

    Args:
        file_paths: List of file paths to process
        dry_run: If True, only preview changes without executing
        max_workers: Maximum number of worker threads (default: CPU count)

    Returns:
        Number of files successfully processed

    Raises:
        ValueError: If file_paths is empty
        FileNotFoundError: If any file path doesn't exist
    """
    ...
```

### TypeScript/Svelte (Frontend)

We use **Prettier** and **ESLint** for code quality.

**Formatting and Linting**:
```bash
cd frontend

# Format with Prettier
pnpm format

# Lint with ESLint
pnpm lint

# Fix auto-fixable issues
pnpm lint --fix

# Type check
pnpm type-check
```

**Style Requirements**:
- Line length: 100 characters
- Use semicolons
- Single quotes for strings
- Trailing commas in objects/arrays
- Use TypeScript strict mode

**Example**:
```typescript
import type { Rule, ScanResult } from '$lib/types';

export async function scanFiles(dryRun: boolean): Promise<ScanResult> {
  const result = await invoke<ScanResult>('scan_files', {
    dryRun,
  });
  return result;
}
```

### Rust (Tauri Bridge)

**Formatting**:
```bash
cd frontend/src-tauri
cargo fmt
```

**Style Requirements**:
- Follow Rust standard formatting (rustfmt)
- Use meaningful variable names
- Add comments for complex logic

## Testing Requirements

### Backend Tests

All backend changes must include tests.

**Running Tests**:
```bash
cd backend

# Run all tests
poetry run pytest

# Run with coverage
poetry run pytest --cov=fileflow_core --cov=fileflow_config --cov=fileflow_storage

# Run specific test file
poetry run pytest tests/unit/test_rule_engine.py

# Run tests matching pattern
poetry run pytest -k "test_screenshot"
```

**Test Requirements**:
- Unit tests for all new functions
- Integration tests for new features
- Test coverage should not decrease
- All tests must pass before submitting PR

**Example Test**:
```python
import pytest
from pathlib import Path
from fileflow_core.rule_engine import RuleEngine

def test_rule_matching_with_patterns():
    """Test that rules correctly match files by pattern."""
    engine = RuleEngine(config)
    matches = engine.match_files([Path("Screenshot 2024-01-01.png")])
    assert len(matches) == 1
    assert matches[0].rule_id == "screenshot-org"
```

### Frontend Tests

Frontend tests are currently being developed (Phase 8).

**Running Tests**:
```bash
cd frontend

# Run tests (when available)
pnpm test

# Run with coverage
pnpm test --coverage
```

## Documentation Requirements

### Code Documentation

**Python**:
- Add Google-style docstrings to all public functions
- Include type hints for all parameters and return values
- Document exceptions that can be raised

**TypeScript**:
- Add JSDoc comments to complex functions
- Use TypeScript types instead of comments where possible

### README Updates

If your change affects:
- Installation process → Update root `README.md`
- CLI commands → Update `backend/README.md`
- GUI features → Update `frontend/README.md`
- Development setup → Update `specs/001-fileflow-manager/quickstart.md`

### Changelog

For significant changes, add an entry to `CHANGELOG.md` (create if doesn't exist):

```markdown
## [Unreleased]

### Added
- Support for regex patterns in rule matching (#123)

### Fixed
- Race condition in parallel file scanning (#124)

### Changed
- Improved error messages for permission errors (#125)
```

## Pull Request Process

### Before Submitting

1. **Update your branch** with latest upstream changes
2. **Run all tests** and ensure they pass
3. **Run code quality tools** and fix any issues
4. **Update documentation** as needed
5. **Test manually** in both CLI and GUI
6. **Validate quickstart** (run `./validate-quickstart.sh`)

### Submitting a Pull Request

1. **Push your branch** to your fork:
   ```bash
   git push origin your-branch-name
   ```

2. **Create Pull Request** on GitHub:
   - Go to the original repository
   - Click "New Pull Request"
   - Select your fork and branch
   - Fill out the PR template

3. **PR Title Format**:
   ```
   <type>: <clear description>
   ```
   Example: `feat: Add regex pattern support for rule matching`

4. **PR Description Should Include**:
   - Summary of changes
   - Motivation and context
   - Type of change (bug fix, feature, docs, etc.)
   - How has this been tested?
   - Checklist (tests added, docs updated, etc.)

### PR Review Process

- **Automated checks** will run (linting, tests, type checking)
- **Maintainers will review** your code
- **Address feedback** by pushing new commits to your branch
- Once approved, maintainers will **merge your PR**

### What Happens After Merge

- Your changes will be included in the next release
- You'll be credited in the release notes
- The branch will be deleted

## Reporting Bugs

### Before Reporting

1. **Check existing issues** to avoid duplicates
2. **Verify the bug** is reproducible
3. **Test with latest version** of the code

### Creating a Bug Report

Open an issue with:

**Title**: Clear, descriptive summary
```
Bug: File operations fail with permission errors on external drives
```

**Template**:
```markdown
## Bug Description
A clear description of what the bug is.

## Steps to Reproduce
1. Go to '...'
2. Click on '...'
3. See error

## Expected Behavior
What you expected to happen.

## Actual Behavior
What actually happened.

## Environment
- macOS version: [e.g., 13.2.1]
- FileFlow version: [e.g., 0.1.2]
- Installation method: [DMG / Development]

## Logs
Include relevant logs from `~/.local/share/fileflow/fileflow.log`

## Screenshots
If applicable, add screenshots.
```

## Suggesting Features

### Before Suggesting

1. **Check existing issues** and roadmap
2. **Consider if it fits** the project scope
3. **Think about implementation** complexity

### Creating a Feature Request

Open an issue with:

**Title**: Clear feature description
```
Feature Request: Add support for cloud storage destinations
```

**Template**:
```markdown
## Feature Description
Clear description of the feature.

## Motivation
Why is this feature needed? What problem does it solve?

## Proposed Solution
How would you implement this feature?

## Alternatives Considered
What other approaches did you consider?

## Additional Context
Any other context, mockups, or examples.
```

## Questions

### Where to Ask

- **General questions**: Open a GitHub Discussion
- **Bug reports**: Open a GitHub Issue
- **Feature requests**: Open a GitHub Issue
- **Development questions**: Check `specs/001-fileflow-manager/quickstart.md`

### Getting Help

If you need help contributing:

1. Read the [quickstart guide](specs/001-fileflow-manager/quickstart.md)
2. Check the [troubleshooting section](specs/001-fileflow-manager/quickstart.md#troubleshooting)
3. Open a GitHub Discussion with your question
4. Include context: what you're trying to do, what you've tried, error messages

## Project Structure

Understanding the codebase:

```
.
├── backend/                  # Python backend
│   ├── fileflow_core/       # Core business logic
│   ├── fileflow_config/     # Configuration management
│   ├── fileflow_storage/    # Database and cache
│   ├── fileflow_cli/        # CLI interface
│   └── fileflow_api/        # Tauri IPC handlers
├── frontend/                 # Tauri + Svelte GUI
│   ├── src/                 # Svelte application
│   └── src-tauri/           # Rust bridge
├── specs/                   # Design documents
└── .github/workflows/       # CI/CD
```

**Key Files**:
- `specs/001-fileflow-manager/spec.md` - Feature specification
- `specs/001-fileflow-manager/plan.md` - Implementation plan
- `specs/001-fileflow-manager/data-model.md` - Data models
- `specs/001-fileflow-manager/contracts/` - API contracts

## Development Tips

### Fast Iteration

**Backend only**:
```bash
cd backend
poetry run fileflow scan --dry-run
```

**Frontend only** (without Tauri):
```bash
cd frontend
pnpm dev  # Opens in browser
```

**Full stack**:
```bash
cd frontend
pnpm tauri dev
```

### Debugging

**Backend**:
- Enable debug logging in `~/.config/fileflow/fileflow.toml`
- Check logs in `~/.local/share/fileflow/fileflow.log`
- Use VS Code debugger (see quickstart.md)

**Frontend**:
- Open DevTools in Tauri app (Cmd+Option+I)
- Use console.log() for debugging
- Check Network tab for IPC calls

**Database**:
```bash
sqlite3 ~/.config/fileflow/fileflow.db
```

### Performance Testing

```bash
# Backend performance
cd backend
poetry run pytest tests/performance/ --benchmark-only

# Build time
cd frontend
time pnpm tauri build
```

### Building for Production

**Backend Package:**
```bash
cd backend
./build.sh  # Runs quality checks and builds wheel + sdist
```

**Backend Executable:**
```bash
cd backend
./build_executable.sh  # Creates standalone executable for Tauri
```

**Frontend DMG:**
```bash
cd frontend
./build-release.sh  # Runs quality checks and builds DMG
```

### Creating a Release

**Automated Release (Maintainers Only):**
```bash
./scripts/create-release.sh patch  # or minor, major
```

This script:
- Runs all quality checks
- Bumps version across all files
- Prompts for changelog updates
- Commits and tags changes
- Pushes to remote and triggers GitHub Actions

**Manual Release:**
```bash
# Bump version
./scripts/bump-version.sh patch

# Update CHANGELOG.md
$EDITOR CHANGELOG.md

# Commit and tag
git add -A
git commit -m "Release v1.0.0"
git tag v1.0.0
git push origin main
git push origin v1.0.0
```

See [RELEASE.md](RELEASE.md) for detailed release documentation.

## License

By contributing, you agree that your contributions will be licensed under the same license as the project (TBD).

## Recognition

Contributors will be recognized in:
- Release notes
- Credits in README.md (for significant contributions)
- GitHub contributors page

Thank you for contributing to FileFlow Manager!
