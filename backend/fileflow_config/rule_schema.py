"""
Rule schema validation for FileFlow Manager.

Additional validation logic beyond Pydantic's built-in validation.
"""

import os
import re
from pathlib import Path

from fileflow_core.models import Rule


class RuleValidator:
    """Validate rule configuration."""

    @staticmethod
    def validate_glob_pattern(pattern: str) -> tuple[bool, str]:
        """Validate a glob pattern."""
        # Check for valid glob syntax
        invalid_chars = ["<", ">", "|", "\0"]
        for char in invalid_chars:
            if char in pattern:
                return False, f"Invalid character in pattern: {char}"

        # Pattern should not be empty
        if not pattern.strip():
            return False, "Pattern cannot be empty"

        return True, ""

    @staticmethod
    def validate_file_type(file_type: str) -> tuple[bool, str]:
        """Validate a file type extension."""
        # Remove leading dot if present
        file_type = file_type.lstrip(".")

        # Check for valid characters (alphanumeric only)
        if not re.match(r"^[a-zA-Z0-9]+$", file_type):
            return False, f"Invalid file type: {file_type}. Use alphanumeric characters only."

        # Check length (reasonable extension length)
        if len(file_type) > 10:
            return False, f"File type too long: {file_type}. Maximum 10 characters."

        return True, ""

    @staticmethod
    def validate_directory(directory: str, expand_vars: bool = True) -> tuple[bool, str]:
        """Validate a directory path."""
        # Allow environment variables
        if directory.startswith("${"):
            if not expand_vars:
                return True, ""  # Can't validate env vars without expansion

        # Expand and check if exists
        if expand_vars:
            expanded = os.path.expandvars(os.path.expanduser(directory))
            # Replace common macOS variables
            expanded = expanded.replace("${DESKTOP}", str(Path.home() / "Desktop"))
            expanded = expanded.replace("${DOWNLOADS}", str(Path.home() / "Downloads"))
            expanded = expanded.replace("${DOCUMENTS}", str(Path.home() / "Documents"))
            expanded = expanded.replace("${HOME}", str(Path.home()))

            if not Path(expanded).exists():
                return (
                    False,
                    f"Directory does not exist: {directory} (expanded to {expanded})",
                )

            if not os.access(expanded, os.R_OK):
                return False, f"Directory is not readable: {directory}"

        return True, ""

    @staticmethod
    def validate_destination(destination: str, check_writable: bool = True) -> tuple[bool, str]:
        """Validate destination path."""
        # Allow environment variables
        if destination.startswith("${"):
            return True, ""  # Will be expanded at runtime

        # Allow template variables
        if "{" in destination:
            return True, ""  # Will be expanded at runtime

        if check_writable:
            expanded = os.path.expandvars(os.path.expanduser(destination))
            expanded = expanded.replace("${DESKTOP}", str(Path.home() / "Desktop"))
            expanded = expanded.replace("${DOWNLOADS}", str(Path.home() / "Downloads"))
            expanded = expanded.replace("${DOCUMENTS}", str(Path.home() / "Documents"))
            expanded = expanded.replace("${HOME}", str(Path.home()))

            dest_path = Path(expanded)

            # Check parent exists or can be created
            if not dest_path.parent.exists():
                try:
                    dest_path.parent.mkdir(parents=True, exist_ok=True)
                except Exception as e:
                    return False, f"Cannot create destination directory: {e}"

            # Check writable
            if dest_path.exists() and not os.access(dest_path, os.W_OK):
                return False, f"Destination is not writable: {destination}"

        return True, ""

    @classmethod
    def validate_rule(cls, rule: Rule, check_filesystem: bool = True) -> tuple[bool, list[str]]:
        """Validate entire rule configuration."""
        errors = []

        # Validate patterns
        for pattern in rule.source_patterns:
            valid, error = cls.validate_glob_pattern(pattern)
            if not valid:
                errors.append(f"Source pattern error: {error}")

        for pattern in rule.exclude_patterns:
            valid, error = cls.validate_glob_pattern(pattern)
            if not valid:
                errors.append(f"Exclude pattern error: {error}")

        # Validate file types
        for file_type in rule.file_types:
            valid, error = cls.validate_file_type(file_type)
            if not valid:
                errors.append(error)

        # Validate directories
        if check_filesystem:
            for directory in rule.source_directories:
                valid, error = cls.validate_directory(directory)
                if not valid:
                    errors.append(f"Source directory error: {error}")

            valid, error = cls.validate_destination(rule.destination)
            if not valid:
                errors.append(f"Destination error: {error}")

        # Validate priority
        if rule.priority < 1 or rule.priority > 1000:
            errors.append(f"Priority must be between 1 and 1000, got {rule.priority}")

        # Validate size constraints
        if rule.min_size_kb is not None and rule.max_size_kb is not None:
            if rule.min_size_kb >= rule.max_size_kb:
                errors.append(
                    f"min_size_kb ({rule.min_size_kb}) must be less than max_size_kb ({rule.max_size_kb})"
                )

        # Validate age constraints
        if rule.min_age_days is not None and rule.max_age_days is not None:
            if rule.min_age_days >= rule.max_age_days:
                errors.append(
                    f"min_age_days ({rule.min_age_days}) must be less than max_age_days ({rule.max_age_days})"
                )

        return len(errors) == 0, errors

    @staticmethod
    def sanitize_rule_id(name: str) -> str:
        """Generate a safe rule ID from a name."""
        # Convert to lowercase
        rule_id = name.lower()

        # Replace spaces and special chars with hyphens
        rule_id = re.sub(r"[^a-z0-9]+", "-", rule_id)

        # Remove leading/trailing hyphens
        rule_id = rule_id.strip("-")

        # Ensure it matches the pattern
        if not re.match(r"^[a-z0-9_-]+$", rule_id):
            raise ValueError(f"Cannot generate valid rule ID from name: {name}")

        return rule_id
