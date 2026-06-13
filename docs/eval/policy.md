# Greeum 평가 정책 (Evaluation Policy)

**Effective**: 2026-06-14
**Owner**: Greeum maintainer

이 문서는 Greeum의 품질·USP·운영 지표를 어떻게 측정하고 회귀를 차단하는지 정의한다.
모든 코드·모델·하이퍼파라미터 변경은 이 지표에 비추어 평가된다.

## 핵심 지표

| 축 | 지표 | 데이터 | 방향 | 비고 |
|----|------|--------|------|------|
| 검색 품질 — 내부 | recall@1/5/10, MRR, pair-AUC | 라이브 DB의 semantic+causal association 쌍 | 모두 ↑ | 현재까지 결정 근거였던 측정 |
| 검색 품질 — 외부 | nDCG@10, Recall@10, MRR | MIRACL-Korean | 모두 ↑ | 다국어 IR 공신력 (Eval-C) |
| **USP — 로그-스케일** | recall@k 곡선 vs N(메모리 크기) | NIAH-스타일 합성 | **기울기 평평할수록 ↑** | Greeum 핵심 차별점 (Eval-B) |
| USP — 비교 | (Greeum hybrid) - (vanilla vector) gap | 동일 NIAH | gap ↑ at 큰 N | "왜 Greeum이 좋은가" 정량화 |
| 운영 | search latency p50/p95, ingest p95 | 자체 micro-bench | ↓ | 회귀 감지용 |

## 임계값 (hard_fail / warn)

베이스라인 측정 후 이 표에 채워넣고 PR block에 사용한다.
초기 임계값은 **baseline × 0.90** (10% 회귀까지 허용), warn은 baseline × 0.95.
시간이 지나며 더 빡빡하게 조일 수 있으나 *완화는 명시적 결재 필요*.

```yaml
# scripts/eval/policy.yml 에 머신-리더블 형태로 별도 보관
```

## 측정 계층 (비용 vs 빈도)

| 계층 | 언제 | 무엇 | 예상 시간 |
|------|------|------|----------|
| **Smoke** | 매 커밋·PR (CI) | internal bench 미니(50쿼리) + NIAH N=1K | 2~5분 |
| **Standard** | 주 1회 / 모델·가중치 변경 PR | full internal + MIRACL-Ko 1K subset + NIAH N=1K/3K/10K | 30분~1시간 |
| **Release** | v5.x 릴리스 직전 | 위 + MIRACL-Ko full + NIAH N=100K | 반나절~ |

## 베이스라인 freeze 규칙

1. **시점 못 박기**: 베이스라인 JSON은 `docs/eval/baseline_<level>_<YYYY-MM-DD>.json` 형식. 시점이 명확해야 회귀 비교가 가능.
2. **재측정 가능성**: 동일 commit + 동일 데이터 + 동일 시드로 재실행 시 동일 결과(±noise) 보장. 시드 고정 필수.
3. **확장만, 교체 금지**: 새 지표는 추가하되 기존 지표 임계값은 *완화 결재* 거치지 않으면 변경 불가.

## 측정 환경

- **Python**: 3.12.x (시스템 또는 `~/.greeum_bench_venv` venv)
- **모델 캐시**: HF `~/.cache/huggingface/hub`
- **시드**: `42` (numpy, random, torch where applicable)
- **하드웨어**: 측정에 GPU 사용 시 결과 JSON에 명시

## 곡선 비교 (USP 특별 케이스)

USP는 단일 점수가 아니라 곡선의 *기울기*가 평가 대상.

```
recall_at_10 vs log10(N):
  Greeum hybrid:   N=1K → .82, N=10K → .76, N=100K → .68  (slope -.07/decade)
  Vanilla vector:  N=1K → .80, N=10K → .60, N=100K → .35  (slope -.225/decade)
  → Greeum이 vanilla 대비 3배 평평 = USP 확인
```

기울기가 vanilla보다 **유의미하게 평평**(예: 절댓값 < vanilla 의 1/2)이면 USP 충족.

## 회귀 발생 시 처리

1. CI smoke fail → PR block + 알림
2. 메인테이너 검토 → (a) 코드 수정 (b) baseline 갱신(드물게, 명시적 사유 + 커밋 메시지) (c) 임계값 완화(결재 필요)
3. 매 회귀는 `docs/eval/regressions/<YYYY-MM-DD>.md`에 사유 기록

## 관련 파일

- 정책: `docs/eval/policy.md` (이 문서)
- 머신-리더블 정책: `scripts/eval/policy.yml`
- 베이스라인: `docs/eval/baseline_*.json`
- 측정 스크립트: `scripts/eval/*.py`
- 결과: `docs/eval/results/<run-id>.json`
