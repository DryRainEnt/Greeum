import numpy as np
import pytest

from greeum.core.branch_index import BranchIndexManager
from greeum.core.database_manager import DatabaseManager

faiss = pytest.importorskip("faiss")


def _add_block(manager: DatabaseManager, block_index: int, root: str, context: str, embedding):
    block_data = {
        "block_index": block_index,
        "timestamp": "2024-01-01T00:00:00",
        "context": context,
        "importance": 0.5,
        "hash": f"hash-{block_index}",
        "prev_hash": "hash-0" if block_index > 1 else "0" * 64,
        "root": root,
        "before": None,
        "after": [],
        "xref": [],
        "branch_depth": 0,
        "visit_count": 0,
        "last_seen_at": 0,
        "slot": None,
        "branch_similarity": 0.0,
        "branch_created_at": 0.0,
        "keywords": [],
        "tags": [],
        "metadata": {},
        "embedding": embedding,
        "embedding_model": "unit-test",
    }
    manager.add_block(block_data)


def test_branch_index_vector_search(tmp_path):
    db_path = tmp_path / "memory.db"
    manager = DatabaseManager(connection_string=str(db_path))

    _add_block(manager, 1, "root-alpha", "Alpha context", [1.0, 0.0, 0.0])
    _add_block(manager, 2, "root-beta", "Beta context", [0.0, 1.0, 0.0])

    branch_manager = BranchIndexManager(manager)
    stats = branch_manager.get_stats()

    assert stats["use_faiss"] is True
    assert stats["vectorized_branches"] >= 1

    query_embedding = np.array([0.0, 1.0, 0.0], dtype=np.float32)
    results = branch_manager.search_current_branch("nonsense", limit=1, query_embedding=query_embedding)

    assert results
    assert results[0]["block_index"] == 2

    manager.conn.close()
