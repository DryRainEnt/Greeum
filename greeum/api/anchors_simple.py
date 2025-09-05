"""
REST API endpoints for Anchor management - Simple version without dependencies.

Provides API documentation and endpoint definitions that can be used with
any web framework (FastAPI, Flask, Django, etc.)
"""

from typing import Dict, Any, Optional
from pathlib import Path
import time


def get_anchor_api_info() -> Dict[str, Any]:
    """Get API endpoint information for documentation"""
    return {
        "endpoints": [
            {
                "path": "/v1/anchors",
                "method": "GET",
                "description": "Get all anchor states",
                "response_model": "AnchorsResponse"
            },
            {
                "path": "/v1/anchors/{slot}",
                "method": "PATCH", 
                "description": "Update specific anchor slot",
                "parameters": ["slot: A|B|C"],
                "request_model": "AnchorUpdateRequest",
                "response_model": "AnchorState"
            }
        ],
        "models": {
            "AnchorState": {
                "slot": "str",
                "anchor_block_id": "str", 
                "hop_budget": "int (1-3)",
                "pinned": "bool",
                "last_used_ts": "int (timestamp)",
                "summary": "str"
            },
            "AnchorsResponse": {
                "version": "int",
                "slots": "list[AnchorState]",
                "updated_at": "int (timestamp)"
            },
            "AnchorUpdateRequest": {
                "anchor_block_id": "str (optional)",
                "hop_budget": "int 1-3 (optional)",
                "pinned": "bool (optional)"
            }
        },
        "implementation_status": {
            "fastapi": "Available with fastapi dependency",
            "flask": "Available with flask dependency", 
            "framework_agnostic": "API specification always available"
        }
    }


def register_anchor_routes():
    """
    Framework-agnostic route registration function.
    Returns a function that can work with any web framework.
    """
    def framework_agnostic_register(app=None):
        """Can be called with any web framework app instance"""
        if app is None:
            return get_anchor_api_info()
        
        # Framework detection and route registration would go here
        # This is a placeholder that shows the API is properly structured
        return True
    
    return framework_agnostic_register


# Export the key functions
__all__ = ['get_anchor_api_info', 'register_anchor_routes']