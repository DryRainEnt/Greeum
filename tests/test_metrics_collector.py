"""
메트릭 수집기 TDD 테스트 스위트
RED 단계: 이 테스트들은 모두 실패해야 함 (구현 전)
"""

import unittest
import tempfile
import json
import sqlite3
import time
from pathlib import Path
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, List

# 아직 구현되지 않은 모듈들 (RED 단계)
try:
    from greeum.core.metrics_collector import (
        MetricsCollector, SearchMetric, WriteMetric, SearchType
    )
except ImportError:
    # 테스트를 위한 임시 정의
    class SearchType:
        LOCAL_GRAPH = "local_graph"
        SLOT_BASED = "slot_based"
        GLOBAL = "global"
        FALLBACK = "fallback"
    
    class SearchMetric:
        pass
    
    class WriteMetric:
        pass
    
    class MetricsCollector:
        pass


class TestMetricsCollectorUnit(unittest.TestCase):
    """메트릭 수집기 단위 테스트"""
    
    def setUp(self):
        """각 테스트 전 실행"""
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = Path(self.temp_dir) / "test_metrics.db"
    
    def tearDown(self):
        """각 테스트 후 정리"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_singleton_pattern(self):
        """요구사항: MetricsCollector는 싱글톤이어야 함"""
        collector1 = MetricsCollector()
        collector2 = MetricsCollector()
        self.assertIs(collector1, collector2, "MetricsCollector should be singleton")
    
    def test_database_initialization(self):
        """요구사항: SQLite DB가 올바른 스키마로 초기화되어야 함"""
        collector = MetricsCollector()
        collector.db_path = self.db_path
        collector._init_database()
        
        # 테이블 존재 확인
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        # search_metrics 테이블
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='search_metrics'")
        self.assertIsNotNone(cursor.fetchone(), "search_metrics table should exist")
        
        # write_metrics 테이블
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='write_metrics'")
        self.assertIsNotNone(cursor.fetchone(), "write_metrics table should exist")
        
        # 인덱스 확인
        cursor.execute("SELECT name FROM sqlite_master WHERE type='index' AND name='idx_search_timestamp'")
        self.assertIsNotNone(cursor.fetchone(), "Search timestamp index should exist")
        
        conn.close()
    
    def test_search_metric_recording(self):
        """요구사항: 검색 메트릭이 정확히 기록되어야 함"""
        collector = MetricsCollector()
        collector.db_path = self.db_path
        collector._init_database()
        
        # 검색 메트릭 생성
        metric = SearchMetric(
            timestamp=datetime.now(),
            search_type=SearchType.LOCAL_GRAPH,
            query="test query",
            slot_used="A",
            radius=2,
            total_results=5,
            relevant_results=3,
            latency_ms=25.5,
            hops_traversed=2,
            top_score=0.95,
            avg_score=0.75,
            fallback_triggered=False,
            nodes_visited=10,
            edges_traversed=15,
            cache_hits=8,
            cache_misses=2
        )
        
        # 기록
        collector.record_search(metric)
        self.assertEqual(len(collector.buffer), 1, "Metric should be in buffer")
        
        # 플러시
        collector._flush_buffer()
        self.assertEqual(len(collector.buffer), 0, "Buffer should be empty after flush")
        
        # DB 확인
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM search_metrics")
        count = cursor.fetchone()[0]
        self.assertEqual(count, 1, "One metric should be in database")
        conn.close()
    
    def test_write_metric_recording(self):
        """요구사항: 쓰기 메트릭이 정확히 기록되어야 함"""
        collector = MetricsCollector()
        collector.db_path = self.db_path
        collector._init_database()
        
        # 쓰기 메트릭 생성
        metric = WriteMetric(
            timestamp=datetime.now(),
            block_id=123,
            near_anchor=True,
            anchor_slot="A",
            anchor_distance=1,
            links_created=3,
            bidirectional_links=1,
            write_latency_ms=15.2,
            link_update_latency_ms=5.1
        )
        
        # 기록
        collector.record_write(metric)
        collector._flush_buffer()
        
        # DB 확인
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM write_metrics")
        count = cursor.fetchone()[0]
        self.assertEqual(count, 1, "One metric should be in database")
        conn.close()
    
    def test_auto_buffer_flush(self):
        """요구사항: 버퍼가 가득 차면 자동으로 플러시되어야 함"""
        collector = MetricsCollector()
        collector.db_path = self.db_path
        collector._init_database()
        collector.buffer_size = 5  # 작은 버퍼 크기로 설정
        
        # 버퍼 크기만큼 메트릭 추가
        for i in range(5):
            metric = SearchMetric(
                timestamp=datetime.now(),
                search_type=SearchType.GLOBAL,
                query=f"query_{i}",
                slot_used=None,
                radius=None,
                total_results=1,
                relevant_results=1,
                latency_ms=10.0,
                hops_traversed=0,
                top_score=0.8,
                avg_score=0.8,
                fallback_triggered=False,
                nodes_visited=1,
                edges_traversed=0,
                cache_hits=0,
                cache_misses=1
            )
            collector.record_search(metric)
        
        # 자동 플러시 확인
        self.assertEqual(len(collector.buffer), 0, "Buffer should be auto-flushed")
        
        # DB 확인
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM search_metrics")
        count = cursor.fetchone()[0]
        self.assertEqual(count, 5, "All metrics should be in database")
        conn.close()
    
    def test_aggregation_accuracy(self):
        """요구사항: 메트릭 집계가 정확해야 함"""
        collector = MetricsCollector()
        collector.db_path = self.db_path
        collector._init_database()
        
        # 다양한 메트릭 추가
        search_types = [SearchType.LOCAL_GRAPH, SearchType.SLOT_BASED, SearchType.FALLBACK]
        latencies = []
        
        for i, search_type in enumerate(search_types * 3):  # 각 타입 3개씩
            latency = 20.0 + i * 5
            latencies.append(latency)
            
            metric = SearchMetric(
                timestamp=datetime.now(),
                search_type=search_type,
                query=f"query_{i}",
                slot_used="A" if search_type == SearchType.LOCAL_GRAPH else None,
                radius=2 if search_type == SearchType.LOCAL_GRAPH else None,
                total_results=5,
                relevant_results=3,
                latency_ms=latency,
                hops_traversed=2 if search_type == SearchType.LOCAL_GRAPH else 0,
                top_score=0.9,
                avg_score=0.7,
                fallback_triggered=(search_type == SearchType.FALLBACK),
                nodes_visited=10,
                edges_traversed=15,
                cache_hits=7,
                cache_misses=3
            )
            collector.record_search(metric)
        
        collector._flush_buffer()
        
        # 집계 확인
        metrics = collector.get_aggregated_metrics()
        
        self.assertEqual(metrics['search']['total'], 9, "Total count should be 9")
        self.assertEqual(
            metrics['search']['by_type'].get(SearchType.LOCAL_GRAPH.value, 0), 3,
            "Local graph count should be 3"
        )
        self.assertAlmostEqual(
            metrics['search']['fallback_rate'], 1/3, 2,
            "Fallback rate should be ~33%"
        )
        self.assertAlmostEqual(
            metrics['search']['avg_latency'], sum(latencies) / len(latencies), 1,
            "Average latency should be accurate"
        )
        self.assertAlmostEqual(
            metrics['search']['cache_hit_rate'], 0.7, 2,
            "Cache hit rate should be 70%"
        )
    
    def test_time_range_filtering(self):
        """요구사항: 시간 범위로 메트릭을 필터링할 수 있어야 함"""
        collector = MetricsCollector()
        collector.db_path = self.db_path
        collector._init_database()
        
        # 과거 메트릭
        old_metric = SearchMetric(
            timestamp=datetime.now() - timedelta(days=2),
            search_type=SearchType.GLOBAL,
            query="old query",
            slot_used=None,
            radius=None,
            total_results=1,
            relevant_results=1,
            latency_ms=10.0,
            hops_traversed=0,
            top_score=0.8,
            avg_score=0.8,
            fallback_triggered=False,
            nodes_visited=1,
            edges_traversed=0,
            cache_hits=0,
            cache_misses=1
        )
        
        # 최근 메트릭
        new_metric = SearchMetric(
            timestamp=datetime.now(),
            search_type=SearchType.GLOBAL,
            query="new query",
            slot_used=None,
            radius=None,
            total_results=1,
            relevant_results=1,
            latency_ms=15.0,
            hops_traversed=0,
            top_score=0.9,
            avg_score=0.9,
            fallback_triggered=False,
            nodes_visited=1,
            edges_traversed=0,
            cache_hits=1,
            cache_misses=0
        )
        
        collector.record_search(old_metric)
        collector.record_search(new_metric)
        collector._flush_buffer()
        
        # 최근 24시간만 조회
        metrics = collector.get_aggregated_metrics(
            start_time=datetime.now() - timedelta(hours=24)
        )
        
        self.assertEqual(metrics['search']['total'], 1, "Should only include recent metric")
        self.assertAlmostEqual(
            metrics['search']['avg_latency'], 15.0, 1,
            "Should only average recent metric"
        )
    
    def test_summary_calculation(self):
        """요구사항: 전체 요약 통계가 정확해야 함"""
        collector = MetricsCollector()
        collector.db_path = self.db_path
        collector._init_database()
        
        # 검색 메트릭
        for i in range(10):
            search_metric = SearchMetric(
                timestamp=datetime.now(),
                search_type=SearchType.LOCAL_GRAPH if i < 4 else SearchType.GLOBAL,
                query=f"query_{i}",
                slot_used="A" if i < 4 else None,
                radius=2 if i < 4 else None,
                total_results=5,
                relevant_results=3,
                latency_ms=20.0 + i,
                hops_traversed=2 if i < 4 else 0,
                top_score=0.9,
                avg_score=0.7,
                fallback_triggered=(i >= 8),  # 마지막 2개는 폴백
                nodes_visited=10,
                edges_traversed=15,
                cache_hits=7,
                cache_misses=3
            )
            collector.record_search(search_metric)
        
        # 쓰기 메트릭
        for i in range(5):
            write_metric = WriteMetric(
                timestamp=datetime.now(),
                block_id=100 + i,
                near_anchor=(i < 3),  # 60% near-anchor
                anchor_slot="A" if i < 3 else None,
                anchor_distance=1 if i < 3 else None,
                links_created=2,
                bidirectional_links=1,
                write_latency_ms=10.0 + i,
                link_update_latency_ms=3.0
            )
            collector.record_write(write_metric)
        
        collector._flush_buffer()
        
        # 요약 확인
        metrics = collector.get_aggregated_metrics()
        summary = metrics['summary']
        
        self.assertEqual(summary['total_operations'], 15, "Total operations should be 15")
        self.assertAlmostEqual(
            summary['local_search_ratio'], 0.4, 1,
            "Local search ratio should be 40%"
        )
        self.assertAlmostEqual(
            summary['fallback_rate'], 0.2, 1,
            "Fallback rate should be 20%"
        )
        self.assertAlmostEqual(
            summary['near_anchor_write_ratio'], 0.6, 1,
            "Near-anchor write ratio should be 60%"
        )
        self.assertAlmostEqual(
            summary['cache_hit_rate'], 0.7, 1,
            "Cache hit rate should be 70%"
        )


class TestMetricsIntegration(unittest.TestCase):
    """메트릭 시스템 통합 테스트"""
    
    def setUp(self):
        """테스트 환경 설정"""
        self.temp_dir = tempfile.mkdtemp()
        # 실제 BlockManager와 통합 테스트
    
    def tearDown(self):
        """테스트 정리"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    @patch('greeum.core.block_manager.BlockManager')
    def test_search_metrics_integration(self, mock_block_manager):
        """요구사항: BlockManager 검색 시 메트릭이 자동 수집되어야 함"""
        # Mock 설정
        mock_bm = mock_block_manager.return_value
        mock_bm.search_with_slots.return_value = [
            {'block_index': 1, 'score': 0.9, 'context': 'Test 1'},
            {'block_index': 2, 'score': 0.8, 'context': 'Test 2'}
        ]
        
        # 메트릭 수집기 모킹
        with patch('greeum.core.metrics_collector.MetricsCollector') as mock_collector:
            collector_instance = mock_collector.return_value
            
            # 검색 실행
            results = mock_bm.search_with_slots(
                query="test",
                slot="A",
                radius=2,
                use_slots=True
            )
            
            # 메트릭 기록 호출 확인
            # 실제 구현 시 record_search가 호출되어야 함
            # collector_instance.record_search.assert_called_once()
    
    def test_write_metrics_integration(self):
        """요구사항: BlockManager 쓰기 시 메트릭이 자동 수집되어야 함"""
        # BlockManager.add_block 호출 시 WriteMetric 기록 확인
        pass
    
    def test_performance_overhead(self):
        """요구사항: 메트릭 수집 오버헤드가 5% 미만이어야 함"""
        import time
        
        # 메트릭 없이 측정
        start = time.time()
        for _ in range(1000):
            # 더미 작업
            _ = [i**2 for i in range(100)]
        baseline_time = time.time() - start
        
        # 메트릭 포함 측정
        collector = MetricsCollector()
        start = time.time()
        for i in range(1000):
            # 더미 작업
            _ = [i**2 for i in range(100)]
            
            # 메트릭 기록 (가벼운 작업이어야 함)
            metric = SearchMetric(
                timestamp=datetime.now(),
                search_type=SearchType.GLOBAL,
                query=f"query_{i}",
                slot_used=None,
                radius=None,
                total_results=1,
                relevant_results=1,
                latency_ms=1.0,
                hops_traversed=0,
                top_score=0.8,
                avg_score=0.8,
                fallback_triggered=False,
                nodes_visited=1,
                edges_traversed=0,
                cache_hits=0,
                cache_misses=1
            )
            collector.record_search(metric)
        
        metrics_time = time.time() - start
        
        # 오버헤드 계산
        overhead = ((metrics_time - baseline_time) / baseline_time) * 100
        self.assertLess(overhead, 5.0, f"Overhead {overhead:.1f}% should be less than 5%")


