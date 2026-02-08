"""Unit tests for association-enhanced search (v5.3.0).

Tests:
- DFSSearchEngine._expand_via_associations()
- GreeumMCPTools._get_associations_for_block()
- get_memory_stats association/consolidation stats
"""

import json
import os
import sqlite3
import tempfile
import unittest
from unittest.mock import MagicMock

import numpy as np


class _TempDB:
    """Minimal DB fixture reused across test classes."""

    def __init__(self):
        self.tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.tmp.close()
        self.conn = sqlite3.connect(self.tmp.name)
        self.conn.row_factory = sqlite3.Row
        self._create_schema()

    def _create_schema(self):
        self.conn.executescript("""
            CREATE TABLE IF NOT EXISTS blocks (
                block_index INTEGER PRIMARY KEY,
                timestamp TEXT NOT NULL DEFAULT '2026-01-01T00:00:00',
                context TEXT NOT NULL DEFAULT '',
                importance REAL NOT NULL DEFAULT 0.5,
                hash TEXT NOT NULL DEFAULT '',
                prev_hash TEXT NOT NULL DEFAULT '',
                slot TEXT,
                root TEXT,
                before TEXT,
                after TEXT DEFAULT '[]',
                xref TEXT DEFAULT '[]',
                branch_depth INTEGER DEFAULT 0,
                visit_count INTEGER DEFAULT 0,
                last_seen_at REAL DEFAULT 0,
                branch_similarity REAL DEFAULT 0,
                branch_created_at REAL DEFAULT 0
            );
            CREATE TABLE IF NOT EXISTS block_embeddings (
                block_index INTEGER PRIMARY KEY,
                embedding BLOB NOT NULL,
                embedding_model TEXT,
                embedding_dim INTEGER
            );
            CREATE TABLE IF NOT EXISTS block_keywords (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                block_index INTEGER NOT NULL,
                keyword TEXT NOT NULL,
                UNIQUE(block_index, keyword)
            );
            CREATE TABLE IF NOT EXISTS block_tags (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                block_index INTEGER NOT NULL,
                tag TEXT NOT NULL,
                UNIQUE(block_index, tag)
            );
            CREATE TABLE IF NOT EXISTS memory_nodes (
                node_id TEXT PRIMARY KEY,
                memory_id INTEGER,
                node_type TEXT,
                content TEXT,
                embedding TEXT,
                activation_level REAL,
                last_activated TEXT,
                metadata TEXT,
                created_at TEXT
            );
            CREATE TABLE IF NOT EXISTS associations (
                association_id TEXT PRIMARY KEY,
                source_node_id TEXT,
                target_node_id TEXT,
                association_type TEXT,
                strength REAL,
                weight REAL,
                created_at TEXT,
                last_activated TEXT,
                activation_count INTEGER,
                metadata TEXT
            );
            CREATE TABLE IF NOT EXISTS consolidation_state (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                block_a INTEGER NOT NULL,
                block_b INTEGER NOT NULL,
                cosine_similarity REAL,
                verdict TEXT NOT NULL,
                connection_type TEXT,
                strength REAL,
                justification TEXT,
                association_id TEXT,
                llm_model TEXT,
                prompt_tokens INTEGER,
                completion_tokens INTEGER,
                latency_ms INTEGER,
                compared_at TEXT NOT NULL,
                UNIQUE(block_a, block_b)
            );
            CREATE TABLE IF NOT EXISTS consolidation_queue (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                block_index INTEGER NOT NULL UNIQUE,
                queued_at TEXT NOT NULL,
                status TEXT DEFAULT 'pending'
            );
        """)
        self.conn.commit()

    def insert_block(self, idx, context="test", embedding=None):
        self.conn.execute(
            "INSERT INTO blocks (block_index, context) VALUES (?, ?)",
            (idx, context),
        )
        if embedding is not None:
            arr = np.array(embedding, dtype=np.float32)
            self.conn.execute(
                "INSERT INTO block_embeddings (block_index, embedding, embedding_model, embedding_dim) VALUES (?, ?, ?, ?)",
                (idx, arr.tobytes(), "test", len(arr)),
            )
        self.conn.commit()

    def insert_node(self, node_id, memory_id, content=""):
        self.conn.execute(
            "INSERT INTO memory_nodes (node_id, memory_id, node_type, content, created_at) VALUES (?, ?, 'memory', ?, '2026-01-01')",
            (node_id, memory_id, content),
        )
        self.conn.commit()

    def insert_association(self, assoc_id, src, tgt, atype="semantic", strength=0.7):
        self.conn.execute(
            "INSERT INTO associations (association_id, source_node_id, target_node_id, association_type, strength, weight, created_at, activation_count, metadata) VALUES (?, ?, ?, ?, ?, 1.0, '2026-01-01', 0, '{}')",
            (assoc_id, src, tgt, atype, strength),
        )
        self.conn.commit()

    def close(self):
        self.conn.close()
        os.unlink(self.tmp.name)


