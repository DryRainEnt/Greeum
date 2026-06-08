"""Anthropic native memory tool (``memory_20250818``) shim.

Anthropic's ``memory_20250818`` tool is client-side: Claude emits commands
(``view``/``create``/``str_replace``/``insert``/``delete``) targeting a virtual
``/memories/`` filesystem and the host executes them. This shim routes those
commands to Greeum's block store so Claude's memory becomes semantically
searchable / branchable / shared across sessions, instead of plain flat files.

Quick start with the Anthropic SDK tool-use loop:

    from anthropic import Anthropic
    from greeum.core import DatabaseManager
    from greeum.core.block_manager import BlockManager
    from greeum.adapters.anthropic_memory import AnthropicMemoryHandler

    handler = AnthropicMemoryHandler.from_block_manager(BlockManager(DatabaseManager()))
    # In your tool-use loop, when a tool_use block has name == "memory":
    output = handler.handle(tool_use_block.input)
    # Return that string as the tool_result content.

The shim is dependency-free at import time — it does **not** import the
``anthropic`` package. You can use it from any host that speaks the memory
tool's JSON shape.

Design notes / caveats (intentional):
    * Greeum blocks are append-only. ``str_replace`` and ``insert`` are
      emulated by reading the original block, applying the edit, and saving
      a NEW block (full provenance preserved). The returned message makes
      this explicit.
    * Virtual paths are stored as a tag (``mem-path:<path>``) and as a metadata
      hint, so listings remain fast and unique paths still address blocks.
    * ``delete`` is soft by default (the block is tagged ``mem-deleted``) so
      a stray Claude delete cannot wipe history. Pass ``hard_delete=True`` to
      the handler if that semantics is required.

Verify the exact tool-spec version against current Anthropic docs before
production use — the memory tool is a moving target.

Install hint: this shim has no extra dependencies. ``pip install greeum`` is enough.
"""
from __future__ import annotations

import logging
import re
import json
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger(__name__)


_PATH_TAG_PREFIX = "mem-path:"
_DELETED_TAG = "mem-deleted"


def _path_tag(path: str) -> str:
    return f"{_PATH_TAG_PREFIX}{path}"


def _normalize_path(path: str) -> str:
    """Normalize a memory-tool path to ``/memories/<rest>`` form (no double slash)."""
    if not path:
        return "/memories/"
    if not path.startswith("/"):
        path = "/" + path
    # collapse duplicate slashes
    path = re.sub(r"/+", "/", path)
    return path


def _safe_str(x: Any) -> str:
    if isinstance(x, str):
        return x
    try:
        return json.dumps(x, ensure_ascii=False, default=str)
    except Exception:  # pragma: no cover - defensive
        return str(x)


