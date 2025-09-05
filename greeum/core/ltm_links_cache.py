"""
LTM Links Cache System (M2.3)

Provides efficient neighbor caching for LTM blocks to support
anchor-based graph traversal and improve search performance.
"""

import logging
from typing import Dict, List, Any, Optional, Tuple
from .database_manager import DatabaseManager
from .block_manager import BlockManager
import numpy as np
import time

logger = logging.getLogger(__name__)


class LTMLinksCache:
    """
    LTM block neighbor links cache management system.
    
    Supports:
    - Adding neighbor links to existing blocks
    - Retrieving cached neighbors for fast graph traversal
    - Cache invalidation and updates
    - Performance metrics and cache hit rate monitoring
    """
    
    def __init__(self, db_manager: Optional[DatabaseManager] = None):
        """Initialize LTM links cache system."""
        self.db_manager = db_manager or DatabaseManager()
        self.block_manager = BlockManager(self.db_manager)
        
        # Performance metrics
        self._cache_hits = 0
        self._cache_misses = 0
        self._link_updates = 0
        
    def add_block_links(self, block_id: str, neighbors: List[Dict[str, Any]]) -> bool:
        """
        Add neighbor links to an existing LTM block.
        
        Args:
            block_id: Target block ID
            neighbors: List of neighbor dicts with 'id' and 'weight' keys
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Get existing block
            block = self.db_manager.get_block_by_index(int(block_id))
            if not block:
                logger.warning(f"Block {block_id} not found")
                return False
            
            # Prepare links data
            links_data = {
                "neighbors": neighbors,
                "updated_at": time.time(),
                "cache_version": "2.3"
            }
            
            # Update block with links
            existing_metadata = block.get('metadata', {})
            existing_metadata['links'] = links_data
            
            success = self.db_manager.update_block_metadata(int(block_id), existing_metadata)
            
            if success:
                self._link_updates += 1
                logger.debug(f"Added {len(neighbors)} links to block {block_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to add links to block {block_id}: {e}")
            return False
    
    def get_block_neighbors(self, block_id: str, max_neighbors: int = 8) -> List[Dict[str, Any]]:
        """
        Retrieve cached neighbors for a block.
        
        Args:
            block_id: Block ID to get neighbors for
            max_neighbors: Maximum number of neighbors to return
            
        Returns:
            List of neighbor dicts with 'id' and 'weight' keys
        """
        try:
            block = self.db_manager.get_block_by_index(int(block_id))
            if not block:
                self._cache_misses += 1
                return []
            
            metadata = block.get('metadata', {})
            links = metadata.get('links', {})
            neighbors = links.get('neighbors', [])
            
            if neighbors:
                self._cache_hits += 1
                # Sort by weight descending and limit results
                sorted_neighbors = sorted(neighbors, key=lambda x: x.get('weight', 0), reverse=True)
                return sorted_neighbors[:max_neighbors]
            else:
                self._cache_misses += 1
                return []
                
        except Exception as e:
            logger.error(f"Failed to get neighbors for block {block_id}: {e}")
            self._cache_misses += 1
            return []
    
    def update_neighbor_weight(self, block_id: str, neighbor_id: str, new_weight: float) -> bool:
        """
        Update weight of a specific neighbor link.
        
        Args:
            block_id: Source block ID
            neighbor_id: Target neighbor block ID
            new_weight: New weight value
            
        Returns:
            True if successful, False otherwise
        """
        try:
            neighbors = self.get_block_neighbors(block_id, max_neighbors=100)  # Get all
            
            # Find and update the specific neighbor
            updated = False
            for neighbor in neighbors:
                if neighbor.get('id') == neighbor_id:
                    neighbor['weight'] = new_weight
                    updated = True
                    break
            
            if not updated:
                # Add new neighbor if not found
                neighbors.append({'id': neighbor_id, 'weight': new_weight})
            
            # Save updated neighbors
            return self.add_block_links(block_id, neighbors)
            
        except Exception as e:
            logger.error(f"Failed to update neighbor weight: {e}")
            return False
    
    def remove_neighbor_link(self, block_id: str, neighbor_id: str) -> bool:
        """
        Remove a specific neighbor link.
        
        Args:
            block_id: Source block ID
            neighbor_id: Target neighbor block ID to remove
            
        Returns:
            True if successful, False otherwise
        """
        try:
            neighbors = self.get_block_neighbors(block_id, max_neighbors=100)  # Get all
            
            # Filter out the target neighbor
            filtered_neighbors = [n for n in neighbors if n.get('id') != neighbor_id]
            
            if len(filtered_neighbors) < len(neighbors):
                return self.add_block_links(block_id, filtered_neighbors)
            else:
                return True  # Neighbor wasn't found, but that's still success
                
        except Exception as e:
            logger.error(f"Failed to remove neighbor link: {e}")
            return False
    
    def bulk_update_links(self, block_links: Dict[str, List[Dict[str, Any]]]) -> int:
        """
        Bulk update neighbor links for multiple blocks.
        
        Args:
            block_links: Dict mapping block_id -> list of neighbors
            
        Returns:
            Number of successfully updated blocks
        """
        success_count = 0
        
        for block_id, neighbors in block_links.items():
            if self.add_block_links(block_id, neighbors):
                success_count += 1
        
        logger.info(f"Bulk update: {success_count}/{len(block_links)} blocks updated")
        return success_count
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache performance statistics."""
        total_requests = self._cache_hits + self._cache_misses
        hit_rate = self._cache_hits / total_requests if total_requests > 0 else 0
        
        return {
            "cache_hits": self._cache_hits,
            "cache_misses": self._cache_misses,
            "hit_rate": hit_rate,
            "total_requests": total_requests,
            "link_updates": self._link_updates
        }
    
    def clear_cache_stats(self) -> None:
        """Reset cache performance counters."""
        self._cache_hits = 0
        self._cache_misses = 0
        self._link_updates = 0
    
    def validate_links_integrity(self, block_id: str) -> Dict[str, Any]:
        """
        Validate integrity of cached links for a block.
        
        Args:
            block_id: Block ID to validate
            
        Returns:
            Dict with validation results
        """
        try:
            neighbors = self.get_block_neighbors(block_id, max_neighbors=100)
            
            validation_result = {
                "block_id": block_id,
                "neighbor_count": len(neighbors),
                "valid_neighbors": 0,
                "invalid_neighbors": 0,
                "missing_blocks": [],
                "weight_issues": []
            }
            
            for neighbor in neighbors:
                neighbor_id = neighbor.get('id')
                weight = neighbor.get('weight', 0)
                
                # Check if neighbor block exists
                try:
                    neighbor_block = self.db_manager.get_block_by_index(int(neighbor_id))
                    if neighbor_block:
                        validation_result["valid_neighbors"] += 1
                    else:
                        validation_result["invalid_neighbors"] += 1
                        validation_result["missing_blocks"].append(neighbor_id)
                except:
                    validation_result["invalid_neighbors"] += 1
                    validation_result["missing_blocks"].append(neighbor_id)
                
                # Check weight validity
                if not (0.0 <= weight <= 1.0):
                    validation_result["weight_issues"].append({
                        "neighbor_id": neighbor_id,
                        "weight": weight
                    })
            
            return validation_result
            
        except Exception as e:
            logger.error(f"Failed to validate links for block {block_id}: {e}")
            return {"error": str(e)}
    
    def cleanup_orphaned_links(self, dry_run: bool = True) -> Dict[str, Any]:
        """
        Clean up links pointing to non-existent blocks.
        
        Args:
            dry_run: If True, only report what would be cleaned up
            
        Returns:
            Dict with cleanup results
        """
        try:
            # Get all blocks with links
            all_blocks = self.db_manager.get_blocks(limit=10000)  # Large limit to get all
            
            cleanup_stats = {
                "blocks_checked": 0,
                "orphaned_links_found": 0,
                "blocks_with_orphans": 0,
                "cleanup_performed": not dry_run
            }
            
            for block in all_blocks:
                metadata = block.get('metadata', {})
                links = metadata.get('links', {})
                neighbors = links.get('neighbors', [])
                
                if not neighbors:
                    continue
                
                cleanup_stats["blocks_checked"] += 1
                block_id = str(block['block_index'])
                
                # Find orphaned links
                valid_neighbors = []
                orphan_count = 0
                
                for neighbor in neighbors:
                    neighbor_id = neighbor.get('id')
                    try:
                        neighbor_block = self.db_manager.get_block_by_index(int(neighbor_id))
                        if neighbor_block:
                            valid_neighbors.append(neighbor)
                        else:
                            orphan_count += 1
                    except:
                        orphan_count += 1
                
                if orphan_count > 0:
                    cleanup_stats["blocks_with_orphans"] += 1
                    cleanup_stats["orphaned_links_found"] += orphan_count
                    
                    # Perform cleanup if not dry run
                    if not dry_run:
                        self.add_block_links(block_id, valid_neighbors)
            
            return cleanup_stats
            
        except Exception as e:
            logger.error(f"Failed to cleanup orphaned links: {e}")
            return {"error": str(e)}


