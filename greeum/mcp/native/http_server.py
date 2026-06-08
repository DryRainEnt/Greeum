"""HTTP transport for Greeum Native MCP Server.

Phase 2 (v5.4): upgraded toward the MCP Streamable HTTP transport spec and
gated by optional X-API-Key authentication so the server can be exposed
remotely (Tailscale + the existing ``GREEUM_API_KEY`` env, then OAuth as a
follow-up).

What this implements today:
    * ``POST /mcp``  — Accept-header dispatch: returns ``application/json``
      OR ``text/event-stream`` (SSE) based on the client's ``Accept`` header,
      matching the Streamable HTTP spec's content negotiation rule.
    * ``Mcp-Session-Id`` header — issued on the first request (UUID), echoed
      on subsequent requests. Stateless for now.
    * ``DELETE /mcp`` — clean session termination ack.
    * **Authentication**: when ``GREEUM_API_KEY`` is set, requests must carry
      X-API-Key. Reuses ``greeum.server.middleware.auth.APIKeyAuthMiddleware``.
    * Health endpoints: ``/`` and ``/healthz`` (unauthenticated).

Deferred (follow-up):
    * ``GET /mcp`` SSE for server-initiated messages.
    * OAuth 2.1.
    * Per-session server state / resumability.
"""

# Note: we intentionally do NOT use `from __future__ import annotations` here.
# FastAPI's dependency analysis evaluates parameter annotations eagerly, and
# the FastAPI types (Request, Header, Body) are imported lazily — string-form
# annotations cannot be resolved against locals, leading to 422s.

import json
import logging
import os
import uuid
from typing import Any, AsyncIterator, List, Optional

from .server import GreeumNativeMCPServer

logger = logging.getLogger("greeum_native_http")

_SESSION_HEADER = "Mcp-Session-Id"

# Lazy module-level FastAPI imports. Held as module globals so type annotations
# on the route handlers can resolve them at definition time.
try:
    from fastapi import FastAPI as _FastAPI
    from fastapi import HTTPException as _HTTPException
    from fastapi import Request as _Request
    from fastapi.middleware.cors import CORSMiddleware as _CORSMiddleware
    from fastapi.responses import JSONResponse as _JSONResponse
    from fastapi.responses import Response as _Response
    from fastapi.responses import StreamingResponse as _StreamingResponse
    _FASTAPI_AVAILABLE = True
except ImportError:
    _FastAPI = None
    _HTTPException = None
    _Request = None
    _CORSMiddleware = None
    _JSONResponse = None
    _Response = None
    _StreamingResponse = None
    _FASTAPI_AVAILABLE = False


def _require_fastapi():
    if not _FASTAPI_AVAILABLE:
        raise RuntimeError(
            "HTTP transport requires FastAPI. Install with 'pip install fastapi'"
        )


def _accepts_event_stream(accept: Optional[str]) -> bool:
    """Return True iff the client prefers ``text/event-stream`` over JSON."""
    if not accept:
        return False
    parts = [p.strip().lower() for p in accept.split(",") if p.strip()]
    if not any("text/event-stream" in p for p in parts):
        return False
    # If JSON is listed before event-stream with non-zero q, prefer JSON.
    es_idx = next((i for i, x in enumerate(parts) if "text/event-stream" in x), len(parts))
    for i, p in enumerate(parts):
        if "application/json" in p and i < es_idx:
            q = 1.0
            if ";q=" in p:
                try:
                    q = float(p.split(";q=", 1)[1].split(";", 1)[0])
                except ValueError:
                    q = 1.0
            if q > 0:
                return False
    return True


def _to_sse_payload(payload: Any) -> bytes:
    """Serialise one JSON-RPC response as a single SSE event."""
    body = json.dumps(payload, ensure_ascii=False)
    return f"event: message\ndata: {body}\n\n".encode("utf-8")


