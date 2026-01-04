"""
Greeum HTTP Client

API 서버와 통신하는 저수준 HTTP 클라이언트입니다.
재시도 로직, 타임아웃, 에러 핸들링을 담당합니다.
"""

import logging
import time
from typing import Any, Dict, Optional
from urllib.parse import urljoin

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logger = logging.getLogger(__name__)


class GreeumHTTPClient:
    """Greeum API 서버와 통신하는 HTTP 클라이언트"""

    DEFAULT_TIMEOUT = 30  # seconds
    DEFAULT_RETRIES = 3
    DEFAULT_BACKOFF = 0.5

    def __init__(
        self,
        base_url: str = "http://localhost:8400",
        api_key: Optional[str] = None,
        timeout: int = DEFAULT_TIMEOUT,
        retries: int = DEFAULT_RETRIES,
        backoff_factor: float = DEFAULT_BACKOFF,
    ):
        """
        Args:
            base_url: API 서버 기본 URL
            api_key: API 인증 키 (X-API-Key 헤더)
            timeout: 요청 타임아웃 (초)
            retries: 재시도 횟수
            backoff_factor: 재시도 간격 계수
        """
        self.base_url = base_url.rstrip("/")
        self._api_key = api_key
        self.timeout = timeout
        self._session: Optional[requests.Session] = None
        self._retries = retries
        self._backoff_factor = backoff_factor

    def _get_session(self) -> requests.Session:
        """재시도 로직이 설정된 세션 반환"""
        if self._session is None:
            self._session = requests.Session()

            # API Key 헤더 설정
            if self._api_key:
                self._session.headers["X-API-Key"] = self._api_key

            retry_strategy = Retry(
                total=self._retries,
                backoff_factor=self._backoff_factor,
                status_forcelist=[429, 500, 502, 503, 504],
                allowed_methods=["HEAD", "GET", "POST", "PUT", "DELETE"],
            )

            adapter = HTTPAdapter(max_retries=retry_strategy)
            self._session.mount("http://", adapter)
            self._session.mount("https://", adapter)

        return self._session

    def set_api_key(self, api_key: str) -> None:
        """API 키 동적 설정 (기존 세션 재생성)"""
        self._api_key = api_key
        if self._session:
            self._session.close()
            self._session = None

    def _make_url(self, endpoint: str) -> str:
        """전체 URL 생성"""
        return urljoin(self.base_url + "/", endpoint.lstrip("/"))

    def health_check(self) -> Dict[str, Any]:
        """헬스체크 수행"""
        try:
            response = self._get_session().get(
                self._make_url("/health"),
                timeout=5,  # 헬스체크는 짧은 타임아웃
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.warning(f"Health check failed: {e}")
            return {"status": "unhealthy", "error": str(e)}

    def is_available(self) -> bool:
        """API 서버 사용 가능 여부 확인"""
        result = self.health_check()
        return result.get("status") == "healthy"

    def add_memory(
        self,
        content: str,
        importance: float = 0.5,
        tags: Optional[list] = None,
    ) -> Dict[str, Any]:
        """기억 추가"""
        payload = {
            "content": content,
            "importance": importance,
        }
        if tags:
            payload["tags"] = tags

        try:
            response = self._get_session().post(
                self._make_url("/memory"),
                json=payload,
                timeout=self.timeout,
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f"Failed to add memory: {e}")
            raise ConnectionError(f"API request failed: {e}") from e

    def get_memory(self, block_id: int) -> Optional[Dict[str, Any]]:
        """특정 기억 조회"""
        try:
            response = self._get_session().get(
                self._make_url(f"/memory/{block_id}"),
                timeout=self.timeout,
            )
            if response.status_code == 404:
                return None
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f"Failed to get memory {block_id}: {e}")
            raise ConnectionError(f"API request failed: {e}") from e

    def search(
        self,
        query: str,
        limit: int = 5,
        slot: Optional[str] = None,
    ) -> Dict[str, Any]:
        """기억 검색"""
        payload = {
            "query": query,
            "limit": limit,
        }
        if slot:
            payload["slot"] = slot

        try:
            response = self._get_session().post(
                self._make_url("/search"),
                json=payload,
                timeout=self.timeout,
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f"Failed to search: {e}")
            raise ConnectionError(f"API request failed: {e}") from e

    def get_stats(self) -> Dict[str, Any]:
        """통계 조회"""
        try:
            response = self._get_session().get(
                self._make_url("/stats"),
                timeout=self.timeout,
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f"Failed to get stats: {e}")
            raise ConnectionError(f"API request failed: {e}") from e

    def close(self) -> None:
        """세션 종료"""
        if self._session:
            self._session.close()
            self._session = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
