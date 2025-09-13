#!/usr/bin/env python3
"""
STM/LTM Consolidation Test
Test that memories properly transition from STM to LTM
"""

import sys
import os
import time

sys.path.insert(0, '.')

from greeum.core.context_memory import ContextMemorySystem

def test_stm_ltm_consolidation():
    """Test STM/LTM consolidation behavior"""
    
    print("\n" + "="*60)
    print("🧠 STM/LTM Consolidation Test")
    print("="*60)
    
    # Clean database
    db_path = "data/stm_test.db"
    if os.path.exists(db_path):
        os.remove(db_path)
    
    memory = ContextMemorySystem(db_path)
    
    print(f"STM capacity: {memory.context_manager.stm_capacity}")
    print(f"Importance threshold: {memory.context_manager.stm_consolidation_threshold}")
    
    # Test 1: Low importance memory should stay in STM
    print("\n📝 Test 1: Low importance memories")
    for i in range(5):
        result_id = memory.add_memory(f"Low importance memory {i}", importance=0.3)
        print(f"Added memory {i}: ID={result_id} ({'STM' if result_id < 0 else 'LTM'})")
    
    stm_count = len([m for m in memory.context_manager.memories if m['ltm_id'] is None])
    print(f"STM memories: {stm_count}/5")
    
    # Test 2: High importance memory should go to LTM immediately
    print("\n⚡ Test 2: High importance memory")
    result_id = memory.add_memory("Critical important memory!", importance=0.8)
    print(f"High importance memory: ID={result_id} ({'STM' if result_id < 0 else 'LTM'})")
    
    # Test 3: STM overflow should trigger LTM promotion
    print("\n🌊 Test 3: STM overflow")
    print(f"Adding {memory.context_manager.stm_capacity + 5} more memories...")
    
    for i in range(memory.context_manager.stm_capacity + 5):
        result_id = memory.add_memory(f"Overflow test memory {i}", importance=0.4)
        if i % 5 == 0:
            stm_current = len([m for m in memory.context_manager.memories if m['ltm_id'] is None])
            print(f"After {i+1} additions: STM count = {stm_current}")
    
    # Final status
    final_stm_count = len([m for m in memory.context_manager.memories if m['ltm_id'] is None])
    total_memories = len(memory.context_manager.memories)
    ltm_count = len([m for m in memory.context_manager.memories if m['ltm_id'] is not None])
    
    print(f"\n📊 Final Status:")
    print(f"Total memories: {total_memories}")
    print(f"STM memories: {final_stm_count}")
    print(f"LTM memories: {ltm_count}")
    print(f"STM capacity respected: {'✅ Yes' if final_stm_count <= memory.context_manager.stm_capacity else '❌ No'}")
    
    # Test 4: Time-based consolidation simulation
    print(f"\n⏰ Test 4: Time-based consolidation")
    print("Simulating old memories (modifying timestamps)...")
    
    # Make some STM memories appear old
    old_time = time.time() - memory.context_manager.stm_time_threshold - 100
    modified_count = 0
    for memory_entry in memory.context_manager.memories:
        if memory_entry['ltm_id'] is None and modified_count < 2:
            memory_entry['timestamp'] = old_time
            modified_count += 1
    
    # Trigger consolidation
    memory.context_manager._trigger_stm_consolidation()
    
    final_stm_after_time = len([m for m in memory.context_manager.memories if m['ltm_id'] is None])
    print(f"STM count after time consolidation: {final_stm_after_time}")
    
    # Cleanup
    if os.path.exists(db_path):
        os.remove(db_path)
    
    # Evaluation
    success_criteria = [
        final_stm_count <= memory.context_manager.stm_capacity,  # STM capacity respected
        ltm_count > 0,  # Some memories promoted to LTM
        final_stm_after_time < final_stm_count  # Time-based consolidation worked
    ]
    
    success_rate = sum(success_criteria) / len(success_criteria) * 100
    
    print(f"\n🎯 Test Results:")
    print(f"STM capacity control: {'✅' if success_criteria[0] else '❌'}")
    print(f"LTM promotion: {'✅' if success_criteria[1] else '❌'}")
    print(f"Time-based consolidation: {'✅' if success_criteria[2] else '❌'}")
    print(f"Overall success: {success_rate:.1f}%")
    
    return success_rate >= 75

if __name__ == "__main__":
    success = test_stm_ltm_consolidation()
    print(f"\nSTM/LTM Consolidation: {'✅ PASSED' if success else '❌ FAILED'}")
    sys.exit(0 if success else 1)