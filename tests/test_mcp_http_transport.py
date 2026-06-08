"""Tests for the upgraded MCP-over-HTTP transport (Phase 2 / v5.4).

Validates Streamable HTTP behaviors layered onto the existing native MCP
server: Accept-based JSON/SSE dispatch, Mcp-Session-Id wiring, X-API-Key
auth gating, and DELETE /mcp session ack.

Uses a mock GreeumNativeMCPServer so we test transport plumbing in isolation —
no embedding load, no DB.
"""
from __future__ import annotations

import json
import os
import unittest
from typing import Any, Dict, Optional
from unittest.mock import patch


def _have_fastapi_testclient() -> bool:
    try:
        import httpx  # noqa: F401  # starlette TestClient hard-requires httpx
        from fastapi.testclient import TestClient  # noqa: F401
        return True
    except Exception:  # noqa: BLE001 — also RuntimeError from starlette
        return False


_UNSET = object()


class _MockServer:
    """Stand-in for GreeumNativeMCPServer covering only what http_server calls."""

    def __init__(self, response: Any = _UNSET):
        self.initialized = False
        # Pass response=None explicitly to test the empty-response branch;
        # default sentinel returns a healthy JSON-RPC payload.
        if response is _UNSET:
            self._response: Any = {"jsonrpc": "2.0", "id": 1, "result": {"ok": True}}
        else:
            self._response = response
        self.calls: list[Dict[str, Any]] = []

    async def initialize(self) -> None:
        self.initialized = True

    async def handle_jsonrpc(self, payload):
        self.calls.append(payload)
        return self._response


@unittest.skipUnless(_have_fastapi_testclient(), "fastapi[test] not installed")
class TestStreamableHTTPTransport(unittest.TestCase):
    def _build(self, response=_UNSET, api_key=None):
        from fastapi.testclient import TestClient
        from greeum.mcp.native.http_server import create_http_app

        mock = _MockServer(response=response)
        app = create_http_app(server=mock, api_key=api_key)
        return TestClient(app), mock

    # ---- content-negotiation ----------------------------------------------
    def test_json_response_by_default(self):
        client, _ = self._build()
        r = client.post("/mcp", json={"jsonrpc": "2.0", "id": 1, "method": "ping"})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.headers["content-type"], "application/json")
        self.assertEqual(r.json()["result"]["ok"], True)

    def test_explicit_json_accept(self):
        client, _ = self._build()
        r = client.post(
            "/mcp",
            json={"jsonrpc": "2.0", "id": 1, "method": "ping"},
            headers={"Accept": "application/json"},
        )
        self.assertEqual(r.status_code, 200)
        self.assertTrue(r.headers["content-type"].startswith("application/json"))

    def test_sse_response_when_accept_event_stream(self):
        client, _ = self._build()
        r = client.post(
            "/mcp",
            json={"jsonrpc": "2.0", "id": 1, "method": "ping"},
            headers={"Accept": "text/event-stream"},
        )
        self.assertEqual(r.status_code, 200)
        self.assertTrue(r.headers["content-type"].startswith("text/event-stream"))
        body = r.text
        # SSE framing: 'event: message' + 'data: {...}' + blank line
        self.assertIn("event: message", body)
        self.assertIn("data: ", body)
        data_line = next(l for l in body.splitlines() if l.startswith("data: "))
        payload = json.loads(data_line[len("data: "):])
        self.assertEqual(payload["result"]["ok"], True)

    def test_json_preferred_when_both_accepted(self):
        """Accept lists JSON first → server picks JSON, not SSE."""
        client, _ = self._build()
        r = client.post(
            "/mcp",
            json={"jsonrpc": "2.0", "id": 1, "method": "ping"},
            headers={"Accept": "application/json, text/event-stream;q=0.5"},
        )
        self.assertTrue(r.headers["content-type"].startswith("application/json"))

    # ---- session id wiring -----------------------------------------------
    def test_server_issues_session_id_when_absent(self):
        client, _ = self._build()
        r = client.post("/mcp", json={"jsonrpc": "2.0", "id": 1, "method": "ping"})
        self.assertIn("mcp-session-id", {k.lower() for k in r.headers.keys()})
        sid = r.headers.get("Mcp-Session-Id") or r.headers.get("mcp-session-id")
        self.assertTrue(sid)

    def test_server_echoes_client_session_id(self):
        client, _ = self._build()
        provided = "session-abc-123"
        r = client.post(
            "/mcp",
            json={"jsonrpc": "2.0", "id": 1, "method": "ping"},
            headers={"Mcp-Session-Id": provided},
        )
        sid = r.headers.get("Mcp-Session-Id") or r.headers.get("mcp-session-id")
        self.assertEqual(sid, provided)

    # ---- DELETE /mcp ------------------------------------------------------
    def test_delete_session_returns_204(self):
        client, _ = self._build()
        r = client.delete("/mcp", headers={"Mcp-Session-Id": "x"})
        self.assertEqual(r.status_code, 204)

    # ---- auth -------------------------------------------------------------
    def test_auth_disabled_by_default(self):
        client, _ = self._build(api_key=None)  # explicit no key
        r = client.post("/mcp", json={"jsonrpc": "2.0", "id": 1, "method": "ping"})
        self.assertEqual(r.status_code, 200)

    def test_auth_required_when_key_set(self):
        client, _ = self._build(api_key="secret")
        # Missing key
        r = client.post("/mcp", json={"jsonrpc": "2.0", "id": 1, "method": "ping"})
        self.assertEqual(r.status_code, 401)
        # Valid key
        r = client.post(
            "/mcp",
            json={"jsonrpc": "2.0", "id": 1, "method": "ping"},
            headers={"X-API-Key": "secret"},
        )
        self.assertEqual(r.status_code, 200)
        # Wrong key
        r = client.post(
            "/mcp",
            json={"jsonrpc": "2.0", "id": 1, "method": "ping"},
            headers={"X-API-Key": "WRONG"},
        )
        self.assertEqual(r.status_code, 403)

    def test_health_bypasses_auth(self):
        client, _ = self._build(api_key="secret")
        r = client.get("/healthz")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()["status"], "ok")
        r = client.get("/")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()["service"], "greeum-mcp")

    def test_env_var_picked_up(self):
        """When api_key=None, the constructor reads GREEUM_API_KEY."""
        with patch.dict(os.environ, {"GREEUM_API_KEY": "envkey"}, clear=False):
            client, _ = self._build(api_key=None)
            r = client.post("/mcp", json={"jsonrpc": "2.0", "id": 1, "method": "ping"})
            self.assertEqual(r.status_code, 401)
            r = client.post(
                "/mcp",
                json={"jsonrpc": "2.0", "id": 1, "method": "ping"},
                headers={"X-API-Key": "envkey"},
            )
            self.assertEqual(r.status_code, 200)

    # ---- error paths ------------------------------------------------------
    def test_invalid_json_returns_400(self):
        client, _ = self._build()
        r = client.post(
            "/mcp",
            content=b"{not json",
            headers={"Content-Type": "application/json"},
        )
        self.assertEqual(r.status_code, 400)

    def test_empty_response_is_202_accepted(self):
        client, _ = self._build(response=None)
        r = client.post("/mcp", json={"jsonrpc": "2.0", "method": "notification"})
        self.assertEqual(r.status_code, 202)


if __name__ == "__main__":
    unittest.main()
