"""
Greeum v3.0.0: Memory Indexer
Multi-dimensional indexing for efficient memory retrieval
"""

import json
import logging
import numpy as np
from typing import Dict, List, Optional, Set, Tuple, Any
from datetime import datetime
from collections import defaultdict
import hashlib

logger = logging.getLogger(__name__)


class MemoryIndexer:
    """
    Multi-dimensional indexing system for memory retrieval
    Indexes memories by multiple dimensions for efficient access
    """
    
    def __init__(self, network, db_manager):
        """
        Initialize memory indexer
        
        Args:
            network: AssociationNetwork instance
            db_manager: DatabaseManager instance
        """
        self.network = network
        self.db_manager = db_manager
        
        # Multiple index structures
        self.temporal_index = {}  # timestamp -> node_ids
        self.semantic_index = {}  # keyword -> node_ids
        self.entity_index = {}    # entity_hash -> node_ids
        self.type_index = {}      # node_type -> node_ids
        self.importance_index = defaultdict(list)  # importance_level -> node_ids
        
        self._build_indexes()
    
    def _build_indexes(self):
        """Build all indexes from existing data"""
        logger.info("Building memory indexes...")
        
        for node_id, node in self.network.nodes.items():
            # Type index
            if node.node_type not in self.type_index:
                self.type_index[node.node_type] = set()
            self.type_index[node.node_type].add(node_id)
            
            # Temporal index (by date)
            if node.created_at:
                date_key = node.created_at[:10]  # YYYY-MM-DD
                if date_key not in self.temporal_index:
                    self.temporal_index[date_key] = set()
                self.temporal_index[date_key].add(node_id)
            
            # Semantic index (extract keywords)
            keywords = self._extract_keywords(node.content)
            for keyword in keywords:
                if keyword not in self.semantic_index:
                    self.semantic_index[keyword] = set()
                self.semantic_index[keyword].add(node_id)
            
            # Entity index (extract entities)
            entities = self._extract_entities(node.content)
            for entity in entities:
                entity_hash = self._hash_entity(entity)
                if entity_hash not in self.entity_index:
                    self.entity_index[entity_hash] = set()
                self.entity_index[entity_hash].add(node_id)
            
            # Importance index (if memory block exists)
            if node.memory_id:
                block = self.db_manager.get_block(node.memory_id)
                if block and 'importance' in block:
                    importance_bucket = int(block['importance'] * 10)  # 0-10 buckets
                    self.importance_index[importance_bucket].append(node_id)
        
        logger.info(f"Built indexes: {len(self.semantic_index)} keywords, "
                   f"{len(self.entity_index)} entities, "
                   f"{len(self.temporal_index)} dates")
    
    def _extract_keywords(self, text: str) -> Set[str]:
        """Extract keywords from text"""
        # Simple keyword extraction (can be enhanced with NLP)
        import re
        
        # Remove special characters and split
        words = re.findall(r'\b[a-zA-Z가-힣]+\b', text.lower())
        
        # Filter stop words (basic)
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 
                     'to', 'for', 'of', 'with', 'by', 'is', 'was', 'are', 'were',
                     '은', '는', '이', '가', '을', '를', '에', '의', '와', '과'}
        
        keywords = {word for word in words if len(word) > 2 and word not in stop_words}
        return keywords
    
    def _extract_entities(self, text: str) -> Set[str]:
        """Extract named entities from text"""
        entities = set()
        
        # Simple pattern-based entity extraction
        # Capitalized words (English names)
        import re
        cap_words = re.findall(r'\b[A-Z][a-z]+\b', text)
        entities.update(cap_words)
        
        # Korean names (simple pattern)
        korean_names = re.findall(r'[가-힣]{2,4}(?:님|씨|선생|교수|대표|이사)', text)
        entities.update(korean_names)
        
        # Email patterns
        emails = re.findall(r'\b[\w._%+-]+@[\w.-]+\.[A-Z|a-z]{2,}\b', text)
        entities.update(emails)
        
        # Project/system names (CamelCase)
        camel_case = re.findall(r'\b[A-Z][a-z]+[A-Z][a-z]+\b', text)
        entities.update(camel_case)
        
        return entities
    
    def _hash_entity(self, entity: str) -> str:
        """Create normalized hash for entity"""
        normalized = entity.lower().strip()
        return hashlib.md5(normalized.encode()).hexdigest()[:8]
    
    def search_by_keyword(self, keywords: List[str]) -> Set[str]:
        """
        Search nodes by keywords
        
        Args:
            keywords: List of keywords to search
            
        Returns:
            Set of matching node IDs
        """
        results = set()
        
        for keyword in keywords:
            keyword_lower = keyword.lower()
            
            # Direct match
            if keyword_lower in self.semantic_index:
                results.update(self.semantic_index[keyword_lower])
            
            # Partial match
            for indexed_keyword, node_ids in self.semantic_index.items():
                if keyword_lower in indexed_keyword or indexed_keyword in keyword_lower:
                    results.update(node_ids)
        
        return results
    
    def search_by_date_range(self, start_date: str, end_date: str) -> Set[str]:
        """
        Search nodes by date range
        
        Args:
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            
        Returns:
            Set of matching node IDs
        """
        results = set()
        
        for date_key, node_ids in self.temporal_index.items():
            if start_date <= date_key <= end_date:
                results.update(node_ids)
        
        return results
    
    def search_by_entity(self, entity: str) -> Set[str]:
        """
        Search nodes by entity
        
        Args:
            entity: Entity name
            
        Returns:
            Set of matching node IDs
        """
        entity_hash = self._hash_entity(entity)
        return self.entity_index.get(entity_hash, set())
    
    def search_by_importance(self, min_importance: float, 
                            max_importance: float = 1.0) -> List[str]:
        """
        Search nodes by importance range
        
        Args:
            min_importance: Minimum importance (0-1)
            max_importance: Maximum importance (0-1)
            
        Returns:
            List of node IDs sorted by importance
        """
        results = []
        min_bucket = int(min_importance * 10)
        max_bucket = int(max_importance * 10)
        
        for bucket in range(min_bucket, max_bucket + 1):
            if bucket in self.importance_index:
                results.extend(self.importance_index[bucket])
        
        return results
    
    def multi_dimensional_search(self, 
                                keywords: Optional[List[str]] = None,
                                entities: Optional[List[str]] = None,
                                date_range: Optional[Tuple[str, str]] = None,
                                importance_range: Optional[Tuple[float, float]] = None,
                                node_types: Optional[List[str]] = None) -> List[str]:
        """
        Perform multi-dimensional search
        
        Args:
            keywords: Keywords to search
            entities: Entities to search
            date_range: (start_date, end_date) tuple
            importance_range: (min, max) importance tuple
            node_types: Node types to filter
            
        Returns:
            List of matching node IDs ranked by relevance
        """
        # Collect results from each dimension
        result_sets = []
        
        if keywords:
            result_sets.append(self.search_by_keyword(keywords))
        
        if entities:
            entity_results = set()
            for entity in entities:
                entity_results.update(self.search_by_entity(entity))
            result_sets.append(entity_results)
        
        if date_range:
            result_sets.append(self.search_by_date_range(*date_range))
        
        if importance_range:
            importance_results = set(self.search_by_importance(*importance_range))
            result_sets.append(importance_results)
        
        if node_types:
            type_results = set()
            for node_type in node_types:
                if node_type in self.type_index:
                    type_results.update(self.type_index[node_type])
            result_sets.append(type_results)
        
        # Intersect all result sets
        if not result_sets:
            return []
        
        final_results = result_sets[0]
        for result_set in result_sets[1:]:
            final_results = final_results.intersection(result_set)
        
        # Rank by number of dimensions matched
        node_scores = {}
        for node_id in final_results:
            score = sum(1 for result_set in result_sets if node_id in result_set)
            node_scores[node_id] = score
        
        # Sort by score
        ranked_results = sorted(node_scores.keys(), 
                              key=lambda x: node_scores[x], 
                              reverse=True)
        
        return ranked_results
    
    def update_index(self, node_id: str):
        """
        Update indexes for a specific node
        
        Args:
            node_id: Node ID to update
        """
        node = self.network.nodes.get(node_id)
        if not node:
            return
        
        # Remove from existing indexes
        self._remove_from_indexes(node_id)
        
        # Re-add to indexes
        if node.node_type not in self.type_index:
            self.type_index[node.node_type] = set()
        self.type_index[node.node_type].add(node_id)
        
        if node.created_at:
            date_key = node.created_at[:10]
            if date_key not in self.temporal_index:
                self.temporal_index[date_key] = set()
            self.temporal_index[date_key].add(node_id)
        
        keywords = self._extract_keywords(node.content)
        for keyword in keywords:
            if keyword not in self.semantic_index:
                self.semantic_index[keyword] = set()
            self.semantic_index[keyword].add(node_id)
        
        entities = self._extract_entities(node.content)
        for entity in entities:
            entity_hash = self._hash_entity(entity)
            if entity_hash not in self.entity_index:
                self.entity_index[entity_hash] = set()
            self.entity_index[entity_hash].add(node_id)
    
    def _remove_from_indexes(self, node_id: str):
        """Remove node from all indexes"""
        # Remove from type index
        for node_ids in self.type_index.values():
            node_ids.discard(node_id)
        
        # Remove from temporal index
        for node_ids in self.temporal_index.values():
            node_ids.discard(node_id)
        
        # Remove from semantic index
        for node_ids in self.semantic_index.values():
            node_ids.discard(node_id)
        
        # Remove from entity index
        for node_ids in self.entity_index.values():
            node_ids.discard(node_id)
        
        # Remove from importance index
        for node_list in self.importance_index.values():
            if node_id in node_list:
                node_list.remove(node_id)
    
    def get_index_stats(self) -> Dict[str, Any]:
        """
        Get indexing statistics
        
        Returns:
            Dictionary with index statistics
        """
        return {
            'total_keywords': len(self.semantic_index),
            'total_entities': len(self.entity_index),
            'total_dates': len(self.temporal_index),
            'node_types': list(self.type_index.keys()),
            'importance_distribution': {
                bucket: len(nodes) 
                for bucket, nodes in self.importance_index.items()
            },
            'avg_keywords_per_node': (
                sum(len(nodes) for nodes in self.semantic_index.values()) / 
                len(self.network.nodes) if self.network.nodes else 0
            )
        }
    
    def find_similar_nodes(self, node_id: str, top_k: int = 5) -> List[Tuple[str, float]]:
        """
        Find nodes similar to given node
        
        Args:
            node_id: Reference node ID
            top_k: Number of similar nodes to return
            
        Returns:
            List of (node_id, similarity_score) tuples
        """
        node = self.network.nodes.get(node_id)
        if not node:
            return []
        
        # Extract features
        keywords = self._extract_keywords(node.content)
        entities = self._extract_entities(node.content)
        
        # Score other nodes
        scores = {}
        for other_id, other_node in self.network.nodes.items():
            if other_id == node_id:
                continue
            
            score = 0.0
            
            # Keyword overlap
            other_keywords = self._extract_keywords(other_node.content)
            if keywords and other_keywords:
                overlap = len(keywords.intersection(other_keywords))
                score += overlap / max(len(keywords), len(other_keywords))
            
            # Entity overlap
            other_entities = self._extract_entities(other_node.content)
            if entities and other_entities:
                overlap = len(entities.intersection(other_entities))
                score += overlap / max(len(entities), len(other_entities))
            
            # Type similarity
            if node.node_type == other_node.node_type:
                score += 0.2
            
            # Temporal proximity
            if node.created_at and other_node.created_at:
                date1 = datetime.fromisoformat(node.created_at)
                date2 = datetime.fromisoformat(other_node.created_at)
                days_diff = abs((date2 - date1).days)
                if days_diff < 7:
                    score += 0.3 * (1 - days_diff / 7)
            
            scores[other_id] = score
        
        # Sort and return top-k
        sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        return sorted_scores[:top_k]