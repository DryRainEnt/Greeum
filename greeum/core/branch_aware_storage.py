"""Branch-aware memory storage with LLM-based branch selection.

v4.0.1: Fixed Slot vs Branch confusion
- Branch = Dynamic LTM context unit (unlimited, identified by root hash)
- Slot = Fixed STM cache page (3 slots: A/B/C, caches block coordinates only)
- This module now works with branches directly, not through slot mapping
"""

from __future__ import annotations

import logging
import os
import uuid
from datetime import datetime
from itertools import combinations
from typing import Dict, List, Optional, Tuple

import numpy as np

logger = logging.getLogger(__name__)

# Optional LLM classifier import
_context_classifier = None
_classifier_import_attempted = False


def _get_context_classifier(db_manager=None):
    """Lazy import of context classifier to avoid circular imports."""
    global _context_classifier, _classifier_import_attempted
    if _classifier_import_attempted:
        # If already initialized but db_manager not set, set it now
        if _context_classifier and db_manager and not _context_classifier.db_manager:
            _context_classifier.set_db_manager(db_manager)
        return _context_classifier
    _classifier_import_attempted = True
    try:
        from .context_classifier import get_context_classifier
        _context_classifier = get_context_classifier(db_manager=db_manager)
        logger.info("LLM-based branch classifier available")
    except ImportError as e:
        logger.debug(f"Branch classifier not available: {e}")
    except Exception as e:
        logger.warning(f"Failed to initialize branch classifier: {e}")
    return _context_classifier


