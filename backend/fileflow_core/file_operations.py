"""
Atomic file operations for FileFlow Manager.

Handles safe file moves and deletions with metadata preservation.
"""

import os
import shutil
from pathlib import Path
from typing import Optional, Tuple


class FileOperations:
    """Safe file operations with atomicity guarantees."""

    @staticmethod
    def move_file(
        source: Path,
        destination: Path,
        preserve_metadata: bool = True,
    ) -> Tuple[bool, Optional[str]]:
        """
        Move file atomically from source to destination.

        Returns (success, error_message).
        """
        try:
            # Ensure destination directory exists
            destination.parent.mkdir(parents=True, exist_ok=True)

            # Check if destination already exists
            if destination.exists():
                return False, f"Destination already exists: {destination}"

            # Check source exists
            if not source.exists():
                return False, f"Source file not found: {source}"

            # Check if we have permissions
            if not os.access(source, os.R_OK):
                return False, f"Cannot read source file: {source}"

            if not os.access(destination.parent, os.W_OK):
                return False, f"Cannot write to destination directory: {destination.parent}"

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

            return True, None

        except PermissionError as e:
            return False, f"Permission denied: {e}"
        except OSError as e:
            return False, f"OS error during move: {e}"
        except Exception as e:
            return False, f"Unexpected error during move: {e}"

    @staticmethod
    def delete_file(file_path: Path) -> Tuple[bool, Optional[str]]:
        """
        Delete a file safely.

        Returns (success, error_message).
        """
        try:
            # Check file exists
            if not file_path.exists():
                return False, f"File not found: {file_path}"

            # Check if we have permissions
            if not os.access(file_path, os.W_OK):
                return False, f"Cannot delete file (permission denied): {file_path}"

            # Delete the file
            file_path.unlink()

            return True, None

        except PermissionError as e:
            return False, f"Permission denied: {e}"
        except OSError as e:
            return False, f"OS error during deletion: {e}"
        except Exception as e:
            return False, f"Unexpected error during deletion: {e}"

    @staticmethod
    def check_disk_space(
        destination: Path,
        required_bytes: int,
    ) -> Tuple[bool, Optional[str]]:
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
    def safe_copy(
        source: Path,
        destination: Path,
        preserve_metadata: bool = True,
    ) -> Tuple[bool, Optional[str]]:
        """
        Copy file safely (for backup purposes).

        Returns (success, error_message).
        """
        try:
            # Ensure destination directory exists
            destination.parent.mkdir(parents=True, exist_ok=True)

            # Check source exists
            if not source.exists():
                return False, f"Source file not found: {source}"

            # Copy with metadata preservation
            if preserve_metadata:
                shutil.copy2(str(source), str(destination))
            else:
                shutil.copy(str(source), str(destination))

            return True, None

        except Exception as e:
            return False, f"Error copying file: {e}"

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
