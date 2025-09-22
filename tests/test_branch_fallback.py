import time
from datetime import datetime, timedelta
from pathlib import Path

import pytest

from greeum.core.branch_aware_storage import BranchAwareStorage
from greeum.core.branch_index import BranchIndexManager
from greeum.core.database_manager import DatabaseManager


def _add_block(manager: DatabaseManager, *, block_index: int, context: str, root: str,
               timestamp: str, keywords, tags, hash_value: str, prev_hash: str = "0" * 64):
    block_data = {
        "block_index": block_index,
        "timestamp": timestamp,
        "context": context,
        "importance": 0.5,
        "hash": hash_value,
        "prev_hash": prev_hash,
        "root": root,
        "before": None,
        "after": [],
        "xref": [],
        "branch_depth": 0,
        "visit_count": 0,
        "last_seen_at": 0,
        "slot": None,
        "branch_similarity": 0.0,
        "branch_created_at": time.time(),
        "keywords": keywords,
        "tags": tags,
        "metadata": {},
        "embedding": [0.1, 0.2, 0.3],
        "embedding_model": "unit-test",
    }
    manager.add_block(block_data)


def _prepare_storage(tmp_path: Path):
    db_path = tmp_path / "memory.db"
    manager = DatabaseManager(connection_string=str(db_path))

    now_iso = datetime.utcnow().isoformat()
    older_iso = (datetime.utcnow() - timedelta(days=2)).isoformat()

    root_alpha = "root-alpha"
    root_beta = "root-beta"

    _add_block(
        manager,
        block_index=1,
        context="Alpha roadmap planning",
        root=root_alpha,
        timestamp=older_iso,
        keywords=["alpha", "roadmap"],
        tags=["alpha"],
        hash_value="hash-alpha-1",
    )

    _add_block(
        manager,
        block_index=2,
        context="Beta launch checklist",
        root=root_beta,
        timestamp=now_iso,
        keywords=["beta", "launch"],
        tags=["beta"],
        hash_value="hash-beta-1",
        prev_hash="hash-alpha-1",
    )

    cursor = manager.conn.cursor()
    cursor.execute(
        "UPDATE stm_slots SET block_hash=?, branch_root=?, updated_at=? WHERE slot_name='A'",
        ("hash-alpha-1", root_alpha, time.time()),
    )
    cursor.execute(
        "UPDATE stm_slots SET block_hash=?, branch_root=?, updated_at=? WHERE slot_name='B'",
        ("hash-beta-1", root_beta, time.time()),
    )
    manager.conn.commit()

    branch_index_manager = BranchIndexManager(manager)
    storage = BranchAwareStorage(manager, branch_index_manager)

    return manager, storage, root_alpha, root_beta


@pytest.fixture()
def storage_env(tmp_path: Path):
    manager, storage, root_alpha, root_beta = _prepare_storage(tmp_path)
    try:
        yield manager, storage, root_alpha, root_beta
    finally:
        manager.conn.close()


def test_fallback_prefers_keyword_overlap(storage_env):
    manager, storage, root_alpha, root_beta = storage_env

    result = storage.store_with_branch_awareness(
        content="Alpha roadmap overview",
        embedding=None,
        importance=0.6,
    )

    assert result["branch_root"] == root_alpha
    assert result["selected_slot"] == "A"


def test_fallback_prefers_recent_when_no_keywords(storage_env):
    manager, storage, root_alpha, root_beta = storage_env

    result = storage.store_with_branch_awareness(
        content="General progress summary",
        embedding=None,
        importance=0.4,
    )

    assert result["branch_root"] == root_beta
    assert result["selected_slot"] == "B"
