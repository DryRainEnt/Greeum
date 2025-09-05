"""
Test suite for M2.3 - LTM Links Cache System functionality
"""

import unittest
import time
import tempfile
import json
from pathlib import Path
from greeum.core.ltm_links_cache import LTMLinksCache, create_neighbor_link, calculate_link_weight
from greeum.core.database_manager import DatabaseManager
from greeum.core.block_manager import BlockManager

class TestM23LTMLinksCache(unittest.TestCase):
    def setUp(self):
        """Set up test environment with temporary database"""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        
        self.db_manager = DatabaseManager(connection_string=self.temp_db.name)
        self.block_manager = BlockManager(self.db_manager)
        self.links_cache = LTMLinksCache(self.db_manager)
        
        # Create test blocks
        self.test_blocks = []
        for i in range(5):
            block = self.block_manager.add_block(
                context=f"Test block {i}",
                keywords=[f"test{i}", "block"],
                tags=[f"tag{i}"],
                embedding=[0.1 * i] * 128,  # Simple embedding
                importance=0.5 + 0.1 * i
            )
            self.test_blocks.append(block)
    
    def tearDown(self):
        """Clean up test environment"""
        Path(self.temp_db.name).unlink(missing_ok=True)
    
    def test_add_block_links_performance(self):
        """Test adding block links performance < 3ms"""
        block_id = str(self.test_blocks[0]['block_index'])
        
        # Prepare test neighbors
        neighbors = [
            create_neighbor_link(str(self.test_blocks[1]['block_index']), 0.8),
            create_neighbor_link(str(self.test_blocks[2]['block_index']), 0.6),
            create_neighbor_link(str(self.test_blocks[3]['block_index']), 0.4)
        ]
        
        start_time = time.perf_counter()
        
        # Add links
        success = self.links_cache.add_block_links(block_id, neighbors)
        
        end_time = time.perf_counter()
        operation_time_ms = (end_time - start_time) * 1000
        
        # Performance requirement: < 3ms
        self.assertLess(operation_time_ms, 3.0, 
                       f"Add block links took {operation_time_ms:.2f}ms, should be < 3ms")
        self.assertTrue(success)
        
        print(f"✓ Add block links performance: {operation_time_ms:.2f}ms")
    
    def test_get_block_neighbors_caching(self):
        """Test neighbor retrieval and caching functionality"""
        block_id = str(self.test_blocks[0]['block_index'])
        
        # Add neighbors
        neighbors = [
            create_neighbor_link(str(self.test_blocks[1]['block_index']), 0.9),
            create_neighbor_link(str(self.test_blocks[2]['block_index']), 0.7),
            create_neighbor_link(str(self.test_blocks[3]['block_index']), 0.5)
        ]
        
        self.links_cache.add_block_links(block_id, neighbors)
        
        # Retrieve neighbors
        cached_neighbors = self.links_cache.get_block_neighbors(block_id)
        
        # Verify neighbors are sorted by weight descending
        self.assertEqual(len(cached_neighbors), 3)
        weights = [n['weight'] for n in cached_neighbors]
        self.assertEqual(weights, sorted(weights, reverse=True))
        
        # Verify specific neighbor data
        self.assertEqual(cached_neighbors[0]['weight'], 0.9)
        self.assertEqual(cached_neighbors[1]['weight'], 0.7)
        self.assertEqual(cached_neighbors[2]['weight'], 0.5)
        
        print("✓ Block neighbors caching working correctly")
    
    def test_cache_hit_rate_tracking(self):
        """Test cache performance metrics tracking"""
        block_id = str(self.test_blocks[0]['block_index'])
        
        # Clear stats
        self.links_cache.clear_cache_stats()
        
        # Add neighbors
        neighbors = [create_neighbor_link(str(self.test_blocks[1]['block_index']), 0.8)]
        self.links_cache.add_block_links(block_id, neighbors)
        
        # Multiple cache hits
        for _ in range(5):
            self.links_cache.get_block_neighbors(block_id)
        
        # Cache miss (non-existent block)
        self.links_cache.get_block_neighbors("999")
        
        # Check stats
        stats = self.links_cache.get_cache_stats()
        self.assertEqual(stats['cache_hits'], 5)
        self.assertEqual(stats['cache_misses'], 1)
        self.assertEqual(stats['total_requests'], 6)
        self.assertAlmostEqual(stats['hit_rate'], 5/6, places=2)
        
        print(f"✓ Cache hit rate tracking: {stats['hit_rate']:.2%}")
    
    def test_neighbor_weight_update(self):
        """Test updating individual neighbor weights"""
        block_id = str(self.test_blocks[0]['block_index'])
        neighbor_id = str(self.test_blocks[1]['block_index'])
        
        # Add initial neighbor
        neighbors = [create_neighbor_link(neighbor_id, 0.5)]
        self.links_cache.add_block_links(block_id, neighbors)
        
        # Update weight
        success = self.links_cache.update_neighbor_weight(block_id, neighbor_id, 0.9)
        self.assertTrue(success)
        
        # Verify update
        updated_neighbors = self.links_cache.get_block_neighbors(block_id)
        self.assertEqual(len(updated_neighbors), 1)
        self.assertEqual(updated_neighbors[0]['weight'], 0.9)
        
        print("✓ Neighbor weight update working correctly")
    
    def test_neighbor_link_removal(self):
        """Test removing specific neighbor links"""
        block_id = str(self.test_blocks[0]['block_index'])
        
        # Add multiple neighbors
        neighbors = [
            create_neighbor_link(str(self.test_blocks[1]['block_index']), 0.8),
            create_neighbor_link(str(self.test_blocks[2]['block_index']), 0.6),
            create_neighbor_link(str(self.test_blocks[3]['block_index']), 0.4)
        ]
        self.links_cache.add_block_links(block_id, neighbors)
        
        # Remove middle neighbor
        target_neighbor = str(self.test_blocks[2]['block_index'])
        success = self.links_cache.remove_neighbor_link(block_id, target_neighbor)
        self.assertTrue(success)
        
        # Verify removal
        remaining_neighbors = self.links_cache.get_block_neighbors(block_id)
        self.assertEqual(len(remaining_neighbors), 2)
        
        neighbor_ids = [n['id'] for n in remaining_neighbors]
        self.assertNotIn(target_neighbor, neighbor_ids)
        
        print("✓ Neighbor link removal working correctly")
    
    def test_bulk_links_update(self):
        """Test bulk updating links for multiple blocks"""
        # Prepare bulk update data
        block_links = {}
        for i in range(3):
            block_id = str(self.test_blocks[i]['block_index'])
            neighbors = [
                create_neighbor_link(str(self.test_blocks[(i+1) % 5]['block_index']), 0.7),
                create_neighbor_link(str(self.test_blocks[(i+2) % 5]['block_index']), 0.5)
            ]
            block_links[block_id] = neighbors
        
        # Perform bulk update
        success_count = self.links_cache.bulk_update_links(block_links)
        self.assertEqual(success_count, 3)
        
        # Verify all blocks were updated
        for block_id in block_links.keys():
            neighbors = self.links_cache.get_block_neighbors(block_id)
            self.assertEqual(len(neighbors), 2)
        
        print("✓ Bulk links update working correctly")
    
    def test_links_integrity_validation(self):
        """Test validation of cached links integrity"""
        block_id = str(self.test_blocks[0]['block_index'])
        
        # Add mix of valid and invalid neighbors
        neighbors = [
            create_neighbor_link(str(self.test_blocks[1]['block_index']), 0.8),  # Valid
            create_neighbor_link("999", 0.6),  # Invalid (missing block)
            create_neighbor_link(str(self.test_blocks[2]['block_index']), 1.5)   # Invalid weight
        ]
        self.links_cache.add_block_links(block_id, neighbors)
        
        # Validate links
        validation = self.links_cache.validate_links_integrity(block_id)
        
        self.assertEqual(validation['neighbor_count'], 3)
        self.assertEqual(validation['valid_neighbors'], 2)  # blocks 1 and 2 exist
        self.assertEqual(validation['invalid_neighbors'], 1)  # block 999 missing
        self.assertIn("999", validation['missing_blocks'])
        self.assertEqual(len(validation['weight_issues']), 1)  # weight 1.5 is invalid
        
        print("✓ Links integrity validation working correctly")
    
    def test_orphaned_links_cleanup(self):
        """Test cleanup of orphaned links pointing to deleted blocks"""
        block_id = str(self.test_blocks[0]['block_index'])
        
        # Add neighbors including future orphan
        neighbors = [
            create_neighbor_link(str(self.test_blocks[1]['block_index']), 0.8),
            create_neighbor_link(str(self.test_blocks[2]['block_index']), 0.6),
            create_neighbor_link("999", 0.4)  # This will be orphaned
        ]
        self.links_cache.add_block_links(block_id, neighbors)
        
        # Dry run cleanup
        dry_stats = self.links_cache.cleanup_orphaned_links(dry_run=True)
        self.assertEqual(dry_stats['blocks_checked'], 1)
        self.assertEqual(dry_stats['orphaned_links_found'], 1)
        self.assertEqual(dry_stats['blocks_with_orphans'], 1)
        self.assertFalse(dry_stats['cleanup_performed'])
        
        # Actual cleanup
        cleanup_stats = self.links_cache.cleanup_orphaned_links(dry_run=False)
        self.assertTrue(cleanup_stats['cleanup_performed'])
        
        # Verify cleanup
        cleaned_neighbors = self.links_cache.get_block_neighbors(block_id)
        self.assertEqual(len(cleaned_neighbors), 2)  # Orphan removed
        
        print("✓ Orphaned links cleanup working correctly")
    
    def test_link_weight_calculation(self):
        """Test embedding-based link weight calculation"""
        # Test embeddings with known similarity
        emb_a = [1.0, 0.0, 0.0]  # Unit vector
        emb_b = [0.0, 1.0, 0.0]  # Perpendicular
        emb_c = [1.0, 0.0, 0.0]  # Identical
        
        # Calculate weights
        weight_ab = calculate_link_weight(emb_a, emb_b)  # Should be ~0.5 (orthogonal)
        weight_ac = calculate_link_weight(emb_a, emb_c)  # Should be 1.0 (identical)
        
        self.assertAlmostEqual(weight_ab, 0.5, places=1)
        self.assertAlmostEqual(weight_ac, 1.0, places=1)
        
        # Test zero vector handling
        weight_zero = calculate_link_weight([0.0, 0.0, 0.0], emb_a)
        self.assertEqual(weight_zero, 0.0)
        
        print("✓ Link weight calculation working correctly")
    
    def test_max_neighbors_limitation(self):
        """Test max neighbors limitation functionality"""
        block_id = str(self.test_blocks[0]['block_index'])
        
        # Add many neighbors
        neighbors = []
        for i in range(10):
            neighbors.append(create_neighbor_link(f"block_{i}", 0.9 - i * 0.1))
        
        self.links_cache.add_block_links(block_id, neighbors)
        
        # Get limited neighbors
        limited_neighbors = self.links_cache.get_block_neighbors(block_id, max_neighbors=3)
        
        self.assertEqual(len(limited_neighbors), 3)
        
        # Should be top 3 by weight
        weights = [n['weight'] for n in limited_neighbors]
        self.assertEqual(weights, [0.9, 0.8, 0.7])
        
        print("✓ Max neighbors limitation working correctly")
    
    def test_links_cache_persistence(self):
        """Test that links cache persists in database"""
        block_id = str(self.test_blocks[0]['block_index'])
        
        # Add neighbors
        neighbors = [create_neighbor_link(str(self.test_blocks[1]['block_index']), 0.8)]
        self.links_cache.add_block_links(block_id, neighbors)
        
        # Create new cache instance (simulates restart)
        new_cache = LTMLinksCache(self.db_manager)
        
        # Verify neighbors persist
        persisted_neighbors = new_cache.get_block_neighbors(block_id)
        self.assertEqual(len(persisted_neighbors), 1)
        self.assertEqual(persisted_neighbors[0]['weight'], 0.8)
        
        print("✓ Links cache persistence working correctly")

if __name__ == "__main__":
    print("🧪 Running M2.3 - LTM Links Cache System Tests")
    print("=" * 60)
    
    unittest.main(verbosity=2)