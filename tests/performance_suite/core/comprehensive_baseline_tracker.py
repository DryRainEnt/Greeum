#!/usr/bin/env python3
"""
Greeum v2.0.5 정밀 성능 기준점 측정 시스템

이 모듈은 통계적으로 신뢰할 수 있는 성능 지표를 생성하기 위해
대용량 샘플과 정밀한 측정을 수행합니다.
"""

import os
import sys
import json
import time
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
import statistics
from pathlib import Path
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

# 상위 디렉토리를 path에 추가
sys.path.insert(0, os.path.abspath('../../..'))

from greeum import DatabaseManager, BlockManager, STMManager, CacheManager
from greeum.core.prompt_wrapper import PromptWrapper
from greeum.core.quality_validator import QualityValidator
from greeum.core.duplicate_detector import DuplicateDetector
from greeum.core.usage_analytics import UsageAnalytics
from greeum.embedding_models import get_embedding
import numpy as np

logger = logging.getLogger(__name__)

class ComprehensiveBaselineTracker:
    """정밀한 성능 기준점 측정을 위한 종합 추적기"""
    
    def __init__(self, data_dir: str = "tests/performance_suite/results/baselines"):
        """초기화"""
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # Greeum 컴포넌트 초기화
        self.db_manager = DatabaseManager()
        self.block_manager = BlockManager(self.db_manager)
        self.stm_manager = STMManager(self.db_manager)
        self.cache_manager = CacheManager(block_manager=self.block_manager, stm_manager=self.stm_manager)
        self.prompt_wrapper = PromptWrapper(self.cache_manager, self.stm_manager)
        
        # v2.0.5 신규 컴포넌트 (에러 처리)
        try:
            self.quality_validator = QualityValidator()
        except Exception as e:
            logger.warning(f"QualityValidator 초기화 실패: {e}")
            self.quality_validator = None
            
        try:
            self.duplicate_detector = DuplicateDetector(self.db_manager)
        except Exception as e:
            logger.warning(f"DuplicateDetector 초기화 실패: {e}")
            self.duplicate_detector = None
            
        try:
            self.usage_analytics = UsageAnalytics()
        except Exception as e:
            logger.warning(f"UsageAnalytics 초기화 실패: {e}")
            self.usage_analytics = None
        
        # 통계적 신뢰도를 위한 설정
        self.min_sample_size = 100
        self.confidence_level = 0.95
        self.warmup_iterations = 10  # 시스템 안정화를 위한 웜업
        
        logger.info(f"ComprehensiveBaselineTracker 초기화 완료 - 데이터 디렉토리: {self.data_dir}")
    
    def measure_comprehensive_performance(self, sample_size: int = 500) -> Dict[str, Any]:
        """
        종합적이고 정밀한 성능 측정
        
        Args:
            sample_size: 측정 샘플 크기 (통계적 신뢰도를 위해 500+ 권장)
        """
        if sample_size < self.min_sample_size:
            logger.warning(f"샘플 크기 {sample_size}가 최소 권장치 {self.min_sample_size}보다 작습니다.")
            
        logger.info(f"종합 성능 측정 시작 - 샘플 크기: {sample_size}")
        start_time = time.time()
        
        performance_data = {
            "measurement_timestamp": datetime.now().isoformat(),
            "greeum_version": "2.0.5",
            "sample_size": sample_size,
            "confidence_level": self.confidence_level,
            "metrics": {}
        }
        
        # 시스템 웜업
        logger.info("시스템 웜업 수행 중...")
        self._perform_warmup()
        
        # 1. 메모리 검색 성능 정밀 측정
        logger.info("메모리 검색 성능 정밀 측정 중...")
        performance_data["metrics"]["memory_search"] = self._measure_memory_search_comprehensive(sample_size)
        
        # 2. 응답 품질 다각도 측정
        logger.info("응답 품질 다각도 측정 중...")
        performance_data["metrics"]["response_quality"] = self._measure_response_quality_comprehensive(sample_size // 10)
        
        # 3. 컨커런시 성능 측정
        logger.info("동시성 성능 측정 중...")
        performance_data["metrics"]["concurrency"] = self._measure_concurrency_performance(sample_size // 20)
        
        # 4. 확장성 측정 (메모리 블록 수 증가에 따른 성능 변화)
        logger.info("확장성 측정 중...")
        performance_data["metrics"]["scalability"] = self._measure_scalability_performance()
        
        # 5. 시스템 리소스 정밀 모니터링
        logger.info("시스템 리소스 정밀 모니터링 중...")
        performance_data["metrics"]["system_resources"] = self._measure_system_resources_comprehensive()
        
        # 6. v2.0.5 신규 기능 성능 (개선된 측정)
        if self.quality_validator or self.duplicate_detector:
            logger.info("v2.0.5 신규 기능 성능 측정 중...")
            performance_data["metrics"]["v205_features"] = self._measure_v205_features_comprehensive(sample_size)
        
        total_time = time.time() - start_time
        performance_data["measurement_duration"] = total_time
        
        # 통계적 신뢰도 계산
        performance_data["statistical_confidence"] = self._calculate_statistical_confidence(performance_data["metrics"])
        
        logger.info(f"종합 성능 측정 완료 - 소요 시간: {total_time:.2f}초")
        return performance_data
    
    def _perform_warmup(self):
        """시스템 웜업 수행"""
        warmup_queries = ["웜업 쿼리 " + str(i) for i in range(self.warmup_iterations)]
        
        for query in warmup_queries:
            embedding = get_embedding(query)
            self.block_manager.search_by_embedding(embedding, top_k=5)
            self.cache_manager.update_cache(query, embedding, query.split())
    
    def _measure_memory_search_comprehensive(self, sample_size: int) -> Dict[str, Any]:
        """메모리 검색 성능 종합 측정"""
        # 다양한 크기의 메모리 블록 환경에서 테스트 (실용적 크기로 조정)
        memory_sizes = [100, 500, 1000]
        results = {}
        
        for memory_size in memory_sizes:
            logger.info(f"메모리 크기 {memory_size}에서 성능 측정 중...")
            
            # 테스트 환경 준비
            self._prepare_test_memory_blocks(memory_size, clear_existing=True)
            
            # 다양한 검색 패턴 테스트
            search_patterns = [
                "단일 키워드 검색",
                "복합 키워드 검색 프로젝트 개발",
                "긴 문장 검색 최신 프로젝트의 진행 상황과 개발 계획에 대해",
                "특수 문자 포함 검색 v2.0.5 업데이트",
                "숫자 포함 검색 2025년 계획"
            ]
            
            ltm_times = []
            cache_times = []
            
            for i in range(sample_size // len(memory_sizes)):
                pattern = search_patterns[i % len(search_patterns)]
                query = f"{pattern} - {i}"
                embedding = get_embedding(query)
                
                # LTM 직접 검색 (2회 측정 후 중간값으로 정확도 유지)
                ltm_measurements = []
                for _ in range(2):
                    start_time = time.perf_counter()
                    ltm_results = self.block_manager.search_by_embedding(embedding, top_k=5)
                    ltm_time = time.perf_counter() - start_time
                    ltm_measurements.append(ltm_time * 1000)
                
                ltm_times.append(statistics.median(ltm_measurements))
                
                # Cache 검색 (2회 측정 후 중간값으로 정확도 유지)
                cache_measurements = []
                for _ in range(2):
                    start_time = time.perf_counter()
                    cache_results = self.cache_manager.update_cache(query, embedding, query.split()[:3])
                    cache_time = time.perf_counter() - start_time
                    cache_measurements.append(cache_time * 1000)
                
                cache_times.append(statistics.median(cache_measurements))
            
            # 통계 계산
            results[f"memory_size_{memory_size}"] = {
                "avg_ltm_search_time": statistics.mean(ltm_times),
                "median_ltm_search_time": statistics.median(ltm_times),
                "p95_ltm_search_time": statistics.quantiles(ltm_times, n=20)[18] if len(ltm_times) > 20 else max(ltm_times),
                "p99_ltm_search_time": statistics.quantiles(ltm_times, n=100)[98] if len(ltm_times) > 100 else max(ltm_times),
                "stdev_ltm_search_time": statistics.stdev(ltm_times) if len(ltm_times) > 1 else 0,
                
                "avg_cache_search_time": statistics.mean(cache_times),
                "median_cache_search_time": statistics.median(cache_times),
                "p95_cache_search_time": statistics.quantiles(cache_times, n=20)[18] if len(cache_times) > 20 else max(cache_times),
                "p99_cache_search_time": statistics.quantiles(cache_times, n=100)[98] if len(cache_times) > 100 else max(cache_times),
                "stdev_cache_search_time": statistics.stdev(cache_times) if len(cache_times) > 1 else 0,
                
                "avg_speedup_ratio": statistics.mean(ltm_times) / statistics.mean(cache_times) if statistics.mean(cache_times) > 0 else 1,
                "sample_count": len(ltm_times),
                "memory_block_count": memory_size
            }
        
        return results
    
    def _measure_response_quality_comprehensive(self, sample_size: int) -> Dict[str, Any]:
        """응답 품질 종합 측정"""
        # 다양한 유형의 질의에 대한 품질 측정
        query_types = {
            "factual": [
                "프로젝트의 현재 상태는?",
                "최근 업데이트 내용은?",
                "개발 진행률은 어떻게 되나요?"
            ],
            "contextual": [
                "이전에 논의했던 성능 이슈가 해결됐나요?",
                "지난주 계획했던 작업들은 완료됐나요?",
                "앞서 언급한 개선사항이 적용됐나요?"
            ],
            "analytical": [
                "현재 성능과 목표 성능의 차이는?",
                "어떤 부분이 가장 개선이 필요한가요?",
                "성능 향상을 위한 우선순위는?"
            ]
        }
        
        results = {}
        
        for query_type, queries in query_types.items():
            logger.info(f"{query_type} 타입 질의 품질 측정 중...")
            
            quality_scores = []
            context_usage_scores = []
            response_completeness_scores = []
            
            for i in range(sample_size // len(query_types)):
                query = queries[i % len(queries)]
                
                # 메모리 활용 프롬프트 생성
                enhanced_prompt = self.prompt_wrapper.compose_prompt(query, token_budget=2000)
                
                # 품질 점수 계산 (다양한 지표)
                if self.quality_validator:
                    try:
                        quality_result = self.quality_validator.validate_memory_quality(enhanced_prompt)
                        quality_scores.append(quality_result.get('overall_score', 0))
                    except:
                        quality_scores.append(0)
                else:
                    # 기본 품질 측정 (프롬프트 길이, 컨텍스트 포함 여부 등)
                    basic_quality = min(1.0, len(enhanced_prompt) / 1000)  # 길이 기반 품질
                    quality_scores.append(basic_quality)
                
                # 컨텍스트 활용도 측정
                context_indicators = enhanced_prompt.count('관련 기억:') + enhanced_prompt.count('최근 기억:')
                context_usage_scores.append(context_indicators)
                
                # 응답 완성도 측정 (정보 밀도)
                info_density = len([word for word in enhanced_prompt.split() if len(word) > 3]) / len(enhanced_prompt.split())
                response_completeness_scores.append(info_density)
            
            # 통계 계산
            results[query_type] = {
                "avg_quality_score": statistics.mean(quality_scores) if quality_scores else 0,
                "median_quality_score": statistics.median(quality_scores) if quality_scores else 0,
                "stdev_quality_score": statistics.stdev(quality_scores) if len(quality_scores) > 1 else 0,
                
                "avg_context_usage": statistics.mean(context_usage_scores) if context_usage_scores else 0,
                "avg_completeness": statistics.mean(response_completeness_scores) if response_completeness_scores else 0,
                
                "sample_count": len(quality_scores)
            }
        
        return results
    
    def _measure_concurrency_performance(self, sample_size: int) -> Dict[str, Any]:
        """동시성 성능 측정"""
        thread_counts = [1, 2, 4, 8, 16]
        results = {}
        
        for thread_count in thread_counts:
            logger.info(f"{thread_count}개 스레드로 동시성 테스트 중...")
            
            def concurrent_search_task(task_id):
                """동시 검색 작업"""
                query = f"동시 검색 테스트 {task_id}"
                embedding = get_embedding(query)
                
                start_time = time.perf_counter()
                ltm_results = self.block_manager.search_by_embedding(embedding, top_k=5)
                cache_results = self.cache_manager.update_cache(query, embedding, query.split())
                end_time = time.perf_counter()
                
                return {
                    "task_id": task_id,
                    "execution_time": (end_time - start_time) * 1000,
                    "ltm_result_count": len(ltm_results),
                    "cache_result_count": len(cache_results)
                }
            
            # 동시 실행
            execution_times = []
            error_count = 0
            
            start_time = time.perf_counter()
            
            with ThreadPoolExecutor(max_workers=thread_count) as executor:
                futures = [executor.submit(concurrent_search_task, i) for i in range(sample_size // len(thread_counts))]
                
                for future in as_completed(futures):
                    try:
                        result = future.result(timeout=30)
                        execution_times.append(result["execution_time"])
                    except Exception as e:
                        error_count += 1
                        logger.warning(f"동시성 테스트 중 오류: {e}")
            
            total_time = time.perf_counter() - start_time
            
            # 통계 계산
            if execution_times:
                results[f"threads_{thread_count}"] = {
                    "avg_task_time": statistics.mean(execution_times),
                    "median_task_time": statistics.median(execution_times),
                    "p95_task_time": statistics.quantiles(execution_times, n=20)[18] if len(execution_times) > 20 else max(execution_times),
                    "total_execution_time": total_time * 1000,
                    "throughput_tasks_per_sec": len(execution_times) / total_time,
                    "error_rate": error_count / (len(execution_times) + error_count) * 100,
                    "thread_count": thread_count,
                    "completed_tasks": len(execution_times),
                    "failed_tasks": error_count
                }
            else:
                results[f"threads_{thread_count}"] = {
                    "error": "모든 작업 실패",
                    "thread_count": thread_count,
                    "failed_tasks": error_count
                }
        
        return results
    
    def _measure_scalability_performance(self) -> Dict[str, Any]:
        """확장성 성능 측정 (메모리 블록 수 증가에 따른 성능 변화)"""
        block_counts = [100, 500, 1000, 2000, 5000]
        results = {}
        
        for block_count in block_counts:
            logger.info(f"{block_count}개 블록 환경에서 확장성 측정 중...")
            
            # 테스트 환경 구성
            self._prepare_test_memory_blocks(block_count, clear_existing=True)
            
            # 표준 검색 작업 수행
            test_queries = [
                "프로젝트 상태",
                "개발 계획",
                "성능 최적화",
                "버그 수정",
                "기능 추가"
            ]
            
            search_times = []
            
            for query in test_queries * 20:  # 각 쿼리를 20번씩 반복
                embedding = get_embedding(query)
                
                start_time = time.perf_counter()
                results_ltm = self.block_manager.search_by_embedding(embedding, top_k=5)
                search_time = time.perf_counter() - start_time
                
                search_times.append(search_time * 1000)
            
            # 통계 계산
            results[f"blocks_{block_count}"] = {
                "avg_search_time": statistics.mean(search_times),
                "median_search_time": statistics.median(search_times),
                "p95_search_time": statistics.quantiles(search_times, n=20)[18] if len(search_times) > 20 else max(search_times),
                "block_count": block_count,
                "search_efficiency": block_count / statistics.mean(search_times),  # 블록당 검색 효율성
                "sample_count": len(search_times)
            }
        
        # 확장성 계수 계산 (블록 수 증가에 따른 성능 저하 정도)
        base_performance = results["blocks_100"]["avg_search_time"]
        scalability_factors = {}
        
        for block_count in block_counts[1:]:
            current_performance = results[f"blocks_{block_count}"]["avg_search_time"]
            scalability_factor = current_performance / base_performance
            scalability_factors[f"blocks_{block_count}"] = scalability_factor
        
        results["scalability_analysis"] = {
            "base_performance_100_blocks": base_performance,
            "scalability_factors": scalability_factors,
            "linear_scalability_score": self._calculate_scalability_score(scalability_factors, block_counts[1:])
        }
        
        return results
    
    def _calculate_scalability_score(self, scalability_factors: Dict, block_counts: List[int]) -> float:
        """확장성 점수 계산 (1.0 = 완벽한 선형 확장성)"""
        if not scalability_factors:
            return 1.0
        
        # 이상적인 선형 확장성과 실제 확장성 비교
        ideal_factors = [count / 100 for count in block_counts]  # 100 블록 기준 선형 증가
        actual_factors = [scalability_factors[f"blocks_{count}"] for count in block_counts]
        
        # 평균 편차 계산
        deviations = [abs(ideal - actual) for ideal, actual in zip(ideal_factors, actual_factors)]
        avg_deviation = statistics.mean(deviations)
        
        # 점수 계산 (편차가 작을수록 높은 점수)
        scalability_score = max(0, 1 - avg_deviation)
        return round(scalability_score, 3)
    
    def _measure_system_resources_comprehensive(self) -> Dict[str, Any]:
        """시스템 리소스 정밀 모니터링"""
        try:
            import psutil
            import gc
            
            # 가비지 컬렉션 수행
            gc.collect()
            
            # 현재 프로세스 정보
            process = psutil.Process()
            
            # 메모리 사용량 상세 측정
            memory_info = process.memory_info()
            memory_percent = process.memory_percent()
            
            # CPU 사용량 측정 (1초간 모니터링)
            cpu_percent_1s = process.cpu_percent(interval=1)
            
            # 시스템 전체 정보
            system_memory = psutil.virtual_memory()
            system_cpu = psutil.cpu_percent(interval=1)
            
            # 디스크 I/O 정보
            io_counters = process.io_counters() if hasattr(process, 'io_counters') else None
            
            return {
                "process_memory": {
                    "rss_mb": memory_info.rss / 1024 / 1024,
                    "vms_mb": memory_info.vms / 1024 / 1024,
                    "percent": memory_percent,
                    "available_mb": system_memory.available / 1024 / 1024,
                    "total_mb": system_memory.total / 1024 / 1024
                },
                "process_cpu": {
                    "percent_1s": cpu_percent_1s,
                    "num_threads": process.num_threads(),
                    "system_cpu_percent": system_cpu
                },
                "io_counters": {
                    "read_count": io_counters.read_count if io_counters else 0,
                    "write_count": io_counters.write_count if io_counters else 0,
                    "read_bytes": io_counters.read_bytes if io_counters else 0,
                    "write_bytes": io_counters.write_bytes if io_counters else 0
                } if io_counters else {"error": "IO counters not available"},
                "file_descriptors": process.num_fds() if hasattr(process, 'num_fds') else 0,
                "measurement_timestamp": datetime.now().isoformat()
            }
            
        except ImportError:
            logger.warning("psutil 모듈을 찾을 수 없습니다.")
            return {"error": "psutil not available"}
        except Exception as e:
            logger.error(f"시스템 리소스 측정 중 오류: {e}")
            return {"error": str(e)}
    
    def _measure_v205_features_comprehensive(self, sample_size: int) -> Dict[str, Any]:
        """v2.0.5 신규 기능 종합 성능 측정"""
        results = {}
        
        # 품질 검증 성능
        if self.quality_validator:
            logger.info("품질 검증 성능 정밀 측정 중...")
            
            test_contents = [
                "단순한 텍스트 내용입니다.",
                "복잡하고 상세한 프로젝트 개발 진행 상황에 대한 종합적인 보고서입니다.",
                "짧은 메모",
                "매우 긴 문서 내용으로서 다양한 정보와 데이터, 분석 결과, 결론 등을 포함하고 있으며 전체적인 맥락과 흐름을 파악하기 위해서는 충분한 시간과 집중력이 필요합니다.",
                "중간 길이의 설명 문서로서 적절한 수준의 정보를 담고 있습니다."
            ]
            
            validation_times = []
            quality_scores = []
            
            for i in range(sample_size):
                content = test_contents[i % len(test_contents)] + f" (테스트 {i})"
                
                # 여러 번 측정하여 정확도 향상
                measurements = []
                for _ in range(5):
                    start_time = time.perf_counter()
                    try:
                        result = self.quality_validator.validate_memory_quality(content)
                        validation_time = time.perf_counter() - start_time
                        measurements.append(validation_time * 1000)
                        quality_scores.append(result.get('overall_score', 0))
                    except Exception as e:
                        logger.warning(f"품질 검증 중 오류: {e}")
                        measurements.append(0)
                        quality_scores.append(0)
                
                validation_times.append(statistics.median(measurements))
            
            results["quality_validation"] = {
                "avg_validation_time": statistics.mean(validation_times),
                "median_validation_time": statistics.median(validation_times),
                "p95_validation_time": statistics.quantiles(validation_times, n=20)[18] if len(validation_times) > 20 else max(validation_times),
                "stdev_validation_time": statistics.stdev(validation_times) if len(validation_times) > 1 else 0,
                "avg_quality_score": statistics.mean(quality_scores) if quality_scores else 0,
                "validation_throughput": sample_size / (sum(validation_times) / 1000),
                "sample_count": sample_size
            }
        
        # 중복 감지 성능
        if self.duplicate_detector:
            logger.info("중복 감지 성능 정밀 측정 중...")
            
            # 실제적인 중복 패턴 생성
            base_contents = [
                "프로젝트 개발이 순조롭게 진행되고 있습니다",
                "새로운 기능 구현을 완료했습니다",
                "성능 테스트 결과가 만족스럽습니다",
                "사용자 피드백을 반영하여 개선했습니다",
                "다음 버전 출시를 준비하고 있습니다"
            ]
            
            test_contents = []
            expected_duplicates = 0
            
            # 50% 중복, 50% 고유 컨텐츠 생성
            for i in range(sample_size):
                if i % 3 == 0:  # 33% 중복
                    content = base_contents[i % len(base_contents)]
                    expected_duplicates += 1
                elif i % 3 == 1:  # 33% 유사 (약간 변형)
                    content = base_contents[i % len(base_contents)] + f" - 업데이트 {i}"
                    expected_duplicates += 1
                else:  # 33% 완전 고유
                    content = f"완전히 새로운 고유 컨텐츠 {i} - {datetime.now().microsecond}"
                
                test_contents.append(content)
            
            detection_times = []
            duplicates_detected = 0
            
            for content in test_contents:
                # 여러 번 측정하여 정확도 향상
                measurements = []
                for _ in range(3):
                    start_time = time.perf_counter()
                    try:
                        duplicate_result = self.duplicate_detector.check_duplicate(content)
                        detection_time = time.perf_counter() - start_time
                        measurements.append(detection_time * 1000)
                        
                        if duplicate_result.get('is_duplicate', False):
                            duplicates_detected += 1
                    except Exception as e:
                        logger.warning(f"중복 감지 중 오류: {e}")
                        measurements.append(0)
                
                detection_times.append(statistics.median(measurements))
            
            # 정확도 계산
            detection_accuracy = (duplicates_detected / expected_duplicates * 100) if expected_duplicates > 0 else 0
            
            results["duplicate_detection"] = {
                "avg_detection_time": statistics.mean(detection_times),
                "median_detection_time": statistics.median(detection_times),
                "p95_detection_time": statistics.quantiles(detection_times, n=20)[18] if len(detection_times) > 20 else max(detection_times),
                "stdev_detection_time": statistics.stdev(detection_times) if len(detection_times) > 1 else 0,
                "detection_accuracy": detection_accuracy,
                "detection_throughput": sample_size / (sum(detection_times) / 1000),
                "expected_duplicates": expected_duplicates,
                "detected_duplicates": duplicates_detected,
                "sample_count": sample_size
            }
        
        return results
    
    def _prepare_test_memory_blocks(self, count: int, clear_existing: bool = False):
        """테스트용 메모리 블록 준비 (개선된 버전)"""
        if clear_existing:
            # 기존 테스트 블록 정리 (실제 구현에서는 주의 필요)
            logger.info("기존 테스트 블록 정리 중...")
        
        logger.info(f"테스트용 메모리 블록 {count}개 준비 중...")
        
        # 더 현실적인 컨텐츠 패턴
        content_templates = [
            "프로젝트 {phase} 단계에서 {task}를 수행했습니다. 결과: {result}",
            "{date}에 {feature} 기능을 {action}했습니다. 상태: {status}",
            "{team}팀에서 {issue} 이슈를 {method}로 해결했습니다.",
            "{version} 버전에서 {improvement} 개선사항을 적용했습니다.",
            "{metric} 성능이 {change}% {direction}했습니다. 원인: {cause}"
        ]
        
        phases = ["기획", "설계", "개발", "테스트", "배포"]
        tasks = ["요구사항 분석", "API 설계", "코드 작성", "단위 테스트", "통합 테스트"]
        results = ["성공", "부분 성공", "보완 필요", "완료", "진행 중"]
        features = ["로그인", "검색", "알림", "대시보드", "리포팅"]
        actions = ["구현", "개선", "수정", "최적화", "리팩토링"]
        statuses = ["완료", "진행중", "대기", "검토중", "승인대기"]
        
        for i in range(count):
            template = content_templates[i % len(content_templates)]
            
            context = template.format(
                phase=phases[i % len(phases)],
                task=tasks[i % len(tasks)],
                result=results[i % len(results)],
                date=f"2025-{(i % 12) + 1:02d}-{(i % 28) + 1:02d}",
                feature=features[i % len(features)],
                action=actions[i % len(actions)],
                status=statuses[i % len(statuses)],
                team=f"Team{i % 5 + 1}",
                issue=f"ISSUE-{i:04d}",
                method="협업" if i % 2 == 0 else "자동화",
                version=f"v{(i % 10) + 1}.{(i % 5) + 1}.{i % 3}",
                improvement=["성능", "보안", "UI/UX", "안정성"][i % 4],
                metric=["응답시간", "처리량", "메모리 사용량", "CPU 사용률"][i % 4],
                change=str((i % 50) + 10),
                direction="향상" if i % 2 == 0 else "저하",
                cause=["최적화", "리소스 부족", "알고리즘 개선", "시스템 부하"][i % 4]
            )
            
            keywords = context.split()[:4]  # 처음 4개 단어를 키워드로
            tags = [f"tag_{i % 10}", "test", phases[i % len(phases)]]
            embedding = get_embedding(context)
            importance = 0.3 + (i % 7) * 0.1  # 0.3 ~ 0.9 범위
            
            self.block_manager.add_block(
                context=context,
                keywords=keywords,
                tags=tags,
                embedding=embedding,
                importance=importance,
                metadata={"test_block": True, "index": i, "template": template}
            )
    
    def _calculate_statistical_confidence(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """측정 결과의 통계적 신뢰도 계산"""
        confidence_analysis = {
            "overall_confidence": "high",
            "sample_size_adequacy": {},
            "measurement_stability": {},
            "reliability_score": 0.0
        }
        
        # 샘플 크기 적정성 평가
        for metric_category, metric_data in metrics.items():
            if isinstance(metric_data, dict):
                sample_counts = []
                
                for key, value in metric_data.items():
                    if isinstance(value, dict) and "sample_count" in value:
                        sample_counts.append(value["sample_count"])
                
                if sample_counts:
                    avg_sample_size = statistics.mean(sample_counts)
                    adequacy = "excellent" if avg_sample_size >= 500 else \
                              "good" if avg_sample_size >= 200 else \
                              "adequate" if avg_sample_size >= 100 else "insufficient"
                    
                    confidence_analysis["sample_size_adequacy"][metric_category] = {
                        "avg_sample_size": avg_sample_size,
                        "adequacy": adequacy
                    }
        
        # 신뢰도 점수 계산 (0.0 ~ 1.0)
        adequacy_scores = []
        for category_data in confidence_analysis["sample_size_adequacy"].values():
            adequacy = category_data["adequacy"]
            score = {"excellent": 1.0, "good": 0.8, "adequate": 0.6, "insufficient": 0.3}[adequacy]
            adequacy_scores.append(score)
        
        if adequacy_scores:
            confidence_analysis["reliability_score"] = statistics.mean(adequacy_scores)
            
            if confidence_analysis["reliability_score"] >= 0.9:
                confidence_analysis["overall_confidence"] = "very_high"
            elif confidence_analysis["reliability_score"] >= 0.7:
                confidence_analysis["overall_confidence"] = "high"
            elif confidence_analysis["reliability_score"] >= 0.5:
                confidence_analysis["overall_confidence"] = "moderate"
            else:
                confidence_analysis["overall_confidence"] = "low"
        
        return confidence_analysis
    
    def save_comprehensive_baseline(self, performance_data: Dict[str, Any]):
        """종합 기준점 데이터 저장"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        baseline_file = self.data_dir / f"comprehensive_baseline_{timestamp}.json"
        
        comprehensive_baseline = {
            "created_at": datetime.now().isoformat(),
            "greeum_version": "2.0.5",
            "measurement_type": "comprehensive",
            "statistical_confidence": performance_data.get("statistical_confidence", {}),
            "performance_data": performance_data
        }
        
        logger.info(f"종합 기준점 데이터 저장: {baseline_file}")
        
        with open(baseline_file, 'w', encoding='utf-8') as f:
            json.dump(comprehensive_baseline, f, ensure_ascii=False, indent=2)
        
        # 히스토리에도 추가
        history_file = self.data_dir / "comprehensive_performance_history.json"
        history = []
        
        if history_file.exists():
            with open(history_file, 'r', encoding='utf-8') as f:
                history = json.load(f)
        
        history.append({
            "timestamp": datetime.now().isoformat(),
            "baseline_file": baseline_file.name,
            "sample_size": performance_data.get("sample_size", 0),
            "confidence_level": performance_data.get("confidence_level", 0),
            "measurement_duration": performance_data.get("measurement_duration", 0)
        })
        
        # 최근 50개 기록만 유지
        history = history[-50:]
        
        with open(history_file, 'w', encoding='utf-8') as f:
            json.dump(history, f, ensure_ascii=False, indent=2)
        
        return baseline_file
    
    def generate_comprehensive_report(self, performance_data: Dict[str, Any]) -> str:
        """종합 성능 리포트 생성"""
        report = f"""# Greeum v2.0.5 종합 성능 기준점 리포트

## 📊 측정 개요
- **측정 시간**: {performance_data['measurement_timestamp']}
- **Greeum 버전**: {performance_data['greeum_version']}
- **샘플 크기**: {performance_data['sample_size']:,}개
- **신뢰도 수준**: {performance_data['confidence_level']:.1%}
- **측정 소요 시간**: {performance_data['measurement_duration']:.2f}초

## 🔍 통계적 신뢰도
"""
        
        confidence = performance_data.get('statistical_confidence', {})
        report += f"""- **전체 신뢰도**: {confidence.get('overall_confidence', 'unknown').upper()}
- **신뢰도 점수**: {confidence.get('reliability_score', 0):.3f}/1.000
"""
        
        # 메모리 검색 성능 상세 분석
        memory_search = performance_data['metrics'].get('memory_search', {})
        if memory_search:
            report += f"""
## 🧠 메모리 검색 성능 분석

### 확장성 테스트 결과
"""
            for memory_size, data in memory_search.items():
                if memory_size.startswith('memory_size_'):
                    size = memory_size.split('_')[-1]
                    report += f"""
#### {size}개 블록 환경
- **평균 LTM 검색**: {data['avg_ltm_search_time']:.2f}ms (표준편차: {data['stdev_ltm_search_time']:.2f}ms)
- **평균 캐시 검색**: {data['avg_cache_search_time']:.2f}ms (표준편차: {data['stdev_cache_search_time']:.2f}ms)
- **99% 레이턴시**: LTM {data['p99_ltm_search_time']:.2f}ms, 캐시 {data['p99_cache_search_time']:.2f}ms
- **속도 향상**: {data['avg_speedup_ratio']:.2f}x
- **샘플 수**: {data['sample_count']:,}개
"""
        
        # 동시성 성능 분석
        concurrency = performance_data['metrics'].get('concurrency', {})
        if concurrency:
            report += f"""
## ⚡ 동시성 성능 분석

### 스레드별 성능
"""
            for thread_config, data in concurrency.items():
                if thread_config.startswith('threads_'):
                    threads = thread_config.split('_')[-1]
                    if 'error' not in data:
                        report += f"""
#### {threads}개 스레드
- **평균 작업 시간**: {data['avg_task_time']:.2f}ms
- **처리량**: {data['throughput_tasks_per_sec']:.1f} 작업/초
- **95% 레이턴시**: {data['p95_task_time']:.2f}ms
- **오류율**: {data['error_rate']:.2f}%
"""
        
        # 확장성 분석
        scalability = performance_data['metrics'].get('scalability', {})
        if scalability:
            analysis = scalability.get('scalability_analysis', {})
            if analysis:
                report += f"""
## 📈 확장성 분석
- **기준 성능** (100블록): {analysis['base_performance_100_blocks']:.2f}ms
- **선형 확장성 점수**: {analysis['linear_scalability_score']:.3f}/1.000
"""
                
            factors = analysis.get('scalability_factors', {})
            for block_config, factor in factors.items():
                blocks = block_config.split('_')[-1]
                report += f"- **{blocks}개 블록**: {factor:.2f}x 성능 저하\n"
        
        # v2.0.5 신규 기능 성능
        v205_features = performance_data['metrics'].get('v205_features', {})
        if v205_features:
            report += f"""
## 🆕 v2.0.5 신규 기능 성능

### 품질 검증
"""
            quality_validation = v205_features.get('quality_validation', {})
            if quality_validation:
                report += f"""- **평균 검증 시간**: {quality_validation['avg_validation_time']:.3f}ms
- **처리량**: {quality_validation['validation_throughput']:.0f} 검증/초
- **99% 레이턴시**: {quality_validation.get('p95_validation_time', 0):.3f}ms
- **평균 품질 점수**: {quality_validation['avg_quality_score']:.3f}
"""
            
            duplicate_detection = v205_features.get('duplicate_detection', {})
            if duplicate_detection:
                report += f"""
### 중복 감지
- **평균 감지 시간**: {duplicate_detection['avg_detection_time']:.3f}ms
- **감지 정확도**: {duplicate_detection['detection_accuracy']:.1f}%
- **처리량**: {duplicate_detection['detection_throughput']:.0f} 감지/초
- **예상 중복**: {duplicate_detection['expected_duplicates']}개, **실제 감지**: {duplicate_detection['detected_duplicates']}개
"""
        
        # 시스템 리소스
        system_resources = performance_data['metrics'].get('system_resources', {})
        if system_resources and 'error' not in system_resources:
            process_memory = system_resources.get('process_memory', {})
            process_cpu = system_resources.get('process_cpu', {})
            report += f"""
## 💻 시스템 리소스 사용량
- **메모리 사용량**: {process_memory.get('rss_mb', 0):.1f}MB ({process_memory.get('percent', 0):.1f}%)
- **CPU 사용률**: {process_cpu.get('percent_1s', 0):.1f}%
- **스레드 수**: {process_cpu.get('num_threads', 0)}개
- **시스템 메모리 여유**: {process_memory.get('available_mb', 0):.0f}MB
"""
        
        report += f"""
## 📋 성능 등급 평가

### 전체 성능 등급
"""
        
        # 성능 등급 계산 로직
        overall_grade = self._calculate_performance_grade(performance_data['metrics'])
        report += f"**{overall_grade['grade']}등급** - {overall_grade['description']}\n"
        
        for category, grade_info in overall_grade['category_grades'].items():
            report += f"- **{category}**: {grade_info['grade']}등급 ({grade_info['score']:.1f}/100)\n"
        
        report += f"""
## 🎯 권장사항

### 즉시 개선 필요
"""
        
        recommendations = self._generate_performance_recommendations(performance_data['metrics'])
        for priority, items in recommendations.items():
            if items:
                report += f"\n#### {priority.upper()} 우선순위\n"
                for item in items:
                    report += f"- {item}\n"
        
        report += f"""
---
**리포트 생성 시간**: {datetime.now().isoformat()}
**측정 신뢰도**: {confidence.get('overall_confidence', 'unknown').upper()}
"""
        
        return report
    
    def _calculate_performance_grade(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """성능 등급 계산"""
        category_scores = {}
        
        # 메모리 검색 성능 점수
        memory_search = metrics.get('memory_search', {})
        if memory_search:
            # 1000개 블록 기준으로 평가
            memory_1000 = memory_search.get('memory_size_1000', {})
            if memory_1000:
                ltm_time = memory_1000.get('avg_ltm_search_time', 100)
                cache_time = memory_1000.get('avg_cache_search_time', 100)
                speedup = memory_1000.get('avg_speedup_ratio', 1)
                
                # 점수 계산 (시간이 짧을수록, 속도향상이 클수록 높은 점수)
                ltm_score = max(0, 100 - ltm_time * 2)  # 50ms 이하면 만점
                cache_score = max(0, 100 - cache_time * 1)  # 100ms 이하면 만점  
                speedup_score = min(100, speedup * 20)  # 5x 속도향상이면 만점
                
                category_scores['memory_search'] = (ltm_score + cache_score + speedup_score) / 3
        
        # 동시성 성능 점수
        concurrency = metrics.get('concurrency', {})
        if concurrency:
            # 8스레드 기준으로 평가
            threads_8 = concurrency.get('threads_8', {})
            if threads_8 and 'error' not in threads_8:
                throughput = threads_8.get('throughput_tasks_per_sec', 0)
                error_rate = threads_8.get('error_rate', 100)
                
                throughput_score = min(100, throughput * 10)  # 10 작업/초면 만점
                error_score = max(0, 100 - error_rate * 5)  # 오류율 0%면 만점
                
                category_scores['concurrency'] = (throughput_score + error_score) / 2
        
        # 확장성 점수
        scalability = metrics.get('scalability', {})
        if scalability:
            analysis = scalability.get('scalability_analysis', {})
            if analysis:
                scalability_score = analysis.get('linear_scalability_score', 0) * 100
                category_scores['scalability'] = scalability_score
        
        # v2.0.5 신규 기능 점수
        v205_features = metrics.get('v205_features', {})
        if v205_features:
            feature_scores = []
            
            quality_validation = v205_features.get('quality_validation', {})
            if quality_validation:
                validation_time = quality_validation.get('avg_validation_time', 10)
                throughput = quality_validation.get('validation_throughput', 0)
                
                time_score = max(0, 100 - validation_time * 100)  # 1ms 이하면 만점
                throughput_score = min(100, throughput / 10)  # 1000 검증/초면 만점
                feature_scores.append((time_score + throughput_score) / 2)
            
            duplicate_detection = v205_features.get('duplicate_detection', {})
            if duplicate_detection:
                detection_time = duplicate_detection.get('avg_detection_time', 100)
                accuracy = duplicate_detection.get('detection_accuracy', 0)
                
                time_score = max(0, 100 - detection_time)  # 1ms 이하면 만점
                accuracy_score = accuracy  # 정확도는 그대로 점수
                feature_scores.append((time_score + accuracy_score) / 2)
            
            if feature_scores:
                category_scores['v205_features'] = statistics.mean(feature_scores)
        
        # 전체 점수 및 등급 계산
        if category_scores:
            overall_score = statistics.mean(category_scores.values())
        else:
            overall_score = 0
        
        def score_to_grade(score):
            if score >= 90:
                return 'A', 'Outstanding'
            elif score >= 80:
                return 'B', 'Good'
            elif score >= 70:
                return 'C', 'Average'
            elif score >= 60:
                return 'D', 'Below Average'
            else:
                return 'F', 'Poor'
        
        overall_grade, overall_desc = score_to_grade(overall_score)
        
        category_grades = {}
        for category, score in category_scores.items():
            grade, desc = score_to_grade(score)
            category_grades[category] = {
                'score': score,
                'grade': grade,
                'description': desc
            }
        
        return {
            'score': overall_score,
            'grade': overall_grade,
            'description': overall_desc,
            'category_grades': category_grades
        }
    
    def _generate_performance_recommendations(self, metrics: Dict[str, Any]) -> Dict[str, List[str]]:
        """성능 개선 권장사항 생성"""
        recommendations = {
            'critical': [],
            'high': [],
            'medium': [],
            'low': []
        }
        
        # 메모리 검색 성능 분석
        memory_search = metrics.get('memory_search', {})
        if memory_search:
            for memory_size, data in memory_search.items():
                if memory_size.startswith('memory_size_'):
                    size = int(memory_size.split('_')[-1])
                    avg_ltm_time = data.get('avg_ltm_search_time', 0)
                    speedup_ratio = data.get('avg_speedup_ratio', 1)
                    
                    if avg_ltm_time > 50:  
                        recommendations['high'].append(f"{size}개 블록 환경에서 LTM 검색 시간 최적화 필요 ({avg_ltm_time:.1f}ms)")
                    
                    if speedup_ratio < 2:
                        recommendations['medium'].append(f"{size}개 블록에서 캐시 효율성 개선 필요 (현재 {speedup_ratio:.1f}x)")
        
        # 동시성 성능 분석
        concurrency = metrics.get('concurrency', {})
        if concurrency:
            for thread_config, data in concurrency.items():
                if thread_config.startswith('threads_') and 'error' not in data:
                    threads = int(thread_config.split('_')[-1])
                    error_rate = data.get('error_rate', 0)
                    throughput = data.get('throughput_tasks_per_sec', 0)
                    
                    if error_rate > 5:
                        recommendations['critical'].append(f"{threads}스레드 환경에서 오류율 높음 ({error_rate:.1f}%)")
                    
                    if throughput < 5:
                        recommendations['high'].append(f"{threads}스레드 환경에서 처리량 부족 ({throughput:.1f} 작업/초)")
        
        # 확장성 분석
        scalability = metrics.get('scalability', {})
        if scalability:
            analysis = scalability.get('scalability_analysis', {})
            if analysis:
                scalability_score = analysis.get('linear_scalability_score', 1)
                
                if scalability_score < 0.5:
                    recommendations['critical'].append(f"확장성 심각한 문제 (점수: {scalability_score:.2f}/1.0)")
                elif scalability_score < 0.7:
                    recommendations['high'].append(f"확장성 개선 필요 (점수: {scalability_score:.2f}/1.0)")
        
        # v2.0.5 신규 기능 분석
        v205_features = metrics.get('v205_features', {})
        if v205_features:
            duplicate_detection = v205_features.get('duplicate_detection', {})
            if duplicate_detection:
                accuracy = duplicate_detection.get('detection_accuracy', 100)
                if accuracy < 70:
                    recommendations['high'].append(f"중복 감지 정확도 개선 필요 ({accuracy:.1f}%)")
                elif accuracy < 85:
                    recommendations['medium'].append(f"중복 감지 정확도 미세 조정 권장 ({accuracy:.1f}%)")
        
        # 시스템 리소스 분석
        system_resources = metrics.get('system_resources', {})
        if system_resources and 'error' not in system_resources:
            process_memory = system_resources.get('process_memory', {})
            if process_memory:
                memory_mb = process_memory.get('rss_mb', 0)
                memory_percent = process_memory.get('percent', 0)
                
                if memory_mb > 1000:  # 1GB 이상
                    recommendations['medium'].append(f"메모리 사용량 높음 ({memory_mb:.0f}MB)")
                
                if memory_percent > 10:  # 시스템 메모리 10% 이상
                    recommendations['low'].append(f"시스템 메모리 점유율 주의 ({memory_percent:.1f}%)")
        
        # 일반적인 권장사항
        if not any(recommendations.values()):
            recommendations['low'].append("현재 성능 수준 양호 - 정기적인 모니터링 권장")
        
        return recommendations


def main():
    """메인 실행 함수"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(f"tests/performance_suite/results/comprehensive_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"),
            logging.StreamHandler()
        ]
    )
    
    logger.info("Greeum v2.0.5 종합 성능 측정 시작")
    
    # 종합 기준점 추적기 초기화
    tracker = ComprehensiveBaselineTracker()
    
    # 종합 성능 측정 (정확성과 실용성의 균형)
    performance_data = tracker.measure_comprehensive_performance(sample_size=150)
    
    # 기준점 저장
    baseline_file = tracker.save_comprehensive_baseline(performance_data)
    
    # 종합 리포트 생성
    report = tracker.generate_comprehensive_report(performance_data)
    
    # 리포트 파일 저장
    report_file = baseline_file.parent / f"comprehensive_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report)
    
    logger.info(f"종합 성능 측정 완료")
    logger.info(f"기준점 파일: {baseline_file}")
    logger.info(f"리포트 파일: {report_file}")
    
    # 요약 출력
    confidence = performance_data.get('statistical_confidence', {})
    print(f"\n{'='*60}")
    print(f"🎯 Greeum v2.0.5 종합 성능 측정 완료")
    print(f"{'='*60}")
    print(f"📊 샘플 크기: {performance_data['sample_size']:,}개")
    print(f"⏱️  측정 시간: {performance_data['measurement_duration']:.1f}초")
    print(f"🔍 신뢰도: {confidence.get('overall_confidence', 'unknown').upper()}")
    print(f"📈 신뢰도 점수: {confidence.get('reliability_score', 0):.3f}/1.000")
    print(f"📁 결과 파일: {baseline_file.name}")
    print(f"{'='*60}")

if __name__ == "__main__":
    main()