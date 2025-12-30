"""
Search endpoints.
"""

import logging
from fastapi import APIRouter, HTTPException, Depends

from ..schemas.search import (
    SearchRequest,
    SearchResponse,
)
from ..services.memory_service import MemoryService, get_memory_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/search", tags=["search"])


@router.post("", response_model=SearchResponse)
async def search_memories(
    request: SearchRequest,
    service: MemoryService = Depends(get_memory_service),
):
    """
    Search memories using semantic similarity.

    Returns ranked results with similarity scores.
    """
    try:
        result = await service.search(
            query=request.query,
            limit=request.limit,
            depth=request.depth,
            slot=request.slot,
        )
        return result
    except Exception as e:
        logger.error(f"Search failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/similar", response_model=SearchResponse)
async def find_similar(
    request: SearchRequest,
    service: MemoryService = Depends(get_memory_service),
):
    """
    Find memories similar to the given query.

    Uses vector similarity for semantic matching.
    """
    try:
        result = await service.search(
            query=request.query,
            limit=request.limit,
            depth=request.depth,
            slot=request.slot,
        )
        return result
    except Exception as e:
        logger.error(f"Similar search failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
