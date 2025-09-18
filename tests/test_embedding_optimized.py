#!/usr/bin/env python3
"""
최적화된 임베딩 모델 테스트

이 모듈은 REFACTOR 단계에서 개선된 임베딩 시스템을 테스트합니다.
"""

import unittest
import time
import tempfile
import os
import sys
from typing import List, Dict, Any

# 프로젝트 루트를 path에 추가
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from tests.base_test_case import BaseGreeumTestCase
from greeum.embedding_models_optimized import (
    OptimizedSimpleEmbeddingModel,
    OptimizedSentenceTransformerModel,
    OptimizedEmbeddingRegistry,
    EmbeddingConfig,
    get_optimized_embedding,
    get_optimized_batch_embeddings,
    get_embedding_stats,
    clear_embedding_caches
)


class TestOptimizedEmbeddingModels(BaseGreeumTestCase):
    """최적화된 임베딩 모델 테스트"""
    
    def setUp(self):
        """테스트 설정"""
        super().setUp()
        
        # 테스트용 설정
        self.config = EmbeddingConfig(
            cache_size=100,
            enable_caching=True,
            batch_size=16,
            max_text_length=256,
            enable_logging=True,
            performance_monitoring=True
        )
        
        # 테스트용 모델들
        self.simple_model = OptimizedSimpleEmbeddingModel(dimension=128, config=self.config)
        
        # Sentence-Transformers 모델 (가능한 경우)
        self.sentence_model = None
        try:
            self.sentence_model = OptimizedSentenceTransformerModel(config=self.config)
        except ImportError:
            pass
        
        # 테스트용 텍스트들
        self.test_texts = [
            "Hello World",
            "안녕하세요 세계",
            "Machine learning is fascinating",
            "The weather is nice today",
            "I like to eat pizza"
        ]
    
    def test_simple_model_basic_functionality(self):
        """Simple 모델 기본 기능 테스트"""
        text = self.test_texts[0]
        
        # 인코딩 테스트
        embedding = self.simple_model.encode(text)
        
        self.assertIsInstance(embedding, list)
        self.assertEqual(len(embedding), 128)
        self.assertTrue(all(isinstance(x, float) for x in embedding))
        
        # 일관성 테스트
        embedding2 = self.simple_model.encode(text)
        self.assertEqual(embedding, embedding2)
        
        # 모델 정보 테스트
        self.assertEqual(self.simple_model.get_dimension(), 128)
        self.assertIn("optimized_simple_hash", self.simple_model.get_model_name())
    
    def test_simple_model_caching(self):
        """Simple 모델 캐싱 테스트"""
        text = self.test_texts[0]
        
        # 첫 번째 인코딩 (캐시 미스)
        start_time = time.time()
        embedding1 = self.simple_model.encode(text)
        first_time = time.time() - start_time
        
        # 두 번째 인코딩 (캐시 히트)
        start_time = time.time()
        embedding2 = self.simple_model.encode(text)
        second_time = time.time() - start_time
        
        # 결과가 동일해야 함
        self.assertEqual(embedding1, embedding2)
        
        # 두 번째가 더 빨라야 함 (캐시 히트)
        self.assertLess(second_time, first_time)
        
        # 캐시 통계 확인
        stats = self.simple_model.get_performance_stats()
        self.assertGreater(stats['cache_hits'], 0)
        self.assertGreater(stats['cache_misses'], 0)
    
    def test_simple_model_batch_encoding(self):
        """Simple 모델 배치 인코딩 테스트"""
        # 배치 인코딩
        embeddings = self.simple_model.batch_encode(self.test_texts)
        
        self.assertEqual(len(embeddings), len(self.test_texts))
        
        for i, embedding in enumerate(embeddings):
            self.assertIsInstance(embedding, list)
            self.assertEqual(len(embedding), 128)
            
            # 개별 인코딩과 비교
            individual_embedding = self.simple_model.encode(self.test_texts[i])
            self.assertEqual(embedding, individual_embedding)
    
    def test_simple_model_performance_monitoring(self):
        """Simple 모델 성능 모니터링 테스트"""
        # 성능 모니터링 초기화
        initial_stats = self.simple_model.get_performance_stats()
        
        # 인코딩 수행
        for text in self.test_texts:
            self.simple_model.encode(text)
        
        # 통계 확인
        final_stats = self.simple_model.get_performance_stats()
        
        self.assertGreater(final_stats['total_encodings'], initial_stats['total_encodings'])
        self.assertGreater(final_stats['total_time'], initial_stats['total_time'])
        self.assertGreater(final_stats['avg_encoding_time'], 0)
    
    def test_simple_model_error_handling(self):
        """Simple 모델 에러 처리 테스트"""
        # 빈 텍스트
        with self.assertRaises(ValueError):
            self.simple_model.encode("")
        
        with self.assertRaises(ValueError):
            self.simple_model.encode("   ")
        
        # 너무 긴 텍스트 (설정에 따라)
        long_text = "x" * (self.config.max_text_length + 100)
        # 경고는 발생하지만 처리되어야 함
        embedding = self.simple_model.encode(long_text)
        self.assertIsInstance(embedding, list)
        self.assertEqual(len(embedding), 128)
    
    def test_simple_model_cache_management(self):
        """Simple 모델 캐시 관리 테스트"""
        # 캐시에 데이터 추가
        for text in self.test_texts:
            self.simple_model.encode(text)
        
        # 캐시 통계 확인
        stats = self.simple_model.get_performance_stats()
        self.assertGreater(stats['size'], 0)
        
        # 캐시 초기화
        self.simple_model.clear_cache()
        
        # 캐시 통계 재확인
        stats_after_clear = self.simple_model.get_performance_stats()
        self.assertEqual(stats_after_clear['size'], 0)
    
    @unittest.skipIf(True, "Sentence-Transformers not available in test environment")
    def test_sentence_transformer_basic_functionality(self):
        """Sentence-Transformer 모델 기본 기능 테스트"""
        if self.sentence_model is None:
            self.skipTest("Sentence-Transformers not available")
        
        text = self.test_texts[0]
        
        # 인코딩 테스트
        embedding = self.sentence_model.encode(text)
        
        self.assertIsInstance(embedding, list)
        self.assertEqual(len(embedding), 768)
        self.assertTrue(all(isinstance(x, float) for x in embedding))
        
        # 일관성 테스트
        embedding2 = self.sentence_model.encode(text)
        self.assertEqual(embedding, embedding2)
        
        # 모델 정보 테스트
        self.assertEqual(self.sentence_model.get_dimension(), 768)
        self.assertIn("optimized_st", self.sentence_model.get_model_name())
    
    @unittest.skipIf(True, "Sentence-Transformers not available in test environment")
    def test_sentence_transformer_semantic_similarity(self):
        """Sentence-Transformer 모델 의미적 유사도 테스트"""
        if self.sentence_model is None:
            self.skipTest("Sentence-Transformers not available")
        
        # 유사한 텍스트들
        similar_texts = [
            "The weather is nice today",
            "Today has beautiful weather"
        ]
        
        # 다른 텍스트
        different_text = "I like to eat pizza"
        
        # 유사도 계산
        emb1 = self.sentence_model.encode(similar_texts[0])
        emb2 = self.sentence_model.encode(similar_texts[1])
        emb3 = self.sentence_model.encode(different_text)
        
        sim_similar = self.sentence_model.similarity(emb1, emb2)
        sim_different = self.sentence_model.similarity(emb1, emb3)
        
        # 유사한 텍스트는 높은 유사도를 가져야 함
        self.assertGreater(sim_similar, 0.5)
        
        # 다른 텍스트는 낮은 유사도를 가져야 함
        self.assertLess(sim_different, 0.5)
    
    @unittest.skipIf(True, "Sentence-Transformers not available in test environment")
    def test_sentence_transformer_batch_optimization(self):
        """Sentence-Transformer 모델 배치 최적화 테스트"""
        if self.sentence_model is None:
            self.skipTest("Sentence-Transformers not available")
        
        # 개별 인코딩 시간 측정
        start_time = time.time()
        individual_embeddings = [self.sentence_model.encode(text) for text in self.test_texts]
        individual_time = time.time() - start_time
        
        # 배치 인코딩 시간 측정
        start_time = time.time()
        batch_embeddings = self.sentence_model.batch_encode(self.test_texts)
        batch_time = time.time() - start_time
        
        # 결과가 동일해야 함
        for ind_emb, batch_emb in zip(individual_embeddings, batch_embeddings):
            for ind_val, batch_val in zip(ind_emb, batch_emb):
                self.assertAlmostEqual(ind_val, batch_val, places=6)
        
        # 배치가 더 효율적이어야 함 (또는 최소한 비슷해야 함)
        self.assertLessEqual(batch_time, individual_time * 1.1)
    
    def test_similarity_calculation(self):
        """유사도 계산 테스트"""
        # 테스트용 벡터들
        vec1 = [1.0, 0.0, 0.0]
        vec2 = [0.0, 1.0, 0.0]
        vec3 = [1.0, 0.0, 0.0]  # vec1과 동일
        
        # 동일한 벡터는 유사도 1
        sim_identical = self.simple_model.similarity(vec1, vec3)
        self.assertAlmostEqual(sim_identical, 1.0, places=5)
        
        # 직교하는 벡터는 유사도 0
        sim_orthogonal = self.simple_model.similarity(vec1, vec2)
        self.assertAlmostEqual(sim_orthogonal, 0.0, places=5)
        
        # 빈 벡터는 유사도 0
        sim_empty = self.simple_model.similarity([], [1.0, 2.0])
        self.assertEqual(sim_empty, 0.0)
        
        # 차원이 다른 벡터는 유사도 0
        sim_different_dim = self.simple_model.similarity([1.0, 2.0], [1.0, 2.0, 3.0])
        self.assertEqual(sim_different_dim, 0.0)


