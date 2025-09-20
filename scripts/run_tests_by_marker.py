#!/usr/bin/env python3
"""
마커별 테스트 실행 스크립트
"""

import subprocess
import sys
import time
from pathlib import Path

def run_tests_by_marker(marker, description=""):
    """특정 마커의 테스트 실행"""
    print(f"\n🧪 {description} 테스트 실행 중...")
    print("=" * 60)
    
    start_time = time.time()
    
    try:
        result = subprocess.run([
            sys.executable, "-m", "pytest", 
            "-m", marker,
            "-v", 
            "--tb=short",
            "--durations=10"
        ], capture_output=True, text=True, cwd=Path(__file__).parent.parent)
        
        duration = time.time() - start_time
        
        print(f"⏱️  실행 시간: {duration:.2f}초")
        print(f"📊 결과: {result.returncode}")
        
        if result.stdout:
            print("\n📝 출력:")
            print(result.stdout)
        
        if result.stderr:
            print("\n⚠️  오류:")
            print(result.stderr)
        
        return result.returncode == 0
        
    except Exception as e:
        print(f"❌ 실행 오류: {e}")
        return False

def main():
    """메인 실행 함수"""
    print("🚀 Greeum 테스트 마커별 실행")
    print("=" * 60)
    
    # 테스트 마커 정의
    markers = [
        ("fast", "빠른 단위 테스트"),
        ("slow", "느린 통합 테스트"),
        ("performance", "성능 측정 테스트"),
        ("database", "데이터베이스 테스트"),
        ("mcp", "MCP 서버 테스트"),
        ("integration", "통합 테스트"),
        ("unit", "순수 단위 테스트")
    ]
    
    # 명령행 인수 처리
    if len(sys.argv) > 1:
        target_marker = sys.argv[1]
        marker_info = next((m for m in markers if m[0] == target_marker), None)
        if marker_info:
            success = run_tests_by_marker(marker_info[0], marker_info[1])
            sys.exit(0 if success else 1)
        else:
            print(f"❌ 알 수 없는 마커: {target_marker}")
            print(f"사용 가능한 마커: {', '.join(m[0] for m in markers)}")
            sys.exit(1)
    
    # 모든 마커 실행
    results = {}
    total_start = time.time()
    
    for marker, description in markers:
        results[marker] = run_tests_by_marker(marker, description)
    
    total_duration = time.time() - total_start
    
    # 결과 요약
    print("\n" + "=" * 60)
    print("📊 테스트 실행 결과 요약")
    print("=" * 60)
    
    for marker, description in markers:
        status = "✅ 성공" if results[marker] else "❌ 실패"
        print(f"{marker:12} | {description:20} | {status}")
    
    print(f"\n⏱️  총 실행 시간: {total_duration:.2f}초")
    
    # 전체 성공 여부
    all_success = all(results.values())
    print(f"\n🎯 전체 결과: {'✅ 모든 테스트 성공' if all_success else '❌ 일부 테스트 실패'}")
    
    sys.exit(0 if all_success else 1)

if __name__ == "__main__":
    main()
