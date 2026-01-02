"""
Hybrid Graph Search for Greeum v5.0
Combines Vector similarity and BM25 for graph-based memory search

Features:
- Anchor-based DFS traversal
- Hybrid scoring (Vector + BM25)
- Adaptive pruning based on similarity
- Project/branch-aware search
- Depth control for exploration

Design principles (from 사업화문서.txt):
- "앵커에서 시작하여 그래프를 탐색"
- "탐색 심도를 인자로 전달"
- "유사도 기반 가지치기"
- "before/after 연결 구조 활용"
"""

import json
import logging
import time
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Tuple, Set
import numpy as np

from .bm25_index import BM25Index, HybridScorer

logger = logging.getLogger(__name__)


@dataclass
class SearchResult:
    """Search result with scoring details"""
    block_index: int
    block_hash: str
    content: str
    keywords: List[str]
    timestamp: str
    importance: float
    hybrid_score: float
    vector_score: float
    bm25_score: float
    depth: int
    project: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "block_index": self.block_index,
            "hash": self.block_hash,
            "context": self.content,
            "keywords": self.keywords,
            "timestamp": self.timestamp,
            "importance": self.importance,
            "_score": self.hybrid_score,
            "_vector_score": self.vector_score,
            "_bm25_score": self.bm25_score,
            "_depth": self.depth,
            "project": self.project
        }


@dataclass
class SearchMetadata:
    """Metadata about the search process"""
    search_type: str = "hybrid_graph"
    anchor_hash: Optional[str] = None
    project: Optional[str] = None
    depth_used: int = 0
    nodes_visited: int = 0
    nodes_pruned: int = 0
    elapsed_ms: float = 0.0
    result_count: int = 0


