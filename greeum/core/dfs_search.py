"""
DFS Local-First Search Engine for Greeum v3.0.0+
Implements depth-first search with branch awareness
"""

import time
import json
import logging
import numpy as np
from typing import List, Dict, Any, Optional, Set, Tuple
from collections import deque
from datetime import datetime
from .global_index import GlobalIndex, GlobalJumpOptimizer
from .branch_index import BranchIndexManager

logger = logging.getLogger(__name__)


class DFSSearchEngine:
    """DFS-based local-first search engine with global jump capability"""

    def __init__(self, db_manager):
        self.db_manager = db_manager
        self.metrics = {
            "total_searches": 0,
            "local_hits": 0,
            "global_fallbacks": 0,
            "branch_index_hits": 0,  # rc6: Track branch index usage
            "total_hops": 0,
            "avg_depth": 0.0,
            "jump_count": 0,
            "jump_success_rate": 0.0
        }

        # Initialize indices
        self.global_index = GlobalIndex(db_manager)
        self.jump_optimizer = GlobalJumpOptimizer()
        self.branch_index_manager = BranchIndexManager(db_manager)  # rc6: Branch indexing

        # P1: Adaptive DFS pattern learning
        self.adaptive_patterns = {
            "branch_access_frequency": {},  # branch_id -> access_count
            "branch_relevance_scores": {},  # branch_id -> avg_score
            "query_patterns": {},  # query_pattern -> successful_branches
            "depth_effectiveness": {1: 0.0, 2: 0.0, 3: 0.0, 4: 0.0, 5: 0.0}
        }
        self.learning_rate = 0.1  # for exponential moving average
    
    def search_with_dfs(self,
                        query: str,
                        query_embedding: Optional[np.ndarray] = None,
                        slot: Optional[str] = None,
                        entry: str = "cursor",
                        depth: int = 3,
                        limit: int = 8,
                        fallback: bool = True) -> Tuple[List[Dict], Dict]:
        """
        DFS local-first search with optional global fallback
        
        Args:
            query: Search query text
            query_embedding: Query embedding vector
            slot: STM slot (A/B/C) for branch head
            depth: Maximum DFS depth (default 3)
            limit: Maximum results (default 8)
            fallback: Enable global fallback if local insufficient
            
        Returns:
            (results, search_meta)
        """
        start_time = time.time()
        self.metrics["total_searches"] += 1
        
        # Get entry point from STM slot with cursor priority
        entry_point = self._get_entry_point_with_priority(slot, entry)
        if not entry_point:
            logger.warning(f"No entry point found for slot {slot}, entry type {entry}")
            # Fallback to most recent block
            entry_point = self._get_most_recent_block()
        
        # Initialize search metadata
        search_meta = {
            "search_type": "local",
            "slot": slot,
            "entry_type": entry,
            "root": None,
            "depth_used": 0,
            "hops": 0,
            "local_used": True,
            "fallback_used": False,
            "query_time_ms": 0.0,
            "result_count": 0
        }
        
        # rc6: Phase 1 - Branch Index Search (fast)
        branch_results = []
        current_branch = None

        if entry_point:
            current_branch = entry_point.get("root", entry_point.get("hash"))
            search_meta["root"] = current_branch

            # Search current branch index first (2ms)
            branch_results = self.branch_index_manager.search_current_branch(
                query, limit, query_embedding=query_embedding
            )

            if len(branch_results) < 3:  # Not enough in current branch
                # Search related branches
                related = self.branch_index_manager.get_related_branches(current_branch, 2)
                for branch in related:
                    additional = self.branch_index_manager.search_branch(
                        branch, query, limit, query_embedding=query_embedding
                    )
                    branch_results.extend(additional)
                    if len(branch_results) >= limit:
                        break

            if branch_results:
                self.metrics["branch_index_hits"] += 1
                search_meta["search_type"] = "branch_index"
                logger.info(f"Branch index found {len(branch_results)} results")

        # Phase 2: DFS local search (if branch index insufficient)
        local_results = branch_results
        local_hops = 0

        if len(branch_results) < 3:  # Fallback to DFS if branch index weak
            dfs_results, local_hops = self._dfs_search(
                entry_point=entry_point,
                query=query,
                query_embedding=query_embedding,
                max_depth=depth,
                max_results=limit
            )

            # Merge results (DFS might find different blocks)
            seen_indices = {r['block_index'] for r in branch_results}
            for r in dfs_results:
                if r['block_index'] not in seen_indices:
                    local_results.append(r)
                    seen_indices.add(r['block_index'])

            search_meta["hops"] = local_hops
            search_meta["depth_used"] = min(depth, local_hops)

        # P1: Update adaptive patterns based on search results
        self._update_adaptive_patterns(local_results, query, depth, local_hops)

        # Check if we have enough results
        if len(local_results) >= limit or not fallback:
            # Local/branch search sufficient
            self.metrics["local_hits"] += 1
            search_meta["result_count"] = len(local_results)
        else:
            # Phase 2: Global fallback with intelligent jump decision
            if fallback and len(local_results) < limit:
                # Check if jump is recommended
                query_complexity = len(query.split()) / 10.0  # Simple complexity measure
                should_jump = self.jump_optimizer.should_jump(
                    len(local_results), 
                    query_complexity
                )
                
                if should_jump:
                    search_meta["fallback_used"] = True
                    search_meta["search_type"] = "jump"
                    self.metrics["global_fallbacks"] += 1
                    
                    # Get global seeds
                    global_seeds = self._global_search(
                        query=query,
                        query_embedding=query_embedding,
                        exclude_ids=set(r.get("hash", "") for r in local_results),
                        limit=max(3, limit - len(local_results))  # At least 3 seeds
                    )
                    
                    # Shallow DFS from each global seed
                    for seed in global_seeds[:3]:  # Limit seeds to avoid explosion
                        # Convert seed to proper format if needed
                        if not isinstance(seed, dict) or "hash" not in seed:
                            continue
                        
                        seed_results, seed_hops = self._dfs_search(
                            entry_point=seed,
                            query=query,
                            query_embedding=query_embedding,
                            max_depth=1,  # Very shallow DFS from jump points
                            max_results=max(2, (limit - len(local_results)) // 2)
                        )
                        
                        # Add source info to jumped results
                        for result in seed_results:
                            result["_jump_source"] = seed.get("block_index", -1)
                        
                        local_results.extend(seed_results)
                        search_meta["hops"] += seed_hops
                        
                        if len(local_results) >= limit:
                            break
                    
                    # Record jump effectiveness
                    jump_added_results = len([r for r in local_results if "_jump_source" in r])
                    search_meta["jump_results"] = jump_added_results
        
        # Sort results by relevance
        results = self._rank_results(local_results, query_embedding)[:limit]
        
        # Update metrics
        self.metrics["total_hops"] += search_meta["hops"]
        if self.metrics["total_searches"] > 0:
            self.metrics["avg_depth"] = self.metrics["total_hops"] / self.metrics["total_searches"]
        
        # Calculate query time
        search_meta["query_time_ms"] = (time.time() - start_time) * 1000
        search_meta["result_count"] = len(results)
        
        logger.info(f"DFS search completed: {search_meta}")
        
        return results, search_meta
    
    def _get_entry_point_with_priority(self, slot: Optional[str], entry_type: str = "cursor") -> Optional[Dict]:
        """Get entry point block from STM slot with cursor → head → most_recent priority"""
        if not slot:
            return self._get_most_recent_block()

        try:
            # Use STMManager's get_entry_point with priority
            from .stm_manager import STMManager

            stm = STMManager(self.db_manager)
            entry_block_id = stm.get_entry_point(slot, entry_type)

            if entry_block_id:
                # Get block by hash
                cursor = self.db_manager.conn.cursor()
                cursor.execute("""
                    SELECT * FROM blocks WHERE hash = ?
                """, (entry_block_id,))
                row = cursor.fetchone()

                if row:
                    return dict(row)

            logger.debug(f"No entry point found for slot {slot}, entry_type {entry_type}")

        except Exception as e:
            logger.error(f"Failed to get entry point: {e}")

        return None

    def _get_entry_point(self, slot: Optional[str]) -> Optional[Dict]:
        """Legacy entry point method for backward compatibility"""
        try:
            return self._get_entry_point_with_priority(slot, "head")
        except Exception as e:
            logger.warning(f"Failed to get entry point for slot {slot}: {e}")
            return None
    
    def _get_most_recent_block(self) -> Optional[Dict]:
        """Get most recent block as fallback entry point"""
        try:
            cursor = self.db_manager.conn.cursor()
            cursor.execute("""
                SELECT * FROM blocks 
                ORDER BY timestamp DESC 
                LIMIT 1
            """)
            row = cursor.fetchone()
            
            if row:
                return dict(row)
        except Exception as e:
            logger.error(f"Failed to get most recent block: {e}")
        
        return None
    
    def _dfs_search(self,
                   entry_point: Dict,
                   query: str,
                   query_embedding: Optional[np.ndarray],
                   max_depth: int,
                   max_results: int) -> Tuple[List[Dict], int]:
        """
        Perform DFS search from entry point with branch-based exploration

        Returns:
            (results, hop_count)
        """
        results = []
        visited = set()
        visited_branches = set()  # Track visited branches
        hop_count = 0
        min_score_threshold = 0.3  # Minimum cumulative score threshold

        # Priority queue for better traversal: (priority, node, depth, score, branch_id)
        # Higher priority = explore first
        import heapq
        entry_branch = entry_point.get("root", entry_point.get("hash"))
        queue = [(-1.0, entry_point, 0, 1.0, entry_branch)]  # Negative for max-heap

        # Cache for embeddings
        embedding_cache = {}

        # Track results per branch for quality check
        branch_results = {}

        while queue and len(results) < max_results:
            neg_priority, node, depth, parent_score, current_branch = heapq.heappop(queue)

            if not node or node.get("hash") in visited:
                continue

            visited.add(node.get("hash"))
            hop_count += 1

            # Calculate relevance score with caching
            node_hash = node.get("hash")
            if node_hash in embedding_cache:
                node_embedding = embedding_cache[node_hash]
            else:
                node_embedding = self._get_node_embedding(node)
                embedding_cache[node_hash] = node_embedding

            score = self._calculate_relevance_improved(
                node, query, query_embedding, node_embedding
            )

            # Track branch for region exploration
            branch_id = node.get("root", node.get("hash"))
            if branch_id not in branch_results:
                branch_results[branch_id] = []

            # Boost score for recent nodes in same branch
            if entry_point.get("root") == branch_id:
                score *= 1.2  # 20% boost for same branch

            # Combine with parent score (propagation)
            combined_score = score * 0.8 + parent_score * 0.2

            # Add to results if relevant (lower threshold)
            threshold = 0.03  # Lower threshold for more inclusive results
            if score > threshold:
                node_copy = dict(node)
                node_copy["_score"] = combined_score
                node_copy["_depth"] = depth
                results.append(node_copy)
                branch_results[branch_id].append(combined_score)

            # Check if current branch has enough quality results
            branch_total_score = sum(branch_results.get(branch_id, []))

            # Branch-based exploration strategy
            # 1. Continue exploring current branch if quality is good OR depth is shallow
            # 2. No hard depth limit - continue while finding relevant content
            should_continue = (
                branch_total_score < min_score_threshold or  # Need more quality results
                depth < 5 or  # Always explore at least 5 levels
                score > 0.2  # Current node is still relevant
            )

            if should_continue:
                # Get neighbors
                children = self._get_children(node)
                parent = self._get_parent(node)
                xrefs = self._get_xrefs(node)

                # Calculate priorities for each neighbor
                for child in children:
                    if child and child.get("hash") not in visited:
                        child_score = self._quick_score(child, query)
                        priority = combined_score * 0.9 + child_score * 0.1
                        child_branch = child.get("root", child.get("hash"))
                        heapq.heappush(queue, (-priority, child, depth + 1, combined_score, child_branch))

                # Parent exploration
                if parent and parent.get("hash") not in visited:
                    parent_score_val = self._quick_score(parent, query)
                    priority = combined_score * 0.7 + parent_score_val * 0.3
                    parent_branch = parent.get("root", parent.get("hash"))
                    heapq.heappush(queue, (-priority, parent, depth + 1, combined_score * 0.8, parent_branch))

                # Cross-references - explore more if current branch is weak
                xref_limit = 5 if branch_total_score < 0.2 else 2
                for xref in xrefs[:xref_limit]:
                    if xref and xref.get("hash") not in visited:
                        xref_score = self._quick_score(xref, query)
                        priority = combined_score * 0.5 + xref_score * 0.5
                        xref_branch = xref.get("root", xref.get("hash"))
                        heapq.heappush(queue, (-priority, xref, depth + 1, combined_score * 0.5, xref_branch))

            # Branch switching: if current branch is exhausted, try before branches
            if branch_total_score < min_score_threshold and branch_id not in visited_branches:
                visited_branches.add(branch_id)
                # Get before branch
                before_branch = self._get_before_branch(node)
                if before_branch and before_branch.get("hash") not in visited:
                    logger.info(f"Switching to before branch: {before_branch.get('hash')[:8]}")
                    before_branch_id = before_branch.get("root", before_branch.get("hash"))
                    heapq.heappush(queue, (-0.8, before_branch, 0, 0.8, before_branch_id))
        
        return results, hop_count
    
    def _get_children(self, node: Dict) -> List[Dict]:
        """Get child nodes"""
        children = []
        
        try:
            # Parse after field
            after_list = node.get("after", [])
            if isinstance(after_list, str):
                after_list = json.loads(after_list)
            
            if after_list:
                cursor = self.db_manager.conn.cursor()
                for child_hash in after_list:
                    cursor.execute("""
                        SELECT * FROM blocks WHERE hash = ?
                    """, (child_hash,))
                    row = cursor.fetchone()
                    if row:
                        children.append(dict(row))
        except Exception as e:
            logger.debug(f"Failed to get children: {e}")
        
        return children
    
    def _get_parent(self, node: Dict) -> Optional[Dict]:
        """Get parent node"""
        try:
            before_hash = node.get("before")
            if before_hash:
                cursor = self.db_manager.conn.cursor()
                cursor.execute("""
                    SELECT * FROM blocks WHERE hash = ?
                """, (before_hash,))
                row = cursor.fetchone()
                if row:
                    return dict(row)
        except Exception as e:
            logger.debug(f"Failed to get parent: {e}")

        return None

    def _get_before_branch(self, node: Dict) -> Optional[Dict]:
        """Get the head of the before branch for branch switching"""
        try:
            # First try to get the root of the before branch
            before_hash = node.get("before")
            if not before_hash:
                return None

            cursor = self.db_manager.conn.cursor()
            # Get the before node
            cursor.execute("""
                SELECT * FROM blocks WHERE hash = ?
            """, (before_hash,))
            before_node = cursor.fetchone()

            if before_node:
                before_dict = dict(before_node)
                # Get the root of that branch
                before_root = before_dict.get("root", before_dict.get("hash"))

                # Find the head node of that branch (most recent in that branch)
                cursor.execute("""
                    SELECT * FROM blocks
                    WHERE root = ?
                    ORDER BY block_index DESC
                    LIMIT 1
                """, (before_root,))
                branch_head = cursor.fetchone()

                if branch_head:
                    return dict(branch_head)
                return before_dict
        except Exception as e:
            logger.debug(f"Failed to get before branch: {e}")

        return None
    
    def _get_xrefs(self, node: Dict) -> List[Dict]:
        """Get cross-referenced nodes"""
        xrefs = []
        
        try:
            xref_list = node.get("xref", [])
            if isinstance(xref_list, str):
                xref_list = json.loads(xref_list)
            
            if xref_list:
                cursor = self.db_manager.conn.cursor()
                for xref_hash in xref_list[:3]:  # Limit xrefs
                    cursor.execute("""
                        SELECT * FROM blocks WHERE hash = ?
                    """, (xref_hash,))
                    row = cursor.fetchone()
                    if row:
                        xrefs.append(dict(row))
        except Exception as e:
            logger.debug(f"Failed to get xrefs: {e}")
        
        return xrefs
    
    def _calculate_relevance_improved(self, 
                                     node: Dict,
                                     query: str,
                                     query_embedding: Optional[np.ndarray],
                                     node_embedding: Optional[np.ndarray] = None) -> float:
        """Calculate improved relevance score with better weighting"""
        score = 0.0
        weights = {
            'exact_match': 0.4,
            'word_overlap': 0.2,
            'embedding': 0.25,
            'recency': 0.1,
            'importance': 0.05
        }
        
        # Text similarity
        if query and node.get("context"):
            query_lower = query.lower()
            context_lower = node.get("context", "").lower()
            
            # Exact match bonus
            if query_lower in context_lower:
                score += weights['exact_match']
            
            # Word overlap with improved scoring
            query_words = set(query_lower.split())
            context_words = set(context_lower.split())

            if query_words and context_words:
                overlap = len(query_words & context_words)
                # Better normalization: ratio of matched words to query words
                # This gives higher scores when more query terms are found
                normalized_overlap = overlap / len(query_words) if query_words else 0
                score += weights['word_overlap'] * min(1.0, normalized_overlap)
        
        # Embedding similarity (use cached embedding)
        if query_embedding is not None and node_embedding is not None:
            cosine_sim = self._cosine_similarity(query_embedding, node_embedding)
            score += weights['embedding'] * cosine_sim
        
        # Recency bonus with smoother decay
        try:
            node_time = datetime.fromisoformat(node.get("timestamp", ""))
            time_diff = (datetime.now() - node_time).total_seconds()
            # Smoother decay: 50% after 3 days
            recency_score = np.exp(-time_diff / (3 * 24 * 3600 * 1.44))
            score += weights['recency'] * recency_score
        except:
            pass
        
        # Importance bonus
        importance = node.get("importance", 0.5)
        score += weights['importance'] * importance
        
        return min(1.0, score)
    
    def _quick_score(self, node: Dict, query: str) -> float:
        """Quick scoring for priority queue without embedding lookup"""
        if not query or not node.get("context"):
            return 0.0
        
        query_lower = query.lower()
        context_lower = node.get("context", "").lower()
        
        # Fast exact match check
        if query_lower in context_lower:
            return 0.8
        
        # Fast word overlap
        query_words = set(query_lower.split())
        context_words = set(context_lower.split()[:20])  # Check first 20 words only
        
        if query_words and context_words:
            overlap = len(query_words & context_words)
            return 0.5 * (overlap / len(query_words))
        
        return 0.1  # Small default score
    
    def _calculate_relevance(self, 
                            node: Dict,
                            query: str,
                            query_embedding: Optional[np.ndarray]) -> float:
        """Legacy relevance calculation - redirect to improved version"""
        return self._calculate_relevance_improved(node, query, query_embedding)
    
    def _get_node_embedding(self, node: Dict) -> Optional[np.ndarray]:
        """Get embedding for node"""
        try:
            block_index = node.get("block_index")
            if block_index is not None:
                cursor = self.db_manager.conn.cursor()
                cursor.execute("""
                    SELECT embedding FROM block_embeddings 
                    WHERE block_index = ?
                """, (block_index,))
                row = cursor.fetchone()
                
                if row and row[0]:
                    return np.frombuffer(row[0], dtype=np.float32)
        except Exception as e:
            logger.debug(f"Failed to get embedding: {e}")
        
        return None
    
    def _cosine_similarity(self, vec1: np.ndarray, vec2: np.ndarray) -> float:
        """Calculate cosine similarity"""
        if vec1 is None or vec2 is None:
            return 0.0
        
        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return float(dot_product / (norm1 * norm2))
    
    def _global_search(self,
                      query: str,
                      query_embedding: Optional[np.ndarray],
                      exclude_ids: Set[str],
                      limit: int) -> List[Dict]:
        """Global search using optimized index with hybrid search"""
        
        # Convert hash exclude set to block_index exclude set
        exclude_indices = set()
        if exclude_ids:
            cursor = self.db_manager.conn.cursor()
            for hash_id in exclude_ids:
                cursor.execute("SELECT block_index FROM blocks WHERE hash = ?", (hash_id,))
                result = cursor.fetchone()
                if result:
                    exclude_indices.add(result[0])
        
        # Use global index for hybrid search
        results = self.global_index.search_hybrid(
            query=query,
            query_embedding=query_embedding,
            limit=limit,
            exclude=exclude_indices,
            keyword_weight=0.6  # Slightly favor keywords for jump
        )
        
        # Record jump metrics
        self.metrics["jump_count"] += 1
        jump_was_useful = len(results) > 0
        self.jump_optimizer.record_jump(jump_was_useful)
        
        # Update jump success rate
        if self.metrics["jump_count"] > 0:
            self.metrics["jump_success_rate"] = self.jump_optimizer.success_rate
        
        logger.debug(f"Global jump found {len(results)} results, "
                    f"success_rate={self.jump_optimizer.success_rate:.2%}")
        
        return results
    
    def _rank_results(self, 
                     results: List[Dict],
                     query_embedding: Optional[np.ndarray]) -> List[Dict]:
        """Rank results by relevance"""
        # Results already have _score from DFS
        # Re-rank if needed
        
        for result in results:
            if "_score" not in result:
                result["_score"] = 0.5
        
        # Sort by score descending
        results.sort(key=lambda x: x.get("_score", 0), reverse=True)
        
        return results
    
    def _apply_adaptive_weights(self, base_score: float, branch_id: str, depth: int) -> float:
        """
        P1: Apply adaptive weights based on learned patterns

        Args:
            base_score: Original relevance score
            branch_id: Branch/root identifier
            depth: Current search depth

        Returns:
            Adjusted score with adaptive weights
        """
        adjusted_score = base_score

        # Apply branch relevance weight
        if branch_id in self.adaptive_patterns["branch_relevance_scores"]:
            branch_weight = self.adaptive_patterns["branch_relevance_scores"][branch_id]
            # Blend with exponential moving average
            adjusted_score = base_score * (1 - self.learning_rate) + base_score * branch_weight * self.learning_rate

        # Apply depth effectiveness weight
        if depth in self.adaptive_patterns["depth_effectiveness"]:
            depth_weight = self.adaptive_patterns["depth_effectiveness"][depth]
            if depth_weight > 0:
                adjusted_score *= (1 + depth_weight * 0.1)  # Max 10% boost per depth level

        # Apply branch access frequency (popular branches get slight boost)
        if branch_id in self.adaptive_patterns["branch_access_frequency"]:
            frequency = self.adaptive_patterns["branch_access_frequency"][branch_id]
            if frequency > 5:  # Only boost after 5 accesses
                frequency_boost = min(1.1, 1 + (frequency - 5) * 0.01)  # Max 10% boost
                adjusted_score *= frequency_boost

        return adjusted_score

    def _update_adaptive_patterns(self, results: List[Dict], query: str, max_depth: int, hops: int):
        """
        P1: Update adaptive patterns based on search results

        Args:
            results: Search results with scores
            query: Original query
            max_depth: Maximum depth used
            hops: Number of hops performed
        """
        if not results:
            return

        # Extract query pattern (simple tokenization)
        query_tokens = set(query.lower().split()[:3])  # First 3 words as pattern
        query_pattern = " ".join(sorted(query_tokens))

        # Update branch patterns
        for result in results:
            branch_id = result.get("root", result.get("hash"))
            if not branch_id:
                continue

            # Update branch access frequency
            if branch_id not in self.adaptive_patterns["branch_access_frequency"]:
                self.adaptive_patterns["branch_access_frequency"][branch_id] = 0
            self.adaptive_patterns["branch_access_frequency"][branch_id] += 1

            # Update branch relevance scores (exponential moving average)
            score = result.get("_score", 0.5)
            if branch_id not in self.adaptive_patterns["branch_relevance_scores"]:
                self.adaptive_patterns["branch_relevance_scores"][branch_id] = score
            else:
                old_score = self.adaptive_patterns["branch_relevance_scores"][branch_id]
                self.adaptive_patterns["branch_relevance_scores"][branch_id] = \
                    old_score * (1 - self.learning_rate) + score * self.learning_rate

            # Update depth effectiveness
            depth = result.get("_depth", 1)
            if depth in self.adaptive_patterns["depth_effectiveness"]:
                # Higher scores at certain depths indicate effectiveness
                if score > 0.3:  # Threshold for "effective"
                    old_effectiveness = self.adaptive_patterns["depth_effectiveness"][depth]
                    self.adaptive_patterns["depth_effectiveness"][depth] = \
                        old_effectiveness * (1 - self.learning_rate) + 1.0 * self.learning_rate

        # Update query patterns with successful branches
        if query_pattern and len(results) > 0:
            if query_pattern not in self.adaptive_patterns["query_patterns"]:
                self.adaptive_patterns["query_patterns"][query_pattern] = set()

            # Add top branches for this query pattern
            for result in results[:3]:  # Top 3 results
                branch_id = result.get("root", result.get("hash"))
                if branch_id:
                    self.adaptive_patterns["query_patterns"][query_pattern].add(branch_id)

        # Log adaptive learning
        logger.debug(f"P1 Adaptive: Updated patterns for {len(results)} results, "
                    f"branches tracked: {len(self.adaptive_patterns['branch_access_frequency'])}")

    def get_adaptive_suggestions(self, query: str) -> List[str]:
        """
        P1: Get suggested branches based on query patterns

        Returns:
            List of suggested branch IDs
        """
        query_tokens = set(query.lower().split()[:3])
        query_pattern = " ".join(sorted(query_tokens))

        suggestions = []

        # Direct pattern match
        if query_pattern in self.adaptive_patterns["query_patterns"]:
            suggestions.extend(list(self.adaptive_patterns["query_patterns"][query_pattern])[:3])

        # High-relevance branches
        sorted_branches = sorted(
            self.adaptive_patterns["branch_relevance_scores"].items(),
            key=lambda x: x[1],
            reverse=True
        )
        for branch_id, score in sorted_branches[:3]:
            if branch_id not in suggestions and score > 0.5:
                suggestions.append(branch_id)

        return suggestions[:5]  # Return top 5 suggestions

    def get_metrics(self) -> Dict[str, Any]:
        """Get search metrics"""
        metrics = dict(self.metrics)

        # Calculate rates
        if metrics["total_searches"] > 0:
            metrics["local_hit_rate"] = metrics["local_hits"] / metrics["total_searches"]
            metrics["fallback_rate"] = metrics["global_fallbacks"] / metrics["total_searches"]
        else:
            metrics["local_hit_rate"] = 0.0
            metrics["fallback_rate"] = 0.0

        # P1: Add adaptive metrics
        metrics["adaptive_patterns"] = {
            "branches_tracked": len(self.adaptive_patterns["branch_access_frequency"]),
            "query_patterns": len(self.adaptive_patterns["query_patterns"]),
            "avg_branch_relevance": np.mean(list(self.adaptive_patterns["branch_relevance_scores"].values()))
                if self.adaptive_patterns["branch_relevance_scores"] else 0.0,
            "depth_effectiveness": dict(self.adaptive_patterns["depth_effectiveness"])
        }
        
        return metrics
