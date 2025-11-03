<!--
Sync Impact Report:
- Version: NEW → 1.0.0
- Type: MAJOR - Initial constitution ratification
- Modified Principles: N/A (initial creation)
- Added Sections: All sections (initial creation)
  1. Core Principles (5 principles: Data Safety First, User Control & Transparency, Extensibility & Future-Proofing, Cross-Device Compatibility, Performance & Reliability)
  2. Immutable Constraints (Technical Stack, File Integrity Rules, Architecture Boundaries, User Experience Mandates)
  3. Non-Negotiable Features (10 mandatory features)
  4. Forbidden Patterns (9 anti-patterns)
  5. Success Criteria (7 measurable outcomes)
  6. Evolution Guidelines (requirements for new features)
  7. Governance (amendment process and compliance)
- Removed Sections: N/A (initial creation)
- Templates Requiring Updates:
  ✅ plan-template.md - Constitution Check section compatible (generic gates structure)
  ✅ spec-template.md - No constitution-specific references, compatible
  ✅ tasks-template.md - Generic structure supports safety/testing principles
  ✅ agent-file-template.md - Generic structure, no updates needed
  ✅ checklist-template.md - Generic structure, no updates needed
- Follow-up TODOs: None
-->

# FileFlow Manager Constitution

## Project Identity

**Name:** FileFlow Manager
**Purpose:** Intelligent, automated file organization system for macOS with extensible rule-based management
**Philosophy:** "Organize automatically, control manually, extend infinitely"

## Core Principles

### I. Data Safety First

File integrity and data safety are paramount and non-negotiable:

- NEVER delete files without explicit user confirmation or SHA-256 checksum verification
- ALWAYS perform dry-run capability before actual operations
- ALWAYS log all file operations with timestamps and checksums
- NEVER overwrite files without checksum comparison
- MAINTAIN operation rollback capability through detailed logging

**Rationale:** User trust depends entirely on never losing data. A single accidental deletion destroys credibility. Every operation must be reversible or verifiable.

### II. User Control & Transparency

Users must understand and control every automated action:

- User must be able to see what will happen before it happens (dry-run)
- All rules must be visible and editable through GUI
- Configuration must be human-readable and version-controllable
- Every automatic action must be auditable through logs
- User can disable any rule at any time

**Rationale:** Automation without visibility breeds distrust. Users must feel in control, not fighting against a black box. Transparency enables learning and refinement.

### III. Extensibility & Future-Proofing

The system must grow with user needs without breaking:

- Rule system must support unlimited custom rules
- File type categories must be easily extensible
- Folder mappings must be user-configurable
- Architecture must allow adding new features without breaking existing ones
- Configuration format must support schema evolution

**Rationale:** User needs evolve. A rigid system becomes obsolete. Extensibility ensures longevity and prevents vendor lock-in to our design assumptions.

### IV. Cross-Device Compatibility

Support diverse macOS configurations without hardcoding assumptions:

- Support different screenshot locations (Desktop vs Downloads)
- Detect system configuration automatically where possible
- Allow manual override of detected settings
- Configuration must be portable across devices

**Rationale:** MacOS users configure systems differently. Hardcoded paths fail for multi-device workflows. Portability enables team/family sharing.

### V. Performance & Reliability

The system must be fast, stable, and non-intrusive:

- File operations must be atomic where possible
- Large file scans must not block the GUI
- Background operations must be cancellable
- Memory footprint must remain reasonable (< 200MB)
- Startup time must be under 3 seconds

**Rationale:** A slow or unreliable organizer is worse than manual organization. Performance enables trust in automation. Resource efficiency respects user hardware.

## Immutable Constraints

### Technical Stack

The following technology choices are fixed for architectural consistency:

- **Backend:** Python 3.10+ (for file operations, logic)
- **Frontend:** Tauri + Svelte (native performance, modern UI)
- **IPC:** Tauri commands for Python-to-GUI communication
- **Config Format:** TOML (human-readable, structured)
- **Database:** SQLite (operation history, file index)
- **CLI Framework:** Click or Typer

**Justification:** Python for robust file operations, Tauri for native performance without Electron bloat, TOML for human-editable configs, SQLite for embedded persistence without server dependencies.

### File Integrity Rules

These cryptographic and metadata rules are immutable:

- SHA-256 for all duplicate detection (no MD5 or weak hashes)
- Checksums must be cached to avoid recalculation
- Original modification timestamps must be preserved
- File permissions must be maintained during moves

**Justification:** SHA-256 is collision-resistant and industry standard. Caching prevents performance degradation. Preserving metadata maintains file provenance and user workflows.

### Architecture Boundaries

Clear separation of concerns is mandatory:

- GUI layer communicates with backend ONLY through defined API
- Backend must be fully functional without GUI (CLI-first design)
- Configuration changes must not require application restart
- Each rule must be independently enable/disable-able

