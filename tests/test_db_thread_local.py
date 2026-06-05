"""Tests for DatabaseManager thread-local connection mode (Auto-3).

The default mode (single shared connection, legacy v5.3.0 behavior) is exercised
indirectly by the rest of the test suite. These tests focus on the opt-in
thread-local mode that fixes the LUCA-reported SQLite cross-thread bug.
"""
from __future__ import annotations

import os
import sqlite3
import tempfile
import threading
import unittest
from unittest.mock import patch

from greeum.core.database_manager import DatabaseManager


class TestThreadLocalConnections(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self._tmp.close()
        self.db_path = self._tmp.name

    def tearDown(self):
        try:
            os.unlink(self.db_path)
        except OSError:
            pass

    def test_default_mode_unchanged(self):
        """Without the env flag, behavior matches legacy: single shared conn."""
        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop("GREEUM_DB_THREAD_LOCAL", None)
            db = DatabaseManager(connection_string=self.db_path)
            self.assertFalse(db._thread_local_mode)
            self.assertIs(db.conn, db._shared_conn)
            self.assertIsNotNone(db._shared_conn)
            db.close()

    def test_thread_local_mode_main_thread(self):
        """In thread-local mode, main thread gets a conn lazily via setup."""
        with patch.dict(os.environ, {"GREEUM_DB_THREAD_LOCAL": "1"}, clear=False):
            db = DatabaseManager(connection_string=self.db_path)
            self.assertTrue(db._thread_local_mode)
            self.assertIsNotNone(db.conn)
            # _shared_conn should stay None in thread-local mode
            self.assertIsNone(db._shared_conn)
            db.close()

    def test_thread_local_mode_cross_thread_no_error(self):
        """The bug: cross-thread access must NOT raise ProgrammingError."""
        with patch.dict(os.environ, {"GREEUM_DB_THREAD_LOCAL": "1"}, clear=False):
            db = DatabaseManager(connection_string=self.db_path)
            errors: list[BaseException] = []
            results: list[int] = []

            def worker():
                try:
                    cur = db.conn.cursor()
                    cur.execute("SELECT 1")
                    row = cur.fetchone()
                    results.append(int(row[0]))
                except BaseException as exc:  # noqa: BLE001
                    errors.append(exc)

            ts = [threading.Thread(target=worker) for _ in range(4)]
            for t in ts:
                t.start()
            for t in ts:
                t.join()

            self.assertEqual(errors, [], f"cross-thread access should not raise: {errors}")
            self.assertEqual(results, [1, 1, 1, 1])
            db.close()

    def test_default_mode_cross_thread_reproduces_bug(self):
        """Document the bug: default mode DOES raise across threads (sanity baseline)."""
        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop("GREEUM_DB_THREAD_LOCAL", None)
            db = DatabaseManager(connection_string=self.db_path)
            err: list[BaseException] = []

            def worker():
                try:
                    db.conn.cursor().execute("SELECT 1").fetchone()
                except BaseException as exc:  # noqa: BLE001
                    err.append(exc)

            t = threading.Thread(target=worker)
            t.start()
            t.join()
            # Expect a sqlite3.ProgrammingError about same-thread.
            # If this assertion ever fails, the legacy bug was fixed and this
            # test should be retired.
            self.assertTrue(
                any(isinstance(e, sqlite3.ProgrammingError) for e in err),
                f"expected ProgrammingError baseline, got: {err}",
            )
            db.close()

    def test_thread_local_different_threads_get_different_conns(self):
        with patch.dict(os.environ, {"GREEUM_DB_THREAD_LOCAL": "1"}, clear=False):
            db = DatabaseManager(connection_string=self.db_path)
            main_conn = db.conn
            worker_conn: list = []

            def worker():
                worker_conn.append(db.conn)

            t = threading.Thread(target=worker)
            t.start()
            t.join()
            self.assertEqual(len(worker_conn), 1)
            self.assertIsNotNone(worker_conn[0])
            self.assertIsNot(main_conn, worker_conn[0])
            db.close()


if __name__ == "__main__":
    unittest.main()
