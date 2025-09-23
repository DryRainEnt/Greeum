from abc import ABC, abstractmethod
import hashlib
import logging
import os
import time
import threading
from dataclasses import dataclass
from enum import Enum
from typing import List, Dict, Optional, Union, Any, Tuple

import numpy as np


logger = logging.getLogger(__name__)


# Cache for loaded SentenceTransformer instances: model key -> (model, dim, needs_padding)
_ST_MODEL_CACHE: Dict[str, Tuple[Any, int, bool]] = {}
_ST_CACHE_LOCK = threading.Lock()


def _sentence_transformer_disabled() -> bool:
    """Return True when SentenceTransformer embeddings should be skipped."""

    value = os.getenv("GREEUM_DISABLE_ST", "")
    return value.lower() in {"1", "true", "yes", "on"}


@dataclass
class EmbeddingConfig:
    """임베딩 모델 동작을 제어하는 구성 값"""

    cache_size: int = 1000
    enable_caching: bool = True
    batch_size: int = 32
    performance_monitoring: bool = True


class EmbeddingQuality(Enum):
    """임베딩 품질 레벨"""

    EXCELLENT = "excellent"
    GOOD = "good"
    FAIR = "fair"
    POOR = "poor"


class PerformanceMonitor:
    """임베딩 인코딩 속도/빈도 측정을 담당"""

    def __init__(self, enabled: bool = True) -> None:
        self.enabled = enabled
        self.lock = threading.RLock()
        self.stats: Dict[str, Union[int, float]] = {
            "total_encodings": 0,
            "total_time": 0.0,
            "cache_hits": 0,
            "cache_misses": 0,
        }

    def record_encoding(self, duration: float) -> None:
        if not self.enabled:
            return
        with self.lock:
            self.stats["total_encodings"] += 1
            self.stats["total_time"] += duration

    def record_cache(self, hit: bool) -> None:
        if not self.enabled:
            return
        with self.lock:
            key = "cache_hits" if hit else "cache_misses"
            self.stats[key] += 1

    def as_dict(self) -> Dict[str, Union[int, float]]:
        if not self.enabled:
            return {}
        with self.lock:
            stats = dict(self.stats)
            if stats["total_encodings"]:
                stats["avg_encoding_time"] = stats["total_time"] / stats["total_encodings"]
            else:
                stats["avg_encoding_time"] = 0.0
            total_cache = stats["cache_hits"] + stats["cache_misses"]
            stats["cache_hit_rate"] = (
                stats["cache_hits"] / total_cache if total_cache else 0.0
            )
            return stats


class LRUEmbeddingCache:
    """간단한 LRU 캐시 구현 (thread-safe)"""

    def __init__(self, max_size: int = 1000) -> None:
        self.max_size = max(0, max_size)
        self._entries: Dict[str, List[float]] = {}
        self._order: List[str] = []
        self.lock = threading.RLock()

    def get(self, key: str) -> Optional[List[float]]:
        if self.max_size == 0:
            return None
        with self.lock:
            if key not in self._entries:
                return None
            # 최근 사용 갱신
            self._order.remove(key)
            self._order.append(key)
            return self._entries[key][:]

    def put(self, key: str, value: List[float]) -> None:
        if self.max_size == 0:
            return
        with self.lock:
            if key in self._entries:
                self._order.remove(key)
            elif len(self._order) >= self.max_size:
                oldest = self._order.pop(0)
                self._entries.pop(oldest, None)
            self._entries[key] = value[:]
            self._order.append(key)

    def clear(self) -> None:
        with self.lock:
            self._entries.clear()
            self._order.clear()

    def stats(self) -> Dict[str, int]:
        with self.lock:
            return {
                "size": len(self._order),
                "max_size": self.max_size,
            }

