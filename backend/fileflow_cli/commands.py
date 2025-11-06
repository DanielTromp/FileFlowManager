"""
Typer CLI commands for FileFlow Manager.
"""

import json
import subprocess
from pathlib import Path
from typing import Optional, Any, Dict

import typer
from rich.console import Console
from rich.table import Table
from typing_extensions import Annotated

from fileflow_config.config_manager import ConfigManager
from fileflow_config.defaults import create_default_config_file
from fileflow_core.logging_config import setup_logging
from fileflow_core.rule_engine import RuleEngine
from fileflow_core.models import OperationType
from fileflow_storage.cache import ChecksumCache
from fileflow_storage.database import Database

app = typer.Typer(
    help="FileFlow Manager - Automated File Organization",
    pretty_exceptions_show_locals=False,
    add_completion=True  # T152: Enable shell completion support
)
console = Console()

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


def format_age(age_days: float) -> str:
    """Format file age in human-readable format."""
    if age_days < 1:
        return "< 1 day"
    elif age_days < 30:
        return f"{int(age_days)} days"
    elif age_days < 365:
        months = int(age_days / 30)
        return f"{months} month{'s' if months > 1 else ''}"
    else:
        years = age_days / 365
        return f"{years:.1f} year{'s' if years >= 2 else ''}"


@app.command()
def scan() -> None:
    """
    Scan directories for files matching active rules and execute operations.

    This will scan your configured directories and immediately execute any
    matching file organization rules. Files will be moved/organized based
    on your active rules.

    For a preview without making changes, the dry-run functionality
    can be added in a future update.
    """
    dry_run = False  # Always execute for now

    # Setup
    config_mgr = get_config_manager()
    config = config_mgr.load()
    db = get_database()
    cache = ChecksumCache(db)
    engine = RuleEngine(db, cache, config_mgr.expand_env_vars)

    # Use all enabled rules
    rule_list = config.rules

    # Run scan
    console.print("\n[bold]FileFlow Scan Results[/bold]")
    console.print("=" * 64)

    with console.status("[bold green]Scanning files..."):
        result = engine.scan(rule_list, dry_run=dry_run)

    # Display results
    console.print(f"\nScan completed in {result.scan_duration_ms / 1000:.1f}s\n")
    console.print(f"Files Scanned:     {result.total_files_scanned:,}")
    console.print(f"Files Matched:     {result.files_matched:,}")
    console.print(f"Duplicates Found:  {len(result.duplicate_pairs):,}")

    if result.planned_operations:
        console.print("\n[bold]Planned Operations[/bold]")
        console.print("-" * 64)

        # Show first 20 operations
        for op in result.planned_operations[:20]:
            op_type = op.operation_type.value.upper()
            source_name = Path(op.source_path).name

            if op.operation_type.name == "MOVE":
                console.print(f"[green]{op_type}[/green]    {source_name}")
                console.print(f"        → {op.destination_path}")
            elif op.operation_type.name == "DELETE":
                console.print(f"[red]{op_type}[/red]  {source_name} (duplicate)")
                console.print(f"        Space freed: {op.file_size / (1024*1024):.1f} MB")
            elif op.operation_type.name == "SKIP":
                console.print(f"[yellow]{op_type}[/yellow]    {source_name}")
                if op.skip_reason:
                    console.print(f"        ! {op.skip_reason.value}")

        if len(result.planned_operations) > 20:
            console.print(f"\n... [{len(result.planned_operations) - 20} more operations]")

    # Summary
    console.print("\n[bold]Summary[/bold]")
    console.print("-" * 64)
    console.print(f"Total operations:         {len(result.planned_operations)}")

    move_count = sum(1 for op in result.planned_operations if op.operation_type.name == "MOVE")
    delete_count = sum(1 for op in result.planned_operations if op.operation_type.name == "DELETE")
    skip_count = sum(1 for op in result.planned_operations if op.operation_type.name == "SKIP")

    console.print(f"  Move operations:        {move_count}")
    console.print(f"  Delete operations:      {delete_count}")
    console.print(f"  Skipped:                {skip_count}")
    console.print(f"\nEstimated space freed:   {result.estimated_space_freed_mb:.1f} MB")

    if dry_run:
        console.print("\n[yellow]To execute these operations, run:[/yellow]")
        console.print("  [bold]fileflow scan --execute[/bold]\n")
    else:
        # Execute operations
        console.print("\n[bold green]Executing operations...[/bold green]")
        with console.status("[bold green]Processing files..."):
            executed = engine.execute(result.planned_operations)

        success_count = sum(1 for op in executed if op.success)
        console.print(f"\n[green]✓ Successfully processed {success_count} files[/green]\n")


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
def rules_list() -> None:
    """List all configured rules."""
    config_mgr = get_config_manager()
    config = config_mgr.load()

    if not config.rules:
        console.print("[yellow]No rules configured.[/yellow]")
        console.print("Run [bold]fileflow rules create[/bold] to add a rule.")
        return

    console.print("\n[bold]Configured Rules[/bold]")
    console.print("=" * 80)

    table = Table(show_header=True, header_style="bold cyan")
    table.add_column("ID", style="cyan")
    table.add_column("Name")
    table.add_column("Priority", justify="center")
    table.add_column("Enabled", justify="center")
    table.add_column("Patterns")
    table.add_column("Source Dirs", no_wrap=False)

    for rule in sorted(config.rules, key=lambda r: r.priority):
        enabled_str = "[green]✓[/green]" if rule.enabled else "[red]✗[/red]"
        patterns = ", ".join(rule.source_patterns[:3])
        if len(rule.source_patterns) > 3:
            patterns += f", +{len(rule.source_patterns) - 3}"

        source_dirs = ", ".join(str(d) for d in rule.source_directories[:2])
        if len(rule.source_directories) > 2:
            source_dirs += f", +{len(rule.source_directories) - 2}"

        table.add_row(
            rule.id,
            rule.name,
            str(rule.priority),
            enabled_str,
            patterns,
            source_dirs,
        )

    console.print(table)
    console.print()


