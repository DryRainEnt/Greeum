"""LangChain ``BaseRetriever`` adapter for Greeum.

Wraps Greeum search behind the LangChain retriever interface so Greeum drops
into any LangChain RAG chain. Supports both **in-process** (``BlockManager``)
and **remote** (``GreeumHTTPClient``) modes via a single ``search_fn``
indirection — no pydantic gymnastics needed to hold non-serialisable state.

Quick start:

    from greeum.core import DatabaseManager
    from greeum.core.block_manager import BlockManager
    from greeum.adapters.langchain import GreeumRetriever

    bm = BlockManager(DatabaseManager())
    retriever = GreeumRetriever.from_block_manager(bm, k=5)
    docs = retriever.invoke("프로젝트 결정 사항")

Or against a remote Greeum HTTP server:

    from greeum.client.http_client import GreeumHTTPClient
    client = GreeumHTTPClient(base_url="http://localhost:8400", api_key="...")
    retriever = GreeumRetriever.from_http_client(client, k=5)

Install:
    pip install greeum[langchain]
"""
from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional

try:  # framework gate
    from langchain_core.callbacks import CallbackManagerForRetrieverRun
    from langchain_core.documents import Document
    from langchain_core.retrievers import BaseRetriever
    from pydantic import ConfigDict, Field
except ImportError as exc:  # pragma: no cover - install-time error path
    raise ImportError(
        "LangChain is not installed. Install with one of:\n"
        "  pip install greeum[langchain]\n"
        "  pip install 'langchain-core>=0.3'"
    ) from exc


SearchFn = Callable[[str, int], List[Dict[str, Any]]]


def _block_to_document(block: Dict[str, Any]) -> Document:
    """Map a Greeum block dict (search result) → LangChain Document.

    Tolerant of both BlockManager.search() shape and the REST /search response
    item shape: ``content`` may live under ``content`` or ``context``;
    relevance may be ``similarity`` or ``final_score`` or ``relevance_score``.
    """
    content = (
        block.get("content")
        or block.get("context")
        or block.get("page_content")
        or ""
    )
    score = (
        block.get("similarity")
        or block.get("final_score")
        or block.get("relevance_score")
        or block.get("score")
    )
    metadata: Dict[str, Any] = {
        "block_index": block.get("block_index"),
        "timestamp": block.get("timestamp"),
        "branch_id": block.get("branch_id") or block.get("root"),
        "slot": block.get("slot"),
        "tags": block.get("tags") or [],
        "keywords": block.get("keywords") or [],
        "importance": block.get("importance"),
        "score": score,
    }
    # Drop None entries for tidiness.
    metadata = {k: v for k, v in metadata.items() if v is not None}
    return Document(page_content=str(content), metadata=metadata)


class GreeumRetriever(BaseRetriever):
    """LangChain retriever backed by Greeum's hybrid search.

    Instantiate via the ``from_block_manager`` or ``from_http_client``
    classmethods rather than the bare constructor — they wire ``search_fn`` for
    you. ``search_fn`` takes ``(query, k)`` and returns a list of block dicts.
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    search_fn: SearchFn
    k: int = Field(default=5, description="Top-k results per retrieval call")

    def _get_relevant_documents(  # noqa: D401
        self,
        query: str,
        *,
        run_manager: CallbackManagerForRetrieverRun,
    ) -> List[Document]:
        results = self.search_fn(query, self.k)
        return [_block_to_document(b) for b in results]

    # ---- Convenience constructors ----------------------------------------

    @classmethod
    def from_block_manager(cls, block_manager: Any, k: int = 5) -> "GreeumRetriever":
        """In-process: use a live ``BlockManager`` instance directly."""
        def _search(query: str, limit: int) -> List[Dict[str, Any]]:
            return block_manager.search(query, limit=limit)
        return cls(search_fn=_search, k=k)

    @classmethod
    def from_http_client(cls, client: Any, k: int = 5,
                         slot: Optional[str] = None) -> "GreeumRetriever":
        """Remote: query a Greeum HTTP server via ``GreeumHTTPClient``.

        ``slot`` optionally restricts retrieval to a specific STM anchor slot
        (A/B/C). The REST response's ``results`` array is returned to the
        caller.
        """
        def _search(query: str, limit: int) -> List[Dict[str, Any]]:
            resp = client.search(query=query, limit=limit, slot=slot)
            # REST envelope: {"results": [...], "search_stats": {...}}
            if isinstance(resp, dict) and "results" in resp:
                return list(resp["results"])
            return list(resp) if isinstance(resp, list) else []
        return cls(search_fn=_search, k=k)


__all__ = ["GreeumRetriever"]
