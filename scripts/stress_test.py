#!/usr/bin/env python3
"""
Greeum Performance Stress Test
Tests throughput and latency of v5.0 components

Usage:
    .venv_test/bin/python scripts/stress_test.py [--quick] [--full]
"""

import os
import sys
import time
import random
import argparse
import tempfile
import statistics
from typing import List, Dict, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed

# Add parent to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from greeum.core import (
    BlockManager,
    DatabaseManager,
    BM25Index,
    HybridScorer,
    InsightFilter,
)
from greeum.text_utils import generate_simple_embedding


class StressTestResult:
    def __init__(self, name: str):
        self.name = name
        self.latencies: List[float] = []
        self.errors = 0
        self.start_time = 0.0
        self.end_time = 0.0

    def record(self, latency_ms: float):
        self.latencies.append(latency_ms)

    def record_error(self):
        self.errors += 1

    @property
    def total_time_ms(self) -> float:
        return (self.end_time - self.start_time) * 1000

    @property
    def throughput(self) -> float:
        if self.total_time_ms == 0:
            return 0
        return len(self.latencies) / (self.total_time_ms / 1000)

    @property
    def avg_latency(self) -> float:
        return statistics.mean(self.latencies) if self.latencies else 0

    @property
    def p50(self) -> float:
        return statistics.median(self.latencies) if self.latencies else 0

    @property
    def p95(self) -> float:
        if len(self.latencies) < 2:
            return self.avg_latency
        sorted_lat = sorted(self.latencies)
        idx = int(len(sorted_lat) * 0.95)
        return sorted_lat[idx]

    @property
    def p99(self) -> float:
        if len(self.latencies) < 2:
            return self.avg_latency
        sorted_lat = sorted(self.latencies)
        idx = int(len(sorted_lat) * 0.99)
        return sorted_lat[idx]

    def print_summary(self):
        print(f"\n{'='*60}")
        print(f"📊 {self.name}")
        print(f"{'='*60}")
        print(f"  Total operations: {len(self.latencies)}")
        print(f"  Errors: {self.errors}")
        print(f"  Total time: {self.total_time_ms:.1f}ms")
        print(f"  Throughput: {self.throughput:.1f} ops/sec")
        print(f"  Latency (avg): {self.avg_latency:.2f}ms")
        print(f"  Latency (p50): {self.p50:.2f}ms")
        print(f"  Latency (p95): {self.p95:.2f}ms")
        print(f"  Latency (p99): {self.p99:.2f}ms")


# Sample data for testing
SAMPLE_CONTENTS = [
    "FastAPI 서버에서 비동기 처리 구현 완료",
    "React 컴포넌트 성능 최적화 작업 중",
    "PostgreSQL 인덱스 튜닝으로 쿼리 속도 3배 향상",
    "Docker 컨테이너 메모리 누수 원인 발견",
    "Kubernetes 배포 파이프라인 구축 완료",
    "Redis 캐시 만료 정책 수정",
    "GraphQL 스키마 설계 리팩토링",
    "WebSocket 연결 안정성 개선",
    "CI/CD 파이프라인 테스트 자동화",
    "마이크로서비스 간 통신 패턴 정의",
    "API 응답 시간 모니터링 대시보드 구축",
    "데이터베이스 마이그레이션 스크립트 작성",
    "인증 토큰 갱신 로직 버그 수정",
    "로그 수집 시스템 ElasticSearch 연동",
    "성능 프로파일링 결과 분석 완료",
]

SAMPLE_KEYWORDS = [
    ["서버", "비동기", "FastAPI"],
    ["React", "성능", "최적화"],
    ["PostgreSQL", "인덱스", "쿼리"],
    ["Docker", "메모리", "누수"],
    ["Kubernetes", "배포", "파이프라인"],
    ["Redis", "캐시", "만료"],
    ["GraphQL", "스키마", "설계"],
    ["WebSocket", "연결", "안정성"],
    ["CI/CD", "테스트", "자동화"],
    ["마이크로서비스", "통신", "패턴"],
    ["API", "모니터링", "대시보드"],
    ["데이터베이스", "마이그레이션", "스크립트"],
    ["인증", "토큰", "버그"],
    ["로그", "ElasticSearch", "연동"],
    ["성능", "프로파일링", "분석"],
]

SAMPLE_QUERIES = [
    "서버 성능 최적화",
    "데이터베이스 쿼리",
    "버그 수정 작업",
    "API 구현",
    "캐시 정책",
    "배포 파이프라인",
    "인증 시스템",
    "모니터링",
]


