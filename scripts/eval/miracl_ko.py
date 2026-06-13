#!/usr/bin/env python3
"""MIRACL-Korean retrieval evaluation.

Pulls the Korean dev split of MIRACL (queries + qrels + corpus), wraps Greeum's
hybrid scorer as a retriever, computes nDCG@10 / Recall@10 / MRR. Vanilla
vector-only baseline runs in parallel for comparison.

MIRACL data files come from HuggingFace ``miracl/miracl`` (queries + qrels in
TSV) and ``miracl/miracl-corpus`` (corpus in jsonl.gz). Files are cached locally
under ``~/.greeum_eval_cache/miracl_ko``.

For the first measurement we run on a **subsampled corpus** — all "gold"
passages referenced by the chosen queries plus a random pool of distractors —
sized to keep total encode time under ~10 minutes on CPU. The full corpus
(~1.4M passages) is doable as a release-tier measurement but takes hours.
"""
from __future__ import annotations

import argparse
import gzip
import json
import math
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
CACHE = Path.home() / ".greeum_eval_cache" / "miracl_ko"


# ---------------------------------------------------------------------------
# Data download

def _ensure_files() -> Dict[str, Path]:
    CACHE.mkdir(parents=True, exist_ok=True)
    from huggingface_hub import hf_hub_download

    paths: Dict[str, Path] = {}
    print("[miracl] downloading queries (Korean dev) ...", file=sys.stderr)
    topics_local = hf_hub_download(
        repo_id="miracl/miracl",
        filename="miracl-v1.0-ko/topics/topics.miracl-v1.0-ko-dev.tsv",
        repo_type="dataset",
        cache_dir=str(CACHE),
    )
    paths["topics"] = Path(topics_local)

    print("[miracl] downloading qrels (Korean dev) ...", file=sys.stderr)
    qrels_local = hf_hub_download(
        repo_id="miracl/miracl",
        filename="miracl-v1.0-ko/qrels/qrels.miracl-v1.0-ko-dev.tsv",
        repo_type="dataset",
        cache_dir=str(CACHE),
    )
    paths["qrels"] = Path(qrels_local)

    print("[miracl] downloading corpus docs-0.jsonl.gz ...", file=sys.stderr)
    corpus_local = hf_hub_download(
        repo_id="miracl/miracl-corpus",
        filename="miracl-corpus-v1.0-ko/docs-0.jsonl.gz",
        repo_type="dataset",
        cache_dir=str(CACHE),
    )
    paths["corpus_0"] = Path(corpus_local)
    return paths


def _load_topics(p: Path) -> Dict[str, str]:
    """qid → query text"""
    out: Dict[str, str] = {}
    for ln in p.read_text(encoding="utf-8").splitlines():
        if not ln.strip(): continue
        cols = ln.split("\t")
        if len(cols) >= 2:
            out[cols[0]] = cols[1]
    return out


def _load_qrels(p: Path) -> Dict[str, Dict[str, int]]:
    """qid → {doc_id: relevance}"""
    out: Dict[str, Dict[str, int]] = {}
    for ln in p.read_text(encoding="utf-8").splitlines():
        if not ln.strip(): continue
        cols = ln.split("\t")
        if len(cols) >= 4:
            qid, _, docid, rel = cols[0], cols[1], cols[2], int(cols[3])
            out.setdefault(qid, {})[docid] = rel
    return out


def _load_corpus(p: Path) -> Dict[str, str]:
    """docid → text. Decompresses on the fly."""
    out: Dict[str, str] = {}
    with gzip.open(p, "rt", encoding="utf-8") as f:
        for ln in f:
            if not ln.strip(): continue
            obj = json.loads(ln)
            # MIRACL corpus jsonl shape: {"docid": ..., "title": ..., "text": ...}
            docid = obj.get("docid")
            text = obj.get("text", "")
            title = obj.get("title", "")
            if docid:
                # Convention: title + " " + text
                out[docid] = (title + " " + text).strip() if title else text
    return out


# ---------------------------------------------------------------------------
# Metrics

def _ndcg_at_k(retrieved: List[str], rel_map: Dict[str, int], k: int) -> float:
    """Standard nDCG@k with binary or graded relevance."""
    dcg = 0.0
    for i, docid in enumerate(retrieved[:k]):
        r = rel_map.get(docid, 0)
        if r > 0:
            dcg += (2 ** r - 1) / math.log2(i + 2)
    # Ideal DCG
    ideal = sorted(rel_map.values(), reverse=True)[:k]
    idcg = sum((2 ** r - 1) / math.log2(i + 2) for i, r in enumerate(ideal) if r > 0)
    return (dcg / idcg) if idcg > 0 else 0.0


