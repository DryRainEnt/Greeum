"""
Raw Data Backup Layer for Greeum v2.6.3
STM Architecture Reimagining - STM을 Raw Data Backup으로 확장

Claude Code auto-compact 대응 컨텍스트 보존 시스템
"""

import os
import time
import json
import uuid
import sqlite3
from typing import List, Dict, Any, Optional, Set
from datetime import datetime, timedelta
from collections import defaultdict, deque
from concurrent.futures import ThreadPoolExecutor

from .stm_layer import STMLayer
from .context_backup import (
    ContextBackupItem, ContextType, ProcessingStatus, 
    BackupStrategy, RetentionPriority, create_context_backup
)
from .auto_compact_monitor import AutoCompactMonitor, CompactEvent
from .claude_code_detector import get_claude_code_detector
from .database_manager import DatabaseManager


class ProcessingQueue:
    """백업 항목 처리 대기열"""
    
    def __init__(self):
        self.priority_queue: deque = deque()  # 우선순위 항목
        self.normal_queue: deque = deque()   # 일반 항목
        
    def add_priority_item(self, backup_id: str):
        """우선순위 항목 추가"""
        self.priority_queue.append(backup_id)
    
    def add_normal_item(self, backup_id: str):
        """일반 항목 추가"""
        self.normal_queue.append(backup_id)
    
    def get_next(self) -> Optional[str]:
        """다음 처리할 항목 반환"""
        if self.priority_queue:
            return self.priority_queue.popleft()
        elif self.normal_queue:
            return self.normal_queue.popleft()
        return None
    
    def is_empty(self) -> bool:
        """대기열이 비어있는지 확인"""
        return len(self.priority_queue) == 0 and len(self.normal_queue) == 0
    
    def size(self) -> Dict[str, int]:
        """대기열 크기"""
        return {
            'priority': len(self.priority_queue),
            'normal': len(self.normal_queue),
            'total': len(self.priority_queue) + len(self.normal_queue)
        }


