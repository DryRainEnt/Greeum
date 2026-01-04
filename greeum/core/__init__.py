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

# Core memory components - using thread-safe factory pattern
from .thread_safe_db import get_database_manager_class
DatabaseManager = get_database_manager_class()
from .block_manager import BlockManager

# Optional components (may not be available in lightweight version)
import logging
_logger = logging.getLogger(__name__)
_import_warnings = []

try:
    from .stm_manager import STMManager
except ImportError as e:
    STMManager = None
    _import_warnings.append(f"STMManager unavailable: {e}")

try:
    from .cache_manager import CacheManager
except ImportError as e:
    CacheManager = None
    _import_warnings.append(f"CacheManager unavailable: {e}")

try:
    from .prompt_wrapper import PromptWrapper
except ImportError as e:
    PromptWrapper = None
    _import_warnings.append(f"PromptWrapper unavailable: {e}")

try:
    from .search_engine import SearchEngine, BertReranker
except ImportError as e:
    SearchEngine = None
    BertReranker = None
    _import_warnings.append(f"SearchEngine/BertReranker unavailable: {e}")

try:
    from .working_memory import STMWorkingSet
except ImportError as e:
    STMWorkingSet = None
    _import_warnings.append(f"STMWorkingSet unavailable: {e}")

# v5.0: Hybrid Graph Search components
try:
    from .bm25_index import BM25Index, HybridScorer
except ImportError as e:
    BM25Index = None
    HybridScorer = None
    _import_warnings.append(f"BM25Index/HybridScorer unavailable: {e}")

try:
    from .hybrid_graph_search import HybridGraphSearch, ProjectAnchorManager, SearchResult
except ImportError as e:
    HybridGraphSearch = None
    ProjectAnchorManager = None
    SearchResult = None
    _import_warnings.append(f"HybridGraphSearch unavailable: {e}")

# v5.0: Insight Pipeline components
try:
    from .insight_pipeline import InsightPipeline, PipelineResult, store_insight
except ImportError as e:
    InsightPipeline = None
    PipelineResult = None
    store_insight = None
    _import_warnings.append(f"InsightPipeline unavailable: {e}")

try:
    from .project_manager import ProjectManager, Project
except ImportError as e:
    ProjectManager = None
    Project = None
    _import_warnings.append(f"ProjectManager unavailable: {e}")

try:
    from .insight_filter import InsightFilter, FilterResult, is_insight
except ImportError as e:
    InsightFilter = None
    FilterResult = None
    is_insight = None
    _import_warnings.append(f"InsightFilter unavailable: {e}")

# v5.0: Unified LLM-based InsightJudge
try:
    from .insight_judge import (
        InsightJudge, JudgmentResult, get_insight_judge,
        StoreResult, store_with_judgment
    )
except ImportError as e:
    InsightJudge = None
    JudgmentResult = None
    get_insight_judge = None
    StoreResult = None
    store_with_judgment = None
    _import_warnings.append(f"InsightJudge unavailable: {e}")

# 임포트 경고 로깅 (개발 환경에서만)
if _import_warnings:
    for warning in _import_warnings:
        _logger.debug(warning)

__all__ = [
    "BlockManager",
    "STMManager",
    "CacheManager",
    "PromptWrapper",
    "DatabaseManager",
    "SearchEngine",
    "BertReranker",
    "STMWorkingSet",
    # v5.0: Hybrid Graph Search
    "BM25Index",
    "HybridScorer",
    "HybridGraphSearch",
    "ProjectAnchorManager",
    "SearchResult",
    # v5.0: Insight Pipeline
    "InsightPipeline",
    "PipelineResult",
    "store_insight",
    "ProjectManager",
    "Project",
    "InsightFilter",
    "FilterResult",
    "is_insight",
    # v5.0: Unified LLM Judge
    "InsightJudge",
    "JudgmentResult",
    "get_insight_judge",
    "StoreResult",
    "store_with_judgment",
]