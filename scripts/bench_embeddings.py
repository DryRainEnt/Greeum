#!/usr/bin/env python3
"""Embedding candidate benchmark for Greeum's harness-integration decision.

Compares attachable embedding backends on Greeum's REAL data (live DB) across the
axes that drive user experience: retrieval QUALITY (recall@k, MRR, pair-AUC) and
DEPLOYMENT cost (model size, load time, query latency, torch dependency).

Ground truth: consolidator-produced `semantic` + `causal` associations are treated as
positive (related) block pairs. `temporal` associations are ignored (time-adjacency,
not relatedness). Negatives for AUC are randomly sampled non-positive pairs.

Read-only against the DB. Re-embeds block texts fresh per candidate, so whatever model
produced the stored vectors is irrelevant.
"""
from __future__ import annotations

import os, sys, time, json, sqlite3, random, glob
from pathlib import Path
from typing import Callable, Optional

import numpy as np

DB = os.environ.get("BENCH_DB", "/home/dryrain/.greeum/memory.db")
OUT = Path(os.environ.get("BENCH_OUT", "/home/dryrain/Greeum/docs/issues/bench_embeddings_results.json"))
SEED = 42
random.seed(SEED); np.random.seed(SEED)


# ----------------------------- data loading -----------------------------
def load_data():
    con = sqlite3.connect(f"file:{DB}?mode=ro", uri=True, timeout=10)
    cur = con.cursor()
    # block_index -> context text
    texts = {bi: ctx for bi, ctx in cur.execute(
        "SELECT block_index, context FROM blocks WHERE context IS NOT NULL AND context != ''")}
    # node_id -> block_index
    node2blk = {nid: mid for nid, mid in cur.execute(
        "SELECT node_id, memory_id FROM memory_nodes")}
    # positive pairs from semantic + causal associations
    pos = set()
    for s, t, atype in cur.execute(
            "SELECT source_node_id, target_node_id, association_type FROM associations "
            "WHERE association_type IN ('semantic','causal')"):
        a, b = node2blk.get(s), node2blk.get(t)
        if a is None or b is None or a == b:
            continue
        if a in texts and b in texts:
            pos.add((a, b))  # directed; we evaluate source->target retrieval
    con.close()
    return texts, sorted(pos)


# ----------------------------- metrics -----------------------------
def evaluate(emb: np.ndarray, idx_of: dict, pos_pairs):
    """emb: (N, d) L2-normalized. idx_of: block_index -> row. Returns metrics dict."""
    sims = emb @ emb.T               # (N,N) cosine
    np.fill_diagonal(sims, -np.inf)  # exclude self
    order = np.argsort(-sims, axis=1)  # ranked neighbor rows per row

    # group positives by source
    by_src: dict[int, set] = {}
    for a, b in pos_pairs:
        by_src.setdefault(a, set()).add(b)

    rec1 = rec5 = rec10 = mrr = 0.0
    n = 0
    for a, targets in by_src.items():
        ra = idx_of[a]
        tgt_rows = {idx_of[b] for b in targets}
        ranked = order[ra]
        # rank positions of each target
        first_rank = None
        hits1 = hits5 = hits10 = 0
        # build rank lookup once
        rank_of = {row: r for r, row in enumerate(ranked)}
        ranks = sorted(rank_of[tr] for tr in tgt_rows)
        first_rank = ranks[0]
        hits1 = sum(1 for r in ranks if r < 1)
        hits5 = sum(1 for r in ranks if r < 5)
        hits10 = sum(1 for r in ranks if r < 10)
        denom = len(tgt_rows)
        rec1 += hits1 / min(1, denom) if denom else 0
        rec5 += hits5 / min(5, denom) if denom else 0
        rec10 += hits10 / min(10, denom) if denom else 0
        mrr += 1.0 / (first_rank + 1)
        n += 1

    # pair-AUC: positives vs random negatives
    pos_scores = [sims[idx_of[a], idx_of[b]] for a, b in pos_pairs]
    all_blocks = list(idx_of.keys())
    pos_set = set(pos_pairs)
    neg_scores = []
    tries = 0
    target_neg = len(pos_pairs)
    while len(neg_scores) < target_neg and tries < target_neg * 20:
        a, b = random.choice(all_blocks), random.choice(all_blocks)
        tries += 1
        if a == b or (a, b) in pos_set or (b, a) in pos_set:
            continue
        neg_scores.append(sims[idx_of[a], idx_of[b]])
    auc = _auc(np.array(pos_scores), np.array(neg_scores))

    return {
        "recall@1": round(rec1 / n, 4),
        "recall@5": round(rec5 / n, 4),
        "recall@10": round(rec10 / n, 4),
        "mrr": round(mrr / n, 4),
        "pair_auc": round(auc, 4),
        "n_query_blocks": n,
        "n_pos_pairs": len(pos_pairs),
    }