def setup_test_env() -> Tuple[str, BlockManager, BM25Index]:
    """Setup temporary test environment"""
    temp_dir = tempfile.mkdtemp(prefix="greeum_stress_")
    db_path = os.path.join(temp_dir, "test.db")

    db_manager = DatabaseManager(connection_string=db_path)
    block_manager = BlockManager(db_manager=db_manager)
    bm25_index = BM25Index()

    return temp_dir, block_manager, bm25_index


def test_write_throughput(block_manager: BlockManager, count: int) -> StressTestResult:
    """Test memory write throughput"""
    result = StressTestResult("Write Throughput")
    result.start_time = time.time()

    for i in range(count):
        idx = i % len(SAMPLE_CONTENTS)
        content = SAMPLE_CONTENTS[idx] + f" #{i}"
        keywords = SAMPLE_KEYWORDS[idx]
        embedding = generate_simple_embedding(content)

        start = time.time()
        try:
            block_manager.add_block(
                context=content,
                keywords=keywords,
                tags=["test", f"batch{i//100}"],
                embedding=embedding,
                importance=random.uniform(0.3, 0.9)
            )
            result.record((time.time() - start) * 1000)
        except Exception as e:
            result.record_error()
            if result.errors <= 3:
                print(f"  Write error: {e}")

    result.end_time = time.time()
    return result


def test_bm25_indexing(bm25_index: BM25Index, count: int) -> StressTestResult:
    """Test BM25 index building speed"""
    result = StressTestResult("BM25 Indexing")
    result.start_time = time.time()

    for i in range(count):
        idx = i % len(SAMPLE_KEYWORDS)
        keywords = SAMPLE_KEYWORDS[idx] + [f"item{i}"]
        doc_id = str(i)

        start = time.time()
        try:
            bm25_index.add_document(doc_id, keywords)
            result.record((time.time() - start) * 1000)
        except Exception as e:
            result.record_error()

    result.end_time = time.time()
    return result


def test_bm25_search(bm25_index: BM25Index, count: int) -> StressTestResult:
    """Test BM25 search speed"""
    result = StressTestResult("BM25 Search")
    result.start_time = time.time()

    for _ in range(count):
        query_keywords = random.choice(SAMPLE_KEYWORDS)
        start = time.time()
        try:
            scores = bm25_index.search(query_keywords, top_k=10)
            result.record((time.time() - start) * 1000)
        except Exception as e:
            result.record_error()

    result.end_time = time.time()
    return result


def test_insight_filter(count: int) -> StressTestResult:
    """Test InsightFilter classification speed"""
    result = StressTestResult("InsightFilter")
    filter_inst = InsightFilter()

    test_contents = SAMPLE_CONTENTS + [
        "오늘 날씨 좋다",
        "점심 뭐 먹지",
        "네 알겠습니다",
        "음 그렇군요",
    ]

    result.start_time = time.time()

    for _ in range(count):
        content = random.choice(test_contents)
        start = time.time()
        try:
            filter_result = filter_inst.filter(content)
            result.record((time.time() - start) * 1000)
        except Exception as e:
            result.record_error()

    result.end_time = time.time()
    return result


def test_concurrent_search(bm25_index: BM25Index, workers: int, count_per_worker: int) -> StressTestResult:
    """Test concurrent search performance"""
    result = StressTestResult(f"Concurrent Search ({workers} workers)")

    def worker_task(worker_id: int) -> List[float]:
        latencies = []
        for _ in range(count_per_worker):
            query_keywords = random.choice(SAMPLE_KEYWORDS)
            start = time.time()
            try:
                bm25_index.search(query_keywords, top_k=10)
                latencies.append((time.time() - start) * 1000)
            except:
                pass
        return latencies

    result.start_time = time.time()

    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = [executor.submit(worker_task, i) for i in range(workers)]
        for future in as_completed(futures):
            try:
                latencies = future.result()
                for lat in latencies:
                    result.record(lat)
            except Exception as e:
                result.record_error()

    result.end_time = time.time()
    return result


def test_hybrid_scorer(bm25_index: BM25Index, count: int) -> StressTestResult:
    """Test HybridScorer fusion performance"""
    result = StressTestResult("HybridScorer")
    scorer = HybridScorer(bm25_index=bm25_index, vector_weight=0.7, bm25_weight=0.3)

    result.start_time = time.time()

    for _ in range(count):
        # Test single document scoring
        vector_similarity = random.uniform(0.1, 0.9)
        query_keywords = random.choice(SAMPLE_KEYWORDS)
        doc_keywords = random.choice(SAMPLE_KEYWORDS)

        start = time.time()
        try:
            hybrid = scorer.score(vector_similarity, query_keywords, doc_keywords)
            result.record((time.time() - start) * 1000)
        except Exception as e:
            result.record_error()
            if result.errors <= 3:
                print(f"  Hybrid error: {e}")

    result.end_time = time.time()
    return result


