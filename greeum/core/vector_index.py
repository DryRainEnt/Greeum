from __future__ import annotations

"""Lightweight FAISS wrapper used internally by Greeum.
조건: faiss-cpu 패키지 설치가 실패할 수 있으므로 Optional import.
"""

from typing import List, Tuple, Optional

try:
    import faiss  # type: ignore
except ImportError:  # pragma: no cover
    faiss = None  # type: ignore

import numpy as np

class FaissVectorIndex:
    """In-memory FAISS IndexFlatL2 wrapper."""

    def __init__(self, dim: int):
        if faiss is None:
            raise ImportError("faiss-cpu 가 설치되지 않았습니다.")
        self.dim = dim
        self.index = faiss.IndexFlatL2(dim)
        self._id_to_block: List[int] = []

    # ------------------------------------------------------------------
    def add_vectors(self, block_indices: List[int], vectors: List[List[float]]):
        if not vectors:
            return
        arr = np.array(vectors, dtype="float32")
        if arr.shape[1] != self.dim:
            raise ValueError("벡터 차원이 일치하지 않습니다.")
        self.index.add(arr)
        self._id_to_block.extend(block_indices)

    def search(self, vector: List[float], top_k: int = 5) -> List[Tuple[int, float]]:
        if self.index.ntotal == 0:
            return []
        vec = np.array([vector], dtype="float32")
        distances, idxs = self.index.search(vec, top_k)
        # FAISS 는 L2 거리 반환 – 유사도 (1 / (1 + d)) 로 변환
        results: List[Tuple[int, float]] = []
        for i, dist in zip(idxs[0], distances[0]):
            if i == -1:
                continue
            similarity = 1.0 / (1.0 + float(dist))
            block_index = self._id_to_block[i]
            results.append((block_index, similarity))
        return results

    # ------------------------------------------------------------------
    def clear(self):
        self.index.reset()
        self._id_to_block.clear() 