#!/usr/bin/env python3
"""
Comprehensive Unit Tests for UsageAnalytics (Greeum v2.1.0)
Tests database initialization, event logging, quality metrics, statistics generation,
session management, and data cleanup functionality.
"""

import os
import json
import sqlite3
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
import threading
import time

from tests.base_test_case import BaseGreeumTestCase
from greeum.core.usage_analytics import UsageAnalytics


class TestUsageAnalytics(BaseGreeumTestCase):
    """Comprehensive test suite for UsageAnalytics class"""
    
    def setUp(self):
        """Set up test fixtures before each test method"""
        super().setUp()
        
        # Analytics 전용 데이터베이스 경로
        self.analytics_db_path = os.path.join(self.temp_dir, "test_analytics.db")
        
        # Initialize analytics with test database
        self.analytics = UsageAnalytics(
            db_manager=self.mock_db_manager,
            analytics_db_path=self.analytics_db_path
        )
    
    def test_database_initialization(self):
        """Test database schema creation and initialization"""
        # Verify database file was created
        self.assertTrue(os.path.exists(self.test_db_path))
        
        # Verify all required tables exist
        with sqlite3.connect(self.analytics_db_path) as conn:
            cursor = conn.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name NOT LIKE 'sqlite_%'
            """)
            tables = {row[0] for row in cursor.fetchall()}
            
        expected_tables = {
            'usage_events', 'quality_metrics', 
            'performance_metrics', 'user_sessions'
        }
        self.assertEqual(tables, expected_tables)
        
        # Verify table schemas
        with sqlite3.connect(self.analytics_db_path) as conn:
            # Check usage_events schema
            cursor = conn.execute("PRAGMA table_info(usage_events)")
            columns = {row[1] for row in cursor.fetchall()}
            expected_columns = {
                'id', 'timestamp', 'event_type', 'tool_name', 
                'user_id', 'session_id', 'metadata', 'duration_ms', 
                'success', 'error_message'
            }
            self.assertEqual(columns, expected_columns)
    
    def test_input_sanitization(self):
        """Test input sanitization and security measures"""
        # Test metadata sanitization
        dangerous_metadata = {
            "normal_key": "normal_value",
            "x" * 200: "too_long_key",  # Should be truncated
            "script_tag": "<script>alert('xss')</script>",
            123: "numeric_key",  # Should be converted to string
            "long_value": "x" * 2000,  # Should be truncated
            None: "null_key",  # Should be filtered out
            "nested": {"not": "allowed"}  # Should be filtered out
        }
        
        sanitized = self.analytics._sanitize_metadata(dangerous_metadata)
        
        # Check key length limits
        for key in sanitized.keys():
            self.assertLessEqual(len(key), 100)
        
        # Check value length limits
        for value in sanitized.values():
            if isinstance(value, str):
                self.assertLessEqual(len(value), 1000)
        
        # Check that dangerous content is handled
        self.assertIn("script_tag", sanitized)
        self.assertIn("123", sanitized)  # Numeric key converted to string
        self.assertNotIn(None, sanitized)  # None key filtered out
    
    def test_database_path_validation(self):
        """Test database path validation and security"""
        # Test valid paths
        valid_path = os.path.join(os.path.expanduser("~"), ".greeum", "test.db")
        validated = self.analytics._validate_db_path(valid_path)
        self.assertTrue(validated.endswith("test.db"))
        
        # Test invalid paths (should raise ValueError)
        with self.assertRaises(ValueError):
            self.analytics._validate_db_path("/etc/passwd")
        
        with self.assertRaises(ValueError):
            self.analytics._validate_db_path("/root/malicious.db")
    
    def test_event_logging_basic(self):
        """Test basic event logging functionality"""
        # Test successful event logging
        result = self.analytics.log_event(
            event_type="test_event",
            tool_name="test_tool",
            metadata={"test": "data"},
            duration_ms=150,
            success=True,
            user_id="test_user",
            session_id="test_session"
        )
        
        self.assertTrue(result)
        
        # Verify event was stored in database
        with sqlite3.connect(self.analytics_db_path) as conn:
            cursor = conn.execute("""
                SELECT event_type, tool_name, user_id, session_id, 
                       duration_ms, success, metadata
                FROM usage_events
                WHERE event_type = 'test_event'
            """)
            
            row = cursor.fetchone()
            self.assertIsNotNone(row)
            self.assertEqual(row[0], "test_event")
            self.assertEqual(row[1], "test_tool")
            self.assertEqual(row[2], "test_user")
            self.assertEqual(row[3], "test_session")
            self.assertEqual(row[4], 150)
            self.assertEqual(row[5], True)
            
            # Check metadata JSON
            metadata = json.loads(row[6])
            self.assertEqual(metadata["test"], "data")
    
    def test_event_logging_edge_cases(self):
        """Test event logging with edge cases and validation"""
        # Test with None values
        result = self.analytics.log_event(
            event_type="test",
            tool_name=None,
            metadata=None,
            duration_ms=None,
            success=True
        )
        self.assertTrue(result)
        
        # Test with invalid duration (should be sanitized)
        result = self.analytics.log_event(
            event_type="test",
            duration_ms=-100  # Invalid negative duration
        )
        self.assertTrue(result)
        
        # Test with very long strings (should be truncated)
        long_string = "x" * 1000
        result = self.analytics.log_event(
            event_type=long_string,
            tool_name=long_string,
            user_id=long_string,
            session_id=long_string,
            error_message=long_string
        )
        self.assertTrue(result)
        
        # Verify truncation occurred
        with sqlite3.connect(self.analytics_db_path) as conn:
            cursor = conn.execute("""
                SELECT event_type, tool_name, user_id, session_id, error_message
                FROM usage_events
                ORDER BY id DESC LIMIT 1
            """)
            
            row = cursor.fetchone()
            self.assertLessEqual(len(row[0]), 50)  # event_type
            self.assertLessEqual(len(row[1]), 50)  # tool_name
            self.assertLessEqual(len(row[2]), 50)  # user_id
            self.assertLessEqual(len(row[3]), 100)  # session_id
            self.assertLessEqual(len(row[4]), 500)  # error_message
    
    def test_quality_metrics_logging(self):
        """Test quality metrics logging functionality"""
        result = self.analytics.log_quality_metrics(
            content_length=250,
            quality_score=0.85,
            quality_level="good",
            importance=0.7,
            adjusted_importance=0.75,
            is_duplicate=False,
            duplicate_similarity=0.2,
            suggestions_count=3
        )
        
        self.assertTrue(result)
        
        # Verify metrics were stored
        with sqlite3.connect(self.analytics_db_path) as conn:
            cursor = conn.execute("""
                SELECT content_length, quality_score, quality_level, 
                       importance, adjusted_importance, is_duplicate,
                       duplicate_similarity, suggestions_count
                FROM quality_metrics
            """)
            
            row = cursor.fetchone()
            self.assertIsNotNone(row)
            self.assertEqual(row[0], 250)  # content_length
            self.assertEqual(row[1], 0.85)  # quality_score
            self.assertEqual(row[2], "good")  # quality_level
            self.assertEqual(row[3], 0.7)  # importance
            self.assertEqual(row[4], 0.75)  # adjusted_importance
            self.assertEqual(row[5], False)  # is_duplicate
            self.assertEqual(row[6], 0.2)  # duplicate_similarity
            self.assertEqual(row[7], 3)  # suggestions_count
    
    def test_performance_metrics_logging(self):
        """Test performance metrics logging"""
        result = self.analytics.log_performance_metric(
            metric_type="memory",
            metric_name="heap_usage",
            metric_value=1024.5,
            unit="MB",
            metadata={"process": "test"}
        )
        
        self.assertTrue(result)
        
        # Verify performance metrics were stored
        with sqlite3.connect(self.analytics_db_path) as conn:
            cursor = conn.execute("""
                SELECT metric_type, metric_name, metric_value, unit, metadata
                FROM performance_metrics
            """)
            
            row = cursor.fetchone()
            self.assertIsNotNone(row)
            self.assertEqual(row[0], "memory")
            self.assertEqual(row[1], "heap_usage")
            self.assertEqual(row[2], 1024.5)
            self.assertEqual(row[3], "MB")
            
            metadata = json.loads(row[4])
            self.assertEqual(metadata["process"], "test")
    
    def test_session_management(self):
        """Test user session start/end functionality"""
        session_id = "test_session_123"
        
        # Test session start
        result = self.analytics.start_session(
            session_id=session_id,
            user_agent="test_agent",
            client_type="test_client"
        )
        self.assertTrue(result)
        
        # Add some events to the session
        self.analytics.log_event("tool_usage", "add_memory", session_id=session_id)
        self.analytics.log_event("tool_usage", "search_memory", session_id=session_id)
        
        # Add some quality metrics
        self.analytics.log_quality_metrics(100, 0.8, "good", 0.5, 0.6)
        
        # Test session end
        result = self.analytics.end_session(session_id)
        self.assertTrue(result)
        
        # Verify session was updated with statistics
        with sqlite3.connect(self.analytics_db_path) as conn:
            cursor = conn.execute("""
                SELECT session_id, total_operations, memory_added, 
                       searches_performed, avg_quality_score, end_time
                FROM user_sessions
                WHERE session_id = ?
            """, (session_id,))
            
            row = cursor.fetchone()
            self.assertIsNotNone(row)
            self.assertEqual(row[0], session_id)
            self.assertEqual(row[1], 2)  # total_operations
            self.assertEqual(row[2], 1)  # memory_added (add_memory events)
            self.assertEqual(row[3], 1)  # searches_performed
            self.assertIsNotNone(row[5])  # end_time should be set
    
    def test_usage_statistics_generation(self):
        """Test usage statistics generation"""
        # Add test data
        self.analytics.log_event("tool_usage", "add_memory", duration_ms=100, success=True)
        self.analytics.log_event("tool_usage", "search_memory", duration_ms=50, success=True)
        self.analytics.log_event("tool_usage", "add_memory", duration_ms=200, success=False)
        
        self.analytics.log_quality_metrics(100, 0.8, "good", 0.5, 0.6, False, 0.1, 2)
        self.analytics.log_quality_metrics(200, 0.9, "excellent", 0.7, 0.8, True, 0.9, 1)
        
        # Generate statistics
        stats = self.analytics.get_usage_statistics(days=1)
        
        # Verify structure and content
        self.assertIn("basic_stats", stats)
        self.assertIn("tool_usage", stats)
        self.assertIn("quality_stats", stats)
        self.assertIn("hourly_usage", stats)
        
        basic_stats = stats["basic_stats"]
        self.assertEqual(basic_stats["total_events"], 3)
        self.assertEqual(basic_stats["successful_events"], 2)
        self.assertAlmostEqual(basic_stats["success_rate"], 2/3, places=2)
        self.assertAlmostEqual(basic_stats["avg_duration_ms"], (100+50+200)/3, places=1)
        
        # Check tool usage
        tool_usage = stats["tool_usage"]
        self.assertEqual(tool_usage.get("add_memory", 0), 2)
        self.assertEqual(tool_usage.get("search_memory", 0), 1)
        
        # Check quality stats
        quality_stats = stats["quality_stats"]
        self.assertAlmostEqual(quality_stats["avg_quality_score"], 0.85, places=2)
        self.assertEqual(quality_stats["duplicate_rate"], 0.5)  # 1 out of 2
    
    def test_quality_trends_analysis(self):
        """Test quality trends analysis"""
        # Add test data across different dates
        base_time = datetime.now() - timedelta(days=5)
        
        # Manually insert data with specific timestamps
        with sqlite3.connect(self.analytics_db_path) as conn:
            for i in range(5):
                timestamp = (base_time + timedelta(days=i)).isoformat()
                conn.execute("""
                    INSERT INTO quality_metrics 
                    (timestamp, content_length, quality_score, quality_level, 
                     importance, adjusted_importance, is_duplicate, duplicate_similarity, suggestions_count)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (timestamp, 100+i*10, 0.7+i*0.05, "good", 0.5, 0.6, False, 0.1, 2))
            conn.commit()
        
        # Generate quality trends
        trends = self.analytics.get_quality_trends(days=7)
        
        # Verify structure
        self.assertIn("daily_trends", trends)
        self.assertIn("quality_distribution", trends)
        self.assertIn("duplicate_trends", trends)
        
        # Check daily trends
        daily_trends = trends["daily_trends"]
        self.assertEqual(len(daily_trends), 5)
        
        # Check quality distribution
        quality_distribution = trends["quality_distribution"]
        self.assertEqual(quality_distribution.get("good", 0), 5)
    
    def test_performance_insights(self):
        """Test performance insights generation"""
        # Add test performance data
        self.analytics.log_event("tool_usage", "slow_tool", duration_ms=2000, success=True)
        self.analytics.log_event("tool_usage", "fast_tool", duration_ms=50, success=True) 
        self.analytics.log_event("tool_usage", "error_tool", duration_ms=100, success=False, error_message="Test error")
        
        self.analytics.log_performance_metric("cpu", "usage_percent", 75.5, "percent")
        self.analytics.log_performance_metric("memory", "heap_size", 512.0, "MB")
        
        # Generate insights
        insights = self.analytics.get_performance_insights(days=1)
        
        # Verify structure
        self.assertIn("performance_by_tool", insights)
        self.assertIn("error_patterns", insights)
        self.assertIn("resource_metrics", insights)
        self.assertIn("recommendations", insights)
        
        # Check performance data
        perf_by_tool = insights["performance_by_tool"]
        self.assertEqual(len(perf_by_tool), 3)
        
        # Find slow_tool in results
        slow_tool_data = next((p for p in perf_by_tool if p["tool_name"] == "slow_tool"), None)
        self.assertIsNotNone(slow_tool_data)
        self.assertEqual(slow_tool_data["avg_duration_ms"], 2000)
        
        # Check error patterns
        error_patterns = insights["error_patterns"]
        self.assertEqual(len(error_patterns), 1)
        self.assertEqual(error_patterns[0]["tool_name"], "error_tool")
        
        # Check resource metrics
        resource_metrics = insights["resource_metrics"]
        self.assertEqual(len(resource_metrics), 2)
        
        # Check recommendations
        recommendations = insights["recommendations"]
        self.assertIsInstance(recommendations, list)
        self.assertGreater(len(recommendations), 0)
    
    def test_data_cleanup(self):
        """Test old data cleanup functionality"""
        # Add old test data
        old_time = datetime.now() - timedelta(days=100)
        recent_time = datetime.now() - timedelta(days=1)
        
        with sqlite3.connect(self.analytics_db_path) as conn:
            # Add old events
            conn.execute("""
                INSERT INTO usage_events (timestamp, event_type, tool_name)
                VALUES (?, 'old_event', 'old_tool')
            """, (old_time.isoformat(),))
            
            # Add recent events
            conn.execute("""
                INSERT INTO usage_events (timestamp, event_type, tool_name)
                VALUES (?, 'recent_event', 'recent_tool')
            """, (recent_time.isoformat(),))
            
            # Add old quality metrics
            conn.execute("""
                INSERT INTO quality_metrics (timestamp, content_length, quality_score, quality_level, importance, adjusted_importance)
                VALUES (?, 100, 0.5, 'acceptable', 0.5, 0.5)
            """, (old_time.isoformat(),))
            
            # Add old completed session
            conn.execute("""
                INSERT INTO user_sessions (session_id, start_time, end_time)
                VALUES ('old_session', ?, ?)
            """, (old_time.isoformat(), old_time.isoformat()))
            
            conn.commit()
        
        # Cleanup old data (keep last 30 days)
        deleted_counts = self.analytics.cleanup_old_data(days_to_keep=30)
        
        # Verify cleanup results
        self.assertIn("usage_events", deleted_counts)
        self.assertIn("quality_metrics", deleted_counts)
        self.assertIn("user_sessions", deleted_counts)
        
        self.assertEqual(deleted_counts["usage_events"], 1)
        self.assertEqual(deleted_counts["quality_metrics"], 1)
        self.assertEqual(deleted_counts["user_sessions"], 1)
        
        # Verify recent data still exists
        with sqlite3.connect(self.analytics_db_path) as conn:
            cursor = conn.execute("SELECT COUNT(*) FROM usage_events WHERE event_type = 'recent_event'")
            self.assertEqual(cursor.fetchone()[0], 1)
    
    def test_thread_safety(self):
        """Test thread safety of concurrent operations"""
        def log_events(thread_id, num_events=10):
            for i in range(num_events):
                self.analytics.log_event(
                    event_type="thread_test",
                    tool_name=f"tool_{thread_id}",
                    metadata={"thread": thread_id, "event": i},
                    duration_ms=i * 10,
                    success=True,
                    session_id=f"session_{thread_id}"
                )
        
        # Start multiple threads
        threads = []
        num_threads = 5
        
        for i in range(num_threads):
            thread = threading.Thread(target=log_events, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Verify all events were logged correctly
        with sqlite3.connect(self.analytics_db_path) as conn:
            cursor = conn.execute("SELECT COUNT(*) FROM usage_events WHERE event_type = 'thread_test'")
            total_events = cursor.fetchone()[0]
            
        self.assertEqual(total_events, num_threads * 10)
        
        # Verify data integrity (no corruption)
        with sqlite3.connect(self.analytics_db_path) as conn:
            cursor = conn.execute("""
                SELECT DISTINCT tool_name FROM usage_events 
                WHERE event_type = 'thread_test'
                ORDER BY tool_name
            """)
            tools = [row[0] for row in cursor.fetchall()]
            
        expected_tools = [f"tool_{i}" for i in range(num_threads)]
        self.assertEqual(tools, expected_tools)
    
    def test_error_handling(self):
        """Test error handling and graceful degradation"""
        # Test with inaccessible database path (permission denied scenario)
        bad_analytics = UsageAnalytics(analytics_db_path="/root/impossible.db")
        
        # These should fail gracefully and return False
        result = bad_analytics.log_event("test", "test")
        self.assertFalse(result)
        
        result = bad_analytics.log_quality_metrics(100, 0.5, "test", 0.5, 0.5)
        self.assertFalse(result)
        
        # Statistics should return error information
        stats = bad_analytics.get_usage_statistics()
        self.assertIn("error", stats)
    
    def test_performance_benchmarks(self):
        """Test performance benchmarks for critical operations"""
        # Benchmark event logging
        num_events = 1000
        start_time = time.time()
        
        for i in range(num_events):
            self.analytics.log_event(
                event_type="benchmark",
                tool_name="test_tool",
                metadata={"index": i},
                duration_ms=i,
                success=True
            )
        
        elapsed_time = time.time() - start_time
        events_per_second = num_events / elapsed_time
        
        # Should be able to log at least 100 events per second
        self.assertGreater(events_per_second, 100, 
                          f"Event logging too slow: {events_per_second:.1f} events/sec")
        
        # Benchmark statistics generation
        start_time = time.time()
        stats = self.analytics.get_usage_statistics(days=7)
        stats_time = time.time() - start_time
        
        # Statistics generation should complete within 1 second
        self.assertLess(stats_time, 1.0,
                       f"Statistics generation too slow: {stats_time:.2f}s")
        
        # Verify statistics are correct
        self.assertEqual(stats["basic_stats"]["total_events"], num_events)
    
    def test_memory_usage_limits(self):
        """Test memory usage with large datasets"""
        # Test with large metadata
        large_metadata = {"data": "x" * 50000}  # 50KB metadata
        
        result = self.analytics.log_event(
            event_type="large_test",
            metadata=large_metadata
        )
        self.assertTrue(result)
        
        # Verify metadata was truncated appropriately
        with sqlite3.connect(self.analytics_db_path) as conn:
            cursor = conn.execute("""
                SELECT LENGTH(metadata) FROM usage_events 
                WHERE event_type = 'large_test'
            """)
            metadata_length = cursor.fetchone()[0]
            
        # Should be much smaller than original due to sanitization
        self.assertLess(metadata_length, 2000)


class TestUsageAnalyticsIntegration(BaseGreeumTestCase):
    """Integration tests for UsageAnalytics with other components"""
    
    def setUp(self):
        """Set up integration test fixtures"""
        super().setUp()
        
        # Analytics 전용 데이터베이스 경로
        self.integration_db_path = os.path.join(self.temp_dir, "test_integration.db")
        
        self.analytics = UsageAnalytics(
            db_manager=self.mock_db_manager,
            analytics_db_path=self.integration_db_path
        )
    
    def test_real_world_usage_simulation(self):
        """Simulate real-world usage patterns"""
        # Simulate a typical user session
        session_id = "real_session_001"
        
        # Session start
        self.analytics.start_session(session_id, "Claude/1.0", "mcp_client")
        
        # User searches for existing memories
        self.analytics.log_event("tool_usage", "search_memory", 
                                metadata={"query": "project status"}, 
                                duration_ms=150, success=True, session_id=session_id)
        
        # User adds new memory
        self.analytics.log_event("tool_usage", "add_memory",
                                metadata={"content_length": 245},
                                duration_ms=89, success=True, session_id=session_id)
        
        # Log quality metrics for the added memory
        self.analytics.log_quality_metrics(245, 0.82, "good", 0.6, 0.65, False, 0.1, 2)
        
        # User checks memory stats
        self.analytics.log_event("tool_usage", "get_memory_stats",
                                duration_ms=45, success=True, session_id=session_id)
        
        # Session end
        self.analytics.end_session(session_id)
        
        # Verify realistic statistics
        stats = self.analytics.get_usage_statistics(days=1)
        
        self.assertEqual(stats["basic_stats"]["total_events"], 4)  # Including start/end events
        self.assertEqual(stats["basic_stats"]["unique_sessions"], 1)
        self.assertAlmostEqual(stats["basic_stats"]["success_rate"], 1.0)
        
        # Check tool usage distribution
        tool_usage = stats["tool_usage"]
        self.assertEqual(tool_usage.get("search_memory", 0), 1)
        self.assertEqual(tool_usage.get("add_memory", 0), 1)
        self.assertEqual(tool_usage.get("get_memory_stats", 0), 1)


if __name__ == '__main__':
    # Create test suite
    suite = unittest.TestSuite()
    
    # Add all test cases
    suite.addTest(unittest.makeSuite(TestUsageAnalytics))
    suite.addTest(unittest.makeSuite(TestUsageAnalyticsIntegration))
    
    # Run tests with verbose output
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print(f"\n{'='*50}")
    print(f"UsageAnalytics Test Summary:")
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Success rate: {((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100):.1f}%")
    print(f"{'='*50}")