# ---------------------------------------------------------------------------
# DFSSearchEngine._expand_via_associations tests
# ---------------------------------------------------------------------------

class TestExpandViaAssociations(unittest.TestCase):
    """Test the _expand_via_associations method of DFSSearchEngine."""

    def setUp(self):
        self.tdb = _TempDB()
        # Create a minimal db_manager mock whose .conn returns our connection
        self.db_manager = MagicMock()
        self.db_manager.conn = self.tdb.conn

        # Insert blocks and nodes
        self.tdb.insert_block(1, "Block one")
        self.tdb.insert_block(2, "Block two")
        self.tdb.insert_block(3, "Block three")
        self.tdb.insert_block(4, "Block four (unrelated)")

        self.tdb.insert_node("node_1", 1, "Block one")
        self.tdb.insert_node("node_2", 2, "Block two")
        self.tdb.insert_node("node_3", 3, "Block three")
        self.tdb.insert_node("node_4", 4, "Block four")

        # Associations: 1↔2 (semantic 0.8), 1→3 (causal 0.6)
        self.tdb.insert_association("a1", "node_1", "node_2", "semantic", 0.8)
        self.tdb.insert_association("a2", "node_1", "node_3", "causal", 0.6)

    def tearDown(self):
        self.tdb.close()

    def _make_engine(self):
        """Create a DFSSearchEngine with mocked dependencies."""
        from greeum.core.dfs_search import DFSSearchEngine
        # Patch __init__ to avoid full initialization
        engine = object.__new__(DFSSearchEngine)
        engine.db_manager = self.db_manager
        return engine

    def test_expands_from_found_indices(self):
        engine = self._make_engine()
        # Start from block 1, expect expansion to block 2 and 3
        results = engine._expand_via_associations({1}, limit=5)
        result_indices = {r['block_index'] for r in results}
        self.assertIn(2, result_indices)
        self.assertIn(3, result_indices)
        self.assertNotIn(1, result_indices)  # Should not include already-found

    def test_bidirectional_lookup(self):
        engine = self._make_engine()
        # Start from block 2 → should find block 1 (reverse direction) and maybe 3 via 1
        results = engine._expand_via_associations({2}, limit=5)
        result_indices = {r['block_index'] for r in results}
        self.assertIn(1, result_indices)  # Reverse direction of node_1→node_2

    def test_respects_limit(self):
        engine = self._make_engine()
        results = engine._expand_via_associations({1}, limit=1)
        self.assertEqual(len(results), 1)
        # Should be block 2 (highest strength 0.8)
        self.assertEqual(results[0]['block_index'], 2)

    def test_excludes_found_indices(self):
        engine = self._make_engine()
        # If block 2 is already found, it should not be in results
        results = engine._expand_via_associations({1, 2}, limit=5)
        result_indices = {r['block_index'] for r in results}
        self.assertNotIn(1, result_indices)
        self.assertNotIn(2, result_indices)
        self.assertIn(3, result_indices)

    def test_empty_found_indices(self):
        engine = self._make_engine()
        results = engine._expand_via_associations(set(), limit=5)
        self.assertEqual(results, [])

    def test_no_associations_returns_empty(self):
        engine = self._make_engine()
        results = engine._expand_via_associations({4}, limit=5)
        self.assertEqual(results, [])

    def test_results_sorted_by_strength(self):
        engine = self._make_engine()
        results = engine._expand_via_associations({1}, limit=5)
        # Block 2 (strength 0.8) should come before block 3 (strength 0.6)
        if len(results) >= 2:
            self.assertEqual(results[0]['block_index'], 2)
            self.assertEqual(results[1]['block_index'], 3)


