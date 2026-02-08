"""Standalone DB access layer for the consolidator process.

Does NOT import Greeum's DatabaseManager / ThreadSafeDatabaseManager.
Uses its own sqlite3 connection with WAL mode and 30s busy_timeout.
"""

from __future__ import annotations

import json
import logging
import sqlite3
import time
from contextlib import contextmanager
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

logger = logging.getLogger(__name__)

_MAX_RETRIES = 5
_BACKOFF_BASE = 0.5  # seconds


class ConsolidatorDB:
    """Separate-process-safe SQLite access for the consolidator."""

    def __init__(self, db_path: str, busy_timeout_ms: int = 30_000) -> None:
        self.db_path = db_path
        self.busy_timeout_ms = busy_timeout_ms
        self._conn: Optional[sqlite3.Connection] = None

    # ------------------------------------------------------------------
    # Connection management
    # ------------------------------------------------------------------

    def connect(self) -> None:
        """Open connection with WAL mode and busy_timeout."""
        self._conn = sqlite3.connect(self.db_path, timeout=self.busy_timeout_ms / 1000)
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.execute("PRAGMA synchronous=NORMAL")
        self._conn.execute("PRAGMA temp_store=MEMORY")
        self._conn.execute(f"PRAGMA busy_timeout = {self.busy_timeout_ms}")
        logger.info("ConsolidatorDB connected: %s (busy_timeout=%dms)", self.db_path, self.busy_timeout_ms)

    def close(self) -> None:
        if self._conn:
            self._conn.close()
            self._conn = None

    @property
    def conn(self) -> sqlite3.Connection:
        if self._conn is None:
            self.connect()
        return self._conn

    # ------------------------------------------------------------------
    # Write helper with exponential backoff
    # ------------------------------------------------------------------

    @contextmanager
    def _write_tx(self):
        """BEGIN IMMEDIATE transaction with exponential backoff on lock."""
        for attempt in range(_MAX_RETRIES):
            try:
                self.conn.execute("BEGIN IMMEDIATE")
                yield self.conn
                self.conn.commit()
                return
            except sqlite3.OperationalError as exc:
                self.conn.rollback()
                if "locked" in str(exc).lower() and attempt < _MAX_RETRIES - 1:
                    wait = _BACKOFF_BASE * (2 ** attempt)
                    logger.warning("DB locked (attempt %d/%d), retrying in %.1fs", attempt + 1, _MAX_RETRIES, wait)
                    time.sleep(wait)
                else:
                    raise

    def _execute_write(self, sql: str, params: tuple = ()) -> Optional[int]:
        """Execute a single write statement with retry."""
        with self._write_tx() as conn:
            cur = conn.execute(sql, params)
            return cur.lastrowid

    # ------------------------------------------------------------------
    # Read methods
    # ------------------------------------------------------------------

    def get_all_embeddings(self) -> List[Tuple[int, np.ndarray]]:
        """Load all block embeddings as (block_index, ndarray) pairs."""
        cur = self.conn.execute("SELECT block_index, embedding FROM block_embeddings ORDER BY block_index")
        results = []
        for row in cur.fetchall():
            arr = np.frombuffer(row["embedding"], dtype=np.float32).copy()
            results.append((row["block_index"], arr))
        return results

    def get_block_content(self, block_index: int) -> Optional[Dict[str, Any]]:
        """Retrieve block content, keywords, tags, and metadata."""
        cur = self.conn.execute(
            "SELECT block_index, timestamp, context, importance, slot FROM blocks WHERE block_index = ?",
            (block_index,),
        )
        row = cur.fetchone()
        if not row:
            return None

        kw_cur = self.conn.execute("SELECT keyword FROM block_keywords WHERE block_index = ?", (block_index,))
        keywords = [r["keyword"] for r in kw_cur.fetchall()]

        tag_cur = self.conn.execute("SELECT tag FROM block_tags WHERE block_index = ?", (block_index,))
        tags = [r["tag"] for r in tag_cur.fetchall()]

        return {
            "block_index": row["block_index"],
            "timestamp": row["timestamp"],
            "context": row["context"],
            "importance": row["importance"],
            "slot": row["slot"],
            "keywords": keywords,
            "tags": tags,
        }

    def get_node_id_for_block(self, block_index: int) -> Optional[str]:
        """Get memory_nodes.node_id for a given memory_id (block_index)."""
        cur = self.conn.execute(
            "SELECT node_id FROM memory_nodes WHERE memory_id = ? LIMIT 1",
            (block_index,),
        )
        row = cur.fetchone()
        return row["node_id"] if row else None

    def get_node_associations_with_content(
        self, node_id: str, limit: int = 5
    ) -> List[Dict[str, Any]]:
        """Get associations for a node, including neighbor content summaries."""
        cur = self.conn.execute(
            """
            SELECT a.association_type, a.strength,
                   CASE WHEN a.source_node_id = ? THEN a.target_node_id ELSE a.source_node_id END AS neighbor_id
            FROM associations a
            WHERE a.source_node_id = ? OR a.target_node_id = ?
            ORDER BY a.strength DESC
            LIMIT ?
            """,
            (node_id, node_id, node_id, limit),
        )
        results = []
        for row in cur.fetchall():
            neighbor = self.conn.execute(
                "SELECT content, memory_id FROM memory_nodes WHERE node_id = ?",
                (row["neighbor_id"],),
            ).fetchone()
            content_summary = ""
            neighbor_block = None
            if neighbor:
                content_summary = (neighbor["content"] or "")[:80]
                neighbor_block = neighbor["memory_id"]
            results.append({
                "association_type": row["association_type"],
                "strength": row["strength"],
                "neighbor_node_id": row["neighbor_id"],
                "neighbor_block": neighbor_block,
                "content_summary": content_summary,
            })
        return results

    def get_existing_association_pairs(self) -> set:
        """Get set of (min_block, max_block) pairs that already have associations."""
        cur = self.conn.execute(
            """
            SELECT n1.memory_id AS id1, n2.memory_id AS id2
            FROM associations a
            JOIN memory_nodes n1 ON a.source_node_id = n1.node_id
            JOIN memory_nodes n2 ON a.target_node_id = n2.node_id
            WHERE n1.memory_id IS NOT NULL AND n2.memory_id IS NOT NULL
            """
        )
        pairs = set()
        for row in cur.fetchall():
            a, b = row["id1"], row["id2"]
            pairs.add((min(a, b), max(a, b)))
        return pairs

    # ------------------------------------------------------------------
    # Write methods
    # ------------------------------------------------------------------

    def create_node_if_needed(self, block_index: int, content: str) -> str:
        """Ensure a memory_node exists for block_index, return node_id."""
        existing = self.get_node_id_for_block(block_index)
        if existing:
            return existing

        import uuid
        node_id = f"node_{uuid.uuid4().hex[:12]}"
        now = __import__("datetime").datetime.now().isoformat()

        self._execute_write(
            """
            INSERT INTO memory_nodes
            (node_id, memory_id, node_type, content, embedding,
             activation_level, last_activated, metadata, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (node_id, block_index, "memory", content, None, 0.0, None, json.dumps({}), now),
        )
        logger.debug("Created node %s for block #%d", node_id, block_index)
        return node_id

    def create_association(
        self,
        source_node_id: str,
        target_node_id: str,
        association_type: str,
        strength: float,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Insert a new association, return association_id."""
        import uuid
        association_id = f"assoc_{uuid.uuid4().hex[:12]}"
        now = __import__("datetime").datetime.now().isoformat()

        self._execute_write(
            """
            INSERT INTO associations
            (association_id, source_node_id, target_node_id, association_type,
             strength, weight, created_at, last_activated, activation_count, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                association_id,
                source_node_id,
                target_node_id,
                association_type,
                strength,
                1.0,
                now,
                None,
                0,
                json.dumps(metadata or {}),
            ),
        )
        logger.debug("Created association %s: %s -> %s (%s, %.2f)",
                      association_id, source_node_id, target_node_id, association_type, strength)
        return association_id

    def association_exists(self, node_a: str, node_b: str) -> bool:
        """Check if an association already exists between two nodes (either direction)."""
        cur = self.conn.execute(
            """
            SELECT 1 FROM associations
            WHERE (source_node_id = ? AND target_node_id = ?)
               OR (source_node_id = ? AND target_node_id = ?)
            LIMIT 1
            """,
            (node_a, node_b, node_b, node_a),
        )
        return cur.fetchone() is not None
