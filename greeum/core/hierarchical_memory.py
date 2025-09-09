"""
Hierarchical Memory System for Greeum v2.6.0

Integrates Working Memory, STM, and LTM layers with automated promotion,
intelligent routing, and unified access patterns.
"""

import time
import asyncio
from typing import List, Dict, Any, Optional, Union, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
from collections import deque

from .memory_layer import (
    MemoryLayerInterface, MemoryLayerType, MemoryPriority,
    MemoryItem, LayerTransferRequest, MemoryLayerManager,
    create_memory_item
)
from .working_memory import STMWorkingSet, MemorySlot, SlotType, SlotIntent
from .stm_layer import STMLayer
from .ltm_layer import LTMLayer
from .database_manager import DatabaseManager


class PromotionStrategy(Enum):
    """메모리 승격 전략"""
    IMMEDIATE = "immediate"        # 즉시 승격
    SCHEDULED = "scheduled"        # 예약된 승격
    THRESHOLD_BASED = "threshold"  # 임계값 기반
    AI_DRIVEN = "ai_driven"       # AI 판단 기반


@dataclass
class PromotionRule:
    """메모리 승격 규칙"""
    source_layer: MemoryLayerType
    target_layer: MemoryLayerType
    strategy: PromotionStrategy
    conditions: Dict[str, Any]
    priority_threshold: float = 0.5
    importance_threshold: float = 0.5
    age_threshold: int = 3600  # 초
    confidence_required: float = 0.7


