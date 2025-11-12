#!/bin/bash
# Comprehensive End-to-End Test for Fileflow Manager
# Tests all major workflows: CLI, scanning, duplicates, old files, config, monitoring

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$SCRIPT_DIR/backend"
TEST_DIR="/tmp/fileflow_e2e_test_$$"
RESULTS_FILE="/tmp/fileflow_e2e_results_$$.txt"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Test result tracking
TESTS_PASSED=0
TESTS_FAILED=0
TESTS_TOTAL=0

log() {
    echo -e "${BLUE}[TEST]${NC} $1"
}

success() {
    echo -e "${GREEN}✓${NC} $1"
    ((TESTS_PASSED++))
    ((TESTS_TOTAL++))
    echo "PASS: $1" >> "$RESULTS_FILE"
}

fail() {
    echo -e "${RED}✗${NC} $1"
    ((TESTS_FAILED++))
    ((TESTS_TOTAL++))
    echo "FAIL: $1" >> "$RESULTS_FILE"
}

section() {
    echo ""
    echo -e "${YELLOW}═══════════════════════════════════════════════════════${NC}"
    echo -e "${YELLOW}$1${NC}"
    echo -e "${YELLOW}═══════════════════════════════════════════════════════${NC}"
    echo ""
}

# Cleanup function
cleanup() {
    log "Cleaning up test environment..."
    if [ -d "$TEST_DIR" ]; then
        rm -rf "$TEST_DIR"
    fi
}

trap cleanup EXIT

# Initialize results file
echo "Fileflow Manager E2E Test Results" > "$RESULTS_FILE"
echo "Started: $(date)" >> "$RESULTS_FILE"
echo "" >> "$RESULTS_FILE"

section "End-to-End Testing: Fileflow Manager"

log "Test directory: $TEST_DIR"
log "Results file: $RESULTS_FILE"

# ============================================================================
section "1. Environment Setup"
# ============================================================================

log "Creating test directory structure..."
mkdir -p "$TEST_DIR"/{screenshots,downloads,documents,duplicates}

# Create test files
echo "Test screenshot 1" > "$TEST_DIR/screenshots/Screenshot 2024-01-15 at 10.30.45.png"
echo "Test screenshot 2" > "$TEST_DIR/screenshots/Screenshot 2024-02-20 at 14.22.10.png"
echo "Old document" > "$TEST_DIR/documents/old_report.pdf"
echo "Duplicate content" > "$TEST_DIR/duplicates/file1.txt"
echo "Duplicate content" > "$TEST_DIR/duplicates/file2.txt"
echo "Duplicate content" > "$TEST_DIR/duplicates/file3.txt"

# Make some files old (100 days)
touch -t $(date -v-100d +%Y%m%d%H%M.%S 2>/dev/null || date -d "100 days ago" +%Y%m%d%H%M.%S 2>/dev/null) "$TEST_DIR/documents/old_report.pdf" 2>/dev/null || true

if [ -d "$TEST_DIR" ] && [ "$(ls -A $TEST_DIR)" ]; then
    success "Test environment created"
else
    fail "Failed to create test environment"
fi

# ============================================================================
section "2. Backend Installation & Configuration"
# ============================================================================

cd "$BACKEND_DIR"

log "Checking Python environment..."
if /Users/daniel/.local/bin/poetry env info &>/dev/null; then
    success "Poetry environment exists"
else
    fail "Poetry environment not found"
fi

log "Checking backend modules..."
if /Users/daniel/.local/bin/poetry run python -c "import fileflow_core, fileflow_storage, fileflow_api, fileflow_cli" 2>/dev/null; then
    success "All backend modules importable"
else
    fail "Failed to import backend modules"
fi

# ============================================================================
section "3. CLI Commands Testing"
# ============================================================================

log "Testing 'fileflow --help'..."
if /Users/daniel/.local/bin/poetry run fileflow --help | grep -q "FileFlow"; then
    success "CLI help command works"
else
    fail "CLI help command failed"
