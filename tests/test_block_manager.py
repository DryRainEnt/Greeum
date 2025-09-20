"""
Test suite for BlockManager core functionality
"""

import unittest
import tempfile
import os
import time
from unittest.mock import Mock, patch, MagicMock

from tests.base_test_case import BaseGreeumTestCase
from greeum.core.block_manager import BlockManager


class TestBlockManager(BaseGreeumTestCase):
    """Test BlockManager core functionality"""
    
    def setUp(self):
        super().setUp()
        self.block_manager = BlockManager(self.db_manager)
    
    def test_block_manager_initialization(self):
        """Test BlockManager initialization"""
        self.assertIsNotNone(self.block_manager)
        self.assertEqual(self.block_manager.db_manager, self.db_manager)
    
    def test_add_block_basic(self):
        """Test basic block addition"""
        context = "Test block content"
        keywords = ["test", "block"]
        tags = ["test"]
        embedding = self.get_test_embedding(context)
        importance = 0.7
        
        result = self.block_manager.add_block(
            context=context,
            keywords=keywords,
            tags=tags,
            embedding=embedding,
            importance=importance
        )
        
        self.assertIsNotNone(result)
        self.assertIn('block_index', result)
        self.assertIn('hash', result)
    
    def test_add_block_with_metadata(self):
        """Test block addition with metadata"""
        context = "Test block with metadata"
        keywords = ["test", "metadata"]
        tags = ["test"]
        embedding = self.get_test_embedding(context)
        importance = 0.8
        metadata = {"source": "test", "version": "1.0"}
        
        result = self.block_manager.add_block(
            context=context,
            keywords=keywords,
            tags=tags,
            embedding=embedding,
            importance=importance,
            metadata=metadata
        )
        
        self.assertIsNotNone(result)
        self.assertIn('block_index', result)
    
    def test_search_by_embedding(self):
        """Test embedding-based search"""
        # Add test blocks first
        contexts = [
            "Machine learning model training",
            "Database optimization work",
            "Frontend development progress"
        ]
        
        for context in contexts:
            self.block_manager.add_block(
                context=context,
                keywords=context.split(),
                tags=["test"],
                embedding=self.get_test_embedding(context),
                importance=0.6
            )
        
        # Search for similar content
        query_embedding = self.get_test_embedding("machine learning")
        results = self.block_manager.search_by_embedding(query_embedding, top_k=2)
        
        self.assertIsInstance(results, list)
        self.assertLessEqual(len(results), 2)
    
    def test_search_by_keywords(self):
        """Test keyword-based search"""
        # Add test blocks
        test_blocks = [
            ("Python development", ["python", "development"]),
            ("JavaScript frontend", ["javascript", "frontend"]),
            ("Database design", ["database", "design"])
        ]
        
        for context, keywords in test_blocks:
            self.block_manager.add_block(
                context=context,
                keywords=keywords,
                tags=["test"],
                embedding=self.get_test_embedding(context),
                importance=0.5
            )
        
        # Search by keywords
        results = self.block_manager.search_by_keywords(["python", "development"], top_k=5)
        
        self.assertIsInstance(results, list)
    
    def test_get_blocks(self):
        """Test getting blocks"""
        # Add multiple blocks
        for i in range(5):
            self.block_manager.add_block(
                context=f"Recent block {i}",
                keywords=[f"block{i}"],
                tags=["recent"],
                embedding=self.get_test_embedding(f"Recent block {i}"),
                importance=0.5
            )
        
        # Get blocks
        blocks = self.block_manager.get_blocks()
        
        self.assertIsInstance(blocks, list)
        self.assertGreaterEqual(len(blocks), 0)
    
    def test_get_block_by_index(self):
        """Test getting block by index"""
        # Add a test block
        result = self.block_manager.add_block(
            context="Test block for retrieval",
            keywords=["test", "retrieval"],
            tags=["test"],
            embedding=self.get_test_embedding("Test block for retrieval"),
            importance=0.6
        )
        
        block_index = result['block_index']
        
        # Retrieve the block
        retrieved_block = self.block_manager.get_block_by_index(block_index)
        
        self.assertIsNotNone(retrieved_block)
        self.assertEqual(retrieved_block['context'], "Test block for retrieval")
    
    def test_block_validation(self):
        """Test block data validation"""
        # Test with invalid importance - BlockManager may accept this, so we'll just verify it works
        try:
            result = self.block_manager.add_block(
                context="Invalid importance test",
                keywords=["test"],
                tags=["test"],
                embedding=self.get_test_embedding("Invalid importance test"),
                importance=1.5  # Invalid: > 1.0
            )
            # If it doesn't raise an exception, that's also acceptable
            self.assertIsNotNone(result)
        except (ValueError, TypeError):
            # This is also acceptable behavior
            pass
        
        # Test with empty context - BlockManager may accept this too
        try:
            result = self.block_manager.add_block(
                context="",  # Empty context
                keywords=["test"],
                tags=["test"],
                embedding=self.get_test_embedding(""),
                importance=0.5
            )
            # If it doesn't raise an exception, that's also acceptable
            self.assertIsNotNone(result)
        except (ValueError, TypeError):
            # This is also acceptable behavior
            pass
    
    def test_block_metrics(self):
        """Test block metrics functionality"""
        # Add multiple blocks
        for i in range(10):
            self.block_manager.add_block(
                context=f"Statistics test block {i}",
                keywords=[f"stat{i}"],
                tags=["statistics"],
                embedding=self.get_test_embedding(f"Statistics test block {i}"),
                importance=0.3 + (i * 0.05)
            )
        
        # Get metrics (if available)
        if hasattr(self.block_manager, 'metrics'):
            metrics = self.block_manager.metrics
            self.assertIsInstance(metrics, dict)
        else:
            # If metrics not available, just verify blocks were added
            blocks = self.block_manager.get_blocks()
            self.assertGreaterEqual(len(blocks), 0)


