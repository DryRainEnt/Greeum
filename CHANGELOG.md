# Changelog

## 3.1.2 - 2025-09-27

### Added
- MCP 도구 `storage_backup`, `storage_merge`를 추가해 CLI 없이도 백업·병합을 수행할 수 있게 함.
- `greeum/core/storage_admin.py` 헬퍼를 도입해 데이터 루트 자동 감지, 백업 생성, 블록 병합 로직을 공통화.

### Changed
- `usage_analytics` MCP 응답을 실제 통계 수치가 포함된 리포트 형식으로 개선.
- README에 PowerShell 대신 Linux·macOS·WSL 사용을 권장하는 플랫폼 주의 문구와 워커 자동 기동 가이드를 추가.

### Testing
- `python3.11 -m pytest`
- MCP `storage_backup` / `storage_merge` 임시 저장소 통합 테스트

## 3.1.1 - 2025-09-25

### Added
- `analyze` MCP 도구를 추가하여 슬롯·브랜치·최근 활동을 한 번에 요약하는 리포트를 제공.
- `AGENTS.md`에 Codex/Claude 환경에서 MCP 도구를 우선 사용하는 워크플로우 지침을 정식 반영.

### Changed
- ThreadSafeDatabaseManager에 키워드/임베딩 검색 및 최근 블록 조회를 구현하여 중복 검사 경로가 더 이상 AttributeError를 발생시키지 않도록 개선.
- Branch-aware 저장 경로에서 임베딩 변환 실패 시 조용히 키워드·시간 폴백을 사용하도록 조정해 불필요한 경고 로그를 제거.
- `usage_analytics.generate_system_report()`를 확장해 슬롯·브랜치 통계를 계산하고 MCP `analyze` 결과로 활용.

### Fixed
- `duplicate_detector`가 ThreadSafe DB와 함께 동작할 때 누락된 메서드 접근으로 에러를 남기던 문제를 해결.
- 빈 슬롯 매핑 시 경고가 과도하게 출력되던 현상을 완화하고, MCP STDIO 로그의 노이즈를 줄임.

### Testing
- `python3.11 -m pytest`
- `python3.11 run_all_tests.py`

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
