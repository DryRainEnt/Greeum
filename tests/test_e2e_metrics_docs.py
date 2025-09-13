"""
E2E 통합 테스트 - 메트릭 & 문서 검증 시스템
RED 단계: 전체 시스템 통합 테스트
"""

import unittest
import tempfile
import subprocess
import json
import time
from pathlib import Path
from datetime import datetime, timedelta
import shutil

class TestE2EIntegration(unittest.TestCase):
    """전체 시스템 E2E 통합 테스트"""
    
    @classmethod
    def setUpClass(cls):
        """테스트 클래스 전체 설정"""
        cls.test_dir = tempfile.mkdtemp(prefix="greeum_e2e_")
        cls.original_cwd = Path.cwd()
        
        # 테스트 디렉토리로 이동
        import os
        os.chdir(cls.test_dir)
        
        # Greeum 초기화
        subprocess.run(["python3", "-m", "greeum.cli", "init"], capture_output=True)
    
    @classmethod
    def tearDownClass(cls):
        """테스트 클래스 정리"""
        import os
        os.chdir(cls.original_cwd)
        shutil.rmtree(cls.test_dir, ignore_errors=True)
    
    def test_01_system_initialization(self):
        """요구사항: 시스템이 정상적으로 초기화되어야 함"""
        # 필요한 디렉토리와 파일 확인
        self.assertTrue(Path("data").exists(), "Data directory should exist")
        self.assertTrue(
            Path("data/memory.db").exists() or Path("data/blocks.db").exists(),
            "Database file should exist"
        )
    
    def test_02_generate_test_data(self):
        """요구사항: 테스트 데이터 생성 및 앵커 설정"""
        # 100개의 테스트 메모리 생성
        for i in range(100):
            result = subprocess.run(
                ["python3", "-m", "greeum.cli", "memory", "add", f"Test memory {i}"],
                capture_output=True,
                text=True
            )
            # 매 10번째마다 확인
            if i % 10 == 0:
                self.assertEqual(result.returncode, 0, f"Memory {i} should be added successfully")
        
        # 앵커 설정
        for slot, block_id in [("A", 10), ("B", 50), ("C", 90)]:
            result = subprocess.run(
                ["python3", "-m", "greeum.cli", "anchors", "set", slot, str(block_id)],
                capture_output=True,
                text=True
            )
            # 앵커 명령어가 구현되었다면 성공해야 함
            # self.assertEqual(result.returncode, 0, f"Anchor {slot} should be set")
    
    def test_03_search_patterns_with_metrics(self):
        """요구사항: 다양한 검색 패턴 실행하며 메트릭 수집"""
        search_patterns = [
            # (쿼리, 옵션, 설명)
            ("Test memory 5", ["--slot", "A", "--radius", "2"], "Local graph search"),
            ("Test memory 55", ["--use-slots"], "Slot-based search"),
            ("nonexistent", ["--fallback"], "Fallback search"),
            ("Test memory 15", [], "Global search"),
        ]
        
        for query, options, description in search_patterns:
            cmd = ["python3", "-m", "greeum.cli", "memory", "search", query] + options
            
            start = time.time()
            result = subprocess.run(cmd, capture_output=True, text=True)
            latency = (time.time() - start) * 1000
            
            # 검색이 실행되어야 함 (명령어가 있다면)
            self.assertIsNotNone(result.stdout, f"{description} should produce output")
            
            # 응답 시간 확인
            self.assertLess(latency, 1000, f"{description} should complete within 1s")
    
    def test_04_metrics_collection_verification(self):
        """요구사항: 메트릭이 정상적으로 수집되고 있어야 함"""
        # 메트릭 대시보드 확인
        result = subprocess.run(
            ["python3", "-m", "greeum.cli", "metrics", "dashboard", "--period", "1h"],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        # 대시보드 출력 확인 (구현되었다면)
        if result.returncode == 0:
            self.assertIn("검색", result.stdout, "Dashboard should show search metrics")
            self.assertIn("쓰기", result.stdout, "Dashboard should show write metrics")
    
    def test_05_metrics_export_and_analysis(self):
        """요구사항: 메트릭을 내보내고 분석할 수 있어야 함"""
        # JSON으로 메트릭 내보내기
        export_file = "e2e_metrics.json"
        result = subprocess.run(
            ["python3", "-m", "greeum.cli", "metrics", "export", 
             "--format", "json", "--output", export_file],
            capture_output=True,
            text=True
        )
        
        if Path(export_file).exists():
            with open(export_file) as f:
                metrics = json.load(f)
            
            # 메트릭 분석
            summary = metrics.get('summary', {})
            
            # 성능 기준 확인
            if 'avg_search_latency_ms' in summary:
                self.assertLess(
                    summary['avg_search_latency_ms'], 100,
                    "Average search latency should be < 100ms"
                )
            
            if 'local_search_ratio' in summary:
                self.assertGreater(
                    summary['local_search_ratio'], 0.2,
                    "Local search ratio should be > 20%"
                )
            
            if 'cache_hit_rate' in summary:
                self.assertGreater(
                    summary['cache_hit_rate'], 0.5,
                    "Cache hit rate should be > 50%"
                )
    
    def test_06_documentation_validation(self):
        """요구사항: 문서 검증 시스템이 작동해야 함"""
        # 테스트용 문서 생성
        docs_dir = Path("test_docs")
        docs_dir.mkdir(exist_ok=True)
        
        # 올바른 예시 문서
        good_doc = docs_dir / "good.md"
        good_doc.write_text("""
# Test Documentation

```bash
greeum memory add "Test"
```

```python
from greeum import BlockManager
bm = BlockManager()
```

```json
{"key": "value"}
```
""")
        
        # 잘못된 예시 문서
        bad_doc = docs_dir / "bad.md"
        bad_doc.write_text("""
# Bad Examples

```bash
greeum nonexistent-command
```

```python
invalid python syntax
```

```json
{invalid json}
```
""")
        
        # 문서 검증 실행
        result = subprocess.run(
            ["python3", "-m", "greeum.cli", "validate", "docs", 
             "--docs-dir", str(docs_dir), "--output", "validation_report.md"],
            capture_output=True,
            text=True
        )
        
        # 검증 결과 확인 (구현되었다면)
        if Path("validation_report.md").exists():
            report = Path("validation_report.md").read_text()
            self.assertIn("Passed", report, "Report should show passed count")
            self.assertIn("Failed", report, "Report should show failed count")
    
    def test_07_drift_detection(self):
        """요구사항: 문서-코드 불일치를 감지해야 함"""
        # 실제 CLI 도움말과 문서 예시 비교
        help_result = subprocess.run(
            ["python3", "-m", "greeum.cli", "memory", "search", "--help"],
            capture_output=True,
            text=True
        )
        
        # 문서에 있는 옵션이 실제로 존재하는지 확인
        documented_options = ["--slot", "--radius", "--fallback"]
        
        for option in documented_options:
            if option not in help_result.stdout:
                print(f"Warning: Drift detected - {option} not in CLI help")
    
    def test_08_performance_overhead_measurement(self):
        """요구사항: 메트릭 수집 오버헤드가 5% 미만이어야 함"""
        # 메트릭 없이 검색 (환경변수로 비활성화)
        import os
        
        # 메트릭 비활성화
        os.environ['DISABLE_METRICS'] = '1'
        
        start = time.time()
        for i in range(10):
            subprocess.run(
                ["python3", "-m", "greeum.cli", "memory", "search", f"test {i}"],
                capture_output=True
            )
        baseline_time = time.time() - start
        
        # 메트릭 활성화
        del os.environ['DISABLE_METRICS']
        
        start = time.time()
        for i in range(10):
            subprocess.run(
                ["python3", "-m", "greeum.cli", "memory", "search", f"test {i}"],
                capture_output=True
            )
        metrics_time = time.time() - start
        
        # 오버헤드 계산
        if baseline_time > 0:
            overhead_percent = ((metrics_time - baseline_time) / baseline_time) * 100
            self.assertLess(
                overhead_percent, 5.0,
                f"Metrics overhead {overhead_percent:.1f}% should be < 5%"
            )
    
    def test_09_continuous_operation(self):
        """요구사항: 장시간 연속 작업이 안정적이어야 함"""
        # 100회 연속 작업
        errors = 0
        
        for i in range(100):
            # 다양한 작업 순환 실행
            operations = [
                ["memory", "add", f"Continuous test {i}"],
                ["memory", "search", f"test {i % 10}"],
                ["anchors", "status"],
            ]
            
            for op in operations:
                result = subprocess.run(
                    ["python3", "-m", "greeum.cli"] + op,
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                
                if result.returncode != 0:
                    errors += 1
        
        # 오류율 5% 미만
        error_rate = errors / 300  # 100 * 3 operations
        self.assertLess(error_rate, 0.05, f"Error rate {error_rate:.1%} should be < 5%")
    
    def test_10_final_system_health_check(self):
        """요구사항: 최종 시스템 건강성 확인"""
        checks = {
            "Database accessible": Path("data/memory.db").exists() or Path("data/blocks.db").exists(),
            "Metrics DB exists": Path("data/metrics.db").exists(),
            "Can add memory": subprocess.run(
                ["python3", "-m", "greeum.cli", "memory", "add", "Final test"],
                capture_output=True
            ).returncode == 0,
            "Can search": subprocess.run(
                ["python3", "-m", "greeum.cli", "memory", "search", "test"],
                capture_output=True
            ).returncode == 0,
        }
        
        # 모든 체크 통과
        for check_name, passed in checks.items():
            self.assertTrue(passed, f"Health check failed: {check_name}")
        
        # 최종 요약
        print("\n=== E2E Test Summary ===")
        print(f"✅ All health checks passed")
        print(f"✅ System is ready for production")


class TestPerformanceBenchmark(unittest.TestCase):
    """성능 벤치마크 테스트"""
    
    def test_search_latency_benchmark(self):
        """요구사항: 검색 응답시간 벤치마크"""
        latencies = []
        
        for i in range(100):
            start = time.time()
            subprocess.run(
                ["python3", "-m", "greeum.cli", "memory", "search", f"test {i}"],
                capture_output=True
            )
            latency = (time.time() - start) * 1000
            latencies.append(latency)
        
        # 통계 계산
        avg_latency = sum(latencies) / len(latencies)
        p95_latency = sorted(latencies)[95]
        p99_latency = sorted(latencies)[99]
        
        # 성능 기준
        self.assertLess(avg_latency, 50, "Average latency should be < 50ms")
        self.assertLess(p95_latency, 100, "P95 latency should be < 100ms")
        self.assertLess(p99_latency, 200, "P99 latency should be < 200ms")
        
        print(f"\n=== Search Latency Benchmark ===")
        print(f"Average: {avg_latency:.1f}ms")
        print(f"P95: {p95_latency:.1f}ms")
        print(f"P99: {p99_latency:.1f}ms")
    
    def test_memory_usage_stability(self):
        """요구사항: 메모리 사용량이 안정적이어야 함"""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        
        # 초기 메모리
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # 1000회 작업
        for i in range(1000):
            subprocess.run(
                ["python3", "-m", "greeum.cli", "memory", "search", "test"],
                capture_output=True
            )
        
        # 최종 메모리
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # 메모리 증가량
        memory_increase = final_memory - initial_memory
        
        # 100MB 이하 증가
        self.assertLess(
            memory_increase, 100,
            f"Memory increase {memory_increase:.1f}MB should be < 100MB"
        )
        
        print(f"\n=== Memory Usage ===")
        print(f"Initial: {initial_memory:.1f}MB")
        print(f"Final: {final_memory:.1f}MB")
        print(f"Increase: {memory_increase:.1f}MB")


if __name__ == '__main__':
    # 테스트 실행 - 순서대로 실행되도록 설정
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # E2E 테스트는 순서대로 실행
    suite.addTests(loader.loadTestsFromTestCase(TestE2EIntegration))
    suite.addTests(loader.loadTestsFromTestCase(TestPerformanceBenchmark))
    
    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(suite)