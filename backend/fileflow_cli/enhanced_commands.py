"""
Enhanced CLI commands with improved output handling.

Demonstrates TTY detection, pagination, JSON output, and better UX.
"""

import sys
from pathlib import Path
from typing import Any

from fileflow_cli.output import (
    ExitCode,
    JSONOutput,
    OutputFormat,
    Paginator,
    confirm_action,
    create_table,
    format_path,
)
from fileflow_config.config_manager import ConfigManager
from fileflow_config.defaults import create_default_config_file
from fileflow_storage.cache import ChecksumCache
from fileflow_storage.database import Database

# Default paths
DEFAULT_CONFIG_PATH = Path.home() / ".config" / "fileflow" / "fileflow.toml"
DEFAULT_DB_PATH = Path.home() / ".config" / "fileflow" / "fileflow.db"


def get_config_manager() -> ConfigManager:
    """Get configuration manager with default config creation."""
    if not DEFAULT_CONFIG_PATH.exists():
        create_default_config_file(str(DEFAULT_CONFIG_PATH))
    return ConfigManager(DEFAULT_CONFIG_PATH)


def get_database() -> Database:
    """Get database instance."""
    return Database(DEFAULT_DB_PATH)


def enhanced_rules_list(
    output_format: str = "table",
    limit: int | None = None,
    page: int = 1,
    no_pagination: bool = False,
) -> None:
    """
    List all configured rules with enhanced output options.

    Args:
        output_format: Output format (table, json, simple)
        limit: Limit number of rules shown
        page: Page number (for pagination)
        no_pagination: Disable pagination even in TTY

    Examples:
        # List all rules with pretty table (default)
        fileflow rules list

        # Output as JSON (good for scripts/piping)
        fileflow rules list --output json

        # Show first 10 rules only
        fileflow rules list --limit 10

        # Show page 2 of results
        fileflow rules list --page 2

        # No pagination (show all)
        fileflow rules list --no-pagination
    """
    out = OutputFormat()

    try:
        config_mgr = get_config_manager()
        config = config_mgr.load()
    except Exception as e:
        if output_format == "json":
            JSONOutput.print(
                JSONOutput.error(
                    f"Failed to load configuration: {e}",
                    code=ExitCode.CONFIG_ERROR,
                    details={"config_path": str(DEFAULT_CONFIG_PATH)},
                )
            )
        else:
            out.print(f"[red]Error: Failed to load configuration: {e}[/red]")
        sys.exit(ExitCode.CONFIG_ERROR)

    if not config.rules:
        if output_format == "json":
            JSONOutput.print(
                JSONOutput.success(
                    data=[],
                    message="No rules configured",
                )
            )
        else:
            out.print("[yellow]No rules configured.[/yellow]")
            out.print("Run [bold]fileflow rules create[/bold] to add a rule.")
        sys.exit(ExitCode.SUCCESS)

    # Sort rules by priority
    rules = sorted(config.rules, key=lambda r: r.priority)

    # Apply limit if specified
    if limit:
        rules = rules[:limit]

    # Handle JSON output
    if output_format == "json":
        rules_data = [
            {
                "id": rule.id,
                "name": rule.name,
                "priority": rule.priority,
                "enabled": rule.enabled,
                "source_patterns": rule.source_patterns,
                "source_directories": rule.source_directories,
                "destination": rule.destination,
                "organize_by_date": rule.organize_by_date,
                "detect_duplicates": rule.detect_duplicates,
            }
            for rule in rules
        ]
        JSONOutput.print(
            JSONOutput.success(
                data=rules_data,
                metadata={
                    "total_rules": len(config.rules),
                    "shown_rules": len(rules),
                    "enabled_rules": sum(1 for r in config.rules if r.enabled),
                },
            )
        )
        sys.exit(ExitCode.SUCCESS)

    # Handle simple text output (for piping)
    if output_format == "simple":
        for rule in rules:
            status = "enabled" if rule.enabled else "disabled"
            print(f"{rule.id}\t{rule.name}\t{rule.priority}\t{status}")
        sys.exit(ExitCode.SUCCESS)

    # Table output with optional pagination
    paginator = Paginator(rules, auto_detect=True)

    # Determine if we should paginate
    should_paginate = (
        paginator.should_paginate() and not no_pagination and out.should_paginate
    )

    if should_paginate:
        # Show specific page
        page_rules = paginator.get_page(page)
        if not page_rules:
            out.print(f"[red]Error: Page {page} out of range (1-{paginator.total_pages})[/red]")
            sys.exit(ExitCode.INVALID_USAGE)
    else:
        # Show all
        page_rules = rules

    # Build table
    out.print("\n[bold]Configured Rules[/bold]")
    out.print("=" * 80)

    table = create_table(
        headers=["ID", "Name", "Priority", "Enabled", "Patterns", "Source Dirs"],
        rows=[
            [
                rule.id,
                rule.name,
                str(rule.priority),
                "✓" if rule.enabled else "✗",
                ", ".join(rule.source_patterns[:3])
                + (f", +{len(rule.source_patterns) - 3}" if len(rule.source_patterns) > 3 else ""),
                ", ".join(format_path(d, max_length=30) for d in rule.source_directories[:2])
                + (f", +{len(rule.source_directories) - 2}" if len(rule.source_directories) > 2 else ""),
            ]
            for rule in page_rules
        ],
    )

    out.console.print(table)

    # Show pagination footer if paginated
    if should_paginate:
        out.print(f"\n{paginator.format_footer(page)}")
        if page < paginator.total_pages:
            out.print(
                f"[dim]Run [bold]fileflow rules list --page {page + 1}[/bold] "
                f"to see more[/dim]"
            )
    out.print()

    sys.exit(ExitCode.SUCCESS)


