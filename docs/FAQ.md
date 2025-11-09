# Frequently Asked Questions (FAQ)

Common questions about FileFlow Manager.

## Table of Contents

1. [General Questions](#general-questions)
2. [Features & Capabilities](#features--capabilities)
3. [File Operations](#file-operations)
4. [Rules & Configuration](#rules--configuration)
5. [Safety & Security](#safety--security)
6. [Performance](#performance)
7. [Troubleshooting](#troubleshooting)
8. [Development](#development)

---

## General Questions

### What is FileFlow Manager?

FileFlow Manager is an automated file organization system for macOS that helps you keep your files organized using customizable, rule-based management. It can automatically organize screenshots by date, detect and skip duplicate files, find large or old files for cleanup, and much more.

### Is FileFlow Manager free?

Yes, FileFlow Manager is free and open source. The code is available on GitHub for anyone to use, modify, and contribute to.

### What platforms does it support?

Currently macOS 10.15 (Catalina) or newer. Support for Linux and Windows may be added in the future.

### Do I need to code to use FileFlow Manager?

No! FileFlow Manager has a user-friendly GUI where you can create and manage rules through forms and buttons. There's also a powerful CLI if you prefer the command line.

### Can I use it on multiple Macs?

Yes! You can export your configuration from one Mac and import it on another. See the [Tutorial](TUTORIAL.md#tutorial-6-backing-up-and-sharing-configuration).

---

## Features & Capabilities

### Can FileFlow Manager organize any file type?

Yes! You can create rules for any file type using:
- File extensions (`.pdf`, `.jpg`, `.mp4`, etc.)
- File patterns (`Screenshot*.png`, `*invoice*.pdf`)
- File types (documents, images, videos, audio, archives)

### Does it support organizing by date?

Yes! When you enable "Organize by Date" on a rule, files are organized into:
- Year/Month/Day folders (YYYY/MM/DD)
- Based on file modification date
- Creates folders automatically

### Can it detect duplicates?

Yes! When "Detect Duplicates" is enabled:
- Uses SHA-256 checksums to identify identical files
- Marks duplicates (won't move them twice)
- Cache speeds up subsequent scans
- Only exact byte-for-byte matches

### Can it organize photos by the date they were taken?

The current version organizes by file modification date. Future versions may support EXIF data for photos to use the date taken.

### Does it work with cloud storage (Dropbox, Google Drive, iCloud)?

Yes, as long as the files are synced locally on your Mac. You can set source or destination paths to cloud-synced folders.

**Note:** Be careful with cloud sync - moving files might trigger re-uploads.

### Can I schedule automatic organization?

Not yet, but this is planned for a future release. Currently, you manually run scans when you want to organize files.

---

## File Operations

### Will FileFlow Manager delete my files?

FileFlow Manager will NEVER delete files unless you explicitly:
1. Go to Large Files or Old Files tab
2. Select files to delete
3. Click "Delete Selected"
4. Confirm the deletion

Regular file organization (scan/execute) only MOVES files, never deletes them.

### Can I undo file operations?

There's no automatic undo feature. However:
- Always run a **dry run** first to preview
- Operations are logged in the database
- You can manually move files back if needed

**Best practice:** Use dry run, review carefully, then execute.

### What happens if a file already exists at the destination?

FileFlow Manager will:
1. Check if files are identical (duplicate detection)
2. If identical: Skip moving (mark as duplicate)
3. If different: Add a number to filename (`file-1.pdf`, `file-2.pdf`)
4. Never overwrite existing files

### Can it move files across different drives?

Yes! FileFlow Manager can move files:
- Between internal drives
- To/from external drives
- To/from network drives (slower)

**Note:** Moving between drives is slower than moving within the same drive.

### Does it preserve file metadata?

Yes! FileFlow Manager preserves:
- File modification date
- File creation date
- File permissions
- Extended attributes (xattrs)

---

## Rules & Configuration

### How many rules can I have?

There's no limit! You can create as many rules as you need. Rules run in priority order (highest first).

### What is rule priority?

Priority determines the order rules run (1-100, higher runs first):
- Priority 100: Runs first
- Priority 50: Runs after 100
- Priority 1: Runs last

If a file matches multiple rules, the first matching rule (highest priority) wins.

### Can I temporarily disable a rule?

Yes! Each rule has an enable/disable toggle. Disabled rules won't run during scans but are preserved in your configuration.

### How do glob patterns work?

Glob patterns use wildcards to match filenames:

- `*` = any characters: `*.pdf` matches `file.pdf`, `report.pdf`
- `?` = single character: `file?.txt` matches `file1.txt`, not `file10.txt`
- `{a,b}` = alternatives: `*.{jpg,png}` matches both JPG and PNG
- `[abc]` = character set: `file[123].txt` matches `file1.txt`, `file2.txt`, `file3.txt`

Examples:
```
Screenshot*.png       → Screenshot 2024-01-01.png ✓
*invoice*.pdf         → my-invoice-jan.pdf ✓
report-[0-9][0-9].txt → report-01.txt ✓
*.{jpg,jpeg,png}      → photo.jpg, image.png ✓
```

### Can I exclude certain files from a rule?

Yes! Use exclude patterns:
```
# Rule: *.pdf
# Exclude: *important*, *backup*
#
# Will match:    report.pdf, invoice.pdf
# Won't match:   important-doc.pdf, backup-file.pdf
```

### Can a file match multiple rules?

A file is processed by the FIRST matching rule (highest priority). After that, it's skipped by other rules.

To process with multiple rules, you'd need to run scans separately or use different source directories.

---

## Safety & Security

### Is FileFlow Manager safe to use?

Yes! FileFlow Manager is designed with safety in mind:
- Dry run mode lets you preview before executing
- No files deleted unless you explicitly confirm
- Never overwrites existing files
- All operations are logged
- Open source code you can review

### Does it require Full Disk Access?

For some operations, yes:
- Organizing files in protected directories
- Scanning system locations
- Large file discovery

Grant access in: System Settings → Privacy & Security → Full Disk Access

### Does it send data anywhere?

No! FileFlow Manager is 100% local:
- All data stays on your Mac
- No analytics or tracking
- No internet connection required
- No cloud services

### Can I review changes before they happen?

Yes! That's what dry run mode is for:
1. Click "Scan Files (Dry Run)"
2. Review all proposed operations
3. Check destination paths
4. Only then click "Execute Operations"

### What if I accidentally execute the wrong operation?

- Operations can't be automatically undone
- Check the operation log to see what was moved
- Manually move files back if needed
- Consider keeping backups of important files

**Prevention:** ALWAYS use dry run first!

---

## Performance

### How fast is FileFlow Manager?

Performance depends on several factors:

**Scanning:**
- 1,000 files: ~1-5 seconds
- 10,000 files: ~10-30 seconds
- 100,000 files: ~1-3 minutes

**With duplicate detection (first time):**
- Add ~50% time for checksum calculation
- Cache makes subsequent scans fast

**File operations:**
- Same drive: Very fast (mostly metadata)
- Different drives: Limited by drive speed
- Network drives: Slower (network speed)

### Why is duplicate detection slow?

First scan with duplicate detection:
- Calculates SHA-256 checksum for every file
- Checksums stored in cache
- Subsequent scans use cache (much faster)

**Tip:** Clear cache if files changed significantly.

### How much disk space does it use?

FileFlow Manager itself is small:
- Application: ~50 MB
- Configuration: ~10 KB
- Database: Grows with operation history (~1 MB per 1000 operations)
- Cache: ~100 KB per 1000 files

### Can it handle large files?

Yes! FileFlow Manager can handle:
- Files of any size
- Large file counts (100,000+)
- Large directory trees

Performance may degrade with extremely large datasets (1M+ files).

### Does it use a lot of memory or CPU?

Normal usage:
- Memory: ~200-500 MB
- CPU: Low when idle, higher during scans
- Disk I/O: Moderate during operations

If you see high usage:
- Wait for operations to complete
- Reduce scope of scans
- Clear cache and restart

---

## Troubleshooting

### The app won't open. What do I do?

See [Installation Issues](../TROUBLESHOOTING.md#installation-issues) in the Troubleshooting Guide.

Quick fix:
```bash
xattr -d com.apple.quarantine "/Applications/FileFlow Manager.app"
```

### Scans find no files. Why?

Common causes:
1. No rules enabled (check Rules tab)
2. Patterns don't match files (check case sensitivity)
3. Source directories empty or wrong path
4. Age/size filters too restrictive

See [Scanning Issues](../TROUBLESHOOTING.md#scanning-issues) for detailed diagnosis.

### Files aren't moving. What's wrong?

Common causes:
1. Was it a dry run? (not execute)
2. Destination doesn't exist
3. No write permissions
4. Files marked as duplicates

See [File Operation Issues](../TROUBLESHOOTING.md#file-operation-issues).

### How do I enable debug logging?

Edit `~/.config/fileflow/fileflow.toml`:
```toml
[settings]
log_level = "debug"
```

Then check logs:
```bash
tail -f ~/.local/share/fileflow/fileflow.log
```

### Where are the log files?

Logs are at:
```
~/.local/share/fileflow/fileflow.log
```

View recent logs:
```bash
tail -50 ~/.local/share/fileflow/fileflow.log
```

### Can I reset everything to defaults?

Yes! Delete configuration and database:
```bash
# Backup first
cp -r ~/.config/fileflow ~/.config/fileflow.backup

# Delete config
rm -rf ~/.config/fileflow

# Restart app (creates fresh config)
```

---

## Development

### How do I contribute to FileFlow Manager?

See [CONTRIBUTING.md](../CONTRIBUTING.md) for detailed instructions.

Quick start:
1. Fork the repository
2. Clone your fork
3. Run `./setup.sh`
4. Make your changes
5. Submit a pull request

### How do I run FileFlow Manager from source?

```bash
# Clone repository
git clone https://github.com/DanielTromp/Filefly-specify.git
cd Filefly-specify

# Run automated setup
./setup.sh

# Run GUI
cd frontend
pnpm tauri dev

# Or run CLI
cd backend
poetry run fileflow --help
```

### How do I build a DMG?

```bash
# Build backend executable
cd backend
./build_executable.sh

# Build frontend DMG
cd ../frontend
./build-release.sh

# DMG location:
# src-tauri/target/release/bundle/dmg/
```

### How do I run tests?

```bash
# Backend tests
cd backend
poetry run pytest

# Frontend tests
cd frontend
pnpm test

# All quality checks
./setup.sh  # Runs linting, type checking, tests
```

### What technology stack does it use?

**Backend:**
- Python 3.10+ with type hints
- Poetry for dependency management
- Typer for CLI
- Pydantic for data validation
- SQLite for database

**Frontend:**
- Tauri (Rust framework)
- Svelte 4 for UI
- TypeScript for type safety
- Tailwind CSS + DaisyUI for styling

### Can I use the backend without the GUI?

Yes! The backend is a full-featured CLI:
```bash
cd backend
poetry run fileflow --help
```

All functionality available in GUI is also available in CLI.

### How do I add a new feature?

1. Open a GitHub Issue to discuss
2. Wait for feedback from maintainers
3. Fork and create feature branch
4. Implement feature with tests
5. Update documentation
6. Submit pull request

See [CONTRIBUTING.md](../CONTRIBUTING.md) for detailed workflow.

---

## More Questions?

### I have a question not listed here

Check these resources:
1. [User Guide](USER_GUIDE.md) - Complete usage guide
2. [Troubleshooting Guide](../TROUBLESHOOTING.md) - Common issues
3. [Tutorial](TUTORIAL.md) - Step-by-step walkthroughs
4. [API Documentation](API.md) - For developers

### I found a bug

Please report it:
1. Check [existing issues](https://github.com/DanielTromp/Filefly-specify/issues)
2. If new, open an issue with bug template
3. Include steps to reproduce
4. Attach logs if relevant

### I have a feature request

We'd love to hear it:
1. Check [existing issues](https://github.com/DanielTromp/Filefly-specify/issues)
2. Open an issue with "enhancement" label
3. Describe the feature and use case
4. Explain why it would be useful

### I want to help improve FileFlow Manager

Awesome! Ways to help:
- **Use it and report bugs**
- **Contribute code** (see [CONTRIBUTING.md](../CONTRIBUTING.md))
- **Improve documentation**
- **Help others** in GitHub Discussions
- **Share FileFlow Manager** with friends
- **Star the repository** on GitHub

Thank you for using FileFlow Manager! 🎉
