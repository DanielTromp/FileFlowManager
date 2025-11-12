# FileFlow Manager User Guide

Welcome to FileFlow Manager! This guide will help you get the most out of your automated file organization system.

## Table of Contents

1. [Installation](#installation)
2. [First Launch](#first-launch)
3. [Understanding the Interface](#understanding-the-interface)
4. [Organizing Files](#organizing-files)
5. [Managing Rules](#managing-rules)
6. [Finding Large Files](#finding-large-files)
7. [Finding Old Files](#finding-old-files)
8. [Configuration Management](#configuration-management)
9. [Best Practices](#best-practices)
10. [Tips & Tricks](#tips--tricks)

---

## Installation

### macOS DMG Installation

1. **Download** the latest DMG from [GitHub Releases](https://github.com/DanielTromp/Filefly-specify/releases)
2. **Open** the downloaded DMG file
3. **Drag** FileFlow Manager to your Applications folder
4. **Bypass Gatekeeper** (first launch only):
   - Right-click on FileFlow Manager in Applications
   - Select "Open" from the menu
   - Click "Open" in the dialog
   - The app will launch (this is only needed once)

**Tip:** If you're comfortable with the command line, you can also bypass Gatekeeper with:
```bash
xattr -d com.apple.quarantine "/Applications/FileFlow Manager.app"
```

---

## First Launch

### Welcome Screen

When you first launch FileFlow Manager, you'll see the Dashboard with 5 preset rules ready to use:

1. **Screenshot Organization** - Organizes screenshots by date
2. **PDF Organization** - Organizes PDFs by month
3. **Downloads Cleanup** - Organizes recent downloads
4. **Desktop Cleanup** - Moves files from desktop to organized folders
5. **Photo Organization** - Organizes photos by date taken

### Initial Configuration

FileFlow creates its configuration at:
- **Config**: `~/.config/fileflow/fileflow.toml`
- **Database**: `~/.config/fileflow/fileflow.db`
- **Logs**: `~/.local/share/fileflow/fileflow.log`

You don't need to modify these manually - everything can be done through the GUI.

---

## Understanding the Interface

FileFlow has 5 main tabs:

### 1. Dashboard (Home)

The Dashboard is your command center with three main cards:

**Scan & Organize** (40% width)
- Select which rules to run
- Choose between dry run (preview) and execute (apply changes)
- See operation summary after scanning

**Recent Activity** (30% width)
- View recently scanned files
- See what operations would be/were performed
- Track file movements and changes

**Statistics** (30% width)
- Total files scanned
- Operations pending
- Space that would be saved
- Last scan time (24-hour format, DD-MM-YYYY)

### 2. Rules

Manage your file organization rules:

- **View all rules** in a list with priority order
- **Create new rules** with the "+ New Rule" button
- **Edit rules** by clicking on them
- **Enable/disable rules** with toggle switches
- **Delete rules** with the delete button
- **Reorder priorities** (higher numbers run first)

### 3. Large Files

Find files that are taking up space:

- **Set size threshold** (default: 100 MB)
- **Scan** to find large files
- **Filter by type** (documents, images, videos, etc.)
- **Preview files** before deletion
- **Batch delete** selected files
- **See space reclaimed** estimate

### 4. Old Files

Find files you haven't modified recently:

- **Set age threshold** (default: 365 days)
- **Scan** to find old files
- **Filter by directory** or file type
- **Review modification dates** (DD-MM-YYYY format)
- **Batch delete** selected files
- **See space reclaimed** estimate

### 5. Settings

Manage your configuration:

- **View current settings** in read-only format
- **Export configuration** to share or backup
- **Import configuration** from another machine
- **Clear cache** to reset checksums
- **View help** documentation

---

## Organizing Files

### Running a Scan

1. Go to the **Dashboard** tab
2. Select which rules you want to run (or select all)
3. Click **Scan Files (Dry Run)** to preview operations
4. Review the operations in "Recent Activity"
5. If satisfied, click **Execute Operations** to apply changes

### Understanding Operations

FileFlow performs these operations:

- **Move**: Moves a file to a new location
- **Skip**: File doesn't match any rule
- **Duplicate**: File is identified as a duplicate (won't be moved)

### Dry Run vs Execute

**Dry Run** (Recommended first):
- Shows what WOULD happen
- Doesn't actually move files
- Safe to run anytime
- No undo needed

**Execute**:
- Actually moves/deletes files
- Cannot be undone automatically
- Check dry run results first
- Operations are logged in database

**Best Practice**: Always run a dry run first, review the results, then execute if happy.

---

## Managing Rules

### Creating a New Rule

1. Go to the **Rules** tab
2. Click **+ New Rule**
3. Fill in the rule details:

**Basic Information**:
- **Name**: Descriptive name (e.g., "Work Documents")
- **Description**: What this rule does
- **Priority**: Higher numbers run first (1-100)
- **Enabled**: Turn rule on/off

**File Selection**:
- **Source Patterns**: Glob patterns (e.g., `*.pdf`, `*.{jpg,png}`)
- **Source Directories**: Where to look for files (e.g., `~/Desktop`, `~/Downloads`)
- **Exclude Patterns**: Patterns to skip (e.g., `*important*`, `*backup*`)

**File Filters**:
- **File Types**: Documents, Images, Videos, Audio, Archives
- **Min Size**: Minimum file size in KB
- **Max Size**: Maximum file size in KB
- **Min Age**: Minimum file age in days
- **Max Age**: Maximum file age in days

**Organization**:
- **Destination**: Where to move matching files
- **Organize by Date**: Create YYYY/MM/DD folder structure
- **Detect Duplicates**: Skip files that are duplicates

4. Click **Save Rule**

### Example Rules

**Screenshots to dated folders**:
```
Name: Screenshot Organization
Patterns: Screenshot*.png, Screen Shot*.png
Source: ~/Desktop
Destination: ~/Pictures/Screenshots
Organize by Date: ✓
Detect Duplicates: ✓
```

**Recent PDFs from Downloads**:
```
Name: Recent PDFs
Patterns: *.pdf
Source: ~/Downloads
Destination: ~/Documents/PDFs
Max Age: 30 days
Organize by Date: ✓ (by month)
```

**Large Videos**:
```
Name: Large Videos
Patterns: *.{mp4,mov,avi}
Source: ~/Downloads
Destination: ~/Movies/Archive
Min Size: 100000 KB (100 MB)
```

### Editing Rules

1. Click on any rule in the list
2. Modify the fields you want to change
3. Click **Save Rule**

Changes take effect on the next scan.

### Disabling Rules Temporarily

Use the toggle switch next to each rule to enable/disable it without deleting.

Disabled rules won't run during scans.

### Rule Priority

Rules run in priority order (highest first):
- Priority 100 runs before Priority 50
- If files match multiple rules, the first match wins
- Set more specific rules to higher priorities

---

## Finding Large Files

### Basic Usage

1. Go to the **Large Files** tab
2. Set size threshold (default 100 MB)
3. Click **Scan for Large Files**
4. Review the list sorted by size
5. Select files to delete
6. Click **Delete Selected**
7. Confirm the operation

### Filtering Results

- **By Type**: Use file type filters (all, documents, images, videos, etc.)
- **By Size**: Adjust threshold to see more/fewer files
- **By Location**: See where each file is located

### Understanding the Results

Each result shows:
- **File name** with full path
- **Size** in human-readable format (MB, GB)
- **Last modified** date (DD-MM-YYYY, 24h format)
- **Type** (document, image, video, etc.)

### Space Reclamation

The total at the bottom shows:
- **Number of files** selected
- **Total space** that will be freed
- **Percentage** of total files

---

## Finding Old Files

### Basic Usage

1. Go to the **Old Files** tab
2. Set age threshold (default 365 days)
3. Click **Scan for Old Files**
4. Review the list sorted by age (oldest first)
5. Select files to delete
6. Click **Delete Selected**
7. Confirm the operation

### Filtering Results

- **By Age**: Adjust threshold to see older/newer files
- **By Type**: Filter by file type
- **By Location**: See where files are located

### Understanding the Results

Each result shows:
- **File name** with full path
- **Age** in days since last modification
- **Last modified** date (DD-MM-YYYY, 24h format)
- **Size** in human-readable format

### Exclusions

Old file scanning automatically excludes:
- System files and directories
- Application bundles (.app)
- Hidden files (starting with .)
- Files in excluded directories (configurable in config)

---

## Configuration Management

### Viewing Current Configuration

1. Go to the **Settings** tab
2. Your current configuration is displayed (read-only)
3. See all rules, settings, and preferences

### Exporting Configuration

**Use Case**: Backup or share your setup with another machine

1. Go to **Settings** tab
2. Click **Export Configuration**
3. Choose a location and filename
4. Click **Save**

Creates a `.toml` file with all your rules and settings.

### Importing Configuration

**Use Case**: Restore from backup or copy setup to new machine

1. Go to **Settings** tab
2. Click **Import Configuration**
3. Select your `.toml` file
4. Choose import mode:
   - **Replace**: Overwrites all existing rules
   - **Merge**: Adds new rules, keeps existing ones
5. Click **Import**

### Environment Variables in Paths

FileFlow supports environment variables in paths:
- `${HOME}` - Your home directory
- `${DESKTOP}` - Desktop folder
- `${DOCUMENTS}` - Documents folder
- `${DOWNLOADS}` - Downloads folder
- `${PICTURES}` - Pictures folder

Example: `${HOME}/Pictures/Screenshots` becomes `/Users/yourusername/Pictures/Screenshots`

---

## Best Practices

### Organization Tips

1. **Start with Dry Runs**
   - Always preview before executing
   - Check that files go to expected locations
   - Verify duplicate detection works correctly

2. **Use Specific Patterns**
   - `Screenshot*.png` is better than `*.png`
   - Use exclude patterns to skip important files
   - Combine patterns for precision: `*.{jpg,jpeg,png}`

3. **Set Appropriate Priorities**
   - High priority (90-100): Very specific rules
   - Medium priority (50-89): General rules
   - Low priority (1-49): Catch-all rules

4. **Enable Duplicate Detection**
   - For photos and screenshots
   - For documents from multiple sources
   - Saves disk space

5. **Use Date Organization**
   - For time-sensitive files (screenshots, photos)
   - Creates logical folder structure
   - Easy to find files by date

### Maintenance

1. **Regular Scans**
   - Run weekly or monthly
   - More frequent for active directories (Downloads, Desktop)
   - Less frequent for stable directories

2. **Review Rules Periodically**
   - Disable unused rules
   - Update paths when you reorganize
   - Adjust priorities as needed

3. **Clean Up Large/Old Files**
   - Monthly: Check for large files in Downloads
   - Quarterly: Check for old files across system
   - Annual: Deep clean with lower thresholds

4. **Backup Configuration**
   - Export config before major changes
   - Keep backups when upgrading
   - Share config across machines

### Safety

1. **Test New Rules**
   - Create rule with specific source directory
   - Run dry run
   - Check a few files manually
   - Then expand to full directories

2. **Use Exclude Patterns**
   - Protect important files: `*important*`, `*backup*`
   - Skip work in progress: `*draft*`, `*temp*`
   - Avoid system files: `.*`, `*.app`

3. **Review Before Execute**
   - Check operation count is reasonable
   - Verify destinations exist
   - Look for unexpected operations

---

## Tips & Tricks

### Keyboard Shortcuts

- **⌘ + R**: Refresh current view
- **⌘ + S**: Save (when editing rules)
- **⌘ + W**: Close window
- **⌘ + Q**: Quit application

### Hidden Features

1. **Batch Operations**
   - Select multiple files with Shift+Click
   - Use Cmd+A to select all
   - Ctrl+Click for non-contiguous selection

2. **Search in Results**
   - Use browser search (⌘+F) in result tables
   - Filter by filename, path, or size
   - Works in all tabs

3. **Quick Rule Toggle**
   - Double-click rule name to edit
   - Single-click toggle to enable/disable
   - Click priority to sort rules

### Performance

1. **Large Scans**
   - Scanning 10,000+ files may take a minute
   - Progress shown in loading spinner
   - Can continue using other tabs during scan

2. **Duplicate Detection**
   - First scan is slower (calculates checksums)
   - Subsequent scans are faster (uses cache)
   - Clear cache if files changed significantly

3. **Database Growth**
   - Database grows with operation history
   - Located at `~/.config/fileflow/fileflow.db`
   - Can be deleted to reset (will lose history)

### Troubleshooting

See [TROUBLESHOOTING.md](../TROUBLESHOOTING.md) for common issues and solutions.

Common quick fixes:
- **Scan not finding files**: Check source directory paths
- **Files not moving**: Check destination directory exists
- **Duplicates not detected**: Clear cache and rescan
- **App won't open**: Remove from quarantine (see Installation)

---

## Getting Help

### Documentation

- **User Guide**: This document
- **Troubleshooting**: [TROUBLESHOOTING.md](../TROUBLESHOOTING.md)
- **FAQ**: [FAQ.md](FAQ.md)
- **API Docs**: [API.md](API.md)

### Community

- **GitHub Issues**: Report bugs and request features
- **GitHub Discussions**: Ask questions and share tips
- **Release Notes**: See what's new in each version

### Contact

For questions or feedback:
- Open an issue on GitHub
- Check existing discussions
- Review the FAQ first

---

## What's Next?

Now that you know the basics:

1. **Explore the preset rules** - See how they work
2. **Create your first custom rule** - Organize your workflow
3. **Run a large files scan** - Free up space
4. **Export your config** - Backup your setup
5. **Share your experience** - Help others get started

Happy organizing! 🗂️
