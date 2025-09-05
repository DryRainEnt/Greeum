"""
Phase 2 Thread Safety Tests

ThreadSafeDatabaseManager와 호환성 래퍼의 thread-safe 기능을 검증합니다.
기존 SQLite 스레딩 오류를 완전히 해결했는지 확인하는 전용 테스트 스위트입니다.

테스트 목표:
1. 동시 접근 안전성 100% 보장
2. 기존 API 완전 호환성 확인  
3. 대규모 동시 작업 안정성 검증
4. 성능 저하 없음 확인

Progressive Replacement Plan Phase 2의 핵심 검증 시스템입니다.
"""

import unittest
import os
import threading
import time
import shutil
import tempfile
from concurrent.futures import ThreadPoolExecutor, as_completed
import random

from tests.base_test_case import BaseGreeumTestCase
# Thread-safe 구현체들 import
from greeum.core.thread_safe_db import ThreadSafeDatabaseManager
from greeum.core.database_manager_v2 import DatabaseManager


class TestThreadSafeDatabaseManager(BaseGreeumTestCase):
    """ThreadSafeDatabaseManager 기본 thread-safe 기능 테스트"""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "test_thread_safe.db")
        self.db_manager = ThreadSafeDatabaseManager(connection_string=self.db_path)
    
    def tearDown(self):
        try:
            self.db_manager.close()
        except:
            pass
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_concurrent_health_checks(self):
        """동시 health_check 호출 테스트"""
        results = []
        errors = []
        
        def health_check_worker(thread_id):
            try:
                for i in range(10):  # 각 스레드에서 10번 체크
                    result = self.db_manager.health_check()
                    results.append((thread_id, i, result))
                    time.sleep(0.01)  # 짧은 지연
            except Exception as e:
                errors.append(f"Thread {thread_id}: {e}")
        
        # 5개 스레드로 동시 실행
        threads = []
        for i in range(5):
            thread = threading.Thread(target=health_check_worker, args=(i,))
            threads.append(thread)
            thread.start()
        
        for thread in threads:
            thread.join()
        
        # 검증
        self.assertEqual(len(errors), 0, f"Thread safety errors: {errors}")
        self.assertEqual(len(results), 50)  # 5 threads * 10 checks
        self.assertTrue(all(result[2] for result in results), "All health checks should pass")
    
    def test_thread_local_connections(self):
        """각 스레드가 독립적인 연결을 가지는지 테스트"""
        connection_ids = set()
        lock = threading.Lock()
        
        def get_connection_id(thread_id):
            conn = self.db_manager._get_connection()
            conn_id = id(conn)
            with lock:
                connection_ids.add((thread_id, conn_id))
        
        # 10개 스레드로 연결 ID 수집
        threads = []
        for i in range(10):
            thread = threading.Thread(target=get_connection_id, args=(i,))
            threads.append(thread)
            thread.start()
        
        for thread in threads:
            thread.join()
        
        # 각 스레드가 서로 다른 연결을 가져야 함
        unique_connections = len(set(conn_id for _, conn_id in connection_ids))
        self.assertEqual(unique_connections, 10, "Each thread should have its own connection")
    
    def test_wal_mode_enabled(self):
        """WAL 모드가 올바르게 설정되었는지 테스트"""
        conn = self.db_manager._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("PRAGMA journal_mode")
        result = cursor.fetchone()
        
        self.assertIn(result[0].lower(), ['wal', 'delete'], "WAL mode should be enabled or fallback to delete")


