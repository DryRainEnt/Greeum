"""Greeum branch-aware migration helpers.

v3.x에서는 AI 기반 액턴트 마이그레이션을 제거하고 브랜치 메타데이터 확장을
다루는 경량 유틸리티만 유지합니다.
"""

from .schema_version import (
    SchemaVersionManager,
    SchemaVersion,
    MigrationVersionGuard,
)

from .backup_system import (
    AtomicBackupSystem,
    BackupMetadata,
    TransactionSafetyWrapper,
)

from .migration_interface import (
    BranchMigrationInterface,
    MigrationCLI,
    MigrationResult,
)

__all__ = [
    "SchemaVersionManager",
    "SchemaVersion",
    "MigrationVersionGuard",
    "AtomicBackupSystem",
    "BackupMetadata",
    "TransactionSafetyWrapper",
    "BranchMigrationInterface",
    "MigrationCLI",
    "MigrationResult",
]

try:  # align with top-level package version when available
    from greeum import __version__ as _pkg_version
except ImportError:  # pragma: no cover - during isolated tests
    _pkg_version = "unknown"

__migration_version__ = SchemaVersion.BRANCH_READY
__version__ = _pkg_version
