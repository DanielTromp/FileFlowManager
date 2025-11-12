"""
File scanner module for FileFlow Manager.

Scans directories for files matching patterns with parallel processing.
Enhanced with progress tracking and cancellation support.
"""

import fnmatch
import os
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path

from fileflow_core.errors import OperationCancelledError, ScanError
from fileflow_core.models import FileMetadata, Rule
from fileflow_core.progress import ProgressTracker


class FileScanner:
    """Scan directories for files matching rules."""

    def __init__(self, max_workers: int = 4):
        """Initialize file scanner with thread pool."""
        self.max_workers = max_workers

    def scan_directory(
        self,
        directory: Path,
        patterns: list[str] | None = None,
        exclude_patterns: list[str] | None = None,
        recursive: bool = True,
        progress_callback: Callable[[str], None] | None = None,
        exclude_dirs: list[Path] | None = None,
        progress_tracker: ProgressTracker | None = None,
    ) -> list[FileMetadata]:
        """
        Scan a single directory for matching files.

        Args:
            directory: Directory to scan
            patterns: Filename patterns to match (default: ["*"])
            exclude_patterns: Filename patterns to exclude
            recursive: Whether to scan subdirectories
            progress_callback: Optional callback for progress updates (legacy)
            exclude_dirs: Directories to exclude from scan
            progress_tracker: Optional ProgressTracker for cancellation support

        Returns:
            List of file metadata for matching files

        Raises:
            OperationCancelledError: If progress_tracker is cancelled
            ScanError: If scanning fails critically
        """
        files = []
        patterns = patterns or ["*"]
        exclude_patterns = exclude_patterns or []
        exclude_dirs = exclude_dirs or []
        files_processed = 0

        try:
            if recursive:
                # Recursive scan
                for root, dirs, filenames in os.walk(directory):
                    # Remove excluded directories from dirs list to prevent os.walk from descending into them
                    root_path = Path(root)
                    dirs_to_remove = []
                    for dirname in dirs:
                        dir_path = root_path / dirname
                        # Check if this directory should be excluded
                        if any(dir_path == exclude_dir or dir_path.is_relative_to(exclude_dir) or exclude_dir.is_relative_to(dir_path) for exclude_dir in exclude_dirs):
                            dirs_to_remove.append(dirname)
                    for dirname in dirs_to_remove:
                        dirs.remove(dirname)

                    for filename in filenames:
                        # Update progress tracker (checks for cancellation)
                        if progress_tracker:
                            files_processed += 1
                            progress_tracker.update(
                                completed=files_processed,
                                current_item=filename,
                            )

                        # Legacy callback
                        if progress_callback:
                            progress_callback(filename)

                        # Check if matches any pattern
                        if not any(fnmatch.fnmatch(filename, pattern) for pattern in patterns):
                            continue

                        # Check if matches any exclude pattern
                        if any(fnmatch.fnmatch(filename, pattern) for pattern in exclude_patterns):
                            continue

                        file_path = Path(root) / filename
                        if file_path.is_file():
                            metadata = self._get_file_metadata(file_path)
                            if metadata:
                                files.append(metadata)
            else:
                # Non-recursive scan
                for item in directory.iterdir():
                    if not item.is_file():
                        continue

                    # Update progress tracker (checks for cancellation)
                    if progress_tracker:
                        files_processed += 1
                        progress_tracker.update(
                            completed=files_processed,
                            current_item=item.name,
                        )

                    # Legacy callback
                    if progress_callback:
                        progress_callback(item.name)

                    filename = item.name

                    # Check if matches any pattern
                    if not any(fnmatch.fnmatch(filename, pattern) for pattern in patterns):
                        continue

                    # Check if matches any exclude pattern
                    if any(fnmatch.fnmatch(filename, pattern) for pattern in exclude_patterns):
                        continue

                    metadata = self._get_file_metadata(item)
                    if metadata:
                        files.append(metadata)

        except OperationCancelledError:
            # User cancelled the operation
            raise
        except PermissionError as e:
            # Raise as ScanError with helpful message
            raise ScanError(
                f"Permission denied while scanning: {e}",
                directory=str(directory),
            )
        except Exception as e:
            # Raise as ScanError
            raise ScanError(
                f"Error scanning directory: {e}",
                directory=str(directory),
            )

        return files

    def scan_directories_parallel(
        self,
        directories: list[Path],
        patterns: list[str] | None = None,
        exclude_patterns: list[str] | None = None,
        recursive: bool = True,
        progress_callback: Callable[[str], None] | None = None,
        exclude_dirs: list[Path] | None = None,
        progress_tracker: ProgressTracker | None = None,
    ) -> list[FileMetadata]:
        """
        Scan multiple directories in parallel.

        Args:
            directories: Directories to scan
            patterns: Filename patterns to match
            exclude_patterns: Filename patterns to exclude
            recursive: Whether to scan subdirectories
            progress_callback: Optional callback for progress updates (legacy)
            exclude_dirs: Directories to exclude from scan
            progress_tracker: Optional ProgressTracker for cancellation support

        Returns:
            List of file metadata for matching files

        Raises:
            OperationCancelledError: If progress_tracker is cancelled
        """
        all_files = []

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = [
                executor.submit(
                    self.scan_directory,
                    directory,
                    patterns,
                    exclude_patterns,
                    recursive,
                    progress_callback,
                    exclude_dirs,
                    progress_tracker,
                )
                for directory in directories
            ]

            for future in as_completed(futures):
                try:
                    files = future.result()
                    all_files.extend(files)
                except OperationCancelledError:
                    # User cancelled, propagate
                    raise
                except Exception:
                    # Skip failed scans
                    pass

        return all_files

    def scan_for_rule(
        self,
        rule: Rule,
        expand_env_vars: Callable[[str], str],
        progress_callback: Callable[[str], None] | None = None,
        progress_tracker: ProgressTracker | None = None,
    ) -> list[FileMetadata]:
        """
        Scan directories for files matching a specific rule.

        Args:
            rule: Rule to match files against
            expand_env_vars: Function to expand environment variables in paths
            progress_callback: Optional callback for progress updates (legacy)
            progress_tracker: Optional ProgressTracker for cancellation support

        Returns:
            List of file metadata for files matching the rule

        Raises:
            OperationCancelledError: If progress_tracker is cancelled
        """
        # Expand environment variables in source directories
        directories = [Path(expand_env_vars(d)) for d in rule.source_directories]

        # Filter to only existing directories
        directories = [d for d in directories if d.exists() and d.is_dir()]

        if not directories:
            return []

        # Expand destination and check if we need to exclude it
        destination = Path(expand_env_vars(rule.destination))
        exclude_dirs_list = []

        # If destination is a subdirectory of any source, exclude it from scanning
        for source_dir in directories:
            try:
                # Check if destination is relative to this source directory
                destination.relative_to(source_dir)
                # Add destination to exclude list
                exclude_dirs_list.append(destination)
                break
            except ValueError:
                # destination is not a subdirectory of this source, continue
                pass

        # Scan with rule patterns
        files = self.scan_directories_parallel(
            directories,
            patterns=rule.source_patterns,
            exclude_patterns=rule.exclude_patterns,
            recursive=rule.recursive_search,
            progress_callback=progress_callback,
            exclude_dirs=exclude_dirs_list,
            progress_tracker=progress_tracker,
        )

        # Additional filtering based on rule constraints
        filtered_files = []
        for file_meta in files:
            # Check file type
            if file_meta.extension.lstrip(".") not in rule.file_types:
                continue

            # Check size constraints
            if rule.min_size_kb and file_meta.size_bytes < rule.min_size_kb * 1024:
                continue
            if rule.max_size_kb and file_meta.size_bytes > rule.max_size_kb * 1024:
                continue

            # Check age constraints
            if rule.min_age_days and file_meta.age_days < rule.min_age_days:
                continue
            if rule.max_age_days and file_meta.age_days > rule.max_age_days:
                continue

            # Mark as matched by this rule
            file_meta.matched_rules.append(rule.id)
            filtered_files.append(file_meta)

        return filtered_files

    def find_large_files(
        self,
        directories: list[Path],
        threshold_mb: int = 100,
        progress_callback: Callable[[str], None] | None = None,
        progress_tracker: ProgressTracker | None = None,
    ) -> list[FileMetadata]:
        """
        Find files larger than threshold, sorted by size (largest first).

        Args:
            directories: Directories to scan
            threshold_mb: Minimum file size in MB
            progress_callback: Optional callback for progress updates (legacy)
            progress_tracker: Optional ProgressTracker for cancellation support

        Returns:
            List of large files sorted by size (largest first)

        Raises:
            OperationCancelledError: If progress_tracker is cancelled
        """
        threshold_bytes = threshold_mb * 1024 * 1024

        all_files = self.scan_directories_parallel(
            directories,
            patterns=["*"],
            progress_callback=progress_callback,
            progress_tracker=progress_tracker,
        )

        large_files = [f for f in all_files if f.size_bytes >= threshold_bytes]

        # Sort by size, largest first
        large_files.sort(key=lambda f: f.size_bytes, reverse=True)

        return large_files

    def find_old_files(
        self,
        directories: list[Path],
        threshold_days: int = 90,
        file_types: list[str] | None = None,
        progress_callback: Callable[[str], None] | None = None,
        progress_tracker: ProgressTracker | None = None,
    ) -> list[FileMetadata]:
        """
        Find files older than threshold, sorted by age (oldest first).

        Args:
            directories: Directories to scan
            threshold_days: Minimum file age in days
            file_types: Optional list of file extensions to filter
            progress_callback: Optional callback for progress updates (legacy)
            progress_tracker: Optional ProgressTracker for cancellation support

        Returns:
            List of old files sorted by age (oldest first)

        Raises:
            OperationCancelledError: If progress_tracker is cancelled
        """
        all_files = self.scan_directories_parallel(
            directories,
            patterns=["*"],
            progress_callback=progress_callback,
            progress_tracker=progress_tracker,
        )

        # Filter by age
        old_files = [f for f in all_files if f.age_days >= threshold_days]

        # Filter by file type if specified
        if file_types:
            old_files = [
                f for f in old_files if f.extension.lstrip(".") in file_types
            ]

        # Sort by age, oldest first (T101)
        old_files.sort(key=lambda f: f.age_days, reverse=True)

        return old_files

    def _get_file_metadata(self, file_path: Path) -> FileMetadata | None:
        """Extract metadata from a file."""
        try:
            stats = file_path.stat()

            # Use birthtime (date added) on macOS/BSD, fallback to ctime on other systems
            # st_birthtime is more accurate for "when file was added to system"
            birthtime = getattr(stats, 'st_birthtime', stats.st_ctime)

            # Use the more recent of birthtime and mtime to avoid impossibly old dates
            # (e.g., files with birthtime set to Unix epoch 1970)
            created_timestamp = max(birthtime, stats.st_mtime)

            return FileMetadata(
                path=str(file_path.absolute()),
                filename=file_path.name,
                extension=file_path.suffix,
                size_bytes=stats.st_size,
                created_at=datetime.fromtimestamp(created_timestamp),
                modified_at=datetime.fromtimestamp(stats.st_mtime),
                checksum=None,  # Calculated on demand
                matched_rules=[],
            )
        except Exception:
            return None
