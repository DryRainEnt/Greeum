"""
Greeum v3.0.0: Context-Dependent Memory System
Extends existing v2.6.4 components for context-aware memory
"""

import time
import logging
from typing import Dict, List, Optional, Tuple, Set
from datetime import datetime

from greeum.core.database_manager import DatabaseManager
from greeum.core.block_manager import BlockManager
try:
    from greeum.stm_manager import STMManager
except ImportError:
    # Fallback to basic implementation if STMManager not available
    class STMManager:
        def __init__(self):
            self.memories = []
        def add(self, content, speaker):
            self.memories.append({'content': content, 'speaker': speaker})
            return len(self.memories) - 1

logger = logging.getLogger(__name__)


class ActiveContextManager:
    """
    Active Context Manager (hippocampus-like)
    Maintains currently active memory context and auto-connects new memories
    Note: No longer inherits from STMManager - they serve different purposes
    """
    
    def __init__(self, db_manager: DatabaseManager):
        """Initialize with existing database"""
        self.db_manager = db_manager
        self.memories = []  # Temporary memory buffer (STM-like functionality)
        
        # Context management
        self.current_context_id = None
        self.context_trigger = None
        self.context_start_time = None
        
        # Active nodes (like place cells)
        self.active_nodes: Dict[int, float] = {}  # {memory_id: activation_level}
        
        # Context switch detection
        self.last_memory_time = time.time()
        self.context_timeout = 300  # 5 minutes of inactivity = new context
        
        # STM/LTM consolidation parameters
        self.stm_capacity = 20  # Max memories in STM
        self.stm_consolidation_threshold = 0.7  # Importance threshold for LTM promotion
        self.stm_time_threshold = 3600  # 1 hour - auto-consolidate old memories
        
        # Ensure v3 tables exist
        self._ensure_v3_tables()
        
        # Start default context
        self.switch_context("session_start")
    
    def _ensure_v3_tables(self):
        """Create v3 tables if they don't exist"""
        cursor = self.db_manager.conn.cursor()
        
        # Contexts table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS contexts (
                context_id TEXT PRIMARY KEY,
                trigger TEXT,
                start_time REAL,
                end_time REAL,
                memory_count INTEGER DEFAULT 0,
                metadata TEXT
            )
        ''')
        
        # Memory connections table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS memory_connections (
                from_memory INTEGER,
                to_memory INTEGER,
                weight REAL DEFAULT 0.5,
                connection_type TEXT,
                created_at REAL,
                context_id TEXT,
                PRIMARY KEY (from_memory, to_memory)
            )
        ''')
        
        # Activation history
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS activation_log (
                memory_id INTEGER,
                activation_level REAL,
                context_id TEXT,
                timestamp REAL,
                trigger_memory INTEGER
            )
        ''')
        
        # Semantic tagging tables
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tag_definitions (
                tag_id INTEGER PRIMARY KEY AUTOINCREMENT,
                tag_name TEXT UNIQUE NOT NULL,
                tag_level INTEGER,
                usage_count INTEGER DEFAULT 0,
                last_used REAL,
                created_at REAL DEFAULT (strftime('%s', 'now')),
                is_active INTEGER DEFAULT 1
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS memory_tags (
                memory_id INTEGER,
                tag_name TEXT,
                tag_type TEXT,  -- 'category', 'activity', 'domain'
                confidence REAL DEFAULT 1.0,
                added_by TEXT DEFAULT 'system',
                added_at REAL DEFAULT (strftime('%s', 'now')),
                PRIMARY KEY (memory_id, tag_name, tag_type)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tag_synonyms (
                synonym TEXT PRIMARY KEY,
                canonical TEXT NOT NULL
            )
        ''')
        
        self.db_manager.conn.commit()
    
    def switch_context(self, trigger: str):
        """
        Switch to a new context (like moving to a new place)
        Saves current context and starts fresh
        """
        # Save current context
        if self.current_context_id:
            self._save_context()
        
        # Create new context with more unique ID
        import uuid
        self.current_context_id = f"ctx_{uuid.uuid4().hex[:12]}"
        self.context_trigger = trigger
        self.context_start_time = time.time()
        self.active_nodes = {}
        
        # Record in database
        cursor = self.db_manager.conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO contexts (context_id, trigger, start_time)
            VALUES (?, ?, ?)
        ''', (self.current_context_id, trigger, self.context_start_time))
        self.db_manager.conn.commit()
        
        logger.info(f"Context switched: {trigger} -> {self.current_context_id}")
    
    def _save_context(self):
        """Save current context state"""
        cursor = self.db_manager.conn.cursor()
        cursor.execute('''
            UPDATE contexts 
            SET end_time = ?, memory_count = ?
            WHERE context_id = ?
        ''', (time.time(), len(self.active_nodes), self.current_context_id))
        self.db_manager.conn.commit()
    
    def add_memory_with_context(self, content: str, importance: float = 0.5) -> int:
        """
        Add memory with automatic context connections
        This is the KEY innovation - memories connect to active context
        """
        # Check if we should switch context (time gap)
        time_gap = time.time() - self.last_memory_time
        if time_gap > self.context_timeout:
            self.switch_context(f"time_gap_{int(time_gap)}s")
        
        # Add to STM first
        stm_id = len(self.memories)
        stm_entry = {
            'content': content, 
            'speaker': 'user', 
            'timestamp': time.time(),
            'importance': importance,
            'context_id': self.current_context_id,
            'ltm_id': None  # Will be set when promoted to LTM
        }
        self.memories.append(stm_entry)
        
        # Check if this memory should be immediately promoted to LTM
        should_promote = (
            importance >= self.stm_consolidation_threshold or  # High importance
            len(self.memories) > self.stm_capacity  # STM overflow
        )
        
        if should_promote:
            return self._promote_to_ltm(stm_id)
        else:
            # Stay in STM for now, trigger consolidation check
            self._trigger_stm_consolidation()
            
            # For STM memories, use negative IDs to distinguish from LTM
            temp_id = -(stm_id + 1)
            
            # Add to active nodes for context connections
            self.active_nodes[temp_id] = 1.0
            
            # Decay other activations
            self._decay_activations()
            
            # Update time
            self.last_memory_time = time.time()
            
            logger.debug(f"Added STM memory #{temp_id} (stm_id: {stm_id}) in context {self.current_context_id}")
            
            return temp_id
    
    def _create_context_connections(self, new_memory_id: int):
        """
        Create connections between new memory and currently active ones
        This implements the "memories form where you are" principle
        """
        cursor = self.db_manager.conn.cursor()
        connections_to_insert = []
        
        for active_id, activation_level in self.active_nodes.items():
            if activation_level > 0.3:  # Only connect to reasonably active memories
                # Connection strength based on activation
                weight = min(0.9, activation_level * 0.7)
                timestamp = time.time()
                
                # Bidirectional connections (batch)
                connections_to_insert.extend([
                    (new_memory_id, active_id, weight, 'context', timestamp, self.current_context_id),
                    (active_id, new_memory_id, weight * 0.7, 'context', timestamp, self.current_context_id)
                ])
        
        # Batch INSERT for performance
        if connections_to_insert:
            cursor.executemany('''
                INSERT OR REPLACE INTO memory_connections
                (from_memory, to_memory, weight, connection_type, created_at, context_id)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', connections_to_insert)
            
            connections_created = len(connections_to_insert)
        else:
            connections_created = 0
        
        self.db_manager.conn.commit()
        logger.debug(f"Created {connections_created} connections for memory #{new_memory_id}")
    
    def _decay_activations(self, decay_rate: float = 0.9):
        """Decay activation levels (forgetting)"""
        for memory_id in list(self.active_nodes.keys()):
            self.active_nodes[memory_id] *= decay_rate
            if self.active_nodes[memory_id] < 0.1:
                del self.active_nodes[memory_id]
    
    def _extract_keywords(self, text: str) -> List[str]:
        """Simple keyword extraction"""
        import re
        # 한글과 영어 모두 지원
        words = re.findall(r'\b[a-zA-Z]+\b|[가-힣]+', text.lower())
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 
                     '은', '는', '이', '가', '을', '를', '에', '의', '과', '와', '그', '저', '것'}
        # 한글은 1글자도 허용, 영어는 2글자 이상
        return [w for w in words if (len(w) >= 1 if any(ord(c) >= 0xAC00 for c in w) else len(w) > 2) 
                and w not in stop_words][:5]
    
    def _promote_to_ltm(self, stm_id: int) -> int:
        """Promote a memory from STM to LTM"""
        if stm_id >= len(self.memories):
            logger.error(f"Invalid STM ID: {stm_id}")
            return -1
        
        stm_entry = self.memories[stm_id]
        
        # Use cached block manager for performance
        if not hasattr(self, '_cached_block_manager'):
            self._cached_block_manager = BlockManager(self.db_manager)
        
        keywords = self._extract_keywords(stm_entry['content'])
        
        # Create permanent LTM block (no metadata parameter - not in schema)
        block_result = self._cached_block_manager.add_block(
            context=stm_entry['content'],
            keywords=keywords,
            tags=[],
            embedding=[],
            importance=stm_entry['importance']
        )
        
        if block_result and 'block_index' in block_result:
            ltm_id = block_result['block_index']
            
            # Update STM entry with LTM reference
            self.memories[stm_id]['ltm_id'] = ltm_id
            
            # Create context connections
            self._create_context_connections(ltm_id)
            
            # Add to active nodes
            self.active_nodes[ltm_id] = 1.0
            
            logger.debug(f"Promoted STM #{stm_id} to LTM #{ltm_id}")
            return ltm_id
        else:
            logger.error("Failed to promote memory to LTM")
            return -1
    
    def _trigger_stm_consolidation(self):
        """Check if STM memories need consolidation"""
        current_time = time.time()
        
        # Find old memories that should be consolidated
        for i, memory in enumerate(self.memories):
            if memory['ltm_id'] is None:  # Not yet in LTM
                age = current_time - memory['timestamp']
                
                # Auto-promote old or important memories
                if (age > self.stm_time_threshold or 
                    memory['importance'] >= self.stm_consolidation_threshold):
                    self._promote_to_ltm(i)
        
        # If STM is still over capacity, promote oldest memories
        while len([m for m in self.memories if m['ltm_id'] is None]) > self.stm_capacity:
            # Find oldest unpromoted memory
            oldest_unpromoted = None
            oldest_time = float('inf')
            
            for i, memory in enumerate(self.memories):
                if memory['ltm_id'] is None and memory['timestamp'] < oldest_time:
                    oldest_time = memory['timestamp']
                    oldest_unpromoted = i
            
            if oldest_unpromoted is not None:
                self._promote_to_ltm(oldest_unpromoted)
            else:
                break  # No more unpromoted memories


