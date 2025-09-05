"""
API 클라이언트 테스트
"""

import unittest
import json
from unittest.mock import patch, MagicMock, Mock
import requests
from requests.exceptions import Timeout, ConnectionError

from tests.base_test_case import BaseGreeumTestCase
from greeum.client import (
    MemoryClient, SimplifiedMemoryClient,
    ClientError, ConnectionFailedError, RequestTimeoutError, APIError
)

class TestMemoryClient(BaseGreeumTestCase):
    """MemoryClient 테스트 클래스"""
    
    def setUp(self):
        """테스트 설정"""
        super().setUp()
        
        self.base_url = "http://test.server.com"
        self.client = MemoryClient(
            base_url=self.base_url,
            max_retries=2,
            retry_delay=0.01  # 빠른 테스트를 위해 짧게 설정
        )
    
    @patch('requests.get')
    def test_successful_request(self, mock_get):
        """성공적인 요청 테스트"""
        # 모의 응답 설정
        mock_response = Mock()
        mock_response.json.return_value = {"status": "success", "version": "1.0.0"}
        mock_response.status_code = 200
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        # API 호출
        result = self.client.get_api_info()
        
        # 검증
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["version"], "1.0.0")
    
    @patch('requests.get')
    def test_retry_on_server_error(self, mock_get):
        """서버 오류 시 재시도 테스트"""
        # 첫 번째 요청은 실패, 두 번째는 성공
        mock_responses = []
        
        # 첫 번째 응답 (실패)
        mock_error_response = Mock()
        mock_error_response.json.return_value = {"error": "Server error"}
        mock_error_response.status_code = 503
        mock_error_response.raise_for_status.side_effect = requests.exceptions.HTTPError("503 Server Error")
        
        # 두 번째 응답 (성공)
        mock_success_response = Mock()
        mock_success_response.json.return_value = {"status": "success", "version": "1.0.0"}
        mock_success_response.status_code = 200
        mock_success_response.raise_for_status.return_value = None
        
        mock_get.side_effect = [mock_error_response, mock_success_response]
        
        # API 호출
        result = self.client.get_api_info()
        
        # 검증
        self.assertEqual(result["status"], "success")
        self.assertEqual(mock_get.call_count, 2)  # 두 번 호출되었는지 확인
    
    @patch('requests.get')
    def test_api_error(self, mock_get):
        """API 오류 테스트"""
        # 모의 응답 설정
        mock_response = Mock()
        mock_response.json.return_value = {"status": "error", "message": "Invalid request"}
        mock_response.status_code = 400
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError("400 Client Error")
        mock_get.return_value = mock_response
        
        # API 호출 및 예외 확인
        with self.assertRaises(APIError) as context:
            self.client.get_api_info()
        
        # 예외 내용 검증
        self.assertEqual(context.exception.status_code, 400)
    
    @patch('requests.get')
    def test_connection_error(self, mock_get):
        """연결 오류 테스트"""
        # ConnectionError 발생 시뮬레이션
        mock_get.side_effect = ConnectionError("Failed to connect")
        
        # API 호출 및 예외 확인
        with self.assertRaises(ConnectionFailedError):
            self.client.get_api_info()
    
    @patch('requests.get')
    def test_timeout_error(self, mock_get):
        """타임아웃 오류 테스트"""
        # Timeout 발생 시뮬레이션
        mock_get.side_effect = Timeout("Request timed out")
        
        # API 호출 및 예외 확인
        with self.assertRaises(RequestTimeoutError):
            self.client.get_api_info()
    
    @patch('requests.get')
    def test_non_json_response(self, mock_get):
        """JSON이 아닌 응답 테스트"""
        # 모의 응답 설정 (JSON이 아닌 텍스트)
        mock_response = Mock()
        mock_response.json.side_effect = ValueError("No JSON object could be decoded")
        mock_response.text = "Not a JSON response"
        mock_response.status_code = 200
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        # API 호출
        result = self.client.get_api_info()
        
        # 검증
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["data"], "Not a JSON response")
    
    @patch('requests.post')
    def test_add_memory(self, mock_post):
        """기억 추가 테스트"""
        # 모의 응답 설정
        mock_response = Mock()
        mock_response.json.return_value = {"status": "success", "block_index": 123}
        mock_response.status_code = 200
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response
        
        # API 호출
        result = self.client.add_memory(
            context="Test memory",
            importance=0.7
        )
        
        # 검증
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["block_index"], 123)
        
        # 요청 데이터 검증
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        self.assertIn("json", call_args.kwargs)
        request_data = call_args.kwargs["json"]
        self.assertEqual(request_data["context"], "Test memory")
        self.assertEqual(request_data["importance"], 0.7)


