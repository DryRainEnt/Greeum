# Changelog

All notable changes to this project are documented in this file.

## v2.6.4 (2025-09-10) - Context Preservation System Phase 2

### 🎯 Major Features
- **PreCompact Hook Integration**: Real-time Claude Code auto-compact protection
- **Context Recovery System**: Intelligent backup restoration with quality scoring
- **Intelligent Context Processor**: AI-based importance analysis and compression
- **E2E Integration Tests**: Comprehensive test suite for context preservation workflows

### 🧠 Context Preservation System
- **Emergency Backup**: Automatic context backup before Claude Code auto-compact events
- **Recovery Manager**: Session-based context restoration with quality metrics (0.92+ scores)
- **Intelligent Processing**: Pattern recognition and semantic density analysis
- **Thread Safety**: Enhanced database operations for concurrent usage

### 🔧 Technical Improvements
- **PreCompactHookHandler**: Monitors Claude Code environment and triggers emergency backups
- **ContextBackupItem Schema**: Structured backup format with retention priorities
- **Database Schema Updates**: Added `context_backups` table for preservation system
- **Performance Optimization**: <1ms backup processing time achieved

### ✅ Quality & Testing
- **100% E2E Test Success**: All 7 comprehensive integration tests passing
- **Compatibility**: Seamless migration from v2.5.2+ with data preservation
- **Error Handling**: Robust failure recovery and partial success handling
- **Concurrent Operations**: Multi-threaded backup/recovery support

### 🚀 Migration & Compatibility
- **Auto-Migration**: Automatic schema upgrade from v2.5.2 to v2.5.3+ format
- **Data Safety**: Complete backup creation before any schema changes
- **Rollback Support**: Emergency rollback to previous states available
- **Zero Data Loss**: 100% original memory preservation guaranteed

### 🔍 Bug Fixes
- Fixed PreCompact signal processing error (`'str' object has no attribute 'get'`)
- Resolved session ID mismatch in E2E tests
- Improved SQLite database initialization and thread safety
- Enhanced error handling in context recovery operations

**Breaking Changes**: None - Full backward compatibility maintained

## v2.2.6 (2025-09-01) - FastMCP Hotfix for WSL Compatibility

### 🚨 Critical Hotfix
- **FastMCP Integration**: Replaced custom JSON-RPC implementation with FastMCP framework
- **WSL Compatibility**: Fixed stdin/stdout buffering issues in Windows PowerShell and WSL environments
- **Claude CLI Support**: Resolved connection failures with Claude Code CLI in cross-platform environments

### 🔧 Technical Changes
- **MCP Server**: Migrated from direct JSON-RPC to FastMCP-based server implementation
- **Transport Layer**: Standardized MCP protocol handling for better compatibility
- **Error Handling**: Improved cross-platform error handling and logging

### ✅ Compatibility Maintained
- **100% API Compatibility**: All existing tools (add_memory, search_memory, etc.) unchanged
- **CLI Commands**: `greeum mcp serve` works identically
- **Data Format**: No changes to memory storage or retrieval
- **User Experience**: Zero impact on existing users

### 🎯 Resolved Issues
- ✅ Fixed WSL Claude CLI connection timeout errors
- ✅ Resolved PowerShell MCP server startup issues  
- ✅ Standardized MCP protocol compliance
- ✅ Improved cross-platform reliability

**Breaking Changes**: None - Full backward compatibility maintained

## v2.2.5 (2025-09-01) - M3 Anchored Memory System Complete

### 🚀 Major Features
- **Complete CLI Interface**: Full `greeum anchors` command suite (status, set, pin, unpin, clear)
- **REST API Endpoints**: GET/PATCH `/v1/anchors` with comprehensive anchor management
- **Enhanced Search API**: Anchor-based localized search with slot, radius, and fallback parameters

