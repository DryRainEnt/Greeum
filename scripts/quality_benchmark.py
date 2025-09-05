#!/usr/bin/env python3
"""
Greeum Quality Benchmark Tool

자동화된 품질 보증을 위한 벤치마크 스크립트.
성능, 메모리, 안정성을 종합적으로 측정하고 품질 기준을 검증합니다.

Usage:
    python scripts/quality_benchmark.py --quick
    python scripts/quality_benchmark.py --full
    python scripts/quality_benchmark.py --regression-only
"""

import argparse
import time
import json
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional
import tempfile

# 성능 측정을 위한 imports
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False

# 프로젝트 모듈 imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from greeum.core.database_manager import DatabaseManager
from greeum.core.block_manager import BlockManager
from greeum.core.search_engine import SearchEngine
from greeum.anchors.manager import AnchorManager


class QualityBenchmark:
    """품질 보증을 위한 종합 벤치마크"""
    
    def __init__(self, config: Optional[Dict] = None):
        """벤치마크 초기화"""
        self.config = config or self._default_config()
        self.results = {
            'timestamp': datetime.now().isoformat(),
            'version': '2.2.5a1',
            'benchmarks': {},
            'quality_gates': {},
            'overall_status': 'unknown'
        }
        
        # 임시 환경 설정
        self.temp_db = None
        self.temp_anchor = None
        self.setup_test_environment()
    
    def _default_config(self) -> Dict:
        """기본 벤치마크 설정"""
        return {
            'performance': {
                'search_latency_target_ms': 100.0,
                'memory_increase_limit_mb': 50.0,
                'throughput_target_ops_per_sec': 10.0
            },
            'regression': {
                'performance_tolerance_percent': 10.0,
                'max_search_time_ms': 200.0,
                'max_add_block_time_ms': 10.0
            },
            'stress': {
                'block_count': 100,
                'search_count': 50,
                'concurrent_operations': 10
            }
        }
    
    def setup_test_environment(self):
        """테스트 환경 설정"""
        print("🔧 Setting up test environment...")
        
        # 임시 파일 생성
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        
        self.temp_anchor = tempfile.NamedTemporaryFile(delete=False, suffix='.json')
        self.temp_anchor.close()
        
        # 테스트 컴포넌트 초기화
        self.db_manager = DatabaseManager(connection_string=self.temp_db.name)
        self.block_manager = BlockManager(self.db_manager)
        self.search_engine = SearchEngine(self.block_manager)
        
        print(f"   ✓ Test database: {self.temp_db.name}")
        print(f"   ✓ Test anchors: {self.temp_anchor.name}")
    
    def cleanup_test_environment(self):
        """테스트 환경 정리"""
        if self.temp_db:
            Path(self.temp_db.name).unlink(missing_ok=True)
        if self.temp_anchor:
            Path(self.temp_anchor.name).unlink(missing_ok=True)
    
    def run_performance_benchmark(self) -> Dict[str, Any]:
        """성능 벤치마크 실행"""
        print("\n⚡ Running Performance Benchmarks...")
        
        results = {
            'search_latency': [],
            'add_block_latency': [],
            'memory_usage': {},
            'throughput': {}
        }
        
        # 테스트 데이터 준비
        test_blocks = self._create_test_dataset(50)
        test_queries = [
            "machine learning algorithms",
            "database optimization techniques", 
            "web development frameworks",
            "data analysis methods",
            "software architecture patterns"
        ]
        
        # 1. 검색 지연시간 측정
        print("   🔍 Measuring search latency...")
        for query in test_queries:
            start_time = time.perf_counter()
            result = self.search_engine.search(query, top_k=5)
            latency_ms = (time.perf_counter() - start_time) * 1000
            results['search_latency'].append(latency_ms)
        
        avg_search_latency = sum(results['search_latency']) / len(results['search_latency'])
        max_search_latency = max(results['search_latency'])
        
        print(f"     Average: {avg_search_latency:.2f}ms, Max: {max_search_latency:.2f}ms")
        
        # 2. 블록 추가 지연시간 측정  
        print("   📦 Measuring add_block latency...")
        for content in test_blocks[:10]:  # 10개만 측정
            start_time = time.perf_counter()
            self.block_manager.add_block(
                context=content,
                keywords=["test"],
                tags=["benchmark"],
                embedding=[0.5] * 128,
                importance=0.5
            )
            latency_ms = (time.perf_counter() - start_time) * 1000
            results['add_block_latency'].append(latency_ms)
        
        avg_add_latency = sum(results['add_block_latency']) / len(results['add_block_latency'])
        print(f"     Average: {avg_add_latency:.2f}ms")
        
        # 3. 메모리 사용량 측정
        if PSUTIL_AVAILABLE:
            print("   🧠 Measuring memory usage...")
            process = psutil.Process()
            initial_memory = process.memory_info().rss / 1024 / 1024  # MB
            
            # 메모리 부하 테스트
            for i in range(20):
                self.search_engine.search(f"test query {i}", top_k=5)
            
            final_memory = process.memory_info().rss / 1024 / 1024  # MB
            memory_increase = final_memory - initial_memory
            
            results['memory_usage'] = {
                'initial_mb': initial_memory,
                'final_mb': final_memory,
                'increase_mb': memory_increase
            }
            print(f"     Memory: {initial_memory:.1f}MB → {final_memory:.1f}MB (+{memory_increase:.1f}MB)")
        
        # 4. 처리량 측정
        print("   📈 Measuring throughput...")
        operations_count = 20
        start_time = time.perf_counter()
        
        for i in range(operations_count):
            self.search_engine.search(f"throughput test {i}", top_k=3)
        
        total_time = time.perf_counter() - start_time
        throughput = operations_count / total_time
        
        results['throughput'] = {
            'operations': operations_count,
            'time_seconds': total_time,
            'ops_per_second': throughput
        }
        print(f"     Throughput: {throughput:.1f} ops/sec")
        
        # 성능 기준 검증
        performance_checks = {
            'search_latency_ok': avg_search_latency <= self.config['performance']['search_latency_target_ms'],
            'add_block_latency_ok': avg_add_latency <= self.config['regression']['max_add_block_time_ms'],
            'memory_ok': True,  # 기본값
            'throughput_ok': throughput >= self.config['performance']['throughput_target_ops_per_sec']
        }
        
        if PSUTIL_AVAILABLE and 'memory_usage' in results:
            performance_checks['memory_ok'] = memory_increase <= self.config['performance']['memory_increase_limit_mb']
        
        results['performance_checks'] = performance_checks
        results['summary'] = {
            'avg_search_latency_ms': avg_search_latency,
            'avg_add_latency_ms': avg_add_latency,
            'throughput_ops_per_sec': throughput,
            'all_checks_passed': all(performance_checks.values())
        }
        
        return results
    
    def run_regression_test(self) -> Dict[str, Any]:
        """회귀 테스트 실행"""
        print("\n🧪 Running Regression Tests...")
        
        results = {
            'api_compatibility': [],
            'performance_regression': {},
            'functionality_tests': {}
        }
        
        # 기존 API 호환성 테스트
        print("   🔄 Testing API compatibility...")
        
        # 1. 기본 검색 동작 (앵커 없이)
        try:
            search_result = self.search_engine.search("test query")
            results['api_compatibility'].append({
                'test': 'basic_search',
                'status': 'pass' if 'blocks' in search_result else 'fail',
                'details': f"Found {len(search_result.get('blocks', []))} results"
            })
        except Exception as e:
            results['api_compatibility'].append({
                'test': 'basic_search',
                'status': 'fail',
                'details': str(e)
            })
        
        # 2. 블록 관리 동작
        try:
            test_block = self.block_manager.add_block(
                context="Regression test block",
                keywords=["regression"],
                tags=["test"],
                embedding=[0.3] * 128,
                importance=0.5
            )
            
            retrieved_block = self.db_manager.get_block_by_index(test_block['block_index'])
            
            results['api_compatibility'].append({
                'test': 'block_management',
                'status': 'pass' if retrieved_block is not None else 'fail',
                'details': f"Block {test_block['block_index']} created and retrieved"
            })
        except Exception as e:
            results['api_compatibility'].append({
                'test': 'block_management',
                'status': 'fail',
                'details': str(e)
            })
        
        # 성능 회귀 테스트
        print("   📊 Testing performance regression...")
        
        # 벤치마크 성능과 비교
        baseline_search_times = []
        for i in range(10):
            start_time = time.perf_counter()
            self.search_engine.search(f"regression test {i}")
            search_time = (time.perf_counter() - start_time) * 1000
            baseline_search_times.append(search_time)
        
        avg_baseline_time = sum(baseline_search_times) / len(baseline_search_times)
        
        results['performance_regression'] = {
            'avg_search_time_ms': avg_baseline_time,
            'within_tolerance': avg_baseline_time <= self.config['regression']['max_search_time_ms'],
            'tolerance_ms': self.config['regression']['max_search_time_ms']
        }
        
        print(f"     Average search time: {avg_baseline_time:.2f}ms")
        
        # 종합 평가
        api_passes = sum(1 for test in results['api_compatibility'] if test['status'] == 'pass')
        total_api_tests = len(results['api_compatibility'])
        
        results['summary'] = {
            'api_compatibility_rate': api_passes / total_api_tests if total_api_tests > 0 else 0,
            'performance_regression_ok': results['performance_regression']['within_tolerance'],
            'all_tests_passed': (api_passes == total_api_tests and 
                               results['performance_regression']['within_tolerance'])
        }
        
        return results
    
    def run_stress_test(self) -> Dict[str, Any]:
        """스트레스 테스트 실행"""
        print("\n🔥 Running Stress Tests...")
        
        results = {
            'concurrent_operations': {},
            'large_dataset': {},
            'stability': {}
        }
        
        # 대용량 데이터셋 테스트
        print("   📊 Testing with large dataset...")
        large_dataset = self._create_test_dataset(self.config['stress']['block_count'])
        
        start_time = time.perf_counter()
        created_blocks = []
        
        for i, content in enumerate(large_dataset):
            try:
                block = self.block_manager.add_block(
                    context=content,
                    keywords=[f"stress_{i}"],
                    tags=["stress_test"],
                    embedding=[float(i % 100) / 100.0] * 128,
                    importance=0.5
                )
                created_blocks.append(block['block_index'])
            except Exception as e:
                print(f"     Error creating block {i}: {e}")
                break
        
        creation_time = time.perf_counter() - start_time
        
        results['large_dataset'] = {
            'target_blocks': len(large_dataset),
            'created_blocks': len(created_blocks),
            'creation_time_seconds': creation_time,
            'avg_time_per_block_ms': (creation_time * 1000) / len(created_blocks) if created_blocks else 0,
            'success_rate': len(created_blocks) / len(large_dataset)
        }
        
        print(f"     Created {len(created_blocks)}/{len(large_dataset)} blocks in {creation_time:.2f}s")
        
        # 스트레스 검색 테스트
        print("   🔍 Testing search under stress...")
        
        search_start = time.perf_counter()
        successful_searches = 0
        search_errors = 0
        
        for i in range(self.config['stress']['search_count']):
            try:
                result = self.search_engine.search(f"stress search {i}", top_k=5)
                if 'blocks' in result:
                    successful_searches += 1
                else:
                    search_errors += 1
            except Exception as e:
                search_errors += 1
        
        search_time = time.perf_counter() - search_start
        
        results['concurrent_operations'] = {
            'target_searches': self.config['stress']['search_count'],
            'successful_searches': successful_searches,
            'search_errors': search_errors,
            'total_time_seconds': search_time,
            'avg_search_time_ms': (search_time * 1000) / self.config['stress']['search_count'],
            'error_rate': search_errors / self.config['stress']['search_count']
        }
        
        print(f"     Completed {successful_searches}/{self.config['stress']['search_count']} searches")
        
        # 시스템 안정성 평가
        results['stability'] = {
            'creation_success_rate': results['large_dataset']['success_rate'],
            'search_success_rate': 1.0 - results['concurrent_operations']['error_rate'],
            'overall_stability': (results['large_dataset']['success_rate'] + 
                                (1.0 - results['concurrent_operations']['error_rate'])) / 2
        }
        
        return results
    
    def _create_test_dataset(self, size: int) -> List[str]:
        """테스트용 데이터셋 생성"""
        topics = [
            "machine learning algorithms and applications",
            "database design and optimization strategies",
            "web development frameworks and tools",
            "software architecture patterns and principles",
            "data analysis techniques and methodologies",
            "cybersecurity best practices and protocols",
            "cloud computing platforms and services",
            "mobile application development approaches",
            "artificial intelligence research and development",
            "system administration and DevOps practices"
        ]
        
        dataset = []
        for i in range(size):
            topic = topics[i % len(topics)]
            content = f"Test content {i}: {topic}. Additional context and details for comprehensive testing."
            dataset.append(content)
        
        return dataset
    
    def evaluate_quality_gates(self) -> Dict[str, Any]:
        """품질 게이트 평가"""
        print("\n🎯 Evaluating Quality Gates...")
        
        benchmarks = self.results['benchmarks']
        gates = {}
        
        # Gate 1: Performance
        if 'performance' in benchmarks:
            perf = benchmarks['performance']['summary']
            gates['performance'] = {
                'status': 'pass' if perf['all_checks_passed'] else 'fail',
                'criteria': 'Search <100ms, Add <10ms, Throughput >10ops/s',
                'actual': f"Search {perf['avg_search_latency_ms']:.1f}ms, "
                         f"Add {perf['avg_add_latency_ms']:.1f}ms, "
                         f"Throughput {perf['throughput_ops_per_sec']:.1f}ops/s"
            }
        
        # Gate 2: Regression
        if 'regression' in benchmarks:
            reg = benchmarks['regression']['summary']
            gates['regression'] = {
                'status': 'pass' if reg['all_tests_passed'] else 'fail',
                'criteria': 'API compatibility 100%, Performance within tolerance',
                'actual': f"API {reg['api_compatibility_rate']:.1%}, "
                         f"Perf {reg['performance_regression_ok']}"
            }
        
        # Gate 3: Stress Test
        if 'stress' in benchmarks:
            stress = benchmarks['stress']['stability']
            stability_threshold = 0.95
            gates['stress'] = {
                'status': 'pass' if stress['overall_stability'] >= stability_threshold else 'fail',
                'criteria': f'Overall stability ≥{stability_threshold:.0%}',
                'actual': f"Stability {stress['overall_stability']:.1%}"
            }
        
        # 전체 게이트 상태
        all_gates_passed = all(gate['status'] == 'pass' for gate in gates.values())
        gates['overall'] = {
            'status': 'pass' if all_gates_passed else 'fail',
            'passed_gates': sum(1 for gate in gates.values() if gate['status'] == 'pass'),
            'total_gates': len(gates)
        }
        
        return gates
    
    def generate_report(self) -> str:
        """품질 보고서 생성"""
        report = []
        report.append("# Greeum Quality Benchmark Report")
        report.append(f"\n**Date**: {self.results['timestamp']}")
        report.append(f"**Version**: {self.results['version']}")
        
        # Quality Gates Summary
        gates = self.results.get('quality_gates', {})
        if 'overall' in gates:
            overall_status = gates['overall']['status']
            status_emoji = "✅" if overall_status == 'pass' else "❌"
            report.append(f"\n## {status_emoji} Overall Status: {overall_status.upper()}")
            report.append(f"**Gates Passed**: {gates['overall']['passed_gates']}/{gates['overall']['total_gates']}")
        
        # Detailed Results
        report.append("\n## Quality Gates Details")
        
        for gate_name, gate_info in gates.items():
            if gate_name == 'overall':
                continue
                
            status_emoji = "✅" if gate_info['status'] == 'pass' else "❌"
            report.append(f"\n### {status_emoji} {gate_name.title()} Gate")
            report.append(f"- **Criteria**: {gate_info['criteria']}")
            report.append(f"- **Result**: {gate_info['actual']}")
            report.append(f"- **Status**: {gate_info['status']}")
        
        # Benchmark Details
        benchmarks = self.results.get('benchmarks', {})
        
        if 'performance' in benchmarks:
            perf = benchmarks['performance']['summary']
            report.append("\n## Performance Metrics")
            report.append(f"- Average Search Latency: {perf['avg_search_latency_ms']:.2f}ms")
            report.append(f"- Average Add Block Latency: {perf['avg_add_latency_ms']:.2f}ms")  
            report.append(f"- Throughput: {perf['throughput_ops_per_sec']:.1f} ops/sec")
        
        if 'regression' in benchmarks:
            reg = benchmarks['regression']['summary']
            report.append("\n## Regression Test Results")
            report.append(f"- API Compatibility: {reg['api_compatibility_rate']:.1%}")
            report.append(f"- Performance Regression: {'✅ OK' if reg['performance_regression_ok'] else '❌ FAIL'}")
        
        if 'stress' in benchmarks:
            stress = benchmarks['stress']
            report.append("\n## Stress Test Results")
            report.append(f"- Dataset Creation: {stress['large_dataset']['success_rate']:.1%}")
            report.append(f"- Search Success Rate: {stress['concurrent_operations']['successful_searches']}/{stress['concurrent_operations']['target_searches']}")
            report.append(f"- Overall Stability: {stress['stability']['overall_stability']:.1%}")
        
        # Recommendations
        report.append("\n## Recommendations")
        
        if gates.get('overall', {}).get('status') == 'pass':
            report.append("- ✅ All quality gates passed - Ready for deployment")
            report.append("- Continue monitoring performance in production")
        else:
            report.append("- ❌ Quality gates failed - Address issues before deployment")
            failed_gates = [name for name, info in gates.items() 
                          if name != 'overall' and info['status'] == 'fail']
            if failed_gates:
                report.append(f"- Failed gates: {', '.join(failed_gates)}")
        
        return '\n'.join(report)
    
    def run_full_benchmark(self):
        """전체 벤치마크 실행"""
        print("🚀 Starting Greeum Quality Benchmark Suite")
        print("=" * 60)
        
        try:
            # Performance benchmarks
            self.results['benchmarks']['performance'] = self.run_performance_benchmark()
            
            # Regression tests  
            self.results['benchmarks']['regression'] = self.run_regression_test()
            
            # Stress tests
            self.results['benchmarks']['stress'] = self.run_stress_test()
            
            # Quality gates evaluation
            self.results['quality_gates'] = self.evaluate_quality_gates()
            
            # Set overall status
            self.results['overall_status'] = self.results['quality_gates']['overall']['status']
            
        except Exception as e:
            print(f"❌ Benchmark failed with error: {e}")
            self.results['overall_status'] = 'error'
            self.results['error'] = str(e)
            
        finally:
            self.cleanup_test_environment()
    
    def run_quick_benchmark(self):
        """빠른 벤치마크 (성능 + 회귀 테스트만)"""
        print("⚡ Starting Quick Quality Benchmark")
        print("=" * 40)
        
        try:
            # Performance benchmarks only
            self.results['benchmarks']['performance'] = self.run_performance_benchmark()
            
            # Regression tests
            self.results['benchmarks']['regression'] = self.run_regression_test()
            
            # Simplified quality gates
            self.results['quality_gates'] = self.evaluate_quality_gates()
            self.results['overall_status'] = self.results['quality_gates']['overall']['status']
            
        except Exception as e:
            print(f"❌ Quick benchmark failed: {e}")
            self.results['overall_status'] = 'error'
            self.results['error'] = str(e)
            
        finally:
            self.cleanup_test_environment()