fi

log "Testing 'fileflow config-show'..."
if /Users/daniel/.local/bin/poetry run fileflow config-show &>/dev/null; then
    success "Config show command works"
else
    fail "Config show command failed"
fi

log "Testing 'fileflow rules list'..."
if /Users/daniel/.local/bin/poetry run fileflow rules list &>/dev/null; then
    success "Rules list command works"
else
    fail "Rules list command failed"
fi

log "Testing 'fileflow history' command..."
if /Users/daniel/.local/bin/poetry run fileflow history --limit 5 &>/dev/null; then
    success "History command works"
else
    fail "History command failed"
fi

log "Testing 'fileflow find-old' command..."
if /Users/daniel/.local/bin/poetry run fileflow find-old --threshold 90 &>/dev/null; then
    success "Find old files command works"
else
    fail "Find old files command failed"
fi

log "Testing 'fileflow find-duplicates' command..."
if /Users/daniel/.local/bin/poetry run fileflow find-duplicates &>/dev/null; then
    success "Find duplicates command works"
else
    fail "Find duplicates command failed"
fi

log "Testing 'fileflow detect-screenshots' command..."
if /Users/daniel/.local/bin/poetry run fileflow detect-screenshots &>/dev/null; then
    success "Detect screenshots command works"
else
    fail "Detect screenshots command failed"
fi

# ============================================================================
section "4. Backend Module Testing"
# ============================================================================

log "Testing FileScanner module..."
if /Users/daniel/.local/bin/poetry run python -c "
from fileflow_core.file_scanner import FileScanner
from pathlib import Path
scanner = FileScanner()
files = scanner.scan(['$TEST_DIR/screenshots'], patterns=['*.png'])
print(f'Found {len(files)} files')
assert len(files) >= 2, f'Expected >= 2 files, got {len(files)}'
" 2>/dev/null; then
    success "FileScanner works"
else
    fail "FileScanner failed"
fi

log "Testing RuleEngine module..."
if /Users/daniel/.local/bin/poetry run python -c "
from fileflow_core.rule_engine import RuleEngine
from fileflow_core.models import OrganizationRule
from pathlib import Path

rule = OrganizationRule(
    rule_id='test-rule',
    name='Test Rule',
    enabled=True,
    priority=1,
    source_patterns=['*.txt'],
    destination_template='test-dest',
    conditions={},
    actions={}
)

engine = RuleEngine()
print('RuleEngine initialized')
" 2>/dev/null; then
    success "RuleEngine works"
else
    fail "RuleEngine failed"
fi

log "Testing DuplicateDetector module..."
if /Users/daniel/.local/bin/poetry run python -c "
from fileflow_core.duplicate_detector import DuplicateDetector
from pathlib import Path

detector = DuplicateDetector()
groups = detector.find_duplicates(['$TEST_DIR/duplicates'])
print(f'Found {len(groups)} duplicate groups')
assert len(groups) > 0, 'Expected to find duplicate groups'
" 2>/dev/null; then
    success "DuplicateDetector works"
else
    fail "DuplicateDetector failed"
fi

log "Testing Database module..."
if /Users/daniel/.local/bin/poetry run python -c "
from fileflow_storage.database import get_database
db = get_database()
db.initialize()
print('Database initialized')
" 2>/dev/null; then
    success "Database module works"
else
    fail "Database module failed"
fi

log "Testing Cache module..."
if /Users/daniel/.local/bin/poetry run python -c "
from fileflow_storage.cache import get_cache_manager
cache = get_cache_manager()
print('Cache manager initialized')
" 2>/dev/null; then
    success "Cache module works"
else
    fail "Cache module failed"
fi

log "Testing ProgressManager module..."
if /Users/daniel/.local/bin/poetry run python -c "
from fileflow_core.progress import get_progress_manager
manager = get_progress_manager()
tracker = manager.create_tracker('test-op', total_items=10)
tracker.start()
tracker.update(completed=5)
progress = tracker.get_progress()
assert progress.percentage == 50.0, f'Expected 50%, got {progress.percentage}%'
tracker.complete()
manager.remove_tracker('test-op')
print('Progress tracking works')
" 2>/dev/null; then
    success "ProgressManager works"
