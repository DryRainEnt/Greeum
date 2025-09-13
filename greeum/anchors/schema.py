"""
Anchor state schema definitions for versioned I/O.
"""

from typing import TypedDict, Literal, List, Optional
import json
from pathlib import Path
from datetime import datetime


class AnchorState(TypedDict):
    """Single anchor slot state."""
    slot: Literal['A', 'B', 'C']
    anchor_block_id: str
    topic_vec: List[float]
    summary: str
    last_used_ts: int
    hop_budget: int
    pinned: bool


class AnchorsSnapshot(TypedDict):
    """Complete anchors system snapshot."""
    version: int
    slots: List[AnchorState]
    updated_at: int


def save_anchors_snapshot(snapshot: AnchorsSnapshot, store_path: Path) -> None:
    """Save anchors snapshot to disk with versioning."""
    store_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(store_path, 'w', encoding='utf-8') as f:
        json.dump(snapshot, f, indent=2, ensure_ascii=False)


def load_anchors_snapshot(store_path: Path) -> Optional[AnchorsSnapshot]:
    """Load anchors snapshot from disk."""
    if not store_path.exists():
        return None
        
    try:
        with open(store_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Version compatibility check
        version = data.get('version', 1)
        if isinstance(version, str):
            version = float(version) if '.' in version else int(version)
        if version > 1:
            raise ValueError(f"Unsupported anchors snapshot version: {data['version']}")
            
        return data
    except (json.JSONDecodeError, ValueError) as e:
        # Log warning and return None for corrupted data
        print(f"Warning: Failed to load anchors snapshot: {e}")
        return None


def create_empty_snapshot() -> AnchorsSnapshot:
    """Create initial empty anchors snapshot."""
    now_ts = int(datetime.now().timestamp())
    
    return {
        "version": 1,
        "slots": [
            {
                "slot": "A",
                "anchor_block_id": "",
                "topic_vec": [],
                "summary": "Empty slot A",
                "last_used_ts": now_ts,
                "hop_budget": 2,
                "pinned": False
            },
            {
                "slot": "B", 
                "anchor_block_id": "",
                "topic_vec": [],
                "summary": "Empty slot B",
                "last_used_ts": now_ts,
                "hop_budget": 2,
                "pinned": False
            },
            {
                "slot": "C",
                "anchor_block_id": "",
                "topic_vec": [],
                "summary": "Empty slot C", 
                "last_used_ts": now_ts,
                "hop_budget": 2,
                "pinned": False
            }
        ],
        "updated_at": now_ts
    }