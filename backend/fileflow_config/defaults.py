"""
Default rules and presets for FileFlow Manager.

Provides sensible defaults for common file organization scenarios.
"""

from datetime import datetime

from fileflow_core.models import (
    Configuration,
    DuplicateHandling,
    GeneralSettings,
    PathSettings,
    Rule,
    ThresholdSettings,
)


def get_default_screenshot_rule() -> Rule:
    """Get the default screenshot organization rule (enabled by default)."""
    return Rule(
        id="screenshot-org",
        enabled=True,
        name="Screenshot Organization",
        description="Automatically organize screenshots by date into Downloads/screenshots/YYYY/MM/DD",
        source_patterns=[
            "Screenshot*.png",
            "Screen Shot*.png",
            "Screenshot*.jpg",
            "Screen Shot*.jpg",
        ],
        source_directories=["${DESKTOP}", "${DOWNLOADS}"],
        destination="${DOWNLOADS}/screenshots",
        organize_by_date=True,
        file_types=["png", "jpg", "jpeg"],
        priority=1,
        exclude_patterns=[],
        min_size_kb=None,
        max_size_kb=None,
        min_age_days=None,
        max_age_days=None,
        created_at=datetime.now(),
        last_modified=datetime.now(),
    )


def get_preset_rules() -> list[Rule]:
    """Get list of preset rules (disabled by default, user can enable)."""
    return [
        Rule(
            id="pdf-org",
            enabled=False,
            name="PDF Organization",
            description="Organize PDF files by date",
            source_patterns=["*.pdf"],
            source_directories=["${DESKTOP}", "${DOWNLOADS}"],
            destination="${DOCUMENTS}/PDFs",
            organize_by_date=True,
            file_types=["pdf"],
            priority=10,
            exclude_patterns=[],
            min_size_kb=None,
            max_size_kb=None,
            min_age_days=None,
            max_age_days=None,
            created_at=datetime.now(),
            last_modified=datetime.now(),
        ),
        Rule(
            id="image-org",
            enabled=False,
            name="Image Organization",
            description="Organize images (excluding screenshots) by date",
            source_patterns=["*.jpg", "*.jpeg", "*.png", "*.gif", "*.heic"],
            source_directories=["${DESKTOP}", "${DOWNLOADS}"],
            destination="${PICTURES}/Organized",
            organize_by_date=True,
            file_types=["jpg", "jpeg", "png", "gif", "heic"],
            priority=20,
            exclude_patterns=["Screenshot*", "Screen Shot*"],
            min_size_kb=None,
            max_size_kb=None,
            min_age_days=None,
            max_age_days=None,
            created_at=datetime.now(),
            last_modified=datetime.now(),
        ),
        Rule(
            id="video-org",
            enabled=False,
            name="Video Organization",
            description="Organize video files by date",
            source_patterns=["*.mp4", "*.mov", "*.avi", "*.mkv"],
            source_directories=["${DESKTOP}", "${DOWNLOADS}"],
            destination="${PICTURES}/Videos",
            organize_by_date=True,
            file_types=["mp4", "mov", "avi", "mkv"],
            priority=20,
            exclude_patterns=[],
            min_size_kb=None,
            max_size_kb=None,
            min_age_days=None,
            max_age_days=None,
            created_at=datetime.now(),
            last_modified=datetime.now(),
        ),
        Rule(
            id="document-org",
            enabled=False,
            name="Document Organization",
            description="Organize document files (Word, Excel, PowerPoint)",
            source_patterns=[
                "*.doc",
                "*.docx",
                "*.xls",
                "*.xlsx",
                "*.ppt",
                "*.pptx",
            ],
            source_directories=["${DESKTOP}", "${DOWNLOADS}"],
            destination="${DOCUMENTS}/Office",
            organize_by_date=False,
            file_types=["doc", "docx", "xls", "xlsx", "ppt", "pptx"],
            priority=15,
            exclude_patterns=[],
            min_size_kb=None,
            max_size_kb=None,
            min_age_days=None,
            max_age_days=None,
            created_at=datetime.now(),
            last_modified=datetime.now(),
        ),
        Rule(
            id="code-org",
            enabled=False,
            name="Code Files",
            description="Organize code files by type",
            source_patterns=[
                "*.py",
                "*.js",
                "*.ts",
                "*.jsx",
                "*.tsx",
                "*.java",
                "*.cpp",
                "*.c",
                "*.h",
            ],
            source_directories=["${DESKTOP}", "${DOWNLOADS}"],
            destination="${DOCUMENTS}/Code",
            organize_by_date=False,
            file_types=["py", "js", "ts", "jsx", "tsx", "java", "cpp", "c", "h"],
            priority=20,
            exclude_patterns=[],
            min_size_kb=None,
            max_size_kb=None,
            min_age_days=None,
            max_age_days=None,
            created_at=datetime.now(),
            last_modified=datetime.now(),
        ),
    ]


def get_default_configuration() -> Configuration:
    """Get default configuration with screenshot rule enabled."""
    return Configuration(
        general=GeneralSettings(
            log_level="INFO",
            auto_run_on_startup=False,
            auto_run_interval_minutes=60,
            enable_notifications=True,
            cache_enabled=True,
        ),
        paths=PathSettings(
            screenshot_source="${DESKTOP}",
            screenshot_destination="${DOWNLOADS}/screenshots",
            monitored_directories=["${DESKTOP}", "${DOWNLOADS}"],
        ),
        thresholds=ThresholdSettings(
            large_file_mb=100,
            old_file_days=90,
        ),
        duplicate_handling=DuplicateHandling(
            auto_delete_duplicates=False,
            always_keep_oldest=True,
        ),
        rules=[
            get_default_screenshot_rule(),
            *get_preset_rules(),
        ],
    )


def create_default_config_file(config_path: str) -> None:
    """Create default configuration file if it doesn't exist."""
    from pathlib import Path

    from fileflow_config.config_manager import ConfigManager

    path = Path(config_path)
    if not path.exists():
        config = get_default_configuration()
        manager = ConfigManager(config_path)
        manager.save(config)
