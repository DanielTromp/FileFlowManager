"""
Tauri IPC command handlers for FileFlow Manager.

This module provides the bridge between the Tauri frontend and Python backend.
Commands are invoked from the Svelte frontend via Tauri's invoke() API.
"""

import json
import os
import sys
import time
from pathlib import Path
from typing import Any

from fileflow_config.config_manager import ConfigManager
from fileflow_config.defaults import create_default_config_file
from fileflow_core.logging_config import get_logger, setup_logging
from fileflow_core.rule_engine import RuleEngine
from fileflow_storage.cache import ChecksumCache
from fileflow_storage.database import Database

# Setup logging
logger = get_logger("tauri_commands")


# Error codes from contracts/tauri-ipc.md (T137)
class CommandError(Exception):
    """
    Structured error for Tauri IPC commands.

    Attributes:
        code: Machine-readable error code
        message: Human-readable error message
        details: Optional additional context
    """

    def __init__(self, code: str, message: str, details: Any = None):
        self.code = code
        self.message = message
        self.details = details
        super().__init__(message)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        result = {
            "code": self.code,
            "message": self.message,
        }
        if self.details is not None:
            result["details"] = self.details
        return result

# Default paths
DEFAULT_CONFIG_PATH = Path.home() / ".config" / "fileflow" / "fileflow.toml"
DEFAULT_DB_PATH = Path.home() / ".config" / "fileflow" / "fileflow.db"


def get_config_manager() -> ConfigManager:
    """Get configuration manager with default config creation."""
    if not DEFAULT_CONFIG_PATH.exists():
        logger.info("Creating default configuration")
        create_default_config_file(str(DEFAULT_CONFIG_PATH))

    return ConfigManager(DEFAULT_CONFIG_PATH)


def get_database() -> Database:
    """Get database instance."""
    return Database(DEFAULT_DB_PATH)


def scan_files(dry_run: bool = True, rule_ids: list[str] | None = None) -> dict[str, Any]:
    """
    Scan files according to active rules.

    Args:
        dry_run: If True, only preview operations without executing
        rule_ids: Optional list of specific rule IDs to scan

    Returns:
        ScanResult as dictionary

    Raises:
        CommandError: With appropriate error code (T137)
    """
    try:
        logger.info(f"Starting scan: dry_run={dry_run}, rule_ids={rule_ids}")

        # Setup
        config_mgr = get_config_manager()
        try:
            config = config_mgr.load()
        except Exception as e:
            raise CommandError(
                "CONFIG_INVALID",
                "Configuration is invalid or cannot be loaded",
                {"original_error": str(e)}
            )

        db = get_database()
        cache = ChecksumCache(db)
        engine = RuleEngine(db, cache, config_mgr.expand_env_vars)

        # Validate rule_ids if specified
        if rule_ids:
            invalid_ids = [rid for rid in rule_ids if not any(r.id == rid for r in config.rules)]
            if invalid_ids:
                raise CommandError(
                    "INVALID_RULE_ID",
                    f"Specified rule IDs don't exist: {', '.join(invalid_ids)}",
                    {"invalid_ids": invalid_ids}
                )
            rule_list = [r for r in config.rules if r.id in rule_ids]
        else:
            rule_list = config.rules

        # Check source directory permissions
        for rule in rule_list:
            for source_dir in rule.source_directories:
                expanded_dir = Path(config_mgr.expand_env_vars(source_dir))
                if not os.access(expanded_dir, os.R_OK):
                    raise CommandError(
                        "PERMISSION_DENIED",
                        f"Cannot read source directory: {expanded_dir}",
                        {"directory": str(expanded_dir), "rule_id": rule.id}
                    )

        # Run scan
        result = engine.scan(rule_list, dry_run=dry_run)

        # If not dry run, execute the operations
        if not dry_run and result.planned_operations:
            logger.info(f"Executing {len(result.planned_operations)} operations")
            import uuid
            operation_id = str(uuid.uuid4())
            start_time = time.time()
            total_operations = len(result.planned_operations)

            # Progress tracking for long operations
            executed_ops = []
            for i, op in enumerate(result.planned_operations):
                elapsed = time.time() - start_time
                if elapsed > 5:  # Emit progress after 5 seconds
                    progress_data = {
                        "type": "scan_execution_progress",
                        "operation_id": operation_id,
                        "message": f"Executing: {Path(op.source_path).name}",
                        "current": i + 1,
                        "total": total_operations,
                        "elapsed_seconds": elapsed
                    }
                    print(f"PROGRESS:{json.dumps(progress_data)}", file=sys.stderr)

                executed_op = engine.execute([op], operation_id=operation_id)[0]
                executed_ops.append(executed_op)

            # Update result with executed operations
            result.planned_operations = executed_ops

        # Convert to dict for JSON serialization
        result_dict = result.model_dump(mode="json")

        logger.info(
            f"Scan complete: {result.files_matched} files matched, "
            f"{len(result.planned_operations)} operations {'executed' if not dry_run else 'planned'}"
        )

        return result_dict

    except CommandError:
        raise
    except Exception as e:
        logger.error(f"Scan failed: {e}", exc_info=True)
        raise CommandError(
            "SCAN_FAILED",
            f"Scan operation failed: {str(e)}",
            {"original_error": str(e), "type": type(e).__name__}
        )


