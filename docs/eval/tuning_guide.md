# Hybrid 가중치 튜닝 가이드

**대상**: Greeum을 RAG/메모리 레이어로 쓰는 모든 사용자
**범위**: `HybridScorer`의 `vector_weight` / `bm25_weight` 환경 변수 튜닝
**Status**: v5.4+ (default 0.9/0.1, 2026-06-14 기준)

## TL;DR

| 데이터 종류 | 권장 (vec / bm25) | env |
|------------|:---:|:---:|
| 개인 메모리, 대화 노트, RAG 일반 | **0.9 / 0.1** (default) | (설정 불필요) |
| Wikipedia·뉴스·formal 문서 검색 | **0.9 / 0.1** 또는 1.0 / 0.0 | `GREEUM_HYBRID_VEC_WEIGHT=1.0` `GREEUM_HYBRID_BM25_WEIGHT=0.0` |
| 짧은 태그·키워드 중심 메모 (예: 제품 카탈로그) | **0.7 / 0.3** 또는 0.5 / 0.5 | `GREEUM_HYBRID_VEC_WEIGHT=0.7` `GREEUM_HYBRID_BM25_WEIGHT=0.3` |
| 다국어·노이즈 많은 텍스트 | 0.9 / 0.1 (default) | (default) |

## 왜 default가 0.9/0.1인가

v5.4부터 default ST 모델이 `multilingual-e5-small`로 바뀌었습니다. e5 가족은
강한 의미 임베딩이라 BM25 시그널이 노이즈처럼 작용해 vector signal을 희석시킵니다.
2026-06-14 sweep 측정에서 **양 데이터에서 0.9/0.1이 0.7/0.3을 strictly dominate**:

| Config | 라이브 DB R@10 | 라이브 DB MRR | MIRACL-Korean nDCG@10 |
|--------|:---:|:---:|:---:|
| 0.7 / 0.3 (v5.4 이전 default) | .477 | .502 | .803 |
| **0.9 / 0.1 (현 default)** | **.540** | **.551** | **.876** |

자세한 측정·결정 과정: `docs/eval/findings/2026-06-14_hybrid_weight_dataset_dependence.md`.

## BM25 비중을 높여야 하는 경우 (드묾)

다음 시나리오에서 BM25 비중 상향이 의미 있을 수 있습니다:

1. **짧은 텍스트가 다수**: 임베딩이 충분한 신호를 못 잡는 ~10 토큰 이하 메모리.
   BM25는 정확 매칭으로 보조.
2. **태그·키워드 중심 검색**: 메모리에 명시적 태그/키워드가 많고, 쿼리도 같은
   토큰을 포함.
3. **OOV(out-of-vocabulary) 토큰 많음**: 임베딩이 모르는 고유명사·코드·제품명이
   검색의 핵심.
4. **다언어 코퍼스인데 임베딩이 한쪽 언어에 약함**: BM25는 언어 독립적이라 보완.

이 경우 0.7/0.3 또는 0.5/0.5를 시도해 보세요. **반드시 본인 데이터에서 측정**:

```bash
GREEUM_HYBRID_VEC_WEIGHT=0.7 \
GREEUM_HYBRID_BM25_WEIGHT=0.3 \
python scripts/eval/internal_bench.py --tier standard --out /tmp/your_bench.json
```

## 측정 방법

본인 데이터에서 튜닝하려면:

1. 라이브 DB를 베이스라인으로 측정:
   ```bash
   make eval-standard
   ```
2. 가중치를 바꿔 재측정:
   ```bash
   GREEUM_HYBRID_VEC_WEIGHT=0.8 GREEUM_HYBRID_BM25_WEIGHT=0.2 \
     python scripts/eval/internal_bench.py --tier standard \
     --out docs/eval/results/internal_w0.8_0.2.json
   ```
3. R@10·MRR·nDCG@10 비교

## 영구 설정

systemd 서비스의 env에 추가:

```ini
[Service]
Environment=GREEUM_HYBRID_VEC_WEIGHT=0.9
Environment=GREEUM_HYBRID_BM25_WEIGHT=0.1
```

또는 사용자 셸 rc에 추가:

```bash
export GREEUM_HYBRID_VEC_WEIGHT=0.9
export GREEUM_HYBRID_BM25_WEIGHT=0.1
```

## 측정되지 않은 경계 / 향후 작업

- 매우 짧은 메모리(< 5 토큰)와 매우 긴 메모리(> 500 토큰) 양 극단에서의 최적 가중치
- BM25 키워드 추출의 10-cap 제거 후 재측정
- 비대칭 prefix(query/passage) 도입 시 가중치 변화
- 더 큰 N (100K+) 메모리에서의 안정성

위 항목은 후속 측정 대상 — 현 default는 측정된 범위 내에서 최적입니다.
