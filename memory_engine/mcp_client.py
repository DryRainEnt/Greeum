import requests
import json
import logging
from typing import Dict, Any, List, Optional, Union

class MCPClient:
    """
    Cursor MCP(Model Control Protocol) 클라이언트
    Cursor 환경에서 MCP를 사용하기 위한 클라이언트 구현
    """
    
    def __init__(self, api_key: str, base_url: str = "http://localhost:8000/api/mcp"):
        """
        MCP 클라이언트 초기화
        
        Args:
            api_key: MCP API 키
            base_url: MCP API 기본 URL
        """
        self.api_key = api_key
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        })
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger("MCPClient")
    
    def _make_request(self, endpoint: str, method: str = "GET", data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        API 요청 처리
        
        Args:
            endpoint: API 엔드포인트
            method: HTTP 메소드 (GET, POST, PUT, DELETE)
            data: 요청 데이터
            
        Returns:
            API 응답
        """
        url = f"{self.base_url}/{endpoint}"
        try:
            if method == "GET":
                response = self.session.get(url)
            elif method == "POST":
                response = self.session.post(url, json=data)
            elif method == "PUT":
                response = self.session.put(url, json=data)
            elif method == "DELETE":
                response = self.session.delete(url)
            else:
                raise ValueError(f"지원하지 않는 HTTP 메소드: {method}")
            
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            self.logger.error(f"API 요청 실패: {e}")
            return {"error": str(e)}
    
    def execute_menu_item(self, menu_path: str) -> Dict[str, Any]:
        """
        Unity 메뉴 아이템 실행
        
        Args:
            menu_path: 메뉴 경로 (예: "GameObject/Create Empty")
            
        Returns:
            API 응답
        """
        data = {"menuPath": menu_path}
        return self._make_request("unity/execute_menu_item", method="POST", data=data)
    
    def select_gameobject(self, object_path: Optional[str] = None, instance_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Unity 게임오브젝트 선택
        
        Args:
            object_path: 게임오브젝트 경로
            instance_id: 게임오브젝트 인스턴스 ID
            
        Returns:
            API 응답
        """
        data = {}
        if object_path:
            data["objectPath"] = object_path
        if instance_id:
            data["instanceId"] = instance_id
        return self._make_request("unity/select_gameobject", method="POST", data=data)
    
    def add_package(self, source: str, **kwargs) -> Dict[str, Any]:
        """
        Unity 패키지 추가
        
        Args:
            source: 패키지 소스 (registry, github, disk)
            **kwargs: 패키지 추가에 필요한 추가 인자
            
        Returns:
            API 응답
        """
        data = {"source": source, **kwargs}
        return self._make_request("unity/add_package", method="POST", data=data)
    
    def run_tests(self, test_mode: str = "EditMode", test_filter: str = "", return_only_failures: bool = True) -> Dict[str, Any]:
        """
        Unity 테스트 실행
        
        Args:
            test_mode: 테스트 모드 (EditMode 또는 PlayMode)
            test_filter: 테스트 필터
            return_only_failures: 실패한 테스트만 반환할지 여부
            
        Returns:
            API 응답
        """
        data = {
            "testMode": test_mode,
            "testFilter": test_filter,
            "returnOnlyFailures": return_only_failures
        }
        return self._make_request("unity/run_tests", method="POST", data=data)
    
    def send_console_log(self, message: str, log_type: str = "info") -> Dict[str, Any]:
        """
        Unity 콘솔에 로그 메시지 전송
        
        Args:
            message: 로그 메시지
            log_type: 로그 타입 (info, warning, error)
            
        Returns:
            API 응답
        """
        data = {
            "message": message,
            "type": log_type
        }
        return self._make_request("unity/send_console_log", method="POST", data=data)
    
    def update_component(self, component_name: str, **kwargs) -> Dict[str, Any]:
        """
        Unity 컴포넌트 업데이트
        
        Args:
            component_name: 컴포넌트 이름
            **kwargs: 컴포넌트 업데이트에 필요한 추가 인자
            
        Returns:
            API 응답
        """
        data = {"componentName": component_name, **kwargs}
        return self._make_request("unity/update_component", method="POST", data=data)
    
    def add_asset_to_scene(self, **kwargs) -> Dict[str, Any]:
        """
        Unity 씬에 에셋 추가
        
        Args:
            **kwargs: 에셋 추가에 필요한 인자
            
        Returns:
            API 응답
        """
        return self._make_request("unity/add_asset_to_scene", method="POST", data=kwargs)

    def manage_memory(self, action: str, memory_content: str = "", memory_id: Optional[str] = None, 
                    query: Optional[str] = None, limit: int = 10) -> Dict[str, Any]:
        """
        메모리 엔진과 MCP 연동
        
        Args:
            action: 메모리 액션 (add, get, query, update, delete)
            memory_content: 추가/업데이트할 메모리 내용
            memory_id: 메모리 ID
            query: 메모리 쿼리 문자열
            limit: 결과 제한 수
            
        Returns:
            API 응답
        """
        data = {
            "action": action,
            "limit": limit
        }
        
        if memory_content:
            data["memory_content"] = memory_content
        if memory_id:
            data["memory_id"] = memory_id
        if query:
            data["query"] = query
            
        return self._make_request("memory", method="POST", data=data) 