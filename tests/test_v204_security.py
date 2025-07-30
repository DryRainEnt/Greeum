#!/usr/bin/env python3
"""
v2.0.4 보안 테스트 - 단순화된 버전
"""

import unittest
import tempfile
import os
import shutil

from greeum.core.database_manager import DatabaseManager
from greeum.core.block_manager import BlockManager
from greeum.embedding_models import SimpleEmbeddingModel
from greeum.text_utils import process_user_input


class TestV204Security(unittest.TestCase):
    """v2.0.4 보안 테스트"""
    
    def test_simple_embedding_security(self):
        """SimpleEmbedding 악성 입력 테스트"""
        model = SimpleEmbeddingModel(dimension=128)
        
        malicious_inputs = [
            "'; DROP TABLE blocks; --",
            "<script>alert('xss')</script>",
            "../../../etc/passwd",
            "a" * 1000,  # 긴 입력
        ]
        
        for malicious_input in malicious_inputs:
            embedding = model.encode(malicious_input)
            self.assertEqual(len(embedding), 128)
            self.assertTrue(all(isinstance(x, float) for x in embedding))
    
    def test_database_basic_security(self):
        """기본 데이터베이스 보안 테스트"""
        temp_dir = tempfile.mkdtemp()
        try:
            db_path = os.path.join(temp_dir, "test.db")
            db_manager = DatabaseManager(connection_string=db_path)
            
            # SQL 인젝션 시도 (키워드 검색)
            malicious_keywords = [
                "'; DROP TABLE blocks; --",
                "' OR '1'='1",
            ]
            
            for keyword in malicious_keywords:
                results = db_manager.search_blocks_by_keyword([keyword])
                self.assertIsInstance(results, list)
            
            # 데이터베이스 연결 확인 - 테스트 블록 추가
            test_block = {
                "block_index": 1,
                "timestamp": "2025-07-30T15:00:00",
                "context": "보안 테스트",
                "keywords": ["보안"],
                "tags": ["테스트"],
                "embedding": [0.1] * 128,
                "importance": 0.5,
                "hash": "test_hash",
                "prev_hash": ""
            }
            db_manager.add_block(test_block)
            
            # 추가된 블록 확인
            retrieved = db_manager.get_block(1)
            self.assertIsNotNone(retrieved)
            
            db_manager.close()
            
        finally:
            shutil.rmtree(temp_dir)
    
    def test_text_processing_safety(self):
        """텍스트 처리 안전성 테스트"""
        malicious_texts = [
            "<script>alert('xss')</script>",
            "'; DELETE FROM users; --",
            "../../../etc/passwd",
        ]
        
        for text in malicious_texts:
            result = process_user_input(text)
            
            # 기본 구조 검증
            self.assertIsInstance(result, dict)
            self.assertIn("keywords", result)
            self.assertIn("tags", result)
            self.assertIn("embedding", result)
            self.assertIn("importance", result)
            
            # 타입 검증
            self.assertIsInstance(result["keywords"], list)
            self.assertIsInstance(result["tags"], list)
            self.assertIsInstance(result["embedding"], list)
            self.assertIsInstance(result["importance"], float)
    
    def test_block_manager_functionality(self):
        """BlockManager 기본 기능 테스트"""
        temp_dir = tempfile.mkdtemp()
        try:
            db_path = os.path.join(temp_dir, "test.db")
            db_manager = DatabaseManager(connection_string=db_path)
            block_manager = BlockManager(db_manager)
            
            # 블록 추가
            result = block_manager.add_block(
                context="테스트 블록",
                keywords=["테스트"],
                tags=["tag1"],
                embedding=[0.1] * 128,
                importance=0.8
            )
            
            self.assertIsNotNone(result)
            self.assertEqual(result["context"], "테스트 블록")
            
            # 검색 테스트
            search_results = block_manager.search_by_keywords(["테스트"])
            self.assertTrue(len(search_results) > 0)
            
            db_manager.close()
            
        finally:
            shutil.rmtree(temp_dir)


if __name__ == '__main__':
    unittest.main(verbosity=2)