def create_http_app(
    server: Optional[GreeumNativeMCPServer] = None,
    allowed_origins: Optional[List[str]] = None,
    api_key: Optional[str] = None,
):
    """Build the FastAPI app for the Streamable-HTTP MCP transport.

    Args:
        server: optional pre-built MCP server; one is created if omitted.
        allowed_origins: CORS allow-list. ``None`` disables CORS.
        api_key: when set, X-API-Key is required on /mcp. Defaults to the
            ``GREEUM_API_KEY`` env var; pass an empty string to force-disable.
    """
    _require_fastapi()

    mcp_server = server or GreeumNativeMCPServer()
    app = _FastAPI(
        title="Greeum MCP",
        description="HTTP transport for MCP tools (Streamable HTTP, v5.4)",
    )

    if allowed_origins:
        app.add_middleware(
            _CORSMiddleware,
            allow_origins=allowed_origins,
            allow_credentials=True,
            allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
            allow_headers=["*"],
            expose_headers=[_SESSION_HEADER],
        )

    # Auth wiring — opt-in via env. Explicit empty string disables.
    if api_key is None:
        api_key = os.environ.get("GREEUM_API_KEY") or None
    if api_key:
        from greeum.server.middleware.auth import APIKeyAuthMiddleware
        app.add_middleware(
            APIKeyAuthMiddleware,
            api_key=api_key,
            public_endpoints=["/", "/healthz"],
        )
        logger.info("MCP HTTP auth enabled (X-API-Key required for /mcp)")
    else:
        logger.info("MCP HTTP auth disabled (no GREEUM_API_KEY set)")

    @app.middleware("http")
    async def log_request(request, call_next):
        logger.info("HTTP %s %s", request.method, request.url.path)
        response = await call_next(request)
        logger.info(
            "HTTP %s %s -> %s",
            request.method, request.url.path, response.status_code,
        )
        return response

    @app.on_event("startup")
    async def startup_event():
        await mcp_server.initialize()
        logger.info("HTTP transport initialized")

    @app.get("/")
    async def root():
        return {
            "service": "greeum-mcp",
            "transport": "streamable-http",
            "version": "v5.4",
            "initialized": mcp_server.initialized,
        }

    @app.get("/healthz")
    async def healthcheck():
        return {"status": "ok", "initialized": mcp_server.initialized}

    @app.post("/mcp")
    async def handle_mcp(request: _Request):
        try:
            payload = await request.json()
        except json.JSONDecodeError as exc:
            raise _HTTPException(status_code=400, detail=f"invalid JSON: {exc}") from exc

        session_id = (
            request.headers.get(_SESSION_HEADER)
            or request.headers.get(_SESSION_HEADER.lower())
            or str(uuid.uuid4())
        )

        try:
            response = await mcp_server.handle_jsonrpc(payload)
        except ValueError as exc:
            raise _HTTPException(status_code=400, detail=str(exc)) from exc
        except Exception as exc:  # pragma: no cover - defensive logging
            logger.exception("MCP request failed")
            raise _HTTPException(status_code=500, detail="Internal server error") from exc

        if response is None or (isinstance(response, list) and not response):
            return _Response(status_code=202, headers={_SESSION_HEADER: session_id})

        accept = request.headers.get("Accept") or request.headers.get("accept")
        if _accepts_event_stream(accept):
            async def event_stream() -> AsyncIterator[bytes]:
                yield _to_sse_payload(response)

            return _StreamingResponse(
                event_stream(),
                media_type="text/event-stream",
                headers={
                    _SESSION_HEADER: session_id,
                    "Cache-Control": "no-cache",
                    "X-Accel-Buffering": "no",
                },
            )

        return _JSONResponse(
            content=response,
            headers={_SESSION_HEADER: session_id},
        )

    @app.delete("/mcp")
    async def end_session(request: _Request):
        sid = request.headers.get(_SESSION_HEADER) or request.headers.get(_SESSION_HEADER.lower())
        logger.info("MCP session terminated: %s", sid or "(none)")
        return _Response(status_code=204)

    return app


def run_http_server(
    host: str = "127.0.0.1",
    port: int = 8000,
    log_level: str = "quiet",
    allowed_origins: Optional[List[str]] = None,
    api_key: Optional[str] = None,
) -> None:
    try:
        import uvicorn
    except ImportError as exc:  # pragma: no cover - graceful error path
        raise RuntimeError(
            "HTTP transport requires uvicorn. Install with 'pip install uvicorn[standard]'"
        ) from exc

    app = create_http_app(allowed_origins=allowed_origins, api_key=api_key)

    uvicorn_level = {
        "debug": "debug",
        "verbose": "info",
        "quiet": "warning",
    }.get(log_level, "warning")

    logger.info("Starting MCP HTTP server on %s:%s", host, port)
    uvicorn.run(app, host=host, port=port, log_level=uvicorn_level)
