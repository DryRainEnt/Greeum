"""Tests for the ChatGPT-connector-compat `search` and `fetch` tools ported
from the legacy `production_mcp_server` into `greeum.mcp.native.tools`
(Phase 4 prep, 2026-06).

Verifies dispatch wiring + schema exposure. Uses a temp DB so live data is
untouched.
"""
from __future__ import annotations

import asyncio
import os
import tempfile
import unittest


def _run(coro):
    return asyncio.get_event_loop().run_until_complete(coro)


class TestSearchFetchTools(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Fresh temp DB so we don't touch the live ~/.greeum.
        cls._tmpdir = tempfile.mkdtemp(prefix="greeum_test_searchfetch_")
        os.environ["GREEUM_DATA_DIR"] = cls._tmpdir
        # Suppress hash banner noise during tests (we don't load a real model).
        os.environ["GREEUM_SILENT_HASH_FALLBACK"] = "1"

        from greeum.core import DatabaseManager
        from greeum.core.block_manager import BlockManager
        from greeum.core.stm_manager import STMManager
        from greeum.mcp.native.tools import GreeumMCPTools

        cls.db = DatabaseManager(connection_string=os.path.join(cls._tmpdir, "memory.db"))
        cls.bm = BlockManager(cls.db)
        cls.stm = STMManager(cls.db)
        cls.tools = GreeumMCPTools({
            "db_manager": cls.db,
            "block_manager": cls.bm,
            "stm_manager": cls.stm,
        })

    @classmethod
    def tearDownClass(cls):
        try:
            cls.db.close()
        except Exception:
            pass

    # ---- dispatch wiring -------------------------------------------------
    def test_search_is_dispatched(self):
        out = _run(self.tools.execute_tool("search", {"query": "anything", "limit": 5}))
        self.assertIsInstance(out, str)

    def test_fetch_is_dispatched(self):
        out = _run(self.tools.execute_tool("fetch", {"count": 5}))
        self.assertIsInstance(out, str)

    def test_search_missing_query(self):
        out = _run(self.tools.execute_tool("search", {}))
        self.assertIn("ERROR", out)
        self.assertIn("query", out.lower())

    def test_fetch_invalid_block_id(self):
        out = _run(self.tools.execute_tool("fetch", {"block_id": "not-an-int"}))
        self.assertIn("ERROR", out)
        self.assertIn("integer", out.lower())

    def test_fetch_nonexistent_block(self):
        out = _run(self.tools.execute_tool("fetch", {"block_id": "999999"}))
        self.assertIn("not found", out.lower())

    # ---- schema exposure -------------------------------------------------
    def test_search_and_fetch_in_tools_list(self):
        """tools/list response must advertise `search` and `fetch`."""
        from greeum.mcp.native.protocol import JSONRPCProcessor
        from greeum.mcp.native.server import GreeumNativeMCPServer
        server = GreeumNativeMCPServer()
        proc = JSONRPCProcessor(server)
        result = _run(proc._handle_tools_list({}))
        names = {t["name"] for t in result["tools"]}
        self.assertIn("search", names)
        self.assertIn("fetch", names)
        self.assertIn("search_memory", names)
        self.assertIn("add_memory", names)


if __name__ == "__main__":
    unittest.main()
