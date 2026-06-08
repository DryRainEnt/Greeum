# MCP legacy → native porting analysis

**Status**: Phase 4 PREP complete (porting + deprecation markers landed). **Deletion deferred to maintainer review.**
**Tracking issue**: `docs/issues/2026-05-30-mcp-implementation-consolidation.md`

## Background

Three MCP server implementations + two tool definitions coexist in `greeum/mcp/`:

| Path | Status | Used by |
|------|--------|---------|
| `greeum/mcp/native/` | **Canonical** (v5.3.0+, all new work) | `greeum mcp serve` (stdio + HTTP) |
| `greeum/mcp/production_mcp_server.py` | Legacy | nothing (verified — 0 imports) |
| `greeum/mcp/server.py` + `tools/memory_tools.py` + `tools/utility_tools.py` | Legacy | `greeum/mcp/cli.py` (orphaned typer CLI, not in pyproject scripts) |
| `greeum/mcp/server_core.py` + `cli_entry.py` | Legacy | `greeum mcp serve --transport websocket` only |
| `greeum/mcp/tools/enhanced_memory_tools.py` | Legacy | nothing (0 imports) |
| `greeum/mcp/enhanced_tool_schema.py` | Legacy | nothing (0 imports) |

This document records what was in legacy, what got ported into native, and what was deliberately dropped — so the eventual deletion can proceed with confidence.

## Tool inventory diff

### Native tools (canonical, after Phase 4 prep)

`add_memory`, `search_memory`, `get_memory_stats`, `usage_analytics`, `analyze`,
`warmup_embeddings`, `storage_backup`, `storage_merge`, `analyze_causality`,
`infer_causality`, `system_doctor`, `get_recent_memories`, `get_memories_by_date`,
**`search` (new, Phase 4)**, **`fetch` (new, Phase 4)**.

### Legacy `production_mcp_server.py` tools

| Tool | Native equivalent | Action |
|------|-------------------|--------|
| `add_memory` | same | already in native |
| `search_memory` | same | already in native |
| `get_memory_stats` | same | already in native |
| `usage_analytics` | same | already in native |
| `search` (OpenAI/ChatGPT-connector compat) | **NEW** in native (Phase 4 prep) | **PORTED** |
| `fetch` (OpenAI/ChatGPT-connector compat) | **NEW** in native (Phase 4 prep) | **PORTED** |

The `search` / `fetch` ports preserve ChatGPT Connectors & OpenAI Deep Research compatibility — these tools MUST be named exactly `search` and `fetch` per OpenAI's connector spec.

### Legacy `server_core.py` tools

Tools registered: `add_memory`, `search_memory`, `get_memory_stats`, `usage_analytics`, `analyze`, `storage_backup`, `storage_merge`. **All present in native already** — no porting needed.

### Legacy `tools/memory_tools.py` (used by `server.py`)

| Method | Native equivalent | Action |
|--------|-------------------|--------|
| `add_memory` | same | already in native |
| `query_memory` | `search_memory` | duplicate name, drop |
| `retrieve_memory(memory_id)` | `fetch` (Phase 4 port) | covered |
| `update_memory(memory_id, content)` | — | **DROP** (Greeum blocks are append-only; mutating contradicts the chain invariant). If "edit" semantics is wanted, the Anthropic memory-tool shim already demonstrates the new-block-per-edit pattern (`greeum.adapters.anthropic_memory`). |
| `delete_memory(memory_id)` | — | **DROP** (same reason). Soft-delete via tombstone tag is the supported pattern. |
| `search_time(time_query)` | `get_memories_by_date` | covered |
| `get_stm_memories(limit)` | not a 1:1 match; `get_recent_memories` returns LTM | **Not ported** for now. STM-specific listing is rarely needed externally; the `stm/slots` REST endpoint (`/stm/slots`, `/stm/slots/{slot}`) exists for ops use. Add an MCP tool later only if a real consumer asks. |
| `forget_stm(memory_id)` | — | **Not ported.** STM TTL handles aging; manual forget is internal. |
| `cleanup_expired_memories` | — | **Not ported.** STM TTL is automatic. |