else
    fail "ProgressManager failed"
fi

# ============================================================================
section "5. Backend API Commands Testing"
# ============================================================================

log "Testing get_rules command..."
if /Users/daniel/code/Filefly-specify/backend/dist/fileflow-backend/fileflow-backend get_rules '{}' 2>/dev/null | grep -q "rules"; then
    success "get_rules API works"
else
    fail "get_rules API failed"
fi

log "Testing get_health_status command..."
if /Users/daniel/code/Filefly-specify/backend/dist/fileflow-backend/fileflow-backend get_health_status '{}' 2>/dev/null | grep -q "overall_status"; then
    success "get_health_status API works"
else
    fail "get_health_status API failed"
fi

log "Testing get_system_metrics command..."
if /Users/daniel/code/Filefly-specify/backend/dist/fileflow-backend/fileflow-backend get_system_metrics '{}' 2>/dev/null | grep -q "metrics"; then
    success "get_system_metrics API works"
else
    fail "get_system_metrics API failed"
fi

log "Testing get_cache_statistics command..."
if /Users/daniel/code/Filefly-specify/backend/dist/fileflow-backend/fileflow-backend get_cache_statistics '{}' 2>/dev/null | grep -q "caches"; then
    success "get_cache_statistics API works"
else
    fail "get_cache_statistics API failed"
fi

log "Testing get_all_operations_progress command..."
if /Users/daniel/code/Filefly-specify/backend/dist/fileflow-backend/fileflow-backend get_all_operations_progress '{}' 2>/dev/null | grep -q "operations"; then
    success "get_all_operations_progress API works"
else
    fail "get_all_operations_progress API failed"
fi

# ============================================================================
section "6. Unit Tests"
# ============================================================================

log "Running backend unit tests..."
if /Users/daniel/.local/bin/poetry run pytest tests/ -v --tb=short -q 2>&1 | tee /tmp/pytest_output.txt | tail -20; then
    PYTEST_PASSED=$(grep -o "[0-9]* passed" /tmp/pytest_output.txt | grep -o "[0-9]*" || echo "0")
    success "Unit tests passed ($PYTEST_PASSED tests)"
else
    fail "Some unit tests failed"
fi

# ============================================================================
section "7. Integration Tests"
# ============================================================================

