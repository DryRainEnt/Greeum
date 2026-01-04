#!/usr/bin/env python3
"""
Greeum Accuracy Stress Test
Tests precision and recall of v5.0 components

Usage:
    .venv_test/bin/python scripts/accuracy_test.py
"""

import os
import sys
import tempfile
import random
from typing import List, Dict, Tuple, Set
from dataclasses import dataclass

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


@dataclass
class AccuracyResult:
    name: str
    total: int
    correct: int
    false_positives: int = 0
    false_negatives: int = 0

    @property
    def accuracy(self) -> float:
        return self.correct / self.total if self.total > 0 else 0

    @property
    def precision(self) -> float:
        tp = self.correct
        fp = self.false_positives
        return tp / (tp + fp) if (tp + fp) > 0 else 0

    @property
    def recall(self) -> float:
        tp = self.correct
        fn = self.false_negatives
        return tp / (tp + fn) if (tp + fn) > 0 else 0

    @property
    def f1(self) -> float:
        p, r = self.precision, self.recall
        return 2 * p * r / (p + r) if (p + r) > 0 else 0

    def print_summary(self):
        print(f"\n{'='*60}")
        print(f"📊 {self.name}")
        print(f"{'='*60}")
        print(f"  Total: {self.total}")
        print(f"  Correct: {self.correct}")
        print(f"  Accuracy: {self.accuracy*100:.1f}%")
        if self.false_positives > 0 or self.false_negatives > 0:
            print(f"  Precision: {self.precision*100:.1f}%")
            print(f"  Recall: {self.recall*100:.1f}%")
            print(f"  F1 Score: {self.f1*100:.1f}%")


# ============================================================
# Test Data - Ground Truth
# ============================================================

# InsightFilter test cases: (content, expected_is_insight)
INSIGHT_TEST_CASES = [
    # TRUE POSITIVES - Should be detected as insights
    ("PostgreSQL 인덱스 튜닝으로 쿼리 속도 3배 향상시켰다", True),
    ("Docker 메모리 누수 원인을 찾아서 해결했다", True),
    ("React 컴포넌트에서 useMemo를 써서 리렌더링 문제를 고쳤다", True),
    ("API 타임아웃 이슈는 커넥션 풀 설정이 문제였다", True),
    ("Git rebase 대신 merge를 선택한 이유는 히스토리 보존 때문", True),
    ("Redis 캐시 TTL을 5분으로 설정했더니 히트율이 올라갔다", True),
    ("테스트 커버리지 80% 달성하려면 edge case 추가 필요", True),
    ("이 버그는 async/await 누락이 원인이었다", True),
    ("배포 실패 원인: 환경변수 미설정", True),
    ("성능 프로파일링 결과 DB 쿼리가 병목이었다", True),
    ("JWT 토큰 갱신 로직에서 레이스 컨디션 발견", True),
    ("로드밸런서 설정 변경으로 지연시간 50% 감소", True),
    ("Fixed the authentication bug by adding proper error handling", True),
    ("Discovered that the memory leak was caused by unclosed connections", True),
    ("Decided to use PostgreSQL instead of MySQL for better JSON support", True),
    ("The solution was to add an index on the user_id column", True),
    ("Learned that React hooks must be called at the top level", True),
    ("주의: 이 API는 rate limit이 있으니 캐싱 필수", True),
    ("중요한 교훈: 프로덕션에서 DEBUG 모드 끄기", True),
    ("webpack 설정에서 tree shaking 활성화하니 번들 크기 30% 감소", True),

    # TRUE NEGATIVES - Should NOT be detected as insights
    ("네", False),
    ("알겠습니다", False),
    ("음", False),
    ("그렇군요", False),
    ("오케이", False),
    ("네 맞아요", False),
    ("안녕하세요", False),
    ("감사합니다", False),
    ("좋아요", False),
    ("ㅋㅋㅋ", False),
    ("ㅎㅎ", False),
    ("?", False),
    ("ok", False),
    ("yes", False),
    ("thanks", False),
    ("hello", False),
    ("sure", False),
    ("got it", False),
    ("hmm", False),
    ("I see", False),
    ("오늘 날씨 좋다", False),
    ("점심 뭐 먹지", False),
    ("커피 마시러 가자", False),
    ("회의 시간이야", False),
    ("잠깐만요", False),
]

