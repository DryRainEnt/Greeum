"""
Test suite for MetricsCollector functionality
"""

import unittest
import tempfile
import os
import time
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock

from tests.base_test_case import BaseGreeumTestCase


class TestMetricsCollector(BaseGreeumTestCase):
    """Test MetricsCollector core functionality"""
    
    def setUp(self):
        super().setUp()
        # Try to import MetricsCollector, skip tests if not available
        try:
            from greeum.core.metrics_collector import MetricsCollector
            self.metrics_collector = MetricsCollector()
        except ImportError:
            self.skipTest("MetricsCollector not available")
    
    def test_metrics_collector_initialization(self):
        """Test MetricsCollector initialization"""
        self.assertIsNotNone(self.metrics_collector)
    
    def test_collect_performance_metrics(self):
        """Test collecting performance metrics"""
        # Collect performance metrics
        metrics_data = {
            'operation': 'memory_search',
            'duration': 0.15,
            'memory_usage': 1024 * 1024,  # 1MB
            'cpu_usage': 0.25,
            'timestamp': datetime.now().isoformat()
        }
        
        result = self.metrics_collector.collect_performance_metrics(metrics_data)
        
        self.assertIsNotNone(result)
        self.assertIn('metric_id', result)
    
    def test_collect_system_metrics(self):
        """Test collecting system metrics"""
        # Collect system metrics
        system_data = {
            'cpu_percent': 45.2,
            'memory_percent': 67.8,
            'disk_usage_percent': 23.4,
            'network_io': {'bytes_sent': 1024, 'bytes_recv': 2048},
            'timestamp': datetime.now().isoformat()
        }
        
        result = self.metrics_collector.collect_system_metrics(system_data)
        
        self.assertIsNotNone(result)
        self.assertIn('metric_id', result)
    
    def test_collect_user_metrics(self):
        """Test collecting user behavior metrics"""
        # Collect user metrics
        user_data = {
            'user_id': 'test_user',
            'action': 'memory_addition',
            'context_length': 150,
            'importance_score': 0.7,
            'response_time': 0.08,
            'timestamp': datetime.now().isoformat()
        }
        
        result = self.metrics_collector.collect_user_metrics(user_data)
        
        self.assertIsNotNone(result)
        self.assertIn('metric_id', result)
    
    def test_collect_error_metrics(self):
        """Test collecting error metrics"""
        # Collect error metrics
        error_data = {
            'error_type': 'DatabaseConnectionError',
            'error_message': 'Connection timeout',
            'component': 'database_manager',
            'severity': 'high',
            'timestamp': datetime.now().isoformat()
        }
        
        result = self.metrics_collector.collect_error_metrics(error_data)
        
        self.assertIsNotNone(result)
        self.assertIn('metric_id', result)
    
    def test_get_metrics_summary(self):
        """Test getting metrics summary"""
        # Add some test metrics first
        for i in range(5):
            metrics_data = {
                'operation': f'test_operation_{i}',
                'duration': 0.1 + (i * 0.02),
                'memory_usage': 1024 * (i + 1),
                'cpu_usage': 0.2 + (i * 0.05),
                'timestamp': datetime.now().isoformat()
            }
            self.metrics_collector.collect_performance_metrics(metrics_data)
        
        # Get summary
        summary = self.metrics_collector.get_metrics_summary()
        
        self.assertIsInstance(summary, dict)
        self.assertIn('total_metrics', summary)
        self.assertIn('performance_metrics', summary)
        self.assertGreaterEqual(summary['total_metrics'], 5)
    
    def test_get_performance_report(self):
        """Test getting performance report"""
        # Add performance metrics
        performance_data = [
            {
                'operation': 'memory_search',
                'duration': 0.12,
                'memory_usage': 1024 * 1024,
                'cpu_usage': 0.3,
                'timestamp': datetime.now().isoformat()
            },
            {
                'operation': 'memory_addition',
                'duration': 0.08,
                'memory_usage': 512 * 1024,
                'cpu_usage': 0.2,
                'timestamp': datetime.now().isoformat()
            },
            {
                'operation': 'embedding_generation',
                'duration': 0.25,
                'memory_usage': 2048 * 1024,
                'cpu_usage': 0.4,
                'timestamp': datetime.now().isoformat()
            }
        ]
        
        for data in performance_data:
            self.metrics_collector.collect_performance_metrics(data)
        
        # Get performance report
        report = self.metrics_collector.get_performance_report()
        
        self.assertIsInstance(report, dict)
        self.assertIn('average_duration', report)
        self.assertIn('operations_summary', report)
        self.assertIn('resource_usage', report)
    
    def test_get_system_health_report(self):
        """Test getting system health report"""
        # Add system metrics
        system_data = [
            {
                'cpu_percent': 45.2,
                'memory_percent': 67.8,
                'disk_usage_percent': 23.4,
                'network_io': {'bytes_sent': 1024, 'bytes_recv': 2048},
                'timestamp': datetime.now().isoformat()
            },
            {
                'cpu_percent': 52.1,
                'memory_percent': 71.2,
                'disk_usage_percent': 24.1,
                'network_io': {'bytes_sent': 1536, 'bytes_recv': 3072},
                'timestamp': datetime.now().isoformat()
            }
        ]
        
        for data in system_data:
            self.metrics_collector.collect_system_metrics(data)
        
        # Get system health report
        health_report = self.metrics_collector.get_system_health_report()
        
        self.assertIsInstance(health_report, dict)
        self.assertIn('cpu_health', health_report)
        self.assertIn('memory_health', health_report)
        self.assertIn('disk_health', health_report)
        self.assertIn('overall_health', health_report)
    
    def test_get_error_report(self):
        """Test getting error report"""
        # Add error metrics
        error_data = [
            {
                'error_type': 'DatabaseConnectionError',
                'error_message': 'Connection timeout',
                'component': 'database_manager',
                'severity': 'high',
                'timestamp': datetime.now().isoformat()
            },
            {
                'error_type': 'ValidationError',
                'error_message': 'Invalid input format',
                'component': 'block_manager',
                'severity': 'medium',
                'timestamp': datetime.now().isoformat()
            },
            {
                'error_type': 'NetworkError',
                'error_message': 'Request timeout',
                'component': 'api_server',
                'severity': 'low',
                'timestamp': datetime.now().isoformat()
            }
        ]
        
        for data in error_data:
            self.metrics_collector.collect_error_metrics(data)
        
        # Get error report
        error_report = self.metrics_collector.get_error_report()
        
        self.assertIsInstance(error_report, dict)
        self.assertIn('error_count', error_report)
        self.assertIn('errors_by_type', error_report)
        self.assertIn('errors_by_severity', error_report)
        self.assertIn('errors_by_component', error_report)
    
    def test_export_metrics_data(self):
        """Test exporting metrics data"""
        # Add some test metrics
        for i in range(3):
            metrics_data = {
                'operation': f'export_test_{i}',
                'duration': 0.1,
                'memory_usage': 1024,
                'cpu_usage': 0.2,
                'timestamp': datetime.now().isoformat()
            }
            self.metrics_collector.collect_performance_metrics(metrics_data)
        
        # Export data
        export_result = self.metrics_collector.export_metrics_data()
        
        self.assertIsNotNone(export_result)
        self.assertIn('data', export_result)
        self.assertIn('export_timestamp', export_result)
        self.assertIn('metrics_count', export_result)
    
    def test_clear_metrics_data(self):
        """Test clearing metrics data"""
        # Add some test metrics first
        for i in range(3):
            metrics_data = {
                'operation': f'clear_test_{i}',
                'duration': 0.1,
                'memory_usage': 1024,
                'cpu_usage': 0.2,
                'timestamp': datetime.now().isoformat()
            }
            self.metrics_collector.collect_performance_metrics(metrics_data)
        
        # Verify data exists
        summary_before = self.metrics_collector.get_metrics_summary()
        self.assertGreaterEqual(summary_before['total_metrics'], 3)
        
        # Clear data
        clear_result = self.metrics_collector.clear_metrics_data()
        
        self.assertTrue(clear_result)
        
        # Verify data is cleared
        summary_after = self.metrics_collector.get_metrics_summary()
        self.assertEqual(summary_after['total_metrics'], 0)


