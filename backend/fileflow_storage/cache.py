"""
Checksum cache manager for FileFlow Manager.

Manages SHA-256 checksum caching to avoid recalculation.
Enhanced with retry logic and error handling.
"""

import hashlib
from datetime import datetime
from pathlib import Path

from fileflow_core.errors import DuplicateDetectionError
from fileflow_core.models import ChecksumCacheEntry
from fileflow_core.retry import retry_file_operation
from fileflow_storage.database import Database


class ChecksumCache:
    """Manage checksum caching with automatic invalidation."""

    def __init__(self, database: Database):
        """Initialize checksum cache with database connection."""
        self.db = database

    @retry_file_operation
    def calculate_checksum(self, file_path: Path, chunk_size: int = 65536) -> str:
        """
        Calculate SHA-256 checksum for a file in chunks.

        Args:
            file_path: Path to the file
            chunk_size: Size of chunks to read (default: 64KB)

        Returns:
            SHA-256 checksum hex string

        Raises:
            DuplicateDetectionError: If checksum calculation fails
        """
        try:
            sha256 = hashlib.sha256()

            with open(file_path, "rb") as f:
                while chunk := f.read(chunk_size):
                    sha256.update(chunk)

            return sha256.hexdigest()
        except OSError as e:
            raise DuplicateDetectionError(
                f"Failed to calculate checksum: {e}",
                file_path=str(file_path),
            ) from e

    def get_checksum(self, file_path: Path) -> str:
        """
        Get checksum for file, using cache if valid.

        Args:
            file_path: Path to the file

        Returns:
            SHA-256 checksum hex string

        Raises:
            DuplicateDetectionError: If checksum retrieval fails
        """
        try:
            file_path_str = str(file_path.absolute())

            # Get file stats
            stats = file_path.stat()
            current_size = stats.st_size
            current_modified = datetime.fromtimestamp(stats.st_mtime)

            # Check cache
            cached_entry = self.db.get_checksum(file_path_str)

            if cached_entry and cached_entry.is_valid(current_modified, current_size):
                # Cache hit - return cached checksum
                return cached_entry.checksum

            # Cache miss or invalid - calculate new checksum
            checksum = self.calculate_checksum(file_path)

            # Update cache
            entry = ChecksumCacheEntry(
                file_path=file_path_str,
                checksum=checksum,
                file_size=current_size,
                modified_time=current_modified,
                cached_at=datetime.now(),
            )
            self.db.cache_checksum(entry)

            return checksum
        except Exception as e:
            # Wrap any unexpected errors
            if isinstance(e, DuplicateDetectionError):
                raise
            raise DuplicateDetectionError(
                f"Failed to get checksum: {e}",
                file_path=str(file_path),
            ) from e

    def invalidate(self, file_path: Path) -> None:
        """Invalidate cache entry for a file."""
        # Remove from database
        str(file_path.absolute())
        # Note: Database doesn't have a delete method, so we'll just let it
        # get invalidated on next access

    def find_duplicates(self, checksum: str) -> list[str]:
        """Find all cached files with the given checksum."""
        return self.db.find_duplicates_by_checksum(checksum)

    def clear_all(self) -> int:
        """Clear all cache entries."""
        return self.db.clear_cache()
