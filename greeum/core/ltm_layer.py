"""
Long-Term Memory (LTM) Layer Implementation for Greeum v2.6.0

Implements permanent memory storage with blockchain-like immutable blocks,
actant structure support, and advanced relationship tracking.
"""

import json
import hashlib
import uuid
from typing import List, Dict, Any, Optional, Set, Tuple
from datetime import datetime
from collections import defaultdict

from .memory_layer import (
    MemoryLayerInterface, MemoryLayerType, MemoryPriority,
    MemoryItem, LayerTransferRequest
)
from .database_manager import DatabaseManager


class ActantStructure:
    """액탄트 구조 데이터"""
    
    def __init__(self, subject: str = None, action: str = None, 
                 object_target: str = None, confidence: float = 0.0):
        self.subject = subject
        self.action = action
        self.object_target = object_target
        self.confidence = confidence
        self.parsed_at = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'subject': self.subject,
            'action': self.action,
            'object_target': self.object_target,
            'confidence': self.confidence,
            'parsed_at': self.parsed_at.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ActantStructure':
        actant = cls(
            subject=data.get('subject'),
            action=data.get('action'),
            object_target=data.get('object_target'),
            confidence=data.get('confidence', 0.0)
        )
        if 'parsed_at' in data:
            actant.parsed_at = datetime.fromisoformat(data['parsed_at'])
        return actant


class LTMBlock:
    """LTM 블록 (불변 구조)"""
    
    def __init__(self, memory_item: MemoryItem, prev_hash: str = ""):
        self.memory_item = memory_item
        self.block_index = None  # DB에서 설정됨
        self.prev_hash = prev_hash
        self.hash = ""
        self.actant_structure: Optional[ActantStructure] = None
        
        # 메타데이터에서 액탄트 정보 추출
        if 'actant' in memory_item.metadata:
            self.actant_structure = ActantStructure.from_dict(memory_item.metadata['actant'])
        
        # 해시 계산
        self._compute_hash()
    
    def _compute_hash(self):
        """블록 해시 계산"""
        block_data = {
            'content': self.memory_item.content,
            'timestamp': self.memory_item.timestamp.isoformat(),
            'keywords': sorted(self.memory_item.keywords),
            'tags': sorted(self.memory_item.tags),
            'importance': self.memory_item.importance,
            'prev_hash': self.prev_hash
        }
        
        if self.actant_structure:
            block_data['actant'] = self.actant_structure.to_dict()
        
        block_str = json.dumps(block_data, sort_keys=True, ensure_ascii=False)
        self.hash = hashlib.sha256(block_str.encode('utf-8')).hexdigest()[:16]
    
    def to_db_dict(self) -> Dict[str, Any]:
        """데이터베이스 저장용 딕셔너리"""
        db_data = {
            'block_index': self.block_index,
            'timestamp': self.memory_item.timestamp.isoformat(),
            'context': self.memory_item.content,
            'importance': self.memory_item.importance,
            'hash': self.hash,
            'prev_hash': self.prev_hash
        }
        
        # 액탄트 필드
        if self.actant_structure:
            db_data.update({
                'actant_subject': self.actant_structure.subject,
                'actant_action': self.actant_structure.action,
                'actant_object': self.actant_structure.object_target,
                'actant_parsed_at': self.actant_structure.parsed_at.isoformat(),
                'migration_confidence': self.actant_structure.confidence
            })
        
        return db_data


