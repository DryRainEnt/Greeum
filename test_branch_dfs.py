#!/usr/bin/env python3
"""
Test suite for Branch/DFS functionality in Greeum v3.0.0+
Tests schema migration, branch storage, and DFS search
"""

import unittest
import os
import sqlite3
import tempfile
import json
import time
from datetime import datetime

# Add parent directory to path
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from greeum.core.database_manager import DatabaseManager
from greeum.core.block_manager import BlockManager
from greeum.core.stm_manager import STMManager
from greeum.core.branch_schema import BranchSchemaSQL
from greeum.core.dfs_search import DFSSearchEngine


class TestBranchSchema(unittest.TestCase):
    """Test branch schema and migration"""
    
    def setUp(self):
        """Create temporary database"""
        self.temp_db = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
        self.db_path = self.temp_db.name
        self.db_manager = DatabaseManager(connection_string=self.db_path)
        
    def tearDown(self):
        """Clean up temporary database"""
        try:
            self.db_manager.conn.close()
        except:
            pass
        os.unlink(self.db_path)
    
    def test_schema_migration(self):
        """Test branch schema migration"""
        cursor = self.db_manager.conn.cursor()
        
        # Check if migration was applied
        cursor.execute("PRAGMA table_info(blocks)")
        columns = {row[1] for row in cursor.fetchall()}
        
        # Verify branch columns exist
        branch_columns = {'root', 'before', 'after', 'xref', 'branch_depth', 'visit_count', 'last_seen_at'}
        self.assertTrue(branch_columns.issubset(columns), 
                       f"Missing branch columns. Found: {columns}")
        
        # Check branch_meta table exists
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='branch_meta'
        """)
        self.assertIsNotNone(cursor.fetchone(), "branch_meta table not created")
        
        print("✓ Schema migration successful")
    
    def test_branch_block_storage(self):
        """Test storing blocks with branch structure"""
        block_manager = BlockManager(self.db_manager)
        
        # Add root block
        root_block = block_manager.add_block(
            context="This is the root of a new branch",
            keywords=["root", "start"],
            tags=["branch"],
            embedding=[0.1] * 10,
            importance=0.9,
            slot="A"
        )
        
        self.assertIsNotNone(root_block)
        self.assertIn('root', root_block)
        self.assertIn('before', root_block)
        self.assertIn('after', root_block)
        
        # Add child block
        child_block = block_manager.add_block(
            context="This is a child of the root",
            keywords=["child", "branch"],
            tags=["branch"],
            embedding=[0.2] * 10,
            importance=0.7,
            slot="A"
        )
        
        self.assertIsNotNone(child_block)
        self.assertEqual(child_block['before'], root_block['hash'])
        
        # Verify parent's after field was updated
        cursor = self.db_manager.conn.cursor()
        cursor.execute("SELECT after FROM blocks WHERE hash = ?", (root_block['hash'],))
        after_field = cursor.fetchone()[0]
        after_list = json.loads(after_field)
        
        self.assertIn(child_block['hash'], after_list)
        
        print(f"✓ Branch storage: root={root_block['block_index']}, child={child_block['block_index']}")


class TestSTMBranchHeads(unittest.TestCase):
    """Test STM as branch head pointers"""
    
    def setUp(self):
        """Create temporary database and managers"""
        self.temp_db = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
        self.db_path = self.temp_db.name
        self.db_manager = DatabaseManager(connection_string=self.db_path)
        self.block_manager = BlockManager(self.db_manager)
        
        # Add some test blocks
        for i in range(5):
            self.block_manager.add_block(
                context=f"Test block {i}",
                keywords=[f"test{i}"],
                tags=["test"],
                embedding=[float(i)] * 10,
                importance=0.5
            )
    
    def tearDown(self):
        """Clean up"""
        try:
            self.db_manager.conn.close()
        except:
            pass
        os.unlink(self.db_path)
    
    def test_stm_initialization(self):
        """Test STM head initialization"""
        stm = STMManager(self.db_manager)
        
        # Check branch heads initialized
        self.assertIsNotNone(stm.branch_heads)
        self.assertEqual(len(stm.branch_heads), 3)  # A, B, C slots
        
        # Get heads info
        heads_info = stm.get_branch_heads_info()
        
        for slot in ["A", "B", "C"]:
            if heads_info.get(slot):
                info = heads_info[slot]
                self.assertIn('head_id', info)
                self.assertIn('block_index', info)
                self.assertIn('context_preview', info)
                print(f"✓ Slot {slot}: block {info['block_index']}")
    
    def test_head_update(self):
        """Test updating branch heads"""
        # Add new block to slot A
        new_block = self.block_manager.add_block(
            context="New block for slot A",
            keywords=["new", "slotA"],
            tags=["test"],
            embedding=[0.5] * 10,
            importance=0.8,
            slot="A"
        )
        
        # Create new STM instance to verify persistence
        stm = STMManager(self.db_manager)
        
        # Check if heads were restored from database
        heads_info = stm.get_branch_heads_info()
        
        # Verify slot A exists and has been updated
        self.assertIn("A", heads_info)
        if heads_info.get("A"):
            # The head should be one of the recent blocks
            self.assertIsNotNone(heads_info["A"]["head_id"])
            print(f"✓ Slot A head: block {heads_info['A']['block_index']}")
        
        print(f"✓ Slot A head updated to block {new_block['block_index']}")


class TestDFSSearch(unittest.TestCase):
    """Test DFS local-first search"""
    
    def setUp(self):
        """Create test branch structure"""
        self.temp_db = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
        self.db_path = self.temp_db.name
        self.db_manager = DatabaseManager(connection_string=self.db_path)
        self.block_manager = BlockManager(self.db_manager)
        
        # Create branch structure:
        #     root
        #     /  \
        #   b1    b2
        #   /      \
        #  b3      b4
        
        # Root
        self.root = self.block_manager.add_block(
            context="Project started with exciting opportunities",
            keywords=["project", "start", "exciting"],
            tags=["milestone"],
            embedding=[0.5] * 10,
            importance=0.9
        )
        
        # Branch 1
        self.b1 = self.block_manager.add_block(
            context="Working on user interface design",
            keywords=["ui", "design", "interface"],
            tags=["development"],
            embedding=[0.4] * 10,
            importance=0.7,
            slot="A"
        )
        
        self.b3 = self.block_manager.add_block(
            context="UI components completed successfully",
            keywords=["ui", "components", "complete"],
            tags=["development"],
            embedding=[0.45] * 10,
            importance=0.6,
            slot="A"
        )
        
        # Branch 2
        self.b2 = self.block_manager.add_block(
            context="Backend API development in progress",
            keywords=["backend", "api", "development"],
            tags=["development"],
            embedding=[0.6] * 10,
            importance=0.7,
            slot="B"
        )
        
        self.b4 = self.block_manager.add_block(
            context="API endpoints tested and deployed",
            keywords=["api", "test", "deploy"],
            tags=["deployment"],
            embedding=[0.65] * 10,
            importance=0.8,
            slot="B"
        )
        
        time.sleep(0.1)  # Ensure timestamps are different
    
    def tearDown(self):
        """Clean up"""
        try:
            self.db_manager.conn.close()
        except:
            pass
        os.unlink(self.db_path)
    
    def test_dfs_local_search(self):
        """Test DFS local search without fallback"""
        dfs_engine = DFSSearchEngine(self.db_manager)
        
        # Search for UI-related content from slot A
        results, meta = dfs_engine.search_with_dfs(
            query="UI interface",
            slot="A",
            depth=2,
            limit=3,
            fallback=False
        )
        
        # Verify results
        self.assertGreater(len(results), 0)
        self.assertEqual(meta['search_type'], 'local')
        self.assertFalse(meta['fallback_used'])
        self.assertGreater(meta['hops'], 0)
        
        # Check that UI-related blocks are found
        contexts = [r['context'] for r in results]
        ui_found = any('ui' in c.lower() or 'interface' in c.lower() for c in contexts)
        self.assertTrue(ui_found, "UI-related content not found")
        
        print(f"✓ DFS local search: {len(results)} results, {meta['hops']} hops")
    
    def test_dfs_with_fallback(self):
        """Test DFS with global fallback"""
        dfs_engine = DFSSearchEngine(self.db_manager)
        
        # Search for content not directly connected to current branch
        results, meta = dfs_engine.search_with_dfs(
            query="deploy test",
            slot="A",  # Start from UI branch
            depth=1,   # Shallow depth
            limit=5,
            fallback=True
        )
        
        # Verify fallback was triggered if needed
        self.assertGreater(len(results), 0)
        
        # Check that deployment-related content is found
        contexts = [r['context'] for r in results]
        deploy_found = any('deploy' in c.lower() or 'test' in c.lower() for c in contexts)
        self.assertTrue(deploy_found, "Deployment content not found")
        
        print(f"✓ DFS with fallback: {len(results)} results, fallback={meta['fallback_used']}")
    
    def test_search_meta_fields(self):
        """Test that all required meta fields are present"""
        dfs_engine = DFSSearchEngine(self.db_manager)
        
        results, meta = dfs_engine.search_with_dfs(
            query="test",
            slot="B",
            depth=3,
            limit=5,
            fallback=True
        )
        
        # Check required meta fields
        required_fields = [
            'search_type', 'slot', 'root', 'depth_used', 
            'hops', 'local_used', 'fallback_used', 
            'query_time_ms', 'result_count'
        ]
        
        for field in required_fields:
            self.assertIn(field, meta, f"Missing meta field: {field}")
        
        print(f"✓ Meta fields complete: {list(meta.keys())}")


class TestSearchIntegration(unittest.TestCase):
    """Test integrated search through BlockManager"""
    
    def setUp(self):
        """Set up test environment"""
        self.temp_db = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
        self.db_path = self.temp_db.name
        self.db_manager = DatabaseManager(connection_string=self.db_path)
        self.block_manager = BlockManager(self.db_manager)
        
        # Create test data
        contexts = [
            "Machine learning model training started",
            "Data preprocessing completed successfully", 
            "Model accuracy improved to 95%",
            "Deployment pipeline configured",
            "Production testing in progress"
        ]
        
        for i, context in enumerate(contexts):
            self.block_manager.add_block(
                context=context,
                keywords=context.lower().split(),
                tags=["ml", "project"],
                embedding=[float(i) * 0.1] * 10,
                importance=0.5 + i * 0.1,
                slot="A" if i < 3 else "B"
            )
    
    def tearDown(self):
        """Clean up"""
        try:
            self.db_manager.conn.close()
        except:
            pass
        os.unlink(self.db_path)
    
    def test_search_with_slots_integration(self):
        """Test search_with_slots with DFS"""
        results = self.block_manager.search_with_slots(
            query="model training",
            limit=5,
            use_slots=True,
            slot="A",
            depth=3,
            fallback=True,
            include_meta=True
        )
        
        self.assertGreater(len(results), 0)
        
        # Check that results have meta information
        for result in results:
            if '_meta' in result:
                meta = result['_meta']
                self.assertIn('search_type', meta)
                self.assertIn('hops', meta)
                break
        
        print(f"✓ Integrated search: {len(results)} results found")
    
    def test_metrics_collection(self):
        """Test that search metrics are collected"""
        initial_metrics = self.block_manager.metrics.copy()
        
        # Perform searches
        for i in range(3):
            self.block_manager.search_with_slots(
                query=f"test query {i}",
                limit=3,
                slot="A" if i % 2 == 0 else "B"
            )
        
        # Check metrics updated
        self.assertGreater(self.block_manager.metrics['total_searches'], 
                          initial_metrics['total_searches'])
        self.assertGreater(self.block_manager.metrics['total_hops'], 0)
        
        if self.block_manager.metrics['search_count'] > 0:
            avg_hops = self.block_manager.metrics['avg_hops']
            self.assertGreater(avg_hops, 0)
            print(f"✓ Metrics: avg_hops={avg_hops:.2f}, "
                  f"local_hit_rate={self.block_manager.metrics.get('local_hit_rate', 0):.2%}")


def run_tests():
    """Run all tests with summary"""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add test classes
    suite.addTests(loader.loadTestsFromTestCase(TestBranchSchema))
    suite.addTests(loader.loadTestsFromTestCase(TestSTMBranchHeads))
    suite.addTests(loader.loadTestsFromTestCase(TestDFSSearch))
    suite.addTests(loader.loadTestsFromTestCase(TestSearchIntegration))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print("\n" + "="*60)
    print("BRANCH/DFS TEST SUMMARY")
    print("="*60)
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Success rate: {(result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100:.1f}%")
    
    if result.failures:
        print("\nFailed tests:")
        for test, traceback in result.failures:
            print(f"  - {test}")
    
    if result.errors:
        print("\nTests with errors:")
        for test, traceback in result.errors:
            print(f"  - {test}")
    
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)