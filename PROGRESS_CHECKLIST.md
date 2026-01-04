# Greeum 작업 현황

**최종 업데이트**: 2026-01-03

---

## 현재 버전: v5.0.0

Greeum은 **LLM을 위한 범용 기억 모듈**로, 인공 인격 개발을 위한 기반 시스템.

### 핵심 구성요소

| 모듈 | 파일 | 설명 |
|------|------|------|
| Hybrid Search | `core/bm25_index.py` | Vector + BM25 조합 검색 |
| Graph DFS | `core/hybrid_graph_search.py` | 앵커 기반 그래프 탐색 |
| Pipeline | `core/insight_pipeline.py` | 검색 → 자동연결 → LLM 판단 |
| Project | `core/project_manager.py` | 프로젝트 = 브랜치 매핑 |
| InsightJudge | `core/insight_judge.py` | LLM 기반 인사이트 필터링 |

### 구현 완료 (Core)

- [x] BM25 키워드 인덱스 + IDF 사전 계산
- [x] HybridScorer (Vector + BM25 가중 융합)
- [x] 앵커 기반 DFS + 가지치기
- [x] ProjectAnchorManager (프로젝트별 앵커)
- [x] 3단계 파이프라인 (유사도 0.85 이상 + 5분 내 → 자동 연결)
- [x] InsightJudge (LLM 기반 콘텐츠 필터링)
- [x] ProjectManager (프로젝트 CRUD)

### 구현 완료 (REST API v5.0.0)

- [x] InsightJudge 통합 (LLM 기반 필터링)
- [x] API Key 인증 (X-API-Key 헤더)
- [x] STM 슬롯 조회 (`/stm/slots`)
- [x] 브랜치 탐색 (`/branch/{id}`, `/branch/{id}/memories`)
- [x] 기억 체인 탐색 (`/branch/memory/{id}/neighbors`)

### 대기 중

- [ ] API/MCP에 프로젝트 파라미터 추가
- [ ] set_project, list_projects 도구

---

## 테스트

```bash
python scripts/test_v5_pipeline.py           # 임시 DB
python scripts/test_v5_pipeline.py --use-real-db  # 실제 DB
# 결과: 6개 모듈, 37개 테스트 케이스 통과
```

---

## 서버 구현 현황

### REST API 서버 v5.0.0

- [x] FastAPI 기반 서버 (`greeum/server/`)
- [x] InsightJudge 통합 (LLM 필터링, 명시적 실패 정책)
- [x] API Key 인증 미들웨어 (`GREEUM_API_KEY` 환경변수)
- [x] 실행: `greeum-server --port 8400`

**엔드포인트:**
```
POST /memory              # InsightJudge 필터링 적용
POST /search              # 의미론적 검색
GET  /memory/{id}         # 기억 조회
GET  /stats               # 통계
GET  /stm/slots           # STM 슬롯 상태 (인공 인격용)
GET  /stm/slots/{slot}    # 특정 슬롯 상세
GET  /branch/{id}         # 브랜치 정보
GET  /branch/{id}/memories # 브랜치 기억 목록
GET  /branch/memory/{id}/neighbors # 기억 체인 탐색
GET  /docs                # Swagger UI
```

**환경변수:**
| 변수 | 설명 |
|------|------|
| `GREEUM_API_KEY` | 설정 시 인증 활성화 |
| `GREEUM_USE_INSIGHT_FILTER` | InsightJudge 사용 여부 (기본: 1) |
| `GREEUM_LLM_URL` | InsightJudge LLM 서버 URL |

### MCP 서버 (완료)

- [x] 기존 MCP 래퍼 (`greeum/mcp/`)
- [x] 도구: add_memory, search_memory, get_memory_stats, usage_analytics, system_doctor, analyze

---

## 다음 작업

1. **인공 인격 프로토타입** 개발 (REST API 활용)
2. API/MCP에 프로젝트 파라미터 추가
3. 정확도 모니터링 및 피드백 루프

---

## 변경 이력

| 날짜 | 내용 |
|------|------|
| 2026-01-03 | REST API v5.0.0 (InsightJudge, 인증, STM/브랜치 탐색) |
| 2026-01-02 | Hybrid Search + 3단계 파이프라인 구현 완료 |
| 2025-12-31 | API 서버 기본 구현 완료 |
