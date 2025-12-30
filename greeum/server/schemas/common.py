"""
Common schemas used across multiple endpoints.
"""

from typing import Optional, Dict, Any
from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    """Health check response."""
    status: str = Field(description="Server status", examples=["healthy"])
    version: str = Field(description="Server version", examples=["4.0.0"])
    uptime_seconds: float = Field(description="Server uptime in seconds")


class StatsResponse(BaseModel):
    """Memory statistics response."""
    total_blocks: int = Field(description="Total memory blocks")
    active_branches: int = Field(description="Active branch count")
    stm_slots: Dict[str, Any] = Field(description="STM slot information")
    database_size_mb: float = Field(description="Database size in MB")
    embedding_model: str = Field(description="Current embedding model")


class ErrorResponse(BaseModel):
    """Error response."""
    error: str = Field(description="Error type")
    message: str = Field(description="Error message")
    details: Optional[Dict[str, Any]] = Field(default=None, description="Additional details")
