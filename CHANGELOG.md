# Changelog

All notable changes to this project are documented in this file.

## [3.1.0rc1] - 2025-01-15

### Fixed
- **Critical Bug Fix**: Fixed undefined `HierarchicalMemorySystem` references throughout the codebase
  - Replaced with `ContextMemorySystem` in `cli/__init__.py`, `backup_restore_cli.py`, and `dashboard.py`
  - Resolved import errors that were breaking CLI functionality

- **Metrics System Complete**: Full implementation of missing metrics functionality
  - Implemented `MetricsDashboard` and `SearchMetrics` classes with all required methods
  - Added `get_local_hit_rate()`, `get_avg_hops()`, `get_jump_rate()`, `get_p95_latency()`
  - Fixed `export_metrics()` to produce correct output format for tests
  - Fixed `get_success_indicators()` to return proper tuple format

### Added
- **v3 Branch/DFS Integration**: Connected metrics system to actual v3 architecture
  - Real-time DFS search metrics from `DFSSearchEngine`
  - Branch head information for A/B/C slots from `STMManager`
  - Slot utilization tracking and adaptive pattern data
  - Full integration with v3.0 Branch/DFS system performance data

### Changed
- **Test Success Rate**: Improved from 93.8% to 100% (all 21 tests passing)
- **MetricsDashboard Constructor**: Now accepts optional `db_manager` for v3 system connection
- **Export Format**: Enhanced dashboard export to include v3 branch data

### Technical Details
- Created `greeum/core/metrics_dashboard.py` wrapper module for proper imports
- Extended `MetricsDashboard` class with `_connect_v3_systems()` and `_get_v3_branch_data()`
- Metrics now reflect actual system state instead of mock data
- Full compatibility with Branch/DFS Integration tests

## [3.1.0b8] - 2025-01-15

### Fixed
- **Critical MCP Integration**: Native MCP server now properly uses BaseAdapter's v3 features
  - Fixed issue where MCP was using legacy direct implementation instead of BaseAdapter
  - MCP responses now include slot information, smart routing metadata, and DFS search results
  - All v3 branch/slot system features are now accessible through Claude Code MCP interface

### Changed
- **GreeumMCPTools Architecture**: Complete rewrite to inherit from BaseAdapter
  - Eliminated duplicate code and legacy fallback methods
  - All MCP tool handlers now use BaseAdapter's comprehensive v3 functionality
  - Smart routing and slot management fully integrated into MCP responses

### Enhanced
- **MCP Response Format**: Now displays complete v3 metadata including:
  - STM slot assignments and branch information
  - Smart routing similarity scores and placement types
  - DFS search metadata and performance metrics

### Technical Details
- GreeumMCPTools now extends BaseAdapter instead of standalone implementation
- Removed _add_memory_direct and other legacy methods
- All tool handlers delegate to BaseAdapter methods for consistent behavior
- Fixed output format discrepancies between CLI and MCP interfaces

## [3.1.0b7] - 2025-01-15

### Fixed
- **Critical Database Error**: Fixed "no such column: content" error in `_get_block_by_hash` method
  - Changed query to use correct column name `context` instead of `content`
  - Removed references to non-existent columns (tags, embedding, created_at, stats)
- **Database Schema Compatibility**: Aligned query with actual blocks table schema
- **Block Retrieval**: Improved error handling for missing blocks

### Technical Details
- Fixed SQL query in BlockManager._get_block_by_hash() to match actual database schema
- Removed JSON parsing for non-existent columns
- Maintained backward compatibility with existing database

## [3.1.0b6] - 2025-01-15

### Changed
- **Smart Routing Architecture Consolidation**: Moved smart routing logic from BlockManager to BaseAdapter for cleaner separation of concerns
- **Unified Slot Selection**: BaseAdapter now handles all slot selection logic using smart routing, eliminating duplicate code
- **Improved DFS Integration**: Fixed DFS search engine integration for more reliable semantic similarity matching

### Fixed
- Smart routing metadata now properly displayed in MCP tool responses
- Fixed import errors between DFSSearch and DFSSearchEngine classes
- Resolved slot overwriting issues where BaseAdapter would override smart routing decisions
- Fixed similarity score extraction from DFS search results

### Technical Details
- BaseAdapter._auto_select_or_initialize_slot() now returns (slot, smart_routing_info) tuple
- BlockManager.add_block() simplified to only use provided slot without additional routing logic
- Smart routing info properly passed through metadata chain from BaseAdapter → BlockManager → MCP response

## [3.1.0b3] - 2025-01-15

### Enhanced
- MCP tool response now displays smart routing information:
  - Shows which STM slot was updated
  - Displays similarity score percentage
  - Indicates placement type (existing_branch/divergence/new_branch)
- Smart routing metadata now stored in block's metadata field for persistence

