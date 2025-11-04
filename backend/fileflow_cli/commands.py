"""
Typer CLI commands for FileFlow Manager.
"""

import subprocess
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table
from typing_extensions import Annotated

from fileflow_config.config_manager import ConfigManager
from fileflow_config.defaults import create_default_config_file
from fileflow_core.logging_config import setup_logging
from fileflow_core.rule_engine import RuleEngine
from fileflow_storage.cache import ChecksumCache
from fileflow_storage.database import Database

app = typer.Typer(
    help="FileFlow Manager - Automated File Organization",
    pretty_exceptions_show_locals=False,
    add_completion=False
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
def find_large() -> None:
    """Find files larger than 100MB."""
    from pathlib import Path
    from fileflow_core.file_scanner import FileScanner

    console.print("\n[bold]Finding files larger than 100 MB...[/bold]\n")

    # Get monitored directories from config
    config_mgr = get_config_manager()
    config = config_mgr.load()
    monitored_dirs = [Path(config_mgr.expand_env_vars(d)) for d in config.paths.monitored_directories]

    # Scan for large files
    scanner = FileScanner()
    large_files = scanner.find_large_files(directories=monitored_dirs, threshold_mb=100)

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
def find_old() -> None:
    """Find files older than 90 days."""
    from pathlib import Path
    from fileflow_core.file_scanner import FileScanner

    console.print("\n[bold]Finding files older than 90 days...[/bold]\n")

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
def config_export(output_path: str) -> None:
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
def config_import(input_path: str) -> None:
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
def config_import_merge(input_path: str) -> None:
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
def config_validate(config_path: Optional[str] = None) -> None:
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


if __name__ == "__main__":
    app()
