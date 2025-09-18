#!/usr/bin/env python3
"""
최적화된 임베딩 모델 시스템

이 모듈은 REFACTOR 단계에서 개선된 임베딩 시스템을 제공합니다.
주요 개선사항:
- LRU 캐싱으로 성능 최적화
- 강화된 에러 처리
- 설정 관리 개선
- 상세한 로깅
- 메모리 효율성
"""

from abc import ABC, abstractmethod
import numpy as np
import logging
import os
import time
from typing import List, Dict, Optional, Union, Any, Tuple
from functools import lru_cache
from collections import OrderedDict
import threading
from dataclasses import dataclass
from enum import Enum

# 로깅 설정
logger = logging.getLogger(__name__)


class EmbeddingQuality(Enum):
    """임베딩 품질 레벨"""
    EXCELLENT = "excellent"
    GOOD = "good"
    FAIR = "fair"
    POOR = "poor"


@dataclass
class EmbeddingConfig:
    """임베딩 설정"""
    cache_size: int = 1000
    enable_caching: bool = True
    batch_size: int = 32
    max_text_length: int = 512
    enable_logging: bool = True
    performance_monitoring: bool = True


class LRUEmbeddingCache:
    """LRU 캐시를 사용한 임베딩 캐시"""
    
    def __init__(self, max_size: int = 1000):
        self.max_size = max_size
        self.cache = OrderedDict()
        self.hits = 0
        self.misses = 0
        self.lock = threading.RLock()
    
    def get(self, key: str) -> Optional[List[float]]:
        """캐시에서 임베딩 조회"""
        with self.lock:
            if key in self.cache:
                # LRU 업데이트
                value = self.cache.pop(key)
                self.cache[key] = value
                self.hits += 1
                return value
            else:
                self.misses += 1
                return None
    
    def put(self, key: str, value: List[float]) -> None:
        """캐시에 임베딩 저장"""
        with self.lock:
            if key in self.cache:
                # 기존 항목 제거
                self.cache.pop(key)
            elif len(self.cache) >= self.max_size:
                # 가장 오래된 항목 제거
                self.cache.popitem(last=False)
            
            self.cache[key] = value
    
    def clear(self) -> None:
        """캐시 초기화"""
        with self.lock:
            self.cache.clear()
            self.hits = 0
            self.misses = 0
    
    def get_stats(self) -> Dict[str, Any]:
        """캐시 통계 반환"""
        with self.lock:
            total_requests = self.hits + self.misses
            hit_rate = self.hits / total_requests if total_requests > 0 else 0.0
            
            return {
                'size': len(self.cache),
                'max_size': self.max_size,
                'hits': self.hits,
                'misses': self.misses,
                'hit_rate': hit_rate,
                'total_requests': total_requests
            }


class PerformanceMonitor:
    """성능 모니터링"""
    
    def __init__(self, enabled: bool = True):
        self.enabled = enabled
        self.stats = {
            'total_encodings': 0,
            'total_time': 0.0,
            'batch_encodings': 0,
            'batch_time': 0.0,
            'cache_hits': 0,
            'cache_misses': 0
        }
        self.lock = threading.RLock()
    
    def record_encoding(self, time_taken: float, batch_size: int = 1):
        """인코딩 성능 기록"""
        if not self.enabled:
            return
        
        with self.lock:
            self.stats['total_encodings'] += batch_size
            self.stats['total_time'] += time_taken
            
            if batch_size > 1:
                self.stats['batch_encodings'] += batch_size
                self.stats['batch_time'] += time_taken
    
    def record_cache(self, hit: bool):
        """캐시 성능 기록"""
        if not self.enabled:
            return
        
        with self.lock:
            if hit:
                self.stats['cache_hits'] += 1
            else:
                self.stats['cache_misses'] += 1
    
    def get_stats(self) -> Dict[str, Any]:
        """성능 통계 반환"""
        with self.lock:
            stats = self.stats.copy()
            
            if stats['total_encodings'] > 0:
                stats['avg_encoding_time'] = stats['total_time'] / stats['total_encodings']
            else:
                stats['avg_encoding_time'] = 0.0
            
            if stats['batch_encodings'] > 0:
                stats['avg_batch_time'] = stats['batch_time'] / stats['batch_encodings']
            else:
                stats['avg_batch_time'] = 0.0
            
            total_cache_requests = stats['cache_hits'] + stats['cache_misses']
            if total_cache_requests > 0:
                stats['cache_hit_rate'] = stats['cache_hits'] / total_cache_requests
            else:
                stats['cache_hit_rate'] = 0.0
            
            return stats


