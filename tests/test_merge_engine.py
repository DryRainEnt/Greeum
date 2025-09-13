"""
Test suite for automatic merge engine (PR#4)
Following TDD approach: RED -> GREEN -> REFACTOR
"""

import unittest
import time
import numpy as np
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock

from greeum.core.merge_engine import (
    MergeEngine,
    MergeScore,
    MergeCheckpoint,
    EMATracker,
    CooldownManager
)


class TestMergeScoreCalculation(unittest.TestCase):
    """Test merge score calculation formula"""
    
    def setUp(self):
        self.engine = MergeEngine()
        
    def test_merge_score_components(self):
        """Test individual components of merge score calculation
        MS = w1*cos(head_i,head_j) + w2*cos(centroid_i,centroid_j) 
             + w3*Jaccard(tags) + w4*exp(-Δt/τ) - w5*divergence
        """
        # Create mock blocks
        block_i = {
            'id': 'block_i',
            'root': 'root_a',
            'embedding': np.array([0.1, 0.2, 0.3]),
            'tags': {'labels': ['tag1', 'tag2', 'tag3']},
            'created_at': time.time() - 300,  # 5 minutes ago
            'stats': {'divergence': 2}
        }
        
        block_j = {
            'id': 'block_j', 
            'root': 'root_a',  # Same root
            'embedding': np.array([0.15, 0.25, 0.28]),
            'tags': {'labels': ['tag2', 'tag3', 'tag4']},
            'created_at': time.time(),
            'stats': {'divergence': 1}
        }
        
        score = self.engine.calculate_merge_score(block_i, block_j)
        
        # Score should be between 0 and 1
        self.assertGreaterEqual(score.total, 0)
        self.assertLessEqual(score.total, 1)
        
        # Components should be weighted properly
        self.assertIn('cosine_heads', score.components)
        self.assertIn('cosine_centroids', score.components)
        self.assertIn('jaccard_tags', score.components)
        self.assertIn('temporal_proximity', score.components)
        self.assertIn('divergence_penalty', score.components)
        
    def test_same_root_requirement(self):
        """Only blocks with same root can be merged"""
        block_i = {'id': 'i', 'root': 'root_a'}
        block_j = {'id': 'j', 'root': 'root_b'}  # Different root
        
        with self.assertRaises(ValueError) as ctx:
            self.engine.calculate_merge_score(block_i, block_j)
        self.assertIn('different roots', str(ctx.exception))
        
    def test_divergence_penalty(self):
        """High divergence should lower merge score"""
        block_low_div = {
            'id': 'low',
            'root': 'root_a',
            'stats': {'divergence': 1}
        }
        
        block_high_div = {
            'id': 'high',
            'root': 'root_a', 
            'stats': {'divergence': 10}
        }
        
        base_block = {'id': 'base', 'root': 'root_a', 'stats': {'divergence': 1}}
        
        score_low = self.engine.calculate_merge_score(base_block, block_low_div)
        score_high = self.engine.calculate_merge_score(base_block, block_high_div)
        
        # Higher divergence should result in lower score
        self.assertGreater(score_low.total, score_high.total)


