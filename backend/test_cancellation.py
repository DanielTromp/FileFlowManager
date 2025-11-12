#!/usr/bin/env python3
"""Test script for operation cancellation."""

import threading
import time

from fileflow_core.progress import OperationStatus, get_progress_manager


def test_cancellation():
    """Test that operations can be cancelled."""
    manager = get_progress_manager()

    # Create a tracker for a long-running operation
    op_id = "test-cancel-op"
    tracker = manager.create_tracker(op_id, total_items=100)

    print(f"Created tracker with ID: {op_id}")
    tracker.start()
    print(f"Status: {tracker.get_progress().status.value}")

    # Simulate work in a background thread
    def do_work():
        try:
            for i in range(100):
                time.sleep(0.1)  # Simulate slow work
                tracker.update(completed=i+1, current_item=f"Processing item {i+1}")
                print(f"Progress: {i+1}/100")
        except Exception as e:
            print(f"Work interrupted: {e}")
            return
        tracker.complete()

    worker = threading.Thread(target=do_work, daemon=True)
    worker.start()

    # Wait a bit for work to start
    time.sleep(0.5)

    # Cancel the operation
    print("\nCancelling operation...")
    success = manager.cancel_operation(op_id)
    print(f"Cancellation request: {'successful' if success else 'failed'}")

    # Wait for worker to finish
    worker.join(timeout=2.0)

    # Check final status
    progress = tracker.get_progress()
    print(f"\nFinal status: {progress.status.value}")
    print(f"Completed items: {progress.completed_items}/{progress.total_items}")
    print(f"Percentage: {progress.percentage:.1f}%")

    # Verify cancellation worked
    assert progress.status == OperationStatus.CANCELLED, f"Expected CANCELLED, got {progress.status}"
    assert progress.completed_items < 100, "Operation should not have completed all items"

    print("\n✅ Cancellation test PASSED!")

    # Cleanup
    manager.remove_tracker(op_id)

if __name__ == "__main__":
    test_cancellation()
