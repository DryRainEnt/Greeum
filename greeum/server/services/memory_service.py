"""
Memory service - wraps core Greeum functionality for the API.

v5.0.0: InsightJudge integration for LLM-based filtering.
"""

import os
import time
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

# InsightJudge 사용 여부 (환경변수로 제어)
_USE_INSIGHT_FILTER = os.environ.get("GREEUM_USE_INSIGHT_FILTER", "1") == "1"

# Lazy-loaded components
_service_instance: Optional["MemoryService"] = None


class MemoryService:
    """Service layer for memory operations.

    v5.0.0: InsightJudge integration for LLM-based content filtering.
    """

    def __init__(self, use_insight_filter: bool = _USE_INSIGHT_FILTER):
        self._initialized = False
        self._db_manager = None
        self._block_manager = None
        self._stm_manager = None
        self._duplicate_detector = None
        self._quality_validator = None
        self._insight_judge = None
        self.use_insight_filter = use_insight_filter

    def _ensure_initialized(self):
        """Lazy initialization of Greeum components."""
        if self._initialized:
            return

        try:
            from greeum.core import DatabaseManager
            from greeum.core.block_manager import BlockManager
            from greeum.core.stm_manager import STMManager
            from greeum.core.duplicate_detector import DuplicateDetector
            from greeum.core.quality_validator import QualityValidator

            self._db_manager = DatabaseManager()
            self._block_manager = BlockManager(self._db_manager)
            self._stm_manager = STMManager(self._db_manager)
            self._duplicate_detector = DuplicateDetector(self._db_manager)
            self._quality_validator = QualityValidator()

            # InsightJudge 초기화 (v5.0.0)
            if self.use_insight_filter:
                try:
                    from greeum.core.insight_judge import get_insight_judge
                    self._insight_judge = get_insight_judge()
                    # BlockManager 검색 함수 연결
                    if hasattr(self._block_manager, 'search'):
                        self._insight_judge.set_search_func(
                            lambda q, limit: self._block_manager.search(q, limit=limit)
                        )
                    logger.info("InsightJudge initialized successfully")
                except Exception as e:
                    logger.warning(f"InsightJudge initialization failed: {e}")
                    self._insight_judge = None

            self._initialized = True
            logger.info("MemoryService initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize MemoryService: {e}")
            raise

    async def add_memory(
        self,
        content: str,
        importance: float = 0.5,
        tags: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Add a new memory block.

        v5.0.0: InsightJudge LLM-based filtering (명시적 실패 정책).
        """
        self._ensure_initialized()

        # Step 1: InsightJudge LLM 필터링 (v5.0.0)
        if self.use_insight_filter and self._insight_judge:
            try:
                judgment = self._insight_judge.judge(content)
                if not judgment.is_insight:
                    return {
                        "success": False,
                        "block_index": -1,
                        "storage": "LTM",
                        "quality_score": 0.0,
                        "duplicate_check": "skipped",
                        "is_insight": False,
                        "insight_reason": judgment.insight_reason,
                        "suggestions": [],
                    }
            except RuntimeError as e:
                # LLM 서버 미사용 시 명시적 실패
                logger.error(f"InsightJudge unavailable: {e}")
                raise RuntimeError(f"InsightJudge LLM server unavailable: {e}")

        # Step 2: Duplicate check
        dup_result = self._duplicate_detector.check_duplicate(content)
        if dup_result.get("is_duplicate"):
            return {
                "success": False,
                "block_index": -1,
                "storage": "LTM",
                "quality_score": 0.0,
                "duplicate_check": "failed",
                "suggestions": [f"Similar to block #{dup_result.get('similar_memories', [{}])[0].get('block_index', 'unknown')}"],
            }

        # Quality validation
        quality_result = self._quality_validator.validate_memory_quality(content, importance)

        # Process content to extract keywords and embedding
        try:
            from greeum.text_utils import process_user_input
            processed = process_user_input(content)
            keywords = processed.get("keywords", [])
            embedding = processed.get("embedding", [])
        except Exception as e:
            logger.warning(f"Failed to process content: {e}")
            keywords = []
            embedding = []

        # Add to block manager
        block_data = self._block_manager.add_block(
            context=content,
            keywords=keywords,
            tags=tags or [],
            embedding=embedding,
            importance=importance,
        )

        # branch_id는 core에서 'root' 또는 'slot'으로 관리됨
        branch_id = None
        if block_data:
            branch_id = block_data.get("root") or block_data.get("slot")

        return {
            "success": True,
            "block_index": block_data.get("block_index", -1) if block_data else -1,
            "branch_id": branch_id,
            "slot": block_data.get("slot") if block_data else None,
            "storage": "LTM",
            "quality_score": quality_result.get("quality_score", 0.0),
            "duplicate_check": "passed",
            "is_insight": True,  # InsightJudge 통과 또는 비활성화
            "insight_reason": None,
            "suggestions": quality_result.get("suggestions", []),
        }

    async def get_memory(self, block_id: int) -> Optional[Dict[str, Any]]:
        """Get a specific memory block."""
        self._ensure_initialized()

        block = self._db_manager.get_block_by_index(block_id)
        if block is None:
            return None

        return {
            "block_index": block.get("block_index", block_id),
            "content": block.get("context", ""),
            "timestamp": datetime.fromisoformat(block.get("timestamp", datetime.now().isoformat())),
            "importance": block.get("importance", 0.5),
            "tags": block.get("tags", []),
            "branch_id": block.get("branch_id"),
        }

    async def search(
        self,
        query: str,
        limit: int = 5,
        depth: Optional[int] = None,
        slot: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Search memories."""
        self._ensure_initialized()

        start_time = time.time()

        # Use block manager search
        results = self._block_manager.search(query, limit=limit)

        elapsed_ms = (time.time() - start_time) * 1000

        formatted_results = []
        for r in results:
            # branch_id는 core에서 'root' 또는 'slot'으로 관리됨
            branch_id = r.get("root") or r.get("slot")
            formatted_results.append({
                "block_index": r.get("block_index", 0),
                "content": r.get("context", ""),
                "timestamp": datetime.fromisoformat(r.get("timestamp", datetime.now().isoformat())),
                "similarity": r.get("similarity", 0.0),
                "branch_id": branch_id,
                "slot": r.get("slot"),
                "importance": r.get("importance", 0.5),
            })

        return {
            "results": formatted_results,
            "search_stats": {
                "branches_searched": 1,
                "blocks_scanned": len(results),
                "elapsed_ms": elapsed_ms,
            },
        }

    async def get_stats(self) -> Dict[str, Any]:
        """Get memory statistics."""
        self._ensure_initialized()

        # Get block count - handle different DB manager types
        try:
            if hasattr(self._db_manager, 'count_blocks'):
                total_blocks = self._db_manager.count_blocks()
            elif hasattr(self._db_manager, 'run_serialized'):
                # ThreadSafeDatabaseManager - count via get_last_block_info
                last_info = self._db_manager.get_last_block_info()
                total_blocks = (last_info.get("block_index", -1) + 1) if last_info else 0
            else:
                total_blocks = 0
        except Exception as e:
            logger.warning(f"Failed to count blocks: {e}")
            total_blocks = 0

        # Get STM stats
        try:
            stm_stats = self._stm_manager.get_stats()
        except Exception as e:
            logger.warning(f"Failed to get STM stats: {e}")
            stm_stats = {}

        # Get database size
        db_path = None
        if hasattr(self._db_manager, 'db_path'):
            db_path = Path(self._db_manager.db_path)
        elif hasattr(self._db_manager, '_db_path'):
            db_path = Path(self._db_manager._db_path)

        db_size_mb = 0.0
        if db_path and db_path.exists():
            db_size_mb = db_path.stat().st_size / (1024 * 1024)

        return {
            "total_blocks": total_blocks,
            "active_branches": stm_stats.get("active_slots", 0),
            "stm_slots": stm_stats,
            "database_size_mb": round(db_size_mb, 2),
            "embedding_model": "sentence-transformers",
        }

    async def run_doctor(self, auto_fix: bool = True) -> Dict[str, Any]:
        """Run system diagnostics."""
        self._ensure_initialized()

        # Basic health check
        try:
            block_count = self._db_manager.count_blocks()
            return {
                "status": "healthy",
                "checks": {
                    "database": "ok",
                    "block_count": block_count,
                    "stm": "ok",
                },
                "fixes_applied": [],
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "checks": {
                    "database": f"error: {e}",
                },
                "fixes_applied": [],
            }


def get_memory_service() -> MemoryService:
    """Dependency injection for MemoryService."""
    global _service_instance
    if _service_instance is None:
        _service_instance = MemoryService()
    return _service_instance
