"""
Automatic Merge Engine for Branch Management
Implements soft merge with EMA tracking, cooldown, and reversible checkpoints
"""

import time
import uuid
import numpy as np
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from collections import deque
import logging

logger = logging.getLogger(__name__)


@dataclass
class MergeScore:
    """Container for merge score and its components"""
    total: float
    components: Dict[str, float] = field(default_factory=dict)
    
    
@dataclass
class MergeCheckpoint:
    """Reversible checkpoint for merge operations"""
    id: str
    slot_i: str
    slot_j: str
    merge_score: float
    reversible: bool
    created_at: float
    state_before: Optional[Dict] = None
    state_after: Optional[Dict] = None
    undone: bool = False
    
    
@dataclass
class MergeResult:
    """Result of merge evaluation"""
    should_merge: bool
    merge_score: float
    reason: str
    is_dry_run: bool
    suggested_action: Optional[str] = None


class EMATracker:
    """Exponential Moving Average tracker for merge scores"""
    
    def __init__(self, 
                 alpha: float = 0.3,
                 window_size: int = 10,
                 trigger_count: int = 6,
                 threshold_high: float = 0.7):
        self.alpha = alpha
        self.window_size = window_size
        self.trigger_count = trigger_count
        self.threshold_high = threshold_high
        self.current_value = 0.5  # Initial EMA
        self.history = deque(maxlen=window_size)
        
    def update(self, new_score: float) -> float:
        """Update EMA: EMA ← α*EMA + (1-α)*new_score"""
        self.current_value = self.alpha * self.current_value + (1 - self.alpha) * new_score
        self.history.append(self.current_value)
        return self.current_value
        
    def should_trigger_merge(self) -> bool:
        """Check if merge should be triggered based on recent history"""
        if len(self.history) < self.window_size:
            return False
            
        high_count = sum(1 for score in self.history if score >= self.threshold_high)
        return high_count >= self.trigger_count


class CooldownManager:
    """Manages cooldown periods between merges"""
    
    def __init__(self, duration_minutes: int = 30):
        self.duration_seconds = duration_minutes * 60
        self.cooldown_start: Optional[float] = None
        
    def start_cooldown(self):
        """Start cooldown period"""
        self.cooldown_start = time.time()
        
    def is_in_cooldown(self) -> bool:
        """Check if currently in cooldown period"""
        if self.cooldown_start is None:
            return False
        return time.time() - self.cooldown_start < self.duration_seconds
        
    def reset_on_activity(self):
        """Reset cooldown timer on user activity"""
        if self.cooldown_start is not None:
            self.cooldown_start = time.time()
            
    def time_remaining(self) -> float:
        """Get remaining cooldown time in seconds"""
        if not self.is_in_cooldown():
            return 0
        return self.duration_seconds - (time.time() - self.cooldown_start)


