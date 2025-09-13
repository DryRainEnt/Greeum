#!/usr/bin/env python3
"""
Importance-Based Filtering Test
Test memory filtering and statistics by importance levels
"""

import sys
import os

sys.path.insert(0, '.')

from greeum.core.context_memory import ContextMemorySystem

def test_importance_filtering():
    """Test importance-based memory filtering"""
    
    print("\n" + "="*60)
    print("🎯 Importance-Based Filtering Test")
    print("="*60)
    
    # Clean database
    db_path = "data/importance_test.db"
    if os.path.exists(db_path):
        os.remove(db_path)
    
    memory = ContextMemorySystem(db_path)
    
    # Create memories with different importance levels
    test_memories = [
        ("Critical bug fixed", 0.9),
        ("Meeting scheduled", 0.3),
        ("Major milestone achieved", 0.8),
        ("Coffee break", 0.1),
        ("Important decision made", 0.7),
        ("Random thought", 0.2),
        ("Security vulnerability patched", 0.95),
        ("Lunch time", 0.15),
        ("Code review completed", 0.6),
        ("Project deadline approaching", 0.85)
    ]
    
    print(f"📝 Adding {len(test_memories)} memories with varying importance...")
    
    for content, importance in test_memories:
        memory_id = memory.add_memory(content, importance)
        source = "STM" if memory_id < 0 else "LTM"
        print(f"  {content[:30]:30} | {importance:0.2f} | {source}")
    
    # Test 1: High importance filtering
    print(f"\n🔥 Test 1: High importance memories (≥0.7)")
    high_importance = memory.get_high_importance_memories(threshold=0.7)
    print(f"Found {len(high_importance)} high importance memories:")
    for mem in high_importance:
        print(f"  [{mem['source']}] {mem['content'][:40]:40} | {mem['importance']:0.2f}")
    
    # Test 2: Low importance filtering
    print(f"\n🔹 Test 2: Low importance memories (≤0.3)")
    low_importance = memory.get_low_importance_memories(threshold=0.3)
    print(f"Found {len(low_importance)} low importance memories:")
    for mem in low_importance:
        print(f"  [{mem['source']}] {mem['content'][:40]:40} | {mem['importance']:0.2f}")
    
    # Test 3: Custom range filtering
    print(f"\n⚖️ Test 3: Medium importance memories (0.5-0.69)")
    medium_importance = memory.filter_by_importance(min_importance=0.5, max_importance=0.69)
    print(f"Found {len(medium_importance)} medium importance memories:")
    for mem in medium_importance:
        print(f"  [{mem['source']}] {mem['content'][:40]:40} | {mem['importance']:0.2f}")
    
    # Test 4: Statistics
    print(f"\n📊 Test 4: Importance statistics")
    stats = memory.get_importance_statistics()
    
    print(f"STM Statistics:")
    print(f"  Count: {stats['stm_stats']['count']}")
    print(f"  Average importance: {stats['stm_stats']['avg_importance']:.3f}")
    if stats['stm_stats']['count'] > 0:
        print(f"  Range: {stats['stm_stats']['min_importance']:.2f} - {stats['stm_stats']['max_importance']:.2f}")
        print(f"  High importance (≥0.7): {stats['stm_stats']['high_importance']}")
    
    print(f"LTM Statistics:")
    print(f"  Count: {stats['ltm_stats']['count']}")
    if stats['ltm_stats']['count'] > 0:
        print(f"  Average importance: {stats['ltm_stats']['avg_importance']:.3f}")
        print(f"  Range: {stats['ltm_stats']['min_importance']:.2f} - {stats['ltm_stats']['max_importance']:.2f}")
        print(f"  High importance (≥0.7): {stats['ltm_stats']['high_importance']}")
    
    if stats['overall_stats']:
        print(f"Overall Statistics:")
        print(f"  Total memories: {stats['overall_stats']['total_memories']}")
        print(f"  Average importance: {stats['overall_stats']['avg_importance']:.3f}")
        print(f"  STM: {stats['overall_stats']['stm_percentage']:.1f}%")
        print(f"  LTM: {stats['overall_stats']['ltm_percentage']:.1f}%")
        print(f"  High importance total: {stats['overall_stats']['high_importance_total']}")
    
    # Test 5: Validation
    print(f"\n✅ Test 5: Validation")
    
    # Count expected high importance (≥0.7)
    expected_high = len([imp for _, imp in test_memories if imp >= 0.7])
    actual_high = len(high_importance)
    
    # Count expected low importance (≤0.3)
    expected_low = len([imp for _, imp in test_memories if imp <= 0.3])
    actual_low = len(low_importance)
    
    # Count expected medium importance (0.5-0.69)
    expected_medium = len([imp for _, imp in test_memories if 0.5 <= imp <= 0.69])
    actual_medium = len(medium_importance)
    
    validation_results = [
        ("High importance filtering", expected_high, actual_high),
        ("Low importance filtering", expected_low, actual_low),
        ("Medium importance filtering", expected_medium, actual_medium),
        ("Statistics calculation", len(test_memories), stats['overall_stats'].get('total_memories', 0))
    ]
    
    passed = 0
    for test_name, expected, actual in validation_results:
        status = "✅" if expected == actual else "❌"
        print(f"  {test_name}: {status} (expected: {expected}, actual: {actual})")
        if expected == actual:
            passed += 1
    
    success_rate = passed / len(validation_results) * 100
    
    # Cleanup
    if os.path.exists(db_path):
        os.remove(db_path)
    
    print(f"\n🎯 Test Results:")
    print(f"Passed: {passed}/{len(validation_results)} ({success_rate:.1f}%)")
    
    return success_rate >= 75

if __name__ == "__main__":
    success = test_importance_filtering()
    print(f"\nImportance Filtering: {'✅ PASSED' if success else '❌ FAILED'}")
    sys.exit(0 if success else 1)