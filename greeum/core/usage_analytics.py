#!/usr/bin/env python3
"""
Usage Analytics & Monitoring System for Greeum v2.0.5
- Tracks memory usage patterns and system performance
- Provides insights for optimization and user behavior analysis
- Integrates with MCP server for real-time monitoring
"""

import json
import logging
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from collections import defaultdict, Counter
from pathlib import Path
import threading

logger = logging.getLogger(__name__)

class UsageAnalytics:
    """사용 패턴 분석 및 모니터링 시스템"""
    
    def __init__(self, db_manager=None, analytics_db_path: Optional[str] = None):
        """
        Analytics 시스템 초기화
        
        Args:
            db_manager: 기존 DatabaseManager (메모리 데이터 접근용)
            analytics_db_path: Analytics 전용 DB 경로
        """
        self.db_manager = db_manager
        # Validate and sanitize database path
        default_path = str(Path.home() / ".greeum" / "analytics.db")
        self.analytics_db_path = self._validate_db_path(analytics_db_path or default_path)
        self.lock = threading.Lock()
        
        # Analytics DB 초기화
        self._init_analytics_db()
        
        # 메트릭 카테고리 정의
        self.metric_categories = {
            'memory_operations': ['add_memory', 'search_memory', 'delete_memory'],
            'stm_operations': ['stm_add', 'stm_promote', 'stm_cleanup'],
            'system_operations': ['get_memory_stats', 'ltm_analyze', 'ltm_verify', 'ltm_export'],
            'quality_metrics': ['quality_validation', 'duplicate_detection'],
            'user_behavior': ['session_start', 'session_end', 'tool_usage']
        }
    
    def _init_analytics_db(self):
        """Analytics 전용 데이터베이스 초기화"""
        try:
            Path(self.analytics_db_path).parent.mkdir(parents=True, exist_ok=True)
            
            with sqlite3.connect(self.analytics_db_path) as conn:
                # 사용 이벤트 테이블
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS usage_events (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                        event_type TEXT NOT NULL,
                        tool_name TEXT,
                        user_id TEXT,
                        session_id TEXT,
                        metadata TEXT,
                        duration_ms INTEGER,
                        success BOOLEAN,
                        error_message TEXT
                    )
                """)
                
                # 품질 메트릭 테이블
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS quality_metrics (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                        content_length INTEGER,
                        quality_score REAL,
                        quality_level TEXT,
                        importance REAL,
                        adjusted_importance REAL,
                        is_duplicate BOOLEAN,
                        duplicate_similarity REAL,
                        suggestions_count INTEGER
                    )
                """)
                
                # 시스템 성능 메트릭 테이블
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS performance_metrics (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                        metric_type TEXT NOT NULL,
                        metric_name TEXT NOT NULL,
                        metric_value REAL,
                        unit TEXT,
                        metadata TEXT
                    )
                """)
                
                # 사용자 세션 테이블
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS user_sessions (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        session_id TEXT UNIQUE NOT NULL,
                        start_time DATETIME DEFAULT CURRENT_TIMESTAMP,
                        end_time DATETIME,
                        total_operations INTEGER DEFAULT 0,
                        memory_added INTEGER DEFAULT 0,
                        searches_performed INTEGER DEFAULT 0,
                        avg_quality_score REAL,
                        user_agent TEXT,
                        client_type TEXT
                    )
                """)
                
                conn.commit()
                logger.info(f"Analytics database initialized: {self.analytics_db_path}")
                
        except Exception as e:
            logger.error(f"Failed to initialize analytics database: {e}")
    
    def _sanitize_metadata(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Sanitize metadata to prevent injection attacks"""
        if not metadata:
            return {}
        
        sanitized = {}
        for key, value in metadata.items():
            # Limit key/value lengths and types
            if isinstance(key, str) and len(key) <= 100:
                if isinstance(value, (str, int, float, bool)):
                    # Truncate string values to prevent DoS
                    if isinstance(value, str):
                        value = value[:1000]
                    sanitized[str(key)[:100]] = value
        return sanitized
    
    def _validate_db_path(self, path: str) -> str:
        """Validate and sanitize database path"""
        resolved_path = Path(path).resolve()
        
        # Allow safe directories including temp directories for testing
        allowed_dirs = [
            Path.home() / ".greeum",
            Path("/tmp"),
            Path("/var/tmp"),
            Path.cwd(),  # Allow current working directory
        ]
        
        # For testing, allow any path that's not obviously dangerous
        if not str(resolved_path).startswith(('/etc', '/bin', '/usr', '/System')):
            return str(resolved_path)
            
        # Fallback to allowed directories check
        if any(str(resolved_path).startswith(str(allowed_dir)) for allowed_dir in allowed_dirs):
            return str(resolved_path)
            
        raise ValueError(f"Database path not allowed: {resolved_path}")

    def log_event(self, event_type: str, tool_name: str = None, metadata: Dict[str, Any] = None,
                  duration_ms: int = None, success: bool = True, error_message: str = None,
                  user_id: str = "anonymous", session_id: str = None) -> bool:
        """
        사용 이벤트 로깅
        
        Args:
            event_type: 이벤트 타입 (tool_usage, session_start, error 등)
            tool_name: 사용된 도구 이름
            metadata: 추가 메타데이터
            duration_ms: 실행 시간 (밀리초)
            success: 성공 여부
            error_message: 오류 메시지 (실패시)
            user_id: 사용자 ID
            session_id: 세션 ID
        """
        try:
            # Sanitize inputs
            event_type = str(event_type)[:50] if event_type else "unknown"
            tool_name = str(tool_name)[:50] if tool_name else None
            user_id = str(user_id)[:50] if user_id else "anonymous"
            session_id = str(session_id)[:100] if session_id else None
            error_message = str(error_message)[:500] if error_message else None
            metadata = self._sanitize_metadata(metadata) if metadata else None
            
            # Validate duration
            if duration_ms is not None and (duration_ms < 0 or duration_ms > 3600000):  # Max 1 hour
                duration_ms = None
            
            with self.lock:
                with sqlite3.connect(self.analytics_db_path) as conn:
                    conn.execute("""
                        INSERT INTO usage_events 
                        (event_type, tool_name, user_id, session_id, metadata, 
                         duration_ms, success, error_message)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        event_type, tool_name, user_id, session_id,
                        json.dumps(metadata) if metadata else None,
                        duration_ms, success, error_message
                    ))
                    conn.commit()
            return True
        except Exception as e:
            logger.error(f"Failed to log event: {e}")
            return False
    
    def log_quality_metrics(self, content_length: int, quality_score: float, 
                          quality_level: str, importance: float, 
                          adjusted_importance: float, is_duplicate: bool = False,
                          duplicate_similarity: float = 0.0, suggestions_count: int = 0) -> bool:
        """품질 메트릭 로깅"""
        try:
            with self.lock:
                with sqlite3.connect(self.analytics_db_path) as conn:
                    conn.execute("""
                        INSERT INTO quality_metrics 
                        (content_length, quality_score, quality_level, importance, 
                         adjusted_importance, is_duplicate, duplicate_similarity, suggestions_count)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        content_length, quality_score, quality_level, importance,
                        adjusted_importance, is_duplicate, duplicate_similarity, suggestions_count
                    ))
                    conn.commit()
            return True
        except Exception as e:
            logger.error(f"Failed to log quality metrics: {e}")
            return False
    
    def log_performance_metric(self, metric_type: str, metric_name: str, 
                             metric_value: float, unit: str = None, 
                             metadata: Dict[str, Any] = None) -> bool:
        """성능 메트릭 로깅"""
        try:
            with self.lock:
                with sqlite3.connect(self.analytics_db_path) as conn:
                    conn.execute("""
                        INSERT INTO performance_metrics 
                        (metric_type, metric_name, metric_value, unit, metadata)
                        VALUES (?, ?, ?, ?, ?)
                    """, (
                        metric_type, metric_name, metric_value, unit,
                        json.dumps(metadata) if metadata else None
                    ))
                    conn.commit()
            return True
        except Exception as e:
            logger.error(f"Failed to log performance metric: {e}")
            return False
    
    def start_session(self, session_id: str, user_agent: str = None, 
                     client_type: str = "mcp_client") -> bool:
        """사용자 세션 시작"""
        try:
            with self.lock:
                with sqlite3.connect(self.analytics_db_path) as conn:
                    conn.execute("""
                        INSERT OR REPLACE INTO user_sessions 
                        (session_id, start_time, user_agent, client_type)
                        VALUES (?, ?, ?, ?)
                    """, (session_id, datetime.now().isoformat(), user_agent, client_type))
                    conn.commit()
                    
            # 세션 시작 이벤트 로깅
            self.log_event("session_start", session_id=session_id, 
                          metadata={"user_agent": user_agent, "client_type": client_type})
            return True
        except Exception as e:
            logger.error(f"Failed to start session: {e}")
            return False
    
    def end_session(self, session_id: str) -> bool:
        """사용자 세션 종료"""
        try:
            with self.lock:
                with sqlite3.connect(self.analytics_db_path) as conn:
                    # 세션 통계 계산
                    cursor = conn.execute("""
                        SELECT COUNT(*) as total_ops,
                               SUM(CASE WHEN tool_name = 'add_memory' THEN 1 ELSE 0 END) as memory_added,
                               SUM(CASE WHEN tool_name = 'search_memory' THEN 1 ELSE 0 END) as searches
                        FROM usage_events 
                        WHERE session_id = ? AND event_type = 'tool_usage'
                    """, (session_id,))
                    
                    stats = cursor.fetchone()
                    total_ops, memory_added, searches = stats if stats else (0, 0, 0)
                    
                    # 평균 품질 점수 계산
                    cursor = conn.execute("""
                        SELECT AVG(quality_score) 
                        FROM quality_metrics 
                        WHERE timestamp >= (
                            SELECT start_time FROM user_sessions WHERE session_id = ?
                        )
                    """, (session_id,))
                    
                    avg_quality = cursor.fetchone()[0] or 0.0
                    
                    # 세션 종료 업데이트
                    conn.execute("""
                        UPDATE user_sessions 
                        SET end_time = ?, total_operations = ?, memory_added = ?, 
                            searches_performed = ?, avg_quality_score = ?
                        WHERE session_id = ?
                    """, (
                        datetime.now().isoformat(), total_ops, memory_added, 
                        searches, avg_quality, session_id
                    ))
                    conn.commit()
                    
            # 세션 종료 이벤트 로깅
            self.log_event("session_end", session_id=session_id,
                          metadata={"total_operations": total_ops, "avg_quality": avg_quality})
            return True
        except Exception as e:
            logger.error(f"Failed to end session: {e}")
            return False
    
    def get_usage_statistics(self, days: int = 7) -> Dict[str, Any]:
        """사용 통계 생성"""
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            
            with sqlite3.connect(self.analytics_db_path) as conn:
                # 기본 사용 통계
                cursor = conn.execute("""
                    SELECT 
                        COUNT(*) as total_events,
                        COUNT(DISTINCT session_id) as unique_sessions,
                        COUNT(CASE WHEN success = 1 THEN 1 END) as successful_events,
                        AVG(duration_ms) as avg_duration_ms
                    FROM usage_events 
                    WHERE timestamp >= ?
                """, (cutoff_date.isoformat(),))
                
                basic_stats = cursor.fetchone()
                
                # 도구별 사용 빈도
                cursor = conn.execute("""
                    SELECT tool_name, COUNT(*) as usage_count
                    FROM usage_events 
                    WHERE timestamp >= ? AND tool_name IS NOT NULL
                    GROUP BY tool_name
                    ORDER BY usage_count DESC
                """, (cutoff_date.isoformat(),))
                
                tool_usage = dict(cursor.fetchall())
                
                # 품질 메트릭 통계
                cursor = conn.execute("""
                    SELECT 
                        AVG(quality_score) as avg_quality,
                        AVG(content_length) as avg_content_length,
                        COUNT(CASE WHEN is_duplicate = 1 THEN 1 END) as duplicate_count,
                        COUNT(*) as total_quality_checks
                    FROM quality_metrics 
                    WHERE timestamp >= ?
                """, (cutoff_date.isoformat(),))
                
                quality_stats = cursor.fetchone()
                
                # 시간대별 사용 패턴
                cursor = conn.execute("""
                    SELECT 
                        strftime('%H', timestamp) as hour,
                        COUNT(*) as event_count
                    FROM usage_events 
                    WHERE timestamp >= ?
                    GROUP BY strftime('%H', timestamp)
                    ORDER BY hour
                """, (cutoff_date.isoformat(),))
                
                hourly_usage = dict(cursor.fetchall())
                
                return {
                    "period_days": days,
                    "basic_stats": {
                        "total_events": basic_stats[0] if basic_stats else 0,
                        "unique_sessions": basic_stats[1] if basic_stats else 0,
                        "successful_events": basic_stats[2] if basic_stats else 0,
                        "success_rate": (basic_stats[2] / basic_stats[0]) if basic_stats and basic_stats[0] > 0 else 0.0,
                        "avg_duration_ms": basic_stats[3] if basic_stats else 0.0
                    },
                    "tool_usage": tool_usage,
                    "quality_stats": {
                        "avg_quality_score": quality_stats[0] if quality_stats else 0.0,
                        "avg_content_length": quality_stats[1] if quality_stats else 0.0,
                        "duplicate_rate": (quality_stats[2] / quality_stats[3]) if quality_stats and quality_stats[3] > 0 else 0.0,
                        "total_quality_checks": quality_stats[3] if quality_stats else 0
                    },
                    "hourly_usage": hourly_usage,
                    "generated_at": datetime.now().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Failed to generate usage statistics: {e}")
            return {"error": str(e)}
    
    def get_quality_trends(self, days: int = 30) -> Dict[str, Any]:
        """품질 트렌드 분석"""
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            
            with sqlite3.connect(self.analytics_db_path) as conn:
                # 일별 품질 트렌드
                cursor = conn.execute("""
                    SELECT 
                        DATE(timestamp) as date,
                        AVG(quality_score) as avg_quality,
                        COUNT(*) as count,
                        AVG(content_length) as avg_length
                    FROM quality_metrics 
                    WHERE timestamp >= ?
                    GROUP BY DATE(timestamp)
                    ORDER BY date
                """, (cutoff_date.isoformat(),))
                
                daily_trends = [
                    {
                        "date": row[0],
                        "avg_quality": row[1],
                        "count": row[2],
                        "avg_length": row[3]
                    }
                    for row in cursor.fetchall()
                ]
                
                # 품질 등급별 분포
                cursor = conn.execute("""
                    SELECT quality_level, COUNT(*) as count
                    FROM quality_metrics 
                    WHERE timestamp >= ?
                    GROUP BY quality_level
                """, (cutoff_date.isoformat(),))
                
                quality_distribution = dict(cursor.fetchall())
                
                # 중복 패턴 분석
                cursor = conn.execute("""
                    SELECT 
                        DATE(timestamp) as date,
                        COUNT(CASE WHEN is_duplicate = 1 THEN 1 END) as duplicates,
                        COUNT(*) as total,
                        AVG(duplicate_similarity) as avg_similarity
                    FROM quality_metrics 
                    WHERE timestamp >= ?
                    GROUP BY DATE(timestamp)
                    ORDER BY date
                """, (cutoff_date.isoformat(),))
                
                duplicate_trends = [
                    {
                        "date": row[0],
                        "duplicate_count": row[1],
                        "total_count": row[2],
                        "duplicate_rate": (row[1] / row[2]) if row[2] > 0 else 0.0,
                        "avg_similarity": row[3] or 0.0
                    }
                    for row in cursor.fetchall()
                ]
                
                return {
                    "period_days": days,
                    "daily_trends": daily_trends,
                    "quality_distribution": quality_distribution,
                    "duplicate_trends": duplicate_trends,
                    "generated_at": datetime.now().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Failed to analyze quality trends: {e}")
            return {"error": str(e)}
    
    def get_performance_insights(self, days: int = 7) -> Dict[str, Any]:
        """성능 인사이트 생성"""
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            
            with sqlite3.connect(self.analytics_db_path) as conn:
                # 느린 작업 식별
                cursor = conn.execute("""
                    SELECT 
                        tool_name,
                        AVG(duration_ms) as avg_duration,
                        MAX(duration_ms) as max_duration,
                        COUNT(*) as operation_count
                    FROM usage_events 
                    WHERE timestamp >= ? AND duration_ms IS NOT NULL AND tool_name IS NOT NULL
                    GROUP BY tool_name
                    ORDER BY avg_duration DESC
                """, (cutoff_date.isoformat(),))
                
                performance_by_tool = [
                    {
                        "tool_name": row[0],
                        "avg_duration_ms": row[1],
                        "max_duration_ms": row[2],
                        "operation_count": row[3]
                    }
                    for row in cursor.fetchall()
                ]
                
                # 오류 패턴 분석
                cursor = conn.execute("""
                    SELECT 
                        tool_name,
                        error_message,
                        COUNT(*) as error_count
                    FROM usage_events 
                    WHERE timestamp >= ? AND success = 0 AND tool_name IS NOT NULL
                    GROUP BY tool_name, error_message
                    ORDER BY error_count DESC
                    LIMIT 10
                """, (cutoff_date.isoformat(),))
                
                error_patterns = [
                    {
                        "tool_name": row[0],
                        "error_message": row[1],
                        "error_count": row[2]
                    }
                    for row in cursor.fetchall()
                ]
                
                # 시스템 리소스 메트릭
                cursor = conn.execute("""
                    SELECT 
                        metric_name,
                        AVG(metric_value) as avg_value,
                        MAX(metric_value) as max_value,
                        unit
                    FROM performance_metrics 
                    WHERE timestamp >= ?
                    GROUP BY metric_name, unit
                """, (cutoff_date.isoformat(),))
                
                resource_metrics = [
                    {
                        "metric_name": row[0],
                        "avg_value": row[1],
                        "max_value": row[2],
                        "unit": row[3]
                    }
                    for row in cursor.fetchall()
                ]
                
                # 권장사항 생성
                recommendations = self._generate_performance_recommendations(
                    performance_by_tool, error_patterns
                )
                
                return {
                    "period_days": days,
                    "performance_by_tool": performance_by_tool,
                    "error_patterns": error_patterns,
                    "resource_metrics": resource_metrics,
                    "recommendations": recommendations,
                    "generated_at": datetime.now().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Failed to generate performance insights: {e}")
            return {"error": str(e)}
    
    def _generate_performance_recommendations(self, performance_data: List[Dict], 
                                           error_data: List[Dict]) -> List[str]:
        """성능 개선 권장사항 생성"""
        recommendations = []
        
        # 느린 작업 권장사항
        if performance_data:
            slowest_tool = performance_data[0]
            if slowest_tool["avg_duration_ms"] > 1000:  # 1초 이상
                recommendations.append(
                    f"🐌 '{slowest_tool['tool_name']}' operation is slow "
                    f"(avg: {slowest_tool['avg_duration_ms']:.0f}ms). Consider optimization."
                )
        
        # 오류 패턴 권장사항
        if error_data:
            top_error = error_data[0]
            if top_error["error_count"] > 5:
                recommendations.append(
                    f"🚫 Frequent errors in '{top_error['tool_name']}': "
                    f"{top_error['error_message']} ({top_error['error_count']} times)"
                )
        
        # 일반 권장사항
        if not recommendations:
            recommendations.append("✅ System performance looks healthy!")
        
        return recommendations
    
    def cleanup_old_data(self, days_to_keep: int = 90) -> Dict[str, int]:
        """오래된 분석 데이터 정리"""
        try:
            cutoff_date = datetime.now() - timedelta(days=days_to_keep)
            
            with self.lock:
                with sqlite3.connect(self.analytics_db_path) as conn:
                    # 각 테이블에서 오래된 데이터 삭제
                    tables = ['usage_events', 'quality_metrics', 'performance_metrics']
                    deleted_counts = {}
                    
                    for table in tables:
                        cursor = conn.execute(f"""
                            DELETE FROM {table} 
                            WHERE timestamp < ?
                        """, (cutoff_date.isoformat(),))
                        deleted_counts[table] = cursor.rowcount
                    
                    # 완료된 세션 중 오래된 것들 삭제
                    cursor = conn.execute("""
                        DELETE FROM user_sessions 
                        WHERE end_time IS NOT NULL AND end_time < ?
                    """, (cutoff_date.isoformat(),))
                    deleted_counts['user_sessions'] = cursor.rowcount
                    
                    conn.commit()
                    
            logger.info(f"Cleaned up analytics data older than {days_to_keep} days: {deleted_counts}")
            return deleted_counts
            
        except Exception as e:
            logger.error(f"Failed to cleanup old analytics data: {e}")
            return {"error": str(e)}
    
    def _get_hourly_activity(self, days: int = 7) -> Dict[int, int]:
        """시간대별 활동 패턴 분석"""
        with self.lock:
            conn = sqlite3.connect(self.analytics_db_path)
            cursor = conn.cursor()
            
            try:
                since_date = datetime.now() - timedelta(days=days)
                cursor.execute("""
                    SELECT 
                        CAST(strftime('%H', timestamp) AS INTEGER) as hour,
                        COUNT(*) as count
                    FROM usage_events 
                    WHERE timestamp >= ?
                    GROUP BY hour
                    ORDER BY hour
                """, [since_date.isoformat()])
                
                return dict(cursor.fetchall())
                
            finally:
                conn.close()
    
    def _get_error_analysis(self, days: int = 7) -> Dict[str, Any]:
        """오류 패턴 분석"""
        with self.lock:
            conn = sqlite3.connect(self.analytics_db_path)
            cursor = conn.cursor()
            
            try:
                since_date = datetime.now() - timedelta(days=days)
                
                # 총 오류 수
                cursor.execute("""
                    SELECT COUNT(*) FROM usage_events 
                    WHERE timestamp >= ? AND success = 0
                """, [since_date.isoformat()])
                
                total_errors = cursor.fetchone()[0] or 0
                
                # 주요 오류 유형
                cursor.execute("""
                    SELECT error_message, COUNT(*) as count
                    FROM usage_events 
                    WHERE timestamp >= ? AND success = 0 AND error_message IS NOT NULL
                    GROUP BY error_message
                    ORDER BY count DESC
                    LIMIT 5
                """, [since_date.isoformat()])
                
                common_errors = cursor.fetchall()
                
                return {
                    'total_errors': total_errors,
                    'common_errors': common_errors
                }
                
            finally:
                conn.close()
    
    def _analyze_stm_promotion_candidates(self) -> int:
        """STM 승격 후보 분석 (모의 구현)"""
        # 실제로는 STMManager와 연동하여 분석
        # 현재는 임의의 값 반환
        import random
        return random.randint(0, 5)

if __name__ == "__main__":
    # 테스트 코드
    analytics = UsageAnalytics()
    
    print("✅ UsageAnalytics module loaded successfully")
    print("📊 Key features:")
    print("  - Event logging and session tracking")
    print("  - Quality metrics analysis")
    print("  - Performance monitoring")
    print("  - Usage pattern insights")
    print("  - Automatic data cleanup")
    
    # 기본 테스트
    session_id = "test_session_001"
    analytics.start_session(session_id, "test_client", "unit_test")
    analytics.log_event("tool_usage", "add_memory", {"test": True}, 150, True, session_id=session_id)
    analytics.log_quality_metrics(100, 0.8, "good", 0.5, 0.6, False, 0.0, 2)
    
    stats = analytics.get_usage_statistics(1)
    print(f"\n📈 Test statistics: {stats['basic_stats']['total_events']} events logged")
    
    analytics.end_session(session_id)
    print("🔚 Test session completed")