# Issue: Hybrid fusion weights — 50/50 default is suboptimal for every embedding

**Reported**: 2026-05-30
**Reporter**: Greeum maintainer (embedding benchmark, see sibling issue)
**Greeum version**: 5.3.0
**Severity**: Medium — quality regression vs. simple retune; not a correctness bug
**Status**: Open

---

## Summary

`HybridScorer` and `HybridGraphSearch` hardcode `vector_weight=0.5, bm25_weight=0.5` for
the `weighted_avg` fusion. Empirically (see `2026-05-30-embedding-packaging-strategy.md`
hybrid section + `scripts/bench_hybrid_weights.py`), this is **strictly worse than the
optimum for every embedding model tested**. The 50/50 weight implicitly assumes BM25 and
vector carry equal signal, but with Greeum's current keyword extraction (cap 10 keywords
via `extract_keywords_from_text`), BM25 is sparse and dilutes good vector models.

## Evidence (weight sweep on live DB, 334 blocks, 1730 GT pairs)

| Model | Best vec/bm25 | R@1 | R@5 | R@10 | MRR | At current 50/50 |
|-------|:---:|---:|---:|---:|---:|:---:|
| e5_small  | 0.9 / 0.1 | .390 | .470 | .537 | .558 | .349/.370/.428/.495 |
| potion_ml | 0.7 / 0.3 | .426 | .438 | .451 | .558 | .374/.415/.466/.527 |

The 50/50 default leaves real performance on the table — 6–13% absolute MRR and 7–11%
absolute recall@10 for both models. Re-tuning is a pure code change with no model
retraining and no user-side action.

## Where the constant lives

- `greeum/core/hybrid_graph_search.py` (HybridGraphSearch `__init__`):
  `self.hybrid_scorer = HybridScorer(self.bm25_index, vector_weight=0.5, bm25_weight=0.5)`
- `greeum/core/bm25_index.py` (HybridScorer defaults): `vector_weight=0.5, bm25_weight=0.5`

## Scope

1. Change the default hybrid weights. **Conservative single value: `vec=0.7, bm25=0.3`**
   (close to potion_ml's peak, also lifts e5_small substantially over 50/50). If the
   embedding default lands as `potion_ml`, 0.7/0.3 is optimal.
2. Optionally expose weights via env vars / config so deployments can tune.
3. Consider per-embedding-model defaults (potion=0.7/0.3, e5_small=0.9/0.1) once the
   embedding strategy is finalized.
4. Evaluate switching the production fusion to RRF (less sensitive to score
   normalization) — but in this benchmark `weighted_avg` at optimum weights beat RRF.

## Acceptance criteria

- [ ] Default hybrid weights changed; `HybridScorer` accepts override via config/env.
- [ ] Re-run `scripts/bench_hybrid.py` against the new default; recall@5/10 and MRR
      improve over 50/50 baseline across the embedding models in scope.
- [ ] No regression in any path that calls `HybridGraphSearch` (DFS pruning thresholds
      may interact with absolute score range — verify `threshold` / `explore_threshold`
      defaults still make sense).
- [ ] Brief docs note: "fusion weights tuned for sparse-BM25 (10-keyword) regime."

## Open questions

1. Is the long-term direction to *also* improve BM25 (raise the 10-keyword cap or use
   token-level TF-IDF)? If yes, weights would need retuning again afterward. Track
   separately if pursued.
2. Should `explore_threshold` / `threshold` in `HybridGraphSearch` be re-tuned alongside?
   They were chosen against the old score distribution.

## Related

- Sibling: `2026-05-30-embedding-packaging-strategy.md` (the trigger for this finding)
- `greeum/core/bm25_index.py` — `HybridScorer`
- `greeum/core/hybrid_graph_search.py` — production default site
- `scripts/bench_hybrid_weights.py` — reproducer
