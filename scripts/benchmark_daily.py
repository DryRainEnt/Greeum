#!/usr/bin/env python3
"""
Greeum v2.0.4 일간 벤치마크 스크립트
- 핵심 성능 지표 측정
- 일관된 성능 기준 유지
- 성능 regression 감지
"""

import time
import psutil
import gc
import json
import sys
from datetime import datetime
from pathlib import Path
from contextlib import contextmanager
from typing import Dict, List, Any

# Greeum 모듈 import
sys.path.insert(0, str(Path(__file__).parent.parent))
from greeum.core.database_manager import DatabaseManager
from greeum.core.block_manager import BlockManager
from greeum.text_utils import process_user_input
from greeum.embedding_models import get_embedding


class DailyBenchmark:
    """일간 성능 벤치마크 실행기"""
    
    def __init__(self):
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "version": "2.0.4",
            "platform": sys.platform,
            "python_version": sys.version,
            "metrics": {}
        }
        
        # 테스트용 임시 데이터베이스
        self.test_db_path = Path.home() / ".greeum_benchmark"
        self.test_db_path.mkdir(exist_ok=True)
        
        self.db_manager = DatabaseManager(str(self.test_db_path / "test.db"))
        self.block_manager = BlockManager(self.db_manager)
        
    @contextmanager
    def measure_time_and_memory(self, operation_name: str):
        """시간과 메모리 사용량 측정 컨텍스트"""
        # 가비지 컬렉션 강제 실행
        gc.collect()
        
        # 시작 상태 측정
        process = psutil.Process()
        start_time = time.perf_counter()
        start_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        try:
            yield
        finally:
            # 종료 상태 측정
            end_time = time.perf_counter()
            end_memory = process.memory_info().rss / 1024 / 1024  # MB
            
            # 결과 저장
            self.results["metrics"][operation_name] = {
                "duration_ms": round((end_time - start_time) * 1000, 2),
                "memory_delta_mb": round(end_memory - start_memory, 2),
                "peak_memory_mb": round(end_memory, 2)
            }
            
            print(f"✅ {operation_name}: {self.results['metrics'][operation_name]['duration_ms']}ms")
    
    def benchmark_memory_add_single(self):
        """단일 메모리 추가 성능"""
        test_content = "벤치마크 테스트용 메모리 블록입니다. 한글과 영어가 모두 포함되어 있습니다."
        
        with self.measure_time_and_memory("memory_add_single"):
            result = process_user_input(test_content)
            block_data = {
                "block_index": 0,
                "timestamp": datetime.now().isoformat(),
                "context": test_content,
                "keywords": result.get("keywords", []),
                "tags": result.get("tags", []),
                "embedding": result.get("embedding", []),
                "importance": 0.5,
                "hash": "test_hash",
                "prev_hash": ""
            }
            self.db_manager.add_block(block_data)
    
    def benchmark_memory_add_batch(self, count: int = 100):
        """배치 메모리 추가 성능"""
        test_contents = [
            f"배치 테스트 {i}번째 메모리 블록입니다. 성능 측정을 위한 테스트 데이터입니다."
            for i in range(count)
        ]
        
        with self.measure_time_and_memory(f"memory_add_batch_{count}"):
            for i, content in enumerate(test_contents):
                result = process_user_input(content)
                block_data = {
                    "block_index": i + 1,
                    "timestamp": datetime.now().isoformat(),
                    "context": content,
                    "keywords": result.get("keywords", []),
                    "tags": result.get("tags", []),
                    "embedding": result.get("embedding", []),
                    "importance": 0.5,
                    "hash": f"test_hash_{i}",
                    "prev_hash": f"test_hash_{i-1}" if i > 0 else ""
                }
                self.db_manager.add_block(block_data)
    
    def benchmark_memory_search_keyword(self):
        """키워드 검색 성능"""
        keywords = ["테스트", "성능", "벤치마크"]
        
        with self.measure_time_and_memory("memory_search_keyword"):
            results = self.db_manager.search_blocks_by_keyword(keywords, limit=10)
            # 결과 검증
            assert isinstance(results, list), "검색 결과가 리스트가 아닙니다"
    
    def benchmark_memory_search_embedding(self):
        """임베딩 검색 성능"""
        query = "성능 테스트 관련 내용"
        
        with self.measure_time_and_memory("memory_search_embedding"):
            try:
                embedding = get_embedding(query)
                results = self.db_manager.search_blocks_by_embedding(embedding, top_k=10)
                assert isinstance(results, list), "임베딩 검색 결과가 리스트가 아닙니다"
            except Exception as e:
                print(f"⚠️  임베딩 검색 실패: {e}")
                self.results["metrics"]["memory_search_embedding"] = {
                    "duration_ms": 0,
                    "memory_delta_mb": 0,
                    "peak_memory_mb": 0,
                    "error": str(e)
                }
    
    def benchmark_text_processing(self):
        """텍스트 처리 성능"""
        test_texts = [
            "한글 텍스트 처리 성능을 측정합니다. 키워드 추출과 임베딩 생성이 포함됩니다.",
            "English text processing performance measurement including keyword extraction and embedding generation.",
            "混合语言文本处理性能测试，包括中文、한글、English的处理能力测试。",
            "🎯 이모지와 특수문자 @#$% 처리 성능도 함께 측정합니다! (테스트용)",
            "Very long text content for performance testing. " * 100  # 긴 텍스트
        ]
        
        with self.measure_time_and_memory("text_processing_batch"):
            for text in test_texts:
                result = process_user_input(text)
                assert "keywords" in result, "키워드 추출 실패"
                assert "embedding" in result, "임베딩 생성 실패"
    
    def benchmark_database_operations(self):
        """데이터베이스 기본 연산 성능"""
        # 블록 추가
        with self.measure_time_and_memory("db_block_insert"):
            for i in range(50):
                block_data = {
                    "block_index": i + 200,
                    "timestamp": datetime.now().isoformat(),
                    "context": f"DB 성능 테스트 블록 {i}",
                    "keywords": ["DB", "테스트"],
                    "tags": ["성능"],
                    "embedding": [0.1] * 128,
                    "importance": 0.5,
                    "hash": f"db_test_{i}",
                    "prev_hash": f"db_test_{i-1}" if i > 0 else ""
                }
                self.db_manager.add_block(block_data)
        
        # 블록 조회
        with self.measure_time_and_memory("db_block_retrieve"):
            for i in range(10):
                block = self.db_manager.get_block(i + 200)
                assert block is not None or i >= 200, f"블록 {i+200} 조회 실패"
        
        # 마지막 블록 정보 조회
        with self.measure_time_and_memory("db_last_block_info"):
            for _ in range(20):
                last_info = self.db_manager.get_last_block_info()
                assert last_info is not None, "마지막 블록 정보 조회 실패"
    
    def benchmark_concurrent_simulation(self):
        """동시 접근 시뮬레이션 (단일 프로세스)"""
        import threading
        import queue
        
        results_queue = queue.Queue()
        errors_queue = queue.Queue()
        
        def worker(worker_id: int):
            """워커 스레드 함수"""
            try:
                for i in range(10):
                    # 메모리 추가
                    content = f"동시접근 테스트 워커{worker_id} 작업{i}"
                    result = process_user_input(content)
                    
                    # 짧은 대기 (실제 사용 패턴 시뮬레이션)
                    time.sleep(0.01)
                    
                results_queue.put(f"worker_{worker_id}_completed")
            except Exception as e:
                errors_queue.put(f"worker_{worker_id}_error: {e}")
        
        with self.measure_time_and_memory("concurrent_simulation"):
            threads = []
            worker_count = 5
            
            # 스레드 시작
            for i in range(worker_count):
                thread = threading.Thread(target=worker, args=(i,))
                threads.append(thread)
                thread.start()
            
            # 모든 스레드 완료 대기
            for thread in threads:
                thread.join(timeout=30)  # 30초 타임아웃
            
            # 결과 검증
            completed_workers = []
            while not results_queue.empty():
                completed_workers.append(results_queue.get())
            
            errors = []
            while not errors_queue.empty():
                errors.append(errors_queue.get())
            
            print(f"   완료된 워커: {len(completed_workers)}/{worker_count}")
            if errors:
                print(f"   오류: {errors}")
    
    def calculate_performance_score(self) -> float:
        """종합 성능 점수 계산 (0-100)"""
        metrics = self.results["metrics"]
        score = 100.0
        
        # 각 지표별 가중치 및 기준값
        benchmarks = {
            "memory_add_single": {"weight": 0.2, "target_ms": 50, "penalty_per_ms": 0.5},
            "memory_add_batch_100": {"weight": 0.3, "target_ms": 3000, "penalty_per_ms": 0.01},
            "memory_search_keyword": {"weight": 0.15, "target_ms": 100, "penalty_per_ms": 0.3},
            "memory_search_embedding": {"weight": 0.15, "target_ms": 200, "penalty_per_ms": 0.2},
            "text_processing_batch": {"weight": 0.1, "target_ms": 500, "penalty_per_ms": 0.1},
            "concurrent_simulation": {"weight": 0.1, "target_ms": 2000, "penalty_per_ms": 0.05}
        }
        
        for metric_name, benchmark in benchmarks.items():
            if metric_name in metrics and "duration_ms" in metrics[metric_name]:
                duration = metrics[metric_name]["duration_ms"]
                target = benchmark["target_ms"]
                
                if duration > target:
                    # 목표치를 초과한 경우 감점
                    penalty = (duration - target) * benchmark["penalty_per_ms"] * benchmark["weight"]
                    score -= penalty
                else:
                    # 목표치보다 빠른 경우 보너스
                    bonus = (target - duration) / target * 10 * benchmark["weight"]
                    score += bonus
        
        return max(0, min(100, score))
    
    def generate_recommendations(self) -> List[str]:
        """성능 개선 권장사항 생성"""
        recommendations = []
        metrics = self.results["metrics"]
        
        # 메모리 추가 성능 검사
        if "memory_add_single" in metrics:
            duration = metrics["memory_add_single"]["duration_ms"]
            if duration > 100:
                recommendations.append(f"단일 메모리 추가가 {duration}ms로 느림. 텍스트 처리 최적화 검토 필요")
        
        # 검색 성능 검사
        if "memory_search_keyword" in metrics:
            duration = metrics["memory_search_keyword"]["duration_ms"]
            if duration > 200:
                recommendations.append(f"키워드 검색이 {duration}ms로 느림. 인덱스 최적화 검토 필요")
        
        # 메모리 사용량 검사
        peak_memories = [m.get("peak_memory_mb", 0) for m in metrics.values() if isinstance(m, dict)]
        if peak_memories and max(peak_memories) > 100:
            recommendations.append(f"최대 메모리 사용량 {max(peak_memories):.1f}MB. 메모리 최적화 검토 필요")
        
        # 에러 검사
        error_metrics = [name for name, data in metrics.items() 
                        if isinstance(data, dict) and "error" in data]
        if error_metrics:
            recommendations.append(f"오류 발생 지표: {', '.join(error_metrics)}. 안정성 검토 필요")
        
        if not recommendations:
            recommendations.append("모든 성능 지표가 양호합니다. 현재 상태 유지 권장")
        
        return recommendations
    
    def run_all_benchmarks(self):
        """모든 벤치마크 실행"""
        print("🚀 Greeum v2.0.4 Daily Benchmark 시작")
        print(f"   날짜: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"   플랫폼: {sys.platform}")
        print(f"   Python: {sys.version.split()[0]}")
        print()
        
        try:
            # 개별 벤치마크 실행
            self.benchmark_memory_add_single()
            self.benchmark_memory_add_batch(100)
            self.benchmark_memory_search_keyword()
            self.benchmark_memory_search_embedding()
            self.benchmark_text_processing()
            self.benchmark_database_operations()
            self.benchmark_concurrent_simulation()
            
            # 성능 점수 계산
            score = self.calculate_performance_score()
            self.results["performance_score"] = round(score, 1)
            
            # 권장사항 생성
            recommendations = self.generate_recommendations()
            self.results["recommendations"] = recommendations
            
            print()
            print(f"📊 종합 성능 점수: {score:.1f}/100")
            print("💡 권장사항:")
            for rec in recommendations:
                print(f"   - {rec}")
            
        except Exception as e:
            print(f"❌ 벤치마크 실행 중 오류: {e}")
            self.results["error"] = str(e)
        
        finally:
            # 결과 저장
            self.save_results()
            
            # 정리
            self.cleanup()
    
    def save_results(self):
        """결과를 파일로 저장"""
        results_dir = Path(__file__).parent.parent / "benchmark_results"
        results_dir.mkdir(exist_ok=True)
        
        # 타임스탬프 기반 파일명
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results_file = results_dir / f"daily_benchmark_{timestamp}.json"
        
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, ensure_ascii=False, indent=2)
        
        print(f"📁 결과 저장: {results_file}")
        
        # 최신 결과도 별도 저장 (대시보드용)
        latest_file = results_dir / "latest_benchmark.json"
        with open(latest_file, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, ensure_ascii=False, indent=2)
    
    def cleanup(self):
        """테스트 파일 정리"""
        try:
            import shutil
            if self.test_db_path.exists():
                shutil.rmtree(self.test_db_path)
        except Exception as e:
            print(f"⚠️  정리 중 오류: {e}")


def main():
    """메인 실행 함수"""
    benchmark = DailyBenchmark()
    benchmark.run_all_benchmarks()


if __name__ == "__main__":
    main()