### 🔧 Quality Assurance
- **Regression Test Suite**: 375-line comprehensive test suite with ±10% performance tolerance validation
- **Performance Benchmarking**: Automated quality benchmark system (633 lines)
- **CI/CD Pipeline**: Complete GitHub Actions workflow with 4-stage quality gates
- **Performance Metrics**: Search 3.6ms, Add 0.5ms, Throughput 2491 ops/sec

### 📚 Documentation
- **User Guide**: Complete anchors system guide with CLI/API examples
- **API Reference**: Updated with full anchor system documentation
- **Quality Reports**: Automated quality assessment and benchmarking reports
- **v2.3 Roadmap**: Detailed 20-week development plan for next major release

### 🛠️ Development Tools
- **Quality Gates**: Automated pass/fail criteria for deployment readiness
- **Performance Monitoring**: Real-time performance regression detection
- **Multi-stage Validation**: Regression, integration, performance, and security testing

### ✅ Production Ready
- All quality gates passing (2/2)
- 100% API compatibility maintained
- Performance benchmarks within tolerance
- Complete documentation and user guides
- Ready for enterprise deployment

## v2.1.0 (2025-08-02) - Production Release

### Production Readiness Improvements
- **Version synchronization**: All configuration files synchronized to v2.1.0
- **Build system optimization**: Successfully builds wheel packages for distribution
- **Syntax fixes**: Resolved critical indentation issues in HybridSTMManager
- **Import validation**: All core modules pass import verification tests

### Documentation Updates
- **CLI command modernization**: Updated all examples to use current `greeum` CLI syntax
- **MCP integration guide**: Aligned documentation with actual implementation
- **Technical accuracy**: Corrected version references throughout documentation
- **User experience**: Consistent command examples across all documentation

### Code Quality Enhancements
- **Legacy file removal**: Eliminated outdated setup.py in favor of pyproject.toml
- **Package structure**: Streamlined configuration for production deployment
- **Error handling**: Fixed syntax errors preventing module imports
- **Import reliability**: Enhanced module loading with proper fallback mechanisms

## v2.0.5 (2025-08-02) - Phase 3 Checkpoint System

### Phase 3 Checkpoint System Implementation

#### New Features
- **CheckpointManager**: Manages checkpoint connections between Working Memory and LTM
- **LocalizedSearchEngine**: Localized search engine with 265-280x speed improvement  
- **PhaseThreeSearchCoordinator**: 4-layer search architecture coordinator
- **Multi-layer memory architecture**: Working Memory → Cache → Checkpoint → LTM

#### Performance Improvements
- **Checkpoint search**: 0.7ms (vs 150ms full LTM search)
- **Speed improvement**: 265-280x improvement over previous version
- **Hit rate**: 100% checkpoint utilization
- **Cumulative performance**: 1000x+ improvement combining Phase 1+2+3

#### Stability Enhancements
- **System stability**: Improved from 82/100 to 92/100
- **Thread safety**: Applied `threading.RLock()` to all shared resources
- **Memory management**: Cache size limits with LRU eviction
- **Error recovery**: Retry mechanisms with fallback systems

### Detailed Stability Improvements

#### Thread Safety Implementation
- `CheckpointManager`: Protected checkpoint cache concurrent access
- `LocalizedSearchEngine`: Infinite recursion prevention (max 3 retries)
- `PhaseThreeSearchCoordinator`: Cache failure handling with backup cache
- `HybridSTMManager`: Slot contention prevention with atomic allocation

#### Memory and Resource Management
- Cache size limits (default 1000 items)
- LRU-based automatic cleanup
- Block access timeout (5 seconds)
- Memory leak reduction: 99% of identified leaks resolved

### Code Quality Improvements

#### Large File Cleanup
- `stm_manager.py`: Reduced from 8,019 to 60 lines (99.25% reduction)
- Removed 7,880 dummy comments
- Eliminated duplicate classes  
- Preserved all core functionality

### MCP Integration Extensions