class TestSimplifiedMemoryClient(BaseGreeumTestCase):
    """SimplifiedMemoryClient 테스트 클래스"""
    
    def setUp(self):
        """테스트 설정"""
        super().setUp()
        
        self.base_url = "http://test.server.com"
        
        # MemoryClient를 모킹하기 위한 패치
        self.memory_client_patcher = patch('greeum.client.MemoryClient')
        self.mock_memory_client = self.memory_client_patcher.start()
        self.mock_instance = self.mock_memory_client.return_value
        
        # SimplifiedMemoryClient 초기화
        self.client = SimplifiedMemoryClient(
            base_url=self.base_url,
            max_retries=2,
            retry_delay=0.01
        )
    
    def tearDown(self):
        """테스트 종료 시 패치 중지"""
        self.memory_client_patcher.stop()
    
    def test_add_success(self):
        """기억 추가 성공 테스트"""
        # MemoryClient.add_memory의 반환값 설정
        self.mock_instance.add_memory.return_value = {
            "status": "success",
            "block_index": 123,
            "data": {
                "keywords": ["test", "memory"],
                "timestamp": "2025-05-20T12:34:56"
            }
        }
        
        # 메서드 호출
        result = self.client.add("Test memory", importance=0.7)
        
        # 검증
        self.assertTrue(result["success"])
        self.assertEqual(result["block_index"], 123)
        self.assertEqual(result["keywords"], ["test", "memory"])
        self.assertEqual(result["timestamp"], "2025-05-20T12:34:56")
        
        # MemoryClient.add_memory가 올바른 인자로 호출되었는지 확인
        self.mock_instance.add_memory.assert_called_once_with("Test memory", importance=0.7)
    
    def test_add_error(self):
        """기억 추가 실패 테스트"""
        # 예외 발생 시뮬레이션
        self.mock_instance.add_memory.side_effect = ConnectionFailedError("Connection failed")
        
        # 메서드 호출
        result = self.client.add("Test memory")
        
        # 검증
        self.assertFalse(result["success"])
        self.assertIn("Connection failed", result["error"])
        self.assertIsNone(result["block_index"])
    
    def test_search(self):
        """기억 검색 테스트"""
        # MemoryClient.search_memories의 반환값 설정
        self.mock_instance.search_memories.return_value = {
            "status": "success",
            "data": [
                {
                    "block_index": 123,
                    "context": "Test memory 1",
                    "timestamp": "2025-05-20T12:34:56",
                    "importance": 0.7,
                    "relevance_score": 0.9
                },
                {
                    "block_index": 124,
                    "context": "Test memory 2",
                    "timestamp": "2025-05-20T12:35:56",
                    "importance": 0.6,
                    "relevance_score": 0.8
                }
            ]
        }
        
        # 메서드 호출
        results = self.client.search("query", limit=2)
        
        # 검증
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0]["block_index"], 123)
        self.assertEqual(results[0]["content"], "Test memory 1")
        self.assertEqual(results[0]["relevance"], 0.9)
        
        # MemoryClient.search_memories가 올바른 인자로 호출되었는지 확인
        self.mock_instance.search_memories.assert_called_once_with("query", mode="hybrid", limit=2)
    
    def test_remember(self):
        """기억 문자열 생성 테스트"""
        # search 메서드 모킹
        self.client.search = MagicMock(return_value=[
            {
                "block_index": 123,
                "content": "Test memory 1",
                "timestamp": "2025-05-20T12:34:56",
                "importance": 0.7,
                "relevance": 0.9
            }
        ])
        
        # 메서드 호출
        result = self.client.remember("query", limit=1)
        
        # 검증
        self.assertIn("[기억 1, 2025-05-20]", result)
        self.assertIn("Test memory 1", result)
        
        # search가 올바른 인자로 호출되었는지 확인
        self.client.search.assert_called_once_with("query", limit=1)
    
    def test_get_health_success(self):
        """서버 상태 확인 성공 테스트"""
        # MemoryClient.get_api_info의 반환값 설정
        self.mock_instance.get_api_info.return_value = {
            "status": "success",
            "version": "1.0.0"
        }
        
        # 메서드 호출
        result = self.client.get_health()
        
        # 검증
        self.assertTrue(result["success"])
        self.assertEqual(result["status"], "online")
        self.assertEqual(result["version"], "1.0.0")
    
    def test_get_health_error(self):
        """서버 상태 확인 실패 테스트"""
        # 예외 발생 시뮬레이션
        self.mock_instance.get_api_info.side_effect = ConnectionFailedError("Connection failed")
        
        # 메서드 호출
        result = self.client.get_health()
        
        # 검증
        self.assertFalse(result["success"])
        self.assertEqual(result["status"], "offline")
        self.assertIn("Connection failed", result["error"])


if __name__ == "__main__":
    unittest.main() 