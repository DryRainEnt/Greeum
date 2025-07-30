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
from typing import Deque, Dict, List, Optional

__all__ = ["STMWorkingSet", "MemorySlot"]


@dataclass
class MemorySlot:
    """단일 작업 기억 원소"""
    content: str
    timestamp: datetime = field(default_factory=datetime.utcnow)
    speaker: str = "user"
    task_id: Optional[str] = None
    step_id: Optional[str] = None
    metadata: Dict[str, str] = field(default_factory=dict)

    def is_expired(self, ttl_seconds: int) -> bool:
        return (datetime.utcnow() - self.timestamp) > timedelta(seconds=ttl_seconds)


class STMWorkingSet:
    """활성 메모리 슬롯 N개를 관리하는 경량 컨테이너"""

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