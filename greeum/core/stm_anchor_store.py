"""Persistent STM anchor storage for 3-slot context pointers."""

from __future__ import annotations

import json
import os
import sqlite3
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional

def _default_anchor_path() -> Path:
    base = os.environ.get("GREEUM_STM_DB")
    if base:
        return Path(base)

    data_dir = os.environ.get("GREEUM_DATA_DIR")
    if data_dir:
        return Path(data_dir).expanduser() / "stm_anchors.db"

    return Path.home() / ".greeum" / "stm_anchors.db"

@dataclass
class AnchorSlot:
    slot_name: str
    anchor_block: Optional[str]
    topic_vec: Optional[list]
    summary: str
    last_seen: float
    hysteresis: float


class STMAnchorStore:
    """Lightweight anchor store backed by a dedicated SQLite database."""

    def __init__(self, path: Optional[Path] = None):
        if path is None:
            path = _default_anchor_path()
        self._path = path
        self._lock = threading.Lock()
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(self._path, check_same_thread=False)
        self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS slots (
                slot_name TEXT PRIMARY KEY,
                anchor_block TEXT,
                topic_vec TEXT,
                summary TEXT,
                last_seen REAL,
                hysteresis REAL
            )
            """
        )
        # Ensure default slots exist
        for slot in ("A", "B", "C"):
            self._conn.execute(
                "INSERT OR IGNORE INTO slots(slot_name, anchor_block, topic_vec, summary, last_seen, hysteresis)"
                " VALUES(?, NULL, NULL, '', 0, 0)",
                (slot,),
            )
        self._conn.commit()

    def get_slots(self) -> Dict[str, AnchorSlot]:
        with self._lock:
            cursor = self._conn.execute(
                "SELECT slot_name, anchor_block, topic_vec, summary, last_seen, hysteresis FROM slots"
            )
            slots: Dict[str, AnchorSlot] = {}
            for row in cursor.fetchall():
                slot_name, anchor_block, topic_vec, summary, last_seen, hysteresis = row
                vec = json.loads(topic_vec) if topic_vec else None
                slots[slot_name] = AnchorSlot(
                    slot_name=slot_name,
                    anchor_block=anchor_block,
                    topic_vec=vec,
                    summary=summary or "",
                    last_seen=last_seen or 0.0,
                    hysteresis=hysteresis or 0.0,
                )
            return slots

    def upsert_slot(
        self,
        slot_name: str,
        anchor_block: Optional[str],
        topic_vec: Optional[list],
        summary: str,
        last_seen: Optional[float] = None,
        hysteresis: Optional[float] = None,
    ) -> None:
        payload = json.dumps(topic_vec) if topic_vec is not None else None
        now = last_seen if last_seen is not None else time.time()
        hyst = hysteresis if hysteresis is not None else 0.0
        with self._lock:
            self._conn.execute(
                """
                INSERT INTO slots(slot_name, anchor_block, topic_vec, summary, last_seen, hysteresis)
                VALUES(?, ?, ?, ?, ?, ?)
                ON CONFLICT(slot_name) DO UPDATE SET
                    anchor_block=excluded.anchor_block,
                    topic_vec=excluded.topic_vec,
                    summary=excluded.summary,
                    last_seen=excluded.last_seen,
                    hysteresis=excluded.hysteresis
                """,
                (slot_name, anchor_block, payload, summary or "", now, hyst),
            )
            self._conn.commit()

    def reset_slot(self, slot_name: str) -> None:
        with self._lock:
            self._conn.execute(
                "UPDATE slots SET anchor_block=NULL, topic_vec=NULL, summary='', last_seen=0, hysteresis=0 WHERE slot_name=?",
                (slot_name,),
            )
            self._conn.commit()

    def close(self) -> None:
        with self._lock:
            self._conn.close()


_singleton: Optional[STMAnchorStore] = None
_singleton_lock = threading.Lock()


def get_anchor_store() -> STMAnchorStore:
    global _singleton
    if _singleton is None:
        with _singleton_lock:
            if _singleton is None:
                _singleton = STMAnchorStore()
    return _singleton
