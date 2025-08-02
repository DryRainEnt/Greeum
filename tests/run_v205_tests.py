#!/usr/bin/env python3
"""
Comprehensive Test Runner for Greeum v2.0.5 Features
Executes all unit tests and integration tests for the new v2.0.5 modules.
Provides detailed coverage reporting and performance analysis.
"""

import unittest
import sys
import os
import time
import json
from datetime import datetime
from io import StringIO

# Add the greeum package to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Import all test modules
from test_usage_analytics import TestUsageAnalytics, TestUsageAnalyticsIntegration
from test_quality_validator import TestQualityValidator, TestQualityValidatorIntegration
from test_duplicate_detector import TestDuplicateDetector, TestDuplicateDetectorIntegration
from test_enhanced_tool_schema import TestEnhancedToolSchema, TestEnhancedToolSchemaIntegration
from test_v205_integration import TestV205Integration, TestV205PerformanceBenchmarks


class TestResult:
    """Enhanced test result tracking"""
    
    def __init__(self):
        self.results = {}
        self.start_time = None
        self.end_time = None
        self.total_tests = 0
        self.total_failures = 0
        self.total_errors = 0
        self.performance_metrics = {}
    
    def add_result(self, module_name, result, duration):
        """Add test result for a module"""
        self.results[module_name] = {
            'tests_run': result.testsRun,
            'failures': len(result.failures),
            'errors': len(result.errors),
            'success_rate': ((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100) if result.testsRun > 0 else 0,
            'duration': duration,
            'failure_details': [str(f[0]) for f in result.failures],
            'error_details': [str(e[0]) for e in result.errors]
        }
        
        self.total_tests += result.testsRun
        self.total_failures += len(result.failures)
        self.total_errors += len(result.errors)
    
    def calculate_performance_metrics(self):
        """Calculate overall performance metrics"""
        if self.start_time and self.end_time:
            total_duration = self.end_time - self.start_time
            self.performance_metrics = {
                'total_duration_seconds': total_duration,
                'tests_per_second': self.total_tests / total_duration if total_duration > 0 else 0,
                'average_test_duration': total_duration / self.total_tests if self.total_tests > 0 else 0
            }
    
    def get_summary(self):
        """Get comprehensive test summary"""
        overall_success_rate = ((self.total_tests - self.total_failures - self.total_errors) / self.total_tests * 100) if self.total_tests > 0 else 0
        
        return {
            'timestamp': datetime.now().isoformat(),
            'total_tests': self.total_tests,
            'total_failures': self.total_failures,
            'total_errors': self.total_errors,
            'overall_success_rate': overall_success_rate,
            'module_results': self.results,
            'performance_metrics': self.performance_metrics,
            'status': 'PASSED' if (self.total_failures + self.total_errors) == 0 else 'FAILED',
            'coverage_areas': [
                'UsageAnalytics - Database operations, event logging, session management',
                'QualityValidator - Content analysis, quality scoring, recommendations',
                'DuplicateDetector - Similarity algorithms, batch processing, performance',
                'EnhancedToolSchema - MCP integration, parameter validation, usage hints',
                'Integration - End-to-end workflows, error handling, performance benchmarks'
            ]
        }


def run_test_suite(test_class, module_name, verbose=True):
    """Run a test suite and return results"""
    print(f"\n{'='*60}")
    print(f"Running {module_name} Tests")
    print(f"{'='*60}")
    
    # Create test suite
    suite = unittest.TestLoader().loadTestsFromTestCase(test_class)
    
    # Capture output
    stream = StringIO()
    runner = unittest.TextTestRunner(stream=stream, verbosity=2 if verbose else 1)
    
    # Run tests with timing
    start_time = time.time()
    result = runner.run(suite)
    duration = time.time() - start_time
    
    # Print results
    if verbose:
        print(stream.getvalue())
    
    print(f"\n{module_name} Results:")
    print(f"  Tests run: {result.testsRun}")
    print(f"  Failures: {len(result.failures)}")
    print(f"  Errors: {len(result.errors)}")
    print(f"  Success rate: {((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100):.1f}%")
    print(f"  Duration: {duration:.2f}s")
    
    if result.failures:
        print(f"  ❌ Failures:")
        for test, failure in result.failures[:3]:  # Show first 3
            print(f"    - {test}")
    
    if result.errors:
        print(f"  ⚠️  Errors:")
        for test, error in result.errors[:3]:  # Show first 3  
            print(f"    - {test}")
    
    return result, duration


def check_module_availability():
    """Check if all required modules are available"""
    print("🔍 Checking module availability...")
    
    modules_to_check = [
        ('greeum.core.usage_analytics', 'UsageAnalytics'),
        ('greeum.core.quality_validator', 'QualityValidator'),
        ('greeum.core.duplicate_detector', 'DuplicateDetector'),
        ('greeum.mcp.enhanced_tool_schema', 'EnhancedToolSchema')
    ]
    
    missing_modules = []
    
    for module_path, class_name in modules_to_check:
        try:
            module = __import__(module_path, fromlist=[class_name])
            getattr(module, class_name)
            print(f"  ✅ {module_path}.{class_name}")
        except (ImportError, AttributeError) as e:
            print(f"  ❌ {module_path}.{class_name} - {e}")
            missing_modules.append(module_path)
    
    if missing_modules:
        print(f"\n⚠️  Missing modules detected: {missing_modules}")
        print("Please ensure all v2.0.5 modules are properly installed.")
        return False
    
    print("✅ All required modules are available")
    return True


def run_performance_analysis():
    """Run performance analysis"""
    print(f"\n{'='*60}")
    print("Performance Analysis")
    print(f"{'='*60}")
    
    try:
        # Import performance test classes
        from test_v205_integration import TestV205PerformanceBenchmarks
        
        # Run performance benchmarks
        suite = unittest.TestLoader().loadTestsFromTestCase(TestV205PerformanceBenchmarks)
        stream = StringIO()
        runner = unittest.TextTestRunner(stream=stream, verbosity=1)
        
        start_time = time.time()
        result = runner.run(suite)
        duration = time.time() - start_time
        
        print(f"Performance Benchmark Results:")
        print(f"  Tests run: {result.testsRun}")
        print(f"  Duration: {duration:.2f}s")
        
        if result.testsRun > 0 and len(result.failures) + len(result.errors) == 0:
            print("  ✅ All performance benchmarks passed")
            print("  🚀 System performance meets requirements")
        else:
            print("  ⚠️  Some performance benchmarks failed")
            print("  📊 Review performance optimization opportunities")
        
        return result.testsRun > 0 and len(result.failures) + len(result.errors) == 0
        
    except Exception as e:
        print(f"❌ Performance analysis failed: {e}")
        return False


def generate_coverage_report(test_result):
    """Generate a coverage report"""
    print(f"\n{'='*60}")
    print("Test Coverage Report")
    print(f"{'='*60}")
    
    coverage_areas = {
        'UsageAnalytics': {
            'Database Operations': ['Database initialization', 'Schema creation', 'Data cleanup'],
            'Event Logging': ['Input sanitization', 'Event recording', 'Error handling'],
            'Session Management': ['Session lifecycle', 'Statistics calculation', 'Analytics generation'],
            'Performance': ['Concurrent operations', 'Memory usage', 'Query optimization']
        },
        'QualityValidator': {
            'Content Analysis': ['Length assessment', 'Content richness', 'Structural quality'],
            'Quality Scoring': ['Multi-factor scoring', 'Importance adjustment', 'Level classification'],
            'Edge Cases': ['Unicode handling', 'Large content', 'Empty content'],
            'Recommendations': ['Suggestion generation', 'Warning creation', 'Best practices']
        },
        'DuplicateDetector': {
            'Similarity Detection': ['Hash matching', 'Text similarity', 'Semantic similarity'],
            'Performance Optimization': ['Context windowing', 'Batch processing', 'Memory efficiency'],
            'Algorithm Testing': ['Threshold classification', 'Fallback mechanisms', 'Error recovery'],
            'Statistical Analysis': ['Duplicate rates', 'Trend analysis', 'Recommendations']
        },
        'EnhancedToolSchema': {
            'Schema Generation': ['All 10 MCP tools', 'Parameter validation', 'Default values'],
            'Usage Guidance': ['Workflow hints', 'Best practices', 'Error prevention'],
            'Integration': ['MCP compatibility', 'JSON serialization', 'Tool relationships'],
            'Documentation': ['Comprehensive descriptions', 'Usage examples', 'Parameter guides']
        },
        'Integration': {
            'End-to-End Workflows': ['Complete memory addition', 'Quality + duplicate flow', 'MCP simulation'],
            'Error Handling': ['Graceful degradation', 'Error recovery', 'Logging'],
            'Performance': ['Load testing', 'Benchmark validation', 'Resource usage'],
            'Real-world Scenarios': ['Batch processing', 'Concurrent operations', 'Schema-driven workflows']
        }
    }
    
    print("📊 Coverage Areas Tested:")
    for area, components in coverage_areas.items():
        area_result = test_result.results.get(area, {})
        success_rate = area_result.get('success_rate', 0)
        status_emoji = "✅" if success_rate >= 95 else "⚠️" if success_rate >= 80 else "❌"
        
        print(f"\n{status_emoji} {area} ({success_rate:.1f}% success rate):")
        for component, features in components.items():
            print(f"  • {component}:")
            for feature in features:
                print(f"    - {feature}")
    
    print(f"\n📈 Overall Coverage Assessment:")
    overall_success = test_result.performance_metrics.get('overall_success_rate', 0)
    if overall_success >= 95:
        print("  🎉 Excellent coverage - Production ready")
    elif overall_success >= 85:
        print("  ✅ Good coverage - Minor issues to address")
    elif overall_success >= 70:
        print("  ⚠️  Adequate coverage - Several issues need attention")
    else:
        print("  ❌ Poor coverage - Major issues require resolution")


def save_test_report(test_result, filename=None):
    """Save detailed test report to file"""
    if filename is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"greeum_v205_test_report_{timestamp}.json"
    
    filepath = os.path.join(os.path.dirname(__file__), 'results', filename)
    
    # Ensure results directory exists
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    
    # Save report
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(test_result.get_summary(), f, indent=2, ensure_ascii=False)
        
        print(f"\n📄 Detailed test report saved: {filepath}")
        return filepath
    except Exception as e:
        print(f"❌ Failed to save test report: {e}")
        return None


def main():
    """Main test execution"""
    print("🚀 Greeum v2.0.5 Comprehensive Test Suite")
    print("="*60)
    print("Testing new features: UsageAnalytics, QualityValidator, DuplicateDetector, EnhancedToolSchema")
    print("="*60)
    
    # Check module availability
    if not check_module_availability():
        print("\n❌ Cannot proceed - missing required modules")
        return 1
    
    # Initialize test tracking
    test_result = TestResult()
    test_result.start_time = time.time()
    
    # Define test suites to run
    test_suites = [
        (TestUsageAnalytics, "UsageAnalytics"),
        (TestUsageAnalyticsIntegration, "UsageAnalytics_Integration"),
        (TestQualityValidator, "QualityValidator"),
        (TestQualityValidatorIntegration, "QualityValidator_Integration"),
        (TestDuplicateDetector, "DuplicateDetector"),
        (TestDuplicateDetectorIntegration, "DuplicateDetector_Integration"),
        (TestEnhancedToolSchema, "EnhancedToolSchema"),
        (TestEnhancedToolSchemaIntegration, "EnhancedToolSchema_Integration"),
        (TestV205Integration, "V205_Integration")
    ]
    
    # Run all test suites
    for test_class, module_name in test_suites:
        try:
            result, duration = run_test_suite(test_class, module_name, verbose=False)
            test_result.add_result(module_name, result, duration)
        except Exception as e:
            print(f"❌ Failed to run {module_name} tests: {e}")
            # Create dummy failed result
            dummy_result = type('DummyResult', (), {
                'testsRun': 1, 'failures': [('Error', str(e))], 'errors': []
            })()
            test_result.add_result(module_name, dummy_result, 0)
    
    test_result.end_time = time.time()
    test_result.calculate_performance_metrics()
    
    # Run performance analysis
    performance_passed = run_performance_analysis()
    
    # Generate coverage report
    generate_coverage_report(test_result)
    
    # Print final summary
    print(f"\n{'='*60}")
    print("FINAL TEST SUMMARY")
    print(f"{'='*60}")
    
    summary = test_result.get_summary()
    print(f"📊 Overall Results:")
    print(f"  Total tests: {summary['total_tests']}")
    print(f"  Failures: {summary['total_failures']}")
    print(f"  Errors: {summary['total_errors']}")
    print(f"  Success rate: {summary['overall_success_rate']:.1f}%")
    print(f"  Total duration: {summary['performance_metrics']['total_duration_seconds']:.2f}s")
    print(f"  Tests per second: {summary['performance_metrics']['tests_per_second']:.1f}")
    
    print(f"\n🎯 Status: {summary['status']}")
    
    if summary['status'] == 'PASSED':
        print("🎉 All tests passed! Greeum v2.0.5 features are ready for production.")
    else:
        print("⚠️  Some tests failed. Review the issues above before deployment.")
    
    print(f"\n✅ Features tested:")
    for area in summary['coverage_areas']:
        print(f"  • {area}")
    
    # Save detailed report
    save_test_report(test_result)
    
    # Return appropriate exit code
    return 0 if summary['status'] == 'PASSED' else 1


if __name__ == '__main__':
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n🛑 Tests interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)