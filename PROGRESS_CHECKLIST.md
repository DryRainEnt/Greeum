# Greeum v5.0 작업 현황 체크리스트

**최종 업데이트**: 2026-01-02
**현재 단계**: v5.0 Phase 1-2 완료, Phase 3 대기 (API/MCP 업데이트)

---

## 🚀 v5.0 진행 상황 (바이브코딩 인사이트 시스템)

| Phase | 상태 | 진행률 |
|-------|-----|-------|
| v5 Phase 1: Hybrid 그래프 탐색 | **완료** | 100% |
| v5 Phase 2: 3단계 파이프라인 | **완료** | 100% |
| v5 Phase 3: API/MCP 업데이트 | 대기 | 0% |

### v5.0 핵심 변경
- **타겟 재정의**: 범용 기억 모듈 → 바이브코딩 개발자를 위한 인사이트 축적 시스템
- **Hybrid Search**: Vector + BM25 조합으로 정확도 향상
- **그래프 탐색**: 앵커 기반 DFS + 가지치기
- **3단계 파이프라인**: 검색 → 자동연결 → LLM 판단
- **프로젝트 = 브랜치**: 명시적 프로젝트 지정

### v5.0 구현 파일
| 파일 | 설명 |
|------|------|
| `core/bm25_index.py` | BM25 키워드 인덱스 |
| `core/hybrid_graph_search.py` | Hybrid 그래프 탐색 + 앵커 관리 |
| `core/insight_pipeline.py` | 3단계 파이프라인 |
| `core/project_manager.py` | 프로젝트 관리 |
| `core/insight_filter.py` | 인사이트 필터링 |

### v5.0 테스트
```bash
python scripts/test_v5_pipeline.py           # 임시 DB
python scripts/test_v5_pipeline.py --use-real-db  # 실제 DB
# 결과: 6/6 모듈, 37개 테스트 케이스 통과
```

### v5.0 설계 문서
- `docs/design/GREEUM_V5_VIBE_CODING_DESIGN.md` - 전체 설계
- `docs/design/V5_IMPLEMENTATION_CHECKLIST.md` - 상세 체크리스트

---

## v4.0 진행 상황 (기존)

| Phase | 상태 | 진행률 |
|-------|-----|-------|
| Phase 0: 설계 | **완료** | 100% |
| Phase 1: API 서버 | **완료** | 100% |
| Phase 2: MCP 래퍼 | **완료** | 100% |
| Phase 2.5: 핵심 기능 | → v5.0으로 대체 | - |
| Phase 3: 안정화 | 대기 | 0% |

---

## ⚠️ Phase 2.5: 핵심 기능 구현 [필요]

> **발견된 문제**: 사업화 문서의 핵심 요구사항인 "조회 후 저장" 흐름이 구현되지 않음.
> 현재는 LLM이 텍스트만 보고 분류하며, 기존 메모리를 참조하지 않음.

### 2.5.1 조회 기반 저장 흐름 구현
- [ ] 저장 시 기존 메모리 조회 로직 추가
- [ ] 각 브랜치별 유사 블록 수집
- [ ] LLM에 유사 블록 컨텍스트 제공
- [ ] LLM 응답 기반 최적 브랜치/블록 결정

### 2.5.2 LLM 분류기 개선 (`context_classifier.py`)
- [ ] `classify()` 메서드에 유사 블록 조회 추가
- [ ] Few-shot 프롬프트 구성 (유사 블록 예시 포함)
- [ ] 브랜치 선정 + 저장 위치 결정 분리

### 2.5.3 시점 기반 저장
- [ ] 과거 시점 기억 끼워넣기 로직
- [ ] 동종 지식 갱신 로직
- [ ] before/after 링크 재정렬

### 2.5.4 조회 시 최적 브랜치 선정
- [ ] 쿼리 기반 브랜치 유사도 계산
- [ ] LLM 기반 최적 브랜치 선택
- [ ] 선택된 브랜치에서 DFS 탐색

### Phase 2.5 검증

#### 2.5.5.1 조회 기반 저장 검증
```bash
# 검증 시나리오
# 1. 업무 관련 메모리 3개 저장 (명시적으로 슬롯 A)
# 2. "테스트 서버 시작" 저장 (슬롯 미지정)
# 3. 기존 업무 메모리를 참조하여 A로 분류되어야 함

# 예상 결과
# - 유사 블록 조회 로그 출력
# - LLM이 기존 메모리 참조하여 판단
# - 올바른 슬롯(A)에 저장
```
- [ ] 유사 블록 조회 동작 확인
- [ ] LLM이 기존 메모리 참조 확인
- [ ] 분류 정확도 95%+ (스트레스 테스트)

