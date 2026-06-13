#!/usr/bin/env python3
"""Internal benchmark — canonical Greeum retrieval quality + latency snapshot.

Drives the existing bench_embeddings/bench_hybrid harnesses on the live DB
(read-only) using the current ``main`` defaults, plus a latency micro-bench
(search round-trip p50/p95, ingest p95). Emits a single consolidated JSON
suitable for baseline freeze + regression checking.

Used by:
- ``scripts/eval/freeze_baseline.py`` (one-shot at policy adoption)
- ``scripts/eval/check_regression.py`` (every PR / CI run)

Defaults are intentionally conservative — the script must finish in ≤ 5
minutes on a CPU machine so it's runnable in CI smoke tier.
"""
from __future__ import annotations

import argparse
import json
import os
import sqlite3
import statistics
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

import numpy as np

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if (_REPO_ROOT / "greeum" / "__init__.py").exists():
    sys.path.insert(0, str(_REPO_ROOT))

from greeum.text_utils import extract_keywords_from_text  # noqa: E402
from greeum.core.bm25_index import BM25Index, HybridScorer, _default_hybrid_weights  # noqa: E402

SEED = 42


# ---------------------------------------------------------------------------
# Live DB read

def _read_live_db(db_path: str, limit: int | None = None) -> Dict[str, Any]:
    """Read blocks + semantic+causal GT pairs from the live DB (read-only)."""
    con = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True, timeout=10)
    cur = con.cursor()
    sql = "SELECT block_index, context FROM blocks WHERE context IS NOT NULL AND context != '' ORDER BY block_index"
    if limit:
        sql += f" LIMIT {int(limit)}"
    blocks = [(int(r[0]), str(r[1])) for r in cur.execute(sql)]
    node2blk = {nid: int(mid) for nid, mid in cur.execute("SELECT node_id, memory_id FROM memory_nodes")}
    pos = set()
    for s, t, atype in cur.execute(
            "SELECT source_node_id, target_node_id, association_type FROM associations "
            "WHERE association_type IN ('semantic','causal')"):
        a, b = node2blk.get(s), node2blk.get(t)
        if a is None or b is None or a == b:
            continue
        a, b = int(a), int(b)
        if any(x[0] == a for x in blocks) and any(x[0] == b for x in blocks):
            pos.add((a, b))
    con.close()
    return {"blocks": blocks, "pos_pairs": sorted(pos)}


# ---------------------------------------------------------------------------
# Embedding model factory

def _get_default_embedder():
    """Use the embedding model the application would auto-select."""
    from greeum.embedding_models import EmbeddingRegistry
    reg = EmbeddingRegistry()
    name = reg.default_model
    model = reg.models[name]
    return model, name


# ---------------------------------------------------------------------------
# Metric computation

def _evaluate_ranking(rank_of: Dict[int, Dict[int, int]],
                      by_src: Dict[int, set]) -> Dict[str, Any]:
    rec1 = rec5 = rec10 = mrr = 0.0
    n = 0
    for a, targets in by_src.items():
        if a not in rank_of:
            continue
        ranks = sorted(rank_of[a].get(b, 10**9) for b in targets)
        denom = len(targets)
        rec1 += sum(1 for r in ranks if r < 1) / min(1, denom)
        rec5 += sum(1 for r in ranks if r < 5) / min(5, denom)
        rec10 += sum(1 for r in ranks if r < 10) / min(10, denom)
        mrr += (1.0 / (ranks[0] + 1)) if ranks[0] < 10**9 else 0.0
        n += 1
    if n == 0:
        return {"recall@1": None, "recall@5": None, "recall@10": None, "mrr": None, "n": 0}
    return {
        "recall@1": round(rec1 / n, 4),
        "recall@5": round(rec5 / n, 4),
        "recall@10": round(rec10 / n, 4),
        "mrr": round(mrr / n, 4),
        "n_query": n,
    }


def _pair_auc(pos: np.ndarray, neg: np.ndarray) -> float:
    if len(pos) == 0 or len(neg) == 0:
        return float("nan")
    alls = np.concatenate([pos, neg])
    ranks = alls.argsort().argsort().astype(float) + 1
    rpos = ranks[: len(pos)].sum()
    return float((rpos - len(pos) * (len(pos) + 1) / 2) / (len(pos) * len(neg)))


