#!/usr/bin/env python3
"""Re-embed all blocks in a Greeum DB with a target embedding model.

Phase 1C (v5.4): fixes the live-DB symptom where ``block_embeddings`` has
mixed dimensions (128 hash / 768 ST-padded / 3072 OpenAI) accumulated across
model changes, which makes vector search across the corpus meaningless.

The script defaults to **dry-run** and **automatic backup-before-write** so
it is safe to run against a live DB once the maintainer has approved the
target model + downtime window.

Usage:

    # Inspect what would change (no writes):
    python scripts/migrate_embeddings.py --db ~/.greeum/memory.db

    # Apply with default model (registry default = ST if available, else m2v):
    python scripts/migrate_embeddings.py --db ~/.greeum/memory.db --apply

    # Force a specific model:
    python scripts/migrate_embeddings.py --db ... --model model2vec --apply
    python scripts/migrate_embeddings.py --db ... --model st --apply

    # Test on first 10 blocks only:
    python scripts/migrate_embeddings.py --db ... --limit 10 --apply

Exit codes:
    0  success (whether dry-run or apply)
    1  partial failure / verification mismatch
    2  invalid arguments / unable to start
"""
from __future__ import annotations

import argparse
import json
import logging
import os
import shutil
import sqlite3
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

# Allow running directly from the repo without `pip install -e .` — if an older
# `greeum` is system-installed (e.g. ~/.local/lib/...), it would otherwise shadow
# the repo. Prepend the repo root to sys.path when it looks like a Greeum repo.
_REPO_ROOT = Path(__file__).parent.parent.resolve()
if (_REPO_ROOT / "greeum" / "__init__.py").exists():
    sys.path.insert(0, str(_REPO_ROOT))

logger = logging.getLogger("migrate_embeddings")

# ---------------------------------------------------------------------------
# Embedding model loading


def _load_target_model(name_hint: str):
    """Load the target embedding model. ``name_hint`` ∈ {auto, st, model2vec, simple}.

    Returns the same EmbeddingModel interface Greeum uses: ``.encode(text) ->
    list[float]``, ``.get_model_name()``, ``.get_dimension()``.
    """
    from greeum.embedding_models import (
        SentenceTransformerModel,
        Model2VecEmbedding,
        SimpleEmbeddingModel,
        EmbeddingRegistry,
    )

    if name_hint == "auto":
        reg = EmbeddingRegistry()
        default_name = reg.default_model
        model = reg.get_model(default_name) if hasattr(reg, "get_model") else reg.models.get(default_name)
        if model is None:
            raise RuntimeError("registry default model not loaded — check ST/Model2Vec install")
        return model
    if name_hint in ("st", "sentence-transformer"):
        return SentenceTransformerModel()
    if name_hint in ("m2v", "model2vec"):
        return Model2VecEmbedding()
    if name_hint == "simple":
        return SimpleEmbeddingModel(dimension=768)
    raise ValueError(f"unknown --model: {name_hint}")


# ---------------------------------------------------------------------------
# DB helpers (read-only via uri=ro for the dry-run pass)


def _open_db(path: str, *, writable: bool) -> sqlite3.Connection:
    if writable:
        conn = sqlite3.connect(path, timeout=10)
    else:
        conn = sqlite3.connect(f"file:{path}?mode=ro", uri=True, timeout=10)
    conn.row_factory = sqlite3.Row
    return conn


def _backup_db(path: str) -> str:
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    bak = f"{path}.bak_pre_embed_migration_{ts}"
    # Use the SQLite backup API to be safe with WAL/concurrent writes.
    src = sqlite3.connect(path, timeout=10)
    try:
        dst = sqlite3.connect(bak, timeout=10)
        with dst:
            src.backup(dst)
        dst.close()
    finally:
        src.close()
    # Sanity: dest exists and non-empty.
    size = Path(bak).stat().st_size
    if size <= 0:
        raise RuntimeError(f"backup verification failed (size=0): {bak}")
    return bak


def _block_iter(conn: sqlite3.Connection, *, limit: Optional[int]) -> List[Tuple[int, str]]:
    cur = conn.cursor()
    sql = "SELECT block_index, context FROM blocks WHERE context IS NOT NULL AND context != '' ORDER BY block_index"
    if limit:
        sql += f" LIMIT {int(limit)}"
    return [(int(r["block_index"]), r["context"]) for r in cur.execute(sql)]


def _existing_embeddings(conn: sqlite3.Connection) -> Dict[int, Tuple[str, int]]:
    cur = conn.cursor()
    return {
        int(r["block_index"]): (str(r["embedding_model"] or ""), int(r["embedding_dim"] or 0))
        for r in cur.execute("SELECT block_index, embedding_model, embedding_dim FROM block_embeddings")
    }


