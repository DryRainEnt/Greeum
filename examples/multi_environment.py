"""
다양한 환경에서의 Greeum 사용 예제

이 예제는 다양한 환경(프록시 설정, 오류 처리 등)에서 Greeum 클라이언트를 활용하는 방법을 보여줍니다.
"""

import logging
from greeum.client import MemoryClient, SimplifiedMemoryClient
from greeum.client import ClientError, ConnectionFailedError, RequestTimeoutError, APIError

# 로깅 설정 (상세 레벨로 설정)
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def example_proxy_setup():
    """프록시 환경에서의 설정 예제"""
    print("\n=== 프록시 환경 설정 예제 ===")
    
    # 프록시 설정
    proxies = {
        "http": "http://proxy.example.com:8080",
        "https": "https://proxy.example.com:8080"
    }
    
    # 클라이언트 초기화 (실제 프록시가 없으므로 실행되지 않음)
    client = MemoryClient(
        base_url="http://localhost:8000",
        proxies=proxies,
        timeout=15,          # 타임아웃 늘리기
        max_retries=5,       # 재시도 횟수 늘리기
        retry_delay=2.0      # 재시도 간격 늘리기
    )
    
    print("프록시 설정이 있는 클라이언트 초기화 완료")
    print(f"프록시: {proxies}")
    print(f"타임아웃: {client.timeout}초")
    print(f"최대 재시도: {client.max_retries}회")
    print(f"재시도 간격: {client.retry_delay}초")

def example_error_handling():
    """오류 처리 예제"""
    print("\n=== 오류 처리 예제 ===")
    
    # 존재하지 않는 서버로 클라이언트 초기화
    client = MemoryClient(
        base_url="http://non-existent-server:8000",
        max_retries=2,
        retry_delay=0.5
    )
    
    try:
        # API 정보 조회 시도
        api_info = client.get_api_info()
        print(f"API 정보: {api_info}")
    except ConnectionFailedError as e:
        print(f"연결 실패 오류 처리: {e}")
    except RequestTimeoutError as e:
        print(f"타임아웃 오류 처리: {e}")
    except APIError as e:
        print(f"API 오류 처리 (코드: {e.status_code}): {e}")
    except ClientError as e:
        print(f"기타 클라이언트 오류: {e}")
    except Exception as e:
        print(f"예상치 못한 오류: {e}")

def example_advanced_retry():
    """고급 재시도 설정 예제"""
    print("\n=== 고급 재시도 설정 예제 ===")
    
    # 존재하지 않는 서버로 클라이언트 초기화 (사용자 정의 재시도 설정)
    client = MemoryClient(
        base_url="http://non-existent-server:8000",
        max_retries=3,
        retry_delay=1.0
    )
    
    # 요청을 실행하고 사용자 정의 재시도 상태 코드 설정
    # 이 예제에서는 실제 요청이 실행되지 않지만, 사용 방법을 보여줌
    try:
        # API 정보 조회 시도 (특정 상태 코드에서만 재시도)
        client._make_request(
            method="get", 
            endpoint="/", 
            retry_on_codes=[429, 503]  # 특정 상태 코드에서만 재시도
        )
    except ConnectionFailedError as e:
        print(f"연결 실패 오류: {e}")
    
    print("사용자 정의 재시도 설정:")
    print(f"- 최대 재시도: {client.max_retries}회")
    print(f"- 재시도 간격: {client.retry_delay}초")
    print("- 재시도할 상태 코드: [429, 503]")
    print("- 429 (Too Many Requests): 요청 제한 초과")
    print("- 503 (Service Unavailable): 서비스 일시적 사용 불가")

def example_simplified_client_error_handling():
    """간소화된 클라이언트 오류 처리 예제"""
    print("\n=== 간소화된 클라이언트 오류 처리 예제 ===")
    
    # 존재하지 않는 서버로 간소화된 클라이언트 초기화
    client = SimplifiedMemoryClient(
        base_url="http://non-existent-server:8000",
        max_retries=2
    )
    
    # 서버 상태 확인
    health = client.get_health()
    print(f"서버 상태: {health['status']}")
    if not health['success']:
        print(f"오류 메시지: {health.get('error')}")
    
    # 기억 추가 시도
    result = client.add("테스트 기억")
    print(f"기억 추가 성공 여부: {result['success']}")
    if not result['success']:
        print(f"오류 메시지: {result.get('error')}")

def main():
    print("=== Greeum 다양한 환경 활용 예제 ===")
    
    # 프록시 설정 예제
    example_proxy_setup()
    
    # 오류 처리 예제
    example_error_handling()
    
    # 고급 재시도 설정 예제
    example_advanced_retry()
    
    # 간소화된 클라이언트 오류 처리 예제
    example_simplified_client_error_handling()

if __name__ == "__main__":
    main() 