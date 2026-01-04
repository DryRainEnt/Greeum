"""
Branch exploration service.

v5.0.0: Branch traversal for AI persona development.
"""

import logging
from typing import Optional, Dict, Any, List
from datetime import datetime

logger = logging.getLogger(__name__)

# Lazy-loaded instance
_branch_service_instance: Optional["BranchService"] = None


class BranchService:
    """Service layer for branch exploration operations."""

    def __init__(self):
        self._initialized = False
        self._db_manager = None
        self._block_manager = None

    def _ensure_initialized(self):
        """Lazy initialization of Greeum components."""
        if self._initialized:
            return

        try:
            from greeum.core import DatabaseManager
            from greeum.core.block_manager import BlockManager

            self._db_manager = DatabaseManager()
            self._block_manager = BlockManager(self._db_manager)
            self._initialized = True
            logger.info("BranchService initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize BranchService: {e}")
            raise

    def _get_blocks_by_branch(self, branch_id: str, limit: int = 1000) -> List[Dict[str, Any]]:
        """Get blocks belonging to a specific branch by filtering on 'root' field."""
        all_blocks = self._db_manager.get_blocks(limit=limit * 10)  # Fetch more to filter
        return [b for b in all_blocks if b.get("root") == branch_id][:limit]

    async def get_branch_info(self, branch_id: str) -> Optional[Dict[str, Any]]:
        """Get information about a specific branch."""
        self._ensure_initialized()

        try:
            # Get all blocks in this branch
            blocks = self._get_blocks_by_branch(branch_id, limit=1000)

            if not blocks:
                return None

            first_block = min(blocks, key=lambda b: b.get("block_index", 0))
            last_block = max(blocks, key=lambda b: b.get("block_index", 0))

            created_at = None
            if first_block.get("timestamp"):
                try:
                    created_at = datetime.fromisoformat(first_block["timestamp"])
                except (ValueError, TypeError):
                    pass

            return {
                "branch_id": branch_id,
                "memory_count": len(blocks),
                "first_block": first_block.get("block_index"),
                "last_block": last_block.get("block_index"),
                "created_at": created_at,
            }

        except Exception as e:
            logger.warning(f"Failed to get branch info for {branch_id}: {e}")
            return None

    async def get_branch_memories(
        self,
        branch_id: str,
        offset: int = 0,
        limit: int = 20,
    ) -> Optional[Dict[str, Any]]:
        """Get memories from a branch with pagination."""
        self._ensure_initialized()

        try:
            # Get all blocks in this branch (sorted by newest first)
            all_blocks = self._get_blocks_by_branch(branch_id, limit=1000)

            if not all_blocks:
                return None

            # Sort by block_index descending (newest first)
            sorted_blocks = sorted(
                all_blocks,
                key=lambda b: b.get("block_index", 0),
                reverse=True,
            )

            total_count = len(sorted_blocks)

            # Apply pagination
            paginated = sorted_blocks[offset:offset + limit]

            memories = []
            for block in paginated:
                timestamp = None
                if block.get("timestamp"):
                    try:
                        timestamp = datetime.fromisoformat(block["timestamp"])
                    except (ValueError, TypeError):
                        pass

                memories.append({
                    "block_id": block.get("block_index"),
                    "content": block.get("context", ""),
                    "timestamp": timestamp,
                    "importance": block.get("importance", 0.5),
                })

            return {
                "branch_id": branch_id,
                "memories": memories,
                "total_count": total_count,
                "offset": offset,
                "limit": limit,
            }

        except Exception as e:
            logger.warning(f"Failed to get branch memories for {branch_id}: {e}")
            return None

    async def get_memory_neighbors(self, block_id: int) -> Optional[Dict[str, Any]]:
        """Get previous and next memories in the chain."""
        self._ensure_initialized()

        try:
            # Get the current block
            current_block = self._db_manager.get_block_by_index(block_id)
            if not current_block:
                return None

            branch_id = current_block.get("branch_id") or current_block.get("root")

            # Get all blocks in the same branch
            if branch_id:
                all_blocks = self._get_blocks_by_branch(branch_id, limit=1000)
            else:
                # Fallback: get nearby blocks by index
                all_blocks = []

            # Sort by block_index
            sorted_blocks = sorted(all_blocks, key=lambda b: b.get("block_index", 0))

            # Find current position
            current_idx = None
            for i, block in enumerate(sorted_blocks):
                if block.get("block_index") == block_id:
                    current_idx = i
                    break

            previous = None
            next_block = None

            if current_idx is not None:
                if current_idx > 0:
                    prev_block = sorted_blocks[current_idx - 1]
                    previous = self._format_memory_item(prev_block)

                if current_idx < len(sorted_blocks) - 1:
                    next_b = sorted_blocks[current_idx + 1]
                    next_block = self._format_memory_item(next_b)

            return {
                "block_id": block_id,
                "previous": previous,
                "next": next_block,
                "branch_id": branch_id,
            }

        except Exception as e:
            logger.warning(f"Failed to get neighbors for block {block_id}: {e}")
            return None

    def _format_memory_item(self, block: Dict[str, Any]) -> Dict[str, Any]:
        """Format a block as a memory item."""
        timestamp = None
        if block.get("timestamp"):
            try:
                timestamp = datetime.fromisoformat(block["timestamp"])
            except (ValueError, TypeError):
                pass

        return {
            "block_id": block.get("block_index"),
            "content": block.get("context", ""),
            "timestamp": timestamp,
            "importance": block.get("importance", 0.5),
        }


def get_branch_service() -> BranchService:
    """Dependency injection for BranchService."""
    global _branch_service_instance
    if _branch_service_instance is None:
        _branch_service_instance = BranchService()
    return _branch_service_instance