# ---------------------------------------------------------------------------
# Migration core


def _write_embedding(conn: sqlite3.Connection, block_index: int, vec: np.ndarray,
                     model_name: str) -> None:
    """INSERT OR REPLACE the embedding row for ``block_index``."""
    arr = np.asarray(vec, dtype=np.float32)
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO block_embeddings (block_index, embedding, embedding_model, embedding_dim)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(block_index) DO UPDATE SET
            embedding=excluded.embedding,
            embedding_model=excluded.embedding_model,
            embedding_dim=excluded.embedding_dim
        """,
        (block_index, arr.tobytes(), model_name, int(arr.shape[-1])),
    )


def _block_embeddings_schema_has_pk(conn: sqlite3.Connection) -> bool:
    """Some old schemas don't have a PRIMARY KEY on block_index. We need it
    for ON CONFLICT(block_index). Older rows may have duplicates; we handle
    them by DELETE-then-INSERT instead.
    """
    cur = conn.cursor()
    info = cur.execute("PRAGMA table_info(block_embeddings)").fetchall()
    return any(int(c["pk"] or 0) > 0 and c["name"] == "block_index" for c in info)


def _write_embedding_safe(conn: sqlite3.Connection, block_index: int, vec: np.ndarray,
                          model_name: str, has_pk: bool) -> None:
    if has_pk:
        _write_embedding(conn, block_index, vec, model_name)
        return
    # Fallback: DELETE + INSERT
    arr = np.asarray(vec, dtype=np.float32)
    cur = conn.cursor()
    cur.execute("DELETE FROM block_embeddings WHERE block_index = ?", (block_index,))
    cur.execute(
        "INSERT INTO block_embeddings (block_index, embedding, embedding_model, embedding_dim)"
        " VALUES (?, ?, ?, ?)",
        (block_index, arr.tobytes(), model_name, int(arr.shape[-1])),
    )


def migrate(
    db_path: str,
    model_hint: str = "auto",
    *,
    apply: bool = False,
    do_backup: bool = True,
    batch_size: int = 50,
    limit: Optional[int] = None,
) -> Dict[str, Any]:
    """Re-embed all blocks. Returns a summary dict.

    ``apply=False`` (default) is dry-run: opens DB read-only, computes the
    plan, returns the diff without writing. ``apply=True`` opens a writable
    handle, snapshots the DB (unless ``do_backup=False``), and re-embeds in
    batches inside transactions.
    """
    db_path = str(Path(db_path).expanduser())
    if not Path(db_path).exists():
        raise FileNotFoundError(db_path)

    summary: Dict[str, Any] = {
        "db_path": db_path,
        "model_hint": model_hint,
        "apply": apply,
        "started_at": datetime.now().isoformat(timespec="seconds"),
    }

    # Plan pass (always read-only first).
    plan_conn = _open_db(db_path, writable=False)
    try:
        blocks = _block_iter(plan_conn, limit=limit)
        existing = _existing_embeddings(plan_conn)
    finally:
        plan_conn.close()

    summary["total_blocks"] = len(blocks)
    summary["existing_embeddings"] = len(existing)
    summary["existing_dim_distribution"] = _count_dims(existing)

    # Load model.
    logger.info("Loading target embedding model: %s", model_hint)
    model = _load_target_model(model_hint)
    target_name = model.get_model_name()
    # Trigger dimension probe via a 1-token encode (some impls are lazy).
    probe = model.encode("dim probe")
    target_dim = len(probe)
    summary["target_model"] = target_name
    summary["target_dim"] = target_dim

    # Build the work list (skip blocks already at target model+dim).
    todo: List[Tuple[int, str]] = []
    skipped = 0
    for idx, ctx in blocks:
        cur = existing.get(idx)
        if cur and cur[0] == target_name and cur[1] == target_dim:
            skipped += 1
        else:
            todo.append((idx, ctx))
    summary["skipped_already_current"] = skipped
    summary["to_migrate"] = len(todo)

    if not apply:
        summary["mode"] = "dry-run"
        summary["finished_at"] = datetime.now().isoformat(timespec="seconds")
        return summary

    # Apply pass.
    summary["mode"] = "apply"

    if do_backup:
        logger.info("Backing up DB before migration ...")
        bak = _backup_db(db_path)
        summary["backup"] = bak
        logger.info("Backup: %s", bak)
    else:
        summary["backup"] = None

    write_conn = _open_db(db_path, writable=True)
    try:
        has_pk = _block_embeddings_schema_has_pk(write_conn)
        summary["block_embeddings_has_pk"] = has_pk

        t0 = time.time()
        done = 0
        for i in range(0, len(todo), batch_size):
            batch = todo[i:i + batch_size]
            with write_conn:  # transactional
                for idx, ctx in batch:
                    vec = np.asarray(model.encode(ctx), dtype=np.float32)
                    _write_embedding_safe(write_conn, idx, vec, target_name, has_pk)
            done += len(batch)
            if done % (batch_size * 4) == 0 or done == len(todo):
                logger.info("Re-embedded %d/%d (%.1f%%)", done, len(todo),
                            100.0 * done / max(1, len(todo)))

        summary["elapsed_s"] = round(time.time() - t0, 2)

        # Verification.
        v = _existing_embeddings(write_conn)
        dims = _count_dims(v)
        summary["post_dim_distribution"] = dims
        summary["post_at_target"] = sum(1 for k, (m, d) in v.items()
                                         if m == target_name and d == target_dim)
        summary["verification_ok"] = (
            summary["post_at_target"] == summary["total_blocks"]
            and len(dims) == 1
            and target_dim in dims
        )
    finally:
        write_conn.close()

    summary["finished_at"] = datetime.now().isoformat(timespec="seconds")
    return summary


def _count_dims(existing: Dict[int, Tuple[str, int]]) -> Dict[int, int]:
    out: Dict[int, int] = {}
    for _model, dim in existing.values():
        out[dim] = out.get(dim, 0) + 1
    return out


# ---------------------------------------------------------------------------
# CLI


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Re-embed all blocks in a Greeum DB with a target embedding model.",
    )
    p.add_argument("--db", default=os.environ.get("GREEUM_DATA_DIR_DB"),
                   help="Path to memory.db. Defaults to $GREEUM_DATA_DIR/memory.db, "
                        "else ~/.greeum/memory.db")
    p.add_argument("--model", default="auto",
                   choices=["auto", "st", "sentence-transformer", "m2v", "model2vec", "simple"],
                   help="Target embedding model. 'auto' uses the registry default.")
    p.add_argument("--apply", action="store_true",
                   help="Write changes. Default is dry-run.")
    p.add_argument("--no-backup", action="store_true",
                   help="Skip pre-write backup (TESTING ONLY — never on live data).")
    p.add_argument("--batch-size", type=int, default=50)
    p.add_argument("--limit", type=int, default=None,
                   help="Process at most N blocks (testing).")
    p.add_argument("--json", action="store_true", help="Emit summary as JSON.")
    p.add_argument("--verbose", action="store_true")
    args = p.parse_args()

    # Resolve --db default
    if not args.db:
        env_dir = os.environ.get("GREEUM_DATA_DIR")
        if env_dir:
            args.db = str(Path(env_dir) / "memory.db")
        else:
            args.db = str(Path.home() / ".greeum" / "memory.db")
    return args


def main() -> int:
    args = _parse_args()
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    if not Path(args.db).exists():
        logger.error("DB not found: %s", args.db)
        return 2
    if args.apply and args.no_backup:
        logger.warning("--no-backup was passed alongside --apply. This is unsafe on live data.")

    try:
        summary = migrate(
            db_path=args.db,
            model_hint=args.model,
            apply=args.apply,
            do_backup=not args.no_backup,
            batch_size=args.batch_size,
            limit=args.limit,
        )
    except Exception as e:
        logger.exception("Migration failed: %s", e)
        return 1

    if args.json:
        print(json.dumps(summary, ensure_ascii=False, indent=2))
    else:
        _print_summary(summary)

    if summary.get("mode") == "apply" and not summary.get("verification_ok", False):
        return 1
    return 0


def _print_summary(s: Dict[str, Any]) -> None:
    print(f"\n=== migrate_embeddings summary ({s['mode']}) ===")
    print(f"  db:                 {s['db_path']}")
    print(f"  target model:       {s.get('target_model')}")
    print(f"  target dim:         {s.get('target_dim')}")
    print(f"  blocks total:       {s.get('total_blocks')}")
    print(f"  existing embeddings:{s.get('existing_embeddings')}")
    print(f"  existing dims:      {s.get('existing_dim_distribution')}")
    print(f"  already at target:  {s.get('skipped_already_current')}")
    print(f"  to migrate:         {s.get('to_migrate')}")
    if s["mode"] == "apply":
        print(f"  backup:             {s.get('backup')}")
        print(f"  elapsed:            {s.get('elapsed_s')}s")
        print(f"  post dims:          {s.get('post_dim_distribution')}")
        print(f"  at target after:    {s.get('post_at_target')}")
        print(f"  verification:       {'OK' if s.get('verification_ok') else 'FAIL'}")


if __name__ == "__main__":
    sys.exit(main())