class TestOptimizedEmbeddingRegistry(BaseGreeumTestCase):
    """최적화된 임베딩 레지스트리 테스트"""
    
    def setUp(self):
        """테스트 설정"""
        super().setUp()
        self.config = EmbeddingConfig(cache_size=50, enable_caching=True)
        self.registry = OptimizedEmbeddingRegistry(self.config)
    
    def test_registry_initialization(self):
        """레지스트리 초기화 테스트"""
        # 기본 모델이 설정되어 있는지 확인
        self.assertIsNotNone(self.registry.default_model)
        
        # 모델 목록 확인
        self.assertGreater(len(self.registry.models), 0)
        
        # 기본 모델 조회 가능한지 확인
        default_model = self.registry.get_model()
        self.assertIsNotNone(default_model)
    
    def test_model_registration(self):
        """모델 등록 테스트"""
        # 새로운 모델 등록
        test_model = OptimizedSimpleEmbeddingModel(dimension=256, config=self.config)
        self.registry.register_model("test_model", test_model)
        
        # 등록된 모델 확인
        retrieved_model = self.registry.get_model("test_model")
        self.assertEqual(retrieved_model, test_model)
        
        # 모델 목록에 포함되어 있는지 확인
        self.assertIn("test_model", self.registry.models)
    
    def test_global_encoding_functions(self):
        """전역 인코딩 함수 테스트"""
        text = "Test text for global functions"
        
        # 단일 인코딩
        embedding = get_optimized_embedding(text)
        self.assertIsInstance(embedding, list)
        self.assertGreater(len(embedding), 0)
        
        # 배치 인코딩
        texts = ["Text 1", "Text 2", "Text 3"]
        embeddings = get_optimized_batch_embeddings(texts)
        
        self.assertEqual(len(embeddings), len(texts))
        for embedding in embeddings:
            self.assertIsInstance(embedding, list)
            self.assertGreater(len(embedding), 0)
    
    def test_performance_stats(self):
        """성능 통계 테스트"""
        # 인코딩 수행
        for text in ["Test 1", "Test 2", "Test 3"]:
            get_optimized_embedding(text)
        
        # 통계 조회
        stats = get_embedding_stats()
        
        self.assertIsInstance(stats, dict)
        self.assertGreater(len(stats), 0)
        
        # 각 모델의 통계 확인
        for model_name, model_stats in stats.items():
            self.assertIn('total_encodings', model_stats)
            self.assertIn('total_time', model_stats)
            self.assertIn('avg_encoding_time', model_stats)
    
    def test_cache_management(self):
        """캐시 관리 테스트"""
        # 캐시에 데이터 추가
        for text in ["Cache test 1", "Cache test 2"]:
            get_optimized_embedding(text)
        
        # 캐시 초기화
        clear_embedding_caches()
        
        # 통계 확인 (캐시가 초기화되었는지)
        stats = get_embedding_stats()
        for model_stats in stats.values():
            if 'size' in model_stats:
                self.assertEqual(model_stats['size'], 0)


