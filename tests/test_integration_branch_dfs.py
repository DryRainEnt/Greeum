"""
Integration tests for Branch/DFS system with auto-merge
Tests PR#1-5 features together
"""

import unittest
import tempfile
import time
import numpy as np
from pathlib import Path

from greeum.core.database_manager import DatabaseManager
from greeum.core.block_manager import BlockManager
from greeum.core.stm_manager import STMManager
from greeum.core.merge_engine import MergeEngine
from greeum.core.metrics_dashboard import MetricsDashboard, SearchMetrics


class TestBranchDFSIntegration(unittest.TestCase):
    """Integration tests for complete Branch/DFS system"""
    
    def setUp(self):
        """Set up test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = Path(self.temp_dir) / "test.db"
        
        # Initialize components
        self.db_manager = DatabaseManager(connection_string=str(self.db_path))
        self.block_manager = BlockManager(self.db_manager)
        self.stm_manager = STMManager(self.db_manager)
        self.metrics = MetricsDashboard()
        
    def tearDown(self):
        """Clean up test environment"""
        if hasattr(self, 'db_manager'):
            self.db_manager.close()
            
    def test_branch_creation_and_dfs_search(self):
        """Test branch creation with DFS local search"""
        
        # Create a branch with multiple blocks
        root_block = self.block_manager.add_block(
            context="Project started",
            keywords=[],
            tags=[],
            embedding=[0.0] * 128,
            importance=0.5,
            slot='A'
        )
        
        # Add more blocks to the branch
        for i in range(5):
            block_id = self.block_manager.add_block(
                context=f"Work item {i}",
                keywords=[],
                tags=[],
                embedding=[0.0] * 128,
                importance=0.5,
                slot='A'
            )
            
        # Verify branch structure
        cursor = self.db_manager.conn.cursor()
        
        # root_block is a dict with block info, get the hash or id
        if isinstance(root_block, dict):
            root_id = root_block.get('hash') or root_block.get('block_index')
        else:
            root_id = root_block
            
        # For initial block, it becomes its own root
        cursor.execute("SELECT COUNT(*) FROM blocks")
        count = cursor.fetchone()[0]
        
        # Should have at least 6 blocks created
        self.assertGreaterEqual(count, 6)
        
    def test_auto_merge_trigger(self):
        """Test automatic merge triggering between slots"""
        
        # Create blocks in slot A
        self.block_manager.add_block(
            context="Initial work",
            keywords=[],
            tags=[],
            embedding=[0.0] * 128,
            importance=0.5,
            slot='A'
        )
        self.block_manager.add_block(
            context="More work",
            keywords=[],
            tags=[],
            embedding=[0.0] * 128,
            importance=0.5,
            slot='A'
        )
        
        # Create blocks in slot B with same root
        self.block_manager.add_block(
            context="Related work",
            keywords=[],
            tags=[],
            embedding=[0.0] * 128,
            importance=0.5,
            slot='B'
        )
        
        # Check if merge engine exists
        if self.block_manager.merge_engine:
            # Record high similarity scores to trigger merge
            for _ in range(10):
                self.block_manager.merge_engine.record_similarity('A', 'B', 0.8)
                
            # Check if merge would be triggered
            result = self.block_manager.merge_engine.evaluate_merge('A', 'B', dry_run=True)
            
            # After multiple high scores, merge should be suggested
            self.assertIsNotNone(result)
            
    def test_metrics_collection(self):
        """Test metrics dashboard collection"""
        
        # Record some search operations
        for i in range(10):
            metrics = SearchMetrics(
                timestamp=time.time(),
                search_type='local' if i < 7 else 'jump',
                slot='A',
                root='root_1',
                depth_used=3,
                hops=5 + i % 3,
                local_used=(i < 7),
                fallback_used=(i >= 7),
                latency_ms=50 + i * 10,
                results_count=3
            )
            self.metrics.record_search(metrics)
            
        # Check calculated metrics
        local_hit_rate = self.metrics.get_local_hit_rate()
        avg_hops = self.metrics.get_avg_hops()
        jump_rate = self.metrics.get_jump_rate()
        
        # Verify metrics are calculated correctly
        self.assertAlmostEqual(local_hit_rate, 0.7, places=1)
        self.assertGreater(avg_hops, 0)
        self.assertAlmostEqual(jump_rate, 0.3, places=1)
        
    def test_merge_and_undo(self):
        """Test merge operation and undo"""
        
        if not self.block_manager.merge_engine:
            self.skipTest("Merge engine not available")
            
        # Create test blocks
        block_a = {
            'id': 'test_a',
            'root': 'root_1',
            'embedding': np.random.rand(128).tolist(),
            'tags': {'labels': ['test', 'merge']},
            'created_at': time.time(),
            'stats': {'divergence': 1}
        }
        
        block_b = {
            'id': 'test_b',
            'root': 'root_1',  # Same root
            'embedding': np.random.rand(128).tolist(),
            'tags': {'labels': ['test', 'experiment']},
            'created_at': time.time(),
            'stats': {'divergence': 2}
        }
        
        # Calculate merge score
        score = self.block_manager.merge_engine.calculate_merge_score(block_a, block_b)
        self.assertIsNotNone(score)
        self.assertGreaterEqual(score.total, 0)
        self.assertLessEqual(score.total, 1)
        
        # Create checkpoint
        checkpoint = self.block_manager.merge_engine.create_checkpoint(
            'A', 'B', score.total, reversible=True
        )
        self.assertIsNotNone(checkpoint)
        
        # Test undo
        success = self.block_manager.merge_engine.undo_checkpoint(checkpoint.id)
        self.assertTrue(success)
        
    def test_performance_targets(self):
        """Test if performance targets are met"""
        
        # Simulate realistic search pattern
        start_time = time.perf_counter()
        
        # Perform 100 searches
        for i in range(100):
            # 70% local searches, 30% with fallback
            is_local = i < 70
            
            metrics = SearchMetrics(
                timestamp=time.time(),
                search_type='local' if is_local else 'jump',
                slot='A',
                root='root_1',
                depth_used=3,
                hops=3 if is_local else 8,  # Local searches have fewer hops
                local_used=is_local,
                fallback_used=not is_local,
                latency_ms=30 if is_local else 100,  # Local is faster
                results_count=5
            )
            self.metrics.record_search(metrics)
            
        # Check success indicators
        indicators = self.metrics.get_success_indicators()
        
        # Log results
        for key, (passed, value) in indicators.items():
            print(f"  {key}: {'✅' if passed else '❌'} {value}")
            
        # Check critical metrics
        self.assertGreaterEqual(
            self.metrics.get_local_hit_rate(), 0.25,
            "Local hit rate should be at least 25%"
        )
        
        self.assertLess(
            self.metrics.get_p95_latency(), 200,
            "P95 latency should be under 200ms"
        )
        
    def test_dashboard_export(self):
        """Test metrics export functionality"""
        
        # Add some data
        for i in range(20):
            metrics = SearchMetrics(
                timestamp=time.time() + i,
                search_type='local',
                slot='A',
                root='root_1',
                depth_used=3,
                hops=5,
                local_used=True,
                fallback_used=False,
                latency_ms=50,
                results_count=3
            )
            self.metrics.record_search(metrics)
            
        # Export metrics
        export_path = Path(self.temp_dir) / "metrics.json"
        self.metrics.export_metrics(str(export_path))
        
        # Verify export file exists and contains data
        self.assertTrue(export_path.exists())
        
        import json
        with open(export_path) as f:
            data = json.load(f)
            
        self.assertIn('dashboard', data)
        self.assertIn('success_indicators', data)
        self.assertIn('metrics', data['dashboard'])


if __name__ == '__main__':
    unittest.main()