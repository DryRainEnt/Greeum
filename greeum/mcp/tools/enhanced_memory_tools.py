"""
v2.4.0a2 Enhanced Memory Tools - Professional MCP Integration

Core objective: Encourage AI to use memory tools more frequently with smaller memory units
through optimized descriptions that provide clear usage guidance and promote active engagement.
"""

from typing import Dict, List, Any, Optional
import json
import asyncio
from datetime import datetime

# Existing tool imports (removed to prevent circular imports)
# from .enhanced_memory_tools import EnhancedMemoryTools


# MCP server tool functions - description optimized version

async def add_memory_frequent(content: str, importance: float = 0.5) -> str:
    """
    Immediate Memory Storage with Greimas Actant Model: Record all interactions using [Subject-Action-Object] structure
    
    Core Principle: Every work unit has permanent preservation value - prioritize pattern accumulation over importance filtering.
    
    Store immediately at these interaction points:
    - User questions/requests -> [User-Request-SpecificFeature]
    - Claude responses/solutions -> [Claude-Provide-Solution] + detailed answer
    - Tool execution results -> [Claude-Execute-ToolName] + outcome + analysis
    - Problem discovery/resolution -> [Actor-Discover-Issue] + solution process  
    - Task transition points -> [Subject-Transition-NewTask] + context
    - Code changes/implementations -> [Claude-Implement-Feature] + technical details
    - All feedback and improvements -> [Actor-Suggest-Enhancement] + details
    - Analysis results -> [Claude-Analyze-Topic] + findings + conclusions
    
    Storage Pattern Examples:
    - "[User-Request-MCPToolTest] Identify and test connected tools"
    - "[Claude-Provide-Solution] Explained MCP server configuration steps with code examples"
    - "[Claude-Implement-Feature] Added actant analysis to BlockManager with 6-role pattern matching"
    - "[Claude-Discover-TypeScriptError] processId type mismatch in src/types/session.ts"
    - "[Claude-Analyze-Performance] Found 5x speed improvement with new caching strategy"
    - "[User-Suggest-GriemasModel] Apply actant structure for interaction patterns"
    
    Target: 20-30 blocks per session for comprehensive external brain functionality
    
    Args:
        content: Content to store (from single sentences to multiple paragraphs)
        importance: Importance level 0.0-1.0 (casual conversation: 0.3-0.5, important decisions: 0.7-1.0)
    
    Returns:
        Stored memory information (including ID and actant analysis results)
    """
    global enhanced_memory_tools
    
    if not enhanced_memory_tools:
        return json.dumps({"error": "Enhanced memory tools not initialized"})
    
    try:
        # Log analytics event (start time)
        start_time = datetime.now()
        
        # Store original content without micro-splitting (includes actant analysis)
        result = await enhanced_memory_tools.add_memory_micro(
            content=content, 
            importance=importance,
            force_micro_split=False  # No splitting as description guidance is the objective
        )
        
        # Log successful analytics event
        try:
            from greeum.core.usage_analytics import UsageAnalytics
            from greeum.core.database_manager import DatabaseManager
            
            db_manager = DatabaseManager()
            analytics = UsageAnalytics(db_manager=db_manager)
            duration_ms = int((datetime.now() - start_time).total_seconds() * 1000)
            
            analytics.log_event(
                event_type="tool_usage",
                tool_name="add_memory_frequent",
                metadata={"content_length": len(content), "importance": importance},
                duration_ms=duration_ms,
                success=True
            )
            
            # Log quality metrics if available
            if result.get("quality_score"):
                analytics.log_quality_metrics(
                    content_length=len(content),
                    quality_score=result.get("quality_score", 0.0) * 100,
                    quality_level=result.get("quality_level", "unknown"),
                    importance=importance,
                    adjusted_importance=result.get("adjusted_importance", importance),
                    is_duplicate=result.get("is_duplicate", False),
                    duplicate_similarity=result.get("duplicate_similarity", 0.0)
                )
        except Exception as analytics_error:
            # Analytics failure should not affect core functionality
            pass
        
        return json.dumps({
            "status": "success",
            "message": "💾 기억 완료! 작은 정보일수록 자주 저장하면 더 나은 맥락을 구성할 수 있어요.",
            "memory_id": result.get("memory_id"),
            "actant_summary": {
                role: data["entity"] 
                for role, data in result.get("actant_analysis", {}).get("actants", {}).items()
            },
            "encourage_more": "다른 흥미로운 내용이 있다면 바로 또 저장해보세요!"
        }, ensure_ascii=False, indent=2)
        
    except Exception as e:
        return json.dumps({"error": f"메모리 저장 실패: {str(e)}"}, ensure_ascii=False)