# ---------------------------------------------------------------------------
# GreeumMCPTools._get_associations_for_block tests
# ---------------------------------------------------------------------------

class TestGetAssociationsForBlock(unittest.TestCase):
    """Test the _get_associations_for_block method of GreeumMCPTools."""

    def setUp(self):
        self.tdb = _TempDB()
        self.tdb.insert_block(10, "Memory ten")
        self.tdb.insert_block(20, "Memory twenty")
        self.tdb.insert_node("n10", 10, "Memory ten")
        self.tdb.insert_node("n20", 20, "Memory twenty")
        self.tdb.insert_association("a_10_20", "n10", "n20", "semantic", 0.75)

    def tearDown(self):
        self.tdb.close()

    def _make_tools(self):
        from greeum.mcp.native.tools import GreeumMCPTools
        db_mgr = MagicMock()
        db_mgr.conn = self.tdb.conn
        components = {
            'db_manager': db_mgr,
            'duplicate_detector': MagicMock(),
            'quality_validator': MagicMock(),
            'usage_analytics': MagicMock(),
        }
        tools = object.__new__(GreeumMCPTools)
        tools.components = components
        return tools

    def test_returns_association_string(self):
        tools = self._make_tools()
        result = tools._get_associations_for_block(10)
        self.assertIn("semantic", result)
        self.assertIn("#20", result)
        self.assertIn("0.75", result)

    def test_returns_empty_for_no_associations(self):
        tools = self._make_tools()
        # Block 999 has no node
        result = tools._get_associations_for_block(999)
        self.assertEqual(result, "")

    def test_returns_empty_for_negative_index(self):
        tools = self._make_tools()
        result = tools._get_associations_for_block(-1)
        self.assertEqual(result, "")

    def test_bidirectional_association(self):
        tools = self._make_tools()
        # Query from block 20 should also find the association to 10
        result = tools._get_associations_for_block(20)
        self.assertIn("semantic", result)
        self.assertIn("#10", result)


# ---------------------------------------------------------------------------
# Consolidation queue tests
# ---------------------------------------------------------------------------

