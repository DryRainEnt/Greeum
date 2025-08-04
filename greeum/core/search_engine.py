from __future__ import annotations
"""Simple internal search engine that combines vector search and optional BERT re-ranker.
Relative/quick benchmark only – external detailed tests handled in GreeumTest repo.
"""
from typing import List, Dict, Any, Optional
import time
import logging
from datetime import datetime

from .block_manager import BlockManager
from ..embedding_models import get_embedding

try:
    from sentence_transformers import CrossEncoder  # type: ignore
except ImportError:
    CrossEncoder = None  # type: ignore

logger = logging.getLogger(__name__)

class BertReranker:
    """Thin wrapper around sentence-transformers CrossEncoder."""
    def __init__(self, model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"):
        if CrossEncoder is None:
            raise ImportError("sentence-transformers 가 설치되지 않았습니다.")
        self.model = CrossEncoder(model_name)

    def rerank(self, query: str, docs: List[Dict[str, Any]], top_k: int) -> List[Dict[str, Any]]:
        pairs = [[query, d["context"]] for d in docs]
        scores = self.model.predict(pairs, convert_to_numpy=True)
        for d, s in zip(docs, scores):
            d["relevance_score"] = float(s)
        docs.sort(key=lambda x: x["relevance_score"], reverse=True)
        return docs[:top_k]

class SearchEngine:
    def __init__(self, block_manager: Optional[BlockManager] = None, reranker: Optional[BertReranker] = None):
        self.bm = block_manager or BlockManager()
        self.reranker = reranker
    
    def _detect_temporal_query(self, query: str) -> bool:
        """날짜 관련 키워드가 있는지 감지"""
        temporal_keywords = [
            '최근', '어제', '오늘', '지난', '전에', '후에', '일전',
            'recent', 'today', 'yesterday', 'last', 'ago', 'before', 'after'
        ]
        query_lower = query.lower()
        return any(keyword in query_lower for keyword in temporal_keywords)
    
    def _apply_temporal_boost(self, blocks: List[Dict[str, Any]], weight: float = 0.3) -> List[Dict[str, Any]]:
        """최신 블록에 시간 기반 점수 부스팅 적용"""
        if not blocks:
            return blocks
        
        now = datetime.now()
        
        for block in blocks:
            try:
                # timestamp 파싱 (ISO 형식)
                timestamp_str = block.get('timestamp', '')
                if timestamp_str:
                    # ISO 형식에서 마이크로초 처리
                    if '.' in timestamp_str:
                        block_time = datetime.fromisoformat(timestamp_str)
                    else:
                        block_time = datetime.fromisoformat(timestamp_str + '.000000')
                    
                    # 시간 차이 계산 (일 단위)
                    days_ago = (now - block_time).total_seconds() / (24 * 3600)
                    
                    # 시간 점수 계산 (최근일수록 높음, 30일 기준 감쇠)
                    temporal_score = max(0.1, 1.0 - (days_ago / 30.0))
                else:
                    temporal_score = 0.1  # timestamp 없으면 최소값
                
                # 기존 relevance_score와 결합
                original_score = block.get('relevance_score', 0.5)
                
                # 최종 점수 = 기존점수*(1-weight) + 시간점수*weight
                block['final_score'] = original_score * (1 - weight) + temporal_score * weight
                block['temporal_score'] = temporal_score  # 디버깅용
                
            except (ValueError, TypeError) as e:
                # timestamp 파싱 실패시 기존 점수 유지
                logger.warning(f"Failed to parse timestamp for block: {e}")
                block['final_score'] = block.get('relevance_score', 0.5)
                block['temporal_score'] = 0.1
        
        # final_score 기준으로 정렬
        return sorted(blocks, key=lambda x: x.get('final_score', 0), reverse=True)

    def search(self, query: str, top_k: int = 5, temporal_boost: Optional[bool] = None, temporal_weight: float = 0.3) -> Dict[str, Any]:
        """Vector search → optional rerank → optional temporal boost. Returns blocks and latency metrics.
        
        Args:
            query: 검색 쿼리
            top_k: 반환할 결과 개수
            temporal_boost: 시간 부스팅 적용 여부. None이면 자동 감지 (날짜 키워드 없으면 적용)
            temporal_weight: 시간 점수 가중치 (0.0-1.0, 기본값 0.3)
        """
        t0 = time.perf_counter()
        emb = get_embedding(query)
        vec_time = time.perf_counter()
        candidate_blocks = self.bm.search_by_embedding(emb, top_k=top_k*3)
        search_time = time.perf_counter()
        
        # BERT 재랭킹 (기존 로직)
        if self.reranker is not None and candidate_blocks:
            candidate_blocks = self.reranker.rerank(query, candidate_blocks, top_k)
        rerank_time = time.perf_counter()
        
        # 시간 부스팅 적용 여부 결정
        if temporal_boost is None:
            # 자동 감지: 날짜 관련 키워드가 없으면 시간 부스팅 적용
            temporal_boost = not self._detect_temporal_query(query)
        
        # 시간 부스팅 적용
        if temporal_boost and candidate_blocks:
            candidate_blocks = self._apply_temporal_boost(candidate_blocks, temporal_weight)
        
        end_time = time.perf_counter()
        
        return {
            "blocks": candidate_blocks[:top_k],
            "timing": {
                "embed_ms": (vec_time - t0)*1000,
                "vector_ms": (search_time - vec_time)*1000,
                "rerank_ms": (rerank_time - search_time)*1000,
                "temporal_ms": (end_time - rerank_time)*1000,
            },
            "metadata": {
                "temporal_boost_applied": temporal_boost,
                "temporal_weight": temporal_weight if temporal_boost else 0.0,
                "query_has_date_keywords": self._detect_temporal_query(query)
            }
        } 