def test_embedding_generation(count: int) -> StressTestResult:
    """Test embedding generation speed"""
    result = StressTestResult("Embedding Generation")
    result.start_time = time.time()

    for i in range(count):
        content = random.choice(SAMPLE_CONTENTS) + f" #{i}"
        start = time.time()
        try:
            embedding = generate_simple_embedding(content)
            result.record((time.time() - start) * 1000)
        except Exception as e:
            result.record_error()

    result.end_time = time.time()
    return result


def run_stress_tests(quick: bool = False, full: bool = False):
    """Run all stress tests"""
    print("🚀 Greeum Performance Stress Test")
    print("=" * 60)

    # Determine scale
    if quick:
        write_count = 100
        search_count = 500
        index_count = 500
        filter_count = 1000
        embed_count = 200
        concurrent_workers = 4
        concurrent_per_worker = 100
    elif full:
        write_count = 5000
        search_count = 5000
        index_count = 5000
        filter_count = 10000
        embed_count = 1000
        concurrent_workers = 8
        concurrent_per_worker = 500
    else:  # default
        write_count = 500
        search_count = 1000
        index_count = 1000
        filter_count = 2000
        embed_count = 500
        concurrent_workers = 4
        concurrent_per_worker = 250

    print(f"\nMode: {'quick' if quick else 'full' if full else 'default'}")
    print(f"Write ops: {write_count}")
    print(f"Search ops: {search_count}")
    print(f"Index ops: {index_count}")
    print(f"Filter ops: {filter_count}")
    print(f"Embed ops: {embed_count}")

    # Setup
    print("\n📦 Setting up test environment...")
    temp_dir, block_manager, bm25_index = setup_test_env()
    print(f"  Temp dir: {temp_dir}")

    results: List[StressTestResult] = []

    try:
        # Test 1: Embedding generation (needed for writes)
        print(f"\n[1/7] Testing embedding generation ({embed_count} ops)...")
        results.append(test_embedding_generation(embed_count))

        # Test 2: Write throughput
        print(f"\n[2/7] Testing write throughput ({write_count} ops)...")
        results.append(test_write_throughput(block_manager, write_count))

        # Test 3: BM25 indexing
        print(f"\n[3/7] Testing BM25 indexing ({index_count} docs)...")
        results.append(test_bm25_indexing(bm25_index, index_count))

        # Test 4: BM25 search
        print(f"\n[4/7] Testing BM25 search ({search_count} queries)...")
        results.append(test_bm25_search(bm25_index, search_count))

        # Test 5: InsightFilter
        print(f"\n[5/7] Testing InsightFilter ({filter_count} classifications)...")
        results.append(test_insight_filter(filter_count))

        # Test 6: HybridScorer
        print(f"\n[6/7] Testing HybridScorer ({search_count} fusions)...")
        results.append(test_hybrid_scorer(bm25_index, search_count))

        # Test 7: Concurrent search
        print(f"\n[7/7] Testing concurrent search ({concurrent_workers}x{concurrent_per_worker})...")
        results.append(test_concurrent_search(
            bm25_index,
            concurrent_workers,
            concurrent_per_worker
        ))

    finally:
        # Cleanup
        import shutil
        shutil.rmtree(temp_dir, ignore_errors=True)

    # Print results
    print("\n" + "=" * 60)
    print("📈 RESULTS SUMMARY")
    print("=" * 60)

    for r in results:
        r.print_summary()

    # Overall summary
    print("\n" + "=" * 60)
    print("🏁 OVERALL")
    print("=" * 60)
    total_ops = sum(len(r.latencies) for r in results)
    total_time = sum(r.total_time_ms for r in results)
    total_errors = sum(r.errors for r in results)

    print(f"  Total operations: {total_ops}")
    print(f"  Total time: {total_time/1000:.2f}s")
    print(f"  Total errors: {total_errors}")
    if total_time > 0:
        print(f"  Overall throughput: {total_ops / (total_time/1000):.1f} ops/sec")

    # Grade
    avg_throughput = sum(r.throughput for r in results) / len(results) if results else 0
    if avg_throughput > 10000:
        grade = "A+ (Excellent)"
    elif avg_throughput > 5000:
        grade = "A (Very Good)"
    elif avg_throughput > 2000:
        grade = "B (Good)"
    elif avg_throughput > 1000:
        grade = "C (Acceptable)"
    else:
        grade = "D (Needs Optimization)"

    print(f"\n  Performance Grade: {grade}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Greeum Stress Test")
    parser.add_argument("--quick", action="store_true", help="Quick test (fewer operations)")
    parser.add_argument("--full", action="store_true", help="Full test (more operations)")
    args = parser.parse_args()

    run_stress_tests(quick=args.quick, full=args.full)