### Legacy `tools/utility_tools.py`

| Method | Native equivalent | Action |
|--------|-------------------|--------|
| `generate_prompt` | `greeum.PromptWrapper` Python API | Python API only, not an MCP tool — drop |
| `extract_keywords` | `greeum.text_utils.extract_keywords_from_text` | Python API, drop |
| `extract_tags` | `greeum.text_utils.extract_tags_from_text` | Python API, drop |
| `compute_embedding` | `greeum.embedding_models.get_embedding` | Python API, drop |
| `estimate_importance` | `greeum.text_utils.compute_text_importance` | Python API, drop |
| `verify_chain` | partial — `ltm verify` CLI; native `system_doctor` checks integrity | **Not separately ported** — `system_doctor` covers chain integrity checks. |
| `server_status` | native `/healthz` (HTTP) + `get_memory_stats` (stdio) | covered |
| `clear_cache` | — | **Not ported.** Cache lifecycle is internal; expose only if a real consumer asks. |

### Legacy `tools/enhanced_memory_tools.py`

`add_memory_frequent`, `smart_search_memory`, etc. — these were exploratory enhanced variants that never made it into a stable surface. **DROP entirely.** No callers, no docs reference them.

### Legacy `enhanced_tool_schema.py`

Was an exploratory tool schema generator. **DROP.** Native uses inline schema in `protocol.py:_handle_tools_list`.

## What got ported in this prep pass

1. **`search`** tool added to `greeum/mcp/native/tools.py` (dispatch) and `greeum/mcp/native/protocol.py` (schema). Thin alias over `search_memory` with the connector spec's parameter shape.
2. **`fetch`** tool added the same way. Resolves `block_id` → `db_manager.get_block_by_index(id)`; falls back to recent N via `_handle_get_recent_memories` when no id.
3. New tests: `tests/test_native_search_fetch.py` (6 tests, all pass; `tools/list` schema exposure verified).

## Deprecation markers added

A header comment + module-load `logger.warning` was added to each of:

- `greeum/mcp/production_mcp_server.py`
- `greeum/mcp/server.py`
- `greeum/mcp/tools/memory_tools.py`
- `greeum/mcp/tools/utility_tools.py`
- `greeum/mcp/tools/enhanced_memory_tools.py`
- `greeum/mcp/enhanced_tool_schema.py`
- `greeum/mcp/cli.py` (orphaned typer CLI, not in pyproject scripts)

For the websocket-transport chain (different deprecation tier — softer notice, recommend HTTP migration):

- `greeum/mcp/server_core.py`
- `greeum/mcp/cli_entry.py`

The headers cause **no behavioral change** — only documentation + a one-time log line at import.

## Deletion checklist (when maintainer approves)

When the maintainer signs off on deletion:

1. Delete the 7 "truly dead" legacy files listed above.
2. Decide on the websocket transport: either
   - **Keep**: rewrite `cli_entry.py` + `server_core.py` against `native/`, OR
   - **Drop**: remove websocket support from CLI (`greeum/cli/__init__.py:1700–1718`), then delete `cli_entry.py` + `server_core.py`. Modern MCP clients have moved to HTTP Streamable; SSE/WebSocket are deprecated upstream.
3. Update `docs/issues/2026-05-30-mcp-implementation-consolidation.md` → Resolved.
4. Run `python -m unittest discover tests` to confirm no test relies on legacy paths.

## Verification done in this prep

- `grep -rn "production_mcp_server"` → 0 internal usages
- `grep -rn "enhanced_tool_schema"` → 0 internal usages
- `grep -rn "tools.enhanced_memory_tools"` → 0 internal usages
- `from .server import GreeumMCPServer` → only `greeum/mcp/cli.py` (which is itself orphan)
- `from .tools.memory_tools` / `from .tools.utility_tools` → only `greeum/mcp/server.py`
- `from .server_core` → only `greeum/mcp/cli_entry.py`
- `from .mcp.cli_entry` → only `greeum/cli/__init__.py:1703` (websocket transport branch)
- Test suite: 173 → 173 (no regression after porting `search`/`fetch`).
