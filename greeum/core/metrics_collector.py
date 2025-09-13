"""
메트릭 수집 및 집계 시스템
Greeum의 성능과 사용 패턴을 추적하는 관측가능성 시스템
"""

from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
import json
import sqlite3
import threading
import time
import logging

logger = logging.getLogger(__name__)


class SearchType(Enum):
    """검색 유형 분류"""
    LOCAL_GRAPH = "local_graph"    # 앵커 기반 로컬 검색
    SLOT_BASED = "slot_based"      # 슬롯 기반 검색
    GLOBAL = "global"               # 전역 검색
    FALLBACK = "fallback"           # 폴백 검색


@dataclass
class SearchMetric:
    """단일 검색 작업 메트릭"""
    timestamp: datetime
    search_type: SearchType
    query: str
    slot_used: Optional[str] = None
    radius: Optional[int] = None
    
    # 성능 지표
    total_results: int = 0
    relevant_results: int = 0  # 임계값 이상 스코어
    latency_ms: float = 0.0
    hops_traversed: int = 0
    
    # 결과 품질
    top_score: float = 0.0
    avg_score: float = 0.0
    fallback_triggered: bool = False
    
    # 네트워크 활용
    nodes_visited: int = 0
    edges_traversed: int = 0
    cache_hits: int = 0
    cache_misses: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        data = asdict(self)
        data['timestamp'] = self.timestamp.timestamp()
        data['search_type'] = self.search_type.value if isinstance(self.search_type, SearchType) else self.search_type
        return data


@dataclass
class WriteMetric:
    """블록 쓰기 작업 메트릭"""
    timestamp: datetime
    block_id: int
    near_anchor: bool = False
    anchor_slot: Optional[str] = None
    anchor_distance: Optional[int] = None
    
    # 링크 형성
    links_created: int = 0
    bidirectional_links: int = 0
    
    # 성능
    write_latency_ms: float = 0.0
    link_update_latency_ms: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        data = asdict(self)
        data['timestamp'] = self.timestamp.timestamp()
        return data


