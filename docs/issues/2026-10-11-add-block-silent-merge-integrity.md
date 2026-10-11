# Issue: `add_block` silently merges near-duplicate content into an existing block without recomputing hash

**Reported**: 2026-10-11 (discovered 2026-08-10 during live v5.4 deploy)
**Reporter**: Greeum maintainer
**Greeum version**: 5.4 track (editable install at `b587b88`)
**Severity**: High — violates the "immutable blockchain-like blocks" guarantee; `content != hash` blocks can be produced
**Status**: Open (Won't Fix — project sunset 2026-10-11, recorded for the record)

---

## Summary

When `BlockManager.add_block` (v3 branch-based path) receives content that is highly similar to an
existing block, the STM slot router (`global_reallocation`, similarity threshold ≈ 0.4) can route the
write into the **existing** block instead of appending a new one. The existing block's `context` is
modified (append-style merge) but its `hash` is **not recomputed**, so the chain now contains a block
whose stored hash no longer matches its content.

## Reproduction (observed on live DB, 2026-08-10)

1. Live DB has block #347 (an audit block about the search bug fix).
2. Call `add_block` directly (not via REST) with a broadcast message that shares vocabulary with #347.
3. Expected: new block #370 appended.
4. Actual: no new block; #347's `context` grows with the new text; `hash` unchanged.

Recovery was done by restoring #347's original content from the pre-migration backup and re-embedding
with e5. No data was lost (merge was append-style), but another session's block was altered.

## Impact

- Breaks the integrity claim of the block store (hash verification would fail for merged blocks).
- Cross-session contamination: one session's write can alter another session's block.
- Workaround that was adopted: **all live writes go through REST `POST :8400/memory`**, which produced
  independent blocks (#348, #369 confirmed normal). Direct `add_block` from scripts is unsafe.

## Root cause (triage)

Slot-aware routing in the v3 path treats "high similarity to slot head" as "same memory, extend it"
rather than "related memory, link it". The merge path bypasses the hash/prev_hash computation that the
append path performs.

## Acceptance criteria (if ever resumed)

- `add_block` never mutates an existing block's `context`; high-similarity input creates a new block
  linked to the neighbor (edge), or is rejected as a duplicate with an explicit return value.
- Any content mutation path recomputes `hash` and is covered by an integrity test that walks the chain.
- Regression test: add two near-duplicate texts, assert block count +2 and chain verification passes.

## Related

- `project-v54-deploy-2026-08-10` session memory; live broadcast block #369.
- `docs/SUNSET.md`