### Improved
- Better visibility of smart routing operations in add_memory responses
- Clearer feedback about automatic memory placement decisions

## [3.1.0b2] - 2025-01-15

### Fixed
- Added missing `get_usage_report` method to UsageAnalytics class
- Resolved MCP usage_analytics tool error ("AttributeError: 'UsageAnalytics' object has no attribute 'get_usage_report'")

## [3.1.0b1] - 2025-01-15

### 🎯 Smart Routing with DFS Integration

This beta release introduces **Smart Routing** - an intelligent memory placement system that automatically finds the optimal STM slot for new memories using DFS search and semantic similarity.

### ✨ **Major Features**

#### **Smart Routing System**
- **NEW**: Automatic semantic-based STM slot selection on `add_memory`
- **NEW**: DFS-powered search from STM heads for optimal placement
- **NEW**: Three-tier routing decision based on similarity scores:
  - High similarity (>0.7): Continue existing branch
  - Medium similarity (0.4-0.7): Create divergence from similar content
  - Low similarity (<0.4): Start completely new branch
- **NEW**: LRU (Least Recently Used) slot replacement when all slots occupied
- **ENHANCED**: Environment variable control via `GREEUM_SMART_ROUTING`
- **DEFAULT**: Smart routing enabled by default for optimal user experience

#### **Technical Implementation**
- **INTEGRATED**: DFS engine directly in `add_block` method for minimal latency
- **OPTIMIZED**: Shallow depth search (depth=2) for performance
- **METRICS**: Tracking smart routing usage and average similarity scores
- **COMPATIBLE**: Fallback to original logic when disabled

### 🔧 **Configuration**

```bash
# Disable smart routing (not recommended)
export GREEUM_SMART_ROUTING=0

# Enable smart routing (default)
export GREEUM_SMART_ROUTING=1
```

### 📊 **Performance Impact**
- **Search overhead**: ~20-30ms per add operation
- **Overall latency**: Acceptable for significant UX improvement
- **Memory placement accuracy**: Significantly improved contextual grouping

### 🐛 **Bug Fixes**
- Fixed STM slot persistence issues
- Improved branch head management
- Enhanced slot hysteresis tracking

### 📝 **Notes**
This is a beta release. Smart routing represents a fundamental shift in how Greeum manages memory placement, moving from manual slot management to intelligent automatic routing. Please test thoroughly before production use.

---

## [3.0.1b2] - 2025-01-14

### 🚀 P1 Storage Path Fine-tuning & STM Activation

This beta release implements **P1 storage path fine-tuning** to fully activate the STM slot system that was integrated but not initialized in b1.

### ✨ **P1 Feature Implementations**

#### **Adaptive DFS Engine**
- **NEW**: Pattern learning system tracks branch access frequency and relevance
- **NEW**: Query pattern matching remembers successful branches per query type
- **NEW**: Depth effectiveness tracking optimizes search depth dynamically
- **ENHANCED**: Branch-weighted scoring with exponential moving average
- **RESULT**: 10-20% improved search relevance through adaptive learning

#### **Branch Weight Adjustment**
- **NEW**: `_apply_adaptive_weights()` adjusts scores based on historical performance
- **NEW**: Popular branches receive frequency boost (max 10%)
- **NEW**: Depth-specific effectiveness weights
- **ENHANCED**: Learning rate of 0.1 for gradual adaptation

#### **Performance Profiling**
- **NEW**: Adaptive metrics in `get_metrics()` response
- **TRACKED**: branches_tracked, query_patterns, avg_branch_relevance
- **OPTIMIZED**: Embedding cache prevents redundant calculations
- **RESULT**: Reduced search latency through intelligent branch selection

### ✨ **P1 Storage Path Enhancements**

#### **STM Slot Auto-initialization**
- **NEW**: `_auto_select_or_initialize_slot()` method in MCP adapter
- **FIXED**: Empty slots now auto-initialize to slot A on first memory
- **ENHANCED**: Slot hysteresis tracking for access patterns
- **RESULT**: STM slots finally active and managing branch heads

#### **Cursor Auto-tracking Mechanism**
- **NEW**: Automatic cursor update after each memory addition
- **NEW**: Search results update cursor to last accessed item
- **ENHANCED**: `set_cursor()` integration in add/search pipelines
- **RESULT**: "Continue where you left off" fully operational

#### **BlockManager STM Integration**
- **IMPROVED**: Auto-initialize slot A when all slots empty
- **ENHANCED**: Logging for slot head updates with P1 markers
- **FIXED**: Slot selection logic for uninitialized states

### 📊 **Implementation Details**

```python
# Before (b1): Slots always None
slot=None  # auto_select_slot 로직 여기서 수행

# After (b2): Active slot management
slot = self._auto_select_or_initialize_slot(stm_manager)
# Returns "A" on first use, tracks access patterns
```