@rules_app.command("show")
def rules_show(rule_id: Annotated[str, typer.Argument(help="Rule ID to display")]) -> None:
    """Show detailed information about a specific rule."""
    config_mgr = get_config_manager()
    config = config_mgr.load()

    rule = next((r for r in config.rules if r.id == rule_id), None)
    if not rule:
        console.print(f"[red]Error: Rule '{rule_id}' not found.[/red]")
        return

    console.print(f"\n[bold]Rule: {rule.name}[/bold]")
    console.print("=" * 80)
    console.print(f"ID:               {rule.id}")
    console.print(f"Priority:         {rule.priority}")
    console.print(f"Enabled:          {'Yes' if rule.enabled else 'No'}")
    console.print(f"\n[bold]Source:[/bold]")
    console.print(f"  Directories:    {', '.join(rule.source_directories)}")
    console.print(f"  Patterns:       {', '.join(rule.source_patterns)}")
    if rule.exclude_patterns:
        console.print(f"  Exclude:        {', '.join(rule.exclude_patterns)}")
    if rule.file_types:
        console.print(f"  File Types:     {', '.join(rule.file_types)}")
    console.print(f"\n[bold]Destination:[/bold]")
    console.print(f"  Path:           {rule.destination}")
    if rule.organize_by_date:
        console.print(f"  Organize:       By date (YYYY/MM/DD)")
    if rule.min_size_kb or rule.max_size_kb:
        console.print(f"\n[bold]Size Constraints:[/bold]")
        if rule.min_size_kb:
            console.print(f"  Minimum:        {rule.min_size_kb} KB")
        if rule.max_size_kb:
            console.print(f"  Maximum:        {rule.max_size_kb} KB")
    if rule.min_age_days or rule.max_age_days:
        console.print(f"\n[bold]Age Constraints:[/bold]")
        if rule.min_age_days:
            console.print(f"  Minimum:        {rule.min_age_days} days")
        if rule.max_age_days:
            console.print(f"  Maximum:        {rule.max_age_days} days")
    console.print()


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
    new_rule = Rule(
        id=rule_id,
        name=name,
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
    console.print(f"Run [bold]fileflow scan[/bold] to apply this rule.\n")


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
def rules_delete(rule_id: Annotated[str, typer.Argument(help="Rule ID to delete")]) -> None:
    """Delete a rule."""
    config_mgr = get_config_manager()
    config = config_mgr.load()

    rule = next((r for r in config.rules if r.id == rule_id), None)
    if not rule:
        console.print(f"[red]Error: Rule '{rule_id}' not found.[/red]")
        return

    # Confirm deletion
    confirm = typer.confirm(f"Delete rule '{rule.name}'?")
    if not confirm:
        console.print("[yellow]Deletion cancelled.[/yellow]")
        return

    # Remove rule
    config.rules = [r for r in config.rules if r.id != rule_id]
    config_mgr.save(config)

    console.print(f"\n[green]✓ Rule '{rule.name}' deleted successfully![/green]\n")


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
    output_format: Annotated[str, typer.Option("--output-format", "-o", help="Output format: table or json")] = "table",
) -> None:
    """Find files larger than 100MB (T153: supports JSON output)."""
    from pathlib import Path
    from fileflow_core.file_scanner import FileScanner

    # Get monitored directories from config
    config_mgr = get_config_manager()
    config = config_mgr.load()
    monitored_dirs = [Path(config_mgr.expand_env_vars(d)) for d in config.paths.monitored_directories]

    # Scan for large files
    scanner = FileScanner()
    large_files = scanner.find_large_files(directories=monitored_dirs, threshold_mb=100)

    if output_format == "json":
        # JSON output (T153)
        output_json({
            "threshold_mb": 100,
            "files_found": len(large_files),
            "total_size_mb": sum(f.size_bytes for f in large_files) / (1024 * 1024),
            "files": [
                {
                    "filename": f.filename,
                    "path": f.path,
                    "size_bytes": f.size_bytes,
                    "size_mb": f.size_bytes / (1024 * 1024),
                    "age_days": f.age_days,
                }
                for f in large_files
            ]
        })
        return

    # Table output (default)
    console.print("\n[bold]Finding files larger than 100 MB...[/bold]\n")

    if not large_files:
        console.print("[yellow]No files found larger than 100 MB.[/yellow]")
        return

    # Display results
    from rich.table import Table

    table = Table(title="Large Files (> 100 MB)")
    table.add_column("File", style="cyan")
    table.add_column("Size", justify="right", style="yellow")
    table.add_column("Path", style="dim")

    for file_meta in large_files[:20]:  # Limit to 20 files
        size_mb = file_meta.size_bytes / (1024 * 1024)
        size_str = f"{size_mb:.2f} MB" if size_mb < 1024 else f"{size_mb/1024:.2f} GB"
        table.add_row(
            file_meta.filename,
            size_str,
            str(Path(file_meta.path).parent),
        )

    console.print(table)

    # Summary
    total_size = sum(f.size_bytes for f in large_files) / (1024 * 1024)
    console.print(f"\n[bold]Found {len(large_files)} files, total size: {total_size:.2f} MB[/bold]")