def execute_operations(
    operation_ids: list[str], confirm_deletions: bool = False
) -> dict[str, Any]:
    """
    Execute specific file operations from a previous scan.

    Args:
        operation_ids: List of operation IDs to execute
        confirm_deletions: Must be True to execute delete operations

    Returns:
        ExecutionResult as dictionary

    Raises:
        CommandError: With appropriate error code (T137)
    """
    try:
        logger.info(f"Executing {len(operation_ids)} operations")

        # Setup
        config_mgr = get_config_manager()
        db = get_database()
        cache = ChecksumCache(db)
        engine = RuleEngine(db, cache, config_mgr.expand_env_vars)

        # For simplicity, re-scan to get operations
        # In production, we'd cache the scan result
        config = config_mgr.load()
        scan_result = engine.scan(config.rules, dry_run=True)

        # Filter to requested operations
        operations_to_execute = [
            op for op in scan_result.planned_operations if op.id in operation_ids
        ]

        # Validate all operation IDs exist
        found_ids = {op.id for op in operations_to_execute}
        invalid_ids = set(operation_ids) - found_ids
        if invalid_ids:
            raise CommandError(
                "INVALID_OPERATION_ID",
                f"Operation IDs not found: {', '.join(invalid_ids)}",
                {"invalid_ids": list(invalid_ids)}
            )

        # Check for delete operations and confirmation (T137)
        has_deletions = any(
            op.operation_type.value == "delete" for op in operations_to_execute
        )
        if has_deletions and not confirm_deletions:
            raise CommandError(
                "DELETION_NOT_CONFIRMED",
                "Delete operations require confirm_deletions=True",
                {"deletion_count": sum(1 for op in operations_to_execute if op.operation_type.value == "delete")}
            )

        # Disk space validation for move operations (T140)
        move_ops = [op for op in operations_to_execute if op.operation_type.value == "move"]
        if move_ops:
            total_size = sum(op.file_size for op in move_ops if op.file_size)
            # Get destination directories and check space
            dest_dirs = {Path(op.destination_path).parent for op in move_ops if op.destination_path}
            for dest_dir in dest_dirs:
                if dest_dir.exists():
                    stat = os.statvfs(dest_dir)
                    free_space = stat.f_bavail * stat.f_frsize
                    # Require 10% buffer beyond total file size
                    required_space = total_size * 1.1
                    if free_space < required_space:
                        raise CommandError(
                            "DISK_SPACE_INSUFFICIENT",
                            f"Insufficient disk space on {dest_dir}",
                            {
                                "required_mb": required_space / (1024 * 1024),
                                "available_mb": free_space / (1024 * 1024),
                                "destination": str(dest_dir)
                            }
                        )

        # Generate operation ID for cancellation tracking
        import time
        import uuid
        operation_id = str(uuid.uuid4())

        # Track progress for long operations
        start_time = time.time()
        total_operations = len(operations_to_execute)

        def progress_callback(message: str, current: int = None):
            """Emit progress events for long-running operations."""
            elapsed = time.time() - start_time
            if elapsed > 5:  # Only emit events after 5 seconds
                progress_data = {
                    "type": "operation_progress",
                    "operation_id": operation_id,
                    "message": message,
                    "current": current,
                    "total": total_operations,
                    "elapsed_seconds": elapsed
                }
                # Print to stderr so it doesn't interfere with stdout result
                print(f"PROGRESS:{json.dumps(progress_data)}", file=sys.stderr)

        # Execute operations with cancellation and progress support
        executed = []
        for i, op in enumerate(operations_to_execute):
            if operation_id and engine.is_cancelled(operation_id):
                # Mark remaining as cancelled
                for remaining_op in operations_to_execute[i:]:
                    remaining_op.success = False
                    remaining_op.error_message = "Operation cancelled by user"
                    executed.append(remaining_op)
                break

            progress_callback(f"Processing: {Path(op.source_path).name}", i + 1)
            executed_op = engine.execute([op], operation_id=operation_id)[0]
            executed.append(executed_op)

        # Build result
        success_count = sum(1 for op in executed if op.success)
        failed_count = len(executed) - success_count

        result = {
            "execution_id": scan_result.scan_id,
            "timestamp": scan_result.timestamp.isoformat(),
            "total_operations": len(executed),
            "successful_operations": success_count,
            "failed_operations": failed_count,
            "skipped_operations": 0,
            "results": [
                {
                    "operation_id": op.id,
                    "success": op.success,
                    "error_message": op.error_message,
                }
                for op in executed
            ],
            "duration_ms": scan_result.scan_duration_ms,
        }

        logger.info(
            f"Execution complete: {success_count} succeeded, {failed_count} failed"
        )

        return result

    except CommandError:
        raise
    except Exception as e:
        logger.error(f"Execution failed: {e}", exc_info=True)
        raise CommandError(
            "EXECUTION_FAILED",
            f"Execution operation failed: {str(e)}",
            {"original_error": str(e), "type": type(e).__name__}
        )


