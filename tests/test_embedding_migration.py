#!/usr/bin/env python3
"""
임베딩 마이그레이션 테스트

이 모듈은 임베딩 시스템 마이그레이션의 안전성과 정확성을 검증합니다.
"""

import unittest
import tempfile
import os
import sys
import shutil
from pathlib import Path
from typing import List, Dict, Any

# 프로젝트 루트를 path에 추가
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from tests.base_test_case import BaseGreeumTestCase
from greeum.embedding_models import (
    SimpleEmbeddingModel, 
    SentenceTransformerModel,
    get_embedding,
    embedding_registry
)


class TestEmbeddingMigration(BaseGreeumTestCase):
    """임베딩 마이그레이션 테스트"""
    
    def setUp(self):
        """테스트 설정"""
        super().setUp()
        
        # 테스트용 임베딩 모델들
        self.old_model = SimpleEmbeddingModel(dimension=768)
        self.new_model = None
        
        try:
            self.new_model = SentenceTransformerModel()
        except ImportError:
            self.skipTest("Sentence-Transformers not available")
        
        # 테스트용 텍스트들
        self.test_texts = [
            "Machine learning is a subset of artificial intelligence",
            "The weather is nice today",
            "I like to eat pizza with my friends",
            "Database optimization is important for performance",
            "안녕하세요, 한국어 텍스트입니다"
        ]
    
    def test_embedding_consistency_after_migration(self):
        """마이그레이션 후 임베딩 일관성 테스트"""
        for text in self.test_texts:
            # 새 모델로 임베딩 생성
            new_embedding = self.new_model.encode(text)
            
            # 같은 텍스트는 같은 임베딩 생성
            new_embedding_2 = self.new_model.encode(text)
            self.assertEqual(new_embedding, new_embedding_2, 
                           f"Same text should produce same embedding: {text}")
            
            # 차원 검증
            self.assertEqual(len(new_embedding), 768, 
                           f"New embedding should be 768D: {text}")
    
    def test_semantic_similarity_improvement(self):
        """의미적 유사도 개선 테스트"""
        # 유사한 텍스트들
        similar_pairs = [
            ("The weather is nice today", "Today has beautiful weather"),
            ("I like pizza", "Pizza is my favorite food"),
            ("Machine learning is important", "AI and ML are crucial technologies")
        ]
        
        # 다른 텍스트들
        different_pairs = [
            ("The weather is nice today", "I like to eat pizza"),
            ("Machine learning is important", "The weather is sunny")
        ]
        
        for text1, text2 in similar_pairs:
            # 새 모델로 유사도 계산
            emb1 = self.new_model.encode(text1)
            emb2 = self.new_model.encode(text2)
            similarity = self.new_model.similarity(emb1, emb2)
            
            # 의미적으로 유사한 텍스트는 높은 유사도를 가져야 함
            self.assertGreater(similarity, 0.5, 
                             f"Similar texts should have high similarity: '{text1}' vs '{text2}' (similarity: {similarity:.3f})")
        
        for text1, text2 in different_pairs:
            # 새 모델로 유사도 계산
            emb1 = self.new_model.encode(text1)
            emb2 = self.new_model.encode(text2)
            similarity = self.new_model.similarity(emb1, emb2)
            
            # 의미적으로 다른 텍스트는 낮은 유사도를 가져야 함
            self.assertLess(similarity, 0.5, 
                          f"Different texts should have low similarity: '{text1}' vs '{text2}' (similarity: {similarity:.3f})")
    
    def test_multilingual_support(self):
        """다국어 지원 테스트"""
        multilingual_texts = [
            "Hello world",  # English
            "안녕하세요 세계",  # Korean
            "Bonjour le monde",  # French
            "Hola mundo",  # Spanish
            "こんにちは世界",  # Japanese
        ]
        
        embeddings = []
        for text in multilingual_texts:
            embedding = self.new_model.encode(text)
            embeddings.append(embedding)
            
            # 모든 임베딩이 768차원인지 확인
            self.assertEqual(len(embedding), 768, f"Multilingual text should produce 768D embedding: {text}")
            
            # 정규화 확인 (Sentence-Transformers는 정규화하지 않을 수 있음)
            norm = sum(x**2 for x in embedding)**0.5
            # 정규화되지 않은 경우도 허용 (모델에 따라 다름)
            self.assertGreater(norm, 0.0, f"Embedding norm should be positive: {text}")
        
        # 모든 임베딩이 서로 다른지 확인 (같은 언어라도 다른 문장이므로)
        for i in range(len(embeddings)):
            for j in range(i+1, len(embeddings)):
                similarity = self.new_model.similarity(embeddings[i], embeddings[j])
                self.assertLess(similarity, 0.99, 
                              f"Different texts should have different embeddings: {multilingual_texts[i]} vs {multilingual_texts[j]}")
    
    def test_embedding_registry_migration(self):
        """임베딩 레지스트리 마이그레이션 테스트"""
        # 현재 기본 모델 확인
        current_model = embedding_registry.get_model()
        self.assertIsInstance(current_model, SentenceTransformerModel, 
                            "Default model should be SentenceTransformerModel after migration")
        
        # 모델 이름 확인
        model_name = current_model.get_model_name()
        self.assertTrue(model_name.startswith('st_'), 
                       f"Model name should start with 'st_': {model_name}")
        
        # 차원 확인
        self.assertEqual(current_model.get_dimension(), 768, 
                       "Default model should be 768D")
    
    def test_global_embedding_function_migration(self):
        """전역 임베딩 함수 마이그레이션 테스트"""
        text = "Test text for global embedding function"
        
        # 전역 함수 사용
        embedding = get_embedding(text)
        
        # 결과 검증
        self.assertIsInstance(embedding, list, "Global function should return list")
        self.assertEqual(len(embedding), 768, "Global function should return 768D embedding")
        
        # 일관성 검증
        embedding2 = get_embedding(text)
        self.assertEqual(embedding, embedding2, "Same text should produce same embedding")
    
    def test_migration_backward_compatibility(self):
        """마이그레이션 하위 호환성 테스트"""
        # SimpleEmbeddingModel도 여전히 사용 가능해야 함
        simple_model = SimpleEmbeddingModel(dimension=768)
        text = "Backward compatibility test"
        
        simple_embedding = simple_model.encode(text)
        new_embedding = self.new_model.encode(text)
        
        # 둘 다 768차원이어야 함
        self.assertEqual(len(simple_embedding), 768, "Simple model should produce 768D embedding")
        self.assertEqual(len(new_embedding), 768, "New model should produce 768D embedding")
        
        # 차원은 같지만 값은 다를 수 있음 (다른 모델이므로)
        self.assertNotEqual(simple_embedding, new_embedding, 
                          "Different models should produce different embeddings")
    
    def test_embedding_quality_improvement(self):
        """임베딩 품질 개선 테스트"""
        # 의미적으로 유사한 텍스트들
        similar_groups = [
            ["car", "automobile", "vehicle"],
            ["happy", "joyful", "cheerful"],
            ["computer", "laptop", "PC"],
            ["book", "novel", "publication"]
        ]
        
        for group in similar_groups:
            embeddings = [self.new_model.encode(text) for text in group]
            
            # 그룹 내 평균 유사도 계산
            similarities = []
            for i in range(len(embeddings)):
                for j in range(i+1, len(embeddings)):
                    sim = self.new_model.similarity(embeddings[i], embeddings[j])
                    similarities.append(sim)
            
            if similarities:
                avg_similarity = sum(similarities) / len(similarities)
                # 의미적으로 유사한 단어들은 높은 평균 유사도를 가져야 함
                self.assertGreater(avg_similarity, 0.3, 
                                 f"Similar words should have high average similarity: {group} (avg: {avg_similarity:.3f})")
    
    def test_embedding_performance(self):
        """임베딩 성능 테스트"""
        import time
        
        # 성능 테스트용 텍스트
        test_texts = [f"Performance test text {i}" for i in range(50)]
        
        # 배치 인코딩 성능
        start_time = time.time()
        batch_embeddings = self.new_model.batch_encode(test_texts)
        batch_time = time.time() - start_time
        
        # 개별 인코딩 성능
        start_time = time.time()
        individual_embeddings = [self.new_model.encode(text) for text in test_texts]
        individual_time = time.time() - start_time
        
        # 결과 검증
        self.assertEqual(len(batch_embeddings), len(test_texts), "Batch size should match input size")
        self.assertEqual(len(individual_embeddings), len(test_texts), "Individual size should match input size")
        
        # 배치와 개별 결과가 거의 동일해야 함 (부동소수점 정밀도 차이 허용)
        for batch_emb, individual_emb in zip(batch_embeddings, individual_embeddings):
            for b_val, i_val in zip(batch_emb, individual_emb):
                self.assertAlmostEqual(b_val, i_val, places=6, 
                                     msg="Batch and individual results should be nearly identical")
        
        # 성능 로깅 (실제 성능은 환경에 따라 다를 수 있음)
        print(f"Batch encoding time: {batch_time:.3f}s")
        print(f"Individual encoding time: {individual_time:.3f}s")
        print(f"Speedup: {individual_time/batch_time:.2f}x")


