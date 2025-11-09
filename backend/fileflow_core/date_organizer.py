"""
Date-based file organization for FileFlow Manager.

Extracts dates from filenames and generates date-based paths.
"""

import re
from datetime import datetime
from pathlib import Path


class DateOrganizer:
    """Extract dates from filenames and create date-based paths."""

    # macOS screenshot patterns
    SCREENSHOT_PATTERNS = [
        # "Screenshot 2025-11-03 at 10.30.45.png"
        r"Screenshot (\d{4})-(\d{2})-(\d{2}) at",
        # "Screen Shot 2025-11-03 at 2.30.45 PM.png"
        r"Screen Shot (\d{4})-(\d{2})-(\d{2}) at",
    ]

    @classmethod
    def extract_date_from_filename(cls, filename: str) -> datetime | None:
        """
        Extract date from screenshot filename.

        Returns datetime object or None if no date found.
        """
        for pattern in cls.SCREENSHOT_PATTERNS:
            match = re.search(pattern, filename)
            if match:
                year = int(match.group(1))
                month = int(match.group(2))
                day = int(match.group(3))
                return datetime(year, month, day)

        return None

    @classmethod
    def extract_date_from_file_metadata(cls, file_path: Path) -> datetime:
        """
        Extract date from file modification time as fallback.

        Returns datetime object.
        """
        stat = file_path.stat()
        return datetime.fromtimestamp(stat.st_mtime)

    @classmethod
    def generate_date_path(
        cls,
        base_path: str,
        date: datetime,
        template: str = "{year}/{month}/{day}",
    ) -> Path:
        """
        Generate date-based path structure.

        Args:
            base_path: Base destination directory
            date: Date to organize by
            template: Path template with {year}, {month}, {day} placeholders

        Returns:
            Full path with date structure
        """
        # Format components with zero padding
        replacements = {
            "{year}": f"{date.year:04d}",
            "{month}": f"{date.month:02d}",
            "{day}": f"{date.day:02d}",
            "{name}": "",  # Placeholder for future use
        }

        # Apply template
        date_part = template
        for placeholder, value in replacements.items():
            date_part = date_part.replace(placeholder, value)

        # Combine base path with date structure
        return Path(base_path) / date_part.strip("/")

    @classmethod
    def organize_file_by_date(
        cls,
        file_path: Path,
        destination_base: str,
        use_filename_date: bool = True,
    ) -> Path:
        """
        Determine destination path for file based on date.

        Args:
            file_path: Source file path
            destination_base: Base destination directory
            use_filename_date: Try to extract date from filename first

        Returns:
            Full destination path including filename
        """
        # Try to extract date from filename
        date = None
        if use_filename_date:
            date = cls.extract_date_from_filename(file_path.name)

        # Fallback to file modification time
        if date is None:
            date = cls.extract_date_from_file_metadata(file_path)

        # Generate date-based directory
        dest_dir = cls.generate_date_path(destination_base, date)

        # Combine with filename
        return dest_dir / file_path.name
