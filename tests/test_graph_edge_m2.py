"""
Test suite for M2.2 - Graph edge management functionality
"""

import unittest
import time
import tempfile
from pathlib import Path
from greeum.graph import GraphIndex
from greeum.core.metrics import get_edge_count

class TestM22GraphEdgeManagement(unittest.TestCase):
    def setUp(self):
        """Set up test environment"""
        self.graph = GraphIndex(theta=0.1, kmax=10)
        
    def test_edge_upsert_performance_requirement(self):
        """Test edge upsert operation performance < 2ms"""
        # Prepare test data - batch edge operations
        edge_data = [
            ("node1", [("node2", 0.8), ("node3", 0.6), ("node4", 0.4)]),
            ("node2", [("node1", 0.8), ("node5", 0.7)]),
            ("node3", [("node1", 0.6), ("node6", 0.5)]),
        ]
        
        start_time = time.perf_counter()
        
        # Perform edge upserts
        for u, neighs in edge_data:
            self.graph.upsert_edges(u, neighs)
        
        end_time = time.perf_counter()
        operation_time_ms = (end_time - start_time) * 1000
        
        # Performance requirement: < 2ms for batch upsert
        self.assertLess(operation_time_ms, 2.0, 
                       f"Edge upsert took {operation_time_ms:.2f}ms, should be < 2ms")
        
        print(f"✓ Edge upsert performance: {operation_time_ms:.2f}ms")
    
    def test_edge_weight_merge_logic(self):
        """Test edge weight merging takes maximum value"""
        # Insert initial edges
        self.graph.upsert_edges("A", [("B", 0.5), ("C", 0.7)])
        
        # Update with higher weight for B, lower for C
        self.graph.upsert_edges("A", [("B", 0.8), ("C", 0.3), ("D", 0.6)])
        
        neighbors = self.graph.neighbors("A")
        neighbor_dict = {v: w for v, w in neighbors}
        
        # Should take maximum weights
        self.assertEqual(neighbor_dict["B"], 0.8)  # max(0.5, 0.8)
        self.assertEqual(neighbor_dict["C"], 0.7)  # max(0.7, 0.3)
        self.assertEqual(neighbor_dict["D"], 0.6)  # new edge
        
        print("✓ Edge weight merge logic working correctly")
    
    def test_edge_theta_pruning(self):
        """Test edge pruning by theta threshold"""
        # Use strict theta for testing
        strict_graph = GraphIndex(theta=0.5, kmax=10)
        
        # Insert edges with mixed weights
        strict_graph.upsert_edges("A", [
            ("B", 0.8),  # Above theta
            ("C", 0.6),  # Above theta
            ("D", 0.3),  # Below theta - should be pruned
            ("E", 0.1)   # Below theta - should be pruned
        ])
        
        neighbors = strict_graph.neighbors("A")
        neighbor_ids = [v for v, w in neighbors]
        
        # Only B and C should remain
        self.assertIn("B", neighbor_ids)
        self.assertIn("C", neighbor_ids)
        self.assertNotIn("D", neighbor_ids)
        self.assertNotIn("E", neighbor_ids)
        
        print("✓ Edge theta pruning working correctly")
    
    def test_edge_kmax_limitation(self):
        """Test edge count limitation by kmax"""
        # Use small kmax for testing
        limited_graph = GraphIndex(theta=0.0, kmax=3)
        
        # Insert more edges than kmax - note: i starts from 0, so weights are 0.9, 0.8, 0.7, 0.6, 0.5, 0.4, 0.3
        edges = [(f"node{i}", 0.9 - i*0.1) for i in range(0, 7)]  # 7 edges
        limited_graph.upsert_edges("A", edges)
        
        neighbors = limited_graph.neighbors("A")
        
        # Should only keep top 3 by weight
        self.assertEqual(len(neighbors), 3)
        
        # Should be sorted by weight descending
        weights = [w for v, w in neighbors]
        self.assertEqual(weights, sorted(weights, reverse=True))
        
        # Check top 3 highest weights are kept (0.9, 0.8, 0.7)
        expected_weights = [0.9, 0.8, 0.7]
        self.assertEqual(weights, expected_weights)
        
        print("✓ Edge kmax limitation working correctly")
    
    def test_bidirectional_edge_management(self):
        """Test managing bidirectional edges with consistent weights"""
        # Add edge A->B
        self.graph.upsert_edges("A", [("B", 0.7)])
        
        # Add reverse edge B->A with same weight
        self.graph.upsert_edges("B", [("A", 0.7)])
        
        # Verify both directions exist
        a_neighbors = self.graph.neighbors("A")
        b_neighbors = self.graph.neighbors("B")
        
        a_neighbor_dict = {v: w for v, w in a_neighbors}
        b_neighbor_dict = {v: w for v, w in b_neighbors}
        
        self.assertEqual(a_neighbor_dict.get("B"), 0.7)
        self.assertEqual(b_neighbor_dict.get("A"), 0.7)
        
        print("✓ Bidirectional edge management working correctly")
    
    def test_edge_count_metrics_update(self):
        """Test edge count metrics are properly updated"""
        initial_count = get_edge_count()
        
        # Add several edges
        self.graph.upsert_edges("A", [("B", 0.5), ("C", 0.6)])
        self.graph.upsert_edges("B", [("C", 0.7), ("D", 0.8)])
        
        # Check metrics were updated
        updated_count = get_edge_count()
        self.assertGreater(updated_count, initial_count)
        
        # Check graph stats
        stats = self.graph.get_stats()
        self.assertEqual(stats["edge_count"], updated_count)
        self.assertGreater(stats["node_count"], 0)
        
        print(f"✓ Edge count metrics: {stats['edge_count']} edges, {stats['node_count']} nodes")
    
    def test_edge_removal_via_node_removal(self):
        """Test edge removal when nodes are removed"""
        # Build small graph
        self.graph.upsert_edges("A", [("B", 0.5), ("C", 0.6)])
        self.graph.upsert_edges("B", [("A", 0.5), ("C", 0.7)])
        self.graph.upsert_edges("C", [("A", 0.6), ("B", 0.7)])
        
        initial_stats = self.graph.get_stats()
        
        # Remove node B
        self.graph.remove_node("B")
        
        # Check B is gone
        b_neighbors = self.graph.neighbors("B")
        self.assertEqual(len(b_neighbors), 0)
        
        # Check incoming edges to B are removed
        a_neighbors = self.graph.neighbors("A")
        c_neighbors = self.graph.neighbors("C")
        
        a_neighbor_ids = [v for v, w in a_neighbors]
        c_neighbor_ids = [v for v, w in c_neighbors]
        
        self.assertNotIn("B", a_neighbor_ids)
        self.assertNotIn("B", c_neighbor_ids)
        
        # Edge count should decrease
        final_stats = self.graph.get_stats()
        self.assertLess(final_stats["edge_count"], initial_stats["edge_count"])
        
        print("✓ Edge removal via node removal working correctly")
    
    def test_neighbor_discovery_algorithms(self):
        """Test neighbor discovery with various filters"""
        # Build test graph
        self.graph.upsert_edges("A", [
            ("B", 0.9), ("C", 0.7), ("D", 0.5), ("E", 0.3), ("F", 0.1)
        ])
        
        # Test k-limitation
        top_2 = self.graph.neighbors("A", k=2)
        self.assertEqual(len(top_2), 2)
        self.assertEqual([v for v, w in top_2], ["B", "C"])
        
        # Test min_w filter
        high_weight = self.graph.neighbors("A", min_w=0.6)
        high_weight_ids = [v for v, w in high_weight]
        self.assertEqual(set(high_weight_ids), {"B", "C"})
        
        # Test combined filter
        filtered = self.graph.neighbors("A", k=1, min_w=0.8)
        self.assertEqual(len(filtered), 1)
        self.assertEqual(filtered[0][0], "B")
        
        print("✓ Neighbor discovery algorithms working correctly")
    
    def test_graph_integrity_after_operations(self):
        """Test graph maintains integrity after various operations"""
        # Perform mixed operations
        self.graph.upsert_edges("A", [("B", 0.8), ("C", 0.6)])
        self.graph.upsert_edges("B", [("A", 0.8), ("D", 0.7)])
        self.graph.upsert_edges("C", [("A", 0.6), ("E", 0.5)])
        
        # Update existing edge
        self.graph.upsert_edges("A", [("B", 0.9)])  # Increase weight
        
        # Add node without edges
        self.graph.add_node("F")
        
        # Remove a node
        self.graph.remove_node("E")
        
        # Verify graph integrity
        stats = self.graph.get_stats()
        self.assertGreater(stats["node_count"], 0)
        self.assertGreaterEqual(stats["edge_count"], 0)
        
        # Verify no broken edges
        for node_id in ["A", "B", "C", "D", "F"]:
            neighbors = self.graph.neighbors(node_id)
            for neighbor_id, weight in neighbors:
                self.assertGreater(weight, 0)
                self.assertIsInstance(neighbor_id, str)
        
        print("✓ Graph integrity maintained after operations")
    
    def test_edge_weight_calculation_consistency(self):
        """Test edge weight calculations are consistent"""
        # Define weight calculation function (similarity-based)
        def calculate_edge_weight(node_a_emb, node_b_emb):
            """Mock weight calculation based on embedding similarity"""
            import numpy as np
            return float(np.dot(node_a_emb, node_b_emb))
        
        # Mock embeddings
        emb_a = [0.8, 0.6]
        emb_b = [0.7, 0.5]
        emb_c = [0.9, 0.4]
        
        # Calculate consistent weights
        weight_ab = calculate_edge_weight(emb_a, emb_b)
        weight_ac = calculate_edge_weight(emb_a, emb_c)
        
        # Insert edges with calculated weights
        self.graph.upsert_edges("A", [("B", weight_ab), ("C", weight_ac)])
        
        # Verify weights are preserved
        neighbors = self.graph.neighbors("A")
        neighbor_dict = {v: w for v, w in neighbors}
        
        self.assertAlmostEqual(neighbor_dict["B"], weight_ab, places=6)
        self.assertAlmostEqual(neighbor_dict["C"], weight_ac, places=6)
        
        print("✓ Edge weight calculation consistency verified")

if __name__ == "__main__":
    print("🧪 Running M2.2 - Graph Edge Management Tests")
    print("=" * 60)
    
    unittest.main(verbosity=2)