"""
Memory-related request/response schemas.
"""

from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field


class MemoryAddRequest(BaseModel):
    """Request to add a new memory."""
    content: str = Field(
        description="Memory content to store",
        min_length=1,
        max_length=10000,
        examples=["Greeum v4.0 아키텍처 설계 완료"]
    )
    importance: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Importance score (0.0-1.0)"
    )
    tags: Optional[List[str]] = Field(
        default=None,
        description="Optional tags for categorization"
    )


class MemoryAddResponse(BaseModel):
    """Response after adding a memory.

    v5.0.0: Added InsightJudge fields (is_insight, insight_reason).
    """
    success: bool = Field(description="Operation success status")
    block_index: int = Field(description="Assigned block index")
    branch_id: Optional[str] = Field(default=None, description="Branch ID")
    slot: Optional[str] = Field(default=None, description="STM slot (A, B, C)")
    storage: str = Field(default="LTM", description="Storage type")
    quality_score: float = Field(description="Content quality score")
    duplicate_check: str = Field(description="Duplicate check result")
    is_insight: Optional[bool] = Field(default=None, description="InsightJudge result (v5.0.0)")
    insight_reason: Optional[str] = Field(default=None, description="InsightJudge reason (v5.0.0)")
    suggestions: Optional[List[str]] = Field(default=None, description="Quality suggestions")


class MemoryGetResponse(BaseModel):
    """Response for memory retrieval."""
    block_index: int = Field(description="Block index")
    content: str = Field(description="Memory content")
    timestamp: datetime = Field(description="Creation timestamp")
    importance: float = Field(description="Importance score")
    tags: List[str] = Field(default_factory=list, description="Tags")
    branch_id: Optional[str] = Field(default=None, description="Branch ID")
