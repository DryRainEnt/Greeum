# Greeum v5.0 구현 체크리스트

**마지막 업데이트**: 2026-01-02 14:30
**참조 설계**: `GREEUM_V5_VIBE_CODING_DESIGN.md`

---

## Phase 1: 그래프 탐색 + Hybrid 유사도 ✅ 완료

### 1.1 BM25 인덱스 ✅
- [x] `greeum/core/bm25_index.py` 생성
- [x] BM25Index 클래스 (IDF 사전 계산)
- [x] HybridScorer 클래스 (Vector + BM25 융합)
- [x] SQLite 영속화 (save_to_db, load_from_db)
- [x] block_keywords 테이블 연동

### 1.2 Hybrid 그래프 탐색 ✅
- [x] `greeum/core/hybrid_graph_search.py` 생성
- [x] HybridGraphSearch 클래스
- [x] 앵커 기반 DFS 탐색
- [x] min_depth 파라미터 (최소 탐색 깊이)
- [x] explore_threshold 가지치기
- [x] before/after 링크 따라 탐색

### 1.3 앵커 관리 ✅
- [x] ProjectAnchorManager 클래스
- [x] project_anchors 테이블 생성
- [x] get_anchor / set_anchor 메서드
- [x] update_on_access (조회 시 앵커 갱신)

### 1.4 통합 ✅
- [x] core/__init__.py 업데이트
- [x] 단위 테스트 통과

---

## Phase 2: 3단계 파이프라인 ✅ 완료

### 2.1 인사이트 파이프라인 ✅
- [x] `greeum/core/insight_pipeline.py` 생성
- [x] InsightPipeline 클래스
- [x] Stage 1: Hybrid Search로 후보 추림
- [x] Stage 2: 자동 연결 (유사도 > 0.85 AND 시간 < 5분)
- [x] Stage 3: LLM 최종 판단
- [x] store_insight() 함수

### 2.2 프로젝트 관리 ✅
- [x] `greeum/core/project_manager.py` 생성
- [x] ProjectManager 클래스
- [x] Project 데이터클래스
- [x] projects 테이블 생성
- [x] 현재 프로젝트 추적 (set_current_project)
- [x] 프로젝트 = 브랜치 매핑

### 2.3 인사이트 필터링 ✅
- [x] `greeum/core/insight_filter.py` 생성
- [x] InsightFilter 클래스
- [x] 패턴 기반 필터 (해결, 선택, 설정 등)
- [x] 스킵 패턴 (인사말, 확인 등)
- [x] 길이 기반 필터
- [x] force 옵션으로 필터 우회

### 2.4 통합 ✅
- [x] core/__init__.py 업데이트
- [x] 모든 imports 테스트 통과

---

## Phase 3: API/MCP 업데이트 ⬜ 대기

### 3.1 REST API 엔드포인트 ⬜
- [ ] POST /projects - 프로젝트 생성
- [ ] GET /projects - 프로젝트 목록
- [ ] POST /projects/current - 현재 프로젝트 설정
- [ ] POST /insights - 인사이트 저장 (파이프라인 통과)
- [ ] POST /insights/search - Hybrid 검색

### 3.2 MCP 도구 업데이트 ⬜
- [ ] add_memory에 project 파라미터 추가
- [ ] search_memory에 project 파라미터 추가
- [ ] set_project 도구 추가
- [ ] list_projects 도구 추가

### 3.3 정확도 모니터링 ⬜
- [ ] 연결 정확도 로깅
- [ ] LLM 판단 이유 저장
- [ ] 피드백 루프 준비

---

## 파일 현황

| 파일 | 상태 | 설명 |
|------|------|------|
| `core/bm25_index.py` | ✅ 완료 | BM25 인덱스 + HybridScorer |
| `core/hybrid_graph_search.py` | ✅ 완료 | 그래프 탐색 + 앵커 관리 |
| `core/insight_pipeline.py` | ✅ 완료 | 3단계 파이프라인 |
| `core/project_manager.py` | ✅ 완료 | 프로젝트 관리 |
| `core/insight_filter.py` | ✅ 완료 | 인사이트 필터링 |
| `core/__init__.py` | ✅ 업데이트 | 모든 새 모듈 export |

---

## 테스트 현황

### 통합 테스트 스크립트 ✅
```bash
python scripts/test_v5_pipeline.py           # 임시 DB
python scripts/test_v5_pipeline.py --use-real-db  # 실제 DB
```

### 테스트 결과 (2026-01-02) ✅
```
Test 1: BM25 Index           - 7/7 PASS
Test 2: Hybrid Graph Search  - 5/5 PASS
Test 3: Insight Filter       - 11/11 PASS
Test 4: Project Manager      - 5/5 PASS
Test 5: Insight Pipeline     - 5/5 PASS
Test 6: Full Integration     - 4/4 PASS
─────────────────────────────────────
Total: 6/6 modules passed
```

---

## 메모

- **MCP 적용**: 전체 구현 완료 후 빌드/재설치 시 검증
- **기존 호환성**: 기존 DFS 검색(`dfs_search.py`)과 병행 운영 가능
- **테스트 환경**: 임시 DB로 진행, 실제 DB 영향 없음
- **다음 단계**: Phase 3 (API/MCP 업데이트) 또는 통합 테스트

---

## 변경 이력

| 날짜 | 변경 내용 |
|------|----------|
| 2026-01-02 14:00 | Phase 1 완료 (BM25, HybridGraphSearch) |
| 2026-01-02 14:30 | Phase 2 완료 (InsightPipeline, ProjectManager, InsightFilter) |
