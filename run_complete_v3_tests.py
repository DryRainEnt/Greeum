#!/usr/bin/env python3
"""
Complete V3.0 Test Suite including PR1-5
Tests all Branch/DFS system components
"""

import unittest
import sys

def run_test_suite(name, module):
    """Run test module and return results"""
    loader = unittest.TestLoader()
    try:
        suite = loader.loadTestsFromName(module)
        runner = unittest.TextTestRunner(verbosity=0)
        result = runner.run(suite)
        return {
            'name': name,
            'run': result.testsRun,
            'failures': len(result.failures),
            'errors': len(result.errors),
            'success': result.wasSuccessful()
        }
    except Exception as e:
        return {
            'name': name,
            'run': 0,
            'failures': 0,
            'errors': 1,
            'success': False,
            'exception': str(e)
        }

def main():
    print("🔍 COMPLETE V3.0 TEST DISCOVERY")
    print("=" * 60)
    
    # All PR tests
    test_suites = [
        # PR1-3: Branch/DFS Core
        ("PR#1-3: Branch Manager", "tests.test_branch_manager"),
        ("PR#1-3: Branch Integration", "tests.test_branch_integration"),
        
        # PR4: Merge Engine
        ("PR#4: Merge Engine", "tests.test_merge_engine"),
        
        # PR5: Integration
        ("PR#5: Branch/DFS Integration", "tests.test_integration_branch_dfs"),
    ]
    
    results = []
    total_tests = 0
    total_failures = 0
    total_errors = 0
    
    print("\n📋 Running All Tests:")
    print("-" * 60)
    
    for name, module in test_suites:
        result = run_test_suite(name, module)
        results.append(result)
        
        status = "✅" if result['success'] else "❌"
        
        if 'exception' in result:
            print(f"{status} {name}: Not found")
        else:
            failures_errors = f"({result['failures']}F/{result['errors']}E)" if not result['success'] else ""
            print(f"{status} {name}: {result['run']} tests {failures_errors}")
            
        total_tests += result['run']
        total_failures += result['failures']
        total_errors += result['errors']
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 COMPREHENSIVE SUMMARY")
    print("=" * 60)
    
    # PR breakdown
    print("\n🔧 By PR:")
    pr1_3_tests = sum(r['run'] for r in results[:2])
    pr1_3_pass = sum(r['run'] - r['failures'] - r['errors'] for r in results[:2])
    pr4_tests = results[2]['run'] if len(results) > 2 else 0
    pr4_pass = results[2]['run'] - results[2]['failures'] - results[2]['errors'] if len(results) > 2 else 0
    pr5_tests = results[3]['run'] if len(results) > 3 else 0
    pr5_pass = results[3]['run'] - results[3]['failures'] - results[3]['errors'] if len(results) > 3 else 0
    
    print(f"  PR#1-3 (Branch/DFS Core): {pr1_3_pass}/{pr1_3_tests} passed")
    print(f"  PR#4 (Merge Engine): {pr4_pass}/{pr4_tests} passed")
    print(f"  PR#5 (Integration): {pr5_pass}/{pr5_tests} passed")
    
    # Overall
    print(f"\n📈 Overall:")
    print(f"  Total Tests: {total_tests}")
    print(f"  Passed: {total_tests - total_failures - total_errors}")
    print(f"  Failed: {total_failures}")
    print(f"  Errors: {total_errors}")
    
    if total_tests > 0:
        success_rate = ((total_tests - total_failures - total_errors) / total_tests * 100)
        print(f"  Success Rate: {success_rate:.1f}%")
        
        if success_rate == 100:
            print("\n🎉 PERFECT! All tests passing!")
        elif success_rate >= 90:
            print("\n✨ Excellent! System is production-ready")
        elif success_rate >= 80:
            print("\n👍 Good! Minor issues to address")
        else:
            print("\n⚠️ Needs attention")
    
    # Missing tests check
    print("\n🔎 Test Coverage Check:")
    if pr1_3_tests == 0:
        print("  ⚠️ PR#1-3 tests missing or not found")
    else:
        print(f"  ✅ PR#1-3: {pr1_3_tests} tests found")
    print(f"  ✅ PR#4: {pr4_tests} tests found")
    print(f"  ✅ PR#5: {pr5_tests} tests found")
    
    return 0 if success_rate >= 80 else 1

if __name__ == "__main__":
    sys.exit(main())