"""
BM25 Index for Greeum v5.0
Provides keyword-based scoring for Hybrid Search (Vector + BM25)

Features:
- Pre-computed IDF for efficient scoring
- Korean/English support via text_utils
- Persistence to SQLite database
- Integration with existing block system
"""

import math
import logging
import json
from typing import List, Dict, Optional, Tuple, Set
from collections import Counter
import sqlite3

logger = logging.getLogger(__name__)


class BM25Index:
    """
    BM25 Index with pre-computed IDF for fast scoring.

    BM25 Formula:
        score = Σ IDF(qi) * (tf * (k1 + 1)) / (tf + k1 * (1 - b + b * dl/avgdl))

    Where:
        - IDF(qi) = log((N - df + 0.5) / (df + 0.5) + 1)
        - tf = term frequency in document
        - dl = document length
        - avgdl = average document length
        - k1 = term frequency saturation parameter (default: 1.5)
        - b = length normalization parameter (default: 0.75)
    """

    def __init__(self, k1: float = 1.5, b: float = 0.75):
        """
        Initialize BM25 Index.

        Args:
            k1: Term frequency saturation (higher = more weight on tf)
            b: Length normalization (0 = no normalization, 1 = full normalization)
        """
        self.k1 = k1
        self.b = b

        # Document frequency for IDF calculation
        self.idf: Dict[str, int] = {}  # word -> document count

        # Document metadata
        self.doc_count: int = 0
        self.total_doc_len: int = 0
        self.avg_doc_len: float = 0.0
        self.doc_lens: Dict[str, int] = {}  # doc_id -> length

        # Document keywords cache (for scoring)
        self.doc_keywords: Dict[str, List[str]] = {}  # doc_id -> keywords list

        # Computed IDF values cache
        self._idf_cache: Dict[str, float] = {}
        self._idf_dirty: bool = True

    def add_document(self, doc_id: str, keywords: List[str]) -> None:
        """
        Add a document to the index.

        Args:
            doc_id: Unique document identifier (e.g., block_index as string)
            keywords: List of keywords/terms in the document
        """
        if doc_id in self.doc_lens:
            # Document already exists, remove old data first
            self._remove_document(doc_id)

        # Store document keywords
        self.doc_keywords[doc_id] = keywords

        # Update document count and length
        self.doc_lens[doc_id] = len(keywords)
        self.doc_count += 1
        self.total_doc_len += len(keywords)
        self.avg_doc_len = self.total_doc_len / self.doc_count if self.doc_count > 0 else 0.0

        # Update document frequency for each unique term
        unique_terms = set(keywords)
        for term in unique_terms:
            self.idf[term] = self.idf.get(term, 0) + 1

        # Mark IDF cache as dirty
        self._idf_dirty = True

    def _remove_document(self, doc_id: str) -> None:
        """Remove a document from the index."""
        if doc_id not in self.doc_lens:
            return

        old_keywords = self.doc_keywords.get(doc_id, [])
        old_len = self.doc_lens[doc_id]

        # Update IDF
        unique_terms = set(old_keywords)
        for term in unique_terms:
            if term in self.idf:
                self.idf[term] -= 1
                if self.idf[term] <= 0:
                    del self.idf[term]

        # Update stats
        self.doc_count -= 1
        self.total_doc_len -= old_len
        self.avg_doc_len = self.total_doc_len / self.doc_count if self.doc_count > 0 else 0.0

        # Remove from storage
        del self.doc_lens[doc_id]
        if doc_id in self.doc_keywords:
            del self.doc_keywords[doc_id]

        self._idf_dirty = True

    def _compute_idf(self, term: str) -> float:
        """Compute IDF for a term."""
        if not self._idf_dirty and term in self._idf_cache:
            return self._idf_cache[term]

        df = self.idf.get(term, 0)
        if df == 0:
            return 0.0

        # BM25 IDF formula: log((N - df + 0.5) / (df + 0.5) + 1)
        idf_value = math.log((self.doc_count - df + 0.5) / (df + 0.5) + 1.0)
        self._idf_cache[term] = idf_value
        return idf_value

    def _rebuild_idf_cache(self) -> None:
        """Rebuild the entire IDF cache."""
        self._idf_cache.clear()
        for term in self.idf:
            self._idf_cache[term] = self._compute_idf(term)
        self._idf_dirty = False

    def score(self, query_keywords: List[str], doc_id: str) -> float:
        """
        Compute BM25 score for a query against a specific document.

        Args:
            query_keywords: Keywords from the query
            doc_id: Document ID to score

        Returns:
            BM25 score (0 if document not found)
        """
        if doc_id not in self.doc_lens:
            return 0.0

        doc_keywords = self.doc_keywords.get(doc_id, [])
        return self.score_with_keywords(query_keywords, doc_keywords)

    def score_with_keywords(self, query_keywords: List[str], doc_keywords: List[str]) -> float:
        """
        Compute BM25 score given query and document keywords directly.

        Args:
            query_keywords: Keywords from the query
            doc_keywords: Keywords from the document

        Returns:
            BM25 score
        """
        if not query_keywords or not doc_keywords:
            return 0.0

        doc_len = len(doc_keywords)
        doc_keyword_counts = Counter(doc_keywords)
        score = 0.0

        for term in query_keywords:
            if term not in doc_keyword_counts:
                continue

            # IDF
            idf = self._compute_idf(term)
            if idf <= 0:
                # Term not in corpus, use smoothed IDF
                idf = math.log(self.doc_count + 1.0)

            # TF with length normalization
            tf = doc_keyword_counts[term]
            tf_normalized = (tf * (self.k1 + 1)) / (
                tf + self.k1 * (1 - self.b + self.b * doc_len / max(self.avg_doc_len, 1.0))
            )

            score += idf * tf_normalized

        return score

    def normalize_score(self, score: float) -> float:
        """
        Normalize BM25 score to [0, 1] range.

        Uses sigmoid-like normalization for better comparison with vector similarity.
        """
        if score <= 0:
            return 0.0
        # Sigmoid normalization: 2 / (1 + exp(-score/scale)) - 1
        scale = 10.0  # Adjust based on typical BM25 score range
        return 2.0 / (1.0 + math.exp(-score / scale)) - 1.0

    def search(self, query_keywords: List[str], top_k: int = 10) -> List[Tuple[str, float]]:
        """
        Search for documents most relevant to the query.

        Args:
            query_keywords: Keywords from the query
            top_k: Number of results to return

        Returns:
            List of (doc_id, score) tuples, sorted by score descending
        """
        if not query_keywords:
            return []

        # Refresh IDF cache if needed
        if self._idf_dirty:
            self._rebuild_idf_cache()

        results = []
        for doc_id in self.doc_lens:
            score = self.score(query_keywords, doc_id)
            if score > 0:
                results.append((doc_id, score))

        # Sort by score descending
        results.sort(key=lambda x: x[1], reverse=True)
        return results[:top_k]

    def get_stats(self) -> Dict:
        """Get index statistics."""
        return {
            "doc_count": self.doc_count,
            "avg_doc_len": round(self.avg_doc_len, 2),
            "vocabulary_size": len(self.idf),
            "k1": self.k1,
            "b": self.b
        }

    # === Persistence Methods ===

    def save_to_db(self, db_manager) -> None:
        """
        Save BM25 index to SQLite database.

        Creates a table 'bm25_index' if not exists.
        """
        cursor = db_manager.conn.cursor()

        # Create table if not exists
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS bm25_index (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        """)

        # Serialize and save
        data = {
            "k1": self.k1,
            "b": self.b,
            "idf": self.idf,
            "doc_count": self.doc_count,
            "total_doc_len": self.total_doc_len,
            "avg_doc_len": self.avg_doc_len,
            "doc_lens": self.doc_lens,
            "doc_keywords": self.doc_keywords
        }

        cursor.execute("""
            INSERT OR REPLACE INTO bm25_index (key, value) VALUES (?, ?)
        """, ("index_data", json.dumps(data)))

        db_manager.conn.commit()
        logger.info(f"BM25 index saved: {self.doc_count} documents, {len(self.idf)} terms")

    def load_from_db(self, db_manager) -> bool:
        """
        Load BM25 index from SQLite database.

        Returns:
            True if loaded successfully, False otherwise
        """
        cursor = db_manager.conn.cursor()

        try:
            cursor.execute("""
                SELECT value FROM bm25_index WHERE key = ?
            """, ("index_data",))

            row = cursor.fetchone()
            if not row:
                logger.info("No BM25 index found in database")
                return False

            data = json.loads(row[0])

            self.k1 = data.get("k1", 1.5)
            self.b = data.get("b", 0.75)
            self.idf = data.get("idf", {})
            self.doc_count = data.get("doc_count", 0)
            self.total_doc_len = data.get("total_doc_len", 0)
            self.avg_doc_len = data.get("avg_doc_len", 0.0)
            self.doc_lens = data.get("doc_lens", {})
            self.doc_keywords = data.get("doc_keywords", {})

            self._idf_dirty = True

            logger.info(f"BM25 index loaded: {self.doc_count} documents, {len(self.idf)} terms")
            return True

        except sqlite3.OperationalError:
            # Table doesn't exist
            logger.info("BM25 index table not found")
            return False
        except Exception as e:
            logger.error(f"Failed to load BM25 index: {e}")
            return False

    def build_from_blocks(self, db_manager, tokenizer_func=None) -> int:
        """
        Build BM25 index from existing blocks in database.

        Args:
            db_manager: Database manager instance
            tokenizer_func: Function to tokenize content (default: split by space and keywords field)

        Returns:
            Number of documents indexed
        """
        from ..text_utils import extract_keywords

        cursor = db_manager.conn.cursor()

        # Get all blocks with their keywords from block_keywords table
        cursor.execute("""
            SELECT b.block_index, b.context, GROUP_CONCAT(bk.keyword, ' ')
            FROM blocks b
            LEFT JOIN block_keywords bk ON b.block_index = bk.block_index
            GROUP BY b.block_index
        """)

        count = 0
        for row in cursor.fetchall():
            block_index, context, keywords_str = row
            doc_id = str(block_index)

            # Parse keywords from concatenated string
            keywords = keywords_str.split() if keywords_str else []

            if not keywords and context:
                # Extract keywords from content
                keywords = extract_keywords(context, max_keywords=10)

            if keywords:
                self.add_document(doc_id, keywords)
                count += 1

        logger.info(f"Built BM25 index from {count} blocks")
        return count


class HybridScorer:
    """
    Combines Vector similarity and BM25 scores using weighted average or RRF.

    Fusion Methods:
    - weighted_avg: score = w_vec * vec_sim + w_bm25 * bm25_norm
    - rrf: score = Σ 1/(k + rank_i) for each ranker
    """

    def __init__(
        self,
        bm25_index: BM25Index,
        vector_weight: float = 0.5,
        bm25_weight: float = 0.5,
        fusion_method: str = "weighted_avg",
        rrf_k: int = 60
    ):
        """
        Initialize HybridScorer.

        Args:
            bm25_index: BM25Index instance
            vector_weight: Weight for vector similarity (for weighted_avg)
            bm25_weight: Weight for BM25 score (for weighted_avg)
            fusion_method: "weighted_avg" or "rrf"
            rrf_k: k parameter for RRF (default: 60)
        """
        self.bm25_index = bm25_index
        self.vector_weight = vector_weight
        self.bm25_weight = bm25_weight
        self.fusion_method = fusion_method
        self.rrf_k = rrf_k

    def score(
        self,
        vector_similarity: float,
        query_keywords: List[str],
        doc_keywords: List[str]
    ) -> float:
        """
        Compute hybrid score from vector similarity and BM25.

        Args:
            vector_similarity: Cosine similarity from vector search (0-1)
            query_keywords: Keywords from query
            doc_keywords: Keywords from document

        Returns:
            Combined score
        """
        bm25_raw = self.bm25_index.score_with_keywords(query_keywords, doc_keywords)
        bm25_norm = self.bm25_index.normalize_score(bm25_raw)

        if self.fusion_method == "weighted_avg":
            return self.vector_weight * vector_similarity + self.bm25_weight * bm25_norm
        else:
            # For single document, just return weighted average
            # RRF is meant for ranking multiple documents
            return self.vector_weight * vector_similarity + self.bm25_weight * bm25_norm

    def rrf_fusion(
        self,
        vector_results: List[Tuple[str, float]],
        bm25_results: List[Tuple[str, float]]
    ) -> List[Tuple[str, float]]:
        """
        Fuse two ranked lists using Reciprocal Rank Fusion.

        Args:
            vector_results: List of (doc_id, score) from vector search
            bm25_results: List of (doc_id, score) from BM25 search

        Returns:
            Fused ranking as list of (doc_id, rrf_score)
        """
        # Build rank dictionaries (1-indexed)
        vector_ranks = {doc_id: rank + 1 for rank, (doc_id, _) in enumerate(vector_results)}
        bm25_ranks = {doc_id: rank + 1 for rank, (doc_id, _) in enumerate(bm25_results)}

        # Get all unique doc_ids
        all_docs = set(vector_ranks.keys()) | set(bm25_ranks.keys())

        # Compute RRF scores
        rrf_scores = []
        max_rank = len(all_docs) + self.rrf_k + 1  # Default rank for missing documents

        for doc_id in all_docs:
            vec_rank = vector_ranks.get(doc_id, max_rank)
            bm25_rank = bm25_ranks.get(doc_id, max_rank)

            rrf_score = (
                self.vector_weight / (self.rrf_k + vec_rank) +
                self.bm25_weight / (self.rrf_k + bm25_rank)
            )
            rrf_scores.append((doc_id, rrf_score))

        # Sort by RRF score descending
        rrf_scores.sort(key=lambda x: x[1], reverse=True)
        return rrf_scores
