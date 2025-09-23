# SQLite Write Queue & Worker Daemon Design

## Goals
- **Reduce add/write latency** by avoiding cold-start initialisation for every CLI call.
- **Eliminate `database is locked` warnings** that appear when multiple processes attempt concurrent writes.
- **Provide a single place** where STM anchor updates, branch metadata updates, association writes, and graph index maintenance can be serialized and monitored.
- **Remain backwards compatible**: if the worker is not running, existing CLI paths continue to function (with current latency characteristics).

## High-Level Architecture
```
+-----------------+        HTTP/stdio RPC         +-----------------------+
| CLI / Tools     |  <------------------------>   |  Write Worker Daemon  |
| (memory add,    |                                |  (single process)     |
|  workflow, etc) |                                |                       |
+-----------------+                                |  - SQLite connection   |
                                                   |  - BranchAwareStorage  |
                                                   |  - Association updates |
                                                   |  - STM anchor updates  |
                                                   +-----------+-----------+
                                                               |
                                                           SQLite DB
```
- A long-running "Write Worker Daemon" owns the SQLite connection(s) and serializes mutating operations.
- CLI commands submit JSON-RPC requests (either over STDIO or the existing HTTP transport). When the daemon is present, CLI skips local BlockManager initialisation and simply forwards the request.
- If the daemon is absent, CLI falls back to the current behaviour (local `BlockManager` + direct DB access) so development environments remain functional.

## Components

### 1. Worker Process (`greeum worker serve`)
- Starts a FastAPI (HTTP) or STDIO server using the existing MCP infrastructure.
- Establishes a single `sqlite3.Connection` (or a small pool if read replicas are needed).
- Hosts a `WriteQueue` (essentially the existing `ThreadSafeDatabaseManager` queue) that executes tasks sequentially.
- Registers MCP tools:
  - `add_memory`
  - `search_memory` (optionally served from the same process – reads can still be handled locally)
  - `update_associations`
  - `anchor_update`
- Maintains STM anchors via the already introduced `STMAnchorStore`.

### 2. Client Library (`WriteServiceClient`)
- Lightweight helper that discovers the worker endpoint from `GREEUM_MCP_HTTP` or a UNIX domain socket path.
- Provides `add_memory_via_worker(...)`, `search_memory_via_worker(...)` wrappers.
- Falls back to local `BlockManager` if RPC fails (raising a warning so logs highlight missing worker).

### 3. CLI Integration
- `greeum memory add` / `search` gain `--use-worker` flag (defaults to `True` once the daemon is GA).
- When the worker is active, CLI calls go through `WriteServiceClient` → daemon. No GraphIndex/SentenceTransformer warmup occurs in the CLI process.
- A new command `greeum worker serve [-t http|stdio]` boots the daemon. For quick local usage we can also add a `greeum worker status` command that pings `/healthz` to ensure the worker is up.

## Data Flow for `memory add`
1. CLI sends JSON-RPC payload `{ method: "tools/call", name: "add_memory", arguments: { ... } }` to the worker.
2. Worker enqueues the operation in its `WriteQueue`.
3. Queue worker executes:
   - `BlockManager._add_block_internal` (refactored to accept an existing connection instead of opening a new one).
   - Branch/association updates.
   - STM anchor persistence.
4. Worker returns block metadata to the CLI.
5. CLI prints the resulting block ID to the user.

## Required Refactors
- **BlockManager**: split the current `add_block` into connection-agnostic logic so that the worker can pass its own connection. This eliminates the `self.conn` assumption and removes per-call initialisation.
- **Association updates**: ensure they use the worker-owned connection, removing leftover direct `DatabaseManager.conn` usage.
- **ThreadSafeDatabaseManager**: deprecated once the worker handles serialization; fallback path can still use it when the worker is absent.
- **CLI fallback**: keep existing code path but add prominent warnings when no worker is running (so production setups know to start the daemon).

## Rollout Plan
1. Implement `WriteQueue` + worker scaffolding in a feature flag (`GREEUM_USE_WORKER`).
2. Refactor BlockManager to accept external connections; update tests.
3. Add CLI flags and environment detection.
4. Update documentation (`README`, `docs/perf_tuning_checklist.md`, new `docs/db_write_queue_design.md`).
5. Benchmark using `scripts/bench_memory.py` with and without the worker to quantify improvements.

## Open Questions / Decisions Needed
- Should reads (search) also be routed through the daemon by default, or remain local? (Proposal: keep reads local for now; they are already ~3s after warmup.)
- Preferred transport default? (HTTP gives better compatibility with existing MCP integrations; STDIO is simpler for scripts.)
- Authentication requirements if we expose HTTP to other machines (for now we assume localhost only).

## Next Steps
- Implement phase 1 (worker scaffolding + BlockManager refactor) behind a feature flag.
- Add integration tests that spin up the daemon and exercise add/search via the RPC path.
- Measure latency before/after to ensure writes drop from ~30s down to the target (<10s).

---

## Implementation Checklist
- [ ] Introduce `WriteQueue` and worker daemon CLI (`greeum worker serve`).
- [ ] Refactor `BlockManager` to accept external connections and reuse the worker queue.
- [ ] Update CLI (`greeum memory add/search`) to auto-detect worker (`--use-worker` flag, fallback to local path).
- [ ] Extend test suite: start worker in tests and verify RPC path add/search.
- [ ] Measure `scripts/bench_memory.py` latency with worker vs current baseline; record results.
- [ ] Update documentation (README, workflow guide) to describe the new worker-based workflow.
