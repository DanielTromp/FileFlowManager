"""
Retry logic with exponential backoff for transient failures.

Provides decorators and utilities for retrying operations that may fail
temporarily due to network issues, file locks, etc.
"""

import functools
import logging
import time
from collections.abc import Callable
from typing import Any, TypeVar

from fileflow_core.errors import OperationCancelledError, RetryableError

logger = logging.getLogger(__name__)

T = TypeVar("T")


class RetryConfig:
    """Configuration for retry behavior."""

    def __init__(
        self,
        max_attempts: int = 3,
        initial_delay: float = 1.0,
        max_delay: float = 60.0,
        exponential_base: float = 2.0,
        jitter: bool = True,
        retryable_exceptions: tuple[type[Exception], ...] = (RetryableError,),
    ):
        """
        Initialize retry configuration.

        Args:
            max_attempts: Maximum number of retry attempts
            initial_delay: Initial delay in seconds before first retry
            max_delay: Maximum delay in seconds between retries
            exponential_base: Base for exponential backoff calculation
            jitter: Whether to add random jitter to delay
            retryable_exceptions: Tuple of exception types that should trigger retry
        """
        self.max_attempts = max_attempts
        self.initial_delay = initial_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
        self.jitter = jitter
        self.retryable_exceptions = retryable_exceptions

    def should_retry(self, exception: Exception) -> bool:
        """Check if an exception should trigger a retry."""
        return isinstance(exception, self.retryable_exceptions)

    def get_delay(self, attempt: int) -> float:
        """
        Calculate delay for a given attempt number.

        Uses exponential backoff: delay = initial_delay * (base ^ attempt)
        Caps at max_delay and optionally adds jitter.

        Args:
            attempt: Attempt number (0-indexed)

        Returns:
            Delay in seconds
        """
        import random

        # Calculate exponential backoff
        delay = min(
            self.initial_delay * (self.exponential_base**attempt), self.max_delay
        )

        # Add jitter if enabled (±25% randomness)
        if self.jitter:
            jitter_range = delay * 0.25
            delay += random.uniform(-jitter_range, jitter_range)

        return max(0, delay)  # Ensure non-negative


