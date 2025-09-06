"""
Greeum v2.5.0 Smart Search Engine
Enhanced search experience with relevance scoring and search suggestions
"""
from typing import List, Dict, Any, Optional, Tuple
import time
import logging
import re
from datetime import datetime, timedelta

from .search_engine import SearchEngine, BertReranker
from .block_manager import BlockManager
from ..temporal_reasoner import TemporalReasoner
from ..text_utils import extract_keywords_from_text

logger = logging.getLogger(__name__)

class SmartSearchEngine:
    """Enhanced search engine with relevance scoring and search suggestions"""
    
    def __init__(self, block_manager: Optional[BlockManager] = None, 
                 reranker: Optional[BertReranker] = None,
                 temporal_reasoner: Optional[TemporalReasoner] = None,
                 anchor_path: Optional[str] = None,
                 graph_path: Optional[str] = None):
        """
        Initialize smart search engine
        
        Args:
            block_manager: Block manager instance
            reranker: BERT reranker for relevance scoring
            temporal_reasoner: Temporal reasoning engine
            anchor_path: Path to anchor data
            graph_path: Path to graph data
        """
        self.base_engine = SearchEngine(
            block_manager=block_manager,
            reranker=reranker,
            anchor_path=anchor_path,
            graph_path=graph_path
        )
        self.temporal_reasoner = temporal_reasoner or TemporalReasoner(
            db_manager=block_manager.db_manager if block_manager else None
        )
        
    def smart_search(self, query: str, top_k: int = 5, 
                     show_relevance: bool = True,
                     suggest_alternatives: bool = True,
                     temporal_boost: Optional[bool] = None,
                     temporal_weight: float = 0.3,
                     slot: Optional[str] = None,
                     radius: Optional[int] = None) -> Dict[str, Any]:
        """
        Enhanced search with relevance scoring and suggestions
        
        Args:
            query: Search query
            top_k: Number of results to return
            show_relevance: Whether to show relevance percentages
            suggest_alternatives: Whether to generate search suggestions
            temporal_boost: Apply temporal boosting
            temporal_weight: Temporal score weight
            slot: Anchor slot for localized search
            radius: Graph traversal radius
            
        Returns:
            Enhanced search results with scores and suggestions
        """
        # 1. Perform base search
        base_result = self.base_engine.search(
            query=query,
            top_k=top_k,
            temporal_boost=temporal_boost,
            temporal_weight=temporal_weight,
            slot=slot,
            radius=radius
        )
        
        # 2. Enhanced relevance scoring
        enhanced_blocks = []
        if show_relevance:
            enhanced_blocks = self._add_relevance_percentages(
                base_result["blocks"], query
            )
        else:
            enhanced_blocks = base_result["blocks"]
        
        # 3. Generate search suggestions
        suggestions = []
        if suggest_alternatives:
            suggestions = self._generate_search_suggestions(
                query, base_result["blocks"]
            )
        
        # 4. Prepare enhanced result
        result = {
            "query": query,
            "blocks": enhanced_blocks,
            "suggestions": suggestions,
            "timing": base_result["timing"],
            "metadata": {
                **base_result["metadata"],
                "relevance_scoring_enabled": show_relevance,
                "suggestions_generated": len(suggestions),
                "smart_search_version": "2.5.0"
            }
        }
        
        return result
    
    def _add_relevance_percentages(self, blocks: List[Dict[str, Any]], 
                                  query: str) -> List[Dict[str, Any]]:
        """
        Add human-readable relevance percentages to search results
        
        Args:
            blocks: Search result blocks
            query: Original query
            
        Returns:
            Blocks with relevance percentages
        """
        if not blocks:
            return blocks
        
        enhanced_blocks = []
        
        # Find the score range for normalization
        scores = []
        for block in blocks:
            # Try multiple score fields (different scoring systems)
            score = (block.get('final_score') or 
                    block.get('relevance_score') or 
                    block.get('similarity') or 0.0)
            scores.append(score)
        
        if not scores:
            return blocks
        
        max_score = max(scores)
        min_score = min(scores) 
        score_range = max_score - min_score if max_score > min_score else 1.0
        
        for i, block in enumerate(blocks):
            enhanced_block = dict(block)  # Copy block
            
            # Get the best available score
            raw_score = (block.get('final_score') or 
                        block.get('relevance_score') or 
                        block.get('similarity') or 0.0)
            
            # Normalize to 0-100 percentage
            if score_range > 0:
                normalized = (raw_score - min_score) / score_range
            else:
                normalized = 1.0 if i == 0 else 0.8 - (i * 0.1)
            
            # Convert to percentage (ensure reasonable range)
            percentage = max(50, min(99, int(normalized * 45 + 50)))
            
            # Add relevance information
            enhanced_block['relevance_percentage'] = percentage
            enhanced_block['relevance_label'] = self._get_relevance_label(percentage)
            enhanced_block['raw_relevance_score'] = raw_score
            
            enhanced_blocks.append(enhanced_block)
        
        return enhanced_blocks
    
    def _get_relevance_label(self, percentage: int) -> str:
        """Convert percentage to human-readable label"""
        if percentage >= 90:
            return "매우 관련성 높음"
        elif percentage >= 80:
            return "관련성 높음"
        elif percentage >= 70:
            return "관련성 보통"
        elif percentage >= 60:
            return "관련성 낮음"
        else:
            return "관련성 매우 낮음"
    
    def _generate_search_suggestions(self, query: str, 
                                   blocks: List[Dict[str, Any]]) -> List[Dict[str, str]]:
        """
        Generate alternative search suggestions based on query and results
        
        Args:
            query: Original query
            blocks: Search results
            
        Returns:
            List of search suggestions
        """
        suggestions = []
        
        # 1. Temporal suggestions
        temporal_suggestions = self._suggest_temporal_variants(query)
        suggestions.extend(temporal_suggestions)
        
        # 2. Keyword-based suggestions
        keyword_suggestions = self._suggest_keyword_variants(query, blocks)
        suggestions.extend(keyword_suggestions)
        
        # 3. Related topic suggestions
        topic_suggestions = self._suggest_related_topics(blocks)
        suggestions.extend(topic_suggestions)
        
        # Remove duplicates and limit
        unique_suggestions = []
        seen_queries = set()
        
        for suggestion in suggestions:
            query_text = suggestion["query"]
            if query_text not in seen_queries and query_text != query:
                unique_suggestions.append(suggestion)
                seen_queries.add(query_text)
                
            if len(unique_suggestions) >= 5:  # Limit to 5 suggestions
                break
        
        return unique_suggestions
    
    def _suggest_temporal_variants(self, query: str) -> List[Dict[str, str]]:
        """Suggest temporal variations of the query"""
        suggestions = []
        
        # Detect if query already has temporal expression
        time_refs = self.temporal_reasoner.extract_time_references(query)
        
        if time_refs:
            # Already has temporal info, suggest broader time ranges
            suggestions.extend([
                {
                    "query": f"최근 {query.replace('어제', '').replace('지난주', '').strip()}",
                    "type": "temporal",
                    "description": "더 넓은 시간 범위에서 검색"
                }
            ])
        else:
            # No temporal info, suggest adding time filters
            suggestions.extend([
                {
                    "query": f"최근 {query}",
                    "type": "temporal", 
                    "description": "최근 기록으로 검색 범위 제한"
                },
                {
                    "query": f"지난주 {query}",
                    "type": "temporal",
                    "description": "지난주 기록에서 검색"
                }
            ])
        
        return suggestions
    
    def _suggest_keyword_variants(self, query: str, 
                                blocks: List[Dict[str, Any]]) -> List[Dict[str, str]]:
        """Suggest keyword variations based on results"""
        suggestions = []
        
        if not blocks:
            return suggestions
        
        # Extract keywords from top results
        result_keywords = set()
        for block in blocks[:3]:  # Top 3 results
            context = block.get('context', '')
            keywords = extract_keywords_from_text(context)
            result_keywords.update(keywords[:5])  # Top 5 keywords per block
        
        # Extract keywords from original query
        query_keywords = set(extract_keywords_from_text(query))
        
        # Find additional keywords
        additional_keywords = result_keywords - query_keywords
        
        # Create suggestions with additional keywords
        for keyword in list(additional_keywords)[:3]:  # Max 3 keyword suggestions
            suggestions.append({
                "query": f"{query} {keyword}",
                "type": "keyword",
                "description": f"'{keyword}' 키워드를 추가하여 검색"
            })
        
        return suggestions
    
    def _suggest_related_topics(self, blocks: List[Dict[str, Any]]) -> List[Dict[str, str]]:
        """Suggest related topics based on search results"""
        suggestions = []
        
        if not blocks:
            return suggestions
        
        # Analyze tags from search results
        all_tags = []
        for block in blocks[:3]:  # Analyze top 3 results
            # Extract tags if available (would need to be stored in block metadata)
            context = block.get('context', '')
            
            # Simple topic extraction based on common patterns
            if '프로젝트' in context:
                suggestions.append({
                    "query": "프로젝트 진행상황",
                    "type": "topic",
                    "description": "관련 프로젝트 정보 검색"
                })
            if '문제' in context or '오류' in context:
                suggestions.append({
                    "query": "문제 해결 방법",
                    "type": "topic", 
                    "description": "유사한 문제 해결 사례 검색"
                })
        
        return suggestions
    
    def get_search_statistics(self) -> Dict[str, Any]:
        """Get search engine statistics"""
        return {
            "engine_version": "2.5.0",
            "features": {
                "relevance_scoring": True,
                "search_suggestions": True,
                "temporal_reasoning": True,
                "bert_reranking": self.base_engine.reranker is not None,
                "anchor_search": True
            },
            "supported_languages": ["ko", "en", "ja", "zh", "es"]
        }