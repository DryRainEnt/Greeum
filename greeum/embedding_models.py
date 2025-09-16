from abc import ABC, abstractmethod
import numpy as np
from typing import List, Dict, Optional, Union, Any

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
    
    def __init__(self, dimension: int = 128):
        """
        간단한 임베딩 모델 초기화
        
        Args:
            dimension: 임베딩 차원
        """
        self.dimension = dimension
    
    def encode(self, text: str) -> List[float]:
        """
        텍스트를 간단한 해싱 기반 벡터로 인코딩
        
        Args:
            text: 인코딩할 텍스트
            
        Returns:
            임베딩 벡터
        """
        # 일관된 시드 생성 (텍스트 길이와 문자 기반)
        seed = len(text)
        
        # 각 문자의 유니코드 값 합산
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
        return f"simple_hash_{self.dimension}"


class SentenceTransformerModel(EmbeddingModel):
    """Sentence-Transformers 기반 의미적 임베딩 모델"""

    def __init__(self, model_name: str = None):
        """
        Sentence-Transformer 모델 초기화

        Args:
            model_name: 모델 이름 (기본값: 다국어 지원 모델)
        """
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

        # 기본 모델: 다국어 지원 (한국어 포함), 384차원
        if model_name is None:
            model_name = 'sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2'

        self.model_name = model_name
        self.model = SentenceTransformer(model_name)
        self.dimension = self.model.get_sentence_embedding_dimension()

        # 768차원 호환성을 위한 차원 변환 필요 여부
        self.needs_padding = (self.dimension < 768)
        self.target_dimension = 768  # Greeum 표준 차원

    def encode(self, text: str) -> List[float]:
        """
        텍스트를 의미적 벡터로 인코딩

        Args:
            text: 인코딩할 텍스트

        Returns:
            임베딩 벡터 (768차원으로 패딩됨)
        """
        # 의미적 임베딩 생성
        embedding = self.model.encode(text, convert_to_numpy=True)

        # 차원 조정 (384 -> 768)
        if self.needs_padding:
            # Zero padding to maintain compatibility
            padded = np.zeros(self.target_dimension)
            padded[:self.dimension] = embedding
            return padded.tolist()
        elif len(embedding) > self.target_dimension:
            # Truncate if needed
            return embedding[:self.target_dimension].tolist()
        else:
            return embedding.tolist()

    def batch_encode(self, texts: List[str]) -> List[List[float]]:
        """
        텍스트 배치를 벡터로 인코딩 (성능 최적화)

        Args:
            texts: 인코딩할 텍스트 목록

        Returns:
            임베딩 벡터 목록
        """
        embeddings = self.model.encode(texts, convert_to_numpy=True, batch_size=32)

        if self.needs_padding:
            # Batch padding
            padded_embeddings = []
            for emb in embeddings:
                padded = np.zeros(self.target_dimension)
                padded[:self.dimension] = emb
                padded_embeddings.append(padded.tolist())
            return padded_embeddings
        else:
            return embeddings.tolist()

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
        import logging
        logger = logging.getLogger(__name__)

        try:
            # Sentence-Transformers 시도
            from sentence_transformers import SentenceTransformer
            model = SentenceTransformerModel()
            self.register_model("sentence-transformer", model, set_as_default=True)
            logger.info("✅ SentenceTransformer 모델 자동 초기화 성공")
        except ImportError:
            # Fallback to Simple
            logger.warning(
                "WARNING: sentence-transformers not installed - using SimpleEmbeddingModel"
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
    import logging
    logger = logging.getLogger(__name__)

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
            f"SentenceTransformer 모델 초기화 성공: {model.get_model_name()} "
            f"(실제: {actual_dim}D, 패딩: 768D)"
        )

        return model

    except ImportError as e:
        logger.error(
            "❌ Sentence-Transformer 초기화 실패!\n"
            "sentence-transformers가 설치되지 않았습니다.\n"
            "pip install sentence-transformers를 실행하세요."
        )
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
    import logging
    logger = logging.getLogger(__name__)

    # 이미 모델이 등록되어 있으면 스킵
    if embedding_registry.default_model:
        logger.debug(f"이미 기본 모델이 설정됨: {embedding_registry.default_model}")
        return embedding_registry.default_model

    try:
        # 1순위: Sentence-Transformers
        init_sentence_transformer()
        return "sentence-transformer"

    except ImportError:
        # 2순위: Simple (경고 표시)
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