def with_retry(
    config: RetryConfig | None = None,
    max_attempts: int | None = None,
    initial_delay: float | None = None,
    retryable_exceptions: tuple[type[Exception], ...] | None = None,
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """
    Decorator to retry a function with exponential backoff.

    Args:
        config: RetryConfig object (overrides other params if provided)
        max_attempts: Maximum retry attempts (default: 3)
        initial_delay: Initial delay in seconds (default: 1.0)
        retryable_exceptions: Exceptions to retry on (default: RetryableError)

    Returns:
        Decorated function

    Example:
        @with_retry(max_attempts=5, initial_delay=0.5)
        def unreliable_operation():
            # May fail transiently
            pass
    """
    # Build config from params if not provided
    if config is None:
        config = RetryConfig(
            max_attempts=max_attempts or 3,
            initial_delay=initial_delay or 1.0,
            retryable_exceptions=retryable_exceptions or (RetryableError,),
        )

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            last_exception: Exception | None = None

            for attempt in range(config.max_attempts):
                try:
                    return func(*args, **kwargs)
                except OperationCancelledError:
                    # Don't retry if user cancelled
                    raise
                except Exception as e:
                    last_exception = e

                    # Check if we should retry this exception
                    if not config.should_retry(e):
                        logger.debug(
                            f"{func.__name__}: Non-retryable exception {type(e).__name__}, not retrying"
                        )
                        raise

                    # Check if we have more attempts
                    if attempt >= config.max_attempts - 1:
                        logger.warning(
                            f"{func.__name__}: Max retry attempts ({config.max_attempts}) reached"
                        )
                        break

                    # Calculate delay and wait
                    delay = config.get_delay(attempt)
                    logger.info(
                        f"{func.__name__}: Attempt {attempt + 1} failed with {type(e).__name__}, "
                        f"retrying in {delay:.2f}s..."
                    )

                    time.sleep(delay)

            # All attempts failed, raise last exception
            if last_exception:
                raise last_exception
            else:
                raise RuntimeError(f"{func.__name__}: All retry attempts failed")

        return wrapper

    return decorator


class RetryContext:
    """Context manager for retry logic."""

    def __init__(self, config: RetryConfig | None = None):
        """
        Initialize retry context.

        Args:
            config: Retry configuration
        """
        self.config = config or RetryConfig()
        self.attempt = 0
        self.last_exception: Exception | None = None

    def __enter__(self) -> "RetryContext":
        """Enter context."""
        return self

    def __exit__(
        self,
        exc_type: type[Exception] | None,
        exc_val: Exception | None,
        exc_tb: Any,
    ) -> bool:
        """
        Exit context.

        Returns:
            True to suppress exception (will retry), False to propagate
        """
        # No exception, success
        if exc_type is None:
            return False

        # Don't retry user cancellation
        if isinstance(exc_val, OperationCancelledError):
            return False

        # Don't retry if exception type not retryable
        if exc_val and not self.config.should_retry(exc_val):
            return False

        # Check if we have more attempts
        if self.attempt >= self.config.max_attempts - 1:
            logger.warning(
                f"Max retry attempts ({self.config.max_attempts}) reached"
            )
            return False

        # Retry
        self.last_exception = exc_val
        delay = self.config.get_delay(self.attempt)
        logger.info(
            f"Attempt {self.attempt + 1} failed with {exc_type.__name__}, "
            f"retrying in {delay:.2f}s..."
        )

        time.sleep(delay)
        self.attempt += 1
        return True  # Suppress exception to retry


def retry_on_failure(
    func: Callable[..., T],
    config: RetryConfig | None = None,
    *args: Any,
    **kwargs: Any,
) -> T:
    """
    Execute a function with retry logic.

    Args:
        func: Function to execute
        config: Retry configuration
        *args: Positional arguments for func
        **kwargs: Keyword arguments for func

    Returns:
        Return value of func

    Raises:
        Last exception if all retries fail

    Example:
        result = retry_on_failure(
            unreliable_function,
            RetryConfig(max_attempts=5),
            arg1, arg2,
            kwarg1=value1
        )
    """
    retry_config = config or RetryConfig()

    for attempt in range(retry_config.max_attempts):
        try:
            return func(*args, **kwargs)
        except OperationCancelledError:
            raise
        except Exception as e:
            if not retry_config.should_retry(e):
                raise

            if attempt >= retry_config.max_attempts - 1:
                raise

            delay = retry_config.get_delay(attempt)
            logger.info(
                f"{func.__name__}: Attempt {attempt + 1} failed, "
                f"retrying in {delay:.2f}s..."
            )
            time.sleep(delay)

    raise RuntimeError("All retry attempts failed")


# Pre-configured retry decorators for common scenarios
def retry_file_operation(func: Callable[..., T]) -> Callable[..., T]:
    """Retry decorator for file operations (shorter delays, more attempts)."""
    return with_retry(
        config=RetryConfig(
            max_attempts=5,
            initial_delay=0.5,
            max_delay=10.0,
            retryable_exceptions=(RetryableError, OSError, PermissionError),
        )
    )(func)


def retry_network_operation(func: Callable[..., T]) -> Callable[..., T]:
    """Retry decorator for network operations (longer delays, fewer attempts)."""
    return with_retry(
        config=RetryConfig(
            max_attempts=3,
            initial_delay=2.0,
            max_delay=30.0,
            retryable_exceptions=(RetryableError, OSError, TimeoutError),
        )
    )(func)


def retry_database_operation(func: Callable[..., T]) -> Callable[..., T]:
    """Retry decorator for database operations."""
    import sqlite3

    return with_retry(
        config=RetryConfig(
            max_attempts=5,
            initial_delay=0.1,
            max_delay=5.0,
            retryable_exceptions=(RetryableError, sqlite3.OperationalError),
        )
    )(func)