async def search_memory_contextual(query: str, limit: int = 8, slot: Optional[str] = None, 
                                  radius: int = 2, fallback: bool = True) -> str:
    """
    Contextual memory search: Find related memories to enrich conversations
    
    Use this tool actively in these situations:
    - When users bring up topics they mentioned before
    - To verify past experiences or preferences related to current conversation
    - To understand previous progress on projects or tasks
    - When discussing user interests or expertise areas
    - To find past solutions or attempts when solving problems
    
    Search tip: You can search not just by keywords, but by emotions, situations, and context.
    Examples: "project", "frustration", "success experience", "interest area", etc.
    
    Enhanced with anchor-based local search (v2.7.0):
    - slot: Use specific memory anchor (A-E) for local graph search
    - radius: Search within N hops from anchor (default 2)
    - fallback: Use global search if local search fails (default True)
    
    Args:
        query: Search content (keywords, topics, emotions, situations, etc.)
        limit: Number of memories to find (default 8 for diverse perspectives)
        slot: Optional anchor slot (A-E) for local graph search
        radius: Search radius from anchor (default 2 hops)
        fallback: Enable fallback to global search (default True)
    
    Returns:
        Related memories with actant analysis and search metadata
    """
    try:
        # Import BaseAdapter to get local database search
        from ..adapters.base_adapter import BaseAdapter
        
        # Create concrete BaseAdapter implementation for local memory search
        class LocalSearchAdapter(BaseAdapter):
            async def run(self):
                pass  # Not used, just satisfying abstract method requirement
        
        adapter = LocalSearchAdapter()
        components = adapter.initialize_greeum_components()
        
        if not components:
            return json.dumps({
                "error": "Failed to initialize Greeum components for local search",
                "suggestion": "Check if memory database exists in current directory"
            })
        
        # Search using local database components
        search_engine = components.get('search_engine')
        block_manager = components.get('block_manager')
        
        results = []
        
        if search_engine and query.strip():
            # Use search engine for semantic search
            try:
                search_results = search_engine.search(query, limit=limit)
                for result in search_results:
                    if isinstance(result, dict):
                        block_info = block_manager.get_block(result.get('block_index'))
                        if block_info:
                            results.append({
                                "memory_id": result.get('block_index'),
                                "content": block_info.get('context', ''),
                                "timestamp": block_info.get('timestamp', ''),
                                "importance": block_info.get('importance', 0.5),
                                "relevance_score": result.get('similarity_score', 0.8)
                            })
                    else:
                        # If result is a block object directly
                        results.append({
                            "memory_id": result.get('block_index') if hasattr(result, 'get') else getattr(result, 'block_index', None),
                            "content": result.get('context', '') if hasattr(result, 'get') else getattr(result, 'context', ''),
                            "timestamp": result.get('timestamp', '') if hasattr(result, 'get') else getattr(result, 'timestamp', ''),
                            "importance": result.get('importance', 0.5) if hasattr(result, 'get') else getattr(result, 'importance', 0.5),
                            "relevance_score": 0.8
                        })
            except Exception as se_error:
                print(f"Search engine failed, falling back to block manager: {se_error}")
                # Fallback to block manager
                pass
        
        # Use block manager with slot/radius options if available
        if not results and block_manager:
            try:
                # Enhanced search with slot and radius parameters
                if hasattr(block_manager, 'search_with_slots'):
                    all_blocks = block_manager.search_with_slots(
                        query, 
                        limit=limit,
                        use_slots=bool(slot),
                        slot=slot,
                        radius=radius,
                        fallback=fallback
                    )
                else:
                    # Fallback to basic search
                    all_blocks = block_manager.search_by_keywords([query], limit=limit)
                    
                for block in all_blocks:
                    result_dict = {
                        "memory_id": block.get('block_index'),
                        "content": block.get('context', ''),
                        "timestamp": block.get('timestamp', ''),
                        "importance": block.get('importance', 0.5),
                        "relevance_score": block.get('relevance_score', 0.6)
                    }
                    
                    # Add search metadata if available
                    if 'search_type' in block:
                        result_dict['search_type'] = block['search_type']
                    if 'hop_distance' in block:
                        result_dict['hop_distance'] = block['hop_distance']
                    if 'slot_used' in block:
                        result_dict['slot_used'] = block['slot_used']
                    if 'graph_used' in block:
                        result_dict['graph_used'] = block['graph_used']
                    if 'fallback_used' in block:
                        result_dict['fallback_used'] = block['fallback_used']
                        
                    results.append(result_dict)
            except Exception as bm_error:
                print(f"Block manager search also failed: {bm_error}")
        
        if not results:
            return json.dumps({
                "status": "no_results",
                "message": f"No memories found related to '{query}'. Store memories more frequently to get richer search results!",
                "suggestion": "Use add_memory_frequent tool to store related content.",
                "note": "Searched in LOCAL directory database"
            }, ensure_ascii=False, indent=2)
        
        # Format search results contextually
        formatted_results = []
        for result in results:
            formatted_results.append({
                "memory_id": result["memory_id"],
                "content": result["content"],
                "timestamp": result["timestamp"],
                "relevance_score": result["relevance_score"],
                "context_value": result["importance"]
            })
        
        return json.dumps({
            "status": "found",
            "message": f"Found {len(results)} memories related to '{query}'! Use this context to enrich conversation.",
            "memories": formatted_results,
            "next_action_suggestion": "Store new information related to these memories using add_memory_frequent!",
            "note": "Results from LOCAL directory database"
        }, ensure_ascii=False, indent=2)
        
    except Exception as e:
        return json.dumps({
            "error": f"Memory search failed: {str(e)}",
            "suggestion": "Ensure Greeum is properly installed and database exists in current directory"
        }, ensure_ascii=False)


