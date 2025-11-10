"""
Rule engine for FileFlow Manager.

Orchestrates file organization based on rules with priority ordering.
"""

import threading
from collections.abc import Callable
from datetime import datetime
from pathlib import Path

from fileflow_core.cache import LRUCache
from fileflow_core.date_organizer import DateOrganizer
from fileflow_core.duplicate_detector import DuplicateDetector
from fileflow_core.file_operations import FileOperations
from fileflow_core.file_scanner import FileScanner
from fileflow_core.models import (
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

    # Class-level cancellation tracking
    _cancelled_operations: set[str] = set()
    _lock = threading.Lock()

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

        # Cache for frequently accessed results
        self._destination_cache = LRUCache(capacity=1000, ttl=300.0)  # 5 minutes TTL
        self._env_var_cache = LRUCache(capacity=100, ttl=60.0)  # 1 minute TTL

    def scan(
        self,
        rules: list[Rule],
        dry_run: bool = True,
        progress_callback: Callable[[str], None] | None = None,
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
        all_files: list[FileMetadata] = []
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
        planned_operations: list[FileOperation] = []

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

    @classmethod
    def cancel_operation(cls, operation_id: str) -> bool:
        """
        Cancel an ongoing operation.

        Args:
            operation_id: The ID of the operation to cancel

        Returns:
            True if the cancellation was registered
        """
        with cls._lock:
            cls._cancelled_operations.add(operation_id)
        return True

    @classmethod
    def is_cancelled(cls, operation_id: str) -> bool:
        """Check if an operation has been cancelled."""
        with cls._lock:
            return operation_id in cls._cancelled_operations

    @classmethod
    def clear_cancellation(cls, operation_id: str):
        """Clear a cancellation flag after operation completes."""
        with cls._lock:
            cls._cancelled_operations.discard(operation_id)

    def execute(
        self,
        operations: list[FileOperation],
        progress_callback: Callable[[str], None] | None = None,
        operation_id: str | None = None,
    ) -> list[FileOperation]:
        """
        Execute file operations with cancellation support.

        Args:
            operations: List of operations to execute
            progress_callback: Optional callback for progress updates
            operation_id: Optional ID for cancellation tracking

        Returns:
            List of executed operations with results
        """
        executed_operations = []

        try:
            for i, operation in enumerate(operations):
                # Check for cancellation
                if operation_id and self.is_cancelled(operation_id):
                    # Mark remaining operations as cancelled
                    for remaining_op in operations[i:]:
                        remaining_op.success = False
                        remaining_op.error_message = "Operation cancelled by user"
                        executed_operations.append(remaining_op)
                    break

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

        finally:
            # Clean up cancellation flag
            if operation_id:
                self.clear_cancellation(operation_id)

        return executed_operations

    def _get_destination(self, file: FileMetadata, rule: Rule) -> str:
        """Determine destination path for a file based on rule (with caching)."""
        # Create cache key from file path and rule ID
        cache_key = f"{file.path}:{rule.id}"

        # Check cache first
        cached_dest = self._destination_cache.get(cache_key)
        if cached_dest is not None:
            return cached_dest

        # Cache environment variable expansion
        env_cache_key = rule.destination
        cached_env = self._env_var_cache.get(env_cache_key)
        if cached_env is not None:
            destination_base = cached_env
        else:
            destination_base = self.expand_env_vars(rule.destination)
            self._env_var_cache.set(env_cache_key, destination_base)

        if rule.organize_by_date:
            # Use date-based organization
            dest_path = self.date_organizer.organize_file_by_date(
                Path(file.path), destination_base
            )
            destination = str(dest_path)
        else:
            # Simple destination
            destination = str(Path(destination_base) / Path(file.path).name)

        # Cache the result
        self._destination_cache.set(cache_key, destination)
        return destination