class ContextRecoveryManager:
    """Context 복구 관리자"""
    
    def __init__(self, backup_layer: 'RawDataBackupLayer'):
        self.backup_layer = backup_layer
    
    def recover_lost_context(self, session_id: str) -> Dict[str, Any]:
        """손실된 컨텍스트 복구"""
        recovery_results = {
            "recovered_items": 0,
            "reconstructed_conversations": 0,
            "ltm_transfers": 0,
            "failed_items": 0
        }
        
        try:
            # 1. LOST 상태 백업들 식별
            lost_backups = self._find_lost_backups(session_id)
            
            if not lost_backups:
                return recovery_results
            
            # 2. 복구 우선순위 결정
            priority_queue = self._prioritize_recovery(lost_backups)
            
            # 3. Context 재구성 및 복구
            for backup_item in priority_queue:
                try:
                    # Context 재구성
                    reconstructed = self._reconstruct_context(backup_item)
                    
                    if reconstructed:
                        # 상태 업데이트
                        backup_item.processing_status = ProcessingStatus.RECOVERED
                        self.backup_layer._update_backup_in_db(backup_item)
                        
                        # 즉시 LTM 전송이 필요한 경우
                        if self._should_immediate_transfer(backup_item):
                            success = self.backup_layer._transfer_to_ltm(backup_item)
                            if success:
                                recovery_results["ltm_transfers"] += 1
                        
                        recovery_results["recovered_items"] += 1
                        
                        # 대화 재구성 카운트 (conversation_turn 기준)
                        if backup_item.context_type == ContextType.CONVERSATION_TURN:
                            recovery_results["reconstructed_conversations"] += 1
                    else:
                        recovery_results["failed_items"] += 1
                        
                except Exception as e:
                    print(f"개별 아이템 복구 실패 {backup_item.id}: {e}")
                    recovery_results["failed_items"] += 1
            
            return recovery_results
            
        except Exception as e:
            print(f"Context 복구 중 오류: {e}")
            recovery_results["failed_items"] = len(lost_backups) if 'lost_backups' in locals() else 0
            return recovery_results
    
    def _find_lost_backups(self, session_id: str) -> List[ContextBackupItem]:
        """LOST 상태의 백업들 찾기"""
        lost_backups = []
        
        for backup_id, backup_item in self.backup_layer.backup_cache.items():
            if (backup_item.session_id == session_id and 
                backup_item.processing_status == ProcessingStatus.LOST):
                lost_backups.append(backup_item)
        
        return lost_backups
    
    def _prioritize_recovery(self, lost_backups: List[ContextBackupItem]) -> List[ContextBackupItem]:
        """복구 우선순위 결정"""
        # 우선순위 기준: 1) retention_priority, 2) auto_compact_risk_score, 3) timestamp
        return sorted(lost_backups, key=lambda x: (
            -x.retention_priority.value if hasattr(x.retention_priority, 'value') else 0,
            -x.auto_compact_risk_score,
            x.timestamp
        ))
    
    def _reconstruct_context(self, backup_item: ContextBackupItem) -> bool:
        """개별 컨텍스트 재구성"""
        try:
            # 이미 semantic 정보가 있다면 재사용
            if (backup_item.extracted_intents and 
                backup_item.semantic_chunks and
                backup_item.processing_status != ProcessingStatus.FAILED):
                return True
            
            # 새로 추출 시도
            return backup_item.extract_semantic_info()
            
        except Exception as e:
            print(f"Context 재구성 실패 {backup_item.id}: {e}")
            return False
    
    def _should_immediate_transfer(self, backup_item: ContextBackupItem) -> bool:
        """즉시 LTM 전송해야 하는지 판단"""
        return (
            backup_item.retention_priority in [RetentionPriority.CRITICAL, RetentionPriority.HIGH] or
            backup_item.auto_compact_risk_score > 0.8 or
            backup_item.is_ready_for_ltm()
        )


