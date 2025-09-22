"""HTTP transport for Greeum Native MCP Server."""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from .server import GreeumNativeMCPServer

logger = logging.getLogger("greeum_native_http")


def _require_fastapi_components():
    try:
        from fastapi import FastAPI, HTTPException, Request, Body
        from fastapi.middleware.cors import CORSMiddleware
        from fastapi.responses import JSONResponse
    except ImportError as exc:  # pragma: no cover - graceful error path
        raise RuntimeError(
            "HTTP transport requires FastAPI. Install with 'pip install fastapi'"
        ) from exc

    return FastAPI, HTTPException, Request, Body, CORSMiddleware, JSONResponse


def create_http_app(
    server: Optional[GreeumNativeMCPServer] = None,
    allowed_origins: Optional[List[str]] = None,
) -> "FastAPI":
    FastAPI, HTTPException, Request, Body, CORSMiddleware, JSONResponse = _require_fastapi_components()

    mcp_server = server or GreeumNativeMCPServer()
    app = FastAPI(title="Greeum MCP", description="HTTP transport for MCP tools")

    if allowed_origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=allowed_origins,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    @app.middleware("http")
    async def log_request(request, call_next):
        logger.info("HTTP %s %s", request.method, request.url.path)
        response = await call_next(request)
        logger.info("HTTP %s %s -> %s", request.method, request.url.path, response.status_code)
        return response

    @app.on_event("startup")
    async def startup_event():
        await mcp_server.initialize()
        logger.info("HTTP transport initialized")

    @app.get("/healthz")
    async def healthcheck():
        return {"status": "ok", "initialized": mcp_server.initialized}

    @app.post("/mcp")
    async def handle_mcp(payload: dict = Body(...)):
        try:
            response = await mcp_server.handle_jsonrpc(payload)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        except Exception as exc:  # pragma: no cover - defensive logging
            logger.exception("MCP request failed")
            raise HTTPException(status_code=500, detail="Internal server error") from exc

        if response is None:
            return JSONResponse(status_code=204, content=None)

        if isinstance(response, list) and not response:
            return JSONResponse(status_code=204, content=None)

        return JSONResponse(content=response)

    return app


def run_http_server(
    host: str = "127.0.0.1",
    port: int = 8000,
    log_level: str = "quiet",
    allowed_origins: Optional[List[str]] = None,
) -> None:
    try:
        import uvicorn
    except ImportError as exc:  # pragma: no cover - graceful error path
        raise RuntimeError(
            "HTTP transport requires uvicorn. Install with 'pip install uvicorn[standard]'"
        ) from exc

    app = create_http_app(allowed_origins=allowed_origins)

    uvicorn_level = {
        "debug": "debug",
        "verbose": "info",
        "quiet": "warning",
    }.get(log_level, "warning")

    logger.info("Starting HTTP MCP server on %s:%s", host, port)
    uvicorn.run(app, host=host, port=port, log_level=uvicorn_level)
