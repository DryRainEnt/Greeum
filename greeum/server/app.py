"""
Greeum API Server - FastAPI Application

Main application factory and configuration.
"""

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import config
from .middleware.logging import RequestLoggingMiddleware
from .middleware.error_handler import setup_error_handlers
from .routes import health_router, memory_router, search_router, admin_router

# Configure logging
logging.basicConfig(
    level=getattr(logging, config.log_level.upper()),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("greeum.server")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    logger.info(f"Starting Greeum API Server on {config.host}:{config.port}")
    yield
    logger.info("Shutting down Greeum API Server")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""

    app = FastAPI(
        title="Greeum API",
        description="Memory system for LLMs with semantic search and branch-based storage",
        version="4.0.0",
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
    )

    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=config.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Request logging middleware
    app.add_middleware(RequestLoggingMiddleware)

    # Error handlers
    setup_error_handlers(app)

    # Include routers
    app.include_router(health_router)
    app.include_router(memory_router)
    app.include_router(search_router)
    app.include_router(admin_router)

    # Include legacy anchors router if available
    try:
        from greeum.api import anchors_router
        if anchors_router is not None:
            app.include_router(anchors_router)
            logger.info("Legacy /v1/anchors router included")
    except ImportError:
        logger.debug("Legacy anchors router not available")

    return app


# Global app instance
app = create_app()
