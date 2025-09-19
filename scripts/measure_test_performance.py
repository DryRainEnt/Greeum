#!/usr/bin/env python3
"""
테스트 성능 측정 및 분석 도구
"""

import subprocess
import json
import time
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List
import argparse

class TestPerformanceMeasurer:
    """테스트 성능 측정기"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.results = {}
        
    def measure_test_category(self, category: str, marker: str, parallel: bool = False) -> Dict[str, Any]:
        """특정 카테고리의 테스트 성능 측정"""
        print(f"\n📊 {category} 테스트 성능 측정 중...")
        print("-" * 50)
        
        cmd = ["pytest", "-m", marker, "-v", "--tb=short", "--durations=0"]
        if parallel:
            cmd.extend(["-n", "auto"])
        
        start_time = time.time()
        
        try:
            result = subprocess.run(
                cmd,
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=600  # 10분 타임아웃
            )
            
            elapsed_time = time.time() - start_time
            
            # 결과 파싱
            stdout_lines = result.stdout.split('\n')
            
            # 테스트 수 추출
            test_count = 0
            passed_count = 0
            failed_count = 0
            
            for line in stdout_lines:
                if 'collected' in line and 'items' in line:
                    # "collected 9 items" 형태에서 숫자 추출
                    parts = line.split()
                    for i, part in enumerate(parts):
                        if part == 'collected':
                            test_count = int(parts[i+1])
                            break
                elif 'passed' in line and 'failed' in line:
                    # "9 passed, 0 failed" 형태에서 숫자 추출
                    parts = line.split()
                    for i, part in enumerate(parts):
                        if part == 'passed':
                            passed_count = int(parts[i-1])
                        elif part == 'failed':
                            failed_count = int(parts[i-1])
            
            # 실행 시간 추출
            duration_lines = [line for line in stdout_lines if 'seconds' in line and 'passed' in line]
            actual_duration = 0
            if duration_lines:
                duration_line = duration_lines[-1]
                # "9 passed in 5.30s" 형태에서 시간 추출
                parts = duration_line.split()
                for i, part in enumerate(parts):
                    if 's' in part and part.replace('s', '').replace('.', '').isdigit():
                        actual_duration = float(part.replace('s', ''))
                        break
            
            return {
                'category': category,
                'marker': marker,
                'parallel': parallel,
                'return_code': result.returncode,
                'elapsed_time': elapsed_time,
                'actual_duration': actual_duration,
                'test_count': test_count,
                'passed_count': passed_count,
                'failed_count': failed_count,
                'success': result.returncode == 0,
                'stdout': result.stdout,
                'stderr': result.stderr,
                'timestamp': datetime.now().isoformat()
            }
            
        except subprocess.TimeoutExpired:
            elapsed_time = time.time() - start_time
            return {
                'category': category,
                'marker': marker,
                'parallel': parallel,
                'return_code': -1,
                'elapsed_time': elapsed_time,
                'actual_duration': 0,
                'test_count': 0,
                'passed_count': 0,
                'failed_count': 0,
                'success': False,
                'stdout': '',
                'stderr': f'Timeout after {elapsed_time:.2f} seconds',
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            elapsed_time = time.time() - start_time
            return {
                'category': category,
                'marker': marker,
                'parallel': parallel,
                'return_code': -1,
                'elapsed_time': elapsed_time,
                'actual_duration': 0,
                'test_count': 0,
                'passed_count': 0,
                'failed_count': 0,
                'success': False,
                'stdout': '',
                'stderr': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def measure_all_categories(self, parallel: bool = False) -> List[Dict[str, Any]]:
        """모든 테스트 카테고리 측정"""
        categories = [
            ("빠른 테스트", "fast"),
            ("통합 테스트", "slow"),
            ("성능 테스트", "performance"),
            ("데이터베이스 테스트", "database"),
            ("MCP 테스트", "mcp")
        ]
        
        results = []
        
        for category, marker in categories:
            result = self.measure_test_category(category, marker, parallel)
            results.append(result)
            
            # 결과 출력
            if result['success']:
                print(f"✅ {category}: {result['test_count']}개 테스트, {result['actual_duration']:.2f}초")
            else:
                print(f"❌ {category}: 실패 - {result['stderr'][:100]}...")
        
        return results
    
    def generate_performance_report(self, results: List[Dict[str, Any]]) -> str:
        """성능 측정 결과 리포트 생성"""
        report = []
        report.append("=" * 80)
        report.append("📊 GREEUM 테스트 성능 측정 결과")
        report.append("=" * 80)
        report.append(f"측정 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")
        
        # 카테고리별 결과
        report.append("📋 카테고리별 성능 결과:")
        report.append("-" * 60)
        report.append(f"{'카테고리':<15} {'테스트수':<8} {'실행시간':<10} {'성공률':<8} {'상태'}")
        report.append("-" * 60)
        
        total_tests = 0
        total_passed = 0
        total_time = 0
        
        for result in results:
            if result['test_count'] > 0:
                success_rate = (result['passed_count'] / result['test_count']) * 100
                status = "✅ 성공" if result['success'] else "❌ 실패"
                
                report.append(f"{result['category']:<15} {result['test_count']:<8} {result['actual_duration']:<10.2f} {success_rate:<8.1f}% {status}")
                
                total_tests += result['test_count']
                total_passed += result['passed_count']
                total_time += result['actual_duration']
            else:
                report.append(f"{result['category']:<15} {'0':<8} {'0.00':<10} {'0.0':<8}% ❌ 실패")
        
        report.append("-" * 60)
        report.append(f"{'전체':<15} {total_tests:<8} {total_time:<10.2f} {(total_passed/total_tests*100) if total_tests > 0 else 0:<8.1f}%")
        
        # 성능 분석
        report.append("\n📈 성능 분석:")
        report.append("-" * 40)
        
        if total_tests > 0:
            avg_time_per_test = total_time / total_tests
            report.append(f"평균 테스트 실행 시간: {avg_time_per_test:.3f}초/테스트")
            
            # 가장 오래 걸리는 카테고리
            slowest = max(results, key=lambda x: x['actual_duration'])
            report.append(f"가장 오래 걸리는 카테고리: {slowest['category']} ({slowest['actual_duration']:.2f}초)")
            
            # 가장 빠른 카테고리
            fastest = min([r for r in results if r['actual_duration'] > 0], key=lambda x: x['actual_duration'], default=None)
            if fastest:
                report.append(f"가장 빠른 카테고리: {fastest['category']} ({fastest['actual_duration']:.2f}초)")
        
        # 권장사항
        report.append("\n💡 권장사항:")
        report.append("-" * 40)
        
        if total_time > 300:  # 5분 이상
            report.append("• 전체 테스트 시간이 5분을 초과합니다. 성능 최적화가 필요합니다.")
        
        slow_tests = [r for r in results if r['actual_duration'] > 60]  # 1분 이상
        if slow_tests:
            report.append(f"• {len(slow_tests)}개 카테고리가 1분 이상 소요됩니다:")
            for test in slow_tests:
                report.append(f"  - {test['category']}: {test['actual_duration']:.2f}초")
        
        failed_tests = [r for r in results if not r['success']]
        if failed_tests:
            report.append(f"• {len(failed_tests)}개 카테고리에서 실패가 발생했습니다:")
            for test in failed_tests:
                report.append(f"  - {test['category']}: {test['stderr'][:100]}...")
        
        return "\n".join(report)
    
    def save_results(self, results: List[Dict[str, Any]], filename: str = None):
        """결과를 JSON 파일로 저장"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"test_performance_{timestamp}.json"
        
        results_file = self.project_root / "test_results" / filename
        results_file.parent.mkdir(exist_ok=True)
        
        data = {
            'measurement_time': datetime.now().isoformat(),
            'results': results,
            'summary': {
                'total_tests': sum(r['test_count'] for r in results),
                'total_passed': sum(r['passed_count'] for r in results),
                'total_time': sum(r['actual_duration'] for r in results),
                'success_rate': sum(r['passed_count'] for r in results) / sum(r['test_count'] for r in results) * 100 if sum(r['test_count'] for r in results) > 0 else 0
            }
        }
        
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False, default=str)
        
        print(f"📁 결과가 {results_file}에 저장되었습니다.")
        return results_file

