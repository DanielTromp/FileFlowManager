"""
Unit tests for retry logic.

Tests the retry system including exponential backoff, jitter,
and pre-configured retry decorators.
"""

import time
from typing import List

import pytest

from fileflow_core.errors import OperationCancelledError, RetryableError
from fileflow_core.retry import (
    RetryConfig,
    retry_database_operation,
    retry_file_operation,
    retry_network_operation,
    retry_on_failure,
    with_retry,
)


class TestRetryConfig:
    """Test RetryConfig class."""

    def test_default_config(self):
        """Test default retry configuration."""
        config = RetryConfig()
        assert config.max_attempts == 3
        assert config.initial_delay == 1.0
        assert config.max_delay == 60.0
        assert config.exponential_base == 2.0
        assert config.jitter is True
        assert config.retryable_exceptions == (RetryableError,)

    def test_custom_config(self):
        """Test custom retry configuration."""
        config = RetryConfig(
            max_attempts=5,
            initial_delay=0.5,
            max_delay=30.0,
            exponential_base=3.0,
            jitter=False,
            retryable_exceptions=(OSError, TimeoutError),
        )
        assert config.max_attempts == 5
        assert config.initial_delay == 0.5
        assert config.max_delay == 30.0
        assert config.exponential_base == 3.0
        assert config.jitter is False
        assert config.retryable_exceptions == (OSError, TimeoutError)

    def test_should_retry(self):
        """Test should_retry method."""
        config = RetryConfig(retryable_exceptions=(RetryableError, OSError))

        assert config.should_retry(RetryableError("Test"))
        assert config.should_retry(OSError("Test"))
        assert not config.should_retry(ValueError("Test"))

    def test_get_delay_without_jitter(self):
        """Test delay calculation without jitter."""
        config = RetryConfig(
            initial_delay=1.0,
            exponential_base=2.0,
            jitter=False,
        )

        # Attempt 0: 1.0 * (2^0) = 1.0
        assert config.get_delay(0) == 1.0

        # Attempt 1: 1.0 * (2^1) = 2.0
        assert config.get_delay(1) == 2.0

        # Attempt 2: 1.0 * (2^2) = 4.0
        assert config.get_delay(2) == 4.0

        # Attempt 3: 1.0 * (2^3) = 8.0
        assert config.get_delay(3) == 8.0

    def test_get_delay_with_max_delay(self):
        """Test delay capping at max_delay."""
        config = RetryConfig(
            initial_delay=10.0,
            max_delay=20.0,
            exponential_base=2.0,
            jitter=False,
        )

        # Attempt 0: 10.0 * (2^0) = 10.0
        assert config.get_delay(0) == 10.0

        # Attempt 1: 10.0 * (2^1) = 20.0 (at max)
        assert config.get_delay(1) == 20.0

        # Attempt 2: 10.0 * (2^2) = 40.0 -> capped at 20.0
        assert config.get_delay(2) == 20.0

    def test_get_delay_with_jitter(self):
        """Test delay calculation with jitter."""
        config = RetryConfig(
            initial_delay=10.0,
            exponential_base=2.0,
            jitter=True,
        )

        # With jitter, delay should be within ±25% of expected value
        expected_delay = 10.0  # 10.0 * (2^0)
        delay = config.get_delay(0)

        # Should be between 7.5 and 12.5
        assert 7.5 <= delay <= 12.5

        # Multiple calls should produce different values (with high probability)
        delays = [config.get_delay(0) for _ in range(10)]
        assert len(set(delays)) > 1  # Should have some variation


