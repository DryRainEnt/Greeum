"""
Near-anchor write API for Greeum Anchorized Memory (M2 Implementation)

Implements write functionality that inserts new blocks near anchor neighborhoods
and manages graph edge updates.
"""

from typing import Optional, Dict, Any, List, Tuple
import time
import logging
import numpy as np
from pathlib import Path

from ..core.block_manager import BlockManager
from ..core.database_manager import DatabaseManager
from ..embedding_models import get_embedding
from ..anchors import AnchorManager
from ..graph import GraphIndex

logger = logging.getLogger(__name__)


class AnchorBasedWriter:
    """Writer that places new blocks near anchor neighborhoods."""
    
    def __init__(self, db_manager: Optional[DatabaseManager] = None, 
                 anchor_path: Optional[Path] = None, 
                 graph_path: Optional[Path] = None):
        self.db_manager = db_manager or DatabaseManager()
        self.block_manager = BlockManager(self.db_manager)
        
        # Allow custom paths for testing
        self.anchor_path = anchor_path or Path("data/anchors.json")
        self.graph_path = graph_path or Path("data/graph_snapshot.jsonl")
        
        # Track metrics
        self.anchor_moves_count = 0
        self.edges_added_count = 0
        self.write_start_time = time.time()
    
    def write(self, text: str, *, slot: Optional[str] = None, 
              policy: Optional[Dict[str, Any]] = None, 
              keywords: Optional[List[str]] = None,
              tags: Optional[List[str]] = None,
              importance: float = 0.5) -> str:
        """
        Write new memory block near anchor neighborhood.
        
        Args:
            text: Content to write
            slot: Target anchor slot (A/B/C), auto-selected if None
            policy: Write policy configuration (link_k, min_w, etc.)
            keywords: Optional keywords list
            tags: Optional tags list
            importance: Block importance score
            
        Returns:
            str: Block ID of the newly created block
        """
        start_time = time.perf_counter()
        
        # Process input and generate embedding
        vec_new = get_embedding(text)
        
        # Set default policy
        if policy is None:
            policy = {"link_k": 8, "min_w": 0.35, "max_neighbors": 32}
        
        link_k = policy.get("link_k", 8)
        min_w = policy.get("min_w", 0.35)
        max_neighbors = policy.get("max_neighbors", 32)
        
        try:
            # Load anchor and graph systems using configured paths
            anchor_manager = None
            graph_index = None
            
            if self.anchor_path.exists():
                try:
                    anchor_manager = AnchorManager(self.anchor_path)
                    
                    # Only load graph if it exists
                    if self.graph_path.exists():
                        graph_index = GraphIndex()
                        if not graph_index.load_snapshot(self.graph_path):
                            logger.warning("Failed to load graph snapshot")
                            graph_index = None
                    else:
                        # Create new graph index for testing
                        graph_index = GraphIndex()
                        
                except Exception as e:
                    logger.warning(f"Failed to load anchor/graph system: {e}")
                    anchor_manager = None
                    graph_index = None
            
            # Select active slot
            selected_slot = slot
            if anchor_manager and not selected_slot:
                selected_slot = anchor_manager.select_active_slot(np.array(vec_new))
            
            # Find target neighborhood for insertion
            target_candidates = []
            
            if anchor_manager and graph_index and selected_slot:
                try:
                    slot_info = anchor_manager.get_slot_info(selected_slot)
                    if slot_info and slot_info['anchor_block_id']:
                        anchor_block_id = slot_info['anchor_block_id']
                        
                        # Get anchor neighborhood
                        neighbors = graph_index.neighbors(anchor_block_id, k=max_neighbors, min_w=min_w)
                        
                        if neighbors:
                            # Find best neighbor by similarity to new content
                            best_neighbor = self._find_best_neighbor(vec_new, neighbors)
                            target_candidates = [best_neighbor] + neighbors[:link_k-1]
                        else:
                            # Use anchor itself as target
                            target_candidates = [(anchor_block_id, 1.0)]
                            
                except Exception as e:
                    logger.warning(f"Failed to find anchor neighborhood: {e}")
            
            # Create new block in LTM
            block = self.block_manager.add_block(
                context=text,
                keywords=keywords or [],
                tags=tags or [],
                embedding=vec_new,
                importance=importance
            )
            
            if not block:
                raise RuntimeError("Failed to create new memory block")
                
            new_block_id = str(block['block_index'])
            
            # Update graph edges if available
            edge_weights = []
            if graph_index and target_candidates:
                try:
                    # Create edges to target neighborhood
                    for target_id, base_weight in target_candidates:
                        # Calculate edge weight based on content similarity
                        edge_weight = self._calculate_edge_weight(vec_new, target_id, base_weight)
                        edge_weights.append((target_id, edge_weight))
                    
                    # Add edges to graph
                    graph_index.upsert_edges(new_block_id, edge_weights)
                    self.edges_added_count += len(edge_weights)
                    
                    # Save updated graph
                    graph_index.save_snapshot(self.graph_path)
                    
                    logger.debug(f"Added {len(edge_weights)} edges for new block {new_block_id}")
                    
                except Exception as e:
                    logger.warning(f"Failed to update graph edges: {e}")
            
            # M2: Update LTM block links cache
            if edge_weights:
                try:
                    # Convert edge weights to neighbor cache format
                    neighbors_cache = [
                        {"id": f"blk_{target_id}", "w": round(weight, 3)} 
                        for target_id, weight in edge_weights
                    ]
                    
                    # Update block's neighbor links cache
                    success = self.block_manager.update_block_links(int(new_block_id), neighbors_cache)
                    if success:
                        logger.debug(f"Updated LTM links cache for block {new_block_id}")
                    
                except Exception as e:
                    logger.warning(f"Failed to update LTM links cache: {e}")
            
            # Update anchor position if applicable
            if anchor_manager and selected_slot:
                try:
                    slot_info = anchor_manager.get_slot_info(selected_slot)
                    if slot_info and not slot_info['pinned']:
                        # Move anchor to new block (it represents latest topic)
                        anchor_manager.move_anchor(selected_slot, new_block_id, np.array(vec_new))
                        self.anchor_moves_count += 1
                        
                        logger.debug(f"Moved anchor {selected_slot} to new block {new_block_id}")
                        
                except Exception as e:
                    logger.warning(f"Failed to update anchor: {e}")
            
            write_time = time.perf_counter() - start_time
            logger.info(f"Write completed: block_id={new_block_id}, slot={selected_slot}, time={write_time:.3f}s")
            
            return new_block_id
            
        except Exception as e:
            logger.error(f"Write operation failed: {e}")
            raise
    
    def _find_best_neighbor(self, query_vec: List[float], neighbors: List[Tuple[str, float]]) -> Tuple[str, float]:
        """Find neighbor with highest similarity to query vector."""
        best_neighbor = neighbors[0]  # Default to first
        best_similarity = 0.0
        
        query_array = np.array(query_vec)
        
        for neighbor_id, base_weight in neighbors:
            try:
                # Get neighbor block data
                neighbor_data = self.db_manager.get_block_by_index(int(neighbor_id))
                if neighbor_data and 'embedding' in neighbor_data:
                    neighbor_vec = np.array(neighbor_data['embedding'])
                    
                    # Calculate cosine similarity
                    similarity = np.dot(query_array, neighbor_vec) / (
                        np.linalg.norm(query_array) * np.linalg.norm(neighbor_vec)
                    )
                    
                    if similarity > best_similarity:
                        best_similarity = similarity
                        best_neighbor = (neighbor_id, base_weight)
                        
            except Exception as e:
                logger.debug(f"Error calculating similarity for neighbor {neighbor_id}: {e}")
                continue
        
        return best_neighbor
    
    def _calculate_edge_weight(self, query_vec: List[float], target_id: str, base_weight: float) -> float:
        """Calculate edge weight based on content similarity."""
        try:
            # Get target block data
            target_data = self.db_manager.get_block_by_index(int(target_id))
            if not target_data or 'embedding' not in target_data:
                return base_weight * 0.5  # Fallback weight
            
            # Calculate similarity
            query_array = np.array(query_vec)
            target_array = np.array(target_data['embedding'])
            
            similarity = np.dot(query_array, target_array) / (
                np.linalg.norm(query_array) * np.linalg.norm(target_array)
            )
            
            # Combine base weight with similarity
            final_weight = base_weight * 0.7 + similarity * 0.3
            return max(0.1, min(1.0, final_weight))  # Clamp to [0.1, 1.0]
            
        except Exception as e:
            logger.debug(f"Error calculating edge weight for {target_id}: {e}")
            return base_weight * 0.5
    
    def get_metrics(self) -> Dict[str, float]:
        """Get write operation metrics."""
        elapsed_minutes = (time.time() - self.write_start_time) / 60.0
        
        return {
            "anchor_moves_per_min": self.anchor_moves_count / max(0.01, elapsed_minutes),
            "edge_growth_rate": self.edges_added_count / max(0.01, elapsed_minutes),
            "total_anchor_moves": self.anchor_moves_count,
            "total_edges_added": self.edges_added_count,
            "elapsed_minutes": elapsed_minutes
        }


