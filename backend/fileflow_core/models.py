"""
Data models for FileFlow Manager.

This module defines all core data structures using Pydantic for validation.
Models are based on the data-model.md specification.
"""

from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import List, Optional
from uuid import uuid4

from pydantic import BaseModel, Field, computed_field, field_validator


class OperationType(str, Enum):
    """Type of file operation."""

    MOVE = "move"
    DELETE = "delete"
    SKIP = "skip"


class SkipReason(str, Enum):
    """Reason for skipping a file operation."""

    NAME_CONFLICT = "name_conflict"
    PERMISSION_DENIED = "permission_denied"
    ALREADY_PROCESSED = "already_processed"
    FILE_NOT_FOUND = "file_not_found"


class Rule(BaseModel):
    """File organization rule configuration."""

    id: str = Field(..., pattern=r"^[a-z0-9_-]+$")
    enabled: bool = True
    name: str = Field(..., min_length=1, max_length=100)
    description: str = Field(..., max_length=500)
    source_patterns: List[str] = Field(..., min_length=1)
    source_directories: List[str] = Field(..., min_length=1)
    destination: str
    organize_by_date: bool = False
    detect_duplicates: bool = True
    recursive_search: bool = True
    file_types: List[str] = Field(..., min_length=1)
    priority: int = Field(10, ge=1, le=1000)
    exclude_patterns: List[str] = Field(default_factory=list)
    min_size_kb: Optional[int] = Field(None, ge=0)
    max_size_kb: Optional[int] = Field(None, ge=0)
    min_age_days: Optional[int] = Field(None, ge=0)
    max_age_days: Optional[int] = Field(None, ge=0)
    created_at: datetime = Field(default_factory=datetime.now)
    last_modified: datetime = Field(default_factory=datetime.now)

    @field_validator("max_size_kb")
    @classmethod
    def validate_max_size(cls, v: Optional[int], info) -> Optional[int]:
        """Ensure max_size is greater than min_size if both are set."""
        if v is not None and info.data.get("min_size_kb") is not None:
            if v <= info.data["min_size_kb"]:
                raise ValueError("max_size_kb must be greater than min_size_kb")
        return v

    @field_validator("max_age_days")
    @classmethod
    def validate_max_age(cls, v: Optional[int], info) -> Optional[int]:
        """Ensure max_age is greater than min_age if both are set."""
        if v is not None and info.data.get("min_age_days") is not None:
            if v <= info.data["min_age_days"]:
                raise ValueError("max_age_days must be greater than min_age_days")
        return v


class FileMetadata(BaseModel):
    """Metadata about a file to be organized."""

    path: str
    filename: str
    extension: str
    size_bytes: int = Field(ge=0)
    created_at: datetime
    modified_at: datetime
    checksum: Optional[str] = None
    matched_rules: List[str] = Field(default_factory=list)

    @computed_field
    @property
    def age_days(self) -> int:
        """Calculate file age in days since last modification."""
        return (datetime.now() - self.modified_at).days

    @computed_field
    @property
    def size_mb(self) -> float:
        """File size in megabytes."""
        return round(self.size_bytes / (1024 * 1024), 2)


class FileOperation(BaseModel):
    """Record of a file operation (move, delete, skip)."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    timestamp: datetime = Field(default_factory=datetime.now)
    operation_type: OperationType
    source_path: str
    destination_path: Optional[str] = None
    file_size: int = Field(ge=0)
    checksum: str
    rule_id: str
    dry_run: bool = False
    success: bool = False
    error_message: Optional[str] = None
    skip_reason: Optional[SkipReason] = None
    duplicate_of: Optional[str] = None

    @field_validator("destination_path")
    @classmethod
    def validate_destination(
        cls, v: Optional[str], info
    ) -> Optional[str]:
        """Ensure destination is set for move operations."""
        if info.data.get("operation_type") == OperationType.MOVE and v is None:
            raise ValueError("destination_path required for move operations")
        return v


class DuplicatePair(BaseModel):
    """Pair of duplicate files with identical checksums."""

    original_path: str
    duplicate_path: str
    checksum: str
    file_size: int = Field(ge=0)


class ScanResult(BaseModel):
    """Result of scanning directories for file organization."""

    scan_id: str = Field(default_factory=lambda: str(uuid4()))
    timestamp: datetime = Field(default_factory=datetime.now)
    total_files_scanned: int = Field(ge=0)
    files_matched: int = Field(ge=0)
    planned_operations: List[FileOperation] = Field(default_factory=list)
    duplicate_pairs: List[DuplicatePair] = Field(default_factory=list)
    large_files: List[FileMetadata] = Field(default_factory=list)
    old_files: List[FileMetadata] = Field(default_factory=list)
    scan_duration_ms: int = Field(ge=0)

    @computed_field
    @property
    def estimated_space_freed_mb(self) -> float:
        """Estimate space to be freed by duplicate deletion."""
        total_bytes = sum(pair.file_size for pair in self.duplicate_pairs)
        return round(total_bytes / (1024 * 1024), 2)


class GeneralSettings(BaseModel):
    """General application settings."""

    log_level: str = Field(default="INFO", pattern=r"^(DEBUG|INFO|WARNING|ERROR)$")
    auto_run_on_startup: bool = False
    auto_run_interval_minutes: int = Field(default=60, ge=1)
    enable_notifications: bool = True
    cache_enabled: bool = True


class PathSettings(BaseModel):
    """Path configuration settings."""

    screenshot_source: str
    screenshot_destination: str
    monitored_directories: List[str] = Field(default_factory=list)


class ThresholdSettings(BaseModel):
    """Detection threshold settings."""

    large_file_mb: int = Field(default=100, ge=1)
    old_file_days: int = Field(default=90, ge=1)


class DuplicateHandling(BaseModel):
    """Duplicate file handling preferences."""

    auto_delete_duplicates: bool = False
    always_keep_oldest: bool = True


class Configuration(BaseModel):
    """Complete application configuration."""

    general: GeneralSettings = Field(default_factory=GeneralSettings)
    paths: PathSettings
    thresholds: ThresholdSettings = Field(default_factory=ThresholdSettings)
    duplicate_handling: DuplicateHandling = Field(default_factory=DuplicateHandling)
    rules: List[Rule] = Field(default_factory=list)


class ChecksumCacheEntry(BaseModel):
    """Cached checksum entry for a file."""

    file_path: str
    checksum: str
    file_size: int = Field(ge=0)
    modified_time: datetime
    cached_at: datetime = Field(default_factory=datetime.now)

    def is_valid(self, current_modified_time: datetime, current_size: int) -> bool:
        """Check if cache entry is still valid."""
        return (
            self.modified_time == current_modified_time
            and self.file_size == current_size
        )
