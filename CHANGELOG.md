# Changelog

## Unreleased (v5.4 트랙 — 작업 중)

### Added
- **MCP-over-HTTP 전송 업그레이드** (`greeum/mcp/native/http_server.py`, Phase 2):
  - MCP Streamable HTTP 스펙 준수 — `POST /mcp`가 `Accept` 헤더 기반으로 JSON 또는 SSE 응답 분기
  - `Mcp-Session-Id` 헤더 발급·에코 (클라이언트가 세션 추적 가능, 서버 stateless)
  - `DELETE /mcp` 세션 종료 ack
  - X-API-Key 인증 통합 (`GREEUM_API_KEY` 설정 시 자동 활성; `server/middleware/auth.py` 재사용)
  - Health 엔드포인트 분리 (`/`, `/healthz` 무인증)
  - 13 신규 단위 테스트 (`tests/test_mcp_http_transport.py`, httpx 부재 시 graceful skip)
  - 미구현(향후): `GET /mcp` 서버 푸시 SSE, OAuth 2.1, per-session 서버 상태
- **프레임워크 어댑터 3종** (`greeum/adapters/`):
  - `langchain.GreeumRetriever` — LangChain `BaseRetriever` 구현, `from_block_manager`/`from_http_client` 분기로 in-process·원격 모두 지원. extra: `greeum[langchain]`.
  - `llamaindex.GreeumRetriever` — LlamaIndex `BaseRetriever` 구현, 동일한 두 모드. extra: `greeum[llamaindex]`.
  - `anthropic_memory.AnthropicMemoryHandler` — Anthropic `memory_20250818` 도구를 Greeum 블록 스토어로 라우팅. view/create/str_replace/insert/delete 지원. 가상 경로는 `mem-path:<path>` 태그로 매핑; 블록 불변성을 위해 편집은 새 블록 생성, 삭제는 기본 soft. 추가 의존성 없음.
  - 12 신규 단위 테스트 (`tests/test_adapters.py`, 프레임워크 미설치 시 graceful skip).
- `Model2VecEmbedding` 클래스 — Model2Vec 기반 정적(no-torch-at-inference) 다국어 임베딩.
  기본 모델 `minishlab/potion-multilingual-128M`. 기존 `EmbeddingModel` 인터페이스 준수, 768차원 패딩.
- `EmbeddingRegistry._auto_init` 우선순위 갱신: SentenceTransformer → Model2Vec → 시끄러운 해시 폴백.
  해시 무음 폴백 footgun 제거.
- `pyproject.toml`에 `greeum[lite]` extra 추가 (`model2vec>=0.6.0`).
- `DatabaseManager` thread-local 연결 모드 (opt-in via `GREEUM_DB_THREAD_LOCAL=1`). LUCA가 보고한
  SQLite cross-thread `ProgrammingError`(60+ 콜사이트 잠재 영향)를 0 코드 변경으로 해소. 기본 OFF —
  Phase 2(MCP-HTTP) 전 활성화 권장.
- 환경변수: `GREEUM_HYBRID_VEC_WEIGHT` / `GREEUM_HYBRID_BM25_WEIGHT` (하이브리드 가중치 런타임 조절),
  `GREEUM_INSIGHT_REQUIRE_LLM` (InsightJudge strict 모드), `GREEUM_DB_THREAD_LOCAL`,
  `GREEUM_DISABLE_M2V`, `GREEUM_SILENT_HASH_FALLBACK`.
- 벤치마크 스크립트 3종 (`scripts/bench_embeddings.py`, `bench_hybrid.py`, `bench_hybrid_weights.py`)
  — 라이브 DB 정답으로 임베딩·하이브리드·가중치 sweep 재현 가능.
- `MemoryAddResponse`에 `judge_status` 필드 추가 (`passed`/`rejected`/`unavailable`/`skipped`).

### Changed
- **하이브리드 융합 가중치 기본값 0.5/0.5 → 0.7/0.3** (`HybridScorer`, `HybridGraphSearch`).
  2026-05-30 라이브 DB 벤치(334 블록, 1730 GT 쌍)에서 모든 임베딩에 대해 0.5/0.5가 차선이었음.
  env var로 런타임 override 가능.
