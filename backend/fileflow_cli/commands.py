"""
Typer CLI commands for FileFlow Manager.
"""

import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Annotated, Any

import typer
from rich.console import Console
from rich.table import Table

from fileflow_cli.output import (
    ExitCode,
    JSONOutput,
    OutputFormat,
    Paginator,
    confirm_action,
    create_table,
    format_age,
    format_file_size,
    format_path,
)
from fileflow_config.config_manager import ConfigManager
from fileflow_config.defaults import create_default_config_file
from fileflow_core.models import OperationType
from fileflow_core.rule_engine import RuleEngine
from fileflow_storage.cache import ChecksumCache
from fileflow_storage.database import Database

app = typer.Typer(
    help="FileFlow Manager - Automated File Organization",
    pretty_exceptions_show_locals=False,
    add_completion=True  # T152: Enable shell completion support
)
console = Console()  # Keep for backward compatibility

# Default paths
DEFAULT_CONFIG_PATH = Path.home() / ".config" / "fileflow" / "fileflow.toml"
DEFAULT_DB_PATH = Path.home() / ".config" / "fileflow" / "fileflow.db"


def get_config_manager() -> ConfigManager:
    """Get configuration manager with default config creation."""
    if not DEFAULT_CONFIG_PATH.exists():
        console.print("[yellow]Creating default configuration...[/yellow]")
        create_default_config_file(str(DEFAULT_CONFIG_PATH))

    return ConfigManager(DEFAULT_CONFIG_PATH)


def get_database() -> Database:
    """Get database instance."""
    return Database(DEFAULT_DB_PATH)


def output_json(data: Any) -> None:
    """
    Output data as JSON (T153).

    Args:
        data: Data to output as JSON
    """
    print(json.dumps(data, indent=2, default=str))


@app.command()
def scan(
    output_format: Annotated[
        str,
        typer.Option("--output", "-o", help="Output format (table, json)")
    ] = "table",
) -> None:
    """
    Scan directories for files matching active rules and execute operations.

    This will scan your configured directories and immediately execute any
    matching file organization rules. Files will be moved/organized based
    on your active rules.

    Examples:
        # Scan and execute file organization
        fileflow scan

        # Scan with JSON output for scripting
        fileflow scan --output json
    """
    out = OutputFormat()
    dry_run = False  # Always execute for now

    try:
        # Setup
        config_mgr = get_config_manager()
        config = config_mgr.load()
        db = get_database()
        cache = ChecksumCache(db)
        engine = RuleEngine(db, cache, config_mgr.expand_env_vars)
    except Exception as e:
        if output_format == "json":
            JSONOutput.print(
                JSONOutput.error(
                    f"Failed to initialize scan: {e}",
                    code=ExitCode.CONFIG_ERROR,
                )
            )
        else:
            out.print(f"[red]Error: Failed to initialize scan: {e}[/red]")
        sys.exit(ExitCode.CONFIG_ERROR)

    # Use all enabled rules
    rule_list = config.rules

    # Run scan
    if output_format != "json":
        out.print("\n[bold]FileFlow Scan Results[/bold]")
        out.print("=" * 64)

    try:
        if output_format != "json":
            with out.console.status("[bold green]Scanning files..."):
                result = engine.scan(rule_list, dry_run=dry_run)
        else:
            result = engine.scan(rule_list, dry_run=dry_run)
    except Exception as e:
        if output_format == "json":
            JSONOutput.print(
                JSONOutput.error(f"Scan failed: {e}", code=ExitCode.GENERAL_ERROR)
            )
        else:
            out.print(f"[red]Error: Scan failed: {e}[/red]")
        sys.exit(ExitCode.GENERAL_ERROR)

    # Prepare operation counts
    move_count = sum(1 for op in result.planned_operations if op.operation_type.name == "MOVE")
    delete_count = sum(1 for op in result.planned_operations if op.operation_type.name == "DELETE")
    skip_count = sum(1 for op in result.planned_operations if op.operation_type.name == "SKIP")

    # Handle JSON output
    if output_format == "json":
        operations_data = [
            {
                "type": op.operation_type.name,
                "source_path": op.source_path,
                "destination_path": op.destination_path,
                "file_size": op.file_size,
                "skip_reason": op.skip_reason.value if op.skip_reason else None,
            }
            for op in result.planned_operations
        ]

        JSONOutput.print(
            JSONOutput.success(
                data={
                    "scan_duration_ms": result.scan_duration_ms,
                    "total_files_scanned": result.total_files_scanned,
                    "files_matched": result.files_matched,
                    "duplicates_found": len(result.duplicate_pairs),
                    "operations": operations_data,
                    "summary": {
                        "total_operations": len(result.planned_operations),
                        "move_operations": move_count,
                        "delete_operations": delete_count,
                        "skip_operations": skip_count,
                        "estimated_space_freed_mb": result.estimated_space_freed_mb,
                    },
                },
                message="Scan completed successfully",
            )
        )
        sys.exit(ExitCode.SUCCESS)

    # Display results (table format)
    out.print(f"\nScan completed in {result.scan_duration_ms / 1000:.1f}s\n")
    out.print(f"Files Scanned:     {result.total_files_scanned:,}")
    out.print(f"Files Matched:     {result.files_matched:,}")
    out.print(f"Duplicates Found:  {len(result.duplicate_pairs):,}")

    if result.planned_operations:
        out.print("\n[bold]Planned Operations[/bold]")
        out.print("-" * 64)

        # Show first 20 operations
        for op in result.planned_operations[:20]:
            op_type = op.operation_type.value.upper()
            source_name = Path(op.source_path).name

            if op.operation_type.name == "MOVE":
                out.print(f"[green]{op_type}[/green]    {source_name}")
                out.print(f"        → {op.destination_path}")
            elif op.operation_type.name == "DELETE":
                out.print(f"[red]{op_type}[/red]  {source_name} (duplicate)")
                out.print(f"        Space freed: {op.file_size / (1024*1024):.1f} MB")
            elif op.operation_type.name == "SKIP":
                out.print(f"[yellow]{op_type}[/yellow]    {source_name}")
                if op.skip_reason:
                    out.print(f"        ! {op.skip_reason.value}")

        if len(result.planned_operations) > 20:
            out.print(f"\n... [{len(result.planned_operations) - 20} more operations]")

    # Summary
    out.print("\n[bold]Summary[/bold]")
    out.print("-" * 64)
    out.print(f"Total operations:         {len(result.planned_operations)}")
    out.print(f"  Move operations:        {move_count}")
    out.print(f"  Delete operations:      {delete_count}")
    out.print(f"  Skipped:                {skip_count}")
    out.print(f"\nEstimated space freed:   {result.estimated_space_freed_mb:.1f} MB")

    if dry_run:
        out.print("\n[yellow]To execute these operations, run:[/yellow]")
        out.print("  [bold]fileflow scan --execute[/bold]\n")
    else:
        # Execute operations
        out.print("\n[bold green]Executing operations...[/bold green]")
        try:
            with out.console.status("[bold green]Processing files..."):
                executed = engine.execute(result.planned_operations)

            success_count = sum(1 for op in executed if op.success)
            out.print(f"\n[green]✓ Successfully processed {success_count} files[/green]\n")
        except Exception as e:
            out.print(f"[red]Error during execution: {e}[/red]")
            sys.exit(ExitCode.GENERAL_ERROR)

    sys.exit(ExitCode.SUCCESS)


