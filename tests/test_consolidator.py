"""Unit tests for the Greeum Consolidator."""

import json
import os
import sqlite3
import tempfile
import unittest

import numpy as np

from greeum.consolidator.config import ConsolidatorConfig
from greeum.consolidator.db import ConsolidatorDB
from greeum.consolidator.state import StateManager, ComparisonRecord
from greeum.consolidator.candidates import select_candidates, CandidatePair
from greeum.consolidator.context_gatherer import ContextGatherer, BlockContext
from greeum.consolidator.judge import ConsolidationJudge, Verdict
from greeum.consolidator.llm_client import LLMResponse
from greeum.consolidator.prompts import build_deliberation_prompt
from greeum.consolidator.writer import AssociationWriter


class TestParseVerdict(unittest.TestCase):
    """Test the verdict parsing logic."""

    def _make_response(self, text: str) -> LLMResponse:
        return LLMResponse(content=text, prompt_tokens=100, completion_tokens=50, latency_ms=1000, model="test")

    def test_connect_verdict(self):
        resp = self._make_response(
            "VERDICT: CONNECT\nTYPE: semantic\nSTRENGTH: 0.75\nREASONING: Both discuss Python programming."
        )
        v = ConsolidationJudge._parse_verdict(resp)
        self.assertTrue(v.connect)
        self.assertEqual(v.connection_type, "semantic")
        self.assertAlmostEqual(v.strength, 0.75)
        self.assertIn("Python", v.reasoning)

    def test_reject_verdict(self):
        resp = self._make_response(
            "VERDICT: REJECT\nTYPE: semantic\nSTRENGTH: 0.15\nREASONING: Superficial similarity only."
        )
        v = ConsolidationJudge._parse_verdict(resp)
        self.assertFalse(v.connect)

    def test_causal_type(self):
        resp = self._make_response(
            "VERDICT: CONNECT\nTYPE: causal\nSTRENGTH: 0.80\nREASONING: A causes B."
        )
        v = ConsolidationJudge._parse_verdict(resp)
        self.assertTrue(v.connect)
        self.assertEqual(v.connection_type, "causal")

    def test_entity_type(self):
        resp = self._make_response(
            "VERDICT: CONNECT\nTYPE: entity\nSTRENGTH: 0.60\nREASONING: Same project mentioned."
        )
        v = ConsolidationJudge._parse_verdict(resp)
        self.assertTrue(v.connect)
        self.assertEqual(v.connection_type, "entity")

    def test_temporal_type(self):
        resp = self._make_response(
            "VERDICT: CONNECT\nTYPE: temporal\nSTRENGTH: 0.45\nREASONING: Events in sequence."
        )
        v = ConsolidationJudge._parse_verdict(resp)
        self.assertTrue(v.connect)
        self.assertEqual(v.connection_type, "temporal")

    def test_strength_below_threshold_rejects(self):
        resp = self._make_response(
            "VERDICT: CONNECT\nTYPE: semantic\nSTRENGTH: 0.20\nREASONING: Weak connection."
        )
        v = ConsolidationJudge._parse_verdict(resp)
        self.assertFalse(v.connect)
        self.assertIn("below threshold", v.reasoning)

    def test_missing_type_defaults_to_semantic(self):
        resp = self._make_response(
            "VERDICT: CONNECT\nSTRENGTH: 0.65\nREASONING: Related topics."
        )
        v = ConsolidationJudge._parse_verdict(resp)
        self.assertTrue(v.connect)
        self.assertEqual(v.connection_type, "semantic")

    def test_invalid_type_ignored(self):
        resp = self._make_response(
            "VERDICT: CONNECT\nTYPE: magical\nSTRENGTH: 0.55\nREASONING: Something."
        )
        v = ConsolidationJudge._parse_verdict(resp)
        # Invalid type → None → defaults to semantic when connect=True
        self.assertEqual(v.connection_type, "semantic")

    def test_strength_clamped(self):
        resp = self._make_response(
            "VERDICT: CONNECT\nTYPE: semantic\nSTRENGTH: 1.5\nREASONING: Very strong."
        )
        v = ConsolidationJudge._parse_verdict(resp)
        self.assertAlmostEqual(v.strength, 1.0)

    def test_extra_whitespace_and_case(self):
        resp = self._make_response(
            "  verdict:   connect  \n  type:  Semantic  \n  strength:  0.70  \n  reasoning:  Some reason.  "
        )
        v = ConsolidationJudge._parse_verdict(resp)
        self.assertTrue(v.connect)
        self.assertEqual(v.connection_type, "semantic")


