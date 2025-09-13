"""
Auto-Compact Monitoring System for Greeum v2.6.3
STM Architecture Reimagining - Auto-Compact 감지 및 대응

Claude Code auto-compact 패턴 분석 및 위험도 예측
"""

import time
import json
import os
from typing import List, Dict, Any, Tuple, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from collections import deque
from enum import Enum

from .claude_code_detector import get_claude_code_detector


class CompactRiskLevel(Enum):
    """Auto-compact 위험도 레벨"""
    SAFE = "safe"           # 0.0 - 0.3
    LOW = "low"             # 0.3 - 0.5
    MEDIUM = "medium"       # 0.5 - 0.7
    HIGH = "high"           # 0.7 - 0.9
    CRITICAL = "critical"   # 0.9 - 1.0


@dataclass
class ContextMetrics:
    """컨텍스트 메트릭"""
    timestamp: datetime
    content_length: int
    session_history_count: int
    tool_usage_count: int
    conversation_turns: int
    memory_pressure: float = 0.0  # 메모리 사용량 압박도


@dataclass
class CompactEvent:
    """Auto-compact 이벤트"""
    timestamp: datetime
    detected_method: str
    context_length_before: int
    context_length_after: int
    affected_items: int = 0
    recovery_initiated: bool = False
    event_id: str = field(default_factory=lambda: f"compact-{int(time.time())}")


