"""Branch-based indexing for efficient local search."""

from __future__ import annotations

import logging
import os
import time
from collections import defaultdict
from typing import Dict, List, Optional, Set, Tuple

import numpy as np

try:  # pragma: no cover - optional dependency
    import faiss  # type: ignore
except ImportError:  # pragma: no cover - fallback when FAISS unavailable
    faiss = None

logger = logging.getLogger(__name__)


class BranchIndex:
    """Index for efficient search within a branch."""

    def __init__(self, branch_root: str, use_faiss: bool = True):
        self.branch_root = branch_root
        self.inverted_index = defaultdict(set)  # keyword -> block_indices
        self.blocks = {}  # block_index -> block_data
        self.embeddings = {}  # block_index -> embedding
        self.use_faiss = bool(use_faiss and faiss is not None)
        self._faiss_index = None
        self._faiss_dim = None
        self._faiss_ids: List[int] = []

        ratio_env = os.getenv("GREEUM_BRANCH_VECTOR_MIX", "0.6:0.4")
        try:
            vector_w, keyword_w = [float(part) for part in ratio_env.split(":", maxsplit=1)]
        except ValueError:
            vector_w, keyword_w = 0.6, 0.4

        total = vector_w + keyword_w
        if total <= 0:
            vector_w, keyword_w = 0.6, 0.4
            total = vector_w + keyword_w

        self.vector_weight = vector_w / total
        self.keyword_weight = keyword_w / total

    @property
    def has_vector_index(self) -> bool:
        return self.use_faiss and self._faiss_index is not None

    def add_block(
        self,
        block_index: int,
        block_data: Dict,
        keywords: List[str],
        embedding: Optional[np.ndarray] = None,
    ) -> None:
        """Add a block to the branch index."""
        self.blocks[block_index] = block_data

        # Index keywords
        for keyword in keywords:
            self.inverted_index[keyword.lower()].add(block_index)

        # Store embedding if provided
        if embedding is not None:
            emb = np.asarray(embedding, dtype=np.float32)
            self.embeddings[block_index] = emb
            if self.use_faiss:
                self._add_to_faiss(block_index, emb)

    def search(
        self,
        query: str,
        limit: int = 10,
        query_embedding: Optional[np.ndarray] = None,
    ) -> List[Dict]:
        """Search within this branch."""
        # Extract keywords from query
        keywords = self._extract_keywords(query)

        keyword_scores: Dict[int, float] = defaultdict(float)
        for keyword in keywords:
            lowered = keyword.lower()
            if lowered in self.inverted_index:
                for block_idx in self.inverted_index[lowered]:
                    keyword_scores[block_idx] += 1.0

        normalized_keyword_scores = {
            block_idx: (score / len(keywords) if keywords else 0.0)
            for block_idx, score in keyword_scores.items()
        }

        vector_scores = {}
        if (
            self.use_faiss
            and query_embedding is not None
            and self._faiss_index is not None
            and self._faiss_ids
        ):
            vector_scores = self._vector_search(query_embedding, limit)

        combined_scores: Dict[int, float] = {}

        for block_idx, score in normalized_keyword_scores.items():
            combined_scores[block_idx] = (
                self.keyword_weight * score
                + self.vector_weight * vector_scores.get(block_idx, 0.0)
            )

        for block_idx, score in vector_scores.items():
            if block_idx not in combined_scores:
                combined_scores[block_idx] = (
                    self.vector_weight * score
                    + self.keyword_weight * normalized_keyword_scores.get(block_idx, 0.0)
                )

        sorted_blocks = sorted(
            combined_scores.items(), key=lambda item: item[1], reverse=True
        )

        results: List[Dict] = []
        for block_idx, score in sorted_blocks[:limit]:
            block = self.blocks.get(block_idx)
            if not block:
                continue
            result = block.copy()
            result["_score"] = float(score)
            result["_source"] = "branch_index"
            if block_idx in vector_scores:
                result["_vector_score"] = float(vector_scores[block_idx])
            if block_idx in normalized_keyword_scores:
                result["_keyword_score"] = float(normalized_keyword_scores[block_idx])
            results.append(result)

        return results

    def _extract_keywords(self, text: str) -> List[str]:
        """Simple keyword extraction."""
        import re

        words = re.findall(r"\b[a-zA-Z가-힣]+\b", text.lower())
        return [w for w in words if len(w) > 2]

    def _add_to_faiss(self, block_index: int, embedding: np.ndarray) -> None:
        vector = embedding.astype(np.float32)
        if self._faiss_dim is None:
            self._faiss_dim = int(vector.shape[0])
            self._faiss_index = faiss.IndexFlatIP(self._faiss_dim)

        if vector.shape[0] != self._faiss_dim:
            logger.warning(
                "Skipping FAISS add for block %s due to dimension mismatch (%s != %s)",
                block_index,
                vector.shape[0],
                self._faiss_dim,
            )
            return

        vec = vector.reshape(1, -1)
        faiss.normalize_L2(vec)
        self._faiss_index.add(vec)
        self._faiss_ids.append(block_index)

    def _vector_search(self, query_embedding: np.ndarray, limit: int) -> Dict[int, float]:
        if self._faiss_index is None or not self._faiss_ids:
            return {}

        query_vec = np.asarray(query_embedding, dtype=np.float32).reshape(1, -1)
        if query_vec.shape[1] != self._faiss_dim:
            logger.debug(
                "Query embedding dimension %s does not match index dimension %s",
                query_vec.shape[1],
                self._faiss_dim,
            )
            return {}

        faiss.normalize_L2(query_vec)
        top_k = min(limit, len(self._faiss_ids))
        distances, indices = self._faiss_index.search(query_vec, top_k)

        scores: Dict[int, float] = {}
        for local_idx, distance in zip(indices[0], distances[0]):
            if local_idx < 0 or local_idx >= len(self._faiss_ids):
                continue
            block_idx = self._faiss_ids[local_idx]
            scores[block_idx] = float(distance)

        return scores


