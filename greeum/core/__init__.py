"""
Greeum Core Memory Engine

This module contains the core components for STM/LTM memory architecture:
- BlockManager: Long-term memory with blockchain-like structure
- STMManager: Short-term memory with TTL-based management
- CacheManager: Waypoint cache for context-relevant retrieval
- PromptWrapper: Automatic prompt composition with memories
- DatabaseManager: Database abstraction layer
- SearchEngine: Advanced multi-layer search with BERT reranking
- VectorIndex: FAISS vector indexing for semantic search
- WorkingMemory: STM working set management
"""

# Core memory components
from .database_manager import DatabaseManager
from .block_manager import BlockManager

# Optional components (may not be available in lightweight version)
try:
    from .stm_manager import STMManager
except ImportError:
    STMManager = None

try:
    from .cache_manager import CacheManager
except ImportError:
    CacheManager = None

try:
    from .prompt_wrapper import PromptWrapper
except ImportError:
    PromptWrapper = None

try:
    from .search_engine import SearchEngine, BertReranker
except ImportError:
    SearchEngine = None
    BertReranker = None

try:
    from .working_memory import STMWorkingSet
except ImportError:
    STMWorkingSet = None

__all__ = [
    "BlockManager",
    "STMManager", 
    "CacheManager",
    "PromptWrapper",
    "DatabaseManager",
    "SearchEngine",
    "BertReranker",
    "STMWorkingSet"
]