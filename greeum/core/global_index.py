"""
Global Index for Greeum v3.0.0+
Implements inverted index and lightweight vector search for global jump
"""

import json
import logging
import sqlite3
import time
import numpy as np
from typing import List, Dict, Set, Optional, Tuple, Any
from collections import defaultdict
from datetime import datetime
import re

logger = logging.getLogger(__name__)


class GlobalIndex:
    """Global index for fast keyword and vector lookup"""
    
    def __init__(self, db_manager):
        self.db_manager = db_manager
        
        # In-memory inverted index
        self.inverted_index = defaultdict(set)  # keyword -> set of block_indices
        self.keyword_idf = {}  # keyword -> IDF score
        
        # Lightweight vector index (simple, no external dependencies)
        self.vectors = []  # List of (block_index, embedding) tuples
        self.vector_norms = []  # Precomputed norms for faster cosine
        
        # Stats
        self.stats = {
            "total_keywords": 0,
            "total_documents": 0,
            "index_size": 0,
            "last_rebuild": None,
            "jump_count": 0
        }
        
        # Build index on initialization
        self._build_index()
    
    def _build_index(self):
        """Build inverted index and vector index from database"""
        start_time = time.time()
        logger.info("Building global index...")
        
        try:
            cursor = self.db_manager.conn.cursor()
            
            # Get all blocks with keywords
            cursor.execute("""
                SELECT b.block_index, b.context, b.importance, b.timestamp
                FROM blocks b
                ORDER BY b.block_index
            """)
            
            blocks = cursor.fetchall()
            self.stats["total_documents"] = len(blocks)
            
            # Build inverted index
            document_freq = defaultdict(int)
            
            for block in blocks:
                block_index = block[0]
                context = block[1] or ""
                
                # Get keywords from database
                cursor.execute("""
                    SELECT keyword FROM block_keywords 
                    WHERE block_index = ?
                """, (block_index,))
                
                keywords = [row[0] for row in cursor.fetchall()]
                
                # Also extract keywords from context
                context_keywords = self._extract_keywords(context)
                all_keywords = set(keywords) | set(context_keywords)
                
                # Update inverted index
                for keyword in all_keywords:
                    keyword_lower = keyword.lower()
                    self.inverted_index[keyword_lower].add(block_index)
                    document_freq[keyword_lower] += 1
                
                # Get embedding for vector index
                cursor.execute("""
                    SELECT embedding FROM block_embeddings 
                    WHERE block_index = ?
                """, (block_index,))
                
                emb_row = cursor.fetchone()
                if emb_row and emb_row[0]:
                    embedding = np.frombuffer(emb_row[0], dtype=np.float32)
                    norm = np.linalg.norm(embedding)
                    if norm > 0:
                        self.vectors.append((block_index, embedding))
                        self.vector_norms.append(norm)
            
            # Calculate IDF scores
            total_docs = len(blocks)
            for keyword, freq in document_freq.items():
                # IDF = log(N / df)
                self.keyword_idf[keyword] = np.log((total_docs + 1) / (freq + 1))
            
            self.stats["total_keywords"] = len(self.inverted_index)
            self.stats["index_size"] = sum(len(docs) for docs in self.inverted_index.values())
            self.stats["last_rebuild"] = datetime.now().isoformat()
            
            elapsed = time.time() - start_time
            logger.info(f"Global index built in {elapsed:.2f}s: "
                       f"{self.stats['total_keywords']} keywords, "
                       f"{len(self.vectors)} vectors")
            
        except Exception as e:
            logger.error(f"Failed to build global index: {e}")
    
    def _extract_keywords(self, text: str, max_keywords: int = 10) -> List[str]:
        """Extract keywords from text using simple heuristics"""
        if not text:
            return []
        
        # Simple keyword extraction: words > 3 chars, not stopwords
        stopwords = {'the', 'and', 'for', 'with', 'this', 'that', 'from', 'have', 'been'}
        
        # Tokenize (simple approach)
        words = re.findall(r'\b[a-zA-Z가-힣]+\b', text.lower())
        
        # Filter and count
        word_freq = defaultdict(int)
        for word in words:
            if len(word) > 3 and word not in stopwords:
                word_freq[word] += 1
        
        # Return top keywords by frequency
        sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
        return [word for word, freq in sorted_words[:max_keywords]]
    
    def search_keywords(self, 
                       keywords: List[str], 
                       limit: int = 10,
                       exclude: Optional[Set[int]] = None) -> List[Tuple[int, float]]:
        """
        Search using inverted index with TF-IDF scoring
        
        Returns:
            List of (block_index, score) tuples
        """
        if not keywords:
            return []
        
        # Aggregate scores for each document
        doc_scores = defaultdict(float)
        
        for keyword in keywords:
            keyword_lower = keyword.lower()
            
            if keyword_lower in self.inverted_index:
                # Get IDF score
                idf = self.keyword_idf.get(keyword_lower, 1.0)
                
                # Get matching documents
                matching_docs = self.inverted_index[keyword_lower]
                
                for doc_id in matching_docs:
                    if exclude and doc_id in exclude:
                        continue
                    
                    # TF is assumed to be 1 for simplicity
                    # Could be improved with actual term frequency
                    doc_scores[doc_id] += idf
        
        # Sort by score
        sorted_results = sorted(doc_scores.items(), key=lambda x: x[1], reverse=True)
        
        return sorted_results[:limit]
    
    def search_vector(self,
                     query_embedding: np.ndarray,
                     limit: int = 10,
                     exclude: Optional[Set[int]] = None) -> List[Tuple[int, float]]:
        """
        Search using lightweight vector similarity
        
        Returns:
            List of (block_index, similarity) tuples
        """
        if query_embedding is None or len(self.vectors) == 0:
            return []
        
        query_norm = np.linalg.norm(query_embedding)
        if query_norm == 0:
            return []
        
        similarities = []
        
        for i, (block_index, embedding) in enumerate(self.vectors):
            if exclude and block_index in exclude:
                continue
            
            # Cosine similarity
            dot_product = np.dot(query_embedding, embedding)
            similarity = dot_product / (query_norm * self.vector_norms[i])
            
            similarities.append((block_index, float(similarity)))
        
        # Sort by similarity
        similarities.sort(key=lambda x: x[1], reverse=True)
        
        return similarities[:limit]
    
    def search_hybrid(self,
                     query: str,
                     query_embedding: Optional[np.ndarray] = None,
                     limit: int = 10,
                     exclude: Optional[Set[int]] = None,
                     keyword_weight: float = 0.5) -> List[Dict]:
        """
        Hybrid search combining keyword and vector search
        
        Returns:
            List of result dicts with block info and scores
        """
        results = []
        
        # Extract keywords from query
        keywords = self._extract_keywords(query)
        
        # Keyword search
        keyword_results = self.search_keywords(keywords, limit * 2, exclude)
        keyword_scores = {idx: score for idx, score in keyword_results}
        
        # Vector search
        vector_scores = {}
        if query_embedding is not None:
            vector_results = self.search_vector(query_embedding, limit * 2, exclude)
            vector_scores = {idx: score for idx, score in vector_results}
        
        # Combine scores
        all_indices = set(keyword_scores.keys()) | set(vector_scores.keys())
        
        combined_scores = []
        for idx in all_indices:
            # Normalize and combine scores
            kw_score = keyword_scores.get(idx, 0.0)
            vec_score = vector_scores.get(idx, 0.0)
            
            # Normalize keyword score (assume max IDF sum is ~10)
            kw_score_norm = min(1.0, kw_score / 10.0)
            
            # Combined score
            final_score = (keyword_weight * kw_score_norm + 
                          (1 - keyword_weight) * vec_score)
            
            combined_scores.append((idx, final_score))
        
        # Sort by combined score
        combined_scores.sort(key=lambda x: x[1], reverse=True)
        
        # Get block details for top results
        cursor = self.db_manager.conn.cursor()
        
        for block_index, score in combined_scores[:limit]:
            cursor.execute("""
                SELECT block_index, hash, context, timestamp, importance, root
                FROM blocks
                WHERE block_index = ?
            """, (block_index,))
            
            row = cursor.fetchone()
            if row:
                results.append({
                    "block_index": row[0],
                    "hash": row[1],
                    "context": row[2],
                    "timestamp": row[3],
                    "importance": row[4],
                    "root": row[5],
                    "_score": score,
                    "_source": "global_index"
                })
        
        # Update stats
        self.stats["jump_count"] += 1
        
        return results
    
    def update_block(self, block_index: int, keywords: List[str], 
                    embedding: Optional[np.ndarray] = None):
        """Update index for a single block (incremental update)"""
        # Remove old entries
        for keyword_set in self.inverted_index.values():
            keyword_set.discard(block_index)
        
        # Add new keywords
        for keyword in keywords:
            keyword_lower = keyword.lower()
            self.inverted_index[keyword_lower].add(block_index)
            
            # Update IDF if new keyword
            if keyword_lower not in self.keyword_idf:
                # Approximate IDF for new keyword
                self.keyword_idf[keyword_lower] = np.log(self.stats["total_documents"] + 1)
        
        # Update vector index
        if embedding is not None:
            # Remove old embedding
            self.vectors = [(idx, emb) for idx, emb in self.vectors if idx != block_index]
            self.vector_norms = self.vector_norms[:len(self.vectors)]
            
            # Add new embedding
            norm = np.linalg.norm(embedding)
            if norm > 0:
                self.vectors.append((block_index, embedding))
                self.vector_norms.append(norm)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get index statistics"""
        return {
            **self.stats,
            "avg_docs_per_keyword": self.stats["index_size"] / max(self.stats["total_keywords"], 1),
            "vector_index_size": len(self.vectors),
            "memory_estimate_mb": self._estimate_memory() / (1024 * 1024)
        }
    
    def _estimate_memory(self) -> int:
        """Estimate memory usage in bytes"""
        # Rough estimation
        keyword_memory = sum(len(k) for k in self.inverted_index.keys()) * 2  # chars
        posting_memory = self.stats["index_size"] * 8  # int per posting
        vector_memory = len(self.vectors) * 4 * 768  # assume 768-dim float32
        
        return keyword_memory + posting_memory + vector_memory
    
    def rebuild(self):
        """Rebuild the entire index from scratch"""
        logger.info("Rebuilding global index...")
        
        # Clear existing index
        self.inverted_index.clear()
        self.keyword_idf.clear()
        self.vectors.clear()
        self.vector_norms.clear()
        
        # Rebuild
        self._build_index()


class GlobalJumpOptimizer:
    """Optimizer for global jump decisions"""
    
    def __init__(self):
        self.jump_history = []
        self.success_rate = 0.0
        self.query_count = 0  # Track total queries for warm-up
        self.db_age_queries = 0  # Queries since DB initialization

    def should_jump(self, local_results: int, query_complexity: float,
                   is_new_db: bool = False, local_quality_score: float = 0.0) -> bool:
        """Decide whether to perform global jump with improved logic"""
        self.query_count += 1

        # Always allow global search when local results are insufficient
        # This is critical for search functionality
        if local_results == 0:
            logger.info(f"Global jump triggered: No local results found")
            return True

        # P0 Hotfix: Warm-up period for new DB or new root (reduced from 5 to 2)
        if is_new_db or self.db_age_queries < 2:
            self.db_age_queries += 1
            # Allow jump even in warm-up if no local results
            if local_results == 0:
                return True
            logger.debug(f"Warm-up mode: query {self.db_age_queries}/2, checking conditions")

        # rc6: More aggressive global fallback
        # Jump if we have very few local results OR low quality
        conditions_any = [
            local_results < 3,  # Changed from 6 to 3 - be more aggressive
            local_quality_score < 0.5,  # Increased from 0.3 - higher quality bar
        ]

        # Additional boost conditions (simplified)
        conditions_boost = [
            query_complexity > 0.3,  # Lower threshold (was 0.5)
            self.query_count > 2,  # After just 2 queries (was 5)
            local_results < 5,  # Always boost if less than 5 results
        ]

        # Jump if ANY primary condition is met OR any boost condition
        # Changed from AND to OR for more aggressive fallback
        should_jump = any(conditions_any) or (local_results < 10 and any(conditions_boost))

        if should_jump:
            logger.info(f"Global jump triggered: local={local_results}, "
                       f"quality={local_quality_score:.2f}, "
                       f"complexity={query_complexity:.2f}, "
                       f"query_count={self.query_count}")
        else:
            logger.debug(f"Jump skipped: local={local_results}, quality={local_quality_score:.2f}")

        return should_jump

    def reset_for_new_root(self):
        """Reset warm-up counter when entering new root/branch"""
        self.db_age_queries = 0
        logger.debug("Jump optimizer reset for new root - warm-up period active")
    
    def record_jump(self, was_useful: bool, results_found: int = 0):
        """Record jump outcome for learning with enhanced tracking"""
        self.jump_history.append({
            "success": was_useful,
            "results": results_found,
            "timestamp": time.time()
        })

        # Keep last 20 jumps only (was 100)
        if len(self.jump_history) > 20:
            self.jump_history.pop(0)

        # Update success rate
        if self.jump_history:
            successes = sum(1 for h in self.jump_history if h["success"])
            self.success_rate = successes / len(self.jump_history)

    def get_optimizer_stats(self) -> Dict[str, Any]:
        """Get optimizer statistics"""
        return {
            "total_queries": self.query_count,
            "db_age_queries": self.db_age_queries,
            "success_rate": self.success_rate,
            "jump_attempts": len(self.jump_history),
            "warm_up_active": self.db_age_queries < 5
        }