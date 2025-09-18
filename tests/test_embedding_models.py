#!/usr/bin/env python3
"""
임베딩 모델 테스트

이 모듈은 Greeum의 임베딩 시스템에 대한 포괄적인 테스트를 제공합니다.
TDD 방식으로 기존 동작을 보장하면서 새로운 기능을 안전하게 도입합니다.
"""

import unittest
import numpy as np
from typing import List, Dict, Any
import os
import sys

# 프로젝트 루트를 path에 추가
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from tests.base_test_case import BaseGreeumTestCase
from greeum.embedding_models import (
    EmbeddingModel,
    SimpleEmbeddingModel,
    SentenceTransformerModel,
    EmbeddingRegistry,
    EmbeddingConfig,
    get_embedding,
    register_embedding_model,
    init_sentence_transformer,
    auto_init_best_model,
    get_embedding_stats,
    clear_embedding_caches,
)


class TestEmbeddingModels(BaseGreeumTestCase):
    """임베딩 모델 기본 테스트"""
    
    def setUp(self):
        """테스트 설정"""
        super().setUp()
        
        # 테스트용 임베딩 모델들
        self.simple_model = SimpleEmbeddingModel(dimension=128)
        self.simple_model_768 = SimpleEmbeddingModel(dimension=768)
        
        # Sentence-Transformers 모델 (가능한 경우)
        self.sentence_model = None
        try:
            self.sentence_model = SentenceTransformerModel()
        except ImportError:
            pass
        
        # 테스트용 텍스트들
        self.test_texts = {
            'simple': "Hello World",
            'korean': "안녕하세요 세계",
            'similar1': "The weather is nice today",
            'similar2': "Today has beautiful weather",
            'different': "I like to eat pizza",
            'empty': "",
            'long': "This is a very long text that contains many words and should be processed correctly by the embedding model. " * 10
        }
    
    def test_simple_embedding_consistency(self):
        """SimpleEmbeddingModel의 일관성 테스트"""
        # 같은 텍스트는 같은 벡터 생성
        text = self.test_texts['simple']
        vec1 = self.simple_model.encode(text)
        vec2 = self.simple_model.encode(text)
        
        self.assertEqual(vec1, vec2, "Same text should produce same embedding")
        
        # 다른 텍스트는 다른 벡터 생성
        vec3 = self.simple_model.encode(self.test_texts['different'])
        self.assertNotEqual(vec1, vec3, "Different text should produce different embedding")
        
        # 차원 검증
        self.assertEqual(len(vec1), 128, "Embedding dimension should be 128")
        self.assertEqual(self.simple_model.get_dimension(), 128, "Model dimension should be 128")
        
        # 모델 이름 검증
        self.assertIn("simple_hash", self.simple_model.get_model_name())
    
    def test_simple_embedding_properties(self):
        """SimpleEmbeddingModel의 기본 속성 테스트"""
        text = self.test_texts['simple']
        embedding = self.simple_model.encode(text)
        
        # 타입 검증
        self.assertIsInstance(embedding, list, "Embedding should be a list")
        self.assertTrue(all(isinstance(x, float) for x in embedding), "All elements should be floats")
        
        # 정규화 검증 (L2 norm이 1에 가까워야 함)
        norm = np.linalg.norm(embedding)
        self.assertAlmostEqual(norm, 1.0, places=5, msg="Embedding should be normalized")
        
        # 범위 검증 (정규분포에서 나온 값들이므로 대부분 -3~3 사이)
        for value in embedding:
            self.assertGreater(value, -5.0, "Embedding values should be reasonable")
            self.assertLess(value, 5.0, "Embedding values should be reasonable")
    
    def test_simple_embedding_different_dimensions(self):
        """다른 차원의 SimpleEmbeddingModel 테스트"""
        # 768차원 모델 테스트
        text = self.test_texts['simple']
        embedding_768 = self.simple_model_768.encode(text)
        
        self.assertEqual(len(embedding_768), 768, "768D model should produce 768D embedding")
        self.assertEqual(self.simple_model_768.get_dimension(), 768, "Model should report 768D")
        
        # 128차원과 768차원은 다르지만 같은 텍스트는 일관성 있어야 함
        embedding_128 = self.simple_model.encode(text)
        self.assertNotEqual(len(embedding_128), len(embedding_768), "Different dimensions should produce different lengths")
    
    def test_simple_embedding_batch_processing(self):
        """SimpleEmbeddingModel의 배치 처리 테스트"""
        texts = [self.test_texts['simple'], self.test_texts['korean'], self.test_texts['different']]
        
        # 개별 인코딩
        individual_embeddings = [self.simple_model.encode(text) for text in texts]
        
        # 배치 인코딩
        batch_embeddings = self.simple_model.batch_encode(texts)
        
        # 결과 비교
        self.assertEqual(len(batch_embeddings), len(texts), "Batch size should match input size")
        
        for i, (individual, batch) in enumerate(zip(individual_embeddings, batch_embeddings)):
            self.assertEqual(individual, batch, f"Individual and batch encoding should be identical for text {i}")
    
    def test_simple_embedding_similarity(self):
        """SimpleEmbeddingModel의 유사도 계산 테스트"""
        # 유사한 텍스트들
        similar_texts = [self.test_texts['similar1'], self.test_texts['similar2']]
        different_text = self.test_texts['different']
        
        # 유사한 텍스트들의 임베딩
        similar_embeddings = [self.simple_model.encode(text) for text in similar_texts]
        
        # 다른 텍스트의 임베딩
        different_embedding = self.simple_model.encode(different_text)
        
        # 유사도 계산
        similarity_similar = self.simple_model.similarity(similar_embeddings[0], similar_embeddings[1])
        similarity_different = self.simple_model.similarity(similar_embeddings[0], different_embedding)
        
        # 유사도는 -1과 1 사이여야 함
        self.assertGreaterEqual(similarity_similar, -1.0, "Similarity should be >= -1")
        self.assertLessEqual(similarity_similar, 1.0, "Similarity should be <= 1")
        self.assertGreaterEqual(similarity_different, -1.0, "Similarity should be >= -1")
        self.assertLessEqual(similarity_different, 1.0, "Similarity should be <= 1")
    
    def test_simple_embedding_edge_cases(self):
        """SimpleEmbeddingModel의 엣지 케이스 테스트"""
        # 빈 문자열
        empty_embedding = self.simple_model.encode(self.test_texts['empty'])
        self.assertEqual(len(empty_embedding), 128, "Empty string should still produce valid embedding")
        
        # 매우 긴 텍스트
        long_embedding = self.simple_model.encode(self.test_texts['long'])
        self.assertEqual(len(long_embedding), 128, "Long text should produce valid embedding")
        
        # 특수 문자
        special_text = "!@#$%^&*()_+-=[]{}|;':\",./<>?"
        special_embedding = self.simple_model.encode(special_text)
        self.assertEqual(len(special_embedding), 128, "Special characters should produce valid embedding")

    def test_embedding_config_and_stats(self):
        """임베딩 구성 및 통계 수집이 동작하는지 확인"""
        config = EmbeddingConfig(cache_size=2, batch_size=2)
        model = SimpleEmbeddingModel(dimension=32, config=config)

        model.encode("cache-test")
        model.encode("cache-test")

        stats = model.get_performance_stats()
        self.assertIn("cache", stats)
        self.assertGreaterEqual(stats["cache"]["max_size"], 2)
        self.assertGreaterEqual(stats.get("total_encodings", 0), 2)

    def test_global_stats_helpers(self):
        """전역 캐시/통계 헬퍼 함수 동작 확인"""
        clear_embedding_caches()
        stats_before = get_embedding_stats()
        default_model_name = next(iter(stats_before))

        cache_info = stats_before[default_model_name].get("cache")
        if cache_info:
            self.assertEqual(cache_info.get("size", 0), 0)

        get_embedding("global-cache-test")
        get_embedding("global-cache-test")

        stats_after = get_embedding_stats()[default_model_name]
        self.assertGreaterEqual(stats_after.get("total_encodings", 0), 2)

        clear_embedding_caches()
        stats_cleared = get_embedding_stats()[default_model_name]
        cache_info = stats_cleared.get("cache")
        if cache_info:
            self.assertEqual(cache_info.get("size", 0), 0)
    
    @unittest.skipIf(True, "Sentence-Transformers not available in test environment")
    def test_sentence_transformer_consistency(self):
        """SentenceTransformerModel의 일관성 테스트"""
        if self.sentence_model is None:
            self.skipTest("Sentence-Transformers not available")
        
        # 같은 텍스트는 같은 벡터 생성
        text = self.test_texts['simple']
        vec1 = self.sentence_model.encode(text)
        vec2 = self.sentence_model.encode(text)
        
        self.assertEqual(vec1, vec2, "Same text should produce same embedding")
        
        # 차원 검증 (768차원)
        self.assertEqual(len(vec1), 768, "Sentence-Transformer should produce 768D embedding")
        self.assertEqual(self.sentence_model.get_dimension(), 768, "Model should report 768D")
    
    @unittest.skipIf(True, "Sentence-Transformers not available in test environment")
    def test_sentence_transformer_semantic_similarity(self):
        """SentenceTransformerModel의 의미적 유사도 테스트"""
        if self.sentence_model is None:
            self.skipTest("Sentence-Transformers not available")
        
        # 유사한 텍스트들
        similar_texts = [self.test_texts['similar1'], self.test_texts['similar2']]
        different_text = self.test_texts['different']
        
        # 유사한 텍스트들의 임베딩
        similar_embeddings = [self.sentence_model.encode(text) for text in similar_texts]
        
        # 다른 텍스트의 임베딩
        different_embedding = self.sentence_model.encode(different_text)
        
        # 유사도 계산
        similarity_similar = self.sentence_model.similarity(similar_embeddings[0], similar_embeddings[1])
        similarity_different = self.sentence_model.similarity(similar_embeddings[0], different_embedding)
        
        # 의미적으로 유사한 텍스트는 높은 유사도를 가져야 함
        self.assertGreater(similarity_similar, 0.5, "Semantically similar texts should have high similarity")
        
        # 의미적으로 다른 텍스트는 낮은 유사도를 가져야 함
        self.assertLess(similarity_different, 0.5, "Semantically different texts should have low similarity")
    
    @unittest.skipIf(True, "Sentence-Transformers not available in test environment")
    def test_sentence_transformer_multilingual(self):
        """SentenceTransformerModel의 다국어 지원 테스트"""
        if self.sentence_model is None:
            self.skipTest("Sentence-Transformers not available")
        
        # 다국어 텍스트들
        texts = [
            self.test_texts['simple'],  # English
            self.test_texts['korean'],  # Korean
            "Bonjour le monde",  # French
            "Hola mundo",  # Spanish
        ]
        
        embeddings = [self.sentence_model.encode(text) for text in texts]
        
        # 모든 임베딩이 768차원인지 확인
        for i, embedding in enumerate(embeddings):
            self.assertEqual(len(embedding), 768, f"Text {i} should produce 768D embedding")
        
        # 모든 임베딩이 정규화되었는지 확인
        for i, embedding in enumerate(embeddings):
            norm = np.linalg.norm(embedding)
            self.assertAlmostEqual(norm, 1.0, places=5, msg=f"Text {i} embedding should be normalized")


