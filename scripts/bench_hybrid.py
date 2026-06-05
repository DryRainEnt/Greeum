#!/usr/bin/env python3
"""Hybrid (BM25 + Vector) retrieval benchmark on Greeum's real pipeline.

Uses Greeum's actual BM25Index + HybridScorer modules so the comparison reflects
production fusion. For each candidate embedding model, evaluates four modes:
    1. bm25_only       — BM25 score ranking (no embedding)
    2. vector_only     — cosine sim ranking (no BM25)
    3. hybrid_wavg     — 0.5*vector + 0.5*bm25_norm (production default)
    4. hybrid_rrf      — Reciprocal Rank Fusion (k=60)

Ground truth: same as scripts/bench_embeddings.py (semantic+causal pairs).
"""
from __future__ import annotations

import os, sys, time, json, sqlite3, random
from pathlib import Path
import numpy as np

sys.path.insert(0, "/home/dryrain/Greeum")
from greeum.text_utils import extract_keywords_from_text
from greeum.core.bm25_index import BM25Index, HybridScorer

DB = os.environ.get("BENCH_DB", "/home/dryrain/.greeum/memory.db")
OUT = Path(os.environ.get("BENCH_OUT", "/home/dryrain/Greeum/docs/issues/bench_hybrid_results.json"))
SEED = 42
random.seed(SEED); np.random.seed(SEED)


def load_data():
    con = sqlite3.connect(f"file:{DB}?mode=ro", uri=True, timeout=10); cur = con.cursor()
    texts = {bi: ctx for bi, ctx in cur.execute(
        "SELECT block_index, context FROM blocks WHERE context IS NOT NULL AND context != ''")}
    node2blk = {nid: mid for nid, mid in cur.execute("SELECT node_id, memory_id FROM memory_nodes")}
    pos = set()
    for s, t, atype in cur.execute(
            "SELECT source_node_id, target_node_id, association_type FROM associations "
            "WHERE association_type IN ('semantic','causal')"):
        a, b = node2blk.get(s), node2blk.get(t)
        if a is None or b is None or a == b: continue
        if a in texts and b in texts: pos.add((a, b))
    con.close()
    return texts, sorted(pos)


def evaluate_ranking(rank_of: dict, by_src: dict, idx_of: dict):
    """rank_of: {src_block -> {tgt_block -> rank_int}}. Returns recall/mrr."""
    rec1 = rec5 = rec10 = mrr = 0.0; n = 0
    for a, targets in by_src.items():
        if a not in rank_of: continue
        ranks = [rank_of[a].get(b, 10**9) for b in targets]
        ranks.sort()
        denom = len(targets)
        rec1 += sum(1 for r in ranks if r < 1) / min(1, denom)
        rec5 += sum(1 for r in ranks if r < 5) / min(5, denom)
        rec10 += sum(1 for r in ranks if r < 10) / min(10, denom)
        mrr += 1.0 / (ranks[0] + 1) if ranks[0] < 10**9 else 0.0
        n += 1
    return {"recall@1": round(rec1/n,4), "recall@5": round(rec5/n,4),
            "recall@10": round(rec10/n,4), "mrr": round(mrr/n,4), "n_query": n}


# ----------------- embedders (reuse logic from bench_embeddings) -----------------
def emb_st(model_id, prefix=""):
    from sentence_transformers import SentenceTransformer
    m = SentenceTransformer(model_id)
    def fn(texts):
        return m.encode([prefix+t for t in texts], normalize_embeddings=True,
                        show_progress_bar=False, batch_size=64)
    return fn, True

def emb_m2v(model_id):
    from model2vec import StaticModel
    m = StaticModel.from_pretrained(model_id)
    def fn(texts):
        v = np.asarray(m.encode(texts))
        v = v / (np.linalg.norm(v, axis=1, keepdims=True) + 1e-9)
        return v
    return fn, False


CANDIDATES = {
    "baseline_minilm": lambda: emb_st("sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"),
    "e5_small":        lambda: emb_st("intfloat/multilingual-e5-small", "query: "),
    "e5_base":         lambda: emb_st("intfloat/multilingual-e5-base", "query: "),
    "potion_ml":       lambda: emb_m2v("minishlab/potion-multilingual-128M"),
}