def create_neighbor_link(block_id: str, weight: float) -> Dict[str, Any]:
    """
    Utility function to create a neighbor link dict.
    
    Args:
        block_id: Target block ID
        weight: Link weight (0.0 to 1.0)
        
    Returns:
        Neighbor link dict
    """
    return {
        "id": str(block_id),
        "weight": float(weight)
    }


def calculate_link_weight(block_a_emb: List[float], block_b_emb: List[float]) -> float:
    """
    Calculate link weight between two blocks based on embedding similarity.
    
    Args:
        block_a_emb: Block A embedding vector
        block_b_emb: Block B embedding vector
        
    Returns:
        Similarity weight (0.0 to 1.0)
    """
    try:
        # Convert to numpy arrays
        vec_a = np.array(block_a_emb)
        vec_b = np.array(block_b_emb)
        
        # Calculate cosine similarity
        dot_product = np.dot(vec_a, vec_b)
        norm_a = np.linalg.norm(vec_a)
        norm_b = np.linalg.norm(vec_b)
        
        if norm_a == 0 or norm_b == 0:
            return 0.0
        
        cosine_sim = dot_product / (norm_a * norm_b)
        
        # Normalize to 0-1 range (cosine similarity is -1 to 1)
        normalized_weight = (cosine_sim + 1.0) / 2.0
        
        return float(np.clip(normalized_weight, 0.0, 1.0))
        
    except Exception as e:
        logger.error(f"Failed to calculate link weight: {e}")
        return 0.0