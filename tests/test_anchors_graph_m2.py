"""
M2 Milestone Tests: Near-Anchor Write & Edges

Tests for anchor-based write functionality, LTM link caching,
and edge growth metrics.
"""

import unittest
import tempfile
import shutil
import json
import time
from pathlib import Path
from unittest.mock import patch, MagicMock
import numpy as np

# Add parent to path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from greeum.api.write import AnchorBasedWriter, write, get_write_metrics
from greeum.anchors import AnchorManager
from greeum.graph import GraphIndex
from greeum.core.database_manager import DatabaseManager
from greeum.core.block_manager import BlockManager


class TestAnchorBasedWriterM2(unittest.TestCase):
    """Test anchor-based writer functionality."""
    
    def setUp(self):
        self.temp_dir = Path(tempfile.mkdtemp())
        self.data_dir = self.temp_dir / "data"
        self.data_dir.mkdir()
        
        # Create test database with sample blocks
        self.db_path = self.temp_dir / "test.db"
        self.db_manager = DatabaseManager(str(self.db_path))
        self.block_manager = BlockManager(self.db_manager)
        
        # Add initial test blocks
        self.test_blocks = []
        test_data = [
            ("Python programming concepts", ["Python", "programming"], ["dev", "lang"]),
            ("Machine learning algorithms", ["ML", "algorithms"], ["ai", "research"]),
            ("Web development with React", ["React", "web"], ["frontend", "js"])
        ]
        
        for content, keywords, tags in test_data:
            embedding = np.random.normal(0, 1, 128).tolist()
            block = self.block_manager.add_block(
                context=content,
                keywords=keywords,
                tags=tags,
                embedding=embedding,
                importance=0.6
            )
            if block:
                self.test_blocks.append(block)
        
        # Create mock anchor and graph files
        self._create_test_anchor_graph_files()
    
    def tearDown(self):
        shutil.rmtree(self.temp_dir)
    
    def _create_test_anchor_graph_files(self):
        """Create test anchor and graph files."""
        # Create anchor file
        anchor_path = self.data_dir / "anchors.json"
        anchor_data = {
            "version": 1,
            "slots": [
                {
                    "slot": "A",
                    "anchor_block_id": "0",
                    "topic_vec": [0.8, 0.2] + [0.0] * 126,  # 128-dim
                    "summary": "Python programming",
                    "last_used_ts": int(time.time()),
                    "hop_budget": 2,
                    "pinned": False
                },
                {
                    "slot": "B",
                    "anchor_block_id": "1", 
                    "topic_vec": [0.3, 0.8] + [0.0] * 126,  # 128-dim
                    "summary": "Machine learning",
                    "last_used_ts": int(time.time()) - 1800,
                    "hop_budget": 2,
                    "pinned": False
                },
                {
                    "slot": "C",
                    "anchor_block_id": "2",
                    "topic_vec": [0.1, 0.3] + [0.0] * 126,  # 128-dim  
                    "summary": "Web development",
                    "last_used_ts": int(time.time()) - 3600,
                    "hop_budget": 2,
                    "pinned": True  # Pinned slot
                }
            ],
            "updated_at": int(time.time())
        }
        
        with open(anchor_path, 'w') as f:
            json.dump(anchor_data, f)
        
        # Create graph file
        graph_path = self.data_dir / "graph_snapshot.jsonl"
        graph_data = {
            "version": 1,
            "nodes": ["0", "1", "2"],
            "edges": [
                {"u": "0", "v": "1", "w": 0.7, "src": ["sim"]},
                {"u": "1", "v": "2", "w": 0.5, "src": ["sim"]},
                {"u": "0", "v": "2", "w": 0.4, "src": ["temp"]}
            ],
            "built_at": int(time.time()),
            "params": {"theta": 0.35, "kmax": 32, "alpha": 0.7, "beta": 0.2, "gamma": 0.1}
        }
        
        with open(graph_path, 'w') as f:
            json.dump(graph_data, f)
    
    def test_anchor_writer_initialization(self):
        """Test writer initialization."""
        writer = AnchorBasedWriter(self.db_manager)
        
        self.assertIsNotNone(writer.db_manager)
        self.assertIsNotNone(writer.block_manager)
        self.assertEqual(writer.anchor_moves_count, 0)
        self.assertEqual(writer.edges_added_count, 0)
    
    @patch('greeum.api.write.get_embedding')
    def test_write_without_anchors(self, mock_embed):
        """Test write operation without anchor/graph files."""
        mock_embed.return_value = [0.1] * 128
        
        # Remove anchor/graph files to test fallback
        (self.data_dir / "anchors.json").unlink(missing_ok=True)
        (self.data_dir / "graph_snapshot.jsonl").unlink(missing_ok=True)
        
        writer = AnchorBasedWriter(self.db_manager)
        
        # Should work without errors and return block ID
        block_id = writer.write("New memory without anchors")
        self.assertIsNotNone(block_id)
        
        # Verify block was created
        block = self.block_manager.get_block_by_index(int(block_id))
        self.assertIsNotNone(block)
        self.assertIn("New memory without anchors", block['context'])
    
    @patch('greeum.api.write.get_embedding')
    @patch('pathlib.Path.exists')
    def test_write_with_anchors(self, mock_exists, mock_embed):
        """Test write operation with anchor/graph system."""
        mock_embed.return_value = [0.8, 0.2] + [0.0] * 126  # Similar to slot A
        mock_exists.return_value = True  # Files exist
        
        writer = AnchorBasedWriter(self.db_manager)
        
        # Patch file paths to use our test data
        with patch('pathlib.Path') as mock_path:
            def path_side_effect(path_str):
                if "anchors.json" in str(path_str):
                    return self.data_dir / "anchors.json"
                elif "graph_snapshot.jsonl" in str(path_str):
                    return self.data_dir / "graph_snapshot.jsonl"
                else:
                    mock_obj = MagicMock()
                    mock_obj.exists.return_value = True
                    return mock_obj
            
            mock_path.side_effect = path_side_effect
            
            # Should select slot A and create block
            block_id = writer.write(
                "Advanced Python programming techniques",
                keywords=["Python", "advanced"],
                tags=["programming", "tutorial"]
            )
            
            self.assertIsNotNone(block_id)
            
            # Check metrics were updated
            metrics = writer.get_metrics()
            self.assertIn("anchor_moves_per_min", metrics)
            self.assertIn("edge_growth_rate", metrics)
    
    def test_find_best_neighbor(self):
        """Test neighbor similarity calculation."""
        writer = AnchorBasedWriter(self.db_manager)
        
        # Mock neighbors with different IDs
        neighbors = [("0", 0.8), ("1", 0.6), ("2", 0.4)]
        query_vec = [0.8, 0.2] + [0.0] * 126
        
        best_neighbor = writer._find_best_neighbor(query_vec, neighbors)
        
        # Should return one of the neighbors
        self.assertIn(best_neighbor, neighbors)
        self.assertIsInstance(best_neighbor[0], str)
        self.assertIsInstance(best_neighbor[1], float)
    
    def test_calculate_edge_weight(self):
        """Test edge weight calculation."""
        writer = AnchorBasedWriter(self.db_manager)
        
        query_vec = [0.8, 0.2] + [0.0] * 126
        target_id = "0"  # First test block
        base_weight = 0.7
        
        edge_weight = writer._calculate_edge_weight(query_vec, target_id, base_weight)
        
        # Should return reasonable weight value
        self.assertGreaterEqual(edge_weight, 0.1)
        self.assertLessEqual(edge_weight, 1.0)
    
    def test_metrics_tracking(self):
        """Test metrics collection."""
        writer = AnchorBasedWriter(self.db_manager)
        
        # Simulate some operations
        writer.anchor_moves_count = 5
        writer.edges_added_count = 20
        
        metrics = writer.get_metrics()
        
        # Check all required metrics are present
        required_metrics = [
            "anchor_moves_per_min", "edge_growth_rate", 
            "total_anchor_moves", "total_edges_added", "elapsed_minutes"
        ]
        
        for metric in required_metrics:
            self.assertIn(metric, metrics)
            self.assertIsInstance(metrics[metric], (int, float))


