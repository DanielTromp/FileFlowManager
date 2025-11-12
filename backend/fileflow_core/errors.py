"""
Enhanced error handling with user-friendly messages and recovery strategies.

This module provides custom exceptions with actionable error messages and
context for better user experience and debugging.
"""

from enum import Enum
from typing import Any


class ErrorSeverity(Enum):
    """Severity levels for errors."""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class FileFlowError(Exception):
    """Base exception for all FileFlow errors."""

    def __init__(
        self,
        message: str,
        user_message: str | None = None,
        suggestion: str | None = None,
        severity: ErrorSeverity = ErrorSeverity.ERROR,
        details: dict[str, Any] | None = None,
        recoverable: bool = True,
    ):
        """
        Initialize FileFlow error.

        Args:
            message: Technical error message for logs
            user_message: User-friendly error message
            suggestion: Actionable suggestion to fix the error
            severity: Error severity level
            details: Additional error context
            recoverable: Whether the error is recoverable
        """
        super().__init__(message)
        self.message = message
        self.user_message = user_message or message
        self.suggestion = suggestion
        self.severity = severity
        self.details = details or {}
        self.recoverable = recoverable

    def to_dict(self) -> dict[str, Any]:
        """Convert error to dictionary for JSON serialization."""
        return {
            "type": self.__class__.__name__,
            "message": self.message,
            "user_message": self.user_message,
            "suggestion": self.suggestion,
            "severity": self.severity.value,
            "details": self.details,
            "recoverable": self.recoverable,
        }


class ConfigurationError(FileFlowError):
    """Configuration-related errors."""

    def __init__(self, message: str, config_path: str | None = None, **kwargs: Any):
        """Initialize configuration error."""
        user_msg = f"Configuration error: {message}"
        suggestion = "Check your configuration file and fix any syntax errors."

        if config_path:
            suggestion = f"Check {config_path} and fix any syntax errors."

        super().__init__(
            message,
            user_message=user_msg,
            suggestion=suggestion,
            details={"config_path": config_path},
            **kwargs,
        )


class FileOperationError(FileFlowError):
    """File operation errors (move, delete, etc.)."""

    def __init__(
        self,
        message: str,
        operation: str,
        source: str | None = None,
        destination: str | None = None,
        **kwargs: Any,
    ):
        """Initialize file operation error."""
        user_msg = f"Failed to {operation} file"
        if source:
            user_msg += f": {source}"

        suggestion = self._get_suggestion(message, operation)

        super().__init__(
            message,
            user_message=user_msg,
            suggestion=suggestion,
            details={
                "operation": operation,
                "source": source,
                "destination": destination,
            },
            **kwargs,
        )

    @staticmethod
    def _get_suggestion(message: str, operation: str) -> str:
        """Get actionable suggestion based on error message."""
        msg_lower = message.lower()

        if "permission" in msg_lower or "denied" in msg_lower:
            return (
                "Check file permissions and ensure FileFlow has "
                "Full Disk Access in System Settings → Privacy & Security."
            )
        elif "not found" in msg_lower:
            return "Verify the file path exists and hasn't been moved or deleted."
        elif "already exists" in msg_lower:
            return "The destination file already exists. FileFlow will add a number to avoid overwriting."
        elif "no space" in msg_lower or "disk full" in msg_lower:
            return "Free up disk space on the destination drive and try again."
        elif "read-only" in msg_lower:
            return "The destination is read-only. Check drive mount options or file system permissions."
        else:
            return f"Unable to {operation} file. Check permissions and available disk space."


class DatabaseError(FileFlowError):
    """Database-related errors."""

    def __init__(self, message: str, db_path: str | None = None, **kwargs: Any):
        """Initialize database error."""
        user_msg = "Database error occurred"
        suggestion = (
            "The database may be corrupted. Try clearing cache in Settings. "
            "If the problem persists, you may need to reset the database."
        )

        if "locked" in message.lower():
            suggestion = (
                "The database is locked by another process. "
                "Close other FileFlow instances and try again."
            )
        elif "disk full" in message.lower():
            suggestion = "Free up disk space and try again."

        super().__init__(
            message,
            user_message=user_msg,
            suggestion=suggestion,
            details={"db_path": db_path},
            **kwargs,
        )


class ValidationError(FileFlowError):
    """Validation errors for user input."""

    def __init__(
        self, message: str, field: str | None = None, value: Any = None, **kwargs: Any
    ):
        """Initialize validation error."""
        user_msg = f"Invalid input: {message}"
        suggestion = "Please correct the input and try again."

        super().__init__(
            message,
            user_message=user_msg,
            suggestion=suggestion,
            severity=ErrorSeverity.WARNING,
            details={"field": field, "value": value},
            **kwargs,
        )


