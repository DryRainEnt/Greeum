import sys
import os
import re
from datetime import datetime, timedelta

# 상위 디렉토리 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from greeum.temporal_reasoner import TemporalReasoner, evaluate_temporal_query

def debug_time_extraction():
    """시간 표현 추출 디버깅"""
    
    # 한국어 테스트
    ko_test = "3일 전에 보낸 이메일을 찾아줘"
    ko_reasoner = TemporalReasoner(default_language="ko")
    
    # 패턴 확인
    print("한국어 시간 패턴 목록:")
    for pattern in ko_reasoner.ko_time_patterns.keys():
        print(f"  패턴: {pattern}")
    
    # 시간 패턴 딕셔너리 확인
    print("\n언어별 시간 패턴 딕셔너리:")
    for lang, patterns in ko_reasoner.time_patterns.items():
        print(f"  언어: {lang}, 패턴 수: {len(patterns)}")
    
    # 한국어 시간 표현 추출 과정 디버깅
    print("\n한국어 시간 표현 추출 과정:")
    print(f"  테스트 문자열: {ko_test}")
    print(f"  사용 언어: {ko_reasoner.default_language}")
    
    # 정규식 패턴 직접 테스트
    print("\n정규식 패턴 테스트 (한국어):")
    for pattern, delta_func in ko_reasoner.ko_time_patterns.items():
        if "(" in pattern and any(c.isdigit() for c in pattern):
            print(f"  패턴: {pattern}")
            try:
                regex = re.compile(pattern)
                matches = list(regex.finditer(ko_test))
                print(f"    매치 결과: {len(matches)} 개")
                for match in matches:
                    print(f"      매칭: {match.group(0)}")
            except Exception as e:
                print(f"    에러: {e}")
    
    # 영어 테스트
    en_test = "Find the email I sent 3 days ago"
    en_reasoner = TemporalReasoner(default_language="en")
    
    # 영어 패턴 확인
    print("\n영어 시간 패턴 목록:")
    for pattern in en_reasoner.en_time_patterns.keys():
        print(f"  패턴: {pattern}")
    
    # 영어 시간 표현 추출 과정 디버깅
    print("\n영어 시간 표현 추출 과정:")
    print(f"  테스트 문자열: {en_test}")
    print(f"  사용 언어: {en_reasoner.default_language}")
    
    # 정규식 패턴 직접 테스트
    print("\n정규식 패턴 테스트 (영어):")
    for pattern, delta_func in en_reasoner.en_time_patterns.items():
        if "(" in pattern and any(c.isdigit() for c in pattern):
            print(f"  패턴: {pattern}")
            try:
                regex = re.compile(pattern)
                matches = list(regex.finditer(en_test))
                print(f"    매치 결과: {len(matches)} 개")
                for match in matches:
                    print(f"      매칭: {match.group(0)}")
            except Exception as e:
                print(f"    에러: {e}")

if __name__ == "__main__":
    debug_time_extraction() 