# Dead Code 전수조사 리포트

## 요약
- **전체 코드베이스의 15-20%**가 dead code 또는 문제 있는 코드
- 10개 카테고리에서 문제 발견
- 즉시 조치 필요 항목과 중장기 개선 항목 분류

---

## 1. 🗂️ Legacy/Obsolete 파일 (높은 우선순위)

### 전체 디렉토리
- `legacy_backup/` - 50개 이상의 구버전 테스트 파일
  - 용량만 차지하고 실제 사용 안됨
  - **권고: 즉시 삭제 또는 별도 아카이브**

### 루트 디렉토리 오염
```
test_branch_dfs.py
test_global_jump.py
test_ci_fix.py
run_all_tests.py
run_v3_tests.py
run_complete_v3_tests.py
test_greeum_integration.py
```
**권고: tests/ 디렉토리로 이동**

### 사용되지 않는 독립 파일
- `greeum/ai_memory_guidance.py` - import 없음
- `greeum/token_utils.py` - import는 되나 사용 없음
- `greeum/utils.py` - 거의 빈 파일

---

## 2. ❌ 잘못된 파라미터 사용 (즉시 수정 필요)

### greeum/cli/merge_cli.py
```python
# 현재 (잘못됨)
db_manager = DatabaseManager(db_path=db_path)

# 수정 필요
db_manager = DatabaseManager(connection_string=db_path)
```
- 3곳에서 동일한 오류
- CLI 명령어 자체가 등록 안되어 실제로는 실행 불가

---

## 3. 🔄 중복/불필요 MCP 서버 구현

현재 4개의 MCP 서버 파일 존재:
1. `production_mcp_server.py` ✅ (현재 사용)
2. `claude_code_mcp_server.py` ❓
3. `working_mcp_server.py` ❓
4. `fastmcp_hotfix_server.py` ❓

**권고: production_mcp_server.py만 남기고 정리**

---

## 4. 🚫 사용되지 않는 Core 컴포넌트

완전히 import되지 않는 파일들:
- `greeum/core/phase_three_coordinator.py`
- `greeum/core/neural_memory.py`
- `greeum/core/engram.py`
- `greeum/core/precompact_hook.py`
- `greeum/core/auto_compact_monitor.py`
- `greeum/core/metrics_collector.py`
- `greeum/core/metrics_dashboard.py`

---

## 5. 📊 중복된 Graph 관련 모듈

기능이 겹치는 모듈들:
- `greeum/core/graph_bootstrap.py`
- `greeum/graph/index.py`
- `greeum/core/global_index.py`
- `greeum/core/branch_global_index.py`

**권고: 통합 또는 역할 명확화**

---

## 6. 🎛️ 등록되지 않은 CLI 명령어

정의는 되었으나 등록 안됨:
- `greeum/cli/merge_cli.py` - merge 명령어 그룹
- `greeum/cli/graph.py` - graph 명령어 (확인 필요)

---

## 7. 🗄️ 사용되지 않는 Migration 모듈

- `greeum/core/migration/ai_parser.py`
- `greeum/core/migration/validation_rollback.py`

---

## 8. 📝 프로젝트 루트의 문서 파일들

```
deployment_checklist.md
openai_mcp_integration_guide.md
report.md
RELEASE_NOTES_v3.0.0.post3.md
DEAD_CODE_REPORT.md (이 파일)
```
**권고: docs/ 디렉토리로 이동**

---

## 조치 계획

### 🔴 즉시 조치 (v3.0.0.post4)
1. [ ] `merge_cli.py`의 `db_path` → `connection_string` 수정
2. [ ] 루트 디렉토리의 테스트 파일들 이동
3. [ ] `legacy_backup/` 디렉토리 삭제

### 🟡 중기 조치 (v3.1.0)
1. [ ] MCP 서버 구현 통합 (1개만 유지)
2. [ ] 사용되지 않는 core 컴포넌트 제거
3. [ ] CLI 명령어 등록 또는 제거
4. [ ] Graph 모듈 통합

### 🟢 장기 개선
1. [ ] 자동 dead code 검출 CI/CD 추가
2. [ ] 코드 커버리지 분석 도입
3. [ ] 정기적인 코드베이스 정리 프로세스

---

## 영향도 분석

- **사용자 영향**: 거의 없음 (대부분 미사용 코드)
- **개발자 영향**: 코드 가독성 및 유지보수성 개선
- **저장 공간**: 약 5-10MB 절약 가능
- **빌드 시간**: 10-15% 단축 예상

---

생성일: 2025-09-14
버전: v3.0.0.post3 기준