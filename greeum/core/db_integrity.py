"""Utility helpers for detecting and repairing SQLite corruption.

이 모듈은 런타임 또는 테스트 중 "database disk image is malformed" 오류가
발생했을 때 자동 백업과 복구를 수행하기 위한 공통 로직을 제공한다.
CLI `greeum setup`에서 사용하던 백업 전략과 동일한 규칙을 재사용해
서비스 경로와 테스트 환경 모두에서 일관된 동작을 보장한다.
"""

from __future__ import annotations

import logging
import shutil
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Optional

LOGGER = logging.getLogger(__name__)

_CORRUPTION_MARKERS = (
    "malformed",
    "database disk image is malformed",
    "not a database",
    "file is encrypted",
    "file is not a database",
)


def is_corruption_error(exc: BaseException) -> bool:
    """Return True if the exception message indicates SQLite corruption."""

    message = str(exc).lower()
    return any(marker in message for marker in _CORRUPTION_MARKERS)


def backup_database_files(db_path: Path, label: str = "malformed") -> Optional[Path]:
    """Back up the database and its sidecar files.

    The backup is stored under ``<data-dir>/backups`` with timestamped filenames.
    Returns the main backup path when a file was copied, otherwise ``None``.
    """

    if not db_path.exists():
        return None

    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    backup_dir = db_path.parent / "backups"
    backup_dir.mkdir(parents=True, exist_ok=True)

    backup_name = f"{db_path.stem}_{label}_{timestamp}{db_path.suffix}"
    backup_path = backup_dir / backup_name
    shutil.copy2(db_path, backup_path)

    for suffix in ("-wal", "-shm"):
        sidecar = Path(f"{db_path}{suffix}")
        if sidecar.exists():
            sidecar_backup = backup_dir / f"{backup_name}{suffix}"
            shutil.copy2(sidecar, sidecar_backup)

    return backup_path


def remove_database_files(db_path: Path) -> None:
    """Remove the database file and its associated WAL/SHM files if present."""

    for candidate in (
        db_path,
        Path(f"{db_path}-wal"),
        Path(f"{db_path}-shm"),
    ):
        try:
            candidate.unlink()
        except FileNotFoundError:
            continue
        except PermissionError as exc:  # pragma: no cover - defensive logging
            LOGGER.warning("Failed to remove %s during repair: %s", candidate, exc)


def rebuild_empty_sqlite_database(db_path: Path) -> None:
    """Create a fresh empty SQLite database at ``db_path``."""

    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    conn.close()

