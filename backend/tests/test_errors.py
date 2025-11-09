"""
Unit tests for error handling system.

Tests the comprehensive error handling infrastructure including
custom exceptions, error formatting, and user-friendly messages.
"""

import pytest

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


class TestFileFlowError:
    """Test base FileFlowError class."""

    def test_basic_error(self):
        """Test basic error creation."""
        error = FileFlowError("Test error")
        assert str(error) == "Test error"
        assert error.message == "Test error"
        assert error.user_message == "Test error"
        assert error.severity == ErrorSeverity.ERROR
        assert error.recoverable is True

    def test_error_with_user_message(self):
        """Test error with custom user message."""
        error = FileFlowError(
            "Technical error",
            user_message="User-friendly error",
            suggestion="Try this fix",
        )
        assert error.message == "Technical error"
        assert error.user_message == "User-friendly error"
        assert error.suggestion == "Try this fix"

    def test_error_severity(self):
        """Test error severity levels."""
        info = FileFlowError("Info", severity=ErrorSeverity.INFO)
        warning = FileFlowError("Warning", severity=ErrorSeverity.WARNING)
        error = FileFlowError("Error", severity=ErrorSeverity.ERROR)
        critical = FileFlowError("Critical", severity=ErrorSeverity.CRITICAL)

        assert info.severity == ErrorSeverity.INFO
        assert warning.severity == ErrorSeverity.WARNING
        assert error.severity == ErrorSeverity.ERROR
        assert critical.severity == ErrorSeverity.CRITICAL

    def test_error_details(self):
        """Test error with additional details."""
        error = FileFlowError(
            "Error with details",
            details={"file": "test.txt", "line": 42},
        )
        assert error.details["file"] == "test.txt"
        assert error.details["line"] == 42

    def test_error_to_dict(self):
        """Test error serialization to dictionary."""
        error = FileFlowError(
            "Test error",
            user_message="User error",
            suggestion="Fix it",
            severity=ErrorSeverity.WARNING,
            details={"key": "value"},
            recoverable=False,
        )
        error_dict = error.to_dict()

        assert error_dict["type"] == "FileFlowError"
        assert error_dict["message"] == "Test error"
        assert error_dict["user_message"] == "User error"
        assert error_dict["suggestion"] == "Fix it"
        assert error_dict["severity"] == "warning"
        assert error_dict["details"] == {"key": "value"}
        assert error_dict["recoverable"] is False


class TestConfigurationError:
    """Test ConfigurationError."""

    def test_basic_configuration_error(self):
        """Test basic configuration error."""
        error = ConfigurationError("Invalid config")
        assert "Configuration error" in error.user_message
        assert "Check your configuration file" in error.suggestion

    def test_configuration_error_with_path(self):
        """Test configuration error with path."""
        error = ConfigurationError("Invalid config", config_path="/path/to/config.json")
        assert error.details["config_path"] == "/path/to/config.json"
        assert "/path/to/config.json" in error.suggestion


class TestFileOperationError:
    """Test FileOperationError."""

    def test_basic_file_operation_error(self):
        """Test basic file operation error."""
        error = FileOperationError("Failed", operation="move", source="/source/file.txt")
        assert "move" in error.user_message
        assert error.details["operation"] == "move"
        assert error.details["source"] == "/source/file.txt"

    def test_permission_denied_suggestion(self):
        """Test permission denied suggestion."""
        error = FileOperationError(
            "Permission denied accessing file",
            operation="read",
            source="/protected/file.txt",
        )
        assert "permission" in error.suggestion.lower()
        assert "Full Disk Access" in error.suggestion

    def test_file_not_found_suggestion(self):
        """Test file not found suggestion."""
        error = FileOperationError(
            "File not found",
            operation="read",
            source="/missing/file.txt",
        )
        assert "verify the file path" in error.suggestion.lower()

    def test_disk_full_suggestion(self):
        """Test disk full suggestion."""
        error = FileOperationError(
            "No space left on device",
            operation="write",
            destination="/full/disk/file.txt",
        )
        assert "disk space" in error.suggestion.lower()


class TestDatabaseError:
    """Test DatabaseError."""

    def test_basic_database_error(self):
        """Test basic database error."""
        error = DatabaseError("Query failed", db_path="/path/to/db.sqlite")
        assert error.details["db_path"] == "/path/to/db.sqlite"
        assert "database" in error.user_message.lower()

    def test_locked_database_suggestion(self):
        """Test locked database suggestion."""
        error = DatabaseError("Database is locked")
        assert "locked" in error.suggestion.lower()
        assert "Close other" in error.suggestion

    def test_disk_full_database_suggestion(self):
        """Test disk full database suggestion."""
        error = DatabaseError("Disk full while writing")
        assert "disk space" in error.suggestion.lower()