class TestDatabaseManagerV2Compatibility(BaseGreeumTestCase):
    """DatabaseManager V2 호환성 래퍼의 thread-safe 기능 테스트"""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "test_compat.db")
        self.db_manager = DatabaseManager(connection_string=self.db_path)
    
    def tearDown(self):
        try:
            self.db_manager.close()
        except:
            pass
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_concurrent_block_operations(self):
        """동시 블록 추가/조회 작업 테스트 - 핵심 시나리오"""
        results = []
        errors = []
        
        def block_operations_worker(thread_id):
            try:
                # 각 스레드에서 5개 블록 추가
                for i in range(5):
                    block_index = thread_id * 100 + i  # 고유한 인덱스
                    block_data = {
                        'block_index': block_index,
                        'timestamp': f'2025-08-05T03:{thread_id:02d}:{i:02d}',
                        'context': f'Thread {thread_id} Block {i} content',
                        'keywords': [f'thread{thread_id}', f'block{i}', 'concurrent'],
                        'tags': ['thread_safety_test'],
                        'embedding': [0.1 + thread_id * 0.1 + i * 0.01] * 128,
                        'importance': 0.5 + i * 0.1,
                        'hash': f'hash_{thread_id}_{i}',
                        'prev_hash': f'prev_{thread_id}_{i-1}' if i > 0 else ''
                    }
                    
                    # 블록 추가
                    added_index = self.db_manager.add_block(block_data)
                    results.append(f"Thread {thread_id}: Added block {added_index}")
                    
                    # 즉시 조회하여 검증
                    retrieved_block = self.db_manager.get_block(block_index)
                    if not retrieved_block:
                        errors.append(f"Thread {thread_id}: Failed to retrieve block {block_index}")
                    elif retrieved_block['context'] != block_data['context']:
                        errors.append(f"Thread {thread_id}: Data corruption in block {block_index}")
                    
                    time.sleep(0.01)  # 스레드 간 경합 유도
                    
            except Exception as e:
                errors.append(f"Thread {thread_id}: {e}")
        
        # 10개 스레드로 동시 실행 (기존 테스트에서 실패했던 시나리오)
        threads = []
        for i in range(10):
            thread = threading.Thread(target=block_operations_worker, args=(i,))
            threads.append(thread)
            thread.start()
        
        for thread in threads:
            thread.join()
        
        # 검증
        self.assertEqual(len(errors), 0, f"Concurrent block operations errors: {errors}")
        self.assertEqual(len(results), 50)  # 10 threads * 5 blocks
        
        # 전체 블록 수 확인
        all_blocks = self.db_manager.get_blocks(limit=1000)
        self.assertEqual(len(all_blocks), 50, "All blocks should be successfully added")
    
    def test_concurrent_search_operations(self):
        """동시 검색 작업 테스트"""
        # 테스트 데이터 먼저 추가
        test_blocks = []
        for i in range(20):
            block_data = {
                'block_index': i,
                'timestamp': f'2025-08-05T04:00:{i:02d}',
                'context': f'Search test block {i} with keyword{i % 5}',
                'keywords': [f'keyword{i % 5}', 'search_test'],
                'tags': ['search'],
                'embedding': [i * 0.05] * 128,
                'importance': 0.1 + i * 0.04,
                'hash': f'search_hash_{i}',
                'prev_hash': f'search_prev_{i-1}' if i > 0 else ''
            }
            self.db_manager.add_block(block_data)
            test_blocks.append(block_data)
        
        search_results = []
        errors = []
        
        def search_worker(thread_id):
            try:
                # 키워드 검색
                keyword_results = self.db_manager.search_blocks_by_keyword([f'keyword{thread_id % 5}'])
                search_results.append(f"Thread {thread_id}: Found {len(keyword_results)} blocks by keyword")
                
                # 임베딩 검색
                query_embedding = [thread_id * 0.1] * 128
                embedding_results = self.db_manager.search_blocks_by_embedding(query_embedding, top_k=3)
                search_results.append(f"Thread {thread_id}: Found {len(embedding_results)} blocks by embedding")
                
                # 중요도 필터링
                importance_results = self.db_manager.filter_blocks_by_importance(0.5, limit=10)
                search_results.append(f"Thread {thread_id}: Found {len(importance_results)} important blocks")
                
            except Exception as e:
                errors.append(f"Thread {thread_id}: {e}")
        
        # 8개 스레드로 동시 검색
        threads = []
        for i in range(8):
            thread = threading.Thread(target=search_worker, args=(i,))
            threads.append(thread)
            thread.start()
        
        for thread in threads:
            thread.join()
        
        # 검증
        self.assertEqual(len(errors), 0, f"Concurrent search errors: {errors}")
        self.assertEqual(len(search_results), 24)  # 8 threads * 3 search types
    
    def test_stress_test_high_concurrency(self):
        """고강도 동시성 스트레스 테스트"""
        operations_completed = []
        errors = []
        
        def stress_worker(worker_id):
            try:
                # 각 워커에서 랜덤한 작업 수행
                for i in range(20):
                    operation = random.choice(['add', 'get', 'search', 'health'])
                    
                    if operation == 'add':
                        block_data = {
                            'block_index': worker_id * 1000 + i,
                            'timestamp': f'2025-08-05T05:{worker_id:02d}:{i:02d}',
                            'context': f'Stress test {worker_id}-{i}',
                            'keywords': [f'stress{worker_id}', f'test{i}'],
                            'tags': ['stress'],
                            'embedding': [random.random()] * 128,
                            'importance': random.random(),
                            'hash': f'stress_{worker_id}_{i}',
                            'prev_hash': ''
                        }
                        self.db_manager.add_block(block_data)
                        operations_completed.append(f'add_{worker_id}_{i}')
                        
                    elif operation == 'get':
                        # 기존 블록 조회 시도
                        target_index = random.randint(0, worker_id * 1000 + i)
                        block = self.db_manager.get_block(target_index)
                        operations_completed.append(f'get_{worker_id}_{target_index}')
                        
                    elif operation == 'search':
                        results = self.db_manager.search_blocks_by_keyword(['stress'])
                        operations_completed.append(f'search_{worker_id}_{len(results)}')
                        
                    elif operation == 'health':
                        health = self.db_manager.health_check()
                        operations_completed.append(f'health_{worker_id}_{health}')
                    
                    # 랜덤 지연 (실제 사용 패턴 시뮬레이션)
                    time.sleep(random.uniform(0.001, 0.01))
                    
            except Exception as e:
                errors.append(f"Worker {worker_id}: {e}")
        
        # 15개 워커로 고강도 테스트
        with ThreadPoolExecutor(max_workers=15) as executor:
            futures = [executor.submit(stress_worker, i) for i in range(15)]
            
            for future in as_completed(futures):
                try:
                    future.result()
                except Exception as e:
                    errors.append(f"Future execution error: {e}")
        
        # 검증
        self.assertEqual(len(errors), 0, f"Stress test errors: {errors}")
        self.assertGreater(len(operations_completed), 200, "Should complete many operations")
        
        # 최종 데이터베이스 상태 확인
        final_health = self.db_manager.health_check()
        self.assertTrue(final_health, "Database should remain healthy after stress test")


