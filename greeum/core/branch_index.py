"""
Branch-based indexing for efficient local search
Greeum v3.1.0rc6
"""

import logging
import time
from typing import Dict, List, Set, Optional, Tuple
from collections import defaultdict
import numpy as np

logger = logging.getLogger(__name__)


class BranchIndex:
    """Index for efficient search within a branch"""

    def __init__(self, branch_root: str):
        self.branch_root = branch_root
        self.inverted_index = defaultdict(set)  # keyword -> block_indices
        self.blocks = {}  # block_index -> block_data
        self.embeddings = {}  # block_index -> embedding

    def add_block(self, block_index: int, block_data: Dict,
                  keywords: List[str], embedding: Optional[np.ndarray] = None):
        """Add a block to the branch index"""
        self.blocks[block_index] = block_data

        # Index keywords
        for keyword in keywords:
            self.inverted_index[keyword.lower()].add(block_index)

        # Store embedding if provided
        if embedding is not None:
            self.embeddings[block_index] = embedding

    def search(self, query: str, limit: int = 10) -> List[Dict]:
        """Search within this branch"""
        # Extract keywords from query
        keywords = self._extract_keywords(query)

        # Score blocks by keyword match
        scores = defaultdict(float)
        for keyword in keywords:
            if keyword.lower() in self.inverted_index:
                for block_idx in self.inverted_index[keyword.lower()]:
                    scores[block_idx] += 1.0

        # Sort by score
        sorted_blocks = sorted(scores.items(), key=lambda x: x[1], reverse=True)

        # Return top results with block data
        results = []
        for block_idx, score in sorted_blocks[:limit]:
            block = self.blocks[block_idx].copy()
            block['_score'] = score / len(keywords) if keywords else 0
            block['_source'] = 'branch_index'
            results.append(block)

        return results

    def _extract_keywords(self, text: str) -> List[str]:
        """Simple keyword extraction"""
        import re
        words = re.findall(r'\b[a-zA-Z가-힣]+\b', text.lower())
        return [w for w in words if len(w) > 2]


class BranchIndexManager:
    """Manages branch indices for all branches"""

    def __init__(self, db_manager):
        self.db_manager = db_manager
        self.branch_indices = {}  # root -> BranchIndex
        self.current_branch = None
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
            branch_index = BranchIndex(root)

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
        logger.info(f"Branch indices built in {elapsed:.2f}s: "
                   f"{len(self.branch_indices)} branches")

    def search_current_branch(self, query: str, limit: int = 10) -> List[Dict]:
        """Search in current branch"""
        if not self.current_branch or self.current_branch not in self.branch_indices:
            return []

        return self.branch_indices[self.current_branch].search(query, limit)

    def search_branch(self, branch_root: str, query: str, limit: int = 10) -> List[Dict]:
        """Search in specific branch"""
        if branch_root not in self.branch_indices:
            return []

        return self.branch_indices[branch_root].search(query, limit)

    def search_all_branches(self, query: str, limit: int = 10) -> List[Dict]:
        """Search across all branches"""
        all_results = []

        for root, index in self.branch_indices.items():
            results = index.search(query, limit)
            for r in results:
                r['_branch'] = root[:8]
            all_results.extend(results)

        # Sort by score and return top results
        all_results.sort(key=lambda x: x.get('_score', 0), reverse=True)
        return all_results[:limit]

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