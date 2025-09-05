#!/usr/bin/env python3
"""
Phase 1+2 통합 성능 검증 테스트

Phase 1: 캐시 최적화
Phase 2: 하이브리드 STM
통합 효과를 측정하고 실제 사용 시나리오를 검증
"""

import time
import json
import threading
import gc
import os
import sys
import logging
import resource
import tracemalloc
from typing import Dict, List, Tuple, Any
from datetime import datetime
from pathlib import Path

# 프로젝트 루트 추가
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from greeum.core.block_manager import BlockManager
from greeum.core.stm_manager import STMManager  
from greeum.core.cache_manager import CacheManager
from greeum.core.prompt_wrapper import PromptWrapper
from greeum.core.database_manager import DatabaseManager
from greeum.text_utils import process_user_input
from greeum.embedding_models import get_embedding

class IntegratedPerformanceTest:
    """Phase 1+2 통합 성능 테스트"""
    
    def __init__(self):
        self.logger = self._setup_logger()
        self.results = {}
        self.memory_usage = []
        
        # 메모리 추적 시작
        tracemalloc.start()
        
        # 테스트 데이터
        self.test_memories = self._generate_test_memories()
        self.test_queries = self._generate_test_queries()
        
    def _setup_logger(self):
        """로거 설정"""
        logger = logging.getLogger('integrated_performance')
        logger.setLevel(logging.INFO)
        
        # 파일 핸들러
        log_file = f"tests/performance_suite/results/integrated_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        fh = logging.FileHandler(log_file)
        fh.setLevel(logging.INFO)
        
        # 포맷터
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        fh.setFormatter(formatter)
        logger.addHandler(fh)
        
        return logger
    
    def _generate_test_memories(self) -> List[str]:
        """테스트용 메모리 데이터 생성"""
        memories = []
        
        # 일반적인 대화 패턴
        conversation_memories = [
            "오늘 새로운 프로젝트를 시작했습니다. 정말 흥미로운 도전이 될 것 같아요.",
            "Python 프로그래밍에 대해 공부하고 있습니다. 특히 비동기 프로그래밍이 어렵네요.",
            "최근에 읽은 책이 매우 인상깊었습니다. 특히 2장이 기억에 남아요.",
            "내일 중요한 미팅이 있어서 준비를 해야 합니다.",
            "머신러닝 모델의 성능을 개선하는 방법에 대해 연구하고 있습니다.",
        ]
        
        # 대용량 데이터 생성
        for i in range(2000):
            if i < len(conversation_memories):
                memories.append(f"{conversation_memories[i]} (반복 {i})")
            else:
                memories.append(f"테스트 메모리 항목 {i}: 이것은 성능 테스트를 위한 샘플 데이터입니다. "
                              f"다양한 키워드와 패턴을 포함하여 검색 성능을 측정합니다.")
        
        return memories
    
    def _generate_test_queries(self) -> List[str]:
        """테스트용 쿼리 생성"""
        return [
            "프로젝트 관련 내용",
            "Python 프로그래밍",
            "머신러닝 모델",
            "책 추천",
            "미팅 준비",
            "성능 최적화",
            "데이터 분석",
            "개발 도구",
            "학습 계획",
            "기술 트렌드"
        ]
    
    def _monitor_memory_usage(self):
        """메모리 사용량 모니터링"""
        try:
            # resource 모듈을 사용한 메모리 정보
            memory_info = resource.getrusage(resource.RUSAGE_SELF)
            
            # tracemalloc을 사용한 Python 메모리 추적
            current_memory, peak_memory = tracemalloc.get_traced_memory()
            
            self.memory_usage.append({
                'timestamp': datetime.now().isoformat(),
                'max_rss_mb': memory_info.ru_maxrss / 1024 / 1024,  # macOS에서는 바이트 단위
                'current_memory_mb': current_memory / 1024 / 1024,
                'peak_memory_mb': peak_memory / 1024 / 1024,
                'gc_count': sum(gc.get_count()),
                'user_time': memory_info.ru_utime,
                'system_time': memory_info.ru_stime
            })
        except Exception as e:
            self.logger.error(f"메모리 모니터링 오류: {e}")
    
    def test_baseline_performance(self) -> Dict[str, Any]:
        """기준 성능 측정 (Phase 1+2 비활성화)"""
        self.logger.info("기준 성능 측정 시작")
        
        # 임시 환경 설정 (캐시 비활성화)
        os.environ['GREEUM_CACHE_ENABLED'] = 'false'
        os.environ['GREEUM_STM_HYBRID'] = 'false'
        
        try:
            # 임시 데이터베이스 사용
            import tempfile
            temp_db = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
            temp_db.close()
            
            db_manager = DatabaseManager(connection_string=temp_db.name)
            block_manager = BlockManager(db_manager)
            
            # 테스트 데이터 추가
            start_time = time.time()
            for i, memory in enumerate(self.test_memories[:100]):
                # 텍스트 처리 및 임베딩 생성
                processed = process_user_input(memory)
                keywords = processed.get('keywords', [])
                tags = processed.get('tags', [])
                embedding = get_embedding(memory, model_name='simple')
                
                block_manager.add_block(
                    context=memory,
                    keywords=keywords,
                    tags=tags,
                    embedding=embedding,
                    importance=0.5
                )
                if i % 100 == 0:
                    self._monitor_memory_usage()
            
            add_time = time.time() - start_time
            
            # 검색 성능 측정
            search_times = []
            for query in self.test_queries:
                processed_query = process_user_input(query)
                keywords = processed_query.get('keywords', [])
                
                start_time = time.time()
                results = block_manager.search_by_keywords(keywords, limit=10)
                search_time = time.time() - start_time
                search_times.append(search_time)
                self._monitor_memory_usage()
            
            baseline_results = {
                'add_time': add_time,
                'avg_search_time': sum(search_times) / len(search_times),
                'total_searches': len(search_times),
                'memory_count': 100
            }
            
            self.logger.info(f"기준 성능: {baseline_results}")
            return baseline_results
            
        finally:
            # 환경 변수 복원
            os.environ.pop('GREEUM_CACHE_ENABLED', None)
            os.environ.pop('GREEUM_STM_HYBRID', None)
            # 임시 데이터베이스 정리
            try:
                os.unlink(temp_db.name)
            except:
                pass
    
    def test_integrated_performance(self) -> Dict[str, Any]:
        """통합 성능 측정 (Phase 1+2 활성화)"""
        self.logger.info("통합 성능 측정 시작")
        
        # Phase 1+2 활성화
        os.environ['GREEUM_CACHE_ENABLED'] = 'true'
        os.environ['GREEUM_STM_HYBRID'] = 'true'
        
        try:
            # 임시 데이터베이스 사용
            import tempfile
            temp_db = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
            temp_db.close()
            
            db_manager = DatabaseManager(connection_string=temp_db.name)
            block_manager = BlockManager(db_manager)
            stm_manager = STMManager(db_manager)
            cache_manager = CacheManager()
            
            # 테스트 데이터 추가
            start_time = time.time()
            for i, memory in enumerate(self.test_memories[:100]):
                # 텍스트 처리 및 임베딩 생성
                processed = process_user_input(memory)
                keywords = processed.get('keywords', [])
                tags = processed.get('tags', [])
                embedding = get_embedding(memory, model_name='simple')
                
                # LTM에 추가
                block_manager.add_block(
                    context=memory,
                    keywords=keywords,
                    tags=tags,
                    embedding=embedding,
                    importance=0.5
                )
                
                # STM에도 추가 (최근 100개)
                if i >= 900:
                    stm_manager.add_memory({
                    'content': memory,
                    'importance': 0.7,
                    'ttl': '1h'
                })
                
                if i % 100 == 0:
                    self._monitor_memory_usage()
            
            add_time = time.time() - start_time
            
            # 검색 성능 측정
            search_times = []
            cache_hits = 0
            stm_hits = 0
            
            for query in self.test_queries * 10:  # 10배 반복으로 캐시 효과 측정
                processed_query = process_user_input(query)
                keywords = processed_query.get('keywords', [])
                
                start_time = time.time()
                
                # STM 검색 먼저 (최근 메모리 조회)
                stm_results = stm_manager.get_recent_memories(count=5)
                if stm_results:
                    stm_hits += 1
                
                # 캐시 검색 (waypoints 조회)
                cache_results = cache_manager.get_waypoints()
                if cache_results:
                    cache_hits += 1
                
                # LTM 검색
                ltm_results = block_manager.search_by_keywords(keywords, limit=10)
                
                search_time = time.time() - start_time
                search_times.append(search_time)
                
                if len(search_times) % 20 == 0:
                    self._monitor_memory_usage()
            
            integrated_results = {
                'add_time': add_time,
                'avg_search_time': sum(search_times) / len(search_times),
                'total_searches': len(search_times),
                'memory_count': 100,
                'cache_hits': cache_hits,
                'stm_hits': stm_hits,
                'cache_hit_rate': cache_hits / len(search_times),
                'stm_hit_rate': stm_hits / len(search_times)
            }
            
            self.logger.info(f"통합 성능: {integrated_results}")
            return integrated_results
            
        finally:
            os.environ.pop('GREEUM_CACHE_ENABLED', None)
            os.environ.pop('GREEUM_STM_HYBRID', None)
            # 임시 데이터베이스 정리
            try:
                os.unlink(temp_db.name)
            except:
                pass
    
    def test_conversation_scenario(self) -> Dict[str, Any]:
        """대화형 AI 시나리오 테스트"""
        self.logger.info("대화형 AI 시나리오 테스트 시작")
        
        # 통합 시스템 설정
        os.environ['GREEUM_CACHE_ENABLED'] = 'true'
        os.environ['GREEUM_STM_HYBRID'] = 'true'
        
        try:
            db_manager = DatabaseManager()
            block_manager = BlockManager(db_manager)
            stm_manager = STMManager(db_manager)
            
            # 100회 연속 대화 시뮬레이션
            conversation_times = []
            prompt_enhancement_times = []
            
            for i in range(100):
                # 사용자 입력 시뮬레이션
                user_input = f"대화 턴 {i}: {self.test_queries[i % len(self.test_queries)]}에 대해 설명해주세요."
                
                # 메모리에 추가
                start_time = time.time()
                
                processed = process_user_input(user_input)
                keywords = processed.get('keywords', [])
                tags = processed.get('tags', [])
                embedding = get_embedding(user_input, model_name='simple')
                
                block_manager.add_block(
                    context=user_input,
                    keywords=keywords,
                    tags=tags,
                    embedding=embedding,
                    importance=0.6
                )
                stm_manager.add_memory({
                    'content': user_input,
                    'importance': 0.8,
                    'ttl': '30m'
                })
                add_time = time.time() - start_time
                
                # 프롬프트 강화 (간단한 시뮬레이션)
                start_time = time.time()
                # 최근 메모리 조회로 프롬프트 강화 시뮬레이션
                recent_memories = stm_manager.get_recent_memories(count=3)
                enhancement_time = time.time() - start_time
                
                conversation_times.append(add_time)
                prompt_enhancement_times.append(enhancement_time)
                
                if i % 10 == 0:
                    self._monitor_memory_usage()
                    gc.collect()  # 가비지 컬렉션 강제 실행
            
            scenario_results = {
                'total_turns': 100,
                'avg_add_time': sum(conversation_times) / len(conversation_times),
                'avg_enhancement_time': sum(prompt_enhancement_times) / len(prompt_enhancement_times),
                'total_conversation_time': sum(conversation_times) + sum(prompt_enhancement_times),
                'memory_growth': len(self.memory_usage)
            }
            
            self.logger.info(f"대화형 시나리오 결과: {scenario_results}")
            return scenario_results
            
        finally:
            os.environ.pop('GREEUM_CACHE_ENABLED', None)
            os.environ.pop('GREEUM_STM_HYBRID', None)
    
    def test_large_document_scenario(self) -> Dict[str, Any]:
        """대용량 문서 분석 시나리오"""
        self.logger.info("대용량 문서 분석 시나리오 테스트 시작")
        
        # 큰 문서 시뮬레이션 (10,000자)
        large_document = "이것은 대용량 문서입니다. " * 500 + \
                        "중요한 정보가 포함되어 있습니다. " * 200 + \
                        "성능 테스트를 위한 데이터입니다. " * 300
        
        os.environ['GREEUM_CACHE_ENABLED'] = 'true'
        os.environ['GREEUM_STM_HYBRID'] = 'true'
        
        try:
            db_manager = DatabaseManager()
            block_manager = BlockManager(db_manager)
            
            # 대용량 문서 처리
            start_time = time.time()
            
            # 문서를 청크로 분할하여 저장
            chunk_size = 500
            chunks = [large_document[i:i+chunk_size] 
                     for i in range(0, len(large_document), chunk_size)]
            
            chunk_times = []
            for i, chunk in enumerate(chunks):
                chunk_start = time.time()
                
                chunk_content = f"문서 청크 {i}: {chunk}"
                processed = process_user_input(chunk_content)
                keywords = processed.get('keywords', [])
                tags = processed.get('tags', [])
                embedding = get_embedding(chunk_content, model_name='simple')
                
                block_manager.add_block(
                    context=chunk_content,
                    keywords=keywords,
                    tags=tags,
                    embedding=embedding,
                    importance=0.7
                )
                chunk_time = time.time() - chunk_start
                chunk_times.append(chunk_time)
                
                if i % 5 == 0:
                    self._monitor_memory_usage()
            
            total_processing_time = time.time() - start_time
            
            # 문서 검색 테스트
            search_queries = ["중요한 정보", "성능 테스트", "대용량 문서", "데이터"]
            search_times = []
            
            for query in search_queries:
                processed_query = process_user_input(query)
                keywords = processed_query.get('keywords', [])
                
                start_time = time.time()
                results = block_manager.search_by_keywords(keywords, limit=10)
                search_time = time.time() - start_time
                search_times.append(search_time)
            
            document_results = {
                'document_size': len(large_document),
                'chunk_count': len(chunks),
                'total_processing_time': total_processing_time,
                'avg_chunk_time': sum(chunk_times) / len(chunk_times),
                'avg_search_time': sum(search_times) / len(search_times),
                'search_queries': len(search_queries)
            }
            
            self.logger.info(f"대용량 문서 시나리오 결과: {document_results}")
            return document_results
            
        finally:
            os.environ.pop('GREEUM_CACHE_ENABLED', None)
            os.environ.pop('GREEUM_STM_HYBRID', None)
    
    def test_concurrent_access(self) -> Dict[str, Any]:
        """동시 접근 테스트"""
        self.logger.info("동시 접근 테스트 시작")
        
        results = {'threads': [], 'errors': []}
        
        def worker_thread(thread_id: int, operation_count: int):
            """워커 스레드"""
            try:
                db_manager = DatabaseManager()
                block_manager = BlockManager(db_manager)
                
                thread_results = {
                    'thread_id': thread_id,
                    'operations': 0,
                    'total_time': 0,
                    'errors': 0
                }
                
                start_time = time.time()
                
                for i in range(operation_count):
                    try:
                        # 메모리 추가
                        content = f"스레드 {thread_id} 작업 {i}: 동시성 테스트"
                        processed = process_user_input(content)
                        keywords = processed.get('keywords', [])
                        tags = processed.get('tags', [])
                        embedding = get_embedding(content, model_name='simple')
                        
                        block_manager.add_block(
                            context=content,
                            keywords=keywords,
                            tags=tags,
                            embedding=embedding,
                            importance=0.5
                        )
                        
                        # 검색
                        search_keywords = [f"스레드", f"{thread_id}"]
                        block_manager.search_by_keywords(search_keywords, limit=5)
                        
                        thread_results['operations'] += 1
                        
                    except Exception as e:
                        thread_results['errors'] += 1
                        self.logger.error(f"스레드 {thread_id} 오류: {e}")
                
                thread_results['total_time'] = time.time() - start_time
                results['threads'].append(thread_results)
                
            except Exception as e:
                results['errors'].append(f"스레드 {thread_id}: {str(e)}")
        
        # 5개 스레드로 동시 실행
        threads = []
        for i in range(5):
            thread = threading.Thread(target=worker_thread, args=(i, 20))
            threads.append(thread)
            thread.start()
        
        # 모든 스레드 완료 대기
        for thread in threads:
            thread.join()
        
        # 결과 집계
        total_operations = sum(t['operations'] for t in results['threads'])
        total_errors = sum(t['errors'] for t in results['threads'])
        avg_time = sum(t['total_time'] for t in results['threads']) / len(results['threads'])
        
        concurrent_results = {
            'thread_count': 5,
            'total_operations': total_operations,
            'total_errors': total_errors,
            'error_rate': total_errors / (total_operations + total_errors) if (total_operations + total_errors) > 0 else 0,
            'avg_thread_time': avg_time,
            'threads_detail': results['threads']
        }
        
        self.logger.info(f"동시 접근 테스트 결과: {concurrent_results}")
        return concurrent_results
    
    def test_edge_cases(self) -> Dict[str, Any]:
        """에지 케이스 테스트"""
        self.logger.info("에지 케이스 테스트 시작")
        
        edge_results = {}
        
        try:
            db_manager = DatabaseManager()
            block_manager = BlockManager(db_manager)
            
            # 1. 빈 메모리 상태에서 검색
            start_time = time.time()
            empty_results = block_manager.search_by_keywords(["존재하지않는"], limit=10)
            empty_search_time = time.time() - start_time
            edge_results['empty_search'] = {
                'time': empty_search_time,
                'results_count': len(empty_results)
            }
            
            # 2. 매우 긴 텍스트 처리
            very_long_text = "매우 긴 텍스트입니다. " * 2000  # 약 20,000자
            start_time = time.time()
            
            processed = process_user_input(very_long_text)
            keywords = processed.get('keywords', [])
            tags = processed.get('tags', [])
            embedding = get_embedding(very_long_text, model_name='simple')
            
            block_manager.add_block(
                context=very_long_text,
                keywords=keywords,
                tags=tags,
                embedding=embedding,
                importance=0.5
            )
            long_text_time = time.time() - start_time
            edge_results['long_text'] = {
                'text_length': len(very_long_text),
                'processing_time': long_text_time
            }
            
            # 3. 특수 문자 및 유니코드 처리
            special_texts = [
                "특수문자 테스트: !@#$%^&*()_+-=[]{}|;':\",./<>?",
                "한글 테스트: 안녕하세요. 한국어 처리가 잘 되나요?",
                "Japanese: こんにちは。日本語も処理できますか？",
                "Emoji: 😀😃😄😁😆😅😂🤣😊😇🙂🙃😉😌😍🥰😘",
                "Mixed: Hello 안녕 こんにちは 😀 !@#$%"
            ]
            
            special_times = []
            for text in special_texts:
                start_time = time.time()
                
                processed = process_user_input(text)
                keywords = processed.get('keywords', [])
                tags = processed.get('tags', [])
                embedding = get_embedding(text, model_name='simple')
                
                block_manager.add_block(
                    context=text,
                    keywords=keywords,
                    tags=tags,
                    embedding=embedding,
                    importance=0.5
                )
                processing_time = time.time() - start_time
                special_times.append(processing_time)
            
            edge_results['special_characters'] = {
                'test_count': len(special_texts),
                'avg_processing_time': sum(special_times) / len(special_times),
                'max_processing_time': max(special_times)
            }
            
            # 4. 매우 높은 중요도와 낮은 중요도
            extreme_importance_times = []
            for importance in [0.0, 0.1, 0.9, 1.0]:
                start_time = time.time()
                
                content = f"중요도 {importance} 테스트"
                processed = process_user_input(content)
                keywords = processed.get('keywords', [])
                tags = processed.get('tags', [])
                embedding = get_embedding(content, model_name='simple')
                
                block_manager.add_block(
                    context=content,
                    keywords=keywords,
                    tags=tags,
                    embedding=embedding,
                    importance=importance
                )
                processing_time = time.time() - start_time
                extreme_importance_times.append(processing_time)
            
            edge_results['extreme_importance'] = {
                'test_count': len(extreme_importance_times),
                'avg_processing_time': sum(extreme_importance_times) / len(extreme_importance_times)
            }
            
            self.logger.info(f"에지 케이스 테스트 결과: {edge_results}")
            return edge_results
            
        except Exception as e:
            self.logger.error(f"에지 케이스 테스트 오류: {e}")
            edge_results['error'] = str(e)
            return edge_results
    
    def analyze_memory_leaks(self) -> Dict[str, Any]:
        """메모리 누수 분석"""
        self.logger.info("메모리 누수 분석 시작")
        
        if not self.memory_usage:
            return {'error': '메모리 사용량 데이터 없음'}
        
        # 메모리 사용량 추세 분석
        initial_memory = self.memory_usage[0]['current_memory_mb']
        final_memory = self.memory_usage[-1]['current_memory_mb']
        peak_memory = max(usage['peak_memory_mb'] for usage in self.memory_usage)
        max_rss = max(usage['max_rss_mb'] for usage in self.memory_usage)
        
        memory_growth = final_memory - initial_memory
        memory_growth_rate = memory_growth / len(self.memory_usage)
        
        # CPU 시간 분석
        initial_user_time = self.memory_usage[0]['user_time']
        final_user_time = self.memory_usage[-1]['user_time']
        total_cpu_time = final_user_time - initial_user_time
        
        # 가비지 컬렉션 분석
        initial_gc = self.memory_usage[0]['gc_count']
        final_gc = self.memory_usage[-1]['gc_count']
        gc_activity = final_gc - initial_gc
        
        leak_analysis = {
            'initial_memory_mb': initial_memory,
            'final_memory_mb': final_memory,
            'peak_memory_mb': peak_memory,
            'max_rss_mb': max_rss,
            'memory_growth_mb': memory_growth,
            'memory_growth_rate_mb_per_sample': memory_growth_rate,
            'total_cpu_time_seconds': total_cpu_time,
            'gc_activity': gc_activity,
            'sample_count': len(self.memory_usage),
            'leak_detected': memory_growth > 50,  # 50MB 이상 증가시 누수 의심
            'memory_efficiency': 'GOOD' if memory_growth < 10 else 'MODERATE' if memory_growth < 50 else 'POOR'
        }
        
        self.logger.info(f"메모리 누수 분석 결과: {leak_analysis}")
        return leak_analysis
    
    def run_comprehensive_test(self) -> Dict[str, Any]:
        """종합 테스트 실행"""
        self.logger.info("=== Phase 1+2 통합 성능 검증 시작 ===")
        
        comprehensive_results = {
            'test_start_time': datetime.now().isoformat(),
            'greeum_version': '2.0.5',
            'test_type': 'Phase 1+2 Integration Performance Test'
        }
        
        try:
            # 1. 기준 성능 측정
            self.logger.info("1. 기준 성능 측정")
            comprehensive_results['baseline'] = self.test_baseline_performance()
            
            # 메모리 정리
            gc.collect()
            time.sleep(1)
            
            # 2. 통합 성능 측정
            self.logger.info("2. 통합 성능 측정")
            comprehensive_results['integrated'] = self.test_integrated_performance()
            
            # 3. 실제 사용 시나리오 테스트
            self.logger.info("3. 대화형 AI 시나리오")
            comprehensive_results['conversation_scenario'] = self.test_conversation_scenario()
            
            self.logger.info("4. 대용량 문서 시나리오")
            comprehensive_results['document_scenario'] = self.test_large_document_scenario()
            
            # 4. 동시성 테스트
            self.logger.info("5. 동시 접근 테스트")
            comprehensive_results['concurrent_access'] = self.test_concurrent_access()
            
            # 5. 에지 케이스 테스트
            self.logger.info("6. 에지 케이스 테스트")
            comprehensive_results['edge_cases'] = self.test_edge_cases()
            
            # 6. 메모리 누수 분석
            self.logger.info("7. 메모리 누수 분석")
            comprehensive_results['memory_analysis'] = self.analyze_memory_leaks()
            
            # 성능 개선 효과 계산
            baseline_search = comprehensive_results['baseline']['avg_search_time']
            integrated_search = comprehensive_results['integrated']['avg_search_time']
            performance_improvement = baseline_search / integrated_search if integrated_search > 0 else 0
            
            comprehensive_results['performance_summary'] = {
                'baseline_search_time': baseline_search,
                'integrated_search_time': integrated_search,
                'performance_improvement_ratio': performance_improvement,
                'cache_hit_rate': comprehensive_results['integrated'].get('cache_hit_rate', 0),
                'stm_hit_rate': comprehensive_results['integrated'].get('stm_hit_rate', 0)
            }
            
            comprehensive_results['test_end_time'] = datetime.now().isoformat()
            self.logger.info("=== 통합 성능 검증 완료 ===")
            
            return comprehensive_results
            
        except Exception as e:
            self.logger.error(f"종합 테스트 실행 중 오류: {e}")
            comprehensive_results['error'] = str(e)
            comprehensive_results['test_end_time'] = datetime.now().isoformat()
            return comprehensive_results

