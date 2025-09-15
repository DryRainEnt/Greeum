"""
Branch-aware memory storage with dynamic threshold
Greeum v3.1.0rc7
"""

import logging
import numpy as np
from typing import Dict, List, Optional, Tuple, Set
from itertools import combinations
import time

logger = logging.getLogger(__name__)


class BranchAwareStorage:
    """Intelligent branch selection for memory storage"""

    def __init__(self, db_manager, branch_index_manager):
        self.db_manager = db_manager
        self.branch_index_manager = branch_index_manager
        self.slot_branches = {}  # slot -> branch_root mapping
        self.branch_centroids = {}  # branch -> centroid embedding
        self.dynamic_threshold = 0.5  # Default, will be calculated

    def update_slot_mapping(self):
        """Update mapping of STM slots to their branches"""
        cursor = self.db_manager.conn.cursor()

        # Get all active STM slots
        cursor.execute("""
            SELECT slot_name, block_hash
            FROM stm_slots
            WHERE block_hash IS NOT NULL
        """)

        self.slot_branches = {}
        for slot_name, block_hash in cursor.fetchall():
            # Get branch for this block
            cursor.execute("""
                SELECT root FROM blocks
                WHERE hash = ?
            """, (block_hash,))

            result = cursor.fetchone()
            if result and result[0]:
                self.slot_branches[slot_name] = result[0]
                logger.debug(f"Slot {slot_name} -> Branch {result[0][:8]}...")

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
            logger.warning("No active slots found, using current branch")
            return self._get_current_branch(), 0.0, "A"

        # Calculate centroids if needed
        if not self.branch_centroids:
            self.calculate_branch_centroids()

        # Update dynamic threshold
        self.calculate_dynamic_threshold()

        if embedding is None:
            # Fallback to keyword-based matching
            return self._keyword_based_selection(content)

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
            return self._get_current_branch(), 0.0, "A"

        # Find best matching branch
        best_branch = max(branch_scores.keys(), key=lambda b: branch_scores[b][0])
        best_score, best_slot = branch_scores[best_branch]

        # Check if similarity meets dynamic threshold
        if best_score >= self.dynamic_threshold:
            logger.info(f"Selected branch {best_branch[:8]}... (slot {best_slot}) "
                       f"with similarity {best_score:.3f} >= {self.dynamic_threshold:.3f}")
            return best_branch, best_score, best_slot
        else:
            logger.info(f"No branch meets threshold {self.dynamic_threshold:.3f}, "
                       f"best was {best_score:.3f}. Using current branch.")
            return self._get_current_branch(), best_score, "A"

    def _keyword_based_selection(self, content: str) -> Tuple[str, float, str]:
        """Fallback to keyword-based branch selection"""
        import re

        # Extract keywords
        words = set(re.findall(r'\b[a-zA-Z가-힣]+\b', content.lower()))

        best_branch = None
        best_score = 0
        best_slot = "A"

        for slot, branch_root in self.slot_branches.items():
            # Get sample content from branch
            cursor = self.db_manager.conn.cursor()
            cursor.execute("""
                SELECT context FROM blocks
                WHERE root = ?
                ORDER BY block_index DESC
                LIMIT 10
            """, (branch_root,))

            branch_words = set()
            for (context,) in cursor.fetchall():
                if context:
                    branch_words.update(re.findall(r'\b[a-zA-Z가-힣]+\b', context.lower()))

            # Calculate overlap
            overlap = len(words & branch_words) / len(words) if words else 0

            if overlap > best_score:
                best_score = overlap
                best_branch = branch_root
                best_slot = slot

        if best_branch and best_score > 0.3:
            return best_branch, best_score, best_slot
        else:
            return self._get_current_branch(), 0.0, "A"

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