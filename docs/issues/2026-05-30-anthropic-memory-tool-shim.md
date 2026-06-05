# Issue: Anthropic native memory-tool (`memory_20250818`) shim

**Reported**: 2026-05-30
**Reporter**: Greeum maintainer (direction review)
**Greeum version**: 5.3.0
**Severity**: Medium — strategic; rides Claude Code/Desktop adoption, competes with Supermemory
**Status**: Open

---

## Summary

Anthropic's native "memory tool" (`memory_20250818`) is a client-side, file-based
interface: Claude issues create/read/update/delete commands against a `/memories`
directory, and the host application executes them. A Greeum shim that backs this
filesystem interface with **Greeum blocks instead of plain files** would let any
Claude-based app get Greeum's semantic/branch memory transparently, with zero custom tool
wiring — directly competing with Supermemory's coding-agent positioning.

## Background

- The memory tool pairs with context-management/editing (`context-management-2025-06-27`):
  Claude offloads to memory as the context window fills, then recalls.
- The host executes the file ops. Greeum can intercept these ops and route them to its
  block store + semantic retrieval rather than flat files.

## Scope

1. Implement a handler conforming to the `memory_20250818` command set
   (view/create/str_replace/insert/delete over a virtual `/memories` tree).
2. Back it with Greeum: writes → `add_memory` blocks (path/section as metadata/tags);
   reads/searches → Greeum semantic + branch retrieval surfaced as file content.
3. Ship as an optional adapter (`greeum[anthropic]`) with a wiring example for the
   Anthropic SDK (tool-use loop + context management beta headers).

## Acceptance criteria

- [ ] A Claude tool-use loop using `memory_20250818` reads/writes through Greeum and gets
      back semantically relevant prior content (not just literal files).
- [ ] Round-trip works: store via memory tool → retrieve later in a new session.
- [ ] Adapter is opt-in; core install unaffected.
- [ ] Example showing it paired with context editing.

## Open questions

1. How faithfully must the virtual filesystem semantics be emulated (paths, listing) vs.
   mapping everything to a flat semantic store? Claude may assume real path structure.
2. Verify the exact current memory-tool command schema/version against Anthropic docs
   before implementing (it may have advanced past `memory_20250818`).
3. Conflict handling when Claude "edits" content that Greeum stored as immutable blocks.

## Related

- Anthropic memory tool + context management docs (verify current version)
- `greeum/mcp/native/tools.py` (existing add/search logic to reuse)
- `docs/ROADMAP.md` (priority #4)
