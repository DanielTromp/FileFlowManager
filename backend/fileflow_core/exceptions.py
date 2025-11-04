"""
Custom exceptions for FileFlow Manager.

Provides specific exception types for better error handling.
"""


class FileFlowError(Exception):
    """Base exception for FileFlow errors."""

    pass


class ConfigurationError(FileFlowError):
    """Configuration-related errors."""

    pass


class ValidationError(FileFlowError):
    """Validation errors."""

    pass


class FileOperationError(FileFlowError):
    """File operation errors."""

    pass


class PermissionError(FileFlowError):
    """Permission-related errors."""

    pass


class DiskSpaceError(FileFlowError):
    """Disk space errors."""

    pass


class RuleNotFoundError(FileFlowError):
    """Rule not found error."""

    pass


class DatabaseError(FileFlowError):
    """Database operation errors."""

    pass


class ScanError(FileFlowError):
    """File scanning errors."""

    pass
