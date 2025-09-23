# SQLite Write Queue & Worker Daemon Design

## Goals
- **Reduce add/write latency** by avoiding cold-start initialisation for every CLI call.
- **Eliminate `database is locked` warnings** that appear when multiple processes attempt concurrent writes.
- **Provide a single place** where STM anchor updates, branch metadata updates, association writes, and graph index maintenance can be serialized and monitored.
- **Remain backwards compatible**: if the worker is not running, existing CLI paths continue to function (with current latency characteristics).

## High-Level Architecture
```
CLI / tools  -->  MCP worker daemon (HTTP/STDIO) --> SQLite DB
```
- The daemon keeps long-lived DatabaseManager/BlockManager instances.
- CLI detects the daemon via env (`GREEUM_MCP_HTTP`/socket); otherwise falls back to current behaviour.
- Write operations enqueue to a shared queue processed sequentially.

## Components
1. **Worker (`greeum worker serve`)** – spins up HTTP or STDIO MCP server, owns the SQLite connection, hosts `WriteQueue`.
2. **Client (`WriteServiceClient`)** – helper to send JSON-RPC add/search; falls back if worker unavailable.
3. **CLI changes** – `greeum memory add/search` default to worker when present (`--use-worker/--no-worker`).

## Data Flow (`add_memory`)
```
CLI -> JSON-RPC request -> Worker queue -> BlockManager._add_block -> STM anchor update -> response
```

## Required Refactors
- `BlockManager._add_block_internal` should accept an explicit connection and avoid per-call initialisation.
- Association/graph updates must route through the worker-owned connection.
- `ThreadSafeDatabaseManager` becomes fallback-only; worker path handles serialization.
- Tests need fixtures that start the worker and exercise both HTTP/STDIO transports.

## Rollout Plan
1. Implement worker scaffolding + queue behind feature flag (`GREEUM_USE_WORKER`).
2. Refactor BlockManager & association updates to reuse the worker connection.
3. Add CLI worker detection and flags.
4. Update documentation & examples (README, workflow guide, new worker doc).
5. Benchmark latency (`scripts/bench_memory.py` & `scripts/benchmark_worker_status.py`).

## Implementation Checklist
- [ ] Introduce worker command (`greeum worker serve`) with shared write queue.
- [ ] Refactor BlockManager to operate on external connections & queue-based writes.
- [ ] Adjust CLI memory commands to auto-detect/optionally use the worker.
- [ ] Extend tests to cover worker RPC path (start worker in fixture, run add/search).
- [ ] Measure latency with worker vs. CLI cold-start; capture numbers in docs.
- [ ] Update README + workflow guide with new workflow.
