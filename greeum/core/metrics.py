"""
Greeum Metrics Collection System

Implements Prometheus-style metrics for anchor-based memory system.
Collects metrics specified in Architecture Reform Plan section 10.
"""

import time
import threading
from typing import Dict, Any, Optional
from collections import defaultdict, deque
from datetime import datetime, timedelta




class SearchMetrics:
    """검색 성능 메트릭스"""

    def __init__(self, timestamp=None, search_type=None, slot=None, root=None,
                 depth_used=None, hops=None, local_used=None, fallback_used=None,
                 latency_ms=None, results_count=None):
        self.timestamp = timestamp or time.time()
        self.search_type = search_type
        self.slot = slot
        self.root = root
        self.depth_used = depth_used
        self.hops = hops
        self.local_used = local_used
        self.fallback_used = fallback_used
        self.latency_ms = latency_ms
        self.results_count = results_count

        # Performance aggregates
        self.local_hit_rate = 0.0
        self.avg_hops = 0.0
        self.p95_latency = 0.0
        self.merge_undo_rate = 0.0

    def update(self, hit_rate=None, hops=None, latency=None, undo_rate=None):
        """메트릭스 업데이트"""
        if hit_rate is not None:
            self.local_hit_rate = hit_rate
        if hops is not None:
            self.avg_hops = hops
        if latency is not None:
            self.p95_latency = latency
        if undo_rate is not None:
            self.merge_undo_rate = undo_rate


class MetricsDashboard:
    """메트릭스 대시보드"""

    def __init__(self, db_manager=None):
        self.collector = MetricsCollector()
        self.search_metrics = SearchMetrics()
        self.recorded_searches = []

        # v3 Branch/DFS 시스템 연결
        if db_manager is None:
            from .database_manager import DatabaseManager
            db_manager = DatabaseManager()

        self.db_manager = db_manager
        self._connect_v3_systems()

    def _connect_v3_systems(self):
        """v3 Branch/DFS 시스템과 연결"""
        try:
            from .dfs_search import DFSSearchEngine
            from .stm_manager import STMManager
            self.dfs_engine = DFSSearchEngine(self.db_manager)
            self.stm_manager = STMManager(self.db_manager)
        except ImportError:
            # v3 시스템 없으면 기본값 사용
            self.dfs_engine = None
            self.stm_manager = None

    def get_search_metrics(self) -> SearchMetrics:
        """검색 메트릭스 반환"""
        return self.search_metrics

    def update_search_metrics(self, **kwargs):
        """검색 메트릭스 업데이트"""
        self.search_metrics.update(**kwargs)

    def record_search(self, metrics: SearchMetrics):
        """검색 메트릭스 기록"""
        self.recorded_searches.append(metrics)

        # Update aggregated metrics
        if len(self.recorded_searches) >= 10:
            # Calculate local hit rate
            local_searches = [m for m in self.recorded_searches if m.local_used]
            self.search_metrics.local_hit_rate = len(local_searches) / len(self.recorded_searches) * 100

            # Calculate average hops
            hops_list = [m.hops for m in self.recorded_searches if m.hops is not None]
            if hops_list:
                self.search_metrics.avg_hops = sum(hops_list) / len(hops_list)

            # Calculate p95 latency
            latency_list = [m.latency_ms for m in self.recorded_searches if m.latency_ms is not None]
            if latency_list:
                latency_list.sort()
                p95_index = int(0.95 * len(latency_list))
                self.search_metrics.p95_latency = latency_list[p95_index] if p95_index < len(latency_list) else latency_list[-1]

    def get_dashboard_export(self):
        """대시보드 익스포트 데이터"""
        # v3 실제 데이터 가져오기
        v3_data = self._get_v3_branch_data()

        return {
            'local_hit_rate': self.search_metrics.local_hit_rate,
            'avg_hops': self.search_metrics.avg_hops,
            'p95_latency': self.search_metrics.p95_latency,
            'total_searches': len(self.recorded_searches),
            'v3_branch_data': v3_data
        }

    def _get_v3_branch_data(self):
        """v3 Branch/DFS 시스템에서 실제 데이터 가져오기"""
        if not self.dfs_engine or not self.stm_manager:
            return {'status': 'v3_systems_not_available'}

        try:
            # DFS 검색 메트릭
            dfs_metrics = self.dfs_engine.metrics.copy()

            # Branch 헤드 정보
            branch_heads = self.stm_manager.branch_heads.copy()

            # 슬롯 사용률
            slot_usage = {}
            for slot, hysteresis in self.stm_manager.slot_hysteresis.items():
                slot_usage[slot] = hysteresis['access_count']

            return {
                'dfs_search_metrics': dfs_metrics,
                'branch_heads': branch_heads,
                'slot_utilization': slot_usage,
                'adaptive_patterns': self.dfs_engine.adaptive_patterns if hasattr(self.dfs_engine, 'adaptive_patterns') else {}
            }
        except Exception as e:
            return {'error': str(e), 'status': 'failed_to_fetch_v3_data'}

    def get_local_hit_rate(self):
        """로컬 히트율 반환"""
        if not self.recorded_searches:
            return 0.0
        local_searches = [m for m in self.recorded_searches if m.local_used]
        return len(local_searches) / len(self.recorded_searches)

    def get_avg_hops(self):
        """평균 홉 수 반환"""
        if not self.recorded_searches:
            return 0.0
        hops_list = [m.hops for m in self.recorded_searches if m.hops is not None]
        if not hops_list:
            return 0.0
        return sum(hops_list) / len(hops_list)

    def get_jump_rate(self):
        """점프율 반환 (fallback 사용률)"""
        if not self.recorded_searches:
            return 0.0
        fallback_searches = [m for m in self.recorded_searches if m.fallback_used]
        return len(fallback_searches) / len(self.recorded_searches)

    def get_p95_latency(self):
        """P95 지연시간 반환"""
        return self.search_metrics.p95_latency

    def export_metrics(self, file_path: str):
        """메트릭스를 파일로 익스포트"""
        import json
        data = {
            'dashboard': {
                'metrics': self.get_dashboard_export()
            },
            'success_indicators': self.get_success_indicators()
        }
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=2)

    def get_success_indicators(self):
        """성공 지표 반환"""
        local_hit_rate = self.get_local_hit_rate()
        avg_hops = self.get_avg_hops()
        p95_latency = self.search_metrics.p95_latency
        merge_undo_rate = self.search_metrics.merge_undo_rate

        return {
            'local_hit_rate_target': (local_hit_rate >= 0.27, local_hit_rate),
            'avg_hops_target': (avg_hops <= 8.5, avg_hops),
            'p95_latency_target': (p95_latency < 150, p95_latency),
            'merge_undo_rate_target': (merge_undo_rate <= 0.05, merge_undo_rate)
        }