def main():
    only = set(sys.argv[1:])
    texts, pos_pairs = load_data()
    blocks = sorted(texts.keys())
    idx_of = {b: i for i, b in enumerate(blocks)}
    corpus = [texts[b] for b in blocks]

    # Extract keywords (production-equivalent via Greeum's text_utils, cap=10)
    block_kw = {b: extract_keywords_from_text(texts[b]) for b in blocks}

    # Build BM25 (matches production: per-block keyword set, cap 10)
    bm25 = BM25Index()
    for b in blocks:
        bm25.add_document(str(b), block_kw[b])
    print(f"[data] blocks={len(blocks)} positive_pairs={len(pos_pairs)} "
          f"bm25_vocab={len(bm25.idf)} avg_doc_len={bm25.avg_doc_len:.1f}")

    by_src = {}
    for a, b in pos_pairs:
        by_src.setdefault(a, set()).add(b)

    # Pre-compute BM25 score matrix once: sims_bm25[src, dst] = normalize_score(score(q_kw, doc))
    N = len(blocks)
    bm25_score = np.zeros((N, N), dtype=np.float32)
    for i, a in enumerate(blocks):
        qkw = block_kw[a]
        for j, c in enumerate(blocks):
            if i == j: continue
            s = bm25.score_with_keywords(qkw, block_kw[c])
            bm25_score[i, j] = bm25.normalize_score(s)
    # BM25-only ranking → rank_of dicts
    rank_bm25 = {}
    for i, a in enumerate(blocks):
        order = np.argsort(-bm25_score[i])
        rank_bm25[a] = {blocks[order[r]]: r for r in range(N) if order[r] != i}
        # adjust ranks to exclude self
        # build rank dict over non-self positions; the dict above already excludes self implicitly via "if !=i"
        # but enumeration positions need to be re-computed:
    # Properly compute rank_bm25 excluding self
    rank_bm25 = {}
    for i, a in enumerate(blocks):
        order = [j for j in np.argsort(-bm25_score[i]) if j != i]
        rank_bm25[a] = {blocks[order[r]]: r for r in range(len(order))}

    results = {"bm25_only": evaluate_ranking(rank_bm25, by_src, idx_of)}
    print(f"[bm25_only] {results['bm25_only']}")

    # Per candidate: compute vector sims + hybrid modes
    cand_results = {}
    for name, build in CANDIDATES.items():
        if only and not any(o in name for o in only):
            continue
        print(f"\n[run] {name} ...")
        t0 = time.time()
        embed_fn, needs_torch = build()
        emb = np.asarray(embed_fn(corpus), dtype=np.float32)
        emb = emb / (np.linalg.norm(emb, axis=1, keepdims=True) + 1e-9)
        load_embed_s = time.time() - t0

        # Vector sim matrix (N,N), self -inf
        vec_sim = emb @ emb.T
        np.fill_diagonal(vec_sim, -np.inf)

        # vector_only ranks
        rank_vec = {}
        for i, a in enumerate(blocks):
            order = [j for j in np.argsort(-vec_sim[i]) if j != i]
            rank_vec[a] = {blocks[order[r]]: r for r in range(len(order))}

        # hybrid weighted_avg: 0.5*vec + 0.5*bm25_norm (vec is in [-inf, 1]; clip to [0,1])
        vec_clip = np.clip(vec_sim, 0.0, 1.0)
        hyb_wavg = 0.5 * vec_clip + 0.5 * bm25_score
        # set self to -inf
        np.fill_diagonal(hyb_wavg, -np.inf)
        rank_wavg = {}
        for i, a in enumerate(blocks):
            order = [j for j in np.argsort(-hyb_wavg[i]) if j != i]
            rank_wavg[a] = {blocks[order[r]]: r for r in range(len(order))}

        # hybrid RRF: per source, RRF over (vector ranking, bm25 ranking)
        rank_rrf = {}
        K = 60
        for i, a in enumerate(blocks):
            vec_order = [j for j in np.argsort(-vec_sim[i]) if j != i]
            bm_order  = [j for j in np.argsort(-bm25_score[i]) if j != i]
            vec_rank = {j: r+1 for r, j in enumerate(vec_order)}
            bm_rank  = {j: r+1 for r, j in enumerate(bm_order)}
            rrf = []
            for j in range(N):
                if j == i: continue
                vr = vec_rank.get(j, N+K+1); br = bm_rank.get(j, N+K+1)
                rrf.append((j, 0.5/(K+vr) + 0.5/(K+br)))
            rrf.sort(key=lambda x: -x[1])
            rank_rrf[a] = {blocks[j]: r for r, (j, _) in enumerate(rrf)}

        cand_results[name] = {
            "vector_only": evaluate_ranking(rank_vec,  by_src, idx_of),
            "hybrid_wavg": evaluate_ranking(rank_wavg, by_src, idx_of),
            "hybrid_rrf":  evaluate_ranking(rank_rrf,  by_src, idx_of),
            "needs_torch_at_inference": needs_torch,
            "embed_total_s": round(load_embed_s, 2),
        }
        for mode in ["vector_only","hybrid_wavg","hybrid_rrf"]:
            print(f"  {mode:14}: {cand_results[name][mode]}")

    results["candidates"] = cand_results
    results["meta"] = {"db": DB, "n_blocks": N, "n_pos_pairs": len(pos_pairs),
                       "bm25_vocab": len(bm25.idf), "avg_doc_len": round(bm25.avg_doc_len, 2),
                       "fusion_weights": [0.5, 0.5], "rrf_k": K}
    OUT.write_text(json.dumps(results, ensure_ascii=False, indent=2))

    # Compact summary table
    print("\n=== SUMMARY (recall@5 / recall@10 / mrr) ===")
    print(f"{'mode':40} {'R@1':>6} {'R@5':>6} {'R@10':>6} {'MRR':>6}")
    m = results["bm25_only"]
    print(f"{'bm25_only':40} {m['recall@1']:>6} {m['recall@5']:>6} {m['recall@10']:>6} {m['mrr']:>6}")
    for name, c in cand_results.items():
        for mode in ["vector_only","hybrid_wavg","hybrid_rrf"]:
            m = c[mode]
            torch_tag = "(torch)" if c["needs_torch_at_inference"] else "(no-torch)"
            print(f"{name+'/'+mode+' '+torch_tag:40} {m['recall@1']:>6} {m['recall@5']:>6} {m['recall@10']:>6} {m['mrr']:>6}")
    print(f"\n[out] {OUT}")


if __name__ == "__main__":
    main()