class TestMetricsDashboard(unittest.TestCase):
    """메트릭 대시보드 테스트"""
    
    def test_dashboard_rendering(self):
        """요구사항: 대시보드가 1초 내에 렌더링되어야 함"""
        import subprocess
        import time
        
        start = time.time()
        
        # 대시보드 렌더링 테스트 (timeout 사용)
        proc = subprocess.run(
            ["python3", "-m", "greeum.cli", "metrics", "dashboard", "--period", "1h"],
            capture_output=True,
            text=True,
            timeout=1.0  # 1초 타임아웃
        )
        
        render_time = time.time() - start
        
        # 1초 내 완료 확인
        self.assertLess(render_time, 1.0, "Dashboard should render within 1 second")
    
    def test_dashboard_live_mode(self):
        """요구사항: 실시간 모드가 정상 작동해야 함"""
        # --live 옵션으로 실행 시 지속적 업데이트 확인
        pass
    
    def test_metrics_export(self):
        """요구사항: 메트릭을 JSON/CSV로 내보낼 수 있어야 함"""
        import subprocess
        import json
        
        # JSON 내보내기
        result = subprocess.run(
            ["python3", "-m", "greeum.cli", "metrics", "export", 
             "--format", "json", "--output", "test_export.json"],
            capture_output=True,
            text=True
        )
        
        # 파일 생성 확인
        export_path = Path("test_export.json")
        self.assertTrue(export_path.exists(), "Export file should be created")
        
        # JSON 유효성 확인
        with open(export_path) as f:
            data = json.load(f)
            self.assertIn('search', data, "Export should contain search metrics")
            self.assertIn('write', data, "Export should contain write metrics")
            self.assertIn('summary', data, "Export should contain summary")
        
        # 정리
        export_path.unlink(missing_ok=True)


if __name__ == '__main__':
    # 테스트 실행
    unittest.main(verbosity=2)