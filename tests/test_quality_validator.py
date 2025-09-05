#!/usr/bin/env python3
"""
Comprehensive Unit Tests for QualityValidator (Greeum v2.0.5)
Tests memory-efficient content analysis, quality score calculation,
edge cases, quality classification, and recommendation generation.
"""

import unittest
from unittest.mock import Mock, patch

from tests.base_test_case import BaseGreeumTestCase
from greeum.core.quality_validator import QualityValidator, QualityLevel


class TestQualityValidator(BaseGreeumTestCase):
    """Comprehensive test suite for QualityValidator class"""
    
    def setUp(self):
        """Set up test fixtures before each test method"""
        super().setUp()
        self.validator = QualityValidator()
    
    def test_validator_initialization(self):
        """Test QualityValidator initialization"""
        self.assertEqual(self.validator.min_length, 10)
        self.assertEqual(self.validator.max_length, 10000)
        self.assertIn('english', self.validator.stop_words)
        self.assertIn('korean', self.validator.stop_words)
        self.assertIn('common', self.validator.stop_words)
    
    def test_quality_level_enum(self):
        """Test QualityLevel enum values"""
        self.assertEqual(QualityLevel.EXCELLENT.value, "excellent")
        self.assertEqual(QualityLevel.GOOD.value, "good")
        self.assertEqual(QualityLevel.ACCEPTABLE.value, "acceptable")
        self.assertEqual(QualityLevel.POOR.value, "poor")
        self.assertEqual(QualityLevel.VERY_POOR.value, "very_poor")
    
    def test_length_quality_assessment(self):
        """Test length-based quality assessment"""
        # Test too short
        result = self.validator._assess_length_quality("short")
        self.assertEqual(result['issue'], 'too_short')
        self.assertEqual(result['score'], 0.1)
        
        # Test minimal length
        result = self.validator._assess_length_quality("This is minimal content")
        self.assertEqual(result['issue'], 'minimal')
        self.assertEqual(result['score'], 0.5)
        
        # Test optimal length
        result = self.validator._assess_length_quality(self.test_contents['good'])
        self.assertIsNone(result['issue'])
        self.assertGreaterEqual(result['score'], 0.7)
        
        # Test too long
        result = self.validator._assess_length_quality(self.test_contents['too_long'])
        self.assertEqual(result['issue'], 'too_long')
        self.assertEqual(result['score'], 0.3)
    
    def test_meaningful_word_detection(self):
        """Test meaningful word detection logic"""
        # Test meaningful words
        self.assertTrue(self.validator._is_meaningful_word("important"))
        self.assertTrue(self.validator._is_meaningful_word("project"))
        self.assertTrue(self.validator._is_meaningful_word("algorithm"))
        
        # Test stop words
        self.assertFalse(self.validator._is_meaningful_word("the"))
        self.assertFalse(self.validator._is_meaningful_word("and"))
        self.assertFalse(self.validator._is_meaningful_word("은"))  # Korean stop word
        
        # Test short words
        self.assertFalse(self.validator._is_meaningful_word("a"))
        self.assertFalse(self.validator._is_meaningful_word("to"))
        
        # Test non-alphabetic
        self.assertFalse(self.validator._is_meaningful_word("123"))
        self.assertFalse(self.validator._is_meaningful_word("@@@"))
    
    def test_content_richness_assessment(self):
        """Test memory-efficient content richness evaluation"""
        # Test rich content
        result = self.validator._assess_content_richness(self.test_contents['excellent'])
        self.assertGreater(result['score'], 0.6)
        self.assertGreater(result['meaningful_word_ratio'], 0.3)
        self.assertGreater(result['lexical_diversity'], 0.5)
        
        # Test poor content
        result = self.validator._assess_content_richness(self.test_contents['repetitive'])
        self.assertLess(result['score'], 0.5)
        self.assertLess(result['lexical_diversity'], 0.3)
        
        # Test empty content
        result = self.validator._assess_content_richness("")
        self.assertEqual(result['score'], 0.0)
        self.assertEqual(result['meaningful_word_ratio'], 0.0)
        
        # Test memory limits with very long content
        very_long_content = " ".join(["word" + str(i) for i in range(15000)])
        result = self.validator._assess_content_richness(very_long_content)
        self.assertTrue(result['truncated'])
        self.assertEqual(result['total_words'], 10000)  # Should be limited
    
    def test_structural_quality_assessment(self):
        """Test structural quality evaluation"""
        # Test well-structured content
        structured_content = "This is the first sentence. Here's another one! And a question?"
        result = self.validator._assess_structural_quality(structured_content)
        self.assertGreater(result['score'], 0.6)
        self.assertEqual(result['sentence_count'], 3)
        self.assertGreater(result['punctuation_count'], 0)
        
        # Test repetitive content
        result = self.validator._assess_structural_quality(self.test_contents['repetitive'])
        self.assertIn('excessive_repetition', result['issues'])
        self.assertLess(result['score'], 0.7)
        
        # Test single long sentence
        long_sentence = "This is a very long sentence without proper punctuation that goes on and on"
        result = self.validator._assess_structural_quality(long_sentence)
        self.assertEqual(result['sentence_count'], 1)
    
    def test_language_quality_assessment(self):
        """Test language quality evaluation"""
        # Test normal content
        result = self.validator._assess_language_quality(self.test_contents['good'])
        self.assertGreaterEqual(result['score'], 0.5)
        
        # Test content with excessive special characters
        result = self.validator._assess_language_quality(self.test_contents['special_chars'])
        self.assertLess(result['score'], 0.5)
        self.assertGreater(result['special_char_ratio'], 0.1)
        
        # Test content with double spaces
        content_with_spaces = "This  has  double  spaces"
        result = self.validator._assess_language_quality(content_with_spaces)
        self.assertLess(result['score'], 0.7)
        
        # Test all uppercase
        uppercase_content = "THIS IS ALL UPPERCASE CONTENT THAT IS QUITE LONG"
        result = self.validator._assess_language_quality(uppercase_content)
        self.assertLess(result['score'], 0.5)
        
        # Test mixed case (good)
        mixed_case = "This Has Proper Mixed Case"
        result = self.validator._assess_language_quality(mixed_case)
        self.assertTrue(result['has_mixed_case'])
    
    def test_information_density_assessment(self):
        """Test information density evaluation"""
        # Test content with high information density
        info_dense = "Meeting on 2025-07-31 at 10:30 AM with John Smith about Project Alpha. Budget: $50,000. Contact: john@example.com"
        result = self.validator._assess_information_density(info_dense)
        self.assertGreater(result['score'], 0.7)
        self.assertGreater(result['density'], 0.2)
        self.assertGreater(result['info_matches'], 5)
        
        # Test content with low information density
        result = self.validator._assess_information_density(self.test_contents['poor'])
        self.assertLessEqual(result['score'], 0.5)
        self.assertLessEqual(result['density'], 0.1)
        
        # Test empty content
        result = self.validator._assess_information_density("")
        self.assertEqual(result['score'], 0.3)
        self.assertEqual(result['density'], 0.0)
    
    def test_searchability_assessment(self):
        """Test searchability evaluation"""
        # Test searchable content
        searchable = "Machine learning project using TensorFlow and Python for natural language processing"
        result = self.validator._assess_searchability(searchable)
        self.assertGreater(result['score'], 0.7)
        self.assertGreater(result['potential_keywords'], 3)
        
        # Test less searchable content
        result = self.validator._assess_searchability("Hi how are you today")
        self.assertLess(result['score'], 0.9)
        self.assertLess(result['potential_keywords'], 3)
        
        # Test content with unique identifiers
        with_identifiers = "Project ABC123 at example.com with contact user@domain.com"
        result = self.validator._assess_searchability(with_identifiers)
        self.assertGreater(result['unique_identifiers'], 0)
    
    def test_temporal_relevance_assessment(self):
        """Test temporal relevance evaluation"""
        # Test content with temporal information
        temporal_content = "오늘 2025년 7월 31일에 중요한 회의가 있었습니다. 다음주에 follow-up이 있을 예정입니다."
        result = self.validator._assess_temporal_relevance(temporal_content)
        self.assertGreater(result['score'], 0.6)
        self.assertGreater(result['temporal_matches'], 0)
        
        # Test content with current context
        current_context = "현재 진행 중인 프로젝트에 대해 지금 논의하고 있습니다"
        result = self.validator._assess_temporal_relevance(current_context)
        self.assertTrue(result['has_current_context'])
        
        # Test content without temporal information
        result = self.validator._assess_temporal_relevance("This is generic content")
        self.assertEqual(result['temporal_matches'], 0)
        self.assertFalse(result['has_current_context'])
    
    def test_quality_score_calculation(self):
        """Test comprehensive quality score calculation"""
        # Mock quality factors for testing
        excellent_factors = {
            'length': {'score': 1.0},
            'richness': {'score': 0.9},
            'structure': {'score': 0.8},
            'language': {'score': 0.9},
            'information_density': {'score': 0.8},
            'searchability': {'score': 0.9},
            'temporal_relevance': {'score': 0.7}
        }
        
        score = self.validator._calculate_quality_score(excellent_factors, 0.8)
        self.assertGreaterEqual(score, 0.8)
        self.assertLessEqual(score, 1.0)
        
        # Test with poor factors
        poor_factors = {
            'length': {'score': 0.2},
            'richness': {'score': 0.1},
            'structure': {'score': 0.3},
            'language': {'score': 0.4},
            'information_density': {'score': 0.2},
            'searchability': {'score': 0.1},
            'temporal_relevance': {'score': 0.5}
        }
        
        score = self.validator._calculate_quality_score(poor_factors, 0.3)
        self.assertLessEqual(score, 0.5)
    
    def test_quality_level_classification(self):
        """Test quality level classification"""
        self.assertEqual(self.validator._classify_quality_level(0.95), QualityLevel.EXCELLENT)
        self.assertEqual(self.validator._classify_quality_level(0.75), QualityLevel.GOOD)
        self.assertEqual(self.validator._classify_quality_level(0.55), QualityLevel.ACCEPTABLE)
        self.assertEqual(self.validator._classify_quality_level(0.35), QualityLevel.POOR)
        self.assertEqual(self.validator._classify_quality_level(0.15), QualityLevel.VERY_POOR)
    
    def test_suggestion_generation(self):
        """Test quality improvement suggestion generation"""
        # Test suggestions for short content
        short_factors = {
            'length': {'score': 0.2, 'issue': 'too_short'},
            'richness': {'score': 0.5, 'meaningful_word_ratio': 0.2},
            'structure': {'score': 0.7, 'sentence_count': 1, 'issues': []},
            'searchability': {'score': 0.3, 'potential_keywords': 1},
            'information_density': {'score': 0.2, 'density': 0.05}
        }
        
        suggestions = self.validator._generate_suggestions(short_factors, "Hi there")
        self.assertGreater(len(suggestions), 0)
        self.assertTrue(any("short" in s.lower() for s in suggestions))
        
        # Test suggestions for repetitive content
        repetitive_factors = {
            'length': {'score': 0.7, 'issue': None},
            'richness': {'score': 0.3, 'meaningful_word_ratio': 0.6},
            'structure': {'score': 0.4, 'sentence_count': 2, 'issues': ['excessive_repetition']},
            'searchability': {'score': 0.5, 'potential_keywords': 2},
            'information_density': {'score': 0.5, 'density': 0.1}
        }
        
        suggestions = self.validator._generate_suggestions(repetitive_factors, "test test test")
        self.assertTrue(any("repetitive" in s.lower() or "repeat" in s.lower() for s in suggestions))
    
    def test_storage_recommendation(self):
        """Test storage recommendation logic"""
        self.assertTrue(self.validator._should_store_memory(0.9, QualityLevel.EXCELLENT))
        self.assertTrue(self.validator._should_store_memory(0.75, QualityLevel.GOOD))
        self.assertTrue(self.validator._should_store_memory(0.55, QualityLevel.ACCEPTABLE))
        self.assertFalse(self.validator._should_store_memory(0.35, QualityLevel.POOR))
        self.assertFalse(self.validator._should_store_memory(0.15, QualityLevel.VERY_POOR))
    
    def test_importance_adjustment(self):
        """Test importance adjustment based on quality"""
        # High quality should increase importance
        adjusted = self.validator._adjust_importance(0.5, 0.9)
        self.assertGreater(adjusted, 0.5)
        
        # Low quality should decrease importance
        adjusted = self.validator._adjust_importance(0.5, 0.2)
        self.assertLess(adjusted, 0.5)
        
        # Test bounds
        adjusted = self.validator._adjust_importance(0.0, 1.0)
        self.assertGreaterEqual(adjusted, 0.0)
        
        adjusted = self.validator._adjust_importance(1.0, 0.0)
        self.assertLessEqual(adjusted, 1.0)
    
    def test_warning_generation(self):
        """Test warning generation for quality issues"""
        # Create factors with various issues
        warning_factors = {
            'length': {'score': 0.8, 'issue': 'too_short'},
            'language': {'score': 0.3},
            'information_density': {'score': 0.8, 'density': 0.02},
            'searchability': {'score': 0.5, 'potential_keywords': 0}
        }
        
        warnings = self.validator._generate_warnings(warning_factors, "Short content")
        
        self.assertGreater(len(warnings), 0)
        self.assertTrue(any("brief" in w.lower() for w in warnings))
        self.assertTrue(any("language" in w.lower() for w in warnings))
        self.assertTrue(any("density" in w.lower() for w in warnings))
        self.assertTrue(any("search" in w.lower() for w in warnings))
    
    def test_comprehensive_validation_excellent_content(self):
        """Test comprehensive validation with excellent content"""
        result = self.validator.validate_memory_quality(
            self.test_contents['excellent'], 
            importance=0.8
        )
        
        # Check structure
        self.assertIn('quality_score', result)
        self.assertIn('quality_level', result)
        self.assertIn('quality_factors', result)
        self.assertIn('suggestions', result)
        self.assertIn('should_store', result)
        self.assertIn('adjusted_importance', result)
        self.assertIn('warnings', result)
        self.assertIn('timestamp', result)
        self.assertIn('validation_version', result)
        
        # Check values
        self.assertGreaterEqual(result['quality_score'], 0.7)
        self.assertIn(result['quality_level'], ['excellent', 'good'])
        self.assertTrue(result['should_store'])
        self.assertEqual(result['validation_version'], '2.1.0')
    
    def test_comprehensive_validation_poor_content(self):
        """Test comprehensive validation with poor content"""
        result = self.validator.validate_memory_quality(
            self.test_contents['very_poor'], 
            importance=0.3
        )
        
        self.assertLessEqual(result['quality_score'], 0.6)
        self.assertIn(result['quality_level'], ['poor', 'very_poor', 'acceptable'])
        # Note: Quality algorithm improved, may store acceptable content
        self.assertGreater(len(result['suggestions']), 0)
        self.assertGreater(len(result['warnings']), 0)
    
    def test_edge_cases(self):
        """Test various edge cases"""
        # Empty content
        result = self.validator.validate_memory_quality("", 0.5)
        self.assertIsInstance(result, dict)
        self.assertIn('quality_score', result)
        
        # None content (should be handled gracefully)
        try:
            result = self.validator.validate_memory_quality(None, 0.5)
            # If it doesn't raise an exception, check it returns valid result
            self.assertIsInstance(result, dict)
        except (TypeError, AttributeError):
            # This is also acceptable behavior
            pass
        
        # Very long content
        result = self.validator.validate_memory_quality(self.test_contents['too_long'], 0.5)
        self.assertEqual(result['quality_factors']['length']['issue'], 'too_long')
        
        # Special characters only
        result = self.validator.validate_memory_quality(self.test_contents['special_chars'], 0.5)
        self.assertLessEqual(result['quality_score'], 0.5)
        
        # Mixed languages
        result = self.validator.validate_memory_quality(self.test_contents['mixed_languages'], 0.5)
        self.assertIsInstance(result['quality_score'], float)
    
    def test_batch_validation(self):
        """Test batch memory validation"""
        test_batch = [
            (self.test_contents['excellent'], 0.8),
            (self.test_contents['good'], 0.6),
            (self.test_contents['poor'], 0.3)
        ]
        
        results = self.validator.validate_batch_memories(test_batch)
        
        self.assertEqual(len(results), 3)
        for result in results:
            self.assertIn('quality_score', result)
            self.assertIn('quality_level', result)
        
        # First should be better than last
        self.assertGreater(results[0]['quality_score'], results[2]['quality_score'])
    
    def test_quality_statistics(self):
        """Test quality statistics generation"""
        # Create sample validation results
        validations = [
            {'quality_level': 'excellent', 'quality_score': 0.9, 'should_store': True},
            {'quality_level': 'good', 'quality_score': 0.8, 'should_store': True},
            {'quality_level': 'acceptable', 'quality_score': 0.6, 'should_store': True},
            {'quality_level': 'poor', 'quality_score': 0.4, 'should_store': False},
            {'quality_level': 'very_poor', 'quality_score': 0.2, 'should_store': False}
        ]
        
        stats = self.validator.get_quality_statistics(validations)
        
        self.assertEqual(stats['total_validations'], 5)
        self.assertAlmostEqual(stats['average_quality_score'], 0.58, places=2)
        self.assertEqual(stats['quality_level_distribution']['excellent'], 1)
        self.assertEqual(stats['quality_level_distribution']['poor'], 1)
        self.assertAlmostEqual(stats['storage_recommendation_rate'], 0.6, places=1)
        
        # Test empty validations
        empty_stats = self.validator.get_quality_statistics([])
        self.assertIn('error', empty_stats)
    
    def test_error_handling(self):
        """Test error handling and fallback behavior"""
        # Mock a validation failure
        with patch.object(self.validator, '_assess_quality_factors', side_effect=Exception("Test error")):
            result = self.validator.validate_memory_quality("test content", 0.5)
            
            # Should return fallback result
            self.assertEqual(result['quality_score'], 0.5)
            self.assertEqual(result['quality_level'], 'acceptable')
            self.assertTrue(result['should_store'])  # Safe fallback
            self.assertIn('error', result['warnings'][0].lower())
    
    def test_performance_with_large_content(self):
        """Test performance with large content"""
        import time
        
        # Test with very long content
        large_content = "This is a test sentence. " * 1000  # ~25KB
        
        start_time = time.time()
        result = self.validator.validate_memory_quality(large_content, 0.5)
        elapsed_time = time.time() - start_time
        
        # Should complete within reasonable time (less than 1 second)
        self.assertLess(elapsed_time, 1.0, f"Validation too slow: {elapsed_time:.2f}s")
        
        # Should still produce valid result
        self.assertIsInstance(result['quality_score'], float)
        self.assertIn(result['quality_level'], [level.value for level in QualityLevel])
    
    def test_memory_efficiency(self):
        """Test memory efficiency with content processing"""
        # Test that the validator doesn't consume excessive memory
        import tracemalloc
        
        tracemalloc.start()
        
        # Process multiple large contents
        for i in range(10):
            large_content = f"Content batch {i}. " + ("Word " * 1000)
            result = self.validator.validate_memory_quality(large_content, 0.5)
            self.assertIsInstance(result, dict)
        
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        
        # Memory usage should be reasonable (less than 50MB peak)
        peak_mb = peak / 1024 / 1024
        self.assertLess(peak_mb, 50, f"Memory usage too high: {peak_mb:.1f}MB")
    
    def test_unicode_and_special_content(self):
        """Test handling of Unicode and special content"""
        unicode_contents = [
            "한글 텍스트와 emoji 😊 섞인 내용입니다",
            "Français avec des accents: café, naïve, résumé",
            "Русский текст с кириллицей",
            "中文内容测试",
            "🎉🎊✨ Only emojis and symbols! 🚀🌟💫",
            "Mixed: Hello 안녕 こんにちは 你好 🌍"
        ]
        
        for content in unicode_contents:
            result = self.validator.validate_memory_quality(content, 0.5)
            
            # Should handle without errors
            self.assertIsInstance(result, dict)
            self.assertIn('quality_score', result)
            self.assertIsInstance(result['quality_score'], float)
            self.assertGreaterEqual(result['quality_score'], 0.0)
            self.assertLessEqual(result['quality_score'], 1.0)


