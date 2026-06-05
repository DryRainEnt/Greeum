# Sprint — Greeum harness integration (2026-06)

**Approved**: 2026-05-30 (Option A 묶음 + 로드맵 전체 + LUCA 확장 경로)
**Scope owner**: dryrain (1인 개발)
**Target**: 4~8주에 걸쳐 단계 출시 (Phase 1 며칠 내, 전체 ~8주 + LUCA 확장 +3~4주)

---

## 의사결정 요약 (브리핑 결과)

- **임베딩 묶음(Option A)**: 기본=potion-multilingual(no-torch), opt-in `greeum[full]`=e5_small, minilm 폐기, 해시 무음 폴백 제거.
- **하이브리드 가중치**: 50/50 → **0.7/0.3** (potion 최적, e5는 0.9/0.1 별도 권장 — 환경변수로 조절 가능)
- **MCP-over-HTTP**: 스펙 준수(Streamable HTTP) + 인증(X-API-Key 재사용, OAuth는 후속).
- **프레임워크 어댑터**: LangChain + LlamaIndex + Anthropic memory-tool 심.
- **MCP 정리**: native/ 단일화, 레거시 제거.
- **커스텀 하네스**: 신규 앱이 아니라 **LUCA 확장 경로** (검증된 다운스트림 → 새 Greeum API 활용).

## 의존성 그래프

```
Phase 1A (가중치+경고) ──→ Phase 1B (model2vec) ──→ Phase 1C (마이그레이션) ──→ Phase 1D (CLI 기본 전환 + v5.4.0a)
Phase 2 (MCP-HTTP)   ───┐
Phase 3 (어댑터)      ───┼ (Phase 1과 병렬 가능, 독립)
Phase 4 (MCP 정리)    ───┘

(Phase 5 / 커스텀 하네스는 보류 — RAG 호환형 출시 후 별도 결정)
```

## WBS / 일정 (1인 개발 기준 추정)

### Phase 1: 임베딩·하이브리드 묶음 (~1.5주)

- **1A. 가중치 재튜닝 + 시끄러운 경고** — ½일 (오늘)
  - [x] `HybridScorer.__init__` defaults: vec=0.7, bm25=0.3 + 환경변수 override
  - [x] `HybridGraphSearch` 호출부 정리 (defaults 상속)
  - [x] `_auto_init` 해시 폴백 경로 → stderr 시끄러운 배너
  - [ ] 기존 테스트 통과 확인

- **1B. Model2Vec 통합** — 2~3일
  - [ ] `Model2VecEmbedding(EmbeddingModel)` 래퍼 + 등록
  - [ ] `_auto_init` 우선순위: ST → Model2Vec → 시끄러운 실패 (해시 기본 폴백 제거)
  - [ ] `pyproject.toml`: core dep에 `model2vec`, `greeum[full]`에 sentence-transformers
  - [ ] CLAUDE.md, docs/installation.md 업데이트

- **1C. 재임베딩 마이그레이션** — 1~2일
  - [ ] `scripts/migrate_embeddings.py` (idempotent + dry-run)
  - [ ] 차원 혼재 DB(128/768/3072) 처리 + 백업
  - [ ] CLI 통합: `greeum migrate embeddings [--model X] [--dry-run]`

- **1D. CLI 기본 전환 + v5.4.0a** — 1~2일
  - [ ] `cli/__init__.py:1660` 의 `GREEUM_DISABLE_ST=1` 디폴트 제거
  - [ ] `--semantic` 플래그 → `--no-semantic`(opt-out)로 의미 반전
  - [ ] minilm 참조 일소 (docs/README/예제)
  - [ ] CHANGELOG, 버전 5.4.0a1 태깅

### Phase 2: MCP-over-HTTP (~1주, 1A 후 병렬 시작 가능)

- [ ] `native/http_server.py`를 MCP Streamable HTTP 스펙으로:
  - Accept-based JSON vs SSE 분기
  - `Mcp-Session-Id` 세션 헤더 처리
  - `GET /mcp` 서버→클라 스트림
