"""
Health check endpoints.
"""

import time
from fastapi import APIRouter

from ..schemas.common import HealthResponse

router = APIRouter(tags=["health"])

# Server start time for uptime calculation
_start_time = time.time()


def get_version() -> str:
    """Get Greeum version."""
    try:
        from greeum import __version__
        return __version__
    except ImportError:
        return "4.0.0-dev"


@router.get("/", response_model=HealthResponse)
async def root():
    """Server information and health status."""
    return HealthResponse(
        status="healthy",
        version=get_version(),
        uptime_seconds=time.time() - _start_time,
    )


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    return HealthResponse(
        status="healthy",
        version=get_version(),
        uptime_seconds=time.time() - _start_time,
    )
