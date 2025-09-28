"""Utilities for managing Greeum storage directories (backup / merge).

This module centralises common operations used by CLI and MCP tooling when
working with memory databases.  The goal is to provide a simple, safe surface
for creating backups and merging decentralised storage roots that might appear
after users switch data directories.
"""

from __future__ import annotations

import os
import shutil
import sqlite3
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence

from ..config_store import DEFAULT_DATA_DIR, GreeumConfig, load_config


SQLITE_SIDEcars = ("memory.db-wal", "memory.db-shm")


@dataclass
class StorageCandidate:
    """Detected storage directory candidates."""

    data_dir: Path
    db_path: Path
    total_blocks: int
    latest_timestamp: Optional[str]


def _iter_candidate_roots() -> Iterable[Path]:
    """Yield potential storage roots in priority order."""

    env_dir = os.getenv("GREEUM_DATA_DIR")
    if env_dir:
        yield Path(env_dir).expanduser()

    config: GreeumConfig = load_config()
    if config.data_dir:
        yield Path(config.data_dir).expanduser()

    # Current working directory variants
    cwd = Path.cwd()
    yield cwd
    yield cwd / "data"
    yield cwd / "greeum-data"
    yield cwd / "greeum-data" / "data"

    # Default global directory
    yield DEFAULT_DATA_DIR.expanduser()


def _scan_for_databases(base: Path, max_depth: int = 2) -> List[Path]:
    """Return all memory.db files found within ``base`` (depth-limited)."""

    results: List[Path] = []

    try:
        if base.is_file() and base.name == "memory.db":
            return [base]
        if not base.is_dir():
            return []
    except OSError:
        return []

    try:
        for path in base.rglob("memory.db"):
            try:
                rel_depth = len(path.parent.relative_to(base).parts)
            except ValueError:
                continue
            if rel_depth <= max_depth:
                results.append(path)
    except (OSError, RuntimeError):
        # rglob can fail on permission errors; ignore quietly
        return []

    return results


def discover_storage_candidates(extra_paths: Optional[Sequence[str]] = None) -> List[StorageCandidate]:
    """Discover available storage roots and summarise their contents."""

    seen: set[Path] = set()
    candidates: List[StorageCandidate] = []

    def _add_candidate(db_path: Path) -> None:
        db_path = db_path.expanduser().resolve()
        data_dir = db_path.parent
        if data_dir in seen:
            return
        seen.add(data_dir)

        total_blocks = 0
        latest_ts: Optional[str] = None

        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*), MAX(timestamp) FROM blocks")
            row = cursor.fetchone()
            if row:
                total_blocks = int(row[0] or 0)
                latest_ts = row[1]
            conn.close()
        except sqlite3.Error:
            # Leave totals at zero if the database is not readable yet
            total_blocks = 0
            latest_ts = None

        candidates.append(
            StorageCandidate(
                data_dir=data_dir,
                db_path=db_path,
                total_blocks=total_blocks,
                latest_timestamp=latest_ts,
            )
        )

    for root in _iter_candidate_roots():
        for db_path in _scan_for_databases(root):
            _add_candidate(db_path)

    if extra_paths:
        for raw in extra_paths:
            path = Path(raw).expanduser()
            if path.name == "memory.db" and path.exists():
                _add_candidate(path)
            else:
                for db_path in _scan_for_databases(path):
                    _add_candidate(db_path)

    return candidates


def resolve_active_storage(preferred: Optional[str] = None) -> StorageCandidate:
    """Return the preferred (or best available) storage candidate."""

    extras = [preferred] if preferred else None
    candidates = discover_storage_candidates(extras)

    if not candidates:
        raise FileNotFoundError(
            "No memory.db found. Run `greeum setup` to initialise a storage directory."
        )

    if preferred:
        preferred_path = Path(preferred).expanduser().resolve()
        for candidate in candidates:
            if preferred_path in (candidate.data_dir, candidate.db_path):
                return candidate

    # Fallback: choose candidate with the newest timestamp, otherwise the first one
    def _sort_key(item: StorageCandidate) -> tuple[int, Optional[str]]:
        return (item.total_blocks, item.latest_timestamp)

    candidates.sort(key=_sort_key, reverse=True)
    return candidates[0]


def _copy_if_exists(source: Path, destination: Path) -> Optional[Path]:
    if source.exists():
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)
        return destination
    return None


def create_backup(data_dir: Path, label: str = "manual") -> Dict[str, Any]:
    """Create a timestamped backup of the active storage files."""

    data_dir = data_dir.expanduser().resolve()

    db_path = data_dir / "memory.db"
    if not db_path.exists():
        db_path = data_dir / "data" / "memory.db"
    if not db_path.exists():
        raise FileNotFoundError(f"memory.db not found under {data_dir}")

    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    backup_dir = data_dir / "backups"
    backup_dir.mkdir(parents=True, exist_ok=True)

    backup_path = backup_dir / f"memory_{label}_{timestamp}.db"
    shutil.copy2(db_path, backup_path)

    sidecar_outputs: List[str] = []
    for sidecar_name in SQLITE_SIDEcars:
        side_src = db_path.with_name(sidecar_name)
        copied = _copy_if_exists(side_src, backup_dir / f"{sidecar_name}_{timestamp}")
        if copied:
            sidecar_outputs.append(str(copied))

    # STM anchor backup (if present)
    raw_anchor = os.getenv("GREEUM_STM_DB")
    anchor_candidates = []
    if raw_anchor:
        anchor_candidates.append(Path(raw_anchor))
    anchor_candidates.extend([
        data_dir / "stm_anchors.db",
        data_dir / "data" / "stm_anchors.db",
    ])
    for candidate in anchor_candidates:
        if candidate.exists():
            copied = _copy_if_exists(candidate, backup_dir / f"stm_anchors_{label}_{timestamp}.db")
            if copied:
                sidecar_outputs.append(str(copied))
            break

    return {
        "backup": str(backup_path),
        "sidecars": sidecar_outputs,
    }


