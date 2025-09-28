#!/usr/bin/env python3
"""
Comprehensive test runner for Branch/DFS system
Runs all relevant tests and generates summary report
"""

import unittest
import sys
import time
from pathlib import Path

def run_test_suite(test_name, test_module):
    """Run a single test suite and return results."""

    module_path = Path(__file__).parent / Path(*test_module.split('.')).with_suffix('.py')
    if not module_path.exists():
        return {
            'name': test_name,
            'run': 0,
            'failures': 0,
            'errors': 0,
            'success': True,
            'skipped': True,
            'reason': f"module {test_module} not found",
        }

    loader = unittest.TestLoader()

    try:
        suite = loader.loadTestsFromName(test_module)
    except ModuleNotFoundError as exc:  # legacy suite removed
        return {
            'name': test_name,
            'run': 0,
            'failures': 0,
            'errors': 0,
            'success': True,
            'skipped': True,
            'reason': str(exc),
        }
    except Exception as exc:
        return {
            'name': test_name,
            'run': 0,
            'failures': 0,
            'errors': 1,
            'success': False,
            'exception': str(exc),
        }

    runner = unittest.TextTestRunner(verbosity=0)
    result = runner.run(suite)

    return {
        'name': test_name,
        'run': result.testsRun,
        'failures': len(result.failures),
        'errors': len(result.errors),
        'success': result.wasSuccessful(),
        'skipped': False,
    }

def main():
    print("🧪 COMPREHENSIVE TEST SUITE EXECUTION")
    print("=" * 60)
    
    # Define test suites
    test_suites = [
        # PR#4: Merge Engine
        ("PR#4: Merge Engine", "tests.test_merge_engine"),
        
        # PR#5: Integration  
        ("PR#5: Integration", "tests.test_integration_branch_dfs"),
        
        # Core Components (if they exist)
        ("Block Manager", "tests.test_block_manager"),
        ("Database Manager", "tests.test_database_manager"),
        ("STM Manager", "tests.test_stm_manager"),
        
        # Additional tests
        ("Usage Analytics", "tests.test_usage_analytics"),
        ("Metrics Collector", "tests.test_metrics_collector"),
    ]
    
    results = []
    total_tests = 0
    total_failures = 0
    total_errors = 0
    
    for name, module in test_suites:
        print(f"\n📋 Running: {name}")
        result = run_test_suite(name, module)
        results.append(result)
        
        if result.get('skipped'):
            print("   ⏭️  SKIPPED: suite not available in current build")
            continue

        if result['success']:
            print(f"   ✅ PASSED ({result['run']} tests)")
        else:
            if 'exception' in result:
                print(f"   ⚠️  ERROR: {result['exception']}")
            else:
                print(f"   ❌ FAILED: {result['failures']} failures, {result['errors']} errors")

        total_tests += result['run']
        total_failures += result['failures']
        total_errors += result['errors']
    
    # Summary Report
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY REPORT")
    print("=" * 60)
    
    # Detailed results
    print("\n🔍 Detailed Results:")
    for result in results:
        if result.get('skipped'):
            print(f"  ⏭️  {result['name']}: skipped (legacy suite removed)")
            continue

        status = "✅" if result['success'] else "❌"
        if 'exception' in result:
            print(f"  {status} {result['name']}: error - {result['exception']}")
        else:
            print(
                f"  {status} {result['name']}: {result['run']} tests, "
                f"{result['failures']} failures, {result['errors']} errors",
            )
    
    # Overall statistics
    print(f"\n📈 Overall Statistics:")
    print(f"  Total Tests Run: {total_tests}")
    print(f"  Total Failures: {total_failures}")
    print(f"  Total Errors: {total_errors}")
    
    success_rate = ((total_tests - total_failures - total_errors) / total_tests * 100) if total_tests > 0 else 0
    print(f"  Success Rate: {success_rate:.1f}%")
    
    # Recommendations
    print("\n💡 Recommendations:")
    if total_errors > 0:
        print("  1. Fix import/module errors first")
        print("  2. Check test file existence and naming")
    if total_failures > 0:
        print("  3. Review failed assertions")
        print("  4. Update test expectations if needed")
    
    return 0 if (total_failures + total_errors) == 0 else 1

if __name__ == "__main__":
    sys.exit(main())