- [ ] `server/auth.py` X-API-Key 미들웨어 재사용 (옵션 활성)
- [ ] 실제 MCP 클라이언트(Claude Code / OpenAI Responses)로 E2E 검증
- [ ] OAuth 2.1: 별도 후속 (P1.5)

### Phase 3: 프레임워크 어댑터 (~1주, 병렬)

- [ ] `greeum/adapters/langchain.py` — `GreeumRetriever(BaseRetriever)`
- [ ] `greeum/adapters/llamaindex.py` — `GreeumRetriever(LIBaseRetriever)`
- [ ] `greeum/adapters/anthropic_memory.py` — `memory_20250818` 명령 → Greeum 블록
- [ ] extras: `greeum[langchain]`, `[llamaindex]`, `[anthropic]`
- [ ] 각 어댑터의 minimal 예제 in `examples/`

### Phase 4: MCP 정리 (~½주, 언제든)

- [ ] `production_mcp_server.py`, `mcp/server.py`, `mcp/tools/`에서 native에 없는 기능 식별·이식
- [ ] 레거시 파일 삭제·아카이브
- [ ] 모든 진입점이 native만 가리키는지 확인

### Phase 5: 커스텀 하네스 / LUCA 확장 — **보류 (2026-05-30 결정)**

RAG 호환형 작업(Phase 1~4)이 완료된 후 별도로 재검토. 현재 sprint scope에서 제외.

---

## 즉시 착수 (오늘 1A)

코드 변경 2건은 작은 패치라 리뷰 후 단일 커밋으로 머지 가능:

1. `greeum/core/bm25_index.py` — `HybridScorer` defaults (vec 0.5→0.7, bm25 0.5→0.3) + 환경변수 override (`GREEUM_HYBRID_VEC_WEIGHT`, `GREEUM_HYBRID_BM25_WEIGHT`).
2. `greeum/core/hybrid_graph_search.py` — 명시적 인자 제거(defaults 상속).
3. `greeum/embedding_models.py` `_auto_init` — 해시 폴백 두 경로 모두 stderr 배너로 격상 (logger 필터링 무효화).

테스트: `tests/`에서 50/50 가정 없음 확인됨 (`grep vector_weight\|bm25_weight tests/`).

## 측정 / 검증

- `scripts/bench_hybrid.py` 재실행 → 새 디폴트 가중치로 baseline 갱신.
- `scripts/bench_embeddings.py` → model2vec 통합 후 production 경로로 한 번 더.
- 매 Phase 종료 시 `tests/` 풀 패스 확인.

## 리스크 & 모니터링

| 리스크 | 트리거 | 응답 |
|--------|--------|------|
| potion 멀티링궐 한국어 품질이 LUCA 실사용에서 부족 | Phase 5 파일럿에서 사용자 체감 저하 | `greeum[full]` 권장으로 후퇴 / 가중치 0.9/0.1로 전환 |
| 마이그레이션 중 DB 파손 | 1C에서 백업 누락 | 강제 백업, 트랜잭션 단위 처리, --dry-run 우선 |
| MCP HTTP 스펙 변경 | MCP 표준이 6월에 또 변경 | 표준 추적 + 호환성 어댑터로 격리 |
| 어댑터 외부 라이브러리 버전 깨짐 | LangChain/LlamaIndex 메이저 업데이트 | extras에 버전 범위 핀, CI 매트릭스 |

## 참조

- 이슈: `docs/issues/2026-05-30-embedding-packaging-strategy.md`, `-hybrid-fusion-weights.md`, `-mcp-http-transport-spec-auth.md`, `-langchain-llamaindex-adapters.md`, `-anthropic-memory-tool-shim.md`, `-mcp-implementation-consolidation.md`
- 측정 원자료: `docs/issues/bench_embeddings_results.json`, `bench_hybrid_results.json`
- 재현 스크립트: `scripts/bench_embeddings.py`, `bench_hybrid.py`, `bench_hybrid_weights.py`
