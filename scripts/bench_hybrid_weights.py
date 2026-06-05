#!/usr/bin/env python3
"""Weight sweep for hybrid (BM25 + Vector) fusion.

Does re-tuning the 50/50 default rescue e5_small under hybrid?
Tests vector_weight ∈ {0.0, 0.3, 0.5, 0.7, 0.8, 0.9, 1.0} for e5_small and potion_ml.
"""
from __future__ import annotations
import os, sys, json, sqlite3, random
import numpy as np

sys.path.insert(0, "/home/dryrain/Greeum")
from greeum.text_utils import extract_keywords_from_text
from greeum.core.bm25_index import BM25Index

DB = "/home/dryrain/.greeum/memory.db"
random.seed(42); np.random.seed(42)


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


def eval_ranks(rank_of, by_src):
    rec1 = rec5 = rec10 = mrr = 0.0; n = 0
    for a, targets in by_src.items():
        if a not in rank_of: continue
        ranks = sorted(rank_of[a].get(b, 10**9) for b in targets)
        denom = len(targets)
        rec1 += sum(1 for r in ranks if r < 1) / min(1, denom)
        rec5 += sum(1 for r in ranks if r < 5) / min(5, denom)
        rec10 += sum(1 for r in ranks if r < 10) / min(10, denom)
        mrr += 1.0 / (ranks[0] + 1) if ranks[0] < 10**9 else 0.0
        n += 1
    return {"r@1": round(rec1/n,3), "r@5": round(rec5/n,3),
            "r@10": round(rec10/n,3), "mrr": round(mrr/n,3)}


def main():
    texts, pos_pairs = load_data()
    blocks = sorted(texts.keys()); N = len(blocks)
    by_src = {}
    for a, b in pos_pairs:
        by_src.setdefault(a, set()).add(b)
    corpus = [texts[b] for b in blocks]
    block_kw = {b: extract_keywords_from_text(texts[b]) for b in blocks}

    bm25 = BM25Index()
    for b in blocks:
        bm25.add_document(str(b), block_kw[b])
    bm25_score = np.zeros((N, N), dtype=np.float32)
    for i, a in enumerate(blocks):
        for j, c in enumerate(blocks):
            if i == j: continue
            bm25_score[i, j] = bm25.normalize_score(bm25.score_with_keywords(block_kw[a], block_kw[c]))

    def get_emb(name):
        if name == "e5_small":
            from sentence_transformers import SentenceTransformer
            m = SentenceTransformer("intfloat/multilingual-e5-small")
            return np.asarray(m.encode(["query: "+t for t in corpus], normalize_embeddings=True,
                                       show_progress_bar=False), dtype=np.float32)
        if name == "potion_ml":
            from model2vec import StaticModel
            m = StaticModel.from_pretrained("minishlab/potion-multilingual-128M")
            v = np.asarray(m.encode(corpus), dtype=np.float32)
            return v / (np.linalg.norm(v, axis=1, keepdims=True) + 1e-9)

    print(f"# blocks={N} pos_pairs={len(pos_pairs)}\n")
    print(f"{'model':12} {'vec_w':>6} {'bm25_w':>6} {'r@1':>6} {'r@5':>6} {'r@10':>6} {'mrr':>6}")
    sweep = [0.0, 0.3, 0.5, 0.7, 0.8, 0.9, 1.0]
    for name in ["e5_small", "potion_ml"]:
        emb = get_emb(name)
        vec_sim = emb @ emb.T
        np.fill_diagonal(vec_sim, -np.inf)
        vec_clip = np.clip(vec_sim, 0.0, 1.0)
        for vw in sweep:
            bw = 1.0 - vw
            mix = vw * vec_clip + bw * bm25_score
            np.fill_diagonal(mix, -np.inf)
            ranks = {}
            for i, a in enumerate(blocks):
                order = [j for j in np.argsort(-mix[i]) if j != i]
                ranks[a] = {blocks[order[r]]: r for r in range(len(order))}
            m = eval_ranks(ranks, by_src)
            print(f"{name:12} {vw:>6.1f} {bw:>6.1f} {m['r@1']:>6} {m['r@5']:>6} {m['r@10']:>6} {m['mrr']:>6}")
        print()


if __name__ == "__main__":
    main()