def _auc(pos: np.ndarray, neg: np.ndarray) -> float:
    # probability a random positive scores higher than a random negative (Mann-Whitney)
    if len(pos) == 0 or len(neg) == 0:
        return float("nan")
    alls = np.concatenate([pos, neg])
    ranks = alls.argsort().argsort().astype(float) + 1
    rpos = ranks[: len(pos)].sum()
    return (rpos - len(pos) * (len(pos) + 1) / 2) / (len(pos) * len(neg))


# ----------------------------- candidates -----------------------------
def hf_size_mb(model_id: str) -> Optional[float]:
    cache = Path.home() / ".cache/huggingface/hub"
    safe = "models--" + model_id.replace("/", "--")
    d = cache / safe
    if not d.exists():
        return None
    total = sum(f.stat().st_size for f in d.rglob("*") if f.is_file() and ".no_exist" not in str(f))
    return round(total / 1e6, 1)


def cand_sentence_transformer(model_id, prefix=""):
    def build():
        from sentence_transformers import SentenceTransformer
        t0 = time.time()
        m = SentenceTransformer(model_id)
        load = time.time() - t0
        def embed(texts):
            return m.encode([prefix + t for t in texts], normalize_embeddings=True,
                            show_progress_bar=False, batch_size=64)
        return embed, load, m.get_sentence_embedding_dimension(), hf_size_mb(model_id), True
    return build


def cand_model2vec(model_id):
    def build():
        from model2vec import StaticModel
        t0 = time.time()
        m = StaticModel.from_pretrained(model_id)
        load = time.time() - t0
        def embed(texts):
            v = np.asarray(m.encode(texts))
            v = v / (np.linalg.norm(v, axis=1, keepdims=True) + 1e-9)
            return v
        dim = m.dim if hasattr(m, "dim") else m.encode(["x"]).shape[-1]
        return embed, load, dim, hf_size_mb(model_id), False
    return build


def cand_onnx_int8(model_id):
    def build():
        from optimum.onnxruntime import ORTModelForFeatureExtraction, ORTQuantizer
        from optimum.onnxruntime.configuration import AutoQuantizationConfig
        from transformers import AutoTokenizer
        import tempfile, torch as _t  # torch only used by exporter, not inference
        t0 = time.time()
        work = Path(tempfile.mkdtemp(prefix="onnx_e5_"))
        ort = ORTModelForFeatureExtraction.from_pretrained(model_id, export=True)
        ort.save_pretrained(work)
        q = ORTQuantizer.from_pretrained(work)
        qconfig = AutoQuantizationConfig.avx2(is_static=False, per_channel=False)
        q.quantize(save_dir=work, quantization_config=qconfig)
        tok = AutoTokenizer.from_pretrained(model_id)
        model = ORTModelForFeatureExtraction.from_pretrained(work, file_name="model_quantized.onnx")
        load = time.time() - t0

        def embed(texts):
            out = []
            for i in range(0, len(texts), 32):
                batch = ["query: " + t for t in texts[i:i+32]]
                enc = tok(batch, padding=True, truncation=True, max_length=256, return_tensors="np")
                res = model(**{k: v for k, v in enc.items()})
                last = res.last_hidden_state           # (b, seq, d)
                mask = enc["attention_mask"][:, :, None]
                pooled = (last * mask).sum(1) / np.clip(mask.sum(1), 1, None)  # mean pool
                out.append(pooled)
            v = np.concatenate(out, 0)
            v = v / (np.linalg.norm(v, axis=1, keepdims=True) + 1e-9)
            return v
        size = round(sum(f.stat().st_size for f in work.rglob("model_quantized.onnx")) / 1e6, 1)
        return embed, load, None, size, False
    return build