class ScanError(FileFlowError):
    """Errors during file scanning."""

    def __init__(self, message: str, directory: str | None = None, **kwargs: Any):
        """Initialize scan error."""
        user_msg = "Error scanning files"
        if directory:
            user_msg += f" in {directory}"

        suggestion = (
            "Check that the directory exists and FileFlow has permission to access it. "
            "Grant Full Disk Access in System Settings if needed."
        )

        super().__init__(
            message,
            user_message=user_msg,
            suggestion=suggestion,
            details={"directory": directory},
            recoverable=True,
            **kwargs,
        )


class DuplicateDetectionError(FileFlowError):
    """Errors during duplicate detection."""

    def __init__(self, message: str, file_path: str | None = None, **kwargs: Any):
        """Initialize duplicate detection error."""
        user_msg = "Error detecting duplicates"
        suggestion = (
            "Try clearing the checksum cache in Settings → Clear Cache and rescan."
        )

        super().__init__(
            message,
            user_message=user_msg,
            suggestion=suggestion,
            details={"file_path": file_path},
            recoverable=True,
            **kwargs,
        )


class RuleError(FileFlowError):
    """Errors in rule configuration or execution."""

    def __init__(
        self, message: str, rule_id: str | None = None, rule_name: str | None = None, **kwargs: Any
    ):
        """Initialize rule error."""
        user_msg = "Error with rule"
        if rule_name:
            user_msg += f" '{rule_name}'"
        elif rule_id:
            user_msg += f" (ID: {rule_id})"

        suggestion = (
            "Check the rule configuration for invalid patterns or paths. "
            "Edit the rule in the Rules tab to fix any issues."
        )

        super().__init__(
            message,
            user_message=user_msg,
            suggestion=suggestion,
            details={"rule_id": rule_id, "rule_name": rule_name},
            **kwargs,
        )


class OperationCancelledError(FileFlowError):
    """Raised when user cancels an operation."""

    def __init__(self, message: str = "Operation cancelled by user", **kwargs: Any):
        """Initialize operation cancelled error."""
        super().__init__(
            message,
            user_message="Operation cancelled",
            suggestion=None,
            severity=ErrorSeverity.INFO,
            recoverable=True,
            **kwargs,
        )


class RetryableError(FileFlowError):
    """Base class for errors that should be retried."""

    def __init__(self, message: str, retry_after: float = 1.0, **kwargs: Any):
        """
        Initialize retryable error.

        Args:
            message: Error message
            retry_after: Seconds to wait before retry
            **kwargs: Additional arguments for FileFlowError
        """
        super().__init__(message, **kwargs)
        self.retry_after = retry_after


class TransientFileError(RetryableError):
    """Transient file operation errors that should be retried."""

    def __init__(
        self, message: str, file_path: str | None = None, retry_after: float = 1.0, **kwargs: Any
    ):
        """Initialize transient file error."""
        super().__init__(
            message,
            user_message="Temporary file operation error",
            suggestion="The operation will be retried automatically.",
            retry_after=retry_after,
            details={"file_path": file_path},
            **kwargs,
        )


class NetworkError(RetryableError):
    """Network-related errors (for network drives)."""

    def __init__(self, message: str, retry_after: float = 2.0, **kwargs: Any):
        """Initialize network error."""
        super().__init__(
            message,
            user_message="Network connection error",
            suggestion="Check your network connection. The operation will be retried.",
            retry_after=retry_after,
            **kwargs,
        )


def format_error_for_user(error: Exception) -> dict[str, Any]:
    """
    Format any exception for user display.

    Args:
        error: Exception to format

    Returns:
        Dictionary with user-friendly error information
    """
    if isinstance(error, FileFlowError):
        return error.to_dict()

    # Handle standard Python exceptions
    error_type = type(error).__name__
    message = str(error)

    # Map common exceptions to user-friendly messages
    user_messages = {
        "FileNotFoundError": "File or directory not found",
        "PermissionError": "Permission denied",
        "OSError": "System error occurred",
        "ValueError": "Invalid value provided",
        "TypeError": "Invalid type provided",
        "KeyError": "Required setting not found",
        "AttributeError": "Configuration error",
    }

    suggestions = {
        "FileNotFoundError": "Check that the file or directory exists and the path is correct.",
        "PermissionError": (
            "Grant FileFlow Full Disk Access in System Settings → Privacy & Security."
        ),
        "OSError": "Check system resources and try again.",
        "ValueError": "Check your input values and try again.",
        "TypeError": "Check your configuration for invalid types.",
        "KeyError": "Check your configuration file for missing required settings.",
        "AttributeError": "Check your configuration file for errors.",
    }

    return {
        "type": error_type,
        "message": message,
        "user_message": user_messages.get(error_type, f"{error_type}: {message}"),
        "suggestion": suggestions.get(error_type, "Check the logs for more details."),
        "severity": "error",
        "details": {},
        "recoverable": True,
    }