class HybridGraphSearch:
    """
    Graph-based search engine using Hybrid similarity (Vector + BM25).

    Implements the design from GREEUM_V5_VIBE_CODING_DESIGN.md:
    - Anchor-based DFS traversal
    - Hybrid scoring for each visited node
    - Pruning based on explore_threshold
    - Depth limit for controlled exploration
    """

    def __init__(self, db_manager, bm25_index: Optional[BM25Index] = None):
        """
        Initialize HybridGraphSearch.

        Args:
            db_manager: Database manager instance
            bm25_index: Optional BM25Index (will create/load if not provided)
        """
        self.db_manager = db_manager

        # Initialize or load BM25 index
        if bm25_index:
            self.bm25_index = bm25_index
        else:
            self.bm25_index = BM25Index()
            if not self.bm25_index.load_from_db(db_manager):
                # Build from existing blocks
                count = self.bm25_index.build_from_blocks(db_manager)
                if count > 0:
                    self.bm25_index.save_to_db(db_manager)
                logger.info(f"Built BM25 index with {count} documents")

        # Hybrid scorer
        self.hybrid_scorer = HybridScorer(
            self.bm25_index,
            vector_weight=0.5,
            bm25_weight=0.5
        )

        # Metrics
        self.metrics = {
            "total_searches": 0,
            "avg_nodes_visited": 0.0,
            "avg_depth": 0.0,
            "avg_results": 0.0,
            "pruning_rate": 0.0
        }

    def search(
        self,
        query: str,
        query_embedding: Optional[np.ndarray] = None,
        anchor_hash: Optional[str] = None,
        project: Optional[str] = None,
        depth: int = 6,
        min_depth: int = 3,
        threshold: float = 0.3,
        explore_threshold: float = 0.15,
        limit: int = 10
    ) -> Tuple[List[SearchResult], SearchMetadata]:
        """
        Perform hybrid graph search from anchor.

        Args:
            query: Search query text
            query_embedding: Query embedding vector (if None, uses text matching only)
            anchor_hash: Starting anchor block hash (if None, uses most recent)
            project: Project/branch to search in (if None, searches all)
            depth: Maximum search depth
            min_depth: Minimum depth to explore before pruning (default: 3)
            threshold: Minimum hybrid score for result inclusion
            explore_threshold: Minimum score to continue exploring a path
            limit: Maximum number of results

        Returns:
            Tuple of (results, metadata)
        """
        start_time = time.time()
        self.metrics["total_searches"] += 1

        # Tokenize query for BM25
        query_keywords = self._tokenize_query(query)

        # Get anchor block
        anchor = self._get_anchor_block(anchor_hash, project)
        if not anchor:
            logger.warning("No anchor block found, falling back to most recent block")
            anchor = self._get_most_recent_block(project)

        if not anchor:
            logger.error("No blocks available for search")
            return [], SearchMetadata(result_count=0)

        # Initialize search state
        visited: Set[str] = set()
        candidates: List[SearchResult] = []
        nodes_pruned = 0
        max_depth_used = 0

        def dfs(block: Dict, current_depth: int, is_anchor: bool = False) -> None:
            nonlocal nodes_pruned, max_depth_used

            if current_depth > depth:
                return

            block_hash = block.get("hash")
            if not block_hash or block_hash in visited:
                return

            visited.add(block_hash)
            max_depth_used = max(max_depth_used, current_depth)

            # Calculate hybrid score
            hybrid_score, vector_score, bm25_score = self._compute_hybrid_score(
                query, query_keywords, query_embedding, block
            )

            # Add to candidates if above threshold
            if hybrid_score > threshold:
                result = SearchResult(
                    block_index=block.get("block_index", 0),
                    block_hash=block_hash,
                    content=block.get("context", ""),
                    keywords=self._get_keywords(block),
                    timestamp=block.get("timestamp", ""),
                    importance=block.get("importance", 0.5),
                    hybrid_score=hybrid_score,
                    vector_score=vector_score,
                    bm25_score=bm25_score,
                    depth=current_depth,
                    project=block.get("root")
                )
                candidates.append(result)

            # Pruning decision:
            # 1. Always continue if within min_depth (ensure graph exploration)
            # 2. Always continue from anchor
            # 3. Continue if score is above explore_threshold
            should_continue = (
                current_depth < min_depth or
                is_anchor or
                hybrid_score >= explore_threshold
            )
            if not should_continue:
                nodes_pruned += 1
                return

            # Explore parent (before)
            parent = self._get_parent(block)
            if parent:
                dfs(parent, current_depth + 1, is_anchor=False)

            # Explore children (after)
            children = self._get_children(block)
            for child in children:
                dfs(child, current_depth + 1, is_anchor=False)

        # Start DFS from anchor (always explore from anchor)
        dfs(anchor, 0, is_anchor=True)

        # Sort by hybrid score and limit results
        candidates.sort(key=lambda x: x.hybrid_score, reverse=True)
        results = candidates[:limit]

        # Calculate elapsed time
        elapsed_ms = (time.time() - start_time) * 1000

        # Build metadata
        metadata = SearchMetadata(
            search_type="hybrid_graph",
            anchor_hash=anchor.get("hash"),
            project=project,
            depth_used=max_depth_used,
            nodes_visited=len(visited),
            nodes_pruned=nodes_pruned,
            elapsed_ms=elapsed_ms,
            result_count=len(results)
        )

        # Update metrics
        self._update_metrics(len(visited), max_depth_used, len(results), nodes_pruned)

        logger.info(
            f"Hybrid search completed: {len(results)} results, "
            f"{len(visited)} nodes visited, {nodes_pruned} pruned, "
            f"{elapsed_ms:.1f}ms"
        )

        return results, metadata

    def _compute_hybrid_score(
        self,
        query: str,
        query_keywords: List[str],
        query_embedding: Optional[np.ndarray],
        block: Dict
    ) -> Tuple[float, float, float]:
        """
        Compute hybrid score (Vector + BM25) for a block.

        Returns:
            Tuple of (hybrid_score, vector_score, bm25_score)
        """
        # Vector similarity
        vector_score = 0.0
        if query_embedding is not None:
            block_embedding = self._get_block_embedding(block)
            if block_embedding is not None:
                vector_score = self._cosine_similarity(query_embedding, block_embedding)

        # BM25 score
        block_keywords = self._get_keywords(block)
        bm25_raw = self.bm25_index.score_with_keywords(query_keywords, block_keywords)
        bm25_score = self.bm25_index.normalize_score(bm25_raw)

        # Fallback: text matching if no embedding
        if query_embedding is None:
            text_score = self._text_similarity(query, block.get("context", ""))
            vector_score = text_score

        # Hybrid score
        hybrid_score = self.hybrid_scorer.score(vector_score, query_keywords, block_keywords)

        return hybrid_score, vector_score, bm25_score

    def _tokenize_query(self, query: str) -> List[str]:
        """Tokenize query for BM25 scoring."""
        try:
            from ..text_utils import extract_keywords
            return extract_keywords(query, max_keywords=10)
        except ImportError:
            # Simple fallback tokenization
            words = query.lower().split()
            stopwords = {"the", "a", "an", "is", "are", "was", "were", "이", "그", "저", "을", "를"}
            return [w for w in words if w not in stopwords and len(w) > 1]

    def _get_anchor_block(self, anchor_hash: Optional[str], project: Optional[str]) -> Optional[Dict]:
        """Get anchor block by hash or project."""
        cursor = self.db_manager.conn.cursor()

        if anchor_hash:
            cursor.execute("SELECT * FROM blocks WHERE hash = ?", (anchor_hash,))
            row = cursor.fetchone()
            if row:
                return dict(row)

        if project:
            # Get most recent block in project (branch)
            cursor.execute("""
                SELECT * FROM blocks
                WHERE root = ?
                ORDER BY timestamp DESC
                LIMIT 1
            """, (project,))
            row = cursor.fetchone()
            if row:
                return dict(row)

        return None

    def _get_most_recent_block(self, project: Optional[str] = None) -> Optional[Dict]:
        """Get most recent block as fallback anchor."""
        cursor = self.db_manager.conn.cursor()

        if project:
            cursor.execute("""
                SELECT * FROM blocks
                WHERE root = ?
                ORDER BY timestamp DESC
                LIMIT 1
            """, (project,))
        else:
            cursor.execute("""
                SELECT * FROM blocks
                ORDER BY timestamp DESC
                LIMIT 1
            """)

        row = cursor.fetchone()
        return dict(row) if row else None

    def _get_parent(self, block: Dict) -> Optional[Dict]:
        """Get parent block (via before link)."""
        before_hash = block.get("before")
        if not before_hash:
            return None

        cursor = self.db_manager.conn.cursor()
        cursor.execute("SELECT * FROM blocks WHERE hash = ?", (before_hash,))
        row = cursor.fetchone()
        return dict(row) if row else None

    def _get_children(self, block: Dict) -> List[Dict]:
        """Get child blocks (via after links)."""
        children = []
        after_list = block.get("after", [])

        if isinstance(after_list, str):
            try:
                after_list = json.loads(after_list)
            except json.JSONDecodeError:
                after_list = []

        if not after_list:
            return []

        cursor = self.db_manager.conn.cursor()
        for child_hash in after_list:
            cursor.execute("SELECT * FROM blocks WHERE hash = ?", (child_hash,))
            row = cursor.fetchone()
            if row:
                children.append(dict(row))

        return children

    def _get_keywords(self, block: Dict) -> List[str]:
        """Extract keywords from block (from block_keywords table)."""
        # First check if keywords are cached in block dict
        keywords = block.get("_keywords")
        if keywords:
            return keywords

        # Query from block_keywords table
        block_index = block.get("block_index")
        if block_index is None:
            return []

        try:
            cursor = self.db_manager.conn.cursor()
            cursor.execute("""
                SELECT keyword FROM block_keywords WHERE block_index = ?
            """, (block_index,))
            keywords = [row[0] for row in cursor.fetchall()]
            return keywords
        except Exception as e:
            logger.debug(f"Failed to get keywords for block {block_index}: {e}")
            return []

    def _get_block_embedding(self, block: Dict) -> Optional[np.ndarray]:
        """Get embedding vector for block."""
        # Check if embedding is in block dict
        embedding = block.get("embedding")
        if embedding is not None:
            if isinstance(embedding, (list, np.ndarray)):
                return np.array(embedding, dtype=np.float32)

        # Fetch from block_embeddings table
        block_index = block.get("block_index")
        if block_index is None:
            return None

        try:
            cursor = self.db_manager.conn.cursor()
            cursor.execute("""
                SELECT embedding FROM block_embeddings WHERE block_index = ?
            """, (block_index,))
            row = cursor.fetchone()
            if row and row[0]:
                return np.frombuffer(row[0], dtype=np.float32)
        except Exception as e:
            logger.debug(f"Failed to get embedding for block {block_index}: {e}")

        return None

    def _cosine_similarity(self, a: np.ndarray, b: np.ndarray) -> float:
        """Compute cosine similarity between two vectors."""
        norm_a = np.linalg.norm(a)
        norm_b = np.linalg.norm(b)
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return float(np.dot(a, b) / (norm_a * norm_b))

    def _text_similarity(self, query: str, content: str) -> float:
        """Simple text similarity (fallback when no embeddings)."""
        if not query or not content:
            return 0.0

        query_lower = query.lower()
        content_lower = content.lower()

        # Exact match bonus
        if query_lower in content_lower:
            return 0.8

        # Word overlap
        query_words = set(query_lower.split())
        content_words = set(content_lower.split())

        if not query_words:
            return 0.0

        overlap = len(query_words & content_words)
        return overlap / len(query_words) * 0.5

    def _update_metrics(
        self,
        nodes_visited: int,
        depth: int,
        results: int,
        pruned: int
    ) -> None:
        """Update search metrics."""
        n = self.metrics["total_searches"]
        if n == 0:
            return

        # Running averages
        self.metrics["avg_nodes_visited"] = (
            self.metrics["avg_nodes_visited"] * (n - 1) + nodes_visited
        ) / n
        self.metrics["avg_depth"] = (
            self.metrics["avg_depth"] * (n - 1) + depth
        ) / n
        self.metrics["avg_results"] = (
            self.metrics["avg_results"] * (n - 1) + results
        ) / n

        total_explored = nodes_visited + pruned
        if total_explored > 0:
            self.metrics["pruning_rate"] = pruned / total_explored

    def rebuild_bm25_index(self) -> int:
        """Rebuild BM25 index from all blocks."""
        self.bm25_index = BM25Index()
        count = self.bm25_index.build_from_blocks(self.db_manager)
        if count > 0:
            self.bm25_index.save_to_db(self.db_manager)
        return count

    def get_stats(self) -> Dict[str, Any]:
        """Get search engine statistics."""
        return {
            "search_metrics": self.metrics,
            "bm25_stats": self.bm25_index.get_stats()
        }


