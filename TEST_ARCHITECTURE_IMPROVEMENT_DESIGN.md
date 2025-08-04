# Test Architecture Improvement Design

## 🎯 목표
견고하고 유지보수 가능한 테스트 아키텍처 구축

## 🔍 현재 테스트 문제점 분석

### 문제 1: 테스트 격리 부족
```python
# 현재 문제 (test_v204_core.py)
class TestDatabaseManager(unittest.TestCase):
    def setUp(self):
        self.db_manager = DatabaseManager(db_path=":memory:")  # 공유 상태
```

### 문제 2: 동시성 테스트 불완전
```python
# 현재 문제: 스레드별 독립 연결 없음
def add_blocks(thread_id):
    self.db_manager.add_block(block)  # 동일한 연결 공유
```

### 문제 3: 테스트 데이터 관리 부족
- 각 테스트마다 다른 데이터베이스 상태
- 테스트 간 상호 영향
- 정리(cleanup) 불완전

## 💡 개선된 테스트 아키텍처 설계

### 1. 테스트 베이스 클래스 설계
```python
import tempfile
import threading
import unittest
from pathlib import Path
from typing import Optional

class GreeumTestBase(unittest.TestCase):
    """Greeum 테스트를 위한 기본 클래스"""
    
    def setUp(self):
        """각 테스트마다 독립적인 환경 구성"""
        # 임시 디렉토리 생성
        self.test_dir = Path(tempfile.mkdtemp(prefix="greeum_test_"))
        self.test_db_path = self.test_dir / "test.db"
        
        # 독립적인 DatabaseManager 인스턴스
        self.db_manager = self._create_db_manager()
        self.block_manager = self._create_block_manager()
        
        # 테스트 데이터 준비
        self._setup_test_data()
    
    def tearDown(self):
        """테스트 후 정리"""
        try:
            if hasattr(self, 'db_manager'):
                self.db_manager.close()
        except:
            pass
        
        # 임시 파일 정리
        import shutil
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir, ignore_errors=True)
    
    def _create_db_manager(self):
        """테스트용 DatabaseManager 생성"""
        return DatabaseManager(db_path=str(self.test_db_path))
    
    def _create_block_manager(self):
        """테스트용 BlockManager 생성"""
        return BlockManager(self.db_manager)
    
    def _setup_test_data(self):
        """기본 테스트 데이터 생성"""
        pass  # 하위 클래스에서 오버라이드
```

### 2. 동시성 테스트 전용 클래스
```python
class ConcurrencyTestMixin:
    """동시성 테스트를 위한 믹스인"""
    
    def run_concurrent_test(self, worker_func, num_threads=5, timeout=30):
        """
        동시성 테스트 실행 헬퍼
        
        Args:
            worker_func: 각 스레드에서 실행할 함수
            num_threads: 스레드 수
            timeout: 타임아웃 (초)
        """
        results = []
        errors = []
        completed = threading.Event()
        
        def thread_wrapper(thread_id):
            try:
                # 각 스레드마다 독립적인 DB 연결
                thread_db = DatabaseManager(db_path=str(self.test_db_path))
                thread_block_manager = BlockManager(thread_db)
                
                result = worker_func(thread_id, thread_db, thread_block_manager)
                results.append((thread_id, result))
            except Exception as e:
                errors.append((thread_id, str(e)))
            finally:
                try:
                    thread_db.close()
                except:
                    pass
        
        # 스레드 생성 및 실행
        threads = []
        for i in range(num_threads):
            thread = threading.Thread(target=thread_wrapper, args=(i,))
            threads.append(thread)
            thread.start()
        
        # 모든 스레드 완료 대기
        all_completed = True
        for thread in threads:
            thread.join(timeout=timeout)
            if thread.is_alive():
                all_completed = False
        
        return {
            'results': results,
            'errors': errors,
            'completed': all_completed,
            'total_threads': num_threads
        }
```

### 3. 테스트 데이터 팩토리
```python
class TestDataFactory:
    """테스트 데이터 생성 팩토리"""
    
    @staticmethod
    def create_test_block(index=0, context=None, **kwargs):
        """표준 테스트 블록 생성"""
        return {
            "block_index": index,
            "timestamp": "2025-08-04T12:00:00",
            "context": context or f"Test context {index}",
            "keywords": kwargs.get("keywords", [f"keyword{index}"]),
            "tags": kwargs.get("tags", ["test"]),
            "embedding": kwargs.get("embedding", [0.1] * 128),
            "importance": kwargs.get("importance", 0.5),
            "hash": f"hash_{index}",
            "prev_hash": kwargs.get("prev_hash", "")
        }
    
    @staticmethod
    def create_block_chain(count=10):
        """연결된 블록 체인 생성"""
        blocks = []
        prev_hash = ""
        
        for i in range(count):
            block = TestDataFactory.create_test_block(
                index=i,
                prev_hash=prev_hash
            )
            # 실제 해시 계산
            block_manager = BlockManager(None)
            block["hash"] = block_manager._compute_hash(block)
            prev_hash = block["hash"]
            blocks.append(block)
        
        return blocks
    
    @staticmethod
    def create_malicious_inputs():
        """SQL Injection 테스트용 악성 입력들"""
        return [
            "'; DROP TABLE blocks; --",
            "' OR '1'='1",
            "UNION SELECT * FROM sqlite_master",
            "../../../etc/passwd",
            "<script>alert('xss')</script>",
            "NULL\x00",
            "A" * 10000  # 버퍼 오버플로우 테스트
        ]
```