class TestEMATracking(unittest.TestCase):
    """Test Exponential Moving Average tracking"""
    
    def setUp(self):
        self.ema_tracker = EMATracker(alpha=0.3)
        
    def test_ema_update_formula(self):
        """Test EMA update: EMA ← α*EMA + (1-α)*MS"""
        initial_ema = 0.5
        new_score = 0.8
        alpha = 0.3
        
        self.ema_tracker.current_value = initial_ema
        updated = self.ema_tracker.update(new_score)
        
        expected = alpha * initial_ema + (1 - alpha) * new_score
        self.assertAlmostEqual(updated, expected, places=5)
        
    def test_ema_convergence(self):
        """EMA should converge to stable value over time"""
        stable_score = 0.7
        
        for _ in range(50):
            self.ema_tracker.update(stable_score)
            
        # After many updates with same value, EMA should converge
        self.assertAlmostEqual(self.ema_tracker.current_value, stable_score, places=2)
        
    def test_merge_threshold_trigger(self):
        """Test merge trigger: Recent R times, M times EMA≥θ_high"""
        tracker = EMATracker(
            alpha=0.3,
            window_size=10,  # R=10
            trigger_count=6,  # M=6
            threshold_high=0.7  # θ_high=0.7
        )
        
        # Add scores that should trigger merge
        high_scores = [0.75, 0.8, 0.72, 0.78, 0.73, 0.71, 0.76, 0.74, 0.77, 0.79]
        
        for score in high_scores:
            tracker.update(score)
            
        self.assertTrue(tracker.should_trigger_merge())
        
    def test_no_trigger_below_threshold(self):
        """Should not trigger if not enough high scores"""
        tracker = EMATracker(
            window_size=10,
            trigger_count=6,
            threshold_high=0.7
        )
        
        # Mix of high and low scores (only 4 high)
        mixed_scores = [0.75, 0.6, 0.72, 0.5, 0.4, 0.71, 0.3, 0.2, 0.73, 0.1]
        
        for score in mixed_scores:
            tracker.update(score)
            
        self.assertFalse(tracker.should_trigger_merge())


class TestCooldownMechanism(unittest.TestCase):
    """Test 30-minute cooldown period"""
    
    def setUp(self):
        self.cooldown = CooldownManager(duration_minutes=30)
        
    def test_30min_cooldown_period(self):
        """Test 30-minute cooldown after merge"""
        self.cooldown.start_cooldown()
        
        # Immediately after start, should be in cooldown
        self.assertTrue(self.cooldown.is_in_cooldown())
        
        # Mock time passing (29 minutes)
        with patch('time.time', return_value=time.time() + 29*60):
            self.assertTrue(self.cooldown.is_in_cooldown())
            
        # After 30 minutes, cooldown should end
        with patch('time.time', return_value=time.time() + 31*60):
            self.assertFalse(self.cooldown.is_in_cooldown())
            
    def test_cooldown_reset_on_activity(self):
        """Cooldown should reset on user activity"""
        self.cooldown.start_cooldown()
        
        # After 15 minutes
        with patch('time.time', return_value=time.time() + 15*60):
            self.assertTrue(self.cooldown.is_in_cooldown())
            
            # User activity resets cooldown
            self.cooldown.reset_on_activity()
            
            # Should restart 30-minute timer
            self.assertTrue(self.cooldown.is_in_cooldown())
            
        # 29 minutes after reset (not original start)
        with patch('time.time', return_value=time.time() + 44*60):
            self.assertTrue(self.cooldown.is_in_cooldown())
            
        # 31 minutes after reset
        with patch('time.time', return_value=time.time() + 46*60):
            self.assertFalse(self.cooldown.is_in_cooldown())


