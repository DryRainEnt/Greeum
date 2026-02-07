"""
Backup upload/export endpoints for remote memory sync.

v5.2.0: Enables `greeum backup push` and `greeum backup pull`.
"""

import logging
import tempfile
import json
from pathlib import Path
from typing import Dict, Any

from fastapi import APIRouter, HTTPException, Depends, Body
from fastapi.responses import JSONResponse

from ..services.memory_service import MemoryService, get_memory_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/backup", tags=["backup"])


@router.post("/upload")
async def upload_backup(
    payload: Dict[str, Any] = Body(...),
    service: MemoryService = Depends(get_memory_service),
):
    """
    Receive a backup JSON and restore memories into this server.

    Expects the standard Greeum backup format with hierarchical_data.
    Supports merge mode (skip duplicates by default).
    """
    service._ensure_initialized()

    # Disable InsightJudge for backup restore (already validated content)
    original_filter = service.use_insight_filter
    service.use_insight_filter = False

    try:
        hierarchical = payload.get("hierarchical_data", {})
        metadata = payload.get("metadata", {})
        merge = payload.get("merge", True)

        restored = 0
        skipped = 0
        errors = 0

        all_memories = (
            hierarchical.get("ltm", [])
            + hierarchical.get("stm", [])
            + hierarchical.get("working_memory", [])
        )

        for mem in all_memories:
            content = mem.get("content", "")
            if not content:
                skipped += 1
                continue

            try:
                result = await service.add_memory(
                    content=content,
                    importance=mem.get("importance", 0.5),
                    tags=mem.get("tags", []),
                )
                if result.get("success"):
                    restored += 1
                else:
                    skipped += 1
            except Exception as e:
                logger.warning(f"Failed to restore memory: {e}")
                errors += 1

        return {
            "success": True,
            "total": len(all_memories),
            "restored": restored,
            "skipped": skipped,
            "errors": errors,
            "source_version": metadata.get("export_version", "unknown"),
        }

    except Exception as e:
        logger.error(f"Backup upload failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        service.use_insight_filter = original_filter


@router.get("/export")
async def export_backup(
    service: MemoryService = Depends(get_memory_service),
):
    """
    Export all server memories as a backup JSON.

    Directly queries the database for maximum compatibility.
    """
    service._ensure_initialized()

    try:
        from datetime import datetime

        blocks = []
        db = service._db_manager

        # Query all blocks from database
        if hasattr(db, "run_serialized"):
            # ThreadSafeDatabaseManager
            def _fetch_all():
                cursor = db.conn.cursor()
                cursor.execute(
                    "SELECT block_index, context, timestamp, importance, slot "
                    "FROM blocks ORDER BY block_index"
                )
                return cursor.fetchall()
            raw_rows = db.run_serialized(_fetch_all)
        elif hasattr(db, "conn"):
            cursor = db.conn.cursor()
            cursor.execute(
                "SELECT block_index, context, timestamp, importance, tags "
                "FROM blocks ORDER BY block_index"
            )
            raw_rows = cursor.fetchall()
        else:
            raw_rows = []

        for r in raw_rows:
            blocks.append({
                "id": str(r[0]),
                "content": r[1] or "",
                "timestamp": r[2] or "",
                "importance": r[3] if r[3] is not None else 0.5,
                "layer": "ltm",
                "keywords": [],
                "tags": [],
                "metadata": {"block_index": r[0], "slot": r[4]},
            })

        return JSONResponse(content={
            "metadata": {
                "export_version": "5.2.0",
                "timestamp": datetime.utcnow().isoformat(),
                "total_memories": len(blocks),
                "source_system": "greeum",
            },
            "hierarchical_data": {
                "working_memory": [],
                "stm": [],
                "ltm": blocks,
            },
            "system_metadata": {},
        })

    except Exception as e:
        logger.error(f"Backup export failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