class TestConsolidatorDB(unittest.TestCase):
    """Test DB operations with a temporary database."""

    def setUp(self):
        self.tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.tmp.close()
        self.db = ConsolidatorDB(self.tmp.name)
        self.db.connect()
        self._create_schema()

    def tearDown(self):
        self.db.close()
        os.unlink(self.tmp.name)

    def _create_schema(self):
        """Create minimal Greeum schema for testing."""
        conn = self.db.conn
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS blocks (
                block_index INTEGER PRIMARY KEY,
                timestamp TEXT NOT NULL,
                context TEXT NOT NULL,
                importance REAL NOT NULL,
                hash TEXT NOT NULL DEFAULT '',
                prev_hash TEXT NOT NULL DEFAULT '',
                slot TEXT
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
        """)
        conn.commit()

    def _insert_block(self, idx, context, importance=0.5, embedding=None):
        conn = self.db.conn
        conn.execute(
            "INSERT INTO blocks (block_index, timestamp, context, importance) VALUES (?, ?, ?, ?)",
            (idx, "2026-01-01T00:00:00", context, importance),
        )
        if embedding is not None:
            arr = np.array(embedding, dtype=np.float32)
            conn.execute(
                "INSERT INTO block_embeddings (block_index, embedding, embedding_model, embedding_dim) VALUES (?, ?, ?, ?)",
                (idx, arr.tobytes(), "test", len(arr)),
            )
        conn.commit()

    def test_get_block_content(self):
        self._insert_block(1, "Hello world")
        result = self.db.get_block_content(1)
        self.assertIsNotNone(result)
        self.assertEqual(result["context"], "Hello world")

    def test_get_block_content_missing(self):
        result = self.db.get_block_content(999)
        self.assertIsNone(result)

    def test_get_all_embeddings(self):
        self._insert_block(1, "A", embedding=[1.0, 0.0, 0.0])
        self._insert_block(2, "B", embedding=[0.0, 1.0, 0.0])
        embeddings = self.db.get_all_embeddings()
        self.assertEqual(len(embeddings), 2)
        self.assertEqual(embeddings[0][0], 1)
        np.testing.assert_array_almost_equal(embeddings[0][1], [1.0, 0.0, 0.0])

    def test_create_node_if_needed(self):
        self._insert_block(1, "Test")
        node_id = self.db.create_node_if_needed(1, "Test")
        self.assertTrue(node_id.startswith("node_"))

        # Second call should return same node
        node_id2 = self.db.create_node_if_needed(1, "Test")
        self.assertEqual(node_id, node_id2)

    def test_create_association(self):
        self._insert_block(1, "A")
        self._insert_block(2, "B")
        n1 = self.db.create_node_if_needed(1, "A")
        n2 = self.db.create_node_if_needed(2, "B")

        assoc_id = self.db.create_association(n1, n2, "semantic", 0.7)
        self.assertTrue(assoc_id.startswith("assoc_"))
        self.assertTrue(self.db.association_exists(n1, n2))
        self.assertTrue(self.db.association_exists(n2, n1))  # either direction

    def test_get_existing_association_pairs(self):
        self._insert_block(1, "A")
        self._insert_block(2, "B")
        n1 = self.db.create_node_if_needed(1, "A")
        n2 = self.db.create_node_if_needed(2, "B")
        self.db.create_association(n1, n2, "semantic", 0.7)

        pairs = self.db.get_existing_association_pairs()
        self.assertIn((1, 2), pairs)


class TestStateManager(unittest.TestCase):
    """Test consolidation_state table management."""

    def setUp(self):
        self.tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.tmp.close()
        self.db = ConsolidatorDB(self.tmp.name)
        self.db.connect()
        self.state = StateManager(self.db)

    def tearDown(self):
        self.db.close()
        os.unlink(self.tmp.name)

    def test_record_and_load(self):
        self.state.record_comparison(ComparisonRecord(
            block_a=1, block_b=2, cosine_similarity=0.5,
            verdict="connected", connection_type="semantic",
            strength=0.7, justification="Test",
            association_id="assoc_test", llm_model="test",
            prompt_tokens=100, completion_tokens=50,
            latency_ms=1000, compared_at="2026-01-01T00:00:00",
        ))

        compared = self.state.load_compared_set()
        self.assertIn((1, 2), compared)

    def test_stats(self):
        for i, verdict in enumerate(["connected", "rejected", "connected", "deferred"]):
            self.state.record_comparison(ComparisonRecord(
                block_a=i, block_b=i + 10, cosine_similarity=0.5,
                verdict=verdict, connection_type="semantic" if verdict == "connected" else None,
                strength=0.7 if verdict == "connected" else None,
                justification="Test", association_id=None, llm_model="test",
                prompt_tokens=100, completion_tokens=50,
                latency_ms=1000, compared_at="2026-01-01T00:00:00",
            ))

        stats = self.state.get_stats()
        self.assertEqual(stats["total"], 4)
        self.assertEqual(stats["connected"], 2)
        self.assertEqual(stats["rejected"], 1)
        self.assertEqual(stats["deferred"], 1)


class TestCandidateSelection(unittest.TestCase):
    """Test candidate pair selection with cosine similarity."""

    def setUp(self):
        self.tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.tmp.close()
        self.db = ConsolidatorDB(self.tmp.name)
        self.db.connect()
        self._create_schema()
        self.state = StateManager(self.db)

    def tearDown(self):
        self.db.close()
        os.unlink(self.tmp.name)

    def _create_schema(self):
        self.db.conn.executescript("""
            CREATE TABLE IF NOT EXISTS blocks (
                block_index INTEGER PRIMARY KEY,
                timestamp TEXT, context TEXT, importance REAL,
                hash TEXT DEFAULT '', prev_hash TEXT DEFAULT '', slot TEXT
            );
            CREATE TABLE IF NOT EXISTS block_embeddings (
                block_index INTEGER PRIMARY KEY,
                embedding BLOB NOT NULL,
                embedding_model TEXT,
                embedding_dim INTEGER
            );
            CREATE TABLE IF NOT EXISTS block_keywords (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                block_index INTEGER, keyword TEXT, UNIQUE(block_index, keyword)
            );
            CREATE TABLE IF NOT EXISTS block_tags (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                block_index INTEGER, tag TEXT, UNIQUE(block_index, tag)
            );
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
        self.db.conn.commit()

    def _insert_embedding(self, idx, emb):
        arr = np.array(emb, dtype=np.float32)
        self.db.conn.execute(
            "INSERT INTO block_embeddings (block_index, embedding, embedding_model, embedding_dim) VALUES (?, ?, ?, ?)",
            (idx, arr.tobytes(), "test", len(arr)),
        )
        self.db.conn.commit()

    def test_selects_similar_pairs(self):
        # Two similar, one different
        self._insert_embedding(1, [1.0, 0.0, 0.0])
        self._insert_embedding(2, [0.9, 0.1, 0.0])
        self._insert_embedding(3, [0.0, 0.0, 1.0])

        candidates = select_candidates(self.db, self.state, min_cosine_similarity=0.3, max_pairs=10)
        # Pair (1,2) should be highly similar, (1,3) and (2,3) should be near 0
        self.assertTrue(len(candidates) >= 1)
        self.assertEqual(candidates[0].block_a, 1)
        self.assertEqual(candidates[0].block_b, 2)
        self.assertGreater(candidates[0].cosine_similarity, 0.9)

    def test_excludes_compared_pairs(self):
        self._insert_embedding(1, [1.0, 0.0])
        self._insert_embedding(2, [0.9, 0.1])

        # Mark as compared
        self.state.record_comparison(ComparisonRecord(
            block_a=1, block_b=2, cosine_similarity=0.99,
            verdict="rejected", connection_type=None,
            strength=None, justification="Test", association_id=None,
            llm_model="test", prompt_tokens=0, completion_tokens=0,
            latency_ms=0, compared_at="2026-01-01",
        ))

        candidates = select_candidates(self.db, self.state, min_cosine_similarity=0.3, max_pairs=10)
        self.assertEqual(len(candidates), 0)

    def test_not_enough_blocks(self):
        self._insert_embedding(1, [1.0, 0.0])
        candidates = select_candidates(self.db, self.state, min_cosine_similarity=0.3, max_pairs=10)
        self.assertEqual(len(candidates), 0)


class TestPromptBuilder(unittest.TestCase):
    """Test the deliberation prompt builder."""

    def test_basic_prompt(self):
        ctx_a = BlockContext(
            block_index=1, content="Python programming tips",
            keywords=["python", "tips"], tags=["dev"], importance=0.8,
            timestamp="2026-01-01T10:00:00",
        )
        ctx_b = BlockContext(
            block_index=2, content="JavaScript best practices",
            keywords=["javascript", "practices"], tags=["dev"], importance=0.7,
            timestamp="2026-01-02T10:00:00",
        )
        prompt = build_deliberation_prompt(ctx_a, ctx_b, 0.65)
        self.assertIn("COSINE SIMILARITY: 0.650", prompt)
        self.assertIn("MEMORY BLOCK A (#1)", prompt)
        self.assertIn("MEMORY BLOCK B (#2)", prompt)
        self.assertIn("Python programming tips", prompt)
        self.assertIn("JavaScript best practices", prompt)
        self.assertIn("render your verdict", prompt)


class TestAssociationWriter(unittest.TestCase):
    """Test association writing."""

    def setUp(self):
        self.tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.tmp.close()
        self.db = ConsolidatorDB(self.tmp.name)
        self.db.connect()
        self.db.conn.executescript("""
            CREATE TABLE IF NOT EXISTS blocks (
                block_index INTEGER PRIMARY KEY,
                timestamp TEXT, context TEXT, importance REAL,
                hash TEXT DEFAULT '', prev_hash TEXT DEFAULT '', slot TEXT
            );
            CREATE TABLE IF NOT EXISTS block_keywords (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                block_index INTEGER, keyword TEXT, UNIQUE(block_index, keyword)
            );
            CREATE TABLE IF NOT EXISTS block_tags (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                block_index INTEGER, tag TEXT, UNIQUE(block_index, tag)
            );
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
        self.db.conn.execute(
            "INSERT INTO blocks VALUES (1, '2026-01-01', 'Block A content', 0.5, '', '', NULL)"
        )
        self.db.conn.execute(
            "INSERT INTO blocks VALUES (2, '2026-01-02', 'Block B content', 0.6, '', '', NULL)"
        )
        self.db.conn.commit()
        self.writer = AssociationWriter(self.db)

    def tearDown(self):
        self.db.close()
        os.unlink(self.tmp.name)

    def test_write_creates_nodes_and_association(self):
        verdict = Verdict(
            connect=True, connection_type="semantic", strength=0.7,
            reasoning="Related topics",
            llm_response=LLMResponse("", 100, 50, 1000, "test"),
        )
        assoc_id = self.writer.write(1, 2, verdict)
        self.assertIsNotNone(assoc_id)
        self.assertTrue(assoc_id.startswith("assoc_"))

        # Verify metadata
        cur = self.db.conn.execute(
            "SELECT metadata FROM associations WHERE association_id = ?", (assoc_id,)
        )
        meta = json.loads(cur.fetchone()["metadata"])
        self.assertEqual(meta["source"], "consolidator")
        self.assertIn("Related topics", meta["reasoning"])

    def test_write_skips_reject(self):
        verdict = Verdict(connect=False, reasoning="Not related")
        assoc_id = self.writer.write(1, 2, verdict)
        self.assertIsNone(assoc_id)

    def test_write_skips_duplicate(self):
        verdict = Verdict(
            connect=True, connection_type="semantic", strength=0.7,
            reasoning="Related",
            llm_response=LLMResponse("", 100, 50, 1000, "test"),
        )
        assoc1 = self.writer.write(1, 2, verdict)
        assoc2 = self.writer.write(1, 2, verdict)
        self.assertIsNotNone(assoc1)
        self.assertIsNone(assoc2)


class TestConfig(unittest.TestCase):
    """Test configuration loading."""

    def test_from_env_defaults(self):
        config = ConsolidatorConfig.from_env()
        self.assertEqual(config.model, "qwen2.5:7b")
        self.assertEqual(config.batch_size, 20)
        self.assertEqual(config.busy_timeout_ms, 30_000)

    def test_from_env_override(self):
        os.environ["GREEUM_CONSOLIDATOR_MODEL"] = "qwen2.5:14b"
        try:
            config = ConsolidatorConfig.from_env()
            self.assertEqual(config.model, "qwen2.5:14b")
        finally:
            del os.environ["GREEUM_CONSOLIDATOR_MODEL"]


class TestConsolidationQueueTable(unittest.TestCase):
    """Test the consolidation_queue table creation via StateManager."""

    def setUp(self):
        self.tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.tmp.close()
        self.db = ConsolidatorDB(self.tmp.name)
        self.db.connect()
        # Create prerequisite tables
        self.db.conn.executescript("""
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
        self.db.conn.commit()

    def tearDown(self):
        self.db.close()
        os.unlink(self.tmp.name)

    def test_state_manager_creates_queue_table(self):
        """StateManager should create consolidation_queue table."""
        state = StateManager(self.db)
        cur = self.db.conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='consolidation_queue'"
        )
        self.assertIsNotNone(cur.fetchone())

    def test_queue_insert_and_read(self):
        """Basic queue insert and read."""
        state = StateManager(self.db)
        self.db._execute_write(
            "INSERT INTO consolidation_queue (block_index, queued_at, status) VALUES (?, ?, 'pending')",
            (100, "2026-02-08T12:00:00"),
        )
        cur = self.db.conn.execute("SELECT block_index, status FROM consolidation_queue WHERE block_index = 100")
        row = cur.fetchone()
        self.assertIsNotNone(row)
        self.assertEqual(row["status"], "pending")

    def test_queue_unique_block_index(self):
        """Duplicate block_index should fail or be ignored."""
        state = StateManager(self.db)
        self.db._execute_write(
            "INSERT INTO consolidation_queue (block_index, queued_at, status) VALUES (?, ?, 'pending')",
            (200, "2026-02-08T12:00:00"),
        )
        # Second insert should raise due to UNIQUE constraint
        with self.assertRaises(Exception):
            self.db._execute_write(
                "INSERT INTO consolidation_queue (block_index, queued_at, status) VALUES (?, ?, 'pending')",
                (200, "2026-02-08T13:00:00"),
            )


if __name__ == "__main__":
    unittest.main()