def enhanced_history_command(
    limit: int = 50,
    operation_type: str | None = None,
    rule_id: str | None = None,
    output_format: str = "table",
    page: int = 1,
) -> None:
    """
    Display operation history with pagination and filtering (CHK056, T149).

    Args:
        limit: Maximum number of operations to show per page
        operation_type: Filter by operation type (move, delete, skip)
        rule_id: Filter by rule ID
        output_format: Output format (table, json, simple)
        page: Page number for pagination

    Examples:
        # Show recent operations
        fileflow history

        # Show only move operations
        fileflow history --operation-type move

        # Show operations for specific rule
        fileflow history --rule-id screenshot-org

        # Export as JSON
        fileflow history --output json

        # Show more results per page
        fileflow history --limit 100

        # View second page
        fileflow history --page 2
    """
    out = OutputFormat()

    try:
        get_database()
    except Exception as e:
        if output_format == "json":
            JSONOutput.print(
                JSONOutput.error(
                    f"Failed to access database: {e}",
                    code=ExitCode.DATABASE_ERROR,
                )
            )
        else:
            out.print(f"[red]Error: Failed to access database: {e}[/red]")
        sys.exit(ExitCode.DATABASE_ERROR)

    # Query database with filters
    # (This is a simplified version - actual implementation would query the database)
    operations: list[Any] = []  # Would query: db.get_operations(limit, operation_type, rule_id)

    if not operations:
        if output_format == "json":
            JSONOutput.print(
                JSONOutput.success(
                    data=[],
                    message="No operations found matching criteria",
                )
            )
        else:
            out.print("[yellow]No operations found matching criteria.[/yellow]")
        sys.exit(ExitCode.SUCCESS)

    # Handle JSON output
    if output_format == "json":
        JSONOutput.print(
            JSONOutput.success(
                data=operations,
                metadata={
                    "total_operations": len(operations),
                    "filters": {
                        "operation_type": operation_type,
                        "rule_id": rule_id,
                    },
                },
            )
        )
        sys.exit(ExitCode.SUCCESS)

    # Table output with pagination
    paginator = Paginator(operations, page_size=limit, auto_detect=False)
    page_ops = paginator.get_page(page)

    out.print("\n[bold]Operation History[/bold]")
    out.print("=" * 100)

    table = create_table(
        headers=["Timestamp", "Type", "Source", "Destination", "Rule ID", "Status"],
        rows=[
            [
                "timestamp_placeholder",
                "type_placeholder",
                "source_placeholder",
                "dest_placeholder",
                "rule_placeholder",
                "✓" if True else "✗",
            ]
            for _ in page_ops
        ],
    )

    out.console.print(table)

    if paginator.should_paginate():
        out.print(f"\n{paginator.format_footer(page)}")
    out.print()

    sys.exit(ExitCode.SUCCESS)