class BranchAwareStorage:
    """Intelligent branch selection for memory storage.

    v4.0.1: Fixed Slot vs Branch confusion
    - Now works with branches directly (dynamic LTM context units)
    - Slots (A/B/C) are STM cache only, not used for branch selection
    - LLM decides: existing branch OR create new branch
    """

    def __init__(self, db_manager, branch_index_manager):
        self.db_manager = db_manager
        self.branch_index_manager = branch_index_manager
        self.branch_centroids: Dict[str, np.ndarray] = {}  # branch_root -> centroid embedding
        self.dynamic_threshold = 0.5  # Default, will be calculated

    # ------------------------------------------------------------------
    # Branch Management (v4.0.1 - direct branch access, no slot mapping)
    # ------------------------------------------------------------------

    def get_all_branches(self) -> List[str]:
        """Get all unique branch roots from the database."""
        cursor = self.db_manager.conn.cursor()
        cursor.execute("""
            SELECT DISTINCT root FROM blocks
            WHERE root IS NOT NULL AND root != ''
        """)
        return [row[0] for row in cursor.fetchall()]

    def calculate_branch_centroids(self):
        """Calculate centroid embeddings for each branch."""
        cursor = self.db_manager.conn.cursor()
        branches = self.get_all_branches()

        for branch_root in branches:
            if branch_root in self.branch_centroids:
                continue  # Already calculated

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

    def _try_llm_classification(self, content: str) -> Optional[Tuple[Optional[str], Optional[str], bool]]:
        """
        Try to classify content using LLM-based classifier.

        Returns:
            Tuple of (branch_id, target_block_hash, create_new_branch) if successful, None otherwise
            - branch_id: The branch root hash to attach to, or None for new branch
            - target_block_hash: The suggested block to attach after
            - create_new_branch: True if LLM decided new context divergence
        """
        # Check if LLM classification is enabled via environment
        if os.environ.get("GREEUM_USE_LLM_CLASSIFIER", "true").lower() not in ("true", "1", "yes"):
            return None

        # Pass db_manager to classifier for memory search
        classifier = _get_context_classifier(db_manager=self.db_manager)
        if classifier is None:
            return None

        try:
            result = classifier.classify(content)
            similar_count = len(result.similar_blocks) if result.similar_blocks else 0

            if result.create_new_branch:
                logger.info(
                    f"LLM decided NEW BRANCH for '{content[:30]}...' "
                    f"(confidence: {result.confidence:.2f}, reasoning: {result.reasoning})"
                )
                return None, None, True
            else:
                logger.debug(
                    f"LLM classified '{content[:30]}...' to branch {result.branch_id[:12] if result.branch_id else 'None'}... "
                    f"(confidence: {result.confidence:.2f}, referenced {similar_count} blocks)"
                )
                return result.branch_id, result.target_block_id, False

        except Exception as e:
            logger.warning(f"LLM classification failed: {e}")
            return None

    def find_best_branch_for_memory(
        self,
        content: str,
        embedding: Optional[np.ndarray]
    ) -> Tuple[Optional[str], float, Optional[str], bool]:
        """
        Find the best branch for storing a new memory.

        v4.0.1: Fixed Slot vs Branch confusion
        - Now returns branch directly, no slot involved
        - LLM decides: existing branch OR new branch creation
        - NO FALLBACK - if no match, create new branch

        Priority: LLM classification -> Semantic similarity -> New branch creation

        Returns:
            (branch_root, similarity_score, target_block_hash, create_new_branch)
            - branch_root: The branch to attach to, or None if creating new
            - similarity_score: Confidence score
            - target_block_hash: Suggested block to attach after
            - create_new_branch: True if should create new branch
        """
        # v4.0.1: Try LLM-based classification first
        llm_result = self._try_llm_classification(content)
        if llm_result:
            branch_id, target_block_hash, create_new = llm_result
            if create_new:
                logger.info("LLM decided to create new branch")
                return None, 0.85, None, True
            elif branch_id:
                logger.info(
                    f"LLM classified to branch {branch_id[:12]}... "
                    f"(target_block: {target_block_hash[:8] if target_block_hash else 'None'})"
                )
                return branch_id, 0.95, target_block_hash, False

        # Calculate centroids if needed
        if not self.branch_centroids:
            self.calculate_branch_centroids()

        # If no branches exist, create new one
        if not self.branch_centroids:
            logger.info("No existing branches - will create new branch")
            return None, 1.0, None, True

        # Calculate dynamic threshold
        self.calculate_dynamic_threshold()

        # If no embedding provided, use current branch or create new
        if embedding is None:
            current = self._get_current_branch()
            if current:
                logger.info(f"No embedding - using current branch {current[:12]}...")
                return current, 0.5, None, False
            else:
                return None, 1.0, None, True

        # Calculate similarity to each branch
        branch_scores: Dict[str, float] = {}
        for branch_root, centroid in self.branch_centroids.items():
            try:
                similarity = np.dot(embedding, centroid) / (
                    np.linalg.norm(embedding) * np.linalg.norm(centroid)
                )
                branch_scores[branch_root] = similarity
                logger.debug(f"Branch {branch_root[:12]}...: similarity={similarity:.3f}")
            except Exception as e:
                logger.debug(f"Error computing similarity for branch {branch_root[:8]}: {e}")

        if not branch_scores:
            return None, 1.0, None, True

        # Find best matching branch
        best_branch = max(branch_scores.keys(), key=lambda b: branch_scores[b])
        best_score = branch_scores[best_branch]

        # Check if similarity meets dynamic threshold
        if best_score >= self.dynamic_threshold:
            logger.info(
                f"Selected branch {best_branch[:12]}... "
                f"with similarity {best_score:.3f} >= {self.dynamic_threshold:.3f}"
            )
            return best_branch, best_score, None, False
        else:
            # v4.0.1: NO FALLBACK - create new branch if no good match
            logger.info(
                f"No branch meets threshold {self.dynamic_threshold:.3f} (best {best_score:.3f}). "
                "Creating new branch."
            )
            return None, best_score, None, True

    # ------------------------------------------------------------------
    # NOTE: Fallback logic removed in v4.0.1
    # Previously: _keyword_temporal_fallback, _keyword_score, _temporal_score, etc.
    # These were removed because:
    # 1. Fallback should be explicit failure, not silent degradation
    # 2. If no good branch match, create new branch instead
    # 3. Slots are NOT branches - no slot-based fallback needed
    # ------------------------------------------------------------------

    def _get_current_branch(self) -> Optional[str]:
        """Get the most recently used branch."""
        cursor = self.db_manager.conn.cursor()
        cursor.execute("""
            SELECT root FROM blocks
            WHERE root IS NOT NULL AND root != ''
            ORDER BY block_index DESC
            LIMIT 1
        """)
        result = cursor.fetchone()
        return result[0] if result else None

    def _generate_new_branch_id(self) -> str:
        """Generate a new unique branch ID."""
        return str(uuid.uuid4())

    def store_with_branch_awareness(
        self,
        content: str,
        embedding: Optional[np.ndarray],
        importance: float = 0.5
    ) -> Dict:
        """
        Store memory with intelligent branch selection based on existing memories.

        v4.0.1: Fixed Slot vs Branch confusion
        - Now uses LLM classification to find best branch or create new one
        - Slots are NOT involved in storage - they're STM cache only
        - Returns branch_root and before_hash for block insertion

        Returns:
            Dictionary with storage result including:
            - branch_root: The branch to store in (new UUID if creating new branch)
            - before_hash: The block to attach after
            - similarity: Confidence score
            - create_new_branch: Whether a new branch was created
            - threshold_used: The dynamic threshold used
        """
        # Find best branch
        branch_root, similarity, target_block_hash, create_new_branch = self.find_best_branch_for_memory(
            content, embedding
        )

        before_hash = ""

        if create_new_branch:
            # Generate new branch ID
            branch_root = self._generate_new_branch_id()
            logger.info(f"Creating new branch: {branch_root[:12]}...")
            # New branch has no before_hash
            before_hash = ""
        elif target_block_hash:
            # Use the target block from LLM classification
            before_hash = target_block_hash
            logger.info(
                f"Using target block {target_block_hash[:8]}... from similar block search"
            )
        elif branch_root:
            # Get the tip of selected branch
            cursor = self.db_manager.conn.cursor()
            cursor.execute("""
                SELECT hash FROM blocks
                WHERE root = ?
                ORDER BY block_index DESC
                LIMIT 1
            """, (branch_root,))

            result = cursor.fetchone()
            if result:
                before_hash = result[0]

        logger.info(
            f"Storing to branch {branch_root[:12] if branch_root else 'new'}... "
            f"with similarity {similarity:.3f}, before={before_hash[:8] if before_hash else 'None'}"
        )

        return {
            "branch_root": branch_root,
            "before_hash": before_hash,
            "similarity": similarity,
            "create_new_branch": create_new_branch,
            "threshold_used": self.dynamic_threshold,
            "target_from_search": target_block_hash is not None
        }