class TestMigrationScript(BaseGreeumTestCase):
    """마이그레이션 스크립트 테스트"""
    
    def test_migration_script_import(self):
        """마이그레이션 스크립트 임포트 테스트"""
        try:
            from scripts.embedding_migration_v2 import EmbeddingMigrator
            self.assertTrue(True, "Migration script should be importable")
        except ImportError as e:
            self.fail(f"Failed to import migration script: {e}")
    
    def test_migration_script_initialization(self):
        """마이그레이션 스크립트 초기화 테스트"""
        try:
            from scripts.embedding_migration_v2 import EmbeddingMigrator
            
            # 임시 데이터베이스로 테스트
            tmp_db_path = tempfile.mktemp(suffix='.db')
            try:
                migrator = EmbeddingMigrator(tmp_db_path)
                
                # 초기화는 실패할 수 있음 (Sentence-Transformers 없을 경우)
                # 하지만 객체 생성은 성공해야 함
                self.assertIsInstance(migrator, EmbeddingMigrator)
                
            finally:
                # 임시 파일 정리 (존재하는 경우에만)
                if os.path.exists(tmp_db_path):
                    try:
                        os.unlink(tmp_db_path)
                    except (PermissionError, OSError):
                        pass  # Windows에서 파일이 사용 중일 수 있음
                
        except Exception as e:
            self.fail(f"Failed to initialize migration script: {e}")


if __name__ == '__main__':
    # 테스트 실행
    unittest.main(verbosity=2)