class TestLTMLinksCache(unittest.TestCase):
    """Test LTM links cache functionality."""
    
    def setUp(self):
        self.temp_dir = Path(tempfile.mkdtemp())
        self.db_path = self.temp_dir / "links_test.db"
        self.db_manager = DatabaseManager(str(self.db_path))
        self.block_manager = BlockManager(self.db_manager)
        
        # Create test block
        self.test_block = self.block_manager.add_block(
            context="Test block for links",
            keywords=["test"],
            tags=["links"],
            embedding=[0.1] * 128,
            importance=0.5
        )
    
    def tearDown(self):
        shutil.rmtree(self.temp_dir)
    
    def test_update_block_links(self):
        """Test updating block neighbor links cache."""
        block_index = self.test_block['block_index']
        
        # Test links data
        neighbors = [
            {"id": "blk_123", "w": 0.8},
            {"id": "blk_456", "w": 0.6},
            {"id": "blk_789", "w": 0.4}
        ]
        
        # Update links
        success = self.block_manager.update_block_links(block_index, neighbors)
        self.assertTrue(success)
        
        # Retrieve and verify
        cached_neighbors = self.block_manager.get_block_neighbors(block_index)
        self.assertEqual(len(cached_neighbors), 3)
        self.assertEqual(cached_neighbors[0]["id"], "blk_123")
        self.assertEqual(cached_neighbors[0]["w"], 0.8)
    
    def test_get_block_neighbors_empty(self):
        """Test getting neighbors for block without cache."""
        block_index = self.test_block['block_index']
        
        # Should return empty list initially
        neighbors = self.block_manager.get_block_neighbors(block_index)
        self.assertEqual(neighbors, [])
    
    def test_get_nonexistent_block_neighbors(self):
        """Test getting neighbors for nonexistent block."""
        neighbors = self.block_manager.get_block_neighbors(99999)
        self.assertEqual(neighbors, [])


