"""
File scanner module for FileFlow Manager.

Scans directories for files matching patterns with parallel processing.
"""

import fnmatch
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path
from typing import Callable, List, Optional

from fileflow_core.models import FileMetadata, Rule


class FileScanner:
    """Scan directories for files matching rules."""

    def __init__(self, max_workers: int = 4):
        """Initialize file scanner with thread pool."""
        self.max_workers = max_workers

    def scan_directory(
        self,
        directory: Path,
        patterns: Optional[List[str]] = None,
        exclude_patterns: Optional[List[str]] = None,
        recursive: bool = True,
        progress_callback: Optional[Callable[[str], None]] = None,
    ) -> List[FileMetadata]:
        """Scan a single directory for matching files."""
        files = []
        patterns = patterns or ["*"]
        exclude_patterns = exclude_patterns or []

        try:
            if recursive:
                # Recursive scan
                for root, _, filenames in os.walk(directory):
                    for filename in filenames:
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

        except PermissionError:
            # Skip directories without permission
            pass
        except Exception:
            # Skip problematic directories
            pass

        return files

    def scan_directories_parallel(
        self,
        directories: List[Path],
        patterns: Optional[List[str]] = None,
        exclude_patterns: Optional[List[str]] = None,
        progress_callback: Optional[Callable[[str], None]] = None,
    ) -> List[FileMetadata]:
        """Scan multiple directories in parallel."""
        all_files = []

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = [
                executor.submit(
                    self.scan_directory,
                    directory,
                    patterns,
                    exclude_patterns,
                    True,
                    progress_callback,
                )
                for directory in directories
            ]

            for future in as_completed(futures):
                try:
                    files = future.result()
                    all_files.extend(files)
                except Exception:
                    # Skip failed scans
                    pass

        return all_files

    def scan_for_rule(
        self,
        rule: Rule,
        expand_env_vars: Callable[[str], str],
        progress_callback: Optional[Callable[[str], None]] = None,
    ) -> List[FileMetadata]:
        """Scan directories for files matching a specific rule."""
        # Expand environment variables in source directories
        directories = [Path(expand_env_vars(d)) for d in rule.source_directories]

        # Filter to only existing directories
        directories = [d for d in directories if d.exists() and d.is_dir()]

        if not directories:
            return []

        # Scan with rule patterns
        files = self.scan_directories_parallel(
            directories,
            patterns=rule.source_patterns,
            exclude_patterns=rule.exclude_patterns,
            progress_callback=progress_callback,
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
        directories: List[Path],
        threshold_mb: int = 100,
        progress_callback: Optional[Callable[[str], None]] = None,
    ) -> List[FileMetadata]:
        """Find files larger than threshold, sorted by size (largest first)."""
        threshold_bytes = threshold_mb * 1024 * 1024

        all_files = self.scan_directories_parallel(
            directories,
            patterns=["*"],
            progress_callback=progress_callback,
        )

        large_files = [f for f in all_files if f.size_bytes >= threshold_bytes]

        # Sort by size, largest first
        large_files.sort(key=lambda f: f.size_bytes, reverse=True)

        return large_files

    def find_old_files(
        self,
        directories: List[Path],
        threshold_days: int = 90,
        file_types: Optional[List[str]] = None,
        progress_callback: Optional[Callable[[str], None]] = None,
    ) -> List[FileMetadata]:
        """Find files older than threshold, sorted by age (oldest first)."""
        all_files = self.scan_directories_parallel(
            directories,
            patterns=["*"],
            progress_callback=progress_callback,
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

    def _get_file_metadata(self, file_path: Path) -> Optional[FileMetadata]:
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
