#!/usr/bin/env python3
"""
Greeum 성능 기준점 추적 및 회귀 감지 시스템

이 모듈은 Greeum의 핵심 성능 지표를 추적하고, 회귀 이슈를 자동으로 감지합니다.
기존 T-GEN-001, T-MEM-002, T-API-001 메트릭을 기반으로 확장된 성능 측정을 제공합니다.
"""

import os
import sys
import json
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import statistics
from pathlib import Path

# 상위 디렉토리를 path에 추가
sys.path.insert(0, os.path.abspath('../../..'))

from greeum import DatabaseManager, BlockManager, STMManager, CacheManager
from greeum.core.prompt_wrapper import PromptWrapper
from greeum.core.quality_validator import QualityValidator
from greeum.core.duplicate_detector import DuplicateDetector
from greeum.core.usage_analytics import UsageAnalytics
from greeum.embedding_models import get_embedding

logger = logging.getLogger(__name__)

class BaselineTracker:
    """Greeum 성능 기준점 추적 및 회귀 감지 클래스"""
    
    def __init__(self, data_dir: str = "tests/performance_suite/results/baselines"):
        """
        기준점 추적기 초기화
        
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
        
        # v2.0.5 신규 컴포넌트
        self.quality_validator = QualityValidator()
        self.duplicate_detector = DuplicateDetector(self.db_manager)
        self.usage_analytics = UsageAnalytics()
        
        # 기준점 데이터 파일 경로
        self.baseline_file = self.data_dir / "greeum_v205_baseline.json"
        self.history_file = self.data_dir / "performance_history.json"
        
        # 기존 검증된 기준점 (v2.0.4 기반)
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
        
        logger.info(f"BaselineTracker 초기화 완료 - 데이터 디렉토리: {self.data_dir}")
    
    def measure_current_performance(self, sample_size: int = 50) -> Dict[str, Any]:
        """
        현재 Greeum v2.0.5 성능 전면 측정
        
        Args:
            sample_size: 테스트 샘플 크기
            
        Returns:
            측정된 성능 지표 딕셔너리
        """
        logger.info(f"현재 성능 측정 시작 - 샘플 크기: {sample_size}")
        start_time = time.time()
        
        performance_data = {
            "measurement_timestamp": datetime.now().isoformat(),
            "greeum_version": "2.0.5",
            "sample_size": sample_size,
            "metrics": {}
        }
        
        # 1. 메모리 검색 성능 측정 (T-MEM-002 확장)
        performance_data["metrics"]["memory_search"] = self._measure_memory_search_performance(sample_size)
        
        # 2. 응답 품질 측정 (T-GEN-001 확장)  
        performance_data["metrics"]["response_quality"] = self._measure_response_quality(sample_size // 5)
        
        # 3. v2.0.5 신규 기능 성능 측정 (에러 처리)
        try:
            performance_data["metrics"]["quality_validation"] = self._measure_quality_validation(sample_size)
        except Exception as e:
            logger.warning(f"품질 검증 측정 실패: {e}")
            performance_data["metrics"]["quality_validation"] = {"error": str(e)}
        
        try:
            performance_data["metrics"]["duplicate_detection"] = self._measure_duplicate_detection(sample_size)
        except Exception as e:
            logger.warning(f"중복 감지 측정 실패: {e}")
            performance_data["metrics"]["duplicate_detection"] = {"error": str(e)}
        
        try:
            performance_data["metrics"]["usage_analytics"] = self._measure_usage_analytics(sample_size)
        except Exception as e:
            logger.warning(f"사용량 분석 측정 실패: {e}")
            performance_data["metrics"]["usage_analytics"] = {"error": str(e)}
        
        # 4. 시스템 리소스 사용량 측정
        performance_data["metrics"]["system_resources"] = self._measure_system_resources()
        
        total_time = time.time() - start_time
        performance_data["measurement_duration"] = total_time
        
        logger.info(f"성능 측정 완료 - 소요 시간: {total_time:.2f}초")
        return performance_data
    
    def _measure_memory_search_performance(self, sample_size: int) -> Dict[str, Any]:
        """메모리 검색 성능 측정"""
        logger.info("메모리 검색 성능 측정 중...")
        
        # 테스트용 메모리 블록 준비 (정확한 측정을 위한 충분한 데이터)
        self._prepare_test_memory_blocks(min(sample_size * 10, 2000))
        
        search_queries = [
            "프로젝트 진행 상황",
            "개발 계획",
            "성능 개선",
            "메모리 최적화",
            "사용자 피드백",
            "버그 수정",
            "새로운 기능",
            "테스트 결과"
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
        
        return {
            "avg_ltm_search_time": statistics.mean(ltm_times),
            "p95_ltm_search_time": statistics.quantiles(ltm_times, n=20)[18],  # 95th percentile
            "avg_cache_search_time": statistics.mean(cache_times),
            "p95_cache_search_time": statistics.quantiles(cache_times, n=20)[18],
            "avg_speedup_ratio": statistics.mean(ltm_times) / statistics.mean(cache_times),
            "sample_count": sample_size
        }
    
    def _measure_response_quality(self, sample_size: int) -> Dict[str, Any]:
        """응답 품질 측정 (T-GEN-001 기반)"""
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
            
            # Greeum 메모리 활용 프롬프트 생성
            enhanced_prompt = self.prompt_wrapper.compose_prompt(query, token_budget=1000)
            
            # 품질 검증 (v2.0.5 신규 기능)
            quality_result = self.quality_validator.validate_memory_quality(enhanced_prompt)
            quality_scores.append(quality_result.get('overall_score', 0))
            
            # 컨텍스트 활용도 측정
            context_info_count = enhanced_prompt.count('관련 기억:') + enhanced_prompt.count('최근 기억:')
            context_usage_scores.append(context_info_count)
        
        # 안전한 통계 계산
        avg_quality = statistics.mean(quality_scores) if quality_scores else 0
        avg_context = statistics.mean(context_usage_scores) if context_usage_scores else 0
        
        # 일관성 계산 (zero division 방지)
        if avg_quality > 0 and len(quality_scores) > 1:
            quality_consistency = 1 - (statistics.stdev(quality_scores) / avg_quality)
        else:
            quality_consistency = 1.0  # 완전 일관성으로 설정
        
        return {
            "avg_quality_score": avg_quality,
            "avg_context_usage": avg_context,
            "quality_consistency": quality_consistency,
            "sample_count": sample_size
        }
    
    def _measure_quality_validation(self, sample_size: int) -> Dict[str, Any]:
        """품질 검증 성능 측정 (v2.0.5 신규)"""
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
            
            start_time = time.time()
            result = self.quality_validator.validate_memory_quality(content)
            validation_time = time.time() - start_time
            
            validation_times.append(validation_time * 1000)  # ms 변환
            validation_scores.append(result.get('overall_score', 0))
        
        return {
            "avg_validation_time": statistics.mean(validation_times),
            "avg_quality_score": statistics.mean(validation_scores),
            "validation_throughput": sample_size / (sum(validation_times) / 1000),  # validations/sec
            "sample_count": sample_size
        }
    
    def _measure_duplicate_detection(self, sample_size: int) -> Dict[str, Any]:
        """중복 감지 성능 측정 (v2.0.5 신규)"""
        logger.info("중복 감지 성능 측정 중...")
        
        # 중복 테스트용 컨텐츠 준비
        base_content = "프로젝트 개발 진행 상황"
        test_contents = []
        
        # 50% 중복, 50% 고유 컨텐츠 생성
        for i in range(sample_size):
            if i % 2 == 0:
                # 중복 컨텐츠 (약간의 변형)
                content = f"{base_content} - 업데이트 {i//2}"
            else:
                # 고유 컨텐츠
                content = f"고유한 기능 구현 완료 - 기능 {i}"
            test_contents.append(content)
        
        detection_times = []
        duplicate_detected = 0
        
        for content in test_contents:
            start_time = time.time()
            duplicate_result = self.duplicate_detector.check_duplicate(content)
            detection_time = time.time() - start_time
            
            detection_times.append(detection_time * 1000)  # ms 변환
            if duplicate_result.get('is_duplicate', False):
                duplicate_detected += 1
        
        return {
            "avg_detection_time": statistics.mean(detection_times),
            "detection_accuracy": (duplicate_detected / (sample_size // 2)) * 100,  # 50% should be duplicates
            "detection_throughput": sample_size / (sum(detection_times) / 1000),  # detections/sec
            "sample_count": sample_size
        }
    
    def _measure_usage_analytics(self, sample_size: int) -> Dict[str, Any]:
        """사용량 분석 성능 측정 (v2.0.5 신규)"""
        logger.info("사용량 분석 성능 측정 중...")
        
        # 테스트 사용량 데이터 생성
        for i in range(sample_size):
            self.usage_analytics.record_usage(
                operation=f"test_operation_{i % 5}",
                duration=0.1 + (i % 10) * 0.05,
                memory_used=100 + (i % 50) * 10
            )
        
        # 분석 성능 측정
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
    
    def _measure_system_resources(self) -> Dict[str, Any]:
        """시스템 리소스 사용량 측정"""
        try:
            import psutil
            
            # 현재 프로세스 정보
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
    
    def _prepare_test_memory_blocks(self, count: int):
        """테스트용 메모리 블록 준비"""
        logger.info(f"테스트용 메모리 블록 {count}개 준비 중...")
        
        base_contexts = [
            "프로젝트 개발 진행 상황",
            "새로운 기능 구현",
            "성능 최적화 작업",
            "버그 수정 완료",
            "사용자 피드백 반영",
            "테스트 결과 분석",
            "코드 리뷰 진행",
            "문서 업데이트"
        ]
        
        for i in range(count):
            context = f"{base_contexts[i % len(base_contexts)]} - 작업 {i}"
            keywords = context.split()[:3]
            tags = [f"tag_{i % 5}", "test"]
            embedding = get_embedding(context)
            importance = 0.5 + (i % 5) * 0.1
            
            self.block_manager.add_block(
                context=context,
                keywords=keywords,
                tags=tags,
                embedding=embedding,
                importance=importance,
                metadata={"test_block": True, "index": i}
            )
    
    def save_baseline(self, performance_data: Dict[str, Any]):
        """기준점 데이터 저장"""
        logger.info(f"기준점 데이터 저장: {self.baseline_file}")
        
        baseline_data = {
            "created_at": datetime.now().isoformat(),
            "greeum_version": "2.0.5",
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
            with open(self.history_file, 'r', encoding='utf-8') as f:
                history = json.load(f)
        
        history.append({
            "timestamp": datetime.now().isoformat(),
            "performance_data": performance_data
        })
        
        # 최근 100개 기록만 유지
        history = history[-100:]
        
        with open(self.history_file, 'w', encoding='utf-8') as f:
            json.dump(history, f, ensure_ascii=False, indent=2)
    
    def detect_regression(self, current_data: Dict[str, Any], threshold: float = 0.1) -> Dict[str, Any]:
        """성능 회귀 감지"""
        logger.info("성능 회귀 감지 분석 중...")
        
        if not self.baseline_file.exists():
            logger.warning("기준점 파일이 없습니다. 회귀 감지를 수행할 수 없습니다.")
            return {"status": "no_baseline", "regressions": []}
        
        with open(self.baseline_file, 'r', encoding='utf-8') as f:
            baseline_data = json.load(f)
        
        baseline_metrics = baseline_data["performance_data"]["metrics"]
        current_metrics = current_data["metrics"]
        
        regressions = []
        
        # 메모리 검색 성능 회귀 검사
        if "memory_search" in baseline_metrics and "memory_search" in current_metrics:
            baseline_search = baseline_metrics["memory_search"]
            current_search = current_metrics["memory_search"]
            
            # 검색 시간 증가 검사
            if current_search["avg_ltm_search_time"] > baseline_search["avg_ltm_search_time"] * (1 + threshold):
                regressions.append({
                    "metric": "avg_ltm_search_time",
                    "baseline": baseline_search["avg_ltm_search_time"],
                    "current": current_search["avg_ltm_search_time"],
                    "regression_pct": ((current_search["avg_ltm_search_time"] / baseline_search["avg_ltm_search_time"]) - 1) * 100
                })
        
        # 응답 품질 회귀 검사  
        if "response_quality" in baseline_metrics and "response_quality" in current_metrics:
            baseline_quality = baseline_metrics["response_quality"]
            current_quality = current_metrics["response_quality"]
            
            # 품질 점수 감소 검사
            if current_quality["avg_quality_score"] < baseline_quality["avg_quality_score"] * (1 - threshold):
                regressions.append({
                    "metric": "avg_quality_score",
                    "baseline": baseline_quality["avg_quality_score"],
                    "current": current_quality["avg_quality_score"],
                    "regression_pct": ((baseline_quality["avg_quality_score"] / current_quality["avg_quality_score"]) - 1) * 100
                })
        
        return {
            "status": "completed",
            "regressions": regressions,
            "threshold": threshold,
            "analysis_timestamp": datetime.now().isoformat()
        }
    
    def generate_baseline_report(self) -> str:
        """기준점 리포트 생성"""
        if not self.baseline_file.exists():
            return "기준점 데이터가 없습니다."
        
        with open(self.baseline_file, 'r', encoding='utf-8') as f:
            baseline_data = json.load(f)
        
        performance_data = baseline_data["performance_data"]
        metrics = performance_data["metrics"]
        
        report = f"""# Greeum v2.0.5 성능 기준점 리포트
        
