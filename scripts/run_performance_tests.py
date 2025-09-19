#!/usr/bin/env python3
"""
성능 테스트 전용 실행 스크립트
일반 개발 워크플로우와 분리하여 실행
"""

import subprocess
import sys
import time
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List

class PerformanceTestRunner:
    """성능 테스트 전용 실행기"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.results = {}
        
    def run_performance_tests(self) -> Dict[str, Any]:
        """성능 테스트 실행"""
        print("🚀 성능 테스트 실행 중...")
        print("=" * 60)
        
        start_time = time.time()
        
        # 성능 테스트만 실행
        cmd = [
            "pytest",
            "-m", "performance",
            "-v",
            "--tb=short",
            "--durations=10",  # 가장 오래 걸린 10개 테스트 표시
            "--maxfail=5",     # 5개 실패 시 중단
            "--timeout=600"    # 10분 타임아웃
        ]
        
        try:
            result = subprocess.run(
                cmd,
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=1800  # 30분 전체 타임아웃
            )
            
            elapsed_time = time.time() - start_time
            
            return {
                'command': ' '.join(cmd),
                'return_code': result.returncode,
                'elapsed_time': elapsed_time,
                'stdout': result.stdout,
                'stderr': result.stderr,
                'success': result.returncode == 0,
                'timestamp': datetime.now().isoformat()
            }
            
        except subprocess.TimeoutExpired:
            elapsed_time = time.time() - start_time
            return {
                'command': ' '.join(cmd),
                'return_code': -1,
                'elapsed_time': elapsed_time,
                'stdout': '',
                'stderr': f'Timeout after {elapsed_time:.2f} seconds',
                'success': False,
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            elapsed_time = time.time() - start_time
            return {
                'command': ' '.join(cmd),
                'return_code': -1,
                'elapsed_time': elapsed_time,
                'stdout': '',
                'stderr': str(e),
                'success': False,
                'timestamp': datetime.now().isoformat()
            }
    
    def run_benchmark_tests(self) -> Dict[str, Any]:
        """벤치마크 테스트 실행"""
        print("\n📊 벤치마크 테스트 실행 중...")
        print("-" * 40)
        
        start_time = time.time()
        
        # 벤치마크 스크립트 실행
        benchmark_scripts = [
            "benchmark/performance_benchmark.py",
            "benchmark/optimized_benchmark.py",
            "benchmark/ultra_optimized_benchmark.py"
        ]
        
        results = []
        
        for script in benchmark_scripts:
            script_path = self.project_root / script
            if script_path.exists():
                print(f"실행 중: {script}")
                
                try:
                    result = subprocess.run(
                        [sys.executable, str(script_path)],
                        cwd=self.project_root,
                        capture_output=True,
                        text=True,
                        timeout=300  # 5분 타임아웃
                    )
                    
                    results.append({
                        'script': script,
                        'return_code': result.returncode,
                        'stdout': result.stdout,
                        'stderr': result.stderr,
                        'success': result.returncode == 0
                    })
                    
                except subprocess.TimeoutExpired:
                    results.append({
                        'script': script,
                        'return_code': -1,
                        'stdout': '',
                        'stderr': 'Timeout',
                        'success': False
                    })
                except Exception as e:
                    results.append({
                        'script': script,
                        'return_code': -1,
                        'stdout': '',
                        'stderr': str(e),
                        'success': False
                    })
        
        elapsed_time = time.time() - start_time
        
        return {
            'type': 'benchmark',
            'elapsed_time': elapsed_time,
            'results': results,
            'success': all(r['success'] for r in results),
            'timestamp': datetime.now().isoformat()
        }
    
    def generate_performance_report(self, pytest_result: Dict[str, Any], benchmark_result: Dict[str, Any]) -> str:
        """성능 테스트 결과 리포트 생성"""
        report = []
        report.append("=" * 80)
        report.append("🚀 GREEUM 성능 테스트 결과 리포트")
        report.append("=" * 80)
        report.append(f"실행 시간: {pytest_result['timestamp']}")
        report.append("")
        
        # pytest 결과
        report.append("📋 pytest 성능 테스트 결과:")
        report.append("-" * 40)
        status = "✅ 성공" if pytest_result['success'] else "❌ 실패"
        report.append(f"상태: {status}")
        report.append(f"실행 시간: {pytest_result['elapsed_time']:.2f}초")
        report.append(f"명령어: {pytest_result['command']}")
        
        if not pytest_result['success']:
            report.append(f"에러: {pytest_result['stderr'][:300]}...")
        
        # 벤치마크 결과
        if benchmark_result:
            report.append("\n📊 벤치마크 테스트 결과:")
            report.append("-" * 40)
            report.append(f"총 실행 시간: {benchmark_result['elapsed_time']:.2f}초")
            
            for result in benchmark_result['results']:
                status = "✅ 성공" if result['success'] else "❌ 실패"
                report.append(f"  {status} {result['script']}")
                if not result['success']:
                    report.append(f"    에러: {result['stderr'][:200]}...")
        
        # 성능 지표 추출 (stdout에서)
        if pytest_result['stdout']:
            report.append("\n📈 성능 지표:")
            report.append("-" * 40)
            
            # 가장 오래 걸린 테스트들 추출
            lines = pytest_result['stdout'].split('\n')
            duration_lines = [line for line in lines if 'slowest' in line.lower() or 'durations' in line.lower()]
            
            for line in duration_lines[:5]:  # 상위 5개만
                report.append(f"  {line.strip()}")
        
        return "\n".join(report)
    
    def save_results(self, pytest_result: Dict[str, Any], benchmark_result: Dict[str, Any] = None):
        """결과를 JSON 파일로 저장"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"performance_test_results_{timestamp}.json"
        
        results_file = self.project_root / "test_results" / filename
        results_file.parent.mkdir(exist_ok=True)
        
        data = {
            'pytest_results': pytest_result,
            'benchmark_results': benchmark_result,
            'summary': {
                'total_elapsed_time': pytest_result['elapsed_time'] + (benchmark_result['elapsed_time'] if benchmark_result else 0),
                'pytest_success': pytest_result['success'],
                'benchmark_success': benchmark_result['success'] if benchmark_result else None,
                'overall_success': pytest_result['success'] and (benchmark_result['success'] if benchmark_result else True)
            }
        }
        
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False, default=str)
        
        print(f"📁 결과가 {results_file}에 저장되었습니다.")
        return results_file

