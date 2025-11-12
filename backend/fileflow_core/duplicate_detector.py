"""
Duplicate file detection for FileFlow Manager.

Uses SHA-256 checksums for accurate duplicate detection.
"""

from pathlib import Path

from fileflow_core.models import DuplicatePair, FileMetadata
from fileflow_storage.cache import ChecksumCache


class DuplicateDetector:
    """Detect duplicate files using checksum comparison."""

    def __init__(self, cache: ChecksumCache):
        """Initialize with checksum cache."""
        self.cache = cache

    def find_duplicates(
        self, files: list[FileMetadata]
    ) -> list[DuplicatePair]:
        """
        Find duplicate files in a list.

        Args:
            files: List of files to check for duplicates

        Returns:
            List of duplicate pairs
        """
        # Calculate checksums for all files
        checksum_map: dict[str, list[FileMetadata]] = {}

        for file in files:
            # Get or calculate checksum
            if file.checksum is None:
                file_path = Path(file.path)
                file.checksum = self.cache.get_checksum(file_path)

            # Group by checksum
            if file.checksum not in checksum_map:
                checksum_map[file.checksum] = []
            checksum_map[file.checksum].append(file)

        # Find duplicates (checksums with multiple files)
        duplicates: list[DuplicatePair] = []

        for checksum, file_list in checksum_map.items():
            if len(file_list) > 1:
                # Sort by modification time (oldest first)
                sorted_files = sorted(
                    file_list,
                    key=lambda f: f.modified_at,
                )

                # First file is the original, others are duplicates
                original = sorted_files[0]
                for duplicate in sorted_files[1:]:
                    duplicates.append(
                        DuplicatePair(
                            original_path=original.path,
                            duplicate_path=duplicate.path,
                            checksum=checksum,
                            file_size=original.size_bytes,
                        )
                    )

        return duplicates

    def is_duplicate(
        self, file1: Path, file2: Path
    ) -> tuple[bool, str, str]:
        """
        Check if two files are duplicates.

        Returns:
            (is_duplicate, checksum1, checksum2)
        """
        checksum1 = self.cache.get_checksum(file1)
        checksum2 = self.cache.get_checksum(file2)

        return checksum1 == checksum2, checksum1, checksum2

    def find_duplicate_in_destination(
        self, source_file: FileMetadata, destination: Path
    ) -> bool:
        """
        Check if source file already exists at destination.

        Returns:
            True if duplicate exists at destination
        """
        if not destination.exists():
            return False

        source_path = Path(source_file.path)
        is_dup, _, _ = self.is_duplicate(source_path, destination)

        return is_dup