class WorkingMemoryAdapter(MemoryLayerInterface):
    """Working Memory를 계층 인터페이스에 맞게 어댑팅"""
    
    def __init__(self, working_memory: STMWorkingSet = None):
        super().__init__(MemoryLayerType.WORKING)
        
        self.working_memory = working_memory or STMWorkingSet(
            capacity=10,
            ttl_seconds=1800  # 30분
        )
        
        # Working Memory 슬롯을 MemoryItem으로 매핑
        self.slot_to_memory: Dict[str, MemoryItem] = {}
        self.memory_to_slot: Dict[str, str] = {}
    
    def initialize(self) -> bool:
        """Working Memory 초기화"""
        try:
            # 기존 슬롯들을 MemoryItem으로 변환
            self._sync_from_working_memory()
            self._initialized = True
            return True
        except Exception as e:
            print(f"Working Memory initialization failed: {e}")
            return False
    
    def _sync_from_working_memory(self):
        """Working Memory의 슬롯들을 MemoryItem으로 동기화"""
        self.slot_to_memory.clear()
        self.memory_to_slot.clear()
        
        for slot in self.working_memory._queue:
            memory_item = self._slot_to_memory_item(slot)
            slot_id = id(slot)
            
            self.slot_to_memory[str(slot_id)] = memory_item
            self.memory_to_slot[memory_item.id] = str(slot_id)
    
    def _slot_to_memory_item(self, slot: MemorySlot) -> MemoryItem:
        """MemorySlot을 MemoryItem으로 변환"""
        # 슬롯 타입에 따른 우선순위 결정
        priority_mapping = {
            SlotType.ANCHOR: MemoryPriority.HIGH,
            SlotType.CONTEXT: MemoryPriority.MEDIUM,
            SlotType.BUFFER: MemoryPriority.LOW
        }
        
        return MemoryItem(
            id=f"working_{id(slot)}",
            content=slot.content,
            timestamp=slot.timestamp,
            layer=MemoryLayerType.WORKING,
            priority=priority_mapping.get(slot.slot_type, MemoryPriority.MEDIUM),
            metadata={
                'speaker': slot.speaker,
                'task_id': slot.task_id,
                'step_id': slot.step_id,
                'slot_type': slot.slot_type.value,
                'ltm_anchor_block': slot.ltm_anchor_block,
                'search_radius': slot.search_radius,
                **slot.metadata
            },
            keywords=[],  # Working Memory에서는 키워드 추출하지 않음
            tags=[],
            embedding=[],
            importance=slot.importance_score
        )
    
    def _memory_item_to_slot(self, memory_item: MemoryItem) -> MemorySlot:
        """MemoryItem을 MemorySlot으로 변환"""
        metadata = memory_item.metadata
        
        return MemorySlot(
            content=memory_item.content,
            timestamp=memory_item.timestamp,
            speaker=metadata.get('speaker', 'user'),
            task_id=metadata.get('task_id'),
            step_id=metadata.get('step_id'),
            slot_type=SlotType(metadata.get('slot_type', 'context')),
            ltm_anchor_block=metadata.get('ltm_anchor_block'),
            search_radius=metadata.get('search_radius', 5),
            importance_score=memory_item.importance,
            metadata={k: v for k, v in metadata.items() 
                     if k not in ['speaker', 'task_id', 'step_id', 'slot_type', 
                                'ltm_anchor_block', 'search_radius']}
        )
    
    def add_memory(self, memory_item: MemoryItem) -> str:
        """Working Memory에 메모리 추가"""
        try:
            slot = self._memory_item_to_slot(memory_item)
            
            # Working Memory에 추가 (기존 add 메서드 사용)
            self.working_memory.add(
                content=slot.content,
                speaker=slot.speaker,
                task_id=slot.task_id,
                step_id=slot.step_id,
                slot_type=slot.slot_type,
                ltm_anchor_block=slot.ltm_anchor_block,
                search_radius=slot.search_radius,
                importance_score=slot.importance_score,
                metadata=slot.metadata
            )
            
            # 매핑 업데이트
            slot_id = str(id(slot))
            self.slot_to_memory[slot_id] = memory_item
            self.memory_to_slot[memory_item.id] = slot_id
            
            return memory_item.id
            
        except Exception as e:
            print(f"Failed to add Working Memory: {e}")
            return ""
    
    def get_memory(self, memory_id: str) -> Optional[MemoryItem]:
        """Working Memory에서 특정 메모리 조회"""
        slot_id = self.memory_to_slot.get(memory_id)
        if not slot_id:
            return None
        
        memory_item = self.slot_to_memory.get(slot_id)
        if not memory_item:
            return None
        
        # 만료 확인
        if memory_item.timestamp + timedelta(seconds=self.working_memory.ttl_seconds) < datetime.utcnow():
            self._remove_expired_memory(memory_id)
            return None
        
        return memory_item
    
    def search_memories(self, query: str, limit: int = 10, 
                       filters: Dict[str, Any] = None) -> List[MemoryItem]:
        """Working Memory 검색"""
        if filters is None:
            filters = {}
        
        # 동기화 먼저 수행
        self._sync_from_working_memory()
        
        results = []
        query_lower = query.lower()
        
        for memory_item in self.slot_to_memory.values():
            # 만료 확인
            if memory_item.timestamp + timedelta(seconds=self.working_memory.ttl_seconds) < datetime.utcnow():
                continue
            
            # 슬롯 타입 필터 (먼저 확인)
            if 'slot_type' in filters:
                if memory_item.metadata.get('slot_type') != filters['slot_type']:
                    continue
            
            # 텍스트 검색 (단어별 분리 검색)
            content_lower = memory_item.content.lower()
            query_words = query_lower.split()
            
            # 모든 쿼리 단어가 콘텐츠에 포함되어 있는지 확인
            if all(word in content_lower for word in query_words):
                results.append(memory_item)
        
        # 중요도순 정렬
        results.sort(key=lambda x: x.importance, reverse=True)
        return results[:limit]
    
    def update_memory(self, memory_id: str, updates: Dict[str, Any]) -> bool:
        """Working Memory 업데이트"""
        memory_item = self.get_memory(memory_id)
        if not memory_item:
            return False
        
        try:
            # 업데이트 적용
            if 'content' in updates:
                memory_item.content = updates['content']
            if 'importance' in updates:
                memory_item.importance = updates['importance']
            if 'metadata' in updates:
                memory_item.metadata.update(updates['metadata'])
            
            # Working Memory에 반영
            slot_id = self.memory_to_slot[memory_id]
            slot = self._memory_item_to_slot(memory_item)
            
            # 기존 슬롯 찾아서 교체 (STMWorkingSet의 _queue 사용)
            for i, existing_slot in enumerate(self.working_memory._queue):
                if str(id(existing_slot)) == slot_id:
                    self.working_memory._queue[i] = slot
                    break
            
            # 매핑 업데이트
            self.slot_to_memory[slot_id] = memory_item
            
            return True
            
        except Exception as e:
            print(f"Failed to update Working Memory: {e}")
            return False
    
    def delete_memory(self, memory_id: str) -> bool:
        """Working Memory에서 메모리 삭제"""
        return self._remove_expired_memory(memory_id)
    
    def _remove_expired_memory(self, memory_id: str) -> bool:
        """만료된 메모리 제거"""
        slot_id = self.memory_to_slot.get(memory_id)
        if not slot_id:
            return False
        
        try:
            # Working Memory에서 슬롯 제거 (_queue에서)
            new_queue = deque([
                slot for slot in self.working_memory._queue
                if str(id(slot)) != slot_id
            ])
            self.working_memory._queue = new_queue
            
            # 매핑 제거
            del self.slot_to_memory[slot_id]
            del self.memory_to_slot[memory_id]
            
            return True
            
        except Exception as e:
            print(f"Failed to remove memory: {e}")
            return False
    
    def cleanup_expired(self) -> int:
        """만료된 메모리 정리"""
        expired_count = 0
        current_time = datetime.utcnow()
        expired_ids = []
        
        for memory_id, memory_item in list(self.slot_to_memory.items()):
            if memory_item.timestamp + timedelta(seconds=self.working_memory.ttl_seconds) < current_time:
                expired_ids.append(memory_item.id)
        
        for memory_id in expired_ids:
            if self._remove_expired_memory(memory_id):
                expired_count += 1
        
        return expired_count
    
    def get_layer_stats(self) -> Dict[str, Any]:
        """Working Memory 통계"""
        self._sync_from_working_memory()
        
        slot_type_counts = {}
        for memory_item in self.slot_to_memory.values():
            slot_type = memory_item.metadata.get('slot_type', 'context')
            slot_type_counts[slot_type] = slot_type_counts.get(slot_type, 0) + 1
        
        return {
            "layer_type": "Working Memory",
            "total_count": len(self.slot_to_memory),
            "max_capacity": self.working_memory.capacity,
            "ttl_seconds": self.working_memory.ttl_seconds,
            "slot_type_distribution": slot_type_counts,
            "average_importance": (
                sum(item.importance for item in self.slot_to_memory.values()) / 
                len(self.slot_to_memory) if self.slot_to_memory else 0
            )
        }
    
    def can_accept_transfer(self, transfer_request: LayerTransferRequest) -> bool:
        """Working Memory는 외부 전송을 받지 않음"""
        return False
    
    def transfer_to_layer(self, transfer_request: LayerTransferRequest) -> bool:
        """Working Memory는 STM으로만 전송 가능"""
        return transfer_request.target_layer == MemoryLayerType.STM