class TestEmbeddingRegistry(BaseGreeumTestCase):
    """임베딩 레지스트리 테스트"""
    
    def setUp(self):
        """테스트 설정"""
        super().setUp()
        self.registry = EmbeddingRegistry()
    
    def test_registry_initialization(self):
        """레지스트리 초기화 테스트"""
        # 기본 모델이 설정되어 있는지 확인
        self.assertIsNotNone(self.registry.default_model, "Default model should be set")
        
        # 등록된 모델 목록 확인
        models = self.registry.list_models()
        self.assertIsInstance(models, dict, "Models should be returned as dict")
        self.assertGreater(len(models), 0, "At least one model should be registered")
    
    def test_model_registration(self):
        """모델 등록 테스트"""
        # 새로운 모델 등록
        test_model = SimpleEmbeddingModel(dimension=256)
        self.registry.register_model("test_model", test_model)
        
        # 등록된 모델 확인
        retrieved_model = self.registry.get_model("test_model")
        self.assertEqual(retrieved_model, test_model, "Retrieved model should be the same")
        
        # 모델 목록에 포함되어 있는지 확인
        models = self.registry.list_models()
        self.assertIn("test_model", models, "Test model should be in model list")
    
    def test_model_retrieval(self):
        """모델 조회 테스트"""
        # 기본 모델 조회
        default_model = self.registry.get_model()
        self.assertIsNotNone(default_model, "Default model should be retrievable")
        
        # 존재하지 않는 모델 조회 시 예외 발생
        with self.assertRaises(ValueError):
            self.registry.get_model("nonexistent_model")
    
    def test_registry_encoding(self):
        """레지스트리를 통한 인코딩 테스트"""
        text = "Test text for encoding"
        
        # 기본 모델로 인코딩
        embedding = self.registry.encode(text)
        self.assertIsInstance(embedding, list, "Embedding should be a list")
        self.assertGreater(len(embedding), 0, "Embedding should not be empty")
        
        # 모든 요소가 float인지 확인
        self.assertTrue(all(isinstance(x, float) for x in embedding), "All elements should be floats")
    
    def test_model_switching(self):
        """모델 전환 테스트"""
        # 새로운 모델 등록 및 기본 모델로 설정
        test_model = SimpleEmbeddingModel(dimension=512)
        self.registry.register_model("test_512", test_model, set_as_default=True)
        
        # 기본 모델이 변경되었는지 확인
        self.assertEqual(self.registry.default_model, "test_512", "Default model should be updated")
        
        # 새로운 모델로 인코딩
        text = "Test text"
        embedding = self.registry.encode(text)
        self.assertEqual(len(embedding), 512, "New model should produce 512D embedding")


