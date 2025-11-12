"""
Progress tracking and cancellation support for long-running operations.

Provides progress reporting, cancellation detection, and progress callbacks
for file scanning, organization, and other operations.
"""

import logging
import threading
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from fileflow_core.errors import OperationCancelledError

logger = logging.getLogger(__name__)


class OperationStatus(Enum):
    """Status of a long-running operation."""

    PENDING = "pending"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    FAILED = "failed"


@dataclass
class ProgressInfo:
    """Progress information for an operation."""

    operation_id: str
    status: OperationStatus = OperationStatus.PENDING
    total_items: int = 0
    completed_items: int = 0
    current_item: str | None = None
    start_time: float = field(default_factory=time.time)
    end_time: float | None = None
    error_message: str | None = None

    @property
    def percentage(self) -> float:
        """Get completion percentage (0-100)."""
        if self.total_items == 0:
            return 0.0
        return (self.completed_items / self.total_items) * 100

    @property
    def elapsed_time(self) -> float:
        """Get elapsed time in seconds."""
        end = self.end_time if self.end_time else time.time()
        return end - self.start_time

    @property
    def estimated_remaining(self) -> float | None:
        """Estimate remaining time in seconds."""
        if self.completed_items == 0 or self.total_items == 0:
            return None

        elapsed = self.elapsed_time
        items_per_second = self.completed_items / elapsed
        remaining_items = self.total_items - self.completed_items

        if items_per_second == 0:
            return None

        return remaining_items / items_per_second

    @property
    def items_per_second(self) -> float:
        """Get processing rate (items per second)."""
        if self.elapsed_time == 0:
            return 0.0
        return self.completed_items / self.elapsed_time

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "operation_id": self.operation_id,
            "status": self.status.value,
            "total_items": self.total_items,
            "completed_items": self.completed_items,
            "current_item": self.current_item,
            "percentage": round(self.percentage, 2),
            "elapsed_time": round(self.elapsed_time, 2),
            "estimated_remaining": (
                round(self.estimated_remaining, 2) if self.estimated_remaining else None
            ),
            "items_per_second": round(self.items_per_second, 2),
            "error_message": self.error_message,
        }


class ProgressTracker:
    """
    Track progress of long-running operations with cancellation support.

    Thread-safe progress tracking with optional callbacks for UI updates.
    """

    def __init__(
        self,
        operation_id: str,
        total_items: int = 0,
        callback: Callable[[ProgressInfo], None] | None = None,
        callback_interval: float = 0.5,
    ):
        """
        Initialize progress tracker.

        Args:
            operation_id: Unique identifier for this operation
            total_items: Total number of items to process
            callback: Optional callback function for progress updates
            callback_interval: Minimum seconds between callback invocations
        """
        self.operation_id = operation_id
        self._progress = ProgressInfo(operation_id=operation_id, total_items=total_items)
        self._callback = callback
        self._callback_interval = callback_interval
        self._last_callback_time = 0.0
        self._cancelled = threading.Event()
        self._paused = threading.Event()
        self._lock = threading.Lock()

    def start(self) -> None:
        """Mark operation as started."""
        with self._lock:
            self._progress.status = OperationStatus.RUNNING
            self._progress.start_time = time.time()
            self._notify_progress()

    def update(
        self,
        completed: int | None = None,
        increment: int = 1,
        current_item: str | None = None,
    ) -> None:
        """
        Update progress.

        Args:
            completed: Absolute number of completed items (or None to increment)
            increment: Amount to increment if completed is None
            current_item: Description of current item being processed

        Raises:
            OperationCancelledError: If operation was cancelled
        """
        # Check for cancellation
        if self._cancelled.is_set():
            raise OperationCancelledError()

        # Wait if paused
        while self._paused.is_set():
            time.sleep(0.1)
            if self._cancelled.is_set():
                raise OperationCancelledError()

        with self._lock:
            if completed is not None:
                self._progress.completed_items = completed
            else:
                self._progress.completed_items += increment

            if current_item is not None:
                self._progress.current_item = current_item

            self._notify_progress()

    def complete(self) -> None:
        """Mark operation as completed."""
        with self._lock:
            self._progress.status = OperationStatus.COMPLETED
            self._progress.end_time = time.time()
            self._progress.current_item = None
            self._notify_progress(force=True)

    def fail(self, error_message: str) -> None:
        """Mark operation as failed."""
        with self._lock:
            self._progress.status = OperationStatus.FAILED
            self._progress.end_time = time.time()
            self._progress.error_message = error_message
            self._notify_progress(force=True)

    def cancel(self) -> None:
        """Cancel the operation."""
        with self._lock:
            self._cancelled.set()
            self._paused.clear()  # Unpause if paused
            self._progress.status = OperationStatus.CANCELLED
            self._progress.end_time = time.time()
            self._notify_progress(force=True)

    def pause(self) -> None:
        """Pause the operation."""
        with self._lock:
            if self._progress.status == OperationStatus.RUNNING:
                self._paused.set()
                self._progress.status = OperationStatus.PAUSED
                self._notify_progress(force=True)

    def resume(self) -> None:
        """Resume the operation."""
        with self._lock:
            if self._progress.status == OperationStatus.PAUSED:
                self._paused.clear()
                self._progress.status = OperationStatus.RUNNING
                self._notify_progress(force=True)

    def is_cancelled(self) -> bool:
        """Check if operation was cancelled."""
        return self._cancelled.is_set()

    def is_paused(self) -> bool:
        """Check if operation is paused."""
        return self._paused.is_set()

    def get_progress(self) -> ProgressInfo:
        """Get current progress information."""
        with self._lock:
            # Return a copy to avoid race conditions
            return ProgressInfo(
                operation_id=self._progress.operation_id,
                status=self._progress.status,
                total_items=self._progress.total_items,
                completed_items=self._progress.completed_items,
                current_item=self._progress.current_item,
                start_time=self._progress.start_time,
                end_time=self._progress.end_time,
                error_message=self._progress.error_message,
            )

    def set_total(self, total: int) -> None:
        """Update total items count."""
        with self._lock:
            self._progress.total_items = total
            self._notify_progress()

    def _notify_progress(self, force: bool = False) -> None:
        """
        Notify callback of progress update.

        Args:
            force: Force notification even if interval hasn't elapsed
        """
        if self._callback is None:
            return

        current_time = time.time()
        time_since_last = current_time - self._last_callback_time

        if force or time_since_last >= self._callback_interval:
            try:
                # Create progress info copy without acquiring lock again
                # (this method is only called while lock is already held)
                progress_copy = ProgressInfo(
                    operation_id=self._progress.operation_id,
                    status=self._progress.status,
                    total_items=self._progress.total_items,
                    completed_items=self._progress.completed_items,
                    current_item=self._progress.current_item,
                    start_time=self._progress.start_time,
                    end_time=self._progress.end_time,
                    error_message=self._progress.error_message,
                )
                self._callback(progress_copy)
                self._last_callback_time = current_time
            except Exception as e:
                logger.error(f"Error in progress callback: {e}")


