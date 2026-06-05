# Issue: Consolidate duplicate MCP server implementations

**Reported**: 2026-05-30
**Reporter**: Greeum maintainer (direction review)
**Greeum version**: 5.3.0
**Severity**: Medium — tech debt; risks divergent tool behavior and confuses contributors
**Status**: Open

---

## Summary

There appear to be **three** MCP server implementations in the tree with **two** separate
tool definitions. `greeum/mcp/native/` is the canonical, actively-maintained one (used by
`greeum mcp serve`, modified in v5.3.0); the others are legacy and should be removed or
clearly archived to avoid divergence.

## Current state (verified, v5.3.0)

Canonical (live path):
- `greeum/mcp/native/` — `server.py`, `tools.py`, `http_server.py`, `transport.py`,
  `protocol.py`, `types.py`, `compat.py`. `greeum mcp serve` → `from ..mcp.native import
  run_server_sync` (`greeum/cli/__init__.py:1669`); HTTP → `native.http_server`
  (`:1689`). `native/tools.py` was the file touched by the v5.3.0 release.

Legacy (not on the live `serve` path):
- `greeum/mcp/production_mcp_server.py`
- `greeum/mcp/server.py`, `greeum/mcp/server_core.py`
- `greeum/mcp/tools/` (separate `memory_tools.py`, `utility_tools.py`,
  `enhanced_memory_tools.py`) and `enhanced_tool_schema.py`

Risk: the two tool definitions can drift (e.g. the legacy `tools/` exposes `search`/`fetch`
OpenAI-compat wrappers; unclear whether `native/tools.py` does). A reader/contributor can
easily edit the wrong one.

## Scope

1. Confirm which entry points (if any) still reference the legacy servers (`cli_entry.py`,
   `cli.py`, `__main__`, pyproject scripts).
2. Decide the canonical surface = `native/`. Migrate any still-wanted features (e.g.
   `search`/`fetch` OpenAI-compat tools) into `native/tools.py`.
3. Remove or move legacy files to a clearly-marked archive; update imports/docs.

## Acceptance criteria

- [ ] Exactly one MCP server implementation and one tool-definition module are reachable
      from any entry point.
- [ ] Any tool present only in the legacy impl is either migrated to `native/` or
      consciously dropped (documented).
- [ ] `greeum mcp serve` (stdio + http) works after removal; tests pass.
- [ ] No dangling imports referencing removed modules.

## Open questions

1. Are `search`/`fetch` (OpenAI/ChatGPT-connector compat tools) present in `native/tools.py`?
   If not, they must be ported before deleting `tools/`.
2. Is `production_mcp_server.py` referenced by any external config/docs users may rely on?

## Related

- `greeum/mcp/` (whole subtree)
- `docs/ROADMAP.md` (priority #5)
- Should land before/with `2026-05-30-mcp-http-transport-spec-auth.md` to avoid fixing HTTP in the wrong place.
