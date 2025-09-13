import time
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from .database_manager import DatabaseManager
import logging

logger = logging.getLogger(__name__)

class STMManager:
    """단기 기억(Short-Term Memory)을 관리하는 클래스 - Branch/DFS 헤드 포인터 역할"""
    
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
        
        # Branch/DFS: STM slots as branch head pointers
        self.branch_heads = {
            "A": None,  # Slot A head block ID
            "B": None,  # Slot B head block ID  
            "C": None   # Slot C head block ID
        }
        
        # Hysteresis tracking for slot stability
        self.slot_hysteresis = {
            "A": {"last_seen_at": 0, "access_count": 0},
            "B": {"last_seen_at": 0, "access_count": 0},
            "C": {"last_seen_at": 0, "access_count": 0}
        }
        
        # Initialize slots from most recent blocks
        self._initialize_branch_heads()
        
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
    
    def _initialize_branch_heads(self):
        """Initialize branch heads from database or recent blocks"""
        try:
            cursor = self.db_manager.conn.cursor()
            
            # First try to restore from branch_meta
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='branch_meta'
            """)
            
            if cursor.fetchone():
                # Try to load saved heads
                cursor.execute("""
                    SELECT heads FROM branch_meta 
                    ORDER BY last_modified DESC 
                    LIMIT 1
                """)
                result = cursor.fetchone()
                
                if result and result[0]:
                    import json
                    try:
                        saved_heads = json.loads(result[0])
                        if isinstance(saved_heads, dict) and saved_heads:
                            self.branch_heads.update(saved_heads)
                            for slot in self.branch_heads:
                                self.slot_hysteresis[slot]["last_seen_at"] = time.time()
                            logger.info(f"Restored branch heads from database: {list(saved_heads.keys())}")
                            return
                    except json.JSONDecodeError:
                        pass
            
            # Fallback: Initialize from recent blocks
            # Check if root column exists
            cursor.execute("PRAGMA table_info(blocks)")
            columns = {row[1] for row in cursor.fetchall()}
            
            if 'root' in columns:
                cursor.execute("""
                    SELECT block_index, hash, root, timestamp 
                    FROM blocks 
                    ORDER BY timestamp DESC 
                    LIMIT 3
                """)
            else:
                # Fallback without root column
                cursor.execute("""
                    SELECT block_index, hash, NULL as root, timestamp 
                    FROM blocks 
                    ORDER BY timestamp DESC 
                    LIMIT 3
                """)
            
            recent_blocks = cursor.fetchall()
            
            slots = ["A", "B", "C"]
            for i, block in enumerate(recent_blocks):
                if i < len(slots):
                    self.branch_heads[slots[i]] = block[1]  # Use hash as block ID
                    self.slot_hysteresis[slots[i]]["last_seen_at"] = time.time()
                    logger.debug(f"Initialized slot {slots[i]} with block {block[0]}")
                    
        except Exception as e:
            logger.warning(f"Failed to initialize branch heads: {e}")
    
    def get_active_head(self, slot: str = None) -> Optional[str]:
        """Get active branch head for given slot or most recent"""
        if slot and slot in self.branch_heads:
            return self.branch_heads[slot]
        
        # Return most recently used head
        most_recent_slot = max(
            self.slot_hysteresis.keys(),
            key=lambda k: self.slot_hysteresis[k]["last_seen_at"]
        )
        return self.branch_heads[most_recent_slot]
    
    def update_head(self, slot: str, new_head_id: str):
        """Update branch head for given slot with persistence"""
        if slot not in self.branch_heads:
            logger.warning(f"Invalid slot: {slot}")
            return
        
        old_head = self.branch_heads[slot]
        self.branch_heads[slot] = new_head_id
        self.slot_hysteresis[slot]["last_seen_at"] = time.time()
        self.slot_hysteresis[slot]["access_count"] += 1
        
        # Persist to database (branch_meta table)
        try:
            cursor = self.db_manager.conn.cursor()
            
            # Get root from the new head block
            cursor.execute("SELECT root FROM blocks WHERE hash = ?", (new_head_id,))
            result = cursor.fetchone()
            root_id = result[0] if result and result[0] else new_head_id
            
            # Update or insert branch_meta
            import json
            heads_json = json.dumps(self.branch_heads)
            
            cursor.execute("""
                INSERT OR REPLACE INTO branch_meta (root, heads, last_modified)
                VALUES (?, ?, ?)
            """, (root_id, heads_json, time.time()))
            
            self.db_manager.conn.commit()
            
        except Exception as e:
            logger.warning(f"Failed to persist head update: {e}")
        
        logger.info(f"Updated slot {slot} head: {old_head} -> {new_head_id}")
    
    def get_branch_heads_info(self) -> Dict[str, Any]:
        """Get information about all branch heads"""
        info = {}
        for slot, head_id in self.branch_heads.items():
            if head_id:
                try:
                    cursor = self.db_manager.conn.cursor()
                    cursor.execute("""
                        SELECT block_index, root, timestamp, context
                        FROM blocks 
                        WHERE hash = ?
                    """, (head_id,))
                    block_info = cursor.fetchone()
                    
                    if block_info:
                        info[slot] = {
                            "head_id": head_id,
                            "block_index": block_info[0],
                            "root": block_info[1],
                            "timestamp": block_info[2],
                            "context_preview": block_info[3][:50] if block_info[3] else "",
                            "last_seen_at": self.slot_hysteresis[slot]["last_seen_at"],
                            "access_count": self.slot_hysteresis[slot]["access_count"]
                        }
                except Exception as e:
                    logger.warning(f"Failed to get info for slot {slot}: {e}")
                    
        return info