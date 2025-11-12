"""
SQLite database management for FileFlow Manager.

Handles operation history and checksum caching with proper schema and indexing.
Enhanced with connection pooling for better performance.
"""

import sqlite3
from datetime import datetime
from pathlib import Path

from fileflow_core.cache import ConnectionPool
from fileflow_core.errors import DatabaseError
from fileflow_core.models import ChecksumCacheEntry, FileOperation, OperationType
from fileflow_core.retry import retry_database_operation


class Database:
    """SQLite database manager for FileFlow operations and cache."""

    def __init__(self, db_path: str | Path, pool_size: int = 5):
        """
        Initialize database with connection pooling.

        Args:
            db_path: Path to SQLite database file
            pool_size: Number of connections in the pool (default: 5)
        """
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        # Create connection pool instead of single connection
        self.pool = ConnectionPool(db_path=self.db_path, pool_size=pool_size)

        # Create schema using a connection from the pool
        self._create_schema()

    def _create_schema(self) -> None:
        """Create database schema if it doesn't exist."""
        with self.pool.get_connection() as conn:
            cursor = conn.cursor()

            # Operations table for audit trail
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS operations (
                    id TEXT PRIMARY KEY,
                    timestamp DATETIME NOT NULL,
                    operation_type TEXT NOT NULL CHECK(operation_type IN ('move', 'delete', 'skip')),
                    source_path TEXT NOT NULL,
                    destination_path TEXT,
                    file_size INTEGER NOT NULL,
                    checksum TEXT NOT NULL,
                    rule_id TEXT NOT NULL,
                    dry_run BOOLEAN NOT NULL,
                    success BOOLEAN NOT NULL,
                    error_message TEXT,
                    skip_reason TEXT,
                    duplicate_of TEXT,
                    FOREIGN KEY (duplicate_of) REFERENCES operations(id)
                )
                """
            )

            # Index for fast timestamp lookups
            cursor.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_operations_timestamp
                ON operations(timestamp DESC)
                """
            )

            # Index for rule-based queries
            cursor.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_operations_rule
                ON operations(rule_id)
                """
            )

            # Checksum cache table
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

            # Index for checksum lookups (duplicate detection)
            cursor.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_checksum_cache_checksum
                ON checksum_cache(checksum)
                """
            )

            conn.commit()

    @retry_database_operation
    def log_operation(self, operation: FileOperation) -> None:
        """
        Log a file operation to the database.

        Args:
            operation: File operation to log

        Raises:
            DatabaseError: If logging fails
        """
        try:
            with self.pool.get_connection() as conn:
                cursor = conn.cursor()

                cursor.execute(
                    """
                    INSERT INTO operations (
                        id, timestamp, operation_type, source_path, destination_path,
                        file_size, checksum, rule_id, dry_run, success,
                        error_message, skip_reason, duplicate_of
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        operation.id,
                        operation.timestamp.isoformat(),
                        operation.operation_type.value,
                        operation.source_path,
                        operation.destination_path,
                        operation.file_size,
                        operation.checksum,
                        operation.rule_id,
                        operation.dry_run,
                        operation.success,
                        operation.error_message,
                        operation.skip_reason.value if operation.skip_reason else None,
                        operation.duplicate_of,
                    ),
                )

                conn.commit()
        except sqlite3.Error as e:
            raise DatabaseError(
                f"Failed to log operation: {e}",
                db_path=str(self.db_path),
            ) from e

    @retry_database_operation
    def get_operation_history(
        self,
        limit: int = 100,
        offset: int = 0,
        operation_type: OperationType | None = None,
        rule_id: str | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        include_dry_runs: bool = False,
    ) -> list[FileOperation]:
        """
        Retrieve operation history with optional filtering.

        Args:
            limit: Maximum number of operations to return
            offset: Number of operations to skip
            operation_type: Filter by operation type
            rule_id: Filter by rule ID
            start_date: Filter by start date
            end_date: Filter by end date
            include_dry_runs: Include dry run operations

        Returns:
            List of file operations

        Raises:
            DatabaseError: If query fails
        """
        try:
            with self.pool.get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()

                query = "SELECT * FROM operations WHERE 1=1"
                params: list[str | int] = []

                if operation_type:
                    query += " AND operation_type = ?"
                    params.append(operation_type.value)

                if rule_id:
                    query += " AND rule_id = ?"
                    params.append(rule_id)

                if start_date:
                    query += " AND timestamp >= ?"
                    params.append(start_date.isoformat())

                if end_date:
                    query += " AND timestamp <= ?"
                    params.append(end_date.isoformat())

                if not include_dry_runs:
                    query += " AND dry_run = 0"

                query += " ORDER BY timestamp DESC LIMIT ? OFFSET ?"
                params.extend([limit, offset])

                cursor.execute(query, params)
                rows = cursor.fetchall()

                operations = []
                for row in rows:
                    operations.append(
                        FileOperation(
                            id=row["id"],
                            timestamp=datetime.fromisoformat(row["timestamp"]),
                            operation_type=OperationType(row["operation_type"]),
                            source_path=row["source_path"],
                            destination_path=row["destination_path"],
                            file_size=row["file_size"],
                            checksum=row["checksum"],
                            rule_id=row["rule_id"],
                            dry_run=bool(row["dry_run"]),
                            success=bool(row["success"]),
                            error_message=row["error_message"],
                            skip_reason=row["skip_reason"],
                            duplicate_of=row["duplicate_of"],
                        )
                    )

                return operations
        except sqlite3.Error as e:
            raise DatabaseError(
                f"Failed to retrieve operation history: {e}",
                db_path=str(self.db_path),
            ) from e

    @retry_database_operation
    def get_checksum(self, file_path: str) -> ChecksumCacheEntry | None:
        """
        Retrieve cached checksum for a file.

        Args:
            file_path: Path to the file

        Returns:
            Checksum cache entry or None if not found

        Raises:
            DatabaseError: If query fails
        """
        try:
            with self.pool.get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()

                cursor.execute(
                    "SELECT * FROM checksum_cache WHERE file_path = ?",
                    (file_path,),
                )

                row = cursor.fetchone()
                if not row:
                    return None

                return ChecksumCacheEntry(
                    file_path=row["file_path"],
                    checksum=row["checksum"],
                    file_size=row["file_size"],
                    modified_time=datetime.fromisoformat(row["modified_time"]),
                    cached_at=datetime.fromisoformat(row["cached_at"]),
                )
        except sqlite3.Error as e:
            raise DatabaseError(
                f"Failed to retrieve checksum: {e}",
                db_path=str(self.db_path),
            ) from e

    @retry_database_operation
    def cache_checksum(self, entry: ChecksumCacheEntry) -> None:
        """
        Cache a file checksum.

        Args:
            entry: Checksum cache entry to store

        Raises:
            DatabaseError: If caching fails
        """
        try:
            with self.pool.get_connection() as conn:
                cursor = conn.cursor()

                cursor.execute(
                    """
                    INSERT OR REPLACE INTO checksum_cache
                    (file_path, checksum, file_size, modified_time, cached_at)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        entry.file_path,
                        entry.checksum,
                        entry.file_size,
                        entry.modified_time.isoformat(),
                        entry.cached_at.isoformat(),
                    ),
                )

                conn.commit()
        except sqlite3.Error as e:
            raise DatabaseError(
                f"Failed to cache checksum: {e}",
                db_path=str(self.db_path),
            ) from e

    @retry_database_operation
    def find_duplicates_by_checksum(self, checksum: str) -> list[str]:
        """
        Find all files with the given checksum.

        Args:
            checksum: Checksum to search for

        Returns:
            List of file paths with matching checksum

        Raises:
            DatabaseError: If query fails
        """
        try:
            with self.pool.get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()

                cursor.execute(
                    "SELECT file_path FROM checksum_cache WHERE checksum = ?",
                    (checksum,),
                )

                return [row["file_path"] for row in cursor.fetchall()]
        except sqlite3.Error as e:
            raise DatabaseError(
                f"Failed to find duplicates: {e}",
                db_path=str(self.db_path),
            ) from e

    @retry_database_operation
    def clear_old_operations(self, days: int = 90) -> int:
        """
        Delete operations older than specified days.

        Args:
            days: Number of days to keep operations

        Returns:
            Number of deleted operations

        Raises:
            DatabaseError: If deletion fails
        """
        try:
            with self.pool.get_connection() as conn:
                cursor = conn.cursor()

                cutoff_date = datetime.now().timestamp() - (days * 24 * 60 * 60)
                cutoff_iso = datetime.fromtimestamp(cutoff_date).isoformat()

                cursor.execute(
                    "DELETE FROM operations WHERE timestamp < ?",
                    (cutoff_iso,),
                )

                deleted_count = cursor.rowcount
                conn.commit()

                return deleted_count
        except sqlite3.Error as e:
            raise DatabaseError(
                f"Failed to clear old operations: {e}",
                db_path=str(self.db_path),
            ) from e

    @retry_database_operation
    def clear_cache(self) -> int:
        """
        Clear all checksum cache entries.

        Returns:
            Number of deleted cache entries

        Raises:
            DatabaseError: If clearing fails
        """
        try:
            with self.pool.get_connection() as conn:
                cursor = conn.cursor()

                cursor.execute("DELETE FROM checksum_cache")

                deleted_count = cursor.rowcount
                conn.commit()

                return deleted_count
        except sqlite3.Error as e:
            raise DatabaseError(
                f"Failed to clear cache: {e}",
                db_path=str(self.db_path),
            ) from e

    def get_stats(self) -> dict:
        """
        Get database statistics.

        Returns:
            Dictionary with operations count, cache count, and database size
        """
        try:
            with self.pool.get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()

                cursor.execute("SELECT COUNT(*) as count FROM operations")
                operations_count = cursor.fetchone()["count"]

                cursor.execute("SELECT COUNT(*) as count FROM checksum_cache")
                cache_count = cursor.fetchone()["count"]

                # Get database file size
                db_size_mb = round(self.db_path.stat().st_size / (1024 * 1024), 2)

                # Get pool statistics
                pool_stats = self.pool.get_stats()

                return {
                    "operations_count": operations_count,
                    "cache_count": cache_count,
                    "database_size_mb": db_size_mb,
                    "connection_pool": pool_stats,
                }
        except Exception as e:
            raise DatabaseError(
                f"Failed to get statistics: {e}",
                db_path=str(self.db_path),
            ) from e

    def close(self) -> None:
        """Close all database connections in the pool."""
        self.pool.close_all()

    def __enter__(self) -> "Database":
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit."""
        self.close()
