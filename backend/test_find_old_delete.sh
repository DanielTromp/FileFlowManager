#!/bin/bash
# Test script for find-old --delete functionality

set -e

echo "=== Testing find-old --delete functionality ==="
echo

# Create a temporary test directory
TEST_DIR="/tmp/fileflow_test_old_files_$$"
mkdir -p "$TEST_DIR"
echo "Created test directory: $TEST_DIR"

# Create some test files with different ages
echo "Creating test files..."
for i in {1..5}; do
    FILE="$TEST_DIR/old_file_$i.txt"
    echo "Test content $i" > "$FILE"
    # Make files appear old by setting modification time to 100 days ago
    touch -t $(date -v-100d +%Y%m%d%H%M.%S) "$FILE" 2>/dev/null || \
    touch -d "100 days ago" "$FILE" 2>/dev/null
    echo "  Created: $FILE"
done

# Create some recent files (should not be found)
for i in {1..2}; do
    FILE="$TEST_DIR/recent_file_$i.txt"
    echo "Recent content $i" > "$FILE"
    echo "  Created: $FILE (recent)"
done

echo
echo "Files created:"
ls -lh "$TEST_DIR"

# Update config to monitor the test directory
CONFIG_FILE="$HOME/.fileflow/config.yaml"
BACKUP_CONFIG="${CONFIG_FILE}.backup_$$"

if [ -f "$CONFIG_FILE" ]; then
    echo
    echo "Backing up config to: $BACKUP_CONFIG"
    cp "$CONFIG_FILE" "$BACKUP_CONFIG"
fi

# Add test directory to monitored directories
echo
echo "Updating config to monitor test directory..."
mkdir -p "$(dirname "$CONFIG_FILE")"

cat > "$CONFIG_FILE" << EOF
version: "1.0"
paths:
  monitored_directories:
    - "$TEST_DIR"
  default_destination: "/tmp"
rules:
  screenshot_organization:
    enabled: true
    source_patterns:
      - "Screenshot*.png"
    destination: "~/Pictures/Screenshots"
    date_format: "%Y/%m"
EOF

echo "Config updated."

# Test 1: find-old without --delete (should show files)
echo
echo "=== Test 1: Find old files (no deletion) ==="
/Users/daniel/.local/bin/poetry run fileflow find-old

# Test 2: find-old with --delete but --output json (should error)
echo
echo "=== Test 2: Test --delete with --output json (should error) ==="
if /Users/daniel/.local/bin/poetry run fileflow find-old --delete --output json 2>&1 | grep -q "Error.*interactive mode only"; then
    echo "✓ Correctly rejected --delete with --output json"
else
    echo "✗ Failed to reject invalid flag combination"
    exit 1
fi

# Test 3: find-old with --delete (will prompt - we'll test the code path exists)
echo
echo "=== Test 3: Test --delete flag (will be cancelled by script) ==="
echo "n" | /Users/daniel/.local/bin/poetry run fileflow find-old --delete && echo "✓ Interactive deletion prompt works"

# Verify files still exist
echo
echo "Verifying files were not deleted (cancelled)..."
OLD_FILES_COUNT=$(find "$TEST_DIR" -name "old_file_*.txt" | wc -l)
if [ "$OLD_FILES_COUNT" -eq 5 ]; then
    echo "✓ Files still exist (deletion was cancelled)"
else
    echo "✗ Unexpected file count: $OLD_FILES_COUNT (expected 5)"
    exit 1
fi

# Cleanup
echo
echo "=== Cleanup ==="
rm -rf "$TEST_DIR"
echo "Removed test directory"

if [ -f "$BACKUP_CONFIG" ]; then
    mv "$BACKUP_CONFIG" "$CONFIG_FILE"
    echo "Restored config"
fi

echo
echo "=== All tests passed! ✓ ==="
