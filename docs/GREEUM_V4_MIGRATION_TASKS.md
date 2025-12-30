# Greeum v4.0 마이그레이션 작업 목록

**문서 버전**: 1.0
**작성일**: 2025-12-31
**관련 문서**: [GREEUM_V4_VISION.md](./GREEUM_V4_VISION.md)

---

## 개요

이 문서는 Greeum v3.x에서 v4.0으로 전환하기 위해 필요한 모든 작업을 정리합니다.

---

## Phase 1: API 서버 구현 (v4.0-alpha)

### 1.1 서버 기본 구조 생성

| # | 작업 | 파일 | 설명 | 의존성 |
|---|-----|------|------|-------|
| 1.1.1 | FastAPI 앱 생성 | `greeum/server/app.py` | FastAPI 인스턴스, CORS, 미들웨어 설정 | 없음 |
| 1.1.2 | 서버 설정 모듈 | `greeum/server/config.py` | 포트, DB 경로, 로깅 레벨 등 | 없음 |
| 1.1.3 | Pydantic 스키마 | `greeum/server/schemas/` | 요청/응답 모델 정의 | 없음 |
| 1.1.4 | 에러 핸들러 | `greeum/server/middleware/error_handler.py` | 공통 예외 처리 | 1.1.1 |
| 1.1.5 | 로깅 미들웨어 | `greeum/server/middleware/logging.py` | 요청/응답 로깅 | 1.1.1 |

### 1.2 엔드포인트 구현

| # | 작업 | 파일 | 설명 | 의존성 |
|---|-----|------|------|-------|
| 1.2.1 | 헬스체크 | `greeum/server/routes/health.py` | `GET /`, `GET /health` | 1.1.1 |
| 1.2.2 | 기억 추가 | `greeum/server/routes/memory.py` | `POST /memory` | 1.1.3 |
| 1.2.3 | 기억 조회 | `greeum/server/routes/memory.py` | `GET /memory/{id}` | 1.2.2 |
| 1.2.4 | 기억 검색 | `greeum/server/routes/search.py` | `POST /search` | 1.1.3 |
| 1.2.5 | 유사 검색 | `greeum/server/routes/search.py` | `POST /search/similar` | 1.2.4 |
| 1.2.6 | 통계 조회 | `greeum/server/routes/admin.py` | `GET /stats`, `GET /stats/usage` | 1.1.1 |
| 1.2.7 | 시스템 진단 | `greeum/server/routes/admin.py` | `POST /admin/doctor` | 1.2.6 |

### 1.3 Core 연동

| # | 작업 | 파일 | 설명 | 의존성 |
|---|-----|------|------|-------|
| 1.3.1 | 서비스 레이어 생성 | `greeum/server/services/memory_service.py` | Core 모듈 래핑 | 1.2.2 |
| 1.3.2 | 의존성 주입 설정 | `greeum/server/dependencies.py` | FastAPI Depends 패턴 | 1.3.1 |
| 1.3.3 | DB 초기화 로직 | `greeum/server/startup.py` | 서버 시작 시 DB 연결 | 1.3.1 |

### 1.4 서버 실행

| # | 작업 | 파일 | 설명 | 의존성 |
|---|-----|------|------|-------|
| 1.4.1 | CLI 진입점 | `greeum/server/__main__.py` | `python -m greeum.server` | 1.3.3 |
| 1.4.2 | pyproject.toml 수정 | `pyproject.toml` | `greeum-server` 스크립트 추가 | 1.4.1 |
| 1.4.3 | 기본 테스트 | `tests/server/test_basic.py` | 서버 시작/중지 테스트 | 1.4.1 |

### Phase 1 검증 기준
- [ ] `greeum-server` 명령으로 서버 시작
- [ ] `GET /health` 응답 200
- [ ] `POST /memory` 기억 추가 성공
- [ ] `POST /search` 검색 결과 반환
- [ ] 기존 MCP 서버 여전히 동작

---

## Phase 2: MCP 래퍼 전환 (v4.0-beta)

### 2.1 API 클라이언트

| # | 작업 | 파일 | 설명 | 의존성 |
|---|-----|------|------|-------|
| 2.1.1 | HTTP 클라이언트 | `greeum/client/http_client.py` | requests/httpx 래핑 | Phase 1 |
| 2.1.2 | 재시도 로직 | `greeum/client/http_client.py` | 연결 실패 시 재시도 | 2.1.1 |
| 2.1.3 | GreeumClient 클래스 | `greeum/client/client.py` | 고수준 API | 2.1.1 |

### 2.2 로컬 STM 캐시

| # | 작업 | 파일 | 설명 | 의존성 |
|---|-----|------|------|-------|
| 2.2.1 | STM 슬롯 구조 | `greeum/client/stm_cache.py` | 3슬롯, 블록 좌표 저장 | 없음 |
| 2.2.2 | 요약 프롬프트 생성 | `greeum/client/stm_cache.py` | 10회 갱신마다 재작성 | 2.2.1 |
| 2.2.3 | 로컬 저장 | `greeum/client/stm_cache.py` | JSON 파일 저장 | 2.2.1 |
| 2.2.4 | 캐시 만료 정책 | `greeum/client/stm_cache.py` | TTL 기반 정리 | 2.2.1 |

### 2.3 MCP 서버 수정

