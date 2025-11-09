"""
Unit tests for progress tracking.

Tests the progress tracking infrastructure including ProgressTracker,
ProgressManager, and cancellation support.
"""

import time

import pytest

from fileflow_core.errors import OperationCancelledError
from fileflow_core.progress import (
    OperationStatus,
    ProgressInfo,
    ProgressManager,
    ProgressTracker,
    get_progress_manager,
)


class TestProgressInfo:
    """Test ProgressInfo class."""

    def test_basic_progress_info(self):
        """Test basic progress info creation."""
        info = ProgressInfo(operation_id="test-001", total_items=100, completed_items=50)

        assert info.operation_id == "test-001"
        assert info.total_items == 100
        assert info.completed_items == 50
        assert info.status == OperationStatus.PENDING

    def test_percentage_calculation(self):
        """Test completion percentage calculation."""
        info = ProgressInfo(operation_id="test", total_items=100, completed_items=25)
        assert info.percentage == 25.0

        info.completed_items = 50
        assert info.percentage == 50.0

        info.completed_items = 100
        assert info.percentage == 100.0

    def test_percentage_with_zero_total(self):
        """Test percentage with zero total items."""
        info = ProgressInfo(operation_id="test", total_items=0, completed_items=0)
        assert info.percentage == 0.0

    def test_elapsed_time(self):
        """Test elapsed time calculation."""
        info = ProgressInfo(operation_id="test")
        time.sleep(0.1)
        assert info.elapsed_time >= 0.1

    def test_items_per_second(self):
        """Test processing rate calculation."""
        info = ProgressInfo(operation_id="test", total_items=100, completed_items=50)
        time.sleep(0.1)
        rate = info.items_per_second
        assert rate > 0

    def test_estimated_remaining(self):
        """Test estimated remaining time."""
        info = ProgressInfo(operation_id="test", total_items=100, completed_items=50)
        time.sleep(0.1)

        remaining = info.estimated_remaining
        assert remaining is not None
        assert remaining > 0

    def test_estimated_remaining_with_zero_completed(self):
        """Test estimated remaining with zero completed items."""
        info = ProgressInfo(operation_id="test", total_items=100, completed_items=0)
        assert info.estimated_remaining is None

    def test_to_dict(self):
        """Test progress info serialization."""
        info = ProgressInfo(
            operation_id="test-001",
            total_items=100,
            completed_items=50,
            current_item="file.txt",
        )

        data = info.to_dict()
        assert data["operation_id"] == "test-001"
        assert data["total_items"] == 100
        assert data["completed_items"] == 50
        assert data["current_item"] == "file.txt"
        assert data["percentage"] == 50.0
        assert "elapsed_time" in data
        assert "items_per_second" in data


class TestProgressTracker:
    """Test ProgressTracker class."""

    def test_basic_tracker_creation(self):
        """Test basic tracker creation."""
        tracker = ProgressTracker("test-001", total_items=100)
        assert tracker.operation_id == "test-001"

        progress = tracker.get_progress()
        assert progress.total_items == 100
        assert progress.status == OperationStatus.PENDING

    def test_start_operation(self):
        """Test starting an operation."""
        tracker = ProgressTracker("test-001")
        tracker.start()

        progress = tracker.get_progress()
        assert progress.status == OperationStatus.RUNNING

    def test_update_progress(self):
        """Test updating progress."""
        tracker = ProgressTracker("test-001", total_items=100)
        tracker.start()

        tracker.update(completed=25, current_item="item1.txt")
        progress = tracker.get_progress()
        assert progress.completed_items == 25
        assert progress.current_item == "item1.txt"

        tracker.update(completed=50, current_item="item2.txt")
        progress = tracker.get_progress()
        assert progress.completed_items == 50
        assert progress.current_item == "item2.txt"

    def test_update_with_increment(self):
        """Test updating progress with increment."""
        tracker = ProgressTracker("test-001", total_items=100)
        tracker.start()

        tracker.update(increment=10)
        assert tracker.get_progress().completed_items == 10

        tracker.update(increment=5)
        assert tracker.get_progress().completed_items == 15

    def test_complete_operation(self):
        """Test completing an operation."""
        tracker = ProgressTracker("test-001", total_items=100)
        tracker.start()
        tracker.update(completed=100)
        tracker.complete()

        progress = tracker.get_progress()
        assert progress.status == OperationStatus.COMPLETED
        assert progress.end_time is not None
        assert progress.current_item is None

    def test_fail_operation(self):
        """Test failing an operation."""
        tracker = ProgressTracker("test-001", total_items=100)
        tracker.start()
        tracker.fail("Something went wrong")

        progress = tracker.get_progress()
        assert progress.status == OperationStatus.FAILED
        assert progress.error_message == "Something went wrong"
        assert progress.end_time is not None

    def test_cancel_operation(self):
        """Test cancelling an operation."""
        tracker = ProgressTracker("test-001", total_items=100)
        tracker.start()
        tracker.cancel()

        progress = tracker.get_progress()
        assert progress.status == OperationStatus.CANCELLED
        assert progress.end_time is not None

    def test_update_after_cancel_raises_error(self):
        """Test that update after cancel raises OperationCancelledError."""
        tracker = ProgressTracker("test-001", total_items=100)
        tracker.start()
        tracker.cancel()

        with pytest.raises(OperationCancelledError):
            tracker.update(completed=50)

    def test_pause_and_resume(self):
        """Test pausing and resuming operation."""
        tracker = ProgressTracker("test-001", total_items=100)
        tracker.start()

        tracker.pause()
        assert tracker.is_paused()
        assert tracker.get_progress().status == OperationStatus.PAUSED

        tracker.resume()
        assert not tracker.is_paused()
        assert tracker.get_progress().status == OperationStatus.RUNNING

    def test_is_cancelled(self):
        """Test is_cancelled method."""
        tracker = ProgressTracker("test-001", total_items=100)
        assert not tracker.is_cancelled()

        tracker.cancel()
        assert tracker.is_cancelled()

    def test_set_total(self):
        """Test updating total items."""
        tracker = ProgressTracker("test-001", total_items=100)
        tracker.set_total(200)

        progress = tracker.get_progress()
        assert progress.total_items == 200

    def test_progress_callback(self):
        """Test progress callback."""
        callback_called = []

        def callback(progress_info):
            callback_called.append(progress_info)

        tracker = ProgressTracker(
            "test-001",
            total_items=100,
            callback=callback,
            callback_interval=0.01,  # Very short interval for testing
        )

        tracker.start()
        time.sleep(0.02)  # Ensure callback time has passed
        tracker.update(completed=50)

        # Callback should have been called at least once
        assert len(callback_called) > 0
        assert callback_called[-1].completed_items == 50


