"""Minimal branch-aware migration helpers.

이전 AI 기반 강제 마이그레이션 코드를 걷어내고, 브랜치 메타 컬럼 및 STM 슬롯이
준비되었는지 확인/적용하는 경량 인터페이스만 남겼습니다.
"""

from __future__ import annotations

import argparse
import logging
import sqlite3
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

from ..branch_schema import BranchSchemaSQL
from .backup_system import AtomicBackupSystem, TransactionSafetyWrapper
from .schema_version import SchemaVersionManager

logger = logging.getLogger(__name__)


@dataclass
class MigrationResult:
    """Outcome of applying the branch-aware migration."""

    applied: bool
    statements_run: int = 0
    statements_skipped: int = 0
    errors: List[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return self.applied and not self.errors


class BranchMigrationInterface:
    """High-level helper that upgrades a SQLite database in-place."""

    def __init__(self, data_dir: str, db_filename: str = "memory.db"):
        self.data_dir = Path(data_dir).expanduser()
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.db_path = self.data_dir / db_filename
        self.version_manager = SchemaVersionManager(str(self.db_path))
        self.backup_system = AtomicBackupSystem(str(self.data_dir))

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _cursor(self) -> sqlite3.Cursor:
        return self.version_manager._cursor()

    def _ensure_slot_defaults(self, cursor: sqlite3.Cursor) -> None:
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS stm_slots (
                slot_name TEXT PRIMARY KEY,
                block_hash TEXT,
                branch_root TEXT,
                updated_at REAL
            )
            """
        )
        for slot in ("A", "B", "C"):
            cursor.execute(
                """
                INSERT OR IGNORE INTO stm_slots(slot_name, block_hash, branch_root, updated_at)
                VALUES(?, NULL, NULL, 0)
                """,
                (slot,),
            )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def check(self) -> bool:
        """Return True if migration is required."""
        return self.version_manager.needs_migration()

    def apply(self, create_backup: bool = True) -> MigrationResult:
        """Apply branch schema migration if needed."""
        logger.info("Starting branch migration for %s", self.db_path)

        result = MigrationResult(applied=False)

        def _execute(cursor: sqlite3.Cursor) -> None:
            statements = BranchSchemaSQL.get_migration_sql()
            for sql in statements:
                try:
                    cursor.execute(sql)
                    result.statements_run += 1
                except sqlite3.OperationalError as exc:
                    message = str(exc).lower()
                    if "duplicate" in message or "exists" in message:
                        result.statements_skipped += 1
                        logger.debug("Skipping already-applied SQL: %s", sql.strip().split("\n")[0])
                        continue
                    result.errors.append(str(exc))
                    logger.error("Migration statement failed: %s", exc)
            self._ensure_slot_defaults(cursor)

        if not self.db_path.exists():
            # Touch the file so SQLite opens it without error.
            self.db_path.touch()

        cursor = self._cursor()
        self.version_manager._ensure_base_tables(cursor)

        try:
            if create_backup and self.db_path.exists():
                with TransactionSafetyWrapper(str(self.db_path), self.backup_system):
                    _execute(cursor)
                    if self.version_manager.conn:
                        self.version_manager.conn.commit()
            else:
                _execute(cursor)
                if self.version_manager.conn:
                    self.version_manager.conn.commit()

            result.applied = result.errors == []
            return result
        except Exception as exc:  # noqa: BLE001
            if self.version_manager.conn:
                self.version_manager.conn.rollback()
            result.errors.append(str(exc))
            logger.error("Branch migration failed: %s", exc)
            return result

    def close(self) -> None:
        self.version_manager.close()


class MigrationCLI:
    """Thin argparse wrapper replicating the previous entry point."""

    def __init__(self, data_dir: str):
        self.interface = BranchMigrationInterface(data_dir)

    def run(self, force: bool = False) -> int:
        needs_migration = self.interface.check()

        if not needs_migration and not force:
            print("✅ Branch schema already up to date.")
            self.interface.close()
            return 0

        result = self.interface.apply(create_backup=True)
        self.interface.close()

        if result.ok:
            print("✅ Branch schema migration applied.")
            if result.statements_skipped:
                print(f"   (skipped {result.statements_skipped} already-applied statements)")
            return 0

        print("[ERROR] Branch schema migration failed:")
        for error in result.errors:
            print(f"   • {error}")
        return 1


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Greeum branch schema migration tool")
    parser.add_argument("--data-dir", default="data", help="Data directory path")
    parser.add_argument(
        "--force",
        action="store_true",
        help="Apply migration even if the schema already reports branch-ready",
    )

    args = parser.parse_args(argv)

    cli = MigrationCLI(args.data_dir)
    exit_code = cli.run(force=args.force)
    return exit_code


if __name__ == "__main__":  # pragma: no cover - manual invocation
    raise SystemExit(main())