class TestMetricsCollectorIntegration(BaseGreeumTestCase):
    """Integration tests for MetricsCollector"""
    
    def setUp(self):
        super().setUp()
        try:
            from greeum.core.metrics_collector import MetricsCollector
            self.metrics_collector = MetricsCollector()
        except ImportError:
            self.skipTest("MetricsCollector not available")
        
        self.setup_database_with_test_data(3)
    
    def test_metrics_collector_with_block_manager(self):
        """Test MetricsCollector integration with BlockManager"""
        # Monitor BlockManager operations
        start_time = time.time()
        
        # Perform BlockManager operation
        test_context = "Metrics integration test with BlockManager"
        result = self.block_manager.add_block(
            context=test_context,
            keywords=["metrics", "integration"],
            tags=["test"],
            embedding=self.get_test_embedding(test_context),
            importance=0.7
        )
        
        duration = time.time() - start_time
        
        # Collect metrics for the operation
        metrics_data = {
            'operation': 'block_manager.add_block',
            'duration': duration,
            'memory_usage': 1024 * 1024,  # Estimated
            'cpu_usage': 0.3,  # Estimated
            'success': result is not None,
            'timestamp': datetime.now().isoformat()
        }
        
        metrics_result = self.metrics_collector.collect_performance_metrics(metrics_data)
        
        self.assertIsNotNone(metrics_result)
        self.assertIn('metric_id', metrics_result)
    
    def test_metrics_collector_with_stm_manager(self):
        """Test MetricsCollector integration with STMManager"""
        # Monitor STMManager operations
        start_time = time.time()
        
        # Perform STMManager operation
        stm_data = {
            'context': 'STM metrics integration test',
            'keywords': ['stm', 'metrics'],
            'tags': ['test'],
            'importance': 0.6,
            'metadata': {'test': True}
        }
        
        stm_result = self.stm_manager.add_to_stm(stm_data)
        duration = time.time() - start_time
        
        # Collect metrics for the operation
        metrics_data = {
            'operation': 'stm_manager.add_to_stm',
            'duration': duration,
            'memory_usage': 512 * 1024,  # Estimated
            'cpu_usage': 0.2,  # Estimated
            'success': stm_result is not None,
            'timestamp': datetime.now().isoformat()
        }
        
        metrics_result = self.metrics_collector.collect_performance_metrics(metrics_data)
        
        self.assertIsNotNone(metrics_result)
        self.assertIn('metric_id', metrics_result)
    
    def test_comprehensive_metrics_collection(self):
        """Test comprehensive metrics collection scenario"""
        # Simulate a complete operation with multiple components
        operations = [
            {
                'component': 'block_manager',
                'operation': 'add_block',
                'duration': 0.12,
                'memory_usage': 1024 * 1024,
                'cpu_usage': 0.3
            },
            {
                'component': 'stm_manager',
                'operation': 'add_to_stm',
                'duration': 0.08,
                'memory_usage': 512 * 1024,
                'cpu_usage': 0.2
            },
            {
                'component': 'search_engine',
                'operation': 'search_by_embedding',
                'duration': 0.15,
                'memory_usage': 2048 * 1024,
                'cpu_usage': 0.4
            }
        ]
        
        # Collect metrics for all operations
        for op in operations:
            metrics_data = {
                'operation': f"{op['component']}.{op['operation']}",
                'duration': op['duration'],
                'memory_usage': op['memory_usage'],
                'cpu_usage': op['cpu_usage'],
                'timestamp': datetime.now().isoformat()
            }
            self.metrics_collector.collect_performance_metrics(metrics_data)
        
        # Get comprehensive report
        performance_report = self.metrics_collector.get_performance_report()
        
        self.assertIsInstance(performance_report, dict)
        self.assertIn('average_duration', performance_report)
        self.assertIn('operations_summary', performance_report)
        self.assertIn('resource_usage', performance_report)
        
        # Verify all operations are included
        operations_summary = performance_report['operations_summary']
        self.assertGreater(len(operations_summary), 0)
    
    def test_metrics_collection_with_errors(self):
        """Test metrics collection with error scenarios"""
        # Simulate various error conditions
        error_scenarios = [
            {
                'error_type': 'DatabaseConnectionError',
                'error_message': 'Connection timeout',
                'component': 'database_manager',
                'severity': 'high'
            },
            {
                'error_type': 'ValidationError',
                'error_message': 'Invalid input format',
                'component': 'block_manager',
                'severity': 'medium'
            },
            {
                'error_type': 'MemoryError',
                'error_message': 'Out of memory',
                'component': 'embedding_generator',
                'severity': 'critical'
            }
        ]
        
        # Collect error metrics
        for error in error_scenarios:
            error_data = {
                **error,
                'timestamp': datetime.now().isoformat()
            }
            self.metrics_collector.collect_error_metrics(error_data)
        
        # Get error report
        error_report = self.metrics_collector.get_error_report()
        
        self.assertIsInstance(error_report, dict)
        self.assertIn('error_count', error_report)
        self.assertIn('errors_by_type', error_report)
        self.assertIn('errors_by_severity', error_report)
        self.assertIn('errors_by_component', error_report)
        
        # Verify error count
        self.assertEqual(error_report['error_count'], 3)
        
        # Verify severity distribution
        errors_by_severity = error_report['errors_by_severity']
        self.assertIn('high', errors_by_severity)
        self.assertIn('medium', errors_by_severity)
        self.assertIn('critical', errors_by_severity)


if __name__ == '__main__':
    unittest.main()