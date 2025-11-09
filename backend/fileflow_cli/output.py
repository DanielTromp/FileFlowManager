"""
Output utilities for FileFlow CLI.

Handles TTY detection, pagination, JSON formatting, and consistent output.
"""

import json
import sys
from enum import IntEnum
from pathlib import Path
from typing import Any

from rich.console import Console
from rich.table import Table


class ExitCode(IntEnum):
    """Standard exit codes for CLI commands (CHK058)."""

    SUCCESS = 0
    GENERAL_ERROR = 1
    INVALID_USAGE = 2
    CONFIG_ERROR = 3
    FILE_NOT_FOUND = 4
    PERMISSION_ERROR = 5
    DATABASE_ERROR = 6
    OPERATION_CANCELLED = 7


class OutputFormat:
    """Handle different output formats based on context (CHK054)."""

    def __init__(self, force_color: bool = False, force_no_color: bool = False):
        """
        Initialize output formatter.

        Args:
            force_color: Force colored output even when piped
            force_no_color: Force plain output even in terminal
        """
        self.is_tty = sys.stdout.isatty()
        self.force_color = force_color
        self.force_no_color = force_no_color

        # Configure console based on TTY status
        self.console = Console(
            force_terminal=force_color,
            no_color=force_no_color or (not self.is_tty and not force_color),
            force_interactive=self.is_tty and not force_no_color,
        )

    @property
    def should_use_color(self) -> bool:
        """Determine if colored output should be used."""
        if self.force_no_color:
            return False
        if self.force_color:
            return True
        return self.is_tty

    @property
    def should_paginate(self) -> bool:
        """Determine if pagination should be used."""
        # Only paginate in interactive TTY sessions
        return self.is_tty and not self.force_no_color

    def print(self, *args, **kwargs) -> None:
        """Print with rich formatting if appropriate."""
        self.console.print(*args, **kwargs)

    def print_plain(self, text: str) -> None:
        """Print without any formatting (for piped output)."""
        print(text)