class EmbeddingModel(ABC):
    """최적화된 임베딩 모델 추상 클래스"""
    
    def __init__(self, config: Optional[EmbeddingConfig] = None):
        self.config = config or EmbeddingConfig()
        self.cache = LRUEmbeddingCache(self.config.cache_size) if self.config.enable_caching else None
        self.monitor = PerformanceMonitor(self.config.performance_monitoring)
        self._model_loaded = False
        self._load_time = 0.0
    
    @abstractmethod
    def _load_model(self) -> None:
        """모델 로드 (구현체에서 구현)"""
        pass
    
    @abstractmethod
    def _encode_impl(self, text: str) -> List[float]:
        """실제 인코딩 구현 (구현체에서 구현)"""
        pass
    
    @abstractmethod
    def get_dimension(self) -> int:
        """임베딩 차원 반환"""
        pass
    
    @abstractmethod
    def get_model_name(self) -> str:
        """모델 이름 반환"""
        pass
    
    def _ensure_model_loaded(self) -> None:
        """모델이 로드되었는지 확인"""
        if not self._model_loaded:
            start_time = time.time()
            self._load_model()
            self._load_time = time.time() - start_time
            self._model_loaded = True
            
            if self.config.enable_logging:
                logger.info(f"Model loaded in {self._load_time:.3f}s: {self.get_model_name()}")
    
    def encode(self, text: str) -> List[float]:
        """
        텍스트를 벡터로 인코딩 (캐싱 포함)
        
        Args:
            text: 인코딩할 텍스트
            
        Returns:
            임베딩 벡터
        """
        if not text or not text.strip():
            raise ValueError("Text cannot be empty")
        
        if len(text) > self.config.max_text_length:
            logger.warning(f"Text too long ({len(text)} chars), truncating to {self.config.max_text_length}")
            text = text[:self.config.max_text_length]
        
        # 캐시 확인
        if self.cache:
            cached_result = self.cache.get(text)
            if cached_result is not None:
                self.monitor.record_cache(True)
                return cached_result
            self.monitor.record_cache(False)
        
        # 모델 로드 확인
        self._ensure_model_loaded()
        
        # 인코딩 수행
        start_time = time.time()
        try:
            result = self._encode_impl(text)
            encoding_time = time.time() - start_time
            
            # 성능 기록
            self.monitor.record_encoding(encoding_time)
            
            # 캐시 저장
            if self.cache:
                self.cache.put(text, result)
            
            if self.config.enable_logging:
                logger.debug(f"Encoded text in {encoding_time:.3f}s: {text[:50]}...")
            
            return result
            
        except Exception as e:
            logger.error(f"Encoding failed for text '{text[:50]}...': {e}")
            raise
    
    def batch_encode(self, texts: List[str]) -> List[List[float]]:
        """
        텍스트 배치를 벡터로 인코딩 (최적화됨)
        
        Args:
            texts: 인코딩할 텍스트 목록
            
        Returns:
            임베딩 벡터 목록
        """
        if not texts:
            return []
        
        # 빈 텍스트 필터링
        valid_texts = [text for text in texts if text and text.strip()]
        if not valid_texts:
            raise ValueError("No valid texts provided")
        
        if len(valid_texts) != len(texts):
            logger.warning(f"Filtered out {len(texts) - len(valid_texts)} empty texts")
        
        # 캐시 확인
        results = []
        uncached_texts = []
        uncached_indices = []
        
        if self.cache:
            for i, text in enumerate(valid_texts):
                cached_result = self.cache.get(text)
                if cached_result is not None:
                    results.append(cached_result)
                    self.monitor.record_cache(True)
                else:
                    results.append(None)  # 플레이스홀더
                    uncached_texts.append(text)
                    uncached_indices.append(i)
                    self.monitor.record_cache(False)
        else:
            uncached_texts = valid_texts
            uncached_indices = list(range(len(valid_texts)))
            results = [None] * len(valid_texts)
        
        # 캐시되지 않은 텍스트들 인코딩
        if uncached_texts:
            self._ensure_model_loaded()
            
            start_time = time.time()
            try:
                uncached_results = self._batch_encode_impl(uncached_texts)
                batch_time = time.time() - start_time
                
                # 성능 기록
                self.monitor.record_encoding(batch_time, len(uncached_texts))
                
                # 결과 저장
                for i, result in zip(uncached_indices, uncached_results):
                    results[i] = result
                    
                    # 캐시 저장
                    if self.cache:
                        self.cache.put(uncached_texts[uncached_indices.index(i)], result)
                
                if self.config.enable_logging:
                    logger.debug(f"Batch encoded {len(uncached_texts)} texts in {batch_time:.3f}s")
                
            except Exception as e:
                logger.error(f"Batch encoding failed: {e}")
                raise
        
        return results
    
    def _batch_encode_impl(self, texts: List[str]) -> List[List[float]]:
        """배치 인코딩 구현 (기본적으로 개별 인코딩)"""
        return [self._encode_impl(text) for text in texts]
    
    def similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """
        두 벡터 간의 코사인 유사도 계산
        
        Args:
            vec1: 첫 번째 벡터
            vec2: 두 번째 벡터
            
        Returns:
            코사인 유사도 (-1 ~ 1)
        """
        if not vec1 or not vec2:
            return 0.0
        
        if len(vec1) != len(vec2):
            logger.warning(f"Vector dimension mismatch: {len(vec1)} vs {len(vec2)}")
            return 0.0
        
        try:
            v1 = np.array(vec1, dtype=np.float32)
            v2 = np.array(vec2, dtype=np.float32)
            
            norm1 = np.linalg.norm(v1)
            norm2 = np.linalg.norm(v2)
            
            if norm1 == 0 or norm2 == 0:
                return 0.0
            
            similarity = float(np.dot(v1, v2) / (norm1 * norm2))
            
            # NaN 체크
            if np.isnan(similarity):
                logger.warning("Similarity calculation resulted in NaN")
                return 0.0
            
            return similarity
            
        except Exception as e:
            logger.error(f"Similarity calculation failed: {e}")
            return 0.0
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """성능 통계 반환"""
        stats = self.monitor.get_stats()
        
        if self.cache:
            cache_stats = self.cache.get_stats()
            stats.update(cache_stats)
        
        stats['model_loaded'] = self._model_loaded
        stats['model_load_time'] = self._load_time
        
        return stats
    
    def clear_cache(self) -> None:
        """캐시 초기화"""
        if self.cache:
            self.cache.clear()
            logger.info("Embedding cache cleared")


