# Issue: LangChain + LlamaIndex retriever adapters

**Reported**: 2026-05-30
**Reporter**: Greeum maintainer (direction review)
**Greeum version**: 5.3.0
**Severity**: Medium — low effort, opens the entire framework/RAG-builder audience
**Status**: Open

---

## Summary

Greeum has no first-class adapter for the two dominant RAG frameworks. Every competitor
(mem0, Zep, Letta, Cognee) ships these. A LangChain `BaseRetriever` and a LlamaIndex
retriever are small wrappers over Greeum's existing search and unlock a large audience of
RAG builders who compose pipelines in these frameworks.

## Current state (verified)

- No `langchain` / `llama_index` imports anywhere in the package (only an OpenAI *example*
  in `examples/llm_integration.py`). Confirmed: no adapter modules exist.
- Greeum search is reachable via `BlockManager.search()`, `SmartSearchEngine.smart_search()`,
  the REST `/search`, and the `search_memory` MCP tool — plenty to wrap.

## Scope

1. **LangChain**: subclass `BaseRetriever`, implement
   `_get_relevant_documents(query) -> List[Document]` mapping Greeum blocks → `Document`
   (page_content = context, metadata = block_index/timestamp/score/tags). Optionally also
   expose as a LangChain Tool.
2. **LlamaIndex**: subclass `BaseRetriever`, implement
   `retrieve(query) -> List[NodeWithScore]`.
3. Both should support pointing at either an **in-process** Greeum (Python API) or a
   **remote** Greeum (HTTP client), so they work regardless of deployment.
4. Package as optional extras (`greeum[langchain]`, `greeum[llamaindex]`) to avoid forcing
   heavy framework deps on core.

## Acceptance criteria

- [ ] `GreeumRetriever` (LangChain) returns ranked `Document`s for a query against a live
      Greeum, usable in a standard LangChain RAG chain.
- [ ] `GreeumRetriever` (LlamaIndex) returns `NodeWithScore`s, usable in a query engine.
- [ ] Both work against in-process and remote (HTTP) Greeum.
- [ ] Extras gate the framework deps; core install unaffected.
- [ ] Minimal usage example for each in `examples/`.

## Open questions

1. Map similarity/relevance score into the frameworks' score field directly, or renormalize?
2. Expose branch/anchor filtering (slot) through retriever kwargs, or keep adapters simple first?

## Related

- `greeum/core/search_engine.py`, `smart_search_engine.py`
- `greeum/client/http_client.py` (`GreeumHTTPClient` for remote mode)
- `docs/ROADMAP.md` (priority #3)
