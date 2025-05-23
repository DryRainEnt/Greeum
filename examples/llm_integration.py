"""
Greeum과 LLM 통합 예제

이 예제는 Greeum 메모리 시스템을 외부 LLM과 통합하는 방법을 보여줍니다.
여기서는 OpenAI의 GPT를 예시로 사용하지만, 다른 LLM API에도 적용할 수 있습니다.
"""

import os
import logging
from typing import List, Dict, Any
from greeum.client import SimplifiedMemoryClient

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# OpenAI 모듈 가져오기 (설치가 필요합니다: pip install openai)
try:
    from openai import OpenAI
except ImportError:
    print("이 예제를 실행하려면 OpenAI 패키지가 필요합니다.")
    print("설치: pip install openai")
    import sys
    sys.exit(1)

class MemoryAugmentedLLM:
    """Greeum 메모리로 증강된 LLM 인터페이스"""
    
    def __init__(self, api_key: str = None, greeum_url: str = "http://localhost:8000"):
        """
        메모리 증강 LLM 초기화
        
        Args:
            api_key: OpenAI API 키 (None이면 환경 변수에서 가져옴)
            greeum_url: Greeum API 서버 URL
        """
        # OpenAI 클라이언트 초기화
        self.client = OpenAI(api_key=api_key)
        
        # Greeum 클라이언트 초기화
        self.memory = SimplifiedMemoryClient(base_url=greeum_url)
        
        # 대화 기록 저장
        self.conversation_history = []
    
    def add_to_memory(self, content: str, role: str = "user", importance: float = 0.5) -> Dict[str, Any]:
        """
        메모리에 내용 추가
        
        Args:
            content: 저장할 내용
            role: 발화자 역할 (user/assistant)
            importance: 중요도 (0.0-1.0)
            
        Returns:
            메모리 추가 결과
        """
        # 역할 정보를 포함하여 메모리에 저장
        if role == "system":
            prefixed_content = f"[시스템] {content}"
        elif role == "assistant":
            prefixed_content = f"[어시스턴트] {content}"
        else:
            prefixed_content = f"[사용자] {content}"
            
        return self.memory.add(prefixed_content, importance=importance)
    
    def query(self, user_input: str, search_query: str = None, 
             model: str = "gpt-3.5-turbo", temperature: float = 0.7) -> str:
        """
        사용자 입력에 대해 메모리 증강 응답 생성
        
        Args:
            user_input: 사용자 입력
            search_query: 메모리 검색 쿼리 (None이면 user_input 사용)
            model: 사용할 LLM 모델
            temperature: 응답 다양성 (0.0-1.0)
            
        Returns:
            LLM 응답
        """
        # 사용자 입력을 대화 기록에 추가
        self.conversation_history.append({"role": "user", "content": user_input})
        
        # 메모리에 사용자 입력 저장
        self.add_to_memory(user_input, role="user")
        
        # 관련 기억 검색 (검색 쿼리가 지정되지 않으면 사용자 입력 사용)
        search_query = search_query or user_input
        relevant_memories = self.memory.remember(search_query, limit=3)
        
        # 시스템 프롬프트 생성
        system_prompt = "당신은 사용자의 과거 대화와 관련된 기억을 가진 도움이 되는 AI 어시스턴트입니다."
        if relevant_memories and relevant_memories != "관련 기억을 찾을 수 없습니다.":
            system_prompt += "\n\n관련 기억:\n" + relevant_memories
        
        # LLM에 전달할 메시지 구성
        messages = [
            {"role": "system", "content": system_prompt}
        ]
        
        # 최근 대화 기록 추가 (최대 5개)
        messages.extend(self.conversation_history[-5:])
        
        # LLM 호출
        response = self.client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature
        )
        
        # 응답 내용 추출
        response_text = response.choices[0].message.content
        
        # 응답을 대화 기록과 메모리에 추가
        self.conversation_history.append({"role": "assistant", "content": response_text})
        self.add_to_memory(response_text, role="assistant", importance=0.6)
        
        return response_text


def main():
    # API 키 가져오기 (환경 변수 또는 직접 지정)
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("OPENAI_API_KEY 환경 변수가 설정되어 있지 않습니다.")
        print("환경 변수를 설정하거나 코드에서 직접 API 키를 제공하세요.")
        return
    
    # 메모리 증강 LLM 초기화
    memory_llm = MemoryAugmentedLLM(api_key=api_key)
    
    # 예제 대화
    print("-" * 50)
    print("Greeum 메모리 증강 LLM 예제를 시작합니다.")
    print("종료하려면 'exit'를 입력하세요.")
    print("-" * 50)
    
    while True:
        user_input = input("\n사용자: ")
        if user_input.lower() in ["exit", "quit", "종료"]:
            break
            
        # LLM 응답 생성
        response = memory_llm.query(user_input)
        print(f"\n어시스턴트: {response}")

if __name__ == "__main__":
    main() 