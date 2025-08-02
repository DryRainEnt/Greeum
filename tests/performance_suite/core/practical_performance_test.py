#!/usr/bin/env python3
"""
Greeum v2.0.5 실용적 성능 측정 시스템

시간 효율성과 측정 정확도의 균형을 맞춘 실용적인 성능 테스트입니다.
충분한 샘플로 통계적 신뢰도를 확보하면서도 합리적인 실행 시간을 유지합니다.
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

# 상위 디렉토리를 path에 추가
sys.path.insert(0, os.path.abspath('../../..'))

from greeum import DatabaseManager, BlockManager, STMManager, CacheManager
from greeum.core.prompt_wrapper import PromptWrapper
from greeum.embedding_models import get_embedding

logger = logging.getLogger(__name__)

class PracticalPerformanceTest:
    """실용적이고 정확한 성능 측정 클래스"""
    
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
        
        logger.info(f"PracticalPerformanceTest 초기화 완료 - 데이터 디렉토리: {self.data_dir}")
    
    def run_comprehensive_test(self, 
                              memory_sample_size: int = 100,
                              quality_sample_size: int = 30,
                              concurrency_sample_size: int = 20) -> Dict[str, Any]:
        """
        종합 성능 테스트 실행
        
        Args:
            memory_sample_size: 메모리 검색 테스트 샘플 수
            quality_sample_size: 응답 품질 테스트 샘플 수  
            concurrency_sample_size: 동시성 테스트 샘플 수
        """
        logger.info(f"종합 성능 테스트 시작 - 메모리:{memory_sample_size}, 품질:{quality_sample_size}, 동시성:{concurrency_sample_size}")
        start_time = time.time()
        
        results = {
            "test_timestamp": datetime.now().isoformat(),
            "greeum_version": "2.0.5",
            "sample_sizes": {
                "memory_search": memory_sample_size,
                "response_quality": quality_sample_size,
                "concurrency": concurrency_sample_size
            },
            "metrics": {}
        }
        
        # 1. 메모리 검색 성능 테스트
        logger.info("🧠 메모리 검색 성능 테스트 중...")
        results["metrics"]["memory_search"] = self._test_memory_search_performance(memory_sample_size)
        
        # 2. 응답 품질 테스트
        logger.info("📝 응답 품질 테스트 중...")
        results["metrics"]["response_quality"] = self._test_response_quality(quality_sample_size)
        
        # 3. 확장성 테스트 (간소화)
        logger.info("📈 확장성 테스트 중...")
        results["metrics"]["scalability"] = self._test_scalability_simplified()
        
        # 4. 동시성 테스트 (간소화)
        logger.info("⚡ 동시성 테스트 중...")
        results["metrics"]["concurrency"] = self._test_concurrency_simplified(concurrency_sample_size)
        
        # 5. 시스템 리소스 모니터링
        logger.info("💻 시스템 리소스 모니터링 중...")
        results["metrics"]["system_resources"] = self._monitor_system_resources()
        
        total_time = time.time() - start_time
        results["total_test_duration"] = total_time
        
        # 성능 등급 계산
        results["performance_grade"] = self._calculate_performance_grade(results["metrics"])
        
        logger.info(f"종합 성능 테스트 완료 - 소요 시간: {total_time:.2f}초")
        return results
    
    def _test_memory_search_performance(self, sample_size: int) -> Dict[str, Any]:
        """메모리 검색 성능 테스트"""
        # 현실적인 크기의 메모리 블록 환경 구성
        memory_sizes = [100, 500, 1000]
        results = {}
        
        for memory_size in memory_sizes:
            logger.info(f"  📊 {memory_size}개 블록 환경 테스트...")
            
            # 테스트 메모리 블록 준비 (기존 블록 활용)
            self._prepare_memory_blocks(memory_size)
            
            # 다양한 쿼리 패턴으로 테스트
            test_queries = [
                "프로젝트 진행 상황",
                "개발 계획 및 일정",
                "성능 최적화 방안",
                "버그 수정 현황",
                "새로운 기능 구현",
                "사용자 피드백 분석",
                "테스트 결과 검토",
                "배포 준비 상황"
            ]
            
            ltm_times = []
            cache_times = []
            speedup_ratios = []
            
            # 각 메모리 크기에 대해 충분한 샘플 수행
            samples_per_size = sample_size // len(memory_sizes)
            
            for i in range(samples_per_size):
                query = test_queries[i % len(test_queries)] + f" {i}"
                embedding = get_embedding(query)
                keywords = query.split()[:3]
                
                # LTM 직접 검색 시간 측정
                start_time = time.perf_counter()
                ltm_results = self.block_manager.search_by_embedding(embedding, top_k=5)
                ltm_time = (time.perf_counter() - start_time) * 1000
                ltm_times.append(ltm_time)
                
                # Cache 검색 시간 측정
                start_time = time.perf_counter()
                cache_results = self.cache_manager.update_cache(query, embedding, keywords)
                cache_time = (time.perf_counter() - start_time) * 1000
                cache_times.append(cache_time)
                
                # 속도 향상 비율 계산
                if cache_time > 0:
                    speedup_ratios.append(ltm_time / cache_time)
            
            # 통계 계산
            results[f"memory_size_{memory_size}"] = {
                "block_count": memory_size,
                "sample_count": len(ltm_times),
                
                # LTM 성능
                "ltm_avg_time_ms": statistics.mean(ltm_times),
                "ltm_median_time_ms": statistics.median(ltm_times),
                "ltm_p95_time_ms": statistics.quantiles(ltm_times, n=20)[18] if len(ltm_times) >= 20 else max(ltm_times),
                "ltm_std_dev": statistics.stdev(ltm_times) if len(ltm_times) > 1 else 0,
                
                # Cache 성능
                "cache_avg_time_ms": statistics.mean(cache_times),
                "cache_median_time_ms": statistics.median(cache_times),
                "cache_p95_time_ms": statistics.quantiles(cache_times, n=20)[18] if len(cache_times) >= 20 else max(cache_times),
                "cache_std_dev": statistics.stdev(cache_times) if len(cache_times) > 1 else 0,
                
                # 속도 향상
                "avg_speedup_ratio": statistics.mean(speedup_ratios) if speedup_ratios else 1,
                "median_speedup_ratio": statistics.median(speedup_ratios) if speedup_ratios else 1,
                "max_speedup_ratio": max(speedup_ratios) if speedup_ratios else 1
            }
        
        # 전체 요약
        all_ltm_times = []
        all_cache_times = []
        all_speedups = []
        
        for size_result in results.values():
            # 가중 평균을 위해 샘플 수 고려하지만 여기서는 단순 평균 사용
            all_ltm_times.append(size_result["ltm_avg_time_ms"])
            all_cache_times.append(size_result["cache_avg_time_ms"])
            all_speedups.append(size_result["avg_speedup_ratio"])
        
        results["summary"] = {
            "overall_ltm_avg": statistics.mean(all_ltm_times),
            "overall_cache_avg": statistics.mean(all_cache_times),
            "overall_speedup_avg": statistics.mean(all_speedups),
            "scalability_factor": max(all_ltm_times) / min(all_ltm_times) if all_ltm_times else 1
        }
        
        return results
    
    def _test_response_quality(self, sample_size: int) -> Dict[str, Any]:
        """응답 품질 테스트"""
        # 다양한 유형의 질의 테스트
        query_types = {
            "factual": [
                "현재 프로젝트 상태는?",
                "최근 업데이트 내용은?",
                "개발 진행률은?"
            ],
            "contextual": [
                "이전 논의한 성능 이슈가 해결됐나요?",
                "지난주 계획한 작업들 완료됐나요?",
                "앞서 언급한 개선사항 적용됐나요?"
            ],
            "analytical": [
                "현재 성능과 목표의 차이는?",
                "가장 개선이 필요한 부분은?",
                "성능 향상 우선순위는?"
            ]
        }
        
        results = {}
        
        for query_type, queries in query_types.items():
            logger.info(f"  📝 {query_type} 타입 질의 테스트...")
            
            quality_scores = []
            context_usage_counts = []
            response_lengths = []
            processing_times = []
            
            samples_per_type = sample_size // len(query_types)
            
            for i in range(samples_per_type):
                query = queries[i % len(queries)]
                
                # 프롬프트 생성 시간 측정
                start_time = time.perf_counter()
                enhanced_prompt = self.prompt_wrapper.compose_prompt(query, token_budget=1500)
                processing_time = (time.perf_counter() - start_time) * 1000
                processing_times.append(processing_time)
                
                # 품질 지표 계산
                response_length = len(enhanced_prompt)
                response_lengths.append(response_length)
                
                # 컨텍스트 활용도 (관련 기억, 최근 기억 섹션 수)
                context_count = enhanced_prompt.count('관련 기억:') + enhanced_prompt.count('최근 기억:')
                context_usage_counts.append(context_count)
                
                # 품질 점수 (정보 밀도 기반)
                words = enhanced_prompt.split()
                meaningful_words = [w for w in words if len(w) > 3]
                quality_score = len(meaningful_words) / len(words) if words else 0
                quality_scores.append(quality_score)
            
            # 통계 계산
            results[query_type] = {
                "sample_count": len(quality_scores),
                "avg_quality_score": statistics.mean(quality_scores),
                "median_quality_score": statistics.median(quality_scores),
                "avg_context_usage": statistics.mean(context_usage_counts),
                "avg_response_length": statistics.mean(response_lengths),
                "avg_processing_time_ms": statistics.mean(processing_times),
                "quality_consistency": 1 - (statistics.stdev(quality_scores) / statistics.mean(quality_scores)) if statistics.mean(quality_scores) > 0 else 1
            }
        
        # 전체 요약
        all_quality_scores = []
        all_context_usage = []
        all_processing_times = []
        
        for type_result in results.values():
            all_quality_scores.append(type_result["avg_quality_score"])
            all_context_usage.append(type_result["avg_context_usage"])
            all_processing_times.append(type_result["avg_processing_time_ms"])
        
        results["summary"] = {
            "overall_quality_score": statistics.mean(all_quality_scores),
            "overall_context_usage": statistics.mean(all_context_usage),
            "overall_processing_time": statistics.mean(all_processing_times),
            "quality_variance": statistics.stdev(all_quality_scores) if len(all_quality_scores) > 1 else 0
        }
        
        return results
    
    def _test_scalability_simplified(self) -> Dict[str, Any]:
        """간소화된 확장성 테스트"""
        block_counts = [100, 500, 1000]
        test_query = "확장성 테스트 쿼리"
        embedding = get_embedding(test_query)
        
        results = {}
        base_time = None
        
        for block_count in block_counts:
            logger.info(f"  📈 {block_count}개 블록 확장성 테스트...")
            
            self._prepare_memory_blocks(block_count)
            
            # 5회 측정 후 평균
            search_times = []
            for _ in range(5):
                start_time = time.perf_counter()
                search_results = self.block_manager.search_by_embedding(embedding, top_k=5)
                search_time = (time.perf_counter() - start_time) * 1000
                search_times.append(search_time)
            
            avg_time = statistics.mean(search_times)
            
            if base_time is None:
                base_time = avg_time
                scalability_factor = 1.0
            else:
                scalability_factor = avg_time / base_time
            
            results[f"blocks_{block_count}"] = {
                "block_count": block_count,
                "avg_search_time_ms": avg_time,
                "scalability_factor": scalability_factor,
                "search_efficiency": block_count / avg_time,  # 블록당 검색 효율
                "measurements": len(search_times)
            }
        
        # 선형성 점수 계산
        scalability_factors = [results[f"blocks_{count}"]["scalability_factor"] for count in block_counts]
        ideal_factors = [count / block_counts[0] for count in block_counts]
        
        deviations = [abs(ideal - actual) for ideal, actual in zip(ideal_factors, scalability_factors)]
        linearity_score = max(0, 1 - statistics.mean(deviations))
        
        results["analysis"] = {
            "base_performance_ms": base_time,
            "linearity_score": linearity_score,
            "scalability_rating": "excellent" if linearity_score > 0.8 else 
                                 "good" if linearity_score > 0.6 else 
                                 "fair" if linearity_score > 0.4 else "poor"
        }
        
        return results
    
    def _test_concurrency_simplified(self, sample_size: int) -> Dict[str, Any]:
        """간소화된 동시성 테스트"""
        import threading
        import queue
        
        thread_counts = [1, 2, 4, 8]
        results = {}
        
        def worker_task(task_queue, result_queue, worker_id):
            """워커 스레드 작업"""
            while True:
                try:
                    task_id = task_queue.get_nowait()
                    query = f"동시성 테스트 {worker_id}-{task_id}"
                    embedding = get_embedding(query)
                    
                    start_time = time.perf_counter()
                    search_results = self.block_manager.search_by_embedding(embedding, top_k=5)
                    execution_time = (time.perf_counter() - start_time) * 1000
                    
                    result_queue.put({
                        "worker_id": worker_id,
                        "task_id": task_id,
                        "execution_time_ms": execution_time,
                        "result_count": len(search_results)
                    })
                    
                    task_queue.task_done()
                except queue.Empty:
                    break
                except Exception as e:
                    result_queue.put({"error": str(e), "worker_id": worker_id})
                    task_queue.task_done()
        
        for thread_count in thread_counts:
            logger.info(f"  ⚡ {thread_count}개 스레드 동시성 테스트...")
            
            # 작업 큐 준비
            task_queue = queue.Queue()
            result_queue = queue.Queue()
            
            tasks_per_thread = max(1, sample_size // len(thread_counts) // thread_count)
            total_tasks = tasks_per_thread * thread_count
            
            for i in range(total_tasks):
                task_queue.put(i)
            
            # 스레드 시작
            threads = []
            start_time = time.perf_counter()
            
            for i in range(thread_count):
                thread = threading.Thread(target=worker_task, args=(task_queue, result_queue, i))
                thread.start()
                threads.append(thread)
            
            # 모든 작업 완료 대기
            task_queue.join()
            total_time = time.perf_counter() - start_time
            
            # 스레드 정리
            for thread in threads:
                thread.join()
            
            # 결과 수집
            execution_times = []
            error_count = 0
            
            while not result_queue.empty():
                result = result_queue.get()
                if "error" in result:
                    error_count += 1
                else:
                    execution_times.append(result["execution_time_ms"])
            
            # 통계 계산
            if execution_times:
                results[f"threads_{thread_count}"] = {
                    "thread_count": thread_count,
                    "total_tasks": total_tasks,
                    "completed_tasks": len(execution_times),
                    "failed_tasks": error_count,
                    "total_time_s": total_time,
                    "avg_task_time_ms": statistics.mean(execution_times),
                    "median_task_time_ms": statistics.median(execution_times),
                    "throughput_tasks_per_sec": len(execution_times) / total_time,
                    "error_rate_pct": (error_count / total_tasks) * 100,
                    "efficiency": len(execution_times) / (thread_count * total_time)  # 스레드당 효율성
                }
            else:
                results[f"threads_{thread_count}"] = {
                    "thread_count": thread_count,
                    "error": "모든 작업 실패",
                    "failed_tasks": error_count
                }
        
        # 동시성 효과 분석
        single_thread_throughput = results.get("threads_1", {}).get("throughput_tasks_per_sec", 0)
        
        concurrency_analysis = {}
        for thread_count in thread_counts[1:]:
            key = f"threads_{thread_count}"
            if key in results and "throughput_tasks_per_sec" in results[key]:
                current_throughput = results[key]["throughput_tasks_per_sec"]
                if single_thread_throughput > 0:
                    speedup = current_throughput / single_thread_throughput
                    efficiency = speedup / thread_count
                    concurrency_analysis[key] = {
                        "speedup": speedup,
                        "efficiency": efficiency,
                        "rating": "excellent" if efficiency > 0.8 else
                                 "good" if efficiency > 0.6 else
                                 "fair" if efficiency > 0.4 else "poor"
                    }
        
        results["concurrency_analysis"] = concurrency_analysis
        
        return results
    
    def _monitor_system_resources(self) -> Dict[str, Any]:
        """시스템 리소스 모니터링"""
        try:
            import psutil
            import gc
            
            # 가비지 컬렉션 수행
            gc.collect()
            
            process = psutil.Process()
            
            # 메모리 정보
            memory_info = process.memory_info()
            memory_percent = process.memory_percent()
            
            # CPU 정보 (0.5초 간격으로 측정)
            cpu_percent = process.cpu_percent(interval=0.5)
            
            # 시스템 전체 정보
            system_memory = psutil.virtual_memory()
            system_cpu = psutil.cpu_percent(interval=0.5)
            
            return {
                "process_memory": {
                    "rss_mb": round(memory_info.rss / 1024 / 1024, 2),
                    "vms_mb": round(memory_info.vms / 1024 / 1024, 2),
                    "percent": round(memory_percent, 2)
                },
                "system_memory": {
                    "total_gb": round(system_memory.total / 1024 / 1024 / 1024, 2),
                    "available_gb": round(system_memory.available / 1024 / 1024 / 1024, 2),
                    "used_percent": round(system_memory.percent, 2)
                },
                "cpu_usage": {
                    "process_percent": round(cpu_percent, 2),
                    "system_percent": round(system_cpu, 2),
                    "thread_count": process.num_threads()
                },
                "measurement_time": datetime.now().isoformat()
            }
            
        except ImportError:
            return {"error": "psutil not available for system monitoring"}
        except Exception as e:
            return {"error": f"System monitoring failed: {str(e)}"}
    
    def _prepare_memory_blocks(self, target_count: int):
        """테스트용 메모리 블록 준비 (기존 블록 활용)"""
        # 현재 블록 수 확인
        current_blocks = self.block_manager.get_blocks(limit=target_count * 2)
        current_count = len(current_blocks)
        
        if current_count < target_count:
            # 부족한 블록 추가 생성
            additional_needed = target_count - current_count
            logger.info(f"  📦 {additional_needed}개 추가 블록 생성 중...")
            
            content_templates = [
                "프로젝트 {phase} 단계 진행: {status}",
                "{date} {feature} 기능 {action} 완료",
                "{team}팀 {task} 작업 결과: {result}",
                "v{version} {component} 성능 개선: {improvement}%",
                "{metric} 지표 {direction}: {change}% 변화"
            ]
            
            phases = ["기획", "설계", "개발", "테스트", "배포"]
            features = ["로그인", "검색", "알림", "대시보드", "리포팅"]
            actions = ["구현", "개선", "수정", "최적화"]
            teams = ["Frontend", "Backend", "DevOps", "QA"]
            
            for i in range(additional_needed):
                template = content_templates[i % len(content_templates)]
                context = template.format(
                    phase=phases[i % len(phases)],
                    status=["완료", "진행중", "검토중"][i % 3],
                    date=f"2025-{(i % 12) + 1:02d}-{(i % 28) + 1:02d}",
                    feature=features[i % len(features)],
                    action=actions[i % len(actions)],
                    team=teams[i % len(teams)],
                    task=f"Task-{i:03d}",
                    result=["성공", "부분성공", "재검토필요"][i % 3],
                    version=f"{(i % 3) + 1}.{(i % 5) + 1}",
                    component=["API", "UI", "DB", "Cache"][i % 4],
                    improvement=str(10 + (i % 30)),
                    metric=["응답시간", "처리량", "메모리", "CPU"][i % 4],
                    direction=["개선", "저하"][i % 2],
                    change=str(5 + (i % 20))
                )
                
                keywords = context.split()[:3]
                tags = ["test", phases[i % len(phases)]]
                embedding = get_embedding(context)
                importance = 0.3 + (i % 7) * 0.1
                
                self.block_manager.add_block(
                    context=context,
                    keywords=keywords,
                    tags=tags,
                    embedding=embedding,
                    importance=importance,
                    metadata={"test_block": True, "batch": "practical_test"}
                )
    
    def _calculate_performance_grade(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """성능 등급 계산"""
        grades = {}
        scores = {}
        
        # 메모리 검색 성능 평가
        memory_search = metrics.get("memory_search", {})
        if memory_search and "summary" in memory_search:
            summary = memory_search["summary"]
            ltm_avg = summary.get("overall_ltm_avg", 100)
            cache_avg = summary.get("overall_cache_avg", 100)
            speedup = summary.get("overall_speedup_avg", 1)
            
            # 점수 계산 (0-100)
            ltm_score = max(0, 100 - ltm_avg * 2)  # 50ms 이하면 만점
            cache_score = max(0, 100 - cache_avg)  # 100ms 이하면 만점
            speedup_score = min(100, speedup * 20)  # 5x 이상이면 만점
            
            memory_score = (ltm_score + cache_score + speedup_score) / 3
            scores["memory_search"] = memory_score
        
        # 응답 품질 평가
        response_quality = metrics.get("response_quality", {})
        if response_quality and "summary" in response_quality:
            summary = response_quality["summary"]
            quality_score = summary.get("overall_quality_score", 0) * 100
            context_usage = summary.get("overall_context_usage", 0)
            processing_time = summary.get("overall_processing_time", 100)
            
            quality_points = quality_score  # 0-100
            context_points = min(100, context_usage * 50)  # 2개면 만점
            speed_points = max(0, 100 - processing_time * 10)  # 10ms 이하면 만점
            
            response_score = (quality_points + context_points + speed_points) / 3
            scores["response_quality"] = response_score
        
        # 확장성 평가
        scalability = metrics.get("scalability", {})
        if scalability and "analysis" in scalability:
            linearity_score = scalability["analysis"].get("linearity_score", 0) * 100
            scores["scalability"] = linearity_score
        
        # 동시성 평가
        concurrency = metrics.get("concurrency", {})
        if concurrency and "concurrency_analysis" in concurrency:
            analysis = concurrency["concurrency_analysis"]
            if analysis:
                # 8스레드 기준으로 평가
                threads_8 = analysis.get("threads_8", {})
                if threads_8:
                    efficiency = threads_8.get("efficiency", 0)
                    concurrency_score = efficiency * 100
                    scores["concurrency"] = concurrency_score
        
        # 전체 점수 계산
        if scores:
            overall_score = statistics.mean(scores.values())
        else:
            overall_score = 0
        
        # 등급 부여
        def score_to_grade(score):
            if score >= 90: return "A+", "Outstanding"
            elif score >= 85: return "A", "Excellent"
            elif score >= 80: return "B+", "Very Good"
            elif score >= 75: return "B", "Good"
            elif score >= 70: return "C+", "Above Average"
            elif score >= 65: return "C", "Average"
            elif score >= 60: return "D+", "Below Average"
            elif score >= 55: return "D", "Poor"
            else: return "F", "Critical"
        
        overall_grade, overall_desc = score_to_grade(overall_score)
        
        # 카테고리별 등급
        category_grades = {}
        for category, score in scores.items():
            grade, desc = score_to_grade(score)
            category_grades[category] = {
                "score": round(score, 1),
                "grade": grade,
                "description": desc
            }
        
        return {
            "overall_score": round(overall_score, 1),
            "overall_grade": overall_grade,
            "overall_description": overall_desc,
            "category_scores": scores,
            "category_grades": category_grades,
            "grade_timestamp": datetime.now().isoformat()
        }
    
    def save_results(self, results: Dict[str, Any]) -> Path:
        """결과 저장"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # JSON 결과 저장
        results_file = self.data_dir / f"practical_performance_test_{timestamp}.json"
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        
        logger.info(f"성능 테스트 결과 저장: {results_file}")
        return results_file
    
    def generate_report(self, results: Dict[str, Any]) -> str:
        """성능 테스트 리포트 생성"""
        grade = results.get("performance_grade", {})
        
        report = f"""# Greeum v2.0.5 실용적 성능 테스트 리포트

## 📊 테스트 개요
- **테스트 시간**: {results['test_timestamp']}
- **총 소요 시간**: {results['total_test_duration']:.2f}초
- **Greeum 버전**: {results['greeum_version']}

## 🎯 전체 성능 등급
**{grade.get('overall_grade', 'N/A')}등급** ({grade.get('overall_score', 0):.1f}/100) - {grade.get('overall_description', '')}

## 📈 카테고리별 성능 분석

"""
        
        # 메모리 검색 성능
        memory_search = results.get("metrics", {}).get("memory_search", {})
        if memory_search and "summary" in memory_search:
            summary = memory_search["summary"]
            category_grade = grade.get("category_grades", {}).get("memory_search", {})
            
            report += f"""### 🧠 메모리 검색 성능
- **등급**: {category_grade.get('grade', 'N/A')} ({category_grade.get('score', 0):.1f}/100)
- **평균 LTM 검색**: {summary.get('overall_ltm_avg', 0):.2f}ms
- **평균 캐시 검색**: {summary.get('overall_cache_avg', 0):.2f}ms
- **평균 속도 향상**: {summary.get('overall_speedup_avg', 1):.2f}x
- **확장성 계수**: {summary.get('scalability_factor', 1):.2f}

#### 메모리 크기별 성능
"""
            
            for size_key in ["memory_size_100", "memory_size_500", "memory_size_1000"]:
                if size_key in memory_search:
                    data = memory_search[size_key]
                    size = data["block_count"]
                    report += f"- **{size:,}개 블록**: LTM {data['ltm_avg_time_ms']:.2f}ms, 캐시 {data['cache_avg_time_ms']:.2f}ms, 속도향상 {data['avg_speedup_ratio']:.2f}x\n"
        
        # 응답 품질
        response_quality = results.get("metrics", {}).get("response_quality", {})
        if response_quality and "summary" in response_quality:
            summary = response_quality["summary"]
            category_grade = grade.get("category_grades", {}).get("response_quality", {})
            
            report += f"""
### 📝 응답 품질
- **등급**: {category_grade.get('grade', 'N/A')} ({category_grade.get('score', 0):.1f}/100)
- **전체 품질 점수**: {summary.get('overall_quality_score', 0):.3f}
- **평균 컨텍스트 활용**: {summary.get('overall_context_usage', 0):.1f}개
- **평균 처리 시간**: {summary.get('overall_processing_time', 0):.2f}ms

#### 질의 유형별 성능
"""
            
            for query_type in ["factual", "contextual", "analytical"]:
                if query_type in response_quality:
                    data = response_quality[query_type]
                    report += f"- **{query_type.title()}**: 품질 {data['avg_quality_score']:.3f}, 컨텍스트 {data['avg_context_usage']:.1f}개, 처리시간 {data['avg_processing_time_ms']:.2f}ms\n"
        
        # 확장성
        scalability = results.get("metrics", {}).get("scalability", {})
        if scalability and "analysis" in scalability:
            analysis = scalability["analysis"]
            category_grade = grade.get("category_grades", {}).get("scalability", {})
            
            report += f"""
### 📈 확장성
- **등급**: {category_grade.get('grade', 'N/A')} ({category_grade.get('score', 0):.1f}/100)
- **선형성 점수**: {analysis.get('linearity_score', 0):.3f}/1.000
- **확장성 평가**: {analysis.get('scalability_rating', 'unknown').upper()}
- **기준 성능**: {analysis.get('base_performance_ms', 0):.2f}ms (100블록)

#### 블록 수별 성능
"""
            
            for block_key in ["blocks_100", "blocks_500", "blocks_1000"]:
                if block_key in scalability:
                    data = scalability[block_key]
                    report += f"- **{data['block_count']:,}개 블록**: {data['avg_search_time_ms']:.2f}ms (확장계수 {data['scalability_factor']:.2f}x)\n"
        
        # 동시성
        concurrency = results.get("metrics", {}).get("concurrency", {})
        if concurrency:
            category_grade = grade.get("category_grades", {}).get("concurrency", {})
            
            report += f"""
### ⚡ 동시성
- **등급**: {category_grade.get('grade', 'N/A')} ({category_grade.get('score', 0):.1f}/100)

#### 스레드별 성능
"""
            
            for thread_key in ["threads_1", "threads_2", "threads_4", "threads_8"]:
                if thread_key in concurrency and "error" not in concurrency[thread_key]:
                    data = concurrency[thread_key]
                    report += f"- **{data['thread_count']}스레드**: {data['throughput_tasks_per_sec']:.1f} 작업/초, 오류율 {data['error_rate_pct']:.1f}%\n"
        
        # 시스템 리소스
        system_resources = results.get("metrics", {}).get("system_resources", {})
        if system_resources and "error" not in system_resources:
            report += f"""
### 💻 시스템 리소스
- **프로세스 메모리**: {system_resources['process_memory']['rss_mb']}MB ({system_resources['process_memory']['percent']}%)
- **시스템 메모리**: {system_resources['system_memory']['used_percent']}% 사용 중
- **CPU 사용률**: 프로세스 {system_resources['cpu_usage']['process_percent']}%, 시스템 {system_resources['cpu_usage']['system_percent']}%
- **스레드 수**: {system_resources['cpu_usage']['thread_count']}개
"""
        
        report += f"""
## 🎯 권장사항

### 개선 우선순위
"""
        
        # 성능 등급 기반 권장사항
        category_grades = grade.get("category_grades", {})
        
        high_priority = []
        medium_priority = []
        low_priority = []
        
        for category, grade_info in category_grades.items():
            score = grade_info.get("score", 0)
            category_name = category.replace("_", " ").title()
            
            if score < 60:
                high_priority.append(f"{category_name} 성능 개선 ({grade_info.get('grade', 'F')}등급)")
            elif score < 75:
                medium_priority.append(f"{category_name} 최적화 검토 ({grade_info.get('grade', 'C')}등급)")
            elif score < 85:
                low_priority.append(f"{category_name} 미세 조정 권장 ({grade_info.get('grade', 'B')}등급)")
        
        if high_priority:
            report += "\n#### 🔴 높은 우선순위\n"
            for item in high_priority:
                report += f"- {item}\n"
        
        if medium_priority:
            report += "\n#### 🟡 중간 우선순위\n"
            for item in medium_priority:
                report += f"- {item}\n"
        
        if low_priority:
            report += "\n#### 🟢 낮은 우선순위\n"
            for item in low_priority:
                report += f"- {item}\n"
        
        if not (high_priority or medium_priority or low_priority):
            report += "\n#### ✅ 현재 성능 수준 양호\n- 정기적인 모니터링 및 유지보수 권장\n"
        
        report += f"""
---
**리포트 생성 시간**: {datetime.now().isoformat()}  
**측정 신뢰도**: 실용적 샘플링 기반 신뢰 가능한 결과
"""
        
        return report