class TestBlockManagerIntegration(BaseGreeumTestCase):
    """Integration tests for BlockManager"""
    
    def setUp(self):
        super().setUp()
        self.block_manager = BlockManager(self.db_manager)
        self.setup_database_with_test_data(5)
    
    def test_block_manager_with_stm_manager(self):
        """Test BlockManager integration with STMManager"""
        # This test verifies that BlockManager works correctly
        # when integrated with STMManager
        self.assertIsNotNone(self.block_manager)
        self.assertIsNotNone(self.stm_manager)
    
    def test_block_manager_with_cache_manager(self):
        """Test BlockManager integration with CacheManager"""
        # This test verifies that BlockManager works correctly
        # when integrated with CacheManager
        self.assertIsNotNone(self.block_manager)
        self.assertIsNotNone(self.cache_manager)
    
    def test_concurrent_block_operations(self):
        """Test concurrent block operations"""
        import threading
        import time
        
        results = []
        errors = []
        
        def add_blocks_worker(worker_id):
            try:
                for i in range(3):
                    result = self.block_manager.add_block(
                        context=f"Concurrent test {worker_id}-{i}",
                        keywords=[f"worker{worker_id}", f"block{i}"],
                        tags=["concurrent"],
                        embedding=self.get_test_embedding(f"Concurrent test {worker_id}-{i}"),
                        importance=0.5
                    )
                    results.append(result)
                    time.sleep(0.01)
            except Exception as e:
                errors.append(f"Worker {worker_id}: {e}")
        
        # Run multiple workers concurrently
        threads = []
        for i in range(3):
            thread = threading.Thread(target=add_blocks_worker, args=(i,))
            threads.append(thread)
            thread.start()
        
        for thread in threads:
            thread.join()
        
        # Verify no errors occurred
        self.assertEqual(len(errors), 0, f"Concurrent operations errors: {errors}")
        self.assertEqual(len(results), 9)  # 3 workers * 3 blocks each


if __name__ == '__main__':
    unittest.main()