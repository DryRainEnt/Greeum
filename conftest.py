"""
Greeum 프로젝트 테스트 설정 및 픽스처
테스트 성능 최적화를 위한 공통 설정
"""

import pytest
import tempfile
import time
from pathlib import Path
from typing import Generator, Dict, Any
import numpy as np

# pytest 마커 설정
def pytest_configure(config):
    """pytest 마커 등록"""
    config.addinivalue_line("markers", "fast: 빠른 단위 테스트 (< 1초)")
    config.addinivalue_line("markers", "slow: 시간이 오래 걸리는 테스트 (1-10초)")
    config.addinivalue_line("markers", "integration: 통합 테스트")
    config.addinivalue_line("markers", "performance: 성능 테스트 (> 10초)")
    config.addinivalue_line("markers", "database: 데이터베이스 테스트")
    config.addinivalue_line("markers", "mcp: MCP 관련 테스트")
    config.addinivalue_line("markers", "embedding: 임베딩 모델 테스트")

# 세션 레벨 픽스처들
@pytest.fixture(scope="session")
def temp_session_dir() -> Generator[Path, None, None]:
    """세션 전체에서 사용할 임시 디렉토리"""
    temp_dir = tempfile.mkdtemp(prefix="greeum_test_")
    yield Path(temp_dir)
    # 정리는 pytest가 자동으로 처리

@pytest.fixture(scope="session")
def sample_embeddings() -> Dict[str, np.ndarray]:
    """재사용 가능한 샘플 임베딩 데이터"""
    return {
        'small': np.random.rand(10, 128).astype(np.float32),
        'medium': np.random.rand(50, 128).astype(np.float32),
        'large': np.random.rand(200, 128).astype(np.float32),
        'single': np.random.rand(1, 128).astype(np.float32)
    }

@pytest.fixture(scope="session")
def test_data_cache() -> Dict[str, Any]:
    """테스트 데이터 캐시"""
    return {
        'contexts': [
            "프로젝트 시작",
            "기능 개발 중",
            "테스트 작성",
            "버그 수정",
            "문서화 작업"
        ],
        'keywords': [
            ["python", "memory", "ai"],
            ["test", "performance", "optimization"],
            ["mcp", "integration", "api"],
            ["database", "sqlite", "storage"],
            ["embedding", "vector", "search"]
        ],
        'tags': [
            ["development", "core"],
            ["testing", "optimization"],
            ["integration", "mcp"],
            ["database", "storage"],
            ["ai", "embedding"]
        ]
    }

# 함수 레벨 픽스처들
@pytest.fixture
def temp_db_path(temp_session_dir: Path) -> Path:
    """각 테스트마다 새로운 데이터베이스 경로"""
    return temp_session_dir / f"test_{int(time.time() * 1000000)}.db"

@pytest.fixture
def mock_embedding_model():
    """임베딩 모델 모킹"""
    from unittest.mock import Mock, patch
    
    with patch('greeum.embedding_models.get_embedding') as mock:
        mock.return_value = [0.1] * 128
        yield mock

@pytest.fixture
def mock_database():
    """데이터베이스 모킹"""
    from unittest.mock import Mock
    mock_db = Mock()
    mock_db.execute.return_value = []
    mock_db.fetchall.return_value = []
    mock_db.fetchone.return_value = None
    return mock_db

# 성능 측정 픽스처
@pytest.fixture
def performance_timer():
    """성능 측정을 위한 타이머"""
    class PerformanceTimer:
        def __init__(self):
            self.start_time = None
            self.end_time = None
        
        def start(self):
            self.start_time = time.perf_counter()
        
        def stop(self):
            self.end_time = time.perf_counter()
            return self.elapsed
        
        @property
        def elapsed(self):
            if self.start_time and self.end_time:
                return self.end_time - self.start_time
            return 0
    
    return PerformanceTimer()

# 테스트 분류 헬퍼 함수들
def is_fast_test(test_func) -> bool:
    """빠른 테스트인지 판단"""
    # 함수명이나 docstring에서 단서 찾기
    func_name = test_func.__name__.lower()
    docstring = (test_func.__doc__ or "").lower()
    
    fast_indicators = ['unit', 'simple', 'basic', 'mock', 'fast']
    slow_indicators = ['integration', 'performance', 'e2e', 'slow', 'heavy']
    
    # 명시적으로 slow로 표시된 경우
    if any(indicator in func_name or indicator in docstring for indicator in slow_indicators):
        return False
    
    # fast로 표시된 경우
    if any(indicator in func_name or indicator in docstring for indicator in fast_indicators):
        return True
    
    # 기본값: 단위 테스트는 fast로 간주
    return 'test_' in func_name and 'integration' not in func_name

def is_performance_test(test_func) -> bool:
    """성능 테스트인지 판단"""
    func_name = test_func.__name__.lower()
    docstring = (test_func.__doc__ or "").lower()
    
    performance_indicators = ['performance', 'benchmark', 'speed', 'timing', 'load']
    return any(indicator in func_name or indicator in docstring for indicator in performance_indicators)

def is_integration_test(test_func) -> bool:
    """통합 테스트인지 판단"""
    func_name = test_func.__name__.lower()
    docstring = (test_func.__doc__ or "").lower()
    
    integration_indicators = ['integration', 'e2e', 'end_to_end', 'workflow', 'complete']
    return any(indicator in func_name or indicator in docstring for indicator in integration_indicators)