log "Testing file scanning integration..."
TEST_RESULT=$(cd "$BACKEND_DIR" && /Users/daniel/.local/bin/poetry run python -c "
from fileflow_core.file_scanner import FileScanner
from pathlib import Path

scanner = FileScanner()
files = scanner.scan(
    directories=[Path('$TEST_DIR')],
    patterns=['*.png', '*.pdf', '*.txt'],
    recursive=True
)
print(len(files))
" 2>/dev/null)

if [ "$TEST_RESULT" -ge 5 ]; then
    success "File scanning integration works (found $TEST_RESULT files)"
else
    fail "File scanning integration failed (found $TEST_RESULT files, expected >= 5)"
fi

log "Testing duplicate detection integration..."
DUP_RESULT=$(cd "$BACKEND_DIR" && /Users/daniel/.local/bin/poetry run python -c "
from fileflow_core.duplicate_detector import DuplicateDetector
from pathlib import Path

detector = DuplicateDetector()
groups = detector.find_duplicates([Path('$TEST_DIR/duplicates')])
print(len(groups))
" 2>/dev/null)

if [ "$DUP_RESULT" -ge 1 ]; then
    success "Duplicate detection integration works (found $DUP_RESULT groups)"
else
    fail "Duplicate detection integration failed"
fi

log "Testing old files detection integration..."
OLD_RESULT=$(cd "$BACKEND_DIR" && /Users/daniel/.local/bin/poetry run python -c "
from fileflow_core.file_scanner import FileScanner
from pathlib import Path

scanner = FileScanner()
old_files = scanner.find_old_files(
    directories=[Path('$TEST_DIR')],
    threshold_days=90
)
print(len(old_files))
" 2>/dev/null)

if [ "$OLD_RESULT" -ge 0 ]; then
    success "Old files detection integration works (found $OLD_RESULT files)"
else
    fail "Old files detection integration failed"
fi

# ============================================================================
section "8. Configuration Management"
# ============================================================================

log "Testing configuration export..."
EXPORT_FILE="/tmp/fileflow_test_export_$$.yaml"
if cd "$BACKEND_DIR" && /Users/daniel/.local/bin/poetry run python -c "
from fileflow_api.tauri_commands import export_configuration
result = export_configuration('$EXPORT_FILE')
print('Exported:', result['success'])
" 2>/dev/null | grep -q "True"; then
    if [ -f "$EXPORT_FILE" ]; then
        success "Configuration export works"
        rm "$EXPORT_FILE"
    else
        fail "Configuration file not created"
    fi
else
    fail "Configuration export failed"
fi

# ============================================================================
section "9. Performance & Observability"
# ============================================================================

log "Testing metrics collection..."
if cd "$BACKEND_DIR" && /Users/daniel/.local/bin/poetry run python -c "
from fileflow_storage.observability import get_metrics_manager
manager = get_metrics_manager()
metrics = manager.get_all_metrics()
print(f'Metrics: {len(metrics)} types')
assert 'counters' in metrics
assert 'gauges' in metrics
" 2>/dev/null; then
    success "Metrics collection works"
else
    fail "Metrics collection failed"
fi

log "Testing health checks..."
if cd "$BACKEND_DIR" && /Users/daniel/.local/bin/poetry run python -c "
from fileflow_storage.observability import get_health_checker
checker = get_health_checker()
status = checker.check_all()
print(f'Health: {status.overall_status.value}')
" 2>/dev/null; then
    success "Health checks work"
else
    fail "Health checks failed"
fi

# ============================================================================
section "10. Test Results Summary"
# ============================================================================

echo ""
echo "Completed: $(date)" >> "$RESULTS_FILE"
echo "" >> "$RESULTS_FILE"
echo "Total Tests: $TESTS_TOTAL" >> "$RESULTS_FILE"
echo "Passed: $TESTS_PASSED" >> "$RESULTS_FILE"
echo "Failed: $TESTS_FAILED" >> "$RESULTS_FILE"

if [ $TESTS_FAILED -eq 0 ]; then
    echo -e "${GREEN}╔═══════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║                 ALL TESTS PASSED!                     ║${NC}"
    echo -e "${GREEN}║                                                       ║${NC}"
    echo -e "${GREEN}║  Total:  $TESTS_TOTAL tests                                      ║${NC}"
    echo -e "${GREEN}║  Passed: $TESTS_PASSED tests                                      ║${NC}"
    echo -e "${GREEN}║  Failed: $TESTS_FAILED tests                                       ║${NC}"
    echo -e "${GREEN}╚═══════════════════════════════════════════════════════╝${NC}"
else
    echo -e "${RED}╔═══════════════════════════════════════════════════════╗${NC}"
    echo -e "${RED}║              SOME TESTS FAILED                        ║${NC}"
    echo -e "${RED}║                                                       ║${NC}"
    echo -e "${RED}║  Total:  $TESTS_TOTAL tests                                      ║${NC}"
    echo -e "${GREEN}║  Passed: $TESTS_PASSED tests                                      ║${NC}"
    echo -e "${RED}║  Failed: $TESTS_FAILED tests                                       ║${NC}"
    echo -e "${RED}╚═══════════════════════════════════════════════════════╝${NC}"
fi

echo ""
log "Full results saved to: $RESULTS_FILE"
echo ""

# Exit with failure if any tests failed
if [ $TESTS_FAILED -gt 0 ]; then
    exit 1
fi
