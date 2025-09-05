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
            
            # TTL 기반 시스템이므로 슬롯 제한 없음, 시간 기반 만료만 존재
            return {
                'active_count': active_count,
                'available_slots': 'unlimited (TTL-based)',
                'total_slots': 'Time-based expiration',
                'ttl_seconds': self.ttl,
                'storage_type': 'TTL-based cache'
            }
        except Exception as e:
            # 오류 발생 시 기본값 반환 (TTL 기반이므로 슬롯 제한 없음)
            return {
                'active_count': 0,
                'available_slots': 'unlimited',
                'total_slots': 'TTL-based',
                'ttl_seconds': self.ttl
            }