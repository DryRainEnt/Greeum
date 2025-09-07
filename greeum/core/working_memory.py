from __future__ import annotations

""" 
STMWorkingSet – 인간의 '작업 기억(working memory)'을 가볍게 모사하는 계층.

* 최근 N개의 메시지를 활성 상태로 유지(선입선출).
* TTL(초)과 capacity를 동시에 고려해 만료.
* 태스크 메타(task_id, step_id)를 기록해 멀티-에이전트 협업을 지원.
* 의존성 없는 경량 구조 – 고급 기능은 추후 확장.
"""

from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Deque, Dict, List, Optional, Any, Union
from enum import Enum

__all__ = ["STMWorkingSet", "MemorySlot", "AIContextualSlots", "SlotType", "SlotIntent"]


class SlotType(Enum):
    """슬롯 사용 유형"""
    CONTEXT = "context"        # 대화 맥락 저장
    ANCHOR = "anchor"          # LTM 앵커 포인트
    BUFFER = "buffer"          # 임시 버퍼
    
class SlotIntent(Enum):
    """AI 의도 분류"""
    CONTINUE_CONVERSATION = "continue_conversation"
    FREQUENT_REFERENCE = "frequent_reference"
    TEMPORARY_HOLD = "temporary_hold"
    CONTEXT_SWITCH = "context_switch"


@dataclass
class MemorySlot:
    """단일 작업 기억 원소"""
    content: str
    timestamp: datetime = field(default_factory=datetime.utcnow)
    speaker: str = "user"
    task_id: Optional[str] = None
    step_id: Optional[str] = None
    metadata: Dict[str, str] = field(default_factory=dict)
    # v2.5.1 확장: 슬롯 타입 및 앵커 정보
    slot_type: SlotType = SlotType.CONTEXT
    ltm_anchor_block: Optional[int] = None
    search_radius: int = 5
    importance_score: float = 0.5

    def is_expired(self, ttl_seconds: int) -> bool:
        return (datetime.utcnow() - self.timestamp) > timedelta(seconds=ttl_seconds)
        
    def is_ltm_anchor(self) -> bool:
        """LTM 앵커 슬롯인지 확인"""
        return self.slot_type == SlotType.ANCHOR and self.ltm_anchor_block is not None
        
    def matches_query(self, query: str) -> bool:
        """쿼리와의 매칭도 확인 (간단한 키워드 매칭)"""
        return query.lower() in self.content.lower()


class STMWorkingSet:
    """활성 메모리 슬롯 N개를 관리하는 경량 컨테이너 (legacy 호환성 유지)"""

    def __init__(self, capacity: int = 8, ttl_seconds: int = 600):
        if capacity <= 0:
            raise ValueError("capacity must be positive")
        self.capacity: int = capacity
        self.ttl_seconds: int = ttl_seconds
        self._queue: Deque[MemorySlot] = deque()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def add(self, content: str, **kwargs) -> MemorySlot:
        """새 작업 기억 추가. 만료/초과 슬롯을 제거한 후 push."""
        slot = MemorySlot(content=content, **kwargs)
        self._purge_expired()
        if len(self._queue) >= self.capacity:
            self._queue.popleft()
        self._queue.append(slot)
        return slot

    def get_recent(self, n: int | None = None) -> List[MemorySlot]:
        """최근 n개(기본 전체) 반환 (최신순)."""
        self._purge_expired()
        if n is None or n >= len(self._queue):
            return list(reversed(self._queue))
        return list(reversed(list(self._queue)[-n:]))

    def clear(self):
        self._queue.clear()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _purge_expired(self):
        """TTL 만료된 슬롯 제거"""
        while self._queue and self._queue[0].is_expired(self.ttl_seconds):
            self._queue.popleft()


