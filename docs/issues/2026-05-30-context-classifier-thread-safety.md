# Issue: ContextClassifier SQLite thread-safety violation

**Reported**: 2026-05-30
**Reporter**: LUCA Finance (downstream consumer)
**Greeum version**: 5.3.0
**Severity**: Medium — fallback works, but classifier output is silently dropped on every call
**Status**: Triaged — confirmed valid (2026-05-30, Greeum maintainer side)

---

## Summary

`greeum.core.context_classifier.ContextClassifier._search_by_keywords` (line 210) calls
`self.db_manager.conn.cursor()` directly. When Greeum is embedded in an async web server
(FastAPI / Uvicorn) that uses thread pools, the `BlockManager` / `DatabaseManager` is
typically created on one worker thread but the classifier is invoked on a different one.
SQLite's default `check_same_thread=True` rejects the reused connection and the call
raises `sqlite3.ProgrammingError`.

The exception is caught at line 245 (`logger.error(f"DB search error: {e}")`) so callers
never see it, but the keyword-based fallback search returns an empty list — meaning the
classifier always degrades to the embedding-similarity path with no DB-side evidence.

## Exact error message

```
ERROR:greeum.core.context_classifier:DB search error:
  SQLite objects created in a thread can only be used in that same thread.
  The object was created in thread id 128775450777280
  and this is thread id 128758851827392.
```

## Where it fires

`greeum/core/context_classifier.py`, line ~210:

```python
def _search_by_keywords(self, keywords, ...):
    ...
    if not keywords or not self.db_manager:
        return ...
    try:
        cursor = self.db_manager.conn.cursor()   # ← direct connection access
        ...
    except Exception as e:
        logger.error(f"DB search error: {e}")    # ← swallows the threading error
        return []
```

The `BlockManager` was initialised on the FastAPI startup thread (or another worker),
but every chat turn that triggers `add_memory` arrives on whichever AnyIO worker the
event loop dispatches — almost never the same one.

## Reproduction (LUCA setup)

1. FastAPI + Uvicorn, single process, default thread pool.
2. `BlockManager` is initialised once at startup (logged as `Shared Greeum BlockManager
   initialized for thread AnyIO worker thread`).
3. Send any chat turn that ends with `save_memory(...)`.
4. Backend logs show the `DB search error` immediately before `Block added successfully`.

Observed at least 5 times in `journalctl -u luca-backend` over a five-day window
(2026-05-25 → 2026-05-30), once per memory write.

## Impact

| Component | Affected? | Notes |
|-----------|-----------|-------|
| `add_memory` (block creation) | No | Falls through to embedding/branch path; block is stored. |
| `_search_by_keywords` keyword evidence | **Yes** | Always returns `[]` in multi-threaded hosts. |
| Branch routing decisions | Likely degraded | Classifier loses one of its two evidence channels, so similarity threshold has to do all the work. |
| User-visible failure | No | Error is swallowed; nothing surfaces upstream. |
| Long-term retrieval quality | **Possibly degraded** | Hard to quantify without a benchmark, but classifier weight balance assumes both signals are live. |

## Root cause

A single sqlite3 connection is held on `DatabaseManager.conn` and reused regardless of
caller thread. Python's sqlite3 module forbids this by default (and rightfully so —
sqlite3 connections are not goroutine-style safe).

Three reasonable fixes, in increasing order of intrusiveness:

1. **Open the connection with `check_same_thread=False`** *and* serialise writes with a
   `threading.Lock`. Smallest patch, but you must audit every write path for the lock.
2. **Thread-local connections** (`threading.local()` + lazy `sqlite3.connect`). No
   external sync needed; each thread gets its own handle.
3. **Connection pool** routed through a single writer thread (the `db_write_queue`
   design already sketched in `docs/db_write_queue_design.md`). Cleanest long term;
   matches the direction the codebase is already heading.

Option 2 is the fastest correct fix for this specific call site. Option 3 is the right
final destination.

## Acceptance criteria ("when is this resolved?")

A fix is considered complete when **all** of the following hold:

### Must-have
- [ ] `ContextClassifier._search_by_keywords` returns non-empty results when called
      from a thread other than the one that initialised `BlockManager`, given keywords
      that match existing blocks.
- [ ] The string `DB search error: SQLite objects created in a thread` no longer appears
      in `journalctl -u luca-backend` over a 7-day observation window with normal LUCA
      traffic (≥ 20 chat turns including memory writes).
- [ ] Existing Greeum test suite (`pytest`) passes, including any new test added for
      multi-threaded access — see below.
- [ ] No regression in single-threaded callers (CLI, MCP server).

