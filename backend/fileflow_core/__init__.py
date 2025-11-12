"""
FileFlow Core Module.

Provides core functionality for file operations, scanning, error handling,
progress tracking, retry logic, and caching.
"""

# Error handling
# Caching
from fileflow_core.cache import (
    ConnectionPool,
    LRUCache,
    QueryCache,
    cached,
)
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

# Progress tracking
from fileflow_core.progress import (
    OperationStatus,
    ProgressInfo,
    ProgressManager,
    ProgressTracker,
    get_progress_manager,
)

# Retry logic
from fileflow_core.retry import (
    RetryConfig,
    RetryContext,
    retry_database_operation,
    retry_file_operation,
    retry_network_operation,
    retry_on_failure,
    with_retry,
)

__all__ = [
    # Error handling
    "FileFlowError",
    "ErrorSeverity",
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
    "format_error_for_user",
    # Progress tracking
    "ProgressTracker",
    "ProgressManager",
    "ProgressInfo",
    "OperationStatus",
    "get_progress_manager",
    # Retry logic
    "RetryConfig",
    "RetryContext",
    "with_retry",
    "retry_on_failure",
    "retry_file_operation",
    "retry_network_operation",
    "retry_database_operation",
    # Caching
    "LRUCache",
    "ConnectionPool",
    "QueryCache",
    "cached",
]
