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




class EmbeddingRegistry:
    """임베딩 모델 레지스트리"""
    
    def __init__(self):
        """임베딩 레지스트리 초기화"""
        self.models = {}
        self.default_model = None
        
        # 기본 모델 등록
        self.register_model("simple", SimpleEmbeddingModel())
    
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

 