def _tables_with_column(conn: sqlite3.Connection, column: str) -> List[str]:
    cursor = conn.cursor()
    tables = []
    for (name,) in cursor.execute("SELECT name FROM sqlite_master WHERE type='table'"):
        try:
            info = cursor.execute(f"PRAGMA table_info({name})").fetchall()
        except sqlite3.Error:
            continue
        if any(col_info[1] == column for col_info in info):
            tables.append(name)
    return tables


def merge_storage(source_db: Path, target_db: Path) -> Dict[str, int]:
    """Merge blocks from ``source_db`` into ``target_db``.

    Blocks with duplicate hashes are skipped.  New blocks are appended with
    sequential ``block_index`` values.  Associated tables that reference
    ``block_index`` are copied using the same mapping so metadata stays
    consistent.
    """

    source_db = source_db.expanduser().resolve()
    target_db = target_db.expanduser().resolve()

    if source_db == target_db:
        raise ValueError("Source and target database paths must be different")

    if not source_db.exists():
        raise FileNotFoundError(f"Source database not found: {source_db}")
    if not target_db.exists():
        raise FileNotFoundError(f"Target database not found: {target_db}")

    src_conn = sqlite3.connect(source_db)
    src_conn.row_factory = sqlite3.Row
    tgt_conn = sqlite3.connect(target_db)
    tgt_conn.row_factory = sqlite3.Row

    try:
        tgt_conn.execute("BEGIN IMMEDIATE")

        max_index_row = tgt_conn.execute("SELECT MAX(block_index) FROM blocks").fetchone()
        current_index = int(max_index_row[0]) if max_index_row and max_index_row[0] is not None else -1

        mapping: Dict[int, int] = {}
        inserted_blocks = 0

        src_cursor = src_conn.execute("SELECT * FROM blocks ORDER BY block_index")
        block_columns = [col[1] for col in src_conn.execute("PRAGMA table_info(blocks)").fetchall()]
        block_placeholder = ",".join(["?" for _ in block_columns])
        block_insert_sql = f"INSERT INTO blocks ({','.join(block_columns)}) VALUES ({block_placeholder})"

        for row in src_cursor:
            if tgt_conn.execute("SELECT 1 FROM blocks WHERE hash = ? LIMIT 1", (row["hash"],)).fetchone():
                existing = tgt_conn.execute(
                    "SELECT block_index FROM blocks WHERE hash = ? LIMIT 1",
                    (row["hash"],),
                ).fetchone()
                if existing:
                    mapping[row["block_index"]] = int(existing[0])
                continue

            current_index += 1
            mapping[row["block_index"]] = current_index

            values = [row[col] if col != "block_index" else current_index for col in block_columns]
            tgt_conn.execute(block_insert_sql, values)
            inserted_blocks += 1

        if not mapping:
            tgt_conn.commit()
            return {"blocks_inserted": 0, "tables_updated": 0}

        tables = _tables_with_column(src_conn, "block_index")
        tables = [name for name in tables if name != "blocks"]

        updated_tables = 0
        keys = list(mapping.keys())
        if not keys:
            tgt_conn.commit()
            return {"blocks_inserted": inserted_blocks, "tables_updated": 0}

        for table in tables:
            info = src_conn.execute(f"PRAGMA table_info({table})").fetchall()
            if not info:
                continue

            columns = [col[1] for col in info]
            insert_columns = [col for col, meta in zip(columns, info) if not (meta[5] == 1 and col == "id")]

            if "block_index" not in insert_columns:
                continue

            placeholders = ",".join(["?" for _ in insert_columns])
            insert_sql = f"INSERT OR IGNORE INTO {table} ({','.join(insert_columns)}) VALUES ({placeholders})"

            chunk_size = 500
            for offset in range(0, len(keys), chunk_size):
                chunk = keys[offset : offset + chunk_size]
                select_sql = (
                    f"SELECT {','.join(insert_columns)} FROM {table} "
                    f"WHERE block_index IN ({','.join('?' for _ in chunk)})"
                )
                rows = src_conn.execute(select_sql, tuple(chunk))

                for row in rows:
                    values = []
                    for col in insert_columns:
                        if col == "block_index":
                            values.append(mapping[row["block_index"]])
                        else:
                            values.append(row[col])
                    tgt_conn.execute(insert_sql, values)

            updated_tables += 1

        tgt_conn.commit()

        return {
            "blocks_inserted": inserted_blocks,
            "tables_updated": updated_tables,
        }

    finally:
        src_conn.close()
        tgt_conn.close()


__all__ = [
    "StorageCandidate",
    "discover_storage_candidates",
    "resolve_active_storage",
    "create_backup",
    "merge_storage",
]
