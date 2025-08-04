"""
Greeum - 다국어 지원 LLM 독립적인 기억 관리 시스템

This package contains independent modules to provide a human-like 
memory system for Large Language Models.
"""

__version__ = "2.1.1"

# Core components imports
try:
    from .text_utils import process_user_input, extract_keywords_from_text, extract_tags_from_text, compute_text_importance, convert_numpy_types, extract_keywords_advanced
except ImportError:
    pass

# 편의를 위한 별명
try:
    process_text = process_user_input
except NameError:
    pass

# Core memory system (v2.0 structure with backward compatibility)
try:
    from .core import (
        BlockManager, STMManager, CacheManager, PromptWrapper,
        DatabaseManager, SearchEngine, BertReranker, 
        STMWorkingSet
    )
except ImportError:
    pass

# Backward compatibility - keep old import paths working
try:
    from .core.database_manager import DatabaseManager
except ImportError:
    pass

try:
    from .embedding_models import (
        SimpleEmbeddingModel,
        EmbeddingRegistry, get_embedding, register_embedding_model
    )
except ImportError:
    pass

try:
    from .temporal_reasoner import TemporalReasoner, evaluate_temporal_query
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

# Backward compatibility - ensure old imports still work
try:
    from .core.block_manager import BlockManager
except ImportError:
    pass

try:
    from .core.stm_manager import STMManager  
except ImportError:
    pass

try:
    from .core.cache_manager import CacheManager
except ImportError:
    pass

try:
    from .core.prompt_wrapper import PromptWrapper
except ImportError:
    pass

# numpy 타입 변환 유틸리티를 최상위로 노출
try:
    from .text_utils import convert_numpy_types
except ImportError:
    pass

try:
    from .client import (
        MemoryClient, SimplifiedMemoryClient, 
        ClientError, ConnectionFailedError, RequestTimeoutError, APIError
    )
except ImportError:
    pass

try:
    from .working_memory import STMWorkingSet
except ImportError:
    pass

try:
    from .search_engine import SearchEngine, BertReranker
except ImportError:
    pass

# MCP integration (v2.0 feature) - optional import
try:
    from . import mcp
except ImportError:
    # MCP is optional and requires 'pip install greeum[mcp]'
    pass

__all__ = [
    "__version__",
    # Core components
    "BlockManager",
    "STMManager",
    "CacheManager",
    "PromptWrapper",
    
    # Database management
    "DatabaseManager",
    
    # Embedding models
    "EmbeddingModel",
    "SimpleEmbeddingModel", 
    "embedding_registry",
    "get_embedding",
    "register_embedding_model",
    
    # Temporal reasoning
    "TemporalReasoner",
    "evaluate_temporal_query",
    
    # Memory evolution
    "MemoryEvolutionManager",
    
    # Knowledge graph
    "KnowledgeGraphManager",

    # Text utilities
    "process_user_input",
    "process_text",
    "extract_keywords_from_text",
    "extract_tags_from_text",
    "compute_text_importance",
    "convert_numpy_types",
    
    # Client and exceptions
    "MemoryClient",
    "SimplifiedMemoryClient",
    "ClientError",
    "ConnectionFailedError",
    "RequestTimeoutError",
    "APIError",

    # Working memory
    "STMWorkingSet",

    # Search engine
    "SearchEngine",
    "BertReranker",
    "extract_keywords_advanced"
] 