# BM25 Search test cases: (query_keywords, expected_doc_ids in top-3)
# We'll build a corpus and test retrieval
BM25_CORPUS = [
    {"id": "doc1", "keywords": ["PostgreSQL", "인덱스", "쿼리", "튜닝", "성능"]},
    {"id": "doc2", "keywords": ["React", "컴포넌트", "렌더링", "최적화", "useMemo"]},
    {"id": "doc3", "keywords": ["Docker", "컨테이너", "메모리", "누수", "디버깅"]},
    {"id": "doc4", "keywords": ["Redis", "캐시", "TTL", "설정", "히트율"]},
    {"id": "doc5", "keywords": ["API", "타임아웃", "커넥션", "풀", "설정"]},
    {"id": "doc6", "keywords": ["Git", "rebase", "merge", "브랜치", "히스토리"]},
    {"id": "doc7", "keywords": ["테스트", "커버리지", "유닛", "통합", "edge"]},
    {"id": "doc8", "keywords": ["JWT", "토큰", "인증", "갱신", "보안"]},
    {"id": "doc9", "keywords": ["Kubernetes", "배포", "파드", "서비스", "스케일링"]},
    {"id": "doc10", "keywords": ["webpack", "번들", "tree", "shaking", "최적화"]},
]

BM25_QUERIES = [
    (["PostgreSQL", "쿼리", "성능"], {"doc1"}),  # Should find doc1
    (["React", "렌더링"], {"doc2"}),  # Should find doc2
    (["Docker", "메모리"], {"doc3"}),  # Should find doc3
    (["캐시", "Redis"], {"doc4"}),  # Should find doc4
    (["API", "타임아웃"], {"doc5"}),  # Should find doc5
    (["Git", "브랜치"], {"doc6"}),  # Should find doc6
    (["테스트", "커버리지"], {"doc7"}),  # Should find doc7
    (["JWT", "인증"], {"doc8"}),  # Should find doc8
    (["Kubernetes", "배포"], {"doc9"}),  # Should find doc9
    (["webpack", "번들"], {"doc10"}),  # Should find doc10
    (["최적화", "성능"], {"doc1", "doc2", "doc10"}),  # Multiple matches
    (["설정", "Redis"], {"doc4", "doc5"}),  # Multiple matches
]

# Hybrid scoring test: vector + BM25 should rank better than either alone
HYBRID_TEST_CASES = [
    # (vector_sim, query_kw, doc_kw, expected_high_score)
    # High vector + high BM25 = highest
    (0.9, ["PostgreSQL", "쿼리"], ["PostgreSQL", "쿼리", "튜닝"], True),
    # High vector + low BM25 = medium
    (0.9, ["React"], ["Docker", "컨테이너"], False),
    # Low vector + high BM25 = medium
    (0.3, ["Redis", "캐시"], ["Redis", "캐시", "TTL"], False),
    # Low vector + low BM25 = lowest
    (0.1, ["API"], ["webpack", "번들"], False),
]


def test_insight_filter_accuracy() -> AccuracyResult:
    """Test InsightFilter classification accuracy"""
    result = AccuracyResult("InsightFilter Accuracy", total=0, correct=0)
    filter_inst = InsightFilter()

    for content, expected in INSIGHT_TEST_CASES:
        result.total += 1
        filter_result = filter_inst.filter(content)
        predicted = filter_result.is_insight

        if predicted == expected:
            result.correct += 1
        elif predicted and not expected:
            result.false_positives += 1
        elif not predicted and expected:
            result.false_negatives += 1
            print(f"  ❌ FN: '{content[:40]}...' (expected insight)")

    return result


