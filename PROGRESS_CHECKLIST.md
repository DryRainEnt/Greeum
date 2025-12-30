# Greeum v4.0 작업 현황 체크리스트

**최종 업데이트**: 2025-12-31
**현재 단계**: Phase 1 준비 완료

---

## 전체 진행 상황

| Phase | 상태 | 진행률 |
|-------|-----|-------|
| Phase 0: 설계 | **완료** | 100% |
| Phase 1: API 서버 | 대기 | 0% |
| Phase 2: MCP 래퍼 | 대기 | 0% |
| Phase 3: 안정화 | 대기 | 0% |

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

## Phase 1: API 서버 구현 [대기]

### 1.1 서버 기본 구조
- [ ] `greeum/server/__init__.py` 생성
- [ ] `greeum/server/app.py` - FastAPI 앱
- [ ] `greeum/server/config.py` - 서버 설정
- [ ] `greeum/server/schemas/` - Pydantic 모델
- [ ] `greeum/server/middleware/error_handler.py`
- [ ] `greeum/server/middleware/logging.py`

### 1.2 엔드포인트 구현
- [ ] `GET /` - 서버 정보
- [ ] `GET /health` - 헬스체크
- [ ] `POST /memory` - 기억 추가
- [ ] `GET /memory/{id}` - 기억 조회
- [ ] `POST /search` - 기억 검색
- [ ] `POST /search/similar` - 유사 검색
- [ ] `GET /stats` - 통계 조회
- [ ] `POST /admin/doctor` - 시스템 진단

### 1.3 Core 연동
- [ ] `greeum/server/services/memory_service.py`
- [ ] `greeum/server/dependencies.py`
- [ ] `greeum/server/startup.py`

### 1.4 서버 실행
- [ ] `greeum/server/__main__.py`
- [ ] `pyproject.toml` 스크립트 추가
- [ ] 기본 테스트 작성

### Phase 1 검증
- [ ] `greeum-server` 명령 실행 확인
- [ ] `GET /health` 응답 200
- [ ] `POST /memory` 동작 확인
- [ ] `POST /search` 동작 확인
- [ ] 기존 MCP 영향 없음 확인

---

## Phase 2: MCP 래퍼 전환 [대기]

### 2.1 API 클라이언트
- [ ] `greeum/client/__init__.py`
- [ ] `greeum/client/http_client.py`
- [ ] `greeum/client/client.py` (GreeumClient)

### 2.2 로컬 STM 캐시
- [ ] `greeum/client/stm_cache.py` - 슬롯 구조
- [ ] 요약 프롬프트 생성 로직
- [ ] 로컬 저장 (JSON)
- [ ] 캐시 만료 정책

### 2.3 MCP 서버 수정
- [ ] `GREEUM_USE_API` 환경변수 지원
- [ ] API 모드 분기 로직
- [ ] STM 캐시 통합
- [ ] 폴백 메커니즘

### Phase 2 검증
- [ ] API 모드 정상 동작
- [ ] 직접 모드 호환성 유지
- [ ] STM 캐시 저장/로드
- [ ] 폴백 동작 확인

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

---

## 커밋 히스토리

| 날짜 | 커밋 | 내용 |
|-----|------|-----|
| 2025-12-31 | b0d74e2 | Phase 0 문서화 완료 (VISION, MIGRATION_TASKS, CHECKLIST) |

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