class HierarchicalMemorySystem:
    """계층적 메모리 시스템 통합 관리자"""
    
    def __init__(self, db_manager: DatabaseManager = None):
        self.db_manager = db_manager or DatabaseManager()
        
        # 계층 매니저
        self.layer_manager = MemoryLayerManager()
        
        # 각 계층 인스턴스
        self.working_memory_adapter = WorkingMemoryAdapter()
        self.stm_layer = STMLayer(self.db_manager)
        self.ltm_layer = LTMLayer(self.db_manager)
        
        # 승격 시스템
        self.promotion_rules: List[PromotionRule] = []
        self.auto_promotion_enabled = True
        self.promotion_interval = 300  # 5분마다 승격 검사
        self.last_promotion_check = datetime.now()
        
        # 통계
        self.stats = {
            "total_promotions": 0,
            "working_to_stm": 0,
            "stm_to_ltm": 0,
            "search_queries": 0,
            "cross_layer_searches": 0
        }
    
    def initialize(self) -> bool:
        """계층적 메모리 시스템 초기화"""
        try:
            # 계층 등록
            self.layer_manager.register_layer(self.working_memory_adapter)
            self.layer_manager.register_layer(self.stm_layer)
            self.layer_manager.register_layer(self.ltm_layer)
            
            # 기본 승격 규칙 설정
            self._setup_default_promotion_rules()
            
            print("🧠 Hierarchical Memory System initialized successfully!")
            print(f"   📋 Working Memory: {self.working_memory_adapter.get_layer_stats()['total_count']} slots")
            print(f"   ⚡ STM: {self.stm_layer.get_layer_stats()['total_count']} memories")  
            print(f"   🏛️  LTM: {self.ltm_layer.get_layer_stats()['total_blocks']} blocks")
            
            return True
            
        except Exception as e:
            print(f"Hierarchical Memory System initialization failed: {e}")
            return False
    
    def _setup_default_promotion_rules(self):
        """기본 승격 규칙 설정"""
        # Working Memory → STM
        self.promotion_rules.append(PromotionRule(
            source_layer=MemoryLayerType.WORKING,
            target_layer=MemoryLayerType.STM,
            strategy=PromotionStrategy.THRESHOLD_BASED,
            conditions={
                'min_content_length': 20,
                'min_age_seconds': 600,  # 10분
                'slot_types': ['context', 'anchor']
            },
            priority_threshold=0.6,
            importance_threshold=0.5
        ))
        
        # STM → LTM
        self.promotion_rules.append(PromotionRule(
            source_layer=MemoryLayerType.STM,
            target_layer=MemoryLayerType.LTM,
            strategy=PromotionStrategy.THRESHOLD_BASED,
            conditions={
                'min_age_seconds': 3600,  # 1시간
                'min_importance': 0.7,
                'has_keywords': True
            },
            priority_threshold=0.8,
            importance_threshold=0.7
        ))
    
    def add_memory(self, content: str, layer: MemoryLayerType = MemoryLayerType.WORKING,
                  priority: MemoryPriority = MemoryPriority.MEDIUM, **kwargs) -> str:
        """메모리 추가 (기본적으로 Working Memory부터 시작)"""
        memory_item = create_memory_item(content, layer, priority, **kwargs)
        
        target_layer = self.layer_manager.get_layer(layer)
        if not target_layer:
            return ""
        
        return target_layer.add_memory(memory_item)
    
    def get_memory(self, memory_id: str, 
                  preferred_layers: List[MemoryLayerType] = None) -> Optional[MemoryItem]:
        """메모리 조회 (계층 우선순위에 따라)"""
        if preferred_layers is None:
            preferred_layers = [MemoryLayerType.WORKING, MemoryLayerType.STM, MemoryLayerType.LTM]
        
        for layer_type in preferred_layers:
            layer = self.layer_manager.get_layer(layer_type)
            if layer:
                memory_item = layer.get_memory(memory_id)
                if memory_item:
                    return memory_item
        
        return None
    
    def search_memories(self, query: str, limit: int = 10, 
                       layer_filter: List[MemoryLayerType] = None,
                       **filters) -> List[MemoryItem]:
        """통합 메모리 검색"""
        self.stats["search_queries"] += 1
        
        if layer_filter:
            self.stats["cross_layer_searches"] += 1
            return self.layer_manager.get_unified_search_results(query, limit, layer_filter)
        else:
            # 모든 계층에서 검색
            return self.layer_manager.get_unified_search_results(query, limit)
    
    def promote_memory(self, memory_id: str, target_layer: MemoryLayerType,
                      reason: str = "Manual promotion") -> bool:
        """수동 메모리 승격"""
        # 현재 메모리 위치 찾기
        current_memory = None
        source_layer_type = None
        
        for layer_type in [MemoryLayerType.WORKING, MemoryLayerType.STM, MemoryLayerType.LTM]:
            layer = self.layer_manager.get_layer(layer_type)
            if layer:
                memory = layer.get_memory(memory_id)
                if memory:
                    current_memory = memory
                    source_layer_type = layer_type
                    break
        
        if not current_memory or not source_layer_type:
            return False
        
        # 전송 요청 생성
        transfer_request = LayerTransferRequest(
            source_layer=source_layer_type,
            target_layer=target_layer,
            memory_id=memory_id,
            reason=reason,
            confidence=1.0,
            metadata={"manual_promotion": True}
        )
        
        # 승격 실행
        success = self.layer_manager.transfer_memory(transfer_request)
        if success:
            self.stats["total_promotions"] += 1
            if source_layer_type == MemoryLayerType.WORKING and target_layer == MemoryLayerType.STM:
                self.stats["working_to_stm"] += 1
            elif source_layer_type == MemoryLayerType.STM and target_layer == MemoryLayerType.LTM:
                self.stats["stm_to_ltm"] += 1
        
        return success
    
    def run_auto_promotion(self) -> Dict[str, int]:
        """자동 승격 실행"""
        if not self.auto_promotion_enabled:
            return {"promoted": 0, "candidates": 0}
        
        # 시간 체크
        now = datetime.now()
        if (now - self.last_promotion_check).total_seconds() < self.promotion_interval:
            return {"promoted": 0, "candidates": 0}
        
        self.last_promotion_check = now
        
        promoted_count = 0
        candidate_count = 0
        
        # 각 승격 규칙 적용
        for rule in self.promotion_rules:
            source_layer = self.layer_manager.get_layer(rule.source_layer)
            if not source_layer:
                continue
            
            # 후보 메모리 찾기
            candidates = self._find_promotion_candidates(source_layer, rule)
            candidate_count += len(candidates)
            
            # 승격 실행
            for memory_item in candidates:
                transfer_request = LayerTransferRequest(
                    source_layer=rule.source_layer,
                    target_layer=rule.target_layer,
                    memory_id=memory_item.id,
                    reason=f"Auto promotion: {rule.strategy.value}",
                    confidence=rule.confidence_required
                )
                
                if self.layer_manager.transfer_memory(transfer_request):
                    promoted_count += 1
                    self.stats["total_promotions"] += 1
                    
                    if (rule.source_layer == MemoryLayerType.WORKING and 
                        rule.target_layer == MemoryLayerType.STM):
                        self.stats["working_to_stm"] += 1
                    elif (rule.source_layer == MemoryLayerType.STM and 
                          rule.target_layer == MemoryLayerType.LTM):
                        self.stats["stm_to_ltm"] += 1
        
        return {"promoted": promoted_count, "candidates": candidate_count}
    
    def _find_promotion_candidates(self, source_layer: MemoryLayerInterface, 
                                 rule: PromotionRule) -> List[MemoryItem]:
        """승격 후보 메모리 찾기"""
        candidates = []
        
        # 계층별 검색 (간단한 구현)
        if rule.source_layer == MemoryLayerType.WORKING:
            # Working Memory의 모든 슬롯 확인
            stats = source_layer.get_layer_stats()
            # 실제로는 source_layer.search_memories를 사용해야 함
            all_memories = source_layer.search_memories("", limit=100)
            
        elif rule.source_layer == MemoryLayerType.STM:
            # STM의 모든 메모리 확인
            all_memories = source_layer.search_memories("", limit=1000)
        else:
            return candidates
        
        # 규칙에 따른 필터링
        now = datetime.now()
        for memory_item in all_memories:
            if self._matches_promotion_rule(memory_item, rule, now):
                candidates.append(memory_item)
        
        return candidates
    
    def _matches_promotion_rule(self, memory_item: MemoryItem, 
                               rule: PromotionRule, current_time: datetime) -> bool:
        """메모리가 승격 규칙에 맞는지 확인"""
        # 기본 임계값 확인
        if memory_item.priority.value < rule.priority_threshold:
            return False
        
        if memory_item.importance < rule.importance_threshold:
            return False
        
        # 나이 확인
        age_seconds = (current_time - memory_item.timestamp).total_seconds()
        if age_seconds < rule.age_threshold:
            return False
        
        # 조건별 확인
        conditions = rule.conditions
        
        # 콘텐츠 길이
        if 'min_content_length' in conditions:
            if len(memory_item.content) < conditions['min_content_length']:
                return False
        
        # 키워드 존재
        if conditions.get('has_keywords', False):
            if not memory_item.keywords:
                return False
        
        # 슬롯 타입 (Working Memory용)
        if 'slot_types' in conditions and rule.source_layer == MemoryLayerType.WORKING:
            slot_type = memory_item.metadata.get('slot_type', 'context')
            if slot_type not in conditions['slot_types']:
                return False
        
        return True
    
    def get_system_overview(self) -> Dict[str, Any]:
        """전체 시스템 개요"""
        base_overview = self.layer_manager.get_system_overview()
        
        # 승격 통계 추가
        base_overview.update({
            "promotion_stats": self.stats.copy(),
            "auto_promotion_enabled": self.auto_promotion_enabled,
            "promotion_rules_count": len(self.promotion_rules),
            "last_promotion_check": self.last_promotion_check.isoformat()
        })
        
        return base_overview
    
    def cleanup_system(self) -> Dict[str, int]:
        """시스템 전체 정리"""
        cleanup_results = {}
        
        # 각 계층 정리
        for layer_type, layer in self.layer_manager.layers.items():
            cleaned = layer.cleanup_expired()
            cleanup_results[layer_type.value] = cleaned
        
        # 자동 승격 실행
        if self.auto_promotion_enabled:
            promotion_results = self.run_auto_promotion()
            cleanup_results["auto_promoted"] = promotion_results["promoted"]
        
        return cleanup_results
    
    def enable_auto_promotion(self, enabled: bool = True, interval: int = 300):
        """자동 승격 활성화/비활성화"""
        self.auto_promotion_enabled = enabled
        self.promotion_interval = interval
        print(f"Auto promotion {'enabled' if enabled else 'disabled'} (interval: {interval}s)")
    
    def add_promotion_rule(self, rule: PromotionRule):
        """승격 규칙 추가"""
        self.promotion_rules.append(rule)
    
    def get_related_memories(self, memory_id: str, max_results: int = 10) -> List[MemoryItem]:
        """관련 메모리 조회 (모든 계층에서)"""
        # LTM에서 관련 메모리 찾기 (액탄트 구조 기반)
        ltm_related = []
        if hasattr(self.ltm_layer, 'get_related_memories'):
            ltm_related = self.ltm_layer.get_related_memories(memory_id)
        
        # 다른 계층에서도 텍스트 유사도 기반 검색
        memory_item = self.get_memory(memory_id)
        if not memory_item:
            return ltm_related
        
        # 메모리 콘텐츠를 쿼리로 사용하여 유사한 메모리 검색
        similar_memories = self.search_memories(
            memory_item.content[:100],  # 첫 100자를 쿼리로 사용
            limit=max_results * 2
        )
        
        # 원본 제외하고 결합
        all_related = []
        seen_ids = set()
        
        for memory in ltm_related + similar_memories:
            if memory.id != memory_id and memory.id not in seen_ids:
                all_related.append(memory)
                seen_ids.add(memory.id)
        
        return all_related[:max_results]


# 편의 함수들
def create_hierarchical_memory_system(db_path: str = None) -> HierarchicalMemorySystem:
    """계층적 메모리 시스템 생성"""
    db_manager = DatabaseManager(db_path) if db_path else DatabaseManager()
    system = HierarchicalMemorySystem(db_manager)
    system.initialize()
    return system


def quick_add_memory(system: HierarchicalMemorySystem, content: str, 
                    importance: float = 0.5, **kwargs) -> str:
    """빠른 메모리 추가"""
    return system.add_memory(
        content=content,
        priority=MemoryPriority.MEDIUM,
        importance=importance,
        metadata=kwargs
    )