def cancel_operation(operation_id: str) -> dict[str, Any]:
    """
    Cancel an ongoing operation.

    Args:
        operation_id: The ID of the operation to cancel

    Returns:
        Success status

    Raises:
        CommandError: If cancellation fails
    """
    try:
        from fileflow_core.rule_engine import RuleEngine

        # Register the cancellation
        success = RuleEngine.cancel_operation(operation_id)

        logger.info(f"Cancellation requested for operation {operation_id}")

        return {
            "success": success,
            "operation_id": operation_id,
            "message": "Cancellation requested successfully"
        }

    except Exception as e:
        logger.error(f"Failed to cancel operation {operation_id}: {e}", exc_info=True)
        raise CommandError(
            "CANCEL_FAILED",
            f"Failed to cancel operation: {str(e)}",
            {"operation_id": operation_id, "error": str(e)}
        )


def get_rules() -> list[dict[str, Any]]:
    """
    Get all configured rules.

    Raises:
        CommandError: With appropriate error code (T137)
    """
    try:
        config_mgr = get_config_manager()
        config = config_mgr.load()

        return [rule.model_dump(mode="json") for rule in config.rules]

    except Exception as e:
        logger.error(f"Failed to get rules: {e}", exc_info=True)
        raise CommandError(
            "CONFIG_READ_FAILED",
            "Cannot read configuration",
            {"original_error": str(e)}
        )


def get_configuration() -> dict[str, Any]:
    """
    Get current configuration.

    Raises:
        CommandError: With appropriate error code (T137)
    """
    try:
        config_mgr = get_config_manager()
        config = config_mgr.load()

        return config.model_dump(mode="json")

    except Exception as e:
        logger.error(f"Failed to get configuration: {e}", exc_info=True)
        raise CommandError(
            "CONFIG_READ_FAILED",
            "Cannot read configuration",
            {"original_error": str(e)}
        )


def export_configuration(destination_path: str) -> dict[str, Any]:
    """
    Export configuration to file (T127).

    Args:
        destination_path: Path to export configuration to

    Returns:
        Success message

    Raises:
        CommandError: With appropriate error code (T137)
    """
    try:
        # Check write permission
        dest_path = Path(destination_path)
        dest_dir = dest_path.parent
        if dest_dir.exists() and not os.access(dest_dir, os.W_OK):
            raise CommandError(
                "PERMISSION_DENIED",
                f"No write access to destination directory: {dest_dir}",
                {"destination": str(dest_dir)}
            )

        config_mgr = get_config_manager()
        config_mgr.export(destination_path)

        logger.info(f"Configuration exported to: {destination_path}")
        return {"success": True, "message": f"Configuration exported to {destination_path}"}

    except CommandError:
        raise
    except Exception as e:
        logger.error(f"Failed to export configuration: {e}", exc_info=True)
        raise CommandError(
            "EXPORT_FAILED",
            f"Cannot write to destination: {str(e)}",
            {"destination": destination_path, "original_error": str(e)}
        )