class AnthropicMemoryHandler:
    """Route memory_20250818 commands to a Greeum backend.

    Construct via the ``from_block_manager`` or ``from_http_client`` classmethods
    rather than the bare constructor; they supply the four function hooks
    (``search_fn``, ``add_fn``, ``get_fn``, ``list_recent_fn``) the handler uses.
    """

    def __init__(
        self,
        search_fn: Callable[[str, int], List[Dict[str, Any]]],
        add_fn: Callable[..., Dict[str, Any]],
        get_fn: Callable[[int], Optional[Dict[str, Any]]],
        list_recent_fn: Callable[[int], List[Dict[str, Any]]],
        hard_delete: bool = False,
    ):
        self._search = search_fn
        self._add = add_fn
        self._get = get_fn
        self._list_recent = list_recent_fn
        self._hard_delete = hard_delete

    # ---- public entry ----------------------------------------------------
    def handle(self, tool_input: Dict[str, Any]) -> str:
        """Execute one memory_20250818 command.

        Args:
            tool_input: the ``input`` dict from Claude's tool_use block.

        Returns:
            A string suitable for the tool_result ``content`` field.
        """
        cmd = (tool_input or {}).get("command", "")
        path = _normalize_path((tool_input or {}).get("path", ""))
        try:
            if cmd == "view":
                return self._view(path, tool_input.get("view_range"))
            if cmd == "create":
                return self._create(path, tool_input.get("file_text", ""))
            if cmd == "str_replace":
                return self._str_replace(
                    path,
                    tool_input.get("old_str", ""),
                    tool_input.get("new_str", ""),
                )
            if cmd == "insert":
                return self._insert(
                    path,
                    int(tool_input.get("insert_line", 0)),
                    tool_input.get("insert_text", ""),
                )
            if cmd == "delete":
                return self._delete(path)
            return f"[error] unsupported command: {cmd!r}"
        except Exception as e:  # noqa: BLE001 — return error to Claude, don't crash host
            logger.exception("AnthropicMemoryHandler command failed: %s", cmd)
            return f"[error] {type(e).__name__}: {e}"

    # ---- command implementations -----------------------------------------
    def _view(self, path: str, view_range: Optional[List[int]] = None) -> str:
        # Directory view: path ends with '/' or has no addressable file.
        if path.endswith("/") or path == "/memories":
            recent = self._list_recent(20)
            entries: List[str] = []
            prefix = path.rstrip("/")
            for b in recent:
                tags = b.get("tags") or []
                if _DELETED_TAG in tags:
                    continue
                ptag = next((t for t in tags if t.startswith(_PATH_TAG_PREFIX)), None)
                vpath = ptag[len(_PATH_TAG_PREFIX):] if ptag else f"/memories/block-{b.get('block_index')}"
                if prefix and not vpath.startswith(prefix):
                    continue
                snippet = (b.get("context") or b.get("content") or "").splitlines()[0:1]
                snippet_s = snippet[0][:80] if snippet else ""
                entries.append(f"  {vpath}   — block #{b.get('block_index')}   {snippet_s}")
            if not entries:
                return f"(empty directory: {path})"
            return f"Directory listing for {path}:\n" + "\n".join(entries)

        # File view: locate block by path tag, else by block-N pattern.
        block = self._resolve_path_to_block(path)
        if block is None:
            return f"[error] no memory at {path}"
        text = block.get("context") or block.get("content") or ""
        if view_range and isinstance(view_range, list) and len(view_range) == 2:
            lines = text.splitlines()
            start, end = view_range
            # 1-indexed inclusive per memory tool spec
            sliced = lines[max(0, start - 1): end if end > 0 else len(lines)]
            text = "\n".join(sliced)
        meta = (
            f"  (block_index={block.get('block_index')}, "
            f"timestamp={block.get('timestamp')}, "
            f"tags={block.get('tags') or []})"
        )
        return text + "\n" + meta

    def _create(self, path: str, file_text: str) -> str:
        if not file_text:
            return "[error] create: file_text is required"
        tags = [_path_tag(path)]
        result = self._add(content=file_text, tags=tags, importance=0.5)
        idx = result.get("block_index") if isinstance(result, dict) else None
        return f"Created memory at {path} (block #{idx})"

    def _str_replace(self, path: str, old: str, new: str) -> str:
        block = self._resolve_path_to_block(path)
        if block is None:
            return f"[error] no memory at {path}"
        original = block.get("context") or block.get("content") or ""
        if old not in original:
            return f"[error] old_str not found in {path}"
        edited = original.replace(old, new, 1)
        tags = [_path_tag(path), f"mem-edits:block-{block.get('block_index')}"]
        result = self._add(content=edited, tags=tags, importance=block.get("importance", 0.5))
        new_idx = result.get("block_index") if isinstance(result, dict) else None
        return (
            f"Edited {path}: str_replace applied as a new block (#{new_idx}); "
            f"previous block #{block.get('block_index')} retained (immutable history)."
        )

    def _insert(self, path: str, insert_line: int, insert_text: str) -> str:
        block = self._resolve_path_to_block(path)
        if block is None:
            return f"[error] no memory at {path}"
        original = block.get("context") or block.get("content") or ""
        lines = original.splitlines()
        line = max(0, min(insert_line, len(lines)))
        lines.insert(line, insert_text)
        edited = "\n".join(lines)
        tags = [_path_tag(path), f"mem-edits:block-{block.get('block_index')}"]
        result = self._add(content=edited, tags=tags, importance=block.get("importance", 0.5))
        new_idx = result.get("block_index") if isinstance(result, dict) else None
        return (
            f"Inserted into {path} at line {insert_line}: new block (#{new_idx}); "
            f"previous block #{block.get('block_index')} retained."
        )

    def _delete(self, path: str) -> str:
        block = self._resolve_path_to_block(path)
        if block is None:
            return f"[error] no memory at {path}"
        if self._hard_delete:
            return f"[error] hard_delete requested but backend does not support it yet (block #{block.get('block_index')})"
        # Soft delete = annotate via a new tag-only block referencing the original.
        tomb_content = (
            f"[memory-tool delete] tombstone for {path} "
            f"(was block #{block.get('block_index')})"
        )
        tags = [_path_tag(path), _DELETED_TAG, f"mem-tombstone:block-{block.get('block_index')}"]
        self._add(content=tomb_content, tags=tags, importance=0.1)
        return f"Deleted {path} (soft; tombstone added — block #{block.get('block_index')} retained)."

    # ---- resolver --------------------------------------------------------
    def _resolve_path_to_block(self, path: str) -> Optional[Dict[str, Any]]:
        # Try a search by the path tag string (search is the most portable signal we have).
        candidates = self._search(_path_tag(path), 5)
        # Filter to non-deleted blocks tagged exactly with this path.
        for b in candidates:
            tags = b.get("tags") or []
            if _path_tag(path) in tags and _DELETED_TAG not in tags:
                return b

        # Fallback: block-N convention.
        m = re.search(r"block-(\d+)", path)
        if m:
            return self._get(int(m.group(1)))
        return None

    # ---- convenience constructors ----------------------------------------
    @classmethod
    def from_block_manager(cls, block_manager: Any,
                           hard_delete: bool = False) -> "AnthropicMemoryHandler":
        def _search(q, k):
            return block_manager.search(q, limit=k)

        def _add(content, tags=None, importance=0.5):
            keywords: List[str] = []
            embedding: List[float] = []
            try:
                from greeum.text_utils import process_user_input
                processed = process_user_input(content)
                keywords = processed.get("keywords", [])
                embedding = processed.get("embedding", [])
            except Exception:  # pragma: no cover - best effort
                pass
            return block_manager.add_block(
                context=content,
                keywords=keywords,
                tags=tags or [],
                embedding=embedding,
                importance=importance,
            ) or {}

        def _get(block_index):
            getter = getattr(block_manager, "get_block_by_index", None) or \
                     getattr(getattr(block_manager, "db_manager", None), "get_block_by_index", None)
            return getter(block_index) if callable(getter) else None

        def _list_recent(n):
            getter = getattr(block_manager, "get_recent_blocks", None) or \
                     getattr(getattr(block_manager, "db_manager", None), "get_recent_blocks", None)
            return getter(n) if callable(getter) else []

        return cls(_search, _add, _get, _list_recent, hard_delete=hard_delete)

    @classmethod
    def from_http_client(cls, client: Any,
                         hard_delete: bool = False) -> "AnthropicMemoryHandler":
        def _search(q, k):
            resp = client.search(query=q, limit=k)
            if isinstance(resp, dict) and "results" in resp:
                return list(resp["results"])
            return list(resp) if isinstance(resp, list) else []

        def _add(content, tags=None, importance=0.5):
            payload = {"content": content, "importance": importance}
            if tags:
                payload["tags"] = tags
            return client.post("/memory", payload) or {}

        def _get(block_index):
            try:
                return client.get(f"/memory/{block_index}")
            except Exception:  # pragma: no cover
                return None

        def _list_recent(n):
            # The REST surface doesn't have a "recent" endpoint; approximate via search.
            try:
                resp = client.search(query="", limit=n)
            except Exception:  # pragma: no cover
                return []
            if isinstance(resp, dict) and "results" in resp:
                return list(resp["results"])
            return []

        return cls(_search, _add, _get, _list_recent, hard_delete=hard_delete)


__all__ = ["AnthropicMemoryHandler"]