class TestEmbeddingIntegration(BaseGreeumTestCase):
    """임베딩 시스템 통합 테스트"""
    
    def test_global_embedding_function(self):
        """전역 임베딩 함수 테스트"""
        text = "Integration test text"
        
        # get_embedding 함수 사용
        embedding = get_embedding(text)
        
        self.assertIsInstance(embedding, list, "Global function should return list")
        self.assertGreater(len(embedding), 0, "Global function should return non-empty embedding")
    
    def test_embedding_model_registration(self):
        """임베딩 모델 등록 함수 테스트"""
        # 새로운 모델 등록
        test_model = SimpleEmbeddingModel(dimension=256)
        register_embedding_model("test_global", test_model)
        
        # 등록된 모델 사용
        embedding = get_embedding("Test text", model_name="test_global")
        self.assertEqual(len(embedding), 256, "Registered model should produce correct dimension")
    
    def test_auto_init_best_model(self):
        """최적 모델 자동 초기화 테스트"""
        # 자동 초기화 실행
        model_type = auto_init_best_model()
        
        # 반환된 모델 타입이 유효한지 확인
        self.assertIn(model_type, ["sentence-transformer", "simple"], "Model type should be valid")
        
        # 기본 모델이 설정되었는지 확인
        from greeum.embedding_models import embedding_registry
        self.assertIsNotNone(embedding_registry.default_model, "Default model should be set after auto init")


