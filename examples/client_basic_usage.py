"""
기본 Greeum 클라이언트 사용 예제

이 예제는 Greeum API 클라이언트의 기본 사용법을 보여줍니다.
"""

import logging
from greeum.client import MemoryClient, ClientError, ConnectionFailedError, APIError

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def main():
    # 클라이언트 초기화
    client = MemoryClient(
        base_url="http://localhost:8000",  # 서버 URL
        max_retries=3,                     # 재시도 횟수
        timeout=10                         # 타임아웃 (초)
    )
    
    try:
        # API 정보 조회
        api_info = client.get_api_info()
        print(f"Greeum API 정보: {api_info}")
        
        # 새 기억 추가
        memory_response = client.add_memory(
            context="Greeum API 클라이언트 테스트 중입니다.",
            importance=0.7  # 중요도 설정 (0.0-1.0)
        )
        block_index = memory_response.get("block_index")
        print(f"기억 추가 완료. 인덱스: {block_index}")
        
        # 특정 기억 조회
        memory_data = client.get_memory(block_index)
        print(f"기억 조회 결과: {memory_data}")
        
        # 기억 검색
        search_results = client.search_memories(
            query="테스트",
            mode="hybrid",  # 검색 모드: embedding, keyword, temporal, hybrid
            limit=5
        )
        print(f"검색 결과: {search_results}")
        
        # 기억 업데이트
        update_response = client.update_memory(
            block_index=block_index,
            new_context="업데이트된 Greeum API 클라이언트 테스트 내용입니다.",
            reason="예제 테스트를 위한 업데이트"
        )
        print(f"업데이트 결과: {update_response}")
        
        # 수정 이력 조회
        revision_chain = client.get_revision_chain(block_index)
        print(f"수정 이력: {revision_chain}")
        
    except ConnectionFailedError as e:
        print(f"서버 연결 실패: {e}")
    except APIError as e:
        print(f"API 오류 (코드: {e.status_code}): {e}")
    except ClientError as e:
        print(f"클라이언트 오류: {e}")
    except Exception as e:
        print(f"예상치 못한 오류: {e}")

if __name__ == "__main__":
    main() 