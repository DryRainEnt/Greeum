"""
Short-Term Memory (STM) Layer Implementation for Greeum v2.6.0

Implements session-based memory with TTL management, optimized for
temporary storage and rapid access patterns.
"""

import time
import json
import uuid
from typing import List, Dict, Any, Optional, Set
from datetime import datetime, timedelta
from collections import defaultdict

from .memory_layer import (
    MemoryLayerInterface, MemoryLayerType, MemoryPriority,
    MemoryItem, LayerTransferRequest
)
from .database_manager import DatabaseManager


class STMIndex:
    """STM 전용 인메모리 인덱스"""
    
    def __init__(self):
        self.keyword_index: Dict[str, Set[str]] = defaultdict(set)
        self.tag_index: Dict[str, Set[str]] = defaultdict(set)
        self.priority_index: Dict[MemoryPriority, Set[str]] = defaultdict(set)
        self.timestamp_index: List[tuple] = []  # (timestamp, memory_id)
        
    def add_memory(self, memory_item: MemoryItem):
        """메모리 인덱스에 추가"""
        memory_id = memory_item.id
        
        # 키워드 인덱스
        for keyword in memory_item.keywords:
            self.keyword_index[keyword.lower()].add(memory_id)
        
        # 태그 인덱스
        for tag in memory_item.tags:
            self.tag_index[tag.lower()].add(memory_id)
        
        # 우선순위 인덱스
        self.priority_index[memory_item.priority].add(memory_id)
        
        # 시간 인덱스 (정렬 유지)
        timestamp_tuple = (memory_item.timestamp, memory_id)
        self.timestamp_index.append(timestamp_tuple)
        self.timestamp_index.sort(key=lambda x: x[0], reverse=True)
    
    def remove_memory(self, memory_item: MemoryItem):
        """메모리 인덱스에서 제거"""
        memory_id = memory_item.id
        
        # 키워드 인덱스
        for keyword in memory_item.keywords:
            self.keyword_index[keyword.lower()].discard(memory_id)
        
        # 태그 인덱스
        for tag in memory_item.tags:
            self.tag_index[tag.lower()].discard(memory_id)
        
        # 우선순위 인덱스
        self.priority_index[memory_item.priority].discard(memory_id)
        
        # 시간 인덱스
        self.timestamp_index = [(ts, mid) for ts, mid in self.timestamp_index if mid != memory_id]
    
    def search_by_keywords(self, keywords: List[str]) -> Set[str]:
        """키워드로 메모리 ID 검색"""
        if not keywords:
            return set()
        
        result_sets = [self.keyword_index[kw.lower()] for kw in keywords]
        return set.intersection(*result_sets) if result_sets else set()
    
    def search_by_tags(self, tags: List[str]) -> Set[str]:
        """태그로 메모리 ID 검색"""
        if not tags:
            return set()
        
        result_sets = [self.tag_index[tag.lower()] for tag in tags]
        return set.intersection(*result_sets) if result_sets else set()
    
    def get_recent_memories(self, limit: int = 10) -> List[str]:
        """최근 메모리 ID 목록"""
        return [mid for _, mid in self.timestamp_index[:limit]]


