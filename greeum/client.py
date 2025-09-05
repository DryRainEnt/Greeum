"""
Greeum API 클라이언트

이 모듈은 Greeum API 서버와의 통신을 위한 클라이언트 클래스를 제공합니다.
"""

import requests
import json
import time
import logging
from requests.exceptions import RequestException, ConnectionError, Timeout, HTTPError
from typing import Dict, List, Any, Optional, Union, Callable

# 로거 설정
logger = logging.getLogger("greeum.client")

class ClientError(Exception):
    """Greeum 클라이언트 예외 기본 클래스"""
    pass

class ConnectionFailedError(ClientError):
    """서버 연결 실패 예외"""
    pass

class AuthenticationError(ClientError):
    """API 인증 실패 예외 (401, 403 등)"""
    pass

class APIError(ClientError):
    """API 오류 응답 예외"""
    def __init__(self, status_code: int, message: str, response: Optional[Dict[str, Any]] = None):
        self.status_code = status_code
        self.response = response
        super().__init__(f"API 오류 (코드: {status_code}): {message}")

class RequestTimeoutError(ClientError):
    """요청 타임아웃 예외"""
    pass

class MemoryClient:
    """Greeum API 클라이언트"""
    
    def __init__(self, base_url: str = "http://localhost:8000", 
                 proxies: Optional[Dict[str, str]] = None, 
                 timeout: int = 30,
                 max_retries: int = 3,
                 retry_delay: float = 1.0,
                 auth_token: Optional[str] = None):
        """
        API 클라이언트 초기화
        
        Args:
            base_url: API 서버 기본 URL
            proxies: 프록시 서버 설정 (예: {"http": "http://proxy:8080", "https": "https://proxy:8080"})
            timeout: 요청 타임아웃 (초)
            max_retries: 최대 재시도 횟수
            retry_delay: 재시도 간 지연 시간 (초)
            auth_token: 인증 토큰 (옵션)
        """
        self.base_url = base_url.rstrip("/")
        self.headers = {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
        if auth_token:
            self.headers["Authorization"] = f"Bearer {auth_token}"
            
        self.proxies = proxies
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        
        logger.debug(f"MemoryClient initialized: {base_url}")
    
    def _make_request(self, method: str, endpoint: str, 
                     params: Optional[Dict[str, Any]] = None,
                     data: Optional[Dict[str, Any]] = None,
                     retry_on_codes: Optional[List[int]] = None) -> Dict[str, Any]:
        """
        HTTP 요청 실행 (재시도 로직 포함)
        
        Args:
            method: HTTP 메서드 (get, post, put, delete)
            endpoint: API 엔드포인트 경로
            params: URL 파라미터 (옵션)
            data: 요청 본문 데이터 (옵션)
            retry_on_codes: 재시도할 HTTP 상태 코드 목록 (기본: [429, 500, 502, 503, 504])
            
        Returns:
            API 응답 데이터
            
        Raises:
            ConnectionFailedError: 서버 연결 실패
            RequestTimeoutError: 요청 타임아웃
            APIError: API 오류 응답
        """
        if retry_on_codes is None:
            retry_on_codes = [429, 500, 502, 503, 504]  # 기본 재시도 상태 코드
            
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        request_data = None
        
        if data:
            request_data = json.dumps(data)
            
        method_func = getattr(requests, method.lower())
        kwargs = {
            "headers": self.headers,
            "proxies": self.proxies,
            "timeout": self.timeout
        }
        
        if params:
            kwargs["params"] = params
            
        if data:
            kwargs["data"] = request_data
            
        logger.debug(f"API request: {method.upper()} {url}")
        
        last_exception = None
        for attempt in range(1, self.max_retries + 1):
            try:
                response = method_func(url, **kwargs)
                
                # 성공 응답
                if response.status_code < 400:
                    try:
                        return response.json()
                    except ValueError:
                        logger.warning(f"Non-JSON response: {response.text[:100]}")
                        return {"status": "success", "data": response.text}
                        
                # 재시도 가능한 오류 상태 코드
                if response.status_code in retry_on_codes and attempt < self.max_retries:
                    retry_after = response.headers.get('Retry-After')
                    if retry_after:
                        try:
                            delay = float(retry_after)
                        except ValueError:
                            delay = self.retry_delay
                    else:
                        delay = self.retry_delay * attempt  # 지수 백오프
                        
                    logger.warning(f"Retryable error (attempt {attempt}/{self.max_retries}): {response.status_code}, retrying after {delay}s")
                    time.sleep(delay)
                    continue
                    
                # 처리할 수 없는 API 오류
                original_error_message = response.text
                error_details = None
                try:
                    error_response = response.json()
                    original_error_message = error_response.get("message", response.text)
                    error_details = error_response # 전체 응답을 details로 저장
                except ValueError:
                    pass # JSON 파싱 실패 시 original_error_message는 response.text 유지
                
                if response.status_code == 401 or response.status_code == 403:
                    raise AuthenticationError(f"인증 실패 (코드: {response.status_code}): {original_error_message}")
                else:
                    raise APIError(response.status_code, original_error_message, response=error_details)
                
            except (ConnectionError, requests.exceptions.ProxyError) as e:
                last_exception = e
                if attempt < self.max_retries:
                    logger.warning(f"Connection error (attempt {attempt}/{self.max_retries}): {str(e)}, retrying after {self.retry_delay}s")
                    time.sleep(self.retry_delay)
                    continue
                raise ConnectionFailedError(f"서버 연결 실패: {str(e)}")
                
            except Timeout as e:
                last_exception = e
                if attempt < self.max_retries:
                    logger.warning(f"Timeout (attempt {attempt}/{self.max_retries}): {str(e)}, retrying after {self.retry_delay}s")
                    time.sleep(self.retry_delay)
                    continue
                raise RequestTimeoutError(f"요청 타임아웃: {str(e)}")
                
            except Exception as e:
                last_exception = e
                logger.error(f"요청 중 예외 발생: {str(e)}")
                raise
                
        # 모든 재시도가 실패한 경우
        if isinstance(last_exception, Timeout):
            raise RequestTimeoutError(f"최대 재시도 횟수 초과 ({self.max_retries}): 타임아웃")
        elif isinstance(last_exception, (ConnectionError, requests.exceptions.ProxyError)):
            raise ConnectionFailedError(f"최대 재시도 횟수 초과 ({self.max_retries}): 연결 실패")
        else:
            raise ClientError(f"최대 재시도 횟수 초과 ({self.max_retries}): {str(last_exception)}")
    
    def get_api_info(self) -> Dict[str, Any]:
        """
        API 서버 정보 조회
        
        Returns:
            API 정보
            
        Raises:
            ConnectionFailedError: 서버 연결 실패
            RequestTimeoutError: 요청 타임아웃
            APIError: API 오류 응답
        """
        return self._make_request("get", "/")
    
    def add_memory(self, context: str, keywords: Optional[List[str]] = None, 
                  tags: Optional[List[str]] = None, importance: Optional[float] = None) -> Dict[str, Any]:
        """
        새 기억 추가
        
        Args:
            context: 기억 내용
            keywords: 키워드 목록 (옵션)
            tags: 태그 목록 (옵션)
            importance: 중요도 (옵션)
            
        Returns:
            API 응답
            
        Raises:
            ConnectionFailedError: 서버 연결 실패
            RequestTimeoutError: 요청 타임아웃
            APIError: API 오류 응답
        """
        data = {"context": context}
        
        if keywords:
            data["keywords"] = keywords
        if tags:
            data["tags"] = tags
        if importance is not None:
            data["importance"] = importance
            
        return self._make_request("post", "/memory/", data=data)
    
    def get_memory(self, block_index: int) -> Dict[str, Any]:
        """
        특정 기억 조회
        
        Args:
            block_index: 블록 인덱스
            
        Returns:
            메모리 블록 정보
            
        Raises:
            ConnectionFailedError: 서버 연결 실패
            RequestTimeoutError: 요청 타임아웃
            APIError: API 오류 응답
        """
        return self._make_request("get", f"/memory/{block_index}")
    
    def get_recent_memories(self, limit: int = 10, offset: int = 0) -> Dict[str, Any]:
        """
        최근 기억 목록 조회
        
        Args:
            limit: 반환할 최대 기억 수
            offset: 시작 오프셋
            
        Returns:
            기억 목록
            
        Raises:
            ConnectionFailedError: 서버 연결 실패
            RequestTimeoutError: 요청 타임아웃
            APIError: API 오류 응답
        """
        params = {
            "limit": limit,
            "offset": offset
        }
        
        return self._make_request("get", "/memory/", params=params)
    
    def search_memories(self, query: str, mode: str = "hybrid", limit: int = 5) -> Dict[str, Any]:
        """
        기억 검색
        
        Args:
            query: 검색 쿼리
            mode: 검색 모드 (embedding, keyword, temporal, hybrid)
            limit: 결과 제한 개수
            
        Returns:
            검색 결과
            
        Raises:
            ConnectionFailedError: 서버 연결 실패
            RequestTimeoutError: 요청 타임아웃
            APIError: API 오류 응답
        """
        data = {
            "query": query,
            "mode": mode,
            "limit": limit
        }
        
        return self._make_request("post", "/search/", data=data)
    
    def update_memory(self, block_index: int, new_context: str, reason: str = "내용 업데이트") -> Dict[str, Any]:
        """
        기억 업데이트
        
        Args:
            block_index: 원본 블록 인덱스
            new_context: 새 내용
            reason: 변경 이유
            
        Returns:
            업데이트된 블록 정보
            
        Raises:
            ConnectionFailedError: 서버 연결 실패
            RequestTimeoutError: 요청 타임아웃
            APIError: API 오류 응답
        """
        data = {
            "original_block_index": block_index,
            "new_context": new_context,
            "reason": reason
        }
        
        return self._make_request("post", "/evolution/revisions", data=data)
    
    def get_revision_chain(self, block_index: int) -> Dict[str, Any]:
        """
        수정 이력 조회
        
        Args:
            block_index: 블록 인덱스
            
        Returns:
            수정 이력 정보
            
        Raises:
            ConnectionFailedError: 서버 연결 실패
            RequestTimeoutError: 요청 타임아웃
            APIError: API 오류 응답
        """
        return self._make_request("get", f"/evolution/revisions/{block_index}")
    
    def search_entities(self, query: str, entity_type: Optional[str] = None, limit: int = 10) -> Dict[str, Any]:
        """
        엔티티 검색
        
        Args:
            query: 검색 쿼리
            entity_type: 엔티티 유형 필터 (옵션)
            limit: 결과 제한 개수
            
        Returns:
            검색된 엔티티 목록
            
        Raises:
            ConnectionFailedError: 서버 연결 실패
            RequestTimeoutError: 요청 타임아웃
            APIError: API 오류 응답
        """
        params = {
            "query": query,
            "limit": limit
        }
        
        if entity_type:
            params["type"] = entity_type
            
        return self._make_request("get", "/knowledge/entities", params=params)
    
    def add_entity(self, name: str, entity_type: str, confidence: float = 0.7) -> Dict[str, Any]:
        """
        엔티티 추가
        
        Args:
            name: 엔티티 이름
            entity_type: 엔티티 유형
            confidence: 신뢰도
            
        Returns:
            생성된 엔티티 정보
            
        Raises:
            ConnectionFailedError: 서버 연결 실패
            RequestTimeoutError: 요청 타임아웃
            APIError: API 오류 응답
        """
        data = {
            "name": name,
            "type": entity_type,
            "confidence": confidence
        }
        
        return self._make_request("post", "/knowledge/entities", data=data)
    
    def get_entity_relationships(self, entity_id: int) -> Dict[str, Any]:
        """
        엔티티 관계 조회
        
        Args:
            entity_id: 엔티티 ID
            
        Returns:
            엔티티 및 관계 정보
            
        Raises:
            ConnectionFailedError: 서버 연결 실패
            RequestTimeoutError: 요청 타임아웃
            APIError: API 오류 응답
        """
        return self._make_request("get", f"/knowledge/entities/{entity_id}")


class SimplifiedMemoryClient:
    """
    간소화된 API 클라이언트
    (외부 LLM 통합에 사용하기 용이한 간결한 인터페이스)
    """
    
    def __init__(self, base_url: str = "http://localhost:8000", 
                proxies: Optional[Dict[str, str]] = None, 
                timeout: int = 30,
                max_retries: int = 3,
                retry_delay: float = 1.0,
                auth_token: Optional[str] = None):
        """
        간소화된 클라이언트 초기화
        
        Args:
            base_url: API 서버 기본 URL
            proxies: 프록시 서버 설정 (예: {"http": "http://proxy:8080", "https": "https://proxy:8080"})
            timeout: 요청 타임아웃 (초)
            max_retries: 최대 재시도 횟수
            retry_delay: 재시도 간 지연 시간 (초)
            auth_token: 인증 토큰 (옵션)
        """
        self.client = MemoryClient(
            base_url=base_url, 
            proxies=proxies, 
            timeout=timeout,
            max_retries=max_retries,
            retry_delay=retry_delay,
            auth_token=auth_token
        )
        logger.debug(f"SimplifiedMemoryClient 초기화: {base_url}")
    
    def add(self, content: str, importance: Optional[float] = None) -> Dict[str, Any]:
        """
        기억 추가 (간소화)
        
        Args:
            content: 기억 내용
            importance: 중요도 (0.0-1.0 사이)
            
        Returns:
            성공 여부와 블록 인덱스를 포함한 결과 객체
            
        Raises:
            ConnectionFailedError: 서버 연결 실패
            RequestTimeoutError: 요청 타임아웃
            APIError: API 오류 응답
        """
        try:
            response = self.client.add_memory(content, importance=importance)
            return {
                "success": True,
                "block_index": response.get("block_index"),
                "keywords": response.get("data", {}).get("keywords", []),
                "timestamp": response.get("data", {}).get("timestamp")
            }
        except ClientError as e:
            logger.error("SimplifiedMemoryClient.add 실패: %s", e)
            return {
                "success": False,
                "error": str(e),
                "block_index": None
            }
    
    def search(self, query: str, limit: int = 3) -> List[Dict[str, Any]]:
        """
        기억 검색 (간소화)
        
        Args:
            query: 검색 쿼리
            limit: 결과 제한 개수
            
        Returns:
            검색 결과 목록. 각 항목은 다음 필드를 포함:
            - block_index: 블록 인덱스
            - content: 기억 내용
            - timestamp: 타임스탬프
            - importance: 중요도
            - relevance: 검색 관련성 점수
            
        Raises:
            ConnectionFailedError: 서버 연결 실패
            RequestTimeoutError: 요청 타임아웃
            APIError: API 오류 응답
        """
        try:
            response = self.client.search_memories(query, mode="hybrid", limit=limit)
            
            # 결과 간소화 및 표준화
            results = []
            for block in response.get("data", []):
                results.append({
                    "block_index": block.get("block_index"),
                    "content": block.get("context"),
                    "timestamp": block.get("timestamp"),
                    "importance": block.get("importance", 0),
                    "relevance": block.get("relevance_score", 0)
                })
                
            return results
        except ClientError as e:
            logger.error(f"SimplifiedMemoryClient: {e.__class__.__name__} 발생 - {str(e)}")
            raise
    
    def remember(self, query: str, limit: int = 3) -> str:
        """
        기억 검색 결과 문자열 반환 (LLM 프롬프트 삽입용)
        
        Args:
            query: 검색 쿼리
            limit: 결과 제한 개수
            
        Returns:
            검색 결과 문자열
        """
        try:
            results = self.search(query, limit=limit)
            
            if not results:
                return "관련 기억을 찾을 수 없습니다."
                
            memory_strings = []
            for i, result in enumerate(results):
                timestamp = result.get("timestamp", "").split("T")[0]
                memory_strings.append(
                    f"[기억 {i+1}, {timestamp}] {result.get('content')}"
                )
                
            return "\n\n".join(memory_strings)
        except Exception as e:
            logger.error(f"SimplifiedMemoryClient: {e.__class__.__name__} 발생 - {str(e)}")
            raise
            
    def update(self, block_index: int, new_content: str, reason: str = "내용 업데이트") -> Dict[str, Any]:
        """
        기억 업데이트 (간소화)
        
        Args:
            block_index: 블록 인덱스
            new_content: 새 내용
            reason: 변경 이유
            
        Returns:
            업데이트 결과 객체
            
        Raises:
            ConnectionFailedError: 서버 연결 실패
            RequestTimeoutError: 요청 타임아웃
            APIError: API 오류 응답
        """
        try:
            response = self.client.update_memory(block_index, new_content, reason)
            
            return {
                "success": True,
                "block_index": response.get("block_index"),
                "original_block_index": block_index,
                "timestamp": response.get("data", {}).get("timestamp")
            }
        except ClientError as e:
            logger.error(f"SimplifiedMemoryClient: {e.__class__.__name__} 발생 - {str(e)}")
            raise
    
    def get_health(self) -> Dict[str, Any]:
        """
        API 서버 상태 확인
        
        Returns:
            서버 상태 정보 객체
        """
        try:
            response = self.client.get_api_info()
            return {
                "status": "online",
                "version": response.get("version", "unknown"),
                "success": True
            }
        except Exception as e:
            logger.error("SimplifiedMemoryClient.get_health 실패: %s", e)
            return {
                "status": "offline",
                "success": False,
                "error": str(e)
            }
            # 이 경우 SimplifiedClientOperationError 클래스 정의 필요
            # raise SimplifiedClientOperationError(f"서버 상태 확인 실패: {str(e)}", original_exception=e)
            # 이 경우 SimplifiedClientOperationError 클래스 정의 필요 