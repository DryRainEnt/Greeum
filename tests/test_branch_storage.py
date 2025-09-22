import sqlite3
from pathlib import Path

import pytest

from greeum.core.database_manager import DatabaseManager
from greeum.core.migration.migration_interface import BranchMigrationInterface


@pytest.fixture()
def temp_data_dir(tmp_path: Path) -> Path:
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    return data_dir


def test_branch_columns_persist_after_migration(temp_data_dir: Path) -> None:
    interface = BranchMigrationInterface(str(temp_data_dir))
    result = interface.apply(create_backup=False)
    interface.close()

    assert result.ok
    db_path = temp_data_dir / "memory.db"

    manager = DatabaseManager(connection_string=str(db_path))

    block_data = {
        "block_index": 1,
        "timestamp": "2024-01-01T00:00:00",
        "context": "branch aware storage",
        "importance": 0.6,
        "hash": "hash-1",
        "prev_hash": "0" * 64,
        "root": "root-alpha",
        "before": None,
        "after": [],
        "xref": [],
        "branch_depth": 0,
        "visit_count": 0,
        "last_seen_at": 0,
        "slot": "A",
        "branch_similarity": 0.91,
        "branch_created_at": 1234567.0,
        "keywords": ["branch"],
        "tags": ["test"],
        "metadata": {},
        "embedding": [0.1, 0.2, 0.3],
        "embedding_model": "unit-test",
    }

    inserted = manager.add_block(block_data)
    assert inserted == 1

    cursor = manager.conn.cursor()
    cursor.execute(
        "SELECT slot, root, branch_similarity, branch_created_at FROM blocks WHERE block_index=?",
        (1,),
    )
    slot, root, similarity, created_at = cursor.fetchone()

    assert slot == "A"
    assert root == "root-alpha"
    assert pytest.approx(similarity, rel=1e-3) == 0.91
    assert created_at == pytest.approx(1234567.0)

    manager.conn.close()


def test_stm_slots_initialized(temp_data_dir: Path) -> None:
    interface = BranchMigrationInterface(str(temp_data_dir))
    interface.apply(create_backup=False)

    conn = sqlite3.connect(str(temp_data_dir / "memory.db"))
    cursor = conn.cursor()
    cursor.execute("SELECT slot_name, block_hash, branch_root FROM stm_slots ORDER BY slot_name")
    rows = cursor.fetchall()

    assert [row[0] for row in rows] == ["A", "B", "C"]
    # 초기 상태에서는 머리 포인터가 비어있어야 한다.
    assert all(row[1] is None for row in rows)
    assert all(row[2] is None for row in rows)

    conn.close()
    interface.close()
