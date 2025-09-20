# pytest 마커 사용 가이드

## 개요

Greeum 프로젝트에서 테스트 성능 향상과 개발자 경험 개선을 위해 pytest 마커를 도입했습니다. 이를 통해 테스트를 분류하고 선택적으로 실행할 수 있습니다.

## 마커 정의

### 🚀 Fast 테스트 (`@pytest.mark.fast`)
- **목적**: 빠른 단위 테스트 (1초 미만)
- **특징**: Mock 사용, 메모리 내 연산만
- **예시**: 함수 호출, 유틸리티 테스트

```python
@pytest.mark.fast
@pytest.mark.unit
class TestTextUtils:
    def test_convert_numpy_types(self):
        # 단순 함수 호출 테스트
        result = convert_numpy_types(np.int32(42))
        assert result == 42
```

### 🐌 Slow 테스트 (`@pytest.mark.slow`)
- **목적**: 느린 통합 테스트 (1초 이상)
- **특징**: 실제 I/O, 네트워크 호출, 대량 데이터 처리
- **예시**: 데이터베이스 테스트, MCP 통신 테스트

```python
@pytest.mark.slow
@pytest.mark.database
class TestDatabaseOperations:
    def test_database_io(self):
        # 실제 데이터베이스 I/O 테스트
        db_manager = DatabaseManager()
        # ... 데이터베이스 작업
```

### ⚡ Performance 테스트 (`@pytest.mark.performance`)
- **목적**: 성능 측정/벤치마크 테스트
- **특징**: 성능 측정이 주목적
- **예시**: 캐시 성능, 검색 성능 테스트

```python
@pytest.mark.performance
def test_cache_performance():
    # 성능 측정 테스트
    start_time = time.time()
    # ... 성능 테스트 코드
    duration = time.time() - start_time
    assert duration < 0.1  # 100ms 미만
```

### 🗄️ Database 테스트 (`@pytest.mark.database`)
- **목적**: 데이터베이스 의존적 테스트
- **특징**: 실제 데이터베이스 I/O 필요
- **예시**: CRUD 작업, 트랜잭션 테스트

```python
@pytest.mark.database
@pytest.mark.slow
class TestDatabaseManager:
    def test_add_block(self):
        # 데이터베이스 작업 테스트
        db_manager = DatabaseManager()
        # ... 데이터베이스 작업
```

### 🔌 MCP 테스트 (`@pytest.mark.mcp`)
- **목적**: MCP 서버/클라이언트 테스트
- **특징**: MCP 프로토콜 통신 테스트
- **예시**: Native MCP, FastMCP 테스트

```python
@pytest.mark.mcp
@pytest.mark.slow
@pytest.mark.integration
async def test_native_mcp_functionality():
    # MCP 서버 통신 테스트
    server = GreeumNativeMCPServer()
    # ... MCP 통신 테스트
```

### 🔗 Integration 테스트 (`@pytest.mark.integration`)
- **목적**: 통합 테스트
- **특징**: 여러 컴포넌트 간 상호작용 테스트
- **예시**: 전체 워크플로우 테스트

```python
@pytest.mark.integration
@pytest.mark.slow
class TestIntegratedFeatures:
    def test_end_to_end_workflow(self):
        # 통합 테스트
        # ... 여러 컴포넌트 상호작용
```

### 🧪 Unit 테스트 (`@pytest.mark.unit`)
- **목적**: 순수 단위 테스트
- **특징**: 단일 함수/클래스 테스트
- **예시**: 유틸리티 함수 테스트

```python
@pytest.mark.unit
@pytest.mark.fast
class TestUtilityFunctions:
    def test_simple_function(self):
        # 단위 테스트
        result = simple_function(input_data)
        assert result == expected_output
```

## 테스트 실행 방법

### 1. 마커별 실행

