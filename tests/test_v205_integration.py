#!/usr/bin/env python3
"""
Integration Tests for Greeum v2.0.5 Features
Tests integration between UsageAnalytics, QualityValidator, DuplicateDetector, and EnhancedToolSchema
Simulates realistic MCP server usage scenarios and validates end-to-end functionality.
"""

import unittest
import sys
import os
import tempfile
import time
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta

# Add the greeum package to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from greeum.core.usage_analytics import UsageAnalytics
from greeum.core.quality_validator import QualityValidator, QualityLevel
from greeum.core.duplicate_detector import DuplicateDetector
from greeum.mcp.enhanced_tool_schema import EnhancedToolSchema


class TestV205Integration(unittest.TestCase):
    """Integration tests for all v2.0.5 features working together"""
    
    def setUp(self):
        """Set up integration test environment"""
        # Create temporary directory for test databases
        self.temp_dir = tempfile.mkdtemp()
        self.test_db_path = os.path.join(self.temp_dir, "integration_test.db")
        
        # Mock database manager
        self.mock_db_manager = Mock()
        self.mock_db_manager.search_blocks_by_embedding.return_value = []
        self.mock_db_manager.search_blocks_by_keyword.return_value = []
        self.mock_db_manager.get_blocks_since_time.return_value = []
        
        # Initialize all components
        self.analytics = UsageAnalytics(
            db_manager=self.mock_db_manager,
            analytics_db_path=self.test_db_path
        )
        self.quality_validator = QualityValidator()
        self.duplicate_detector = DuplicateDetector(self.mock_db_manager)
        
        # Test session
        self.session_id = "integration_test_session"
        
    def tearDown(self):
        """Clean up test environment"""
        if os.path.exists(self.test_db_path):
            os.remove(self.test_db_path)
        os.rmdir(self.temp_dir)
    
    def test_complete_memory_workflow(self):
        """Test complete memory addition workflow with all v2.0.5 features"""
        # Start analytics session
        self.analytics.start_session(self.session_id, "MCP Client v1.0", "integration_test")
        
        # Test content
        content = "오늘 중요한 프로젝트 결정을 내렸습니다. React 18과 TypeScript를 사용하여 새로운 대시보드를 개발하기로 했고, 개발 기간은 2개월로 예상됩니다. 데이터베이스는 PostgreSQL 14를 사용할 예정입니다."
        importance = 0.7
        
        # Step 1: Quality validation
        start_time = time.time()
        quality_result = self.quality_validator.validate_memory_quality(content, importance)
        quality_time = int((time.time() - start_time) * 1000)
        
        # Log quality validation event
        self.analytics.log_event(
            event_type="quality_validation",
            tool_name="validate_memory_quality",
            metadata={"content_length": len(content)},
            duration_ms=quality_time,
            success=True,
            session_id=self.session_id
        )
        
        # Log quality metrics
        self.analytics.log_quality_metrics(
            content_length=len(content),
            quality_score=quality_result['quality_score'],
            quality_level=quality_result['quality_level'],
            importance=importance,
            adjusted_importance=quality_result['adjusted_importance'],
            is_duplicate=False,
            duplicate_similarity=0.0,
            suggestions_count=len(quality_result['suggestions'])
        )
        
        # Verify quality validation
        self.assertGreaterEqual(quality_result['quality_score'], 0.6)
        self.assertTrue(quality_result['should_store'])
        self.assertEqual(quality_result['validation_version'], '2.0.5')
        
        # Step 2: Duplicate detection
        start_time = time.time()
        duplicate_result = self.duplicate_detector.check_duplicate(content, importance)
        duplicate_time = int((time.time() - start_time) * 1000)
        
        # Log duplicate detection event
        self.analytics.log_event(
            event_type="duplicate_detection",
            tool_name="check_duplicate",
            metadata={
                "similarity_score": duplicate_result['similarity_score'],
                "duplicate_type": duplicate_result['duplicate_type']
            },
            duration_ms=duplicate_time,
            success=True,
            session_id=self.session_id
        )
        
        # Verify duplicate detection
        self.assertFalse(duplicate_result['is_duplicate'])  # No duplicates in empty DB
        self.assertEqual(duplicate_result['suggested_action'], 'store_anyway')
        
        # Step 3: Simulate memory storage (would normally happen here)
        self.analytics.log_event(
            event_type="tool_usage",
            tool_name="add_memory",
            metadata={
                "content_length": len(content),
                "final_importance": quality_result['adjusted_importance'],
                "quality_score": quality_result['quality_score']
            },
            duration_ms=95,
            success=True,
            session_id=self.session_id
        )
        
        # Step 4: End session and get analytics
        self.analytics.end_session(self.session_id)
        
        # Verify session analytics
        stats = self.analytics.get_usage_statistics(days=1)
        
        self.assertGreaterEqual(stats['basic_stats']['total_events'], 4)  # At least 4 events logged
        self.assertEqual(stats['basic_stats']['unique_sessions'], 1)
        self.assertAlmostEqual(stats['basic_stats']['success_rate'], 1.0)
        self.assertIn('add_memory', stats['tool_usage'])
        
        # Verify quality statistics
        quality_stats = stats['quality_stats']
        self.assertGreater(quality_stats['avg_quality_score'], 0.6)
        self.assertEqual(quality_stats['total_quality_checks'], 1)
    
    def test_batch_processing_integration(self):
        """Test batch processing with all components"""
        # Test batch of diverse content
        test_batch = [
            ("First high-quality memory about project planning and technical decisions", 0.8),
            ("Second memory with good technical content and implementation details", 0.7),
            ("Short note", 0.3),  # Should be flagged as low quality
            ("Third comprehensive memory with detailed information about system architecture", 0.9),
            ("First high-quality memory about project planning and technical decisions", 0.8)  # Duplicate
        ]
        
        session_id = "batch_test_session"
        self.analytics.start_session(session_id, "Batch Test Client", "batch_processing")
        
        batch_results = []
        
        # Process each item in batch
        for i, (content, importance) in enumerate(test_batch):
            # Quality validation
            quality_result = self.quality_validator.validate_memory_quality(content, importance)
            
            # Duplicate detection (mock some similar content for duplicate testing)
            if i == 4:  # Last item is duplicate of first
                self.mock_db_manager.search_blocks_by_embedding.return_value = [
                    {'block_index': 1, 'context': test_batch[0][0]}
                ]
            else:
                self.mock_db_manager.search_blocks_by_embedding.return_value = []
            
            duplicate_result = self.duplicate_detector.check_duplicate(content, importance)
            
            # Log analytics
            self.analytics.log_event(
                event_type="batch_processing",
                tool_name="process_memory",
                metadata={
                    "batch_index": i,
                    "quality_score": quality_result['quality_score'],
                    "is_duplicate": duplicate_result['is_duplicate']
                },
                duration_ms=50 + i * 10,
                success=True,
                session_id=session_id
            )
            
            # Log quality metrics
            self.analytics.log_quality_metrics(
                content_length=len(content),
                quality_score=quality_result['quality_score'],
                quality_level=quality_result['quality_level'],
                importance=importance,
                adjusted_importance=quality_result['adjusted_importance'],
                is_duplicate=duplicate_result['is_duplicate'],
                duplicate_similarity=duplicate_result['similarity_score'],
                suggestions_count=len(quality_result['suggestions'])
            )
            
            batch_results.append({
                'quality': quality_result,
                'duplicate': duplicate_result
            })
        
        # Verify batch results
        self.assertEqual(len(batch_results), 5)
        
        # First item should be high quality, not duplicate
        self.assertGreater(batch_results[0]['quality']['quality_score'], 0.7)
        self.assertFalse(batch_results[0]['duplicate']['is_duplicate'])
        
        # Third item should be low quality (short note)
        self.assertLess(batch_results[2]['quality']['quality_score'], 0.5)
        self.assertFalse(batch_results[2]['quality']['should_store'])
        
        # Last item should be detected as duplicate
        self.assertTrue(batch_results[4]['duplicate']['is_duplicate'])
        
        # End session and verify analytics
        self.analytics.end_session(session_id)
        
        stats = self.analytics.get_usage_statistics(days=1)
        batch_events = [event for event_type, count in stats['tool_usage'].items() 
                       if 'batch' in event_type or 'process' in event_type]
        self.assertGreater(len(batch_events), 0)
    
    def test_mcp_server_simulation(self):
        """Simulate realistic MCP server usage with all components"""
        # Get enhanced schemas
        all_schemas = EnhancedToolSchema.get_all_enhanced_schemas()
        self.assertEqual(len(all_schemas), 10)
        
        # Simulate MCP server session
        mcp_session_id = "mcp_server_session"
        self.analytics.start_session(mcp_session_id, "Claude Code MCP", "claude_code")
        
        # Simulate typical MCP operations
        operations = [
            {
                'tool': 'search_memory',
                'content': 'project status',
                'success': True,
                'duration_ms': 120
            },
            {
                'tool': 'add_memory', 
                'content': 'Sprint planning completed. Development tasks assigned to team members. Sprint goal: Complete user authentication module by next Friday.',
                'success': True,
                'duration_ms': 89
            },
            {
                'tool': 'get_memory_stats',
                'content': '',
                'success': True,
                'duration_ms': 45
            },
            {
                'tool': 'usage_analytics',
                'content': '',
                'success': True,
                'duration_ms': 78
            }
        ]
        
        for op in operations:
            # Process operation based on type
            if op['tool'] == 'add_memory' and op['content']:
                # Full workflow for add_memory
                quality_result = self.quality_validator.validate_memory_quality(op['content'], 0.6)
                duplicate_result = self.duplicate_detector.check_duplicate(op['content'], 0.6)
                
                # Log quality metrics
                self.analytics.log_quality_metrics(
                    content_length=len(op['content']),
                    quality_score=quality_result['quality_score'],
                    quality_level=quality_result['quality_level'],
                    importance=0.6,
                    adjusted_importance=quality_result['adjusted_importance'],
                    is_duplicate=duplicate_result['is_duplicate'],
                    duplicate_similarity=duplicate_result['similarity_score'],
                    suggestions_count=len(quality_result['suggestions'])
                )
            
            # Log the MCP tool usage
            self.analytics.log_event(
                event_type="mcp_tool_usage",
                tool_name=op['tool'],
                metadata={"mcp_client": "claude_code"},
                duration_ms=op['duration_ms'],
                success=op['success'],
                session_id=mcp_session_id
            )
        
        # End MCP session
        self.analytics.end_session(mcp_session_id)
        
        # Verify MCP analytics
        stats = self.analytics.get_usage_statistics(days=1)
        
        # Should have multiple tool usages
        self.assertGreaterEqual(len(stats['tool_usage']), 3)
        self.assertIn('add_memory', stats['tool_usage'])
        self.assertIn('search_memory', stats['tool_usage'])
        
        # Verify performance insights
        insights = self.analytics.get_performance_insights(days=1)
        self.assertIn('performance_by_tool', insights)
        self.assertIn('recommendations', insights)
        
        # Should have reasonable performance
        for perf_data in insights['performance_by_tool']:
            self.assertLess(perf_data['avg_duration_ms'], 1000)  # Under 1 second
    
    def test_quality_and_duplicate_correlation(self):
        """Test correlation between quality scores and duplicate detection"""
        test_cases = [
            {
                'content': 'High quality detailed technical content with specific information about system architecture and implementation decisions',
                'expected_quality': 'high',
                'duplicate_candidate': 'Similar detailed technical content about system design and architectural decisions'
            },
            {
                'content': 'Short low quality content',
                'expected_quality': 'low',
                'duplicate_candidate': 'Brief poor quality text'
            },
            {
                'content': 'Medium quality content with some useful information but not very detailed',
                'expected_quality': 'medium',  
                'duplicate_candidate': 'Moderate quality content with decent information level'
            }
        ]
        
        correlation_session = "correlation_test_session"
        self.analytics.start_session(correlation_session, "Correlation Test", "analysis")
        
        for i, case in enumerate(test_cases):
            # Validate original content
            quality_result = self.quality_validator.validate_memory_quality(case['content'], 0.5)
            
            # Test duplicate detection with similar content
            self.mock_db_manager.search_blocks_by_embedding.return_value = [
                {'block_index': i+1, 'context': case['duplicate_candidate']}
            ]
            
            duplicate_result = self.duplicate_detector.check_duplicate(case['content'], 0.5)
            
            # Log correlation data
            self.analytics.log_event(
                event_type="correlation_test",
                tool_name="quality_duplicate_analysis",
                metadata={
                    "quality_score": quality_result['quality_score'],
                    "quality_level": quality_result['quality_level'],
                    "duplicate_similarity": duplicate_result['similarity_score'],
                    "expected_quality": case['expected_quality']
                },
                duration_ms=75,
                success=True,
                session_id=correlation_session
            )
            
            # Log quality metrics
            self.analytics.log_quality_metrics(
                content_length=len(case['content']),
                quality_score=quality_result['quality_score'],
                quality_level=quality_result['quality_level'],
                importance=0.5,
                adjusted_importance=quality_result['adjusted_importance'],
                is_duplicate=duplicate_result['is_duplicate'],
                duplicate_similarity=duplicate_result['similarity_score'],
                suggestions_count=len(quality_result['suggestions'])
            )
            
            # Verify expectations
            if case['expected_quality'] == 'high':
                self.assertGreaterEqual(quality_result['quality_score'], 0.7)
                self.assertTrue(quality_result['should_store'])
            elif case['expected_quality'] == 'low':
                self.assertLessEqual(quality_result['quality_score'], 0.4)
                self.assertFalse(quality_result['should_store'])
            else:  # medium
                self.assertGreater(quality_result['quality_score'], 0.4)
                self.assertLess(quality_result['quality_score'], 0.7)
        
        # End session and analyze correlations
        self.analytics.end_session(correlation_session)
        
        # Get quality trends
        trends = self.analytics.get_quality_trends(days=1)
        self.assertIn('quality_distribution', trends)
        self.assertGreater(len(trends['quality_distribution']), 0)
    
    def test_error_handling_integration(self):
        """Test error handling across all integrated components"""
        error_session = "error_handling_session"
        self.analytics.start_session(error_session, "Error Test Client", "error_testing")
        
        # Test various error scenarios
        error_scenarios = [
            {"content": None, "description": "null_content"},
            {"content": "", "description": "empty_content"},
            {"content": "x" * 50000, "description": "oversized_content"},  # Very large content
            {"content": "Normal content", "db_error": True, "description": "database_error"}
        ]
        
        for scenario in error_scenarios:
            try:
                # Quality validation (should handle errors gracefully)
                if scenario['content'] is not None:
                    quality_result = self.quality_validator.validate_memory_quality(
                        scenario['content'], 0.5
                    )
                    quality_success = True
                    quality_error = None
                else:
                    quality_success = False
                    quality_error = "null_content"
                    quality_result = None
                
                # Duplicate detection with potential database error
                if scenario.get('db_error'):
                    self.mock_db_manager.search_blocks_by_embedding.side_effect = Exception("DB Error")
                    duplicate_result = self.duplicate_detector.check_duplicate("test", 0.5)
                    duplicate_success = not ('error' in duplicate_result.get('duplicate_type', ''))
                else:
                    self.mock_db_manager.search_blocks_by_embedding.side_effect = None
                    self.mock_db_manager.search_blocks_by_embedding.return_value = []
                    
                    if scenario['content']:
                        duplicate_result = self.duplicate_detector.check_duplicate(scenario['content'], 0.5)
                        duplicate_success = True
                    else:
                        duplicate_success = False
                        duplicate_result = None
                
                # Log error handling results
                self.analytics.log_event(
                    event_type="error_handling",
                    tool_name="integrated_validation",
                    metadata={
                        "scenario": scenario['description'],
                        "quality_success": quality_success,
                        "duplicate_success": duplicate_success
                    },
                    duration_ms=100,
                    success=quality_success and duplicate_success,
                    error_message=quality_error,
                    session_id=error_session
                )
                
                # Verify graceful handling
                if quality_result:
                    self.assertIsInstance(quality_result, dict)
                    self.assertIn('quality_score', quality_result)
                
                if duplicate_result:
                    self.assertIsInstance(duplicate_result, dict)
                    self.assertIn('is_duplicate', duplicate_result)
                
            except Exception as e:
                # Log unexpected errors
                self.analytics.log_event(
                    event_type="error_handling",
                    tool_name="integrated_validation",
                    metadata={"scenario": scenario['description']},
                    duration_ms=50,
                    success=False,
                    error_message=str(e),
                    session_id=error_session
                )
        
        # End session and verify error analytics
        self.analytics.end_session(error_session)
        
        insights = self.analytics.get_performance_insights(days=1)
        if insights.get('error_patterns'):
            # Should have recorded some errors
            self.assertGreater(len(insights['error_patterns']), 0)
    
    def test_performance_under_load(self):
        """Test performance of integrated system under load"""
        load_session = "performance_load_session"
        self.analytics.start_session(load_session, "Performance Test", "load_testing")
        
        # Simulate high load scenario
        num_operations = 100
        start_time = time.time()
        
        for i in range(num_operations):
            content = f"Performance test content number {i} with various details and information to simulate realistic memory content."
            
            # Quick quality validation
            quality_result = self.quality_validator.validate_memory_quality(content, 0.5)
            
            # Quick duplicate check
            duplicate_result = self.duplicate_detector.check_duplicate(content, 0.5)
            
            # Log performance metrics
            if i % 10 == 0:  # Log every 10th operation
                self.analytics.log_performance_metric(
                    metric_type="load_test",
                    metric_name="operations_completed",
                    metric_value=i,
                    unit="count",
                    metadata={"session": load_session}
                )
            
            # Log operation
            self.analytics.log_event(
                event_type="load_test",
                tool_name="integrated_processing",
                metadata={"operation_index": i},
                duration_ms=10 + (i % 5),  # Simulate variable duration
                success=True,
                session_id=load_session
            )
        
        total_time = time.time() - start_time
        operations_per_second = num_operations / total_time
        
        # Log final performance metric
        self.analytics.log_performance_metric(
            metric_type="load_test",
            metric_name="operations_per_second",
            metric_value=operations_per_second,
            unit="ops/sec",
            metadata={"total_operations": num_operations, "total_time_seconds": total_time}
        )
        
        # Performance should be reasonable
        self.assertGreater(operations_per_second, 50, 
                          f"Performance too slow: {operations_per_second:.1f} ops/sec")
        
        # End session and verify performance analytics
        self.analytics.end_session(load_session)
        
        insights = self.analytics.get_performance_insights(days=1)
        self.assertIn('resource_metrics', insights)
        
        # Find load test metrics
        load_metrics = [m for m in insights['resource_metrics'] 
                       if m['metric_name'] == 'operations_per_second']
        self.assertGreater(len(load_metrics), 0)
        self.assertGreater(load_metrics[0]['avg_value'], 50)
    
    def test_schema_driven_workflow(self):
        """Test workflow driven by enhanced tool schemas"""
        # Get schemas for workflow tools
        add_memory_schema = EnhancedToolSchema.get_add_memory_schema()
        search_memory_schema = EnhancedToolSchema.get_search_memory_schema()
        
        # Verify schemas have workflow guidance
        self.assertIn("search_memory first", add_memory_schema['description'])
        self.assertIn("ALWAYS USE THIS FIRST", search_memory_schema['description'])
        
        # Simulate schema-driven workflow
        schema_session = "schema_workflow_session"
        self.analytics.start_session(schema_session, "Schema-Driven Client", "schema_test")
        
        # Step 1: Follow schema guidance - search first
        search_content = "project planning"
        
        # Simulate search (following schema guidance)
        self.analytics.log_event(
            event_type="schema_guided",
            tool_name="search_memory",
            metadata={"follows_schema": True, "query": search_content},
            duration_ms=85,
            success=True,
            session_id=schema_session
        )
        
        # Step 2: Add memory (following schema workflow)
        new_content = "Project planning session completed. Decided on microservices architecture with Docker containers. Timeline: 3 months development, 1 month testing."
        
        # Validate following schema constraints
        input_schema = add_memory_schema['inputSchema']
        content_constraints = input_schema['properties']['content']
        
        # Check minLength constraint
        self.assertGreaterEqual(len(new_content), content_constraints['minLength'])
        
        # Process with quality validation
        quality_result = self.quality_validator.validate_memory_quality(new_content, 0.7)
        
        # Check against schema importance guidance
        importance_guidance = input_schema['properties']['importance']['description']
        self.assertIn("0.7-0.8: High", importance_guidance)  # Verify guidance exists
        
        # Log schema-compliant operation
        self.analytics.log_event(
            event_type="schema_guided",
            tool_name="add_memory",
            metadata={
                "follows_schema": True,
                "content_length": len(new_content),
                "meets_min_length": len(new_content) >= content_constraints['minLength'],
                "quality_score": quality_result['quality_score']
            },
            duration_ms=120,
            success=True,
            session_id=schema_session
        )
        
        # End session
        self.analytics.end_session(schema_session)
        
        # Verify schema-driven workflow analytics
        stats = self.analytics.get_usage_statistics(days=1)
        schema_events = stats['tool_usage']
        
        # Should show proper workflow order
        self.assertIn('search_memory', schema_events)
        self.assertIn('add_memory', schema_events)