## 측정 정보
- **측정 시간**: {performance_data['measurement_timestamp']}
- **Greeum 버전**: {performance_data['greeum_version']}
- **샘플 크기**: {performance_data['sample_size']}
- **측정 소요 시간**: {performance_data['measurement_duration']:.2f}초

## 핵심 성능 지표

### 메모리 검색 성능
- **평균 LTM 검색 시간**: {metrics['memory_search']['avg_ltm_search_time']:.2f} ms
- **95% LTM 검색 시간**: {metrics['memory_search']['p95_ltm_search_time']:.2f} ms
- **평균 캐시 검색 시간**: {metrics['memory_search']['avg_cache_search_time']:.2f} ms
- **평균 속도 향상**: {metrics['memory_search']['avg_speedup_ratio']:.2f}x

### 응답 품질
- **평균 품질 점수**: {metrics['response_quality']['avg_quality_score']:.2f}
- **평균 컨텍스트 활용도**: {metrics['response_quality']['avg_context_usage']:.2f}
- **품질 일관성**: {metrics['response_quality']['quality_consistency']:.2f}

### v2.0.5 신규 기능
- **품질 검증 평균 시간**: {metrics.get('quality_validation', {}).get('avg_validation_time', 'N/A')} ms
- **중복 감지 평균 시간**: {metrics.get('duplicate_detection', {}).get('avg_detection_time', 'N/A')} ms
- **사용량 분석 시간**: {metrics.get('usage_analytics', {}).get('analysis_time', 'N/A')} ms

