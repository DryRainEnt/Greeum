"""
Greeum API Server - FastAPI Application

Main application factory and configuration.
v5.0.0: InsightJudge integration, API key authentication.
"""

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import config
from .middleware.logging import RequestLoggingMiddleware
from .middleware.error_handler import setup_error_handlers
from .middleware.auth import APIKeyAuthMiddleware
from .routes import (
    health_router,
    memory_router,
    search_router,
    admin_router,
    stm_router,
    branch_router,
)

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
        description="Memory system for LLMs with InsightJudge filtering and branch-based storage",
        version="5.0.0",
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
    )

    # API Key Authentication middleware (v5.0.0)
    if config.auth_enabled and config.api_key:
        app.add_middleware(
            APIKeyAuthMiddleware,
            api_key=config.api_key,
            public_endpoints=config.public_endpoints,
        )
        logger.info("API key authentication enabled")
    else:
        logger.warning("API authentication disabled - open access mode")

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
    app.include_router(stm_router)  # v5.0.0: STM slot management
    app.include_router(branch_router)  # v5.0.0: Branch exploration

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
