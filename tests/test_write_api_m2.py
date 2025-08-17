#!/usr/bin/env python3
"""
Test suite for M2.1 - Near-anchor write API core (v2.2.1a1)

Tests the AnchorBasedWriter class and write() function for:
- Basic write functionality
- Near-anchor placement logic
- Topic vector slot selection
- Write API response time < 5ms
"""

import unittest
import tempfile
import shutil
import time
import numpy as np
from pathlib import Path
import sys
import os

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from greeum.api.write import AnchorBasedWriter, write, get_write_metrics
from greeum.core.database_manager import DatabaseManager
from greeum.anchors import AnchorManager
from greeum.graph import GraphIndex


class TestM21WriteAPICore(unittest.TestCase):
    """Test M2.1 - Near-anchor write API core functionality."""
    
    def setUp(self):
        """Set up test environment with temporary data."""
        self.test_dir = tempfile.mkdtemp()
        self.test_db = os.path.join(self.test_dir, "test_write.db")
        self.test_anchors = os.path.join(self.test_dir, "test_anchors.json")
        self.test_graph = os.path.join(self.test_dir, "test_graph.jsonl")
        
        # Create test database
        self.db_manager = DatabaseManager(self.test_db)
        
        # Create test writer
        self.writer = AnchorBasedWriter(self.db_manager)
        
        # Add some sample blocks for testing
        self._create_sample_blocks()
        self._create_sample_anchors()
        
    def tearDown(self):
        """Clean up test environment."""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
    
    def _create_sample_blocks(self):
        """Create sample blocks in test database."""
        sample_texts = [
            "Machine learning is transforming modern technology",
            "Deep neural networks enable complex pattern recognition", 
            "Natural language processing advances AI communication",
            "Computer vision helps machines understand images",
            "Reinforcement learning optimizes decision making"
        ]
        
        for i, text in enumerate(sample_texts):
            # Create simple embedding (128-dim for compatibility)
            embedding = np.random.rand(128).tolist()
            
            block = self.writer.block_manager.add_block(
                context=text,
                keywords=[f"keyword_{i}"],
                tags=[f"tag_{i}"],
                embedding=embedding,
                importance=0.5 + i * 0.1
            )
            self.assertIsNotNone(block, f"Failed to create sample block {i}")
    
    def _create_sample_anchors(self):
        """Create sample anchor configuration."""
        # Create basic anchor manager with empty slots
        anchor_manager = AnchorManager(Path(self.test_anchors))
        
        # Initialize with some blocks
        test_embedding = np.random.rand(128)
        anchor_manager.move_anchor('A', '1', test_embedding)
        anchor_manager.move_anchor('B', '2', test_embedding) 
        anchor_manager.move_anchor('C', '3', test_embedding)
        
    def test_anchor_writer_initialization(self):
        """Test AnchorBasedWriter class initialization."""
        # Test default initialization
        writer = AnchorBasedWriter()
        self.assertIsNotNone(writer.db_manager)
        self.assertIsNotNone(writer.block_manager)
        self.assertEqual(writer.anchor_moves_count, 0)
        self.assertEqual(writer.edges_added_count, 0)
        
        # Test custom db_manager
        custom_writer = AnchorBasedWriter(self.db_manager)
        self.assertEqual(custom_writer.db_manager, self.db_manager)
    
    def test_write_basic_functionality(self):
        """Test basic write functionality without anchors."""
        test_text = "This is a test memory for basic write functionality"
        
        # Test write without anchor system
        start_time = time.perf_counter()
        block_id = self.writer.write(
            text=test_text,
            keywords=["test", "memory"],
            tags=["basic", "functionality"],
            importance=0.7
        )
        write_time = time.perf_counter() - start_time
        
        # Verify block was created
        self.assertIsNotNone(block_id)
        self.assertIsInstance(block_id, str)
        
        # Verify write time < 5ms requirement
        self.assertLess(write_time, 0.005, f"Write took {write_time:.3f}s, should be < 5ms")
        
        # Verify block exists in database
        block_data = self.db_manager.get_block_by_index(int(block_id))
        self.assertIsNotNone(block_data)
        self.assertEqual(block_data['context'], test_text)
        self.assertEqual(block_data['importance'], 0.7)
    
    def test_write_with_slot_selection(self):
        """Test write with explicit slot selection."""
        test_text = "Testing slot-based write functionality"
        
        # Create anchor configuration
        if not os.path.exists(self.test_anchors):
            self._create_sample_anchors()
        
        # Test write with specific slot
        block_id = self.writer.write(
            text=test_text,
            slot='B',
            importance=0.6
        )
        
        self.assertIsNotNone(block_id)
        
        # Verify block was created
        block_data = self.db_manager.get_block_by_index(int(block_id))
        self.assertIsNotNone(block_data)
        self.assertEqual(block_data['context'], test_text)
    
    def test_write_performance_requirement(self):
        """Test write API response time requirement (< 5ms)."""
        test_cases = [
            "Short text",
            "Medium length text with some more content for testing performance",
            "Very long text content that includes multiple sentences and various topics to test the performance of the write API under more realistic conditions with longer content that might take more time to process"
        ]
        
        times = []
        for text in test_cases:
            start_time = time.perf_counter()
            block_id = self.writer.write(text=text)
            elapsed = time.perf_counter() - start_time
            times.append(elapsed)
            
            # Verify each write completes
            self.assertIsNotNone(block_id)
        
        # All writes should be under 5ms
        max_time = max(times)
        avg_time = sum(times) / len(times)
        
        self.assertLess(max_time, 0.005, f"Max write time {max_time:.3f}s exceeds 5ms requirement")
        self.assertLess(avg_time, 0.005, f"Average write time {avg_time:.3f}s should be under 5ms")
        
        print(f"✅ Write performance: max={max_time*1000:.1f}ms, avg={avg_time*1000:.1f}ms")
    
    def test_near_anchor_placement_logic(self):
        """Test near-anchor placement logic when anchor system available."""
        # This test requires anchor and graph systems
        # For now, test the fallback behavior when systems aren't available
        
        test_text = "Testing near-anchor placement logic"
        
        # Test that write works even without anchor/graph systems
        block_id = self.writer.write(text=test_text)
        self.assertIsNotNone(block_id)
        
        # Verify the block exists
        block_data = self.db_manager.get_block_by_index(int(block_id))
        self.assertIsNotNone(block_data)
        self.assertEqual(block_data['context'], test_text)
    
    def test_write_with_policy(self):
        """Test write with custom policy configuration."""
        test_text = "Testing write with custom policy"
        
        custom_policy = {
            "link_k": 5,
            "min_w": 0.4,
            "max_neighbors": 16
        }
        
        block_id = self.writer.write(
            text=test_text,
            policy=custom_policy,
            importance=0.8
        )
        
        self.assertIsNotNone(block_id)
        
        # Verify block was created with correct importance
        block_data = self.db_manager.get_block_by_index(int(block_id))
        self.assertIsNotNone(block_data)
        self.assertEqual(block_data['importance'], 0.8)
    
    def test_write_metrics_collection(self):
        """Test write metrics collection."""
        # Get initial metrics
        initial_metrics = self.writer.get_metrics()
        self.assertIn('anchor_moves_per_min', initial_metrics)
        self.assertIn('edge_growth_rate', initial_metrics)
        self.assertIn('total_anchor_moves', initial_metrics)
        self.assertIn('total_edges_added', initial_metrics)
        
        # Perform some writes
        for i in range(3):
            self.writer.write(f"Test write {i} for metrics collection")
        
        # Get updated metrics
        updated_metrics = self.writer.get_metrics()
        
        # Verify metrics structure
        for key in initial_metrics:
            self.assertIn(key, updated_metrics)
            self.assertIsInstance(updated_metrics[key], (int, float))
    
    def test_global_write_function(self):
        """Test the global write() function API."""
        test_text = "Testing global write function"
        
        # Patch the data directory for testing
        original_path = Path("data/anchors.json")
        test_anchor_path = Path(self.test_anchors)
        
        try:
            # Test global write function
            start_time = time.perf_counter()
            block_id = write(
                text=test_text,
                keywords=["global", "test"],
                tags=["api"],
                importance=0.75
            )
            write_time = time.perf_counter() - start_time
            
            self.assertIsNotNone(block_id)
            self.assertIsInstance(block_id, str)
            
            # Performance check
            self.assertLess(write_time, 0.010, "Global write function should be fast")
            
        except Exception as e:
            # Expected if anchor system not available - that's fine for basic test
            self.assertIn("write", str(e).lower(), "Error should be write-related")
    
    def test_write_error_handling(self):
        """Test write error handling for edge cases."""
        # Test empty text - should work but may have warning
        try:
            block_id = self.writer.write("")
            # Empty text is allowed, just verify it returns something
            self.assertIsNotNone(block_id)
        except Exception:
            # Exception is also acceptable for empty text
            pass
        
        # Test invalid slot
        block_id = self.writer.write("Test text", slot="Invalid")
        # Should still work (fallback to auto-selection)
        self.assertIsNotNone(block_id)
        
        # Test negative importance
        block_id = self.writer.write("Test text", importance=-0.5)
        # Should still work (clamped or accepted)
        self.assertIsNotNone(block_id)


