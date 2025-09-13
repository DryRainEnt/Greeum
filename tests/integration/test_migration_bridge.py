#!/usr/bin/env python3
"""
Test v2.6.4 to v3.0 Migration Bridge
Shows how to gradually transition between versions
"""

import sys
import os
import logging

# Reduce noise
logging.basicConfig(level=logging.INFO)
logging.getLogger('greeum.core.causal_reasoning').setLevel(logging.ERROR)

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from greeum.core.v3_migration_bridge import V3MigrationBridge

def test_migration():
    """Test the migration bridge functionality"""
    
    print("\n🌉 Greeum v2.6.4 → v3.0 Migration Bridge Test")
    print("=" * 60)
    
    # Initialize bridge
    bridge = V3MigrationBridge(db_path="data/migration_test.db")
    
    print("\n📝 Phase 1: Hybrid Mode (Both systems active)")
    print("-" * 40)
    
    # Add memories in hybrid mode
    m1 = bridge.add_memory("프로젝트 초기 설계 회의")
    print(f"✓ Added memory #{m1} (stored in both systems)")
    
    m2 = bridge.add_memory("데이터베이스 스키마 결정")
    print(f"✓ Added memory #{m2} (stored in both systems)")
    
    m3 = bridge.add_memory("API 엔드포인트 설계")
    print(f"✓ Added memory #{m3} (stored in both systems)")
    
    # Search in hybrid mode
    print("\n🔍 Searching in hybrid mode:")
    results = bridge.search("설계", limit=3)
    for i, result in enumerate(results, 1):
        source = result.get('source', 'unknown')
        content = result.get('context', '')[:30]
        print(f"  {i}. [{source}] {content}...")
    
    print("\n📝 Phase 2: Legacy Mode Only")
    print("-" * 40)
    bridge.set_mode('legacy')
    
    m4 = bridge.add_memory("레거시 시스템 전용 메모리")
    print(f"✓ Added memory #{m4} (v2.6.4 only)")
    
    print("\n📝 Phase 3: V3 Mode Only")
    print("-" * 40)
    bridge.set_mode('v3')
    
    # V3 with context switching
    bridge.context_memory.switch_context("new_feature_planning")
    m5 = bridge.add_memory("새로운 기능 계획 - 컨텍스트 인식")
    print(f"✓ Added memory #{m5} (v3.0 only with context)")
    
    print("\n📝 Phase 4: Migration Test")
    print("-" * 40)
    bridge.set_mode('hybrid')
    
    # Migrate specific blocks
    print("Migrating blocks 0-2 to v3.0...")
    stats = bridge.batch_migrate(start_index=0, end_index=2)
    print(f"Migration results: {stats}")
    
    # Check statistics
    print("\n📊 System Statistics:")
    stats = bridge.get_statistics()
    print(f"  Mode: {stats['mode']}")
    print(f"  Migrated blocks: {stats['migrated_blocks']}")
    print(f"  V2.6.4 total blocks: {stats.get('v2_total_blocks', 0)}")
    print(f"  V3.0 contexts: {stats['v3_contexts']}")
    
    print("\n" + "=" * 60)
    print("✅ Migration Bridge Test Complete!")
    print("\n핵심 기능:")
    print("  1. Hybrid mode: 양쪽 시스템 동시 운영")
    print("  2. Legacy mode: v2.6.4만 사용")
    print("  3. V3 mode: v3.0만 사용")
    print("  4. Batch migration: 점진적 데이터 이전")
    print("  5. Unified search: 통합 검색 결과")
    
    # Cleanup
    if os.path.exists("data/migration_test.db"):
        os.remove("data/migration_test.db")
        print("\n✓ Test database cleaned up")

if __name__ == "__main__":
    test_migration()