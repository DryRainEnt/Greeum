"""
Context Backup System for Greeum v2.6.3
STM Architecture Reimagining - Raw Data Backup Schema

Claude Code auto-compact 대응 컨텍스트 보존 시스템
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Dict, Any, Optional
from datetime import datetime
import uuid
import json


class ContextType(Enum):
    """컨텍스트 백업 유형"""
    USER_MESSAGE = "user_message"           # 사용자 메시지
    ASSISTANT_RESPONSE = "assistant_response" # AI 응답
    TOOL_RESULT = "tool_result"             # 도구 실행 결과
    SYSTEM_STATE = "system_state"           # 시스템 상태 정보
    ERROR_CONTEXT = "error_context"         # 오류 발생 맥락
    CONVERSATION_TURN = "conversation_turn" # 대화 턴 전체
    MCP_INTERACTION = "mcp_interaction"     # MCP 서버 상호작용


class ProcessingStatus(Enum):
    """처리 상태"""
    RAW = "raw"                            # 원시 데이터 상태
    EXTRACTING = "extracting"              # 정보 추출 중
    READY_FOR_LTM = "ready_for_ltm"       # LTM 전송 준비 완료
    PROCESSED = "processed"                # LTM 처리 완료
    LOST = "lost"                          # Auto-compact으로 손실
    RECOVERED = "recovered"                # 백업에서 복구됨
    FAILED = "failed"                      # 처리 실패
    ARCHIVED = "archived"                  # 보관됨


class BackupStrategy(Enum):
    """백업 전략"""
    IMMEDIATE = "immediate"                # 즉시 백업
    PERIODIC = "periodic"                  # 주기적 백업
    THRESHOLD_BASED = "threshold_based"    # 임계점 기반 백업
    USER_TRIGGERED = "user_triggered"      # 사용자 수동 백업
    AUTO_COMPACT_TRIGGERED = "auto_compact_triggered" # Auto-compact 감지 시


class RetentionPriority(Enum):
    """보존 우선순위"""
    CRITICAL = "critical"      # 절대 삭제 금지 (영구 보존)
    HIGH = "high"             # 높은 보존 우선순위 (30일)
    NORMAL = "normal"         # 일반 보존 (7일)
    LOW = "low"              # 낮은 보존 (24시간)
    DISPOSABLE = "disposable" # 언제든 삭제 가능 (1시간)


@dataclass
class ContextBackupItem:
    """Raw Context Backup Item for STM Layer"""
    
    # Core Identifiers
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    session_id: str = ""
    timestamp: datetime = field(default_factory=datetime.now)
    
    # Raw Context Data (핵심: 원본 데이터 보존)
    raw_content: str = ""
    context_type: ContextType = ContextType.USER_MESSAGE
    
    # Context Position & Sequencing
    sequence_number: int = 0
    parent_context_id: Optional[str] = None
    conversation_turn: int = 0
    
    # Pre-processing Metadata (처리 전 원본 정보)
    original_length: int = 0
    auto_compact_risk_score: float = 0.0  # 0.0-1.0
    processing_status: ProcessingStatus = ProcessingStatus.RAW
    
    # Extraction Ready Data (LTM 처리 준비 데이터)
    extracted_intents: List[str] = field(default_factory=list)
    key_entities: List[str] = field(default_factory=list)
    semantic_chunks: List[str] = field(default_factory=list)
    
    # Backup Strategy Metadata
    backup_strategy: BackupStrategy = BackupStrategy.IMMEDIATE
    retention_priority: RetentionPriority = RetentionPriority.NORMAL
    recovery_metadata: Dict[str, Any] = field(default_factory=dict)
    
    # Claude Code Integration
    claudecode_context_id: Optional[str] = None
    tool_usage_context: List[str] = field(default_factory=list)
    
    # Processing Timestamps
    created_at: datetime = field(default_factory=datetime.now)
    processed_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    
    def __post_init__(self):
        """초기화 후 처리"""
        if not self.session_id:
            self.session_id = f"session-{uuid.uuid4().hex[:8]}"
        
        if self.original_length == 0 and self.raw_content:
            self.original_length = len(self.raw_content)
        
        # 보존 우선순위에 따른 만료 시간 설정
        if self.expires_at is None:
            self.expires_at = self._calculate_expiry_time()
    
    def _calculate_expiry_time(self) -> Optional[datetime]:
        """보존 우선순위에 따른 만료 시간 계산"""
        from datetime import timedelta
        
        if self.retention_priority == RetentionPriority.CRITICAL:
            return None  # 영구 보존
        elif self.retention_priority == RetentionPriority.HIGH:
            return self.created_at + timedelta(days=30)
        elif self.retention_priority == RetentionPriority.NORMAL:
            return self.created_at + timedelta(days=7)
        elif self.retention_priority == RetentionPriority.LOW:
            return self.created_at + timedelta(days=1)
        else:  # DISPOSABLE
            return self.created_at + timedelta(hours=1)
    
    def is_expired(self) -> bool:
        """만료되었는지 확인"""
        if self.expires_at is None:  # CRITICAL = 영구 보존
            return False
        return datetime.now() > self.expires_at
    
    def is_ready_for_ltm(self) -> bool:
        """LTM 전송 준비가 되었는지 확인"""
        return (
            self.processing_status == ProcessingStatus.READY_FOR_LTM and
            len(self.extracted_intents) > 0 and
            len(self.semantic_chunks) > 0
        )
    
    def should_immediate_process(self) -> bool:
        """즉시 처리해야 하는지 확인"""
        return (
            self.auto_compact_risk_score > 0.7 or
            self.retention_priority == RetentionPriority.CRITICAL or
            self.backup_strategy == BackupStrategy.AUTO_COMPACT_TRIGGERED
        )
    
    def extract_semantic_info(self) -> bool:
        """의미 정보 추출 (간단한 버전)"""
        try:
            self.processing_status = ProcessingStatus.EXTRACTING
            
            # 간단한 의도 추출 (키워드 기반)
            content_lower = self.raw_content.lower()
            intent_keywords = {
                "질문": ["뭐", "무엇", "어떻게", "왜", "언제", "어디서", "누가", "?"],
                "요청": ["해줘", "만들어", "구현", "작성", "생성", "추가"],
                "설명": ["설명", "알려줘", "보여줘", "이해", "파악"],
                "문제해결": ["오류", "에러", "문제", "해결", "수정", "고치"],
                "확인": ["확인", "체크", "검증", "테스트", "검토"]
            }
            
            for intent, keywords in intent_keywords.items():
                if any(keyword in content_lower for keyword in keywords):
                    self.extracted_intents.append(intent)
            
            # 간단한 엔티티 추출 (대문자 단어, 코드 패턴)
            words = self.raw_content.split()
            for word in words:
                # 대문자로 시작하는 단어 (고유명사 가능성)
                if word[0].isupper() and len(word) > 2:
                    self.key_entities.append(word)
                
                # 파일 확장자 패턴
                if '.' in word and any(ext in word for ext in ['.py', '.js', '.md', '.json', '.txt']):
                    self.key_entities.append(word)
            
            # 의미 청크로 분할 (문장 단위)
            sentences = [s.strip() for s in self.raw_content.split('.') if s.strip()]
            self.semantic_chunks = sentences[:10]  # 최대 10개 청크
            
            self.processing_status = ProcessingStatus.READY_FOR_LTM
            self.processed_at = datetime.now()
            
            return True
            
        except Exception as e:
            self.processing_status = ProcessingStatus.FAILED
            self.recovery_metadata['extraction_error'] = str(e)
            return False
    
    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환 (직렬화)"""
        return {
            'id': self.id,
            'session_id': self.session_id,
            'timestamp': self.timestamp.isoformat(),
            'raw_content': self.raw_content,
            'context_type': self.context_type.value,
            'sequence_number': self.sequence_number,
            'parent_context_id': self.parent_context_id,
            'conversation_turn': self.conversation_turn,
            'original_length': self.original_length,
            'auto_compact_risk_score': self.auto_compact_risk_score,
            'processing_status': self.processing_status.value,
            'extracted_intents': self.extracted_intents,
            'key_entities': self.key_entities,
            'semantic_chunks': self.semantic_chunks,
            'backup_strategy': self.backup_strategy.value,
            'retention_priority': self.retention_priority.value,
            'recovery_metadata': self.recovery_metadata,
            'claudecode_context_id': self.claudecode_context_id,
            'tool_usage_context': self.tool_usage_context,
            'created_at': self.created_at.isoformat(),
            'processed_at': self.processed_at.isoformat() if self.processed_at else None,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ContextBackupItem':
        """딕셔너리에서 복원 (역직렬화)"""
        item = cls()
        
        item.id = data.get('id', item.id)
        item.session_id = data.get('session_id', item.session_id)
        item.timestamp = datetime.fromisoformat(data['timestamp']) if data.get('timestamp') else item.timestamp
        item.raw_content = data.get('raw_content', '')
        item.context_type = ContextType(data.get('context_type', 'user_message'))
        item.sequence_number = data.get('sequence_number', 0)
        item.parent_context_id = data.get('parent_context_id')
        item.conversation_turn = data.get('conversation_turn', 0)
        item.original_length = data.get('original_length', 0)
        item.auto_compact_risk_score = data.get('auto_compact_risk_score', 0.0)
        item.processing_status = ProcessingStatus(data.get('processing_status', 'raw'))
        item.extracted_intents = data.get('extracted_intents', [])
        item.key_entities = data.get('key_entities', [])
        item.semantic_chunks = data.get('semantic_chunks', [])
        item.backup_strategy = BackupStrategy(data.get('backup_strategy', 'immediate'))
        item.retention_priority = RetentionPriority(data.get('retention_priority', 'normal'))
        item.recovery_metadata = data.get('recovery_metadata', {})
        item.claudecode_context_id = data.get('claudecode_context_id')
        item.tool_usage_context = data.get('tool_usage_context', [])
        item.created_at = datetime.fromisoformat(data['created_at']) if data.get('created_at') else item.created_at
        item.processed_at = datetime.fromisoformat(data['processed_at']) if data.get('processed_at') else None
        item.expires_at = datetime.fromisoformat(data['expires_at']) if data.get('expires_at') else None
        
        return item
    
    def to_json(self) -> str:
        """JSON 문자열로 변환"""
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)
    
    @classmethod
    def from_json(cls, json_str: str) -> 'ContextBackupItem':
        """JSON 문자열에서 복원"""
        data = json.loads(json_str)
        return cls.from_dict(data)
    
    def __str__(self) -> str:
        """문자열 표현"""
        status_emoji = {
            ProcessingStatus.RAW: "[NOTE]",
            ProcessingStatus.EXTRACTING: "[PROCESS]", 
            ProcessingStatus.READY_FOR_LTM: "✅",
            ProcessingStatus.PROCESSED: "💾",
            ProcessingStatus.LOST: "[ERROR]",
            ProcessingStatus.RECOVERED: "[PROCESS]",
            ProcessingStatus.FAILED: "💥",
            ProcessingStatus.ARCHIVED: "📦"
        }
        
        priority_emoji = {
            RetentionPriority.CRITICAL: "🔥",
            RetentionPriority.HIGH: "⭐", 
            RetentionPriority.NORMAL: "📄",
            RetentionPriority.LOW: "📃",
            RetentionPriority.DISPOSABLE: "🗑️"
        }
        
        content_preview = (self.raw_content[:50] + "...") if len(self.raw_content) > 50 else self.raw_content
        
        return (
            f"{status_emoji.get(self.processing_status, '❓')} "
            f"{priority_emoji.get(self.retention_priority, '❓')} "
            f"[{self.context_type.value}] "
            f"{content_preview} "
            f"(risk: {self.auto_compact_risk_score:.1f})"
        )


