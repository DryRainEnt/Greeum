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
    """AI가 유연하게 활용하는 3-슬롯 시스템 (싱글톤 패턴)"""
    
    _instance = None
    _initialized = False
    
    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self, ttl_seconds: int = 1800, enable_analytics: bool = True):  # 30분 기본 TTL
        # 이미 초기화되었으면 스킵
        if self._initialized:
            return
        self._initialized = True
        self.ttl_seconds = ttl_seconds
        self.enable_analytics = enable_analytics
        self.slots: Dict[str, Optional[MemorySlot]] = {
            'active': None,   # 현재 대화 맥락
            'anchor': None,   # LTM 앵커 포인트
            'buffer': None,   # 임시/전환 버퍼
            # v2.7.0: 명시적 슬롯 이름 지원
            'A': None,
            'B': None,
            'C': None,
            'D': None,
            'E': None
        }
        
        # Analytics 초기화 (선택적)
        self.analytics = None
        if enable_analytics:
            try:
                from .usage_analytics import UsageAnalytics
                self.analytics = UsageAnalytics()
            except ImportError:
                # Analytics가 없어도 정상 동작
                pass
        
    def ai_decide_usage(self, content: str, context: Dict[str, Any]) -> str:
        """AI가 상황에 따라 슬롯 용도 결정"""
        from datetime import datetime
        start_time = datetime.utcnow()
        
        intent = self._analyze_intent(content, context)
        
        if intent == SlotIntent.CONTINUE_CONVERSATION:
            slot_used = self._use_as_context_cache(content, context)
        elif intent == SlotIntent.FREQUENT_REFERENCE:
            slot_used = self._use_as_ltm_anchor(content, context)
        elif intent == SlotIntent.TEMPORARY_HOLD:
            slot_used = self._use_as_buffer(content, context)
        else:
            slot_used = self._use_as_context_cache(content, context)
        
        # Analytics 추적: 슬롯 작업 수행 + AI 의도 분석 업데이트
        if self.analytics:
            end_time = datetime.utcnow()
            processing_time = (end_time - start_time).total_seconds() * 1000  # milliseconds
            
            # 슬롯 작업 추적
            self.analytics.track_slots_operation(
                operation="ai_decide_usage",
                slot_type=slot_used,
                content=content[:100],  # 첫 100자만
                ai_intent=intent.value,
                ai_confidence=self._get_intent_confidence(content, intent),
                slot_allocation=slot_used,
                response_time_ms=processing_time,
                success=True
            )
            
            # AI 의도 분석 정확성 추적 (예측된 슬롯과 실제 사용된 슬롯 업데이트)
            self.analytics.track_ai_intent(
                input_content=content[:100],
                predicted_intent=intent.value,
                predicted_slot=slot_used,  # AI가 예측한 슬롯
                actual_slot_used=slot_used,  # 실제 사용된 슬롯 (현재는 동일)
                importance_score=self._get_intent_confidence(content, intent),
                context_metadata={"context_size": len(str(context)), "processing_time_ms": processing_time}
            )
        
        return slot_used
            
    def _analyze_intent(self, content: str, context: Dict[str, Any]) -> SlotIntent:
        """컨텐츠와 맥락 분석하여 의도 파악 (v2.5.2 향상된 버전)"""
        # v2.5.2: 실제 데이터 기반 20% 정확도 문제 해결
        # 멀티 레이어 분석: 키워드 + 컴텍스트 + 문법 패턴
        
        content_lower = content.lower()
        
        # Layer 1: 강한 시그널 키워드 (우선순위 최고)
        strong_temp_signals = ['임시로만', '잠깐만', '잠시만']  # "나중에" 제거, 복합패턴 처리로
        strong_ref_signals = ['기억해둘어', '저장해줘', '보관해둑', '기억해둬']  # "기억해둬" 추가
        
        if any(signal in content_lower for signal in strong_temp_signals):
            return SlotIntent.TEMPORARY_HOLD
        if any(signal in content_lower for signal in strong_ref_signals):
            return SlotIntent.FREQUENT_REFERENCE
            
        # Layer 2: 컴텍스트 기반 분석
        context_hints = self._analyze_context_hints(content, context)
        if context_hints:
            return context_hints
            
        # Layer 3: 문법 패턴 분석
        grammar_intent = self._analyze_grammar_patterns(content_lower)
        if grammar_intent:
            return grammar_intent
            
        # Layer 4: 기본 키워드 (기존 방식, 낮은 신뢰도)
        basic_temp_keywords = ['임시', '잠깐', '잠김']
        basic_ref_keywords = ['기억', '저장', '보관', '참조']
        
        if any(keyword in content_lower for keyword in basic_temp_keywords):
            return SlotIntent.TEMPORARY_HOLD
        elif any(keyword in content_lower for keyword in basic_ref_keywords):
            return SlotIntent.FREQUENT_REFERENCE
        else:
            return SlotIntent.CONTINUE_CONVERSATION
            
    def _analyze_context_hints(self, content: str, context: Dict[str, Any]) -> Optional[SlotIntent]:
        """컴텍스트 정보를 통한 의도 분석"""
        # 컴텍스트에 LTM 참조 정보가 있으면 FREQUENT_REFERENCE 강하게 시사
        if context.get('ltm_block_id') is not None:
            return SlotIntent.FREQUENT_REFERENCE
            
        # 메타데이터에 임시 언급이 있으면 TEMPORARY_HOLD
        metadata = context.get('metadata', {})
        if metadata.get('temp') or metadata.get('temporary'):
            return SlotIntent.TEMPORARY_HOLD
            
        # 대화 소스가 사용자 질문이나 요청이면 컴텍스트 우선
        source = context.get('source', '')
        if source in ['user_request', 'user_question']:
            return SlotIntent.CONTINUE_CONVERSATION
            
        return None
        
    def _analyze_grammar_patterns(self, content_lower: str) -> Optional[SlotIntent]:
        """문법 패턴을 통한 의도 분석 (v2.5.2 개선)"""
        
        # v2.5.2 수정: 복합 패턴 우선 처리 - "나중에 참조할 수 있게" 같은 경우
        if '나중에' in content_lower and any(ref_word in content_lower for ref_word in ['참조', '저장', '보관']):
            return SlotIntent.FREQUENT_REFERENCE  # 장기 보관 의도
            
        # v2.5.2 추가: "저장해둬 나중에 참조용으로" 패턴 처리
        if any(save_word in content_lower for save_word in ['저장해둬', '보관해둬']) and '참조' in content_lower:
            return SlotIntent.FREQUENT_REFERENCE
            
        # v2.5.2 수정: 명확한 기억/저장 명령어 패턴
        if any(pattern in content_lower for pattern in ['기억해둬', '기억해두', '기억해줘']):
            return SlotIntent.FREQUENT_REFERENCE
            
        # 명령법 패턴: ~해줘, ~해드, ~해두어  
        if any(pattern in content_lower for pattern in ['해줘', '해드', '해두어', '해들어']):
            # 구체적인 명령어에 따라 분류
            if any(cmd in content_lower for cmd in ['저장해줘', '보관해들어']):
                return SlotIntent.FREQUENT_REFERENCE
            elif any(cmd in content_lower for cmd in ['잠시만', '임시로']):
                return SlotIntent.TEMPORARY_HOLD
                
        # 의문문 패턴: 언제, 어떻게, 왜 - 일반적으로 계속 대화
        if any(pattern in content_lower for pattern in ['언제', '어떻게', '왜', '무엇', '누가']):
            return SlotIntent.CONTINUE_CONVERSATION
            
        # v2.5.2 수정: 단순 시간 표현 (복합 패턴이 이미 처리되지 않은 경우)
        if content_lower.startswith('나중에') or content_lower.startswith('이따가'):
            return SlotIntent.TEMPORARY_HOLD
            
        return None
        
    def _get_intent_confidence(self, content: str, intent: SlotIntent) -> float:
        """의도 예측 신뢰도 계산 (v2.5.2 향상된 버전)"""
        content_lower = content.lower()
        confidence = 0.5  # 기본 신뢰도
        
        # 강한 시그널 키워드 보너스
        if intent == SlotIntent.TEMPORARY_HOLD:
            strong_signals = ['임시로', '잠깐만', '나중에']
            strong_matches = sum(1 for signal in strong_signals if signal in content_lower)
            confidence += strong_matches * 0.3
            
            basic_matches = sum(1 for kw in ['임시', '잠깐'] if kw in content_lower)
            confidence += basic_matches * 0.1
            
        elif intent == SlotIntent.FREQUENT_REFERENCE:
            strong_signals = ['기억해둘어', '저장해줘', '보관해둑']
            strong_matches = sum(1 for signal in strong_signals if signal in content_lower)
            confidence += strong_matches * 0.3
            
            basic_matches = sum(1 for kw in ['기억', '저장', '참조'] if kw in content_lower)
            confidence += basic_matches * 0.1
            
        else:  # CONTINUE_CONVERSATION
            # 질문 패턴이 있으면 대화 신뢰도 상승
            question_patterns = ['언제', '어떻게', '왜', '무엇']
            question_matches = sum(1 for pattern in question_patterns if pattern in content_lower)
            confidence += question_matches * 0.2
            
        return min(0.95, confidence)  # 최대 95% 신뢰도
            
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
        from datetime import datetime
        start_time = datetime.utcnow()
        
        if slot_name not in self.slots:
            return None
        slot = self.slots[slot_name]
        
        # TTL 만료 검사
        if slot and slot.is_expired(self.ttl_seconds):
            self.slots[slot_name] = None
            
            # Analytics 추적: TTL 만료로 인한 슬롯 비우기
            if self.analytics:
                self.analytics.track_slots_operation(
                    operation="slot_expired",
                    slot_type=slot_name,
                    content=slot.content[:100] if slot else "",
                    response_time_ms=0,
                    success=True,
                    error_message=f"TTL expired ({self.ttl_seconds}s)"
                )
            
            return None
        
        # Analytics 추적: 성공적인 슬롯 조회
        if self.analytics and slot:
            end_time = datetime.utcnow()
            processing_time = (end_time - start_time).total_seconds() * 1000
            
            self.analytics.track_slots_operation(
                operation="get_slot",
                slot_type=slot.slot_type.value,
                content=slot.content[:100],
                ltm_anchor_block=slot.ltm_anchor_block,
                response_time_ms=processing_time,
                success=True
            )
        
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
            old_slot = self.slots[slot_name]
            self.slots[slot_name] = None
            
            # Analytics 추적: 수동 슬롯 비우기
            if self.analytics and old_slot:
                self.analytics.track_slots_operation(
                    operation="clear_slot",
                    slot_type=old_slot.slot_type.value,
                    content=old_slot.content[:100],
                    response_time_ms=0,
                    success=True,
                    error_message="manual_clear"
                )
            
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