def import_configuration(
    source_path: str,
    merge: bool = False
) -> dict[str, Any]:
    """
    Import configuration from file (T128).

    Args:
        source_path: Path to import configuration from
        merge: If True, merge with existing config. If False, replace entirely.

    Returns:
        Success message

    Raises:
        CommandError: With appropriate error code (T137)
    """
    try:
        # Check file exists
        if not Path(source_path).exists():
            raise CommandError(
                "FILE_NOT_FOUND",
                f"Source file doesn't exist: {source_path}",
                {"source": source_path}
            )

        config_mgr = get_config_manager()
        try:
            config_mgr.import_config(source_path, merge=merge)
        except ValueError as e:
            raise CommandError(
                "VALIDATION_FAILED",
                f"Invalid configuration: {str(e)}",
                {"source": source_path, "validation_error": str(e)}
            )

        mode = "merged" if merge else "replaced"
        logger.info(f"Configuration {mode} from: {source_path}")
        return {"success": True, "message": f"Configuration {mode} successfully"}

    except CommandError:
        raise
    except Exception as e:
        logger.error(f"Failed to import configuration: {e}", exc_info=True)
        raise CommandError(
            "IMPORT_FAILED",
            f"Cannot read source file: {str(e)}",
            {"source": source_path, "original_error": str(e)}
        )


def detect_screenshot_location() -> str:
    """Auto-detect macOS screenshot location."""
    try:
        import subprocess

        result = subprocess.run(
            ["defaults", "read", "com.apple.screencapture", "location"],
            capture_output=True,
            text=True,
        )

        if result.returncode == 0:
            location = result.stdout.strip()
            logger.info(f"Detected screenshot location: {location}")
            return location
        else:
            # Default location
            default = str(Path.home() / "Desktop")
            logger.info(f"Using default screenshot location: {default}")
            return default

    except Exception as e:
        logger.error(f"Failed to detect screenshot location: {e}")
        return str(Path.home() / "Desktop")


def get_operation_history(
    limit: int = 100,
    offset: int = 0,
    operation_type: str | None = None,
    rule_id: str | None = None,
    include_dry_runs: bool = False,
) -> list[dict[str, Any]]:
    """
    Retrieve operation history from database.

    Args:
        limit: Maximum number of operations to return
        offset: Number of operations to skip (for pagination)
        operation_type: Filter by operation type (move, delete, etc.)
        rule_id: Filter by rule ID
        include_dry_runs: Include dry-run operations in results

    Returns:
        List of FileOperation dictionaries

    Raises:
        CommandError: With appropriate error code (T137)
    """
    try:
        db = get_database()

        # Convert string operation_type to OperationType if provided
        from fileflow_core.models import OperationType

        op_type = OperationType(operation_type) if operation_type else None

        operations = db.get_operation_history(
            limit=limit,
            offset=offset,
            operation_type=op_type,
            rule_id=rule_id,
            include_dry_runs=include_dry_runs,
        )

        logger.info(f"Retrieved {len(operations)} operations from history")

        return [op.model_dump(mode="json") for op in operations]

    except Exception as e:
        logger.error(f"Failed to get operation history: {e}", exc_info=True)
        raise CommandError(
            "DATABASE_ERROR",
            f"Failed to query database: {str(e)}",
            {"original_error": str(e)}
        )


