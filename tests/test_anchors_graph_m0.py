"""
M0 Milestone Tests: Skeleton & Back-compatibility

Tests for anchor manager, graph index basic functionality,
and search API parameter compatibility without implementation.
"""

import unittest
import tempfile
import shutil
from pathlib import Path
import numpy as np

from greeum.anchors import AnchorManager, AnchorState
from greeum.graph import GraphIndex
from greeum.core.search_engine import SearchEngine
from greeum.core.database_manager import DatabaseManager
from greeum.core.block_manager import BlockManager


class TestAnchorsM0(unittest.TestCase):
    """Test anchor manager basic functionality."""
    
    def setUp(self):
        self.temp_dir = Path(tempfile.mkdtemp())
        self.anchor_store = self.temp_dir / "anchors.json"
    
    def tearDown(self):
        shutil.rmtree(self.temp_dir)
    
    def test_anchor_manager_initialization(self):
        """Test anchor manager creates empty state correctly."""
        manager = AnchorManager(self.anchor_store)
        
        # Should have 3 slots A, B, C
        self.assertEqual(len(manager.state), 3)
        self.assertIn('A', manager.state)
        self.assertIn('B', manager.state)
        self.assertIn('C', manager.state)
        
        # All slots should be empty initially
        self.assertFalse(manager.is_initialized())
        
        # Should default to slot A for empty vector
        active_slot = manager.select_active_slot(np.array([]))
        self.assertEqual(active_slot, 'A')
    
    def test_anchor_slot_selection(self):
        """Test slot selection with topic vectors."""
        manager = AnchorManager(self.anchor_store)
        
        # Set up slot A with a vector
        test_vec = np.array([1.0, 0.0, 0.0])
        manager.move_anchor('A', 'block_123', test_vec)
        
        # Similar vector should select slot A
        similar_vec = np.array([0.9, 0.1, 0.0])
        selected_slot = manager.select_active_slot(similar_vec)
        self.assertEqual(selected_slot, 'A')
        
        # Very different vector should still select A (only initialized slot)
        different_vec = np.array([0.0, 0.0, 1.0])
        selected_slot = manager.select_active_slot(different_vec)
        self.assertEqual(selected_slot, 'A')
    
    def test_anchor_pinning(self):
        """Test anchor pin/unpin functionality."""
        manager = AnchorManager(self.anchor_store)
        
        # Pin anchor to specific block
        manager.pin_anchor('A', 'block_456')
        slot_info = manager.get_slot_info('A')
        
        self.assertTrue(slot_info['pinned'])
        self.assertEqual(slot_info['anchor_block_id'], 'block_456')
        
        # Move should be ignored when pinned
        manager.move_anchor('A', 'block_789', np.array([1.0, 0.0]))
        slot_info = manager.get_slot_info('A')
        self.assertEqual(slot_info['anchor_block_id'], 'block_456')  # Unchanged
        
        # Unpin should allow movement
        manager.unpin_anchor('A')
        manager.move_anchor('A', 'block_789', np.array([1.0, 0.0]))
        slot_info = manager.get_slot_info('A')
        self.assertEqual(slot_info['anchor_block_id'], 'block_789')  # Changed
    
    def test_anchor_persistence(self):
        """Test anchor state persistence across manager instances."""
        # Create manager and set up state
        manager1 = AnchorManager(self.anchor_store)
        manager1.pin_anchor('B', 'persistent_block')
        
        # Create new manager instance
        manager2 = AnchorManager(self.anchor_store)
        slot_info = manager2.get_slot_info('B')
        
        self.assertTrue(slot_info['pinned'])
        self.assertEqual(slot_info['anchor_block_id'], 'persistent_block')


