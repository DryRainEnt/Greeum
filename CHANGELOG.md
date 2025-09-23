# Changelog

## 3.1.1rc7.dev4 - 2025-09-24

### Added
- `docs/README_ko.md`와 README 상단 언어 전환 링크를 추가해 한국어 초심자 온보딩을 지원.

### Changed
- 기본 SQLite 연결에 WAL 모드와 `busy_timeout`을 적용하고, MCP STDIO 경로에 비동기 쓰기 큐를 도입해 동시 `add_memory` 호출 시 잠금 충돌을 완화.
- README를 설치 → `greeum setup` → MCP 연동 순으로 재구성하고 `--semantic` 사용 팁을 명확히 안내.

### Fixed
- SentenceTransformer 미설치 환경에서 폴백 임베딩을 사용할 때도 `add_memory`가 실패하지 않도록 로깅·보고 흐름을 조정.

### Testing
- `python3.11 -m pytest tests/test_branch_storage.py`

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
