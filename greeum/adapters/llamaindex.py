"""LlamaIndex ``BaseRetriever`` adapter for Greeum.

Wraps Greeum search as a LlamaIndex retriever. Same dual-mode design as the
LangChain adapter: pass either a ``BlockManager`` (in-process) or a
``GreeumHTTPClient`` (remote) via the classmethods.

Quick start:

    from greeum.adapters.llamaindex import GreeumRetriever

    retriever = GreeumRetriever.from_block_manager(bm, k=5)
    nodes = retriever.retrieve("프로젝트 결정 사항")

Install:
    pip install greeum[llamaindex]
"""
from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional

try:  # framework gate
    from llama_index.core.retrievers import BaseRetriever
    from llama_index.core.schema import NodeWithScore, QueryBundle, TextNode
except ImportError as exc:  # pragma: no cover - install-time error path
    raise ImportError(
        "LlamaIndex is not installed. Install with one of:\n"
        "  pip install greeum[llamaindex]\n"
        "  pip install 'llama-index-core>=0.11'"
    ) from exc


SearchFn = Callable[[str, int], List[Dict[str, Any]]]


def _block_to_node_with_score(block: Dict[str, Any]) -> NodeWithScore:
    content = (
        block.get("content")
        or block.get("context")
        or ""
    )
    score = (
        block.get("similarity")
        or block.get("final_score")
        or block.get("relevance_score")
        or block.get("score")
        or 0.0
    )
    metadata = {
        "block_index": block.get("block_index"),
        "timestamp": block.get("timestamp"),
        "branch_id": block.get("branch_id") or block.get("root"),
        "slot": block.get("slot"),
        "tags": block.get("tags") or [],
        "keywords": block.get("keywords") or [],
        "importance": block.get("importance"),
    }
    metadata = {k: v for k, v in metadata.items() if v is not None}
    node = TextNode(text=str(content), metadata=metadata)
    return NodeWithScore(node=node, score=float(score) if score is not None else 0.0)


class GreeumRetriever(BaseRetriever):
    """LlamaIndex retriever backed by Greeum's hybrid search."""

    def __init__(self, search_fn: SearchFn, k: int = 5):
        self._search_fn = search_fn
        self._k = k
        super().__init__()

    def _retrieve(self, query_bundle: QueryBundle) -> List[NodeWithScore]:
        query = (
            query_bundle.query_str
            if hasattr(query_bundle, "query_str")
            else str(query_bundle)
        )
        results = self._search_fn(query, self._k)
        return [_block_to_node_with_score(b) for b in results]

    # ---- Convenience constructors ----------------------------------------

    @classmethod
    def from_block_manager(cls, block_manager: Any, k: int = 5) -> "GreeumRetriever":
        def _search(query: str, limit: int) -> List[Dict[str, Any]]:
            return block_manager.search(query, limit=limit)
        return cls(search_fn=_search, k=k)

    @classmethod
    def from_http_client(cls, client: Any, k: int = 5,
                         slot: Optional[str] = None) -> "GreeumRetriever":
        def _search(query: str, limit: int) -> List[Dict[str, Any]]:
            resp = client.search(query=query, limit=limit, slot=slot)
            if isinstance(resp, dict) and "results" in resp:
                return list(resp["results"])
            return list(resp) if isinstance(resp, list) else []
        return cls(search_fn=_search, k=k)


__all__ = ["GreeumRetriever"]