def test_bm25_search_accuracy() -> AccuracyResult:
    """Test BM25 search retrieval accuracy"""
    result = AccuracyResult("BM25 Search Accuracy", total=0, correct=0)

    # Build index
    bm25 = BM25Index()
    for doc in BM25_CORPUS:
        bm25.add_document(doc["id"], doc["keywords"])

    for query_keywords, expected_ids in BM25_QUERIES:
        result.total += 1
        search_results = bm25.search(query_keywords, top_k=3)
        found_ids = {doc_id for doc_id, _ in search_results}

        # Check if any expected doc is in top-3
        if found_ids & expected_ids:
            result.correct += 1
        else:
            result.false_negatives += 1
            print(f"  ❌ Miss: query={query_keywords}, expected={expected_ids}, got={found_ids}")

    return result


def test_bm25_ranking_accuracy() -> AccuracyResult:
    """Test BM25 ranking correctness (relevant docs should rank higher)"""
    result = AccuracyResult("BM25 Ranking Accuracy", total=0, correct=0)

    # Build index
    bm25 = BM25Index()
    for doc in BM25_CORPUS:
        bm25.add_document(doc["id"], doc["keywords"])

    for query_keywords, expected_ids in BM25_QUERIES:
        result.total += 1
        search_results = bm25.search(query_keywords, top_k=10)

        if not search_results:
            result.false_negatives += 1
            continue

        # Check if top result is in expected
        top_doc_id = search_results[0][0]
        if top_doc_id in expected_ids:
            result.correct += 1
        else:
            # Check if expected doc exists but ranked lower
            found_ranks = {doc_id: rank for rank, (doc_id, _) in enumerate(search_results)}
            for exp_id in expected_ids:
                if exp_id in found_ranks:
                    print(f"  ⚠️ Rank: query={query_keywords}, expected {exp_id} at rank {found_ranks[exp_id]+1}")
            result.false_negatives += 1

    return result


def test_hybrid_scorer_accuracy() -> AccuracyResult:
    """Test HybridScorer fusion correctness"""
    result = AccuracyResult("HybridScorer Accuracy", total=0, correct=0)

    # Build BM25 index for scorer
    bm25 = BM25Index()
    for doc in BM25_CORPUS:
        bm25.add_document(doc["id"], doc["keywords"])

    scorer = HybridScorer(bm25_index=bm25, vector_weight=0.5, bm25_weight=0.5)

    scores = []
    for vec_sim, query_kw, doc_kw, _ in HYBRID_TEST_CASES:
        hybrid_score = scorer.score(vec_sim, query_kw, doc_kw)
        scores.append(hybrid_score)

    # Test 1: High vec + high BM25 should be highest
    result.total += 1
    if scores[0] > scores[1] and scores[0] > scores[2] and scores[0] > scores[3]:
        result.correct += 1
    else:
        print(f"  ❌ High+High not highest: scores={scores}")

    # Test 2: Low vec + low BM25 should be lowest
    result.total += 1
    if scores[3] < scores[0] and scores[3] < scores[1] and scores[3] < scores[2]:
        result.correct += 1
    else:
        print(f"  ❌ Low+Low not lowest: scores={scores}")

    # Test 3: Mixing should give medium scores
    result.total += 1
    avg_mixed = (scores[1] + scores[2]) / 2
    if scores[0] > avg_mixed > scores[3]:
        result.correct += 1
    else:
        print(f"  ❌ Mixed not in middle: high={scores[0]}, mixed_avg={avg_mixed}, low={scores[3]}")

    return result