def main():
    """메인 실행 함수"""
    parser = argparse.ArgumentParser(description="Greeum Quality Benchmark Tool")
    parser.add_argument("--quick", action="store_true", 
                       help="Run quick benchmark (performance + regression only)")
    parser.add_argument("--full", action="store_true",
                       help="Run full benchmark suite including stress tests")
    parser.add_argument("--regression-only", action="store_true",
                       help="Run regression tests only")
    parser.add_argument("--output", "-o", default="quality_report.md",
                       help="Output file for quality report")
    parser.add_argument("--json", action="store_true",
                       help="Also output results as JSON")
    
    args = parser.parse_args()
    
    # 기본값 설정
    if not any([args.quick, args.full, args.regression_only]):
        args.quick = True  # 기본은 quick 모드
    
    # 벤치마크 실행
    benchmark = QualityBenchmark()
    
    if args.regression_only:
        print("🧪 Running Regression Tests Only")
        benchmark.results['benchmarks']['regression'] = benchmark.run_regression_test()
        benchmark.results['quality_gates'] = {'regression': {'status': 'pass' if benchmark.results['benchmarks']['regression']['summary']['all_tests_passed'] else 'fail'}}
        benchmark.results['overall_status'] = benchmark.results['quality_gates']['regression']['status']
    elif args.full:
        benchmark.run_full_benchmark()
    else:  # quick
        benchmark.run_quick_benchmark()
    
    # 결과 출력
    print("\n" + "=" * 60)
    print("📊 Benchmark Complete!")
    print("=" * 60)
    
    report = benchmark.generate_report()
    print(report)
    
    # 파일 저장
    with open(args.output, 'w', encoding='utf-8') as f:
        f.write(report)
    print(f"\n📄 Report saved to: {args.output}")
    
    if args.json:
        json_file = args.output.replace('.md', '.json')
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(benchmark.results, f, indent=2)
        print(f"📄 JSON results saved to: {json_file}")
    
    # 종료 코드 설정
    exit_code = 0 if benchmark.results['overall_status'] == 'pass' else 1
    print(f"\n{'🎉 SUCCESS' if exit_code == 0 else '❌ FAILURE'}: Quality benchmark {'passed' if exit_code == 0 else 'failed'}")
    
    return exit_code


if __name__ == "__main__":
    exit(main())