def main():
    """메인 실행 함수"""
    test = IntegratedPerformanceTest()
    results = test.run_comprehensive_test()
    
    # 결과 저장
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    result_file = f"tests/performance_suite/results/integrated_performance_test_{timestamp}.json"
    
    os.makedirs(os.path.dirname(result_file), exist_ok=True)
    
    with open(result_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    # 간단한 리포트 출력
    print("\n=== Phase 1+2 통합 성능 검증 결과 ===")
    
    if 'performance_summary' in results:
        summary = results['performance_summary']
        print(f"기준 검색 시간: {summary['baseline_search_time']:.4f}초")
        print(f"통합 검색 시간: {summary['integrated_search_time']:.4f}초")
        print(f"성능 개선 비율: {summary['performance_improvement_ratio']:.2f}배")
        print(f"캐시 적중률: {summary['cache_hit_rate']:.1%}")
        print(f"STM 적중률: {summary['stm_hit_rate']:.1%}")
    
    if 'memory_analysis' in results:
        memory = results['memory_analysis']
        print(f"메모리 효율성: {memory.get('memory_efficiency', 'UNKNOWN')}")
        print(f"메모리 누수 감지: {'예' if memory.get('leak_detected', False) else '아니오'}")
    
    print(f"\n상세 결과 저장: {result_file}")
    
    return results

if __name__ == "__main__":
    main()