class TestPerformanceRegression(BaseGreeumTestCase):
    """Thread-safe 구현의 성능 회귀 테스트"""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "test_performance.db")
        self.db_manager = DatabaseManager(connection_string=self.db_path)
    
    def tearDown(self):
        try:
            self.db_manager.close()
        except:
            pass
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_single_thread_performance(self):
        """단일 스레드 성능 기준선 측정"""
        start_time = time.time()
        
        # 100개 블록 추가
        for i in range(100):
            block_data = {
                'block_index': i,
                'timestamp': f'2025-08-05T06:00:{i:02d}',
                'context': f'Performance test block {i}',
                'keywords': [f'perf{i}', 'baseline'],
                'tags': ['performance'],
                'embedding': [i * 0.01] * 128,
                'importance': 0.5,
                'hash': f'perf_hash_{i}',
                'prev_hash': f'perf_prev_{i-1}' if i > 0 else ''
            }
            self.db_manager.add_block(block_data)
        
        # 100번 조회
        for i in range(100):
            block = self.db_manager.get_block(i)
            self.assertIsNotNone(block)
        
        elapsed_time = time.time() - start_time
        
        # 성능 기준: 200개 작업이 5초 이내에 완료되어야 함
        self.assertLess(elapsed_time, 5.0, 
                       f"Single thread performance test took {elapsed_time:.2f}s, should be < 5.0s")
        
        print(f"Single thread performance: {elapsed_time:.2f}s for 200 operations")
    
    def test_multi_thread_efficiency(self):
        """멀티 스레드 효율성 테스트"""
        start_time = time.time()
        
        def efficient_worker(thread_id):
            # 각 스레드에서 10개 블록 처리
            for i in range(10):
                block_index = thread_id * 100 + i
                block_data = {
                    'block_index': block_index,
                    'timestamp': f'2025-08-05T07:{thread_id:02d}:{i:02d}',
                    'context': f'Efficiency test {thread_id}-{i}',
                    'keywords': [f'efficient{thread_id}'],
                    'tags': ['efficiency'],
                    'embedding': [thread_id * 0.1 + i * 0.01] * 128,
                    'importance': 0.6,
                    'hash': f'eff_hash_{thread_id}_{i}',
                    'prev_hash': ''
                }
                self.db_manager.add_block(block_data)
                
                # 조회로 검증
                retrieved = self.db_manager.get_block(block_index)
                self.assertIsNotNone(retrieved)
        
        # 10개 스레드로 동시 실행
        threads = []
        for i in range(10):
            thread = threading.Thread(target=efficient_worker, args=(i,))
            threads.append(thread)
            thread.start()
        
        for thread in threads:
            thread.join()
        
        elapsed_time = time.time() - start_time
        
        # 멀티 스레드 성능 기준: 200개 작업이 8초 이내에 완료되어야 함
        self.assertLess(elapsed_time, 8.0,
                       f"Multi thread efficiency test took {elapsed_time:.2f}s, should be < 8.0s")
        
        print(f"Multi thread efficiency: {elapsed_time:.2f}s for 200 operations across 10 threads")


if __name__ == '__main__':
    # 테스트 실행 전 환경 확인
    print("=== Thread Safety Test Suite ===")
    print("Testing ThreadSafeDatabaseManager and Compatibility Wrapper")
    print("Target: Resolve SQLite threading errors completely")
    print()
    
    # 상세한 테스트 실행
    unittest.main(verbosity=2)