def _quality_metrics(blocks, pos_pairs, embedder) -> Dict[str, Any]:
    """recall@k / MRR / pair-AUC for embedding-only and hybrid (production weights)."""
    import random
    random.seed(SEED); np.random.seed(SEED)

    block_ids = [b for b, _ in blocks]
    texts = [t for _, t in blocks]
    idx_of = {b: i for i, b in enumerate(block_ids)}
    N = len(blocks)

    by_src: Dict[int, set] = {}
    for a, b in pos_pairs:
        by_src.setdefault(a, set()).add(b)

    # --- Embedding-only ranking ---
    t0 = time.time()
    embeddings = np.asarray(embedder.batch_encode(texts), dtype=np.float32)
    embed_time = time.time() - t0
    sims = embeddings @ embeddings.T
    np.fill_diagonal(sims, -np.inf)
    rank_vec = {}
    for i, a in enumerate(block_ids):
        order = [j for j in np.argsort(-sims[i]) if j != i]
        rank_vec[a] = {block_ids[order[r]]: r for r in range(len(order))}
    vec_metrics = _evaluate_ranking(rank_vec, by_src)

    # pair-AUC
    pos_scores = [sims[idx_of[a], idx_of[b]] for a, b in pos_pairs]
    pos_set = set(pos_pairs)
    neg_scores = []
    tries = 0
    target_neg = len(pos_pairs)
    while len(neg_scores) < target_neg and tries < target_neg * 20:
        a, b = random.choice(block_ids), random.choice(block_ids)
        tries += 1
        if a == b or (a, b) in pos_set or (b, a) in pos_set:
            continue
        neg_scores.append(sims[idx_of[a], idx_of[b]])
    vec_metrics["pair_auc"] = round(_pair_auc(np.array(pos_scores), np.array(neg_scores)), 4)

    # --- BM25 + hybrid ranking ---
    block_kw = {b: extract_keywords_from_text(t) for b, t in blocks}
    bm25 = BM25Index()
    for b, _ in blocks:
        bm25.add_document(str(b), block_kw[b])

    bm25_score = np.zeros((N, N), dtype=np.float32)
    for i, a in enumerate(block_ids):
        for j, c in enumerate(block_ids):
            if i == j:
                continue
            bm25_score[i, j] = bm25.normalize_score(
                bm25.score_with_keywords(block_kw[a], block_kw[c])
            )

    vec_clip = np.clip(sims, 0.0, 1.0)
    vec_w, bm25_w = _default_hybrid_weights()  # production weights
    hyb = vec_w * vec_clip + bm25_w * bm25_score
    np.fill_diagonal(hyb, -np.inf)
    rank_hyb = {}
    for i, a in enumerate(block_ids):
        order = [j for j in np.argsort(-hyb[i]) if j != i]
        rank_hyb[a] = {block_ids[order[r]]: r for r in range(len(order))}
    hyb_metrics = _evaluate_ranking(rank_hyb, by_src)

    return {
        "embedding_only": vec_metrics,
        "hybrid_production": {
            "weights": {"vec": vec_w, "bm25": bm25_w},
            **hyb_metrics,
        },
        "_aux": {
            "n_blocks": N,
            "n_pos_pairs": len(pos_pairs),
            "embed_total_s": round(embed_time, 2),
            "embed_per_doc_ms": round(embed_time / max(1, N) * 1000, 2),
        },
    }


def _latency_microbench(embedder, blocks, n_samples: int = 30) -> Dict[str, Any]:
    """Single-shot latency: encode 1 query → cosine vs corpus → top-10. Repeat."""
    import random
    random.seed(SEED)
    texts = [t for _, t in blocks]
    corpus_emb = np.asarray(embedder.batch_encode(texts), dtype=np.float32)

    queries = [random.choice(texts) for _ in range(n_samples)]
    search_lats: List[float] = []
    for q in queries:
        t0 = time.time()
        qv = np.asarray(embedder.encode(q), dtype=np.float32)
        _ = (corpus_emb @ qv)  # cosine since both L2-normed
        search_lats.append((time.time() - t0) * 1000.0)

    # Ingest latency = single encode (the encode is the bottleneck; DB write is fast).
    ingest_lats: List[float] = []
    for q in queries:
        t0 = time.time()
        _ = embedder.encode(q)
        ingest_lats.append((time.time() - t0) * 1000.0)

    return {
        "search_latency_ms": {
            "p50": round(statistics.median(search_lats), 2),
            "p95": round(_percentile(search_lats, 95), 2),
            "mean": round(statistics.fmean(search_lats), 2),
            "n_samples": n_samples,
        },
        "ingest_latency_ms": {
            "p50": round(statistics.median(ingest_lats), 2),
            "p95": round(_percentile(ingest_lats, 95), 2),
            "mean": round(statistics.fmean(ingest_lats), 2),
            "n_samples": n_samples,
        },
    }


