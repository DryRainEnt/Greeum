#!/usr/bin/env python3
"""
Test script for InsightJudge - LLM-based unified insight + branch judge

Usage:
    .venv_test/bin/python scripts/test_insight_judge.py [--live]

Options:
    --live    Use live LLM server (requires llama-server running)
"""

import os
import sys
import argparse
from unittest.mock import patch, MagicMock
from typing import List, Tuple

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from greeum.core.insight_judge import InsightJudge, JudgmentResult


# Test cases: (content, expected_is_insight)
TEST_CASES = [
    # TRUE INSIGHTS
    ("PostgreSQL 인덱스 튜닝으로 쿼리 속도 3배 향상시켰다", True),
    ("Docker 메모리 누수 원인을 찾아서 해결했다", True),
    ("버그 수정함", True),
    ("fixed the authentication bug", True),
    ("React에서 useMemo로 렌더링 문제 고침", True),
    ("API 타임아웃은 커넥션 풀 설정 문제였음", True),
    ("주의: rate limit 걸려있음", True),
    ("배포 실패 원인: 환경변수 미설정", True),
    ("성능 프로파일링 결과 DB가 병목", True),

    # NOT INSIGHTS (noise)
    ("네", False),
    ("알겠습니다", False),
    ("ok", False),
    ("thanks", False),
    ("안녕하세요", False),
    ("hello", False),
    ("오늘 날씨 좋다", False),
    ("점심 뭐 먹지", False),
    ("ㅋㅋㅋ", False),
    ("음", False),
]


def mock_llm_response(content: str) -> str:
    """Generate mock LLM response based on content heuristics."""
    content_lower = content.lower()

    # Noise patterns
    noise_patterns = [
        "네", "알겠", "ok", "thanks", "안녕", "hello", "날씨", "점심",
        "ㅋㅋ", "ㅎㅎ", "음", "그렇", "커피", "good", "sure", "yes"
    ]

    is_noise = (
        len(content.strip()) < 10 or
        any(p in content_lower for p in noise_patterns)
    )

    if is_noise:
        return """INSIGHT: NO
REASON: Simple acknowledgment or casual content with no technical value
BRANCH: NONE
BRANCH_REASON: Not storing
CATEGORIES:"""
    else:
        return """INSIGHT: YES
REASON: Contains technical insight about development work
BRANCH: NEW_BRANCH
BRANCH_REASON: New technical context
CATEGORIES: problem_solving, debugging"""


def test_parsing():
    """Test response parsing logic."""
    print("\n" + "="*60)
    print("📋 Testing Response Parsing")
    print("="*60)

    judge = InsightJudge(enabled=False)  # Disabled for parsing tests

    test_responses = [
        # Standard YES response
        ("""INSIGHT: YES
REASON: Documents a bug fix
BRANCH: EXISTING:abc123
BRANCH_REASON: Related to API
CATEGORIES: problem_solving, debugging""", True, False),

        # Standard NO response
        ("""INSIGHT: NO
REASON: Simple greeting
BRANCH: NONE
BRANCH_REASON: Not storing
CATEGORIES:""", False, False),

        # NEW_BRANCH response
        ("""INSIGHT: YES
REASON: New project setup
BRANCH: NEW_BRANCH
BRANCH_REASON: New context
CATEGORIES: config, setup""", True, True),

        # Edge case: minimal response
        ("""INSIGHT: YES
BRANCH: NEW_BRANCH""", True, True),
    ]

    passed = 0
    for response, expected_insight, expected_new_branch in test_responses:
        result = judge._parse_response(response, {})

        if result.is_insight == expected_insight and result.create_new_branch == expected_new_branch:
            print(f"  ✅ Parsed correctly: insight={result.is_insight}, new_branch={result.create_new_branch}")
            passed += 1
        else:
            print(f"  ❌ Parse error: expected insight={expected_insight}, new_branch={expected_new_branch}")
            print(f"      Got: insight={result.is_insight}, new_branch={result.create_new_branch}")

    print(f"\n  Parsing tests: {passed}/{len(test_responses)} passed")
    return passed == len(test_responses)


def test_with_mock_llm():
    """Test InsightJudge with mocked LLM responses."""
    print("\n" + "="*60)
    print("🤖 Testing with Mock LLM")
    print("="*60)

    judge = InsightJudge(enabled=True)

    # Mock the LLM call
    correct = 0
    total = len(TEST_CASES)

    for content, expected in TEST_CASES:
        # Directly test parsing with mock response
        mock_response = mock_llm_response(content)
        result = judge._parse_response(mock_response, {})

        if result.is_insight == expected:
            correct += 1
            status = "✅"
        else:
            status = "❌"
            print(f"  {status} '{content[:30]}...' expected={expected}, got={result.is_insight}")

    accuracy = correct / total * 100
    print(f"\n  Mock LLM accuracy: {correct}/{total} ({accuracy:.1f}%)")

    return accuracy >= 80