class TestWithRetryDecorator:
    """Test with_retry decorator."""

    def test_successful_call_no_retry(self):
        """Test successful call without retries."""
        call_count = [0]

        @with_retry(max_attempts=3)
        def successful_func():
            call_count[0] += 1
            return "success"

        result = successful_func()
        assert result == "success"
        assert call_count[0] == 1  # Called only once

    def test_retry_on_retryable_error(self):
        """Test retry on retryable error."""
        call_count = [0]

        @with_retry(max_attempts=3, initial_delay=0.01)
        def failing_func():
            call_count[0] += 1
            if call_count[0] < 3:
                raise RetryableError("Temporary failure")
            return "success"

        result = failing_func()
        assert result == "success"
        assert call_count[0] == 3  # Retried twice, succeeded on third

    def test_no_retry_on_non_retryable_error(self):
        """Test no retry on non-retryable error."""
        call_count = [0]

        @with_retry(max_attempts=3)
        def failing_func():
            call_count[0] += 1
            raise ValueError("Non-retryable error")

        with pytest.raises(ValueError, match="Non-retryable error"):
            failing_func()

        assert call_count[0] == 1  # Only called once, no retries

    def test_max_attempts_exceeded(self):
        """Test failure after max attempts exceeded."""
        call_count = [0]

        @with_retry(max_attempts=3, initial_delay=0.01)
        def always_failing_func():
            call_count[0] += 1
            raise RetryableError("Always fails")

        with pytest.raises(RetryableError, match="Always fails"):
            always_failing_func()

        assert call_count[0] == 3  # Tried 3 times

    def test_operation_cancelled_no_retry(self):
        """Test no retry on operation cancelled."""
        call_count = [0]

        @with_retry(max_attempts=3)
        def cancelled_func():
            call_count[0] += 1
            raise OperationCancelledError()

        with pytest.raises(OperationCancelledError):
            cancelled_func()

        assert call_count[0] == 1  # Only called once, no retries

    def test_custom_retryable_exceptions(self):
        """Test retry with custom retryable exceptions."""
        call_count = [0]

        @with_retry(
            max_attempts=3,
            initial_delay=0.01,
            retryable_exceptions=(OSError, TimeoutError),
        )
        def custom_failing_func():
            call_count[0] += 1
            if call_count[0] < 2:
                raise OSError("Temporary OS error")
            return "success"

        result = custom_failing_func()
        assert result == "success"
        assert call_count[0] == 2  # Retried once


class TestRetryOnFailure:
    """Test retry_on_failure function."""

    def test_successful_call(self):
        """Test successful function call."""
        def successful_func(x, y):
            return x + y

        result = retry_on_failure(
            successful_func,
            RetryConfig(max_attempts=3),
            5,
            10,
        )
        assert result == 15

    def test_retry_and_succeed(self):
        """Test retry after failure then succeed."""
        call_count = [0]

        def failing_then_success():
            call_count[0] += 1
            if call_count[0] < 2:
                raise RetryableError("Temporary failure")
            return "success"

        result = retry_on_failure(
            failing_then_success,
            RetryConfig(max_attempts=3, initial_delay=0.01),
        )
        assert result == "success"
        assert call_count[0] == 2


class TestPreConfiguredDecorators:
    """Test pre-configured retry decorators."""

    def test_retry_file_operation(self):
        """Test file operation retry decorator."""
        call_count = [0]

        @retry_file_operation
        def file_op():
            call_count[0] += 1
            if call_count[0] < 2:
                raise OSError("Temporary file error")
            return "success"

        result = file_op()
        assert result == "success"
        assert call_count[0] == 2  # Retried once

    def test_retry_network_operation(self):
        """Test network operation retry decorator."""
        call_count = [0]

        @retry_network_operation
        def network_op():
            call_count[0] += 1
            if call_count[0] < 2:
                raise TimeoutError("Temporary timeout")
            return "success"

        result = network_op()
        assert result == "success"
        assert call_count[0] == 2  # Retried once

    def test_retry_database_operation(self):
        """Test database operation retry decorator."""
        import sqlite3

        call_count = [0]

        @retry_database_operation
        def db_op():
            call_count[0] += 1
            if call_count[0] < 2:
                raise sqlite3.OperationalError("Database locked")
            return "success"

        result = db_op()
        assert result == "success"
        assert call_count[0] == 2  # Retried once


class TestRetryTiming:
    """Test retry timing and delays."""

    def test_exponential_backoff_timing(self):
        """Test that delays follow exponential backoff."""
        call_times: List[float] = []

        config = RetryConfig(
            max_attempts=4,
            initial_delay=0.1,
            exponential_base=2.0,
            jitter=False,
        )

        @with_retry(config=config)
        def failing_func():
            call_times.append(time.time())
            if len(call_times) < 4:
                raise RetryableError("Temporary failure")
            return "success"

        failing_func()

        # Verify we had 4 calls
        assert len(call_times) == 4

        # Check delays between calls (should be approximately 0.1, 0.2, 0.4)
        delay1 = call_times[1] - call_times[0]
        delay2 = call_times[2] - call_times[1]
        delay3 = call_times[3] - call_times[2]

        # Allow 50ms tolerance for timing
        assert 0.05 <= delay1 <= 0.15  # Expected: 0.1s
        assert 0.15 <= delay2 <= 0.25  # Expected: 0.2s
        assert 0.35 <= delay3 <= 0.45  # Expected: 0.4s

    def test_retry_with_arguments(self):
        """Test retry decorator with function arguments."""
        call_count = [0]

        @with_retry(max_attempts=3, initial_delay=0.01)
        def func_with_args(a, b, c=10):
            call_count[0] += 1
            if call_count[0] < 2:
                raise RetryableError("Temporary failure")
            return a + b + c

        result = func_with_args(5, 10, c=20)
        assert result == 35
        assert call_count[0] == 2