@app.command(name="find-old")
def find_old(
    output_format: Annotated[str, typer.Option("--output-format", "-o", help="Output format: table or json")] = "table",
) -> None:
    """Find files older than 90 days (T153: supports JSON output)."""
    from pathlib import Path
    from fileflow_core.file_scanner import FileScanner

    # Get monitored directories from config
    config_mgr = get_config_manager()
    config = config_mgr.load()
    monitored_dirs = [Path(config_mgr.expand_env_vars(d)) for d in config.paths.monitored_directories]

    # Scan for old files (T103)
    scanner = FileScanner()
    old_files = scanner.find_old_files(
        directories=monitored_dirs,
        threshold_days=90,
    )

    if output_format == "json":
        # JSON output (T153)
        total_size_mb = sum(f.size_bytes for f in old_files) / (1024 * 1024)
        avg_age_days = sum(f.age_days for f in old_files if f.age_days) / len(old_files) if old_files else 0
        output_json({
            "threshold_days": 90,
            "files_found": len(old_files),
            "total_size_mb": total_size_mb,
            "average_age_days": avg_age_days,
            "files": [
                {
                    "filename": f.filename,
                    "path": f.path,
                    "size_bytes": f.size_bytes,
                    "size_mb": f.size_bytes / (1024 * 1024),
                    "age_days": f.age_days,
                }
                for f in old_files
            ]
        })
        return

    # Table output (default)
    console.print("\n[bold]Finding files older than 90 days...[/bold]\n")

    if not old_files:
        console.print("[yellow]No files found older than 90 days.[/yellow]")
        return

    # Display results in table (T103)
    from rich.table import Table

    table = Table(title="Old Files (> 90 days)")
    table.add_column("File", style="cyan")
    table.add_column("Age", justify="right", style="yellow")
    table.add_column("Size", justify="right")
    table.add_column("Path", style="dim")

    for file_meta in old_files[:20]:  # Limit to 20 files
        age_str = format_age(file_meta.age_days) if file_meta.age_days else "N/A"
        size_mb = file_meta.size_bytes / (1024 * 1024)
        size_str = f"{size_mb:.2f} MB" if size_mb < 1024 else f"{size_mb/1024:.2f} GB"
        table.add_row(
            file_meta.filename,
            age_str,
            size_str,
            str(Path(file_meta.path).parent),
        )

    console.print(table)

    # Summary (T105)
    total_size_mb = sum(f.size_bytes for f in old_files) / (1024 * 1024)
    avg_age_days = sum(f.age_days for f in old_files if f.age_days) / len(old_files) if old_files else 0
    console.print(f"\n[bold]Found {len(old_files)} files, total size: {total_size_mb:.2f} MB[/bold]")
    console.print(f"[bold]Average age: {avg_age_days:.0f} days ({avg_age_days/365:.1f} years)[/bold]\n")


