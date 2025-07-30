#!/usr/bin/env python3
"""
v2.0.4 통합 테스트
- CLI, MCP, 데이터베이스 간 연동 테스트
- 실제 사용 시나리오 기반 검증
"""

import unittest
import tempfile
import os
import shutil
import subprocess
import json
import time


class TestV204Integration(unittest.TestCase):
    """v2.0.4 통합 테스트"""
    
    def setUp(self):
        """테스트 환경 설정"""
        self.test_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.chdir(self.test_dir)
        
        # 데이터 디렉토리 생성
        os.makedirs("data", exist_ok=True)
    
    def tearDown(self):
        """테스트 환경 정리"""
        os.chdir(self.original_cwd)
        shutil.rmtree(self.test_dir)
    
    def test_cli_basic_workflow(self):
        """CLI 기본 워크플로우 테스트"""
        # 1. 메모리 추가
        result = subprocess.run([
            "python3", "-m", "greeum.cli", "memory", "add",
            "통합 테스트 메모리 항목"
        ], capture_output=True, text=True, cwd=self.original_cwd)
        
        self.assertEqual(result.returncode, 0)
        self.assertIn("Memory added", result.stdout)
        
        # 2. 메모리 검색
        result = subprocess.run([
            "python3", "-m", "greeum.cli", "memory", "search",
            "통합"
        ], capture_output=True, text=True, cwd=self.original_cwd)
        
        self.assertEqual(result.returncode, 0)
        self.assertIn("Found", result.stdout)
        self.assertIn("통합 테스트", result.stdout)
    
    def test_cli_error_handling(self):
        """CLI 오류 처리 테스트"""
        # 잘못된 명령어
        result = subprocess.run([
            "python3", "-m", "greeum.cli", "invalid_command"
        ], capture_output=True, text=True, cwd=self.original_cwd)
        
        self.assertNotEqual(result.returncode, 0)
        
        # 빈 검색어
        result = subprocess.run([
            "python3", "-m", "greeum.cli", "memory", "search", ""
        ], capture_output=True, text=True, cwd=self.original_cwd)
        
        # 빈 검색어도 처리 가능해야 함
        self.assertEqual(result.returncode, 0)
    
    def test_mcp_server_basic_functionality(self):
        """MCP 서버 기본 기능 테스트"""
        from greeum.mcp.claude_code_mcp_server import ClaudeCodeMCPServer
        
        server = ClaudeCodeMCPServer()
        
        # 메모리 추가 테스트
        result = server._add_memory_direct("MCP 통합 테스트 메모리")
        self.assertIsInstance(result, dict)
        self.assertIn("block_index", result)
        self.assertEqual(result["context"], "MCP 통합 테스트 메모리")
        
        # 메모리 검색 테스트
        search_results = server._search_memory_direct("MCP")
        self.assertIsInstance(search_results, list)
        
        # 최소 1개 이상의 결과 (방금 추가한 것)
        self.assertGreater(len(search_results), 0)
    
    def test_database_cli_consistency(self):
        """데이터베이스와 CLI 간 일관성 테스트"""
        from greeum.core.database_manager import DatabaseManager
        from greeum.core.block_manager import BlockManager
        
        # 1. CLI로 메모리 추가
        result = subprocess.run([
            "python3", "-m", "greeum.cli", "memory", "add",
            "일관성 테스트 항목"
        ], capture_output=True, text=True, cwd=self.original_cwd)
        
        self.assertEqual(result.returncode, 0)
        
        # 2. 데이터베이스에서 직접 검색
        db_manager = DatabaseManager()
        block_manager = BlockManager(db_manager)
        
        results = block_manager.search_by_keywords(["일관성"])
        self.assertGreater(len(results), 0)
        
        # 추가한 내용이 포함되어 있는지 확인
        found = False
        for result in results:
            if "일관성 테스트" in result.get("context", ""):
                found = True
                break
        
        self.assertTrue(found, "CLI로 추가한 메모리가 데이터베이스에서 검색되지 않음")
        
        db_manager.close()
    
    def test_unicode_handling(self):
        """유니코드 처리 통합 테스트"""
        unicode_texts = [
            "한글 메모리 테스트 🚀",
            "English memory test 🎉",
            "中文记忆测试 📝",
            "日本語メモリーテスト ✨"
        ]
        
        for i, text in enumerate(unicode_texts):
            # CLI로 추가
            result = subprocess.run([
                "python3", "-m", "greeum.cli", "memory", "add",
                text
            ], capture_output=True, text=True, cwd=self.original_cwd)
            
            self.assertEqual(result.returncode, 0, f"Failed to add: {text}")
            
            # MCP 서버로 검색
            from greeum.mcp.claude_code_mcp_server import ClaudeCodeMCPServer
            server = ClaudeCodeMCPServer()
            
            # 언어별 키워드로 검색
            search_terms = ["한글", "English", "中文", "日本語"]
            if i < len(search_terms):
                search_results = server._search_memory_direct(search_terms[i])
                self.assertIsInstance(search_results, list)
    
    def test_large_scale_integration(self):
        """대규모 통합 테스트"""
        from greeum.mcp.claude_code_mcp_server import ClaudeCodeMCPServer
        
        server = ClaudeCodeMCPServer()
        
        # 100개의 메모리 추가
        for i in range(100):
            text = f"대규모 테스트 항목 {i} - 샘플 데이터"
            result = server._add_memory_direct(text, importance=0.5)
            
            self.assertIsInstance(result, dict)
            self.assertIn("block_index", result)
            
            # 10개마다 중간 검색 테스트
            if i % 10 == 9:
                search_results = server._search_memory_direct("대규모")
                self.assertGreater(len(search_results), i // 2)  # 최소 절반은 검색되어야 함
        
        # 최종 검색 테스트
        final_results = server._search_memory_direct("대규모")
        self.assertGreater(len(final_results), 50)  # 최소 50개는 검색되어야 함
        
        # 특정 인덱스 검색
        specific_results = server._search_memory_direct("항목 50")
        self.assertGreater(len(specific_results), 0)
    
    def test_concurrent_access_simulation(self):
        """동시 접근 시뮬레이션 테스트"""
        import threading
        import time
        
        from greeum.mcp.claude_code_mcp_server import ClaudeCodeMCPServer
        
        results = []
        errors = []
        
        def worker_thread(thread_id):
            try:
                server = ClaudeCodeMCPServer()
                
                # 각 스레드가 10개씩 추가
                for i in range(10):
                    text = f"동시 접근 테스트 Thread-{thread_id} Item-{i}"
                    result = server._add_memory_direct(text)
                    
                    if result and "block_index" in result:
                        results.append(result["block_index"])
                    
                    time.sleep(0.01)  # 짧은 지연
                    
                # 검색 테스트
                search_results = server._search_memory_direct(f"Thread-{thread_id}")
                if len(search_results) >= 5:  # 최소 절반은 검색되어야 함
                    results.append(f"search_success_{thread_id}")
                    
            except Exception as e:
                errors.append(f"Thread {thread_id}: {str(e)}")
        
        # 3개 스레드로 동시 실행
        threads = []
        for i in range(3):
            thread = threading.Thread(target=worker_thread, args=(i,))
            threads.append(thread)
            thread.start()
        
        # 모든 스레드 완료 대기
        for thread in threads:
            thread.join(timeout=30)  # 30초 타임아웃
        
        # 결과 검증
        self.assertEqual(len(errors), 0, f"Concurrent access errors: {errors}")
        self.assertGreater(len(results), 20)  # 최소 20개 이상의 성공적인 작업
    
    def test_error_recovery(self):
        """오류 복구 테스트"""
        from greeum.mcp.claude_code_mcp_server import ClaudeCodeMCPServer
        
        server = ClaudeCodeMCPServer()
        
        # 정상 메모리 추가
        result1 = server._add_memory_direct("정상 메모리 1")
        self.assertIsInstance(result1, dict)
        
        # 극단적 입력 시도
        extreme_inputs = [
            "",  # 빈 문자열
            "x" * 10000,  # 매우 긴 문자열
            "\x00\x01\x02",  # 특수 문자
            "🚀" * 1000,  # 이모지 반복
        ]
        
        for extreme_input in extreme_inputs:
            try:
                result = server._add_memory_direct(extreme_input)
                # 결과가 None이 아니면 성공적으로 처리됨
                if result is not None:
                    self.assertIsInstance(result, dict)
            except Exception:
                # 예외가 발생해도 시스템이 계속 동작해야 함
                pass
        
        # 시스템이 여전히 정상 동작하는지 확인
        result2 = server._add_memory_direct("정상 메모리 2")
        self.assertIsInstance(result2, dict)
        
        # 검색도 정상 동작하는지 확인
        search_results = server._search_memory_direct("정상")
        self.assertGreater(len(search_results), 0)


if __name__ == '__main__':
    unittest.main(verbosity=2)