class AIContextualSlots:
    """AI가 유연하게 활용하는 3-슬롯 시스템"""
    
    def __init__(self, ttl_seconds: int = 1800):  # 30분 기본 TTL
        self.ttl_seconds = ttl_seconds
        self.slots: Dict[str, Optional[MemorySlot]] = {
            'active': None,   # 현재 대화 맥락
            'anchor': None,   # LTM 앵커 포인트
            'buffer': None    # 임시/전환 버퍼
        }
        
    def ai_decide_usage(self, content: str, context: Dict[str, Any]) -> str:
        """AI가 상황에 따라 슬롯 용도 결정"""
        intent = self._analyze_intent(content, context)
        
        if intent == SlotIntent.CONTINUE_CONVERSATION:
            return self._use_as_context_cache(content, context)
        elif intent == SlotIntent.FREQUENT_REFERENCE:
            return self._use_as_ltm_anchor(content, context)
        elif intent == SlotIntent.TEMPORARY_HOLD:
            return self._use_as_buffer(content, context)
        else:
            return self._use_as_context_cache(content, context)
            
    def _analyze_intent(self, content: str, context: Dict[str, Any]) -> SlotIntent:
        """컨텐츠와 맥락 분석하여 의도 파악"""
        # 간단한 휴리스틱 - 향후 ML 모델로 교체 가능
        # 임시 보관 키워드 먼저 검사 (우선순위 높음)
        if any(keyword in content.lower() for keyword in ['임시', '잠깐', '나중에', '잠김']):
            return SlotIntent.TEMPORARY_HOLD
        elif any(keyword in content.lower() for keyword in ['기억', '저장', '보관', '참조']):
            return SlotIntent.FREQUENT_REFERENCE
        else:
            return SlotIntent.CONTINUE_CONVERSATION
            
    def _use_as_context_cache(self, content: str, context: Dict[str, Any]) -> str:
        """대화 맥락 저장용으로 active 슬롯 사용"""
        slot = MemorySlot(
            content=content,
            slot_type=SlotType.CONTEXT,
            metadata=context.get('metadata', {}),
            importance_score=0.7
        )
        self.slots['active'] = slot
        return 'active'
        
    def _use_as_ltm_anchor(self, content: str, context: Dict[str, Any]) -> str:
        """LTM 앵커 통로용으로 anchor 슬롯 사용"""
        ltm_block = context.get('ltm_block_id', None)
        slot = MemorySlot(
            content=content,
            slot_type=SlotType.ANCHOR,
            ltm_anchor_block=ltm_block,
            search_radius=context.get('search_radius', 5),
            metadata=context.get('metadata', {}),
            importance_score=0.9
        )
        self.slots['anchor'] = slot
        return 'anchor'
        
    def _use_as_buffer(self, content: str, context: Dict[str, Any]) -> str:
        """임시 버퍼용으로 buffer 슬롯 사용"""
        slot = MemorySlot(
            content=content,
            slot_type=SlotType.BUFFER,
            metadata=context.get('metadata', {}),
            importance_score=0.3
        )
        self.slots['buffer'] = slot
        return 'buffer'
        
    def get_slot(self, slot_name: str) -> Optional[MemorySlot]:
        """특정 슬롯 내용 조회"""
        if slot_name not in self.slots:
            return None
        slot = self.slots[slot_name]
        if slot and slot.is_expired(self.ttl_seconds):
            self.slots[slot_name] = None
            return None
        return slot
        
    def get_all_active_slots(self) -> Dict[str, MemorySlot]:
        """만료되지 않은 모든 활성 슬롯 조회"""
        active_slots = {}
        for name, slot in self.slots.items():
            if slot and not slot.is_expired(self.ttl_seconds):
                active_slots[name] = slot
        return active_slots
        
    def clear_slot(self, slot_name: str) -> bool:
        """특정 슬롯 비우기"""
        if slot_name in self.slots:
            self.slots[slot_name] = None
            return True
        return False
        
    def get_status(self) -> Dict[str, Any]:
        """슬롯 상태 정보 조회"""
        status = {}
        for name, slot in self.slots.items():
            if slot and not slot.is_expired(self.ttl_seconds):
                status[name] = {
                    'type': slot.slot_type.value,
                    'content_preview': slot.content[:100] + '...' if len(slot.content) > 100 else slot.content,
                    'timestamp': slot.timestamp.isoformat(),
                    'importance': slot.importance_score,
                    'is_anchor': slot.is_ltm_anchor(),
                    'anchor_block': slot.ltm_anchor_block
                }
            else:
                status[name] = None
        return status