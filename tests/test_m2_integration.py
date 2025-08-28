"""
M2 Integration & End-to-End Testing Suite (v2.2.5a1)

Comprehensive testing of all M2 components working together:
- M2.1: Near-anchor write API
- M2.2: Graph edge management  
- M2.3: LTM links cache
- M2.4: Auto anchor movement

Tests the complete anchored memory workflow.
"""

import unittest
import time
import tempfile
import numpy as np
from pathlib import Path
from datetime import datetime

# Import all M2 components
from greeum.api.write import AnchorBasedWriter
from greeum.graph.index import GraphIndex
from greeum.core.ltm_links_cache import LTMLinksCache, create_neighbor_link
from greeum.anchors.auto_movement import AutoAnchorMovement
from greeum.anchors.manager import AnchorManager
from greeum.core.database_manager import DatabaseManager
from greeum.core.block_manager import BlockManager
from greeum.core.search_engine import SearchEngine


class TestM2Integration(unittest.TestCase):
    """Comprehensive M2 system integration tests."""
    
    def setUp(self):
        """Set up complete M2 testing environment."""
        # Create temporary files
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        
        self.temp_anchors = tempfile.NamedTemporaryFile(delete=False, suffix='.json')
        self.temp_anchors.close()
        
        self.temp_graph = tempfile.NamedTemporaryFile(delete=False, suffix='.jsonl')
        self.temp_graph.close()
        
        # Initialize core components
        self.db_manager = DatabaseManager(connection_string=self.temp_db.name)
        self.block_manager = BlockManager(self.db_manager)
        self.search_engine = SearchEngine(
            block_manager=self.block_manager,
            anchor_path=self.temp_anchors.name,
            graph_path=self.temp_graph.name
        )
        
        # Create test blocks first to get valid IDs for anchors
        self._create_test_anchor_blocks()
        
        # Initialize M2 components with isolated test data
        self.graph_index = GraphIndex(theta=0.3, kmax=8)
        self.links_cache = LTMLinksCache(self.db_manager)
        self.anchor_manager = AnchorManager(Path(self.temp_anchors.name))
        self.auto_movement = AutoAnchorMovement(self.anchor_manager, self.links_cache, self.db_manager)
        self.anchor_writer = AnchorBasedWriter(
            db_manager=self.db_manager,
            anchor_path=Path(self.temp_anchors.name),
            graph_path=Path(self.temp_graph.name)
        )
        
        # Create diverse test content
        self.test_content = [
            "Machine learning algorithms are transforming data science",
            "Deep neural networks enable advanced pattern recognition", 
            "Natural language processing improves text understanding",
            "Computer vision applications in autonomous vehicles",
            "Reinforcement learning for game AI optimization",
            "Quantum computing breakthrough in cryptography",
            "Blockchain technology for decentralized systems",
            "Cloud computing scalability and performance",
            "Cybersecurity threats in IoT devices",
            "Big data analytics for business intelligence"
        ]
        
        print(f"🧪 M2 Integration Test Environment Ready")
        print(f"   Database: {self.temp_db.name}")
        print(f"   Anchors: {self.temp_anchors.name}")
        print(f"   Test anchor blocks: {self.test_anchor_ids}")
    
    def _create_test_anchor_blocks(self):
        """Create dedicated blocks for anchor testing with isolated environment."""
        import json
        
        # Create test blocks specifically for anchors
        anchor_contents = [
            "Anchor A: Machine learning and AI development topics",
            "Anchor B: Data analysis and statistical methods",  
            "Anchor C: Software engineering and system design"
        ]
        
        self.test_anchor_ids = []
        
        for i, content in enumerate(anchor_contents):
            # Create embedding for test block
            test_embedding = [0.1 * (i + 1)] * 128  # Simple test embedding
            
            block = self.block_manager.add_block(
                context=content,
                keywords=[f"anchor_{chr(65+i)}", "test"],
                tags=["test_anchor"],
                embedding=test_embedding,
                importance=0.8
            )
            
            self.test_anchor_ids.append(str(block['block_index']))
        
        # Create isolated anchor configuration for testing
        test_anchor_config = {
            "version": 1,
            "slots": [
                {
                    "slot": "A",
                    "anchor_block_id": self.test_anchor_ids[0],
                    "topic_vec": [0.1] * 128,
                    "summary": "Test anchor A",
                    "last_used_ts": int(time.time()),
                    "hop_budget": 3,
                    "pinned": False
                },
                {
                    "slot": "B", 
                    "anchor_block_id": self.test_anchor_ids[1],
                    "topic_vec": [0.2] * 128,
                    "summary": "Test anchor B",
                    "last_used_ts": int(time.time()),
                    "hop_budget": 2,
                    "pinned": False
                },
                {
                    "slot": "C",
                    "anchor_block_id": self.test_anchor_ids[2], 
                    "topic_vec": [0.3] * 128,
                    "summary": "Test anchor C",
                    "last_used_ts": int(time.time()),
                    "hop_budget": 3,
                    "pinned": False
                }
            ],
            "updated_at": int(time.time())
        }
        
        # Write isolated anchor config to temp file
        with open(self.temp_anchors.name, 'w') as f:
            json.dump(test_anchor_config, f, indent=2)
    
    def tearDown(self):
        """Clean up test environment."""
        Path(self.temp_db.name).unlink(missing_ok=True)
        Path(self.temp_anchors.name).unlink(missing_ok=True)
        Path(self.temp_graph.name).unlink(missing_ok=True)
    
    def test_e2e_write_search_workflow(self):
        """Test complete end-to-end workflow: write → build graph → search → move anchors."""
        print("\n🔄 Testing End-to-End Workflow...")
        
        # Phase 1: Write multiple blocks using anchor-based writer
        written_blocks = []
        total_write_time = 0
        
        for i, content in enumerate(self.test_content):
            start_time = time.perf_counter()
            
            # Use anchor-based write with slot rotation
            slot = ['A', 'B', 'C'][i % 3]
            block_id = self.anchor_writer.write(
                text=content,
                slot=slot,
                keywords=[f"test{i}", "integration"],
                tags=["e2e_test"],
                importance=0.5 + 0.1 * (i % 5)
            )
            
            write_time = (time.perf_counter() - start_time) * 1000
            total_write_time += write_time
            written_blocks.append(block_id)
            
            self.assertIsNotNone(block_id)
            print(f"   ✓ Block {block_id} written to slot {slot} ({write_time:.2f}ms)")
        
        # Verify all blocks were written
        self.assertEqual(len(written_blocks), len(self.test_content))
        avg_write_time = total_write_time / len(written_blocks)
        self.assertLess(avg_write_time, 10.0, f"Average write time {avg_write_time:.2f}ms too slow")
        
        print(f"   📊 Phase 1 Complete: {len(written_blocks)} blocks, avg {avg_write_time:.2f}ms")
        
        # Phase 2: Build graph connections between blocks
        print("\n🕸️  Building Graph Connections...")
        
        for i, block_id in enumerate(written_blocks):
            # Get block data
            block = self.db_manager.get_block_by_index(int(block_id))
            self.assertIsNotNone(block)
            
            # Create connections to similar blocks
            neighbors = []
            for j, other_id in enumerate(written_blocks):
                if i != j:
                    other_block = self.db_manager.get_block_by_index(int(other_id))
                    
                    # Calculate similarity (mock for this test)
                    similarity = max(0.1, 0.8 - abs(i - j) * 0.1)
                    if similarity > 0.4:
                        neighbors.append((other_id, similarity))
            
            # Add edges to graph
            if neighbors:
                self.graph_index.upsert_edges(block_id, neighbors)
                print(f"   ✓ Block {block_id}: {len(neighbors)} connections")
        
        graph_stats = self.graph_index.get_stats()
        self.assertGreater(graph_stats['edge_count'], 0)
        print(f"   📊 Graph: {graph_stats['node_count']} nodes, {graph_stats['edge_count']} edges")
        
        # Phase 3: Add neighbor links cache
        print("\n🔗 Building Links Cache...")
        
        cache_updates = 0
        for block_id in written_blocks:
            neighbors = self.graph_index.neighbors(block_id, k=5)
            if neighbors:
                neighbor_links = [create_neighbor_link(nid, weight) for nid, weight in neighbors]
                success = self.links_cache.add_block_links(block_id, neighbor_links)
                if success:
                    cache_updates += 1
        
        print(f"   📊 Cache: {cache_updates} blocks with neighbor links")
        
        # Phase 4: Perform searches and test anchor movement
        print("\n🔍 Testing Search & Anchor Movement...")
        
        search_queries = [
            "machine learning neural networks",
            "quantum computing cryptography", 
            "blockchain decentralized systems"
        ]
        
        total_search_time = 0
        anchor_movements = 0
        
        for query in search_queries:
            start_time = time.perf_counter()
            
            # Perform anchor-based search
            results = self.search_engine.search(
                query=query,
                top_k=3,
                slot='A',  # Use slot A for search
                radius=2,
                fallback=True
            )
            
            search_time = (time.perf_counter() - start_time) * 1000
            total_search_time += search_time
            
            # Verify search results
            self.assertIn('blocks', results)
            self.assertIn('metadata', results)
            
            blocks_found = len(results['blocks'])
            print(f"   ✓ Query '{query[:30]}...': {blocks_found} results ({search_time:.2f}ms)")
            
            # Test anchor movement evaluation
            if blocks_found > 0:
                # Create mock topic vector from query
                query_topic = np.random.rand(128) * 0.1  # Mock embedding
                
                evaluation = self.auto_movement.evaluate_anchor_movement(
                    slot='A',
                    search_results=results['blocks'],
                    query_topic_vec=query_topic
                )
                
                if evaluation['should_move']:
                    anchor_movements += 1
                    print(f"     → Anchor movement: {evaluation['reason']}")
        
        avg_search_time = total_search_time / len(search_queries)
        self.assertLess(avg_search_time, 50.0, f"Average search time {avg_search_time:.2f}ms too slow")
        
        print(f"   📊 Search: {len(search_queries)} queries, avg {avg_search_time:.2f}ms")
        print(f"   📊 Movements: {anchor_movements} anchor movements evaluated")
        
        # Phase 5: Verify system integrity
        print("\n✅ Verifying System Integrity...")
        
        # Check database integrity (test blocks + anchor blocks)
        all_blocks = self.db_manager.get_blocks(limit=100)
        expected_total = len(written_blocks) + len(self.test_anchor_ids)
        self.assertEqual(len(all_blocks), expected_total)
        print(f"   ✓ Database: {len(all_blocks)} blocks intact ({len(written_blocks)} test + {len(self.test_anchor_ids)} anchor)")
        
        # Check graph integrity
        graph_stats_final = self.graph_index.get_stats()
        self.assertEqual(graph_stats_final['node_count'], graph_stats['node_count'])
        print(f"   ✓ Graph: integrity maintained")
        
        # Check cache integrity
        cache_stats = self.links_cache.get_cache_stats()
        print(f"   ✓ Cache: {cache_stats['cache_hits']} hits, {cache_stats['hit_rate']:.1%} hit rate")
        
        # Check anchor state
        for slot in ['A', 'B', 'C']:
            slot_info = self.anchor_manager.get_slot_info(slot)
            if slot_info:
                print(f"   ✓ Anchor {slot}: block {slot_info['anchor_block_id']}")
        
        print(f"\n🎉 End-to-End Workflow Complete!")
        print(f"   Total time: {(total_write_time + total_search_time):.2f}ms")
        print(f"   Blocks: {len(written_blocks)} written, {len(all_blocks)} stored")
        print(f"   Performance: Write {avg_write_time:.2f}ms, Search {avg_search_time:.2f}ms")
    
    def test_performance_stress_test(self):
        """Stress test the integrated system with high load."""
        print("\n🔥 Running Performance Stress Test...")
        
        # Generate larger dataset
        stress_content = [f"Stress test content item {i} with various topics and keywords related to technology, science, and innovation" for i in range(50)]
        
        # Measure bulk write performance
        start_time = time.perf_counter()
        written_blocks = []
        
        for i, content in enumerate(stress_content):
            slot = ['A', 'B', 'C'][i % 3]
            block_id = self.anchor_writer.write(
                text=content,
                slot=slot,
                importance=0.5
            )
            written_blocks.append(block_id)
        
        bulk_write_time = (time.perf_counter() - start_time) * 1000
        avg_write_time = bulk_write_time / len(stress_content)
        
        print(f"   📊 Bulk Write: {len(stress_content)} blocks in {bulk_write_time:.2f}ms")
        print(f"   📊 Average: {avg_write_time:.2f}ms per block")
        
        # Performance requirements
        self.assertLess(avg_write_time, 15.0, f"Write performance degraded: {avg_write_time:.2f}ms")
        self.assertLess(bulk_write_time, 5000.0, f"Bulk write too slow: {bulk_write_time:.2f}ms")
        
        # Test search performance under load
        search_start = time.perf_counter()
        
        for i in range(20):
            results = self.search_engine.search(
                query=f"stress test {i}",
                top_k=5,
                slot=['A', 'B', 'C'][i % 3]
            )
            self.assertIsNotNone(results)
        
        bulk_search_time = (time.perf_counter() - search_start) * 1000
        avg_search_time = bulk_search_time / 20
        
        print(f"   📊 Bulk Search: 20 queries in {bulk_search_time:.2f}ms")
        print(f"   📊 Average: {avg_search_time:.2f}ms per query")
        
        # Search performance requirements
        self.assertLess(avg_search_time, 100.0, f"Search performance degraded: {avg_search_time:.2f}ms")
        
        print(f"   ✅ Stress Test Passed!")
    
    def test_component_isolation(self):
        """Test that components work independently and don't interfere."""
        print("\n🔀 Testing Component Isolation...")
        
        # Test 1: Graph index operates independently
        self.graph_index.add_node("test_node")
        self.graph_index.upsert_edges("test_node", [("other_node", 0.8)])
        
        stats_before = self.graph_index.get_stats()
        
        # Other operations shouldn't affect graph
        block_id = self.anchor_writer.write("Test isolation content")
        self.links_cache.add_block_links(block_id, [create_neighbor_link("999", 0.5)])
        
        stats_after = self.graph_index.get_stats()
        self.assertEqual(stats_before['node_count'], stats_after['node_count'])
        print("   ✓ Graph index isolation maintained")
        
        # Test 2: Links cache operates independently
        cache_stats_before = self.links_cache.get_cache_stats()
        
        # Graph operations shouldn't affect cache stats
        self.graph_index.upsert_edges("new_node", [("another_node", 0.6)])
        
        cache_stats_after = self.links_cache.get_cache_stats()
        self.assertEqual(cache_stats_before['total_requests'], cache_stats_after['total_requests'])
        print("   ✓ Links cache isolation maintained")
        
        # Test 3: Anchor manager operates independently
        initial_anchor = self.anchor_manager.get_slot_info('A')
        
        # Database operations shouldn't affect anchors
        test_block = self.block_manager.add_block(
            context="Isolation test",
            keywords=["test"],
            tags=["isolation"],
            embedding=[0.5] * 128,
            importance=0.5
        )
        
        final_anchor = self.anchor_manager.get_slot_info('A')
        
        # Anchor should only change through explicit moves
        if initial_anchor and final_anchor:
            self.assertEqual(initial_anchor['anchor_block_id'], final_anchor['anchor_block_id'])
        
        print("   ✓ Anchor manager isolation maintained")
        print("   ✅ Component Isolation Test Passed!")
    
    def test_backward_compatibility(self):
        """Test that M2 system maintains backward compatibility."""
        print("\n🔄 Testing Backward Compatibility...")
        
        # Test 1: Standard block manager operations still work
        standard_block = self.block_manager.add_block(
            context="Standard block without anchor features",
            keywords=["standard", "compatibility"],
            tags=["legacy"],
            embedding=[0.3] * 128,
            importance=0.6
        )
        
        self.assertIsNotNone(standard_block)
        print("   ✓ Standard block creation works")
        
        # Test 2: Standard search still works
        results = self.search_engine.search(
            query="standard compatibility",
            top_k=5
            # No slot parameter - should use fallback search
        )
        
        self.assertIn('blocks', results)
        self.assertGreater(len(results['blocks']), 0)
        print("   ✓ Standard search works")
        
        # Test 3: Mixed operations work together
        anchor_block = self.anchor_writer.write("Anchor-based block")
        
        all_blocks = self.db_manager.get_blocks()
        block_ids = [str(b['block_index']) for b in all_blocks]
        
        self.assertIn(str(standard_block['block_index']), block_ids)
        self.assertIn(anchor_block, block_ids)
        print("   ✓ Mixed anchor/standard blocks coexist")
        
        print("   ✅ Backward Compatibility Test Passed!")
    
    def test_error_recovery(self):
        """Test system recovery from various error conditions."""
        print("\n🚨 Testing Error Recovery...")
        
        # Test 1: Invalid anchor operations
        try:
            self.anchor_writer.write("Test content", slot="INVALID_SLOT")
            print("   ⚠️  Invalid slot accepted (may be handled gracefully)")
        except Exception as e:
            print(f"   ✓ Invalid slot rejected: {type(e).__name__}")
        
        # Test 2: Missing graph data
        result = self.graph_index.neighbors("nonexistent_node")
        self.assertEqual(len(result), 0)
        print("   ✓ Missing graph data handled gracefully")
        
        # Test 3: Cache misses
        neighbors = self.links_cache.get_block_neighbors("999")
        self.assertEqual(len(neighbors), 0)
        print("   ✓ Cache misses handled gracefully")
        
        # Test 4: System continues to work after errors
        recovery_block = self.anchor_writer.write("Recovery test content")
        self.assertIsNotNone(recovery_block)
        print("   ✓ System recovers and continues working")
        
        print("   ✅ Error Recovery Test Passed!")


if __name__ == "__main__":
    print("🧪 Running M2 Integration & End-to-End Testing Suite")
    print("=" * 70)
    print("Testing complete M2 anchored memory system integration:")
    print("  • M2.1: Near-anchor write API")
    print("  • M2.2: Graph edge management") 
    print("  • M2.3: LTM links cache")
    print("  • M2.4: Auto anchor movement")
    print("=" * 70)
    
    unittest.main(verbosity=2)