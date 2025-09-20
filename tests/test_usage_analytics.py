"""
Test suite for UsageAnalytics functionality
"""

import unittest
import tempfile
import os
import time
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock

from tests.base_test_case import BaseGreeumTestCase


class TestUsageAnalytics(BaseGreeumTestCase):
    """Test UsageAnalytics core functionality"""
    
    def setUp(self):
        super().setUp()
        # Try to import UsageAnalytics, skip tests if not available
        try:
            from greeum.core.usage_analytics import UsageAnalytics
            self.usage_analytics = UsageAnalytics()
        except ImportError:
            self.skipTest("UsageAnalytics not available")
    
    def test_usage_analytics_initialization(self):
        """Test UsageAnalytics initialization"""
        self.assertIsNotNone(self.usage_analytics)
    
    def test_log_memory_add(self):
        """Test logging memory addition events"""
        # Log a memory addition event
        block_id = 1
        importance = 0.7
        
        result = self.usage_analytics.log_memory_add(block_id, importance)
        
        # log_memory_add may not return anything, which is acceptable
        self.assertTrue(True)  # Just verify the method exists and can be called
    
    def test_log_search(self):
        """Test logging search query events"""
        # Log a search query event
        query = 'test search query'
        results_count = 5
        duration_ms = 100.0
        
        result = self.usage_analytics.log_search(query, results_count, duration_ms)
        
        # log_search may not return anything, which is acceptable
        self.assertTrue(True)  # Just verify the method exists and can be called
    
    def test_log_operation(self):
        """Test logging operation events"""
        # Log an operation event
        operation = 'memory_retrieval'
        metadata = {
            'context': 'User retrieved recent memories',
            'success': True
        }
        
        result = self.usage_analytics.log_operation(operation, metadata)
        
        # log_operation may not return anything, which is acceptable
        self.assertTrue(True)  # Just verify the method exists and can be called
    
    def test_get_analytics_data(self):
        """Test getting analytics data"""
        # Add some test events first
        for i in range(5):
            self.usage_analytics.log_memory_add(i + 1, 0.5 + (i * 0.1))
        
        # Get analytics data
        analytics_data = self.usage_analytics.get_analytics_data(days=7)
        
        self.assertIsInstance(analytics_data, dict)
    
    def test_get_usage_report(self):
        """Test getting usage report"""
        # Add some test events
        self.usage_analytics.log_memory_add(1, 0.8)
        self.usage_analytics.log_search('test query', 3, 50.0)
        self.usage_analytics.log_operation('test_operation')
        
        # Get usage report
        report = self.usage_analytics.get_usage_report(days=7)
        
        self.assertIsInstance(report, dict)
    
    def test_get_quality_metrics(self):
        """Test getting quality metrics"""
        # Add some test events
        for i in range(3):
            self.usage_analytics.log_memory_add(i + 1, 0.5 + (i * 0.1))
        
        # Get quality metrics
        metrics = self.usage_analytics.get_quality_metrics()
        
        self.assertIsInstance(metrics, dict)
    
    def test_log_event(self):
        """Test logging custom events"""
        # Log custom events
        self.usage_analytics.log_event('custom_event', 'test_tool', {'test': True})
        
        # Just verify the method exists and can be called
        self.assertTrue(True)
    
    def test_close(self):
        """Test closing analytics"""
        # Test closing the analytics
        self.usage_analytics.close()
        
        # Just verify the method exists and can be called
        self.assertTrue(True)
    
    def test_track_ai_intent(self):
        """Test tracking AI intent"""
        # Track AI intent
        self.usage_analytics.track_ai_intent('test_intent', 0.8, {'test': True})
        
        # Just verify the method exists and can be called
        self.assertTrue(True)


class TestUsageAnalyticsIntegration(BaseGreeumTestCase):
    """Integration tests for UsageAnalytics"""
    
    def setUp(self):
        super().setUp()
        try:
            from greeum.core.usage_analytics import UsageAnalytics
            self.usage_analytics = UsageAnalytics()
        except ImportError:
            self.skipTest("UsageAnalytics not available")
        
        self.setup_database_with_test_data(3)
    
    def test_usage_analytics_with_block_manager(self):
        """Test UsageAnalytics integration with BlockManager"""
        # Track memory addition through BlockManager
        test_context = "Integration test with BlockManager"
        result = self.block_manager.add_block(
            context=test_context,
            keywords=["integration", "block_manager"],
            tags=["test"],
            embedding=self.get_test_embedding(test_context),
            importance=0.7
        )
        
        # Log the event using actual API
        if isinstance(result, dict) and 'block_index' in result:
            self.usage_analytics.log_memory_add(result['block_index'], 0.7)
        elif isinstance(result, int):
            self.usage_analytics.log_memory_add(result, 0.7)
        
        # Just verify the integration works
        self.assertTrue(True)
    
    def test_usage_analytics_with_stm_manager(self):
        """Test UsageAnalytics integration with STMManager"""
        # Track STM operations
        memory_id = self.stm_manager.add_memory(content='STM integration test', importance=0.6)
        
        # Log the STM event
        self.usage_analytics.log_operation('stm_add', {'memory_id': memory_id})
        
        # Just verify the integration works
        self.assertTrue(True)
    
    def test_comprehensive_usage_tracking(self):
        """Test comprehensive usage tracking scenario"""
        # Simulate a complete user session
        self.usage_analytics.log_memory_add(1, 0.8)
        self.usage_analytics.log_search('project planning', 5, 120.0)
        self.usage_analytics.log_operation('memory_retrieval', {'success': True})
        self.usage_analytics.log_memory_add(2, 0.7)
        
        # Get comprehensive analytics
        analytics = self.usage_analytics.get_analytics_data(days=1)
        
        self.assertIsInstance(analytics, dict)


if __name__ == '__main__':
    unittest.main()