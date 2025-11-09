"""
Database migrations framework for FileFlow Manager.

Simple migration system for schema changes.
"""

import sqlite3
from datetime import datetime
from pathlib import Path


class Migration:
    """Base class for database migrations."""

    version: int
    description: str

    def up(self, conn: sqlite3.Connection) -> None:
        """Apply migration."""
        raise NotImplementedError

    def down(self, conn: sqlite3.Connection) -> None:
        """Rollback migration."""
        raise NotImplementedError


class InitialSchema(Migration):
    """Initial database schema - v1."""

    version = 1
    description = "Initial schema with operations and checksum_cache tables"

    def up(self, conn: sqlite3.Connection) -> None:
        """Create initial schema."""
        cursor = conn.cursor()

        # This is handled by database.py, but included here for completeness
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS operations (
                id TEXT PRIMARY KEY,
                timestamp DATETIME NOT NULL,
                operation_type TEXT NOT NULL,
                source_path TEXT NOT NULL,
                destination_path TEXT,
                file_size INTEGER NOT NULL,
                checksum TEXT NOT NULL,
                rule_id TEXT NOT NULL,
                dry_run BOOLEAN NOT NULL,
                success BOOLEAN NOT NULL,
                error_message TEXT,
                skip_reason TEXT,
                duplicate_of TEXT
            )
            """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS checksum_cache (
                file_path TEXT PRIMARY KEY,
                checksum TEXT NOT NULL,
                file_size INTEGER NOT NULL,
                modified_time DATETIME NOT NULL,
                cached_at DATETIME NOT NULL
            )
            """
        )

        conn.commit()

    def down(self, conn: sqlite3.Connection) -> None:
        """Drop initial schema."""
        cursor = conn.cursor()
        cursor.execute("DROP TABLE IF EXISTS operations")
        cursor.execute("DROP TABLE IF EXISTS checksum_cache")
        conn.commit()


class MigrationManager:
    """Manage database migrations."""

    def __init__(self, db_path: str | Path):
        """Initialize migration manager."""
        self.db_path = Path(db_path)
        self.conn = sqlite3.connect(str(self.db_path))
        self._create_migration_table()
        self.migrations: list[Migration] = [InitialSchema()]

    def _create_migration_table(self) -> None:
        """Create migrations tracking table."""
        cursor = self.conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS migrations (
                version INTEGER PRIMARY KEY,
                description TEXT NOT NULL,
                applied_at DATETIME NOT NULL
            )
            """
        )
        self.conn.commit()

    def get_current_version(self) -> int:
        """Get current database version."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT MAX(version) as version FROM migrations")
        result = cursor.fetchone()
        return result[0] if result[0] is not None else 0

    def migrate(self, target_version: int | None = None) -> None:
        """Run migrations up to target version."""
        current_version = self.get_current_version()

        if target_version is None:
            target_version = max(m.version for m in self.migrations)

        for migration in sorted(self.migrations, key=lambda m: m.version):
            if migration.version > current_version and migration.version <= target_version:
                print(f"Applying migration {migration.version}: {migration.description}")
                migration.up(self.conn)

                # Record migration
                cursor = self.conn.cursor()
                cursor.execute(
                    "INSERT INTO migrations (version, description, applied_at) VALUES (?, ?, ?)",
                    (migration.version, migration.description, datetime.now().isoformat()),
                )
                self.conn.commit()

    def rollback(self, target_version: int = 0) -> None:
        """Rollback migrations to target version."""
        current_version = self.get_current_version()

        for migration in sorted(self.migrations, key=lambda m: m.version, reverse=True):
            if migration.version <= current_version and migration.version > target_version:
                print(f"Rolling back migration {migration.version}: {migration.description}")
                migration.down(self.conn)

                # Remove migration record
                cursor = self.conn.cursor()
                cursor.execute("DELETE FROM migrations WHERE version = ?", (migration.version,))
                self.conn.commit()

    def close(self) -> None:
        """Close database connection."""
        self.conn.close()