async def check_memory_freshness() -> str:
    """
    Memory freshness check: Review recent memory status and encourage frequent storage
    
    Use this tool when:
    - Starting conversations to understand recent context
    - Revisiting old topics to verify latest information  
    - When memory storage frequency feels low for status check
    - Checking recent progress on important projects or tasks
    
    Usage tip: Use this information to immediately supplement any gaps in memory.
    """
    try:
        # Import BaseAdapter to get local database statistics
        from ..adapters.base_adapter import BaseAdapter
        from datetime import datetime, timedelta
        
        # Create a concrete BaseAdapter implementation for local memory statistics
        class LocalGreaumAdapter(BaseAdapter):
            async def run(self):
                pass  # Not used, just satisfying abstract method requirement
        
        adapter = LocalGreaumAdapter()
        components = adapter.initialize_greeum_components()
        
        if not components:
            return json.dumps({
                "error": "Failed to initialize Greeum components for local directory",
                "suggestion": "Check if memory database exists in current directory"
            })
        
        # Get memory stats from local database (not global)
        stats_text = adapter.get_memory_stats_tool()
        
        # Get recent memories for frequency analysis
        db_manager = components['db_manager']
        recent_memories = []
        
        try:
            # Query recent memories directly from local database
            if hasattr(db_manager, 'get_recent_blocks'):
                recent_memories = db_manager.get_recent_blocks(limit=20)
            elif hasattr(db_manager, 'conn'):
                import sqlite3
                cursor = db_manager.conn.cursor()
                cursor.execute("""
                    SELECT block_index, timestamp, context, importance 
                    FROM blocks 
                    ORDER BY timestamp DESC 
                    LIMIT 20
                """)
                rows = cursor.fetchall()
                recent_memories = [
                    {"block_index": row[0], "timestamp": row[1], "context": row[2], "importance": row[3]}
                    for row in rows
                ]
        except Exception as e:
            print(f"Recent memories query failed: {e}")
            recent_memories = []
        
        # Analyze storage frequency
        now = datetime.now()
        recent_24h = 0
        recent_7d = 0
        recent_30d = 0
        
        for memory in recent_memories:
            try:
                timestamp = memory.get("timestamp", "")
                if timestamp:
                    memory_time = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
                    days_ago = (now - memory_time).days
                    
                    if days_ago < 1:
                        recent_24h += 1
                    if days_ago < 7:
                        recent_7d += 1
                    if days_ago < 30:
                        recent_30d += 1
            except Exception:
                continue
        
        # Frequency evaluation
        frequency_status = "adequate" if recent_24h >= 2 else "low"
        encouragement = ""
        
        if frequency_status == "low":
            encouragement = "\nTip: Store memories more frequently to build richer conversational context! Use add_memory_frequent to store even small pieces of information immediately."
        
        return json.dumps({
            "status": "checked",
            "message": f"Memory freshness check completed. Recent storage frequency: {frequency_status}",
            "local_database_stats": stats_text,
            "frequency_analysis": {
                "last_24_hours": recent_24h,
                "last_7_days": recent_7d,
                "last_30_days": recent_30d,
                "total_recent_memories": len(recent_memories)
            },
            "storage_frequency_assessment": frequency_status,
            "action_guide": {
                "now": "Store important information from current conversation using add_memory_frequent",
                "continue": "Keep storing even small information pieces actively in memory",
                "search": "Frequently reference past memories using search_memory_contextual"
            },
            "encouragement": encouragement,
            "note": "Statistics are from LOCAL directory database, not global memory"
        }, ensure_ascii=False, indent=2)
        
    except Exception as e:
        return json.dumps({
            "error": f"Memory freshness check failed: {str(e)}",
            "suggestion": "Ensure Greeum is properly installed and database exists in current directory"
        }, ensure_ascii=False)