class TestEmbeddingConfig(BaseGreeumTestCase):
    """임베딩 설정 테스트"""
    
    def test_default_config(self):
        """기본 설정 테스트"""
        config = EmbeddingConfig()
        
        self.assertEqual(config.cache_size, 1000)
        self.assertTrue(config.enable_caching)
        self.assertEqual(config.batch_size, 32)
        self.assertEqual(config.max_text_length, 512)
        self.assertTrue(config.enable_logging)
        self.assertTrue(config.performance_monitoring)
    
    def test_custom_config(self):
        """사용자 정의 설정 테스트"""
        config = EmbeddingConfig(
            cache_size=500,
            enable_caching=False,
            batch_size=16,
            max_text_length=256,
            enable_logging=False,
            performance_monitoring=False
        )
        
        self.assertEqual(config.cache_size, 500)
        self.assertFalse(config.enable_caching)
        self.assertEqual(config.batch_size, 16)
        self.assertEqual(config.max_text_length, 256)
        self.assertFalse(config.enable_logging)
        self.assertFalse(config.performance_monitoring)
    
    def test_config_with_model(self):
        """설정을 사용한 모델 생성 테스트"""
        config = EmbeddingConfig(cache_size=100, enable_caching=True)
        model = OptimizedSimpleEmbeddingModel(dimension=128, config=config)
        
        # 설정이 적용되었는지 확인
        self.assertEqual(model.config.cache_size, 100)
        self.assertTrue(model.config.enable_caching)
        
        # 캐시 기능 테스트
        text = "Config test"
        embedding1 = model.encode(text)
        embedding2 = model.encode(text)  # 캐시 히트
        
        self.assertEqual(embedding1, embedding2)


if __name__ == '__main__':
    # 테스트 실행
    unittest.main(verbosity=2)