# Configuration Management Commands

@app.command(name="config-show")
def config_show() -> None:
    """Show current configuration (T119)."""
    console.print("\n[bold]Current Configuration[/bold]\n")

    try:
        config_mgr = get_config_manager()
        config = config_mgr.load()

        # General settings
        console.print("[bold cyan]General Settings[/bold cyan]")
        console.print(f"  Log level: {config.general.log_level}")
        console.print(f"  Auto-run on startup: {config.general.auto_run_on_startup}")
        console.print(f"  Auto-run interval: {config.general.auto_run_interval_minutes} minutes")
        console.print(f"  Notifications: {config.general.enable_notifications}")
        console.print(f"  Cache: {config.general.cache_enabled}")

        # Paths
        console.print(f"\n[bold cyan]Paths[/bold cyan]")
        console.print(f"  Screenshot source: {config.paths.screenshot_source}")
        console.print(f"  Screenshot destination: {config.paths.screenshot_destination}")
        if config.paths.monitored_directories:
            console.print(f"  Monitored directories: {', '.join(config.paths.monitored_directories)}")

        # Rules
        console.print(f"\n[bold cyan]Rules ({len(config.rules)})[/bold cyan]")
        for rule in config.rules:
            status = "✓" if rule.enabled else "✗"
            console.print(f"  [{status}] {rule.name} ({rule.id})")

        console.print()

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)


@app.command(name="config-export")
def config_export(
    output_path: Annotated[str, typer.Argument(help="Path where to save the exported configuration")]
) -> None:
    """Export configuration to TOML file (T120)."""
    console.print(f"\n[bold]Exporting configuration to {output_path}...[/bold]\n")

    try:
        config_mgr = get_config_manager()
        config_mgr.export(output_path)

        console.print(f"[green]✓ Configuration exported successfully[/green]\n")

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)


@app.command(name="config-import")
def config_import(
    input_path: Annotated[str, typer.Argument(help="Path to configuration file to import")]
) -> None:
    """Import configuration from TOML file (T121). Replaces existing configuration."""
    console.print(f"\n[bold]Importing configuration from {input_path} (replace mode)...[/bold]\n")

    try:
        config_mgr = get_config_manager()
        config_mgr.import_config(input_path, merge=False)

        console.print(f"[green]✓ Configuration imported successfully[/green]\n")

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)


@app.command(name="config-import-merge")
def config_import_merge(
    input_path: Annotated[str, typer.Argument(help="Path to configuration file to import")]
) -> None:
    """Import configuration with merge (keeps existing rules, adds new ones)."""
    console.print(f"\n[bold]Importing configuration from {input_path} (merge mode)...[/bold]\n")

    try:
        config_mgr = get_config_manager()
        config_mgr.import_config(input_path, merge=True)

        console.print(f"[green]✓ Configuration merged successfully[/green]\n")

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)


@app.command(name="config-validate")
def config_validate(
    config_path: Annotated[Optional[str], typer.Argument(help="Path to configuration file (optional, validates default if not provided)")] = None
) -> None:
    """Validate configuration file (T122)."""
    if config_path:
        console.print(f"\n[bold]Validating configuration at {config_path}...[/bold]\n")
        config_mgr = ConfigManager(config_path)
    else:
        console.print("\n[bold]Validating default configuration...[/bold]\n")
        config_mgr = get_config_manager()

    try:
        valid, error_msg = config_mgr.validate()

        if valid:
            console.print("[green]✓ Configuration is valid[/green]\n")
        else:
            console.print(f"[red]✗ Configuration is invalid: {error_msg}[/red]\n")
            raise typer.Exit(1)

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)


