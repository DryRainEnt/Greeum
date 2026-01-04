"""
STM Cache

MCP 클라이언트 측 로컬 STM 캐시입니다.
서버의 STM 정보를 로컬에 캐싱하여 빠른 컨텍스트 접근을 제공합니다.
"""

import json
import logging
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class STMCache:
    """
    로컬 STM 캐시

    슬롯별 블록 참조와 요약 정보를 로컬에 저장합니다.
    API 서버 부하를 줄이고 빠른 컨텍스트 접근을 제공합니다.
    """

    DEFAULT_CACHE_DIR = "~/.greeum/cache"
    CACHE_FILENAME = "stm_cache.json"
    MAX_BLOCKS_PER_SLOT = 20
    SUMMARY_THRESHOLD = 10  # 이 개수 이상일 때 요약 생성

    def __init__(
        self,
        cache_dir: Optional[str] = None,
        ttl_seconds: int = 3600,
    ):
        """
        Args:
            cache_dir: 캐시 저장 디렉토리
            ttl_seconds: 캐시 만료 시간 (초)
        """
        if cache_dir:
            self._cache_dir = Path(cache_dir).expanduser()
        else:
            self._cache_dir = Path(self.DEFAULT_CACHE_DIR).expanduser()

        self._cache_dir.mkdir(parents=True, exist_ok=True)
        self._cache_path = self._cache_dir / self.CACHE_FILENAME
        self._ttl_seconds = ttl_seconds

        # 슬롯 구조: A, B, C, ...
        self._slots: Dict[str, Dict[str, Any]] = {}
        self._last_updated: float = 0

        # 기존 캐시 로드
        self.load()

    @property
    def cache_path(self) -> Path:
        """캐시 파일 경로"""
        return self._cache_path

    @property
    def slots(self) -> Dict[str, Dict[str, Any]]:
        """슬롯 데이터 접근"""
        return self._slots

    def load(self) -> bool:
        """캐시 파일에서 로드"""
        try:
            if self._cache_path.exists():
                with open(self._cache_path, "r", encoding="utf-8") as f:
                    data = json.load(f)

                self._slots = data.get("slots", {})
                self._last_updated = data.get("last_updated", 0)

                # TTL 확인
                if time.time() - self._last_updated > self._ttl_seconds:
                    logger.info("STM cache expired, clearing")
                    self._slots = {}
                    return False

                logger.info(f"STM cache loaded: {len(self._slots)} slots")
                return True
        except Exception as e:
            logger.warning(f"Failed to load STM cache: {e}")

        return False

    def save(self) -> bool:
        """캐시 파일로 저장"""
        try:
            data = {
                "slots": self._slots,
                "last_updated": time.time(),
                "version": "1.0",
            }

            with open(self._cache_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            self._last_updated = data["last_updated"]
            logger.debug(f"STM cache saved to {self._cache_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to save STM cache: {e}")
            return False

    def add_block_reference(
        self,
        slot: str,
        block_index: int,
        content_preview: str,
        importance: float = 0.5,
    ) -> None:
        """
        슬롯에 블록 참조 추가

        Args:
            slot: 슬롯 이름 (A, B, C, ...)
            block_index: 블록 인덱스
            content_preview: 콘텐츠 미리보기 (처음 100자)
            importance: 중요도
        """
        if slot not in self._slots:
            self._slots[slot] = {
                "blocks": [],
                "summary": None,
                "created_at": datetime.now().isoformat(),
                "access_count": 0,
            }

        slot_data = self._slots[slot]

        # 중복 체크
        existing_indices = [b["block_index"] for b in slot_data["blocks"]]
        if block_index in existing_indices:
            return

        # 블록 참조 추가
        slot_data["blocks"].append({
            "block_index": block_index,
            "content_preview": content_preview[:100],
            "importance": importance,
            "added_at": datetime.now().isoformat(),
        })

        # 최대 개수 초과 시 오래된 것 제거
        if len(slot_data["blocks"]) > self.MAX_BLOCKS_PER_SLOT:
            slot_data["blocks"] = slot_data["blocks"][-self.MAX_BLOCKS_PER_SLOT:]

        # 요약 필요 여부 확인
        if len(slot_data["blocks"]) >= self.SUMMARY_THRESHOLD:
            slot_data["needs_summary"] = True

        slot_data["updated_at"] = datetime.now().isoformat()

    def get_slot(self, slot: str) -> Optional[Dict[str, Any]]:
        """슬롯 데이터 조회"""
        if slot in self._slots:
            self._slots[slot]["access_count"] += 1
            return self._slots[slot]
        return None

    def get_slot_summary(self, slot: str) -> Optional[str]:
        """슬롯 요약 조회"""
        slot_data = self.get_slot(slot)
        if slot_data:
            return slot_data.get("summary")
        return None

    def set_slot_summary(self, slot: str, summary: str) -> None:
        """슬롯 요약 설정"""
        if slot in self._slots:
            self._slots[slot]["summary"] = summary
            self._slots[slot]["needs_summary"] = False
            self._slots[slot]["summary_updated_at"] = datetime.now().isoformat()

    def get_context_prompt(self, slot: Optional[str] = None) -> str:
        """
        컨텍스트 프롬프트 생성

        현재 캐시된 STM 정보를 기반으로 LLM에 제공할 컨텍스트를 생성합니다.

        Args:
            slot: 특정 슬롯만 포함 (None이면 전체)

        Returns:
            컨텍스트 프롬프트 문자열
        """
        lines = ["[Current Memory Context]"]

        slots_to_include = [slot] if slot else list(self._slots.keys())

        for s in slots_to_include:
            slot_data = self._slots.get(s)
            if not slot_data:
                continue

            lines.append(f"\n## Slot {s}")

            # 요약이 있으면 요약 사용
            if slot_data.get("summary"):
                lines.append(f"Summary: {slot_data['summary']}")

            # 최근 블록 미리보기
            recent_blocks = slot_data.get("blocks", [])[-5:]  # 최근 5개
            if recent_blocks:
                lines.append("Recent memories:")
                for b in recent_blocks:
                    lines.append(f"  - #{b['block_index']}: {b['content_preview'][:50]}...")

        return "\n".join(lines)

    def generate_summary_prompt(self, slot: str) -> Optional[str]:
        """
        요약 생성을 위한 프롬프트 생성

        LLM에게 슬롯 요약을 요청할 때 사용할 프롬프트를 생성합니다.

        Args:
            slot: 슬롯 이름

        Returns:
            요약 요청 프롬프트 또는 None
        """
        slot_data = self._slots.get(slot)
        if not slot_data or not slot_data.get("needs_summary"):
            return None

        blocks = slot_data.get("blocks", [])
        if len(blocks) < self.SUMMARY_THRESHOLD:
            return None

        previews = [b["content_preview"] for b in blocks]
        content_list = "\n".join(f"- {p}" for p in previews)

        return f"""다음은 슬롯 {slot}에 저장된 기억들의 미리보기입니다:

{content_list}

이 기억들의 공통 주제와 핵심 내용을 2-3문장으로 요약해주세요.
요약은 나중에 관련 기억을 찾을 때 참고됩니다."""

    def clear_slot(self, slot: str) -> None:
        """슬롯 비우기"""
        if slot in self._slots:
            del self._slots[slot]
            logger.info(f"Cleared slot {slot}")

    def clear_all(self) -> None:
        """전체 캐시 비우기"""
        self._slots = {}
        self._last_updated = 0
        logger.info("Cleared all STM cache")

    def get_stats(self) -> Dict[str, Any]:
        """캐시 통계"""
        total_blocks = sum(
            len(s.get("blocks", [])) for s in self._slots.values()
        )

        return {
            "active_slots": len(self._slots),
            "total_cached_blocks": total_blocks,
            "slots_needing_summary": sum(
                1 for s in self._slots.values() if s.get("needs_summary")
            ),
            "cache_age_seconds": time.time() - self._last_updated if self._last_updated else 0,
            "ttl_seconds": self._ttl_seconds,
        }