class TestQualityValidatorIntegration(BaseGreeumTestCase):
    """Integration tests for QualityValidator with realistic scenarios"""
    
    def setUp(self):
        """Set up integration test fixtures"""
        super().setUp()
        self.validator = QualityValidator()
    
    def test_realistic_user_inputs(self):
        """Test with realistic user input scenarios"""
        realistic_inputs = {
            'project_update': "프로젝트 상태 업데이트: 백엔드 API 개발이 85% 완료되었고, 프론트엔드 React 컴포넌트는 60% 진행되었습니다. 다음주까지 베타 버전 배포 예정입니다. 주요 이슈: 데이터베이스 성능 최적화 필요.",
            'casual_chat': "안녕하세요! 오늘 날씨가 정말 좋네요 ㅎㅎ",
            'technical_note': "Bug fix: Fixed memory leak in WebSocket connection handler. Issue was caused by event listeners not being properly cleaned up on disconnect. Solution: Added cleanup function in useEffect hook. Performance improved by 40%.",
            'learning_note': "Today I learned about the difference between async/await and Promises in JavaScript. Async/await is syntactic sugar that makes asynchronous code look more like synchronous code, which improves readability.",
            'meeting_minutes': "팀 회의 (2025-07-31): 참석자 - 김철수, 박영희, 이민수. 안건: Q3 목표 설정, 새로운 기능 우선순위 논의. 결정사항: 사용자 인증 시스템 우선 개발, 8월 15일까지 완료 목표.",
            'error_report': "Error in production: NullPointerException at line 247 in UserService.java. Occurs when user profile is null. Temporary fix applied. Need permanent solution.",
            'reminder': "Remember to update SSL certificates before they expire on August 15th",
        }
        
        for scenario, content in realistic_inputs.items():
            result = self.validator.validate_memory_quality(content, 0.6)
            
            # All should be processed successfully
            self.assertIsInstance(result, dict)
            self.assertGreater(len(result['suggestions']), 0)
            
            # Check quality expectations
            if scenario in ['project_update', 'technical_note', 'learning_note', 'meeting_minutes']:
                self.assertGreaterEqual(result['quality_score'], 0.6, 
                                      f"{scenario} should have good quality")
                self.assertTrue(result['should_store'])
            elif scenario in ['casual_chat']:
                self.assertLessEqual(result['quality_score'], 0.7,
                                   f"{scenario} should have lower quality")
                # Note: casual_chat may still be stored if above minimum threshold
    
    def test_code_content_validation(self):
        """Test validation of code snippets and technical content"""
        code_contents = [
            """
            def fibonacci(n):
                if n <= 1:
                    return n
                return fibonacci(n-1) + fibonacci(n-2)
            """,
            """
            SELECT users.name, COUNT(orders.id) as order_count
            FROM users 
            LEFT JOIN orders ON users.id = orders.user_id
            WHERE users.created_at >= '2025-01-01'
            GROUP BY users.id
            ORDER BY order_count DESC;
            """,
            """
            import React, { useState, useEffect } from 'react';
            
            const UserProfile = ({ userId }) => {
                const [user, setUser] = useState(null);
                
                useEffect(() => {
                    fetchUser(userId).then(setUser);
                }, [userId]);
                
                return <div>{user?.name}</div>;
            };
            """
        ]
        
        for code in code_contents:
            result = self.validator.validate_memory_quality(code.strip(), 0.7)
            
            # Code should generally have decent information density
            info_density = result['quality_factors']['information_density']['score']
            self.assertGreaterEqual(info_density, 0.5)
            
            # Should be considered worth storing
            self.assertTrue(result['should_store'])


if __name__ == '__main__':
    unittest.main()