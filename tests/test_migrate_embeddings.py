"""Tests for scripts/migrate_embeddings.py (Phase 1C).

Uses temp DBs simulating the live mixed-dim state. The fastest deterministic
model (SimpleEmbeddingModel, hash-based) is used as the migration target so
tests don't depend on sentence-transformers / model2vec downloads.
"""
from __future__ import annotations

import os
import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path

import numpy as np

# Make scripts/ importable
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
import migrate_embeddings as mig  # noqa: E402


def _seed_db(path: str, blocks: list[tuple[int, str, int, str]]) -> None:
    """Create a minimal Greeum-compatible DB with given mixed embeddings.

    Each tuple = (block_index, context, embedding_dim, embedding_model).
    """
    conn = sqlite3.connect(path)
    try:
        conn.execute("""
            CREATE TABLE blocks (
                block_index INTEGER PRIMARY KEY,
                timestamp TEXT,
                context TEXT,
                importance REAL,
                hash TEXT,
                prev_hash TEXT
            )
        """)
        conn.execute("""
            CREATE TABLE block_embeddings (
                block_index INTEGER PRIMARY KEY,
                embedding BLOB,
                embedding_model TEXT,
                embedding_dim INTEGER
            )
        """)
        for idx, ctx, dim, model in blocks:
            conn.execute(
                "INSERT INTO blocks (block_index, timestamp, context, importance, hash, prev_hash) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (idx, "2026-06-01T00:00:00", ctx, 0.5, f"h{idx}", f"h{idx-1}" if idx > 0 else ""),
            )
            arr = np.random.RandomState(idx).rand(dim).astype(np.float32)
            conn.execute(
                "INSERT INTO block_embeddings (block_index, embedding, embedding_model, embedding_dim) "
                "VALUES (?, ?, ?, ?)",
                (idx, arr.tobytes(), model, dim),
            )
        conn.commit()
    finally:
        conn.close()


def _read_dim_distribution(path: str) -> dict[int, int]:
    conn = sqlite3.connect(path)
    try:
        out: dict[int, int] = {}
        for (dim,) in conn.execute("SELECT embedding_dim FROM block_embeddings"):
            out[int(dim)] = out.get(int(dim), 0) + 1
        return out
    finally:
        conn.close()


class TestMigrateEmbeddings(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp(prefix="greeum_migrate_test_")
        self.db = os.path.join(self.tmpdir, "memory.db")
        # Seed: mixed-dim — 3×128 (legacy hash), 5×768 (legacy ST-pad), 2×3072 (OpenAI)
        seed = []
        for i in range(3):
            seed.append((i, f"hash-era block {i}", 128, "default"))
        for i in range(3, 8):
            seed.append((i, f"sentence-transformer block {i}", 768, "default"))
        for i in range(8, 10):
            seed.append((i, f"openai block {i}", 3072, "default"))
        _seed_db(self.db, seed)
        os.environ["GREEUM_SILENT_HASH_FALLBACK"] = "1"

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    # ---- dry-run ----------------------------------------------------------
    def test_dry_run_reports_plan_no_writes(self):
        before = _read_dim_distribution(self.db)
        summary = mig.migrate(self.db, model_hint="simple", apply=False)
        after = _read_dim_distribution(self.db)
        self.assertEqual(before, after, "dry-run must not write to DB")
        self.assertEqual(summary["mode"], "dry-run")
        self.assertEqual(summary["total_blocks"], 10)
        self.assertEqual(summary["to_migrate"], 10)
        self.assertEqual(summary["existing_dim_distribution"], {128: 3, 768: 5, 3072: 2})

    # ---- apply ------------------------------------------------------------
    def test_apply_normalises_all_dimensions(self):
        summary = mig.migrate(self.db, model_hint="simple", apply=True)
        self.assertEqual(summary["mode"], "apply")
        self.assertTrue(summary["verification_ok"], summary)
        post = _read_dim_distribution(self.db)
        self.assertEqual(len(post), 1, f"post should have one dim only, got {post}")
        # SimpleEmbeddingModel default is 768
        self.assertEqual(post.get(768), 10)

    def test_apply_creates_backup(self):
        summary = mig.migrate(self.db, model_hint="simple", apply=True)
        backup = summary.get("backup")
        self.assertIsNotNone(backup)
        self.assertTrue(Path(backup).exists())
        # Backup retains the original mixed dims.
        self.assertEqual(_read_dim_distribution(backup), {128: 3, 768: 5, 3072: 2})

    def test_no_backup_flag_skips_backup(self):
        summary = mig.migrate(self.db, model_hint="simple", apply=True, do_backup=False)
        self.assertIsNone(summary.get("backup"))

    def test_idempotent_second_run_is_noop(self):
        # First pass migrates everything.
        mig.migrate(self.db, model_hint="simple", apply=True)
        # Second pass: everything should be already at target.
        summary2 = mig.migrate(self.db, model_hint="simple", apply=True, do_backup=False)
        self.assertEqual(summary2["skipped_already_current"], 10)
        self.assertEqual(summary2["to_migrate"], 0)

    def test_limit_restricts_processed_blocks(self):
        summary = mig.migrate(self.db, model_hint="simple", apply=True, limit=4)
        self.assertEqual(summary["total_blocks"], 4)
        # Only first 4 blocks migrated; remaining 6 keep original dim.
        post = _read_dim_distribution(self.db)
        # 4 are now at 768 (simple), 2 remain at 128, 5-? at 768 — depends.
        # Actually first 4 block_index are 0,1,2,3 → dims 128,128,128,768.
        # All four get re-embedded to 768.
        self.assertEqual(post.get(768), 5 + 3)  # original 5 ST + 3 re-embedded from 128
        self.assertEqual(post.get(128, 0), 0)   # all 128s in first 4 became 768
        self.assertEqual(post.get(3072), 2)     # untouched

    # ---- error paths ------------------------------------------------------
    def test_missing_db_raises_filenotfound(self):
        with self.assertRaises(FileNotFoundError):
            mig.migrate(os.path.join(self.tmpdir, "nope.db"), apply=False)

    def test_invalid_model_hint(self):
        with self.assertRaises(ValueError):
            mig.migrate(self.db, model_hint="bogus", apply=False)

    # ---- schema fallback for legacy DBs ----------------------------------
    def test_legacy_schema_without_pk_uses_delete_insert(self):
        # Drop the table and recreate without PK on block_index.
        conn = sqlite3.connect(self.db)
        try:
            conn.execute("DROP TABLE block_embeddings")
            conn.execute("""
                CREATE TABLE block_embeddings (
                    block_index INTEGER,
                    embedding BLOB,
                    embedding_model TEXT,
                    embedding_dim INTEGER
                )
            """)
            for idx in range(10):
                arr = np.zeros(128, dtype=np.float32)
                conn.execute(
                    "INSERT INTO block_embeddings VALUES (?, ?, ?, ?)",
                    (idx, arr.tobytes(), "default", 128),
                )
            conn.commit()
        finally:
            conn.close()

        summary = mig.migrate(self.db, model_hint="simple", apply=True, do_backup=False)
        self.assertTrue(summary["verification_ok"])
        self.assertFalse(summary["block_embeddings_has_pk"])
        # Each block has exactly one embedding row (no duplicates from re-insert).
        conn = sqlite3.connect(self.db)
        try:
            rows = list(conn.execute(
                "SELECT block_index, COUNT(*) FROM block_embeddings GROUP BY block_index"
            ))
            for _, c in rows:
                self.assertEqual(c, 1)
        finally:
            conn.close()


if __name__ == "__main__":
    unittest.main()
