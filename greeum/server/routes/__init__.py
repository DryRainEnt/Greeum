"""
API route modules.
"""

from .health import router as health_router
from .memory import router as memory_router
from .search import router as search_router
from .admin import router as admin_router

__all__ = [
    "health_router",
    "memory_router",
    "search_router",
    "admin_router",
]
