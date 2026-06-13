#!/usr/bin/env python3
"""NIAH-style scaling test — Greeum's log-shaped USP measurement.

For each memory size N in a sweep (e.g., 200 / 1K / 3K / 10K), we:
  1. Inject K ``needle`` memories — each carries a unique fact and a unique
     synthetic identifier so the retrieval task has one right answer.
  2. Pad to N total with ``filler`` memories sampled from a fixed pool.
  3. Embed everything once (real ST encoding using the registry default).
  4. For each needle, run a query and check whether the needle is in the top-k.
  5. Report recall@1/5/10 and the curve of (N → recall@k).

Comparison baselines:
  - ``vanilla_vector``  — cosine sim only (the bottom-up baseline)
  - ``greeum_hybrid``   — BM25 + vector at the production weights (Greeum's value-add)

The USP claim — "memory growth degrades quality logarithmically, not
exponentially" — is verified by comparing the two slopes on the (log N, recall)
plot:

    if slope(greeum_hybrid) / slope(vanilla_vector) << 1, the USP holds.

Determinism: fixed seed; same Greeum default model = same numbers across runs
(modulo torch CUDA reduction order, which is tiny).
"""
from __future__ import annotations

import argparse
import json
import os
import random
import statistics
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Tuple

import numpy as np

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if (_REPO_ROOT / "greeum" / "__init__.py").exists():
    sys.path.insert(0, str(_REPO_ROOT))

from greeum.text_utils import extract_keywords_from_text  # noqa: E402
from greeum.core.bm25_index import BM25Index, _default_hybrid_weights  # noqa: E402

SEED = 42

# ---------------------------------------------------------------------------
# Synthetic corpus

_KO_TEMPLATES = [
    "오늘 회의에서 결정된 사항은 {topic} 우선순위를 높이는 것이다.",
    "{topic} 시스템 점검 결과 일부 모듈에서 응답 지연이 발견됐다.",
    "프로젝트 {topic} 의 이번 주 마일스톤은 베타 배포다.",
    "사용자 피드백 정리: {topic} 흐름이 직관적이지 않다는 의견 다수.",
    "DB 마이그레이션 시 {topic} 인덱스 재구축이 필요할 수 있다.",
    "리포트 작성 중인 {topic} 항목은 다음 주 월요일 제출 예정.",
    "{topic} 에 관한 외부 컨설팅 미팅이 다음 분기로 미뤄졌다.",
    "회고 — {topic} 관련 의사결정 속도가 느렸다는 점에 의견이 모였다.",
    "{topic} 모듈에서 SQLite 락 충돌이 간헐적으로 발생.",
    "캐시 정책 변경: {topic} 데이터는 TTL 60초로 단축.",
]
_EN_TEMPLATES = [
    "Discussed {topic} prioritization in this morning's standup.",
    "Logged a flaky test in the {topic} pipeline; needs triage.",
    "Slack thread on {topic} confirmed the rollout window for next Tuesday.",
    "Updated the {topic} dashboard with the new latency percentile widgets.",
    "Reviewing the {topic} RFC — split into two follow-up issues.",
    "Filed a bug: {topic} retries don't reset the backoff window.",
    "Took notes on {topic} architecture choices for the design doc.",
    "Pair programming session on {topic} produced a draft patch.",
    "Customer hit a {topic} timeout under heavy concurrent load.",
    "Spec'd out the {topic} schema migration; needs DBA review.",
]
_TOPICS = [
    "임베딩", "벡터", "BM25", "스토리지", "캐시", "RAG", "MCP", "워커", "로깅",
    "indexing", "ranking", "schema", "ingestion", "auth", "telemetry",
    "observability", "branch", "anchor", "consolidator", "search",
    "데이터셋", "프롬프트", "스로틀", "큐", "프로파일러", "샤딩",
    "deployment", "rollback", "cluster", "transcoding", "compression",
]


def _gen_filler(rng: random.Random) -> str:
    tpl = rng.choice(_KO_TEMPLATES + _EN_TEMPLATES)
    return tpl.format(topic=rng.choice(_TOPICS))


