"""Branch-aware schema version management for Greeum.

이 모듈은 브랜치 메타데이터 컬럼과 STM 앵커 저장소가 준비되었는지 확인하고
필요 시 안전하게 스키마를 업그레이드하는 단순한 버전 관리 유틸리티를 제공합니다.
"""

from __future__ import annotations

import logging
import os
import sqlite3
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Dict, Optional

from ..branch_schema import BranchSchemaSQL

logger = logging.getLogger(__name__)


class SchemaVersion(Enum):
    """High level schema states used by the branch-aware preview."""

    LEGACY = "legacy"
    BRANCH_READY = "branch-ready"
    EMPTY = "empty"
    UNKNOWN = "unknown"


@dataclass
class SchemaInspection:
    """Snapshot describing the current database schema state."""

    version: SchemaVersion
    needs_migration: bool
    block_count: int = 0
    has_branch_tables: bool = False


class SchemaVersionManager:
    """SQLite schema inspector/upgrade helper for branch meta columns."""

    def __init__(self, db_path: str):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn: Optional[sqlite3.Connection] = None

    # ------------------------------------------------------------------
    # Connection helpers
    # ------------------------------------------------------------------
    def connect(self) -> None:
        if self.conn is None:
            self.conn = sqlite3.connect(str(self.db_path))
            self.conn.row_factory = sqlite3.Row

    def close(self) -> None:
        if self.conn is not None:
            self.conn.close()
            self.conn = None

    def _cursor(self) -> sqlite3.Cursor:
        self.connect()
        assert self.conn is not None  # For type checkers
        return self.conn.cursor()

    # ------------------------------------------------------------------
    # Inspection utilities
    # ------------------------------------------------------------------
    def inspect(self) -> SchemaInspection:
        cursor = self._cursor()

        # Determine whether we have any data at all.
        cursor.execute(
            """
            SELECT name FROM sqlite_master
            WHERE type='table' AND name='blocks'
            """
        )
        blocks_table_exists = cursor.fetchone() is not None

        if not blocks_table_exists:
            return SchemaInspection(version=SchemaVersion.EMPTY, needs_migration=True)

        # Count total blocks for reporting.
        cursor.execute("SELECT COUNT(*) FROM blocks")
        block_count = int(cursor.fetchone()[0])

        needs_migration = BranchSchemaSQL.check_migration_needed(cursor)

        branch_tables_present = not needs_migration
        version = SchemaVersion.BRANCH_READY if branch_tables_present else SchemaVersion.LEGACY

        return SchemaInspection(
            version=version,
            needs_migration=needs_migration,
            block_count=block_count,
            has_branch_tables=branch_tables_present,
        )

    def detect_schema_version(self) -> SchemaVersion:
        return self.inspect().version

    def needs_migration(self) -> bool:
        return self.inspect().needs_migration

    # ------------------------------------------------------------------
    # Upgrade helpers
    # ------------------------------------------------------------------
    def _ensure_base_tables(self, cursor: sqlite3.Cursor) -> None:
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS blocks (
                block_index INTEGER PRIMARY KEY,
                timestamp TEXT NOT NULL,
                context TEXT NOT NULL,
                importance REAL NOT NULL,
                hash TEXT NOT NULL,
                prev_hash TEXT NOT NULL
            )
            """
        )

    def upgrade_to_branch_schema(self) -> bool:
        """Apply BranchSchemaSQL statements if the schema is not yet updated."""

        cursor = self._cursor()
        self._ensure_base_tables(cursor)

        statements = BranchSchemaSQL.get_migration_sql()
        statements_run = 0

        try:
            for sql in statements:
                try:
                    cursor.execute(sql)
                    statements_run += 1
                except sqlite3.OperationalError as exc:
                    message = str(exc).lower()
                    if "duplicate" in message or "exists" in message:
                        logger.debug("Skipping already-applied SQL: %s", sql.strip().split("\n")[0])
                        continue
                    raise

            if self.conn:
                self.conn.commit()

            logger.info("Branch schema upgrade completed (%s statements)", statements_run)
            return True
        except Exception as exc:  # noqa: BLE001 - broad to rollback safely
            if self.conn:
                self.conn.rollback()
            logger.error("Branch schema upgrade failed: %s", exc)
            return False

    # ------------------------------------------------------------------
    # Validation utilities
    # ------------------------------------------------------------------
    def validate_schema_integrity(self) -> Dict[str, Any]:
        cursor = self._cursor()
        issues: Dict[str, Any] = {"ok": True, "errors": [], "warnings": []}

        try:
            cursor.execute("PRAGMA table_info(blocks)")
            columns = {row[1] for row in cursor.fetchall()}
            required_columns = {
                "root",
                "before",
                "after",
                "xref",
                "slot",
                "branch_similarity",
                "branch_created_at",
            }

            missing_columns = sorted(required_columns - columns)
            if missing_columns:
                issues["ok"] = False
                issues["errors"].append({"missing_columns": missing_columns})

            cursor.execute(
                """
                SELECT name FROM sqlite_master
                WHERE type='table' AND name='branch_meta'
                """
            )
            if not cursor.fetchone():
                issues["ok"] = False
                issues["errors"].append({"missing_table": "branch_meta"})

            anchor_path = Path(
                os.environ.get("GREEUM_STM_DB", str(self.db_path.parent / "stm_anchors.db"))
            ).expanduser()
            if not anchor_path.exists():
                issues["warnings"].append({
                    "missing_anchor_store": str(anchor_path),
                    "hint": "STM 앵커 저장소가 초기화되지 않았습니다. greeum setup 또는 STMManager 초기화를 실행해 주세요.",
                })

        except Exception as exc:  # noqa: BLE001
            issues["ok"] = False
            issues["errors"].append({"exception": str(exc)})

        return issues


class MigrationVersionGuard:
    """Utility to guard branch-aware features behind a schema check."""

    def __init__(self, version_manager: SchemaVersionManager):
        self.version_manager = version_manager

    def check_compatibility(self) -> bool:
        return self.version_manager.detect_schema_version() == SchemaVersion.BRANCH_READY

    def enforce_compatibility(self) -> None:
        if not self.check_compatibility():
            inspection = self.version_manager.inspect()
            raise RuntimeError(
                "Branch metadata is not ready. "
                f"Current version: {inspection.version.value}. "
                "Run `greeum migrate check` to upgrade the schema."
            )