class TestWriteAPIFunctions(unittest.TestCase):
    """Test top-level write API functions."""
    
    def setUp(self):
        self.temp_dir = Path(tempfile.mkdtemp())
    
    def tearDown(self):
        shutil.rmtree(self.temp_dir)
    
    @patch('greeum.api.write.get_embedding')
    def test_write_api_function(self, mock_embed):
        """Test main write API function."""
        mock_embed.return_value = [0.1] * 128
        
        with patch('greeum.api.write.AnchorBasedWriter') as mock_writer_class:
            mock_writer = MagicMock()
            mock_writer.write.return_value = "test_block_123"
            mock_writer_class.return_value = mock_writer
            
            result = write(
                text="Test memory content",
                slot="A",
                keywords=["test"],
                tags=["api"],
                importance=0.7
            )
            
            # Verify API was called correctly
            self.assertEqual(result, "test_block_123")
            mock_writer.write.assert_called_once()
            
            call_args = mock_writer.write.call_args
            self.assertEqual(call_args.kwargs['text'], "Test memory content")
            self.assertEqual(call_args.kwargs['slot'], "A")
            self.assertEqual(call_args.kwargs['keywords'], ["test"])
            self.assertEqual(call_args.kwargs['importance'], 0.7)
    
    def test_get_write_metrics_api(self):
        """Test write metrics API function."""
        with patch('greeum.api.write.get_writer') as mock_get_writer:
            mock_writer = MagicMock()
            mock_writer.get_metrics.return_value = {
                "anchor_moves_per_min": 2.5,
                "edge_growth_rate": 10.0
            }
            mock_get_writer.return_value = mock_writer
            
            metrics = get_write_metrics()
            
            self.assertIn("anchor_moves_per_min", metrics)
            self.assertIn("edge_growth_rate", metrics)
            self.assertEqual(metrics["anchor_moves_per_min"], 2.5)


class TestM2Integration(unittest.TestCase):
    """Integration tests for M2 milestone."""
    
    def setUp(self):
        self.temp_dir = Path(tempfile.mkdtemp())
        self.data_dir = self.temp_dir / "data"
        self.data_dir.mkdir()
        
        # Create minimal test environment
        self.db_path = self.temp_dir / "integration.db"
        self.db_manager = DatabaseManager(str(self.db_path))
        self.block_manager = BlockManager(self.db_manager)
    
    def tearDown(self):
        shutil.rmtree(self.temp_dir)
    
    @patch('greeum.api.write.get_embedding')
    def test_complete_write_workflow(self, mock_embed):
        """Test complete write workflow from API to storage."""
        mock_embed.return_value = [0.5] * 128
        
        # Initial state: no anchors/graph
        writer = AnchorBasedWriter(self.db_manager)
        initial_metrics = writer.get_metrics()
        
        # Write new memory
        block_id = writer.write(
            "Complete integration test memory",
            keywords=["integration", "test"],
            tags=["m2", "workflow"],
            importance=0.8
        )
        
        # Verify block was created
        self.assertIsNotNone(block_id)
        block = self.block_manager.get_block_by_index(int(block_id))
        self.assertIsNotNone(block)
        self.assertEqual(block['context'], "Complete integration test memory")
        self.assertEqual(block['keywords'], ["integration", "test"])
        self.assertEqual(block['importance'], 0.8)
        
        # Check metrics were updated
        final_metrics = writer.get_metrics()
        self.assertGreaterEqual(final_metrics['elapsed_minutes'], initial_metrics['elapsed_minutes'])
    
    def test_error_handling(self):
        """Test error handling in write operations."""
        writer = AnchorBasedWriter(self.db_manager)
        
        with patch('greeum.api.write.get_embedding') as mock_embed:
            mock_embed.return_value = [0.1] * 128
            
            # Test with invalid parameters
            with patch.object(writer.block_manager, 'add_block') as mock_add_block:
                mock_add_block.return_value = None  # Simulate failure
                
                # Should raise RuntimeError when block creation fails
                with self.assertRaises(RuntimeError):
                    writer.write("This should fail")


if __name__ == '__main__':
    # Run tests with verbose output
    unittest.main(verbosity=2)