@app.command()
def detect_screenshots() -> None:
    """Auto-detect macOS screenshot location."""
    try:
        result = subprocess.run(
            ["defaults", "read", "com.apple.screencapture", "location"],
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            location = result.stdout.strip()
            console.print("[bold]Screenshot Location Detection[/bold]")
            console.print("=" * 64)
            console.print(f"\nDetected location: [cyan]{location}[/cyan]")
            console.print("Method: macOS system preferences")
            console.print("Confidence: High")
        else:
            console.print("[yellow]Using default location: ~/Desktop[/yellow]")
    except Exception:
        console.print("[yellow]Could not detect screenshot location. Using default: ~/Desktop[/yellow]")


# Create a rules subcommand group
rules_app = typer.Typer(help="Manage file organization rules")
app.add_typer(rules_app, name="rules")


@rules_app.command("list")
def rules_list(
    output_format: Annotated[
        str,
        typer.Option("--output", "-o", help="Output format (table, json, simple)")
    ] = "table",
    limit: Annotated[
        int | None,
        typer.Option("--limit", "-l", help="Limit number of rules shown")
    ] = None,
    page: Annotated[
        int,
        typer.Option("--page", "-p", help="Page number (for pagination)")
    ] = 1,
    no_pagination: Annotated[
        bool,
        typer.Option("--no-pagination", help="Disable pagination")
    ] = False,
) -> None:
    """
    List all configured rules.

    Examples:
        # List all rules with pretty table
        fileflow rules list

        # Output as JSON (good for scripts)
        fileflow rules list --output json

        # Show first 5 rules only
        fileflow rules list --limit 5

        # View page 2 of results
        fileflow rules list --page 2
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
                )
            )
        else:
            out.print(f"[red]Error: Failed to load configuration: {e}[/red]")
        sys.exit(ExitCode.CONFIG_ERROR)

    if not config.rules:
        if output_format == "json":
            JSONOutput.print(
                JSONOutput.success(data=[], message="No rules configured")
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
            }
            for rule in rules
        ]
        JSONOutput.print(
            JSONOutput.success(
                data=rules_data,
                metadata={
                    "total_rules": len(config.rules),
                    "shown_rules": len(rules),
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
    should_paginate = (
        paginator.should_paginate() and not no_pagination and out.should_paginate
    )

    if should_paginate:
        page_rules = paginator.get_page(page)
        if not page_rules:
            out.print(f"[red]Error: Page {page} out of range (1-{paginator.total_pages})[/red]")
            sys.exit(ExitCode.INVALID_USAGE)
    else:
        page_rules = rules

    out.print("\n[bold]Configured Rules[/bold]")
    out.print("=" * 80)

    rows = []
    for rule in page_rules:
        enabled_str = "✓" if rule.enabled else "✗"
        patterns = ", ".join(rule.source_patterns[:3])
        if len(rule.source_patterns) > 3:
            patterns += f", +{len(rule.source_patterns) - 3}"

        source_dirs = ", ".join(format_path(d, max_length=30) for d in rule.source_directories[:2])
        if len(rule.source_directories) > 2:
            source_dirs += f", +{len(rule.source_directories) - 2}"

        rows.append([
            rule.id,
            rule.name,
            str(rule.priority),
            enabled_str,
            patterns,
            source_dirs,
        ])

    table = create_table(
        headers=["ID", "Name", "Priority", "Enabled", "Patterns", "Source Dirs"],
        rows=rows,
    )

    out.console.print(table)

    if should_paginate:
        out.print(f"\n{paginator.format_footer(page)}")
        if page < paginator.total_pages:
            out.print(
                f"[dim]Run [bold]fileflow rules list --page {page + 1}[/bold] to see more[/dim]"
            )
    out.print()

    sys.exit(ExitCode.SUCCESS)


@rules_app.command("show")
def rules_show(
    rule_id: Annotated[str, typer.Argument(help="Rule ID to display")],
    output_format: Annotated[
        str,
        typer.Option("--output", "-o", help="Output format (text, json)")
    ] = "text",
) -> None:
    """
    Show detailed information about a specific rule.

    Examples:
        # Show rule details
        fileflow rules show screenshot-org

        # Export as JSON
        fileflow rules show screenshot-org --output json
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
                )
            )
        else:
            out.print(f"[red]Error: Failed to load configuration: {e}[/red]")
        sys.exit(ExitCode.CONFIG_ERROR)

    rule = next((r for r in config.rules if r.id == rule_id), None)
    if not rule:
        if output_format == "json":
            JSONOutput.print(
                JSONOutput.error(
                    f"Rule '{rule_id}' not found",
                    code=ExitCode.FILE_NOT_FOUND,
                )
            )
        else:
            out.print(f"[red]Error: Rule '{rule_id}' not found.[/red]")
        sys.exit(ExitCode.FILE_NOT_FOUND)

    # Handle JSON output
    if output_format == "json":
        rule_data = {
            "id": rule.id,
            "name": rule.name,
            "priority": rule.priority,
            "enabled": rule.enabled,
            "source_directories": rule.source_directories,
            "source_patterns": rule.source_patterns,
            "exclude_patterns": rule.exclude_patterns,
            "destination": rule.destination,
            "organize_by_date": rule.organize_by_date,
            "detect_duplicates": rule.detect_duplicates,
            "file_types": rule.file_types,
            "min_size_kb": rule.min_size_kb,
            "max_size_kb": rule.max_size_kb,
            "min_age_days": rule.min_age_days,
            "max_age_days": rule.max_age_days,
        }
        JSONOutput.print(JSONOutput.success(data=rule_data))
        sys.exit(ExitCode.SUCCESS)

    out.print(f"\n[bold]Rule: {rule.name}[/bold]")
    out.print("=" * 80)
    out.print(f"ID:               {rule.id}")
    out.print(f"Priority:         {rule.priority}")
    out.print(f"Enabled:          {'Yes' if rule.enabled else 'No'}")
    out.print("\n[bold]Source:[/bold]")
    out.print(f"  Directories:    {', '.join(rule.source_directories)}")
    out.print(f"  Patterns:       {', '.join(rule.source_patterns)}")
    if rule.exclude_patterns:
        out.print(f"  Exclude:        {', '.join(rule.exclude_patterns)}")
    if rule.file_types:
        out.print(f"  File Types:     {', '.join(rule.file_types)}")
    out.print("\n[bold]Destination:[/bold]")
    out.print(f"  Path:           {rule.destination}")
    if rule.organize_by_date:
        out.print("  Organize:       By date (YYYY/MM/DD)")
    if rule.min_size_kb or rule.max_size_kb:
        out.print("\n[bold]Size Constraints:[/bold]")
        if rule.min_size_kb:
            out.print(f"  Minimum:        {rule.min_size_kb} KB")
        if rule.max_size_kb:
            out.print(f"  Maximum:        {rule.max_size_kb} KB")
    if rule.min_age_days or rule.max_age_days:
        out.print("\n[bold]Age Constraints:[/bold]")
        if rule.min_age_days:
            out.print(f"  Minimum:        {rule.min_age_days} days")
        if rule.max_age_days:
            out.print(f"  Maximum:        {rule.max_age_days} days")
    out.print()
    sys.exit(ExitCode.SUCCESS)


