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

## 후속 (2026-06-14 같은 날) — sweep 측정 후 default를 **0.9/0.1로 상향**

위 분석 직후 양 데이터에서 가중치 sweep (0.5/0.5, 0.7/0.3, 0.8/0.2, 0.9/0.1, 1.0/0.0):

| config | live DB R@10 | live DB MRR | MIRACL-Ko nDCG@10 |
|--------|:---:|:---:|:---:|
| 0.5 / 0.5 | — | — | .714 |
| 0.7 / 0.3 (이전 default) | .477 | .502 | .803 |
| 0.8 / 0.2 | .497 | .508 | .843 |
| **0.9 / 0.1 (새 default)** | **.540** | **.551** | **.876** |
| 1.0 / 0.0 (vanilla) | .518 | .520 | .877 |

**결론**: 0.9/0.1이 양 데이터에서 0.7/0.3을 strictly dominate. 손실 axis 없음.

원인 추정: 기존 0.7/0.3은 Model2Vec(potion-multilingual)의 peak였음. v5.4에서
default ST 모델을 minilm → multilingual-e5-small로 swap한 시점부터 e5의 더 강한
vector signal에 맞춰 가중치도 vec-heavy(0.9/0.1)로 같이 갱신했어야 함.

### 변경 사항 (2026-06-14)
- `greeum/core/bm25_index.py::_default_hybrid_weights()` default 변경 (0.7/0.3 → 0.9/0.1)
- 베이스라인 4개 모두 새 default로 재측정·갱신
- CLAUDE.md 기본값 표기 갱신
- `docs/eval/tuning_guide.md` 신규 작성: 데이터 종류별 가중치 권장값

### 정책 충실도
- 회귀-추적 워크플로우의 첫 실전 사례: 측정이 default를 흔들었고, *측정이 가르치는 대로* 따랐음
- 회귀 체커는 "max" 방향 — 새 값이 더 높으면 통과 (실제로 모든 베이스라인 새 값으로 갱신해도 통과)
- 환경변수 override 여전히 작동 → 사용자별·데이터별 튜닝 가능

## 관련

- 정책: `docs/eval/policy.md`
- 라이브 DB 베이스라인: `docs/eval/baseline_internal_standard_2026-06-14.json`
- MIRACL-Ko 베이스라인: `docs/eval/baseline_miracl_ko_standard_2026-06-14.json`
- 가중치 환경변수: `GREEUM_HYBRID_VEC_WEIGHT`, `GREEUM_HYBRID_BM25_WEIGHT`
- 가중치 기본값: `greeum/core/bm25_index.py::_default_hybrid_weights`