```bash
# 빠른 테스트만 실행
pytest -m "fast"

# 느린 테스트만 실행
pytest -m "slow"

# 성능 테스트만 실행
pytest -m "performance"

# 데이터베이스 테스트만 실행
pytest -m "database"

# MCP 테스트만 실행
pytest -m "mcp"

# 통합 테스트만 실행
pytest -m "integration"

# 단위 테스트만 실행
pytest -m "unit"
```

### 2. 복합 마커 실행

```bash
# 빠른 단위 테스트만 실행
pytest -m "fast and unit"

# 느린 통합 테스트만 실행
pytest -m "slow and integration"

# 데이터베이스 테스트 제외
pytest -m "not database"

# 성능 테스트 제외
pytest -m "not performance"
```

### 3. tox를 사용한 실행

```bash
# 빠른 테스트
tox -e fast

# 느린 테스트
tox -e slow

# 성능 테스트
tox -e performance

# 통합 테스트
tox -e integration
```

### 4. 스크립트를 사용한 실행

```bash
# 특정 마커 실행
python scripts/run_tests_by_marker.py fast

# 모든 마커 실행
python scripts/run_tests_by_marker.py
```

## CI/CD 통합

### GitHub Actions 예시

```yaml
name: Tests

on: [push, pull_request]

jobs:
  fast-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Run fast tests
        run: pytest -m "fast" -v

  slow-tests:
    runs-on: ubuntu-latest
    if: github.event_name == 'push'
    steps:
      - uses: actions/checkout@v3
      - name: Run slow tests
        run: pytest -m "slow" -v

  performance-tests:
    runs-on: ubuntu-latest
    if: github.event_name == 'push' && github.ref == 'refs/heads/main'
    steps:
      - uses: actions/checkout@v3
      - name: Run performance tests
        run: pytest -m "performance" -v
```

## 모범 사례

### 1. 마커 선택 기준

- **Fast**: Mock 사용, 메모리 내 연산만
- **Slow**: 실제 I/O, 네트워크 호출, 대량 데이터 처리
- **Performance**: 성능 측정이 주목적
- **Database**: 데이터베이스 I/O 필요
- **MCP**: MCP 프로토콜 통신
- **Integration**: 여러 컴포넌트 상호작용
- **Unit**: 단일 함수/클래스 테스트

### 2. 마커 조합

```python
# 일반적인 조합
@pytest.mark.fast
@pytest.mark.unit

@pytest.mark.slow
@pytest.mark.database

@pytest.mark.slow
@pytest.mark.mcp
@pytest.mark.integration
```

### 3. 테스트 실행 시간 최적화

```bash
# 개발 중: 빠른 테스트만
pytest -m "fast"

# PR 전: 빠른 + 단위 테스트
pytest -m "fast or unit"

# 릴리스 전: 전체 테스트
pytest
```

### 4. 픽스처 활용

```python
# conftest.py에서 제공하는 픽스처 활용
def test_database_operation(database_test_setup):
    db_manager = database_test_setup
    # ... 테스트 코드

def test_mcp_communication(mcp_test_setup):
    mock_server = mcp_test_setup
    # ... 테스트 코드
```

## 문제 해결

### 1. 마커가 인식되지 않는 경우

```bash
# pytest 설정 확인
pytest --markers

# 설정 파일 확인
cat pytest.ini
cat pyproject.toml
```

### 2. 테스트 실행 시간 측정

```bash
# 실행 시간 측정
pytest --durations=10

# 특정 마커의 실행 시간
pytest -m "fast" --durations=10
```

### 3. 마커 검증

```bash
# 마커 사용 검증
pytest --strict-markers

# 특정 마커의 테스트 목록
pytest -m "fast" --collect-only
```

## 참고 자료

- [pytest 마커 공식 문서](https://docs.pytest.org/en/stable/mark.html)
- [pytest 설정 가이드](https://docs.pytest.org/en/stable/customize.html)
- [tox 설정 가이드](https://tox.wiki/en/latest/config.html)
