#!/usr/bin/env python3
"""
Greeum 프로젝트 테스트 실행 스크립트
테스트 성능 최적화를 위한 단계별 실행 전략
"""

import subprocess
import sys
import time
import argparse
from pathlib import Path
from typing import List, Dict, Any
import json

class TestRunner:
    """테스트 실행 관리자"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.results = {}
        
    def run_command(self, cmd: List[str], description: str) -> Dict[str, Any]:
        """명령어 실행 및 결과 반환"""
        print(f"\n🚀 {description}")
        print(f"실행 명령: {' '.join(cmd)}")
        print("-" * 60)
        
        start_time = time.time()
        
        try:
            result = subprocess.run(
                cmd,
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=300  # 5분 타임아웃
            )
            
            elapsed_time = time.time() - start_time
            
            return {
                'description': description,
                'command': ' '.join(cmd),
                'return_code': result.returncode,
                'elapsed_time': elapsed_time,
                'stdout': result.stdout,
                'stderr': result.stderr,
                'success': result.returncode == 0
            }
            
        except subprocess.TimeoutExpired:
            elapsed_time = time.time() - start_time
            return {
                'description': description,
                'command': ' '.join(cmd),
                'return_code': -1,
                'elapsed_time': elapsed_time,
                'stdout': '',
                'stderr': f'Timeout after {elapsed_time:.2f} seconds',
                'success': False
            }
        except Exception as e:
            elapsed_time = time.time() - start_time
            return {
                'description': description,
                'command': ' '.join(cmd),
                'return_code': -1,
                'elapsed_time': elapsed_time,
                'stdout': '',
                'stderr': str(e),
                'success': False
            }
    
    def run_fast_tests(self, parallel: bool = False) -> Dict[str, Any]:
        """빠른 테스트 실행"""
        cmd = ["pytest", "-m", "fast", "-v", "--tb=short"]
        if parallel:
            cmd.extend(["-n", "auto"])
        
        return self.run_command(cmd, "빠른 테스트 실행 (단위 테스트)")
    
    def run_integration_tests(self, parallel: bool = False) -> Dict[str, Any]:
        """통합 테스트 실행"""
        cmd = ["pytest", "-m", "slow", "-v", "--tb=short"]
        if parallel:
            cmd.extend(["-n", "auto"])
        
        return self.run_command(cmd, "통합 테스트 실행")
    
    def run_all_tests_except_performance(self, parallel: bool = False) -> Dict[str, Any]:
        """성능 테스트 제외한 전체 테스트 실행"""
        cmd = ["pytest", "-m", "not performance", "-v", "--tb=short"]
        if parallel:
            cmd.extend(["-n", "auto"])
        
        return self.run_command(cmd, "성능 테스트 제외한 전체 테스트 실행")
    
    def run_performance_tests(self) -> Dict[str, Any]:
        """성능 테스트 실행"""
        cmd = ["pytest", "-m", "performance", "-v", "--tb=short", "--durations=10"]
        return self.run_command(cmd, "성능 테스트 실행")
    
    def run_specific_tests(self, pattern: str, parallel: bool = False) -> Dict[str, Any]:
        """특정 패턴의 테스트 실행"""
        cmd = ["pytest", "-k", pattern, "-v", "--tb=short"]
        if parallel:
            cmd.extend(["-n", "auto"])
        
        return self.run_command(cmd, f"특정 테스트 실행: {pattern}")
    
    def generate_report(self, results: List[Dict[str, Any]]) -> str:
        """테스트 결과 리포트 생성"""
        report = []
        report.append("=" * 80)
        report.append("🧪 GREEUM 테스트 실행 결과 리포트")
        report.append("=" * 80)
        
        total_time = 0
        success_count = 0
        
        for result in results:
            status = "✅ 성공" if result['success'] else "❌ 실패"
            report.append(f"\n{status} {result['description']}")
            report.append(f"   실행 시간: {result['elapsed_time']:.2f}초")
            report.append(f"   명령어: {result['command']}")
            
            if not result['success']:
                report.append(f"   에러: {result['stderr'][:200]}...")
            
            total_time += result['elapsed_time']
            if result['success']:
                success_count += 1
        
        report.append(f"\n📊 전체 요약:")
        report.append(f"   총 실행 시간: {total_time:.2f}초")
        report.append(f"   성공한 테스트: {success_count}/{len(results)}")
        report.append(f"   성공률: {success_count/len(results)*100:.1f}%")
        
        return "\n".join(report)
    
    def save_results(self, results: List[Dict[str, Any]], filename: str = None):
        """결과를 JSON 파일로 저장"""
        if filename is None:
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            filename = f"test_results_{timestamp}.json"
        
        results_file = self.project_root / "test_results" / filename
        results_file.parent.mkdir(exist_ok=True)
        
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False, default=str)
        
        print(f"📁 결과가 {results_file}에 저장되었습니다.")

def main():
    """메인 실행 함수"""
    parser = argparse.ArgumentParser(description="Greeum 프로젝트 테스트 실행")
    parser.add_argument("--mode", choices=["fast", "integration", "all", "performance", "custom"], 
                       default="fast", help="실행할 테스트 모드")
    parser.add_argument("--parallel", action="store_true", help="병렬 실행 활성화")
    parser.add_argument("--pattern", help="특정 테스트 패턴 (custom 모드에서 사용)")
    parser.add_argument("--save-results", action="store_true", help="결과를 파일로 저장")
    
    args = parser.parse_args()
    
    runner = TestRunner()
    results = []
    
    print("🚀 Greeum 테스트 실행기 시작")
    print(f"모드: {args.mode}")
    print(f"병렬 실행: {'활성화' if args.parallel else '비활성화'}")
    
    if args.mode == "fast":
        results.append(runner.run_fast_tests(args.parallel))
    elif args.mode == "integration":
        results.append(runner.run_integration_tests(args.parallel))
    elif args.mode == "all":
        results.append(runner.run_all_tests_except_performance(args.parallel))
    elif args.mode == "performance":
        results.append(runner.run_performance_tests())
    elif args.mode == "custom":
        if not args.pattern:
            print("❌ custom 모드에서는 --pattern 옵션이 필요합니다.")
            sys.exit(1)
        results.append(runner.run_specific_tests(args.pattern, args.parallel))
    
    # 결과 출력
    print(runner.generate_report(results))
    
    # 결과 저장
    if args.save_results:
        runner.save_results(results)
    
    # 실패한 테스트가 있으면 종료 코드 1 반환
    if any(not result['success'] for result in results):
        sys.exit(1)
    else:
        print("\n🎉 모든 테스트가 성공적으로 완료되었습니다!")
        sys.exit(0)

if __name__ == "__main__":
    main()