_NEEDLE_DOMAINS = [
    ("기후 적응 기금", "일조량 모니터링", "8천만 달러"),
    ("초기 단계 스타트업", "유전자 데이터 라벨링", "27만 달러"),
    ("한국형 발사체", "재진입 차폐재", "탄소 복합 구조"),
    ("도시 재생 정책", "유휴 지하공간", "공공 미디어 아카이브"),
    ("해양 음향 관측", "심해 결빙", "고주파 트랜스듀서"),
    ("디지털 카르타", "산악 구조 신호", "이리듐 위성 링크"),
    ("범용 RAG", "메모리 누적 비용", "anchor 기반 DFS"),
    ("개발자 도구", "교차 컴파일 성능", "ramdisk 캐시"),
    ("문화재 분류", "고려청자 분류", "비파괴 X선 형광"),
    ("교육 평가", "수업 참여도", "음성 활성도 패턴"),
]


def _gen_needle(idx: int, mode: str = "trivial") -> Tuple[str, str]:
    """Return (memory_text, query_text) for the idx-th needle.

    ``mode``:
      - ``trivial``: needle and query share a unique code token (both BM25 and
        vector trivially recover it). Useful for capacity/latency curves but
        NOT a meaningful recall stress test.
      - ``semantic``: paraphrased query with NO unique token overlap; the
        retrieval system must match on semantic content. Used to probe actual
        log-scale degradation.
    """
    domain_idx = idx % len(_NEEDLE_DOMAINS)
    program, focus, detail = _NEEDLE_DOMAINS[domain_idx]
    unique_id = f"NDL-{idx:05d}"
    if mode == "trivial":
        fact = f"비밀 코드 {unique_id} 는 {idx}번 needle 의 식별자다. {program}, {focus}, {detail}."
        query = f"비밀 코드 {unique_id} 가 가리키는 needle 번호는?"
        return fact, query
    # semantic: paraphrased query with no unique-id overlap
    fact = (
        f"{program} 의 {focus} 영역에서 {detail} 를 적용한 사례가 needle {idx} "
        f"({unique_id}) 로 기록됐다."
    )
    # Query is a paraphrase — uses different surface words, no unique id
    query = (
        f"{program} 분야에서 {focus} 관련해 {detail} 가 적용된 기록은?"
    )
    return fact, query


def _build_corpus(N: int, n_needles: int, seed: int,
                  needle_mode: str = "trivial") -> Tuple[List[str], List[Tuple[int, str]]]:
    """Return (corpus, [(needle_corpus_idx, query)]) of length N."""
    rng = random.Random(seed)
    assert n_needles < N, "needles must be fewer than corpus size"
    corpus: List[str] = []
    needle_positions: List[Tuple[int, str]] = []
    positions = sorted(rng.sample(range(N), n_needles))
    pos_set = set(positions)
    needle_iter = iter(range(n_needles))
    for i in range(N):
        if i in pos_set:
            j = next(needle_iter)
            fact, q = _gen_needle(j, mode=needle_mode)
            corpus.append(fact)
            needle_positions.append((i, q))
        else:
            corpus.append(_gen_filler(rng))
    return corpus, needle_positions


# ---------------------------------------------------------------------------
# Scorers

def _build_bm25(corpus: List[str]) -> Tuple[BM25Index, Dict[int, List[str]]]:
    bm25 = BM25Index()
    kws: Dict[int, List[str]] = {}
    for i, text in enumerate(corpus):
        kws[i] = extract_keywords_from_text(text)
        bm25.add_document(str(i), kws[i])
    return bm25, kws


def _vector_rank(emb: np.ndarray, q_emb: np.ndarray, top_k: int) -> List[int]:
    sims = emb @ q_emb
    return list(np.argsort(-sims)[:top_k])