class BranchIndexManager:
    """Manages branch indices for all branches."""

    def __init__(self, db_manager):
        self.db_manager = db_manager
        self.branch_indices = {}  # root -> BranchIndex
        self.current_branch = None
        self.use_faiss = self._faiss_enabled()
        self._build_indices()

    def _build_indices(self):
        """Build indices for all branches"""
        start_time = time.time()
        logger.info("Building branch indices...")

        cursor = self.db_manager.conn.cursor()

        # Get all branches
        cursor.execute("""
            SELECT DISTINCT root
            FROM blocks
            WHERE root IS NOT NULL
        """)
        branches = cursor.fetchall()

        for (root,) in branches:
            branch_index = BranchIndex(root, use_faiss=self.use_faiss)

            # Get all blocks in this branch
            cursor.execute("""
                SELECT b.block_index, b.hash, b.context, b.timestamp,
                       b.importance, b.root, b.before, b.after
                FROM blocks b
                WHERE b.root = ?
            """, (root,))

            for row in cursor.fetchall():
                block_data = {
                    'block_index': row[0],
                    'hash': row[1],
                    'context': row[2],
                    'timestamp': row[3],
                    'importance': row[4],
                    'root': row[5],
                    'before': row[6],
                    'after': row[7]
                }

                # Extract keywords from context
                keywords = branch_index._extract_keywords(row[2] or "")

                # Get embedding if exists
                cursor.execute("""
                    SELECT embedding FROM block_embeddings
                    WHERE block_index = ?
                """, (row[0],))
                emb_row = cursor.fetchone()
                embedding = None
                if emb_row and emb_row[0]:
                    embedding = np.frombuffer(emb_row[0], dtype=np.float32)

                branch_index.add_block(row[0], block_data, keywords, embedding)

            self.branch_indices[root] = branch_index

        # Set current branch (most recent)
        cursor.execute("""
            SELECT root FROM blocks
            ORDER BY block_index DESC
            LIMIT 1
        """)
        result = cursor.fetchone()
        if result:
            self.current_branch = result[0]

        elapsed = time.time() - start_time
        mode = "FAISS+keyword" if self.use_faiss else "keyword-only"
        logger.info(
            "Branch indices built in %.2fs (%s, %s branches)",
            elapsed,
            mode,
            len(self.branch_indices),
        )

    def search_current_branch(
        self, query: str, limit: int = 10, query_embedding: Optional[np.ndarray] = None
    ) -> List[Dict]:
        """Search in current branch."""
        if not self.current_branch or self.current_branch not in self.branch_indices:
            return []

        return self.branch_indices[self.current_branch].search(
            query, limit, query_embedding=query_embedding
        )

    def search_branch(
        self,
        branch_root: str,
        query: str,
        limit: int = 10,
        query_embedding: Optional[np.ndarray] = None,
    ) -> List[Dict]:
        """Search in specific branch."""
        if branch_root not in self.branch_indices:
            return []

        return self.branch_indices[branch_root].search(
            query, limit, query_embedding=query_embedding
        )

    def search_all_branches(
        self, query: str, limit: int = 10, query_embedding: Optional[np.ndarray] = None
    ) -> List[Dict]:
        """Search across all branches."""
        all_results = []

        for root, index in self.branch_indices.items():
            results = index.search(query, limit, query_embedding=query_embedding)
            for r in results:
                r['_branch'] = root[:8]
            all_results.extend(results)

        # Sort by score and return top results
        all_results.sort(key=lambda x: x.get('_score', 0), reverse=True)
        return all_results[:limit]

    @staticmethod
    def _faiss_enabled() -> bool:
        if os.getenv("GREEUM_DISABLE_FAISS", "false").lower() in {"1", "true", "yes"}:
            return False
        return faiss is not None

    def get_stats(self) -> Dict[str, int | bool | str]:
        vectorized = sum(1 for index in self.branch_indices.values() if index.has_vector_index)
        faiss_mode = bool(self.use_faiss and vectorized)
        mode = "FAISS+keyword" if faiss_mode else "keyword-only"
        return {
            "branch_count": len(self.branch_indices),
            "vectorized_branches": vectorized,
            "use_faiss": faiss_mode,
            "mode": mode,
        }

    def get_related_branches(self, branch_root: str, limit: int = 3) -> List[str]:
        """Get branches related to given branch (by xref or temporal proximity)"""
        cursor = self.db_manager.conn.cursor()

        # Get min/max block indices for this branch
        cursor.execute("""
            SELECT MIN(block_index), MAX(block_index)
            FROM blocks
            WHERE root = ?
        """, (branch_root,))

        min_idx, max_idx = cursor.fetchone()
        if not min_idx:
            return []

        # Find branches with blocks in similar range
        cursor.execute("""
            SELECT DISTINCT root,
                   MIN(block_index) as min_idx,
                   MAX(block_index) as max_idx
            FROM blocks
            WHERE root != ?
            GROUP BY root
            HAVING (min_idx BETWEEN ? AND ?) OR (max_idx BETWEEN ? AND ?)
            ORDER BY ABS((min_idx + max_idx)/2 - ?)
            LIMIT ?
        """, (branch_root, min_idx-100, max_idx+100, min_idx-100, max_idx+100,
              (min_idx + max_idx)/2, limit))

        return [row[0] for row in cursor.fetchall()]

    def update_branch(self, block_index: int, block_data: Dict,
                     keywords: List[str], embedding: Optional[np.ndarray] = None):
        """Update index when new block is added"""
        root = block_data.get('root')
        if not root:
            return

        # Create branch index if doesn't exist
        if root not in self.branch_indices:
            self.branch_indices[root] = BranchIndex(root)

        # Add to branch index
        self.branch_indices[root].add_block(block_index, block_data, keywords, embedding)

        # Update current branch
        self.current_branch = root
