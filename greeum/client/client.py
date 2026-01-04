"""
Greeum Client

고수준 클라이언트 인터페이스입니다.
API 모드와 직접 모드를 투명하게 전환합니다.
"""

import logging
import os
from typing import Any, Dict, List, Optional

from greeum.client.http_client import GreeumHTTPClient
from greeum.client.stm_cache import STMCache

logger = logging.getLogger(__name__)


class GreeumClient:
    """
    Greeum 통합 클라이언트

    API 서버 사용 가능 시 HTTP 통신, 불가능 시 직접 모드로 폴백합니다.
    """

    def __init__(
        self,
        api_url: Optional[str] = None,
        api_key: Optional[str] = None,
        use_api: Optional[bool] = None,
        fallback_to_direct: bool = False,
        cache_dir: Optional[str] = None,
    ):
        """
        Args:
            api_url: API 서버 URL (우선순위: 파라미터 > 환경변수 > Config 파일)
            api_key: API 인증 키 (우선순위: 파라미터 > 환경변수 > Config 파일)
            use_api: API 모드 사용 여부 (우선순위: 파라미터 > 환경변수 > Config 파일)
            fallback_to_direct: API 실패 시 직접 모드 폴백 여부 (기본: False - 명시적 실패)
            cache_dir: STM 캐시 저장 경로
        """
        # Config 파일에서 원격 설정 로드
        remote_config = self._load_remote_config()

        # API URL 결정 (우선순위: 파라미터 > 환경변수 > Config 파일)
        self._api_url = (
            api_url or
            os.environ.get("GREEUM_API_URL") or
            (remote_config.server_url if remote_config else None) or
            "http://localhost:8400"
        )

        # API Key 결정 (우선순위: 파라미터 > 환경변수 > Config 파일)
        self._api_key = (
            api_key or
            os.environ.get("GREEUM_API_KEY") or
            (remote_config.api_key if remote_config else None)
        )

        # use_api 결정 (우선순위: 파라미터 > 환경변수 > Config 파일)
        use_api_env = os.environ.get("GREEUM_USE_API", "").lower()
        if use_api is not None:
            self._use_api = use_api
        elif use_api_env:
            self._use_api = use_api_env in ("true", "1", "yes")
        elif remote_config and remote_config.enabled:
            self._use_api = True
        else:
            self._use_api = False

        self._fallback_to_direct = fallback_to_direct
        self._http_client: Optional[GreeumHTTPClient] = None
        self._stm_cache = STMCache(cache_dir=cache_dir)

        # 직접 모드용 컴포넌트 (lazy init)
        self._direct_components: Optional[Dict[str, Any]] = None
        self._api_available: Optional[bool] = None

        logger.info(
            f"GreeumClient initialized: use_api={self._use_api}, "
            f"api_url={self._api_url}, fallback={self._fallback_to_direct}"
        )

    def _load_remote_config(self):
        """Config 파일에서 원격 설정 로드"""
        try:
            from greeum.config_store import get_remote_config
            return get_remote_config()
        except Exception:
            return None

    def _get_http_client(self) -> GreeumHTTPClient:
        """HTTP 클라이언트 lazy 초기화"""
        if self._http_client is None:
            self._http_client = GreeumHTTPClient(
                base_url=self._api_url,
                api_key=self._api_key,
            )
        return self._http_client

    def _check_api_available(self) -> bool:
        """API 서버 사용 가능 여부 확인 (캐시됨)"""
        if self._api_available is None:
            self._api_available = self._get_http_client().is_available()
            if not self._api_available:
                logger.warning(
                    f"API server not available at {self._api_url}"
                )
        return self._api_available

    def _reset_api_check(self) -> None:
        """API 가용성 캐시 초기화 (재확인 필요 시)"""
        self._api_available = None

    def _init_direct_components(self) -> Dict[str, Any]:
        """직접 모드용 Greeum 컴포넌트 초기화"""
        if self._direct_components is None:
            try:
                from greeum.core import DatabaseManager
                from greeum.core.block_manager import BlockManager
                from greeum.core.stm_manager import STMManager
                from greeum.core.duplicate_detector import DuplicateDetector
                from greeum.core.quality_validator import QualityValidator

                db_manager = DatabaseManager()
                self._direct_components = {
                    "db_manager": db_manager,
                    "block_manager": BlockManager(db_manager),
                    "stm_manager": STMManager(db_manager),
                    "duplicate_detector": DuplicateDetector(db_manager),
                    "quality_validator": QualityValidator(),
                }
                logger.info("Direct mode components initialized")
            except ImportError as e:
                logger.error(f"Failed to import Greeum components: {e}")
                raise
        return self._direct_components

    def _should_use_api(self) -> bool:
        """API 모드 사용 여부 결정"""
        if not self._use_api:
            return False

        if self._check_api_available():
            return True

        if self._fallback_to_direct:
            logger.warning("API unavailable, falling back to direct mode")
            return False

        raise ConnectionError(
            f"API 서버에 연결할 수 없습니다: {self._api_url}\n"
            f"API 서버가 실행 중인지 확인하거나, 직접 모드를 사용하려면 "
            f"GREEUM_USE_API=false로 설정하세요."
        )

    def add_memory(
        self,
        content: str,
        importance: float = 0.5,
        tags: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        기억 추가

        Args:
            content: 기억 내용
            importance: 중요도 (0.0-1.0)
            tags: 태그 목록

        Returns:
            추가 결과 (success, block_index, storage, etc.)
        """
        if self._should_use_api():
            result = self._get_http_client().add_memory(
                content=content,
                importance=importance,
                tags=tags,
            )
            # STM 캐시에 참조 추가
            if result.get("success"):
                slot = result.get("branch_id", "A")  # 기본 슬롯
                self._stm_cache.add_block_reference(
                    slot=slot,
                    block_index=result.get("block_index", -1),
                    content_preview=content[:100],
                )
            return result

        # 직접 모드
        return self._add_memory_direct(content, importance, tags)

    def _add_memory_direct(
        self,
        content: str,
        importance: float,
        tags: Optional[List[str]],
    ) -> Dict[str, Any]:
        """직접 모드로 기억 추가"""
        components = self._init_direct_components()

        # 중복 검사
        dup_result = components["duplicate_detector"].check_duplicate(content)
        if dup_result.get("is_duplicate"):
            return {
                "success": False,
                "block_index": -1,
                "storage": "LTM",
                "quality_score": 0.0,
                "duplicate_check": "failed",
                "suggestions": [
                    f"Similar to block #{dup_result.get('similar_memories', [{}])[0].get('block_index', 'unknown')}"
                ],
            }

        # 품질 검증
        quality_result = components["quality_validator"].validate_memory_quality(
            content, importance
        )

        # 콘텐츠 처리
        try:
            from greeum.text_utils import process_user_input
            processed = process_user_input(content)
            keywords = processed.get("keywords", [])
            embedding = processed.get("embedding", [])
        except Exception as e:
            logger.warning(f"Failed to process content: {e}")
            keywords = []
            embedding = []

        # 블록 추가
        block_data = components["block_manager"].add_block(
            context=content,
            keywords=keywords,
            tags=tags or [],
            embedding=embedding,
            importance=importance,
        )

        return {
            "success": True,
            "block_index": block_data.get("block_index", -1) if block_data else -1,
            "branch_id": block_data.get("branch_id") if block_data else None,
            "storage": "LTM",
            "quality_score": quality_result.get("quality_score", 0.0),
            "duplicate_check": "passed",
            "suggestions": quality_result.get("suggestions", []),
        }

    def search(
        self,
        query: str,
        limit: int = 5,
        slot: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        기억 검색

        Args:
            query: 검색 쿼리
            limit: 최대 결과 수
            slot: STM 슬롯 필터

        Returns:
            검색 결과 (results, search_stats)
        """
        if self._should_use_api():
            return self._get_http_client().search(
                query=query,
                limit=limit,
                slot=slot,
            )

        # 직접 모드
        return self._search_direct(query, limit)

    def _search_direct(self, query: str, limit: int) -> Dict[str, Any]:
        """직접 모드로 검색"""
        import time
        from datetime import datetime

        components = self._init_direct_components()
        start_time = time.time()

        results = components["block_manager"].search(query, limit=limit)
        elapsed_ms = (time.time() - start_time) * 1000

        formatted_results = []
        for r in results:
            formatted_results.append({
                "block_index": r.get("block_index", 0),
                "content": r.get("context", ""),
                "timestamp": datetime.fromisoformat(
                    r.get("timestamp", datetime.now().isoformat())
                ),
                "similarity": r.get("similarity", 0.0),
                "branch_id": r.get("branch_id"),
                "importance": r.get("importance", 0.5),
            })

        return {
            "results": formatted_results,
            "search_stats": {
                "branches_searched": 1,
                "blocks_scanned": len(results),
                "elapsed_ms": elapsed_ms,
            },
        }

    def get_stats(self) -> Dict[str, Any]:
        """통계 조회"""
        if self._should_use_api():
            return self._get_http_client().get_stats()

        # 직접 모드
        components = self._init_direct_components()

        try:
            db_manager = components["db_manager"]
            if hasattr(db_manager, "count_blocks"):
                total_blocks = db_manager.count_blocks()
            elif hasattr(db_manager, "get_last_block_info"):
                last_info = db_manager.get_last_block_info()
                total_blocks = (last_info.get("block_index", -1) + 1) if last_info else 0
            else:
                total_blocks = 0
        except Exception:
            total_blocks = 0

        try:
            stm_stats = components["stm_manager"].get_stats()
        except Exception:
            stm_stats = {}

        return {
            "total_blocks": total_blocks,
            "active_branches": stm_stats.get("active_slots", 0),
            "stm_slots": stm_stats,
            "mode": "direct",
        }

    def get_stm_cache(self) -> STMCache:
        """로컬 STM 캐시 접근"""
        return self._stm_cache

    def close(self) -> None:
        """리소스 정리"""
        if self._http_client:
            self._http_client.close()
        self._stm_cache.save()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
