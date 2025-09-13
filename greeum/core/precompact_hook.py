#!/usr/bin/env python3
"""
PreCompact Hook Handler for Claude Code Integration

이 모듈은 Claude Code의 auto-compact 이벤트를 실시간으로 감지하고
긴급 백업을 수행하는 핵심 컴포넌트입니다.

Author: Greeum Development Team
Version: 2.6.4
"""

import os
import sys
import signal
import threading
import time
import json
import logging
from typing import Dict, Any, Optional, Callable, List
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass

from .claude_code_detector import ClaudeCodeDetector
from .context_backup import ContextBackupItem, ContextType
from .raw_data_backup_layer import RawDataBackupLayer
from .auto_compact_monitor import AutoCompactMonitor


@dataclass
class PreCompactEvent:
    """PreCompact 이벤트 데이터 구조"""
    timestamp: datetime
    context_length: int
    session_id: str
    trigger_type: str  # 'auto', 'manual', 'memory_limit'
    context_preview: str
    urgency_level: float  # 0.0-1.0
    

class PreCompactHookHandler:
    """
    Claude Code PreCompact 이벤트 실시간 처리 핸들러
    
    Claude Code 환경에서 auto-compact가 발생하기 전에
    컨텍스트를 긴급 백업하고 보존하는 역할을 담당합니다.
    """
    
    def __init__(self, backup_layer: RawDataBackupLayer, session_id: Optional[str] = None):
        self.backup_layer = backup_layer
        self.detector = ClaudeCodeDetector()
        self.monitor = AutoCompactMonitor()
        self.logger = logging.getLogger(__name__)
        
        # Hook 상태 관리
        self.is_active = False
        self.hook_thread: Optional[threading.Thread] = None
        self.event_handlers: List[Callable[[PreCompactEvent], None]] = []
        
        # Context 모니터링
        self.last_context_length = 0
        self.context_history: List[Dict[str, Any]] = []
        self.session_id = session_id or self._generate_session_id()
        
        # 설정
        self.monitoring_interval = 1.0  # 초 단위
        self.emergency_threshold = 0.8   # 긴급 백업 임계값
        
    def register_hook(self) -> bool:
        """
        PreCompact Hook을 등록하고 모니터링을 시작합니다.
        
        Returns:
            bool: Hook 등록 성공 여부
        """
        if not self.detector.is_claude_code_host:
            self.logger.warning("Not running in Claude Code environment - hook registration skipped")
            return False
            
        try:
            # 환경 변수 기반 모니터링 시작
            self._setup_environment_monitoring()
            
            # 컨텍스트 길이 모니터링 스레드 시작
            self.hook_thread = threading.Thread(
                target=self._context_monitoring_loop,
                daemon=True,
                name="PreCompactHookHandler"
            )
            self.is_active = True
            self.hook_thread.start()
            
            self.logger.info(f"PreCompact Hook registered successfully for session {self.session_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to register PreCompact Hook: {e}")
            return False
    
    def unregister_hook(self) -> None:
        """Hook 등록을 해제하고 모니터링을 중단합니다."""
        self.is_active = False
        if self.hook_thread and self.hook_thread.is_alive():
            self.hook_thread.join(timeout=2.0)
        self.logger.info("PreCompact Hook unregistered")
    
    def add_event_handler(self, handler: Callable[[PreCompactEvent], None]) -> None:
        """PreCompact 이벤트 핸들러를 추가합니다."""
        self.event_handlers.append(handler)
        
    def handle_precompact_signal(self, context_data: Dict[str, Any]) -> None:
        """
        PreCompact 시그널을 처리하고 긴급 백업을 수행합니다.
        
        Args:
            context_data: 현재 컨텍스트 데이터
        """
        try:
            # PreCompact 이벤트 생성
            event = self._create_precompact_event(context_data)
            
            # 긴급도 평가
            if event.urgency_level >= self.emergency_threshold:
                backup_id = self.emergency_backup(context_data)
                self.logger.info(f"Emergency backup completed: {backup_id}")
            
            # 등록된 핸들러들에게 이벤트 전달
            for handler in self.event_handlers:
                try:
                    handler(event)
                except Exception as e:
                    self.logger.error(f"Event handler failed: {e}")
                    
        except Exception as e:
            self.logger.error(f"Failed to handle precompact signal: {e}")
    
    def emergency_backup(self, urgent_data: Any) -> str:
        """
        긴급 백업을 수행합니다.
        
        Args:
            urgent_data: 백업할 긴급 데이터
            
        Returns:
            str: 백업 ID
        """
        try:
            # ContextBackupItem 생성
            backup_item = ContextBackupItem(
                raw_content=str(urgent_data),
                context_type=ContextType.ERROR_CONTEXT,
                session_id=self.session_id,
                timestamp=datetime.now(),
                auto_compact_risk_score=1.0,  # 최고 위험도
                original_length=len(str(urgent_data)),
                recovery_metadata={
                    "trigger": "emergency_backup",
                    "handler": "PreCompactHookHandler",
                    "context_preview": str(urgent_data)[:200] + "..." if len(str(urgent_data)) > 200 else str(urgent_data)
                }
            )
            
            # 즉시 백업 수행
            backup_id = self.backup_layer.backup_context_immediately(
                content=backup_item.raw_content,
                context_type=backup_item.context_type,
                session_id=backup_item.session_id
            )
            
            self.logger.info(f"Emergency backup completed - ID: {backup_id}")
            return backup_id
            
        except Exception as e:
            self.logger.error(f"Emergency backup failed: {e}")
            return f"error_{int(time.time())}"
    
    def get_hook_status(self) -> Dict[str, Any]:
        """현재 Hook 상태를 반환합니다."""
        return {
            "is_active": self.is_active,
            "session_id": self.session_id,
            "claude_code_detected": self.detector.is_claude_code_host,
            "monitoring_interval": self.monitoring_interval,
            "emergency_threshold": self.emergency_threshold,
            "last_context_length": self.last_context_length,
            "context_history_size": len(self.context_history),
            "event_handlers_count": len(self.event_handlers)
        }
    
    def _setup_environment_monitoring(self) -> None:
        """환경 변수 기반 모니터링을 설정합니다."""
        # Claude Code 특정 환경 변수들 모니터링
        self.claude_code_vars = [
            "CLAUDECODE",
            "CLAUDE_CODE_ENTRYPOINT", 
            "CLAUDE_SESSION_ID",
            "CLAUDE_CONTEXT_LENGTH"
        ]
        
        # 초기 환경 상태 저장
        self.initial_env = {var: os.getenv(var) for var in self.claude_code_vars}
        self.logger.debug(f"Initial environment: {self.initial_env}")
    
    def _context_monitoring_loop(self) -> None:
        """컨텍스트 길이 모니터링 루프"""
        while self.is_active:
            try:
                current_length = self._get_current_context_length()
                
                if current_length != self.last_context_length:
                    # 컨텍스트 변화 감지
                    self._handle_context_change(current_length)
                    self.last_context_length = current_length
                
                # Auto-compact 위험도 평가
                risk_score = self.monitor.calculate_risk(
                    content_length=current_length,
                    session_history=len(self.context_history),
                    conversation_turns=len(self.context_history)
                )
                if risk_score >= self.emergency_threshold:
                    self._trigger_emergency_backup_check()
                
                time.sleep(self.monitoring_interval)
                
            except Exception as e:
                self.logger.error(f"Context monitoring error: {e}")
                time.sleep(self.monitoring_interval * 2)  # 오류 시 간격 증가
    
    def _get_current_context_length(self) -> int:
        """현재 컨텍스트 길이를 추정합니다."""
        try:
            # Claude Code 환경 변수에서 컨텍스트 길이 추출 시도
            length_var = os.getenv("CLAUDE_CONTEXT_LENGTH")
            if length_var:
                return int(length_var)
            
            # 다른 방법으로 컨텍스트 길이 추정
            # (실제 구현에서는 더 정교한 방법이 필요할 수 있음)
            return self._estimate_context_length()
            
        except Exception:
            return 0
    
    def _estimate_context_length(self) -> int:
        """컨텍스트 길이를 추정합니다."""
        # 임시 구현 - 실제로는 더 정교한 추정이 필요
        try:
            # sys.argv나 환경 변수 크기로 대략적 추정
            total_size = sum(len(arg) for arg in sys.argv)
            total_size += sum(len(f"{k}={v}") for k, v in os.environ.items() 
                            if k.startswith("CLAUDE"))
            return total_size
        except Exception:
            return 0
    
    def _handle_context_change(self, new_length: int) -> None:
        """컨텍스트 변화를 처리합니다."""
        change_data = {
            "timestamp": datetime.now().isoformat(),
            "old_length": self.last_context_length,
            "new_length": new_length,
            "change_delta": new_length - self.last_context_length
        }
        
        self.context_history.append(change_data)
        
        # 히스토리 크기 제한 (최근 100개)
        if len(self.context_history) > 100:
            self.context_history.pop(0)
        
        self.logger.debug(f"Context change detected: {change_data}")
    
    def _trigger_emergency_backup_check(self) -> None:
        """긴급 백업 체크를 트리거합니다."""
        try:
            # 현재 환경 상태 수집
            current_env = {var: os.getenv(var) for var in self.claude_code_vars}
            
            # 환경 변화 감지
            env_changed = current_env != self.initial_env
            
            if env_changed:
                self.logger.warning("Environment change detected - potential auto-compact incoming")
                
                # 긴급 백업 데이터 준비
                emergency_data = {
                    "session_id": self.session_id,
                    "context_history": self.context_history[-10:],  # 최근 10개
                    "environment_change": {
                        "before": self.initial_env,
                        "after": current_env
                    },
                    "timestamp": datetime.now().isoformat()
                }
                
                # 긴급 백업 수행
                self.emergency_backup(emergency_data)
                
        except Exception as e:
            self.logger.error(f"Emergency backup check failed: {e}")
    
    def _create_precompact_event(self, context_data: Dict[str, Any]) -> PreCompactEvent:
        """PreCompact 이벤트를 생성합니다."""
        return PreCompactEvent(
            timestamp=datetime.now(),
            context_length=context_data.get("length", 0),
            session_id=self.session_id,
            trigger_type=context_data.get("trigger_type", "unknown"),
            context_preview=context_data.get("preview", str(context_data)[:200]),
            urgency_level=context_data.get("urgency", 0.5)
        )
    
    def _generate_session_id(self) -> str:
        """세션 ID를 생성합니다."""
        return f"claude_session_{int(time.time())}_{os.getpid()}"


