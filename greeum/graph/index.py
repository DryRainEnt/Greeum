"""
Lightweight graph index for memory block relationships.

Provides efficient adjacency list storage and beam search traversal
for anchor-based localized memory exploration.
"""

import heapq
from typing import Dict, List, Tuple, Set, Callable, Optional
from pathlib import Path

from .snapshot import save_graph_snapshot, load_graph_snapshot
from ..core.metrics import update_edge_count


class GraphIndex:
    """
    In-memory graph index with adjacency lists and beam search.
    
    Optimized for small-to-medium graphs with fast neighbor lookups
    and bounded traversal for memory exploration.
    """
    
    def __init__(self, theta: float = 0.35, kmax: int = 32):
        """
        Initialize graph index.
        
        Args:
            theta: Minimum edge weight threshold for pruning
            kmax: Maximum neighbors per node to store
        """
        self.theta = theta
        self.kmax = kmax
        self.adj: Dict[str, List[Tuple[str, float]]] = {}
        self._edge_count = 0
    
    def neighbors(self, u: str, k: Optional[int] = None, min_w: Optional[float] = None) -> List[Tuple[str, float]]:
        """
        Get top-k neighbors of node u, optionally filtered by minimum weight.
        
        Returns neighbors sorted by weight descending.
        """
        if u not in self.adj:
            return []
        
        neighbor_list = self.adj[u]
        
        # Apply weight filter if specified
        if min_w is not None:
            neighbor_list = [(v, w) for v, w in neighbor_list if w >= min_w]
        
        # Apply k limit (defaults to kmax if not specified)
        k_limit = k if k is not None else self.kmax
        return neighbor_list[:k_limit]
    
    def beam_search(
        self, 
        start: str, 
        is_goal: Callable[[str], bool],
        beam: int = 32,
        max_hop: int = 2
    ) -> List[str]:
        """
        Beam search from start node to find nodes satisfying goal condition.
        
        Uses priority queue to maintain top-beam nodes at each depth level.
        Returns all goal nodes found within max_hop distance.
        """
        if start not in self.adj:
            return [start] if is_goal(start) else []
        
        frontier = [(start, 1.0)]  # (node, score)
        visited: Set[str] = set()
        hits: List[str] = []
        
        for depth in range(max_hop + 1):
            if not frontier:
                break
            
            next_frontier = []
            
            for node, score in frontier:
                if node in visited:
                    continue
                    
                visited.add(node)
                
                # Check if current node satisfies goal
                if is_goal(node):
                    hits.append(node)
                
                # Expand to neighbors if not at max depth
                if depth < max_hop:
                    for neighbor, weight in self.neighbors(node, k=beam):
                        if neighbor not in visited:
                            # Combine parent score with edge weight
                            neighbor_score = score * weight
                            next_frontier.append((neighbor, neighbor_score))
            
            # Keep top-beam nodes for next iteration
            if next_frontier:
                next_frontier.sort(key=lambda x: -x[1])  # Sort by score descending
                frontier = next_frontier[:beam]
            else:
                frontier = []
        
        return hits
    
    def upsert_edges(self, u: str, neighs: List[Tuple[str, float]]) -> None:
        """
        Insert or update edges from node u to neighbors.
        
        Merges with existing neighbors and prunes by theta/kmax constraints.
        """
        if u not in self.adj:
            self.adj[u] = []
        
        # Merge new neighbors with existing ones
        existing_dict = {v: w for v, w in self.adj[u]}
        
        for v, weight in neighs:
            # Update weight (take maximum for multiple edges)
            if v in existing_dict:
                existing_dict[v] = max(existing_dict[v], weight)
            else:
                existing_dict[v] = weight
        
        # Convert back to list and filter by theta
        merged_neighbors = [
            (v, w) for v, w in existing_dict.items() 
            if w >= self.theta
        ]
        
        # Sort by weight descending and apply kmax limit
        merged_neighbors.sort(key=lambda x: -x[1])
        self.adj[u] = merged_neighbors[:self.kmax]
        
        # Update edge count estimate
        self._edge_count = sum(len(neighbors) for neighbors in self.adj.values())
        update_edge_count(self._edge_count)  # Record for metrics
    
    def add_node(self, node_id: str) -> None:
        """Add node to graph (creates empty adjacency list if not exists)."""
        if node_id not in self.adj:
            self.adj[node_id] = []
    
    def remove_node(self, node_id: str) -> None:
        """Remove node and all edges involving it."""
        if node_id in self.adj:
            del self.adj[node_id]
        
        # Remove incoming edges
        for u in list(self.adj.keys()):
            self.adj[u] = [(v, w) for v, w in self.adj[u] if v != node_id]
        
        self._update_edge_count()
    
    def get_stats(self) -> Dict[str, int]:
        """Get graph statistics."""
        return {
            "node_count": len(self.adj),
            "edge_count": self._edge_count,
            "avg_degree": self._edge_count / len(self.adj) if self.adj else 0
        }
    
    def _update_edge_count(self) -> None:
        """Recalculate edge count after modifications."""
        self._edge_count = sum(len(neighbors) for neighbors in self.adj.values())
    
    def save_snapshot(self, store_path: Path) -> None:
        """Save current graph state to snapshot file."""
        params = {
            "theta": self.theta,
            "kmax": self.kmax,
            "alpha": 0.7,  # Default bootstrap params
            "beta": 0.2,
            "gamma": 0.1
        }
        save_graph_snapshot(self.adj, params, store_path)
    
    def load_snapshot(self, store_path) -> bool:
        """Load graph state from snapshot file. Returns True if successful."""
        adj = load_graph_snapshot(store_path)
        if adj is not None:
            self.adj = adj
            self._update_edge_count()
            return True
        return False
    
    def clear(self) -> None:
        """Clear all nodes and edges."""
        self.adj.clear()
        self._edge_count = 0