def create_rule(rule_data: dict[str, Any]) -> dict[str, Any]:
    """
    Create a new rule.

    Args:
        rule_data: Rule configuration dictionary

    Returns:
        Created rule as dictionary

    Raises:
        CommandError: With appropriate error code (T137)
    """
    try:
        from fileflow_config.rule_schema import RuleValidator
        from fileflow_core.models import Rule

        config_mgr = get_config_manager()
        config = config_mgr.load()

        # Generate rule ID if not provided
        if 'id' not in rule_data:
            rule_data['id'] = RuleValidator.sanitize_rule_id(rule_data['name'])

        # Check if rule ID already exists
        if any(r.id == rule_data['id'] for r in config.rules):
            raise CommandError(
                "DUPLICATE_RULE_NAME",
                f"Rule with ID '{rule_data['id']}' already exists",
                {"rule_id": rule_data['id']}
            )

        # Create rule from data
        try:
            new_rule = Rule(**rule_data)
        except Exception as e:
            raise CommandError(
                "VALIDATION_FAILED",
                f"Invalid rule data: {str(e)}",
                {"validation_error": str(e)}
            )

        # Validate rule
        valid, errors = RuleValidator.validate_rule(new_rule, check_filesystem=True)
        if not valid:
            raise CommandError(
                "VALIDATION_FAILED",
                f"Rule validation failed: {'; '.join(errors)}",
                {"validation_errors": errors}
            )

        # Add to configuration
        config.rules.append(new_rule)
        try:
            config_mgr.save(config)
        except Exception as e:
            raise CommandError(
                "CONFIG_WRITE_FAILED",
                "Cannot write to configuration file",
                {"original_error": str(e)}
            )

        logger.info(f"Created rule: {new_rule.name} ({new_rule.id})")
        return new_rule.model_dump(mode="json")

    except CommandError:
        raise
    except Exception as e:
        logger.error(f"Failed to create rule: {e}", exc_info=True)
        raise CommandError(
            "VALIDATION_FAILED",
            f"Failed to create rule: {str(e)}",
            {"original_error": str(e)}
        )


def update_rule(rule_id: str, rule_data: dict[str, Any]) -> dict[str, Any]:
    """
    Update an existing rule.

    Args:
        rule_id: ID of rule to update
        rule_data: Updated rule configuration

    Returns:
        Updated rule as dictionary

    Raises:
        CommandError: With appropriate error code (T137)
    """
    try:
        from fileflow_config.rule_schema import RuleValidator

        config_mgr = get_config_manager()
        config = config_mgr.load()

        # Find rule
        rule = next((r for r in config.rules if r.id == rule_id), None)
        if not rule:
            raise CommandError(
                "RULE_NOT_FOUND",
                f"Rule '{rule_id}' not found",
                {"rule_id": rule_id}
            )

        # Update fields
        for key, value in rule_data.items():
            if hasattr(rule, key):
                setattr(rule, key, value)

        # Validate updated rule
        valid, errors = RuleValidator.validate_rule(rule, check_filesystem=True)
        if not valid:
            raise CommandError(
                "VALIDATION_FAILED",
                f"Rule validation failed: {'; '.join(errors)}",
                {"validation_errors": errors}
            )

        # Save configuration
        try:
            config_mgr.save(config)
        except Exception as e:
            raise CommandError(
                "CONFIG_WRITE_FAILED",
                "Cannot write to configuration file",
                {"original_error": str(e)}
            )

        logger.info(f"Updated rule: {rule.name} ({rule.id})")
        return rule.model_dump(mode="json")

    except CommandError:
        raise
    except Exception as e:
        logger.error(f"Failed to update rule: {e}", exc_info=True)
        raise CommandError(
            "VALIDATION_FAILED",
            f"Failed to update rule: {str(e)}",
            {"original_error": str(e)}
        )


def delete_rule(rule_id: str) -> dict[str, Any]:
    """
    Delete a rule.

    Args:
        rule_id: ID of rule to delete

    Returns:
        Success message

    Raises:
        CommandError: With appropriate error code (T137)
    """
    try:
        config_mgr = get_config_manager()
        config = config_mgr.load()

        # Find rule
        rule = next((r for r in config.rules if r.id == rule_id), None)
        if not rule:
            raise CommandError(
                "RULE_NOT_FOUND",
                f"Rule '{rule_id}' not found",
                {"rule_id": rule_id}
            )

        rule_name = rule.name

        # Remove rule
        config.rules = [r for r in config.rules if r.id != rule_id]
        try:
            config_mgr.save(config)
        except Exception as e:
            raise CommandError(
                "CONFIG_WRITE_FAILED",
                "Cannot write to configuration file",
                {"original_error": str(e)}
            )

        logger.info(f"Deleted rule: {rule_name} ({rule_id})")
        return {"success": True, "message": f"Rule '{rule_name}' deleted"}

    except CommandError:
        raise
    except Exception as e:
        logger.error(f"Failed to delete rule: {e}", exc_info=True)
        raise CommandError(
            "CONFIG_WRITE_FAILED",
            f"Failed to delete rule: {str(e)}",
            {"original_error": str(e)}
        )


