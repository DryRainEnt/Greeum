# Issue: MCP HTTP transport — spec compliance + auth

**Reported**: 2026-05-30
**Reporter**: Greeum maintainer (direction review)
**Greeum version**: 5.3.0
**Severity**: High — highest-leverage gap for multi-harness reach (remote/hosted clients)
**Status**: Open

---

## Summary

An HTTP transport for the native MCP server already exists
(`greeum/mcp/native/http_server.py`, launched via `greeum mcp serve --transport http`),
but it is **not compliant with the MCP Streamable HTTP transport spec** and has **no
authentication**. This caps Greeum at local stdio use and blocks the remote/hosted
clients that matter most: OpenAI Responses API, Claude Connectors, Open WebUI, Continue,
Cline, Gemini CLI.

## Current state (verified, v5.3.0)

`native/http_server.py` provides:
- `POST /mcp` → naive JSON-RPC pass-through to `mcp_server.handle_jsonrpc(payload)` (line 60-76).
- `GET /healthz` (line 56).
- Optional CORS (line 35-42).
- **No auth.** No API-key check, no OAuth.
- **Not Streamable HTTP**: no SSE streaming, no `Accept: text/event-stream` handling,
  no `GET /mcp` for server-initiated events, no `Mcp-Session-Id` session management.

This is a plain HTTP JSON-RPC wrapper, not the transport modern harnesses negotiate.

## What modern harnesses expect (early-mid 2026)

- **Streamable HTTP** is the standard remote transport; SSE-only is deprecated.
  `POST /mcp` must return either a JSON response or an SSE stream based on the client's
  `Accept` header; session id via `Mcp-Session-Id` header; optional `GET /mcp` for
  server→client streaming.
- **Auth**: OAuth 2.1 is increasingly the default for remote MCP; static API key is the
  "legacy but accepted" minimum. (Greeum's REST API already has X-API-Key — reuse it.)

## Scope

Not greenfield — upgrade the existing HTTP transport:
1. Make `/mcp` Streamable-HTTP compliant (Accept-based JSON vs SSE, session header).
2. Add auth: at minimum X-API-Key (reuse `GREEUM_API_KEY` + existing server auth
   middleware); ideally an OAuth 2.1 path for hosted deployments.
3. Bind/host/port hardening + docs for remote exposure (it already runs behind Tailscale
   in practice — see remote injection setup).

## Acceptance criteria

### Must-have
- [ ] A real MCP client (e.g. Claude Code / OpenAI Responses remote-MCP, or `mcp` client
      lib) can connect over Streamable HTTP and list+call Greeum tools end-to-end.
- [ ] `POST /mcp` honors `Accept: text/event-stream` (SSE) and `application/json`.
- [ ] Session management via `Mcp-Session-Id` works across multiple requests.
- [ ] Auth enforced when `GREEUM_API_KEY` is set; unauthenticated calls rejected (401).
- [ ] stdio transport unaffected (no regression).

### Should-have
- [ ] OAuth 2.1 flow for hosted/multi-user deployments.
- [ ] Conformance test against the MCP transport spec (or the official validator).
- [ ] Docs: how to expose Greeum as a remote MCP server (Tailscale / reverse proxy / TLS).

## Open questions

1. Reuse the existing FastAPI REST server process (:8400) and mount `/mcp` there, or keep
   `native/http_server.py` separate? Consolidating would reduce the dual-server surface.
2. Is OAuth 2.1 in-scope now, or ship API-key-only first and add OAuth later?

## Related

- `greeum/mcp/native/http_server.py`, `greeum/mcp/native/transport.py`, `protocol.py`
- `greeum/server/auth.py` (existing X-API-Key middleware to reuse)
- `docs/ROADMAP.md` (priority #1)
- Depends on / interacts with `2026-05-30-mcp-implementation-consolidation.md`
