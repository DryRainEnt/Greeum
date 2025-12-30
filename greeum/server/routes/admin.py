"""
Admin and statistics endpoints.
"""

import logging
from typing import Optional
from fastapi import APIRouter, HTTPException, Depends

from ..schemas.common import StatsResponse
from ..services.memory_service import MemoryService, get_memory_service

logger = logging.getLogger(__name__)
router = APIRouter(tags=["admin"])


@router.get("/stats", response_model=StatsResponse)
async def get_stats(
    service: MemoryService = Depends(get_memory_service),
):
    """
    Get memory system statistics.
    """
    try:
        return await service.get_stats()
    except Exception as e:
        logger.error(f"Failed to get stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/admin/doctor")
async def system_doctor(
    auto_fix: bool = True,
    service: MemoryService = Depends(get_memory_service),
):
    """
    Run system diagnostics and optionally fix issues.
    """
    try:
        result = await service.run_doctor(auto_fix=auto_fix)
        return result
    except Exception as e:
        logger.error(f"Doctor failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