class TestValidationError:
    """Test ValidationError."""

    def test_basic_validation_error(self):
        """Test basic validation error."""
        error = ValidationError("Invalid email", field="email", value="not-an-email")
        assert error.severity == ErrorSeverity.WARNING
        assert error.details["field"] == "email"
        assert error.details["value"] == "not-an-email"
        assert "Invalid input" in error.user_message


class TestScanError:
    """Test ScanError."""

    def test_basic_scan_error(self):
        """Test basic scan error."""
        error = ScanError("Cannot scan directory", directory="/path/to/dir")
        assert error.details["directory"] == "/path/to/dir"
        assert error.recoverable is True
        assert "permission" in error.suggestion.lower()


class TestDuplicateDetectionError:
    """Test DuplicateDetectionError."""

    def test_basic_duplicate_detection_error(self):
        """Test basic duplicate detection error."""
        error = DuplicateDetectionError("Checksum failed", file_path="/path/to/file.txt")
        assert error.details["file_path"] == "/path/to/file.txt"
        assert error.recoverable is True
        assert "cache" in error.suggestion.lower()


class TestRuleError:
    """Test RuleError."""

    def test_rule_error_with_name(self):
        """Test rule error with rule name."""
        error = RuleError("Invalid pattern", rule_name="screenshot-org")
        assert "screenshot-org" in error.user_message

    def test_rule_error_with_id(self):
        """Test rule error with rule ID."""
        error = RuleError("Invalid pattern", rule_id="rule-123")
        assert "rule-123" in error.user_message


class TestOperationCancelledError:
    """Test OperationCancelledError."""

    def test_operation_cancelled(self):
        """Test operation cancelled error."""
        error = OperationCancelledError()
        assert error.severity == ErrorSeverity.INFO
        assert error.recoverable is True
        assert error.suggestion is None
        assert "cancelled" in error.user_message.lower()


class TestRetryableError:
    """Test RetryableError."""

    def test_retryable_error(self):
        """Test retryable error."""
        error = RetryableError("Temporary failure", retry_after=2.5)
        assert error.retry_after == 2.5
        assert error.recoverable is True


class TestTransientFileError:
    """Test TransientFileError."""

    def test_transient_file_error(self):
        """Test transient file error."""
        error = TransientFileError("File locked", file_path="/path/to/file.txt")
        assert error.details["file_path"] == "/path/to/file.txt"
        assert "retried automatically" in error.suggestion


class TestNetworkError:
    """Test NetworkError."""

    def test_network_error(self):
        """Test network error."""
        error = NetworkError("Connection timeout")
        assert error.retry_after == 2.0
        assert "network" in error.user_message.lower()
        assert "retried" in error.suggestion.lower()


class TestFormatErrorForUser:
    """Test format_error_for_user helper."""

    def test_format_fileflow_error(self):
        """Test formatting FileFlow error."""
        error = FileFlowError(
            "Technical message",
            user_message="User message",
            suggestion="Fix suggestion",
        )
        formatted = format_error_for_user(error)

        assert formatted["type"] == "FileFlowError"
        assert formatted["message"] == "Technical message"
        assert formatted["user_message"] == "User message"
        assert formatted["suggestion"] == "Fix suggestion"

    def test_format_standard_exception(self):
        """Test formatting standard Python exception."""
        error = FileNotFoundError("File not found: /path/to/file.txt")
        formatted = format_error_for_user(error)

        assert formatted["type"] == "FileNotFoundError"
        assert formatted["user_message"] == "File or directory not found"
        assert "path is correct" in formatted["suggestion"]

    def test_format_permission_error(self):
        """Test formatting permission error."""
        error = PermissionError("Permission denied")
        formatted = format_error_for_user(error)

        assert formatted["type"] == "PermissionError"
        assert formatted["user_message"] == "Permission denied"
        assert "Full Disk Access" in formatted["suggestion"]

    def test_format_value_error(self):
        """Test formatting value error."""
        error = ValueError("Invalid value")
        formatted = format_error_for_user(error)

        assert formatted["type"] == "ValueError"
        assert "Invalid value" in formatted["user_message"]

    def test_format_unknown_error(self):
        """Test formatting unknown error type."""
        error = RuntimeError("Unknown error")
        formatted = format_error_for_user(error)

        assert formatted["type"] == "RuntimeError"
        assert "check the logs" in formatted["suggestion"].lower()
