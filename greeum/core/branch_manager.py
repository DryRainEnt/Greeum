"""
Branch-based Memory Manager for Greeum v3.0.0
트리/브랜치 구조 기반 메모리 관리자
"""

import os
import json
import hashlib
import datetime
import uuid
from typing import List, Dict, Any, Optional, Tuple, Set
from dataclasses import dataclass, field
import numpy as np
from pathlib import Path
import logging
import time

from .stm_anchor_store import get_anchor_store

logger = logging.getLogger(__name__)

@dataclass
class BranchBlock:
    """브랜치 기반 메모리 블록"""
    id: str
    root: str  # 브랜치 루트 (프로젝트)
    before: Optional[str]  # 부모 (이전 블록)
    after: List[str] = field(default_factory=list)  # 자식들
    content: Dict[str, Any] = field(default_factory=dict)
    tags: Dict[str, Any] = field(default_factory=dict)  # actants, labels
    emb: Optional[List[float]] = None  # 임베딩 (선택)
    stats: Dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'root': self.root,
            'before': self.before,
            'after': self.after,
            'content': self.content,
            'tags': self.tags,
            'emb': self.emb,
            'stats': self.stats,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }

@dataclass
class BranchMeta:
    """브랜치 메타데이터"""
    root: str
    title: str = ""
    heads: Dict[str, str] = field(default_factory=dict)  # STM 슬롯 헤드 {"A": uuid, "B": uuid, "C": uuid}
    size: int = 0
    depth: int = 0
    
@dataclass 
class SearchResult:
    """검색 결과 with 메타데이터"""
    items: List[BranchBlock]
    meta: Dict[str, Any]  # search_type, depth_used, hops, slot, root

