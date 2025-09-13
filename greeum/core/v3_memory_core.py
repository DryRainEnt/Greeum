"""
Greeum v3.0.0: AI-Native Memory Core
Clean slate design with no legacy compatibility
"""

import uuid
import json
import sqlite3
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from dataclasses import dataclass, field, asdict
from pathlib import Path

logger = logging.getLogger(__name__)

@dataclass
class V3Memory:
    """v3.0.0 Memory structure designed for AI"""
    memory_id: str
    timestamp: str
    
    # Primary Actants
    subject: Optional[str] = None
    action: Optional[str] = None
    object: Optional[str] = None
    
    # Extended Actants
    sender: Optional[str] = None
    receiver: Optional[str] = None
    context: Optional[str] = None
    
    # AI Analysis
    intent: Optional[str] = None
    emotion: Optional[str] = None
    importance: float = 0.5
    
    # Relations
    causes: List[str] = field(default_factory=list)
    effects: List[str] = field(default_factory=list)
    related: List[str] = field(default_factory=list)
    
    # Original
    original_text: str = ""
    
    # Metadata
    ai_model: str = "claude"
    confidence: float = 0.5
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())


class V3MemoryCore:
    """
    Core v3.0.0 memory system
    Designed for AI to directly read and write
    """
    
    def __init__(self, db_path: Optional[str] = None):
        """
        Initialize v3 memory core
        
        Args:
            db_path: Path to v3 database (default: data/greeum_v3.db)
        """
        if db_path:
            self.db_path = db_path
        else:
            # Default v3 database (separate from v2.x)
            self.db_path = Path("data") / "greeum_v3.db"
            self.db_path.parent.mkdir(exist_ok=True)
        
        self.conn = sqlite3.connect(str(self.db_path))
        self.conn.row_factory = sqlite3.Row
        self._create_tables()
        
        logger.info(f"V3 Memory Core initialized: {self.db_path}")
    
    def _create_tables(self):
        """Create v3 tables"""
        cursor = self.conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS v3_memories (
                memory_id TEXT PRIMARY KEY,
                timestamp TEXT NOT NULL,
                
                -- Actants
                subject TEXT,
                action TEXT,
                object TEXT,
                sender TEXT,
                receiver TEXT,
                context TEXT,
                
                -- AI Analysis
                intent TEXT,
                emotion TEXT,
                importance REAL DEFAULT 0.5,
                
                -- Relations (JSON arrays)
                causes TEXT DEFAULT '[]',
                effects TEXT DEFAULT '[]',
                related TEXT DEFAULT '[]',
                
                -- Original
                original_text TEXT NOT NULL,
                
                -- Metadata
                ai_model TEXT DEFAULT 'claude',
                confidence REAL DEFAULT 0.5,
                created_at TEXT NOT NULL
            )
        ''')
        
        # Simple indexes
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_v3_timestamp ON v3_memories(timestamp)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_v3_subject ON v3_memories(subject)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_v3_action ON v3_memories(action)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_v3_importance ON v3_memories(importance DESC)')
        
        self.conn.commit()
    
    def add_memory(self, memory: V3Memory) -> str:
        """
        Add a new v3 memory
        
        Args:
            memory: V3Memory object (typically created by AI)
            
        Returns:
            memory_id of the added memory
        """
        cursor = self.conn.cursor()
        
        # Generate ID if not provided
        if not memory.memory_id:
            memory.memory_id = f"v3_{uuid.uuid4().hex[:12]}"
        
        cursor.execute('''
            INSERT INTO v3_memories (
                memory_id, timestamp, subject, action, object,
                sender, receiver, context, intent, emotion, importance,
                causes, effects, related, original_text,
                ai_model, confidence, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            memory.memory_id,
            memory.timestamp,
            memory.subject,
            memory.action,
            memory.object,
            memory.sender,
            memory.receiver,
            memory.context,
            memory.intent,
            memory.emotion,
            memory.importance,
            json.dumps(memory.causes),
            json.dumps(memory.effects),
            json.dumps(memory.related),
            memory.original_text,
            memory.ai_model,
            memory.confidence,
            memory.created_at
        ))
        
        self.conn.commit()
        logger.debug(f"Added v3 memory: {memory.memory_id}")
        
        return memory.memory_id
    
    def get_memory(self, memory_id: str) -> Optional[V3Memory]:
        """
        Get a specific memory
        
        Args:
            memory_id: Memory ID to retrieve
            
        Returns:
            V3Memory object or None
        """
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM v3_memories WHERE memory_id = ?', (memory_id,))
        
        row = cursor.fetchone()
        if not row:
            return None
        
        return self._row_to_memory(row)
    
    def search_by_actant(self, 
                        subject: Optional[str] = None,
                        action: Optional[str] = None,
                        object: Optional[str] = None,
                        limit: int = 20) -> List[V3Memory]:
        """
        Search memories by actant components
        
        Args:
            subject: Subject to search for
            action: Action to search for
            object: Object to search for
            limit: Maximum results
            
        Returns:
            List of matching memories
        """
        cursor = self.conn.cursor()
        
        conditions = []
        params = []
        
        if subject:
            conditions.append("subject = ?")
            params.append(subject)
        if action:
            conditions.append("action = ?")
            params.append(action)
        if object:
            conditions.append("object = ?")
            params.append(object)
        
        if conditions:
            where_clause = "WHERE " + " AND ".join(conditions)
        else:
            where_clause = ""
        
        query = f'''
            SELECT * FROM v3_memories 
            {where_clause}
            ORDER BY timestamp DESC
            LIMIT ?
        '''
        params.append(limit)
        
        cursor.execute(query, params)
        
        memories = []
        for row in cursor.fetchall():
            memories.append(self._row_to_memory(row))
        
        return memories
    
    def get_recent_memories(self, limit: int = 10) -> List[V3Memory]:
        """
        Get recent memories
        
        Args:
            limit: Number of memories to return
            
        Returns:
            List of recent memories
        """
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT * FROM v3_memories
            ORDER BY timestamp DESC
            LIMIT ?
        ''', (limit,))
        
        memories = []
        for row in cursor.fetchall():
            memories.append(self._row_to_memory(row))
        
        return memories
    
    def get_important_memories(self, threshold: float = 0.7, limit: int = 20) -> List[V3Memory]:
        """
        Get memories above importance threshold
        
        Args:
            threshold: Minimum importance (0-1)
            limit: Maximum results
            
        Returns:
            List of important memories
        """
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT * FROM v3_memories
            WHERE importance >= ?
            ORDER BY importance DESC
            LIMIT ?
        ''', (threshold, limit))
        
        memories = []
        for row in cursor.fetchall():
            memories.append(self._row_to_memory(row))
        
        return memories
    
    def find_related_memories(self, memory_id: str) -> List[V3Memory]:
        """
        Find memories related to a given memory
        
        Args:
            memory_id: Source memory ID
            
        Returns:
            List of related memories
        """
        memory = self.get_memory(memory_id)
        if not memory:
            return []
        
        related_ids = memory.causes + memory.effects + memory.related
        
        if not related_ids:
            return []
        
        placeholders = ','.join('?' * len(related_ids))
        cursor = self.conn.cursor()
        cursor.execute(f'''
            SELECT * FROM v3_memories
            WHERE memory_id IN ({placeholders})
        ''', related_ids)
        
        memories = []
        for row in cursor.fetchall():
            memories.append(self._row_to_memory(row))
        
        return memories
    
    def update_relations(self, memory_id: str, 
                        causes: Optional[List[str]] = None,
                        effects: Optional[List[str]] = None,
                        related: Optional[List[str]] = None):
        """
        Update memory relations
        
        Args:
            memory_id: Memory to update
            causes: New causes list
            effects: New effects list
            related: New related list
        """
        cursor = self.conn.cursor()
        
        updates = []
        params = []
        
        if causes is not None:
            updates.append("causes = ?")
            params.append(json.dumps(causes))
        if effects is not None:
            updates.append("effects = ?")
            params.append(json.dumps(effects))
        if related is not None:
            updates.append("related = ?")
            params.append(json.dumps(related))
        
        if not updates:
            return
        
        params.append(memory_id)
        
        cursor.execute(f'''
            UPDATE v3_memories
            SET {', '.join(updates)}
            WHERE memory_id = ?
        ''', params)
        
        self.conn.commit()
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get v3 memory statistics
        
        Returns:
            Dictionary with statistics
        """
        cursor = self.conn.cursor()
        
        # Total count
        cursor.execute('SELECT COUNT(*) FROM v3_memories')
        total = cursor.fetchone()[0]
        
        # Subject distribution
        cursor.execute('''
            SELECT subject, COUNT(*) as count 
            FROM v3_memories 
            WHERE subject IS NOT NULL
            GROUP BY subject 
            ORDER BY count DESC
            LIMIT 5
        ''')
        top_subjects = {row[0]: row[1] for row in cursor.fetchall()}
        
        # Action distribution
        cursor.execute('''
            SELECT action, COUNT(*) as count
            FROM v3_memories
            WHERE action IS NOT NULL
            GROUP BY action
            ORDER BY count DESC
            LIMIT 5
        ''')
        top_actions = {row[0]: row[1] for row in cursor.fetchall()}
        
        # Average importance
        cursor.execute('SELECT AVG(importance) FROM v3_memories')
        avg_importance = cursor.fetchone()[0] or 0
        
        # Memories with relations
        cursor.execute('''
            SELECT COUNT(*) FROM v3_memories
            WHERE causes != '[]' OR effects != '[]' OR related != '[]'
        ''')
        with_relations = cursor.fetchone()[0]
        
        return {
            'total_memories': total,
            'top_subjects': top_subjects,
            'top_actions': top_actions,
            'average_importance': avg_importance,
            'memories_with_relations': with_relations,
            'relation_percentage': (with_relations / total * 100) if total > 0 else 0
        }
    
    def _row_to_memory(self, row) -> V3Memory:
        """Convert database row to V3Memory object"""
        return V3Memory(
            memory_id=row['memory_id'],
            timestamp=row['timestamp'],
            subject=row['subject'],
            action=row['action'],
            object=row['object'],
            sender=row['sender'],
            receiver=row['receiver'],
            context=row['context'],
            intent=row['intent'],
            emotion=row['emotion'],
            importance=row['importance'],
            causes=json.loads(row['causes']) if row['causes'] else [],
            effects=json.loads(row['effects']) if row['effects'] else [],
            related=json.loads(row['related']) if row['related'] else [],
            original_text=row['original_text'],
            ai_model=row['ai_model'],
            confidence=row['confidence'],
            created_at=row['created_at']
        )
    
    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
            logger.info(f"V3 Memory Core closed: {self.db_path}")