### Should-have
- [ ] A dedicated test (`tests/test_context_classifier_threading.py` or similar) spins up
      ≥ 2 worker threads, performs concurrent `add_memory` + classifier queries, and
      asserts no `ProgrammingError` is raised and keyword search returns expected hits.
- [ ] Brief note in `docs/troubleshooting.md` describing the symptom and pointing to the
      fix, so future downstream users searching the error string find an answer.

### Nice-to-have
- [ ] If option 1 (`check_same_thread=False` + lock) is chosen, document the locking
      contract on `DatabaseManager` so future contributors don't accidentally bypass it.
- [ ] If option 3 (write queue) lands, retire `db_write_queue_design.md` as superseded
      by the actual implementation.

## Workaround (LUCA side, while this is open)

None applied yet. LUCA tolerates the silent degradation because:
- Blocks are still stored (the visible user-facing path works).
- The classifier still has the embedding-similarity channel.

LUCA does **not** plan to patch around this in its own codebase — the upstream fix is
small and the right place. If a fix is not available within ~4 weeks, LUCA will revisit.

## Related code & docs

- `greeum/core/context_classifier.py` lines 206–245
- `greeum/core/database_manager.py` — connection ownership
- `docs/db_write_queue_design.md` — long-term direction
- LUCA-side log evidence: `journalctl --user -u luca-backend` (search `DB search error`)

## Open questions for Greeum maintainers

1. Is `DatabaseManager.conn` intended to be a process-wide singleton, or was per-thread
   ownership the original assumption? The answer changes which fix is least invasive.
2. Are there other call sites that touch `conn` directly (grep `db_manager.conn`)?
   They will have the same latent bug.
3. Does the v5.4 roadmap already plan to land the write-queue design? If so, this issue
   can be closed by that work rather than a standalone patch.

---

## Maintainer triage (2026-05-30)

Verified against the v5.3.0 source tree. The report is **substantively accurate**; one
naming correction and the open questions are answered below.

### Correction
- The method is `ContextClassifier._search_via_db` (not `_search_by_keywords`),
  defined at `greeum/core/context_classifier.py:198`. The cited line numbers are correct:
  direct connection access at **:210** (`cursor = self.db_manager.conn.cursor()`) and the
  swallowed error at **:245** (`logger.error(f"DB search error: {e}")`).

### Q1 — Is `DatabaseManager.conn` a process-wide singleton or per-thread?
**Process-wide singleton, and not thread-safe.** `DatabaseManager._setup_connection`
(`database_manager.py:124`) calls `sqlite3.connect(self.connection_string, timeout=timeout)`
**without** `check_same_thread=False`, so it defaults to `True`. A single `self.conn` is
created on whichever thread constructs the manager and then reused everywhere. Per-thread
ownership was **not** the original design. Consequence: any access from another thread
raises `ProgrammingError`. This rules out a pure point-fix — options 2 (thread-local) or
3 (write queue) are the correct directions; option 1 requires `check_same_thread=False`
*plus* a write lock.

### Q2 — Other call sites touching `conn` directly?
**Yes — pervasive. 60+ sites** use `*.conn.cursor()` directly and share the identical
latent bug. Affected modules (non-test):
`knowledge_graph.py`, `core/association_network.py`, `core/project_manager.py`,
`core/branch_aware_storage.py`, `core/semantic_tagging.py`, `core/global_index.py`,
`core/branch_index.py`, `core/ltm_layer.py`, `core/hybrid_graph_search.py`,
`core/context_classifier.py`, `cli/doctor.py`, `server/routes/backup.py`, `utils.py`.

This reframes the issue: context_classifier is only the call site LUCA happened to observe.
The defect lives in `DatabaseManager`'s connection model, so the fix belongs there
(centralized), not in 60 individual call sites. A point-patch to `_search_via_db` would
silence LUCA's specific log line while leaving every other path latently broken — and any
of them firing off-thread (e.g. branch routing, association network, semantic tagging
during a concurrent write) would reproduce the same error.

### Q3 — Does v5.4 plan to land the write-queue design?
Not yet confirmed as a committed roadmap item (product decision for the maintainer).
Relevant existing assets: `docs/db_write_queue_design.md` (design sketch) and the
`greeum/worker/` package (async write worker already in tree). Recommend deciding whether
v5.4 adopts option 3 wholesale; if not, land option 2 in `DatabaseManager` as the
near-term correct fix.

### Recommended path
1. **Near-term (correct, low-risk):** centralize connection access in `DatabaseManager`
   via thread-local connections (option 2) so all 60+ call sites are fixed at once without
   touching each one.
2. **Long-term:** route writes through the single-writer queue (option 3 / `greeum/worker`).
3. Add the multi-threaded regression test from the Should-have list against the
   centralized fix, and document the symptom in `docs/troubleshooting.md`.