class RelationshipTracker:
    """관계 추적 시스템"""
    
    def __init__(self):
        self.subject_collaborations: Dict[str, Set[int]] = defaultdict(set)
        self.action_causalities: Dict[str, Set[int]] = defaultdict(set)
        self.object_dependencies: Dict[str, Set[int]] = defaultdict(set)
    
    def add_block_relationships(self, block: LTMBlock):
        """블록의 관계 정보 추가"""
        if not block.actant_structure or not block.block_index:
            return
        
        actant = block.actant_structure
        
        if actant.subject:
            self.subject_collaborations[actant.subject].add(block.block_index)
        
        if actant.action:
            self.action_causalities[actant.action].add(block.block_index)
        
        if actant.object_target:
            self.object_dependencies[actant.object_target].add(block.block_index)
    
    def find_related_blocks(self, actant: ActantStructure, 
                          relationship_types: List[str] = None) -> Set[int]:
        """관련 블록 찾기"""
        if relationship_types is None:
            relationship_types = ['subject', 'action', 'object']
        
        related_blocks = set()
        
        if 'subject' in relationship_types and actant.subject:
            related_blocks.update(self.subject_collaborations.get(actant.subject, set()))
        
        if 'action' in relationship_types and actant.action:
            related_blocks.update(self.action_causalities.get(actant.action, set()))
        
        if 'object' in relationship_types and actant.object_target:
            related_blocks.update(self.object_dependencies.get(actant.object_target, set()))
        
        return related_blocks