#### 2.5.5.2 시점 기반 저장 검증
```bash
# 검증 시나리오
# 1. "어제 회의 내용" 저장
# 2. "오늘 회의 결과" 저장
# 3. "그저께 회의 준비" 저장 (과거 시점)

# 예상 결과
# - 시점 순서: 그저께 → 어제 → 오늘
# - before/after 링크가 시점 순서 반영
```
- [ ] 과거 시점 끼워넣기 동작
- [ ] 링크 순서 정확성

#### 2.5.5.3 조회 시 브랜치 선정 검증
```bash
# 검증 시나리오
# 1. 슬롯 A에 업무 메모리 10개, 슬롯 C에 학습 메모리 10개 저장
# 2. "프로젝트 진행 상황" 검색 (슬롯 미지정)

# 예상 결과
# - A 브랜치가 최적으로 선정됨
# - A 브랜치에서 우선 검색
```
- [ ] 쿼리 기반 브랜치 선정 동작
- [ ] 최적 브랜치 우선 검색 확인

---

## Phase 0: 설계 및 문서화 [완료]

- [x] 사업화 문서 검토 (1번 항목: Greeum)
- [x] 기존 코드베이스 분석
  - [x] core/ 모듈 구조 파악 (~22,000줄)
  - [x] mcp/ 모듈 구조 파악 (~3,500줄)
  - [x] 재사용 가능 코드 식별 (100%)
- [x] 비전 문서 작성 (`docs/GREEUM_V4_VISION.md`)
- [x] 마이그레이션 작업 목록 (`docs/GREEUM_V4_MIGRATION_TASKS.md`)
- [x] Git 사용자 설정 (DryRainEnt)

---

## Phase 1: API 서버 구현 [완료]

### 1.1 서버 기본 구조
- [x] `greeum/server/__init__.py` 생성
- [x] `greeum/server/app.py` - FastAPI 앱
- [x] `greeum/server/config.py` - 서버 설정
- [x] `greeum/server/schemas/` - Pydantic 모델
- [x] `greeum/server/middleware/error_handler.py`
- [x] `greeum/server/middleware/logging.py`

### 1.2 엔드포인트 구현
- [x] `GET /` - 서버 정보
- [x] `GET /health` - 헬스체크
- [x] `POST /memory` - 기억 추가
- [x] `GET /memory/{id}` - 기억 조회
- [x] `POST /search` - 기억 검색
- [x] `POST /search/similar` - 유사 검색
- [x] `GET /stats` - 통계 조회
- [x] `POST /admin/doctor` - 시스템 진단

### 1.3 Core 연동
- [x] `greeum/server/services/memory_service.py`
- [x] 의존성 주입 (FastAPI Depends)
- [x] 기존 api/anchors 라우터 통합

### 1.4 서버 실행
- [x] `greeum/server/__main__.py`
- [x] `pyproject.toml` 스크립트 추가 (greeum-server)
- [ ] 기본 테스트 작성 (Phase 3에서 진행)

### Phase 1 검증

#### 1.4.1 서버 시작 검증
```bash
# 검증 명령
greeum-server --port 8400 &
sleep 3
curl -s http://localhost:8400/health | jq .

# 예상 결과
# {"status": "healthy", "version": "4.0.0-alpha"}
```
- [x] 서버가 3초 내에 시작됨 ✓ (2025-12-31 검증)
- [x] 헬스체크 응답 status: "healthy" ✓

#### 1.4.2 기억 추가 검증
```bash
# 검증 명령
curl -X POST http://localhost:8400/memory \
  -H "Content-Type: application/json" \
  -d '{"content": "Phase 1 검증 테스트", "importance": 0.7}' | jq .

# 예상 결과
# {"success": true, "block_index": N, "storage": "LTM", ...}
```
- [x] success: true 반환 ✓
- [x] block_index 숫자 반환 ✓ (block_index: 0)
- [x] 중복 검사 통과 메시지 ✓ (duplicate_check: "passed")

#### 1.4.3 기억 검색 검증
```bash
# 검증 명령
curl -X POST http://localhost:8400/search \
  -H "Content-Type: application/json" \
  -d '{"query": "Phase 1 검증", "limit": 5}' | jq .

# 예상 결과
# {"results": [...], "search_stats": {"elapsed_ms": N}}
```
- [x] 방금 추가한 기억이 results에 포함 ✓
- [x] elapsed_ms < 300 ✓ (1.1ms)

#### 1.4.4 기존 MCP 호환성 검증
```bash
# 검증 명령 (API 서버 실행 상태에서)
python -c "
from greeum.mcp.server_core import GreeumMCPServer
import asyncio
async def test():
    server = GreeumMCPServer()
    await server.initialize()
    result = server._handle_search_memory('테스트', 5)
    print('MCP 직접 호출:', 'OK' if result else 'FAIL')
asyncio.run(test())
"

# 예상 결과
# MCP 직접 호출: OK
```
- [x] MCP 서버 초기화 성공 ✓ (기존 MCP 모듈 정상 동작)
- [x] 직접 호출 방식 여전히 동작 ✓

