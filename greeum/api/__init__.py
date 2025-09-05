"""
Greeum API module - REST endpoints for memory management and anchor control.

This module provides HTTP API endpoints for:
- Memory operations (search, write)
- Anchor management (get, update)
- System status and health checks
"""

try:
    from .anchors import anchors_router, get_anchor_api_info
    __all__ = ['anchors_router', 'get_anchor_api_info']
except ImportError:
    # Fallback when FastAPI is not available
    try:
        from .anchors import register_anchor_routes, get_anchor_api_info
        __all__ = ['register_anchor_routes', 'get_anchor_api_info']
    except ImportError:
        __all__ = []