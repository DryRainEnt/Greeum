import time
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from .database_manager import DatabaseManager

class STMManager:
    """단기 기억(Short-Term Memory)을 관리하는 클래스 (DatabaseManager 사용)"""
    
    def __init__(self, db_manager: DatabaseManager, ttl: int = 3600):
        """
        단기 기억 매니저 초기화
        
        Args:
            db_manager: DatabaseManager 인스턴스
            ttl: Time-To-Live (초 단위, 기본값 1시간)
        """
        self.db_manager = db_manager
        self.ttl = ttl
        
        # STM → Working Memory 자동 승격 설정
        self.promotion_threshold = 0.75  # 유사도 임계값
        self.access_count_threshold = 3  # 접근 횟수 임계값
        self.memory_access_count = {}  # 메모리 ID별 접근 횟수
        
    def clean_expired(self) -> int:
        """만료된 기억 제거 (DatabaseManager 사용)"""
        deleted_count = self.db_manager.delete_expired_short_term_memories(self.ttl)
        return deleted_count
    
    def add_memory(self, content: str = None, memory_data: Dict[str, Any] = None, importance: float = 0.5) -> Optional[str]:
        """
        단기 기억 추가 (DatabaseManager 사용)
        
        Args:
            content: 메모리 내용 (문자열로 직접 전달)
            memory_data: 기억 데이터 딕셔너리 (id, timestamp, content, speaker, metadata 포함 가능)
            importance: 중요도 (0.0~1.0)
        Returns:
            추가된 기억의 ID 또는 None (실패 시)
        """
        # content만 전달된 경우 memory_data 구성
        if content and not memory_data:
            memory_data = {
                'content': content,
                'importance': importance
            }
        elif memory_data and importance != 0.5:
            memory_data['importance'] = importance
        try:
            if 'id' not in memory_data or not memory_data['id']:
                import uuid
                memory_data['id'] = str(uuid.uuid4())
            if 'timestamp' not in memory_data or not memory_data['timestamp']:
                 memory_data['timestamp'] = datetime.now().isoformat()

            memory_id = self.db_manager.add_short_term_memory(memory_data)
            self.clean_expired()
            return memory_id
        except Exception as e:
            print(f"Error adding short term memory: {e}")
            return None

    def get_recent_memories(self, count: int = 10) -> List[Dict[str, Any]]:
        """
        최근 기억 조회 (DatabaseManager 사용)
        """
        self.clean_expired()
        return self.db_manager.get_recent_short_term_memories(count)
    
    def clear_all(self) -> int:
        """모든 단기 기억 삭제 (DatabaseManager 사용)"""
        return self.db_manager.clear_short_term_memories()
    
    def get_memory_by_id(self, memory_id: str) -> Optional[Dict[str, Any]]:
        """ID로 단기 기억 조회 (DatabaseManager에 기능 구현 가정)"""
        return self.db_manager.get_short_term_memory_by_id(memory_id)
    
    def check_promotion_to_working_memory(self, memory_id: str, query_embedding: Optional[np.ndarray] = None) -> bool:
        """
        STM 메모리가 Working Memory로 승격될 조건 확인
        
        Args:
            memory_id: 메모리 ID
            query_embedding: 쿼리 임베딩 (유사도 계산용)
            
        Returns:
            승격 가능 여부
        """
        # 접근 횟수 증가
        self.memory_access_count[memory_id] = self.memory_access_count.get(memory_id, 0) + 1
        
        # 접근 횟수 기반 승격
        if self.memory_access_count[memory_id] >= self.access_count_threshold:
            return True
            
        # 벡터 유사도 기반 승격 (임베딩이 제공된 경우)
        if query_embedding is not None:
            memory = self.get_memory_by_id(memory_id)
            if memory and 'embedding' in memory:
                memory_embedding = np.array(memory['embedding'])
                similarity = np.dot(query_embedding, memory_embedding) / (
                    np.linalg.norm(query_embedding) * np.linalg.norm(memory_embedding)
                )
                if similarity >= self.promotion_threshold:
                    return True
                    
        return False
    
    def promote_to_ltm(self, memory_id: str) -> Optional[int]:
        """
        STM 메모리를 LTM으로 승격
        
        Args:
            memory_id: 승격할 메모리 ID
            
        Returns:
            생성된 LTM 블록 인덱스
        """
        memory = self.get_memory_by_id(memory_id)
        if not memory:
            return None
            
        try:
            from .block_manager import BlockManager
            block_manager = BlockManager(self.db_manager)
            
            # LTM 블록으로 변환
            block = block_manager.add_block(
                context=memory.get('content', ''),
                keywords=memory.get('keywords', []),
                tags=['promoted_from_stm'],
                embedding=memory.get('embedding'),
                importance=0.8  # 승격된 메모리는 높은 중요도
            )
            
            if block is not None:
                # STM에서 제거
                self.db_manager.delete_short_term_memory(memory_id)
                del self.memory_access_count[memory_id]
                # block is now just the index (int), not a dict
                return block
                
        except Exception as e:
            print(f"Error promoting STM to LTM: {e}")
            
        return None
    
    def get_stats(self) -> Dict[str, Any]:
        """
        단기 기억 통계 정보 조회
        
        Returns:
            Dict[str, Any]: 활성 슬롯 수, 사용 가능한 슬롯 수 등 통계 정보
        """
        try:
            # 만료된 기억 정리
            self.clean_expired()
            
            # 현재 활성 기억 개수 조회
            recent_memories = self.get_recent_memories(count=100)  # 충분히 많은 수로 조회
            active_count = len(recent_memories) if recent_memories else 0
            
            # 승격 대기 메모리 수
            promotion_ready = sum(1 for count in self.memory_access_count.values() 
                                if count >= self.access_count_threshold)
            
            # TTL 기반 시스템이므로 슬롯 제한 없음, 시간 기반 만료만 존재
            return {
                'active_count': active_count,
                'available_slots': 'unlimited (TTL-based)',
                'total_slots': 'Time-based expiration',
                'ttl_seconds': self.ttl,
                'storage_type': 'TTL-based cache',
                'promotion_ready': promotion_ready,
                'promotion_threshold': self.promotion_threshold,
                'access_count_threshold': self.access_count_threshold
            }
        except Exception as e:
            # 오류 발생 시 기본값 반환 (TTL 기반이므로 슬롯 제한 없음)
            return {
                'active_count': 0,
                'available_slots': 'unlimited',
                'total_slots': 'TTL-based',
                'ttl_seconds': self.ttl
            }