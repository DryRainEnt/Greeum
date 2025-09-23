import os
import time
from datetime import datetime, timedelta
from pathlib import Path

import pytest

from greeum.core.branch_aware_storage import BranchAwareStorage
from greeum.core.branch_index import BranchIndexManager
from greeum.core.database_manager import DatabaseManager
from greeum.core.stm_anchor_store import STMAnchorStore


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
    anchor_path = tmp_path / "stm_anchors.db"
    prev_anchor_env = os.environ.get("GREEUM_STM_DB")
    os.environ["GREEUM_STM_DB"] = str(anchor_path)
    # Reset anchor store singleton so tests use the isolated path
    from greeum.core import stm_anchor_store
    stm_anchor_store._singleton = None


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

    anchor_store = STMAnchorStore(anchor_path)
    now_ts = time.time()
    anchor_store.upsert_slot(
        slot_name="A",
        anchor_block="hash-alpha-1",
        topic_vec=None,
        summary=root_alpha,
        last_seen=now_ts,
        hysteresis=0,
    )
    anchor_store.upsert_slot(
        slot_name="B",
        anchor_block="hash-beta-1",
        topic_vec=None,
        summary=root_beta,
        last_seen=now_ts,
        hysteresis=0,
    )
    anchor_store.close()

    branch_index_manager = BranchIndexManager(manager)
    storage = BranchAwareStorage(manager, branch_index_manager)

    return manager, storage, root_alpha, root_beta, prev_anchor_env


@pytest.fixture()
def storage_env(tmp_path: Path):
    manager, storage, root_alpha, root_beta, prev_anchor_env = _prepare_storage(tmp_path)
    try:
        yield manager, storage, root_alpha, root_beta
    finally:
        manager.conn.close()
        if prev_anchor_env is not None:
            os.environ["GREEUM_STM_DB"] = prev_anchor_env
        else:
            os.environ.pop("GREEUM_STM_DB", None)


def test_fallback_prefers_keyword_overlap(storage_env):
    manager, storage, root_alpha, root_beta = storage_env
    storage.keyword_weight = 0.9
    storage.temporal_weight = 0.1

    result = storage.store_with_branch_awareness(
        content="Alpha roadmap overview",
        embedding=None,
        importance=0.6,
    )

    assert result["selected_slot"] == "A"


def test_fallback_prefers_recent_when_no_keywords(storage_env):
    manager, storage, root_alpha, root_beta = storage_env
    storage.keyword_weight = 0.1
    storage.temporal_weight = 0.9

    result = storage.store_with_branch_awareness(
        content="General progress summary",
        embedding=None,
        importance=0.4,
    )

    assert result["selected_slot"] == "B"