class ProgressManager:
    """
    Manage multiple progress trackers.

    Centralized management of progress for concurrent operations.
    """

    def __init__(self):
        """Initialize progress manager."""
        self._trackers: dict[str, ProgressTracker] = {}
        self._lock = threading.Lock()

    def create_tracker(
        self,
        operation_id: str,
        total_items: int = 0,
        callback: Callable[[ProgressInfo], None] | None = None,
    ) -> ProgressTracker:
        """
        Create a new progress tracker.

        Args:
            operation_id: Unique identifier
            total_items: Total items to process
            callback: Progress update callback

        Returns:
            New ProgressTracker instance
        """
        with self._lock:
            tracker = ProgressTracker(operation_id, total_items, callback)
            self._trackers[operation_id] = tracker
            return tracker

    def get_tracker(self, operation_id: str) -> ProgressTracker | None:
        """Get tracker by operation ID."""
        with self._lock:
            return self._trackers.get(operation_id)

    def remove_tracker(self, operation_id: str) -> None:
        """Remove a tracker."""
        with self._lock:
            self._trackers.pop(operation_id, None)

    def cancel_operation(self, operation_id: str) -> bool:
        """
        Cancel an operation.

        Args:
            operation_id: Operation to cancel

        Returns:
            True if operation was cancelled, False if not found
        """
        tracker = self.get_tracker(operation_id)
        if tracker:
            tracker.cancel()
            return True
        return False

    def get_all_progress(self) -> list[ProgressInfo]:
        """Get progress for all tracked operations."""
        with self._lock:
            return [tracker.get_progress() for tracker in self._trackers.values()]

    def cleanup_completed(self) -> int:
        """
        Remove completed/cancelled/failed operations.

        Returns:
            Number of trackers removed
        """
        with self._lock:
            to_remove = [
                op_id
                for op_id, tracker in self._trackers.items()
                if tracker.get_progress().status
                in (
                    OperationStatus.COMPLETED,
                    OperationStatus.CANCELLED,
                    OperationStatus.FAILED,
                )
            ]

            for op_id in to_remove:
                del self._trackers[op_id]

            return len(to_remove)


# Global progress manager instance
_global_manager = ProgressManager()


def get_progress_manager() -> ProgressManager:
    """Get the global progress manager instance."""
    return _global_manager