class SpreadingActivation:
    """
    Implements spreading activation for memory recall
    Based on research on semantic networks and memory retrieval
    """
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self.decay_rate = 0.5
        self.threshold = 0.1
        self.max_depth = 3
    
    def activate(self, source_memory_id: int) -> Dict[int, float]:
        """
        Spread activation from source memory through network
        Returns dict of memory_id -> activation_level
        """
        activations = {source_memory_id: 1.0}
        visited = {source_memory_id}
        current_layer = [(source_memory_id, 1.0)]
        
        for depth in range(self.max_depth):
            next_layer = []
            
            for memory_id, activation_level in current_layer:
                # Get connections
                connections = self._get_connections(memory_id)
                
                for target_id, weight in connections:
                    if target_id in visited:
                        continue
                    
                    # Calculate spread activation
                    spread = activation_level * weight * self.decay_rate
                    
                    if spread > self.threshold:
                        if target_id not in activations:
                            activations[target_id] = 0
                        activations[target_id] += spread
                        next_layer.append((target_id, activations[target_id]))
                        visited.add(target_id)
            
            current_layer = next_layer
            if not current_layer:
                break
        
        # Log activation
        self._log_activation(activations, source_memory_id)
        
        return activations
    
    def _get_connections(self, memory_id: int) -> List[Tuple[int, float]]:
        """Get all connections from a memory"""
        cursor = self.db_manager.conn.cursor()
        cursor.execute('''
            SELECT to_memory, weight 
            FROM memory_connections 
            WHERE from_memory = ?
            ORDER BY weight DESC
        ''', (memory_id,))
        
        return [(row[0], row[1]) for row in cursor.fetchall()]
    
    def _log_activation(self, activations: Dict[int, float], trigger_id: int):
        """Log activation for learning"""
        cursor = self.db_manager.conn.cursor()
        timestamp = time.time()
        
        for memory_id, level in activations.items():
            cursor.execute('''
                INSERT INTO activation_log 
                (memory_id, activation_level, context_id, timestamp, trigger_memory)
                VALUES (?, ?, ?, ?, ?)
            ''', (memory_id, level, f"recall_{int(timestamp)}", timestamp, trigger_id))
        
        self.db_manager.conn.commit()