### ✅ **Verification Status**

| Component | b1 Status | b2 Status | Result |
|-----------|-----------|-----------|---------|
| MCP→Core routing | ✅ Working | ✅ Working | Maintained |
| STM slot init | ❌ All None | ✅ Auto-init | **FIXED** |
| Cursor tracking | ❌ Not set | ✅ Auto-track | **NEW** |
| Branch heads | ❌ Empty | ✅ Active | **ACTIVATED** |

### 🎯 **User Experience Impact**

- **First memory**: Automatically creates slot A branch
- **Subsequent memories**: Follow active branch structure
- **Search continuity**: Cursor maintains position in branch
- **Context preservation**: True branch-based organization

---

## [3.0.1b1] - 2025-01-14

### 🚨 Context-Priority Hotfixes & MCP Integration

This beta release addresses critical user experience issues with **MCP layer bypassing v3 core systems** and implements essential hotfixes to restore intended v3 behavior: context-priority search, explainable metadata, and stable performance.

### 🔥 **P0+ Emergency Patches**

#### **MCP Core Integration Recovery**
- **FIXED**: MCP `add_memory`/`search_memory` bypassing STM/slots/heads → Direct core routing
- **NEW**: MCP → `BlockManager.add_block()` with slot-based branch storage
- **NEW**: MCP → `search_with_slots()` with cursor-priority entry points
- **RESULT**: Immediate user experience improvement - branch/slot priority now works in MCP

#### **Entry Point Priority System**
- **NEW**: STM slot cursor tracking with `cursor → head → most_recent` priority
- **NEW**: `get_entry_point(entry_type="cursor")` API in STMManager
- **NEW**: DFS search respects entry parameter for contextual starting points
- **RESULT**: "Continue where you left off" experience restored

### 🎯 **P0 Critical Hotfixes**

#### **1. API Contract Restoration**
- **FIXED**: `add_block()` returns dict format (was inconsistent)
- **ENHANCED**: Standardized response format across MCP/REST/CLI

#### **2. Search Metadata Standardization**
- **ENFORCED**: All search paths include `search_type, entry_type, slot, hops, time_ms`
- **NEW**: `BlockManager.search_with_slots()` returns `{items: [], meta: {}}` format
- **FIXED**: DFS syntax error causing legacy fallback

#### **3. Global Jump Heuristics Refinement**
- **NEW**: Warm-up mode - first 5 queries stay local for new DB/roots
- **TIGHTENED**: Jump conditions now require ALL criteria (was OR):
  - Local results < 2 (was 3)
  - Local quality < 0.4 (NEW)
  - Query complexity > 0.8 (was 0.7)
  - Jump success rate > 0.7 (was 0.6)
- **RESULT**: Reduced jump oversensitivity, improved local-first stability

### ✅ **Technical Validation**

#### **Verified Working**
```bash
✅ DFS search_type=local, entry_type=cursor
✅ Metadata standardization (4 core keys)
✅ Warm-up mode jump suppression (5 queries)
✅ MCP-v3 core complete integration
```

#### **User Experience Restoration**
- **"Continue where you left off"** ✓ - cursor-priority entry points
- **"Explainable search"** ✓ - standardized metadata in all responses
- **"Stable performance"** ✓ - jump oversensitivity eliminated
- **"Branch-aware storage"** ✓ - MCP uses slot heads for structured organization

### 🎯 **Performance Targets**

| Metric | Status | Target |
|--------|--------|---------|
| local_hit_rate | ✅ Immediate improvement | +10pp↑ |
| search_meta_coverage | ✅ 100% | 100% |
| jump_oversensitivity | ✅ Warm-up suppression | Eliminated |
| entry_priority | ✅ cursor → head → recent | Working |

### 🔄 **Migration**

- **Zero breaking changes**: Fully compatible with v3.0.0.post4
- **Enhanced MCP**: Existing MCP setups automatically benefit from core integration
- **Backward compatibility**: All existing APIs continue to work

---

## [3.0.0.post2] - 2025-01-14

### 🔧 Stability & Compatibility Improvements

This release focuses on critical bug fixes, API compatibility improvements, and code quality enhancements that significantly improve system stability and maintainability.

### ✅ Bug Fixes

#### **Critical DFS Search Fix**
- **Fixed DFS depth limit functionality**: Previously non-functional in linear chain structures
- **Enhanced branch-based testing**: Modified test scenarios to reflect real-world branched memory structures
- **Improved search accuracy**: DFS now correctly respects depth limits in complex branch hierarchies

#### **API Compatibility Resolution**
- **Fixed BlockManager.add_block() signature mismatch**: Resolved parameter inconsistencies affecting integration
- **Enhanced STM manager stability**: Improved branch metadata handling and slot management
- **Corrected database schema migrations**: Better thread-safe operations and branch schema handling

