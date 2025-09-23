# Performance Tuning Checklist

단기/장기 메모리 경합과 임베딩 로딩 지연을 줄이기 위한 단계별 계획입니다. 각 단계가 끝날 때마다 기록을 남겨 다음 작업자가 이어받을 수 있도록 합니다.

## 1. 현황 계측
- [ ] `greeum mcp serve -t stdio` + `greeum memory add/search` 왕복 시간을 10회 측정하고 평균·p95 값을 기록하기 (`scripts/bench_memory.py` 초안 작성).
- [ ] `/tmp/greeum_codex_stdio.log` 및 SQLite `busy_timeout` 경고 수를 집계해 baseline 확보.

## 2. 쓰기 직렬화 & 재시도 정책
- [x] `DatabaseManager.run_serialized()`로 공용 쓰기 락/대기 경고(`GREEUM_SQLITE_WRITE_WARN`, 기본 5초) 도입.
- [ ] 큐 또는 전용 워커 스레드 기반 직렬화로 확대(필요 시 anyio 적용).

## 3. SQLite 설정 최적화
- [ ] `PRAGMA busy_timeout`을 실측 기반으로 1–2초 내외로 조정하고 환경 변수(`GREEUM_SQLITE_BUSY_TIMEOUT`) 문서화.
- [ ] WAL 모드 유지 여부, `synchronous`/`temp_store` 조합 검증.

## 4. 임베딩 로딩 개선
- [ ] `greeum setup` 수행 시 SentenceTransformer 미리 로딩하고 캐시 경로 검증.
- [ ] 실행 중에는 lazy singleton을 통해 모델 재사용, 폴백(SimpleEmbedding) 경로는 즉시 반환하도록 분리.

## 5. 테스트 & 자동화
- [ ] `pytest -m "perf"` 태그로 성능 회귀 테스트 추가 (30초 이내 목표, 초과 시 실패).
- [ ] CI에 선택 실행 단계 문서화 (`docs/greeum-workflow-guide.md`에 링크 추가).

## 6. 문서 업데이트
- [ ] README 및 한국어 가이드(`docs/README_ko.md`)에 튜닝 관련 환경 변수와 설정 절차 반영.
- [ ] 로컬에서 락 경고가 발생할 경우 대응 방법(큐 상태 확인, busy_timeout 조정)을 FAQ에 추가.

> 체크리스트는 작업자의 진행 상황을 남기는 용도로 활용합니다. 각 항목 옆에 담당자 이니셜과 날짜를 적어 두면 컨텍스트 압축 후에도 추적이 가능합니다.