def main():
    """메인 실행 함수"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(f"tests/performance_suite/results/practical_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"),
            logging.StreamHandler()
        ]
    )
    
    logger.info("🚀 Greeum v2.0.5 실용적 성능 테스트 시작")
    
    # 성능 테스트 실행
    tester = PracticalPerformanceTest()
    
    # 균형잡힌 샘플 크기로 정확하면서도 빠른 테스트
    results = tester.run_comprehensive_test(
        memory_sample_size=120,  # 메모리 검색: 충분한 통계적 신뢰도
        quality_sample_size=45,  # 응답 품질: 질의 유형별로 충분한 샘플
        concurrency_sample_size=32  # 동시성: 스레드별로 적절한 부하
    )
    
    # 결과 저장
    results_file = tester.save_results(results)
    
    # 리포트 생성 및 저장
    report = tester.generate_report(results)
    
    report_file = results_file.parent / f"practical_performance_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report)
    
    # 결과 출력
    grade = results.get("performance_grade", {})
    
    print(f"\n{'='*60}")
    print(f"🎯 Greeum v2.0.5 실용적 성능 테스트 완료")
    print(f"{'='*60}")
    print(f"⏱️  총 소요 시간: {results['total_test_duration']:.1f}초")
    print(f"🏆 전체 성능 등급: {grade.get('overall_grade', 'N/A')} ({grade.get('overall_score', 0):.1f}/100)")
    print(f"📊 카테고리별 등급:")
    
    for category, grade_info in grade.get("category_grades", {}).items():
        category_name = category.replace("_", " ").title()
        print(f"   - {category_name}: {grade_info.get('grade', 'N/A')} ({grade_info.get('score', 0):.1f}/100)")
    
    print(f"📁 결과 파일: {results_file.name}")
    print(f"📄 리포트 파일: {report_file.name}")
    print(f"{'='*60}")
    
    logger.info(f"실용적 성능 테스트 완료 - 결과: {results_file}, 리포트: {report_file}")

if __name__ == "__main__":
    main()