@rules_app.command("create")
def rules_create() -> None:
    """Create a new rule interactively."""
    from fileflow_config.rule_schema import RuleValidator
    from fileflow_core.models import Rule

    console.print("\n[bold]Create New Rule[/bold]")
    console.print("=" * 80)

    # Get rule name
    name = typer.prompt("Rule name")
    rule_id = RuleValidator.sanitize_rule_id(name)
    console.print(f"Generated ID: {rule_id}")

    # Check if rule ID already exists
    config_mgr = get_config_manager()
    config = config_mgr.load()
    if any(r.id == rule_id for r in config.rules):
        console.print(f"[red]Error: Rule with ID '{rule_id}' already exists.[/red]")
        return

    # Get source directories
    source_dirs_str = typer.prompt("Source directories (comma-separated)", default="${DOWNLOADS}")
    source_directories = [d.strip() for d in source_dirs_str.split(",")]

    # Get patterns
    patterns_str = typer.prompt("File patterns (comma-separated)", default="*")
    source_patterns = [p.strip() for p in patterns_str.split(",")]

    # Get destination
    destination = typer.prompt("Destination directory")

    # Get priority
    priority = typer.prompt("Priority (1-1000, lower runs first)", default="500", type=int)

    # Create rule
    description = typer.prompt("Description (optional)", default="")
    new_rule = Rule(
        id=rule_id,
        name=name,
        description=description or f"Rule for organizing {name}",
        priority=priority,
        enabled=True,
        source_directories=source_directories,
        source_patterns=source_patterns,
        destination=destination,
        file_types=[],
        exclude_patterns=[],
        organize_by_date=False,
        detect_duplicates=False,
        min_size_kb=None,
        max_size_kb=None,
        min_age_days=None,
        max_age_days=None,
    )

    # Validate rule
    valid, errors = RuleValidator.validate_rule(new_rule, check_filesystem=True)
    if not valid:
        console.print("\n[red]Validation errors:[/red]")
        for error in errors:
            console.print(f"  • {error}")
        console.print("\n[yellow]Rule not created.[/yellow]")
        return

    # Add to configuration
    config.rules.append(new_rule)
    config_mgr.save(config)

    console.print(f"\n[green]✓ Rule '{name}' created successfully![/green]")
    console.print("Run [bold]fileflow scan[/bold] to apply this rule.\n")


@rules_app.command("update")
def rules_update(rule_id: Annotated[str, typer.Argument(help="Rule ID to update")]) -> None:
    """Update an existing rule."""
    config_mgr = get_config_manager()
    config = config_mgr.load()

    rule = next((r for r in config.rules if r.id == rule_id), None)
    if not rule:
        console.print(f"[red]Error: Rule '{rule_id}' not found.[/red]")
        return

    console.print(f"\n[bold]Update Rule: {rule.name}[/bold]")
    console.print("=" * 80)
    console.print("[dim]Press Enter to keep current value[/dim]\n")

    # Update fields
    new_name = typer.prompt("Name", default=rule.name)
    if new_name != rule.name:
        rule.name = new_name

    new_priority = typer.prompt("Priority", default=str(rule.priority), type=int)
    if new_priority != rule.priority:
        rule.priority = new_priority

    # Source directories
    current_dirs = ", ".join(rule.source_directories)
    new_dirs_str = typer.prompt("Source directories", default=current_dirs)
    if new_dirs_str != current_dirs:
        rule.source_directories = [d.strip() for d in new_dirs_str.split(",")]

    # Patterns
    current_patterns = ", ".join(rule.source_patterns)
    new_patterns_str = typer.prompt("File patterns", default=current_patterns)
    if new_patterns_str != current_patterns:
        rule.source_patterns = [p.strip() for p in new_patterns_str.split(",")]

    # Destination
    new_dest = typer.prompt("Destination", default=rule.destination)
    if new_dest != rule.destination:
        rule.destination = new_dest

    # Save
    config_mgr.save(config)
    console.print(f"\n[green]✓ Rule '{rule.name}' updated successfully![/green]\n")


@rules_app.command("delete")
def rules_delete(
    rule_id: Annotated[str, typer.Argument(help="Rule ID to delete")],
    yes: Annotated[
        bool,
        typer.Option("--yes", "-y", help="Skip confirmation prompt")
    ] = False,
) -> None:
    """
    Delete a rule.

    Examples:
        # Delete with confirmation
        fileflow rules delete screenshot-org

        # Skip confirmation
        fileflow rules delete screenshot-org --yes
    """
    out = OutputFormat()

    try:
        config_mgr = get_config_manager()
        config = config_mgr.load()
    except Exception as e:
        out.print(f"[red]Error: Failed to load configuration: {e}[/red]")
        sys.exit(ExitCode.CONFIG_ERROR)

    rule = next((r for r in config.rules if r.id == rule_id), None)
    if not rule:
        out.print(f"[red]Error: Rule '{rule_id}' not found.[/red]")
        sys.exit(ExitCode.FILE_NOT_FOUND)

    # Confirm deletion
    if not yes:
        if not confirm_action(f"Delete rule '{rule.name}'?", default=False):
            out.print("[yellow]Deletion cancelled.[/yellow]")
            sys.exit(ExitCode.OPERATION_CANCELLED)

    # Delete rule
    config.rules = [r for r in config.rules if r.id != rule_id]
    config_mgr.save(config)

    out.print(f"[green]✓ Rule '{rule.name}' deleted successfully.[/green]")
    sys.exit(ExitCode.SUCCESS)


@rules_app.command("enable")
def rules_enable(rule_id: Annotated[str, typer.Argument(help="Rule ID to enable")]) -> None:
    """Enable a rule."""
    config_mgr = get_config_manager()
    config = config_mgr.load()

    rule = next((r for r in config.rules if r.id == rule_id), None)
    if not rule:
        console.print(f"[red]Error: Rule '{rule_id}' not found.[/red]")
        return

    if rule.enabled:
        console.print(f"[yellow]Rule '{rule.name}' is already enabled.[/yellow]")
        return

    rule.enabled = True
    config_mgr.save(config)
    console.print(f"[green]✓ Rule '{rule.name}' enabled![/green]")


@rules_app.command("disable")
def rules_disable(rule_id: Annotated[str, typer.Argument(help="Rule ID to disable")]) -> None:
    """Disable a rule."""
    config_mgr = get_config_manager()
    config = config_mgr.load()

    rule = next((r for r in config.rules if r.id == rule_id), None)
    if not rule:
        console.print(f"[red]Error: Rule '{rule_id}' not found.[/red]")
        return

    if not rule.enabled:
        console.print(f"[yellow]Rule '{rule.name}' is already disabled.[/yellow]")
        return

    rule.enabled = False
    config_mgr.save(config)
    console.print(f"[green]✓ Rule '{rule.name}' disabled![/green]")


@app.command(name="find-large")
def find_large(
    output_format: Annotated[
        str,
        typer.Option("--output", "-o", help="Output format (table, json)")
    ] = "table",
    threshold: Annotated[
        int,
        typer.Option("--threshold", "-t", help="Size threshold in MB")
    ] = 100,
) -> None:
    """
    Find files larger than specified threshold (default: 100MB).

    Examples:
        # Find files larger than 100MB
        fileflow find-large

        # Find files larger than 500MB
        fileflow find-large --threshold 500

        # Output as JSON
        fileflow find-large --output json
    """
    from pathlib import Path

    from fileflow_core.file_scanner import FileScanner

    out = OutputFormat()

    try:
        # Get monitored directories from config
        config_mgr = get_config_manager()
        config = config_mgr.load()
        monitored_dirs = [Path(config_mgr.expand_env_vars(d)) for d in config.paths.monitored_directories]
    except Exception as e:
        if output_format == "json":
            JSONOutput.print(
                JSONOutput.error(
                    f"Failed to load configuration: {e}",
                    code=ExitCode.CONFIG_ERROR,
                )
            )
        else:
            out.print(f"[red]Error: Failed to load configuration: {e}[/red]")
        sys.exit(ExitCode.CONFIG_ERROR)

    try:
        # Scan for large files
        scanner = FileScanner()
        large_files = scanner.find_large_files(directories=monitored_dirs, threshold_mb=threshold)
    except Exception as e:
        if output_format == "json":
            JSONOutput.print(
                JSONOutput.error(f"Scan failed: {e}", code=ExitCode.GENERAL_ERROR)
            )
        else:
            out.print(f"[red]Error: Scan failed: {e}[/red]")
        sys.exit(ExitCode.GENERAL_ERROR)

    # Handle JSON output
    if output_format == "json":
        JSONOutput.print(
            JSONOutput.success(
                data=[
                    {
                        "filename": f.filename,
                        "path": f.path,
                        "size_bytes": f.size_bytes,
                        "size_mb": f.size_bytes / (1024 * 1024),
                        "age_days": f.age_days,
                    }
                    for f in large_files
                ],
                metadata={
                    "threshold_mb": threshold,
                    "files_found": len(large_files),
                    "total_size_mb": sum(f.size_bytes for f in large_files) / (1024 * 1024),
                },
                message=f"Found {len(large_files)} files larger than {threshold}MB" if large_files else f"No files found larger than {threshold}MB",
            )
        )
        sys.exit(ExitCode.SUCCESS)

    # Table output (default)
    out.print(f"\n[bold]Finding files larger than {threshold} MB...[/bold]\n")

    if not large_files:
        out.print(f"[green]✓ No files found larger than {threshold} MB.[/green]")
        sys.exit(ExitCode.SUCCESS)

    # Display results
    table = create_table(
        headers=["File", "Size", "Path"],
        rows=[
            [
                file_meta.filename,
                format_file_size(file_meta.size_bytes),
                format_path(Path(file_meta.path).parent, max_length=50),
            ]
            for file_meta in large_files[:20]
        ],
        title=f"Large Files (> {threshold} MB)",
    )

    out.console.print(table)

    # Summary
    total_size = sum(f.size_bytes for f in large_files) / (1024 * 1024)
    out.print(f"\n[bold]Found {len(large_files)} files, total size: {total_size:.2f} MB[/bold]")

    if len(large_files) > 20:
        out.print(f"[dim]Showing first 20 of {len(large_files)} files[/dim]\n")
    else:
        out.print()

    sys.exit(ExitCode.SUCCESS)


