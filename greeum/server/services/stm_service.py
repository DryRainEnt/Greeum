"""
STM (Short-Term Memory) service for slot management.

v5.0.0: Provides STM slot status for AI persona development.
"""

import logging
from typing import Optional, Dict, Any, List
from datetime import datetime

logger = logging.getLogger(__name__)

# Lazy-loaded instance
_stm_service_instance: Optional["STMService"] = None


class STMService:
    """Service layer for STM slot operations."""

    def __init__(self):
        self._initialized = False
        self._db_manager = None
        self._stm_manager = None
        self._block_manager = None

    def _ensure_initialized(self):
        """Lazy initialization of Greeum components."""
        if self._initialized:
            return

        try:
            from greeum.core import DatabaseManager
            from greeum.core.block_manager import BlockManager
            from greeum.core.stm_manager import STMManager

            self._db_manager = DatabaseManager()
            self._block_manager = BlockManager(self._db_manager)
            self._stm_manager = STMManager(self._db_manager)
            self._initialized = True
            logger.info("STMService initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize STMService: {e}")
            raise

    async def get_all_slots(self) -> Dict[str, Any]:
        """Get status of all STM slots."""
        self._ensure_initialized()

        slots_info = {}
        active_count = 0

        for slot_name in ["A", "B", "C"]:
            slot_data = await self._get_slot_info(slot_name)
            slots_info[slot_name] = slot_data
            if slot_data and slot_data.get("is_active"):
                active_count += 1

        return {
            "slots": slots_info,
            "active_count": active_count,
        }

    async def get_slot_detail(self, slot_name: str) -> Optional[Dict[str, Any]]:
        """Get detailed information for a specific slot."""
        self._ensure_initialized()

        if slot_name.upper() not in ["A", "B", "C"]:
            return None

        slot_info = await self._get_slot_info(slot_name.upper())
        if not slot_info:
            return None

        # Get recent memories from this slot's branch
        recent_memories = []
        if slot_info.get("branch_id"):
            recent_memories = await self._get_branch_memories(
                slot_info["branch_id"], limit=10
            )

        return {
            "slot": slot_info,
            "recent_memories": recent_memories,
        }

    async def _get_slot_info(self, slot_name: str) -> Optional[Dict[str, Any]]:
        """Get information for a single slot."""
        try:
            # Get slot anchor from STM manager
            stm_stats = self._stm_manager.get_stats()
            slot_data = stm_stats.get("slots", {}).get(slot_name, {})

            if not slot_data or not slot_data.get("anchor_block_id"):
                return {
                    "slot_name": slot_name,
                    "block_id": None,
                    "branch_id": None,
                    "content_preview": None,
                    "last_accessed": None,
                    "is_active": False,
                }

            block_id = slot_data.get("anchor_block_id")
            branch_id = slot_data.get("branch_id")

            # Get block content for preview
            content_preview = None
            last_accessed = None

            if block_id is not None:
                block = self._db_manager.get_block_by_index(block_id)
                if block:
                    content = block.get("context", "")
                    content_preview = content[:100] + "..." if len(content) > 100 else content
                    timestamp_str = block.get("timestamp")
                    if timestamp_str:
                        try:
                            last_accessed = datetime.fromisoformat(timestamp_str)
                        except (ValueError, TypeError):
                            pass

            return {
                "slot_name": slot_name,
                "block_id": block_id,
                "branch_id": branch_id,
                "content_preview": content_preview,
                "last_accessed": last_accessed,
                "is_active": True,
            }

        except Exception as e:
            logger.warning(f"Failed to get slot info for {slot_name}: {e}")
            return None

    async def _get_branch_memories(
        self, branch_id: str, limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Get recent memories from a branch."""
        try:
            # Query blocks by branch_id
            blocks = self._db_manager.get_blocks_by_branch(branch_id, limit=limit)

            memories = []
            for block in blocks:
                memories.append({
                    "block_id": block.get("block_index"),
                    "content": block.get("context", ""),
                    "timestamp": block.get("timestamp"),
                    "importance": block.get("importance", 0.5),
                })

            return memories

        except Exception as e:
            logger.warning(f"Failed to get branch memories for {branch_id}: {e}")
            return []


def get_stm_service() -> STMService:
    """Dependency injection for STMService."""
    global _stm_service_instance
    if _stm_service_instance is None:
        _stm_service_instance = STMService()
    return _stm_service_instance
