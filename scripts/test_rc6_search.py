#!/usr/bin/env python3
"""
Test RC6 improvements: Branch indexing + aggressive global fallback
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import time
from greeum.core.database_manager import DatabaseManager
from greeum.core.block_manager import BlockManager

def test_search():
    print("=== Testing v3.1.0rc6 Search Improvements ===\n")

    db = DatabaseManager()
    bm = BlockManager(db)

    # Test queries
    test_queries = [
        ("Extended Mind 철학 설계", "Should find block 13 (philosophy)"),
        ("Greeum 설계철학", "Direct philosophy search"),
        ("인과관계 추론 확장", "Should find block 17"),
        ("MCP 테스트", "Recent memories test")
    ]

    for query, description in test_queries:
        print(f"Query: '{query}'")
        print(f"Purpose: {description}")

        start = time.perf_counter()
        result = bm.search_with_slots(
            query=query,
            limit=10,
            fallback=True  # Enable global fallback
        )
        elapsed = (time.perf_counter() - start) * 1000

        # Extract results
        items = result.get('items', [])
        meta = result.get('meta', {})

        print(f"Results: {len(items)} found in {elapsed:.1f}ms")
        print(f"Search type: {meta.get('search_type', 'unknown')}")
        print(f"Fallback used: {meta.get('fallback_used', False)}")

        # Show top 3 results
        for i, item in enumerate(items[:3]):
            block_idx = item.get('block_index', '?')
            context = str(item.get('context', ''))[:100]
            score = item.get('_score', 0)
            print(f"  {i+1}. Block #{block_idx} (score={score:.3f}): {context}...")

        print("-" * 60 + "\n")

    # Print final metrics
    print("=== Search Engine Metrics ===")
    if hasattr(bm, 'dfs_search_engine'):
        metrics = bm.dfs_search_engine.metrics
        for key, value in metrics.items():
            print(f"  {key}: {value}")

if __name__ == "__main__":
    test_search()