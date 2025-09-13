#!/usr/bin/env python3
"""
Context Recovery System for Greeum

백업된 컨텍스트 데이터를 복원하고 재구성하여 
Claude Code 세션 간 연속성을 보장하는 핵심 시스템입니다.

Author: Greeum Development Team
Version: 2.6.4
"""

import json
import logging
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
from pathlib import Path

from .context_backup import ContextBackupItem, ContextType, ProcessingStatus, BackupStrategy, RetentionPriority
from .raw_data_backup_layer import RawDataBackupLayer
from .database_manager import DatabaseManager


@dataclass
class RecoverySession:
    """복원 세션 정보"""
    session_id: str
    original_session_id: str
    recovery_timestamp: datetime
    items_recovered: int
    recovery_quality_score: float
    context_preview: str


@dataclass
class ContextSegment:
    """컨텍스트 세그먼트"""
    content: str
    timestamp: datetime
    importance_score: float
    segment_type: str  # 'dialogue', 'code', 'analysis', 'instruction'
    context_position: int  # 원래 컨텍스트에서의 위치
    

class ContextRecoveryManager:
    """
    백업된 컨텍스트 복원 및 재구성 관리자
    
    Claude Code의 auto-compact로 손실된 컨텍스트를 
    백업 데이터로부터 지능적으로 복원합니다.
    """
    
    def __init__(self, backup_layer: RawDataBackupLayer):
        self.backup_layer = backup_layer
        self.logger = logging.getLogger(__name__)
        
        # 복원 설정
        self.max_recovery_items = 100
        self.min_quality_threshold = 0.5
        self.context_merge_window = timedelta(minutes=30)
        
        # 세그먼트 분류 키워드
        self.segment_classifiers = {
            'dialogue': ['사용자:', 'assistant:', 'User:', 'Assistant:', '질문:', '답변:'],
            'code': ['```', 'def ', 'class ', 'import ', 'function', 'const ', 'let ', 'var '],
            'analysis': ['분석', '결과', '평가', '검토', '테스트', 'analysis', 'result', 'evaluation'],
            'instruction': ['지시:', '요청:', '명령:', 'instruction:', 'command:', 'request:']
        }
    
    def recover_session_context(self, session_id: str, limit: int = None) -> Dict[str, Any]:
        """
        특정 세션의 컨텍스트를 복원합니다.
        
        Args:
            session_id: 복원할 세션 ID
            limit: 복원할 최대 항목 수 (None이면 기본값 사용)
            
        Returns:
            복원된 컨텍스트 데이터
        """
        try:
            self.logger.info(f"Starting context recovery for session: {session_id}")
            
            # 백업 데이터 검색
            backup_items = self._get_session_backup_items(session_id, limit or self.max_recovery_items)
            
            if not backup_items:
                return self._create_empty_recovery_result(session_id, "No backup items found")
            
            # 백업 항목들을 시간순 정렬
            backup_items.sort(key=lambda x: x.timestamp)
            
            # 컨텍스트 세그먼트 추출 및 분류
            segments = self._extract_context_segments(backup_items)
            
            # 세그먼트 품질 평가 및 우선순위 지정
            prioritized_segments = self._prioritize_segments(segments)
            
            # 연속적인 컨텍스트 플로우 재구성
            recovered_context = self._rebuild_context_flow(prioritized_segments)
            
            # 복원 품질 평가
            quality_score = self._evaluate_recovery_quality(backup_items, recovered_context)
            
            # 복원 세션 기록
            recovery_session = RecoverySession(
                session_id=self._generate_recovery_session_id(),
                original_session_id=session_id,
                recovery_timestamp=datetime.now(),
                items_recovered=len(backup_items),
                recovery_quality_score=quality_score,
                context_preview=recovered_context[:500] + "..." if len(recovered_context) > 500 else recovered_context
            )
            
            result = {
                'success': True,
                'recovery_session': recovery_session,
                'recovered_context': recovered_context,
                'segments_count': len(segments),
                'quality_score': quality_score,
                'original_items_count': len(backup_items),
                'recovery_timestamp': datetime.now().isoformat()
            }
            
            self.logger.info(f"Context recovery completed - Quality: {quality_score:.2f}, Items: {len(backup_items)}")
            return result
            
        except Exception as e:
            self.logger.error(f"Context recovery failed for session {session_id}: {e}")
            return self._create_empty_recovery_result(session_id, f"Recovery failed: {str(e)}")
    
    def rebuild_conversation_flow(self, backup_items: List[ContextBackupItem]) -> str:
        """
        백업 항목들로부터 대화 흐름을 재구성합니다.
        
        Args:
            backup_items: 백업된 컨텍스트 항목들
            
        Returns:
            재구성된 대화 흐름 텍스트
        """
        try:
            if not backup_items:
                return ""
            
            # 타임스탬프 기준 정렬
            sorted_items = sorted(backup_items, key=lambda x: x.timestamp)
            
            conversation_parts = []
            last_timestamp = None
            
            for item in sorted_items:
                # 시간 간격이 클 경우 구분자 추가
                if last_timestamp and (item.timestamp - last_timestamp).seconds > 300:  # 5분
                    conversation_parts.append("\n--- [시간 간격] ---\n")
                
                # 컨텍스트 타입에 따른 포맷팅
                formatted_content = self._format_content_by_type(item)
                conversation_parts.append(formatted_content)
                
                last_timestamp = item.timestamp
            
            return "\n\n".join(conversation_parts)
            
        except Exception as e:
            self.logger.error(f"Failed to rebuild conversation flow: {e}")
            return f"[복원 오류: {str(e)}]"
    
    def smart_context_merge(self, old_context: str, new_context: str) -> str:
        """
        기존 컨텍스트와 새로운 컨텍스트를 지능적으로 병합합니다.
        
        Args:
            old_context: 기존 컨텍스트
            new_context: 새로운 컨텍스트
            
        Returns:
            병합된 컨텍스트
        """
        try:
            if not old_context:
                return new_context
            if not new_context:
                return old_context
            
            # 중복 내용 감지 및 제거
            merged_content = self._remove_duplicate_content(old_context, new_context)
            
            # 컨텍스트 연결점 찾기
            connection_point = self._find_context_connection_point(old_context, new_context)
            
            if connection_point:
                # 자연스러운 연결점이 있는 경우
                merged = self._merge_at_connection_point(old_context, new_context, connection_point)
            else:
                # 연결점이 없는 경우 시간 기준으로 병합
                merged = self._merge_by_timestamp(old_context, new_context)
            
            return merged
            
        except Exception as e:
            self.logger.error(f"Smart context merge failed: {e}")
            return f"{old_context}\n\n--- [병합 오류] ---\n\n{new_context}"
    
    def get_recovery_statistics(self, days: int = 7) -> Dict[str, Any]:
        """최근 복원 통계를 반환합니다."""
        try:
            # 최근 N일간의 백업 데이터 통계
            cutoff_date = datetime.now() - timedelta(days=days)
            
            # 데이터베이스에서 통계 쿼리 (실제 구현 시 SQL 쿼리 필요)
            stats = {
                'recovery_attempts': 0,
                'successful_recoveries': 0,
                'average_quality_score': 0.0,
                'total_items_recovered': 0,
                'most_common_failure_reason': 'No data',
                'average_recovery_time': 0.0,
                'context_types_recovered': {}
            }
            
            return stats
            
        except Exception as e:
            self.logger.error(f"Failed to get recovery statistics: {e}")
            return {'error': str(e)}
    
    def _get_session_backup_items(self, session_id: str, limit: int) -> List[ContextBackupItem]:
        """세션의 백업 항목들을 가져옵니다."""
        try:
            items = []
            
            # 백업 계층의 캐시에서 세션 항목들 검색
            for backup_item in self.backup_layer.backup_cache.values():
                if backup_item.session_id == session_id:
                    items.append(backup_item)
            
            # 캐시에 없으면 데이터베이스에서 직접 조회
            if not items and hasattr(self.backup_layer, 'db_manager'):
                try:
                    cursor = self.backup_layer.db_manager.conn.cursor()
                    cursor.execute("""
                        SELECT * FROM context_backups 
                        WHERE session_id = ? 
                        ORDER BY timestamp DESC 
                        LIMIT ?
                    """, (session_id, limit))
                    
                    for row in cursor.fetchall():
                        # DB row를 ContextBackupItem으로 변환
                        backup_item = self._backup_from_db_row(dict(row))
                        if backup_item:
                            items.append(backup_item)
                            
                except Exception as db_e:
                    self.logger.warning(f"Database query failed, using cache only: {db_e}")
            
            self.logger.info(f"Found {len(items)} backup items for session {session_id}")
            return items[:limit]
            
        except Exception as e:
            self.logger.error(f"Failed to get session backup items: {e}")
            return []
    
    def _backup_from_db_row(self, row_dict: Dict[str, Any]) -> Optional[ContextBackupItem]:
        """데이터베이스 row를 ContextBackupItem으로 변환합니다."""
        try:
            # 기본 필드들
            item = ContextBackupItem(
                id=row_dict.get('id', ''),
                session_id=row_dict.get('session_id', ''),
                raw_content=row_dict.get('raw_content', ''),
                context_type=ContextType(row_dict.get('context_type', 'user_message')),
                sequence_number=row_dict.get('sequence_number', 0),
                parent_context_id=row_dict.get('parent_context_id'),
                conversation_turn=row_dict.get('conversation_turn', 0),
                original_length=row_dict.get('original_length', 0),
                auto_compact_risk_score=row_dict.get('auto_compact_risk_score', 0.0),
                processing_status=ProcessingStatus(row_dict.get('processing_status', 'raw')),
                backup_strategy=BackupStrategy(row_dict.get('backup_strategy', 'immediate')),
                retention_priority=RetentionPriority(row_dict.get('retention_priority', 'normal'))
            )
            
            # 타임스탬프 변환
            if 'timestamp' in row_dict and row_dict['timestamp']:
                item.timestamp = datetime.fromisoformat(row_dict['timestamp'])
            if 'created_at' in row_dict and row_dict['created_at']:
                item.created_at = datetime.fromisoformat(row_dict['created_at'])
            if 'processed_at' in row_dict and row_dict['processed_at']:
                item.processed_at = datetime.fromisoformat(row_dict['processed_at'])
            if 'expires_at' in row_dict and row_dict['expires_at']:
                item.expires_at = datetime.fromisoformat(row_dict['expires_at'])
                
            # JSON 필드들 파싱
            if 'extracted_intents' in row_dict and row_dict['extracted_intents']:
                item.extracted_intents = json.loads(row_dict['extracted_intents'])
            if 'key_entities' in row_dict and row_dict['key_entities']:
                item.key_entities = json.loads(row_dict['key_entities'])
            if 'semantic_chunks' in row_dict and row_dict['semantic_chunks']:
                item.semantic_chunks = json.loads(row_dict['semantic_chunks'])
            if 'recovery_metadata' in row_dict and row_dict['recovery_metadata']:
                item.recovery_metadata = json.loads(row_dict['recovery_metadata'])
            if 'tool_usage_context' in row_dict and row_dict['tool_usage_context']:
                item.tool_usage_context = json.loads(row_dict['tool_usage_context'])
                
            return item
            
        except Exception as e:
            self.logger.error(f"Failed to convert DB row to ContextBackupItem: {e}")
            return None
    
    def _extract_context_segments(self, backup_items: List[ContextBackupItem]) -> List[ContextSegment]:
        """백업 항목들로부터 컨텍스트 세그먼트를 추출합니다."""
        segments = []
        
        for i, item in enumerate(backup_items):
            try:
                # 컨텍스트 타입 분류
                segment_type = self._classify_segment_type(item.raw_content)
                
                # 중요도 스코어 계산
                importance_score = self._calculate_segment_importance(item)
                
                segment = ContextSegment(
                    content=item.raw_content,
                    timestamp=item.timestamp,
                    importance_score=importance_score,
                    segment_type=segment_type,
                    context_position=i
                )
                
                segments.append(segment)
                
            except Exception as e:
                self.logger.warning(f"Failed to extract segment from item {i}: {e}")
                continue
        
        return segments
    
    def _classify_segment_type(self, content: str) -> str:
        """컨텍스트 내용의 타입을 분류합니다."""
        content_lower = content.lower()
        
        for segment_type, keywords in self.segment_classifiers.items():
            if any(keyword.lower() in content_lower for keyword in keywords):
                return segment_type
        
        return 'general'
    
    def _calculate_segment_importance(self, item: ContextBackupItem) -> float:
        """세그먼트의 중요도를 계산합니다."""
        importance = 0.5  # 기본값
        
        # 보존 우선순위 반영 (RetentionPriority enum 사용)
        priority_weights = {
            RetentionPriority.CRITICAL: 0.3,
            RetentionPriority.HIGH: 0.2,
            RetentionPriority.NORMAL: 0.1,
            RetentionPriority.LOW: 0.05
        }
        importance += priority_weights.get(item.retention_priority, 0.05)
        
        # Auto-compact 위험도 반영
        importance += item.auto_compact_risk_score * 0.2
        
        # 컨텐츠 길이 반영 (적당한 길이가 좋음)
        length_factor = min(item.original_length / 1000, 1.0) * 0.15
        importance += length_factor
        
        # 컨텍스트 타입별 가중치
        type_weights = {
            ContextType.ERROR_CONTEXT: 0.3,
            ContextType.USER_MESSAGE: 0.2,
            ContextType.TOOL_RESULT: 0.15,
            ContextType.CONVERSATION_TURN: 0.1,
            ContextType.SYSTEM_STATE: 0.05
        }
        importance += type_weights.get(item.context_type, 0.05)
        
        return min(importance, 1.0)
    
    def _prioritize_segments(self, segments: List[ContextSegment]) -> List[ContextSegment]:
        """세그먼트들을 우선순위로 정렬합니다."""
        return sorted(segments, key=lambda s: (s.importance_score, s.context_position), reverse=True)
    
    def _rebuild_context_flow(self, segments: List[ContextSegment]) -> str:
        """우선순위가 지정된 세그먼트들로부터 컨텍스트 플로우를 재구성합니다."""
        if not segments:
            return ""
        
        # 높은 품질의 세그먼트만 선택
        quality_segments = [s for s in segments if s.importance_score >= self.min_quality_threshold]
        
        # 시간순으로 재정렬
        time_ordered = sorted(quality_segments, key=lambda s: s.timestamp)
        
        # 컨텍스트 재구성
        context_parts = []
        for segment in time_ordered:
            formatted_segment = self._format_segment_for_recovery(segment)
            context_parts.append(formatted_segment)
        
        return "\n\n".join(context_parts)
    
    def _format_segment_for_recovery(self, segment: ContextSegment) -> str:
        """복원용 세그먼트 포맷팅"""
        timestamp_str = segment.timestamp.strftime("%H:%M:%S")
        type_marker = {
            'dialogue': '💬',
            'code': '🔧', 
            'analysis': '📊',
            'instruction': '📋',
            'general': '[NOTE]'
        }.get(segment.segment_type, '[NOTE]')
        
        return f"[{timestamp_str}] {type_marker} {segment.content}"
    
    def _format_content_by_type(self, item: ContextBackupItem) -> str:
        """컨텍스트 타입에 따라 내용을 포맷팅합니다."""
        timestamp = item.timestamp.strftime("%Y-%m-%d %H:%M:%S")
        
        if item.context_type == "emergency_precompact":
            return f"[ALERT] [긴급백업 {timestamp}]\n{item.raw_content}"
        elif item.context_type == "user_interaction":
            return f"👤 [사용자 {timestamp}]\n{item.raw_content}"
        elif item.context_type == "code_analysis":
            return f"🔧 [코드분석 {timestamp}]\n{item.raw_content}"
        else:
            return f"[NOTE] [{item.context_type} {timestamp}]\n{item.raw_content}"
    
    def _evaluate_recovery_quality(self, original_items: List[ContextBackupItem], recovered_context: str) -> float:
        """복원 품질을 평가합니다."""
        if not original_items or not recovered_context:
            return 0.0
        
        # 기본 품질 스코어
        quality_score = 0.7
        
        # 복원된 컨텍스트 길이 비율
        total_original_length = sum(item.original_length for item in original_items)
        recovery_ratio = min(len(recovered_context) / max(total_original_length, 1), 1.0)
        quality_score *= recovery_ratio
        
        # 시간 연속성 평가
        time_continuity = self._evaluate_time_continuity(original_items)
        quality_score += time_continuity * 0.2
        
        # 컨텐츠 다양성 평가
        content_diversity = len(set(item.context_type for item in original_items)) / 5.0  # 최대 5가지 타입
        quality_score += content_diversity * 0.1
        
        return min(quality_score, 1.0)
    
    def _evaluate_time_continuity(self, items: List[ContextBackupItem]) -> float:
        """시간 연속성을 평가합니다."""
        if len(items) < 2:
            return 1.0
        
        sorted_items = sorted(items, key=lambda x: x.timestamp)
        gaps = []
        
        for i in range(1, len(sorted_items)):
            gap = (sorted_items[i].timestamp - sorted_items[i-1].timestamp).total_seconds()
            gaps.append(gap)
        
        # 평균 간격이 적절한지 평가 (너무 크면 연속성 낮음)
        avg_gap = sum(gaps) / len(gaps)
        continuity_score = max(0, 1.0 - (avg_gap / 3600))  # 1시간 기준
        
        return continuity_score
    
    def _remove_duplicate_content(self, old_context: str, new_context: str) -> str:
        """중복 내용을 제거합니다."""
        # 단순 구현 - 실제로는 더 정교한 중복 감지 필요
        lines_old = set(old_context.split('\n'))
        lines_new = new_context.split('\n')
        
        unique_new_lines = [line for line in lines_new if line not in lines_old]
        
        return '\n'.join(unique_new_lines)
    
    def _find_context_connection_point(self, old_context: str, new_context: str) -> Optional[str]:
        """두 컨텍스트 간의 연결점을 찾습니다."""
        # 단순 구현 - 공통 문장이나 패턴 찾기
        old_lines = old_context.split('\n')[-10:]  # 마지막 10줄
        new_lines = new_context.split('\n')[:10]   # 처음 10줄
        
        for old_line in old_lines:
            for new_line in new_lines:
                # 70% 이상 유사하면 연결점으로 판단
                similarity = self._calculate_line_similarity(old_line, new_line)
                if similarity > 0.7:
                    return old_line
        
        return None
    
    def _calculate_line_similarity(self, line1: str, line2: str) -> float:
        """두 줄의 유사도를 계산합니다."""
        if not line1 or not line2:
            return 0.0
        
        # 단순 구현 - 실제로는 더 정교한 유사도 계산 필요
        words1 = set(line1.lower().split())
        words2 = set(line2.lower().split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = words1 & words2
        union = words1 | words2
        
        return len(intersection) / len(union)
    
    def _merge_at_connection_point(self, old_context: str, new_context: str, connection_point: str) -> str:
        """연결점에서 두 컨텍스트를 병합합니다."""
        # 연결점을 기준으로 split하고 merge
        old_parts = old_context.split(connection_point)
        new_parts = new_context.split(connection_point)
        
        if len(old_parts) >= 2 and len(new_parts) >= 2:
            merged = old_parts[0] + connection_point + new_parts[1]
        else:
            merged = old_context + "\n\n--- [연결] ---\n\n" + new_context
        
        return merged
    
    def _merge_by_timestamp(self, old_context: str, new_context: str) -> str:
        """타임스탬프 기준으로 두 컨텍스트를 병합합니다."""
        return f"{old_context}\n\n--- [시간순 병합] ---\n\n{new_context}"
    
    def _create_empty_recovery_result(self, session_id: str, reason: str) -> Dict[str, Any]:
        """빈 복원 결과를 생성합니다."""
        return {
            'success': False,
            'session_id': session_id,
            'error_reason': reason,
            'recovered_context': "",
            'segments_count': 0,
            'quality_score': 0.0,
            'recovery_timestamp': datetime.now().isoformat()
        }
    
    def _generate_recovery_session_id(self) -> str:
        """복원 세션 ID를 생성합니다."""
        return f"recovery_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{id(self) % 10000}"


# 편의 함수들
def create_recovery_manager(backup_layer: RawDataBackupLayer) -> ContextRecoveryManager:
    """Context Recovery Manager 인스턴스를 생성합니다."""
    return ContextRecoveryManager(backup_layer)


def quick_session_recovery(session_id: str) -> str:
    """빠른 세션 복원을 수행합니다."""
    try:
        from .database_manager import DatabaseManager
        
        db_manager = DatabaseManager()
        backup_layer = RawDataBackupLayer(db_manager)
        recovery_manager = create_recovery_manager(backup_layer)
        
        result = recovery_manager.recover_session_context(session_id)
        return result.get('recovered_context', 'Recovery failed')
        
    except Exception as e:
        return f"Quick recovery failed: {str(e)}"


if __name__ == "__main__":
    # 테스트용 실행
    logging.basicConfig(level=logging.INFO)
    
    print("[PROCESS] Context Recovery System 테스트")
    
    # 임시 테스트 데이터
    test_session_id = "test_session_123"
    
    # 테스트 복원
    result = quick_session_recovery(test_session_id)
    print(f"✅ 테스트 복원 결과: {result}")
    
    print("✅ Context Recovery System 준비 완료")