@app.command(name="find-old")
def find_old(
    output_format: Annotated[
        str,
        typer.Option("--output", "-o", help="Output format (table, json)")
    ] = "table",
    threshold: Annotated[
        int,
        typer.Option("--threshold", "-t", help="Age threshold in days")
    ] = 90,
) -> None:
    """
    Find files older than specified threshold (default: 90 days).

    Examples:
        # Find files older than 90 days
        fileflow find-old

        # Find files older than 180 days (6 months)
        fileflow find-old --threshold 180

        # Output as JSON
        fileflow find-old --output json
    """
    from pathlib import Path

    from fileflow_core.file_scanner import FileScanner

    out = OutputFormat()

    try:
        # Get monitored directories from config
        config_mgr = get_config_manager()
        config = config_mgr.load()
        monitored_dirs = [Path(config_mgr.expand_env_vars(d)) for d in config.paths.monitored_directories]
    except Exception as e:
        if output_format == "json":
            JSONOutput.print(
                JSONOutput.error(
                    f"Failed to load configuration: {e}",
                    code=ExitCode.CONFIG_ERROR,
                )
            )
        else:
            out.print(f"[red]Error: Failed to load configuration: {e}[/red]")
        sys.exit(ExitCode.CONFIG_ERROR)

    try:
        # Scan for old files
        scanner = FileScanner()
        old_files = scanner.find_old_files(
            directories=monitored_dirs,
            threshold_days=threshold,
        )
    except Exception as e:
        if output_format == "json":
            JSONOutput.print(
                JSONOutput.error(f"Scan failed: {e}", code=ExitCode.GENERAL_ERROR)
            )
        else:
            out.print(f"[red]Error: Scan failed: {e}[/red]")
        sys.exit(ExitCode.GENERAL_ERROR)

    # Calculate statistics
    total_size_mb = sum(f.size_bytes for f in old_files) / (1024 * 1024) if old_files else 0
    avg_age_days = sum(f.age_days for f in old_files if f.age_days) / len(old_files) if old_files else 0

    # Handle JSON output
    if output_format == "json":
        JSONOutput.print(
            JSONOutput.success(
                data=[
                    {
                        "filename": f.filename,
                        "path": f.path,
                        "size_bytes": f.size_bytes,
                        "size_mb": f.size_bytes / (1024 * 1024),
                        "age_days": f.age_days,
                    }
                    for f in old_files
                ],
                metadata={
                    "threshold_days": threshold,
                    "files_found": len(old_files),
                    "total_size_mb": total_size_mb,
                    "average_age_days": avg_age_days,
                },
                message=f"Found {len(old_files)} files older than {threshold} days" if old_files else f"No files found older than {threshold} days",
            )
        )
        sys.exit(ExitCode.SUCCESS)

    # Table output (default)
    out.print(f"\n[bold]Finding files older than {threshold} days...[/bold]\n")

    if not old_files:
        out.print(f"[green]✓ No files found older than {threshold} days.[/green]")
        sys.exit(ExitCode.SUCCESS)

    # Display results in table
    table = create_table(
        headers=["File", "Age", "Size", "Path"],
        rows=[
            [
                file_meta.filename,
                format_age(file_meta.age_days) if file_meta.age_days else "N/A",
                format_file_size(file_meta.size_bytes),
                format_path(Path(file_meta.path).parent, max_length=40),
            ]
            for file_meta in old_files[:20]
        ],
        title=f"Old Files (> {threshold} days)",
    )

    out.console.print(table)

    # Summary
    out.print(f"\n[bold]Found {len(old_files)} files, total size: {total_size_mb:.2f} MB[/bold]")
    out.print(f"[bold]Average age: {avg_age_days:.0f} days ({avg_age_days/365:.1f} years)[/bold]")

    if len(old_files) > 20:
        out.print(f"[dim]Showing first 20 of {len(old_files)} files[/dim]\n")
    else:
        out.print()

    sys.exit(ExitCode.SUCCESS)


# Configuration Management Commands