class TestProgressManager:
    """Test ProgressManager class."""

    def test_create_tracker(self):
        """Test creating a tracker."""
        manager = ProgressManager()
        tracker = manager.create_tracker("test-001", total_items=100)

        assert tracker.operation_id == "test-001"
        assert tracker.get_progress().total_items == 100

    def test_get_tracker(self):
        """Test getting a tracker by ID."""
        manager = ProgressManager()
        tracker1 = manager.create_tracker("test-001", total_items=100)

        tracker2 = manager.get_tracker("test-001")
        assert tracker2 is tracker1

        tracker3 = manager.get_tracker("non-existent")
        assert tracker3 is None

    def test_remove_tracker(self):
        """Test removing a tracker."""
        manager = ProgressManager()
        manager.create_tracker("test-001", total_items=100)

        manager.remove_tracker("test-001")
        assert manager.get_tracker("test-001") is None

    def test_cancel_operation(self):
        """Test cancelling an operation via manager."""
        manager = ProgressManager()
        tracker = manager.create_tracker("test-001", total_items=100)
        tracker.start()

        result = manager.cancel_operation("test-001")
        assert result is True
        assert tracker.is_cancelled()

        result = manager.cancel_operation("non-existent")
        assert result is False

    def test_get_all_progress(self):
        """Test getting all progress."""
        manager = ProgressManager()
        manager.create_tracker("test-001", total_items=100)
        manager.create_tracker("test-002", total_items=200)

        all_progress = manager.get_all_progress()
        assert len(all_progress) == 2

        operation_ids = {p.operation_id for p in all_progress}
        assert "test-001" in operation_ids
        assert "test-002" in operation_ids

    def test_cleanup_completed(self):
        """Test cleanup of completed operations."""
        manager = ProgressManager()

        # Create trackers in different states
        tracker1 = manager.create_tracker("test-001", total_items=100)
        tracker1.start()
        tracker1.complete()

        tracker2 = manager.create_tracker("test-002", total_items=100)
        tracker2.start()
        tracker2.cancel()

        tracker3 = manager.create_tracker("test-003", total_items=100)
        tracker3.start()
        tracker3.fail("Error")

        tracker4 = manager.create_tracker("test-004", total_items=100)
        tracker4.start()  # Still running

        # Cleanup should remove completed, cancelled, and failed
        removed_count = manager.cleanup_completed()
        assert removed_count == 3

        # Only the running tracker should remain
        all_progress = manager.get_all_progress()
        assert len(all_progress) == 1
        assert all_progress[0].operation_id == "test-004"


class TestGetProgressManager:
    """Test global progress manager."""

    def test_get_global_manager(self):
        """Test getting global progress manager."""
        manager1 = get_progress_manager()
        manager2 = get_progress_manager()

        # Should return same instance
        assert manager1 is manager2


class TestProgressIntegration:
    """Integration tests for progress tracking."""

    def test_full_operation_lifecycle(self):
        """Test complete operation lifecycle."""
        tracker = ProgressTracker("scan-files", total_items=1000)

        # Start
        tracker.start()
        assert tracker.get_progress().status == OperationStatus.RUNNING

        # Update progress
        for i in range(1, 11):
            tracker.update(completed=i * 100, current_item=f"file{i}.txt")

        progress = tracker.get_progress()
        assert progress.completed_items == 1000
        assert progress.percentage == 100.0

        # Complete
        tracker.complete()
        assert tracker.get_progress().status == OperationStatus.COMPLETED

    def test_operation_with_cancellation(self):
        """Test operation that gets cancelled."""
        tracker = ProgressTracker("scan-files", total_items=1000)
        tracker.start()

        # Simulate cancellation in the middle
        tracker.update(completed=500)
        tracker.cancel()

        # Further updates should raise
        with pytest.raises(OperationCancelledError):
            tracker.update(completed=600)

    def test_multiple_concurrent_operations(self):
        """Test tracking multiple concurrent operations."""
        manager = ProgressManager()

        # Start multiple operations
        scan_tracker = manager.create_tracker("scan", total_items=1000)
        scan_tracker.start()

        move_tracker = manager.create_tracker("move", total_items=500)
        move_tracker.start()

        delete_tracker = manager.create_tracker("delete", total_items=100)
        delete_tracker.start()

        # Update all
        scan_tracker.update(completed=500)
        move_tracker.update(completed=250)
        delete_tracker.update(completed=50)

        # Get all progress
        all_progress = manager.get_all_progress()
        assert len(all_progress) == 3

        # Complete some
        scan_tracker.complete()
        move_tracker.complete()

        # Cleanup
        removed = manager.cleanup_completed()
        assert removed == 2

        all_progress = manager.get_all_progress()
        assert len(all_progress) == 1
        assert all_progress[0].operation_id == "delete"
