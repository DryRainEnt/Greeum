"""
Metrics Dashboard for Branch/DFS Performance Monitoring
Tracks local_hit_rate, avg_hops, jump_rate, and merge statistics
"""

import time
import json
from typing import Dict, List, Optional, Tuple
from collections import deque, defaultdict
from dataclasses import dataclass, field, asdict
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


@dataclass
class SearchMetrics:
    """Metrics for a single search operation"""
    timestamp: float
    search_type: str  # 'local', 'jump', 'global'
    slot: Optional[str]
    root: Optional[str]
    depth_used: int
    hops: int
    local_used: bool
    fallback_used: bool
    latency_ms: float
    results_count: int


@dataclass
class BranchStats:
    """Statistics for a single branch"""
    root: str
    size: int
    depth: int
    heads: Dict[str, str]
    last_updated: float
    access_count: int = 0
    local_hit_count: int = 0


@dataclass
class MergeStats:
    """Statistics for merge operations"""
    suggested: int = 0
    accepted: int = 0
    undone: int = 0
    last_merge: Optional[float] = None
    avg_score: float = 0.0


class MetricsDashboard:
    """Real-time metrics collection and analysis"""
    
    def __init__(self, window_size: int = 100):
        """
        Initialize metrics dashboard
        
        Args:
            window_size: Number of recent operations to track
        """
        # Search metrics tracking
        self.search_history = deque(maxlen=window_size)
        self.search_by_type = defaultdict(list)
        
        # Branch statistics
        self.branch_stats: Dict[str, BranchStats] = {}
        
        # Merge statistics
        self.merge_stats = MergeStats()
        
        # Performance metrics
        self.latency_history = deque(maxlen=window_size)
        self.hop_history = deque(maxlen=window_size)
        
        # Time-based aggregation
        self.hourly_stats = defaultdict(lambda: {
            'searches': 0,
            'local_hits': 0,
            'jumps': 0,
            'avg_latency': 0,
            'avg_hops': 0
        })
        
        # Start time
        self.start_time = time.time()
        
    def record_search(self, metrics: SearchMetrics):
        """Record a search operation"""
        self.search_history.append(metrics)
        self.search_by_type[metrics.search_type].append(metrics)
        
        # Update latency and hop history
        self.latency_history.append(metrics.latency_ms)
        self.hop_history.append(metrics.hops)
        
        # Update hourly stats
        hour_key = datetime.fromtimestamp(metrics.timestamp).strftime('%Y%m%d_%H')
        hour_stats = self.hourly_stats[hour_key]
        hour_stats['searches'] += 1
        
        if metrics.local_used and not metrics.fallback_used:
            hour_stats['local_hits'] += 1
            
        if metrics.search_type == 'jump':
            hour_stats['jumps'] += 1
            
        # Update moving averages
        n = hour_stats['searches']
        hour_stats['avg_latency'] = (
            (hour_stats['avg_latency'] * (n - 1) + metrics.latency_ms) / n
        )
        hour_stats['avg_hops'] = (
            (hour_stats['avg_hops'] * (n - 1) + metrics.hops) / n
        )
        
        # Update branch stats if available
        if metrics.root and metrics.root in self.branch_stats:
            branch = self.branch_stats[metrics.root]
            branch.access_count += 1
            if metrics.local_used and not metrics.fallback_used:
                branch.local_hit_count += 1
                
    def update_branch_stats(self, root: str, size: int, depth: int, 
                           heads: Dict[str, str]):
        """Update branch statistics"""
        if root not in self.branch_stats:
            self.branch_stats[root] = BranchStats(
                root=root,
                size=size,
                depth=depth,
                heads=heads,
                last_updated=time.time()
            )
        else:
            branch = self.branch_stats[root]
            branch.size = size
            branch.depth = depth
            branch.heads = heads
            branch.last_updated = time.time()
            
    def record_merge(self, suggested: bool, accepted: bool, undone: bool = False):
        """Record merge operation"""
        if suggested:
            self.merge_stats.suggested += 1
        if accepted:
            self.merge_stats.accepted += 1
            self.merge_stats.last_merge = time.time()
        if undone:
            self.merge_stats.undone += 1
            
    def get_local_hit_rate(self) -> float:
        """Calculate local hit rate from recent searches"""
        if not self.search_history:
            return 0.0
            
        local_hits = sum(
            1 for m in self.search_history 
            if m.local_used and not m.fallback_used
        )
        return local_hits / len(self.search_history)
        
    def get_avg_hops(self) -> float:
        """Calculate average hops from recent searches"""
        if not self.hop_history:
            return 0.0
        return sum(self.hop_history) / len(self.hop_history)
        
    def get_jump_rate(self) -> float:
        """Calculate jump rate from recent searches"""
        if not self.search_history:
            return 0.0
            
        jumps = sum(1 for m in self.search_history if m.search_type == 'jump')
        return jumps / len(self.search_history)
        
    def get_p95_latency(self) -> float:
        """Calculate 95th percentile latency"""
        if not self.latency_history:
            return 0.0
            
        sorted_latencies = sorted(self.latency_history)
        index = int(len(sorted_latencies) * 0.95)
        return sorted_latencies[index] if index < len(sorted_latencies) else sorted_latencies[-1]
        
    def get_merge_undo_rate(self) -> float:
        """Calculate merge undo rate"""
        if self.merge_stats.accepted == 0:
            return 0.0
        return self.merge_stats.undone / self.merge_stats.accepted
        
    def get_dashboard_data(self) -> Dict:
        """Get comprehensive dashboard data"""
        uptime = time.time() - self.start_time
        
        return {
            'uptime_seconds': uptime,
            'metrics': {
                'local_hit_rate': f"{self.get_local_hit_rate():.1%}",
                'avg_hops': f"{self.get_avg_hops():.2f}",
                'jump_rate': f"{self.get_jump_rate():.1%}",
                'p95_latency_ms': f"{self.get_p95_latency():.1f}",
            },
            'search_stats': {
                'total': len(self.search_history),
                'by_type': {
                    'local': len(self.search_by_type['local']),
                    'jump': len(self.search_by_type['jump']),
                    'global': len(self.search_by_type['global'])
                }
            },
            'branch_stats': {
                'total_branches': len(self.branch_stats),
                'avg_depth': sum(b.depth for b in self.branch_stats.values()) / len(self.branch_stats) if self.branch_stats else 0,
                'avg_size': sum(b.size for b in self.branch_stats.values()) / len(self.branch_stats) if self.branch_stats else 0,
            },
            'merge_stats': {
                'suggested': self.merge_stats.suggested,
                'accepted': self.merge_stats.accepted,
                'undone': self.merge_stats.undone,
                'undo_rate': f"{self.get_merge_undo_rate():.1%}"
            }
        }
        
    def get_success_indicators(self) -> Dict[str, Tuple[bool, str]]:
        """Check if success metrics are met"""
        indicators = {}
        
        # Target: local_hit_rate +10pp (from baseline ~17% to 27%+)
        local_hit = self.get_local_hit_rate()
        indicators['local_hit_rate'] = (
            local_hit >= 0.27,
            f"{local_hit:.1%} (target: ≥27%)"
        )
        
        # Target: avg_hops ≥15% reduction (from baseline)
        avg_hops = self.get_avg_hops()
        # Assuming baseline was ~10 hops
        indicators['avg_hops'] = (
            avg_hops <= 8.5,
            f"{avg_hops:.1f} (target: ≤8.5)"
        )
        
        # Target: p95 latency < 150ms
        p95 = self.get_p95_latency()
        indicators['p95_latency'] = (
            p95 < 150,
            f"{p95:.1f}ms (target: <150ms)"
        )
        
        # Target: merge undo rate ≤5%
        undo_rate = self.get_merge_undo_rate()
        indicators['merge_undo_rate'] = (
            undo_rate <= 0.05,
            f"{undo_rate:.1%} (target: ≤5%)"
        )
        
        return indicators
        
    def export_metrics(self, filepath: str):
        """Export metrics to JSON file"""
        data = {
            'timestamp': datetime.now().isoformat(),
            'dashboard': self.get_dashboard_data(),
            'success_indicators': {
                k: {'passed': v[0], 'value': v[1]} 
                for k, v in self.get_success_indicators().items()
            },
            'hourly_stats': dict(self.hourly_stats),
            'branch_details': [asdict(b) for b in self.branch_stats.values()]
        }
        
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
            
        logger.info(f"Metrics exported to {filepath}")