@app.command(name="config-show")
def config_show(
    output_format: Annotated[
        str,
        typer.Option("--output", "-o", help="Output format (table, json)")
    ] = "table",
) -> None:
    """
    Show current configuration.

    Examples:
        # Show configuration
        fileflow config-show

        # Output as JSON
        fileflow config-show --output json
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
                )
            )
        else:
            out.print(f"[red]Error: Failed to load configuration: {e}[/red]")
        sys.exit(ExitCode.CONFIG_ERROR)

    # Handle JSON output
    if output_format == "json":
        JSONOutput.print(
            JSONOutput.success(
                data={
                    "general": {
                        "log_level": config.general.log_level,
                        "auto_run_on_startup": config.general.auto_run_on_startup,
                        "auto_run_interval_minutes": config.general.auto_run_interval_minutes,
                        "enable_notifications": config.general.enable_notifications,
                        "cache_enabled": config.general.cache_enabled,
                    },
                    "paths": {
                        "screenshot_source": config.paths.screenshot_source,
                        "screenshot_destination": config.paths.screenshot_destination,
                        "monitored_directories": config.paths.monitored_directories,
                    },
                    "rules": [
                        {
                            "id": rule.id,
                            "name": rule.name,
                            "enabled": rule.enabled,
                            "priority": rule.priority,
                        }
                        for rule in config.rules
                    ],
                },
                metadata={"rules_count": len(config.rules)},
            )
        )
        sys.exit(ExitCode.SUCCESS)

    # Table output (default)
    out.print("\n[bold]Current Configuration[/bold]\n")

    # General settings
    out.print("[bold cyan]General Settings[/bold cyan]")
    out.print(f"  Log level: {config.general.log_level}")
    out.print(f"  Auto-run on startup: {config.general.auto_run_on_startup}")
    out.print(f"  Auto-run interval: {config.general.auto_run_interval_minutes} minutes")
    out.print(f"  Notifications: {config.general.enable_notifications}")
    out.print(f"  Cache: {config.general.cache_enabled}")

    # Paths
    out.print("\n[bold cyan]Paths[/bold cyan]")
    out.print(f"  Screenshot source: {config.paths.screenshot_source}")
    out.print(f"  Screenshot destination: {config.paths.screenshot_destination}")
    if config.paths.monitored_directories:
        out.print(f"  Monitored directories: {', '.join(config.paths.monitored_directories)}")

    # Rules
    out.print(f"\n[bold cyan]Rules ({len(config.rules)})[/bold cyan]")
    for rule in config.rules:
        status = "✓" if rule.enabled else "✗"
        out.print(f"  [{status}] {rule.name} ({rule.id})")

    out.print()
    sys.exit(ExitCode.SUCCESS)


@app.command(name="config-export")
def config_export(
    output_path: Annotated[str, typer.Argument(help="Path where to save the exported configuration")],
) -> None:
    """
    Export configuration to TOML file.

    Examples:
        # Export configuration
        fileflow config-export ~/backup/config.toml
    """
    out = OutputFormat()

    out.print(f"\n[bold]Exporting configuration to {output_path}...[/bold]\n")

    try:
        config_mgr = get_config_manager()
        config_mgr.export(output_path)
        out.print("[green]✓ Configuration exported successfully[/green]\n")
        sys.exit(ExitCode.SUCCESS)
    except Exception as e:
        out.print(f"[red]Error: {e}[/red]")
        sys.exit(ExitCode.GENERAL_ERROR)


@app.command(name="config-import")
def config_import(
    input_path: Annotated[str, typer.Argument(help="Path to configuration file to import")],
) -> None:
    """
    Import configuration from TOML file (replaces existing configuration).

    Examples:
        # Import configuration (replaces existing)
        fileflow config-import ~/backup/config.toml
    """
    out = OutputFormat()

    out.print(f"\n[bold]Importing configuration from {input_path} (replace mode)...[/bold]\n")

    try:
        config_mgr = get_config_manager()
        config_mgr.import_config(input_path, merge=False)
        out.print("[green]✓ Configuration imported successfully[/green]\n")
        sys.exit(ExitCode.SUCCESS)
    except FileNotFoundError:
        out.print(f"[red]Error: File not found: {input_path}[/red]")
        sys.exit(ExitCode.FILE_NOT_FOUND)
    except Exception as e:
        out.print(f"[red]Error: {e}[/red]")
        sys.exit(ExitCode.GENERAL_ERROR)


@app.command(name="config-import-merge")
def config_import_merge(
    input_path: Annotated[str, typer.Argument(help="Path to configuration file to import")],
) -> None:
    """
    Import configuration with merge (keeps existing rules, adds new ones).

    Examples:
        # Merge configuration (keeps existing rules)
        fileflow config-import-merge ~/backup/config.toml
    """
    out = OutputFormat()

    out.print(f"\n[bold]Importing configuration from {input_path} (merge mode)...[/bold]\n")

    try:
        config_mgr = get_config_manager()
        config_mgr.import_config(input_path, merge=True)
        out.print("[green]✓ Configuration merged successfully[/green]\n")
        sys.exit(ExitCode.SUCCESS)
    except FileNotFoundError:
        out.print(f"[red]Error: File not found: {input_path}[/red]")
        sys.exit(ExitCode.FILE_NOT_FOUND)
    except Exception as e:
        out.print(f"[red]Error: {e}[/red]")
        sys.exit(ExitCode.GENERAL_ERROR)


@app.command(name="config-validate")
def config_validate(
    config_path: Annotated[
        str | None,
        typer.Argument(help="Path to configuration file (optional, validates default if not provided)")
    ] = None,
) -> None:
    """
    Validate configuration file.

    Examples:
        # Validate default configuration
        fileflow config-validate

        # Validate specific configuration file
        fileflow config-validate ~/custom/config.toml
    """
    out = OutputFormat()

    if config_path:
        out.print(f"\n[bold]Validating configuration at {config_path}...[/bold]\n")
        config_mgr = ConfigManager(config_path)
    else:
        out.print("\n[bold]Validating default configuration...[/bold]\n")
        config_mgr = get_config_manager()

    try:
        valid, error_msg = config_mgr.validate()

        if valid:
            out.print("[green]✓ Configuration is valid[/green]\n")
            sys.exit(ExitCode.SUCCESS)
        else:
            out.print(f"[red]✗ Configuration is invalid: {error_msg}[/red]\n")
            sys.exit(ExitCode.CONFIG_ERROR)

    except FileNotFoundError:
        out.print(f"[red]Error: Configuration file not found: {config_path}[/red]")
        sys.exit(ExitCode.FILE_NOT_FOUND)
    except Exception as e:
        out.print(f"[red]Error: {e}[/red]")
        sys.exit(ExitCode.CONFIG_ERROR)


@app.command(name="config-edit")
def config_edit() -> None:
    """
    Open configuration file in default editor.

    Examples:
        # Edit configuration file
        fileflow config-edit
    """
    import os
    import shutil

    out = OutputFormat()
    config_path = DEFAULT_CONFIG_PATH

    if not config_path.exists():
        out.print("[yellow]Configuration file does not exist. Creating default configuration...[/yellow]")
        create_default_config_file(str(config_path))

    # Determine editor
    editor = os.environ.get('EDITOR') or os.environ.get('VISUAL')

    if not editor:
        # Try to find common editors
        for candidate in ['nano', 'vim', 'vi', 'emacs']:
            if shutil.which(candidate):
                editor = candidate
                break

    if not editor:
        out.print("[red]No editor found. Please set the EDITOR environment variable.[/red]")
        out.print(f"\nConfiguration file location: [cyan]{config_path}[/cyan]")
        out.print("\nYou can edit it manually or set EDITOR:")
        out.print("  export EDITOR=nano")
        out.print("  export EDITOR=vim")
        sys.exit(ExitCode.CONFIG_ERROR)

    out.print(f"[bold]Opening configuration in {editor}...[/bold]\n")
    out.print(f"File: [cyan]{config_path}[/cyan]\n")

    try:
        # Open editor
        result = subprocess.run([editor, str(config_path)])

        if result.returncode == 0:
            # Validate configuration after editing
            out.print("\n[bold]Validating edited configuration...[/bold]")
            config_mgr = ConfigManager(config_path)
            valid, error_msg = config_mgr.validate()

            if valid:
                out.print("[green]✓ Configuration is valid[/green]\n")
                sys.exit(ExitCode.SUCCESS)
            else:
                out.print(f"[yellow]⚠ Warning: Configuration has errors: {error_msg}[/yellow]")
                out.print("[yellow]  Fix the errors and run: fileflow config-validate[/yellow]\n")
                sys.exit(ExitCode.CONFIG_ERROR)
        else:
            out.print(f"[yellow]Editor exited with code {result.returncode}[/yellow]\n")
            sys.exit(ExitCode.GENERAL_ERROR)

    except FileNotFoundError:
        out.print(f"[red]Editor '{editor}' not found[/red]")
        sys.exit(ExitCode.FILE_NOT_FOUND)
    except Exception as e:
        out.print(f"[red]Error opening editor: {e}[/red]")
        sys.exit(ExitCode.GENERAL_ERROR)


@app.command(name="config-reset")
def config_reset(
    force: Annotated[
        bool,
        typer.Option("--force", help="Skip confirmation prompt")
    ] = False,
    keep_rules: Annotated[
        bool,
        typer.Option("--keep-rules", help="Keep existing rules, reset only settings")
    ] = False,
) -> None:
    """
    Reset configuration to defaults.

    Examples:
        # Reset configuration (with confirmation)
        fileflow config-reset

        # Reset without confirmation
        fileflow config-reset --force

        # Reset but keep custom rules
        fileflow config-reset --keep-rules
    """
    out = OutputFormat()
    config_path = DEFAULT_CONFIG_PATH

    if not config_path.exists():
        out.print("[yellow]Configuration file does not exist.[/yellow]\n")
        sys.exit(ExitCode.SUCCESS)

    # Load current config to backup rules if needed
    current_rules = []
    if keep_rules:
        try:
            config_mgr = get_config_manager()
            config = config_mgr.load()
            current_rules = config.rules
        except Exception:
            out.print("[yellow]Warning: Could not load current rules[/yellow]")

    # Confirmation
    if not force:
        if not confirm_action(
            "This will reset your configuration. Continue?",
            default=False
        ):
            out.print("\n[yellow]Reset cancelled[/yellow]\n")
            sys.exit(ExitCode.OPERATION_CANCELLED)

    try:
        # Create backup
        import shutil
        from datetime import datetime

        backup_path = config_path.parent / f"fileflow.toml.backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        shutil.copy(config_path, backup_path)
        out.print(f"\n[green]✓ Backup created: {backup_path}[/green]")

        # Reset configuration
        create_default_config_file(str(config_path))
        out.print("[green]✓ Configuration reset to defaults[/green]")

        # Restore rules if requested
        if keep_rules and current_rules:
            config_mgr = get_config_manager()
            config = config_mgr.load()
            config.rules = current_rules
            config_mgr.save(config)
            out.print(f"[green]✓ Restored {len(current_rules)} custom rules[/green]")

        out.print("\n[bold]Configuration has been reset![/bold]\n")
        sys.exit(ExitCode.SUCCESS)

    except Exception as e:
        out.print(f"[red]Error resetting configuration: {e}[/red]")
        sys.exit(ExitCode.GENERAL_ERROR)


@app.command(name="history")
def history(
    limit: Annotated[
        int,
        typer.Option("--limit", "-n", help="Maximum number of operations to show")
    ] = 100,
    operation_type: Annotated[
        str | None,
        typer.Option("--operation-type", "-t", help="Filter by operation type (move, delete, skip)")
    ] = None,
    rule_id: Annotated[
        str | None,
        typer.Option("--rule-id", "-r", help="Filter by rule ID")
    ] = None,
    include_dry_runs: Annotated[
        bool,
        typer.Option("--include-dry-runs", "-d", help="Include dry-run operations")
    ] = False,
    output_format: Annotated[
        str,
        typer.Option("--output", "-o", help="Output format (table, json)")
    ] = "table",
) -> None:
    """
    Show operation history with optional filtering.

    View past file operations including moves, deletions, and skipped files.
    Filter by operation type, rule, and optionally include dry-run operations.

    Examples:
        # Show last 50 operations
        fileflow history --limit 50

        # Show only move operations
        fileflow history --operation-type move

        # Show operations for a specific rule
        fileflow history --rule-id screenshot-org

        # Include dry-run operations
        fileflow history --include-dry-runs

        # Output as JSON
        fileflow history --output json
    """
    out = OutputFormat()

    try:
        # Parse operation type if provided
        op_type = None
        if operation_type:
            try:
                op_type = OperationType(operation_type.lower())
            except ValueError:
                if output_format == "json":
                    JSONOutput.print(
                        JSONOutput.error(
                            f"Invalid operation type '{operation_type}'",
                            code=ExitCode.INVALID_USAGE,
                            details={"valid_types": ["move", "delete", "skip"]},
                        )
                    )
                else:
                    out.print(f"[red]Error: Invalid operation type '{operation_type}'[/red]")
                    out.print("[yellow]Valid types: move, delete, skip[/yellow]")
                sys.exit(ExitCode.INVALID_USAGE)

        # Get history from database
        db = Database(DEFAULT_DB_PATH)
        operations = db.get_operation_history(
            limit=limit,
            operation_type=op_type,
            rule_id=rule_id,
            include_dry_runs=include_dry_runs,
        )

        # Calculate statistics
        total_size = sum(op.file_size for op in operations if op.file_size and op.success and not op.dry_run)
        successful = sum(1 for op in operations if op.success and not op.dry_run)
        failed = sum(1 for op in operations if not op.success and not op.dry_run)
        dry_runs = sum(1 for op in operations if op.dry_run)

        # Handle JSON output
        if output_format == "json":
            operations_data = [
                {
                    "timestamp": op.timestamp.isoformat() if op.timestamp else None,
                    "operation_type": op.operation_type.value,
                    "source_path": op.source_path,
                    "destination_path": op.destination_path,
                    "rule_id": op.rule_id,
                    "file_size": op.file_size,
                    "success": op.success,
                    "dry_run": op.dry_run,
                }
                for op in operations
            ]

            JSONOutput.print(
                JSONOutput.success(
                    data=operations_data,
                    metadata={
                        "total_operations": len(operations),
                        "successful": successful,
                        "failed": failed,
                        "dry_runs": dry_runs,
                        "total_size_bytes": total_size,
                        "filters": {
                            "limit": limit,
                            "operation_type": operation_type,
                            "rule_id": rule_id,
                            "include_dry_runs": include_dry_runs,
                        },
                    },
                    message=f"Found {len(operations)} operations" if operations else "No operations found matching the criteria",
                )
            )
            sys.exit(ExitCode.SUCCESS)

        # Table output (default)
        if not operations:
            out.print("[yellow]No operations found matching the criteria.[/yellow]")
            if not include_dry_runs:
                out.print("[dim]Tip: Use --include-dry-runs to see dry-run operations[/dim]")
            sys.exit(ExitCode.SUCCESS)

        # Build table
        from rich.table import Table

        table = Table(title=f"Operation History (showing {len(operations)})")
        table.add_column("Date/Time", style="cyan", no_wrap=True)
        table.add_column("Operation", style="magenta")
        table.add_column("Source", style="blue")
        table.add_column("Destination", style="green")
        table.add_column("Rule", style="yellow")
        table.add_column("Size", justify="right")
        table.add_column("Status", justify="center")

        # Add rows
        for op in operations:
            # Format timestamp
            timestamp = op.timestamp.strftime("%Y-%m-%d %H:%M:%S") if op.timestamp else "N/A"

            # Format operation type with emoji
            op_icons = {
                OperationType.MOVE: "→",
                OperationType.DELETE: "🗑",
                OperationType.SKIP: "⊘",
            }
            op_display = f"{op_icons.get(op.operation_type, '?')} {op.operation_type.value}"

            # Format file paths
            source = Path(op.source_path).name if op.source_path else "N/A"
            destination = str(Path(op.destination_path).name) if op.destination_path else "-"

            # Format file size
            size = format_file_size(op.file_size) if op.file_size else "-"

            # Format status
            if op.dry_run:
                status = "[dim]dry-run[/dim]"
            elif op.success:
                status = "[green]✓[/green]"
            else:
                status = "[red]✗[/red]"

            # Format rule ID
            rule = op.rule_id or "-"

            table.add_row(
                timestamp,
                op_display,
                source,
                destination,
                rule,
                size,
                status,
            )

        out.console.print(table)

        # Summary statistics
        out.print("\n[bold]Summary:[/bold]")
        out.print(f"  Total operations: {len(operations)}")
        out.print(f"  Successful: {successful}")
        if failed > 0:
            out.print(f"  Failed: {failed}")
        if dry_runs > 0:
            out.print(f"  Dry-runs: {dry_runs}")

        if total_size > 0:
            out.print(f"  Total data processed: {format_file_size(total_size)}")

        out.print()
        sys.exit(ExitCode.SUCCESS)

    except Exception as e:
        if output_format == "json":
            JSONOutput.print(
                JSONOutput.error(f"Error retrieving history: {e}", code=ExitCode.DATABASE_ERROR)
            )
        else:
            out.print(f"[red]Error retrieving history: {e}[/red]")
        sys.exit(ExitCode.DATABASE_ERROR)


@app.command(name="system-status")
def system_status() -> None:
    """Show system health check and status (T145).

    Displays:
    - Configuration file status and validity
    - Database connection and health
    - Cache status and statistics
    - Monitored directories accessibility
    - Active rules count
    - Recent operation statistics
    """
    try:
        console.print("\n[bold]FileFlow System Status[/bold]\n")

        # Check configuration
        config_mgr = get_config_manager()
        try:
            config = config_mgr.load()
            console.print("[green]✓[/green] Configuration: Valid")
            console.print(f"  Location: {DEFAULT_CONFIG_PATH}")
            console.print(f"  Rules: {len(config.rules)} total, {len([r for r in config.rules if r.enabled])} enabled")
        except Exception as e:
            console.print(f"[red]✗[/red] Configuration: Error - {e}")
            raise typer.Exit(1)

        # Check database
        try:
            db = Database(DEFAULT_DB_PATH)
            # Test database connectivity
            db.get_operation_history(limit=1)
            console.print("[green]✓[/green] Database: Connected")
            console.print(f"  Location: {DEFAULT_DB_PATH}")
            console.print(f"  Size: {DEFAULT_DB_PATH.stat().st_size / 1024:.1f} KB" if DEFAULT_DB_PATH.exists() else "  Size: N/A")
        except Exception as e:
            console.print(f"[red]✗[/red] Database: Error - {e}")

        # Check cache
        try:
            db = get_database()
            ChecksumCache(db)
            # Get cache stats (this would need to be implemented in cache.py)
            console.print("[green]✓[/green] Cache: Enabled")
        except Exception as e:
            console.print(f"[yellow]⚠[/yellow] Cache: Warning - {e}")

        # Check monitored directories
        console.print("\n[bold]Monitored Directories:[/bold]")
        for directory in config.paths.monitored_directories:
            expanded_path = Path(directory).expanduser()
            if expanded_path.exists() and expanded_path.is_dir():
                # Count files
                try:
                    file_count = len(list(expanded_path.iterdir()))
                    console.print(f"  [green]✓[/green] {expanded_path} ({file_count} items)")
                except PermissionError:
                    console.print(f"  [yellow]⚠[/yellow] {expanded_path} (permission denied)")
            else:
                console.print(f"  [red]✗[/red] {expanded_path} (not accessible)")

        # Recent operations stats
        console.print("\n[bold]Recent Activity (Last 7 Days):[/bold]")
        try:
            from datetime import datetime, timedelta
            week_ago = datetime.now() - timedelta(days=7)
            recent_ops = db.get_operation_history(
                limit=1000,
                start_date=week_ago,
                include_dry_runs=False
            )

            if recent_ops:
                move_count = sum(1 for op in recent_ops if op.operation_type == OperationType.MOVE)
                delete_count = sum(1 for op in recent_ops if op.operation_type == OperationType.DELETE)
                skip_count = sum(1 for op in recent_ops if op.operation_type == OperationType.SKIP)
                total_size = sum(op.file_size for op in recent_ops if op.file_size and op.success)

                console.print(f"  Moves: {move_count}")
                console.print(f"  Deletions: {delete_count}")
                console.print(f"  Skipped: {skip_count}")

                if total_size > 0:
                    if total_size < 1024 * 1024:
                        size_str = f"{total_size / 1024:.1f} KB"
                    elif total_size < 1024 * 1024 * 1024:
                        size_str = f"{total_size / (1024 * 1024):.1f} MB"
                    else:
                        size_str = f"{total_size / (1024 * 1024 * 1024):.2f} GB"
                    console.print(f"  Data processed: {size_str}")
            else:
                console.print("  No operations in the last 7 days")
        except Exception as e:
            console.print(f"  [yellow]Could not retrieve statistics: {e}[/yellow]")

        console.print("\n[green]System is operational[/green]\n")

    except Exception as e:
        console.print(f"\n[red]Error checking system status: {e}[/red]")
        raise typer.Exit(1)


@app.command(name="clear-cache")
def clear_cache(
    force: Annotated[bool, typer.Option("--force", "-f", help="Skip confirmation prompt")] = False,
) -> None:
    """Clear checksum cache and optimize database (T146).

    Clears the checksum cache to force recalculation on next scan.
    Also runs VACUUM on the database to reclaim space.
    """
    try:
        if not force:
            console.print("[yellow]This will clear all cached checksums.[/yellow]")
            console.print("Files will need to be rehashed on the next scan.")
            confirm = typer.confirm("Are you sure you want to continue?")
            if not confirm:
                console.print("Operation cancelled.")
                raise typer.Exit(0)

        console.print("\n[bold]Clearing cache...[/bold]\n")

        # Clear checksum cache using proper database API
        db = Database(DEFAULT_DB_PATH)

        # Get stats before clearing
        stats = db.get_stats()
        cache_count = stats["cache_count"]

        # Clear cache
        db.clear_cache()

        console.print(f"[green]✓[/green] Cleared {cache_count} cached checksums")

        # Vacuum database using connection pool
        with db.pool.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("VACUUM")
        console.print("[green]✓[/green] Optimized database")

        # Show new database size
        db_size = DEFAULT_DB_PATH.stat().st_size / 1024
        console.print(f"\nDatabase size: {db_size:.1f} KB")
        console.print("[green]Cache cleared successfully![/green]\n")

    except Exception as e:
        console.print(f"[red]Error clearing cache: {e}[/red]")
        raise typer.Exit(1)


@app.command(name="find-duplicates")
def find_duplicates(
    delete_auto: Annotated[bool, typer.Option("--delete-auto", help="Automatically delete all duplicates (keep oldest)")] = False,
    delete_interactive: Annotated[bool, typer.Option("--delete-interactive", "-i", help="Interactively choose which duplicates to delete")] = False,
    min_size_mb: Annotated[int, typer.Option("--min-size", help="Only find duplicates larger than this size (MB)")] = 1,
) -> None:
    """Find and optionally delete duplicate files (T151).

    Scans monitored directories for files with identical SHA-256 checksums.
    By default, displays duplicates without deleting. Use --delete-auto or
    --delete-interactive to remove duplicates.

    Examples:
        fileflow find-duplicates                    # List all duplicates
        fileflow find-duplicates --min-size 10      # Only show duplicates >10MB
        fileflow find-duplicates --delete-auto      # Auto-delete (keep oldest)
        fileflow find-duplicates -i                 # Interactive deletion
    """
    try:
        config_mgr = get_config_manager()
        config = config_mgr.load()
        db = Database(DEFAULT_DB_PATH)
        cache = ChecksumCache(db)

        # Get monitored directories
        monitored_dirs = [
            Path(config_mgr.expand_env_vars(d))
            for d in config.paths.monitored_directories
        ]

        console.print(f"\n[bold]Scanning for duplicates in {len(monitored_dirs)} directories...[/bold]\n")

        # Scan all files and compute checksums
        from collections import defaultdict

        from fileflow_core.file_scanner import FileScanner

        FileScanner()
        checksum_to_files = defaultdict(list)

        for directory in monitored_dirs:
            if not directory.exists():
                console.print(f"[yellow]⚠[/yellow] Directory not found: {directory}")
                continue

            for file_path in directory.rglob("*"):
                if file_path.is_file():
                    try:
                        # Skip files smaller than min_size_mb
                        file_size_mb = file_path.stat().st_size / (1024 * 1024)
                        if file_size_mb < min_size_mb:
                            continue

                        # Calculate checksum
                        checksum = cache.get_checksum(file_path)
                        checksum_to_files[checksum].append(file_path)
                    except Exception as e:
                        console.print(f"[yellow]⚠[/yellow] Error processing {file_path.name}: {e}")

        # Find duplicates (checksums with multiple files)
        duplicates = {
            checksum: files
            for checksum, files in checksum_to_files.items()
            if len(files) > 1
        }

        if not duplicates:
            console.print("[green]No duplicate files found![/green]\n")
            return

        # Calculate total duplicate space
        total_duplicate_size = 0
        total_duplicate_count = 0

        for _, files in duplicates.items():
            # Keep one, rest are duplicates
            file_size = files[0].stat().st_size
            duplicate_count = len(files) - 1
            total_duplicate_size += file_size * duplicate_count
            total_duplicate_count += duplicate_count

        # Display duplicates
        console.print(f"[bold]Found {len(duplicates)} sets of duplicates ({total_duplicate_count} redundant files)[/bold]\n")
        console.print(f"Potential space savings: {total_duplicate_size / (1024 * 1024):.2f} MB\n")

        # Create table
        table = Table(title="Duplicate Files")
        table.add_column("Set", style="cyan", width=4)
        table.add_column("Files", style="yellow", width=3)
        table.add_column("Size", style="magenta", width=10)
        table.add_column("Paths", style="white")

        files_to_delete = []

        for idx, (_, files) in enumerate(sorted(duplicates.items(), key=lambda x: len(x[1]), reverse=True), 1):
            file_size = files[0].stat().st_size
            size_str = f"{file_size / (1024 * 1024):.2f} MB" if file_size > 1024 * 1024 else f"{file_size / 1024:.1f} KB"

            # Sort by modification time (oldest first) for consistent behavior
            sorted_files = sorted(files, key=lambda f: f.stat().st_mtime)

            paths_str = "\n".join([
                f"[green]{'[KEEP]' if i == 0 else '[DELETE]'}[/green] {f}"
                for i, f in enumerate(sorted_files)
            ])

            table.add_row(
                str(idx),
                str(len(files)),
                size_str,
                paths_str
            )

            # Collect files to delete (all except oldest)
            if delete_auto:
                files_to_delete.extend(sorted_files[1:])
            elif delete_interactive:
                # Will prompt per set below
                pass

        console.print(table)
        console.print()

        # Handle deletion modes
        if delete_auto:
            console.print(f"\n[yellow]Auto-delete mode: Deleting {len(files_to_delete)} duplicate files (keeping oldest)[/yellow]")
            confirm = typer.confirm("Are you sure?")
            if not confirm:
                console.print("Operation cancelled.")
                return

            deleted_count = 0
            space_freed = 0

            for file_path in files_to_delete:
                try:
                    file_size = file_path.stat().st_size
                    file_path.unlink()
                    deleted_count += 1
                    space_freed += file_size
                    console.print(f"[green]✓[/green] Deleted: {file_path}")
                except Exception as e:
                    console.print(f"[red]✗[/red] Failed to delete {file_path.name}: {e}")

            console.print(f"\n[green]Deleted {deleted_count} files, freed {space_freed / (1024 * 1024):.2f} MB[/green]\n")

        elif delete_interactive:
            console.print("\n[bold]Interactive Deletion Mode[/bold]")
            console.print("For each duplicate set, choose which files to delete.\n")

            deleted_count = 0
            space_freed = 0

            for idx, (_, files) in enumerate(sorted(duplicates.items(), key=lambda x: len(x[1]), reverse=True), 1):
                sorted_files = sorted(files, key=lambda f: f.stat().st_mtime)

                console.print(f"\n[bold]Set {idx} of {len(duplicates)}:[/bold]")
                for i, file_path in enumerate(sorted_files):
                    mtime = datetime.fromtimestamp(file_path.stat().st_mtime).strftime("%Y-%m-%d %H:%M:%S")
                    console.print(f"  [{i+1}] {file_path} (modified: {mtime})")

                console.print(f"\n  [bold]{'[RECOMMENDED]' if len(sorted_files) > 1 else ''}[/bold] Keep file [1] (oldest), delete others")

                choice = typer.prompt(
                    "\nEnter file numbers to delete (comma-separated) or 'skip' to keep all",
                    default="2-" + str(len(sorted_files)) if len(sorted_files) > 1 else "skip"
                )

                if choice.strip().lower() == "skip":
                    console.print("[yellow]Skipped this set[/yellow]")
                    continue

                # Parse choices
                try:
                    to_delete: list[int] = []
                    for part in choice.split(","):
                        part = part.strip()
                        if "-" in part:
                            start, end = part.split("-")
                            start = int(start) if start else 2
                            end = int(end) if end else len(sorted_files)
                            to_delete.extend(range(start, end + 1))
                        else:
                            to_delete.append(int(part))

                    for file_idx in sorted(set(to_delete), reverse=True):
                        if 1 <= file_idx <= len(sorted_files):
                            file_path = sorted_files[file_idx - 1]
                            try:
                                file_size = file_path.stat().st_size
                                file_path.unlink()
                                deleted_count += 1
                                space_freed += file_size
                                console.print(f"[green]✓[/green] Deleted: {file_path.name}")
                            except Exception as e:
                                console.print(f"[red]✗[/red] Failed to delete {file_path.name}: {e}")
                except ValueError:
                    console.print("[red]Invalid input, skipping this set[/red]")

            console.print(f"\n[green]Deleted {deleted_count} files, freed {space_freed / (1024 * 1024):.2f} MB[/green]\n")

    except Exception as e:
        console.print(f"[red]Error finding duplicates: {e}[/red]")
        raise typer.Exit(1)


@app.command(name="completion")
def generate_completion(
    shell: Annotated[
        str,
        typer.Argument(
            help="Shell type: bash, zsh, or fish"
        )
    ] = "bash",
    install: Annotated[
        bool,
        typer.Option(
            "--install",
            help="Show installation instructions"
        )
    ] = False,
) -> None:
    """
    Generate shell completion scripts (T152).

    Supports bash, zsh, and fish shells.

    Examples:
        fileflow completion bash > ~/.bash_completions/fileflow.bash
        fileflow completion zsh > ~/.zsh/completions/_fileflow
        fileflow completion fish > ~/.config/fish/completions/fileflow.fish

        # Show installation instructions
        fileflow completion bash --install
    """
    shell = shell.lower()

    if shell not in ["bash", "zsh", "fish"]:
        console.print(f"[red]Error: Unsupported shell '{shell}'. Use: bash, zsh, or fish[/red]")
        raise typer.Exit(1)

    if install:
        # Show installation instructions
        console.print(f"\n[bold cyan]Shell Completion Installation for {shell.upper()}[/bold cyan]\n")

        if shell == "bash":
            console.print("[bold]1. Generate completion script:[/bold]")
            console.print("   fileflow completion bash > ~/.bash_completions/fileflow.bash\n")
            console.print("[bold]2. Add to your ~/.bashrc:[/bold]")
            console.print("   source ~/.bash_completions/fileflow.bash\n")
            console.print("[bold]3. Reload your shell:[/bold]")
            console.print("   source ~/.bashrc\n")

        elif shell == "zsh":
            console.print("[bold]1. Create completions directory (if needed):[/bold]")
            console.print("   mkdir -p ~/.zsh/completions\n")
            console.print("[bold]2. Generate completion script:[/bold]")
            console.print("   fileflow completion zsh > ~/.zsh/completions/_fileflow\n")
            console.print("[bold]3. Add to your ~/.zshrc (if not already present):[/bold]")
            console.print("   fpath=(~/.zsh/completions $fpath)")
            console.print("   autoload -Uz compinit && compinit\n")
            console.print("[bold]4. Reload your shell:[/bold]")
            console.print("   source ~/.zshrc\n")

        elif shell == "fish":
            console.print("[bold]1. Create completions directory (if needed):[/bold]")
            console.print("   mkdir -p ~/.config/fish/completions\n")
            console.print("[bold]2. Generate completion script:[/bold]")
            console.print("   fileflow completion fish > ~/.config/fish/completions/fileflow.fish\n")
            console.print("[bold]3. Completions will be automatically loaded[/bold]\n")

        console.print("[dim]After installation, you can use TAB to autocomplete fileflow commands![/dim]\n")
        return

    # Generate and print completion script
    # Typer uses click underneath, so we can access the click completion
    from click.shell_completion import get_completion_class

    # Get the click command from the Typer app
    click_command = typer.main.get_command(app)

    # Get the appropriate completion class
    completion_class = get_completion_class(shell)
    if completion_class is None:
        console.print(f"[red]Error: Could not generate completion for {shell}[/red]")
        raise typer.Exit(1)

    # Generate completion script
    completion = completion_class(
        cli=click_command,
        ctx_args={},
        prog_name="fileflow",
        complete_var=f"_{shell.upper()}_COMPLETE"
    )

    # Output the completion script
    print(completion.source())


if __name__ == "__main__":
    app()
