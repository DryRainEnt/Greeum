# Greeum v2.0.5 Test Suite

Comprehensive unit and integration tests for the new v2.0.5 features.

## Overview

This test suite provides comprehensive coverage for the four major new modules in Greeum v2.0.5:

1. **UsageAnalytics** - Usage pattern analysis and monitoring system
2. **QualityValidator** - Memory-efficient content analysis and quality scoring  
3. **DuplicateDetector** - Smart duplicate detection with similarity algorithms
4. **EnhancedToolSchema** - Enhanced MCP tool schemas with usage guidance

## Test Files

### Unit Tests
- `test_usage_analytics.py` - Tests for UsageAnalytics class (database operations, event logging, session management)
- `test_quality_validator.py` - Tests for QualityValidator class (content analysis, quality scoring, edge cases)
- `test_duplicate_detector.py` - Tests for DuplicateDetector class (similarity detection, batch processing, performance)
- `test_enhanced_tool_schema.py` - Tests for EnhancedToolSchema class (schema generation, parameter validation)

### Integration Tests
- `test_v205_integration.py` - End-to-end integration tests and performance benchmarks

### Test Runner
- `run_v205_tests.py` - Comprehensive test runner with detailed reporting
- `README_v205_tests.md` - This documentation file

## Running Tests

### Quick Test Run
```bash
# Run all v2.0.5 tests
cd /Users/dryrain/DevRoom/Greeum/tests
python run_v205_tests.py
```

### Individual Module Tests
```bash
# Test specific modules
python test_usage_analytics.py
python test_quality_validator.py
python test_duplicate_detector.py
python test_enhanced_tool_schema.py
python test_v205_integration.py
```

### Using unittest directly
```bash
# Run with unittest module
python -m unittest test_usage_analytics -v
python -m unittest test_quality_validator -v
# etc.
```

## Test Coverage

### UsageAnalytics Tests (60+ tests)
- **Database Operations**: Schema creation, path validation, data cleanup
- **Event Logging**: Input sanitization, event recording, error handling
- **Session Management**: Session lifecycle, statistics calculation, analytics generation
- **Performance**: Thread safety, concurrent operations, memory usage
- **Security**: Input validation, SQL injection prevention, path traversal protection

### QualityValidator Tests (45+ tests)  
- **Content Analysis**: Length assessment, content richness, structural quality, language quality
- **Quality Scoring**: Multi-factor scoring, importance adjustment, level classification
- **Edge Cases**: Unicode handling, large content, special characters, empty content
- **Recommendations**: Suggestion generation, warning creation, improvement hints
- **Performance**: Memory efficiency, processing speed, batch validation

### DuplicateDetector Tests (40+ tests)
- **Similarity Detection**: Hash matching, text similarity, semantic similarity, exact duplicates
- **Performance Optimization**: Context windowing, batch processing, memory efficiency
- **Algorithm Testing**: Threshold classification, fallback mechanisms, error recovery
- **Statistical Analysis**: Duplicate rates, trend analysis, recommendations
- **Integration**: Database integration, embedding search, keyword fallback

### EnhancedToolSchema Tests (35+ tests)
- **Schema Generation**: All 10 MCP tools, parameter validation, default values
- **Usage Guidance**: Workflow hints, best practices, error prevention
- **Integration**: MCP compatibility, JSON serialization, tool relationships
- **Documentation**: Comprehensive descriptions, usage examples, parameter guides
- **Validation**: Enum values, required fields, type constraints

### Integration Tests (25+ tests)
- **End-to-End Workflows**: Complete memory addition, quality + duplicate flow, MCP simulation
- **Error Handling**: Graceful degradation, error recovery, comprehensive logging
- **Performance**: Load testing, benchmark validation, resource usage optimization
- **Real-world Scenarios**: Batch processing, concurrent operations, schema-driven workflows

## Test Metrics and Benchmarks

### Performance Requirements
- **UsageAnalytics**: >500 events/second logging, <1s statistics generation
- **QualityValidator**: >100 validations/second, <50MB memory usage
- **DuplicateDetector**: >50 checks/second, efficient similarity algorithms
- **Integration**: >15 complete workflows/second end-to-end

### Coverage Targets
- **Unit Test Coverage**: >90% for each module
- **Integration Coverage**: End-to-end workflows for all major features
- **Error Coverage**: All exception paths and edge cases tested
- **Performance Coverage**: Load testing and resource usage validation

## Test Results and Reporting

### Output Files
- `results/greeum_v205_test_report_YYYYMMDD_HHMMSS.json` - Detailed test results
- Console output with color-coded success/failure indicators
- Performance benchmarks and optimization recommendations

### Success Criteria
- **All unit tests pass** (>95% success rate required)
- **Integration tests pass** (end-to-end workflows functional)
- **Performance benchmarks met** (processing speed requirements)
- **No memory leaks** (resource usage within limits)
- **Error handling verified** (graceful degradation confirmed)

## Debugging Failed Tests

### Common Issues
1. **Database Path Errors**: Ensure test has write permissions to temp directory
2. **Import Errors**: Verify all v2.0.5 modules are properly installed
3. **Performance Failures**: Check system resources during test execution
4. **Mock Configuration**: Verify mock objects are properly configured

### Debug Commands
```bash
# Run with verbose output
python run_v205_tests.py --verbose

# Run specific failing test
python -m unittest test_usage_analytics.TestUsageAnalytics.test_specific_method -v

# Check module imports
python -c "from greeum.core.usage_analytics import UsageAnalytics; print('OK')"
```

## Development Guidelines

### Adding New Tests
1. Follow existing test patterns and naming conventions
2. Include both positive and negative test cases
3. Test edge cases and error conditions
4. Add performance benchmarks for critical operations
5. Update this README with new test coverage

### Test Data
- Use realistic test data that represents actual usage scenarios
- Include multilingual content (Korean, English, etc.)
- Test with various content lengths and types
- Include edge cases (empty, very long, special characters)

### Mocking Strategy
- Mock external dependencies (database, network calls)
- Use realistic mock data that represents actual system behavior
- Test both success and failure scenarios
- Verify mock calls and parameter validation

## Continuous Integration

These tests are designed to run in CI/CD environments:

- **No external dependencies** (all mocked appropriately)
- **Deterministic results** (no random or time-dependent behavior)
- **Fast execution** (complete suite runs in <60 seconds)
- **Clear reporting** (JSON output suitable for CI parsing)
- **Exit codes** (0 for success, non-zero for failures)

## Maintenance

### Regular Updates
- Update test data as new features are added
- Adjust performance benchmarks based on system improvements
- Add regression tests for any bugs discovered
- Keep mock data synchronized with actual system behavior

### Version Compatibility
- Tests are specifically designed for Greeum v2.0.5
- May require updates for future versions
- Backward compatibility testing included where appropriate

---

**Last Updated**: 2025-07-31
**Test Suite Version**: 1.0.0
**Compatible with**: Greeum v2.0.5+