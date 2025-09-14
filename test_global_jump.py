#!/usr/bin/env python3
"""
Test suite for Global Jump functionality in Greeum v3.0.0+
Tests inverted index, vector search, and jump decisions
"""

import unittest
import os
import tempfile
import time
import numpy as np
from datetime import datetime

# Add parent directory to path
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from greeum.core.database_manager import DatabaseManager
from greeum.core.block_manager import BlockManager
from greeum.core.global_index import GlobalIndex, GlobalJumpOptimizer
from greeum.core.dfs_search import DFSSearchEngine


class TestGlobalIndex(unittest.TestCase):
    """Test global index functionality"""
    
    def setUp(self):
        """Create test database with diverse content"""
        self.temp_db = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
        self.db_path = self.temp_db.name
        self.db_manager = DatabaseManager(connection_string=self.db_path)
        self.block_manager = BlockManager(self.db_manager)
        
        # Create diverse test data across different topics
        test_data = [
            # Machine Learning cluster
            ("Introduction to machine learning algorithms", ["machine", "learning", "algorithms"], 0.8),
            ("Deep learning neural networks explained", ["deep", "learning", "neural", "networks"], 0.9),
            ("Training models with gradient descent", ["training", "models", "gradient", "descent"], 0.7),
            
            # Project Management cluster  
            ("Project planning and timeline management", ["project", "planning", "timeline", "management"], 0.7),
            ("Agile methodology sprint planning", ["agile", "methodology", "sprint", "planning"], 0.8),
            ("Team collaboration and communication", ["team", "collaboration", "communication"], 0.6),
            
            # Database cluster
            ("SQL query optimization techniques", ["sql", "query", "optimization", "techniques"], 0.7),
            ("NoSQL database design patterns", ["nosql", "database", "design", "patterns"], 0.8),
            ("Database indexing strategies", ["database", "indexing", "strategies"], 0.9),
            
            # Isolated topics
            ("Weather forecast for next week", ["weather", "forecast", "week"], 0.3),
            ("Recipe for chocolate cake", ["recipe", "chocolate", "cake"], 0.2),
        ]
        
        for i, (context, keywords, importance) in enumerate(test_data):
            # Create embedding based on topic cluster
            if "machine" in context.lower() or "learning" in context.lower():
                base_emb = [0.8, 0.2, 0.1]  # ML cluster
            elif "project" in context.lower() or "agile" in context.lower():
                base_emb = [0.2, 0.8, 0.1]  # PM cluster
            elif "database" in context.lower() or "sql" in context.lower():
                base_emb = [0.1, 0.2, 0.8]  # DB cluster
            else:
                base_emb = [0.3, 0.3, 0.3]  # Neutral
            
            # Add noise to make embeddings unique
            embedding = base_emb + [np.random.random() * 0.1 for _ in range(7)]
            
            self.block_manager.add_block(
                context=context,
                keywords=keywords,
                tags=["test"],
                embedding=embedding,
                importance=importance
            )
            
            time.sleep(0.01)  # Small delay for timestamp variation
    
    def tearDown(self):
        """Clean up"""
        try:
            self.db_manager.conn.close()
        except:
            pass
        os.unlink(self.db_path)
    
    def test_inverted_index_build(self):
        """Test inverted index construction"""
        index = GlobalIndex(self.db_manager)
        
        # Check index was built
        self.assertGreater(len(index.inverted_index), 0)
        self.assertGreater(index.stats["total_keywords"], 0)
        self.assertGreater(index.stats["total_documents"], 0)
        
        # Check specific keywords are indexed
        self.assertIn("machine", index.inverted_index)
        self.assertIn("learning", index.inverted_index)
        self.assertIn("database", index.inverted_index)
        
        # Check IDF scores computed
        self.assertIn("machine", index.keyword_idf)
        self.assertGreater(index.keyword_idf["machine"], 0)
        
        print(f"✓ Inverted index built: {index.stats['total_keywords']} keywords, "
              f"{index.stats['total_documents']} documents")
    
    def test_keyword_search(self):
        """Test keyword-based search"""
        index = GlobalIndex(self.db_manager)
        
        # Search for machine learning topics
        results = index.search_keywords(["machine", "learning"], limit=5)
        
        self.assertGreater(len(results), 0)
        
        # Check results are sorted by score
        scores = [score for _, score in results]
        self.assertEqual(scores, sorted(scores, reverse=True))
        
        # Top results should be ML-related
        top_block_idx = results[0][0]
        cursor = self.db_manager.conn.cursor()
        cursor.execute("SELECT context FROM blocks WHERE block_index = ?", (top_block_idx,))
        context = cursor.fetchone()[0]
        
        self.assertTrue("machine" in context.lower() or "learning" in context.lower())
        
        print(f"✓ Keyword search found {len(results)} results for 'machine learning'")
    
    def test_vector_search(self):
        """Test vector similarity search"""
        index = GlobalIndex(self.db_manager)
        
        # Create query embedding similar to ML cluster
        query_embedding = np.array([0.75, 0.15, 0.1] + [0.05] * 7, dtype=np.float32)
        
        results = index.search_vector(query_embedding, limit=5)
        
        self.assertGreater(len(results), 0)
        
        # Top results should have high similarity
        top_similarity = results[0][1]
        self.assertGreater(top_similarity, 0.5)
        
        print(f"✓ Vector search found {len(results)} results, "
              f"top similarity={top_similarity:.3f}")
    
    def test_hybrid_search(self):
        """Test hybrid keyword + vector search"""
        index = GlobalIndex(self.db_manager)
        
        # Query for database topics
        query = "database optimization"
        query_embedding = np.array([0.1, 0.1, 0.85] + [0.05] * 7, dtype=np.float32)
        
        results = index.search_hybrid(
            query=query,
            query_embedding=query_embedding,
            limit=5,
            keyword_weight=0.5
        )
        
        self.assertGreater(len(results), 0)
        
        # Check results have required fields
        for result in results:
            self.assertIn("block_index", result)
            self.assertIn("context", result)
            self.assertIn("_score", result)
            self.assertIn("_source", result)
            self.assertEqual(result["_source"], "global_index")
        
        # Top results should be database-related
        top_context = results[0]["context"]
        self.assertTrue("database" in top_context.lower() or 
                       "sql" in top_context.lower() or
                       "index" in top_context.lower())
        
        print(f"✓ Hybrid search found {len(results)} results for '{query}'")


