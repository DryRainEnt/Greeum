#!/usr/bin/env python3
"""
Comprehensive Unit Tests for DuplicateDetector (Greeum v2.0.5)
Tests similarity detection algorithms, hash-based exact matching,
batch duplicate checking, performance optimization, and edge cases.
"""

import hashlib
import time
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta

from tests.base_test_case import BaseGreeumTestCase
from greeum.core.duplicate_detector import DuplicateDetector


class TestDuplicateDetector(BaseGreeumTestCase):
    """Comprehensive test suite for DuplicateDetector class"""
    
    def setUp(self):
        """Set up test fixtures before each test method"""
        super().setUp()
        
        # Initialize detector with test database
        self.detector = DuplicateDetector(
            db_manager=self.mock_db_manager,
            similarity_threshold=0.85
        )
    
    def test_detector_initialization(self):
        """Test DuplicateDetector initialization"""
        self.assertEqual(self.detector.similarity_threshold, 0.85)
        self.assertEqual(self.detector.exact_match_threshold, 0.95)
        self.assertEqual(self.detector.partial_match_threshold, 0.7)
        self.assertIsNotNone(self.detector.db_manager)
    
    def test_exact_duplicate_detection(self):
        """Test exact duplicate detection using hash matching"""
        # Mock return exact duplicate
        self.mock_db_manager.search_blocks_by_embedding.return_value = [
            {'block_index': 1, 'context': self.duplicate_test_contents['exact_duplicate']}
        ]
        
        result = self.detector.check_duplicate(self.duplicate_test_contents['original'])
        
        self.assertTrue(result['is_duplicate'])
        self.assertEqual(result['duplicate_type'], 'exact')
        self.assertEqual(result['similarity_score'], 1.0)
        self.assertEqual(result['suggested_action'], 'skip')
        self.assertIn('Exact duplicate detected', result['recommendation'])
    
    def test_similar_content_detection(self):
        """Test similar content detection"""
        # Mock return similar content
        self.mock_db_manager.search_blocks_by_embedding.return_value = [
            {'block_index': 1, 'context': self.duplicate_test_contents['similar']}
        ]
        
        result = self.detector.check_duplicate(self.duplicate_test_contents['original'])
        
        self.assertTrue(result['is_duplicate'])
        self.assertEqual(result['duplicate_type'], 'similar')
        self.assertGreaterEqual(result['similarity_score'], 0.85)
        self.assertIn(result['suggested_action'], ['skip', 'merge'])
        self.assertIn('Similar content found', result['recommendation'])
    
    def test_partial_similarity_detection(self):
        """Test partial similarity detection (not considered duplicate)"""
        # Mock return partially similar content
        self.mock_db_manager.search_blocks_by_embedding.return_value = [
            {'block_index': 1, 'context': self.duplicate_test_contents['partial_similar']}
        ]
        
        result = self.detector.check_duplicate(self.duplicate_test_contents['original'])
        
        self.assertFalse(result['is_duplicate'])
        self.assertEqual(result['duplicate_type'], 'partial')
        self.assertGreaterEqual(result['similarity_score'], 0.7)
        self.assertLess(result['similarity_score'], 0.85)
        self.assertEqual(result['suggested_action'], 'store_anyway')
        self.assertIn('Partially similar', result['recommendation'])
    
    def test_no_duplicate_detection(self):
        """Test when no duplicates are found"""
        # Mock return different content
        self.mock_db_manager.search_blocks_by_embedding.return_value = [
            {'block_index': 1, 'context': self.duplicate_test_contents['different']}
        ]
        
        result = self.detector.check_duplicate(self.duplicate_test_contents['original'])
        
        self.assertFalse(result['is_duplicate'])
        self.assertEqual(result['duplicate_type'], 'none')
        self.assertLess(result['similarity_score'], 0.7)
        self.assertEqual(result['suggested_action'], 'store_anyway')
        self.assertIn('Unique content', result['recommendation'])
    
    def test_empty_and_short_content(self):
        """Test handling of empty and very short content"""
        # Test empty content
        result = self.detector.check_duplicate(self.test_contents['empty'])
        
        self.assertFalse(result['is_duplicate'])
        self.assertEqual(result['duplicate_type'], 'none')
        self.assertEqual(result['similarity_score'], 0.0)
        self.assertEqual(result['suggested_action'], 'skip')
        self.assertIn('too short', result['recommendation'])
        
        # Test very short content
        result = self.detector.check_duplicate(self.test_contents['short'])
        
        self.assertFalse(result['is_duplicate'])
        self.assertEqual(result['duplicate_type'], 'none')
        self.assertEqual(result['suggested_action'], 'skip')
    
    def test_no_similar_memories_found(self):
        """Test when no similar memories are found in database"""
        # Mock empty search results
        self.mock_db_manager.search_blocks_by_embedding.return_value = []
        self.mock_db_manager.search_blocks_by_keyword.return_value = []
        self.mock_db_manager.get_blocks_since_time.return_value = []
        
        result = self.detector.check_duplicate(self.duplicate_test_contents['original'])
        
        self.assertFalse(result['is_duplicate'])
        self.assertEqual(result['duplicate_type'], 'none')
        self.assertEqual(result['similarity_score'], 0.0)
        self.assertEqual(result['suggested_action'], 'store_anyway')
        self.assertIn('No similar memories found', result['recommendation'])
    
    def test_keyword_extraction(self):
        """Test keyword extraction functionality"""
        keywords = self.detector._extract_keywords(self.duplicate_test_contents['original'])
        
        self.assertIsInstance(keywords, list)
        self.assertLessEqual(len(keywords), 5)  # Should return max 5 keywords
        
        # Should filter out stop words and short words
        for keyword in keywords:
            self.assertGreater(len(keyword), 3)
            self.assertNotIn(keyword, {"the", "a", "an", "and", "or", "but", "in", "on", "at"})
        
        # Test with empty content
        empty_keywords = self.detector._extract_keywords("")
        self.assertEqual(empty_keywords, [])
        
        # Test with stop words only
        stop_word_keywords = self.detector._extract_keywords("the and or but")
        self.assertEqual(len(stop_word_keywords), 0)
    
    def test_similarity_analysis(self):
        """Test similarity analysis between content and memories"""
        # Test exact match
        memories = [{'context': self.duplicate_test_contents['exact_duplicate'], 'block_index': 1}]
        result = self.detector._analyze_similarity(self.duplicate_test_contents['original'], memories)
        
        self.assertEqual(result['similarity'], 1.0)
        self.assertEqual(result['match_type'], 'exact_hash')
        
        # Test text similarity
        memories = [{'context': self.duplicate_test_contents['similar'], 'block_index': 1}]
        result = self.detector._analyze_similarity(self.duplicate_test_contents['original'], memories)
        
        self.assertGreater(result['similarity'], 0.8)
        self.assertEqual(result['match_type'], 'text_similarity')
        
        # Test with multiple memories (should return best match)
        memories = [
            {'context': self.duplicate_test_contents['different'], 'block_index': 1},
            {'context': self.duplicate_test_contents['similar'], 'block_index': 2},
            {'context': self.duplicate_test_contents['partial_similar'], 'block_index': 3}
        ]
        result = self.detector._analyze_similarity(self.duplicate_test_contents['original'], memories)
        
        # Should match with the most similar one
        self.assertEqual(result['memory']['block_index'], 2)
        self.assertGreater(result['similarity'], 0.7)
    
    def test_duplicate_classification(self):
        """Test duplicate type classification based on similarity scores"""
        # Test exact classification
        duplicate_type, is_duplicate = self.detector._classify_duplicate(0.98)
        self.assertEqual(duplicate_type, 'exact')
        self.assertTrue(is_duplicate)
        
        # Test similar classification
        duplicate_type, is_duplicate = self.detector._classify_duplicate(0.87)
        self.assertEqual(duplicate_type, 'similar')
        self.assertTrue(is_duplicate)
        
        # Test partial classification
        duplicate_type, is_duplicate = self.detector._classify_duplicate(0.75)
        self.assertEqual(duplicate_type, 'partial')
        self.assertFalse(is_duplicate)
        
        # Test none classification
        duplicate_type, is_duplicate = self.detector._classify_duplicate(0.5)
        self.assertEqual(duplicate_type, 'none')
        self.assertFalse(is_duplicate)
    
    def test_recommendation_generation(self):
        """Test recommendation and suggested action generation"""
        # Test exact duplicate recommendation
        best_match = {
            'memory': {'block_index': 1},
            'similarity': 0.98,
            'match_type': 'exact_hash'
        }
        recommendation, action = self.detector._generate_recommendation('exact', best_match, 0.5)
        
        self.assertIn('Exact duplicate detected', recommendation)
        self.assertEqual(action, 'skip')
        
        # Test similar content recommendation
        best_match = {
            'memory': {'block_index': 2},
            'similarity': 0.87,
            'match_type': 'text_similarity'
        }
        recommendation, action = self.detector._generate_recommendation('similar', best_match, 0.7)
        
        self.assertIn('Similar content found', recommendation)
        self.assertEqual(action, 'merge')  # High importance should suggest merge
        
        # Test similar content with low importance
        recommendation, action = self.detector._generate_recommendation('similar', best_match, 0.5)
        self.assertEqual(action, 'skip')  # Low importance should suggest skip
        
        # Test partial similarity recommendation
        best_match = {'similarity': 0.75}
        recommendation, action = self.detector._generate_recommendation('partial', best_match, 0.5)
        
        self.assertIn('Partially similar', recommendation)
        self.assertEqual(action, 'store_anyway')
        
        # Test no duplicate recommendation
        recommendation, action = self.detector._generate_recommendation('none', {}, 0.5)
        
        self.assertIn('Unique content', recommendation)
        self.assertEqual(action, 'store_anyway')
    
    def test_batch_duplicate_checking(self):
        """Test batch duplicate checking for multiple contents"""
        # Test with batch containing duplicates
        contents = [
            "First unique content",
            "Second unique content", 
            "First unique content",  # Duplicate within batch
            "Third unique content"
        ]
        
        # Mock no external duplicates
        self.mock_db_manager.search_blocks_by_embedding.return_value = []
        
        results = self.detector.check_batch_duplicates(contents)
        
        self.assertEqual(len(results), 4)
        
        # First occurrence should not be marked as duplicate
        self.assertFalse(results[0]['is_duplicate'])
        
        # Third item should be marked as batch duplicate
        self.assertTrue(results[2]['is_duplicate'])
        self.assertEqual(results[2]['duplicate_type'], 'batch_duplicate')
        self.assertEqual(results[2]['similarity_score'], 1.0)
        self.assertEqual(results[2]['suggested_action'], 'skip')
    
    def test_duplicate_statistics(self):
        """Test duplicate statistics generation"""
        # Mock recent memories with some duplicates
        duplicate_memories = [
            {'context': 'Content A', 'timestamp': '2025-07-30T10:00:00'},
            {'context': 'Content B', 'timestamp': '2025-07-30T11:00:00'},
            {'context': 'Content A', 'timestamp': '2025-07-30T12:00:00'},  # Duplicate
            {'context': 'Content C', 'timestamp': '2025-07-30T13:00:00'},
            {'context': 'Content B', 'timestamp': '2025-07-30T14:00:00'},  # Duplicate
        ]
        
        self.mock_db_manager.get_blocks_since_time.return_value = duplicate_memories
        
        stats = self.detector.get_duplicate_statistics(days=7)
        
        self.assertEqual(stats['total_memories'], 5)
        self.assertEqual(stats['unique_memories'], 3)
        self.assertEqual(stats['estimated_duplicates'], 2)
        self.assertAlmostEqual(stats['duplicate_rate'], 0.4, places=1)  # 2/5 = 0.4
        self.assertIn('recommendations', stats)
        
        # Test with no memories
        self.mock_db_manager.get_blocks_since_time.return_value = []
        stats = self.detector.get_duplicate_statistics(days=7)
        
        self.assertEqual(stats['total_memories'], 0)
        self.assertEqual(stats['estimated_duplicates'], 0)
        self.assertEqual(stats['duplicate_rate'], 0.0)
    
    def test_statistics_recommendations(self):
        """Test statistics-based recommendations"""
        # Test high duplicate rate recommendations  
        recommendations = self.detector._generate_statistics_recommendations(0.25)
        self.assertTrue(any('High duplicate rate' in r for r in recommendations))
        
        # Test moderate duplicate rate recommendations
        recommendations = self.detector._generate_statistics_recommendations(0.15)
        self.assertTrue(any('Moderate duplicate rate' in r for r in recommendations))
        
        # Test low duplicate rate recommendations
        recommendations = self.detector._generate_statistics_recommendations(0.03)
        self.assertTrue(any('Low duplicate rate' in r for r in recommendations))
    
    def test_search_fallback_mechanism(self):
        """Test fallback mechanism when embedding search fails"""
        # Mock embedding search failure
        self.mock_db_manager.search_blocks_by_embedding.side_effect = Exception("Embedding search failed")
        
        # Should fall back to keyword search
        result = self.detector.check_duplicate(self.duplicate_test_contents['original'])
        
        # Should still work with keyword search
        self.assertIsInstance(result, dict)
        self.assertIn('is_duplicate', result)
        
        # Verify keyword search was called
        self.mock_db_manager.search_blocks_by_keyword.assert_called()
    
    def test_context_window_optimization(self):
        """Test context window optimization for performance"""
        # Test with custom context window
        result = self.detector.check_duplicate(
            self.duplicate_test_contents['original'], 
            context_window_hours=12
        )
        
        self.assertIsInstance(result, dict)
        
        # When embedding and keyword searches fail, should use time-based search
        self.mock_db_manager.search_blocks_by_embedding.return_value = []
        self.mock_db_manager.search_blocks_by_keyword.return_value = []
        
        result = self.detector.check_duplicate(
            self.duplicate_test_contents['original'],
            context_window_hours=24
        )
        
        # Should call get_blocks_since_time with appropriate cutoff
        self.mock_db_manager.get_blocks_since_time.assert_called()
        call_args = self.mock_db_manager.get_blocks_since_time.call_args[0]
        cutoff_time = datetime.fromisoformat(call_args[0])
        expected_cutoff = datetime.now() - timedelta(hours=24)
        
        # Should be within a few minutes of expected time
        time_diff = abs((cutoff_time - expected_cutoff).total_seconds())
        self.assertLess(time_diff, 300)  # Within 5 minutes
    
    def test_error_handling(self):
        """Test error handling and graceful degradation"""
        # Mock database manager that raises exceptions
        self.mock_db_manager.search_blocks_by_embedding.side_effect = Exception("Database error")
        self.mock_db_manager.search_blocks_by_keyword.side_effect = Exception("Database error")  
        self.mock_db_manager.get_blocks_since_time.side_effect = Exception("Database error")
        
        result = self.detector.check_duplicate(self.duplicate_test_contents['original'])
        
        # Should return error result gracefully
        self.assertFalse(result['is_duplicate'])
        self.assertEqual(result['duplicate_type'], 'error')
        self.assertEqual(result['suggested_action'], 'store_anyway')
        self.assertIn('Duplicate check failed', result['recommendation'])
    
    def test_unicode_and_special_characters(self):
        """Test handling of Unicode and special characters"""
        unicode_contents = [
            self.test_contents['unicode'],
            self.test_contents['special_chars'],
            "Mixed content: Hello 世界 🌍 test@example.com",
            "Emoji only: 😊😂🤔🎉✨",
            "Code snippet: def func(): return True",
        ]
        
        for content in unicode_contents:
            result = self.detector.check_duplicate(content)
            
            # Should handle without errors
            self.assertIsInstance(result, dict)
            self.assertIn('is_duplicate', result)
            self.assertIsInstance(result['similarity_score'], float)
            self.assertGreaterEqual(result['similarity_score'], 0.0)
            self.assertLessEqual(result['similarity_score'], 1.0)
    
    def test_performance_benchmarks(self):
        """Test performance benchmarks for duplicate detection"""
        import time
        
        # Test single duplicate check performance
        start_time = time.time()
        for i in range(100):
            result = self.detector.check_duplicate(f"Test content {i}")
        elapsed_time = time.time() - start_time
        
        # Should process at least 50 checks per second
        checks_per_second = 100 / elapsed_time
        self.assertGreater(checks_per_second, 50, 
                          f"Duplicate checking too slow: {checks_per_second:.1f} checks/sec")
        
        # Test batch processing performance
        batch_contents = [f"Batch content {i}" for i in range(50)]
        
        start_time = time.time()
        results = self.detector.check_batch_duplicates(batch_contents)
        batch_time = time.time() - start_time
        
        # Batch processing should complete within reasonable time
        self.assertLess(batch_time, 5.0, f"Batch processing too slow: {batch_time:.2f}s")
        self.assertEqual(len(results), 50)
    
    def test_memory_usage_optimization(self):
        """Test memory usage with large datasets"""
        import tracemalloc
        
        tracemalloc.start()
        
        # Process many duplicate checks
        for i in range(200):
            content = f"Memory test content {i % 10}"  # Some duplicates
            result = self.detector.check_duplicate(content)
            self.assertIsInstance(result, dict)
        
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        
        # Memory usage should be reasonable (less than 20MB peak)
        peak_mb = peak / 1024 / 1024
        self.assertLess(peak_mb, 20, f"Memory usage too high: {peak_mb:.1f}MB")
    
    def test_hash_collision_handling(self):
        """Test handling of potential hash collisions"""
        # Create contents that might have hash collisions
        content1 = "Content with specific hash pattern A"
        content2 = "Content with specific hash pattern B"
        
        # Calculate hashes
        hash1 = hashlib.md5(content1.lower().strip().encode()).hexdigest()
        hash2 = hashlib.md5(content2.lower().strip().encode()).hexdigest()
        
        # They should be different
        self.assertNotEqual(hash1, hash2)
        
        # Test with similar but not identical content
        similar_content = "Content with specific hash pattern A "  # Extra space
        
        result = self.detector.check_duplicate(content1)
        self.assertIsInstance(result, dict)
    
    def test_large_content_handling(self):
        """Test handling of very large content"""
        # Test with very long content
        large_content = self.test_contents['long'] * 100  # ~50KB content
        
        start_time = time.time()
        result = self.detector.check_duplicate(large_content)
        elapsed_time = time.time() - start_time
        
        # Should complete within reasonable time (less than 2 seconds)
        self.assertLess(elapsed_time, 2.0, f"Large content processing too slow: {elapsed_time:.2f}s")
        
        # Should still produce valid result
        self.assertIsInstance(result, dict)
        self.assertIn('similarity_score', result)
    
    def test_custom_similarity_thresholds(self):
        """Test custom similarity thresholds"""
        # Test with strict thresholds
        strict_detector = DuplicateDetector(
            db_manager=self.mock_db_manager,
            similarity_threshold=0.95
        )
        
        self.assertEqual(strict_detector.similarity_threshold, 0.95)
        
        # Test with lenient thresholds
        lenient_detector = DuplicateDetector(
            db_manager=self.mock_db_manager,
            similarity_threshold=0.7
        )
        
        self.assertEqual(lenient_detector.similarity_threshold, 0.7)
        
        # Test classification with different thresholds
        duplicate_type, is_duplicate = strict_detector._classify_duplicate(0.85)
        self.assertEqual(duplicate_type, 'partial')
        self.assertFalse(is_duplicate)
        
        duplicate_type, is_duplicate = lenient_detector._classify_duplicate(0.85)
        self.assertEqual(duplicate_type, 'similar')
        self.assertTrue(is_duplicate)