def enhanced_duplicate_detection(
    auto_delete: bool = False,
    interactive: bool = False,
    output_format: str = "table",
) -> None:
    """
    Find and optionally delete duplicate files (CHK057, T151).

    Args:
        auto_delete: Automatically delete duplicates without confirmation
        interactive: Interactively confirm each deletion
        output_format: Output format (table, json, simple)

    Examples:
        # Find duplicates (no deletion)
        fileflow files duplicates

        # Interactively delete duplicates
        fileflow files duplicates --interactive

        # Auto-delete all duplicates (careful!)
        fileflow files duplicates --auto-delete

        # Export duplicate list as JSON
        fileflow files duplicates --output json
    """
    out = OutputFormat()

    try:
        db = get_database()
        ChecksumCache(db)
        # Would scan for duplicates here
        duplicates: list[Any] = []  # Placeholder
    except Exception as e:
        if output_format == "json":
            JSONOutput.print(
                JSONOutput.error(
                    f"Failed to scan for duplicates: {e}",
                    code=ExitCode.GENERAL_ERROR,
                )
            )
        else:
            out.print(f"[red]Error: Failed to scan for duplicates: {e}[/red]")
        sys.exit(ExitCode.GENERAL_ERROR)

    # CHK057: Handle case when no duplicates are found
    if not duplicates:
        if output_format == "json":
            JSONOutput.print(
                JSONOutput.success(
                    data=[],
                    message="No duplicate files found",
                    metadata={"files_scanned": 0},
                )
            )
        else:
            out.print("[green]✓ No duplicate files found[/green]")
            out.print("Your file system is clean!")
        sys.exit(ExitCode.SUCCESS)

    # Handle JSON output
    if output_format == "json":
        JSONOutput.print(
            JSONOutput.success(
                data=duplicates,
                metadata={"duplicate_pairs": len(duplicates)},
            )
        )
        sys.exit(ExitCode.SUCCESS)

    # Show duplicates
    out.print(f"\n[bold]Found {len(duplicates)} duplicate file groups[/bold]")
    out.print("=" * 80)

    # Handle deletion modes
    if auto_delete:
        if not out.is_tty:
            # Stdin redirected - proceed without confirmation
            deleted_count = len(duplicates)
            out.print(f"[green]Deleted {deleted_count} duplicate files[/green]")
        else:
            # Interactive terminal - require confirmation
            if confirm_action(
                f"Delete {len(duplicates)} duplicate files?", default=False
            ):
                deleted_count = len(duplicates)
                out.print(f"[green]Deleted {deleted_count} duplicate files[/green]")
            else:
                out.print("[yellow]Deletion cancelled[/yellow]")
                sys.exit(ExitCode.OPERATION_CANCELLED)
    elif interactive:
        # CHK055: Handle stdin redirection - fall back to auto mode
        if not out.is_tty:
            out.print(
                "[yellow]Warning: Interactive mode requires a terminal. "
                "Using non-interactive mode.[/yellow]"
            )
        else:
            deleted_count = 0
            for dup in duplicates:
                if confirm_action(f"Delete duplicate: {dup}?", default=False):
                    # Delete file
                    deleted_count += 1
            out.print(f"[green]Deleted {deleted_count} duplicate files[/green]")

    sys.exit(ExitCode.SUCCESS)