# Global writer instance for API endpoints
_writer_instance = None

def get_writer() -> AnchorBasedWriter:
    """Get global writer instance."""
    global _writer_instance
    if _writer_instance is None:
        _writer_instance = AnchorBasedWriter()
    return _writer_instance


# Main API function
def write(text: str, *, slot: Optional[str] = None, 
          policy: Optional[Dict[str, Any]] = None,
          keywords: Optional[List[str]] = None,
          tags: Optional[List[str]] = None, 
          importance: float = 0.5) -> str:
    """
    Write new memory block with near-anchor placement.
    
    This is the main API function that implements the M2 specification:
    - Computes new vector embedding for the text
    - Selects active slot based on content similarity  
    - Finds best neighbor in anchor neighborhood
    - Inserts LTM block with proper linking
    - Updates graph edges (upsert_edges)
    - Moves anchor to new block if not pinned
    
    Args:
        text: Content to write
        slot: Target anchor slot (A/B/C), auto-selected if None
        policy: Write policy (link_k, min_w, max_neighbors)
        keywords: Optional keywords list
        tags: Optional tags list  
        importance: Block importance score (0.0-1.0)
        
    Returns:
        str: Block ID of newly created block
        
    Raises:
        RuntimeError: If write operation fails
    """
    writer = get_writer()
    return writer.write(
        text=text,
        slot=slot, 
        policy=policy,
        keywords=keywords,
        tags=tags,
        importance=importance
    )


def get_write_metrics() -> Dict[str, float]:
    """Get write operation metrics for monitoring."""
    writer = get_writer()
    return writer.get_metrics()