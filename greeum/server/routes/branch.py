"""
Branch exploration endpoints.

v5.0.0: Branch traversal for AI persona development.
"""

import logging
from fastapi import APIRouter, HTTPException, Depends, Query

from ..schemas.branch import (
    BranchInfoResponse,
    BranchMemoriesResponse,
    NeighborsResponse,
)
from ..services.branch_service import BranchService, get_branch_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/branch", tags=["branch"])


@router.get("/{branch_id}", response_model=BranchInfoResponse)
async def get_branch_info(
    branch_id: str,
    service: BranchService = Depends(get_branch_service),
):
    """
    Get information about a specific branch.

    Returns memory count, first/last block IDs, and creation time.
    """
    try:
        result = await service.get_branch_info(branch_id)
        if result is None:
            raise HTTPException(
                status_code=404,
                detail=f"Branch {branch_id} not found"
            )
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get branch info for {branch_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{branch_id}/memories", response_model=BranchMemoriesResponse)
async def get_branch_memories(
    branch_id: str,
    offset: int = Query(default=0, ge=0, description="Pagination offset"),
    limit: int = Query(default=20, ge=1, le=100, description="Results per page"),
    service: BranchService = Depends(get_branch_service),
):
    """
    Get memories from a specific branch.

    Returns paginated list of memories, sorted by newest first.
    """
    try:
        result = await service.get_branch_memories(branch_id, offset=offset, limit=limit)
        if result is None:
            raise HTTPException(
                status_code=404,
                detail=f"Branch {branch_id} not found"
            )
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get branch memories for {branch_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Note: This endpoint is under /memory prefix in routes/memory.py
# But for clarity, we also add a branch-related endpoint here
@router.get("/memory/{block_id}/neighbors", response_model=NeighborsResponse)
async def get_memory_neighbors(
    block_id: int,
    service: BranchService = Depends(get_branch_service),
):
    """
    Get previous and next memories in the chain.

    Useful for traversing memory sequences.
    """
    try:
        result = await service.get_memory_neighbors(block_id)
        if result is None:
            raise HTTPException(
                status_code=404,
                detail=f"Memory block {block_id} not found"
            )
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get neighbors for block {block_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