| # | 작업 | 파일 | 설명 | 의존성 |
|---|-----|------|------|-------|
| 2.3.1 | API 모드 플래그 | `greeum/mcp/config.py` | `GREEUM_USE_API=true` 환경변수 | 2.1.3 |
| 2.3.2 | 도구 핸들러 분기 | `greeum/mcp/server_core.py` | API 모드 시 HTTP 호출 | 2.3.1 |
| 2.3.3 | STM 캐시 통합 | `greeum/mcp/server_core.py` | 검색 전 STM 확인 | 2.2.1 |
| 2.3.4 | 폴백 로직 | `greeum/mcp/server_core.py` | API 실패 시 직접 호출 | 2.3.2 |

### 2.4 하위 호환성 테스트

| # | 작업 | 파일 | 설명 | 의존성 |
|---|-----|------|------|-------|
| 2.4.1 | MCP 기능 테스트 | `tests/mcp/test_compatibility.py` | 모든 도구 동작 확인 | 2.3.4 |
| 2.4.2 | 데이터 무결성 | `tests/mcp/test_data_integrity.py` | API 경유 저장 데이터 검증 | 2.4.1 |
| 2.4.3 | 성능 비교 | `tests/mcp/test_performance.py` | 직접 호출 vs API 호출 | 2.4.1 |

### Phase 2 검증 기준
- [ ] `GREEUM_USE_API=true` 시 API 서버로 요청
- [ ] `GREEUM_USE_API=false` 시 기존 방식 동작 (호환성)
- [ ] STM 캐시 로컬 저장/로드 정상
- [ ] API 서버 다운 시 폴백 동작

---

## Phase 3: 안정화 및 배포 (v4.0)

### 3.1 성능 최적화

| # | 작업 | 설명 | 의존성 |
|---|-----|------|-------|
| 3.1.1 | 연결 풀링 | HTTP 클라이언트 연결 재사용 | Phase 2 |
| 3.1.2 | 배치 API | 다건 기억 추가/검색 | Phase 2 |
| 3.1.3 | 캐싱 레이어 | 자주 검색되는 결과 캐싱 | Phase 2 |

### 3.2 운영 기능

| # | 작업 | 설명 | 의존성 |
|---|-----|------|-------|
| 3.2.1 | 프로세스 관리 | systemd 서비스 파일 | 3.1.1 |
| 3.2.2 | 로그 로테이션 | 로그 파일 관리 | 3.2.1 |
| 3.2.3 | 헬스체크 스크립트 | 모니터링용 스크립트 | 3.2.1 |

### 3.3 문서화

| # | 작업 | 설명 | 의존성 |
|---|-----|------|-------|
| 3.3.1 | API 문서 | OpenAPI/Swagger 자동 생성 확인 | Phase 1 |
| 3.3.2 | 마이그레이션 가이드 | v3 → v4 전환 안내 | Phase 2 |
| 3.3.3 | 클라이언트 사용법 | Python 클라이언트 예제 | 2.1.3 |
| 3.3.4 | README 업데이트 | 새로운 기능 반영 | 3.3.2 |

### 3.4 배포

| # | 작업 | 설명 | 의존성 |
|---|-----|------|-------|
| 3.4.1 | 버전 범프 | pyproject.toml 버전 4.0.0 | 3.3.4 |
| 3.4.2 | CHANGELOG 작성 | 변경사항 정리 | 3.4.1 |
| 3.4.3 | PyPI 배포 | pip install greeum 업데이트 | 3.4.2 |

### Phase 3 검증 기준
- [ ] 24시간 연속 운영 안정성
- [ ] 기억 추가 < 500ms (99th)
- [ ] 기억 검색 < 300ms (99th)
- [ ] 문서 완비

---

## 작업 우선순위 요약

### 즉시 시작 가능 (의존성 없음)
1. `1.1.1` FastAPI 앱 생성
2. `1.1.2` 서버 설정 모듈
3. `1.1.3` Pydantic 스키마
4. `2.2.1` STM 슬롯 구조 (병렬 진행 가능)

### 핵심 경로 (Critical Path)
```
1.1.1 → 1.2.1 → 1.2.2 → 1.3.1 → 1.4.1 → Phase 1 완료
                                    ↓
                              2.1.1 → 2.3.2 → 2.4.1 → Phase 2 완료
                                                    ↓
                                              3.4.1 → v4.0 릴리스
```

### 예상 작업량

| Phase | 작업 수 | 예상 규모 |
|-------|--------|----------|
| Phase 1 | 14개 | 신규 코드 ~1,500줄 |
| Phase 2 | 12개 | 신규 코드 ~800줄, 수정 ~300줄 |
| Phase 3 | 10개 | 문서 + 설정 위주 |

---

## 체크리스트

### Phase 1 완료 조건
- [ ] 서버 독립 실행 가능
- [ ] 모든 핵심 엔드포인트 동작
- [ ] 기본 테스트 통과
- [ ] 기존 MCP 영향 없음

### Phase 2 완료 조건
- [ ] MCP가 API 경유로 동작
- [ ] STM 캐시 로컬 저장
- [ ] 하위 호환성 100%
- [ ] 폴백 메커니즘 동작

### Phase 3 완료 조건
- [ ] 성능 목표 달성
- [ ] 운영 환경 준비
- [ ] 문서 완비
- [ ] PyPI 배포

---

## 리스크 및 대응

| 리스크 | 가능성 | 영향 | 대응 |
|-------|-------|-----|------|
| API 성능 저하 | 중 | 중 | 연결 풀링, 캐싱 |
| MCP 호환성 깨짐 | 저 | 고 | 폴백 로직, 충분한 테스트 |
| DB 마이그레이션 필요 | 저 | 중 | 스키마 동일 유지 |
| 임베딩 모델 로드 시간 | 중 | 저 | 서버 시작 시 워밍업 |

---

**문서 끝**
