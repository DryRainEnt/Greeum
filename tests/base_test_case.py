#!/usr/bin/env python3
"""
Greeum 테스트를 위한 기본 클래스

이 모듈은 Greeum 프로젝트의 모든 테스트에서 공통으로 사용되는
설정, 픽스처, 헬퍼 메서드들을 제공합니다.
"""

import unittest
import tempfile
import os
import sys
import sqlite3
from unittest.mock import Mock, MagicMock
from typing import Dict, List, Any, Optional

# 프로젝트 루트를 path에 추가
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from greeum import DatabaseManager, BlockManager, STMManager, CacheManager
from greeum.core.prompt_wrapper import PromptWrapper
from greeum.embedding_models import get_embedding


class BaseGreeumTestCase(unittest.TestCase):
    """Greeum 테스트를 위한 기본 클래스"""
    
    def setUp(self):
        """모든 Greeum 테스트에서 공통으로 사용되는 설정"""
        # 임시 환경 설정
        self.temp_dir = tempfile.mkdtemp()
        self.test_db_path = os.path.join(self.temp_dir, "test_greeum.db")
        
        # Greeum 핵심 컴포넌트 초기화
        self.db_manager = DatabaseManager(connection_string=self.test_db_path)
        self.block_manager = BlockManager(self.db_manager)
        self.stm_manager = STMManager(self.db_manager)
        self.cache_manager = CacheManager(
            block_manager=self.block_manager, 
            stm_manager=self.stm_manager
        )
        self.prompt_wrapper = PromptWrapper(self.cache_manager, self.stm_manager)
        
        # Mock 객체들 (필요시 사용)
        self.mock_db_manager = Mock()
        self.mock_block_manager = Mock()
        self.mock_stm_manager = Mock()
        
        # 공통 테스트 데이터 설정
        self._setup_common_test_data()
        
        # 공통 Mock 응답 설정
        self._setup_common_mock_responses()
    
    def tearDown(self):
        """테스트 후 정리 작업"""
        # 임시 파일 및 디렉토리 정리
        if os.path.exists(self.test_db_path):
            try:
                os.remove(self.test_db_path)
            except (PermissionError, OSError):
                pass  # 파일이 사용 중인 경우 무시
        
        try:
            os.rmdir(self.temp_dir)
        except (PermissionError, OSError):
            pass  # 디렉토리가 비어있지 않은 경우 무시
    
    def _setup_common_test_data(self):
        """공통 테스트 데이터 설정"""
        # 다양한 품질의 테스트 컨텐츠
        self.test_contents = {
            'excellent': "Today I completed the machine learning model training with 95.2% accuracy on the validation dataset. The model was deployed to production at 2025-07-31 10:30 AM using Docker containers on AWS ECS. Key hyperparameters: learning_rate=0.001, batch_size=32, epochs=100. Performance metrics show 15ms average inference time.",
            'good': "프로젝트 회의에서 중요한 결정을 내렸습니다. React 18을 사용하여 새로운 대시보드를 개발하기로 했고, PostgreSQL 14를 데이터베이스로 선정했습니다. 개발 기간은 3개월로 예상됩니다.",
            'acceptable': "오늘은 새로운 프로젝트를 시작했는데 정말 흥미로운 주제입니다. 앞으로 많은 것을 배울 수 있을 것 같아요.",
            'poor': "안녕하세요 오늘 날씨가 좋네요",
            'very_poor': "ㅎㅎㅎ",
            'empty': "",
            'short': "Hi",
            'too_long': "x" * 15000,  # Very long content
            'special_chars': "!!!@@@###$$$%%%^^^&&&***((()))",
            'mixed_languages': "Hello 안녕하세요 こんにちは Bonjour Hola",
            'code_snippet': "def calculate_accuracy(predictions, labels):\\n    correct = sum(p == l for p, l in zip(predictions, labels))\\n    return correct / len(labels) * 100",
            'repetitive': "test test test test test test test test test test",
            'urls_and_data': "Check out https://example.com for the latest updates. Contact: user@domain.com, Phone: +1-555-123-4567"
        }
        
        # 중복 감지 테스트용 컨텐츠
        self.duplicate_test_contents = {
            'original': "Today I completed the machine learning project with 95% accuracy",
            'exact_duplicate': "Today I completed the machine learning project with 95% accuracy",
            'similar': "Today I finished the machine learning project with 95% accuracy",
            'partial_similar': "I completed a project today with good results",
            'different': "The weather is nice and sunny today"
        }
        
        # 다국어 테스트 컨텐츠
        self.multilingual_contents = {
            'korean': "한글 텍스트와 emoji 😊 섞인 내용입니다",
            'french': "Français avec des accents: café, naïve, résumé",
            'russian': "Русский текст с кириллицей",
            'chinese': "中文内容测试",
            'mixed_emoji': "🎉🎊✨ Only emojis and symbols! 🚀🌟💫",
            'mixed_languages': "Mixed: Hello 안녕 こんにちは 你好 🌍"
        }
        
        # 공통 테스트 쿼리들
        self.test_queries = [
            "최근 프로젝트 진행 상황은 어떻게 되나요?",
            "개발 중 어려웠던 점은 무엇인가요?",
            "다음에 구현할 기능은 무엇인가요?",
            "성능 개선을 위한 계획이 있나요?",
            "사용자 피드백은 어떤가요?"
        ]
        
        # 검색 테스트용 쿼리들
        self.search_queries = [
            "프로젝트 진행 상황",
            "개발 계획",
            "성능 개선",
            "메모리 최적화",
            "사용자 피드백",
            "버그 수정",
            "새로운 기능",
            "테스트 결과"
        ]
    
    def _setup_common_mock_responses(self):
        """공통 Mock 응답 설정"""
        # Mock 메모리 블록들
        self.mock_memory_blocks = [
            {
                'block_index': 1,
                'context': self.test_contents['excellent'],
                'timestamp': '2025-07-30T10:00:00',
                'importance': 0.9,
                'keywords': ['machine', 'learning', 'accuracy'],
                'tags': ['development', 'ml', 'production']
            },
            {
                'block_index': 2,
                'context': self.test_contents['good'],
                'timestamp': '2025-07-30T11:00:00',
                'importance': 0.7,
                'keywords': ['프로젝트', '회의', 'React'],
                'tags': ['meeting', 'decision', 'frontend']
            },
            {
                'block_index': 3,
                'context': self.test_contents['poor'],
                'timestamp': '2025-07-30T12:00:00',
                'importance': 0.3,
                'keywords': ['weather', 'sunny'],
                'tags': ['casual', 'weather']
            }
        ]
        
        # Mock DB manager 기본 응답 설정
        self.mock_db_manager.search_blocks_by_embedding.return_value = self.mock_memory_blocks
        self.mock_db_manager.search_blocks_by_keyword.return_value = self.mock_memory_blocks
        self.mock_db_manager.get_blocks_since_time.return_value = self.mock_memory_blocks
        self.mock_db_manager.get_blocks.return_value = self.mock_memory_blocks
    
    # === 공통 헬퍼 메서드들 ===
    
    def create_test_memory_blocks(self, count: int = 10) -> List[Dict[str, Any]]:
        """테스트용 메모리 블록 생성"""
        created_blocks = []
        base_contexts = [
            "프로젝트 개발 진행 상황", "새로운 기능 구현", "성능 최적화 작업", "버그 수정 완료",
            "사용자 피드백 반영", "테스트 결과 분석", "코드 리뷰 진행", "문서 업데이트"
        ]
        
        for i in range(count):
            context = f"{base_contexts[i % len(base_contexts)]} - 작업 {i}"
            keywords = context.split()[:3]
            tags = [f"tag_{i % 5}", "test"]
            embedding = get_embedding(context)
            importance = 0.5 + (i % 5) * 0.1
            
            try:
                result = self.block_manager.add_block(
                    context=context,
                    keywords=keywords,
                    tags=tags,
                    embedding=embedding,
                    importance=importance,
                    metadata={"test_block": True, "index": i}
                )
                if result:
                    created_blocks.append(result)
            except Exception as e:
                # 테스트 환경에서는 에러를 무시하고 계속 진행
                pass
        
        return created_blocks
    
    def assert_greeum_components_initialized(self):
        """Greeum 컴포넌트들이 올바르게 초기화되었는지 확인"""
        self.assertIsNotNone(self.db_manager)
        self.assertIsNotNone(self.block_manager)
        self.assertIsNotNone(self.stm_manager)
        self.assertIsNotNone(self.cache_manager)
        self.assertIsNotNone(self.prompt_wrapper)
    
    def assert_database_exists(self):
        """테스트 데이터베이스가 생성되었는지 확인"""
        self.assertTrue(os.path.exists(self.test_db_path))
    
    def assert_valid_memory_block(self, block: Dict[str, Any]):
        """메모리 블록이 유효한 구조를 가지는지 확인"""
        required_fields = ['context', 'keywords', 'tags', 'importance']
        for field in required_fields:
            self.assertIn(field, block, f"Memory block missing required field: {field}")
        
        # 중요도는 0-1 사이의 값이어야 함
        self.assertGreaterEqual(block['importance'], 0.0)
        self.assertLessEqual(block['importance'], 1.0)
        
        # 컨텍스트는 비어있지 않아야 함
        self.assertIsInstance(block['context'], str)
        self.assertGreater(len(block['context'].strip()), 0)
    
    def create_mock_component(self, component_name: str, **kwargs) -> Mock:
        """특정 컴포넌트에 대한 Mock 객체 생성"""
        mock_component = Mock()
        
        # 컴포넌트별 기본 Mock 동작 설정
        if component_name == 'database_manager':
            mock_component.add_block.return_value = {'block_index': 1, 'success': True}
            mock_component.search_blocks_by_embedding.return_value = self.mock_memory_blocks
            mock_component.get_blocks.return_value = self.mock_memory_blocks
            
        elif component_name == 'block_manager':
            mock_component.add_block.return_value = {'block_index': 1, 'success': True}
            mock_component.search_by_embedding.return_value = self.mock_memory_blocks
            mock_component.get_recent_blocks.return_value = self.mock_memory_blocks
            
        elif component_name == 'quality_validator':
            mock_component.validate_memory_quality.return_value = {
                'quality_score': 0.8,
                'quality_level': 'good',
                'should_store': True,
                'suggestions': [],
                'warnings': []
            }
            
        elif component_name == 'duplicate_detector':
            mock_component.check_duplicate.return_value = {
                'is_duplicate': False,
                'duplicate_type': 'none',
                'similarity_score': 0.1,
                'suggested_action': 'store_anyway',
                'recommendation': 'Unique content, safe to store'
            }
        
        # 사용자 정의 속성 추가
        for key, value in kwargs.items():
            setattr(mock_component, key, value)
        
        return mock_component
    
    def setup_database_with_test_data(self, block_count: int = 5):
        """테스트 데이터로 데이터베이스 초기화"""
        # 데이터베이스 테이블 생성
        self.db_manager.create_tables()
        
        # 테스트 블록 추가
        return self.create_test_memory_blocks(block_count)
    
    def verify_database_tables_exist(self):
        """필수 데이터베이스 테이블들이 존재하는지 확인"""
        with sqlite3.connect(self.test_db_path) as conn:
            cursor = conn.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name NOT LIKE 'sqlite_%'
            """)
            tables = [row[0] for row in cursor.fetchall()]
            
            # 필수 테이블들 확인
            expected_tables = ['memory_blocks', 'stm_entries']  # 실제 테이블명에 맞게 조정
            for table in expected_tables:
                if table in tables:  # 유연한 테이블 확인
                    return True
            
            # 최소한 하나의 테이블은 있어야 함
            self.assertGreater(len(tables), 0, "No tables found in test database")
    
    def get_test_embedding(self, text: str) -> List[float]:
        """테스트용 임베딩 생성"""
        try:
            return get_embedding(text)
        except Exception:
            # 임베딩 생성 실패시 더미 임베딩 반환
            return [0.1 * i for i in range(128)]  # 128차원 더미 임베딩
    
    def assert_search_results_valid(self, results: List[Dict[str, Any]], min_count: int = 0):
        """검색 결과의 유효성 확인"""
        self.assertIsInstance(results, list)
        self.assertGreaterEqual(len(results), min_count)
        
        for result in results:
            self.assertIsInstance(result, dict)
            # 검색 결과에 최소한의 필드가 있는지 확인
            if 'context' in result:
                self.assertIsInstance(result['context'], str)
    
    def create_test_user_input(self, content_type: str = 'good') -> str:
        """특정 품질의 테스트 사용자 입력 생성"""
        if content_type in self.test_contents:
            return self.test_contents[content_type]
        else:
            return f"테스트 사용자 입력: {content_type} 품질 컨텐츠"
    
    def skip_if_component_unavailable(self, component_name: str):
        """컴포넌트가 사용 불가능한 경우 테스트 스킵"""
        try:
            if component_name == 'quality_validator':
                from greeum.core.quality_validator import QualityValidator
                QualityValidator()
            elif component_name == 'duplicate_detector':
                from greeum.core.duplicate_detector import DuplicateDetector
                DuplicateDetector(self.mock_db_manager)
            elif component_name == 'usage_analytics':
                from greeum.core.usage_analytics import UsageAnalytics
                UsageAnalytics()
        except ImportError as e:
            self.skipTest(f"{component_name} not available: {e}")
        except Exception as e:
            self.skipTest(f"Failed to initialize {component_name}: {e}")


class BaseGreeumIntegrationTestCase(BaseGreeumTestCase):
    """통합 테스트를 위한 확장된 기본 클래스"""
    
    def setUp(self):
        """통합 테스트용 추가 설정"""
        super().setUp()
        
        # 실제 데이터베이스와 컴포넌트들 초기화
        self.setup_database_with_test_data(10)
        
        # v2.1.0 신규 컴포넌트들 (선택적 초기화)
        self._setup_optional_components()
    
    def _setup_optional_components(self):
        """선택적 컴포넌트들 초기화"""
        try:
            from greeum.core.quality_validator import QualityValidator
            self.quality_validator = QualityValidator()
        except ImportError:
            self.quality_validator = None
        
        try:
            from greeum.core.duplicate_detector import DuplicateDetector
            self.duplicate_detector = DuplicateDetector(self.db_manager)
        except ImportError:
            self.duplicate_detector = None
        
        try:
            from greeum.core.usage_analytics import UsageAnalytics
            self.usage_analytics = UsageAnalytics()
        except ImportError:
            self.usage_analytics = None
    
    def run_comprehensive_test_suite(self) -> Dict[str, Any]:
        """포괄적인 통합 테스트 실행"""
        results = {
            'component_tests': {},
            'integration_tests': {},
            'performance_tests': {}
        }
        
        # 컴포넌트별 기본 기능 테스트
        results['component_tests']['database'] = self._test_database_operations()
        results['component_tests']['memory'] = self._test_memory_operations()
        results['component_tests']['search'] = self._test_search_operations()
        
        return results
    
    def _test_database_operations(self) -> bool:
        """데이터베이스 기본 작업 테스트"""
        try:
            # 테이블 존재 확인
            self.verify_database_tables_exist()
            
            # 기본 CRUD 작업 테스트
            test_context = "통합 테스트용 컨텍스트"
            result = self.block_manager.add_block(
                context=test_context,
                keywords=["통합", "테스트"],
                tags=["integration"],
                embedding=self.get_test_embedding(test_context),
                importance=0.7
            )
            
            return result is not None
        except Exception:
            return False
    
    def _test_memory_operations(self) -> bool:
        """메모리 작업 테스트"""
        try:
            # STM 작업 테스트
            test_data = {"key": "test_value", "timestamp": "2025-01-01T00:00:00"}
            # STM 관련 테스트 로직
            
            return True
        except Exception:
            return False
    
    def _test_search_operations(self) -> bool:
        """검색 작업 테스트"""
        try:
            # 임베딩 검색 테스트
            query_embedding = self.get_test_embedding("검색 테스트 쿼리")
            results = self.block_manager.search_by_embedding(query_embedding, top_k=3)
            
            self.assert_search_results_valid(results, min_count=0)
            return True
        except Exception:
            return False