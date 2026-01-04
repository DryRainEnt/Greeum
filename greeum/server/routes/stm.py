"""
STM (Short-Term Memory) slot endpoints.

v5.0.0: STM slot status for AI persona development.
"""

import logging
from fastapi import APIRouter, HTTPException, Depends

from ..schemas.stm import STMSlotsResponse, SlotDetailResponse
from ..services.stm_service import STMService, get_stm_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/stm", tags=["stm"])


@router.get("/slots", response_model=STMSlotsResponse)
async def get_all_slots(
    service: STMService = Depends(get_stm_service),
):
    """
    Get status of all STM slots (A, B, C).

    Returns current anchor information for each slot.
    Useful for understanding active memory contexts.
    """
    try:
        result = await service.get_all_slots()
        return result
    except Exception as e:
        logger.error(f"Failed to get STM slots: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/slots/{slot_name}", response_model=SlotDetailResponse)
async def get_slot_detail(
    slot_name: str,
    service: STMService = Depends(get_stm_service),
):
    """
    Get detailed information for a specific STM slot.

    Includes recent memories from the slot's branch.
    """
    # Validate slot name
    if slot_name.upper() not in ["A", "B", "C"]:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid slot name: {slot_name}. Must be A, B, or C."
        )

    try:
        result = await service.get_slot_detail(slot_name)
        if result is None:
            raise HTTPException(
                status_code=404,
                detail=f"Slot {slot_name.upper()} not found or not initialized"
            )
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get slot detail for {slot_name}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
