"""
Test suite for STMManager core functionality
"""

import unittest
import tempfile
import os
import time
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock

from tests.base_test_case import BaseGreeumTestCase
from greeum.core.stm_manager import STMManager


class TestSTMManager(BaseGreeumTestCase):
    """Test STMManager core functionality"""
    
    def setUp(self):
        super().setUp()
        self.stm_manager = STMManager(self.db_manager)
    
    def test_stm_manager_initialization(self):
        """Test STMManager initialization"""
        self.assertIsNotNone(self.stm_manager)
        self.assertEqual(self.stm_manager.db_manager, self.db_manager)
    
    def test_add_memory(self):
        """Test adding memory to STM"""
        test_content = 'Test STM content'
        
        result = self.stm_manager.add_memory(content=test_content, importance=0.7)
        
        self.assertIsNotNone(result)
        self.assertIsInstance(result, str)  # Returns memory_id
    
    def test_get_memory_by_id(self):
        """Test retrieving memory by ID from STM"""
        # Add test memory first
        test_content = 'Test STM retrieval'
        memory_id = self.stm_manager.add_memory(content=test_content, importance=0.8)
        
        # Retrieve the memory
        retrieved_memory = self.stm_manager.get_memory_by_id(memory_id)
        
        self.assertIsNotNone(retrieved_memory)
        self.assertEqual(retrieved_memory['content'], 'Test STM retrieval')
    
    def test_get_recent_memories(self):
        """Test getting recent memories from STM"""
        # Add multiple test memories
        test_contents = [
            'Python development work',
            'JavaScript frontend work',
            'Database optimization'
        ]
        
        for content in test_contents:
            self.stm_manager.add_memory(content=content, importance=0.7)
        
        # Get recent memories
        recent_memories = self.stm_manager.get_recent_memories(count=3)
        
        self.assertIsInstance(recent_memories, list)
        self.assertLessEqual(len(recent_memories), 3)
    
    def test_get_stats(self):
        """Test getting STM statistics"""
        # Add multiple memories
        for i in range(5):
            self.stm_manager.add_memory(content=f'Stats test memory {i}', importance=0.5 + (i * 0.1))
        
        # Get statistics
        stats = self.stm_manager.get_stats()
        
        self.assertIsInstance(stats, dict)
        self.assertIn('total_memories', stats)
    
    def test_clean_expired(self):
        """Test cleaning expired STM entries"""
        # Add some memories
        for i in range(3):
            self.stm_manager.add_memory(content=f'Clean test memory {i}', importance=0.5)
        
        # Clean expired entries
        cleaned_count = self.stm_manager.clean_expired()
        
        self.assertIsInstance(cleaned_count, int)
        self.assertGreaterEqual(cleaned_count, 0)
    
    def test_clear_all(self):
        """Test clearing all STM entries"""
        # Add some memories first
        for i in range(3):
            self.stm_manager.add_memory(content=f'Clear test memory {i}', importance=0.5)
        
        # Clear all entries
        cleared_count = self.stm_manager.clear_all()
        
        self.assertIsInstance(cleared_count, int)
        self.assertGreaterEqual(cleared_count, 0)
    
    def test_promote_to_ltm(self):
        """Test promoting STM memory to LTM"""
        # Add STM memory
        memory_id = self.stm_manager.add_memory(content='Important memory for promotion', importance=0.9)
        
        # Promote to LTM
        ltm_index = self.stm_manager.promote_to_ltm(memory_id)
        
        # Should return LTM block index or None
        self.assertTrue(ltm_index is None or isinstance(ltm_index, int))
    
    def test_check_promotion(self):
        """Test checking if memory should be promoted"""
        # Add memory
        memory_id = self.stm_manager.add_memory(content='Check promotion test', importance=0.8)
        
        # Check promotion eligibility
        should_promote = self.stm_manager.check_promotion_to_working_memory(memory_id)
        
        self.assertIsInstance(should_promote, bool)


class TestSTMManagerIntegration(BaseGreeumTestCase):
    """Integration tests for STMManager"""
    
    def setUp(self):
        super().setUp()
        self.stm_manager = STMManager(self.db_manager)
        self.setup_database_with_test_data(3)
    
    def test_stm_manager_with_block_manager(self):
        """Test STMManager integration with BlockManager"""
        from greeum.core.block_manager import BlockManager
        
        block_manager = BlockManager(self.db_manager)
        
        # Test that they work together
        self.assertIsNotNone(self.stm_manager)
        self.assertIsNotNone(block_manager)
    
    def test_stm_manager_with_cache_manager(self):
        """Test STMManager integration with CacheManager"""
        from greeum.core.cache_manager import CacheManager
        
        cache_manager = CacheManager(
            block_manager=self.block_manager,
            stm_manager=self.stm_manager
        )
        
        # Test that they work together
        self.assertIsNotNone(self.stm_manager)
        self.assertIsNotNone(cache_manager)
    
    def test_stm_to_ltm_promotion(self):
        """Test promoting STM entries to LTM (Long Term Memory)"""
        # Add STM entry
        memory_id = self.stm_manager.add_memory(content='Important STM content for promotion', importance=0.9)
        
        # Promote to LTM
        ltm_index = self.stm_manager.promote_to_ltm(memory_id)
        
        # Should return LTM block index or None
        self.assertTrue(ltm_index is None or isinstance(ltm_index, int))
        
        # Verify STM entry is still accessible
        stm_entry = self.stm_manager.get_memory_by_id(memory_id)
        self.assertIsNotNone(stm_entry)
    
    def test_concurrent_stm_operations(self):
        """Test concurrent STM operations"""
        import threading
        import time
        
        results = []
        errors = []
        
        def stm_operations_worker(worker_id):
            try:
                for i in range(3):
                    memory_id = self.stm_manager.add_memory(
                        content=f'Concurrent STM test {worker_id}-{i}',
                        importance=0.5 + (i * 0.1)
                    )
                    results.append(memory_id)
                    
                    # Retrieve the memory
                    retrieved = self.stm_manager.get_memory_by_id(memory_id)
                    if retrieved:
                        results.append(f"Retrieved {memory_id}")
                    
                    time.sleep(0.01)
            except Exception as e:
                errors.append(f"Worker {worker_id}: {e}")
        
        # Run multiple workers concurrently
        threads = []
        for i in range(3):
            thread = threading.Thread(target=stm_operations_worker, args=(i,))
            threads.append(thread)
            thread.start()
        
        for thread in threads:
            thread.join()
        
        # Verify no errors occurred
        self.assertEqual(len(errors), 0, f"Concurrent STM operations errors: {errors}")
        self.assertGreater(len(results), 0)
    
    def test_stm_memory_limits(self):
        """Test STM memory limits and eviction"""
        # Add many memories to test memory limits
        memory_ids = []
        
        for i in range(20):  # Add more than typical STM limit
            memory_id = self.stm_manager.add_memory(
                content=f'Memory limit test entry {i}',
                importance=0.3 + (i * 0.02)
            )
            memory_ids.append(memory_id)
        
        # Check that STM respects memory limits
        stats = self.stm_manager.get_stats()
        
        # STM should have some limit mechanism
        self.assertIsInstance(stats, dict)
        self.assertIn('total_memories', stats)
        
        # Some memories might be evicted based on importance or TTL
        self.assertLessEqual(stats['total_memories'], 20)


if __name__ == '__main__':
    unittest.main()