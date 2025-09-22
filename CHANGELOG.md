# Changelog

## 3.1.1rc7.dev3 - 2025-09-23

### Added
- MCP `add_memory` now reports verified block indices even when the first block has index 0, ensuring consistent success messages.
- `force_simple_fallback()` utility allows CLI/MCP flows to switch to hash-based embeddings when semantic models are disabled.

### Changed
- `greeum mcp serve` defaults to SimpleEmbedding and only loads SentenceTransformer when `--semantic` is specified (or when `GREEUM_DISABLE_ST` is unset).
- CLI `serve --semantic` path attempts SentenceTransformer initialization and falls back gracefully if the model/import fails.
- Workflow CLI notes now explicitly advise running `greeum setup` before connecting Codex to avoid first-launch timeouts.

### Removed
- Legacy integration/performance test suites are fully removed; only branch/MCP focused tests remain.

### Testing
- `python3.11 -m pytest tests/test_branch_storage.py tests/test_branch_fallback.py tests/test_branch_index_faiss.py tests/test_cli_reindex.py tests/test_branch_manager.py tests/test_branch_integration.py`
