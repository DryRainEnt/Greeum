"""
MemoryBlockEngine API 클라이언트
"""

import requests
import json
from typing import Dict, List, Any, Optional, Union

class MemoryClient:
    """MemoryBlockEngine API 클라이언트"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        """
        API 클라이언트 초기화
        
        Args:
            base_url: API 서버 기본 URL
        """
        self.base_url = base_url.rstrip("/")
        self.headers = {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
    
    def get_api_info(self) -> Dict[str, Any]:
        """
        API 서버 정보 조회
        
        Returns:
            API 정보
        """
        response = requests.get(f"{self.base_url}/", headers=self.headers)
        response.raise_for_status()
        return response.json()
    
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
        """
        data = {"context": context}
        
        if keywords:
            data["keywords"] = keywords
        if tags:
            data["tags"] = tags
        if importance is not None:
            data["importance"] = importance
            
        response = requests.post(
            f"{self.base_url}/memory/",
            headers=self.headers,
            json=data
        )
        response.raise_for_status()
        return response.json()
    
    def get_memory(self, block_index: int) -> Dict[str, Any]:
        """
        특정 기억 조회
        
        Args:
            block_index: 블록 인덱스
            
        Returns:
            메모리 블록 정보
        """
        response = requests.get(
            f"{self.base_url}/memory/{block_index}",
            headers=self.headers
        )
        response.raise_for_status()
        return response.json()
    
    def get_recent_memories(self, limit: int = 10, offset: int = 0) -> Dict[str, Any]:
        """
        최근 기억 목록 조회
        
        Args:
            limit: 반환할 최대 기억 수
            offset: 시작 오프셋
            
        Returns:
            기억 목록
        """
        params = {
            "limit": limit,
            "offset": offset
        }
        
        response = requests.get(
            f"{self.base_url}/memory/",
            headers=self.headers,
            params=params
        )
        response.raise_for_status()
        return response.json()
    
    def search_memories(self, query: str, mode: str = "hybrid", limit: int = 5) -> Dict[str, Any]:
        """
        기억 검색
        
        Args:
            query: 검색 쿼리
            mode: 검색 모드 (embedding, keyword, temporal, hybrid)
            limit: 결과 제한 개수
            
        Returns:
            검색 결과
        """
        data = {
            "query": query,
            "mode": mode,
            "limit": limit
        }
        
        response = requests.post(
            f"{self.base_url}/search/",
            headers=self.headers,
            json=data
        )
        response.raise_for_status()
        return response.json()
    
    def update_memory(self, block_index: int, new_context: str, reason: str = "내용 업데이트") -> Dict[str, Any]:
        """
        기억 업데이트
        
        Args:
            block_index: 원본 블록 인덱스
            new_context: 새 내용
            reason: 변경 이유
            
        Returns:
            업데이트된 블록 정보
        """
        data = {
            "original_block_index": block_index,
            "new_context": new_context,
            "reason": reason
        }
        
        response = requests.post(
            f"{self.base_url}/evolution/revisions",
            headers=self.headers,
            json=data
        )
        response.raise_for_status()
        return response.json()
    
    def get_revision_chain(self, block_index: int) -> Dict[str, Any]:
        """
        수정 이력 조회
        
        Args:
            block_index: 블록 인덱스
            
        Returns:
            수정 이력 정보
        """
        response = requests.get(
            f"{self.base_url}/evolution/revisions/{block_index}",
            headers=self.headers
        )
        response.raise_for_status()
        return response.json()
    
    def search_entities(self, query: str, entity_type: Optional[str] = None, limit: int = 10) -> Dict[str, Any]:
        """
        엔티티 검색
        
        Args:
            query: 검색 쿼리
            entity_type: 엔티티 유형 필터 (옵션)
            limit: 결과 제한 개수
            
        Returns:
            검색된 엔티티 목록
        """
        params = {
            "query": query,
            "limit": limit
        }
        
        if entity_type:
            params["type"] = entity_type
            
        response = requests.get(
            f"{self.base_url}/knowledge/entities",
            headers=self.headers,
            params=params
        )
        response.raise_for_status()
        return response.json()
    
    def add_entity(self, name: str, entity_type: str, confidence: float = 0.7) -> Dict[str, Any]:
        """
        엔티티 추가
        
        Args:
            name: 엔티티 이름
            entity_type: 엔티티 유형
            confidence: 신뢰도
            
        Returns:
            생성된 엔티티 정보
        """
        data = {
            "name": name,
            "type": entity_type,
            "confidence": confidence
        }
        
        response = requests.post(
            f"{self.base_url}/knowledge/entities",
            headers=self.headers,
            json=data
        )
        response.raise_for_status()
        return response.json()
    
    def get_entity_relationships(self, entity_id: int) -> Dict[str, Any]:
        """
        엔티티 관계 조회
        
        Args:
            entity_id: 엔티티 ID
            
        Returns:
            엔티티 및 관계 정보
        """
        response = requests.get(
            f"{self.base_url}/knowledge/entities/{entity_id}",
            headers=self.headers
        )
        response.raise_for_status()
        return response.json()


class SimplifiedMemoryClient:
    """
    간소화된 API 클라이언트
    (외부 LLM 통합에 사용하기 용이한 간결한 인터페이스)
    """
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        """
        간소화된 클라이언트 초기화
        
        Args:
            base_url: API 서버 기본 URL
        """
        self.client = MemoryClient(base_url)
    
    def add(self, content: str) -> Dict[str, Any]:
        """
        기억 추가 (간소화)
        
        Args:
            content: 기억 내용
            
        Returns:
            성공 여부와 블록 인덱스
        """
        response = self.client.add_memory(content)
        
        if response.get("status") != "success":
            raise Exception(response.get("message", "기억 추가 실패"))
            
        return {
            "success": True,
            "block_index": response.get("block_index"),
            "keywords": response.get("data", {}).get("keywords", [])
        }
    
    def search(self, query: str, limit: int = 3) -> List[Dict[str, Any]]:
        """
        기억 검색 (간소화)
        
        Args:
            query: 검색 쿼리
            limit: 결과 제한 개수
            
        Returns:
            검색 결과 목록
        """
        response = self.client.search_memories(query, mode="hybrid", limit=limit)
        
        if response.get("status") != "success":
            raise Exception(response.get("message", "검색 실패"))
            
        # 결과 간소화
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
    
    def remember(self, query: str, limit: int = 3) -> str:
        """
        기억 검색 결과 문자열 반환 (LLM 프롬프트 삽입용)
        
        Args:
            query: 검색 쿼리
            limit: 결과 제한 개수
            
        Returns:
            검색 결과 문자열
        """
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