class LTMLayer(MemoryLayerInterface):
    """장기 기억 계층 구현"""
    
    def __init__(self, db_manager: DatabaseManager = None):
        super().__init__(MemoryLayerType.LTM)
        
        self.db_manager = db_manager or DatabaseManager()
        
        # 블록체인 상태
        self.blocks: Dict[int, LTMBlock] = {}
        self.block_by_memory_id: Dict[str, int] = {}
        self.last_block_index = -1
        self.last_hash = ""
        
        # 관계 추적
        self.relationship_tracker = RelationshipTracker()
        
        # 검색 인덱스
        self.content_index: Dict[str, Set[int]] = defaultdict(set)  # 단어 -> 블록 인덱스
        self.keyword_index: Dict[str, Set[int]] = defaultdict(set)
        self.tag_index: Dict[str, Set[int]] = defaultdict(set)
        self.actant_index: Dict[str, Dict[str, Set[int]]] = {
            'subject': defaultdict(set),
            'action': defaultdict(set),
            'object': defaultdict(set)
        }
        
        # 통계
        self.stats = {
            "total_blocks": 0,
            "blocks_with_actant": 0,
            "total_relationships": 0,
            "chain_integrity_checks": 0,
            "search_queries": 0
        }
    
    def initialize(self) -> bool:
        """LTM 계층 초기화"""
        try:
            self._load_existing_blocks()
            self._build_indices()
            self._verify_chain_integrity()
            self._initialized = True
            return True
        except Exception as e:
            print(f"LTM Layer initialization failed: {e}")
            return False
    
    def _load_existing_blocks(self):
        """데이터베이스에서 기존 블록 로드"""
        try:
            # v2.5.3 스키마의 blocks 테이블에서 로드
            cursor = self.db_manager.conn.cursor()
            # 기존 스키마에 맞게 쿼리 (액탄트 컬럼은 선택적)
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='blocks'")
            if cursor.fetchone():
                # 컬럼 정보 확인
                cursor.execute("PRAGMA table_info(blocks)")
                columns = [col[1] for col in cursor.fetchall()]
                
                if 'actant_subject' in columns:
                    # v2.5.3 스키마
                    cursor.execute("""
                        SELECT block_index, timestamp, context, importance, hash, prev_hash,
                               actant_subject, actant_action, actant_object, 
                               actant_parsed_at, migration_confidence
                        FROM blocks 
                        ORDER BY block_index
                    """)
                else:
                    # 기존 스키마 (액탄트 없음)
                    cursor.execute("""
                        SELECT block_index, timestamp, context, importance, hash, prev_hash
                        FROM blocks 
                        ORDER BY block_index
                    """)
            else:
                return  # blocks 테이블 없음
            
            for row in cursor.fetchall():
                memory_item = self._create_memory_item_from_db(row)
                block = LTMBlock(memory_item, row[5])  # prev_hash
                block.block_index = row[0]
                block.hash = row[4]
                
                # 액탄트 구조 복원 (컬럼이 있는 경우에만)
                if len(row) > 6:  # 액탄트 컬럼들이 있음
                    if row[6] or row[7] or row[8]:  # actant_subject, action, object
                        block.actant_structure = ActantStructure(
                            subject=row[6],
                            action=row[7],
                            object_target=row[8],
                            confidence=row[10] if len(row) > 10 else 0.0
                        )
                        if len(row) > 9 and row[9]:  # actant_parsed_at
                            block.actant_structure.parsed_at = datetime.fromisoformat(row[9])
                
                self.blocks[block.block_index] = block
                self.block_by_memory_id[memory_item.id] = block.block_index
                
                if block.block_index > self.last_block_index:
                    self.last_block_index = block.block_index
                    self.last_hash = block.hash
            
        except Exception as e:
            print(f"Failed to load existing LTM blocks: {e}")
    
    def _create_memory_item_from_db(self, row) -> MemoryItem:
        """데이터베이스 행에서 MemoryItem 생성"""
        return MemoryItem(
            id=f"ltm_block_{row[0]}",  # block_index 기반 ID
            content=row[2],  # context
            timestamp=datetime.fromisoformat(row[1]),
            layer=MemoryLayerType.LTM,
            priority=MemoryPriority.HIGH,  # LTM은 기본적으로 높은 우선순위
            metadata={},
            keywords=[],  # 별도 테이블에서 로드 필요
            tags=[],      # 별도 테이블에서 로드 필요
            embedding=[], # 별도 테이블에서 로드 필요
            importance=row[3]
        )
    
    def _build_indices(self):
        """검색 인덱스 구축"""
        for block_index, block in self.blocks.items():
            self._add_to_indices(block)
            self.relationship_tracker.add_block_relationships(block)
        
        self.stats["total_blocks"] = len(self.blocks)
        self.stats["blocks_with_actant"] = sum(
            1 for block in self.blocks.values() 
            if block.actant_structure
        )
    
    def _add_to_indices(self, block: LTMBlock):
        """블록을 인덱스에 추가"""
        block_index = block.block_index
        memory_item = block.memory_item
        
        # 콘텐츠 인덱스 (단어 단위)
        words = memory_item.content.lower().split()
        for word in words:
            word = word.strip('.,!?";:()[]{}')
            if len(word) > 2:  # 짧은 단어 제외
                self.content_index[word].add(block_index)
        
        # 키워드 인덱스
        for keyword in memory_item.keywords:
            self.keyword_index[keyword.lower()].add(block_index)
        
        # 태그 인덱스
        for tag in memory_item.tags:
            self.tag_index[tag.lower()].add(block_index)
        
        # 액탄트 인덱스
        if block.actant_structure:
            actant = block.actant_structure
            if actant.subject:
                self.actant_index['subject'][actant.subject.lower()].add(block_index)
            if actant.action:
                self.actant_index['action'][actant.action.lower()].add(block_index)
            if actant.object_target:
                self.actant_index['object'][actant.object_target.lower()].add(block_index)
    
    def _verify_chain_integrity(self) -> bool:
        """블록체인 무결성 검증"""
        try:
            if not self.blocks:
                return True
            
            sorted_blocks = sorted(self.blocks.items())
            prev_hash = ""
            
            for block_index, block in sorted_blocks:
                if block.prev_hash != prev_hash:
                    print(f"Chain integrity broken at block {block_index}")
                    return False
                prev_hash = block.hash
            
            self.stats["chain_integrity_checks"] += 1
            return True
            
        except Exception as e:
            print(f"Chain integrity verification failed: {e}")
            return False
    
    def add_memory(self, memory_item: MemoryItem) -> str:
        """LTM에 메모리 블록 추가"""
        try:
            # 새 블록 생성
            new_block = LTMBlock(memory_item, self.last_hash)
            new_block.block_index = self.last_block_index + 1
            
            # 액탄트 구조 파싱 (필요시)
            if not new_block.actant_structure:
                new_block.actant_structure = self._parse_actant_structure(memory_item.content)
                if new_block.actant_structure:
                    memory_item.metadata['actant'] = new_block.actant_structure.to_dict()
            
            # 데이터베이스에 저장
            db_data = new_block.to_db_dict()
            self._save_block_to_db(db_data)
            
            # 메타데이터 저장 (키워드, 태그 등)
            self._save_block_metadata(new_block)
            
            # 메모리 구조 업데이트
            self.blocks[new_block.block_index] = new_block
            self.block_by_memory_id[memory_item.id] = new_block.block_index
            self.last_block_index = new_block.block_index
            self.last_hash = new_block.hash
            
            # 인덱스 업데이트
            self._add_to_indices(new_block)
            self.relationship_tracker.add_block_relationships(new_block)
            
            # 통계 업데이트
            self.stats["total_blocks"] += 1
            if new_block.actant_structure:
                self.stats["blocks_with_actant"] += 1
            
            return memory_item.id
            
        except Exception as e:
            print(f"Failed to add LTM memory: {e}")
            return ""
    
    def _parse_actant_structure(self, content: str) -> Optional[ActantStructure]:
        """콘텐츠에서 액탄트 구조 파싱 (간단한 규칙 기반)"""
        # 실제로는 v2.5.3의 AI parser를 사용해야 하지만,
        # 여기서는 간단한 패턴 매칭으로 구현
        import re
        
        # 한국어 패턴 매칭
        patterns = [
            (r'(\w+)(?:가|이)\s*(\w+)(?:를|을|한|함)', r'\1', r'\2', 'object_from_content'),
            (r'(\w+)\s*(\w+)(?:했|함|한)', r'user', r'\2', r'\1'),
        ]
        
        for pattern, subject_pattern, action_pattern, object_pattern in patterns:
            match = re.search(pattern, content)
            if match:
                try:
                    subject = match.group(1) if subject_pattern.startswith(r'\1') else subject_pattern
                    action = match.group(1 if action_pattern.startswith(r'\1') else 2)
                    obj = match.group(2 if object_pattern.startswith(r'\2') else 1)
                    
                    return ActantStructure(
                        subject=subject,
                        action=action,
                        object_target=obj,
                        confidence=0.6  # 규칙 기반은 중간 신뢰도
                    )
                except:
                    continue
        
        return None
    
    def _save_block_to_db(self, db_data: Dict[str, Any]):
        """블록을 데이터베이스에 저장"""
        cursor = self.db_manager.conn.cursor()
        
        # 스키마에 따라 적절한 INSERT 사용
        cursor.execute("PRAGMA table_info(blocks)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'actant_subject' in columns:
            # v2.5.3 스키마
            cursor.execute("""
                INSERT INTO blocks (
                    block_index, timestamp, context, importance, hash, prev_hash,
                    actant_subject, actant_action, actant_object, 
                    actant_parsed_at, migration_confidence
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                db_data['block_index'],
                db_data['timestamp'],
                db_data['context'],
                db_data['importance'],
                db_data['hash'],
                db_data['prev_hash'],
                db_data.get('actant_subject'),
                db_data.get('actant_action'),
                db_data.get('actant_object'),
                db_data.get('actant_parsed_at'),
                db_data.get('migration_confidence')
            ))
        else:
            # 기존 스키마 (액탄트 없음) - DatabaseManager의 add_block 사용
            block_data = {
                'block_index': db_data['block_index'],
                'timestamp': db_data['timestamp'],
                'context': db_data['context'],
                'importance': db_data['importance'],
                'hash': db_data['hash'],
                'prev_hash': db_data['prev_hash'],
                'keywords': [],  # 나중에 별도 저장
                'tags': [],      # 나중에 별도 저장
                'metadata': {},  # 나중에 별도 저장
                'embedding': []  # 나중에 별도 저장
            }
            self.db_manager.add_block(block_data)
            return  # add_block에서 이미 commit함
        
        self.db_manager.conn.commit()
    
    def _save_block_metadata(self, block: LTMBlock):
        """블록 메타데이터 저장 (키워드, 태그)"""
        cursor = self.db_manager.conn.cursor()
        block_index = block.block_index
        memory_item = block.memory_item
        
        # 키워드 저장
        for keyword in memory_item.keywords:
            cursor.execute("""
                INSERT INTO block_keywords (block_index, keyword) 
                VALUES (?, ?)
            """, (block_index, keyword))
        
        # 태그 저장
        for tag in memory_item.tags:
            cursor.execute("""
                INSERT INTO block_tags (block_index, tag) 
                VALUES (?, ?)
            """, (block_index, tag))
        
        # 메타데이터 저장 (통합 JSON 형태로)
        metadata_to_save = memory_item.metadata.copy()
        metadata_to_save.update({
            'keywords': memory_item.keywords,
            'tags': memory_item.tags,
            'importance': memory_item.importance,
            'layer': memory_item.layer.value,
            'priority': memory_item.priority.value
        })
        
        cursor.execute("""
            INSERT OR REPLACE INTO block_metadata 
            (block_index, metadata) 
            VALUES (?, ?)
        """, (
            block_index,
            json.dumps(metadata_to_save, ensure_ascii=False)
        ))
        
        self.db_manager.conn.commit()
    
    def get_memory(self, memory_id: str) -> Optional[MemoryItem]:
        """특정 메모리 조회"""
        block_index = self.block_by_memory_id.get(memory_id)
        if block_index is None:
            return None
        
        block = self.blocks.get(block_index)
        return block.memory_item if block else None
    
    def search_memories(self, query: str, limit: int = 10, 
                       filters: Dict[str, Any] = None) -> List[MemoryItem]:
        """LTM 메모리 검색"""
        if filters is None:
            filters = {}
        
        self.stats["search_queries"] += 1
        candidate_blocks = set()
        
        # 액탄트 검색
        if 'actant_subject' in filters:
            subject_blocks = self.actant_index['subject'].get(filters['actant_subject'].lower(), set())
            candidate_blocks.update(subject_blocks)
        
        if 'actant_action' in filters:
            action_blocks = self.actant_index['action'].get(filters['actant_action'].lower(), set())
            candidate_blocks.update(action_blocks)
        
        if 'actant_object' in filters:
            object_blocks = self.actant_index['object'].get(filters['actant_object'].lower(), set())
            candidate_blocks.update(object_blocks)
        
        # 키워드 검색
        if 'keywords' in filters:
            for keyword in filters['keywords']:
                keyword_blocks = self.keyword_index.get(keyword.lower(), set())
                candidate_blocks.update(keyword_blocks)
        
        # 태그 검색
        if 'tags' in filters:
            for tag in filters['tags']:
                tag_blocks = self.tag_index.get(tag.lower(), set())
                candidate_blocks.update(tag_blocks)
        
        # 텍스트 검색 (단어 단위)
        if not candidate_blocks:
            query_words = query.lower().split()
            for word in query_words:
                word = word.strip('.,!?";:()[]{}')
                if len(word) > 2:
                    word_blocks = self.content_index.get(word, set())
                    candidate_blocks.update(word_blocks)
        
        # 결과 수집 및 정렬
        results = []
        for block_index in candidate_blocks:
            block = self.blocks.get(block_index)
            if block:
                results.append(block.memory_item)
        
        # 중요도와 시간순으로 정렬
        results.sort(key=lambda x: (x.importance, x.timestamp), reverse=True)
        
        return results[:limit]
    
    def update_memory(self, memory_id: str, updates: Dict[str, Any]) -> bool:
        """LTM 메모리 업데이트 (제한적 - 불변성 유지)"""
        # LTM은 불변 구조이므로 메타데이터만 업데이트 가능
        block_index = self.block_by_memory_id.get(memory_id)
        if block_index is None:
            return False
        
        block = self.blocks.get(block_index)
        if not block:
            return False
        
        try:
            # 메타데이터만 업데이트 (콘텐츠 불변)
            if 'metadata' in updates:
                block.memory_item.metadata.update(updates['metadata'])
                self._save_block_metadata(block)
            
            # 키워드/태그 업데이트 (인덱스 재구축 필요)
            if 'keywords' in updates or 'tags' in updates:
                # 기존 인덱스에서 제거
                self._remove_from_indices(block)
                
                # 업데이트
                if 'keywords' in updates:
                    block.memory_item.keywords = updates['keywords']
                if 'tags' in updates:
                    block.memory_item.tags = updates['tags']
                
                # 새 인덱스에 추가
                self._add_to_indices(block)
                self._save_block_metadata(block)
            
            return True
            
        except Exception as e:
            print(f"Failed to update LTM memory: {e}")
            return False
    
    def _remove_from_indices(self, block: LTMBlock):
        """블록을 인덱스에서 제거"""
        block_index = block.block_index
        memory_item = block.memory_item
        
        # 키워드 인덱스
        for keyword in memory_item.keywords:
            self.keyword_index[keyword.lower()].discard(block_index)
        
        # 태그 인덱스
        for tag in memory_item.tags:
            self.tag_index[tag.lower()].discard(block_index)
    
    def delete_memory(self, memory_id: str) -> bool:
        """LTM 메모리 삭제 (불변성으로 인해 제한적)"""
        # LTM은 불변 구조이므로 실제 삭제는 불가
        # 대신 "삭제됨" 마크만 추가
        block_index = self.block_by_memory_id.get(memory_id)
        if block_index is None:
            return False
        
        block = self.blocks.get(block_index)
        if not block:
            return False
        
        try:
            # 메타데이터에 삭제 마크 추가
            block.memory_item.metadata['deleted'] = True
            block.memory_item.metadata['deleted_at'] = datetime.now().isoformat()
            
            # 인덱스에서는 제거
            self._remove_from_indices(block)
            
            # 데이터베이스 업데이트
            self._save_block_metadata(block)
            
            return True
            
        except Exception as e:
            print(f"Failed to mark LTM memory as deleted: {e}")
            return False
    
    def cleanup_expired(self) -> int:
        """LTM은 만료 개념 없음"""
        return 0
    
    def get_layer_stats(self) -> Dict[str, Any]:
        """LTM 계층 통계"""
        return {
            "layer_type": "LTM",
            "total_blocks": len(self.blocks),
            "last_block_index": self.last_block_index,
            "chain_hash": self.last_hash,
            "blocks_with_actant": len([b for b in self.blocks.values() if b.actant_structure]),
            "total_relationships": (
                len(self.relationship_tracker.subject_collaborations) +
                len(self.relationship_tracker.action_causalities) +
                len(self.relationship_tracker.object_dependencies)
            ),
            "index_sizes": {
                "content_words": len(self.content_index),
                "keywords": len(self.keyword_index),
                "tags": len(self.tag_index),
                "actant_subjects": len(self.actant_index['subject']),
                "actant_actions": len(self.actant_index['action']),
                "actant_objects": len(self.actant_index['object'])
            },
            "stats": self.stats.copy()
        }
    
    def can_accept_transfer(self, transfer_request: LayerTransferRequest) -> bool:
        """전송 요청 수락 가능 여부"""
        # LTM은 STM에서의 승격만 수락
        return transfer_request.source_layer == MemoryLayerType.STM
    
    def transfer_to_layer(self, transfer_request: LayerTransferRequest) -> bool:
        """LTM에서는 다른 계층으로 전송하지 않음"""
        return False
    
    def get_related_memories(self, memory_id: str, 
                           relationship_types: List[str] = None) -> List[MemoryItem]:
        """관련된 메모리들 조회"""
        block_index = self.block_by_memory_id.get(memory_id)
        if block_index is None:
            return []
        
        block = self.blocks.get(block_index)
        if not block or not block.actant_structure:
            return []
        
        related_block_indices = self.relationship_tracker.find_related_blocks(
            block.actant_structure, relationship_types
        )
        
        # 자기 자신 제외
        related_block_indices.discard(block_index)
        
        results = []
        for related_index in related_block_indices:
            related_block = self.blocks.get(related_index)
            if related_block:
                results.append(related_block.memory_item)
        
        # 중요도순 정렬
        results.sort(key=lambda x: x.importance, reverse=True)
        
        return results