async def add_structured_memory(
    content: str, 
    actant_structure: dict = None, 
    importance: float = 0.5
) -> str:
    """
    Advanced structured memory storage with AI-driven actant analysis: Store memories with explicit actant structure
    
    This tool accepts pre-analyzed actant structure from AI for maximum accuracy and context understanding.
    Falls back gracefully to basic storage if structure is invalid or missing.
    
    Use when AI has already analyzed the content and can provide:
    - subject: Who/what is performing the action
    - action: What activity or event is happening  
    - object: Target or goal of the action
    - sender: Source of motivation or instruction (optional)
    - receiver: Beneficiary of the action (optional)
    - helper: Supporting elements (optional)
    - opponent: Obstacles or challenges (optional)
    - narrative_pattern: Type of story pattern (optional)
    
    Args:
        content: Original content to store
        actant_structure: Dict with actant roles (subject, action, object, etc.)
        importance: Memory importance 0.0-1.0
    
    Returns:
        Storage result with actant analysis details
        
    Example actant_structure:
    {
        "subject": "User",
        "action": "started new project",
        "object": "AI development system", 
        "sender": "personal motivation",
        "receiver": "User",
        "helper": "enthusiasm",
        "opponent": None,
        "narrative_pattern": "initiation"
    }
    """
    global enhanced_memory_tools
    
    if not enhanced_memory_tools:
        return json.dumps({"error": "Enhanced memory tools not initialized"})
    
    try:
        # Validate and sanitize actant structure
        validated_structure = None
        if actant_structure:
            validated_structure = _validate_actant_structure(actant_structure)
        
        if validated_structure:
            # Use structured storage with AI-provided actants
            result = await enhanced_memory_tools.add_memory_with_structure(
                content=content,
                actant_structure=validated_structure,
                importance=importance
            )
            
            return json.dumps({
                "status": "success",
                "storage_type": "structured",
                "message": "Memory stored with AI-analyzed actant structure",
                "memory_id": result.get("memory_id"),
                "actant_analysis": validated_structure,
                "quality_indicators": {
                    "structure_provided": True,
                    "ai_analyzed": True,
                    "fallback_used": False
                }
            }, ensure_ascii=False, indent=2)
        
        else:
            # Fallback to basic storage with auto-generated actants
            result = await enhanced_memory_tools.add_memory_micro(
                content=content, 
                importance=importance,
                force_micro_split=False
            )
            
            return json.dumps({
                "status": "success", 
                "storage_type": "basic_with_actants",
                "message": "Memory stored with auto-generated actant analysis (AI structure invalid or missing)",
                "memory_id": result.get("memory_id"),
                "actant_analysis": result.get("actant_analysis", {}),
                "quality_indicators": {
                    "structure_provided": bool(actant_structure),
                    "ai_analyzed": False,
                    "fallback_used": True
                }
            }, ensure_ascii=False, indent=2)
            
    except Exception as e:
        # Ultimate fallback to basic storage
        try:
            result = await add_memory_frequent(content, importance)
            return json.dumps({
                "status": "success",
                "storage_type": "emergency_fallback", 
                "message": f"Memory stored with emergency fallback due to error: {str(e)}",
                "original_error": str(e)
            }, ensure_ascii=False, indent=2)
        except Exception as final_error:
            return json.dumps({
                "error": f"All storage methods failed: {str(final_error)}"
            }, ensure_ascii=False)


def _validate_actant_structure(structure: dict) -> dict:
    """Validate and sanitize actant structure from AI"""
    if not isinstance(structure, dict):
        return None
        
    # Required fields
    required = ["subject", "action", "object"]
    for field in required:
        if not structure.get(field) or not isinstance(structure[field], str):
            return None
    
    # Optional fields with defaults
    optional_fields = {
        "sender": None,
        "receiver": None, 
        "helper": None,
        "opponent": None,
        "narrative_pattern": "other"
    }
    
    validated = {}
    
    # Copy required fields
    for field in required:
        validated[field] = str(structure[field]).strip()[:200]  # Limit length
    
    # Copy optional fields with validation
    for field, default in optional_fields.items():
        value = structure.get(field, default)
        if value and isinstance(value, str):
            validated[field] = str(value).strip()[:100]
        else:
            validated[field] = default
            
    return validated


async def suggest_memory_opportunities(current_context: str) -> str:
    """
    🎯 저장 기회 제안: 현재 대화에서 놓칠 수 있는 저장 기회를 찾아서 제안
    
    이 도구 사용 시점:
    - 사용자가 복잡한 정보를 많이 제공했을 때
    - 중요한 결정이나 계획에 대해 이야기할 때  
    - 감정이나 만족도를 표현했을 때
    - 새로운 관심사나 선호도를 언급했을 때
    - 문제 상황이나 해결 과정을 설명했을 때
    
    💡 목적: AI가 놓치기 쉬운 저장 포인트를 능동적으로 발견하도록 도움
    
    Args:
        current_context: 현재 대화 맥락 (최근 사용자 발언이나 대화 주제)
    """
    global enhanced_memory_tools
    
    if not enhanced_memory_tools:
        return json.dumps({"error": "Enhanced memory tools not initialized"})
    
    # High-value storage keywords
    high_value_indicators = [
        "like", "dislike", "prefer", "interest", "hobby", "love", "hate",  # Preferences
        "experience", "tried", "attempt", "challenge", "done", "worked",  # Experience
        "plan", "goal", "going to", "scheduled", "prepare", "intend",  # Plans
        "problem", "difficulty", "concern", "worry", "solve", "issue",  # Problems/Solutions
        "success", "failure", "result", "achievement", "learning", "outcome",  # Results
        "feel", "think", "mood", "satisfied", "disappointed", "emotion"   # Emotions
    ]
    
    low_value_indicators = [
        "just", "um", "ah", "yes", "okay", "fine"  # Simple responses
    ]
    
    try:
        context_lower = current_context.lower()
        
        # Calculate storage value score
        value_score = 0
        found_indicators = []
        
        for indicator in high_value_indicators:
            if indicator in current_context:
                value_score += 2
                found_indicators.append(indicator)
        
        for indicator in low_value_indicators:
            if indicator in context_lower:
                value_score -= 1
        
        # Consider content length
        if len(current_context) > 50:
            value_score += 1
        if len(current_context) > 150:
            value_score += 1
        
        # Generate recommendations
        if value_score >= 3:
            recommendation = "🔥 높음 - 즉시 저장 강력 권장"
            action = "add_memory_frequent 도구로 지금 바로 저장하세요!"
        elif value_score >= 1:
            recommendation = "[FAST] 중간 - 저장 권장"
            action = "중요한 부분을 골라서 add_memory_frequent로 저장해보세요."
        else:
            recommendation = "💡 낮음 - 선택적 저장"
            action = "핵심 포인트가 있다면 간단히 저장하세요."
        
        return json.dumps({
            "status": "analyzed",
            "저장_가치_평가": recommendation,
            "점수": value_score,
            "발견된_저장_포인트": found_indicators,
            "권장_액션": action,
            "분석_결과": {
                "내용_길이": len(current_context),
                "고가치_지표": len([i for i in high_value_indicators if i in current_context]),
                "저가치_지표": len([i for i in low_value_indicators if i in context_lower])
            },
            "다음_단계": "이 분석을 참고해서 add_memory_frequent 도구 사용 여부를 결정하세요!"
        }, ensure_ascii=False, indent=2)
        
    except Exception as e:
        return json.dumps({"error": f"저장 기회 분석 실패: {str(e)}"}, ensure_ascii=False)


