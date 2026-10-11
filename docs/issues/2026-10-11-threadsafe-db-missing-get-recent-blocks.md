# Issue: `ThreadSafeDatabaseManager` lacks `get_recent_blocks` — MCP `get_recent_memories` tool errors

**Reported**: 2026-10-11
**Reporter**: Greeum maintainer
**Greeum version**: 5.4 track (`b587b88`)
**Severity**: Medium — one MCP tool is unusable whenever the thread-safe DB manager is active; no data risk
**Status**: Open (Won't Fix — project sunset 2026-10-11, recorded for the record)

---

## Summary

Calling the MCP tool `get_recent_memories` returns:

```
ERROR: Failed to retrieve recent memories: 'ThreadSafeDatabaseManager' object has no attribute 'get_recent_blocks'
```

`greeum/mcp/native/tools.py:1259` calls `db_manager.get_recent_blocks(limit=limit)`. That method exists
only on `greeum/core/database_manager.py:1406` (`DatabaseManager`). `greeum/core/thread_safe_db.py`
(`ThreadSafeDatabaseManager`) does not implement it, and its `__getattr__` (line 1222) raises
`AttributeError` instead of delegating, so the call fails.

## Reproduction

1. Run `greeum mcp serve` in a configuration that selects `ThreadSafeDatabaseManager` (default for the
   MCP server in this environment).
2. Invoke `get_recent_memories` with any `limit`.
3. Observe the error above. `search_memory` and `add_memory` on the same server work.

## Other call sites of `get_recent_blocks`

- `greeum/cli/graph.py:42`
- `greeum/mcp/server_core.py:399`
- `greeum/mcp/tools/enhanced_memory_tools.py:325` (guarded by `hasattr`, degrades silently)
- `greeum/adapters/anthropic_memory.py:280` (guarded by `getattr`)

## Fix sketch (if ever resumed)

Add to `ThreadSafeDatabaseManager`:

```python
def get_recent_blocks(self, limit: int = 10) -> List[Dict[str, Any]]:
    conn = self._get_connection()
    rows = conn.execute(
        "SELECT * FROM blocks ORDER BY block_index DESC LIMIT ?", (limit,)
    ).fetchall()
    return [self._row_to_block(r) for r in rows]  # reuse existing row→dict helper
```

Then add a parity test asserting that every public method of `DatabaseManager` used by
`greeum/mcp/native/tools.py` exists on `ThreadSafeDatabaseManager`.

## Related

- `2026-05-30-context-classifier-thread-safety.md` (same thread-safe DB area)
- `docs/SUNSET.md`
