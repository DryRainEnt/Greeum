"""HTTP client helpers for interacting with the long-lived worker daemon."""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from typing import Any, Dict, Optional


class WorkerUnavailableError(RuntimeError):
    """Raised when the worker endpoint cannot be reached."""


def resolve_endpoint(explicit: Optional[str] = None) -> Optional[str]:
    """Resolve the worker endpoint from arguments or environment variables."""

    if explicit:
        return explicit

    env_endpoint = os.getenv("GREEUM_WORKER_ENDPOINT")
    if env_endpoint:
        return env_endpoint

    http_endpoint = os.getenv("GREEUM_MCP_HTTP")
    if http_endpoint:
        return http_endpoint

    return None


@dataclass
class WriteServiceClient:
    """Simple JSON-RPC client for the worker daemon."""

    endpoint: str
    timeout: float = 30.0

    def call(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        payload = {
            "jsonrpc": "2.0",
            "id": tool_name,
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": arguments,
            },
        }

        data = json.dumps(payload).encode("utf-8")
        request = urllib.request.Request(
            self.endpoint,
            data=data,
            headers={"Content-Type": "application/json"},
        )

        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                if response.status == 204:
                    return {}
                raw = response.read().decode("utf-8")
        except urllib.error.HTTPError as exc:  # pragma: no cover - network failure
            detail = exc.read().decode("utf-8", "replace")
            raise WorkerUnavailableError(f"HTTP error {exc.code}: {detail}") from exc
        except urllib.error.URLError as exc:  # pragma: no cover - worker offline
            raise WorkerUnavailableError(str(exc)) from exc

        try:
            payload = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise WorkerUnavailableError(f"Invalid worker response: {raw}") from exc

        if "error" in payload:
            raise RuntimeError(f"Worker error: {payload['error']}")

        return payload.get("result") or {}

    def add_memory(self, content: str, importance: float, metadata: Optional[Dict[str, Any]] = None, slot: Optional[str] = None) -> Dict[str, Any]:
        arguments: Dict[str, Any] = {
            "content": content,
            "importance": importance,
        }
        if metadata:
            arguments["metadata"] = metadata
        if slot:
            arguments["slot"] = slot

        return self.call("add_memory", arguments)

    def search_memory(self, query: str, limit: int = 5, threshold: float = 0.1, slot: Optional[str] = None, fallback: bool = True) -> Dict[str, Any]:
        arguments: Dict[str, Any] = {
            "query": query,
            "limit": limit,
            "threshold": threshold,
            "fallback": fallback,
        }
        if slot:
            arguments["slot"] = slot

        return self.call("search_memory", arguments)

    def healthcheck(self) -> bool:
        try:
            parsed = urllib.parse.urlparse(self.endpoint)
            path = parsed.path or "/mcp"
            if path.endswith("/mcp"):
                path = path[: -len("/mcp")] + "/healthz"
            else:
                path = "/healthz"
            health_url = urllib.parse.urlunparse(parsed._replace(path=path))
            with urllib.request.urlopen(health_url, timeout=self.timeout) as response:
                return response.status == 200
        except Exception:  # pragma: no cover - worker offline
            return False
