"""Candidate pair selection using cosine similarity matrix."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Dict, List, Set, Tuple

import numpy as np

from .db import ConsolidatorDB
from .state import StateManager

logger = logging.getLogger(__name__)


@dataclass
class CandidatePair:
    """A pair of blocks to be evaluated by the judge."""
    block_a: int
    block_b: int
    cosine_similarity: float


def select_candidates(
    db: ConsolidatorDB,
    state: StateManager,
    min_cosine_similarity: float = 0.3,
    max_pairs: int = 50,
) -> List[CandidatePair]:
    """Select candidate pairs for judicial deliberation.

    Algorithm:
    1. Load all embeddings → (N, dim) matrix
    2. L2-normalize → cosine similarity via dot product
    3. Exclude already-compared pairs (from consolidation_state)
    4. Exclude already-connected pairs (from associations)
    5. Filter by min_cosine_similarity
    6. Sort descending, return top max_pairs
    """
    # 1. Load embeddings
    raw = db.get_all_embeddings()
    if len(raw) < 2:
        logger.info("Not enough blocks for comparison (%d)", len(raw))
        return []

    # Group by embedding dimension (DB may contain mixed models)
    by_dim: Dict[int, List[Tuple[int, np.ndarray]]] = {}
    for idx, emb in raw:
        by_dim.setdefault(emb.shape[0], []).append((idx, emb))

    for dim, group in by_dim.items():
        logger.info("Embedding group dim=%d: %d blocks", dim, len(group))

    # 3. Load exclusion sets (shared across all dim groups)
    compared_set = state.load_compared_set()
    connected_set = db.get_existing_association_pairs()
    exclude_set = compared_set | connected_set
    logger.info("Excluding %d compared + %d connected = %d pairs",
                len(compared_set), len(connected_set), len(exclude_set))

    # 4. Collect candidate pairs per dimension group
    candidates: List[CandidatePair] = []
    for dim, group in by_dim.items():
        if len(group) < 2:
            continue

        block_indices = [idx for idx, _ in group]
        embeddings = np.stack([emb for _, emb in group])  # (N, dim)

        # 2. L2-normalize and compute cosine similarity matrix
        norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
        norms = np.where(norms == 0, 1.0, norms)
        normalized = embeddings / norms
        sim_matrix = normalized @ normalized.T

        n = len(block_indices)
        for i in range(n):
            for j in range(i + 1, n):
                sim = float(sim_matrix[i, j])
                if sim < min_cosine_similarity:
                    continue

                a, b = block_indices[i], block_indices[j]
                pair_key = (min(a, b), max(a, b))
                if pair_key in exclude_set:
                    continue

                candidates.append(CandidatePair(block_a=pair_key[0], block_b=pair_key[1], cosine_similarity=sim))

    # 5. Sort by similarity descending, take top max_pairs
    candidates.sort(key=lambda c: c.cosine_similarity, reverse=True)
    result = candidates[:max_pairs]

    logger.info("Selected %d candidate pairs (from %d above threshold %.2f)",
                len(result), len(candidates), min_cosine_similarity)
    return result
