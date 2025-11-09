"""
Custom exceptions for FileFlow Manager.

This module re-exports the enhanced error handling system for backwards compatibility.
For new code, import directly from fileflow_core.errors.
"""

# Re-export all error classes from the new error handling system
from fileflow_core.errors import (
    ConfigurationError,
    DatabaseError,
    DuplicateDetectionError,
    ErrorSeverity,
    FileFlowError,
    FileOperationError,
    NetworkError,
    OperationCancelledError,
    RetryableError,
    RuleError,
    ScanError,
    TransientFileError,
    ValidationError,
    format_error_for_user,
)

# Legacy aliases for backwards compatibility
PermissionError = FileOperationError
DiskSpaceError = FileOperationError


class RuleNotFoundError(RuleError):
    """Rule not found error (backwards compatibility alias)."""

    def __init__(self, message: str, rule_id: str | None = None):
        """Initialize rule not found error."""
        super().__init__(message, rule_id=rule_id, rule_name=None)


__all__ = [
    # Core error classes
    "FileFlowError",
    "ErrorSeverity",
    "format_error_for_user",
    # Specific error types
    "ConfigurationError",
    "FileOperationError",
    "DatabaseError",
    "ValidationError",
    "ScanError",
    "DuplicateDetectionError",
    "RuleError",
    "OperationCancelledError",
    "RetryableError",
    "TransientFileError",
    "NetworkError",
    # Backwards compatibility aliases
    "PermissionError",
    "DiskSpaceError",
    "RuleNotFoundError",
]