class RawDataBackupLayer(STMLayer):
    """STM을 Raw Data Backup으로 확장한 계층"""
    
    def __init__(self, 
                 db_manager: DatabaseManager = None,
                 max_backup_size: int = 10000,
                 critical_retention_days: int = 30,
                 auto_compact_threshold: float = 0.8,
                 batch_processing_interval: int = 300):  # 5분
        
        # 기본 STM 초기화
        super().__init__(db_manager, default_ttl=86400)  # 24시간 기본 TTL
        
        # Raw Data Backup 전용 설정
        self.max_backup_size = max_backup_size
        self.critical_retention_days = critical_retention_days
        self.batch_processing_interval = batch_processing_interval
        
        # 백업 캐시 (ContextBackupItem 저장)
        self.backup_cache: Dict[str, ContextBackupItem] = {}
        
        # 세션별 시퀀스 번호 관리
        self.session_sequence: Dict[str, int] = defaultdict(int)
        
        # Auto-compact 모니터링
        self.auto_compact_monitor = AutoCompactMonitor(threshold=auto_compact_threshold)
        
        # Processing Pipeline
        self.processing_queue = ProcessingQueue()
        self.recovery_manager = ContextRecoveryManager(self)
        
        # Claude Code 감지기
        self.claude_detector = get_claude_code_detector()
        
        # 통계
        self.backup_stats = {
            "total_backups_created": 0,
            "auto_compact_events_detected": 0,
            "recovery_operations": 0,
            "ltm_transfers": 0,
            "processing_errors": 0
        }
        
        # 백그라운드 처리용 스레드 풀
        self.thread_pool = ThreadPoolExecutor(max_workers=2)
        
        print(f"🚀 RawDataBackupLayer 초기화 완료")
        print(f"   Claude Code 환경: {'✅' if self.claude_detector.is_claude_code_host else '❌'}")
        print(f"   최대 백업 크기: {max_backup_size:,}")
    
    def initialize(self) -> bool:
        """확장 초기화"""
        if not super().initialize():
            return False
        
        try:
            # Context Backup 테이블 생성
            self._create_backup_tables()
            
            # 기존 백업 데이터 로드
            self._load_existing_backups()
            
            # Auto-compact 모니터링 데이터 로드
            monitor_file = self._get_monitor_data_path()
            self.auto_compact_monitor.load_monitoring_data(monitor_file)
            
            return True
            
        except Exception as e:
            print(f"RawDataBackupLayer 초기화 실패: {e}")
            return False
    
    def _create_backup_tables(self):
        """백업 전용 테이블 생성"""
        cursor = self.db_manager.conn.cursor()
        
        # Context Backup 테이블
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS context_backups (
                id TEXT PRIMARY KEY,
                session_id TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                raw_content TEXT NOT NULL,
                context_type TEXT NOT NULL,
                sequence_number INTEGER NOT NULL,
                parent_context_id TEXT,
                conversation_turn INTEGER,
                original_length INTEGER,
                auto_compact_risk_score REAL,
                processing_status TEXT DEFAULT 'raw',
                backup_strategy TEXT DEFAULT 'immediate',
                retention_priority TEXT DEFAULT 'normal',
                extracted_intents TEXT, -- JSON array
                key_entities TEXT,      -- JSON array
                semantic_chunks TEXT,   -- JSON array
                recovery_metadata TEXT, -- JSON object
                claudecode_context_id TEXT,
                tool_usage_context TEXT, -- JSON array
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                processed_at TEXT,
                expires_at TEXT
            )
        """)
        
        # 인덱스 생성
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_session_sequence ON context_backups(session_id, sequence_number)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_processing_status ON context_backups(processing_status)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_retention_priority ON context_backups(retention_priority)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_compact_risk ON context_backups(auto_compact_risk_score)")
        
        # Auto-compact 이벤트 로그 테이블
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS auto_compact_events (
                id TEXT PRIMARY KEY,
                session_id TEXT,
                detected_at TEXT,
                detected_method TEXT,
                context_length_before INTEGER,
                context_length_after INTEGER,
                affected_backup_count INTEGER,
                recovery_initiated BOOLEAN DEFAULT FALSE,
                event_data TEXT -- JSON
            )
        """)
        
        self.db_manager.conn.commit()
    
    def _load_existing_backups(self):
        """기존 백업 데이터 로드"""
        try:
            cursor = self.db_manager.conn.cursor()
            cursor.execute("SELECT * FROM context_backups WHERE processing_status != 'processed'")
            
            for row in cursor.fetchall():
                backup_item = self._backup_from_db_row(dict(row))
                if backup_item and not backup_item.is_expired():
                    self.backup_cache[backup_item.id] = backup_item
            
            print(f"📦 기존 백업 {len(self.backup_cache)}개 로드 완료")
            
        except Exception as e:
            print(f"기존 백업 로드 실패: {e}")
    
    def backup_context_immediately(self, 
                                  content: str,
                                  context_type: ContextType,
                                  session_id: str = None,
                                  retention_priority: RetentionPriority = None) -> str:
        """실시간 컨텍스트 백업"""
        start_time = time.time()
        
        try:
            # 세션 ID 설정
            session_id = session_id or self.claude_detector.claude_session_id or self.current_session_id
            
            # 시퀀스 번호 할당
            sequence = self.session_sequence[session_id]
            self.session_sequence[session_id] += 1
            
            # Auto-compact 위험도 계산
            risk_score = self.auto_compact_monitor.calculate_risk(
                content_length=len(content),
                session_history=self.get_session_backup_count(session_id),
                tool_usage_count=self._count_tool_usage_in_session(session_id),
                conversation_turns=self._count_conversation_turns(session_id)
            )
            
            # 보존 우선순위 결정
            if retention_priority is None:
                retention_priority = self._calculate_retention_priority(content, risk_score)
            
            # 백업 아이템 생성
            backup_item = ContextBackupItem(
                session_id=session_id,
                raw_content=content,
                context_type=context_type,
                sequence_number=sequence,
                auto_compact_risk_score=risk_score,
                processing_status=ProcessingStatus.RAW,
                backup_strategy=BackupStrategy.IMMEDIATE,
                retention_priority=retention_priority
            )
            
            # 즉시 캐시 및 DB 저장
            self.backup_cache[backup_item.id] = backup_item
            self._store_backup_to_db(backup_item)
            
            # 고위험 항목 우선 처리 대기열 추가
            if risk_score > 0.7 or retention_priority == RetentionPriority.CRITICAL:
                self.processing_queue.add_priority_item(backup_item.id)
            else:
                self.processing_queue.add_normal_item(backup_item.id)
            
            # 통계 업데이트
            self.backup_stats["total_backups_created"] += 1
            
            # Auto-compact 모니터링에 메트릭 기록
            self.auto_compact_monitor.record_context_metrics(
                content_length=len(content),
                session_history_count=self.get_session_backup_count(session_id),
                tool_usage_count=self._count_tool_usage_in_session(session_id),
                conversation_turns=self._count_conversation_turns(session_id)
            )
            
            # 처리 시간 체크 (성능 목표: <1ms)
            processing_time = time.time() - start_time
            if processing_time > 0.001:  # 1ms 초과 시 경고
                print(f"⚠️ 백업 처리 시간 {processing_time*1000:.1f}ms (목표: <1ms)")
            
            return backup_item.id
            
        except Exception as e:
            print(f"즉시 백업 실패: {e}")
            self.backup_stats["processing_errors"] += 1
            return ""
    
    def process_backup_queue(self) -> Dict[str, Any]:
        """백업 항목 배치 처리"""
        start_time = time.time()
        
        results = {
            "processed_count": 0,
            "ltm_transferred": 0,
            "failed_count": 0,
            "processing_time": 0.0
        }
        
        processed_count = 0
        max_batch_size = 100  # 배치당 최대 처리 개수
        
        try:
            while not self.processing_queue.is_empty() and processed_count < max_batch_size:
                backup_id = self.processing_queue.get_next()
                backup_item = self.backup_cache.get(backup_id)
                
                if not backup_item:
                    continue
                
                try:
                    # 만료된 항목 건너뛰기
                    if backup_item.is_expired():
                        self._cleanup_expired_backup(backup_id)
                        continue
                    
                    # 1. 정보 추출
                    backup_item.processing_status = ProcessingStatus.EXTRACTING
                    extraction_success = backup_item.extract_semantic_info()
                    
                    if extraction_success:
                        # 2. LTM 전송 준비
                        backup_item.processing_status = ProcessingStatus.READY_FOR_LTM
                        
                        # 3. LTM 전송 시도
                        if self._should_transfer_to_ltm(backup_item):
                            success = self._transfer_to_ltm(backup_item)
                            if success:
                                backup_item.processing_status = ProcessingStatus.PROCESSED
                                results["ltm_transferred"] += 1
                            else:
                                results["failed_count"] += 1
                        
                        # DB 업데이트
                        self._update_backup_in_db(backup_item)
                        results["processed_count"] += 1
                    else:
                        results["failed_count"] += 1
                    
                    processed_count += 1
                    
                except Exception as e:
                    print(f"백업 처리 실패 {backup_id}: {e}")
                    results["failed_count"] += 1
            
            results["processing_time"] = time.time() - start_time
            
            # 성능 검증 (목표: >100 items/sec)
            if results["processing_time"] > 0:
                throughput = results["processed_count"] / results["processing_time"]
                if throughput < 100:
                    print(f"⚠️ 배치 처리 성능 {throughput:.1f} items/sec (목표: >100)")
            
            return results
            
        except Exception as e:
            print(f"배치 처리 중 오류: {e}")
            results["processing_time"] = time.time() - start_time
            self.backup_stats["processing_errors"] += 1
            return results
    
    def detect_and_handle_auto_compact(self) -> Optional[CompactEvent]:
        """Auto-compact 감지 및 처리"""
        compact_event = self.auto_compact_monitor.detect_auto_compact_event()
        
        if compact_event:
            print(f"🚨 Auto-compact 감지됨: {compact_event.event_id}")
            
            # 영향받은 백업 항목들 LOST 상태로 변경
            affected_count = self._mark_affected_backups_as_lost(compact_event)
            compact_event.affected_items = affected_count
            
            # 이벤트 DB 저장
            self._store_compact_event(compact_event)
            
            # 통계 업데이트
            self.backup_stats["auto_compact_events_detected"] += 1
            
            # 자동 복구 시작 (백그라운드)
            if affected_count > 0:
                self.thread_pool.submit(self._auto_recovery_process, compact_event)
            
            return compact_event
        
        return None
    
    def _mark_affected_backups_as_lost(self, compact_event: CompactEvent) -> int:
        """영향받은 백업들을 LOST 상태로 변경"""
        affected_count = 0
        
        # 처리 중이던 항목들을 LOST로 변경
        for backup_id, backup_item in self.backup_cache.items():
            if backup_item.processing_status in [ProcessingStatus.RAW, ProcessingStatus.EXTRACTING]:
                backup_item.processing_status = ProcessingStatus.LOST
                backup_item.recovery_metadata['lost_event_id'] = compact_event.event_id
                backup_item.recovery_metadata['lost_timestamp'] = compact_event.timestamp.isoformat()
                self._update_backup_in_db(backup_item)
                affected_count += 1
        
        return affected_count
    
    def _auto_recovery_process(self, compact_event: CompactEvent):
        """자동 복구 프로세스 (백그라운드 실행)"""
        try:
            print(f"🔄 자동 복구 프로세스 시작: {compact_event.event_id}")
            
            # 세션별 복구 실행
            sessions_to_recover = set()
            for backup_item in self.backup_cache.values():
                if backup_item.processing_status == ProcessingStatus.LOST:
                    sessions_to_recover.add(backup_item.session_id)
            
            total_recovered = 0
            for session_id in sessions_to_recover:
                recovery_results = self.recovery_manager.recover_lost_context(session_id)
                total_recovered += recovery_results["recovered_items"]
            
            # 이벤트 업데이트
            compact_event.recovery_initiated = True
            
            print(f"✅ 자동 복구 완료: {total_recovered}개 항목 복구")
            self.backup_stats["recovery_operations"] += 1
            
        except Exception as e:
            print(f"자동 복구 프로세스 실패: {e}")
    
    def get_session_backup_count(self, session_id: str) -> int:
        """세션의 백업 개수"""
        return sum(1 for item in self.backup_cache.values() 
                  if item.session_id == session_id)
    
    def _count_tool_usage_in_session(self, session_id: str) -> int:
        """세션의 도구 사용 횟수"""
        return sum(len(item.tool_usage_context) for item in self.backup_cache.values()
                  if item.session_id == session_id)
    
    def _count_conversation_turns(self, session_id: str) -> int:
        """세션의 대화 턴 수"""
        turns = set()
        for item in self.backup_cache.values():
            if item.session_id == session_id:
                turns.add(item.conversation_turn)
        return len(turns)
    
    def _calculate_retention_priority(self, content: str, risk_score: float) -> RetentionPriority:
        """보존 우선순위 계산"""
        # 위험도 기반
        if risk_score > 0.9:
            return RetentionPriority.CRITICAL
        elif risk_score > 0.7:
            return RetentionPriority.HIGH
        
        # 내용 기반 분석
        content_lower = content.lower()
        
        # 중요한 키워드 포함 시
        critical_keywords = ["오류", "error", "실패", "fail", "중요", "important", "긴급", "urgent"]
        if any(keyword in content_lower for keyword in critical_keywords):
            return RetentionPriority.HIGH
        
        # 코드 관련 내용
        code_keywords = ["def ", "class ", "function", "import", "from", "```"]
        if any(keyword in content_lower for keyword in code_keywords):
            return RetentionPriority.NORMAL
        
        return RetentionPriority.NORMAL
    
    def _should_transfer_to_ltm(self, backup_item: ContextBackupItem) -> bool:
        """LTM 전송 여부 판단"""
        return (
            backup_item.is_ready_for_ltm() and
            (backup_item.retention_priority in [RetentionPriority.CRITICAL, RetentionPriority.HIGH] or
             backup_item.auto_compact_risk_score > 0.6)
        )
    
    def _transfer_to_ltm(self, backup_item: ContextBackupItem) -> bool:
        """LTM으로 전송"""
        try:
            from .memory_layer import create_memory_item, MemoryLayerType
            from .hierarchical_memory import HierarchicalMemorySystem
            
            # MemoryItem으로 변환
            memory_item = create_memory_item(
                content=backup_item.raw_content,
                layer=MemoryLayerType.LTM,
                keywords=backup_item.key_entities,
                tags=backup_item.extracted_intents,
                importance=min(backup_item.auto_compact_risk_score + 0.3, 1.0),
                metadata={
                    'backup_source': 'raw_data_backup',
                    'original_backup_id': backup_item.id,
                    'session_id': backup_item.session_id,
                    'context_type': backup_item.context_type.value,
                    'semantic_chunks': backup_item.semantic_chunks
                }
            )
            
            # HierarchicalMemorySystem을 통해 LTM에 저장
            hierarchical_system = HierarchicalMemorySystem(self.db_manager)
            success = hierarchical_system.ltm_layer.add_memory(memory_item)
            
            if success:
                self.backup_stats["ltm_transfers"] += 1
                return True
            
            return False
            
        except Exception as e:
            print(f"LTM 전송 실패 {backup_item.id}: {e}")
            return False
    
    def _store_backup_to_db(self, backup_item: ContextBackupItem):
        """백업 항목을 DB에 저장"""
        cursor = self.db_manager.conn.cursor()
        
        cursor.execute("""
            INSERT OR REPLACE INTO context_backups 
            (id, session_id, timestamp, raw_content, context_type, sequence_number,
             parent_context_id, conversation_turn, original_length, auto_compact_risk_score,
             processing_status, backup_strategy, retention_priority, extracted_intents,
             key_entities, semantic_chunks, recovery_metadata, claudecode_context_id,
             tool_usage_context, created_at, processed_at, expires_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            backup_item.id,
            backup_item.session_id,
            backup_item.timestamp.isoformat(),
            backup_item.raw_content,
            backup_item.context_type.value,
            backup_item.sequence_number,
            backup_item.parent_context_id,
            backup_item.conversation_turn,
            backup_item.original_length,
            backup_item.auto_compact_risk_score,
            backup_item.processing_status.value,
            backup_item.backup_strategy.value,
            backup_item.retention_priority.value,
            json.dumps(backup_item.extracted_intents),
            json.dumps(backup_item.key_entities),
            json.dumps(backup_item.semantic_chunks),
            json.dumps(backup_item.recovery_metadata),
            backup_item.claudecode_context_id,
            json.dumps(backup_item.tool_usage_context),
            backup_item.created_at.isoformat(),
            backup_item.processed_at.isoformat() if backup_item.processed_at else None,
            backup_item.expires_at.isoformat() if backup_item.expires_at else None
        ))
        
        self.db_manager.conn.commit()
    
    def _update_backup_in_db(self, backup_item: ContextBackupItem):
        """기존 백업 항목 업데이트"""
        self._store_backup_to_db(backup_item)  # INSERT OR REPLACE 사용
    
    def _backup_from_db_row(self, row: Dict[str, Any]) -> Optional[ContextBackupItem]:
        """DB 행에서 ContextBackupItem 생성"""
        try:
            return ContextBackupItem(
                id=row['id'],
                session_id=row['session_id'],
                timestamp=datetime.fromisoformat(row['timestamp']),
                raw_content=row['raw_content'],
                context_type=ContextType(row['context_type']),
                sequence_number=row['sequence_number'],
                parent_context_id=row['parent_context_id'],
                conversation_turn=row['conversation_turn'],
                original_length=row['original_length'],
                auto_compact_risk_score=row['auto_compact_risk_score'],
                processing_status=ProcessingStatus(row['processing_status']),
                backup_strategy=BackupStrategy(row['backup_strategy']),
                retention_priority=RetentionPriority(row['retention_priority']),
                extracted_intents=json.loads(row['extracted_intents'] or '[]'),
                key_entities=json.loads(row['key_entities'] or '[]'),
                semantic_chunks=json.loads(row['semantic_chunks'] or '[]'),
                recovery_metadata=json.loads(row['recovery_metadata'] or '{}'),
                claudecode_context_id=row['claudecode_context_id'],
                tool_usage_context=json.loads(row['tool_usage_context'] or '[]'),
                created_at=datetime.fromisoformat(row['created_at']),
                processed_at=datetime.fromisoformat(row['processed_at']) if row['processed_at'] else None,
                expires_at=datetime.fromisoformat(row['expires_at']) if row['expires_at'] else None
            )
        except Exception as e:
            print(f"DB 행 변환 실패: {e}")
            return None
    
    def _store_compact_event(self, event: CompactEvent):
        """Compact 이벤트 DB 저장"""
        cursor = self.db_manager.conn.cursor()
        
        cursor.execute("""
            INSERT INTO auto_compact_events
            (id, session_id, detected_at, detected_method, context_length_before,
             context_length_after, affected_backup_count, recovery_initiated, event_data)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            event.event_id,
            getattr(event, 'session_id', ''),
            event.timestamp.isoformat(),
            event.detected_method,
            event.context_length_before,
            event.context_length_after,
            event.affected_items,
            event.recovery_initiated,
            json.dumps({'event_id': event.event_id})
        ))
        
        self.db_manager.conn.commit()
    
    def _cleanup_expired_backup(self, backup_id: str):
        """만료된 백업 정리"""
        if backup_id in self.backup_cache:
            del self.backup_cache[backup_id]
        
        cursor = self.db_manager.conn.cursor()
        cursor.execute("DELETE FROM context_backups WHERE id = ?", (backup_id,))
        self.db_manager.conn.commit()
    
    def _get_monitor_data_path(self) -> str:
        """모니터링 데이터 파일 경로"""
        data_dir = os.path.expanduser("~/.greeum")
        os.makedirs(data_dir, exist_ok=True)
        return os.path.join(data_dir, "auto_compact_monitor.json")
    
    def get_backup_statistics(self) -> Dict[str, Any]:
        """백업 시스템 통계"""
        stats = self.backup_stats.copy()
        
        # 현재 상태
        stats.update({
            "cache_size": len(self.backup_cache),
            "queue_size": self.processing_queue.size(),
            "sessions_count": len(self.session_sequence),
            "auto_compact_risk": self.auto_compact_monitor.get_current_risk_status(),
            "monitor_stats": self.auto_compact_monitor.get_statistics()
        })
        
        # 상태별 분포
        status_counts = defaultdict(int)
        priority_counts = defaultdict(int)
        
        for backup_item in self.backup_cache.values():
            status_counts[backup_item.processing_status.value] += 1
            priority_counts[backup_item.retention_priority.value] += 1
        
        stats.update({
            "status_distribution": dict(status_counts),
            "priority_distribution": dict(priority_counts)
        })
        
        return stats
    
    def print_status_report(self):
        """상태 리포트 출력"""
        print("=" * 70)
        print("🔄 Raw Data Backup Layer Status Report")
        print("=" * 70)
        
        stats = self.get_backup_statistics()
        
        print(f"📦 Backup Cache: {stats['cache_size']:,} items")
        print(f"⏳ Processing Queue: {stats['queue_size']['total']} items "
              f"(Priority: {stats['queue_size']['priority']}, Normal: {stats['queue_size']['normal']})")
        print(f"🎯 Sessions: {stats['sessions_count']}")
        
        print(f"\n📊 Lifetime Statistics:")
        print(f"  Created: {stats['total_backups_created']:,}")
        print(f"  LTM Transfers: {stats['ltm_transfers']:,}")
        print(f"  Auto-compact Events: {stats['auto_compact_events_detected']:,}")
        print(f"  Recovery Operations: {stats['recovery_operations']:,}")
        print(f"  Errors: {stats['processing_errors']:,}")
        
        # 위험도 상태
        risk_status = stats['auto_compact_risk']
        print(f"\n🎯 Auto-compact Risk: {risk_status['risk_level'].upper()} ({risk_status['risk_score']:.1%})")
        
        # 상태 분포
        print(f"\n📈 Status Distribution:")
        for status, count in stats['status_distribution'].items():
            print(f"  {status}: {count}")
        
        print("=" * 70)
    
    def __del__(self):
        """소멸자 - 정리 작업"""
        try:
            # 모니터링 데이터 저장
            monitor_file = self._get_monitor_data_path()
            self.auto_compact_monitor.save_monitoring_data(monitor_file)
            
            # 스레드 풀 종료
            if hasattr(self, 'thread_pool'):
                self.thread_pool.shutdown(wait=False)
        except:
            pass


