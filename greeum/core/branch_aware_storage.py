"""Branch-aware memory storage with semantic + fallback heuristics."""

from __future__ import annotations

import logging
import math
import os
import re
import time
from datetime import datetime
from itertools import combinations
from typing import Dict, List, Optional, Tuple

import numpy as np

from .stm_anchor_store import get_anchor_store

logger = logging.getLogger(__name__)


class BranchAwareStorage:
    """Intelligent branch selection for memory storage."""

    def __init__(self, db_manager, branch_index_manager):
        self.db_manager = db_manager
        self.branch_index_manager = branch_index_manager
        self.slot_branches = {}  # slot -> branch_root mapping
        self.branch_centroids = {}  # branch -> centroid embedding
        self.dynamic_threshold = 0.5  # Default, will be calculated
        self.keyword_weight, self.temporal_weight = self._load_fallback_weights()
        self.anchor_store = get_anchor_store()

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _load_fallback_weights(self) -> Tuple[float, float]:
        ratio = os.getenv("GREEUM_BRANCH_FALLBACK_RATIO", "0.5:0.5")
        try:
            keyword_str, temporal_str = ratio.split(":", maxsplit=1)
            keyword_weight = float(keyword_str)
            temporal_weight = float(temporal_str)
        except ValueError:
            keyword_weight = 0.5
            temporal_weight = 0.5

        total = keyword_weight + temporal_weight
        if total <= 0:
            return 0.5, 0.5
        return keyword_weight / total, temporal_weight / total

    def update_slot_mapping(self):
        """Update mapping of STM slots to their branches"""
        cursor = self.db_manager.conn.cursor()
        self.slot_branches = {}
        slots = self.anchor_store.get_slots()
        for slot_name, slot_data in slots.items():
            if not slot_data.anchor_block:
                continue
            cursor.execute(
                "SELECT root FROM blocks WHERE hash = ?",
                (slot_data.anchor_block,),
            )
            result = cursor.fetchone()
            root_hash = result[0] if result and result[0] else slot_data.anchor_block
            self.slot_branches[slot_name] = root_hash
            logger.debug(f"Slot {slot_name} -> Branch {root_hash[:8]}...")

    def calculate_branch_centroids(self):
        """Calculate centroid embeddings for each branch"""
        cursor = self.db_manager.conn.cursor()

        for branch_root in set(self.slot_branches.values()):
            # Get all embeddings in this branch
            cursor.execute("""
                SELECT be.embedding
                FROM block_embeddings be
                JOIN blocks b ON be.block_index = b.block_index
                WHERE b.root = ?
                AND be.embedding IS NOT NULL
                LIMIT 100
            """, (branch_root,))

            embeddings = []
            for (embedding_blob,) in cursor.fetchall():
                if embedding_blob:
                    try:
                        emb = np.frombuffer(embedding_blob, dtype=np.float32)
                        embeddings.append(emb)
                    except:
                        continue

            if embeddings:
                # Calculate centroid
                centroid = np.mean(embeddings, axis=0)
                self.branch_centroids[branch_root] = centroid
                logger.debug(f"Calculated centroid for branch {branch_root[:8]}... "
                           f"({len(embeddings)} embeddings)")

    def calculate_dynamic_threshold(self):
        """Calculate dynamic threshold based on max semantic distance between branches"""
        if len(self.branch_centroids) < 2:
            return 0.5  # Default if not enough branches

        max_distance = 0
        min_distance = float('inf')

        # Calculate pairwise distances between branch centroids
        for branch1, branch2 in combinations(self.branch_centroids.keys(), 2):
            centroid1 = self.branch_centroids[branch1]
            centroid2 = self.branch_centroids[branch2]

            # Cosine distance
            similarity = np.dot(centroid1, centroid2) / (
                np.linalg.norm(centroid1) * np.linalg.norm(centroid2)
            )
            distance = 1 - similarity

            max_distance = max(max_distance, distance)
            min_distance = min(min_distance, distance)

        # Dynamic threshold: 60% of max distance
        # If branches are very different (max_distance high), be more strict
        # If branches are similar (max_distance low), be more lenient
        self.dynamic_threshold = 0.3 + (max_distance * 0.4)

        logger.info(f"Dynamic threshold calculated: {self.dynamic_threshold:.3f} "
                   f"(max_dist={max_distance:.3f}, min_dist={min_distance:.3f})")

        return self.dynamic_threshold

    def find_best_branch_for_memory(self,
                                   content: str,
                                   embedding: Optional[np.ndarray]) -> Tuple[str, float, str]:
        """
        Find the best branch for storing a new memory

        Returns:
            (branch_root, similarity_score, selected_slot)
        """
        # Update mappings
        self.update_slot_mapping()

        if not self.slot_branches:
            logger.debug("No active slots found during branch selection; using current branch")
            return self._get_current_branch(), 0.0, "A"

        # Calculate centroids if needed
        if not self.branch_centroids:
            self.calculate_branch_centroids()

        # Update dynamic threshold
        self.calculate_dynamic_threshold()

        if embedding is None:
            return self._keyword_temporal_fallback(content)

        # Calculate similarity to each branch
        branch_scores = {}
        for slot, branch_root in self.slot_branches.items():
            if branch_root in self.branch_centroids:
                centroid = self.branch_centroids[branch_root]
                similarity = np.dot(embedding, centroid) / (
                    np.linalg.norm(embedding) * np.linalg.norm(centroid)
                )
                branch_scores[branch_root] = (similarity, slot)
                logger.debug(f"Branch {branch_root[:8]}... (slot {slot}): "
                           f"similarity={similarity:.3f}")

        if not branch_scores:
            return self._keyword_temporal_fallback(content)

        # Find best matching branch
        best_branch = max(branch_scores.keys(), key=lambda b: branch_scores[b][0])
        best_score, best_slot = branch_scores[best_branch]

        # Check if similarity meets dynamic threshold
        if best_score >= self.dynamic_threshold:
            logger.info(f"Selected branch {best_branch[:8]}... (slot {best_slot}) "
                       f"with similarity {best_score:.3f} >= {self.dynamic_threshold:.3f}")
            return best_branch, best_score, best_slot
        else:
            logger.info(
                "No branch meets threshold %.3f (best %.3f). Using keyword/temporal fallback.",
                self.dynamic_threshold,
                best_score,
            )
            return self._keyword_temporal_fallback(content, default_slot=best_slot)

    # ------------------------------------------------------------------
    # Fallback logic
    # ------------------------------------------------------------------
    def _keyword_temporal_fallback(self, content: str, default_slot: str = "A") -> Tuple[str, float, str]:
        """Fallback using simple keyword overlap + temporal recency scores."""

        if not self.slot_branches:
            logger.warning("Fallback invoked without slot mapping; using current branch")
            return self._get_current_branch(), 0.0, default_slot

        keywords = self._extract_keywords(content)
        cursor = self.db_manager.conn.cursor()
        now_ts = time.time()

        best_candidate = None
        for slot, branch_root in self.slot_branches.items():
            branch_keywords = set()
            latest_ts = None

            cursor.execute(
                """
                SELECT context, timestamp
                FROM blocks
                WHERE root = ?
                ORDER BY block_index DESC
                LIMIT 12
                """,
                (branch_root,),
            )

            for context, timestamp in cursor.fetchall():
                if context:
                    branch_keywords.update(self._extract_keywords(context))
                parsed_ts = self._parse_timestamp(timestamp)
                if parsed_ts is not None:
                    latest_ts = parsed_ts if latest_ts is None else max(latest_ts, parsed_ts)

            keyword_score = self._keyword_score(keywords, branch_keywords)
            temporal_score = self._temporal_score(latest_ts, now_ts)
            combined = (self.keyword_weight * keyword_score) + (
                self.temporal_weight * temporal_score
            )

            logger.debug(
                "Fallback candidate branch %s slot %s -> keyword=%.3f temporal=%.3f combined=%.3f",
                branch_root[:8] if branch_root else "<rootless>",
                slot,
                keyword_score,
                temporal_score,
                combined,
            )

            candidate = (combined, keyword_score, temporal_score, branch_root, slot)
            if best_candidate is None or candidate > best_candidate:
                best_candidate = candidate

        if not best_candidate:
            return self._get_current_branch(), 0.0, default_slot

        combined, keyword_score, temporal_score, branch_root, slot = best_candidate
        logger.info(
            "Fallback selected branch %s (slot %s) with combined=%.3f (keyword=%.3f, temporal=%.3f)",
            branch_root[:8] if branch_root else "<rootless>",
            slot,
            combined,
            keyword_score,
            temporal_score,
        )
        return branch_root, combined, slot or default_slot

    @staticmethod
    def _keyword_score(query_words: set, branch_words: set) -> float:
        if not query_words:
            return 0.0
        overlap = len(query_words & branch_words)
        return overlap / len(query_words)

    @staticmethod
    def _temporal_score(latest_ts: Optional[float], now_ts: float) -> float:
        if latest_ts is None:
            return 0.0
        age = max(now_ts - latest_ts, 0.0)
        raw_half_life = os.getenv("GREEUM_BRANCH_TEMPORAL_HALFLIFE", 60 * 60 * 24 * 3)
        try:
            half_life = float(raw_half_life)
        except (TypeError, ValueError):
            half_life = 60 * 60 * 24 * 3

        if half_life <= 0:
            half_life = 60 * 60 * 24 * 3
        return math.exp(-age / half_life)

    @staticmethod
    def _parse_timestamp(value: Optional[str]) -> Optional[float]:
        if value is None:
            return None
        if isinstance(value, (int, float)):
            return float(value)

        value = value.strip()
        if not value:
            return None

        try:
            return float(value)
        except ValueError:
            pass

        cleaned = value.replace("Z", "")
        try:
            return datetime.fromisoformat(cleaned).timestamp()
        except ValueError:
            for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d", "%Y/%m/%d %H:%M:%S"):
                try:
                    return datetime.strptime(cleaned, fmt).timestamp()
                except ValueError:
                    continue
        return None

    @staticmethod
    def _extract_keywords(text: str) -> set:
        if not text:
            return set()
        return {match for match in re.findall(r"\b[a-zA-Z가-힣]+\b", text.lower()) if len(match) > 2}

    def _get_current_branch(self) -> str:
        """Get the current active branch"""
        cursor = self.db_manager.conn.cursor()
        cursor.execute("""
            SELECT root FROM blocks
            ORDER BY block_index DESC
            LIMIT 1
        """)

        result = cursor.fetchone()
        return result[0] if result and result[0] else ""

    def store_with_branch_awareness(self,
                                   content: str,
                                   embedding: Optional[np.ndarray],
                                   importance: float = 0.5) -> Dict:
        """
        Store memory with intelligent branch selection

        Returns:
            Dictionary with storage result including selected branch
        """
        # Find best branch
        branch_root, similarity, slot = self.find_best_branch_for_memory(content, embedding)

        # Get the tip of selected branch for 'before' link
        cursor = self.db_manager.conn.cursor()
        cursor.execute("""
            SELECT hash FROM blocks
            WHERE root = ?
            ORDER BY block_index DESC
            LIMIT 1
        """, (branch_root,))

        before_hash = ""
        result = cursor.fetchone()
        if result:
            before_hash = result[0]

        logger.info(f"Storing to branch {branch_root[:8]}... (slot {slot}) "
                   f"with similarity {similarity:.3f}")

        return {
            "branch_root": branch_root,
            "before_hash": before_hash,
            "similarity": similarity,
            "selected_slot": slot,
            "threshold_used": self.dynamic_threshold
        }
