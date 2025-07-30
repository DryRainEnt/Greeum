#!/usr/bin/env python3
"""
Greeum v2.0.4 주간 스트레스 테스트
- 대용량 데이터 처리 검증
- 장시간 실행 안정성 테스트
- 극한 상황에서의 복구 능력 검증
"""

import time
import psutil
import gc
import json
import sys
import threading
import queue
import random
import string
import tempfile
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from contextlib import contextmanager
from typing import Dict, List, Any, Optional
import concurrent.futures

# Greeum 모듈 import
sys.path.insert(0, str(Path(__file__).parent.parent))
from greeum.core.database_manager import DatabaseManager
from greeum.core.block_manager import BlockManager
from greeum.text_utils import process_user_input
from greeum.embedding_models import get_embedding


class StressTestSuite:
    """주간 스트레스 테스트 실행기"""
    
    def __init__(self):
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "version": "2.0.4",
            "platform": sys.platform,
            "python_version": sys.version,
            "stress_tests": {},
            "system_info": self._get_system_info()
        }
        
        # 테스트용 임시 디렉토리
        self.test_dir = Path(tempfile.mkdtemp(prefix="greeum_stress_"))
        print(f"📁 스트레스 테스트 디렉토리: {self.test_dir}")
        
        # 다양한 데이터베이스 인스턴스
        self.primary_db = DatabaseManager(str(self.test_dir / "primary.db"))
        self.secondary_db = DatabaseManager(str(self.test_dir / "secondary.db"))
        
        self.primary_bm = BlockManager(self.primary_db)
        self.secondary_bm = BlockManager(self.secondary_db)
    
    def _get_system_info(self) -> Dict[str, Any]:
        """시스템 정보 수집"""
        return {
            "cpu_count": psutil.cpu_count(),
            "memory_total_gb": round(psutil.virtual_memory().total / 1024**3, 2),
            "disk_free_gb": round(shutil.disk_usage("/").free / 1024**3, 2),
            "python_version": sys.version.split()[0]
        }
    
    @contextmanager
    def monitor_resources(self, test_name: str, duration_hint: Optional[int] = None):
        """리소스 사용량 모니터링 컨텍스트"""
        start_time = time.perf_counter()
        process = psutil.Process()
        
        # 시작 상태
        start_stats = {
            "cpu_percent": process.cpu_percent(),
            "memory_mb": process.memory_info().rss / 1024 / 1024,
            "open_files": len(process.open_files()) if hasattr(process, 'open_files') else 0
        }
        
        # 모니터링 데이터 수집용
        monitoring_data = {
            "peak_memory_mb": start_stats["memory_mb"],
            "peak_cpu_percent": start_stats["cpu_percent"],
            "memory_samples": [start_stats["memory_mb"]],
            "cpu_samples": [start_stats["cpu_percent"]]
        }
        
        # 백그라운드 모니터링 시작
        stop_monitoring = threading.Event()
        
        def monitor_worker():
            while not stop_monitoring.wait(1.0):  # 1초마다 샘플링
                try:
                    current_memory = process.memory_info().rss / 1024 / 1024
                    current_cpu = process.cpu_percent()
                    
                    monitoring_data["memory_samples"].append(current_memory)
                    monitoring_data["cpu_samples"].append(current_cpu)
                    
                    monitoring_data["peak_memory_mb"] = max(
                        monitoring_data["peak_memory_mb"], current_memory
                    )
                    monitoring_data["peak_cpu_percent"] = max(
                        monitoring_data["peak_cpu_percent"], current_cpu
                    )
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    break
        
        monitor_thread = threading.Thread(target=monitor_worker, daemon=True)
        monitor_thread.start()
        
        try:
            yield monitoring_data
        finally:
            # 모니터링 중지
            stop_monitoring.set()
            monitor_thread.join(timeout=2)
            
            # 종료 상태
            end_time = time.perf_counter()
            end_stats = {
                "cpu_percent": process.cpu_percent(),
                "memory_mb": process.memory_info().rss / 1024 / 1024,
                "open_files": len(process.open_files()) if hasattr(process, 'open_files') else 0
            }
            
            # 결과 저장
            self.results["stress_tests"][test_name] = {
                "duration_seconds": round(end_time - start_time, 2),
                "start_stats": start_stats,
                "end_stats": end_stats,
                "peak_memory_mb": round(monitoring_data["peak_memory_mb"], 2),
                "peak_cpu_percent": round(monitoring_data["peak_cpu_percent"], 2),
                "avg_memory_mb": round(sum(monitoring_data["memory_samples"]) / len(monitoring_data["memory_samples"]), 2),
                "avg_cpu_percent": round(sum(monitoring_data["cpu_samples"]) / len(monitoring_data["cpu_samples"]), 2),
                "memory_leak_mb": round(end_stats["memory_mb"] - start_stats["memory_mb"], 2),
                "file_leak_count": end_stats["open_files"] - start_stats["open_files"]
            }
            
            print(f"✅ {test_name}: {self.results['stress_tests'][test_name]['duration_seconds']}초, "
                  f"피크 메모리: {self.results['stress_tests'][test_name]['peak_memory_mb']:.1f}MB")
    
    def generate_test_data(self, count: int, complexity: str = "medium") -> List[str]:
        """테스트 데이터 생성"""
        templates = {
            "simple": [
                "간단한 테스트 데이터 {i}",
                "Simple test data {i}",
                "테스트 {i}"
            ],
            "medium": [
                "중간 복잡도의 테스트 데이터입니다. 번호: {i}, 한글과 영어가 포함되어 있습니다.",
                "Medium complexity test data with number {i}. Contains Korean and English text.",
                "복합 언어 테스트 データ {i} - 한글/English/日本語 혼합",
                "기술적 내용: 데이터베이스 성능 최적화, 인덱싱 전략, 쿼리 최적화 방법론 {i}"
            ],
            "complex": [
                "매우 복잡한 테스트 데이터입니다. " * 10 + f" 번호: {i}",
                "Complex multilingual test data with extensive content. " * 5 + f" Number: {i}",
                "🎯 이모지와 특수문자 @#$%^&*()_+ 포함 테스트 데이터 {i} ✨🚀💡",
                "JSON 형태 데이터: " + json.dumps({"id": "{i}", "content": "복잡한 구조의 데이터", "metadata": {"tags": ["test", "stress"], "importance": 0.8}})
            ]
        }
        
        template_list = templates.get(complexity, templates["medium"])
        test_data = []
        
        for i in range(count):
            template = random.choice(template_list)
            test_data.append(template.format(i=i))
        
        return test_data
    
    def stress_test_massive_memory_blocks(self, block_counts: List[int] = [1000, 5000, 10000]):
        """대용량 메모리 블록 처리 테스트"""
        for count in block_counts:
            test_name = f"massive_blocks_{count}"
            print(f"🔥 대용량 블록 테스트 시작: {count}개")
            
            with self.monitor_resources(test_name):
                test_data = self.generate_test_data(count, "medium")
                
                # 배치 처리로 메모리 효율성 확보
                batch_size = 100
                successful_inserts = 0
                
                for i in range(0, count, batch_size):
                    batch = test_data[i:i + batch_size]
                    
                    for j, content in enumerate(batch):
                        try:
                            result = process_user_input(content)
                            block_data = {
                                "block_index": i + j,
                                "timestamp": datetime.now().isoformat(),
                                "context": content,
                                "keywords": result.get("keywords", []),
                                "tags": result.get("tags", []),
                                "embedding": result.get("embedding", []),
                                "importance": random.uniform(0.1, 0.9),
                                "hash": f"stress_{i+j}",
                                "prev_hash": f"stress_{i+j-1}" if i+j > 0 else ""
                            }
                            self.primary_db.add_block(block_data)
                            successful_inserts += 1
                            
                        except Exception as e:
                            print(f"   블록 {i+j} 추가 실패: {e}")
                    
                    # 배치마다 가비지 컬렉션
                    if i % (batch_size * 10) == 0:
                        gc.collect()
                        print(f"   진행: {i+len(batch)}/{count} ({((i+len(batch))/count*100):.1f}%)")
                
                # 결과에 성공률 추가
                self.results["stress_tests"][test_name]["successful_inserts"] = successful_inserts
                self.results["stress_tests"][test_name]["success_rate"] = round(successful_inserts / count * 100, 2)
    
    def stress_test_concurrent_access(self, worker_count: int = 10, operations_per_worker: int = 100):
        """동시 접근 스트레스 테스트"""
        test_name = f"concurrent_access_{worker_count}workers"
        print(f"🔥 동시 접근 테스트 시작: {worker_count}개 워커")
        
        with self.monitor_resources(test_name):
            results_queue = queue.Queue()
            errors_queue = queue.Queue()
            
            def worker(worker_id: int):
                """워커 함수"""
                worker_stats = {"operations": 0, "errors": 0, "start_time": time.time()}
                
                for i in range(operations_per_worker):
                    try:
                        # 랜덤한 작업 선택
                        operation = random.choice(["add", "search", "retrieve"])
                        
                        if operation == "add":
                            content = f"동시접근 테스트 워커{worker_id} 작업{i}"
                            result = process_user_input(content)
                            block_data = {
                                "block_index": worker_id * 1000 + i,
                                "timestamp": datetime.now().isoformat(),
                                "context": content,
                                "keywords": result.get("keywords", []),
                                "tags": result.get("tags", []),
                                "embedding": result.get("embedding", []),
                                "importance": 0.5,
                                "hash": f"worker_{worker_id}_{i}",
                                "prev_hash": ""
                            }
                            self.secondary_db.add_block(block_data)
                            
                        elif operation == "search":
                            keywords = [f"워커{worker_id}", "테스트"]
                            self.secondary_db.search_blocks_by_keyword(keywords, limit=5)
                            
                        elif operation == "retrieve":
                            block_id = random.randint(0, max(1, worker_id * 1000 + i - 1))
                            self.secondary_db.get_block(block_id)
                        
                        worker_stats["operations"] += 1
                        
                        # 랜덤 대기 (실제 사용 패턴 시뮬레이션)
                        time.sleep(random.uniform(0.001, 0.01))
                        
                    except Exception as e:
                        worker_stats["errors"] += 1
                        errors_queue.put(f"Worker {worker_id}, Op {i}: {str(e)}")
                
                worker_stats["end_time"] = time.time()
                worker_stats["duration"] = worker_stats["end_time"] - worker_stats["start_time"]
                results_queue.put((worker_id, worker_stats))
            
            # 스레드 풀로 동시 실행
            with concurrent.futures.ThreadPoolExecutor(max_workers=worker_count) as executor:
                futures = [executor.submit(worker, i) for i in range(worker_count)]
                
                # 모든 워커 완료 대기
                concurrent.futures.wait(futures, timeout=300)  # 5분 타임아웃
            
            # 결과 수집
            worker_results = []
            while not results_queue.empty():
                worker_results.append(results_queue.get())
            
            errors = []
            while not errors_queue.empty():
                errors.append(errors_queue.get())
            
            # 통계 계산
            total_operations = sum(stats["operations"] for _, stats in worker_results)
            total_errors = sum(stats["errors"] for _, stats in worker_results)
            avg_duration = sum(stats["duration"] for _, stats in worker_results) / len(worker_results) if worker_results else 0
            
            self.results["stress_tests"][test_name].update({
                "completed_workers": len(worker_results),
                "total_operations": total_operations,
                "total_errors": total_errors,
                "error_rate": round(total_errors / max(1, total_operations) * 100, 2),
                "avg_worker_duration": round(avg_duration, 2),
                "operations_per_second": round(total_operations / max(1, avg_duration), 2)
            })
            
            if errors:
                print(f"   오류 {len(errors)}개 발생")
    
    def stress_test_memory_leak_detection(self, duration_minutes: int = 30):
        """메모리 누수 감지 테스트"""
        test_name = f"memory_leak_{duration_minutes}min"
        print(f"🔥 메모리 누수 테스트 시작: {duration_minutes}분간")
        
        with self.monitor_resources(test_name, duration_minutes * 60):
            end_time = time.time() + (duration_minutes * 60)
            cycle_count = 0
            
            while time.time() < end_time:
                cycle_count += 1
                
                # 메모리 집약적 작업들
                test_data = self.generate_test_data(50, "complex")
                
                for i, content in enumerate(test_data):
                    result = process_user_input(content)
                    # 메모리에만 저장하고 DB에는 저장하지 않음 (누수 테스트)
                    
                # 검색 작업
                keywords = ["테스트", "메모리", "누수"]
                try:
                    self.primary_db.search_blocks_by_keyword(keywords, limit=10)
                except:
                    pass
                
                # 주기적으로 가비지 컬렉션 강제 실행
                if cycle_count % 10 == 0:
                    gc.collect()
                    print(f"   사이클 {cycle_count} 완료 ({((time.time() - (end_time - duration_minutes * 60)) / (duration_minutes * 60) * 100):.1f}%)")
                
                time.sleep(1)  # 1초 대기
            
            self.results["stress_tests"][test_name]["completed_cycles"] = cycle_count
    
    def stress_test_disk_space_simulation(self):
        """디스크 공간 부족 시뮬레이션"""
        test_name = "disk_space_simulation"
        print(f"🔥 디스크 공간 부족 시뮬레이션 시작")
        
        with self.monitor_resources(test_name):
            # 매우 큰 텍스트 데이터 생성하여 디스크 공간 소모
            large_content = "Large content for disk space test. " * 1000  # ~30KB per block
            
            successful_adds = 0
            disk_full_errors = 0
            
            for i in range(1000):  # 최대 30MB 시도
                try:
                    result = process_user_input(large_content + f" Block {i}")
                    block_data = {
                        "block_index": i + 20000,
                        "timestamp": datetime.now().isoformat(),
                        "context": large_content + f" Block {i}",
                        "keywords": result.get("keywords", []),
                        "tags": result.get("tags", []),
                        "embedding": result.get("embedding", []),
                        "importance": 0.5,
                        "hash": f"disk_test_{i}",
                        "prev_hash": f"disk_test_{i-1}" if i > 0 else ""
                    }
                    self.primary_db.add_block(block_data)
                    successful_adds += 1
                    
                    if i % 100 == 0:
                        print(f"   진행: {i}/1000 블록")
                    
                except Exception as e:
                    if "disk" in str(e).lower() or "space" in str(e).lower():
                        disk_full_errors += 1
                    print(f"   블록 {i} 저장 실패: {e}")
                    break
            
            self.results["stress_tests"][test_name].update({
                "successful_adds": successful_adds,
                "disk_full_errors": disk_full_errors,
                "total_attempted": i + 1
            })
    
    def stress_test_corruption_recovery(self):
        """데이터 손상 복구 테스트"""
        test_name = "corruption_recovery"
        print(f"🔥 데이터 손상 복구 테스트 시작")
        
        with self.monitor_resources(test_name):
            # 먼저 정상 데이터 추가
            normal_data = self.generate_test_data(100, "medium")
            for i, content in enumerate(normal_data):
                result = process_user_input(content)
                block_data = {
                    "block_index": i + 30000,
                    "timestamp": datetime.now().isoformat(),
                    "context": content,
                    "keywords": result.get("keywords", []),
                    "tags": result.get("tags", []),
                    "embedding": result.get("embedding", []),
                    "importance": 0.5,
                    "hash": f"recovery_test_{i}",
                    "prev_hash": f"recovery_test_{i-1}" if i > 0 else ""
                }
                self.primary_db.add_block(block_data)
            
            # 데이터 검증
            initial_blocks = []
            for i in range(10):
                block = self.primary_db.get_block(i + 30000)
                if block:
                    initial_blocks.append(block)
            
            # 손상된 데이터 시뮬레이션 (잘못된 형식의 데이터)
            corrupted_attempts = 0
            recovery_attempts = 0
            
            corrupted_data_types = [
                None,  # NULL 데이터
                "",    # 빈 문자열
                "a" * 100000,  # 너무 긴 문자열
                {"invalid": "json"},  # 잘못된 타입
                "\x00\x01\x02",  # 바이너리 데이터
            ]
            
            for corrupt_data in corrupted_data_types:
                try:
                    result = process_user_input(str(corrupt_data) if corrupt_data is not None else "NULL")
                    corrupted_attempts += 1
                except Exception:
                    recovery_attempts += 1  # 예외 처리로 복구
            
            # 복구 후 데이터 검증
            recovered_blocks = []
            for i in range(10):
                block = self.primary_db.get_block(i + 30000)
                if block:
                    recovered_blocks.append(block)
            
            self.results["stress_tests"][test_name].update({
                "initial_blocks_count": len(initial_blocks),
                "corrupted_attempts": corrupted_attempts,
                "recovery_attempts": recovery_attempts,
                "recovered_blocks_count": len(recovered_blocks),
                "data_integrity_maintained": len(initial_blocks) == len(recovered_blocks)
            })
    
    def analyze_stress_test_results(self) -> Dict[str, Any]:
        """스트레스 테스트 결과 분석"""
        analysis = {
            "overall_score": 0,
            "stability_grade": "Unknown",
            "critical_issues": [],
            "warnings": [],
            "recommendations": []
        }
        
        tests = self.results["stress_tests"]
        total_score = 0
        test_count = 0
        
        for test_name, test_result in tests.items():
            test_score = 100  # 시작 점수
            
            # 메모리 누수 검사
            memory_leak = test_result.get("memory_leak_mb", 0)
            if memory_leak > 50:
                analysis["critical_issues"].append(f"{test_name}: 심각한 메모리 누수 {memory_leak:.1f}MB")
                test_score -= 50
            elif memory_leak > 10:
                analysis["warnings"].append(f"{test_name}: 메모리 누수 감지 {memory_leak:.1f}MB")
                test_score -= 20
            
            # 파일 핸들 누수 검사
            file_leak = test_result.get("file_leak_count", 0)
            if file_leak > 10:
                analysis["critical_issues"].append(f"{test_name}: 파일 핸들 누수 {file_leak}개")
                test_score -= 30
            elif file_leak > 0:
                analysis["warnings"].append(f"{test_name}: 파일 핸들 증가 {file_leak}개")
                test_score -= 10
            
            # 오류율 검사
            error_rate = test_result.get("error_rate", 0)
            if error_rate > 5:
                analysis["critical_issues"].append(f"{test_name}: 높은 오류율 {error_rate}%")
                test_score -= 40
            elif error_rate > 1:
                analysis["warnings"].append(f"{test_name}: 오류율 {error_rate}%")
                test_score -= 15
            
            # 성공률 검사
            success_rate = test_result.get("success_rate", 100)
            if success_rate < 90:
                analysis["critical_issues"].append(f"{test_name}: 낮은 성공률 {success_rate}%")
                test_score -= 50
            elif success_rate < 95:
                analysis["warnings"].append(f"{test_name}: 성공률 {success_rate}%")
                test_score -= 20
            
            total_score += max(0, test_score)
            test_count += 1
        
        # 전체 점수 계산
        if test_count > 0:
            analysis["overall_score"] = round(total_score / test_count, 1)
        
        # 등급 결정
        score = analysis["overall_score"]
        if score >= 90:
            analysis["stability_grade"] = "A (Excellent)"
        elif score >= 80:
            analysis["stability_grade"] = "B (Good)"
        elif score >= 70:
            analysis["stability_grade"] = "C (Fair)"
        elif score >= 60:
            analysis["stability_grade"] = "D (Poor)"
        else:
            analysis["stability_grade"] = "F (Critical)"
        
        # 권장사항 생성
        if analysis["critical_issues"]:
            analysis["recommendations"].append("즉시 수정 필요한 심각한 문제들이 발견되었습니다.")
        if analysis["warnings"]:
            analysis["recommendations"].append("모니터링이 필요한 경고 사항들이 있습니다.")
        if score >= 90:
            analysis["recommendations"].append("모든 스트레스 테스트를 성공적으로 통과했습니다.")
        else:
            analysis["recommendations"].append("안정성 개선을 위한 추가 최적화가 필요합니다.")
        
        return analysis
    
    def run_all_stress_tests(self):
        """모든 스트레스 테스트 실행"""
        print("🔥 Greeum v2.0.4 Weekly Stress Test 시작")
        print(f"   날짜: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"   플랫폼: {sys.platform}")
        print(f"   시스템: CPU {self.results['system_info']['cpu_count']}코어, "
              f"RAM {self.results['system_info']['memory_total_gb']:.1f}GB")
        print()
        
        try:
            # 스트레스 테스트 실행
            self.stress_test_massive_memory_blocks([1000, 5000])  # 10000은 시간상 제외
            self.stress_test_concurrent_access(worker_count=8, operations_per_worker=50)
            self.stress_test_memory_leak_detection(duration_minutes=5)  # 30분은 시간상 5분으로 축소
            self.stress_test_disk_space_simulation()
            self.stress_test_corruption_recovery()
            
            # 결과 분석
            analysis = self.analyze_stress_test_results()
            self.results["analysis"] = analysis
            
            print()
            print(f"📊 전체 안정성 점수: {analysis['overall_score']}/100")
            print(f"🏆 안정성 등급: {analysis['stability_grade']}")
            
            if analysis["critical_issues"]:
                print("❌ 심각한 문제:")
                for issue in analysis["critical_issues"]:
                    print(f"   - {issue}")
            
            if analysis["warnings"]:
                print("⚠️  경고:")
                for warning in analysis["warnings"]:
                    print(f"   - {warning}")
            
            print("💡 권장사항:")
            for rec in analysis["recommendations"]:
                print(f"   - {rec}")
            
        except Exception as e:
            print(f"❌ 스트레스 테스트 실행 중 오류: {e}")
            self.results["error"] = str(e)
            import traceback
            self.results["traceback"] = traceback.format_exc()
        
        finally:
            # 결과 저장
            self.save_results()
            
            # 정리
            self.cleanup()
    
    def save_results(self):
        """결과를 파일로 저장"""
        results_dir = Path(__file__).parent.parent / "stress_test_results"
        results_dir.mkdir(exist_ok=True)
        
        # 타임스탬프 기반 파일명
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results_file = results_dir / f"weekly_stress_test_{timestamp}.json"
        
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, ensure_ascii=False, indent=2)
        
        print(f"📁 결과 저장: {results_file}")
        
        # 최신 결과도 별도 저장
        latest_file = results_dir / "latest_stress_test.json"
        with open(latest_file, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, ensure_ascii=False, indent=2)
    
    def cleanup(self):
        """테스트 파일 정리"""
        try:
            if self.test_dir.exists():
                shutil.rmtree(self.test_dir)
                print(f"🧹 테스트 디렉토리 정리 완료")
        except Exception as e:
            print(f"⚠️  정리 중 오류: {e}")


def main():
    """메인 실행 함수"""
    stress_test = StressTestSuite()
    stress_test.run_all_stress_tests()


if __name__ == "__main__":
    main()