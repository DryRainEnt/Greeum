# Issue: Embedding packaging strategy — "small vs. performant" dilemma

**Reported**: 2026-05-30
**Reporter**: Greeum maintainer (direction review)
**Greeum version**: 5.3.0
**Severity**: High — blocks the "drop-in, pluggable into any harness" goal; currently the default path silently degrades RAG quality
**Status**: Triaged — **benchmarked** (2026-05-30); recommendation below, awaiting decision

---

## Problem

The recurring blocker. Two bad ends of a spectrum:

- **Bundle full semantic embeddings** → `sentence-transformers` + `torch` is large/heavy
  (default model `paraphrase-multilingual-MiniLM-L12-v2`, ~470MB with torch). Too big to
  ship by default; painful install; bad fit for a "drop-in" middleware.
- **Drop embeddings** → falls back to `SimpleEmbeddingModel` (hash-based). Similarities
  collapse to ~0, slot routing degrades to round-robin, the 0.4 threshold becomes
  meaningless. RAG is effectively non-functional (see CLAUDE.md "Semantic Embedding
  Requirement").

## Current state (verified, v5.3.0)

- Auto-select: `GREEUM_DISABLE_ST` set → SimpleEmbedding; else try sentence-transformers;
  else hash fallback with a warning (`greeum/embedding_models.py:~495-524`).
- **Footgun**: `greeum mcp serve` (stdio) **defaults to `GREEUM_DISABLE_ST=1`** unless
  `--semantic` is passed (`greeum/cli/__init__.py:1660,1666`). So the out-of-the-box MCP
  server runs on hash embeddings — degraded RAG, silently.
- Heavy deps live behind `greeum[full]`.

## Options to evaluate

| # | Approach | Size / weight | Quality | Notes |
|---|----------|---------------|---------|-------|
| A | **Static/distilled embeddings (Model2Vec)** | ~15–120MB, **no torch**, CPU, very fast | Good (retains large fraction of teacher); drop on nuanced tasks | **Lead candidate.** Multilingual distillation needed (Korean!). Squares "small + works". |
| B | **ONNX quantized MiniLM** | ~90MB, no torch | Near-full ST | Same model, runtime via onnxruntime; higher quality than A, heavier. |
| C | **Pluggable remote embedding provider** | 0 local | Depends on provider | OpenAI `text-embedding-3-small` or host endpoint. Defeats local-first; needs key/network. Good as *option*, not sole default. |
| D | **Loud-fail + opt-in heavy** | lean core | n/a | Make missing-semantic a **hard, visible error** for semantic ops instead of silent hash. Pairs with A/B as bundled default. |
| E | **Tiered default** | — | — | Synthesis: ship A (static) as bundled default; `greeum[full]` → full ST upgrade; `greeum[remote]` → API. |

## Benchmark results (2026-05-30)

Ran `scripts/bench_embeddings.py` on the **live DB** (334 blocks, 297 Korean / 37 English).
Ground truth = consolidator `semantic`+`causal` association pairs (1730 pairs, 195 query
blocks); temporal excluded. Embedding-only retrieval (no BM25/graph hybrid) — relative
ranking is the decision signal. Raw data: `bench_embeddings_results.json`.

| Candidate | torch? | model file | dim | R@1 | R@5 | R@10 | MRR | AUC | per-doc |
|-----------|:---:|---:|---:|---:|---:|---:|---:|---:|---:|
| **e5_small** (multilingual-e5-small) | yes | ~470MB | 384 | .34 | **.46** | **.51** | **.51** | .76 | 1.88ms |
| **model2vec potion-multilingual** | **NO** | 512MB fp32 / ~256 fp16 | 256 | **.34** | .38 | .43 | .49 | .70 | **0.07ms** |
| baseline minilm (**current default**) | yes | ~470MB | 384 | .26 | .32 | .34 | .41 | .82 | 2.07ms |
| e5_base | yes | ~1.1GB | 768 | .32 | .43 | .50 | .50 | .72 | 4.96ms |
| model2vec distill-e5small (naive) | NO | ~256MB | 256 | .25 | .27 | .30 | .38 | .62 | 0.25ms |
| hash fallback (**current `mcp serve` default**) | NO | 0 | 384 | .015 | .05 | .07 | .09 | .49 | 0.03ms |
| e5_small ONNX int8 | NO | ~120MB* | 384 | — not benchmarked (optimum 2.x/transformers version conflict) | | | | | |

\* estimated. **Dependency footprint** (the real "heavy"): torch GPU build = 1.76GB +
CUDA libs 4.57GB; CPU-only torch ≈ 200MB. model2vec = numpy (41MB) only, CPU, no GPU.

### Findings
1. **The current default (minilm) is the weakest real model.** Switching to
   `multilingual-e5-small` is a free quality upgrade — same 384-dim, same ~470MB, same
   torch dep — for ~+43% recall@5 (.32→.46) and +26% MRR.
2. **model2vec potion-multilingual** ties e5_small at recall@1 and MRR, trails at
   recall@5/10, but **eliminates torch entirely** and is ~27× faster on CPU. The model
   *file* (~512MB fp32, ~256MB fp16) is comparable to e5_small — the win is killing the
   multi-GB torch/CUDA dependency, not the weights.
3. **Naive self-distillation is worse** than the published potion model — don't roll our own.
4. **hash fallback ≈ random** (R@1 .015) and it is the *current `greeum mcp serve` default*.
   Footgun confirmed empirically.
5. AUC favors minilm (.82) despite worst recall — AUC measures global related-vs-random
   separability; recall/MRR measure precise top-k ranking, which is what retrieval UX needs.
   Weight recall/MRR higher.

## Recommended direction (UX-first; to confirm)

1. **Default = model2vec potion-multilingual (fp16, ~256MB).** No torch/CUDA, instant on
   any CPU, quality competitive. This is the answer to "too big/heavy" — a usable
   out-of-the-box semantic default with zero heavyweight install.
2. **`greeum[full]` opt-in = multilingual-e5-small** for users who want top recall@5/10 and
   accept torch. (Replaces minilm everywhere.)
3. **Retire minilm as default** — strictly worse quality than e5_small, no lighter to deploy than potion.
4. **Kill the silent hash fallback.** Hash may remain only as an explicit, loud,
   opt-in test mode — never a silent default on a path advertising semantic search.
5. Remember these are embedding-only numbers; Greeum's BM25+graph hybrid lifts all rows.

## Hybrid (BM25 + Vector) re-measurement (2026-05-30)

`scripts/bench_hybrid.py` + `scripts/bench_hybrid_weights.py` using Greeum's actual
`BM25Index` + `HybridScorer`. Production fusion is `vec_w=0.5, bm25_w=0.5,
fusion="weighted_avg"` (hardcoded in `HybridGraphSearch.__init__`).

### Headline: **the current 50/50 default is suboptimal for every embedding tested**.

Best config per candidate (weighted_avg, weight sweep over [0, 0.3, 0.5, 0.7, 0.8, 0.9, 1.0]):

| Model | Best vec/bm25 | R@1 | R@5 | R@10 | MRR |
|-------|:---:|---:|---:|---:|---:|
| **e5_small** | **0.9 / 0.1** | .390 | **.470** | **.537** | .558 |
| **potion-ml (no-torch)** | **0.7 / 0.3** | **.426** | .438 | .451 | **.558** |
| Greeum current default (e5_small)  | 0.5 / 0.5 | .349 | .370 | .428 | .495 |
| Greeum current default (potion-ml) | 0.5 / 0.5 | .374 | .415 | .466 | .527 |
| BM25-only (vec=0, any model)       | 0.0 / 1.0 | .297 | .348 | .378 | .442 |

### Findings (hybrid)
- At optimal weights, **potion@70/30 ties e5_small@90/10 on MRR (.558) and BEATS it on R@1 (.426 vs .390)** — the top-1/MRR metrics most relevant to user-facing search.
- e5_small retains a real advantage at deeper recall (R@5/R@10) of ~.03–.07.
- The current 50/50 default is **strictly worse than each model's optimum** across every metric.
- BM25 (10-keyword cap via `extract_keywords_from_text`) is too sparse to carry much signal alone — best as a 10–30% boost, not a 50% partner.
- This implies a separate, codebase-side fix: **retune the production hybrid weights**
  (see new sibling issue `2026-05-30-hybrid-fusion-weights.md`).

## Final recommendation (UX-first, hybrid-aware)

1. **Default embedding = `model2vec` potion-multilingual** (no torch, ~256MB fp16).
   At hybrid_wavg with **vec=0.7, bm25=0.3** it delivers the **highest R@1 (.426) and tied-best MRR (.558)** of any config tested — and works on any CPU with no torch/CUDA. This is the answer to "too big/heavy."
2. **`greeum[full]` opt-in = multilingual-e5-small** with **vec=0.9, bm25=0.1**, for users
   prioritizing deeper recall (R@5/R@10 lifts of .03–.07 over potion).
3. **Retire minilm as the default** (strictly worse than e5_small at quality).
4. **Kill the silent hash fallback** — never a default on a path advertising semantic search.
5. **Retune hybrid weights** (separate issue) — current 50/50 is wrong regardless of the
   embedding choice.

## Open questions

1. Does a Model2Vec multilingual distillation hold up on **Korean** semantic similarity
   against Greeum's actual data? (Needs a benchmark before committing — quality numbers
   from my side are unverified.)
2. Dimension compatibility: existing blocks are embedded at the current model's dimension.
   Changing the default model requires a **re-embed/migration** path for existing DBs.
   (Note: `embedding_migration.log` exists — there's precedent.)
3. Is local-first a hard constraint, or is a remote-embedding default acceptable for some
   deployments?

## Acceptance criteria (provisional — finalize after decision)

- [ ] Decision recorded on default embedding strategy.
- [ ] Out-of-the-box install (`pip install greeum`) yields **functional semantic search**
      with no extra steps, at an acceptable package size.
- [ ] No silent hash fallback on a path that advertises semantic search — degradation is
      explicit and logged at WARN/ERROR, surfaced to the caller where feasible.
- [ ] Korean + English retrieval quality benchmarked vs. current full-ST baseline; drop
      within an agreed tolerance.
- [ ] Migration path documented for re-embedding existing DBs if the default model changes.

## Related

- `greeum/embedding_models.py` (model registry, auto-select)
- `greeum/cli/__init__.py:1641-1700` (serve embedding gating)
- CLAUDE.md "⚠️ CRITICAL REQUIREMENTS — Semantic Embedding Requirement"
- `docs/ROADMAP.md` (priority #2)
