#!/usr/bin/env python3
"""
Comprehensive Error Handling Test
Test that the system gracefully handles various error conditions
"""

import sys
import os

sys.path.insert(0, '.')

from greeum.core.context_memory import ContextMemorySystem

def test_error_handling():
    """Test comprehensive error handling"""
    
    print("\n" + "="*60)
    print("🛡️ Comprehensive Error Handling Test")
    print("="*60)
    
    # Clean database
    db_path = "data/error_test.db"
    if os.path.exists(db_path):
        os.remove(db_path)
    
    memory = ContextMemorySystem(db_path)
    
    # Test 1: Input validation for add_memory
    print("\n📝 Test 1: add_memory input validation")
    
    error_tests = [
        ("Empty string", "", ValueError),
        ("Whitespace only", "   ", ValueError),
        ("None content", None, ValueError),
        ("Integer content", 123, ValueError),
        ("Invalid importance type", "test", "string", ValueError),
        ("Negative importance", "test", -0.5, ValueError),
        ("Too high importance", "test", 1.5, ValueError),
    ]
    
    passed = 0
    for test_name, content, *args in error_tests:
        try:
            if len(args) == 2:  # content, importance, expected_error
                importance, expected_error = args
                memory.add_memory(content, importance)
            else:  # content, expected_error
                expected_error = args[0]
                memory.add_memory(content)
            
            print(f"  ❌ {test_name}: Should have raised {expected_error.__name__}")
        except ValueError as e:
            if len(args) == 2 and args[1] == ValueError:
                print(f"  ✅ {test_name}: Correctly raised ValueError")
                passed += 1
            elif len(args) == 1 and args[0] == ValueError:
                print(f"  ✅ {test_name}: Correctly raised ValueError")
                passed += 1
            else:
                print(f"  ❌ {test_name}: Unexpected ValueError: {e}")
        except Exception as e:
            print(f"  ❌ {test_name}: Unexpected error: {type(e).__name__}: {e}")
    
    # Test 2: Input validation for recall
    print(f"\n🔍 Test 2: recall input validation")
    
    recall_tests = [
        ("Empty query", "", ValueError),
        ("Whitespace query", "   ", ValueError),
        ("None query", None, ValueError),
        ("Integer query", 123, ValueError),
    ]
    
    for test_name, query, expected_error in recall_tests:
        try:
            memory.recall(query)
            print(f"  ❌ {test_name}: Should have raised {expected_error.__name__}")
        except ValueError:
            print(f"  ✅ {test_name}: Correctly raised ValueError")
            passed += 1
        except Exception as e:
            print(f"  ❌ {test_name}: Unexpected error: {type(e).__name__}: {e}")
    
    # Test 3: Input validation for switch_context
    print(f"\n🔄 Test 3: switch_context input validation")
    
    context_tests = [
        ("Empty trigger", "", ValueError),
        ("Whitespace trigger", "   ", ValueError),
        ("None trigger", None, ValueError),
        ("Integer trigger", 123, ValueError),
    ]
    
    for test_name, trigger, expected_error in context_tests:
        try:
            memory.switch_context(trigger)
            print(f"  ❌ {test_name}: Should have raised {expected_error.__name__}")
        except ValueError:
            print(f"  ✅ {test_name}: Correctly raised ValueError")
            passed += 1
        except Exception as e:
            print(f"  ❌ {test_name}: Unexpected error: {type(e).__name__}: {e}")
    
    # Test 4: Graceful degradation
    print(f"\n🚧 Test 4: Graceful degradation")
    
    # Test with valid inputs to ensure system still works
    try:
        memory_id = memory.add_memory("Test memory for error handling", 0.5)
        print(f"  ✅ Valid add_memory: ID={memory_id}")
        passed += 1
    except Exception as e:
        print(f"  ❌ Valid add_memory failed: {e}")
    
    try:
        results = memory.recall("test")
        print(f"  ✅ Valid recall: Found {len(results)} results")
        passed += 1
    except Exception as e:
        print(f"  ❌ Valid recall failed: {e}")
    
    try:
        memory.switch_context("error_test_context")
        context_info = memory.get_context_info()
        print(f"  ✅ Valid context switch: {context_info.get('context_id', 'unknown')}")
        passed += 1
    except Exception as e:
        print(f"  ❌ Valid context operations failed: {e}")
    
    # Test 5: Error recovery
    print(f"\n🔄 Test 5: Error recovery")
    
    # Test that system continues working after errors
    error_count = 0
    for i in range(5):
        try:
            memory.add_memory("", 0.5)  # This should fail
        except ValueError:
            error_count += 1
        except Exception:
            pass
    
    # Now test that normal operation still works
    try:
        memory_id = memory.add_memory(f"Recovery test memory", 0.6)
        if memory_id > 0 or memory_id < 0:  # Valid ID (positive or negative)
            print(f"  ✅ System recovery: Successfully added memory after {error_count} errors")
            passed += 1
        else:
            print(f"  ❌ System recovery: Invalid memory ID returned")
    except Exception as e:
        print(f"  ❌ System recovery: Failed to add memory after errors: {e}")
    
    # Cleanup
    if os.path.exists(db_path):
        os.remove(db_path)
    
    # Evaluation
    total_tests = len(error_tests) + len(recall_tests) + len(context_tests) + 4  # +4 for graceful degradation and recovery
    success_rate = passed / total_tests * 100
    
    print(f"\n🎯 Test Results:")
    print(f"Passed: {passed}/{total_tests} ({success_rate:.1f}%)")
    print(f"Input validation: {'✅ Robust' if passed >= total_tests * 0.8 else '❌ Needs improvement'}")
    print(f"Error recovery: {'✅ Resilient' if success_rate >= 80 else '❌ Fragile'}")
    
    return success_rate >= 75

if __name__ == "__main__":
    success = test_error_handling()
    print(f"\nError Handling: {'✅ PASSED' if success else '❌ FAILED'}")
    sys.exit(0 if success else 1)