def main():
    """메인 실행 함수"""
    parser = argparse.ArgumentParser(description="Greeum 테스트 성능 측정")
    parser.add_argument("--parallel", action="store_true", help="병렬 실행으로 측정")
    parser.add_argument("--category", help="특정 카테고리만 측정 (fast, slow, performance, database, mcp)")
    parser.add_argument("--save-results", action="store_true", help="결과를 파일로 저장")
    
    args = parser.parse_args()
    
    measurer = TestPerformanceMeasurer()
    
    print("🚀 Greeum 테스트 성능 측정기 시작")
    print(f"병렬 실행: {'활성화' if args.parallel else '비활성화'}")
    
    if args.category:
        # 특정 카테고리만 측정
        category_map = {
            'fast': '빠른 테스트',
            'slow': '통합 테스트', 
            'performance': '성능 테스트',
            'database': '데이터베이스 테스트',
            'mcp': 'MCP 테스트'
        }
        
        if args.category not in category_map:
            print(f"❌ 잘못된 카테고리: {args.category}")
            print(f"사용 가능한 카테고리: {', '.join(category_map.keys())}")
            sys.exit(1)
        
        result = measurer.measure_test_category(category_map[args.category], args.category, args.parallel)
        results = [result]
    else:
        # 모든 카테고리 측정
        results = measurer.measure_all_categories(args.parallel)
    
    # 결과 출력
    print(measurer.generate_performance_report(results))
    
    # 결과 저장
    if args.save_results:
        measurer.save_results(results)
    
    # 실패한 테스트가 있으면 종료 코드 1 반환
    if any(not result['success'] for result in results):
        sys.exit(1)
    else:
        print("\n🎉 모든 성능 측정이 성공적으로 완료되었습니다!")
        sys.exit(0)

if __name__ == "__main__":
    main()
