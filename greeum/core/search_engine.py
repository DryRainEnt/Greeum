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
    def __init__(self, block_manager: Optional[BlockManager] = None, reranker: Optional[BertReranker] = None,
                 anchor_path: Optional[str] = None, graph_path: Optional[str] = None):
        self.bm = block_manager or BlockManager()
        self.reranker = reranker
        
        # Allow custom paths for testing
        self.anchor_path = anchor_path or "data/anchors.json"
        self.graph_path = graph_path or "data/graph_snapshot.jsonl"
    
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

    def search(self, query: str, top_k: int = 5, temporal_boost: Optional[bool] = None, temporal_weight: float = 0.3,
               slot: Optional[str] = None, radius: Optional[int] = None, fallback: bool = True) -> Dict[str, Any]:
        """Vector search → optional rerank → optional temporal boost. Returns blocks and latency metrics.
        
        Args:
            query: 검색 쿼리
            top_k: 반환할 결과 개수
            temporal_boost: 시간 부스팅 적용 여부. None이면 자동 감지 (날짜 키워드 없으면 적용)
            temporal_weight: 시간 점수 가중치 (0.0-1.0, 기본값 0.3)
            slot: 앵커 슬롯 (A/B/C) for localized search (M0: parameter only, no implementation)
            radius: 그래프 탐색 반경 (M0: parameter only, no implementation) 
            fallback: 국소 검색 실패시 기본 검색 사용 여부 (M0: parameter only, no implementation)
        """
        # M1: Implement localized search using anchor/graph system
        localized_blocks = None
        local_hit_rate = 0.0
        fallback_used = False
        avg_hops = 0
        
        # Standard search setup (always needed for timing and fallback)
        t0 = time.perf_counter()
        emb = get_embedding(query)
        vec_time = time.perf_counter()
        
        if slot is not None:
            try:
                # Attempt localized search using anchors and graph
                localized_blocks, local_metrics = self._localized_search(
                    query, emb, slot, radius, top_k
                )
                local_hit_rate = local_metrics.get('hit_rate', 0.0)
                avg_hops = local_metrics.get('avg_hops', 0)
                
                logger.debug(f"Localized search: {len(localized_blocks) if localized_blocks else 0} results, hit_rate={local_hit_rate:.2f}")
                
            except Exception as e:
                logger.warning(f"Localized search failed: {e}")
                localized_blocks = None
        
        # Determine if we should use localized results or fallback
        if localized_blocks and len(localized_blocks) >= max(1, top_k // 2):
            # Use localized results if we got sufficient hits
            candidate_blocks = localized_blocks[:top_k*3]
            fallback_used = False
        elif fallback:
            # Fallback to standard search
            from . import metrics
            metrics.record_fallback_search()  # Record fallback metric
            candidate_blocks = self.bm.search_by_embedding(emb, top_k=top_k*3)
            fallback_used = True
        else:
            # No fallback allowed, return empty or partial results
            candidate_blocks = localized_blocks[:top_k*3] if localized_blocks else []
            fallback_used = False
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
                "query_has_date_keywords": self._detect_temporal_query(query),
                # M1: New localized search metrics
                "localized_search_used": slot is not None,
                "fallback_used": fallback_used,
                "local_hit_rate": local_hit_rate,
                "avg_hops": avg_hops,
                "anchor_slot": slot
            }
        } 

    def _localized_search(self, query: str, query_emb: list, slot: str, radius: int = None, top_k: int = 5):
        """
        Perform localized search using anchor-based graph traversal.
        
        Returns:
            Tuple[List[Dict], Dict]: (blocks, metrics)
        """
        from greeum.anchors import AnchorManager
        from greeum.graph import GraphIndex
        from pathlib import Path
        import numpy as np
        
        # Load anchor manager and graph index
        try:
            anchor_path = Path(self.anchor_path)
            graph_path = Path(self.graph_path)
            
            if not anchor_path.exists():
                raise FileNotFoundError(f"Anchor file not found: {anchor_path}")
            
            anchor_manager = AnchorManager(anchor_path)
            graph_index = GraphIndex()
            
            # Only load graph if it exists, otherwise create empty
            if graph_path.exists():
                if not graph_index.load_snapshot(graph_path):
                    logger.warning("Failed to load graph snapshot, using empty graph")
            else:
                logger.debug("Graph file not found, using empty graph")
            
        except Exception as e:
            raise RuntimeError(f"Failed to load anchor/graph system: {e}")
        
        # Get anchor information
        slot_info = anchor_manager.get_slot_info(slot)
        if not slot_info or not slot_info['anchor_block_id']:
            raise ValueError(f"Slot {slot} is not initialized")
        
        anchor_block_id = slot_info['anchor_block_id']
        hop_budget = radius if radius is not None else slot_info['hop_budget']
        
        # Define goal function for beam search
        query_vec = np.array(query_emb)
        def is_relevant_block(block_id: str) -> bool:
            try:
                # Get block from database
                block_data = self.bm.db_manager.get_block_by_index(int(block_id))
                if not block_data:
                    return False
                
                # Check similarity with query
                block_emb = np.array(block_data['embedding'])
                similarity = np.dot(query_vec, block_emb) / (
                    np.linalg.norm(query_vec) * np.linalg.norm(block_emb)
                )
                
                # Threshold for relevance (based on actual data analysis: 90th percentile)
                return similarity > 0.1
                
            except Exception:
                return False
        
        # Perform beam search
        start_time = time.perf_counter()
        beam_width = 32
        from . import metrics
        metrics.update_beam_width(beam_width)  # Record current beam width
        
        relevant_block_ids = graph_index.beam_search(
            start=anchor_block_id,
            is_goal=is_relevant_block,
            beam=beam_width,
            max_hop=hop_budget
        )
        search_time = time.perf_counter() - start_time
        
        # Retrieve actual blocks
        blocks = []
        for block_id in relevant_block_ids[:top_k*3]:
            try:
                block_data = self.bm.db_manager.get_block_by_index(int(block_id))
                if block_data:
                    blocks.append(block_data)
            except Exception:
                continue
        
        # Calculate metrics
        total_searched = len(relevant_block_ids)
        hit_rate = len(blocks) / max(1, total_searched) if total_searched > 0 else 0.0
        hit = len(blocks) > 0
        
        # Record metrics
        from . import metrics
        metrics.record_local_search(hit=hit, hops=hop_budget)
        
        # Update anchor position if we found good results
        if blocks and not slot_info['pinned']:
            best_block_id = str(blocks[0]['block_index'])
            anchor_manager.move_anchor(slot, best_block_id, query_vec)
        
        metrics = {
            'hit_rate': hit_rate,
            'avg_hops': min(hop_budget, 2),  # Estimate based on hop budget
            'search_time_ms': search_time * 1000,
            'total_searched': total_searched,
            'anchor_moved': len(blocks) > 0 and not slot_info['pinned']
        }
        
        return blocks, metrics