@app.command(name="config-edit")
def config_edit() -> None:
    """Open configuration file in default editor (T123)."""
    import os
    import shutil

    config_path = DEFAULT_CONFIG_PATH

    if not config_path.exists():
        console.print("[yellow]Configuration file does not exist. Creating default configuration...[/yellow]")
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
        console.print(f"[red]No editor found. Please set the EDITOR environment variable.[/red]")
        console.print(f"\nConfiguration file location: [cyan]{config_path}[/cyan]")
        console.print(f"\nYou can edit it manually or set EDITOR:")
        console.print(f"  export EDITOR=nano")
        console.print(f"  export EDITOR=vim")
        raise typer.Exit(1)

    console.print(f"[bold]Opening configuration in {editor}...[/bold]\n")
    console.print(f"File: [cyan]{config_path}[/cyan]\n")

    try:
        # Open editor
        result = subprocess.run([editor, str(config_path)])

        if result.returncode == 0:
            # Validate configuration after editing
            console.print("\n[bold]Validating edited configuration...[/bold]")
            config_mgr = ConfigManager(config_path)
            valid, error_msg = config_mgr.validate()

            if valid:
                console.print("[green]✓ Configuration is valid[/green]\n")
            else:
                console.print(f"[yellow]⚠ Warning: Configuration has errors: {error_msg}[/yellow]")
                console.print(f"[yellow]  Fix the errors and run: fileflow config-validate[/yellow]\n")
        else:
            console.print(f"[yellow]Editor exited with code {result.returncode}[/yellow]\n")

    except FileNotFoundError:
        console.print(f"[red]Editor '{editor}' not found[/red]")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]Error opening editor: {e}[/red]")
        raise typer.Exit(1)


@app.command(name="config-reset")
def config_reset(
    force: Annotated[bool, typer.Option("--force", help="Skip confirmation prompt")] = False,
    keep_rules: Annotated[bool, typer.Option("--keep-rules", help="Keep existing rules, reset only settings")] = False
) -> None:
    """Reset configuration to defaults (T124)."""
    config_path = DEFAULT_CONFIG_PATH

    if not config_path.exists():
        console.print("[yellow]Configuration file does not exist.[/yellow]\n")
        return

    # Load current config to backup rules if needed
    current_rules = []
    if keep_rules:
        try:
            config_mgr = get_config_manager()
            config = config_mgr.load()
            current_rules = config.rules
        except Exception:
            console.print("[yellow]Warning: Could not load current rules[/yellow]")

    # Confirmation
    if not force:
        console.print("\n[bold red]⚠ Warning: This will reset your configuration![/bold red]\n")
        if keep_rules:
            console.print("  • Settings will be reset to defaults")
            console.print("  • Custom rules will be preserved")
        else:
            console.print("  • All settings will be reset to defaults")
            console.print("  • All custom rules will be deleted")

        console.print(f"\nConfiguration file: [cyan]{config_path}[/cyan]\n")

        confirm = typer.confirm("Are you sure you want to continue?")
        if not confirm:
            console.print("\n[yellow]Reset cancelled[/yellow]\n")
            raise typer.Exit(0)

    try:
        # Create backup
        import shutil
        from datetime import datetime

        backup_path = config_path.parent / f"fileflow.toml.backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        shutil.copy(config_path, backup_path)
        console.print(f"\n[green]✓ Backup created: {backup_path}[/green]")

        # Reset configuration
        create_default_config_file(str(config_path))
        console.print(f"[green]✓ Configuration reset to defaults[/green]")

        # Restore rules if requested
        if keep_rules and current_rules:
            config_mgr = get_config_manager()
            config = config_mgr.load()
            config.rules = current_rules
            config_mgr.save(config)
            console.print(f"[green]✓ Restored {len(current_rules)} custom rules[/green]")

        console.print("\n[bold]Configuration has been reset![/bold]\n")

    except Exception as e:
        console.print(f"[red]Error resetting configuration: {e}[/red]")
        raise typer.Exit(1)


