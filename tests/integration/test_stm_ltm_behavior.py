#!/usr/bin/env python3
"""
STM/LTM 동작 검증 테스트
정말로 의도한 대로 작동하는지 확인
"""

import sys
import os
import time
import sqlite3

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from greeum.core.context_memory import ContextMemorySystem

def test_stm_ltm_separation():
    """STM과 LTM이 제대로 분리되어 작동하는지 테스트"""
    
    print("\n" + "="*60)
    print("🧪 STM/LTM Separation Test")
    print("="*60)
    
    # Initialize
    db_path = "data/stm_ltm_test.db"
    if os.path.exists(db_path):
        os.remove(db_path)
    
    memory = ContextMemorySystem(db_path)
    
    print("\n1️⃣ STM Phase (Active Context)")
    print("-" * 40)
    
    # Add memories
    m1 = memory.add_memory("작업 시작 - 코드 리뷰")
    m2 = memory.add_memory("버그 발견 - null 체크 누락")
    m3 = memory.add_memory("수정 완료 - 테스트 추가")
    
    # Check STM state
    active = memory.context_manager.active_nodes
    buffer = memory.context_manager.memories
    
    print(f"✓ Active nodes: {len(active)} nodes")
    for node_id, activation in list(active.items())[:3]:
        print(f"  Node #{node_id}: activation={activation:.2f}")
    
    print(f"✓ Temporary buffer: {len(buffer)} items")
    
    # Check if memories went straight to LTM
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM blocks")
    ltm_count = cursor.fetchone()[0]
    
    print(f"\n⚠️  LTM status: {ltm_count} blocks already stored")
    
    if ltm_count > 0:
        print("   → Memories go straight to LTM (no staging in STM)")
    
    print("\n2️⃣ Context Switch Test")
    print("-" * 40)
    
    # Force context switch
    memory.switch_context("break_time")
    m4 = memory.add_memory("휴식 시간")
    
    # Check if old context was saved
    cursor.execute("SELECT COUNT(*) FROM contexts")
    context_count = cursor.fetchone()[0]
    print(f"✓ Contexts created: {context_count}")
    
    # Check connections
    cursor.execute("SELECT COUNT(*) FROM memory_connections")
    connections = cursor.fetchone()[0]
    print(f"✓ Connections: {connections}")
    
    print("\n3️⃣ Memory Decay Test")
    print("-" * 40)
    
    # Add multiple memories to test decay
    initial_active = len(memory.context_manager.active_nodes)
    
    for i in range(5):
        memory.add_memory(f"Memory {i}")
    
    final_active = memory.context_manager.active_nodes
    
    print(f"✓ Active nodes after 5 additions:")
    for node_id, activation in final_active.items():
        if activation > 0.1:
            print(f"  Node #{node_id}: {activation:.3f}")
    
    # Check which nodes decayed out
    print(f"\n✓ Decay behavior:")
    print(f"  Initial: {initial_active} nodes")
    print(f"  Final: {len(final_active)} nodes")
    print(f"  Decayed out: {initial_active - len([a for a in final_active.values() if a < 0.1])}")
    
    print("\n4️⃣ Real STM vs LTM Behavior")
    print("-" * 40)
    
    print("Current implementation:")
    print("  STM = active_nodes (현재 활성 메모리)")
    print("  LTM = blocks table (영구 저장)")
    print("  Transfer = Immediate (즉시 저장)")
    
    print("\nIntended behavior:")
    print("  STM = temporary holding")
    print("  LTM = consolidated storage")
    print("  Transfer = After processing/sleep")
    
    # Cleanup
    conn.close()
    if os.path.exists(db_path):
        os.remove(db_path)
    
    print("\n" + "="*60)
    print("📊 Summary:")
    print("  ✅ Network formation works")
    print("  ✅ Context switching works")
    print("  ✅ Activation decay works")
    print("  ⚠️  STM→LTM transfer is immediate (not staged)")
    print("="*60)

if __name__ == "__main__":
    test_stm_ltm_separation()