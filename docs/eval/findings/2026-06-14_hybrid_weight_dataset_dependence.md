# Finding: 하이브리드 가중치 0.7/0.3은 데이터-의존적 (MIRACL-Ko에선 차선)

**Date**: 2026-06-14
**Source**: `docs/eval/results/miracl_ko_standard_2026-06-14.json`
**Severity**: Medium — 실제로 v5.4 default 결정에 영향

## 발견

라이브 DB(334블록, 개인 메모리, 한/영 혼재) 벤치마크에서 골랐던 **`vec=0.7, bm25=0.3`** 가중치를
**MIRACL-Korean dev (100q × 2187 passages, 한국어 위키)** 에서 측정해보니 vanilla vector-only 대비
크게 손해:

| 모드 | nDCG@10 | Recall@10 | MRR | search p50 ms |
|------|---------|-----------|-----|---------------|
| **vanilla vector** (vec_w=1.0) | **.819** | **.794** | **.948** | 7.97 |
| **greeum_hybrid** (vec=0.7, bm25=0.3) | .669 | .713 | .785 | 4.88 |
| Δ (vanilla − hybrid) | +.150 | +.081 | +.163 | — |

라이브 DB 측정에선 정확히 반대였음(0.7/0.3이 모든 임베딩 후보 대비 우월). 즉 가중치 최적값은
**데이터 분포에 강하게 의존**.

## 추정 원인

1. MIRACL 코퍼스 = 한국어 위키 — 정형·사실·균일 텍스트
2. Greeum의 BM25 키워드 추출(`extract_keywords_from_text`, 최대 10개) 위키 텍스트엔 노이즈
3. e5-small 벡터는 한국어 위키 검색에 이미 강함 — BM25 30%를 더하면 강한 신호에 노이즈 섞기
4. 우리 라이브 DB는 비정형 대화·메모, 키워드 가시성↑ — BM25가 진짜 신호로 작동

## 시사점 / 권고

### 즉시 결정 필요
- **default 가중치 0.7/0.3 유지 여부**: 본인 사용성(개인 메모리)엔 최적, 외부 RAG/위키 검색엔 차선
- 환경변수(`GREEUM_HYBRID_VEC_WEIGHT`, `GREEUM_HYBRID_BM25_WEIGHT`) 이미 노출 — 사용자별 튜닝 가능
- 문서에 "데이터 종류별 권장 가중치" 표 추가 권장

### v5.4 릴리스 전에 검토
- (a) **현 0.7/0.3 유지** + 데이터별 가이드 문서 (적은 변경, 보수적)
- (b) **default를 0.9/0.1로 상향** (양쪽 데이터에 덜 손해, 단 라이브 DB 성능 일부 하락 측정 필요)
- (c) **BM25 키워드 추출 개선** (10-cap 제거, 전체 토큰 + IDF) — 더 큰 작업

### 후속 측정
- MIRACL-Ko에서 가중치 sweep(0.5/0.5 → 1.0/0.0) 돌려 변곡점 확인
- 라이브 DB에서 0.9/0.1로 재측정해 손실 폭 정량화

## 사후 합리화 방지 메모

이 발견은 *벤치마크가 결정 근거를 흔든* 사례 — 정확히 우리가 "추측 말고 실측"으로 방지하려던 상황.
정책에 따라:
- 절대 가중치 변경은 새 데이터 측정 결과를 근거로만
- 데이터별 최적 가중치가 다르면 그 사실 자체를 문서화 (단일 값 강요하지 않음)

## 관련

- 정책: `docs/eval/policy.md`
- 라이브 DB 베이스라인: `docs/eval/baseline_internal_standard_2026-06-14.json`
- MIRACL-Ko 베이스라인: `docs/eval/baseline_miracl_ko_standard_2026-06-14.json`
- 가중치 환경변수: `GREEUM_HYBRID_VEC_WEIGHT`, `GREEUM_HYBRID_BM25_WEIGHT`
- 가중치 기본값: `greeum/core/bm25_index.py::_default_hybrid_weights`