class ContextMemorySystem:
    """
    Main interface for Context-Dependent Memory System
    Combines all v3.0 features with v2.6.4 compatibility
    """
    
    def __init__(self, db_path: Optional[str] = None):
        """Initialize context memory system"""
        # Load configuration
        from greeum.core.config import get_config
        self.config = get_config()
        
        # Use provided path or config default
        final_db_path = db_path or self.config.get_database_path()
        
        # Auto-migration from v2.6.4 if needed
        from greeum.core.v300_migration import auto_migrate_if_needed
        migration_success = auto_migrate_if_needed(final_db_path)
        if not migration_success:
            logger.warning("Database migration failed, but continuing...")
        
        self.db_manager = DatabaseManager(connection_string=final_db_path)
        self.context_manager = ActiveContextManager(self.db_manager)
        self.activation_engine = SpreadingActivation(self.db_manager)
        self.block_manager = BlockManager(self.db_manager)
        
        # Initialize semantic tagging if enabled
        if self.config.memory.enable_auto_tagging:
            from greeum.core.semantic_tagging import SemanticTagger
            self.tagger = SemanticTagger(self.db_manager)
        else:
            self.tagger = None
    
    def add_memory(self, content: str, importance: float = 0.5) -> int:
        """
        Add a new memory with context awareness and automatic tagging
        
        Args:
            content: Memory content (required, non-empty string)
            importance: Memory importance (0.0-1.0, default 0.5)
            
        Returns:
            Memory ID (positive for LTM, negative for STM) or -1 on error
            
        Raises:
            ValueError: Invalid input parameters
            RuntimeError: Critical system error
        """
        # Input validation
        if not isinstance(content, str):
            raise ValueError(f"Content must be a string, got {type(content)}")
        
        if not content or not content.strip():
            raise ValueError("Content cannot be empty or whitespace only")
        
        if not isinstance(importance, (int, float)):
            raise ValueError(f"Importance must be a number, got {type(importance)}")
        
        if not (0.0 <= importance <= 1.0):
            raise ValueError(f"Importance must be between 0.0 and 1.0, got {importance}")
        
        content = content.strip()
        
        try:
            # Add memory with context
            memory_id = self.context_manager.add_memory_with_context(content, importance)
            
            if memory_id == -1:
                logger.error("Failed to add memory to context manager")
                return -1
            
            # Add semantic tags if enabled
            if memory_id and memory_id != -1 and self.tagger:
                try:
                    tags = self.tagger.quick_tag(content)
                    self.tagger.save_tags(memory_id, tags)
                    logger.debug(f"Tagged memory #{memory_id}: {tags.category}/{tags.activity}")
                except Exception as e:
                    logger.warning(f"Tagging failed for memory #{memory_id}: {e}")
                    # Continue execution - tagging failure is not critical
            
            return memory_id
            
        except ValueError:
            # Re-raise validation errors
            raise
        except Exception as e:
            logger.error(f"Critical error adding memory: {e}")
            raise RuntimeError(f"Failed to add memory: {e}") from e
    
    def recall(self, query: str, use_activation: bool = True, 
               category: Optional[str] = None, activity: Optional[str] = None) -> List[Dict]:
        """
        Recall memories using search, tags, and activation
        
        Args:
            query: Search query (required, non-empty string)
            use_activation: Whether to use spreading activation
            category: Optional semantic category filter
            activity: Optional semantic activity filter
            
        Returns:
            List of matching memory dictionaries
            
        Raises:
            ValueError: Invalid input parameters
            RuntimeError: Critical system error
        """
        # Input validation
        if not isinstance(query, str):
            raise ValueError(f"Query must be a string, got {type(query)}")
        
        if not query or not query.strip():
            raise ValueError("Query cannot be empty or whitespace only")
        
        query = query.strip()
        
        try:
            # First, try tag-based search if tagger is available
            tag_results = []
            if self.tagger and (category or activity):
                try:
                    tag_memory_ids = self.tagger.search_by_tags(category=category, activity=activity)
                    for mem_id in tag_memory_ids:
                        try:
                            block = self.block_manager.db_manager.get_block(mem_id)
                            if block:
                                tag_results.append(block)
                        except Exception as e:
                            logger.warning(f"Failed to retrieve block {mem_id}: {e}")
                            continue
                except Exception as e:
                    logger.warning(f"Tag-based search failed: {e}")
                    # Continue with keyword search
            
            # Then, keyword search
            try:
                keywords = self.context_manager._extract_keywords(query)
                results = self.block_manager.db_manager.search_blocks_by_keyword(
                    keywords, 
                    limit=10
                )
            except Exception as e:
                logger.error(f"Keyword search failed: {e}")
                results = []
            
            # Combine and deduplicate
            all_results = tag_results + results
            seen_ids = set()
            unique_results = []
            for result in all_results:
                if result and 'block_index' in result and result['block_index'] not in seen_ids:
                    unique_results.append(result)
                    seen_ids.add(result['block_index'])
            
            if not use_activation or not unique_results:
                return unique_results
        
            # Then, spreading activation
            try:
                all_activations = {}
                for result in unique_results[:3]:  # Top 3 as seeds
                    try:
                        memory_id = result['block_index']
                        activations = self.activation_engine.activate(memory_id)
                        
                        for mem_id, level in activations.items():
                            if mem_id not in all_activations:
                                all_activations[mem_id] = 0
                            all_activations[mem_id] += level
                    except Exception as e:
                        logger.warning(f"Activation failed for memory {result['block_index']}: {e}")
                        continue
                
                # Combine results
                activated_memories = []
                for mem_id, activation in all_activations.items():
                    if activation > 0.2:
                        try:
                            memory = self.block_manager.db_manager.get_block(mem_id)
                            if memory:
                                memory['activation_score'] = activation
                                activated_memories.append(memory)
                        except Exception as e:
                            logger.warning(f"Failed to retrieve activated memory {mem_id}: {e}")
                            continue
                
                # Sort by activation
                activated_memories.sort(key=lambda x: x.get('activation_score', 0), reverse=True)
                
                return activated_memories
                
            except Exception as e:
                logger.warning(f"Spreading activation failed: {e}")
                return unique_results
        
        except ValueError:
            # Re-raise validation errors
            raise
        except Exception as e:
            logger.error(f"Critical error during recall: {e}")
            return []  # Return empty list instead of crashing
    
    def switch_context(self, trigger: str):
        """
        Manually switch context
        
        Args:
            trigger: Context trigger description (required, non-empty string)
            
        Raises:
            ValueError: Invalid trigger parameter
            RuntimeError: Context switch failed
        """
        if not isinstance(trigger, str):
            raise ValueError(f"Trigger must be a string, got {type(trigger)}")
        
        if not trigger or not trigger.strip():
            raise ValueError("Trigger cannot be empty or whitespace only")
        
        try:
            self.context_manager.switch_context(trigger.strip())
        except Exception as e:
            logger.error(f"Failed to switch context to '{trigger}': {e}")
            raise RuntimeError(f"Context switch failed: {e}") from e
    
    def get_context_info(self) -> Dict:
        """
        Get current context information
        
        Returns:
            Dictionary with context information or empty dict on error
        """
        try:
            return {
                'context_id': self.context_manager.current_context_id,
                'trigger': self.context_manager.context_trigger,
                'start_time': self.context_manager.context_start_time,
                'active_memories': len(self.context_manager.active_nodes),
                'activation_levels': self.context_manager.active_nodes.copy()
            }
        except Exception as e:
            logger.error(f"Failed to get context info: {e}")
            return {}
    
    def get_memory_connections(self, memory_id: int) -> List[Dict]:
        """Get all connections for a memory"""
        cursor = self.db_manager.conn.cursor()
        cursor.execute('''
            SELECT * FROM memory_connections
            WHERE from_memory = ? OR to_memory = ?
        ''', (memory_id, memory_id))
        
        connections = []
        for row in cursor.fetchall():
            connections.append({
                'from': row[0],
                'to': row[1],
                'weight': row[2],
                'type': row[3],
                'context': row[5]
            })
        
        return connections
    
    def filter_by_importance(self, min_importance: float = 0.0, max_importance: float = 1.0, 
                           include_stm: bool = True, limit: int = 20) -> List[Dict]:
        """Filter memories by importance level"""
        results = []
        
        # Get STM memories if requested (only those not yet promoted to LTM)
        if include_stm:
            for i, stm_memory in enumerate(self.context_manager.memories):
                if (stm_memory['ltm_id'] is None and  # Not promoted to LTM yet
                    min_importance <= stm_memory['importance'] <= max_importance):
                    results.append({
                        'memory_id': -(i + 1),  # Negative ID for STM
                        'content': stm_memory['content'],
                        'importance': stm_memory['importance'],
                        'timestamp': stm_memory['timestamp'],
                        'context_id': stm_memory['context_id'],
                        'source': 'STM',
                        'ltm_id': stm_memory.get('ltm_id')
                    })
        
        # Get LTM memories
        cursor = self.db_manager.conn.cursor()
        cursor.execute('''
            SELECT block_index, context, importance, timestamp 
            FROM blocks 
            WHERE importance BETWEEN ? AND ?
            ORDER BY importance DESC, timestamp DESC
            LIMIT ?
        ''', (min_importance, max_importance, limit))
        
        for row in cursor.fetchall():
            results.append({
                'memory_id': row[0],
                'content': row[1],
                'importance': row[2],
                'timestamp': row[3],
                'source': 'LTM'
            })
        
        # Sort by importance (descending) - primary sort key
        results.sort(key=lambda x: -x['importance'])
        
        return results[:limit]
    
    def get_high_importance_memories(self, threshold: float = 0.7, limit: int = 10) -> List[Dict]:
        """Get memories with importance above threshold"""
        return self.filter_by_importance(min_importance=threshold, limit=limit)
    
    def get_low_importance_memories(self, threshold: float = 0.3, limit: int = 10) -> List[Dict]:
        """Get memories with importance below threshold"""
        return self.filter_by_importance(max_importance=threshold, limit=limit)
    
    def get_importance_statistics(self) -> Dict:
        """Get statistics about memory importance distribution"""
        stats = {
            'stm_stats': {'count': 0, 'avg_importance': 0, 'high_importance': 0},
            'ltm_stats': {'count': 0, 'avg_importance': 0, 'high_importance': 0},
            'overall_stats': {}
        }
        
        # STM statistics
        stm_importances = [m['importance'] for m in self.context_manager.memories if m['ltm_id'] is None]
        if stm_importances:
            stats['stm_stats'] = {
                'count': len(stm_importances),
                'avg_importance': sum(stm_importances) / len(stm_importances),
                'min_importance': min(stm_importances),
                'max_importance': max(stm_importances),
                'high_importance': len([i for i in stm_importances if i >= 0.7])
            }
        
        # LTM statistics
        cursor = self.db_manager.conn.cursor()
        cursor.execute('SELECT AVG(importance), MIN(importance), MAX(importance), COUNT(*) FROM blocks')
        row = cursor.fetchone()
        
        if row and row[3] > 0:  # If there are LTM memories
            stats['ltm_stats'] = {
                'count': row[3],
                'avg_importance': row[0],
                'min_importance': row[1],
                'max_importance': row[2]
            }
            
            # Count high importance LTM memories
            cursor.execute('SELECT COUNT(*) FROM blocks WHERE importance >= 0.7')
            stats['ltm_stats']['high_importance'] = cursor.fetchone()[0]
        
        # Overall statistics
        total_count = stats['stm_stats']['count'] + stats['ltm_stats']['count']
        if total_count > 0:
            total_avg = ((stats['stm_stats']['avg_importance'] * stats['stm_stats']['count']) +
                        (stats['ltm_stats']['avg_importance'] * stats['ltm_stats']['count'])) / total_count
            
            stats['overall_stats'] = {
                'total_memories': total_count,
                'avg_importance': total_avg,
                'stm_percentage': stats['stm_stats']['count'] / total_count * 100,
                'ltm_percentage': stats['ltm_stats']['count'] / total_count * 100,
                'high_importance_total': stats['stm_stats']['high_importance'] + stats['ltm_stats']['high_importance']
            }
        
        return stats