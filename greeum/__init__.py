"""
Greeum v5.1.0 - LLM-Integrated Memory System with Intelligent Filtering

Features:
- InsightJudge: LLM-based content filtering (no pattern matching)
- HybridGraphSearch: BM25 + Vector search fusion
- Branch-aware storage with LLM classification
- GraphIndex beam search and spreading activation
- STM/LTM consolidation for LLMs with human-like memory capabilities
- Remote server connection with API key authentication
"""

__version__ = "5.1.0"

# Main Interface (v3.0+)
from .core.context_memory import ContextMemorySystem

# Core components
from .core.block_manager import BlockManager
from .core.stm_manager import STMManager
from .core.cache_manager import CacheManager
from .core.prompt_wrapper import PromptWrapper
from .core.database_manager import DatabaseManager

# Search engines
from .core.smart_search_engine import SmartSearchEngine
from .core.ltm_links_cache import LTMLinksCache, create_neighbor_link, calculate_link_weight

# Anchors
from .anchors.auto_movement import AutoAnchorMovement

# Text utilities
try:
    from .text_utils import (
        process_user_input, extract_keywords_from_text,
        extract_tags_from_text, compute_text_importance,
        convert_numpy_types, extract_keywords_advanced
    )
    process_text = process_user_input  # Alias
except ImportError:
    pass

# Embedding models
try:
    from .embedding_models import (
        SimpleEmbeddingModel,
        EmbeddingRegistry, get_embedding, register_embedding_model
    )
except ImportError:
    pass

# Optional modules
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

# Client (legacy compatibility - will be deprecated)
try:
    from .client import (
        MemoryClient, SimplifiedMemoryClient,
        ClientError, ConnectionFailedError, RequestTimeoutError, APIError
    )
except ImportError:
    pass

# New client (v5.1.0+)
try:
    from .client import GreeumClient, GreeumHTTPClient
except ImportError:
    pass

# MCP integration - optional
try:
    from . import mcp
except (ImportError, AttributeError):
    pass

__all__ = [
    "__version__",
    "ContextMemorySystem",

    # Core components
    "BlockManager",
    "STMManager",
    "CacheManager",
    "PromptWrapper",
    "DatabaseManager",

    # Search
    "SmartSearchEngine",
    "LTMLinksCache",
    "create_neighbor_link",
    "calculate_link_weight",

    # Anchors
    "AutoAnchorMovement",

    # Embedding models
    "SimpleEmbeddingModel",
    "EmbeddingRegistry",
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
    "extract_keywords_advanced",

    # Client (legacy)
    "MemoryClient",
    "SimplifiedMemoryClient",
    "ClientError",
    "ConnectionFailedError",
    "RequestTimeoutError",
    "APIError",

    # Client (new)
    "GreeumClient",
    "GreeumHTTPClient",
] 