class TestEmbeddingCompatibility(BaseGreeumTestCase):
    """임베딩 시스템 호환성 테스트"""
    
    def test_block_manager_integration(self):
        """BlockManager와의 통합 테스트"""
        # BlockManager에서 임베딩 사용
        context = "Test context for block manager integration"
        keywords = ["test", "integration"]
        tags = ["test"]
        importance = 0.7
        
        # 임베딩 자동 생성
        embedding = get_embedding(context)
        
        # BlockManager에 블록 추가
        result = self.block_manager.add_block(
            context=context,
            keywords=keywords,
            tags=tags,
            embedding=embedding,
            importance=importance
        )
        
        # 결과 검증
        self.assertIsNotNone(result, "Block should be added successfully")
        if isinstance(result, dict):
            self.assertIn("block_index", result, "Result should contain block_index")
    
    def test_search_engine_integration(self):
        """SearchEngine과의 통합 테스트"""
        # 테스트 데이터 추가
        test_contexts = [
            "Machine learning project with high accuracy",
            "Weather forecast for tomorrow",
            "Database optimization techniques"
        ]
        
        for context in test_contexts:
            embedding = get_embedding(context)
            self.block_manager.add_block(
                context=context,
                keywords=context.split()[:3],
                tags=["test"],
                embedding=embedding,
                importance=0.8
            )
        
        # 검색 테스트
        query = "machine learning"
        query_embedding = get_embedding(query)
        
        # 임베딩 기반 검색
        results = self.block_manager.search_by_embedding(query_embedding, top_k=2)
        
        # 결과 검증
        self.assertIsInstance(results, list, "Search results should be a list")
        self.assertLessEqual(len(results), 2, "Should return at most 2 results")
    
    def test_dimension_compatibility(self):
        """차원 호환성 테스트"""
        # 다양한 차원의 임베딩 생성
        dimensions = [128, 256, 512, 768]
        
        for dim in dimensions:
            model = SimpleEmbeddingModel(dimension=dim)
            embedding = model.encode("Test text")
            
            self.assertEqual(len(embedding), dim, f"Model should produce {dim}D embedding")
            self.assertEqual(model.get_dimension(), dim, f"Model should report {dim}D dimension")