class ProjectAnchorManager:
    """
    Manages anchors for project-based search.

    Each project has an anchor pointing to the most recently accessed block.
    This implements the design principle: "최근 조회된 블록을 앵커로"
    """

    def __init__(self, db_manager):
        self.db_manager = db_manager
        self._ensure_table()

    def _ensure_table(self) -> None:
        """Create project_anchors table if not exists."""
        cursor = self.db_manager.conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS project_anchors (
                project_name TEXT PRIMARY KEY,
                anchor_hash TEXT NOT NULL,
                anchor_block_index INTEGER,
                last_updated TEXT,
                access_count INTEGER DEFAULT 0
            )
        """)
        self.db_manager.conn.commit()

    def get_anchor(self, project: str) -> Optional[str]:
        """Get anchor hash for project."""
        cursor = self.db_manager.conn.cursor()
        cursor.execute("""
            SELECT anchor_hash FROM project_anchors WHERE project_name = ?
        """, (project,))
        row = cursor.fetchone()
        return row[0] if row else None

    def set_anchor(self, project: str, block_hash: str, block_index: int) -> None:
        """Set anchor for project."""
        from datetime import datetime

        cursor = self.db_manager.conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO project_anchors
            (project_name, anchor_hash, anchor_block_index, last_updated, access_count)
            VALUES (?, ?, ?, ?, COALESCE(
                (SELECT access_count + 1 FROM project_anchors WHERE project_name = ?),
                1
            ))
        """, (project, block_hash, block_index, datetime.now().isoformat(), project))
        self.db_manager.conn.commit()

    def update_on_access(self, project: str, block_hash: str, block_index: int) -> None:
        """Update anchor when a block is accessed (search/retrieve)."""
        # Only update if it's a different block
        current = self.get_anchor(project)
        if current != block_hash:
            self.set_anchor(project, block_hash, block_index)

    def list_projects(self) -> List[Dict[str, Any]]:
        """List all projects with their anchors."""
        cursor = self.db_manager.conn.cursor()
        cursor.execute("""
            SELECT project_name, anchor_hash, last_updated, access_count
            FROM project_anchors
            ORDER BY last_updated DESC
        """)

        return [
            {
                "project": row[0],
                "anchor_hash": row[1],
                "last_updated": row[2],
                "access_count": row[3]
            }
            for row in cursor.fetchall()
        ]