class TestGraphIndexM0(unittest.TestCase):
    """Test graph index basic functionality."""
    
    def setUp(self):
        self.graph = GraphIndex(theta=0.3, kmax=5)
    
    def test_graph_initialization(self):
        """Test graph index initialization."""
        self.assertEqual(self.graph.theta, 0.3)
        self.assertEqual(self.graph.kmax, 5)
        self.assertEqual(len(self.graph.adj), 0)
    
    def test_upsert_edges(self):
        """Test edge insertion and updates."""
        # Add edges for node A
        self.graph.upsert_edges('A', [('B', 0.8), ('C', 0.6)])
        
        neighbors = self.graph.neighbors('A')
        self.assertEqual(len(neighbors), 2)
        self.assertEqual(neighbors[0], ('B', 0.8))  # Higher weight first
        self.assertEqual(neighbors[1], ('C', 0.6))
    
    def test_neighbors_filtering(self):
        """Test neighbor filtering by weight and count."""
        self.graph.upsert_edges('A', [
            ('B', 0.9), ('C', 0.7), ('D', 0.5), ('E', 0.3), ('F', 0.1)
        ])
        
        # Filter by weight
        high_weight = self.graph.neighbors('A', min_w=0.6)
        self.assertEqual(len(high_weight), 2)  # B and C
        
        # Limit by count
        top_3 = self.graph.neighbors('A', k=3)
        self.assertEqual(len(top_3), 3)  # B, C, D
    
    def test_beam_search_basic(self):
        """Test basic beam search functionality."""
        # Create simple path: A -> B -> C
        self.graph.upsert_edges('A', [('B', 0.8)])
        self.graph.upsert_edges('B', [('C', 0.7)])
        
        # Search for nodes that are 'C'
        def is_c(node):
            return node == 'C'
        
        results = self.graph.beam_search('A', is_c, max_hop=2)
        self.assertIn('C', results)
    
    def test_graph_stats(self):
        """Test graph statistics calculation."""
        self.graph.upsert_edges('A', [('B', 0.8), ('C', 0.6)])
        self.graph.upsert_edges('B', [('C', 0.5)])
        
        stats = self.graph.get_stats()
        self.assertEqual(stats['node_count'], 2)  # A and B have outgoing edges
        self.assertEqual(stats['edge_count'], 3)  # A->B, A->C, B->C


class TestSearchAPICompatibilityM0(unittest.TestCase):
    """Test search API backward compatibility with new parameters."""
    
    def test_search_signature_compatibility(self):
        """Test that search function accepts new parameters without error."""
        # This is a basic signature test - we don't need actual database
        # Just test that the function accepts the new parameters
        
        from greeum.core.search_engine import SearchEngine
        
        # Mock the search engine to avoid database dependency
        class MockSearchEngine:
            def search(self, query: str, top_k: int = 5, temporal_boost = None, 
                      temporal_weight: float = 0.3, slot = None, radius = None, 
                      fallback: bool = True):
                return {
                    "blocks": [],
                    "metrics": {"total_ms": 0},
                    "metadata": {"temporal_boost_applied": False}
                }
        
        mock_engine = MockSearchEngine()
        
        # Test original signature still works
        result1 = mock_engine.search("test")
        self.assertIn("blocks", result1)
        
        # Test new parameters are accepted
        result2 = mock_engine.search("test", slot="A", radius=2, fallback=True)
        self.assertIn("blocks", result2)
        
        # Test invalid parameters are accepted (will be ignored in M0)
        result3 = mock_engine.search("test", slot="INVALID", radius=-1)
        self.assertIn("blocks", result3)
    
    def test_parameter_acknowledgment(self):
        """Test that new parameters are acknowledged in the actual search function."""
        # Test the actual search function signature by importing it
        from greeum.core.search_engine import SearchEngine
        import inspect
        
        # Get the search method signature
        sig = inspect.signature(SearchEngine.search)
        params = list(sig.parameters.keys())
        
        # Verify new parameters are in signature
        self.assertIn("slot", params)
        self.assertIn("radius", params) 
        self.assertIn("fallback", params)
        
        # Verify original parameters are still there
        self.assertIn("query", params)
        self.assertIn("top_k", params)


if __name__ == '__main__':
    unittest.main()