def create_context_backup(
    content: str,
    context_type: ContextType = ContextType.USER_MESSAGE,
    session_id: str = "",
    retention_priority: RetentionPriority = RetentionPriority.NORMAL,
    auto_compact_risk_score: float = 0.0
) -> ContextBackupItem:
    """편의 함수: ContextBackupItem 생성"""
    
    return ContextBackupItem(
        raw_content=content,
        context_type=context_type,
        session_id=session_id,
        retention_priority=retention_priority,
        auto_compact_risk_score=auto_compact_risk_score,
        backup_strategy=BackupStrategy.IMMEDIATE
    )


if __name__ == "__main__":
    # 테스트 코드
    print("🧪 ContextBackupItem 테스트")
    
    # 백업 항목 생성
    backup = create_context_backup(
        content="Claude Code에서 STM 성능 문제를 해결하고 싶어요. 어떻게 해야 할까요?",
        context_type=ContextType.USER_MESSAGE,
        retention_priority=RetentionPriority.HIGH,
        auto_compact_risk_score=0.8
    )
    
    print(f"생성된 백업: {backup}")
    
    # 의미 정보 추출
    if backup.extract_semantic_info():
        print(f"✅ 의미 추출 완료:")
        print(f"  의도: {backup.extracted_intents}")
        print(f"  엔티티: {backup.key_entities[:5]}")
        print(f"  청크 수: {len(backup.semantic_chunks)}")
    
    # 직렬화/역직렬화 테스트
    json_str = backup.to_json()
    restored = ContextBackupItem.from_json(json_str)
    print(f"✅ 직렬화 테스트: {backup.id == restored.id}")