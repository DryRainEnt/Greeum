from pathlib import Path

from click.testing import CliRunner

from greeum.cli.__init__ import main as greeum_cli
from greeum.core.database_manager import DatabaseManager


def _add_block(manager: DatabaseManager, block_index: int, root: str):
    block_data = {
        "block_index": block_index,
        "timestamp": "2024-01-01T00:00:00",
        "context": f"context-{block_index}",
        "importance": 0.5,
        "hash": f"hash-{block_index}",
        "prev_hash": "0" * 64,
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
        "keywords": ["sample"],
        "tags": [],
        "metadata": {},
        "embedding": [0.1, 0.2, 0.3],
        "embedding_model": "unit-test",
    }
    manager.add_block(block_data)


def test_cli_memory_reindex(tmp_path):
    data_dir = tmp_path / "data"
    data_dir.mkdir()

    db_path = data_dir / "memory.db"
    manager = DatabaseManager(connection_string=str(db_path))
    _add_block(manager, 1, "root-alpha")
    manager.conn.close()

    runner = CliRunner()
    result = runner.invoke(
        greeum_cli,
        ["memory", "reindex", "--data-dir", str(data_dir), "--disable-faiss"],
    )

    assert result.exit_code == 0
    assert "Rebuilt" in result.output
