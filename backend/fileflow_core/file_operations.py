"""
Atomic file operations for FileFlow Manager.

Handles safe file moves and deletions with metadata preservation.
Enhanced with retry logic and comprehensive error handling.
"""

import os
import shutil
from pathlib import Path
from typing import Any

from fileflow_core.errors import (
    FileOperationError,
    OperationCancelledError,
    TransientFileError,
)
from fileflow_core.progress import ProgressTracker
from fileflow_core.retry import retry_file_operation


class FileOperations:
    """Safe file operations with atomicity guarantees."""

    @staticmethod
    @retry_file_operation
    def _move_file_with_retry(
        source: Path,
        destination: Path,
        preserve_metadata: bool = True,
    ) -> None:
        """
        Internal move operation with retry logic.

        Raises FileOperationError or TransientFileError on failure.
        """
        # Ensure destination directory exists
        destination.parent.mkdir(parents=True, exist_ok=True)

        # Check if destination already exists
        if destination.exists():
            raise FileOperationError(
                f"Destination already exists: {destination}",
                operation="move",
                source=str(source),
                destination=str(destination),
                recoverable=False,
            )

        # Check source exists
        if not source.exists():
            raise FileOperationError(
                f"Source file not found: {source}",
                operation="move",
                source=str(source),
                recoverable=False,
            )

        # Check if we have permissions
        if not os.access(source, os.R_OK):
            raise FileOperationError(
                "Cannot read source file: permission denied",
                operation="move",
                source=str(source),
                recoverable=False,
            )

        if not os.access(destination.parent, os.W_OK):
            raise FileOperationError(
                "Cannot write to destination directory: permission denied",
                operation="move",
                source=str(source),
                destination=str(destination),
                recoverable=False,
            )

        try:
            # Atomic move (rename on same filesystem)
            # If cross-filesystem, this will fall back to copy+delete
            os.replace(str(source), str(destination))

            # Preserve metadata if requested
            if preserve_metadata:
                try:
                    # Note: os.replace preserves timestamps on some systems
                    # This is a safety measure
                    shutil.copystat(str(source), str(destination))
                except Exception:
                    # Not critical if metadata preservation fails
                    pass

        except PermissionError as e:
            raise FileOperationError(
                str(e),
                operation="move",
                source=str(source),
                destination=str(destination),
                recoverable=False,
            ) from e
        except OSError as e:
            # OSError might be transient (file lock, network hiccup)
            # Raise as TransientFileError to trigger retry
            raise TransientFileError(
                str(e),
                file_path=str(source),
                retry_after=1.0,
            ) from e

    @staticmethod
    def move_file(
        source: Path,
        destination: Path,
        preserve_metadata: bool = True,
    ) -> tuple[bool, str | None]:
        """
        Move file atomically from source to destination.

        Returns (success, error_message).

        Enhanced with automatic retry logic for transient failures.
        """
        try:
            FileOperations._move_file_with_retry(source, destination, preserve_metadata)
            return True, None
        except FileOperationError as e:
            return False, e.user_message
        except Exception as e:
            return False, f"Unexpected error during move: {e}"

    @staticmethod
    @retry_file_operation
    def _delete_file_with_retry(file_path: Path) -> None:
        """
        Internal delete operation with retry logic.

        Raises FileOperationError or TransientFileError on failure.
        """
        # Check file exists
        if not file_path.exists():
            raise FileOperationError(
                f"File not found: {file_path}",
                operation="delete",
                source=str(file_path),
                recoverable=False,
            )

        # Check if we have permissions
        if not os.access(file_path, os.W_OK):
            raise FileOperationError(
                "Cannot delete file: permission denied",
                operation="delete",
                source=str(file_path),
                recoverable=False,
            )

        try:
            # Delete the file
            file_path.unlink()
        except PermissionError as e:
            raise FileOperationError(
                str(e),
                operation="delete",
                source=str(file_path),
                recoverable=False,
            ) from e
        except OSError as e:
            # OSError might be transient
            raise TransientFileError(
                str(e),
                file_path=str(file_path),
                retry_after=1.0,
            ) from e

    @staticmethod
    def delete_file(file_path: Path) -> tuple[bool, str | None]:
        """
        Delete a file safely.

        Returns (success, error_message).

        Enhanced with automatic retry logic for transient failures.
        """
        try:
            FileOperations._delete_file_with_retry(file_path)
            return True, None
        except FileOperationError as e:
            return False, e.user_message
        except Exception as e:
            return False, f"Unexpected error during deletion: {e}"

    @staticmethod
    def check_disk_space(
        destination: Path,
        required_bytes: int,
    ) -> tuple[bool, str | None]:
        """
        Check if there's enough disk space at destination.

        Returns (sufficient_space, error_message).
        """
        try:
            # Get filesystem stats
            stat = os.statvfs(destination.parent)

            # Calculate available space
            available_bytes = stat.f_bavail * stat.f_frsize

            if available_bytes < required_bytes:
                available_mb = available_bytes / (1024 * 1024)
                required_mb = required_bytes / (1024 * 1024)
                return (
                    False,
                    f"Insufficient disk space. Available: {available_mb:.2f} MB, Required: {required_mb:.2f} MB",
                )

            return True, None

        except Exception as e:
            return False, f"Error checking disk space: {e}"

    @staticmethod
    @retry_file_operation
    def _safe_copy_with_retry(
        source: Path,
        destination: Path,
        preserve_metadata: bool = True,
    ) -> None:
        """
        Internal copy operation with retry logic.

        Raises FileOperationError or TransientFileError on failure.
        """
        # Ensure destination directory exists
        destination.parent.mkdir(parents=True, exist_ok=True)

        # Check source exists
        if not source.exists():
            raise FileOperationError(
                f"Source file not found: {source}",
                operation="copy",
                source=str(source),
                recoverable=False,
            )

        try:
            # Copy with metadata preservation
            if preserve_metadata:
                shutil.copy2(str(source), str(destination))
            else:
                shutil.copy(str(source), str(destination))
        except PermissionError as e:
            raise FileOperationError(
                str(e),
                operation="copy",
                source=str(source),
                destination=str(destination),
                recoverable=False,
            ) from e
        except OSError as e:
            # OSError might be transient
            raise TransientFileError(
                str(e),
                file_path=str(source),
                retry_after=1.0,
            ) from e

    @staticmethod
    def safe_copy(
        source: Path,
        destination: Path,
        preserve_metadata: bool = True,
    ) -> tuple[bool, str | None]:
        """
        Copy file safely (for backup purposes).

        Returns (success, error_message).

        Enhanced with automatic retry logic for transient failures.
        """
        try:
            FileOperations._safe_copy_with_retry(source, destination, preserve_metadata)
            return True, None
        except FileOperationError as e:
            return False, e.user_message
        except Exception as e:
            return False, f"Error copying file: {e}"

    @staticmethod
    def delete_files_batch(
        file_paths: list[Path],
        confirm: bool = True,
        progress_tracker: ProgressTracker | None = None,
    ) -> dict[str, Any]:
        """
        Delete multiple files safely with confirmation requirement and progress tracking.

        Args:
            file_paths: List of file paths to delete
            confirm: If True, requires explicit confirmation (safety check)
            progress_tracker: Optional progress tracker for monitoring deletion progress

        Returns:
            Dictionary with:
                - deleted_count: Number of files successfully deleted
                - failed_count: Number of files that failed to delete
                - errors: List of error messages
                - space_freed_mb: Total space freed in MB
        """
        if not confirm:
            return {
                "deleted_count": 0,
                "failed_count": 0,
                "errors": ["Confirmation required for batch deletion"],
                "space_freed_mb": 0,
            }

        deleted_count = 0
        failed_count = 0
        errors = []
        space_freed_bytes = 0

        # Initialize progress tracking if provided
        if progress_tracker:
            progress_tracker.set_total(len(file_paths))
            progress_tracker.start()

        for idx, file_path in enumerate(file_paths):
            try:
                # Check for cancellation
                if progress_tracker and progress_tracker.is_cancelled():
                    raise OperationCancelledError()

                # Get file size before deletion
                if file_path.exists():
                    file_size = file_path.stat().st_size
                    space_freed_bytes += file_size

                success, error_msg = FileOperations.delete_file(file_path)

                if success:
                    deleted_count += 1
                else:
                    failed_count += 1
                    if error_msg:
                        errors.append(f"{file_path.name}: {error_msg}")

                # Update progress
                if progress_tracker:
                    progress_tracker.update(completed=idx + 1, current_item=str(file_path.name))

            except OperationCancelledError:
                if progress_tracker:
                    progress_tracker.cancel()
                errors.append("Operation cancelled by user")
                break
            except Exception as e:
                failed_count += 1
                errors.append(f"{file_path.name}: {str(e)}")

        space_freed_mb = space_freed_bytes / (1024 * 1024)

        # Complete progress tracking
        if progress_tracker and not progress_tracker.is_cancelled():
            progress_tracker.complete()

        return {
            "deleted_count": deleted_count,
            "failed_count": failed_count,
            "errors": errors,
            "space_freed_mb": round(space_freed_mb, 2),
        }

    @staticmethod
    def get_safe_filename(filename: str, max_length: int = 255) -> str:
        """
        Generate a safe filename by removing invalid characters.

        Args:
            filename: Original filename
            max_length: Maximum filename length (default 255 for most filesystems)

        Returns:
            Safe filename
        """
        # Remove invalid characters for macOS/Linux
        invalid_chars = ['/', '\0']
        safe_name = filename

        for char in invalid_chars:
            safe_name = safe_name.replace(char, '_')

        # Truncate if too long
        if len(safe_name) > max_length:
            name, ext = os.path.splitext(safe_name)
            max_name_length = max_length - len(ext)
            safe_name = name[:max_name_length] + ext

        return safe_name