if __name__ == "__main__":
    # 테스트 코드
    print("🧪 RawDataBackupLayer 테스트")
    
    backup_layer = RawDataBackupLayer()
    backup_layer.initialize()
    
    # 테스트 백업 생성
    test_contents = [
        "Claude Code에서 STM 성능 문제를 해결하고 싶어요.",
        "def calculate_risk(content_length, session_history): return 0.5",
        "🚨 Auto-compact이 감지되었습니다! 중요한 데이터를 백업하세요.",
        "일반적인 대화 내용입니다."
    ]
    
    backup_ids = []
    for i, content in enumerate(test_contents):
        context_type = [
            ContextType.USER_MESSAGE,
            ContextType.ASSISTANT_RESPONSE, 
            ContextType.SYSTEM_STATE,
            ContextType.CONVERSATION_TURN
        ][i]
        
        backup_id = backup_layer.backup_context_immediately(content, context_type)
        backup_ids.append(backup_id)
        print(f"✅ 백업 생성: {backup_id[:8]}...")
    
    # 배치 처리 테스트
    print("\n🔄 배치 처리 실행...")
    results = backup_layer.process_backup_queue()
    print(f"  처리: {results['processed_count']}")
    print(f"  LTM 전송: {results['ltm_transferred']}")
    print(f"  실패: {results['failed_count']}")
    
    # Auto-compact 시뮬레이션
    print("\n🚨 Auto-compact 시뮬레이션...")
    backup_layer.auto_compact_monitor.context_length_history.append((datetime.now() - timedelta(minutes=5), 45000))
    backup_layer.auto_compact_monitor.context_length_history.append((datetime.now(), 15000))
    
    compact_event = backup_layer.detect_and_handle_auto_compact()
    if compact_event:
        print(f"  감지됨: {compact_event.event_id}")
        print(f"  영향받은 항목: {compact_event.affected_items}")
    
    # 상태 리포트
    backup_layer.print_status_report()