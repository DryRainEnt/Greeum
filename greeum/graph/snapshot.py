"""
Graph snapshot I/O for persistent graph index storage.
"""

import json
from pathlib import Path
from typing import Dict, List, Tuple, Optional, TypedDict
from datetime import datetime


class GraphSnapshot(TypedDict):
    """Graph index snapshot format."""
    version: int
    nodes: List[str]
    edges: List[Dict[str, any]]  # [{"u": "blk_a", "v": "blk_b", "w": 0.62, "src": ["sim", "time"]}]
    built_at: int
    params: Dict[str, float]  # {"theta": 0.35, "kmax": 32, "alpha": 0.7, "beta": 0.2, "gamma": 0.1}


def save_graph_snapshot(
    adjacency: Dict[str, List[Tuple[str, float]]],
    params: Dict[str, float],
    store_path: Path
) -> None:
    """Save graph adjacency to JSONL snapshot."""
    store_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Extract all nodes
    nodes = set(adjacency.keys())
    for neighbors in adjacency.values():
        for neighbor_id, _ in neighbors:
            nodes.add(neighbor_id)
    
    # Convert adjacency to edge list
    edges = []
    for u, neighbors in adjacency.items():
        for v, weight in neighbors:
            edges.append({
                "u": u,
                "v": v, 
                "w": weight,
                "src": ["generated"]  # Source will be updated during bootstrap
            })
    
    snapshot: GraphSnapshot = {
        "version": 1,
        "nodes": sorted(nodes),
        "edges": edges,
        "built_at": int(datetime.now().timestamp()),
        "params": params
    }
    
    # Save as JSONL for potential streaming processing
    with open(store_path, 'w', encoding='utf-8') as f:
        json.dump(snapshot, f, indent=2, ensure_ascii=False)


def load_graph_snapshot(store_path) -> Optional[Dict[str, List[Tuple[str, float]]]]:
    """Load graph adjacency from snapshot file."""
    from pathlib import Path
    path_obj = Path(store_path)
    if not path_obj.exists():
        return None
    
    try:
        with open(store_path, 'r', encoding='utf-8') as f:
            snapshot = json.load(f)
        
        # Version compatibility check
        if snapshot.get('version', 1) > 1:
            raise ValueError(f"Unsupported graph snapshot version: {snapshot['version']}")
        
        # Reconstruct adjacency list
        adjacency: Dict[str, List[Tuple[str, float]]] = {}
        
        for edge in snapshot.get('edges', []):
            u, v, weight = edge['u'], edge['v'], edge['w']
            
            if u not in adjacency:
                adjacency[u] = []
            
            adjacency[u].append((v, weight))
        
        # Sort neighbors by weight (descending)
        for neighbors in adjacency.values():
            neighbors.sort(key=lambda x: -x[1])
        
        return adjacency
    
    except (json.JSONDecodeError, KeyError, ValueError) as e:
        print(f"Warning: Failed to load graph snapshot: {e}")
        return None


def get_snapshot_info(store_path: Path) -> Optional[Dict]:
    """Get metadata about graph snapshot without loading full adjacency."""
    if not store_path.exists():
        return None
    
    try:
        with open(store_path, 'r', encoding='utf-8') as f:
            snapshot = json.load(f)
        
        return {
            "version": snapshot.get("version", 1),
            "node_count": len(snapshot.get("nodes", [])),
            "edge_count": len(snapshot.get("edges", [])),
            "built_at": snapshot.get("built_at", 0),
            "params": snapshot.get("params", {})
        }
    
    except (json.JSONDecodeError, KeyError) as e:
        return {"error": str(e)}