def _percentile(values: List[float], p: float) -> float:
    if not values:
        return 0.0
    s = sorted(values)
    k = (len(s) - 1) * (p / 100.0)
    f = int(k); c = min(f + 1, len(s) - 1)
    if f == c:
        return s[f]
    return s[f] + (s[c] - s[f]) * (k - f)


# ---------------------------------------------------------------------------
# Driver

def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--db", default=os.environ.get("GREEUM_DATA_DIR_DB",
                                                  str(Path.home() / ".greeum" / "memory.db")))
    p.add_argument("--limit-blocks", type=int, default=None,
                   help="Cap number of blocks (CI smoke uses ≤ 100)")
    p.add_argument("--limit-pairs", type=int, default=None,
                   help="Cap number of GT pairs (CI smoke uses ≤ 200)")
    p.add_argument("--latency-samples", type=int, default=30)
    p.add_argument("--out", default=None, help="Output JSON path")
    p.add_argument("--tier", choices=["smoke", "standard", "release"], default="standard")
    args = p.parse_args()

    if not Path(args.db).exists():
        print(f"DB not found: {args.db}", file=sys.stderr)
        return 2

    # Smoke tier: trim aggressively.
    if args.tier == "smoke":
        args.limit_blocks = args.limit_blocks or 100
        args.limit_pairs = args.limit_pairs or 200
        args.latency_samples = min(args.latency_samples, 10)

    print(f"[eval] db={args.db} tier={args.tier} limit_blocks={args.limit_blocks}", file=sys.stderr)
    data = _read_live_db(args.db, limit=args.limit_blocks)
    pos_pairs = data["pos_pairs"]
    if args.limit_pairs:
        pos_pairs = pos_pairs[: args.limit_pairs]
    print(f"[eval] blocks={len(data['blocks'])} pos_pairs={len(pos_pairs)}", file=sys.stderr)

    embedder, model_name = _get_default_embedder()
    print(f"[eval] embedder={model_name}", file=sys.stderr)

    quality = _quality_metrics(data["blocks"], pos_pairs, embedder)
    latency = _latency_microbench(embedder, data["blocks"], n_samples=args.latency_samples)

    summary = {
        "schema_version": 1,
        "produced_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "tier": args.tier,
        "config": {
            "db": args.db,
            "n_blocks": len(data["blocks"]),
            "n_pos_pairs": len(pos_pairs),
            "limit_blocks": args.limit_blocks,
            "limit_pairs": args.limit_pairs,
            "latency_samples": args.latency_samples,
            "embedder": model_name,
            "hybrid_weights": list(_default_hybrid_weights()),
        },
        "quality": quality,
        "latency": latency,
    }

    # Surface key numbers to stderr for terminal feedback.
    eo = quality["embedding_only"]
    hp = quality["hybrid_production"]
    print(
        f"[eval] embedding_only  R@5={eo.get('recall@5')} R@10={eo.get('recall@10')} MRR={eo.get('mrr')}",
        file=sys.stderr,
    )
    print(
        f"[eval] hybrid_prod     R@5={hp.get('recall@5')} R@10={hp.get('recall@10')} MRR={hp.get('mrr')}  "
        f"(weights={hp['weights']})",
        file=sys.stderr,
    )
    print(
        f"[eval] search p50/p95 = {latency['search_latency_ms']['p50']}/{latency['search_latency_ms']['p95']} ms",
        file=sys.stderr,
    )

    out = json.dumps(summary, ensure_ascii=False, indent=2)
    if args.out:
        Path(args.out).write_text(out, encoding="utf-8")
        print(f"[eval] wrote {args.out}", file=sys.stderr)
    else:
        print(out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