#### 1.4.5 통합 테스트 스크립트
```bash
# 위치: tests/server/test_phase1.py
pytest tests/server/test_phase1.py -v

# 예상 결과: 모든 테스트 PASSED
```
- [x] test_server_starts ✓ (수동 검증 완료)
- [x] test_health_endpoint ✓
- [x] test_add_memory ✓
- [x] test_search_memory ✓
- [x] test_mcp_compatibility ✓ (테스트 파일 작성은 Phase 3)

---

## Phase 2: MCP 래퍼 전환 [완료]

### 2.1 API 클라이언트
- [x] `greeum/client/__init__.py` ✓
- [x] `greeum/client/http_client.py` ✓
- [x] `greeum/client/client.py` (GreeumClient) ✓

### 2.2 로컬 STM 캐시
- [x] `greeum/client/stm_cache.py` - 슬롯 구조 ✓
- [x] 요약 프롬프트 생성 로직 ✓
- [x] 로컬 저장 (JSON) ✓
- [x] 캐시 만료 정책 (TTL 기반) ✓

### 2.3 MCP 서버 수정
- [x] `GREEUM_USE_API` 환경변수 지원 ✓
- [x] API 모드 분기 로직 ✓
- [x] STM 캐시 통합 ✓ (GreeumClient에서 자동 관리)
- [x] 폴백 메커니즘 ✓ (API 실패 → 직접 모드)

### Phase 2 검증

#### 2.4.1 API 모드 동작 검증
```bash
# 검증 명령 (API 서버 실행 상태에서)
GREEUM_USE_API=true GREEUM_API_URL=http://localhost:8400 \
python -c "
from greeum.mcp.server_core import GreeumMCPServer
import asyncio
async def test():
    server = GreeumMCPServer()
    await server.initialize()
    result = server._handle_add_memory('API 모드 테스트', 0.5)
    print(result)
asyncio.run(test())
"

# 예상 결과
# SUCCESS: Memory Successfully Added!
# (API 서버 로그에 POST /memory 요청 기록)
```
- [x] 환경변수로 API 모드 전환됨 ✓ (코드 검증)
- [x] 기억 추가가 API 서버 경유로 처리됨 ✓ (GreeumClient 통해)

#### 2.4.2 폴백 동작 검증
```bash
# 검증 명령 (API 서버 중지 상태에서)
GREEUM_USE_API=true GREEUM_API_URL=http://localhost:9999 \
python -c "
from greeum.client import GreeumClient
client = GreeumClient()
result = client.search('test', limit=3)
print(result)
"

# 실제 결과 (2025-12-31 검증)
# API unavailable, falling back to direct mode
# {'results': [...], 'search_stats': {...}}
```
- [x] API 연결 실패 시 경고 메시지 ✓
- [x] 직접 모드로 폴백하여 정상 처리 ✓

#### 2.4.3 STM 캐시 검증
```bash
# 검증 명령
python -c "
from greeum.client.stm_cache import STMCache
import os

cache = STMCache()
cache.add_block_reference('A', 123, 'test content')
cache.add_block_reference('A', 124, 'another content')

# 저장 확인
cache.save()
print('저장됨:', os.path.exists(cache.cache_path))

# 로드 확인
cache2 = STMCache()
cache2.load()
print('슬롯 A 블록 수:', len(cache2.slots['A']['blocks']))
"

# 실제 결과 (2025-12-31 검증)
# 저장됨: True
# 슬롯 A 블록 수: 4
```
- [x] 로컬 파일에 캐시 저장됨 ✓
- [x] 재로드 시 데이터 유지 ✓
- [x] 슬롯별 블록 좌표 관리 ✓

#### 2.4.4 통합 테스트 스크립트
```bash
# 위치: tests/client/test_phase2.py
pytest tests/client/test_phase2.py -v

# 예상 결과: 모든 테스트 PASSED
```
- [x] test_api_mode_add_memory ✓ (수동 검증)
- [x] test_api_mode_search ✓ (수동 검증)
- [x] test_fallback_on_api_failure ✓
- [x] test_stm_cache_save_load ✓
- [x] test_stm_summary_generation ✓ (generate_summary_prompt 구현됨)

---

## Phase 3: 안정화 및 배포 [대기]

### 3.1 성능 최적화
- [ ] 연결 풀링
- [ ] 배치 API
- [ ] 캐싱 레이어

### 3.2 운영 기능
- [ ] systemd 서비스 파일
- [ ] 로그 로테이션
- [ ] 모니터링 스크립트

