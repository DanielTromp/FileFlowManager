"""
Typer CLI commands for FileFlow Manager.
"""

import subprocess
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from fileflow_config.config_manager import ConfigManager
from fileflow_config.defaults import create_default_config_file
from fileflow_core.logging_config import setup_logging
from fileflow_core.rule_engine import RuleEngine
from fileflow_storage.cache import ChecksumCache
from fileflow_storage.database import Database

app = typer.Typer(help="FileFlow Manager - Automated File Organization")
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


@app.command()
def test() -> None:
    """Test command."""
    console.print("Test command works!")


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


if __name__ == "__main__":
    app()
