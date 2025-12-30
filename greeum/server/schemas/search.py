"""
Search-related request/response schemas.
"""

from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field


class SearchRequest(BaseModel):
    """Search request parameters."""
    query: str = Field(
        description="Search query",
        min_length=1,
        examples=["Greeum 아키텍처"]
    )
    limit: int = Field(
        default=5,
        ge=1,
        le=50,
        description="Maximum results to return"
    )
    depth: Optional[int] = Field(
        default=None,
        ge=1,
        le=10,
        description="Search depth for branch traversal"
    )
    slot: Optional[str] = Field(
        default=None,
        description="Specific STM slot to search (A, B, or C)"
    )


class SearchResult(BaseModel):
    """Individual search result."""
    block_index: int = Field(description="Block index")
    content: str = Field(description="Memory content")
    timestamp: datetime = Field(description="Creation timestamp")
    similarity: float = Field(description="Similarity score (0.0-1.0)")
    branch_id: Optional[str] = Field(default=None, description="Branch ID")
    importance: float = Field(description="Importance score")


class SearchStats(BaseModel):
    """Search operation statistics."""
    branches_searched: int = Field(description="Number of branches searched")
    blocks_scanned: int = Field(description="Number of blocks scanned")
    elapsed_ms: float = Field(description="Search time in milliseconds")


class SearchResponse(BaseModel):
    """Search response with results and stats."""
    results: List[SearchResult] = Field(description="Search results")
    search_stats: SearchStats = Field(description="Search statistics")