def _hybrid_rank(emb: np.ndarray, q_emb: np.ndarray, bm25: BM25Index,
                 kws: Dict[int, List[str]], q_kws: List[str], top_k: int,
                 vec_w: float, bm25_w: float) -> List[int]:
    sims = np.clip(emb @ q_emb, 0.0, 1.0)
    bm25_scores = np.zeros(len(emb), dtype=np.float32)
    for i in range(len(emb)):
        bm25_scores[i] = bm25.normalize_score(
            bm25.score_with_keywords(q_kws, kws[i])
        )
    combined = vec_w * sims + bm25_w * bm25_scores
    return list(np.argsort(-combined)[:top_k])


def _eval_at_N(N: int, n_needles: int, embedder, top_k: int = 10,
               seed: int = SEED, needle_mode: str = "trivial") -> Dict[str, Any]:
    corpus, needles = _build_corpus(N, n_needles, seed, needle_mode=needle_mode)
    t0 = time.time()
    emb = np.asarray(embedder.batch_encode(corpus), dtype=np.float32)
    embed_s = time.time() - t0

    bm25, kws = _build_bm25(corpus)
    vec_w, bm25_w = _default_hybrid_weights()

    vec_hits = {1: 0, 5: 0, 10: 0}
    hyb_hits = {1: 0, 5: 0, 10: 0}
    vec_search_lats: List[float] = []
    hyb_search_lats: List[float] = []

    for needle_idx, q in needles:
        q_emb = np.asarray(embedder.encode(q), dtype=np.float32)
        q_kws = extract_keywords_from_text(q)

        ts = time.time()
        ranked_v = _vector_rank(emb, q_emb, top_k)
        vec_search_lats.append((time.time() - ts) * 1000.0)

        ts = time.time()
        ranked_h = _hybrid_rank(emb, q_emb, bm25, kws, q_kws, top_k, vec_w, bm25_w)
        hyb_search_lats.append((time.time() - ts) * 1000.0)

        for k in (1, 5, 10):
            if needle_idx in ranked_v[:k]:
                vec_hits[k] += 1
            if needle_idx in ranked_h[:k]:
                hyb_hits[k] += 1

    def _rec(hits, k): return round(hits[k] / len(needles), 4)
    return {
        "N": N,
        "n_needles": len(needles),
        "embed_total_s": round(embed_s, 2),
        "vanilla_vector": {
            "recall@1": _rec(vec_hits, 1),
            "recall@5": _rec(vec_hits, 5),
            "recall@10": _rec(vec_hits, 10),
            "search_p50_ms": round(statistics.median(vec_search_lats), 2),
            "search_p95_ms": round(_percentile(vec_search_lats, 95), 2),
        },
        "greeum_hybrid": {
            "recall@1": _rec(hyb_hits, 1),
            "recall@5": _rec(hyb_hits, 5),
            "recall@10": _rec(hyb_hits, 10),
            "search_p50_ms": round(statistics.median(hyb_search_lats), 2),
            "search_p95_ms": round(_percentile(hyb_search_lats, 95), 2),
            "weights": {"vec": vec_w, "bm25": bm25_w},
        },
    }


def _percentile(values: List[float], p: float) -> float:
    if not values: return 0.0
    s = sorted(values)
    k = (len(s) - 1) * (p / 100.0)
    f = int(k); c = min(f + 1, len(s) - 1)
    return s[f] if f == c else s[f] + (s[c] - s[f]) * (k - f)