class STMLayer(MemoryLayerInterface):
    """단기 기억 계층 구현"""
    
    def __init__(self, db_manager: DatabaseManager = None, 
                 default_ttl: int = 3600,  # 1시간
                 max_capacity: int = 1000):
        super().__init__(MemoryLayerType.STM)
        
        self.db_manager = db_manager or DatabaseManager()
        self.default_ttl = default_ttl
        self.max_capacity = max_capacity
        
        # 인메모리 캐시 및 인덱스
        self.memory_cache: Dict[str, MemoryItem] = {}
        self.index = STMIndex()
        
        # 세션 관리
        self.session_memories: Dict[str, Set[str]] = defaultdict(set)
        self.current_session_id = str(uuid.uuid4())
        
        # 통계
        self.stats = {
            "total_added": 0,
            "total_expired": 0,
            "total_transferred": 0,
            "cache_hits": 0,
            "cache_misses": 0
        }
    
    def initialize(self) -> bool:
        """STM 계층 초기화"""
        try:
            # 데이터베이스에서 기존 STM 메모리 로드
            self._load_existing_memories()
            self._initialized = True
            return True
        except Exception as e:
            print(f"STM Layer initialization failed: {e}")
            return False
    
    def _load_existing_memories(self):
        """데이터베이스에서 기존 STM 메모리 로드"""
        try:
            # STM 테이블에서 만료되지 않은 메모리들 로드 (직접 SQL)
            cursor = self.db_manager.conn.cursor()
            cursor.execute("SELECT * FROM short_term_memories")
            stm_memories = cursor.fetchall()
            
            for memory_data in stm_memories:
                # 만료되지 않은 것만 로드 (timestamp 필드 사용)
                created_time = datetime.fromisoformat(memory_data['timestamp'])
                if self._is_expired(created_time):
                    continue
                
                memory_item = self._convert_from_db(dict(memory_data))
                self.memory_cache[memory_item.id] = memory_item
                self.index.add_memory(memory_item)
                
        except Exception as e:
            print(f"Failed to load existing STM memories: {e}")
    
    def _convert_from_db(self, db_data: Dict[str, Any]) -> MemoryItem:
        """데이터베이스 데이터를 MemoryItem으로 변환"""
        metadata = json.loads(db_data.get('metadata', '{}'))
        
        return MemoryItem(
            id=db_data['id'],
            content=db_data['content'],
            timestamp=datetime.fromisoformat(db_data['timestamp']),  # timestamp 필드 사용
            layer=MemoryLayerType.STM,
            priority=MemoryPriority(metadata.get('priority', 0.6)),
            metadata=metadata,
            keywords=metadata.get('keywords', []),
            tags=metadata.get('tags', []),
            embedding=metadata.get('embedding', []),
            importance=metadata.get('importance', 0.5)
        )
    
    def _convert_to_db(self, memory_item: MemoryItem) -> Dict[str, Any]:
        """MemoryItem을 데이터베이스 형식으로 변환"""
        metadata = memory_item.metadata.copy()
        metadata.update({
            'priority': memory_item.priority.value,
            'keywords': memory_item.keywords,
            'tags': memory_item.tags,
            'embedding': memory_item.embedding,
            'importance': memory_item.importance,
            'session_id': self.current_session_id
        })
        
        return {
            'id': memory_item.id,
            'content': memory_item.content,
            'importance': memory_item.importance,
            'created_at': memory_item.timestamp.isoformat(),
            'ttl_seconds': self.default_ttl,
            'metadata': json.dumps(metadata, ensure_ascii=False)
        }
    
    def add_memory(self, memory_item: MemoryItem) -> str:
        """STM에 메모리 추가"""
        try:
            # 용량 체크 및 정리
            if len(self.memory_cache) >= self.max_capacity:
                self._cleanup_low_priority()
            
            # 메모리 ID 설정
            if not memory_item.id:
                memory_item.id = str(uuid.uuid4())
            
            # 계층 및 타임스탬프 설정
            memory_item.layer = MemoryLayerType.STM
            memory_item.timestamp = datetime.now()
            
            # 캐시 및 인덱스에 추가
            self.memory_cache[memory_item.id] = memory_item
            self.index.add_memory(memory_item)
            
            # 세션에 추가
            self.session_memories[self.current_session_id].add(memory_item.id)
            
            # 데이터베이스에 저장
            db_data = self._convert_to_db(memory_item)
            
            # STM 테이블에 직접 INSERT (add_short_term_memory 대신)
            cursor = self.db_manager.conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO short_term_memories 
                (id, timestamp, content, speaker, metadata) 
                VALUES (?, ?, ?, ?, ?)
            """, (
                db_data['id'],
                db_data['created_at'],
                db_data['content'],
                'user',  # speaker
                db_data['metadata']
            ))
            self.db_manager.conn.commit()
            
            # 통계 업데이트
            self.stats["total_added"] += 1
            
            return memory_item.id
            
        except Exception as e:
            print(f"Failed to add STM memory: {e}")
            return ""
    
    def get_memory(self, memory_id: str) -> Optional[MemoryItem]:
        """특정 메모리 조회"""
        # 캐시에서 먼저 확인
        if memory_id in self.memory_cache:
            memory_item = self.memory_cache[memory_id]
            
            # 만료 체크
            if self._is_expired(memory_item.timestamp):
                self._remove_expired_memory(memory_id)
                return None
            
            self.stats["cache_hits"] += 1
            return memory_item
        
        # 캐시 미스
        self.stats["cache_misses"] += 1
        return None
    
    def search_memories(self, query: str, limit: int = 10, 
                       filters: Dict[str, Any] = None) -> List[MemoryItem]:
        """STM 메모리 검색"""
        if filters is None:
            filters = {}
        
        # 만료된 메모리 정리
        self.cleanup_expired()
        
        candidate_ids = set()
        
        # 키워드 검색
        if 'keywords' in filters:
            keyword_ids = self.index.search_by_keywords(filters['keywords'])
            candidate_ids.update(keyword_ids)
        
        # 태그 검색
        if 'tags' in filters:
            tag_ids = self.index.search_by_tags(filters['tags'])
            candidate_ids.update(tag_ids)
        
        # 텍스트 검색 (단순 포함 검색)
        if not candidate_ids:
            query_lower = query.lower()
            for memory_id, memory_item in self.memory_cache.items():
                if query_lower in memory_item.content.lower():
                    candidate_ids.add(memory_id)
        
        # 결과 수집 및 정렬
        results = []
        for memory_id in candidate_ids:
            memory_item = self.get_memory(memory_id)
            if memory_item:
                results.append(memory_item)
        
        # 우선순위와 시간순으로 정렬
        results.sort(key=lambda x: (x.priority.value, x.timestamp), reverse=True)
        
        return results[:limit]
    
    def update_memory(self, memory_id: str, updates: Dict[str, Any]) -> bool:
        """STM 메모리 업데이트"""
        try:
            memory_item = self.get_memory(memory_id)
            if not memory_item:
                return False
            
            # 인덱스에서 제거 (업데이트 전)
            self.index.remove_memory(memory_item)
            
            # 업데이트 적용
            if 'content' in updates:
                memory_item.content = updates['content']
            if 'keywords' in updates:
                memory_item.keywords = updates['keywords']
            if 'tags' in updates:
                memory_item.tags = updates['tags']
            if 'importance' in updates:
                memory_item.importance = updates['importance']
            if 'priority' in updates:
                memory_item.priority = updates['priority']
            if 'metadata' in updates:
                memory_item.metadata.update(updates['metadata'])
            
            # 인덱스에 다시 추가
            self.index.add_memory(memory_item)
            
            # 데이터베이스 업데이트 (직접 SQL)
            db_data = self._convert_to_db(memory_item)
            cursor = self.db_manager.conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO short_term_memories 
                (id, timestamp, content, speaker, metadata) 
                VALUES (?, ?, ?, ?, ?)
            """, (
                db_data['id'],
                db_data['created_at'],
                db_data['content'],
                'user',  # speaker
                db_data['metadata']
            ))
            self.db_manager.conn.commit()
            
            return True
            
        except Exception as e:
            print(f"Failed to update STM memory: {e}")
            return False
    
    def delete_memory(self, memory_id: str) -> bool:
        """STM 메모리 삭제"""
        try:
            memory_item = self.memory_cache.get(memory_id)
            if not memory_item:
                return False
            
            # 인덱스에서 제거
            self.index.remove_memory(memory_item)
            
            # 캐시에서 제거
            del self.memory_cache[memory_id]
            
            # 세션에서 제거
            for session_memories in self.session_memories.values():
                session_memories.discard(memory_id)
            
            # 데이터베이스에서 삭제
            cursor = self.db_manager.conn.cursor()
            cursor.execute("DELETE FROM short_term_memories WHERE id = ?", (memory_id,))
            self.db_manager.conn.commit()
            
            return True
            
        except Exception as e:
            print(f"Failed to delete STM memory: {e}")
            return False
    
    def cleanup_expired(self) -> int:
        """만료된 메모리 정리"""
        expired_count = 0
        expired_ids = []
        
        # 만료된 메모리 찾기
        for memory_id, memory_item in list(self.memory_cache.items()):
            if self._is_expired(memory_item.timestamp):
                expired_ids.append(memory_id)
        
        # 정리 실행
        for memory_id in expired_ids:
            if self._remove_expired_memory(memory_id):
                expired_count += 1
        
        self.stats["total_expired"] += expired_count
        return expired_count
    
    def _is_expired(self, timestamp: datetime) -> bool:
        """메모리 만료 여부 확인"""
        expiry_time = timestamp + timedelta(seconds=self.default_ttl)
        return datetime.now() > expiry_time
    
    def _remove_expired_memory(self, memory_id: str) -> bool:
        """만료된 메모리 제거"""
        try:
            memory_item = self.memory_cache.get(memory_id)
            if memory_item:
                self.index.remove_memory(memory_item)
                del self.memory_cache[memory_id]
                
                # 세션에서도 제거
                for session_memories in self.session_memories.values():
                    session_memories.discard(memory_id)
            
            # 데이터베이스에서도 삭제
            cursor = self.db_manager.conn.cursor()
            cursor.execute("DELETE FROM short_term_memories WHERE id = ?", (memory_id,))
            self.db_manager.conn.commit()
            
            return True
        except Exception as e:
            print(f"Failed to remove expired memory: {e}")
            return False
    
    def _cleanup_low_priority(self):
        """용량 초과 시 낮은 우선순위 메모리 정리"""
        # 낮은 우선순위부터 정리
        for priority in [MemoryPriority.DISPOSABLE, MemoryPriority.LOW]:
            if len(self.memory_cache) < self.max_capacity:
                break
                
            memory_ids = list(self.index.priority_index[priority])
            for memory_id in memory_ids[:len(memory_ids)//2]:  # 절반 정리
                self.delete_memory(memory_id)
    
    def get_layer_stats(self) -> Dict[str, Any]:
        """STM 계층 통계"""
        self.cleanup_expired()
        
        return {
            "layer_type": "STM",
            "total_count": len(self.memory_cache),
            "max_capacity": self.max_capacity,
            "current_session_id": self.current_session_id,
            "session_count": len(self.session_memories),
            "default_ttl": self.default_ttl,
            "stats": self.stats.copy(),
            "priority_distribution": {
                priority.name: len(memory_ids) 
                for priority, memory_ids in self.index.priority_index.items()
            }
        }
    
    def can_accept_transfer(self, transfer_request: LayerTransferRequest) -> bool:
        """전송 요청 수락 가능 여부"""
        # STM은 Working Memory에서의 전송만 수락
        if transfer_request.source_layer != MemoryLayerType.WORKING:
            return False
        
        # 용량 확인
        if len(self.memory_cache) >= self.max_capacity:
            return False
        
        return True
    
    def transfer_to_layer(self, transfer_request: LayerTransferRequest) -> bool:
        """다른 계층으로 메모리 전송 (STM → LTM)"""
        # STM에서는 LTM으로만 전송 가능
        if transfer_request.target_layer != MemoryLayerType.LTM:
            return False
        
        memory_item = self.get_memory(transfer_request.memory_id)
        if not memory_item:
            return False
        
        # 전송 조건 확인 (높은 우선순위 + 중요도)
        if (memory_item.priority.value < MemoryPriority.HIGH.value or 
            memory_item.importance < 0.7):
            return False
        
        self.stats["total_transferred"] += 1
        return True
    
    def start_new_session(self) -> str:
        """새 세션 시작"""
        self.current_session_id = str(uuid.uuid4())
        return self.current_session_id
    
    def get_session_memories(self, session_id: str = None) -> List[MemoryItem]:
        """특정 세션의 메모리 조회"""
        target_session = session_id or self.current_session_id
        memory_ids = self.session_memories.get(target_session, set())
        
        results = []
        for memory_id in memory_ids:
            memory_item = self.get_memory(memory_id)
            if memory_item:
                results.append(memory_item)
        
        # 시간순 정렬
        results.sort(key=lambda x: x.timestamp, reverse=True)
        return results