class AutoCompactMonitor:
    """Claude Code Auto-Compact 모니터링 및 예측 시스템"""
    
    def __init__(self, 
                 threshold: float = 0.8,
                 history_size: int = 100,
                 risk_update_interval: int = 30):  # 30초마다 위험도 업데이트
        
        self.threshold = threshold
        self.history_size = history_size
        self.risk_update_interval = risk_update_interval
        
        # 컨텍스트 길이 히스토리 (시간, 길이) 
        self.context_length_history: deque = deque(maxlen=history_size)
        
        # 메트릭 히스토리
        self.metrics_history: deque = deque(maxlen=history_size)
        
        # Compact 이벤트 기록
        self.compact_events: List[CompactEvent] = []
        
        # 현재 위험도 상태
        self.current_risk_score: float = 0.0
        self.current_risk_level: CompactRiskLevel = CompactRiskLevel.SAFE
        self.last_risk_update: datetime = datetime.now()
        
        # Claude Code 감지기
        self.claude_detector = get_claude_code_detector()
        
        # 패턴 분석 데이터
        self.compact_patterns: Dict[str, Any] = {
            'average_compact_interval': None,
            'typical_context_length_threshold': 50000,
            'session_based_threshold': 100,
            'tool_usage_impact_factor': 1.2
        }
    
    def record_context_metrics(self, 
                             content_length: int,
                             session_history_count: int = 0,
                             tool_usage_count: int = 0,
                             conversation_turns: int = 0) -> None:
        """현재 컨텍스트 메트릭 기록"""
        
        metrics = ContextMetrics(
            timestamp=datetime.now(),
            content_length=content_length,
            session_history_count=session_history_count,
            tool_usage_count=tool_usage_count,
            conversation_turns=conversation_turns
        )
        
        # 히스토리에 추가
        self.context_length_history.append((metrics.timestamp, content_length))
        self.metrics_history.append(metrics)
        
        # 위험도 업데이트 (간격 체크)
        if (datetime.now() - self.last_risk_update).seconds >= self.risk_update_interval:
            self._update_risk_assessment()
    
    def calculate_risk(self, 
                      content_length: int,
                      session_history: int,
                      tool_usage_count: int = 0,
                      conversation_turns: int = 0) -> float:
        """Auto-compact 위험도 계산 (0.0-1.0)"""
        
        risk_factors = []
        
        # 1. 컨텍스트 길이 기반 위험도
        length_threshold = self.compact_patterns['typical_context_length_threshold']
        length_risk = min(content_length / length_threshold, 1.0)
        risk_factors.append(('content_length', length_risk, 0.4))  # 40% 가중치
        
        # 2. 세션 히스토리 기반 위험도  
        history_threshold = self.compact_patterns['session_based_threshold']
        history_risk = min(session_history / history_threshold, 1.0)
        risk_factors.append(('session_history', history_risk, 0.3))  # 30% 가중치
        
        # 3. 도구 사용 빈도 기반 위험도
        tool_factor = self.compact_patterns['tool_usage_impact_factor']
        tool_risk = min((tool_usage_count * tool_factor) / 50, 1.0)  # 50회 기준
        risk_factors.append(('tool_usage', tool_risk, 0.15))  # 15% 가중치
        
        # 4. 최근 compact 패턴 기반 위험도
        pattern_risk = self._analyze_compact_pattern()
        risk_factors.append(('pattern', pattern_risk, 0.15))  # 15% 가중치
        
        # 가중 평균 계산
        total_risk = sum(risk * weight for _, risk, weight in risk_factors)
        
        # Claude Code 환경에서는 위험도 조정
        if self.claude_detector.is_claude_code_host:
            # Claude Code에서는 더 보수적으로 평가
            total_risk = min(total_risk * 1.1, 1.0)
        
        return round(total_risk, 3)
    
    def _analyze_compact_pattern(self) -> float:
        """최근 compact 패턴 분석하여 위험도 반환"""
        if len(self.compact_events) < 2:
            return 0.0
        
        now = datetime.now()
        recent_events = [
            event for event in self.compact_events[-5:]  # 최근 5개 이벤트
            if (now - event.timestamp).total_seconds() < 3600  # 1시간 이내
        ]
        
        if len(recent_events) < 2:
            return 0.0
        
        # 최근 이벤트 간격 분석
        intervals = []
        for i in range(1, len(recent_events)):
            interval = (recent_events[i].timestamp - recent_events[i-1].timestamp).total_seconds()
            intervals.append(interval)
        
        if intervals:
            avg_interval = sum(intervals) / len(intervals)
            # 짧은 간격일수록 높은 위험도
            if avg_interval < 600:  # 10분 미만
                return 0.8
            elif avg_interval < 1800:  # 30분 미만
                return 0.5
            else:
                return 0.2
        
        return 0.0
    
    def _update_risk_assessment(self) -> None:
        """현재 위험도 상태 업데이트"""
        if not self.metrics_history:
            return
        
        latest_metrics = self.metrics_history[-1]
        
        self.current_risk_score = self.calculate_risk(
            content_length=latest_metrics.content_length,
            session_history=latest_metrics.session_history_count,
            tool_usage_count=latest_metrics.tool_usage_count,
            conversation_turns=latest_metrics.conversation_turns
        )
        
        # 위험도 레벨 결정
        if self.current_risk_score >= 0.9:
            self.current_risk_level = CompactRiskLevel.CRITICAL
        elif self.current_risk_score >= 0.7:
            self.current_risk_level = CompactRiskLevel.HIGH
        elif self.current_risk_score >= 0.5:
            self.current_risk_level = CompactRiskLevel.MEDIUM
        elif self.current_risk_score >= 0.3:
            self.current_risk_level = CompactRiskLevel.LOW
        else:
            self.current_risk_level = CompactRiskLevel.SAFE
        
        self.last_risk_update = datetime.now()
    
    def detect_auto_compact_event(self) -> Optional[CompactEvent]:
        """Auto-compact 발생 감지"""
        if len(self.context_length_history) < 2:
            return None
        
        # 최근 두 기록 비교
        current_time, current_length = self.context_length_history[-1]
        previous_time, previous_length = self.context_length_history[-2]
        
        # 급격한 길이 감소 패턴 감지 (50% 이상 감소)
        if current_length < previous_length * 0.5 and previous_length > 1000:
            
            compact_event = CompactEvent(
                timestamp=current_time,
                detected_method="length_drop_pattern",
                context_length_before=previous_length,
                context_length_after=current_length,
                affected_items=0  # 나중에 백업 시스템에서 설정
            )
            
            self.compact_events.append(compact_event)
            
            # 패턴 업데이트
            self._update_compact_patterns(compact_event)
            
            return compact_event
        
        return None
    
    def _update_compact_patterns(self, event: CompactEvent) -> None:
        """Compact 패턴 업데이트"""
        # 평균 compact 간격 계산
        if len(self.compact_events) >= 2:
            recent_events = self.compact_events[-5:]  # 최근 5개
            intervals = []
            
            for i in range(1, len(recent_events)):
                interval = (recent_events[i].timestamp - recent_events[i-1].timestamp).total_seconds()
                intervals.append(interval)
            
            if intervals:
                self.compact_patterns['average_compact_interval'] = sum(intervals) / len(intervals)
        
        # 임계점 조정
        lengths_before_compact = [e.context_length_before for e in self.compact_events[-10:]]
        if lengths_before_compact:
            avg_threshold = sum(lengths_before_compact) / len(lengths_before_compact)
            # 기존 임계점과 새 관찰값의 가중 평균
            current_threshold = self.compact_patterns['typical_context_length_threshold']
            self.compact_patterns['typical_context_length_threshold'] = int(
                current_threshold * 0.7 + avg_threshold * 0.3
            )
    
    def get_current_risk_status(self) -> Dict[str, Any]:
        """현재 위험도 상태 반환"""
        return {
            'risk_score': self.current_risk_score,
            'risk_level': self.current_risk_level.value,
            'last_update': self.last_risk_update.isoformat(),
            'recommendations': self._get_risk_recommendations()
        }
    
    def _get_risk_recommendations(self) -> List[str]:
        """위험도에 따른 권장사항"""
        recommendations = []
        
        if self.current_risk_level == CompactRiskLevel.CRITICAL:
            recommendations.extend([
                "[ALERT] 즉시 중요한 컨텍스트를 백업하세요",
                "[ALERT] 진행 중인 작업을 안전한 지점에서 저장하세요", 
                "[ALERT] Auto-compact가 임박했습니다"
            ])
        elif self.current_risk_level == CompactRiskLevel.HIGH:
            recommendations.extend([
                "⚠️ 중요한 정보를 메모리에 저장하세요",
                "⚠️ 복잡한 작업은 단계별로 진행하세요"
            ])
        elif self.current_risk_level == CompactRiskLevel.MEDIUM:
            recommendations.extend([
                "📋 정기적으로 진행상황을 기록하세요",
                "📋 핵심 정보는 별도 보관하세요"
            ])
        elif self.current_risk_level == CompactRiskLevel.LOW:
            recommendations.append("✅ 안전한 상태입니다")
        else:  # SAFE
            recommendations.append("🟢 매우 안전한 상태입니다")
        
        return recommendations
    
    def get_statistics(self) -> Dict[str, Any]:
        """모니터링 통계"""
        stats = {
            'monitoring_duration': len(self.context_length_history),
            'total_compact_events': len(self.compact_events),
            'current_risk': self.get_current_risk_status(),
            'patterns': self.compact_patterns.copy()
        }
        
        if self.metrics_history:
            latest = self.metrics_history[-1]
            stats['latest_metrics'] = {
                'content_length': latest.content_length,
                'session_history': latest.session_history_count,
                'tool_usage': latest.tool_usage_count,
                'conversation_turns': latest.conversation_turns
            }
        
        if self.compact_events:
            recent_events = [e for e in self.compact_events 
                           if (datetime.now() - e.timestamp).days < 1]
            stats['recent_events_24h'] = len(recent_events)
        
        return stats
    
    def save_monitoring_data(self, file_path: str) -> bool:
        """모니터링 데이터 저장"""
        try:
            data = {
                'timestamp': datetime.now().isoformat(),
                'monitoring_config': {
                    'threshold': self.threshold,
                    'history_size': self.history_size,
                    'risk_update_interval': self.risk_update_interval
                },
                'current_state': {
                    'risk_score': self.current_risk_score,
                    'risk_level': self.current_risk_level.value,
                    'last_update': self.last_risk_update.isoformat()
                },
                'compact_events': [
                    {
                        'timestamp': event.timestamp.isoformat(),
                        'detected_method': event.detected_method,
                        'context_length_before': event.context_length_before,
                        'context_length_after': event.context_length_after,
                        'event_id': event.event_id
                    }
                    for event in self.compact_events
                ],
                'patterns': self.compact_patterns,
                'statistics': self.get_statistics()
            }
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            return True
            
        except Exception as e:
            print(f"모니터링 데이터 저장 실패: {e}")
            return False
    
    def load_monitoring_data(self, file_path: str) -> bool:
        """모니터링 데이터 로드"""
        try:
            if not os.path.exists(file_path):
                return False
            
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 기본 설정 복원
            config = data.get('monitoring_config', {})
            self.threshold = config.get('threshold', self.threshold)
            
            # 상태 복원
            state = data.get('current_state', {})
            self.current_risk_score = state.get('risk_score', 0.0)
            
            # 이벤트 복원
            events_data = data.get('compact_events', [])
            self.compact_events = []
            for event_data in events_data:
                event = CompactEvent(
                    timestamp=datetime.fromisoformat(event_data['timestamp']),
                    detected_method=event_data['detected_method'],
                    context_length_before=event_data['context_length_before'],
                    context_length_after=event_data['context_length_after'],
                    event_id=event_data.get('event_id', '')
                )
                self.compact_events.append(event)
            
            # 패턴 복원
            self.compact_patterns.update(data.get('patterns', {}))
            
            return True
            
        except Exception as e:
            print(f"모니터링 데이터 로드 실패: {e}")
            return False
    
    def print_risk_report(self):
        """위험도 리포트 출력"""
        print("=" * 60)
        print("🎯 Auto-Compact Risk Assessment Report")
        print("=" * 60)
        
        status = self.get_current_risk_status()
        
        # 위험도 레벨에 따른 이모지
        level_emojis = {
            'safe': '🟢',
            'low': '🟡', 
            'medium': '🟠',
            'high': '🔴',
            'critical': '[ALERT]'
        }
        
        emoji = level_emojis.get(status['risk_level'], '❓')
        
        print(f"Current Risk: {emoji} {status['risk_level'].upper()} ({status['risk_score']:.1%})")
        print(f"Last Update: {datetime.fromisoformat(status['last_update']).strftime('%H:%M:%S')}")
        print()
        
        print("📋 Recommendations:")
        for rec in status['recommendations']:
            print(f"  {rec}")
        
        if self.compact_events:
            print(f"\n📊 Recent Events: {len(self.compact_events)} total")
            for event in self.compact_events[-3:]:  # 최근 3개
                print(f"  {event.timestamp.strftime('%m-%d %H:%M')} - "
                      f"{event.context_length_before:,} → {event.context_length_after:,}")
        
        print("=" * 60)


if __name__ == "__main__":
    # 테스트 코드
    print("🧪 AutoCompactMonitor 테스트")
    
    monitor = AutoCompactMonitor()
    
    # 테스트 메트릭 기록
    test_scenarios = [
        (5000, 10, 5, 3),    # 안전한 상태
        (25000, 50, 15, 12), # 중간 위험
        (45000, 80, 25, 20), # 높은 위험
        (60000, 120, 35, 30) # 임계 위험
    ]
    
    for i, (length, history, tools, turns) in enumerate(test_scenarios):
        print(f"\n--- 시나리오 {i+1} ---")
        monitor.record_context_metrics(length, history, tools, turns)
        
        risk = monitor.calculate_risk(length, history, tools, turns)
        print(f"컨텍스트 길이: {length:,}")
        print(f"위험도: {risk:.1%}")
        
        # Auto-compact 시뮬레이션 (마지막 시나리오)
        if i == len(test_scenarios) - 1:
            monitor.record_context_metrics(15000, history, tools, turns)  # 급감
            event = monitor.detect_auto_compact_event()
            if event:
                print(f"[ALERT] Auto-compact 감지됨: {event.event_id}")
    
    # 최종 리포트
    monitor.print_risk_report()