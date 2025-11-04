"""
Rule engine for FileFlow Manager.

Orchestrates file organization based on rules with priority ordering.
"""

from datetime import datetime
from pathlib import Path
from typing import Callable, List, Optional

from fileflow_core.date_organizer import DateOrganizer
from fileflow_core.duplicate_detector import DuplicateDetector
from fileflow_core.file_operations import FileOperations
from fileflow_core.file_scanner import FileScanner
from fileflow_core.models import (
    DuplicatePair,
    FileMetadata,
    FileOperation,
    OperationType,
    Rule,
    ScanResult,
    SkipReason,
)
from fileflow_storage.cache import ChecksumCache
from fileflow_storage.database import Database


class RuleEngine:
    """Execute file organization rules."""

    def __init__(
        self,
        database: Database,
        cache: ChecksumCache,
        expand_env_vars: Callable[[str], str],
    ):
        """Initialize rule engine with dependencies."""
        self.db = database
        self.cache = cache
        self.expand_env_vars = expand_env_vars
        self.scanner = FileScanner()
        self.duplicate_detector = DuplicateDetector(cache)
        self.file_ops = FileOperations()
        self.date_organizer = DateOrganizer()

    def scan(
        self,
        rules: List[Rule],
        dry_run: bool = True,
        progress_callback: Optional[Callable[[str], None]] = None,
    ) -> ScanResult:
        """
        Scan files and plan operations based on rules.

        Args:
            rules: List of rules to process
            dry_run: If True, only plan operations without executing
            progress_callback: Optional callback for progress updates

        Returns:
            ScanResult with planned operations
        """
        start_time = datetime.now()

        # Filter to only enabled rules, sort by priority
        active_rules = [r for r in rules if r.enabled]
        active_rules.sort(key=lambda r: r.priority)

        # Scan files for each rule
        all_files: List[FileMetadata] = []
        processed_files: set[str] = set()

        for rule in active_rules:
            if progress_callback:
                progress_callback(f"Scanning for rule: {rule.name}")

            # Scan files matching this rule
            matched_files = self.scanner.scan_for_rule(
                rule, self.expand_env_vars, progress_callback
            )

            # Filter out already processed files (higher priority rules processed first)
            for file in matched_files:
                if file.path not in processed_files:
                    all_files.append(file)
                    processed_files.add(file.path)

        # Plan operations
        planned_operations: List[FileOperation] = []

        for file in all_files:
            for rule in active_rules:
                if rule.id in file.matched_rules:
                    # Determine destination
                    destination = self._get_destination(file, rule)

                    # Check if destination already exists
                    dest_path = Path(destination)
                    if dest_path.exists():
                        # Check if it's a duplicate
                        if self.duplicate_detector.find_duplicate_in_destination(
                            file, dest_path
                        ):
                            # It's a duplicate - plan deletion of source
                            operation = FileOperation(
                                timestamp=datetime.now(),
                                operation_type=OperationType.DELETE,
                                source_path=file.path,
                                destination_path=None,
                                file_size=file.size_bytes,
                                checksum=file.checksum or "",
                                rule_id=rule.id,
                                dry_run=dry_run,
                                success=False,
                                duplicate_of=destination,
                            )
                            planned_operations.append(operation)
                        else:
                            # Name conflict - skip
                            operation = FileOperation(
                                timestamp=datetime.now(),
                                operation_type=OperationType.SKIP,
                                source_path=file.path,
                                destination_path=destination,
                                file_size=file.size_bytes,
                                checksum=file.checksum or "",
                                rule_id=rule.id,
                                dry_run=dry_run,
                                success=False,
                                skip_reason=SkipReason.NAME_CONFLICT,
                            )
                            planned_operations.append(operation)
                    else:
                        # Plan move operation
                        operation = FileOperation(
                            timestamp=datetime.now(),
                            operation_type=OperationType.MOVE,
                            source_path=file.path,
                            destination_path=destination,
                            file_size=file.size_bytes,
                            checksum=file.checksum or "",
                            rule_id=rule.id,
                            dry_run=dry_run,
                            success=False,
                        )
                        planned_operations.append(operation)

                    # Only process with first matching rule (highest priority)
                    break

        # Find duplicates
        duplicates = self.duplicate_detector.find_duplicates(all_files)

        # Calculate duration
        duration_ms = int((datetime.now() - start_time).total_seconds() * 1000)

        return ScanResult(
            timestamp=datetime.now(),
            total_files_scanned=len(all_files),
            files_matched=len(all_files),
            planned_operations=planned_operations,
            duplicate_pairs=duplicates,
            large_files=[],  # Not calculated in scan
            old_files=[],  # Not calculated in scan
            scan_duration_ms=duration_ms,
        )

    def execute(
        self,
        operations: List[FileOperation],
        progress_callback: Optional[Callable[[str], None]] = None,
    ) -> List[FileOperation]:
        """
        Execute file operations.

        Args:
            operations: List of operations to execute
            progress_callback: Optional callback for progress updates

        Returns:
            List of executed operations with results
        """
        executed_operations = []

        for operation in operations:
            if progress_callback:
                progress_callback(f"Processing: {Path(operation.source_path).name}")

            # Update to non-dry-run
            operation.dry_run = False

            if operation.operation_type == OperationType.MOVE:
                success, error = self.file_ops.move_file(
                    Path(operation.source_path),
                    Path(operation.destination_path or ""),
                    preserve_metadata=True,
                )
                operation.success = success
                operation.error_message = error

            elif operation.operation_type == OperationType.DELETE:
                success, error = self.file_ops.delete_file(
                    Path(operation.source_path)
                )
                operation.success = success
                operation.error_message = error

            # Log operation
            self.db.log_operation(operation)
            executed_operations.append(operation)

        return executed_operations

    def _get_destination(self, file: FileMetadata, rule: Rule) -> str:
        """Determine destination path for a file based on rule."""
        destination_base = self.expand_env_vars(rule.destination)

        if rule.organize_by_date:
            # Use date-based organization
            dest_path = self.date_organizer.organize_file_by_date(
                Path(file.path), destination_base
            )
            return str(dest_path)
        else:
            # Simple destination
            return str(Path(destination_base) / Path(file.path).name)
