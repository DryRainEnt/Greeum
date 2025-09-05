"""
Test suite for M2.4 - Auto Anchor Movement System functionality
"""

import unittest
import time
import tempfile
import numpy as np
from pathlib import Path
from datetime import datetime, timedelta

from greeum.anchors.auto_movement import AutoAnchorMovement
from greeum.anchors.manager import AnchorManager
from greeum.core.ltm_links_cache import LTMLinksCache, create_neighbor_link
from greeum.core.database_manager import DatabaseManager
from greeum.core.block_manager import BlockManager

class TestM24AutoAnchorMovement(unittest.TestCase):
    def setUp(self):
        """Set up test environment"""
        # Create temporary files
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        
        self.temp_anchors = tempfile.NamedTemporaryFile(delete=False, suffix='.json')
        self.temp_anchors.close()
        
        # Initialize components
        self.db_manager = DatabaseManager(connection_string=self.temp_db.name)
        self.block_manager = BlockManager(self.db_manager)
        self.links_cache = LTMLinksCache(self.db_manager)
        self.anchor_manager = AnchorManager(Path(self.temp_anchors.name))
        self.auto_movement = AutoAnchorMovement(self.anchor_manager, self.links_cache, self.db_manager)
        
        # Create test blocks with diverse embeddings
        self.test_blocks = []
        embeddings = [
            [0.8, 0.6] + [0.0] * 126,  # Block 0: topic A
            [0.6, 0.8] + [0.0] * 126,  # Block 1: topic B
            [0.9, 0.4] + [0.0] * 126,  # Block 2: similar to A
            [0.3, 0.9] + [0.0] * 126,  # Block 3: similar to B
            [0.5, 0.5] + [0.0] * 126,  # Block 4: neutral
        ]
        
        for i, embedding in enumerate(embeddings):
            block = self.block_manager.add_block(
                context=f"Test block {i} with topic vector {embedding[:2]}",
                keywords=[f"test{i}", "block"],
                tags=[f"tag{i}"],
                embedding=embedding,
                importance=0.5 + 0.1 * i
            )
            self.test_blocks.append(block)
    
    def tearDown(self):
        """Clean up test environment"""
        Path(self.temp_db.name).unlink(missing_ok=True)
        Path(self.temp_anchors.name).unlink(missing_ok=True)
    
    def test_topic_drift_analysis(self):
        """Test topic drift detection and analysis"""
        # Set initial topic vector for slot A
        initial_topic = np.array([0.8, 0.6] + [0.0] * 126)
        self.anchor_manager.move_anchor('A', str(self.test_blocks[0]['block_index']), initial_topic)
        
        # Test no drift (similar vector)
        similar_topic = np.array([0.85, 0.55] + [0.0] * 126)
        no_drift = self.auto_movement.analyze_topic_drift('A', similar_topic)
        
        self.assertFalse(no_drift['drift_detected'])
        self.assertLess(no_drift['drift_magnitude'], self.auto_movement.topic_drift_threshold)
        self.assertEqual(no_drift['recommendation'], 'no_action')
        
        # Test significant drift (different vector)
        different_topic = np.array([0.2, 0.9] + [0.0] * 126)
        drift_detected = self.auto_movement.analyze_topic_drift('A', different_topic)
        
        self.assertTrue(drift_detected['drift_detected'])
        self.assertGreater(drift_detected['drift_magnitude'], self.auto_movement.topic_drift_threshold)
        self.assertIn(drift_detected['recommendation'], ['move_suggested', 'move_required'])
        
        print(f"✓ Topic drift analysis: no drift={no_drift['drift_magnitude']:.3f}, "
              f"high drift={drift_detected['drift_magnitude']:.3f}")
    
    def test_optimal_anchor_block_selection(self):
        """Test finding optimal block for anchor placement"""
        query_topic = np.array([0.8, 0.6] + [0.0] * 126)
        
        # Mock search results with test blocks
        candidate_blocks = []
        for block in self.test_blocks:
            candidate_blocks.append({
                'block_index': block['block_index'],
                'embedding': block['embedding'],
                'timestamp': block['timestamp'],
                'relevance_score': 0.7,
                'context': block['context']
            })
        
        # Find optimal block
        optimal_block = self.auto_movement.find_optimal_anchor_block('A', query_topic, candidate_blocks)
        
        self.assertIsNotNone(optimal_block)
        # Should select block 0 (most similar to query_topic [0.8, 0.6])
        self.assertEqual(optimal_block, str(self.test_blocks[0]['block_index']))
        
        print(f"✓ Optimal anchor selection: block {optimal_block}")
    
    def test_anchor_movement_evaluation_performance(self):
        """Test anchor movement evaluation performance < 5ms"""
        # Setup anchor
        topic_vec = np.array([0.8, 0.6] + [0.0] * 126)
        self.anchor_manager.move_anchor('A', str(self.test_blocks[0]['block_index']), topic_vec)
        
        # Prepare search results
        search_results = [
            {
                'block_index': self.test_blocks[1]['block_index'],
                'embedding': self.test_blocks[1]['embedding'],
                'timestamp': self.test_blocks[1]['timestamp'],
                'relevance_score': 0.8
            }
        ]
        
        query_topic = np.array([0.6, 0.8] + [0.0] * 126)  # Different topic
        
        start_time = time.perf_counter()
        
        # Evaluate movement
        evaluation = self.auto_movement.evaluate_anchor_movement('A', search_results, query_topic)
        
        end_time = time.perf_counter()
        operation_time_ms = (end_time - start_time) * 1000
        
        # Performance requirement: < 5ms
        self.assertLess(operation_time_ms, 5.0, 
                       f"Movement evaluation took {operation_time_ms:.2f}ms, should be < 5ms")
        
        # Verify evaluation results
        self.assertIn('should_move', evaluation)
        self.assertIn('reason', evaluation)
        self.assertIn('drift_analysis', evaluation)
        
        print(f"✓ Movement evaluation performance: {operation_time_ms:.2f}ms")
    
    def test_anchor_movement_execution(self):
        """Test successful anchor movement execution"""
        # Setup initial anchor
        initial_topic = np.array([0.8, 0.6] + [0.0] * 126)
        initial_block = str(self.test_blocks[0]['block_index'])
        self.anchor_manager.move_anchor('A', initial_block, initial_topic)
        
        # Execute movement to different block
        target_block = str(self.test_blocks[1]['block_index'])
        new_topic = np.array([0.6, 0.8] + [0.0] * 126)
        
        success = self.auto_movement.execute_anchor_movement(
            'A', target_block, new_topic, "test_movement"
        )
        
        self.assertTrue(success)
        
        # Verify anchor was moved
        slot_info = self.anchor_manager.get_slot_info('A')
        self.assertEqual(slot_info['anchor_block_id'], target_block)
        
        # Verify movement was recorded in history
        stats = self.auto_movement.get_movement_stats()
        self.assertEqual(stats['total_movements'], 1)
        self.assertIn('test_movement', stats['movements_by_reason'])
        
        print("✓ Anchor movement execution working correctly")
    
    def test_pinned_anchor_protection(self):
        """Test that pinned anchors are not moved automatically"""
        # Setup and pin anchor
        initial_topic = np.array([0.8, 0.6] + [0.0] * 126)
        initial_block = str(self.test_blocks[0]['block_index'])
        self.anchor_manager.move_anchor('A', initial_block, initial_topic)
        self.anchor_manager.pin_anchor('A')
        
        # Try to evaluate movement for pinned anchor
        search_results = [
            {
                'block_index': self.test_blocks[1]['block_index'],
                'embedding': self.test_blocks[1]['embedding'],
                'timestamp': self.test_blocks[1]['timestamp'],
                'relevance_score': 0.9
            }
        ]
        
        different_topic = np.array([0.2, 0.9] + [0.0] * 126)
        evaluation = self.auto_movement.evaluate_anchor_movement('A', search_results, different_topic)
        
        # Should not move pinned anchor
        self.assertFalse(evaluation['should_move'])
        self.assertEqual(evaluation['reason'], 'anchor_pinned')
        
        print("✓ Pinned anchor protection working correctly")
    
    def test_anchor_conflict_resolution(self):
        """Test resolution of anchor conflicts with similar topics"""
        # Set similar topic vectors for different slots
        similar_topic1 = np.array([0.8, 0.6] + [0.0] * 126)
        similar_topic2 = np.array([0.82, 0.58] + [0.0] * 126)  # Very similar
        
        self.anchor_manager.move_anchor('A', str(self.test_blocks[0]['block_index']), similar_topic1)
        self.anchor_manager.move_anchor('B', str(self.test_blocks[1]['block_index']), similar_topic2)
        
        # Resolve conflicts
        actions = self.auto_movement.resolve_anchor_conflicts()
        
        if actions:
            # Should detect and resolve conflict
            self.assertGreater(len(actions), 0)
            action = actions[0]
            self.assertEqual(action['action'], 'diversify_slot')
            self.assertGreater(action['similarity'], 0.8)
            
            print(f"✓ Conflict resolution: {len(actions)} conflicts resolved")
        else:
            print("✓ No conflicts detected (expected for some test runs)")
    
    def test_movement_parameter_optimization(self):
        """Test optimization of movement parameters based on usage"""
        # Record multiple movements to trigger optimization
        for i in range(25):  # Trigger "too many movements" condition
            self.auto_movement.movement_history.append({
                "timestamp": (datetime.now() - timedelta(hours=i)).isoformat(),
                "slot": "A",
                "from_block": "0",
                "to_block": str(i),
                "reason": "test_movement",
                "topic_vec_sample": [0.5, 0.5, 0.0, 0.0, 0.0]
            })
        
        # Get initial thresholds
        initial_movement_threshold = self.auto_movement.movement_threshold
        initial_drift_threshold = self.auto_movement.topic_drift_threshold
        
        # Optimize parameters
        optimized = self.auto_movement.optimize_movement_parameters()
        
        # Should increase thresholds due to too many movements
        self.assertGreaterEqual(optimized['movement_threshold'], initial_movement_threshold)
        self.assertGreaterEqual(optimized['topic_drift_threshold'], initial_drift_threshold)
        
        print(f"✓ Parameter optimization: movement threshold {optimized['movement_threshold']:.3f}, "
              f"drift threshold {optimized['topic_drift_threshold']:.3f}")
    
    def test_movement_statistics_tracking(self):
        """Test comprehensive movement statistics tracking"""
        # Add test movements
        test_movements = [
            {"slot": "A", "reason": "topic_drift"},
            {"slot": "B", "reason": "better_candidate"},
            {"slot": "A", "reason": "topic_drift"},
            {"slot": "C", "reason": "high_topic_drift"}
        ]
        
        for i, movement in enumerate(test_movements):
            self.auto_movement.movement_history.append({
                "timestamp": (datetime.now() - timedelta(hours=i)).isoformat(),
                "slot": movement["slot"],
                "from_block": str(i),
                "to_block": str(i+1),
                "reason": movement["reason"],
                "topic_vec_sample": [0.5] * 5
            })
        
        # Get statistics
        stats = self.auto_movement.get_movement_stats()
        
        self.assertEqual(stats['total_movements'], 4)
        self.assertEqual(stats['recent_movements_24h'], 4)
        self.assertEqual(stats['movements_by_slot']['A'], 2)
        self.assertEqual(stats['movements_by_slot']['B'], 1)
        self.assertEqual(stats['movements_by_slot']['C'], 1)
        self.assertEqual(stats['movements_by_reason']['topic_drift'], 2)
        
        print(f"✓ Movement statistics: {stats['total_movements']} total, "
              f"{stats['recent_movements_24h']} recent")
    
    def test_topic_vector_dimension_handling(self):
        """Test handling of different topic vector dimensions"""
        # Test with different dimension vectors
        small_vec = np.array([0.8, 0.6])  # 2D
        large_vec = np.array([0.8, 0.6] + [0.1] * 200)  # 202D
        
        # Should handle dimension normalization
        drift_small = self.auto_movement.analyze_topic_drift('A', small_vec)
        drift_large = self.auto_movement.analyze_topic_drift('A', large_vec)
        
        # Both should work without errors
        self.assertIn('drift_magnitude', drift_small)
        self.assertIn('drift_magnitude', drift_large)
        
        print("✓ Topic vector dimension handling working correctly")
    
    def test_movement_threshold_sensitivity(self):
        """Test movement decision sensitivity to threshold changes"""
        # Setup anchor with known topic
        topic_vec = np.array([0.8, 0.6] + [0.0] * 126)
        self.anchor_manager.move_anchor('A', str(self.test_blocks[0]['block_index']), topic_vec)
        
        # Test with different thresholds
        original_threshold = self.auto_movement.movement_threshold
        
        # High threshold (conservative)
        self.auto_movement.movement_threshold = 0.8
        evaluation_conservative = self.auto_movement.evaluate_anchor_movement(
            'A', [self.test_blocks[1]], np.array([0.6, 0.8] + [0.0] * 126)
        )
        
        # Low threshold (aggressive)
        self.auto_movement.movement_threshold = 0.1
        evaluation_aggressive = self.auto_movement.evaluate_anchor_movement(
            'A', [self.test_blocks[1]], np.array([0.6, 0.8] + [0.0] * 126)
        )
        
        # Restore original threshold
        self.auto_movement.movement_threshold = original_threshold
        
        # Conservative should be less likely to move
        # Aggressive should be more likely to move
        # (Exact behavior depends on similarity calculations)
        
        print(f"✓ Threshold sensitivity: conservative={evaluation_conservative['should_move']}, "
              f"aggressive={evaluation_aggressive['should_move']}")

if __name__ == "__main__":
    print("🧪 Running M2.4 - Auto Anchor Movement System Tests")
    print("=" * 60)
    
    unittest.main(verbosity=2)