### 4. 개선된 테스트 클래스들
```python
class TestDatabaseManagerImproved(GreeumTestBase):
    """개선된 DatabaseManager 테스트"""
    
    def test_health_check_normal(self):
        """정상 상태 health check"""
        self.assertTrue(self.db_manager.health_check())
    
    def test_sql_injection_prevention(self):
        """SQL Injection 방어 테스트"""
        malicious_inputs = TestDataFactory.create_malicious_inputs()
        
        for malicious_input in malicious_inputs:
            with self.subTest(input=malicious_input):
                # 악성 입력에도 시스템이 안전해야 함
                results = self.db_manager.search_blocks_by_keyword([malicious_input])
                self.assertIsInstance(results, list)
                
                # 데이터베이스 무결성 유지 확인
                self.assertTrue(self.db_manager.health_check())


class TestConcurrentAccess(GreeumTestBase, ConcurrencyTestMixin):
    """동시성 테스트"""
    
    def test_concurrent_write_operations(self):
        """동시 쓰기 작업 테스트"""
        
        def write_worker(thread_id, db_manager, block_manager):
            """각 스레드에서 실행할 쓰기 작업"""
            blocks_written = 0
            for i in range(10):
                block = TestDataFactory.create_test_block(
                    index=thread_id * 100 + i,
                    context=f"Thread {thread_id} Block {i}"
                )
                block_manager.add_block(**block)
                blocks_written += 1
            return blocks_written
        
        # 5개 스레드로 동시 실행
        result = self.run_concurrent_test(write_worker, num_threads=5)
        
        # 검증
        self.assertEqual(len(result['errors']), 0, 
                        f"Concurrent write errors: {result['errors']}")
        self.assertTrue(result['completed'])
        self.assertEqual(len(result['results']), 5)
        
        # 모든 블록이 정상적으로 저장되었는지 확인
        total_blocks = sum(result[1] for result in result['results'])
        self.assertEqual(total_blocks, 50)  # 5 스레드 * 10 블록
    
    def test_read_write_concurrency(self):
        """읽기/쓰기 동시성 테스트"""
        # 기본 데이터 준비
        test_blocks = TestDataFactory.create_block_chain(20)
        for block in test_blocks:
            self.block_manager.add_block(**block)
        
        def mixed_worker(thread_id, db_manager, block_manager):
            operations = 0
            for i in range(10):
                if i % 2 == 0:
                    # 읽기 작업
                    results = block_manager.search_by_keywords([f"keyword{i}"])
                    operations += len(results)
                else:
                    # 쓰기 작업
                    block = TestDataFactory.create_test_block(
                        index=thread_id * 1000 + i
                    )
                    block_manager.add_block(**block)
                    operations += 1
            return operations
        
        result = self.run_concurrent_test(mixed_worker, num_threads=3)
        
        self.assertEqual(len(result['errors']), 0)
        self.assertTrue(result['completed'])


class TestBlockManagerIntegrity(GreeumTestBase):
    """블록 체인 무결성 테스트"""
    
    def _setup_test_data(self):
        """테스트용 블록 체인 준비"""
        self.test_blocks = TestDataFactory.create_block_chain(5)
        for block in self.test_blocks:
            self.block_manager.add_block(**block)
    
    def test_verify_integrity_valid_chain(self):
        """정상 블록 체인 검증"""
        self.assertTrue(self.block_manager.verify_integrity())
    
    def test_verify_integrity_broken_chain(self):
        """손상된 블록 체인 검증"""
        # 마지막 블록의 해싱을 의도적으로 손상
        last_block = self.test_blocks[-1]
        corrupted_block = last_block.copy()
        corrupted_block['hash'] = 'corrupted_hash'
        
        # 직접 데이터베이스 수정 (손상 시뮬레이션)
        self.db_manager.conn.execute(
            "UPDATE blocks SET hash = ? WHERE block_index = ?",
            ('corrupted_hash', last_block['block_index'])
        )
        self.db_manager.conn.commit()
        
        # 무결성 검증 실패해야 함
        self.assertFalse(self.block_manager.verify_integrity())
```

## 🧪 테스트 실행 전략

### 테스트 분류
```python
# pytest markers 사용
import pytest

@pytest.mark.unit
def test_basic_functionality():
    """단위 테스트"""

@pytest.mark.integration  
def test_component_integration():
    """통합 테스트"""

@pytest.mark.concurrency
def test_thread_safety():
    """동시성 테스트"""

@pytest.mark.performance
def test_large_scale():
    """성능 테스트"""

@pytest.mark.security
def test_injection_prevention():
    """보안 테스트"""
```

### CI/CD 테스트 단계
```yaml
# .github/workflows/comprehensive_test.yml
test-matrix:
  - stage: "unit"
    marker: "unit" 
    timeout: "5m"
  - stage: "integration"
    marker: "integration"
    timeout: "10m"
  - stage: "concurrency" 
    marker: "concurrency"
    timeout: "15m"
  - stage: "performance"
    marker: "performance"
    timeout: "30m"
```

## 📋 구현 계획

### Day 1: 기반 클래스
- [ ] GreeumTestBase 구현
- [ ] ConcurrencyTestMixin 구현
- [ ] TestDataFactory 구현

### Day 2: 테스트 재작성
- [ ] 기존 테스트 마이그레이션
- [ ] 동시성 테스트 강화
- [ ] 엣지 케이스 추가

### Day 3: CI/CD 통합
- [ ] pytest 설정 최적화
- [ ] GitHub Actions 워크플로우 개선
- [ ] 테스트 리포트 개선

이 아키텍처로 안정적이고 신뢰할 수 있는 테스트 환경을 구축할 수 있습니다.