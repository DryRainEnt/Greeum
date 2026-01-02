# Greeum 작업 현황

**최종 업데이트**: 2026-01-02

---

## 현재 아키텍처

Greeum은 **바이브코딩 개발자를 위한 인사이트 축적 시스템**으로 발전 중.

### 핵심 구성요소

| 모듈 | 파일 | 설명 |
|------|------|------|
| Hybrid Search | `core/bm25_index.py` | Vector + BM25 조합 검색 |
| Graph DFS | `core/hybrid_graph_search.py` | 앵커 기반 그래프 탐색 |
| Pipeline | `core/insight_pipeline.py` | 검색 → 자동연결 → LLM 판단 |
| Project | `core/project_manager.py` | 프로젝트 = 브랜치 매핑 |
| Filter | `core/insight_filter.py` | 패턴 기반 인사이트 필터링 |

### 구현 완료 (Core)

- [x] BM25 키워드 인덱스 + IDF 사전 계산
- [x] HybridScorer (Vector + BM25 가중 융합)
- [x] 앵커 기반 DFS + 가지치기
- [x] ProjectAnchorManager (프로젝트별 앵커)
- [x] 3단계 파이프라인 (유사도 0.85 이상 + 5분 내 → 자동 연결)
- [x] InsightFilter (한/영 패턴 매칭)
- [x] ProjectManager (프로젝트 CRUD)

### 대기 중 (API/MCP)

- [ ] REST API 엔드포인트 추가
  - POST /projects, GET /projects
  - POST /insights, POST /insights/search
- [ ] MCP 도구 업데이트
  - add_memory에 project 파라미터
  - search_memory에 project 파라미터
  - set_project, list_projects 도구

---

## 테스트

```bash
python scripts/test_v5_pipeline.py           # 임시 DB
python scripts/test_v5_pipeline.py --use-real-db  # 실제 DB
# 결과: 6개 모듈, 37개 테스트 케이스 통과
```

---

## 서버 구현 현황

### API 서버 (완료)

- [x] FastAPI 기반 서버 (`greeum/server/`)
- [x] 기본 엔드포인트: `/health`, `/memory`, `/search`, `/stats`
- [x] 실행: `greeum-server --port 8400`

### MCP 서버 (완료)

- [x] 기존 MCP 래퍼 (`greeum/mcp/`)
- [x] 도구: add_memory, search_memory, get_memory_stats, usage_analytics, system_doctor, analyze

---

## 다음 작업

1. **MCP 빌드/재설치** 후 새 기능 적용
2. API/MCP에 프로젝트 파라미터 추가
3. 정확도 모니터링 및 피드백 루프

---

## 변경 이력

| 날짜 | 내용 |
|------|------|
| 2026-01-02 | Hybrid Search + 3단계 파이프라인 구현 완료 |
| 2025-12-31 | API 서버 기본 구현 완료 |