class JSONOutput:
    """Standardized JSON output format (CHK060)."""

    @staticmethod
    def success(
        data: Any,
        message: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Format successful response.

        Args:
            data: Response data
            message: Optional success message
            metadata: Optional metadata (timestamp, version, etc.)

        Returns:
            Standardized success response
        """
        response = {
            "success": True,
            "data": data,
        }

        if message:
            response["message"] = message

        if metadata:
            response["metadata"] = metadata

        return response

    @staticmethod
    def error(
        error: str,
        code: ExitCode = ExitCode.GENERAL_ERROR,
        details: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Format error response.

        Args:
            error: Error message
            code: Exit code
            details: Optional error details

        Returns:
            Standardized error response
        """
        response = {
            "success": False,
            "error": error,
            "error_code": code.value,
            "error_name": code.name,
        }

        if details:
            response["details"] = details

        return response

    @staticmethod
    def print(data: dict[str, Any], indent: int | None = 2) -> None:
        """
        Print JSON response to stdout.

        Args:
            data: Data to output
            indent: Indentation level (2 for pretty print, None for compact)
        """
        # Detect if output is piped - use compact JSON for piped output
        if not sys.stdout.isatty():
            indent = None

        print(json.dumps(data, indent=indent, default=str))


class Paginator:
    """Handle pagination for long outputs (CHK056)."""

    def __init__(
        self,
        items: list[Any],
        page_size: int | None = None,
        auto_detect: bool = True,
    ):
        """
        Initialize paginator.

        Args:
            items: List of items to paginate
            page_size: Items per page (auto-detected from terminal if None)
            auto_detect: Auto-detect terminal height for page size
        """
        self.items = items
        self.total_items = len(items)

        if page_size is None and auto_detect:
            # Auto-detect terminal height
            try:
                import shutil

                terminal_height = shutil.get_terminal_size().lines
                # Reserve lines for header/footer (subtract 5)
                self.page_size = max(10, terminal_height - 5)
            except Exception:
                self.page_size = 20  # Default fallback
        else:
            self.page_size = page_size or 20

        self.total_pages = (self.total_items + self.page_size - 1) // self.page_size

    def get_page(self, page_num: int) -> list[Any]:
        """
        Get items for a specific page.

        Args:
            page_num: Page number (1-indexed)

        Returns:
            List of items for the page
        """
        if page_num < 1 or page_num > self.total_pages:
            return []

        start_idx = (page_num - 1) * self.page_size
        end_idx = min(start_idx + self.page_size, self.total_items)
        return self.items[start_idx:end_idx]

    def get_all(self) -> list[Any]:
        """Get all items (no pagination)."""
        return self.items

    def format_footer(self, current_page: int) -> str:
        """
        Format pagination footer.

        Args:
            current_page: Current page number

        Returns:
            Formatted footer string
        """
        start = (current_page - 1) * self.page_size + 1
        end = min(current_page * self.page_size, self.total_items)

        return (
            f"Showing {start}-{end} of {self.total_items:,} items "
            f"(Page {current_page}/{self.total_pages})"
        )

    def should_paginate(self) -> bool:
        """Check if pagination is needed."""
        return self.total_items > self.page_size


def format_file_size(size_bytes: int) -> str:
    """
    Format file size in human-readable format.

    Args:
        size_bytes: Size in bytes

    Returns:
        Formatted size string (e.g., "1.5 MB")
    """
    size: float = float(size_bytes)
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if size < 1024.0:
            return f"{size:.1f} {unit}"
        size /= 1024.0
    return f"{size:.1f} PB"


def format_age(age_days: float) -> str:
    """
    Format file age in human-readable format.

    Args:
        age_days: Age in days

    Returns:
        Formatted age string (e.g., "3 months")
    """
    if age_days < 1:
        return "< 1 day"
    elif age_days < 30:
        return f"{int(age_days)} day{'s' if age_days != 1 else ''}"
    elif age_days < 365:
        months = int(age_days / 30)
        return f"{months} month{'s' if months > 1 else ''}"
    else:
        years = age_days / 365
        return f"{years:.1f} year{'s' if years >= 2 else ''}"


def format_path(
    path: str | Path, max_length: int | None = None, home_abbrev: bool = True
) -> str:
    """
    Format file path for display.

    Args:
        path: Path to format
        max_length: Maximum length (truncate if longer)
        home_abbrev: Replace home directory with ~

    Returns:
        Formatted path string
    """
    path_str = str(path)

    # Replace home directory with ~
    if home_abbrev:
        home = str(Path.home())
        if path_str.startswith(home):
            path_str = "~" + path_str[len(home) :]

    # Truncate if too long
    if max_length and len(path_str) > max_length:
        # Keep start and end, replace middle with ...
        keep = (max_length - 3) // 2
        path_str = path_str[:keep] + "..." + path_str[-keep:]

    return path_str


def create_table(
    headers: list[str],
    rows: list[list[str]],
    title: str | None = None,
    show_lines: bool = False,
) -> Table:
    """
    Create a rich Table with consistent styling.

    Args:
        headers: Column headers
        rows: Table rows
        title: Optional table title
        show_lines: Show lines between rows

    Returns:
        Configured Table instance
    """
    table = Table(
        show_header=True,
        header_style="bold cyan",
        title=title,
        title_style="bold",
        show_lines=show_lines,
    )

    for header in headers:
        table.add_column(header)

    for row in rows:
        table.add_row(*row)

    return table


def confirm_action(message: str, default: bool = False) -> bool:
    """
    Prompt user for confirmation (interactive mode only).

    Args:
        message: Confirmation message
        default: Default value if user presses Enter

    Returns:
        True if confirmed, False otherwise
    """
    # Non-interactive mode: use default
    if not sys.stdin.isatty() or not sys.stdout.isatty():
        return default

    default_str = "Y/n" if default else "y/N"
    response = input(f"{message} [{default_str}]: ").strip().lower()

    if not response:
        return default

    return response in ("y", "yes")
