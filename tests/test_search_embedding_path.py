"""Regression test for the silent query-embedding bug (block #347, 2026-07-27).

Root cause: BlockManager.search_with_slots did
    registry = EmbeddingRegistry(); registry.get_model('default')
but nothing is registered under the key 'default' → ValueError → swallowed by a
bare `except: pass` → query_embedding stayed None → the vector branch of DFS
search was silently skipped → every search degraded to keyword-only.

Our v5.4 eval harness bypassed BlockManager.search_with_slots (it called the
HybridScorer directly), so it never caught this. These tests exercise the real
search path.
"""
from __future__ import annotations

import os
import tempfile
import unittest
from unittest.mock import patch


class TestGetModelDefaultTrap(unittest.TestCase):
    """Document the trap: 'default' is NOT a registered model key."""

    def test_get_model_default_raises(self):
        from greeum.embedding_models import embedding_registry
        # This is exactly what the buggy code did — it must raise, proving the
        # old code path could only ever hit the bare-except and lose the embedding.
        with self.assertRaises(ValueError):
            embedding_registry.get_model("default")

    def test_get_embedding_helper_works(self):
        """The fix uses get_embedding() → encodes with the registry default_model."""
        from greeum.embedding_models import get_embedding
        vec = get_embedding("의미 검색 테스트 문장")
        self.assertIsInstance(vec, list)
        self.assertGreater(len(vec), 0)
        # Not all-zero (a real embedding, not a dead vector)
        self.assertTrue(any(abs(x) > 1e-9 for x in vec))


class TestSearchPopulatesQueryEmbedding(unittest.TestCase):
    """Integration: search_with_slots must pass a non-None query_embedding to DFS."""

    def setUp(self):
        self._tmp = tempfile.mkdtemp(prefix="greeum_search_path_")
        os.environ["GREEUM_DATA_DIR"] = self._tmp
        os.environ["GREEUM_SILENT_HASH_FALLBACK"] = "1"
        from greeum.core import DatabaseManager
        from greeum.core.block_manager import BlockManager
        self.db = DatabaseManager(connection_string=os.path.join(self._tmp, "memory.db"))
        self.bm = BlockManager(self.db)

    def tearDown(self):
        try:
            self.db.close()
        except Exception:
            pass

    def test_query_embedding_reaches_dfs(self):
        """Before the fix this was None; after the fix it is a real vector."""
        captured = {}

        real_import = __import__

        from greeum.core.dfs_search import DFSSearchEngine

        orig = DFSSearchEngine.search_with_dfs

        def spy(self, query, query_embedding=None, **kwargs):
            captured["query_embedding"] = query_embedding
            return [], {"hops": 0, "fallback_used": True, "search_type": "local"}

        with patch.object(DFSSearchEngine, "search_with_dfs", spy):
            self.bm.search_with_slots("한국어 의미 검색 쿼리", limit=5)

        self.assertIn("query_embedding", captured)
        self.assertIsNotNone(
            captured["query_embedding"],
            "query_embedding must be populated — the vector branch was silently "
            "skipped before the #347 fix",
        )
        # And it's a real embedding of non-trivial length.
        self.assertGreater(len(captured["query_embedding"]), 0)


if __name__ == "__main__":
    unittest.main()
