"""
API Key authentication middleware for Greeum API Server.

v5.0.0: Simple API key authentication via header or query parameter.
"""

import logging
from typing import Optional, List

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

logger = logging.getLogger("greeum.server.auth")


class APIKeyAuthMiddleware(BaseHTTPMiddleware):
    """
    Simple API Key authentication middleware.

    Checks for X-API-Key header or api_key query parameter.
    Public endpoints bypass authentication.
    """

    def __init__(
        self,
        app,
        api_key: str,
        public_endpoints: Optional[List[str]] = None,
    ):
        super().__init__(app)
        self.api_key = api_key
        self.public_endpoints = public_endpoints or [
            "/",
            "/health",
            "/docs",
            "/redoc",
            "/openapi.json",
        ]

    async def dispatch(self, request: Request, call_next):
        """Process request with authentication check."""
        path = request.url.path

        # Public endpoints bypass authentication
        if self._is_public_endpoint(path):
            return await call_next(request)

        # Extract API key from header or query parameter
        provided_key = request.headers.get("X-API-Key")
        if not provided_key:
            provided_key = request.query_params.get("api_key")

        # Check for missing API key
        if not provided_key:
            logger.warning(f"Missing API key for {request.method} {path}")
            return JSONResponse(
                status_code=401,
                content={
                    "error": "authentication_required",
                    "message": "API key required. Provide X-API-Key header or api_key query parameter.",
                    "docs": "See /docs for API documentation",
                },
            )

        # Validate API key
        if provided_key != self.api_key:
            logger.warning(f"Invalid API key for {request.method} {path}")
            return JSONResponse(
                status_code=403,
                content={
                    "error": "invalid_api_key",
                    "message": "Invalid API key",
                },
            )

        # Authentication successful
        return await call_next(request)

    def _is_public_endpoint(self, path: str) -> bool:
        """Check if the path is a public endpoint."""
        for endpoint in self.public_endpoints:
            if path == endpoint or path.startswith(f"{endpoint}/"):
                return True
        return False