class BranchManager:
    """브랜치 기반 메모리 매니저 (PR#1 구현)"""
    
    # 초극적 최적화 설정값 (Phase 3 - Ultra-Aggressive)
    DEPTH_DEFAULT = 6      # 4→6: 50% 더 깊은 탐색
    K_DEFAULT = 20         # 12→20: 67% 더 많은 후보
    BLEACH_BETA = 0.1      # 0.15→0.1: 진부화 페널티 최소화
    NOVELTY_GAMMA_LOCAL = 0.5    # 0.4→0.5: 로컬 새로움 가중치 최대화
    NOVELTY_GAMMA_GLOBAL = 0.05
    SIMILARITY_THRESHOLD = 0.02  # 0.05→0.02: 매우 관대한 유사도 임계값
    MIN_SIMILARITY_SCORE = 0.1   # 최소 유사도 점수 (새로운)
    
    def __init__(self, db_manager=None):
        """브랜치 매니저 초기화"""
        self.db_manager = db_manager
        self.anchor_store = get_anchor_store()
        self.blocks: Dict[str, BranchBlock] = {}  # id -> block
        self.branches: Dict[str, BranchMeta] = {}  # root -> meta
        self.stm_slots = {"A": None, "B": None, "C": None}  # 슬롯 -> 헤드
        self.active_slot = "A"

        # Load persisted STM anchors if present
        for slot_name, slot_data in self.anchor_store.get_slots().items():
            if slot_name in self.stm_slots:
                self.stm_slots[slot_name] = slot_data.anchor_block
        
        # 전역 인덱스 초기화
        from .branch_global_index import GlobalIndex
        self.global_index = GlobalIndex()
        
        # 자동 머지 엔진 초기화
        from .branch_auto_merge import AutoMergeEngine
        self.auto_merge = AutoMergeEngine(self)
        
        # 메트릭 추적
        self.metrics = {
            'total_searches': 0,
            'local_hit_rate': 0.0,
            'avg_hops': 0.0,
            'fallback_rate': 0.0,
            'depth_used_distribution': {},
            'cache_hit_rate': 0.0,
            'cache_hits': 0
        }
        
        # 검색 결과 캐싱 (Phase 2 최적화)
        self.search_cache = {}
        self.cache_max_size = 100
        self.cache_ttl = 300  # 5분
        
        self._load_existing_data()

    def update_stm_slot(self, slot: str, block_hash: Optional[str]) -> None:
        if slot not in self.stm_slots:
            return
        self.stm_slots[slot] = block_hash
        if block_hash:
            self.anchor_store.upsert_slot(
                slot_name=slot,
                anchor_block=block_hash,
                topic_vec=None,
                summary="",
                last_seen=time.time(),
                hysteresis=0,
            )
        else:
            self.anchor_store.reset_slot(slot)
        
    def _load_existing_data(self):
        """기존 데이터 로드 (마이그레이션 대비)"""
        if self.db_manager:
            # TODO: 기존 GraphIndex 데이터를 브랜치 구조로 변환
            logger.info("Loading existing data for branch migration")
    
    def add_block(self, content: str, slot: Optional[str] = None, 
                  root: Optional[str] = None, tags: Optional[Dict] = None,
                  importance: float = 0.5) -> BranchBlock:
        """
        새 블록 추가 (on_save 알고리즘)
        
        Args:
            content: 저장할 내용
            slot: STM 슬롯 (A/B/C)
            root: 브랜치 루트 (없으면 현재 슬롯의 루트 사용)
            tags: 태그 (actants, labels)
            importance: 중요도
        
        Returns:
            생성된 BranchBlock
        """
        # 1) 활성 슬롯 결정
        active_slot = slot or self.active_slot
        head_id = self.stm_slots.get(active_slot)
        
        # 2) 부모 블록 결정
        if head_id and head_id in self.blocks:
            parent = self.blocks[head_id]
            use_root = root or parent.root
            before = head_id
        else:
            # 새 브랜치 시작
            use_root = root or str(uuid.uuid4())
            before = None
            
        # 3) 새 블록 생성
        new_block = BranchBlock(
            id=str(uuid.uuid4()),
            root=use_root,
            before=before,
            after=[],
            content={'text': content, 'normalized': self._normalize(content)},
            tags=tags or {},
            stats={'visit': 0, 'importance': importance}
        )
        
        # 4) 부모의 after에 추가
        if before and before in self.blocks:
            self.blocks[before].after.append(new_block.id)
            self.blocks[before].updated_at = time.time()
            
        # 5) 블록 저장
        self.blocks[new_block.id] = new_block
        
        # 6) 전역 인덱스에 추가
        if self.global_index:
            self.global_index.add_node(
                node_id=new_block.id,
                content=content,
                root=use_root,
                created_at=new_block.created_at
            )
        
        # 7) STM 헤드 업데이트
        self.update_stm_slot(active_slot, new_block.id)
        self.active_slot = active_slot
        
        # 8) 브랜치 메타 업데이트
        if use_root not in self.branches:
            self.branches[use_root] = BranchMeta(root=use_root)
        branch_meta = self.branches[use_root]
        branch_meta.heads[active_slot] = new_block.id
        branch_meta.size += 1
        branch_meta.depth = max(branch_meta.depth, self._calculate_depth(new_block))
        
        logger.info(f"Added block {new_block.id} to branch {use_root} at slot {active_slot}")
        
        # 9) 자동 머지 평가
        if self.auto_merge:
            proposals = self.auto_merge.evaluate_auto_merge()
            if proposals:
                logger.info(f"Auto-merge proposals: {len(proposals)}")
                # 첫 번째 제안을 dry-run으로 로그
                for proposal in proposals[:1]:  # 첫 번째만
                    result = self.auto_merge.apply_merge(proposal, dry_run=True)
                    logger.info(f"Merge proposal: {proposal.slot_i}+{proposal.slot_j} score={proposal.score:.3f}")
        
        return new_block
    
    def search(self, query: str, slot: Optional[str] = None,
               root: Optional[str] = None, depth: int = DEPTH_DEFAULT,
               k: int = K_DEFAULT, fallback: bool = True) -> SearchResult:
        """
        최적화된 DFS 로컬 우선 탐색 with 캐싱
        
        Args:
            query: 검색 쿼리
            slot: STM 슬롯 (없으면 최근 활성 슬롯)
            root: 브랜치 루트
            depth: DFS 깊이 제한
            k: 결과 개수
            fallback: 전역 점프 허용 여부
            
        Returns:
            SearchResult with items and meta
        """
        start_time = time.time()
        self.metrics['total_searches'] += 1
        
        # 캐시 키 생성
        cache_key = f"{query}:{slot}:{root}:{depth}:{k}"
        
        # 캐시 확인
        if cache_key in self.search_cache:
            cached_result, cache_time = self.search_cache[cache_key]
            if time.time() - cache_time < self.cache_ttl:
                self.metrics['cache_hits'] += 1
                self.metrics['cache_hit_rate'] = self.metrics['cache_hits'] / self.metrics['total_searches']
                # 캐시된 결과의 메타데이터 업데이트
                cached_result.meta['from_cache'] = True
                cached_result.meta['time_ms'] = (time.time() - start_time) * 1000
                return cached_result
        
        # 0) 엔트리 포인트 선택
        entry_id = self._choose_entry(slot, root)
        if not entry_id:
            return SearchResult(items=[], meta={'search_type': 'empty', 'hops': 0})
            
        # 1) DFS 로컬 탐색 (최적화된 매개변수)
        results, hops = self._dfs_search(entry_id, query, depth, k)
        
        # 메트릭 업데이트
        self.metrics['avg_hops'] = (self.metrics['avg_hops'] * (self.metrics['total_searches'] - 1) + hops) / self.metrics['total_searches']
        
        search_type = 'dfs_partial'
        
        # 로컬 히트 조건 개선: 충분한 결과 또는 높은 품질 결과
        local_hit_threshold = max(3, k // 3)  # 최소 3개 또는 요청한 결과의 1/3
        high_quality_results = sum(1 for block in results if self._calculate_score(query, block, local=True) > 0.5)
        
        if len(results) >= local_hit_threshold or high_quality_results >= 2:
            # 로컬 히트 성공!
            self.metrics['local_hit_rate'] = (self.metrics.get('local_hit_rate', 0) * (self.metrics['total_searches'] - 1) + 1) / self.metrics['total_searches']
            search_type = 'dfs_local'
        else:
            # 2) Fallback: 전역 점프 (개선된 로직)
            if fallback and hasattr(self, 'global_index') and self.global_index:
                logger.debug(f"Using global index fallback, current results: {len(results)}")
                entry_points = self.global_index.get_entry_points(query, limit=5)  # 더 많은 엔트리 포인트
                
                for entry_point in entry_points:
                    if entry_point in self.blocks and entry_point != entry_id:  # 중복 방지
                        additional_results, additional_hops = self._dfs_search(
                            entry_point, query, max(2, depth//2), k - len(results)  # 최소 깊이 보장
                        )
                        results.extend(additional_results)
                        hops += additional_hops
                        
                        if len(results) >= k:
                            search_type = 'global_assisted'
                            break
                            
                self.metrics['fallback_rate'] = (self.metrics.get('fallback_rate', 0) * (self.metrics['total_searches'] - 1) + 1) / self.metrics['total_searches']
        
        # 결과 생성
        final_results = results[:k]
        result = SearchResult(
            items=final_results,
            meta={
                'search_type': search_type,
                'depth_used': depth,
                'hops': hops,
                'slot': slot or self.active_slot,
                'root': self.blocks[entry_id].root if entry_id in self.blocks else None,
                'time_ms': (time.time() - start_time) * 1000,
                'from_cache': False,
                'results_found': len(final_results)
            }
        )
        
        # 캐시 저장 (유효한 결과만)
        if final_results:
            self._update_cache(cache_key, result)
            
        return result
    
    def _choose_entry(self, slot: Optional[str], root: Optional[str]) -> Optional[str]:
        """엔트리 포인트 선택"""
        if slot and slot in self.stm_slots:
            return self.stm_slots[slot]
        elif root and root in self.branches:
            # 루트의 첫 활성 헤드 사용
            for s in ["A", "B", "C"]:
                if s in self.branches[root].heads:
                    return self.branches[root].heads[s]
        else:
            # 최근 활성 슬롯
            return self.stm_slots.get(self.active_slot)
    
    def _dfs_search(self, start_id: str, query: str, 
                    max_depth: int, k: int) -> Tuple[List[BranchBlock], int]:
        """
        DFS 탐색 with 휴리스틱
        
        Returns:
            (results, hop_count)
        """
        if start_id not in self.blocks:
            return [], 0
            
        visited: Set[str] = set()
        results: List[Tuple[float, BranchBlock]] = []
        hop_count = 0
        
        def dfs(node_id: str, depth: int):
            nonlocal hop_count
            
            # 깊이 제한을 엄격히 적용 (>= 사용)
            if depth >= max_depth or node_id in visited:
                return
                
            visited.add(node_id)
            hop_count += 1
            
            if node_id not in self.blocks:
                return
                
            block = self.blocks[node_id]
            
            # 스코어 계산 (초관대한 임계값)
            score = self._calculate_score(query, block, local=True)
            if score >= self.MIN_SIMILARITY_SCORE:  # 최소 임계값으로 변경
                results.append((score, block))
                
            # 자식 탐색 (after) - 오버샘플링 확대
            for child_id in block.after:
                if len(results) >= k * 3:  # k*2 → k*3: 50% 더 많은 오버샘플링
                    break
                dfs(child_id, depth + 1)
                
            # 부모 탐색도 허용 (양방향 DFS)
            if block.before and depth < max_depth - 1:  # 부모 탐색 복원
                dfs(block.before, depth + 1)
                
            # 형제 탐색 (같은 부모의 다른 자식들)
            if block.before and block.before in self.blocks:
                parent = self.blocks[block.before]
                for sibling_id in parent.after:
                    if sibling_id != node_id and len(results) < k * 3:
                        dfs(sibling_id, depth + 1)
        
        dfs(start_id, 0)
        
        # 정렬 및 상위 K 선택
        results.sort(key=lambda x: x[0], reverse=True)
        return [block for _, block in results[:k]], hop_count
    
    def _calculate_score(self, query: str, block: BranchBlock, local: bool = True) -> float:
        """
        초극적 최적화된 스코어 계산 (Ultra-Aggressive Local Search)
        Score = w0 * cos(q,b) * (1 - β*Bleach(b)) * (1 + γ*Novelty(q,b|branch)) + recency + keyword_bonus + locality_bonus
        """
        # 코사인 유사도 (개선된 버전)
        query_words = set(query.lower().split())
        block_text = block.content.get('text', '').lower()
        block_words = set(block_text.split())
        
        if not query_words or not block_words:
            return self.MIN_SIMILARITY_SCORE if local else 0.0  # 로컬 검색시 최소 점수 보장
        
        # Jaccard 유사도 + 정확 매칭 보너스
        intersection = len(query_words & block_words)
        union = len(query_words | block_words)
        cos_sim = intersection / union if union > 0 else 0.0
        
        # 정확한 키워드 매칭 보너스 (강화)
        exact_matches = sum(1 for word in query_words if word in block_text)
        keyword_bonus = 0.4 * (exact_matches / len(query_words)) if query_words else 0.0  # 0.2→0.4
        
        # 부분 매칭 보너스 (새로운)
        partial_matches = sum(1 for word in query_words 
                            for block_word in block_words 
                            if word in block_word or block_word in word)
        partial_bonus = 0.2 * (partial_matches / len(query_words)) if query_words else 0.0
        
        # 초관대한 유사도 임계값 (거의 모든 블록 통과)
        if cos_sim < self.SIMILARITY_THRESHOLD:
            cos_sim = max(cos_sim * 0.8, self.MIN_SIMILARITY_SCORE)  # 페널티 최소화
        
        # Bleach (노출 진부화) - 최소화
        visit_count = block.stats.get('visit', 0)
        bleach = min(visit_count / 25.0, 0.5)  # 25회 이상, 최대 50% 페널티만
        
        # Novelty (새로움 보상) - 브랜치 로컬리티 고려
        gamma = self.NOVELTY_GAMMA_LOCAL if local else self.NOVELTY_GAMMA_GLOBAL
        # 브랜치 내 다양성 보상 (간이 구현)
        branch_diversity = 0.2 if local else 0.0  # 0.1→0.2
        novelty = branch_diversity
        
        # 기본 스코어
        base_score = cos_sim * (1 - self.BLEACH_BETA * bleach) * (1 + gamma * novelty)
        
        # 최근성 부스트 (대폭 강화)
        time_diff = time.time() - block.created_at
        recency_boost = 0.5 * np.exp(-time_diff / (2 * 24 * 3600))  # 2일 반감기, 가중치 대폭 증가
        
        # 브랜치 로컬리티 메가 보너스
        locality_bonus = 0.3 if local else 0.0  # 0.1→0.3
        
        # 로컬 검색시 추가 생존성 보장
        survival_bonus = 0.15 if local and (cos_sim > 0 or exact_matches > 0 or partial_matches > 0) else 0.0
        
        final_score = base_score + recency_boost + keyword_bonus + partial_bonus + locality_bonus + survival_bonus
        
        return max(final_score, self.MIN_SIMILARITY_SCORE if local else 0.0)
    
    def _update_cache(self, cache_key: str, result: SearchResult):
        """검색 결과 캐시 업데이트"""
        # 캐시 크기 제한
        if len(self.search_cache) >= self.cache_max_size:
            # 가장 오래된 항목 제거 (LRU)
            oldest_key = min(self.search_cache.keys(), 
                           key=lambda k: self.search_cache[k][1])
            del self.search_cache[oldest_key]
        
        self.search_cache[cache_key] = (result, time.time())
        
    def clear_cache(self):
        """캐시 전체 정리"""
        self.search_cache.clear()
        logger.info("Search cache cleared")
    
    def _calculate_depth(self, block: BranchBlock) -> int:
        """블록의 깊이 계산"""
        depth = 0
        current = block
        
        while current.before and depth < 100:  # 무한루프 방지
            depth += 1
            if current.before in self.blocks:
                current = self.blocks[current.before]
            else:
                break
                
        return depth
    
    def _normalize(self, text: str) -> str:
        """텍스트 정규화"""
        # TODO: 실제 정규화 로직
        return text.lower().strip()
    
    def get_metrics(self) -> Dict[str, Any]:
        """메트릭 반환"""
        return self.metrics.copy()
    
    def activate_slot(self, slot: str, block_id: str):
        """STM 슬롯 활성화"""
        if slot in self.stm_slots and block_id in self.blocks:
            self.update_stm_slot(slot, block_id)
            self.active_slot = slot
            
            # 브랜치 메타 업데이트
            block = self.blocks[block_id]
            if block.root in self.branches:
                self.branches[block.root].heads[slot] = block_id
                
            logger.info(f"Activated slot {slot} with block {block_id}")
