"""
Auto Anchor Movement System (M2.4)

Implements intelligent automatic anchor movement based on topic vectors,
search patterns, and memory access optimization.
"""

import logging
from typing import Dict, List, Any, Optional, Tuple
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path

from .manager import AnchorManager
from ..core.ltm_links_cache import LTMLinksCache, calculate_link_weight
from ..core.database_manager import DatabaseManager
from ..core.metrics import record_anchor_move, record_anchor_switch

logger = logging.getLogger(__name__)


class AutoAnchorMovement:
    """
    Automatic anchor movement system for optimizing memory access patterns.
    
    Features:
    - Topic vector drift detection and anchor adjustment
    - Memory access pattern analysis for optimal anchor placement
    - Smart anchor movement based on search results relevance
    - Conflict resolution when multiple anchors compete for same topics
    """
    
    def __init__(self, anchor_manager: AnchorManager, links_cache: LTMLinksCache,
                 db_manager: Optional[DatabaseManager] = None):
        """Initialize auto anchor movement system."""
        self.anchor_manager = anchor_manager
        self.links_cache = links_cache
        self.db_manager = db_manager or DatabaseManager()
        
        # Movement thresholds and parameters
        self.movement_threshold = 0.3  # Minimum similarity difference to trigger move
        self.topic_drift_threshold = 0.2  # Topic vector change threshold
        self.recency_weight = 0.15  # Weight for recent blocks
        self.relevance_threshold = 0.6  # Minimum relevance for anchor candidates
        
        # Movement history for analysis
        self.movement_history: List[Dict[str, Any]] = []
        
    def analyze_topic_drift(self, slot: str, new_topic_vec: np.ndarray) -> Dict[str, Any]:
        """
        Analyze topic drift for a slot and determine if anchor should move.
        
        Args:
            slot: Anchor slot (A, B, C)
            new_topic_vec: New topic vector from recent queries/writes
            
        Returns:
            Dict with drift analysis results
        """
        slot_info = self.anchor_manager.get_slot_info(slot)
        if not slot_info or not slot_info['topic_vec']:
            return {
                "drift_detected": False,
                "drift_magnitude": 0.0,
                "recommendation": "no_action"
            }
        
        # Calculate topic vector drift
        current_vec = np.array(slot_info['topic_vec'])
        
        # Ensure dimension compatibility
        new_topic_vec = self.anchor_manager._normalize_vector_dimension(new_topic_vec)
        
        # Calculate cosine similarity between old and new topic vectors
        dot_product = np.dot(current_vec, new_topic_vec)
        norm_product = np.linalg.norm(current_vec) * np.linalg.norm(new_topic_vec)
        
        if norm_product == 0:
            drift_magnitude = 1.0  # Maximum drift for zero vectors
        else:
            similarity = dot_product / norm_product
            drift_magnitude = 1.0 - similarity  # Convert similarity to drift
        
        # Analyze drift significance
        drift_detected = drift_magnitude > self.topic_drift_threshold
        
        # Determine recommendation
        if drift_magnitude > 0.4:
            recommendation = "move_required"
        elif drift_magnitude > self.topic_drift_threshold:
            recommendation = "move_suggested"
        else:
            recommendation = "no_action"
        
        return {
            "drift_detected": drift_detected,
            "drift_magnitude": drift_magnitude,
            "similarity": 1.0 - drift_magnitude,
            "recommendation": recommendation,
            "threshold": self.topic_drift_threshold
        }
    
    def find_optimal_anchor_block(self, slot: str, topic_vec: np.ndarray, 
                                candidate_blocks: List[Dict[str, Any]]) -> Optional[str]:
        """
        Find optimal block to move anchor to based on topic vector similarity.
        
        Args:
            slot: Target slot for anchor movement
            topic_vec: Topic vector to match
            candidate_blocks: List of candidate blocks from search results
            
        Returns:
            Best block ID for anchor placement, or None if no good candidates
        """
        if not candidate_blocks:
            return None
        
        best_block = None
        best_score = 0.0
        
        # Ensure topic vector is normalized
        topic_vec = self.anchor_manager._normalize_vector_dimension(topic_vec)
        
        for block in candidate_blocks:
            block_embedding = block.get('embedding', [])
            if not block_embedding:
                continue
            
            # Calculate topic similarity
            block_vec = np.array(block_embedding)
            block_vec = self.anchor_manager._normalize_vector_dimension(block_vec)
            
            similarity = calculate_link_weight(topic_vec.tolist(), block_vec.tolist())
            
            # Apply recency boost for recent blocks
            try:
                block_time = datetime.fromisoformat(block.get('timestamp', ''))
                hours_old = (datetime.now() - block_time).total_seconds() / 3600
                recency_boost = max(0, self.recency_weight * (1 - hours_old / 24))  # 24h decay
            except:
                recency_boost = 0
            
            # Apply relevance score if available
            relevance_score = block.get('relevance_score', 0.5)
            
            # Combined score: similarity + recency + relevance
            final_score = similarity * 0.6 + recency_boost + relevance_score * 0.4
            
            if final_score > best_score and similarity > self.relevance_threshold:
                best_score = final_score
                best_block = str(block['block_index'])
        
        logger.debug(f"Optimal anchor for slot {slot}: block {best_block} (score: {best_score:.3f})")
        return best_block
    
    def evaluate_anchor_movement(self, slot: str, search_results: List[Dict[str, Any]], 
                               query_topic_vec: np.ndarray) -> Dict[str, Any]:
        """
        Evaluate whether anchor should move based on search results.
        
        Args:
            slot: Anchor slot used for search
            search_results: Search results from localized search
            query_topic_vec: Topic vector of the search query
            
        Returns:
            Movement evaluation results
        """
        slot_info = self.anchor_manager.get_slot_info(slot)
        if not slot_info:
            return {"should_move": False, "reason": "slot_not_found"}
        
        # Skip if anchor is pinned
        if slot_info['pinned']:
            return {"should_move": False, "reason": "anchor_pinned"}
        
        # Analyze topic drift
        drift_analysis = self.analyze_topic_drift(slot, query_topic_vec)
        
        # Find optimal anchor candidate
        optimal_block = self.find_optimal_anchor_block(slot, query_topic_vec, search_results)
        
        # Current anchor block
        current_anchor = slot_info['anchor_block_id']
        
        # Decision logic
        should_move = False
        reason = "no_action"
        
        if drift_analysis['recommendation'] == "move_required":
            should_move = True
            reason = "high_topic_drift"
        elif drift_analysis['recommendation'] == "move_suggested" and optimal_block:
            # Only move if we found a significantly better block
            if optimal_block != current_anchor:
                should_move = True
                reason = "topic_drift_with_better_candidate"
        elif optimal_block and optimal_block != current_anchor:
            # Check if the new candidate is significantly better
            current_block = self.db_manager.get_block_by_index(int(current_anchor))
            if current_block:
                current_similarity = calculate_link_weight(
                    query_topic_vec.tolist(), 
                    current_block.get('embedding', [])
                )
                
                optimal_block_data = self.db_manager.get_block_by_index(int(optimal_block))
                if optimal_block_data:
                    optimal_similarity = calculate_link_weight(
                        query_topic_vec.tolist(),
                        optimal_block_data.get('embedding', [])
                    )
                    
                    if optimal_similarity - current_similarity > self.movement_threshold:
                        should_move = True
                        reason = "better_candidate_found"
        
        return {
            "should_move": should_move,
            "reason": reason,
            "current_anchor": current_anchor,
            "optimal_block": optimal_block,
            "drift_analysis": drift_analysis,
            "movement_threshold": self.movement_threshold
        }
    
    def execute_anchor_movement(self, slot: str, target_block_id: str, 
                              topic_vec: np.ndarray, reason: str) -> bool:
        """
        Execute anchor movement with proper logging and metrics.
        
        Args:
            slot: Slot to move
            target_block_id: Target block for anchor
            topic_vec: New topic vector
            reason: Reason for movement
            
        Returns:
            True if movement was successful
        """
        try:
            # Record movement in history
            movement_record = {
                "timestamp": datetime.now().isoformat(),
                "slot": slot,
                "from_block": self.anchor_manager.get_slot_info(slot)['anchor_block_id'],
                "to_block": target_block_id,
                "reason": reason,
                "topic_vec_sample": topic_vec[:5].tolist()  # First 5 dims for logging
            }
            self.movement_history.append(movement_record)
            
            # Keep only recent history (last 100 movements)
            if len(self.movement_history) > 100:
                self.movement_history = self.movement_history[-100:]
            
            # Execute the movement
            old_anchor = self.anchor_manager.get_slot_info(slot)['anchor_block_id']
            self.anchor_manager.move_anchor(slot, target_block_id, topic_vec)
            
            # Log movement
            logger.info(f"Anchor moved: slot {slot} from block {old_anchor} to {target_block_id} ({reason})")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to execute anchor movement: {e}")
            return False
    
    def resolve_anchor_conflicts(self) -> List[Dict[str, Any]]:
        """
        Resolve conflicts when multiple anchors have similar topic vectors.
        
        Returns:
            List of conflict resolution actions taken
        """
        actions = []
        slots = ['A', 'B', 'C']
        
        # Compare all slot pairs for topic similarity
        for i, slot1 in enumerate(slots):
            for slot2 in slots[i+1:]:
                slot1_info = self.anchor_manager.get_slot_info(slot1)
                slot2_info = self.anchor_manager.get_slot_info(slot2)
                
                if not slot1_info['topic_vec'] or not slot2_info['topic_vec']:
                    continue
                
                # Calculate topic vector similarity
                vec1 = np.array(slot1_info['topic_vec'])
                vec2 = np.array(slot2_info['topic_vec'])
                
                similarity = calculate_link_weight(vec1.tolist(), vec2.tolist())
                
                # High similarity indicates conflict
                if similarity > 0.8:
                    # Resolve by diversifying the less recently used slot
                    if slot1_info['last_used_ts'] < slot2_info['last_used_ts']:
                        target_slot = slot1
                        keep_slot = slot2
                    else:
                        target_slot = slot2
                        keep_slot = slot1
                    
                    # Only resolve if neither is pinned
                    target_info = self.anchor_manager.get_slot_info(target_slot)
                    if not target_info['pinned']:
                        actions.append({
                            "action": "diversify_slot",
                            "target_slot": target_slot,
                            "keep_slot": keep_slot,
                            "similarity": similarity,
                            "timestamp": datetime.now().isoformat()
                        })
                        
                        # Actually perform diversification
                        self._diversify_slot_topic(target_slot)
        
        return actions
    
    def _diversify_slot_topic(self, slot: str) -> None:
        """
        Diversify a slot's topic vector to reduce conflicts.
        
        Args:
            slot: Slot to diversify
        """
        slot_info = self.anchor_manager.get_slot_info(slot)
        if not slot_info or slot_info['pinned']:
            return
        
        # Add small random perturbation to topic vector
        current_vec = np.array(slot_info['topic_vec'])
        noise = np.random.normal(0, 0.05, current_vec.shape)  # 5% noise
        diversified_vec = current_vec + noise
        
        # Normalize to maintain vector properties
        diversified_vec = diversified_vec / np.linalg.norm(diversified_vec)
        
        # Update topic vector
        slot_info['topic_vec'] = diversified_vec.tolist()
        self.anchor_manager._save_state()
        
        logger.info(f"Diversified topic vector for slot {slot} to reduce conflicts")
    
    def get_movement_stats(self) -> Dict[str, Any]:
        """Get statistics about anchor movements."""
        if not self.movement_history:
            return {"total_movements": 0}
        
        # Analyze movement patterns
        slot_movements = {}
        reason_counts = {}
        recent_movements = 0
        
        cutoff_time = datetime.now() - timedelta(hours=24)
        
        for record in self.movement_history:
            slot = record['slot']
            reason = record['reason']
            timestamp = datetime.fromisoformat(record['timestamp'])
            
            slot_movements[slot] = slot_movements.get(slot, 0) + 1
            reason_counts[reason] = reason_counts.get(reason, 0) + 1
            
            if timestamp > cutoff_time:
                recent_movements += 1
        
        return {
            "total_movements": len(self.movement_history),
            "recent_movements_24h": recent_movements,
            "movements_by_slot": slot_movements,
            "movements_by_reason": reason_counts,
            "movement_threshold": self.movement_threshold,
            "topic_drift_threshold": self.topic_drift_threshold
        }
    
    def optimize_movement_parameters(self) -> Dict[str, float]:
        """
        Optimize movement parameters based on usage patterns.
        
        Returns:
            Optimized parameters
        """
        stats = self.get_movement_stats()
        
        # Adjust thresholds based on movement frequency
        recent_movements = stats.get("recent_movements_24h", 0)
        
        if recent_movements > 20:
            # Too many movements, increase thresholds
            self.movement_threshold = min(0.5, self.movement_threshold * 1.1)
            self.topic_drift_threshold = min(0.3, self.topic_drift_threshold * 1.1)
        elif recent_movements < 2:
            # Too few movements, decrease thresholds
            self.movement_threshold = max(0.2, self.movement_threshold * 0.9)
            self.topic_drift_threshold = max(0.1, self.topic_drift_threshold * 0.9)
        
        return {
            "movement_threshold": self.movement_threshold,
            "topic_drift_threshold": self.topic_drift_threshold,
            "recency_weight": self.recency_weight,
            "relevance_threshold": self.relevance_threshold
        }