#!/usr/bin/env python3
"""
Greeum 통합 성능 기준점 추적기 v2.0.5

이 모듈은 기존 BaselineTracker와 ComprehensiveBaselineTracker를 통합하여
단순/정밀 모드를 선택할 수 있는 통합된 성능 측정 시스템을 제공합니다.

Features:
- 단순 모드: 빠른 성능 체크 (50-200 샘플)
- 정밀 모드: 통계적 신뢰도가 높은 측정 (500+ 샘플)
- 회귀 감지 및 성능 히스토리 관리
- v2.0.5 신규 기능 포함 (품질 검증, 중복 감지, 사용량 분석)
"""

import os
import sys
import json
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
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

logger = logging.getLogger(__name__)

class UnifiedBaselineTracker:
    """통합 성능 기준점 추적 및 회귀 감지 클래스"""
    
    def __init__(self, data_dir: str = "tests/performance_suite/results/baselines"):
        """
        통합 기준점 추적기 초기화
        
        Args:
            data_dir: 기준점 데이터 저장 디렉토리
        """
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # Greeum 컴포넌트 초기화
        self.db_manager = DatabaseManager()
        self.block_manager = BlockManager(self.db_manager)
        self.stm_manager = STMManager(self.db_manager)
        self.cache_manager = CacheManager(block_manager=self.block_manager, stm_manager=self.stm_manager)
        self.prompt_wrapper = PromptWrapper(self.cache_manager, self.stm_manager)
        
        # v2.0.5 신규 컴포넌트 (에러 처리 포함)
        self._init_v205_components()
        
        # 측정 모드별 설정
        self.mode_configs = {
            'simple': {
                'min_sample_size': 50,
                'max_sample_size': 200,
                'warmup_iterations': 5,
                'parallel_threads': 1
            },
            'comprehensive': {
                'min_sample_size': 100,
                'max_sample_size': 1000,
                'warmup_iterations': 10,
                'parallel_threads': 4
            }
        }
        
        # 파일 경로
        self.baseline_file = self.data_dir / "unified_baseline.json"
        self.history_file = self.data_dir / "performance_history.json"
        
        # 검증된 기준점 (v2.0.4 기반)
        self.verified_baselines = {
            "T-GEN-001": {
                "avg_score_improvement": 1.86,
                "avg_info_increase": 4.2,
                "more_specific_rate": 92.0,
                "quality_improvement_pct": 18.6
            },
            "T-MEM-002": {
                "avg_ltm_search_time": 145.78,  # ms
                "avg_cache_search_time": 28.92,  # ms
                "avg_speedup_ratio": 5.04,
                "max_speedup_ratio": 8.67
            },
            "T-API-001": {
                "standard_reprompt_rate": 28.4,
                "enhanced_reprompt_rate": 6.2,
                "api_call_reduction": 22.2,
                "reprompt_reduction_pct": 78.2
            }
        }
        
        logger.info(f"UnifiedBaselineTracker 초기화 완료 - 데이터 디렉토리: {self.data_dir}")
    
    def _init_v205_components(self):
        """v2.0.5 신규 컴포넌트 초기화"""
        components = [
            ('quality_validator', QualityValidator, lambda: QualityValidator()),
            ('duplicate_detector', DuplicateDetector, lambda: DuplicateDetector(self.db_manager)),
            ('usage_analytics', UsageAnalytics, lambda: UsageAnalytics())
        ]
        
        for attr_name, component_class, initializer in components:
            try:
                component = initializer()
                setattr(self, attr_name, component)
                logger.debug(f"{component_class.__name__} 초기화 성공")
            except Exception as e:
                logger.warning(f"{component_class.__name__} 초기화 실패: {e}")
                setattr(self, attr_name, None)
    
    def measure_performance(self, mode: str = 'simple', sample_size: Optional[int] = None) -> Dict[str, Any]:
        """
        성능 측정 (모드 선택 가능)
        
        Args:
            mode: 'simple' 또는 'comprehensive'
            sample_size: 측정 샘플 크기 (None이면 모드별 기본값 사용)
            
        Returns:
            측정된 성능 지표 딕셔너리
        """
        if mode not in self.mode_configs:
            raise ValueError(f"지원하지 않는 모드: {mode}. 'simple' 또는 'comprehensive'를 선택하세요.")
        
        config = self.mode_configs[mode]
        
        if sample_size is None:
            sample_size = config['min_sample_size'] * 2  # 기본값: 최소값의 2배
        
        # 샘플 크기 검증
        if sample_size < config['min_sample_size']:
            logger.warning(f"샘플 크기 {sample_size}가 {mode} 모드 최소값 {config['min_sample_size']}보다 작습니다.")
            sample_size = config['min_sample_size']
        elif sample_size > config['max_sample_size']:
            logger.warning(f"샘플 크기 {sample_size}가 {mode} 모드 최대값 {config['max_sample_size']}보다 큽니다.")
            sample_size = config['max_sample_size']
        
        logger.info(f"{mode.upper()} 모드 성능 측정 시작 - 샘플 크기: {sample_size}")
        start_time = time.time()
        
        performance_data = {
            "measurement_timestamp": datetime.now().isoformat(),
            "greeum_version": "2.0.5",
            "measurement_mode": mode,
            "sample_size": sample_size,
            "metrics": {}
        }
        
        # 시스템 웜업 (모드별 설정)
        if mode == 'comprehensive':
            logger.info("시스템 웜업 수행 중...")
            self._perform_warmup(config['warmup_iterations'])
        
        # 성능 측정 수행
        if mode == 'simple':
            self._measure_simple_mode(performance_data, sample_size)
        else:
            self._measure_comprehensive_mode(performance_data, sample_size, config)
        
        total_time = time.time() - start_time
        performance_data["measurement_duration"] = total_time
        
        logger.info(f"{mode.upper()} 모드 성능 측정 완료 - 소요 시간: {total_time:.2f}초")
        return performance_data
    
    def _measure_simple_mode(self, performance_data: Dict[str, Any], sample_size: int):
        """단순 모드 성능 측정"""
        logger.info("단순 모드 측정 실행 중...")
        
        # 필수 측정 항목만
        performance_data["metrics"]["memory_search"] = self._measure_memory_search_performance(sample_size)
        performance_data["metrics"]["response_quality"] = self._measure_response_quality(min(sample_size // 5, 10))
        performance_data["metrics"]["system_resources"] = self._measure_system_resources()
        
        # v2.0.5 기능들 (간단한 측정)
        if self.quality_validator:
            try:
                performance_data["metrics"]["quality_validation"] = self._measure_quality_validation(min(sample_size, 50))
            except Exception as e:
                logger.warning(f"품질 검증 측정 실패: {e}")
                performance_data["metrics"]["quality_validation"] = {"error": str(e)}
    
    def _measure_comprehensive_mode(self, performance_data: Dict[str, Any], sample_size: int, config: Dict[str, Any]):
        """정밀 모드 성능 측정"""
        logger.info("정밀 모드 측정 실행 중...")
        
        # 병렬 처리를 위한 측정 함수들
        measurement_tasks = [
            ("memory_search", lambda: self._measure_memory_search_performance(sample_size)),
            ("response_quality", lambda: self._measure_response_quality(sample_size // 5)),
            ("system_resources", lambda: self._measure_system_resources())
        ]
        
        # v2.0.5 기능들 추가
        if self.quality_validator:
            measurement_tasks.append(("quality_validation", lambda: self._measure_quality_validation(sample_size)))
        if self.duplicate_detector:
            measurement_tasks.append(("duplicate_detection", lambda: self._measure_duplicate_detection(sample_size)))
        if self.usage_analytics:
            measurement_tasks.append(("usage_analytics", lambda: self._measure_usage_analytics(sample_size)))
        
        # 병렬 측정 실행
        with ThreadPoolExecutor(max_workers=config['parallel_threads']) as executor:
            future_to_metric = {executor.submit(task_func): metric_name 
                              for metric_name, task_func in measurement_tasks}
            
            for future in as_completed(future_to_metric):
                metric_name = future_to_metric[future]
                try:
                    result = future.result()
                    performance_data["metrics"][metric_name] = result
                    logger.debug(f"{metric_name} 측정 완료")
                except Exception as e:
                    logger.error(f"{metric_name} 측정 실패: {e}")
                    performance_data["metrics"][metric_name] = {"error": str(e)}
    
    def _perform_warmup(self, iterations: int = 10):
        """시스템 웜업"""
        logger.debug(f"시스템 웜업 {iterations}회 수행 중...")
        
        for i in range(iterations):
            # 간단한 작업들로 시스템 캐시 워밍업
            test_content = f"웜업 테스트 {i}"
            try:
                embedding = get_embedding(test_content)
                self.block_manager.search_by_embedding(embedding, top_k=1)
                if self.quality_validator:
                    self.quality_validator.validate_memory_quality(test_content)
            except Exception as e:
                logger.debug(f"웜업 {i+1}회차 오류 (무시): {e}")
        
        logger.debug("시스템 웜업 완료")
    
    def _measure_memory_search_performance(self, sample_size: int) -> Dict[str, Any]:
        """메모리 검색 성능 측정"""
        logger.info("메모리 검색 성능 측정 중...")
        
        # 테스트용 메모리 블록 준비
        self._prepare_test_memory_blocks(min(sample_size * 10, 2000))
        
        search_queries = [
            "프로젝트 진행 상황", "개발 계획", "성능 개선", "메모리 최적화",
            "사용자 피드백", "버그 수정", "새로운 기능", "테스트 결과"
        ]
        
        ltm_times = []
        cache_times = []
        
        for i in range(sample_size):
            query = search_queries[i % len(search_queries)] + f" {i}"
            embedding = get_embedding(query)
            
            # LTM 직접 검색 시간 측정
            start_time = time.time()
            ltm_results = self.block_manager.search_by_embedding(embedding, top_k=5)
            ltm_time = time.time() - start_time
            ltm_times.append(ltm_time * 1000)  # ms 변환
            
            # Cache 검색 시간 측정
            start_time = time.time()
            cache_results = self.cache_manager.update_cache(query, embedding, query.split())
            cache_time = time.time() - start_time
            cache_times.append(cache_time * 1000)  # ms 변환
        
        # 통계 계산
        result = {
            "avg_ltm_search_time": statistics.mean(ltm_times),
            "avg_cache_search_time": statistics.mean(cache_times),
            "sample_count": sample_size
        }
        
        # 정밀 모드인 경우 추가 통계
        if sample_size >= 100:
            result.update({
                "p95_ltm_search_time": statistics.quantiles(ltm_times, n=20)[18],
                "p95_cache_search_time": statistics.quantiles(cache_times, n=20)[18],
                "std_ltm_search_time": statistics.stdev(ltm_times),
                "std_cache_search_time": statistics.stdev(cache_times)
            })
        
        # 속도 향상 비율 계산 (zero division 방지)
        avg_cache_time = result["avg_cache_search_time"]
        if avg_cache_time > 0:
            result["avg_speedup_ratio"] = result["avg_ltm_search_time"] / avg_cache_time
        else:
            result["avg_speedup_ratio"] = 1.0
        
        return result
    
    def _measure_response_quality(self, sample_size: int) -> Dict[str, Any]:
        """응답 품질 측정"""
        logger.info("응답 품질 측정 중...")
        
        test_queries = [
            "최근 프로젝트 진행 상황은 어떻게 되나요?",
            "개발 중 어려웠던 점은 무엇인가요?",
            "다음에 구현할 기능은 무엇인가요?",
            "성능 개선을 위한 계획이 있나요?",
            "사용자 피드백은 어떤가요?"
        ]
        
        quality_scores = []
        context_usage_scores = []
        
        for i in range(sample_size):
            query = test_queries[i % len(test_queries)]
            
            try:
                # Greeum 메모리 활용 프롬프트 생성
                enhanced_prompt = self.prompt_wrapper.compose_prompt(query, token_budget=1000)
                
                # 품질 검증 (v2.0.5 신규 기능)
                if self.quality_validator:
                    quality_result = self.quality_validator.validate_memory_quality(enhanced_prompt)
                    quality_scores.append(quality_result.get('quality_score', 0))
                else:
                    quality_scores.append(0.5)  # 기본값
                
                # 컨텍스트 활용도 측정
                context_info_count = enhanced_prompt.count('관련 기억:') + enhanced_prompt.count('최근 기억:')
                context_usage_scores.append(context_info_count)
                
            except Exception as e:
                logger.warning(f"응답 품질 측정 중 오류 (샘플 {i}): {e}")
                quality_scores.append(0.0)
                context_usage_scores.append(0)
        
        # 안전한 통계 계산
        avg_quality = statistics.mean(quality_scores) if quality_scores else 0
        avg_context = statistics.mean(context_usage_scores) if context_usage_scores else 0
        
        # 일관성 계산 (zero division 방지)
        if avg_quality > 0 and len(quality_scores) > 1:
            quality_consistency = max(0, 1 - (statistics.stdev(quality_scores) / avg_quality))
        else:
            quality_consistency = 1.0
        
        return {
            "avg_quality_score": avg_quality,
            "avg_context_usage": avg_context,
            "quality_consistency": quality_consistency,
            "sample_count": sample_size
        }
    
    def _measure_quality_validation(self, sample_size: int) -> Dict[str, Any]:
        """품질 검증 성능 측정"""
        if not self.quality_validator:
            return {"error": "QualityValidator not available"}
        
        logger.info("품질 검증 성능 측정 중...")
        
        test_contents = [
            "프로젝트 개발이 순조롭게 진행되고 있습니다.",
            "새로운 기능 구현을 완료했습니다.",
            "성능 테스트 결과가 만족스럽습니다.",
            "사용자 피드백을 반영하여 개선했습니다.",
            "다음 버전 출시를 준비하고 있습니다."
        ]
        
        validation_times = []
        validation_scores = []
        
        for i in range(sample_size):
            content = test_contents[i % len(test_contents)] + f" (테스트 {i})"
            
            try:
                start_time = time.time()
                result = self.quality_validator.validate_memory_quality(content)
                validation_time = time.time() - start_time
                
                validation_times.append(validation_time * 1000)  # ms 변환
                validation_scores.append(result.get('quality_score', 0))
            except Exception as e:
                logger.warning(f"품질 검증 측정 중 오류 (샘플 {i}): {e}")
                validation_times.append(0)
                validation_scores.append(0)
        
        if validation_times and sum(validation_times) > 0:
            throughput = sample_size / (sum(validation_times) / 1000)
        else:
            throughput = 0
        
        return {
            "avg_validation_time": statistics.mean(validation_times) if validation_times else 0,
            "avg_quality_score": statistics.mean(validation_scores) if validation_scores else 0,
            "validation_throughput": throughput,
            "sample_count": sample_size
        }
    
    def _measure_duplicate_detection(self, sample_size: int) -> Dict[str, Any]:
        """중복 감지 성능 측정"""
        if not self.duplicate_detector:
            return {"error": "DuplicateDetector not available"}
        
        logger.info("중복 감지 성능 측정 중...")
        
        # 중복 테스트용 컨텐츠 준비
        base_content = "프로젝트 개발 진행 상황"
        test_contents = []
        
        # 50% 중복, 50% 고유 컨텐츠 생성
        for i in range(sample_size):
            if i % 2 == 0:
                content = f"{base_content} - 업데이트 {i//2}"
            else:
                content = f"고유한 기능 구현 완료 - 기능 {i}"
            test_contents.append(content)
        
        detection_times = []
        duplicate_detected = 0
        
        for content in test_contents:
            try:
                start_time = time.time()
                duplicate_result = self.duplicate_detector.check_duplicate(content)
                detection_time = time.time() - start_time
                
                detection_times.append(detection_time * 1000)  # ms 변환
                if duplicate_result.get('is_duplicate', False):
                    duplicate_detected += 1
            except Exception as e:
                logger.warning(f"중복 감지 측정 중 오류: {e}")
                detection_times.append(0)
        
        if detection_times and sum(detection_times) > 0:
            throughput = sample_size / (sum(detection_times) / 1000)
        else:
            throughput = 0
        
        return {
            "avg_detection_time": statistics.mean(detection_times) if detection_times else 0,
            "detection_accuracy": (duplicate_detected / max(sample_size // 2, 1)) * 100,
            "detection_throughput": throughput,
            "sample_count": sample_size
        }
    
    def _measure_usage_analytics(self, sample_size: int) -> Dict[str, Any]:
        """사용량 분석 성능 측정"""
        if not self.usage_analytics:
            return {"error": "UsageAnalytics not available"}
        
        logger.info("사용량 분석 성능 측정 중...")
        
        # 테스트 사용량 데이터 생성
        for i in range(sample_size):
            try:
                self.usage_analytics.record_usage(
                    operation=f"test_operation_{i % 5}",
                    duration=0.1 + (i % 10) * 0.05,
                    memory_used=100 + (i % 50) * 10
                )
            except Exception as e:
                logger.warning(f"사용량 기록 중 오류 (샘플 {i}): {e}")
        
        # 분석 성능 측정
        try:
            start_time = time.time()
            analytics_result = self.usage_analytics.get_analytics_summary()
            analysis_time = time.time() - start_time
            
            return {
                "analysis_time": analysis_time * 1000,  # ms
                "total_operations": analytics_result.get('total_operations', 0),
                "avg_operation_time": analytics_result.get('avg_operation_time', 0),
                "memory_efficiency": analytics_result.get('memory_efficiency', 0),
                "sample_count": sample_size
            }
        except Exception as e:
            logger.error(f"사용량 분석 중 오류: {e}")
            return {"error": str(e)}
    
    def _measure_system_resources(self) -> Dict[str, Any]:
        """시스템 리소스 사용량 측정"""
        try:
            import psutil
            process = psutil.Process()
            
            return {
                "memory_usage_mb": process.memory_info().rss / 1024 / 1024,
                "cpu_percent": process.cpu_percent(),
                "num_threads": process.num_threads(),
                "num_fds": process.num_fds() if hasattr(process, 'num_fds') else 0
            }
        except ImportError:
            logger.warning("psutil 모듈을 찾을 수 없습니다. 시스템 리소스 측정을 건너뜁니다.")
            return {"error": "psutil not available"}
        except Exception as e:
            logger.error(f"시스템 리소스 측정 중 오류: {e}")
            return {"error": str(e)}
    
    def _prepare_test_memory_blocks(self, count: int):
        """테스트용 메모리 블록 준비"""
        logger.info(f"테스트용 메모리 블록 {count}개 준비 중...")
        
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
                self.block_manager.add_block(
                    context=context,
                    keywords=keywords,
                    tags=tags,
                    embedding=embedding,
                    importance=importance,
                    metadata={"test_block": True, "index": i}
                )
            except Exception as e:
                logger.warning(f"테스트 블록 {i} 생성 실패: {e}")
    
    def save_baseline(self, performance_data: Dict[str, Any]):
        """기준점 데이터 저장"""
        logger.info(f"기준점 데이터 저장: {self.baseline_file}")
        
        baseline_data = {
            "created_at": datetime.now().isoformat(),
            "greeum_version": "2.0.5",
            "measurement_mode": performance_data.get('measurement_mode', 'simple'),
            "performance_data": performance_data,
            "verified_baselines": self.verified_baselines
        }
        
        with open(self.baseline_file, 'w', encoding='utf-8') as f:
            json.dump(baseline_data, f, ensure_ascii=False, indent=2)
        
        # 히스토리에도 추가
        self._update_performance_history(performance_data)
    
    def _update_performance_history(self, performance_data: Dict[str, Any]):
        """성능 히스토리 업데이트"""
        history = []
        
        if self.history_file.exists():
            try:
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    history = json.load(f)
            except Exception as e:
                logger.warning(f"히스토리 파일 읽기 실패: {e}")
        
        history.append({
            "timestamp": datetime.now().isoformat(),
            "mode": performance_data.get('measurement_mode', 'simple'),
            "performance_data": performance_data
        })
        
        # 최근 100개 기록만 유지
        history = history[-100:]
        
        try:
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(history, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.warning(f"히스토리 파일 저장 실패: {e}")
    
    def detect_regression(self, current_data: Dict[str, Any], threshold: float = 0.1) -> Dict[str, Any]:
        """성능 회귀 감지"""
        logger.info("성능 회귀 감지 분석 중...")
        
        if not self.baseline_file.exists():
            logger.warning("기준점 파일이 없습니다. 회귀 감지를 수행할 수 없습니다.")
            return {"status": "no_baseline", "regressions": []}
        
        try:
            with open(self.baseline_file, 'r', encoding='utf-8') as f:
                baseline_data = json.load(f)
        except Exception as e:
            logger.error(f"기준점 파일 읽기 실패: {e}")
            return {"status": "error", "error": str(e), "regressions": []}
        
        baseline_metrics = baseline_data["performance_data"]["metrics"]
        current_metrics = current_data["metrics"]
        
        regressions = []
        
        # 메모리 검색 성능 회귀 검사
        self._check_memory_search_regression(baseline_metrics, current_metrics, threshold, regressions)
        
        # 응답 품질 회귀 검사
        self._check_response_quality_regression(baseline_metrics, current_metrics, threshold, regressions)
        
        return {
            "status": "completed",
            "regressions": regressions,
            "threshold": threshold,
            "analysis_timestamp": datetime.now().isoformat()
        }
    
    def _check_memory_search_regression(self, baseline_metrics: Dict, current_metrics: Dict, 
                                      threshold: float, regressions: List[Dict]):
        """메모리 검색 성능 회귀 검사"""
        if "memory_search" not in baseline_metrics or "memory_search" not in current_metrics:
            return
        
        baseline_search = baseline_metrics["memory_search"]
        current_search = current_metrics["memory_search"]
        
        # LTM 검색 시간 증가 검사
        if (current_search.get("avg_ltm_search_time", 0) > 
            baseline_search.get("avg_ltm_search_time", 0) * (1 + threshold)):
            regressions.append({
                "metric": "avg_ltm_search_time",
                "baseline": baseline_search.get("avg_ltm_search_time", 0),
                "current": current_search.get("avg_ltm_search_time", 0),
                "regression_pct": ((current_search.get("avg_ltm_search_time", 0) / 
                                  max(baseline_search.get("avg_ltm_search_time", 1), 0.001)) - 1) * 100
            })
        
        # 속도 향상 비율 감소 검사
        if (current_search.get("avg_speedup_ratio", 0) < 
            baseline_search.get("avg_speedup_ratio", 0) * (1 - threshold)):
            regressions.append({
                "metric": "avg_speedup_ratio",
                "baseline": baseline_search.get("avg_speedup_ratio", 0),
                "current": current_search.get("avg_speedup_ratio", 0),
                "regression_pct": ((baseline_search.get("avg_speedup_ratio", 0) / 
                                  max(current_search.get("avg_speedup_ratio", 1), 0.001)) - 1) * 100
            })
    
    def _check_response_quality_regression(self, baseline_metrics: Dict, current_metrics: Dict,
                                         threshold: float, regressions: List[Dict]):
        """응답 품질 회귀 검사"""
        if "response_quality" not in baseline_metrics or "response_quality" not in current_metrics:
            return
        
        baseline_quality = baseline_metrics["response_quality"]
        current_quality = current_metrics["response_quality"]
        
        # 품질 점수 감소 검사
        if (current_quality.get("avg_quality_score", 0) < 
            baseline_quality.get("avg_quality_score", 0) * (1 - threshold)):
            regressions.append({
                "metric": "avg_quality_score",
                "baseline": baseline_quality.get("avg_quality_score", 0),
                "current": current_quality.get("avg_quality_score", 0),
                "regression_pct": ((baseline_quality.get("avg_quality_score", 0) / 
                                  max(current_quality.get("avg_quality_score", 1), 0.001)) - 1) * 100
            })
    
    def generate_report(self, performance_data: Optional[Dict[str, Any]] = None) -> str:
        """성능 리포트 생성"""
        if performance_data is None:
            if not self.baseline_file.exists():
                return "기준점 데이터가 없습니다."
            
            with open(self.baseline_file, 'r', encoding='utf-8') as f:
                baseline_data = json.load(f)
            performance_data = baseline_data["performance_data"]
        
        metrics = performance_data["metrics"]
        mode = performance_data.get("measurement_mode", "unknown")
        
        report = f"""# Greeum v2.0.5 통합 성능 기준점 리포트

## 측정 정보
- **측정 시간**: {performance_data.get('measurement_timestamp', 'N/A')}
- **Greeum 버전**: {performance_data.get('greeum_version', '2.0.5')}
- **측정 모드**: {mode.upper()}
- **샘플 크기**: {performance_data.get('sample_size', 'N/A')}
- **측정 소요 시간**: {performance_data.get('measurement_duration', 0):.2f}초

## 핵심 성능 지표

### 메모리 검색 성능
- **평균 LTM 검색 시간**: {metrics.get('memory_search', {}).get('avg_ltm_search_time', 'N/A'):.2f} ms
- **평균 캐시 검색 시간**: {metrics.get('memory_search', {}).get('avg_cache_search_time', 'N/A'):.2f} ms
- **평균 속도 향상**: {metrics.get('memory_search', {}).get('avg_speedup_ratio', 'N/A'):.2f}x"""

        # 정밀 모드인 경우 추가 통계 표시
        memory_search = metrics.get('memory_search', {})
        if 'p95_ltm_search_time' in memory_search:
            report += f"""
- **95% LTM 검색 시간**: {memory_search['p95_ltm_search_time']:.2f} ms
- **95% 캐시 검색 시간**: {memory_search['p95_cache_search_time']:.2f} ms"""

        report += f"""

### 응답 품질
- **평균 품질 점수**: {metrics.get('response_quality', {}).get('avg_quality_score', 'N/A'):.2f}
- **평균 컨텍스트 활용도**: {metrics.get('response_quality', {}).get('avg_context_usage', 'N/A'):.2f}
- **품질 일관성**: {metrics.get('response_quality', {}).get('quality_consistency', 'N/A'):.2f}

### v2.0.5 신규 기능"""
        
        # v2.0.5 기능들 (오류 처리 포함)
        quality_validation = metrics.get('quality_validation', {})
        if 'error' not in quality_validation:
            report += f"""
- **품질 검증 평균 시간**: {quality_validation.get('avg_validation_time', 'N/A'):.2f} ms"""
        
        duplicate_detection = metrics.get('duplicate_detection', {})
        if 'error' not in duplicate_detection:
            report += f"""
- **중복 감지 평균 시간**: {duplicate_detection.get('avg_detection_time', 'N/A'):.2f} ms"""
        
        usage_analytics = metrics.get('usage_analytics', {})
        if 'error' not in usage_analytics:
            report += f"""
- **사용량 분석 시간**: {usage_analytics.get('analysis_time', 'N/A'):.2f} ms"""

        report += f"""

### 시스템 리소스
- **메모리 사용량**: {metrics.get('system_resources', {}).get('memory_usage_mb', 'N/A'):.1f} MB
- **CPU 사용률**: {metrics.get('system_resources', {}).get('cpu_percent', 'N/A'):.1f}%

## 검증된 기준점 (v2.0.4)
- **T-GEN-001 품질 향상**: {self.verified_baselines['T-GEN-001']['quality_improvement_pct']}%
- **T-MEM-002 속도 향상**: {self.verified_baselines['T-MEM-002']['avg_speedup_ratio']}x
- **T-API-001 재질문 감소**: {self.verified_baselines['T-API-001']['reprompt_reduction_pct']}%

---
*Generated by UnifiedBaselineTracker v2.0.5*
"""
        
        return report


def main():
    """메인 실행 함수"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Greeum 통합 성능 기준점 측정')
    parser.add_argument('--mode', choices=['simple', 'comprehensive'], default='simple',
                       help='측정 모드 선택 (기본값: simple)')
    parser.add_argument('--sample-size', type=int, help='측정 샘플 크기')
    parser.add_argument('--save', action='store_true', help='기준점 데이터 저장')
    
    args = parser.parse_args()
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    logger.info(f"Greeum v2.0.5 통합 기준점 측정 시작 - 모드: {args.mode}")
    
    # 통합 기준점 추적기 초기화
    tracker = UnifiedBaselineTracker()
    
    # 성능 측정
    performance_data = tracker.measure_performance(
        mode=args.mode,
        sample_size=args.sample_size
    )
    
    # 기준점 저장 (옵션)
    if args.save:
        tracker.save_baseline(performance_data)
        logger.info("기준점 데이터 저장 완료")
    
    # 리포트 생성 및 출력
    report = tracker.generate_report(performance_data)
    
    # 리포트 파일 저장
    report_file = tracker.data_dir / f"unified_report_{args.mode}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report)
    
    logger.info(f"기준점 측정 완료 - 리포트: {report_file}")
    print(report)


if __name__ == "__main__":
    main()