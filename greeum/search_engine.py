from __future__ import annotations
"""Simple internal search engine that combines vector search and optional BERT re-ranker.
Relative/quick benchmark only – external detailed tests handled in GreeumTest repo.
"""
from typing import List, Dict, Any, Optional
import time
import logging

from .block_manager import BlockManager
from .embedding_models import get_embedding

try:
    from sentence_transformers import CrossEncoder  # type: ignore
except ImportError:
    CrossEncoder = None  # type: ignore

logger = logging.getLogger(__name__)

class BertReranker:
    """Thin wrapper around sentence-transformers CrossEncoder."""
    def __init__(self, model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"):
        if CrossEncoder is None:
            raise ImportError("sentence-transformers 가 설치되지 않았습니다.")
        self.model = CrossEncoder(model_name)

    def rerank(self, query: str, docs: List[Dict[str, Any]], top_k: int) -> List[Dict[str, Any]]:
        pairs = [[query, d["context"]] for d in docs]
        scores = self.model.predict(pairs, convert_to_numpy=True)
        for d, s in zip(docs, scores):
            d["relevance_score"] = float(s)
        docs.sort(key=lambda x: x["relevance_score"], reverse=True)
        return docs[:top_k]

class SearchEngine:
    def __init__(self, block_manager: Optional[BlockManager] = None, reranker: Optional[BertReranker] = None):
        self.bm = block_manager or BlockManager()
        self.reranker = reranker

    def search(self, query: str, top_k: int = 5) -> Dict[str, Any]:
        """Vector search → optional rerank. Returns blocks and latency metrics."""
        t0 = time.perf_counter()
        emb = get_embedding(query)
        vec_time = time.perf_counter()
        candidate_blocks = self.bm.search_by_embedding(emb, top_k=top_k*3)
        search_time = time.perf_counter()
        if self.reranker is not None and candidate_blocks:
            candidate_blocks = self.reranker.rerank(query, candidate_blocks, top_k)
        end_time = time.perf_counter()
        return {
            "blocks": candidate_blocks[:top_k],
            "timing": {
                "embed_ms": (vec_time - t0)*1000,
                "vector_ms": (search_time - vec_time)*1000,
                "rerank_ms": (end_time - search_time)*1000,
            }
        } 