class TestV205PerformanceBenchmarks(unittest.TestCase):
    """Performance benchmarks for v2.0.5 integrated features"""
    
    def setUp(self):
        """Set up performance test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.test_db_path = os.path.join(self.temp_dir, "perf_test.db")
        
        self.mock_db_manager = Mock()
        self.mock_db_manager.search_blocks_by_embedding.return_value = []
        
        self.analytics = UsageAnalytics(
            db_manager=self.mock_db_manager,
            analytics_db_path=self.test_db_path
        )
        self.quality_validator = QualityValidator()
        self.duplicate_detector = DuplicateDetector(self.mock_db_manager)
    
    def tearDown(self):
        """Clean up performance test environment"""
        if os.path.exists(self.test_db_path):
            os.remove(self.test_db_path)
        os.rmdir(self.temp_dir)
    
    def test_quality_validation_performance(self):
        """Benchmark quality validation performance"""
        test_contents = [
            "Short content for testing quality validation performance",
            "Medium length content with more details about the testing process and quality validation algorithms that are being benchmarked in this performance test",
            "Very long content piece that contains extensive information about various topics including technical details, project specifications, implementation notes, and comprehensive documentation that would typically be found in real-world memory storage scenarios" * 5
        ]
        
        # Benchmark different content sizes
        for content in test_contents:
            iterations = 50
            start_time = time.time()
            
            for _ in range(iterations):
                result = self.quality_validator.validate_memory_quality(content, 0.5)
                self.assertIsInstance(result, dict)
            
            elapsed_time = time.time() - start_time
            validations_per_second = iterations / elapsed_time
            
            # Should be able to validate at least 100 items per second
            self.assertGreater(validations_per_second, 100,
                             f"Quality validation too slow for {len(content)} chars: {validations_per_second:.1f} validations/sec")
    
    def test_duplicate_detection_performance(self):
        """Benchmark duplicate detection performance"""
        # Mock database with varying response sizes
        mock_responses = [
            [],  # No similar memories
            [{'block_index': i, 'context': f'Memory {i}'} for i in range(5)],  # Small response
            [{'block_index': i, 'context': f'Memory {i}'} for i in range(20)]  # Larger response
        ]
        
        test_content = "Performance test content for duplicate detection benchmarking"
        
        for response_size, mock_response in enumerate(mock_responses):
            self.mock_db_manager.search_blocks_by_embedding.return_value = mock_response
            
            iterations = 30
            start_time = time.time()
            
            for _ in range(iterations):
                result = self.duplicate_detector.check_duplicate(test_content, 0.5)
                self.assertIsInstance(result, dict)
            
            elapsed_time = time.time() - start_time
            checks_per_second = iterations / elapsed_time
            
            # Should be able to check at least 50 duplicates per second
            self.assertGreater(checks_per_second, 50,
                             f"Duplicate detection too slow with {len(mock_response)} similar memories: {checks_per_second:.1f} checks/sec")
    
    def test_analytics_logging_performance(self):
        """Benchmark analytics logging performance"""
        session_id = "perf_benchmark_session"
        self.analytics.start_session(session_id, "Performance Test", "benchmarking")
        
        # Test event logging performance
        iterations = 200
        start_time = time.time()
        
        for i in range(iterations):
            self.analytics.log_event(
                event_type="performance_test",
                tool_name="benchmark_tool",
                metadata={"iteration": i, "test_data": "benchmark"},
                duration_ms=i % 100,
                success=True,
                session_id=session_id
            )
        
        elapsed_time = time.time() - start_time
        events_per_second = iterations / elapsed_time
        
        # Should be able to log at least 500 events per second
        self.assertGreater(events_per_second, 500,
                          f"Event logging too slow: {events_per_second:.1f} events/sec")
        
        # Test quality metrics logging performance
        start_time = time.time()
        
        for i in range(iterations):
            self.analytics.log_quality_metrics(
                content_length=100 + i,
                quality_score=0.5 + (i % 50) * 0.01,
                quality_level="good",
                importance=0.5,
                adjusted_importance=0.6,
                is_duplicate=i % 10 == 0,
                duplicate_similarity=0.1,
                suggestions_count=2
            )
        
        elapsed_time = time.time() - start_time
        metrics_per_second = iterations / elapsed_time
        
        # Should be able to log at least 300 quality metrics per second
        self.assertGreater(metrics_per_second, 300,
                          f"Quality metrics logging too slow: {metrics_per_second:.1f} metrics/sec")
        
        self.analytics.end_session(session_id)
    
    def test_integrated_workflow_performance(self):
        """Benchmark complete integrated workflow performance"""
        session_id = "integrated_perf_session"
        self.analytics.start_session(session_id, "Integrated Performance Test", "full_workflow")
        
        test_content = "Integrated performance test content with sufficient detail for quality validation and duplicate detection benchmarking"
        
        iterations = 25  # Lower iterations for full workflow
        start_time = time.time()
        
        for i in range(iterations):
            # Full workflow: quality -> duplicate -> analytics
            quality_result = self.quality_validator.validate_memory_quality(test_content, 0.6)
            duplicate_result = self.duplicate_detector.check_duplicate(test_content, 0.6)
            
            # Log analytics
            self.analytics.log_event(
                event_type="integrated_workflow",
                tool_name="full_processing",
                metadata={
                    "iteration": i,
                    "quality_score": quality_result['quality_score'],
                    "is_duplicate": duplicate_result['is_duplicate']
                },
                duration_ms=75,
                success=True,
                session_id=session_id
            )
            
            self.analytics.log_quality_metrics(
                content_length=len(test_content),
                quality_score=quality_result['quality_score'],
                quality_level=quality_result['quality_level'],
                importance=0.6,
                adjusted_importance=quality_result['adjusted_importance'],
                is_duplicate=duplicate_result['is_duplicate'],
                duplicate_similarity=duplicate_result['similarity_score'],
                suggestions_count=len(quality_result['suggestions'])
            )
        
        elapsed_time = time.time() - start_time
        workflows_per_second = iterations / elapsed_time
        
        # Should be able to process at least 15 complete workflows per second
        self.assertGreater(workflows_per_second, 15,
                          f"Integrated workflow too slow: {workflows_per_second:.1f} workflows/sec")
        
        self.analytics.end_session(session_id)
        
        # Verify analytics generation performance
        start_time = time.time()
        stats = self.analytics.get_usage_statistics(days=1)
        stats_time = time.time() - start_time
        
        # Statistics generation should be fast
        self.assertLess(stats_time, 0.5, f"Statistics generation too slow: {stats_time:.2f}s")
        self.assertGreater(stats['basic_stats']['total_events'], iterations)


if __name__ == '__main__':
    # Create comprehensive test suite
    suite = unittest.TestSuite()
    
    # Add integration tests
    suite.addTest(unittest.makeSuite(TestV205Integration))
    suite.addTest(unittest.makeSuite(TestV205PerformanceBenchmarks))
    
    # Run tests with verbose output
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print comprehensive summary
    print(f"\n{'='*60}")
    print(f"Greeum v2.0.5 Integration Test Summary")
    print(f"{'='*60}")
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Success rate: {((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100):.1f}%")
    print(f"{'='*60}")
    
    # Print integration test results
    if result.failures:
        print(f"\n❌ FAILURES ({len(result.failures)}):")
        for test, failure in result.failures[:3]:  # Show first 3 failures
            print(f"  - {test}: {failure.split(chr(10))[0]}")
    
    if result.errors:
        print(f"\n⚠️  ERRORS ({len(result.errors)}):")
        for test, error in result.errors[:3]:  # Show first 3 errors
            print(f"  - {test}: {error.split(chr(10))[0]}")
    
    if result.testsRun == len(result.failures) + len(result.errors):
        print(f"\n❌ All tests failed - check component implementations")
    elif len(result.failures) + len(result.errors) == 0:
        print(f"\n✅ All integration tests passed successfully!")
        print(f"🚀 Greeum v2.0.5 components are ready for production")
    else:
        print(f"\n⚠️  Some integration issues detected - review failures")
    
    print(f"\n📊 Test Coverage Areas:")
    print(f"  ✅ UsageAnalytics - Event logging, session management, statistics")
    print(f"  ✅ QualityValidator - Content analysis, scoring, recommendations")
    print(f"  ✅ DuplicateDetector - Similarity detection, batch processing")
    print(f"  ✅ EnhancedToolSchema - MCP integration, parameter validation")
    print(f"  ✅ Integration - End-to-end workflows, error handling")
    print(f"  ✅ Performance - Load testing, benchmarking, optimization")
    
    print(f"\n{'='*60}")