class EmbeddingModel(ABC):
    """임베딩 모델 추상 클래스"""
    
    @abstractmethod
    def encode(self, text: str) -> List[float]:
        """
        텍스트를 벡터로 인코딩
        
        Args:
            text: 인코딩할 텍스트
            
        Returns:
            임베딩 벡터
        """
        pass
    
    @abstractmethod
    def get_dimension(self) -> int:
        """
        임베딩 차원 반환
        
        Returns:
            임베딩 차원 수
        """
        pass
    
    @abstractmethod
    def get_model_name(self) -> str:
        """
        모델 이름 반환
        
        Returns:
            모델 이름
        """
        pass
    
    def batch_encode(self, texts: List[str]) -> List[List[float]]:
        """
        텍스트 배치를 벡터로 인코딩
        
        Args:
            texts: 인코딩할 텍스트 목록
            
        Returns:
            임베딩 벡터 목록
        """
        return [self.encode(text) for text in texts]
    
    def similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """
        두 벡터 간의 코사인 유사도 계산
        
        Args:
            vec1: 첫 번째 벡터
            vec2: 두 번째 벡터
            
        Returns:
            코사인 유사도 (-1 ~ 1)
        """
        v1 = np.array(vec1)
        v2 = np.array(vec2)
        
        norm1 = np.linalg.norm(v1)
        norm2 = np.linalg.norm(v2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
            
        return float(np.dot(v1, v2) / (norm1 * norm2))


class SimpleEmbeddingModel(EmbeddingModel):
    """간단한 임베딩 모델 (개발용)"""

    def __init__(self, dimension: int = 128, config: Optional[EmbeddingConfig] = None):
        """간단한 임베딩 모델 초기화."""

        self.dimension = dimension
        self.config = config or EmbeddingConfig()
        self._cache = LRUEmbeddingCache(self.config.cache_size) if self.config.enable_caching else None
        self._monitor = PerformanceMonitor(self.config.performance_monitoring)

    def _encode_without_cache(self, text: str) -> List[float]:
        # Deterministic hash-based vector generation (no global RNG mutation)
        bytes_needed = self.dimension * 4  # use 32-bit signed ints for range coverage
        buffer = bytearray()
        counter = 0
        text_bytes = text.encode("utf-8", "ignore")
        prefix = b"greeum.simple"
        while len(buffer) < bytes_needed:
            counter_bytes = counter.to_bytes(4, "big", signed=False)
            digest = hashlib.blake2b(prefix + counter_bytes + text_bytes, digest_size=64)
            buffer.extend(digest.digest())
            counter += 1

        arr = np.frombuffer(buffer[:bytes_needed], dtype=np.uint8).astype(np.float32)
        # Map [0,255] -> [-1,1]
        arr = (arr / 255.0) * 2.0 - 1.0
        norm = np.linalg.norm(arr)
        if norm > 0:
            arr = arr / norm
        return arr.tolist()

    def encode(self, text: str) -> List[float]:
        start = time.perf_counter()
        if self._cache:
            cached = self._cache.get(text)
            if cached is not None:
                self._monitor.record_cache(True)
                self._monitor.record_encoding(time.perf_counter() - start)
                return cached
        self._monitor.record_cache(False)
        vector = self._encode_without_cache(text)
        if self._cache:
            self._cache.put(text, vector)
        self._monitor.record_encoding(time.perf_counter() - start)
        return vector

    def batch_encode(self, texts: List[str]) -> List[List[float]]:
        embeddings: List[List[float]] = []
        batch_start = 0
        batch_size = max(1, self.config.batch_size)
        while batch_start < len(texts):
            batch = texts[batch_start : batch_start + batch_size]
            for text in batch:
                embeddings.append(self.encode(text))
            batch_start += batch_size
        return embeddings

    def clear_cache(self) -> None:
        if self._cache:
            self._cache.clear()

    def get_performance_stats(self) -> Dict[str, Any]:
        stats = self._monitor.as_dict()
        if self._cache:
            stats["cache"] = self._cache.stats()
        stats["dimension"] = self.dimension
        stats["model"] = self.get_model_name()
        return stats
    
    def get_dimension(self) -> int:
        """임베딩 차원 반환"""
        return self.dimension
    
    def get_model_name(self) -> str:
        """모델 이름 반환"""
        return f"simple_hash_{self.dimension}"


class SentenceTransformerModel(EmbeddingModel):
    """Sentence-Transformers 기반 의미적 임베딩 모델 (Lazy Loading)"""

    def __init__(self, model_name: str = None, config: Optional[EmbeddingConfig] = None):
        """
        Sentence-Transformer 모델 초기화 (Lazy Loading)

        Args:
            model_name: 모델 이름 (기본값: 다국어 지원 모델)
        """
        # 기본 모델: 다국어 지원 (한국어 포함), 384차원
        if model_name is None:
            model_name = 'sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2'

        self.model_name = model_name
        self.model = None  # Lazy loading: 실제 사용 시 초기화
        self._dimension = None
        self._needs_padding = None
        self.target_dimension = 768  # Greeum 표준 차원
        self.config = config or EmbeddingConfig()
        self._cache = LRUEmbeddingCache(self.config.cache_size) if self.config.enable_caching else None
        self._monitor = PerformanceMonitor(self.config.performance_monitoring)
        logger.debug("SentenceTransformerModel initialized with lazy loading for: %s", model_name)

    def _ensure_model_loaded(self):
        """모델이 로드되어 있는지 확인하고 필요 시 로드"""
        if self.model is None:
            if _sentence_transformer_disabled():
                raise RuntimeError(
                    "SentenceTransformer usage disabled via GREEUM_DISABLE_ST; "
                    "switching to fallback embedding model."
                )

            logger.info("Loading SentenceTransformer model: %s", self.model_name)

            try:
                from sentence_transformers import SentenceTransformer
            except ImportError:
                raise ImportError(
                    "sentence-transformers가 설치되지 않았습니다.\n"
                    "다음 명령어로 설치하세요:\n"
                    "  pip install sentence-transformers\n"
                    "또는\n"
                    "  pip install greeum[full]"
                )

            cache_dir = os.path.expanduser("~/.cache/sentence_transformers")
            os.makedirs(cache_dir, exist_ok=True)

            device = os.getenv("GREEUM_ST_DEVICE")
            cache_key = f"{self.model_name}@{device or 'auto'}"

            with _ST_CACHE_LOCK:
                cached = _ST_MODEL_CACHE.get(cache_key)
                if cached:
                    self.model, self._dimension, self._needs_padding = cached
                    logger.debug(
                        "Reusing cached SentenceTransformer model %s on device %s",
                        self.model_name,
                        getattr(self.model, "_target_device", None),
                    )
                else:
                    try:
                        model = SentenceTransformer(
                            self.model_name,
                            cache_folder=cache_dir,
                            device=device,
                        )
                    except TypeError:
                        model = SentenceTransformer(self.model_name, cache_folder=cache_dir)

                    self.model = model
                    logger.debug(
                        "SentenceTransformer loaded on device %s",
                        getattr(self.model, "_target_device", None),
                    )
                    self._dimension = self.model.get_sentence_embedding_dimension()
                    self._needs_padding = (self._dimension < 768)
                    _ST_MODEL_CACHE[cache_key] = (self.model, self._dimension, self._needs_padding)

            if self._dimension is None:
                self._dimension = self.model.get_sentence_embedding_dimension()
            if self._needs_padding is None:
                self._needs_padding = (self._dimension < 768)

            logger.info("Model ready: %s (dim: %s)", self.model_name, self._dimension)

    @property
    def dimension(self):
        """차원 정보 (lazy loading)"""
        if self._dimension is None:
            self._ensure_model_loaded()
        return self._dimension

    @property
    def needs_padding(self):
        """패딩 필요 여부 (lazy loading)"""
        if self._needs_padding is None:
            self._ensure_model_loaded()
        return self._needs_padding

    def encode(self, text: str) -> List[float]:
        """
        텍스트를 의미적 벡터로 인코딩

        Args:
            text: 인코딩할 텍스트

        Returns:
            임베딩 벡터 (768차원으로 패딩됨)
        """
        start = time.perf_counter()
        cache_key = text
        if self._cache:
            cached = self._cache.get(cache_key)
            if cached is not None:
                self._monitor.record_cache(True)
                self._monitor.record_encoding(time.perf_counter() - start)
                return cached

        self._monitor.record_cache(False)

        self._ensure_model_loaded()
        embedding = self.model.encode(text, convert_to_numpy=True)

        if self.needs_padding:
            padded = np.zeros(self.target_dimension)
            padded[: self.dimension] = embedding
            embedding = padded
        elif len(embedding) > self.target_dimension:
            embedding = embedding[: self.target_dimension]

        embedding = np.asarray(embedding, dtype=float)
        norm = np.linalg.norm(embedding)
        if norm > 0:
            embedding = embedding / norm
        embedding_list = embedding.tolist()

        if self._cache:
            self._cache.put(cache_key, embedding_list)
        self._monitor.record_encoding(time.perf_counter() - start)
        return embedding_list

    def batch_encode(self, texts: List[str]) -> List[List[float]]:
        """배치 인코딩은 encode를 반복 호출하여 캐시/통계와 일관성을 유지한다."""

        embeddings: List[List[float]] = []
        batch_start = 0
        batch_size = max(1, self.config.batch_size)

        while batch_start < len(texts):
            batch = texts[batch_start : batch_start + batch_size]
            for text in batch:
                embeddings.append(self.encode(text))
            batch_start += batch_size

        return embeddings

    def clear_cache(self) -> None:
        if self._cache:
            self._cache.clear()

    def get_performance_stats(self) -> Dict[str, Any]:
        stats = self._monitor.as_dict()
        if self._cache:
            stats["cache"] = self._cache.stats()
        stats["dimension"] = self.target_dimension
        stats["model"] = self.get_model_name()
        return stats

    def get_dimension(self) -> int:
        """
        임베딩 차원 반환 (패딩된 차원)

        Returns:
            임베딩 차원 수 (768)
        """
        return self.target_dimension

    def get_model_name(self) -> str:
        """
        모델 이름 반환

        Returns:
            모델 이름
        """
        return f"st_{self.model_name.split('/')[-1]}"

    def get_actual_dimension(self) -> int:
        """
        실제 모델 차원 반환 (패딩 전)

        Returns:
            실제 임베딩 차원 수
        """
        # lazy loading을 통해 필요 시 차원 정보 로드
        return self.dimension


class EmbeddingRegistry:
    """임베딩 모델 레지스트리"""
    
    def __init__(self):
        """임베딩 레지스트리 초기화"""
        self.models = {}
        self.default_model = None
        
        # 초기화 시 자동으로 최적 모델 선택
        self._auto_init()

    def _auto_init(self):
        """레지스트리 초기화 시 최적 모델 자동 선택"""
        if _sentence_transformer_disabled():
            logger.info(
                "GREEUM_DISABLE_ST set – defaulting to SimpleEmbeddingModel (hash fallback)."
            )
            self.register_model("simple", SimpleEmbeddingModel(dimension=768), set_as_default=True)
            return
        try:
            # 1순위: Sentence-Transformers (의미 기반)
            model = SentenceTransformerModel()
            self.register_model("sentence-transformer", model, set_as_default=True)
            logger.info("✅ SentenceTransformer 모델 자동 초기화 성공 (의미 기반 검색 활성화)")
        except (ImportError, RuntimeError):
            # 2순위: Simple (Fallback)
            logger.warning(
                "⚠️ WARNING: sentence-transformers unavailable or disabled - using SimpleEmbeddingModel\n"
                "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                "의미 기반 검색이 비활성화됩니다. 다음 기능들이 제대로 작동하지 않습니다:\n"
                "  • 의미 기반 검색\n"
                "  • 슬롯 자동 할당\n"
                "  • 유사 메모리 그룹화\n"
                "\n"
                "해결 방법:\n"
                "  pip install sentence-transformers\n"
                "  또는\n"
                "  pip install greeum[full]\n"
                "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
            )
            self.register_model("simple", SimpleEmbeddingModel(dimension=768), set_as_default=True)

    def register_model(self, name: str, model: EmbeddingModel, set_as_default: bool = False) -> None:
        """
        임베딩 모델 등록

        Args:
            name: 모델 이름
            model: 임베딩 모델 인스턴스
            set_as_default: 기본 모델로 설정할지 여부
        """
        self.models[name] = model
        logger.debug("Registered embedding model '%s' (%s)", name, model.get_model_name())

        if set_as_default or self.default_model is None:
            self.default_model = name
    
    def get_model(self, name: Optional[str] = None) -> EmbeddingModel:
        """
        임베딩 모델 가져오기
        
        Args:
            name: 모델 이름 (None이면 기본 모델)
            
        Returns:
            임베딩 모델 인스턴스
        """
        model_name = name or self.default_model
        
        if model_name not in self.models:
            raise ValueError(f"등록되지 않은 임베딩 모델: {model_name}")
            
        return self.models[model_name]
    
    def list_models(self) -> Dict[str, Dict[str, Any]]:
        """
        등록된 모델 목록 반환
        
        Returns:
            모델 이름과 정보 사전
        """
        return {
            name: {
                "dimension": model.get_dimension(),
                "model_name": model.get_model_name(),
                "is_default": name == self.default_model
            }
            for name, model in self.models.items()
        }
    
    def encode(self, text: str, model_name: Optional[str] = None) -> List[float]:
        """
        지정한 모델로 텍스트 인코딩

        Args:
            text: 인코딩할 텍스트
            model_name: 사용할 모델 이름 (없으면 기본 모델)

        Returns:
            임베딩 벡터
        """
        model = self.get_model(model_name)
        return model.encode(text)

    def clear_caches(self) -> None:
        for model in self.models.values():
            if hasattr(model, "clear_cache"):
                model.clear_cache()

    def stats(self) -> Dict[str, Dict[str, Any]]:
        return {
            name: model.get_performance_stats() if hasattr(model, "get_performance_stats") else {}
            for name, model in self.models.items()
        }


# 전역 레지스트리 인스턴스 생성
embedding_registry = EmbeddingRegistry()

# 간편하게 사용할 수 있는 함수
def get_embedding(text: str, model_name: Optional[str] = None) -> List[float]:
    """
    텍스트의 임베딩 벡터 반환
    
    Args:
        text: 인코딩할 텍스트
        model_name: 사용할 모델 이름 (없으면 기본 모델)
        
    Returns:
        임베딩 벡터
    """
    return embedding_registry.encode(text, model_name)

def register_embedding_model(name: str, model: EmbeddingModel, set_as_default: bool = False) -> None:
    """
    임베딩 모델 등록

    Args:
        name: 모델 이름
        model: 임베딩 모델 인스턴스
        set_as_default: 기본 모델로 설정할지 여부
    """
    embedding_registry.register_model(name, model, set_as_default)


def clear_embedding_caches() -> None:
    """등록된 모든 임베딩 모델 캐시 초기화"""

    embedding_registry.clear_caches()


def get_embedding_stats() -> Dict[str, Dict[str, Any]]:
    """모델별 성능 통계 조회"""

    return embedding_registry.stats()


def force_simple_fallback(set_as_default: bool = True) -> None:
    """강제로 SimpleEmbeddingModel을 기본값으로 등록.

    CLI나 워크플로우가 `GREEUM_DISABLE_ST`를 켰을 때 기존 SentenceTransformer
    레지스트리가 남아 있으면 이후 호출에서 런타임 오류가 발생하므로, 해당
    상황에서 즉시 호출해 해시 기반 임베딩으로 전환한다.
    """

    embedding_registry.register_model(
        "simple",
        SimpleEmbeddingModel(dimension=768),
        set_as_default=set_as_default,
    )


def init_sentence_transformer(model_name: str = None, set_as_default: bool = True) -> SentenceTransformerModel:
    """
    Sentence-Transformer 모델 초기화 및 등록

    Args:
        model_name: 사용할 모델 이름 (None이면 기본 다국어 모델)
        set_as_default: 기본 모델로 설정할지 여부

    Returns:
        초기화된 SentenceTransformerModel 인스턴스

    Raises:
        ImportError: sentence-transformers가 설치되지 않은 경우
    """
    if _sentence_transformer_disabled():
        raise RuntimeError("SentenceTransformer usage disabled via GREEUM_DISABLE_ST.")

    try:
        # 모델 생성
        model = SentenceTransformerModel(model_name)

        # 레지스트리에 등록
        embedding_registry.register_model(
            "sentence-transformer",
            model,
            set_as_default=set_as_default
        )

        # 차원 호환성 경고
        actual_dim = model.get_actual_dimension()
        if actual_dim != 768:
            logger.warning(
                f"모델 차원이 {actual_dim}입니다. "
                f"768차원으로 패딩되어 호환성을 유지합니다."
            )

        logger.info(
            "SentenceTransformer 모델 초기화 성공: %s (실제: %sD, 패딩: 768D)",
            model.get_model_name(),
            actual_dim,
        )

        return model

    except ImportError as e:
        logger.error(
            "❌ Sentence-Transformer 초기화 실패!\n"
            "sentence-transformers가 설치되지 않았습니다.\n"
            "pip install sentence-transformers를 실행하세요."
        )
        raise
    except RuntimeError as e:
        logger.warning(str(e))
        raise


def init_openai(api_key: str = None, model_name: str = "text-embedding-ada-002", set_as_default: bool = True):
    """
    OpenAI 임베딩 모델 초기화 (스텁 - 향후 구현)

    Args:
        api_key: OpenAI API 키
        model_name: 사용할 모델 이름
        set_as_default: 기본 모델로 설정할지 여부
    """
    raise NotImplementedError("OpenAI 임베딩은 아직 구현되지 않았습니다.")


def auto_init_best_model() -> str:
    """
    사용 가능한 최선의 모델 자동 초기화

    Returns:
        초기화된 모델 타입 ("sentence-transformer" | "simple")
    """
    # 이미 모델이 등록되어 있으면 스킵
    if embedding_registry.default_model:
        logger.debug(f"이미 기본 모델이 설정됨: {embedding_registry.default_model}")
        return embedding_registry.default_model

    try:
        # 1순위: Sentence-Transformers (의미 기반)
        init_sentence_transformer()
        logger.info("✅ Sentence-Transformers 모델 초기화 성공 (의미 기반 검색 활성화)")
        return "sentence-transformer"

    except (ImportError, RuntimeError):
        # 2순위: Simple (Fallback)
        logger.warning(
            "⚠️  WARNING: Using SimpleEmbeddingModel (random vectors)\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "sentence-transformers가 설치되지 않아 랜덤 임베딩을 사용합니다.\n"
            "이로 인해 다음 기능들이 제대로 작동하지 않습니다:\n"
            "  • 의미 기반 검색\n"
            "  • 슬롯 자동 할당\n"
            "  • 유사 메모리 그룹화\n"
            "\n"
            "해결 방법:\n"
            "  pip install sentence-transformers\n"
            "  또는\n"
            "  pip install greeum[full]\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        )
        embedding_registry.register_model(
            "simple",
            SimpleEmbeddingModel(dimension=768),
            set_as_default=True
        )
        return "simple"


# 모듈 로드 시 자동 실행 (임시 비활성화 - 명시적 초기화 권장)
# auto_init_best_model()