class OptimizedSimpleEmbeddingModel(EmbeddingModel):
    """최적화된 간단한 임베딩 모델"""
    
    def __init__(self, dimension: int = 128, config: Optional[EmbeddingConfig] = None):
        super().__init__(config)
        self.dimension = dimension
        self._model_loaded = True  # Simple 모델은 로드가 필요 없음
    
    def _load_model(self) -> None:
        """Simple 모델은 로드가 필요 없음"""
        pass
    
    def _encode_impl(self, text: str) -> List[float]:
        """간단한 해싱 기반 벡터 인코딩"""
        # 일관된 시드 생성
        seed = len(text)
        for char in text:
            seed += ord(char)
        
        # 시드 설정
        np.random.seed(seed % 10000)
        
        # 임베딩 생성
        embedding = np.random.normal(0, 1, self.dimension)
        
        # 정규화
        norm = np.linalg.norm(embedding)
        if norm > 0:
            embedding = embedding / norm
        
        return embedding.tolist()
    
    def get_dimension(self) -> int:
        """임베딩 차원 반환"""
        return self.dimension
    
    def get_model_name(self) -> str:
        """모델 이름 반환"""
        return f"optimized_simple_hash_{self.dimension}"


class OptimizedSentenceTransformerModel(EmbeddingModel):
    """최적화된 Sentence-Transformers 모델"""
    
    def __init__(self, model_name: str = None, config: Optional[EmbeddingConfig] = None):
        super().__init__(config)
        self.model_name = model_name or 'sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2'
        self.model = None
        self.actual_dimension = None
        self.target_dimension = 768
    
    def _load_model(self) -> None:
        """Sentence-Transformers 모델 로드"""
        try:
            from sentence_transformers import SentenceTransformer
            
            self.model = SentenceTransformer(self.model_name)
            self.actual_dimension = self.model.get_sentence_embedding_dimension()
            
            logger.info(f"Sentence-Transformers model loaded: {self.model_name}")
            logger.info(f"Actual dimension: {self.actual_dimension}, Target: {self.target_dimension}")
            
        except ImportError:
            raise ImportError(
                "sentence-transformers가 설치되지 않았습니다.\n"
                "다음 명령어로 설치하세요:\n"
                "  pip install sentence-transformers\n"
                "또는\n"
                "  pip install greeum[full]"
            )
        except Exception as e:
            raise RuntimeError(f"Failed to load Sentence-Transformers model: {e}")
    
    def _encode_impl(self, text: str) -> List[float]:
        """의미적 벡터 인코딩"""
        if not self.model:
            raise RuntimeError("Model not loaded")
        
        # 의미적 임베딩 생성
        embedding = self.model.encode(text, convert_to_numpy=True)
        
        # 차원 조정
        if self.actual_dimension < self.target_dimension:
            # Zero padding
            padded = np.zeros(self.target_dimension, dtype=np.float32)
            padded[:self.actual_dimension] = embedding
            return padded.tolist()
        elif self.actual_dimension > self.target_dimension:
            # Truncate
            return embedding[:self.target_dimension].tolist()
        else:
            return embedding.tolist()
    
    def _batch_encode_impl(self, texts: List[str]) -> List[List[float]]:
        """배치 인코딩 최적화"""
        if not self.model:
            raise RuntimeError("Model not loaded")
        
        # 배치 크기 조정
        batch_size = min(self.config.batch_size, len(texts))
        
        embeddings = self.model.encode(
            texts, 
            convert_to_numpy=True, 
            batch_size=batch_size,
            show_progress_bar=False
        )
        
        # 차원 조정
        if self.actual_dimension < self.target_dimension:
            padded_embeddings = []
            for emb in embeddings:
                padded = np.zeros(self.target_dimension, dtype=np.float32)
                padded[:self.actual_dimension] = emb
                padded_embeddings.append(padded.tolist())
            return padded_embeddings
        elif self.actual_dimension > self.target_dimension:
            return [emb[:self.target_dimension].tolist() for emb in embeddings]
        else:
            return embeddings.tolist()
    
    def get_dimension(self) -> int:
        """임베딩 차원 반환 (패딩된 차원)"""
        return self.target_dimension
    
    def get_model_name(self) -> str:
        """모델 이름 반환"""
        return f"optimized_st_{self.model_name.split('/')[-1]}"
    
    def get_actual_dimension(self) -> int:
        """실제 모델 차원 반환 (패딩 전)"""
        return self.actual_dimension or 0