def test_with_live_llm():
    """Test InsightJudge with live LLM server."""
    print("\n" + "="*60)
    print("🔴 Testing with Live LLM")
    print("="*60)

    judge = InsightJudge(enabled=True, timeout=10.0)

    if not judge.is_available():
        print("  ⚠️  LLM server not available at", judge.llm_url)
        print("  Skipping live tests. Start llama-server to run these tests.")
        return None

    print(f"  ✅ LLM server available at {judge.llm_url}")

    correct = 0
    total = len(TEST_CASES)

    for content, expected in TEST_CASES:
        result = judge.judge(content)

        if result.is_insight == expected:
            correct += 1
            status = "✅"
        else:
            status = "❌"

        print(f"  {status} '{content[:25]}...' → insight={result.is_insight} (expected={expected})")
        if result.insight_reason:
            print(f"       Reason: {result.insight_reason[:50]}...")

    accuracy = correct / total * 100
    print(f"\n  Live LLM accuracy: {correct}/{total} ({accuracy:.1f}%)")

    # Print stats
    stats = judge.get_stats()
    print(f"\n  Stats: {stats}")

    return accuracy


def test_edge_cases():
    """Test edge cases."""
    print("\n" + "="*60)
    print("🔬 Testing Edge Cases")
    print("="*60)

    judge = InsightJudge(enabled=True)

    edge_cases = [
        ("", False),  # Empty
        ("a", False),  # Too short
        ("네네네네네", False),  # Repeated acknowledgment
        ("!@#$%^&*()", False),  # Special chars only
        ("12345", False),  # Numbers only
        ("버그 수정", True),  # Short but insight
    ]

    passed = 0
    for content, expected in edge_cases:
        # Quick filter test (before LLM)
        if len(content.strip()) < 5:
            result = JudgmentResult(is_insight=False, insight_confidence=1.0, insight_reason="Too short")
        else:
            mock_response = mock_llm_response(content)
            result = judge._parse_response(mock_response, {})

        if result.is_insight == expected:
            passed += 1
            print(f"  ✅ '{content[:20]}' → {result.is_insight}")
        else:
            print(f"  ❌ '{content[:20]}' expected={expected}, got={result.is_insight}")

    print(f"\n  Edge cases: {passed}/{len(edge_cases)} passed")
    return passed == len(edge_cases)


def test_prompt_building():
    """Test prompt building with branches."""
    print("\n" + "="*60)
    print("📝 Testing Prompt Building")
    print("="*60)

    from greeum.core.insight_judge import SimilarBlock

    judge = InsightJudge(enabled=False)

    # Create mock similar blocks
    mock_blocks = {
        "branch_abc123": [
            SimilarBlock(1, "Fixed API timeout issue", "branch_abc123", 0.85, "hash1"),
            SimilarBlock(2, "Added retry logic", "branch_abc123", 0.75, "hash2"),
        ],
        "branch_def456": [
            SimilarBlock(3, "Setup Docker compose", "branch_def456", 0.65, "hash3"),
        ],
    }

    prompt = judge._build_prompt("New API bug fix", mock_blocks, "Working on backend")

    # Check prompt contains expected parts
    checks = [
        ("Working on backend" in prompt, "Context hint included"),
        ("branch_abc" in prompt, "Branch ID included"),
        ("Fixed API timeout" in prompt, "Similar block content included"),
        ("NEW CONTENT TO JUDGE" in prompt, "Content section included"),
        ("New API bug fix" in prompt, "Actual content included"),
    ]

    passed = 0
    for check, desc in checks:
        if check:
            passed += 1
            print(f"  ✅ {desc}")
        else:
            print(f"  ❌ {desc}")

    print(f"\n  Prompt building: {passed}/{len(checks)} passed")
    return passed == len(checks)


def run_all_tests(live: bool = False):
    """Run all tests."""
    print("🎯 InsightJudge Test Suite")
    print("="*60)

    results = []

    # Test 1: Parsing
    results.append(("Parsing", test_parsing()))

    # Test 2: Mock LLM
    results.append(("Mock LLM", test_with_mock_llm()))

    # Test 3: Edge cases
    results.append(("Edge Cases", test_edge_cases()))

    # Test 4: Prompt building
    results.append(("Prompt Building", test_prompt_building()))

    # Test 5: Live LLM (optional)
    if live:
        live_result = test_with_live_llm()
        if live_result is not None:
            results.append(("Live LLM", live_result >= 80))

    # Summary
    print("\n" + "="*60)
    print("📊 TEST SUMMARY")
    print("="*60)

    all_passed = True
    for name, passed in results:
        status = "✅" if passed else "❌"
        print(f"  {status} {name}")
        if not passed:
            all_passed = False

    print("\n" + "="*60)
    if all_passed:
        print("🎉 All tests passed!")
    else:
        print("⚠️  Some tests failed")

    return all_passed


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Test InsightJudge")
    parser.add_argument("--live", action="store_true", help="Test with live LLM server")
    args = parser.parse_args()

    success = run_all_tests(live=args.live)
    sys.exit(0 if success else 1)