class TestGlobalJump(unittest.TestCase):
    """Test global jump integration in DFS search"""
    
    def setUp(self):
        """Create test environment with separated clusters"""
        self.temp_db = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
        self.db_path = self.temp_db.name
        self.db_manager = DatabaseManager(connection_string=self.db_path)
        self.block_manager = BlockManager(self.db_manager)
        
        # Create two separate branches
        # Branch A: Technical topics
        for i in range(5):
            self.block_manager.add_block(
                context=f"Technical document {i}: coding and development",
                keywords=["technical", "coding", "development"],
                tags=["tech"],
                embedding=[0.9, 0.1] + [0.1] * 8,
                importance=0.7,
                slot="A"
            )
        
        # Branch B: Business topics (disconnected from A)
        for i in range(5):
            self.block_manager.add_block(
                context=f"Business report {i}: strategy and planning",
                keywords=["business", "strategy", "planning"],
                tags=["business"],
                embedding=[0.1, 0.9] + [0.1] * 8,
                importance=0.7,
                slot="B"
            )
        
        # Create isolated high-relevance block
        self.block_manager.add_block(
            context="Critical coding guidelines and best practices",
            keywords=["critical", "coding", "guidelines", "best", "practices"],
            tags=["important"],
            embedding=[0.95, 0.05] + [0.1] * 8,
            importance=0.95
        )
    
    def tearDown(self):
        """Clean up"""
        try:
            self.db_manager.conn.close()
        except:
            pass
        os.unlink(self.db_path)
    
    def test_jump_decision(self):
        """Test jump optimizer decision making"""
        optimizer = GlobalJumpOptimizer()
        
        # Should jump when local results insufficient
        self.assertTrue(optimizer.should_jump(local_results=1, query_complexity=0.5))
        
        # Should not jump when local results sufficient
        self.assertFalse(optimizer.should_jump(local_results=5, query_complexity=0.2))
        
        # Should jump for complex queries
        self.assertTrue(optimizer.should_jump(local_results=3, query_complexity=0.8))
        
        # Test learning from history
        for _ in range(10):
            optimizer.record_jump(was_useful=True)
        
        self.assertGreater(optimizer.success_rate, 0.9)
        self.assertTrue(optimizer.should_jump(local_results=3, query_complexity=0.5))
        
        print(f"✓ Jump optimizer working, success_rate={optimizer.success_rate:.2%}")
    
    def test_global_jump_search(self):
        """Test DFS with global jump"""
        dfs_engine = DFSSearchEngine(self.db_manager)
        
        # Search for coding from business branch (should trigger jump)
        results, meta = dfs_engine.search_with_dfs(
            query="coding guidelines best practices",
            slot="B",  # Start from business branch
            depth=2,
            limit=5,
            fallback=True
        )
        
        # Should find results through jump
        self.assertGreater(len(results), 0)
        
        # Check that jump was used
        if meta.get("fallback_used"):
            self.assertEqual(meta["search_type"], "jump")
            
            # Should find the isolated high-relevance block
            contexts = [r["context"] for r in results]
            found_critical = any("Critical coding guidelines" in c for c in contexts)
            self.assertTrue(found_critical, "Should find critical block through jump")
        
        print(f"✓ Global jump search: {len(results)} results, "
              f"jump={meta.get('fallback_used', False)}")
    
    def test_jump_metrics(self):
        """Test jump metrics collection"""
        dfs_engine = DFSSearchEngine(self.db_manager)
        
        # Perform multiple searches
        for i in range(3):
            query = ["coding tips", "business strategy", "random query"][i]
            slot = ["A", "B", "A"][i]
            
            results, meta = dfs_engine.search_with_dfs(
                query=query,
                slot=slot,
                depth=2,
                limit=3,
                fallback=True
            )
        
        # Check metrics updated
        metrics = dfs_engine.metrics
        
        if metrics["jump_count"] > 0:
            self.assertGreaterEqual(metrics["jump_success_rate"], 0)
            self.assertLessEqual(metrics["jump_success_rate"], 1)
            
            print(f"✓ Jump metrics: count={metrics['jump_count']}, "
                  f"success_rate={metrics['jump_success_rate']:.2%}")
        else:
            print("✓ No jumps needed in test queries")


def run_tests():
    """Run all global jump tests"""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add test classes
    suite.addTests(loader.loadTestsFromTestCase(TestGlobalIndex))
    suite.addTests(loader.loadTestsFromTestCase(TestGlobalJump))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print("\n" + "="*60)
    print("GLOBAL JUMP TEST SUMMARY")
    print("="*60)
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Success rate: {(result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100:.1f}%")
    
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)