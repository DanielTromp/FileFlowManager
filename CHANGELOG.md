# Changelog

All notable changes to FileFlow Manager will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Initial setup and configuration scripts
- Automated quality checks in CI/CD
- Python package build automation
- DMG build automation for macOS
- GitHub Actions release workflow

### Changed
- Improved type safety across backend codebase
- Enhanced ESLint configuration for frontend
- Updated documentation with complete setup instructions

### Fixed
- All mypy type errors (40 issues resolved)
- All ESLint errors (28 issues resolved)
- Loading spinner visibility in DMG builds
- CSP configuration for DaisyUI assets

## [0.1.2] - 2025-01-09

### Added
- Loading spinners for all async operations
- European date/time format (24h clock, DD-MM-YYYY)
- Automated DMG builds via GitHub Actions
- Help button linking to GitHub documentation
- Date formatting utility module

### Changed
- Dashboard layout adjusted to 40%-30%-30% for better date display
- API parameter naming to camelCase for Tauri compatibility

### Fixed
- Help button now opens GitHub documentation correctly
- API parameter mismatches in configuration and cache operations

## [0.1.1] - 2025-01-08

### Added
- Architecture-specific backend binary symlinks for Tauri
- Shell permissions for opening URLs
- Release process documentation

### Fixed
- DMG loading spinner not showing (CSP and Tailwind safelist)
- Backend binary path resolution on different architectures

## [0.1.0] - 2025-01-07

### Added
- Initial release of FileFlow Manager
- Rule-based file organization system
- Screenshot organization preset
- PDF organization preset
- Downloads organization preset
- Desktop cleanup preset
- Photo organization preset
- File duplicate detection
- File age-based organization
- File size-based filtering
- Dry run mode for safe testing
- Operation history tracking
- SQLite-based storage
- Cross-platform GUI with Tauri
- Command-line interface with Typer
- Comprehensive test suite
- Type-safe Python backend with mypy
- ESLint and Prettier for frontend

---

## Version History Format

Each version entry should follow this structure:

```markdown
## [X.Y.Z] - YYYY-MM-DD

### Added
- New features and capabilities

### Changed
- Changes to existing functionality

### Deprecated
- Features that will be removed in future versions

### Removed
- Features that were removed

### Fixed
- Bug fixes

### Security
- Security improvements or vulnerability fixes
```

## Release Links

- [Unreleased]: https://github.com/YOUR_ORG/fileflow-manager/compare/v0.1.2...HEAD
- [0.1.2]: https://github.com/YOUR_ORG/fileflow-manager/compare/v0.1.1...v0.1.2
- [0.1.1]: https://github.com/YOUR_ORG/fileflow-manager/compare/v0.1.0...v0.1.1
- [0.1.0]: https://github.com/YOUR_ORG/fileflow-manager/releases/tag/v0.1.0