class MetricsCollector:
    """
    Thread-safe metrics collector for Greeum anchor memory system.

    Collects metrics specified in Architecture Reform Plan 311-316:
    - greeum_anchors_switches_per_min
    - greeum_local_hit_rate / greeum_fallback_rate
    - greeum_avg_hops / greeum_beam_width
    - greeum_anchor_moves_total
    - greeum_edge_count / greeum_edge_growth_rate
    """

    def __init__(self):
        self._lock = threading.Lock()
        self._start_time = time.time()

        # Counter metrics
        self._anchor_moves_total = defaultdict(int)  # by slot
        self._anchor_switches_total = 0
        self._local_searches_total = 0
        self._local_hits_total = 0
        self._fallback_searches_total = 0

        # Gauge metrics
        self._current_edge_count = 0
        self._current_beam_width = 32

        # Histogram data (recent values for averages)
        self._recent_hops = deque(maxlen=100)  # Last 100 searches
        self._recent_switch_times = deque(maxlen=50)  # Last 50 switches

        # Edge growth tracking
        self._edge_count_history = []  # (timestamp, count) pairs

    def record_anchor_move(self, slot: str) -> None:
        """Record anchor movement for specified slot."""
        with self._lock:
            self._anchor_moves_total[slot] += 1
    
    def record_anchor_switch(self, from_slot: str, to_slot: str) -> None:
        """Record anchor slot switch."""
        with self._lock:
            self._anchor_switches_total += 1
            self._recent_switch_times.append(time.time())
    
    def record_local_search(self, hit: bool, hops: int) -> None:
        """Record localized search attempt."""
        with self._lock:
            self._local_searches_total += 1
            if hit:
                self._local_hits_total += 1
            self._recent_hops.append(hops)
    
    def record_fallback_search(self) -> None:
        """Record fallback to global search."""
        with self._lock:
            self._fallback_searches_total += 1
    
    def update_edge_count(self, count: int) -> None:
        """Update current edge count and track growth."""
        with self._lock:
            self._current_edge_count = count
            self._edge_count_history.append((time.time(), count))
            
            # Keep only last hour of history
            cutoff = time.time() - 3600
            self._edge_count_history = [
                (ts, cnt) for ts, cnt in self._edge_count_history if ts > cutoff
            ]
    
    def update_beam_width(self, width: int) -> None:
        """Update current beam width setting."""
        with self._lock:
            self._current_beam_width = width
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get all current metrics in Prometheus format."""
        with self._lock:
            current_time = time.time()
            elapsed_minutes = (current_time - self._start_time) / 60.0
            
            # Calculate rates
            switches_per_min = self._anchor_switches_total / elapsed_minutes if elapsed_minutes > 0 else 0
            
            # Calculate hit/fallback rates
            total_searches = self._local_searches_total + self._fallback_searches_total
            local_hit_rate = self._local_hits_total / self._local_searches_total if self._local_searches_total > 0 else 0
            fallback_rate = self._fallback_searches_total / total_searches if total_searches > 0 else 0
            
            # Calculate average hops
            avg_hops = sum(self._recent_hops) / len(self._recent_hops) if self._recent_hops else 0
            
            # Calculate edge growth rate (edges per hour)
            edge_growth_rate = 0
            if len(self._edge_count_history) > 1:
                earliest = self._edge_count_history[0]
                latest = self._edge_count_history[-1]
                time_diff_hours = (latest[0] - earliest[0]) / 3600.0
                edge_diff = latest[1] - earliest[1]
                edge_growth_rate = edge_diff / time_diff_hours if time_diff_hours > 0 else 0
            
            return {
                # Architecture Reform Plan metrics
                "greeum_anchors_switches_per_min": switches_per_min,
                "greeum_local_hit_rate": local_hit_rate,
                "greeum_fallback_rate": fallback_rate,
                "greeum_avg_hops": avg_hops,
                "greeum_beam_width": self._current_beam_width,
                "greeum_anchor_moves_total": dict(self._anchor_moves_total),
                "greeum_edge_count": self._current_edge_count,
                "greeum_edge_growth_rate": edge_growth_rate,
                
                # Additional useful metrics
                "greeum_local_searches_total": self._local_searches_total,
                "greeum_local_hits_total": self._local_hits_total,
                "greeum_fallback_searches_total": self._fallback_searches_total,
                "greeum_uptime_seconds": current_time - self._start_time,
            }
    
    def export_prometheus_format(self) -> str:
        """Export metrics in Prometheus exposition format."""
        metrics = self.get_metrics()
        lines = []
        
        # Counter metrics
        lines.append(f"# HELP greeum_anchors_switches_per_min Anchor slot switches per minute")
        lines.append(f"# TYPE greeum_anchors_switches_per_min gauge")
        lines.append(f"greeum_anchors_switches_per_min {metrics['greeum_anchors_switches_per_min']:.3f}")
        
        lines.append(f"# HELP greeum_local_hit_rate Localized search hit rate")
        lines.append(f"# TYPE greeum_local_hit_rate gauge")
        lines.append(f"greeum_local_hit_rate {metrics['greeum_local_hit_rate']:.3f}")
        
        lines.append(f"# HELP greeum_fallback_rate Fallback search rate")
        lines.append(f"# TYPE greeum_fallback_rate gauge")
        lines.append(f"greeum_fallback_rate {metrics['greeum_fallback_rate']:.3f}")
        
        lines.append(f"# HELP greeum_avg_hops Average hops in localized search")
        lines.append(f"# TYPE greeum_avg_hops gauge")
        lines.append(f"greeum_avg_hops {metrics['greeum_avg_hops']:.3f}")
        
        lines.append(f"# HELP greeum_beam_width Current beam search width")
        lines.append(f"# TYPE greeum_beam_width gauge")
        lines.append(f"greeum_beam_width {metrics['greeum_beam_width']}")
        
        lines.append(f"# HELP greeum_edge_count Current graph edge count")
        lines.append(f"# TYPE greeum_edge_count gauge")
        lines.append(f"greeum_edge_count {metrics['greeum_edge_count']}")
        
        lines.append(f"# HELP greeum_edge_growth_rate Edge growth rate per hour")
        lines.append(f"# TYPE greeum_edge_growth_rate gauge")
        lines.append(f"greeum_edge_growth_rate {metrics['greeum_edge_growth_rate']:.3f}")
        
        # Per-slot anchor moves
        for slot, count in metrics['greeum_anchor_moves_total'].items():
            lines.append(f"greeum_anchor_moves_total{{slot=\"{slot}\"}} {count}")
        
        return "\\n".join(lines)


# Global metrics collector instance
_metrics_collector: Optional[MetricsCollector] = None


def get_metrics_collector() -> MetricsCollector:
    """Get global metrics collector instance (thread-safe singleton)."""
    global _metrics_collector
    if _metrics_collector is None:
        _metrics_collector = MetricsCollector()
    return _metrics_collector


def record_anchor_move(slot: str) -> None:
    """Convenience function to record anchor movement."""
    get_metrics_collector().record_anchor_move(slot)


def record_anchor_switch(from_slot: str, to_slot: str) -> None:
    """Convenience function to record anchor switch."""
    get_metrics_collector().record_anchor_switch(from_slot, to_slot)


def record_local_search(hit: bool, hops: int) -> None:
    """Convenience function to record localized search."""
    get_metrics_collector().record_local_search(hit, hops)


def record_fallback_search() -> None:
    """Convenience function to record fallback search."""
    get_metrics_collector().record_fallback_search()


def update_edge_count(count: int) -> None:
    """Convenience function to update edge count."""
    get_metrics_collector().update_edge_count(count)


def update_beam_width(width: int) -> None:
    """Convenience function to update beam width."""
    get_metrics_collector().update_beam_width(width)


def get_all_metrics() -> Dict[str, Any]:
    """Get all current metrics."""
    return get_metrics_collector().get_metrics()


def get_edge_count() -> int:
    """Get current edge count."""
    return get_metrics_collector()._current_edge_count


def export_prometheus() -> str:
    """Export metrics in Prometheus format."""
    return get_metrics_collector().export_prometheus_format()