class MergeEngine:
    """Main engine for automatic branch merging"""
    
    def __init__(self, db_manager=None):
        self.db_manager = db_manager
        # Merge score weights
        self.weights = {
            'w1': 0.3,  # Head cosine similarity
            'w2': 0.2,  # Centroid cosine similarity  
            'w3': 0.2,  # Tag Jaccard similarity
            'w4': 0.2,  # Temporal proximity
            'w5': 0.1   # Divergence penalty
        }
        
        # Time decay constant (τ) in seconds
        self.tau = 3600  # 1 hour
        
        # EMA trackers for each slot pair
        self.ema_trackers: Dict[Tuple[str, str], EMATracker] = {}
        
        # Cooldown manager
        self.cooldown = CooldownManager(duration_minutes=30)
        
        # Checkpoint storage (for O(1) undo)
        self.checkpoints: List[MergeCheckpoint] = []
        self.undo_stack: List[MergeCheckpoint] = []
        
        # State storage for undo
        self.state_history: List[Dict] = []
        self.current_state: Dict = {}
        
        # Branch metadata cache
        self.branch_cache: Dict[str, List[Dict]] = {}
        
    def calculate_merge_score(self, block_i: Dict, block_j: Dict) -> MergeScore:
        """
        Calculate merge score between two blocks
        MS = w1*cos(head_i,head_j) + w2*cos(centroid_i,centroid_j) 
             + w3*Jaccard(tags) + w4*exp(-Δt/τ) - w5*divergence
        """
        # Check same root requirement
        if block_i.get('root') != block_j.get('root'):
            raise ValueError("Cannot merge blocks with different roots")
            
        components = {}
        
        # 1. Cosine similarity of head embeddings
        if 'embedding' in block_i and 'embedding' in block_j:
            emb_i = np.array(block_i['embedding'])
            emb_j = np.array(block_j['embedding'])
            
            # Normalize and compute cosine
            norm_i = np.linalg.norm(emb_i)
            norm_j = np.linalg.norm(emb_j)
            
            if norm_i > 0 and norm_j > 0:
                cos_heads = np.dot(emb_i, emb_j) / (norm_i * norm_j)
                components['cosine_heads'] = float(cos_heads)
            else:
                components['cosine_heads'] = 0.5
        else:
            components['cosine_heads'] = 0.5
            
        # 2. Centroid similarity (compute from branch history)
        centroid_i = self._compute_centroid(block_i)
        centroid_j = self._compute_centroid(block_j)
        
        if centroid_i is not None and centroid_j is not None:
            norm_ci = np.linalg.norm(centroid_i)
            norm_cj = np.linalg.norm(centroid_j)
            if norm_ci > 0 and norm_cj > 0:
                cos_centroids = np.dot(centroid_i, centroid_j) / (norm_ci * norm_cj)
                components['cosine_centroids'] = float(cos_centroids)
            else:
                components['cosine_centroids'] = 0.5
        else:
            components['cosine_centroids'] = components['cosine_heads'] * 0.9
        
        # 3. Jaccard similarity of tags
        tags_i = set(block_i.get('tags', {}).get('labels', []))
        tags_j = set(block_j.get('tags', {}).get('labels', []))
        
        if tags_i or tags_j:
            intersection = len(tags_i & tags_j)
            union = len(tags_i | tags_j)
            jaccard = intersection / union if union > 0 else 0
            components['jaccard_tags'] = jaccard
        else:
            components['jaccard_tags'] = 0.5
            
        # 4. Temporal proximity
        time_i = block_i.get('created_at', time.time())
        time_j = block_j.get('created_at', time.time())
        delta_t = abs(time_j - time_i)
        temporal = np.exp(-delta_t / self.tau)
        components['temporal_proximity'] = float(temporal)
        
        # 5. Divergence penalty
        div_i = block_i.get('stats', {}).get('divergence', 0)
        div_j = block_j.get('stats', {}).get('divergence', 0)
        avg_divergence = (div_i + div_j) / 2
        # Normalize divergence to [0, 1] range (assuming max divergence of 10)
        div_penalty = min(avg_divergence / 10, 1.0)
        components['divergence_penalty'] = div_penalty
        
        # Calculate total score
        total = (
            self.weights['w1'] * components['cosine_heads'] +
            self.weights['w2'] * components['cosine_centroids'] +
            self.weights['w3'] * components['jaccard_tags'] +
            self.weights['w4'] * components['temporal_proximity'] -
            self.weights['w5'] * components['divergence_penalty']
        )
        
        # Clamp to [0, 1]
        total = max(0, min(1, total))
        
        return MergeScore(total=total, components=components)
    
    def _compute_centroid(self, block: Dict) -> Optional[np.ndarray]:
        """Compute centroid embedding from branch history"""
        if not self.db_manager:
            return None
            
        # Get branch blocks (up to 10 ancestors)
        branch_blocks = self._get_branch_blocks(block.get('id'), block.get('root'), limit=10)
        
        if not branch_blocks:
            return block.get('embedding')
            
        # Compute weighted average of embeddings
        embeddings = []
        weights = []
        
        for i, b in enumerate(branch_blocks):
            if 'embedding' in b and b['embedding']:
                embeddings.append(np.array(b['embedding']))
                # Recent blocks have higher weight
                weights.append(1.0 / (i + 1))
                
        if not embeddings:
            return None
            
        # Normalize weights
        weights = np.array(weights)
        weights = weights / weights.sum()
        
        # Compute weighted centroid
        centroid = np.zeros_like(embeddings[0])
        for emb, w in zip(embeddings, weights):
            centroid += emb * w
            
        return centroid
    
    def _get_branch_blocks(self, block_id: str, root: str, limit: int = 10) -> List[Dict]:
        """Get blocks in the same branch"""
        if block_id in self.branch_cache:
            return self.branch_cache[block_id][:limit]
            
        blocks = []
        
        if self.db_manager:
            try:
                # Get blocks with same root, ordered by creation time
                query = "SELECT * FROM blocks WHERE root = ? ORDER BY created_at DESC LIMIT ?"
                result = self.db_manager.execute_query(query, (root, limit))
                blocks = [dict(row) for row in result] if result else []
            except:
                pass
                
        self.branch_cache[block_id] = blocks
        return blocks
        
    def get_ema_tracker(self, slot_i: str, slot_j: str) -> EMATracker:
        """Get or create EMA tracker for slot pair"""
        key = tuple(sorted([slot_i, slot_j]))
        if key not in self.ema_trackers:
            self.ema_trackers[key] = EMATracker()
        return self.ema_trackers[key]
        
    def record_similarity(self, slot_i: str, slot_j: str, score: float):
        """Record similarity score and update EMA"""
        tracker = self.get_ema_tracker(slot_i, slot_j)
        tracker.update(score)
        
    def create_checkpoint(self, 
                         slot_i: str, 
                         slot_j: str,
                         merge_score: float,
                         reversible: bool = True) -> MergeCheckpoint:
        """Create a reversible checkpoint"""
        checkpoint = MergeCheckpoint(
            id=str(uuid.uuid4()),
            slot_i=slot_i,
            slot_j=slot_j,
            merge_score=merge_score,
            reversible=reversible,
            created_at=time.time(),
            state_before=self.current_state.copy() if reversible else None
        )
        
        self.checkpoints.append(checkpoint)
        if reversible:
            self.undo_stack.append(checkpoint)
            
        return checkpoint
        
    def undo_checkpoint(self, checkpoint_id: str) -> bool:
        """Undo a checkpoint (O(1) operation)"""
        # Check 5-minute window
        current_time = time.time()
        
        # Find checkpoint in undo stack (O(1) for recent items)
        for i in range(len(self.undo_stack) - 1, -1, -1):
            cp = self.undo_stack[i]
            if cp.id == checkpoint_id:
                # Check 5-minute window
                if current_time - cp.created_at > 300:  # 5 minutes
                    logger.warning(f"Cannot undo checkpoint {checkpoint_id}: outside 5-minute window")
                    return False
                    
                # Restore state (O(1) dictionary assignment)
                if cp.state_before:
                    self.current_state = cp.state_before.copy()
                    
                # Mark as undone and remove from stack
                cp.undone = True
                self.undo_stack.pop(i)
                
                logger.info(f"Successfully undone checkpoint {checkpoint_id}")
                return True
                
        logger.warning(f"Checkpoint {checkpoint_id} not found in undo stack")
        return False
        
    def save_state(self, state: Dict):
        """Save current state"""
        self.current_state = state.copy()
        self.state_history.append(state.copy())
        
    def get_current_state(self) -> Dict:
        """Get current state"""
        return self.current_state.copy()
        
    def merge_slots(self, slot_i: str, slot_j: str) -> MergeCheckpoint:
        """Perform actual merge between slots"""
        # Save state before merge
        checkpoint = self.create_checkpoint(slot_i, slot_j, 0.0, reversible=True)
        
        # Simulate merge operation (actual implementation would modify block structure)
        merged_state = self.current_state.copy()
        if f'slot_{slot_i}' in merged_state and f'slot_{slot_j}' in merged_state:
            # Merge slot_j into slot_i
            merged_state[f'slot_{slot_i}']['merged_from'] = slot_j
            merged_state[f'slot_{slot_j}']['merged_into'] = slot_i
            
        checkpoint.state_after = merged_state
        self.current_state = merged_state
        
        # Start cooldown
        self.cooldown.start_cooldown()
        
        return checkpoint
        
    def evaluate_merge(self, 
                      slot_i: str, 
                      slot_j: str,
                      dry_run: bool = False) -> MergeResult:
        """Evaluate whether slots should be merged"""
        # Check cooldown
        if self.cooldown.is_in_cooldown() and not dry_run:
            return MergeResult(
                should_merge=False,
                merge_score=0.0,
                reason=f"In cooldown period ({self.cooldown.time_remaining():.0f}s remaining)",
                is_dry_run=dry_run
            )
            
        # Get EMA tracker
        tracker = self.get_ema_tracker(slot_i, slot_j)
        
        # Check if merge should be triggered
        should_merge = tracker.should_trigger_merge()
        
        result = MergeResult(
            should_merge=should_merge,
            merge_score=tracker.current_value,
            reason="EMA threshold met" if should_merge else "EMA below threshold",
            is_dry_run=dry_run,
            suggested_action="merge" if should_merge else "wait"
        )
        
        return result
        
    def apply_merge(self, slot_i: str, slot_j: str) -> MergeCheckpoint:
        """Apply merge between slots"""
        return self.merge_slots(slot_i, slot_j)
        
    def is_in_cooldown(self) -> bool:
        """Check if engine is in cooldown"""
        return self.cooldown.is_in_cooldown()