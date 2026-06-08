"""Tests for greeum.adapters — LangChain, LlamaIndex, Anthropic memory tool.

LangChain and LlamaIndex are optional dependencies; their tests skip cleanly
when the framework isn't installed. The Anthropic memory shim has no extra
dependencies and is always tested.
"""
from __future__ import annotations

import importlib
import unittest


def _have(mod: str) -> bool:
    try:
        importlib.import_module(mod)
        return True
    except ImportError:
        return False


# --- Anthropic memory tool shim (no optional deps) -----------------------
class TestAnthropicMemoryHandler(unittest.TestCase):
    def setUp(self):
        from greeum.adapters.anthropic_memory import AnthropicMemoryHandler

        # In-memory fake "store" implementing the four callables.
        self.store: list[dict] = []
        self.next_idx = 1
        self.path_to_block: dict[str, dict] = {}

        def add_fn(content, tags=None, importance=0.5):
            blk = {
                "block_index": self.next_idx,
                "context": content,
                "tags": list(tags or []),
                "importance": importance,
                "timestamp": "2026-06-09T00:00:00",
            }
            self.next_idx += 1
            self.store.append(blk)
            for t in blk["tags"]:
                if t.startswith("mem-path:"):
                    self.path_to_block[t[len("mem-path:"):]] = blk
            return blk

        def search_fn(query, k):
            # very small "BM25-like": substring match in tags or content
            hits = [b for b in self.store if query in (b.get("context") or "") or query in (b.get("tags") or [])]
            return hits[:k]

        def get_fn(idx):
            for b in self.store:
                if b["block_index"] == idx:
                    return b
            return None

        def list_recent_fn(n):
            return list(reversed(self.store))[:n]

        self.handler = AnthropicMemoryHandler(search_fn, add_fn, get_fn, list_recent_fn)

    def test_create_and_view_file(self):
        out = self.handler.handle({"command": "create", "path": "/memories/note.md",
                                   "file_text": "hello world"})
        self.assertIn("Created memory at /memories/note.md", out)
        view = self.handler.handle({"command": "view", "path": "/memories/note.md"})
        self.assertIn("hello world", view)
        self.assertIn("block_index=1", view)

    def test_view_directory_empty(self):
        out = self.handler.handle({"command": "view", "path": "/memories/"})
        self.assertIn("empty directory", out)

    def test_view_directory_after_creates(self):
        self.handler.handle({"command": "create", "path": "/memories/a.md", "file_text": "A"})
        self.handler.handle({"command": "create", "path": "/memories/b.md", "file_text": "B"})
        listing = self.handler.handle({"command": "view", "path": "/memories/"})
        self.assertIn("/memories/a.md", listing)
        self.assertIn("/memories/b.md", listing)

    def test_str_replace_creates_new_block_preserves_old(self):
        self.handler.handle({"command": "create", "path": "/memories/edit.md",
                             "file_text": "alpha bravo charlie"})
        edited = self.handler.handle({
            "command": "str_replace",
            "path": "/memories/edit.md",
            "old_str": "bravo",
            "new_str": "BRAVO",
        })
        self.assertIn("new block", edited)
        # Original block #1 still in store
        self.assertEqual(self.store[0]["context"], "alpha bravo charlie")
        # New block exists with edit
        self.assertTrue(any("BRAVO" in b["context"] for b in self.store))

    def test_insert(self):
        self.handler.handle({"command": "create", "path": "/memories/x.md",
                             "file_text": "line1\nline2\nline3"})
        out = self.handler.handle({
            "command": "insert",
            "path": "/memories/x.md",
            "insert_line": 1,
            "insert_text": "INSERTED",
        })
        self.assertIn("new block", out)
        # Latest block contains the inserted line
        latest = self.store[-1]["context"]
        self.assertIn("INSERTED", latest)

    def test_delete_is_soft(self):
        self.handler.handle({"command": "create", "path": "/memories/del.md", "file_text": "doomed"})
        out = self.handler.handle({"command": "delete", "path": "/memories/del.md"})
        self.assertIn("soft", out)
        # tombstone exists
        self.assertTrue(any("mem-deleted" in (b.get("tags") or []) for b in self.store))
        # original still there
        self.assertTrue(any(b.get("context") == "doomed" for b in self.store))

    def test_unsupported_command(self):
        out = self.handler.handle({"command": "nuke", "path": "/memories/"})
        self.assertIn("unsupported command", out)

    def test_view_nonexistent_file(self):
        out = self.handler.handle({"command": "view", "path": "/memories/missing.md"})
        self.assertIn("no memory", out)

    def test_path_normalization(self):
        # double slashes should collapse
        self.handler.handle({"command": "create", "path": "//memories///dir//file.md",
                             "file_text": "ok"})
        view = self.handler.handle({"command": "view", "path": "/memories/dir/file.md"})
        self.assertIn("ok", view)


# --- LangChain adapter ----------------------------------------------------
@unittest.skipUnless(_have("langchain_core"), "langchain_core not installed (pip install greeum[langchain])")
class TestLangChainAdapter(unittest.TestCase):
    def test_block_to_document_mapping(self):
        from greeum.adapters.langchain import _block_to_document
        d = _block_to_document({
            "block_index": 42,
            "content": "hello",
            "similarity": 0.87,
            "tags": ["t1"],
            "timestamp": "2026-06-09",
        })
        self.assertEqual(d.page_content, "hello")
        self.assertEqual(d.metadata["block_index"], 42)
        self.assertEqual(d.metadata["score"], 0.87)
        self.assertEqual(d.metadata["tags"], ["t1"])

    def test_retriever_via_search_fn(self):
        from greeum.adapters.langchain import GreeumRetriever
        records = [
            {"block_index": 1, "content": "alpha", "similarity": 0.9, "tags": []},
            {"block_index": 2, "content": "beta",  "similarity": 0.7, "tags": []},
        ]
        retriever = GreeumRetriever(search_fn=lambda q, k: records[:k], k=2)
        docs = retriever.invoke("anything")
        self.assertEqual(len(docs), 2)
        self.assertEqual(docs[0].page_content, "alpha")
        self.assertEqual(docs[0].metadata["block_index"], 1)


# --- LlamaIndex adapter ---------------------------------------------------
@unittest.skipUnless(_have("llama_index.core"), "llama_index.core not installed (pip install greeum[llamaindex])")
class TestLlamaIndexAdapter(unittest.TestCase):
    def test_retrieve_returns_nodes_with_score(self):
        from greeum.adapters.llamaindex import GreeumRetriever
        from llama_index.core.schema import QueryBundle
        records = [
            {"block_index": 1, "content": "x1", "similarity": 0.5},
            {"block_index": 2, "content": "x2", "similarity": 0.4},
        ]
        retriever = GreeumRetriever(search_fn=lambda q, k: records[:k], k=2)
        out = retriever._retrieve(QueryBundle(query_str="q"))
        self.assertEqual(len(out), 2)
        self.assertEqual(out[0].score, 0.5)
        self.assertEqual(out[0].node.text, "x1")
        self.assertEqual(out[0].node.metadata["block_index"], 1)


if __name__ == "__main__":
    unittest.main()
