#!/usr/bin/env python3
"""
Test branch-aware storage with dynamic threshold
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import time
from datetime import datetime
from greeum.core.database_manager import DatabaseManager
from greeum.core.block_manager import BlockManager
from greeum.embedding_models import SimpleEmbeddingModel

def test_branch_aware_storage():
    print("=== TESTING BRANCH-AWARE STORAGE WITH DYNAMIC THRESHOLD ===\n")

    db = DatabaseManager()
    bm = BlockManager(db)
    model = SimpleEmbeddingModel(dimension=768)

    # Test memories for 3 different contexts (A: DFS/STM, B: Backup, C: MCP)
    test_memories = [
        # Round 1 - A-B-C
        ('[A1-DFS탐색] DFS 알고리즘 최적화: 양방향에서 단방향 깊이우선 탐색으로 개선', 'A'),
        ('[B1-백업설계] ContextBackupItem 스키마 설계: STM 맥락 유지 백업 시스템', 'B'),
        ('[C1-MCP테스트] v3.0.1b2 MCP 파이프라인: 메모리 추가/검색/통계 기능 검증', 'C'),
        # Round 2 - A-B-C
        ('[A2-STM버그] STM 슬롯 포인터 수정: 최신노드 after 필드 비어있는 문제 해결', 'A'),
        ('[B2-맥락유지] Claude Code /clear 대응: 최근 3개 맥락 자동 백업 기능', 'B'),
        ('[C2-배포자동화] PyPI 배포 스크립트: twine upload 자동화 파이프라인 구축', 'C'),
        # Round 3 - mixed to test threshold
        ('[A3-검색개선] Branch-based DFS: 브랜치별 인덱스로 검색 속도 7배 향상', 'A'),
        ('[C3-rc6테스트] v3.1.0rc6 검증: 블록 13 철학 메모리 검색 성공 확인', 'C'),
        ('[B3-복구전략] 맥락 복구 알고리즘: 세션 종료 후에도 연속성 유지', 'B'),
    ]

    print("Creating memories with branch-aware storage...\n")
    created_blocks = []

    for content, expected_branch in test_memories:
        # Generate embedding
        embedding = model.encode(content)

        # Add memory
        result = bm.add_block(
            context=content,
            keywords=[],
            tags=[],
            embedding=embedding,  # Already a list
            importance=0.8
        )

        if result and 'block_index' in result:
            block_idx = result['block_index']
            created_blocks.append((block_idx, expected_branch, content[:50]))
            print(f"Created Block #{block_idx} (Expected: Branch {expected_branch})")
            print(f"  Content: {content[:60]}...")

            # Check if branch-aware storage worked
            if bm.branch_aware_storage:
                cursor = db.conn.cursor()
                cursor.execute("""
                    SELECT root FROM blocks WHERE block_index = ?
                """, (block_idx,))
                result = cursor.fetchone()
                if result:
                    actual_root = result[0][:8] if result[0] else 'None'
                    print(f"  Actual root: {actual_root}...")
            print()

        time.sleep(0.1)

    print(f"\n--- Created {len(created_blocks)} memories ---\n")

    # Test search - should find memories in correct branches
    print("=== TESTING BRANCH-BASED SEARCH ===\n")

    test_queries = [
        ("DFS STM 알고리즘 최적화", "Should find A1, A2, A3"),
        ("백업 맥락유지 복구", "Should find B1, B2, B3"),
        ("MCP 배포 파이프라인", "Should find C1, C2, C3")
    ]

    for query, expected in test_queries:
        print(f"Query: '{query}'")
        print(f"Expected: {expected}")

        results = bm.search_with_slots(
            query=query,
            limit=10,
            fallback=True
        )

        items = results.get('items', [])
        meta = results.get('meta', {})

        print(f"Found {len(items)} results (search_type: {meta.get('search_type', 'unknown')})")

        # Count results by branch type
        branch_counts = {'A': 0, 'B': 0, 'C': 0}
        for item in items:
            context = item.get('context', '')
            if context.startswith('[A'):
                branch_counts['A'] += 1
            elif context.startswith('[B'):
                branch_counts['B'] += 1
            elif context.startswith('[C'):
                branch_counts['C'] += 1

        print(f"  Branch distribution: A={branch_counts['A']}, B={branch_counts['B']}, C={branch_counts['C']}")

        # Show top 3 results
        for i, item in enumerate(items[:3]):
            idx = item.get('block_index')
            context = item.get('context', '')[:80]
            score = item.get('_score', 0)
            print(f"  {i+1}. #{idx} (score={score:.3f}): {context}...")
        print()

    # Check dynamic threshold
    if bm.branch_aware_storage:
        print("=== DYNAMIC THRESHOLD INFO ===")
        print(f"Threshold: {bm.branch_aware_storage.dynamic_threshold:.3f}")
        print(f"Active slots: {list(bm.branch_aware_storage.slot_branches.keys())}")
        print(f"Branch centroids: {len(bm.branch_aware_storage.branch_centroids)}")

if __name__ == "__main__":
    test_branch_aware_storage()