def test_insight_filter_edge_cases() -> AccuracyResult:
    """Test InsightFilter on edge cases"""
    result = AccuracyResult("InsightFilter Edge Cases", total=0, correct=0)
    filter_inst = InsightFilter()

    edge_cases = [
        # Short but valuable
        ("버그 수정함", True),
        ("fixed bug", True),
        # Long but not valuable
        ("오늘 하루 종일 회의만 했는데 정말 피곤하네요 커피 마시러 가야겠어요", False),
        # Mixed language
        ("React에서 useMemo로 performance 개선했음", True),
        # Technical terms without insight
        ("Docker Redis Kubernetes PostgreSQL", False),
        # Question (usually not insight)
        ("이거 왜 안 되지?", False),
        # Code-like content
        ("def fix_bug(): pass", False),
        # Numbered insight
        ("1. 캐시 TTL 5분으로 설정 2. 히트율 90% 달성", True),
    ]

    for content, expected in edge_cases:
        result.total += 1
        filter_result = filter_inst.filter(content)
        predicted = filter_result.is_insight

        if predicted == expected:
            result.correct += 1
        else:
            marker = "FP" if predicted else "FN"
            print(f"  ❌ {marker}: '{content[:40]}...'")
            if predicted:
                result.false_positives += 1
            else:
                result.false_negatives += 1

    return result


def test_bm25_partial_match() -> AccuracyResult:
    """Test BM25 with partial keyword matches"""
    result = AccuracyResult("BM25 Partial Match", total=0, correct=0)

    bm25 = BM25Index()
    for doc in BM25_CORPUS:
        bm25.add_document(doc["id"], doc["keywords"])

    partial_queries = [
        # Single keyword should still find relevant docs
        (["PostgreSQL"], {"doc1"}),
        (["Docker"], {"doc3"}),
        (["캐시"], {"doc4"}),
        # Typo-like (different but related)
        (["데이터베이스", "쿼리"], {"doc1"}),  # Related to PostgreSQL
    ]

    for query_keywords, expected_ids in partial_queries:
        result.total += 1
        search_results = bm25.search(query_keywords, top_k=5)
        found_ids = {doc_id for doc_id, _ in search_results}

        if found_ids & expected_ids:
            result.correct += 1
        else:
            # Partial match might not always work
            pass

    return result


def run_accuracy_tests():
    """Run all accuracy tests"""
    print("🎯 Greeum Accuracy Stress Test")
    print("=" * 60)

    results: List[AccuracyResult] = []

    # Test 1: InsightFilter accuracy
    print("\n[1/6] Testing InsightFilter classification...")
    results.append(test_insight_filter_accuracy())

    # Test 2: InsightFilter edge cases
    print("\n[2/6] Testing InsightFilter edge cases...")
    results.append(test_insight_filter_edge_cases())

    # Test 3: BM25 search accuracy
    print("\n[3/6] Testing BM25 search retrieval...")
    results.append(test_bm25_search_accuracy())

    # Test 4: BM25 ranking accuracy
    print("\n[4/6] Testing BM25 ranking correctness...")
    results.append(test_bm25_ranking_accuracy())

    # Test 5: BM25 partial match
    print("\n[5/6] Testing BM25 partial match...")
    results.append(test_bm25_partial_match())

    # Test 6: HybridScorer accuracy
    print("\n[6/6] Testing HybridScorer fusion...")
    results.append(test_hybrid_scorer_accuracy())

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

    total_tests = sum(r.total for r in results)
    total_correct = sum(r.correct for r in results)
    overall_accuracy = total_correct / total_tests if total_tests > 0 else 0

    print(f"  Total tests: {total_tests}")
    print(f"  Total correct: {total_correct}")
    print(f"  Overall accuracy: {overall_accuracy*100:.1f}%")

    # Grade
    if overall_accuracy >= 0.95:
        grade = "A+ (Excellent)"
    elif overall_accuracy >= 0.90:
        grade = "A (Very Good)"
    elif overall_accuracy >= 0.80:
        grade = "B (Good)"
    elif overall_accuracy >= 0.70:
        grade = "C (Acceptable)"
    else:
        grade = "D (Needs Improvement)"

    print(f"\n  Accuracy Grade: {grade}")

    # Detailed breakdown
    print("\n" + "-" * 60)
    print("📋 DETAILED BREAKDOWN")
    print("-" * 60)
    for r in results:
        status = "✅" if r.accuracy >= 0.8 else "⚠️" if r.accuracy >= 0.6 else "❌"
        print(f"  {status} {r.name}: {r.accuracy*100:.0f}% ({r.correct}/{r.total})")


if __name__ == "__main__":
    run_accuracy_tests()
