# Greeum Issues

이 디렉토리에서 Greeum 버그/개선 이슈를 추적한다. (GitHub Issues 대신 레포 내부 파일로 관리)

## 작성 규칙

- 파일명: `YYYY-MM-DD-short-slug.md` (보고일 + 짧은 영문 슬러그)
- 상태(Status): `Open` → `Triaged` → `In Progress` → `Resolved` → `Closed`
- 심각도(Severity): `Critical` / `High` / `Medium` / `Low`
- 각 이슈는 최소: Summary, 재현, 영향(Impact), 근본 원인, 완료 기준(Acceptance criteria)을 포함
- 다운스트림(LUCA 등)이 올린 이슈는 원문을 보존하고, 메인테이너 검증은 별도 "Maintainer triage" 섹션으로 추가

전략 방향과 우선순위는 `docs/ROADMAP.md` 참조.

**2026-05-30 의사결정**: Option A 묶음 + 로드맵 전체 + LUCA 확장 경로 모두 승인. 스프린트 계획: `docs/sprints/2026-06-greeum-harness-sprint.md`.

**진행 상황 (2026-06-12)**: Phase 1A/1B/1C/1D-code/2/3/4-prep 완료(커밋). 본인 결재 게이트로 남은 항목: (1) 라이브 마이그레이션 실행, (2) `GREEUM_DB_THREAD_LOCAL` default 전환, (3) v5.4.0a 버전 bump + 릴리스 태깅, (4) Phase 4 본격 삭제.

## 열린 이슈

| 보고일 | 우선순위 | 심각도 | 상태 | 제목 |
|--------|----------|--------|------|------|
| 2026-05-30 | P0 | High | **In Progress** | [임베딩 패키징 전략 — 벤치 완료, 단계 출시 중](2026-05-30-embedding-packaging-strategy.md) |
| 2026-05-30 | P1 | Medium | **In Progress** | [Hybrid 가중치 50/50 → 0.7/0.3 (Phase 1A 코드 반영됨)](2026-05-30-hybrid-fusion-weights.md) |
| 2026-05-30 | P0 | High | **In Progress** (Phase 2 부분 완료) | [MCP HTTP transport — spec 준수 + 인증](2026-05-30-mcp-http-transport-spec-auth.md) |
| 2026-05-30 | P1 | Medium | **Resolved** (Phase 3, 커밋됨) | [LangChain + LlamaIndex retriever 어댑터](2026-05-30-langchain-llamaindex-adapters.md) |
| 2026-05-30 | P1 | Medium | **Resolved** (Phase 3, 커밋됨) | [Anthropic native memory-tool 심](2026-05-30-anthropic-memory-tool-shim.md) |
| 2026-05-30 | P2 | Medium | **Prep 완료 (삭제 결재 대기)** | [MCP 서버 중복 구현 정리](2026-05-30-mcp-implementation-consolidation.md) — 포팅·deprecation 헤더 완료, 분석은 `docs/design/mcp_legacy_porting.md` |
| 2026-05-30 | — | Medium | Triaged | [ContextClassifier SQLite thread-safety violation](2026-05-30-context-classifier-thread-safety.md) |

## 닫힌 이슈

_(없음)_
