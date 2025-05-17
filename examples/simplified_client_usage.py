"""
간소화된 Greeum 클라이언트 사용 예제

이 예제는 LLM 통합에 사용하기 편리한 SimplifiedMemoryClient의 사용법을 보여줍니다.
"""

import logging
from greeum.client import SimplifiedMemoryClient

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def main():
    # 간소화된 클라이언트 초기화
    client = SimplifiedMemoryClient(
        base_url="http://localhost:8000",
        max_retries=3,
        timeout=10
    )
    
    # 서버 상태 확인
    health = client.get_health()
    if health["success"]:
        print(f"서버 상태: 온라인 (버전: {health['version']})")
    else:
        print(f"서버 상태: 오프라인 - {health.get('error')}")
        return
    
    # 새 기억 추가
    memory_result = client.add(
        content="Greeum을 사용하여 LLM의 기억 관리 시스템을 테스트합니다.",
        importance=0.8
    )
    
    if memory_result["success"]:
        block_index = memory_result["block_index"]
        print(f"기억 추가 성공 (인덱스: {block_index})")
        print(f"추출된 키워드: {memory_result['keywords']}")
    else:
        print(f"기억 추가 실패: {memory_result.get('error')}")
        return
    
    # 기억 검색
    search_results = client.search("LLM 기억", limit=3)
    
    if search_results:
        print("\n검색 결과:")
        for i, result in enumerate(search_results):
            print(f"{i+1}. [{result['timestamp']}] (관련성: {result['relevance']:.2f}) {result['content']}")
    else:
        print("검색 결과 없음")
    
    # LLM 프롬프트용 기억 문자열 가져오기
    memory_text = client.remember("기억 관리", limit=2)
    print("\nLLM 프롬프트용 기억 문자열:")
    print(memory_text)
    
    # 기억 업데이트
    update_result = client.update(
        block_index=block_index,
        new_content="업데이트: Greeum을 사용한 LLM 기억 관리 시스템은 매우 유용합니다.",
        reason="내용 개선"
    )
    
    if update_result["success"]:
        print(f"\n기억 업데이트 성공 (새 인덱스: {update_result['block_index']})")
    else:
        print(f"\n기억 업데이트 실패: {update_result.get('error')}")

if __name__ == "__main__":
    main() 