class MetricsCollector:
    """중앙 메트릭 수집기 (Singleton)"""
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        """싱글톤 인스턴스 생성"""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """초기화 (한 번만 실행)"""
        if not hasattr(self, 'initialized'):
            self.db_path = Path("data/metrics.db")
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
            self._init_database()
            self.buffer: List[Dict] = []
            self.buffer_size = 100
            self.buffer_lock = threading.Lock()
            self.initialized = True
            logger.info(f"MetricsCollector initialized with DB at {self.db_path}")
    
    def _init_database(self):
        """메트릭 저장용 SQLite DB 초기화"""
        conn = sqlite3.connect(str(self.db_path))
        try:
            # search_metrics 테이블
            conn.execute("""
                CREATE TABLE IF NOT EXISTS search_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp REAL NOT NULL,
                    search_type TEXT NOT NULL,
                    query TEXT,
                    slot_used TEXT,
                    radius INTEGER,
                    total_results INTEGER DEFAULT 0,
                    relevant_results INTEGER DEFAULT 0,
                    latency_ms REAL DEFAULT 0,
                    hops_traversed INTEGER DEFAULT 0,
                    top_score REAL DEFAULT 0,
                    avg_score REAL DEFAULT 0,
                    fallback_triggered INTEGER DEFAULT 0,
                    nodes_visited INTEGER DEFAULT 0,
                    edges_traversed INTEGER DEFAULT 0,
                    cache_hits INTEGER DEFAULT 0,
                    cache_misses INTEGER DEFAULT 0
                )
            """)
            
            # write_metrics 테이블
            conn.execute("""
                CREATE TABLE IF NOT EXISTS write_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp REAL NOT NULL,
                    block_id INTEGER NOT NULL,
                    near_anchor INTEGER DEFAULT 0,
                    anchor_slot TEXT,
                    anchor_distance INTEGER,
                    links_created INTEGER DEFAULT 0,
                    bidirectional_links INTEGER DEFAULT 0,
                    write_latency_ms REAL DEFAULT 0,
                    link_update_latency_ms REAL DEFAULT 0
                )
            """)
            
            # 인덱스 생성
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_search_timestamp 
                ON search_metrics(timestamp)
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_write_timestamp 
                ON write_metrics(timestamp)
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_search_type 
                ON search_metrics(search_type)
            """)
            
            conn.commit()
            logger.debug("Metrics database initialized successfully")
        finally:
            conn.close()
    
    def record_search(self, metric: SearchMetric):
        """검색 메트릭 기록"""
        with self.buffer_lock:
            self.buffer.append({
                'type': 'search',
                'data': metric.to_dict()
            })
            
            if len(self.buffer) >= self.buffer_size:
                self._flush_buffer()
    
    def record_write(self, metric: WriteMetric):
        """쓰기 메트릭 기록"""
        with self.buffer_lock:
            self.buffer.append({
                'type': 'write',
                'data': metric.to_dict()
            })
            
            if len(self.buffer) >= self.buffer_size:
                self._flush_buffer()
    
    def _flush_buffer(self):
        """버퍼를 DB에 플러시"""
        if not self.buffer:
            return
        
        conn = sqlite3.connect(str(self.db_path))
        try:
            cursor = conn.cursor()
            
            for item in self.buffer:
                if item['type'] == 'search':
                    self._insert_search_metric(cursor, item['data'])
                elif item['type'] == 'write':
                    self._insert_write_metric(cursor, item['data'])
            
            conn.commit()
            logger.debug(f"Flushed {len(self.buffer)} metrics to database")
            self.buffer.clear()
        except Exception as e:
            logger.error(f"Failed to flush metrics: {e}")
        finally:
            conn.close()
    
    def _insert_search_metric(self, cursor, data: Dict):
        """검색 메트릭 DB 삽입"""
        cursor.execute("""
            INSERT INTO search_metrics (
                timestamp, search_type, query, slot_used, radius,
                total_results, relevant_results, latency_ms, hops_traversed,
                top_score, avg_score, fallback_triggered,
                nodes_visited, edges_traversed, cache_hits, cache_misses
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            data['timestamp'], data['search_type'], data['query'],
            data['slot_used'], data['radius'],
            data['total_results'], data['relevant_results'],
            data['latency_ms'], data['hops_traversed'],
            data['top_score'], data['avg_score'],
            1 if data['fallback_triggered'] else 0,
            data['nodes_visited'], data['edges_traversed'],
            data['cache_hits'], data['cache_misses']
        ))
    
    def _insert_write_metric(self, cursor, data: Dict):
        """쓰기 메트릭 DB 삽입"""
        cursor.execute("""
            INSERT INTO write_metrics (
                timestamp, block_id, near_anchor, anchor_slot, anchor_distance,
                links_created, bidirectional_links, write_latency_ms, link_update_latency_ms
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            data['timestamp'], data['block_id'],
            1 if data['near_anchor'] else 0,
            data['anchor_slot'], data['anchor_distance'],
            data['links_created'], data['bidirectional_links'],
            data['write_latency_ms'], data['link_update_latency_ms']
        ))
    
    def get_aggregated_metrics(self, 
                              start_time: Optional[datetime] = None,
                              end_time: Optional[datetime] = None) -> Dict:
        """집계된 메트릭 조회"""
        if not start_time:
            start_time = datetime.now() - timedelta(hours=24)
        if not end_time:
            end_time = datetime.now()
        
        # 버퍼 플러시
        with self.buffer_lock:
            if self.buffer:
                self._flush_buffer()
        
        conn = sqlite3.connect(str(self.db_path))
        try:
            # 검색 메트릭 집계
            search_stats = self._aggregate_search_metrics(conn, start_time, end_time)
            
            # 쓰기 메트릭 집계
            write_stats = self._aggregate_write_metrics(conn, start_time, end_time)
            
            return {
                'period': {
                    'start': start_time.isoformat(),
                    'end': end_time.isoformat()
                },
                'search': search_stats,
                'write': write_stats,
                'summary': self._calculate_summary(search_stats, write_stats)
            }
        finally:
            conn.close()
    
    def _aggregate_search_metrics(self, conn: sqlite3.Connection, 
                                  start_time: datetime, end_time: datetime) -> Dict:
        """검색 메트릭 집계"""
        cursor = conn.cursor()
        
        # 시간 범위 설정
        start_ts = start_time.timestamp()
        end_ts = end_time.timestamp()
        
        # 전체 검색 수
        cursor.execute("""
            SELECT COUNT(*) FROM search_metrics 
            WHERE timestamp >= ? AND timestamp <= ?
        """, (start_ts, end_ts))
        total = cursor.fetchone()[0]
        
        # 검색 타입별 집계
        cursor.execute("""
            SELECT search_type, COUNT(*) FROM search_metrics 
            WHERE timestamp >= ? AND timestamp <= ?
            GROUP BY search_type
        """, (start_ts, end_ts))
        by_type = dict(cursor.fetchall())
        
        # 폴백 비율
        cursor.execute("""
            SELECT COUNT(*) FROM search_metrics 
            WHERE timestamp >= ? AND timestamp <= ? AND fallback_triggered = 1
        """, (start_ts, end_ts))
        fallback_count = cursor.fetchone()[0]
        fallback_rate = fallback_count / total if total > 0 else 0
        
        # 평균 지표
        cursor.execute("""
            SELECT 
                AVG(latency_ms),
                AVG(hops_traversed),
                AVG(total_results),
                AVG(top_score)
            FROM search_metrics 
            WHERE timestamp >= ? AND timestamp <= ?
        """, (start_ts, end_ts))
        avg_metrics = cursor.fetchone()
        
        # 캐시 적중률
        cursor.execute("""
            SELECT SUM(cache_hits), SUM(cache_misses) 
            FROM search_metrics 
            WHERE timestamp >= ? AND timestamp <= ?
        """, (start_ts, end_ts))
        cache_stats = cursor.fetchone()
        total_cache_access = (cache_stats[0] or 0) + (cache_stats[1] or 0)
        cache_hit_rate = (cache_stats[0] or 0) / total_cache_access if total_cache_access > 0 else 0
        
        # 로컬 검색 비율
        local_count = by_type.get('local_graph', 0)
        local_ratio = local_count / total if total > 0 else 0
        
        return {
            'total': total,
            'by_type': by_type,
            'fallback_rate': fallback_rate,
            'avg_latency': avg_metrics[0] or 0,
            'avg_hops': avg_metrics[1] or 0,
            'avg_results': avg_metrics[2] or 0,
            'avg_top_score': avg_metrics[3] or 0,
            'cache_hit_rate': cache_hit_rate,
            'local_ratio': local_ratio
        }
    
    def _aggregate_write_metrics(self, conn: sqlite3.Connection,
                                 start_time: datetime, end_time: datetime) -> Dict:
        """쓰기 메트릭 집계"""
        cursor = conn.cursor()
        
        start_ts = start_time.timestamp()
        end_ts = end_time.timestamp()
        
        # 전체 쓰기 수
        cursor.execute("""
            SELECT COUNT(*) FROM write_metrics 
            WHERE timestamp >= ? AND timestamp <= ?
        """, (start_ts, end_ts))
        total_writes = cursor.fetchone()[0]
        
        # Near-anchor 쓰기 비율
        cursor.execute("""
            SELECT COUNT(*) FROM write_metrics 
            WHERE timestamp >= ? AND timestamp <= ? AND near_anchor = 1
        """, (start_ts, end_ts))
        near_anchor_count = cursor.fetchone()[0]
        near_anchor_ratio = near_anchor_count / total_writes if total_writes > 0 else 0
        
        # 평균 지표
        cursor.execute("""
            SELECT 
                AVG(links_created),
                AVG(write_latency_ms),
                AVG(link_update_latency_ms)
            FROM write_metrics 
            WHERE timestamp >= ? AND timestamp <= ?
        """, (start_ts, end_ts))
        avg_metrics = cursor.fetchone()
        
        return {
            'total_writes': total_writes,
            'near_anchor_ratio': near_anchor_ratio,
            'avg_links': avg_metrics[0] or 0,
            'avg_latency': avg_metrics[1] or 0,
            'avg_link_update_latency': avg_metrics[2] or 0
        }
    
    def _calculate_summary(self, search_stats: Dict, write_stats: Dict) -> Dict:
        """전체 요약 계산"""
        total_operations = search_stats.get('total', 0) + write_stats.get('total_writes', 0)
        
        return {
            'total_operations': total_operations,
            'local_search_ratio': search_stats.get('local_ratio', 0),
            'fallback_rate': search_stats.get('fallback_rate', 0),
            'avg_search_latency_ms': search_stats.get('avg_latency', 0),
            'avg_hops': search_stats.get('avg_hops', 0),
            'cache_hit_rate': search_stats.get('cache_hit_rate', 0),
            'near_anchor_write_ratio': write_stats.get('near_anchor_ratio', 0),
            'avg_links_per_block': write_stats.get('avg_links', 0)
        }
    
    def flush(self):
        """수동으로 버퍼 플러시"""
        with self.buffer_lock:
            if self.buffer:
                self._flush_buffer()
    
    def reset(self):
        """메트릭 초기화 (테스트용)"""
        conn = sqlite3.connect(str(self.db_path))
        try:
            conn.execute("DELETE FROM search_metrics")
            conn.execute("DELETE FROM write_metrics")
            conn.commit()
            self.buffer.clear()
            logger.info("Metrics reset completed")
        finally:
            conn.close()