class TestEmbeddingPerformance(BaseGreeumTestCase):
    """임베딩 성능 테스트"""
    
    def setUp(self):
        """성능 테스트 설정"""
        super().setUp()
        self.simple_model = SimpleEmbeddingModel(dimension=128)
    
    def test_encoding_speed(self):
        """인코딩 속도 테스트"""
        import time
        
        text = "Performance test text for encoding speed measurement"
        
        # SimpleEmbeddingModel 속도 테스트
        start_time = time.time()
        for _ in range(100):
            self.simple_model.encode(text)
        simple_time = time.time() - start_time
        
        # 100회 인코딩이 1초 이내에 완료되어야 함
        self.assertLess(simple_time, 1.0, "SimpleEmbeddingModel should be fast enough")
    
    def test_batch_encoding_efficiency(self):
        """배치 인코딩 효율성 테스트"""
        import time
        
        texts = [f"Batch test text {i}" for i in range(50)]
        
        # 개별 인코딩
        start_time = time.time()
        individual_embeddings = [self.simple_model.encode(text) for text in texts]
        individual_time = time.time() - start_time
        
        # 배치 인코딩
        start_time = time.time()
        batch_embeddings = self.simple_model.batch_encode(texts)
        batch_time = time.time() - start_time
        
        # 배치 인코딩이 더 효율적이어야 함 (또는 최소한 비슷해야 함)
        self.assertLessEqual(batch_time, individual_time * 1.1, "Batch encoding should be efficient")
        
        # 결과가 동일해야 함
        self.assertEqual(individual_embeddings, batch_embeddings, "Individual and batch results should be identical")


if __name__ == '__main__':
    # 테스트 실행
    unittest.main(verbosity=2)