class TestCheckpointAndUndo(unittest.TestCase):
    """Test reversible checkpoint and O(1) undo mechanism"""
    
    def setUp(self):
        self.engine = MergeEngine()
        
    def test_reversible_checkpoint_creation(self):
        """Test creation of reversible checkpoint"""
        # Create checkpoint for merge
        checkpoint = self.engine.create_checkpoint(
            slot_i='A',
            slot_j='B',
            merge_score=0.85,
            reversible=True
        )
        
        self.assertIsNotNone(checkpoint)
        self.assertTrue(checkpoint.reversible)
        self.assertEqual(checkpoint.slot_i, 'A')
        self.assertEqual(checkpoint.slot_j, 'B')
        self.assertEqual(checkpoint.merge_score, 0.85)
        self.assertIsNotNone(checkpoint.id)
        self.assertIsNotNone(checkpoint.created_at)
        
    def test_O1_undo_mechanism(self):
        """Test O(1) time complexity undo"""
        # Create multiple checkpoints
        cp1 = self.engine.create_checkpoint('A', 'B', 0.8, reversible=True)
        cp2 = self.engine.create_checkpoint('B', 'C', 0.75, reversible=True)
        cp3 = self.engine.create_checkpoint('A', 'C', 0.9, reversible=True)
        
        # Undo should be O(1) - constant time
        start_time = time.perf_counter()
        success = self.engine.undo_checkpoint(cp3.id)
        undo_time = time.perf_counter() - start_time
        
        self.assertTrue(success)
        self.assertLess(undo_time, 0.001)  # Should be very fast (< 1ms)
        
        # Should maintain undo stack
        self.assertEqual(len(self.engine.undo_stack), 2)
        
    def test_undo_within_5min_window(self):
        """Undo should only work within 5-minute window"""
        checkpoint = self.engine.create_checkpoint('A', 'B', 0.8, reversible=True)
        
        # Within 5 minutes - should work
        with patch('time.time', return_value=time.time() + 4*60):
            self.assertTrue(self.engine.undo_checkpoint(checkpoint.id))
            
        # Create another checkpoint
        checkpoint2 = self.engine.create_checkpoint('B', 'C', 0.7, reversible=True)
        
        # After 5 minutes - should fail
        with patch('time.time', return_value=time.time() + 6*60):
            self.assertFalse(self.engine.undo_checkpoint(checkpoint2.id))
            
    def test_undo_restores_previous_state(self):
        """Undo should restore exact previous state"""
        # Mock initial state
        initial_state = {
            'slot_A': {'head': 'block_1', 'root': 'root_a'},
            'slot_B': {'head': 'block_2', 'root': 'root_a'},
            'slot_C': {'head': 'block_3', 'root': 'root_b'}
        }
        
        self.engine.save_state(initial_state)
        
        # Perform merge (changes state)
        checkpoint = self.engine.merge_slots('A', 'B')
        
        # State should be different after merge
        merged_state = self.engine.get_current_state()
        # Check that merge actually modified the state
        if 'slot_A' in merged_state and 'slot_B' in merged_state:
            self.assertIn('merged_from', merged_state['slot_A'])
            self.assertIn('merged_into', merged_state['slot_B'])
        
        # Undo the merge
        self.engine.undo_checkpoint(checkpoint.id)
        
        # State should be restored
        restored_state = self.engine.get_current_state()
        self.assertEqual(initial_state, restored_state)


class TestAutoMergeIntegration(unittest.TestCase):
    """Integration tests for complete auto-merge flow"""
    
    def setUp(self):
        self.engine = MergeEngine()
        
    def test_dry_run_mode(self):
        """Test merge in dry-run mode (no actual changes)"""
        result = self.engine.evaluate_merge(
            slot_i='A',
            slot_j='B',
            dry_run=True
        )
        
        self.assertIsNotNone(result)
        self.assertTrue(result.is_dry_run)
        self.assertIsNotNone(result.suggested_action)
        self.assertIsNotNone(result.merge_score)
        self.assertIsNotNone(result.reason)
        
        # No actual checkpoint should be created in dry-run
        self.assertEqual(len(self.engine.checkpoints), 0)
        
    def test_auto_merge_with_ema_threshold(self):
        """Test complete auto-merge flow with EMA threshold"""
        # Simulate multiple high similarity scores over time
        for _ in range(10):
            score = np.random.uniform(0.75, 0.85)
            self.engine.record_similarity('A', 'B', score)
            
        # Check if merge is suggested
        suggestion = self.engine.evaluate_merge('A', 'B', dry_run=True)
        
        if suggestion.should_merge:
            # Apply the merge
            checkpoint = self.engine.apply_merge('A', 'B')
            self.assertIsNotNone(checkpoint)
            self.assertTrue(checkpoint.reversible)
            
            # Cooldown should be active
            self.assertTrue(self.engine.is_in_cooldown())


if __name__ == '__main__':
    unittest.main()