**Justification:** Separation enables testing, automation, and alternative UIs. CLI-first ensures power users aren't blocked by GUI. Hot-reload prevents workflow interruption.

### User Experience Mandates

These responsiveness and clarity rules are non-negotiable:

- No operation should take > 5 seconds without progress indicator
- Error messages must be actionable (tell user what to do)
- All destructive actions require confirmation or dry-run validation
- GUI must be responsive even during heavy file operations

**Justification:** Perceived responsiveness builds trust. Actionable errors reduce support burden. Confirmation prevents regret. Responsiveness prevents frustration.

## Non-Negotiable Features

These 10 features define the minimum viable product and must always be present:

1. **Dry Run Mode:** Every operation must have a dry-run preview
2. **Duplicate Detection:** SHA-256 checksum-based, not name-based
3. **Date Organization:** Screenshots organized by YYYY/MM/DD structure
4. **Rollback Logging:** All operations logged with enough detail to reverse
5. **File Type Presets:** Preconfigured categories for common file types
6. **Large File Detection:** Configurable threshold (default: 100MB)
7. **Old File Detection:** Configurable age threshold (default: 90 days)
8. **Multi-tab GUI:** Separate tabs for triggers, config, large files, old files
9. **CLI Interface:** Full feature parity with GUI operations
10. **Config File Export/Import:** Settings must be portable

**Justification:** These features collectively deliver the core value proposition: safe, intelligent, automated file organization with user control.

## Forbidden Patterns

These anti-patterns are explicitly banned to protect users and maintainability:

- ❌ No silent file deletion without checksum verification
- ❌ No hardcoded file paths (except for macOS defaults as fallbacks)
- ❌ No blocking operations on main GUI thread
- ❌ No storing sensitive data in plain text
- ❌ No modifying files in-place (only moves and deletes)
- ❌ No ignoring file operation errors
- ❌ No single-threaded sequential processing for large batches
- ❌ No proprietary config formats
- ❌ No tightly coupling rules to specific folder structures

**Rationale:** Each forbidden pattern represents a failure mode that breaks user trust (data loss), portability (hardcoded paths), usability (blocking), security (plain text secrets), or performance (sequential processing).

## Success Criteria

The application succeeds if it meets these measurable outcomes:

1. A non-technical user can configure their first rule in < 2 minutes
2. Processing 1000 files takes < 30 seconds on average hardware
3. Zero data loss incidents in normal operation
4. Configuration survives system crashes without corruption
5. User can understand what happened by reading the log
6. Adding a new file type category takes < 1 minute
7. Application runs stable for 30+ days without restart

**Measurement:** These criteria must be validated through usability testing (criteria 1, 6), performance benchmarks (2), operational monitoring (3, 7), crash recovery testing (4), and log readability reviews (5).

## Evolution Guidelines

When adding new features, they MUST satisfy all of the following requirements:

- Maintain backward compatibility with existing configs
- Follow the same pattern as existing features (consistency)
- Include both GUI and CLI interfaces
- Have comprehensive error handling
- Be documented in user-facing help text
- Include dry-run capability where applicable
- Be independently toggleable

**Justification:** Consistency reduces learning curve. Dual interfaces serve all user types. Error handling prevents silent failures. Documentation enables self-service. Dry-run maintains safety. Toggleability preserves user control.

## Governance

### Constitution Authority

This constitution supersedes all other project practices, guidelines, and conventions. When conflicts arise between this document and any other guidance, this constitution takes precedence.

### Amendment Process

Amendments to this constitution require:

1. **Proposal:** Written justification explaining the need for change
2. **Impact Analysis:** Assessment of how the change affects existing features, codebase, and user workflows
3. **Migration Plan:** If breaking backward compatibility, a concrete migration path for users
4. **Approval:** Consensus from maintainers (or project owner if solo project)
5. **Documentation:** Update to this file with version increment per semantic versioning

### Versioning Policy

Constitution versions follow semantic versioning:

- **MAJOR:** Backward incompatible governance/principle removals or redefinitions
- **MINOR:** New principle/section added or materially expanded guidance
- **PATCH:** Clarifications, wording improvements, typo fixes, non-semantic refinements

### Compliance Review

All pull requests and code reviews must verify compliance with this constitution:

- Feature designs must align with Core Principles
- Implementations must respect Immutable Constraints
- New features must include Non-Negotiable Features applicable to that domain
- Code must avoid all Forbidden Patterns
- Changes must preserve or improve Success Criteria outcomes

### Complexity Justification

Any deviation from this constitution (e.g., introducing a Forbidden Pattern, violating a principle) must be explicitly justified in the plan.md Complexity Tracking section with:

- What constitutional rule is being violated
- Why the violation is necessary for the current need
- What simpler constitutional-compliant alternative was rejected and why

**Version**: 1.0.0 | **Ratified**: 2025-11-03 | **Last Amended**: 2025-11-03