# 편의 함수들
def create_precompact_hook(backup_layer: RawDataBackupLayer, session_id: Optional[str] = None) -> PreCompactHookHandler:
    """PreCompact Hook Handler 인스턴스를 생성합니다."""
    return PreCompactHookHandler(backup_layer, session_id)


def register_default_precompact_hook() -> Optional[PreCompactHookHandler]:
    """기본 설정으로 PreCompact Hook을 등록합니다."""
    try:
        from .database_manager import DatabaseManager
        
        # 기본 컴포넌트들 초기화
        db_manager = DatabaseManager()
        backup_layer = RawDataBackupLayer(db_manager)
        
        # Hook 핸들러 생성 및 등록
        hook_handler = create_precompact_hook(backup_layer)
        
        if hook_handler.register_hook():
            return hook_handler
        else:
            return None
            
    except Exception as e:
        logging.error(f"Failed to register default precompact hook: {e}")
        return None


if __name__ == "__main__":
    # 테스트용 실행
    logging.basicConfig(level=logging.INFO)
    
    print("[LINK] PreCompact Hook Handler 테스트")
    
    # 기본 Hook 등록 테스트
    hook = register_default_precompact_hook()
    
    if hook:
        print("✅ PreCompact Hook 등록 성공")
        print(f"📊 Hook 상태: {hook.get_hook_status()}")
        
        # 3초 후 테스트 이벤트 발생
        time.sleep(3)
        
        test_context = {
            "length": 15000,
            "trigger_type": "test", 
            "preview": "테스트 컨텍스트 데이터...",
            "urgency": 0.9
        }
        
        hook.handle_precompact_signal(test_context)
        print("✅ 테스트 이벤트 처리 완료")
        
        # Hook 해제
        hook.unregister_hook()
        print("✅ Hook 해제 완료")
    else:
        print("[ERROR] PreCompact Hook 등록 실패")