class TestConsolidationQueue(unittest.TestCase):
    """Test the consolidation_queue table and queue-based operations."""

    def setUp(self):
        self.tdb = _TempDB()

    def tearDown(self):
        self.tdb.close()

    def test_queue_insert(self):
        """Simulate what block_manager does when adding a block."""
        self.tdb.conn.execute(
            "INSERT OR IGNORE INTO consolidation_queue (block_index, queued_at, status) VALUES (?, ?, 'pending')",
            (42, "2026-02-08T12:00:00"),
        )
        self.tdb.conn.commit()

        cur = self.tdb.conn.execute("SELECT * FROM consolidation_queue WHERE block_index = 42")
        row = cur.fetchone()
        self.assertIsNotNone(row)
        self.assertEqual(row["status"], "pending")

    def test_queue_unique_constraint(self):
        """Duplicate block_index should be ignored (INSERT OR IGNORE)."""
        self.tdb.conn.execute(
            "INSERT OR IGNORE INTO consolidation_queue (block_index, queued_at, status) VALUES (?, ?, 'pending')",
            (42, "2026-02-08T12:00:00"),
        )
        self.tdb.conn.execute(
            "INSERT OR IGNORE INTO consolidation_queue (block_index, queued_at, status) VALUES (?, ?, 'pending')",
            (42, "2026-02-08T13:00:00"),
        )
        self.tdb.conn.commit()

        cur = self.tdb.conn.execute("SELECT COUNT(*) FROM consolidation_queue WHERE block_index = 42")
        self.assertEqual(cur.fetchone()[0], 1)

    def test_state_manager_creates_queue_table(self):
        """StateManager._ensure_table should create consolidation_queue."""
        # Use a fresh DB without the queue table
        tmp2 = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        tmp2.close()
        try:
            from greeum.consolidator.db import ConsolidatorDB
            from greeum.consolidator.state import StateManager

            db = ConsolidatorDB(tmp2.name)
            db.connect()
            # Create minimum schema for state manager
            db.conn.executescript("""
                CREATE TABLE IF NOT EXISTS memory_nodes (
                    node_id TEXT PRIMARY KEY, memory_id INTEGER, node_type TEXT,
                    content TEXT, embedding TEXT, activation_level REAL,
                    last_activated TEXT, metadata TEXT, created_at TEXT
                );
                CREATE TABLE IF NOT EXISTS associations (
                    association_id TEXT PRIMARY KEY, source_node_id TEXT,
                    target_node_id TEXT, association_type TEXT, strength REAL,
                    weight REAL, created_at TEXT, last_activated TEXT,
                    activation_count INTEGER, metadata TEXT
                );
            """)
            db.conn.commit()

            state = StateManager(db)

            # Verify consolidation_queue exists
            cur = db.conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='consolidation_queue'"
            )
            self.assertIsNotNone(cur.fetchone())

            db.close()
        finally:
            os.unlink(tmp2.name)


# ---------------------------------------------------------------------------
# get_memory_stats enrichment tests
# ---------------------------------------------------------------------------

class TestGetMemoryStatsEnrichment(unittest.TestCase):
    """Test that get_memory_stats includes association and consolidation info."""

    def setUp(self):
        self.tdb = _TempDB()
        self.tdb.insert_block(1, "Block 1")
        self.tdb.insert_block(2, "Block 2")
        self.tdb.insert_node("n1", 1, "Block 1")
        self.tdb.insert_node("n2", 2, "Block 2")
        self.tdb.insert_association("a1", "n1", "n2", "semantic", 0.7)

        # Add consolidation state
        self.tdb.conn.execute(
            "INSERT INTO consolidation_state (block_a, block_b, cosine_similarity, verdict, compared_at) VALUES (1, 2, 0.8, 'connected', '2026-01-01')"
        )
        self.tdb.conn.commit()

    def tearDown(self):
        self.tdb.close()

    def _make_tools(self):
        from greeum.mcp.native.tools import GreeumMCPTools
        db_mgr = MagicMock()
        db_mgr.conn = self.tdb.conn

        # get_last_block_info returns block 2 as last
        db_mgr.get_last_block_info.return_value = {'block_index': 1}

        components = {
            'db_manager': db_mgr,
            'duplicate_detector': MagicMock(),
            'quality_validator': MagicMock(),
            'usage_analytics': MagicMock(),
        }
        tools = object.__new__(GreeumMCPTools)
        tools.components = components
        tools._add_lock = None
        tools._write_queue_send = None
        return tools

    def test_stats_include_associations(self):
        import asyncio
        tools = self._make_tools()
        result = asyncio.get_event_loop().run_until_complete(
            tools._handle_get_memory_stats({})
        )
        self.assertIn("Associations", result)
        self.assertIn("semantic", result)

    def test_stats_include_consolidation(self):
        import asyncio
        tools = self._make_tools()
        result = asyncio.get_event_loop().run_until_complete(
            tools._handle_get_memory_stats({})
        )
        self.assertIn("Consolidation", result)
        self.assertIn("connected", result)


if __name__ == "__main__":
    unittest.main()
