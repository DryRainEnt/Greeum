#!/usr/bin/env python3
"""
Test Context-Dependent Memory System
Shows how memories form networks based on context
"""

import sys
import os
import time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from greeum.core.context_memory import ContextMemorySystem

def test_context_memory():
    """Test context-dependent memory formation"""
    
    print("Testing Context-Dependent Memory System")
    print("=" * 50)
    
    # Initialize
    memory = ContextMemorySystem(db_path="data/test_context_memory.db")
    
    # Scenario 1: Morning work context
    print("\n📍 Context: Morning Work Session")
    memory.switch_context("morning_work")
    
    m1 = memory.add_memory("버그를 발견했다. 로그인 화면에서 에러 발생")
    print(f"  Added memory #{m1}")
    
    m2 = memory.add_memory("원인은 토큰 만료 처리 문제였다")
    print(f"  Added memory #{m2}")
    
    m3 = memory.add_memory("수정 완료. 테스트도 통과했다")
    print(f"  Added memory #{m3}")
    
    # Check connections
    connections = memory.get_memory_connections(m3)
    print(f"  Memory #{m3} has {len(connections)} connections")
    
    # Scenario 2: Context switch (lunch break)
    print("\n📍 Context Switch: Lunch Break")
    time.sleep(1)  # Small delay
    memory.switch_context("lunch_break")
    
    m4 = memory.add_memory("점심으로 김치찌개를 먹었다")
    print(f"  Added memory #{m4}")
    
    m5 = memory.add_memory("동료와 주말 계획 얘기를 나눴다")
    print(f"  Added memory #{m5}")
    
    # Check connections (should be connected to each other, not to morning work)
    connections_m5 = memory.get_memory_connections(m5)
    print(f"  Memory #{m5} has {len(connections_m5)} connections")
    
    # Scenario 3: Return to work (afternoon)
    print("\n📍 Context: Afternoon Work Session")
    memory.switch_context("afternoon_work")
    
    m6 = memory.add_memory("오전에 수정한 버그 관련 추가 테스트 진행")
    print(f"  Added memory #{m6}")
    
    m7 = memory.add_memory("배포 준비 완료")
    print(f"  Added memory #{m7}")
    
    # Test recall with spreading activation
    print("\n🔍 Testing Recall with Spreading Activation")
    print("Query: '버그'")
    
    results = memory.recall("버그", use_activation=True)
    
    print(f"Found {len(results)} memories:")
    for i, result in enumerate(results[:5], 1):
        activation = result.get('activation_score', 0)
        print(f"  {i}. Memory #{result['block_index']}: {result['context'][:50]}...")
        print(f"     Activation: {activation:.3f}")
    
    # Show how morning bug work and afternoon testing are connected
    print("\n🔗 Network Structure:")
    print("Morning work memories should be strongly connected to each other")
    print("Lunch memories should be isolated")
    print("Afternoon work might connect back to morning through content similarity")
    
    # Get context info
    print("\n📊 Current Context Info:")
    info = memory.get_context_info()
    print(f"  Context ID: {info['context_id']}")
    print(f"  Trigger: {info['trigger']}")
    print(f"  Active memories: {info['active_memories']}")
    
    # Demonstrate bias
    print("\n🎯 Testing Context Bias (Recency Effect)")
    print("Adding a new memory about bugs...")
    m8 = memory.add_memory("버그 수정 관련 문서 작성 중")
    
    print("This should strongly connect to recent afternoon memories,")
    print("and weakly to morning memories (through semantic similarity)")
    
    connections_m8 = memory.get_memory_connections(m8)
    for conn in connections_m8:
        if conn['from'] == m8:
            print(f"  → Memory #{conn['to']}: weight={conn['weight']:.3f}")
    
    print("\n" + "=" * 50)
    print("Context-Dependent Memory Test Complete!")
    print("\nKey observations:")
    print("1. Memories in same context are auto-connected")
    print("2. Context switches create natural boundaries")
    print("3. Spreading activation retrieves related memories")
    print("4. Recent context has stronger influence (bias)")
    
    # Cleanup
    if os.path.exists("data/test_context_memory.db"):
        os.remove("data/test_context_memory.db")
        print("\nTest database cleaned up")

if __name__ == "__main__":
    test_context_memory()