def _recall_at_k(retrieved: List[str], rel_map: Dict[str, int], k: int) -> float:
    relevant = {d for d, r in rel_map.items() if r > 0}
    if not relevant: return 0.0
    found = sum(1 for d in retrieved[:k] if d in relevant)
    return found / len(relevant)


def _reciprocal_rank(retrieved: List[str], rel_map: Dict[str, int]) -> float:
    relevant = {d for d, r in rel_map.items() if r > 0}
    for i, docid in enumerate(retrieved):
        if docid in relevant:
            return 1.0 / (i + 1)
    return 0.0


# ---------------------------------------------------------------------------
# Driver

def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--n-queries", type=int, default=100,
                   help="Number of dev queries to evaluate (random subsample, seed fixed).")
    p.add_argument("--n-distractors", type=int, default=2000,
                   help="Random corpus passages to include alongside gold-set.")
    p.add_argument("--top-k", type=int, default=10)
    p.add_argument("--out", required=True)
    p.add_argument("--seed", type=int, default=SEED)
    p.add_argument("--tier", choices=["smoke", "standard", "release"], default="standard")
    args = p.parse_args()

    if args.tier == "smoke":
        args.n_queries = min(args.n_queries, 30)
        args.n_distractors = min(args.n_distractors, 500)
    elif args.tier == "release":
        args.n_queries = max(args.n_queries, 500)
        args.n_distractors = max(args.n_distractors, 50_000)

    random.seed(args.seed); np.random.seed(args.seed)

    paths = _ensure_files()
    topics = _load_topics(paths["topics"])
    qrels = _load_qrels(paths["qrels"])
    print(f"[miracl] loaded queries={len(topics)} qrels_groups={len(qrels)}", file=sys.stderr)

    # Subset queries (must have at least one gold judgment, and the gold docs
    # must be discoverable in our chosen corpus shard).
    print(f"[miracl] loading corpus shard 0 ...", file=sys.stderr)
    corpus = _load_corpus(paths["corpus_0"])
    print(f"[miracl] corpus shard 0 docs={len(corpus)}", file=sys.stderr)

    # Filter to queries whose qrels have at least 1 positive judgment AND
    # at least one of those positives lives in our shard.
    eligible = []
    for qid, qtext in topics.items():
        rel_map = qrels.get(qid, {})
        positives = [d for d, r in rel_map.items() if r > 0]
        if not positives:
            continue
        in_shard = [d for d in positives if d in corpus]
        if not in_shard:
            continue
        eligible.append(qid)
    print(f"[miracl] eligible queries (positive in shard 0): {len(eligible)}", file=sys.stderr)
    if not eligible:
        print("ERROR: no eligible queries; widen corpus shards", file=sys.stderr)
        return 1

    qids = sorted(random.sample(eligible, min(args.n_queries, len(eligible))))
    print(f"[miracl] sampled {len(qids)} queries for evaluation", file=sys.stderr)

    # Build evaluation corpus: gold docs + random distractors.
    gold_doc_ids = set()
    for qid in qids:
        for d, r in qrels[qid].items():
            if r > 0 and d in corpus:
                gold_doc_ids.add(d)
    all_doc_ids = list(corpus.keys())
    non_gold_pool = [d for d in all_doc_ids if d not in gold_doc_ids]
    random.shuffle(non_gold_pool)
    distractors = non_gold_pool[: args.n_distractors]
    eval_doc_ids = sorted(gold_doc_ids) + distractors
    eval_texts = [corpus[d] for d in eval_doc_ids]
    print(f"[miracl] eval corpus: {len(gold_doc_ids)} gold + {len(distractors)} distractors "
          f"= {len(eval_doc_ids)} passages", file=sys.stderr)

    # Embed corpus
    from greeum.embedding_models import EmbeddingRegistry
    reg = EmbeddingRegistry()
    embedder = reg.models[reg.default_model]
    print(f"[miracl] embedder={reg.default_model}", file=sys.stderr)

    t0 = time.time()
    corpus_emb = np.asarray(embedder.batch_encode(eval_texts), dtype=np.float32)
    embed_s = time.time() - t0
    print(f"[miracl] corpus embed: {embed_s:.1f}s ({embed_s / len(eval_texts) * 1000:.1f} ms/doc)",
          file=sys.stderr)

    # Build BM25 over the same corpus.
    bm25 = BM25Index()
    kws: Dict[str, List[str]] = {}
    for d, text in zip(eval_doc_ids, eval_texts):
        kws[d] = extract_keywords_from_text(text)
        bm25.add_document(d, kws[d])

    vec_w, bm25_w = _default_hybrid_weights()
    print(f"[miracl] hybrid weights vec={vec_w} bm25={bm25_w}", file=sys.stderr)

    # Per-query evaluation
    metrics = {
        "vanilla_vector": {"ndcg@10": [], "recall@10": [], "rr": []},
        "greeum_hybrid":  {"ndcg@10": [], "recall@10": [], "rr": []},
    }

    search_lats_v: List[float] = []
    search_lats_h: List[float] = []

    for qid in qids:
        query = topics[qid]
        rel_map = qrels[qid]

        ts = time.time()
        q_emb = np.asarray(embedder.encode(query), dtype=np.float32)
        sims = corpus_emb @ q_emb
        ranked_idx_v = np.argsort(-sims)
        ranked_v = [eval_doc_ids[i] for i in ranked_idx_v[: max(50, args.top_k)]]
        search_lats_v.append((time.time() - ts) * 1000.0)

        # Hybrid
        ts = time.time()
        q_kws = extract_keywords_from_text(query)
        bm25_scores = np.zeros(len(eval_doc_ids), dtype=np.float32)
        for i, d in enumerate(eval_doc_ids):
            bm25_scores[i] = bm25.normalize_score(bm25.score_with_keywords(q_kws, kws[d]))
        clipped = np.clip(sims, 0.0, 1.0)
        combined = vec_w * clipped + bm25_w * bm25_scores
        ranked_idx_h = np.argsort(-combined)
        ranked_h = [eval_doc_ids[i] for i in ranked_idx_h[: max(50, args.top_k)]]
        search_lats_h.append((time.time() - ts) * 1000.0)

        metrics["vanilla_vector"]["ndcg@10"].append(_ndcg_at_k(ranked_v, rel_map, args.top_k))
        metrics["vanilla_vector"]["recall@10"].append(_recall_at_k(ranked_v, rel_map, args.top_k))
        metrics["vanilla_vector"]["rr"].append(_reciprocal_rank(ranked_v, rel_map))

        metrics["greeum_hybrid"]["ndcg@10"].append(_ndcg_at_k(ranked_h, rel_map, args.top_k))
        metrics["greeum_hybrid"]["recall@10"].append(_recall_at_k(ranked_h, rel_map, args.top_k))
        metrics["greeum_hybrid"]["rr"].append(_reciprocal_rank(ranked_h, rel_map))

    def _avg(name, side):
        return round(statistics.fmean(metrics[side][name]), 4) if metrics[side][name] else None

    summary = {
        "schema_version": 1,
        "produced_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "tier": args.tier,
        "config": {
            "lang": "ko",
            "split": "dev",
            "n_queries": len(qids),
            "n_distractors": len(distractors),
            "n_gold_total": len(gold_doc_ids),
            "n_eval_corpus": len(eval_doc_ids),
            "top_k": args.top_k,
            "embedder": reg.default_model,
            "hybrid_weights": [vec_w, bm25_w],
            "seed": args.seed,
        },
        "vanilla_vector": {
            "nDCG@10":   _avg("ndcg@10",   "vanilla_vector"),
            "Recall@10": _avg("recall@10", "vanilla_vector"),
            "MRR":       _avg("rr",        "vanilla_vector"),
            "search_p50_ms": round(statistics.median(search_lats_v), 2),
            "search_p95_ms": round(sorted(search_lats_v)[int(len(search_lats_v) * 0.95) - 1] if search_lats_v else 0, 2),
        },
        "greeum_hybrid": {
            "nDCG@10":   _avg("ndcg@10",   "greeum_hybrid"),
            "Recall@10": _avg("recall@10", "greeum_hybrid"),
            "MRR":       _avg("rr",        "greeum_hybrid"),
            "search_p50_ms": round(statistics.median(search_lats_h), 2),
            "search_p95_ms": round(sorted(search_lats_h)[int(len(search_lats_h) * 0.95) - 1] if search_lats_h else 0, 2),
        },
    }

    Path(args.out).write_text(json.dumps(summary, ensure_ascii=False, indent=2),
                              encoding="utf-8")
    print(f"\n=== MIRACL-Korean dev — {len(qids)} queries × {len(eval_doc_ids)} passages ===",
          file=sys.stderr)
    for side in ("vanilla_vector", "greeum_hybrid"):
        s = summary[side]
        print(
            f"  {side:18}  nDCG@10={s['nDCG@10']}  Recall@10={s['Recall@10']}  "
            f"MRR={s['MRR']}   search p50/p95={s['search_p50_ms']}/{s['search_p95_ms']} ms",
            file=sys.stderr,
        )
    print(f"\n[miracl] wrote {args.out}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