class TestDuplicateDetectorIntegration(BaseGreeumTestCase):
    """Integration tests for DuplicateDetector with realistic scenarios"""
    
    def setUp(self):
        """Set up integration test fixtures"""
        super().setUp()
        self.detector = DuplicateDetector(self.mock_db_manager)
        
        # Realistic memory database
        self.realistic_memories = [
            {
                'block_index': 1,
                'context': "프로젝트 회의에서 새로운 기능 개발 방향에 대해 논의했습니다. React 18을 사용하기로 결정했고, 개발 기간은 2개월로 예상됩니다.",
                'timestamp': '2025-07-30T09:00:00',
                'importance': 0.8
            },
            {
                'block_index': 2, 
                'context': "Bug fix completed: Fixed memory leak in user authentication module. Performance improved by 30%.",
                'timestamp': '2025-07-30T14:30:00',
                'importance': 0.7
            },
            {
                'block_index': 3,
                'context': "Today I learned about advanced SQL optimization techniques including query execution plans and index optimization.",
                'timestamp': '2025-07-29T16:45:00',
                'importance': 0.6
            }
        ]
    
    def test_realistic_duplicate_scenarios(self):
        """Test realistic duplicate detection scenarios"""
        test_scenarios = [
            {
                'name': 'exact_duplicate',
                'content': "프로젝트 회의에서 새로운 기능 개발 방향에 대해 논의했습니다. React 18을 사용하기로 결정했고, 개발 기간은 2개월로 예상됩니다.",
                'expected_duplicate': True,
                'expected_type': 'exact'
            },
            {
                'name': 'paraphrased',
                'content': "프로젝트 미팅에서 새 기능 개발에 대해 이야기했습니다. React 18 사용을 결정했고, 개발은 2개월 걸릴 것 같습니다.",
                'expected_duplicate': True,
                'expected_type': 'similar'
            },
            {
                'name': 'related_topic',
                'content': "오늘 React 18의 새로운 기능들에 대해 학습했습니다. 동시성 모드가 정말 인상적이었습니다.",
                'expected_duplicate': False,
                'expected_type': 'partial'
            },
            {
                'name': 'completely_different',
                'content': "오늘 날씨가 정말 좋네요. 산책을 다녀왔습니다.",
                'expected_duplicate': False,
                'expected_type': 'none'
            }
        ]
        
        for scenario in test_scenarios:
            # Mock appropriate database response
            if scenario['expected_duplicate']:
                self.mock_db_manager.search_blocks_by_embedding.return_value = [self.realistic_memories[0]]
            else:
                self.mock_db_manager.search_blocks_by_embedding.return_value = self.realistic_memories
            
            result = self.detector.check_duplicate(scenario['content'])
            
            self.assertEqual(result['is_duplicate'], scenario['expected_duplicate'],
                           f"Failed for scenario: {scenario['name']}")
            
            if scenario['expected_duplicate']:
                self.assertEqual(result['duplicate_type'], scenario['expected_type'],
                               f"Wrong duplicate type for scenario: {scenario['name']}")
    
    def test_real_world_content_types(self):
        """Test with real-world content types"""
        content_types = {
            'meeting_notes': "팀 스탠드업 미팅 (2025-07-31): 진행사항 - API 개발 80% 완료, 프론트엔드 60% 완료. 이슈: 데이터베이스 성능 최적화 필요. 다음 목표: 베타 버전 8월 15일 배포.",
            'code_commit': "feat: Add user authentication middleware\n\n- Implemented JWT token validation\n- Added role-based access control\n- Updated API documentation\n- Added unit tests with 95% coverage",
            'learning_note': "오늘 학습한 내용: PostgreSQL의 인덱스 최적화 기법. B-tree, Hash, GIN 인덱스의 차이점과 사용 사례를 이해했습니다. 쿼리 성능이 3배 향상되었습니다.",
            'bug_report': "Critical bug in production: NullPointerException in UserService.getUserById() when user is not found. Error rate: 0.3%. Temporary fix applied. Needs permanent solution by tomorrow.",
            'personal_note': "오늘은 개인적으로 힘든 하루였지만, 팀원들의 도움으로 문제를 해결할 수 있었습니다. 협업의 중요성을 다시 한 번 느꼈습니다."
        }
        
        # Test each content type
        for content_type, content in content_types.items():
            # Mock no duplicates for clean testing
            self.mock_db_manager.search_blocks_by_embedding.return_value = []
            
            result = self.detector.check_duplicate(content, importance=0.7)
            
            # All should be processed successfully
            self.assertIsInstance(result, dict)
            self.assertIn('is_duplicate', result)
            self.assertIn('recommendation', result)
            
            # Should generally recommend storing (no duplicates)
            self.assertEqual(result['suggested_action'], 'store_anyway',
                           f"Failed for content type: {content_type}")


if __name__ == '__main__':
    # Create test suite
    suite = unittest.TestSuite()
    
    # Add all test cases
    suite.addTest(unittest.makeSuite(TestDuplicateDetector))
    suite.addTest(unittest.makeSuite(TestDuplicateDetectorIntegration))
    
    # Run tests with verbose output
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print(f"\n{'='*50}")
    print(f"DuplicateDetector Test Summary:")
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Success rate: {((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100):.1f}%")
    print(f"{'='*50}")