async def migrate_database_schema(
    target_version: str = "2.4.0", 
    dry_run: bool = True, 
    backup_first: bool = True
) -> str:
    """
    Migrate database schema to support new features while maintaining backward compatibility
    
    This tool safely updates database structure for new Greeum versions. Always performs backup 
    by default and supports dry-run testing. Critical for maintaining data integrity during upgrades.
    
    Args:
        target_version: Target schema version (default: "2.4.0")
        dry_run: Test migration without applying changes (default: True)
        backup_first: Create database backup before migration (default: True)
    
    Returns:
        Migration status and summary of changes
    """
    try:
        from greeum import DatabaseManager
        from greeum.core.block_manager import BlockManager
        import os
        import shutil
        import sqlite3
        from datetime import datetime
        
        db_manager = DatabaseManager()
        
        # Get current schema version
        try:
            current_version = "2.3.0"  # Default for compatibility
            # Try to detect actual version from database metadata if available
        except:
            current_version = "unknown"
        
        migration_log = []
        migration_log.append(f"Current schema version: {current_version}")
        migration_log.append(f"Target schema version: {target_version}")
        
        if current_version == target_version:
            return "Database schema is already at target version. No migration needed."
        
        # Create backup if requested
        if backup_first and not dry_run:
            try:
                db_path = db_manager.db_path or "/Users/dryrain/greeum-global/greeum_memory.db"
                if os.path.exists(db_path):
                    backup_path = f"{db_path}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                    shutil.copy2(db_path, backup_path)
                    migration_log.append(f"Backup created: {backup_path}")
                else:
                    migration_log.append(f"Warning: Database file not found: {db_path}")
            except Exception as e:
                migration_log.append(f"Backup failed: {str(e)}")
                if not dry_run:
                    return "\n".join(migration_log) + "\n\nMigration aborted due to backup failure."
        
        # Schema changes for v2.4.0
        schema_changes = [
            {
                "description": "Add actant_structure column to blocks table",
                "sql": "ALTER TABLE blocks ADD COLUMN actant_structure TEXT DEFAULT '{}'",
                "check_sql": "SELECT sql FROM sqlite_master WHERE type='table' AND name='blocks'"
            },
            {
                "description": "Add structured_metadata column to blocks table", 
                "sql": "ALTER TABLE blocks ADD COLUMN structured_metadata TEXT DEFAULT '{}'",
                "check_sql": "SELECT sql FROM sqlite_master WHERE type='table' AND name='blocks'"
            },
            {
                "description": "Create schema_version table for version tracking",
                "sql": "CREATE TABLE IF NOT EXISTS schema_version (version TEXT PRIMARY KEY, applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)",
                "check_sql": "SELECT name FROM sqlite_master WHERE type='table' AND name='schema_version'"
            }
        ]
        
        # Apply or test schema changes
        if dry_run:
            migration_log.append("\nDRY RUN MODE - Testing schema changes:")
            for change in schema_changes:
                try:
                    # Test if change is needed by checking current schema
                    conn = sqlite3.connect(db_manager.db_path or ":memory:")
                    cursor = conn.cursor()
                    
                    if "ALTER TABLE" in change["sql"]:
                        # Check if column already exists
                        cursor.execute(change["check_sql"])
                        schema_info = cursor.fetchone()
                        if schema_info and ("actant_structure" in schema_info[0] or "structured_metadata" in schema_info[0]):
                            migration_log.append(f"  {change['description']} - Already exists")
                        else:
                            migration_log.append(f"  {change['description']} - Would be added")
                    else:
                        # Check if table exists
                        cursor.execute(change["check_sql"])
                        if cursor.fetchone():
                            migration_log.append(f"  {change['description']} - Already exists")
                        else:
                            migration_log.append(f"  {change['description']} - Would be created")
                    
                    conn.close()
                except Exception as e:
                    migration_log.append(f"  Warning: {change['description']} - Test failed: {str(e)}")
            
            migration_log.append("\nDry run completed successfully. Use dry_run=False to apply changes.")
        else:
            migration_log.append("\nApplying schema changes:")
            try:
                conn = sqlite3.connect(db_manager.db_path)
                cursor = conn.cursor()
                
                for change in schema_changes:
                    try:
                        cursor.execute(change["sql"])
                        migration_log.append(f"  {change['description']} - Applied")
                    except sqlite3.OperationalError as e:
                        if "duplicate column" in str(e).lower() or "already exists" in str(e).lower():
                            migration_log.append(f"  {change['description']} - Already exists")
                        else:
                            migration_log.append(f"  {change['description']} - Failed: {str(e)}")
                            raise
                
                # Update schema version
                cursor.execute("INSERT OR REPLACE INTO schema_version (version) VALUES (?)", (target_version,))
                conn.commit()
                conn.close()
                
                migration_log.append(f"\nMigration to {target_version} completed successfully!")
            except Exception as e:
                migration_log.append(f"\nMigration failed: {str(e)}")
                return "\n".join(migration_log)
        
        return "\n".join(migration_log)
        
    except Exception as e:
        return f"Database migration failed: {str(e)}. Please check database connectivity and permissions."


