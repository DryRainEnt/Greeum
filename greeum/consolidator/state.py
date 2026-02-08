"""Consolidation state table management.

Tracks which block pairs have been compared and their verdicts.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional, Set, Tuple

from .db import ConsolidatorDB

logger = logging.getLogger(__name__)


@dataclass
class ComparisonRecord:
    """A single comparison record from consolidation_state."""
    block_a: int
    block_b: int
    cosine_similarity: Optional[float]
    verdict: str
    connection_type: Optional[str]
    strength: Optional[float]
    justification: Optional[str]
    association_id: Optional[str]
    llm_model: Optional[str]
    prompt_tokens: Optional[int]
    completion_tokens: Optional[int]
    latency_ms: Optional[int]
    compared_at: str


class StateManager:
    """Manages the consolidation_state table."""

    def __init__(self, db: ConsolidatorDB) -> None:
        self.db = db
        self._ensure_table()

    def _ensure_table(self) -> None:
        """Create consolidation_state and consolidation_queue tables if they don't exist."""
        self.db._execute_write(
            """
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
            )
            """
        )
        self.db._execute_write(
            """
            CREATE TABLE IF NOT EXISTS consolidation_queue (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                block_index INTEGER NOT NULL UNIQUE,
                queued_at TEXT NOT NULL,
                status TEXT DEFAULT 'pending'
            )
            """
        )

    def load_compared_set(self) -> Set[Tuple[int, int]]:
        """Bulk load all compared pairs as (min, max) tuples."""
        cur = self.db.conn.execute("SELECT block_a, block_b FROM consolidation_state")
        return {(row["block_a"], row["block_b"]) for row in cur.fetchall()}

    def record_comparison(self, record: ComparisonRecord) -> None:
        """Insert or replace a comparison result."""
        pair = (min(record.block_a, record.block_b), max(record.block_a, record.block_b))
        self.db._execute_write(
            """
            INSERT OR REPLACE INTO consolidation_state
            (block_a, block_b, cosine_similarity, verdict, connection_type,
             strength, justification, association_id, llm_model,
             prompt_tokens, completion_tokens, latency_ms, compared_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                pair[0], pair[1],
                record.cosine_similarity,
                record.verdict,
                record.connection_type,
                record.strength,
                record.justification,
                record.association_id,
                record.llm_model,
                record.prompt_tokens,
                record.completion_tokens,
                record.latency_ms,
                record.compared_at,
            ),
        )

    def get_stats(self) -> Dict[str, int]:
        """Get verdict counts."""
        cur = self.db.conn.execute(
            "SELECT verdict, COUNT(*) as cnt FROM consolidation_state GROUP BY verdict"
        )
        stats: Dict[str, int] = {"total": 0, "connected": 0, "rejected": 0, "deferred": 0, "error": 0}
        for row in cur.fetchall():
            stats[row["verdict"]] = row["cnt"]
            stats["total"] += row["cnt"]
        return stats

    def get_type_distribution(self) -> Dict[str, int]:
        """Get connection type distribution for connected pairs."""
        cur = self.db.conn.execute(
            """
            SELECT connection_type, COUNT(*) as cnt
            FROM consolidation_state
            WHERE verdict = 'connected' AND connection_type IS NOT NULL
            GROUP BY connection_type
            """
        )
        return {row["connection_type"]: row["cnt"] for row in cur.fetchall()}

    def get_deferred_pairs(self) -> List[Tuple[int, int]]:
        """Get pairs marked as deferred for retry."""
        cur = self.db.conn.execute(
            "SELECT block_a, block_b FROM consolidation_state WHERE verdict = 'deferred'"
        )
        return [(row["block_a"], row["block_b"]) for row in cur.fetchall()]

    def get_average_latency(self) -> Optional[float]:
        """Get average LLM latency in ms."""
        cur = self.db.conn.execute(
            "SELECT AVG(latency_ms) as avg_ms FROM consolidation_state WHERE latency_ms IS NOT NULL"
        )
        row = cur.fetchone()
        return row["avg_ms"] if row else None