def _slope_per_decade(points: List[Tuple[int, float]]) -> float:
    """Linear fit of y vs log10(N); return slope per decade."""
    if len(points) < 2: return 0.0
    xs = np.log10([n for n, _ in points])
    ys = np.array([y for _, y in points])
    slope, _ = np.polyfit(xs, ys, 1)
    return float(round(slope, 4))


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--N", default="200,1000,3000,10000",
                   help="Comma-separated memory sizes to sweep")
    p.add_argument("--needles", type=int, default=50,
                   help="Number of needle memories per N (must be < min N)")
    p.add_argument("--seed", type=int, default=SEED)
    p.add_argument("--out", required=True)
    p.add_argument("--needle-mode", choices=["trivial", "semantic"], default="trivial",
                   help="trivial: query shares unique id with needle (latency curve only). "
                        "semantic: paraphrased query with no id overlap (recall stress test).")
    args = p.parse_args()

    Ns = [int(x) for x in args.N.split(",")]
    if args.needles >= min(Ns):
        print(f"--needles ({args.needles}) must be smaller than smallest N ({min(Ns)})",
              file=sys.stderr)
        return 2

    random.seed(args.seed); np.random.seed(args.seed)

    from greeum.embedding_models import EmbeddingRegistry
    reg = EmbeddingRegistry()
    embedder = reg.models[reg.default_model]
    print(f"[niah] embedder={reg.default_model}", file=sys.stderr)

    per_N: List[Dict[str, Any]] = []
    for N in Ns:
        print(f"[niah] N={N} mode={args.needle_mode} ... encoding+search", file=sys.stderr)
        per_N.append(_eval_at_N(N, args.needles, embedder, seed=args.seed,
                                needle_mode=args.needle_mode))
        r = per_N[-1]
        print(
            f"[niah] N={N:>6}  vanilla R@1={r['vanilla_vector']['recall@1']:.3f} "
            f"R@10={r['vanilla_vector']['recall@10']:.3f}    "
            f"hybrid R@1={r['greeum_hybrid']['recall@1']:.3f} "
            f"R@10={r['greeum_hybrid']['recall@10']:.3f}",
            file=sys.stderr,
        )

    # Slopes on recall@k vs log10(N): a flatter line = the USP claim is met.
    summary = {
        "schema_version": 1,
        "produced_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "config": {
            "Ns": Ns,
            "needles_per_N": args.needles,
            "seed": args.seed,
            "embedder": reg.default_model,
            "needle_mode": args.needle_mode,
            "scoring_mode": "brute_force (every query vs every doc)",
            "limitations": [
                "Brute-force scoring scales linearly with N for BM25; production "
                "Greeum uses HybridGraphSearch anchor-DFS which bounds candidates "
                "to a local neighborhood and is the real subject of the log-shaped "
                "USP claim. This script does not exercise the anchor path.",
                "trivial needle_mode shares the unique id between needle and query, "
                "so recall stays at 1.0 by token overlap up to large N. Use "
                "--needle-mode semantic to probe actual semantic retrieval.",
            ],
        },
        "per_N": per_N,
    }
    for metric in ("recall@1", "recall@5", "recall@10"):
        v_points = [(r["N"], r["vanilla_vector"][metric]) for r in per_N]
        h_points = [(r["N"], r["greeum_hybrid"][metric]) for r in per_N]
        v_slope = _slope_per_decade(v_points)
        h_slope = _slope_per_decade(h_points)
        summary[f"slope.{metric}.vanilla_vector"] = v_slope
        summary[f"slope.{metric}.greeum_hybrid"] = h_slope
        # USP ratio: smaller |hybrid slope| / |vanilla slope| = better.
        # If both are ~0 the ratio is undefined → record None.
        if abs(v_slope) > 1e-4:
            summary[f"slope_ratio.{metric}"] = round(abs(h_slope) / abs(v_slope), 3)
        else:
            summary[f"slope_ratio.{metric}"] = None

    Path(args.out).write_text(json.dumps(summary, ensure_ascii=False, indent=2),
                              encoding="utf-8")
    print(f"[niah] wrote {args.out}", file=sys.stderr)

    # Pretty-print the USP verdict.
    print("\n=== Log-scale USP — slopes (per decade of N) ===", file=sys.stderr)
    for metric in ("recall@1", "recall@5", "recall@10"):
        v = summary[f"slope.{metric}.vanilla_vector"]
        h = summary[f"slope.{metric}.greeum_hybrid"]
        r = summary[f"slope_ratio.{metric}"]
        print(f"  {metric}: vanilla {v:+.4f}/decade   hybrid {h:+.4f}/decade   "
              f"ratio |hyb|/|van|={r}", file=sys.stderr)

    return 0


if __name__ == "__main__":
    sys.exit(main())