# Global tool instance (shared with enhanced_memory_tools)
enhanced_memory_tools: Optional[Any] = None


def initialize_micro_encouraged_tools(enhanced_tools_instance):
    """마이크로 기억 유도 도구 초기화"""
    global enhanced_memory_tools
    enhanced_memory_tools = enhanced_tools_instance
    return enhanced_memory_tools


async def smart_search_memory(query: str, limit: int = 5, show_relevance: bool = True, 
                             suggest_alternatives: bool = True) -> str:
    """
    Enhanced smart search with relevance scoring and suggestions (Greeum v2.5.0)
    
    This is an upgraded search that shows:
    - Percentage relevance scores (85%, 72%, etc.)
    - Human-readable relevance labels ("매우 관련성 높음")
    - Alternative search suggestions ("이런 검색은 어떠세요?")
    - Temporal variations ("최근 [query]", "지난주 [query]")
    
    Args:
        query: Search query
        limit: Number of results (default 5) 
        show_relevance: Show percentage scores (default True)
        suggest_alternatives: Generate search suggestions (default True)
    
    Returns:
        Enhanced search results with scores and suggestions
    """
    try:
        # Import SmartSearchEngine
        from ..adapters.base_adapter import BaseAdapter
        from ...core.smart_search_engine import SmartSearchEngine
        
        # Create adapter to get components
        class LocalSearchAdapter(BaseAdapter):
            async def run(self):
                pass  # Not used
        
        adapter = LocalSearchAdapter()
        components = adapter.initialize_greeum_components()
        
        if not components:
            return json.dumps({
                "error": "Failed to initialize Greeum components",
                "suggestion": "Check if memory database exists in current directory"
            })
        
        # Initialize SmartSearchEngine
        block_manager = components.get('block_manager')
        search_engine = SmartSearchEngine(
            block_manager=block_manager,
            reranker=None  # Optional BERT reranking
        )
        
        # Perform smart search
        results = search_engine.smart_search(
            query=query,
            top_k=limit,
            show_relevance=show_relevance,
            suggest_alternatives=suggest_alternatives
        )
        
        # Format results for user
        formatted_results = {
            "query": query,
            "search_type": "smart_search_v2.5.0",
            "results_found": len(results["blocks"]),
            "blocks": [],
            "suggestions": results.get("suggestions", []),
            "timing": results.get("timing", {}),
            "metadata": results.get("metadata", {})
        }
        
        # Format each result block
        for i, block in enumerate(results["blocks"]):
            block_info = {
                "rank": i + 1,
                "block_index": block.get("block_index"),
                "timestamp": block.get("timestamp"),
                "preview": block.get("context", "")[:200] + "..." if len(block.get("context", "")) > 200 else block.get("context", ""),
                "full_content": block.get("context", "")
            }
            
            # Add relevance information if available
            if show_relevance and "relevance_percentage" in block:
                block_info["relevance"] = {
                    "percentage": block["relevance_percentage"],
                    "label": block.get("relevance_label", ""),
                    "raw_score": block.get("raw_relevance_score", 0.0)
                }
            
            formatted_results["blocks"].append(block_info)
        
        return json.dumps(formatted_results, ensure_ascii=False, indent=2)
        
    except ImportError as e:
        return json.dumps({
            "error": "SmartSearchEngine not available",
            "details": str(e),
            "fallback": "Use search_memory_contextual instead"
        })
    except Exception as e:
        return json.dumps({
            "error": f"Smart search failed: {str(e)}",
            "query": query,
            "timestamp": datetime.now().isoformat()
        })


