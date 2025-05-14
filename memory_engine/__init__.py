"""
MemoryBlockEngine - LLM 독립적 메모리 시스템

이 패키지는 LLM에 인간과 유사한 기억 시스템을 제공하기 위한 
독립적인 모듈을 포함하고 있습니다.
"""

__version__ = "0.1.0"

# 핵심 컴포넌트 임포트
try:
    from .database_manager import DatabaseManager
except ImportError:
    pass

try:
    from .embedding_models import (
        SimpleEmbeddingModel, SentenceTransformerEmbedding, OpenAIEmbedding,
        EmbeddingRegistry, get_embedding, register_embedding_model,
        init_sentence_transformer, init_openai
    )
except ImportError:
    pass

try:
    from .temporal_reasoner import TemporalReasoner
except ImportError:
    pass

try:
    from .memory_evolution import MemoryEvolutionManager
except ImportError:
    pass

try:
    from .knowledge_graph import KnowledgeGraphManager
except ImportError:
    pass

# 기존 컴포넌트 (호환성 유지)
try:
    from .block_manager import BlockManager
except ImportError:
    pass

try:
    from .stm_manager import STMManager
except ImportError:
    pass

try:
    from .cache_manager import CacheManager
except ImportError:
    pass

try:
    from .prompt_wrapper import PromptWrapper
except ImportError:
    pass

try:
    from .text_utils import process_user_input
except ImportError:
    pass

__all__ = [
    # 코어 컴포넌트
    "BlockManager",
    "STMManager",
    "CacheManager",
    "PromptWrapper",
    
    # 데이터베이스 관리
    "DatabaseManager",
    
    # 임베딩 모델
    "EmbeddingModel",
    "SimpleEmbeddingModel", 
    "SentenceTransformerEmbedding",
    "OpenAIEmbedding",
    "embedding_registry",
    "get_embedding",
    "register_embedding_model",
    "init_sentence_transformer",
    "init_openai",
    
    # 시간적 추론
    "TemporalReasoner",
    "evaluate_temporal_query",
    
    # 기억 진화
    "MemoryEvolutionManager",
    
    # 지식 그래프
    "KnowledgeGraphManager",
] 