def toggle_rule(rule_id: str, enabled: bool) -> dict[str, Any]:
    """
    Enable or disable a rule.

    Args:
        rule_id: ID of rule to toggle
        enabled: True to enable, False to disable

    Returns:
        Updated rule as dictionary

    Raises:
        CommandError: With appropriate error code (T137)
    """
    try:
        config_mgr = get_config_manager()
        config = config_mgr.load()

        # Find rule
        rule = next((r for r in config.rules if r.id == rule_id), None)
        if not rule:
            raise CommandError(
                "RULE_NOT_FOUND",
                f"Rule '{rule_id}' not found",
                {"rule_id": rule_id}
            )

        # Toggle enabled state
        rule.enabled = enabled
        try:
            config_mgr.save(config)
        except Exception as e:
            raise CommandError(
                "CONFIG_WRITE_FAILED",
                "Cannot write to configuration file",
                {"original_error": str(e)}
            )

        action = "enabled" if enabled else "disabled"
        logger.info(f"Rule '{rule.name}' ({rule.id}) {action}")
        return rule.model_dump(mode="json")

    except CommandError:
        raise
    except Exception as e:
        logger.error(f"Failed to toggle rule: {e}", exc_info=True)
        raise CommandError(
            "CONFIG_WRITE_FAILED",
            f"Failed to toggle rule: {str(e)}",
            {"original_error": str(e)}
        )


def get_large_files(
    threshold_mb: int = 100,
    limit: int | None = None,
) -> list[dict[str, Any]]:
    """
    Find files larger than threshold.

    Args:
        threshold_mb: Size threshold in MB (default: 100)
        limit: Maximum number of files to return

    Returns:
        List of FileMetadata dictionaries sorted by size (largest first)

    Raises:
        CommandError: With appropriate error code (T137)
    """
    try:
        from fileflow_core.file_scanner import FileScanner

        # Validate threshold
        if threshold_mb <= 0:
            raise CommandError(
                "INVALID_THRESHOLD",
                "Threshold must be greater than 0",
                {"threshold_mb": threshold_mb}
            )

        config_mgr = get_config_manager()
        config = config_mgr.load()

        # Get monitored directories
        monitored_dirs = [Path(config_mgr.expand_env_vars(d)) for d in config.paths.monitored_directories]

        # Scan for large files
        scanner = FileScanner()
        large_files = scanner.find_large_files(
            directories=monitored_dirs,
            threshold_mb=threshold_mb,
        )

        # Apply limit if specified
        if limit and limit > 0:
            large_files = large_files[:limit]

        logger.info(
            f"Found {len(large_files)} files larger than {threshold_mb} MB"
        )

        return [file.model_dump(mode="json") for file in large_files]

    except CommandError:
        raise
    except Exception as e:
        logger.error(f"Failed to get large files: {e}", exc_info=True)
        raise CommandError(
            "SCAN_FAILED",
            f"Failed to scan directories: {str(e)}",
            {"original_error": str(e)}
        )


def get_old_files(
    threshold_days: int = 90,
    file_types: list[str] | None = None,
    limit: int | None = None,
) -> list[dict[str, Any]]:
    """
    Find files older than threshold.

    Args:
        threshold_days: Age threshold in days (default: 90)
        file_types: Optional list of file extensions to filter by
        limit: Maximum number of files to return

    Returns:
        List of FileMetadata dictionaries sorted by age (oldest first)

    Raises:
        CommandError: With appropriate error code (T137)
    """
    try:
        from fileflow_core.file_scanner import FileScanner

        # Validate threshold
        if threshold_days <= 0:
            raise CommandError(
                "INVALID_THRESHOLD",
                "Threshold must be greater than 0",
                {"threshold_days": threshold_days}
            )

        config_mgr = get_config_manager()
        config = config_mgr.load()

        # Get monitored directories (T107)
        monitored_dirs = [Path(config_mgr.expand_env_vars(d)) for d in config.paths.monitored_directories]

        # Scan for old files (T107)
        scanner = FileScanner()
        old_files = scanner.find_old_files(
            directories=monitored_dirs,
            threshold_days=threshold_days,
            file_types=file_types,
        )

        # Apply limit if specified
        if limit and limit > 0:
            old_files = old_files[:limit]

        logger.info(
            f"Found {len(old_files)} files older than {threshold_days} days"
        )

        return [file.model_dump(mode="json") for file in old_files]

    except CommandError:
        raise
    except Exception as e:
        logger.error(f"Failed to get old files: {e}", exc_info=True)
        raise CommandError(
            "SCAN_FAILED",
            f"Failed to scan directories: {str(e)}",
            {"original_error": str(e)}
        )