@app.command(name="history")
def history(
    limit: Annotated[int, typer.Option("--limit", "-n", help="Maximum number of operations to show")] = 100,
    operation_type: Annotated[Optional[str], typer.Option("--operation-type", "-t", help="Filter by operation type (move, delete, skip)")] = None,
    rule_id: Annotated[Optional[str], typer.Option("--rule-id", "-r", help="Filter by rule ID")] = None,
    include_dry_runs: Annotated[bool, typer.Option("--include-dry-runs", "-d", help="Include dry-run operations")] = False,
) -> None:
    """Show operation history with optional filtering (T149).

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
    """
    try:
        # Parse operation type if provided
        op_type = None
        if operation_type:
            try:
                op_type = OperationType(operation_type.lower())
            except ValueError:
                console.print(f"[red]Error: Invalid operation type '{operation_type}'[/red]")
                console.print("[yellow]Valid types: move, delete, skip[/yellow]")
                raise typer.Exit(1)

        # Get history from database
        db = Database(DEFAULT_DB_PATH)
        operations = db.get_operation_history(
            limit=limit,
            operation_type=op_type,
            rule_id=rule_id,
            include_dry_runs=include_dry_runs,
        )

        if not operations:
            console.print("[yellow]No operations found matching the criteria.[/yellow]")
            if not include_dry_runs:
                console.print("[dim]Tip: Use --include-dry-runs to see dry-run operations[/dim]")
            return

        # Build table
        table = Table(title=f"Operation History (showing {len(operations)} of {len(operations)})")
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
            if op.file_size:
                if op.file_size < 1024:
                    size = f"{op.file_size}B"
                elif op.file_size < 1024 * 1024:
                    size = f"{op.file_size / 1024:.1f}KB"
                elif op.file_size < 1024 * 1024 * 1024:
                    size = f"{op.file_size / (1024 * 1024):.1f}MB"
                else:
                    size = f"{op.file_size / (1024 * 1024 * 1024):.2f}GB"
            else:
                size = "-"

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

        console.print(table)

        # Summary statistics
        total_size = sum(op.file_size for op in operations if op.file_size and op.success and not op.dry_run)
        successful = sum(1 for op in operations if op.success and not op.dry_run)
        failed = sum(1 for op in operations if not op.success and not op.dry_run)
        dry_runs = sum(1 for op in operations if op.dry_run)

        console.print(f"\n[bold]Summary:[/bold]")
        console.print(f"  Total operations: {len(operations)}")
        console.print(f"  Successful: {successful}")
        if failed > 0:
            console.print(f"  Failed: {failed}")
        if dry_runs > 0:
            console.print(f"  Dry-runs: {dry_runs}")

        if total_size > 0:
            if total_size < 1024 * 1024:
                size_str = f"{total_size / 1024:.1f}KB"
            elif total_size < 1024 * 1024 * 1024:
                size_str = f"{total_size / (1024 * 1024):.1f}MB"
            else:
                size_str = f"{total_size / (1024 * 1024 * 1024):.2f}GB"
            console.print(f"  Total data processed: {size_str}")

        console.print()

    except Exception as e:
        console.print(f"[red]Error retrieving history: {e}[/red]")
        raise typer.Exit(1)


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
            history = db.get_operation_history(limit=1)
            console.print("[green]✓[/green] Database: Connected")
            console.print(f"  Location: {DEFAULT_DB_PATH}")
            console.print(f"  Size: {DEFAULT_DB_PATH.stat().st_size / 1024:.1f} KB" if DEFAULT_DB_PATH.exists() else "  Size: N/A")
        except Exception as e:
            console.print(f"[red]✗[/red] Database: Error - {e}")

        # Check cache
        try:
            cache = ChecksumCache(DEFAULT_DB_PATH)
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

        console.print(f"\n[green]System is operational[/green]\n")

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

        # Clear checksum cache
        db = Database(DEFAULT_DB_PATH)
        cursor = db.conn.cursor()

        # Get cache size before clearing
        cursor.execute("SELECT COUNT(*) FROM checksum_cache")
        cache_count = cursor.fetchone()[0]

        # Clear cache
        cursor.execute("DELETE FROM checksum_cache")
        db.conn.commit()

        console.print(f"[green]✓[/green] Cleared {cache_count} cached checksums")

        # Vacuum database
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
        from fileflow_core.file_scanner import FileScanner
        from collections import defaultdict

        scanner = FileScanner()
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

        for checksum, files in duplicates.items():
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

        for idx, (checksum, files) in enumerate(sorted(duplicates.items(), key=lambda x: len(x[1]), reverse=True), 1):
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

            for idx, (checksum, files) in enumerate(sorted(duplicates.items(), key=lambda x: len(x[1]), reverse=True), 1):
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
                    to_delete = []
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
    import click
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