class OptimizedEmbeddingRegistry:
    """최적화된 임베딩 레지스트리"""
    
    def __init__(self, config: Optional[EmbeddingConfig] = None):
        self.config = config or EmbeddingConfig()
        self.models = {}
        self.default_model = None
        self.lock = threading.RLock()
        
        # 자동 초기화
        self._auto_init()
    
    def _auto_init(self) -> None:
        """최적 모델 자동 초기화"""
        try:
            # 1순위: Sentence-Transformers
            model = OptimizedSentenceTransformerModel(config=self.config)
            self.register_model("sentence-transformer", model, set_as_default=True)
            logger.info("✅ Optimized SentenceTransformer 모델 초기화 성공")
            
        except (ImportError, RuntimeError) as e:
            # 2순위: Simple (Fallback)
            logger.warning(f"⚠️ Sentence-Transformers 초기화 실패: {e}")
            logger.warning("SimpleEmbeddingModel을 사용합니다.")
            
            model = OptimizedSimpleEmbeddingModel(dimension=768, config=self.config)
            self.register_model("simple", model, set_as_default=True)
    
    def register_model(self, name: str, model: EmbeddingModel, set_as_default: bool = False) -> None:
        """임베딩 모델 등록"""
        with self.lock:
            self.models[name] = model
            
            if set_as_default or self.default_model is None:
                self.default_model = name
            
            logger.info(f"Model registered: {name} (default: {set_as_default})")
    
    def get_model(self, name: Optional[str] = None) -> EmbeddingModel:
        """임베딩 모델 가져오기"""
        with self.lock:
            model_name = name or self.default_model
            
            if model_name not in self.models:
                raise ValueError(f"등록되지 않은 임베딩 모델: {model_name}")
            
            return self.models[model_name]
    
    def encode(self, text: str, model_name: Optional[str] = None) -> List[float]:
        """지정한 모델로 텍스트 인코딩"""
        model = self.get_model(model_name)
        return model.encode(text)
    
    def batch_encode(self, texts: List[str], model_name: Optional[str] = None) -> List[List[float]]:
        """지정한 모델로 텍스트 배치 인코딩"""
        model = self.get_model(model_name)
        return model.batch_encode(texts)
    
    def get_all_stats(self) -> Dict[str, Dict[str, Any]]:
        """모든 모델의 통계 반환"""
        with self.lock:
            return {
                name: model.get_performance_stats()
                for name, model in self.models.items()
            }
    
    def clear_all_caches(self) -> None:
        """모든 모델의 캐시 초기화"""
        with self.lock:
            for model in self.models.values():
                model.clear_cache()
            logger.info("All embedding caches cleared")


# 전역 레지스트리 인스턴스
optimized_embedding_registry = OptimizedEmbeddingRegistry()

# 편의 함수들
def get_optimized_embedding(text: str, model_name: Optional[str] = None) -> List[float]:
    """최적화된 임베딩 벡터 반환"""
    return optimized_embedding_registry.encode(text, model_name)

def get_optimized_batch_embeddings(texts: List[str], model_name: Optional[str] = None) -> List[List[float]]:
    """최적화된 배치 임베딩 벡터 반환"""
    return optimized_embedding_registry.batch_encode(texts, model_name)

def get_embedding_stats() -> Dict[str, Any]:
    """임베딩 시스템 통계 반환"""
    return optimized_embedding_registry.get_all_stats()

def clear_embedding_caches() -> None:
    """모든 임베딩 캐시 초기화"""
    optimized_embedding_registry.clear_all_caches()