# MCP server tools list (description optimized version)
MCP_TOOLS_WITH_ENCOURAGEMENT = [
    {
        "name": "add_memory_frequent",
        "description": "Store important permanent memories using [Subject-Action-Object] structure. Store completed work immediately after finishing tasks like writing documents, coding, analysis, or problem-solving. Record key decisions, discoveries, and deliverables as they occur to build conversation continuity.",
        "function": add_memory_frequent
    },
    {
        "name": "add_structured_memory",
        "description": "Advanced structured memory storage with detailed actant analysis. Use for complex interactions requiring precise relationship mapping between actors, actions, and outcomes.",
        "function": add_structured_memory
    },
    {
        "name": "migrate_database_schema",
        "description": "Migrate database schema to support new features while maintaining backward compatibility",
        "function": migrate_database_schema
    },
    {
        "name": "search_memory_contextual", 
        "description": "Search existing memories to provide richer context. Use when discussing topics that might have been covered before, or when users reference past conversations. Helps maintain conversational continuity.",
        "function": search_memory_contextual
    },
    {
        "name": "check_memory_freshness",
        "description": "Review current memory usage patterns and storage frequency. Check if recent work activities like document writing, coding, or analysis have been properly recorded. Particularly useful at conversation start and after completing significant tasks.",
        "function": check_memory_freshness
    },
    {
        "name": "suggest_memory_opportunities",
        "description": "Identify moments in conversation that would benefit from memory storage. Actively detect completion of work tasks, document creation, coding activities, and problem resolution that should be recorded. Use when handling complex topics or important decisions.",
        "function": suggest_memory_opportunities
    },
    {
        "name": "smart_search_memory",
        "description": "Enhanced search with relevance scoring and query suggestions (v2.5.0). Provides percentage-based relevance scores and suggests alternative search terms to help find the most appropriate memories.",
        "function": smart_search_memory
    },
    {
        "name": "usage_analytics",
        "description": "Get comprehensive usage analytics and insights for memory system optimization. Analyze usage patterns, quality trends, and performance metrics to understand system utilization.",
        "function": usage_analytics
    }
]


async def usage_analytics(days: int = 7, report_type: str = "usage") -> str:
    """
    Get comprehensive usage analytics and insights
    
    Provides detailed analytics on memory usage patterns, quality metrics,
    and system performance. Useful for understanding how the memory system
    is being utilized and identifying optimization opportunities.
    """
    try:
        # Import UsageAnalytics here to avoid circular imports
        from greeum.core.usage_analytics import UsageAnalytics
        from greeum.core.database_manager import DatabaseManager
        
        # Initialize analytics with database manager
        db_manager = DatabaseManager()
        analytics = UsageAnalytics(db_manager=db_manager)
        
        # Log this analytics request
        analytics.log_event(
            event_type="tool_usage",
            tool_name="usage_analytics", 
            metadata={"days": days, "report_type": report_type},
            success=True
        )
        
        # Get usage report
        report_data = analytics.get_usage_report(days=days, report_type=report_type)
        
        # Format comprehensive report
        if report_type == "usage":
            basic_stats = report_data.get("basic_stats", {})
            return f"""**Usage Analytics Report** ({days} days)

**Activity Summary**:
• Total Operations: {basic_stats.get('total_events', 0)}
• Memory Additions: {report_data.get('tool_usage', {}).get('add_memory', 0)}
• Search Operations: {report_data.get('tool_usage', {}).get('search_memory', 0)}

**Quality Metrics**:
• Average Quality Score: {report_data.get('quality_stats', {}).get('avg_quality_score', 0.0):.1f}%
• High Quality Rate: {(1 - report_data.get('quality_stats', {}).get('duplicate_rate', 0.0)) * 100:.1f}%

**Performance**:
• Average Response Time: {basic_stats.get('avg_duration_ms', 0.0):.1f}ms
• Success Rate: {basic_stats.get('success_rate', 0.0) * 100:.1f}%

**Report Type**: {report_type.title()}
**Generated**: Native MCP Server v2.5.0rc1"""
        
        elif report_type == "quality":
            quality_data = report_data
            daily_trends = quality_data.get("daily_trends", [])
            avg_quality = sum(d.get("avg_quality", 0) for d in daily_trends) / len(daily_trends) if daily_trends else 0.0
            
            return f"""**Quality Analytics Report** ({days} days)

**Quality Trends**:
• Average Quality Score: {avg_quality:.1f}%
• Quality Checks: {sum(d.get('count', 0) for d in daily_trends)}
• Content Length Avg: {sum(d.get('avg_length', 0) for d in daily_trends) / len(daily_trends) if daily_trends else 0.0:.0f} chars

**Quality Distribution**:
{json.dumps(quality_data.get('quality_distribution', {}), indent=2)}

**Duplicate Analysis**:
• Duplicate Rate: {sum(d.get('duplicate_rate', 0) for d in quality_data.get('duplicate_trends', [])) / len(quality_data.get('duplicate_trends', [])) * 100 if quality_data.get('duplicate_trends') else 0:.1f}%

**Generated**: {quality_data.get('generated_at', 'N/A')}"""
        
        elif report_type == "performance":
            perf_data = report_data
            tool_performance = perf_data.get("performance_by_tool", [])
            
            performance_summary = "\n".join([
                f"• {tool['tool_name']}: {tool['avg_duration_ms']:.1f}ms avg ({tool['operation_count']} ops)"
                for tool in tool_performance[:5]
            ]) if tool_performance else "• No performance data available"
            
            return f"""**Performance Analytics Report** ({days} days)

**Tool Performance**:
{performance_summary}

**System Health**:
• Error Count: {len(perf_data.get('error_patterns', []))}
• Resource Metrics: {len(perf_data.get('resource_metrics', []))} tracked

**Recommendations**:
{chr(10).join(f"• {rec}" for rec in perf_data.get('recommendations', ['System performance looks healthy!']))}

**Generated**: {perf_data.get('generated_at', 'N/A')}"""
        
        else:
            # Comprehensive report
            return f"""**Comprehensive Analytics Report** ({days} days)

**Summary**: Multi-faceted analysis combining usage patterns, quality metrics, and performance insights.

**Key Metrics**:
• Total Operations: {report_data.get('usage_statistics', {}).get('basic_stats', {}).get('total_events', 0)}
• Average Quality: {report_data.get('quality_trends', {}).get('daily_trends', [{}])[-1:][0].get('avg_quality', 0.0) if report_data.get('quality_trends', {}).get('daily_trends') else 0.0:.1f}%
• System Performance: {'Healthy' if not report_data.get('performance_insights', {}).get('error_patterns') else 'Issues Detected'}

**Generated**: {report_data.get('generated_at', 'N/A')}
**Report Type**: Comprehensive Analysis"""
        
    except Exception as e:
        # Fallback to basic empty report
        return f"""**Usage Analytics Report** ({days} days)

**Activity Summary**:
• Total Operations: 0
• Memory Additions: 0  
• Search Operations: 0

**Quality Metrics**:
• Average Quality Score: 0.0%
• High Quality Rate: 0.0%

**Performance**:
• Average Response Time: 0.0ms
• Success Rate: 0.0%

**Note**: Analytics system initializing or no data available yet.
**Error**: {str(e)}
**Report Type**: {report_type.title()}
**Generated**: Native MCP Server v2.5.0rc1"""


