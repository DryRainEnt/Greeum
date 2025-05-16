"""
Greeum - LLM-Independent Memory System with Multilingual Support

This package contains independent modules to provide a human-like 
memory system for Large Language Models.
"""

__version__ = "0.5.0"

# Core components imports
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

# Original components (for compatibility)
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
    from .text_utils import process_user_input, extract_keywords, extract_tags, compute_text_importance
except ImportError:
    pass

# 편의를 위한 별명
process_text = process_user_input

__all__ = [
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
    "SentenceTransformerEmbedding",
    "OpenAIEmbedding",
    "embedding_registry",
    "get_embedding",
    "register_embedding_model",
    "init_sentence_transformer",
    "init_openai",
    
    # Temporal reasoning
    "TemporalReasoner",
    "evaluate_temporal_query",
    
    # Memory evolution
    "MemoryEvolutionManager",
    
    # Knowledge graph
    "KnowledgeGraphManager",
] 