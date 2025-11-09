# FileFlow Manager Tutorial

This tutorial will walk you through common file organization scenarios using FileFlow Manager.

## Table of Contents

1. [Tutorial 1: Organizing Screenshots](#tutorial-1-organizing-screenshots)
2. [Tutorial 2: Cleaning Up Downloads](#tutorial-2-cleaning-up-downloads)
3. [Tutorial 3: Creating Custom Rules](#tutorial-3-creating-custom-rules)
4. [Tutorial 4: Finding and Deleting Large Files](#tutorial-4-finding-and-deleting-large-files)
5. [Tutorial 5: Organizing Photos by Date](#tutorial-5-organizing-photos-by-date)
6. [Tutorial 6: Backing Up and Sharing Configuration](#tutorial-6-backing-up-and-sharing-configuration)

---

## Tutorial 1: Organizing Screenshots

**Goal**: Automatically organize screenshots by date into a clean folder structure.

**Time**: 5 minutes

### Step 1: Launch FileFlow Manager

1. Open FileFlow Manager from your Applications folder
2. If this is your first launch, you'll see the Dashboard with preset rules

### Step 2: Check the Screenshot Rule

1. Click on the **Rules** tab
2. Find "Screenshot Organization" in the list
3. Click on it to see the details:
   - **Source Patterns**: `Screenshot*.png`, `Screen Shot*.png`
   - **Source Directories**: `~/Desktop`
   - **Destination**: `~/Pictures/Screenshots`
   - **Organize by Date**: ✓ Enabled
   - **Detect Duplicates**: ✓ Enabled

### Step 3: Test with Dry Run

1. Go back to the **Dashboard** tab
2. Ensure "Screenshot Organization" is checked
3. Click **Scan Files (Dry Run)**
4. Wait for the scan to complete

### Step 4: Review Results

1. Look at the **Recent Activity** card
2. You'll see each screenshot that was found
3. Check the destination paths - they should show:
   ```
   ~/Pictures/Screenshots/YYYY/MM/DD/Screenshot...png
   ```
4. Verify the count in the **Statistics** card

### Step 5: Execute Operations

1. If you're happy with the preview, click **Execute Operations**
2. Click **Confirm** in the dialog
3. Wait for completion
4. Check `~/Pictures/Screenshots` in Finder - your screenshots are now organized by date!

**What you learned**:
- How to run a dry run
- How to review operations before executing
- How date-based organization works
- How to verify operations completed

---

## Tutorial 2: Cleaning Up Downloads

**Goal**: Move recent downloads to organized folders and clean up old files.

**Time**: 10 minutes

### Step 1: Enable the Downloads Cleanup Rule

1. Go to the **Rules** tab
2. Find "Downloads Cleanup"
3. Toggle it **On** if it's off
4. Click on it to review settings:
   - Moves files from `~/Downloads`
   - Files less than 30 days old
   - Organized by file type

### Step 2: Scan Downloads

1. Go to **Dashboard**
2. Select "Downloads Cleanup"
3. Click **Scan Files (Dry Run)**
4. Review where files will go:
   - PDFs → `~/Documents/PDFs`
   - Images → `~/Pictures`
   - Videos → `~/Movies`
   - Documents → `~/Documents`

### Step 3: Adjust if Needed

If you want different destinations:

1. Go to **Rules** tab
2. Click "Downloads Cleanup"
3. Modify the **Destination** field
4. Click **Save Rule**
5. Go back to **Dashboard** and scan again

### Step 4: Execute

1. Click **Execute Operations**
2. Confirm
3. Check your Downloads folder - much cleaner!

### Step 5: Find Old Files

1. Go to the **Old Files** tab
2. Set threshold to **180 days** (6 months)
3. Click **Scan for Old Files**
4. Review the list - sorted by oldest first
5. Select files you want to delete
6. Click **Delete Selected**
7. Confirm deletion

**What you learned**:
- How to enable/disable rules
- How to modify rule settings
- How file type organization works
- How to find and delete old files

---

## Tutorial 3: Creating Custom Rules

**Goal**: Create a custom rule to organize work documents.

**Time**: 10 minutes

### Scenario

You download work documents to `~/Downloads` and want them automatically moved to `~/Documents/Work` when they contain "invoice" or "report" in the filename.

### Step 1: Create the Rule

1. Go to the **Rules** tab
2. Click **+ New Rule**
3. Fill in the basic information:
   - **Name**: Work Documents
   - **Description**: Organize work invoices and reports
   - **Priority**: 80 (higher than general downloads rule)
   - **Enabled**: ✓ On

### Step 2: Configure File Selection

1. **Source Patterns**:
   ```
   *invoice*.pdf
   *report*.pdf
   *Invoice*.pdf
   *Report*.pdf
   ```
   (One pattern per line)

2. **Source Directories**:
   ```
   ~/Downloads
   ```

3. **Exclude Patterns**:
   ```
   *personal*
   *Personal*
   ```
   (Skip files with "personal" in the name)

### Step 3: Configure Filters

1. **File Types**: Select "Documents"
2. **Min Size**: Leave empty
3. **Max Size**: Leave empty
4. **Min Age**: Leave empty
5. **Max Age**: `30` days (only recent files)

### Step 4: Configure Organization

1. **Destination**: `~/Documents/Work`
2. **Organize by Date**: ✓ Check (creates YYYY/MM folders)
3. **Detect Duplicates**: ✓ Check

### Step 5: Save and Test

1. Click **Save Rule**
2. Go to **Dashboard**
3. Select "Work Documents"
4. Click **Scan Files (Dry Run)**
5. Review results
6. If correct, click **Execute Operations**

### Step 6: Test the Rule

1. Download a test PDF with "invoice" in the filename
2. Go to **Dashboard**
3. Run scan again
4. The file should appear in results
5. Execute to move it

**What you learned**:
- How to create custom rules from scratch
- How to use pattern matching
- How to set rule priorities
- How to use exclude patterns
- How to combine filters

---

## Tutorial 4: Finding and Deleting Large Files

**Goal**: Free up disk space by finding and removing large files.

**Time**: 10 minutes

### Step 1: Find Large Files

1. Go to the **Large Files** tab
2. Set threshold to **100 MB**
3. Click **Scan for Large Files**
4. Wait for scan to complete

### Step 2: Review Results

The results show:
- **File name** and full path
- **Size** (in MB or GB)
- **Last modified** date
- **Type** (document, video, image, etc.)

Results are sorted by size (largest first).

### Step 3: Filter Results

Try different filters:

1. **By Size**:
   - Change threshold to **500 MB** for only very large files
   - Or **50 MB** to see more files

2. **By Type**:
   - Click "Videos" to see only video files
   - Click "Documents" to see only documents
   - Click "All" to see everything

### Step 4: Identify Files to Delete

Common candidates:
- Old downloads you don't need
- Duplicate movies or videos
- Large temporary files
- Old disk images (.dmg, .iso)
- Installation files you've already used

### Step 5: Select and Delete

1. Click checkboxes next to files you want to delete
2. OR use **Shift+Click** to select a range
3. Review the total space that will be freed (shown at bottom)
4. Click **Delete Selected**
5. **Confirm** the deletion
6. Wait for completion

### Step 6: Verify

1. Check that the count decreased
2. Check that space reclaimed shows correctly
3. Verify files are gone from Finder

**What you learned**:
- How to find large files quickly
- How to filter by size and type
- How to select multiple files
- How to see space reclamation estimates
- How to safely delete files

---

## Tutorial 5: Organizing Photos by Date

**Goal**: Organize photos into a date-based folder structure.

**Time**: 10 minutes

### Step 1: Create Photo Organization Rule

1. Go to **Rules** tab
2. Click **+ New Rule**
3. Fill in details:
   - **Name**: Photo Organization
   - **Description**: Organize photos by date taken
   - **Priority**: 70
   - **Enabled**: ✓ On

### Step 2: Configure Patterns

1. **Source Patterns**:
   ```
   *.jpg
   *.jpeg
   *.png
   *.heic
   *.HEIC
   *.JPG
   *.JPEG
   ```

2. **Source Directories**:
   ```
   ~/Downloads
   ~/Desktop
   ```

3. **Exclude Patterns**:
   ```
   Screenshot*
   Screen Shot*
   ```

### Step 3: Configure Filters

1. **File Types**: Select "Images"
2. **Min Age**: Leave empty
3. **Max Age**: `90` days (last 3 months)

### Step 4: Configure Organization

1. **Destination**: `~/Pictures/Organized`
2. **Organize by Date**: ✓ Check
3. **Detect Duplicates**: ✓ Check

### Step 5: Test

1. Save the rule
2. Go to **Dashboard**
3. Select "Photo Organization"
4. Run **Dry Run**
5. Check that photos will go to:
   ```
   ~/Pictures/Organized/YYYY/MM/DD/photo.jpg
   ```
6. Execute if satisfied

**What you learned**:
- How to organize multiple file extensions
- How to exclude specific patterns
- How to use file type filters
- How duplicate detection prevents copies

---

## Tutorial 6: Backing Up and Sharing Configuration

**Goal**: Export your configuration to use on another Mac.

**Time**: 5 minutes

### Step 1: Export Configuration

1. Go to the **Settings** tab
2. Click **Export Configuration**
3. Choose a location (e.g., Desktop)
4. Name it `fileflow-config.toml`
5. Click **Save**

### Step 2: Review the Export

1. Open the file in a text editor
2. You'll see:
   - All your rules
   - Settings and preferences
   - Paths using environment variables (e.g., `${HOME}`)

### Step 3: Transfer to Another Mac

1. Copy the `fileflow-config.toml` file to your other Mac
   - Via AirDrop
   - Via USB drive
   - Via cloud storage

### Step 4: Import on New Mac

1. Launch FileFlow Manager on the new Mac
2. Go to **Settings** tab
3. Click **Import Configuration**
4. Select your `fileflow-config.toml` file
5. Choose import mode:
   - **Replace**: Delete all existing rules and use imported ones
   - **Merge**: Keep existing rules and add imported ones
6. Click **Import**

### Step 5: Verify

1. Go to **Rules** tab
2. Verify all your rules are there
3. Check that paths resolved correctly:
   - `${HOME}` becomes `/Users/yourusername`
   - `${DESKTOP}` becomes `/Users/yourusername/Desktop`
   - etc.

### Step 6: Adjust Paths if Needed

If you have different folder structures on different Macs:

1. Edit each rule
2. Update **Source Directories** and **Destination**
3. Save changes
4. Export again for future use

**What you learned**:
- How to export configuration
- How to import configuration
- How environment variables work
- How to maintain config across machines
- When to use Replace vs Merge

---

## Next Steps

### Practice Scenarios

1. **Desktop Cleanup**: Create a rule to move files from Desktop to appropriate folders
2. **Archive Old Documents**: Find documents older than 1 year and move to Archive folder
3. **Organize Music**: Create rules for different music file types
4. **Video Organization**: Organize videos by size (short vs long)

### Advanced Techniques

1. **Complex Patterns**: Use multiple patterns with wildcards
2. **Priority Tuning**: Adjust priorities for perfect rule ordering
3. **Scheduled Scans**: Set up regular organization (future feature)
4. **Custom Destinations**: Create dynamic destination paths

### Troubleshooting

If something doesn't work as expected:

1. Check [TROUBLESHOOTING.md](../TROUBLESHOOTING.md)
2. Review [FAQ.md](FAQ.md)
3. Enable debug logging in settings
4. Check logs at `~/.local/share/fileflow/fileflow.log`

### Getting Help

- **Questions**: Open a GitHub Discussion
- **Bugs**: Open a GitHub Issue
- **Features**: Open a GitHub Issue with "enhancement" label
- **Documentation**: Check [USER_GUIDE.md](USER_GUIDE.md)

---

## Tutorial Completed! 🎉

You now know how to:
- ✅ Use preset rules for common tasks
- ✅ Create custom rules for your workflow
- ✅ Find and delete large/old files
- ✅ Organize files by date
- ✅ Export and import configuration
- ✅ Test changes with dry run before executing

Start organizing your files and enjoy a cleaner, more efficient file system!