- **InsightJudge fail-soft 정책**: LLM(127.0.0.1:8080) 타임아웃·다운 시 메모리는 저장하되 `is_insight=null`로
  정직 표기. 기존 엄격(500) 동작은 `GREEUM_INSIGHT_REQUIRE_LLM=1`로 유지 가능. 데이터 손실 < LLM 의존.
- 해시 폴백 경고를 stderr 시끄러운 배너로 격상 (logger 필터링 무효화). `_emit_hash_fallback_banner`.

### Issue tracking
- 이슈 7건을 `docs/issues/`에 등록 (이전 GitHub Issues 미사용). 인덱스: `docs/issues/README.md`.
- 스프린트 계획: `docs/sprints/2026-06-greeum-harness-sprint.md`.

### Testing
- 17개 신규 테스트 추가 (`test_model2vec_embedding.py`, `test_db_thread_local.py`).
- 전체 142개 통과 (이전 125 → 142, 회귀 없음).

---

## 5.3.0 - 2026-02-08

### Added
- **Consolidator 서브패키지** (12개 모듈): LLM 기반 블록 쌍 평가 및 연결 생성.
  `greeum/consolidator/` — `candidates.py`, `config.py`, `context_gatherer.py`, `db.py`, `judge.py`,
  `llm_client.py`, `loop.py`, `prompts.py`, `state.py`, `writer.py`, `__main__.py`.
- **연결 기반 검색 확장**: DFS 검색 결과를 `associations` 테이블로 보강 (양방향 조회).
- **MCP 응답 강화**: 검색 결과에 `[type↔#idx(strength)]` 형식 연결 정보 표시.
- **증분 통합 큐**: 새 블록 추가 시 `consolidation_queue`에 자동 등록.
- `get_memory_stats`에 association/consolidation 통계 포함.

### Changed
- BEGIN/ROLLBACK 디버그 프로브 제거 (트랜잭션 누수 방지).
- 큐 드레인 원자적 처리 (`BEGIN IMMEDIATE`).
- 예외 범위 축소 (bare except → `sqlite3.OperationalError`).
- N+1 쿼리 → 3-쿼리 배치 최적화.
- Association 쿼리에 `LIMIT` 추가.

### Testing
- 16개 association 검색 테스트 신규.
- 30개 consolidator 단위 테스트 (큐 테스트 3개 포함).
- 기존 테스트 부채 수정. 전체 130개 통과.

---

## 5.2.3 - 2026-01

### Fixed
- systemd 셋업 전 기존 서버 프로세스 정리 (좀비 프로세스 방지).

## 5.2.2 - 2026-01

### Added
- 원격 클라이언트 셋업 시 Tailscale 자동 설치.

## 5.2.1 - 2026-01

### Added
- 로컬↔원격 메모리 동기화용 backup push/pull 명령.

## 5.2.0 - 2026-01

### Added
- `greeum setup`에 서버 모드 추가. README 갱신.
- 원격 연결 타임아웃 증가 (이전 통신 불안정성 완화).

---

## 5.1.0 - 2025-12

### Added
- **원격 서버 연결 기능**: 다른 기기에서 중앙 Greeum 서버에 메모리 주입 가능.
- 레거시 파일 대거 정리.

---

## 5.0 - 2025-12

### Added
- **Hybrid Graph Search**: 앵커 기반 DFS + Vector + BM25 가중 융합 (`HybridGraphSearch`, `HybridScorer`).
- **BM25 Index**: 사전 계산된 IDF, SQLite 영속화.
- **3단계 인사이트 파이프라인**: 검색 → 자동 연결 → LLM 판단 (`InsightJudge`).
- **REST API v5.0**: FastAPI 기반, API Key 인증, STM/브랜치 탐색 엔드포인트.
- **ProjectManager**: 프로젝트=브랜치 매핑 (`ProjectAnchorManager`).

### Changed
- API 서버 구조 통합 (이전 Flask → FastAPI).

---

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
