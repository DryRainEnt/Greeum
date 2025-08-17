"""
STM 3-slot anchor manager for localized memory exploration.

Manages anchor selection, movement, and pinning based on input topic vectors.
Provides hysteresis and automatic slot switching for optimal memory traversal.
"""

import numpy as np
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional, Tuple, List

from .schema import AnchorState, AnchorsSnapshot, save_anchors_snapshot, load_anchors_snapshot, create_empty_snapshot
from ..core.metrics import record_anchor_move, record_anchor_switch


class AnchorManager:
    """Manages STM 3-slot anchor state for graph-based memory exploration."""
    
    def __init__(self, store_path: Path):
        """Initialize anchor manager with persistent storage."""
        self.store_path = store_path
        self.state: Dict[str, AnchorState] = {}
        self._load_state()
    
    def _load_state(self) -> None:
        """Load anchor state from disk or create empty state."""
        snapshot = load_anchors_snapshot(self.store_path)
        
        if snapshot is None:
            snapshot = create_empty_snapshot()
            save_anchors_snapshot(snapshot, self.store_path)
        
        # Convert to slot-keyed dictionary
        self.state = {slot['slot']: slot for slot in snapshot['slots']}
    
    def _save_state(self) -> None:
        """Persist current anchor state to disk."""
        snapshot: AnchorsSnapshot = {
            "version": 1,
            "slots": list(self.state.values()),
            "updated_at": int(datetime.now().timestamp())
        }
        save_anchors_snapshot(snapshot, self.store_path)
    
    def _normalize_vector_dimension(self, input_vec: np.ndarray) -> np.ndarray:
        """
        Normalize input vector to match system's embedding dimension.
        
        Handles dimension mismatches by truncating or padding vectors.
        System uses 128-dimensional embeddings by default.
        """
        target_dim = 128  # Standard Greeum embedding dimension
        current_dim = len(input_vec)
        
        if current_dim == target_dim:
            return input_vec  # Already correct dimension
        elif current_dim > target_dim:
            # Truncate longer vectors
            return input_vec[:target_dim]
        else:
            # Pad shorter vectors with zeros
            padded = np.zeros(target_dim)
            padded[:current_dim] = input_vec
            return padded
    
    def select_active_slot(self, input_vec: np.ndarray) -> str:
        """
        Select most relevant anchor slot based on topic vector similarity.
        
        Uses cosine similarity with hysteresis to avoid excessive slot switching.
        Defaults to slot 'A' for empty or uninitialized vectors.
        Automatically handles dimension mismatches.
        """
        if len(input_vec) == 0:
            return 'A'
            
        # Normalize input vector dimension to match system embeddings
        input_vec = self._normalize_vector_dimension(input_vec)
        
        best_slot = 'A'
        best_similarity = -1.0
        
        for slot_key, slot_state in self.state.items():
            if not slot_state['topic_vec']:
                continue
                
            topic_vec = np.array(slot_state['topic_vec'])
            if len(topic_vec) == 0:
                continue
                
            # Calculate cosine similarity
            dot_product = np.dot(input_vec, topic_vec)
            norm_product = np.linalg.norm(input_vec) * np.linalg.norm(topic_vec)
            
            if norm_product > 0:
                similarity = dot_product / norm_product
                
                # Apply hysteresis: favor recently used slots
                recency_bonus = 0.1 if slot_state['last_used_ts'] > (datetime.now().timestamp() - 3600) else 0
                adjusted_similarity = similarity + recency_bonus
                
                if adjusted_similarity > best_similarity:
                    best_similarity = adjusted_similarity
                    best_slot = slot_key
        
        return best_slot
    
    def move_anchor(self, slot: str, new_block_id: str, topic_vec: Optional[np.ndarray] = None) -> None:
        """
        Move anchor to new block unless pinned.
        
        Updates topic vector using EMA for gradual topic drift adaptation.
        """
        if slot not in self.state:
            return
            
        slot_state = self.state[slot]
        
        # Respect pinned state
        if slot_state['pinned']:
            return
        
        # Update anchor block
        old_block_id = slot_state['anchor_block_id']
        slot_state['anchor_block_id'] = new_block_id
        slot_state['last_used_ts'] = int(datetime.now().timestamp())
        
        # Record metrics
        record_anchor_move(slot)
        
        # Update topic vector with EMA if provided
        if topic_vec is not None and len(topic_vec) > 0:
            # Normalize topic vector dimension
            topic_vec = self._normalize_vector_dimension(topic_vec)
            
            if not slot_state['topic_vec']:
                # First topic vector
                slot_state['topic_vec'] = topic_vec.tolist()
            else:
                # EMA update: 80% old + 20% new
                current_vec = np.array(slot_state['topic_vec'])
                updated_vec = 0.8 * current_vec + 0.2 * topic_vec
                slot_state['topic_vec'] = updated_vec.tolist()
        
        self._save_state()
    
    def pin_anchor(self, slot: str, block_id: Optional[str] = None) -> None:
        """Pin anchor, preventing automatic movement.
        
        Args:
            slot: Slot to pin (A, B, or C)
            block_id: Optional block ID to set as anchor. If None, pins current anchor.
        """
        if slot not in self.state:
            return
        
        if block_id is not None:
            self.state[slot]['anchor_block_id'] = block_id
            
        self.state[slot]['pinned'] = True
        self.state[slot]['last_used_ts'] = int(datetime.now().timestamp())
        self._save_state()
    
    def unpin_anchor(self, slot: str) -> None:
        """Unpin anchor, allowing automatic movement."""
        if slot not in self.state:
            return
            
        self.state[slot]['pinned'] = False
        self._save_state()
    
    def get_slot_info(self, slot: str) -> Optional[AnchorState]:
        """Get current state of specific slot."""
        return self.state.get(slot)
    
    def profile(self, slot: str) -> Dict:
        """
        Get exploration profile for slot based on usage patterns.
        
        Returns adaptive parameters for graph traversal.
        """
        if slot not in self.state:
            return {"hop_budget": 2, "explore_eps": 0.1}
        
        slot_state = self.state[slot]
        
        # Adaptive hop budget based on slot usage
        base_hops = slot_state['hop_budget']
        
        # Increase exploration for frequently used slots
        recent_usage = slot_state['last_used_ts'] > (datetime.now().timestamp() - 1800)  # 30min
        adaptive_hops = base_hops + (1 if recent_usage else 0)
        
        # Exploration epsilon for beam search diversity
        explore_eps = 0.15 if recent_usage else 0.1
        
        return {
            "hop_budget": min(adaptive_hops, 3),  # Cap at 3 hops
            "explore_eps": explore_eps,
            "pinned": slot_state['pinned']
        }
    
    def get_all_anchors(self) -> Dict[str, str]:
        """Get all active anchor block IDs."""
        return {
            slot: state['anchor_block_id'] 
            for slot, state in self.state.items() 
            if state['anchor_block_id']
        }
    
    def is_initialized(self) -> bool:
        """Check if any anchors are initialized with actual blocks."""
        return any(state['anchor_block_id'] for state in self.state.values())
    
    def set_hop_budget(self, slot: str, hop_budget: int) -> None:
        """Set hop budget for specific slot."""
        if slot not in self.state:
            raise ValueError(f"Slot {slot} not found")
        
        if not isinstance(hop_budget, int) or not (1 <= hop_budget <= 3):
            raise ValueError("hop_budget must be integer between 1-3")
        
        self.state[slot]['hop_budget'] = hop_budget
        self.state[slot]['last_used_ts'] = int(datetime.now().timestamp())
        self._save_state()
    
    def get_hop_budget(self, slot: str) -> int:
        """Get current hop budget for slot."""
        if slot not in self.state:
            raise ValueError(f"Slot {slot} not found")
        return self.state[slot]['hop_budget']
    
    def update_summary(self, slot: str, summary: str) -> None:
        """Update summary description for slot."""
        if slot not in self.state:
            raise ValueError(f"Slot {slot} not found")
        
        self.state[slot]['summary'] = summary
        self.state[slot]['last_used_ts'] = int(datetime.now().timestamp())
        self._save_state()