def cand_model2vec_distill(teacher):
    """Distill a sentence-transformer into a static (no-torch-at-inference) model.
    Distillation is a one-time offline step (uses torch); the artifact is numpy-only."""
    def build():
        from model2vec.distill import distill
        t0 = time.time()
        m = distill(model_name=teacher)
        load = time.time() - t0
        def embed(texts):
            v = np.asarray(m.encode(texts))
            v = v / (np.linalg.norm(v, axis=1, keepdims=True) + 1e-9)
            return v
        dim = m.encode(["x"]).shape[-1]
        return embed, load, dim, None, False
    return build


def cand_hash():
    def build():
        sys.path.insert(0, "/home/dryrain/Greeum")
        from greeum.embedding_models import SimpleEmbeddingModel
        t0 = time.time()
        m = SimpleEmbeddingModel(dimension=384)
        load = time.time() - t0
        def embed(texts):
            v = np.array([m.encode(t) for t in texts], dtype=float)
            v = v / (np.linalg.norm(v, axis=1, keepdims=True) + 1e-9)
            return v
        return embed, load, 384, 0.0, False
    return build


CANDIDATES = {
    "baseline_minilm (current)": cand_sentence_transformer("sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"),
    "e5_small": cand_sentence_transformer("intfloat/multilingual-e5-small", prefix="query: "),
    "e5_base": cand_sentence_transformer("intfloat/multilingual-e5-base", prefix="query: "),
    "model2vec_potion_ml": cand_model2vec("minishlab/potion-multilingual-128M"),
    "model2vec_distill_e5small": cand_model2vec_distill("intfloat/multilingual-e5-small"),
    "e5_small_onnx_int8": cand_onnx_int8("intfloat/multilingual-e5-small"),
    "hash_fallback (floor)": cand_hash(),
}


def main():
    only = set(sys.argv[1:])  # optionally run a subset by name substring
    texts, pos_pairs = load_data()
    blocks = sorted(texts.keys())
    idx_of = {b: i for i, b in enumerate(blocks)}
    corpus = [texts[b] for b in blocks]
    print(f"[data] blocks={len(blocks)} positive_pairs={len(pos_pairs)}")

    results = {}
    for name, build in CANDIDATES.items():
        if only and not any(o in name for o in only):
            continue
        print(f"\n[run] {name} ...")
        try:
            embed, load_s, dim, size_mb, needs_torch = build()
            t0 = time.time()
            emb = np.asarray(embed(corpus), dtype=np.float32)
            embed_s = time.time() - t0
            if dim is None:
                dim = emb.shape[1]
            m = evaluate(emb, idx_of, pos_pairs)
            m.update({
                "dim": int(dim),
                "model_size_mb": size_mb,
                "load_s": round(load_s, 2),
                "embed_total_s": round(embed_s, 2),
                "per_doc_ms": round(embed_s / len(corpus) * 1000, 2),
                "needs_torch_at_inference": needs_torch,
            })
            results[name] = m
            print(f"  {json.dumps(m, ensure_ascii=False)}")
        except Exception as e:
            import traceback; traceback.print_exc()
            results[name] = {"error": f"{type(e).__name__}: {e}"}

    OUT.write_text(json.dumps({"db": DB, "n_blocks": len(blocks),
                               "n_pos_pairs": len(pos_pairs), "results": results},
                              ensure_ascii=False, indent=2))
    # table
    print("\n\n=== SUMMARY ===")
    cols = ["recall@1","recall@5","recall@10","mrr","pair_auc","dim","model_size_mb","load_s","per_doc_ms","needs_torch_at_inference"]
    print(f"{'model':28} " + " ".join(f"{c:>10}" for c in cols))
    for name, m in results.items():
        if "error" in m:
            print(f"{name:28} ERROR: {m['error'][:60]}"); continue
        print(f"{name:28} " + " ".join(f"{str(m.get(c,'')):>10}" for c in cols))
    print(f"\n[out] {OUT}")


if __name__ == "__main__":
    main()
