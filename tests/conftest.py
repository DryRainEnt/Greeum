"""
pytest 설정 및 공통 픽스처
"""

import os
import tempfile
import pytest
import asyncio
from pathlib import Path
from unittest.mock import Mock, patch
from typing import Generator, Dict, Any

# 프로젝트 루트를 Python 경로에 추가
import sys
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


@pytest.fixture(scope="session")
def event_loop():
    """세션 스코프 이벤트 루프"""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function")
def temp_dir() -> Generator[Path, None, None]:
    """임시 디렉토리 픽스처"""
    with tempfile.TemporaryDirectory() as tmp_dir:
        yield Path(tmp_dir)


@pytest.fixture(scope="function")
def temp_db_path(temp_dir: Path) -> str:
    """임시 데이터베이스 경로 픽스처"""
    return str(temp_dir / "test.db")


@pytest.fixture(scope="function")
def mock_database_manager():
    """Mock 데이터베이스 매니저 픽스처"""
    mock_db = Mock()
    mock_db.health_check.return_value = True
    mock_db.get_blocks.return_value = []
    mock_db.add_block.return_value = "test_block_id"
    mock_db.search_blocks.return_value = []
    return mock_db


@pytest.fixture(scope="function")
def mock_mcp_server():
    """Mock MCP 서버 픽스처"""
    mock_server = Mock()
    mock_server.initialize = Mock(return_value=asyncio.coroutine(lambda: None)())
    mock_server.handle_request = Mock(return_value={
        "jsonrpc": "2.0",
        "id": 1,
        "result": {"status": "success"}
    })
    return mock_server


@pytest.fixture(scope="function")
def mock_embedding_model():
    """Mock 임베딩 모델 픽스처"""
    with patch('greeum.embedding_models.get_embedding') as mock_embedding:
        mock_embedding.return_value = [0.1] * 128  # 128차원 임베딩
        yield mock_embedding


@pytest.fixture(scope="function")
def test_environment_vars():
    """테스트용 환경 변수 설정"""
    original_env = {}
    test_env = {
        'GREEUM_DATA_DIR': str(Path.cwd() / "test_data"),
        'GREEUM_DB_PATH': str(Path.cwd() / "test.db"),
        'GREEUM_LOG_LEVEL': 'DEBUG'
    }
    
    # 기존 환경 변수 백업
    for key in test_env:
        original_env[key] = os.environ.get(key)
        os.environ[key] = test_env[key]
    
    yield test_env
    
    # 환경 변수 복원
    for key, value in original_env.items():
        if value is None:
            os.environ.pop(key, None)
        else:
            os.environ[key] = value


@pytest.fixture(scope="function")
def performance_test_data():
    """성능 테스트용 샘플 데이터"""
    return {
        'small_texts': [
            "This is a short test text",
            "Another brief example",
            "Quick performance test"
        ],
        'medium_texts': [
            "This is a medium length test text that contains more content for performance testing purposes",
            "Another medium length example with sufficient content to measure processing time accurately",
            "Performance testing requires adequate sample size for meaningful measurements"
        ],
        'large_texts': [
            "This is a much longer test text that simulates real-world content for comprehensive performance testing. " * 10,
            "Another large text sample for performance measurement with substantial content to evaluate system behavior under realistic conditions. " * 10
        ]
    }


# 마커별 픽스처
@pytest.fixture(scope="function")
def database_test_setup(temp_db_path: str):
    """데이터베이스 테스트용 설정"""
    from greeum.core.database_manager import DatabaseManager
    db_manager = DatabaseManager(connection_string=temp_db_path)
    yield db_manager
    # 정리 작업
    if os.path.exists(temp_db_path):
        os.remove(temp_db_path)


@pytest.fixture(scope="function")
def mcp_test_setup():
    """MCP 테스트용 설정"""
    with patch('greeum.mcp.native.server.GreeumNativeMCPServer') as mock_server_class:
        mock_server = Mock()
        mock_server.initialize = Mock(return_value=asyncio.coroutine(lambda: None)())
        mock_server_class.return_value = mock_server
        yield mock_server


# 성능 테스트용 픽스처
@pytest.fixture(scope="function")
def performance_benchmark():
    """성능 벤치마크 픽스처"""
    import time
    start_time = time.perf_counter()
    yield
    end_time = time.perf_counter()
    duration = end_time - start_time
    print(f"\n⏱️  Test duration: {duration:.3f}s")


# 자동 마커 적용 (선택사항)
def pytest_collection_modifyitems(config, items):
    """테스트 수집 시 자동으로 마커 적용"""
    for item in items:
        # 파일 경로 기반 자동 마커 적용
        if "performance_suite" in str(item.fspath):
            item.add_marker(pytest.mark.performance)
        elif "integration" in str(item.fspath):
            item.add_marker(pytest.mark.integration)
        elif "test_native_mcp" in str(item.fspath) or "test_fastmcp" in str(item.fspath):
            item.add_marker(pytest.mark.mcp)
        
        # 함수명 기반 자동 마커 적용
        if "performance" in item.name.lower():
            item.add_marker(pytest.mark.performance)
        if "database" in item.name.lower() or "db_" in item.name.lower():
            item.add_marker(pytest.mark.database)
        if "mcp" in item.name.lower():
            item.add_marker(pytest.mark.mcp)