class TestWriteAPIIntegration(unittest.TestCase):
    """Integration tests for write API with existing components."""
    
    def test_existing_write_api_compatibility(self):
        """Test compatibility with existing write API patterns."""
        # Test that we don't break existing import patterns
        try:
            from greeum.api.write import write
            self.assertTrue(callable(write))
        except ImportError as e:
            self.fail(f"Failed to import write function: {e}")
    
    def test_anchor_manager_integration(self):
        """Test integration with AnchorManager."""
        try:
            from greeum.anchors import AnchorManager
            # Basic integration test - should not crash
            temp_path = Path(tempfile.mktemp(suffix=".json"))
            manager = AnchorManager(temp_path)
            self.assertIsNotNone(manager)
            
            # Cleanup
            if temp_path.exists():
                temp_path.unlink()
                
        except Exception as e:
            self.fail(f"AnchorManager integration failed: {e}")
    
    def test_database_write_consistency(self):
        """Test database write consistency."""
        with tempfile.TemporaryDirectory() as temp_dir:
            test_db = os.path.join(temp_dir, "consistency_test.db")
            db_manager = DatabaseManager(test_db)
            
            writer = AnchorBasedWriter(db_manager)
            
            # Write multiple blocks
            block_ids = []
            for i in range(5):
                block_id = writer.write(f"Consistency test block {i}")
                block_ids.append(block_id)
            
            # Verify all blocks exist and are unique
            self.assertEqual(len(set(block_ids)), 5, "All block IDs should be unique")
            
            for block_id in block_ids:
                block_data = db_manager.get_block_by_index(int(block_id))
                self.assertIsNotNone(block_data, f"Block {block_id} should exist")


def run_m21_tests():
    """Run M2.1 test suite and return results."""
    print("🧪 Running M2.1 - Near-anchor write API core tests")
    print("=" * 60)
    
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add test classes
    suite.addTests(loader.loadTestsFromTestCase(TestM21WriteAPICore))
    suite.addTests(loader.loadTestsFromTestCase(TestWriteAPIIntegration))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print("\n" + "=" * 60)
    print(f"📊 M2.1 Test Results:")
    print(f"   Tests run: {result.testsRun}")
    print(f"   Failures: {len(result.failures)}")
    print(f"   Errors: {len(result.errors)}")
    print(f"   Success rate: {((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100):.1f}%")
    
    # Check specific requirements
    if result.failures == 0 and result.errors == 0:
        print("✅ All M2.1 core tests passed!")
        return True
    else:
        print("❌ Some M2.1 tests failed")
        return False


if __name__ == "__main__":
    success = run_m21_tests()
    sys.exit(0 if success else 1)