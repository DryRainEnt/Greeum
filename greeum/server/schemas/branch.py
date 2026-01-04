"""
Branch exploration schemas.

v5.0.0: Branch traversal for AI persona development.
"""

from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field


class MemoryItem(BaseModel):
    """A memory item in a branch."""
    block_id: int = Field(description="Block index")
    content: str = Field(description="Memory content")
    timestamp: Optional[datetime] = Field(default=None, description="Creation timestamp")
    importance: float = Field(default=0.5, description="Importance score")


class BranchInfoResponse(BaseModel):
    """Response for branch information."""
    branch_id: str = Field(description="Branch identifier")
    memory_count: int = Field(description="Total memories in branch")
    first_block: Optional[int] = Field(default=None, description="First block ID")
    last_block: Optional[int] = Field(default=None, description="Last block ID")
    created_at: Optional[datetime] = Field(default=None, description="Branch creation time")


class BranchMemoriesResponse(BaseModel):
    """Response for memories in a branch."""
    branch_id: str = Field(description="Branch identifier")
    memories: List[MemoryItem] = Field(default_factory=list, description="Memories in the branch")
    total_count: int = Field(description="Total memories in branch")
    offset: int = Field(default=0, description="Current offset")
    limit: int = Field(default=20, description="Results per page")


class NeighborsResponse(BaseModel):
    """Response for memory neighbors (chain traversal)."""
    block_id: int = Field(description="Current block ID")
    previous: Optional[MemoryItem] = Field(default=None, description="Previous memory in chain")
    next: Optional[MemoryItem] = Field(default=None, description="Next memory in chain")
    branch_id: Optional[str] = Field(default=None, description="Branch containing this memory")