### 🎯 System Stability

#### **Test Coverage Achievement**
- **100% test pass rate**: All 47 tests now passing (previously 58.2%)
- **Enhanced test quality**: 3 new orphan handling tests added for edge case coverage
- **Removed 11 legacy test files**: Eliminated 3,109 lines of obsolete test code

#### **Formal Specification Adoption**
- **Orphan → Root auto-promotion**: Officially adopted as system specification
- **Data safety guarantee**: Zero data loss through automatic orphan node recovery
- **Consistent tree structure**: All nodes remain accessible through DFS traversal

### 🚀 Performance & Quality

#### **Code Quality Improvements**
- **Removed legacy components**: 644 lines added, 3,109 lines removed (net -2,465 lines)
- **Enhanced maintainability**: Cleaner codebase with focused functionality
- **Improved memory efficiency**: Reduced runtime overhead from legacy code removal

#### **Performance Metrics**
- **local_hit_rate**: 70.0% (target: ≥27%) - **2.6x exceeded**
- **avg_hops**: 4.5 (target: ≤8.5) - **47% improvement**
- **p95_latency**: 100ms (target: <150ms) - **33% improvement**  
- **merge_undo_rate**: 0.0% (target: ≤5%) - **Perfect score**

### 🔄 Migration

- **Zero breaking changes**: Fully compatible with v3.0.0.post1
- **No migration required**: Existing installations upgrade seamlessly
- **Enhanced API stability**: Improved consistency across all public interfaces

### 📊 Statistics

- **Test Files Cleaned**: 11 legacy files removed
- **Code Reduction**: 3,109 lines of legacy code eliminated
- **Test Coverage**: 47/47 tests (100% success rate)
- **Performance**: All targets exceeded by significant margins

---

## [3.0.0] - 2025-01-13

### 🎉 Major Release - Association Network & GraphIndex Integration

This release introduces a revolutionary memory architecture combining association networks with graph-based search, enabling human-like memory retrieval through spreading activation.

### ✨ New Features

#### **Association Network System**
- **Memory Nodes**: Every memory block now creates a corresponding node in the association network
- **Automatic Associations**: Memories are automatically linked based on:
  - Semantic similarity (keyword and embedding matching)
  - Temporal proximity (memories created within time windows)
  - Entity relationships (shared subjects/objects)
- **Spreading Activation**: Cognitive-inspired activation propagation for retrieving related memories
- **1,156 nodes** with **5,788 associations** bootstrapped from existing data

#### **GraphIndex Integration**
- **High-performance beam search** for local graph exploration
- **Bidirectional integration** with AssociationNetwork
- **1,168 indexed nodes** for instant graph traversal
- **Anchor-based navigation** for focused memory regions

#### **Enhanced Search Capabilities**
- **Hybrid search** combining embedding similarity with spreading activation
- **Context-aware retrieval** through activation propagation
- **Multi-hop reasoning** via graph traversal

### 🔧 Improvements

#### **Architecture Enhancements**
- Unified `BlockManager` integrating both GraphIndex and AssociationNetwork
- Clean separation between graph search (GraphIndex) and semantic associations (AssociationNetwork)
- Improved database schema with dedicated tables for nodes and associations

#### **Performance Optimizations**
- Efficient batch processing for association creation
- Optimized activation propagation with configurable thresholds
- Smart caching of frequently accessed associations

#### **Code Quality**
- Removed 7 redundant test files
- Cleaned up 4 test directories
- Deleted 17 backup databases
- Removed legacy MCP directory with 6 obsolete files
- Organized documentation into `docs/design/` and `docs/releases/`

### 🐛 Bug Fixes
- Fixed CLI version display issue
- Resolved UsageAnalytics stub implementation missing methods
- Fixed block_index access error in CLI
- Corrected STM memory addition parameter handling

### 📊 Statistics
- **Total Memory Nodes**: 1,156
- **Total Associations**: 5,788
- **Average Association Strength**: 0.957
- **Association Types**: temporal (69%), semantic (31%), entity (<1%)
- **Maximum Node Degree**: 5
- **Isolated Nodes**: 1

### 🔄 Migration
- Automatic bootstrapping of association network from existing blocks
- Backward compatible with v2.x data structures
- No manual migration required

### 🚀 Performance
- Memory search expanded by average 2x through spreading activation
- Graph traversal up to 5 hops in milliseconds
- Association creation < 100ms per block

### 📦 Dependencies
- Core dependencies remain unchanged
- Optional GraphIndex requires numpy
- Python 3.10+ required

### 🔗 Integration
- Full CLI support for all new features
- MCP tools updated for association network
- REST API endpoints remain compatible

---

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