### 시스템 리소스
- **메모리 사용량**: {metrics.get('system_resources', {}).get('memory_usage_mb', 'N/A')} MB
- **CPU 사용률**: {metrics.get('system_resources', {}).get('cpu_percent', 'N/A')}%

## 검증된 기준점 (v2.0.4)
- **T-GEN-001 품질 향상**: {self.verified_baselines['T-GEN-001']['quality_improvement_pct']}%
- **T-MEM-002 속도 향상**: {self.verified_baselines['T-MEM-002']['avg_speedup_ratio']}x
- **T-API-001 재질문 감소**: {self.verified_baselines['T-API-001']['reprompt_reduction_pct']}%
"""
        
        return report

def main():
    """메인 실행 함수"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    logger.info("Greeum v2.0.5 기준점 측정 시작")
    
    # 기준점 추적기 초기화
    tracker = BaselineTracker()
    
    # 현재 성능 측정 (정확한 지표를 위한 충분한 샘플)
    performance_data = tracker.measure_current_performance(sample_size=200)
    
    # 기준점 저장
    tracker.save_baseline(performance_data)
    
    # 리포트 생성
    report = tracker.generate_baseline_report()
    
    # 리포트 파일 저장
    report_file = tracker.data_dir / f"baseline_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report)
    
    logger.info(f"기준점 측정 완료 - 리포트: {report_file}")
    print(report)

if __name__ == "__main__":
    main()