def delete_files(
    file_paths: list[str],
    confirm_deletions: bool = True,
) -> dict[str, Any]:
    """
    Delete multiple files with confirmation.

    Args:
        file_paths: List of file paths to delete
        confirm_deletions: Must be True to execute deletions

    Returns:
        Dictionary with deletion results (deleted_count, failed_count, errors, space_freed_mb)

    Raises:
        CommandError: With appropriate error code (T137)
    """
    try:
        from fileflow_core.file_operations import FileOperations

        # Validate file_paths not empty
        if not file_paths:
            raise CommandError(
                "NO_FILES_SPECIFIED",
                "file_paths is empty",
                {"file_paths": file_paths}
            )

        # Validate confirmation
        if not confirm_deletions:
            raise CommandError(
                "DELETION_NOT_CONFIRMED",
                "Deletions require confirm_deletions=True",
                {"file_count": len(file_paths)}
            )

        # Convert to Path objects
        paths = [Path(p) for p in file_paths]

        # Perform batch deletion
        result = FileOperations.delete_files_batch(paths, confirm=True)

        logger.info(
            f"Deleted {result['deleted_count']} files, "
            f"freed {result['space_freed_mb']:.2f} MB"
        )

        return result

    except CommandError:
        raise
    except Exception as e:
        logger.error(f"Failed to delete files: {e}", exc_info=True)
        raise CommandError(
            "EXECUTION_FAILED",
            f"Failed to delete files: {str(e)}",
            {"original_error": str(e)}
        )


# CLI entry point for Tauri sidecar
if __name__ == "__main__":
    # Setup logging
    setup_logging("INFO")

    # Read command from stdin (JSON-RPC style)
    if len(sys.argv) > 1:
        command = sys.argv[1]
        args = json.loads(sys.argv[2]) if len(sys.argv) > 2 else {}

        try:
            result: Any
            if command == "scan_files":
                result = scan_files(**args)
            elif command == "execute_operations":
                result = execute_operations(**args)
            elif command == "cancel_operation":
                result = cancel_operation(**args)
            elif command == "get_rules":
                result = get_rules()
            elif command == "get_configuration":
                result = get_configuration()
            elif command == "detect_screenshot_location":
                result = detect_screenshot_location()
            elif command == "get_operation_history":
                result = get_operation_history(**args)
            elif command == "create_rule":
                result = create_rule(**args)
            elif command == "update_rule":
                result = update_rule(**args)
            elif command == "delete_rule":
                result = delete_rule(**args)
            elif command == "toggle_rule":
                result = toggle_rule(**args)
            elif command == "get_large_files":
                result = get_large_files(**args)
            elif command == "get_old_files":
                result = get_old_files(**args)
            elif command == "delete_files":
                result = delete_files(**args)
            elif command == "export_configuration":
                result = export_configuration(**args)
            elif command == "import_configuration":
                result = import_configuration(**args)
            else:
                result = {"error": f"Unknown command: {command}"}

                # Output result as JSON
            print(json.dumps(result))

        except CommandError as e:
            # Serialize structured error (T137)
            error_result = {"error": e.to_dict()}
            print(json.dumps(error_result))
            sys.exit(1)
        except Exception as e:
            # Fallback for unexpected errors
            error_result = {
                "error": {
                    "code": "UNKNOWN_ERROR",
                    "message": str(e),
                    "details": {"type": type(e).__name__}
                }
            }
            print(json.dumps(error_result))
            sys.exit(1)
