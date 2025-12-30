"""
Memory management endpoints.
"""

import logging
from fastapi import APIRouter, HTTPException, Depends

from ..schemas.memory import (
    MemoryAddRequest,
    MemoryAddResponse,
    MemoryGetResponse,
)
from ..services.memory_service import MemoryService, get_memory_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/memory", tags=["memory"])


@router.post("", response_model=MemoryAddResponse)
async def add_memory(
    request: MemoryAddRequest,
    service: MemoryService = Depends(get_memory_service),
):
    """
    Add a new memory to long-term storage.

    Performs duplicate detection and quality validation before storing.
    """
    try:
        result = await service.add_memory(
            content=request.content,
            importance=request.importance,
            tags=request.tags,
        )
        return result
    except Exception as e:
        logger.error(f"Failed to add memory: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{block_id}", response_model=MemoryGetResponse)
async def get_memory(
    block_id: int,
    service: MemoryService = Depends(get_memory_service),
):
    """
    Retrieve a specific memory by block ID.
    """
    try:
        result = await service.get_memory(block_id)
        if result is None:
            raise HTTPException(status_code=404, detail=f"Memory block {block_id} not found")
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get memory {block_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
