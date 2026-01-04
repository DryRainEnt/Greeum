"""
API route modules.

v5.0.0: Added STM and branch routes for AI persona development.
"""

from .health import router as health_router
from .memory import router as memory_router
from .search import router as search_router
from .admin import router as admin_router
from .stm import router as stm_router
from .branch import router as branch_router

__all__ = [
    "health_router",
    "memory_router",
    "search_router",
    "admin_router",
    "stm_router",
    "branch_router",
]
