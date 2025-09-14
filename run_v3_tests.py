#!/usr/bin/env python3
"""
V3.0 Branch/DFS System Test Suite
Clean test runner for core v3.0 functionality only
"""

import unittest
import sys
import time
from pathlib import Path

def run_test_module(name, module_path):
    """Run a single test module"""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    try:
        suite = loader.loadTestsFromName(module_path)
        runner = unittest.TextTestRunner(verbosity=1)
        result = runner.run(suite)
        
        return {
            'name': name,
            'tests': result.testsRun,
            'failures': len(result.failures),
            'errors': len(result.errors),
            'success': result.wasSuccessful()
        }
    except Exception as e:
        return {
            'name': name,
            'tests': 0,
            'failures': 0,
            'errors': 1,
            'success': False,
            'exception': str(e)
        }

def main():
    print("🚀 V3.0 BRANCH/DFS SYSTEM TEST SUITE")
    print("=" * 60)
    print("📝 Testing only core v3.0 features (legacy removed)")
    print()
    
    # Core v3.0 test modules
    test_modules = [
        ("PR#4: Merge Engine", "tests.test_merge_engine"),
        ("PR#5: Branch/DFS Integration", "tests.test_integration_branch_dfs"),
    ]
    
    results = []
    total_tests = 0
    total_failures = 0
    total_errors = 0
    
    for name, module in test_modules:
        print(f"🧪 Running: {name}")
        print("-" * 40)
        
        result = run_test_module(name, module)
        results.append(result)
        
        if result['success']:
            print(f"✅ PASSED: {result['tests']} tests")
        else:
            if 'exception' in result:
                print(f"⚠️ ERROR: {result['exception']}")
            else:
                print(f"❌ FAILED: {result['failures']} failures, {result['errors']} errors")
        print()
        
        total_tests += result['tests']
        total_failures += result['failures']
        total_errors += result['errors']
    
    # Summary
    print("=" * 60)
    print("📊 V3.0 TEST SUMMARY")
    print("=" * 60)
    
    for result in results:
        status = "✅" if result['success'] else "❌"
        print(f"{status} {result['name']}: {result['tests']} tests run")
        if not result['success']:
            print(f"   → {result['failures']} failures, {result['errors']} errors")
    
    print()
    print(f"📈 Overall Results:")
    print(f"  • Total Tests: {total_tests}")
    print(f"  • Failures: {total_failures}")
    print(f"  • Errors: {total_errors}")
    
    if total_tests > 0:
        success_rate = ((total_tests - total_failures - total_errors) / total_tests * 100)
        print(f"  • Success Rate: {success_rate:.1f}%")
        
        if success_rate == 100:
            print("\n🎉 ALL V3.0 TESTS PASSING!")
        elif success_rate >= 90:
            print("\n✨ V3.0 system is stable")
        else:
            print("\n⚠️ Some issues need attention")
    
    # Performance targets check
    print("\n🎯 Performance Targets (from integration tests):")
    print("  • local_hit_rate: Target ≥27%")
    print("  • avg_hops: Target ≤8.5")
    print("  • p95_latency: Target <150ms")
    print("  • merge_undo_rate: Target ≤5%")
    
    return 0 if (total_failures + total_errors) == 0 else 1

if __name__ == "__main__":
    sys.exit(main())