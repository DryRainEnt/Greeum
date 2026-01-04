"""
STM (Short-Term Memory) slot schemas.

v5.0.0: STM slot status for AI persona development.
"""

from typing import Optional, Dict
from datetime import datetime
from pydantic import BaseModel, Field


class SlotInfo(BaseModel):
    """Information about a single STM slot."""
    slot_name: str = Field(description="Slot name (A, B, C)")
    block_id: Optional[int] = Field(default=None, description="Current anchor block ID")
    branch_id: Optional[str] = Field(default=None, description="Branch ID")
    content_preview: Optional[str] = Field(default=None, description="First 100 chars of content")
    last_accessed: Optional[datetime] = Field(default=None, description="Last access timestamp")
    is_active: bool = Field(default=False, description="Slot has an anchor")


class STMSlotsResponse(BaseModel):
    """Response for all STM slots status."""
    slots: Dict[str, Optional[SlotInfo]] = Field(
        description="STM slots (A, B, C) with their current state"
    )
    active_count: int = Field(description="Number of active slots")


class SlotDetailResponse(BaseModel):
    """Detailed response for a single STM slot."""
    slot: SlotInfo = Field(description="Slot information")
    recent_memories: list = Field(
        default_factory=list,
        description="Recent memories in this slot's branch"
    )
