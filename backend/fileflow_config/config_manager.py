"""
TOML configuration management for FileFlow Manager.

Handles reading, writing, and validating configuration files.
"""

import os
from pathlib import Path
from typing import Dict, Optional

try:
    import tomllib  # Python 3.11+
except ModuleNotFoundError:
    import tomli as tomllib  # Python 3.10 backport

from fileflow_core.models import Configuration, Rule


class ConfigManager:
    """Manage TOML configuration files."""

    def __init__(self, config_path: str | Path):
        """Initialize configuration manager."""
        self.config_path = Path(config_path)
        self.config_path.parent.mkdir(parents=True, exist_ok=True)

    def load(self) -> Configuration:
        """Load configuration from TOML file."""
        if not self.config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {self.config_path}")

        with open(self.config_path, "rb") as f:
            data = tomllib.load(f)

        # Parse configuration with Pydantic validation
        return Configuration(**data)

    def save(self, config: Configuration) -> None:
        """Save configuration to TOML file."""
        # Convert to dict and write as TOML
        toml_content = self._to_toml(config.model_dump())

        # Atomic write: write to temp file then rename
        temp_path = self.config_path.with_suffix(".toml.tmp")
        with open(temp_path, "w") as f:
            f.write(toml_content)

        temp_path.replace(self.config_path)

    def _to_toml(self, data: dict, indent: int = 0) -> str:
        """Convert dictionary to TOML format."""
        lines = []
        indent_str = "  " * indent

        # Process non-table items first
        for key, value in data.items():
            if value is None:
                continue  # Skip None values entirely
            elif isinstance(value, dict):
                continue  # Handle tables separately
            elif isinstance(value, list):
                if value and isinstance(value[0], dict):
                    continue  # Array of tables handled separately
                else:
                    lines.append(f"{indent_str}{key} = {self._format_value(value)}")
            else:
                lines.append(f"{indent_str}{key} = {self._format_value(value)}")

        # Process tables
        for key, value in data.items():
            if isinstance(value, dict):
                if indent == 0:
                    lines.append(f"\n[{key}]")
                    lines.append(self._to_toml(value, indent + 1).rstrip())
                else:
                    # Nested table
                    lines.append(f"\n{indent_str}[{key}]")
                    lines.append(self._to_toml(value, indent + 1).rstrip())

        # Process array of tables (like rules)
        for key, value in data.items():
            if isinstance(value, list) and value and isinstance(value[0], dict):
                for item in value:
                    lines.append(f"\n[[{key}]]")
                    lines.append(self._to_toml(item, indent + 1).rstrip())

        return "\n".join(lines) + "\n"

    def _format_value(self, value) -> str:
        """Format a value for TOML."""
        if value is None:
            raise ValueError("None values should not reach _format_value")
        elif isinstance(value, bool):
            return "true" if value else "false"
        elif isinstance(value, str):
            # Escape quotes and backslashes
            escaped = value.replace("\\", "\\\\").replace('"', '\\"')
            return f'"{escaped}"'
        elif isinstance(value, (int, float)):
            return str(value)
        elif isinstance(value, list):
            formatted_items = [self._format_value(item) for item in value]
            return "[" + ", ".join(formatted_items) + "]"
        else:
            return str(value)

    def expand_env_vars(self, path: str) -> str:
        """Expand environment variables in path."""
        # Common macOS path variables
        replacements = {
            "${HOME}": str(Path.home()),
            "${DESKTOP}": str(Path.home() / "Desktop"),
            "${DOWNLOADS}": str(Path.home() / "Downloads"),
            "${DOCUMENTS}": str(Path.home() / "Documents"),
            "${PICTURES}": str(Path.home() / "Pictures"),
        }

        expanded = path
        for var, value in replacements.items():
            expanded = expanded.replace(var, value)

        # Also handle standard environment variable syntax
        expanded = os.path.expandvars(expanded)
        expanded = os.path.expanduser(expanded)

        return expanded

    def validate(self) -> tuple[bool, Optional[str]]:
        """Validate configuration file."""
        try:
            config = self.load()

            # Additional validation
            for rule in config.rules:
                # Check source directories exist or use env vars
                for source_dir in rule.source_directories:
                    expanded = self.expand_env_vars(source_dir)
                    if not expanded.startswith("$") and not Path(expanded).exists():
                        return False, f"Source directory not found for rule '{rule.name}': {source_dir}"

                # Check destination is writable or uses env vars
                dest = self.expand_env_vars(rule.destination)
                if not dest.startswith("$"):
                    dest_path = Path(dest)
                    if dest_path.exists() and not os.access(dest_path, os.W_OK):
                        return False, f"Destination not writable for rule '{rule.name}': {rule.destination}"

            return True, None

        except FileNotFoundError as e:
            return False, str(e)
        except Exception as e:
            return False, f"Configuration validation failed: {str(e)}"

    def export(self, destination: str | Path) -> None:
        """Export configuration to another location."""
        config = self.load()
        temp_manager = ConfigManager(destination)
        temp_manager.save(config)

    def import_config(self, source: str | Path, merge: bool = False) -> None:
        """Import configuration from another location."""
        source_manager = ConfigManager(source)
        new_config = source_manager.load()

        if merge and self.config_path.exists():
            # Merge with existing configuration
            existing_config = self.load()

            # Merge rules (keep existing, add new)
            existing_rule_ids = {rule.id for rule in existing_config.rules}
            for rule in new_config.rules:
                if rule.id not in existing_rule_ids:
                    existing_config.rules.append(rule)

            # Update settings (imported config takes precedence)
            existing_config.general = new_config.general
            existing_config.paths = new_config.paths
            existing_config.thresholds = new_config.thresholds
            existing_config.duplicate_handling = new_config.duplicate_handling

            self.save(existing_config)
        else:
            # Replace entire configuration
            self.save(new_config)

    def get_rule(self, rule_id: str) -> Optional[Rule]:
        """Get a specific rule by ID."""
        config = self.load()
        for rule in config.rules:
            if rule.id == rule_id:
                return rule
        return None

    def add_rule(self, rule: Rule) -> None:
        """Add a new rule to configuration."""
        config = self.load()

        # Check for duplicate ID
        if any(r.id == rule.id for r in config.rules):
            raise ValueError(f"Rule with ID '{rule.id}' already exists")

        # Check for duplicate name
        if any(r.name == rule.name for r in config.rules):
            raise ValueError(f"Rule with name '{rule.name}' already exists")

        config.rules.append(rule)
        self.save(config)

    def update_rule(self, rule_id: str, updates: Dict) -> Rule:
        """Update an existing rule."""
        config = self.load()

        rule_index = None
        for i, rule in enumerate(config.rules):
            if rule.id == rule_id:
                rule_index = i
                break

        if rule_index is None:
            raise ValueError(f"Rule with ID '{rule_id}' not found")

        # Update rule with new values
        updated_rule = config.rules[rule_index].model_copy(update=updates)
        config.rules[rule_index] = updated_rule

        self.save(config)
        return updated_rule

    def delete_rule(self, rule_id: str) -> None:
        """Delete a rule from configuration."""
        config = self.load()

        config.rules = [rule for rule in config.rules if rule.id != rule_id]
        self.save(config)

    def toggle_rule(self, rule_id: str, enabled: bool) -> Rule:
        """Enable or disable a rule."""
        return self.update_rule(rule_id, {"enabled": enabled})