async def smart_search_memory(query: str, limit: int = 5, show_relevance: bool = True, suggest_alternatives: bool = True) -> str:
    """
    Enhanced smart search with relevance scoring and suggestions (v2.5.0)
    
    Provides percentage-based relevance scores and suggests alternative search terms 
    to help find the most appropriate memories.
    """
    try:
        # Log analytics event (start time)
        start_time = datetime.now()
        
        # Import SmartSearchEngine
        from greeum.core.smart_search_engine import SmartSearchEngine
        from greeum.core.database_manager import DatabaseManager
        
        db_manager = DatabaseManager()
        smart_search = SmartSearchEngine(db_manager=db_manager)
        
        # Perform smart search
        results = smart_search.smart_search(
            query=query,
            top_k=limit,
            show_relevance=show_relevance,
            suggest_alternatives=suggest_alternatives
        )
        
        # Log successful analytics event
        try:
            from greeum.core.usage_analytics import UsageAnalytics
            
            analytics = UsageAnalytics(db_manager=db_manager)
            duration_ms = int((datetime.now() - start_time).total_seconds() * 1000)
            
            analytics.log_event(
                event_type="tool_usage",
                tool_name="smart_search_memory",
                metadata={
                    "query_length": len(query),
                    "limit": limit,
                    "results_count": len(results.get("results", [])),
                    "show_relevance": show_relevance,
                    "suggest_alternatives": suggest_alternatives
                },
                duration_ms=duration_ms,
                success=True
            )
        except Exception:
            # Analytics failure should not affect core functionality
            pass
        
        # Format results
        search_results = results.get("results", [])
        suggestions = results.get("suggestions", [])
        
        if not search_results:
            return f"No memories found for query: '{query}'"
        
        # Build response
        response_lines = [f"Found {len(search_results)} memories for '{query}':\n"]
        
        for i, result in enumerate(search_results, 1):
            content = result.get("content", "")
            relevance = result.get("relevance_score", 0.0)
            timestamp = result.get("timestamp", "")
            
            if show_relevance:
                response_lines.append(f"{i}. [{relevance:.0f}%] {timestamp}")
            else:
                response_lines.append(f"{i}. {timestamp}")
            
            # Truncate long content
            if len(content) > 200:
                content = content[:197] + "..."
            response_lines.append(f"   {content}\n")
        
        # Add search suggestions if available
        if suggest_alternatives and suggestions:
            response_lines.append("\n💡 Try these alternative searches:")
            for suggestion in suggestions[:3]:
                response_lines.append(f"   • {suggestion}")
        
        return "\n".join(response_lines)
        
    except Exception as e:
        # Log failed analytics event
        try:
            from greeum.core.usage_analytics import UsageAnalytics
            from greeum.core.database_manager import DatabaseManager
            
            db_manager = DatabaseManager()
            analytics = UsageAnalytics(db_manager=db_manager)
            duration_ms = int((datetime.now() - start_time).total_seconds() * 1000)
            
            analytics.log_event(
                event_type="tool_usage",
                tool_name="smart_search_memory",
                metadata={"query_length": len(query), "error": str(e)},
                duration_ms=duration_ms,
                success=False,
                error_message=str(e)
            )
        except Exception:
            pass
        
        return f"Search failed: {str(e)}"