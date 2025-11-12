#!/usr/bin/env python3
"""
Standalone entry point for FileFlow backend.
This is used by PyInstaller to create a standalone executable.
"""

import json
import sys

from fileflow_api.tauri_commands import (
    CommandError,
    cancel_operation,
    create_rule,
    delete_files,
    delete_rule,
    detect_screenshot_location,
    execute_operations,
    export_configuration,
    export_metrics,
    get_all_operations_progress,
    get_cache_statistics,
    get_configuration,
    get_health_status,
    get_large_files,
    get_old_files,
    get_operation_history,
    get_operation_progress,
    get_rules,
    get_system_metrics,
    import_configuration,
    scan_files,
    toggle_rule,
    update_rule,
)
from fileflow_core.logging_config import setup_logging

if __name__ == "__main__":
    # Setup logging
    setup_logging("INFO")

    # Read command from command line arguments
    if len(sys.argv) > 1:
        command = sys.argv[1]
        args = json.loads(sys.argv[2]) if len(sys.argv) > 2 else {}

        try:
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
            elif command == "get_system_metrics":
                result = get_system_metrics()
            elif command == "get_health_status":
                result = get_health_status()
            elif command == "get_cache_statistics":
                result = get_cache_statistics()
            elif command == "export_metrics":
                result = export_metrics(**args)
            elif command == "get_operation_progress":
                result = get_operation_progress(**args)
            elif command == "get_all_operations_progress":
                result = get_all_operations_progress()
            else:
                result = {"error": f"Unknown command: {command}"}

            # Output result as JSON
            print(json.dumps(result))

        except CommandError as e:
            # Serialize structured error
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
