import re
import sys

def test_regex():
    # 테스트할 정규식 패턴
    pattern = r"(\d+)일 전"
    text = "3일 전에 보낸 이메일을 찾아줘"
    
    print(f"Python 버전: {sys.version}")
    print(f"테스트 문자열: {text}")
    print(f"테스트 패턴: {pattern}")
    
    # 방법 1: re.finditer
    try:
        matches = list(re.finditer(pattern, text))
        print(f"re.finditer 결과: {len(matches)}")
        for match in matches:
            print(f"  Match: {match.group(0)}, Capture: {match.group(1)}")
    except Exception as e:
        print(f"re.finditer 에러: {e}")
    
    # 방법 2: 문자열 패턴 직접 컴파일
    try:
        pattern_str = "(\d+)일 전"
        regex = re.compile(pattern_str)
        matches = list(regex.finditer(text))
        print(f"문자열 패턴 컴파일 결과: {len(matches)}")
        for match in matches:
            print(f"  Match: {match.group(0)}, Capture: {match.group(1)}")
    except Exception as e:
        print(f"패턴 컴파일 에러: {e}")
    
    # 방법 3: 원시 문자열 패턴 사용
    try:
        raw_pattern = r"(\d+)일 전"
        regex = re.compile(raw_pattern)
        matches = list(regex.finditer(text))
        print(f"원시 문자열 패턴 결과: {len(matches)}")
        for match in matches:
            print(f"  Match: {match.group(0)}, Capture: {match.group(1)}")
    except Exception as e:
        print(f"원시 문자열 패턴 에러: {e}")
    
    # 방법 4: re.search 사용
    try:
        match = re.search(pattern, text)
        if match:
            print(f"re.search 결과: {match.group(0)}, Capture: {match.group(1)}")
        else:
            print("re.search 결과: 매치 없음")
    except Exception as e:
        print(f"re.search 에러: {e}")
    
    # 방법 5: 이스케이프 처리
    try:
        escaped_pattern = "([0-9]+)일 전"
        regex = re.compile(escaped_pattern)
        matches = list(regex.finditer(text))
        print(f"이스케이프 패턴 결과: {len(matches)}")
        for match in matches:
            print(f"  Match: {match.group(0)}, Capture: {match.group(1)}")
    except Exception as e:
        print(f"이스케이프 패턴 에러: {e}")

if __name__ == "__main__":
    test_regex() 