### 3.3 문서화
- [ ] API 문서 (OpenAPI)
- [ ] 마이그레이션 가이드
- [ ] README 업데이트

### 3.4 배포
- [ ] 버전 4.0.0 범프
- [ ] CHANGELOG 작성
- [ ] PyPI 배포

### Phase 3 검증

#### 3.5.1 성능 검증
```bash
# 검증 명령: 부하 테스트
python -c "
import time
import requests
import statistics

# 100회 기억 추가 테스트
times = []
for i in range(100):
    start = time.time()
    resp = requests.post('http://localhost:8400/memory',
        json={'content': f'성능 테스트 {i}', 'importance': 0.5})
    times.append((time.time() - start) * 1000)

print(f'평균: {statistics.mean(times):.1f}ms')
print(f'99th: {sorted(times)[98]:.1f}ms')
print(f'최대: {max(times):.1f}ms')
"

# 예상 결과
# 평균: < 200ms
# 99th: < 500ms
# 최대: < 1000ms
```
- [ ] 평균 응답 시간 < 200ms
- [ ] 99th percentile < 500ms
- [ ] 동시 10 req/s 처리 가능

#### 3.5.2 안정성 검증
```bash
# 검증 명령: 24시간 운영 시뮬레이션 (축약)
timeout 3600 bash -c '
while true; do
    curl -s http://localhost:8400/health > /dev/null || echo "FAIL $(date)"
    sleep 60
done
' &
STABILITY_PID=$!

# 1시간 후 확인
sleep 3600
kill $STABILITY_PID
echo "1시간 동안 FAIL 없으면 통과"
```
- [ ] 1시간 연속 운영 무중단
- [ ] 메모리 누수 없음 (RSS 증가 < 100MB)

#### 3.5.3 문서 검증
```bash
# 검증 명령: OpenAPI 문서 확인
curl -s http://localhost:8400/openapi.json | jq '.paths | keys'

# 예상 결과: 모든 엔드포인트 문서화
# ["/", "/health", "/memory", "/search", "/stats", "/admin/doctor"]
```
- [ ] OpenAPI 스키마 자동 생성
- [ ] 모든 엔드포인트 문서화
- [ ] README에 설치/사용법 명시

#### 3.5.4 배포 전 최종 검증
```bash
# 검증 명령: 전체 테스트 스위트
pytest tests/ -v --tb=short

# 예상 결과: 모든 테스트 PASSED
```
- [ ] 모든 단위 테스트 통과
- [ ] 모든 통합 테스트 통과
- [ ] 커버리지 70% 이상

---

## 커밋 히스토리

| 날짜 | 커밋 | 내용 |
|-----|------|-----|
| 2025-12-31 | (pending) | Phase 2 MCP 래퍼 전환 완료 (5개 파일, ~600줄) |
| 2025-12-31 | ba97812 | Phase 1 API 서버 기본 구현 완료 (18개 파일, 903줄) |
| 2025-12-31 | 375bf89 | 구조 결정 및 오픈소스 전략 반영 |
| 2025-12-31 | 36e6749 | 각 Phase별 검증 방법 상세화 |
| 2025-12-31 | b0d74e2 | Phase 0 문서화 완료 (VISION, MIGRATION_TASKS, CHECKLIST) |

---

## 핵심 결정사항 (2025-12-31)

### 구조 결정
- **서버 위치**: `greeum/server/` 신규 생성 (기존 `api/`는 유지)
- **API 경로**: 버전 없이 `/memory`, `/search`, `/stats`
- **하위호환**: 기존 `/v1/anchors`는 유지 (api/anchors.py import)

### 오픈소스 전략: Open Core
```
오픈소스 (MIT 유지)           │  유료/비공개 (향후)
──────────────────────────────┼──────────────────────
• greeum/core/               │  • 클라우드 호스팅 서비스
• greeum/server/             │  • 관리 대시보드
• greeum/client/             │  • 멀티테넌트 지원
• greeum/mcp/                │  • SLA 기술지원
• 로컬 셀프호스팅            │  • 엔터프라이즈 기능
```

---

## 메모

- **첫 사용자**: 본인 (dryrain PC를 서버로 사용)
- **MCP 호환성**: 반드시 유지 (폴백 로직 필수)
- **core/ 모듈**: 수정 없이 그대로 재사용
- **맥락 휘발 대비**: Greeum 메모리에 주요 결정사항 저장

---

## 참고 문서

- [GREEUM_V4_VISION.md](docs/GREEUM_V4_VISION.md) - 목표 아키텍처
- [GREEUM_V4_MIGRATION_TASKS.md](docs/GREEUM_V4_MIGRATION_TASKS.md) - 상세 작업 목록
- [사업화문서.txt](~/바탕화면/Shared/사업화문서.txt) - 원본 요구사항
