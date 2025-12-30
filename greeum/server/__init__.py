"""
Greeum API Server

FastAPI-based REST API server for Greeum memory system.
Provides HTTP endpoints for memory management, search, and system administration.
"""

from .app import create_app, app

__all__ = ["create_app", "app"]
