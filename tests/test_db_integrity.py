from pathlib import Path

from greeum.core.database_manager import DatabaseManager
from greeum.core.thread_safe_db import ThreadSafeDatabaseManager


def _write_malformed_db(db_path: Path) -> None:
    db_path.write_text("not-a-valid-sqlite-file")


def test_database_manager_repairs_malformed_sqlite(tmp_path) -> None:
    data_dir = tmp_path / "store"
    data_dir.mkdir()
    db_path = data_dir / "memory.db"
    _write_malformed_db(db_path)

    manager = DatabaseManager(connection_string=str(db_path))
    row = manager.conn.execute("PRAGMA integrity_check").fetchone()
    manager.conn.close()

    assert row is not None
    assert (row[0] or "").lower() == "ok"

    backups = list((data_dir / "backups").glob("memory_malformed_*.db"))
    assert backups, "expected malformed backup to be created"


def test_thread_safe_manager_repairs_malformed_sqlite(tmp_path) -> None:
    data_dir = tmp_path / "store"
    data_dir.mkdir()
    db_path = data_dir / "memory.db"
    _write_malformed_db(db_path)

    manager = ThreadSafeDatabaseManager(connection_string=str(db_path))
    conn = manager._get_connection()
    row = conn.execute("PRAGMA integrity_check").fetchone()

    assert row is not None
    assert (row[0] or "").lower() == "ok"

    backups = list((data_dir / "backups").glob("memory_malformed_*.db"))
    assert backups, "expected malformed backup to be created"

