"""
Tauri IPC command handlers for FileFlow Manager.

This module provides the bridge between the Tauri frontend and Python backend.
Commands are invoked from the Svelte frontend via Tauri's invoke() API.
"""

import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

from fileflow_config.config_manager import ConfigManager
from fileflow_config.defaults import create_default_config_file
from fileflow_core.logging_config import get_logger, setup_logging
from fileflow_core.models import FileOperation, ScanResult
from fileflow_core.rule_engine import RuleEngine
from fileflow_storage.cache import ChecksumCache
from fileflow_storage.database import Database

# Setup logging
logger = get_logger("tauri_commands")

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


def scan_files(dry_run: bool = True, rule_ids: Optional[List[str]] = None) -> Dict[str, Any]:
    """
    Scan files according to active rules.

    Args:
        dry_run: If True, only preview operations without executing
        rule_ids: Optional list of specific rule IDs to scan

    Returns:
        ScanResult as dictionary
    """
    try:
        logger.info(f"Starting scan: dry_run={dry_run}, rule_ids={rule_ids}")

        # Setup
        config_mgr = get_config_manager()
        config = config_mgr.load()
        db = get_database()
        cache = ChecksumCache(db)
        engine = RuleEngine(db, cache, config_mgr.expand_env_vars)

        # Filter rules if specified
        rule_list = config.rules
        if rule_ids:
            rule_list = [r for r in config.rules if r.id in rule_ids]

        # Run scan
        result = engine.scan(rule_list, dry_run=dry_run)

        # Convert to dict for JSON serialization
        result_dict = result.model_dump(mode="json")

        logger.info(
            f"Scan complete: {result.files_matched} files matched, "
            f"{len(result.planned_operations)} operations planned"
        )

        return result_dict

    except Exception as e:
        logger.error(f"Scan failed: {e}", exc_info=True)
        raise


def execute_operations(
    operation_ids: List[str], confirm_deletions: bool = False
) -> Dict[str, Any]:
    """
    Execute specific file operations from a previous scan.

    Args:
        operation_ids: List of operation IDs to execute
        confirm_deletions: Must be True to execute delete operations

    Returns:
        ExecutionResult as dictionary
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

        # Check for delete operations
        has_deletions = any(
            op.operation_type.value == "delete" for op in operations_to_execute
        )
        if has_deletions and not confirm_deletions:
            raise ValueError(
                "Delete operations require confirm_deletions=True"
            )

        # Execute operations
        executed = engine.execute(operations_to_execute)

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

    except Exception as e:
        logger.error(f"Execution failed: {e}", exc_info=True)
        raise


def get_rules() -> List[Dict[str, Any]]:
    """Get all configured rules."""
    try:
        config_mgr = get_config_manager()
        config = config_mgr.load()

        return [rule.model_dump(mode="json") for rule in config.rules]

    except Exception as e:
        logger.error(f"Failed to get rules: {e}", exc_info=True)
        raise


def get_configuration() -> Dict[str, Any]:
    """Get current configuration."""
    try:
        config_mgr = get_config_manager()
        config = config_mgr.load()

        return config.model_dump(mode="json")

    except Exception as e:
        logger.error(f"Failed to get configuration: {e}", exc_info=True)
        raise


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
    operation_type: Optional[str] = None,
    rule_id: Optional[str] = None,
    include_dry_runs: bool = False,
) -> List[Dict[str, Any]]:
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
        raise


# CLI entry point for Tauri sidecar
if __name__ == "__main__":
    # Setup logging
    setup_logging("INFO")

    # Read command from stdin (JSON-RPC style)
    if len(sys.argv) > 1:
        command = sys.argv[1]
        args = json.loads(sys.argv[2]) if len(sys.argv) > 2 else {}

        try:
            if command == "scan_files":
                result = scan_files(**args)
            elif command == "execute_operations":
                result = execute_operations(**args)
            elif command == "get_rules":
                result = get_rules()
            elif command == "get_configuration":
                result = get_configuration()
            elif command == "detect_screenshot_location":
                result = detect_screenshot_location()
            elif command == "get_operation_history":
                result = get_operation_history(**args)
            else:
                result = {"error": f"Unknown command: {command}"}

            # Output result as JSON
            print(json.dumps(result))

        except Exception as e:
            error_result = {"error": str(e)}
            print(json.dumps(error_result))
            sys.exit(1)
