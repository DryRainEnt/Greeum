from typing import List, Dict, Any, Optional
from datetime import datetime

from .cache_manager import CacheManager
from .stm_manager import STMManager

class PromptWrapper:
    """프롬프트 조합기 클래스"""
    
    def __init__(self, 
                 cache_manager: Optional[CacheManager] = None,
                 stm_manager: Optional[STMManager] = None):
        """
        프롬프트 조합기 초기화
        
        Args:
            cache_manager: 캐시 매니저 인스턴스 (없으면 자동 생성)
            stm_manager: STM 매니저 인스턴스 (없으면 자동 생성)
        """
        self.cache_manager = cache_manager or CacheManager()
        self.stm_manager = stm_manager or STMManager()
    
    def _format_memory_block(self, block: Dict[str, Any]) -> str:
        """
        메모리 블록을 프롬프트에 포함될 형식으로 변환
        
        Args:
            block: 메모리 블록
            
        Returns:
            포맷팅된 블록 텍스트
        """
        timestamp = block.get("timestamp", "")
        if timestamp:
            try:
                dt = datetime.fromisoformat(timestamp)
                timestamp = dt.strftime("%Y-%m-%d %H:%M")
            except (ValueError, TypeError):
                pass
                
        context = block.get("context", "")
        relevance = block.get("relevance", 0)
        importance = block.get("importance", 0)
        
        # 중요도와 관련성에 따라 메모리 순위 표시
        stars = "⭐" * int((relevance + importance) * 3)
        if not stars:
            stars = "⭐"
            
        return f"""[기억 {timestamp}] {stars}
{context}
"""
    
    def _format_stm_memory(self, memory: Dict[str, Any]) -> str:
        """
        단기 기억을 프롬프트에 포함될 형식으로 변환
        
        Args:
            memory: 단기 기억
            
        Returns:
            포맷팅된 기억 텍스트
        """
        timestamp = memory.get("timestamp", "")
        if timestamp:
            try:
                dt = datetime.fromisoformat(timestamp)
                timestamp = dt.strftime("%H:%M")
            except (ValueError, TypeError):
                pass
                
        content = memory.get("content", "")
        speaker = memory.get("speaker", "")
        
        if speaker:
            return f"[{timestamp}] {speaker}: {content}"
        else:
            return f"[{timestamp}] {content}"
    
    def compose_prompt(self, user_input: str, system_prompt: str = "") -> str:
        """
        LLM에 전달할 프롬프트 생성
        
        Args:
            user_input: 사용자 입력
            system_prompt: 시스템 프롬프트 (기본 지시사항)
            
        Returns:
            조합된 최종 프롬프트
        """
        # 캐시에서 웨이포인트 블록 가져오기
        waypoints = self.cache_manager.get_waypoints()
        waypoint_blocks = []
        
        for waypoint in waypoints:
            block_index = waypoint.get("block_index")
            if block_index is not None:
                block = self.cache_manager.block_manager.get_block_by_index(block_index)
                if block:
                    # 관련성 점수 추가
                    block["relevance"] = waypoint.get("relevance", 0)
                    waypoint_blocks.append(block)
        
        # 단기 기억 가져오기
        recent_memories = self.stm_manager.get_recent_memories(count=5)
        
        # 프롬프트 조합 시작
        prompt_parts = []
        
        # 1. 시스템 프롬프트 추가
        if system_prompt:
            prompt_parts.append(system_prompt)
        else:
            # 기본 시스템 프롬프트
            prompt_parts.append("""당신은 사용자와의 대화 내용과 기억을 가지고 있는 AI 어시스턴트입니다.
아래에 제공된 기억과 대화 기록을 바탕으로 사용자의 질문에 자연스럽게 답변해주세요.
기억은 '기억'으로 표시되어 있으며, 과거 대화는 시간과 함께 제공됩니다.""")
        
        # 2. 웨이포인트 블록 추가 (중요 장기 기억)
        if waypoint_blocks:
            prompt_parts.append("\n## 관련 기억:")
            for block in waypoint_blocks:
                prompt_parts.append(self._format_memory_block(block))
        
        # 3. 단기 기억 (최근 대화) 추가
        if recent_memories:
            prompt_parts.append("\n## 최근 대화:")
            for memory in recent_memories:
                prompt_parts.append(self._format_stm_memory(memory))
        
        # 4. 현재 사용자 입력 추가
        prompt_parts.append(f"\n## 현재 입력:\n{user_input}")
        
        # 최종 프롬프트 조합
        return "\n".join(prompt_parts)
    
    def compose_prompt_with_custom_blocks(self, 
                                         user_input: str, 
                                         memory_blocks: List[Dict[str, Any]],
                                         system_prompt: str = "") -> str:
        """
        직접 지정한 메모리 블록으로 프롬프트 생성
        
        Args:
            user_input: 사용자 입력
            memory_blocks: 직접 지정한 메모리 블록 목록
            system_prompt: 시스템 프롬프트 (기본 지시사항)
            
        Returns:
            조합된 최종 프롬프트
        """
        # 단기 기억 가져오기
        recent_memories = self.stm_manager.get_recent_memories(count=5)
        
        # 프롬프트 조합 시작
        prompt_parts = []
        
        # 1. 시스템 프롬프트 추가
        if system_prompt:
            prompt_parts.append(system_prompt)
        else:
            # 기본 시스템 프롬프트
            prompt_parts.append("""당신은 사용자와의 대화 내용과 기억을 가지고 있는 AI 어시스턴트입니다.
아래에 제공된 기억과 대화 기록을 바탕으로 사용자의 질문에 자연스럽게 답변해주세요.
기억은 '기억'으로 표시되어 있으며, 과거 대화는 시간과 함께 제공됩니다.""")
        
        # 2. 지정한 메모리 블록 추가
        if memory_blocks:
            prompt_parts.append("\n## 관련 기억:")
            for block in memory_blocks:
                prompt_parts.append(self._format_memory_block(block))
        
        # 3. 단기 기억 (최근 대화) 추가
        if recent_memories:
            prompt_parts.append("\n## 최근 대화:")
            for memory in recent_memories:
                prompt_parts.append(self._format_stm_memory(memory))
        
        # 4. 현재 사용자 입력 추가
        prompt_parts.append(f"\n## 현재 입력:\n{user_input}")
        
        # 최종 프롬프트 조합
        return "\n".join(prompt_parts) 