def main():
    """메인 실행 함수"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Greeum 성능 테스트 실행")
    parser.add_argument("--benchmark", action="store_true", help="벤치마크 테스트도 함께 실행")
    parser.add_argument("--save-results", action="store_true", help="결과를 파일로 저장")
    
    args = parser.parse_args()
    
    runner = PerformanceTestRunner()
    
    print("🚀 Greeum 성능 테스트 실행기 시작")
    print(f"벤치마크 포함: {'예' if args.benchmark else '아니오'}")
    
    # pytest 성능 테스트 실행
    pytest_result = runner.run_performance_tests()
    
    # 벤치마크 테스트 실행 (옵션)
    benchmark_result = None
    if args.benchmark:
        benchmark_result = runner.run_benchmark_tests()
    
    # 결과 출력
    print(runner.generate_performance_report(pytest_result, benchmark_result))
    
    # 결과 저장
    if args.save_results:
        runner.save_results(pytest_result, benchmark_result)
    
    # 실패한 테스트가 있으면 종료 코드 1 반환
    overall_success = pytest_result['success'] and (benchmark_result['success'] if benchmark_result else True)
    
    if not overall_success:
        print("\n❌ 일부 성능 테스트가 실패했습니다.")
        sys.exit(1)
    else:
        print("\n🎉 모든 성능 테스트가 성공적으로 완료되었습니다!")
        sys.exit(0)

if __name__ == "__main__":
    main()
