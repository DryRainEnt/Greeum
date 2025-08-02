import time
from typing import List, Dict, Any, Optional
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
        
    def clean_expired(self) -> int:
        """만료된 기억 제거 (DatabaseManager 사용)"""
        deleted_count = self.db_manager.delete_expired_short_term_memories(self.ttl)
        return deleted_count
    
    def add_memory(self, memory_data: Dict[str, Any]) -> Optional[str]:
        """
        단기 기억 추가 (DatabaseManager 사용)
        
        Args:
            memory_data: 기억 데이터 (id, timestamp, content, speaker, metadata 포함 가능)
        Returns:
            추가된 기억의 ID 또는 None (실패 시)
        """
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