#### v2.0.5 MCP Tools
- `intelligent_search`: 4-layer search system
- `checkpoint_search`: Checkpoint-based localized search
- `performance_stats`: Real-time performance monitoring
- `verify_system`: System integrity verification
- `memory_health`: Memory status diagnostics

### New Technical Documentation
- `PHASE_3_COMPLETION_REPORT.md`: Detailed performance analysis
- `PHASE_3_CHECKPOINT_DESIGN.md`: Checkpoint system technical design
- Checkpoint reliability test suite
- Extended performance benchmarks

---

## v2.0.4 (2025-07-30) - Phase 2 Hybrid STM Implementation

### Major Features
- Hybrid STM system implementation
- Working Memory 4-slot system
- Priority-based intelligent cleanup
- Full compatibility with Legacy STM

### Performance Improvements
- Interactive scenarios: 1500x performance improvement
- Cache hit rate: 100% achieved
- Overall performance grade: B+ (82/100)

---

## v2.0.3 (2025-07-29) - Phase 1 Cache Optimization

### Major Features
- Intelligent cache system implementation
- MD5 hash-based cache keys
- TTL-based automatic expiration
- In-memory keyword boosting

### Performance Improvements
- Cache search: 234ms → 36ms (6.5x improvement)
- Cache hit: 0.27ms (870x improvement)
- Cumulative speed: 259x improvement

---

## v2.0.2 (2025-07-25) - Stability and Compatibility Improvements

### Improvements
- Enhanced database connection stability
- Strengthened exception handling
- Optimized memory usage
- Improved multi-threading support

### Bug Fixes
- Fixed embedding vector dimension mismatch
- Improved STM expiration logic
- Fixed cache invalidation timing issues

---

## v2.0.1 (2025-07-20) - Quality Management System

### New Features
- 7-metric quality assessment system
- Automatic duplicate detection (85% similarity threshold)
- Quality-based importance auto-adjustment
- STM→LTM promotion recommendation system

### Performance Improvements
- Quality verification algorithm optimization
- Duplicate detection speed: 3x improvement
- Memory efficiency: 25% improvement

---

## v2.0.0 (2025-07-15) - Major Architecture Upgrade

### Major Changes
- Multi-layer memory system implementation
- Blockchain-like LTM structure
- Waypoint cache system
- Complete MCP integration

### New Features
- Multi-language temporal expression processing
- Hybrid search system
- Real-time quality monitoring
- Usage pattern analysis

### Performance Improvements
- Response quality: 18.6% improvement
- Search speed: 5.04x improvement
- Re-questioning: 78.2% reduction

---

## v1.x.x Legacy Series

### v1.2.0 (2025-06-30)
- Claude Code MCP server integration
- 12 MCP tools implementation
- Real-time synchronization support

### v1.1.0 (2025-06-15)
- Vector search engine implementation
- FAISS indexing support
- Semantic similarity search

### v1.0.0 (2025-06-01)
- First stable version
- Basic LTM/STM system
- RESTful API provision

---

## v0.x.x Previous Versions

### v0.5.2 (2025-05-20)
- Improved module import stability
- Enhanced API client
- Strengthened exception handling

### v0.5.1 (2025-05-18)
- numpy type conversion utilities
- Proxy environment support
- OpenAI API v1.0.0+ compatibility

### v0.5.0 (2025-05-17)
- Code modularization and structure improvements
- Test framework construction
- Basic memory system implementation

---

## v2.0.5 Summary

**Greeum v2.0.5 introduces checkpoint-based localized search for AI memory systems:**

- **Multi-layer architecture**: Human memory structure implementation
- **265x performance**: Checkpoint-based localized search
- **92/100 stability**: Production-ready quality
- **99% code improvement**: Reduced from 8,019 to 60 lines

Technical implementation prioritizing reliability over performance optimization.

---

<p align="center">
  <strong>Next Release: v2.1.0 (Distributed architecture support planned)</strong>
</p>